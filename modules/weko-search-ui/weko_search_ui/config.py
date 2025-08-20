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

import pickle

from invenio_records_rest.config import RECORDS_REST_ENDPOINTS
from invenio_search import RecordsSearch
from invenio_stats.config import SEARCH_INDEX_PREFIX as index_prefix

WEKO_SEARCH_UI_SEARCH_INDEX_API = "/api/index/"

WEKO_SEARCH_UI_BASE_TEMPLATE = "weko_search_ui/base.html"
"""Default base template for the demo page."""

WEKO_SEARCH_UI_THEME_FRONTPAGE_TEMPLATE = "weko_search_ui/header_frontpage.html"
"""Reset invenio_theme.config['THEME_FRONTPAGE_TEMPLATE'] info"""

WEKO_SEARCH_UI_SEARCH_TEMPLATE = "weko_search_ui/search.html"

WEKO_SEARCH_UI_SEARCH_RESULTS_TEMPLATE = "weko_search_ui/search_results.html"

WEKO_SEARCH_UI_ADMIN_BULK_DELETE = "weko_search_ui/admin/item_management_display.html"

"""Reset search_ui_search config"""

WEKO_SEARCH_UI_JSTEMPLATE_LIST_RESULTS = "templates/weko_search_ui/itemlist.html"

WEKO_SEARCH_UI_JSTEMPLATE_TABLE_RESULTS = (
    "templates/weko_search_ui/itemtablecontents.html"
)

WEKO_ITEM_MANAGEMENT_JSTEMPLATE_RESULTS_EDIT = (
    "templates/weko_search_ui/itemListItemManagementEdit.html"
)

WEKO_SEARCH_UI_BULK_UPDATE_JSTEMPLATE_RESULTS = (
    "templates/weko_search_ui/bulkupdate_itemlist.html"
)

WEKO_ITEM_WORKFLOW_JSTEMPLATE_RESULTS_EDIT = (
    "templates/weko_search_ui/itemListWorkFlowItemLink.html"
)

WEKO_SEARCH_UI_JSTEMPLATE_RESULTS_BASIC = "templates/weko_search_ui/itemlistbasic.html"

WEKO_SEARCH_UI_JSTEMPLATE_INDEX = "templates/weko_search_ui/indexlist.html"

WEKO_SEARCH_UI_JSTEMPLATE_BREAD = "templates/weko_search_ui/breadcrumb.html"

WEKO_ITEM_MANAGEMENT_JSTEMPLATE_BREAD = (
    "templates/weko_search_ui/breadcrumbItemManagement.html"
)

WEKO_SEARCH_UI_JSTEMPLATE_COUNT = "templates/weko_search_ui/count.html"

SEARCH_UI_JSTEMPLATE_PAGINATION = "templates/weko_search_ui/pagination.html"

SEARCH_UI_ITEM_MANAGEMENT_JSTEMPLATE_PAGINATION = (
    "templates/weko_search_ui/paginationItemManagement.html"
)

SEARCH_UI_JSTEMPLATE_SELECT_BOX = "templates/weko_search_ui/selectbox.html"

SEARCH_UI_JSTEMPLATE_SORT_ORDER = "templates/weko_search_ui/togglebutton.html"

WEKO_ITEM_ADMIN_IMPORT_TEMPLATE = "weko_search_ui/admin/import.html"
"""import template for the import page."""

WEKO_ITEM_ADMIN_ROCRATE_IMPORT_TEMPLATE = "weko_search_ui/admin/rocrate_import.html"
"""import template for the rocrate import page."""

WEKO_SEARCH_UI_ADMIN_EXPORT_TEMPLATE = "weko_search_ui/admin/export.html"
"""Template for the Admin Bulk Export page."""

INDEX_IMG = "indextree/36466818-image.jpg"

# Opensearch description
WEKO_OPENSEARCH_SYSTEM_SHORTNAME = "WEKO"
WEKO_OPENSEARCH_SYSTEM_DESCRIPTION = (
    "WEKO - NII Scholarly and Academic Information Navigator"
)
WEKO_OPENSEARCH_IMAGE_URL = "static/favicon.ico"

RECORDS_REST_ENDPOINTS = pickle.loads(pickle.dumps(RECORDS_REST_ENDPOINTS, -1))
RECORDS_REST_ENDPOINTS["recid"][
    "search_factory_imp"
] = "weko_search_ui.query.es_search_factory"
RECORDS_REST_ENDPOINTS["recid"]["search_serializers"] = {
    "application/json": ("weko_records.serializers" ":json_v1_search"),
}

RECORDS_REST_ENDPOINTS["recid"]["search_index"] = "{}-weko".format(index_prefix)
RECORDS_REST_ENDPOINTS["recid"]["search_type"] = "item-v1.0.0"

# Opensearch endpoint
RECORDS_REST_ENDPOINTS["opensearch"] = pickle.loads(pickle.dumps(RECORDS_REST_ENDPOINTS["recid"], -1))
RECORDS_REST_ENDPOINTS["opensearch"][
    "search_factory_imp"
] = "weko_search_ui.query.opensearch_factory"
RECORDS_REST_ENDPOINTS["opensearch"]["list_route"] = "/opensearch/search"
RECORDS_REST_ENDPOINTS["opensearch"]["search_serializers"] = {
    "application/json": ("weko_records.serializers:opensearch_v1_search"),
}

RECORDS_REST_ENDPOINTS["recid"]["record_class"] = "weko_records.api:WekoRecord"
RECORDS_REST_ENDPOINTS["recid"]["record_serializers"] = {
    "application/json": ("invenio_records_rest.serializers:json_v1_response"),
    "application/vnd.citationstyles.csl+json": (
        "weko_records.serializers:csl_v1_response"
    ),
    "text/x-bibliography": ("weko_records.serializers:citeproc_v1_response"),
}

# Workspace endpoint
RECORDS_REST_ENDPOINTS["worksapce"] = pickle.loads(pickle.dumps(RECORDS_REST_ENDPOINTS["recid"], -1))
RECORDS_REST_ENDPOINTS["worksapce"]["list_route"] = "/workspace/search"
RECORDS_REST_ENDPOINTS["worksapce"]["search_serializers"] = {
    "application/json": ("weko_records.serializers:opensearch_v1_search"),
}

# RECORDS_REST_ENDPOINTS['recid']['read_permission_factory_imp'] = allow_all

INDEXER_DEFAULT_INDEX = "{}-weko-item-v1.0.0".format(index_prefix)  # Use direct index
INDEXER_DEFAULT_DOCTYPE = "item-v1.0.0"
INDEXER_DEFAULT_DOC_TYPE = "item-v1.0.0"
INDEXER_FILE_DOC_TYPE = "content"

SEARCH_UI_SEARCH_INDEX = "{}-weko".format(index_prefix)

# set item type aggs
RECORDS_REST_FACETS = dict()
RECORDS_REST_FACETS_NO_SEARCH_PERMISSION = dict()

RECORDS_REST_SORT_OPTIONS = dict()
RECORDS_REST_SORT_OPTIONS[SEARCH_UI_SEARCH_INDEX] = dict(
    controlnumber=dict(
        title="ID",
        fields=["control_number"],
        default_order="asc",
        order=2,
    ),
    wtl=dict(
        title="Title",
        fields=["title"],
        default_order="asc",
        order=3,
    ),
    creator=dict(
        title="Creator",
        fields=["creator.creatorName"],
        default_order="asc",
        order=4,
    ),
    upd=dict(
        title="Update date",
        fields=["_updated"],
        default_order="asc",
        order=5,
    ),
    createdate=dict(
        title="Create date",
        fields=["_created"],
        default_order="asc",
        order=6,
    ),
    pyear=dict(
        title="Date of Issued",
        fields=["date.value"],  # dateofissued
        default_order="asc",
        order=7,
        nested=dict(path="date", filter=dict(term={"date.dateType": "Issued"})),
    ),
    publish_date=dict(
        title="Publish date",
        fields=["publish_date"],  # date.value
        default_order="asc",
        order=8,
    ),
    # add 20181121 start
    custom_sort=dict(
        title="Custom",
        fields=["custom_sort.sort"],
        default_order="asc",
        order=9,
    ),
    itemType=dict(
        title="ItemType",
        fields=["itemtype.keyword"],
        default_order="asc",
        order=10,
    ),
    # add 20181121 end
    # add 20210505 start
    relevance=dict(
        title="Relevance",
        fields=[],
        default_order="asc",
        order=11,
    ),
    # add 20210505 end
    temporal=dict(
        title="Temporal",
        fields=["date_range1.gte"],
        default_order="asc",
        order=12,
    ),
)

WEKO_SEARCH_REST_ENDPOINTS = dict(
    recid=dict(
        pid_type="recid",
        pid_minter="recid",
        pid_fetcher="recid",
        search_class=RecordsSearch,
        search_index=SEARCH_UI_SEARCH_INDEX,
        search_type="item-v1.0.0",
        search_factory_imp="weko_search_ui.query.weko_search_factory",
        # record_class='',
        record_serializers={
            "application/json": (
                "invenio_records_rest.serializers" ":json_v1_response"
            ),
        },
        search_serializers={
            "application/json": ("weko_records.serializers" ":json_v1_search"),
        },
        index_route="/index/",
        search_api_route="/<string:version>/records",
        search_result_list_route="/<string:version>/records/list",
        links_factory_imp="weko_search_ui.links:default_links_factory",
        default_media_type="application/json",
        max_result_window=10000,
    ),
)

WEKO_SEARCH_KEYWORDS_DICT = {
    "nested": {
        "id": (
            "",
            {
                "id_attr": {
                    "identifier": ("relation.relatedIdentifier", "identifierType=identifier"),
                    "URI": ("identifier", "identifierType=*"),
                    "fullTextURL": ("file.URI", "objectType=fullTextURL"),
                    "selfDOI": ("identifierRegistration", "identifierType=selfDOI"),
                    "ISBN": ("relation.relatedIdentifier", "identifierType=*"),
                    "ISSN": ("sourceIdentifier", "identifierType=*"),
                    "NCID": [
                        ("relation.relatedIdentifier", "identifierType=*"),
                        ("sourceIdentifier", "identifierType=*"),
                    ],
                    "PMID": ("relation.relatedIdentifier", "identifierType=*"),
                    "DOI": ("relation.relatedIdentifier", "identifierType=*"),
                    "NAID": ("relation.relatedIdentifier", "identifierType=*"),
                    "ICHUSHI": ("relation.relatedIdentifier", "identifierType=*"),
                }
            },
        ),
        "license": ("content", {"license": ("content.licensetype.raw")}),
    },
    "string": {
        "title": ["search_title", "search_title.ja"],
        "creator": ["search_creator", "search_creator.ja"],
        "des": ["search_des", "search_des.ja"],
        "publisher": ["search_publisher", "search_publisher.ja"],
        "cname": ["search_contributor", "search_contributor.ja"],
        "itemtype": ("itemtype.keyword", str),
        "type": {
            "type.raw": [
                "conference paper",
                "data paper",
                "departmental bulletin paper",
                "editorial",
                "journal article",
                "newspaper",
                "periodical",
                "review article",
                "software paper",
                "article",
                "book",
                "book part",
                "cartographic material",
                "map",
                "conference object",
                "conference proceedings",
                "conference poster",
                "dataset",
                "interview",
                "image",
                "still image",
                "moving image",
                "video",
                "lecture",
                "patent",
                "internal report",
                "report",
                "research report",
                "technical report",
                "policy report",
                "report part",
                "working paper",
                "data management plan",
                "sound",
                "thesis",
                "bachelor thesis",
                "master thesis",
                "doctoral thesis",
                "interactive resource",
                "learning object",
                "manuscript",
                "musical notation",
                "research proposal",
                "software",
                "technical documentation",
                "workflow",
                "other",
            ]
        },
        "mimetype": "file.mimeType",
        "language": {
            "language": [
                "jpn",
                "eng",
                "fra",
                "ita",
                "deu",
                "spa",
                "zho",
                "rus",
                "lat",
                "msa",
                "epo",
                "ara",
                "ell",
                "kor",
                "other"
            ]
        },
        "srctitle": ["sourceTitle", "sourceTitle.ja"],
        "spatial": "geoLocation.geoLocationPlace",
        "temporal": "temporal",
        "version": "versiontype",
        "dissno": "dissertationNumber",
        "degreename": ["degreeName", "degreeName.ja"],
        "dgname": ["dgName", "dgName.ja"],
        "wid": ("creator.nameIdentifier", str),
        "iid": ("path.tree", int),
    },
    "date": {
        "filedate": [
            ("from", "to"),
            (
                "file.date",
                {
                    "fd_attr": {
                        "file.date.dateType": [
                            "Accepted",
                            "Available",
                            "Collected",
                            "Copyrighted",
                            "Created",
                            "Issued",
                            "Submitted",
                            "Updated",
                            "Valid",
                        ]
                    }
                },
            ),
        ],
        "dategranted": [("from", "to"), "dateGranted"],
        "date_range1": [("from", "to"), "date_range1"],
        "date_range2": [("from", "to"), "date_range2"],
        "date_range3": [("from", "to"), "date_range3"],
        "date_range4": [("from", "to"), "date_range4"],
        "date_range5": [("from", "to"), "date_range5"],
    },
    "object": {
        "subject": (
            "subject",
            {
                "sbjscheme": {
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
                        "SciVal",
                    ]
                }
            },
        )
    },
    "text": {
        "text1": "text1",
        "text2": "text2",
        "text3": "text3",
        "text4": "text4",
        "text5": "text5",
        "text6": "text6",
        "text7": "text7",
        "text8": "text8",
        "text9": "text9",
        "text10": "text10",
        "text11": "text11",
        "text12": "text12",
        "text13": "text13",
        "text14": "text14",
        "text15": "text15",
        "text16": "text16",
        "text17": "text17",
        "text18": "text18",
        "text19": "text19",
        "text20": "text20",
        "text21": "text21",
        "text22": "text22",
        "text23": "text23",
        "text24": "text24",
        "text25": "text25",
        "text26": "text26",
        "text27": "text27",
        "text28": "text28",
        "text29": "text29",
        "text30": "text30",
    },
    "range": {
        "integer_range1": [("from", "to"), "integer_range1"],
        "integer_range2": [("from", "to"), "integer_range2"],
        "integer_range3": [("from", "to"), "integer_range3"],
        "integer_range4": [("from", "to"), "integer_range4"],
        "integer_range5": [("from", "to"), "integer_range5"],
        "float_range1": [("from", "to"), "float_range1"],
        "float_range2": [("from", "to"), "float_range2"],
        "float_range3": [("from", "to"), "float_range3"],
        "float_range4": [("from", "to"), "float_range4"],
        "float_range5": [("from", "to"), "float_range5"],
    },
    "geo_distance": {"geo_point1": [("lat", "lon", "distance"), "geo_point1"]},
    "geo_shape": {"geo_shape1": [("lat", "lon", "distance"), "geo_shape1"]},
}

WEKO_SEARCH_TYPE_KEYWORD = "keyword"

WEKO_SEARCH_TYPE_INDEX = "index"

WEKO_SEARCH_MAX_RESULT = 10000
"""Maximum total number of records retrieved from a ES query."""

WEKO_SEARCH_MAX_FEEDBACK_MAIL = 10000
"""Maximum number of feedback mail could be send."""

WEKO_SEARCH_TYPE_DICT = {"FULL_TEXT": "0", "KEYWORD": "1", "INDEX": "2"}
WEKO_SYS_USER = "System Administrator"

WEKO_REPO_USER = "Repository Administrator"

WEKO_FLOW_DEFINE = {"flow_name": "Registration Flow",
                    "repository_id": "Root Index",}

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
        "action": "ADD",
        "workflow_flow_action_id": "0",
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
        "action": "ADD",
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
        "action": "ADD",
        "workflow_flow_action_id": "0",
    },
]

WEKO_IMPORT_CHECK_LIST_NAME = ["No", "Item Type", "Item Id", "Title", "Check result"]

WEKO_IMPORT_LIST_NAME = [
    "No",
    "Start Date",
    "End Date",
    "Item Id",
    "Action",
    "Work Flow Status",
]
WEKO_ADMIN_LIFETIME_DEFAULT = 1800

WEKO_IMPORT_EMAIL_PATTERN = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
WEKO_IMPORT_PUBLISH_STATUS = ["public", "private"]
WEKO_IMPORT_DOI_TYPE = ["JaLC", "Crossref", "DataCite", "NDL JaLC"]

WEKO_IMPORT_SUBITEM_DATE_ISO = "subitem_1582683677698"
"""Subitem ID of property Date (ISO-8601)."""

#: Change identifier mode file language list
WEKO_ADMIN_IMPORT_CHANGE_IDENTIFIER_MODE_FILE_LANGUAGES = ["en", "ja"]
#: Change identifier mode file location
WEKO_ADMIN_IMPORT_CHANGE_IDENTIFIER_MODE_FILE_LOCATION = (
    "/code/modules/weko-search-ui/weko_search_ui/static/change_identifier_mode/"
)
#: Change identifier mode first name file
WEKO_ADMIN_IMPORT_CHANGE_IDENTIFIER_MODE_FIRST_FILE_NAME = "change_identifier_mode"
#: Change identifier mode file extension
WEKO_ADMIN_IMPORT_CHANGE_IDENTIFIER_MODE_FILE_EXTENSION = ".txt"

WEKO_EXPORT_TEMPLATE_BASIC_ID = [
    "#.id",
    ".uri",
    ".metadata.path[0]",
    ".pos_index[0]",
    ".publish_status",
    ".feedback_mail[0]",
    ".researchmap_linkage",
    ".cnri",
    ".doi_ra",
    ".doi",
    ".edit_mode",
]
WEKO_EXPORT_TEMPLATE_BASIC_NAME = [
    "#ID",
    "URI",
    ".IndexID[0]",
    ".POS_INDEX[0]",
    ".PUBLISH_STATUS",
    ".FEEDBACK_MAIL[0]",
    ".RESEAECHMAP_LINKAGE",
    ".CNRI",
    ".DOI_RA",
    ".DOI",
    "Keep/Upgrade Version",
]
WEKO_EXPORT_TEMPLATE_BASIC_OPTION = [
    "#",
    "",
    "Allow Multiple",
    "Allow Multiple",
    "Required",
    "Allow Multiple",
    "",
    "",
    "",
    "",
    "Required",
]

WEKO_IMPORT_SYSTEM_ITEMS = ["resource_type", "version_type", "access_right"]
WEKO_IMPORT_THUMBNAIL_FILE_TYPE = [
    "gif",
    "jpg",
    "jpe",
    "jpeg",
    "png",
    "bmp",
    "tiff",
    "tif",
]
VERSION_TYPE_URI = {
    "AO": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
    "SMUR": "http://purl.org/coar/version/c_71e4c1898caa6e32",
    "AM": "http://purl.org/coar/version/c_ab4af688f83e57aa",
    "P": "http://purl.org/coar/version/c_fa2ee174bc00049f",
    "VoR": "http://purl.org/coar/version/c_970fb48d4fbd8a85",
    "CVoR": "http://purl.org/coar/version/c_e19f295774971610",
    "EVoR": "http://purl.org/coar/version/c_dc82b40f9837b551",
    "NA": "http://purl.org/coar/version/c_be7fb7dd8ff6fe43",
}
ACCESS_RIGHT_TYPE_URI = {
    "embargoed access": "http://purl.org/coar/access_right/c_f1cf",
    "metadata only access": "http://purl.org/coar/access_right/c_14cb",
    "open access": "http://purl.org/coar/access_right/c_abf2",
    "restricted access": "http://purl.org/coar/access_right/c_16ec",
}
DATE_ISO_TEMPLATE_URL = "/static/templates/weko_deposit/datepicker_multi_format.html"

RESOURCE_TYPE_URI = {
    "conference paper": "http://purl.org/coar/resource_type/c_5794",
    "data paper": "http://purl.org/coar/resource_type/c_beb9",
    "departmental bulletin paper": "http://purl.org/coar/resource_type/c_6501",
    "editorial": "http://purl.org/coar/resource_type/c_b239",
    "journal": "http://purl.org/coar/resource_type/c_0640",
    "journal article": "http://purl.org/coar/resource_type/c_6501",
    "newspaper": "http://purl.org/coar/resource_type/c_2fe3",
    "periodical": "http://purl.org/coar/resource_type/c_2659",
    "review article": "http://purl.org/coar/resource_type/c_dcae04bc",
    "other periodical":"http://purl.org/coar/resource_type/QX5C-AR31",
    "software paper": "http://purl.org/coar/resource_type/c_7bab",
    "article": "http://purl.org/coar/resource_type/c_6501",
    "book": "http://purl.org/coar/resource_type/c_2f33",
    "book part": "http://purl.org/coar/resource_type/c_3248",
    "cartographic material": "http://purl.org/coar/resource_type/c_12cc",
    "map": "http://purl.org/coar/resource_type/c_12cd",
    "conference output":"http://purl.org/coar/resource_type/c_c94f",
    "conference presentation":"http://purl.org/coar/resource_type/c_c94f",
    "conference object": "http://purl.org/coar/resource_type/c_c94f",
    "conference proceedings": "http://purl.org/coar/resource_type/c_f744",
    "conference poster": "http://purl.org/coar/resource_type/c_6670",
    "dataset": "http://purl.org/coar/resource_type/c_ddb1",
    "interview": "http://purl.org/coar/resource_type/c_26e4",
    "image": "http://purl.org/coar/resource_type/c_c513",
    "still image": "http://purl.org/coar/resource_type/c_ecc8",
    "moving image": "http://purl.org/coar/resource_type/c_8a7e",
    "video": "http://purl.org/coar/resource_type/c_12ce",
    "lecture": "http://purl.org/coar/resource_type/c_8544",
    "patent": "http://purl.org/coar/resource_type/c_15cd",
    "internal report": "http://purl.org/coar/resource_type/c_18ww",
    "report": "http://purl.org/coar/resource_type/c_93fc",
    "research report": "http://purl.org/coar/resource_type/c_18ws",
    "technical report": "http://purl.org/coar/resource_type/c_18gh",
    "policy report": "http://purl.org/coar/resource_type/c_186u",
    "report part": "http://purl.org/coar/resource_type/c_ba1f",
    "working paper": "http://purl.org/coar/resource_type/c_8042",
    "data management plan": "http://purl.org/coar/resource_type/c_ab20",
    "sound": "http://purl.org/coar/resource_type/c_18cc",
    "thesis": "http://purl.org/coar/resource_type/c_46ec",
    "bachelor thesis": "http://purl.org/coar/resource_type/c_7a1f",
    "master thesis": "http://purl.org/coar/resource_type/c_bdcc",
    "doctoral thesis": "http://purl.org/coar/resource_type/c_db06",
    "interactive resource": "http://purl.org/coar/resource_type/c_e9a0",
    "learning object": "http://purl.org/coar/resource_type/c_e059",
    "manuscript": "http://purl.org/coar/resource_type/c_0040",
    "musical notation": "http://purl.org/coar/resource_type/c_18cw",
    "research proposal": "http://purl.org/coar/resource_type/c_baaf",
    "software": "http://purl.org/coar/resource_type/c_5ce6",
    "technical documentation": "http://purl.org/coar/resource_type/c_71bd",
    "workflow": "http://purl.org/coar/resource_type/c_393c",
    "other": "http://purl.org/coar/resource_type/c_1843",
    "aggregated data": "http://purl.org/coar/resource_type/ACF7-8YT9",
    "clinical trial data": "http://purl.org/coar/resource_type/c_cb28",
    "compiled data": "http://purl.org/coar/resource_type/FXF3-D3G7",
    "encoded data": "http://purl.org/coar/resource_type/AM6W-6QAW",
    "experimental data": "http://purl.org/coar/resource_type/63NG-B465",
    "genomic data": "http://purl.org/coar/resource_type/A8F1-NPV9",
    "geospatial data": "http://purl.org/coar/resource_type/2H0M-X761",
    "laboratory notebook": "http://purl.org/coar/resource_type/H41Y-FW7B",
    "measurement and test data": "http://purl.org/coar/resource_type/DD58-GFSX",
    "observational data": "http://purl.org/coar/resource_type/FF4C-28RK",
    "recorded data": "http://purl.org/coar/resource_type/CQMR-7K63",
    "simulation data": "http://purl.org/coar/resource_type/W2XT-7017",
    "survey data": "http://purl.org/coar/resource_type/NHD0-W6SY",
    "design patent":"http://purl.org/coar/resource_type/C53B-JCY5/",
    "PCT application":"http://purl.org/coar/resource_type/SB3Y-W4EH/",
    "plant patent":"http://purl.org/coar/resource_type/Z907-YMBB/",
    "plant variety protection":"http://purl.org/coar/resource_type/GPQ7-G5VE/",
    "software patent":"http://purl.org/coar/resource_type/MW8G-3CR8/",
    "trademark":"http://purl.org/coar/resource_type/H6QP-SC1X/",
    "utility model":"http://purl.org/coar/resource_type/9DKX-KSAF/",
    "commentary":"http://purl.org/coar/resource_type/D97F-VB57/",
    'design': 'http://purl.org/coar/resource_type/542X-3S04/',
    'industrial design': 'http://purl.org/coar/resource_type/JBNF-DYAD/',
    'layout design': 'http://purl.org/coar/resource_type/BW7T-YM2G/',
    'peer review': 'http://purl.org/coar/resource_type/H9BQ-739P/',
    'research protocol': 'http://purl.org/coar/resource_type/YZ1N-ZFT9/',
    'source code':'http://purl.org/coar/resource_type/QH80-2R4E/',
    'transcription': 'http://purl.org/coar/resource_type/6NC7-GK9S/',
}

WEKO_IMPORT_VALIDATE_MESSAGE = {
    "%r is too long": "%rの数が上限数を超えています。",
    "%r is not one of %r": "%rは次の決められた選択肢に含まれていません。%r",
    "%r is a required property": "%rは必須項目です。",
}

WEKO_SEARCH_UI_BULK_EXPORT_TASK = "KEY_EXPORT_ALL"
"""Template for the Admin Bulk Export page."""

WEKO_SEARCH_UI_BULK_EXPORT_URI = "URI_EXPORT_ALL"
"""Template for the Admin Bulk Export page."""

WEKO_SEARCH_UI_BULK_EXPORT_MSG = "MSG_EXPORT_ALL"
"""Template for the Admin Bulk Export page."""

WEKO_SEARCH_UI_TO_NUMBER_FORMAT = "99999999999999.99"
"""The format of to_number function."""

WEKO_SEARCH_UI_BULK_EXPORT_RUN_MSG = "RUN_MSG_EXPORT_ALL"
"""Bulk export running message."""

WEKO_SEARCH_UI_BULK_EXPORT_FILE_CREATE_RUN_MSG = "RUN_MSG_EXPORT_ALL_FILE_CREATE"
"""Bulk export file create running message."""

WEKO_SEARCH_UI_BULK_EXPORT_EXPIRED_TIME = 1440
"""Template for the Admin Bulk Export page."""

WEKO_SEARCH_UI_EXPORT_FILE_RETENTION_DAYS = 7
"""Retention period for export files in days."""

WEKO_SEARCH_UI_FILE_DOWNLOAD_TTL_BUFFER = 3600
"""Time (in seconds) to extend file TTL during download."""

WEKO_SEARCH_UI_BULK_EXPORT_TASKID_EXPIRED_TIME = 1

WEKO_SEARCH_UI_BULK_EXPORT_LIMIT = 300
"""The number of items exported to tsv/csv file each once.
Note: If set to 500 or more, errors may occur during export processing.
"""

WEKO_SEARCH_UI_BULK_EXPORT_RETRY = 5
"""Number of export retries."""

WEKO_SEARCH_UI_IMPORT_TMP_PREFIX = "weko_import_"
"""Import tmp prefix."""

WEKO_SEARCH_UI_ROCRATE_IMPORT_TMP_PREFIX = "weko_rocrate_import_"
"""RO-Crate Import tmp prefix."""

WEKO_SEARCH_UI_IMPORT_UNUSE_FILES_URI = "import_unuse_files_uri_{}"
"""Cache key unuse file. uri."""

WEKO_SEARCH_UI_BULK_EXPORT_RETRY_INTERVAL = 1
""" retry interval(sec) """

CELERY_RESULT_PERSISTENT = True
""" If set to True, result messages will be persistent. This means the messages will not be lost after a broker restart. The default is for the results to be transient."""
CELERY_TASK_TRACK_STARTED=True
""" If True the task will report its status as ‘started’ when the task is executed by a worker. """
WEKO_SEARCH_UI_FACET_LANG_DISP_FLG = False
""" Enable the Facet Search specified language display feature. """

CHILD_INDEX_THUMBNAIL_WIDTH = 100
""" child index thumbnail width in result index serch"""

CHILD_INDEX_THUMBNAIL_HEIGHT = 100
""" child index thumbnail height in result index serch"""

WEKO_SEARCH_UI_RESULT_TMP_PREFIX = 'weko_search_result_list_'

SWORD_METADATA_FILE = "metadata/sword.json"
""" Metadata file name for SWORDBagIt. """

ROCRATE_METADATA_FILE = "data/ro-crate-metadata.json"
""" Metadata file name for RO-Crate+Bagit. """

ROCRATE_METADATA_WK_CONTEXT_V1 = "http://purl.org/wk/v1/wk-context.jsonld"
""" Metadata context file name for RO-Crate+Bagit. """
