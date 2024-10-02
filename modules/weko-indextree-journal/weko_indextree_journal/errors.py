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

"""Journal errors."""
from invenio_rest.errors import RESTException

FAILED_MSG = ''


class JournalBaseRESTError(RESTException):
    """Invalid request body."""

    code = 400


class JournalInvalidDataRESTError(RESTException):
    """Invalid request body."""

    code = 400
    description = 'Could not load data.'


class JournalDeletedRESTError(RESTException):
    """Invalid request body."""

    code = 204
    description = 'This journal has been deleted.'


class JournalNotFoundRESTError(RESTException):
    """Invalid request body."""

    code = 204
    description = 'No such journal.'


class JournalUpdatedRESTError(RESTException):
    """Invalid request body."""

    code = 400
    description = 'Could not update data.'


class JournalAddedRESTError(RESTException):
    """Invalid request body."""

    code = 400
    description = 'Could not add data.'


class JournalMovedRESTError(RESTException):
    """Invalid request body."""

    code = 400
    description = 'Could not move data.'


"""Custom errors for weko index-tree journal."""

class WekoJournalError(Exception):
    def __init__(self, ex=None, msg=None, *args):
        """Constructor.

        Initialize the weko index-tree journal error.

        Args:
            ex (Exception): Original exception object
            msg (str): Error message
        """
        if ex is not None:
            self.exception = ex
        if msg is None:
            msg = "Some error has occurred in weko_indextree_journal."
        self.msg = msg
        super().__init__(msg, *args)


class WekoJournalSettingError(WekoJournalError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some setting error has occurred in weko_indextree_journal."
        super().__init__(ex, msg, *args)


class WekoJournalExportError(WekoJournalError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some export error has occurred in weko_indextree_journal."
        super().__init__(ex, msg, *args)


class WekoJournalRegistrarionError(WekoJournalError):
    def __init__(self, ex=None, msg=None, *args):
        if msg is None:
            msg = "Some registration error has occurred in weko_indextree_journal."
        super().__init__(ex, msg, *args)

