# .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp

from datetime import datetime
from mock import patch
import pytest
from unittest.mock import MagicMock, mock_open

from flask import current_app, url_for, make_response, json
from invenio_accounts.testutils import login_user_via_session
from invenio_cache import current_cache
from invenio_files_rest.models import FileInstance

from weko_authors.admin import ImportView
from weko_authors.tasks import import_author, import_id_prefix, import_affiliation_id
from weko_workflow.utils import delete_cache_data


def assert_role(response,is_permission,status_code=403):
    if is_permission:
        assert response.status_code != status_code
    else:
        assert response.status_code == status_code
# class AuthorManagementView(BaseView):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestAuthorManagementView -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
class TestAuthorManagementView():
    # def index(self):
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestAuthorManagementView::test_index_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_index_acl_guest(self,client):
        url = url_for('authors.index')
        res =  client.get(url)
        assert res.status_code == 302

    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestAuthorManagementView::test_index_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    @pytest.mark.parametrize('users_index, is_permission', [
        (0,True), # sysadmin
        (1,True), # repoadmin
        (2,True), # comadmin
        (3,False), # contributor
        (4,False), # generaluser
        (5,False), # originalroleuser
        (6,True), # originalroleuser2
        (7,False), # user
        (8,False), # student
    ])
    def test_index_acl(self,client,users,users_index,is_permission):
        login_user_via_session(client=client, email=users[users_index]['email'])
        url = url_for('authors.index')
        with patch("flask.templating._render", return_value=""):
            res =  client.get(url)
            assert_role(res,is_permission)
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestAuthorManagementView::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_index(self,client,users,mocker):
        login_user_via_session(client=client, email=users[0]['email'])
        url = url_for('authors.index')
        # tab_value = author
        mock_render = mocker.patch("weko_authors.admin.AuthorManagementView.render",return_value=make_response())
        args = {}
        res = client.get(url,query_string=args)
        mock_render.assert_called_with(
            "weko_authors/admin/author_list.html",
            render_widgets=False,
            lang_code="en"
        )

        # tab_value = prefix
        mock_render = mocker.patch("weko_authors.admin.AuthorManagementView.render",return_value=make_response())
        args = {"tab":"prefix"}
        res = client.get(url,query_string=args)
        mock_render.assert_called_with(
            "weko_authors/admin/prefix_list.html",
            render_widgets=False,
            lang_code="en"
        )

        # tab_value = affiliation
        mock_render = mocker.patch("weko_authors.admin.AuthorManagementView.render",return_value=make_response())
        args = {"tab":"affiliation"}
        res = client.get(url,query_string=args)
        mock_render.assert_called_with(
            "weko_authors/admin/affiliation_list.html",
            render_widgets=False,
            lang_code="en"
        )


    # def add(self):
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestAuthorManagementView::test_add_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_add_acl_guest(self,client):
        url = url_for('authors.add')
        res =  client.get(url)
        assert res.status_code == 302

    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestAuthorManagementView::test_add_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
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
    def test_add_acl(self,client,users,users_index,is_permission):
        login_user_via_session(client=client, email=users[users_index]['email'])
        url = url_for('authors.add')
        with patch("flask.templating._render", return_value=""):
            res =  client.get(url)
            assert_role(res,is_permission)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestAuthorManagementView::test_add -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_add(self,client,users,mocker):
        login_user_via_session(client=client, email=users[0]['email'])
        url = url_for('authors.add')
        mock_render = mocker.patch("weko_authors.admin.AuthorManagementView.render",return_value=make_response())
        res = client.get(url)
        args, kwargs = mock_render.call_args
        assert args[0] == "weko_authors/admin/author_edit.html"
        assert json.loads(kwargs["identifier_reg"]) == {"ISNI": {"minLength": 0,"maxLength": 30,"reg": "^.*$"},"GRID": {"minLength": 0,"maxLength": 30,"reg": "^.*$"},"Ringgold": {"minLength": 0,"maxLength": 30,"reg": "^.*$"},"kakenhi": {"minLength": 0,"maxLength": 30,"reg": "^.*$"}}
        assert kwargs["render_widgets"] == False
        assert kwargs["lang_code"] == "en"



    #  def edit(self):
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestAuthorManagementView::test_edit_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_edit_acl_guest(self,client):
        url = url_for('authors.edit')
        res =  client.get(url)
        assert res.status_code == 302

    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestAuthorManagementView::test_edit_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
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
    def test_edit_acl(self,client,users,users_index,is_permission):
        login_user_via_session(client=client, email=users[users_index]['email'])
        url = url_for('authors.edit')
        with patch("flask.templating._render", return_value=""):
            res =  client.get(url)
            assert_role(res,is_permission)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestAuthorManagementView::test_edit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_edit(self,client,users,mocker):
        login_user_via_session(client=client, email=users[0]['email'])
        url = url_for('authors.edit')
        mock_render = mocker.patch("weko_authors.admin.AuthorManagementView.render",return_value=make_response())
        res = client.get(url)
        args, kwargs = mock_render.call_args
        assert args[0] == "weko_authors/admin/author_edit.html"
        assert json.loads(kwargs["identifier_reg"]) == {"ISNI": {"minLength": 0,"maxLength": 30,"reg": "^.*$"},"GRID": {"minLength": 0,"maxLength": 30,"reg": "^.*$"},"Ringgold": {"minLength": 0,"maxLength": 30,"reg": "^.*$"},"kakenhi": {"minLength": 0,"maxLength": 30,"reg": "^.*$"}}
        assert kwargs["render_widgets"] == False
        assert kwargs["lang_code"] == "en"



# class ExportView(BaseView):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestExportView -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
class TestExportView():
    #     def index(self):
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestExportView::test_index_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_index_acl_guest(self,client):
        url = url_for('authors/export.index')
        res =  client.get(url)
        assert res.status_code == 302

    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestExportView::test_index_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
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
        url = url_for('authors/export.index')
        with patch("flask.templating._render", return_value=""):
            res =  client.get(url)
            assert_role(res,is_permission)

    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestExportView::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_index(self,client,users,mocker):
        login_user_via_session(client=client, email=users[0]['email'])
        url = url_for('authors/export.index')
        mock_render = mocker.patch("weko_authors.admin.ExportView.render",return_value=make_response())
        res = client.get(url)
        mock_render.assert_called_with("weko_authors/admin/author_export.html")


    # def download(self):
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestExportView::test_download_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_download_acl_guest(self,client):
        url = url_for('authors/export.download')
        res =  client.get(url)
        assert res.status_code == 302

    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestExportView::test_download_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
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
    def test_download_acl(self,client,users,users_index,is_permission,mocker):
        login_user_via_session(client=client, email=users[users_index]['email'])
        url = url_for('authors/export.download')
        mocker.patch("weko_authors.admin.get_export_url", return_value={})
        with patch("flask.templating._render", return_value=""):
            res =  client.get(url)
            assert_role(res,is_permission)

    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestExportView::test_download -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_download(self,client,db,users,mocker):
        login_user_via_session(client=client, email=users[0]['email'])
        url = url_for('authors/export.download')
        file_instance = FileInstance(
            uri="strage/test/test_file.txt",
            storage_class="S",
            size=15,
            checksum="test_checksum",
            readable=True,
            writable=True,
            json={"url":{"url":"https://test.com/test/test_file.txt"}}
        )
        db.session.add(file_instance)
        db.session.commit()

        # not exist file_url
        current_cache.set("weko_authors_exported_url",{})
        res = client.get(url)
        assert res.status_code == 404

        # exist file_url
        current_cache.set("weko_authors_exported_url",{"file_uri":"strage/test/test_file.txt"})
        mock_send = mocker.patch("weko_authors.admin.FileInstance.send_file",return_value=make_response())
        res = client.get(url)
        assert res.status_code == 200
        mock_send.assert_called()


    # def check_status(self):
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestExportView::test_check_status_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_check_status_acl_guest(self,client):
        url = url_for('authors/export.check_status')
        res =  client.get(url)
        assert res.status_code == 302

    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestExportView::test_check_status_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
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
    def test_check_status_acl(self,client,users,users_index,is_permission):
        login_user_via_session(client=client, email=users[users_index]['email'])
        url = url_for('authors/export.check_status')
        res =  client.get(url)
        assert_role(res,is_permission)

    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestExportView::test_check_status -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_check_status(self,client,users,mocker):
        class MockAsyncResult():
            def __init__(self,task_id,state,result):
                self.state = state
                self.result = result
            def successful(self):
                return self.state == "SUCCESS"
            def failed(self):
                return self.state == "FAILURE"

        class MockFileInstance():
            def __init__(self,date):
                self.updated_at = date
            @property
            def updated(self):
                return self.updated_at

        login_user_via_session(client=client, email=users[0]['email'])
        url = url_for('authors/export.check_status')
        current_cache.set("weko_authors_export_status",{"key":"authors_export_status","task_id":"test_task"})
        current_cache.set("weko_authors_exported_url",{"key":"authors_exported_url","file_uri":"test_file.txt"})
        mocker.patch("weko_authors.admin.export_all.AsyncResult",return_value=MockAsyncResult("test_id","SUCCESS","result"))
        res = client.get(url)
        test = {'code': 200, 'data': {'download_link': 'http://app/admin/authors/export/download/Creator_export_all', 'filename': '', 'key': 'authors_exported_url'}}
        assert json.loads(res.data)==test

        # # not task.result
        current_cache.set("weko_authors_export_status",{"key":"authors_export_status","task_id":"test_task"})
        mocker.patch("weko_authors.admin.export_all.AsyncResult",return_value=MockAsyncResult("test_id","SUCCESS",{}))
        res = client.get(url)
        test = {'code': 200, 'data': {'download_link': 'http://app/admin/authors/export/download/Creator_export_all', 'error': 'export_fail', 'filename': '', 'key': 'authors_exported_url'}}
        assert json.loads(res.data)==test

        # not task is success,failed,revoked
        current_cache.set("weko_authors_export_status",{"key":"authors_export_status","task_id":"test_task"})
        current_cache.set("weko_authors_exported_url",{"key":"authors_exported_url","file_uri":"test_file.txt"})
        mocker.patch("weko_authors.admin.export_all.AsyncResult",return_value=MockAsyncResult("test_id","STARTED",{}))
        res = client.get(url)
        test = {'code': 200, 'data': {'download_link': 'http://app/admin/authors/export/download/Creator_export_all', 'filename': '', 'key': 'authors_export_status', "task_id": "test_task"}}
        assert json.loads(res.data) == test

        # not exist get_export_status
        current_cache.delete("weko_authors_export_status")
        current_cache.set("weko_authors_exported_url",{"key":"authors_exported_url","file_uri":"test_file.txt"})
        res = client.get(url)
        test = {'code': 200, 'data': {'download_link': 'http://app/admin/authors/export/download/Creator_export_all', 'filename': '', 'key': 'authors_exported_url'}}
        assert json.loads(res.data) == test

        # exist weko_authors_export_status,not exist weko_authors_export_status[task_id]
        current_cache.set("weko_authors_export_status",{"key":"authors_export_status"})
        res = client.get(url)
        test = {'code': 200, 'data': {'download_link': '', 'filename': '', 'key': 'authors_export_status'}}
        assert json.loads(res.data) == test

        # get file instance
        try:
            with patch("weko_authors.admin.FileInstance.get_by_uri") as mocker_get_by_uri:
                current_cache.set(
                    current_app.config.get("WEKO_AUTHORS_EXPORT_TARGET_CACHE_KEY"),
                    "author_db",
                    timeout=0
                )
                expected_date = datetime.now()
                mocker_get_by_uri.return_value = MockFileInstance(expected_date)
                res = client.get(url)
                expected_filename = "Creator_export_all_" + expected_date.strftime("%Y%m%d%H%M") + ".tsv"
                test = {'code': 200, 'data': {'download_link': '', 'filename': expected_filename, 'key': 'authors_export_status'}}
                assert json.loads(res.data) == test
        finally:
            delete_cache_data(current_app.config.get("WEKO_AUTHORS_EXPORT_TARGET_CACHE_KEY"))

        # not get_export_status
        try:
            current_cache.set("weko_authors_export_stop_point",{"key":"authors_export_stop_point"})
            current_cache.set("weko_authors_export_status", [])
            current_cache.set("weko_authors_exported_url",{"key":"authors_exported_url","file_uri":"test_file.txt"})
            mocker.patch("weko_authors.admin.export_all.AsyncResult",return_value=MockAsyncResult("test_id","SUCCESS","result"))
            res = client.get(url)
            test = {'code': 200, 'data': {'download_link':'http://app/admin/authors/export/download/Creator_export_all','filename':'','key':'authors_exported_url','stop_point':{'key':'authors_export_stop_point'}}}
            assert json.loads(res.data)==test
        finally:
            delete_cache_data("weko_authors_export_stop_point")

        # exsit FileInstance.get_by_uri
        current_cache.set("weko_authors_export_status",{"key":"authors_export_status","task_id":"test_task"})
        current_cache.set("weko_authors_exported_url",{"key":"authors_exported_url","file_uri":"test_file.txt"})
        mocker.patch("weko_authors.admin.export_all.AsyncResult",return_value=MockAsyncResult("test_id","SUCCESS","result"))
        mock_file_instance = MagicMock(spec=FileInstance)
        mock_file_instance.updated = datetime(2020, 8, 28, 8, 28)
        mocker.patch("weko_authors.admin.FileInstance.get_by_uri",return_value=mock_file_instance)
        res = client.get(url)
        test = {'code': 200, 'data': {'download_link': 'http://app/admin/authors/export/download/Creator_export_all', 'filename': '_202008280828.tsv', 'key': 'authors_exported_url'}}
        assert json.loads(res.data)==test


    # def export(self):
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestExportView::test_export_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_export_acl_guest(self,client):
        url = url_for('authors/export.export')
        res =  client.post(url)
        assert res.status_code == 302

    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestExportView::test_export_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
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
    def test_export_acl(self,client,users,users_index,is_permission,mocker):
        class MockTask:
            id = "test_id"
        mocker.patch("weko_authors.admin.export_all.delay",return_valuc=MockTask)
        mocker.patch("weko_authors.admin.set_export_status")
        login_user_via_session(client=client, email=users[users_index]['email'])
        url = url_for('authors/export.export')
        res =  client.post(url, data=json.dumps({"isTarget":None}), content_type='application/json')
        assert_role(res,is_permission)

    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestExportView::test_export -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_export(self,client,users,mocker):
        url = url_for('authors/export.export')
        mocker.patch("weko_authors.admin.set_export_status")
        class MockTask:
            id = "test_id"
        mocker.patch("weko_authors.admin.export_all.delay",return_value=MockTask)
        login_user_via_session(client=client, email=users[0]['email'])
        data = {"isTarget":None}
        res = client.post(url, data=json.dumps(data), content_type='application/json')
        assert json.loads(res.data) == {"code":200,"data":{"task_id":"test_id"}}
        data = {"isTarget":"author_db"}
        res = client.post(url, data=json.dumps(data), content_type='application/json')
        assert json.loads(res.data) == {"code":200,"data":{"task_id":"test_id"}}

    # def cancel(self):
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestExportView::test_cancel_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_cancel_acl_guest(self,client):
        url = url_for('authors/export.cancel')
        res =  client.post(url)
        assert res.status_code == 302

    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestExportView::test_cancel_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
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
    def test_cancel_acl(self,client,users,users_index,is_permission):
        login_user_via_session(client=client, email=users[users_index]['email'])
        url = url_for('authors/export.cancel')
        res =  client.post(url)
        assert_role(res,is_permission)

    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestExportView::test_cancel -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_cancel(self,client,users,mocker):
        login_user_via_session(client=client, email=users[0]['email'])
        url = url_for('authors/export.cancel')
        mocker.patch("weko_authors.admin.revoke")
        current_cache.set("weko_authors_export_status",{"key":"authors_export_status","task_id":"test_task"})
        current_cache.set("weko_authors_export_stop_point",{"key":"authors_export_stop_point"})
        current_cache.set("weko_authors_export_temp_file_path_key",{"key":"authors_export_temp_file_path_key"})
        mocker.patch("os.remove")
        res = client.post(url)
        assert json.loads(res.data) == {"code":200,"data":{"status":"success"}}

        # not temp_file_path
        current_cache.set("weko_authors_export_status",None)
        current_cache.set("weko_authors_export_stop_point",{"key":"authors_export_stop_point"})
        res = client.post(url)
        assert json.loads(res.data) == {"code":200,"data":{"status":"fail"}}

        # not exist status
        res = client.post(url)
        assert json.loads(res.data) == {"code":200,"data":{"status":"fail"}}

        # ranse Exception
        test = {"code": 200, "data": {"status": "fail"}}
        with patch("weko_authors.admin.get_export_status",side_effect=Exception("test_error")):
            res = client.post(url)
            assert json.loads(res.data) == test

    # def resume(self):
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestExportView::test_resume -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_resume(self,client,users,mocker):
        url = url_for('authors/export.resume')
        mocker.patch("weko_authors.admin.set_export_status")
        class MockTask:
            id = "test_id"
        mocker.patch("weko_authors.admin.export_all.delay",return_value=MockTask)
        login_user_via_session(client=client, email=users[0]['email'])
        res = client.post(url)
        assert json.loads(res.data) == {"code":200,"data":{"task_id":"test_id"}}


# class ImportView(BaseView):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestImportView -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
class TestImportView():
    #  def index(self):
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestImportView::test_index_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_index_acl_guest(self,client):
        url = url_for('authors/import.index')
        res =  client.get(url)
        assert res.status_code == 302

    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestImportView::test_index_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
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
        url = url_for('authors/import.index')
        with patch("flask.templating._render", return_value=""):
            res =  client.get(url)
            assert_role(res,is_permission)

    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestImportView::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_index(self,client,users,mocker):
        login_user_via_session(client=client, email=users[0]['email'])
        url = url_for('authors/import.index')
        mock_render = mocker.patch("weko_authors.admin.ImportView.render",return_value=make_response())

        res = client.get(url)
        assert res.status_code == 200
        mock_render.assert_called_with("weko_authors/admin/author_import.html")


    # def is_import_available(self):
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestImportView::test_is_import_available_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_is_import_available_acl_guest(self,client):
        url = url_for('authors/import.is_import_available')
        res =  client.get(url)
        assert res.status_code == 302

    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestImportView::test_is_import_available_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
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
    def test_is_import_available_acl(self,client,users,users_index,is_permission,mocker):
        login_user_via_session(client=client, email=users[users_index]['email'])
        url = url_for('authors/import.is_import_available')
        mocker.patch("weko_authors.admin.check_is_import_available",return_value={"result":"success"})
        res =  client.get(url)
        assert_role(res,is_permission)

    def test_is_import_available(self,client,users,mocker):
        login_user_via_session(client=client, email=users[0]['email'])
        url = url_for('authors/import.is_import_available')
        mocker.patch("weko_authors.admin.check_is_import_available",return_value={"result":"success"})
        res =  client.get(url)
        assert json.loads(res.data) == {"result":"success"}


    # def check_import_file(self):
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestImportView::test_check_import_file_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_check_import_file_acl_guest(self,client):
        url = url_for('authors/import.check_import_file')
        res =  client.post(url)
        assert res.status_code == 302

    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestImportView::test_check_import_file_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
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
    def test_check_import_file_acl(self,client,users,users_index,is_permission):
        login_user_via_session(client=client, email=users[users_index]['email'])
        url = url_for('authors/import.check_import_file')
        res =  client.post(url)
        assert_role(res,is_permission)

    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestImportView::test_check_import_file -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_check_import_file(self,client,users,mocker):
        login_user_via_session(client=client, email=users[0]['email'])
        url = url_for('authors/import.check_import_file')

        # not exist json
        res =  client.post(url,json={})
        assert json.loads(res.data) == {"code":1,"error":None,"list_import_data":[],"counts":0,"max_page":1}

        # target == "id_prefix"
        mocker.patch("weko_authors.admin.check_import_data_for_prefix",return_value={"list_import_data":["test_import_data"]})
        res = client.post(url,json={"file_name":"test_file.txt","file":"test1,test2","target":"id_prefix"})
        assert json.loads(res.data) == {"code":1,"error":None,"list_import_data":["test_import_data"],"counts":0,"max_page":1}

        # target == "author_db"
        mocker.patch("weko_authors.admin.check_import_data_for_prefix",return_value={"list_import_data":["test_import_data"]})
        mocker.patch("weko_authors.admin.check_import_data", return_value={"error":"Internal server error"})
        current_cache.set("authors_import_band_check_user_file_path",{"key":"authors_import_band_check_user_file_path"})
        mocker.patch("os.remove")
        res = client.post(url,json={"file_name":"test_file.txt","file":"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKAQMAAAC3/F3+AAAAA3NCSVQICAjb4U/gAAAABlBMVEUjHyD///9mY0coAAAACXBIWXMAAAsSAAALEgHS3X78AAAAFnRFWHRDcmVhdGlvbiBUaW1lADAzLzIzLzEysFVRHgAAABx0RVh0U29mdHdhcmUAQWRvYmUgRmlyZXdvcmtzIENTNXG14zYAAAAWSURBVAiZY/h/gAGIPoPRATCCsMHiAPy6EMmRpJhhAAAAAElFTkSuQmCC","target":"author_db"})
        assert json.loads(res.data) == {"code":1,"error":"Internal server error","list_import_data":None,"counts":None,"max_page":None}

        # not band_file_path
        mocker.patch("weko_authors.admin.check_import_data_for_prefix",return_value={"list_import_data":["test_import_data"]})
        mocker.patch("weko_authors.admin.check_import_data", return_value={"error":"Internal server error"})
        res = client.post(url,json={"file_name":"test_file.txt","file":"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKAQMAAAC3/F3+AAAAA3NCSVQICAjb4U/gAAAABlBMVEUjHyD///9mY0coAAAACXBIWXMAAAsSAAALEgHS3X78AAAAFnRFWHRDcmVhdGlvbiBUaW1lADAzLzIzLzEysFVRHgAAABx0RVh0U29mdHdhcmUAQWRvYmUgRmlyZXdvcmtzIENTNXG14zYAAAAWSURBVAiZY/h/gAGIPoPRATCCsMHiAPy6EMmRpJhhAAAAAElFTkSuQmCC","target":"author_db"})
        assert json.loads(res.data) == {"code":1,"error":"Internal server error","list_import_data":None,"counts":None,"max_page":None}

        # target == "dummy"
        mocker.patch("weko_authors.admin.check_import_data_for_prefix",return_value={"list_import_data":["test_import_data"]})
        res = client.post(url,json={"file_name":"test_file.txt","file":"test1,test2","target":"dummy"})
        assert json.loads(res.data) == {"code":1,"error":None,"list_import_data":[],"counts":0,"max_page":1}

        # Exception
        mock_logger = MagicMock()
        current_app.logger = mock_logger
        mocker.patch("weko_authors.admin.check_import_data_for_prefix",return_value={"list_import_data":["test_import_data"]})
        mocker.patch("weko_authors.admin.check_import_data", return_value={"error":"Internal server error"})
        current_cache.set("authors_import_band_check_user_file_path",{"key":"authors_import_band_check_user_file_path"})
        mocker.patch("os.remove", side_effect=FileNotFoundError)
        res = client.post(url,json={"file_name":"test_file.txt","file":"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKAQMAAAC3/F3+AAAAA3NCSVQICAjb4U/gAAAABlBMVEUjHyD///9mY0coAAAACXBIWXMAAAsSAAALEgHS3X78AAAAFnRFWHRDcmVhdGlvbiBUaW1lADAzLzIzLzEysFVRHgAAABx0RVh0U29mdHdhcmUAQWRvYmUgRmlyZXdvcmtzIENTNXG14zYAAAAWSURBVAiZY/h/gAGIPoPRATCCsMHiAPy6EMmRpJhhAAAAAElFTkSuQmCC","target":"author_db"})
        mock_logger.error.assert_called_once_with("Error deleting {'key': 'authors_import_band_check_user_file_path'}: ")

    # def import_authors(self) -> jsonify:
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestImportView::test_import_authors_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_import_authors_acl_guest(self,client):
        url = url_for('authors/import.import_authors')
        res =  client.post(url)
        assert res.status_code == 302

    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestImportView::test_import_authors_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
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
    def test_import_authors_acl(self,client,users,users_index,is_permission,mocker):
        mocker.patch("weko_authors.admin.check_is_import_available",return_value={"is_available":False})
        login_user_via_session(client=client, email=users[users_index]['email'])
        url = url_for('authors/import.import_authors')
        res =  client.post(url)
        assert_role(res,is_permission)
# .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestImportView::test_import_authors -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_import_authors(self,client,users,mocker):
        login_user_via_session(client=client, email=users[0]['email'])
        url = url_for('authors/import.import_authors')
        class MockTaskGroup:
            def __init__(self):
                self.id = 1
            def save(self):
                pass
            @property
            def children(self):
                return [self.MockTask(id) for id in range(2)]

            class MockTask:
                def __init__(self,id):
                    self.task_id = id

        # not is_available
        mocker.patch("weko_authors.admin.check_is_import_available",return_value={"is_available":False})
        res = client.post(url)
        assert json.loads(res.data) == {"is_available":False}

        # is_target == "id_prefix"
        data = {
            "isTarget": "id_prefix",
            "max_page": 1,
            "records": [
                {"pk_id": "test_id0", "scheme": "WEKO", "name": "name0"},
                {"pk_id": "test_id1", "scheme": "GRID", "name": "name1"},
            ],
        }
        mocker.patch("weko_authors.admin.check_is_import_available",return_value={"is_available":True})
        mocker.patch("weko_authors.admin.group.apply_async",return_value=MockTaskGroup())
        res = client.post(url, data=json.dumps(data), content_type='application/json')
        test = {
            "status": "success",
            "count": 0,
            "data": {
                "group_task_id": 1,
                "tasks": [
                    {"task_id": 0, "scheme": "WEKO", "name": "name0", "status": "PENDING"},
                    {"task_id": 1, "scheme": "GRID", "name": "name1", "status": "PENDING"},
                ],
            },
            "records": [
                {"pk_id": "test_id0", "scheme": "WEKO", "name": "name0"},
                {"pk_id": "test_id1", "scheme": "GRID", "name": "name1"},
            ],
        }
        assert json.loads(res.data) == test

        # is_target == "affiliation_id"
        data = {
            "isTarget": "affiliation_id",
            "max_page": 1,
            "records": [
                {"pk_id": "test_id0", "scheme": "WEKO", "name": "name0"},
                {"pk_id": "test_id1", "scheme": "GRID", "name": "name1"},
            ],
        }
        mocker.patch("weko_authors.admin.check_is_import_available",return_value={"is_available":True})
        mocker.patch("weko_authors.admin.group.apply_async",return_value=MockTaskGroup())
        res = client.post(url, data=json.dumps(data), content_type='application/json')
        test = {
            "status": "success",
            "count": 0,
            "data": {
                "group_task_id": 1,
                "tasks": [
                    {"task_id": 0, "scheme": "WEKO", "name": "name0", "status": "PENDING"},
                    {"task_id": 1, "scheme": "GRID", "name": "name1", "status": "PENDING"},
                ],
            },
            "records": [
                {"pk_id": "test_id0", "scheme": "WEKO", "name": "name0"},
                {"pk_id": "test_id1", "scheme": "GRID", "name": "name1"},
            ],
        }
        assert json.loads(res.data) == test

        # is_target == "author_db"
        data = {
            "isTarget": "author_db",
            "max_page": 1,
            "records": [
                {"pk_id": "test_id0", "scheme": "WEKO", "name": "name0"},
                {"pk_id": "test_id1", "scheme": "GRID", "name": "name1"},
            ],
        }
        mocker.patch("weko_authors.admin.check_is_import_available",return_value={"is_available":True})
        current_cache.set(current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_OVER_MAX_FILE_PATH_KEY"],
                          {"key":"cache_result_over_max_file_path_key"})
        mocker.patch("os.remove")
        current_cache.set(current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_FILE_PATH_KEY"],
                          {"key":"authors_import_result_file_path"})
        current_cache.set(current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_SUMMARY_KEY"],
                          {"key":"result_summary_key"})
        mocker.patch("weko_authors.admin.prepare_import_data",return_value=([
                {"pk_id": "test_id0", "current_weko_id": "1000", "weko_id": "1000"},
                {"pk_id": "test_id1", "current_weko_id": "1001", "weko_id": "1001"},
            ], 1, 1))
        mocker.patch("weko_authors.admin.group.apply_async",return_value=MockTaskGroup())
        res = client.post(url, data=json.dumps(data), content_type='application/json')
        test = {
            "status": "success",
            "count": 1,
            "data": {
                "group_task_id": 1,
                "tasks": [
                    {
                        "task_id": 0,
                        "record_id": "test_id0",
                        "previous_weko_id": "1000",
                        "new_weko_id": "1000",
                        "status": "PENDING",
                    },
                    {
                        "task_id": 1,
                        "record_id": "test_id1",
                        "previous_weko_id": "1001",
                        "new_weko_id": "1001",
                        "status": "PENDING",
                    },
                ],
            },
            "records": [
                {"pk_id": "test_id0", "current_weko_id": "1000", "weko_id": "1000"},
                {"pk_id": "test_id1", "current_weko_id": "1001", "weko_id": "1001"},
            ],
        }
        assert json.loads(res.data) == test

        # is_target == "dummy"
        data = {
            "isTarget": "dummy",
            "max_page": 1,
            "records": [
                {"pk_id": "test_id0", "scheme": "WEKO", "name": "name0"},
                {"pk_id": "test_id1", "scheme": "GRID", "name": "name1"},
            ],
        }
        mocker.patch("weko_authors.admin.check_is_import_available",return_value={"is_available":True})
        res = client.post(url, data=json.dumps(data), content_type='application/json')
        assert res.status_code == 200
        assert json.loads(res.data) == {'status': 'fail', 'message': 'Invalid target'}

        # result_over_max_file_path, result_file_path, result_summary is None and count > current_app.config.get is true
        data = {
            "isTarget": "author_db",
            "max_page": 1,
            "records": [
                {"pk_id": "test_id0", "scheme": "WEKO", "name": "name0"},
                {"pk_id": "test_id1", "scheme": "GRID", "name": "name1"},
            ],
        }
        mocker.patch("weko_authors.admin.check_is_import_available",return_value={"is_available":True})
        current_cache.set(current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_OVER_MAX_FILE_PATH_KEY"],None)
        current_cache.set(current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_FILE_PATH_KEY"], None)
        current_cache.set(current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_SUMMARY_KEY"],None)
        mocker.patch("weko_authors.admin.prepare_import_data",return_value=([
                {"pk_id": "test_id0", "current_weko_id": "1000", "weko_id": "1000"},
                {"pk_id": "test_id1", "current_weko_id": "1001", "weko_id": "1001"},
            ], 1, 2000))
        mocker.patch("weko_authors.admin.group.apply_async",return_value=MockTaskGroup())
        mock_task = MagicMock()
        mock_task.id = 'mocked_task_id'
        mocker.patch("weko_authors.admin.import_author_over_max.delay",return_value=mock_task)
        mocker.patch("weko_authors.admin.update_cache_data",return_value=None)
        res = client.post(url, data=json.dumps(data), content_type='application/json')
        test = {
            "status": "success",
            "count": 2000,
            "data": {
                "group_task_id": 1,
                "tasks": [
                    {
                        "task_id": 0,
                        "record_id": "test_id0",
                        "previous_weko_id": "1000",
                        "new_weko_id": "1000",
                        "status": "PENDING",
                    },
                    {
                        "task_id": 1,
                        "record_id": "test_id1",
                        "previous_weko_id": "1001",
                        "new_weko_id": "1001",
                        "status": "PENDING",
                    },
                ],
            },
            "records": [
                {"pk_id": "test_id0", "current_weko_id": "1000", "weko_id": "1000"},
                {"pk_id": "test_id1", "current_weko_id": "1001", "weko_id": "1001"},
            ],
        }
        assert json.loads(res.data) == test

        #  Exception (result_over_max_file_path is true)
        data = {
            "isTarget": "author_db",
            "max_page": 1,
            "records": [
                {"pk_id": "test_id0", "scheme": "WEKO", "name": "name0"},
                {"pk_id": "test_id1", "scheme": "GRID", "name": "name1"},
            ],
        }
        mock_logger_error = MagicMock()
        current_app.logger.error = mock_logger_error
        mocker.patch("weko_authors.admin.check_is_import_available",return_value={"is_available":True})
        current_cache.set(current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_OVER_MAX_FILE_PATH_KEY"],
                          {"key": "cache_result_over_max_file_path_key"})
        mocker.patch("os.remove", side_effect=FileNotFoundError)
        client.post(url, data=json.dumps(data), content_type='application/json')
        mock_logger_error.assert_called_once_with("Error deleting {'key': 'cache_result_over_max_file_path_key'}: ")

        #  Exception (result_file_path is true)
        data = {
            "isTarget": "author_db",
            "max_page": 1,
            "records": [
                {"pk_id": "test_id0", "scheme": "WEKO", "name": "name0"},
                {"pk_id": "test_id1", "scheme": "GRID", "name": "name1"},
            ],
        }
        mock_logger_error = MagicMock()
        current_app.logger.error = mock_logger_error
        mocker.patch("weko_authors.admin.check_is_import_available",return_value={"is_available":True})
        current_cache.set(current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_FILE_PATH_KEY"],
                {"key": "authors_import_result_file_path"})
        mocker.patch("os.remove", side_effect=FileNotFoundError)
        client.post(url, data=json.dumps(data), content_type='application/json')
        mock_logger_error.assert_called_once_with("Error deleting {'key': 'authors_import_result_file_path'}: ")

    # def check_import_status(self):
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestImportView::test_check_import_status_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_check_import_status_acl_guest(self,client):
        url = url_for('authors/import.check_import_status')
        res =  client.post(url)
        assert res.status_code == 302

    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestImportView::test_check_import_status_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
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
    def test_check_import_status_acl(self,client,users,users_index,is_permission):
        login_user_via_session(client=client, email=users[users_index]['email'])
        url = url_for('authors/import.check_import_status')
        res =  client.post(url)
        assert_role(res,is_permission)
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestImportView::test_check_import_status -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_check_import_status(self,client,users,mocker):
        login_user_via_session(client=client, email=users[0]['email'])
        url = url_for('authors/import.check_import_status')

        class MockAsyncResult:
            def __init__(self,id,start,end,status,error):
                self.id = id
                result = {}
                if start:
                    result["start_date"] = start
                if end:
                    result["end_date"] = end
                if status:
                    result["status"] = status
                    result["error_id"] = error
                self.result = result
        tasks = list()
        tasks.append(MockAsyncResult(1,"2022-10-01 01:02:03","2022-10-01 02:03:04","SUCCESS","not_error"))
        tasks.append(MockAsyncResult(2,None,None,None,None))
        mocker.patch("weko_authors.admin.ImportView.get_task",side_effect=lambda target, task_id:[task for task in tasks if task.id == task_id][0])

        # not exist data
        data = {}
        res = client.post(url,json=data)
        assert res.status_code == 200
        assert json.loads(res.data) == []

        # isTarget == "dummy"
        data = {"isTarget": "dummy"}
        res = client.post(url,json=data)
        assert res.status_code == 200
        assert json.loads(res.data) == []

        # isTarget == "author_db"
        data = {"isTarget": "author_db", "tasks": [1, 2]}
        test = {
            "over_max": {
                "error_id": "not_error",
                "status": "SUCCESS",
                "task_id": {"key": "authors_import_over_max_task"},
            },
            "summary": {"failure_count": 5, "success_count": 6},
            "tasks": [
                {
                    "task_id": 1,
                    "start_date": "2022-10-01 01:02:03",
                    "end_date": "2022-10-01 02:03:04",
                    "status": "SUCCESS",
                    "error_id": "not_error",
                },
                {
                    "task_id": 2,
                    "start_date": "",
                    "end_date": "",
                    "status": "PENDING",
                    "error_id": None,
                },
            ],
        }
        current_cache.set("authors_import_over_max_task",{"key":"authors_import_over_max_task"})
        current_cache.set("result_summary_key",{"success_count":5,"failure_count":5})
        mocker.patch("weko_authors.admin.import_author_over_max.AsyncResult",side_effect=lambda x:[task for task in tasks][0])
        res = client.post(url,json=data)
        assert res.status_code == 200
        assert json.loads(res.data) == test

        # isTarget == "id_prefix"
        data = {"isTarget": "id_prefix", "tasks": [1,2]}
        test = [
            {
                "task_id": 1,
                "start_date": "2022-10-01 01:02:03",
                "end_date": "2022-10-01 02:03:04",
                "status": "FAILURE",
                "error_id": "error_id",
            },
            {
                "task_id": 2,
                "start_date": "",
                "end_date": "",
                "status": "RUNNING",
                "error_id": "not_error",
            },
        ]
        failure_tasks = list()
        failure_tasks.append(MockAsyncResult(1,"2022-10-01 01:02:03","2022-10-01 02:03:04","FAILURE","error_id"))
        failure_tasks.append(MockAsyncResult(2,None,None,"RUNNING","not_error"))
        mocker.patch("weko_authors.admin.ImportView.get_task",side_effect=lambda target, task_id:[task for task in failure_tasks if task.id == task_id][0])
        res = client.post(url,json=data)
        assert res.status_code == 200
        assert json.loads(res.data) == test

        # over_max_task, summary is None
        data = {"isTarget": "author_db", "tasks": [1, 2]}
        test = {
            "summary": {"failure_count": 0, "success_count": 1},
            "tasks": [
                {
                    "task_id": 1,
                    "start_date": "2022-10-01 01:02:03",
                    "end_date": "2022-10-01 02:03:04",
                    "status": "SUCCESS",
                    "error_id": "not_error",
                },
                {
                    "task_id": 2,
                    "start_date": "",
                    "end_date": "",
                    "status": "PENDING",
                    "error_id": None,
                },
            ],
        }
        mocker.patch("weko_authors.admin.ImportView.get_task",side_effect=lambda target, task_id:[task for task in tasks if task.id == task_id][0])
        current_cache.set("authors_import_over_max_task",None)
        current_cache.set("result_summary_key",None)
        res = client.post(url,json=data)
        assert res.status_code == 200
        assert json.loads(res.data) == test

        # if task.result and task.result.get('status') is false
        data = {"isTarget": "author_db", "tasks": [1, 2]}
        test = {
            "over_max": {
                "error_id": None,
                "status": "PENDING",
                "task_id": {"key": "authors_import_over_max_task"},
            },
            "summary": {"failure_count": 5, "success_count": 6},
            "tasks": [
                {
                    "task_id": 1,
                    "start_date": "2022-10-01 01:02:03",
                    "end_date": "2022-10-01 02:03:04",
                    "status": "SUCCESS",
                    "error_id": "not_error",
                },
                {
                    "task_id": 2,
                    "start_date": "",
                    "end_date": "",
                    "status": "PENDING",
                    "error_id": None,
                },
            ],
        }
        current_cache.set("authors_import_over_max_task",{"key":"authors_import_over_max_task"})
        current_cache.set("result_summary_key",{"success_count":5,"failure_count":5})
        mocker.patch("weko_authors.admin.import_author_over_max.AsyncResult",side_effect=lambda x:[task for task in tasks][1])
        res = client.post(url,json=data)
        assert res.status_code == 200
        assert json.loads(res.data) == test

    # def check_pagination(self):
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestImportView::test_check_pagination -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_check_pagination(self,client,users):
        login_user_via_session(client=client, email=users[0]['email'])
        url = url_for('authors/import.check_pagination')
        args = {"page_number":1}
        mock_data = {"key": "value"}
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_data))) as mock_file, \
            patch("json.load", return_value=mock_data) as mock_json:
            with open("somefile.json", "r", encoding="utf-8-sig") as check_part_file:
                res = client.get(url,query_string=args)
                assert res.status_code == 200
                assert json.loads(res.data) == mock_data

    # def check_file_download(self):
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestImportView::test_check_file_download -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_check_file_download(self,client,users,mocker):
        current_cache.delete("authors_import_band_check_user_file_path")
        login_user_via_session(client=client, email=users[0]['email'])
        url = url_for('authors/import.check_file_download')
        data = {"max_page":1}
        mocker.patch("weko_authors.admin.band_check_file_for_user",return_value="test_file_path")
        mock_send = mocker.patch("weko_authors.admin.send_file",return_value=make_response())
        client.post(url, data=json.dumps(data), content_type='application/json')
        mock_send.assert_called_with(
            "test_file_path",
            as_attachment=True
        )
        mocker.patch("weko_authors.admin.band_check_file_for_user",return_value="test_file_path")
        mock_send_file = mocker.patch("weko_authors.admin.send_file", side_effect=Exception("File not found"))
        current_cache.set("authors_import_band_check_user_file_path",{"key":"authors_import_band_check_user_file_path"})
        res = client.post(url, data=json.dumps(data), content_type='application/json')
        mock_send_file.assert_called_once()
        assert res.status_code == 500
        assert json.loads(res.data) == {"msg":"Failed"}

    # def get_task(self, target, task_id):
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestImportView::test_get_task -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_get_task(self,client,users,mocker):
        def mock_async_result():
            mock_result = MagicMock()
            mock_result.status = 'SUCCESS'
            return mock_result

        view = ImportView()
        import_id_prefix.AsyncResult = MagicMock(return_value=mock_async_result)
        import_affiliation_id.AsyncResult = MagicMock(return_value=mock_async_result)
        import_author.AsyncResult = MagicMock(return_value=mock_async_result)

        task = view.get_task('id_prefix', 100)
        assert task == mock_async_result
        import_id_prefix.AsyncResult.assert_called_once_with(100)
        task = view.get_task('affiliation_id', 200)
        assert task == mock_async_result
        import_affiliation_id.AsyncResult.assert_called_once_with(200)
        task = view.get_task('author_db', 300)
        assert task == mock_async_result
        import_author.AsyncResult.assert_called_once_with(300)
        task = view.get_task('invalid_target', 100)
        assert task is None

    # result_file_download(self):
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestImportView::test_result_file_download -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_result_file_download(self,client,users,mocker):
        login_user_via_session(client=client, email=users[0]['email'])
        url = url_for('authors/import.result_file_download')
        data = {"max_page":1}

        current_cache.set("authors_import_result_file_path",{"key":"authors_import_result_file_path"})
        mock_send = mocker.patch("weko_authors.admin.send_file",return_value=make_response())
        client.post(url, data=json.dumps(data), content_type='application/json')
        mock_send.assert_called_with(
            {"key":"authors_import_result_file_path"},
            as_attachment=True
        )
        current_cache.delete("authors_import_result_file_path")
        mocker.patch("weko_authors.admin.create_result_file_for_user",return_value="test_file_path")
        mock_send = mocker.patch("weko_authors.admin.send_file",return_value=make_response())
        client.post(url, data=json.dumps(data), content_type='application/json')
        mock_send.assert_called_with(
            "test_file_path",
            as_attachment=True
        )
        mocker.patch("weko_authors.admin.create_result_file_for_user",return_value=None)
        res = client.post(url, data=json.dumps(data), content_type='application/json')
        assert res.status_code == 200
        assert json.loads(res.data) == {"Result": "Dont need to create result file"}

        mocker.patch("weko_authors.admin.create_result_file_for_user",return_value="test_file_path")
        mock_send_file = mocker.patch("weko_authors.admin.send_file", side_effect=Exception("File not found"))
        res = client.post(url, data=json.dumps(data), content_type='application/json')
        mock_send_file.assert_called_once()
        assert res.status_code == 500
        assert json.loads(res.data) == {"msg":"Failed"}
