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

"""Configuration for weko-items-ui."""
from invenio_stats.queries import ESWekoRankingQuery

WEKO_WORKFLOW_BASE_TEMPLATE = 'weko_workflow/base.html'
"""Default base template for the demo page."""

WEKO_ITEMS_UI_BASE_TEMPLATE = 'weko_items_ui/base.html'
"""Default base template for the item page."""

WEKO_ITEMS_UI_INDEX_TEMPLATE = 'weko_items_ui/item_index.html'
"""Edit template with file upload for the item page."""

WEKO_ITEMS_UI_ITME_EDIT_TEMPLATE = 'weko_items_ui/iframe/item_edit.html'
"""Edit template with item login for the item page."""

WEKO_ITEMS_UI_FORM_TEMPLATE = 'weko_items_ui/edit.html'
"""Edit template with file upload for the item page."""

WEKO_ITEMS_UI_ERROR_TEMPLATE = 'weko_items_ui/error.html'
"""Error template for the item page."""

WEKO_ITEMS_UI_UPLOAD_TEMPLATE = 'weko_items_ui/upload.html'
"""Demo template for the item page post test data."""

WEKO_ITEMS_UI_EXPORT_TEMPLATE = 'weko_items_ui/export.html'
"""Item export template."""

WEKO_ITEMS_UI_EXPORT_RESULTS_LIST_TEMPLATE = 'weko_items_ui/' \
                                             'export_results_list.html'
"""Item export results list template."""

WEKO_ITEMS_UI_JSTEMPLATE_EXPORT_LIST = 'templates/weko_items_ui/' \
                                       'export_list.html'
"""Javascript template for item export list."""

WEKO_ITEMS_UI_INDEX_URL = '/items/index/{pid_value}'

WEKO_ITEMS_UI_RANKING_TEMPLATE = 'weko_items_ui/ranking.html'

WEKO_ITEMS_UI_DEFAULT_MAX_EXPORT_NUM = 100
"""Default max number of allowed to be exported."""

WEKO_ITEMS_UI_MAX_EXPORT_NUM_PER_ROLE = {
    'System Administrator': WEKO_ITEMS_UI_DEFAULT_MAX_EXPORT_NUM,
    'Repository Administrator': WEKO_ITEMS_UI_DEFAULT_MAX_EXPORT_NUM,
    'Contributor': WEKO_ITEMS_UI_DEFAULT_MAX_EXPORT_NUM,
    'General': WEKO_ITEMS_UI_DEFAULT_MAX_EXPORT_NUM,
    'Community Administrator': WEKO_ITEMS_UI_DEFAULT_MAX_EXPORT_NUM
}
"""Max number of items that can be exported per role."""

WEKO_ITEMS_UI_EXPORT_FORMAT_TSV = 'TSV'
"""Format for exporting items -- TSV. """

WEKO_ITEMS_UI_EXPORT_FORMAT_BIBTEX = 'BIBTEX'
"""Format for exporting items -- BIBTEX. """

WEKO_ITEMS_UI_DATA_REGISTRATION = ""
WEKO_ITEMS_UI_APPLICATION_FOR_LIFE = ""
WEKO_ITEMS_UI_APPLICATION_FOR_ACCUMULATION = ""
WEKO_ITEMS_UI_APPLICATION_FOR_COMBINATIONAL_ANALYSIS = ""
WEKO_ITEMS_UI_APPLICATION_FOR_PERFECTURES = ""
WEKO_ITEMS_UI_APPLICATION_FOR_LOCATION_INFORMATION = ""
WEKO_ITEMS_UI_USAGE_REPORT = ""
WEKO_ITEMS_UI_OUTPUT_REPORT = ""
""" Item type """

WEKO_ITEMS_UI_APPLICATION_ITEM_TYPES_LIST = []

WEKO_ITEMS_UI_SHOW_TERM_AND_CONDITION = []

WEKO_ITEMS_UI_GROUP_APPROVAL_1 = {}

WEKO_ITEMS_UI_GROUP_APPROVAL_2 = {}

WEKO_ITEMS_UI_GROUP_TERMS = {}

WEKO_ITEMS_UI_GROUP_RESEARCH = {}

WEKO_ITEMS_UI_GROUP_OTHER = {}

WEKO_ITEMS_UI_GROUP_LOCATION = {}

WEKO_ITEMS_UI_GROUP_ALL = []

WEKO_ITEMS_UI_APPLICATION_FOR_LIFE_ROLES = {}
""" Application for Life """

WEKO_ITEMS_UI_APPLICATION_FOR_ACCUMULATION_ROLES = {}
""" Application for Accumulation """

WEKO_ITEMS_UI_APPLICATION_FOR_COMBINATIONAL_ANALYSIS_ROLES = {}
""" Application for Combinational Analysis """

WEKO_ITEMS_UI_APPLICATION_FOR_PERFECTURES_ROLES = {}
""" Application for Perfectures """

WEKO_ITEMS_UI_APPLICATION_FOR_LOCATION_INFORMATION_ROLES = {}
""" Application for location information """

WEKO_ITEMS_UI_USAGE_APPLICATION_ITEM_TYPE = {}

WEKO_ITEMS_UI_LIST_ITEM_TYPE_NOT_NEED_AGREE = []

WEKO_ITEMS_UI_PERFECTURE_LOCATION_ITEM_TYPES = []

WEKO_ITEMS_UI_HIDE_AUTO_FILL_METADATA = []

WEKO_ITEMS_UI_USAGE_APPLICATION_TITLE_KEY = ""
WEKO_ITEMS_UI_USAGE_APPLICATION_TITLE = ""
WEKO_ITEMS_UI_USAGE_REPORT_TITLE_KEY = ""
WEKO_ITEMS_UI_USAGE_REPORT_TITLE = ""
WEKO_ITEMS_UI_OUTPUT_REGISTRATION_TITLE_KEY = ""
WEKO_ITEMS_UI_OUTPUT_REGISTRATION_TITLE = ""
WEKO_ITEMS_UI_AUTO_FILL_TITLE_SETTING = {}
WEKO_ITEMS_UI_AUTO_FILL_DATA_TYPE_SETTING = {}

WEKO_ITEMS_UI_HIDE_PUBLICATION_DATE = []

WEKO_ITEMS_UI_ACTION_ENDPOINT_KEY = {}

WEKO_ITEMS_UI_APPROVAL_MAIL_SUBITEM_KEY = {}

WEKO_ITEMS_UI_USAGE_APPLICATION_ITEM_TYPES_LIST = []

WEKO_ITEMS_UI_API_RETURN_CODE_ERROR = -1
"""Number response indicates that API is not processing request."""

WEKO_ITEMS_UI_MS_MIME_TYPE = {
    'ms_word': ['application/msword',
                'application/vnd.openxmlformats-officedocument.'
                'wordprocessingml.document',
                'application/vnd.openxmlformats-officedocument.'
                'wordprocessingml.template',
                'application/vnd.ms-word.document.macroEnabled.12',
                'application/vnd.ms-word.template.macroEnabled.12'
                ],
    'ms_powerpoint': ['application/vnd.ms-powerpoint',
                      'application/vnd.openxmlformats-officedocument.'
                      'presentationml.presentation',
                      'application/vnd.openxmlformats-officedocument.'
                      'presentationml.template',
                      'application/vnd.openxmlformats-officedocument.'
                      'presentationml.slideshow',
                      'application/vnd.ms-powerpoint.addin.macroEnabled.12',
                      'application/vnd.ms-powerpoint.presentation.'
                      'macroEnabled.12',
                      'applcation/vnd.ms-powerpoint.template.macroEnabled.12',
                      'application/vnd.ms-powerpoint.slideshow.macroEnabled.12'
                      ],
    'ms_excel': ['application/vnd.ms-excel',
                 'application/vnd.openxmlformats-officedocument.'
                 'spreadsheetml.sheet',
                 'application/vnd.openxmlformats-officedocument.'
                 'spreadsheetml.template',
                 'application/vnd.ms-excel.sheet.macroEnabled.12',
                 'application/vnd.ms-excel.template.macroEnabled.12',
                 'application/vnd.ms-excel.addin.macroEnabled.12',
                 'application/vnd.ms-excel.sheet.binary.macroEnabled.12']
}

WEKO_ITEMS_UI_FILE_SISE_PREVIEW_LIMIT = {
    'ms_word': 30,
    'ms_powerpoint': 20,
    'ms_excel': 10
}
"""Limit size of preview-able file."""

WEKO_ITEMS_UI_MULTIPLE_APPROVALS = True

WEKO_ITEMS_UI_EXPORT_TMP_PREFIX = 'weko_export_'

WEKO_ITEMS_UI_INDEX_PATH_SPLIT = '///'

WEKO_ITEMS_UI_SAVE_FREQUENCY = 600000
"""Save once every millisecond."""

WEKO_ITEMS_UI_RANKING_DEFAULT_SETTINGS = {
    'is_show': False,
    'new_item_period': 14,
    'statistical_period': 365,
    'display_rank': 10,
    'rankings': {"new_items": False, "most_reviewed_items": False, "most_downloaded_items": False, "most_searched_keywords": False, "created_most_items_user": False}
}

WEKO_ITEMS_UI_RANKING_BUFFER = 100

WEKO_ITEMS_UI_SEARCH_RANK_KEY_FILTER = ['']

WEKO_ITEMS_UI_SHARED_USER_ROLE_ID_LIST = [1,2,3]

WEKO_ITEMS_UI_RANKING_QUERY = dict(
    most_view_ranking = dict(
        query_class = ESWekoRankingQuery,
        query_config = dict(
            index='{}-stats-{}',
            doc_type='{}-day-aggregation',
            main_fields=['start_date', 'end_date', 'group_field', 'agg_size', 'count_field'],
            metric_fields=dict(),
            main_query={
                "size": 0,
                "query": {
                    "bool": {
                        "must": [
                            {
                                "range": {
                                    "timestamp": {
                                        "gte": "@start_date",
                                        "lte": "@end_date",
                                        "time_zone": "@time_zone"
                                    }
                                }
                            }
                        ],
                        "must_not": "@must_not"
                    }
                },
                "aggs": {
                    "my_buckets": {
                        "terms": {
                            "size": "@agg_size",
                            "order": {
                                "my_sum": "desc"
                            },
                            "script":{
                              "source": "def @group_field = doc['@group_field'].value; return @group_field.contains('.') ? @group_field.substring(0, @group_field.indexOf('.')) : @group_field;"
                            }
                        },
                        "aggs": {
                            "my_sum": {
                                "sum": {
                                    "field": "@count_field"
                                }
                            }
                        }
                    }
                }
            }
        )
    )
)
