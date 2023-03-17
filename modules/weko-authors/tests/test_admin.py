# .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp

from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from mock import patch, MagicMock

import pytest

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
    @pytest.mark.parametrize('users_index, status_code', [
        (0, 403), # contributor
        (1, 200), # repoadmin
        (2, 200), # sysadmin
        (3, 200), # comadmin
        (4, 403), # generaluser
        (5, 403), # originalroleuser
        (6, 200), # originalroleuser2
        (7, 403), # user
        (8, 403), # student  
    ])
    def test_index_acl(self,client,users,users_index,status_code):
        login_user_via_session(client=client, email=users[users_index]['email'])
        url = url_for('authors.index')
        with patch("flask.templating._render", return_value=""):
            res =  client.get(url)
            assert res.status_code == status_code

    # def add(self):
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestAuthorManagementView::test_add_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_add_acl_guest(self,client):
        url = url_for('authors.add')
        res =  client.get(url)
        assert res.status_code == 302

    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestAuthorManagementView::test_add_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    @pytest.mark.parametrize('users_index, status_code', [
        (0, 403), # contributor
        (1, 200), # repoadmin
        (2, 200), # sysadmin
        (3, 200), # comadmin
        (4, 403), # generaluser
        (5, 403), # originalroleuser
        (6, 200), # originalroleuser2
        (7, 403), # user
        (8, 403), # student  
    ])
    def test_add_acl(self,client,users,users_index,status_code):
        login_user_via_session(client=client, email=users[users_index]['email'])
        url = url_for('authors.add')
        with patch("flask.templating._render", return_value=""):
            res =  client.get(url)
            assert res.status_code == status_code

    #  def edit(self):
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestAuthorManagementView::test_edit_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_edit_acl_guest(self,client):
        url = url_for('authors.edit')
        res =  client.get(url)
        assert res.status_code == 302

    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestAuthorManagementView::test_edit_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    @pytest.mark.parametrize('users_index, status_code', [
        (0, 403), # contributor
        (1, 200), # repoadmin
        (2, 200), # sysadmin
        (3, 200), # comadmin
        (4, 403), # generaluser
        (5, 403), # originalroleuser
        (6, 200), # originalroleuser2
        (7, 403), # user
        (8, 403), # student  
    ])
    def test_edit_acl(self,client,users,users_index,status_code):
        login_user_via_session(client=client, email=users[users_index]['email'])
        url = url_for('authors.edit')
        with patch("flask.templating._render", return_value=""):
            res =  client.get(url)
            assert res.status_code == status_code

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
    @pytest.mark.parametrize('users_index, status_code', [
        (0, 403), # contributor
        (1, 200), # repoadmin
        (2, 200), # sysadmin
        (3, 200), # comadmin
        (4, 403), # generaluser
        (5, 403), # originalroleuser
        (6, 200), # originalroleuser2
        (7, 403), # user
        (8, 403), # student  
    ])
    def test_index_acl(self,client,users,users_index,status_code):
        login_user_via_session(client=client, email=users[users_index]['email'])
        url = url_for('authors/export.index')
        with patch("flask.templating._render", return_value=""):
            res =  client.get(url)
            assert res.status_code == status_code
        
    # def download(self):
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestExportView::test_download_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_download_acl_guest(self,client):
        url = url_for('authors/export.download')
        res =  client.get(url)
        assert res.status_code == 302
    
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestExportView::test_download_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    @pytest.mark.parametrize('users_index, status_code', [
        (0, 403), # contributor
        (1, 200), # repoadmin
        (2, 200), # sysadmin
        (3, 200), # comadmin
        (4, 403), # generaluser
        (5, 403), # originalroleuser
        (6, 200), # originalroleuser2
        (7, 403), # user
        (8, 403), # student  
    ])
    def test_download_acl(self,client,users,users_index,status_code):
        login_user_via_session(client=client, email=users[users_index]['email'])
        url = url_for('authors/export.download')
        with patch("flask.templating._render", return_value=""):
            res =  client.get(url)
            assert res.status_code == status_code
            
    # def check_status(self):
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestExportView::test_check_status_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_check_status_acl_guest(self,client):
        url = url_for('authors/export.check_status')
        res =  client.get(url)
        assert res.status_code == 302
    
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestExportView::test_check_status_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    @pytest.mark.parametrize('users_index, status_code', [
        (0, 403), # contributor
        (1, 200), # repoadmin
        (2, 200), # sysadmin
        (3, 200), # comadmin
        (4, 403), # generaluser
        (5, 403), # originalroleuser
        (6, 200), # originalroleuser2
        (7, 403), # user
        (8, 403), # student  
    ])
    def test_check_status_acl(self,client,users,users_index,status_code):
        login_user_via_session(client=client, email=users[users_index]['email'])
        url = url_for('authors/export.check_status')
        with patch("flask.templating._render", return_value=""):
            res =  client.get(url)
            assert res.status_code == status_code
            
    # def export(self):
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestExportView::test_export_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_export_acl_guest(self,client):
        url = url_for('authors/export.export')
        res =  client.get(url)
        assert res.status_code == 302
    
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestExportView::test_export_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    @pytest.mark.parametrize('users_index, status_code', [
        (0, 403), # contributor
        (1, 200), # repoadmin
        (2, 200), # sysadmin
        (3, 200), # comadmin
        (4, 403), # generaluser
        (5, 403), # originalroleuser
        (6, 200), # originalroleuser2
        (7, 403), # user
        (8, 403), # student  
    ])
    def test_export_acl(self,client,users,users_index,status_code):
        login_user_via_session(client=client, email=users[users_index]['email'])
        url = url_for('authors/export.export')
        with patch("flask.templating._render", return_value=""):
            res =  client.get(url)
            assert res.status_code == status_code

    # def cancel(self):
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestExportView::test_cancel_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_cancel_acl_guest(self,client):
        url = url_for('authors/export.cancel')
        res =  client.get(url)
        assert res.status_code == 302
    
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestExportView::test_cancel_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    @pytest.mark.parametrize('users_index, status_code', [
        (0, 403), # contributor
        (1, 200), # repoadmin
        (2, 200), # sysadmin
        (3, 200), # comadmin
        (4, 403), # generaluser
        (5, 403), # originalroleuser
        (6, 200), # originalroleuser2
        (7, 403), # user
        (8, 403), # student  
    ])
    def test_cancel_acl(self,client,users,users_index,status_code):
        login_user_via_session(client=client, email=users[users_index]['email'])
        url = url_for('authors/export.cancel')
        with patch("flask.templating._render", return_value=""):
            res =  client.get(url)
            assert res.status_code == status_code

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
    @pytest.mark.parametrize('users_index, status_code', [
        (0, 403), # contributor
        (1, 200), # repoadmin
        (2, 200), # sysadmin
        (3, 200), # comadmin
        (4, 403), # generaluser
        (5, 403), # originalroleuser
        (6, 200), # originalroleuser2
        (7, 403), # user
        (8, 403), # student  
    ])
    def test_index_acl(self,client,users,users_index,status_code):
        login_user_via_session(client=client, email=users[users_index]['email'])
        url = url_for('authors/import.index')
        with patch("flask.templating._render", return_value=""):
            res =  client.get(url)
            assert res.status_code == status_code
            
    # def is_import_available(self):
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestImportView::test_is_import_available_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_is_import_available_acl_guest(self,client):
        url = url_for('authors/import.is_import_available')
        res =  client.get(url)
        assert res.status_code == 302
    
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestImportView::test_is_import_available_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    @pytest.mark.parametrize('users_index, status_code', [
        (0, 403), # contributor
        (1, 200), # repoadmin
        (2, 200), # sysadmin
        (3, 200), # comadmin
        (4, 403), # generaluser
        (5, 403), # originalroleuser
        (6, 200), # originalroleuser2
        (7, 403), # user
        (8, 403), # student  
    ])
    def test_is_import_available_acl(self,client,users,users_index,status_code):
        login_user_via_session(client=client, email=users[users_index]['email'])
        url = url_for('authors/import.is_import_available')
        with patch("flask.templating._render", return_value=""):
            res =  client.get(url)
            assert res.status_code == status_code

    # def check_import_file(self):
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestImportView::test_check_import_file_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_check_import_file_acl_guest(self,client):
        url = url_for('authors/import.check_import_file')
        res =  client.get(url)
        assert res.status_code == 302
    
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestImportView::test_check_import_file_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    @pytest.mark.parametrize('users_index, status_code', [
        (0, 403), # contributor
        (1, 200), # repoadmin
        (2, 200), # sysadmin
        (3, 200), # comadmin
        (4, 403), # generaluser
        (5, 403), # originalroleuser
        (6, 200), # originalroleuser2
        (7, 403), # user
        (8, 403), # student  
    ])
    def test_check_import_file_acl(self,client,users,users_index,status_code):
        login_user_via_session(client=client, email=users[users_index]['email'])
        url = url_for('authors/import.check_import_file')
        with patch("flask.templating._render", return_value=""):
            res =  client.get(url)
            assert res.status_code == status_code
            
    # def import_authors(self) -> jsonify:
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestImportView::test_import_authors_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_import_authors_acl_guest(self,client):
        url = url_for('authors/import.import_authors')
        res =  client.get(url)
        assert res.status_code == 302
    
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestImportView::test_import_authors_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    @pytest.mark.parametrize('users_index, status_code', [
        (0, 403), # contributor
        (1, 200), # repoadmin
        (2, 200), # sysadmin
        (3, 200), # comadmin
        (4, 403), # generaluser
        (5, 403), # originalroleuser
        (6, 200), # originalroleuser2
        (7, 403), # user
        (8, 403), # student  
    ])
    def test_import_authors_acl(self,client,users,users_index,status_code):
        login_user_via_session(client=client, email=users[users_index]['email'])
        url = url_for('authors/import.import_authors')
        with patch("flask.templating._render", return_value=""):
            res =  client.get(url)
            assert res.status_code == status_code
            
    # def check_import_status(self):
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestImportView::test_check_import_status_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_check_import_status_acl_guest(self,client):
        url = url_for('authors/import.check_import_status')
        res =  client.get(url)
        assert res.status_code == 302
    
    # .tox/c1/bin/pytest --cov=weko_authors tests/test_admin.py::TestImportView::test_check_import_status_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    @pytest.mark.parametrize('users_index, status_code', [
        (0, 403), # contributor
        (1, 200), # repoadmin
        (2, 200), # sysadmin
        (3, 200), # comadmin
        (4, 403), # generaluser
        (5, 403), # originalroleuser
        (6, 200), # originalroleuser2
        (7, 403), # user
        (8, 403), # student  
    ])
    def test_check_import_status_acl(self,client,users,users_index,status_code):
        login_user_via_session(client=client, email=users[users_index]['email'])
        url = url_for('authors/import.check_import_status')
        with patch("flask.templating._render", return_value=""):
            res =  client.get(url)
            assert res.status_code == status_code
