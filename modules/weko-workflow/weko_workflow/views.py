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


from flask import Blueprint, jsonify, render_template, request, session, url_for
from flask_babelex import gettext as _
from flask_login import login_required
from invenio_pidstore.models import PersistentIdentifier
from weko_records.api import ItemsMetadata

from .api import WorkActivity, WorkActivityHistory, WorkFlow

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
    activities = activity.get_activity_list()
    return render_template(
        'weko_workflow/activity_list.html',
        activities=activities
    )


@blueprint.route('/activity/new', methods=['GET'])
@login_required
def new_activity():
    workflow = WorkFlow()
    workflows = workflow.get_workflow_list()
    return render_template(
        'weko_workflow/workflow_list.html',
        workflows=workflows
    )


@blueprint.route('/activity/init', methods=['POST'])
@login_required
def init_activity():
    post_activity = request.get_json()
    activity = WorkActivity()
    rtn = activity.init_activity(post_activity)
    if rtn is None:
        return jsonify(code=-1, msg='error')
    return jsonify(code=0, msg='success',
                   data={'redirect': url_for(
                       'weko_workflow.list_activity')})


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
        item = ItemsMetadata.get_record(id_=activity_detail.item_id)
    steps = activity.get_activity_steps(activity_id)
    history = WorkActivityHistory()
    histories = history.get_activity_history_list(activity_id)
    return render_template(
        'weko_workflow/activity_detail.html',
        activity=activity_detail,
        item=item,
        steps=steps,
        histories=histories
    )


@blueprint.route(
    '/activity/action/<string:activity_id>/<int:action_id>',
    methods=['POST'])
def next_action(activity_id='0', action_id=0):
    post_json = request.get_json()
    history = WorkActivityHistory()
    activity = dict(
        activity_id=activity_id,
        action_id=action_id,
        action_version=post_json.get('action_version'),
        commond=post_json.get('commond')
    )
    rtn = history.create_activity_history(activity)
    if rtn is None:
        return jsonify(code=-1, msg='error')
    session['activity_info'] = activity
    activity = WorkActivity()
    activity_detail = activity.get_activity_detail(activity_id)
    redirect_url = '/'
    if activity_detail.item_id:
        pid = PersistentIdentifier.get_by_object(
            pid_type='recid', object_type='rec',
            object_uuid=activity_detail.item_id)
        return jsonify(code=0, msg='success',
                       data={'redirect': url_for(
                           'invenio_records_ui.recid',
                           pid_value=pid.pid_value)})
    workflow = WorkFlow()
    itemtype_id = workflow.get_workflow_by_id(
        activity_detail.workflow_id).itemtype_id
    return jsonify(code=0, msg='success',
                   data={'redirect': url_for(
                       'weko_items_ui.index', item_type_id=itemtype_id)})
