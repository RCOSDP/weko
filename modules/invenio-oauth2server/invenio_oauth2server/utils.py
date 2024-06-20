# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Utility functions."""

from flask import current_app
from flask_login import current_user
from future.utils import raise_from
from invenio_accounts.errors import JWTDecodeError as _JWTDecodeError
from invenio_accounts.errors import JWTExpiredToken as _JWTExpiredToken
from invenio_accounts.utils import jwt_decode_token
from invenio_db.utils import rebuild_encrypted_properties

from .errors import (
    JWTDecodeError,
    JWTExpiredToken,
    JWTInvalidHeaderError,
    JWTInvalidIssuer,
)
from .models import Token


def rebuild_access_tokens(old_key):
    """Rebuild the access_token field when the SECRET_KEY is changed.

    Needed to fix the access tokens used in the REST API calls.

    :param old_key: the old SECRET_KEY.
    """
    current_app.logger.info("rebuilding Token.access_token...")
    rebuild_encrypted_properties(old_key, Token, ["access_token", "refresh_token"])


def jwt_verify_token(headers):
    """Verify the JWT token.

    :param dict headers: The request headers.
    :returns: The token data.
    :rtype: dict
    """
    # Get the token from headers
    token = headers.get(current_app.config["OAUTH2SERVER_JWT_AUTH_HEADER"])
    if token is None:
        raise JWTInvalidHeaderError
    # Get authentication type
    authentication_type = current_app.config["OAUTH2SERVER_JWT_AUTH_HEADER_TYPE"]
    # Check if the type should be checked
    if authentication_type is not None:
        # Get the prefix and the token
        prefix, token = token.split()
        # Check if the type matches
        if prefix != authentication_type:
            raise JWTInvalidHeaderError

    try:
        # Get the token data
        decode = jwt_decode_token(token)
        # Check the integrity of the user
        if current_user.get_id() != decode.get("sub"):
            raise JWTInvalidIssuer
        return decode
    except _JWTDecodeError as exc:
        raise_from(JWTDecodeError(), exc)
    except _JWTExpiredToken as exc:
        raise_from(JWTExpiredToken(), exc)
