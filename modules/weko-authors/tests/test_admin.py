# .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp

from datetime import datetime
from flask import url_for,make_response,json
from mock import patch
import pytest

from invenio_accounts.testutils import login_user_via_session
from invenio_cache import current_cache
from invenio_files_rest.models import FileInstance

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
        mock_send.assert_called_with(
            "Creator_export_all.tsv",
            mimetype="application/octet-stream",
            as_attachment=True
        )


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

        # not task.result
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
        mocker_get_by_uri = mocker.patch("weko_authors.admin.FileInstance.get_by_uri")
        expected_date = datetime.now()
        mocker_get_by_uri.return_value = MockFileInstance(expected_date)
        res = client.get(url)
        expected_filename = "Creator_export_all_" + expected_date.strftime("%Y%m%d%H%M") + ".tsv"
        test = {'code': 200, 'data': {'download_link': '', 'filename': expected_filename, 'key': 'authors_export_status'}}
        assert json.loads(res.data) == test


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
        res =  client.post(url)
        assert_role(res,is_permission)

    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestExportView::test_export -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_export(self,client,users,mocker):
        login_user_via_session(client=client, email=users[0]['email'])
        url = url_for('authors/export.export')
        mocker.patch("weko_authors.admin.set_export_status")
        class MockTask:
            id = "test_id"
        mocker.patch("weko_authors.admin.export_all.delay",return_value=MockTask)
        res = client.post(url)
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
        
        res = client.post(url)
        assert json.loads(res.data) == {"code":200,"data":{"status":"success"}}
        
        # not exist status
        res = client.post(url)
        assert json.loads(res.data) == {"code":200,"data":{"status":"fail"}}
        
        # ranse Exception
        test = {"code": 200, "data": {"status": "fail"}}
        with patch("weko_authors.admin.get_export_status",side_effect=Exception("test_error")):
            res = client.post(url)
            assert json.loads(res.data) == test


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
        assert json.loads(res.data) == {"code":1,"error":None,"list_import_data":[]}
        
        # exist json
        mocker.patch("weko_authors.admin.check_import_data",return_value={"list_import_data":["test_import_data"]})
        res = client.post(url,json={"filename":"test_file.txt","file":"test1,test2"})
        assert json.loads(res.data) == {"code":1,"error":None,"list_import_data":["test_import_data"]}


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
        
        # not is_available
        with patch("weko_authors.admin.check_is_import_available",return_value={"is_available":False}):
            res = client.post(url)
            assert json.loads(res.data) == {"is_available":False}
        
        mocker.patch("weko_authors.admin.check_is_import_available",return_value={"is_available":True})

        class MockTaskGroup:
            def __init__(self):
                self.id = 1
            def save(self):
                pass
            @property
            def children(self):
                return [self.MockTask(id) for id in range(4)]
            
            class MockTask:
                def __init__(self,id):
                    self.task_id = id
        data = {"records":[
            {"pk_id":"test_id0"},{"pk_id":"test_id1"},{"pk_id":"test_id2"},{"pk_id":"test_id3"}
        ]}
        
        mocker.patch("weko_authors.admin.group.apply_async",return_value=MockTaskGroup())
        res = client.post(url,json=data)
        test = {
            "status":"success",
            "data":{
                "group_task_id":1,
                "tasks":[{"task_id":0,"record_id":"test_id0","status":"PENDING"},{"task_id":1,"record_id":"test_id1","status":"PENDING"},{"task_id":2,"record_id":"test_id2","status":"PENDING"},{"task_id":3,"record_id":"test_id3","status":"PENDING"}]
            }
        }
        assert json.loads(res.data) == test

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
        mocker.patch("weko_authors.admin.import_author.AsyncResult",side_effect=lambda x:[task for task in tasks if task.id == x][0])
        
        # not exist data
        data = {}
        res = client.post(url,json=data)
        assert res.status_code == 200
        assert json.loads(res.data) == []
        
        data = {"tasks":[1,2]}
        test = [
            {"task_id":1,"start_date":"2022-10-01 01:02:03","end_date":"2022-10-01 02:03:04","status":"SUCCESS","error_id":"not_error"},
            {"task_id":2,"start_date":"","end_date":"","status":"PENDING","error_id":None}
        ]
        res = client.post(url,json=data)
        assert res.status_code == 200
        assert json.loads(res.data) == test