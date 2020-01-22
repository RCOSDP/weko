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

import mock
import pytest
from pytest_invenio.fixtures import app, database
from weko_index_tree.api import Indexes
from weko_index_tree.utils import get_index_id
from weko_workflow.api import WorkActivity, WorkFlow
from weko_workflow.models import Activity
from weko_workflow.models import WorkFlow as _WorkFlow
from weko_workflow.utils import is_usage_application_item_type


def test_get_current_language(app):
    """Test_get_current_language."""
    from weko_workflow.utils import get_current_language
    # Note:whenever use app.config,we need to use app.app_context
    with app.app_context():
        mock_vn = mock.MagicMock()
        mock_vn.language = 'vn'
        # Case current language is not in list(ja,en) languages
        with mock.patch('weko_workflow.utils.current_i18n', mock_vn):
            assert get_current_language() == 'en'
        mock_en = mock.MagicMock()
        mock_en.language = 'en'
        # Case current language is en
        with mock.patch('weko_workflow.utils.current_i18n', mock_en):
            assert get_current_language() == 'en'
        mock_ja = mock.MagicMock()
        mock_ja.language = 'ja'
        # Case current language is ja
        with mock.patch('weko_workflow.utils.current_i18n', mock_ja):
            assert get_current_language() == 'ja'


def test_get_term_and_condition_content(app):
    """Test_get_term_and_condition_content."""
    from weko_workflow.utils import get_term_and_condition_content
    # Change location of file location to test folder
    with app.app_context():
        app.config['WEKO_WORKFLOW_TERM_AND_CONDITION_FILE_LOCATION'] = \
            '/code/tests/term_and_condition/'
    # Case en
    with mock.patch('weko_workflow.utils.get_current_language',
                    return_value='en'):
        assert get_term_and_condition_content('ライフ利用申請')
        with pytest.raises(Exception) as ex:
            assert get_term_and_condition_content('Not Exist Item Type')
            assert "No such file or directory" in str(ex.value)
    # Case ja
    with mock.patch('weko_workflow.utils.get_current_language',
                    return_value='ja'):
        assert get_term_and_condition_content('ライフ利用申請')


def test_get_index_id(app, database):
    """Test_get_index_id."""
    # WorkActivity mocked object
    mock_work_activity = mock.MagicMock()
    activity = Activity()
    activity.workflow_id = 'workflow_id'
    activity.id = '123'
    activity.activity_id = '123'
    mock_work_activity.return_value.get_activity_detail.return_value = activity
    # WorkFlow mocked object
    mock_workflow = mock.MagicMock()
    temp_wf = WorkFlow()
    temp_wf.itemtype_id = '111'
    temp_wf.id = '123'
    temp_wf.index_tree_id = 'index_tree_id'
    mock_workflow.return_value.get_workflow_by_id.return_value = temp_wf

    # Case workflow has index tree ID
    with mock.patch('weko_workflow.api.WorkActivity', mock_work_activity,
                    mock_work_activity), mock.patch(
        'weko_workflow.api.WorkFlow', mock_workflow), mock.patch.object(
            Indexes, 'get_index', return_value='123'):
        assert get_index_id('activity_id') == 'index_tree_id'

    # Case workflow has index tree ID but DataBase doesn't exist that indexTree
    with mock.patch('weko_workflow.api.WorkActivity', mock_work_activity,
                    mock_work_activity), mock.patch(
        'weko_workflow.api.WorkFlow', mock_workflow), mock.patch.object(
            Indexes, 'get_index', return_value=None):
        assert not get_index_id('activity_id')
    # Case workflow does not has index tree id
    mock_workflow_none = mock.MagicMock()
    temp_wf = WorkFlow()
    temp_wf.index_tree_id = None
    temp_wf.id = '123'
    mock_workflow_none.return_value.get_workflow_by_id.return_value = temp_wf
    with mock.patch('weko_workflow.api.WorkActivity', mock_work_activity,
                    mock_work_activity), mock.patch(
        'weko_workflow.api.WorkFlow', mock_workflow_none), mock.patch.object(
            Indexes, 'get_index', return_value=None):
        assert not get_index_id('activity_result')


def test_check_usage_application_item_type():
    """Test_check_usage_application_item_type."""
    m = mock.MagicMock()
    temp_wf = WorkFlow()
    temp_wf.itemtype_id = '111'
    temp_wf.id = '123'
    m.return_value.get_workflow_by_id.return_value = temp_wf

    # Case usage application
    with mock.patch('weko_workflow.utils.WorkFlow', m), mock.patch(
        'weko_workflow.utils.get_item_type_name',
        return_value='ライフ利用申請'), mock.patch.object(Indexes, 'get_index',
                                                   return_value=None):
        activity_result = Activity()
        activity_result.workflow_id = '132'
        assert is_usage_application_item_type(activity_result)

    # Case not usage application
    with mock.patch('weko_workflow.utils.WorkFlow', m), mock.patch(
        'weko_workflow.utils.get_item_type_name',
        return_value='1ライフ利用申請'), mock.patch.object(Indexes, 'get_index',
                                                    return_value=None):
        activity_result = Activity()
        activity_result.workflow_id = '132'
        assert not is_usage_application_item_type(activity_result)


def insert_data_for_activity(database):
    """Insert_data_for_activity."""
    from weko_workflow.models import ActivityAction, ActionStatus
    flow_id = "ed1fc1a1-db3d-450c-a093-b85e63d3d647"
    item_id = "f7ab31d0-f401-4e60-adc9-000000000111"
    record = {'item_1574156725144': {'subitem_usage_location': 'sage location',
                                     'pubdate': '2019-12-08',
                                     '$schema': '/items/jsonschema/19',
                                     'title': 'username'}}
    from helpers import insert_activity, insert_flow, insert_record_metadata,\
        insert_workflow, insert_action_to_db, insert_flow_action,\
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
    action_status_a = ActionStatus(action_status_id="A",
                                   action_status_name="Name")
    database.session.add(action_status_a)
    action_status_b = ActionStatus(action_status_id="B",
                                   action_status_name="NameB")
    database.session.add(action_status_b)
    action_status_f = ActionStatus(action_status_id="F",
                                   action_status_name="NameB")
    database.session.add(action_status_f)
    database.session.commit()


def test_init_activity(database, app, client):
    """Test_init_activity."""
    from helpers import insert_user_to_db, login_user_via_session
    from weko_workflow.api import WorkActivity
    insert_user_to_db(database)
    login_user_via_session(client, 1)
    insert_data_for_activity(database)
    activity = WorkActivity()
    activity.init_activity({'flow_id': 1,
                            'itemtype_id': 1,
                            'workflow_id': 1})
    from weko_workflow.models import Activity as _Activity
    assert len(_Activity.query.all()) == 1


def test_exclude_admin_workflow(app, database, client):
    """Test_exclude_admin_workflow."""
    from weko_workflow.utils import exclude_admin_workflow
    from weko_workflow.models import Action
    from helpers import insert_workflow, insert_flow, insert_flow_action,\
        login_user_via_session
    # Insert a new workflow to test
    flow_id = "ed1fc1a1-db3d-450c-a093-b85e63d3d648"
    insert_flow(database, 2, flow_id, "Flow Name2", 1, "A")
    insert_flow_action(database, flow_id, 1, 1)
    insert_flow_action(database, flow_id, 2, 4)
    insert_flow_action(database, flow_id, 3, 2)
    insert_flow_action(database, flow_id, 11, 3)
    insert_workflow(database, 2, flow_id, "Flow Name2", 1, 2, 1)

    # Login as admin
    workflow_list = _WorkFlow.query.all()
    assert len(workflow_list) == 2
    # current user is admin,list workflow should be 2
    with mock.patch('weko_workflow.utils.get_current_user_role',
                    return_value="Administrator"):
        assert len(exclude_admin_workflow(workflow_list)) == 2

    # Login as non-admin
    workflow_list = _WorkFlow.query.all()
    with mock.patch('weko_workflow.utils.get_current_user_role',
                    return_value="General"):
        assert len(exclude_admin_workflow(workflow_list)) == 1
