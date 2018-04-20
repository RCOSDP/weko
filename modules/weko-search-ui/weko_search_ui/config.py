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

WEKO_SEARCH_UI_JSTEMPLATE_INDEX = 'templates/weko_search_ui/indexlist.html'

WEKO_SEARCH_UI_JSTEMPLATE_BREAD = 'templates/weko_search_ui/breadcrumb.html'

WEKO_SEARCH_UI_JSTEMPLATE_COUNT = 'templates/weko_search_ui/count.html'

SEARCH_UI_JSTEMPLATE_PAGINATION = 'templates/weko_search_ui/pagination.html'

SEARCH_UI_JSTEMPLATE_SELECT_BOX = 'templates/weko_search_ui/selectbox.html'

SEARCH_UI_JSTEMPLATE_SORT_ORDER = 'templates/weko_search_ui/togglebutton.html'

RECORDS_REST_ENDPOINTS = copy.deepcopy(RECORDS_REST_ENDPOINTS)
RECORDS_REST_ENDPOINTS['recid']['search_factory_imp'] = \
    'weko_search_ui.query.es_search_factory'
RECORDS_REST_ENDPOINTS['recid']['search_serializers'] = {
    'application/json': ('weko_records.serializers'
                         ':json_v1_search'),
}

RECORDS_REST_ENDPOINTS['recid']['search_index'] = 'weko'
RECORDS_REST_ENDPOINTS['recid']['search_type'] = 'item'

INDEXER_DEFAULT_INDEX = 'weko'
INDEXER_DEFAULT_DOCTYPE = 'item'
INDEXER_DEFAULT_DOC_TYPE = 'item'
INDEXER_FILE_DOC_TYPE = 'content'

SEARCH_UI_SEARCH_INDEX = 'weko'

RECORDS_REST_FACETS = dict(
    weko=dict(
        aggs=dict(
            authors=dict(terms=dict(
                field='NIItype')),
        ),
        post_filters=dict(
            authors=terms_filter(
                'NIItype'),
        )
    )
)
RECORDS_REST_SORT_OPTIONS = dict(
    weko=dict(
        bestmatch=dict(
            title='Best match',
            fields=['-_score'],
            default_order='asc',
            order=1,
        ),
        controlnumber=dict(
            title='Control number',
            fields=['control_number'],
            default_order='desc',
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
        )
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
