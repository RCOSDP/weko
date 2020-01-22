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

"""WEKO3 pytest docstring."""


def login_user_via_session(client, user_id):
    """Login a user via the session."""
    with client.session_transaction() as sess:
        sess['user_id'] = user_id
        sess['_fresh'] = True


def insert_user_to_db(database):
    """Insert_user_to_db."""
    from invenio_accounts.models import User, Role

    admin_role = Role(id=1, name='System Administrator')
    database.session.add(admin_role)
    admin = User(email='admin@invenio.org', password='123456', active=True,
                 roles=[admin_role])
    non_admin = User(email='non_admin@invenio.org', password='123456',
                     active=True)
    database.session.add(admin)
    database.session.add(non_admin)
    database.session.commit()


def insert_activity_data_to_db(database):
    """Insert_activity_data_to_db."""
    from weko_records.models import ItemType, ItemTypeName
    from weko_workflow.models import Activity, FlowDefine, WorkFlow, FlowAction

    flow_define = FlowDefine(id=20,
                             flow_id="07091c20-f99a-424d-ab1d-5eea6e67f361",
                             flow_name="Flow2", flow_status="F")
    acivity = Activity(
        id=10,
        activity_id='A-20191218-00007',
        item_id="e8492239-8e49-47b3-93c3-5081a96aaf05",
        workflow_id=13,
        flow_id=20,
        activity_start='2019-12-16 10:51:02.702925',
        activity_update_user=1,
        flow_define=flow_define
    )

    work_flow = WorkFlow(id=13,
                         flows_id="07091c20-f99a-424d-ab1d-5eea6e67f361",
                         flows_name="WorkFLow2", itemtype_id=9, flow_id=20)
    item_type = ItemType(id=9, name_id=1, tag=2)
    item_type_name = ItemTypeName(id=1, name='利用報告')  #

    database.session.add(acivity)
    database.session.add(flow_define)
    database.session.add(item_type_name)  #
    database.session.add(item_type)
    database.session.add(work_flow)
    database.session.commit()


def insert_metadata_to_db(database):
    """Insert_metadata_to_db."""
    from weko_records.models import ItemMetadata

    json_str = {"lang": "en", "owner": "1", "title": "info",
                "$schema": "/items/jsonschema/9", "pubdate": "2020-01-02",
                "advisor_user_id": 4, "guarantor_user_id": 5,
                "item_1574156430076": {"subitem_fullname": "Admin"},
                "item_1574156469332": {
                    "subitem_mail_address": "info@inveniosoftware.org"},
                "item_1574156494186": {
                    "subitem_university/institution": "University"},
                "item_1574156533722": {
                    "subitem_affiliated_division/department": "Department"},
                "item_1574156555579": {
                    "subitem_dataset_usage": "Dataset Usaged"},
                "item_1574156568322": {"subitem_phone_number": "0909090909"},
                "item_1574156584363": [
                    {"subitem_affiliated_institution_name": "Name"}],
                "item_1574156621314": [
                    {"subitem_affiliated_institution_position": "Member"}],
                "item_1574156745257": {
                    "subitem_advisor_fullname": "Advisor Name"},
                "item_1574156763832": {
                    "subitem_advisor_affiliation": "Advisor Affiliation"},
                "item_1574156763833": {
                    "subitem_advisor_mail_address": "test01@hitachi.com"},
                "item_1574156763834": {
                    "subitem_guarantor_mail_address": "test02@hitachi.com"},
                "item_1574156844689": {
                    "subitem_guarantor_fullname": "Guarantor Name"},
                "item_1574156863246": {
                    "subitem_guarantor_affiliation": "Guarantor Affiliation"},
                "item_1574156962829": {
                    "subitem_research_title": "Research Title"},
                "item_1574156983988": {
                    "subitem_title": "Title"}}
    metadata = ItemMetadata(id='e8492239-8e49-47b3-93c3-5081a96aaf05',
                            item_type_id=9, json=json_str, version_id=10)
    database.session.add(metadata)
    database.session.commit()


def insert_action_data_to_db(database):
    """Insert_action_data_to_db."""
    from weko_workflow.models import Action, ActionStatus, FlowAction

    action_status = ActionStatus(id=20, action_status_id='M',
                                 action_status_name='action_doing')
    action_status2 = ActionStatus(id=21, action_status_id='F',
                                  action_status_name='action_done')

    action = Action(id=10, action_name='Start', action_endpoint='begin_action')
    action2 = Action(id=11, action_name='Item Registration(JGSS)',
                     action_endpoint='item_login')
    action3 = Action(id=12, action_name='Approval', action_endpoint='approval')
    action4 = Action(id=13, action_name='End', action_endpoint='end_action')

    flow_action = FlowAction(status='N',
                             created='2020-01-08 08:19:33',
                             updated='2020-01-08 08:19:33',
                             id=10,
                             flow_id="07091c20-f99a-424d-ab1d-5eea6e67f361",
                             action_id=11,
                             action_order=1, action_status='A',
                             action_date='2020-01-08 08:19:33')

    database.session.add(action_status)
    database.session.add(action_status2)
    database.session.add(action)
    database.session.add(action2)
    database.session.add(action3)
    database.session.add(action4)
    database.session.commit()
    database.session.add(flow_action)
    database.session.commit()


def insert_history_doing_data_to_db(database):
    """Insert_history_doing_data_to_db."""
    from weko_workflow.models import ActivityHistory

    activity_history = ActivityHistory(id=50, activity_id='A-20191218-00006',
                                       action_id=11, action_status='F',
                                       action_user=1)
    activity_history2 = ActivityHistory(id=51, activity_id='A-20191218-00006',
                                        action_id=12, action_status='M',
                                        action_user=1)
    database.session.add(activity_history)
    database.session.add(activity_history2)
    database.session.commit()


def insert_history_done_data_to_db(database):
    """Insert_history_done_data_to_db."""
    from weko_workflow.models import ActivityHistory

    activity_history = ActivityHistory(id=52, activity_id='A-20191218-00007',
                                       action_id=11, action_status='F',
                                       action_user=1)
    activity_history2 = ActivityHistory(id=53, activity_id='A-20191218-00007',
                                        action_id=12, action_status='F',
                                        action_user=1)
    activity_history3 = ActivityHistory(id=54, activity_id='A-20191218-00007',
                                        action_id=13, action_status='F',
                                        action_user=1)
    database.session.add(activity_history)
    database.session.add(activity_history2)
    database.session.add(activity_history3)
    database.session.commit()
