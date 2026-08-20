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

"""Celery tasks driving the DOI deposits.

The tasks hold the scheduling -- when to come back, how long to wait, when to
give up -- and delegate every decision about the deposit itself to
:mod:`weko_workflow.doi.orchestrator`.
"""

from celery import shared_task
from flask import current_app

from .base import DepositStatus
from .errors import DepositLogNotReadyError
from .orchestrator import STATUS_PENDING, run_deposit, run_poll


@shared_task(bind=True, ignore_result=True)
def deposit_doi(self, log_id):
    """Build and send one deposit.

    :param log_id: id of the :class:`~weko_workflow.models.DoiDepositLog`
    """
    with current_app.app_context():
        try:
            status = run_deposit(log_id)
        except DepositLogNotReadyError as ex:
            # saving_doi_pidstore() had not committed yet: come back later.
            raise self.retry(
                exc=ex,
                countdown=current_app.config.get(
                    'WEKO_DOI_SUBMIT_COUNTDOWN', 10),
                max_retries=current_app.config.get('WEKO_DOI_MAX_RETRY', 3))

        if status is DepositStatus.ACCEPTED:
            poll_doi_deposit.apply_async(
                args=[log_id],
                countdown=current_app.config.get(
                    'WEKO_DOI_FIRST_POLL_DELAY', 60))
        elif status is DepositStatus.RETRIABLE:
            raise self.retry(
                countdown=_backoff(self.request.retries),
                max_retries=current_app.config.get('WEKO_DOI_MAX_RETRY', 3))


@shared_task(bind=True, ignore_result=True)
def poll_doi_deposit(self, log_id):
    """Ask the agency whether an accepted deposit succeeded.

    Reschedules itself until the agency answers or
    ``WEKO_DOI_MAX_POLL_ATTEMPTS`` is reached, at which point the log is left
    in ``unknown`` for an operator to resend.

    :param log_id: id of the :class:`~weko_workflow.models.DoiDepositLog`
    """
    with current_app.app_context():
        try:
            status = run_poll(log_id)
        except DepositLogNotReadyError as ex:
            raise self.retry(
                exc=ex,
                countdown=current_app.config.get(
                    'WEKO_DOI_SUBMIT_COUNTDOWN', 10),
                max_retries=current_app.config.get('WEKO_DOI_MAX_RETRY', 3))

        if status in (DepositStatus.ACCEPTED, DepositStatus.RETRIABLE):
            poll_doi_deposit.apply_async(
                args=[log_id],
                countdown=current_app.config.get(
                    'WEKO_DOI_POLL_INTERVAL', 300))


@shared_task(ignore_result=True)
def resend_doi_deposit(log_id):
    """Send a failed deposit again, after the metadata has been fixed.

    :param log_id: id of the :class:`~weko_workflow.models.DoiDepositLog`
    """
    from invenio_db import db

    from ..models import DoiDepositLog

    with current_app.app_context():
        log = DoiDepositLog.query.filter_by(id=log_id).one_or_none()
        if log is None:
            current_app.logger.error(
                'DOI deposit log {0} does not exist.'.format(log_id))
            return
        log.deposit_status = STATUS_PENDING
        log.error_message = None
        db.session.commit()
        deposit_doi.delay(log_id)


def _backoff(retries):
    """Return the delay before the next attempt, growing exponentially."""
    base = current_app.config.get('WEKO_DOI_RETRY_COUNTDOWN', 60)
    return base * (2 ** max(0, retries))
