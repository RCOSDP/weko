# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# weko-gridlayout is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""
import pytest
from datetime import datetime
from weko_gridlayout.utils import convert_data_to_edit_pack


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
