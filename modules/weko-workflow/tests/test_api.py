import pytest

from flask_login.utils import login_user

from weko_workflow.api import Flow, WorkActivity

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


conditions = [
    {
        'tab': ['todo'],
        'pagestodo': ['1'],
        'sizetodo': ['10']
    },
    {
        'tab': ['wait'],
        'pageswait': ['1'],
        'sizewait': ['10']
    },
    {
        'tab': ['all'],
        'pagesall': ['1'],
        'sizeall': ['10']
    },
    {
        'tab': ['todo']
    },
    {
        'tab': ['wait']
    },
    {
        'tab': ['all']
    }
]

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_get_activity_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('conditions', conditions)
def test_WorkActivity_get_activity_list(app, users, db_register_activity, conditions):
    # test preparation
    activity = WorkActivity()

    # contributor
    with app.test_request_context():
        login_user(users[0]['obj'])
        activities, max_page, size, page, name_param, count = \
            activity.get_activity_list(None, conditions, False)
        
        if conditions.get('tab')[0] == 'todo':
            assert size == conditions.get('sizetodo')[0] if conditions.get('sizetodo') else '20'
            assert page == conditions.get('pagestodo')[0] if conditions.get('pagestodo') else '1'
            assert max_page == 1
            assert count == 1
            assert name_param == ''
            assert activities[0].activity_id == db_register_activity.get('activity')[0].activity_id
            assert activities[0].title == db_register_activity.get('activity')[0].title
        elif conditions.get('tab')[0] == 'wait':
            assert size == conditions.get('sizewait')[0] if conditions.get('sizewait') else '20'
            assert page == conditions.get('pageswait')[0] if conditions.get('pageswait') else '1'
            assert max_page == 1
            assert count == 1
            assert name_param == ''
            assert activities[0].activity_id == db_register_activity.get('activity')[2].activity_id
            assert activities[0].title == db_register_activity.get('activity')[2].title
        elif conditions.get('tab')[0] == 'all':
            assert size == conditions.get('sizeall')[0] if conditions.get('sizeall') else '20'
            assert page == conditions.get('pagesall')[0] if conditions.get('pagesall') else '1'
            assert max_page == 1
            assert count == 1
            assert name_param == ''
            assert activities[0].activity_id == db_register_activity.get('activity')[0].activity_id
            assert activities[0].title == db_register_activity.get('activity')[0].title
        else:
            assert False
    
    # sysadmin
    with app.test_request_context():
        login_user(users[2]['obj'])
        activities, max_page, size, page, name_param, count = \
            activity.get_activity_list(None, conditions, False)
            
        if conditions.get('tab')[0] == 'todo':
            assert size == conditions.get('sizetodo')[0] if conditions.get('sizetodo') else '20'
            assert page == conditions.get('pagestodo')[0] if conditions.get('pagestodo') else '1'
            assert max_page == 1
            assert count == 3
            assert name_param == ''
            for i in range(0, 3):
                assert activities[i].activity_id == db_register_activity.get('activity')[2-i].activity_id
            for i in range(0, 3):
                assert activities[i].title == db_register_activity.get('activity')[2-i].title
        elif conditions.get('tab')[0] == 'wait':
            assert size == conditions.get('sizetodo')[0] if conditions.get('sizetodo') else '20'
            assert page == conditions.get('pagestodo')[0] if conditions.get('pagestodo') else '1'
            assert max_page == 1
            assert count == 1
            assert activities[0].activity_id == db_register_activity.get('activity')[2].activity_id
            assert activities[0].title == db_register_activity.get('activity')[2].title
        elif conditions.get('tab')[0] == 'all':
            assert size == conditions.get('sizeall')[0] if conditions.get('sizeall') else '20'
            assert page == conditions.get('pagesall')[0] if conditions.get('pagesall') else '1'
            assert max_page == 1
            assert count == 3
            assert name_param == ''
            for i in range(0, 3):
                assert activities[i].activity_id == db_register_activity.get('activity')[2-i].activity_id
            for i in range(0, 3):
                assert activities[i].title == db_register_activity.get('activity')[2-i].title
        else:
            assert False


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
