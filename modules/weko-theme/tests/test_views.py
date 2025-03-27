import json
import pytest
from mock import patch, MagicMock
from flask import current_app, make_response, request
from flask_login import current_user
from flask import url_for

from weko_admin.models import SiteInfo
from invenio_accounts.testutils import login_user_via_session
from weko_theme import WekoTheme
from weko_theme.views import (
    index,
    edit,
    get_default_search_setting,
    get_init_display_setting
)

# def index():
# .tox/c1/bin/pytest --cov=weko_theme tests/test_views.py::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-theme/.tox/c1/tmp
def test_index(i18n_app, users):
    WekoTheme(i18n_app)

    with i18n_app.test_client() as client:
        res = client.get(url_for("weko_theme.index"))
        assert res.status_code == 200


# def edit():
# .tox/c1/bin/pytest --cov=weko_theme tests/test_views.py::test_edit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-theme/.tox/c1/tmp
def test_edit(i18n_app, users):
    site_info = MagicMock()
    site_info.favicon = "favicon,favicon"
    site_info.ogp_image = "ogp_image"
    WekoTheme(i18n_app)

    with i18n_app.test_client() as client:
        with patch('weko_theme.views.SiteInfo.get', return_value=site_info):
            # Exception coverage
            try:
                client.get(url_for("weko_theme.edit"))
            except:
                pass

        res = client.get(url_for("weko_theme.edit"))
        assert res.status_code == 200


# def get_default_search_setting():
def test_get_default_search_setting(i18n_app, users):
    with i18n_app.test_client() as client:
        WekoTheme(i18n_app)
        res = client.get(url_for("weko_theme.get_default_search_setting"))
        assert res.status_code == 200

# .tox/c1/bin/pytest --cov=weko_theme tests/test_views.py::test_get_site_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-theme/.tox/c1/tmp
#def get_site_info(site_info)
def test_get_site_info(i18n_app, db):
    WekoTheme(i18n_app)
    assert "get_site_info" in current_app.jinja_env.filters.keys()
    
    from weko_admin.models import SiteInfo
    with i18n_app.test_request_context("/test_request"):
        # not exist favicon, ogp_image, prefix
        siteinfo1 = SiteInfo(
            copy_right="test_copy_right1",
            description="test site info1.",
            keyword="test keyword1",
            favicon_name="test favicon name1",
            site_name=[{"name":"name1","language":"en","index":"0"}],
            notify=[{"notify_name":"notify1","language":"en"}],
            ogp_image_name="test ogp image name1"
        )
        db.session.add(siteinfo1)
        db.session.commit()
        test = {
            "title": "name1",
            "login_instructions":"notify1",
            "site_name":[{"name":"name1","language":"en","index":"0"}],
            "description":"test site info1.",
            "copy_right": "test_copy_right1",
            "keyword": "test keyword1",
            "favicon": "",
            "ogp_image": "",
            "url": "http://TEST_SERVER/test_request",
            "notify": [{"notify_name":"notify1","language":"en"}],
            "enable_notify": False,
            "google_tracking_id_user": ""
        }
        result = current_app.jinja_env.filters["get_site_info"](siteinfo1)
        assert result == test
        SiteInfo.query.delete()
        db.session.commit()
        
        siteinfo2 = SiteInfo(
            copy_right="test_copy_right2",
            description="test site info2.",
            keyword="test keyword2",
            favicon_name="test favicon name2",
            favicon="data:image/x-icon;base64,/static/favicon.ico",
            site_name=[{"name":"name2","language":"en","index":"0"}],
            notify=[{"notify_name":"notify2","language":"en"}],
            ogp_image_name="test ogp image name2",
            ogp_image="/static/ogp.ico",
            google_tracking_id_user="12345"
        )
        db.session.add(siteinfo2)
        db.session.commit()
        test = {
            "title": "name2",
            "login_instructions":"notify2",
            "site_name":[{"name":"name2","language":"en","index":"0"}],
            "description":"test site info2.",
            "copy_right": "test_copy_right2",
            "keyword": "test keyword2",
            "favicon": "http://TEST_SERVER/api/admin/favicon",
            "ogp_image": "http://TEST_SERVER/api/admin/ogp_image",
            "url": "http://TEST_SERVER/test_request",
            "notify": [{"notify_name":"notify2","language":"en"}],
            "enable_notify": False,
            "google_tracking_id_user": "12345"
        }
        result = current_app.jinja_env.filters["get_site_info"](siteinfo2)
        assert result == test

# def get_init_display_setting(settings):
def test_get_init_display_setting(i18n_app, users):
    with i18n_app.test_client() as client:
        WekoTheme(i18n_app)
        get_init_display_setting({})