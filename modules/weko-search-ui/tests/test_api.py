import json
import pytest
from flask import current_app, make_response, request
from flask_login import current_user
from mock import patch, MagicMock

from weko_admin.models import SearchManagement
from weko_search_ui.api import (
    SearchSetting,
    get_search_detail_keyword,
    get_childinfo,
    escape_str
)


## class SearchSetting(object):
# get_results_setting(cls):
def test_get_results_setting(i18n_app, users, db, app):
    from sqlalchemy.sql import func
    
    test_1 = SearchManagement(
        id=1,
        default_dis_sort_index="id",
        sort_setting={
            "allow": [
                {
                    "id": "_rfind"
                }
            ]
        }
    )
    
    assert SearchSetting.get_results_setting()[0] == app.config['RECORDS_REST_SORT_OPTIONS']
    assert SearchSetting.get_results_setting()[1] == 20

    db.session.add(test_1)
    db.session.commit()

    assert SearchSetting.get_results_setting()[0] != app.config['RECORDS_REST_SORT_OPTIONS']
    assert SearchSetting.get_results_setting()[1] == 20

# get_default_sort(cls, search_type, root_flag=False):
def test_get_default_sort(i18n_app, users, db, app):
    from sqlalchemy.sql import func
    from weko_admin import config as ad_config
    
    test_1 = SearchManagement(
        id=1,
        default_dis_sort_index=json.dumps({"custom_sort": "custom_sort"}),
        sort_setting={
            "allow": [
                {
                    "id": "_rfind"
                }
            ]
        },
        default_dis_sort_keyword=json.dumps({"custom_sort": "custom_sort"})
    )
    
    app.config["WEKO_SEARCH_TYPE_KEYWORD"] = "keyword"

    sort_key_str = ad_config.WEKO_ADMIN_MANAGEMENT_OPTIONS["dlt_keyword_sort_selected"]
    assert SearchSetting.get_default_sort(root_flag=True, search_type="keyword")[0] in sort_key_str

    app.config["WEKO_SEARCH_TYPE_KEYWORD"] = "not keyword"

    sort_key_str = ad_config.WEKO_ADMIN_MANAGEMENT_OPTIONS["dlt_index_sort_selected"]
    assert SearchSetting.get_default_sort(root_flag=True, search_type="keyword")[0] in sort_key_str

    db.session.add(test_1)
    db.session.commit()

    app.config["WEKO_SEARCH_TYPE_KEYWORD"] = "keyword"

    sort_key_str = ad_config.WEKO_ADMIN_MANAGEMENT_OPTIONS["dlt_keyword_sort_selected"]
    assert SearchSetting.get_default_sort(root_flag=True, search_type="keyword")[0] in sort_key_str

    app.config["WEKO_SEARCH_TYPE_KEYWORD"] = "not keyword"

    sort_key_str = ad_config.WEKO_ADMIN_MANAGEMENT_OPTIONS["dlt_index_sort_selected"]
    assert SearchSetting.get_default_sort(root_flag=True, search_type="keyword")[0] in sort_key_str

# get_sort_key(cls, key_str):
def test_get_sort_key(i18n_app, users, app):
    sort_key = app.config['RECORDS_REST_SORT_OPTIONS']['test-weko']['test-weko']['fields'][0]

    assert SearchSetting.get_sort_key(key_str="test-weko") == sort_key
    assert SearchSetting.get_sort_key(key_str="not-test-weko") != sort_key

# get_custom_sort(cls, index_id, sort_type):
def test_get_custom_sort(i18n_app, users, indices):
    index_id = 33

    assert SearchSetting.get_custom_sort(index_id, sort_type="asc")[0]['_script']['order'] == 'asc'
    assert SearchSetting.get_custom_sort(index_id, sort_type="asc")[1]['_created']['order'] == 'desc'
    assert SearchSetting.get_custom_sort(index_id, sort_type="desc")[0]['_script']['order'] == 'desc'
    assert SearchSetting.get_custom_sort(index_id, sort_type="desc")[1]['_created']['order'] == 'asc'

# get_nested_sorting(cls, key_str):
def test_get_nested_sorting(i18n_app, users, app):
    key_str = "test-weko"
    check_key = app.config['RECORDS_REST_SORT_OPTIONS'][key_str][key_str]['nested']

    assert SearchSetting.get_nested_sorting(key_str) == check_key


# def get_search_detail_keyword(str):
def test_get_search_detail_keyword(i18n_app, users, db):
    from sqlalchemy.sql import func
    
    test_1 = SearchManagement(
        id=1,
        default_dis_sort_index=json.dumps({"custom_sort": "custom_sort"}),
        sort_setting={
            "allow": [
                {
                    "id": "_rfind"
                }
            ]
        },
        default_dis_sort_keyword=json.dumps({"custom_sort": "custom_sort"})
    )
    data_1 = [[1, 2], [3, 4]]
    data_2 = [{
        "id": 1,
        "parent_name": "test"
    }]

    assert isinstance(get_search_detail_keyword("str"), str)
    assert len(json.loads(get_search_detail_keyword("str")).get('condition_setting')) > 0

    db.session.add(test_1)
    db.session.commit()

    with patch("weko_records.utils.get_keywords_data_load", return_value=data_1):
        with patch("weko_search_ui.api.get_childinfo", return_value=data_2):
            assert len(json.loads(get_search_detail_keyword("str")).get('condition_setting')) <= 0

# def get_childinfo(index_tree, result_list=[], parename=""):
def test_get_childinfo(i18n_app, users):
    index_tree = {
        "pid": 1,
        "cid": 1,
        "name": "testIndexThree",
        "parent": "0",
        "children": [44],
    }

    assert isinstance(get_childinfo(index_tree), list)

    index_tree["pid"] = 0

    assert isinstance(get_childinfo(index_tree), list)
    assert len(get_childinfo(index_tree)) > 1

# def escape_str(s):
def test_escape_str(i18n_app, users):
    s = "\str"

    assert len(escape_str(s)) == len(s) + 1


