from datetime import datetime
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import SQLAlchemyError

from flask_login.utils import login_user
import json
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


from weko_workflow.api import Flow, WorkActivity, _WorkFlow,WorkFlow

from weko_workflow.models import Activity as _Activity, FlowAction, FlowActionRole

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

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_WorkActivity_count_waiting_approval_by_workflow_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_WorkActivity_count_waiting_approval_by_workflow_id(app, db, db_register):
    activity = WorkActivity()
    assert activity.count_waiting_approval_by_workflow_id(1) == 0


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

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_GetCommunity_get_community_by_root_node_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_GetCommunity_get_community_by_root_node_id(db):
    communities = GetCommunity.get_community_by_root_node_id(1738541618993)
    assert communities is not None

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
def test_workactivity_send_mail_item_registered(app, mocker):
    set_target_id = set()
    recid = MagicMock()
    actor_id = 0
    actor_name = "actor_name"
    targets = list()
    settings = dict()
    profiles = dict()
    actor = MagicMock()
    send_count = 2
    template_file = 'email_notification_item_registered_{language}.tpl'

    # Mock dependent methods
    mock_get_params = mocker.patch.object(
        WorkActivity, '_get_params_for_registrant',
        return_value=(set_target_id, recid, actor_id, actor_name)
    )
    mock_get_settings = mocker.patch.object(
        WorkActivity, '_get_settings_for_targets',
        return_value=(targets, settings, profiles, actor)
    )
    mock_send_email = mocker.patch.object(
        WorkActivity, 'send_notification_email',
        return_value=send_count
    )
    mock_create_context = mocker.patch.object(
        WorkActivity, '_create_notification_context',
        return_value=MagicMock()
    )

    activity_obj = WorkActivity()
    activity = MagicMock(activity_id=123)
    activity_obj.send_mail_item_registered(activity)

    mock_get_params.assert_called_once_with(activity)
    mock_get_settings.assert_called_once_with(set_target_id)
    mock_send_email.assert_called_once()
    args, kwargs = mock_send_email.call_args
    assert args == (activity, targets, settings, profiles, template_file)
    data_callback = kwargs.get('data_callback')
    target = MagicMock()
    profile = MagicMock()
    data_callback(activity, target, profile)
    mock_create_context.assert_called_once_with(activity, target, profile, actor_name, recid)

    mock_get_params.side_effect = SQLAlchemyError
    res = activity_obj.send_mail_item_registered(activity)
    assert res is None


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_send_mail_request_approval -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_send_mail_request_approval(app, users, db, db_register, mocker):
    set_target_id = set()
    recid = MagicMock()
    actor_id = 0
    actor_name = "actor_name"
    targets = list()
    settings = dict()
    profiles = dict()
    actor = MagicMock()
    send_count = 2
    template_file = 'email_notification_request_approval_{language}.tpl'

    # Mock dependent methods
    mock_get_params = mocker.patch.object(
        WorkActivity, '_get_params_for_approver',
        return_value=(set_target_id, recid, actor_id, actor_name)
    )
    mock_get_settings = mocker.patch.object(
        WorkActivity, '_get_settings_for_targets',
        return_value=(targets, settings, profiles, actor)
    )
    mock_send_email = mocker.patch.object(
        WorkActivity, 'send_notification_email',
        return_value=send_count
    )
    mock_create_context = mocker.patch.object(
        WorkActivity, '_create_notification_context',
        return_value=MagicMock()
    )

    activity_obj = WorkActivity()
    activity = MagicMock(activity_id=123)
    activity_obj.send_mail_request_approval(activity)

    mock_get_params.assert_called_once_with(activity)
    mock_get_settings.assert_called_once_with(set_target_id)
    mock_send_email.assert_called_once()
    args, kwargs = mock_send_email.call_args
    assert args == (activity, targets, settings, profiles, template_file)
    data_callback = kwargs.get('data_callback')
    target = MagicMock()
    profile = MagicMock()
    data_callback(activity, target, profile)
    mock_create_context.assert_called_once_with(activity, target, profile, actor_name)

    mock_get_params.side_effect = SQLAlchemyError
    res = activity_obj.send_mail_request_approval(activity)
    assert res is None


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_send_mail_item_approved -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_send_mail_item_approved(app, users, mocker):
    set_target_id = set()
    recid = MagicMock()
    actor_id = 0
    actor_name = "actor_name"
    targets = list()
    settings = dict()
    profiles = dict()
    actor = MagicMock()
    send_count = 2
    template_file = 'email_notification_item_approved_{language}.tpl'

    # Mock dependent methods
    mock_get_params = mocker.patch.object(
        WorkActivity, '_get_params_for_registrant',
        return_value=(set_target_id, recid, actor_id, actor_name)
    )
    mock_get_settings = mocker.patch.object(
        WorkActivity, '_get_settings_for_targets',
        return_value=(targets, settings, profiles, actor)
    )
    mock_send_email = mocker.patch.object(
        WorkActivity, 'send_notification_email',
        return_value=send_count
    )
    mock_create_context = mocker.patch.object(
        WorkActivity, '_create_notification_context',
        return_value=MagicMock()
    )

    activity_obj = WorkActivity()
    activity = MagicMock(activity_id=123)
    activity_obj.send_mail_item_approved(activity)

    mock_get_params.assert_called_once_with(activity)
    mock_get_settings.assert_called_once_with(set_target_id)
    mock_send_email.assert_called_once()
    args, kwargs = mock_send_email.call_args
    assert args == (activity, targets, settings, profiles, template_file, mocker.ANY)
    data_callback = args[5]
    target = MagicMock()
    profile = MagicMock()
    data_callback(activity, target, profile)
    mock_create_context.assert_called_once_with(activity, target, profile, actor_name, recid)

    mock_get_params.side_effect = SQLAlchemyError
    res = activity_obj.send_mail_item_approved(activity)
    assert res is None


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_send_mail_item_rejected -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_send_mail_item_rejected(app, users, mocker):
    set_target_id = set()
    recid = MagicMock()
    actor_id = 0
    actor_name = "actor_name"
    targets = list()
    settings = dict()
    profiles = dict()
    actor = MagicMock()
    send_count = 2
    template_file = "email_notification_item_rejected_{language}.tpl"

    # Mock dependent methods
    mock_get_params = mocker.patch.object(
        WorkActivity, "_get_params_for_registrant",
        return_value=(set_target_id, recid, actor_id, actor_name)
    )
    mock_get_settings = mocker.patch.object(
        WorkActivity, "_get_settings_for_targets",
        return_value=(targets, settings, profiles, actor)
    )
    mock_send_email = mocker.patch.object(
        WorkActivity, "send_notification_email",
        return_value=send_count
    )
    mock_create_context = mocker.patch.object(
        WorkActivity, "_create_notification_context",
        return_value=MagicMock()
    )

    activity_obj = WorkActivity()
    activity = MagicMock(activity_id=123)
    activity_obj.send_mail_item_rejected(activity)

    mock_get_params.assert_called_once_with(activity)
    mock_get_settings.assert_called_once_with(set_target_id)
    mock_send_email.assert_called_once()
    args, kwargs = mock_send_email.call_args
    assert args == (activity, targets, settings, profiles, template_file, mocker.ANY)
    data_callback = args[5]
    target = MagicMock()
    profile = MagicMock()
    data_callback(activity, target, profile)
    mock_create_context.assert_called_once_with(activity, target, profile, actor_name)

    mock_get_params.side_effect = SQLAlchemyError
    res = activity_obj.send_mail_item_rejected(activity)
    assert res is None

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_send_mail_item_deleted -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_send_mail_item_deleted(app, mocker):
    set_target_id = set()
    recid = MagicMock()
    actor_id = 0
    actor_name = "actor_name"
    targets = list()
    settings = dict()
    profiles = dict()
    actor = MagicMock()
    send_count = 2
    template_file = "email_notification_item_deleted_{language}.tpl"

    # Mock dependent methods
    mock_get_params = mocker.patch.object(
        WorkActivity, "_get_params_for_registrant",
        return_value=(set_target_id, recid, actor_id, actor_name)
    )
    mock_get_settings = mocker.patch.object(
        WorkActivity, "_get_settings_for_targets",
        return_value=(targets, settings, profiles, actor)
    )
    mock_send_email = mocker.patch.object(
        WorkActivity, "send_notification_email",
        return_value=send_count
    )
    mock_create_context = mocker.patch.object(
        WorkActivity, "_create_notification_context",
        return_value=MagicMock()
    )

    activity_obj = WorkActivity()
    activity = MagicMock(activity_id=123)
    activity_obj.send_mail_item_deleted(activity)

    mock_get_params.assert_called_once_with(activity)
    mock_get_settings.assert_called_once_with(set_target_id)
    mock_send_email.assert_called_once()
    args, kwargs = mock_send_email.call_args
    assert args == (activity, targets, settings, profiles, template_file, mocker.ANY)
    data_callback = args[5]
    target = MagicMock()
    profile = MagicMock()
    data_callback(activity, target, profile)
    mock_create_context.assert_called_once_with(activity, target, profile, actor_name, recid)

    mock_get_params.side_effect = SQLAlchemyError
    res = activity_obj.send_mail_item_deleted(activity)
    assert res is None


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_send_mail_request_delete_approval -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_send_mail_request_delete_approval(app, mocker):
    set_target_id = set()
    recid = MagicMock()
    actor_id = 0
    actor_name = "actor_name"
    targets = list()
    settings = dict()
    profiles = dict()
    actor = MagicMock()
    send_count = 2
    template_file = "email_notification_delete_request_{language}.tpl"

    # Mock dependent methods
    mock_get_params = mocker.patch.object(
        WorkActivity, "_get_params_for_approver",
        return_value=(set_target_id, recid, actor_id, actor_name)
    )
    mock_get_settings = mocker.patch.object(
        WorkActivity, "_get_settings_for_targets",
        return_value=(targets, settings, profiles, actor)
    )
    mock_send_email = mocker.patch.object(
        WorkActivity, "send_notification_email",
        return_value=send_count
    )
    mock_create_context = mocker.patch.object(
        WorkActivity, "_create_notification_context",
        return_value=MagicMock()
    )

    activity_obj = WorkActivity()
    activity = MagicMock(activity_id=123)
    activity_obj.send_mail_request_delete_approval(activity)

    mock_get_params.assert_called_once_with(activity)
    mock_get_settings.assert_called_once_with(set_target_id)
    mock_send_email.assert_called_once()
    args, kwargs = mock_send_email.call_args
    assert args == (activity, targets, settings, profiles, template_file, mocker.ANY)
    data_callback = args[5]
    target = MagicMock()
    profile = MagicMock()
    data_callback(activity, target, profile)
    mock_create_context.assert_called_once_with(activity, target, profile, actor_name)

    mock_get_params.side_effect = SQLAlchemyError
    res = activity_obj.send_mail_request_delete_approval(activity)
    assert res is None


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_workactivity_send_mail_item_delete_approved -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_workactivity_send_mail_item_delete_approved(app, mocker):
    set_target_id = set()
    recid = MagicMock()
    actor_id = 0
    actor_name = "actor_name"
    targets = list()
    settings = dict()
    profiles = dict()
    actor = MagicMock()
    send_count = 2
    template_file = "email_notification_delete_approved_{language}.tpl"

    # Mock dependent methods
    mock_get_params = mocker.patch.object(
        WorkActivity, "_get_params_for_registrant",
        return_value=(set_target_id, recid, actor_id, actor_name)
    )
    mock_get_settings = mocker.patch.object(
        WorkActivity, "_get_settings_for_targets",
        return_value=(targets, settings, profiles, actor)
    )
    mock_send_email = mocker.patch.object(
        WorkActivity, "send_notification_email",
        return_value=send_count
    )
    mock_create_context = mocker.patch.object(
        WorkActivity, "_create_notification_context",
        return_value=MagicMock()
    )

    activity_obj = WorkActivity()
    activity = MagicMock(activity_id=123)
    activity_obj.send_mail_item_delete_approved(activity)

    mock_get_params.assert_called_once_with(activity)
    mock_get_settings.assert_called_once_with(set_target_id)
    mock_send_email.assert_called_once()
    args, kwargs = mock_send_email.call_args
    assert args == (activity, targets, settings, profiles, template_file, mocker.ANY)
    data_callback = args[5]
    target = MagicMock()
    profile = MagicMock()
    data_callback(activity, target, profile)
    mock_create_context.assert_called_once_with(activity, target, profile, actor_name, recid)

    mock_get_params.side_effect = SQLAlchemyError
    res = activity_obj.send_mail_item_delete_approved(activity)
    assert res is None


def test_workactivity_send_mail_item_delete_rejected(app, mocker):
    set_target_id = set()
    recid = MagicMock()
    actor_id = 0
    actor_name = "actor_name"
    targets = list()
    settings = dict()
    profiles = dict()
    actor = MagicMock()
    send_count = 2
    template_file = "email_notification_item_delete_rejected_{language}.tpl"

    # Mock dependent methods
    mock_get_params = mocker.patch.object(
        WorkActivity, "_get_params_for_registrant",
        return_value=(set_target_id, recid, actor_id, actor_name)
    )
    mock_get_settings = mocker.patch.object(
        WorkActivity, "_get_settings_for_targets",
        return_value=(targets, settings, profiles, actor)
    )
    mock_send_email = mocker.patch.object(
        WorkActivity, "send_notification_email",
        return_value=send_count
    )
    mock_create_context = mocker.patch.object(
        WorkActivity, "_create_notification_context",
        return_value=MagicMock()
    )

    activity_obj = WorkActivity()
    activity = MagicMock(activity_id=123)
    activity_obj.send_mail_item_delete_rejected(activity)

    mock_get_params.assert_called_once_with(activity)
    mock_get_settings.assert_called_once_with(set_target_id)
    mock_send_email.assert_called_once()
    args, kwargs = mock_send_email.call_args
    assert args == (activity, targets, settings, profiles, template_file, mocker.ANY)
    data_callback = args[5]
    target = MagicMock()
    profile = MagicMock()
    data_callback(activity, target, profile)
    mock_create_context.assert_called_once_with(activity, target, profile, actor_name)

    mock_get_params.side_effect = SQLAlchemyError
    res = activity_obj.send_mail_item_delete_rejected(activity)
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


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_create_notification_context_with_recid -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_create_notification_context_with_recid(app, mocker):
    activity = MagicMock(
        updated=datetime.strptime("2025/03/28 12:00:00","%Y/%m/%d %H:%M:%S"),
        title="Test Activity", activity_id="123"
    )
    target = MagicMock(email="test@example.com")
    profile = MagicMock(timezone="Asia/Tokyo", username="test_user")
    actor_name = "actor_name"
    recid = MagicMock(pid_value="1234567890")

    activity_obj = WorkActivity()
    with app.test_request_context(base_url='http://example.org/'):
        context = activity_obj._create_notification_context(activity, target, profile, actor_name, recid)
        assert context.get("recipient_name") == profile.username
        assert context.get("actor_name") == actor_name
        assert context.get("target_title") == activity.title
        assert context.get("target_url") == "http://example.org/records/1234567890"
        assert context.get("event_date") == "2025-03-28 21:00:00"


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test_create_notification_context_without_recid -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test__create_notification_context_without_recid(app, mocker):
    activity = MagicMock(
        updated=datetime.strptime("2025/03/28 12:00:00","%Y/%m/%d %H:%M:%S"),
        title="Test Activity", activity_id="123"
    )
    target = MagicMock(email="test@example.com")
    profile = MagicMock(timezone="Asia/Tokyo", username="test_user")
    actor_name = "actor_name"

    activity_obj = WorkActivity()
    with app.test_request_context(base_url='http://example.org/'):
        context = activity_obj._create_notification_context(activity, target, profile, actor_name)
        assert context.get("recipient_name") == profile.username
        assert context.get("actor_name") == actor_name
        assert context.get("target_title") == activity.title
        assert context.get("target_url") == "http://example.org/workflow/activity/detail/123"
        assert context.get("event_date") == "2025-03-28 21:00:00"


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_api.py::test__get_settings_for_targets -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test__get_settings_for_targets(app, users, db_user_profile, db_notification_user_settings):
    set_target_id = {users[2]["id"]}
    activity_obj = WorkActivity()
    targets, settings, profiles, actor = activity_obj._get_settings_for_targets(set_target_id)
    assert targets == [users[2]["obj"]]
    assert settings.get(users[2]["id"]) == db_notification_user_settings
    assert profiles.get(users[2]["id"]) == db_user_profile
    assert actor == None

    actor_id = users[2]["id"]
    targets, settings, profiles, actor = activity_obj._get_settings_for_targets(set_target_id, actor_id)
    assert targets == [users[2]["obj"]]
    assert settings.get(users[2]["id"]) == db_notification_user_settings
    assert profiles.get(users[2]["id"]) == db_user_profile
    assert actor == users[2]["obj"]


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

