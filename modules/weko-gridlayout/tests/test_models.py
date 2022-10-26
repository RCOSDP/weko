import pytest
import json
from mock import patch, MagicMock

from weko_gridlayout.models import (
    WidgetType,
    WidgetItem,
    WidgetMultiLangData,
    WidgetDesignSetting,
    WidgetDesignPage,
    WidgetDesignPageMultiLangData
)


# class WidgetType(db.Model):
#     def create(cls, data):
def test_WidgetType_create(i18n_app, db):
    data = {
        "type_id": 1,
        "type_name": "test",
    }
    assert WidgetType.create(data)
def test_WidgetType_create_2(i18n_app):
    data = {
        "type_id": 1,
        "type_name": "test",
    }
    # Coverage for execption
    assert WidgetType.create(data)


#     def get(cls, widget_type_id):
#     def get_all_widget_types(cls):


# class WidgetItem(db.Model, Timestamp):
#     def get_by_id(cls, widget_item_id):


#     def get_id_by_repository_and_type(cls, repository, widget_type):
def test_get_id_by_repository_and_type(i18n_app, widget_items):
    repository = "Root Index"
    widget_type = "Free description"
    assert WidgetItem.get_id_by_repository_and_type(repository, widget_type)
    assert not WidgetItem.get_id_by_repository_and_type("repository", "widget_type")


#     def get_sequence(cls, session): ERR ~ execution error
def test_get_sequence(i18n_app, db):
    session = None
    assert WidgetItem.get_sequence(session)


#     def create(cls, widget_data, session):


#     def update_by_id(cls, widget_item_id, widget_data, session=None):
def test_update_by_id(i18n_app, widget_items):
    widget_item_id = MagicMock()
    widget_data = MagicMock()
    with patch("weko_gridlayout.models.WidgetItem.get_by_id", return_value=""):
        assert not WidgetItem.update_by_id(widget_item_id, widget_data)


#     def update_setting_by_id(cls, widget_id, settings):
#     def delete_by_id(cls, widget_id, session):


# class WidgetMultiLangData(db.Model):
#     def get_by_id(cls, widget_multi_lang_id):
#     def create(cls, data, session):
#     def get_by_widget_id(cls, widget_id):
#     def update_by_id(cls, widget_item_id, data):
#     def delete_by_widget_id(cls, widget_id, session):


# class WidgetDesignSetting(db.Model):
#     def select_all(cls):
#     def select_by_repository_id(cls, repository_id):
#     def update(cls, repository_id, settings):
#     def create(cls, repository_id, settings=None):


# class WidgetDesignPage(db.Model):
#     def create_or_update(cls, repository_id, title, url, content,
#     def delete(cls, page_id):
#     def update_settings(cls, page_id, settings=None):
#     def update_settings_by_repository_id(cls, repository_id, settings=None):
#     def get_all(cls):
#     def get_all_valid(cls):
#     def get_by_id(cls, id):
#     def get_by_id_or_none(cls, id):
#     def get_by_url(cls, url):
#     def get_by_repository_id(cls, repository_id):


# class WidgetDesignPageMultiLangData(db.Model):
#     def __init__(self, lang_code, title):
#     def get_by_id(cls, id):
#     def delete_by_page_id(cls, page_id):