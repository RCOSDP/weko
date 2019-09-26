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
from weko_index_tree.models import IndexStyle
from weko_index_tree.utils import get_index_link_list
from weko_records_ui.ipaddr import check_site_license_permission
from weko_search_ui.api import get_search_detail_keyword

from .utils import get_design_layout, get_weko_contents, has_widget_design

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
    get_args = request.args
    ctx = {'community': None}
    community_id = ""
    if 'community' in get_args:
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

    if hasattr(current_i18n, 'language'):
        index_link_list = get_index_link_list(current_i18n.language)
    else:
        index_link_list = get_index_link_list()

    detail_condition = get_search_detail_keyword('')
    check_site_license_permission()
    send_info = {}
    send_info['site_license_flag'] = True \
        if hasattr(current_user, 'site_license_flag') else False
    send_info['site_license_name'] = current_user.site_license_name \
        if hasattr(current_user, 'site_license_name') else ''
    top_viewed.send(current_app._get_current_object(),
                    info=send_info)

    # For front page, always use main layout
    page, render_widgets = get_design_layout(
        current_app.config['WEKO_THEME_DEFAULT_COMMUNITY'])
    render_header_footer = has_widget_design(
        current_app.config['WEKO_THEME_DEFAULT_COMMUNITY'],
        current_i18n.language)
    page = None

    return render_template(
        current_app.config['THEME_FRONTPAGE_TEMPLATE'],
        page=page,
        render_widgets=render_widgets,
        render_header_footer=render_header_footer,
        **get_weko_contents(request.args))


@blueprint.route('/edit')
def edit():
    """Simplistic front page view."""
    return render_template(
        current_app.config['BASE_EDIT_TEMPLATE'],
    )


@blueprint.app_template_filter('get_site_info')
def get_site_info(site_info):
    """Get site info.

    :return: result

    """
    from weko_admin.models import SiteInfo
    from weko_admin.utils import get_site_name_for_current_language
    site_info = SiteInfo.get()
    site_name = site_info.site_name if site_info and site_info.site_name else []
    title = get_site_name_for_current_language(site_name) \
        or current_app.config['THEME_SITENAME']
    favicon = request.url_root + 'api/admin/favicon'
    prefix = ''
    if site_info and site_info.favicon:
        prefix = site_info.favicon.split(",")[0] == 'data:image/x-icon;base64'
    if not prefix:
        favicon = site_info.favicon if site_info and site_info.favicon else ''

    result = {
        'title': title,
        'site_name': site_info.site_name if site_info
        and site_info.site_name else [],
        'description': site_info.description if site_info
        and site_info.description else '',
        'copy_right': site_info.copy_right if site_info
        and site_info.copy_right else '',
        'keyword': site_info.keyword if site_info and site_info.keyword else '',
        'favicon': favicon,
        'url': request.url
    }
    return result
