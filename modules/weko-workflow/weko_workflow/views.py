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

import json
import os
import sys
from collections import OrderedDict
from functools import wraps

import redis
from flask import Blueprint, current_app, jsonify, render_template, request, \
    session, url_for
from flask_babelex import gettext as _
from flask_login import current_user, login_required
from invenio_accounts.models import Role, userrole
from invenio_db import db
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_pidstore.resolver import Resolver
from simplekv.memory.redisstore import RedisStore
from sqlalchemy import types
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import cast
from weko_accounts.api import ShibUser
from weko_authors.models import Authors
from weko_deposit.api import WekoDeposit
from weko_deposit.pidstore import get_record_identifier, \
    get_record_without_version
from weko_items_ui.api import item_login
from weko_items_ui.utils import get_actionid, to_files_js
from weko_records.api import FeedbackMailList, ItemsMetadata
from weko_records.models import ItemMetadata
from weko_records.serializers.utils import get_item_type_name
from werkzeug.utils import import_string

from .api import Action, Flow, GetCommunity, UpdateItem, WorkActivity, \
    WorkActivityHistory, WorkFlow
from .config import IDENTIFIER_GRANT_IS_WITHDRAWING, IDENTIFIER_GRANT_LIST, \
    IDENTIFIER_GRANT_SELECT_DICT, IDENTIFIER_GRANT_SUFFIX_METHOD, \
    ITEM_REGISTRATION_ACTION_ID
from .models import ActionStatusPolicy, ActivityStatusPolicy
from .romeo import search_romeo_issn, search_romeo_jtitles
from .utils import IdentifierHandle, delete_unregister_buckets, \
    get_activity_id_of_record_without_version, get_identifier_setting, \
    is_hidden_pubdate, is_show_autofill_metadata, item_metadata_validation, \
    merge_buckets_by_records, saving_doi_pidstore, set_bucket_default_size, \
    register_cnri

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
    activity = WorkActivity()
    getargs = request.args
    ctx = {'community': None}
    community_id = ""
    if 'community' in getargs:
        activities = activity.get_activity_list(request.args.get('community'))
        comm = GetCommunity.get_community_by_id(request.args.get('community'))
        ctx = {'community': comm}
        community_id = comm.id
    else:
        activities = activity.get_activity_list()

    from weko_theme.utils import get_design_layout
    # Get the design for widget rendering
    page, render_widgets = get_design_layout(
        request.args.get('community') or current_app.config[
            'WEKO_THEME_DEFAULT_COMMUNITY'])

    return render_template(
        'weko_workflow/activity_list.html',
        page=page,
        render_widgets=render_widgets,
        activities=activities,
        community_id=community_id,
        **ctx
    )


@blueprint.route('/iframe/success', methods=['GET'])
def iframe_success():
    """Renders an item register view.

    :return: The rendered template.
    """
    # get session value
    history = WorkActivityHistory()
    histories = history.get_activity_history_list(session['itemlogin_id'])
    activity = session['itemlogin_activity']
    item = session['itemlogin_item']
    steps = session['itemlogin_steps']
    action_id = session['itemlogin_action_id']
    cur_step = session['itemlogin_cur_step']
    record = session['itemlogin_record']
    res_check = session['itemlogin_res_check']
    pid = session['itemlogin_pid']
    community_id = session.get('itemlogin_community_id')

    ctx = {'community': None}
    if community_id:
        comm = GetCommunity.get_community_by_id(community_id)
        ctx = {'community': comm}

    # delete session value
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

    from weko_theme.utils import get_design_layout
    # Get the design for widget rendering
    page, render_widgets = get_design_layout(
        community_id or current_app.config['WEKO_THEME_DEFAULT_COMMUNITY'])

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
                           community_id=community_id,
                           **ctx)


@blueprint.route('/activity/new', methods=['GET'])
@login_required
def new_activity():
    """New activity."""
    workflow = WorkFlow()
    workflows = workflow.get_workflow_list()
    getargs = request.args
    ctx = {'community': None}
    community_id = ""
    if 'community' in getargs:
        comm = GetCommunity.get_community_by_id(request.args.get('community'))
        ctx = {'community': comm}
        community_id = comm.id

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
    if 'community' in getargs:
        comm = GetCommunity.get_community_by_id(request.args.get('community'))
        return jsonify(code=0, msg='success',
                       data={'redirect': url_for(
                           'weko_workflow.display_activity',
                           activity_id=rtn.activity_id, community=comm.id)})
    return jsonify(code=0, msg='success',
                   data={'redirect': url_for(
                       'weko_workflow.display_activity',
                       activity_id=rtn.activity_id)})


@blueprint.route('/activity/list', methods=['GET'])
@login_required
def list_activity():
    """List activity."""
    activity = WorkActivity()
    activities = activity.get_activity_list()

    from weko_theme.utils import get_design_layout
    # Get the design for widget rendering
    page, render_widgets = get_design_layout(
        current_app.config['WEKO_THEME_DEFAULT_COMMUNITY'])
    return render_template(
        'weko_workflow/activity_list.html',
        page=page,
        render_widgets=render_widgets,
        activities=activities
    )


@blueprint.route('/activity/detail/<string:activity_id>', methods=['GET'])
@login_required
def display_activity(activity_id=0):
    """Display activity."""
    activity = WorkActivity()
    activity_detail = activity.get_activity_detail(activity_id)
    item = None
    if activity_detail and activity_detail.item_id:
        try:
            item = ItemsMetadata.get_record(id_=activity_detail.item_id)
        except NoResultFound as ex:
            current_app.logger.exception(str(ex))
            item = None

    steps = activity.get_activity_steps(activity_id)
    history = WorkActivityHistory()
    histories = history.get_activity_history_list(activity_id)
    workflow = WorkFlow()
    workflow_detail = workflow.get_workflow_by_id(
        activity_detail.workflow_id)

    if activity_detail.activity_status == \
        ActivityStatusPolicy.ACTIVITY_FINALLY \
        or activity_detail.activity_status == \
            ActivityStatusPolicy.ACTIVITY_CANCEL:
        activity_detail.activity_status_str = _('End')
    else:
        activity_detail.activity_status_str = \
            request.args.get('status', 'ToDo')
    cur_action = activity_detail.action
    action_endpoint = cur_action.action_endpoint
    action_id = cur_action.id
    temporary_comment = activity.get_activity_action_comment(
        activity_id=activity_id, action_id=action_id)

    # display_activity of Identifier grant
    identifier_setting = None
    if 'identifier_grant' == action_endpoint and item:
        community_id = request.args.get('community', None)
        if not community_id:
            community_id = 'Root Index'
        identifier_setting = get_identifier_setting(community_id)

        # valid date pidstore_identifier data
        if identifier_setting:
            if not identifier_setting.jalc_doi:
                identifier_setting.jalc_doi = '<Empty>'
            if not identifier_setting.jalc_crossref_doi:
                identifier_setting.jalc_crossref_doi = '<Empty>'
            if not identifier_setting.jalc_datacite_doi:
                identifier_setting.jalc_datacite_doi = '<Empty>'

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

    temporary_journal = activity.get_action_journal(
        activity_id=activity_id, action_id=action_id)
    if temporary_journal:
        temporary_journal = temporary_journal.action_journal

    cur_step = action_endpoint
    step_item_login_url = None
    approval_record = []
    pid = None
    record = {}
    need_file = False
    json_schema = ''
    schema_form = ''
    item_save_uri = ''
    files = []
    endpoints = {}
    links = None
    need_thumbnail = False
    files_thumbnail = []
    allow_multi_thumbnail = False
    show_autofill_metadata = True
    is_hidden_pubdate_value = False
    item_type_name = get_item_type_name(workflow_detail.itemtype_id)
    if 'item_login' == action_endpoint or 'file_upload' == action_endpoint:
        activity_session = dict(
            activity_id=activity_id,
            action_id=activity_detail.action_id,
            action_version=cur_action.action_version,
            action_status=ActionStatusPolicy.ACTION_DOING,
            commond=''
        )
        show_autofill_metadata = is_show_autofill_metadata(item_type_name)
        is_hidden_pubdate_value = is_hidden_pubdate(item_type_name)
        session['activity_info'] = activity_session
        # get item edit page info.
        step_item_login_url, need_file, record, json_schema, schema_form,\
            item_save_uri, files, endpoints, need_thumbnail, files_thumbnail, \
            allow_multi_thumbnail \
            = item_login(item_type_id=workflow_detail.itemtype_id)
        if item:
            # Remove the unused local variable
            # _pid_identifier = PersistentIdentifier.get_by_object(
            #     pid_type='depid', object_type='rec', object_uuid=item.id)
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

    # if 'approval' == action_endpoint:
    if item:
        # get record data for the first time access to editing item screen
        pid_identifier = PersistentIdentifier.get_by_object(
            pid_type='depid', object_type='rec', object_uuid=item.id)
        record_class = import_string('weko_deposit.api:WekoRecord')
        resolver = Resolver(pid_type='recid', object_type='rec',
                            getter=record_class.get_record)
        pid, approval_record = resolver.resolve(pid_identifier.pid_value)

        files = to_files_js(approval_record)

        # get files data after click Save btn
        sessionstore = RedisStore(redis.StrictRedis.from_url(
            'redis://{host}:{port}/1'.format(
                host=os.getenv('INVENIO_REDIS_HOST', 'localhost'),
                port=os.getenv('INVENIO_REDIS_PORT', '6379'))))
        if sessionstore.redis.exists('activity_item_' + str(activity_id)):
            item_str = sessionstore.get('activity_item_' + str(activity_id))
            item_json = json.loads(item_str.decode('utf-8'))
            if 'files' in item_json:
                files = item_json.get('files')
        if not files:
            deposit = WekoDeposit.get_record(item.id)
            if deposit:
                files = to_files_js(deposit)

        if files:
            if not files_thumbnail:
                files_thumbnail = [i for i in files
                                   if 'is_thumbnail' in i.keys()
                                   and i['is_thumbnail']]

        from weko_deposit.links import base_factory
        links = base_factory(pid)

    res_check = check_authority_action(str(activity_id), str(action_id))

    getargs = request.args
    ctx = {'community': None}
    community_id = ""
    if 'community' in getargs:
        comm = GetCommunity.get_community_by_id(request.args.get('community'))
        ctx = {'community': comm}
        community_id = comm.id
    # be use for index tree and comment page.
    if 'item_login' == action_endpoint or 'file_upload' == action_endpoint:
        session['itemlogin_id'] = activity_id
        session['itemlogin_activity'] = activity_detail
        session['itemlogin_item'] = item
        session['itemlogin_steps'] = steps
        session['itemlogin_action_id'] = action_id
        session['itemlogin_cur_step'] = cur_step
        session['itemlogin_record'] = approval_record
        session['itemlogin_histories'] = histories
        session['itemlogin_res_check'] = res_check
        session['itemlogin_pid'] = pid
        session['itemlogin_community_id'] = community_id

    from weko_theme.utils import get_design_layout
    # Get the design for widget rendering
    page, render_widgets = get_design_layout(
        community_id or current_app.config['WEKO_THEME_DEFAULT_COMMUNITY'])

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
        idf_grant_method=IDENTIFIER_GRANT_SUFFIX_METHOD,
        record=approval_record,
        records=record,
        step_item_login_url=step_item_login_url,
        need_file=need_file,
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
        pid=pid,
        community_id=community_id,
        need_thumbnail=need_thumbnail,
        files_thumbnail=files_thumbnail,
        allow_multi_thumbnail=allow_multi_thumbnail,
        enable_feedback_maillist=current_app.config[
            'WEKO_WORKFLOW_ENABLE_FEEDBACK_MAIL'],
        enable_contributor=current_app.config[
            'WEKO_WORKFLOW_ENABLE_CONTRIBUTOR'],
        show_automatic_metadata_input=show_autofill_metadata,
        is_hidden_pubdate=is_hidden_pubdate_value,
        **ctx
    )


def check_authority(func):
    """Check Authority."""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        work = WorkActivity()
        roles, users = work.get_activity_action_role(
            activity_id=kwargs.get('activity_id'),
            action_id=kwargs.get('action_id'))
        cur_user = current_user.get_id()
        cur_role = db.session.query(Role).join(userrole).filter_by(
            user_id=cur_user).all()
        if users['deny'] and int(cur_user) in users['deny']:
            return jsonify(code=403, msg=_('Authorization required'))
        if users['allow'] and int(cur_user) not in users['allow']:
            return jsonify(code=403, msg=_('Authorization required'))
        for role in cur_role:
            if roles['deny'] and role.id in roles['deny']:
                return jsonify(code=403, msg=_('Authorization required'))
            if roles['allow'] and role.id not in roles['allow']:
                return jsonify(code=403, msg=_('Authorization required'))
        return func(*args, **kwargs)

    return decorated_function


def check_authority_action(activity_id='0', action_id=0):
    """Check authority."""
    work = WorkActivity()
    roles, users = work.get_activity_action_role(activity_id, action_id)
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
    from .models import User, Activity
    activity = Activity.query.filter_by(
        activity_id=activity_id).first()
    # If user is the author of activity
    if int(cur_user) == activity.activity_login_user:
        return 0
    # If user has admin role
    supers = current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER']
    for role in list(current_user.roles or []):
        if role.name in supers:
            return 0
    # If user has community role
    # and the user who created activity is member of community
    # role -> has permission:
    community_role_name = current_app.config['WEKO_PERMISSION_ROLE_COMMUNITY']
    # Get the list of users who has the community role
    community_users = User.query.outerjoin(userrole).outerjoin(Role) \
        .filter(community_role_name == Role.name) \
        .filter(userrole.c.role_id == Role.id) \
        .filter(User.id == userrole.c.user_id) \
        .all()
    community_user_ids = [
        community_user.id for community_user in community_users]
    for role in list(current_user.roles or []):
        if role.name in community_role_name:
            # User has community role
            if activity.activity_login_user in community_user_ids:
                return 0
            break

    # Check if this activity has contributor equaling to current user
    im = ItemMetadata.query.filter_by(id=activity.item_id)\
        .filter(
        cast(ItemMetadata.json['shared_user_id'], types.INT) == int(cur_user))\
        .one_or_none()
    if im:
        # There is an ItemMetadata with contributor equaling to current user,
        # allow to access
        return 0

    # Otherwise, user has no permission
    return 1


@blueprint.route(
    '/activity/action/<string:activity_id>/<int:action_id>',
    methods=['POST'])
@login_required
@check_authority
def next_action(activity_id='0', action_id=0):
    """Next action."""
    work_activity = WorkActivity()
    history = WorkActivityHistory()

    post_json = request.get_json()
    activity = dict(
        activity_id=activity_id,
        action_id=action_id,
        action_version=post_json.get('action_version'),
        action_status=ActionStatusPolicy.ACTION_DONE,
        commond=post_json.get('commond')
    )

    action = Action().get_action_detail(action_id)
    action_endpoint = action.action_endpoint

    if 'begin_action' == action_endpoint:
        return jsonify(code=0, msg=_('success'))

    if 'end_action' == action_endpoint:
        work_activity.end_activity(activity)
        return jsonify(code=0, msg=_('success'))

    if action_endpoint == 'item_login':
        register_cnri(activity_id)

    activity_detail = work_activity.get_activity_detail(activity_id)
    item_id = None
    recid = None
    record = None
    pid_without_ver = None
    if activity_detail and activity_detail.item_id:
        item_id = activity_detail.item_id
        current_pid = PersistentIdentifier.get_by_object(pid_type='recid',
                                                         object_type='rec',
                                                         object_uuid=item_id)
        recid = get_record_identifier(current_pid.pid_value)
        record = WekoDeposit.get_record(item_id)
        if record:
            pid_without_ver = get_record_without_version(current_pid)
            deposit = WekoDeposit(record, record.model)

    if post_json.get('temporary_save') == 1 \
            and action_endpoint != 'identifier_grant':
        if 'journal' in post_json:
            work_activity.create_or_update_action_journal(
                activity_id=activity_id,
                action_id=action_id,
                journal=post_json.get('journal')
            )
        else:
            work_activity.upt_activity_action_comment(
                activity_id=activity_id,
                action_id=action_id,
                comment=post_json.get('commond')
            )
        return jsonify(code=0, msg=_('success'))
    elif post_json.get('journal'):
        work_activity.create_or_update_action_journal(
            activity_id=activity_id,
            action_id=action_id,
            journal=post_json.get('journal')
        )

    if 'approval' == action_endpoint:
        if item_id is not None:
            item = ItemsMetadata.get_record(id_=item_id)
            pid_identifier = PersistentIdentifier.get_by_object(
                pid_type='depid', object_type='rec', object_uuid=item.id)
            record_class = import_string('weko_deposit.api:WekoRecord')
            resolver = Resolver(pid_type='recid', object_type='rec',
                                getter=record_class.get_record)
            _pid, _approval_record = resolver.resolve(pid_identifier.pid_value)

            action_feedbackmail = work_activity.get_action_feedbackmail(
                activity_id=activity_id,
                action_id=ITEM_REGISTRATION_ACTION_ID)
            if action_feedbackmail:
                FeedbackMailList.update(
                    item_id=item_id,
                    feedback_maillist=action_feedbackmail.feedback_maillist
                )
                if not recid and pid_without_ver:
                    FeedbackMailList.update(
                        item_id=pid_without_ver.object_uuid,
                        feedback_maillist=action_feedbackmail.feedback_maillist
                    )

            if record:
                deposit.update_feedback_mail()
                deposit.update_jpcoar_identifier()
            # TODO: Make private as default.
            # UpdateItem.publish(pid, approval_record)

    if 'item_link' == action_endpoint:
        relation_data = post_json.get('link_data'),
        item = ItemsMetadata.get_record(id_=item_id)
        pid_identifier = PersistentIdentifier.get_by_object(
            pid_type='depid', object_type='rec', object_uuid=item.id)
        record_class = import_string('weko_deposit.api:WekoRecord')
        resolver = Resolver(pid_type='recid', object_type='rec',
                            getter=record_class.get_record)
        _pid, item_record = resolver.resolve(pid_identifier.pid_value)
        updated_item = UpdateItem()
        updated_item.set_item_relation(relation_data, item_record)

    # save pidstore_identifier to ItemsMetadata
    identifier_select = post_json.get('identifier_grant')
    if 'identifier_grant' == action_endpoint and identifier_select:
        idf_grant_jalc_doi_manual = post_json.get(
            'identifier_grant_jalc_doi_suffix')
        idf_grant_jalc_cr_doi_manual = post_json.get(
            'identifier_grant_jalc_cr_doi_suffix')
        idf_grant_jalc_dc_doi_manual = post_json.get(
            'identifier_grant_jalc_dc_doi_suffix')

        # If is action identifier_grant, then save to to database
        identifier_grant = {
            'action_identifier_select': identifier_select,
            'action_identifier_jalc_doi': idf_grant_jalc_doi_manual,
            'action_identifier_jalc_cr_doi': idf_grant_jalc_cr_doi_manual,
            'action_identifier_jalc_dc_doi': idf_grant_jalc_dc_doi_manual
        }

        work_activity.create_or_update_action_identifier(
            activity_id=activity_id,
            action_id=action_id,
            identifier=identifier_grant
        )
        # get workflow of first record attached version ID: x.1
        # if not recid and pid_without_ver:
        #     activity_without_ver = \
        #         get_activity_id_of_record_without_version(pid_without_ver)
        #     work_activity.create_or_update_action_identifier(
        #         activity_id=activity_without_ver,
        #         action_id=action_id,
        #         identifier=identifier_grant
        #     )

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
            if record and pid_without_ver and not recid:
                record_without_version = pid_without_ver.object_uuid
            saving_doi_pidstore(item_id, record_without_version, post_json,
                                int(identifier_select))

    rtn = history.create_activity_history(activity)
    if not rtn:
        return jsonify(code=-1, msg=_('error'))
    # next action
    work_activity.upt_activity_action_status(
        activity_id=activity_id, action_id=action_id,
        action_status=ActionStatusPolicy.ACTION_DONE)
    work_activity.upt_activity_action_comment(
        activity_id=activity_id,
        action_id=action_id,
        comment=''
    )
    flow = Flow()
    next_flow_action = flow.get_next_flow_action(
        activity_detail.flow_define.flow_id, action_id)
    if next_flow_action and len(next_flow_action) > 0:
        next_action_endpoint = next_flow_action[0].action.action_endpoint
        if 'end_action' == next_action_endpoint:
            new_activity_id = None
            if record:
                deposit.publish()
                updated_item = UpdateItem()
                # publish record without version ID when registering newly
                if recid:
                    # new record attached version ID
                    ver_attaching_record = deposit.newversion(current_pid)
                    new_activity_id = ver_attaching_record.model.id
                    ver_attaching_deposit = WekoDeposit(
                        ver_attaching_record,
                        ver_attaching_record.model)
                    ver_attaching_deposit.publish()
                    record_bucket_id = merge_buckets_by_records(
                        current_pid.object_uuid,
                        ver_attaching_record.model.id,
                        sub_bucket_delete=True
                    )
                    if not record_bucket_id:
                        return jsonify(code=-1, msg=_('error'))
                    # Record without version: Make status Public as default
                    updated_item.publish(record)
                else:
                    # update to record without version ID when editing
                    new_activity_id = record.model.id
                    if pid_without_ver:
                        record_without_ver = WekoDeposit.get_record(
                            pid_without_ver.object_uuid)
                        deposit_without_ver = WekoDeposit(
                            record_without_ver,
                            record_without_ver.model)
                        deposit_without_ver['path'] = deposit.get('path', [])
                        parent_record = deposit_without_ver.\
                            merge_data_to_record_without_version(current_pid)
                        deposit_without_ver.publish()

                        set_bucket_default_size(new_activity_id)
                        merge_buckets_by_records(
                            new_activity_id,
                            pid_without_ver.object_uuid
                        )
                        updated_item.publish(parent_record)
                delete_unregister_buckets(new_activity_id)
            activity.update(
                action_id=next_flow_action[0].action_id,
                action_version=next_flow_action[0].action_version,
                item_id=new_activity_id,
            )
            work_activity.end_activity(activity)
        else:
            next_action_id = next_flow_action[0].action_id
            work_activity.upt_activity_action(
                activity_id=activity_id, action_id=next_action_id,
                action_status=ActionStatusPolicy.ACTION_DOING)
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
    rtn = history.create_activity_history(activity)
    if rtn is None:
        return jsonify(code=-1, msg=_('error'))

    # next action
    activity_detail = work_activity.get_activity_detail(activity_id)
    flow = Flow()

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
            activity_detail.flow_define.flow_id, action_id)
    else:
        pre_action = flow.get_next_flow_action(
            activity_detail.flow_define.flow_id, 1)

    if pre_action and len(pre_action) > 0:
        previous_action_id = pre_action[0].action_id
        if req == 0:
            work_activity.upt_activity_action_status(
                activity_id=activity_id,
                action_id=action_id,
                action_status=ActionStatusPolicy.ACTION_THROWN_OUT)
        else:
            work_activity.upt_activity_action_status(
                activity_id=activity_id, action_id=action_id,
                action_status=ActionStatusPolicy.ACTION_RETRY)
        work_activity.upt_activity_action_status(
            activity_id=activity_id, action_id=previous_action_id,
            action_status=ActionStatusPolicy.ACTION_DOING)
        work_activity.upt_activity_action(
            activity_id=activity_id, action_id=previous_action_id,
            action_status=ActionStatusPolicy.ACTION_DOING)
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
@login_required
@check_authority
def cancel_action(activity_id='0', action_id=0):
    """Next action."""
    post_json = request.get_json()
    work_activity = WorkActivity()

    activity = dict(
        activity_id=activity_id,
        action_id=action_id,
        action_version=post_json.get('action_version'),
        action_status=ActionStatusPolicy.ACTION_CANCELED,
        commond=post_json.get('commond'))

    # clear deposit
    activity_detail = work_activity.get_activity_detail(activity_id)
    if activity_detail:
        cancel_item_id = activity_detail.item_id
        if not cancel_item_id:
            pid_value = post_json.get('pid_value')
            if pid_value:
                pid = PersistentIdentifier.get('recid', pid_value)
                cancel_item_id = pid.object_uuid
        if cancel_item_id:
            cancel_record = WekoDeposit.get_record(cancel_item_id)
            if cancel_record:
                cancel_deposit = WekoDeposit(
                    cancel_record, cancel_record.model)
                cancel_deposit.clear()
                # Remove draft child
                cancel_pid = PersistentIdentifier.get_by_object(
                    pid_type='recid', object_type='rec',
                    object_uuid=cancel_item_id)
                cancel_pv = PIDVersioning(child=cancel_pid)
                if cancel_pv.exists:
                    cancel_pv.remove_child(cancel_pid)

    work_activity.upt_activity_action_status(
        activity_id=activity_id, action_id=action_id,
        action_status=ActionStatusPolicy.ACTION_CANCELED)

    rtn = work_activity.quit_activity(activity)

    if not rtn:
        work_activity.upt_activity_action_status(
            activity_id=activity_id, action_id=action_id,
            action_status=ActionStatusPolicy.ACTION_DOING)
        return jsonify(code=-1, msg=_('Error! Cannot process quit activity!'))

    return jsonify(code=0,
                   msg=_('success'),
                   data={'redirect': url_for(
                       'weko_workflow.display_activity',
                       activity_id=activity_id)})


@blueprint.route(
    '/activity/detail/<string:activity_id>/<int:action_id>'
    '/withdraw',
    methods=['POST'])
@login_required
@check_authority
def withdraw_confirm(activity_id='0', action_id='0'):
    """Check weko user info.

    :return:
    """
    try:
        post_json = request.get_json()
        password = post_json.get('passwd', None)
        if not password:
            return jsonify(code=-1, msg=_('Password not provided'))
        wekouser = ShibUser()
        if wekouser.check_weko_user(current_user.email, password):
            activity = WorkActivity()
            item_id = activity.get_activity_detail(activity_id).item_id
            identifier_actionid = get_actionid('identifier_grant')
            identifier = activity.get_action_identifier_grant(
                activity_id,
                identifier_actionid)
            identifier_handle = IdentifierHandle(item_id)

            if identifier_handle.delete_pidstore_doi():
                identifier['action_identifier_select'] = \
                    IDENTIFIER_GRANT_IS_WITHDRAWING
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
                            activity.create_or_update_action_identifier(
                                record_without_ver_activity_id,
                                identifier_actionid,
                                identifier)

                return jsonify(
                    code=0,
                    msg=_('success'),
                    data={'redirect': url_for(
                        'weko_workflow.display_activity',
                        activity_id=activity_id)}
                )
            else:
                return jsonify(code=-1, msg=_('DOI Persistent is not exist.'))
        else:
            return jsonify(code=-1, msg=_('Invalid password'))
    except ValueError:
        current_app.logger.error('Unexpected error: {}', sys.exc_info()[0])
    return jsonify(code=-1, msg=_('Error!'))


@blueprint.route('/findDOI', methods=['POST'])
@login_required
def check_existed_doi():
    """Next action."""
    doi_link = request.get_json()
    respon = dict()
    respon['isExistDOI'] = False
    respon['isWithdrawnDoi'] = False
    respon['code'] = 1
    respon['msg'] = 'error'
    if doi_link:
        identifier = IdentifierHandle(None)
        doi_pidstore = identifier.check_pidstore_exist(
            'doi',
            doi_link['doi_link'])
        if doi_pidstore:
            respon['isExistDOI'] = True
            respon['msg'] = _('This DOI has been used already for another '
                              'item. Please input another DOI.')
            if doi_pidstore.status == PIDStatus.DELETED:
                respon['isWithdrawnDoi'] = True
                respon['msg'] = _(
                    'This DOI was withdrawn. Please input another DOI.')
        else:
            respon['msg'] = _('success')
        respon['code'] = 0
    return jsonify(respon)


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
            action_id=ITEM_REGISTRATION_ACTION_ID)
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
