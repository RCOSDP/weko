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


class WekoWorkflowException(Exception):
    """Base class for all exceptions raised by weko_workflow."""

    def __init__(self, *args, **kwargs):
        """Initialize the exception with a message."""
        super().__init__(*args, **kwargs)
