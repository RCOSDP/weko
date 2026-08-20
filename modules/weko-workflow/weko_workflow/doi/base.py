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

"""Common interface every DOI registration agency implements.

The orchestrator only ever talks to this interface, so that it never has to
know whether the agency answers synchronously (DataCite) or asynchronously
(Crossref).  Two things absorb that difference:

* :class:`DepositStatus` -- ``SUCCEEDED`` is the synchronous answer,
  ``ACCEPTED`` means "come back later", and
* :attr:`AgencyCapabilities.requires_polling` -- whether :meth:`poll` exists.
"""

from enum import Enum


class DepositStatus(Enum):
    """Outcome of a single deposit or poll attempt."""

    SUCCEEDED = 'succeeded'
    """The agency confirmed the registration."""

    ACCEPTED = 'accepted'
    """The agency took the request but has not judged it yet."""

    RETRIABLE = 'retriable'
    """Temporary failure; the same request may succeed later."""

    FAILED = 'failed'
    """Definitive failure; retrying the same request cannot help."""


class AgencyCapabilities(object):
    """What the orchestrator has to know about an agency's protocol."""

    def __init__(self, requires_polling=False,
                 payload_content_type='application/xml'):
        """Describe the agency's protocol.

        :param requires_polling: True when :meth:`DoiRegistrationAgency.poll`
            has to be called to learn the outcome
        :param payload_content_type: media type of the built payload
        """
        self.requires_polling = requires_polling
        self.payload_content_type = payload_content_type


class DepositRequest(object):
    """Everything needed to send one record to one agency."""

    def __init__(self, item_uuid, doi, resource_url, payload,
                 tracking_id=None, record_type=None):
        """Bundle the payload with the identifiers it registers.

        :param item_uuid: uuid of the item the DOI belongs to
        :param doi: DOI to register
        :param resource_url: URL the DOI has to resolve to
        :param payload: agency specific body (XML or JSON text)
        :param tracking_id: id the agency uses to talk about this submission
        :param record_type: agency specific record type, for the log
        """
        self.item_uuid = item_uuid
        self.doi = doi
        self.resource_url = resource_url
        self.payload = payload
        self.tracking_id = tracking_id
        self.record_type = record_type


class DepositResult(object):
    """Outcome of :meth:`DoiRegistrationAgency.register` or ``poll``."""

    def __init__(self, status, tracking_id=None, http_status=None,
                 message=None, response=None, retry_after=None):
        """Describe one attempt.

        :param status: a :class:`DepositStatus`
        :param tracking_id: id to poll with, when the status is ``ACCEPTED``
        :param http_status: HTTP status the agency answered with
        :param message: human readable summary, stored in the log
        :param response: raw body, stored in the log for auditing
        :param retry_after: seconds to wait before retrying
        """
        self.status = status
        self.tracking_id = tracking_id
        self.http_status = http_status
        self.message = message
        self.response = response
        self.retry_after = retry_after

    def __repr__(self):
        """Return a debug friendly representation."""
        return '<DepositResult {0} tracking_id={1} http={2}>'.format(
            self.status.value, self.tracking_id, self.http_status)


class DoiRegistrationAgency(object):
    """Base class of every DOI registration agency.

    Adding an agency means subclassing this and registering the subclass in
    ``WEKO_DOI_AGENCIES``; the orchestrator itself never changes.
    """

    name = ''
    """Short name stored in ``doi_deposit_log.agency``."""

    capabilities = AgencyCapabilities()
    """Protocol traits, see :class:`AgencyCapabilities`."""

    def is_allowed(self):
        """Tell whether this agency may be called at all.

        An enabled agency whose credentials are missing has to answer False
        *and* log an error, so that a missing setting is never mistaken for
        "registration is turned off".

        :return: True when a deposit may be sent
        """
        raise NotImplementedError

    def validate(self, source):
        """List the reasons this record cannot be registered.

        Called before building the payload, so that metadata the agency is
        known to reject never reaches the network.

        :param source: a :class:`~weko_workflow.doi.metadata.DoiMetadataSource`
        :return: list of human readable messages; empty when acceptable
        """
        return []

    def build_payload(self, source):
        """Turn the item metadata into an agency specific request.

        :param source: a :class:`~weko_workflow.doi.metadata.DoiMetadataSource`
        :return: a :class:`DepositRequest`
        """
        raise NotImplementedError

    def register(self, request):
        """Send the request to the agency.

        :param request: a :class:`DepositRequest`
        :return: a :class:`DepositResult`
        """
        raise NotImplementedError

    def poll(self, tracking_id):
        """Ask the agency for the outcome of an accepted submission.

        Only called when :attr:`AgencyCapabilities.requires_polling` is True.

        :param tracking_id: value returned in ``DepositResult.tracking_id``
        :return: a :class:`DepositResult`
        """
        raise NotImplementedError
