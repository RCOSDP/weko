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


from blinker import Namespace
from flask import Blueprint, current_app, flash, render_template, request, \
    session
from flask_login import login_required
from flask_security import current_user
from invenio_i18n.ext import current_i18n
from weko_admin.utils import set_default_language
from weko_index_tree.models import Index, IndexStyle
from weko_records_ui.ipaddr import check_site_license_permission
from weko_search_ui.api import get_search_detail_keyword

_signals = Namespace()
top_viewed = _signals.signal('top-viewed')

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
    community_id = ""
    if 'community' in getArgs:
        from weko_workflow.api import GetCommunity
        comm = GetCommunity.get_community_by_id(request.args.get('community'))
        ctx = {'community': comm}
        community_id = comm.id
    # In case user opens the web for the first time,
    # set default language base on Admin language setting
    set_default_language()
    # Get index style
    style = IndexStyle.get(
        current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'])
    if not style:
        IndexStyle.create(
            current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'],
            width=3,
            height=None)
        style = IndexStyle.get(
            current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'])
    width = style.width
    height = style.height
    index_link_enabled = style.index_link_enabled

    index_link_list = []
    for index in Index.query.all():
        if index.index_link_enabled and index.public_state:
            if hasattr(current_i18n, 'language'):
                if current_i18n.language == 'ja' and index.index_link_name:
                    index_link_list.append((index.id, index.index_link_name))
                else:
                    index_link_list.append(
                        (index.id, index.index_link_name_english))
            else:
                index_link_list.append(
                    (index.id, index.index_link_name_english))

    detail_condition = get_search_detail_keyword('')
    check_site_license_permission()
    send_info = {}
    send_info['site_license_flag'] = True \
        if hasattr(current_user, 'site_license_flag') else False
    send_info['site_license_name'] = current_user.site_license_name \
        if hasattr(current_user, 'site_license_name') else ''
    top_viewed.send(current_app._get_current_object(),
                    info=send_info)
    return render_template(
        current_app.config['THEME_FRONTPAGE_TEMPLATE'],
        render_widgets=True,
        community_id=community_id,
        detail_condition=detail_condition,
        width=width, height=height,
        index_link_list=index_link_list,
        index_link_enabled=index_link_enabled, **ctx)


@blueprint.route('/edit')
def edit():
    """Simplistic front page view."""
    return render_template(
        current_app.config['BASE_EDIT_TEMPLATE'],
    )
