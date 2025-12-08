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
"""Enable logger login activity tracking."""

WEKO_ACCOUNTS_BASE_TEMPLATE = 'weko_accounts/base.html'
"""Default base template for the demo page."""

WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED = False
"""Enable Shibboleth user login system."""

WEKO_ACCOUNTS_SHIB_CACHE_PREFIX = 'Shib-Session-'
"""Shibboleth cache prefix info."""

WEKO_ACCOUNTS_SECURITY_LOGIN_USER_TEMPLATE = 'weko_accounts/login_user.html'
"""Default template for login."""

WEKO_ACCOUNTS_SECURITY_REGISTER_USER_TEMPLATE = 'weko_accounts/register_user.html'
"""Default template for user registration."""

WEKO_ACCOUNTS_SECURITY_LOGIN_SHIB_USER_TEMPLATE = 'weko_accounts/' \
    'login_shibuser_pattern_1.html'
"""Shibboleth template for login."""

WEKO_ACCOUNTS_SECURITY_LOGIN_SHIB_INST_TEMPLATE = 'weko_accounts/' \
    'login_shibuser_pattern_2.html'
"""Shibboleth template 2 for login."""

WEKO_ACCOUNTS_CONFIRM_USER_TEMPLATE = 'weko_accounts/confirm_user.html'
"""Default template for login."""

WEKO_ACCOUNTS_SET_SHIB_TEMPLATE = 'weko_accounts/setting/shibuser.html'
"""Control shibboleth user."""

WEKO_ACCOUNTS_STUB_USER_TEMPLATE = 'weko_accounts/shib_user.html'
"""Test page for shibboleth user login."""

WEKO_ACCOUNTS_SHIB_LOGIN_CACHE_TTL = 180
"""Cache default timeout 3 minute"""

WEKO_ACCOUNTS_SHIB_IDP_LOGIN_URL = '{}secure/login.php'
"""Login proxy URL."""

WEKO_ACCOUNTS_SSO_ATTRIBUTE_MAP = {
    'SHIB_ATTR_EPPN': (False, 'shib_eppn'),
    # "SHIB_ATTR_LOGIN_ID": (False, 'shib_uid'),
    # "SHIB_ATTR_HANDLE": (False, 'shib_handle'),
    'SHIB_ATTR_ROLE_AUTHORITY_NAME': (False, 'shib_role_authority_name'),
    'SHIB_ATTR_PAGE_NAME': (False, 'shib_page_name'),
    'SHIB_ATTR_ACTIVE_FLAG': (False, 'shib_active_flag'),
    'SHIB_ATTR_SITE_USER_WITHIN_IP_RANGE_FLAG': (False, 'shib_ip_range_flag'),
    'SHIB_ATTR_MAIL': (False, 'shib_mail'),
    'SHIB_ATTR_USER_NAME': (False, 'shib_user_name'),
    'SHIB_ATTR_ORGANIZATION': (False, 'shib_organization'),
}
"""IdP attribute map."""

WEKO_ACCOUNTS_SHIB_ROLE_RELATION = {
    '管理者': 'System Administrator',
    '図書館員': 'Repository Administrator',
    '教員': 'Contributor',
    '教官': 'Contributor',
    '事務局': 'Repository Administrator',
    '事務局２': 'Contributor',
    '学会員': 'IPSJ:学会員',
    '会誌購読員': '',
    '準登録個人': 'IPSJ:準登録個人',
    '準登録（団体）': '',
    '論文誌購読員': '',
    '賛助会員': '',
    '購読員': '',
    '非会員': '',
}
"""Role relation."""

WEKO_ACCOUNTS_GENERAL_ROLE = ''
"""Default role."""

WEKO_ACCOUNTS_SHIB_ROLE_ALL_USERS = ['非会員']
"""Roles given to all login users."""

WEKO_ACCOUNTS_SHIB_IDP_LOGIN_ENABLED = True
"""Shibboleth login pattern."""

WEKO_ACCOUNTS_SHIB_INST_LOGIN_DIRECTLY_ENABLED = True
"""Enable Shibboleth login system using IdP selection only."""

WEKO_ACCOUNTS_SHIB_DP_LOGIN_DIRECTLY_ENABLED = True
"""Enable Shibboleth login system using DP selection only."""

WEKO_ACCOUNTS_SHIB_ALLOW_USERNAME_INST_EPPN = True
"""Allow using SHIB_ATTR_USER_NAME instead of SHIB_ATTR_EPPN."""

WEKO_ACCOUNTS_SHIB_ALLOW_CREATE_GROUP_ROLE = True
"""Allow new role creation from SHIB_ATTR_PAGE_NAME (wekoSocietySubGroup) at shib login."""

WEKO_ACCOUNTS_LOGIN_LABEL = "Log in to account"
"""The login label"""

WEKO_ACCOUNTS_REGISTER_LABEL = "Sign up for a %(sitename)s account!"
"""The register label"""

WEKO_ACCOUNTS_REAL_IP = None # X-Real-IP > X-Forwarded-For[0] > remote_addr
# WEKO_ACCOUNTS_REAL_IP = "remote_add" # remote_addr
# WEKO_ACCOUNTS_REAL_IP = "x_real_ip" # X-Real-IP > remote_addr
# WEKO_ACCOUNTS_REAL_IP = "x_forwarded_for" # X-Forwarded-For[first] > remote_addr
# WEKO_ACCOUNTS_REAL_IP = "x_forwarded_for_rev" # X-Forwarded-For[last] > remote_addr

