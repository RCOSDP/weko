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

WEKO_WORKFLOW_ENABLE_FEEDBACK_MAIL = True
"""Enable showing function feed back mail"""

WEKO_WORKFLOW_ENABLE_CONTRIBUTOR = True
"""Enable Contributor"""

WEKO_WORKFLOW_UI_ENDPOINTS = {
    'index': {
        'route': '/',
        'view_imp': 'weko_workflow.views.index',
    },
    'iframe_success': {
        'route': '/iframe/success',
        'view_imp': 'weko_workflow.views.iframe_success',
        "methods": ['GET'],
    },
    'new_activity': {
        'route': '/activity/new',
        'view_imp': 'weko_workflow.views.new_activity',
        "methods": ['GET'],
    },
    'init_activity': {
        'route': '/activity/init',
        'view_imp': 'weko_workflow.views.init_activity',
        "methods": ['POST'],
    },
    'list_activity': {
        'route': '/activity/list',
        'view_imp': 'weko_workflow.views.list_activity',
        "methods": ['GET'],
    },
    'display_activity': {
        'route': '/activity/detail/<string:activity_id>',
        'view_imp': 'weko_workflow.views.display_activity',
        "methods": ['GET'],
    },
    'next_action': {
        'route': '/activity/action/<string:activity_id>/<int:action_id>',
        'view_imp': 'weko_workflow.views.next_action',
        "methods": ['POST'],
    },
    'previous_action': {
        'route': '/activity/action/<string:activity_id>/<int:action_id>'
                 '/rejectOrReturn/<int:req>',
        'view_imp': 'weko_workflow.views.previous_action',
        "methods": ['POST'],
    },
    'get_journals': {
        'route': '/journal/list',
        'view_imp': 'weko_workflow.views.get_journals',
        "methods": ['GET'],
    },
    'get_journal': {
        'route': '/journal/<string:method>/<string:value>',
        'view_imp': 'weko_workflow.views.get_journal',
        "methods": ['GET'],
    },
    'cancel_action': {
        'route': '/activity/action/<string:activity_id>/<int:action_id>/cancel',
        'view_imp': 'weko_workflow.views.cancel_action',
        "methods": ['POST'],
    },
    'withdraw_confirm': {
        'route': '/activity/detail/<string:activity_id>/<int:action_id>'
                 '/withdraw',
        'view_imp': 'weko_workflow.views.withdraw_confirm',
        "methods": ['POST'],
    },
    'check_existed_doi': {
        'route': '/findDOI',
        'view_imp': 'weko_workflow.views.check_existed_doi',
        "methods": ['POST'],
    },
    'save_feedback_maillist': {
        'route': '/save_feedback_maillist/<string:activity_id>/<int:action_id>',
        'view_imp': 'weko_workflow.views.save_feedback_maillist',
        "methods": ['POST'],
    },
    'get_feedback_maillist': {
        'route': '/get_feedback_maillist/<string:activity_id>',
        'view_imp': 'weko_workflow.views.get_feedback_maillist',
        "methods": ['GET'],
    },
}
"""Basic Weko WorkFlow endpoints configuration."""
