# .tox/c1/bin/pytest --cov=invenio_communities tests/test_admin.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-communities/.tox/c1/tmp

from flask import url_for
import pytest
from mock import patch
from invenio_accounts.testutils import login_user_via_session

from weko_schema_ui.api import WekoSchema


# class OAISchemaSettingView(BaseView):
# .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_admin.py::TestOAISchemaSettingView -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
class TestOAISchemaSettingView():  
    # def list(self):
    # .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_admin.py::TestOAISchemaSettingView::test_list_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
    def test_list_acl_guest(self,app,client,db_sessionlifetime):
        url = url_for('schemasettings.list')
        res = client.get(url)
        assert res.status_code == 302

    # .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_admin.py::TestOAISchemaSettingView::test_list_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
    @pytest.mark.parametrize(
        "id, status_code",
        [
        (0, 403), # contributor
        (1, 403), # repoadmin
        (2, 200), # sysadmin
        (3, 403), # comadmin
        (4, 403), # generaluser
        (5, 403), # original role
        (6, 403), # original role + repoadmin
        (7, 403), # no role
    ],
    )
    def test_list_acl(self,app,client,users,id,status_code):
        url = url_for('schemasettings.list')
        login_user_via_session(client,email=users[id]["email"])
        res = client.get(url)
        assert res.status_code == status_code  
    
    # def add(self):
    # .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_admin.py::TestOAISchemaSettingView::test_add_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
    def test_add_acl_guest(self,app,client,db_sessionlifetime):
        url = url_for('schemasettings.add')
        res = client.get(url)
        assert res.status_code == 302

    # .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_admin.py::TestOAISchemaSettingView::test_add_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
    @pytest.mark.parametrize(
        "id, status_code",
        [
        (0, 403), # contributor
        (1, 403), # repoadmin
        (2, 200), # sysadmin
        (3, 403), # comadmin
        (4, 403), # generaluser
        (5, 403), # original role
        (6, 403), # original role + repoadmin
        (7, 403), # no role
    ],
    )
    def test_add_acl(self,app,client,users,id,status_code):
        url = url_for('schemasettings.add')
        login_user_via_session(client,email=users[id]["email"])
        res = client.get(url)
        assert res.status_code == status_code  
    
    # def delete(self, pid=None):
    # .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_admin.py::TestOAISchemaSettingView::test_delete_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
    def test_delete_acl_guest(self,app,client,db_sessionlifetime):
        url = url_for('schemasettings.delete',pid=None)
        res = client.get(url)
        assert res.status_code == 405
        
        res = client.post(url)
        assert res.status_code == 302

    # .tox/c1/bin/pytest --cov=weko_schema_ui tests/test_admin.py::TestOAISchemaSettingView::test_delete_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-schema-ui/.tox/c1/tmp
    @pytest.mark.parametrize(
        "id, status_code",
        [
        (0, 403), # contributor
        (1, 403), # repoadmin
        (2, 302), # sysadmin
        (3, 403), # comadmin
        (4, 403), # generaluser
        (5, 403), # original role
        (6, 403), # original role + repoadmin
        (7, 403), # no role
    ],
    )
    def test_delete_acl(self, app, client, users, db_oaischema, id, status_code):
        login_user_via_session(client, email=users[id]["email"])
        schema_obj = WekoSchema.get_record_by_name('oai_dc_mapping')
        _id = str(schema_obj.id)

        url = url_for('schemasettings.delete', pid=_id)
        res = client.get(url)
        assert res.status_code == 405
        
        res = client.post(url)
        assert res.status_code == status_code  