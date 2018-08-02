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

from invenio_db import db
from sqlalchemy import asc

from .models import Flow


class WorkFlow(object):
    """Operated on the Flow"""
    def create_flow(self, flow):
        """
        Create new flow
        :param flow:
        :return:
        """
        pass

    def upt_flow(self, flow):
        """
        Update flow info
        :param flow:
        :return:
        """
        pass

    def get_flow_list(self):
        """
        get flow list info
        :return:
        """
        with db.session.no_autoflush:
            query = Flow.query.distinct(Flow.flow_id).order_by(
                asc(Flow.flow_id))
            return query.all()

    def get_flow_detail(self, flow_id):
        """
        get flow detail info
        :param flow_id:
        :return:
        """
        with db.session.no_autoflush:
            query = Flow.query.filter_by(
                flow_id=flow_id).order_by(
                asc(Flow.action_order))
            return query.all()

    def del_flow(self, flow_id):
        """
        Delete flow info
        :param flow_id:
        :return:
        """
        pass

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
        pass

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

class WorkFLows(object):
    """Operated on the Flows"""
    def create_flows(self, flows):
        """
        Create new flows
        :param flows:
        :return:
        """
        pass

    def upt_flows(self, flows):
        """
        Update flows info
        :param flows:
        :return:
        """
        pass

    def get_flows_list(self):
        """
        get flows list info
        :return:
        """
        pass

    def get_flows_detail(self, flows_id):
        """
        get flows detail info
        :param flows_id:
        :return:
        """
        pass

    def del_flows(self, flows_id):
        """
        Delete flows info
        :param flows_id:
        :return:
        """
        pass

class WorkActivity(object):
    """Operated on the Activity"""
    def create_activity(self, activity):
        """
        Create new activity
        :param activity:
        :return:
        """
        pass

    def upt_activity(self, activity):
        """
        Update activity info
        :param activity:
        :return:
        """
        pass

    def get_activity_list(self):
        """
        get activity list info
        :return:
        """
        pass

    def get_activity_detail(self, activity_id):
        """
        get activity detail info
        :param activity_id:
        :return:
        """
        pass

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
        pass

    def get_activity_history_list(self):
        """
        get activity history list info
        :return:
        """
        pass

    def get_activity_history_detail(self, activity_id):
        """
        get activity history detail info
        :param activity_id:
        :return:
        """
        pass
