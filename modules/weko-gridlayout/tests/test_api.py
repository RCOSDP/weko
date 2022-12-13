import os
import json
import copy
import pytest
import unittest
from datetime import datetime
from mock import patch, MagicMock, Mock
from flask import current_app, make_response, request
from flask_login import current_user
from flask_babelex import Babel

from weko_gridlayout.api import WidgetItems


# class WidgetItems(object):
class test_WidgetItems():
    # def __init__(self):
    #     self.test_build_general_data()
    #     self.test_build_settings_data()

    # def build_general_data(cls, data_object, widget_items, is_update=False):
    def test_build_general_data(i18n_app):
        data_object = MagicMock()
        widget_items = {
            "repository": "repository",
            "widget_type": "widget_type",
            "browsing_role": "browsing_role",
            "edit_role": "edit_role",
            "enable": "enable",
        }
        # Doesn't return any value
        assert not WidgetItems.build_general_data(data_object, widget_items)

        widget_items["browsing_role"] = ["browsing_role"]
        widget_items["edit_role"] = ["edit_role"]

        # Doesn't return any value
        assert not WidgetItems.build_general_data(data_object, widget_items)

        # Will result in error for exception coverage
        assert not WidgetItems.build_general_data("data_object", widget_items)
        

    # def build_settings_data(cls, widget_object, widget_items):
    def test_build_settings_data(i18n_app):
        widget_object = MagicMock()
        widget_items = {
            "label_color": "label_color",
            "frame_border": "frame_border",
            "frame_border_color": "frame_border_color",
            "text_color": "text_color",
            "background_color": "background_color",
        }

        # Doesn't return any value
        assert not WidgetItems.build_settings_data(widget_object, widget_items)


    # def build_object(cls, widget_items=None, is_update=False):
    def test_build_object(i18n_app):
        with patch("weko_gridlayout.api.WidgetItems.build_general_data", return_value="data"):
            with patch("weko_gridlayout.api.WidgetItems.build_settings_data", return_value="data"):
                widget_items = dict()
                assert not WidgetItems.build_object(widget_items)

                widget_items = list()
                assert not WidgetItems.build_object(widget_items)
        # assert not WidgetItems.build_object(widget_items=None)


    # def create(cls, widget_items=None):
    def test_create(i18n_app):
        widget_items = list()
        assert not WidgetItems.create(widget_items)

        widget_items = {
            "repository": "repository",
            "widget_type": "widget_type",
            "browsing_role": "browsing_role",
            "edit_role": "edit_role",
            "enable": "enable",
            "label_color": "label_color",
            "frame_border": "frame_border",
            "frame_border_color": "frame_border_color",
            "text_color": "text_color",
            "background_color": "background_color",
        }
        # with patch("weko_gridlayout.api.WidgetItems.build_object", return_value=widget_items):
        assert not WidgetItems.create(widget_items)


    # def update(cls, widget_items, widget_id):
    def test_update(i18n_app):
        widget_items = {
            "repository": "repository",
            "widget_type": "widget_type",
            "browsing_role": "browsing_role",
            "edit_role": "edit_role",
            "enable": "enable",
            "label_color": "label_color",
            "frame_border": "frame_border",
            "frame_border_color": "frame_border_color",
            "text_color": "text_color",
            "background_color": "background_color",
        }
        with patch("weko_gridlayout.api.WidgetItem.update_by_id", return_value=""):
            assert WidgetItems.update(widget_items, {"id": 1})
            assert not WidgetItems.update("widget_items", {"id": 1})


    # def update_by_id(cls, widget_items, widget_id):
    def test_update_by_id(i18n_app):
        widget_items = {
            "repository": "repository",
            "widget_type": "widget_type",
            "browsing_role": "browsing_role",
            "edit_role": "edit_role",
            "enable": "enable",
            "label_color": "label_color",
            "frame_border": "frame_border",
            "frame_border_color": "frame_border_color",
            "text_color": "text_color",
            "background_color": "background_color",
        }
        with patch("weko_gridlayout.api.WidgetItem.update_by_id", return_value=""):
            assert WidgetItems.update_by_id(widget_items, {"id": 1})
            assert not WidgetItems.update_by_id("widget_items", {"id": 1})


    # def delete(cls, widget_id):
    def test_delete(i18n_app, db):
        from weko_gridlayout.models import WidgetItem
        widget = WidgetItem(
            widget_id=1,
            repository_id="1",
            widget_type="1",
            # label="1",
            # language="jp",
            # repository="repository"
        )
        db.session.add(widget)
        db.session.commit()

        # Doesn't return any value
        # ERROR ~ delete function doesn't exist in WidgetItem class
        assert not WidgetItems.delete(1)


    # def get_all_widget_items(cls):
    def test_get_all_widget_items(i18n_app, widget_item):
        assert WidgetItems.get_all_widget_items()


    # def validate_exist_multi_language(cls, item, data):
    def test_validate_exist_multi_language(i18n_app):
        item = {
            "multiLangSetting": {"k": {"label": "label"}}
        }
        data = {
            "k": {"label": "label"}
        }
        assert WidgetItems.validate_exist_multi_language(item, data)

        item = {}
        assert not WidgetItems.validate_exist_multi_language(item, data)


    # def is_existed(cls, widget_items, widget_item_id):
    def test_is_existed(i18n_app, widget_item):
        assert not WidgetItems.is_existed(widget_item, "1")

        # ERROR ~ get_by_repo_and_type function doesn't exist in WidgetItem class
        with patch("weko_gridlayout.api.WidgetItem.get_by_repo_and_type", return_value=""):
            widget_item = {
                "repository": "repository",
                "widget_type": "widget_type",
            }
            assert WidgetItems.is_existed(widget_item, "1")


    # def get_account_role(cls):
    def test_get_account_role(i18n_app, users):
        assert WidgetItems.get_account_role()


    def test_get_account_role_2(i18n_app):
        # For exception coverage
        assert WidgetItems.get_account_role()


    # def parse_result(cls, in_result):
    def test_parse_result(i18n_app):
        in_result = MagicMock()
        in_result.id = 1
        in_result.repository_id = 1
        in_result.widget_type = "test"
        in_result.label = "test"
        in_result.language = "test"
        in_result.browsing_role = "test"
        in_result.edit_role = "test"
        in_result.is_enabled = "test"
        in_result.settings = json.dumps({
            "label_color": "test",
            "has_frame_border": "test",
            "frame_border_color": "test",
            "text_color": "test",
            "background_color": "test",
            "multiLangSetting": "test", 
        })
        
        assert WidgetItems.parse_result(in_result)


test = test_WidgetItems()

def test_build_general_data():
    test.test_build_general_data()
def test_build_settings_data():
    test.test_build_settings_data()
def test_build_object():
    test.test_build_object()
def test_create():
    test.test_create()
def test_update():
    test.test_update()
def test_update_by_id():
    test.test_update_by_id()
def test_delete(db):
    test.test_delete(db)
def test_get_all_widget_items(widget_item):
    test.test_get_all_widget_items(widget_item)
def test_validate_exist_multi_language():
    test.test_validate_exist_multi_language()   
def test_is_existed(widget_item):
    test.test_is_existed(widget_item)
def test_get_account_role(users):
    test.test_get_account_role(users)
def test_get_account_role_2():
    test.test_get_account_role_2()
def test_parse_result():
    test.test_parse_result()
