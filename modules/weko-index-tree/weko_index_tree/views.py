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

from flask import Blueprint, current_app, json, jsonify, render_template, \
    request
from flask_babelex import gettext as _

from .api import Indexes, IndexTrees
from .utils import get_all_children

blueprint = Blueprint(
    'weko_index_tree',
    __name__,
    url_prefix='/indextree',
    template_folder='templates',
    static_folder='static',
)


@blueprint.route("/")
def index():
    """Render the index tree edit page."""
    result = IndexTrees.get()
    current_app.logger.debug(result)
    index_tree = []
    if result is not None:
        index_tree = json.dumps(result.tree, indent=4, ensure_ascii=False)
    current_app.logger.debug(index_tree)
    return render_template(
        current_app.config['WEKO_INDEX_TREE_INDEX_TEMPLATE'],
        index_tree=index_tree)


@blueprint.route("/jsonmapping", methods=['GET'])
def get_indexjson():
    """Render the index tree edit page."""
    result = IndexTrees.get()
    return jsonify(result.tree)


@blueprint.route("/edit", methods=['POST'])
def edit():
    """Update the index tree."""
    data = request.get_json()
    tree_info = json.loads(data.get('index_tree'))
    current_app.logger.debug(data.get('index_tree'))
    current_app.logger.debug(json.loads(data.get('index_tree')))
    result = IndexTrees.update(tree=tree_info)
    if result is None:
        return jsonify(msg=_('Fail'))
    indexes = get_all_children(tree_info)
    result = Indexes.create(indexes=indexes)
    if result is None:
        return jsonify(msg=_('Fail'))
    return jsonify(msg=_('Success'))
