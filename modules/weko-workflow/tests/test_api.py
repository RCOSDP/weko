import uuid
from mock import patch
from datetime import datetime
from flask_login.utils import login_user

from weko_workflow.models import Activity, ActivityAction
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


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_get_activity_list_todo -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_get_activity_list_todo(app, db, workflow, users):
    wa = WorkActivity()
    activity1 = Activity(
        status='N',
        activity_id='A-00000001-00001',
        workflow_id=workflow['workflow'].id,
        flow_id=workflow['flow'].id,
        action_id=5,
        action_status = 'M',
        activity_login_user=users[2]['id'],
        activity_update_user=users[2]['id'],
        activity_status='M',
        activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
        activity_confirm_term_of_use=True,
        title='test_system',
        shared_user_id=-1,
        extra_info={},
        action_order=4
    )
    activity2 = Activity(
        status='N',
        activity_id='A-00000001-00002',
        workflow_id=workflow['workflow'].id,
        flow_id=workflow['flow'].id,
        action_id=5,
        action_status = 'M',
        activity_login_user=users[1]['id'],
        activity_update_user=users[1]['id'],
        activity_status='M',
        activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
        activity_confirm_term_of_use=True,
        title='test_repo',
        shared_user_id=-1,
        extra_info={},
        action_order=4
    )
    activity3 = Activity(
        status='N',
        activity_id='A-00000001-00003',
        workflow_id=workflow['workflow'].id,
        flow_id=workflow['flow'].id,
        action_id=5,
        action_status = 'M',
        activity_login_user=users[3]['id'],
        activity_update_user=users[3]['id'],
        activity_status='M',
        activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
        activity_confirm_term_of_use=True,
        title='test_comm',
        shared_user_id=-1,
        extra_info={},
        action_order=4
    )
    activity4 = Activity(
        status='N',
        activity_id='A-00000001-00004',
        workflow_id=workflow['workflow'].id,
        flow_id=workflow['flow'].id,
        action_id=5,
        action_status = 'M',
        activity_login_user=users[0]['id'],
        activity_update_user=users[0]['id'],
        activity_status='M',
        activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
        activity_confirm_term_of_use=True,
        title='test_contributor',
        shared_user_id=-1,
        extra_info={},
        action_order=4
    )
    activity5 = Activity(
        status='N',
        activity_id='A-00000001-00005',
        workflow_id=workflow['workflow'].id,
        flow_id=workflow['flow'].id,
        item_id=uuid.uuid4(),
        action_id=4,        
        action_status = 'M',
        activity_login_user=users[3]['id'],
        activity_update_user=users[3]['id'],
        activity_status='M',
        activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
        activity_confirm_term_of_use=True,
        title='test_comm_approval',
        shared_user_id=-1,
        extra_info={},
        action_order=6
    )
    activity6 = Activity(
        status='N',
        activity_id='A-00000001-00006',
        workflow_id=workflow['workflow'].id,
        flow_id=workflow['flow'].id,
        item_id=uuid.uuid4(),
        action_id=4,        
        action_status = 'M',
        activity_login_user=users[0]['id'],
        activity_update_user=users[0]['id'],
        activity_status='M',
        activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
        activity_confirm_term_of_use=True,
        title='test_contributor_approval',
        shared_user_id=-1,
        extra_info={},
        action_order=6
    )
    activity7 = Activity(
        status='N',
        activity_id='A-00000001-00007',
        workflow_id=workflow['workflow'].id,
        flow_id=workflow['flow'].id,
        action_id=5,
        action_status = 'C',
        activity_login_user=users[1]['id'],
        activity_update_user=users[1]['id'],
        activity_status='C',
        activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
        activity_confirm_term_of_use=True,
        title='test_repo_cancel',
        shared_user_id=-1,
        extra_info={},
        action_order=4
    )
    # 代理登録 repo → system
    activity8 = Activity(
        status='N',
        activity_id='A-00000001-00008',
        workflow_id=workflow['workflow'].id,
        flow_id=workflow['flow'].id,
        action_id=5,
        action_status = 'M',
        activity_login_user=users[1]['id'],
        activity_update_user=users[1]['id'],
        activity_status='M',
        activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
        activity_confirm_term_of_use=True,
        title='test_share_repo_to_system',
        shared_user_id=users[2]['id'],
        extra_info={},
        action_order=4
    )
    # 代理登録 comm → repo
    activity9 = Activity(
        status='N',
        activity_id='A-00000001-00009',
        workflow_id=workflow['workflow'].id,
        flow_id=workflow['flow'].id,
        action_id=5,
        action_status = 'M',
        activity_login_user=users[3]['id'],
        activity_update_user=users[3]['id'],
        activity_status='M',
        activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
        activity_confirm_term_of_use=True,
        title='test_share_comm_to_repo',
        shared_user_id=users[1]['id'],
        extra_info={},
        action_order=4
    )
    # 代理登録 contributor → comm
    activity10 = Activity(
        status='N',
        activity_id='A-00000001-00010',
        workflow_id=workflow['workflow'].id,
        flow_id=workflow['flow'].id,
        action_id=5,
        action_status = 'M',
        activity_login_user=users[0]['id'],
        activity_update_user=users[0]['id'],
        activity_status='M',
        activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
        activity_confirm_term_of_use=True,
        title='test_share_con_to_comm',
        shared_user_id=users[3]['id'],
        extra_info={},
        action_order=4
    )

    with db.session.begin_nested():
        db.session.add(activity1)
        db.session.add(activity2)
        db.session.add(activity3)
        db.session.add(activity4)
        db.session.add(activity5)
        db.session.add(activity6)
        db.session.add(activity7)
        db.session.add(activity8)
        db.session.add(activity9)
        db.session.add(activity10)
    db.session.commit()

    activity_action1 = ActivityAction(
        activity_id=activity1.activity_id,
        action_id=5,
        action_status="M",
        action_handler=users[2]['id'],
        action_order=4
    )
    activity_action2 = ActivityAction(
        activity_id=activity2.activity_id,
        action_id=5,
        action_status="M",
        action_handler=users[1]['id'],
        action_order=4
    )
    activity_action3 = ActivityAction(
        activity_id=activity3.activity_id,
        action_id=5,
        action_status="M",
        action_handler=users[3]['id'],
        action_order=4
    )
    activity_action4 = ActivityAction(
        activity_id=activity4.activity_id,
        action_id=5,
        action_status="M",
        action_handler=users[0]['id'],
        action_order=4
    )
    activity_action5 = ActivityAction(
        activity_id=activity5.activity_id,
        action_id=4,
        action_status="M",
        action_handler=-1,
        action_order=6
    )
    activity_action6 = ActivityAction(
        activity_id=activity6.activity_id,
        action_id=4,
        action_status="M",
        action_handler=-1,
        action_order=6
    )
    activity_action7 = ActivityAction(
        activity_id=activity7.activity_id,
        action_id=5,
        action_status="C",
        action_handler=-1,
        action_order=4
    )
    activity_action8 = ActivityAction(
        activity_id=activity8.activity_id,
        action_id=5,
        action_status="M",
        action_handler=users[1]['id'],
        action_order=4
    )
    activity_action9 = ActivityAction(
        activity_id=activity9.activity_id,
        action_id=5,
        action_status="M",
        action_handler=users[3]['id'],
        action_order=4
    )
    activity_action10 = ActivityAction(
        activity_id=activity10.activity_id,
        action_id=5,
        action_status="M",
        action_handler=users[0]['id'],
        action_order=4
    )

    with db.session.begin_nested():
        db.session.add(activity_action1)
        db.session.add(activity_action2)
        db.session.add(activity_action3)
        db.session.add(activity_action4)
        db.session.add(activity_action5)
        db.session.add(activity_action6)
        db.session.add(activity_action7)
        db.session.add(activity_action8)
        db.session.add(activity_action9)
        db.session.add(activity_action10)
    db.session.commit()

    with app.test_request_context():
        #system admin
        login_user(users[2]["obj"])
        activities, max_page, size, page, name_param = wa.get_activity_list(
            None, {}, False, False)
        assert len(activities) == 4

        # repo admin
        login_user(users[1]["obj"])
        activities, max_page, size, page, name_param = wa.get_activity_list(
            None, {}, False, False)
        assert len(activities) == 5

        # comm admin
        login_user(users[3]["obj"])
        with patch('weko_workflow.api.WekoDeposit.get_record', return_value={'path': [1]}):
            activities, max_page, size, page, name_param = wa.get_activity_list(
                None, {}, False, False)
            assert len(activities) == 5

        # contributor admin
        login_user(users[0]["obj"])
        activities, max_page, size, page, name_param = wa.get_activity_list(
            None, {}, False, False)
        assert len(activities) == 2