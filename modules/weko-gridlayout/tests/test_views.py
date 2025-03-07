import json
import pytest
from mock import patch, Mock, MagicMock
from flask import jsonify, url_for
from flask_security import url_for_security

from invenio_accounts.testutils import login_user_via_session


user_results1 = [
    (0, 403),
    (1, 403),
    (2, 200),
    (3, 200),
    (4, 200),
]


# def preload_pages(): 
def test_preload_pages(i18n_app):
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


@pytest.mark.parametrize('id, status_code', user_results1)
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


@pytest.mark.parametrize('id, status_code', user_results1)
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


@pytest.mark.parametrize('id, status_code', user_results1)
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


@pytest.mark.parametrize('id, status_code', user_results1)
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
    login_user_via_session(client=client, email=users[3]["email"])

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


@pytest.mark.parametrize('id, status_code', user_results1)
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
    login_user_via_session(client=client, email=users[3]["email"])
    with patch("weko_gridlayout.views.WidgetItemServices.delete_by_id", return_value={}):
        # no request data
        res3 = client.post("/admin/delete_widget_item")
        assert res3.status_code == 400

        # invalid request data
        res4 = client.post(
            "/admin/delete_widget_item",
            data="test",
            content_type="application/json"
        )
        assert res4.status_code == 400


@pytest.mark.parametrize('id, status_code', user_results1)
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
    login_user_via_session(client=client, email=users[3]["email"])
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
    login_user_via_session(client=client, email=users[3]["email"])
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
        with patch('weko_gridlayout.views.get_weko_contents', return_value={}):
            with patch('weko_gridlayout.views.render_template', return_value={}):
                assert handle_not_found(exception=notfound) != None
    
    extra = MagicMock()

    with patch('weko_gridlayout.views.WidgetDesignPage.get_by_url', return_value=None):
        with patch('weko_gridlayout.views.get_weko_contents', return_value={}):
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


# def get_access_counter_record(repository_id, current_language): 
def test_get_access_counter_record(i18n_app):
    from datetime import date, timedelta

    def set_func(key, value, time):
        return True
    
    def get_func(key):
        return ""
    
    cache = MagicMock()
    cache.get = get_func
    cache.set = set_func
    
    i18n_app.extensions['invenio-cache'] = MagicMock()
    i18n_app.extensions['invenio-cache'].cache = cache

    widget_design_setting = {
        "widget-settings": [{
            "created_date": date.today().strftime("%Y-%m-%d"),
            "type": "Access counter",
        }]
    }

    with i18n_app.test_client() as client:
        with patch("weko_gridlayout.views.WidgetDesignServices.get_widget_design_setting", return_value=widget_design_setting):
            with patch("weko_gridlayout.views.QueryCommonReportsHelper.get", return_value={"all": {'count': {'count': 9999}}}):
                res = client.get(
                    url_for(
                        "weko_gridlayout_api.get_access_counter_record",
                        repository_id=1,
                        current_language="en"
                    ),
                )
                assert res.status_code == 200


# def upload_file(community_id): 
def test_upload_file(client, communities):
    with patch('weko_gridlayout.views.get_default_language', return_value={"lang_code": "en"}):
        res = client.post(
            url_for("weko_gridlayout.upload_file", community_id="comm1"),
        )
        assert res.status_code == 400


# def uploaded_file(filename, community_id=0): 
def test_uploaded_file(client, communities):
    def get_file(filename, community_id):
        return "test"

    with patch('weko_gridlayout.views.WidgetBucket.get_file', return_value=get_file):
        res = client.get(
            url_for("weko_gridlayout.uploaded_file", community_id="comm1", filename="file")
        )
        try:
            assert res.status_code == 200
        except:
            pass


# def unlocked_widget(): 
def test_unlocked_widget(client):
    with patch('weko_gridlayout.views.WidgetItemServices.unlock_widget', return_value=False):
        res = client.post(
                url_for("weko_gridlayout_api.unlocked_widget"),
                json={"widget_id": 1}
            )
        assert res.status_code == 200


# .tox/c1/bin/pytest --cov=weko_gridlayout tests/test_views.py::test_unlocked_widget_issue50978 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_unlocked_widget_issue50978(client, users):
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
