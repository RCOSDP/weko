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


from flask import (Blueprint, current_app, render_template)
from flask_login import login_required

from .permissions import index_tree_permission

blueprint = Blueprint(
    'weko_index_tree',
    __name__,
    url_prefix='/indextree',
    template_folder='templates',
    static_folder='static',
)


@blueprint.route('/')
@login_required
@index_tree_permission.require(http_exception=403)
def index():
    """Render the index tree edit page."""
    return render_template(
        current_app.config['WEKO_INDEX_TREE_INDEX_TEMPLATE'],
        get_tree_json=current_app.config["WEKO_INDEX_TREE_LIST_API"],
        upt_tree_json="",
        mod_tree_detail=current_app.config["WEKO_INDEX_TREE_API"]
    )

