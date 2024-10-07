# .tox/c1/bin/pytest --cov=weko_sitemap tests/test_admin.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp

from flask import url_for,json
import pytest
from mock import patch
from invenio_accounts.testutils import login_user_via_session

# .tox/c1/bin/pytest --cov=weko_sitemap tests/test_admin.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp

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
    "id, is_admin",
    [
         (0, False),
         (1, False),
         (2, True),
         (3, True),
         (4, False),
         (5, False),
         (6, False),
         (7, False),
    ],
    )
    def test_index_acl(self,app,client,users,db_sessionlifetime,id,is_admin):
        login_user_via_session(client=client, email=users[id]["email"])
        url = url_for("sitemap.index", _external=True)
        with patch("flask.templating._render", return_value=""):
            ret = client.get(url)
            if is_admin:
                assert ret.status_code != 403
            else:
                assert ret.status_code == 403

    # def update_sitemap(self):
    # .tox/c1/bin/pytest --cov=weko_sitemap tests/test_admin.py::TestSitemapSettingView::test_update_sitemap_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp
    def test_update_sitemap_acl_guest(self,app,client,db_sessionlifetime):
        url = url_for("sitemap.update_sitemap", _external=True)
        ret = client.post(url)
        assert ret.status_code==302

    # .tox/c1/bin/pytest --cov=weko_sitemap tests/test_admin.py::TestSitemapSettingView::test_update_sitemap_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp
    @pytest.mark.parametrize(
    "id, is_admin",
    [
         (0, False),
         (1, False),
         (2, True),
         (3, True),
         (4, False),
         (5, False),
         (6, False),
         (7, False),
    ],
    )
    def test_update_sitemap_acl(self,app,client,users,db_sessionlifetime,id,is_admin):
        login_user_via_session(client=client, email=users[id]["email"])
        url = url_for("sitemap.update_sitemap", _external=True)
        ret = client.post(url)
        if is_admin:
            assert ret.status_code != 403
        else:
            assert ret.status_code == 403

    # .tox/c1/bin/pytest --cov=weko_sitemap tests/test_admin.py::TestSitemapSettingView::test_update_sitemap -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp
    def test_update_sitemap(self, client, users):
        login_user_via_session(client=client, email=users[3]["email"])
        patch("weko_sitemap.admin.validate_csrf_header")

        class MockTask:
            def __init__(self,id):
                self.id = id

        patch("weko_sitemap.tasks.link_success_handler.s",return_value=None)
        patch("weko_sitemap.tasks.link_error_handler.s",return_value=None)
        patch("weko_sitemap.tasks.update_sitemap.apply_async",return_value=MockTask("test_task"))

        url = url_for("sitemap.update_sitemap")
        test = {
            "task_id": "test_task",
            "loc":"/admin/sitemap/task_status/test_task",
        }
        res = client.post(url)
        assert json.loads(res.data) == test

    # def get_task_status(self, task_id):
    # .tox/c1/bin/pytest --cov=weko_sitemap tests/test_admin.py::TestSitemapSettingView::test_get_task_status_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp
    def test_get_task_status_acl_guest(self,app,client,db_sessionlifetime):
        url = url_for("sitemap.get_task_status", task_id=1,_external=True)
        ret = client.get(url)
        assert ret.status_code==302

    # .tox/c1/bin/pytest --cov=weko_sitemap tests/test_admin.py::TestSitemapSettingView::test_update_sitemap_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp
    @pytest.mark.parametrize(
    "id, is_admin",
    [
         (0, False),
         (1, False),
         (2, True),
         (3, True),
         (4, False),
         (5, False),
         (6, False),
         (7, False),
    ],
    )
    def test_update_sitemap_acl(self,app,client,users,db_sessionlifetime,id,is_admin):
        login_user_via_session(client=client, email=users[id]["email"])
        url = url_for("sitemap.get_task_status", task_id=1,_external=True)
        ret = client.get(url)
        if is_admin:
            assert ret.status_code != 403
        else:
            assert ret.status_code == 403

    # .tox/c1/bin/pytest --cov=weko_sitemap tests/test_admin.py::TestSitemapSettingView::test_get_task_status -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-sitemap/.tox/c1/tmp
    def test_get_task_status(self, app, client,users,db_sessionlifetime):
        login_user_via_session(client=client, email=users[2]["email"])

        class MockResult:
            def __init__(self,state):
                self.state = state
                self.info=[
                        {"start_time":"test_start_time",
                        "end_time":"test_end_time",
                        "total":"test_total"}
                    ]
        def mock_result_success(task_id):
            return MockResult("SUCCESS")
        def mock_result_else(task_id):
            return MockResult("ERROR")

        # task_result.state = success
        patch("weko_sitemap.admin.AsyncResult",side_effect=mock_result_success)
        url = url_for("sitemap.get_task_status", task_id="test_id",_external=True)
        ret = client.get(url)
        result = json.loads(ret.data)
        assert result["start_time"] == "test_start_time"
        assert result["end_time"] == "test_end_time"
        assert result["total"] == "test_total"
        assert result["state"] == "SUCCESS"

        # task_result.state != success
        patch("weko_sitemap.admin.AsyncResult",side_effect=mock_result_else)
        url = url_for("sitemap.get_task_status", task_id="test_id",_external=True)
        ret = client.get(url)
        result = json.loads(ret.data)
        assert result["start_time"] == ""
        assert result["end_time"] == ""
        assert result["total"] == ""
        assert result["state"] == "ERROR"

