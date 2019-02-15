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
from invenio_search import RecordsSearch

WEKO_SEARCH_UI_SEARCH_INDEX_API = '/api/index/'

WEKO_SEARCH_UI_BASE_TEMPLATE = 'weko_search_ui/base.html'
"""Default base template for the demo page."""

WEKO_SEARCH_UI_THEME_FRONTPAGE_TEMPLATE = \
    'weko_search_ui/header_frontpage.html'
"""Reset invenio_theme.config['THEME_FRONTPAGE_TEMPLATE'] info"""

WEKO_SEARCH_UI_SEARCH_TEMPLATE = 'weko_search_ui/search.html'

"""Reset search_ui_search config"""

WEKO_SEARCH_UI_JSTEMPLATE_RESULTS = 'templates/weko_search_ui/itemlist.html'

WEKO_ITEM_MANAGEMENT_JSTEMPLATE_RESULTS_EDIT = 'templates/weko_search_ui/itemListItemManagementEdit.html'

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

RECORDS_REST_ENDPOINTS['recid']['search_index'] = 'weko'
RECORDS_REST_ENDPOINTS['recid']['search_type'] = 'item'

# Opensearch endpoint
RECORDS_REST_ENDPOINTS['opensearch'] = copy.deepcopy(RECORDS_REST_ENDPOINTS['recid'])
RECORDS_REST_ENDPOINTS['opensearch']['search_factory_imp'] = \
    'weko_search_ui.query.opensearch_factory'
RECORDS_REST_ENDPOINTS['opensearch']['list_route'] = '/opensearch/search'
RECORDS_REST_ENDPOINTS['opensearch']['search_serializers'] = {
    'application/json': ('weko_records.serializers'
                         ':opensearch_v1_search'),
}

INDEXER_DEFAULT_INDEX = 'weko'
INDEXER_DEFAULT_DOCTYPE = 'item'
INDEXER_DEFAULT_DOC_TYPE = 'item'
INDEXER_FILE_DOC_TYPE = 'content'

SEARCH_UI_SEARCH_INDEX = 'weko'

# set item type aggs
RECORDS_REST_FACETS = dict(
    weko=dict(
        aggs=dict(
            itemtypes=dict(terms=dict(
                field='item_type_id')),
        )
    )
)
RECORDS_REST_SORT_OPTIONS = dict(
    weko=dict(
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
            fields=['creator'],
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
            fields=['dateofissued'],
            default_order='asc',
            order=7,
        ),
        publish_date=dict(
            title='Publish date',
            fields=['date'],
            default_order='asc',
            order=8,
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
)


WEKO_SEARCH_REST_ENDPOINTS = dict(
    recid=dict(
        pid_type='recid',
        pid_minter='recid',
        pid_fetcher='recid',
        search_class=RecordsSearch,
        search_index='weko',
        search_type='item',
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
                "identifier": ("relation.relatedIdentifier", "identifierType=*"),
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
                "ichushi": ("relation.relatedIdentifier", "identifierType=ICHUSHI")
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

