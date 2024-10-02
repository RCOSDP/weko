# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2024 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Utility function for ACCOUNTS."""

import enum
import re
import uuid
from datetime import datetime
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from flask import current_app, request, session, url_for
from flask_security import current_user
from flask_security.confirmable import generate_confirmation_token
from flask_security.recoverable import generate_reset_password_token
from flask_security.signals import password_changed, user_registered
from flask_security.utils import config_value as security_config_value
from flask_security.utils import get_security_endpoint_name, hash_password, send_mail
from invenio_db import db
from invenio_i18n import gettext as _
from jwt import DecodeError, ExpiredSignatureError, decode, encode
from werkzeug.routing import BuildError
from werkzeug.utils import import_string
from wtforms import ValidationError

from .errors import JWTDecodeError, JWTExpiredToken
from .proxies import current_datastore, current_security


class DomainStatus(enum.Enum):
    """Domain status.

    The domain status controls if new users can register and their verification status.
    """

    new = 1
    """User registration is allowed - new domain requiring review."""

    moderated = 2
    """User registration is allowed and users are automatically verified."""

    verified = 3
    """User registration is allowed and users are automatically verified."""

    blocked = 4
    """User registration from domain is blocked."""


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
        "exp": now + current_app.config["ACCOUNTS_JWT_EXPIRATION_DELTA"],
        "sub": user_id or current_user.get_id(),
        "jti": uid,
    }
    # Add any additional data to the token
    if additional_data is not None:
        token_data.update(additional_data)

    # Encode the token and send it back
    encoded_token = encode(
        token_data,
        current_app.config["ACCOUNTS_JWT_SECRET_KEY"],
        current_app.config["ACCOUNTS_JWT_ALOGORITHM"],
    )

    if not isinstance(encoded_token, str):
        # the token only needs to be decoded if it isn't a string already...
        encoded_token = encoded_token.decode("utf-8")

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
            current_app.config["ACCOUNTS_JWT_SECRET_KEY"],
            algorithms=[current_app.config["ACCOUNTS_JWT_ALOGORITHM"]],
        )
    except DecodeError as exc:
        raise JWTDecodeError() from exc
    except ExpiredSignatureError as exc:
        raise JWTExpiredToken() from exc


def set_session_info(app, response, **extra):
    """Add X-Session-ID and X-User-ID to http response."""
    session_id = getattr(session, "sid_s", None)
    if session_id:
        response.headers["X-Session-ID"] = session_id
    if current_user.is_authenticated:
        response.headers["X-User-ID"] = current_user.get_id()


def obj_or_import_string(value, default=None):
    """Import string or return object.

    :params value: Import path or class object to instantiate.
    :params default: Default object to return if the import fails.
    :returns: The imported object.
    """
    if isinstance(value, str):
        return import_string(value)
    elif value:
        return value
    return default


def _generate_token_url(endpoint, token):
    try:
        url = url_for(endpoint, token=token, _external=True)
    except BuildError:
        # Try to parse URL and build
        scheme, netloc, path, query, fragment = urlsplit(endpoint)
        scheme = scheme or request.scheme
        netloc = netloc or request.host
        assert netloc
        qs = parse_qs(query)
        if "{token}" in path:
            path = path.format(token=token)
        else:
            qs["token"] = token
        query = urlencode(qs)
        url = urlunsplit((scheme, netloc, path, query, fragment))
    return url


def default_reset_password_link_func(user):
    """Return the reset password link that will be sent to a user via email."""
    token = generate_reset_password_token(user)
    endpoint = current_app.config[
        "ACCOUNTS_RESET_PASSWORD_ENDPOINT"
    ] or get_security_endpoint_name("reset_password")
    return token, _generate_token_url(endpoint, token)


def default_confirmation_link_func(user):
    """Return the confirmation link that will be sent to a user via email."""
    token = generate_confirmation_token(user)
    endpoint = current_app.config[
        "ACCOUNTS_CONFIRM_EMAIL_ENDPOINT"
    ] or get_security_endpoint_name("confirm_email")
    return token, _generate_token_url(endpoint, token)


def register_user(_confirmation_link_func=None, send_register_msg=True, **user_data):
    """Register a user."""
    confirmation_link_func = _confirmation_link_func or default_confirmation_link_func
    if user_data.get("password") is not None:
        user_data["password"] = hash_password(user_data["password"])
    user = current_datastore.create_user(**user_data)
    current_datastore.commit()

    token, confirmation_link = None, None
    if current_security.confirmable and user.confirmed_at is None:
        token, confirmation_link = confirmation_link_func(user)

    user_registered.send(
        current_app._get_current_object(), user=user, confirm_token=token
    )

    if send_register_msg and security_config_value("SEND_REGISTER_EMAIL"):
        send_mail(
            security_config_value("EMAIL_SUBJECT_REGISTER"),
            user.email,
            "welcome",
            user=user,
            confirmation_link=confirmation_link,
        )

    return user


def change_user_password(_reset_password_link_func=None, **user_data):
    """Change user password."""
    reset_password_link_func = (
        _reset_password_link_func or default_reset_password_link_func
    )
    user = user_data["user"]
    user.password = None
    if user_data.get("password") is not None:
        user.password = hash_password(user_data["password"])
    current_datastore.put(user)
    if security_config_value("SEND_PASSWORD_CHANGE_EMAIL"):
        reset_password_link = None
        if current_security.recoverable:
            _, reset_password_link = reset_password_link_func(user)
        subject = security_config_value("EMAIL_SUBJECT_PASSWORD_CHANGE_NOTICE")
        send_mail(
            subject,
            user.email,
            "change_notice_rest",
            user=user,
            reset_password_link=reset_password_link,
        )
    password_changed.send(current_app._get_current_object(), user=user)


def validate_username(username):
    """Validate the username.

    :param username: The username to validate.
    :raises ValueError: If validation fails.
    """
    username_regex = current_app.config["ACCOUNTS_USERNAME_REGEX"]

    if not re.fullmatch(username_regex, username):
        # if validation fails, we raise a ValueError with the configured
        # text explaining the validation rules.
        message = current_app.config["ACCOUNTS_USERNAME_RULES_TEXT"]
        raise ValueError(message)


def validate_domain_form(form, field):
    """Validator for use with WTForm."""
    if not validate_domain(field.data):
        raise ValidationError(_("The email domain is blocked."))


def validate_domain(email):
    """Validate the domain of email address."""
    email = email.lower()
    try:
        prefix, domain = split_emailaddr(email)
    except ValueError:
        return False
    with db.session.no_autoflush:
        domain = current_datastore.find_domain(domain)
        if domain is not None and domain.status == DomainStatus.blocked:
            return False
        return True


def split_emailaddr(email):
    """Split email address in prefix and domain."""
    prefix, domain = email.rsplit("@", 1)
    prefix = prefix.lower().strip()
    domain = domain.lower().strip()
    if domain[-1] == ".":
        domain = domain[:-1]
    return prefix, domain
