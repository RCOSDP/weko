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

"""Configuration for weko-theme."""
BASE_PAGE_TEMPLATE = 'weko_theme/page.html'
"""Base template for user facing pages."""

BASE_EDIT_TEMPLATE = 'weko_theme/edit.html'
"""Base template for user facing pages.

The template provides a basic skeleton which takes care of loading assets,
embedding header metadata and define basic template blocks. All other user
facing templates usually extends from this template and thus changing this
template allows to change design and layout of WEKO3.
"""

THEME_HEADER_TEMPLATE = 'weko_theme/header.html'
"""Header template which is normally included in :data:`BASE_TEMPLATE`."""

THEME_HEADER_EDITOR_TEMPLATE = 'weko_theme/header_editor.html'
"""Header editor template."""

THEME_HEADER_WYSIWYG_TEMPLATE = 'weko_theme/header_wysiwyg.html'
"""Header wysiwyg template."""

THEME_HEADER_LOGIN_TEMPLATE = 'weko_theme/header_login.html'
"""Header login template, included in :data:`THEME_HEADER_TEMPLATE`."""

THEME_BODY_TEMPLATE = 'weko_theme/body.html'
"""Body template which is normally included in :data:`BASE_TEMPLATE`."""

THEME_LOGO = 'images/weko-logo.png'
"""The logo to be used on the header and on the cover."""

THEME_LOGO_ADMIN = 'images/weko-logo.png'
"""The logo to be used on the admin views header."""

THEME_URL_LOGO_ADMIN = '/'
"""The url of admin logo"""

THEME_FOOTER_TEMPLATE = 'weko_theme/footer.html'
"""Footer template which is normally included in :data:`BASE_TEMPLATE`."""

THEME_FOOTER_EDITOR_TEMPLATE = 'weko_theme/footer_editor.html'
"""Footer editor template."""

THEME_FOOTER_WYSIWYG_TEMPLATE = 'weko_theme/footer_wysiwyg.html'
"""Footer wysiwyg template."""

THEME_SITENAME = 'WEKO3'
"""The name of the site to be used on the header and as a title."""

THEME_SITEURL = 'https://localhost'
"""The URL displayed in the sitemap. Change it to self domain name."""

THEME_SEARCHBAR = True
"""Enable or disable the search bar."""

THEME_FRONTPAGE_TEMPLATE = 'weko_theme/frontpage.html'
"""Template for front page."""

WEKO_THEME_DEFAULT_COMMUNITY = 'Root Index'
"""Default community identifier."""

WEKO_THEME_ADMIN_ITEM_MANAGEMENT_INIT_TEMPLATE = \
    'weko_theme/admin/item_management_init.html'
"""Template for Item Management."""

WEKO_THEME_ADMIN_ITEM_MANAGEMENT_TEMPLATE = \
    'weko_theme/admin/item_management_display.html'
"""Template for Admin Item Management."""

ADMIN_BASE_TEMPLATE = 'weko_theme/page_admin.html'

SETTINGS_TEMPLATE = 'weko_theme/page_setting.html'

COVER_TEMPLATE = 'weko_theme/page_cover.html'

WEKO_THEME_INSTANCE_DATA_DIR = 'data'
"""ユーザーデータのィレクトリ."""

WEKO_THEME_ADMIN_MENU = [
    {
        'name': 'Home',
        'order': 1
    },
    {
        'name': 'ホーム',
        'order': 1
    },
    {
        'name': 'Author Management',
        'order': 6,
        'submenu': [
            {
                'name': 'Edit',
                'order': 1
            },
            {
                'name': 'Export',
                'order': 2
            },
            {
                'name': 'Import',
                'order': 3
            }
        ]
    },
    {
        'name': 'Communities',
        'order': 9,
        'submenu': [
            {
                'name': 'Community',
                'order': 1
            },
            {
                'name': 'Inclusion Request',
                'order': 2
            }
        ]
    },
    {
        'name': 'Files',
        'order': 13,
        'submenu': [
            {
                'name': 'Bucket',
                'order': 1
            },
            {
                'name': 'File Instance',
                'order': 2
            },
            {
                'name': 'Location',
                'order': 3
            },
            {
                'name': 'Multipart Object',
                'order': 4
            },
            {
                'name': 'Object Version',
                'order': 5
            }
        ]
    },
    {
        'name': 'Index Tree',
        'order': 4,
        'submenu': [
            {
                'name': 'Custom Sort',
                'order': 3
            },
            {
                'name': 'Edit Tree',
                'order': 1
            },
            {
                'name': 'Journal Information',
                'order': 2
            }
        ]
    },
    {
        'name': 'Item Types',
        'order': 2,
        'submenu': [
            {
                'name': 'Metadata',
                'order': 1
            },
            {
                'name': 'Mapping',
                'order': 2
            },
            {
                'name': 'OAI Schema',
                'order': 3
            },
            {
                'name': 'Properties',
                'order': 4
            },
            {
                'name': 'JSON-LD mapping',
                'order': 5
            },
            {
                'name': 'RO-Crate mapping',
                'order': 6
            }
        ]
    },
    {
        'name': 'Items',
        'order': 3,
        'submenu': [
            {
                'name': 'Bulk Delete',
                'order': 2
            },
            {
                'name': 'Bulk Export',
                'order': 3
            },
            {
                'name': 'Bulk Update',
                'order': 1
            },
            {
                'name': 'Import',
                'order': 4
            },
            {
                'name': 'RO-Crate Import',
                'order': 5
            }
        ]
    },
    {
        'name': 'OAI-PMH',
        'order': 10,
        'submenu': [
            {
                'name': 'Harvesting',
                'order': 1
            },
            {
                'name': 'Identify',
                'order': 2
            },
            {
                'name': 'Sets',
                'order': 3
            }
        ]
    },
    {
        'name': 'Records',
        'order': 13,
        'submenu': [
            {
                'name': 'Persistent Identifier',
                'order': 1
            },
            {
                'name': 'Record Metadata',
                'order': 2
            }
        ]
    },
    {
        'name': 'SWORD API',
        'order': 12,
        'submenu': [
            {
                'name': 'TSV/XML',
                'order': 1
            },
            {
                'name': 'JSON-LD',
                'order': 2
            }
        ]
    },
    {
        'name': 'Resource Sync',
        'order': 11,
        'submenu': [
            {
                'name': 'Change List',
                'order': 2
            },
            {
                'name': 'Resource List',
                'order': 1
            },
            {
                'name': 'Resync',
                'order': 3
            }
        ]
    },
    {
        'name': 'Setting',
        'order': 16,
        'submenu': [
            {
                'name': 'Items',
                'order': 1
            },
            {
                'name': 'Activity',
                'order': 2
            },
            {
                'name': 'Index Link',
                'order': 3
            },
            {
                'name': 'Language',
                'order': 4
            },
            {
                'name': 'PDF Cover Page',
                'order': 5
            },
            {
                'name': 'Ranking',
                'order': 6
            },
            {
                'name': 'Stats',
                'order': 7
            },
            {
                'name': 'Style',
                'order': 8
            },
            {
                'name': 'Identifier',
                'order': 9
            },
            {
                'name': 'Item Export',
                'order': 10
            },
            {
                'name': 'Log Analysis',
                'order': 11
            },
            {
                'name': 'Search',
                'order': 12
            },
            {
                'name': 'Faceted Search',
                'order': 13
            },
            {
                'name': 'Site Info',
                'order': 14
            },
            {
                'name': 'Site License',
                'order': 15
            },
            {
                'name': 'Sitemap',
                'order': 16
            },
            {
                'name': 'Mail',
                'order': 17
            },
            {
                'name': 'WebAPI Account',
                'order': 18
            },
            {
                'name': 'File Preview',
                'order': 19
            },
            {
                'name': 'Shibboleth',
                'order': 20
            },
            {
                'name': 'Restricted Access',
                'order': 21
            },
            {
                'name': 'Others',
                'order': 22
            }
        ]
    },
    {
        'name': 'Statistics',
        'order': 7,
        'submenu': [
            {
                'name': 'Feedback Mail',
                'order': 2
            },
            {
                'name': 'Report',
                'order': 1
            },
            {
                'name': 'Site License',
                'order': 3
            }
        ]
    },
    {
        'name': 'User Management',
        'order': 15,
        'submenu': [
            {
                'name': 'Access: Roles',
                'order': 1
            },
            {
                'name': 'Access: System Roles',
                'order': 2
            },
            {
                'name': 'Access: Users',
                'order': 3
            },
            {
                'name': 'Linked account identities',
                'order': 4
            },
            {
                'name': 'Linked account tokens',
                'order': 5
            },
            {
                'name': 'Linked accounts',
                'order': 6
            },
            {
                'name': 'OAuth Application Tokens',
                'order': 7
            },
            {
                'name': 'OAuth Applications',
                'order': 8
            },
            {
                'name': 'Role',
                'order': 9
            },
            {
                'name': 'Session Activity',
                'order': 10
            },
            {
                'name': 'User',
                'order': 11
            },
            {
                'name': 'User Profile',
                'order': 12
            }
        ]
    },
    {
        'name': 'Web Design',
        'order': 5,
        'submenu': [
            {
                'name': 'Page Layout',
                'order': 2
            },
            {
                'name': 'Widget',
                'order': 1
            }
        ]
    },
    {
        'name': 'WorkFlow',
        'order': 8,
        'submenu': [
            {
                'name': 'Flow List',
                'order': 1
            },
            {
                'name': 'WorkFlow List',
                'order': 2
            }
        ]
    },
    {
        'name': 'Logs',
        'order': 16,
        'submenu': [
            {
                'name': 'Export',
                'order': 1
            }
        ]
    },
    {
        'name': 'Maintenance',
        'order': 17,
        'submenu': [
            {
                'name': 'ElasticSearch Index',
                'order': 1
            }
        ]
    },
]


WEKO_SHOW_INDEX_FOR_AUTHENTICATED_USER = False
"""インデックスツリー設定"""

DISPLAY_LOGIN = True
""" Display Login/Sign up menu """


ENABLE_COOKIE_CONSENT = False
""" Enable klaro cookie consent function """

WEKO_THEME_FETCH_SEARCH_FLG = True
""" Enable DOM differential update functionality when searching. """
