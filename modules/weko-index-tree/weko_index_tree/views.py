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

"""Blueprint for weko-index-tree."""

import requests

from flask import Blueprint, current_app, json, jsonify, \
    render_template, request, url_for
from flask_babelex import gettext as _
from flask_login import login_required
from werkzeug.utils import secure_filename
from functools import wraps
from sqlalchemy.exc import SQLAlchemyError
from invenio_records_rest.errors import PIDResolveRESTError

from .api import Indexes, IndexTrees, ItemRecord
from .permissions import index_tree_permission
from .utils import get_all_children, reset_tree

blueprint = Blueprint(
    'weko_index_tree',
    __name__,
    url_prefix='/indextree',
    template_folder='templates',
    static_folder='static',
)


def pass_record(f):
    """Decorator to retrieve persistent identifier and record."""

    @wraps(f)
    def inner(pid_value, *args, **kwargs):
        try:
            pid, record = request.view_args['pid_value'].data
            return f(pid=pid, record=record, *args, **kwargs)
        except SQLAlchemyError:
            raise PIDResolveRESTError(pid)

    return inner


@blueprint.route("/")
@login_required
@index_tree_permission.require(http_exception=403)
def index():
    """Render the index tree edit page."""

    return render_template(
        current_app.config['WEKO_INDEX_TREE_INDEX_TEMPLATE'],
        get_tree_json=url_for('.get_indexjson'),
        upt_tree_json=url_for('.edit'),
        mod_tree_detail=url_for('.upt_index_detail', index_id=0)[:-1]
    )


@blueprint.route("/jsonmapping", methods=['GET'])
def get_indexjson():
    """provide the index tree json for top page."""

    result = IndexTrees.get()
    if result is None:
        return jsonify([])
    return jsonify(result.tree)


@blueprint.route(
    '/jsonmapping/<pid(recid,record_class='
    '"weko_deposit.api:WekoRecord"):pid_value>',
    methods=['GET']
)
@pass_record
def get_indexjson_by_pid(pid, record):
    """provide the index tree json for top page."""

    result = IndexTrees.get()
    if result is None:
        return jsonify([])
    tree = result.tree

    # edite mode
    if record.get('_oai'):
        reset_tree(record.get('path'), tree)

    return jsonify(tree)


@blueprint.route("/detail/<int:index_id>", methods=['GET'])
@login_required
@index_tree_permission.require(http_exception=403)
def get_index_detail(index_id=0):
    """
    Get the detail info by index_id

    :param index_id: Indentifier of index
    :return: the json data of index detail info
    """
    result = None
    if index_id > 0:
        result = Indexes.get_detail_by_id(index_id)
    if result is None:
        return jsonify(code=400, msg='param error')
    return jsonify(result.serialize())


@blueprint.route("/detail/<int:index_id>", methods=['POST'])
@login_required
@index_tree_permission.require(http_exception=403)
def upt_index_detail(index_id=0):
    """
    Update the detail info

    :param index_id: Indentifier of index
    :return: updated json data of index detail info
    """
    data = request.get_json()
    result = None
    if index_id > 0:
        result = Indexes.upt_detail_by_id(index_id, **data)
    if result is None:
        return jsonify(code=400, msg='param error')
    return jsonify(result.serialize())


@blueprint.route("/thumbnail/<int:index_id>", methods=['GET'])
@login_required
@index_tree_permission.require(http_exception=403)
def get_index_thumbnail(index_id=0):
    """
    Get thumbnail info

    :param index_id: Indentifier of index
    :return: binary data for thumbnail
    """
    result = None
    if index_id > 0:
        result = Indexes.get_Thumbnail_by_id(index_id)
    if result is None:
        return jsonify(code=400, msg='param error')
    return result


@blueprint.route("/thumbnail/<int:index_id>", methods=['POST'])
@login_required
@index_tree_permission.require(http_exception=403)
def upt_index_thumbnail(index_id=0):
    """
    Update the thumbnail of index

    :param index_id: Indentifier of index
    :return: updated detail info of index
    """
    file = request.files['thumbnail_file']
    data = {
        'thumbnail': file.read(),
        'thumbnail_name': secure_filename(file.filename),
        'thumbnail_mime_type': file.content_type
    }
    result = None
    if index_id > 0:
        result = Indexes.upt_detail_by_id(index_id, **data)
    if result is None:
        return jsonify(code=400, msg='param error', data=data)
    return jsonify(result.serialize())


@blueprint.route("/detail/<int:index_id>", methods=['DELETE'])
@login_required
@index_tree_permission.require(http_exception=403)
def del_index_detail(index_id=0):
    """
    Delete the index

    :param index_id: Indentifier of index
    :return: delete info
    """
    result = None
    if index_id > 0:
        """check if item belongs to the index"""
        # index_children_count = Indexes.has_children(index_id)
        # if index_children_count > 0:
        #     return jsonify(code=1, msg='have children index')
        # tree_obj = Indexes.get_self_path(index_id)
        # if tree_obj is None:
        #     # the index has be removed
        #     return jsonify(code=0, msg=_('success'), data={'count': 0})
        # tree_path = tree_obj.path if tree_obj is not None else '0'
        # weko_indexer = ItemRecord()
        # item_count = weko_indexer.get_count_by_index_id(tree_path=tree_path)
        # if item_count > 0:
        #     return jsonify(code=1, msg='have children items')
        result = Indexes.del_by_indexid(index_id)
        weko_indexer = ItemRecord()
        count_del, count_upt = \
            weko_indexer.del_items_by_index_id(str(index_id),
                                               with_children=True)
    if result is None:
        return jsonify(code=400, msg='param error')
    return jsonify(code=0, msg='delete success',
                   data={'count_del': count_del, 'count_upt': count_upt})


@blueprint.route("/edit", methods=['GET'])
@login_required
@index_tree_permission.require(http_exception=403)
def edit_get():
    """Render the index tree edit page."""

    result = IndexTrees.get()
    index_tree = []
    if result is not None:
        index_tree = json.dumps(result.tree, indent=4, ensure_ascii=False)
    return render_template(
        current_app.config['WEKO_INDEX_TREE_EDIT_TEMPLATE'],
        index_tree=index_tree)


@blueprint.route("/edit", methods=['POST', 'PUT'])
@login_required
@index_tree_permission.require(http_exception=403)
def edit():
    """Update the index tree."""

    tree_info = request.get_json()
    #    tree_info = json.loads(str(data))
    result = IndexTrees.update(tree=tree_info)
    if result is None:
        return jsonify(msg=_('Fail'))
    indexes = get_all_children(tree_info)
    result = Indexes.create(indexes=indexes)
    if result is None:
        return jsonify(msg=_('Fail'))
    return jsonify(msg=_('Success'))


@blueprint.route("/items/count/<tree_id>", methods=['GET'])
def items_count(tree_id):
    """
    Get the count of item which belongs to the index

    :param tree_id: Indentifier of index
    :return: the count of item
    """
    tree_obj = Indexes.get_self_path(tree_id)
    if tree_obj is None:
        return jsonify(code=0, msg=_('success'), data={'count': 0})
    tree_path = tree_obj.path if tree_obj is not None else '0'
    weko_indexer = ItemRecord()
    item_count = weko_indexer.get_count_by_index_id(tree_path=tree_path)
    return jsonify(code=0, msg=_('success'),
                   data={'count': item_count})


@blueprint.route("/move/<child_id>/<parent_id>", methods=['GET'])
def move_up(child_id, parent_id):
    """
    Move the branch of children to the branch of parent

    :param child_id: Indentifier of child index
    :param parent_id: Indentifier of parent index
    :return: the count info of updated index
    """
    index_children_count = Indexes.has_children(parent_id)
    weko_indexer = ItemRecord()
    count_del, count_upt = weko_indexer.del_items_by_index_id(child_id)
    return jsonify(code=0, msg=_('success'),
                   data={'count': index_children_count, 'del': count_del,
                         'upt': count_upt})
