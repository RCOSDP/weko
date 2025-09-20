# -*- coding: utf-8 -*-
"""Blueprint for weko-workflow."""

import json
import re
import shutil
import sys
import traceback
from collections import OrderedDict
from copy import deepcopy
from datetime import datetime
from functools import wraps
from typing import List
from urllib.parse import urljoin

from weko_admin.models import AdminSettings
from weko_items_ui.signals import cris_researchmap_linkage_request
from weko_items_ui.models import CRIS_Institutions, CRISLinkageResult
from weko_workflow.schema.marshmallow import ActionSchema, \
    ActivitySchema, GetRequestMailListSchema, ResponseMessageSchema, CancelSchema, PasswdSchema, LockSchema,\
    ResponseLockSchema, LockedValueSchema, GetFeedbackMailListSchema, SaveActivityResponseSchema,\
    SaveActivitySchema, CheckApprovalSchema,ResponseUnlockSchema, GetItemApplicationSchema
from weko_workflow.schema.utils import get_schema_action, type_null_check
from marshmallow.exceptions import ValidationError

from flask import Response, Blueprint, abort, current_app, has_request_context, \
    jsonify, make_response, render_template, request, session, url_for, redirect
from flask_babelex import gettext as _
from flask_login import current_user, login_required
from flask_security import url_for_security
from flask_security.utils import hash_password
from weko_admin.api import validate_csrf_header
from flask_wtf import FlaskForm
from invenio_accounts.models import Role, User, userrole
from invenio_db import db
from invenio_files_rest.utils import remove_file_cancel_action
from invenio_oauth2server import require_api_auth, require_oauth_scopes
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidrelations.models import PIDRelation
from invenio_pidstore.resolver import Resolver
from invenio_pidstore.errors import PIDDoesNotExistError,PIDDeletedError
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_rest import ContentNegotiatedMethodView
from sqlalchemy.exc import SQLAlchemyError
from weko_redis import RedisConnection
from weko_accounts.models import User
from weko_accounts.utils import login_required_customize
from weko_admin.models import AdminSettings
from weko_authors.models import Authors
from weko_admin.models import AdminSettings
from weko_deposit.api import WekoDeposit, WekoRecord
from weko_deposit.links import base_factory
from weko_deposit.pidstore import get_record_identifier, \
    get_record_without_version
from weko_deposit.signals import item_created
from weko_index_tree.utils import get_user_roles
from weko_items_ui.api import item_login
from weko_items_ui.utils import check_item_is_being_edit, get_workflow_by_item_type_id, \
    get_current_user
from weko_logging.activity_logger import UserActivityLogger
from weko_records.api import FeedbackMailList, RequestMailList, ItemLink, ItemTypes, ItemApplication
from weko_records.models import ItemMetadata
from weko_records.serializers.utils import get_item_type_name
from weko_records_ui.models import FilePermission
from weko_search_ui.utils import check_tsv_import_items, import_items_to_system
from weko_user_profiles.config import \
    WEKO_USERPROFILES_INSTITUTE_POSITION_LIST, \
    WEKO_USERPROFILES_POSITION_LIST
from weko_user_profiles.models import UserProfile
from werkzeug.utils import import_string

from .api import Action, Flow, GetCommunity, WorkActivity, \
    WorkActivityHistory, WorkFlow
from .config import IDENTIFIER_GRANT_LIST, IDENTIFIER_GRANT_SELECT_DICT, \
    IDENTIFIER_GRANT_SUFFIX_METHOD, WEKO_WORKFLOW_TODO_TAB, \
    WEKO_WORKFLOW_DELETION_FLOW_TYPE
from .errors import ActivityBaseRESTError, ActivityNotFoundRESTError, \
    DeleteActivityFailedRESTError, InvalidInputRESTError, \
    RegisteredActivityNotFoundRESTError
from .models import ActionStatusPolicy, Activity, ActivityAction, \
    ActivityStatusPolicy, FlowAction, GuestActivity
from .models import Action as _Action
from .romeo import search_romeo_issn, search_romeo_jtitles
from .scopes import activity_scope
from .utils import IdentifierHandle, auto_fill_title, \
    check_authority_by_admin, check_continue, check_doi_validation_not_pass, \
    check_existed_doi, is_terms_of_use_only, \
    delete_cache_data, delete_guest_activity, filter_all_condition, \
    get_account_info, get_actionid, get_activity_display_info, \
    get_application_and_approved_date, get_approval_keys, get_cache_data, \
    get_files_and_thumbnail, get_identifier_setting, get_main_record_detail, \
    get_pid_and_record, get_pid_value_by_activity_detail, \
    get_record_by_root_ver, get_thumbnails, get_usage_data, \
    get_workflow_item_type_names, grant_access_rights_to_all_open_restricted_files, handle_finish_workflow, \
    init_activity_for_guest_user, is_enable_item_name_link, \
    is_hidden_pubdate, is_show_autofill_metadata, \
    is_usage_application_item_type, prepare_data_for_guest_activity, \
    prepare_doi_link_workflow, process_send_approval_mails, \
    process_send_notification_mail, process_send_reminder_mail, register_hdl, \
    save_activity_data, saving_doi_pidstore, \
    send_usage_application_mail_for_guest_user, set_files_display_type, \
    update_approval_date, update_cache_data, validate_guest_activity_expired, \
    validate_guest_activity_token, get_contributors, make_activitylog_tsv, validate_action_role_user, \
    delete_lock_activity_cache, delete_user_lock_activity_cache, \
    check_an_item_is_locked, prepare_edit_workflow

workflow_blueprint = Blueprint(
    'weko_workflow',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/workflow'
)


depositactivity_blueprint = Blueprint(
    'weko_activity_rest',
    __name__,
    url_prefix='/depositactivity',
)


@workflow_blueprint.app_template_filter('regex_replace')
def regex_replace(s, pattern, replace):
    """

    Args:
        s (_type_): _description_
        pattern (_type_): _description_
        replace (_type_): _description_

    Returns:
        _type_: _description_
    """
    return re.sub(pattern, replace, s)


@workflow_blueprint.route('/')
@login_required
def index():
    """Render the activity list.
    Args:

    Returns:
        str: render result of weko_workflow/activity_list.html
    ---
      get:
        description: Render the activity list
        security:
        - login_required: []
        parameters:
          - name: community
            in: query
            description: community id
            schema:
              type: string
          - name: tab
            in: query
            description: Specify tab name to initial open(todo or all or wait)
            schema:
              type: string
        responses:
          200:
            description: render result of weko_workflow/activity_list.html
            content:
                text/html
    """

    if not current_user or not current_user.roles:
        return abort(403)

    activity = WorkActivity()
    conditions = filter_all_condition(request.args)
    ctx = {'community': None}
    community_id = ""
    from weko_theme.utils import get_design_layout

    # WEKO_THEME_DEFAULT_COMMUNITY = 'Root Index'
    # Get the design for widget rendering
    page, render_widgets = get_design_layout(
        request.args.get('community') or current_app.config[
            'WEKO_THEME_DEFAULT_COMMUNITY'])

    tab = request.args.get('tab',WEKO_WORKFLOW_TODO_TAB)
    if 'community' in request.args:
        activities, maxpage, size, pages, name_param, _ = activity \
            .get_activity_list(conditions=conditions)
        comm = GetCommunity.get_community_by_id(request.args.get('community'))
        ctx = {'community': comm}
        if comm is not None:
            community_id = comm.id
    else:
        activities, maxpage, size, pages, name_param, _ = activity \
            .get_activity_list(conditions=conditions)

    # WEKO_WORKFOW_PAGINATION_VISIBLE_PAGES = 1
    pagination_visible_pages = current_app.config. \
        get('WEKO_WORKFOW_PAGINATION_VISIBLE_PAGES')
    # WEKO_WORKFLOW_SELECT_DICT = []
    options = current_app.config.get('WEKO_WORKFLOW_SELECT_DICT')
    # WEKO_ITEMS_UI_USAGE_REPORT = ""
    item_type = current_app.config.get('WEKO_ITEMS_UI_USAGE_REPORT')
    # WEKO_WORKFLOW_ACTIONS = [
    # WEKO_WORKFLOW_ACTION_START,
    # WEKO_WORKFLOW_ACTION_END,
    # WEKO_WORKFLOW_ACTION_ITEM_REGISTRATION,
    # WEKO_WORKFLOW_ACTION_APPROVAL,
    # WEKO_WORKFLOW_ACTION_ITEM_LINK,
    # WEKO_WORKFLOW_ACTION_IDENTIFIER_GRANT
    # ]
    action_status = current_app.config.get('WEKO_WORKFLOW_ACTION')
    send_mail = current_app.config.get('WEKO_WORKFLOW_ENABLE_AUTO_SEND_EMAIL')
    req_per_page = current_app.config.get('WEKO_WORKFLOW_PER_PAGE')
    columns = current_app.config.get('WEKO_WORKFLOW_COLUMNS')
    filters = current_app.config.get('WEKO_WORKFLOW_FILTER_COLUMNS')
    # WEKO_WORKFLOW_SEND_MAIL_USER_GROUP = {}
    send_mail_user_group = current_app.config.get(
        'WEKO_WORKFLOW_SEND_MAIL_USER_GROUP')
    # WEKO_WORKFLOW_ENABLE_SHOW_ACTIVITY = False
    enable_show_activity = current_app.config[
        'WEKO_WORKFLOW_ENABLE_SHOW_ACTIVITY']

    if enable_show_activity:
        get_application_and_approved_date(activities, columns)
        get_workflow_item_type_names(activities)

    settings = AdminSettings.get('activity_display_settings')

    if settings:
        activity_display_flg = settings.activity_display_flg
    else:
        activity_display_flg = current_app.config.get("WEKO_WORKFLOW_APPROVER_EMAIL_COLUMN_VISIBLE")

    if 'approver_email' in columns and not activity_display_flg:
        columns.remove('approver_email')
    elif 'approver_email' not in columns and activity_display_flg:
        columns.append('approver_email')

    from weko_user_profiles.config import WEKO_USERPROFILES_ADMINISTRATOR_ROLE
    admin_role = WEKO_USERPROFILES_ADMINISTRATOR_ROLE
    has_admin_role = False
    for role in current_user.roles:
        if role == admin_role:
            has_admin_role = True
            break
    send_mail = has_admin_role and send_mail

    # Get Approver Info
    for activitie in activities:
        activitie.approver = []
        activitie.approver_email = []
        steps = activity.get_activity_steps(activitie.activity_id)
        for step in steps:
            if step['ActionName'] == 'Approval':
                approver = User.query.filter_by(email=step['Author']).one_or_none()
                if approver is not None:
                    approver_id = approver.id
                    approver_profile = UserProfile.get_by_userid(approver_id)
                    if hasattr(approver_profile, '_displayname') and approver_profile._displayname:
                        activitie.approver.append(approver_profile._displayname)
                    else:
                        # If the Author has not registered his/her name, use his/her email address.
                        activitie.approver.append(step['Author'])
                else:
                    activitie.approver.append(step['Author'])
                activitie.approver_email.append(step['Author'])

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
        delete_activity_log_enable=current_app.config.get("DELETE_ACTIVITY_LOG_ENABLE"),
        activitylog_roles=current_app.config.get("WEKO_WORKFLOW_ACTIVITYLOG_ROLE_ENABLE"),
        **ctx
    )


@workflow_blueprint.route('/iframe/success', methods=['GET'])
def iframe_success():
    """アイテム登録ビューをレンダリングする
    セッションに保存されているデータから画面表示に必要な情報を取得し、
    レンダリングする。

    Returns:
        str: アイテム登録ビュー
            render result of weko_workflow/item_login_success.html

    ---
    get:
        description: "render template"
        responses:
            200:
                description: "render_template"
                content:
                    text/html
    """
    files_thumbnail = None
    # get session value
    if not session.keys() >= {
        "itemlogin_id","itemlogin_activity","itemlogin_item",
        "itemlogin_steps","itemlogin_action_id","itemlogin_cur_step",
        "itemlogin_res_check","itemlogin_pid"}:
        current_app.logger.error("iframe_success: incorrected session value")
        return render_template("weko_theme/error.html",
                error="can not get data required for rendering")
    history = WorkActivityHistory()
    histories = history.get_activity_history_list(session['itemlogin_id'])
    activity = session['itemlogin_activity']
    item = session['itemlogin_item']
    steps = session['itemlogin_steps']
    action_id = session['itemlogin_action_id']
    cur_step = session['itemlogin_cur_step']
    res_check = session['itemlogin_res_check']
    pid = session['itemlogin_pid']
    if not (activity and steps and action_id and cur_step and histories):
        current_app.logger.error("iframe_success: incorrected session value")
        return render_template("weko_theme/error.html",
                error="can not get data required for rendering")
    if not (isinstance(res_check,int) and res_check in [0, 1]):
        current_app.logger.error("iframe_success: incorrected session value")
        return render_template("weko_theme/error.html",
                error="can not get data required for rendering")
    community_id = session.get('itemlogin_community_id')
    record = None
    files = []
    if item and item.get('pid') and 'value' in item['pid']:
        record, files = get_record_by_root_ver(item['pid']['value'])
        if not isinstance(files, list):
            current_app.logger.error("iframe_success: can not get files")
            return render_template("weko_theme/error.html",
                    error="can not get data required for rendering")
        files_thumbnail = get_thumbnails(files, None)
    else:
        if "itemlogin_record" not in session:
            current_app.logger.error("iframe_success: incorrected session value")
            return render_template("weko_theme/error.html",
                    error="can not get data required for rendering")
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
    if not action:
        current_app.logger.error("iframe_success: can not get action_detail")
        return render_template("weko_theme/error.html",
                error="can not get data required for rendering")
    action_endpoint = action.action_endpoint
    workflow = WorkFlow()
    workflow_detail = workflow.get_workflow_by_id(activity.workflow_id)
    if not workflow_detail:
        current_app.logger.error("views.iframe_success: can not get workflow_detail")
        return render_template("weko_theme/error.html",
                error="can not get data required for rendering")
    item_type_name = get_item_type_name(workflow_detail.itemtype_id)

    record_detail_alt = get_main_record_detail(activity.activity_id,
                                               activity)
    ctx.update(
        dict(
            record_org=record_detail_alt.get('record'),
            files_org=record_detail_alt.get('files'),
            thumbnails_org=record_detail_alt.get('files_thumbnail')
        )
    )

    form = FlaskForm(request.form)

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
                           form=form,
                           **ctx)


@workflow_blueprint.route('/activity/new', methods=['GET'])
@login_required
def new_activity():
    """New activity.
    Args:

    Returns:
        str: render result of weko_workflow/workflow_list.html
    ---
      get:
        description: Render the workflow list
        security:
        - login_required: []
        parameters:
          - name: community
            in: query
            description: community id
            schema:
              type: string
        responses:
          200:
            description: render result of weko_workflow/workflow_list.html
            content:
                text/html

    """
    workflow = WorkFlow()
    workflows = workflow.get_workflow_list()
    workflows = workflow.get_workflows_by_roles(workflows)
    ctx = {'community': None}
    community_id = ""
    if 'community' in request.args:
        comm = GetCommunity.get_community_by_id(request.args.get('community'))
        ctx = {'community': comm}
        if comm is not None:
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



@workflow_blueprint.route('/activity/init', methods=['POST'])
@login_required
def init_activity(json_data=None, community=None):
    """Return URL of workflow activity made from the request body.
    Args:

    Returns:
        dict: json data validated by ResponseMessageSchema.

    Raises:
        marshmallow.exceptions.ValidationError: if ResponseMessageSchema is invalid.

    ---
    post:
      description: "init activity"
      security:
        - login_required: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              ActivitySchema
            example: { "flow_id": 1,"workflow_id":1,"itemtype_id": 15}
      parameters:
        - in: query
          name: community
          description: community id
          schema:
            type: string
      responses:
        200:
          description: "success"
          content:
            application/json:
              schema:
                ResponseMessageSchema
              example: { "code": 0,"msg":"success","data": {"redirect": "/workflow/activity/detail/A-20220724-00008"}}
        400:
            description: "parameter error"
            content:
              application/json:
                schema:
                  ResponseMessageSchema
                example: { "code": -1,"msg":"parameter error"}
        500:
            description: "server error"
            content:
              application/json:
                schema:
                  ResponseMessageSchema
                example: { "code": -1,"msg":"server error"}
    """
    url = ''
    post_activity = None
    try:
        post_activity = ActivitySchema().load(json_data or request.get_json())
    except ValidationError as err:
        traceback.print_exc()
        res = ResponseMessageSchema().load({'code':-1,'msg':str(err)})
        return jsonify(res.data), 400

    if is_terms_of_use_only(post_activity.data["workflow_id"]):
        # if the workflow is terms_of_use_only(利用規約のみ) ,
        # do not create activity. redirect file download.
        file_name = post_activity.data["extra_info"]["file_name"]
        record_id = post_activity.data["extra_info"]["record_id"]
        url = _generate_download_url(record_id=record_id,file_name=file_name)
        res = ResponseMessageSchema().load({'code':1,'msg':'success','data':{'is_download':True, 'redirect': url}})
        return jsonify(res.data), 200

    activity = WorkActivity()
    community_id = request.args.get('community') or community
    try:
        if community_id is not None:
            rtn = activity.init_activity(post_activity.data, community_id)
        else:
            rtn = activity.init_activity(post_activity.data)
        if rtn is None:
            res = ResponseMessageSchema().load({'code':-1,'msg':'can not make activity_id'})
            return jsonify(res.data), 500
        url = url_for('weko_workflow.display_activity',
                      activity_id=rtn.activity_id)
        if community_id is not None and community_id != 'undefined':
            comm = GetCommunity.get_community_by_id(community_id)
            if comm is not None:
                url = url_for('weko_workflow.display_activity',
                          activity_id=rtn.activity_id, community=comm.id)
        db.session.commit()
    except SQLAlchemyError as ex:
        traceback.print_exc()
        current_app.logger.error("sqlalchemy error: {}".format(ex))
        db.session.rollback()
        res = ResponseMessageSchema().load({'code':-1,'msg':"sqlalchemy error: {}".format(ex)})
        return jsonify(res.data), 500
    except Exception as ex:
        traceback.print_exc()
        current_app.logger.error("Unexpected error: {}".format(ex))
        db.session.rollback()
        res = ResponseMessageSchema().load({'code':-1,'msg':"Unexpected error: {}".format(ex)})
        return jsonify(res.data),500

    res = ResponseMessageSchema().load({'code':0,'msg':'success','data':{'redirect': url}})

    return jsonify(res.data),200


def _generate_download_url(record_id :str ,file_name :str) -> str:
    """ generate file download url

    Args:
        str: record_id :recid
        str: file_name
    Returns:
        str: url
    """

    url:str = url_for(
            'invenio_records_ui.recid_files'
            ,pid_value=record_id, filename=file_name
        )
    current_app.logger.info('generated redirect url is ' + url)
    return url

@workflow_blueprint.route('/activity/list', methods=['GET'])
@login_required
def list_activity():
    """List activity."""
    activity = WorkActivity()
    getargs = request.args
    conditions = filter_all_condition(getargs)

    activities, maxpage, size, pages, name_param, _ = activity.get_activity_list(
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


@workflow_blueprint.route('/activity/init-guest', methods=['POST'])
def init_activity_guest():
    """Init workflow activity for guest user.
        Return URL of workflow activity made from the request body.
    Returns:
        dict: json data validated by ResponseMessageSchema.

    """
    post_data = request.get_json()

    password_for_download = ""
    if post_data.get('password_for_download'):
        pwd = post_data['password_for_download']
        password_for_download = hash_password(pwd)

    if is_terms_of_use_only(post_data["workflow_id"]):
        # if the workflow is terms_of_use_only(利用規約のみ) ,
        # do not create activity. redirect file download.
        file_name = post_data["file_name"]
        record_id = post_data["record_id"]
        url = _generate_download_url(record_id=record_id,file_name=file_name)
        res = ResponseMessageSchema().load({'code':1,'msg':'success','data':{'is_download':True, 'redirect': url}})
        return jsonify(res.data), 200

    if post_data.get('guest_mail'):
        try:
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
                    "password_for_download": password_for_download
                },
            }
            __, tmp_url = init_activity_for_guest_user(data)
            db.session.commit()
        except SQLAlchemyError as ex:
            current_app.logger.error("sqlalchemy error: {}".format(ex))
            db.session.rollback()
            return jsonify(msg='Cannot send mail')
        except BaseException as ex:
            current_app.logger.error('Unexpected error: {}'.format(ex))
            db.session.rollback()
            return jsonify(msg='Cannot send mail')

        if send_usage_application_mail_for_guest_user(
                post_data.get('guest_mail'), tmp_url, data.get('extra_info')):
            return jsonify(msg=_('Email is sent successfully.'))
    return jsonify(msg='Cannot send mail')


@workflow_blueprint.route('/activity/guest-user/<string:file_name>', methods=['GET'])
def display_guest_activity(file_name=""):
    """Display content application activity for guest user.
    @param file_name:File name
    @return:
    """
    return render_guest_workflow(file_name=file_name)


@workflow_blueprint.route('/activity/guest-user/recid/<string:record_id>', methods=['GET'])
def display_guest_activity_item_application(record_id=""):
    """Display item application activity for guest user.
    @param record_id:File name
    @return:
    """
    return render_guest_workflow(file_name='recid/' + record_id)


def render_guest_workflow(file_name=""):
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
    record_detail_alt = get_main_record_detail(activity_id,
                                               guest_activity.get('activity'))
    if record_detail_alt.get('record'):
        record_detail_alt['record']['is_guest'] = True

    guest_activity.update(
        dict(
            record_org=record_detail_alt.get('record'),
            files_org=record_detail_alt.get('files'),
            thumbnails_org=record_detail_alt.get('files_thumbnail'),
            record=record_detail_alt.get('record'),
            files=record_detail_alt.get('files'),
            files_thumbnail=record_detail_alt.get('files_thumbnail'),
            pid=record_detail_alt.get('pid', None),
            open_restricted=True,
        )
    )

    form = FlaskForm(request.form)

    return render_template(
        'weko_workflow/activity_detail.html',
        form=form,
        **guest_activity
    )


@workflow_blueprint.route('/verify_deletion/<string:activity_id>', methods=['GET'])
@login_required_customize
def verify_deletion(activity_id="0"):
    """Verify if the activity is deleted.

    Args:
        activity_id (str, optional): Activity ID. Defaults to "0".

    Returns:
        dict: JSON response with code, is_deleted, and for_delete status.
    """
    is_deleted = False
    for_delete = False
    activity = WorkActivity().get_activity_by_id(activity_id)
    if activity and activity.item_id:
        item_id = str(activity.item_id)

        recid = PersistentIdentifier.query.filter_by(
            pid_type='recid', object_type='rec', object_uuid=item_id
        ).one_or_none()
        if recid and recid.is_deleted():
            is_deleted = True

        for_delete = activity.flow_define.flow_type == WEKO_WORKFLOW_DELETION_FLOW_TYPE
    res = {'code': 200, 'is_deleted':is_deleted, 'for_delete':for_delete}

    return jsonify(res), 200

@workflow_blueprint.route('/activity/detail/<string:activity_id>',
                 methods=['GET', 'POST'])
@login_required_customize
def display_activity(activity_id="0", community_id=None):
    """各アクティビティのビューをレンダリングする

    各アクティビティの画面表示に必要な情報を取得し、
    レンダリングする。

    Args:
        activity_id (str, optional): 対象のアクティビティID.パスパラメータから取得. Defaults to '0'.

    Returns:
        str: render result of weko_workflow/activity_detail.html

    ---
    get:
        description: "render template"
        security:
            - login_required: []
        parameters:
            - in: path
                name: activity_id
                description: 対象のアクティビティID
                schema:
                    type: string
            - in: query
                name: community
                description: community id
                schema:
                    type: string
        responses:
            200:
                description: "render_template"
                content:
                    text/html
            404:
                description: "Exception"
                content:
                    text/html
    post:
        description: "render template"
        security:
            - login_required: []
        parameters:
            - in: path
              name: activity_id
              description: 対象のアクティビティID
              schema:
                type: string
            - in: query
                name: community
                description: community id
                schema:
                    type: string
        responses:
            200:
                description: "render_template"
                content:
                    text/html
            404:
                description: "Exception"
                content:
                    text/html
    """

    check_flg = type_null_check(activity_id, str)
    if not check_flg:
        current_app.logger.error("display_activity: argument error")
        return render_template("weko_theme/error.html",
                error="can not get data required for rendering")

    activity = WorkActivity()
    activity_detail = activity.get_activity_detail(activity_id)
    for_delete = activity_detail.flow_define.flow_type == WEKO_WORKFLOW_DELETION_FLOW_TYPE

    if "?" in activity_id:
        activity_id = activity_id.split("?")[0]

    action_endpoint, action_id, activity_detail, cur_action, histories, item, \
        steps, temporary_comment, workflow_detail, owner_id, shared_user_ids = \
        get_activity_display_info(activity_id)
    if any([s is None for s in [action_endpoint, action_id, activity_detail, cur_action, histories, steps, workflow_detail, owner_id, shared_user_ids]]):
        current_app.logger.error("display_activity: can not get activity display info")
        return render_template("weko_theme/error.html",
                error="can not get data required for rendering")

    # display_activity of Identifier grant
    identifier_setting = None
    if action_endpoint == 'identifier_grant' and item:
        community_id = request.args.get('community') or community_id
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

    cris_linkage = {'researchmap' : False}
    allow_multi_thumbnail = False
    application_item_type = False
    approval_record = []
    cur_step = action_endpoint
    contributors = []
    data_type = activity_detail.extra_info.get(
        'related_title') if activity_detail.extra_info else None
    endpoints = {}
    files = []
    files_thumbnail = []
    institute_position_list = WEKO_USERPROFILES_INSTITUTE_POSITION_LIST
    is_auto_set_index_action = True
    is_hidden_pubdate_value = False
    item_save_uri = ''
    item_type_name = get_item_type_name(workflow_detail.itemtype_id)
    json_schema = ''
    links = None
    need_billing_file = False
    need_file = False
    need_thumbnail = False
    position_list = WEKO_USERPROFILES_POSITION_LIST
    recid = None
    record = {}
    schema_form = ''
    show_autofill_metadata = True
    step_item_login_url = None
    term_and_condition_content = ''
    title = ""
    user_lock_key = "workflow_userlock_activity_{}".format(str(current_user.get_id()))
    if action_endpoint in ['item_login',
                           'item_login_application',
                           'file_upload']:
        if not activity.get_activity_by_id(activity_id):
            pass
        if activity.get_activity_by_id(activity_id).action_status != ActionStatusPolicy.ACTION_CANCELED:
            cur_locked_val = str(get_cache_data(user_lock_key)) or str()
            if not cur_locked_val:
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
            allow_multi_thumbnail ,cris_linkage \
            = item_login(item_type_id=workflow_detail.itemtype_id)
        if not step_item_login_url:
            current_app.logger.error("display_activity: can not get item")
            return render_template("weko_theme/error.html",
                    error="can not get data required for rendering")

        application_item_type = is_usage_application_item_type(activity_detail)

        if not record and item:
            record = item

        redis_connection = RedisConnection()
        sessionstore = redis_connection.connection(db=current_app.config['ACCOUNTS_SESSION_REDIS_DB_NO'], kv = True)


        if not (json_schema and schema_form):
            current_app.logger.error("display_activity: can not get json_schema,schema_form")
            return render_template("weko_theme/error.html",
                    error="can not get data required for rendering")

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
    if activity_detail and \
            activity_detail.item_id and \
            activity_detail.activity_status != ActivityStatusPolicy.ACTIVITY_CANCEL:
        try:
            if not for_delete:
                item_id = str(activity_detail.item_id)
                # get record data for the first time access to editing item screen
                recid, approval_record = get_pid_and_record(item_id)
                files, files_thumbnail = get_files_and_thumbnail(activity_id, item_id)

                links = base_factory(recid)

            # get contributors data
            # 一時保存データが無い場合は、登録済みアイテムから取得する
            if len(shared_user_ids) == 0:
                contributors = get_contributors(recid.pid_value)
            else:
                contributors = get_contributors(None, user_id_list_json=shared_user_ids, owner_id=owner_id)
        except PIDDeletedError:
            current_app.logger.error("PIDDeletedError: {}".format(sys.exc_info()))
            abort(404)
        except PIDDoesNotExistError:
            current_app.logger.error("PIDDoesNotExistError: {}".format(sys.exc_info()))
            abort(404)
        except Exception:
            current_app.logger.error("Unexpected error: {}".format(sys.exc_info()))
    else:
            # get contributors data
            # 登録済みアイテムが無い場合は、一時保存データから取得する
            contributors = get_contributors(None, user_id_list_json=shared_user_ids, owner_id=owner_id)

    res_check = check_authority_action(str(activity_id), int(action_id),
                                       is_auto_set_index_action,
                                       activity_detail.action_order)

    # getargs = request.args
    ctx = {'community': None}
    # community_id = ""
    if community_id is not None:
        comm = GetCommunity.get_community_by_id(community_id)
        ctx = {'community': comm}
        community_id = comm.id if comm is not None else ""
    # be use for index tree and comment page.
    if 'item_login' == action_endpoint or \
            'item_login_application' == action_endpoint or \
            'file_upload' == action_endpoint:
        cur_locked_val = str(get_cache_data(user_lock_key)) or str()
        if not cur_locked_val:
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

    user_id = current_user.id if hasattr(current_user , 'id') else None
    user_profile = None
    if user_id:
        from weko_user_profiles.views import get_user_profile_info
        user_profile={}
        user_profile['results'] = get_user_profile_info(int(user_id))
    from weko_records_ui.utils import get_list_licence
    from weko_theme.utils import get_design_layout

    # Get the design for widget rendering
    page, render_widgets = get_design_layout(
        community_id or current_app.config['WEKO_THEME_DEFAULT_COMMUNITY'])

    list_license = get_list_licence()
    if list_license is None or not isinstance(list_license, list):
        current_app.logger.error("display_activity: bad value for list_licences")
        return render_template("weko_theme/error.html",
                error="can not get data required for rendering")


    if action_endpoint == 'item_link' and recid:
        try:
            item_link = ItemLink.get_item_link_info(recid.pid_value)
            ctx['item_link'] = item_link
        except Exception:
            current_app.logger.error("Unexpected error: {}".format(sys.exc_info()))

    # Get item link info.
    try:
        if activity_detail.activity_status != ActivityStatusPolicy.ACTIVITY_CANCEL:
            record_detail_alt = get_main_record_detail(
                activity_id, activity_detail, action_endpoint, item,
                approval_record, files, files_thumbnail)
            if not record_detail_alt:
                current_app.logger.error("display_activity: bad value for record_detail_alt")
                return render_template("weko_theme/error.html",
                            error="can not get data required for rendering")

            ctx.update(
                dict(
                    record_org=record_detail_alt.get('record'),
                    files_org=record_detail_alt.get('files'),
                    thumbnails_org=record_detail_alt.get('files_thumbnail')
                )
            )
    except PIDDeletedError as ex:
        current_app.logger.info("Item is already deleted.")
        traceback.print_exc()

    # Get email approval key
    approval_email_key = get_approval_keys()

    # Get Auto fill data for Restricted Access Item Type.
    usage_data = get_usage_data(
        workflow_detail.itemtype_id, activity_detail, user_profile)
    ctx.update(usage_data)

    if approval_record and files:
        files = set_files_display_type(approval_record, files)

    # Add item link data for approval steps
    if approval_record and recid and action_endpoint in ['approval', 'approval_advisor', 'approval_guarantor', 'approval_administrator']:
        try:
            item_link_info = ItemLink.get_item_link_info(recid.pid_value)
        except Exception:
            item_link_info = None
            current_app.logger.error("Unexpected error: {}".format(sys.exc_info()))

        if item_link_info:
            approval_record["relation"] = item_link_info
        else:
            approval_record["relation"] = []

    ctx.update(
        dict(
            files_thumbnail=files_thumbnail,
            files=files,
            record=approval_record
        )
    )
    _id = None
    if recid:
        _id = re.sub("\.[0-9]+", "", recid.pid_value)

    form = FlaskForm(request.form)

    approval_pending = False
    if action_endpoint == 'approval' and workflow_detail.open_restricted:
        approval_pending = True

    application_approved = False
    url_to_item_to_apply_for = ''
    if getattr(activity_detail, 'extra_info', '') and activity_detail.extra_info and action_endpoint == 'end_action':
        applied_record_id = activity_detail.extra_info.get('record_id', -1)
        record = WekoRecord.get_record_by_pid(applied_record_id)
        if record:
            url_to_item_to_apply_for = urljoin(request.url_root, url_for(
                'invenio_records_ui.recid', pid_value=record.pid.pid_value))
            application_approved = True

    # Get Settings
    approval_preview = False
    enable_request_maillist = False
    is_no_content_item_application = False
    restricted_access_settings = AdminSettings.get(name="restricted_access", dict_to_object=False)
    if restricted_access_settings:
        if action_endpoint == 'approval' and restricted_access_settings.get("preview_workflow_approval_enable", False):
            approval_preview = workflow_detail.open_restricted
        enable_request_maillist = restricted_access_settings.get('display_request_form', False)
        item_application_settings = restricted_access_settings.get("item_application", {})
        is_no_content_item_application = item_application_settings.get("item_application_enable", False) \
            and workflow_detail.itemtype_id in item_application_settings.get("application_item_types", [])

    last_result :CRISLinkageResult = CRISLinkageResult().get_last( _id ,CRIS_Institutions.RM)
    last_linkage_result = _('Nothing')
    if last_result:
        last_linkage_result = _('Successful') if last_result.succeed == True else _('Failed') if last_result.succeed == False else _('Running')
        last_linkage_result = last_linkage_result + ' (' +last_result.updated.strftime('%Y-%m-%d') + ') '

    return render_template(
        'weko_workflow/activity_detail.html',
        action_endpoint_key=current_app.config.get(
            'WEKO_ITEMS_UI_ACTION_ENDPOINT_KEY'),
        action_id=action_id,
        activity_id=activity_detail.activity_id,
        activity=activity_detail,
        allow_multi_thumbnail=allow_multi_thumbnail,
        application_approved = application_approved,
        application_item_type=application_item_type,
        approval_email_key=approval_email_key,
        approval_pending = approval_pending,
        approval_preview=approval_preview,
        auto_fill_data_type=data_type,
        auto_fill_title=title,
        community_id=community_id,
        cur_step=cur_step,
        contributors=contributors,
        enable_contributor=current_app.config[
            'WEKO_WORKFLOW_ENABLE_CONTRIBUTOR'],
        enable_feedback_maillist=current_app.config[
            'WEKO_WORKFLOW_ENABLE_FEEDBACK_MAIL'],
        enable_request_maillist=enable_request_maillist,
        endpoints=endpoints,
        error_type='item_login_error',
        histories=histories,
        id=workflow_detail.itemtype_id,
        idf_grant_data=identifier_setting,
        idf_grant_input=IDENTIFIER_GRANT_LIST,
        idf_grant_method=current_app.config.get(
            'IDENTIFIER_GRANT_SUFFIX_METHOD', IDENTIFIER_GRANT_SUFFIX_METHOD),
        institute_position_list=institute_position_list,
        is_auto_set_index_action=is_auto_set_index_action,
        is_enable_item_name_link=is_enable_item_name_link(
            action_endpoint, item_type_name),
        is_hidden_pubdate=is_hidden_pubdate_value,
        is_show_autofill_metadata=show_autofill_metadata,
        is_no_content_item_application=is_no_content_item_application,
        item_save_uri=item_save_uri,
        item=item,
        jsonschema=json_schema,
        links=links,
        list_license=list_license,
        need_billing_file=need_billing_file,
        need_file=need_file,
        need_thumbnail=need_thumbnail,
        out_put_report_title=current_app.config[
            'WEKO_ITEMS_UI_OUTPUT_REGISTRATION_TITLE'],
        page=page,
        pid=recid,
        _id=_id,
        position_list=position_list,
        records=record,
        render_widgets=render_widgets,
        res_check=res_check,
        schemaform=schema_form,
        step_item_login_url=step_item_login_url,
        steps=steps,
        temporary_comment=temporary_comment,
        temporary_idf_grant_suffix=temporary_identifier_inputs,
        temporary_idf_grant=temporary_identifier_select,
        temporary_journal=temporary_journal,
        term_and_condition_content=term_and_condition_content,
        url_to_item_to_apply_for = url_to_item_to_apply_for,
        user_profile=user_profile,
        form=form,
        for_delete=for_delete,
        open_restricted=workflow_detail.open_restricted,
        researchmap_latest_linkage_result=last_linkage_result,
        cris_linkage=cris_linkage,
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

        is_set, is_allow, is_deny = validate_action_role_user(
            activity_id=kwargs.get('activity_id'),
            action_id=kwargs.get('action_id'),
            action_order=activity_detail.action_order
        )
        error_msg = _('Authorization required')
        if is_set:
            if is_deny:
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

    cur_user = current_user.get_id()
    if current_app.config['WEKO_WORKFLOW_ENABLE_CONTRIBUTOR'] and \
        action_id != _Action.query.filter_by(action_endpoint='approval').one().id:
        # item_registrationが完了していないactivityを再編集する場合、item_metadataテーブルにデータはない
        # その為、workflow_activityテーブルのtemp_dataを参照し、保存されている代理投稿者をチェックする
        im = ItemMetadata.query.filter_by(id=activity.item_id).one_or_none()
        if not im and activity.temp_data:
            temp_data = json.loads(activity.temp_data)
            if temp_data is not None:
                activity_shared_user_ids = temp_data.get('metainfo').get("shared_user_ids", [])
                activity_owner = temp_data.get('metainfo').get("owner", '-1')
                shared_user_ids = [ int(shared_user_ids_dict['user']) for shared_user_ids_dict in activity_shared_user_ids ]
                # if exist shared_user_ids or owner allow to access
                if int(cur_user) in shared_user_ids:
                    return 0
                if int(cur_user) == int(activity_owner):
                    return 0
        elif im:
            # Check if this activity has contributor equaling to current user
            metadata_shared_user_ids = im.json.get('shared_user_ids', [])
            metadata_weko_shared_ids = im.json.get('weko_shared_ids', [])
            metadata_owner = int(im.json.get('owner', '-1'))
            if int(cur_user) in metadata_shared_user_ids + metadata_weko_shared_ids:
                return 0
            if int(cur_user) == int(metadata_owner):
                return 0

    # Validation of action role(user)
    # If action_roles is set
    is_action_role_set, is_allow_action_role, is_deny_action_role = validate_action_role_user(activity_id, action_id, action_order)
    if is_action_role_set:
        # If allow roles(users) does not contain any role of current_user
        # or deny roles(users) contains any role of curren_user,
        # deny to access
        if is_deny_action_role:
            return 1
        # If allow roles(users) contains any role of current_user,
        # allow to access
        elif is_allow_action_role:
            return 0
    
    # Activity creator validation
    if contain_login_item_application:
        activity_action_obj = work.get_activity_action_comment(
            activity_id, action_id, action_order)
        if activity_action_obj and activity_action_obj.action_handler \
            and int(activity_action_obj.action_handler)==int(cur_user):
            return 0
    else:
        if activity.activity_login_user == int(cur_user):
            return 0

    # Otherwise, user has no permission
    return 1


@workflow_blueprint.route(
    '/activity/action/<string:activity_id>/<int:action_id>',
    methods=['POST'])
@login_required_customize
@check_authority
def next_action(activity_id='0', action_id=0, json_data=None):
    """そのアクションにおける処理を行い、アクティビティの状態を更新する。

    Args:
        activity_id (str, optional): 対象のアクティビティID.パスパラメータから取得. Defaults to '0'.
        action_id (int, optional): 現在のアクションID.パスパラメータから取得. Defaults to 0.

    Returns:
        object: 成否判定のコードとメッセージを含むjson dataをレスポンスボディにもつResponse.
            json data validated by ResponseMessageSchema

    Raises:
        marshmallow.exceptions.ValidationError: if ResponseMessageSchema is invalid.


    ---
    post:
        description: "next action"
        security:
            - login_required_customize: []
            - check_authority: []
        requestBody:
            required: false
            content:
                application/json:
                    schema:
                        ActionSchema, NextSchema, NextItemLinkSchema, NextIdentifierSchema, NextOAPolicySchema
                    example: {"action_version": "1.0.0", "commond": "this is test comment", "temporary_save": 0}
        parameters:
            - in: path
              name: activity_id
              description: 対象のアクティビティID
              schema:
                type: string
            - in: path
              name: action_id
              description: 現在のアクションID
              schema:
                type: int
        responses:
            200:
                description: "success"
                content:
                    application/json:
                        schema:
                            ResponseMessageSchema
            500:
                description: "server error"
                content:
                    application/json:
                        schema:
                            ResponseMessageSchema
                        example: {"code": -2, "msg": ""}
    """

    check_flg = type_null_check(activity_id, str)
    check_flg &= type_null_check(action_id, int)
    if not check_flg:
        current_app.logger.error("next_action: argument error")
        res = ResponseMessageSchema().load({"code":-1, "msg":"argument error"})
        return jsonify(res.data), 500

    action = Action().get_action_detail(action_id)
    action_endpoint = action.action_endpoint

    current_app.logger.debug('action_endpoint: {0}'.format(action_endpoint))

    work_activity = WorkActivity()
    history = WorkActivityHistory()
    activity_detail = work_activity.get_activity_detail(activity_id)
    if activity_detail is None:
        current_app.logger.error("next_action: can not get activity_detail")
        res = ResponseMessageSchema().load({"code":-1, "msg":"can not get activity detail"})
        return jsonify(res.data), 500
    for_delete = activity_detail.flow_define.flow_type == WEKO_WORKFLOW_DELETION_FLOW_TYPE
    action_order = activity_detail.action_order

    try:
        schema = get_schema_action(action_id)
        if schema is None:
            current_app.logger.error("next_action: can not get schema by action_id")
            res = ResponseMessageSchema().load({"code":-2, "msg":"can not get schema by action_id"})
            return jsonify(res.data), 500
        req_body = json_data or request.get_json() or {}
        if 'action_version' not in req_body:
            req_body['action_version'] = action.action_version
        schema_load = schema.load(req_body)
    except ValidationError as err:
        traceback.print_exc()
        current_app.logger.error("next_action: "+str(err))
        res = ResponseMessageSchema().load({"code":-1, "msg":str(err)})
        return jsonify(res.data), 500
    post_json = schema_load.data

    # A-20220808-00001
    # A-20220808-00001
    # A-20220808-00001
    #current_app.logger.error("next_action:activity_id:{}".format(activity_id))
    # 3
    # 5
    # 7
    #current_app.logger.error("next_action:action_id:{}".format(action_id))
    # {'commond': '', 'action_version': '1.0.1', 'temporary_save': 0}
    # {'commond': '', 'action_version': '1.0.1', 'temporary_save': 0, 'link_data': []}
    # {'identifier_grant': '1', 'identifier_grant_jalc_doi_suffix': '', 'identifier_grant_jalc_doi_link': 'https://doi.org/xxx/0000000059', 'identifier_grant_jalc_cr_doi_suffix': '', 'identifier_grant_jalc_cr_doi_link': 'https://doi.org/yyy/0000000059', 'identifier_grant_jalc_dc_doi_suffix': '', 'identifier_grant_jalc_dc_doi_link': 'https://doi.org/zzz/0000000059', 'identifier_grant_ndl_jalc_doi_suffix': '', 'identifier_grant_ndl_jalc_doi_link': 'https://doi.org/<Empty>/0000000059', 'identifier_grant_crni_link': '', 'action_version': '1.0.0', 'commond': '', 'temporary_save': 0}
    #current_app.logger.error("next_action:post_json:{}".format(post_json))
    activity = dict(
        activity_id=activity_id,
        action_id=action_id,
        action_version=post_json.get('action_version'),
        action_status=ActionStatusPolicy.ACTION_DONE,
        commond=post_json.get('commond'),
        action_order=action_order
    )

    if action_endpoint == 'begin_action':
        res = ResponseMessageSchema().load({"code":0, "msg":_("success")})
        return jsonify(res.data), 200

    if action_endpoint == 'end_action':
        work_activity.end_activity(activity)
        res = ResponseMessageSchema().load({"code":0,"msg":_("success")})
        return jsonify(res.data), 200
    if 'approval' == action_endpoint and post_json.get('temporary_save') == 0:
        update_approval_date(activity_detail)
    item_id = None
    recid = None
    deposit = None
    pid_without_ver = None
    current_pid = None
    if activity_detail and activity_detail.item_id:
        item_id = activity_detail.item_id
        try:
            current_pid = PersistentIdentifier.get_by_object(pid_type='recid',
                                                             object_type='rec',
                                                             object_uuid=item_id)
        except PIDDoesNotExistError as err:
            current_app.logger.error("can not get PersistentIdentifier")
            res = ResponseMessageSchema().load({"code":-1, "msg":"can not get PersistentIdentifier"})
            return jsonify(res.data), 500
        recid = get_record_identifier(current_pid.pid_value)
        deposit = WekoDeposit.get_record(item_id)
        if deposit:
            pid_without_ver = get_record_without_version(current_pid)
    if pid_without_ver is None:
        current_app.logger.error("next_action: can not get pid_without_ver")
        res = ResponseMessageSchema().load({"code":-1, "msg":"can not get pid_without_ver"})
        return jsonify(res.data), 500

    current_app.logger.debug("action_endpoint: {0}, current_pid: {1}, item_id: {2}".format(
        action_endpoint, current_pid, pid_without_ver.pid_value))
    record = WekoRecord.get_record_by_pid(pid_without_ver.pid_value)
    if record is None:
        current_app.logger.error("next_action: can not get record")
        res = ResponseMessageSchema().load({"code":-1, "msg":"can not get record"})
        return jsonify(res.data), 500
    current_app.logger.debug("record: {0}".format(record.pid_cnri))

    if action_endpoint in ['item_login', 'item_login_application'] and (record.pid_cnri is None) and current_app.config.get('WEKO_HANDLE_ALLOW_REGISTER_CNRI'):
        register_hdl(activity_id)

    flow = Flow()
    current_flow_action = flow.get_flow_action_detail(
        activity_detail.flow_define.flow_id, action_id, action_order)
    if current_flow_action is None:
        current_app.logger.error("next_action: can not get current_flow_action")
        res = ResponseMessageSchema().load({"code":-1, "msg":"can not get curretn_flow_action"})
        return jsonify(res.data), 500
    next_flow_action = flow.get_next_flow_action(
        activity_detail.flow_define.flow_id, action_id, action_order)
    if not isinstance(next_flow_action, list) or len(next_flow_action) <= 0:
        current_app.logger.error("next_action: can not get next_flow_action")
        res = ResponseMessageSchema().load({"code":-2,"msg":"can not get next_flow_action"})
        return jsonify(res.data), 500
    next_action_endpoint = next_flow_action[0].action.action_endpoint
    next_action_id = next_flow_action[0].action_id
    next_action_order = next_flow_action[
        0].action_order if action_order else None
    action_mails_setting = {"previous":
                            current_flow_action.send_mail_setting
                            if current_flow_action.send_mail_setting
                            else {},
                            "next": next_flow_action[0].send_mail_setting
                            if next_flow_action[0].send_mail_setting
                            else {},
                            "approval": False,
                            "reject": False}
    # Start to send mail
    if next_action_endpoint in ['approval' , 'end_action'] and post_json.get('temporary_save') == 0:
        next_action_detail = work_activity.get_activity_action_comment(
            activity_id, next_action_id,
            next_action_order)

        if next_action_detail is None:
            current_app.logger.error("next_action: can not get next_action_detail")
            res = ResponseMessageSchema().load({"code":-2, "msg":"can not get next_action_detail"})
            return jsonify(res.data), 500

        is_last_step = next_action_endpoint == 'end_action'
        # Only gen url file link at last approval step
        url_and_expired_date = {}
        if is_last_step:
            # Approve to file permission
            # 利用申請のWF時、申請されたファイルと、そのアイテム内の制限公開ファイルすべてにアクセス権を付与する
            permissions :List[FilePermission] = FilePermission.find_by_activity(activity_id)
            guest_activity :GuestActivity = GuestActivity.find_by_activity_id(activity_id)
            # validate file name
            extra_info: dict = deepcopy(activity_detail.extra_info)
            if extra_info and extra_info.get('file_name') and \
                not re.fullmatch(r'recid/\d+(?:\.\d+)?', extra_info.get('file_name')):
                if permissions and len(permissions) == 1:
                    # 利用申請(ログイン済)なら、WF作成時にFilePermissionが1レコードだけ作られている。
                    url_and_expired_date = grant_access_rights_to_all_open_restricted_files(activity_id,permissions[0] ,activity_detail)
                elif guest_activity and len(guest_activity) == 1:
                    # 利用申請(ゲスト)なら、WF作成時にFilePermissionが作られていないが、GuestActivityが作られている。
                    url_and_expired_date = grant_access_rights_to_all_open_restricted_files(activity_id,guest_activity[0] ,activity_detail)

            if not url_and_expired_date:
                url_and_expired_date = {}
        action_mails_setting['approval'] = True

        next_action_handler = next_action_detail.action_handler
        # in case of current action has action user
        if next_action_handler == -1:
            current_flow_action = FlowAction.query.filter_by(
                flow_id=activity_detail.flow_define.flow_id,
                action_id=next_action_id,
                action_order=next_action_order).one_or_none()
            if current_flow_action and current_flow_action.action_roles and current_flow_action.action_roles[0].action_request_mail:
                is_request_enabled = AdminSettings.get("restricted_access", dict_to_object=False) \
                    .get("display_request_form", False)
                #リクエスト機能がAdmin画面で無効化されている場合、メールは送信しない。
                if is_request_enabled :
                    next_action_handler = work_activity.get_user_ids_of_request_mails_by_activity_id(activity_id)
                else:
                    next_action_handler = []
            if current_flow_action and current_flow_action.action_roles and \
                    current_flow_action.action_roles[0].action_user:
                next_action_handler = current_flow_action.action_roles[
                    0].action_user
        # next_action_handlerがlist型ならfor文で複数回メール送信する。その際、handlerがロールを満たすか確認する。
        if type(next_action_handler) == list:
            for handler in next_action_handler:
                roles, users = work_activity.get_activity_action_role(activity_id, next_action_id,
                                                 current_flow_action.action_order)
                is_approver = work_activity.check_user_role_for_mail(handler, roles)
                if is_approver:
                    process_send_approval_mails(activity_detail, action_mails_setting, handler, url_and_expired_date)
        else:
            process_send_approval_mails(activity_detail, action_mails_setting, next_action_handler, url_and_expired_date)
    if current_app.config.get(
        'WEKO_WORKFLOW_ENABLE_AUTO_SEND_EMAIL') and \
        current_user.is_authenticated and \
        (not activity_detail.extra_info or not
            activity_detail.extra_info.get('guest_mail')):
        process_send_notification_mail(activity_detail, action_endpoint,
                                       next_action_endpoint, action_mails_setting)

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
        res = ResponseMessageSchema().load({"code":0, "msg":_("success")})
        return jsonify(res.data), 200
    elif post_json.get('journal'):
        work_activity.create_or_update_action_journal(
            activity_id=activity_id,
            action_id=action_id,
            journal=post_json.get('journal')
        )

    if action_endpoint == 'approval' and item_id and not for_delete:
        last_idt_setting = work_activity.get_action_identifier_grant(
            activity_id=activity_id,
            action_id=get_actionid('identifier_grant'))
        if not post_json.get('temporary_save') and last_idt_setting \
                and last_idt_setting.get('action_identifier_select') \
                and last_idt_setting.get('action_identifier_select') > 0:

            _pid = pid_without_ver.pid_value
            record_without_version = item_id
            if not recid:
                record_without_version = pid_without_ver.object_uuid

            current_app.logger.debug(
                'last_idt_setting: {0}'.format(last_idt_setting))
            saving_doi_pidstore(
                item_id,
                record_without_version,
                prepare_doi_link_workflow(_pid, last_idt_setting),
                int(last_idt_setting['action_identifier_select']))
        elif last_idt_setting \
                and last_idt_setting.get('action_identifier_select'):
            without_ver_identifier_handle = IdentifierHandle(item_id)
            if last_idt_setting.get('action_identifier_select') == -2:
                del_doi = without_ver_identifier_handle.delete_pidstore_doi()
                current_app.logger.debug(
                    'delete_pidstore_doi: {0}'.format(del_doi))
            elif last_idt_setting.get('action_identifier_select') == -3:
                without_ver_identifier_handle.remove_idt_registration_metadata()

        action_feedbackmail = work_activity.get_action_feedbackmail(
            activity_id=activity_id,
            action_id=current_app.config.get(
                "WEKO_WORKFLOW_ITEM_REGISTRATION_ACTION_ID", 3))
        activity_request_mail = work_activity.get_activity_request_mail(
            activity_id=activity_id)
        activity_item_application = work_activity.get_activity_item_application(
            activity_id=activity_id
        )
        if action_feedbackmail or activity_request_mail or activity_item_application:
            item_ids = [item_id]
            if not recid:
                if ".0" in current_pid.pid_value:
                    pv = PIDVersioning(child=pid_without_ver)
                    last_ver = PIDVersioning(parent=pv.parent,child=pid_without_ver).get_children(
                        pid_status=PIDStatus.REGISTERED
                    ).filter(PIDRelation.relation_type == 2).order_by(
                        PIDRelation.index.desc()).first()
                    if last_ver is None:
                        res = ResponseMessageSchema().load({"code":-1, "msg":"can not get last_ver"})
                        return jsonify(res.data), 500
                    item_ids.append(last_ver.object_uuid)
                else:
                    draft_pid = PersistentIdentifier.get(
                        'recid',
                        '{}.0'.format(pid_without_ver.pid_value)
                    )
                    item_ids.append(draft_pid.object_uuid)
                item_ids.append(pid_without_ver.object_uuid)

            if action_feedbackmail and action_feedbackmail.feedback_maillist:
                FeedbackMailList.update_by_list_item_id(
                    item_ids=item_ids,
                    feedback_maillist=action_feedbackmail.feedback_maillist
                )
            else:
                FeedbackMailList.delete_by_list_item_id(item_ids)

            enable_request_maillist = False
            enable_item_application = False
            restricted_access_settings = AdminSettings.get("restricted_access", dict_to_object=False)
            if restricted_access_settings:
                enable_request_maillist = restricted_access_settings.get("display_request_form", False)
                item_application_settings = restricted_access_settings.get("item_application", {})
                enable_item_application = item_application_settings.get("item_application_enable", False)
                application_item_types = item_application_settings.get("application_item_types", [])
                can_register_item_application = enable_item_application and (activity_detail.workflow.itemtype_id in application_item_types)

            if activity_request_mail and activity_request_mail.request_maillist and enable_request_maillist:
                RequestMailList.update_by_list_item_id(
                    item_ids=item_ids,
                    request_maillist=activity_request_mail.request_maillist
                )
            else:
                RequestMailList.delete_by_list_item_id(item_ids)

            if activity_item_application and activity_item_application.item_application and can_register_item_application:
                ItemApplication.update_by_list_item_id(
                    item_ids=item_ids,
                    item_application=activity_item_application.item_application
                )
            else:
                ItemApplication.delete_by_list_item_id(item_ids)

        deposit.update_request_mail()

    if action_endpoint == 'item_link' and item_id:

        item_link = ItemLink(current_pid.pid_value)
        relation_data = post_json.get('link_data') or []
        err = item_link.update(relation_data)
        if err:
            res = ResponseMessageSchema().load({"code":-1, "msg":_(err)})
            return jsonify(res.data), 500
        if post_json.get('temporary_save') == 1:
            work_activity.upt_activity_action_comment(
                activity_id=activity_id,
                action_id=action_id,
                comment=post_json.get('commond'),
                action_order=action_order
            )
            res = ResponseMessageSchema().load({"code":0,"msg":_("success")})
            return jsonify(res.data), 200

    # save pidstore_identifier to ItemsMetadata
    identifier_select = post_json.get('identifier_grant')
    if 'identifier_grant' == action_endpoint \
            and identifier_select is not None:
        # If is action identifier_grant, then save to to database
        identifier_grant = {
            'action_identifier_select': identifier_select,
            'action_identifier_jalc_doi': post_json.get(
                'identifier_grant_jalc_doi_suffix'),
            'action_identifier_jalc_cr_doi': post_json.get(
                'identifier_grant_jalc_cr_doi_suffix'),
            'action_identifier_jalc_dc_doi': post_json.get(
                'identifier_grant_jalc_dc_doi_suffix'),
            'action_identifier_ndl_jalc_doi': post_json.get(
                'identifier_grant_ndl_jalc_doi_suffix')
        }
        work_activity.create_or_update_action_identifier(
            activity_id=activity_id,
            action_id=action_id,
            identifier=identifier_grant
        )
        if post_json.get('temporary_save') == 1:
            res = ResponseMessageSchema().load({"code":0, "msg":_("success")})
            return jsonify(res.data), 200

        if identifier_select == IDENTIFIER_GRANT_SELECT_DICT['NotGrant']:
            if item_id != pid_without_ver.object_uuid:
                _old_idt = IdentifierHandle(pid_without_ver.object_uuid)
                _new_idt = IdentifierHandle(item_id)
                _old_v, _old_t = _old_idt.get_idt_registration_data()
                _new_v, _new_t = _new_idt.get_idt_registration_data()
                if not _old_v:
                    _new_idt.remove_idt_registration_metadata()
                elif _old_v != _new_v:
                    _new_idt.update_idt_registration_metadata(
                        _old_v,
                        _old_t)
            else:
                _identifier = IdentifierHandle(item_id)
                _value, _type = _identifier.get_idt_registration_data()

                if _value:
                    _identifier.remove_idt_registration_metadata()
        else:
            # If is action identifier_grant, then save to to database
            error_list = check_doi_validation_not_pass(
                item_id, activity_id, identifier_select)
            if isinstance(error_list, str):
                res = ResponseMessageSchema().load({"code":-1, "msg":_(error_list)})
                return jsonify(res.data), 500
            elif error_list:
                return previous_action(
                    activity_id=activity_id,
                    action_id=action_id,
                    req=-1)

            record_without_version = item_id
            if not recid:
                record_without_version = pid_without_ver.object_uuid
            saving_doi_pidstore(item_id, record_without_version, post_json,
                                int(identifier_select), True)
    elif 'identifier_grant' == action_endpoint \
            and not post_json.get('temporary_save'):
        _value, _type = IdentifierHandle(item_id).get_idt_registration_data()
        if _value and _type:
            error_list = check_doi_validation_not_pass(
                item_id, activity_id, IDENTIFIER_GRANT_SELECT_DICT[_type[0]],
                pid_without_ver.object_uuid)
            if isinstance(error_list, str):
                res = ResponseMessageSchema().load({"code":-1, "msg":_(error_list)})
                return jsonify(res.data), 500
            elif error_list:
                return previous_action(
                    activity_id=activity_id,
                    action_id=action_id,
                    req=-1)


    del_reject_flg = json_data.get('approval_reject', False) if json_data else False
    if next_action_endpoint == "end_action"  and for_delete and  del_reject_flg == False:
        parts = current_pid.pid_value.split('.')
        if len(parts) > 1 and parts[1] != '0':
            from weko_records_ui.utils import delete_version
            delete_version(current_pid.pid_value)
        else:
            from weko_records_ui.utils import soft_delete
            soft_delete(parts[0])
        db.session.commit()
        UserActivityLogger.info(
            operation="ITEM_DELETE",
            target_key=current_pid.pid_value
        )

    if for_delete and del_reject_flg:
        # skip action after thrown out action
        flow_detail = flow.get_flow_detail(activity_detail.flow_define.flow_id)
        skip_activity = activity.copy()
        skip_acts = [
            act for act in flow_detail.flow_actions
            if act.action.action_endpoint not in ('begin_action','end_action')
                and act.action_order > action_order
        ]
        for skip_act in skip_acts:
            skip_activity.update(
                action_id=skip_act.action_id,
                action_status=ActionStatusPolicy.ACTION_SKIPPED,
                action_order=skip_act.action_order
            )
            work_activity.upt_activity_action_status(
                activity_id=activity_id, action_id=skip_act.action_id,
                action_status=ActionStatusPolicy.ACTION_SKIPPED,
                action_order=skip_act.action_order
            )
            history.create_activity_history(skip_activity, skip_act.action_order)

        # thrown out action and set end action to next action
        activity.update(
            action_status=ActionStatusPolicy.ACTION_THROWN_OUT
        )

        last_flow_action = flow.get_last_flow_action(
            activity_detail.flow_define.flow_id)
        next_action_endpoint = last_flow_action.action.action_endpoint
        next_action_id = last_flow_action.action_id
        next_action_order = last_flow_action.action_order if action_order else None
        next_flow_action[0]=last_flow_action

    rtn = history.create_activity_history(activity, action_order)
    if not rtn:
        res = ResponseMessageSchema().load({"code":-1, "msg":_("error")})
        return jsonify(res.data), 500
    # next action
    flag = work_activity.upt_activity_action_status(
        activity_id=activity_id, action_id=action_id,
        action_status=ActionStatusPolicy.ACTION_THROWN_OUT \
            if del_reject_flg and for_delete else ActionStatusPolicy.ACTION_DONE,
        action_order=action_order
    )
    if not flag:
        res = ResponseMessageSchema().load({"code":-2, "msg":""})
        return jsonify(res.data), 500
    work_activity.upt_activity_action_comment(
        activity_id=activity_id,
        action_id=action_id,
        comment='',
        action_order=action_order
    )
    if for_delete and del_reject_flg:
        work_activity.notify_about_activity(activity_id, "deletion_rejected")

    if next_action_endpoint == "approval":
        if for_delete:
            work_activity.notify_about_activity(activity_id, "deletion_request")
        else:
            work_activity.notify_about_activity(activity_id, "request_approval")

    if next_action_endpoint == "end_action":
        if not for_delete:
            non_extract = work_activity.get_non_extract_files(activity_id)
            deposit.non_extract = non_extract
            new_item_id = handle_finish_workflow(
                deposit, current_pid, recid
            )
            if new_item_id is None:
                res = ResponseMessageSchema().load({"code":-1, "msg":_("error")})
                return jsonify(res.data), 500

            activity.update(
                action_id=next_action_id,
                action_version=next_flow_action[0].action_version,
                item_id=new_item_id,
                action_order=next_action_order
            )

            # Call signal to cris linkage
            temp_data = work_activity.get_activity_metadata(activity_id=activity_id)
            if temp_data:
                if json.loads(temp_data).get('cris_linkage',{}).get('researchmap' , False):
                    cris_researchmap_linkage_request.send(new_item_id)

            work_activity.end_activity(activity)

            if action_endpoint == "approval":
                work_activity.notify_about_activity(activity_id, "approved")
            else:
                work_activity.notify_about_activity(activity_id, "registered")

            # Call signal to push item data to ES.
            try:
                if '.' not in current_pid.pid_value and has_request_context():
                    user_id = activity_detail.activity_login_user if \
                        activity and activity_detail.activity_login_user else -1
                    item_created.send(
                        current_app._get_current_object(),
                        user_id=user_id,
                        item_id=current_pid,
                        item_title=activity_detail.title
                    )
            except BaseException:
                abort(500, 'MAPPING_ERROR')
        else:
            activity.update(
                action_id=next_action_id,
                action_version=next_flow_action[0].action_version,
                item_id=current_pid.object_uuid,
                action_status=ActionStatusPolicy.ACTION_DONE,
                action_order=next_action_order
            )
            work_activity.end_activity(activity)

            if action_endpoint == "approval" and not del_reject_flg:
                work_activity.notify_about_activity(activity_id, "deletion_approved")
    else:
        flag = work_activity.upt_activity_action(
            activity_id=activity_id, action_id=next_action_id,
            action_status=ActionStatusPolicy.ACTION_DOING,
            action_order=next_action_order)
        flag &= work_activity.upt_activity_action_status(
            activity_id=activity_id, action_id=next_action_id,
            action_status=ActionStatusPolicy.ACTION_DOING,
            action_order=next_action_order)
        if not flag:
            res = ResponseMessageSchema().load({"code":-2, "msg":""})
            return jsonify(res.data), 500

    # delete session value
    if session.get('itemlogin_id'):
        del session['itemlogin_id']
    if session.get('itemlogin_activity'):
        del session['itemlogin_activity']
    if session.get('itemlogin_item'):
        del session['itemlogin_item']
    if session.get('itemlogin_steps'):
        del session['itemlogin_steps']
    if session.get('itemlogin_action_id'):
        del session['itemlogin_action_id']
    if session.get('itemlogin_cur_step'):
        del session['itemlogin_cur_step']
    if session.get('itemlogin_record'):
        del session['itemlogin_record']
    if session.get('itemlogin_res_check'):
        del session['itemlogin_res_check']
    if session.get('itemlogin_pid'):
        del session['itemlogin_pid']
    if session.get('itemlogin_community_id'):
        del session['itemlogin_community_id']
    res = ResponseMessageSchema().load({"code":0, "msg":_("success")})
    return jsonify(res.data), 200


@workflow_blueprint.route(
    '/activity/action/<string:activity_id>/<int:action_id>'
    '/rejectOrReturn/<int:req>',
    methods=['POST'])
@login_required
@check_authority
def previous_action(activity_id='0', action_id=0, req=0):
    """reqに従い次のアクションを決定し、アクティビティの状態を更新する

    Args:
        activity_id (str, optional): 対象アクティビティID.パスパラメータから取得. Defaults to '0'.
        action_id (int, optional): 現在のアクションID.パスパラメータから取得. Defaults to 0.
        req (int, optional): 次のアクションの種類.パスパラメータから取得. Defaults to 0.
                             0:1つ前のフローアクション
                             -1: アイテム登録アクション
                             それ以外: 2つ目のアクション
    Returns:
        object: 成否判定のコードとメッセージを含むjson dataをレスポンスボディにもつResponse.
            json data validated by ResponseMessageSchema.

    Raises:
        marshmallow.exceptions.ValidationError: if ResponseMessageSchema is invalid.

    ---

    post:
        description: "previous_action"
        security:
            - login_required: []
            - check_authority: []
        requestBody:
            required: false
            content:
                application/json:
                    schema:
                        ActionSchema
                    example: {"action_version": "1.0.0", "commond": "test comment"}
        parameters:
            - in: path
              name: activity_id
              description: 対象のアクティビティID
              schema:
                type: string
            - in: path
              name: action_id
              description: 現在のアクションID
              schema:
                type: int
            - in: path
              name: req
              description: 次のアクションの種類.
                           0: 1つ前のフローアクション
                           -1: アイテム登録アクション
                           それ以外: 2つ目のアクション.
              schema:
                type: int
        responses:
            200:
                description: "success"
                content:
                    application/json:
                        schema:
                            ResponseMessageSchema
                        example: {"code": 0, "msg": "success"}
            500:
                description: "server error"
                content:
                    application/json:
                        schema:
                            ResponseMessageSchema
                        example: {"code": -1, "msg": "server error"}

    """

    check_flg = type_null_check(activity_id, str)
    check_flg &= type_null_check(action_id, int)
    check_flg &= type_null_check(req, int)
    if not check_flg:
        current_app.logger.error("previous_action: argument error")
        res = ResponseMessageSchema().load({"code":-1,"msg":"argument error"})
        return jsonify(res.data), 500
    try:
        action = Action().get_action_detail(action_id)
        req_body = request.get_json() or {}
        if 'action_version' not in req_body:
            req_body['action_version'] = action.action_version
        schema_load = ActionSchema().load(req_body)
    except ValidationError as err:
        current_app.logger.error("previous_action: "+str(err))
        res = ResponseMessageSchema().load({"code":-1, "msg":str(err)})
        return jsonify(res.data), 500
    post_data = schema_load.data
    # A-20220808-00001
    #current_app.logger.error("previous:activity_id:{}".format(activity_id))
    # 7
    #current_app.logger.error("previous:action_id:{}".format(action_id))
    # -1
    #current_app.logger.error("previous:req:{}".format(req))
    # :{'identifier_grant': '1', 'identifier_grant_jalc_doi_suffix': '', 'identifier_grant_jalc_doi_link': 'https://doi.org/xxx/0000000059', 'identifier_grant_jalc_cr_doi_suffix': '', 'identifier_grant_jalc_cr_doi_link': 'https://doi.org/yyy/0000000059', 'identifier_grant_jalc_dc_doi_suffix': '', 'identifier_grant_jalc_dc_doi_link': 'https://doi.org/zzz/0000000059', 'identifier_grant_ndl_jalc_doi_suffix': '', 'identifier_grant_ndl_jalc_doi_link': 'https://doi.org/<Empty>/0000000059', 'identifier_grant_crni_link': '', 'action_version': '1.0.0', 'commond': '', 'temporary_save': 0}
    #current_app.logger.error("previous:post_data:{}".format(post_data))
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
    if activity_detail is None:
        current_app.logger.error("previous_action: can not get activity_detail")
        res = ResponseMessageSchema().load({"code":-1, "msg":"can not get activity detail"})
        return jsonify(res.data), 500
    action_order = activity_detail.action_order

    for_delete = activity_detail.flow_define.flow_type == WEKO_WORKFLOW_DELETION_FLOW_TYPE
    if req == 0 and for_delete and action_id == 4:
        jsondata = {'approval_reject': 1}
        return next_action(
            activity_id=activity_id, action_id=action_id, json_data=jsondata
        )

    flow = Flow()
    rtn = history.create_activity_history(activity, action_order)
    if rtn is None:
        res = ResponseMessageSchema().load({"code":-1, "msg":_("error")})
        return jsonify(res.data), 500
    current_flow_action = flow.\
        get_flow_action_detail(
            activity_detail.flow_define.flow_id, action_id, action_order)
    if current_flow_action is None:
        current_app.logger.error("previous_action: can not get current_flow_action")
        res = ResponseMessageSchema().load({"code":-1, "msg":"can not get flow action detail"})
        return jsonify(res.data), 500
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
        current_app.logger.info("doi does not exists.")

    if req == -1:
        pre_action = flow.get_item_registration_flow_action(
            activity_detail.flow_define.flow_id)
    elif req == 0:
        pre_action = flow.get_previous_flow_action(
            activity_detail.flow_define.flow_id, action_id,
            action_order)
        # update action_identifier_select
        identifier_actionid = get_actionid('identifier_grant')
        identifier = work_activity.get_action_identifier_grant(
            activity_id,
            identifier_actionid)
        if identifier and identifier['action_identifier_select'] == -2:
            identifier['action_identifier_select'] = \
                current_app.config.get(
                    "WEKO_WORKFLOW_IDENTIFIER_GRANT_CAN_WITHDRAW", -1)
            work_activity.create_or_update_action_identifier(
                activity_id,
                identifier_actionid,
                identifier)
    else:
        pre_action = flow.get_next_flow_action(
            activity_detail.flow_define.flow_id, 1, 1)

    if pre_action and len(pre_action) > 0:
        previous_action_id = pre_action[0].action_id
        previous_action_order = pre_action[
            0].action_order if action_order else None
        if req == 0:
            flag = work_activity.upt_activity_action_status(
                activity_id=activity_id,
                action_id=action_id,
                action_status=ActionStatusPolicy.ACTION_THROWN_OUT,
                action_order=action_order)
        else:
            flag = work_activity.upt_activity_action_status(
                activity_id=activity_id, action_id=action_id,
                action_status=ActionStatusPolicy.ACTION_RETRY,
                action_order=action_order)
        flag &= work_activity.upt_activity_action_status(
            activity_id=activity_id, action_id=previous_action_id,
            action_status=ActionStatusPolicy.ACTION_DOING,
            action_order=previous_action_order)
        flag &= work_activity.upt_activity_action(
            activity_id=activity_id, action_id=previous_action_id,
            action_status=ActionStatusPolicy.ACTION_DOING,
            action_order=previous_action_order)
        if not flag:
            res = ResponseMessageSchema().load({'code':-2,'msg':""})
            return jsonify(res.data), 500
    res = ResponseMessageSchema().load({'code':0,'msg':_('success')})

    if action_id == 4:          # action_endpoint == "approval"
        work_activity.notify_about_activity(activity_id, "rejected")

    return jsonify(res.data), 200


@workflow_blueprint.route('/journal/list', methods=['GET'])
def get_journals():
    """Get journals."""
    key = request.values.get('key')
    if not key:
        return jsonify({})

    redis_connection = RedisConnection()
    datastore = redis_connection.connection(db=current_app.config['CACHE_REDIS_DB'], kv = True)

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


@workflow_blueprint.route('/journal/<string:method>/<string:value>', methods=['GET'])
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


@workflow_blueprint.route(
    '/activity/action/<string:activity_id>/<int:action_id>'
    '/cancel',
    methods=['POST'])
@login_required_customize
@check_authority
def cancel_action(activity_id='0', action_id=0):
    """アクティビティIDで与えられたアクティビティをキャンセルする
    Args:
        activity_id (str, optional): 対象アクティビティID.パスパラメータから取得. Defaults to '0'.
        action_id (int, optional): 現在のアクションID.パスパラメータから取得. Defaults to 0.

    Returns:
        object: 成否判定のコードとメッセージ、リダイレクト先のURLを含むjson dataをレスポンスボディにもつResponse.
              json data validated by ResponseMessageSchema

    Raises:
        marshmallow.exceptions.ValidationError: if ResponseMessageSchema is invalid.

    ---

    post:
        description: "cancel action"
        security:
            - login_required_customize: []
            - check_authority: []
        requestBody:
            required: false
            content:
                application/json:
                    schema:
                        CancelSchema
                    example: {"action_version": "1.0.0", "commond": "this is test comment", "pid_value":1}
        parameters:
            - in: path
              name: activity_id
              description: 対象のアクティビティID
              schema:
                type: string
            - in: path
              name: action_id
              description: 現在のアクションID
              schema:
                type: int
        responses:
            200:
                description: "success"
                content:
                    application/json:
                        schema:
                            ResponseMessageSchema
                        example: {"code": 0, "msg": _("success"), "data": {"redirect": "/workflow/activity/detail/1"}}
            500:
                description: "server error"
                content:
                    application/json:
                        schema:
                            ResponseMessageSchema
                        example: {"code": -1, "msg": "server error"}
    """

    check_flg = type_null_check(activity_id, str)
    check_flg &= type_null_check(action_id, int)
    if not check_flg:
        current_app.logger.error("cancel_action: argument error")
        res = ResponseMessageSchema().load({"code":-1, "msg":"argument error"})
        return jsonify(res.data), 500

    try:
        schema_load = CancelSchema().load(request.get_json())
    except ValidationError as err:
        current_app.logger.error("cancel_action: "+str(err))
        res = ResponseMessageSchema().load({"code":-1, "msg":str(err)})
        return jsonify(res.data), 500

    post_json = schema_load.data
    work_activity = WorkActivity()
    # Clear deposit
    activity_detail = work_activity.get_activity_by_id(activity_id)
    if activity_detail is None:
        current_app.logger.error("cancel_action: can not get activity_detail")
        res = ResponseMessageSchema().load({"code":-1, "msg":"can not get activity detail"})
        return jsonify(res.data), 500

    activity = dict(
        activity_id=activity_id,
        action_id=action_id,
        action_version=post_json.get('action_version'),
        action_status=ActionStatusPolicy.ACTION_CANCELED,
        commond=post_json.get('commond'),
        action_order=activity_detail.action_order
    )

    # Clear deposit
    cancel_item_id = activity_detail.item_id
    if cancel_item_id is None:
        pid_value = post_json.get('pid_value') if post_json.get(
            'pid_value') else get_pid_value_by_activity_detail(
            activity_detail)
        if pid_value:
            try:
                pid = PersistentIdentifier.get('recid', pid_value)
            except PIDDoesNotExistError:
                current_app.logger.error("cancel_action: can not get PersistIdentifier")
                res = ResponseMessageSchema().load({"code":-1, "msg":"can not get PersistIdentifier"})
                return jsonify(res.data), 500
            cancel_item_id = pid.object_uuid
    for_delete = activity_detail.flow_define.flow_type == WEKO_WORKFLOW_DELETION_FLOW_TYPE
    cancel_record = None
    if cancel_item_id:
        cancel_record = WekoDeposit.get_record(cancel_item_id)
    if (
        cancel_record is None
        or not (for_delete and not cancel_record.pid.pid_value.endswith('.0'))
    ):
        try:
            with db.session.begin_nested():
                if cancel_record:
                    pid_value = cancel_record.pid.pid_value
                    cancel_deposit = WekoDeposit(
                        cancel_record, cancel_record.model)

                    # Remove file and update size location.
                    if cancel_deposit.files and \
                            cancel_deposit.files.bucket:
                        remove_file_cancel_action(
                            cancel_deposit.files.bucket.id)

                    cancel_deposit.clear()
                    # Remove draft child
                    try:
                        cancel_pid = PersistentIdentifier.get_by_object(
                            pid_type='recid',
                            object_type='rec',
                            object_uuid=cancel_item_id)
                    except PIDDoesNotExistError:
                        current_app.logger.error("cancel_action: can not get PersistentIdentifier")
                        res = ResponseMessageSchema().load({"code":-1, "msg":"can not get PersistentIdentifier"})
                        return jsonify(res.data), 500
                    cancel_pv = PIDVersioning(child=cancel_pid)

                    if cancel_pv.exists:
                        parent_pid = deepcopy(cancel_pv.parent)
                        cancel_pv.remove_child(cancel_pid)
                        # rollback parent info
                        cancel_pv.parent.status = parent_pid.status
                        cancel_pv.parent.object_type = \
                            parent_pid.object_type
                        cancel_pv.parent.object_uuid = \
                            parent_pid.object_uuid

                pids = PersistentIdentifier.query.filter_by(
                    object_uuid=cancel_item_id)
                for p in pids:
                    if not p.pid_value.endswith('.0'):
                        p.status = PIDStatus.DELETED
            db.session.commit()
            # update item link info
            if cancel_record:
                if pid_value.endswith('.0'):
                    weko_record = WekoRecord.get_record_by_pid(pid_value)
                    if weko_record:
                        weko_record.update_item_link(pid_value.split('.')[0])
                else:
                    item_link = ItemLink(pid_value)
                    item_link.update([])
        except Exception:
            db.session.rollback()
            current_app.logger.error(
                'Unexpected error: {}'.format(sys.exc_info()))
            res = ResponseMessageSchema().load({"code":-1, "msg":str(sys.exc_info()[0])})
            return jsonify(res.data), 500

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
        res = ResponseMessageSchema().load({"code":-1, "msg":'Error! Cannot process quit activity!'})
        return jsonify(res.data), 500

    if session.get("guest_url"):
        url = session.get("guest_url")
    else:
        url = url_for('weko_workflow.display_activity',
                      activity_id=activity_id)

    if activity_detail.extra_info and \
            activity_detail.extra_info.get('guest_mail'):
        delete_guest_activity(activity_id)

    # Remove to file permission
    permissions = FilePermission.find_by_activity(activity_id)
    if permissions:
        for permission in permissions:
            FilePermission.delete_object(permission)

    #  not work
    cache_key = "workflow_userlock_activity_{}".format(str(current_user.get_id()))
    cur_locked_val = str(get_cache_data(cache_key)) or None
    if cur_locked_val and cur_locked_val==activity_id:
        update_cache_data(
            cache_key,
            cur_locked_val,
            1
        )
        delete_cache_data(cache_key)

    try:
        cache_key = 'workflow_locked_activity_{}'.format(activity_id)
        cur_locked_val = str(get_cache_data(cache_key)) or None
        if cur_locked_val:
            update_cache_data(
                cache_key,
                cur_locked_val,
                1
            )
            delete_cache_data(cache_key)
    except Exception as e:
        current_app.logger.error(traceback.format_exc())

    res = ResponseMessageSchema().load(
        {"code":0, "msg":_("success"),"data":{"redirect":url}}
        )
    return jsonify(res.data), 200


@workflow_blueprint.route(
    '/activity/detail/<string:activity_id>/<int:action_id>'
    '/withdraw',
    methods=['POST'])
@login_required_customize
@check_authority
def withdraw_confirm(activity_id='0', action_id=0):
    """ユーザー情報を確認し、リダイレクト先のURLを返す。
    Args:
        activity_id (str, optional): 対象アクティビティID.パスパラメータから取得. Defaults to '0'.
        action_id (int, optional): 現在のアクションID.パスパラメータから取得. Defaults to 0.

    Returns:
        object: ユーザー情報の確認結果とリダイレクト先URLのjson dataをレスポンスボディにもつResponse. validated by ResponseMessageSchema

    Raises:
        marshmallow.exceptions.ValidationError: if ResponseMessageSchema is invalid.

    ---
    post:
        description: "withdraw confirm"
        security:
            - login_required_customize: []
            - check_authority: []
        requestBody:
            required: false
            content:
                application/json:
                    schema:
                        PasswdSchema
                    example: {"passwd": "DELETE"}
        parameters:
            - in: path
              name: activity_id
              description: 対象のアクティビティID
              schema:
                type: string
            - in: path
              name: action_id
              description: 現在のアクションID
              schema:
                type: int
        responses:
            200:
                description: "success"
                content:
                    application/json:
                        schema:
                            ResponseMessageSchema
                        example:
                            {"code": 0, "msg": "success", "data": {"redirect":"/workflow/activity/detail/1"}}
            500:
                description: "server error"
                content:
                    application/json:
                        schema:
                            ResponseMessageSchema
                        example:
                            {"code": -1, "msg": "argument error"}}


    """
    try:
        check_flg = type_null_check(activity_id, str)
        check_flg &= type_null_check(action_id, int)
        if not check_flg:
            current_app.logger.error("withdraw_confirm: argument error")
            res = ResponseMessageSchema().load({"code":-1, "msg":"argument error"})
            return jsonify(res.data), 500

        try:
            schema_load = PasswdSchema().load(request.get_json())
        except ValidationError as err:
            current_app.logger.error("withdraw_confirm: "+str(err))
            res = ResponseMessageSchema().load({"code":-1, "msg":str(err)})
            return jsonify(res.data), 500
        post_json = schema_load.data

        password = post_json.get('passwd', None)
        # wekouser = ShibUser()
        if password == 'DELETE':
            activity = WorkActivity()
            identifier_actionid = get_actionid('identifier_grant')
            identifier = activity.get_action_identifier_grant(
                activity_id,
                identifier_actionid)
            identifier['action_identifier_select'] = \
                current_app.config.get(
                    "WEKO_WORKFLOW_IDENTIFIER_GRANT_IS_WITHDRAWING", -2)
            activity.create_or_update_action_identifier(
                activity_id,
                identifier_actionid,
                identifier)

            if session.get("guest_url"):
                url = session.get("guest_url")
            else:
                url = url_for('weko_workflow.display_activity',
                              activity_id=activity_id)
            res = ResponseMessageSchema().load({"code":0, "msg": _("success"), "data": {"redirect": url}})
            return jsonify(res.data), 200
        else:
            res = ResponseMessageSchema().load({"code":-1, "msg":_('Invalid password')})
            return jsonify(res.data), 500
    except ValueError:
        current_app.logger.error("withdraw_confirm: Unexpected error: {}".format(sys.exc_info()))
    res = ResponseMessageSchema().load({"code":-1, "msg":_('Error!')})
    return jsonify(res.data), 500


@workflow_blueprint.route('/findDOI', methods=['POST'])
@login_required
def find_doi():
    """Next action."""
    doi_link = request.get_json() or {}
    return jsonify(check_existed_doi(doi_link.get('doi_link')))


@workflow_blueprint.route(
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
    except Exception:
        current_app.logger.error("Unexpected error: {}".format(sys.exc_info()))
    return jsonify(code=-1, msg=_('Error'))


@workflow_blueprint.route(
    '/save_request_maillist/<string:activity_id>/<int:action_id>',
    methods=['POST'])
@login_required
@check_authority
def save_request_maillist(activity_id='0', action_id='0'):
    """Save request_mail's list to Activity History models.

    :return:
    """
    try:
        if request.headers['Content-Type'] != 'application/json':
            """Check header of request"""
            return jsonify(code=-1, msg=_('Header Error'))

        request_body = request.get_json(force=True)
        request_maillist = request_body.get('request_maillist', [])
        is_display_request_button = request_body.get('is_display_request_button', False)

        work_activity = WorkActivity()
        work_activity.create_or_update_activity_request_mail(
            activity_id=activity_id,
            request_maillist=request_maillist,
            is_display_request_button=is_display_request_button
        )
        return jsonify(code=0, msg=_('Success'))
    except Exception:
        current_app.logger.exception("Unexpected error occured.")
    return jsonify(code=-1, msg=_('Error'))


@workflow_blueprint.route(
    '/save_item_application/<string:activity_id>/<int:action_id>',
    methods=['POST'])
@login_required
@check_authority
def save_item_application(activity_id='0', action_id='0'):

    try:
        if request.headers['Content-Type'] != 'application/json':
            """Check header of request"""
            return jsonify(code=-1, msg=_('Header Error'))

        request_body = request.get_json(force=True)
        workflow_for_item_application = request_body.get('workflow_for_item_application', '')
        terms_without_contents = request_body.get('terms_without_contents', '')
        is_display_item_application_button = request_body.get('is_display_item_application_button', False)
        terms_description_without_contents =request_body.get('terms_description_without_contents', '')
        if terms_description_without_contents:
            item_application = {
                "workflow" : workflow_for_item_application,
                "terms" : terms_without_contents,
                "termsDescription" : terms_description_without_contents
            }
        else:
            item_application = {
                "workflow" : workflow_for_item_application,
                "terms" : terms_without_contents
            }
        work_activity = WorkActivity()
        work_activity.create_or_update_activity_item_application(
            activity_id=activity_id,
            item_application=item_application,
            is_display_item_application_button= is_display_item_application_button
        )
        return jsonify(code=0, msg=_('Success'))
    except Exception:
        current_app.logger.exception("Unexpected error occured.")
    return jsonify(code=-1, msg=_('Error'))


@workflow_blueprint.route('/get_feedback_maillist/<string:activity_id>',
                 methods=['GET'])
@login_required
def get_feedback_maillist(activity_id='0'):
    """アクティビティに設定されているフィードバックメール送信先の情報を取得して返す

    Args:
       activity_id (str, optional): 対象のアクティビティID.パスパラメータから取得. Defaults to '0'.

    Returns:
        object: 設定されているフィードバックメール送信先を示すResponse
               json data validated by ResponseMessageSchema or GetFeedbackMailListSchema

    Raises:
        marshmallow.exceptions.ValidationError: if ResponseMessageSchema is invalid.
    ---
    get:
        description: "get feedback maillist"
        security:
            - login_required: []
        responses:
            200:
                description: "success"
                content:
                    application/json:
                        schema:
                            GetFeedbackMailListSchema
                        example: {"code":1,"msg":_('Success'),"data":mail_list}

            400:
                description: "arguments error"
                content:
                    application/json:
                        schema:
                            ResponseMessageSchema
                        example: {"code": -1, "msg": "arguments error"}
    """
    check_flg = type_null_check(activity_id, str)
    if not check_flg:
        current_app.logger.error("get_feedback_maillist: argument error")
        res = ResponseMessageSchema().load({"code":-1, "msg":"arguments error"})
        return jsonify(res.data), 400
    try:
        work_activity = WorkActivity()
        action_feedbackmail = work_activity.get_action_feedbackmail(
            activity_id=activity_id,
            action_id=current_app.config.get(
                "WEKO_WORKFLOW_ITEM_REGISTRATION_ACTION_ID", 3))
        if action_feedbackmail:
            mail_list = action_feedbackmail.feedback_maillist
            if not isinstance(mail_list, list):
                res = ResponseMessageSchema().load({"code":-1,"msg":"mail_list is not list"})
                return jsonify(res.data), 400
            temp_list = []
            added_user = []
            for mail in mail_list.copy():
                aid = mail.get('author_id')
                if aid:
                    mail_list.remove(mail)
                    if aid not in added_user:
                        emails = Authors.get_emails_by_id(aid)
                        temp_list += [
                            {'email': e, 'author_id': mail.get('author_id')}
                            for e in emails
                        ]
                        added_user.append(aid)
            mail_list += temp_list
            res = GetFeedbackMailListSchema().load({'code':1,'msg':_('Success'),'data':mail_list})
            return jsonify(res.data), 200
        else:
            res = ResponseMessageSchema().load({'code':0,'msg':'Empty!'})
            return jsonify(res.data), 200
    except Exception:
        current_app.logger.error("Unexpected error: {}".format(sys.exc_info()))
    res = ResponseMessageSchema().load({'code':-1,'msg':_('Error')})
    return jsonify(res.data), 400


@workflow_blueprint.route('/get_request_maillist/<string:activity_id>', methods=['GET'])
@login_required
def get_request_maillist(activity_id='0'):
    """アクティビティに設定されているリクエストメール送信先の情報を取得して返す

    Args:
       activity_id (str, optional): 対象のアクティビティID.パスパラメータから取得. Defaults to '0'.

    Returns:
        object: 設定されているリクエストメール送信先を示すResponse
               json data validated by ResponseMessageSchema or GetRequestMailListSchema

    Raises:
        marshmallow.exceptions.ValidationError: if ResponseMessageSchema is invalid.
    ---
    get:
        description: "get request maillist"
        security:
            - login_required: []
        responses:
            200:
                description: "success"
                content:
                    application/json:
                        schema:
                            GetRequestMailListSchema
                        example: {"code":1,"msg":_('Success'),"data":mail_list}
            400:
                description: "arguments error"
                content:
                    application/json:
                        schema:
                            ResponseMessageSchema
                        example: {"code": -1, "msg": "arguments error"}
    """
    check_flg = type_null_check(activity_id, str)
    if not check_flg:
        current_app.logger.error("get_request_maillist: argument error")
        res = ResponseMessageSchema().load({"code":-1, "msg":"arguments error"})
        return jsonify(res.data), 400
    try:
        activity_request_mail = WorkActivity().get_activity_request_mail(
            activity_id=activity_id)
        if activity_request_mail:
            request_mail_list = activity_request_mail.request_maillist
            if not isinstance(request_mail_list, list):
                res = ResponseMessageSchema().load({"code":-1,"msg":"mail_list is not list"})
                return jsonify(res.data), 400
            temp_list = []
            added_user = []
            for mail in request_mail_list.copy():
                aid = mail.get('author_id')
                if aid:
                    request_mail_list.remove(mail)
                    if aid not in added_user:
                        emails = Authors.get_emails_by_id(aid)
                        temp_list += [
                            {'email': e, 'author_id': mail.get('author_id')}
                            for e in emails
                        ]
                        added_user.append(aid)
            request_mail_list += temp_list
            res = GetRequestMailListSchema().load({
                'code':1,
                'msg':_('Success'),
                'request_maillist': request_mail_list,
                'is_display_request_button': activity_request_mail.display_request_button
            })
            return jsonify(res.data), 200
        else:
            res = ResponseMessageSchema().load({'code':0,'msg':'Empty!'})
            return jsonify(res.data), 200
    except Exception:
        current_app.logger.exception("Unexpected error:")
    res = ResponseMessageSchema().load({'code':-1,'msg':_('Error')})
    return jsonify(res.data), 400


@workflow_blueprint.route('/activity/unlocks/<string:activity_id>',methods=["POST"])
@login_required
def unlocks_activity(activity_id="0"):
    data = json.loads(request.data.decode("utf-8"))
    msg_lock = None
    if data.get("locked_value") != 0:
        msg_lock = delete_lock_activity_cache(activity_id, data)
    msg_userlock = delete_user_lock_activity_cache(activity_id, data)
    res = {"code":200, "msg_lock":msg_lock,"msg_userlock":msg_userlock}
    return jsonify(res), 200

@workflow_blueprint.route('/activity/user_lock', methods=["GET"])
@login_required
def is_user_locked():
    cache_key = "workflow_userlock_activity_{}".format(str(current_user.get_id()))
    cur_locked_val = str(get_cache_data(cache_key)) or str()


    if cur_locked_val:
        work_activity = WorkActivity()
        act = work_activity.get_activity_by_id(cur_locked_val)
        if act is None or act.activity_status in [ActivityStatusPolicy.ACTIVITY_CANCEL,ActivityStatusPolicy.ACTIVITY_FORCE_END,ActivityStatusPolicy.ACTIVITY_FINALLY]:
            is_open = False
        else:
            is_open = True
    else:
        is_open=False

    res = {"is_open": is_open, "activity_id": cur_locked_val or ""}
    return jsonify(res), 200

@workflow_blueprint.route('/activity/user_lock/<string:activity_id>', methods=["POST"])
@login_required
def user_lock_activity(activity_id="0"):
    """アクティビティの操作者を確認し、そのユーザーが他にアクティビティを開いている場合ロックする

    Args:
        activity_id (str, optional): 対象アクティビティID.パスパラメータから取得. Defaults to '0'.

    Result:
        object: アクティビティの状態を示すjson data

    ---
    post:
        description: "user lock activity"
        security:
            - login_required: []
        parameters:
            - in: path
                name: activity_id
                description: 対象のアクティビティID
                schema:
                    type: string
        responses:
            200:
                description: "success or locked"
                content:
                    application/json:
                        example:
                            {"code":200, "msg":"Success", "err": "","locked_by_email": "example@example.org"}
    """
    validate_csrf_header(request)
    cache_key = "workflow_userlock_activity_{}".format(str(current_user.get_id()))
    timeout = current_app.permanent_session_lifetime
    cur_locked_val = str(get_cache_data(cache_key)) or str()
    err = ""
    if cur_locked_val:
        err = _("Opened")
    else:
        work_activity = WorkActivity()
        act = work_activity.get_activity_by_id(activity_id)
        if act is None or act.activity_status in [ActivityStatusPolicy.ACTIVITY_BEGIN,ActivityStatusPolicy.ACTIVITY_MAKING]:
            update_cache_data(
                cache_key,
                activity_id,
                timeout
            )
        # elif cur_locked_val==activity_id:
        #     delete_cache_data(cache_key)

    res = {"code":200,"msg": "" if err else _("Success"),"err": err or "", "activity_id": cur_locked_val}
    return jsonify(res), 200

@workflow_blueprint.route('/activity/user_unlock/<string:activity_id>', methods=["POST"])
@login_required
def user_unlock_activity(activity_id="0"):
    """キャッシュデータを削除することによりロックを解除する
    そのアクティビティがユーザーロックを受けていない場合のみ解除
    Args:
        activity_id (str, optional): 対象のアクティビティID.パスパラメータから取得.. Defaults to "0".

    Returns:
        object: ロック解除が出来たかを示すResponse

    ---
    post:
        description: "user unlock activity"
        security:
            - login_required: []
        requestBody:
            required: false
            content:
                text/plain:
                    example: '{"is_opened": true}'
        parameters:
            - in: path
              name: activity_id
              description: 対象のアクティビティID
              schema:
                type: string
        responses:
            200:
                description: "success"
                content:
                    application/json:
                        schema:
                            ResponseMessageSchema
                        example: {"code":200,"msg":"Unlock success"}
    """
    data = json.loads(request.data.decode("utf-8"))
    msg = delete_user_lock_activity_cache(activity_id, data)
    res = {"code":200, "msg":msg}
    return jsonify(res), 200

@workflow_blueprint.route('/get_item_application/<string:activity_id>', methods=['GET'])
@login_required
def get_item_application(activity_id='0'):
    check_flg = type_null_check(activity_id, str)
    if not check_flg:
        current_app.logger.error("get_item_application: argument error")
        res = ResponseMessageSchema().load({"code":-1, "msg":"arguments error"})
        return jsonify(res.data), 400
    try:
        item_application_and_button = WorkActivity().get_activity_item_application(
            activity_id=activity_id)
        if item_application_and_button:
            res = GetItemApplicationSchema().load({
                'code':1,
                'msg':_('Success'),
                'item_application': item_application_and_button.item_application,
                'is_display_item_application_button': item_application_and_button.display_item_application_button
            })
            return jsonify(res.data), 200
        else:
            res = ResponseMessageSchema().load({'code':0,'msg':'Empty!'})
            return jsonify(res.data), 200
    except Exception:
        current_app.logger.exception("Unexpected error:")
    res = ResponseMessageSchema().load({'code':-1,'msg':_('Error')})
    return jsonify(res.data), 400

@workflow_blueprint.route('/activity/lock/<string:activity_id>', methods=['POST'])
@login_required
def lock_activity(activity_id="0"):
    """アクティビティの操作者を確認し、操作可能者以外の場合ロックする

    ワークフローに関するアクティビティの操作が、操作可能者以外により
    行われないようセッション管理し、ロックする

    Args:
        activity_id (str, optional): 対象アクティビティID.パスパラメータから取得. Defaults to '0'.

    Returns:
        object: アクティビティの状態を示すjson dataをレスポンスボディに含むResponse.json data validated by ResponseMessageSchema
    Raises:
        marshmallow.exceptions.ValidationError: if ResponseMessageSchema is invalid.

    ---
    post:
        description: "lock activity"
        security:
            - login_required: []
        requestBody:
            required: false
            content:
                application/json:
                    schema:
                        LockSchema
                    example:
                        {'locked_value': '1-1661748792565'}
        parameters:
            - in: path
              name: activity_id
              description: 対象のアクティビティID
              schema:
                type: string
        responses:
            200:
                description: "success"
                content:
                    application/json:
                        schema:
                            ResponseLockSchema
                        example:
                            {"code": 200, "msg": "Success", "err": "",
                            "locked_value": "1-1661748792565", "locked_by_email": "example@example.org",
                            "locked_by_username": ""}
            500:
                description: "server error"
                content:
                    application/json:
                        schema:
                            ResponseMessageSchema
                        example:
                            {"code":-1,"msg":"argument error"}
    """
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


    #validate_csrf_header(request)

    check_flg = type_null_check(activity_id, str)
    if not check_flg:
        current_app.logger.error("lock_activity: argument error")
        res = ResponseMessageSchema().load({"code":-1, "msg":"argument error"})
        return jsonify(res.data), 500

    cache_key = 'workflow_locked_activity_{}'.format(activity_id)
    timeout = current_app.permanent_session_lifetime
    try:
        schema_load = LockSchema().load(request.form.to_dict())
    except ValidationError as err:
        current_app.logger.error("lock_activity: "+str(err))
        res = ResponseMessageSchema().load({"code":-1, "msg":str(err)})
        return jsonify(res.data), 500

    data = schema_load.data
    locked_value = data.get('locked_value')
    cur_locked_val = str(get_cache_data(cache_key)) or str()
    err = ''
    if cur_locked_val and not is_approval_user(activity_id):
        if locked_value != cur_locked_val:
            locked_value = cur_locked_val
            err = _('Locked')
        else:
            work_activity = WorkActivity()
            act = work_activity.get_activity_by_id(activity_id)
            if act is None or act.activity_status in [ActivityStatusPolicy.ACTIVITY_BEGIN,ActivityStatusPolicy.ACTIVITY_MAKING]:
                update_cache_data(
                    cache_key,
                    locked_value,
                    timeout
                )
    else:
        # create new lock cache
        locked_value = str(current_user.get_id()) + '-' + \
            str(int(datetime.timestamp(datetime.now()) * 10 ** 3))
        work_activity = WorkActivity()
        act = work_activity.get_activity_by_id(activity_id)
        if act is None or act.activity_status in [ActivityStatusPolicy.ACTIVITY_BEGIN,ActivityStatusPolicy.ACTIVITY_MAKING]:
            update_cache_data(
                cache_key,
                locked_value,
                timeout
            )

    locked_by_email, locked_by_username = get_account_info(
        locked_value.split('-')[0])
    if locked_by_email is None or locked_by_username is None:
        current_app.logger.error("lock_activity: can not get locked_by_email or locked_by_username")
        res = ResponseMessageSchema().load({"code":-1, "msg":"can not get user locked"})
        return jsonify(res.data), 500
    res = ResponseLockSchema().load({"code":200,"msg":"" if err else _("Success"),"err":err or "",
                                     "locked_value":locked_value,"locked_by_email":locked_by_email,
                                     "locked_by_username":locked_by_username})
    return jsonify(res.data), 200


@workflow_blueprint.route('/activity/unlock/<string:activity_id>', methods=['POST'])
@login_required
def unlock_activity(activity_id="0"):
    """キャッシュデータを削除することによりロックを解除する。

    Args:
        activity_id (str, optional): 対象のアクティビティID.パスパラメータから取得. Defaults to '0'.

    Returns:
        object: ロック解除が出来たかを示すResponse
               json data validated by ResponseMessageSchema or ResponseUnlockSchema

    Raises:
        marshmallow.exceptions.ValidationError: if ResponseMessageSchema is invalid.
    ---
    post:
        description: "unlock activity"
        security:
            - login_required: []
        requestBody:
            required: false
            content:
                text/plain:
                    schema:
                        LockedValueSchema
                    example: '{"locked_value":"1-1661748792565"}'
        parameters:
            - in: path
              name: activity_id
              description: 対象のアクティビティID
              schema:
                type: string
        responses:
            200:
                description: "success"
                content:
                    application/json:
                        schema:
                            ResponseMessageSchema
                        example: {"code":200,"msg":"Unlock success"}
            400:
                description: "arguments error"
                content:
                    application/json:
                        schema:
                            ResponseMessageSchema
                        example: {"code": -1, "msg": "arguments error"}
    """
    check_flg = type_null_check(activity_id, str)
    if not check_flg:
        current_app.logger.error("unlock_activity: argument error")
        res = ResponseMessageSchema().load({"code":-1, "msg":"arguments error"})
        return jsonify(res.data), 400
    try:
        data = LockedValueSchema().load(json.loads(request.data.decode("utf-8")))
    except ValidationError as err:
        res = ResponseMessageSchema().load({'code':-1, 'msg':str(err)})
        return jsonify(res.data), 400
    msg = delete_lock_activity_cache(activity_id, data.data)
    res = ResponseUnlockSchema().load({'code':200,'msg':msg or _('Not unlock')})
    return jsonify(res.data), 200


@workflow_blueprint.route('/check_approval/<string:activity_id>', methods=['GET'])
@login_required
def check_approval(activity_id='0'):
    """アクティビティに対して承認の確認が必要であるかの判定をして、その結果を返す

    Args:
        activity_id (str, optional): 対象のアクティビティID.パスパラメータから取得. Defaults to '0'.

    Returns:
        object: 承認の確認が必要かの判定結果を示すResponse
               json data validated by ResponseMessageSchema or CheckApprovalSchema

    Raises:
        marshmallow.exceptions.ValidationError: if ResponseMessageSchema is invalid.
    ---
    get:
        description: "check approval"
        security:
            - login_required: []
        responses:
            200:
                description: "success"
                content:
                    application/json:
                        schema:
                            CheckApprovalSchema
                        example: {"check_handle": -1, "check_continue": -1, "error": 1 }
            400:
                description: "arguments error"
                content:
                    application/json:
                        schema:
                            ResponseMessageSchema
                        example: {"code": -1, "msg": "arguments error"}
    """
    check_flg = type_null_check(activity_id, str)
    if not check_flg:
        current_app.logger.error("check_approval: argument error")
        res = ResponseMessageSchema().load({"code":-1, "msg":"arguments error"})
        return jsonify(res.data), 400
    response = {
        'check_handle': -1,
        'check_continue': -1,
        'error': 1
    }
    try:
        response = check_continue(response, activity_id)
    except Exception:
        current_app.logger.error("Unexpected error: {}".format(sys.exc_info()))
        response['error'] = -1
    res = CheckApprovalSchema().load(response)
    return jsonify(res.data), 200


@workflow_blueprint.route('/send_mail/<string:activity_id>/<string:mail_id>',
                 methods=['POST'])
@login_required
def send_mail(activity_id='0', mail_id=''):
    """
    Sends an email for the specified activity using the given mail id.

    This route is accessed via a POST request and requires the user to be logged in.

    Args:
        activity_id (str): The ID of the activity.
        mail_id (str): The ID of the mail template.

    Returns:
        Response: JSON response indicating the success or failure of sending the mail.

    Raises:
        None
    """
    try:
        work_activity = WorkActivity()
        activity_detail = work_activity.get_activity_detail(activity_id)
        if current_app.config.get('WEKO_WORKFLOW_ENABLE_AUTO_SEND_EMAIL'):
            process_send_reminder_mail(activity_detail, mail_id)
    except ValueError:
        return jsonify(code=-1, msg='Error')
    return jsonify(code=1, msg='Success')


@workflow_blueprint.route('/save_activity_data', methods=['POST'])
@login_required_customize
def save_activity():
    """アイテムデータの新規登録、編集の完了後にアイテムデータの更新をする

    Returns:
        object: アイテムデータの更新が成功したか示すResponse
               json data validated by ResponseMessageSchema or SaveActivityResponseSchema

    Raises:
        marshmallow.exceptions.ValidationError: if ResponseMessageSchema is invalid.
    ---
    post:
        description: "save activity"
        security:
            - login_required_customize: []
        requestBody:
            required: false
            content:
                application/json:
                    schema:
                        SaveActivitySchema
                    example: {"activity_id": "A-20220830-00001", "title": "title", "shared_user_ids": []}
        responses:
            200:
                description: "success"
                content:
                    application/json:
                        schema:
                            SaveActivityResponseSchema
                        example: {"success": True, "msg": ""}
            400:
                description: "validation error"
                content:
                    application/json:
                        schema:
                            ResponseMessageSchema
                        example: {"code": -1,"msg":"{'shared_user_ids': ['Missing data for required field.']}"}
    """
    response = {
        "success": True,
        "msg": ""
    }
    try:
        data = SaveActivitySchema().load(request.get_json())
        save_activity_data(data.data)
    except ValidationError as err:
        res = ResponseMessageSchema().load({'code':-1, 'msg':str(err)})
        return jsonify(res.data), 400
    except Exception as error:
        response['success'] = False
        response["msg"] = str(error)
    res = SaveActivityResponseSchema().load(response)
    return jsonify(res.data), 200


@workflow_blueprint.route('/usage-report', methods=['GET'])
@login_required
def usage_report():
    """
    Retrieves and returns the usage reports for the 'usage-report' route.

    This route is accessed via a GET request.

    Returns:
        Response: JSON response containing the usage reports.

    Raises:
        None
    """
    getargs = request.args
    item_type_usage_report = current_app.config.get(
        'WEKO_ITEMS_UI_USAGE_REPORT')
    conditions = filter_all_condition(getargs)
    conditions['workflow'] = [item_type_usage_report]
    conditions['status'] = ['doing']
    activity = WorkActivity()
    # For usage report, just get all activities with provided conditions
    activities, _, _, _, _, _ = activity \
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


@workflow_blueprint.route('/get-data-init', methods=['GET'])
@login_required
def get_data_init():
    """
    Retrieves and returns initial data for the 'get-data-init' route.

    This route is accessed via a GET request and requires the user to be logged in.

    Returns:
        Response: JSON response containing the initial data.

    Raises:
        None
    """
    from weko_records_ui.utils import get_roles, get_terms, get_workflows
    init_workflows = get_workflows()
    init_roles = get_roles()
    init_terms = get_terms()
    roles = Role.query.all()
    logged_roles = []
    for role in roles:
        if role.id > 2:
            logged_roles.append({'id': role.id, 'name': role.name})
    return jsonify(
        init_workflows=init_workflows,
        init_roles=init_roles,
        logged_roles = logged_roles,
        init_terms=init_terms)


@workflow_blueprint.route('/download_activitylog/', methods=['GET','POST'])
@login_required
def download_activitylog():
    """download activitylog

    Args:
        filters: activity filters.
    Returns:
        object: tsv file of activitiylog

    ---
    get:
        responses:
            200:
                description: "success"
                content:
                    test/tsv:

            400:
                description: "no activity error"

            403:
                description: "permittion error"

    """
    if not current_app.config.get("DELETE_ACTIVITY_LOG_ENABLE"):
        abort(403)

    activity = WorkActivity()
    activities = []
    if current_user and current_user.roles:
        admin_roles = current_app.config.get("WEKO_WORKFLOW_ACTIVITYLOG_ROLE_ENABLE")
        has_admin_role = False
        for role in current_user.roles:
            if role in admin_roles:
                has_admin_role = True
                break
        if not has_admin_role:
            abort(403)
    if 'activity_id' in request.args:
        tmp_activity = activity.get_activity_by_id(activity_id=request.args.get('activity_id'))
        if tmp_activity == None:
            return jsonify(code=-1, msg='no activity error') ,400
        activities.append(tmp_activity)
    else:
        conditions = filter_all_condition(request.args)
        activities, _, _, _, _, _ = activity.get_activity_list(conditions=conditions, activitylog=True)

        if not activities:
            return jsonify(code=-1, msg='no activity error') ,400

    response = Response(
                make_activitylog_tsv(activities),
                mimetype='text/tsv',
                headers={"Content-disposition": "attachment; filename=activitylog.tsv"},
            )
    return response , 200

@workflow_blueprint.route('/clear_activitylog/', methods=['GET'])
@login_required
def clear_activitylog():
    """clear and download activitylog.

    Args:
        filters(optional): activity filters.
        activity_id(optional): activity_id.
    Returns:
        object: tsv file of activitiylog

    ---
    get:
        responses:
            200:
                description: "success"
                content:
                    test/tsv:
            400:
                description: "no activity error"  or "delete failed error"

            403:
                description: "permittion error"

    """
    def _quit_activity(del_activity):
        """ quit activity"""
        _activity = dict(
            activity_id=del_activity.activity_id,
            action_id=del_activity.action_id,
            action_status=ActionStatusPolicy.ACTION_CANCELED,
            action_order=del_activity.action_order
        )

        result = activity.quit_activity(_activity)

        if not result:
            return False
        else:
            activity.upt_activity_action_status(
                activity_id=del_activity.activity_id,
                action_id=del_activity.action_id,
                action_status=ActionStatusPolicy.ACTION_CANCELED,
                action_order=del_activity.action_order)
            return True

    if not current_app.config.get("DELETE_ACTIVITY_LOG_ENABLE"):
        abort(403)

    activity = WorkActivity()
    workflow_activity_action = ActivityAction()
    activities = []
    if current_user and current_user.roles:
        admin_roles = current_app.config.get("WEKO_WORKFLOW_ACTIVITYLOG_ROLE_ENABLE")
        has_admin_role = False
        for role in current_user.roles:
            if role in admin_roles:
                has_admin_role = True
                break
        if not has_admin_role:
            abort(403)

    # delete a activity
    if 'activity_id' in request.args:
        del_activity = activity.get_activity_by_id(activity_id=request.args.get('activity_id'))
        if del_activity == None:
            return jsonify(code=-1, msg='no activity error') ,400
        if del_activity.activity_status in [ActivityStatusPolicy.ACTIVITY_MAKING, ActivityStatusPolicy.ACTIVITY_BEGIN]:
            result = _quit_activity(del_activity)
            if not result:
                return jsonify(code=-1, msg=str(DeleteActivityFailedRESTError())) ,400
        try:
            with db.session.begin_nested():
                workflow_activity_action.query.filter_by(activity_id=del_activity.activity_id).delete()
                db.session.delete(del_activity)
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            current_app.logger.exception(str(ex))
            return jsonify(code=-1, msg='delete failed error') ,400
    # delete all filitering activity
    else:

        conditions = filter_all_condition(request.args)
        activities, _, _, _, _, _ = activity.get_activity_list(conditions=conditions, activitylog=True)

        if not activities:
            return jsonify(code=-1, msg='no activity error') ,400

        for del_activity in activities:
            if del_activity.activity_status in [ActivityStatusPolicy.ACTIVITY_MAKING, ActivityStatusPolicy.ACTIVITY_BEGIN]:
                result = _quit_activity(del_activity)
                if not result:
                   return jsonify(code=-1, msg=str(DeleteActivityFailedRESTError())) ,400

        try:
            with db.session.begin_nested():
                for activty in activities:
                    workflow_activity_action.query.filter_by(activity_id=activty.activity_id).delete()
                    db.session.delete(activty)
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            current_app.logger.exception(str(ex))
            return jsonify(code=-1, msg='delete failed error') ,400

    return jsonify(code=1, msg='delete activitylogs success') ,200

class ActivityActionResource(ContentNegotiatedMethodView):
    """Workflow Activity Resource."""

    activity = WorkActivity()

    def activity_information(self, activity):
        """Display Activity Detail in response.

        Args:
            activity ([type]): [description]

        Returns:
            [type]: [description]

        """
        response = {
            'activityId': activity.activity_id,
            'email': None,
            'status': None
        }

        user = User.query.get(activity.activity_login_user)
        response['email'] = user.email if user else ''

        status = ActionStatusPolicy.describe(
            ActionStatusPolicy.ACTION_DOING)
        if activity.activity_status == \
                ActivityStatusPolicy.ACTIVITY_FINALLY:
            status = ActionStatusPolicy.describe(
                ActionStatusPolicy.ACTION_DONE)
        elif activity.activity_status == \
                ActivityStatusPolicy.ACTIVITY_CANCEL:
            status = ActionStatusPolicy.describe(
                ActionStatusPolicy.ACTION_CANCELED)
        response['status'] = _(status)

        current_app.logger.info('{}_{}_{}_{}_FINISH_{}'.format(
            self._prefix, request.method,
            current_user.email, self._time,
            activity.activity_id))
        return response

    def logging_error(self, name, detail):
        """Logging error.

        Args:
            error ([type]): [description]
            detail ([type]): [description]

        """
        current_app.logger.info('{}_{}_{}_{}_ERROR_{}: {}'.format(
            self._prefix, request.method,
            current_user.email, self._time,
            name,
            detail))

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super(ActivityActionResource, self).__init__(
            *args,
            **kwargs
        )
        self._prefix = current_app.config.get(
            'WEKO_WORKFLOW_GAKUNINRDM_PREFIX')
        self._time = datetime.now().timestamp()

    @require_api_auth()
    @require_oauth_scopes(activity_scope.id)
    def post(self):
        """Handle POST activity action.

        Raises:
            InvalidInputRESTError: [description]
            InvalidInputRESTError: [description]
            InvalidInputRESTError: [description]

        Returns:
            [type]: [description]

        """
        current_app.logger.info('{}_{}_{}_{}_REQUEST'.format(
            self._prefix, request.method,
            current_user.email, self._time))

        item_type_id = request.form.get('item_type_id')
        itemmetadata = request.files.get('file')
        if not item_type_id or not itemmetadata:
            self.logging_error('missing_input', 'missing_input')
            raise InvalidInputRESTError()

        # checking the metadata
        check_result = check_tsv_import_items(itemmetadata, False, True)
        item = check_result.get('list_record')[0] \
            if check_result.get('list_record') else None
        if check_result.get('error') or not item or item.get('errors'):
            if check_result.get('error'):
                self.logging_error('check_import_items',
                                   check_result.get('error'))
            elif item.get('errors'):
                self.logging_error('check_import_items', item.get('errors'))
            else:
                self.logging_error('check_import_items', 'item_missing')
            raise InvalidInputRESTError()

        # register new item
        item['root_path'] = check_result.get('data_path') + '/data'
        import_result = import_items_to_system(item, None, True)
        shutil.rmtree(check_result.get('data_path'))
        if not import_result['success']:
            self.logging_error('import_items_to_system',
                               import_result['success'])
            raise InvalidInputRESTError()

        _default = current_app.config.get('WEKO_WORKFLOW_GAKUNINRDM_DATA')[0]
        post_activity = {
            'flow_id': _default.get('flow_id'),
            'itemtype_id': item_type_id,
            'workflow_id': _default.get('workflow_id')
        }

        try:
            activity = None
            pid = PersistentIdentifier.query.filter_by(
                pid_type='recid',
                pid_value=import_result.get('recid')
            ).first()
            activity = self.activity.init_activity(
                post_activity, item_id=pid.object_uuid)
            self.activity.update_title(
                activity.activity_id,
                item.get('item_title'))
        except Exception as ex:
            self.logging_error('init_activity', str(ex))
            raise InvalidInputRESTError()
        finally:
            if not activity or not activity.activity_id:
                self.logging_error('init_activity', 'activity_error')
                raise InvalidInputRESTError()

        return make_response(jsonify(self.activity_information(activity)), 200)

    @require_api_auth()
    @require_oauth_scopes(activity_scope.id)
    def get(self, activity_id):
        """Handle GET activity action.

        Args:
            activity_id ([type]): [description]

        Raises:
            ActivityBaseRESTError: [description]
            ActivityNotFoundRESTError: [description]

        Returns:
            [type]: [description]

        """
        current_app.logger.info('{}_{}_{}_{}_REQUEST'.format(
            self._prefix, request.method,
            current_user.email, self._time))

        if not activity_id:
            self.logging_error('missing_input', 'missing_input')
            raise ActivityBaseRESTError()

        activity = self.activity.get_activity_by_id(activity_id)
        if not activity:
            self.logging_error('get_activity_by_id', str(activity_id))
            raise ActivityNotFoundRESTError()

        return make_response(jsonify(self.activity_information(activity)), 200)

    @require_api_auth()
    @require_oauth_scopes(activity_scope.id)
    def delete(self, activity_id):
        """Handle DELETE activity action.

        This will cancel selected activity.
        Args:
            activity_id ([type]): [description]

        Raises:
            ActivityBaseRESTError: [description]
            RegisteredActivityNotFoundRESTError: [description]
            DeleteActivityFailedRESTError: [description]

        Returns:
            [type]: [description]

        """
        current_app.logger.info('{}_{}_{}_{}_REQUEST'.format(
            self._prefix, request.method,
            current_user.email, self._time))

        if not activity_id:
            self.logging_error('missing_input', 'missing_input')
            raise ActivityBaseRESTError()

        activity = self.activity.get_activity_by_id(activity_id)
        if not activity:
            self.logging_error('get_activity_by_id', str(activity_id))
            raise RegisteredActivityNotFoundRESTError()
        elif activity.activity_status != ActionStatusPolicy.ACTION_DOING:
            self.logging_error('get_activity_by_id', 'action_not_doing')
            raise DeleteActivityFailedRESTError()

        _activity = dict(
            activity_id=activity.activity_id,
            action_id=activity.action_id,
            action_status=ActionStatusPolicy.ACTION_CANCELED,
            action_order=activity.action_order
        )

        result = self.activity.quit_activity(_activity)
        if not result:
            self.logging_error('quit_activity', 'action_not_doing')
            raise DeleteActivityFailedRESTError()
        else:
            self.activity.upt_activity_action_status(
                activity_id=activity.activity_id,
                action_id=activity.action_id,
                action_status=ActionStatusPolicy.ACTION_CANCELED,
                action_order=activity.action_order)

        status = 200
        message = '登録アクティビティを削除'
        self.activity_information(activity)
        return make_response(message, status)


depositactivity_blueprint.add_url_rule(
    '/<string:activity_id>',
    view_func=ActivityActionResource.as_view(
        'workflow_activity_action'
    ),
    methods=['GET', 'DELETE']
)


depositactivity_blueprint.add_url_rule(
    '',
    view_func=ActivityActionResource.as_view(
        'workflow_activity_new'
    ),
    methods=['POST']
)


@workflow_blueprint.teardown_request
@depositactivity_blueprint.teardown_request
def dbsession_clean(exception):
    """
    Cleans up the database session after each request.

    Args:
        exception (Exception): The exception that occurred during the request.

    Returns:
        None

    Raises:
        None
    """
    current_app.logger.debug("weko_workflow dbsession_clean: {}".format(exception))
    if exception is None:
        try:
            db.session.commit()
        except:
            db.session.rollback()
    db.session.remove()


@workflow_blueprint.route('/edit_item_direct/<string:pid_value>', methods=['GET'])
def edit_item_direct(pid_value):
    """edit_item_direct.

    Check if you are logged in:
        logged in: redirect to edit_item_direct_after_login
        not logged in: redirect to login page

    Args:
        pid_value (str): The pid_value of the item to be edited.

    return: The result json:
        code: status code,
        msg: meassage result,
        data: url redirect
    """

    from flask_security import current_user

    # ! Check if you are logged in
    if not current_user.is_authenticated:
        return redirect(url_for_security(
            'login',
            next="/workflow/edit_item_direct_after_login/" + pid_value))
    else:
        return redirect(url_for(".edit_item_direct_after_login", pid_value=pid_value))


@workflow_blueprint.route('/edit_item_direct_after_login/<string:pid_value>', methods=['GET'])
@login_required
def edit_item_direct_after_login(pid_value):
    """edit_item_direct_after_login.

    Host the api which provide 2 service:
        Check permission: check if user is owner/admin/shared user
        Create new activity for editing flow

    Args:
        pid_value (str): The pid_value of the item to be edited.

    return: The result json:
        code: status code,
        msg: meassage result,
        data: url redirect
    """

    from flask_security import current_user

    # Cache Storage
    redis_connection = RedisConnection()
    sessionstorage = redis_connection.connection(db=current_app.config['ACCOUNTS_SESSION_REDIS_DB_NO'], kv = True)
    if sessionstorage.redis.exists("pid_{}_will_be_edit".format(pid_value)):
        return render_template("weko_theme/error.html",
                error="This Item is being edited."), 400
    else:
        sessionstorage.put(
            "pid_{}_will_be_edit".format(pid_value),
            str(current_user.get_id()).encode('utf-8'),
            ttl_secs=3)

    # ! Check if the record exists
    try:
        record_class = import_string('weko_deposit.api:WekoDeposit')
        resolver = Resolver(pid_type='recid',
                            object_type='rec',
                            getter=record_class.get_record)
        recid, deposit = resolver.resolve(pid_value)

        if not deposit:
            return render_template("weko_theme/error.html",
                    error="Record does not exist."), 404
    except PIDDoesNotExistError as ex:
        return render_template("weko_theme/error.html",
                error="Record does not exist."), 404

    authenticators = [str(deposit.get('owner'))] + \
                     [str(shared_id) for shared_id in deposit.get('weko_shared_ids', [])]
    user_id = str(get_current_user())
    activity = WorkActivity()
    latest_pid = PIDVersioning(child=recid).last_child

    # ! Check User's Permissions
    if user_id not in authenticators and not get_user_roles(is_super_role=True)[0]:
        return render_template("weko_theme/error.html",
                error="You are not allowed to edit this item."), 400

    # ! Check dependency ItemType
    if not ItemTypes.get_latest():
        return render_template("weko_theme/error.html",
                error="You do not even have an ItemType."), 400

    item_type_id = deposit.get('item_type_id')
    item_type = ItemTypes.get_by_id(item_type_id)
    if not item_type:
        return render_template("weko_theme/error.html",
                error="Dependency ItemType not found."), 400

    # Check Record is in import progress
    if check_an_item_is_locked(pid_value):
        return render_template("weko_theme/error.html",
                error="Item cannot be edited because the import is in progress."), 400

    # ! Check Record is being edit
    item_uuid = latest_pid.object_uuid
    post_workflow = activity.get_workflow_activity_by_item_id(item_uuid)

    if post_workflow:
        is_begin_edit = check_item_is_being_edit(recid, post_workflow, activity)
        if is_begin_edit:
            return render_template("weko_theme/error.html",
                    error="This Item is being edited."), 400

    post_activity = '{"workflow_id": 0, "flow_id": 0, ' \
        '"itemtype_id": 0, "community": 0, "post_workflow": 0}'
    post_activity = json.loads(post_activity)
    if post_workflow:
        post_activity['workflow_id'] = post_workflow.workflow_id
        post_activity['flow_id'] = post_workflow.flow_id
    else:
        post_workflow = activity.get_workflow_activity_by_item_id(
            recid.object_uuid
        )
        workflow = get_workflow_by_item_type_id(item_type.name_id,
                                                item_type_id)
        if not workflow:
            return render_template("weko_theme/error.html",
                    error="Workflow setting does not exist."), 400
        post_activity['workflow_id'] = workflow.id
        post_activity['flow_id'] = workflow.flow_id
    post_activity['itemtype_id'] = item_type_id
    post_activity['post_workflow'] = post_workflow

    try:
        rtn = prepare_edit_workflow(post_activity, recid, deposit)
        db.session.commit()
    except SQLAlchemyError as ex:
        current_app.logger.error('sqlalchemy error: {}'.format(ex))
        db.session.rollback()
        return render_template("weko_theme/error.html",
                error="An error has occurred."), 500
    except BaseException as ex:
        import traceback
        current_app.logger.error(traceback.format_exc())
        current_app.logger.error('Unexpected error: {}'.format(ex))
        db.session.rollback()
        return render_template("weko_theme/error.html",
                error="An error has occurred."), 500

    return redirect(url_for(
        'weko_workflow.display_activity', activity_id=rtn.activity_id))
