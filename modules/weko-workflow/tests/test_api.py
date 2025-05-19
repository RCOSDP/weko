from flask_login.utils import login_user

from weko_workflow.api import Flow, WorkActivity
from weko_workflow.models import Activity, ActivityHistory, ActivityAction
from mock import patch, MagicMock
import pytest
from invenio_pidstore.errors import PIDAlreadyExists

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_Flow_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_Flow_action(app, client, users, db, action_data):
    with app.test_request_context():
        login_user(users[2]["obj"])
        _flow = Flow()
        flow = _flow.create_flow({'flow_name': 'create_flow_test'})
        assert flow.flow_name == 'create_flow_test'

        _flow_data = [
            {
                "id":"2",
                "name":"End",
                "date":"2022-12-09",
                "version":"1.0.0",
                "user":"2",
                "user_deny": False,
                "role":"0",
                "role_deny": False,
                "workflow_flow_action_id":8,
                "send_mail_setting": {
                    "request_approval": False,
                    "inform_approval": False,
                    "inform_reject": False},
                "action":"ADD"
            },
            {
                "id":"1",
                "name":"Start",
                "date":"2022-12-09",
                "version":"1.0.0",
                "user":"2",
                "user_deny": False,
                "role":"0",
                "role_deny": False,
                "workflow_flow_action_id":7,
                "send_mail_setting": {
                    "request_approval": False,
                    "inform_approval": False,
                    "inform_reject": False
                },
                "action":"ADD"
            },
            {
                "id":"3",
                "name":"Item Registration",
                "date":"2022-12-9",
                "version":"1.0.1",
                "user":"2",
                "user_deny": False,
                "role":"0",
                "role_deny": False,
                "workflow_flow_action_id":-1,
                "send_mail_setting": {
                    "request_approval": False,
                    "inform_approval": False,
                    "inform_reject": False
                },
            "action":"ADD"
            }
        ]
        _flow.upt_flow_action(flow.flow_id, _flow_data)

        flow_id = flow.flow_id
        flow = _flow.get_flow_detail(flow_id)
        assert flow.flow_name == 'create_flow_test'

        res = _flow.del_flow(flow_id)
        assert res['code'] == 500

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_Flow_get_flow_action_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_Flow_get_flow_action_list(db,workflow):
    res = Flow().get_flow_action_list(workflow["flow"].id)
    assert len(res) == 7
    assert res[0].action_order == 1
    assert res[1].action_order == 2
    assert res[2].action_order == 3
    assert res[3].action_order == 4
    assert res[4].action_order == 5
    assert res[5].action_order == 6
    assert res[6].action_order == 7

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_filter_by_date -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_filter_by_date(app, db):
    query = db.session.query()
    activity = WorkActivity()
    assert activity.filter_by_date('2022-01-01', '2022-01-02', query)


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_get_all_activity_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_get_all_activity_list(app, client, users, db_register):
    with app.test_request_context():
        login_user(users[2]["obj"])
        activity = WorkActivity()
        activities = activity.get_all_activity_list()
        assert len(activities) == 13


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_get_activity_index_search -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_get_activity_index_search(app, db_register):
    activity = WorkActivity()
    with app.test_request_context():
        activity_detail, item, steps, action_id, cur_step, \
            temporary_comment, approval_record, step_item_login_url,\
            histories, res_check, pid, community_id, ctx = activity.get_activity_index_search('1')
        assert activity_detail.id == 1
        assert activity_detail.action_id == 1
        assert activity_detail.title == 'test'
        assert activity_detail.activity_id == '1'
        assert activity_detail.flow_id == 1
        assert activity_detail.workflow_id == 1
        assert activity_detail.action_order == 1


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_upt_activity_detail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_upt_activity_detail(app, db_register, db_records):
    activity = WorkActivity()
    db_activity = activity.upt_activity_detail(db_records[2][2].id)
    assert db_activity.id == 4
    assert db_activity.action_id == 2
    assert db_activity.title == 'test item1'
    assert db_activity.activity_id == '2'
    assert db_activity.flow_id == 1
    assert db_activity.workflow_id == 1
    assert db_activity.action_order == 1


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_get_corresponding_usage_activities -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_get_corresponding_usage_activities(app, db_register):
    activity = WorkActivity()
    usage_application_list, output_report_list = activity.get_corresponding_usage_activities(1)
    assert usage_application_list == {'activity_data_type': {}, 'activity_ids': []}
    assert output_report_list == {'activity_data_type': {}, 'activity_ids': []}

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_init_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_init_activity(app, users, item_type, workflow):
    """
    Test init_activity

    Args:
        app (fixture): 
        users (fixture): user info
        item_type (fixture): item_type data
        workflow (fixture): data of FlowDefine, FlowAction, WorkFlow
    """
    workflow_id = workflow['workflow'].id
    flow_def_id = workflow['flow'].id
    with app.test_request_context():
        login_user(users[2]["obj"])
        # send param
        input = {'workflow_id': workflow_id, 'flow_id': flow_def_id}

        # 51992 case.01(init_activity)
        q = Activity.query.all()
        assert len(q) == 0
        q = ActivityHistory.query.all()
        assert len(q) == 0
        q = ActivityAction.query.all()
        assert len(q) == 0

        activity = WorkActivity()
        input = {'workflow_id': workflow_id, 'flow_id': flow_def_id}
        activity_detail = activity.init_activity(input)
        assert isinstance(activity_detail, Activity)
        q = Activity.query.all()
        assert len(q) == 1
        q = ActivityHistory.query.all()
        assert len(q) == 1
        q = ActivityAction.query.all()
        assert len(q) == 7

        
        with patch("weko_workflow.api.current_app") as mock_current_app:
            mock_current_app.config = {
                'WEKO_WORKFLOW_ENABLE_SHOWING_TERM_OF_USE': True,
                'WEKO_ITEMS_UI_SHOW_TERM_AND_CONDITION': ['itemtype_with_terms'],
                'WEKO_WORKFLOW_MAX_ACTIVITY_ID': 1000000,
                'WEKO_WORKFLOW_ACTIVITY_ID_FORMAT': 'A-{}-{}'
            }

            input = {'workflow_id': workflow_id, 'flow_id': flow_def_id, 'activity_confirm_term_of_use': False}
            # 51992 case.02(init_activity)
            with patch('weko_workflow.api.get_item_type_name', return_value='itemtype_with_terms'):
                activity_detail = activity.init_activity(input)
                assert activity_detail.activity_confirm_term_of_use == False

            # 51992 case.03(init_activity)
            with patch('weko_workflow.api.get_item_type_name', return_value='itemtype_with_terms2'):
                activity_detail = activity.init_activity(input)
                assert activity_detail.activity_confirm_term_of_use == True

            # 51992 case.04(init_activity)
            input = {'workflow_id': workflow_id, 'flow_id': flow_def_id}
            activity_detail = activity.init_activity(input)
            assert activity_detail.activity_login_user == str(users[2]["obj"].id)
            
            # 51992 case.05(init_activity)
            input = {'workflow_id': workflow_id, 'flow_id': flow_def_id, 'activity_login_user': 1}
            activity_detail = activity.init_activity(input)
            assert activity_detail.activity_login_user == 1
            
            # 51992 case.08(init_activity)
            input = {'workflow_id': workflow_id, 'flow_id': flow_def_id, 'related_title': 'Test%20Title'}
            activity_detail = activity.init_activity(input)
            assert activity_detail.extra_info["related_title"] == 'Test Title'
            
            # 51992 case.09(init_activity)
            input = {'workflow_id': workflow_id, 'flow_id': flow_def_id}
            with patch("weko_workflow.api.PersistentIdentifier.create", side_effect=Exception("Test Error")):
                with pytest.raises(Exception):
                    activity.init_activity(input)
            
            # 51992 case.10(init_activity)
            with patch("weko_workflow.api.db.session.add", side_effect=Exception("Test Error")):
                input = {'workflow_id': workflow_id, 'flow_id': flow_def_id}
                with pytest.raises(Exception):
                    activity.init_activity(input)

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_init_activity_with_single_flow_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_init_activity_with_single_flow_action(app, users, item_type, workflow_one, mocker):
    """
    Test init_activity when FlowAction return a data

    Args:
        app (fixture): 
        users (fixture): user info
        item_type (fixture): item_type data
        workflow_one (fixture): one FlowAction workflow
        mocker (fixture): mocker
    """
    workflow_id = workflow_one["workflow"].flows_id
    flow_id = int(workflow_one["flow"].id)
    work_activity = WorkActivity()
    # send param
    input = {'workflow_id': workflow_id, 'flow_id': flow_id}
    
    # mock
    mocker.patch("weko_workflow.api.PersistentIdentifier.create")
    mocker.patch("weko_workflow.api.db.session.add")

    # 51992 case.06(init_activity)
    with app.test_request_context():
        result = work_activity.init_activity(input)
        
        assert result.action_id == 0
        assert result.action_order == 0


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_init_activity_with_no_begin_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_init_activity_with_no_begin_action(app, users, item_type, workflow, no_begin_action, mocker):
    """
    Test init_activity when workflow_action has not begin_action

    Args:
        app (fixture): 
        users (fixture): user info
        item_type (fixture): item_type data
        workflow (fixture): data of FlowDefine, FlowAction, WorkFlow
        no_begin_action(fixture): update begin_action to other_action
        mocker (fixture): mocker
    """
    workflow_id = workflow['workflow'].id
    flow_def_id = workflow['flow'].id
    work_activity = WorkActivity()
    # send param
    input = {'workflow_id': workflow_id, 'flow_id': flow_def_id}
    
    # mock
    mocker.patch("weko_workflow.api.PersistentIdentifier.create")
    mocker.patch("weko_workflow.api.db.session.add")

    # 51992 case.07(init_activity)
    with app.test_request_context():
        with pytest.raises(AttributeError):
            result = work_activity.init_activity(input)
    
            assert result.action_id == 0  # action_id should be the initial value
    