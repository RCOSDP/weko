# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Utility function for ACCOUNTS."""

import uuid
from datetime import datetime

from flask import current_app, session
from flask_security import current_user
from future.utils import raise_from
from jwt import DecodeError, ExpiredSignatureError, decode, encode

from .errors import JWTDecodeError, JWTExpiredToken
from .models import User, userrole, Role


def jwt_create_token(user_id=None, additional_data=None):
    """Encode the JWT token.

    :param int user_id: Addition of user_id.
    :param dict additional_data: Additional information for the token.
    :returns: The encoded token.
    :rtype: str

    .. note::
        Definition of the JWT claims:

        * exp: ((Expiration Time) expiration time of the JWT.
        * sub: (subject) the principal that is the subject of the JWT.
        * jti: (JWT ID) UID for the JWT.
    """
    # Create an ID
    uid = str(uuid.uuid4())
    # The time in UTC now
    now = datetime.utcnow()
    # Build the token data
    token_data = {
        'exp': now + current_app.config['ACCOUNTS_JWT_EXPIRATION_DELTA'],
        'sub': user_id or current_user.get_id(),
        'jti': uid,
    }
    # Add any additional data to the token
    if additional_data is not None:
        token_data.update(additional_data)

    # Encode the token and send it back
    encoded_token = encode(
        token_data,
        current_app.config['ACCOUNTS_JWT_SECRET_KEY'],
        current_app.config['ACCOUNTS_JWT_ALOGORITHM']
    ).decode('utf-8')
    return encoded_token


def jwt_decode_token(token):
    """Decode the JWT token.

    :param str token: Additional information for the token.
    :returns: The token data.
    :rtype: dict
    """
    try:
        return decode(
            token,
            current_app.config['ACCOUNTS_JWT_SECRET_KEY'],
            algorithms=[
                current_app.config['ACCOUNTS_JWT_ALOGORITHM']
            ]
        )
    except DecodeError as exc:
        raise_from(JWTDecodeError(), exc)
    except ExpiredSignatureError as exc:
        raise_from(JWTExpiredToken(), exc)


def set_session_info(app, response, **extra):
    """Add X-Session-ID and X-User-ID to http response."""
    session_id = getattr(session, 'sid_s', None)
    if session_id:
        response.headers['X-Session-ID'] = session_id
    if current_user.is_authenticated:
        response.headers['X-User-ID'] = current_user.get_id()


def get_user_ids_by_role(role_id):
    """Get user IDs by role ID.

    Args:
        role_id (int): The ID of the role.

    Returns:
        list: A list of user IDs associated with the given role.
    """
    return [str(user.id) for user in User.query.join(userrole).join(Role).filter(Role.id == role_id).all()]
