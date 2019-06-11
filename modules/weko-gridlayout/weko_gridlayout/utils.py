# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Utilities for convert response json."""
import copy
import json

from flask import current_app, jsonify, make_response
from invenio_db import db
from sqlalchemy import asc
from weko_admin.models import AdminLangSettings

from .api import WidgetItems, WidgetMultiLangData
from .config import WEKO_GRIDLAYOUT_DEFAULT_LANGUAGE_CODE, \
    WEKO_GRIDLAYOUT_DEFAULT_WIDGET_LABEL
from .models import WidgetDesignSetting, WidgetItem, WidgetMultiLangData, \
    WidgetType


def get_repository_list():
    """Get repository list from Community table.

    :return: Repository list.
    """
    result = {
        "repositories": [{"id": "Root Index", "title": ""}],
        "error": ""
    }
    try:
        from invenio_communities.models import Community
        with db.session.no_autoflush:
            communities = Community.query.all()
        if communities:
            for community in communities:
                community_result = dict()
                community_result['id'] = community.id
                community_result['title'] = community.title
                result['repositories'].append(community_result)
    except Exception as e:
        result['error'] = str(e)

    return result


def get_widget_list(repository_id, default_language):
    """Get Widget list.

    :param repository_id: Identifier of the repository.
    :param default_language: The default language.
    :return: Widget list.
    """
    result = {
        "data": [],
        "error": ""
    }
    try:
        with db.session.no_autoflush:
            widget_item_list = WidgetItem.query.filter_by(
                repository_id=str(repository_id), is_enabled=True,
                is_deleted=False
            ).all()
        lang_code_default = None
        if default_language:
            lang_code_default = default_language.get('lang_code')
        if type(widget_item_list) is list:
            for widget_item in widget_item_list:
                data = dict()
                data["widgetId"] = widget_item.repository_id
                data["widgetType"] = widget_item.widget_type
                data["widgetLabel"] = widget_item.label
                data["Id"] = widget_item.id
                settings = widget_item.settings
                settings = json.loads(settings)
                languages = settings.get("multiLangSetting")
                if type(languages) is dict and lang_code_default is not None:
                    if languages.get(lang_code_default):
                        data_display = languages[lang_code_default]
                        data["widgetLabelDisplay"] = data_display.get('label')
                    elif languages.get('en'):
                        data_display = languages['en']
                        data["widgetLabelDisplay"] = data_display.get('label')
                    else:
                        data["widgetLabelDisplay"] = \
                            WEKO_GRIDLAYOUT_DEFAULT_WIDGET_LABEL
                else:
                    data["widgetLabelDisplay"] = \
                        WEKO_GRIDLAYOUT_DEFAULT_WIDGET_LABEL
                result["data"].append(data)
    except Exception as e:
        result["error"] = str(e)

    return result


def get_widget_preview(repository_id, default_language):
    """Get Widget preview by repository id.

    :param repository_id: Identifier of the repository
    :param default_language: The default language.
    :return: Widget preview json.
    """
    result = {
        "data": [],
        "error": ""
    }
    try:
        widget_setting = WidgetDesignSetting.select_by_repository_id(
            repository_id)
        lang_code_default = None
        if default_language:
            lang_code_default = default_language.get('lang_code')
        if widget_setting:
            settings = widget_setting.get('settings')
            if settings:
                settings = json.loads(settings)
                for item in settings:
                    widget_preview = dict()
                    widget_preview["widget_id"] = item.get("widget_id")
                    widget_preview["x"] = item.get("x")
                    widget_preview["y"] = item.get("y")
                    widget_preview["width"] = item.get("width")
                    widget_preview["height"] = item.get("height")
                    widget_preview["width"] = item.get("width")
                    widget_preview["id"] = item.get("id")
                    widget_preview["type"] = item.get("type")
                    widget_preview["name"] = item.get("name")
                    widget_preview["widget_language"] = item.get(
                        "widget_language")
                    languages = item.get("multiLangSetting")
                    if type(languages) is dict and lang_code_default \
                        is not None:
                        if languages.get(lang_code_default):
                            data_display = languages.get(lang_code_default)
                            widget_preview["name_display"] = data_display.get(
                                'label')
                        elif languages.get('en'):
                            data_display = languages.get('en')
                            widget_preview["name_display"] = data_display.get(
                                'label')
                        else:
                            widget_preview["name_display"] = \
                                WEKO_GRIDLAYOUT_DEFAULT_WIDGET_LABEL
                    else:
                        widget_preview["name_display"] = \
                            WEKO_GRIDLAYOUT_DEFAULT_WIDGET_LABEL
                    result["data"].append(widget_preview)
    except Exception as e:
        result['error'] = str(e)
    return result


def get_widget_design_setting(repository_id: str,
                              current_language: str) -> dict:
    """Get Widget design setting by repository id.

    :param repository_id: Identifier of the repository.
    :param current_language: The default language.
    :return: Widget design setting.
    """
    result = {
        "widget-settings": [
        ],
        "error": ""
    }
    try:
        widget_setting = WidgetDesignSetting.select_by_repository_id(
            repository_id)
        if widget_setting:
            settings = widget_setting.get('settings')
            if settings:
                settings = json.loads(settings)
                for widget_item in settings:
                    widget = _get_widget_design_item_base_on_current_language(
                        current_language,
                        widget_item)
                    result["widget-settings"].append(widget)
    except Exception as e:
        result['error'] = str(e)
    return result


def _get_widget_design_item_base_on_current_language(current_language,
                                                     widget_item):
    """Get widget design item base on current language.

    :param current_language: The current language.
    :param widget_item: Widget item.
    :return:
    """
    widget = widget_item.copy()
    widget["multiLangSetting"] = dict()
    languages = widget_item.get("multiLangSetting")
    if isinstance(languages, dict):
        for key, value in languages.items():
            if key == current_language:
                widget["multiLangSetting"] = value
                break
    if not widget["multiLangSetting"]:
        default_language_code = WEKO_GRIDLAYOUT_DEFAULT_LANGUAGE_CODE
        if isinstance(languages, dict) \
            and languages.get(default_language_code):
            widget["multiLangSetting"] = languages.get(default_language_code)
        else:
            widget["multiLangSetting"] = {
                "label": WEKO_GRIDLAYOUT_DEFAULT_WIDGET_LABEL,
                "description": {}
            }
    return widget


def update_widget_design_setting(data):
    """Update Widget layout setting.

    :param data: json data is submitted from client side.
    :return: result json.
    """
    result = {
        "result": False,
        "error": ''
    }
    repository_id = data.get('repository_id')
    setting_data = data.get('settings')
    try:
        json_data = json.loads(setting_data)
        if type(json_data) is list:
            for item in json_data:
                widget_item = WidgetItem.get_by_id(item.get('widget_id'))
                widget_setting = json.loads(widget_item.settings)
                item.update(widget_setting)
        setting_data = json.dumps(json_data)
        if repository_id and setting_data:
            if WidgetDesignSetting.select_by_repository_id(repository_id):
                result["result"] = WidgetDesignSetting.update(repository_id,
                                                              setting_data)
            else:
                result["result"] = WidgetDesignSetting.create(repository_id,
                                                              setting_data)
        else:
            result['error'] = "Fail to save Widget design. Please check again."
    except Exception as e:
        result['error'] = str(e)
    return result


def get_widget_type_list():
    """Get all Widget types.

    :param: None
    :return: options json
    """
    widget_types = WidgetType.get_all_widget_types()
    options = []
    if type(widget_types) is list:
        for widget_type in widget_types:
            option = dict()
            option["text"] = widget_type.type_name
            option["value"] = widget_type.type_id
            options.append(option)
    result = {"options": options}

    return result


def update_admin_widget_item_setting(data):
    """Create/update widget item.

    :param: widget item data
    :return: options json
    """
    status = 201
    success = True
    msg = ""
    flag = data.get('flag_edit')
    data_result = data.get('data')
    data_id = data.get('data_id')
    if not data_result:
        success = True
        msg = 'Invalid data.'
    if flag:
        if success:
            if WidgetItems.is_existed(data_result, data_id.get('id')):
                msg = 'Fail to update. Data input to create is exist!'
            else:
                if validate_admin_widget_item_setting(data_id):
                    if not WidgetItems.update_by_id(data_result, data_id):
                        success = False
                        msg = 'Update widget item fail.'
                    else:
                        handle_change_item_in_preview_widget_item(data_id,
                                                                  data_result)
                        msg = 'Widget item updated successfully.'
                else:
                    if not WidgetItems.update_by_id(data_result, data_id):
                        success = False
                        msg = 'Update widget item fail.'
                    else:
                        msg = 'Widget item updated successfully.'
    else:
        if WidgetItems.is_existed(data_result, data_result.get('id')):
            success = False
            msg = 'Fail to create. Data input to create is exist!'
        else:
            if not WidgetItems.create(
                data_result) and not WidgetMultiLangData.create(
                data_result.get('multiLangSetting')):
                success = False
                msg = 'Create widget item fail.'
            else:
                msg = 'Widget item created successfully.'

    return make_response(
        jsonify({'status': status,
                 'success': success,
                 'message': msg}), status)


def delete_item_in_preview_widget_item(data_id, json_data):
    """Delete item in preview widget design.

    Arguments:
        data_id {widget_item} -- [id of widget item]
        json_data {dict} -- [data to be updated]

    Returns:
        [data] -- [data after updated]

    """
    remove_list = []
    if type(json_data) is list:
        for item in json_data:
            if str(item.get('name')) == str(data_id.get('label')) and str(
                item.get('type')) == str(data_id.get('widget_type')):
                remove_list.append(item)
    for item in remove_list:
        json_data.remove(item)
    data = json.dumps(json_data)
    return data


def update_general_item(item, data_result):
    """Update general field item.

    :param item: item need to be update
    :param data_result: result
    """
    item['frame_border'] = data_result.get('frame_border')
    item['frame_border_color'] = data_result.get(
        'frame_border_color')
    item['background_color'] = data_result.get('background_color')
    item['label_color'] = data_result.get('label_color')
    item['text_color'] = data_result.get('text_color')
    item['name'] = data_result.get('label')
    item['type'] = data_result.get('widget_type')
    item['multiLangSetting'] = data_result.get('multiLangSetting')


def update_item_in_preview_widget_item(data_id, data_result, json_data):
    """Update item in preview widget design when it is edited in widget item.

    Arguments:
        data_id {widget_item} -- [id of widget item]
        data_result {widget_item} -- [sent]
        json_data {dict} -- [data to be updated]
    Returns:
        [data] -- [data after updated]

    """
    if type(json_data) is list:
        for item in json_data:
            if str(item.get('widget_id')) == str(data_id.get('id')):
                update_general_item(item, data_result)
    data = json.dumps(json_data)
    return data


def handle_change_item_in_preview_widget_item(data_id, data_result):
    """Handle change when edit widget item effect to widget design.

    Arguments:
        data_id {widget_item} -- [id of widget item]
        data_result {widget_item} -- [data is sent by client]

    Returns:
        [False] -- [handle failed]
        [True] -- [handle success]

    """
    try:
        data = WidgetDesignSetting.select_by_repository_id(
            data_id.get('repository'))
        if data.get('settings'):
            json_data = json.loads(data.get('settings'))
            if str(data_id.get('repository')) != str(data_result.get(
                'repository')) or data_result.get('enable') is False:
                data = delete_item_in_preview_widget_item(data_id, json_data)
            else:
                data = update_item_in_preview_widget_item(
                    data_id, data_result, json_data)
            return WidgetDesignSetting.update(data_id.get('repository'), data)

        return False
    except Exception as e:
        print(e)
        return False


def delete_admin_widget_item_setting(widget_id):
    """Delete widget item.

    :param: widget id
    :return: options json
    """
    status = 201
    success = True
    if validate_admin_widget_item_setting(widget_id):
        success = False
        msg = "Cannot delete this widget because " \
              "it's setting in Widget Design."
    elif not WidgetItems.delete(widget_id):
        success = False
        msg = 'Delete widget item fail.'
    else:
        msg = 'Widget item delete successfully.'

    return make_response(
        jsonify({'status': status,
                 'success': success,
                 'message': msg}), status)


def validate_admin_widget_item_setting(widget_id):
    """Validate widget item.

    :param: widget id
    :return: true if widget item is used in widget design else return false
    """
    try:
        if (type(widget_id)) is dict:
            repository_id = widget_id.get('repository')
            widget_item_id = widget_id.get('id')
        else:
            repository_id = widget_id.repository_id
            widget_item_id = widget_id.id
        data = WidgetDesignSetting.select_by_repository_id(
            repository_id)
        if data.get('settings'):
            json_data = json.loads(data.get('settings'))
            for item in json_data:
                if str(item.get('widget_id')) == str(widget_item_id):
                    return True
        return False
    except Exception as e:
        current_app.logger.error('Failed to validate record: ', e)
        return True


def get_default_language():
    """Get default Language.

    :return:
    """
    result = AdminLangSettings.query.filter_by(is_registered=True).order_by(
        asc('admin_lang_settings_sequence'))
    result = AdminLangSettings.parse_result(result)
    if type(result) is list:
        return result[0]
    return


def get_system_language():
    """Get system language for widget setting.

    Returns:
        result -- dictionary contains language list

    """
    result = {
        'language': [],
        'error': ''
    }
    try:
        sys_lang = AdminLangSettings.load_lang()
        result['language'] = sys_lang
    except Exception as e:
        result['error'] = str(e)

    return result


def build_data(data):
    """Build data get from client to dictionary.

    Arguments:
        data {json} -- Client data

    Returns:
        dictionary -- server data

    """
    result = dict()
    result['repository_id'] = data.get('repository')
    result['widget_type'] = data.get('widget_type')
    result['settings'] = json.dumps(build_data_setting(data))
    result['is_enabled'] = data.get('enable')
    result['multiLangSetting'] = data.get('multiLangSetting')
    result['is_deleted'] = False
    role = data.get('browsing_role')
    if isinstance(role, list):
        result['browsing_role'] = ','.join(str(e) for e in role)
    else:
        result['browsing_role'] = role
    role = data.get('edit_role')
    if isinstance(role, list):
        result['edit_role'] = ','.join(str(e) for e in role)
    else:
        result['edit_role'] = role
    return result


def build_data_setting(data):
    """Build setting pack.

    Arguments:
        data {json} -- client data

    Returns:
        dictionary -- setting pack

    """
    result = dict()
    result['background_color'] = data.get('background_color')
    result['frame_border'] = data.get('frame_border')
    result['frame_border_color'] = data.get('frame_border_color')
    result['label_color'] = data.get('label_color')
    result['text_color'] = data.get('text_color')

    return result


def build_multi_lang_data(widget_id, multi_lang_json):
    """Build multiple language data.

    Arguments:
        widget_id {sequence} -- id of widget
        multi_lang_json {json} -- multiple language data as json

    Returns:
        dictionary -- multiple language data

    """
    if not multi_lang_json:
        return None

    result = list()
    for k, v in multi_lang_json.items():
        new_lang_data = dict()
        new_lang_data['widget_id'] = widget_id
        new_lang_data['lang_code'] = k
        new_lang_data['label'] = v.get('label')
        new_lang_data['description_data'] = json.dumps(v.get('description'))
        result.append(new_lang_data)
    return result


def convert_widget_data_to_dict(widget_data):
    """Convert widget data object to dict.

    Arguments:
        widget_data {object} -- Object data

    Returns:
        dictionary -- dictionary data

    """
    result = dict()
    settings = json.loads(widget_data.settings)

    result['widget_id'] = widget_data.widget_id
    result['repository_id'] = widget_data.repository_id
    result['widget_type'] = widget_data.widget_type
    result['settings'] = settings
    result['browsing_role'] = widget_data.browsing_role
    result['edit_role'] = widget_data.edit_role
    result['is_enabled'] = widget_data.is_enabled
    result['is_deleted'] = widget_data.is_deleted
    return result


def convert_widget_multi_lang_to_dict(multi_lang_data):
    """Convert multiple language data object to dict.

    Arguments:
        multi_lang_data {object} -- object data

    Returns:
        dictionary -- dictionary data

    """
    result = dict()
    description = json.loads(multi_lang_data.description_data)

    result['id'] = multi_lang_data.id
    result['widget_id'] = multi_lang_data.widget_id
    result['lang_code'] = multi_lang_data.lang_code
    result['label'] = multi_lang_data.label
    result['description_data'] = description
    return result


def convert_data_to_desgin_pack(widget_data, list_multi_lang_data):
    """Convert loaded data to widget design data pack.

    Arguments:
        widget_data {dict} -- widget data
        list_multi_lang_data {list} -- List of multiple language data

    Returns:
        dictionary -- widget design data pack

    """
    if not widget_data or not list_multi_lang_data:
        return None
    result = dict()
    result['widget_id'] = widget_data.get('widget_id')
    result['repository_id'] = widget_data.get('repository_id')
    result['widget_type'] = widget_data.get('widget_type')
    result['browsing_role'] = widget_data.get('browsing_role')
    result['edit_role'] = widget_data.get('edit_role')
    result['is_enabled'] = widget_data.get('is_enabled')
    result['is_deleted'] = widget_data.get('is_deleted')

    multi_lang_setting = dict()
    for data in list_multi_lang_data:
        new_data = dict()
        converted_data = convert_widget_multi_lang_to_dict(data)
        new_data['label'] = converted_data.get('label')
        new_data['description'] = converted_data.get('description_data')
        multi_lang_setting[converted_data.get('lang_code')] = new_data
    settings = widget_data.get('settings')
    settings['multiLangSetting'] = multi_lang_setting
    result['settings'] = settings

    return result


def convert_data_to_edit_pack(data):
    """Convert loaded data to edit data pack.

    Arguments:
        data {dict} -- loaded data

    Returns:
        dictionary -- edit data pack

    """
    if not data:
        return None
    result = dict()
    settings = copy.deepcopy(data.get('settings'))
    result['widget_id'] = data.get('widget_id')
    result['background_color'] = settings.get('background_color')
    result['browsing_role'] = data.get('browsing_role')
    result['edit_role'] = data.get('edit_role')
    result['is_enabled'] = data.get('is_enabled')
    result['enable'] = data.get('is_enabled')
    result['frame_border'] = settings.get('frame_border')
    result['frame_border_color'] = settings.get('frame_border_color')
    result['label_color'] = settings.get('label_color')
    result['multiLangSetting'] = settings.get('multiLangSetting')
    result['repository_id'] = data.get('repository_id')
    result['text_color'] = settings.get('text_color')
    result['widget_type'] = data.get('widget_type')
    return result
