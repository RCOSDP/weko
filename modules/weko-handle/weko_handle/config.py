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

WEKO_HANDLE_ALLOW_REGISTER_ARK = True
"""Allow registering ARK."""

BASE_ARK_ID_FOR_MINTER_USE = 'fk4w379'
"""A random valid ARK base identifier which will be minted inside EZID"""

WEKO_SERVER_CNRI_HOST_LINK = 'http://hdl.handle.net/'
"""Host server of CNRI"""