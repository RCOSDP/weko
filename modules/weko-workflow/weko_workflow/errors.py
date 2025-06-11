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

"""Index errors."""
from flask_babelex import gettext as _
from invenio_rest.errors import RESTException


class ActivityBaseRESTError(RESTException):
    """Invalid argument."""

    code = 400
    description = _('Invalid ID supplied.')


class VersionNotFoundRESTError(RESTException):
    """API Version error."""
    
    code = 400
    description = _('This API version does not found.')


class InvalidParameterValueError(RESTException):
    """Invalid value."""

    code = 400
    description = _('Invalid request parameter value.')

class InvalidTokenError(RESTException):
    """Invalid token."""

    code = 400
    description = _('Invalid token.')

class ExpiredActivityError(RESTException):
    """Expired activity."""

    code = 400
    description = _('Expired token.')

class IndexNotFoundError(RESTException):
    """Index not found."""

    code = 404
    description = _('Index not found."')

class ItemUneditableError(RESTException):
    """Item uneditable."""

    code = 403
    description = _('Item uneditable."')

class MetadataFormatError(RESTException):
    """Metadata format Error."""

    code = 400
    _description = _('Metadata format Error.')
    cause = []

    def __init__(self, cause, **kwargs):
        self.cause = [cause] if isinstance(cause, str) else cause
        super().__init__(**kwargs)
    
    @property
    def description(self):
        res = self._description
        for val in self.cause:
            res = f"{res}\n  - {val}"
        return res

class StatusNotApproveError(RESTException):
    """Status is Not Approve Error."""

    code = 400
    description = _('Activity status is not Approval.')

class StatusNotItemRegistrationError(RESTException):
    """Status is Not ItemRegistration(item_login) Error."""

    code = 400
    description = _('Activity status is not Item Registration.')


class PermissionError(RESTException):
    """Permission error."""

    code = 403
    description = _('Permission denied.')


class InvalidInputRESTError(RESTException):
    """Invalid request body."""

    code = 405
    description = _('Invalid input.')


class ActivityNotFoundRESTError(RESTException):
    """Can't get Activity detail by ID."""

    code = 404
    description = _('指定されたIDによる登録アクティビティが存在しない。')


class RegisteredActivityNotFoundRESTError(RESTException):
    """Can't get Registered Activity by ID."""

    code = 404
    description = _('登録アクティビティが見つからない。')


class DeleteActivityFailedRESTError(RESTException):
    """Can't finish Delete Activity process."""

    code = 404
    description = _('登録アクティビティを削除エラー。')


class InternalServerError(RESTException):
    """Internal Server Error."""
    
    code = 500
    description = _('Internal Server Error.')
