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

"""Crossref registration agency.

Crossref only offers the asynchronous HTTPS POST deposit: ``servlet/deposit``
answers "received", and the outcome has to be fetched afterwards from
``servlet/submissionDownload``.  The synchronous REST deposit v2 is not
available to us, hence there is a single code path here.
"""

import re
import time
import xml.etree.ElementTree as ElementTree

import requests
from flask import current_app

from ..base import AgencyCapabilities, DepositRequest, DepositResult, \
    DepositStatus, DoiRegistrationAgency
from . import crossref_mapper

REQUIRED_SETTINGS = (
    'WEKO_CROSSREF_DEPOSIT_URL',
    'WEKO_CROSSREF_SUBMISSION_LOG_URL',
    'WEKO_CROSSREF_LOGIN_ID',
    'WEKO_CROSSREF_LOGIN_PASSWD',
    'WEKO_CROSSREF_DEPOSITOR_NAME',
    'WEKO_CROSSREF_DEPOSITOR_EMAIL',
    'WEKO_CROSSREF_REGISTRANT',
)
"""Settings without which no deposit can be built or sent."""

DOI_RE = re.compile(r'^10\.\d{4,9}/\S+$')
"""A DOI is a 10.NNNN prefix and a suffix; anything else cannot register."""

PENDING_BATCH_STATUS = ('in_process', 'queued', 'submitted',
                        'unknown_submission')
"""``doi_batch_diagnostic/@status`` values meaning "not judged yet".

``unknown_submission`` is included on purpose: Crossref answers it for a
submission it has not started processing yet, not only for an unknown one.
"""


class CrossrefAgency(DoiRegistrationAgency):
    """Deposit DOIs to Crossref over the HTTPS POST interface."""

    name = 'Crossref'

    capabilities = AgencyCapabilities(requires_polling=True,
                                      payload_content_type='application/xml')

    def is_allowed(self):
        """Tell whether Crossref deposits are enabled and configured.

        :return: True when a deposit may be sent
        """
        if not current_app.config.get('WEKO_CROSSREF_ALLOW_REGISTER_DOI'):
            return False

        missing = [key for key in REQUIRED_SETTINGS
                   if not current_app.config.get(key)]
        if missing:
            current_app.logger.error(
                'Crossref DOI registration is enabled but not configured: '
                '{0}'.format(', '.join(missing)))
            return False
        return True

    def validate(self, source):
        """List the reasons Crossref would reject this record.

        Crossref validates more than the schema does, so the checks that are
        cheap to run locally happen here instead of costing a round trip.

        :param source: a :class:`~weko_workflow.doi.metadata.DoiMetadataSource`
        :return: list of human readable messages
        """
        errors = []
        if not source.doi:
            errors.append('DOI is empty.')
        elif not DOI_RE.match(source.doi):
            # Typically an unset prefix in the identifier settings, which
            # Crossref would reject after a full deposit round trip.
            errors.append(
                'DOI "{0}" is not a well formed DOI; check the Crossref '
                'prefix in the identifier settings.'.format(source.doi))
        if not (source.resource_url or '').startswith('http'):
            errors.append('Resource URL is missing or not absolute.')
        if not [title for title, dummy in source.titles() if title]:
            errors.append('dc:title is required by Crossref.')
        if not source.publication_date():
            errors.append('datacite:date is required by Crossref.')

        if crossref_mapper.choose_record_type(source) == 'journal_article':
            journal = source.journal()
            if not journal.get('full_title'):
                errors.append('jpcoar:sourceTitle is required for a journal '
                              'article.')
            issn = journal.get('issn')
            if issn and not is_valid_issn(issn):
                errors.append('jpcoar:sourceIdentifier "{0}" is not a valid '
                              'ISSN.'.format(issn))
        return errors

    def build_payload(self, source):
        """Build the Crossref ``doi_batch`` document for one item.

        :param source: a :class:`~weko_workflow.doi.metadata.DoiMetadataSource`
        :return: a :class:`~weko_workflow.doi.base.DepositRequest`
        """
        batch_id = build_batch_id(source.item_uuid)
        xml, record_type = crossref_mapper.build_doi_batch(source, batch_id)
        return DepositRequest(
            item_uuid=source.item_uuid,
            doi=source.doi,
            resource_url=source.resource_url,
            payload=xml,
            tracking_id=batch_id,
            record_type=record_type,
        )

    def register(self, request):
        """Send the deposit to Crossref.

        Crossref answers "received" only; the outcome is fetched later by
        :meth:`poll`, hence the ``ACCEPTED`` status.

        :param request: a :class:`~weko_workflow.doi.base.DepositRequest`
        :return: a :class:`~weko_workflow.doi.base.DepositResult`
        """
        url = current_app.config.get('WEKO_CROSSREF_DEPOSIT_URL')
        timeout = current_app.config.get('WEKO_CROSSREF_TIMEOUT', 30)
        file_name = '{0}.xml'.format(request.tracking_id)

        try:
            response = requests.post(
                url,
                data={
                    'operation': 'doMDUpload',
                    'login_id': current_app.config.get(
                        'WEKO_CROSSREF_LOGIN_ID'),
                    'login_passwd': current_app.config.get(
                        'WEKO_CROSSREF_LOGIN_PASSWD'),
                },
                files={
                    'fname': (file_name,
                              request.payload.encode('utf-8'),
                              'text/xml'),
                },
                timeout=timeout)
        except requests.exceptions.RequestException as ex:
            return DepositResult(
                DepositStatus.RETRIABLE,
                message='Could not reach Crossref: {0}'.format(ex))

        body = response.text or ''
        if response.status_code == 200 and 'SUCCESS' in body.upper():
            return DepositResult(
                DepositStatus.ACCEPTED,
                tracking_id=request.tracking_id,
                http_status=response.status_code,
                message='Crossref received the submission.',
                response=body)

        if response.status_code in (429,) or response.status_code >= 500:
            return DepositResult(
                DepositStatus.RETRIABLE,
                http_status=response.status_code,
                message='Crossref is not accepting submissions right now.',
                response=body)

        return DepositResult(
            DepositStatus.FAILED,
            http_status=response.status_code,
            message='Crossref refused the submission.',
            response=body)

    def poll(self, tracking_id):
        """Fetch the submission log of an accepted deposit.

        :param tracking_id: the ``doi_batch_id`` that was deposited
        :return: a :class:`~weko_workflow.doi.base.DepositResult`
        """
        url = current_app.config.get('WEKO_CROSSREF_SUBMISSION_LOG_URL')
        timeout = current_app.config.get('WEKO_CROSSREF_TIMEOUT', 30)

        try:
            response = requests.get(
                url,
                params={
                    'usr': current_app.config.get('WEKO_CROSSREF_LOGIN_ID'),
                    'pwd': current_app.config.get(
                        'WEKO_CROSSREF_LOGIN_PASSWD'),
                    'doi_batch_id': tracking_id,
                    'type': 'result',
                },
                timeout=timeout)
        except requests.exceptions.RequestException as ex:
            return DepositResult(
                DepositStatus.RETRIABLE,
                tracking_id=tracking_id,
                message='Could not reach Crossref: {0}'.format(ex))

        return parse_submission_log(response.text, tracking_id,
                                    response.status_code)


def parse_submission_log(body, tracking_id, http_status=None):
    """Turn a ``doi_batch_diagnostic`` document into a result.

    :param body: body returned by ``submissionDownload``
    :param tracking_id: the ``doi_batch_id`` that was polled
    :param http_status: HTTP status the log was served with
    :return: a :class:`~weko_workflow.doi.base.DepositResult`
    """
    try:
        root = ElementTree.fromstring(body or '')
    except ElementTree.ParseError:
        return DepositResult(
            DepositStatus.RETRIABLE,
            tracking_id=tracking_id,
            http_status=http_status,
            message='Crossref answered something that is not XML.',
            response=body)

    if _local_name(root.tag) != 'doi_batch_diagnostic':
        return DepositResult(
            DepositStatus.RETRIABLE,
            tracking_id=tracking_id,
            http_status=http_status,
            message='Unexpected submission log root <{0}>.'.format(
                _local_name(root.tag)),
            response=body)

    batch_status = (root.get('status') or '').lower()
    if batch_status in PENDING_BATCH_STATUS:
        return DepositResult(
            DepositStatus.ACCEPTED,
            tracking_id=tracking_id,
            http_status=http_status,
            message='Crossref has not judged the submission yet '
                    '({0}).'.format(batch_status),
            response=body)

    failures = []
    successes = 0
    for record in root.iter():
        if _local_name(record.tag) != 'record_diagnostic':
            continue
        status = (record.get('status') or '').lower()
        if status == 'failure':
            failures.append(_diagnostic_message(record))
        elif status in ('success', 'warning'):
            successes += 1

    if failures:
        return DepositResult(
            DepositStatus.FAILED,
            tracking_id=tracking_id,
            http_status=http_status,
            message='; '.join(failures),
            response=body)

    if not successes:
        return DepositResult(
            DepositStatus.RETRIABLE,
            tracking_id=tracking_id,
            http_status=http_status,
            message='Submission log holds no record diagnostic yet.',
            response=body)

    return DepositResult(
        DepositStatus.SUCCEEDED,
        tracking_id=tracking_id,
        http_status=http_status,
        message='Crossref registered the DOI.',
        response=body)


def _diagnostic_message(record):
    """Render one failed ``record_diagnostic`` as a single line."""
    doi = None
    message = None
    for child in record:
        if _local_name(child.tag) == 'doi':
            doi = (child.text or '').strip()
        elif _local_name(child.tag) == 'msg':
            message = (child.text or '').strip()
    return '{0}: {1}'.format(doi or '-', message or 'rejected by Crossref')


def _local_name(tag):
    """Strip the namespace from an element tag."""
    return tag.rsplit('}', 1)[-1]


def build_batch_id(item_uuid):
    """Build a ``doi_batch_id`` that is unique per attempt.

    :param item_uuid: item the deposit belongs to
    :return: value for ``doi_batch_id``
    """
    return 'weko-{0}-{1}'.format(
        crossref_mapper.normalize_item_number(item_uuid),
        time.strftime('%Y%m%d%H%M%S'))


def is_valid_issn(value):
    """Check an ISSN, check digit included.

    Crossref validates the check digit even though the schema does not, so a
    typo in the metadata only shows up as a failed deposit otherwise.

    :param value: ISSN as written in the metadata
    :return: True when the value is a well formed ISSN
    """
    digits = re.sub(r'[^0-9Xx]', '', str(value or '')).upper()
    if len(digits) != 8:
        return False
    try:
        total = sum(int(digits[index]) * (8 - index) for index in range(7))
    except ValueError:
        return False
    remainder = total % 11
    check = 11 - remainder
    expected = 'X' if check == 10 else '0' if check == 11 else str(check)
    return digits[7] == expected
