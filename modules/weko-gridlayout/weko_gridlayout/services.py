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

import copy
import json

from invenio_db import db

from .config import WEKO_GRIDLAYOUT_DEFAULT_WIDGET_LABEL
from .models import WidgetDesignSetting, WidgetItem
from .utils import update_general_item


class WidgetItemServices:
    """Services for Widget item setting."""

    def create(widget_data):
        result = dict()
        if not widget_data:
            result['error'] = 'Widget data is empty'
            return result

        # session = db.session
        multi_lang_data = copy.deepcopy(widget_data.get('multiLangSetting'))
        if not multi_lang_data:
            result['error'] = 'Multiple language data is empty'

        del widget_data['multiLangSetting']
        # with session.begin_nested():


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
                    data["widgetId"] = widget_item.repository_id
                    data["widgetType"] = widget_item.widget_type
                    data["widgetLabel"] = widget_item.label
                    data["Id"] = widget_item.id
                    settings = widget_item.settings
                    settings = json.loads(settings)
                    languages = settings.get("multiLangSetting")
                    if type(languages) is dict and \
                            lang_code_default is not None:
                        if languages.get(lang_code_default):
                            data_display = languages[lang_code_default]
                            data["widgetLabelDisplay"] = data_display.get(
                                'label')
                        elif languages.get('en'):
                            data_display = languages['en']
                            data["widgetLabelDisplay"] = data_display.get(
                                'label')
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
                        widget_preview["widget_language"] = item.get(
                            "widget_language")
                        languages = item.get("multiLangSetting")
                        if type(languages) is dict and lang_code_default \
                                is not None:
                            if languages.get(lang_code_default):
                                data_display = languages.get(lang_code_default)
                                widget_preview[
                                    "name_display"] = data_display.get(
                                    'label')
                            elif languages.get('en'):
                                data_display = languages.get('en')
                                widget_preview[
                                    "name_display"] = data_display.get(
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
                    widget_item = WidgetItem.get_by_id(item.get('widget_id'))
                    widget_setting = json.loads(widget_item.settings)
                    item.update(widget_setting)
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
    def update_item_in_preview_widget_item(cls, data_id, data_result,
                                           json_data):
        """Update item in preview widget when it is edited in widget item.

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

    @classmethod
    def handle_change_item_in_preview_widget_item(cls, data_id, data_result):
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
                    data = cls.delete_item_in_preview_widget_item(data_id,
                                                                  json_data)
                else:
                    data = cls.update_item_in_preview_widget_item(
                        data_id, data_result, json_data)
                return WidgetDesignSetting.update(data_id.get('repository'),
                                                  data)

            return False
        except Exception as e:
            print(e)
            return False


class TopPageServices:
    pass
