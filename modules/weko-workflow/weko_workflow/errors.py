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
from flask_babel import gettext as _
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


"""Custom errors for weko workflow."""

class WekoWorkflowError(Exception):
    def __init__(self, ex=None, msg=None, *args):
        """Constructor.

        Initialize the weko workflow error.

        Args:
            ex (Exception): Original exception object
            msg (str): Error message
        """
        if ex is not None:
            self.exception = ex
        if msg is None:
            msg = "Some error has occurred in weko_workflow."
        self.msg = msg
        super().__init__(msg, *args)


class WekoWorkflowNameError(WekoWorkflowError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some name error has occurred in weko_workflow."
        super().__init__(ex, msg, *args)


class WekoWorkflowMailError(WekoWorkflowError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some mail error has occurred in weko_workflow."
        super().__init__(ex, msg, *args)


class WekoActionError(WekoWorkflowError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some action error has occurred in weko_workflow."
        super().__init__(ex, msg, *args)


class WekoActivityError(WekoWorkflowError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some activity error has occurred in weko_workflow."
        super().__init__(ex, msg, *args)


class WekoActivityHistoryError(WekoActivityError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some activity history error has occurred in weko_workflow."
        super().__init__(ex, msg, *args)


class WekoActivityValidationError(WekoActivityError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some activity validation error has occurred in weko_workflow."
        super().__init__(ex, msg, *args)

