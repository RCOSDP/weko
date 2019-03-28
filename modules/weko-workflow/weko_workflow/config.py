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

WEKO_WORKFLOW_ACTION_ENDPOINTS = {
    'item_login': {
        'endpoint': 'weko_items_ui.index',
        'params': {}
    }
}

IDENTIFIER_GRANT_LIST = [(0, 'Not Grant', '', '', ''),
                         (1, 'JaLC DOI', 'http://doi.org/', '1000/', '1234'),
                         (2, 'JaLC CrossRef DOI', 'http://doi.org/', '2000/', '2345'),
                         (3, 'JaLC DataCite DOI', 'http://doi.org/', '3000/', '4567'),
                         (4, 'CNRI', 'http://hdl.handle.net/4000/56789012', '', '')
                        ]
"""Options list for Identifier Grant action."""

IDENTIFIER_GRANT_SUFFIX_METHOD = 1
"""
    Suffix input method for Identifier Grant action

    :case 0: Automatic serial number
    :case 1: Semi-automatic input
    :case 2: Free input
"""
