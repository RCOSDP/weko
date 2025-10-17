# -*- coding: utf-8 -*-
""" Test admin views."""

import pytest

from flask import url_for,make_response,json
from mock import patch

from invenio_accounts.testutils import login_user_via_session
from weko_logging.utils import UserActivityLogUtils

def assert_role(response,is_permission,status_code=403):
    if is_permission:
        assert response.status_code != status_code
    else:
        assert response.status_code == status_code

# class ExportLogAdminView(BaseView):
# .tox/c1/bin/pytest --cov=weko_logging tests/test_admin.py::TestExportLogAdminView -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
class TestExportLogAdminView():

    # def index(self):
    # .tox/c1/bin/pytest --cov=weko_logging tests/test_admin.py::TestExportLogAdminView::test_index_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
    @pytest.mark.parametrize('users_index, is_permission', [
        (0,True), # sysadmin
        (1,True), # repoadmin
        (2,True), # comadmin
        (3,False), # contributor
        (4,False), # generaluser
        (5, False), # originalroleuser
        (6, True), # originalroleuser2
        (7, False), # user
        (8, False), # student
    ])
    def test_index_acl(self,client,users,users_index,is_permission):
        login_user_via_session(client=client, email=users[users_index]['email'])
        url = url_for("logs/export.index")
        with patch("flask.templating._render", return_value=""):
            res =  client.get(url)
            assert_role(res,is_permission)

    # def index(self):
    # .tox/c1/bin/pytest --cov=weko_logging tests/test_admin.py::TestExportLogAdminView::test_index_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
    def test_index_acl_guest(self, app, db, client):
        url = url_for("logs/export.index")
        res =  client.get(url)
        assert res.status_code == 302

    # def index(self):
    # .tox/c1/bin/pytest --cov=weko_logging tests/test_admin.py::TestExportLogAdminView::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
    def test_index(self, client, users, mocker):
        login_user_via_session(client=client, email=users[0]['email'])
        url = url_for("logs/export.index", _external=True)
        # tab_value = author
        mock_render = mocker.patch("weko_logging.admin.ExportLogAdminView.render",return_value=make_response())
        args = {}
        client.get(url,query_string=args)
        mock_render.assert_called_with(
            "weko_logging/admin/export_log.html",
        )

    # def export_user_activity_log(self):
    # .tox/c1/bin/pytest --cov=weko_logging tests/test_admin.py::TestExportLogAdminView::test_export_user_activity_log_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
    @pytest.mark.parametrize('users_index, is_permission', [
        (0,True), # sysadmin
        (1,True), # repoadmin
        (2,True), # comadmin
        (3,False), # contributor
        (4,False), # generaluser
        (5, False), # originalroleuser
        (6, True), # originalroleuser2
        (7, False), # user
        (8, False), # student
    ])
    def test_export_user_activity_log_acl(self,client,users,users_index,is_permission, redis_connect, mocker):
        class MockTaskDelay:
            def __init__(self, task_id):
                self._id = task_id
            @property
            def id(self):
                return self._id

        login_user_via_session(client=client, email=users[users_index]['email'])
        redis_connect.delete(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_STATUS_KEY)
        url = url_for("logs/export.export_user_activity_log")
        mock_task = mocker.patch("weko_logging.admin.export_all_user_activity_logs.delay")
        mock_task.return_value = MockTaskDelay("test_id")
        res =  client.post(url)
        assert_role(res,is_permission)


    # def export_user_activity_log(self):
    # .tox/c1/bin/pytest --cov=weko_logging tests/test_admin.py::TestExportLogAdminView::test_export_user_activity_log_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
    def test_export_user_activity_log_acl_guest(self, app, db, client, redis_connect):
        redis_connect.delete(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_STATUS_KEY)
        url = url_for("logs/export.export_user_activity_log")
        res = client.post(url)
        assert res.status_code == 302


    # def export_user_activity_log(self):
    # .tox/c1/bin/pytest --cov=weko_logging tests/test_admin.py::TestExportLogAdminView::test_export_user_activity_log -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
    def test_export_user_activity_log(self, client, users, db, redis_connect, mock_async_result_factory, mocker):
        class MockTaskDelay:
            def __init__(self, task_id):
                self._id = task_id
            @property
            def id(self):
                return self._id

        login_user_via_session(client=client, email=users[0]['email'])
        redis_connect.delete(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_STATUS_KEY)
        url = url_for("logs/export.export_user_activity_log")

        # Case 1: Task is None
        mock_task = mocker.patch("weko_logging.admin.export_all_user_activity_logs.delay")
        mock_task.return_value = MockTaskDelay("test_id")
        res = client.post(url)
        assert res.status_code == 200
        assert json.loads(res.data) == {"code":200,"data":{"task_id":"test_id"}}

        # Case 2: Task is already ended
        redis_connect.put(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_STATUS_KEY, bytes(json.dumps({"task_id": "test_id"}), "utf-8"))
        mock_async_result = mocker.patch("weko_logging.admin.export_all_user_activity_logs.AsyncResult")
        task_mock_data = mock_async_result_factory("test_id", "SUCCESS", "result")
        mock_async_result.return_value = task_mock_data
        mock_task = mocker.patch("weko_logging.admin.export_all_user_activity_logs.delay")
        mock_task.return_value = MockTaskDelay("test_id")
        res = client.post(url)
        assert res.status_code == 200
        assert json.loads(res.data) == {"code":200,"data":{"task_id":"test_id"}}

        # Case 3: Task is running
        redis_connect.put(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_STATUS_KEY, bytes(json.dumps({"task_id": "test_id"}), "utf-8"))
        mock_async_result = mocker.patch("weko_logging.admin.export_all_user_activity_logs.AsyncResult")
        running_mock_data = mock_async_result_factory("test_id", "PENDING", "result")
        mock_async_result.return_value = running_mock_data
        res = client.post(url)
        assert res.status_code == 200
        assert json.loads(res.data) == {"code":409,"data":{"message":"Export task is running."}}


    # def check_export_status(self):
    # .tox/c1/bin/pytest --cov=weko_logging tests/test_admin.py::TestExportLogAdminView::test_check_export_status_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
    @pytest.mark.parametrize('users_index, is_permission', [
        (0,True), # sysadmin
        (1,True), # repoadmin
        (2,True), # comadmin
        (3,False), # contributor
        (4,False), # generaluser
        (5, False), # originalroleuser
        (6, True), # originalroleuser2
        (7, False), # user
        (8, False), # student
    ])
    def test_check_export_status_acl(self, client, users, users_index, is_permission, mocker):
        login_user_via_session(client=client, email=users[users_index]['email'])
        url = url_for("logs/export.check_export_status")
        mocker_celery_run = mocker.patch("weko_logging.admin.check_celery_is_run")
        mocker_celery_run.return_value = True
        res =  client.get(url)
        assert_role(res,is_permission)


    # def check_export_status(self):
    # .tox/c1/bin/pytest --cov=weko_logging tests/test_admin.py::TestExportLogAdminView::test_check_export_status_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
    def test_check_export_status_acl_guest(self, app, db, client, mocker):
        url = url_for("logs/export.check_export_status")
        mocker_celery_run = mocker.patch("weko_logging.admin.check_celery_is_run")
        mocker_celery_run.return_value = True
        res =  client.get(url)
        assert res.status_code == 302


    # def check_export_status(self):
    # .tox/c1/bin/pytest --cov=weko_logging tests/test_admin.py::TestExportLogAdminView::test_check_export_status -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
    def test_check_export_status(self, client, users, db, redis_connect, mock_async_result_factory, mocker):
        login_user_via_session(client=client, email=users[0]['email'])
        url = url_for("logs/export.check_export_status")
        expected_is_celey_run = True
        mock_celey_is_run = mocker.patch("weko_logging.admin.check_celery_is_run")
        mock_celey_is_run.return_value = expected_is_celey_run
        redis_connect.delete(UserActivityLogUtils.USER_ACTIVITY_LOG_EXPORT_CACHE_STATUS_KEY)

        # Case 1: export task status is not set
        mock_get_export_task_status = mocker.patch("weko_logging.admin.UserActivityLogUtils.get_export_task_status")
        mock_get_export_task_status.return_value = {}

        res =  client.get(url)
        assert res.status_code == 200
        assert json.loads(res.data) == {"code":200,"data":{"celery_is_run": expected_is_celey_run, "download_link": ""}}

        # patched url
        mock_async_result = mocker.patch("weko_logging.admin.export_all_user_activity_logs.AsyncResult")

        # Case 2: export task status is set (task is running)
        mock_get_export_task_status.return_value = {"task_id": "test_id"}
        running_mock_data = mock_async_result_factory("test_id", "PENDING", "result")
        mock_async_result.return_value = running_mock_data

        res =  client.get(url)
        assert res.status_code == 200
        assert json.loads(res.data) == {"code":200, "data": {"celery_is_run": expected_is_celey_run, "task_id": "test_id", "status": "PENDING", "download_link": ""}}

        # Case 3: export task status is set (task is failed)
        mock_get_export_task_status.return_value = {"task_id": "test_id"}
        failed_mock_data = mock_async_result_factory("test_id", "FAILURE", "result")
        mock_async_result.return_value = failed_mock_data

        res =  client.get(url)
        assert res.status_code == 200
        assert json.loads(res.data) == {"code":200, "data": {"celery_is_run": expected_is_celey_run, "task_id": "test_id", "status": "FAILURE", "error": "export failed", "download_link": ""}}

        # Case 4: export task status is set (task is successful)
        mock_get_export_task_status.return_value = {"task_id": "test_id"}
        success_mock_data = mock_async_result_factory("test_id", "SUCCESS", "result")
        mock_async_result.return_value = success_mock_data
        mock_get_export_url = mocker.patch("weko_logging.admin.UserActivityLogUtils.get_export_url")
        mock_get_export_url.return_value = {"start_time": "2021-01-01T00:00:00", "end_time": "2021-01-01T00:00:00", "file_uri": "test_uri"}

        res =  client.get(url)
        assert res.status_code == 200
        assert json.loads(res.data) == {"code":200, "data": {
            "celery_is_run":expected_is_celey_run, "task_id": "test_id", "status": "SUCCESS",
            "start_time": "2021-01-01T00:00:00", "end_time": "2021-01-01T00:00:00",
            "download_link": "http://test_server/admin/logs/export/download"}}


    # def cancel_export(self):
    # .tox/c1/bin/pytest --cov=weko_logging tests/test_admin.py::TestExportLogAdminView::test_cancel_export_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
    @pytest.mark.parametrize('users_index, is_permission', [
        (0,True), # sysadmin
        (1,True), # repoadmin
        (2,True), # comadmin
        (3,False), # contributor
        (4,False), # generaluser
        (5, False), # originalroleuser
        (6, True), # originalroleuser2
        (7, False), # user
        (8, False), # student
    ])
    def test_cancel_export_acl(self,client,users,users_index,is_permission, mocker):
        login_user_via_session(client=client, email=users[users_index]['email'])
        url = url_for("logs/export.cancel_export")
        mock_task = mocker.patch("weko_logging.admin.UserActivityLogUtils.cancel_export_log")
        mock_task.return_value = True
        res =  client.get(url)
        assert_role(res,is_permission)


    # def cancel_export(self):
    # .tox/c1/bin/pytest --cov=weko_logging tests/test_admin.py::TestExportLogAdminView::test_cancel_export_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
    def test_cancel_export_acl_guest(self, app, db, client, mocker):
        url = url_for("logs/export.cancel_export")
        mock_task = mocker.patch("weko_logging.admin.UserActivityLogUtils.cancel_export_log")
        mock_task.return_value = True
        res =  client.get(url)
        assert res.status_code == 302


    # def cancel_export(self):
    # .tox/c1/bin/pytest --cov=weko_logging tests/test_admin.py::TestExportLogAdminView::test_cancel_export -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
    def test_cancel_export(self, client, users, db, redis_connect, mocker):
        login_user_via_session(client=client, email=users[0]['email'])
        url = url_for("logs/export.cancel_export")
        mock_task = mocker.patch("weko_logging.admin.UserActivityLogUtils.cancel_export_log")
        mock_task.return_value = True
        mock_get_export_task_status = mocker.patch("weko_logging.admin.UserActivityLogUtils.get_export_task_status")
        mock_get_export_task_status.return_value = {"status": "SUCCESS"}
        res =  client.get(url)
        assert res.status_code == 200
        assert json.loads(res.data) == {"data": {"cancel_status": True, "export_status": True, "status": "SUCCESS"}}


    # def download_user_activity_log(self):
    # .tox/c1/bin/pytest --cov=weko_logging tests/test_admin.py::TestExportLogAdminView::test_download_user_activity_log_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
    @pytest.mark.parametrize('users_index, is_permission', [
        (0,True), # sysadmin
        (1,True), # repoadmin
        (2,True), # comadmin
        (3,False), # contributor
        (4,False), # generaluser
        (5, False), # originalroleuser
        (6, True), # originalroleuser2
        (7, False), # user
        (8, False), # student
    ])
    def test_download_user_activity_log_acl(self,client,users,users_index,is_permission, mocker):
        class MockFileInstance:
            def __init__(self):
                self.uri = "test_uri"
            def send_file(self, *args, **kwargs):
                return "send_file"

        login_user_via_session(client=client, email=users[users_index]['email'])
        get_export_url_mock = mocker.patch("weko_logging.utils.UserActivityLogUtils.get_export_url")
        get_export_url_mock.return_value = {"file_uri": "test_uri"}
        get_by_uri_mock = mocker.patch("invenio_files_rest.models.FileInstance.get_by_uri")
        get_by_uri_mock.return_value = MockFileInstance()
        url = url_for("logs/export.download_user_activity_log")
        res =  client.get(url)
        assert_role(res,is_permission)


    # def download_user_activity_log(self):
    # .tox/c1/bin/pytest --cov=weko_logging tests/test_admin.py::TestExportLogAdminView::test_download_user_activity_log_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
    def test_download_user_activity_log_acl_guest(self, app, db, client, mocker):
        class MockFileInstance:
            def __init__(self):
                self.uri = "test_uri"
            def send_file(self, *args, **kwargs):
                return "send_file"

        get_export_url_mock = mocker.patch("weko_logging.utils.UserActivityLogUtils.get_export_url")
        get_export_url_mock.return_value = {"file_uri": "test_uri"}
        get_by_uri_mock = mocker.patch("invenio_files_rest.models.FileInstance.get_by_uri")
        get_by_uri_mock.return_value = MockFileInstance()
        url = url_for("logs/export.download_user_activity_log")
        res =  client.get(url)
        assert res.status_code == 302


    # def download_user_activity_log(self):
    # .tox/c1/bin/pytest --cov=weko_logging tests/test_admin.py::TestExportLogAdminView::test_download_user_activity_log -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-logging/.tox/c1/tmp
    def test_download_user_activity_log(self, client, users, db, redis_connect, mocker):
        class MockFileInstance:
            def __init__(self):
                self.uri = "test_uri"
            def send_file(self, *args, **kwargs):
                return "send_file"

        login_user_via_session(client=client, email=users[0]['email'])
        get_export_url_mock = mocker.patch("weko_logging.utils.UserActivityLogUtils.get_export_url")
        url = url_for("logs/export.download_user_activity_log")

        # Test Case 1: export url set
        get_export_url_mock.return_value = {"file_uri": "test_uri"}
        get_by_uri_mock = mocker.patch("invenio_files_rest.models.FileInstance.get_by_uri")
        get_by_uri_mock.return_value = MockFileInstance()

        res =  client.get(url)
        assert res.status_code == 200

        # Test Case 2: export url not set
        get_export_url_mock.return_value = {}

        res =  client.get(url)
        assert res.status_code == 404
