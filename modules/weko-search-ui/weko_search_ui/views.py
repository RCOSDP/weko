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

"""Blueprint for weko-search-ui."""

from flask import Blueprint, current_app, request, render_template

blueprint = Blueprint(
    'weko_search_ui',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.route("/search/index")
def search():
    """ Index Search page ui."""
    search_type = request.args.get('search_type', '0')
    cur_index_id = search_type if search_type not in ('0', '1', ) else None
    return render_template(current_app.config['SEARCH_UI_SEARCH_TEMPLATE'],
                           index_id=cur_index_id)
