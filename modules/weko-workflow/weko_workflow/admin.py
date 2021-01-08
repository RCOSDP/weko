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

import re
import uuid

from flask import abort, jsonify, request, url_for
from flask_admin import BaseView, expose
from flask_babelex import gettext as _
from flask_login import current_user
from invenio_accounts.models import Role, User
from invenio_db import db
from weko_records.api import ItemTypes

from .api import Action, Flow, WorkActivity, WorkFlow
from .config import WEKO_WORKFLOW_SHOW_HARVESTING_ITEMS
from .models import WorkflowRole


class FlowSettingView(BaseView):
    @expose('/', methods=['GET'])
    def index(self):
        """Get flow list info.

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
        """Get flow detail info.

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
        UUID_PATTERN = re.compile(r'^[\da-f]{8}-([\da-f]{4}-){3}[\da-f]{12}$',
                                  re.IGNORECASE)
        if not UUID_PATTERN.match(flow_id):
            abort(404)
        workflow = Flow()
        flow = workflow.get_flow_detail(flow_id)
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

    @staticmethod
    def update_flow(flow_id):
        post_data = request.get_json()
        workflow = Flow()
        try:
            workflow.upt_flow(flow_id, post_data)
        except ValueError as ex:
            response = jsonify(msg=str(ex))
            response.status_code = 400
            return response

        return jsonify(code=0, msg=_('Updated flow successfully.'))

    @expose('/<string:flow_id>', methods=['POST'])
    def new_flow(self, flow_id='0'):
        if flow_id != '0':
            return self.update_flow(flow_id)

        post_data = request.get_json()
        workflow = Flow()
        try:
            flow = workflow.create_flow(post_data)
        except ValueError as ex:
            response = jsonify(msg=str(ex))
            response.status_code = 400
            return response

        redirect_url = url_for('flowsetting.flow_detail', flow_id=flow.flow_id)
        return jsonify(code=0, msg='', data={'redirect': redirect_url})

    @expose('/<string:flow_id>', methods=['DELETE'])
    def del_flow(self, flow_id='0'):
        """Delete Flow info."""
        if '0' == flow_id:
            return jsonify(code=500, msg='No data to delete.',
                           data={'redirect': url_for('flowsetting.index')})

        code = 0
        msg = ''

        flow = Flow()
        flow_detail = flow.get_flow_detail(flow_id)
        if flow_detail:
            workflow = WorkFlow()
            workflows = workflow.get_workflow_by_flow_id(flow_detail.id)
            if workflows and len(workflows) > 0:
                code = 500
                msg = 'Cannot be deleted because flow is used.'
            else:
                """Delete flow"""
                result = flow.del_flow(flow_id)
                code = result.get('code')
                msg = result.get('msg')

        return jsonify(code=code, msg=msg,
                       data={'redirect': url_for('flowsetting.index')})

    @expose('/action/<string:flow_id>', methods=['POST'])
    def upt_flow_action(self, flow_id=0):
        """Update FlowAction Info."""
        actions = request.get_json()
        workflow = Flow()
        workflow.upt_flow_action(flow_id, actions)
        return jsonify(code=0, msg=_('Updated flow action successfully'))


class WorkFlowSettingView(BaseView):
    @expose('/', methods=['GET'])
    def index(self):
        """Get flow list info.

        :return:
        """
        workflow = WorkFlow()
        workflows = workflow.get_workflow_list()
        role = Role.query.all()
        for wf in workflows:
            list_hide = Role.query.outerjoin(WorkflowRole) \
                .filter(WorkflowRole.workflow_id == wf.id) \
                .filter(WorkflowRole.role_id == Role.id) \
                .all()
            if list_hide:
                displays, hides = self.get_name_display_hide(list_hide, role)
            else:
                displays = [x.name for x in role]
                hides = []
            wf.display = ',<br>'.join(displays)
            wf.hide = ',<br>'.join(hides)

        return self.render(
            'weko_workflow/admin/workflow_list.html',
            workflows=workflows
        )

    @expose('/<string:workflow_id>', methods=['GET'])
    def workflow_detail(self, workflow_id='0'):
        """Get workflow info.

        :return:
        """
        if WEKO_WORKFLOW_SHOW_HARVESTING_ITEMS:
            itemtype_list = ItemTypes.get_latest()
        else:
            itemtype_list = ItemTypes.get_latest_custorm_harvesting()
        flow_api = Flow()
        flow_list = flow_api.get_flow_list()
        display = []
        hide = []
        role = Role.query.all()
        if '0' == workflow_id:
            """Create new workflow"""
            return self.render(
                'weko_workflow/admin/workflow_detail.html',
                workflow=None,
                itemtype_list=itemtype_list,
                flow_list=flow_list,
                hide_list=hide,
                display_list=role
            )
        """Update the workflow info"""
        workflow = WorkFlow()
        workflows = workflow.get_workflow_detail(workflow_id)
        hide = Role.query.outerjoin(WorkflowRole) \
            .filter(WorkflowRole.workflow_id == workflows.id) \
            .filter(WorkflowRole.role_id == Role.id) \
            .all()
        if hide:
            display = self.get_displays(hide, role)
        else:
            display = role
            hide = []
        return self.render(
            'weko_workflow/admin/workflow_detail.html',
            workflow=workflows,
            itemtype_list=itemtype_list,
            flow_list=flow_list,
            hide_list=hide,
            display_list=display
        )

    @expose('/<string:workflow_id>', methods=['POST', 'PUT'])
    def update_workflow(self, workflow_id='0'):
        """Update workflow info.

        :return:
        """
        json_data = request.get_json()
        list_hide = json_data.get('list_hide', [])
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
            if len(list_hide) > 0:
                workflow_detail = workflow.get_workflow_by_flows_id(
                    form_workflow.get('flows_id'))
                self.save_workflow_role(workflow_detail.id, list_hide)
        else:
            """Update the workflow info"""
            form_workflow.update(
                id=json_data.get('id', None),
                flows_id=workflow_id
            )
            workflow.upt_workflow(form_workflow)
            if len(list_hide) > 0:
                self.save_workflow_role(form_workflow.get('id'), list_hide)
        return jsonify(code=0, msg='',
                       data={'redirect': url_for('workflowsetting.index')})

    @expose('/<string:workflow_id>', methods=['DELETE'])
    def delete_workflow(self, workflow_id='0'):
        """Update workflow info.

        :return:
        """
        workflow = WorkFlow()
        if '0' == workflow_id:
            return jsonify(code=500, msg='No data to delete.',
                           data={'redirect': url_for('workflowsetting.index')})

        code = 0
        msg = ''
        delete_flag = True

        workflow_detail = workflow.get_workflow_by_flows_id(workflow_id)
        if workflow_detail:
            activity = WorkActivity()
            activitys = activity.get_activity_by_workflow_id(workflow_detail.id)
            if activitys and len(activitys) > 0:
                for i in activitys:
                    if i.activity_status not in ['F', 'C']:
                        delete_flag = False
                        break

            if delete_flag:
                """Delete new workflow"""
                result = workflow.del_workflow(workflow_id)
                code = result.get('code')
                msg = result.get('msg')
            else:
                code = 500
                msg = 'Cannot be deleted because workflow is used.'

        return jsonify(code=code, msg=msg,
                       data={'redirect': url_for('workflowsetting.index')})

    @classmethod
    def get_workflows_by_roles(cls, workflows):
        """Get list workflow.

        :param workflows.

        :return: wfs.
        """
        wfs = []
        current_user_roles = [role.id for role in current_user.roles]
        if isinstance(workflows, list):
            role = Role.query.all()
            while workflows:
                tmp = workflows.pop(0)
                list_hide = Role.query.outerjoin(WorkflowRole) \
                    .filter(WorkflowRole.workflow_id == tmp.id) \
                    .filter(WorkflowRole.role_id == Role.id) \
                    .all()
                displays = cls.get_displays(list_hide, role)
                if any(x.id in current_user_roles for x in displays):
                    wfs.append(tmp)
        return wfs

    @classmethod
    def get_name_display_hide(cls, list_hide, role):
        """Get workflow role: displays, hides.

        :param role:
        :param list_hide:

        :return: displays, hides.
        """
        displays = []
        hides = []
        if isinstance(role, list):
            for tmp in role:
                if not any(x.id == tmp.id for x in list_hide):
                    displays.append(tmp.name)
                else:
                    hides.append(tmp.name)
        return displays, hides

    @classmethod
    def get_displays(cls, list_hide, role):
        """Get workflow role: displays.

        :param role:
        :param list_hide:

        :return: displays.
        """
        displays = []
        if isinstance(role, list):
            for tmp in role:
                if not any(x.id == tmp.id for x in list_hide):
                    displays.append(tmp)
        return displays

    @classmethod
    def save_workflow_role(cls, wf_id, list_hide):
        """Update workflow role.

        :return:
        """
        with db.session.begin_nested():
            db.session.query(WorkflowRole).filter_by(
                workflow_id=wf_id).delete()
            if isinstance(list_hide, list):
                while list_hide:
                    tmp = list_hide.pop(0)
                    wfrole = dict(
                        workflow_id=wf_id,
                        role_id=tmp
                    )
                    db.session.execute(WorkflowRole.__table__.insert(), wfrole)
        db.session.commit()


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
