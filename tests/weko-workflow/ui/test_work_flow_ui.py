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
    """Insert data for activity."""
    from weko_workflow.models import ActivityAction, ActionStatus
    flow_id = "ed1fc1a1-db3d-450c-a093-b85e63d3d647"
    item_id = "f7ab31d0-f401-4e60-adc9-000000000111"
    record = {'item_1574156725144': {'subitem_usage_location': 'sage location',
                                     'pubdate': '2019-12-08',
                                     '$schema': '/items/jsonschema/19',
                                     'title': 'username'}
              }
    from helpers import insert_activity, insert_flow, insert_record_metadata,\
        insert_workflow, insert_action_to_db, insert_flow_action, \
        insert_item_type_name, insert_item_type, insert_activity_action
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


def test_show_term_and_condition(app, database, client, es_clear):
    """Test_show_term_and_condition."""
    # login before making request
    insert_user_to_db(database)
    login_user_via_session(client, 1)
    insert_data_for_activity(database)
    steps = 'weko_workflow/term_and_condition.html', 'need_file', 'record', \
            'json_schema', 'schema_form', 'item_save_uri', 'files', \
            'endpoints', 'need_thumbnail', 'files_thumbnail', \
            'allow_multi_thumbnail'
    with mock.patch('weko_workflow.views.item_login', return_value=steps):
        # Test showing term and condition
        res1 = client.get('/workflow/activity/detail/A-20200108-00100?status'
                          '=ToDo?itemtitle=titletest')
        assert res1.status_code == 200
        # Agree term and condition
        # upt_activity_agreement_step
        res2 = client.post('/workflow/activity/detail/A-20200108-00100?status'
                           '=ToDo',
                           data={'checked': 'on', 'title': 'titletest'},
                           content_type='application/x-www-form-urlencoded')
        assert res2.status_code == 200
        # Re-confirm that activity has been confirmed
        from weko_workflow.models import Activity as _Activity
        activity = _Activity.query.filter_by(
            activity_id='A-20200108-00100').one_or_none()
        print(activity.activity_id)
        assert activity.activity_confirm_term_of_use
        # Login with appover account
        login_user_via_session(client, 2)
        res1 = client.get('/workflow/activity/detail/A-20200108-00100?status'
                          '=ToDo')
        assert res1.status_code == 200
        # Login with non-admin non-approver account
        login_user_via_session(client, 3)
        res1 = client.get('/workflow/activity/detail/A-20200108-00100?status'
                          '=ToDo')
        assert res1.status_code == 200


def test_new_activity(app, database, client):
    """Test_new_activity."""
    login_user_via_session(client, 1)
    res_admin = client.get('workflow/activity/new')
    assert res_admin.status_code == 200
    login_user_via_session(client, 3)
    res_non_admin = client.get('workflow/activity/new')
    assert res_non_admin.status_code == 200
