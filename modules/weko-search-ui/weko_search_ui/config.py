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

"""Configuration for weko-search-ui."""

import copy

from invenio_records_rest.config import RECORDS_REST_ENDPOINTS
from invenio_records_rest.facets import terms_filter
from invenio_records_rest.utils import allow_all
from invenio_search import RecordsSearch
from invenio_stats.config import SEARCH_INDEX_PREFIX as index_prefix

WEKO_SEARCH_UI_SEARCH_INDEX_API = '/api/index/'

WEKO_SEARCH_UI_BASE_TEMPLATE = 'weko_search_ui/base.html'
"""Default base template for the demo page."""

WEKO_SEARCH_UI_THEME_FRONTPAGE_TEMPLATE = \
    'weko_search_ui/header_frontpage.html'
"""Reset invenio_theme.config['THEME_FRONTPAGE_TEMPLATE'] info"""

WEKO_SEARCH_UI_SEARCH_TEMPLATE = 'weko_search_ui/search.html'

WEKO_SEARCH_UI_SEARCH_RESULTS_TEMPLATE = 'weko_search_ui/search_results.html'

WEKO_SEARCH_UI_ADMIN_BULK_DELETE = \
    'weko_search_ui/admin/item_management_display.html'

"""Reset search_ui_search config"""

WEKO_SEARCH_UI_JSTEMPLATE_LIST_RESULTS = 'templates/weko_search_ui/itemlist.html'

WEKO_SEARCH_UI_JSTEMPLATE_TABLE_RESULTS = 'templates/weko_search_ui/itemtablecontents.html'

WEKO_ITEM_MANAGEMENT_JSTEMPLATE_RESULTS_EDIT = 'templates/weko_search_ui/itemListItemManagementEdit.html'

WEKO_SEARCH_UI_BULK_UPDATE_JSTEMPLATE_RESULTS = 'templates/weko_search_ui/bulkupdate_itemlist.html'

WEKO_ITEM_WORKFLOW_JSTEMPLATE_RESULTS_EDIT = 'templates/weko_search_ui/itemListWorkFlowItemLink.html'

WEKO_SEARCH_UI_JSTEMPLATE_RESULTS_BASIC = 'templates/weko_search_ui/itemlistbasic.html'

WEKO_SEARCH_UI_JSTEMPLATE_INDEX = 'templates/weko_search_ui/indexlist.html'

WEKO_SEARCH_UI_JSTEMPLATE_BREAD = 'templates/weko_search_ui/breadcrumb.html'

WEKO_ITEM_MANAGEMENT_JSTEMPLATE_BREAD = 'templates/weko_search_ui/breadcrumbItemManagement.html'

WEKO_SEARCH_UI_JSTEMPLATE_COUNT = 'templates/weko_search_ui/count.html'

SEARCH_UI_JSTEMPLATE_PAGINATION = 'templates/weko_search_ui/pagination.html'

SEARCH_UI_ITEM_MANAGEMENT_JSTEMPLATE_PAGINATION = 'templates/weko_search_ui/paginationItemManagement.html'

SEARCH_UI_JSTEMPLATE_SELECT_BOX = 'templates/weko_search_ui/selectbox.html'

SEARCH_UI_JSTEMPLATE_SORT_ORDER = 'templates/weko_search_ui/togglebutton.html'

WEKO_ITEM_ADMIN_IMPORT_TEMPLATE = 'weko_search_ui/admin/import.html'
"""import template for the import page."""

INDEX_IMG = 'indextree/36466818-image.jpg'

# Opensearch description
WEKO_OPENSEARCH_SYSTEM_SHORTNAME = 'WEKO'
WEKO_OPENSEARCH_SYSTEM_DESCRIPTION = 'WEKO - NII Scholarly and Academic Information Navigator'
WEKO_OPENSEARCH_IMAGE_URL = 'static/favicon.ico'

RECORDS_REST_ENDPOINTS = copy.deepcopy(RECORDS_REST_ENDPOINTS)
RECORDS_REST_ENDPOINTS['recid']['search_factory_imp'] = \
    'weko_search_ui.query.es_search_factory'
RECORDS_REST_ENDPOINTS['recid']['search_serializers'] = {
    'application/json': ('weko_records.serializers'
                         ':json_v1_search'),
}

RECORDS_REST_ENDPOINTS['recid']['search_index'] = '{}-weko'.format(index_prefix)
RECORDS_REST_ENDPOINTS['recid']['search_type'] = 'item-v1.0.0'

# Opensearch endpoint
RECORDS_REST_ENDPOINTS['opensearch'] = copy.deepcopy(
    RECORDS_REST_ENDPOINTS['recid'])
RECORDS_REST_ENDPOINTS['opensearch']['search_factory_imp'] = \
    'weko_search_ui.query.opensearch_factory'
RECORDS_REST_ENDPOINTS['opensearch']['list_route'] = '/opensearch/search'
RECORDS_REST_ENDPOINTS['opensearch']['search_serializers'] = {
    'application/json': ('weko_records.serializers:opensearch_v1_search'),
}

RECORDS_REST_ENDPOINTS['recid']['record_class'] = 'weko_records.api:WekoRecord'
RECORDS_REST_ENDPOINTS['recid']['record_serializers'] = {
    'application/vnd.citationstyles.csl+json': (
        'weko_records.serializers:csl_v1_response'),
    'text/x-bibliography': ('weko_records.serializers:citeproc_v1_response')
}

# RECORDS_REST_ENDPOINTS['recid']['read_permission_factory_imp'] = allow_all

INDEXER_DEFAULT_INDEX = '{}-weko-item-v1.0.0'.format(
    index_prefix)  # Use direct index
INDEXER_DEFAULT_DOCTYPE = 'item-v1.0.0'
INDEXER_DEFAULT_DOC_TYPE = 'item-v1.0.0'
INDEXER_FILE_DOC_TYPE = 'content'

SEARCH_UI_SEARCH_INDEX = '{}-weko'.format(index_prefix)

# set item type aggs
RECORDS_REST_FACETS = dict()

WEKO_FACETED_SEARCH_MAPPING = {
    'accessRights': 'accessRights',
    'language': 'language',
    'distributor': 'contributor.contributorName',
    'dataType': 'description.value'
}

RECORDS_REST_FACETS[SEARCH_UI_SEARCH_INDEX] = dict(
    aggs=dict(
        accessRights=dict(terms=dict(
            field=WEKO_FACETED_SEARCH_MAPPING['accessRights'])),
        language=dict(terms=dict(
            field=WEKO_FACETED_SEARCH_MAPPING['language'])),
        distributor=dict(
            filter=dict(
                term={"contributor.@attributes.contributorType": "Distributor"}
            ),
            aggs=dict(
                distributor=dict(
                    terms=dict(
                        field=WEKO_FACETED_SEARCH_MAPPING['distributor']))
            )
        ),
        dataType=dict(
            filter=dict(
                term={"description.descriptionType": "Other"}
            ),
            aggs=dict(
                dataType=dict(
                    terms=dict(
                        script=dict(
                            source='''
                            ArrayList result = new ArrayList();
                            int size = params._source.description.length;
                            for (int i=0; i<size; i++) {
                                String valueName = params._source.description[i].value;
                                if(params._source.description[i].descriptionType.equals("Other")) {
                                    result.add(valueName);
                                }
                            }
                            return result;''',
                            lang="painless"
                        )
                    )
                )
            )
        )
    ),
    post_filters=dict(
        accessRights=terms_filter(WEKO_FACETED_SEARCH_MAPPING['accessRights']),
        language=terms_filter(WEKO_FACETED_SEARCH_MAPPING['language']),
        distributor=terms_filter(WEKO_FACETED_SEARCH_MAPPING['distributor']),
        dataType=terms_filter(WEKO_FACETED_SEARCH_MAPPING['dataType']),
    )
)

RECORDS_REST_SORT_OPTIONS = dict()
RECORDS_REST_SORT_OPTIONS[SEARCH_UI_SEARCH_INDEX] = dict(
    controlnumber=dict(
        title='ID',
        fields=['control_number'],
        default_order='asc',
        order=2,
    ),
    wtl=dict(
        title='Title',
        fields=['title'],
        default_order='asc',
        order=3,
    ),
    creator=dict(
        title='Creator',
        fields=['creator.creatorName'],
        default_order='asc',
        order=4,
    ),
    upd=dict(
        title='Update date',
        fields=['_updated'],
        default_order='asc',
        order=5,
    ),
    createdate=dict(
        title='Create date',
        fields=['_created'],
        default_order='asc',
        order=6,
    ),
    pyear=dict(
        title='Date of Issued',
        fields=['date.value'],  # dateofissued
        default_order='asc',
        order=7,
        nested=dict(
            path='date',
            filter=dict(
                term={
                    'date.dateType': 'Issued'
                }
            )
        )
    ),
    publish_date=dict(
        title='Publish date',
        fields=['publish_date'],  # date.value
        default_order='asc',
        order=8
    ),
    # add 20181121 start
    custom_sort=dict(
        title='Custom',
        fields=['custom_sort.sort'],
        default_order='asc',
        order=9,
    ),
    itemType=dict(
        title='ItemType',
        fields=['itemtype'],
        default_order='asc',
        order=10,
    )
    # add 20181121 end
)

WEKO_SEARCH_REST_ENDPOINTS = dict(
    recid=dict(
        pid_type='recid',
        pid_minter='recid',
        pid_fetcher='recid',
        search_class=RecordsSearch,
        search_index=SEARCH_UI_SEARCH_INDEX,
        search_type='item-v1.0.0',
        search_factory_imp='weko_search_ui.query.weko_search_factory',
        # record_class='',
        record_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/json': ('weko_records.serializers'
                                 ':json_v1_search'),
        },
        index_route='/index/',
        links_factory_imp='weko_search_ui.links:default_links_factory',
        default_media_type='application/json',
        max_result_window=10000,
    ),
)

WEKO_SEARCH_KEYWORDS_DICT = {
    "nested": {
        "subject": ("subject", {"sbjscheme": {
            "subject.subjectScheme": [
                "BSH",
                "DDC",
                "LCC",
                "LCSH",
                "MeSH",
                "NDC",
                "NDLC",
                "NDLSH",
                "UDC",
                "Other",
                "SciVal"
            ]
        }}),
        "id": ("", {
            "id_attr": {
                "identifier": (
                    "relation.relatedIdentifier", "identifierType=*"),
                "URI": ("identifier", "identifierType=*"),
                "fullTextURL": ("file.URI", "objectType=*"),
                "selfDOI": ("identifierRegistration", "identifierType=*"),
                "ISBN": ("relation.relatedIdentifier", "identifierType=ISBN"),
                "ISSN": ("sourceIdentifier", "identifierType=ISSN"),
                "NCID": [
                    ("relation.relatedIdentifier", "identifierType=NCID"),
                    ("sourceIdentifier", "identifierType=NCID")
                ],
                "pmid": ("relation.relatedIdentifier", "identifierType=PMID"),
                "doi": ("relation.relatedIdentifier", "identifierType=DOI"),
                "NAID": ("relation.relatedIdentifier", "identifierType=NAID"),
                "ichushi": (
                    "relation.relatedIdentifier", "identifierType=ICHUSHI")
            }})
    },
    "string": {
        "title": ["search_title", "search_title.ja"],
        "creator": ["search_creator", "search_creator.ja"],
        "des": ["search_des", "search_des.ja"],
        "publisher": ["search_publisher", "search_publisher.ja"],
        "cname": ["search_contributor", "search_contributor.ja"],
        "itemtype": ("item_type_id", int),
        "type": {
            "type": [
                "conference paper",
                "departmental bulletin paper",
                "journal article",
                "article",
                "book",
                "conference object",
                "dataset",
                "research report",
                "technical report",
                "thesis",
                "learning material",
                "software",
                "other"
            ]
        },
        "mimetype": "file.mimeType",
        "language": {
            "language": ["jpn", "eng",
                         "fra", "ita",
                         "deu", "spa",
                         "zho", "rus",
                         "lat", "msa",
                         "epo", "ara",
                         "ell", "kor",
                         "-"]},
        "srctitle": ["sourceTitle", "sourceTitle.ja"],
        "spatial": "geoLocation.geoLocationPlace",
        "temporal": "temporal",
        "rights": "rights",
        "version": "versionType",
        "dissno": "dissertationNumber",
        "degreename": ["degreeName", "degreeName.ja"],
        "dgname": ["dgName", "dgName.ja"],
        "wid": "weko_id",
        "iid": ("path.tree", int)
    },
    "date": {
        "filedate": [('from', 'to'), ("file.date", {"fd_attr": {
            "file.date.dateType": ["Accepted",
                                   "Available",
                                   "Collected",
                                   "Copyrighted",
                                   "Created",
                                   "Issued",
                                   "Submitted",
                                   "Updated",
                                   "Valid"]}})],
        "dategranted": [('from', 'to'), "dateGranted"]
    }
}

WEKO_SEARCH_TYPE_KEYWORD = 'keyword'

WEKO_SEARCH_TYPE_INDEX = 'index'

WEKO_SEARCH_MAX_FEEDBACK_MAIL = 100
"""Maximum number of feedback mail could be send."""

WEKO_SEARCH_TYPE_DICT = {
    'FULL_TEXT': '0',
    'KEYWORD': '1',
    'INDEX': '2'
}
WEKO_SYS_USER = 'System Administrator'

WEKO_REPO_USER = 'Repository Administrator'

WEKO_FLOW_DEFINE = {'flow_name': 'Registration Flow'}

WEKO_FLOW_DEFINE_LIST_ACTION = [
    {
        "id": "1",
        "name": "Start",
        "date": "2019-12-03",
        "version": "1.0.0",
        "user": "0",
        "user_deny": False,
        "role": "0",
        "role_deny": False,
        "action": "ADD"
    },
    {
        "id": "3",
        "name": "Item Registration",
        "date": "2019-12-3",
        "version": "1.0.1",
        "user": "0",
        "user_deny": False,
        "role": "0",
        "role_deny": False,
        "action": "ADD"
    },
    {
        "id": "2",
        "name": "End",
        "date": "2019-12-03",
        "version": "1.0.0",
        "user": "0",
        "user_deny": False,
        "role": "0",
        "role_deny": False,
        "action": "ADD"
    }
]

WEKO_IMPORT_CHECK_LIST_NAME = [
    'No', 'Item Type', 'Item Id', 'Title', 'Check result'
]

WEKO_IMPORT_LIST_NAME = [
    'No', 'Start Date', 'End Date', 'Item Id', 'Action', 'Work Flow Status'
]
WEKO_ADMIN_LIFETIME_DEFAULT = 1800

#: Change identifier mode file language list
WEKO_ADMIN_IMPORT_CHANGE_IDENTIFIER_MODE_FILE_LANGUAGES = ['en', 'ja']
#: Change identifier mode file location
WEKO_ADMIN_IMPORT_CHANGE_IDENTIFIER_MODE_FILE_LOCATION = '/code/modules/weko-search-ui/weko_search_ui/static/change_identifier_mode/'
#: Change identifier mode first name file
WEKO_ADMIN_IMPORT_CHANGE_IDENTIFIER_MODE_FIRST_FILE_NAME = 'change_identifier_mode'
#: Change identifier mode file extension
WEKO_ADMIN_IMPORT_CHANGE_IDENTIFIER_MODE_FILE_EXTENSION = '.txt'
