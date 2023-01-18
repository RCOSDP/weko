# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# weko-gridlayout is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""
import pytest
from mock import patch, MagicMock

from weko_gridlayout.services import (
    WidgetItemServices,
    WidgetDesignServices,
    WidgetDesignPageServices,
    WidgetDataLoaderServices
) 
from weko_gridlayout.models import WidgetDesignPage


### class WidgetItemServices:
#     def get_widget_by_id(cls, widget_id):
def test_get_widget_by_id(i18n_app, widget_item):
    for item in widget_item:
        assert WidgetItemServices.get_widget_by_id("1")


#     def save_command(cls, data):
def test_save_command(i18n_app):
    data = {
        "data": 1,
        "flag_edit": False
    }
    return_data = {
        "message": "test",
        "success": "test"
    }
    return_data_2 = {
        "error": False,
    }
    with patch("weko_gridlayout.utils.build_data", return_value=""):
        with patch("weko_gridlayout.services.WidgetItemServices.create", return_value=return_data_2):
            assert WidgetItemServices.save_command(data)


#     def __edit_widget(cls, data, ):
#     def get_by_id(cls, widget_id):


#     def create(cls, widget_data):
@pytest.mark.parametrize("widget_data, result_error",
                         [({}, 'Widget data is empty!'),
                          ({'multiLangSetting':''}, 'Multiple language data is empty'),
                          ({'repository_id': 'Root Index',
                            'widget_type': '',
                            'multiLangSetting':
                                {'en':
                                    {
                                        'label': 'test',
                                        'description': ''
                                    }
                                }
                            }, '')])
def test_create(db, widget_data, result_error):
    """
    Test of new widget creation.
    """
    with patch("weko_gridlayout.models.WidgetItem.get_sequence", return_value=3):
        result = WidgetItemServices.create(widget_data)
        assert result['error'] == result_error

def test_create_exception(app, db):
    """
    Test of new widget creation.
    """
    widget_data = {'multiLangSetting':
        {'en':
            {'label': 'test',
            'description': ''
            }
        }
    }
    with patch("weko_gridlayout.models.WidgetItem.get_sequence",
                side_effect=Exception("Exception")):
        result = WidgetItemServices.create(widget_data)
        assert result['error'] == "Exception"


#     def update_by_id(cls, widget_id, widget_data):
@pytest.mark.parametrize("widget_id, widget_data, result_error",
                         [(None, None, 'Widget data is empty!'),
                          (1, None, 'Widget data is empty!'),
                          (None, {'multiLangSetting':''}, 'Widget data is empty!'),
                          (1, {'multiLangSetting':''}, 'Multiple language data is empty'),
                          (1, {'multiLangSetting':
                                {'en':
                                    {
                                        'label': 'test',
                                        'description': ''
                                    }
                                }
                            }, '')])
def test_update_by_id(db, widget_id, widget_data, result_error):
    """
    Test of widget updating by id.
    """
    result = WidgetItemServices.update_by_id(widget_id, widget_data)
    assert result['error'] == result_error

def test_update_by_id_exception(db):
    widget_data = {'multiLangSetting':
        {'en':
            {'label': 'test',
            'description': ''
            }
        }
    }
    with patch("weko_gridlayout.models.WidgetItem.update_by_id",
               side_effect=Exception("Exception")):
        result = WidgetItemServices.update_by_id(1, widget_data)
        assert result['error'] == "Exception"


#     def delete_by_id(cls, widget_id):
#     def delete_multi_item_by_id(cls, widget_id, session):
#     def get_widget_data_by_widget_id(cls, widget_id):
#     def load_edit_pack(cls, widget_id):
#     def get_locked_widget_info(cls, widget_id, widget_item=None,
#     def lock_widget(cls, widget_id, locked_value):
#     def unlock_widget(cls, widget_id):
#     def __validate(cls, data, is_used_in_widget_design=False):


### class WidgetDesignServices:
#     def get_repository_list(cls):
#     def get_widget_list(cls, repository_id, default_language):
#     def get_widget_preview(cls, repository_id, default_language,
#     def get_widget_design_setting(cls, repository_id: str,
#     def _get_setting(cls, settings, current_language):
#     def _get_design_base_on_current_language(cls, current_language,
#     def update_widget_design_setting(cls, data):
#     def update_item_in_preview_widget_item(cls, widget_id, data_result,
#     def handle_change_item_in_preview_widget_item(cls, widget_id, data_result):
#     def is_used_in_widget_design(cls, widget_id):


### class WidgetDesignPageServices:
#     def get_widget_design_setting(cls, page_id: str, current_language: str):
def test_get_widget_design_setting(i18n_app):
    return_data = MagicMock()
    return_data.settings = "test"
    with patch("weko_gridlayout.services.WidgetDesignPage.get_by_id", return_value=return_data):
        with patch("weko_gridlayout.services.WidgetDesignServices._get_setting", return_value="return_data"):
            assert WidgetDesignPageServices.get_widget_design_setting(1, "ja")
    return_data.settings = None
    assert WidgetDesignPageServices.get_widget_design_setting(1, "ja")


#     def add_or_update_page(cls, data):
def test_add_or_update_page(i18n_app):
    data = {
        "is_edit": "test",
        "page_id": "test",
        "repository_id": "test",
        "title": "test",
        "url": "test",
        "content": "test",
        "settings": "test",
        "multi_lang_data": "test",
        "is_main_layout": "test",
    }
    with patch("weko_gridlayout.services.WidgetDesignPage.create_or_update", return_value="return_data"):
        with patch("weko_gridlayout.services.WidgetDesignPageServices._update_main_layout_id_for_widget", return_value="return_data"):
            assert WidgetDesignPageServices.add_or_update_page(data)
    data["is_edit"] = False
    assert WidgetDesignPageServices.add_or_update_page(data)


#     def _update_main_layout_id_for_widget(cls, repository_id):
def test__update_main_layout_id_for_widget(i18n_app, db):
    test = WidgetDesignPage(
        id=1,
        repository_id="test",
        url="/",
        is_main_layout=True
    )
    db.session.add(test)
    db.session.commit()
    assert WidgetDesignPageServices._update_main_layout_id_for_widget("test")


#     def _update_main_layout_page_id_for_widget_design(
#     def _update_page_id_for_widget_design_setting(cls, settings, page_id):
#     def __update_main_layout_page_id_for_widget_item(cls, repository_id,
#     def _update_page_id_for_widget_item_setting(cls, page_id,
#     def delete_page(cls, page_id):
#     def get_page_list(cls, repository_id, language):
#     def get_page(cls, page_id, repository_id):


### class WidgetDataLoaderServices:
#     def get_new_arrivals_data(cls, widget_id):
def test_get_new_arrivals_data(i18n_app, widget_item):
    return_data = {
        "settings": {
            "display_result": "test",
            "new_dates": "test",
        }
    }
    with patch("weko_gridlayout.services.WidgetItemServices.get_widget_data_by_widget_id", return_value=return_data):
        assert WidgetDataLoaderServices.get_new_arrivals_data(1)

#     def get_arrivals_rss(cls, data, term, count):
def test_get_arrivals_rss(i18n_app):
    data = MagicMock()
    term = "test"
    count = 1
    assert WidgetDataLoaderServices.get_arrivals_rss(data, term, count)


#     def get_widget_page_endpoints(cls, widget_id, language):
def test_get_widget_page_endpoints(i18n_app, widget_item):
    widget_id = 1
    language = "ja"
    return_data = {
        "repository_id": "test",
        "settings": {
            "menu_show_pages": "test"
        },
        "widget_type": "Menu"
    }
    return_data_2 = MagicMock()
    return_data_2.title = "test"
    return_data_2.url = "test"
    return_data_2.is_main_layout = "test"
    return_data_3 = MagicMock()
    return_data_3.title = "test"
    return_data_2.multi_lang_data = {"ja": "test", "language": return_data_3}
    with patch("weko_gridlayout.services.WidgetItemServices.get_widget_data_by_widget_id", return_value=return_data):
        with patch("weko_gridlayout.services.WidgetDesignPage.get_by_id", return_value=return_data_2):
            assert WidgetDataLoaderServices.get_widget_page_endpoints(widget_id, language)
        assert WidgetDataLoaderServices.get_widget_page_endpoints(widget_id, language)