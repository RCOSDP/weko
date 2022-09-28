import json
import pytest
from flask import current_app, make_response, request
from flask_login import current_user
from mock import patch

from weko_theme.utils import (
    get_weko_contents,
    get_community_id,
    get_design_layout,
    has_widget_design,
    MainScreenInitDisplaySetting
)


# def get_weko_contents(getargs):
def test_get_weko_contents(i18n_app, users, client_request_args, communities,redis_connect):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert get_weko_contents('comm1')


# def get_community_id(getargs):
def test_get_community_id(i18n_app, users, client_request_args, communities):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert get_community_id(request.args)


# def get_design_layout(repository_id):
def test_get_design_layout(i18n_app, users, client_request_args, communities):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert get_design_layout('Root Index')


# def has_widget_design(repository_id, current_language):
def test_has_widget_design(i18n_app, users, client_request_args, communities):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert not has_widget_design('Root Index', 'en')


# class MainScreenInitDisplaySetting:
def test_get_init_display_setting(i18n_app, users, client_request_args, communities):
    assert MainScreenInitDisplaySetting.get_init_display_setting()
