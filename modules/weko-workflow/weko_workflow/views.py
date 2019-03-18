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


from functools import wraps
from flask import Blueprint, abort, current_app, jsonify, render_template, \
    request, session, url_for
from flask_babelex import gettext as _
from flask_login import current_user, login_required
from invenio_accounts.models import Role, userrole
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier
from invenio_pidstore.resolver import Resolver
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.utils import import_string
from weko_records.api import ItemsMetadata

from .api import Action, Flow, WorkActivity, WorkActivityHistory, WorkFlow, UpdateItem, GetCommunity
from .models import ActionStatusPolicy, ActivityStatusPolicy

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
        community_id =comm.id
    else:
        activities = activity.get_activity_list()
    return render_template(
        'weko_workflow/activity_list.html',
        activities=activities, community_id=community_id, **ctx
    )

@blueprint.route('/iframe/success', methods=['GET'])
def iframe_success():
    """Renders an item register view.

    :return: The rendered template.
    """
    return render_template('weko_workflow/item_login_success.html')


@blueprint.route('/activity/new', methods=['GET'])
@login_required
def new_activity():
    workflow = WorkFlow()
    workflows = workflow.get_workflow_list()
    getargs = request.args
    ctx = {'community': None}
    community_id=""
    if 'community' in getargs:
        comm = GetCommunity.get_community_by_id(request.args.get('community'))
        ctx = {'community': comm}
        community_id = comm.id
    return render_template(
        'weko_workflow/workflow_list.html',
        workflows=workflows, community_id =community_id, **ctx
    )


@blueprint.route('/activity/init', methods=['POST'])
@login_required
def init_activity():
    post_activity = request.get_json()
    activity = WorkActivity()
    getargs = request.args
    if 'community' in getargs:
        rtn = activity.init_activity(post_activity, request.args.get('community'))
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
    activity = WorkActivity()
    activities = activity.get_activity_list()
    return render_template(
        'weko_workflow/activity_list.html',
        activities=activities
    )


@blueprint.route('/activity/detail/<string:activity_id>', methods=['GET'])
@login_required
def display_activity(activity_id=0):
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
    workflow_detail = workflow.get_workflow_by_id(
        activity_detail.workflow_id)
    if ActivityStatusPolicy.ACTIVITY_FINALLY != activity_detail.activity_status:
        activity_detail.activity_status_str = \
            request.args.get('status', 'ToDo')
    else:
        activity_detail.activity_status_str = _('End')
    cur_action = activity_detail.action
    action_endpoint = cur_action.action_endpoint
    action_id = cur_action.id
    temporary_comment = activity.get_activity_action_comment(
        activity_id=activity_id, action_id=action_id)
    if temporary_comment:
        temporary_comment = temporary_comment.action_comment
    cur_step = action_endpoint
    step_item_login_url = None
    approval_record = []
    pid = None
    if 'item_login' == action_endpoint or 'file_upload' == action_endpoint:
        activity_session = dict(
            activity_id=activity_id,
            action_id=activity_detail.action_id,
            action_version=cur_action.action_version,
            action_status=ActionStatusPolicy.ACTION_DOING,
            commond=''
        )
        session['activity_info'] = activity_session
        step_item_login_url = url_for(
            'weko_items_ui.iframe_index',
            item_type_id=workflow_detail.itemtype_id)
        if item:
            pid_identifier = PersistentIdentifier.get_by_object(
                pid_type='depid', object_type='rec', object_uuid=item.id)
            step_item_login_url = url_for(
                'invenio_deposit_ui.iframe_depid',
                pid_value=pid_identifier.pid_value)
    # if 'approval' == action_endpoint:
    if item:
        pid_identifier = PersistentIdentifier.get_by_object(
            pid_type='depid', object_type='rec', object_uuid=item.id)
        record_class = import_string('weko_deposit.api:WekoRecord')
        resolver = Resolver(pid_type='recid', object_type='rec',
                            getter=record_class.get_record)
        pid, approval_record = resolver.resolve(pid_identifier.pid_value)

    res_check = check_authority_action(activity_id,action_id)

    getargs = request.args
    ctx = {'community': None}
    community_id = ""
    if 'community' in getargs:
        comm = GetCommunity.get_community_by_id(request.args.get('community'))
        community_id=request.args.get('community')
        ctx = {'community': comm}
        community_id = comm.id
    return render_template(
        'weko_workflow/activity_detail.html',
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
        community_id=community_id,
        **ctx
    )


def check_authority(func):
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
    post_json = request.get_json()
    activity = dict(
        activity_id=activity_id,
        action_id=action_id,
        action_version=post_json.get('action_version'),
        action_status=ActionStatusPolicy.ACTION_DONE,
        commond=post_json.get('commond')
    )
    work_activity = WorkActivity()
    if 1 == post_json.get('temporary_save'):
        work_activity.upt_activity_action_comment(
            activity_id=activity_id,
            action_id=action_id,
            comment=post_json.get('commond')
        )
        return jsonify(code=0, msg=_('success'))
    history = WorkActivityHistory()
    action = Action().get_action_detail(action_id)
    action_endpoint = action.action_endpoint
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
            UpdateItem.publish(pid, approval_record)

    if 'item_link'==action_endpoint:
        relation_data= post_json.get('link_data'),
        activity_obj = WorkActivity()
        activity_detail = activity_obj.get_activity_detail(activity_id)
        item = ItemsMetadata.get_record(id_=activity_detail.item_id)
        pid_identifier = PersistentIdentifier.get_by_object(
            pid_type='depid', object_type='rec', object_uuid=item.id)
        record_class = import_string('weko_deposit.api:WekoRecord')
        resolver = Resolver(pid_type='recid', object_type='rec',
                            getter=record_class.get_record)
        pid, item_record = resolver.resolve(pid_identifier.pid_value)
        updateItem = UpdateItem()
        updateItem.set_item_relation(relation_data, item_record)

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
            activity.update(
                action_id=next_flow_action[0].action_id,
                action_version=next_flow_action[0].action_version,
            )
            work_activity.end_activity(activity)
        else:
            next_action_id = next_flow_action[0].action_id
            work_activity.upt_activity_action(
                activity_id=activity_id, action_id=next_action_id)
    return jsonify(code=0, msg=_('success'))


@blueprint.route(
    '/activity/action/<string:activity_id>/<int:action_id>'
    '/rejectOrReturn/<int:req>',
    methods=['POST'])
@login_required
@check_authority
def previous_action(activity_id='0', action_id=0, req=0):
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
    action = Action().get_action_detail(action_id)
    rtn = history.create_activity_history(activity)
    if rtn is None:
        return jsonify(code=-1, msg=_('error'))

    # next action
    activity_detail = work_activity.get_activity_detail(activity_id)
    flow = Flow()

    if req == 0:
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
            activity_id=activity_id, action_id=previous_action_id)
    return jsonify(code=0, msg=_('success'))
