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
# from flask_babelex import gettext as _

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
    code = 400
    description = 'Could not update data.'


class JournalAddedRESTError(RESTException):
    code = 400
    description = 'Could not add data.'


class JournalMovedRESTError(RESTException):
    code = 400
    description = 'Could not move data.'
