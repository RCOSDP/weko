# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Base configuration for weko-accounts."""

WEKO_ACCOUNTS_LOGGER_ENABLED = True
""" Enable logger login activity tracking. """

WEKO_ACCOUNTS_BASE_TEMPLATE = 'weko_accounts/base.html'
"""Default base template for the demo page."""

SHIB_ACCOUNTS_LOGIN_ENABLED = False
""" Enable Shibboleth user login system"""

SHIB_CACHE_PREFIX = 'Shib-Session-'
"""Shibboleth cache prefix info"""

SECURITY_LOGIN_USER_TEMPLATE = 'weko_accounts/login_user.html'
"""Default template for login."""

WEKO_ACCOUNTS_CONFIRM_USER_TEMPLATE = 'weko_accounts/confirm_user.html'
"""Default template for login."""

WEKO_ACCOUNTS_SET_SHIB_TEMPLATE = 'weko_accounts/setting/shibuser.html'
"""control shibboleth user."""

WEKO_ACCOUNTS_STUB_USER_TEMPLATE = 'weko_accounts/shib_user.html'
"""Test page for shibboleth user login."""

SHIB_ACCOUNTS_LOGIN_CACHE_TTL = 180
""" cache default timeout 3 minute"""

SHIB_IDP_LOGIN_URL = 'https://www.we50hitdev.com/secure/login.php'

SSO_ATTRIBUTE_MAP = {
    'SHIB_ATTR_EPPN': (True, 'shib_eppn'),
    # "SHIB_ATTR_LOGIN_ID": (False, "shib_uid"),
    # "SHIB_ATTR_HANDLE": (False, "shib_handle"),
    # "SHIB_ATTR_ROLE_AUTHORITY_NAME": (False, "shib_role_authority_name"),
    # "SHIB_ATTR_PAGE_NAME": (False, "shib_page_name"),
    # "SHIB_ATTR_ACTIVE_FLAG": (False, "shib_active_flag"),
    # "SHIB_ATTR_SITE_USER_WITHIN_IP_RANGE_FLAG": (False, "shib_ip_range_flag"),
    'SHIB_ATTR_MAIL': (False, 'shib_mail'),
    'SHIB_ATTR_USER_NAME': (False, 'shib_user_name'),
}
