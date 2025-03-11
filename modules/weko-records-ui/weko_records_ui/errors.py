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
from flask_babelex import gettext as _
from invenio_rest.errors import RESTException, RESTValidationError


class VersionNotFoundRESTError(RESTException):
    """API Version error."""

    code = 400
    description = 'This API version does not found'


class DateFormatRESTError(RESTException):
    """Date Format error."""

    code = 400
    description = 'Date formatting(YYYY-MM) is incorrect.'


class ModeNotFoundRESTError(RESTException):
    """Date Format error."""

    code = 400
    description = 'Mode not specified.'

class InvalidEmailError(RESTException):
    """Invalid email Error error."""

    code = 400
    description = _('Invalid mailaddress.')

class RequiredItemNotExistError(RESTValidationError):
    """Required Item not exists in request body error."""

    description = _('Reqired item does not exist.')

class InvalidCaptchaError(RESTException):
    """Invalid CAPTCHA calculation result error."""

    code = 400
    description = _('The calculation results are different.')

class InvalidRequestError(RESTException):
    """Invalid Request error."""

    code = 400
    description = 'Invalid Request Header or Body'

class AuthenticationRequiredError(RESTException):
    """Contents not found error."""

    code = 401
    description = _('Unauthorized.')

class PermissionError(RESTException):
    """Permission error"""

    code = 403
    description = 'Permission denied'

class AvailableFilesNotFoundRESTError(RESTException):
    """Available Files Not Found error."""

    code = 403
    description = 'This File is private or you don\'t have permission'

class RecordsNotFoundRESTError(RESTException):
    """Records Not Found error."""

    code = 404
    description = 'This Item does not found'

class FilesNotFoundRESTError(RESTException):
    """Files Not Found error."""

    code = 404
    description = 'This File does not found'

class ContentsNotFoundError(RESTException):
    """Contents not found error."""

    code = 404
    description = _('Contents not found.')

class InternalServerError(RESTException):
    """Internal Server Error."""

    code = 500
    description = 'Internal Server Error'
