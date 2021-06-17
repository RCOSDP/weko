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

"""Blueprint for weko-workflow."""

import copy
import json
import os
import sys
from collections import OrderedDict
from functools import wraps

import redis
from flask import Blueprint, abort, current_app, jsonify, render_template, \
    request, session, url_for
from flask_babelex import gettext as _
from flask_login import current_user, login_required
from invenio_accounts.models import Role, User, userrole
from invenio_db import db
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidrelations.models import PIDRelation
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_pidstore.resolver import Resolver
from invenio_records.models import RecordMetadata
from simplekv.memory.redisstore import RedisStore
from sqlalchemy import types
from sqlalchemy.sql.expression import cast
from weko_accounts.api import ShibUser
from weko_accounts.utils import login_required_customize
from weko_authors.models import Authors
from weko_deposit.api import WekoDeposit
from weko_deposit.links import base_factory
from weko_deposit.pidstore import get_record_identifier, \
    get_record_without_version
from weko_items_ui.api import item_login
from weko_items_ui.utils import to_files_js
from weko_records.api import FeedbackMailList, ItemLink, ItemsMetadata
from weko_records.models import ItemMetadata
from weko_records.serializers.utils import get_item_type_name
from weko_records_ui.models import FilePermission
from weko_records_ui.utils import get_list_licence, get_roles, get_terms, \
    get_workflows
from weko_user_profiles.config import WEKO_USERPROFILES_INSTITUTE_POSITION_LIST, \
    WEKO_USERPROFILES_POSITION_LIST
from werkzeug.utils import import_string

from .api import Action, Flow, GetCommunity, WorkActivity, \
    WorkActivityHistory, WorkFlow
from .config import IDENTIFIER_GRANT_LIST, IDENTIFIER_GRANT_SELECT_DICT, \
    IDENTIFIER_GRANT_SUFFIX_METHOD, WEKO_WORKFLOW_TODO_TAB
from .models import ActionStatusPolicy, Activity, ActivityAction, FlowAction
from .romeo import search_romeo_issn, search_romeo_jtitles
from .utils import IdentifierHandle, auto_fill_title, \
    check_authority_by_admin, check_continue, check_existed_doi, \
    create_onetime_download_url_to_guest, delete_cache_data, \
    delete_guest_activity, filter_all_condition, get_account_info, \
    get_actionid, get_activity_display_info, \
    get_activity_id_of_record_without_version, get_allow_multi_thumbnail, \
    get_application_and_approved_date, get_approval_keys, get_cache_data, \
    get_files_and_thumbnail, get_identifier_setting, get_item_link_info, \
    get_pid_and_record, get_record_by_root_ver, get_thumbnails, \
    get_usage_data, get_workflow_item_type_names, handle_finish_workflow, \
    init_activity_for_guest_user, is_enable_item_name_link, \
    is_hidden_pubdate, is_show_autofill_metadata, \
    is_usage_application_item_type, item_metadata_validation, \
    prepare_data_for_guest_activity, process_send_approval_mails, \
    process_send_notification_mail, process_send_reminder_mail, register_hdl, \
    save_activity_data, saving_doi_pidstore, \
    send_usage_application_mail_for_guest_user, set_files_display_type, \
    update_approval_date, update_cache_data, validate_guest_activity_expired, \
    validate_guest_activity_token

blueprint = Blueprint(
    'weko_workflow',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/workflow'
)


@blueprint.route('/')
@login_required
def index():
    """Render a basic view."""
    if not current_user or not current_user.roles:
        return abort(403)

    activity = WorkActivity()
    getargs = request.args
    conditions = filter_all_condition(getargs)
    ctx = {'community': None}
    community_id = ""
    from weko_theme.utils import get_design_layout

    # Get the design for widget rendering
    page, render_widgets = get_design_layout(
        request.args.get('community') or current_app.config[
            'WEKO_THEME_DEFAULT_COMMUNITY'])

    tab = request.args.get('tab')
    tab = WEKO_WORKFLOW_TODO_TAB if not tab else tab
    if 'community' in getargs:
        activities, maxpage, size, pages, name_param = activity \
            .get_activity_list(request.args.get('community'),
                               conditions=conditions)
        comm = GetCommunity.get_community_by_id(request.args.get('community'))
        ctx = {'community': comm}
        community_id = comm.id
    else:
        activities, maxpage, size, pages, name_param = activity \
            .get_activity_list(conditions=conditions)

    pagination_visible_pages = current_app.config. \
        get('WEKO_WORKFOW_PAGINATION_VISIBLE_PAGES')
    options = current_app.config.get('WEKO_WORKFLOW_SELECT_DICT')
    item_type = current_app.config.get('WEKO_ITEMS_UI_USAGE_REPORT')
    action_status = current_app.config.get('WEKO_WORKFLOW_ACTION')
    send_mail = current_app.config.get('WEKO_WORKFLOW_ENABLE_AUTO_SEND_EMAIL')
    req_per_page = current_app.config.get('WEKO_WORKFLOW_PER_PAGE')
    columns = current_app.config.get('WEKO_WORKFLOW_COLUMNS')
    filters = current_app.config.get('WEKO_WORKFLOW_FILTER_COLUMNS')
    send_mail_user_group = current_app.config.get(
        'WEKO_WORKFLOW_SEND_MAIL_USER_GROUP')

    enable_show_activity = current_app.config[
        'WEKO_WORKFLOW_ENABLE_SHOW_ACTIVITY']

    if enable_show_activity:
        get_application_and_approved_date(activities, columns)
        get_workflow_item_type_names(activities)

    from weko_user_profiles.config import WEKO_USERPROFILES_ADMINISTRATOR_ROLE
    admin_role = WEKO_USERPROFILES_ADMINISTRATOR_ROLE
    has_admin_role = False
    for role in current_user.roles:
        if role == admin_role:
            has_admin_role = True
            break
    send_mail = has_admin_role and send_mail

    return render_template(
        'weko_workflow/activity_list.html',
        page=page,
        pages=pages,
        name_param=name_param,
        size=size,
        tab=tab,
        maxpage=maxpage,
        render_widgets=render_widgets,
        enable_show_activity=enable_show_activity,
        activities=activities,
        community_id=community_id,
        columns=columns,
        send_mail=send_mail,
        req_per_page=req_per_page,
        pagination_visible_pages=pagination_visible_pages,
        options=options,
        item_type=item_type,
        action_status=action_status,
        filters=filters,
        send_mail_user_group=send_mail_user_group,
        **ctx
    )


@blueprint.route('/iframe/success', methods=['GET'])
def iframe_success():
    """Renders an item register view.

    :return: The rendered template.
    """
    files_thumbnail = None
    # get session value
    history = WorkActivityHistory()
    histories = history.get_activity_history_list(session['itemlogin_id'])
    activity = session['itemlogin_activity']
    item = session['itemlogin_item']
    steps = session['itemlogin_steps']
    action_id = session['itemlogin_action_id']
    cur_step = session['itemlogin_cur_step']
    res_check = session['itemlogin_res_check']
    pid = session['itemlogin_pid']
    community_id = session.get('itemlogin_community_id')
    record = None
    files = []
    if item and item.get('pid') and 'value' in item['pid']:
        record, files = get_record_by_root_ver(item['pid']['value'])
        files_thumbnail = get_thumbnails(files, None)
    else:
        record = session['itemlogin_record']
    ctx = {'community': None}
    if community_id:
        comm = GetCommunity.get_community_by_id(community_id)
        ctx = {'community': comm}

    from weko_theme.utils import get_design_layout

    # Get the design for widget rendering
    page, render_widgets = get_design_layout(
        community_id or current_app.config['WEKO_THEME_DEFAULT_COMMUNITY'])

    work_activity = WorkActivity()
    activity_action = work_activity.get_activity_action_comment(
        activity.activity_id, action_id, activity.action_order)
    action_comment = activity_action.action_comment \
        if activity_action and activity_action.action_comment else ''

    action = Action().get_action_detail(action_id)
    action_endpoint = action.action_endpoint
    workflow = WorkFlow()
    workflow_detail = workflow.get_workflow_by_id(activity.workflow_id)
    item_type_name = get_item_type_name(workflow_detail.itemtype_id)

    return render_template('weko_workflow/item_login_success.html',
                           page=page,
                           render_widgets=render_widgets,
                           activity=activity,
                           item=item,
                           steps=steps,
                           action_id=action_id,
                           cur_step=cur_step,
                           record=record,
                           histories=histories,
                           res_check=res_check,
                           pid=pid,
                           files=files,
                           community_id=community_id,
                           action_comment=action_comment,
                           files_thumbnail=files_thumbnail,
                           is_enable_item_name_link=is_enable_item_name_link(
                               action_endpoint, item_type_name),
                           **ctx)


@blueprint.route('/activity/new', methods=['GET'])
@login_required
def new_activity():
    """New activity."""
    workflow = WorkFlow()
    workflows = workflow.get_workflow_list()
    workflows = workflow.get_workflows_by_roles(workflows)
    getargs = request.args
    ctx = {'community': None}
    community_id = ""
    if 'community' in getargs:
        comm = GetCommunity.get_community_by_id(request.args.get('community'))
        ctx = {'community': comm}
        community_id = comm.id

    # Process exclude workflows
    from weko_workflow.utils import exclude_admin_workflow
    exclude_admin_workflow(workflows)

    from weko_theme.utils import get_design_layout

    # Get the design for widget rendering
    page, render_widgets = get_design_layout(
        community_id or current_app.config['WEKO_THEME_DEFAULT_COMMUNITY'])

    return render_template(
        'weko_workflow/workflow_list.html',
        page=page,
        render_widgets=render_widgets,
        workflows=workflows, community_id=community_id, **ctx
    )


@blueprint.route('/activity/init', methods=['POST'])
@login_required
def init_activity():
    """Init activity."""
    post_activity = request.get_json()
    activity = WorkActivity()
    getargs = request.args
    if 'community' in getargs:
        rtn = activity.init_activity(
            post_activity, request.args.get('community'))
    else:
        rtn = activity.init_activity(post_activity)
    if rtn is None:
        return jsonify(code=-1, msg='error')
    url = url_for('weko_workflow.display_activity',
                  activity_id=rtn.activity_id)
    if 'community' in getargs and request.args.get('community') != 'undefined':
        comm = GetCommunity.get_community_by_id(request.args.get('community'))
        url = url_for('weko_workflow.display_activity',
                      activity_id=rtn.activity_id, community=comm.id)
    return jsonify(code=0, msg='success',
                   data={'redirect': url})


@blueprint.route('/activity/list', methods=['GET'])
@login_required
def list_activity():
    """List activity."""
    activity = WorkActivity()
    getargs = request.args
    conditions = filter_all_condition(getargs)

    activities, maxpage, size, pages, name_param = activity.get_activity_list(
        conditions=conditions)

    from weko_theme.utils import get_design_layout

    # Get the design for widget rendering
    page, render_widgets = get_design_layout(
        current_app.config['WEKO_THEME_DEFAULT_COMMUNITY'])
    tab = request.args.get('tab')
    tab = 'todo' if not tab else tab
    return render_template(
        'weko_workflow/activity_list.html',
        page=page,
        pages=pages,
        name_param=name_param,
        size=size,
        tab=tab,
        maxpage=maxpage,
        render_widgets=render_widgets,
        activities=activities
    )


@blueprint.route('/activity/init-guest', methods=['POST'])
def init_activity_guest():
    """Init activity for guest user.

    @return:
    """
    post_data = request.get_json()

    if post_data.get('guest_mail'):
        # Prepare activity data.
        data = {
            'itemtype_id': post_data.get('item_type_id'),
            'workflow_id': post_data.get('workflow_id'),
            'flow_id': post_data.get('flow_id'),
            'activity_confirm_term_of_use': True,
            'extra_info': {
                "guest_mail": post_data.get('guest_mail'),
                "record_id": post_data.get('record_id'),
                "related_title": post_data.get('guest_item_title'),
                "file_name": post_data.get('file_name'),
                "is_restricted_access": True,
            }
        }
        __, tmp_url = init_activity_for_guest_user(data)

        if send_usage_application_mail_for_guest_user(
                post_data.get('guest_mail'), tmp_url):
            return jsonify(msg=_('Email is sent successfully.'))
    return jsonify(msg='Cannot send mail')


@blueprint.route('/activity/guest-user/<string:file_name>', methods=['GET'])
def display_guest_activity(file_name=""):
    """Display activity for guest user.

    @param file_name:File name
    @return:
    """
    # Get token
    from weko_workflow.models import GuestActivity
    GuestActivity.get_expired_activities()
    token = request.args.get('token')
    # Validate token
    is_valid, activity_id, guest_email = validate_guest_activity_token(
        token, file_name)
    if not is_valid:
        return render_template("weko_theme/error.html",
                               error=_("Token is invalid"))

    error_msg = validate_guest_activity_expired(activity_id)
    if error_msg:
        return render_template("weko_theme/error.html",
                               error=error_msg)

    session['guest_token'] = token
    session['guest_email'] = guest_email
    session['guest_url'] = request.full_path

    guest_activity = prepare_data_for_guest_activity(activity_id)

    # Get Auto fill data for Restricted Access Item Type.
    usage_data = get_usage_data(
        guest_activity.get('id'), guest_activity.get('activity'))
    guest_activity.update(usage_data)

    # Get item link info.
    item_link_info = get_item_link_info(activity_id,
                                        guest_activity.get('activity'))
    guest_activity.update(
        dict(
            record_after_update=item_link_info.get('record'),
            newFiles=item_link_info.get('files'),
            new_thumbnail=item_link_info.get('files_thumbnail'),
            record=item_link_info.get('record', []),
            files=item_link_info.get('files', []),
            files_thumbnail=item_link_info.get('files_thumbnail', [])
        )
    )

    return render_template(
        'weko_workflow/activity_detail.html',
        **guest_activity
    )


@blueprint.route('/activity/detail/<string:activity_id>',
                 methods=['GET', 'POST'])
@login_required
def display_activity(activity_id="0"):
    """Display activity."""
    activity = WorkActivity()
    if "?" in activity_id:
        activity_id = activity_id.split("?")[0]
    action_endpoint, action_id, activity_detail, cur_action, histories, item, \
        steps, temporary_comment, workflow_detail = \
        get_activity_display_info(activity_id)

    # display_activity of Identifier grant
    identifier_setting = None
    if action_endpoint == 'identifier_grant' and item:
        community_id = request.args.get('community', None)
        if not community_id:
            community_id = 'Root Index'
        identifier_setting = get_identifier_setting(community_id)

        # valid date pidstore_identifier data
        if identifier_setting:
            text_empty = '<Empty>'
            if not identifier_setting.jalc_doi:
                identifier_setting.jalc_doi = text_empty
            if not identifier_setting.jalc_crossref_doi:
                identifier_setting.jalc_crossref_doi = text_empty
            if not identifier_setting.jalc_datacite_doi:
                identifier_setting.jalc_datacite_doi = text_empty
            if not identifier_setting.ndl_jalc_doi:
                identifier_setting.ndl_jalc_doi = text_empty
    temporary_identifier_select = 0
    temporary_identifier_inputs = []
    last_identifier_setting = activity.get_action_identifier_grant(
        activity_id=activity_id, action_id=action_id)
    if last_identifier_setting:
        temporary_identifier_select = last_identifier_setting.get(
            'action_identifier_select')
        temporary_identifier_inputs.append(
            last_identifier_setting.get('action_identifier_jalc_doi'))
        temporary_identifier_inputs.append(
            last_identifier_setting.get('action_identifier_jalc_cr_doi'))
        temporary_identifier_inputs.append(
            last_identifier_setting.get('action_identifier_jalc_dc_doi'))
        temporary_identifier_inputs.append(
            last_identifier_setting.get('action_identifier_ndl_jalc_doi'))

    temporary_journal = activity.get_action_journal(
        activity_id=activity_id, action_id=action_id)
    if temporary_journal:
        temporary_journal = temporary_journal.action_journal

    cur_step = action_endpoint
    step_item_login_url = None
    approval_record = []
    recid = None
    record = {}
    need_file = False
    need_billing_file = False
    json_schema = ''
    schema_form = ''
    item_save_uri = ''
    files = []
    endpoints = {}
    links = None
    need_thumbnail = False
    files_thumbnail = []
    allow_multi_thumbnail = False
    term_and_condition_content = ''
    is_auto_set_index_action = True
    application_item_type = False
    title = ""
    data_type = activity_detail.extra_info.get(
        "related_title") if activity_detail.extra_info else None
    show_autofill_metadata = True
    is_hidden_pubdate_value = False
    position_list = WEKO_USERPROFILES_POSITION_LIST
    institute_position_list = WEKO_USERPROFILES_INSTITUTE_POSITION_LIST
    item_type_name = get_item_type_name(workflow_detail.itemtype_id)

    if 'item_login' == action_endpoint or \
            'item_login_application' == action_endpoint or \
            'file_upload' == action_endpoint:
        activity_session = dict(
            activity_id=activity_id,
            action_id=activity_detail.action_id,
            action_version=cur_action.action_version,
            action_status=ActionStatusPolicy.ACTION_DOING,
            commond=''
        )
        session['activity_info'] = activity_session
        # get item edit page info.
        step_item_login_url, need_file, need_billing_file, \
            record, json_schema, schema_form,\
            item_save_uri, files, endpoints, need_thumbnail, files_thumbnail, \
            allow_multi_thumbnail \
            = item_login(item_type_id=workflow_detail.itemtype_id)
        application_item_type = is_usage_application_item_type(activity_detail)
        if not record and item:
            record = item

        sessionstore = RedisStore(redis.StrictRedis.from_url(
            'redis://{host}:{port}/1'.format(
                host=os.getenv('INVENIO_REDIS_HOST', 'localhost'),
                port=os.getenv('INVENIO_REDIS_PORT', '6379'))))
        if sessionstore.redis.exists(
            'updated_json_schema_{}'.format(activity_id)) \
            and sessionstore.get(
                'updated_json_schema_{}'.format(activity_id)):
            json_schema = (json_schema + "/{}").format(activity_id)
            schema_form = (schema_form + "/{}").format(activity_id)
        title = auto_fill_title(item_type_name)
        show_autofill_metadata = is_show_autofill_metadata(item_type_name)
        is_hidden_pubdate_value = is_hidden_pubdate(item_type_name)

    # if 'approval' == action_endpoint:
    if item:
        # get record data for the first time access to editing item screen
        recid, approval_record = get_pid_and_record(item)
        files, files_thumbnail = get_files_and_thumbnail(activity_id, item)

        links = base_factory(recid)

    res_check = check_authority_action(str(activity_id), int(action_id),
                                       is_auto_set_index_action,
                                       activity_detail.action_order)
    getargs = request.args
    ctx = {'community': None}
    community_id = ""
    if 'community' in getargs:
        comm = GetCommunity.get_community_by_id(request.args.get('community'))
        ctx = {'community': comm}
        community_id = comm.id
    # be use for index tree and comment page.
    if 'item_login' == action_endpoint or \
            'item_login_application' == action_endpoint or \
            'file_upload' == action_endpoint:
        session['itemlogin_id'] = activity_id
        session['itemlogin_activity'] = activity_detail
        session['itemlogin_item'] = item
        session['itemlogin_steps'] = steps
        session['itemlogin_action_id'] = action_id
        session['itemlogin_cur_step'] = cur_step
        session['itemlogin_record'] = approval_record
        session['itemlogin_histories'] = histories
        session['itemlogin_res_check'] = res_check
        session['itemlogin_pid'] = recid
        session['itemlogin_community_id'] = community_id

    user_id = current_user.id
    user_profile = {}
    if user_id:
        from weko_user_profiles.views import get_user_profile_info
        user_profile['results'] = get_user_profile_info(int(user_id))
    from weko_theme.utils import get_design_layout

    # Get the design for widget rendering
    page, render_widgets = get_design_layout(
        community_id or current_app.config['WEKO_THEME_DEFAULT_COMMUNITY'])
    list_license = get_list_licence()

    if action_endpoint == 'item_link' and recid:
        item_link = ItemLink.get_item_link_info(recid.pid_value)
        ctx['item_link'] = item_link

    # Get item link info.
    item_link_info = get_item_link_info(
        activity_id, activity_detail, action_endpoint, item,
        approval_record, files, files_thumbnail)
    ctx.update(
        dict(
            record_after_update=item_link_info.get('record'),
            newFiles=item_link_info.get('files'),
            new_thumbnail=item_link_info.get('files_thumbnail'),
        )
    )

    # Get email approval key
    approval_email_key = get_approval_keys()

    # Get Auto fill data for Restricted Access Item Type.
    usage_data = get_usage_data(
        workflow_detail.itemtype_id, activity_detail, user_profile)
    ctx.update(usage_data)

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
        temporary_journal=temporary_journal,
        temporary_idf_grant=temporary_identifier_select,
        temporary_idf_grant_suffix=temporary_identifier_inputs,
        idf_grant_data=identifier_setting,
        idf_grant_input=IDENTIFIER_GRANT_LIST,
        idf_grant_method=current_app.config.get(
            'IDENTIFIER_GRANT_SUFFIX_METHOD', IDENTIFIER_GRANT_SUFFIX_METHOD),
        record=approval_record,
        records=record,
        step_item_login_url=step_item_login_url,
        need_file=need_file,
        need_billing_file=need_billing_file,
        jsonschema=json_schema,
        schemaform=schema_form,
        id=workflow_detail.itemtype_id,
        item_save_uri=item_save_uri,
        files=files,
        endpoints=endpoints,
        error_type='item_login_error',
        links=links,
        histories=histories,
        res_check=res_check,
        pid=recid,
        community_id=community_id,
        need_thumbnail=need_thumbnail,
        files_thumbnail=files_thumbnail,
        allow_multi_thumbnail=allow_multi_thumbnail,
        is_auto_set_index_action=is_auto_set_index_action,
        term_and_condition_content=term_and_condition_content,
        enable_feedback_maillist=current_app.config[
            'WEKO_WORKFLOW_ENABLE_FEEDBACK_MAIL'],
        enable_contributor=current_app.config[
            'WEKO_WORKFLOW_ENABLE_CONTRIBUTOR'],
        activity_id=activity_detail.activity_id,
        user_profile=user_profile,
        application_item_type=application_item_type,
        auto_fill_title=title,
        out_put_report_title=current_app.config[
            "WEKO_ITEMS_UI_OUTPUT_REGISTRATION_TITLE"],
        auto_fill_data_type=data_type,
        is_show_autofill_metadata=show_autofill_metadata,
        is_hidden_pubdate=is_hidden_pubdate_value,
        action_endpoint_key=current_app.config.get(
            'WEKO_ITEMS_UI_ACTION_ENDPOINT_KEY'),
        approval_email_key=approval_email_key,
        position_list=position_list,
        institute_position_list=institute_position_list,
        is_enable_item_name_link=is_enable_item_name_link(
            action_endpoint, item_type_name),
        list_license=list_license,
        **ctx
    )


def check_authority(func):
    """Check Authority."""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        work = WorkActivity()
        activity_id = kwargs.get('activity_id')
        activity_detail = work.get_activity_by_id(activity_id)

        # If user has admin role
        if check_authority_by_admin(activity_detail):
            return func(*args, **kwargs)

        roles, users = work.get_activity_action_role(
            activity_id=kwargs.get('activity_id'),
            action_id=kwargs.get('action_id'),
            action_order=activity_detail.action_order
        )
        cur_user = current_user.get_id()
        cur_role = db.session.query(Role).join(userrole).filter_by(
            user_id=cur_user).all()
        error_msg = _('Authorization required')
        if users['deny'] and int(cur_user) in users['deny']:
            return jsonify(code=403, msg=error_msg)
        if users['allow'] and int(cur_user) not in users['allow']:
            return jsonify(code=403, msg=error_msg)
        for role in cur_role:
            if roles['deny'] and role.id in roles['deny']:
                return jsonify(code=403, msg=error_msg)
            if roles['allow'] and role.id not in roles['allow']:
                return jsonify(code=403, msg=error_msg)
        return func(*args, **kwargs)

    return decorated_function


def check_authority_action(activity_id='0', action_id=0,
                           contain_login_item_application=False,
                           action_order=0):
    """Check authority."""
    if not current_user.is_authenticated:
        return 1

    work = WorkActivity()
    activity = Activity.query.filter_by(activity_id=activity_id).first()
    # If user has admin role
    if check_authority_by_admin(activity):
        return 0

    roles, users = work.get_activity_action_role(activity_id, action_id,
                                                 action_order)
    cur_user = current_user.get_id()
    cur_role = db.session.query(Role).join(userrole).filter_by(
        user_id=cur_user).all()

    # If action_user is set:
    # If current_user is in denied action_user
    if users['deny'] and int(cur_user) in users['deny']:
        return 1
    # If current_user is in allowed action_user
    if users['allow'] and int(cur_user) in users['allow']:
        return 0
    # Else if action_user is not set
    # or action_user does not contain current_user:
    for role in cur_role:
        if roles['deny'] and role.id in roles['deny']:
            return 1
        if roles['allow'] and role.id not in roles['allow']:
            return 1

    # If action_roles is not set
    # or action roles does not contain any role of current_user:
    # Gather information
    # If user is the author of activity
    if int(cur_user) == activity.activity_login_user and \
            not contain_login_item_application:
        return 0

    if current_app.config['WEKO_WORKFLOW_ENABLE_CONTRIBUTOR']:
        # Check if this activity has contributor equaling to current user
        im = ItemMetadata.query.filter_by(id=activity.item_id) \
            .filter(
            cast(ItemMetadata.json['shared_user_id'], types.INT)
            == int(cur_user)).one_or_none()
        if im:
            # There is an ItemMetadata with contributor equaling to current
            # user, allow to access
            return 0
    # Check current user is action handler of activity
    activity_action_obj = ActivityAction.query.filter_by(
        activity_id=activity_id, action_id=action_id,
        action_order=action_order).first()
    if (activity_action_obj.action_handler
            and int(activity_action_obj.action_handler) == int(cur_user)
            and contain_login_item_application):
        return 0

    # Otherwise, user has no permission
    return 1


@blueprint.route(
    '/activity/action/<string:activity_id>/<int:action_id>',
    methods=['POST'])
@login_required_customize
@check_authority
def next_action(activity_id='0', action_id=0):
    """Next action."""
    work_activity = WorkActivity()
    history = WorkActivityHistory()
    activity_detail = work_activity.get_activity_detail(activity_id)
    action_order = activity_detail.action_order
    post_json = request.get_json()
    activity = dict(
        activity_id=activity_id,
        action_id=action_id,
        action_version=post_json.get('action_version'),
        action_status=ActionStatusPolicy.ACTION_DONE,
        commond=post_json.get('commond'),
        action_order=action_order
    )

    action = Action().get_action_detail(action_id)
    action_endpoint = action.action_endpoint

    if action_endpoint == 'begin_action':
        return jsonify(code=0, msg=_('success'))

    if action_endpoint == 'end_action':
        work_activity.end_activity(activity)
        return jsonify(code=0, msg=_('success'))
    if 'approval' == action_endpoint:
        update_approval_date(activity_detail)
    item_id = None
    recid = None
    deposit = None
    pid_without_ver = None
    current_pid = None
    if activity_detail and activity_detail.item_id:
        item_id = activity_detail.item_id
        current_pid = PersistentIdentifier.get_by_object(pid_type='recid',
                                                         object_type='rec',
                                                         object_uuid=item_id)
        recid = get_record_identifier(current_pid.pid_value)
        deposit = WekoDeposit.get_record(item_id)
        if deposit:
            pid_without_ver = get_record_without_version(current_pid)

    if action_endpoint in ['item_login',
                           'item_login_application'] and current_pid and \
        current_pid is pid_without_ver and \
            current_app.config.get('WEKO_HANDLE_ALLOW_REGISTER_CRNI'):
        register_hdl(activity_id)
    flow = Flow()
    next_flow_action = flow.get_next_flow_action(
        activity_detail.flow_define.flow_id, action_id, action_order)
    next_action_endpoint = next_flow_action[0].action.action_endpoint
    next_action_id = next_flow_action[0].action_id
    next_action_order = next_flow_action[
        0].action_order if action_order else None
    # Start to send mail
    if 'approval' in [action_endpoint, next_action_endpoint]:
        current_flow_action = flow.get_flow_action_detail(
            activity_detail.flow_define.flow_id, action_id, action_order)
        next_action_detail = work_activity.get_activity_action_comment(
            activity_id, next_action_id,
            next_action_order)
        is_last_approval_step = work_activity \
            .is_last_approval_step(activity_id, action_id, action_order) \
            if action_endpoint == "approval" else False
        # Only gen url file link at last approval step
        url_and_expired_date = {}
        if is_last_approval_step:
            url_and_expired_date = create_onetime_download_url_to_guest(
                activity_detail.activity_id,
                activity_detail.extra_info)
            if not url_and_expired_date:
                url_and_expired_date = {}
        action_mails_setting = {"previous":
                                current_flow_action.send_mail_setting
                                if current_flow_action.send_mail_setting
                                else {},
                                "next": next_flow_action[0].send_mail_setting
                                if next_flow_action[0].send_mail_setting
                                else {},
                                "approval": True,
                                "reject": False}

        next_action_handler = next_action_detail.action_handler
        # in case of current action has action user
        if next_action_handler == -1:
            current_flow_action = FlowAction.query.filter_by(
                flow_id=activity_detail.flow_define.flow_id,
                action_id=next_action_id,
                action_order=next_action_order).one_or_none()
            if current_flow_action and current_flow_action.action_roles and \
                    current_flow_action.action_roles[0].action_user:
                next_action_handler = current_flow_action.action_roles[
                    0].action_user
        process_send_approval_mails(activity_detail, action_mails_setting,
                                    next_action_handler,
                                    url_and_expired_date)
    if current_app.config.get(
        'WEKO_WORKFLOW_ENABLE_AUTO_SEND_EMAIL') and \
        current_user.is_authenticated and \
        (not activity_detail.extra_info or not
            activity_detail.extra_info.get('guest_mail')):
        process_send_notification_mail(activity_detail,
                                       action_endpoint, next_action_endpoint)

    if post_json.get('temporary_save') == 1 \
            and action_endpoint not in ['identifier_grant', 'item_link']:
        if 'journal' in post_json:
            work_activity.create_or_update_action_journal(
                activity_id=activity_id,
                action_id=action_id,
                journal=post_json.get('journal'))
        else:
            work_activity.upt_activity_action_comment(
                activity_id=activity_id,
                action_id=action_id,
                comment=post_json.get('commond'),
                action_order=action_order
            )
        return jsonify(code=0, msg=_('success'))
    elif post_json.get('journal'):
        work_activity.create_or_update_action_journal(
            activity_id=activity_id,
            action_id=action_id,
            journal=post_json.get('journal')
        )

    if action_endpoint == 'approval' and item_id:
        item = ItemsMetadata.get_record(id_=item_id)
        pid_identifier = PersistentIdentifier.get_by_object(
            pid_type='depid', object_type='rec', object_uuid=item.id)
        record_class = import_string('weko_deposit.api:WekoRecord')
        resolver = Resolver(pid_type='recid', object_type='rec',
                            getter=record_class.get_record)
        _pid, _approval_record = resolver.resolve(pid_identifier.pid_value)

        action_feedbackmail = work_activity.get_action_feedbackmail(
            activity_id=activity_id,
            action_id=current_app.config.get(
                "WEKO_WORKFLOW_ITEM_REGISTRATION_ACTION_ID", 3))
        if action_feedbackmail:
            item_ids = [item_id]
            if not recid and pid_without_ver:
                if ".0" in current_pid.pid_value:
                    pv = PIDVersioning(child=pid_without_ver)
                    last_ver = PIDVersioning(parent=pv.parent).get_children(
                        pid_status=PIDStatus.REGISTERED
                    ).filter(PIDRelation.relation_type == 2).order_by(
                        PIDRelation.index.desc()).first()
                    item_ids.append(last_ver.object_uuid)
                else:
                    draft_pid = PersistentIdentifier.get(
                        'recid',
                        '{}.0'.format(pid_without_ver.pid_value)
                    )
                    item_ids.append(draft_pid.object_uuid)
                item_ids.append(pid_without_ver.object_uuid)

            if action_feedbackmail.feedback_maillist:
                FeedbackMailList.update_by_list_item_id(
                    item_ids=item_ids,
                    feedback_maillist=action_feedbackmail.feedback_maillist
                )
            else:
                FeedbackMailList.delete_by_list_item_id(item_ids)

        if deposit:
            deposit.update_feedback_mail()
            deposit.update_jpcoar_identifier()

    if action_endpoint == 'item_link' and item_id:
        current_pid = PersistentIdentifier.get_by_object(
            pid_type='recid',
            object_type='rec',
            object_uuid=item_id
        )

        if not pid_without_ver:
            pid_without_ver = get_record_without_version(current_pid)

        item_link = ItemLink(current_pid.pid_value)
        relation_data = post_json.get('link_data')
        if relation_data:
            err = item_link.update(relation_data)
            if err:
                return jsonify(code=-1, msg=_(err))
        if post_json.get('temporary_save') == 1:
            work_activity.upt_activity_action_comment(
                activity_id=activity_id,
                action_id=action_id,
                comment=post_json.get('commond'),
                action_order=action_order
            )
            return jsonify(code=0, msg=_('success'))

    # save pidstore_identifier to ItemsMetadata
    identifier_select = post_json.get('identifier_grant')
    if 'identifier_grant' == action_endpoint and identifier_select:
        idf_grant_jalc_doi_manual = post_json.get(
            'identifier_grant_jalc_doi_suffix')
        idf_grant_jalc_cr_doi_manual = post_json.get(
            'identifier_grant_jalc_cr_doi_suffix')
        idf_grant_jalc_dc_doi_manual = post_json.get(
            'identifier_grant_jalc_dc_doi_suffix')
        idf_grant_ndl_jalc_doi_manual = post_json.get(
            'identifier_grant_ndl_jalc_doi_suffix')

        # If is action identifier_grant, then save to to database
        identifier_grant = {
            'action_identifier_select': identifier_select,
            'action_identifier_jalc_doi': idf_grant_jalc_doi_manual,
            'action_identifier_jalc_cr_doi': idf_grant_jalc_cr_doi_manual,
            'action_identifier_jalc_dc_doi': idf_grant_jalc_dc_doi_manual,
            'action_identifier_ndl_jalc_doi': idf_grant_ndl_jalc_doi_manual
        }

        work_activity.create_or_update_action_identifier(
            activity_id=activity_id,
            action_id=action_id,
            identifier=identifier_grant
        )

        error_list = item_metadata_validation(item_id, identifier_select)

        if post_json.get('temporary_save') == 1:
            return jsonify(code=0, msg=_('success'))

        if isinstance(error_list, str):
            return jsonify(code=-1, msg=_(error_list))

        sessionstore = RedisStore(redis.StrictRedis.from_url(
            'redis://{host}:{port}/1'.format(
                host=os.getenv('INVENIO_REDIS_HOST', 'localhost'),
                port=os.getenv('INVENIO_REDIS_PORT', '6379'))))
        if error_list:
            sessionstore.put(
                'updated_json_schema_{}'.format(activity_id),
                json.dumps(error_list).encode('utf-8'),
                ttl_secs=300)
            return previous_action(
                activity_id=activity_id,
                action_id=action_id,
                req=-1
            )
        else:
            if sessionstore.redis.exists(
                    'updated_json_schema_{}'.format(activity_id)):
                sessionstore.delete(
                    'updated_json_schema_{}'.format(activity_id))

        if identifier_select != IDENTIFIER_GRANT_SELECT_DICT['NotGrant'] \
                and item_id is not None:
            record_without_version = item_id
            if deposit and pid_without_ver and not recid:
                record_without_version = pid_without_ver.object_uuid
            saving_doi_pidstore(item_id, record_without_version, post_json,
                                int(identifier_select))

    rtn = history.create_activity_history(activity, action_order)
    if not rtn:
        return jsonify(code=-1, msg=_('error'))
    # next action
    work_activity.upt_activity_action_status(
        activity_id=activity_id, action_id=action_id,
        action_status=ActionStatusPolicy.ACTION_DONE,
        action_order=action_order
    )
    work_activity.upt_activity_action_comment(
        activity_id=activity_id,
        action_id=action_id,
        comment='',
        action_order=action_order
    )
    flow = Flow()
    next_flow_action = flow.get_next_flow_action(
        activity_detail.flow_define.flow_id, action_id, action_order)
    if next_flow_action and len(next_flow_action) > 0:
        next_action_endpoint = next_flow_action[0].action.action_endpoint
        if 'end_action' == next_action_endpoint:
            new_activity_id = None
            if deposit:
                new_activity_id = handle_finish_workflow(deposit,
                                                         current_pid,
                                                         recid)
                if not new_activity_id:
                    return jsonify(code=-1, msg=_('error'))

            # Remove to file permission
            permission = FilePermission.find_by_activity(activity_id)
            if permission:
                FilePermission.delete_object(permission)

            activity.update(
                action_id=next_action_id,
                action_version=next_flow_action[0].action_version,
                item_id=new_activity_id,
                action_order=next_action_order
            )
            work_activity.end_activity(activity)
        else:
            work_activity.upt_activity_action(
                activity_id=activity_id, action_id=next_action_id,
                action_status=ActionStatusPolicy.ACTION_DOING,
                action_order=next_action_order)
            work_activity.upt_activity_action_status(
                activity_id=activity_id, action_id=next_action_id,
                action_status=ActionStatusPolicy.ACTION_DOING,
                action_order=next_action_order)
    # delete session value
    if session.get('itemlogin_id'):
        del session['itemlogin_id']
        del session['itemlogin_activity']
        del session['itemlogin_item']
        del session['itemlogin_steps']
        del session['itemlogin_action_id']
        del session['itemlogin_cur_step']
        del session['itemlogin_record']
        del session['itemlogin_res_check']
        del session['itemlogin_pid']
        del session['itemlogin_community_id']
    return jsonify(code=0, msg=_('success'))


@blueprint.route(
    '/activity/action/<string:activity_id>/<int:action_id>'
    '/rejectOrReturn/<int:req>',
    methods=['POST'])
@login_required
@check_authority
def previous_action(activity_id='0', action_id=0, req=0):
    """Previous action."""
    post_data = request.get_json()
    activity = dict(
        activity_id=activity_id,
        action_id=action_id,
        action_version=post_data.get('action_version'),
        action_status=ActionStatusPolicy.ACTION_THROWN_OUT if 0 == req else
        ActionStatusPolicy.ACTION_RETRY,
        commond=post_data.get('commond')
    )
    work_activity = WorkActivity()
    history = WorkActivityHistory()
    # next action
    activity_detail = work_activity.get_activity_by_id(activity_id)
    action_order = activity_detail.action_order
    flow = Flow()
    rtn = history.create_activity_history(activity, action_order)
    if rtn is None:
        return jsonify(code=-1, msg=_('error'))
    current_flow_action = flow.\
        get_flow_action_detail(
            activity_detail.flow_define.flow_id, action_id, action_order)
    action_mails_setting = {
        "previous": current_flow_action.send_mail_setting
        if current_flow_action.send_mail_setting else {},
        "next": {},
        "approval": False,
        "reject": True}
    process_send_approval_mails(activity_detail, action_mails_setting, -1, {})
    try:
        pid_identifier = PersistentIdentifier.get_by_object(
            pid_type='doi', object_type='rec',
            object_uuid=activity_detail.item_id)
        with db.session.begin_nested():
            db.session.delete(pid_identifier)
        db.session.commit()
    except PIDDoesNotExistError as pidNotEx:
        current_app.logger.info(pidNotEx)

    if req == -1:
        pre_action = flow.get_item_registration_flow_action(
            activity_detail.flow_define.flow_id)
    elif req == 0:
        pre_action = flow.get_previous_flow_action(
            activity_detail.flow_define.flow_id, action_id,
            action_order)
    else:
        pre_action = flow.get_next_flow_action(
            activity_detail.flow_define.flow_id, 1, 1)

    if pre_action and len(pre_action) > 0:
        previous_action_id = pre_action[0].action_id
        previous_action_order = pre_action[
            0].action_order if action_order else None
        if req == 0:
            work_activity.upt_activity_action_status(
                activity_id=activity_id,
                action_id=action_id,
                action_status=ActionStatusPolicy.ACTION_THROWN_OUT,
                action_order=action_order)
        else:
            work_activity.upt_activity_action_status(
                activity_id=activity_id, action_id=action_id,
                action_status=ActionStatusPolicy.ACTION_RETRY,
                action_order=action_order)
        work_activity.upt_activity_action_status(
            activity_id=activity_id, action_id=previous_action_id,
            action_status=ActionStatusPolicy.ACTION_DOING,
            action_order=previous_action_order)
        work_activity.upt_activity_action(
            activity_id=activity_id, action_id=previous_action_id,
            action_status=ActionStatusPolicy.ACTION_DOING,
            action_order=previous_action_order)
    return jsonify(code=0, msg=_('success'))


@blueprint.route('/journal/list', methods=['GET'])
def get_journals():
    """Get journals."""
    key = request.values.get('key')
    if not key:
        return jsonify({})

    datastore = RedisStore(redis.StrictRedis.from_url(
        current_app.config['CACHE_REDIS_URL']))
    cache_key = current_app.config[
        'WEKO_WORKFLOW_OAPOLICY_SEARCH'].format(keyword=key)

    if datastore.redis.exists(cache_key):
        data = datastore.get(cache_key)
        multiple_result = json.loads(
            data.decode('utf-8'),
            object_pairs_hook=OrderedDict)

    else:
        multiple_result = search_romeo_jtitles(key, 'starts') if key else {}
        try:
            datastore.put(
                cache_key,
                json.dumps(multiple_result).encode('utf-8'),
                ttl_secs=int(
                    current_app.config['WEKO_WORKFLOW_OAPOLICY_CACHE_TTL']))
        except Exception:
            pass

    return jsonify(multiple_result)


@blueprint.route('/journal/<string:method>/<string:value>', methods=['GET'])
def get_journal(method, value):
    """Get journal."""
    if not method or not value:
        return jsonify({})

    if method == 'issn':
        result = search_romeo_issn(value)
    else:
        value = value.split(" / ")[0]
        result = search_romeo_jtitles(value, 'exact')

    if result['romeoapi'] and int(result['romeoapi']['header']['numhits']) > 1:
        if isinstance(result['romeoapi']['journals']['journal'], list):
            result['romeoapi']['journals']['journal'] = \
                result['romeoapi']['journals']['journal'][0]
        if isinstance(result['romeoapi']['publishers']['publisher'], list):
            result['romeoapi']['publishers']['publisher'] = \
                result['romeoapi']['publishers']['publisher'][0]

    return jsonify(result)


@blueprint.route(
    '/activity/action/<string:activity_id>/<int:action_id>'
    '/cancel',
    methods=['POST'])
@login_required_customize
@check_authority
def cancel_action(activity_id='0', action_id=0):
    """Next action."""
    post_json = request.get_json()
    work_activity = WorkActivity()
    # Clear deposit
    activity_detail = work_activity.get_activity_by_id(activity_id)

    activity = dict(
        activity_id=activity_id,
        action_id=action_id,
        action_version=post_json.get('action_version'),
        action_status=ActionStatusPolicy.ACTION_CANCELED,
        commond=post_json.get('commond'),
        action_order=activity_detail.action_order
    )

    # Clear deposit
    if activity_detail:
        cancel_item_id = activity_detail.item_id
        if not cancel_item_id:
            pid_value = post_json.get('pid_value')
            if pid_value:
                pid = PersistentIdentifier.get('recid', pid_value)
                cancel_item_id = pid.object_uuid
        if cancel_item_id:
            cancel_record = WekoDeposit.get_record(cancel_item_id)
            try:
                with db.session.begin_nested():
                    if cancel_record:
                        cancel_deposit = WekoDeposit(
                            cancel_record, cancel_record.model)
                        cancel_deposit.clear()
                        # Remove draft child
                        cancel_pid = PersistentIdentifier.get_by_object(
                            pid_type='recid',
                            object_type='rec',
                            object_uuid=cancel_item_id)
                        cancel_pv = PIDVersioning(child=cancel_pid)
                        if cancel_pv.exists:
                            cancel_pv.remove_child(cancel_pid)
                db.session.commit()
            except Exception:
                db.session.rollback()
                current_app.logger.error(
                    'Unexpected error: {}', sys.exc_info()[0])
                return jsonify(code=-1,
                               msg=sys.exc_info()[0])

    work_activity.upt_activity_action_status(
        activity_id=activity_id, action_id=action_id,
        action_status=ActionStatusPolicy.ACTION_CANCELED,
        action_order=activity_detail.action_order)

    rtn = work_activity.quit_activity(activity)

    if not rtn:
        work_activity.upt_activity_action_status(
            activity_id=activity_id, action_id=action_id,
            action_status=ActionStatusPolicy.ACTION_DOING,
            action_order=activity_detail.action_order)
        return jsonify(code=-1, msg=_('Error! Cannot process quit activity!'))

    if session.get("guest_url"):
        url = session.get("guest_url")
    else:
        url = url_for('weko_workflow.display_activity',
                      activity_id=activity_id)

    if activity_detail.extra_info and \
            activity_detail.extra_info.get('guest_mail'):
        delete_guest_activity(activity_id)

    # Remove to file permission
    permission = FilePermission.find_by_activity(activity_id)
    if permission:
        FilePermission.delete_object(permission)

    return jsonify(code=0,
                   msg=_('success'),
                   data={'redirect': url})


@blueprint.route(
    '/activity/detail/<string:activity_id>/<int:action_id>'
    '/withdraw',
    methods=['POST'])
@login_required_customize
@check_authority
def withdraw_confirm(activity_id='0', action_id='0'):
    """Check weko user info.

    :return:
    """
    try:
        post_json = request.get_json()
        password = post_json.get('passwd', None)
        if not password:
            return jsonify(code=-1,
                           msg=_('Password not provided'))
        wekouser = ShibUser()
        if password == 'DELETE':
        #if wekouser.check_weko_user(current_user.email, password):
            activity = WorkActivity()
            item_id = activity.get_activity_detail(activity_id).item_id
            identifier_actionid = get_actionid('identifier_grant')
            identifier = activity.get_action_identifier_grant(
                activity_id,
                identifier_actionid)
            identifier_handle = IdentifierHandle(item_id)

            if identifier_handle.delete_pidstore_doi():
                identifier['action_identifier_select'] = \
                    current_app.config.get(
                        "WEKO_WORKFLOW_IDENTIFIER_GRANT_IS_WITHDRAWING", -2)
                if identifier:
                    activity.create_or_update_action_identifier(
                        activity_id,
                        identifier_actionid,
                        identifier)
                    current_pid = PersistentIdentifier.get_by_object(
                        pid_type='recid',
                        object_type='rec',
                        object_uuid=item_id)
                    recid = get_record_identifier(current_pid.pid_value)
                    if not recid:
                        pid_without_ver = get_record_without_version(
                            current_pid)
                        record_without_ver_activity_id = \
                            get_activity_id_of_record_without_version(
                                pid_without_ver)
                        if record_without_ver_activity_id is not None:
                            without_ver_item_id = activity.get_activity_detail(
                                record_without_ver_activity_id).item_id
                            without_ver_identifier_handle = IdentifierHandle(
                                item_id)
                            without_ver_identifier_handle \
                                .remove_idt_registration_metadata()
                            activity.create_or_update_action_identifier(
                                record_without_ver_activity_id,
                                identifier_actionid,
                                identifier)

                if session.get("guest_url"):
                    url = session.get("guest_url")
                else:
                    url = url_for('weko_workflow.display_activity',
                                  activity_id=activity_id)
                return jsonify(
                    code=0,
                    msg=_('success'),
                    data={'redirect': url}
                )
            else:
                return jsonify(code=-1, msg=_('DOI Persistent is not exist.'))
        else:
            return jsonify(code=-1, msg=_('Invalid password'))
    except ValueError:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
    return jsonify(code=-1, msg=_('Error!'))


@blueprint.route('/findDOI', methods=['POST'])
@login_required
def find_doi():
    """Next action."""
    doi_link = request.get_json() or {}
    return jsonify(check_existed_doi(doi_link.get('doi_link')))


@blueprint.route(
    '/save_feedback_maillist/<string:activity_id>/<int:action_id>',
    methods=['POST'])
@login_required
@check_authority
def save_feedback_maillist(activity_id='0', action_id='0'):
    """Save feedback_mail's list to Activity History models.

    :return:
    """
    try:
        if request.headers['Content-Type'] != 'application/json':
            """Check header of request"""
            return jsonify(code=-1, msg=_('Header Error'))

        feedback_maillist = request.get_json()

        work_activity = WorkActivity()
        work_activity.create_or_update_action_feedbackmail(
            activity_id=activity_id,
            action_id=action_id,
            feedback_maillist=feedback_maillist
        )
        return jsonify(code=0, msg=_('Success'))
    except (ValueError, Exception):
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
    return jsonify(code=-1, msg=_('Error'))


@blueprint.route('/get_feedback_maillist/<string:activity_id>',
                 methods=['GET'])
@login_required
def get_feedback_maillist(activity_id='0'):
    """Get feedback_mail's list base on Activity Identifier.

    :param activity_id: Acitivity Identifier.
    :return: Return code and mail list in json format.
    """
    try:
        work_activity = WorkActivity()
        action_feedbackmail = work_activity.get_action_feedbackmail(
            activity_id=activity_id,
            action_id=current_app.config.get(
                "WEKO_WORKFLOW_ITEM_REGISTRATION_ACTION_ID", 3))
        if action_feedbackmail:
            mail_list = action_feedbackmail.feedback_maillist
            for mail in mail_list:
                if mail.get('author_id'):
                    email = Authors.get_first_email_by_id(
                        mail.get('author_id'))
                    if email:
                        mail['email'] = email
                    else:
                        mail_list.remove(mail)
            return jsonify(code=1,
                           msg=_('Success'),
                           data=mail_list)
        else:
            return jsonify(code=0, msg=_('Empty!'))
    except (ValueError, Exception):
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
    return jsonify(code=-1, msg=_('Error'))


@blueprint.route('/activity/lock/<string:activity_id>', methods=['POST'])
@login_required
def lock_activity(activity_id=0):
    """Lock activity."""
    def is_approval_user(activity_id):
        workflow_activity_action = ActivityAction.query.filter_by(
            activity_id=activity_id,
            action_status=ActionStatusPolicy.ACTION_DOING
        ).one_or_none()
        if workflow_activity_action:
            action_handler = workflow_activity_action.action_handler
            if action_handler:
                return int(current_user.get_id()) == int(action_handler)
        return False
    cache_key = 'workflow_locked_activity_{}'.format(activity_id)
    timeout = current_app.permanent_session_lifetime.seconds
    data = request.form.to_dict()
    locked_value = data.get('locked_value')
    cur_locked_val = str(get_cache_data(cache_key)) or str()
    err = ''
    if cur_locked_val and not is_approval_user(activity_id):
        if locked_value != cur_locked_val:
            locked_value = cur_locked_val
            err = _('Locked')
        else:
            update_cache_data(
                cache_key,
                locked_value,
                timeout
            )
    else:
        # create new lock cache
        from datetime import datetime
        locked_value = str(current_user.get_id()) + '-' + \
            str(int(datetime.timestamp(datetime.now()) * 10 ** 3))
        update_cache_data(
            cache_key,
            locked_value,
            timeout
        )

    locked_by_email, locked_by_username = get_account_info(
        locked_value.split('-')[0])
    return jsonify(
        code=200,
        msg='' if err else _('Success'),
        err=err or '',
        locked_value=locked_value,
        locked_by_email=locked_by_email,
        locked_by_username=locked_by_username
    )


@blueprint.route('/activity/unlock/<string:activity_id>', methods=['POST'])
@login_required
def unlock_activity(activity_id=0):
    """Unlock activity."""
    cache_key = 'workflow_locked_activity_{}'.format(activity_id)
    data = json.loads(request.data.decode("utf-8"))
    locked_value = str(data.get('locked_value'))
    msg = None
    # get lock activity from cache
    cur_locked_val = str(get_cache_data(cache_key)) or str()
    if cur_locked_val and cur_locked_val == locked_value:
        delete_cache_data(cache_key)
        msg = _('Unlock success')
    return jsonify(code=200, msg=msg or _('Not unlock'))


@blueprint.route('/check_approval/<string:activity_id>', methods=['GET'])
@login_required
def check_approval(activity_id='0'):
    """Check approval."""
    response = {
        'check_handle': -1,
        'check_continue': -1,
        'error': 1
    }
    try:
        response = check_continue(response, activity_id)
    except (ValueError, Exception):
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
        response['error'] = -1
    return jsonify(response)


@blueprint.route('/send_mail/<string:activity_id>/<string:mail_template>',
                 methods=['POST'])
@login_required
def send_mail(activity_id='0', mail_template=''):
    """Send mail.

    :param activity_id:
    :param mail_template:
    :return:
    """
    try:
        work_activity = WorkActivity()
        activity_detail = work_activity.get_activity_detail(activity_id)
        if current_app.config.get('WEKO_WORKFLOW_ENABLE_AUTO_SEND_EMAIL'):
            process_send_reminder_mail(activity_detail, mail_template)
    except ValueError:
        return jsonify(code=-1, msg='Error')
    return jsonify(code=1, msg='Success')


@blueprint.route('/save_activity_data', methods=['POST'])
@login_required_customize
def save_activity():
    """Save activity.

    @return:
    """
    response = {
        "success": True,
        "msg": ""
    }
    try:
        data = request.get_json()
        save_activity_data(data)
    except Exception as error:
        response['success'] = False
        response["msg"] = str(error)

    return jsonify(response), 200


@blueprint.route('/usage-report', methods=['GET'])
def usage_report():
    """
    Get usage reports.

    @return:
    """
    getargs = request.args
    item_type_usage_report = current_app.config.get(
        'WEKO_ITEMS_UI_USAGE_REPORT')
    conditions = filter_all_condition(getargs)
    conditions['workflow'] = [item_type_usage_report]
    conditions['status'] = ['doing']
    activity = WorkActivity()
    # For usage report, just get all activities with provided conditions
    activities, _, _, _, _ = activity \
        .get_activity_list(conditions=conditions, is_get_all=True)
    get_workflow_item_type_names(activities)
    activities_result = []
    for activity in activities:
        _activity = {"activity_id": activity.activity_id,
                     "item": activity.title,
                     "work_flow": activity.flows_name,
                     "email": activity.email,
                     "status": activity.StatusDesc,
                     "user_role": activity.role_name}
        activities_result.append(_activity)
    return jsonify(activities=activities_result)


@blueprint.route('/get-data-init', methods=['GET'])
@login_required
def get_data_init():
    """Init data."""
    init_workflows = get_workflows()
    init_roles = get_roles()
    init_terms = get_terms()
    return jsonify(
        init_workflows=init_workflows,
        init_roles=init_roles,
        init_terms=init_terms)
