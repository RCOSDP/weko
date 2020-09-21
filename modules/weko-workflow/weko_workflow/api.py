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
from datetime import datetime, timedelta

from flask import current_app, request, session, url_for
from flask_login import current_user
from invenio_accounts.models import Role, User, userrole
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from sqlalchemy import asc, desc, or_, types
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import cast
from weko_records.models import ItemMetadata

from .config import IDENTIFIER_GRANT_LIST, IDENTIFIER_GRANT_SUFFIX_METHOD, \
    WEKO_WORKFLOW_ALL_TAB, WEKO_WORKFLOW_TODO_TAB, WEKO_WORKFLOW_WAIT_TAB
from .models import Action as _Action
from .models import ActionCommentPolicy, ActionFeedbackMail, \
    ActionIdentifier, ActionJournal, ActionStatusPolicy
from .models import Activity as _Activity
from .models import ActivityAction, ActivityHistory, ActivityStatusPolicy
from .models import FlowAction as _FlowAction
from .models import FlowActionRole as _FlowActionRole
from .models import FlowDefine as _Flow
from .models import FlowStatusPolicy
from .models import WorkFlow as _WorkFlow


class Flow(object):
    """Operated on the Flow."""

    def create_flow(self, flow):
        """
        Create new flow.

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
        """Update flow info.

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
        """Get flow list info.

        :return:
        """
        with db.session.no_autoflush:
            query = _Flow.query.filter_by(
                is_deleted=False).order_by(asc(_Flow.flow_id))
            return query.all()

    def get_flow_detail(self, flow_id):
        """Get flow detail info.

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
        """Delete flow info.

        :param flow_id:
        :return:
        """
        try:
            with db.session.begin_nested():
                flow = _Flow.query.filter_by(
                    flow_id=flow_id).one_or_none()
                if flow:
                    flow.is_deleted = True
                    db.session.merge(flow)
            db.session.commit()
            return {'code': 0, 'msg': ''}
        except Exception as ex:
            db.session.rollback()
            current_app.logger.exception(str(ex))
            return {'code': 500, 'msg': str(ex)}

    def upt_flow_action(self, flow_id, actions):
        """Update FlowAction Info."""
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
                    _flow = _Flow.query.filter_by(
                        flow_id=flow_id).one_or_none()
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
        """Return next action info.

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
        """Return next action info.

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

    def get_last_flow_action(self, flow_id):
        """Return last action info.

        :param flow_id: registered id of flow
        :return: flow action or None when error
        """
        with db.session.no_autoflush:
            flow_actions = _FlowAction.query.filter_by(
                flow_id=flow_id).order_by(asc(
                    _FlowAction.action_order)).all()
            if flow_actions:
                last_action = flow_actions.pop()
                return last_action
        return None

    def get_item_registration_flow_action(self, flow_id):
        """Return Item Registration action info.

        :param flow_id: item_registration's flow id
        :return flow_action: flow action's object
        """
        action_id = current_app.config.get(
            "WEKO_WORKFLOW_ITEM_REGISTRATION_ACTION_ID", 3)
        with db.session.no_autoflush:
            flow_action = _FlowAction.query.filter_by(
                flow_id=flow_id,
                action_id=action_id).all()
            return flow_action


class WorkFlow(object):
    """Operated on the WorkFlow."""

    def create_workflow(self, workflow):
        """Create new workflow.

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
        """Update workflow info.

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
        """Get workflow list info.

        :return:
        """
        with db.session.no_autoflush:
            query = _WorkFlow.query.filter_by(
                is_deleted=False).order_by(asc(_WorkFlow.flows_id))
            return query.all()

    def get_workflow_detail(self, workflow_id):
        """Get workflow detail info.

        :param workflow_id:
        :return:
        """
        with db.session.no_autoflush:
            query = _WorkFlow.query.filter_by(
                flows_id=workflow_id)
            return query.one_or_none()

    def get_workflow_by_id(self, workflow_id):
        """Get workflow detail info by workflow id.

        :param workflow_id:
        :return:
        """
        with db.session.no_autoflush:
            query = _WorkFlow.query.filter_by(
                id=workflow_id)
            return query.one_or_none()

    def get_workflow_by_flows_id(self, flows_id):
        """Get workflow detail info by flows id.

        :param flows_id:
        :return:
        """
        with db.session.no_autoflush:
            query = _WorkFlow.query.filter_by(
                flows_id=flows_id)
            return query.one_or_none()

    def get_workflow_by_flow_id(self, flow_id):
        """Get workflow detail info by flow id.

        :param flow_id:
        :return:
        """
        with db.session.no_autoflush:
            query = _WorkFlow.query.filter_by(
                flow_id=flow_id, is_deleted=False)
            return query.all()

    def del_workflow(self, workflow_id):
        """Delete flow info.

        :param workflow_id:
        :return:
        """
        try:
            with db.session.begin_nested():
                workflow = _WorkFlow.query.filter_by(
                    flows_id=workflow_id).one_or_none()
                if workflow:
                    workflow.is_deleted = True
                    db.session.merge(workflow)
            db.session.commit()
            return {'code': 0, 'msg': ''}
        except Exception as ex:
            db.session.rollback()
            current_app.logger.exception(str(ex))
            return {'code': 500, 'msg': str(ex)}

    def find_workflow_by_name(self, workflow_name):
        """Find workflow by name.

        :param workflow_name:
        :return:
        """
        with db.session.no_autoflush:
            return _WorkFlow.query.filter_by(flows_name=workflow_name).first()


class Action(object):
    """Operated on the Action."""

    def create_action(self, action):
        """Create new action info.

        :param action:
        :return:
        """
        pass

    def upt_action(self, action):
        """Update action info.

        :param action:
        :return:
        """
        pass

    def get_action_list(self, is_deleted=False):
        """Get action list info.

        :param is_deleted:
        :return:
        """
        with db.session.no_autoflush:
            query = _Action.query.order_by(asc(_Action.id))
            return query.all()

    def get_action_detail(self, action_id):
        """Get detail info of action.

        :param action_id:
        :return:
        """
        with db.session.no_autoflush:
            query = _Action.query.filter_by(id=action_id)
            return query.one_or_none()

    def del_action(self, action_id):
        """Delete the action info.

        :param action_id:
        :return:
        """
        pass


class ActionStatus(object):
    """Operated on the ActionStatus."""

    def create_action_status(self, action_status):
        """Create new action status info.

        :param action_status:
        :return:
        """
        pass

    def upt_action_status(self, action_status):
        """Update action status info.

        :param action_status:
        :return:
        """
        pass

    def get_action_status_list(self, is_deleted=False):
        """Get action status list info.

        :param is_deleted:
        :return:
        """
        pass

    def get_action_status_detail(self, action_status_id):
        """Get detail info of action status.

        :param action_status_id:
        :return:
        """
        pass

    def del_action_status(self, action_status_id):
        """Delete the action status info.

        :param action_status_id:
        :return:
        """
        pass


class WorkActivity(object):
    """Operated on the Activity."""

    def init_activity(self, activity, community_id=None, item_id=None):
        """Create new activity.

        :param activity:
        :param community_id:
        :param item_id:
        :return:
        """
        utc_now = datetime.utcnow()
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
                # Dummy activity ID, the real one will be updated
                #   after this activity is created
                activity_id='A' + str(
                    datetime.utcnow().timestamp()).split('.')[0],
                item_id=item_id,
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
            db.session.add(db_activity)
        except Exception as ex:
            db.session.rollback()
            current_app.logger.exception(str(ex))
            return None
        else:
            db.session.commit()

            try:
                # Calculate activity_id based on id
                current_date_start = utc_now.strftime("%Y-%m-%d 00:00:00")
                from datetime import timedelta
                next_date_start = (utc_now + timedelta(1)).\
                    strftime("%Y-%m-%d 00:00:00")

                from sqlalchemy import func
                min_id = db.session.query(func.min(_Activity.id)).filter(
                    _Activity.created >= '{}'.format(current_date_start),
                    _Activity.created < '{}'.format(next_date_start),
                ).scalar()

                if min_id:
                    # Calculate aid
                    number = db_activity.id - min_id + 1
                    if number > 99999:
                        raise IndexError('The number is out of range \
                            (maximum is 99999, current is {}'.format(number))
                else:
                    # The default activity Id of the current day
                    number = 1

                # Activity Id's format
                activity_id_format = current_app.\
                    config['WEKO_WORKFLOW_ACTIVITY_ID_FORMAT']

                # A-YYYYMMDD-NNNNN (NNNNN starts from 00001)
                datetime_str = utc_now.strftime("%Y%m%d")

                # Define activity Id of day
                activity_id = activity_id_format.format(
                    datetime_str,
                    '{inc:05d}'.format(inc=number))

                # Update the activity with calculated activity_id
                action_pid = PersistentIdentifier.create(
                    pid_type='actid',
                    pid_value=str(activity_id),
                    status=PIDStatus.REGISTERED
                    # object_type='act', #Workflow Activity Object Type
                )
                db_activity.activity_id = action_pid.pid_value

                # Add history and flow_action
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
                    db.session.add(db_history)

                    for flow_action in flow_actions:
                        db_activity_action = ActivityAction(
                            activity_id=db_activity.activity_id,
                            action_id=flow_action.action_id,
                            action_status=ActionStatusPolicy.ACTION_DONE,
                        )
                        db.session.add(db_activity_action)

            except IndexError as ex:
                current_app.logger.exception(str(ex))

                return None

            except Exception as ex:
                db.session.rollback()
                current_app.logger.exception(str(ex))

                return None

            else:
                db.session.commit()

                return db_activity

    def upt_activity_action(self, activity_id, action_id, action_status):
        """Update activity info.

        :param activity_id:
        :param action_id:
        :param action_status:
        :return:
        """
        with db.session.begin_nested():
            activity = _Activity.query.filter_by(
                activity_id=activity_id).one_or_none()
            activity.action_id = action_id
            activity.action_status = action_status
            db.session.merge(activity)
        db.session.commit()

    def upt_activity_action_status(
            self,
            activity_id,
            action_id,
            action_status):
        """Update activity info.

        :param activity_id:
        :param action_id:
        :param action_status:
        :return:
        """
        with db.session.begin_nested():
            activity_action = ActivityAction.query.filter_by(
                activity_id=activity_id,
                action_id=action_id, ).one_or_none()
            activity_action.action_status = action_status
            db.session.merge(activity_action)
        db.session.commit()

    def upt_activity_action_comment(self, activity_id, action_id, comment):
        """Update activity info.

        :param activity_id:
        :param action_id:
        :param comment:
        :return:
        """
        with db.session.begin_nested():
            activity_action = ActivityAction.query.filter_by(
                activity_id=activity_id,
                action_id=action_id, ).one_or_none()
            if activity_action:
                activity_action.action_comment = comment
                db.session.merge(activity_action)
        db.session.commit()

    def get_activity_action_comment(self, activity_id, action_id):
        """Get activity info.

        :param activity_id:
        :param action_id:
        :return:
        """
        with db.session.no_autoflush:
            activity_action = ActivityAction.query.filter_by(
                activity_id=activity_id,
                action_id=action_id, ).one_or_none()
            return activity_action

    def create_or_update_action_journal(self, activity_id, action_id, journal):
        """Create or update action journal info.

        :param activity_id:
        :param action_id:
        :param journal:
        :return:
        """
        with db.session.begin_nested():
            action_journal = ActionJournal.query.filter_by(
                activity_id=activity_id,
                action_id=action_id).one_or_none()
            if action_journal:
                action_journal.action_journal = journal
                db.session.merge(action_journal)
            else:
                new_action_journal = ActionJournal(
                    activity_id=activity_id,
                    action_id=action_id,
                    action_journal=journal,
                )
                db.session.add(new_action_journal)
        db.session.commit()

    def create_or_update_action_identifier(self, activity_id,
                                           action_id, identifier):
        """Create or update action identifier grant info.

        :param activity_id:
        :param action_id:
        :param identifier:
        :return:
        """
        with db.session.begin_nested():
            action_identifier = ActionIdentifier.query.filter_by(
                activity_id=activity_id,
                action_id=action_id).one_or_none()
            if action_identifier:
                action_identifier.action_identifier_select = identifier.get(
                    'action_identifier_select')
                action_identifier.action_identifier_jalc_doi =\
                    identifier.get(
                        'action_identifier_jalc_doi')
                action_identifier.action_identifier_jalc_cr_doi =\
                    identifier.get(
                        'action_identifier_jalc_cr_doi')
                action_identifier.action_identifier_jalc_dc_doi =\
                    identifier.get(
                        'action_identifier_jalc_dc_doi')
                action_identifier.action_identifier_ndl_jalc_doi =\
                    identifier.get(
                        'action_identifier_ndl_jalc_doi')
                db.session.merge(action_identifier)
            else:
                new_action_identifier = ActionIdentifier(
                    activity_id=activity_id,
                    action_id=action_id,
                    action_identifier_select=identifier.get(
                        'action_identifier_select'),
                    action_identifier_jalc_doi=identifier.get(
                        'action_identifier_jalc_doi'),
                    action_identifier_jalc_cr_doi=identifier.get(
                        'action_identifier_jalc_cr_doi'),
                    action_identifier_jalc_dc_doi=identifier.get(
                        'action_identifier_jalc_dc_doi'),
                    action_identifier_ndl_jalc_doi=identifier.get(
                        'action_identifier_ndl_jalc_doi')
                )
                db.session.add(new_action_identifier)

        db.session.commit()

    def create_or_update_action_feedbackmail(self,
                                             activity_id,
                                             action_id,
                                             feedback_maillist):
        """Create or update action ActionFeedbackMail's model.

        :param activity_id: activity identifier
        :param action_id:   action identifier
        :param feedback_maillist: list of feedback mail in json format
        :return:
        """
        try:
            with db.session.begin_nested():
                action_feedbackmail = ActionFeedbackMail.query.filter_by(
                    activity_id=activity_id).one_or_none()
                if action_feedbackmail:
                    action_feedbackmail.feedback_maillist = feedback_maillist
                    db.session.merge(action_feedbackmail)
                else:
                    action_feedbackmail = ActionFeedbackMail(
                        activity_id=activity_id,
                        action_id=action_id,
                        feedback_maillist=feedback_maillist
                    )
                    db.session.add(action_feedbackmail)
            db.session.commit()
        except SQLAlchemyError as ex:
            db.session.rollback()
            current_app.logger.exception(str(ex))

    def get_action_journal(self, activity_id, action_id):
        """Get action journal info.

        :param activity_id:
        :param action_id:
        :return:
        """
        with db.session.no_autoflush:
            action_journal = ActionJournal.query.filter_by(
                activity_id=activity_id,
                action_id=action_id, ).one_or_none()
            return action_journal

    def get_action_identifier_grant(self, activity_id, action_id):
        """Get action idnetifier grant info.

        :param activity_id:
        :param action_id:
        :return:
        """
        identifier = {'action_identifier_select': '',
                      'action_identifier_jalc_doi': '',
                      'action_identifier_jalc_cr_doi': '',
                      'action_identifier_jalc_dc_doi': '',
                      'action_identifier_ndl_jalc_doi': ''
                      }
        with db.session.no_autoflush:
            action_identifier = ActionIdentifier.query.filter_by(
                activity_id=activity_id,
                action_id=action_id).one_or_none()
            if action_identifier:
                identifier['action_identifier_select'] =\
                    action_identifier.action_identifier_select
                identifier['action_identifier_jalc_doi'] =\
                    action_identifier.action_identifier_jalc_doi
                identifier['action_identifier_jalc_cr_doi'] =\
                    action_identifier.action_identifier_jalc_cr_doi
                identifier['action_identifier_jalc_dc_doi'] =\
                    action_identifier.action_identifier_jalc_dc_doi
                identifier['action_identifier_ndl_jalc_doi'] =\
                    action_identifier.action_identifier_ndl_jalc_doi
            else:
                identifier = action_identifier
        return identifier

    def get_action_feedbackmail(self, activity_id, action_id):
        """Get ActionFeedbackMail object from model base on activity's id.

        :param activity_id: acitivity identifier
        :param action_id:   action identifier
        :return:    object's model or none
        """
        with db.session.no_autoflush:
            action_feedbackmail = ActionFeedbackMail.query.filter_by(
                activity_id=activity_id).one_or_none()
            return action_feedbackmail

    def get_activity_action_status(self, activity_id, action_id):
        """Get activity action status."""
        with db.session.no_autoflush:
            activity_ac = ActivityAction.query.filter_by(
                activity_id=activity_id, action_id=action_id).one()
            action_stus = activity_ac.action_status
            return action_stus

    def upt_activity_item(self, activity, item_id):
        """Update activity info for item id.

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
        """End activity."""
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
                    if activity.get('item_id') is not None:
                        db_activity.item_id = activity.get('item_id')
                    db.session.merge(db_activity)
                    db_history = ActivityHistory(
                        activity_id=activity.get('activity_id'),
                        action_id=activity.get('action_id'),
                        action_version=activity.get('action_version'),
                        action_status=activity.get('action_status'),
                        action_user=current_user.get_id(),
                        action_date=datetime.utcnow(),
                        action_comment=ActionCommentPolicy.
                        FINALLY_ACTION_COMMENT)
                    db.session.add(db_history)
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            current_app.logger.exception(str(ex))

    def quit_activity(self, activity):
        """Cancel doing activity.

        :param activity:
        :return:
        """
        flow = Flow()
        work_activity = WorkActivity()
        activity_detail = work_activity.get_activity_detail(
            activity.get('activity_id'))

        last_flow_action = flow.get_last_flow_action(
            activity_detail.flow_define.flow_id)

        if not last_flow_action:
            current_app.logger.error('Cannot get last action of flow!')
            return None

        try:
            with db.session.begin_nested():
                db_activity = _Activity.query.filter_by(
                    activity_id=activity.get('activity_id')).one_or_none()
                if db_activity:
                    db_activity.action_id = activity.get('action_id')
                    db_activity.action_status = activity.get('action_status')
                    db_activity.activity_status = \
                        ActivityStatusPolicy.ACTIVITY_CANCEL
                    db_activity.activity_end = datetime.utcnow()
                    if 'item_id' in activity:
                        db_activity.item_id = activity.get('item_id')
                    db.session.merge(db_activity)

                    db_history = ActivityHistory(
                        activity_id=activity.get('activity_id'),
                        action_id=activity.get('action_id'),
                        action_version=activity.get('action_version'),
                        action_status=activity.get('action_status'),
                        action_user=current_user.get_id(),
                        action_date=datetime.utcnow(),
                        action_comment=activity.get('commond'))
                    db.session.add(db_history)

                    db_history = ActivityHistory(
                        activity_id=activity.get('activity_id'),
                        action_id=last_flow_action.action_id,
                        action_version=last_flow_action.action_version,
                        action_status=ActionStatusPolicy.ACTION_DONE,
                        action_user=current_user.get_id(),
                        action_date=datetime.utcnow(),
                        action_comment=ActionCommentPolicy.
                        FINALLY_ACTION_COMMENT)
                    db.session.add(db_history)
            db.session.commit()
            return True
        except Exception as ex:
            db.session.rollback()
            current_app.logger.exception(str(ex))
            return None

    def validate_date_to_filter(self, created):
        """
        Validate date created.

        :param created:
        :return:
        """
        created_date = created[0]
        if len(created_date) == 10:
            try:
                date_after_parse = datetime.strptime(created_date,
                                                     '%Y-%m-%d')
                return date_after_parse
            except ValueError:
                return None
        else:
            return None

    def filter_by_date(self, created_from, created_to, query):
        """
        Filter date created.

        :param created_from:
        :param created_to:
        :param query:
        :return:
        """
        date_created_from = None
        date_created_to = None

        if created_from:
            date_created_from = self.validate_date_to_filter(created_from)

        if created_to:
            date_created_to = self.validate_date_to_filter(created_to)

        if date_created_from and date_created_to:
            return query.filter(
                _Activity.created.between(date_created_from, date_created_to
                                          + timedelta(hours=23,
                                                      minutes=59,
                                                      seconds=59)))
        elif date_created_from:
            return query.filter(
                _Activity.created >= date_created_from)
        elif date_created_to:
            return query.filter(
                _Activity.created <= date_created_to + timedelta(hours=23,
                                                                 minutes=59,
                                                                 seconds=59))
        else:
            return query

    def filter_conditions(self, conditions, query):
        """
        Filter based on conditions.

        :param conditions:
        :param query:
        :return:
        """
        if conditions:
            title = conditions.get('item')
            status = conditions.get('status')
            workflow = conditions.get('workflow')
            user = conditions.get('user')
            created_from = conditions.get('createdfrom')
            created_to = conditions.get('createdto')

            if title:
                query = query.filter(or_(
                    _Activity.title.like(i + '%') for i in title))
            if user:
                query = query.join(
                    User, User.id == _Activity.activity_login_user).filter(
                    User.email.in_(user))
            if status:
                list_status = []
                for i in status:
                    if i == 'doing':
                        list_status.append(
                            ActivityStatusPolicy.ACTIVITY_MAKING)
                    elif i == 'done':
                        list_status.append(
                            ActivityStatusPolicy.ACTIVITY_FINALLY)
                    elif i == 'actioncancel':
                        list_status.append(
                            ActivityStatusPolicy.ACTIVITY_CANCEL)
                query = query.filter(
                    _Activity.activity_status.in_(list_status))
            if workflow:
                query = query.join(
                    _WorkFlow, _WorkFlow.id == _Activity.workflow_id).filter(
                    or_(_WorkFlow.flows_name.like(i + '%') for i in workflow))
            if created_from or created_to:
                query = self.filter_by_date(created_from,
                                            created_to,
                                            query)
        return query

    def query_activites_by_tab_is_wait(self, query, is_admin,
                                       is_community_admin):
        """
        Query activities by tab is wait.

        :param query:
        :param is_admin:
        :param is_community_admin:
        :return:
        """
        self_user_id = int(current_user.get_id())
        self_group_ids = [role.id for role in current_user.roles]
        query = query \
            .filter(_Activity.activity_login_user == self_user_id) \
            .filter(_FlowAction.action_id == _Activity.action_id) \
            .filter(((_FlowActionRole.action_user != self_user_id)
                     & (_FlowActionRole.action_user_exclude == '0'))
                    | (_FlowActionRole.action_role.notin_(self_group_ids)
                       & (_FlowActionRole.action_role_exclude == '0'))) \
            .filter((_Activity.activity_status
                     == ActivityStatusPolicy.ACTIVITY_BEGIN)
                    | (_Activity.activity_status
                       == ActivityStatusPolicy.ACTIVITY_MAKING))

        return query

    def query_activites_by_tab_is_all(self,
                                      query,
                                      is_admin,
                                      is_community_admin,
                                      community_user_ids):
        """
        Query activites by tab is all.

        :param query:
        :param is_admin:
        :param is_community_admin:
        :param community_user_ids:
        :return:
        """
        self_user_id = int(current_user.get_id())
        if is_community_admin:
            query = query \
                .filter(_Activity.activity_login_user.in_(community_user_ids))

        if not is_admin and not is_community_admin:
            query = query \
                .filter((_Activity.activity_login_user == self_user_id)
                        | (_Activity.shared_user_id == self_user_id))
        return query

    def check_current_user_role(self):
        """
        Check curent user role.

        :return:
        """
        is_admin = False
        is_community_admin = False
        supers = current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER']
        for role in list(current_user.roles or []):
            if role.name in supers:
                is_admin = True
                break
        # Community users
        community_role_name = current_app.config[
            'WEKO_PERMISSION_ROLE_COMMUNITY']
        for role in list(current_user.roles or []):
            if role.name in community_role_name:
                is_community_admin = True
                break
        return is_admin, is_community_admin

    def query_activites_by_tab_is_todo(self, query, is_admin,
                                       is_community_admin):
        """
        Query activites by tab is todo.

        :param query:
        :param is_admin:
        :param is_community_admin:
        :return:
        """
        self_user_id = int(current_user.get_id())
        self_group_ids = [role.id for role in current_user.roles]
        query = query \
            .filter((_Activity.activity_status
                    == ActivityStatusPolicy.ACTIVITY_BEGIN)
                    | (_Activity.activity_status
                    == ActivityStatusPolicy.ACTIVITY_MAKING)) \
            .filter(
                ((_FlowActionRole.action_user == self_user_id)
                 & (_FlowActionRole.action_user_exclude == '0'))
                | (_FlowActionRole.action_role.in_(self_group_ids)
                   & (_FlowActionRole.action_role_exclude == '0'))
                | _FlowActionRole.id.is_(None))\
            .filter(_FlowAction.action_id == _Activity.action_id)
        return query

    def get_activity_list(self, community_id=None, conditions=None):
        """Get activity list info.

        :return:
        """
        with db.session.no_autoflush:
            is_admin, is_community_admin = self.check_current_user_role()

            community_role_name = current_app.config[
                'WEKO_PERMISSION_ROLE_COMMUNITY']
            tab_list = conditions.get('tab')

            # Get tab of page
            tab = WEKO_WORKFLOW_TODO_TAB if not tab_list else tab_list[0]
            size = 20
            page = 1

            activities = []
            community_users = User.query.outerjoin(userrole).outerjoin(
                Role) \
                .filter(community_role_name == Role.name) \
                .filter(userrole.c.role_id == Role.id) \
                .filter(User.id == userrole.c.user_id) \
                .all()
            community_user_ids = [
                community_user.id for community_user in community_users]

            # query all activities
            query_action_activities = _Activity.query.outerjoin(_Flow) \
                .outerjoin(_FlowAction).outerjoin(_FlowActionRole)

            # query activities by tab is wait
            if tab == WEKO_WORKFLOW_WAIT_TAB:
                page_wait = conditions.get('pageswait')
                size_wait = conditions.get('sizewait')
                if page_wait and page_wait[0].isnumeric():
                    page = page_wait[0]
                if size_wait and size_wait[0].isnumeric():
                    size = size_wait[0]
                query_action_activities = self.query_activites_by_tab_is_wait(
                    query_action_activities, is_admin, is_community_admin)
            # query activities by tab is all
            elif tab == WEKO_WORKFLOW_ALL_TAB:
                page_all = conditions.get('pagesall')
                size_all = conditions.get('sizeall')
                if page_all and page_all[0].isnumeric():
                    page = page_all[0]
                if size_all and size_all[0].isnumeric():
                    size = size_all[0]
                query_action_activities = self.query_activites_by_tab_is_all(
                    query_action_activities, is_admin, is_community_admin,
                    community_user_ids)
            # query activities by tab is todo
            elif tab == WEKO_WORKFLOW_TODO_TAB:
                page_todo = conditions.get('pagestodo')
                size_todo = conditions.get('sizetodo')
                if page_todo and page_todo[0].isnumeric():
                    page = page_todo[0]
                if size_todo and size_todo[0].isnumeric():
                    size = size_todo[0]
                query_action_activities = self.query_activites_by_tab_is_all(
                    query_action_activities, is_admin, is_community_admin,
                    community_user_ids)

                query_action_activities = self.query_activites_by_tab_is_todo(
                    query_action_activities, is_admin, is_community_admin)

            # Filter conditions
            query_action_activities = self.filter_conditions(
                conditions, query_action_activities)

            # Count all result
            count = query_action_activities.distinct(_Activity.id).count()
            import math
            maxpage = math.ceil(count / int(size))
            name_param = ''
            if int(page) > maxpage:
                page = 1
                name_param = 'pages' + tab
            offset = int(size) * (int(page) - 1)
            action_activities = query_action_activities \
                .distinct(_Activity.id).order_by(asc(_Activity.id)).limit(
                    size).offset(offset).all()

            # Append to do and action activities into the master list
            activities.extend(action_activities)

            # Sort the list of activity
            activities.sort(key=lambda a: a.activity_id)
            for activi in activities:
                if activi.activity_status == \
                        ActivityStatusPolicy.ACTIVITY_FINALLY:
                    activi.StatusDesc = ActionStatusPolicy.describe(
                        ActionStatusPolicy.ACTION_DONE)
                elif activi.activity_status == \
                        ActivityStatusPolicy.ACTIVITY_CANCEL:
                    activi.StatusDesc = ActionStatusPolicy.describe(
                        ActionStatusPolicy.ACTION_CANCELED)
                else:
                    activi.StatusDesc = ActionStatusPolicy.describe(
                        ActionStatusPolicy.ACTION_DOING)
                activi.User = User.query.filter_by(
                    id=activi.activity_update_user).first()
            return activities, maxpage, size, page, name_param

    def get_all_activity_list(self, community_id=None):
        """Get all activity list info.

        :return: List of activities
        """
        with db.session.no_autoflush:
            self_group_ids = [role.id for role in current_user.roles]

            db_flow_action_users = _FlowActionRole.query.filter_by(
                action_user_exclude=False).all()
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
            db_activitys = _Activity.query.filter_by().all()
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
            return activities

    def get_activity_steps(self, activity_id):
        """Get activity steps."""
        steps = []
        his = WorkActivityHistory()
        histories = his.get_activity_history_list(activity_id)
        history_dict = {}
        for history in histories:
            history_dict[history.action_id] = {
                'Updater': history.user.email,
                'Result': ActionStatusPolicy.describe(
                    self.get_activity_action_status(
                        activity_id=activity_id,
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
                            'Updater')
                        if flow_action.action_id in history_dict else '',
                        'Status': history_dict[flow_action.action_id].get(
                            'Result')
                        if flow_action.action_id in history_dict else ' '
                    })

        return steps

    def get_activity_detail(self, activity_id):
        """Get activity detail info.

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
        """Get activity action."""
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
        """Delete activity info.

        :param activity_id:
        :return:
        """
        pass

    def get_activity_index_search(self, activity_id):
        """Get page info after item search."""
        from weko_records.api import ItemsMetadata
        from flask_babelex import gettext as _
        from werkzeug.utils import import_string
        from invenio_pidstore.resolver import Resolver
        from .views import check_authority_action
        from .utils import get_identifier_setting
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
        if ActivityStatusPolicy.ACTIVITY_FINALLY != \
                activity_detail.activity_status:
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
            comm = GetCommunity.get_community_by_id(
                request.args.get('community'))
            ctx = {'community': comm}
            community_id = comm.id

        # display_activity of Identifier grant
        if action_endpoint == 'identifier_grant' and item:
            text_empty = '<Empty>'
            community_id = request.args.get('community', None)
            if not community_id:
                community_id = 'Root Index'
            identifier_setting = get_identifier_setting(community_id)

            # valid date pidstore_identifier data
            if identifier_setting:
                if not identifier_setting.jalc_doi:
                    identifier_setting.jalc_doi = text_empty
                if not identifier_setting.jalc_crossref_doi:
                    identifier_setting.jalc_crossref_doi = text_empty
                if not identifier_setting.jalc_datacite_doi:
                    identifier_setting.jalc_datacite_doi = text_empty

            temporary_idt_select = 0
            temporary_idt_inputs = []
            last_idt_setting = activity.get_action_identifier_grant(
                activity_id=activity_id, action_id=action_id)
            if last_idt_setting:
                temporary_idt_select = last_idt_setting.get(
                    'action_identifier_select')
                temporary_idt_inputs.append(
                    last_idt_setting.get('action_identifier_jalc_doi'))
                temporary_idt_inputs.append(
                    last_idt_setting.get('action_identifier_jalc_cr_doi'))
                temporary_idt_inputs.append(
                    last_idt_setting.get('action_identifier_jalc_dc_doi'))

            ctx['temporary_idf_grant'] = temporary_idt_select
            ctx['temporary_idf_grant_suffix'] = temporary_idt_inputs
            ctx['idf_grant_data'] = identifier_setting
            ctx['idf_grant_input'] = IDENTIFIER_GRANT_LIST
            ctx['idf_grant_method'] = IDENTIFIER_GRANT_SUFFIX_METHOD

        return activity_detail, item, steps, action_id, cur_step, \
            temporary_comment, approval_record, step_item_login_url,\
            histories, res_check, pid, community_id, ctx

    def upt_activity_detail(self, item_id):
        """Update activity info for item id.

        :param item_id:
        :return:
        """
        try:
            with db.session.no_autoflush:
                action = _Action.query.filter_by(
                    action_endpoint='end_action').one_or_none()
                db_activity = _Activity.query.filter_by(
                    item_id=item_id).one_or_none()
                if db_activity is None:
                    return None
                db_activity.item_id = None
                db_activity.action_id = action.id
                db_activity.action_status = ActionStatusPolicy.ACTION_SKIPPED
                db_activity.activity_status =\
                    ActivityStatusPolicy.ACTIVITY_FINALLY,
            with db.session.begin_nested():
                db_history = ActivityHistory(
                    activity_id=db_activity.activity_id,
                    action_id=action.id,
                    action_version=action.action_version,
                    action_status=ActionStatusPolicy.ACTION_DONE,
                    action_user=current_user.get_id(),
                    action_date=db_activity.activity_start,
                    action_comment=ActionCommentPolicy.FINALLY_ACTION_COMMENT
                )
                db.session.merge(db_activity)
                db.session.add(db_history)
            db.session.commit()
            return db_activity
        except NoResultFound as ex:
            current_app.logger.exception(str(ex))
            return None
        except Exception as ex:
            db.session.rollback()
            current_app.logger.exception(str(ex))
            return None

    def get_workflow_activity_by_item_id(self, object_uuid):
        """Get workflow activity status by item ID.

        :param object_uuid:
        """
        try:
            with db.session.no_autoflush:
                activity = _Activity.query.filter_by(
                    item_id=object_uuid).order_by(
                    _Activity.updated.desc()).first()
                return activity
        except Exception as ex:
            current_app.logger.error(ex)
            return None

    def update_title_and_shared_user_id(self, activity_id, title,
                                        shared_user_id):
        """
        Update title and shared user id to activity.

        :param activity_id:
        :param title:
        :param shared_user_id:
        :return:
        """
        try:
            with db.session.begin_nested():
                activity = self.get_activity_detail(activity_id)
                if activity:
                    activity.title = title
                    activity.shared_user_id = shared_user_id
                    db.session.add(activity)
            db.session.commit()
        except Exception as ex:
            current_app.logger.exception(str(ex))
            db.session.rollback()

    def get_activity_by_workflow_id(self, workflow_id):
        """Get workflow activity by workflow ID."""
        try:
            with db.session.no_autoflush:
                activitys = _Activity.query.filter_by(
                    workflow_id=workflow_id).all()
                return activitys
        except Exception as ex:
            current_app.logger.error(ex)
            return None

    def update_title(self, activity_id, title):
        """
        Update title to activity.

        :param activity_id:
        :param title:
        :return:
        """
        try:
            with db.session.begin_nested():
                activity = self.get_activity_detail(activity_id)
                if activity:
                    activity.title = title
                    db.session.add(activity)
            db.session.commit()
        except Exception as ex:
            current_app.logger.exception(str(ex))
            db.session.rollback()


class WorkActivityHistory(object):
    """Operated on the Activity."""

    def create_activity_history(self, activity):
        """Create new activity history.

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
            action_comment=activity.get('commond'),
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
        """Get activity history list info.

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
        """Get activity history detail info.

        :param activity_id:
        :return:
        """
        pass

    def upd_activity_history_detail(self, activity_id, action_id):
        """Get activity history detail info.

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
    """The class about item."""

    def publish(pid, record):
        r"""Record publish  status change view.

        Change record publish status with given status and renders record
        export template.

        :param pid: PID object.
        :param record: Record object.
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

    def update_status(pid, record, status='1'):
        r"""Record update status.

        :param pid: PID object.
        :param record: Record object.
        :param status: Publish status (0: publish, 1: private).
        """
        from invenio_db import db
        from weko_deposit.api import WekoIndexer
        publish_status = record.get('publish_status')
        if not publish_status:
            record.update({'publish_status': status})
        else:
            record['publish_status'] = status

        record.commit()
        db.session.commit()

        indexer = WekoIndexer()
        indexer.update_publish_status(record)

    def set_item_relation(self, relation_data, record):
        """Set relation info of item.

        :param relation_data: item relation data
        :param record: item info
        """
        from weko_deposit.api import WekoIndexer

        indexer = WekoIndexer()
        indexer.update_relation_info(record, relation_data)


class GetCommunity(object):
    """Get Community Info."""

    @classmethod
    def get_community_by_id(self, community_id):
        """Get Community by ID."""
        from invenio_communities.models import Community
        c = Community.get(community_id)
        return c
