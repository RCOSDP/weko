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

"""weko records config file."""

WEKO_ITEMPROPS_SCHEMAID_CREATOR = 73
# Item property ID of Creator schema

WEKO_ITEMPROPS_SCHEMAID_DESCRIP = 66
# Item property ID of Description schema

WEKO_ITEMPROPS_SCHEMAID_LANGUAG = 71
# Item property ID of Language schema

WEKO_ITEMPROPS_SCHEMAID_VERSION = 76
# Item property ID of Version schema

WEKO_ITEMPROPS_SCHEMAID_DOI = 86
# Item property ID of Identifier schema

WEKO_ITEMPROPS_SCHEMAID_ALTITLE = 69
# Item property ID of Alternative title schema

WEKO_ITEMPROPS_SCHEMAID_PAGES = 85
# Item property ID of Number of Pages schema

WEKO_ITEMPROPS_SCHEMAID_VOLUME = 88
# Item property ID of Volume number schema

WEKO_ITEMPROPS_SCHEMAID_ISSUENO = 87
# Item property ID of Issue number schema

WEKO_ITEMPROPS_SCHEMAID_PUBLISH = 68
# Item property ID of Publisher schema

WEKO_ITEMTYPE_ID_BASEFILESVIEW = 10

WEKO_ITEMTYPE_EXCLUDED_KEYS = ['required', 'isRequired', 'title', 'uniqueKey',
                               'title_i18n', 'isShowList', 'isSpecifyNewline',
                               'isHide', 'enum', 'titleMap', 'title_i18n_temp',
                               'currentEnum']

WEKO_RECORDS_AUTHOR_KEYS = ['nameIdentifierScheme', 'nameIdentifier',
                            'nameIdentifierURI',
                            'creatorName',
                            'familyName',
                            'givenName',
                            'creatorAlternative',
                            'affiliationNameIdentifier',
                            'affiliationNameIdentifierScheme',
                            'affiliationNameIdentifierURI',
                            'affiliationName']
"""List author key."""

WEKO_RECORDS_AUTHOR_NONE_LANG_KEYS = ['nameIdentifierScheme', 'nameIdentifier',
                                      'nameIdentifierURI',
                                      'affiliationNameIdentifier',
                                      'affiliationNameIdentifierScheme',
                                      'affiliationNameIdentifierURI']
"""List author none language keys."""

WEKO_RECORDS_ALTERNATIVE_NAME_KEYS = ['creatorAlternative',
                                      'creatorAlternativeLang']
"""List alternative name key."""

WEKO_RECORDS_AFFILIATION_NAME_KEYS = ['affiliationName', 'affiliationNameLang']
"""List affiliation name key."""

WEKO_RECORDS_MANAGED_KEYS =  ["accessrole","affiliationNameIdentifierScheme","bibliographicIssueDateType","catalog_access_right","catalog_description_type","catalog_file_object_type","catalog_identifier_type",
"catalog_license_type","catalog_subject_scheme","contributorAffiliationScheme","contributor_type","contributorType","creatorNameType","dateType","displaytype","fileDateType","holding_agent_name_identifier_scheme","jpcoar_dataset_series","nameIdentifierScheme","nameType","objectType","resourcetype","subitem_access_right","subitem_apc","subitem_award_number_type","subitem_conference_country","subitem_date_issued_type","subitem_degreegrantor_identifier_scheme","subitem_description_type","subitem_funder_identifier_type","subitem_funding_stream_identifier_type","subitem_identifier_reg_type","subitem_identifier_type","subitem_relation_type","subitem_relation_type_select","subitem_source_identifier_type","subitem_subject_scheme","subitem_version_type"]

WEKO_RECORDS_TITLE_TITLE = 'Title'
"""Title."""

WEKO_RECORDS_LANGUAGE_TITLES = ['Language', '言語']
"""List language titles."""

WEKO_RECORDS_EVENT_TITLES = ['調査開始／終了', 'イベント',
                             'Event', '開始時点/終了時点',
                             'Time Period Event']
"""List event titles."""

WEKO_RECORDS_TIME_PERIOD_TITLES = ['時間的範囲', 'Time Period',
                                   '調査日', 'Date', '対象時期',
                                   'TimePeriod', 'Time Period(s)', 'Temporal']
"""List time period titles."""

"""
WEKO_TEST_FIELD = {
    "1" : {
        "geo_point1" : {
            "input_type":"geo_point",
            "path":{
                "lat":"$.item_1551265326081.attribute_value_mlt[?subitem_1551256775293=='Location_sub'].subitem_1551256778926[*].subitem_1551256814806",
                "lon":"$.item_1551265326081.attribute_value_mlt[*].subitem_1551256778926[*].subitem_1551256783928"
            },
            "path_type":{
                "lat":"json",
                "lon":"json"
            }
        },

        "geo_shape1" : {
            "input_type":"geo_shape",
            "path":{
                "type":"",
                "coordinates":""
            },
            "path_type":{
                "type":"",
                "coordinates":""
            }
        },

        "integer_range1":{
            "input_type":"range",
            "path":{
                "gte":"$.item_1551265553273.attribute_value_mlt[*].subitem_1551256248092",
                "lte":"$.item_1551265553273.attribute_value_mlt[*].subitem_1551256248092"
            },
            "path_type":{
                "gte":"json",
                "lte":"json"
            }
        },
        "float_range1":{
            "input_type":"range",
            "path":{
                "gte":"",
                "lte":""
            },
            "path_type":{
                "gte":"",
                "lte":""
            }

        },

        "date_range1":{
            "input_type":"range",
            "path":{
                "gte":"",
                "lte":""
            },
            "path_type":{
                "gte":"",
                "lte":""
            }
        },
        "text1" : {
            "input_type":"text",
            "path" : "$.item_1551264308487.attribute_value_mlt[*].subitem_1551255647225",
            "path_type":"json"
        },
        "text2" : {
            "input_type":"text",
            "path" : ["jpcoar",".//dc:title[@xml:lang='en']"],
            "path_type":"xml"
        }
    }
}
"""

WEKO_TEST_FIELD = {
    "20": {
        "date_range1": {
            "input_type": "range",
            "path": {
                "gte": "$.item_1602145192334.attribute_value_mlt[0].subitem_1602144573160",
                "lte": "$.item_1602145192334.attribute_value_mlt[1].subitem_1602144573160"
            },
            "path_type": {
                "gte": "json",
                "lte": "json"
            }
        },
        "text1": {
            "input_type": "text",
            "path": "$.item_1592405734122.attribute_value_mlt[*].subitem_1592369405220",
            "path_type": "json"
        },
        "text2": {
            "input_type": "text",
            "path": "$.item_1551264822581.attribute_value_mlt[*].subitem_1592472785169",
            "path_type": "json"
        },
        "text3": {
            "input_type": "text",
            "path": "$.item_1551264846237.attribute_value_mlt[*].subitem_1551255577890",
            "path_type": "json"
        },
        "text4": {
            "input_type": "text",
            "path": "$.item_1570068313185.attribute_value_mlt[*].subitem_1586419454219",
            "path_type": "json"
        },
        "text5": {
            "input_type": "text",
            "path": "$.item_1602145817646.attribute_value_mlt[*].subitem_1602142814330",
            "path_type": "json"
        },
        "text6": {
            "input_type": "text",
            "path": ".metadata.item_1602145850035.attribute_value_mlt[*].subitem_1602142123771",
            "path_type": "json"
        },
        "text7": {
            "input_type": "text",
            "path": "$.item_1592405736602.attribute_value_mlt[0].subitem_1602215239359",
            "path_type": "json"
        },
        "text8": {
            "input_type": "text",
            "path": "$.item_1592405735401.attribute_value_mlt[*].subitem_1602214558730",
            "path_type": "json"
        },
        "text9": {
            "input_type": "text",
            "path": "$.item_1551264917614.attribute_value_mlt[*].subitem_1551255702686",
            "path_type": "json"
        },
        "text10": {
            "input_type": "text",
            "path": "$.item_1602147887655.attribute_value_mlt[*].subitem_1602143328410",
            "path_type": "json"
        },
        "text11": {
            "input_type": "text",
            "path": "$.item_1588260046718.attribute_value_mlt[*].subitem_1591178807921",
            "path_type": "json"
        },

    }
}


COPY_NEW_FIELD = True

WEKO_RECORDS_SYSTEM_COMMA = "-,-"
"""The system comma used to break metadata subitems."""

WEKO_RECORDS_REST_ENDPOINTS = {
    'oa_status_callback': {
        'route': '/<string:version>/oa_status/callback',
        'default_media_type': 'application/json',
    }
}
"""REST endpoints."""

WEKO_RECORDS_API_LIMIT_RATE_DEFAULT = ['100 per minute']
"""API rate limit."""
