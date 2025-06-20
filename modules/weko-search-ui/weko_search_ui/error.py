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

"""Search Error"""
from invenio_rest.errors import RESTException, RESTValidationError

class VersionNotFoundRESTError(RESTException):
    """API Version error."""

    code = 400
    description = 'This API version does not found'

class InvalidRequestError(RESTException):
    """Invalid Request error."""

    code = 400
    description = 'Invalid Request Header or Body'

class InternalServerError(RESTException):
    """Internal Server Error."""

    code = 500
    description = 'Internal Server Error'

class UnhandledElasticsearchError(RESTException):
    """Failed to handle exception."""

    code = 500
    description = 'An internal server error occurred when handling the ' \
                  'request.'