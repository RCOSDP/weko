import json
import pytest
from mock import patch, Mock
from flask import jsonify

from invenio_accounts.testutils import login_user_via_session


user_results1 = [
    (0, 403),
    (1, 403),
    (2, 200),
    (3, 200),
    (4, 200),
]


@pytest.mark.parametrize('id, status_code', user_results1)
def test_unlocked_widget_login(client_api, users, id, status_code):
    login_user_via_session(client=client_api, email=users[id]["email"])
    with patch("weko_gridlayout.views.WidgetItemServices.unlock_widget", return_value=True):
        res = client_api.post("/admin/widget/unlock",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res.status_code == status_code


def test_unlocked_widget_guest(client_api, users):
    with patch("weko_gridlayout.views.WidgetItemServices.unlock_widget", return_value=True):
        res = client_api.post("/admin/widget/unlock",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res.status_code == 302


@pytest.mark.parametrize('id, status_code', user_results1)
def test_save_widget_layout_setting_login(client_api, users, id, status_code):
    login_user_via_session(client=client_api, email=users[id]["email"])
    with patch("weko_gridlayout.views.WidgetDesignServices.update_widget_design_setting", return_value={}):
        res = client_api.post("/admin/save_widget_layout_setting",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res.status_code == status_code


def test_save_widget_layout_setting_guest(client_api, users):
    with patch("weko_gridlayout.views.WidgetDesignServices.update_widget_design_setting", return_value={}):
        res = client_api.post("/admin/save_widget_layout_setting",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res.status_code == 302


@pytest.mark.parametrize('id, status_code', user_results1)
def test_save_widget_item_login(client_api, users, id, status_code):
    login_user_via_session(client=client_api, email=users[id]["email"])
    with patch("weko_gridlayout.views.WidgetItemServices.save_command", return_value={}):
        res = client_api.post("/admin/save_widget_item",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res.status_code == status_code


def test_save_widget_item_guest(client_api, users):
    with patch("weko_gridlayout.views.WidgetItemServices.save_command", return_value={}):
        res = client_api.post("/admin/save_widget_item",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res.status_code == 302


@pytest.mark.parametrize('id, status_code', user_results1)
def test_save_widget_design_page_login(client_api, users, id, status_code):
    login_user_via_session(client=client_api, email=users[id]["email"])
    with patch("weko_gridlayout.views.WidgetDesignPageServices.add_or_update_page", return_value={}):
        res = client_api.post("/admin/save_widget_design_page",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res.status_code == status_code


def test_save_widget_design_page_guest(client_api, users):
    with patch("weko_gridlayout.views.WidgetDesignPageServices.add_or_update_page", return_value={}):
        res = client_api.post("/admin/save_widget_design_page",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res.status_code == 302


@pytest.mark.parametrize('id, status_code', user_results1)
def test_load_widget_list_design_setting_login(client_api, users, id, status_code):
    from weko_gridlayout import views
    from weko_gridlayout.services import WidgetDesignServices
    views.get_default_language = Mock()
    WidgetDesignServices.get_widget_list = Mock(return_value={})
    WidgetDesignServices.get_widget_preview = Mock(return_value={})
    login_user_via_session(client=client_api, email=users[id]["email"])
    res = client_api.post("/admin/load_widget_list_design_setting",
                          data=json.dumps({}),
                          content_type="application/json")
    assert res.status_code == status_code


def test_load_widget_list_design_setting_guest(client_api, users):
    from weko_gridlayout import views
    from weko_gridlayout.services import WidgetDesignServices
    views.get_default_language = Mock()
    WidgetDesignServices.get_widget_list = Mock(return_value={})
    WidgetDesignServices.get_widget_preview = Mock(return_value={})
    res = client_api.post("/admin/load_widget_list_design_setting",
                          data=json.dumps({}),
                          content_type="application/json")
    assert res.status_code == 302


user_results2 = [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
]


@pytest.mark.parametrize('id, status_code', user_results2)
def test_load_widget_design_setting_login(client_api, users, id, status_code):
    login_user_via_session(client=client_api, email=users[id]["email"])
    with patch("weko_gridlayout.views.get_widget_design_setting", return_value=jsonify({})):
        res1 = client_api.post("/admin/load_widget_design_setting",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res1.status_code == status_code
        res2 = client_api.post("/admin/load_widget_design_setting/japanese",
                               data=json.dumps({}),
                               content_type="application/json")
        assert res2.status_code == status_code


def test_load_widget_design_setting_guest(client_api, users):
    with patch("weko_gridlayout.views.get_widget_design_setting", return_value=jsonify({})):
        res1 = client_api.post("/admin/load_widget_design_setting",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res1.status_code == 200
        res2 = client_api.post("/admin/load_widget_design_setting/japanese",
                       data=json.dumps({}),
                       content_type="application/json")
        assert res2.status_code == 200


@pytest.mark.parametrize('id, status_code', user_results1)
def test_load_widget_design_pages_login(client_api, users, id, status_code):
    login_user_via_session(client=client_api, email=users[id]["email"])
    with patch("weko_gridlayout.views.get_default_language", return_vlaue={}):
        with patch("weko_gridlayout.views.WidgetDesignPageServices.get_page_list", return_value={}):
            res1 = client_api.post("/admin/load_widget_design_pages",
                                  data=json.dumps({}),
                                  content_type="application/json")
            assert res1.status_code == status_code
            res2 = client_api.post("/admin/load_widget_design_pages/japanese",
                                  data=json.dumps({}),
                                  content_type="application/json")
            assert res2.status_code == status_code


def test_load_widget_design_pages_guest(client_api, users):
    with patch("weko_gridlayout.views.get_default_language", return_vlaue={}):
        with patch("weko_gridlayout.views.WidgetDesignPageServices.get_page_list", return_value={}):
            res1 = client_api.post("/admin/load_widget_design_pages",
                                  data=json.dumps({}),
                                  content_type="application/json")
            assert res1.status_code == 302
            res2 = client_api.post("/admin/load_widget_design_pages/japanese",
                      data=json.dumps({}),
                      content_type="application/json")
            assert res2.status_code == 302


@pytest.mark.parametrize('id, status_code', user_results1)
def test_load_widget_design_page_login(client_api, users, id, status_code):
    login_user_via_session(client=client_api, email=users[id]["email"])
    with patch("weko_gridlayout.views.WidgetDesignPageServices.get_page", return_value={}):
        res = client_api.post("/admin/load_widget_design_page",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res.status_code == status_code


def test_load_widget_design_page_guest(client_api, users):
    with patch("weko_gridlayout.views.WidgetDesignPageServices.get_page", return_value={}):
        res = client_api.post("/admin/load_widget_design_page",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res.status_code == 302


@pytest.mark.parametrize('id, status_code', user_results1)
def test_delete_widget_item_login(client_api, users, id, status_code):
    login_user_via_session(client=client_api, email=users[id]["email"])
    with patch("weko_gridlayout.views.WidgetItemServices.delete_by_id", return_value={}):
        res = client_api.post("/admin/delete_widget_item",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res.status_code == status_code


def test_delete_widget_item_guest(client_api, users):
    with patch("weko_gridlayout.views.WidgetItemServices.delete_by_id", return_value={}):
        res = client_api.post("/admin/delete_widget_item",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res.status_code == 302


@pytest.mark.parametrize('id, status_code', user_results1)
def test_delete_widget_design_page_login(client_api, users, id, status_code):
    login_user_via_session(client=client_api, email=users[id]["email"])
    with patch("weko_gridlayout.views.WidgetDesignPageServices.delete_page", return_value={}):
        res = client_api.post("/admin/delete_widget_design_page",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res.status_code == status_code


def test_delete_widget_design_page_guest(client_api, users):
    with patch("weko_gridlayout.views.WidgetDesignPageServices.delete_page", return_value={}):
        res = client_api.post("/admin/delete_widget_design_page",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res.status_code == 302