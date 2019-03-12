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

"""Configuration for weko-index-tree."""

WEKO_INDEX_TREE_BASE_TEMPLATE = 'weko_index_tree/base.html'
"""Default base template for the index tree page."""

WEKO_INDEX_TREE_INDEX_TEMPLATE = 'weko_index_tree/index.html'
"""Index template for the index tree page."""

WEKO_INDEX_TREE_EDIT_TEMPLATE = 'weko_index_tree/tree_edit.html'
"""Index template for the index tree page."""

WEKO_INDEX_TREE_ADMIN_TEMPLATE = 'weko_index_tree/setting/index_setting.html'
"""Index area setting page."""

WEKO_INDEX_TREE_LINK_ADMIN_TEMPLATE = 'weko_index_tree/setting/index_link_setting.html'
"""Index link setting page."""

WEKO_INDEX_TREE_STYLE_OPTIONS = {
    'id': 'weko',
    'widths': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11']
}

WEKO_INDEX_TREE_DEFAULT_DISPLAY_NUMBER = 5
"""Default display number of the index."""

WEKO_INDEX_TREE_API = "/api/tree/index/"

WEKO_INDEX_TREE_LIST_API = "/api/tree"

_IID = 'iid(tid,record_class="weko_index_tree.api:Indexes")'

WEKO_INDEX_TREE_REST_ENDPOINTS = dict(
    tid=dict(
        record_class='weko_index_tree.api:Indexes',
        index_route='/tree/index/<int:index_id>',
        tree_route='/tree',
        item_tree_route='/tree/<int:pid_value>',
        index_move_route='/tree/move/<int:index_id>',
        default_media_type='application/json',
        create_permission_factory_imp=
        'weko_index_tree.permissions:index_tree_permission',
        read_permission_factory_imp=
        'weko_index_tree.permissions:index_tree_permission',
        update_permission_factory_imp=
        'weko_index_tree.permissions:index_tree_permission',
        delete_permission_factory_imp=
        'weko_index_tree.permissions:index_tree_permission',
    )
)

WEKO_INDEX_TREE_UPDATED = True
"""For index tree cache."""
