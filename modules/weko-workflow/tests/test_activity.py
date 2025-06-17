import copy
import pytest
import uuid
from flask import jsonify, url_for
from unittest.mock import Mock, MagicMock, PropertyMock, patch, mock_open
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.datastructures import FileStorage
import json

from invenio_files_rest.errors import FileSizeError
from invenio_files_rest.models import Bucket, ObjectVersion
from invenio_pidstore.models import PersistentIdentifier

from invenio_db.shared import SQLAlchemy
from invenio_records.models import RecordMetadata
from weko_admin.models import Identifier
from weko_deposit.api import WekoDeposit, WekoRecord
from weko_workflow.errors import WekoWorkflowException
from weko_workflow.headless import HeadlessActivity
from weko_workflow.models import Activity


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp

# class HeadlessActivity(WorkActivity):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
class TestHeadlessActivity:
    # def __init__(self):
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test_init -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_init(self, app, db, workflow):
        activity = HeadlessActivity()
        assert activity is not None
        assert activity.user is None
        assert activity.workflow is None
        assert activity.item_type is None
        assert activity.recid is None
        assert activity.files_info is None
        assert activity._model is None
        assert activity._deposit is None

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
    def test_init_activity(self, app, db, item_type, workflow, users, client):
        # success to initialize activity for new item registration
        mock_activity = MagicMock(spec=Activity)
        mock_activity.activity_id = "A-TEST-00001"
        mock_activity.action_id = 3
        mock_activity.activity_community_id = None
        # without community
        with patch("weko_workflow.headless.activity.init_activity") as mock_init_activity, \
                patch("weko_workflow.headless.activity.HeadlessActivity.get_activity_by_id") as mock_get_activity:
            url = url_for("weko_workflow.display_activity", activity_id=mock_activity.activity_id)
            mock_init_activity.return_value = jsonify(
                {"code": 0, "msg": "success", "data": {"redirect": url}}), 200
            mock_get_activity.return_value = mock_activity

            activity = HeadlessActivity()
            detail = activity.init_activity(users[0]["id"], workflow_id=workflow["workflow"].id)

            assert detail == url
            assert activity._model is mock_activity
            assert activity.user == users[0]["obj"]
            assert activity.workflow == workflow["workflow"]
            assert activity.current_action == "item_login"
            assert activity.activity_id == mock_activity.activity_id
            assert activity.community is None
            mock_init_activity.assert_called_once()
            mock_get_activity.assert_called_once()

        # with community
        mock_activity.activity_id = "A-TEST-00002"
        mock_activity.activity_community_id = "comm01"
        with patch("weko_workflow.headless.activity.init_activity") as mock_init_activity, \
                patch("weko_workflow.headless.activity.HeadlessActivity.get_activity_by_id") as mock_get_activity:
            url = url_for(
                "weko_workflow.display_activity",
                activity_id=mock_activity.activity_id, community=mock_activity.activity_community_id
            )
            mock_init_activity.return_value = jsonify(
                {"code": 0, "msg": "success", "data": {"redirect": url}}), 200
            mock_get_activity.return_value = mock_activity

            activity = HeadlessActivity()
            detail = activity.init_activity(
                users[0]["id"], workflow_id=workflow["workflow"].id,
                community=mock_activity.activity_community_id
            )

            assert detail == url
            assert activity._model is mock_activity
            assert activity.user == users[0]["obj"]
            assert activity.workflow == workflow["workflow"]
            assert activity.current_action == "item_login"
            assert activity.activity_id == mock_activity.activity_id
            assert activity.community == mock_activity.activity_community_id
            mock_init_activity.assert_called_once()
            mock_get_activity.assert_called_once()

        with patch("weko_workflow.headless.activity.init_activity") as mock_init_activity, \
                patch("weko_workflow.headless.activity.HeadlessActivity.get_activity_by_id") as mock_get_activity:

            # failed to initialize activity
            mock_init_activity.return_value = jsonify({"code": -1, "msg": "can not make activity_id"}), 500
            activity = HeadlessActivity()
            with pytest.raises(WekoWorkflowException) as ex:
                activity.init_activity(users[0]["id"], workflow_id=workflow["workflow"].id)
            assert ex.value.args[0] == "can not make activity_id"
            mock_init_activity.assert_called_once()
            mock_get_activity.assert_not_called()

        # already initialized activity
        with pytest.raises(WekoWorkflowException) as ex:
            activity = HeadlessActivity()
            activity._model = MagicMock(spec=Activity)
            activity.init_activity(users[0]["id"], workflow_id=workflow["workflow"].id)
        assert ex.value.args[0] == "activity is already initialized."

        # no specified workflow_id
        activity = HeadlessActivity()
        with pytest.raises(WekoWorkflowException) as ex:
            activity.init_activity(users[0]["id"])
        assert ex.value.args[0] == "workflow_id is required to create activity."

        # workflow_id is not found
        with pytest.raises(WekoWorkflowException) as ex:
            activity.init_activity(users[0]["id"], workflow_id=999)
        assert ex.value.args[0] == "workflow(id=999) is not found."

        # success to initialize activity for item edit
        # without community
        mock_activity = MagicMock(spec=Activity)
        mock_activity.activity_id = "A-TEST-00003"
        mock_activity.action_id = 3
        mock_activity.activity_community_id = None
        mock_activity.workflow = workflow["workflow"]
        with patch("weko_workflow.headless.activity.prepare_edit_item") as mock_prepare, \
                patch("weko_workflow.headless.activity.HeadlessActivity.get_activity_by_id") as mock_get_activity,\
                patch("weko_workflow.headless.activity.PersistentIdentifier.get_by_object") as mock_get_pid:
            url = url_for("weko_workflow.display_activity", activity_id=mock_activity.activity_id)
            mock_prepare.return_value = jsonify(
                {"code": 0, "msg": "success", "data": {"redirect": url}})
            mock_get_activity.return_value = mock_activity
            mock_pid = MagicMock(spec=PersistentIdentifier)
            mock_pid.pid_value = "200001.0"
            mock_get_pid.return_value = mock_pid

            activity = HeadlessActivity()
            detail = activity.init_activity(users[0]["id"], item_id="200001")

            assert detail == url
            assert activity.recid == mock_pid.pid_value
            assert activity._model is mock_activity
            assert activity.user == users[0]["obj"]
            assert activity.workflow == workflow["workflow"]
            assert activity.current_action == "item_login"
            assert activity.activity_id == mock_activity.activity_id
            assert activity.community is None
            mock_prepare.assert_called_once()
            mock_get_activity.assert_called_once()

        # with community
        mock_activity.activity_id = "A-TEST-00004"
        mock_activity.activity_community_id = "comm01"
        with patch("weko_workflow.headless.activity.prepare_edit_item") as mock_prepare, \
                patch("weko_workflow.headless.activity.HeadlessActivity.get_activity_by_id") as mock_get_activity,\
                patch("weko_workflow.headless.activity.PersistentIdentifier.get_by_object") as mock_get_pid:
            url = url_for("weko_workflow.display_activity", activity_id=mock_activity.activity_id, community=mock_activity.activity_community_id)
            mock_prepare.return_value = jsonify(
                {"code": 0, "msg": "success", "data": {"redirect": url}}
            )
            mock_get_activity.return_value = mock_activity
            mock_pid = MagicMock(spec=PersistentIdentifier)
            mock_pid.pid_value = "200001.0"
            mock_get_pid.return_value = mock_pid

            activity = HeadlessActivity()
            detail = activity.init_activity(
                users[0]["id"], item_id="200001", community=mock_activity.activity_community_id
            )

            assert detail == url
            assert activity.recid == mock_pid.pid_value
            assert activity._model is mock_activity
            assert activity.user == users[0]["obj"]
            assert activity.workflow == workflow["workflow"]
            assert activity.current_action == "item_login"
            assert activity.activity_id == mock_activity.activity_id
            assert activity.community == mock_activity.activity_community_id
            mock_prepare.assert_called_once()
            mock_get_activity.assert_called_once()

        # failed to initialize activity for item edit
        with patch("weko_workflow.headless.activity.prepare_edit_item") as mock_prepare:
            mock_prepare.return_value = jsonify({"code": -1, "msg": "An error has occurred."})
            activity = HeadlessActivity()
            with pytest.raises(WekoWorkflowException) as ex:
                activity.init_activity(users[0]["id"], item_id="200001")
            assert ex.value.args[0] == "An error has occurred."

        # success to initialize activity for item delete
        mock_activity = MagicMock(spec=Activity)
        mock_activity.activity_id = "D-TEST-00005"
        mock_activity.action_id = 4
        mock_activity.activity_community_id = None
        mock_activity.workflow = workflow["workflow"]
        with patch("weko_workflow.headless.activity.prepare_delete_item") as mock_prepare, \
                patch("weko_workflow.headless.activity.HeadlessActivity.get_activity_by_id") as mock_get_activity,\
                patch("weko_workflow.headless.activity.PersistentIdentifier.get_by_object") as mock_get_pid:
            url = url_for("weko_workflow.display_activity", activity_id=mock_activity.activity_id)
            mock_prepare.return_value = jsonify(
                {"code": 0, "msg": "success", "data": {"redirect": url}})
            mock_get_activity.return_value = mock_activity
            mock_pid = MagicMock(spec=PersistentIdentifier)
            mock_pid.pid_value = "200001.0"
            mock_get_pid.return_value = mock_pid

            activity = HeadlessActivity()
            detail = activity.init_activity(users[0]["id"], item_id="200001", for_delete=True)

            assert detail == url
            assert activity.recid == mock_pid.pid_value
            assert activity._model is mock_activity
            assert activity.user == users[0]["obj"]
            assert activity.workflow == workflow["workflow"]
            assert activity.current_action == "approval"
            assert activity.activity_id == mock_activity.activity_id
            assert activity.community is None
            mock_prepare.assert_called_once()
            mock_get_activity.assert_called_once()

        # item delete directly
        with patch("weko_workflow.headless.activity.prepare_delete_item") as mock_prepare:
            url = url_for("invenio_records_ui.recid", pid_value="200001")
            mock_prepare.return_value = jsonify({"code": 0, "msg": "success", "data": {"redirect": url}})

            activity = HeadlessActivity()
            detail = activity.init_activity(users[0]["id"], item_id="200001", for_delete=True)

            assert detail == url
            assert activity.recid == "200001"
            assert activity._model is None
            assert activity.user == users[0]["obj"]
            assert activity.workflow is None

        # success to initialize activity for existing activity
        mock_activity = MagicMock(spec=Activity)
        mock_activity.activity_id = "A-TEST-00006"
        mock_activity.action_id = 3
        mock_activity.activity_community_id = None
        mock_activity.workflow = workflow["workflow"]
        # login user matches
        mock_activity.activity_login_user = users[0]["id"]
        mock_activity.shared_user_id = users[3]["id"]
        with patch("weko_workflow.headless.activity.verify_deletion") as mock_verify_deletion, \
                patch("weko_workflow.api.WorkActivity.get_activity_by_id") as mock_get_activity_by_id, \
                patch("weko_workflow.headless.activity.PersistentIdentifier.get_by_object") as mock_get_pid, \
                patch("weko_workflow.headless.activity.HeadlessActivity._activity_lock") as mock_activity_lock, \
                patch("weko_workflow.headless.activity.HeadlessActivity._activity_unlock") as mock_activity_unlock:
            mock_verify_deletion.return_value = jsonify({"code": 200, "is_delete": False}), 200
            mock_get_activity_by_id.return_value = mock_activity
            mock_pid = MagicMock(spec=PersistentIdentifier)
            mock_pid.pid_value = "200002.0"
            mock_get_pid.return_value = mock_pid

            activity = HeadlessActivity()
            detail = activity.init_activity(users[0]["id"], workflow_id=workflow["workflow"].id, activity_id=mock_activity.activity_id)
            assert detail == url_for("weko_workflow.display_activity", activity_id=mock_activity.activity_id)
            assert activity._model is mock_activity
            assert activity.user == users[0]["obj"]
            assert activity.workflow == workflow["workflow"]
            assert activity.current_action == "item_login"
            assert activity.activity_id == mock_activity.activity_id
            assert activity.community is None
            assert activity._recid == mock_pid.pid_value
            mock_verify_deletion.assert_called_once_with(mock_activity.activity_id)
            mock_get_activity_by_id.assert_called_once_with(mock_activity.activity_id)
            mock_activity_lock.assert_called_once()
            mock_activity_unlock.assert_called_once()

        # shared user matches
        with patch("weko_workflow.headless.activity.verify_deletion") as mock_verify_deletion, \
                patch("weko_workflow.api.WorkActivity.get_activity_by_id") as mock_get_activity_by_id, \
                patch("weko_workflow.headless.activity.PersistentIdentifier.get_by_object") as mock_get_pid, \
                patch("weko_workflow.headless.activity.HeadlessActivity._activity_lock") as mock_activity_lock, \
                patch("weko_workflow.headless.activity.HeadlessActivity._activity_unlock") as mock_activity_unlock:
            mock_verify_deletion.return_value = jsonify({"code": 200, "is_delete": False}), 200
            mock_get_activity_by_id.return_value = mock_activity
            mock_pid = MagicMock(spec=PersistentIdentifier)
            mock_pid.pid_value = "200002.0"
            mock_get_pid.return_value = mock_pid

            activity = HeadlessActivity()
            detail = activity.init_activity(users[3]["id"], workflow_id=workflow["workflow"].id, activity_id=mock_activity.activity_id)
            assert detail == url_for("weko_workflow.display_activity", activity_id=mock_activity.activity_id)
            assert activity._model is mock_activity
            assert activity.user == users[3]["obj"]
            assert activity.workflow == workflow["workflow"]
            assert activity.current_action == "item_login"
            assert activity.activity_id == mock_activity.activity_id
            assert activity.community is None
            assert activity._recid == mock_pid.pid_value
            mock_verify_deletion.assert_called_once_with(mock_activity.activity_id)
            mock_get_activity_by_id.assert_called_once_with(mock_activity.activity_id)
            mock_activity_lock.assert_called_once()
            mock_activity_unlock.assert_called_once()

        # admin user
        with patch("weko_workflow.headless.activity.verify_deletion") as mock_verify_deletion, \
                patch("weko_workflow.api.WorkActivity.get_activity_by_id") as mock_get_activity_by_id, \
                patch("weko_workflow.headless.activity.PersistentIdentifier.get_by_object") as mock_get_pid, \
                patch("weko_workflow.headless.activity.HeadlessActivity._activity_lock") as mock_activity_lock, \
                patch("weko_workflow.headless.activity.HeadlessActivity._activity_unlock") as mock_activity_unlock:
            mock_verify_deletion.return_value = jsonify({"code": 200, "is_delete": False}), 200
            mock_get_activity_by_id.return_value = mock_activity
            mock_pid = MagicMock(spec=PersistentIdentifier)
            mock_pid.pid_value = "200002.0"
            mock_get_pid.return_value = mock_pid

            activity = HeadlessActivity()
            detail = activity.init_activity(users[1]["id"], workflow_id=workflow["workflow"].id, activity_id=mock_activity.activity_id)
            assert detail == url_for("weko_workflow.display_activity", activity_id=mock_activity.activity_id)
            assert activity._model is mock_activity
            assert activity.user == users[1]["obj"]
            assert activity.workflow == workflow["workflow"]
            assert activity.current_action == "item_login"
            assert activity.activity_id == mock_activity.activity_id
            assert activity.community is None
            assert activity._recid == mock_pid.pid_value
            mock_verify_deletion.assert_called_once_with(mock_activity.activity_id)
            mock_get_activity_by_id.assert_called_once_with(mock_activity.activity_id)
            mock_activity_lock.assert_called_once()
            mock_activity_unlock.assert_called_once()


        # no authority to access activity
        with patch("weko_workflow.headless.activity.verify_deletion") as mock_verify_deletion, \
                patch("weko_workflow.api.WorkActivity.get_activity_by_id") as mock_get_activity_by_id:
            mock_verify_deletion.return_value = jsonify({"code": 200, "is_delete": False}), 200
            mock_get_activity_by_id.return_value = mock_activity
            activity = HeadlessActivity()
            with pytest.raises(WekoWorkflowException) as ex:
                activity.init_activity(users[4]["id"], workflow_id=workflow["workflow"].id, activity_id=mock_activity.activity_id)
            assert ex.value.args[0] == f"user({users[4]['id']}) cannot access activity({mock_activity.activity_id})."

        # activity is already deleted
        with patch("weko_workflow.headless.activity.verify_deletion") as mock_verify_deletion:
            mock_verify_deletion.return_value = jsonify({"code": 200, "is_delete": True}), 200
            activity_id = "A-TEST-00007"
            activity = HeadlessActivity()
            with pytest.raises(WekoWorkflowException) as ex:
                activity.init_activity(users[1]["id"], workflow_id=workflow["workflow"].id, activity_id=activity_id)
            assert ex.value.args[0] == "activity({}) is already deleted.".format(activity_id)
            mock_verify_deletion.assert_called_once_with(activity_id)

        with patch("weko_workflow.headless.activity.verify_deletion") as mock_verify_deletion, \
                patch("weko_workflow.api.WorkActivity.get_activity_by_id") as mock_get_activity_by_id:
            activity_id = "A-TEST-00008"
            mock_verify_deletion.return_value = jsonify({"code": 200, "is_delete": False}), 200
            mock_get_activity_by_id.return_value = None
            with pytest.raises(WekoWorkflowException) as ex:
                activity.init_activity(users[1]["id"], workflow_id=workflow["workflow"].id, activity_id=activity_id)
            assert ex.value.args[0] == "activity({}) is not found.".format(activity_id)
            mock_verify_deletion.assert_called_once_with(activity_id)
            mock_get_activity_by_id.assert_called_once_with(activity_id)


    #  item_registration(slef, metadata, files, index, comment):
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test_item_registration -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_item_registration(self, app, db, item_type, workflow, users, client, mocker):
        activity = HeadlessActivity()

        with pytest.raises(WekoWorkflowException) as ex:
            activity.item_registration(metadata={}, files=[], index=[], comment="")
        assert ex.value.args[0] == "activity is not initialized."

        # activity.init_activity(users[0]["id"], workflow_id=workflow["workflow"].id)
        activity._model = MagicMock(spec=Activity, activity_id="A-TEST-00001", activity_community_id=None)

        with patch("weko_workflow.headless.activity.check_validation_error_msg") as mock_validation_msg:
            msg = ["error<br/>title"]
            error_list = {"mapping": {"title": "error"}}
            mock_validation_msg.return_value = jsonify(code=1, msg=msg, error_list=error_list)
            with pytest.raises(WekoWorkflowException) as ex:
                activity.item_registration(metadata={}, files=[], index=[], comment="")
            assert ex.value.args[0] == {"msg": ["error<br/>title"], "error_list": {"mapping": {"title": "error"}}}

        with patch("weko_workflow.headless.activity.check_validation_error_msg") as mock_validation_msg, \
                patch("weko_workflow.headless.activity.HeadlessActivity._input_metadata") as mock_input_metadata, \
                patch("weko_workflow.headless.activity.HeadlessActivity._designate_index") as mock_designate_index, \
                patch("weko_workflow.headless.activity.HeadlessActivity._comment") as mock_comment:
            mock_validation_msg.return_value = jsonify(code=0)
            mock_input_metadata.return_value = "200001"
            activity = HeadlessActivity()
            mock_activity = MagicMock(spec=Activity, activity_id="A-TEST-00001", activity_community_id=None)
            activity._model = mock_activity
            url = activity.item_registration({"metadata", "test"}, files=["test.txt"], index=["1"], comment="test")
            assert activity._recid == "200001"
            assert url == url_for("weko_workflow.display_activity", activity_id=mock_activity.activity_id)

    # def auto(self, **params):
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test_auto -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_auto(sefl, app, workflow, mocker):
        mock_activity = MagicMock(spec=Activity)
        mock_activity.activity_id = "A-TEST-00001"
        mock_activity.action_id = 3         # "item_login"
        mock_activity.activity_community_id = None

        def se_init_activity(*args, **kwargs):
            activity._model = mock_activity
        def se_item_registration(*args, **kwargs):
            activity._model.action_id = 5   # "item_link"
            activity._recid = "200001"
        def se_item_link(*args, **kwargs):
            activity._model.action_id = 2   # "end_action"
        def se_item_link2(*args, **kwargs):
            activity._model.action_id = 7   # "identifier_grant"
        def se_identifier_grant(*args, **kwargs):
            activity._model.action_id = 4   # "approval"

        mock_init_activity = mocker.patch("weko_workflow.headless.activity.HeadlessActivity.init_activity")
        mock_init_activity.side_effect = se_init_activity
        mock_item_registration = mocker.patch("weko_workflow.headless.activity.HeadlessActivity.item_registration")
        mock_item_registration.side_effect = se_item_registration
        mock_item_link = mocker.patch("weko_workflow.headless.activity.HeadlessActivity.item_link")
        mock_item_link.side_effect = se_item_link

        activity = HeadlessActivity(_lock_skip=True)
        url, current_action, recid = activity.auto(user_id=1, workflow_id=1)
        assert url == url_for("weko_workflow.display_activity", activity_id=mock_activity.activity_id)
        assert current_action == "end_action"
        assert recid == "200001"

        mock_activity = MagicMock(spec=Activity)
        mock_activity.activity_id = "A-TEST-00002"
        mock_activity.action_id = 3         # "item_login"
        mock_activity.activity_community_id = None

        mock_item_link.side_effect = se_item_link2
        mock_identifier_grant = mocker.patch("weko_workflow.headless.activity.HeadlessActivity.identifier_grant")
        mock_identifier_grant.side_effect = se_identifier_grant

        activity = HeadlessActivity(_lock_skip=True)
        url, current_action, recid = activity.auto(user_id=1, workflow_id=1)
        assert url == url_for("weko_workflow.display_activity", activity_id=mock_activity.activity_id)
        assert current_action == "approval"
        assert recid == "200001"

        mock_activity = MagicMock(spec=Activity)
        mock_activity.activity_id = "A-TEST-00002"
        mock_activity.action_id = 6         # "oa_policy"
        mock_activity.activity_community_id = None

        activity = HeadlessActivity(_lock_skip=True)
        with pytest.raises(NotImplementedError) as ex:
            activity.auto(user_id=1, workflow_id=1)
        assert ex.value.args[0] == "Action {} is not implemented.".format("oa_policy")


    # def _input_metadata(self, metadata, files=None, non_extract=None):
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test__input_metadata_new -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test__input_metadata_new(self, app, db, item_type, workflow, users, client, mocker):
        mock_feedback_mail = mocker.patch("weko_workflow.headless.activity.HeadlessActivity.create_or_update_action_feedbackmail")
        mock_request_mail = mocker.patch("weko_workflow.headless.activity.HeadlessActivity.create_or_update_activity_request_mail")
        mock_deposit_create = mocker.patch("weko_workflow.headless.activity.WekoDeposit.create", return_value=MagicMock(spec=WekoDeposit))
        mock_deposit_update = mocker.patch("weko_workflow.headless.activity.WekoDeposit.update")
        mock_deposit_delete = mocker.patch("weko_workflow.headless.activity.WekoDeposit.commit")

        mocker.patch("weko_workflow.headless.activity.get_mapping", return_value={"title.@value": "item_title.subitem_title", "identifierRegistration.@attributes.identifierType": "item_1617186819068.subitem_identifier_reg_type"})
        mocker.patch("weko_search_ui.utils.get_data_by_property", return_value=(["Test Title"], "item_title.subitem_title"))
        mocker.patch("weko_workflow.headless.activity.current_pidstore.minters", {"weko_deposit_minter": lambda record_uuid, data: MagicMock(pid_value="200001")})
        mock_upt_meta = mocker.patch("weko_workflow.headless.activity.HeadlessActivity.upt_activity_metadata")

        files_info = [
            {"filename": "test.txt", "key": "test.txt", "version_id": str(uuid.uuid4())},
            {"filename": "ignore.txt", "key": "ignore.txt", "version_id": str(uuid.uuid4())}
        ]
        activity = HeadlessActivity(_lock_skip=True)
        mock_activity = MagicMock(spec=Activity)
        mock_activity.activity_id = "A-TEST-00001"
        mock_activity.action_id = 3  # "item_login"
        mock_activity.activity_community_id = None
        activity._model = mock_activity
        activity.workflow = workflow["workflow"]
        activity.workflow.index_tree_id = "1"
        activity.item_type = item_type

        metadata = {
            "pubdate": "2024-01-01",
            "shared_user_id": users[1]["id"],
            "item_title":[{"subitem_title":"Test Title"}],
            "item_files": [{"filename": "test.txt"}, {"filename": "ignore.txt"}]
        }
        files = ["test.txt", "ignore.txt"]

        # success to input metadata
        with patch("weko_workflow.headless.activity.validate_form_input_data") as mock_validate, \
                patch("weko_workflow.headless.activity.HeadlessActivity.update_activity") as mock_update_activity, \
                patch("weko_workflow.headless.activity.HeadlessActivity._upload_files") as mock_upload, \
                patch("weko_workflow.headless.activity.HeadlessActivity._delete_file") as mock_delete, \
                patch("weko_workflow.headless.activity.HeadlessActivity.upt_activity_metadata") as mock_upt_meta:
            mock_validate.side_effect = lambda result, itemtype_id, metadata: result.update({"is_valid": True})
            mock_upload.return_value = copy.deepcopy(files_info)
            non_extract = ["ignore.txt"]
            recid = activity._input_metadata(metadata, files, non_extract)

            assert recid == "200001"
            mock_feedback_mail.assert_called_once()
            mock_request_mail.assert_called_once()
            mock_update_activity.call_args[0][0] == mock_activity.activity_id
            mock_update_activity.call_args[0][1]["shared_user_id"] == users[1]["id"]
            mock_deposit_create.assert_called_once()
            mock_upload.assert_called_once_with(files)
            mock_delete.assert_called_once()

            args, _ = mock_upt_meta.call_args
            assert args[0] == mock_activity.activity_id
            updated_data = json.loads(args[1])

            assert updated_data["metainfo"]["pubdate"] == "2024-01-01"
            assert updated_data["metainfo"]["item_title"][0]["subitem_title"] == "Test Title"
            assert updated_data["files"][0]["filename"] == "test.txt"
            assert updated_data["files"][0]["non_extract"] is False
            assert updated_data["files"][1]["filename"] == "ignore.txt"
            assert updated_data["files"][1]["non_extract"] is True

        activity = HeadlessActivity(_lock_skip=True)
        mock_activity = MagicMock(spec=Activity)
        mock_activity.activity_id = "A-TEST-00001"
        mock_activity.action_id = 3  # "item_login"
        mock_activity.activity_community_id = None
        activity._model = mock_activity
        activity.workflow = workflow["workflow"]
        activity.workflow.index_tree_id = "1"
        activity.item_type = item_type

        metadata = {
            "pubdate": "2024-01-01",
            "weko_shared_id": users[1]["id"],
            "item_title":[{"subitem_title":"Test Title"}],
            "item_files": [{"filename": "test.txt"}, {"filename": "ignore.txt"}]
        }

        with patch("weko_workflow.headless.activity.validate_form_input_data") as mock_validate, \
                patch("weko_workflow.headless.activity.HeadlessActivity.update_activity") as mock_update_activity, \
                patch("weko_workflow.headless.activity.HeadlessActivity._upload_files") as mock_upload, \
                patch("weko_workflow.headless.activity.HeadlessActivity._delete_file") as mock_delete, \
                patch("weko_workflow.headless.activity.HeadlessActivity.upt_activity_metadata") as mock_upt_meta:
            mock_validate.side_effect = lambda result, *args: result.update({"is_valid": True})
            mock_upload.return_value = copy.deepcopy(files_info)
            # non_extract not specified
            recid = activity._input_metadata(metadata, files)
            assert recid == "200001"
            mock_update_activity.call_args[0][0] == mock_activity.activity_id
            mock_update_activity.call_args[0][1]["shared_user_id"] == users[1]["id"]
            mock_upload.assert_called_once_with(files)
            mock_delete.assert_called_once()
            mock_upt_meta.assert_called_once()

            args, _ = mock_upt_meta.call_args
            updated_data = json.loads(args[1])
            assert updated_data["files"][0]["filename"] == "test.txt"
            assert updated_data["files"][0]["non_extract"] is False
            assert updated_data["files"][1]["filename"] == "ignore.txt"
            assert updated_data["files"][1]["non_extract"] is False

        workflow_index_tree_id = workflow["workflow"].index_tree_id
        activity.workflow.index_tree_id = None
        metadata = {
            "pubdate": "2024-01-01",
            "path": [str(workflow_index_tree_id)],
            "item_title":[{"subitem_title":"Test Title"}],
        }
        # files is None
        with patch("weko_workflow.headless.activity.validate_form_input_data") as mock_validate, \
                patch("weko_workflow.headless.activity.HeadlessActivity.update_activity") as mock_update_activity, \
                patch("weko_workflow.headless.activity.HeadlessActivity._upload_files") as mock_upload, \
                patch("weko_workflow.headless.activity.HeadlessActivity._delete_file") as mock_delete, \
                patch("weko_workflow.headless.activity.HeadlessActivity.upt_activity_metadata") as mock_upt_meta:
            mock_validate.side_effect = lambda result, *args: result.update({"is_valid": True})

            recid = activity._input_metadata(metadata)
            assert recid == "200001"
            mock_update_activity.call_args[0][0] == mock_activity.activity_id
            mock_update_activity.call_args[0][1]["shared_user_id"] == -1
            mock_upload.assert_called_once_with(None)
            mock_delete.assert_called_once()
            mock_upt_meta.assert_called_once()

        args, _ = mock_upt_meta.call_args
        updated_data = json.loads(args[1])
        assert updated_data["files"] == []
        assert updated_data["metainfo"]["pubdate"] == "2024-01-01"

        # no index tree id, shared_user_id and weko_shared_id are specified
        metadata = {
            "pubdate": "2024-01-01",
            "shared_user_id": users[1]["id"],
            "weko_shared_id": users[3]["id"],
            "item_title":[{"subitem_title":"Test Title"}],
            "item_files": [{"filename": "test.txt"}, {"filename": "ignore.txt"}]
        }
        with patch("weko_workflow.headless.activity.validate_form_input_data") as mock_validate, \
                patch("weko_workflow.headless.activity.HeadlessActivity.update_activity") as mock_update_activity, \
                patch("weko_workflow.headless.activity.HeadlessActivity._upload_files") as mock_upload, \
                patch("weko_workflow.headless.activity.HeadlessActivity._delete_file") as mock_delete, \
                patch("weko_workflow.headless.activity.HeadlessActivity.upt_activity_metadata") as mock_upt_meta:
            mock_validate.side_effect = lambda result, *args: result.update({"is_valid": True})

            with pytest.raises(WekoWorkflowException) as ex:
                activity._input_metadata(metadata, files)
            assert ex.value.args[0] == "Index is not specified in workflow or item metadata."
            mock_update_activity.call_args[0][0] == mock_activity.activity_id
            mock_update_activity.call_args[0][1]["shared_user_id"] == users[1]["id"]    # shared_user_id is used

        metadata = {
            "pubdate": "2024-01-01",
            "path": [str(workflow_index_tree_id)],
            "item_title":[{"subitem_title":"Test Title"}],
        }

        activity.workflow.index_tree_id = workflow_index_tree_id
        # input_metadata_invalid
        with patch("weko_workflow.headless.activity.validate_form_input_data") as mock_validate, \
                patch("weko_workflow.headless.activity.HeadlessActivity.update_activity") as mock_update_activity, \
                patch("weko_workflow.headless.activity.HeadlessActivity._upload_files") as mock_upload, \
                patch("weko_workflow.headless.activity.HeadlessActivity._delete_file") as mock_delete, \
                patch("weko_workflow.headless.activity.HeadlessActivity.upt_activity_metadata") as mock_upt_meta:
            mock_validate.side_effect = lambda result, *args: result.update({"is_valid": False, "error": "Invalid metadata"})

            with pytest.raises(WekoWorkflowException) as ex:
                activity._input_metadata(metadata)
            assert ex.value.args[0] == "Invalid metadata"
            mock_upt_meta.assert_called_once()

        # upt_activity_metadata raises Exception
        with patch("weko_workflow.headless.activity.validate_form_input_data") as mock_validate, \
                patch("weko_workflow.headless.activity.HeadlessActivity.update_activity") as mock_update_activity, \
                patch("weko_workflow.headless.activity.HeadlessActivity._upload_files") as mock_upload, \
                patch("weko_workflow.headless.activity.HeadlessActivity._delete_file") as mock_delete, \
                patch("weko_workflow.headless.activity.HeadlessActivity.upt_activity_metadata") as mock_upt_meta:
            mock_validate.side_effect = lambda result, *args: result.update({"is_valid": False, "error": "Invalid metadata"})
            mock_upt_meta.side_effect = SQLAlchemyError("Database error")
            with pytest.raises(WekoWorkflowException) as ex:
                activity._input_metadata(metadata, files)
            assert ex.value.args[0] == "Failed to input metadata to deposit: Database error"

        # upt_activity_metadata raises Exception
        with patch("weko_workflow.headless.activity.validate_form_input_data") as mock_validate, \
                patch("weko_workflow.headless.activity.HeadlessActivity.update_activity") as mock_update_activity, \
                patch("weko_workflow.headless.activity.HeadlessActivity._upload_files") as mock_upload, \
                patch("weko_workflow.headless.activity.HeadlessActivity._delete_file") as mock_delete, \
                patch("weko_workflow.headless.activity.HeadlessActivity.upt_activity_metadata") as mock_upt_meta:
            mock_validate.side_effect = lambda result, *args: result.update({"is_valid": False, "error": "Invalid metadata"})
            mock_upt_meta.side_effect = ValueError("Unexpected Error")
            with pytest.raises(WekoWorkflowException) as ex:
                activity._input_metadata(metadata, files)
            assert ex.value.args[0] == "Failed to input metadata to deposit: Unexpected Error"

        # item type mismatch
        metadata["$schema"] = "/items/jsonschema/999"
        with pytest.raises(WekoWorkflowException) as ex:
            activity._input_metadata(metadata, files)
        assert ex.value.args[0] == "Itemtype of importing item;(id={}) is not matched with workflow itemtype;(id={}).".format(999, workflow["workflow"].itemtype_id)

    # def _input_metadata(self, metadata, files=None, non_extract=None):
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test__input_metadata_update -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test__input_metadata_update(self, app, db, item_type, workflow, users, client, mocker):
        mock_feedback_mail = mocker.patch("weko_workflow.headless.activity.HeadlessActivity.create_or_update_action_feedbackmail")
        mock_request_mail = mocker.patch("weko_workflow.headless.activity.HeadlessActivity.create_or_update_activity_request_mail")
        mock_deposit_update = mocker.patch("weko_workflow.headless.activity.WekoDeposit.update")
        mock_deposit_delete = mocker.patch("weko_workflow.headless.activity.WekoDeposit.commit")

        mocker.patch("weko_workflow.headless.activity.get_mapping", return_value={"title.@value": "item_title.subitem_title", "identifierRegistration.@attributes.identifierType": "item_1617186819068.subitem_identifier_reg_type"})
        mocker.patch("weko_search_ui.utils.get_data_by_property", return_value=(["Test Title"], "item_title.subitem_title"))
        mock_upt_meta = mocker.patch("weko_workflow.headless.activity.HeadlessActivity.upt_activity_metadata")

        activity = HeadlessActivity(_lock_skip=True, _metadata_inheritance=True)
        mock_activity = MagicMock(spec=Activity)
        mock_activity.activity_id = "A-TEST-00001"
        mock_activity.action_id = 3  # "item_login"
        mock_activity.activity_community_id = None
        mock_activity.item_id = uuid.uuid4()
        activity._recid = "200001.0"
        activity._model = mock_activity
        activity.workflow = workflow["workflow"]
        activity.workflow.index_tree_id = "1"
        activity.item_type = item_type

        old_metadata = {
            "pubdate": "2023-01-01",
            "item_title":[{"subitem_title":"Old Title"}],
            "item_files": [{"filename": "old.txt"}, {"filename": "ignore.txt"}],
            "item_1617186819068": "Old Data"
        }
        metadata = {
            "pubdate": "2024-01-01",
            "edit_mode": "Keep",
            "item_title":[{"subitem_title":"Test Title"}],
            "item_files": [{"filename": "test.txt"}, {"filename": "ignore.txt"}],
            "item_1617186845099": "New Data"
        }
        _uuid = uuid.uuid4()
        old_files_info = [
            {"filename": "old.txt", "key": "old.txt", "version_id": str(uuid.uuid4())},
            {"filename": "ignore.txt", "key": "ignore.txt", "version_id": str(_uuid)}
        ]
        files_info = [
            {"filename": "test.txt", "key": "test.txt", "version_id": str(uuid.uuid4())},
            {"filename": "ignore.txt", "key": "ignore.txt", "version_id": str(_uuid)}
        ]
        files = ["test.txt", "ignore.txt"]

        # success to input metadata
        with patch("weko_workflow.headless.activity.validate_form_input_data") as mock_validate, \
                patch("weko_workflow.headless.activity.HeadlessActivity.update_activity") as mock_update_activity, \
                patch("weko_workflow.headless.activity.WekoDeposit.get_record") as mock_get_record, \
                patch("weko_workflow.headless.activity.PersistentIdentifier.get_by_object") as mock_get_pid, \
                patch("weko_workflow.headless.activity.to_files_js") as mock_files_js, \
                patch("weko_workflow.headless.activity.HeadlessActivity._upload_files") as mock_upload, \
                patch("weko_workflow.headless.activity.HeadlessActivity._delete_file") as mock_delete, \
                patch("weko_workflow.headless.activity.HeadlessActivity.upt_activity_metadata") as mock_upt_meta:
            mock_validate.side_effect = lambda result, itemtype_id, metadata: result.update({"is_valid": True})
            mock_upload.return_value = copy.deepcopy(files_info)

            mock_deposit = MagicMock(spec=WekoDeposit)
            mock_deposit.item_metadata = copy.deepcopy(old_metadata)
            mock_get_record.return_value = mock_deposit
            mock_pid = MagicMock(spec=PersistentIdentifier, pid_value="200001.0")
            mock_get_pid.return_value = mock_pid
            mock_files_js.return_value = copy.deepcopy(old_files_info)

            recid = activity._input_metadata(metadata, files)

            assert recid == mock_pid.pid_value
            mock_feedback_mail.assert_called_once()
            mock_request_mail.assert_called_once()
            mock_update_activity.call_args[0][0] == mock_activity.activity_id
            mock_update_activity.call_args[0][1]["shared_user_id"] == users[1]["id"]
            mock_upload.assert_called_once_with(files)
            mock_delete.assert_called_once()

            args, _ = mock_upt_meta.call_args
            assert args[0] == mock_activity.activity_id
            updated_data = json.loads(args[1])

            assert updated_data["metainfo"]["pubdate"] == "2024-01-01"
            assert updated_data["metainfo"]["item_title"][0]["subitem_title"] == "Test Title"
            assert updated_data["metainfo"]["item_1617186819068"] == "Old Data"  # Keep old data
            assert updated_data["metainfo"]["item_1617186845099"] == "New Data"
            assert updated_data["files"][0]["filename"] == "test.txt"
            assert updated_data["files"][1]["filename"] == "ignore.txt"

    # def _input_metadata(self, metadata, files=None, non_extract=None):
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test__input_metadata_upgrade -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test__input_metadata_upgrade(self, app, db, item_type, workflow, users, client, mocker):

        mock_feedback_mail = mocker.patch("weko_workflow.headless.activity.HeadlessActivity.create_or_update_action_feedbackmail")
        mock_request_mail = mocker.patch("weko_workflow.headless.activity.HeadlessActivity.create_or_update_activity_request_mail")
        mock_deposit_update = mocker.patch("weko_workflow.headless.activity.WekoDeposit.update")
        mock_deposit_delete = mocker.patch("weko_workflow.headless.activity.WekoDeposit.commit")

        mocker.patch("weko_workflow.headless.activity.db", return_value=MagicMock(spec=SQLAlchemy))
        mocker.patch("weko_workflow.headless.activity.get_mapping", return_value={"title.@value": "item_title.subitem_title", "identifierRegistration.@attributes.identifierType": "item_1617186819068.subitem_identifier_reg_type"})
        mocker.patch("weko_search_ui.utils.get_data_by_property", return_value=(["Test Title"], "item_title.subitem_title"))
        mock_upt_meta = mocker.patch("weko_workflow.headless.activity.HeadlessActivity.upt_activity_metadata")

        activity = HeadlessActivity(_lock_skip=True, _metadata_inheritance=True)
        mock_activity = MagicMock(spec=Activity)
        mock_activity.activity_id = "A-TEST-00001"
        mock_activity.action_id = 3  # "item_login"
        mock_activity.activity_community_id = None
        mock_activity.item_id = uuid.uuid4()
        activity._recid = "200001.0"
        activity._model = mock_activity
        activity.workflow = workflow["workflow"]
        activity.workflow.index_tree_id = "1"
        activity.item_type = item_type

        old_metadata = {
            "pubdate": "2023-01-01",
            "item_title":[{"subitem_title":"Old Title"}],
            "item_files": [{"filename": "old.txt"}, {"filename": "ignore.txt"}],
            "item_1617186819068": "Old Data"
        }
        metadata = {
            "pubdate": "2024-01-01",
            "edit_mode": "Upgrade",
            "item_title":[{"subitem_title":"Test Title"}],
            "item_files": [{"filename": "test.txt"}, {"filename": "ignore.txt"}],
            "item_1617186845099": "New Data"
        }
        _uuid = uuid.uuid4()
        old_files_info = [
            {"filename": "old.txt", "key": "old.txt", "version_id": str(uuid.uuid4())},
            {"filename": "ignore.txt", "key": "ignore.txt", "version_id": str(_uuid)}
        ]
        files_info = [
            {"filename": "test.txt", "key": "test.txt", "version_id": str(uuid.uuid4())},
            {"filename": "ignore.txt", "key": "ignore.txt", "version_id": str(_uuid)}
        ]
        files = ["test.txt", "ignore.txt"]

        # success to input metadata
        with patch("weko_workflow.headless.activity.validate_form_input_data") as mock_validate, \
                patch("weko_workflow.headless.activity.HeadlessActivity.update_activity") as mock_update_activity, \
                patch("weko_workflow.headless.activity.WekoDeposit.get_record") as mock_get_record, \
                patch("weko_workflow.headless.activity.PersistentIdentifier.get_by_object") as mock_get_pid, \
                patch("weko_workflow.headless.activity.PersistentIdentifier.get") as mock_get, \
                patch("weko_workflow.headless.activity.WekoRecord.get_record_by_pid") as mock_get_weko_record, \
                patch("weko_workflow.headless.activity.to_files_js") as mock_files_js, \
                patch("weko_workflow.headless.activity.HeadlessActivity._upload_files") as mock_upload, \
                patch("weko_workflow.headless.activity.HeadlessActivity._delete_file") as mock_delete, \
                patch("weko_workflow.headless.activity.HeadlessActivity.upt_activity_metadata") as mock_upt_meta:
            mock_validate.side_effect = lambda result, itemtype_id, metadata: result.update({"is_valid": True})
            mock_upload.return_value = copy.deepcopy(files_info)

            mock_deposit = MagicMock(spec=WekoDeposit)
            mock_deposit.pid = MagicMock(spec=PersistentIdentifier, pid_value="200001.2")
            mock_deposit.model = MagicMock(spec=RecordMetadata, id=uuid.uuid4())
            mock_deposit.item_metadata = copy.deepcopy(old_metadata)
            mock_draft_deposit = MagicMock(spec=WekoDeposit)
            mock_parent_deposit = MagicMock(spec=WekoDeposit)
            mock_parent_deposit.newversion.return_value = mock_deposit
            mock_get_record.side_effect = [mock_draft_deposit, mock_parent_deposit]

            mock_cur_pid = MagicMock(spec=PersistentIdentifier, pid_value="200001.0")
            mock_parent_pid = MagicMock(spec=PersistentIdentifier, pid_value="200001")
            mock_get.return_value = mock_parent_pid
            mock_get_pid.side_effect = [mock_cur_pid, mock_deposit.pid]
            mock_get_weko_record.return_value = MagicMock(spec=WekoRecord, pid=mock_deposit.pid)

            mock_files_js.return_value = copy.deepcopy(old_files_info)

            recid = activity._input_metadata(metadata, files)

            assert recid == mock_deposit.pid.pid_value
            mock_feedback_mail.assert_called_once()
            mock_request_mail.assert_called_once()
            mock_update_activity.call_args[0][0] == mock_activity.activity_id
            mock_update_activity.call_args[0][1]["shared_user_id"] == users[1]["id"]
            mock_upload.assert_called_once_with(files)
            mock_delete.assert_called_once()

            args, _ = mock_upt_meta.call_args
            assert args[0] == mock_activity.activity_id
            updated_data = json.loads(args[1])

            assert updated_data["metainfo"]["pubdate"] == "2024-01-01"
            assert updated_data["metainfo"]["item_title"][0]["subitem_title"] == "Test Title"
            assert updated_data["metainfo"]["item_1617186819068"] == "Old Data"  # Keep old data
            assert updated_data["metainfo"]["item_1617186845099"] == "New Data"
            assert updated_data["files"][0]["filename"] == "test.txt"
            assert updated_data["files"][1]["filename"] == "ignore.txt"

    # def _upload_files(self, files=None):
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

        # Test case: successful upload with file path
        with app.test_request_context(), \
            patch("os.path.isfile", return_value=True), \
            patch("os.path.getsize", return_value=10):
            with patch("builtins.open", mock_open(read_data="data")):
                files_info = activity._upload_files(["/temp/test.txt"])
                assert len(files_info) == 1
                assert files_info[0]["filename"] == "test.txt"

        # Test case: successful upload with FileStorage object, dict
        with app.test_request_context():
            mock_file = MagicMock(spec=FileStorage)
            mock_file.filename = "test.txt"
            mock_file.stream = mock_open(read_data="data")
            mock_file.content_length = 400
            mock_file.tell = lambda: 400
            mock_file.seek = lambda *pos: None
            files_info = activity._upload_files([mock_file, {"filename": "test2.txt", "size": 200}])
            assert len(files_info) == 2
            assert files_info[0]["filename"] == "test.txt"
            assert files_info[1]["filename"] == "test2.txt"

        # Test case: file size exceeds limit
        with pytest.raises(FileSizeError) as ex:
            mock_file = MagicMock(spec=FileStorage)
            mock_file.filename = "test.txt"
            mock_file.stream = mock_open(read_data="data")
            mock_file.content_length = 501
            mock_file.tell = lambda: 501
            mock_file.seek = lambda *pos: None
            activity._upload_files([mock_file])
        assert ex.value.description.startswith("File size limit exceeded.")

        # Test case: file not found
        with pytest.raises(WekoWorkflowException) as ex:
            activity._upload_files(["non_existent_file.txt"])
        assert ex.value.args[0] == "file(non_existent_file.txt) is not found."

    # def _delete_file(self, version_ids):
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test__delete_file -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test__delete_file(self, app, db, workflow, users, client, mocker):
        version_ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]

        mock_get = mocker.patch("weko_workflow.headless.activity.ObjectVersion.get")
        mock_object0 = MagicMock(spec=ObjectVersion, bucket=MagicMock(spec=Bucket), version_id=version_ids[0], key="test.txt", is_head=True, file_id=uuid.uuid4())
        mock_object1 = MagicMock(spec=ObjectVersion, bucket=MagicMock(spec=Bucket), version_id=version_ids[1], key="test2.txt", is_head=True, file_id=uuid.uuid4())
        mock_object2 = MagicMock(spec=ObjectVersion, bucket=MagicMock(spec=Bucket), version_id=version_ids[2], key="test3.txt", is_head=False, file_id=uuid.uuid4())
        mock_get.side_effect = [mock_object0, mock_object1, mock_object2]
        mocke_get_versions = mocker.patch("weko_workflow.headless.activity.ObjectVersion.get_versions")
        mocke_get_versions.return_value.first.side_effect = [
            MagicMock(spec=ObjectVersion, is_head=False),
            None
        ]
        mock_delete = mocker.patch("weko_workflow.headless.activity.delete_file_instance")
        mock_delete.side_effect = [False, True, False]
        mock_remove = mocker.patch("weko_workflow.headless.activity.remove_file_data")

        activity = HeadlessActivity()
        activity._delete_file(version_ids)

        mock_object0.remove.assert_called_once()
        mock_object1.remove.assert_called_once()
        mock_object2.remove.assert_called_once()
        mock_delete.assert_any_call(mock_object0.file_id)
        mock_delete.assert_any_call(mock_object1.file_id)
        mock_delete.assert_any_call(mock_object2.file_id)
        mock_remove.delay.assert_any_call(str(mock_object0.file_id))
        mock_remove.delay.assert_any_call(str(mock_object2.file_id))


    # def _designate_index(self, index=None):
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test__designate_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test__designate_index(self, app, db, workflow, users, client, mocker):
        activity = HeadlessActivity(_lock_skip=True)
        activity.workflow = workflow["workflow"]
        activity._recid = "200001"

        with patch("weko_workflow.headless.activity.update_index_tree_for_record") as mock_update_index:
            # index is not a list
            activity._designate_index("1")
            mock_update_index.assert_called_once_with(activity.recid, "1")

        activity = HeadlessActivity(_lock_skip=True)
        activity.workflow = workflow["workflow"]
        activity._recid = "200001"
        with patch("weko_workflow.headless.activity.update_index_tree_for_record") as mock_update_index:
        # Test case: index is a list
            activity._designate_index(["1", "2"])
            assert mock_update_index.call_count == 2
            mock_update_index.assert_any_call(activity.recid, "1")
            mock_update_index.assert_any_call(activity.recid, "2")

        activity = HeadlessActivity(_lock_skip=True)
        activity.workflow = workflow["workflow"]
        activity.workflow.index_tree_id = "3"
        activity._recid = "200001"
        with patch("weko_workflow.headless.activity.update_index_tree_for_record") as mock_update_index:
        # Test case: index is a list with item_type_id
            activity._designate_index(["1", "2"])
            mock_update_index.assert_called_once_with(activity.recid, "3")

        activity.workflow.index_tree_id = None
        with patch("weko_workflow.headless.activity.update_index_tree_for_record") as mock_update_index, \
                patch("weko_workflow.headless.activity.HeadlessActivity._activity_unlock") as mock_activity_unlock:
            mock_update_index.side_effect = Exception("Test Error")
            # Test case: successful index designation
            with pytest.raises(WekoWorkflowException) as ex:
                activity._designate_index(["1", "2"])
            mock_update_index.assert_called_with(activity.recid, "1")
            mock_activity_unlock.assert_called_once()


    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test__comment -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test__comment(self, app, db, workflow, users, client, mocker):
        activity = HeadlessActivity(_lock_skip=True)
        mock_activity = MagicMock(spec=Activity)
        mock_activity.activity_id = "A-TEST-00001"
        mock_activity.action_id = 3
        mock_activity.activity_community_id = None
        activity._model = mock_activity

        with patch("weko_workflow.headless.activity.next_action") as mock_next_action, \
                patch("weko_workflow.headless.activity.HeadlessActivity._activity_unlock") as mock_activity_unlock:
            mock_next_action.return_value = MagicMock(json={"code": 0, "msg": ""}), 200
            # Test case: successful comment
            activity._comment("This is a test comment")
            mock_next_action.assert_called_once_with(
                activity_id=mock_activity.activity_id, action_id=mock_activity.action_id,
                json_data={"commond": "This is a test comment"}
            )
            mock_activity_unlock.assert_called_once()

        # Test case: failed to set comment
        with patch("weko_workflow.headless.activity.next_action") as mock_next_action, \
                patch("weko_workflow.headless.activity.HeadlessActivity._activity_unlock") as mock_activity_unlock:
            mock_next_action.return_value = MagicMock(json={"code": 1, "msg": "error"}), 500
            with pytest.raises(WekoWorkflowException) as ex:
                activity._comment("This is a test comment")
            assert ex.value.args[0] == "error"
            mock_next_action.assert_called_once_with(
                activity_id=mock_activity.activity_id, action_id=mock_activity.action_id,
                json_data={"commond": "This is a test comment"}
            )
            mock_activity_unlock.assert_called_once()

        # Test case: SQLAlchemyError occurs in next_action
        with patch("weko_workflow.headless.activity.next_action") as mock_next_action, \
                patch("weko_workflow.headless.activity.HeadlessActivity._activity_unlock") as mock_activity_unlock:
            mock_next_action.side_effect = SQLAlchemyError("Test Error")
            with pytest.raises(WekoWorkflowException) as ex:
                activity._comment("This is a test comment")
            assert ex.value.args[0] == "failed to set comment."
            mock_activity_unlock.assert_called_once()

    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test_item_link -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_item_link(self, app, db, workflow, users, client, mocker):
        activity = HeadlessActivity(_lock_skip=True)
        mock_activity = MagicMock(spec=Activity)
        mock_activity.activity_id = "A-TEST-00001"
        mock_activity.action_id = 3
        mock_activity.activity_community_id = None
        activity._model = mock_activity

        link_data = [{"link": "test_link"}]
        with patch("weko_workflow.headless.activity.next_action") as mock_next_action, \
                patch("weko_workflow.headless.activity.HeadlessActivity._activity_unlock") as mock_activity_unlock:
            mock_next_action.return_value = MagicMock(json={"code": 0, "msg": ""}), 200
            # Test case: successful item link
            activity.item_link(link_data)
            mock_next_action.assert_called_once_with(
                activity_id=mock_activity.activity_id, action_id=mock_activity.action_id,
                json_data={"link_data": link_data}
            )
            mock_activity_unlock.assert_called_once()

        # Test case: failed to set comment
        with patch("weko_workflow.headless.activity.next_action") as mock_next_action, \
                patch("weko_workflow.headless.activity.HeadlessActivity._activity_unlock") as mock_activity_unlock:
            mock_next_action.return_value = MagicMock(json={"code": 1, "msg": "error"}), 500
            with pytest.raises(WekoWorkflowException) as ex:
                activity.item_link(link_data)
            assert ex.value.args[0] == "error"
            mock_next_action.assert_called_once_with(
                activity_id=mock_activity.activity_id, action_id=mock_activity.action_id,
                json_data={"link_data": link_data}
            )
            mock_activity_unlock.assert_called_once()

        # Test case: SQLAlchemyError occurs in next_action
        with patch("weko_workflow.headless.activity.next_action") as mock_next_action, \
                patch("weko_workflow.headless.activity.HeadlessActivity._activity_unlock") as mock_activity_unlock:
            mock_next_action.side_effect = SQLAlchemyError("Test Error")
            with pytest.raises(WekoWorkflowException) as ex:
                activity.item_link(link_data)
            assert ex.value.args[0] == "failed in Item Link."
            mock_activity_unlock.assert_called_once()


    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test_identifier_grant -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_identifier_grant(self, app, db, workflow, users, client, mocker):
        activity = HeadlessActivity(_lock_skip=True)
        activity._recid = "200001"
        mock_activity = MagicMock(spec=Activity)
        mock_activity.activity_id = "A-TEST-00001"
        mock_activity.action_id = 3
        mock_activity.activity_community_id = None
        activity._model = mock_activity

        mock_setting = MagicMock(spec=Identifier)
        mock_setting.jalc_doi = "10.1234"
        mock_setting.jalc_crossref_doi = "10.1235"
        mock_setting.jalc_datacite_doi = "10.1236"
        mock_setting.ndl_jalc_doi = "10.1237"

        grant_data = {"identifier_grant": "0"}
        with patch("weko_workflow.headless.activity.next_action") as mock_next_action, \
                patch("weko_workflow.headless.activity.get_identifier_setting") as mock_identifier, \
                patch("weko_workflow.headless.activity.HeadlessActivity._activity_unlock") as mock_activity_unlock:
            mock_next_action.return_value = MagicMock(json={"code": 0, "msg": ""}), 200
            mock_identifier.return_value = mock_setting

            # Test case: successful item link
            activity.identifier_grant(grant_data)
            _, kwargs = mock_next_action.call_args
            assert kwargs["activity_id"] == mock_activity.activity_id
            assert kwargs["action_id"] == mock_activity.action_id
            assert kwargs["json_data"]["identifier_grant"] == "0"
            mock_activity_unlock.assert_called_once()

        with patch("weko_workflow.headless.activity.next_action") as mock_next_action, \
                patch("weko_workflow.headless.activity.get_identifier_setting") as mock_identifier, \
                patch("weko_workflow.headless.activity.HeadlessActivity._activity_unlock") as mock_activity_unlock:
            # Test case: failed identifier grant
            mock_next_action.return_value = MagicMock(json={"code": 1, "msg": "error"}), 500
            mock_identifier.return_value = mock_setting

            with pytest.raises(WekoWorkflowException) as ex:
                activity.identifier_grant(grant_data)
            assert ex.value.args[0] == "error"
            _, kwargs = mock_next_action.call_args
            assert kwargs["activity_id"] == mock_activity.activity_id
            assert kwargs["action_id"] == mock_activity.action_id
            assert kwargs["json_data"]["identifier_grant"] == "0"
            mock_activity_unlock.assert_called_once()

        with patch("weko_workflow.headless.activity.next_action") as mock_next_action, \
                patch("weko_workflow.headless.activity.get_identifier_setting") as mock_identifier, \
                patch("weko_workflow.headless.activity.HeadlessActivity._activity_unlock") as mock_activity_unlock:
                # Test case: SQLAlchemyError occurs in next_action
            mock_next_action.side_effect = SQLAlchemyError("Test Error")
            mock_identifier.return_value = mock_setting
            with pytest.raises(WekoWorkflowException) as ex:
                activity.identifier_grant(grant_data)
            assert ex.value.args[0] == "failed in Identifier Grant."
            _, kwargs = mock_next_action.call_args
            assert kwargs["activity_id"] == mock_activity.activity_id
            assert kwargs["action_id"] == mock_activity.action_id
            assert kwargs["json_data"]["identifier_grant"] == "0"
            mock_activity_unlock.assert_called_once()


    # def end(self):
    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test_end -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_end(self, app, db, item_type, workflow, users, client):
        with patch("weko_workflow.views.WorkActivity.get_new_activity_id") as mock_get_new_activity_id:
            mock_get_new_activity_id.side_effect = [f"A-TEST-0000{i}" for i in range(1, 20)]
            activity = HeadlessActivity()
            activity.user = users[0]["obj"]
            activity._recid = "200001"
            activity.workflow = workflow["workflow"]
            activity.item_type = item_type
            activity._model = MagicMock(spec=Activity, activity_id="A-TEST-00001", avtion_id=3, activity_community_id=None)

            activity.end()

            assert activity.user is None
            assert activity.recid is None
            assert activity.workflow is None
            assert activity.item_type is None
            assert activity._model is None
            assert activity.activity_id is None
            assert activity.detail == ""
            assert activity.current_action is None


    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test__activity_lock -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test__activity_lock(self, app, db, workflow):
        # Test case: _lock_skip is True
        activity = HeadlessActivity(_lock_skip=True)
        result = activity._activity_lock()
        assert result is None

        # Test case: _lock_skip is False and lock_activity returns a valid response
        activity._lock_skip = False
        mock_activity = MagicMock(spec=Activity)
        mock_activity.activity_id = "A-TEST-00001"
        activity._model = mock_activity

        with patch("weko_workflow.headless.activity.lock_activity") as mock_lock_activity:
            mock_lock_activity.return_value=jsonify(code=200, locked_value="test_locked_value"), 200
            result = activity._activity_lock()
            assert result == "test_locked_value"
            mock_lock_activity.assert_called_once_with(activity.activity_id)

        # Test case: lock_activity raises an exception
        with patch("weko_workflow.headless.activity.lock_activity") as mock_lock_activity:
            mock_lock_activity.return_value = jsonify(code=-1, msg="Test error"), 500
            with pytest.raises(Exception) as ex:
                activity._activity_lock()
            assert ex.value.args[0] == "Activity is already locked."


    # .tox/c1/bin/pytest --cov=weko_workflow tests/test_activity.py::TestHeadlessActivity::test__activity_unlock -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test__activity_unlock(self, app, db, workflow):
        activity = HeadlessActivity(_lock_skip=True)

        # Test case: _lock_skip is True
        with patch("weko_workflow.headless.activity.delete_lock_activity_cache") as mock_delete_lock:
            result = activity._activity_unlock("test_locked_value")
            assert result is None
            mock_delete_lock.assert_not_called()

            # Test case: _lock_skip is False
            activity._lock_skip = False
            result = activity._activity_unlock("test_locked_value")
            mock_delete_lock.assert_called_once_with(activity.activity_id, {"locked_value": "test_locked_value"})
