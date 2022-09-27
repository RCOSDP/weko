import json
import pytest
from flask import current_app, make_response, request
from flask_login import current_user
from mock import patch

from weko_search_ui.views import (
    search,
    opensearch_description,
    journal_detail,
    search_feedback_mail_list,
    get_child_list,
    get_path_name_dict,
    gettitlefacet,
    get_last_item_id
)


# def search(): ~ jinja2.exceptions.TemplateNotFound: weko_theme/page.html
def test_search(i18n_app, users, db_register, index_style):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert search()


# def opensearch_description():
def test_opensearch_description(i18n_app, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert opensearch_description()


# def journal_detail(index_id=0):
def test_journal_detail(i18n_app, users, indices):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert journal_detail(33)


# def search_feedback_mail_list():
def test_search_feedback_mail_list(i18n_app, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert search_feedback_mail_list()


# def get_child_list(index_id=0):
def test_get_child_list(i18n_app, users, indices):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert get_child_list(33)


# def get_path_name_dict(path_str=""):
def test_get_path_name_dict(i18n_app, users, indices):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert get_path_name_dict('33_44')


# def gettitlefacet():
def test_gettitlefacet(i18n_app, users, facet_search_setting):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert gettitlefacet()


# def get_last_item_id():
def test_get_last_item_id(i18n_app, users, db_activity):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert get_last_item_id()
