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
    get_site_info,
    get_init_display_setting
)

# def index():
def test_index(i18n_app, users):
    WekoTheme(i18n_app)

    with i18n_app.test_client() as client:
        res = client.get(url_for("weko_theme.index"))
        assert res.status_code == 200


# def edit():
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


# def get_init_display_setting(settings):
def test_get_init_display_setting(i18n_app, users):
    with i18n_app.test_client() as client:
        WekoTheme(i18n_app)
        get_init_display_setting({})