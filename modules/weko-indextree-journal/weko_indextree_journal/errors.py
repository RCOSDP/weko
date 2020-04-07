# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# WEKO-Indextree-Journal is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

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
