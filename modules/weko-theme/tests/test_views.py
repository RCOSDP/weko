import json
import pytest
from flask import current_app, make_response, request
from flask_login import current_user
from mock import patch

from weko_admin.models import SiteInfo
from weko_theme.views import (
    index,
    edit,
    get_default_search_setting,
    get_site_info,
    get_init_display_setting
)


# def index():
# def test_index(i18n_app, users):
#     with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
#         assert index()


# def edit():
# def test_edit(i18n_app, users):
#     with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
#         assert edit()


# def get_default_search_setting():
def test_get_default_search_setting(i18n_app, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert get_default_search_setting()


# def get_site_info(site_info):
def test_get_site_info(i18n_app, users):
    site_info = SiteInfo.get()

    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert get_site_info(site_info)


# def get_init_display_setting(settings):
def test_get_init_display_setting(i18n_app, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert get_init_display_setting("settings")