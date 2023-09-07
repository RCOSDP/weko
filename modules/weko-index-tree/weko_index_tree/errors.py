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
from invenio_rest.errors import RESTException

# from flask_babelex import gettext as _


SUCCESS_MSG = 'Index deleted successfully.'
FAILED_MSG = ''


class IndexBaseRESTError(RESTException):
    """Invalid request body."""

    code = 400


class InvalidDataRESTError(RESTException):
    """Invalid request body."""

    code = 400
    description = 'Could not load data.'


class IndexDeletedRESTError(RESTException):
    """Invalid request body."""

    code = 204
    description = 'This index has been deleted.'


class IndexNotFoundRESTError(RESTException):
    """Invalid request body."""

    code = 204
    description = 'No such index.'


class IndexUpdatedRESTError(RESTException):
    """Index ujpdated rest error."""

    code = 400
    description = 'Could not update data.'


class IndexAddedRESTError(RESTException):
    """Index added REST error."""

    code = 400
    description = 'Could not add data.'


class IndexMovedRESTError(RESTException):
    """Index moved rest error."""

    code = 400
    description = 'Could not move data.'


class VersionNotFoundRESTError(RESTException):
    """API Version error."""

    code = 400
    description = 'This API version does not found'


class PermissionError(RESTException):
    """Permission error"""

    code = 403
    description = 'Permission denied'


class IndexNotFound404Error(RESTException):
    """Index not found."""

    code = 404
    description = 'No such index.'


class InternalServerError(RESTException):
    """Internal Server Error."""

    code = 500
    description = 'Internal Server Error'
