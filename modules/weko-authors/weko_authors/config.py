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
# from invenio_stats.config import SEARCH_INDEX_PREFIX as index_prefix
import os
from .rest import Authors

WEKO_AUTHORS_LIST_SCHEME = ['e-Rad', 'NRID', 'ORCID', 'ISNI', 'VIAF', 'AID',
                            'kakenhi', 'Ringgold', 'GRID', 'ROR', 'Other']
""" List of Author Name Identifier Scheme """

WEKO_AUTHORS_INDEX_ITEM_OTHER = 10
""" Item other index """

WEKO_AUTHORS_LIST_SCHEME_AFFILIATION = [
    'ISNI', 'GRID', 'Ringgold', 'kakenhi', 'Other']
""" List of Affiliation Name Identifier Scheme """

WEKO_AUTHORS_AFFILIATION_IDENTIFIER_ITEM_OTHER = 4
""" Item other index """

WEKO_AUTHORS_BASE_TEMPLATE = 'weko_authors/base.html'
"""Default base template for the author page."""

WEKO_AUTHORS_ADMIN_LIST_TEMPLATE = 'weko_authors/admin/author_list.html'
"""List template for the admin author page."""

WEKO_AUTHORS_ADMIN_EDIT_TEMPLATE = 'weko_authors/admin/author_edit.html'
"""Edit template for the admin author page."""

WEKO_AUTHORS_ADMIN_PREFIX_TEMPLATE = 'weko_authors/admin/prefix_list.html'
"""Template for the id prefix settings page."""

WEKO_AUTHORS_ADMIN_AFFILIATION_TEMPLATE = \
    'weko_authors/admin/affiliation_list.html'
"""Template for the id affiliation settings page."""

WEKO_AUTHORS_ADMIN_EXPORT_TEMPLATE = 'weko_authors/admin/author_export.html'
"""Template for the export page."""

WEKO_AUTHORS_EXPORT_ENTRYPOINTS = {
    'export': '/admin/authors/export/export',
    'cancel': '/admin/authors/export/cancel',
    'check_status': '/admin/authors/export/check_status'
}

WEKO_AUTHORS_EXPORT_FILE_NAME = 'Creator_export_all'
WEKO_AUTHORS_EXPORT_CACHE_STATUS_KEY = 'weko_authors_export_status'
WEKO_AUTHORS_EXPORT_CACHE_URL_KEY = 'weko_authors_exported_url'

WEKO_AUTHORS_FILE_MAPPING = [
    {
        'label_en': 'WEKO ID',
        'label_jp': 'WEKO ID',
        'json_id': 'pk_id'
    },
    {
        'json_id': 'authorNameInfo',
        'child': [
            {
                'label_en': 'Family Name',
                'label_jp': '姓',
                'json_id': 'familyName'
            },
            {
                'label_en': 'Given Name',
                'label_jp': '名',
                'json_id': 'firstName'
            },
            {
                'label_en': 'Language',
                'label_jp': '言語',
                'json_id': 'language',
                'validation': {
                    'map': ['ja', 'ja-Kana', 'en', 'fr',
                            'it', 'de', 'es', 'zh-cn', 'zh-tw',
                            'ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']
                }
            },
            {
                'label_en': 'Name Format',
                'label_jp': 'フォーマット',
                'json_id': 'nameFormat',
                'validation': {
                    'map': ['familyNmAndNm']
                },
                'autofill': {
                    'condition': {
                        'either_required': ['familyName', 'firstName']
                    },
                    'value': 'familyNmAndNm'
                }
            },
            {
                'label_en': 'Name Display',
                'label_jp': '姓名・言語 表示／非表示',
                'json_id': 'nameShowFlg',
                'mask': {
                    'true': 'Y',
                    'false': 'N'
                },
                'validation': {
                    'map': ['Y', 'N']
                }
            }
        ]
    },
    {
        'json_id': 'authorIdInfo',
        'child': [
            {
                'label_en': 'Identifier Scheme',
                'label_jp': '外部著者ID 識別子',
                'json_id': 'idType',
                'validation': {
                    'validator': {
                        'class_name': 'weko_authors.contrib.validation',
                        'func_name': 'validate_identifier_scheme'
                    },
                    'required': {
                        'if': ['authorId']
                    }
                }
            },
            {
                'label_en': 'Identifier',
                'label_jp': '外部著者ID',
                'json_id': 'authorId',
                'validation': {
                    'required': {
                        'if': ['idType']
                    }
                }
            },
            {
                'label_en': 'Identifier Display',
                'label_jp': '外部著者ID 表示／非表示',
                'json_id': 'authorIdShowFlg',
                'mask': {
                    'true': 'Y',
                    'false': 'N'
                },
                'validation': {
                    'map': ['Y', 'N']
                }
            }
        ]
    },
    {
        'json_id': 'emailInfo',
        'child': [
            {
                'label_en': 'Mail Address',
                'label_jp': 'メールアドレス',
                'json_id': 'email'
            }
        ]
    },
    {
        'label_en': 'Delete Flag',
        'label_jp': '削除フラグ',
        'json_id': 'is_deleted',
        'mask': {
            'true': 'D',
            'false': ''
        },
        'validation': {
            'map': ['D']
        }
    }
]

WEKO_AUTHORS_ADMIN_IMPORT_TEMPLATE = 'weko_authors/admin/author_import.html'
"""Template for the import page."""

WEKO_AUTHORS_IMPORT_TMP_PREFIX = 'weko_authors_import_'

WEKO_AUTHORS_IMPORT_ENTRYPOINTS = {
    'is_import_available': '/admin/authors/import/is_import_available',
    'check_import_file': '/admin/authors/import/check_import_file',
    'import': '/admin/authors/import/import',
    'check_import_status': '/admin/authors/import/check_import_status'
}

WEKO_AUTHORS_IMPORT_CACHE_KEY = 'author_import_cache'

WEKO_AUTHORS_NUM_OF_PAGE = 25
"""Default number of author search results that display in one page."""

from invenio_stats.config import SEARCH_INDEX_PREFIX as index_prefix
WEKO_AUTHORS_ES_INDEX_NAME = "{}-authors".format(index_prefix)
"""Search engine index alias for author."""

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
    },
    'author_affiliation': {
        'contributorAffiliations': {
            'names': {
                'key': 'contributorAffiliationNames',
                'values': {
                    'name': 'contributorAffiliationName',
                    'lang': 'contributorAffiliationNameLang'
                }
            },
            'identifiers': {
                'key': 'contributorAffiliationNameIdentifiers',
                'values': {
                    'identifier': 'contributorAffiliationNameIdentifier',
                    'uri': 'contributorAffiliationURI',
                    'scheme': 'contributorAffiliationScheme'
                }
            }
        },
        'creatorAffiliations': {
            'names': {
                'key': 'affiliationNames',
                'values': {
                    'name': 'affiliationName',
                    'lang': 'affiliationNameLang'
                }
            },
            'identifiers': {
                'key': 'affiliationNameIdentifiers',
                'values': {
                    'identifier': 'affiliationNameIdentifier',
                    'uri': 'affiliationNameIdentifierURI',
                    'scheme': 'affiliationNameIdentifierScheme'
                }
            }
        },
        'affiliations': {
            'names': {
                'key': 'affiliationNames',
                'values': {
                    'name': 'affiliationName',
                    'lang': 'lang'
                }
            },
            'identifiers': {
                'key': 'nameIdentifiers',
                'values': {
                    'identifier': 'nameIdentifier',
                    'uri': 'nameIdentifierURI',
                    'scheme': 'nameIdentifierScheme'
                }
            }
        }
    }
}
"""Key of author get fill import data."""

WEKO_AUTHORS_IDENTIFIER_REG = {
    "ISNI": {
        "minLength": 0,
        "maxLength": 30,
        "reg": "^.*$"
    },
    "GRID": {
        "minLength": 0,
        "maxLength": 30,
        "reg": "^.*$"
    },
    "Ringgold": {
        "minLength": 0,
        "maxLength": 30,
        "reg": "^.*$"
    },
    "kakenhi": {
        "minLength": 0,
        "maxLength": 30,
        "reg": "^.*$"
    }
}
"""
Key of author affiliation nameidentifier regulations.
length: "minLength" <= nameidentifier's length <= "maxLength"
"reg": string pattern, excluding first and last slashes from literal notation
"""

WEKO_AUTHORS_REST_ENDPOINTS = {
    'authors': {
        'route': '/<string:version>/authors/count',
        'default_media_type': 'application/json',
    },
}

WEKO_AUTHORS_COUNT_API_VERSION = {
    'get-v1': Authors.get_v1
}
"""API version."""
