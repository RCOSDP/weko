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

from flask import request
from invenio_rest.errors import FieldError, RESTException, RESTValidationError


#
# Search
#
class SearchPaginationRESTError(RESTException):
    """Search pagination error."""

    code = 400

    def __init__(self, errors=None, **kwargs):
        """Initialize exception."""
        _errors = []
        if errors:
            for field, messages in errors.items():
                _errors.extend([FieldError(field, msg) for msg in messages])
        super().__init__(errors=_errors, **kwargs)


#
# Query
#
class InvalidQueryRESTError(RESTException):
    """Invalid query syntax."""

    code = 400
    description = "Invalid query syntax."


#
# CiteProc
#
class StyleNotFoundRESTError(RESTException):
    """No such style."""

    code = 400

    def __init__(self, style=None, **kwargs):
        """Initialize exception."""
        super().__init__(**kwargs)
        arg = f' "{style}" ' if style else " "
        self.description = f"Style{arg}could not be found."


#
# PID
#
class PIDRESTException(RESTException):
    """Base REST API PID exception class."""

    def __init__(self, pid_error=None, **kwargs):
        """Initialize exception."""
        super().__init__(**kwargs)
        self.pid_error = pid_error


class PIDDoesNotExistRESTError(PIDRESTException):
    """Non-existent PID."""

    code = 404
    description = "PID does not exist."


class PIDUnregisteredRESTError(PIDRESTException):
    """Unregistered PID."""

    code = 404
    description = "PID is not registered."


class PIDDeletedRESTError(PIDRESTException):
    """Deleted PID."""

    code = 410
    description = "PID has been deleted."


class PIDMissingObjectRESTError(PIDRESTException):
    """PID missing object."""

    code = 500

    def __init__(self, pid, **kwargs):
        """Initialize exception."""
        super().__init__(**kwargs)
        self.description = f"No object assigned to {pid}."


class PIDRedirectedRESTError(PIDRESTException):
    """Invalid redirect for destination."""

    code = 500

    def __init__(self, pid_type=None, **kwargs):
        """Initialize exception."""
        super().__init__(**kwargs)
        arg = f' "{pid_type}" ' if pid_type else " "
        self.description = f"Invalid redirect - pid_type{arg}endpoint missing."


#
# Views
#
class PIDResolveRESTError(RESTException):
    """Invalid PID."""

    code = 500

    def __init__(self, pid=None, **kwargs):
        """Initialize exception."""
        super().__init__(**kwargs)
        arg = f" #{pid} " if pid else " "
        self.description = f"PID{arg}could not be resolved."


class UnsupportedMediaRESTError(RESTException):
    """Creating record with unsupported media type."""

    code = 415

    def __init__(self, content_type=None, **kwargs):
        """Initialize exception."""
        super().__init__(**kwargs)
        content_type = content_type or request.mimetype
        self.description = f'Unsupported media type "{content_type}".'


class InvalidDataRESTError(RESTException):
    """Invalid request body."""

    code = 400
    description = "Could not load data."


class PatchJSONFailureRESTError(RESTException):
    """Failed to patch JSON."""

    code = 400
    description = "Could not patch JSON."


class SuggestMissingContextRESTError(RESTException):
    """Missing a context value when getting record suggestions."""

    code = 400

    def __init__(self, ctx_field=None, **kwargs):
        """Initialize exception."""
        super().__init__(**kwargs)
        arg = f' "{ctx_field}" ' if ctx_field else " "
        self.description = f"Missing{arg}context"


class SuggestNoCompletionsRESTError(RESTException):
    """No completion requested when getting record suggestions."""

    code = 400

    def __init__(self, options=None, **kwargs):
        """Initialize exception."""
        super().__init__(**kwargs)
        arg = f" (options: {options})" if options else ""
        self.description = f"No completions requested.{arg}"


class JSONSchemaValidationError(RESTValidationError):
    """JSONSchema validation error exception."""

    code = 400

    def __init__(self, error=None, **kwargs):
        """Initialize exception."""
        super().__init__(**kwargs)
        error = error.message if error else ""
        self.description = f"Validation error: {error}."


class UnhandledSearchError(RESTException):
    """Failed to handle exception."""

    code = 500
    description = "An internal server error occurred when handling the request."
