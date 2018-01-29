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

WEKO_SEARCH_UI_BASE_TEMPLATE = 'weko_search_ui/base.html'
"""Default base template for the demo page."""

WEKO_SEARCH_UI_THEME_FRONTPAGE_TEMPLATE = \
    'weko_search_ui/header_frontpage.html'
"""Reset invenio_theme.config['THEME_FRONTPAGE_TEMPLATE'] info"""

WEKO_SEARCH_UI_SEARCH_TEMPLATE = 'weko_search_ui/search.html'
"""Reset search_ui_search config"""

WEKO_SEARCH_UI_JSTEMPLATE_RESULTS = 'templates/weko_search_ui/weko.html'

WEKO_SEARCH_UI_JSTEMPLATE_COUNT = 'templates/weko_search_ui/count.html'

RECORDS_REST_ENDPOINTS = copy.deepcopy(RECORDS_REST_ENDPOINTS)
RECORDS_REST_ENDPOINTS['recid']['search_factory_imp'] = \
    'weko_search_ui.query.es_search_factory'

RECORDS_REST_ENDPOINTS['recid']['search_index'] = 'weko'
RECORDS_REST_ENDPOINTS['recid']['search_type'] = 'item'

INDEXER_DEFAULT_INDEX = 'weko'
INDEXER_DEFAULT_DOCTYPE = 'item'
INDEXER_DEFAULT_DOC_TYPE = 'item'

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
            fields=['update_date'],
            default_order='asc',
            order=5,
        ),
        createdate=dict(
            title='Create date',
            fields=['create_date'],
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
            fields=['publish_date'],
            default_order='asc',
            order=8,
        )
    )
)

RECORDS_UI_EXPORT_FORMATS = {
    'recid': {
        'junii2': dict(
            title='JUNII2',
            serializer='weko_records.serializers.Junii2_v2',
            order=1,
        ),
        'jpcoar': dict(
            title='JPCOAR',
            serializer='weko_records.serializers.Jpcoar_v1',
            order=2,
        ),
        'json': dict(
            title='JSON',
            serializer='invenio_records_rest.serializers.json_v1',
            order=4,
        ),
        # Deprecated names
        'hx': False,
        'hm': False,
        'xm': False,
        'xd': False,
        'xe': False,
        'xn': False,
        'xw': False,
    }
}
