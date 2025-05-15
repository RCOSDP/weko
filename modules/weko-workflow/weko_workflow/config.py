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

"""Configuration for weko-workflow."""

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
WEKO_WORKFLOW_MAIL_TEMPLATE_FOLDER_PATH = 'modules/weko-workflow/weko_workflow/templates/weko_workflow/email_templates/'
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

WEKO_WORKFLOW_REQUEST_FOR_REGISTER_USAGE_REPORT = '7'
"""Mail template for Request for register Data Usage Report"""

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

WEKO_WORKFLOW_USAGE_APPLICATION_ITEM_TYPES_LIST = [31001, 31002, 31004, 31005, 31006, 31007, 31008]

WEKO_WORKFLOW_USAGE_REPORT_ITEM_TYPES_LIST = [3007, 31003]

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
    'shared_user_ids',
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
WEKO_ITEMS_UI_MULTIPLE_APPROVALS = True

WEKO_STR_TRUE = ['true', 't', 'yes', '1']

WEKO_WORKFLOW_REST_ENDPOINTS = dict(
    activities=dict(
        activities_route='/<string:version>/workflow/activities',
        default_media_type='application/json',
    ),
    approve=dict(
        route='/<string:version>/workflow/activities/<string:activity_id>/approve',
        default_media_type='application/json',
    ),
    throw_out=dict(
        route='/<string:version>/workflow/activities/<string:activity_id>/throw-out',
        default_media_type='application/json',
    ),
    file_application=dict(
        route='/<string:version>/workflow/activities/<string:activity_id>/application',
        default_media_type='application/json',
    ),
)

WEKO_WORKFLOW_API_LIMIT_RATE_DEFAULT = ['100 per minute']

WEKO_WORKFLOW_API_ACCEPT_LANGUAGES = ['en', 'ja']

WEKO_WORKFLOW_ITEM_REGISTRANT_ID = -2
"""Item registrant id."""

WEKO_WORKFLOW_APPROVAL_PREVIEW = True
"""Setting preview function during approval"""
