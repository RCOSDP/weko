# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Drive a DOI deposit from the item metadata to the agency and back.

Everything the agencies have in common lives here: when a deposit is
requested, how its state moves, and the rule that a broken registration
agency must never abort the item registration itself.
"""

from flask import current_app
from invenio_db import db

from .base import DepositStatus
from .errors import DepositLogNotReadyError, DoiDepositError
from .metadata import DoiMetadataSource
from .registry import get_agency, is_supported

STATUS_PENDING = 'pending'
"""The deposit has been requested but not sent yet."""

STATUS_SUBMITTED = 'submitted'
"""The agency accepted the request and is being polled."""

STATUS_SUCCESS = 'success'
"""The agency confirmed the registration."""

STATUS_FAILURE = 'failure'
"""The agency rejected the record, or the metadata could not be built."""

STATUS_UNKNOWN = 'unknown'
"""Polling was given up before the agency answered."""


def request_doi_deposit(item_uuid, doi_select, doi, resource_url=None,
                        record=None):
    """Ask for a DOI to be registered with its agency.

    Called at the end of ``saving_doi_pidstore()``, that is *before* the
    caller commits.  Only the log row is written here; the deposit itself
    runs in a task, which is why the task is delayed and retries until the
    row it works on is visible.

    Every error is swallowed on purpose: a registration agency must never
    make an item registration fail.

    :param item_uuid: uuid of the item the DOI belongs to
    :param doi_select: identifier grant value, ``1`` to ``4``
    :param doi: the DOI that was granted
    :param resource_url: URL the DOI has to resolve to
    :param record: already loaded record, to save a query
    :return: the created log, or None when nothing was requested
    """
    from .tasks import deposit_doi

    try:
        if not is_supported(doi_select):
            return None

        agency = get_agency(doi_select)
        if not agency.is_allowed():
            return None

        if not resource_url:
            resource_url = build_resource_url(item_uuid, record=record)

        log = _create_log(agency, item_uuid, doi_select, doi, resource_url)
        countdown = current_app.config.get(
            'WEKO_DOI_SUBMIT_COUNTDOWN', 10)
        deposit_doi.apply_async(args=[log.id], countdown=countdown)
        current_app.logger.info(
            'DOI deposit requested: agency={0} doi={1} log={2}'.format(
                agency.name, doi, log.id))
        return log
    except Exception as ex:
        current_app.logger.error(
            'Could not request the DOI deposit of {0}: {1}'.format(
                item_uuid, ex))
        return None


def _create_log(agency, item_uuid, doi_select, doi, resource_url):
    """Write the ``pending`` row the whole deposit is tracked by."""
    from ..models import DoiDepositLog

    log = DoiDepositLog(
        item_uuid=str(item_uuid),
        agency=agency.name,
        doi_select=str(doi_select),
        doi=doi,
        resource_url=resource_url,
        deposit_status=STATUS_PENDING,
    )
    db.session.add(log)
    db.session.flush()
    return log


def build_resource_url(item_uuid, record=None):
    """Build the landing page URL the DOI has to resolve to.

    :param item_uuid: uuid of the item
    :param record: already loaded record, to save a query
    :return: absolute URL of the item's landing page
    """
    from weko_deposit.api import WekoRecord

    from ..utils import get_url_root

    if record is None:
        record = WekoRecord.get_record(item_uuid)
    deposit_id = record.pid_parent.pid_value.split('parent:')[1]
    return '{0}records/{1}'.format(get_url_root(), deposit_id)


def run_deposit(log_id):
    """Build the payload of a pending deposit and send it.

    :param log_id: id of the :class:`~weko_workflow.models.DoiDepositLog`
    :return: the :class:`~weko_workflow.doi.base.DepositStatus` reached
    :raises DepositLogNotReadyError: when the row is not visible yet
    """
    log = _load_log(log_id)
    if log.deposit_status not in (STATUS_PENDING, STATUS_FAILURE):
        current_app.logger.info(
            'DOI deposit {0} is already {1}, skipping.'.format(
                log_id, log.deposit_status))
        return None

    agency = get_agency(log.doi_select)
    if not agency.is_allowed():
        current_app.logger.warning(
            'DOI deposit {0} was requested but {1} is now disabled.'.format(
                log_id, agency.name))
        return None

    log.attempt = (log.attempt or 0) + 1

    try:
        source = DoiMetadataSource(log.item_uuid, log.doi, log.resource_url)
        errors = agency.validate(source)
        if errors:
            return _finish(log, STATUS_FAILURE, '; '.join(errors))
        request = agency.build_payload(source)
    except Exception as ex:
        current_app.logger.exception(
            'Could not build the {0} payload of {1}: {2}'.format(
                agency.name, log.item_uuid, ex))
        return _finish(log, STATUS_FAILURE,
                       'Could not build the payload: {0}'.format(ex))

    log.payload = request.payload
    log.record_type = request.record_type
    log.tracking_id = request.tracking_id
    db.session.commit()

    try:
        result = agency.register(request)
    except DoiDepositError as ex:
        result = None
        current_app.logger.error(
            'Deposit of {0} to {1} failed: {2}'.format(
                log.doi, agency.name, ex.message))
    if result is None:
        return _finish(log, STATUS_FAILURE, 'The agency raised an error.')

    return _apply_result(log, result, agency)


def run_poll(log_id):
    """Ask the agency for the outcome of a submitted deposit.

    :param log_id: id of the :class:`~weko_workflow.models.DoiDepositLog`
    :return: the :class:`~weko_workflow.doi.base.DepositStatus` reached
    :raises DepositLogNotReadyError: when the row is not visible yet
    """
    log = _load_log(log_id)
    if log.deposit_status != STATUS_SUBMITTED:
        return None

    agency = get_agency(log.doi_select)
    log.poll_attempt = (log.poll_attempt or 0) + 1

    max_attempts = current_app.config.get('WEKO_DOI_MAX_POLL_ATTEMPTS', 20)
    if log.poll_attempt > max_attempts:
        # Crossref sometimes keeps a submission queued for hours; stop asking
        # and leave it for an operator to resend rather than poll forever.
        _finish(log, STATUS_UNKNOWN,
                'Gave up polling after {0} attempts; the submission may '
                'still be queued.'.format(max_attempts))
        return None

    result = agency.poll(log.tracking_id)
    return _apply_result(log, result, agency)


def _apply_result(log, result, agency):
    """Move the log to the state the agency's answer implies."""
    if result.status is DepositStatus.SUCCEEDED:
        _finish(log, STATUS_SUCCESS, result.message, result)
    elif result.status is DepositStatus.ACCEPTED:
        log.deposit_status = STATUS_SUBMITTED
        log.tracking_id = result.tracking_id or log.tracking_id
        log.http_status = result.http_status
        log.error_message = None
        db.session.commit()
    elif result.status is DepositStatus.RETRIABLE:
        log.http_status = result.http_status
        log.error_message = result.message
        db.session.commit()
    else:
        _finish(log, STATUS_FAILURE, result.message, result)
    return result.status


def _finish(log, status, message, result=None):
    """Store a definitive outcome and notify when it is a failure."""
    log.deposit_status = status
    log.error_message = message
    if result is not None:
        log.http_status = result.http_status
        log.response = result.response
    db.session.commit()

    if status == STATUS_SUCCESS:
        current_app.logger.info(
            'DOI {0} registered with {1}.'.format(log.doi, log.agency))
    else:
        current_app.logger.error(
            'DOI {0} could not be registered with {1}: {2}'.format(
                log.doi, log.agency, message))
        notify_failure(log)
    return DepositStatus.SUCCEEDED if status == STATUS_SUCCESS \
        else DepositStatus.FAILED


def _load_log(log_id):
    """Load a log row, or ask the caller to come back later."""
    from ..models import DoiDepositLog

    log = DoiDepositLog.query.filter_by(id=log_id).one_or_none()
    if log is None:
        raise DepositLogNotReadyError(
            'DOI deposit log {0} is not visible yet.'.format(log_id))
    return log


def notify_failure(log):
    """Mail the administrators about a deposit that will not succeed.

    :param log: the :class:`~weko_workflow.models.DoiDepositLog` that failed
    """
    recipients = current_app.config.get('WEKO_DOI_NOTIFY_EMAIL')
    if not recipients:
        return
    if isinstance(recipients, str):
        recipients = [recipients]

    from invenio_mail.api import send_mail

    send_mail(
        '[WEKO3] {0} DOI registration failed'.format(log.agency),
        recipients,
        body=('DOI: {0}\nItem: {1}\nStatus: {2}\nMessage: {3}\n'.format(
            log.doi, log.item_uuid, log.deposit_status, log.error_message)))
