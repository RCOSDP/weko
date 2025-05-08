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

from flask import abort, current_app, jsonify, request, url_for
from flask_admin import BaseView, expose
from flask_login import current_user
from flask_babelex import gettext as _
from invenio_accounts.models import Role, User
from invenio_db import db
from invenio_files_rest.models import Location
from invenio_i18n.ext import current_i18n
from invenio_mail.models import MailTemplates
from weko_admin.models import AdminSettings
from weko_index_tree.models import Index
from weko_records.api import ItemTypes
from weko_records.models import ItemTypeProperty

from .api import Action, Flow, WorkActivity, WorkFlow
from .config import WEKO_WORKFLOW_SHOW_HARVESTING_ITEMS
from .models import WorkflowRole
from .utils import recursive_get_specified_properties


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
        actions = self.get_actions()
        mail_templates = MailTemplates.get_templates()
        use_restricted_item = current_app.config.get('WEKO_ADMIN_USE_MAIL_TEMPLATE_EDIT', False)
        display_request_form = AdminSettings.get('items_display_settings', {}).get("display_request_form", False)
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
                action_list=actions,
                mail_templates=mail_templates,
                use_restricted_item=use_restricted_item,
                display_request_form=display_request_form,
                workflow_registrant_id = current_app.config.get("WEKO_WORKFLOW_ITEM_REGISTRANT_ID"),
                workflow_request_mail_id = current_app.config.get("WEKO_WORKFLOW_REQUEST_MAIL_ID")
            )
        UUID_PATTERN = re.compile(r'^[\da-f]{8}-([\da-f]{4}-){3}[\da-f]{12}$',
                                  re.IGNORECASE)
        if not UUID_PATTERN.match(flow_id):
            abort(404)
        workflow = Flow()
        flow = workflow.get_flow_detail(flow_id)
        specified_properties = self.get_specified_properties()

        if not self._check_auth(flow_id) :
            abort(403)

        return self.render(
            'weko_workflow/admin/flow_detail.html',
            flow_id=flow_id,
            flow=flow,
            flows=None,
            users=users,
            roles=roles,
            actions=flow.flow_actions,
            action_list=actions,
            specifed_properties=specified_properties,
            mail_templates=mail_templates,
            use_restricted_item=use_restricted_item,
            display_request_form=display_request_form,
            workflow_registrant_id = current_app.config.get("WEKO_WORKFLOW_ITEM_REGISTRANT_ID"),
            workflow_request_mail_id = current_app.config.get("WEKO_WORKFLOW_REQUEST_MAIL_ID")
        )

    @staticmethod
    def get_specified_properties():
        current_lang = current_i18n.language if current_i18n.language \
            in ['en', 'ja'] else 'en'
        result = ItemTypeProperty.query.filter_by(delflg=False).all()
        specified_properties = []
        for value in result:
            properties = value.form
            if properties:
                result = recursive_get_specified_properties(properties)
                if result:
                    title_i18n = value.form.get('title_i18n', {}).get(
                        current_lang, '')
                    specified_properties.append({
                        'value': result,
                        'text': title_i18n if title_i18n else value.name
                    })
        return specified_properties

    @staticmethod
    def update_flow(flow_id):
        post_data = request.get_json()
        workflow = Flow()
        try:
            workflow.upt_flow(flow_id, post_data)
            db.session.commit()
        except ValueError as ex:
            db.session.rollback()
            response = jsonify(msg=str(ex))
            response.status_code = 400
            return response
        except Exception as ex:
            db.session.rollback()
            response = jsonify(msg=str(ex))
            response.status_code = 500
            return response

        return jsonify(code=0, msg=_('Updated flow successfully.'))

    @expose('/<string:flow_id>', methods=['POST'])
    def new_flow(self, flow_id='0'):
        if flow_id != '0':
            if not self._check_auth(flow_id) :
                abort(403)
            return self.update_flow(flow_id)

        post_data = request.get_json()
        workflow = Flow()
        try:
            flow = workflow.create_flow(post_data)
            db.session.commit()
        except ValueError as ex:
            db.session.rollback()
            response = jsonify(msg=str(ex))
            response.status_code = 400
            return response
        except Exception as ex:
            db.session.rollback()
            response = jsonify(msg=str(ex))
            response.status_code = 500
            return response

        redirect_url = url_for('flowsetting.flow_detail', flow_id=flow.flow_id)
        return jsonify(code=0, msg='', data={'redirect': redirect_url})

    @expose('/<string:flow_id>', methods=['DELETE'])
    def del_flow(self, flow_id='0'):
        """Delete Flow info."""
        if '0' == flow_id:
            return jsonify(code=500, msg='No data to delete.',
                           data={'redirect': url_for('flowsetting.index')})
        
        if not self._check_auth(flow_id) :
            abort(403)

        code = 0
        msg = ''

        flow = Flow()
        flow_detail = flow.get_flow_detail(flow_id)
        if flow_detail:
            workflow = WorkFlow()
            workflows = workflow.get_workflow_by_flow_id(flow_detail.id)
            if workflows and len(workflows) > 0:
                code = 500
                # msg = 'Cannot be deleted because flow is used.'
                msg = _('Cannot be deleted because flow is used.')

            else:
                """Delete flow"""
                result = flow.del_flow(flow_id)
                code = result.get('code')
                msg = result.get('msg')

        return jsonify(code=code, msg=msg,
                       data={'redirect': url_for('flowsetting.index')})

    @staticmethod
    def get_actions():
        """Get Actions info."""
        actions = Action().get_action_list()
        action_list = list()
        for action in actions:
            if action.action_name in current_app.config[
                    'WEKO_WORKFLOW_ACTIONS']:
                action_list.append(action)
        return action_list

    @expose('/action/<string:flow_id>', methods=['POST'])
    def upt_flow_action(self, flow_id=0):
        """Update FlowAction Info."""
        if not self._check_auth(str(flow_id)) :
            abort(403)
        try:
            actions = request.get_json()
            workflow = Flow()
            workflow.upt_flow_action(flow_id, actions)
            flow = workflow.get_flow_detail(flow_id)
            actions = []
            for action in flow.flow_actions:
                actions.append({
                    'id': action.id,
                    'action_order': action.action_order,
                })
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return jsonify(
                code=400,
                actions=actions), 400
        return jsonify(
            code=0,
            msg=_('Updated flow action successfully'),
            actions=actions)

    @staticmethod
    def _check_auth(flow_id:str ):
        """  
        if the flow is used in open_restricted workflow , 
        the flow can Update by System Administrator.

        Args FlowDefine
        """
        if flow_id == '0':
            return True

        flow = Flow().get_flow_detail(flow_id)
        is_sysadmin = False
        for r in current_user.roles:
            if r.name in current_app.config['WEKO_SYS_USER']:
                is_sysadmin =True
                break
        if not is_sysadmin :
            wfs:list = WorkFlow().get_workflow_by_flow_id(flow.id)
            if 0 < len(list(filter(lambda wf : wf.open_restricted ,wfs ))):
                return False
        return True

class WorkFlowSettingView(BaseView):
    MULTI_LANGUAGE = {
        "display": {
            "en": "Display",
            "ja": "表示"
        },
        "hide": {
            "en": "Hide",
            "ja": "非表示",
        },
        "display_hide": {
            "en": "Display/Hide",
            "ja": "表示/非表示",
        }
    }

    @expose('/', methods=['GET'])
    def index(self):
        """Get flow list info.

        :return:
        """
        workflow = WorkFlow()
        workflows = workflow.get_workflow_list()
        role = Role.query.all()
        for wf in workflows:
            index_tree = Index().get_index_by_id(wf.index_tree_id)
            wf.index_tree = index_tree
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

        display_label = self.get_language_workflows("display")

        return self.render(
            'weko_workflow/admin/workflow_list.html',
            workflows=workflows,
            display_label=display_label
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
        index_list = Index().get_all()
        location_list = Location.query.order_by(Location.id.asc()).all()
        hide = []
        role = Role.query.all()
        display_label = self.get_language_workflows("display")
        hide_label = self.get_language_workflows("hide")
        display_hide = self.get_language_workflows("display_hide")

        # the workflow that open_restricted is true can update by system administrator only
        is_sysadmin = False
        for r in current_user.roles:
            if r.name in current_app.config['WEKO_SYS_USER']:
                is_sysadmin =True
                break

        if '0' == workflow_id:
            """Create new workflow"""
            return self.render(
                'weko_workflow/admin/workflow_detail.html',
                workflow=None,
                itemtype_list=itemtype_list,
                flow_list=flow_list,
                index_list=index_list,
                location_list=location_list,
                hide_list=hide,
                display_list=role,
                display_label=display_label,
                hide_label=hide_label,
                display_hide_label=display_hide,
                is_sysadmin=is_sysadmin,
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
        
        if workflows.open_restricted and not is_sysadmin:
            abort(403)

        return self.render(
            'weko_workflow/admin/workflow_detail.html',
            workflow=workflows,
            itemtype_list=itemtype_list,
            flow_list=flow_list,
            index_list=index_list,
            location_list=location_list,
            hide_list=hide,
            display_list=display,
            display_label=display_label,
            hide_label=hide_label,
            display_hide_label=display_hide,
            is_sysadmin=is_sysadmin
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
            flow_id=json_data.get('flow_id', 0),
            index_tree_id=json_data.get('index_id'),
            location_id=json_data.get('location_id'),
            open_restricted=json_data.get('open_restricted', False),
            is_gakuninrdm=json_data.get('is_gakuninrdm')
        )
        workflow = WorkFlow()
        try:
            if '0' == workflow_id:
                """Create new workflow"""
                form_workflow.update(
                    flows_id=uuid.uuid4()
                )
                workflow.create_workflow(form_workflow)
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
                self.save_workflow_role(form_workflow.get('id'), list_hide)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return jsonify(code=400, msg='Error'), 400
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
        current_app.logger.error("wf_id:{}".format(wf_id))
        # ['4']
        current_app.logger.error("list_hide:{}".format(list_hide))
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

    @classmethod
    def get_language_workflows(cls, key):
        """Get language workflows.

        :return:
        """
        cur_language = current_i18n.language
        language = cur_language if cur_language in ['en', 'ja'] else "en"
        return cls.MULTI_LANGUAGE[key].get(language)


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
