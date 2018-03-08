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

from flask import Blueprint, current_app, flash, json, jsonify, \
    render_template, request, url_for
from flask_babelex import gettext as _
from flask_login import login_required
from werkzeug.utils import secure_filename

from .api import Indexes, IndexTrees
from .permissions import index_tree_permission
from .utils import get_all_children

blueprint = Blueprint(
    'weko_index_tree',
    __name__,
    url_prefix='/indextree',
    template_folder='templates',
    static_folder='static',
)


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


@blueprint.route("/detail/<int:index_id>", methods=['GET'])
@login_required
@index_tree_permission.require(http_exception=403)
def get_index_detail(index_id=0):
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
    data = request.get_json()
    result = None
    if index_id > 0:
        result = Indexes.upt_detail_by_id(index_id, **data)
    if result is None:
        return jsonify(code=400, msg='param error')
    flash(_('update index detail info success.'), category='success')
    return jsonify(result.serialize())


@blueprint.route("/thumbnail/<int:index_id>", methods=['GET'])
@login_required
@index_tree_permission.require(http_exception=403)
def get_index_thumbnail(index_id=0):
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
    result = None
    if index_id > 0:
        """check if item belongs to the index"""
        # TODO
        result = Indexes.del_by_indexid(index_id)
    if result is None:
        return jsonify(code=400, msg='param error')
    return jsonify(code=0, msg='delete success')


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
