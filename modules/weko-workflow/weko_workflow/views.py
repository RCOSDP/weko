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
from invenio_pidstore.models import PersistentIdentifier
from invenio_pidstore.resolver import Resolver
from invenio_pidstore.errors import PIDDoesNotExistError
from simplekv.memory.redisstore import RedisStore
from sqlalchemy.orm.exc import NoResultFound
from weko_accounts.api import ShibUser
from weko_deposit.api import WekoDeposit, WekoRecord
from weko_index_tree.models import Index
from weko_items_ui.api import item_login
from weko_items_ui.utils import get_actionid
from weko_items_ui.views import to_files_js
from weko_records.api import ItemsMetadata
from weko_records_ui.models import Identifier
from werkzeug.utils import import_string

from .api import Action, Flow, GetCommunity, UpdateItem, WorkActivity, \
    WorkActivityHistory, WorkFlow
from .config import IDENTIFIER_GRANT_IS_WITHDRAWING, IDENTIFIER_GRANT_LIST, \
    IDENTIFIER_GRANT_SUFFIX_METHOD
from .models import ActionStatusPolicy, ActivityStatusPolicy
from .romeo import search_romeo_issn, search_romeo_jtitles
from .utils import find_doi, get_community_id_by_index, is_withdrawn_doi, \
    pidstore_identifier_mapping, item_metadata_validation

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
    return render_template(
        'weko_workflow/activity_list.html',
        render_widgets=True,
        activities=activities, community_id=community_id, **ctx
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
    community_id = session['itemlogin_community_id']

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

    return render_template('weko_workflow/item_login_success.html',
                           render_widgets=True,
                           activity=activity,
                           item=item,
                           steps=steps,
                           action_id=action_id,
                           cur_step=cur_step,
                           record=record,
                           histories=histories,
                           res_check=res_check,
                           pid=pid,
                           community_id=community_id)


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
    return render_template(
        'weko_workflow/workflow_list.html',
        render_widgets=True,
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
    return render_template(
        'weko_workflow/activity_list.html',
        render_widgets=True,
        activities=activities
    )


@blueprint.route('/activity/detail/<string:activity_id>', methods=['GET'])
@login_required
def display_activity(activity_id=0):
    """Display activity."""
    activity = WorkActivity()
    activity_detail = activity.get_activity_detail(activity_id)
    item = None
    if activity_detail is not None and activity_detail.item_id is not None:
        try:
            item = ItemsMetadata.get_record(id_=activity_detail.item_id)
        except NoResultFound as ex:
            current_app.logger.exception(str(ex))
            item = None

    steps = activity.get_activity_steps(activity_id)
    history = WorkActivityHistory()
    histories = history.get_activity_history_list(activity_id)
    workflow = WorkFlow()
    workflow_detail = workflow.get_workflow_by_id(activity_detail.workflow_id)
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
    idf_grant_data = None
    identifier_type = []
    resource_type = []
    if 'identifier_grant' == action_endpoint and item:
        pidstore_identifier = item.get('pidstore_identifier')
        if pidstore_identifier:
            identifier_type = \
                pidstore_identifier['identifierRegistration']
        path = WekoRecord.get_record(item.id).get('path')
        if len(path) > 1:
            community_id = 'Root Index'
        else:
            index_address = path.pop(-1).split('/')
            index_id = Index.query.filter_by(id=index_address.pop()).one()
            community_id = get_community_id_by_index(
                index_id.index_name_english)
        idf_grant_data = Identifier.query.filter_by(
            repository=community_id).one_or_none()

        # valid date pidstore_identifier data
        if idf_grant_data is not None:
            if not idf_grant_data.jalc_doi:
                idf_grant_data.jalc_doi = '<Empty>'
            if not idf_grant_data.jalc_crossref_doi:
                idf_grant_data.jalc_crossref_doi = '<Empty>'
            if not idf_grant_data.jalc_datacite_doi:
                idf_grant_data.jalc_datacite_doi = '<Empty>'
            if not idf_grant_data.cnri:
                idf_grant_data.cnri = '<Empty>'
            if not idf_grant_data.suffix:
                idf_grant_data.suffix = '<Empty>'

    temporary_idf_grant = 0
    temporary_idf_grant_suffix = []
    temporary_identifier = activity.get_action_identifier_grant(
        activity_id=activity_id, action_id=action_id)
    if temporary_identifier:
        temporary_idf_grant = temporary_identifier.get(
            'action_identifier_select')
        temporary_idf_grant_suffix.append(
            temporary_identifier.get('action_identifier_jalc_doi'))
        temporary_idf_grant_suffix.append(
            temporary_identifier.get('action_identifier_jalc_cr_doi'))
        temporary_idf_grant_suffix.append(
            temporary_identifier.get('action_identifier_jalc_dc_doi'))

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
    if 'item_login' == action_endpoint or 'file_upload' == action_endpoint:
        activity_session = dict(
            activity_id=activity_id,
            action_id=activity_detail.action_id,
            action_version=cur_action.action_version,
            action_status=ActionStatusPolicy.ACTION_DOING,
            commond=''
        )
        session['activity_info'] = activity_session
        # get item edit page info.
        step_item_login_url, need_file, record, json_schema, \
            schema_form, item_save_uri, files, endpoints = item_login(
                item_type_id=workflow_detail.itemtype_id)
        if item:
            pid_identifier = PersistentIdentifier.get_by_object(
                pid_type='depid', object_type='rec', object_uuid=item.id)
            record = item
            
        if 'update_json_schema' in session:
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
            if deposit is not None:
                files = to_files_js(deposit)

        from weko_deposit.links import base_factory
        links = base_factory(pid)

    res_check = check_authority_action(activity_id, action_id)

    getargs = request.args
    ctx = {'community': None}
    community_id = ""
    if 'community' in getargs:
        comm = GetCommunity.get_community_by_id(request.args.get('community'))
        community_id = request.args.get('community')
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

    return render_template(
        'weko_workflow/activity_detail.html',
        render_widgets=True,
        activity=activity_detail,
        item=item,
        steps=steps,
        action_id=action_id,
        cur_step=cur_step,
        temporary_comment=temporary_comment,
        temporary_journal=temporary_journal,
        temporary_idf_grant=temporary_idf_grant,
        temporary_idf_grant_suffix=temporary_idf_grant_suffix,
        idf_grant_data=idf_grant_data,
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
        identifier_type=identifier_type,
        resource_type=resource_type,
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
    if users['deny'] and int(cur_user) in users['deny']:
        return 1
    if users['allow'] and int(cur_user) not in users['allow']:
        return 1
    for role in cur_role:
        if roles['deny'] and role.id in roles['deny']:
            return 1
        if roles['allow'] and role.id not in roles['allow']:
            return 1
    return 0


@blueprint.route(
    '/activity/action/<string:activity_id>/<int:action_id>',
    methods=['POST'])
@login_required
@check_authority
def next_action(activity_id='0', action_id=0):
    """Next action."""
    post_json = request.get_json()
    activity = dict(
        activity_id=activity_id,
        action_id=action_id,
        action_version=post_json.get('action_version'),
        action_status=ActionStatusPolicy.ACTION_DONE,
        commond=post_json.get('commond')
    )

    work_activity = WorkActivity()

    history = WorkActivityHistory()
    action = Action().get_action_detail(action_id)
    action_endpoint = action.action_endpoint

    if (1 == post_json.get('temporary_save') and
            action_endpoint != 'identifier_grant'):
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

    if 'begin_action' == action_endpoint:
        return jsonify(code=0, msg=_('success'))

    if 'end_action' == action_endpoint:
        work_activity.end_activity(activity)
        return jsonify(code=0, msg=_('success'))

    if 'approval' == action_endpoint:
        activity_obj = WorkActivity()
        activity_detail = activity_obj.get_activity_detail(activity_id)
        item = None
        if activity_detail is not None and activity_detail.item_id is not None:
            item = ItemsMetadata.get_record(id_=activity_detail.item_id)
            pid_identifier = PersistentIdentifier.get_by_object(
                pid_type='depid', object_type='rec', object_uuid=item.id)
            record_class = import_string('weko_deposit.api:WekoRecord')
            resolver = Resolver(pid_type='recid', object_type='rec',
                                getter=record_class.get_record)
            pid, approval_record = resolver.resolve(pid_identifier.pid_value)

            # TODO: Make private as default.
            # UpdateItem.publish(pid, approval_record)

    if 'item_link' == action_endpoint:
        relation_data = post_json.get('link_data'),
        activity_obj = WorkActivity()
        activity_detail = activity_obj.get_activity_detail(activity_id)
        item = ItemsMetadata.get_record(id_=activity_detail.item_id)
        pid_identifier = PersistentIdentifier.get_by_object(
            pid_type='depid', object_type='rec', object_uuid=item.id)
        record_class = import_string('weko_deposit.api:WekoRecord')
        resolver = Resolver(pid_type='recid', object_type='rec',
                            getter=record_class.get_record)
        pid, item_record = resolver.resolve(pid_identifier.pid_value)
        updated_item = UpdateItem()
        updated_item.set_item_relation(relation_data, item_record)

    # save pidstore_identifier to ItemsMetadata
    idf_grant = post_json.get('identifier_grant')
    if 'identifier_grant' == action_endpoint and idf_grant is not None:
        idf_grant_jalc_doi_manual = post_json.get(
            'identifier_grant_jalc_doi_suffix')
        idf_grant_jalc_cr_doi_manual = post_json.get(
            'identifier_grant_jalc_cr_doi_suffix')
        idf_grant_jalc_dc_doi_manual = post_json.get(
            'identifier_grant_jalc_dc_doi_suffix')

        # If is action identifier_grant, then save to to database
        identifier_grant = {
            'action_identifier_select': idf_grant,
            'action_identifier_jalc_doi': idf_grant_jalc_doi_manual,
            'action_identifier_jalc_cr_doi': idf_grant_jalc_cr_doi_manual,
            'action_identifier_jalc_dc_doi': idf_grant_jalc_dc_doi_manual
        }

        activity_obj = WorkActivity()
        activity_detail = activity_obj.get_activity_detail(activity_id)
        valid_error_list = item_metadata_validation(activity_detail.item_id, idf_grant)
        
        if valid_error_list:
            session['update_json_schema'] = valid_error_list
            previous_action(activity_id=activity_id, action_id=action_id, req=-1)
            return jsonify(code=0, msg=_('success'))
            # return jsonify(code = -1, msg=_('error'))
        else:
            return jsonify(code = -1, msg=_('error 2'))
        
        work_activity.create_or_update_action_identifier(
            activity_id=activity_id,
            action_id=action_id,
            identifier=identifier_grant
        )
        if post_json.get('temporary_save') != 1:
            pidstore_identifier_mapping(post_json, int(idf_grant), activity_id)
        else:
            return jsonify(code=0, msg=_('success'))

    rtn = history.create_activity_history(activity)
    if rtn is None:
        return jsonify(code=-1, msg=_('error'))
    # next action
    activity_detail = work_activity.get_activity_detail(activity_id)
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
            if activity_detail is not None and \
                    activity_detail.item_id is not None:
                record = WekoDeposit.get_record(activity_detail.item_id)
                if record is not None:
                    deposit = WekoDeposit(record, record.model)
                    deposit.publish()
                    # For current item: Make status Public as default
                    updated_item = UpdateItem()
                    updated_item.publish(record)
                    # For previous item: Update status to Private
                    current_pid = PersistentIdentifier.get_by_object(
                        pid_type='recid', object_type='rec',
                        object_uuid=activity_detail.item_id)
                    current_pv = PIDVersioning(child=current_pid)
                    if current_pv.exists and current_pv.previous is not None:
                        prev_record = WekoDeposit.get_record(
                            current_pv.previous.object_uuid)
                        if prev_record is not None:
                            updated_item.update_status(prev_record)
            activity.update(
                action_id=next_flow_action[0].action_id,
                action_version=next_flow_action[0].action_version,
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
            pid_type='doi', object_type='rec', object_uuid=activity_detail.item_id)
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
    if activity_detail is not None:
        cancel_item_id = activity_detail.item_id
        if cancel_item_id is None:
            pid_value = post_json.get('pid_value')
            if pid_value is not None:
                pid = PersistentIdentifier.get('recid', pid_value)
                cancel_item_id = pid.object_uuid
        if cancel_item_id is not None:
            cancel_record = WekoDeposit.get_record(cancel_item_id)
            if cancel_record is not None:
                cancel_deposit = WekoDeposit(
                    cancel_record, cancel_record.model)
                cancel_deposit.clear()
                # Remove draft child
                cancel_pid = PersistentIdentifier.get_by_object(
                    pid_type='recid', object_type='rec', object_uuid=cancel_item_id)
                cancel_pv = PIDVersioning(child=cancel_pid)
                if cancel_pv.exists:
                    previous_pid = cancel_pv.previous
                    if previous_pid is not None:
                        activity.update(dict(item_id=previous_pid.object_uuid))
                    cancel_pv.remove_child(cancel_pid)

    work_activity.upt_activity_action_status(
        activity_id=activity_id, action_id=action_id,
        action_status=ActionStatusPolicy.ACTION_CANCELED)

    rtn = work_activity.quit_activity(activity)

    if rtn is None:
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
            identifier_actionid = get_actionid('identifier_grant')
            identifier = activity.get_action_identifier_grant(
                activity_id,
                identifier_actionid)

            # Clear identifier in ItemMetadata
            pidstore_identifier_mapping(None, -1, activity_id)
            
            identifier['action_identifier_select'] = \
                IDENTIFIER_GRANT_IS_WITHDRAWING
            if identifier:
                activity.create_or_update_action_identifier(
                    activity_id,
                    identifier_actionid,
                    identifier)

            return jsonify(code=0,
                           msg=_('success'),
                           data={'redirect': url_for(
                               'weko_workflow.display_activity',
                               activity_id=activity_id)})
        else:
            return jsonify(code=-1, msg=_('Invalid password'))
    except BaseException:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
    return jsonify(code=-1, msg=_('Error!'))


@blueprint.route('/findDOI', methods=['POST'])
@login_required
def check_existed_doi():
    """Next action."""
    doi_link = request.get_json()
    data = {}
    data['isExistDOI'] = False
    data['isWithdrawnDoi'] = False
    data['code'] = 1
    data['msg'] = 'error'
    if doi_link is not None:
        isExistDOI = find_doi(doi_link)
        isWithdrawnDoi = is_withdrawn_doi(doi_link)
        if isExistDOI:
            data['isExistDOI'] = isExistDOI
            data['msg'] = _('This DOI has been used already for another item. '
                            'Please input another DOI.')
        elif isWithdrawnDoi:
            data['isWithdrawnDoi'] = isWithdrawnDoi
            data['msg'] = _(
                'This DOI was withdrawn. Please input another DOI.')
        else:
            data['msg'] = _('success')
        data['code'] = 0
    return jsonify(data)
