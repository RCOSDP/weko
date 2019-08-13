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

WEKO_ITEMS_UI_EXPORT_RESULTS_LIST_TEMPLATE = 'weko_items_ui/export_results_list.html'
"""Item export results list template."""

WEKO_ITEMS_UI_JSTEMPLATE_EXPORT_LIST = 'templates/weko_items_ui/export_list.html'
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

WEKO_ITEMS_UI_EXPORT_FORMAT_JSON = 'JSON'
"""Format for exporting items -- JSON. """

WEKO_ITEMS_UI_EXPORT_FORMAT_BIBTEX = 'BIBTEX'
"""Format for exporting items -- BIBTEX. """

IDENTIFIER_GRANT_DOI = 0
"""Identifier grant was select."""

IDENTIFIER_GRANT_CAN_WITHDRAW = -1
"""Identifier grant can withdraw."""

IDENTIFIER_GRANT_IS_WITHDRAWING = -2
"""Identifier grant is withdrawing."""

IDENTIFIER_GRANT_WITHDRAWN = -3
"""Identifier grant was withdrawn."""
