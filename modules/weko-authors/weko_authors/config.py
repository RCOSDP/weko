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

"""Configuration for weko-authors."""

from invenio_stats.config import SEARCH_INDEX_PREFIX as index_prefix

WEKO_AUTHORS_LIST_SCHEME = ['e-Rad', 'NRID', 'ORCID', 'ISNI', 'VIAF', 'AID',
                            'kakenhi', 'Ringgold', 'GRID', 'Other']
""" List of scheme """

WEKO_AUTHORS_INDEX_ITEM_OTHER = 9
""" Item other index """

WEKO_AUTHORS_BASE_TEMPLATE = 'weko_authors/base.html'
"""Default base template for the author page."""

WEKO_AUTHORS_ADMIN_LIST_TEMPLATE = 'weko_authors/admin/author_list.html'
"""List template for the admin author page."""

WEKO_AUTHORS_ADMIN_EDIT_TEMPLATE = 'weko_authors/admin/author_edit.html'
"""Edit template for the admin author page."""

WEKO_AUTHORS_ADMIN_PREFIX_TEMPLATE = 'weko_authors/admin/prefix_list.html'
"""template for the id prefix settings page."""

WEKO_AUTHORS_ADMIN_EXPORT_TEMPLATE = 'weko_authors/admin/author_export.html'
"""template for the export page."""

WEKO_AUTHORS_EXPORT_ENTRYPOINTS = {
    'export': '/admin/authors/export/export',
    'cancel': '/admin/authors/export/cancel',
    'check_status': '/admin/authors/export/check_status'
}

WEKO_AUTHORS_EXPORT_FILE_NAME = 'Creator_export_all.tsv'
WEKO_AUTHORS_EXPORT_CACHE_STATUS_KEY = 'weko_authors_export_status'
WEKO_AUTHORS_EXPORT_CACHE_URL_KEY = 'weko_authors_exported_url'

WEKO_AUTHORS_TSV_MAPPING = [
    {
        'header': '#WEKO ID',
        'label': '#WEKO ID',
        'json_id': 'pk_id'
    },
    {
        'json_id': 'authorNameInfo',
        'child': [
            {
                'header': 'Family Name',
                'label': '姓',
                'json_id': 'familyName'
            },
            {
                'header': 'Given name',
                'label': '名',
                'json_id': 'firstName'
            },
            {
                'header': 'Language',
                'label': '言語',
                'json_id': 'language'
            },
            {
                'header': 'Name Display',
                'label': '姓名・言語 表示／非表示',
                'json_id': 'nameShowFlg',
                'mask': {
                    'true': 'Y',
                    'false': 'N'
                }
            }]
    },
    {
        'json_id': 'authorIdInfo',
        'child': [
            {
                'header': 'Identifier Scheme',
                'label': '外部著者ID 識別子',
                'json_id': 'idType'
            },
            {
                'header': 'Identifier URI',
                'label': '外部著者ID URI',
                'json_id': 'authorId'
            },
            {
                'header': 'Identifier Display',
                'label': '外部著者ID 表示／非表示',
                'json_id': 'authorIdShowFlg',
                'mask': {
                    'true': 'Y',
                    'false': 'N'
                }
            }
        ]
    },
    {
        'json_id': 'emailInfo',
        'child': [
            {
                'header': 'Mail Address',
                'label': 'メールアドレス',
                'json_id': 'email'
            }
        ]
    },
    {
        'header': 'Delete Flag',
        'label': '削除フラグ',
        'json_id': 'is_deleted',
        'mask': {
            'true': 'D',
            'false': None
        }
    }
]

WEKO_AUTHORS_NUM_OF_PAGE = 25
"""Default number of author search results that display in one page."""

WEKO_AUTHORS_ES_INDEX_NAME = "{}-authors".format(index_prefix)
"""Elasticsearch index alias for author."""

WEKO_AUTHORS_ES_DOC_TYPE = "author-v1.0.0"
"""Elasticsearch document type for author."""

WEKO_AUTHORS_IMPORT_KEY = {
    'author_name': {
        'contributorNames': ['contributorName', 'lang'],
        'creatorNames': ['creatorName', 'creatorNameLang'],
        'names': ['name', 'nameLang']
    },
    'author_mail': {
        'contributorMails': 'contributorMail',
        'creatorMails': 'creatorMail',
        'mails': 'mail'
    }
}
"""Key of author get fill import data."""
