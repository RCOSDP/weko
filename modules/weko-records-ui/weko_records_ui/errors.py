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


class VersionNotFoundRESTError(RESTException):
    """API Version error."""

    code = 400
    description = _('This API version does not found.')

class InvalidEmailError(RESTException):
    """Invalid email Error error."""

    code = 400
    description = _('Invalid mailaddress.')

class InvalidTokenError(RESTException):
    """Invalid Token Error error."""

    code = 400
    description = _('Invalid Tokens.')
    
class InvalidWorkflowError(RESTException):
    """Contents not found error."""

    code = 403
    description =_("This data is not available for this user.")

class ContentsNotFoundError(RESTException):
    """Contents not found error."""

    code = 404
    description = _('Contents not found.')
    
class InternalServerError(RESTException):
    """Internal Server Error."""
    
    code = 500
    description = _('Internal Server Error.')