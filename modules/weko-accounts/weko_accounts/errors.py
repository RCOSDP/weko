# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Records Error"""

from invenio_rest.errors import RESTException


class VersionNotFoundRESTError(RESTException):
    """API Version error."""

    code = 400
    description = 'This API version does not found'


class UserAllreadyLoggedInError(RESTException):
    """User allready logged in."""

    code = 400
    description = 'User allready logged in.'


class UserNotFoundError(RESTException):
    """User not found."""

    code = 403
    description = 'Specified user does not exist.'


class InvalidPasswordError(RESTException):
    """Invalid password."""

    code = 403
    description = 'Invalid password.'


class DisabledUserError(RESTException):
    """Account is disabled."""

    code = 403
    description = 'Account is disabled.'
