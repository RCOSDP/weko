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

"""Service for widget modules."""
import copy
import json

from flask import current_app
from invenio_db import db
from invenio_records.models import RecordMetadata
from sqlalchemy.dialects import postgresql
from sqlalchemy import cast

from .config import WEKO_GRIDLAYOUT_DEFAULT_LANGUAGE_CODE, \
    WEKO_GRIDLAYOUT_DEFAULT_WIDGET_LABEL
from .models import WidgetDesignSetting, WidgetItem, WidgetMultiLangData
from .utils import build_data, build_multi_lang_data, \
    convert_data_to_desgin_pack, convert_data_to_edit_pack, \
    convert_widget_data_to_dict, convert_widget_multi_lang_to_dict, \
    update_general_item, get_role_list


class WidgetItemServices:
    """Services for Widget item setting."""

    @classmethod
    def get_repo_by_id(cls, widget_id):
        """Get repository of widget item by widget id.

        Arguments:
            widget_id {int} -- id of widget item
        """
        widget_item = WidgetItem.get_by_id(widget_id)
        return widget_item.repository_id

    @classmethod
    def save_command(cls, data):
        """Handle save command for edit and create.

        Arguments:
            data {json} -- data to save

        Returns:
            dict -- saved result

        """
        result = {
            'message': '',
            'success': False
        }
        if not data:
            result['message'] = 'No data saved!'
            return result
        widget_data = data.get('data')
        repository = widget_data.get('repository')
        type_id = widget_data.get('widget_type')
        multi_lang_data = widget_data.get('multiLangSetting')
        current_id = None
        if data.get('data_id'):
            current_id = data.get('data_id')
        for k, v in multi_lang_data.items():
            if cls.is_exist(repository, type_id, k, v.get('label'),
                            current_id):
                result['message'] = 'Save fail. Data input to create is exist!'
                return result
        if data.get('flag_edit'):
            old_repo = cls.get_repo_by_id(current_id)
            if (str(old_repo) != str(widget_data.get('repository')) and
                WidgetDesignServices.validate_admin_widget_item_setting(
                    data.get('data_id'))):
                result['message'] = "Cannot update repository " \
                                 "of this widget because " \
                                 "it's setting in Widget Design."
                result['success'] = False
                return result

            respond = cls.update_by_id(
                data.get('data_id'),
                build_data(widget_data))

            if WidgetDesignServices.validate_admin_widget_item_setting(
                    data.get('data_id')):
                WidgetDesignServices.handle_change_item_in_preview_widget_item(
                    data.get('data_id'), widget_data)
            if respond['error']:
                result['message'] = respond['error']
            else:
                result['message'] = 'Widget item updated successfully.'
                result['success'] = True
        else:
            respond = cls.create(build_data(widget_data))
            if respond['error']:
                result['message'] = respond['error']
            else:
                result['message'] = 'Widget item saved successfully.'
                result['success'] = True
        return result

    @classmethod
    def get_by_id(cls, widget_id):
        """Get widget by widget id.

        Arguments:
            widget_id {sequence} -- The widget id

        Returns:
            dictionary -- widget data

        """
        result = {
            'widget_data': '',
            'error': ''
        }
        widget_data = WidgetItem.get_by_id(widget_id)
        multi_lang_data = WidgetMultiLangData.get_by_widget_id(widget_id)
        if not widget_data or not multi_lang_data:
            result['error'] = 'No widget found!'
            return result

        lang_data = dict()
        for data in multi_lang_data:
            new_data = dict()
            new_data['label'] = multi_lang_data.get('label')
            new_data['description'] = multi_lang_data.get('description_data')
            lang_data[multi_lang_data.get('lang_code')] = new_data
        widget_data['multiLangSetting'] = lang_data
        result['widget_data'] = widget_data
        return result

    @classmethod
    def create(cls, widget_data):
        """Create new widget.

        Arguments:
            widget_data {dictionary} -- widget data

        Returns:
            dict -- error message

        """
        result = {
            'error': ''
        }
        if not widget_data:
            result['error'] = 'Widget data is empty!'
            return result

        session = db.session
        multi_lang_data = copy.deepcopy(widget_data.get('multiLangSetting'))
        if not multi_lang_data:
            result['error'] = 'Multiple language data is empty'
            return result

        del widget_data['multiLangSetting']
        try:
            with session.begin_nested():
                next_id = WidgetItem.get_sequence(session)
                widget_data['widget_id'] = next_id
                WidgetItem.create(widget_data, session)
                list_multi_lang_data = build_multi_lang_data(
                    next_id,
                    multi_lang_data)
                for data in list_multi_lang_data:
                    WidgetMultiLangData.create(data, session)
            session.commit()
        except Exception as e:
            import traceback
            traceback.print_exc()
            result['error'] = str(e)
            current_app.logger.debug(e)
            session.rollback()
        return result

    @classmethod
    def update_by_id(cls, widget_id, widget_data):
        """Update widget by id.

        Arguments:
            widget_id {sequence} -- The widget id
            widget_data {dict} -- The widget data

        Returns:
            dict -- error message

        """
        result = {
            'error': ''
        }
        if not widget_data or not widget_id:
            result['error'] = 'Widget data is empty!'
            return result

        multi_lang_data = copy.deepcopy(widget_data.get('multiLangSetting'))
        if not multi_lang_data:
            result['error'] = 'Multiple language data is empty'
            return result
        del widget_data['multiLangSetting']
        session = db.session
        try:
            with session.begin_nested():
                WidgetItem.update_by_id(widget_id, widget_data, session)
                WidgetMultiLangData.delete_by_widget_id(widget_id, session)
                list_multi_lang_data = build_multi_lang_data(
                    widget_id,
                    multi_lang_data)
                for data in list_multi_lang_data:
                    WidgetMultiLangData.create(data, session)
            session.commit()
        except Exception as e:
            result['error'] = str(e)
            current_app.logger.debug(e)
            session.rollback()
        return result

    @classmethod
    def delete_by_id(cls, widget_id):
        """Delete widget by id.

        Arguments:
            widget_id {sequence} -- The widget id

        Returns:
            dict -- error message

        """
        result = {
            'message': ''
        }
        if not widget_id:
            result['message'] = 'Could not found widget item in data base.'
            return result

        if WidgetDesignServices.validate_admin_widget_item_setting(widget_id):
            result['message'] = "Cannot delete this widget because " \
                               "it's setting in Widget Design."
            return result
        session = db.session
        try:
            with session.begin_nested():
                WidgetItem.delete_by_id(widget_id, session)
                WidgetMultiLangData.delete_by_widget_id(widget_id, session)
            session.commit()
            result['message'] = 'Widget item has deleted successfully.'
        except Exception as e:
            result['message'] = str(e)
            current_app.logger.debug(e)
            session.rollback()
        return result

    @classmethod
    def delete_multi_item_by_id(cls, widget_id, session):
        """Delete widget by id.

        Arguments:
            widget_id {sequence} -- The widget id

        Returns:
            dict -- error message

        """
        WidgetItem.delete_by_id(widget_id, session)
        WidgetMultiLangData.delete_by_widget_id(widget_id, session)

    @classmethod
    def is_exist(cls, repository_id, type_id, lang_code, label, current_id):
        """Check widget is exist or not.

        Arguments:
            repository_id {string} -- The repository id
            type_id {string} -- The type id
            lang_code {string} -- The language code
            label {string} -- The label

        Returns:
            boolean -- True if widget already exist

        """
        list_id = WidgetItem.get_id_by_repository_and_type(
                repository_id, type_id)
        if not list_id:
            return False

        if current_id and current_id in list_id:
            list_id.remove(current_id)
        for id in list_id:
            multi_lang_data = WidgetMultiLangData.query.filter_by(widget_id = id, is_deleted=False).all()
            if multi_lang_data:
                for data in multi_lang_data:
                    dict_data = convert_widget_multi_lang_to_dict(data)
                    if (dict_data.get('label') == label and
                            dict_data.get('lang_code') == lang_code):
                        return True
        return False

    @classmethod
    def get_widget_data_by_widget_id(cls, widget_id):
        """Get widget data for widget design by id.

        Arguments:
            widget_id {sequence} -- The widget id

        Returns:
            dict -- The widget data(design format)

        """
        if not widget_id:
            return None
        widget_data = convert_widget_data_to_dict(
            WidgetItem.get_by_id(widget_id))
        multi_lang_data = WidgetMultiLangData.get_by_widget_id(widget_id)
        result = convert_data_to_desgin_pack(widget_data, multi_lang_data)
        return result

    @classmethod
    def load_edit_pack(cls, widget_id):
        """Get widget data for widget edit by id.

        Arguments:
            widget_id {sequence} -- The widget id

        Returns:
            dict -- The widget data(edit format)

        """
        if not widget_id:
            return None
        widget_data = convert_widget_data_to_dict(
            WidgetItem.get_by_id(widget_id))
        multi_lang_data = WidgetMultiLangData.get_by_widget_id(widget_id)
        converted_data = convert_data_to_desgin_pack(
            widget_data,
            multi_lang_data)
        result = convert_data_to_edit_pack(converted_data)
        return result


class WidgetDesignServices:
    """Services for Widget item setting."""

    @classmethod
    def get_repository_list(cls):
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

    @classmethod
    def get_widget_list(cls, repository_id, default_language):
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
                    widget_item_data = \
                        WidgetItemServices.get_widget_data_by_widget_id(
                            widget_item.widget_id)
                    data["widgetId"] = widget_item_data.get('repository_id')
                    data["widgetType"] = widget_item_data.get('widget_type')
                    data["Id"] = widget_item_data.get('widget_id')
                    settings = widget_item_data.get('settings')
                    languages = settings.get("multiLangSetting")
                    if (type(languages) is dict and
                            lang_code_default is not None):
                        if languages.get(lang_code_default):
                            data_display = languages[lang_code_default]
                            data["label"] = data_display.get(
                                'label')
                        elif languages.get('en'):
                            data_display = languages['en']
                            data["label"] = data_display.get(
                                'label')
                        else:
                            data["label"] = \
                                WEKO_GRIDLAYOUT_DEFAULT_WIDGET_LABEL
                    else:
                        data["label"] = \
                            WEKO_GRIDLAYOUT_DEFAULT_WIDGET_LABEL
                    result["data"].append(data)
        except Exception as e:
            result["error"] = str(e)

        return result

    @classmethod
    def get_widget_preview(cls, repository_id, default_language):
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
                        languages = item.get("multiLangSetting")
                        if type(languages) is dict and lang_code_default \
                                is not None:
                            if languages.get(lang_code_default):
                                data_display = languages.get(lang_code_default)
                                widget_preview["name"] = data_display.get(
                                    'label')
                            elif languages.get('en'):
                                data_display = languages.get('en')
                                widget_preview["name"] = data_display.get(
                                    'label')
                            else:
                                widget_preview["name"] = \
                                    WEKO_GRIDLAYOUT_DEFAULT_WIDGET_LABEL
                        else:
                            widget_preview["name"] = \
                                WEKO_GRIDLAYOUT_DEFAULT_WIDGET_LABEL
                        result["data"].append(widget_preview)
        except Exception as e:
            result['error'] = str(e)
        return result

    @classmethod
    def get_widget_design_setting(cls, repository_id: str,
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
                        widget = cls._get_design_base_on_current_language(
                            current_language,
                            widget_item)
                        result["widget-settings"].append(widget)
        except Exception as e:
            result['error'] = str(e)
        return result

    @classmethod
    def _get_design_base_on_current_language(cls, current_language,
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
            if (isinstance(languages, dict) and
                    languages.get(default_language_code)):
                widget["multiLangSetting"] = languages.get(
                    default_language_code)
            else:
                widget["multiLangSetting"] = {
                    "label": WEKO_GRIDLAYOUT_DEFAULT_WIDGET_LABEL,
                    "description": {}
                }
        return widget

    @classmethod
    def update_widget_design_setting(cls, data):
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
                    widget_item = \
                        WidgetItemServices.get_widget_data_by_widget_id(
                            item.get('widget_id'))
                    item.update(widget_item.get('settings'))
            setting_data = json.dumps(json_data)
            if repository_id and setting_data:
                if WidgetDesignSetting.select_by_repository_id(repository_id):
                    result["result"] = WidgetDesignSetting.update(
                        repository_id, setting_data)
                else:
                    result["result"] = WidgetDesignSetting.create(
                        repository_id, setting_data)
            else:
                result[
                    'error'] = "Fail to save Widget design. " \
                               "Please check again."
        except Exception as e:
            result['error'] = str(e)
        return result

    @classmethod
    def delete_item_in_preview_widget_item(cls, data_id, json_data):
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

    @classmethod
    def update_item_in_preview_widget_item(cls, widget_id, data_result,
                                           json_data):
        """Update item in preview widget when it is edited in widget item.

        Arguments:
            widget_id {int} -- [widget id of widget item]
            data_result {widget_item} -- data receive from client
            json_data {dict} -- data to be updated
        Returns:
            [data] -- [data after updated]

        """
        if type(json_data) is list:
            for item in json_data:
                if str(item.get('widget_id')) == str(widget_id):
                    update_general_item(item, data_result)
        data = json.dumps(json_data)
        return data

    @classmethod
    def handle_change_item_in_preview_widget_item(cls, widget_id, data_result):
        """Handle change when edit widget item effect to widget design.

        Arguments:
            data_id {widget_item} -- [id of widget item]
            data_result {widget_item} -- [data is sent by client]

        Returns:
            [False] -- [handle failed]
            [True] -- [handle success]

        """
        try:
            repo_id = WidgetItemServices.get_repo_by_id(widget_id)
            data = WidgetDesignSetting.select_by_repository_id(repo_id)
            if data.get('settings'):
                json_data = json.loads(data.get('settings'))
                data = cls.update_item_in_preview_widget_item(
                    widget_id, data_result, json_data)
                return WidgetDesignSetting.update(repo_id,
                                                  data)

            return False
        except Exception as e:
            print(e)
            return False

    @classmethod
    def validate_admin_widget_item_setting(cls, widget_id):
        """Validate widget item.

        :param: widget id
        :return: true if widget item is used in widget design else return false
        """
        try:
            if widget_id:
                widget_item_id = widget_id
                repo_id = WidgetItemServices.get_repo_by_id(widget_id)
                data = WidgetDesignSetting.select_by_repository_id(
                    repo_id)
                if data.get('settings'):
                    json_data = json.loads(data.get('settings'))
                    for item in json_data:
                        if str(item.get('widget_id')) == str(widget_item_id):
                            return True
            return False
        except Exception as e:
            current_app.logger.error('Failed to validate record: ', e)
            return True


class WidgetDataLoaderServices:
    """Services for load data to page."""

    @classmethod
    def get_new_arrivals_data(cls, list_dates, number_result, rss_status):
        """Get new arrivals data from DB.

        Returns:
            dictionary -- new arrivals data

        """
        result = {
            'data': '',
            'error': ''
        }
        if not list_dates or number_result == 0:
            return None
        try:
            data = list()
            for date in list_dates:
                records = db.session.query(RecordMetadata).filter(
                    RecordMetadata.json['pubdate']['attribute_value'] == cast(
                        date,
                        postgresql.JSONB),
                    RecordMetadata.json['publish_status'] == cast(
                        "1",
                        postgresql.JSONB)
                ).all()
                for record in records:
                    record_data = record.json
                    new_data = dict()
                    new_data['name'] = record_data['item_title']
                    new_data['url'] = '/records/' + \
                        record_data['control_number']
                    new_data['roles'] = get_role_list(record_data['path'])
                    rss = dict()
                    if rss_status:
                        rss = cls.get_arrivals_rss()
                    new_data['rss'] = rss
                    if (len(data) < int(number_result)):
                        data.append(new_data)
                    else:
                        break
            result['data'] = data
        except Exception as e:
            result['error'] = str(e)
        return result

    @classmethod
    def get_arrivals_rss(cls):
        result = dict()
        return result
