import pytest
import uuid
from flask import jsonify
from flask_login.utils import login_user
from unittest.mock import Mock, MagicMock, PropertyMock, patch, mock_open
from sqlalchemy.exc import SQLAlchemyError
import json

from invenio_files_rest.errors import FileSizeError
from invenio_files_rest.models import Bucket

from weko_workflow.api import WorkActivity, ActivityStatusPolicy
from weko_workflow.errors import WekoWorkflowException
from weko_workflow.headless import HeadlessActivity
from weko_workflow.models import Activity, ActivityAction, ActivityHistory


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp

# class HeadlessActivity(WorkActivity):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
class TestHeadlessActivity:
    # def __init__(self):
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test_init -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_init(self, app, db, workflow):
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
        with patch("weko_workflow.views.WorkActivity.get_new_activity_id") as mock_get_new_activity_id:
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

            activity.init_activity(users[0]["id"], workflow["workflow"].id, community="comm01")

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
            mock_init_activity.return_value = jsonify({"code": -1, "msg": "error"}), 500
            with pytest.raises(WekoWorkflowException) as ex:
                activity.init_activity(users[0]["id"], workflow["workflow"].id)
            assert str(ex.value) == "error"

        with patch("weko_workflow.headless.activity.verify_deletion") as mock_verify_deletion:
            mock_verify_deletion.return_value = jsonify({"is_delete": True})
            with pytest.raises(WekoWorkflowException) as ex:
                activity.init_activity(users[1]["id"], workflow["workflow"].id, activity_id="A-TEST-00001")
            assert str(ex.value) == "activity(A-TEST-00001) is already deleted."

        with patch("weko_workflow.headless.activity.verify_deletion") as mock_verify_deletion:
            mock_verify_deletion.return_value = jsonify({"is_delete": False})
            with patch("weko_workflow.api.WorkActivity.get_activity_by_id") as mock_get_activity_by_id:
                mock_get_activity_by_id.return_value = None
                with pytest.raises(WekoWorkflowException) as ex:
                    activity.init_activity(users[1]["id"], workflow["workflow"].id, activity_id="A-TEST-00001",)
                assert str(ex.value) == "activity(A-TEST-00001) is not found."

            with patch("weko_workflow.api.WorkActivity.get_activity_by_id") as mock_get_activity_by_id:
                mock_get_activity_by_id.return_value = MagicMock(activity_login_user=users[1]["id"], shared_user_id=users[1]["id"])
                with patch("weko_workflow.utils.check_authority_by_admin", return_value=False):
                    with pytest.raises(WekoWorkflowException) as ex:
                        activity.init_activity(users[0]["id"], workflow["workflow"].id, activity_id="A-TEST-00001")
                    assert str(ex.value) == f"user({users[0]['id']}) cannot restart activity(A-TEST-00001)."

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

        mock_get_new_activity_id = mocker.patch("weko_workflow.views.WorkActivity.get_new_activity_id")
        mock_get_new_activity_id.side_effect = [f"A-TEST-0000{i}" for i in range(1, 20)]

        patch("weko_workflow.headless.activity.check_validation_error_msg")
        with patch("weko_workflow.headless.activity.HeadlessActivity._input_metadata", return_value=200001):
            with patch("weko_workflow.headless.activity.HeadlessActivity._comment"):
                activity = HeadlessActivity()
                # FIXME: Don't use HeadlessActivity.init_activity, but use WorkActivity.init_activity.
                activity.init_activity(users[0]["id"], workflow["workflow"].id)
                url = activity.item_registration({}, [], [])
                assert activity.recid == 200001
                assert url == "http://test_server.localdomain/workflow/activity/detail/A-TEST-00001"

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test_auto -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    # def auto(self, **params):
    def test_auto(self, app, workflow, mocker):
        original_detail = HeadlessActivity.detail
        original_current_action = HeadlessActivity.current_action

        detail = "http://test_server.localdomain/workflow/activity/detail/A-TEST-00001"
        actions = (["item_login"] * 2 + ["item_link"] * 3 + ["identifier_grant"] * 4 + ["end_action"] * 2)

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

        type(activity).detail = original_detail
        type(activity).current_action = original_current_action

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test__input_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test__input_metadata(self, app, db, workflow, users, client, mocker):
        mock_upload = mocker.patch.object(
                HeadlessActivity,
                "_upload_files",
                return_value=[
                    {"filename": "test.txt", "file_id": "12345"},
                    {"filename": "ignore.txt", "file_id": "67890"}
                ]
            )
        mock_upt_meta = mocker.patch("weko_workflow.api.WorkActivity.upt_activity_metadata", return_value=None)
        mocker.patch("weko_workflow.headless.activity.get_workflow_journal", return_value=None)
        mocker.patch("weko_workflow.headless.activity.get_feedback_maillist", return_value=(MagicMock(json={"code": 1, "data": []}), None))
        mocker.patch("weko_workflow.headless.activity.get_mapping", return_value={"title.@value": "title"})
        mocker.patch("weko_search_ui.utils.get_data_by_property", return_value=(["Test Title"], None))
        mocker.patch("weko_workflow.headless.activity.current_pidstore.minters", {"weko_deposit_minter": lambda record_uuid, data: MagicMock(pid_value="200001")})
        mocker.patch("weko_workflow.headless.activity.WekoDeposit.create",return_value=MagicMock())
        mocker.patch("weko_workflow.headless.activity.WekoDeposit.update")
        mocker.patch("weko_workflow.headless.activity.WekoDeposit.commit")
        mocker.patch("weko_workflow.headless.activity.delete_user_lock_activity_cache")
        mocker.patch("weko_workflow.headless.activity.delete_lock_activity_cache")
        with patch("weko_workflow.views.WorkActivity.get_new_activity_id") as mock_get_new_activity_id:
            # case 1
            mocker.patch("weko_workflow.headless.activity.validate_form_input_data",
                side_effect=lambda result, itemtype_id, metadata: result.update({"is_valid": True}))
            mock_get_new_activity_id.side_effect = [f"A-TEST-0000{i}" for i in range(1, 20)]
            login_user(users[1]["obj"])
            activity = HeadlessActivity()
            files = ["test.txt", "ignore.txt"]
            non_extract = ["ignore.txt"]
            activity.init_activity(users[1]["id"], workflow["workflow"].id, community="comm01")

            metadata = {"title": "Test Title", "pubdate": "2024-01-01", "shared_user_id": users[1]["id"]}
            files = []
            recid = activity._input_metadata(metadata, files,non_extract)
            assert recid == "200001"
            # non_extractフラグの検証
            args, _ = mock_upt_meta.call_args
            updated_data = json.loads(args[1])
            assert updated_data["files"][0].get("non_extract", False) is False  # test.txt
            assert updated_data["files"][1]["non_extract"] is True  # ignore.txt

            # non_extractがNoneの場合
            mock_upload.return_value = [
                {"filename": "test.txt", "file_id": "12345"},
                {"filename": "ignore.txt", "file_id": "67890"}
            ]
            recid = activity._input_metadata(metadata, files, non_extract=None)
            args, _ = mock_upt_meta.call_args
            updated_data = json.loads(args[1])
            assert updated_data["files"][0].get("non_extract", False) is False  # test.txt
            assert updated_data["files"][1].get("non_extract", False) is False  # ignore.txt

            # files is None
            mocker.patch("weko_workflow.headless.activity.validate_form_input_data",
                side_effect=lambda result, itemtype_id, metadata: result.update({"is_valid": True}))
            files = None
            recid = activity._input_metadata(metadata, files)
            assert recid == "200001"

            # input_metadata_invalid
            mocker.patch("weko_workflow.headless.activity.validate_form_input_data",
                side_effect=lambda result, itemtype_id, metadata: result.update({"is_valid": False, "error": "Invalid metadata"}))
            with pytest.raises(WekoWorkflowException) as ex:
                activity._input_metadata(metadata, files)
            assert str(ex.value) == "failed to input metadata: Invalid metadata"

            # TODO: metadata_existing_record
            # activity.recid = "200001"
            # mocker.patch("weko_workflow.headless.activity.validate_form_input_data", side_effect=lambda result, itemtype_id, metadata: result.update({"is_valid": True}))
            # recid = activity._input_metadata(metadata, files)
            # assert recid == "200001"

            # upt_activity_metadata raises Exception
            mocker.patch("weko_workflow.headless.activity.validate_form_input_data",
                side_effect=lambda result, itemtype_id, metadata: result.update({"is_valid": True}))
            mocker.patch("weko_workflow.api.WorkActivity.upt_activity_metadata",
                side_effect=Exception("upt_activity_metadata error"))
            with pytest.raises(WekoWorkflowException) as ex:
                activity._input_metadata(metadata, files)
            assert (str(ex.value) == "failed to input metadata: upt_activity_metadata error")

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test__upload_files -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test__upload_files(self, app, db, workflow, users, client, mocker):
        activity = HeadlessActivity()
        activity._deposit = {"_buckets": {"deposit": uuid.uuid4()}}
        mocker.patch.object(Bucket, "query", new=Mock())
        mock_bucket = Mock(spec=Bucket)
        mock_bucket.size_limit = 1000
        mock_bucket.location.max_file_size = 500
        mocker.patch.object(Bucket.query, "get", return_value=mock_bucket)
        mock_object_version = MagicMock()
        mock_object_version.basename = "test.txt"
        mocker.patch("weko_workflow.headless.activity.ObjectVersion.create", return_value=mock_object_version,)
        mocker.patch("weko_workflow.headless.activity.ObjectVersion.set_contents")

        # Test case: file size exceeds limit
        with pytest.raises(FileSizeError) as ex:
            activity._upload_files([MagicMock(filename="test.txt", stream=mock_open(read_data="data"), content_length=501)])
        assert "File size limit exceeded." in str(ex.value)

        # Test case: file not found
        with pytest.raises(WekoWorkflowException) as ex:
            activity._upload_files(["non_existent_file.txt"])
        assert str(ex.value) == "file(non_existent_file.txt) is not found."

        # Test case: successful upload with file path
        mocker.patch("os.path.isfile", return_value=True)
        mocker.patch("os.path.getsize", return_value=10)
        with patch("builtins.open", mock_open(read_data="data")):
            files_info = activity._upload_files(["test.txt"])
            assert len(files_info) == 1
            assert files_info[0]["filename"] == "test.txt"

        # Test case: successful upload with FileStorage object
        file_storage = MagicMock(
            filename="test.txt", stream=mock_open(read_data="data"), content_length=10)
        files_info = activity._upload_files([file_storage])
        assert len(files_info) == 1
        assert files_info[0]["filename"] == "test.txt"


    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test__designate_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test__designate_index(self, app, db, workflow, users, client, mocker):
        activity = HeadlessActivity()

        login_user(users[1]["obj"])
        activity.init_activity(users[1]["id"], workflow["workflow"].id)

        # Mocking the necessary methods
        mock_user_lock = mocker.patch.object(activity, "_user_lock")
        mock_activity_lock = mocker.patch.object(
            activity, "_activity_lock", return_value="locked_value")
        mock_user_unlock = mocker.patch.object(activity, "_user_unlock")
        mock_activity_unlock = mocker.patch.object(activity, "_activity_unlock")
        mock_update_index_tree_for_record = mocker.patch(
            "weko_workflow.headless.activity.update_index_tree_for_record")

        # Test case: index is not a list
        activity._designate_index(1)
        mock_update_index_tree_for_record.assert_called_once_with(activity.recid, 1)

        # Test case: index is a list
        activity._designate_index([1, 2])
        assert mock_update_index_tree_for_record.call_count == 3
        mock_update_index_tree_for_record.assert_any_call(activity.recid, 1)
        mock_update_index_tree_for_record.assert_any_call(activity.recid, 2)

        # Verify locks and unlocks
        assert mock_user_lock.call_count == 2
        assert mock_activity_lock.call_count == 2
        assert mock_user_unlock.call_count == 2
        assert mock_activity_unlock.call_count == 2
        mock_activity_unlock.assert_any_call("locked_value")

        # update_index_tree_for_record raises Exception
        mock_update_index_tree_for_record = mocker.patch(
            "weko_workflow.headless.activity.update_index_tree_for_record",
            side_effect=Exception("update_index_tree_for_record error"))
        with pytest.raises(WekoWorkflowException) as ex:
            activity._designate_index(1)
        assert str(ex.value) == "failed to designate index."
        mock_update_index_tree_for_record.assert_called_once_with(activity.recid, 1)

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test__comment -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test__comment(self, app, db, workflow, users, client, mocker):
        activity = HeadlessActivity()

        login_user(users[1]["obj"])
        activity.init_activity(users[1]["id"], workflow["workflow"].id)

        # Mocking the necessary methods
        mock_user_lock = mocker.patch.object(activity, "_user_lock")
        mock_activity_lock = mocker.patch.object(
            activity, "_activity_lock", return_value="locked_value")
        mock_user_unlock = mocker.patch.object(activity, "_user_unlock")
        mock_activity_unlock = mocker.patch.object(activity, "_activity_unlock")
        mock_next_action = mocker.patch(
            "weko_workflow.headless.activity.next_action",
            return_value=(MagicMock(json={"code": 0, "msg": ""}), None))
        # Test case: successful comment
        activity._comment("This is a test comment")
        mock_next_action.assert_called_once_with(
            activity.activity_id,
            activity.current_action_id,
            {"commond": "This is a test comment"})
        mock_user_lock.assert_called_once()
        mock_activity_lock.assert_called_once()
        mock_user_unlock.assert_called_once()
        mock_activity_unlock.assert_called_once_with("locked_value")

        # Test case: failed to set comment
        mock_next_action.return_value = (MagicMock(json={"code": 1, "msg": "error"}),None)
        with pytest.raises(WekoWorkflowException) as ex:
            activity._comment("This is a test comment")
        assert str(ex.value) == "error"
        mock_user_lock.assert_called()
        mock_activity_lock.assert_called()
        mock_user_unlock.assert_called()
        mock_activity_unlock.assert_called_with("locked_value")

        # Test case: SQLAlchemyError occurs in next_action
        mock_next_action.side_effect = SQLAlchemyError("SQLAlchemyError occurred")
        with pytest.raises(WekoWorkflowException) as ex:
            activity._comment("This is a test comment")
        assert str(ex.value) == "failed to set comment."
        mock_user_lock.assert_called()
        mock_activity_lock.assert_called()
        mock_user_unlock.assert_called()
        mock_activity_unlock.assert_called_with("locked_value")

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test_item_link -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_item_link(self, app, db, workflow, users, client, mocker):
        activity = HeadlessActivity()

        login_user(users[1]["obj"])
        activity.init_activity(users[1]["id"], workflow["workflow"].id)

        # Mocking the necessary methods
        mock_user_lock = mocker.patch.object(activity, "_user_lock")
        mock_activity_lock = mocker.patch.object(activity, "_activity_lock", return_value="locked_value")
        mock_user_unlock = mocker.patch.object(activity, "_user_unlock")
        mock_activity_unlock = mocker.patch.object(activity, "_activity_unlock")
        mock_next_action = mocker.patch("weko_workflow.headless.activity.next_action",return_value=(MagicMock(json={"code": 0, "msg": ""}), None))

        # Test case: successful item link
        link_data = [{"link": "test_link"}]
        activity.item_link(link_data)
        mock_next_action.assert_called_once_with(
            activity.activity_id, activity.current_action_id, {"link_data": link_data})
        mock_user_lock.assert_called_once()
        mock_activity_lock.assert_called_once()
        mock_user_unlock.assert_called_once()
        mock_activity_unlock.assert_called_once_with("locked_value")

        # Test case: failed item link
        mock_next_action.return_value = (MagicMock(json={"code": 1, "msg": "error"}),None)
        with pytest.raises(WekoWorkflowException) as ex:
            activity.item_link(link_data)
        assert str(ex.value) == "error"
        mock_user_lock.assert_called()
        mock_activity_lock.assert_called()
        mock_user_unlock.assert_called()
        mock_activity_unlock.assert_called_with("locked_value")

        # Test case: SQLAlchemyError occurs in next_action
        mock_next_action.side_effect = SQLAlchemyError("SQLAlchemyError occurred")
        with pytest.raises(WekoWorkflowException) as ex:
            activity.item_link(link_data)
        assert str(ex.value) == "failed in Item Link."
        mock_user_lock.assert_called()
        mock_activity_lock.assert_called()
        mock_user_unlock.assert_called()
        mock_activity_unlock.assert_called_with("locked_value")

    def test_approval(self):
        pass

    def test_oa_policy(self):
        pass

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test_identifier_grant -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_identifier_grant(self, app, db, workflow, users, client, mocker):
        activity = HeadlessActivity()

        login_user(users[1]["obj"])
        activity.init_activity(users[1]["id"], workflow["workflow"].id)

        # Mocking the necessary methods
        mock_user_lock = mocker.patch.object(activity, "_user_lock")
        mock_activity_lock = mocker.patch.object(
            activity, "_activity_lock", return_value="locked_value"
        )
        mock_user_unlock = mocker.patch.object(activity, "_user_unlock")
        mock_activity_unlock = mocker.patch.object(activity, "_activity_unlock")
        mock_next_action = mocker.patch(
            "weko_workflow.headless.activity.next_action",
            return_value=(MagicMock(json={"code": 0, "msg": ""}), None),
        )

        # Test case: successful identifier grant
        grant_data = {"identifier_grant": "1"}
        activity.identifier_grant(grant_data)
        mock_next_action.assert_called_once_with(
            activity.activity_id, activity.current_action_id, grant_data
        )
        mock_user_lock.assert_called_once()
        mock_activity_lock.assert_called_once()
        mock_user_unlock.assert_called_once()
        mock_activity_unlock.assert_called_once_with("locked_value")

        # Test case: failed identifier grant
        mock_next_action.return_value = (
            MagicMock(json={"code": 1, "msg": "error"}),
            None,
        )
        with pytest.raises(WekoWorkflowException) as ex:
            activity.identifier_grant(grant_data)
        assert str(ex.value) == "error"
        mock_user_lock.assert_called()
        mock_activity_lock.assert_called()
        mock_user_unlock.assert_called()
        mock_activity_unlock.assert_called_with("locked_value")

        # Test case: SQLAlchemyError occurs in next_action
        mock_next_action.side_effect = SQLAlchemyError("SQLAlchemyError occurred")
        with pytest.raises(WekoWorkflowException) as ex:
            activity.identifier_grant(grant_data)
        assert str(ex.value) == "failed in Identifier Grant."
        mock_user_lock.assert_called()
        mock_activity_lock.assert_called()
        mock_user_unlock.assert_called()
        mock_activity_unlock.assert_called_with("locked_value")

    # def end(self):
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test_end -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_end(self, app, db, workflow, users, client):
        with patch("weko_workflow.views.WorkActivity.get_new_activity_id") as mock_get_new_activity_id:
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
            assert activity.detail != ""
            assert activity.current_action == "item_login"

            activity.end()

            assert activity.user is None
            assert activity._model is None
            assert activity.activity_id == None
            assert activity.detail == ""
            assert activity.current_action == None

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test__upload_files -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test__upload_files(self, app, db, workflow, users, client, mocker):
        activity = HeadlessActivity()
        activity._deposit = {"_buckets": {"deposit": uuid.uuid4()}}
        mocker.patch.object(Bucket, "query", new=Mock())
        mock_bucket = Mock(spec=Bucket)
        mock_bucket.size_limit = 1000
        mock_bucket.location.max_file_size = 500
        mocker.patch.object(Bucket.query, "get", return_value=mock_bucket)
        mock_object_version = MagicMock()
        mock_object_version.basename = "test.txt"
        mocker.patch("weko_workflow.headless.activity.ObjectVersion.create", return_value=mock_object_version,)
        mocker.patch("weko_workflow.headless.activity.ObjectVersion.set_contents")

        # Test case: file size exceeds limit
        with pytest.raises(FileSizeError) as ex:
            activity._upload_files([MagicMock(filename="test.txt", stream=mock_open(read_data="data"), content_length=501)])
        assert "File size limit exceeded." in str(ex.value)

        # Test case: file not found
        with pytest.raises(WekoWorkflowException) as ex:
            activity._upload_files(["non_existent_file.txt"])
        assert str(ex.value) == "file(non_existent_file.txt) is not found."

        # Test case: successful upload with file path
        mocker.patch("os.path.isfile", return_value=True)
        mocker.patch("os.path.getsize", return_value=10)
        with patch("builtins.open", mock_open(read_data="data")):
            files_info = activity._upload_files(["test.txt"])
            assert len(files_info) == 1
            assert files_info[0]["filename"] == "test.txt"

        # Test case: successful upload with FileStorage object
        file_storage = MagicMock(
            filename="test.txt", stream=mock_open(read_data="data"), content_length=10
        )
        files_info = activity._upload_files([file_storage])
        assert len(files_info) == 1
        assert files_info[0]["filename"] == "test.txt"

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test__user_lock -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test__user_lock(self, app, db, workflow, users, client, mocker):
        activity = HeadlessActivity()
        login_user(users[1]["obj"])
        activity.init_activity(users[1]["id"], workflow["workflow"].id)

        # Mocking the necessary methods and properties
        mock_current_cache_get = mocker.patch("weko_workflow.headless.activity.current_cache.get", return_value=None)
        mock_update_cache_data = mocker.patch("weko_workflow.headless.activity.update_cache_data")
        mock_get_activity_by_id = mocker.patch(
            "weko_workflow.api.WorkActivity.get_activity_by_id",
            return_value=MagicMock(activity_status=ActivityStatusPolicy.ACTIVITY_BEGIN)
        )
        mock_current_app = mocker.patch("weko_workflow.headless.activity.current_app")
        mock_current_app.permanent_session_lifetime.seconds = 3600

        # Test case: _lock_skip is True
        activity._lock_skip = True
        assert activity._user_lock() is None

        # Test case: cur_locked_val is not empty
        mock_current_cache_get.return_value = "some_value"
        activity._lock_skip = False
        message = activity._user_lock()
        assert message == "Opened"
        mock_current_cache_get.assert_called_once_with("workflow_userlock_activity_{}".format(str(activity.user.id)))

        # Test case: cur_locked_val is empty and activity is in ACTIVITY_BEGIN status
        mock_current_cache_get.return_value = None
        message = activity._user_lock()
        assert message == "Locked"
        mock_get_activity_by_id.assert_called_once_with(activity.activity_id)
        mock_update_cache_data.assert_called_once_with("workflow_userlock_activity_{}".format(str(activity.user.id)), activity.activity_id, 3600)

        # Test case: cur_locked_val is empty and activity is in ACTIVITY_MAKING status
        mock_get_activity_by_id.return_value.activity_status = (ActivityStatusPolicy.ACTIVITY_MAKING)
        message = activity._user_lock()
        assert message == "Locked"
        mock_get_activity_by_id.assert_called_with(activity.activity_id)
        mock_update_cache_data.assert_called_with("workflow_userlock_activity_{}".format(str(activity.user.id)),activity.activity_id, 3600)

        # Test case: cur_locked_val is empty and activity is not in ACTIVITY_BEGIN or ACTIVITY_MAKING status
        mock_get_activity_by_id.return_value.activity_status = (ActivityStatusPolicy.ACTIVITY_ERROR)
        message = activity._user_lock()
        assert message == "Locked"
        mock_get_activity_by_id.assert_called_with(activity.activity_id)

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test__user_unlock -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test__user_unlock(self, app, db, workflow, users, client, mocker):
        activity = HeadlessActivity()
        login_user(users[1]["obj"])
        activity.init_activity(users[1]["id"], workflow["workflow"].id)

        # Mocking the necessary methods and properties
        mock_delete_user_lock_activity_cache = mocker.patch("weko_workflow.headless.activity.delete_user_lock_activity_cache")

        # Test case: _lock_skip is True
        activity._lock_skip = True
        result = activity._user_unlock()
        assert result is None
        mock_delete_user_lock_activity_cache.assert_not_called()

        # Test case: _lock_skip is False
        activity._lock_skip = False
        data = {"key": "value"}
        result = activity._user_unlock(data)
        mock_delete_user_lock_activity_cache.assert_called_once_with(activity.activity_id, data)

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test__activity_lock -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test__activity_lock(self, app, db, workflow, users, client, mocker):
        activity = HeadlessActivity()
        login_user(users[1]["obj"])
        activity.init_activity(users[1]["id"], workflow["workflow"].id)

        # Test case: _lock_skip is True
        activity._lock_skip = True
        result = activity._activity_lock()
        assert result is None

        # Test case: _lock_skip is False and lock_activity returns a valid response
        activity._lock_skip = False
        mock_lock_activity = mocker.patch("weko_workflow.headless.activity.lock_activity",
            return_value=(MagicMock(get_json=lambda: {"locked_value": "test_locked_value"}),None)
        )
        result = activity._activity_lock()
        assert result == "test_locked_value"
        mock_lock_activity.assert_called_once_with(activity.activity_id)

        # Test case: lock_activity raises an exception
        mock_lock_activity = mocker.patch("weko_workflow.headless.activity.lock_activity",
            side_effect=Exception("lock_activity error")
        )
        with pytest.raises(Exception) as ex:
            activity._activity_lock()
        assert str(ex.value) == "lock_activity error"

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test__activity_lock -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test__activity_lock(self, app, db, workflow, users, client, mocker):
        activity = HeadlessActivity()
        login_user(users[1]["obj"])
        activity.init_activity(users[1]["id"], workflow["workflow"].id)

        # Test case: _lock_skip is True
        activity._lock_skip = True
        result = activity._activity_lock()
        assert result is None

        # Test case: _lock_skip is False and lock_activity returns a valid response
        activity._lock_skip = False
        mock_lock_activity = mocker.patch("weko_workflow.headless.activity.lock_activity",
            return_value=(MagicMock(get_json=lambda: {"locked_value": "test_locked_value"}),None)
        )
        result = activity._activity_lock()
        assert result == "test_locked_value"
        mock_lock_activity.assert_called_once_with(activity.activity_id)

        # Test case: lock_activity raises an exception
        mock_lock_activity = mocker.patch("weko_workflow.headless.activity.lock_activity",
            side_effect=Exception("lock_activity error")
        )
        with pytest.raises(Exception) as ex:
            activity._activity_lock()
        assert str(ex.value) == "lock_activity error"

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test__activity_unlock -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test__activity_unlock(self, app, db, workflow, users, client, mocker):
        activity = HeadlessActivity()
        login_user(users[1]["obj"])
        activity.init_activity(users[1]["id"], workflow["workflow"].id)

        # Mocking the necessary methods and properties
        mock_delete_lock_activity_cache = mocker.patch("weko_workflow.headless.activity.delete_lock_activity_cache")

        # Test case: _lock_skip is True
        activity._lock_skip = True
        result = activity._activity_unlock("test_locked_value")
        assert result is None
        mock_delete_lock_activity_cache.assert_not_called()

        # Test case: _lock_skip is False
        activity._lock_skip = False
        result = activity._activity_unlock("test_locked_value")
        mock_delete_lock_activity_cache.assert_called_once_with(activity.activity_id, {"locked_value": "test_locked_value"})
