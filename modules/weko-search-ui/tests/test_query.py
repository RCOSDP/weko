import pytest
from re import L
from mock import patch
from werkzeug import ImmutableMultiDict
from werkzeug.datastructures import CombinedMultiDict

from weko_search_ui.query import (
    get_item_type_aggs,
    get_permission_filter,
    default_search_factory,
    item_path_search_factory,
    check_admin_user,
    opensearch_factory,
    item_search_factory,
    feedback_email_search_factory
)


# def get_item_type_aggs(search_index):
def test_get_item_type_aggs(i18n_app, users, client_request_args, db_records2, records):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert not get_item_type_aggs("test-weko")


# def get_permission_filter(index_id: str = None):
def test_get_permission_filter(i18n_app, users, client_request_args, indices):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert get_permission_filter(33)


# def default_search_factory(self, search, query_parser=None, search_type=None):
def test_default_search_factory(i18n_app, users, client_request_args, db_records2, records):
    search = records
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert not default_search_factory(self=None, search=search)


# def item_path_search_factory(self, search, index_id=None):


# def check_admin_user():


# def opensearch_factory(self, search, query_parser=None):


# def item_search_factory(


# def feedback_email_search_factory(self, search):
