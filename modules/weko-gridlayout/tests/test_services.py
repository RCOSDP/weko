# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# weko-gridlayout is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""
import pytest
import copy
import json
from mock import patch, MagicMock
from datetime import datetime

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
def test_save_command(i18n_app, users):
    data = {
        "data": {
            "settings": "test",
            "multiLangSetting": MagicMock(),
            "repository": "99"
        },
        "flag_edit": True
    }
    return_data = {
        "message": "test",
        "success": "test"
    }
    return_data_2 = {
        "error": False,
    }
    old_widget_data = MagicMock()
    old_widget_data.repository_id = "999"
    old_widget_data.updated = datetime.now()
    old_widget_data.locked_by_user = users[0]['obj'].id
    with patch("flask_login.utils._get_user", return_value=users[0]['obj']):
        with patch("weko_gridlayout.utils.build_data", return_value=""):
            with patch("weko_gridlayout.services.WidgetItemServices.create", return_value=return_data_2):
                with patch('weko_gridlayout.services.WidgetItem.get_by_id', return_value=old_widget_data):
                    assert WidgetItemServices.save_command(data)

                    data2 = None
                    assert WidgetItemServices.save_command(data2)

                    data["flag_edit"] = False
                    assert WidgetItemServices.save_command(data)

#     def __edit_widget(cls, data, ):

#     def get_by_id(cls, widget_id):
def test_get_by_id(i18n_app):
    widget_id = "1"
    return_data = {"multiLangSetting": "test"}
    return_data_2 = [{
        "label": "test",
        "description_data": "test",
        "lang_code": "test"
    }]
    with patch("weko_gridlayout.models.WidgetItem.get_by_id", return_value=""):
        with patch("weko_gridlayout.models.WidgetMultiLangData.get_by_widget_id", return_value=""):
            assert WidgetItemServices.get_by_id(widget_id)
    with patch("weko_gridlayout.models.WidgetItem.get_by_id", return_value=return_data):
        with patch("weko_gridlayout.models.WidgetMultiLangData.get_by_widget_id", return_value=return_data_2):
            assert WidgetItemServices.get_by_id(widget_id)


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


#     def delete_by_id(cls, widget_id):.
def test_delete_by_id(i18n_app):
    widget_id = "1"
    assert WidgetItemServices.delete_by_id(widget_id="")
    with patch("weko_gridlayout.services.WidgetDesignServices.is_used_in_widget_design", return_value=True):
        assert WidgetItemServices.delete_by_id(widget_id)
    with patch("weko_gridlayout.services.WidgetDesignServices.is_used_in_widget_design", return_value=False):
        with patch("weko_gridlayout.models.WidgetItem.delete_by_id", return_value=""):
            with patch("weko_gridlayout.models.WidgetMultiLangData.delete_by_widget_id", return_value=""):
                assert WidgetItemServices.delete_by_id(widget_id)
        assert WidgetItemServices.delete_by_id(widget_id)


#     def delete_multi_item_by_id(cls, widget_id, session):


#     def get_widget_data_by_widget_id(cls, widget_id):
def test_get_widget_data_by_widget_id(i18n_app):
    assert WidgetItemServices.get_widget_data_by_widget_id(widget_id=None) == None

#     def load_edit_pack(cls, widget_id):
def test_load_edit_pack(i18n_app, widget_items):
    widget_id = widget_items[0].widget_id
    with patch("weko_gridlayout.utils.convert_widget_data_to_dict", return_value=""):
        # with patch("weko_gridlayout.models.WidgetItem.get_by_id", return_value=""):
        with patch("weko_gridlayout.models.WidgetMultiLangData.get_by_widget_id", return_value=""):
            with patch("weko_gridlayout.utils.convert_data_to_design_pack", return_value=""):
                with patch("weko_gridlayout.utils.convert_data_to_edit_pack", return_value="test"):
                    # Doesn't return any value
                    assert not WidgetItemServices.load_edit_pack(widget_id)
    # Doesn't return any value
    assert not WidgetItemServices.load_edit_pack(widget_id=None)


#     def get_locked_widget_info(cls, widget_id, widget_item=None,
def test_get_locked_widget_info(i18n_app, widget_items, users):
    import datetime

    widget_item = MagicMock()
    widget_item.updated = datetime.datetime.now()
    widget_item.locked_by_user = "9999"
    widget_item.locked = True

    def widget_item_func(item):
        return widget_item

    with patch("flask_login.utils._get_user", return_value=users[0]['obj']):
        with patch('weko_gridlayout.services.WidgetItemServices.get_widget_by_id', widget_item_func):
            assert WidgetItemServices.get_locked_widget_info(widget_id=None) != None

        widget_item.updated = datetime.datetime.now() - datetime.timedelta(days=2)

        with patch('weko_gridlayout.services.WidgetItemServices.get_widget_by_id', widget_item_func):
            assert WidgetItemServices.get_locked_widget_info(widget_id=None) == None

        widget_item.updated = datetime.datetime.now()
        widget_item.locked_by_user = users[0]['obj'].id

        with patch('weko_gridlayout.services.WidgetItemServices.get_widget_by_id', widget_item_func):
            assert WidgetItemServices.get_locked_widget_info(widget_id=None) == None


#     def lock_widget(cls, widget_id, locked_value):
def test_lock_widget(i18n_app, users):
    widget_id = "1"
    locked_value = "1"
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        with patch("weko_gridlayout.models.WidgetItem.update_by_id", return_value=""):
            # Doesn't return any value
            assert not WidgetItemServices.lock_widget(widget_id, locked_value)


#     def unlock_widget(cls, widget_id):
def test_unlock_widget(i18n_app):
    widget_id = "1"
    with patch("weko_gridlayout.models.WidgetItem.update_by_id", return_value=""):
        assert WidgetItemServices.unlock_widget(widget_id) == ""


#     def __validate(cls, data, is_used_in_widget_design=False):


### class WidgetDesignServices:
#     def get_repository_list(cls):
def test_get_repository_list(i18n_app, db, communities, users):
    comm = communities
    # super role user
    with patch("flask_login.utils._get_user", return_value=users[2]['obj']):
        result = WidgetDesignServices.get_repository_list()
        assert len(result['repositories']) == 2
        assert result['repositories'][0]['id'] == 'Root Index'
        assert result['repositories'][1]['id'] == comm.id

    # comadmin role user
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        result = WidgetDesignServices.get_repository_list()
        assert len(result['repositories']) == 0

        comm.group_id = users[3]['obj'].roles[0].id
        db.session.commit()
        result = WidgetDesignServices.get_repository_list()
        assert len(result['repositories']) == 1
        assert result['repositories'][0]['id'] == comm.id

def test_get_repository_list_2(i18n_app):
    result = WidgetDesignServices.get_repository_list()
    assert len(result['repositories']) == 1
    assert result['repositories'][0]['id'] == 'Root Index'



#     def get_widget_list(cls, repository_id, default_language):
def test_get_widget_list(i18n_app, widget_items):
    repository_id = "Root Index"
    default_language = {"lang_code": "ja"}

    assert WidgetDesignServices.get_widget_list(repository_id, default_language)

    default_language = {"lang_code": "en"}
    assert WidgetDesignServices.get_widget_list(repository_id, default_language)

    with patch('weko_gridlayout.services.isinstance', side_effect=Exception('')):
        assert WidgetDesignServices.get_widget_list(repository_id, default_language)


#     def get_widget_preview(cls, repository_id, default_language,
def test_get_widget_preview(i18n_app, widget_item):
    repository_id = "Root Index"
    default_language = {"lang_code": "ja"}
    WEKO_GRIDLAYOUT_ACCESS_COUNTER_TYPE = "Access counter"
    return_data = {
        "settings": [{
            "widget_id": "test",
            "x": "test",
            "y": "test",
            "width": "test",
            "height": "test",
            "id": "test",
            "type": WEKO_GRIDLAYOUT_ACCESS_COUNTER_TYPE,
            "name": "test",
            "created_date": "test",
            "multiLangSetting": {
                "ja": "ja",
            }
        }]
    }
    with patch("weko_gridlayout.models.WidgetDesignSetting.select_by_repository_id", return_value=return_data):
        assert WidgetDesignServices.get_widget_preview(repository_id, default_language)
        return_data["settings"][0]["multiLangSetting"] = {"en": {"label": "en"}}
        assert WidgetDesignServices.get_widget_preview(repository_id, default_language)
        return_data["settings"][0]["multiLangSetting"] = {"xx": {"label": "en"}}
        assert WidgetDesignServices.get_widget_preview(repository_id, default_language)
        return_data["settings"][0]["multiLangSetting"] = None
        assert WidgetDesignServices.get_widget_preview(repository_id, default_language)


#     def get_widget_design_setting(cls, repository_id: str,
def test_get_widget_design_setting_2(i18n_app):
    repository_id = "Root Index"
    current_language = "ja"
    return_data = {
        "settings": {
            "widget_id": "test",
            "x": "test",
            "y": "test",
            "width": "test",
            "height": "test",
            "id": "test",
            "type": "test",
            "name": "test",
            "created_date": "test",
            "multiLangSetting": {
                "ja": "ja",
            }
        }
    }
    with patch("weko_gridlayout.models.WidgetDesignSetting.select_by_repository_id", return_value=return_data):
        with patch("weko_gridlayout.services.WidgetDesignServices._get_setting", return_value="return_data"):
            assert WidgetDesignServices.get_widget_design_setting(repository_id, current_language)
    assert WidgetDesignServices.get_widget_design_setting(repository_id, current_language)


#     def _get_setting(cls, settings, current_language):
def test__get_setting(i18n_app):
    current_language = "ja"
    settings = json.dumps(
        {
            "settings": {
                "widget_id": "test",
                "x": "test",
                "y": "test",
                "width": "test",
                "height": "test",
                "id": "test",
                "type": "test",
                "name": "test",
                "created_date": "test",
                "multiLangSetting": {
                    "ja": "ja",
                }
            }
        }
    )
    with patch("weko_gridlayout.services.WidgetDesignServices._get_design_base_on_current_language", return_value="return_data"):
        assert WidgetDesignServices._get_setting(settings, current_language)


#     def _get_design_base_on_current_language(cls, current_language,
def test__get_design_base_on_current_language(i18n_app):
    current_language = "ja"
    widget_item = {
        "multiLangSetting": {
            "ja": "ja",
            "en": "en",
        }
    }
    assert WidgetDesignServices._get_design_base_on_current_language(current_language, widget_item)
    widget_item = {}
    assert WidgetDesignServices._get_design_base_on_current_language(current_language, widget_item)


#     def update_widget_design_setting(cls, data):
def test_update_widget_design_setting(i18n_app):
    WEKO_GRIDLAYOUT_ACCESS_COUNTER_TYPE = "Access counter"
    data = {
        "widget_id": "test",
        "settings": [{
            "settings": "test",
            "type": WEKO_GRIDLAYOUT_ACCESS_COUNTER_TYPE,
            "created_date": None
        }],
        "repository_id": "Root Index",
        "page_id": "test",
    }

    return_data = {
        "settings": {
            "widget_id": "test",
            "x": "test",
            "y": "test",
            "width": "test",
            "height": "test",
            "id": "test",
            "type": "test",
            "name": "test",
            "created_date": "test",
            "multiLangSetting": {
                "ja": "ja",
            }
        }
    }

    with patch("weko_gridlayout.services.WidgetItemServices.get_widget_data_by_widget_id", return_value=return_data):
        with patch("weko_gridlayout.utils.validate_main_widget_insertion", return_value="test"):
            with patch("weko_gridlayout.utils.delete_widget_cache", return_value="test"):
                with patch("weko_gridlayout.models.WidgetDesignPage.update_settings", return_value="test"):
                    with patch("weko_gridlayout.services.WidgetDesignSetting.select_by_repository_id", return_value="return_data"):
                        assert WidgetDesignServices.update_widget_design_setting(data)
                        data["page_id"] = None
                        assert WidgetDesignServices.update_widget_design_setting(data)
        assert WidgetDesignServices.update_widget_design_setting(data)


#     def update_item_in_preview_widget_item(cls, widget_id, data_result,
def test_update_item_in_preview_widget_item(i18n_app):
    widget_id = "1"
    data_result = {"test": "test"}
    json_data = [{
        "widget_id": "1"
    }]
    with patch("weko_gridlayout.utils.update_general_item", return_value="test"):
        assert WidgetDesignServices.update_item_in_preview_widget_item(widget_id=widget_id, data_result=data_result, json_data=json_data)


#     def handle_change_item_in_preview_widget_item(cls, widget_id, data_result):
def test_handle_change_item_in_preview_widget_item(i18n_app):
    return_data = MagicMock()
    return_data.repository_id = "1"
    return_data.settings = "1"
    return_data.id = "1"
    widget_id = "1"
    data_result = MagicMock()
    with patch("weko_gridlayout.services.WidgetItemServices.get_widget_by_id", return_value=return_data):
        with patch("weko_gridlayout.models.WidgetDesignSetting.select_by_repository_id", return_value=return_data):
            with patch("weko_gridlayout.services.WidgetDesignPage.get_by_repository_id", return_value=[return_data]):
                with patch("weko_gridlayout.services.WidgetDesignServices.update_item_in_preview_widget_item", return_value="test"):
                    with patch("weko_gridlayout.models.WidgetDesignPage.update_settings", return_value=False):
                        assert not WidgetDesignServices.handle_change_item_in_preview_widget_item(widget_id, data_result)
                    with patch("weko_gridlayout.models.WidgetDesignPage.update_settings", return_value=True):
                        with patch("weko_gridlayout.utils.delete_widget_cache", return_value="test"):
                            assert WidgetDesignServices.handle_change_item_in_preview_widget_item(widget_id, data_result)
    assert not WidgetDesignServices.handle_change_item_in_preview_widget_item(widget_id, data_result)

#     def is_used_in_widget_design(cls, widget_id):
def test_is_used_in_widget_design(i18n_app):
    return_data = MagicMock()
    return_data.repository_id = "1"
    return_data.settings = [{"widget_id": "1"}]
    return_data.id = "1"
    widget_id = "1"
    data_result = MagicMock()
    with patch("weko_gridlayout.services.WidgetItemServices.get_widget_by_id", return_value=return_data):
        with patch("weko_gridlayout.models.WidgetDesignSetting.select_by_repository_id", return_value=return_data):
            with patch("weko_gridlayout.services.WidgetDesignPage.get_by_repository_id", return_value=[return_data]):
                assert WidgetDesignServices.is_used_in_widget_design(widget_id)
    assert not WidgetDesignServices.is_used_in_widget_design(widget_id="")
    assert WidgetDesignServices.is_used_in_widget_design(widget_id)



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
#     def __update_main_layout_page_id_for_widget_item(cls, repository_id,
def test__update_main_layout_id_for_widget(i18n_app, db):
    test = WidgetDesignPage(
        id=1,
        repository_id="test",
        url="/",
        is_main_layout=True
    )
    db.session.add(test)
    db.session.commit()
    with patch("weko_gridlayout.models.WidgetItem.get_id_by_repository_and_type", return_value=["1"]):
        with patch("weko_gridlayout.models.WidgetItem.get_by_id", return_value=""):
            with patch("weko_gridlayout.services.WidgetDesignPageServices._update_page_id_for_widget_item_setting", return_value=""):
                assert WidgetDesignPageServices._update_main_layout_id_for_widget("test")


#     def _update_main_layout_page_id_for_widget_design( ERR ~
def test__update_main_layout_page_id_for_widget_design(i18n_app):
    repository_id = "1"
    page_id = "1"

    def widget_design(id):
        widget_design = {
            "settings": [{"type": "type"}],
        }
        return widget_design

    i18n_app.config['WEKO_GRIDLAYOUT_MENU_WIDGET_TYPE'] = "type"

    with patch("weko_gridlayout.services.WidgetDesignSetting.select_by_repository_id", widget_design):
        with patch("weko_gridlayout.services.WidgetDesignSetting.update", return_value="widget_design"):
            assert not WidgetDesignPageServices._update_main_layout_page_id_for_widget_design(repository_id, page_id)


#     def _update_page_id_for_widget_design_setting(cls, settings, page_id):
def test__update_page_id_for_widget_design_setting(i18n_app):
    WEKO_GRIDLAYOUT_MENU_WIDGET_TYPE = 'Menu'
    settings = [{
        "type": WEKO_GRIDLAYOUT_MENU_WIDGET_TYPE,
        "menu_show_pages": ["0"]
    }]
    page_id = "0"
    assert WidgetDesignPageServices._update_page_id_for_widget_design_setting(settings, page_id)


#     def _update_page_id_for_widget_item_setting(cls, page_id,
def test__update_page_id_for_widget_item_setting(i18n_app):
    page_id = "0"
    widget_item = MagicMock()
    widget_item.settings = {
        "menu_show_pages": ["0"]
    }

    with patch("weko_gridlayout.models.WidgetItem.update_setting_by_id", return_value=""):
        # Doesn't return any value
        assert not WidgetDesignPageServices._update_page_id_for_widget_item_setting(page_id, widget_item)


#     def delete_page(cls, page_id):
def test_delete_page(i18n_app):
    page_id = "1"
    with patch("weko_gridlayout.models.WidgetDesignPageMultiLangData.delete_by_page_id", return_value="test"):
        with patch("weko_gridlayout.models.WidgetDesignPage.delete", return_value=""):
            assert WidgetDesignPageServices.delete_page(page_id)
    assert WidgetDesignPageServices.delete_page(page_id)



#     def get_page_list(cls, repository_id, language):
def test_get_page_list(i18n_app):
    repository_id = "1"
    language = "ja"
    return_data = MagicMock()
    return_data_2 = MagicMock()
    return_data_2.title = "test"
    return_data.multi_lang_data = {"language": return_data_2, "ja": "ja"}
    return_data.title = "test"
    return_data.id = "test"
    with patch("weko_gridlayout.services.WidgetDesignPage.get_by_repository_id", return_value=[return_data]):
        assert WidgetDesignPageServices.get_page_list(repository_id, language)
    assert WidgetDesignPageServices.get_page_list(repository_id, language)


#     def get_page(cls, page_id, repository_id):
def test_get_page(i18n_app):
    page_id = "1"
    repository_id = "1"
    return_data = MagicMock()
    return_data_2 = MagicMock()
    return_data_2.title = "test"
    return_data.multi_lang_data = {"lang": return_data_2}
    return_data.title = "test"
    return_data.id = "test"
    return_data.url = "test"
    return_data.content = "test"
    return_data.repository_id = "test"
    return_data.is_main_layout = "test"

    with patch("weko_gridlayout.services.WidgetDesignPage.get_by_id", return_value=return_data):
        assert WidgetDesignPageServices.get_page(page_id, repository_id)

    from sqlalchemy.orm.exc import NoResultFound
    i18n_app.config['WEKO_THEME_DEFAULT_COMMUNITY'] = "1"

    with patch("weko_gridlayout.services.WidgetDesignPage.get_by_id", side_effect=NoResultFound('')):
        assert WidgetDesignPageServices.get_page(0, repository_id)

        i18n_app.config['WEKO_THEME_DEFAULT_COMMUNITY'] = "0"

        assert WidgetDesignPageServices.get_page(0, repository_id)
        assert WidgetDesignPageServices.get_page(1, repository_id)

    with patch("weko_gridlayout.services.WidgetDesignPage.get_by_id", side_effect=Exception('')):
        assert WidgetDesignPageServices.get_page(page_id, repository_id)


### class WidgetDataLoaderServices:
#     def _get_index_info(cls, index_json, index_info):
def test__get_index_info(i18n_app):
    w = WidgetDataLoaderServices()
    index_json = [{
        "id": "id",
        "name": "0",
        "pid": "999",
        "children": [{
            "id": "id",
            "name": "0",
            "pid": "999",
            "children": ""
        }]
    }]
    index_info = {}

    assert w._get_index_info(index_json=index_json, index_info=index_info) == None


#     def get_new_arrivals_data(cls, widget_id):
def test_get_new_arrivals_data(i18n_app, widget_item):
    w = WidgetDataLoaderServices()
    data1 = {
        "settings": {
            "display_result": "test",
            "new_dates": "test",
        }
    }
    with patch("weko_gridlayout.services.WidgetItemServices.get_widget_data_by_widget_id", return_value=data1):
        assert "Widget is not exist" in w.get_new_arrivals_data(None)["error"]

    data2 = {}

    with patch("weko_gridlayout.services.WidgetItemServices.get_widget_data_by_widget_id", return_value=data2):
        assert "Widget is not exist" in w.get_new_arrivals_data(1)["error"]

    data3 = copy.deepcopy(data1)
    del data3["settings"]["new_dates"]

    with patch("weko_gridlayout.services.WidgetItemServices.get_widget_data_by_widget_id", return_value=data3):
        assert "Widget is not exist" in w.get_new_arrivals_data(1)["error"]

    def get_new_items(start_date, end_date, agg_size, must_not):
        return {}

    def get_new_items_2(start_date, end_date, agg_size, must_not):
        return {"res": "res"}

    res = MagicMock()
    res.get_new_items = get_new_items
    data4 = copy.deepcopy(data1)
    data4["settings"]["display_result"] = 999

    with patch("weko_gridlayout.services.WidgetItemServices.get_widget_data_by_widget_id", return_value=data4):
        with patch("weko_gridlayout.services.QueryRankingHelper", res):
            assert "Cannot search data" in w.get_new_arrivals_data(1)["error"]

    res.get_new_items = get_new_items_2

    with patch("weko_gridlayout.services.WidgetItemServices.get_widget_data_by_widget_id", return_value=data4):
        with patch("weko_gridlayout.services.QueryRankingHelper", res):
            assert "Cannot search data" in w.get_new_arrivals_data(1)["error"]


#     def get_arrivals_rss(cls, data, term, count):
def test_get_arrivals_rss(i18n_app):
    data = MagicMock()
    term = "test"
    count = 1

    data = {
        "hits": {
            "hits": [{
                "_source": {
                    "path": "path"
                },
                "_id": "_id",
                "control_number": "control_number"
            }]
        }
    }

    assert WidgetDataLoaderServices.get_arrivals_rss(None, term, count) != None

    with patch('weko_items_ui.utils.find_hidden_items', return_value=["_id"]):
        assert WidgetDataLoaderServices.get_arrivals_rss(data, term, count) != None

    # with patch('weko_items_ui.utils.find_hidden_items', return_value=["id"]):
        # assert WidgetDataLoaderServices.get_arrivals_rss(data, term, count) != None


#     def get_widget_page_endpoints(cls, widget_id, language):
def test_get_widget_page_endpoints(i18n_app, widget_item):
    from sqlalchemy.orm.exc import NoResultFound

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

            # Exception coverage ~ line 1185
            with patch("weko_gridlayout.services.WidgetDesignPage.get_by_id", side_effect=NoResultFound('')):
                WidgetDataLoaderServices.get_widget_page_endpoints(widget_id, language)

        assert WidgetDataLoaderServices.get_widget_page_endpoints(widget_id, language)
