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

"""WEKO3 module docstring."""

import uuid
from flask import abort, jsonify, request, url_for
from flask_admin import BaseView, expose
from flask_babelex import gettext as _
from invenio_accounts.models import Role, User

from weko_records.api import ItemTypes

from .api import Action, Flow, WorkFlow


class FlowSettingView(BaseView):
    @expose('/', methods=['GET'])
    def index(self):
        """
        Get flow list info
        :return:
        """
        workflow = Flow()
        flows = workflow.get_flow_list()
        return self.render(
            'weko_workflow/admin/flow_list.html',
            flows=flows
        )

    @expose('/<string:flow_id>', methods=['GET'])
    def flow_detail(self, flow_id='0'):
        """
        Get flow detail info
        :param flow_id:
        :return:
        """
        users = User.query.filter_by(active=True).all()
        roles = Role.query.all()
        action = Action()
        actions = action.get_action_list()
        if '0' == flow_id:
            flow = None
            return self.render(
                'weko_workflow/admin/flow_detail.html',
                flow_id=flow_id,
                flow=flow,
                flows=None,
                users=users,
                roles=roles,
                actions=None,
                action_list=actions
            )
        workflow = Flow()
        flow = workflow.get_flow_detail(flow_id)
        if not flow:
            abort(400)
        return self.render(
            'weko_workflow/admin/flow_detail.html',
            flow_id=flow_id,
            flow=flow,
            flows=None,
            users=users,
            roles=roles,
            actions=flow.flow_actions,
            action_list=actions
        )

    @expose('/<string:flow_id>', methods=['POST'])
    def new_flow(self, flow_id='0'):
        post_data = request.get_json()
        workflow = Flow()
        if '0' == flow_id:
            """Create new flow info"""
            flow = workflow.create_flow(post_data)
            return jsonify(code=0, msg='',
                           data={
                               'redirect': url_for(
                                   'flowsetting.flow_detail',
                                   flow_id=flow.flow_id)
                           })
        workflow.upt_flow(flow_id, post_data)
        return jsonify(code=0, msg=_('Update flow successfully.'))

    @expose('/<string:flow_id>', methods=['DELETE'])
    def del_flow(self, flow_id='0'):
        """Delete Flow info"""
        workflow = Flow()
        workflow.del_flow(flow_id)
        return jsonify(code=0, msg='',
                       data={'redirect': url_for('flowsetting.index')})

    @expose('/action', methods=['GET'])
    def action(self):
        """
        Get Action list info
        :return:
        """
        action = Action()
        actions = action.get_action_list()
        return self.render(
            'weko_workflow/admin/action_list.html',
            actions=actions
        )

    @expose('/action/<string:action_id>', methods=['GET'])
    def action_detail(self, action_id):
        """
        Get Action detail info
        :param action_id:
        :return:
        """
        pass

    @expose('/action/<string:flow_id>', methods=['POST'])
    def upt_flow_action(self, flow_id=0):
        """Update FlowAction Info"""
        actions = request.get_json()
        workflow = Flow()
        workflow.upt_flow_action(flow_id, actions)
        return jsonify(code=0, msg=_('Update flow action successfully'))


class WorkFlowSettingView(BaseView):
    @expose('/', methods=['GET'])
    def index(self):
        """
        Get flow list info
        :return:
        """
        workflow = WorkFlow()
        workflows = workflow.get_workflow_list()
        return self.render(
            'weko_workflow/admin/workflow_list.html',
            workflows=workflows
        )

    @expose('/<string:workflow_id>', methods=['GET'])
    def workflow_detail(self, workflow_id='0'):
        """
        Get workflow info
        :return:
        """
        itemtype_list = ItemTypes.get_latest()
        flow_api = Flow()
        flow_list = flow_api.get_flow_list()
        if '0' == workflow_id:
            """Create new workflow"""
            return self.render(
                'weko_workflow/admin/workflow_detail.html',
                workflow=None,
                itemtype_list=itemtype_list,
                flow_list=flow_list
            )
        """Update the workflow info"""
        workflow = WorkFlow()
        workflows = workflow.get_workflow_detail(workflow_id)
        return self.render(
            'weko_workflow/admin/workflow_detail.html',
            workflow=workflows,
            itemtype_list=itemtype_list,
            flow_list=flow_list
        )

    @expose('/<string:workflow_id>', methods=['POST', 'PUT'])
    def update_workflow(self, workflow_id='0'):
        """
        Update workflow info
        :return:
        """
        json_data = request.get_json()
        form_workflow = dict(
            flows_name=json_data.get('flows_name', None),
            itemtype_id=json_data.get('itemtype_id', 0),
            flow_id=json_data.get('flow_id', 0)
        )
        workflow = WorkFlow()
        if '0' == workflow_id:
            """Create new workflow"""
            form_workflow.update(
                flows_id=uuid.uuid4()
            )
            workflow.create_workflow(form_workflow)
        else:
            """Update the workflow info"""
            form_workflow.update(
                id=json_data.get('id', None),
                flows_id=workflow_id
            )
            workflow.upt_workflow(form_workflow)
        return jsonify(code=0, msg='',
                       data={'redirect': url_for('workflowsetting.index')})

    @expose('/<string:workflow_id>', methods=['DELETE'])
    def delete_workflow(self, workflow_id='0'):
        """
        Update workflow info
        :return:
        """
        workflow = WorkFlow()
        if '0' != workflow_id:
            """Delete new workflow"""
            workflow.del_workflow(workflow_id)
        return jsonify(code=0, msg='',
                       data={'redirect': url_for('workflowsetting.index')})


workflow_adminview = {
    'view_class': WorkFlowSettingView,
    'kwargs': {
        'category': _('WorkFlow'),
        'name': _('WorkFlow List'),
        'endpoint': 'workflowsetting'
    }
}

flow_adminview = {
    'view_class': FlowSettingView,
    'kwargs': {
        'category': _('WorkFlow'),
        'name': _('Flow List'),
        'endpoint': 'flowsetting'
    }
}

__all__ = (
    'flow_adminview',
    'workflow_adminview',
)
