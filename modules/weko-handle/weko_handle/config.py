# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# WEKO-Handle is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-handle."""

# extra configuration variables.

WEKO_HANDLE_BASE_TEMPLATE = 'weko_handle/base.html'
"""Default base template for the demo page."""

WEKO_HANDLE_CREDS_JSON_PATH = '/code/modules/resources/handle_creds.json'
"""Default dir contain Handle Cred Json."""

WEKO_HANDLE_ALLOW_REGISTER_CNRI = False
"""Allow registering CNRI."""

WEKO_HANDLE_ALLOW_REGISTER_ARK = False
"""Allow registering ARK."""

WEKO_HANDLE_ARK_LOGIN_URL = None
""" Login URL for ARK server."""

WEKO_HANDLE_ARK_LOGIN_USER = None
""" Login user for ARK server."""

WEKO_HANDLE_ARK_LOGIN_PASSWD = None
""" Login password for ARK server."""

WEKO_HANDLE_ARK_MINT_URL = None
"""" MINT URL for ARK server."""

WEKO_HANDLE_ARK_NAAN = None
""" NAAN of Ark """

WEKO_HANDLE_ARK_SHOULDER = None
""" Shoulder of Ark """

WEKO_HANDLE_ARK_TIMEOUT = 30
""" Timeout in seconds for each request to the ARK server."""




WEKO_HANDLE_ARK_API_KEY = None
""" API key for ARK server.

When set, the login request to WEKO_HANDLE_ARK_LOGIN_URL is skipped and
the key is sent with every mint request instead.
"""

WEKO_HANDLE_ARK_API_KEY_HEADER = 'Authorization'
""" Header name the ARK API key is sent in.

Use 'X-API-Key' together with an empty WEKO_HANDLE_ARK_API_KEY_PREFIX for
servers expecting a bare key header.
"""

WEKO_HANDLE_ARK_API_KEY_PREFIX = 'Bearer '
""" Prefix prepended to the ARK API key. Set to '' to send a bare key."""
