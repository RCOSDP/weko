# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""OAuth2Server configuration variables."""

OAUTH2_CACHE_TYPE = "redis"
"""Type of cache to use for storing the temporary grant token."""

OAUTH2_PROVIDER_ERROR_ENDPOINT = "invenio_oauth2server.errors"
"""Error view endpoint."""

OAUTH2SERVER_CLIENT_ID_SALT_LEN = 40
"""Length of client id."""

OAUTH2SERVER_CLIENT_SECRET_SALT_LEN = 60
"""Length of the client secret."""

OAUTH2SERVER_TOKEN_PERSONAL_SALT_LEN = 60
"""Length of the personal access token."""

OAUTH2SERVER_ALLOWED_GRANT_TYPES = {
    "authorization_code",
    "client_credentials",
    "refresh_token",
}
"""A set of allowed grant types.

The allowed values are ``authorization_code``, ``password``,
``client_credentials``, ``refresh_token``). By default password is disabled,
as it requires the client application to gain access to the username and
password of the resource owner.
"""

OAUTH2SERVER_ALLOWED_RESPONSE_TYPES = {
    "code",
    "token",
}
"""A set of allowed response types.

The allowed values are ``code`` and ``token``.

- ``code`` is used for authorization_code grant types
- ``token`` is used for implicit grant types
"""

OAUTH2SERVER_ALLOWED_URLENCODE_CHARACTERS = "=&;:%+~,*@!()/?"
"""A string of special characters that should be valid inside a query string.

.. seealso::

    See :py:func:`monkeypatch_oauthlib_urlencode_chars
    <invenio_oauth2server.ext.InvenioOAuth2ServerREST.monkeypatch_oauthlib_urlencode_chars>`
    for a full explanation.
"""

OAUTH2SERVER_JWT_AUTH_HEADER = "Authorization"
"""Header for the JWT.

.. note::

    Authorization: Bearer xxx
"""

OAUTH2SERVER_JWT_AUTH_HEADER_TYPE = "Bearer"
"""Header Authorization type.

.. note::

    By default the authorization type is ``Bearer`` as recommented by
    `JWT  <https://jwt.io>`_
"""

OAUTH2SERVER_JWT_VERIFICATION_FACTORY = "invenio_oauth2server.utils:" "jwt_verify_token"
"""Import path of factory used to verify JWT.

The ``request.headers`` should be passed as parameter.
"""
