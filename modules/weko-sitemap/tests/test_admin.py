# .tox/c1/bin/pytest --cov=weko_sitemap tests/test_admin.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp

from flask import url_for
import pytest
from unittest.mock import MagicMock
from mock import patch
from invenio_accounts.testutils import login_user_via_session

# class SitemapSettingView(BaseView):
class TestSitemapSettingView:
    # def index(self):
    # .tox/c1/bin/pytest --cov=weko_sitemap tests/test_admin.py::TestSitemapSettingView::test_index_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp
    def test_index_acl_guest(self,app,client,db_sessionlifetime):
        url = url_for("sitemap.index", _external=True)
        ret = client.get(url)
        assert ret.status_code==302
    
    # .tox/c1/bin/pytest --cov=weko_sitemap tests/test_admin.py::TestSitemapSettingView::test_index_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp
    @pytest.mark.parametrize(
    "id, status_code",
    [
         (0, 403),
         (1, 403),
         (2, 200),
         (3, 200),
         (4, 403),
         (5, 403),
         (6, 403),
         (7, 403),
    ],
    )
    def test_index_acl(self,app,client,users,db_sessionlifetime,id,status_code):
        login_user_via_session(client=client, email=users[id]["email"])
        url = url_for("sitemap.index", _external=True)
        with patch("flask.templating._render", return_value=""):
            ret = client.get(url)
            assert ret.status_code==status_code

    # def update_sitemap(self):
    # .tox/c1/bin/pytest --cov=weko_sitemap tests/test_admin.py::TestSitemapSettingView::test_update_sitemap_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp
    def test_update_sitemap_acl_guest(self,app,client,db_sessionlifetime):
        url = url_for("sitemap.update_sitemap", _external=True)
        ret = client.post(url)
        assert ret.status_code==302
    
    # .tox/c1/bin/pytest --cov=weko_sitemap tests/test_admin.py::TestSitemapSettingView::test_update_sitemap_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp
    @pytest.mark.parametrize(
    "id, status_code",
    [
         (0, 403),
         (1, 403),
         (2, 200),
         (3, 200),
         (4, 403),
         (5, 403),
         (6, 403),
         (7, 403),
    ],
    )       
    def test_update_sitemap_acl(self,app,client,users,db_sessionlifetime,id,status_code):
        login_user_via_session(client=client, email=users[id]["email"])
        url = url_for("sitemap.update_sitemap", _external=True)
        ret = client.post(url)
        assert ret.status_code==status_code
        
    # def get_task_status(self, task_id):
    # .tox/c1/bin/pytest --cov=weko_sitemap tests/test_admin.py::TestSitemapSettingView::test_get_task_status_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp
    def test_get_task_status_acl_guest(self,app,client,db_sessionlifetime):
        url = url_for("sitemap.get_task_status", task_id=1,_external=True)
        ret = client.get(url)
        assert ret.status_code==302
    
    # .tox/c1/bin/pytest --cov=weko_sitemap tests/test_admin.py::TestSitemapSettingView::test_update_sitemap_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp
    @pytest.mark.parametrize(
    "id, status_code",
    [
         (0, 403),
         (1, 403),
         (2, 200),
         (3, 200),
         (4, 403),
         (5, 403),
         (6, 403),
         (7, 403),
    ],
    )       
    def test_update_sitemap_acl(self,app,client,users,db_sessionlifetime,id,status_code):
        login_user_via_session(client=client, email=users[id]["email"])
        url = url_for("sitemap.get_task_status", task_id=1,_external=True)
        ret = client.get(url)
        assert ret.status_code==status_code