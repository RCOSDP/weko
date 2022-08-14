# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# weko-gridlayout is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""
import pytest
from datetime import datetime
from weko_gridlayout.utils import convert_data_to_edit_pack, main_design_has_main_widget

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


# .tox/c1/bin/pytest --cov=weko_gridlayout tests/test_utils.py::test_filter_condition -v --cov-branch --cov-report=term -s --basetemp=/code/modules/weko-gridlayout/.tox/c1/tmp -vv

# def get_widget_type_list():
# def delete_item_in_preview_widget_item(data_id, json_data):
# def convert_popular_data(source_data, des_data):
# def update_general_item(item, data_result):
# def update_menu_item(item, data_result):
# def update_access_counter_item(item, data_result):
# def update_new_arrivals_item(item, data_result):
# def get_default_language():
# def get_unregister_language():
# def get_register_language():
# def get_system_language():
# def build_data(data):
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

#def test_has_main_contents_widget(db_register):



# def get_widget_design_setting(repository_id, current_language, page_id=None):
#     def validate_response():
#     def get_widget_response(_page_id):
# def compress_widget_response(response):
# def delete_widget_cache(repository_id, page_id=None):
#     def __init__(self):
#     def initialize_widget_bucket(self):
#     def __validate(self, file_stream, file_name, community_id="0", file_size=0):
#     def save_file(self, file_stream, file_name: str, mimetype: str,
#     def get_file(self, file_name, community_id=0):
# def validate_upload_file(community_id: str):
