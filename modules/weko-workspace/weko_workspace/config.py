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

"""Configuration for weko-workspace."""

from flask_babelex import lazy_gettext as _
from invenio_stats.config import SEARCH_INDEX_PREFIX as index_prefix

# Front-end variable definition
WEKO_WORKSPACE_BASE_TEMPLATE = 'weko_workspace/workspace_base.html'
"""Default base template for the demo page."""

# Back-end variable definition
WEKO_WORKSPACE_PID_TYPE = 'recid'
"""Get object_uuid."""

WEKO_WORKSPACE_ITEM = {
    "recid": None,
    "title": None,
    "favoriteSts": None,
    "readSts": None,
    "peerReviewSts": None,
    "doi": None,
    "resourceType": None,
    "authorlist": None,
    "accessCnt": None,
    "downloadCnt": None,
    "itemStatus": None,
    "publicationDate": None,
    "magazineName": None,
    "conferenceName": None,
    "volume": None,
    "issue": None,
    "funderName": None,
    "awardTitle": None,
    "fbEmailSts": None,
    "relation": None,
    "relationType": None,
    "relationTitle": None,
    "relationUrl": None,
    "connectionToPaperSts": None,
    "connectionToDatasetSts": None,
    "fileSts": None,
    "fileCnt": None,
    "publicSts": None,
    "publicCnt": None,
    "embargoedSts": None,
    "embargoedCnt": None,
    "restrictedPublicationSts": None,
    "restrictedPublicationCnt": None,
}
"""Default item template for the workspace item list page."""

WEKO_WORKSPACE_AUTOFILL_JAMAS_XML_DATA_KEYS = [
    "dc:title",
    "dc:creator",
    "prism:organization",
    "prism:publicationName",
    "prism:volume",
    "prism:number",
    "prism:startingPage",
    "prism:pageRange",
    "prism:publicationDate",
    "prism:issn",
    "prism:eIssn",
    "prism:doi",
]
"""Jamas XML data keys"""

WEKO_WORKSPACE_AUTOFILL_JAMAS_REQUIRED_ITEM = [
    "title",
    "creator",
    "sourceTitle",
    "sourceIdentifier",
    "volume",
    "issue",
    "pageStart",
    "date",
    "relation"
]
"""Jamas required item"""

WEKO_WORKSPACE_ARTICLE_TYPES = [
    "conference paper",
    "data paper",
    "departmental bulletin paper",
    "editorial",
    "journal",
    "journal article",
    "newspaper",
    "review article",
    "other periodical",
    "software paper",
    "article"
]
"""Definition of Article categories"""

WEKO_WORKSPACE_DATASET_TYPES = [
    "aggregated data",
    "clinical trial data",
    "compiled data",
    "dataset",
    "encoded data",
    "experimental data",
    "genomic data",
    "geospatial data",
    "laboratory notebook",
    "measurement and test data",
    "observational data",
    "recorded data",
    "simulation data",
    "survey data"
]
"""Definition of Dataset categories"""

WEKO_WORKSPACE_DEFAULT_FILTERS = {
    "resource_type": {
        "label": "Resource Type",
        "options": [
            "conference paper",
            "data paper",
            "departmental bulletin paper",
            "editorial",
            "journal",
            "journal article",
            "newspaper",
            "review article",
            "other periodical",
            "software paper",
            "article",
            "book",
            "book part",
            "cartographic material",
            "map",
            "conference output",
            "conference presentation",
            "conference proceedings",
            "conference poster",
            "aggregated data",
            "clinical trial data",
            "compiled data",
            "dataset",
            "encoded data",
            "experimental data",
            "genomic data",
            "geospatial data",
            "laboratory notebook",
            "measurement and test data",
            "observational data",
            "recorded data",
            "simulation data",
            "survey data",
            "image",
            "still image",
            "moving image",
            "video",
            "lecture",
            "design patent",
            "patent",
            "PCT application",
            "plant patent",
            "plant variety protection",
            "software patent",
            "trademark",
            "utility model",
            "report",
            "research report",
            "technical report",
            "policy report",
            "working paper",
            "data management plan",
            "sound",
            "thesis",
            "bachelor thesis",
            "master thesis",
            "doctoral thesis",
            "commentary",
            "design",
            "industrial design",
            "interactive resource",
            "layout design",
            "learning object",
            "manuscript",
            "musical notation",
            "peer review",
            "research proposal",
            "research protocol",
            "software",
            "source code",
            "technical documentation",
            "transcription",
            "workflow",
            "other",
        ],
        "default": [],  # 複数選択フィールド、文字列配列を保持
    },
    "peer_review": {
        "label": "Peer Review",
        "options": ["Yes", "No"],
        "default": [],  # 単一選択フィールド、デフォルトは未選択で null を使用
    },
    "related_to_paper": {
        "label": "Related To Paper",
        "options": ["Yes", "No"],
        "default": None,  # 単一選択フィールド、デフォルトは未選択で null を使用
    },
    "related_to_data": {
        "label": "Related To Data",
        "options": ["Yes", "No"],
        "default": None,  # 単一選択フィールド、デフォルトは未選択で null を使用
    },
    "funder_name": {
        "label": "Funding Reference - Funder Name",
        "options": [],  # 動的フィールド、初期は空、後でリストデータに基づいて填充される
        "default": [],  # 複数選択フィールド、空配列を保持
    },
    "award_title": {
        "label": "Funding Reference - Award Title",
        "options": [],  # 動的フィールド、初期は空、後でリストデータに基づいて填充される
        "default": [],  # 複数選択フィールド、空配列を保持
    },
    "file_present": {
        "label": "File",
        "options": ["Yes", "No"],
        "default": None,  # 単一選択フィールド、デフォルトは未選択で null を使用
    },
    "favorite": {
        "label": "Favorite",
        "options": ["Yes", "No"],
        "default": None,  # 単一選択フィールド、デフォルトは未選択で null を使用
    },
}
"""Default filter options for the workspace item list page."""

WEKO_WORKSPACE_OA_STATUS_MAPPING = {
    "Unprocessed": "Unlinked",
    "Unprocessed Pending": "Unlinked",
    "Processing Metadata Registered": "Metadata Registered",
    "Processing Metadata Registered (Fulltext Requested)": "Fulltext Requested",
    "Processing Metadata Registered (Fulltext Obtained)": "Fulltext Provided",
    "Processing Metadata Not Registered (Fulltext Requested)": "Unlinked (Fulltext Requested)",
    "Processing Metadata Not Registered (Fulltext Obtained)": "Unlinked (Fulltext Provided)",
    "Processed Fulltext Opened (OA)": "OA",
    "Processed Fulltext Registered (Embargo)": "Embargo OA",
    "Processed (Not OA) Metadata Opened (Fulltext Not Opened)": "Not OA",
    "Processed (Not OA) Metadata Opened (Fulltext Opened Limitedly)": "Opened Limitedly",
    "Unregistrable No Contact Information/Undeliverable": "Unlinked",
    "Unregistrable No Reply": "Unlinked",
    "Unregistrable No Permission": "Unlinked",
    "Unregistrable No Fulltext": "Unlinked",
    "Unregistrable Other Reasons": "Unlinked",
    "Excluded Already Opened Elsewhere": "Opened Elsewhere",
    "Excluded Not Funded by Designated FA": "Unlinked",
    "Excluded Not Affiliated First Author": "Unlinked",
    "Excluded Overlapped Content": "Unlinked",
    "Excluded Other Reasons": "Unlinked"
}
"""Mapping of OA status to the OA status in WEKO."""


WEKO_WORKSPACE_AUTOFILL_JAMAS_XML_DATA_KEYS = [
    "dc:title",
    "dc:creator",
    "prism:organization",
    "prism:publicationName",
    "prism:volume",
    "prism:number",
    "prism:startingPage",
    "prism:pageRange",
    "prism:publicationDate",
    "prism:issn",
    "prism:eIssn",
    "prism:doi",
]
"""Jamas XML data keys"""

WEKO_WORKSPACE_AUTOFILL_JAMAS_REQUIRED_ITEM = [
    "title",
    "creator",
    "sourceTitle",
    "sourceIdentifier",
    "volume",
    "issue",
    "pageStart",
    "date",
    "relation"
]
"""Jamas required item"""

WEKO_WORKSPACE_ITEM_SEARCH_INDEX = "{}-weko".format(index_prefix)
"""Search index for WEKO workspace item."""
WEKO_WORKSPACE_ITEM_SEARCH_TYPE = "item-v1.0.0"
"""Search type for WEKO workspace item."""


WEKO_WORKFLOW_BASE_TEMPLATE = 'weko_workflow/base.html'
"""Default base template for the demo page."""

WEKO_WORKFLOW_POP_PAGE = 'weko_workflow/admin/pop_page.html'
"""Default pop page template for the flow detail page."""

WEKO_WORKFLOW_OAPOLICY_SEARCH = 'oa_policy_{keyword}'
"""OA Policy cache."""

WEKO_WORKFLOW_OAPOLICY_CACHE_TTL = 24 * 60 * 60
""" cache default timeout 1 day"""

WEKO_WORKFLOW_MAX_ACTIVITY_ID = 99999
""" max activity id per day"""

WEKO_WORKFLOW_ACTIVITY_ID_FORMAT = 'A-{}-{}'
"""Activity Id's format (A-YYYYMMDD-NNNNN with NNNNN starts from 00001)."""

WEKO_WORKFLOW_ACTION_ENDPOINTS = {
    'item_login': {
        'endpoint': 'weko_items_ui.index',
        'params': {}
    }
}

IDENTIFIER_GRANT_LIST = [(0, 'Not Grant', ''),
                         (1, 'JaLC DOI', 'https://doi.org'),
                         (2, 'JaLC CrossRef DOI', 'https://doi.org'),
                         (3, 'JaLC DataCite DOI', 'https://doi.org'),
                         (4, 'NDL JaLC DOI', 'https://doi.org')
                         ]
"""Options list for Identifier Grant action."""

IDENTIFIER_GRANT_SUFFIX_METHOD = 0
"""
    Suffix input method for Identifier Grant action

    :case 0: Automatic serial number
    :case 1: Semi-automatic input
    :case 2: Free input
"""

WEKO_WORKFLOW_IDENTIFIER_GRANT_CAN_WITHDRAW = -1
"""Identifier grant can withdraw."""

WEKO_WORKFLOW_IDENTIFIER_GRANT_IS_WITHDRAWING = -2
"""Identifier grant is withdrawing."""

WEKO_WORKFLOW_ITEM_REGISTRATION_ACTION_ID = 3
"""Item Registration action id default."""

"""Identifier grant is withdrawing."""

IDENTIFIER_GRANT_SELECT_DICT = {
    'NotGrant': '0',
    'JaLC': '1',
    'Crossref': '2',
    'DataCite': '3',
    'NDL JaLC': '4'
}
"""Identifier grant selected enum."""

DOI_VALIDATION_INFO = {
    'jpcoar:URI': [
        ['file.URI.@value', None]
    ],
    'dc:title': [
        ['title.@value', None],
        # ['title.@attributes.xml:lang', None]
    ],
    'datacite:date': [
        ['date.@value', None],
         ['date.@attributes.dateType', None]
    ],
    'dc:type': [
        ['type.@attributes.rdf:resource', None],
        ['type.@value', None],
    ],
    'jpcoar:pageStart': [
        ['pageStart.@value', None],
    ],
    'dcndl:dateGranted': [
        ['dateGranted.@value', None],
    ],
    'jpcoar:degreeGrantor': [
        ['degreeGrantor.nameIdentifier.@attributes.nameIdentifierScheme', None],
        ['degreeGrantor.nameIdentifier.@value', None],
        ['degreeGrantor.degreeGrantorName.@attributes.xml:lang', None],
        ['degreeGrantor.degreeGrantorName.@value', None],
    ],
    'jpcoar:givenName': [
        ['creator.givenName.@value', None],
        # ['creator.givenName.@attributes.xml:lang', None]
    ],
    'jpcoar:creatorName': [
        ['creator.creatorName.@value', None],
        # ['creator.creatorName.@attributes.xml:lang', None]
    ],
    'jpcoar:sourceIdentifier': [
        ['sourceIdentifier.@value', None],
        ['sourceIdentifier.@attributes.identifierType', None]
    ],
    'jpcoar:sourceTitle': [
        ['sourceTitle.@value', None],
        ['sourceTitle.@attributes.xml:lang', None]
    ],
    'dc:publisher': [
        ['publisher.@value', None],
        # ['publisher.@attributes.xml:lang', None]
    ],
    'jpcoar:publisher_jpcoar': [
        ['publisher_jpcoar.publisherName.@value', None],
        # ['publisher_jpcoar.publisherName.@attributes.xml:lang', None],
    ],
    'datacite:geoLocationPoint': [
        ['geoLocation.geoLocationPoint.pointLatitude.@value', None],
        ['geoLocation.geoLocationPoint.pointLongitude.@value', None]
    ],
    'datacite:geoLocationBox': [
        ['geoLocation.geoLocationBox.eastBoundLongitude.@value', None],
        ['geoLocation.geoLocationBox.northBoundLatitude.@value', None],
        ['geoLocation.geoLocationBox.southBoundLatitude.@value', None],
        ['geoLocation.geoLocationBox.westBoundLongitude.@value', None]
    ],
    'datacite:geoLocationPlace': [
        ['geoLocation.geoLocationPlace.@value', None]
    ],
    'jpcoar:mimeType': [
        ['file.mimeType.@value', None]
    ],
    'datacite:version': [
        ['version.@value', None]
    ],
    'oaire:version': [
        ['versiontype.@value', None],
        ['versiontype.@attributes.rdf:resource', None]
    ]
}
DOI_VALIDATION_INFO_CROSSREF = {
    'jpcoar:URI': [
        ['file.URI.@value', None]
    ],
    'dc:title': [
        ['title.@value', None],
        ['title.@attributes.xml:lang', None]
    ],
    'datacite:date': [
        # ['date.@attributes.dateType', None],
        ['date.@value', None]
    ],
    'dc:type': [
        ['type.@attributes.rdf:resource', None],
        ['type.@value', None],
    ],
    'jpcoar:pageStart': [
        ['pageStart.@value', None],
    ],
    'dcndl:dateGranted': [
        ['dateGranted.@value', None],
    ],
    'jpcoar:givenName': [
        ['creator.givenName.@value', None],
        ['creator.givenName.@attributes.xml:lang', None]
    ],
    'jpcoar:creatorName': [
        ['creator.creatorName.@value', None],
        ['creator.creatorName.@attributes.xml:lang', None]
    ],
    'jpcoar:sourceIdentifier': [
        ['sourceIdentifier.@value', None],
        ['sourceIdentifier.@attributes.identifierType', None]
    ],
    'jpcoar:sourceTitle': [
        ['sourceTitle.@value', None],
        ['sourceTitle.@attributes.xml:lang', 'en']
    ],
    'dc:publisher': [
        ['publisher.@value', None],
        ['publisher.@attributes.xml:lang', 'en']
    ],
    'jpcoar:publisher_jpcoar': [
        ['publisher_jpcoar.publisherName.@value', None],
        ['publisher_jpcoar.publisherName.@attributes.xml:lang', 'en'],
    ],
}
DOI_VALIDATION_INFO_DATACITE = {
    'jpcoar:URI': [
        ['file.URI.@value', None]
    ],
    'dc:title': [
        ['title.@value', None],
        ['title.@attributes.xml:lang', None]
    ],
    'datacite:date': [
        ['date.@attributes.dateType', None],
        ['date.@value', None]
    ],
    'dc:type': [
        ['type.@attributes.rdf:resource', None],
        ['type.@value', None],
    ],
    'dcndl:dateGranted': [
        ['dateGranted.@value', None],
    ],
    'jpcoar:givenName': [
        ['creator.givenName.@value', None],
        ['creator.givenName.@attributes.xml:lang', 'en']
    ],
    'jpcoar:creatorName': [
        ['creator.creatorName.@value', None],
        ['creator.creatorName.@attributes.xml:lang', 'en']
    ],
    'dc:publisher': [
        ['publisher.@value', None],
        ['publisher.@attributes.xml:lang', 'en']
    ],
    'jpcoar:publisher_jpcoar': [
        ['publisher_jpcoar.publisherName.@value', None],
        ['publisher_jpcoar.publisherName.@attributes.xml:lang', 'en'],
    ],
}
"""List of DOI validation information."""

DOI_VALIDATION_INFO_JALC = {
    'jpcoar:URI': [['file.URI.@value', None]],
    'dc:title': [['title.@value', None]],
    'jpcoar:givenName': [['creator.givenName.@value', None]],
    'jpcoar:sourceIdentifier': [
        ['sourceIdentifier.@value', None],
        ['sourceIdentifier.@attributes.identifierType', None]],
    'jpcoar:sourceTitle': [
        ['sourceTitle.@value', None],
        ['sourceTitle.@attributes.xml:lang', 'en']],
    'dc:publisher': [
        ['publisher.@value', None],
        ['publisher.@attributes.xml:lang', 'en']],
    'datacite:geoLocationPoint': [
        ['geoLocation.geoLocationPoint.pointLatitude.@value', None],
        ['geoLocation.geoLocationPoint.pointLongitude.@value', None]],
    'datacite:geoLocationBox': [
        ['geoLocation.geoLocationBox.eastBoundLongitude.@value', None],
        ['geoLocation.geoLocationBox.northBoundLatitude.@value', None],
        ['geoLocation.geoLocationBox.southBoundLatitude.@value', None],
        ['geoLocation.geoLocationBox.westBoundLongitude.@value', None]],
    'datacite:geoLocationPlace': [['geoLocation.geoLocationPlace.@value', None]],
    'jpcoar:mimeType': [['file.mimeType.@value', None]],
    'datacite:version': [['version.@value', None]],
    'oaire:version': [['versiontype.@value', None],
                      ['versiontype.@attributes.rdf:resource', None]]
}
WEKO_SERVER_CNRI_HOST_LINK = 'http://hdl.handle.net/'
"""Host server of CNRI"""

WEKO_WORKFLOW_SHOW_HARVESTING_ITEMS = True
"""Toggle display harvesting items in Workflow list."""

WEKO_WORKFLOW_ACTION_START = 'Start'
"""Start Action"""

WEKO_WORKFLOW_ACTION_END = 'End'
"""End Action"""

WEKO_WORKFLOW_ACTION_ITEM_REGISTRATION = 'Item Registration'
"""Item Registration Action"""

WEKO_WORKFLOW_ACTION_APPROVAL = 'Approval'
"""Approval Action"""

WEKO_WORKFLOW_ACTION_ITEM_LINK = 'Item Link'
"""Item Link Action"""

WEKO_WORKFLOW_ACTION_OA_POLICY_CONFIRMATION = 'OA Policy Confirmation'
"""OA Policy Confirmation Action"""

WEKO_WORKFLOW_ACTION_IDENTIFIER_GRANT = 'Identifier Grant'
"""Identifier Grant Action"""

WEKO_WORKFLOW_ACTION_ITEM_REGISTRATION_USAGE_APPLICATION = ''
"""Action Item Registration for Usage Application"""

WEKO_WORKFLOW_ACTION_ADMINISTRATOR = ''
"""Action Approval by Administrator"""

WEKO_WORKFLOW_ACTION_GUARANTOR = ''
"""Action Approval by Guarantor"""

WEKO_WORKFLOW_ACTION_ADVISOR = ''
"""Action Approval by Advisor"""

WEKO_WORKFLOW_ACTIONS = [
    WEKO_WORKFLOW_ACTION_START,
    WEKO_WORKFLOW_ACTION_END,
    WEKO_WORKFLOW_ACTION_ITEM_REGISTRATION,
    WEKO_WORKFLOW_ACTION_APPROVAL,
    WEKO_WORKFLOW_ACTION_ITEM_LINK,
    WEKO_WORKFLOW_ACTION_IDENTIFIER_GRANT
]
"""Action list"""

WEKO_WORKFLOW_COLUMNS = [
    'updated',
    'activity_id',
    'title',
    'flows_name',
    'action_name',
    'StatusDesc',
    'email'
]
"""Work flow activity columns"""

WEKO_WORKFLOW_FILTER_COLUMNS = [
    'workflow',
    'user',
    'item',
    'status'
]
"""Work flow filters"""

WEKO_WORKFLOW_VALIDATION_ENABLE = False
"""Enable validation on Flow List screen"""

WEKO_WORKFLOW_ENABLE_AUTO_SEND_EMAIL = True

WEKO_WORKFLOW_ENABLE_AUTO_SET_INDEX_FOR_ITEM_TYPE = False
"""Enable showing index selection for item type"""

WEKO_WORKFLOW_ENABLE_SHOWING_TERM_OF_USE = False
"""Enable showing term of use"""

WEKO_WORKFLOW_ENABLE_FEEDBACK_MAIL = True
"""Enable showing function feed back mail"""

WEKO_WORKFLOW_ENABLE_CONTRIBUTOR = True
"""Enable Contributor"""

WEKO_WORKFLOW_TERM_AND_CONDITION_FILE_LANGUAGES = []
"""Term and condition file language list"""

WEKO_WORKFLOW_TERM_AND_CONDITION_FILE_LOCATION = ""
"""Term and condition file location"""

WEKO_WORKFLOW_TERM_AND_CONDITION_FILE_EXTENSION = ''
"""Term and condition file extension"""

WEKO_WORKFLOW_ENABLE_SHOW_ACTIVITY = False
""" Show activity to tabs: Todo, Wait, All """

WEKO_WORKFLOW_CONTINUE_APPROVAL = False

WEKO_WORKFLOW_ENGLISH_MAIL_TEMPLATE_FOLDER_PATH = ''
WEKO_WORKFLOW_JAPANESE_MAIL_TEMPLATE_FOLDER_PATH = ''
WEKO_WORKFLOW_MAIL_TEMPLATE_FOLDER_PATH = ''
"""Email template path"""

WEKO_WORKFLOW_RECEIVE_USAGE_APP_BESIDE_PERFECTURE_AND_LOCATION_DATA_OF_GENERAL_USER = ''
"""Receiving Usage Application <Other than Perfecture Data & Location Data: General user> mail template"""
WEKO_WORKFLOW_RECEIVE_USAGE_APP_BESIDE_PERFECTURE_AND_LOCATION_DATA_OF_STUDENT_OR_GRADUATED_STUDENT = ''
"""Receiving Usage Application <Other than Perfecture Data & Location Data: Graduated Student OR Student> mail template"""

WEKO_WORKFLOW_PERFECTURE_OR_LOCATION_DATA_OF_GENERAL_USER = ''
"""Receiving Usage Application <Other than Perfecture Data & Location Data: Graduated Student OR Student> mail template"""
WEKO_WORKFLOW_PERFECTURE_OR_LOCATION_DATA_OF_STUDENT_OR_GRADUATED_STUDENT = ''
"""Receiving Usage Application <Perfecture Data & Location Data: General user> mail template"""

WEKO_WORKFLOW_REQUEST_APPROVAL_TO_ADVISOR_OF_USAGE_APP = ''
"""Request Approval to the Advisor of Usage Application mail template"""
WEKO_WORKFLOW_REQUEST_APPROVAL_TO_GUARANTOR_OF_USAGE_APP = ''
"""Request Approval to the Guarantor of Usage Application mail template"""

WEKO_WORKFLOW_APPROVE_USAGE_APP_BESIDE_LOCATION_DATA = ''
"""Approve Usage Application <Other than Location> mail template"""
WEKO_WORKFLOW_APPROVE_LOCATION_DATA = ''
"""Approve Usage Application  <Location data> mail template"""

WEKO_WORKFLOW_REMIND_SUBMIT_DATA_USAGE_REPORT_FOR_USER_BESIDE_STUDENT = ''
"""Remind to submit the Data Usage Report <Other than Student> mail template"""
WEKO_WORKFLOW_REMIND_SUBMIT_DATA_USAGE_REPORT_FOR_STUDENT = ''
"""Remind to submit the Data Usage Report <Student> mail template"""

WEKO_WORKFLOW_USAGE_REPORT_WORKFLOW_NAME = ''

WEKO_WORKFLOW_PER_PAGE = 1
"""Number of activity per page"""

WEKO_WORKFOW_PAGINATION_VISIBLE_PAGES = 1
"""Number of pagination visible pages"""

WEKO_WORKFLOW_SELECT_DICT = []
"""Id and name of mail pattern for reminder mail"""

WEKO_WORKFLOW_ACTION = ""
"""Action status of activities were specialized to send reminder mail"""

WEKO_WORKFLOW_RECEIVE_USAGE_REPORT = ""
"""Receiving Usaage Report mail template's filename"""

WEKO_WORKFLOW_RECEIVE_OUTPUT_REGISTRATION = ""
"""Receiving Output Registration mail template's filename"""

WEKO_WORKFLOW_APPROVE_USAGE_REPORT = ""
"""Approve Usaage Report mail template's filename"""

WEKO_WORKFLOW_APPROVE_OUTPUT_REGISTRATION = ""
"""Approve Output Registration mail template's filename"""

WEKO_WORKFLOW_ACCESS_ACTIVITY_URL = ""
"""Template access the URL"""

WEKO_WORKFLOW_USAGE_REPORT_ACTIVITY_URL = ""
"""Template access the URL"""

WEKO_WORKFLOW_DATE_FORMAT = "%Y-%m-%d"
"""Date format string."""

WEKO_WORKFLOW_TODO_TAB = 'todo'

WEKO_WORKFLOW_WAIT_TAB = 'wait'

WEKO_WORKFLOW_ALL_TAB = 'all'

WEKO_WORKFLOW_IDENTIFIER_GRANT_DOI = 0
"""Identifier grant was select."""

WEKO_WORKFLOW_IDENTIFIER_GRANT_WITHDRAWN = -3
"""Identifier grant was withdrawn."""

WEKO_WORKFLOW_SEND_MAIL_USER_GROUP = {}

WEKO_WORKFLOW_FILTER_PARAMS = [
    'createdfrom', 'createdto', 'workflow', 'user', 'item', 'status', 'tab',
    'sizewait', 'sizetodo', 'sizeall', 'pagesall', 'pagestodo', 'pageswait'
]

WEKO_WORKFLOW_ACTIVITY_TOKEN_PATTERN = "activity={} file_name={} date={} email={}"
"""Token pattern."""

WEKO_WORKFLOW_APPROVE_DONE = 'email_pattern_approval_done.tpl'
"""Mail template for Done Approval"""

WEKO_WORKFLOW_APPROVE_REJECTED = 'email_pattern_approval_rejected.tpl'
"""Mail template for Rejected Approval"""

WEKO_WORKFLOW_REQUEST_APPROVAL = 'email_pattern_request_approval.tpl'
"""Mail template for Requested Approval"""

WEKO_WORKFLOW_REQUEST_FOR_REGISTER_USAGE_REPORT = 'email_pattern_request_for_register_usage_report.tpl'
"""Mail template for Request for register Data Usage Report"""

WEKO_WORKFLOW_USAGE_APPLICATION_ITEM_TYPES_LIST = [31001, 31002]

WEKO_WORKFLOW_USAGE_REPORT_ITEM_TYPES_LIST = [31003]

WEKO_WORKFLOW_USAGE_APPLICATION_ITEM_TITLE = '利用申請'

WEKO_WORKFLOW_USAGE_REPORT_ITEM_TITLE = '利用報告'

WEKO_WORKFLOW_RESTRICTED_ACCESS_APPROVAL_DATE = 'subitem_restricted_access_approval_date'

WEKO_WORKFLOW_RESTRICTED_ACCESS_USAGE_REPORT_ID = 'subitem_restricted_access_usage_report_id'

WEKO_WORKFLOW_GAKUNINRDM_DATA = [
    {
        'workflow_id': -1,
        'workflow_name': 'GRDM_デフォルトワークフロー',
        'item_type_id': 15,
        'flow_id': -1,
        'flow_name': 'GRDM_デフォルトフロー',
        'action_endpoint_list': [
            'begin_action',
            'item_login',
            'item_link',
            'identifier_grant',
            'approval',
            'end_action'
        ]
    }
]
"""GakuninRDM information to create flow and workflow"""

WEKO_WORKFLOW_GAKUNINRDM_PREFIX = 'GakuninRDM'
"""GekuninRDM prefix for logging."""

WEKO_WORKFLOW_ACTIVITYLOG_ROLE_ENABLE = ["System Administrator","Repository Administrator"]
""" Roles that can output activitylog"""

WEKO_WORKFLOW_ACTIVITYLOG_BULK_MAX = 100000
""" Maximum activitylog output at one time"""

WEKO_WORKFLOW_ACTIVITYLOG_XLS_COLUMNS = [
    'activity_start',
    'workflow_id',
    'approval2',
    'status',
    'activity_end',
    'workflow_status',
    'extra_info',
    'activity_community_id',
    'created',
    'flow_id',
    'action_order',
    'updated',
    'activity_confirm_term_of_use',
    'action_id',
    'id',
    'title',
    'action_status',
    'activity_id',
    'shared_user_id',
    'activity_login_user',
    'activity_name',
    'temp_data',
    'activity_update_user',
    'item_id',
    'approval1',
    'activity_status',
    'StatusDesc',
    'email',
    'flows_name',
    'action_name',
    'role_name'
]

WEKO_WORKSPACE_SYS_HTTP_PROXY = ''
"""HTTP proxy"""

WEKO_WORKSPACE_SYS_HTTPS_PROXY = ''
"""HTTPS proxy"""

WEKO_WORKSPACE_REQUEST_TIMEOUT = 5
"""Request time out"""

WEKO_WORKSPACE_JAMAS_API_URL = 'https://search.jamas.or.jp/'
"""Jamas API URL"""

WEKO_WORKSPACE_CiNii_API_URL = 'https://cir.nii.ac.jp/opensearch/all'
"""CiNii API URL"""

WEKO_WORKSPACE_JALC_API_URL = 'https://api.japanlinkcenter.org/dois/'
"""JALC API URL"""

WEKO_WORKSPACE_DATACITE_API_URL = 'https://api.datacite.org/dois/'
"""DataCite API URL"""

WEKO_ITEMS_AUTOFILL_CINII_REQUIRED_ITEM = [
    "title",
    "alternative",
    "creator",
    "contributor",
    "description",
    "subject",
    "sourceTitle",
    "volume",
    "issue",
    "pageStart",
    "pageEnd",
    "numPages",
    "date",
    "publisher",
    "sourceIdentifier",
    "relation"
]

WEKO_RECORDS_UI_LICENSE_DICT = [
    {
        'name': _('write your own license'),
        'value': 'license_free',
    },
    # version 0
    {
        'name': _(
            'Creative Commons CC0 1.0 Universal Public Domain Designation'),
        'code': 'CC0',
        'href_ja': 'https://creativecommons.org/publicdomain/zero/1.0/deed.ja',
        'href_default': 'https://creativecommons.org/publicdomain/zero/1.0/',
        'value': 'license_12',
        'src': '88x31(0).png',
        'src_pdf': 'cc-0.png',
        'href_pdf': 'https://creativecommons.org/publicdomain/zero/1.0/'
                    'deed.ja',
        'txt': 'This work is licensed under a Public Domain Dedication '
               'International License.'
    },
    # version 3.0
    {
        'name': _('Creative Commons Attribution 3.0 Unported (CC BY 3.0)'),
        'code': 'CC BY 3.0',
        'href_ja': 'https://creativecommons.org/licenses/by/3.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by/3.0/',
        'value': 'license_6',
        'src': '88x31(1).png',
        'src_pdf': 'by.png',
        'href_pdf': 'http://creativecommons.org/licenses/by/3.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               ' 3.0 International License.'
    },
    {
        'name': _(
            'Creative Commons Attribution-ShareAlike 3.0 Unported '
            '(CC BY-SA 3.0)'),
        'code': 'CC BY-SA 3.0',
        'href_ja': 'https://creativecommons.org/licenses/by-sa/3.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-sa/3.0/',
        'value': 'license_7',
        'src': '88x31(2).png',
        'src_pdf': 'by-sa.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-sa/3.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-ShareAlike 3.0 International License.'
    },
    {
        'name': _(
            'Creative Commons Attribution-NoDerivs 3.0 Unported (CC BY-ND 3.0)'),
        'code': 'CC BY-ND 3.0',
        'href_ja': 'https://creativecommons.org/licenses/by-nd/3.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-nd/3.0/',
        'value': 'license_8',
        'src': '88x31(3).png',
        'src_pdf': 'by-nd.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-nd/3.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-NoDerivatives 3.0 International License.'

    },
    {
        'name': _(
            'Creative Commons Attribution-NonCommercial 3.0 Unported'
            ' (CC BY-NC 3.0)'),
        'code': 'CC BY-NC 3.0',
        'href_ja': 'https://creativecommons.org/licenses/by-nc/3.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-nc/3.0/',
        'value': 'license_9',
        'src': '88x31(4).png',
        'src_pdf': 'by-nc.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-nc/3.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-NonCommercial 3.0 International License.'
    },
    {
        'name': _(
            'Creative Commons Attribution-NonCommercial-ShareAlike 3.0 '
            'Unported (CC BY-NC-SA 3.0)'),
        'code': 'CC BY-NC-SA 3.0',
        'href_ja': 'https://creativecommons.org/licenses/by-nc-sa/3.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-nc-sa/3.0/',
        'value': 'license_10',
        'src': '88x31(5).png',
        'src_pdf': 'by-nc-sa.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-nc-sa/3.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-NonCommercial-ShareAlike 3.0 International License.'
    },
    {
        'name': _(
            'Creative Commons Attribution-NonCommercial-NoDerivs '
            '3.0 Unported (CC BY-NC-ND 3.0)'),
        'code': 'CC BY-NC-ND 3.0',
        'href_ja': 'https://creativecommons.org/licenses/by-nc-nd/3.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-nc-nd/3.0/',
        'value': 'license_11',
        'src': '88x31(6).png',
        'src_pdf': 'by-nc-nd.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-nc-nd/3.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-NonCommercial-ShareAlike 3.0 International License.'
    },
    # version 4.0
    {
        'name': _('Creative Commons Attribution 4.0 International (CC BY 4.0)'),
        'code': 'CC BY 4.0',
        'href_ja': 'https://creativecommons.org/licenses/by/4.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by/4.0/',
        'value': 'license_0',
        'src': '88x31(1).png',
        'src_pdf': 'by.png',
        'href_pdf': 'http://creativecommons.org/licenses/by/4.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               ' 4.0 International License.'
    },
    {
        'name': _(
            'Creative Commons Attribution-ShareAlike 4.0 International '
            '(CC BY-SA 4.0)'),
        'code': 'CC BY-SA 4.0',
        'href_ja': 'https://creativecommons.org/licenses/by-sa/4.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-sa/4.0/',
        'value': 'license_1',
        'src': '88x31(2).png',
        'src_pdf': 'by-sa.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-sa/4.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-ShareAlike 4.0 International License.'
    },
    {
        'name': _(
            'Creative Commons Attribution-NoDerivatives 4.0 International '
            '(CC BY-ND 4.0)'),
        'code': 'CC BY-ND 4.0',
        'href_ja': 'https://creativecommons.org/licenses/by-nd/4.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-nd/4.0/',
        'value': 'license_2',
        'src': '88x31(3).png',
        'src_pdf': 'by-nd.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-nd/4.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-NoDerivatives 4.0 International License.'
    },
    {
        'name': _(
            'Creative Commons Attribution-NonCommercial 4.0 International'
            ' (CC BY-NC 4.0)'),
        'code': 'CC BY-NC 4.0',
        'href_ja': 'https://creativecommons.org/licenses/by-nc/4.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-nc/4.0/',
        'value': 'license_3',
        'src': '88x31(4).png',
        'src_pdf': 'by-nc.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-nc/4.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-NonCommercial 4.0 International License.'
    },
    {
        'name': _(
            'Creative Commons Attribution-NonCommercial-ShareAlike 4.0'
            ' International (CC BY-NC-SA 4.0)'),
        'code': 'CC BY-NC-SA 4.0',
        'href_ja': 'https://creativecommons.org/licenses/by-nc-sa/4.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-nc-sa/4.0/',
        'value': 'license_4',
        'src': '88x31(5).png',
        'src_pdf': 'by-nc-sa.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-nc-sa/4.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-NonCommercial-ShareAlike 4.0 International License.'
    },
    {
        'name': _(
            'Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 '
            'International (CC BY-NC-ND 4.0)'),
        'code': 'CC BY-NC-ND 4.0',
        'href_ja': 'https://creativecommons.org/licenses/by-nc-nd/4.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-nc-nd/4.0/',
        'value': 'license_5',
        'src': '88x31(6).png',
        'src_pdf': 'by-nc-nd.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-nc-nd/4.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-NonCommercial-ShareAlike 4.0 International License.'
    },
]
"""Define of list license will be used."""

WEKO_THEME_DEFAULT_COMMUNITY = 'Root Index'
"""Default community identifier."""

DEPOSIT_UI_JSTEMPLATE_FORM = \
    'templates/invenio_deposit/form.html'
"""Template for <invenio-records-form> defined by `invenio-records-js`."""

# Error message variable definition

# Others

