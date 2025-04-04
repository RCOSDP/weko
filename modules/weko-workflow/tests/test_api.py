from datetime import datetime
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import SQLAlchemyError

from flask_login.utils import login_user
import json

from weko_workflow.api import Flow, WorkActivity, _WorkFlow,WorkFlow

from weko_workflow.models import Activity as _Activity, FlowAction, FlowActionRole

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

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_count_waiting_approval_by_workflow_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_count_waiting_approval_by_workflow_id(app, db, db_register):
    activity = WorkActivity()
    assert activity.count_waiting_approval_by_workflow_id(1) == 0

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_filter_by_date -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_filter_by_date(app, db):
    query = db.session.query()
    activity = WorkActivity()
    assert activity.filter_by_date('2022-01-01', '2022-01-02', query)


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_filter_by_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_filter_by_action(app, db):
    query = db.session.query(_Activity)
    activity = WorkActivity()


    # case: empty action
    list_action = []
    assert activity._WorkActivity__filter_by_action(query, list_action) == query


    # case: single action, correct
    list_action = ['start']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(_Activity.action_id.in_([1])))

    list_action = ['end']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(_Activity.action_id.in_([2])))

    list_action = ['itemregistration']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(_Activity.action_id.in_([3])))

    list_action = ['approval']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(_Activity.action_id.in_([4])))

    list_action = ['itemlink']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(_Activity.action_id.in_([5])))

    list_action = ['oapolicyconfirmation']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(_Activity.action_id.in_([6])))

    list_action = ['identifiergrant']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(_Activity.action_id.in_([7])))


    # case: single action, incorrect
    list_action = ['invalid_action']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(_Activity.action_id.in_([])))


    # case: multiple actions, correct
    list_action = ['start', 'itemregistration', 'approval', 'identifiergrant']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(_Activity.action_id.in_([1, 3, 4, 7])))


    # case: multiple actions, incorrect
    list_action = ['invalid1', 'invalid2', 'invalid3']
    assert str(activity._WorkActivity__filter_by_action(query, list_action)) == str(query.filter(_Activity.action_id.in_([])))


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

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_get_deleted_workflow_list -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_deleted_workflow_list(app,db,workflow):
    res = WorkFlow().get_deleted_workflow_list()
    assert res[0].flows_name == "test workflow02"

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_activity_request_mail_list_create_and_update -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_activity_request_mail_list_create_and_update(app, workflow, db, mocker):
    activity = WorkActivity()
    _request_maillist1 = []
    _request_maillist2 = [{"email": "test@example.com", "author_id": ""}]
    activity.create_or_update_activity_request_mail("1", _request_maillist1, True)
    assert activity.get_activity_request_mail("1").request_maillist == []
    activity.create_or_update_activity_request_mail("1", _request_maillist2, True)
    assert activity.get_activity_request_mail("1").request_maillist == _request_maillist2
    activity.create_or_update_activity_request_mail("1111111", _request_maillist1, "aaa")
    assert activity.get_activity_request_mail("1").request_maillist == _request_maillist2


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_notify_about_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_notify_about_activity(app, db, db_register, mocker):
    activity = WorkActivity()
    mock_notify_item_registered = mocker.patch.object(activity, "notify_item_registered")
    mock_notify_request_approval = mocker.patch.object(activity, "notify_request_approval")
    mock_notify_item_approved = mocker.patch.object(activity, "notify_item_approved")
    mock_notify_item_rejected = mocker.patch.object(activity, "notify_item_rejected")
    mock_send_mail_item_registered = mocker.patch.object(activity, "send_mail_item_registered")
    mock_send_mail_request_approval = mocker.patch.object(activity, "send_mail_request_approval")
    mock_send_mail_item_approved = mocker.patch.object(activity, "send_mail_item_approved")
    mock_send_mail_item_rejected = mocker.patch.object(activity, "send_mail_item_rejected")
    
    # with WEKO_NOTIFICATIONS is True
    app.config["WEKO_NOTIFICATIONS"] = True
    activity1 = db_register["activities"][0]
    
    activity.notify_about_activity(activity1.activity_id, 'registered')
    mock_notify_item_registered.assert_called_once_with(activity1)
    mock_send_mail_item_registered.assert_called_once_with(activity1)
    
    activity.notify_about_activity(activity1.activity_id, 'request_approval')
    mock_notify_request_approval.assert_called_once_with(activity1)
    mock_send_mail_request_approval.assert_called_once_with(activity1)
    
    activity.notify_about_activity(activity1.activity_id, 'approved')
    mock_notify_item_approved.assert_called_once_with(activity1)
    mock_send_mail_item_approved.assert_called_once_with(activity1)
    
    activity.notify_about_activity(activity1.activity_id, 'rejected')
    mock_notify_item_rejected.assert_called_once_with(activity1)
    mock_send_mail_item_rejected.assert_called_once_with(activity1)
    
    mock_notify_item_rejected.reset_mock()
    mock_send_mail_item_rejected.reset_mock()
    activity.notify_about_activity(activity1.activity_id, 'invalid_case')
    mock_notify_item_rejected.assert_not_called()
    mock_send_mail_item_rejected.assert_not_called()
    
    # with WEKO_NOTIFICATIONS is False
    mock_notify_item_registered.reset_mock()
    mock_send_mail_item_registered.reset_mock()
    app.config["WEKO_NOTIFICATIONS"] = False
    assert activity.notify_about_activity(activity1.activity_id, 'registered') == None
    mock_notify_item_registered.assert_not_called()
    mock_send_mail_item_registered.assert_not_called()
    
    # with restricted workflow
    activity1.workflow.open_restricted = True
    app.config["WEKO_NOTIFICATIONS"] = True
    mock_notify_item_registered.reset_mock()
    mock_send_mail_item_registered.reset_mock()
    assert activity.notify_about_activity(activity1.activity_id, 'registered') == None
    mock_notify_item_registered.assert_not_called()
    mock_send_mail_item_registered.assert_not_called()
    
    
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_send_mail_item_registered -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_send_mail_item_registered(app, users, mocker):
    mock_activity1 = MagicMock(
        activity_login_user=users[0]["id"],
        shared_user_id=users[1]["id"],
        item_id=123,
        activity_id=456,
        title="Test Item",
        updated=datetime.strptime('2025/03/28 12:00:00','%Y/%m/%d %H:%M:%S'),
        flow_define=MagicMock(flow_id=789),
        activity_community_id=None
    )
    mock_activity2 = MagicMock(
        activity_login_user=users[0]["id"],
        shared_user_id=-1,
        item_id=123,
        activity_id=456,
        title="Test Item",
        updated=datetime.strptime('2025/03/28 12:00:00','%Y/%m/%d %H:%M:%S'),
        flow_define=MagicMock(flow_id=789),
        activity_community_id=None
    )
    mocker.patch("weko_workflow.api.PersistentIdentifier.get_by_object", return_value=MagicMock(pid_value="123.456"))
    mocker.patch("weko_workflow.api.UserProfile.get_by_userid", return_value=MagicMock(username="test_user"))
    mocker.patch("weko_workflow.api.NotificationsUserSettings.query.filter", return_value=MagicMock(all=lambda: []))
    mocker.patch("weko_workflow.api.UserProfile.query.filter", return_value=MagicMock(all=lambda: []))
    mock_send_notification_email = mocker.patch("weko_workflow.api.WorkActivity.send_notification_email")

    activity = WorkActivity()
    activity.send_mail_item_registered(mock_activity1)
    args, kwargs = mock_send_notification_email.call_args
    assert args[0] == mock_activity1  # activity
    assert args[1] == [users[0]["obj"], users[1]["obj"]]  # targets
    assert args[2] == {}  # settings_dict
    assert args[3] == {}  # profiles_dict
    assert args[4] == 'email_nortification_item_registered_{language}.tpl'  # template_file
    assert callable(args[5])  # data_callback
    
    mock_target = MagicMock(email="test@example.com")
    mock_profile = MagicMock(username="test_user", timezone="Asia/Tokyo")
    result = args[5](mock_activity1, mock_target, mock_profile)
    assert result["item_title"] == "Test Item"
    assert result["submitter_name"] == "test_user"
    assert "record_url" in result
    
    activity.send_mail_item_registered(mock_activity2)
    args, kwargs = mock_send_notification_email.call_args
    assert args[1] == []
    
    mocker.patch("weko_workflow.api.PersistentIdentifier.get_by_object", side_effect=SQLAlchemyError)
    res = activity.send_mail_item_registered(mock_activity2)
    assert res is None

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_send_mail_request_approval -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_send_mail_request_approval(app, users, db, db_register, mocker):
    from invenio_communities.models import Community
    from weko_index_tree.models import Index
    with app.test_request_context():
        index = Index(position=1, id=111)
        db.session.add(index)
        db.session.commit()
        comm = Community(id="test_com11", id_role=users[3]["id"],
                            id_user=users[3]["id"], title="test community",
                            description="this is test community",
                            root_node_id=index.id)
        db.session.add(comm)
        db.session.commit()
        flow_define = db_register["flow_define"]

        mock_activity1 = MagicMock(
            activity_login_user=users[0]["id"],
            shared_user_id=users[1]["id"],
            item_id=123,
            activity_id=456,
            title="Test Item",
            updated=datetime.strptime('2025/03/28 12:00:00','%Y/%m/%d %H:%M:%S'),
            flow_define=flow_define,
            activity_community_id=None
        )
        mock_activity2 = MagicMock(
            activity_login_user=users[0]["id"],
            shared_user_id=-1,
            item_id=123,
            activity_id=456,
            title="Test Item",
            updated=datetime.strptime('2025/03/28 12:00:00','%Y/%m/%d %H:%M:%S'),
            flow_define=flow_define,
            activity_community_id=None
        )
        mock_activity3 = MagicMock(
            activity_login_user=users[0]["id"],
            shared_user_id=-1,
            item_id=123,
            activity_id=456,
            title="Test Item",
            updated=datetime.strptime('2025/03/28 12:00:00','%Y/%m/%d %H:%M:%S'),
            flow_define=flow_define,
            activity_community_id="test_com11"
        )
        mocker.patch("weko_workflow.api.PersistentIdentifier.get_by_object", return_value=MagicMock(pid_value="123.456"))
        mock_send_notification_email = mocker.patch("weko_workflow.api.WorkActivity.send_notification_email")
        activity = WorkActivity()
        activity.send_mail_request_approval(mock_activity1)
        mock_send_notification_email.assert_called_once()
        args, kwargs = mock_send_notification_email.call_args
        assert callable(args[5])  # data_callback
        
        mock_target = MagicMock(email="test@example.com")
        mock_profile = MagicMock(username="test_user", timezone="Asia/Tokyo")
        result = args[5](mock_activity1, mock_target, mock_profile)
        assert result["item_title"] == "Test Item"
        assert result["approver_name"] == "test_user"
        assert "approval_url" in result
        
        # self request
        activity.send_mail_request_approval(mock_activity2)
        args, kwargs = mock_send_notification_email.call_args
        assert users[0]["obj"] not in args[1]
        
        # with community admin
        with patch("weko_workflow.api.GetCommunity.get_community_by_id", return_value=MagicMock(id_role=4)):
            activity.send_mail_request_approval(mock_activity3)
            args, kwargs = mock_send_notification_email.call_args
            assert users[3]["obj"] in args[1]
        
        # with action_user
        flow_action = FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=4,
                     action_version='1.0.0',
                     action_order=4,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}
                     )
        db.session.add(flow_action)
        db.session.commit()
        flow_action_role = FlowActionRole(
            action_user = users[7]["id"],
            flow_action_id = flow_action.id,
            action_user_exclude = False)
        db.session.add(flow_action_role)
        db.session.commit()
        activity.send_mail_request_approval(mock_activity2)
        args, kwargs = mock_send_notification_email.call_args
        assert users[7]["obj"] in args[1]
        
        # with action_user_exclude
        flow_action_role.action_role_exclude = True
        flow_action_role.action_role = 1
        flow_action_role.action_user_exclude = True
        flow_action_role.action_user = users[6]["id"]
        db.session.commit()
        activity.send_mail_request_approval(mock_activity2)
        args, kwargs = mock_send_notification_email.call_args
        assert users[6]["obj"] not in args[1]
        
        # invalid action_user type
        flow_action_role.action_user = 1.0
        for action in flow_define.flow_actions:
            action.action_role = flow_action_role
        mocker.patch("weko_workflow.api.Flow.get_flow_detail", return_value=flow_define)
        activity.send_mail_request_approval(mock_activity2)
        args, kwargs = mock_send_notification_email.call_args
        assert args[1] == [users[1]["obj"], users[6]["obj"]]
        
        # exception
        mocker.patch("weko_workflow.api.PersistentIdentifier.get_by_object", side_effect=SQLAlchemyError)
        res = activity.send_mail_request_approval(mock_activity1)
        assert res is None

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_send_mail_item_approved -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_send_mail_item_approved(app, users, mocker):
    mock_activity1 = MagicMock(
        activity_login_user=users[0]["id"],
        shared_user_id=users[1]["id"],
        item_id=123,
        activity_id=456,
        title="Test Item",
        updated=datetime.strptime('2025/03/28 12:00:00','%Y/%m/%d %H:%M:%S'),
        flow_define=MagicMock(flow_id=789),
        activity_community_id=None
    )
    mock_activity2 = MagicMock(
        activity_login_user=users[0]["id"],
        activity_update_user=users[0]["id"],
        shared_user_id=-1,
        item_id=123,
        activity_id=456,
        title="Test Item",
        updated=datetime.strptime('2025/03/28 12:00:00','%Y/%m/%d %H:%M:%S'),
        flow_define=MagicMock(flow_id=789),
        activity_community_id=None
    )
    mocker.patch("weko_workflow.api.PersistentIdentifier.get_by_object", return_value=MagicMock(pid_value="123.456"))
    mocker.patch("weko_workflow.api.UserProfile.get_by_userid", return_value=MagicMock(username="test_user"))
    mocker.patch("weko_workflow.api.NotificationsUserSettings.query.filter", return_value=MagicMock(all=lambda: []))
    mocker.patch("weko_workflow.api.UserProfile.query.filter", return_value=MagicMock(all=lambda: []))
    mock_send_notification_email = mocker.patch("weko_workflow.api.WorkActivity.send_notification_email")

    activity = WorkActivity()
    activity.send_mail_item_approved(mock_activity1)
    args, kwargs = mock_send_notification_email.call_args
    assert args[0] == mock_activity1  # activity
    assert args[1] == [users[0]["obj"], users[1]["obj"]]  # targets
    assert args[2] == {}  # settings_dict
    assert args[3] == {}  # profiles_dict
    assert args[4] == 'email_nortification_item_approved_{language}.tpl'  # template_file
    assert callable(args[5])  # data_callback
    
    mock_target = MagicMock(email="test@example.com")
    mock_profile = MagicMock(username="test_user", timezone="Asia/Tokyo")
    result = args[5](mock_activity1, mock_target, mock_profile)
    assert result["item_title"] == "Test Item"
    assert result["submitter_name"] == "test_user"
    assert "record_url" in result
    
    activity.send_mail_item_approved(mock_activity2)
    args, kwargs = mock_send_notification_email.call_args
    assert args[1] == []  # targets
    
    mocker.patch("weko_workflow.api.PersistentIdentifier.get_by_object", side_effect=SQLAlchemyError)
    res = activity.send_mail_item_approved(mock_activity2)
    assert res is None

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_send_mail_item_rejected -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_send_mail_item_rejected(app, users, mocker):
    mock_activity1 = MagicMock(
        activity_login_user=users[0]["id"],
        shared_user_id=users[1]["id"],
        item_id=123,
        activity_id=456,
        title="Test Item",
        updated=datetime.strptime('2025/03/28 12:00:00','%Y/%m/%d %H:%M:%S'),
        flow_define=MagicMock(flow_id=789),
        activity_community_id=None
    )
    mock_activity2 = MagicMock(
        activity_login_user=users[0]["id"],
        activity_update_user=users[0]["id"],
        shared_user_id=-1,
        item_id=123,
        activity_id=456,
        title="Test Item",
        updated=datetime.strptime('2025/03/28 12:00:00','%Y/%m/%d %H:%M:%S'),
        flow_define=MagicMock(flow_id=789),
        activity_community_id=None
    )
    mocker.patch("weko_workflow.api.PersistentIdentifier.get_by_object", return_value=MagicMock(pid_value="123.456"))
    mocker.patch("weko_workflow.api.UserProfile.get_by_userid", return_value=MagicMock(username="test_user"))
    mocker.patch("weko_workflow.api.NotificationsUserSettings.query.filter", return_value=MagicMock(all=lambda: []))
    mocker.patch("weko_workflow.api.UserProfile.query.filter", return_value=MagicMock(all=lambda: []))
    mock_send_notification_email = mocker.patch("weko_workflow.api.WorkActivity.send_notification_email")

    activity = WorkActivity()
    activity.send_mail_item_rejected(mock_activity1)
    args, kwargs = mock_send_notification_email.call_args
    assert args[0] == mock_activity1  # activity
    assert args[1] == [users[0]["obj"], users[1]["obj"]]  # targets
    assert args[2] == {}  # settings_dict
    assert args[3] == {}  # profiles_dict
    assert args[4] == 'email_nortification_item_rejected_{language}.tpl'  # template_file
    assert callable(args[5])  # data_callback
    
    mock_target = MagicMock(email="test@example.com")
    mock_profile = MagicMock(username="test_user", timezone="Asia/Tokyo")
    result = args[5](mock_activity1, mock_target, mock_profile)
    assert result["item_title"] == "Test Item"
    assert result["submitter_name"] == "test_user"
    assert "url" in result
    
    activity.send_mail_item_rejected(mock_activity2)
    args, kwargs = mock_send_notification_email.call_args
    assert args[1] == []  # targets
    
    mocker.patch("weko_workflow.api.PersistentIdentifier.get_by_object", side_effect=SQLAlchemyError)
    res = activity.send_mail_item_rejected(mock_activity2)
    assert res is None

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_send_notification_email -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_send_notification_email(app, mocker):
    mock_activity = MagicMock(activity_id="123")
    mock_target = MagicMock(id=1, email="test@example.com", confirmed_at=True)
    mock_settings = {1: MagicMock(subscribe_email=True)}
    mock_profiles = {1: MagicMock(language="en")}
    mock_template = "email_template_{language}.tpl"
    mock_data_callback = MagicMock(return_value={"subject": "Test Subject", "body": "Test Body"})

    mock_load_template = mocker.patch("weko_workflow.utils.load_template", return_value="template_content")
    mock_fill_template = mocker.patch("weko_workflow.utils.fill_template", return_value={"subject": "Test Subject", "body": "Test Body"})
    mock_send_mail = mocker.patch("weko_workflow.utils.send_mail")

    activity = WorkActivity()
    activity.send_notification_email(mock_activity, [mock_target], mock_settings, mock_profiles, mock_template, mock_data_callback)

    mock_load_template.assert_called_once_with(mock_template, "en")
    mock_fill_template.assert_called_once_with("template_content", mock_data_callback.return_value)
    mock_send_mail.assert_called_once_with("Test Subject", "test@example.com", "Test Body")
    
    mock_settings_false = {1: MagicMock(subscribe_email=False)}
    mock_send_mail.reset_mock()
    activity.send_notification_email(mock_activity, [mock_target], mock_settings_false, mock_profiles, mock_template, mock_data_callback)
    mock_send_mail.assert_not_called()

    mock_target_false = MagicMock(id=1, email="test@example.com", confirmed_at=False)
    mock_send_mail.reset_mock()
    activity.send_notification_email(mock_activity, [mock_target_false], mock_settings, mock_profiles, mock_template, mock_data_callback)
    mock_send_mail.assert_not_called()
    
    mock_logger = mocker.patch("weko_workflow.api.current_app.logger.error")
    mock_fill_template = mocker.patch("weko_workflow.utils.fill_template", side_effect=Exception("Template error"))
    activity.send_notification_email(mock_activity, [mock_target], mock_settings, mock_profiles, mock_template, mock_data_callback)
    mock_logger.assert_called_once()

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_get_non_extract_files -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_non_extract_files(app, mocker):
    activity = WorkActivity()

    # Mock the `get_activity_metadata` method
    mocker.patch.object(activity, 'get_activity_metadata', return_value=json.dumps({
        "files": [
            {"filename": "file1.txt", "non_extract": True},
            {"filename": "file2.txt", "non_extract": False},
            {"filename": "file3.txt", "non_extract": True}
        ]
    }))

    # metadata is available
    result = activity.get_non_extract_files(activity_id=1)
    assert result == ["file1.txt", "file3.txt"]

    # metadata is None
    mocker.patch.object(activity, 'get_activity_metadata', return_value=None)
    result = activity.get_non_extract_files(activity_id=1)
    assert result is None

    # no files have "non_extract" set to True
    mocker.patch.object(activity, 'get_activity_metadata', return_value=json.dumps({
        "files": [
            {"filename": "file1.txt", "non_extract": False},
            {"filename": "file2.txt", "non_extract": False}
        ]
    }))
    result = activity.get_non_extract_files(activity_id=1)
    assert result == []

