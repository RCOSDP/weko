# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# weko-gridlayout is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""
import pytest
import json
import copy
from mock import patch, MagicMock, Mock
from datetime import datetime
from uuid import UUID
from io import BytesIO
from werkzeug.datastructures import FileStorage

from invenio_files_rest.models import Bucket, Location
from invenio_files_rest.errors import FileInstanceAlreadySetError, \
    FilesException, UnexpectedFileSizeError
from sqlalchemy.orm.exc import MultipleResultsFound    

from weko_gridlayout.utils import (
    get_widget_type_list,
    delete_item_in_preview_widget_item,
    convert_popular_data,
    update_general_item,
    update_menu_item,
    update_access_counter_item,
    update_new_arrivals_item,
    get_default_language,
    get_unregister_language,
    get_register_language,
    get_system_language,
    build_data,
    _escape_html_multi_lang_setting,
    build_data_setting,
    _build_access_counter_setting_data,
    _build_new_arrivals_setting_data,
    _build_notice_setting_data,
    _build_header_setting_data,
    build_multi_lang_data,
    convert_widget_data_to_dict,
    convert_widget_multi_lang_to_dict,
    convert_data_to_design_pack,
    convert_data_to_edit_pack,
    build_rss_xml,
    find_rss_value,
    get_rss_data_source,
    get_elasticsearch_result_by_date,
    validate_main_widget_insertion,
    get_widget_design_page_with_main,
    main_design_has_main_widget,
    has_main_contents_widget,
    get_widget_design_setting,
    compress_widget_response,
    delete_widget_cache,
    validate_upload_file,
    WidgetBucket,
)



# def get_widget_type_list():
def test_get_widget_type_list(i18n_app, db_register):
    assert get_widget_type_list()


# def delete_item_in_preview_widget_item(data_id, json_data):
def test_delete_item_in_preview_widget_item(i18n_app):
    data_id = {
        "label": "test",
        "widget_type": "test"
    }
    json_data = [{
        "name": "test",
        "type": "test"
    }]
    assert delete_item_in_preview_widget_item(data_id, json_data)


# def convert_popular_data(source_data, des_data):
def test_convert_popular_data(i18n_app):
    source_data = {
        "background_color": "test",
        "label_enable": "test",
        "theme": "test",
        "frame_border_color": "test",
        "border_style": "test",
        "label_text_color": "test",
        "label_color": "test",
    }
    des_data = {}
    # Doesn't return any value
    assert not convert_popular_data(source_data, des_data)


# def update_general_item(item, data_result):
def test_update_general_item(i18n_app):
    WEKO_GRIDLAYOUT_ACCESS_COUNTER_TYPE = "Access counter"
    WEKO_GRIDLAYOUT_NEW_ARRIVALS_TYPE = "New arrivals"
    WEKO_GRIDLAYOUT_MENU_WIDGET_TYPE = 'Menu'
    WEKO_GRIDLAYOUT_HEADER_WIDGET_TYPE = 'Header'
    item = {
        "name": "test",
        "type": "test",
        "multiLangSetting": "test",
    }
    data_result = {
        "label": "test",
        "widget_type": "test",
        "multiLangSetting": "test",
        "settings": {},
        "widget_type": WEKO_GRIDLAYOUT_ACCESS_COUNTER_TYPE
    }
    
    # Doesn't return any value
    with patch("weko_gridlayout.utils.convert_popular_data", return_value=""):
        with patch("weko_gridlayout.utils.update_access_counter_item", return_value=""):
            assert not update_general_item(item, data_result)
        with patch("weko_gridlayout.utils.update_new_arrivals_item", return_value=""):
            data_result["widget_type"] = WEKO_GRIDLAYOUT_NEW_ARRIVALS_TYPE
            assert not update_general_item(item, data_result)
        with patch("weko_gridlayout.utils.update_menu_item", return_value=""):
            data_result["widget_type"] = WEKO_GRIDLAYOUT_MENU_WIDGET_TYPE
            assert not update_general_item(item, data_result)
        with patch("weko_gridlayout.utils._build_header_setting_data", return_value=""):
            data_result["widget_type"] = WEKO_GRIDLAYOUT_HEADER_WIDGET_TYPE
            assert not update_general_item(item, data_result)


# def update_menu_item(item, data_result):
def test_update_menu_item(i18n_app):
    item = MagicMock()
    data_result = MagicMock()

    # Doesn't return any value
    assert not update_menu_item(item, data_result)


# def update_access_counter_item(item, data_result):
# .tox/c1/bin/pytest --cov=weko_gridlayout tests/test_utils.py::test_update_access_counter_item -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-gridlayout/.tox/c1/tmp
def test_update_access_counter_item(i18n_app):
    
    item = {
        'x': 2, 'y': 0, 'width': 2, 'height': 6, 
        'name': 'test_counter01', 
        'id': 'test_community05', 
        'type': 'Access counter', 
        'widget_id': 1, 
        'background_color': '#FFFFFF', 'label_enable': True, 'theme': 'default', 'frame_border_color': '#DDDDDD', 
        'border_style': 'solid', 'label_text_color': '#333333', 'label_color': '#F5F5F5', 
        'access_counter': '11', 
        'following_message': 'foll', 
        'other_message': 'other', 
        'preceding_message': 'pre', 
        'count_start_date': '2024-02-10',
        'multiLangSetting': {
            'en': {
                'label': 'test_conter06', 
                'description': {
                    'preceding_message': 'pre', 
                    'following_message': 'foll', 
                    'other_message': 'other', 
                    'access_counter': '12',
                    'count_start_date': '2024-02-10'
                }
            }
        }, 
        'created_date': '2024-03-19'
    } 
    data_result = {'access_counter': '14', 'count_start_date': '2024-02-14', 'preceding_message': 'pre_1', 'following_message': 'foll_1'}
    update_access_counter_item(item, data_result)
    assert item == {
        'x': 2, 'y': 0, 'width': 2, 'height': 6, 
        'name': 'test_counter01', 
        'id': 'test_community05', 
        'type': 'Access counter', 
        'widget_id': 1, 
        'background_color': '#FFFFFF', 'label_enable': True, 'theme': 'default', 'frame_border_color': '#DDDDDD', 
        'border_style': 'solid', 'label_text_color': '#333333', 'label_color': '#F5F5F5', 
        'access_counter': '14', 
        'following_message': 'foll_1', 
        'other_message': None, 
        'preceding_message': 'pre_1', 
        'count_start_date': '2024-02-14',
        'multiLangSetting': {
            'en': {
                'label': 'test_conter06', 
                'description': {
                    'preceding_message': 'pre', 
                    'following_message': 'foll', 
                    'other_message': 'other', 
                    'access_counter': '12',
                    'count_start_date': '2024-02-10'
                }
            }
        }, 
        'created_date': '2024-03-19'
    } 


# def update_new_arrivals_item(item, data_result):
def test_update_new_arrivals_item(i18n_app):
    item = MagicMock()
    data_result = MagicMock()

    # Doesn't return any value
    assert not update_new_arrivals_item(item, data_result)


# def get_default_language():
def test_get_default_language(i18n_app, admin_lang_settings):
    assert get_default_language()


# def get_unregister_language():
def test_get_unregister_language(i18n_app, admin_lang_settings):
    assert get_unregister_language()


# def get_register_language():
def test_get_register_language(i18n_app, admin_lang_settings):
    assert get_register_language()


# def get_system_language():
def test_get_system_language(i18n_app, admin_lang_settings):
    assert get_system_language()
def test_get_system_language_2(i18n_app):
    # For exception coverage
    assert get_system_language()


# def build_data(data):
def test_build_data(i18n_app):
    data = MagicMock()
    with patch("weko_gridlayout.utils.build_data_setting", return_value=""):
        assert build_data(data)


# def _escape_html_multi_lang_setting(multi_lang_setting: dict):
def test__escape_html_multi_lang_setting(i18n_app):
    multi_lang_setting = {
        "a": 1,
        "b": {"c": 2}
    }
    # Doesn't return any value
    assert not _escape_html_multi_lang_setting(multi_lang_setting)


# def build_data_setting(data):
def test_build_data_setting(i18n_app):
    WEKO_GRIDLAYOUT_ACCESS_COUNTER_TYPE = "Access counter"
    WEKO_GRIDLAYOUT_NEW_ARRIVALS_TYPE = "New arrivals"
    WEKO_GRIDLAYOUT_NOTICE_TYPE = "Notice"
    WEKO_GRIDLAYOUT_MENU_WIDGET_TYPE = 'Menu'
    WEKO_GRIDLAYOUT_HEADER_WIDGET_TYPE = 'Header'
    with patch("weko_gridlayout.utils.convert_popular_data", return_value=""):
        data = {
            "widget_type": WEKO_GRIDLAYOUT_ACCESS_COUNTER_TYPE, 
            "settings": {
                "menu_orientation": "test",
                "menu_bg_color": "test",
                "menu_active_bg_color": "test",
                "menu_default_color": "test",
                "menu_active_color": "test",
                "menu_show_pages": "test",
            }
        }
        with patch("weko_gridlayout.utils._build_access_counter_setting_data", return_value=""):
            # Doesn't return any value
            assert not build_data_setting(data)

        with patch("weko_gridlayout.utils._build_new_arrivals_setting_data", return_value=""):
            data["widget_type"] = WEKO_GRIDLAYOUT_NEW_ARRIVALS_TYPE
            # Doesn't return any value
            assert not build_data_setting(data)

        with patch("weko_gridlayout.utils._build_notice_setting_data", return_value=""):
            data["widget_type"] = WEKO_GRIDLAYOUT_NOTICE_TYPE
            # Doesn't return any value
            assert not build_data_setting(data)
        
        data["widget_type"] = WEKO_GRIDLAYOUT_MENU_WIDGET_TYPE
        assert build_data_setting(data)

        with patch("weko_gridlayout.utils._build_header_setting_data", return_value=""):       
            data["widget_type"] = WEKO_GRIDLAYOUT_HEADER_WIDGET_TYPE
            # Doesn't return any value
            assert not build_data_setting(data)


# def _build_access_counter_setting_data(result, setting):
# .tox/c1/bin/pytest --cov=weko_gridlayout tests/test_utils.py::test__build_access_counter_setting_data -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-gridlayout/.tox/c1/tmp
def test__build_access_counter_setting_data(i18n_app):
    result = {
        'background_color': '#FFFFFF', 
        'label_enable': True, 
        'theme': 'default', 
        'frame_border_color': '#DDDDDD', 
        'border_style': 'solid', 
        'label_text_color': '#333333', 
        'label_color': '#F5F5F5'
    }
    setting = {
        'preceding_message': 'pre', 
        'following_message': 'foll', 
        'other_message': 'other', 
        'access_counter': 10,
        'count_start_date': '2024-04-10'
    }
    _build_access_counter_setting_data(result, setting)
    from flask import Markup
    test = {
        'background_color': '#FFFFFF', 
        'label_enable': True, 
        'theme': 'default', 
        'frame_border_color': '#DDDDDD', 
        'border_style': 'solid', 
        'label_text_color': '#333333', 
        'label_color': '#F5F5F5',
        'preceding_message': Markup('pre'), 
        'following_message': Markup('foll'), 
        'other_message': Markup('other'), 
        'access_counter': Markup(10),
        'count_start_date': Markup('2024-04-10')
    }
    assert result == test


# def _build_new_arrivals_setting_data(result, setting):
def test__build_new_arrivals_setting_data(i18n_app):
    result = {}
    setting = {
        "new_dates": "test",
        "display_result": "test",
        "rss_feed": "test",
    }
    # Doesn't return any value
    assert not _build_new_arrivals_setting_data(result, setting)


# def _build_notice_setting_data(result, setting):
def test__build_notice_setting_data(i18n_app):
    result = {}
    setting = {
        "setting": "test",
        "read_more": "test",
    }
    # Doesn't return any value
    assert not _build_notice_setting_data(result, setting)


# def _build_header_setting_data(result, setting):
def test__build_header_setting_data(i18n_app):
    result = {}
    setting = {
        "fixedHeaderBackgroundColor": "test",
        "fixedHeaderTextColor": "test",
    }
    # Doesn't return any value
    assert not _build_header_setting_data(result, setting)


# def build_multi_lang_data(widget_id, multi_lang_json):
def test_build_multi_lang_data(i18n_app):
    widget_id = 1
    multi_lang_json = {
        "test": {"label": 1, "description": 2}
    }
    
    assert build_multi_lang_data(widget_id, multi_lang_json)

    multi_lang_json = {}
    # Doesn't return any value
    assert not build_multi_lang_data(widget_id, multi_lang_json)


# def convert_widget_data_to_dict(widget_data):
def test_convert_widget_data_to_dict(i18n_app):
    def test_func():
        return
    widget_data = MagicMock()
    widget_data.settings = {}
    widget_data.widget_id = "test"
    widget_data.repository_id = "test"
    widget_data.widget_type = "test"
    widget_data.is_enabled = "test"
    widget_data.is_deleted = "test"
    widget_data.updated = MagicMock()
    widget_data.updated.timestamp = test_func
    assert convert_widget_data_to_dict(widget_data)


# def convert_widget_multi_lang_to_dict(multi_lang_data):
def test_convert_widget_multi_lang_to_dict(i18n_app):
    multi_lang_data = MagicMock()
    multi_lang_data.description_data = json.dumps({"test": "test"})
    multi_lang_data.id = "test"
    multi_lang_data.widget_id = "test"
    multi_lang_data.lang_code = "test"
    multi_lang_data.label = "test"
    assert convert_widget_multi_lang_to_dict(multi_lang_data)


# def convert_data_to_design_pack(widget_data, list_multi_lang_data):
def test_convert_data_to_design_pack(i18n_app):
    widget_data = {
        "widget_id": "test",
        "repository_id": "test",
        "widget_type": "test",
        "is_enabled": "test",
        "is_deleted": "test",
        "updated": "test",
        "settings": {"multiLangSetting": ""},
    }
    list_multi_lang_data = ["test"]
    return_data = {
        "label": "test",
        "description_data": "test",
        "lang_code": "test",
    }
    with patch("weko_gridlayout.utils.convert_widget_multi_lang_to_dict", return_value=return_data):
        assert convert_data_to_design_pack(widget_data, list_multi_lang_data)

    widget_data = {}
    assert not convert_data_to_design_pack(widget_data, list_multi_lang_data)



# def convert_data_to_edit_pack(data):
# .tox/c1/bin/pytest --cov=weko_gridlayout tests/test_utils.py::test_convert_data_to_edit_pack -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-gridlayout/.tox/c1/tmp
def test_convert_data_to_edit_pack():
    data_tmp = {
        "widget_id":1,
        "repository_id": "test_repository01",
        "is_enabled":True, "is_deleted": False,
        "updated": 1710792308.342129,
        "settings":{
            "background_color": "#FFFFFF","label_enable": True,"theme": "default","frame_border_color": "#DDDDDD",
            "border_style": "solid","label_text_color": "#333333","label_color": "#F5F5F5",
            "access_counter":10,
            "preceding_message":"test_pre",
            "following_message": "test_follow",
            "other_message": "test_other",
            "count_start_date": "2024-01-11",
            "new_dates": "test_new_dates",
            "display_result": "test_display_result",
            "rss_feed": "test_rss",
            "menu_orientation":"test_menu_orientation",
            "menu_bg_color":"test_color",
            "fixedHeaderBackgroundColor":"test_fixedHeaderBackgroundColor",
            "multiLangSetting":"test_multi_lang_settings"
        }
    }
    test_tmp = {
        "background_color": "#FFFFFF",
        "label_enable": True,
        "theme": "default",
        "frame_border_color": "#DDDDDD",
        "border_style": "solid",
        "label_text_color": "#333333",
        "label_color": "#F5F5F5",
        "widget_id": 1,
        "is_enabled": True,
        "enable": True,
        "multiLangSetting": "test_multi_lang_settings",
        "repository_id": "test_repository01",
        "updated": 1710792308.342129,
    }
    
    # widget_type = Access counter
    data = json.loads(json.dumps(data_tmp))
    data["widget_type"] = "Access counter"
    result = convert_data_to_edit_pack(data)
    test = json.loads(json.dumps(test_tmp))
    test["widget_type"] = "Access counter"
    test["settings"] = {
        "access_counter": 10,
        "preceding_message": "test_pre",
        "following_message": "test_follow",
        "other_message": "test_other",
        "count_start_date": "2024-01-11",
    }
    assert result == test
    
    # widget_type = New arrivals
    data = json.loads(json.dumps(data_tmp))
    data["widget_type"] = "New arrivals"
    result = convert_data_to_edit_pack(data)
    test = json.loads(json.dumps(test_tmp))
    test["widget_type"] = "New arrivals"
    test["settings"] = {
        "new_dates": "test_new_dates",
        "display_result": "test_display_result",
        "rss_feed": "test_rss",
    }
    assert result == test
    
    # widget_type = Menu
    data = json.loads(json.dumps(data_tmp))
    data["widget_type"] = "Menu"
    result = convert_data_to_edit_pack(data)
    test = json.loads(json.dumps(test_tmp))
    test["widget_type"] = "Menu"
    test["settings"] = {
        "menu_orientation":"test_menu_orientation",
        "menu_bg_color":"test_color",
        "menu_active_bg_color": None,
        "menu_default_color": None,
        "menu_active_color": None,
        "menu_show_pages": None
    }
    assert result == test
    
    # widget_type = Header
    data = json.loads(json.dumps(data_tmp))
    data["widget_type"] = "Header"
    result = convert_data_to_edit_pack(data)
    test = json.loads(json.dumps(test_tmp))
    test["widget_type"] = "Header"
    test["settings"] = {
        "fixedHeaderBackgroundColor": "test_fixedHeaderBackgroundColor",
        "fixedHeaderTextColor": None
    }
    assert result == test
    
# @pytest.mark.parametrize("data, result",[({}, None),
#     ({
#         "settings": {
#             "multiLangSetting": {
#                 "en": {
#                     "label": "for test"
#                 }},
#             "access_counter": "test access_counter",
#             "preceding_message": "test preceding_message",
#             "following_message": "test following_message",
#             "other_message": "test other_message"

#         },
#         "widget_id": 1,
#         "repository_id": "Root Index",
#         "widget_type": "Access counter",
#         "is_enabled": True},
#      {
#         "background_color": None,
#         "label_enable": None,
#         "theme": None,
#         "updated": None,
#         "frame_border_color": None,
#         "border_style": None,
#         "widget_id": 1,
#         "is_enabled": True,
#         "enable": True,
#         "multiLangSetting": {"en": {"label": "for test"}},
#         "repository_id": "Root Index",
#         "widget_type": "Access counter",
#         "settings": {"access_counter": "test access_counter",
#                     "preceding_message": "test preceding_message",
#                     "following_message": "test following_message",
#                     "other_message": "test other_message"}}),
#     ({
#         "settings": {
#             "multiLangSetting": {
#                 "en": {
#                     "label": "for test"
#                 }},
#             "new_dates": "test new_dates",
#             "display_result": "test display_result",
#             "rss_feed": "test rss_feed"
#         },
#         "widget_id": 1,
#         "repository_id": "Root Index",
#         "widget_type": "New arrivals",
#         "is_enabled": True},
#      {
#         "background_color": None,
#         "label_enable": None,
#         "theme": None,
#         "updated": None,
#         "frame_border_color": None,
#         "border_style": None,
#         "widget_id": 1,
#         "is_enabled": True,
#         "enable": True,
#         "multiLangSetting": {"en": {"label": "for test"}},
#         "repository_id": "Root Index",
#         "widget_type": "New arrivals",
#         "settings": {
#             "new_dates": "test new_dates",
#             "display_result": "test display_result",
#             "rss_feed": "test rss_feed"}}),
#     ({
#         "settings": {
#             "background_color": "#FFFFFF",
#             "label_enable": True,
#             "theme": "default",
#             "frame_border_color": "#DDDDDD",
#             "border_style": "solid",
#             "widget_id": 1,
#             "is_enabled": True,
#             "menu_orientation": "test menu_orientation",
#             "menu_bg_color": "test menu_bg_color",
#             "menu_active_bg_color": "test menu_active_bg_color",
#             "menu_default_color": "test menu_default_color",
#             "menu_active_color": "test menu_active_color",
#             "menu_show_pages": "test menu_show_pages"},
#         "widget_type": "Menu"},
#          {
#             "background_color": "#FFFFFF",
#             "label_color": None,
#             "label_enable": True,
#             "label_text_color": None,
#             "theme": "default",
#             "frame_border_color": "#DDDDDD",
#             "border_style": "solid",
#             "widget_id": 1,
#             "is_enabled": True,
#             "enable": True,
#             "multiLangSetting": None,
#             "repository_id": None,
#             "widget_type": "Menu",
#             "updated": None,
#             "settings": {
#                 "menu_orientation": "test menu_orientation",
#                 "menu_bg_color": "test menu_bg_color",
#                 "menu_active_bg_color": "test menu_active_bg_color",
#                 "menu_default_color": "test menu_default_color",
#                 "menu_active_color": "test menu_active_color",
#                 "menu_show_pages": "test menu_show_pages"}}),
#     ({
#         "settings": {
#             "background_color": "#FFFFFF",
#             "label_enable": True,
#             "theme": "default",
#             "frame_border_color": "#DDDDDD",
#             "border_style": "solid",
#             "widget_id": 1,
#             "is_enabled": True,
#             "fixedHeaderBackgroundColor": "#FFFFFF",
#             "fixedHeaderTextColor": "#000000"},
#         "widget_type": "Header"},
#      {
#             "background_color": "#FFFFFF",
#             "label_color": None,
#             "label_enable": True,
#             "label_text_color": None,
#             "theme": "default",
#             "frame_border_color": "#DDDDDD",
#             "border_style": "solid",
#             "widget_id": 1,
#             "is_enabled": True,
#             "enable": None,
#             "multiLangSetting": None,
#             "repository_id": None,
#             "widget_type": "Header",
#             "updated": None,
#             "settings": {
#                 "fixedHeaderBackgroundColor": "#FFFFFF",
#                 "fixedHeaderTextColor": "#000000"}}),
#     ({
#         "widget_type": "Free description",
#         "settings": {
#             "background_color": "#FFFFFF",
#             "label_enable": True,
#             "theme": "default",
#             "frame_border_color": "#DDDDDD",
#             "border_style": "solid",
#             "widget_id": 1,
#             "is_enabled": True,
#         }},
#         {
#             "background_color": "#FFFFFF",
#             "label_enable": True,
#             "theme": "default",
#             "frame_border_color": "#DDDDDD",
#             "border_style": "solid",
#             "label_text_color": None,
#             "label_color": None,
#             "widget_id": 1,
#             "is_enabled": True,
#             "enable": True,
#             "multiLangSetting": None,
#             "repository_id": None,
#             "widget_type": "Free description",
#             "updated": None,
#             "settings": {}}),
#     ])
# def test_convert_data_to_edit_pack(data, result):
#     data = data
#     res = convert_data_to_edit_pack(data)
#     assert res == result


# def build_rss_xml(data=None, index_id=0, page=1, count=20, term=0, lang=''):
def test_build_rss_xml(i18n_app, indices):
    assert build_rss_xml(index_id=33)
    assert build_rss_xml()
    with patch("weko_gridlayout.utils.find_rss_value", return_value=""):
        assert build_rss_xml(data=["test"])
    

# def find_rss_value(data, keyword):
keywords = [
    'title',
    'link',
    'seeAlso',
    'creator',
    'publisher',
    'sourceTitle',
    'issn',
    'volume',
    'issue',
    'pageStart',
    'pageEnd',
    'date',
    'description',
    '_updated',
    ''
]
@pytest.mark.parametrize('keyword', keywords)
def test_find_rss_value(i18n_app, keyword, item_type):

    data = {
        "_source": {
            "date": ["test"],
            "creator": {
                "familyName": ["test", "test"],
                "givenName": ["test", "test"]
            },
            "_item_metadata": {
                "item_title": "item_title",
                "control_number": "9999"
            }
        }
    }

    return_data = {
        "description.@attributes.descriptionType": "test",
        "description.@value": "test",
    }

    with patch("weko_gridlayout.utils.get_rss_data_source", return_value="Issued"):
        with patch("weko_records.api.Mapping.get_record", return_value="test"):
            with patch("weko_records.serializers.utils.get_mapping", return_value=return_data):
                find_rss_value(data, keyword) 
                                
                
                data2 = None
                assert find_rss_value(data2, keyword) == None

                if keyword == "creator":
                    data3 = copy.deepcopy(data)
                    data3["_source"]["creator"]["familyName"] = []
                    assert find_rss_value(data3, keyword) == ""

                    data4 = copy.deepcopy(data)
                    del data4["_source"]["creator"]
                    assert find_rss_value(data4, keyword) == ""

                if keyword == "issn":
                    data5 = copy.deepcopy(data)
                    data5["_source"]["sourceIdentifier"] = ["test"]
                    assert find_rss_value(data5, keyword) != ""
                
                if keyword == 'description':
                    item_map = {
                        "description.@attributes.descriptionType": "description.@attributes.descriptionType",
                        "description.@value": "description.@value"
                    }
                    data6 = copy.deepcopy(data)
                    data6["_source"]["description"] = ["test"]
                    data6["_source"]["_item_metadata"]["description"] = {
                        "attribute_value_mlt": "attribute_value_mlt"
                    }
                    with patch('weko_gridlayout.utils.Mapping.get_record', return_value=""):
                        with patch('weko_gridlayout.utils.get_mapping', return_value=item_map):
                            with patch('weko_gridlayout.utils.get_pair_value', return_value=[("Abstract", "Abstract")]):
                                assert find_rss_value(data6, keyword) != ""



                


# def get_rss_data_source(source, keyword):
def test_get_rss_data_source(i18n_app):
    source = {"test": ["test"]}
    keyword = "test"
    assert get_rss_data_source(source, keyword)
    source["test"] = "test"
    assert get_rss_data_source(source, keyword)
    source["test"] = None
    assert not get_rss_data_source(source, keyword)
    

# def get_elasticsearch_result_by_date(start_date, end_date):
def test_get_elasticsearch_result_by_date(i18n_app):
    from elasticsearch.exceptions import NotFoundError

    start_date = "2021-11-11"
    end_date = "2021-11-22"

    assert get_elasticsearch_result_by_date(start_date, end_date)

    with patch('weko_gridlayout.utils.item_search_factory', side_effect=NotFoundError('')):
        # Exception coverage ~ line 779
        try:
            get_elasticsearch_result_by_date(start_date, end_date)
        except:
            pass
    

# def validate_main_widget_insertion(repository_id, new_settings, page_id=0):
def test_validate_main_widget_insertion(i18n_app, widget_item):
    repository_id = 1
    new_settings = ""
    return_data = MagicMock()

    with patch("weko_gridlayout.utils.has_main_contents_widget", return_value=True):
        assert validate_main_widget_insertion(repository_id, new_settings)

    with patch("weko_gridlayout.models.WidgetDesignSetting.select_by_repository_id", return_value=return_data):
        assert validate_main_widget_insertion(repository_id, new_settings)

    main_settings = {
        "settings": []
    }

    with patch("weko_gridlayout.utils.has_main_contents_widget", return_value=True):
        with patch('weko_gridlayout.utils.get_widget_design_page_with_main', return_value=False):
            with patch('weko_gridlayout.utils.WidgetDesignSetting.select_by_repository_id', return_value=main_settings):
                with patch('weko_gridlayout.utils.WidgetDesignPage.get_by_id_or_none', return_value=False):
                 assert validate_main_widget_insertion(repository_id, new_settings)
    

# def get_widget_design_page_with_main(repository_id):
def test_get_widget_design_page_with_main(i18n_app):
    repository_id = 1
    mock_data = MagicMock()
    mock_data.settings = 9999
    
    with patch("weko_gridlayout.utils.WidgetDesignPage.get_by_repository_id", return_value=[mock_data]):
        with patch("weko_gridlayout.utils.has_main_contents_widget", return_value="test"):
            assert get_widget_design_page_with_main(repository_id) != None
    
    assert get_widget_design_page_with_main(repository_id=None) == None
    

# def main_design_has_main_widget(repository_id):
def test_main_design_has_main_widget(db_register):
    assert main_design_has_main_widget('Root Index')==True
    assert main_design_has_main_widget('test')==False
    assert main_design_has_main_widget('')==False


# def has_main_contents_widget(settings):


# def get_widget_design_setting(repository_id, current_language, page_id=None):
def test_get_widget_design_setting(i18n_app):
    with i18n_app.test_client():
        repository_id = "root"
        current_language = "en"

        def lower_func():
            return "gzip"

        def get_func(item):
            return "gzip"

        i18n_app.config['WEKO_GRIDLAYOUT_IS_COMPRESS_WIDGET'] = "test"
        i18n_app.config['WEKO_GRIDLAYOUT_WIDGET_PAGE_CACHE_KEY'] = "test"
        accept_encoding = MagicMock()
        accept_encoding.lower = lower_func
        
        headers = {
            "Accept-Encoding": accept_encoding,
            'Content-Encoding': "json"
        }

        request = MagicMock()
        request.headers = headers

        current_cache = MagicMock()
        current_cache.get = get_func

        with patch('weko_gridlayout.utils.request', request):
            with patch('weko_gridlayout.utils.current_cache', current_cache):
                assert get_widget_design_setting(
                    repository_id=repository_id,
                    current_language=current_language,
                    page_id="1"
                ) != None

                assert get_widget_design_setting(
                    repository_id=repository_id,
                    current_language=current_language,
                    page_id=0
                ) != None


# def compress_widget_response(response):
def test_compress_widget_response(i18n_app):
    def set_data(item):
        return item

    def get_data():
        return b'test'

    response = MagicMock()
    response.get_data = get_data
    response.set_data = set_data
    response.headers = {}

    assert compress_widget_response(response=response) != None


# def delete_widget_cache(repository_id, page_id=None):
def test_delete_widget_cache(i18n_app):
    repository_id = 1
    page_id = 1

    assert delete_widget_cache(repository_id=repository_id, page_id=page_id) == None


# def validate_upload_file(community_id: str): ~ ERROR
def test_validate_upload_file(i18n_app): 
    community_id = ""
    file_data = MagicMock()
    file_data.filename = "file"
    files = {
        "file": file_data
    }
    request = MagicMock()
    request.files = files

    def data_return(item):
        return item

    with patch("weko_gridlayout.utils.request", request):
        validate_upload_file(community_id=community_id)
    
    file_data.filename = ""
    files = {
        "file": file_data
    }
    request.files = files

    with patch("weko_gridlayout.utils.request", request):
        validate_upload_file(community_id=community_id)
    
    community_id = "0@9999"
    file_data.filename = "file"
    files = {
        "file": file_data
    }
    request.files = files

    with patch("weko_gridlayout.utils.request", request):
        validate_upload_file(community_id=community_id)


class TestWidgetBucket:
    # def __init__(self):

    # def initialize_widget_bucket(self):
    #         location = Location.get_default()
    #                         default_storage_class=storage_class)
    def test_initialize_widget_bucket(self, app):
        w = WidgetBucket()

        def get_func(key):
            return "key"
        
        def none_get_func(key):
            return None

        def get_default():
            return "get_default"
        
        bucket = MagicMock()
        bucket.query = MagicMock()
        bucket.query.get = get_func

        with patch('weko_gridlayout.utils.Bucket', bucket):
            # Exception coverage ~ line 971
            try:
                w.initialize_widget_bucket()
            except:
                pass
        
        bucket.query.get = none_get_func
        location = MagicMock()
        location.get_default = get_default

        with patch('weko_gridlayout.utils.Bucket', bucket):
            with patch('weko_gridlayout.utils.Location', location):
                with patch('weko_gridlayout.utils.db.session.add', return_value=""):
                    assert w.initialize_widget_bucket() == None

    
        
        
        
    # def __validate(self, file_stream, file_name, community_id="0", file_size=0):
    # def save_file(self, file_stream, file_name: str, mimetype: str,
    # .tox/c1/bin/pytest --cov=weko_gridlayout tests/test_utils.py::TestWidgetBucket::test_save_file -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-gridlayout/.tox/c1/tmp
    def test_save_file(self, app, db, location):
        bucket_id = app.config['WEKO_GRIDLAYOUT_BUCKET_UUID']
        bucket_id = UUID(bucket_id)
        storage_class = app.config[
                    'FILES_REST_DEFAULT_STORAGE_CLASS']
        location = Location.get_default()
        bucket = Bucket(id=bucket_id,
                            location=location,
                            default_storage_class=storage_class)
        db.session.add(bucket)
        img=FileStorage(filename='test.png', stream=BytesIO(b'test'))
        
        w = WidgetBucket()
        with app.test_request_context("/widget/uploads/test_comm@widget"):
            result = w.save_file(img, "test_file.png","image/png","test_comm@widget")
            test = {"status": True, "duplicated": False, "url": "/widget/uploaded/test_file.png/test_comm", "msg": "OK", "mimetype": "image/png", "file_name": "test_file.png"}
            assert result == test
            with patch("weko_gridlayout.utils.WidgetBucket._WidgetBucket__validate",
                       side_effect=FileInstanceAlreadySetError("The test_file.png file is alreasy exists")):
                result = w.save_file(img, "test_file.png","image/png","test_comm@widget")
                test = {"status": False, "duplicated": True, "url": "/widget/uploaded/test_file.png/test_comm", "msg": "The test_file.png file is alreasy exists", "mimetype": "image/png", "file_name": "test_file.png"}
                assert result == test
            with patch("weko_gridlayout.utils.WidgetBucket._WidgetBucket__validate",
                       side_effect=UnexpectedFileSizeError("10 is greater than the maximum value allowed (16777216).")):
                result = w.save_file(img, "test_file.png","image/png","test_comm@widget")
                test = {"status": False, "duplicated": False, "url": "", "msg": "10 is greater than the maximum value allowed (16777216).", "mimetype": "image/png", "file_name": "test_file.png"}
                assert result == test
                

    # def get_file(self, file_name, community_id=0):
    # .tox/c1/bin/pytest --cov=weko_gridlayout tests/test_utils.py::TestWidgetBucket::test_get_file -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-gridlayout/.tox/c1/tmp
    def test_get_file(self,app,widget_upload):
        w = WidgetBucket()
        obj = widget_upload["obj"]
        key = widget_upload["key"]
        assert key=='0_test.png'
        with app.test_request_context():
            ret = w.get_file("test.png")
            assert ret.status_code==200
            assert ret.headers['Content-length'] == str(obj.file.size)
        
        def none_get_func(key, value):
            return None

        with patch('weko_gridlayout.utils.ObjectVersion.get', none_get_func):
            # Exception coverage ~ line 1084
            try:
                w.get_file("test.png")
            except:
                pass