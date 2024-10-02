# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Useful decorators for checking authentication and scopes."""

from functools import wraps

from flask import abort, current_app, request
from flask_login import current_user

from .provider import oauth2
from .proxies import current_oauth2server


def require_api_auth(allow_anonymous=False):
    """Decorator to require API authentication using OAuth token.

    :param allow_anonymous: Allow access without OAuth token
        (default: ``False``).
    """

    def wrapper(f):
        """Wrap function with oauth require decorator."""
        f_oauth_required = oauth2.require_oauth()(f)

        @wraps(f)
        def decorated(*args, **kwargs):
            """Require OAuth 2.0 Authentication."""
            if not hasattr(current_user, "login_via_oauth2"):
                if not current_user.is_authenticated:
                    if allow_anonymous:
                        return f(*args, **kwargs)
                    abort(401)
                if current_app.config["ACCOUNTS_JWT_ENABLE"]:
                    # Verify the token
                    current_oauth2server.jwt_verification_factory(request.headers)
                # fully logged in with normal session
                return f(*args, **kwargs)
            else:
                # otherwise, try oauth2
                return f_oauth_required(*args, **kwargs)

        return decorated

    return wrapper


def require_oauth_scopes(*scopes):
    r"""Decorator to require a list of OAuth scopes.

    Decorator must be preceded by a ``require_api_auth()`` decorator.
    Note, API key authentication is bypassing this check.

    :param \*scopes: List of scopes required.
    """
    required_scopes = set(scopes)

    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Variable requests.oauth is only defined for oauth requests (see
            # require_api_auth() above).
            if hasattr(request, "oauth") and request.oauth is not None:
                token_scopes = set(request.oauth.access_token.scopes)
                if not required_scopes.issubset(token_scopes):
                    abort(403)
            return f(*args, **kwargs)

        return decorated

    return wrapper
