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


import time

from blinker import Namespace
from flask import Blueprint, current_app, jsonify, render_template, request
from flask_security import current_user
from invenio_i18n.ext import current_i18n
from invenio_db import db
from weko_admin.models import SiteInfo
from weko_admin.utils import get_search_setting
from weko_records_ui.ipaddr import check_site_license_permission

from .utils import MainScreenInitDisplaySetting, get_design_layout, \
    get_weko_contents, has_widget_design

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


@blueprint.route('/get_search_setting', methods=['GET'])
def get_default_search_setting():
    """Site license setting page."""
    data = get_search_setting()
    data = {
        "dlt_dis_num_selected": data.get('dlt_dis_num_selected'),
        "dlt_index_sort_selected": data.get('dlt_index_sort_selected'),
        "dlt_keyword_sort_selected": data.get('dlt_keyword_sort_selected'),
        "init_disp_setting": data.get('init_disp_setting')
    }
    return jsonify({'status': 1, "data": data})


@blueprint.app_template_filter('get_site_info')
def get_site_info(site_info):
    """Get site info.

    :return: result

    """
    from weko_admin.utils import get_notify_for_current_language, \
        get_site_name_for_current_language
    site_info = SiteInfo.get()
    site_name = site_info.site_name if site_info and site_info.site_name else []
    notify = site_info.notify if site_info and site_info.notify else []
    try:
        google_tracking_id_user = site_info.google_tracking_id_user if site_info.google_tracking_id_user else current_app.config['GOOGLE_TRACKING_ID_USER']
    except BaseException:
        google_tracking_id_user = ""
    
    title = get_site_name_for_current_language(site_name) \
        or current_app.config['THEME_SITENAME']
    login_instructions = get_notify_for_current_language(notify)
    ts = time.time()
    favicon = request.url_root + 'api/admin/favicon'
    prefix = ''
    if site_info and site_info.favicon:
        prefix = site_info.favicon.split(",")[0] == 'data:image/x-icon;base64'
    if not prefix:
        favicon = site_info.favicon if site_info and site_info.favicon else ''
    ogp_image = ''
    if site_info and site_info.ogp_image:
        ogp_image = request.url_root + 'api/admin/ogp_image'

    result = {
        'title': title,
        'login_instructions': login_instructions,
        'site_name': site_info.site_name if site_info
        and site_info.site_name else [],
        'description': site_info.description if site_info
        and site_info.description else '',
        'copy_right': site_info.copy_right if site_info
        and site_info.copy_right else '',
        'keyword': site_info.keyword if site_info and site_info.keyword else '',
        'favicon': favicon,
        'ogp_image': ogp_image,
        'url': request.url,
        'notify': site_info.notify if site_info
        and site_info.notify else [],
        'enable_notify': current_app.config[
            "WEKO_ADMIN_ENABLE_LOGIN_INSTRUCTIONS"],
        'google_tracking_id_user': google_tracking_id_user if google_tracking_id_user else "",
    }
    return result


@blueprint.app_template_filter('get_init_display_setting')
def get_init_display_setting(settings):
    """Get initial display settings.

    :param settings:
    :return:
    """
    init_display_setting = MainScreenInitDisplaySetting() \
        .get_init_display_setting()
    return init_display_setting

# @blueprint.teardown_request
# def dbsession_clean(exception):
#     current_app.logger.debug("weko_theme dbsession_clean: {}".format(exception))
#     if exception is None:
#         try:
#             db.session.commit()
#         except:
#             db.session.rollback()
#     db.session.remove()