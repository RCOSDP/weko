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

"""Weko Search-UI admin."""

import json
import os
import sys
from datetime import datetime
from xml.etree import ElementTree as ET

from blinker import Namespace
from flask import abort, current_app, jsonify, make_response, redirect, \
    render_template, request, url_for
from flask_admin import BaseView, expose
from flask_babelex import gettext as _
from flask_security import current_user
from invenio_db import db
from invenio_i18n.ext import current_i18n
from weko_index_tree.api import Indexes
from weko_index_tree.models import Index, IndexStyle
from weko_records_ui.ipaddr import check_site_license_permission

from weko_search_ui.api import get_search_detail_keyword

from .api import SearchSetting
from .query import item_path_search_factory
from .utils import delete_records, get_journal_info, get_tree_items, \
    import_items

_signals = Namespace()
searched = _signals.signal('searched')


class ItemManagementBulkDelete(BaseView):
    """Item Management - Bulk Delete view."""

    @expose('/', methods=['GET', 'PUT'])
    def index(self):
        """Bulk delete items and index trees."""
        if request.method == 'PUT':
            # Do delete items inside the current index tree (maybe root tree)
            q = request.values.get('q')
            if q is not None and q.isdigit():
                current_tree = Indexes.get_index(q)
                recursive_tree = Indexes.get_recursive_tree(q)

                if current_tree is not None:

                    # Delete items in current_tree
                    delete_records(current_tree.id)

                    # If recursively, then delete all child index trees and theirs
                    # items
                    if request.values.get(
                            'recursively') == 'true' and recursive_tree is not None:
                        # Delete recursively
                        direct_child_trees = []
                        for index, obj in enumerate(recursive_tree):
                            if obj[1] != current_tree.id:
                                child_tree = Indexes.get_index(obj[1])

                                # Do delete items in child_tree
                                delete_records(child_tree.id)

                                # Add the level 1 child into the current_tree
                                if obj[0] == current_tree.id:
                                    direct_child_trees.append(child_tree.id)
                        # Then do delete child_tree inside current_tree
                        for cid in direct_child_trees:
                            # Delete this tree and children
                            Indexes.delete(cid)

                    return jsonify({'status': 1})
            else:
                return jsonify({'status': 0, 'msg': 'Invalid tree'})

        """Render view."""
        detail_condition = get_search_detail_keyword('')
        return self.render(
            current_app.config['WEKO_THEME_ADMIN_ITEM_MANAGEMENT_TEMPLATE'],
            management_type='delete',
            detail_condition=detail_condition
        )


class ItemManagementCustomSort(BaseView):
    """Item Management - Custom Sort view."""

    @expose('/', methods=['GET'])
    def index(self):
        """Custom sort index."""
        return self.render(
            current_app.config['WEKO_THEME_ADMIN_ITEM_MANAGEMENT_TEMPLATE'],
            management_type='sort',
        )

    @expose('/save', methods=['POST'])
    def save_sort(self):
        """Save custom sort."""
        try:
            data = request.get_json()
            index_id = data.get("q_id")
            sort_data = data.get("sort")

            # save data to DB
            item_sort = {}
            for sort in sort_data:
                sd = sort.get('custom_sort').get(index_id)
                if sd:
                    item_sort[sort.get('id')] = sd

            Indexes.set_item_sort_custom(index_id, item_sort)

            # update es
            # fp = Indexes.get_self_path(index_id)
            # Indexes.update_item_sort_custom_es(fp.path, sort_data)

            jfy = {}
            jfy['status'] = 200
            jfy['message'] = 'Data is successfully updated.'
            return make_response(jsonify(jfy), jfy['status'])
        except Exception as ex:
            jfy['status'] = 405
            jfy['message'] = 'Error'
            return make_response(jsonify(jfy), jfy['status'])


class ItemManagementBulkSearch(BaseView):
    """Item Management - Search."""

    @expose('/', methods=['GET'])
    def index(self):
        """Index Search page ui."""
        search_type = request.args.get('search_type', '0')
        getArgs = request.args
        community_id = ""
        ctx = {'community': None}
        cur_index_id = search_type if search_type not in ('0', '1', ) else None
        if 'community' in getArgs:
            from weko_workflow.api import GetCommunity
            comm = GetCommunity.get_community_by_id(
                request.args.get('community'))
            ctx = {'community': comm}
            community_id = comm.id

        # Get index style
        style = IndexStyle.get(
            current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'])
        width = style.width if style else '3'

        detail_condition = get_search_detail_keyword('')

        height = style.height if style else None

        if 'item_management' in getArgs:
            management_type = request.args.get('item_management', 'sort')

            has_items = False
            has_child_trees = False
            if management_type == 'delete':
                # Does this tree has items or children?
                q = request.args.get('q')
                if q is not None and q.isdigit():
                    current_tree = Indexes.get_index(q)
                    recursive_tree = Indexes.get_recursive_tree(q)

                    if current_tree is not None:
                        tree_items = get_tree_items(current_tree.id)
                        has_items = len(tree_items) > 0
                        if recursive_tree is not None:
                            has_child_trees = len(recursive_tree) > 1

            return self.render(
                current_app.config['WEKO_THEME_ADMIN_ITEM_MANAGEMENT_TEMPLATE'],
                index_id=cur_index_id,
                community_id=community_id,
                width=width,
                height=height,
                management_type=management_type,
                fields=current_app.config['WEKO_RECORDS_UI_BULK_UPDATE_FIELDS']['fields'],
                licences=current_app.config['WEKO_RECORDS_UI_BULK_UPDATE_FIELDS']['licences'],
                has_items=has_items,
                has_child_trees=has_child_trees,
                detail_condition=detail_condition,
                **ctx)
        else:
            return abort(500)

    @staticmethod
    def is_visible():
        """Should never be visible."""
        return False


class ItemImportView(BaseView):
    """ItemImportView."""

    @expose('/', methods=['GET'])
    def index(self):
        """Renders an item import view.

        :param
        :return: The rendered template.
        """
        from .config import WEKO_ITEM_ADMIN_IMPORT_TEMPLATE
        from weko_workflow.api import WorkFlow
        from .utils import get_content_workflow
        import json
        workflow = WorkFlow()
        workflows = workflow.get_workflow_list()
        workflows_js = [get_content_workflow(item) for item in workflows]

        return self.render(
            WEKO_ITEM_ADMIN_IMPORT_TEMPLATE,
            workflows=json.dumps(workflows_js)
        )

    @expose('/check', methods=['POST'])
    def check(self) -> jsonify:
        """Register an item type mapping."""
        data = request.get_json()
        list_record = [],
        data_path = ''
        if data:
            result = import_items(data.get('file').split(",")[-1])
            if isinstance(result, dict):
                if result.get('error'):
                    return jsonify(code=0, error=result.get('error'))
                else:
                    list_record = result.get('list_record', [])
                    data_path = result.get('data_path', '')
        return jsonify(code=1, list_record=list_record, data_path=data_path)

    @expose('/download', methods=['POST'])
    def download(self):
        """Register an item type mapping."""
        data = request.get_json()
        from datetime import datetime
        from .utils import make_stats_tsv
        from flask import Response
        now = str(datetime.date(datetime.now()))
        file_name = "check_"+now+".tsv"
        if data:
            tsv_file = make_stats_tsv(data.get('list_result'))
            return Response(
                tsv_file.getvalue(),
                mimetype="text/tsv",
                headers={
                    "Content-disposition": "attachment; filename="+file_name
                }
            )
        else:
            return Response(
                [],
                mimetype="text/tsv",
                headers={
                    "Content-disposition": "attachment; filename="+file_name
                }
            )

    @expose('/import', methods=['POST'])
    def import_item(self) -> jsonify:
        """Register an item type mapping."""
        from .utils import create_deposit, up_load_file_content,\
            register_item_metadata
        data = request.get_json()

        response_object = {
            "status": "success",
        }
        if data:
            list_record = data.get('list_record')
            list_record = [item for item in list_record if not item.get(
                'errors')]
            ids = [item.get('id', None) for item in list_record]
            current_app.logger.debug(ids)
            create_deposit(ids)
            file_path = data.get('root_path')
            up_load_file_content(list_record, file_path)
            register_item_metadata(list_record)
        return jsonify(response_object)


item_management_bulk_search_adminview = {
    'view_class': ItemManagementBulkSearch,
    'kwargs': {
        'endpoint': 'items/search',
        'category': 'Items',
        'name': ''
    }
}

item_management_bulk_delete_adminview = {
    'view_class': ItemManagementBulkDelete,
    'kwargs': {
        'category': _('Items'),
        'name': _('Bulk Delete'),
        'endpoint': 'items/bulk/delete'
    }
}

item_management_custom_sort_adminview = {
    'view_class': ItemManagementCustomSort,
    'kwargs': {
        'category': _('Items'),
        'name': _('Custom Sort'),
        'endpoint': 'items/custom_sort'
    }
}

item_management_import_adminview = {
    'view_class': ItemImportView,
    'kwargs': {
        'category': _('Items'),
        'name': _('Import'),
        'endpoint': 'items/import'
    }
}

__all__ = (
    'item_management_bulk_delete_adminview',
    'item_management_bulk_search_adminview',
    'item_management_custom_sort_adminview',
    'item_management_import_adminview'
)
