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

from datetime import datetime
from flask import current_app, request, session, url_for
from flask_login import current_user
from invenio_accounts.models import User
from invenio_db import db
from sqlalchemy import asc,desc
from sqlalchemy.orm.exc import NoResultFound
from weko_records.models import ItemMetadata

from .models import Action as _Action
from .models import Activity as _Activity
from .models import ActivityAction
from .models import ActivityHistory
from .models import FlowDefine as _Flow
from .models import FlowAction as _FlowAction
from .models import FlowActionRole as _FlowActionRole
from .models import WorkFlow as _WorkFlow
from .models import ActionStatusPolicy, ActionCommentPolicy, \
    ActivityStatusPolicy, FlowStatusPolicy

class Flow(object):
    """Operated on the Flow"""

    def create_flow(self, flow):
        """
        Create new flow
        :param flow:
        :return:
        """
        try:
            with db.session.no_autoflush:
                action_start = _Action.query.filter_by(
                    action_endpoint='begin_action').one_or_none()
                action_end = _Action.query.filter_by(
                    action_endpoint='end_action').one_or_none()
            _flow = _Flow(
                flow_id=uuid.uuid4(),
                flow_name=flow.get('flow_name'),
                flow_user=current_user.get_id()
            )
            _flowaction_start = _FlowAction(
                flow_id=_flow.flow_id,
                action_id=action_start.id,
                action_version=action_start.action_version,
                action_order=1
            )
            _flowaction_end = _FlowAction(
                flow_id=_flow.flow_id,
                action_id=action_end.id,
                action_version=action_end.action_version,
                action_order=2
            )
            with db.session.begin_nested():
                db.session.add(_flow)
                db.session.add(_flowaction_start)
                db.session.add(_flowaction_end)
            db.session.commit()
            return _flow
        except Exception as ex:
            current_app.logger.exception(str(ex))
            db.session.rollback()
            return None

    def upt_flow(self, flow_id, flow):
        """
        Update flow info
        :param flow_id:
        :param flow:
        :return:
        """
        try:
            with db.session.begin_nested():
                _flow = _Flow.query.filter_by(
                    flow_id=flow_id).one_or_none()
                if _flow:
                    _flow.flow_name = flow.get('flow_name')
                    _flow.flow_user = current_user.get_id()
                    db.session.merge(_flow)
            db.session.commit()
            return _flow
        except Exception as ex:
            current_app.logger.exception(str(ex))
            db.session.rollback()
            return None

    def get_flow_list(self):
        """
        get flow list info
        :return:
        """
        with db.session.no_autoflush:
            query = _Flow.query.order_by(asc(_Flow.flow_id))
            return query.all()

    def get_flow_detail(self, flow_id):
        """
        get flow detail info
        :param flow_id:
        :return:
        """
        with db.session.no_autoflush:
            query = _Flow.query.filter_by(
                flow_id=flow_id)
            flow_detail = query.one_or_none()
            for action in flow_detail.flow_actions:
                action_roles = _FlowActionRole.query.filter_by(
                    flow_action_id=action.id).first()
                action.action_role = action_roles if action_roles else None
            return flow_detail

    def del_flow(self, flow_id):
        """
        Delete flow info
        :param flow_id:
        :return:
        """
        with db.session.begin_nested():
            _FlowAction.query.filter_by(
                flow_id=flow_id).delete(synchronize_session=False)
            _Flow.query.filter_by(
                flow_id=flow_id).delete(synchronize_session=False)
        db.session.commit()
        return True

    def upt_flow_action(self, flow_id, actions):
        """Update FlowAction Info"""
        with db.session.begin_nested():
            for order, action in enumerate(actions):
                flowaction_filter = _FlowAction.query.filter_by(
                    flow_id=flow_id, action_id=action.get('id'))
                if action.get('action', None) == 'DEL':
                    flowaction_id = flowaction_filter.one_or_none().id
                    _FlowActionRole.query.filter_by(
                        flow_action_id=flowaction_id).delete()
                    flowaction_filter.delete()
                    continue
                flowaction = flowaction_filter.one_or_none()
                if flowaction is None:
                    """new"""
                    flowaction = _FlowAction(
                        flow_id=flow_id,
                        action_id=action.get('id'),
                        action_order=order + 1,
                        action_version=action.get('version')
                    )
                    _flow = _Flow.query.filter_by(flow_id=flow_id).one_or_none()
                    _flow.flow_status = FlowStatusPolicy.AVAILABLE
                    db.session.add(flowaction)
                else:
                    """Update"""
                    flowaction.action_order = order + 1
                    db.session.merge(flowaction)
                _FlowActionRole.query.filter_by(
                    flow_action_id=flowaction.id).delete()
                flowactionrole = _FlowActionRole(
                    flow_action_id=flowaction.id,
                    action_role=action.get(
                        'role') if '0' != action.get('role') else None,
                    action_role_exclude=action.get(
                        'role_deny') if '0' != action.get('role') else False,
                    action_user=action.get(
                        'user') if '0' != action.get('user') else None,
                    action_user_exclude=action.get(
                        'user_deny') if '0' != action.get('user') else False
                )
                if flowactionrole.action_role or flowactionrole.action_user:
                    db.session.add(flowactionrole)
        db.session.commit()

    def get_next_flow_action(self, flow_id, cur_action_id):
        """
        return next action info
        :param flow_id:
        :param cur_action_id:
        :return:
        """
        with db.session.no_autoflush:
            cur_action = _FlowAction.query.filter_by(
                flow_id=flow_id).filter_by(
                action_id=cur_action_id).one_or_none()
            if cur_action:
                next_action_order = cur_action.action_order + 1
                next_action = _FlowAction.query.filter_by(
                    flow_id=flow_id).filter_by(
                    action_order=next_action_order).all()
                return next_action
        return None

    def get_previous_flow_action(self, flow_id, cur_action_id):
        """
        return next action info
        :param flow_id:
        :param cur_action_id:
        :return:
        """
        with db.session.no_autoflush:
            cur_action = _FlowAction.query.filter_by(
                flow_id=flow_id,
                action_id=cur_action_id).one_or_none()
            if cur_action and cur_action.action_order > 1:
                previous_action_order = cur_action.action_order - 1
                previous_action = _FlowAction.query.filter_by(
                    flow_id=flow_id).filter_by(
                    action_order=previous_action_order).all()
                return previous_action
            return None


class WorkFlow(object):
    """Operated on the WorkFlow"""
    def create_workflow(self, workflow):
        """
        Create new workflow
        :param workflow:
        :return:
        """
        assert workflow
        try:
            with db.session.begin_nested():
                db.session.execute(_WorkFlow.__table__.insert(), workflow)
            db.session.commit()
            return workflow
        except Exception as ex:
            db.session.rollback()
            current_app.logger.exception(str(ex))
            return None

    def upt_workflow(self, workflow):
        """
        Update workflow info
        :param workflow:
        :return:
        """
        assert workflow
        try:
            with db.session.begin_nested():
                _workflow = _WorkFlow.query.filter_by(
                    flows_id=workflow.get('flows_id')
                ).one_or_none()
                if _workflow:
                    _workflow.flows_name = workflow.get('flows_name')
                    _workflow.itemtype_id = workflow.get('itemtype_id')
                    _workflow.flow_id = workflow.get('flow_id')
                    db.session.merge(_workflow)
            db.session.commit()
            return _workflow
        except Exception as ex:
            db.session.rollback()
            current_app.logger.exception(str(ex))
            return None

    def get_workflow_list(self):
        """
        get workflow list info
        :return:
        """
        with db.session.no_autoflush:
            query = _WorkFlow.query.order_by(asc(_WorkFlow.flows_id))
            return query.all()

    def get_workflow_detail(self, workflow_id):
        """
        get workflow detail info
        :param workflow_id:
        :return:
        """
        with db.session.no_autoflush:
            query = _WorkFlow.query.filter_by(
                flows_id=workflow_id)
            return query.one_or_none()

    def get_workflow_by_id(self, workflow_id):
        """
        get workflow detail info
        :param workflow_id:
        :return:
        """
        with db.session.no_autoflush:
            query = _WorkFlow.query.filter_by(
                id=workflow_id)
            return query.one_or_none()

    def del_workflow(self, workflow_id):
        """
        Delete flow info
        :param workflow_id:
        :return:
        """
        with db.session.no_autoflush:
            query = _WorkFlow.query.filter_by(
                flows_id=workflow_id)
            query.delete(synchronize_session=False)
        db.session.commit()


class Action(object):
    """Operated on the Action"""
    def create_action(self, action):
        """
        Create new action info
        :param action:
        :return:
        """
        pass

    def upt_action(self, action):
        """
        Update action info
        :param action:
        :return:
        """
        pass

    def get_action_list(self, is_deleted=False):
        """
        Get action list info
        :param is_deleted:
        :return:
        """
        with db.session.no_autoflush:
            query = _Action.query.order_by(asc(_Action.id))
            return query.all()

    def get_action_detail(self, action_id):
        """
        Get detail info of action
        :param action_id:
        :return:
        """
        with db.session.no_autoflush:
            query = _Action.query.filter_by(id=action_id)
            return query.one_or_none()

    def del_action(self, action_id):
        """
        Delete the action info
        :param action_id:
        :return:
        """
        pass


class ActionStatus(object):
    """Operated on the ActionStatus"""
    def create_action_status(self, action_status):
        """
        Create new action status info
        :param action_status:
        :return:
        """
        pass

    def upt_action_status(self, action_status):
        """
        Update action status info
        :param action_status:
        :return:
        """
        pass

    def get_action_status_list(self, is_deleted=False):
        """
        Get action status list info
        :param is_deleted:
        :return:
        """
        pass

    def get_action_status_detail(self, action_status_id):
        """
        Get detail info of action status
        :param action_status_id:
        :return:
        """
        pass

    def del_action_status(self, action_status_id):
        """
        Delete the action status info
        :param action_status_id:
        :return:
        """
        pass


class WorkActivity(object):
    """Operated on the Activity"""

    def init_activity(self, activity, community_id=None):
        """
        Create new activity
        :param activity:
        :return:
        """
        try:
            action_id = 0
            next_action_id = 0
            with db.session.no_autoflush:
                action = _Action.query.filter_by(
                    action_endpoint='begin_action').one_or_none()
                if action is not None:
                    action_id = action.id
                flow_define = _Flow.query.filter_by(
                    id=activity.get('flow_id')).one_or_none()
                if flow_define:
                    flow_actions = _FlowAction.query.filter_by(
                        flow_id=flow_define.flow_id).order_by(
                        asc(_FlowAction.action_order)).all()
                    if flow_actions and len(flow_actions) >= 2:
                        next_action_id = flow_actions[1].action_id
            db_activity = _Activity(
                activity_id='A' + str(
                    datetime.utcnow().timestamp()).split('.')[0],
                workflow_id=activity.get('workflow_id'),
                flow_id=activity.get('flow_id'),
                action_id=next_action_id,
                action_status=ActionStatusPolicy.ACTION_BEGIN,
                activity_login_user=current_user.get_id(),
                activity_update_user=current_user.get_id(),
                activity_status=ActivityStatusPolicy.ACTIVITY_MAKING,
                activity_start=datetime.utcnow(),
                activity_community_id=community_id
            )
            db_history = ActivityHistory(
                activity_id=db_activity.activity_id,
                action_id=action_id,
                action_version=action.action_version,
                action_status=ActionStatusPolicy.ACTION_DONE,
                action_user=current_user.get_id(),
                action_date=db_activity.activity_start,
                action_comment=ActionCommentPolicy.BEGIN_ACTION_COMMENT
            )

            with db.session.begin_nested():
                db.session.add(db_activity)
                db.session.add(db_history)

                for flow_action in flow_actions:
                    db_activity_action = ActivityAction(
                        activity_id= db_activity.activity_id,
                        action_id=flow_action.action_id,
                        action_status=ActionStatusPolicy.ACTION_DONE,
                    )
                    db.session.add(db_activity_action)

        except Exception as ex:
            db.session.rollback()
            current_app.logger.exception(str(ex))
            return None
        else:
            db.session.commit()
            return db_activity

    def upt_activity_action(self, activity_id, action_id):
        """
        Update activity info
        :param activity_id:
        :param action_id:
        :return:
        """
        with db.session.begin_nested():
            activity = _Activity.query.filter_by(
                activity_id=activity_id).one_or_none()
            activity.action_id = action_id
            activity.action_status = ActionStatusPolicy.ACTION_DOING
            db.session.merge(activity)
        db.session.commit()

    # add by ryuu sta
    def upt_activity_action_status(self, activity_id, action_id, action_status):
        """
        Update activity info
        :param activity_id:
        :param action_id:
        :param action_status:
        :return:
        """
        with db.session.begin_nested():
            activity_action = ActivityAction.query.filter_by(
                activity_id=activity_id,
                action_id=action_id,).one_or_none()
            activity_action.action_status = action_status
            db.session.merge(activity_action)
        db.session.commit()

    def upt_activity_action_comment(self, activity_id, action_id, comment):
        """
        Update activity info
        :param activity_id:
        :param action_id:
        :param comment:
        :return:
        """
        with db.session.begin_nested():
            activity_action = ActivityAction.query.filter_by(
                activity_id=activity_id,
                action_id=action_id,).one_or_none()
            if activity_action:
                activity_action.action_comment = comment
                db.session.merge(activity_action)
        db.session.commit()

    def get_activity_action_comment(self, activity_id, action_id):
        """
        get activity info
        :param activity_id:
        :param action_id:
        :return:
        """
        with db.session.no_autoflush:
            activity_action = ActivityAction.query.filter_by(
                activity_id=activity_id,
                action_id=action_id,).one_or_none()
            return activity_action

    def get_activity_action_status(self, activity_id, action_id):
        with db.session.no_autoflush:
            activity_ac = ActivityAction.query.filter_by(
                activity_id=activity_id, action_id=action_id).one()
            action_stus = activity_ac.action_status
            return action_stus
    # add by ryuu end

    def upt_activity_item(self, activity, item_id):
        """
        Update activity info for item id
        :param activity:
        :param item_id:
        :return:
        """
        try:
            with db.session.begin_nested():
                db_activity = _Activity.query.filter_by(
                    activity_id=activity.get('activity_id')).one()
                db_activity.item_id = item_id
                db_activity.action_status = activity.get('action_status')
                db_new_history = ActivityHistory(
                    activity_id=db_activity.activity_id,
                    action_id=db_activity.action_id,
                    action_version=activity.get('action_version'),
                    action_status=activity.get('action_status'),
                    action_user=current_user.get_id(),
                    action_date=datetime.utcnow(),
                    action_comment=activity.get('commond')
                )
                db.session.merge(db_activity)
                db.session.add(db_new_history)
            db.session.commit()
            return True
        except NoResultFound as ex:
            current_app.logger.exception(str(ex))
            return None
        except Exception as ex:
            db.session.rollback()
            current_app.logger.exception(str(ex))
            return None

    def end_activity(self, activity):
        try:
            with db.session.begin_nested():
                db_activity = _Activity.query.filter_by(
                    activity_id=activity.get('activity_id')).one_or_none()
                if db_activity:
                    db_activity.activity_status = \
                        ActivityStatusPolicy.ACTIVITY_FINALLY
                    db_activity.action_id = activity.get('action_id')
                    db_activity.action_status = activity.get('action_status')
                    db_activity.activity_end = datetime.utcnow()
                    db.session.merge(db_activity)
                    db_history = ActivityHistory(
                        activity_id=activity.get('activity_id'),
                        action_id=activity.get('action_id'),
                        action_version=activity.get('action_version'),
                        action_status=activity.get('action_status'),
                        action_user=current_user.get_id(),
                        action_date=datetime.utcnow(),
                        action_comment=
                        ActionCommentPolicy.FINALLY_ACTION_COMMENT
                    )
                    db.session.add(db_history)
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            current_app.logger.exception(str(ex))

    def get_activity_list(self, community_id=None):
        """
        get activity list info
        :return:
        """
        with db.session.no_autoflush:
            self_user_id = int(current_user.get_id())
            self_group_ids = [role.id for role in current_user.roles]

            db_flow_action_users = _FlowActionRole.query.filter_by(
                action_user=self_user_id, action_user_exclude=False).all()
            db_flow_action_ids = [db_flow_action_user.flow_action_id for
                                  db_flow_action_user in db_flow_action_users]
            db_flow_action_roles = _FlowActionRole.query.filter_by(
                action_user_exclude=False).filter(
                _FlowActionRole.action_role.in_(self_group_ids)).all()
            db_flow_action_ids.extend(
                [db_flow_action_role.flow_action_id for
                 db_flow_action_role in db_flow_action_roles])
            db_flow_actions = _FlowAction.query.filter(
                _FlowAction.id.in_(db_flow_action_ids)).all()
            db_flow_define_flow_ids = [db_flow_action.flow_id for
                                       db_flow_action in db_flow_actions]
            db_flow_defines = _Flow.query.filter(
                _Flow.flow_id.in_(db_flow_define_flow_ids)).all()
            db_flow_define_ids = [db_flow_define.id for
                                  db_flow_define in db_flow_defines]
            db_activitys = _Activity.query.filter_by(
                activity_login_user=self_user_id).all()
            db_flow_define_ids.extend(
                [db_activity.flow_id for db_activity in db_activitys])
            db_flow_define_ids = list(set(db_flow_define_ids))
            if community_id is not None:
                activities = _Activity.query.filter(
                    _Activity.flow_id.in_(db_flow_define_ids),
                    _Activity.activity_community_id == community_id
                ).order_by(
                    asc(_Activity.id)).all()
            else:
                activities = _Activity.query.filter(
                    _Activity.flow_id.in_(db_flow_define_ids)).order_by(
                    asc(_Activity.id)).all()
            for activi in activities:
                if activi.item_id is None:
                    activi.ItemName = ''
                else:
                    item = ItemMetadata.query.filter_by(
                        id=activi.item_id).one_or_none()
                    if item:
                        activi.ItemName = item.json.get('title_ja')
                    else:
                        activi.ItemName = ''
                activi.StatusDesc = ActionStatusPolicy.describe(
                    ActionStatusPolicy.ACTION_DONE) \
                    if ActivityStatusPolicy.ACTIVITY_FINALLY == activi.activity_status \
                    else ActionStatusPolicy.describe(
                    ActionStatusPolicy.ACTION_DOING)
                activi.User = User.query.filter_by(
                    id=activi.activity_update_user).first()
                if ActivityStatusPolicy.ACTIVITY_FINALLY == activi.activity_status:
                    activi.type = 'All'
                    continue
                activi.type = 'ToDo'
                if self_user_id == activi.activity_login_user:
                    db_flow_action = _FlowAction.query.filter_by(
                        flow_id=activi.flow_define.flow_id,
                        action_id=activi.action_id).one_or_none()
                    current_app.logger.debug(
                        'activi {0}:{1} db_flow_action is {2}'.format(
                            activi.activity_id,
                            activi.activity_login_user,
                            'True' if db_flow_action else 'None'))
                    if db_flow_action:
                        for role in db_flow_action.action_roles:
                            activi.type = 'Wait'
                            if role.action_user == self_user_id and \
                                    role.action_user_exclude is False:
                                activi.type = 'ToDo'
                                break
                            if role.action_role in self_group_ids and \
                                    role.action_role_exclude is False:
                                activi.type = 'ToDo'
                                break
            return activities

    def get_activity_steps(self, activity_id):
        steps = []
        his = WorkActivityHistory()
        histories = his.get_activity_history_list(activity_id)
        history_dict = {}
        for history in histories:
            history_dict[history.action_id] = {
                'Updater': history.user.email,
                'Result': ActionStatusPolicy.describe(
                    self.get_activity_action_status(activity_id=activity_id,
                                                    action_id=history.action_id)
                )
            }
        with db.session.no_autoflush:
            activity = _Activity.query.filter_by(
                activity_id=activity_id).one_or_none()
            if activity is not None:
                flow_actions = _FlowAction.query.filter_by(
                    flow_id=activity.flow_define.flow_id).order_by(asc(
                    _FlowAction.action_order)).all()
                for flow_action in flow_actions:
                    steps.append({
                        'ActivityId': activity_id,
                        'ActionId': flow_action.action_id,
                        'ActionName': flow_action.action.action_name,
                        'ActionVersion': flow_action.action_version,
                        'ActionEndpoint': flow_action.action.action_endpoint,
                        'Author': history_dict[flow_action.action_id].get(
                            'Updater') if flow_action.action_id in history_dict else '',
                        'Status': history_dict[flow_action.action_id].get(
                            'Result') if flow_action.action_id in history_dict else ' '
                    })

        return steps

    def get_activity_detail(self, activity_id):
        """
        get activity detail info
        :param activity_id:
        :return:
        """
        with db.session.no_autoflush:
            query = _Activity.query.filter_by(activity_id=activity_id)
            activity = query.one_or_none()
            if activity:
                activity_login_user = User.query.filter_by(
                    id=activity.activity_login_user).one_or_none()
                if activity_login_user:
                    activity.login_user = activity_login_user.email
                activity_update_user = User.query.filter_by(
                    id=activity.activity_update_user).one_or_none()
                if activity_update_user:
                    activity.update_user = activity_update_user.email
            return activity

    def get_activity_action_role(self, activity_id, action_id):
        roles = {
            'allow': [],
            'deny': []
        }
        users = {
            'allow': [],
            'deny': []
        }
        with db.session.no_autoflush:
            activity = _Activity.query.filter_by(
                activity_id=activity_id).first()
            flow_action = _FlowAction.query.filter_by(
                flow_id=activity.flow_define.flow_id,
                action_id=int(action_id)).one_or_none()
            for action_role in flow_action.action_roles:
                if action_role.action_role_exclude:
                    roles['deny'].append(action_role.action_role)
                elif action_role.action_role:
                    roles['allow'].append(action_role.action_role)
                if action_role.action_user_exclude:
                    users['deny'].append(action_role.action_user)
                elif action_role.action_user:
                    users['allow'].append(action_role.action_user)
            return roles, users

    def del_activity(self, activity_id):
        """
        Delete activity info
        :param activity_id:
        :return:
        """
        pass

    def get_activity_index_search(self, activity_id):
        """Get page info after item search"""
        from weko_records.api import ItemsMetadata
        from flask_babelex import gettext as _
        from invenio_pidstore.models import PersistentIdentifier
        from werkzeug.utils import import_string
        from invenio_pidstore.resolver import Resolver
        from .views import check_authority_action
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

        res_check = check_authority_action(activity_id, action_id)

        getargs = request.args
        ctx = {'community': None}
        community_id = ""
        if 'community' in getargs:
            comm = GetCommunity.get_community_by_id(request.args.get('community'))
            community_id = request.args.get('community')
            ctx = {'community': comm}
            community_id = comm.id

        return activity_detail, item, steps, action_id, cur_step, temporary_comment, approval_record, step_item_login_url, histories, res_check, pid, community_id, ctx


class WorkActivityHistory(object):
    """Operated on the Activity"""
    def create_activity_history(self, activity):
        """
        Create new activity history
        :param activity:
        :return:
        """
        db_history = ActivityHistory(
            activity_id=activity.get('activity_id'),
            action_id=activity.get('action_id'),
            action_version=activity.get('action_version'),
            action_status=activity.get('action_status'),
            action_user=current_user.get_id(),
            action_date=datetime.utcnow(),
            action_comment=activity.get('commond')
        )
        new_history = False
        activity = WorkActivity()
        activity = activity.get_activity_detail(db_history.activity_id)
        if activity.action_id != db_history.action_id or \
                activity.action_status != db_history.action_status:
            new_history = True
            activity.action_id = db_history.action_id
            activity.action_status = db_history.action_status
            activity.activity_update_user = db_history.action_user
            activity.updated = datetime.utcnow()
        try:
            with db.session.begin_nested():
                if new_history:
                    db.session.merge(activity)
                    db.session.add(db_history)
        except Exception as ex:
            current_app.logger.exception(str(ex))
            db.session.rollback()
            return None
        else:
            db.session.commit()
            return db_history

    def get_activity_history_list(self, activity_id):
        """
        get activity history list info
        :param activity_id:
        :return:
        """
        with db.session.no_autoflush:
            query = ActivityHistory.query.filter_by(
                activity_id=activity_id).order_by(asc(ActivityHistory.id))
            histories = query.all()
            for history in histories:
                history.ActionName = _Action.query.filter_by(
                    id=history.action_id).first().action_name,
                history.StatusDesc = ActionStatusPolicy.describe(
                    history.action_status)
                history.CommentDesc = ActionCommentPolicy.describe(
                    history.action_comment)
            return histories

    def get_activity_history_detail(self, activity_id):
        """
        get activity history detail info
        :param activity_id:
        :return:
        """
        pass

    def upd_activity_history_detail(self, activity_id, action_id):
        """
        get activity history detail info
        :param activity_id:
        :param action_id:
        :return:
        """
        try:
            with db.session.begin_nested():
                activity = ActivityHistory.query.filter_by(
                    activity_id=activity_id,
                    action_id=action_id).order_by(
                    desc(ActivityHistory.id)).one_or_none()
                if activity:
                    activity.action_status = ActionStatusPolicy.ACTION_DOING
                    db.session.merge(activity)
            db.session.commit()
            return True
        except Exception as ex:
            current_app.logger.exception(str(ex))
            db.session.rollback()
            return None

class UpdateItem(object):
    """the class about item"""

    def publish(pid, record):
        r"""Record publish  status change view.

        Change record publish status with given status and renders record export
        template.

        :param pid: PID object.
        :param record: Record object.
        :param template: Template to render.
        :param \*\*kwargs: Additional view arguments based on URL rule.
        :return: The rendered template.
        """

        from invenio_db import db
        from weko_deposit.api import WekoIndexer
        publish_status = record.get('publish_status')
        if not publish_status:
            record.update({'publish_status': '0'})
        else:
            record['publish_status'] = '0'

        record.commit()
        db.session.commit()

        indexer = WekoIndexer()
        indexer.update_publish_status(record)

    def set_item_relation(self, relationData, record):
        """
        set relation info of item
        :param relationData: item relation data
        :param record: item info
        """

        from weko_deposit.api import WekoIndexer

        indexer = WekoIndexer()
        indexer.update_relation_info(record, relationData)


class GetCommunity(object):
    """Get Community Info"""
    @classmethod
    def get_community_by_id(self, community_id):
        """"""
        from invenio_communities.models import Community
        c = Community.get(community_id)
        return c
