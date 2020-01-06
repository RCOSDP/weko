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

WEKO_WORKFLOW_ACTIVITY_ID_FORMAT = 'A-{}-{}'
"""Activity Id's format (A-YYYYMMDD-NNNNN with NNNNN starts from 00001)."""


WEKO_WORKFLOW_ACTION_ENDPOINTS = {
    'item_login': {
        'endpoint': 'weko_items_ui.index',
        'params': {}
    }
}

IDENTIFIER_GRANT_LIST = [(0, 'Not Grant', ''),
                         (1, 'JaLC DOI', 'http://doi.org'),
                         (2, 'JaLC CrossRef DOI', 'http://doi.org'),
                         (3, 'JaLC DataCite DOI', 'http://doi.org')
                         ]
"""Options list for Identifier Grant action."""

IDENTIFIER_GRANT_SUFFIX_METHOD = 0
"""
    Suffix input method for Identifier Grant action

    :case 0: Automatic serial number
    :case 1: Semi-automatic input
    :case 2: Free input
"""

IDENTIFIER_ITEMSMETADATA_KEY = [
    'identifier.@value',
    'identifier.@attributes.identifierType',
    'identifierRegistration.@value',
    'identifierRegistration.@attributes.identifierType'
]
"""ItemsMetadata format for Identifier Grant action."""

IDENTIFIER_GRANT_CAN_WITHDRAW = -1
"""Identifier grant can withdraw."""

IDENTIFIER_GRANT_IS_WITHDRAWING = -2
"""Identifier grant is withdrawing."""

ITEM_REGISTRATION_ACTION_ID = 3
"""Item Registration action id default."""

ITEM_REGISTRATION_FLOW_ID = 3
"""Identifier grant is withdrawing."""

IDENTIFIER_GRANT_SELECT_DICT = {
    'NotGrant': '0',
    'JaLCDOI': '1',
    'CrossRefDOI': '2'
}
"""Identifier grant selected enum."""

WEKO_SERVER_CNRI_HOST_LINK = 'http://hdl.handle.net/'
"""Host server of CNRI"""

WEKO_WORKFLOW_SHOW_HARVESTING_ITEMS = False
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
    WEKO_WORKFLOW_ACTION_OA_POLICY_CONFIRMATION,
    WEKO_WORKFLOW_ACTION_IDENTIFIER_GRANT
]
"""Action list"""

WEKO_WORKFLOW_COLUMNS = [
    'updated',
    'activity_id',
    'ItemName',
    'flows_name',
    'action_name',
    'StatusDesc',
    'email'
]
"""Work flow activity columns"""

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

WEKO_WORKFLOW_REMIND_SUBMIT_DATA_USAGE_REPORT_FOR_USER_BESIDE_GRADUATED_STUDENT = ''
"""Remind to submit the Data Usage Report <Other than Graduated Student> mail template"""
WEKO_WORKFLOW_REMIND_SUBMIT_DATA_USAGE_REPORT_FOR_GRADUATED_STUDENT = ''

WEKO_WORKFLOW_USAGE_REPORT_INDEX_NAME = ''
WEKO_WORKFLOW_USAGE_REPORT_WORKFLOW_NAME = ''

WEKO_WORKFLOW_PER_PAGE = 5
WEKO_WORKFOW_PAGINATION_VISIBLE_PAGES = 3

WEKO_WORKFLOW_SELECT_DICT = []
