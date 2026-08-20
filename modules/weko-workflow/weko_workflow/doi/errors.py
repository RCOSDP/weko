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

"""Errors raised while depositing a DOI to a registration agency."""


class DoiDepositError(Exception):
    """Base class of every DOI deposit error."""

    def __init__(self, message, http_status=None, response=None):
        """Keep the information needed to fill in a DoiDepositLog row.

        :param message: human readable reason of the failure
        :param http_status: HTTP status code the agency answered with
        :param response: raw body the agency answered with
        """
        super(DoiDepositError, self).__init__(message)
        self.message = message
        self.http_status = http_status
        self.response = response


class RetriableDepositError(DoiDepositError):
    """Temporary failure: the very same request may succeed later.

    Network errors, timeouts, HTTP 429 and 5xx belong here.
    """

    def __init__(self, message, http_status=None, response=None,
                 retry_after=None):
        """Store the delay asked for by the agency, when it sent one."""
        super(RetriableDepositError, self).__init__(
            message, http_status=http_status, response=response)
        self.retry_after = retry_after


class PermanentDepositError(DoiDepositError):
    """Definitive failure: retrying the same request cannot help.

    Metadata rejected by the agency and authentication errors belong here.
    """


class AgencyNotSupportedError(DoiDepositError):
    """No agency is registered for the requested ``doi_select``."""


class DepositLogNotReadyError(DoiDepositError):
    """The log row is not visible yet.

    ``saving_doi_pidstore()`` runs before its caller commits, so a task may
    start before the row it works on exists.  Raising this asks the task to
    come back later.
    """
