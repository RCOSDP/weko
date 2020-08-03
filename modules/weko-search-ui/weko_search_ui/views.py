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

import time
from xml.etree import ElementTree

from blinker import Namespace
from flask import Blueprint, current_app, jsonify, render_template, request
from flask_security import current_user
from invenio_db import db
from invenio_i18n.ext import current_i18n
from weko_admin.models import AdminSettings
from weko_gridlayout.utils import get_widget_design_page_with_main, \
    main_design_has_main_widget
from weko_index_tree.api import Indexes
from weko_index_tree.models import IndexStyle
from weko_index_tree.utils import get_index_link_list
from weko_records.api import ItemLink
from weko_records_ui.ipaddr import check_site_license_permission
from weko_theme.utils import get_design_layout

from weko_search_ui.api import get_search_detail_keyword

from .api import SearchSetting
from .config import WEKO_SEARCH_TYPE_DICT
from .utils import check_permission, get_feedback_mail_list, \
    get_journal_info, parse_feedback_mail_data

_signals = Namespace()
searched = _signals.signal('searched')

blueprint = Blueprint(
    'weko_search_ui',
    __name__,
    template_folder='templates',
    static_folder='static',
)

blueprint_api = Blueprint(
    'weko_search_ui',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.route("/search/index")
def search():
    """Index Search page ui."""
    search_type = request.args.get('search_type', WEKO_SEARCH_TYPE_DICT[
        'FULL_TEXT'])
    get_args = request.args
    community_id = ""
    ctx = {'community': None}
    cur_index_id = search_type if search_type not in \
        (WEKO_SEARCH_TYPE_DICT['FULL_TEXT'], WEKO_SEARCH_TYPE_DICT[
            'KEYWORD'], ) else None
    if 'community' in get_args:
        from weko_workflow.api import GetCommunity
        comm = GetCommunity.get_community_by_id(request.args.get('community'))
        ctx = {'community': comm}
        community_id = comm.id

    # Get the design for widget rendering
    page, render_widgets = get_design_layout(
        community_id or current_app.config['WEKO_THEME_DEFAULT_COMMUNITY'])

    # Get index style
    style = IndexStyle.get(
        current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'])
    width = style.width if style else '3'

    # add at 1206 for search management
    sort_options, display_number = SearchSetting.get_results_setting()
    ts = time.time()
    disply_setting = dict(size=display_number, timestamp=ts)

    detail_condition = get_search_detail_keyword('')

    export_settings = AdminSettings.get('item_export_settings') or \
        AdminSettings.Dict2Obj(
            current_app.config['WEKO_ADMIN_DEFAULT_ITEM_EXPORT_SETTINGS'])

    height = style.height if style else None
    if 'item_link' in get_args:
        from weko_workflow.api import WorkActivity

        activity_id = request.args.get('item_link')
        workflow_activity = WorkActivity()
        activity_detail, item, steps, action_id, cur_step, temporary_comment,\
            approval_record, step_item_login_url, histories, res_check, pid, \
            community_id, ctx = workflow_activity.get_activity_index_search(
                activity_id=activity_id)

        recid = approval_record.get('control_number', None)
        if recid:
            pid_without_ver = recid.split('.')[0]
            item_link = ItemLink.get_item_link_info(pid_without_ver)
            ctx['item_link'] = item_link

        return render_template(
            'weko_workflow/activity_detail.html',
            page=page,
            render_widgets=render_widgets,
            activity=activity_detail,
            item=item,
            steps=steps,
            action_id=action_id,
            cur_step=cur_step,
            temporary_comment=temporary_comment,
            record=approval_record,
            step_item_login_url=step_item_login_url,
            histories=histories,
            res_check=res_check,
            pid=pid,
            index_id=cur_index_id,
            community_id=community_id,
            width=width,
            height=height,
            allow_item_exporting=export_settings.allow_item_exporting,
            is_permission=check_permission(),
            is_login=bool(current_user.get_id()),
            **ctx)
    else:
        journal_info = None
        index_display_format = '1'
        check_site_license_permission()
        send_info = dict()
        send_info['site_license_flag'] = True \
            if hasattr(current_user, 'site_license_flag') else False
        send_info['site_license_name'] = current_user.site_license_name \
            if hasattr(current_user, 'site_license_name') else ''
        if search_type in WEKO_SEARCH_TYPE_DICT.values():
            searched.send(
                current_app._get_current_object(),
                search_args=get_args,
                info=send_info
            )
            if search_type == WEKO_SEARCH_TYPE_DICT['INDEX']:
                cur_index_id = request.args.get('q', '0')
                journal_info = get_journal_info(cur_index_id)
                index_info = Indexes.get_index(cur_index_id)
                if index_info:
                    index_display_format = index_info.display_format
                    if index_display_format == '2':
                        disply_setting = dict(size=100, timestamp=ts)

        if hasattr(current_i18n, 'language'):
            index_link_list = get_index_link_list(current_i18n.language)
        else:
            index_link_list = get_index_link_list()
        return render_template(
            current_app.config['SEARCH_UI_SEARCH_TEMPLATE'],
            page=page,
            render_widgets=render_widgets,
            index_id=cur_index_id,
            community_id=community_id,
            sort_option=sort_options,
            disply_setting=disply_setting,
            detail_condition=detail_condition,
            width=width,
            height=height,
            index_link_enabled=style.index_link_enabled,
            index_link_list=index_link_list,
            journal_info=journal_info,
            index_display_format=index_display_format,
            allow_item_exporting=export_settings.allow_item_exporting,
            is_permission=check_permission(),
            is_login=bool(current_user.get_id()),
            **ctx)


@blueprint_api.route('/opensearch/description.xml', methods=['GET'])
def opensearch_description():
    """Returns WEKO3 opensearch description document.

    :return:
    """
    # create a response
    response = current_app.response_class()

    # set the returned data, which will just contain the title
    ns_opensearch = "http://a9.com/-/spec/opensearch/1.1/"

    ElementTree.register_namespace('', ns_opensearch)
    # ElementTree.register_namespace('jairo', ns_jairo)

    root = ElementTree.Element('OpenSearchDescription')

    sname = ElementTree.SubElement(root, '{' + ns_opensearch + '}ShortName')
    sname.text = current_app.config['WEKO_OPENSEARCH_SYSTEM_SHORTNAME']

    des = ElementTree.SubElement(root, '{' + ns_opensearch + '}Description')
    des.text = current_app.config['WEKO_OPENSEARCH_SYSTEM_DESCRIPTION']

    img = ElementTree.SubElement(root, '{' + ns_opensearch + '}Image')
    img.set('height', '16')
    img.set('width', '16')
    img.set('type', 'image/x-icon')
    img.text = request.host_url + \
        current_app.config['WEKO_OPENSEARCH_IMAGE_URL']

    url = ElementTree.SubElement(root, '{' + ns_opensearch + '}Url')
    url.set('type', 'application/atom+xml')
    url.set('template', request.host_url
            + 'api/opensearch/search?q={searchTerms}')

    url = ElementTree.SubElement(root, '{' + ns_opensearch + '}Url')
    url.set('type', 'application/atom+xml')
    url.set('template', request.host_url
            + 'api/opensearch/search?q={searchTerms}&amp;format=atom')

    response.data = ElementTree.tostring(root)

    # update headers
    response.headers['Content-Type'] = 'application/xml'
    return response


@blueprint.route("/journal_info/<int:index_id>", methods=['GET'])
def journal_detail(index_id=0):
    """Render a check view."""
    result = get_journal_info(index_id)
    return jsonify(result)


@blueprint.route("/search/feedback_mail_list", methods=['GET'])
def search_feedback_mail_list():
    """Render a check view."""
    data = get_feedback_mail_list()
    result = {}
    if data:
        result = parse_feedback_mail_data(data)
    return jsonify(result)


@blueprint.route("/get_child_list/<int:index_id>", methods=['GET'])
def get_child_list(index_id=0):
    """Get child id list to index list display."""
    return jsonify(Indexes.get_child_id_list(index_id))


@blueprint.route("/get_path_name_dict/<string:path_str>", methods=['GET'])
def get_path_name_dict(path_str=''):
    """Get path and name."""
    path_name_dict = {}
    path_arr = path_str.split('_')
    for path in path_arr:
        index = Indexes.get_index(index_id=path)
        path_name_dict[path] = index.index_name
    return jsonify(path_name_dict)
