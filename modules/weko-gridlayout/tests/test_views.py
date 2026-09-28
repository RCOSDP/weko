import json
import pytest
from mock import patch, Mock, MagicMock
import uuid
from flask import jsonify, url_for
from flask_security import url_for_security

from invenio_cache import current_cache
from invenio_accounts.testutils import login_user_via_session
from weko_gridlayout.models import WidgetDesignPage,WidgetDesignSetting,WidgetItem

# The endpoints these cases cover carry @login_required and nothing else
# (weko_gridlayout/views.py), so every signed-in user reaches them. The 403s
# that used to be here also did not describe a coherent rule: they denied
# contributor and repoadmin while allowing generaluser.
user_results1 = [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
]

# users indices: 0=contributor, 1=repoadmin, 2=sysadmin, 3=comadmin,
# 4=generaluser (see conftest.users fixture).
#
# load_widget_list_design_setting/save_widget_layout_setting/
# save_widget_design_page/delete_widget_design_page/delete_widget_item are
# now protected by weko_admin.permissions.repository_scope_required. These
# requests carry no repository_id/page_id/data_id in the body, so
# repository_id cannot be resolved: System/Repository Administrator are
# still allowed unconditionally, but Contributor/Community Administrator/
# no-role users are rejected because scope cannot be confirmed.
user_results_repo_scope_no_target = [
    (0, 403),
    (1, 200),
    (2, 200),
    (3, 403),
    (4, 403),
]


# def preload_pages():
def test_preload_pages(i18n_app, db):
    # preload_pages reads widget_design_page, so the tables have to exist.
    from weko_gridlayout.views import preload_pages

    assert preload_pages() == None


# def load_repository():
def test_load_repository(client, users):
    login_user_via_session(client=client, email=users[2]["email"])
    res = client.get(
        url_for("weko_gridlayout_api.load_repository"),
    )

    assert res.status_code == 200


@pytest.mark.parametrize('id, status_code', user_results1)
def test_unlocked_widget_login(client, users, id, status_code):
    login_user_via_session(client=client, email=users[id]["email"])
    with patch("weko_gridlayout.views.WidgetItemServices.unlock_widget", return_value=True):
        res = client.post("/admin/widget/unlock",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res.status_code == status_code


def test_unlocked_widget_guest(client, users):
    with patch("weko_gridlayout.views.WidgetItemServices.unlock_widget", return_value=True):
        res = client.post("/admin/widget/unlock",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res.status_code == 302


@pytest.mark.parametrize('id, status_code', user_results_repo_scope_no_target)
def test_save_widget_layout_setting_login(client, users, id, status_code):
    login_user_via_session(client=client, email=users[id]["email"])
    with patch("weko_gridlayout.views.WidgetDesignServices.update_widget_design_setting", return_value={}):
        res = client.post("/admin/save_widget_layout_setting",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res.status_code == status_code


def test_save_widget_layout_setting_guest(client, users):
    with patch("weko_gridlayout.views.WidgetDesignServices.update_widget_design_setting", return_value={}):
        res = client.post("/admin/save_widget_layout_setting",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res.status_code == 302


# save_widget_item is now protected by repository_scope_required as well.
# This request carries no data_id/data.repository, so the scope cannot be
# resolved and only System/Repository Administrator are allowed.
@pytest.mark.parametrize('id, status_code', user_results_repo_scope_no_target)
def test_save_widget_item_login(client, users, id, status_code):
    login_user_via_session(client=client, email=users[id]["email"])
    with patch("weko_gridlayout.views.WidgetItemServices.save_command", return_value={}):
        res = client.post("/admin/save_widget_item",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res.status_code == status_code


def test_save_widget_item_guest(client, users):
    with patch("weko_gridlayout.views.WidgetItemServices.save_command", return_value={}):
        res = client.post("/admin/save_widget_item",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res.status_code == 302


# save_widget_item scope check (repository_scope_required).
# data_id -> the widget being updated (source repository, taken from DB),
# data.repository -> the repository requested by the client (destination).
# .tox/c1/bin/pytest --cov=weko_gridlayout tests/test_views.py -k save_widget_item_scope -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-gridlayout/.tox/c1/tmp
def test_save_widget_item_scope_no_role(client, users, widget_item):
    """ロールなしログインユーザーは拒否されること。"""
    login_user_via_session(client=client, email=users[4]["email"])
    with patch("weko_gridlayout.views.WidgetItemServices.save_command", return_value={}):
        res = client.post(
            "/admin/save_widget_item",
            data=json.dumps({"flag_edit": False,
                             "data": {"repository": "Root Index"}}),
            content_type="application/json")
        assert res.status_code == 403


@pytest.mark.parametrize('id', [1, 2])  # repoadmin, sysadmin
def test_save_widget_item_scope_super_user(client, users, widget_item, id):
    """System/Repository Administratorは新規作成・更新とも許可されること。"""
    login_user_via_session(client=client, email=users[id]["email"])
    with patch("weko_gridlayout.views.WidgetItemServices.save_command", return_value={}):
        # create
        res = client.post(
            "/admin/save_widget_item",
            data=json.dumps({"flag_edit": False,
                             "data": {"repository": "Root Index"}}),
            content_type="application/json")
        assert res.status_code == 200

        # update
        res = client.post(
            "/admin/save_widget_item",
            data=json.dumps({"flag_edit": True,
                             "data_id": widget_item[0].widget_id,
                             "data": {"repository": "Root Index"}}),
            content_type="application/json")
        assert res.status_code == 200


@pytest.mark.parametrize('repository, status_code',
                         [("Root Index", 200), ("other", 403)])
def test_save_widget_item_scope_comadmin_create(client, users, repository,
                                                status_code):
    """Community Administratorの新規作成は担当コミュニティのみ許可されること。"""
    login_user_via_session(client=client, email=users[3]["email"])  # comadmin
    community = MagicMock(id="Root Index")
    with patch("weko_gridlayout.views.WidgetItemServices.save_command", return_value={}):
        with patch("invenio_communities.models.Community.get_repositories_by_user",
                   return_value=[community]):
            res = client.post(
                "/admin/save_widget_item",
                data=json.dumps({"flag_edit": False,
                                 "data": {"repository": repository}}),
                content_type="application/json")
            assert res.status_code == status_code


@pytest.mark.parametrize('repository, status_code',
                         [("Root Index", 200), ("other", 403)])
def test_save_widget_item_scope_comadmin_update(client, users, widget_item,
                                                repository, status_code):
    """担当内ウィジェットの更新は許可され、担当外への移動は拒否されること。"""
    login_user_via_session(client=client, email=users[3]["email"])  # comadmin
    community = MagicMock(id="Root Index")
    with patch("weko_gridlayout.views.WidgetItemServices.save_command", return_value={}):
        with patch("invenio_communities.models.Community.get_repositories_by_user",
                   return_value=[community]):
            res = client.post(
                "/admin/save_widget_item",
                data=json.dumps({"flag_edit": True,
                                 "data_id": widget_item[0].widget_id,
                                 "data": {"repository": repository}}),
                content_type="application/json")
            assert res.status_code == status_code


def test_save_widget_item_scope_not_found(client, users, widget_item):
    """存在しないdata_idを指定した場合は404になること。"""
    login_user_via_session(client=client, email=users[3]["email"])  # comadmin
    community = MagicMock(id="Root Index")
    with patch("weko_gridlayout.views.WidgetItemServices.save_command", return_value={}):
        with patch("invenio_communities.models.Community.get_repositories_by_user",
                   return_value=[community]):
            res = client.post(
                "/admin/save_widget_item",
                data=json.dumps({"flag_edit": True,
                                 "data_id": 999999,
                                 "data": {"repository": "Root Index"}}),
                content_type="application/json")
            assert res.status_code == 404


@pytest.mark.parametrize('id, status_code', user_results_repo_scope_no_target)
def test_save_widget_design_page_login(client, users, id, status_code):
    login_user_via_session(client=client, email=users[id]["email"])
    with patch("weko_gridlayout.views.WidgetDesignPageServices.add_or_update_page", return_value={}):
        res = client.post("/admin/save_widget_design_page",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res.status_code == status_code


def test_save_widget_design_page_guest(client, users):
    with patch("weko_gridlayout.views.WidgetDesignPageServices.add_or_update_page", return_value={}):
        res = client.post("/admin/save_widget_design_page",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res.status_code == 302


@pytest.mark.parametrize('id, status_code', user_results_repo_scope_no_target)
def test_load_widget_list_design_setting_login(client, users, id, status_code):
    from weko_gridlayout import views
    from weko_gridlayout.services import WidgetDesignServices
    views.get_default_language = Mock()
    WidgetDesignServices.get_widget_list = Mock(return_value={})
    WidgetDesignServices.get_widget_preview = Mock(return_value={})
    login_user_via_session(client=client, email=users[id]["email"])
    res = client.post("/admin/load_widget_list_design_setting",
                          data=json.dumps({}),
                          content_type="application/json")
    assert res.status_code == status_code


def test_load_widget_list_design_setting_guest(client, users):
    from weko_gridlayout import views
    from weko_gridlayout.services import WidgetDesignServices
    views.get_default_language = Mock()
    WidgetDesignServices.get_widget_list = Mock(return_value={})
    WidgetDesignServices.get_widget_preview = Mock(return_value={})
    res = client.post("/admin/load_widget_list_design_setting",
                          data=json.dumps({}),
                          content_type="application/json")
    assert res.status_code == 302

# .tox/c1/bin/pytest --cov=weko_gridlayout tests/test_views.py::test_load_widget_list_design_setting_issue50978 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_load_widget_list_design_setting_issue50978(client, users):
    from weko_gridlayout import views
    from weko_gridlayout.services import WidgetDesignServices
    views.get_default_language = Mock()
    WidgetDesignServices.get_widget_list = Mock(return_value={})
    WidgetDesignServices.get_widget_preview = Mock(return_value={})
    # Use a System Administrator here: load_widget_list_design_setting is now
    # protected by repository_scope_required, and this test targets the
    # view's own request-body validation (400), not the scope check, so it
    # must bypass the scope check via the unconditional super-user path.
    login_user_via_session(client=client, email=users[2]["email"])

    # no request data
    res = client.post("/admin/load_widget_list_design_setting")
    assert res.status_code == 400

    # invalid request data
    res = client.post(
        "/admin/load_widget_list_design_setting",
        data="test",
        content_type="application/json"
    )
    assert res.status_code == 400


user_results2 = [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
]


@pytest.mark.parametrize('id, status_code', user_results2)
def test_load_widget_design_setting_login(client, users, id, status_code):
    login_user_via_session(client=client, email=users[id]["email"])
    with patch("weko_gridlayout.views.get_widget_design_setting", return_value=jsonify({})):
        res1 = client.post("/admin/load_widget_design_setting",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res1.status_code == status_code
        res2 = client.post("/admin/load_widget_design_setting/japanese",
                               data=json.dumps({}),
                               content_type="application/json")
        assert res2.status_code == status_code


def test_load_widget_design_setting_guest(client, users):
    with patch("weko_gridlayout.views.get_widget_design_setting", return_value=jsonify({})):
        res1 = client.post("/admin/load_widget_design_setting",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res1.status_code == 200
        res2 = client.post("/admin/load_widget_design_setting/japanese",
                       data=json.dumps({}),
                       content_type="application/json")
        assert res2.status_code == 200


# .tox/c1/bin/pytest --cov=weko_gridlayout tests/test_views.py::test_load_widget_design_setting_issue50978 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_load_widget_design_setting_issue50978(client, users):
    with patch("weko_gridlayout.views.get_widget_design_setting", return_value=jsonify({})):
        # no request data
        res3 = client.post("/admin/load_widget_design_setting/japanese")
        assert res3.status_code == 400

        # invalid request data
        res4 = client.post(
            "/admin/load_widget_design_setting/japanese",
            data="test",
            content_type="application/json"
        )
        assert res4.status_code == 400


@pytest.mark.parametrize('id, status_code', user_results1)
def test_load_widget_design_pages_login(client, users, id, status_code):
    login_user_via_session(client=client, email=users[id]["email"])
    with patch("weko_gridlayout.views.get_default_language", return_value={}):
        with patch("weko_gridlayout.views.WidgetDesignPageServices.get_page_list", return_value={}):
            res1 = client.post("/admin/load_widget_design_pages",
                                  data=json.dumps({}),
                                  content_type="application/json")
            assert res1.status_code == status_code
            res2 = client.post("/admin/load_widget_design_pages/japanese",
                                  data=json.dumps({}),
                                  content_type="application/json")
            assert res2.status_code == status_code


def test_load_widget_design_pages_guest(client, users):
    with patch("weko_gridlayout.views.get_default_language", return_value={}):
        with patch("weko_gridlayout.views.WidgetDesignPageServices.get_page_list", return_value={}):
            res1 = client.post("/admin/load_widget_design_pages",
                                  data=json.dumps({}),
                                  content_type="application/json")
            assert res1.status_code == 302
            res2 = client.post("/admin/load_widget_design_pages/japanese",
                      data=json.dumps({}),
                      content_type="application/json")
            assert res2.status_code == 302


# .tox/c1/bin/pytest --cov=weko_gridlayout tests/test_views.py::test_load_widget_design_pages_issue50978 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_load_widget_design_pages_issue50978(client, users):
    login_user_via_session(client=client, email=users[3]["email"])
    with patch("weko_gridlayout.views.get_default_language", return_value={}):
        with patch("weko_gridlayout.views.WidgetDesignPageServices.get_page_list", return_value={}):
            # no request data
            res3 = client.post("/admin/load_widget_design_pages/japanese")
            assert res3.status_code == 400

            # invalid request data
            res4 = client.post(
                "/admin/load_widget_design_pages/japanese",
                data="test",
                content_type="application/json"
            )
            assert res4.status_code == 400


@pytest.mark.parametrize('id, status_code', user_results1)
def test_load_widget_design_page_login(client, users, id, status_code):
    login_user_via_session(client=client, email=users[id]["email"])
    with patch("weko_gridlayout.views.WidgetDesignPageServices.get_page", return_value={}):
        res = client.post("/admin/load_widget_design_page",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res.status_code == status_code


def test_load_widget_design_page_guest(client, users):
    with patch("weko_gridlayout.views.WidgetDesignPageServices.get_page", return_value={}):
        res = client.post("/admin/load_widget_design_page",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res.status_code == 302


# .tox/c1/bin/pytest --cov=weko_gridlayout tests/test_views.py::test_load_widget_design_page_issue50978 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_load_widget_design_page_issue50978(client, users):
    login_user_via_session(client=client, email=users[3]["email"])
    with patch("weko_gridlayout.views.WidgetDesignPageServices.get_page", return_value={}):
        # no request data
        res3 = client.post("/admin/load_widget_design_page")
        assert res3.status_code == 400

        # invalid request data
        res4 = client.post(
            "/admin/load_widget_design_page",
            data="test",
            content_type="application/json"
        )
        assert res4.status_code == 400


@pytest.mark.parametrize('id, status_code', user_results_repo_scope_no_target)
def test_delete_widget_item_login(client, users, id, status_code):
    login_user_via_session(client=client, email=users[id]["email"])
    with patch("weko_gridlayout.views.WidgetItemServices.delete_by_id", return_value={}):
        res = client.post("/admin/delete_widget_item",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res.status_code == status_code


def test_delete_widget_item_guest(client, users):
    with patch("weko_gridlayout.views.WidgetItemServices.delete_by_id", return_value={}):
        res = client.post("/admin/delete_widget_item",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res.status_code == 302


# .tox/c1/bin/pytest --cov=weko_gridlayout tests/test_views.py::test_load_widget_design_page_issue50978 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_delete_widget_item_issue50978(client, users):
    # System Administrator: delete_widget_item is now protected by
    # repository_scope_required and this test targets the view's own
    # request-body validation (400), so it must bypass the scope check.
    login_user_via_session(client=client, email=users[2]["email"])
    with patch("weko_gridlayout.views.WidgetItemServices.delete_by_id", return_value={}):
        # no request data. The view reads request.headers['Content-Type']
        # directly, so it needs the header even when there is no body.
        res3 = client.post("/admin/delete_widget_item",
                           content_type="application/json")
        assert res3.status_code == 400

        # invalid request data
        res4 = client.post(
            "/admin/delete_widget_item",
            data="test",
            content_type="application/json"
        )
        assert res4.status_code == 400


@pytest.mark.parametrize('id, status_code', user_results_repo_scope_no_target)
def test_delete_widget_design_page_login(client, users, id, status_code):
    login_user_via_session(client=client, email=users[id]["email"])
    with patch("weko_gridlayout.views.WidgetDesignPageServices.delete_page", return_value={}):
        res = client.post("/admin/delete_widget_design_page",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res.status_code == status_code


def test_delete_widget_design_page_guest(client, users):
    with patch("weko_gridlayout.views.WidgetDesignPageServices.delete_page", return_value={}):
        res = client.post("/admin/delete_widget_design_page",
                              data=json.dumps({}),
                              content_type="application/json")
        assert res.status_code == 302


# .tox/c1/bin/pytest --cov=weko_gridlayout tests/test_views.py::test_delete_widget_design_page_issue50978 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_delete_widget_design_page_issue50978(client, users):
    # System Administrator: delete_widget_design_page is now protected by
    # repository_scope_required and this test targets the view's own
    # request-body validation (400), so it must bypass the scope check.
    login_user_via_session(client=client, email=users[2]["email"])
    with patch("weko_gridlayout.views.WidgetDesignPageServices.delete_page", return_value={}):
        # no request data
        res3 = client.post(
            "/admin/delete_widget_design_page",
            content_type="application/json"
        )
        assert res3.status_code == 400

        # invalid request data
        res4 = client.post(
            "/admin/delete_widget_design_page",
            data="test",
            content_type="application/json"
        )
        assert res4.status_code == 400


# def index():
def test_index(client, users):
    login_user_via_session(client=client, email=users[2]['obj'].email)
    res = client.get(
        url_for("weko_gridlayout.index")
    )
    assert res.status_code == 200


# def load_widget_design_page_setting(page_id: str, current_language=''):
def test_load_widget_design_page_setting(client, users):
    login_user_via_session(client=client, email=users[2]['obj'].email)
    res = client.get(
        url_for(
            "weko_gridlayout_api.load_widget_design_page_setting",
            page_id="1",
            current_language="en"
        )
    )
    assert res.status_code == 200


# def save_widget_layout_setting():
def test_save_widget_layout_setting(client, users):
    login_user_via_session(client=client, email=users[2]['obj'].email)
    res = client.post(
        url_for("weko_gridlayout_api.save_widget_layout_setting"),
        headers={"Content-Type": "application/test"}
    )
    assert res.status_code == 200

    res = client.post(
        url_for("weko_gridlayout_api.save_widget_layout_setting"),
        json={"test": "test"},
        headers={"Content-Type": "application/json"},
    )
    assert res.status_code == 200

# .tox/c1/bin/pytest --cov=weko_gridlayout tests/test_views.py::test_save_widget_layout_setting_issue50978 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_save_widget_layout_setting_issue50978(client, users):
    login_user_via_session(client=client, email=users[2]['obj'].email)
    # no request data
    res3 = client.post(
        "/admin/save_widget_layout_setting",
        content_type="application/json"
    )
    assert res3.status_code == 400

    # invalid request data
    res4 = client.post(
        "/admin/save_widget_layout_setting",
        data="test",
        content_type="application/json"
    )
    assert res4.status_code == 400


# def save_widget_design_page():
def test_save_widget_design_page(client, users):
    login_user_via_session(client=client, email=users[2]['obj'].email)
    res = client.post(
        url_for("weko_gridlayout_api.save_widget_design_page"),
        headers={"Content-Type": "application/test"}
    )
    assert res.status_code == 200


# .tox/c1/bin/pytest --cov=weko_gridlayout tests/test_views.py::test_save_widget_design_page_issue50978 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_save_widget_design_page_issue50978(client, users):
    # System Administrator: save_widget_design_page is now protected by
    # repository_scope_required and this test targets the view's own
    # request-body validation (400), so it must bypass the scope check.
    login_user_via_session(client=client, email=users[2]["email"])
    # no request data
    res3 = client.post(
        "/admin/save_widget_design_page",
        content_type="application/json"
    )
    assert res3.status_code == 400

    # invalid request data
    res4 = client.post(
        "/admin/save_widget_design_page",
        data="test",
        content_type="application/json"
    )
    assert res4.status_code == 400


# def delete_widget_design_page():
def test_delete_widget_design_page(client, users):
    login_user_via_session(client=client, email=users[2]['obj'].email)
    res = client.post(
        url_for("weko_gridlayout_api.delete_widget_design_page"),
        headers={"Content-Type": "application/test"}
    )
    assert res.status_code == 200


# def load_widget_type():
def test_load_widget_type(client, users):
    login_user_via_session(client=client, email=users[2]['obj'].email)
    res = client.get(
        url_for("weko_gridlayout_api.load_widget_type"),
        headers={"Content-Type": "application/json"}
    )
    assert res.status_code == 200


# def save_widget_item():
def test_save_widget_item(client, users):
    login_user_via_session(client=client, email=users[2]['obj'].email)
    res = client.post(
        url_for("weko_gridlayout_api.save_widget_item"),
        headers={"Content-Type": "application/test"}
    )
    assert res.status_code == 200


# def delete_widget_item():
def test_delete_widget_item(client, users):
    login_user_via_session(client=client, email=users[2]['obj'].email)
    res = client.post(
        url_for("weko_gridlayout_api.delete_widget_item"),
        headers={"Content-Type": "application/test"}
    )
    assert res.status_code == 200


# def get_widget_item_list()
def test_get_widget_item_list(client, users):
    login_user_via_session(client=client, email=users[2]['obj'].email)
    res = client.get(
        url_for("weko_gridlayout_api.get_widget_item_list"),
        headers={"Content-Type": "application/json"}
    )
    assert res.status_code == 200


# def get_account_role():
def test_get_account_role(client, users):
    login_user_via_session(client=client, email=users[2]['obj'].email)
    res = client.get(
        url_for("weko_gridlayout_api.get_account_role"),
    )
    assert res.status_code == 200


# def get_system_lang():
def test_get_system_lang(client, users):
    res = client.get(
        url_for("weko_gridlayout_api.get_system_lang"),
    )
    assert res.status_code == 200


# def get_new_arrivals_data():
def test_get_new_arrivals_data(client, users):
    res = client.get(
        url_for("weko_gridlayout_api.get_new_arrivals_data", widget_id=1),
    )
    assert res.status_code == 200


# def get_rss_data():
# def test_get_rss_data(client, users):
#     res = client.get(
#         url_for(
#             "security.register",
#         ),
#         query_string={
#             'term': '1',
#             'count': 'a',
#         },
#     )
#     assert res.status_code == 200


# def get_widget_page_endpoints(widget_id, lang=''):
def test_get_widget_page_endpoints(client, users):
    with patch('weko_gridlayout.views.get_default_language', return_value={"lang_code": "en"}):
        res = client.get(
            url_for("weko_gridlayout_api.get_widget_page_endpoints", widget_id=1),
            headers={"Content-Type": "application/json"}
        )
        assert res.status_code == 200

        res = client.get(
            url_for("weko_gridlayout_api.get_widget_page_endpoints", widget_id=1),
            headers={"Content-Type": "application/test"}
        )
        assert res.status_code == 403


# def view_widget_page():
def test_view_widget_page(i18n_app):
    from weko_gridlayout.views import view_widget_page

    page = MagicMock()
    page.settings = [{
        "type": "Main contents"
    }]
    i18n_app.config['WEKO_GRIDLAYOUT_MAIN_TYPE'] = "Main contents"
    i18n_app.config['THEME_FRONTPAGE_TEMPLATE'] = 'weko_theme/frontpage.html'

    with patch('weko_gridlayout.views.WidgetDesignPage.get_by_url', return_value=page):
        # Exception coverage
        try:
            view_widget_page()
        except:
            pass


# def handle_not_found(exception, **extra):
def test_handle_not_found(i18n_app):
    from weko_gridlayout.views import handle_not_found
    from werkzeug.exceptions import NotFound

    page = MagicMock()
    page.settings = [{
        "type": "Main contents"
    }]
    i18n_app.config['WEKO_GRIDLAYOUT_MAIN_TYPE'] = "Main contents"
    i18n_app.config['THEME_FRONTPAGE_TEMPLATE'] = 'weko_theme/frontpage.html'
    i18n_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS'] = {
        'id': 'weko',
        'widths': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11']
    }
    notfound = NotFound()

    with patch('weko_gridlayout.views.WidgetDesignPage.get_by_url', return_value=page):
        with patch('weko_theme.utils.get_weko_contents', return_value={}):
            with patch('weko_gridlayout.views.render_template', return_value={}):
                assert handle_not_found(exception=notfound) != None

    extra = MagicMock()

    with patch('weko_gridlayout.views.WidgetDesignPage.get_by_url', return_value=None):
        with patch('weko_theme.utils.get_weko_contents', return_value={}):
            with patch('weko_gridlayout.views.render_template', return_value={}):
                assert handle_not_found(exception=notfound, current_handler=extra) != None
    # Exception coverage
    try:
        assert handle_not_found(exception=notfound, current_handler=extra) != None
    except:
        pass


# def _add_url_rule(url_or_urls):
def test__add_url_rule(app):
    from weko_gridlayout.views import _add_url_rule
    url_or_urls = "url_or_urls"

    assert _add_url_rule(url_or_urls) == None

# .tox/c1/bin/pytest --cov=weko_gridlayout tests/test_views.py::test_get_access_counter_record -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-gridlayout/.tox/c1/tmp
def test_get_access_counter_record(i18n_app, db, es, monkeypatch):
    current_cache.delete("access_counter")
    # not exist count_start_date
    widget_design_setting_settings = [
        {
            "x": 0,"y": 0,"width": 2,"height": 6,
            "name": "test_access_counter01",
            "id": "test_community01",
            "type": "Access counter",
            "widget_id": 1,
            "background_color": "#FFFFFF","label_enable": True,"theme": "default","frame_border_color": "#DDDDDD","border_style": "solid","label_text_color": "#333333","label_color": "#F5F5F5",
            "access_counter": "0",
            "following_message": "None","other_message": "None","preceding_message": "None",
            "multiLangSetting": {
                "en": {
                    "label": "test_access_counter01",
                    "description": {"access_counter": "0"}
                }
            },
            "created_date": "2024-03-08"
        }
    ]
    widget_design_setting = WidgetDesignSetting(
        repository_id="test_community01",
        settings=json.dumps(widget_design_setting_settings)
    )
    # exist count_start_date
    page_setting1 = [
        {
            "x": 0,"y": 0,"width": 3,"height": 6,
            "name": "test_menu01",
            "id": "test_community01",
            "type": "Menu",
            "widget_id": 3,
            "background_color": "#FFFFFF","label_enable": True,"theme": "default","frame_border_color": "#DDDDDD","border_style": "solid","label_text_color": "#333333","label_color": "#F5F5F5",
            "menu_orientation": "horizontal",
            "menu_bg_color": "#ffffff",
            "menu_active_bg_color": "#ffffff",
            "menu_default_color": "#000000",
            "menu_active_color": "#000000",
            "menu_show_pages": [1,2,"0"],
            "multiLangSetting": {
                "en": {
                    "label": "test_menu01",
                    "description": None
                }
            }
        },
        {
            "x": 0,"y": 0,"width": 2,"height": 6,
            "name": "test_access_counter02",
            "id": "test_community01",
            "type": "Access counter",
            "widget_id": 2,
            "background_color": "#FFFFFF","label_enable": True,"theme": "default","frame_border_color": "#DDDDDD","border_style": "solid","label_text_color": "#333333","label_color": "#F5F5F5",
            "access_counter": "0",
            "following_message": "None","other_message": "None","preceding_message": "None",
            "multiLangSetting": {
                "en": {
                    "label": "test_access_counter02",
                    "description": {"access_counter": "0", "count_start_date": "2024-03-08"}
                }
            },
            "created_date": "2024-03-09",
            "count_start_date": "2024-03-08"
        }
    ]
    widget_design_page1 = WidgetDesignPage(
        title="page01",
        repository_id="test_community01",
        url="/page01",
        settings=json.dumps(page_setting1)
    )

    # Use the same widget as main
    page_setting2 = [
        {
            "x": 0,"y": 0,"width": 2,"height": 6,
            "name": "test_access_counter01",
            "id": "test_community01",
            "type": "Access counter",
            "widget_id": 1,
            "background_color": "#FFFFFF","label_enable": True,"theme": "default","frame_border_color": "#DDDDDD","border_style": "solid","label_text_color": "#333333","label_color": "#F5F5F5",
            "access_counter": "0",
            "following_message": "None","other_message": "None","preceding_message": "None",
            "multiLangSetting": {
                "en": {
                    "label": "test_access_counter01",
                    "description": {"access_counter": "0"}
                }
            },
            "created_date": "2024-03-09"
        }
    ]
    widget_design_page2 = WidgetDesignPage(
        title="page02",
        repository_id="test_community01",
        url="/page02",
        settings=json.dumps(page_setting2)
    )
    db.session.add(widget_design_page1)
    db.session.add(widget_design_page2)
    db.session.add(widget_design_setting)
    db.session.commit()

    uuid1=uuid.uuid4()
    es.index(
        index='{}stats-top-view-0001'.format(i18n_app.config['SEARCH_INDEX_PREFIX']),
        doc_type="top-view-day-aggregation",
        id=uuid1,
        body={
            "timestamp":"2024-03-08T00:00:00",
            "unique_id":uuid1,
            "count":1,"unique_count":1,
            "country":None,"hostname":"None",
            "remote_addr":"192.168.56.1",
            "site_license_name":"","site_license_flag":False
        },
        refresh='true'
    )
    uuid2=uuid.uuid4()
    es.index(
        index='{}stats-top-view-0001'.format(i18n_app.config['SEARCH_INDEX_PREFIX']),
        doc_type="top-view-day-aggregation",
        id=uuid2,
        body={
            "timestamp":"2024-03-09T00:00:00",
            "unique_id":uuid2,
            "count":3,"unique_count":3,
            "country":None,"hostname":"None",
            "remote_addr":"192.168.56.1",
            "site_license_name":"","site_license_flag":False
        },
        refresh='true'
    )
    uuid3=uuid.uuid4()
    es.index(
        index='{}stats-top-view-0001'.format(i18n_app.config['SEARCH_INDEX_PREFIX']),
        doc_type="top-view-day-aggregation",
        id=uuid3,
        body={
            "timestamp":"2024-03-09T00:00:00",
            "unique_id":uuid3,
            "count":5,"unique_count":3,
            "country":None,"hostname":"None",
            "remote_addr":"192.168.56.1",
            "site_license_name":"","site_license_flag":False
        },
        refresh='true'
    )

    import datetime
    with i18n_app.test_client() as client:
        with patch("weko_gridlayout.views.date") as mock_date:
            mock_date.today.return_value = datetime.date(2024,3,10)
            with patch("weko_gridlayout.views.current_cache.set") as mock_set:
                url = url_for("weko_gridlayout_api.get_access_counter_record",
                          repository_id="test_community01",
                          path="main",
                          current_language="en")
                test = {"1":{"2024-03-08":{"access_counter":"0","all":{"count":9},"date":"2024-03-08-2024-03-10"}}}
                res = client.get(url)
                assert res.status_code==200
                assert json.loads(res.data) == test
                args, kwargs = mock_set.call_args
                # The cache key carries the path ('main', or the page id).
                assert args[0] == 'access_counter_main'
                assert json.loads(args[1].data) == test
                assert args[2] == 50

            mock_cache_data = {"1":{"2024-03-08":{"access_counter":"0","all":{"192.168.56.1":{"count":9,"host":"None","ip":"192.168.56.1"},"count":9},"date":"2024-03-08-2024-03-10"}}}
            with patch("weko_gridlayout.views.current_cache.get", return_value=jsonify(mock_cache_data)):
                with patch("weko_gridlayout.views.current_cache.set") as mock_set:
                    url = url_for("weko_gridlayout_api.get_access_counter_record",
                              repository_id="test_community01",
                              path="page02",
                              current_language="en")
                    test = {"1":{"2024-03-08":{"access_counter":"0","all":{"192.168.56.1":{"count":9,"host":"None","ip":"192.168.56.1"},"count":9},"date":"2024-03-08-2024-03-10"}}}
                    res = client.get(url)
                    assert res.status_code==200
                    assert json.loads(res.data) == test
                    mock_set.assert_not_called()

            with patch("weko_gridlayout.views.current_cache.set") as mock_set:
                url = url_for("weko_gridlayout_api.get_access_counter_record",
                          repository_id="test_community01",
                          path="page01",
                          current_language="en")
                test = {"2":{"2024-03-08":{"access_counter":"0","all":{"count":9},"date":"2024-03-08-2024-03-10"}}}
                res = client.get(url)
                assert res.status_code==200
                assert json.loads(res.data) == test
                args, kwargs = mock_set.call_args
                assert args[0] == 'access_counter_1'
                assert json.loads(args[1].data) == test
                assert args[2] == 50

            # not exist widget_ids
            with patch("weko_gridlayout.services.WidgetDesignServices.get_widget_design_setting", return_value={}):
                url = url_for("weko_gridlayout_api.get_access_counter_record",
                          repository_id="test_community01",
                          path="main",
                          current_language="en")
                res = client.get(url)
                assert res.status_code==404


# def upload_file(community_id):
def test_upload_file(client, users, communities):
    # upload_file is login_required now.
    login_user_via_session(client=client, email=users[2]["email"])
    with patch('weko_gridlayout.views.get_default_language', return_value={"lang_code": "en"}):
        res = client.post(
            url_for("weko_gridlayout.upload_file", community_id="comm1"),
        )
        assert res.status_code == 400


# def uploaded_file(filename, community_id=0):
def test_uploaded_file(client, communities):
    # The view returns whatever get_file() gives it, so the stand-in has to be
    # something Flask can turn into a response - a function is not.
    with patch('weko_gridlayout.views.WidgetBucket.get_file', return_value="test"):
        res = client.get(
            url_for("weko_gridlayout.uploaded_file", community_id="comm1", filename="file")
        )
        assert res.status_code == 200
        assert res.get_data(as_text=True) == "test"


# def unlocked_widget():
def test_unlocked_widget(client, users):
    login_user_via_session(client=client, email=users[2]["email"])
    with patch('weko_gridlayout.views.WidgetItemServices.unlock_widget', return_value=False):
        res = client.post(
                url_for("weko_gridlayout_api.unlocked_widget"),
                json={"widget_id": 1}
            )
        assert res.status_code == 200


# .tox/c1/bin/pytest --cov=weko_gridlayout tests/test_views.py::test_unlocked_widget_issue50978 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_unlocked_widget_issue50978(client, users):
    login_user_via_session(client=client, email=users[2]["email"])
    with patch('weko_gridlayout.views.WidgetItemServices.unlock_widget', return_value=False):
        # no request data
        res3 = client.post(
            "/admin/widget/unlock",
            content_type="application/json"
        )
        assert res3.status_code == 400

        # invalid request data
        res4 = client.post(
            "/admin/widget/unlock",
            data="test",
            content_type="application/json"
        )
        assert res4.status_code == 400


# ---------------------------------------------------------------------------
# repository_scope_required coverage
#
# no.283/284/288/289/292: load_widget_list_design_setting,
# save_widget_layout_setting, save_widget_design_page,
# delete_widget_design_page and delete_widget_item are now protected by
# weko_admin.permissions.repository_scope_required so that only
# System/Repository Administrator or the Community Administrator in charge
# of the target repository can operate on it.
#
# users indices (see conftest.users): 0=contributor, 1=repoadmin,
# 2=sysadmin, 3=comadmin, 4=generaluser, 7=plain user with no role.
# ---------------------------------------------------------------------------

IN_SCOPE_COMMUNITY = [MagicMock(id='Root Index')]
OUT_OF_SCOPE_COMMUNITY = [MagicMock(id='OtherRepo')]


# def load_widget_list_design_setting():
@pytest.mark.parametrize('id, status_code', [(1, 200), (2, 200)])
def test_load_widget_list_design_setting_scope_super_user(
        client, users, id, status_code):
    """System/Repository Administratorは無条件で許可されること。"""
    from weko_gridlayout.services import WidgetDesignServices
    WidgetDesignServices.get_widget_list = Mock(return_value={})
    WidgetDesignServices.get_widget_preview = Mock(return_value={})
    login_user_via_session(client=client, email=users[id]["email"])
    res = client.post("/admin/load_widget_list_design_setting",
                      data=json.dumps({"repository_id": "Root Index"}),
                      content_type="application/json")
    assert res.status_code == status_code


def test_load_widget_list_design_setting_scope_community_admin_allowed(
        client, users):
    """担当コミュニティのCommunity Administratorは許可されること。"""
    from weko_gridlayout.services import WidgetDesignServices
    WidgetDesignServices.get_widget_list = Mock(return_value={})
    WidgetDesignServices.get_widget_preview = Mock(return_value={})
    login_user_via_session(client=client, email=users[3]["email"])
    with patch("invenio_communities.models.Community.get_repositories_by_user",
              return_value=IN_SCOPE_COMMUNITY):
        res = client.post("/admin/load_widget_list_design_setting",
                          data=json.dumps({"repository_id": "Root Index"}),
                          content_type="application/json")
    assert res.status_code == 200


def test_load_widget_list_design_setting_scope_community_admin_denied(
        client, users):
    """担当外コミュニティのCommunity Administratorは拒否されること。"""
    login_user_via_session(client=client, email=users[3]["email"])
    with patch("invenio_communities.models.Community.get_repositories_by_user",
              return_value=OUT_OF_SCOPE_COMMUNITY):
        res = client.post("/admin/load_widget_list_design_setting",
                          data=json.dumps({"repository_id": "Root Index"}),
                          content_type="application/json")
    assert res.status_code == 403


def test_load_widget_list_design_setting_scope_no_role(client, users):
    """ロールなしログインユーザーは拒否されること。"""
    login_user_via_session(client=client, email=users[4]["email"])
    res = client.post("/admin/load_widget_list_design_setting",
                      data=json.dumps({"repository_id": "Root Index"}),
                      content_type="application/json")
    assert res.status_code == 403


def test_load_widget_list_design_setting_scope_anonymous(client, users):
    """未ログインの場合はログイン画面へリダイレクトされること(login_requiredが先に働く)。"""
    res = client.post("/admin/load_widget_list_design_setting",
                      data=json.dumps({"repository_id": "Root Index"}),
                      content_type="application/json")
    assert res.status_code == 302


# def save_widget_layout_setting():
def test_save_widget_layout_setting_scope_community_admin_allowed(
        client, users):
    """担当コミュニティのCommunity Administratorは許可されること。"""
    login_user_via_session(client=client, email=users[3]["email"])
    with patch("weko_gridlayout.views.WidgetDesignServices.update_widget_design_setting",
              return_value={}):
        with patch("invenio_communities.models.Community.get_repositories_by_user",
                  return_value=IN_SCOPE_COMMUNITY):
            res = client.post(
                "/admin/save_widget_layout_setting",
                data=json.dumps({"repository_id": "Root Index", "page_id": 0}),
                content_type="application/json")
    assert res.status_code == 200


def test_save_widget_layout_setting_scope_community_admin_denied(
        client, users):
    """担当外コミュニティのCommunity Administratorは拒否されること。"""
    login_user_via_session(client=client, email=users[3]["email"])
    with patch("invenio_communities.models.Community.get_repositories_by_user",
              return_value=OUT_OF_SCOPE_COMMUNITY):
        res = client.post(
            "/admin/save_widget_layout_setting",
            data=json.dumps({"repository_id": "Root Index", "page_id": 0}),
            content_type="application/json")
    assert res.status_code == 403


def test_save_widget_layout_setting_scope_no_role(client, users):
    """ロールなしログインユーザーは拒否されること。"""
    login_user_via_session(client=client, email=users[4]["email"])
    res = client.post(
        "/admin/save_widget_layout_setting",
        data=json.dumps({"repository_id": "Root Index", "page_id": 0}),
        content_type="application/json")
    assert res.status_code == 403


def test_save_widget_layout_setting_scope_anonymous(client, users):
    """未ログインの場合はログイン画面へリダイレクトされること(login_requiredが先に働く)。"""
    res = client.post(
        "/admin/save_widget_layout_setting",
        data=json.dumps({"repository_id": "Root Index", "page_id": 0}),
        content_type="application/json")
    assert res.status_code == 302


def test_save_widget_layout_setting_scope_both_params_required(
        client, users, db_register):
    """既存ページ更新時はDB側とbody側の双方が担当範囲内であることを要求すること。

    page_id=1の実データは'Root Index'(担当内)に属するが、bodyでは担当外の
    OtherRepoが指定されているため拒否される。
    """
    login_user_via_session(client=client, email=users[3]["email"])
    with patch("weko_gridlayout.views.WidgetDesignServices.update_widget_design_setting",
              return_value={}):
        with patch("invenio_communities.models.Community.get_repositories_by_user",
                  return_value=IN_SCOPE_COMMUNITY):
            res = client.post(
                "/admin/save_widget_layout_setting",
                data=json.dumps({"repository_id": "OtherRepo", "page_id": 1}),
                content_type="application/json")
    assert res.status_code == 403


def test_save_widget_layout_setting_scope_id_param_not_found(
        client, users, db_register):
    """id_paramで指定したページが存在しない場合は404になること。"""
    login_user_via_session(client=client, email=users[3]["email"])
    res = client.post(
        "/admin/save_widget_layout_setting",
        data=json.dumps({"repository_id": "Root Index", "page_id": 999}),
        content_type="application/json")
    assert res.status_code == 404


# def save_widget_design_page():
def test_save_widget_design_page_scope_community_admin_allowed(
        client, users):
    """担当コミュニティのCommunity Administratorは許可されること。"""
    login_user_via_session(client=client, email=users[3]["email"])
    with patch("weko_gridlayout.views.WidgetDesignPageServices.add_or_update_page",
              return_value={}):
        with patch("invenio_communities.models.Community.get_repositories_by_user",
                  return_value=IN_SCOPE_COMMUNITY):
            res = client.post(
                "/admin/save_widget_design_page",
                data=json.dumps({"repository_id": "Root Index", "page_id": 0}),
                content_type="application/json")
    assert res.status_code == 200


def test_save_widget_design_page_scope_community_admin_denied(client, users):
    """担当外コミュニティのCommunity Administratorは拒否されること。"""
    login_user_via_session(client=client, email=users[3]["email"])
    with patch("invenio_communities.models.Community.get_repositories_by_user",
              return_value=OUT_OF_SCOPE_COMMUNITY):
        res = client.post(
            "/admin/save_widget_design_page",
            data=json.dumps({"repository_id": "Root Index", "page_id": 0}),
            content_type="application/json")
    assert res.status_code == 403


def test_save_widget_design_page_scope_no_role(client, users):
    """ロールなしログインユーザーは拒否されること。"""
    login_user_via_session(client=client, email=users[4]["email"])
    res = client.post(
        "/admin/save_widget_design_page",
        data=json.dumps({"repository_id": "Root Index", "page_id": 0}),
        content_type="application/json")
    assert res.status_code == 403


def test_save_widget_design_page_scope_anonymous(client, users):
    """未ログインの場合はログイン画面へリダイレクトされること(login_requiredが先に働く)。"""
    res = client.post(
        "/admin/save_widget_design_page",
        data=json.dumps({"repository_id": "Root Index", "page_id": 0}),
        content_type="application/json")
    assert res.status_code == 302


def test_save_widget_design_page_scope_both_params_required(
        client, users, db_register):
    """既存ページ更新時はDB側とbody側の双方が担当範囲内であることを要求すること。"""
    login_user_via_session(client=client, email=users[3]["email"])
    with patch("weko_gridlayout.views.WidgetDesignPageServices.add_or_update_page",
              return_value={}):
        with patch("invenio_communities.models.Community.get_repositories_by_user",
                  return_value=IN_SCOPE_COMMUNITY):
            res = client.post(
                "/admin/save_widget_design_page",
                data=json.dumps({"repository_id": "OtherRepo", "page_id": 1}),
                content_type="application/json")
    assert res.status_code == 403


# def delete_widget_design_page():
def test_delete_widget_design_page_scope_community_admin_allowed(
        client, users, db_register):
    """担当コミュニティのCommunity Administratorは許可されること。"""
    login_user_via_session(client=client, email=users[3]["email"])
    with patch("weko_gridlayout.views.WidgetDesignPageServices.delete_page",
              return_value={}):
        with patch("invenio_communities.models.Community.get_repositories_by_user",
                  return_value=IN_SCOPE_COMMUNITY):
            res = client.post(
                "/admin/delete_widget_design_page",
                data=json.dumps({"page_id": 1}),
                content_type="application/json")
    assert res.status_code == 200


def test_delete_widget_design_page_scope_community_admin_denied(
        client, users, db_register):
    """担当外コミュニティのCommunity Administratorは拒否されること。"""
    login_user_via_session(client=client, email=users[3]["email"])
    with patch("invenio_communities.models.Community.get_repositories_by_user",
              return_value=OUT_OF_SCOPE_COMMUNITY):
        res = client.post(
            "/admin/delete_widget_design_page",
            data=json.dumps({"page_id": 1}),
            content_type="application/json")
    assert res.status_code == 403


def test_delete_widget_design_page_scope_no_role(client, users, db_register):
    """ロールなしログインユーザーは拒否されること。"""
    login_user_via_session(client=client, email=users[4]["email"])
    res = client.post(
        "/admin/delete_widget_design_page",
        data=json.dumps({"page_id": 1}),
        content_type="application/json")
    assert res.status_code == 403


def test_delete_widget_design_page_scope_anonymous(client, users, db_register):
    """未ログインの場合はログイン画面へリダイレクトされること(login_requiredが先に働く)。"""
    res = client.post(
        "/admin/delete_widget_design_page",
        data=json.dumps({"page_id": 1}),
        content_type="application/json")
    assert res.status_code == 302


def test_delete_widget_design_page_scope_id_param_not_found(client, users):
    """id_paramで指定したページが存在しない場合は404になること。"""
    login_user_via_session(client=client, email=users[3]["email"])
    res = client.post(
        "/admin/delete_widget_design_page",
        data=json.dumps({"page_id": 999}),
        content_type="application/json")
    assert res.status_code == 404


# def delete_widget_item():
#
# WidgetItem's primary key column is widget_id, not id. If pk_attr were left
# at its default ('id'), WidgetItem.query.filter_by(id=...) would raise
# InvalidRequestError (no such column) and turn into a 500 for a Community
# Administrator (System/Repository Administrator would never hit this path
# since they return early). This is the specific regression this decorator
# application must avoid on this endpoint.
def test_delete_widget_item_scope_community_admin_allowed_pk_attr(
        client, users, db_register):
    """pk_attr='widget_id'が機能し、担当コミュニティ管理者が例外なく200になること。"""
    login_user_via_session(client=client, email=users[3]["email"])
    with patch("weko_gridlayout.views.WidgetItemServices.delete_by_id",
              return_value={}):
        with patch("invenio_communities.models.Community.get_repositories_by_user",
                  return_value=IN_SCOPE_COMMUNITY):
            res = client.post(
                "/admin/delete_widget_item",
                data=json.dumps({"data_id": 1}),
                content_type="application/json")
    assert res.status_code == 200


def test_delete_widget_item_scope_community_admin_denied(
        client, users, db_register):
    """担当外コミュニティのCommunity Administratorは拒否されること。"""
    login_user_via_session(client=client, email=users[3]["email"])
    with patch("invenio_communities.models.Community.get_repositories_by_user",
              return_value=OUT_OF_SCOPE_COMMUNITY):
        res = client.post(
            "/admin/delete_widget_item",
            data=json.dumps({"data_id": 1}),
            content_type="application/json")
    assert res.status_code == 403


def test_delete_widget_item_scope_no_role(client, users, db_register):
    """ロールなしログインユーザーは拒否されること。"""
    login_user_via_session(client=client, email=users[4]["email"])
    res = client.post(
        "/admin/delete_widget_item",
        data=json.dumps({"data_id": 1}),
        content_type="application/json")
    assert res.status_code == 403


def test_delete_widget_item_scope_anonymous(client, users, db_register):
    """未ログインの場合はログイン画面へリダイレクトされること(login_requiredが先に働く)。"""
    res = client.post(
        "/admin/delete_widget_item",
        data=json.dumps({"data_id": 1}),
        content_type="application/json")
    assert res.status_code == 302


def test_delete_widget_item_scope_id_param_not_found(client, users):
    """id_paramで指定したウィジェットが存在しない場合は404になること。"""
    login_user_via_session(client=client, email=users[3]["email"])
    res = client.post(
        "/admin/delete_widget_item",
        data=json.dumps({"data_id": 999}),
        content_type="application/json")
    assert res.status_code == 404
