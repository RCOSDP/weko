# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

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
