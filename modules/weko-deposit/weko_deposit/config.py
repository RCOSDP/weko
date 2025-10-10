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

"""Configuration for weko-deposit."""

import copy

from invenio_records_rest.utils import deny_all

WEKO_BUCKET_QUOTA_SIZE = 50 * 1024 * 1024 * 1024  # 50 GB
"""Maximum quota per bucket."""

WEKO_MAX_FILE_SIZE = WEKO_BUCKET_QUOTA_SIZE
"""Maximum file size accepted."""

WEKO_DEPOSIT_TEXTMIMETYPE_WHITELIST_FOR_ES = [
    'text/plain',
    'text/csv',
    'text/html',
    'text/tab-separated-values',
    'text/xml',
    'application/x-tex',
    'application/x-latex'
]

WEKO_MIMETYPE_WHITELIST_FOR_ES = [
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.oasis.opendocument.text',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.oasis.opendocument.spreadsheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'application/vnd.oasis.opendocument.presentation',
    'application/pdf',
] + WEKO_DEPOSIT_TEXTMIMETYPE_WHITELIST_FOR_ES



WEKO_DEPOSIT_FILESIZE_LIMIT = 2 * 1024 * 1024
""" The file size(Byte) limit for extracting text from a file. """

FILES_REST_STORAGE_FACTORY = 'weko_deposit.storage.pyfs_storage_factory'
"""Import path of factory used to create a storage instance."""

FILES_REST_UPLOAD_OWNER_FACTORIES = 'weko_deposit.serializer.file_uploaded_owner'
"""file update version"""

WEKO_DEPOSIT_ITEMS_CACHE_PREFIX = 'cache_itemsIndex_{pid_value}'
""" cache items prefix info"""

WEKO_DEPOSIT_ITEM_UPDATE_STATUS_TTL = 60 * 10
""" cache default timeout for update status (sec.)"""

WEKO_DEPOSIT_ITEM_UPDATE_TASK_TTL = 60 * 60 * 24 * 30 # 1 month
""" cache default timeout for update task (sec.)"""

WEKO_DEPOSIT_ITEM_UPDATE_RETRY_COUNT = 1
""" retry count of update_items_by_authorInfo """

WEKO_DEPOSIT_ITEM_UPDATE_RETRY_COUNTDOWN = 3
""" retry countdown of update_items_by_authorInfo (sec.)"""

WEKO_DEPOSIT_ITEM_UPDATE_RETRY_BACKOFF_RATE = 2
""" retry backoff rate of update_items_by_authorInfo """


WEKO_DEPOSIT_ITEMS_CACHE_TTL = 300
""" cache default timeout 5 minutes"""

WEKO_DEPOSIT_MAX_BACK_OFF_TIME = 32

_PID = 'pid(depid,record_class="weko_deposit.api:WekoDeposit")'

#: Template for deposit list view.
DEPOSIT_SEARCH_API = '/api/deposits/items'

#: Template for deposit records API.
DEPOSIT_RECORDS_API = '/api/deposits/items/{pid_value}'
DEPOSIT_RECORDS_EDIT_API = '/api/deposits/redirect/{pid_value}'

DEPOSIT_REST_ENDPOINTS = dict(
    depid=dict(
        pid_type='depid',
        pid_minter='weko_deposit_minter',
        pid_fetcher='weko_deposit_fetcher',
        record_class='weko_deposit.api:WekoDeposit',
        record_serializers={
            'application/json': ('weko_records.serializers'
                                 ':deposit_json_v1_response'),
        },
        files_serializers={
            'application/json': ('invenio_deposit.serializers'
                                 ':json_v1_files_response'),
        },
        search_class='invenio_deposit.search:DepositSearch',
        search_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        list_route='/deposits/items',
        item_route='/deposits/items/<{0}:pid_value>'.format(_PID),
        file_list_route='/deposits/items/<{0}:pid_value>/files'.format(_PID),
        file_item_route='/deposits/items/<{0}:pid_value>/files/<path:key>'.format(
            _PID),
        default_media_type='application/json',
        links_factory_imp='weko_deposit.links:links_factory',
        max_result_window=10000,
        # create_permission_factory_imp='',
        # read_permission_factory_imp='',
        # update_permission_factory_imp='',
        delete_permission_factory_imp=deny_all,
    )
)

# for redirect to next page(index select)
WEKO_DEPOSIT_REST_ENDPOINTS = copy.deepcopy(DEPOSIT_REST_ENDPOINTS)
WEKO_DEPOSIT_REST_ENDPOINTS['depid']['rdc_route'] = '/deposits/redirect/<{0}:pid_value>'.format(
    _PID)
WEKO_DEPOSIT_REST_ENDPOINTS['depid']['pub_route'] = '/deposits/publish/<{0}:pid_value>'.format(
    _PID)

DEPOSIT_RECORDS_UI_ENDPOINTS = {
    'depid': {
        'pid_type': 'depid',
        'route': '/item/edit/<pid_value>',
        'template': 'weko_items_ui/edit.html',
        'record_class': 'weko_deposit.api:WekoDeposit',
        'view_imp': 'weko_items_ui.views.default_view_method',
        'permission_factory_imp': 'weko_items_ui.permissions:edit_permission_factory',
    },
    'iframe_depid': {
        'pid_type': 'depid',
        'route': '/item/iframe/edit/<pid_value>',
        'template': 'weko_items_ui/iframe/item_edit.html',
        'record_class': 'weko_deposit.api:WekoDeposit',
        'view_imp': 'weko_items_ui.views.default_view_method',
        'permission_factory_imp': 'weko_items_ui.permissions:edit_permission_factory',
    }
}

RECORDS_REST_DEFAULT_CREATE_PERMISSION_FACTORY = None
RECORDS_REST_DEFAULT_UPDATE_PERMISSION_FACTORY = None
DEPOSIT_JSONSCHEMAS_PREFIX = ''

WEKO_DEPOSIT_SYS_CREATOR_KEY = {
    'creator_type': 'creatorType', #? ADDED 20231017 CREATOR TYPE BUG FIX
    'creator_names': 'creatorNames',
    'creator_name': 'creatorName',
    'creator_lang': 'creatorNameLang',
    'family_names': 'familyNames',
    'family_name': 'familyName',
    'family_lang': 'familyNameLang',
    'given_names': 'givenNames',
    'given_name': 'givenName',
    'given_lang': 'givenNameLang',
    'alternative_names': 'creatorAlternatives',
    'alternative_name': 'creatorAlternative',
    'alternative_lang': 'creatorAlternativeLang',
    'identifiers': 'nameIdentifiers',
    'creator_mails': 'creatorMails',
    'affiliation_name_identifier_scheme': 'affiliationNameIdentifierScheme',
    'affiliation_names': 'affiliationNames',
    'affiliation_name': 'affiliationName',
    'affiliation_lang': 'affiliationNameLang',
    'affiliationNameIdentifiers': 'affiliationNameIdentifiers',
    'affiliation_name_identifier': 'affiliationNameIdentifier',
    'affiliation_name_identifier_URI': 'affiliationNameIdentifierURI',
    'creatorAffiliations': 'creatorAffiliations',
}
"""Key of Bibliographic information."""

WEKO_DEPOSIT_BIBLIOGRAPHIC_INFO_KEY = [
    'bibliographicVolumeNumber',
    'bibliographicIssueNumber',
    'p.',
    'bibliographicNumberOfPages',
    'bibliographicIssueDates'
]
"""Key of Bibliographic information."""

WEKO_DEPOSIT_BIBLIOGRAPHIC_TRANSLATIONS = {
    'bibliographicVolumeNumber': {
        "en": "Volume",
        "ja": "巻"
    },
    'bibliographicIssueNumber': {
        "en": "Issue",
        "ja": "号"
    },
    'p.': {
        "en": "p.",
        "ja": "p."
    },
    'bibliographicNumberOfPages': {
        "en": "Number of Pages",
        "ja": "ページ数"
    },
    'bibliographicIssueDates': {
        "en": "Issued Date",
        "ja": "発行年"
    }
}

"""Translation of Bibliographic information."""

WEKO_DEPOSIT_BIBLIOGRAPHIC_INFO_SYS_KEY = [
    'bibliographic_titles',
    'bibliographicPageEnd',
    'bibliographicIssueNumber',
    'bibliographicPageStart',
    'bibliographicVolumeNumber',
    'bibliographicNumberOfPages',
    'bibliographicIssueDates'
]
"""Bibliographic information sys key."""


