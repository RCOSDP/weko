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

WEKO_ITEMS_UI_BASE_TEMPLATE = 'weko_items_ui/base.html'
"""Default base template for the item page."""

WEKO_ITEMS_UI_INDEX_TEMPLATE = 'weko_items_ui/item_index.html'
"""Edit template with file upload for the item page."""

WEKO_ITEMS_UI_FORM_TEMPLATE = 'weko_items_ui/edit.html'
"""Edit template with file upload for the item page."""

WEKO_ITEMS_UI_ERROR_TEMPLATE = 'weko_items_ui/error.html'
"""Error template for the item page."""

WEKO_ITEMS_UI_UPLOAD_TEMPLATE = 'weko_items_ui/upload.html'
"""Demo template for the item page post test data."""

WEKO_ITEMS_UI_INDEX_URL = '/items/index/{pid_value}'
