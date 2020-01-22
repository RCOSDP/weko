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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""WEKO3 pytest docstring."""

from helpers import insert_user_to_db, login_user_via_session
from mock import mock, patch
from pytest_invenio.fixtures import app, database, es_clear
from weko_records.api import ItemsMetadata
from weko_workflow.models import Action, WorkFlow


def insert_data_for_activity(database):
    """Insert_data_for_activity."""
    from weko_workflow.models import ActivityAction, ActionStatus
    flow_id = "ed1fc1a1-db3d-450c-a093-b85e63d3d647"
    item_id = "f7ab31d0-f401-4e60-adc9-000000000111"
    record = {'item_1574156725144': {'subitem_usage_location': 'sage location',
                                     'pubdate': '2019-12-08',
                                     '$schema': '/items/jsonschema/19',
                                     'title': 'username'}}
    insert_record_metadata(database, item_id, record)
    insert_flow(database, 1, flow_id, "Flow Name", 1, "A")
    insert_item_type_name(database, "地点情報利用申請", True, True)
    insert_item_type(database, 1, {}, {}, {}, 1, 1, True)
    insert_action_to_db(database)

    # Insert a flow contain 5 steps
    insert_flow_action(database, flow_id, 1, 1)
    insert_flow_action(database, flow_id, 2, 5)
    insert_flow_action(database, flow_id, 8, 2)
    insert_flow_action(database, flow_id, 9, 3)
    insert_flow_action(database, flow_id, 11, 4)

    insert_workflow(database, 1, flow_id, "Flow Name", 1, 1, 1)
    insert_activity(database, "A-20200108-00100", item_id, 1, 1, 8)
    action_status = ActionStatus(action_status_id="A",
                                 action_status_name="Name")
    database.session.add(action_status)
    database.session.commit()
    insert_activity_action(database, "A-20200108-00100", 8, 2)


def test_auto_fill_title(app, database, client, es_clear):
    """Test_auto_fill_title."""
    # Login before making request
    insert_user_to_db(database)
    login_user_via_session(client, 1)
    insert_data_for_activity(database)
    steps = 'weko_workflow/term_and_condition.html', 'need_file', 'record',\
            'json_schema', 'schema_form', 'item_save_uri', 'files',\
            'endpoints', 'need_thumbnail', 'files_thumbnail', \
            'allow_multi_thumbnail'
    with mock.patch('weko_workflow.views.item_login', return_value=steps):
        res1 = client.get('/workflow/activity/detail/A-20200108-00100?status'
                          '=ToDo?itemtitle=titletest')
        assert res1.status_code == 200


def insert_item_type_name(database, name, has_site_license, is_active):
    """Insert_item_type_name."""
    from weko_records.models import ItemTypeName

    item_name = ItemTypeName(name=name,
                             has_site_license=has_site_license,
                             is_active=is_active)
    database.session.add(item_name)
    database.session.commit()


def insert_item_type(database, name_id, schema, form, render, tag, version_id,
                     is_deleted):
    """Insert_item_type."""
    from weko_records.models import ItemType

    item_type = ItemType(name_id=1, harvesting_type=False, schema={}, form={},
                         render={}, tag=tag, version_id=version_id,
                         is_deleted=is_deleted)
    database.session.add(item_type)
    database.session.commit()


def insert_flow(database, _id, flow_id, flow_name, flow_user, flow_status):
    """Insert_flow."""
    from weko_workflow.models import FlowDefine

    flow = FlowDefine(id=_id, flow_id=flow_id, flow_name=flow_name,
                      flow_user=flow_user, flow_status=flow_status)
    database.session.add(flow)
    database.session.commit()


def insert_index(database, id, parent, position, index_name,
                 index_name_english, index_link_name_english):
    """Insert_index."""
    from weko_index_tree.models import Index
    index = Index(id=id, parent=parent, position=position,
                  index_name=index_name, index_name_english=index_name_english,
                  index_link_name_english=index_link_name_english)
    database.session.add(index)
    database.session.commit()


def insert_workflow(database, id, flows_id, flows_name, itemtype_id, flow_id,
                    index_tree_id):
    """Insert_workflow."""
    from weko_workflow.models import WorkFlow

    workflow = WorkFlow(id=id, flows_id=flows_id, flows_name=flows_name,
                        itemtype_id=itemtype_id, flow_id=flow_id,
                        index_tree_id=index_tree_id)
    database.session.add(workflow)
    database.session.commit()


def insert_activity(database, activity_id, item_id, workflow_id, flow_id,
                    current_action_id):
    """Insert_activity."""
    from weko_workflow.models import Activity

    activity = Activity(activity_id=activity_id, item_id=item_id,
                        workflow_id=workflow_id, flow_id=flow_id,
                        activity_start="2020-01-08 09:14:14",
                        activity_confirm_term_of_use=False,
                        action_id=current_action_id)
    database.session.add(activity)
    database.session.commit()
    return activity


def insert_record_metadata(database, id, jsondata):
    """Insert_record_metadata."""
    from invenio_records.models import RecordMetadata

    record_metadata = RecordMetadata(id=id, json=jsondata, version_id=1)
    database.session.add(record_metadata)
    database.session.commit()


def insert_flow_action(database, flow_id, action_id, action_order):
    """Insert_flow_action."""
    from weko_workflow.models import FlowAction

    flow_action = FlowAction(flow_id=flow_id, action_id=action_id,
                             action_order=action_order, action_status="A",
                             action_date="2020-01-08 09:14:14")
    database.session.add(flow_action)
    database.session.commit()


def insert_activity_action(database, activity_id, action_id, action_handler):
    """Insert_activity_action."""
    from weko_workflow.models import ActivityAction, ActionStatus

    activity_action = ActivityAction(activity_id=activity_id,
                                     action_id=action_id,
                                     action_status="A",
                                     action_handler=action_handler)
    database.session.add(activity_action)
    database.session.commit()


def insert_action_to_db(database):
    """Insert_action_to_db."""
    from weko_workflow.models import Action, FlowDefine, FlowAction

    action_start = Action(status='N', id=1, created='2019-11-20 12:06:14',
                          updated='2019-11-20 12:06:14', action_name='Start',
                          action_desc='Indicates that the action has started.',
                          action_endpoint='begin_action',
                          action_version='2018-05-15 00:00:00',
                          action_lastdate='2018-05-15 00:00:00')
    action_end = Action(status='N', id=2, created='2019-11-20 12:06:14',
                        updated='2019-11-20 12:06:14', action_name='End',
                        action_desc='Indicates that the action has been '
                                    'completed.',
                        action_endpoint='end_action',
                        action_version='2018-05-15 00:00:00',
                        action_lastdate='2018-05-15 00:00:00')
    action_item_registration = Action(status='N', id=3,
                                      created='2019-11-20 12:06:14',
                                      updated='2019-11-20 12:06:14',
                                      action_name='Item Registration',
                                      action_desc='Registering items.',
                                      action_endpoint='item_login',
                                      action_version='2018-05-15 00:00:00',
                                      action_lastdate='2018-05-15 00:00:00')
    action_approval = Action(
        status='N',
        id=4, created='2019-11-20 12:06:14',
        updated='2019-11-20 12:06:14',
        action_name='Approval',
        action_desc='Approval action for approval requested items.',
        action_endpoint='approval',
        action_version='2018-05-15 00:00:00',
        action_lastdate='2018-05-15 00:00:00'
    )
    action_item_registration_application = Action(
        status='N',
        id=8,
        created='2019-11-20 12:06:14',
        updated='2019-11-20 12:06:14',
        action_name='Item Registration for Usage Application',
        action_desc='Item Registration for Usage Application.',
        action_endpoint='item_login_application',
        action_version='2018-05-15 00:00:00',
        action_lastdate='2018-05-15 00:00:00',
        action_is_need_agree=True
    )
    action_item_link = Action(status='N', id=5, created='2019-11-20 12:06:14',
                              updated='2019-11-20 12:06:14',
                              action_name='Item Link',
                              action_desc='Plug-in for link items.',
                              action_endpoint='item_link',
                              action_version='2018-05-15 00:00:00',
                              action_lastdate='2018-05-15 00:00:00')
    action_oa_policy = Action(status='N', id=6, created='2019-11-20 12:06:14',
                              updated='2019-11-20 12:06:14',
                              action_name='OA Policy Confirmation',
                              action_desc='Action for OA Policy confirmation.',
                              action_endpoint='oa_policy',
                              action_version='2018-05-15 00:00:00',
                              action_lastdate='2018-05-15 00:00:00')
    action_grant = Action(status='N', id=7, created='2019-11-20 12:06:14',
                          updated='2019-11-20 12:06:14',
                          action_name='Identifier Grant',
                          action_desc='Select DOI issuing organization and '
                                      'CNRI.',
                          action_endpoint='identifier_grant',
                          action_version='2018-05-15 00:00:00',
                          action_lastdate='2018-05-15 00:00:00')
    action_approval_guarantor = Action(status='N', id=9,
                                       created='2019-11-20 12:06:14',
                                       updated='2019-11-20 12:06:14',
                                       action_name='Approval by Guarantor',
                                       action_desc='Approval action performed '
                                                   'by Guarantor.',
                                       action_endpoint='approval_guarantor',
                                       action_version='2018-05-15 00:00:00',
                                       action_lastdate='2018-05-15 00:00:00')
    action_approval_advisor = Action(status='N', id=10,
                                     created='2019-11-20 12:06:14',
                                     updated='2019-11-20 12:06:14',
                                     action_name='Approval by Advisor',
                                     action_desc='Approval action performed '
                                                 'by Advisor.',
                                     action_endpoint='approval_advisor',
                                     action_version='2018-05-15 00:00:00',
                                     action_lastdate='2018-05-15 00:00:00')
    action_approval_admin = Action(status='N', id=11,
                                   created='2019-11-20 12:06:14',
                                   updated='2019-11-20 12:06:14',
                                   action_name='Approval by Administrator',
                                   action_desc='Approval action performed '
                                               'by Administrator.',
                                   action_endpoint='approval_administrator',
                                   action_version='2018-05-15 00:00:00',
                                   action_lastdate='2018-05-15 00:00:00')

    database.session.add(action_start)
    database.session.add(action_end)
    database.session.add(action_item_registration)
    database.session.add(action_item_registration_application)
    database.session.add(action_approval)
    database.session.add(action_item_link)
    database.session.add(action_oa_policy)
    database.session.add(action_grant)
    database.session.add(action_approval_guarantor)
    database.session.add(action_approval_advisor)
    database.session.add(action_approval_admin)
