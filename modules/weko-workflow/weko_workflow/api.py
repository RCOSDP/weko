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
from flask import current_app
from flask_login import current_user
from invenio_accounts.models import User
from invenio_db import db
from sqlalchemy import asc
from sqlalchemy.orm.exc import NoResultFound
from weko_records.api import ItemsMetadata

from .models import Action as _Action
from .models import Activity as _Activity
from .models import ActivityHistory
from .models import Flow as _Flow
from .models import FlowAction as _FlowAction
from .models import WorkFlow as _WorkFlow
from .models import ActionStatusPolicy, FlowStatusPolicy, StatusPolicy


class Flow(object):
    """Operated on the Flow"""

    def create_flow(self, flow):
        """
        Create new flow
        :param flow:
        :return:
        """
        _flow = _Flow(
            flow_name=flow.get('flow_name'),
            flow_user=current_user.get_id()
        )
        with db.session.begin_nested():
            db.session.add(_flow)
        db.session.commit()
        return _flow

    def upt_flow(self, flow_id, flow):
        """
        Update flow info
        :param flow_id:
        :param flow:
        :return:
        """
        with db.session.begin_nested():
            _flow = _Flow.query.filter_by(
                flow_id=flow_id).one_or_none()
            if _flow is not None:
                _flow.flow_name = flow.get('flow_name')
                _flow.flow_user = current_user.get_id()
                db.session.merge(_flow)
        db.session.commit()
        return _flow

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
            return query.one_or_none()

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
                flowaction_filter = _FlowAction.query.filter_by(flow_id=flow_id)\
                    .filter_by(action_id=action.get('id'))
                if action.get('action', None) == 'DEL':
                    flowaction_filter.delete()
                    continue
                flowaction = flowaction_filter.one_or_none()
                if flowaction is None:
                    """new"""
                    flowaction = _FlowAction(
                        flow_id=flow_id,
                        action_id=action.get('id'),
                        action_order=order + 1
                    )
                    _flow = _Flow.query.filter_by(flow_id=flow_id).one_or_none()
                    _flow.flow_status = FlowStatusPolicy.AVAILABLE
                    db.session.add(flowaction)
                else:
                    """Update"""
                    flowaction.action_order = order + 1
                    db.session.merge(flowaction)
        db.session.commit()


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
        except BaseException as ex:
            db.session.rollback()
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
                if _workflow is not None:
                    _workflow.flows_name = workflow.get('flows_name')
                    _workflow.itemtype_id = workflow.get('itemtype_id')
                    _workflow.flow_id = workflow.get('flow_id')
                    db.session.add(_workflow)
            db.session.commit()
            return workflow
        except BaseException as ex:
            db.session.rollback()
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

    def get_workflow_by_id(self, id):
        """
        get workflow detail info
        :param workflow_id:
        :return:
        """
        with db.session.no_autoflush:
            query = _WorkFlow.query.filter_by(
                id=id)
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
        pass

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

    def init_activity(self, activity):
        """
        Create new activity
        :param activity:
        :return:
        """
        db_activity = _Activity(
            activity_id='A' + str(datetime.utcnow().timestamp()).split('.')[0],
            workflow_id=activity.get('workflow_id'),
            flow_id=activity.get('flow_id'),
            action_id=0,
            action_status=ActionStatusPolicy.ACTION_FINALLY,
            activity_login_user=current_user.get_id(),
            activity_update_user=current_user.get_id(),
            activity_status=0,
            activity_start=datetime.utcnow()
        )
        db_history = ActivityHistory(
            activity_id=db_activity.activity_id,
            action_id=db_activity.action_id,
            action_version='1.0.0',
            action_status=ActionStatusPolicy.ACTION_FINALLY,
            action_user=current_user.get_id(),
            action_date=db_activity.activity_start,
            action_comment='Begin Action'
        )
        try:
            with db.session.begin_nested():
                db.session.add(db_activity)
                db.session.add(db_history)
        except Exception as ex:
            current_app.logger.exception(str(ex))
            db.session.rollback()
            return None
        else:
            db.session.commit()
            return db_activity

    def upt_activity(self, activity):
        """
        Update activity info
        :param activity:
        :return:
        """
        pass

    def upt_activity_item(self, activity, item_id):
        """
        Update activity info for item id
        :param activity:
        :param item_id:
        :return:
        """
        current_app.logger.debug('received item: {0}'.format(item_id))
        try:
            with db.session.begin_nested():
                db_activity = _Activity.query.filter_by(
                    activity_id=activity.get('activity_id')).one()
                db_activity.item_id = item_id
                db_activity.action_status = ActionStatusPolicy.ACTION_FINALLY
                db_history = ActivityHistory.query.filter_by(
                    activity_id=db_activity.activity_id,
                    action_id=db_activity.action_id).first()
                db_new_history = ActivityHistory(
                    activity_id=db_activity.activity_id,
                    action_id=db_activity.action_id,
                    action_version=db_history.action_version,
                    action_status=ActionStatusPolicy.ACTION_FINALLY,
                    action_user=current_user.get_id(),
                    action_date=datetime.utcnow(),
                    action_comment=db_history.action_comment
                )
                db.session.merge(db_activity)
                db.session.add(db_new_history)

            db.session.commit()
            return True
        except NoResultFound as ex:
            current_app.logger.exception(str(ex))
            return None


    def get_activity_list(self):
        """
        get activity list info
        :return:
        """
        with db.session.no_autoflush:
            query = _Activity.query.order_by(asc(_Activity.id))
            activities = query.all()
            for activi in activities:
                if activi.item_id is None:
                    activi.ItemName = ''
                else:
                    item = ItemsMetadata.get_record(id_=activi.item_id)
                    activi.ItemName = item.get('title_ja')
                activi.StatusDesc = StatusPolicy.describe(activi.status)
                activi.User = User.query.filter_by(
                    id=activi.activity_update_user).first()
            return activities

    def get_activity_steps(self, activity_id):
        steps = []
        his = WorkActivityHistory()
        histories = his.get_activity_history_list(activity_id)
        history_dict = {}
        for history in histories:
            history_dict[history.action_id] = {
                'Updater': history.user.email,
                'Result': history.StatusDesc
            }
        with db.session.no_autoflush:
            activity = _Activity.query.filter_by(
                activity_id=activity_id).one_or_none()
            if activity is not None:
                flow_actions = _FlowAction.query.filter_by(
                    flow_id=activity.flow.flow_id).order_by(asc(
                    _FlowAction.action_order)).all()
                for flow_action in flow_actions:
                    steps.append({
                        'ActivityId': activity_id,
                        'ActionId': flow_action.action_id,
                        'ActionName': flow_action.action.action_name,
                        'ActionVersion': flow_action.action_version,
                        'Author': history_dict[flow_action.action_id].get('Updater') if flow_action.action_id in history_dict else '',
                        'Status': history_dict[flow_action.action_id].get('Result') if flow_action.action_id in history_dict else ' '
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
            return activity

    def del_activity(self, activity_id):
        """
        Delete activity info
        :param activity_id:
        :return:
        """
        pass

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
            action_status=ActionStatusPolicy.ACTION_MAKING,
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
            activity.modified = datetime.utcnow()
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
                history.ActionName = \
                    _Action.query.filter_by(
                        id=history.action_id).first().action_name,
                history.StatusDesc = \
                    ActionStatusPolicy.describe(history.action_status)
            return histories

    def get_activity_history_detail(self, activity_id):
        """
        get activity history detail info
        :param activity_id:
        :return:
        """
        pass
