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

"""Blueprint for weko-theme."""


from flask import Blueprint, current_app, render_template, request, flash
from weko_index_tree.models import IndexStyle
from flask_login import login_required

blueprint = Blueprint(
    'weko_theme',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.route('/')
def index():
    """Simplistic front page view."""
    getArgs = request.args
    ctx = {'community': None}
    community_id=""
    if 'community' in getArgs:
        from weko_workflow.api import GetCommunity
        comm = GetCommunity.get_community_by_id(request.args.get('community'))
        ctx = {'community': comm}
        community_id = comm.id

    # Get index style
    style = IndexStyle.get(current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'])
    width = style.width if style else '3'

    return render_template(
        current_app.config['THEME_FRONTPAGE_TEMPLATE'],
        community_id =community_id, width=width, **ctx)


@blueprint.route('/edit')
def edit():
    """Simplistic front page view."""
    return render_template(
        current_app.config['BASE_EDIT_TEMPLATE'],
    )

@blueprint.route("/item_management")
@login_required
def item_management():
    """Render view."""
    page_id="itemManagement"
    return render_template(
        current_app.config['WEKO_ITEM_MANAGEMENT_INIT_TEMPLATE'],
        page_id=page_id
    )
