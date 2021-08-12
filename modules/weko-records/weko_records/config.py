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

COPY_NEW_FIELD = True