# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# weko-gridlayout is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""
import pytest
from mock import patch, MagicMock, Mock
from datetime import datetime
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
    convert_data_to_edit_pack
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
def test_update_access_counter_item(i18n_app):
    item = MagicMock()
    data_result = MagicMock()

    # Doesn't return any value
    assert not update_access_counter_item(item, data_result)


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
# def build_data_setting(data):
# def _build_access_counter_setting_data(result, setting):
# def _build_new_arrivals_setting_data(result, setting):
# def _build_notice_setting_data(result, setting):
# def _build_header_setting_data(result, setting):
# def build_multi_lang_data(widget_id, multi_lang_json):
# def convert_widget_data_to_dict(widget_data):
# def convert_widget_multi_lang_to_dict(multi_lang_data):
# def convert_data_to_design_pack(widget_data, list_multi_lang_data):
# def convert_data_to_edit_pack(data):


@pytest.mark.parametrize("data, result",[({}, None),
    ({
        "settings": {
            "multiLangSetting": {
                "en": {
                    "label": "for test"
                }},
            "access_counter": "test access_counter",
            "preceding_message": "test preceding_message",
            "following_message": "test following_message",
            "other_message": "test other_message"

        },
        "widget_id": 1,
        "repository_id": "Root Index",
        "widget_type": "Access counter",
        "is_enabled": True},
     {
        "background_color": None,
        "label_enable": None,
        "theme": None,
        "updated": None,
        "frame_border_color": None,
        "border_style": None,
        "widget_id": 1,
        "is_enabled": True,
        "enable": True,
        "multiLangSetting": {"en": {"label": "for test"}},
        "repository_id": "Root Index",
        "widget_type": "Access counter",
        "settings": {"access_counter": "test access_counter",
                    "preceding_message": "test preceding_message",
                    "following_message": "test following_message",
                    "other_message": "test other_message"}}),
    ({
        "settings": {
            "multiLangSetting": {
                "en": {
                    "label": "for test"
                }},
            "new_dates": "test new_dates",
            "display_result": "test display_result",
            "rss_feed": "test rss_feed"
        },
        "widget_id": 1,
        "repository_id": "Root Index",
        "widget_type": "New arrivals",
        "is_enabled": True},
     {
        "background_color": None,
        "label_enable": None,
        "theme": None,
        "updated": None,
        "frame_border_color": None,
        "border_style": None,
        "widget_id": 1,
        "is_enabled": True,
        "enable": True,
        "multiLangSetting": {"en": {"label": "for test"}},
        "repository_id": "Root Index",
        "widget_type": "New arrivals",
        "settings": {
            "new_dates": "test new_dates",
            "display_result": "test display_result",
            "rss_feed": "test rss_feed"}}),
    ({
        "settings": {
            "background_color": "#FFFFFF",
            "label_enable": True,
            "theme": "default",
            "frame_border_color": "#DDDDDD",
            "border_style": "solid",
            "widget_id": 1,
            "is_enabled": True,
            "menu_orientation": "test menu_orientation",
            "menu_bg_color": "test menu_bg_color",
            "menu_active_bg_color": "test menu_active_bg_color",
            "menu_default_color": "test menu_default_color",
            "menu_active_color": "test menu_active_color",
            "menu_show_pages": "test menu_show_pages"},
        "widget_type": "Menu"},
         {
            "background_color": "#FFFFFF",
            "label_color": None,
            "label_enable": True,
            "label_text_color": None,
            "theme": "default",
            "frame_border_color": "#DDDDDD",
            "border_style": "solid",
            "widget_id": 1,
            "is_enabled": True,
            "enable": True,
            "multiLangSetting": None,
            "repository_id": None,
            "widget_type": "Menu",
            "updated": None,
            "settings": {
                "menu_orientation": "test menu_orientation",
                "menu_bg_color": "test menu_bg_color",
                "menu_active_bg_color": "test menu_active_bg_color",
                "menu_default_color": "test menu_default_color",
                "menu_active_color": "test menu_active_color",
                "menu_show_pages": "test menu_show_pages"}}),
    ({
        "settings": {
            "background_color": "#FFFFFF",
            "label_enable": True,
            "theme": "default",
            "frame_border_color": "#DDDDDD",
            "border_style": "solid",
            "widget_id": 1,
            "is_enabled": True,
            "fixedHeaderBackgroundColor": "#FFFFFF",
            "fixedHeaderTextColor": "#000000"},
        "widget_type": "Header"},
     {
            "background_color": "#FFFFFF",
            "label_color": None,
            "label_enable": True,
            "label_text_color": None,
            "theme": "default",
            "frame_border_color": "#DDDDDD",
            "border_style": "solid",
            "widget_id": 1,
            "is_enabled": True,
            "enable": None,
            "multiLangSetting": None,
            "repository_id": None,
            "widget_type": "Header",
            "updated": None,
            "settings": {
                "fixedHeaderBackgroundColor": "#FFFFFF",
                "fixedHeaderTextColor": "#000000"}}),
    ({
        "widget_type": "Free description",
        "settings": {
            "background_color": "#FFFFFF",
            "label_enable": True,
            "theme": "default",
            "frame_border_color": "#DDDDDD",
            "border_style": "solid",
            "widget_id": 1,
            "is_enabled": True,
        }},
        {
            "background_color": "#FFFFFF",
            "label_enable": True,
            "theme": "default",
            "frame_border_color": "#DDDDDD",
            "border_style": "solid",
            "label_text_color": None,
            "label_color": None,
            "widget_id": 1,
            "is_enabled": True,
            "enable": True,
            "multiLangSetting": None,
            "repository_id": None,
            "widget_type": "Free description",
            "updated": None,
            "settings": {}}),
    ])
def test_convert_data_to_edit_pack(data, result):
    data = data
    res = convert_data_to_edit_pack(data)
    assert res == result


# def build_rss_xml(data=None, index_id=0, page=1, count=20, term=0, lang=''):
# def find_rss_value(data, keyword):
# def get_rss_data_source(source, keyword):
# def get_elasticsearch_result_by_date(start_date, end_date):
# def validate_main_widget_insertion(repository_id, new_settings, page_id=0):
# def get_widget_design_page_with_main(repository_id):


# def main_design_has_main_widget(repository_id):
def test_main_design_has_main_widget(db_register):
    assert main_design_has_main_widget('Root Index')==True
    assert main_design_has_main_widget('test')==False
    assert main_design_has_main_widget('')==False


# def has_main_contents_widget(settings):
# def get_widget_design_setting(repository_id, current_language, page_id=None):
# def compress_widget_response(response):
# def delete_widget_cache(repository_id, page_id=None):
# def validate_upload_file(community_id: str):