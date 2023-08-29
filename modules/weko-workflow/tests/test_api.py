from mock import Mock, patch
import pytest
from flask import current_app, session
from flask_login.utils import login_user
from invenio_accounts.models import Role, User
from sqlalchemy import and_, or_, not_

from weko_workflow.api import Flow, WorkActivity
from weko_workflow.models import Action as _Action
from weko_workflow.models import Activity as _Activity
from weko_workflow.models import ActivityAction
from weko_workflow.models import FlowAction as _FlowAction
from weko_workflow.models import FlowActionRole as _FlowActionRole
from weko_workflow.models import FlowDefine as _Flow
from weko_workflow.models import WorkFlow as _WorkFlow

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
            histories, res_check, pid, community_id, ctx = activity.get_activity_index_search(1)
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
    assert db_activity == None


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_get_corresponding_usage_activities -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_get_corresponding_usage_activities(app, db_register):
    activity = WorkActivity()
    usage_application_list, output_report_list = activity.get_corresponding_usage_activities(1)
    assert usage_application_list == {'activity_data_type': {}, 'activity_ids': []}
    assert output_report_list == {'activity_data_type': {}, 'activity_ids': []}

# def query_activities_by_tab_is_wait(query)
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_query_activities_by_tab_is_wait -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_query_activities_by_tab_is_wait(users, db):
    current_app.config['WEKO_WORKFLOW_ENABLE_SHOW_ACTIVITY'] = False
    with patch("flask_login.utils._get_user", return_value=users[0]['obj']):
        query = db.session.query(
                _Activity,
                User.email,
                _WorkFlow.flows_name,
                _Action.action_name,
                Role.name
            ).outerjoin(_Flow).outerjoin(
                _WorkFlow,
                and_(_Activity.workflow_id == _WorkFlow.id,)
            ).outerjoin(_Action).outerjoin(_FlowAction).outerjoin(_FlowActionRole).outerjoin(
                ActivityAction,
                and_(
                    ActivityAction.activity_id == _Activity.activity_id,
                    ActivityAction.action_id == _Activity.action_id,
                )
            ).outerjoin(
                User,
                and_(
                    _Activity.activity_update_user == User.id,
                    _Activity.shared_user_ids == [],
                )
                )
        expected = "AND (workflow_activity.activity_login_user = ? OR (workflow_activity.shared_user_ids LIKE '%' + ? || '%')) AND (workflow_flow_action_role.action_user != ? AND workflow_flow_action_role.action_user_exclude = ? AND (workflow_activity.shared_user_ids NOT LIKE '%' + ? || '%') OR workflow_flow_action_role.action_role NOT IN (?) AND workflow_flow_action_role.action_role_exclude = ? AND (workflow_activity.shared_user_ids NOT LIKE '%' + ? || '%') OR workflow_activity_action.action_handler != ? AND (workflow_activity.shared_user_ids NOT LIKE '%' + ? || '%') OR (workflow_activity.shared_user_ids LIKE '%' + ? || '%') AND workflow_flow_action_role.action_user != workflow_activity.activity_login_user AND workflow_flow_action_role.action_user_exclude = ? OR (workflow_activity.shared_user_ids LIKE '%' + ? || '%') AND workflow_activity_action.action_handler != workflow_activity.activity_login_user)"
        with pytest.raises(Exception):
            ret = WorkActivity.query_activities_by_tab_is_wait(query)
            assert str(ret).find(expected)
    
    current_app.config['WEKO_WORKFLOW_ENABLE_SHOW_ACTIVITY'] = True
    with patch("flask_login.utils._get_user", return_value=users[0]['obj']):
        query = db.session.query(
                _Activity,
                User.email,
                _WorkFlow.flows_name,
                _Action.action_name,
                Role.name
            ).outerjoin(_Flow).outerjoin(
                _WorkFlow,
                and_(_Activity.workflow_id == _WorkFlow.id,)
            ).outerjoin(_Action).outerjoin(_FlowAction).outerjoin(_FlowActionRole).outerjoin(
                ActivityAction,
                and_(
                    ActivityAction.activity_id == _Activity.activity_id,
                    ActivityAction.action_id == _Activity.action_id,
                )
            ).outerjoin(
                User,
                and_(
                    _Activity.activity_update_user == User.id,
                    _Activity.shared_user_ids == [],
                )
                )
        expected = "AND (workflow_activity.activity_login_user = ?) AND ((workflow_flow_action_role.action_user != ? AND workflow_flow_action_role.action_user_exclude = '0') OR (workflow_flow_action_role.action_role NOT IN (?) AND workflow_flow_action_role.action_role_exclude = '0') OR (workflow_activity_action.action_handler != ? ))"
        ret = WorkActivity.query_activities_by_tab_is_wait(query)
        assert str(ret).find(expected)
    
# def query_activities_by_tab_is_all(query, is_community_admin, community_user_ids)
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_query_activities_by_tab_is_all -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_query_activities_by_tab_is_all(users, db):
    is_community_admin=False
    community_user_ids=[]
    with patch("flask_login.utils._get_user", return_value=users[0]['obj']):
        query = db.session.query(
                _Activity,
                User.email
            ).outerjoin(
                User,
                and_(
                    _Activity.activity_update_user == User.id,
                )
            )
        
        expected = "(workflow_activity.shared_user_ids LIKE '%' || ? || '%') AND workflow_flow_action.action_id != ?"
        
        with pytest.raises(Exception):
            ret = WorkActivity.query_activities_by_tab_is_all(query, is_community_admin, community_user_ids)
            assert str(ret).find(expected)
        
        is_community_admin = True
        community_user_ids = [3]
        expected = "(workflow_activity.activity_update_user LIKE '%' || ? || '%')"
        ret = WorkActivity.query_activities_by_tab_is_all(query, is_community_admin, community_user_ids)
        assert str(ret).find(expected)

# def query_activities_by_tab_is_todo(query, is_admin)
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_query_activities_by_tab_is_todo -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_query_activities_by_tab_is_todo(users, db):
    with patch("flask_login.utils._get_user", return_value=users[0]['obj']):
        query = db.session.query(
                _Activity,
                _FlowActionRole
            )
        expected = "(workflow_activity.shared_user_ids LIKE '%' || ? || '%')"

        with pytest.raises(Exception):
            ret = WorkActivity.query_activities_by_tab_is_todo(query, False)
            assert str(ret).find(expected)

        with pytest.raises(Exception):
            current_app.config['WEKO_WORKFLOW_ENABLE_SHOW_ACTIVITY'] = True
            expected = "(workflow_activity.action_handler LIKE '%' || ? || '%')"
            ret = WorkActivity.query_activities_by_tab_is_todo(query, True)
            assert str(ret).find(expected)

        current_app.config['WEKO_WORKFLOW_ENABLE_SHOW_ACTIVITY'] = False
        expected = "(workflow_activity.shared_user_ids LIKE '%' || ? || '%')"
        ret = WorkActivity.query_activities_by_tab_is_todo(query, True)
        assert str(ret).find(expected)

