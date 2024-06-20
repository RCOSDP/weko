# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
# Copyright (C) 2022 RERO.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Errors raised by Invenio-OAuth2Server."""

import json

from werkzeug.exceptions import HTTPException


class OAuth2ServerError(Exception):
    """Base class for errors in oauth2server module."""


class ScopeDoesNotExists(OAuth2ServerError):
    """Scope is not registered it scopes registry."""

    def __init__(self, scope, *args, **kwargs):
        """Initialize exception by storing invalid scope."""
        super(ScopeDoesNotExists, self).__init__(*args, **kwargs)
        self.scope = scope


class JWTExtendedException(HTTPException):
    """Base exception for all JWT errors."""

    errors = None

    def __init__(self, errors=None, **kwargs):
        """Initialize JWTExtendedException."""
        super(JWTExtendedException, self).__init__(**kwargs)

        if errors is not None:
            self.errors = errors

    def get_errors(self):
        """Get errors.

        :returns: A list containing a dictionary representing the errors.
        """
        return [e.to_dict() for e in self.errors] if self.errors else None

    def get_body(self, environ=None, scope=None):
        """Get the request body."""
        body = dict(
            status=self.code,
            message=self.description,
        )

        errors = self.get_errors()
        if self.errors:
            body["errors"] = errors

        return json.dumps(body)

    def get_headers(self, environ=None, scope=None):
        """Get a list of headers."""
        return [("Content-Type", "application/json")]


class JWTDecodeError(JWTExtendedException):
    """Exception raised when decoding is failed."""

    code = 400
    description = "The JWT token has invalid format."


class JWTInvalidIssuer(JWTExtendedException):
    """Exception raised when the user is not valid."""

    code = 403
    description = "The JWT token is not valid."


class JWTExpiredToken(JWTExtendedException):
    """Exception raised when JWT is expired."""

    code = 403
    description = "The JWT token is expired."


class JWTInvalidHeaderError(JWTExtendedException):
    """Exception raised when header argument is missing."""

    code = 400
    description = "Missing required header argument."


class JWTNoAuthorizationError(JWTExtendedException):
    """Exception raised when permission denied."""

    code = 400
    description = "The JWT token is not valid."
