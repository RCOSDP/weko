# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Records REST errors.

All error classes in this module are inheriting from
:class:`invenio_rest.errors.RESTException` or
:class:`invenio_rest.errors.RESTValidationError`.
"""

from __future__ import absolute_import, print_function

from flask import request
from invenio_rest.errors import RESTException, RESTValidationError


#
# Search
#
class MaxResultWindowRESTError(RESTException):
    """Maximum number of results have been reached."""

    code = 400
    description = 'Maximum number of results have been reached.'


#
# Query
#
class InvalidQueryRESTError(RESTException):
    """Invalid query syntax."""

    code = 400
    description = 'Invalid query syntax.'


#
# CiteProc
#
class StyleNotFoundRESTError(RESTException):
    """No such style."""

    code = 400

    def __init__(self, style=None, **kwargs):
        """Initialize exception."""
        super(RESTException, self).__init__(**kwargs)
        self.description = 'Style{0}could not be found.'.format(
            ' "{0}" '.format(style) if style else ' ')


#
# PID
#
class PIDRESTException(RESTException):
    """Base REST API PID exception class."""

    def __init__(self, pid_error=None, **kwargs):
        """Initialize exception."""
        super(RESTException, self).__init__(**kwargs)
        self.pid_error = pid_error


class PIDDoesNotExistRESTError(PIDRESTException):
    """Non-existent PID."""

    code = 404
    description = 'PID does not exist.'


class PIDUnregisteredRESTError(PIDRESTException):
    """Unregistered PID."""

    code = 404
    description = 'PID is not registered.'


class PIDDeletedRESTError(PIDRESTException):
    """Deleted PID."""

    code = 410
    description = 'PID has been deleted.'


class PIDMissingObjectRESTError(PIDRESTException):
    """PID missing object."""

    code = 500

    def __init__(self, pid, **kwargs):
        """Initialize exception."""
        super(PIDMissingObjectRESTError, self).__init__(**kwargs)
        self.description = 'No object assigned to {0}.'.format(pid)


class PIDRedirectedRESTError(PIDRESTException):
    """Invalid redirect for destination."""

    code = 500

    def __init__(self, pid_type=None, **kwargs):
        """Initialize exception."""
        super(PIDRedirectedRESTError, self).__init__(**kwargs)
        self.description = (
            'Invalid redirect - pid_type{0}endpoint missing.'.format(
                ' "{0}" '.format(pid_type) if pid_type else ' ')
        )


#
# Views
#
class PIDResolveRESTError(RESTException):
    """Invalid PID."""

    code = 500

    def __init__(self, pid=None, **kwargs):
        """Initialize exception."""
        super(RESTException, self).__init__(**kwargs)
        self.description = 'PID{0}could not be resolved.'.format(
            ' #{0} '.format(pid) if pid else ' ')


class UnsupportedMediaRESTError(RESTException):
    """Creating record with unsupported media type."""

    code = 415

    def __init__(self, content_type=None, **kwargs):
        """Initialize exception."""
        super(RESTException, self).__init__(**kwargs)
        content_type = content_type or request.mimetype
        self.description = 'Unsupported media type "{0}".'.format(content_type)


class InvalidDataRESTError(RESTException):
    """Invalid request body."""

    code = 400
    description = 'Could not load data.'


class PatchJSONFailureRESTError(RESTException):
    """Failed to patch JSON."""

    code = 400
    description = 'Could not patch JSON.'


class SuggestMissingContextRESTError(RESTException):
    """Missing a context value when getting record suggestions."""

    code = 400

    def __init__(self, ctx_field=None, **kwargs):
        """Initialize exception."""
        super(RESTException, self).__init__(**kwargs)
        self.description = 'Missing{0}context'.format(
            ' "{0}" '.format(ctx_field) if ctx_field else ' ')


class SuggestNoCompletionsRESTError(RESTException):
    """No completion requested when getting record suggestions."""

    code = 400

    def __init__(self, options=None, **kwargs):
        """Initialize exception."""
        super(RESTException, self).__init__(**kwargs)
        self.description = 'No completions requested.{0}'.format(
            ' (options: {0})'.format(options) if options else '')


class JSONSchemaValidationError(RESTValidationError):
    """JSONSchema validation error exception."""

    code = 400

    def __init__(self, error=None, **kwargs):
        """Initialize exception."""
        super(RESTValidationError, self).__init__(**kwargs)
        self.description = 'Validation error: {0}.'.format(
            error.message if error else '')


class UnhandledElasticsearchError(RESTException):
    """Failed to handle exception."""

    code = 500
    description = 'An internal server error occurred when handling the ' \
                  'request.'
