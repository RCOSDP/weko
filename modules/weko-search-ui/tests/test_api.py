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

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_api.py::test_get_search_detail_keyword -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
# def get_search_detail_keyword(str):
def test_get_search_detail_keyword(i18n_app, users, db,redis_connect):
    from weko_records.models import ItemTypeName,ItemType
    from weko_index_tree.models import Index
    names = ["test_itemtype01", "test's itemtype02",""]
    redis_connect.delete("index_tree_view_127.0.0.1_en")
    for i, name in enumerate(names):
        id = i+1
        item_type_name = ItemTypeName(id=id,name=name)
        db.session.add(item_type_name)
        item_type = ItemType(name_id=id,schema={},form={},render={},tag=1)
        db.session.add(item_type)
        db.session.commit()
    [{
        "pid":"","cid":"","id":"","name":"","parent":"","children":[]
    }]
    db.session.add(Index(id=1,parent=0,position=0,index_name="test_index1",index_name_english="test_index1"))
    db.session.add(Index(id=2,parent=0,position=1,index_name="test_index2",index_name_english="test_index2"))
    db.session.add(Index(id=3,parent=2,position=0,index_name="test_index2_1",index_name_english="test_index2_1"))
    db.session.add(Index(id=4,parent=2,position=1,index_name="test_index'2_2",index_name_english="test_index'2_2"))
    db.session.commit()
    index_tree = [
        {"pid":0,"cid":1,"id":"1","name":"test_index1","children":[]},
        {
            "pid":0,"cid":2,"id":"2","name":"test_index2","children":[
                {"pid":2,"cid":3,"id":"3","name":"test_index2_1","parent":"2","children":[]},
                {"pid":2,"cid":4,"id":"4","name":"test_index&#39;2_2","parent":"2","children":[]}
            ]},
        {"pid":0,"cid":"","id":"5","name":"","chidren":[]}
    ]
    
    # not exist search_management
    with patch("weko_search_ui.api.Indexes.get_browsing_tree",return_value=index_tree):
        res = get_search_detail_keyword("")
    assert type(res) == str
    res = json.loads(res)
    assert len(res.get("condition_setting",[])) > 0
    for r in res.get("condition_setting",[]):
        if r.get("id") == "iid":
            assert r.get("check_val") == [{"checkStus":False,"contents":"test_index1","id":1},{"checkStus":False,"contents":"test_index2","id":2},{"checkStus":False,"contents":"test_index2/test_index2_1","id":3},{"checkStus":False,"contents":"test_index2/test_index&#39;2_2","id":4},{"checkStus":False,"contents":"","id":""}]
        if r.get("id") == "itemtype":
            assert r.get("check_val") == [{"checkStus":False,"contents":"test_itemtype01","id":"test_itemtype01"},{"checkStus":False,"contents":"test&#39;s itemtype02","id":"test&#39;s itemtype02"},{"checkStus":False,"contents":"","id":""}]
    
    # exist search_management
    search_management = SearchManagement(
        search_conditions=[
            {"id":"title","mapping":["title"],"contents":"","inputVal":"","inputType":"text","contents_value":{"en":"Title","ja":"タイトル"}},
            {"id":"iid","mapping":["iid"],"contents":"","inputVal":"","check_val":[],"inputType":"checkbox_list","contents_value":{"en":"Index","ja":"インデックス"}},
            {"id":"itemtype","mapping":["itemtype"],"contents":"","inputVal":"","check_val":[],"inputType":"checkbox_list","contents_value":{"en":"Item Type","ja":"アイテムタイプ"}}
        ]
    )
    db.session.add(search_management)
    db.session.commit()
    with patch("weko_search_ui.api.Indexes.get_browsing_tree",return_value=index_tree):
        res = get_search_detail_keyword("")
    assert type(res) == str
    test = {"condition_setting":[
        {"contents":"タイトル","contents_value":{"en":"Title","ja":"タイトル"},"id":"title","inputType":"text","inputVal":"","mapping":["title"]},
        {"check_val":[{"checkStus":False,"contents":"test_index1","id":1},{"checkStus":False,"contents":"test_index2","id":2},{"checkStus":False,"contents":"test_index2/test_index2_1","id":3},{"checkStus":False,"contents":"test_index2/test_index&#39;2_2","id":4},{"checkStus":False,"contents":"","id":""}],"contents":"インデックス","contents_value":{"en":"Index","ja":"インデックス"},"id":"iid","inputType":"checkbox_list","inputVal":"","mapping":["iid"]},
        {"check_val":[{"checkStus":False,"contents":"test_itemtype01","id":"test_itemtype01"},{"checkStus":False,"contents":"test&#39;s itemtype02","id":"test&#39;s itemtype02"},{"checkStus":False,"contents":"","id":""}],"contents":"アイテムタイプ","contents_value":{"en":"Item Type","ja":"アイテムタイプ"},"id":"itemtype","inputType":"checkbox_list","inputVal":"","mapping":["itemtype"]}
    ]}
    assert json.loads(res) == test
    
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


