from re import L

import pytest
from werkzeug import ImmutableMultiDict
from werkzeug.datastructures import CombinedMultiDict

from weko_search_ui.query import default_search_factory


# def get_item_type_aggs(search_index):
def test_get_item_type_aggs(i18n_app, users, client_request_args, db_records2):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert test.get_item_type_aggs()

# def get_permission_filter(index_id: str = None):


# def default_search_factory(self, search, query_parser=None, search_type=None):


# def item_path_search_factory(self, search, index_id=None):


# def check_admin_user():


# def opensearch_factory(self, search, query_parser=None):


# def item_search_factory(


# def feedback_email_search_factory(self, search):


