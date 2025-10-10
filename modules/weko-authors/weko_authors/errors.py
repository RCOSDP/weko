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

"""Authors Error"""
from invenio_rest.errors import RESTException


class AuthorBaseRESTError(RESTException):
    """Invalid request body."""

    code = 400
    description = 'Invalid request body.'


class VersionNotFoundRESTError(AuthorBaseRESTError):
    """API Version error."""

    code = 400
    description = 'This API version does not found.'


class AuthorNotFoundRESTError(AuthorBaseRESTError):
    """Author Not Found error."""

    code = 404
    description = 'This author does not found.'


class InvalidDataRESTError(AuthorBaseRESTError):
    """Invalid request body."""

    code = 400
    description = 'Could not load data.'


class AuthorInternalServerError(AuthorBaseRESTError):
    """Internal Server Error."""

    code = 500
    description = 'Internal Server Error'


class AuthorsValidationError(AuthorBaseRESTError):
    """Authors validation error."""

    code = 400
    description = 'Authors validation error.'

class AuthorsPermissionError(AuthorsValidationError):
    """Authors permission error."""

    code = 403
    description = 'Authors permission error.'