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

WEKO_ACCOUNTS_SHIB_IDP_LOGIN_URL = '{}secure/login.py'
"""Login proxy URL."""

WEKO_ACCOUNTS_SSO_ATTRIBUTE_MAP = {
    'SHIB_ATTR_EPPN': (False, 'shib_eppn'),
    # 'SHIB_ATTR_LOGIN_ID': (False, 'shib_uid'),
    # 'SHIB_ATTR_HANDLE': (False, 'shib_handle'),
    'SHIB_ATTR_ROLE_AUTHORITY_NAME': (False, 'shib_role_authority_name'),
    # 'SHIB_ATTR_PAGE_NAME': (False, 'shib_page_name'),
    # 'SHIB_ATTR_ACTIVE_FLAG': (False, 'shib_active_flag'),
    'SHIB_ATTR_SITE_USER_WITHIN_IP_RANGE_FLAG': (False, 'shib_ip_range_flag'),
    'SHIB_ATTR_MAIL': (False, 'shib_mail'),
    'SHIB_ATTR_USER_NAME': (False, 'shib_user_name'),
}
"""IdP attribute map."""

WEKO_ACCOUNTS_ATTRIBUTE_MAP = {
    'shib_eppn': 'eppn',
    'shib_role_authority_name': 'eduPersonAffiliation',
    'shib_mail': 'mail',
    'shib_user_name': 'DisplayName'
}
"""IdP attribute map."""

WEKO_ACCOUNTS_ATTRIBUTE_LIST = [
    'eppn',
    'DisplayName',
    'mail',
    'eduPersonOrcid',
    'jasn',
    'jaGivenName',
    'jaDisplayName',
    'jao',
    'jaou',
    'isMemberOf',
    'sn',
    'o',
    'ou',
    'givenName',
    'eduPersonAffiliation',
    'eduPersonScopedAffiliation',
    'eduPersonTargetedID'
]
"""Attribute List."""

WEKO_ACCOUNTS_ROLE_LIST = [
    'System Administrator', 
    'Repository Administrator', 
    'Community Administrator', 
    'Contributor', 
    'None'
]
"""Role List."""

WEKO_ACCOUNTS_GENERAL_ROLE = 'Contributor'
"""Default role."""

WEKO_ACCOUNTS_GAKUNIN_ROLE = {
  'defaultRole': 'Contributor',
  'organizationName': []  
} 
"""Gakunin Default role."""

WEKO_ACCOUNTS_ORTHROS_INSIDE_ROLE = {
  'defaultRole': 'Repository Administrator',
  'organizationName': []  
} 
"""Orthros (Inside) Default role."""

WEKO_ACCOUNTS_ORTHROS_OUTSIDE_ROLE = {
  'defaultRole': 'Community Administrator',
  'organizationName': []  
} 
"""Orthros (Outside) Default role."""

WEKO_ACCOUNTS_EXTRA_ROLE = {
  'defaultRole': 'None', # ロール無
  'organizationName': []  
} 
"""Extra Default role."""

WEKO_ACCOUNTS_SHIB_ROLE_RELATION = {
    '管理者': 'System Administrator',
    '学認IdP': WEKO_ACCOUNTS_GAKUNIN_ROLE['defaultRole'],
    '機関内のOrthros': WEKO_ACCOUNTS_ORTHROS_INSIDE_ROLE['defaultRole'],
    '機関外のOrthros': WEKO_ACCOUNTS_ORTHROS_OUTSIDE_ROLE['defaultRole'],
    'その他': WEKO_ACCOUNTS_EXTRA_ROLE['defaultRole']
}
"""Role relation."""

WEKO_ACCOUNTS_SHIB_IDP_LOGIN_ENABLED = True
"""Shibboleth login pattern."""

WEKO_ACCOUNTS_SHIB_INST_LOGIN_DIRECTLY_ENABLED = True
"""Enable Shibboleth login system using IdP selection only."""

WEKO_ACCOUNTS_SHIB_DP_LOGIN_DIRECTLY_ENABLED = True
"""Enable Shibboleth login system using DP selection only."""

WEKO_ACCOUNTS_SHIB_ALLOW_USERNAME_INST_EPPN = True
"""Allow using SHIB_ATTR_USER_NAME instead of SHIB_ATTR_EPPN."""
WEKO_ACCOUNTS_LOGIN_LABEL = 'Log in to account'
"""The login label"""

WEKO_ACCOUNTS_REGISTER_LABEL = 'Sign up for a %(sitename)s account!'
"""The register label"""

WEKO_ACCOUNTS_REAL_IP = None # X-Real-IP > X-Forwarded-For[0] > remote_addr
# WEKO_ACCOUNTS_REAL_IP = 'remote_add' # remote_addr
# WEKO_ACCOUNTS_REAL_IP = 'x_real_ip' # X-Real-IP > remote_addr
# WEKO_ACCOUNTS_REAL_IP = 'x_forwarded_for' # X-Forwarded-For[first] > remote_addr
# WEKO_ACCOUNTS_REAL_IP = 'x_forwarded_for_rev' # X-Forwarded-For[last] > remote_addr

WEKO_ACCOUNTS_REST_ENDPOINTS = {
    'login': {
        'route': '/<string:version>/login',
        'default_media_type': 'application/json',
    },
    'logout': {
        'route': '/<string:version>/logout',
        'default_media_type': 'application/json',
    },
}

WEKO_API_LIMIT_RATE_DEFAULT = ['100 per minute']
"""Default rate limit per endpoint for one user in the WEKO API."""


WEKO_ACCOUNTS_SKIP_CONFIRMATION_PAGE = False
"""Skip shibboleth confirmation page."""

WEKO_ACCOUNTS_IDP_ENTITY_ID = ''
"""IdP entity ID that institution owned."""

WEKO_ACCOUNTS_GAKUNIN_DEFAULT_GROUP_MAPPING = {}
# {
#     "http://idp.example.org/idp/shibboleth": [
#        "jc_role_sysadm", "jc_role_repoadm", "jc_role_comadm"],
#}

WEKO_ACCOUNTS_SHIB_BIND_GAKUNIN_MAP_GROUPS = False

WEKO_ACCOUNTS_GAKUNIN_GROUP_SUFFIX = "_gakunin_groups"

WEKO_ACCOUNTS_GAKUNIN_GROUP_PATTERN_DICT = {
    "prefix":"jc",
    "sysadm_group":"jc_roles_sysadm",
    "role_keyword":"roles",
    "role_mapping":{
        "repoadm":"Repository_Administrator",
        "comadm":"Community_Administrator",
        "contributor":"Contributor",
    }
}

WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_BROWSING_PERMISSION =False
"""閲覧権限のデフォルト権限を設定する"""

WEKO_INDEXTREE_GAKUNIN_GROUP_DEFAULT_CONTRIBUTE_PERMISSION = False
"""投稿権限のデフォルト権限を設定する"""

WEKO_ACCOUNTS_GAKUNIN_USER_NAME_PREFIX = 'G_'
"""Prefix for Gakunin user name."""

WEKO_ACCOUNTS_SHIB_USER_NAME_NO_HASH_LENGTH = 253
"""Length of Shibboleth user name without hash value."""
