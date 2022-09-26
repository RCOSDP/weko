import json
import pytest
from flask import current_app, make_response, request
from flask_login import current_user
from mock import patch

from weko_search_ui.api import (
    SearchSetting,
    get_search_detail_keyword,
    get_childinfo,
    escape_str
)


## class SearchSetting(object):
# get_results_setting(cls):
def test_get_results_setting(i18n_app, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert SearchSetting.get_results_setting()

# get_default_sort(cls, search_type, root_flag=False):
def test_get_default_sort(i18n_app, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert SearchSetting.get_default_sort(search_type="keyword")

# get_sort_key(cls, key_str):
def test_get_sort_key(i18n_app, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert not SearchSetting.get_sort_key(key_str="test")

# get_custom_sort(cls, index_id, sort_type):
def test_get_custom_sort(i18n_app, users, indices):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert SearchSetting.get_custom_sort(index_id=33,sort_type="asc")
        assert SearchSetting.get_custom_sort(index_id=33,sort_type="desc")

# get_nested_sorting(cls, key_str): ~ AttributeError: 'NoneType' object has no attribute 'get'
def test_get_nested_sorting(i18n_app, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert SearchSetting.get_nested_sorting(key_str="test-weko")


# def get_search_detail_keyword(str):
def test_get_search_detail_keyword(i18n_app, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert get_search_detail_keyword("str")


# def get_childinfo(index_tree, result_list=[], parename=""):
def test_get_childinfo(i18n_app, users, indices):
    index_tree = {
        "pid": 1,
        "cid": 1,
        "name": "testIndexThree",
        "parent": "0",
        "children": [44],
    }

    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert get_childinfo(index_tree)


# def escape_str(s):
def test_escape_str(i18n_app, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert escape_str("str")


