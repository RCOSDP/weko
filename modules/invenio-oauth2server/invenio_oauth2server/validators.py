# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Validators for OAuth 2.0 redirect URIs and scopes."""

from flask import current_app
from oauthlib.oauth2.rfc6749.errors import (
    InsecureTransportError,
    InvalidRedirectURIError,
)
from six.moves.urllib_parse import urlparse
from wtforms.validators import URL

from .errors import ScopeDoesNotExists
from .proxies import current_oauth2server


def validate_redirect_uri(value):
    """Validate a redirect URI.

    Redirect URIs must be a valid URL and use https unless the host is
    localhost for which http is accepted.

    :param value: The redirect URI.
    """
    sch, netloc, path, par, query, fra = urlparse(value)
    if not (sch and netloc):
        raise InvalidRedirectURIError()
    if sch != "https":
        if ":" in netloc:
            netloc, port = netloc.split(":", 1)
        if not (netloc in ("localhost", "127.0.0.1") and sch == "http"):
            raise InsecureTransportError()


def validate_scopes(value_list):
    """Validate if each element in a list is a registered scope.

    :param value_list: The list of scopes.
    :raises invenio_oauth2server.errors.ScopeDoesNotExists: The exception is
        raised if a scope is not registered.
    :returns: ``True`` if it's successfully validated.
    """
    for value in value_list:
        if value not in current_oauth2server.scopes:
            raise ScopeDoesNotExists(value)
    return True


class URLValidator(URL):
    """URL validator."""

    def __call__(self, form, field):
        """Check URL."""
        parsed = urlparse(field.data)
        if current_app.debug and parsed.hostname == "localhost":
            return
        super(URLValidator, self).__call__(form=form, field=field)
