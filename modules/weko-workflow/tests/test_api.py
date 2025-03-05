import uuid

from flask_login.utils import login_user
import pytest
from unittest.mock import patch

from weko_workflow.api import Flow, WorkActivity, WorkFlow, GetCommunity

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_Flow_create_flow -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_Flow_create_flow(app, client, users, db, action_data):
    with app.test_request_context():
        _flow = Flow()
        
        flow = _flow.create_flow({'flow_name': 'create_flow_test_root', 'repository_id': 'Root Index'})
        assert flow.flow_name == 'create_flow_test_root'
        assert flow.repository_id == 'Root Index'
        
        flow = _flow.create_flow({'flow_name': 'create_flow_test_1', 'repository_id': 'comm01'})
        assert flow.flow_name == 'create_flow_test_1'
        assert flow.repository_id == 'comm01'

        with pytest.raises(ValueError, match='Flow name cannot be empty.'):
            _flow.create_flow({'flow_name': '', 'repository_id': 'com1'})
        
        with pytest.raises(ValueError, match='Repository cannot be empty.'):
            _flow.create_flow({'flow_name': 'test_flow'})
        
        with pytest.raises(ValueError, match='Flow name is already in use.'):
            _flow.create_flow({'flow_name': 'create_flow_test_root', 'repository_id': 'Root Index'})
        
        with pytest.raises(ValueError, match='Repository is not found.'):
            _flow.create_flow({'flow_name': 'test_flow', 'repository_id': '999'})

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_Flow_upt_flow -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_Flow_upt_flow(app, client, users, db, action_data):
    with app.test_request_context():
        _flow = Flow()
        flow = _flow.create_flow({'flow_name': 'upt_flow_test', 'repository_id': 'Root Index'})
        
        flow = _flow.upt_flow(flow.flow_id, {'flow_name': 'upt_flow_test_1', 'repository_id': 'Root Index'})
        assert flow.flow_name == 'upt_flow_test_1'
        assert flow.repository_id == 'Root Index'
        
        flow = _flow.upt_flow(flow.flow_id, {'flow_name': 'upt_flow_test_1', 'repository_id': 'comm01'})
        assert flow.flow_name == 'upt_flow_test_1'
        assert flow.repository_id == 'comm01'
        
        with pytest.raises(ValueError, match='Flow name cannot be empty.'):
            _flow.upt_flow(flow.flow_id, {'flow_name': '', 'repository_id': 'Root Index'})
        
        with pytest.raises(ValueError, match='Repository cannot be empty.'):
            _flow.upt_flow(flow.flow_id, {'flow_name': 'upt_flow_test_1', 'repository_id': ''})
        
        flow1 = _flow.create_flow({'flow_name': 'upt_flow_test', 'repository_id': 'comm01'})
        db.session.add(flow)
        db.session.add(flow1)
        db.session.commit()
        with pytest.raises(ValueError, match='Flow name is already in use.'):
            _flow.upt_flow(flow.flow_id, {'flow_name': 'upt_flow_test', 'repository_id': 'Root Index'})
        
        with pytest.raises(ValueError, match='Repository is not found.'):
            _flow.upt_flow(flow.flow_id, {'flow_name': 'test_flow', 'repository_id': '999'})

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_Flow_get_flow_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_Flow_get_flow_list(app, client, users, db, action_data):
    with app.test_request_context():
        _flow = Flow()
        flow = _flow.create_flow({'flow_name': 'get_flow_list_test', 'repository_id': 'Root Index'})
        db.session.add(flow)
        db.session.commit()
        
        login_user(users[2]["obj"])
        res = _flow.get_flow_list()
        assert len(res) == 1
        assert res[0] == flow
        
        login_user(users[3]["obj"])
        res = _flow.get_flow_list()
        assert len(res) == 0
        
        flow_com = _flow.create_flow({'flow_name': 'flow_comm01', 'repository_id': 'comm01'})
        db.session.add(flow_com)
        db.session.commit()
        
        res = _flow.get_flow_list()
        assert len(res) == 1
        assert res[0] == flow_com


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_Flow_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_Flow_action(app, client, users, db, action_data):
    with app.test_request_context():
        login_user(users[2]["obj"])
        _flow = Flow()
        flow = _flow.create_flow({'flow_name': 'create_flow_test', 'repository_id': 'Root Index'})
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

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkFlow_upt_workflow -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkFlow_upt_workflow(app, db, workflow):
    w = workflow["workflow"]
    _workflow = WorkFlow()
    data = dict(flows_id=w.flows_id,
                flows_name='test workflow01',
                itemtype_id=1,
                flow_id=1,
                index_tree_id=None,
                open_restricted=False,
                location_id=None,
                is_gakuninrdm=False,
                repository_id='Root Index')
        
    res = _workflow.upt_workflow(data)
    for key in data:
        assert getattr(res, key) == data[key]
    
    res = _workflow.upt_workflow({'flows_id': uuid.uuid4()})
    assert res is None
    
    with pytest.raises(AssertionError):
        _workflow.upt_workflow(None)

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkFlow_get_workflow_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkFlow_get_workflow_list(app, db, workflow, users):
    w = workflow["workflow"]
    _workflow = WorkFlow()
    res = _workflow.get_workflow_list()
    assert len(res) == 1
    
    user = users[2]["obj"]
    res = _workflow.get_workflow_list(user=user)
    assert len(res) == 1
    
    user = users[3]["obj"]
    res = _workflow.get_workflow_list(user=user)
    assert len(res) == 0
    
    w.repository_id = "comm01"
    db.session.commit()
    user = users[3]["obj"]
    res = _workflow.get_workflow_list(user=user)
    assert len(res) == 1

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

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_GetCommunity_get_community_by_root_node_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_GetCommunity_get_community_by_root_node_id(db):
    communities = GetCommunity.get_community_by_root_node_id(1738541618993)
    assert communities is not None

