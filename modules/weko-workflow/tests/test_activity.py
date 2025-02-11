import pytest
from unittest.mock import MagicMock, PropertyMock, patch

from flask import jsonify
from flask_login.utils import login_user

from weko_workflow.api import WorkActivity
from weko_workflow.errors import WekoWorkflowException
from weko_workflow.headless import HeadlessActivity
from weko_workflow.models import Activity, ActivityAction, ActivityHistory


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp

# class HeadlessActivity(WorkActivity):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
class TestHeadlessActivity:
    # def __init__(self):
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test_init -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_init(self,app,db,workflow):
        activity = HeadlessActivity()
        assert activity is not None
        assert isinstance(activity._actions, dict)
        assert activity._actions.get(1) == "begin_action"
        assert activity._actions.get(2) == "end_action"
        assert activity._actions.get(3) == "item_login"
        assert activity._actions.get(4) == "approval"
        assert activity._actions.get(5) == "item_link"
        assert activity._actions.get(6) == "oa_policy"
        assert activity._actions.get(7) == "identifier_grant"

    # def init_activity(self, user_id, workflow_id=None, ...):
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test_init_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_init_activity(self, app, db, workflow, users, client):
        with patch('weko_workflow.views.WorkActivity.get_new_activity_id') as mock_get_new_activity_id:
            mock_get_new_activity_id.side_effect = [f"A-TEST-0000{i}" for i in range(1, 20)]
            login_user(users[1]["obj"])

            assert Activity.query.count() == 0
            assert ActivityHistory.query.count() == 0
            assert ActivityAction.query.count() == 0

            activity = HeadlessActivity()
            assert activity._model is None

            activity.init_activity(users[0]["id"], workflow["workflow"].id)

            assert Activity.query.count() == 1
            assert activity._model is not None
            assert activity._model.activity_login_user == users[0]["id"]
            assert activity.current_action == "item_login"
            assert activity.activity_id == "A-TEST-00001"
            assert activity.detail == "http://test_server.localdomain/workflow/activity/detail/A-TEST-00001"

            activity = HeadlessActivity()

            activity.init_activity(users[0]["id"], workflow["workflow"].id,community="comm01")

            assert Activity.query.count() == 2
            assert activity._model is not None
            assert activity._model.activity_login_user == users[0]["id"]
            assert activity.current_action == "item_login"
            assert activity.activity_id == "A-TEST-00002"
            assert activity.community == "comm01"
            assert activity.detail == "http://test_server.localdomain/workflow/activity/detail/A-TEST-00002?community=comm01"

        with pytest.raises(WekoWorkflowException) as ex:
            activity.init_activity(users[0]["id"], workflow["workflow"].id)
        assert str(ex.value) == "activity is already initialized."

        activity = HeadlessActivity()
        with pytest.raises(WekoWorkflowException) as ex:
            activity.init_activity(users[0]["id"])
        assert str(ex.value) == "workflow_id is required to create activity."

        with pytest.raises(WekoWorkflowException) as ex:
            activity.init_activity(users[0]["id"], 999)
        assert str(ex.value) == "workflow(id=999) is not found."

        with patch("weko_workflow.headless.activity.init_activity") as mock_init_activity:
            mock_init_activity.return_value = jsonify({ "code": -1,"msg":"error"}), 500
            with pytest.raises(WekoWorkflowException) as ex:
                activity.init_activity(users[0]["id"], workflow["workflow"].id)
            assert str(ex.value) == "error"

    #  item_registration(slef, metadata, files, index, comment):
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test_item_registration -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_item_registration(self, app, db, workflow, users, client, mocker):

        activity = HeadlessActivity()

        with pytest.raises(WekoWorkflowException) as ex:
            activity.item_registration(metadata={}, files=[], index=[], comment="")
        assert str(ex.value) == "activity is not initialized."

        login_user(users[1]["obj"])
        activity.init_activity(users[0]["id"], workflow["workflow"].id)

        with patch("weko_workflow.headless.activity.check_validation_error_msg") as mock_validation_msg:
            msg = ["error<br/>title"]
            error_list = {"mapping": {"title": "error"}}
            mock_validation_msg.return_value = jsonify(code=1, msg=msg, error_list=error_list)
            with pytest.raises(WekoWorkflowException) as ex:
                activity.item_registration(metadata={}, files=[], index=[], comment="")

            assert ex.value.args[0] == {"msg": ["error<br/>title"], "error_list": {"mapping": {"title": "error"}}}

        mock_get_new_activity_id = mocker.patch('weko_workflow.views.WorkActivity.get_new_activity_id')
        mock_get_new_activity_id.side_effect = [f"A-TEST-0000{i}" for i in range(1, 20)]

        patch("weko_workflow.headless.activity.check_validation_error_msg")
        with patch("weko_workflow.headless.activity.HeadlessActivity._input_metadata", return_value=200001):
            with patch("weko_workflow.headless.activity.HeadlessActivity._comment"):
                activity = HeadlessActivity()
                activity.init_activity(users[0]["id"], workflow["workflow"].id)
                url = activity.item_registration({}, [], [])
                assert activity.recid == 200001
                assert url == "http://test_server.localdomain/workflow/activity/detail/A-TEST-00001"

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test_auto -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    # def auto(self, **params):
    def test_auto(self, app, workflow, mocker):
        detail = "http://test_server.localdomain/workflow/activity/detail/A-TEST-00001"
        actions = ["item_login"] * 2 + ["item_link"] * 3 + ["identifier_grant"] * 4 + ["end_action"] * 2

        # Flow of actions: start_action -> item_login -> item_link -> identifier_grant -> end_action
        activity = HeadlessActivity()
        mock_detail = PropertyMock(return_value=detail)
        mock_current_action = PropertyMock(side_effect=actions)
        mocker.patch("weko_workflow.headless.activity.HeadlessActivity.init_activity")

        mock_init_activity = MagicMock()
        mock_item_registration = MagicMock()
        mock_item_link = MagicMock()
        mock_identifier_grant = MagicMock()
        mock_oa_policy = MagicMock()
        mock_end = MagicMock()

        activity.init_activity = mock_init_activity
        activity.item_registration = mock_item_registration
        activity.item_link = mock_item_link
        activity.identifier_grant = mock_identifier_grant
        activity.oa_policy = mock_oa_policy
        activity.end = mock_end

        type(activity).detail = mock_detail
        type(activity).current_action = mock_current_action

        url, current_action, _ = activity.auto(user_id=1, workflow_id=1)
        assert url == detail
        assert current_action == "end_action"

        assert mock_init_activity.call_count == 1
        assert mock_item_registration.call_count == 1
        assert mock_item_link.call_count == 1
        assert mock_identifier_grant.call_count == 1
        assert mock_oa_policy.call_count == 0
        assert mock_end.call_count == 1

        # Flow of actions: start_action -> item_login -> item_link -> oa_policy -> approval -> end_action
        # Stop at approval
        detail = "http://test_server.localdomain/workflow/activity/detail/A-TEST-00002"
        actions = ["item_login"] * 2 + ["item_link"] * 3 + ["oa_policy"] * 5 + ["approval"] * 2

        activity = HeadlessActivity()
        mock_detail = PropertyMock(return_value=detail)
        mock_current_action = PropertyMock(side_effect=actions)
        mocker.patch("weko_workflow.headless.activity.HeadlessActivity.init_activity")

        mock_init_activity = MagicMock()
        mock_item_registration = MagicMock()
        mock_item_link = MagicMock()
        mock_identifier_grant = MagicMock()
        mock_oa_policy = MagicMock()
        mock_end = MagicMock()

        activity.init_activity = mock_init_activity
        activity.item_registration = mock_item_registration
        activity.item_link = mock_item_link
        activity.oa_policy = mock_oa_policy
        activity.end = mock_end

        type(activity).detail = mock_detail
        type(activity).current_action = mock_current_action

        url, current_action, _ = activity.auto(user_id=1, workflow_id=1)
        assert url == detail
        assert current_action == "approval"

        assert mock_init_activity.call_count == 1
        assert mock_item_registration.call_count == 1
        assert mock_item_link.call_count == 1
        assert mock_identifier_grant.call_count == 0
        assert mock_oa_policy.call_count == 1
        assert mock_end.call_count == 1

        # continue from item_link
        detail = "http://test_server.localdomain/workflow/activity/detail/A-TEST-00003"
        actions = ["item_link"] * 3 + ["end_action"] * 2

        activity = HeadlessActivity()
        mock_detail = PropertyMock(return_value=detail)
        mock_current_action = PropertyMock(side_effect=actions)
        mocker.patch("weko_workflow.headless.activity.HeadlessActivity.init_activity")

        mock_init_activity = MagicMock()
        mock_item_registration = MagicMock()
        mock_item_link = MagicMock()
        mock_identifier_grant = MagicMock()
        mock_oa_policy = MagicMock()
        mock_end = MagicMock()

        activity.init_activity = mock_init_activity
        activity.item_link = mock_item_link
        activity.end = mock_end

        type(activity).detail = mock_detail
        type(activity).current_action = mock_current_action

        url, current_action, _ = activity.auto(user_id=1, workflow_id=1)
        assert url == detail
        assert current_action == "end_action"

        assert mock_init_activity.call_count == 1
        assert mock_item_registration.call_count == 0
        assert mock_item_link.call_count == 1
        assert mock_identifier_grant.call_count == 0
        assert mock_oa_policy.call_count == 0
        assert mock_end.call_count == 1

    def test__input_metadata(self):
        pass

    def test__upload_files(self):
        pass

    def test__designate_index(self):
        pass

    def test__comment(self):
        pass

    def test_item_link(self):
        pass

    def test_approval(self):
        pass

    def test_oa_policy(self):
        pass

    def test_identifier_grant(self):
        pass

    # def end(self):
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test_end -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_end(self, app, db, workflow, users, client):
        with patch('weko_workflow.views.WorkActivity.get_new_activity_id') as mock_get_new_activity_id:
            mock_get_new_activity_id.side_effect = [f"A-TEST-0000{i}" for i in range(1, 20)]
            login_user(users[1]["obj"])
            activity = HeadlessActivity()
            act_data = {
                "workflow_id": workflow["workflow"].id,
                "flow_id": workflow["workflow"].flow_id,
                "itemtype_id": workflow["workflow"].itemtype_id,
                "activity_login_user": users[0]["id"],
            }
            activity.user = users[0]["obj"]
            activity._model = WorkActivity().init_activity(act_data)
            assert activity.user is not None
            assert activity.activity_id == "A-TEST-00001"
            assert activity.detail == "http://test_server.localdomain/workflow/activity/detail/A-TEST-00001"
            assert activity.current_action == "item_login"

            activity.end()

            assert activity.user is None
            assert activity._model is None
            assert activity.activity_id == None
            assert activity.detail == ""
            assert activity.current_action == None
