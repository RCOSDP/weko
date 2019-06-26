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
from sqlalchemy import cast
from sqlalchemy.dialects import postgresql

from .config import WEKO_GRIDLAYOUT_DEFAULT_LANGUAGE_CODE, \
    WEKO_GRIDLAYOUT_DEFAULT_WIDGET_LABEL
from .models import WidgetDesignSetting, WidgetItem, WidgetMultiLangData
from .utils import build_data, build_multi_lang_data, \
    convert_data_to_desgin_pack, convert_data_to_edit_pack, \
    convert_widget_data_to_dict, convert_widget_multi_lang_to_dict, \
    update_general_item, build_rss_xml


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
            new_data['label'] = data.get('label')
            new_data['description'] = data.get('description_data')
            lang_data[data.get('lang_code')] = new_data
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
        for widget_id in list_id:
            multi_lang_data = WidgetMultiLangData.query.filter_by(
                widget_id=widget_id, is_deleted=False).all()
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
                    RecordMetadata.json['pubdate']["attribute_value"] == cast(
                        date,
                        postgresql.JSONB),
                    RecordMetadata.json['publish_status'] == cast(
                        "0",
                        postgresql.JSONB)
                ).order_by(RecordMetadata.updated.desc()).all()
                for record in records:
                    record_data = record.json
                    new_data = dict()
                    new_data['name'] = record_data['item_title']
                    new_data['url'] = '/records/' \
                                      + record_data['control_number']
                    rss = dict()
                    if rss_status:
                        rss = cls.get_arrivals_rss()
                    new_data['rss'] = rss
                    if len(data) < int(number_result):
                        data.append(new_data)
                    else:
                        break
                if len(data) == int(number_result):
                    break
            result['data'] = data
        except Exception as e:
            result['error'] = str(e)
        return result

    @classmethod
    def get_arrivals_rss(cls):
        """Get New Arrivals RSS.

        :type: object
        """
        data = {
            "took": 8,
            "timed_out": False,
            "_shards": {
                "total": 23,
                "successful": 23,
                "failed": 0
            },
            "hits": {
                "total": 3,
                "max_score": 0.55880964,
                "hits": [{
                    "_index": "weko-jpcoar-v1.0.0",
                    "_type": "item",
                    "_id": "0d35de8f-9601-4c1b-b5ff-4aeb8f80b1dc",
                    "_score": 0.55880964,
                    "_source": {
                        "weko_creator_id": "1",
                        "itemtype": "BaseView",
                        "_item_metadata": {
                            "item_1560938217591": {
                                "attribute_name": "課金ファイル",
                                "attribute_value_mlt": [{
                                    "groupsprice": [{}]
                                }]
                            },
                            "item_1554881204737": {
                                "attribute_name": "Title",
                                "attribute_value_mlt": [{
                                    "subitem_1551255647225": "Zannaghazi",
                                    "subitem_1551255648112": "en"
                                }]
                            },
                            "pubdate": {
                                "attribute_name": "公開日",
                                "attribute_value": "2019-06-25"
                            },
                            "item_title": "Zannaghazi",
                            "item_type_id": "116",
                            "control_number": "1",
                            "_oai": {
                                "id": "oai:invenio:recid/1"
                            },
                            "weko_shared_id": -1,
                            "owner": "1",
                            "custom_sort": {
                                "1561432655406": ""
                            },
                            "path": ["1561432655406"],
                            "publish_status": "1"
                        },
                        "publish_status": "0",
                        "title": ["Zannaghazi"],
                        "_oai": {
                            "id": "oai:invenio:recid/1"
                        },
                        "weko_shared_id": -1,
                        "_created": "2019-06-25T03:22:53.980352+00:00",
                        "custom_sort": {
                            "1561432655406": ""
                        },
                        "control_number": "1",
                        "path": ["1561432655406"],
                        "_updated": "2019-06-25T03:23:00.090339+00:00",
                        "publish_date": "2019-06-25",
                        "relation_version_is_last": True
                    }
                }, {
                    "_index": "weko-jpcoar-v1.0.0",
                    "_type": "item",
                    "_id": "70aae405-d943-4f51-a0f6-14db8c920a15",
                    "_score": 0.047463723,
                    "_source": {
                        "weko_creator_id": "1",
                        "identifierRegistration": [{
                            "identifierType": "DataCite",
                            "value": "123"
                        }],
                        "pageEnd": ["123"],
                        "volume": ["123"],
                        "dissertationNumber": ["123"],
                        "version": ["123"],
                        "numPages": ["123"],
                        "relation": {
                            "relatedTitle": ["123"],
                            "relatedIdentifier": [{
                                "identifierType": "NAID",
                                "value": "123"
                            }]
                        },
                        "title": ["Test1"],
                        "control_number": "3",
                        "apc": ["Not required"],
                        "accessRights": ["embargoed access"],
                        "temporal": ["123"],
                        "language": ["arm"],
                        "identifier": [{
                            "identifierType": "HDL",
                            "value": "123"
                        }],
                        "degreeGrantor": {
                            "nameIdentifier": ["123"],
                            "degreeGrantorName": ["123"]
                        },
                        "sourceIdentifier": [{
                            "identifierType": "NCID",
                            "value": "123"
                        }],
                        "_created": "2019-06-25T07:38:47.313901+00:00",
                        "date": [{
                            "value": "2019-06-19",
                            "dateType": "Submitted"
                        }],
                        "_updated": "2019-06-25T07:38:53.698017+00:00",
                        "publish_date": "2019-06-25",
                        "rights": ["123"],
                        "contributor": {
                            "contributorName": ["123"],
                            "nameIdentifier": ["123"],
                            "affiliation": {
                                "nameIdentifier": ["123"],
                                "affiliationName": ["123"]
                            },
                            "contributorAlternative": ["123"],
                            "familyName": ["123"],
                            "givenName": ["123"]
                        },
                        "creator": {
                            "nameIdentifier": ["123"],
                            "creatorName": ["Zan"],
                            "creatorAlternative": ["123"],
                            "givenName": ["123"],
                            "familyName": ["123"],
                            "affiliation": {
                                "nameIdentifier": ["123"],
                                "affiliationName": ["123"]
                            }
                        },
                        "geoLocation": {
                            "geoLocationPoint": {
                                "pointLongitude": ["123"],
                                "pointLatitude": ["123"]
                            },
                            "geoLocationPlace": ["123"],
                            "geoLocationBox": {
                                "eastBoundLongitude": ["123"],
                                "northBoundLatitude": ["123"],
                                "southBoundLatitude": ["123"],
                                "westBoundLongitude": ["123"]
                            }
                        },
                        "type": ["departmental bulletin paper"],
                        "sourceTitle": ["123"],
                        "issue": ["123"],
                        "rightsHolder": {
                            "nameIdentifier": ["123"],
                            "rightsHolderName": ["123"]
                        },
                        "path": ["1561432655406"],
                        "itemtype": "Multiple",
                        "alternative": ["Test2"],
                        "description": ["123"],
                        "degreeName": ["123"],
                        "conference": {
                            "conferenceCountry": ["asm"],
                            "conferenceName": ["123"],
                            "conferenceSequence": ["123"],
                            "conferencePlace": ["123"]
                        },
                        "dateGranted": ["2019-06-20"],
                        "subject": [{
                            "subjectScheme": "MeSH",
                            "value": "123"
                        }],
                        "_item_metadata": {
                            "item_1551264447183": {
                                "attribute_name": "Access Rights",
                                "attribute_value_mlt": [{
                                    "subitem_1551257578398": "123",
                                    "subitem_1551257553743": "embargoed access"
                                }]
                            },
                            "item_1551265002099": {
                                "attribute_name": "Language",
                                "attribute_value_mlt": [{
                                    "subitem_1551255818386": "arm"
                                }]
                            },
                            "item_1551264974654": {
                                "attribute_name": "Date",
                                "attribute_value_mlt": [{
                                    "subitem_1551255753471": "2019-06-19",
                                    "subitem_1551255775519": "Submitted"
                                }]
                            },
                            "item_1551265438256": {
                                "attribute_name": "Source Title",
                                "attribute_value_mlt": [{
                                    "subitem_1551256349044": "123",
                                    "subitem_1551256350188": "ab"
                                }]
                            },
                            "pubdate": {
                                "attribute_name": "公開日",
                                "attribute_value": "2019-06-25"
                            },
                            "item_1551264767789": {
                                "attribute_name": "Rights Holder",
                                "attribute_value_mlt": [{
                                    "subitem_1551257249371": [{
                                        "subitem_1551257257683": "sq",
                                        "subitem_1551257255641": "123"
                                    }],
                                    "subitem_1551257138324": "123",
                                    "subitem_1551257143244": [{
                                        "subitem_1551257145912": "123",
                                        "subitem_1551257232980": "123",
                                        "subitem_1551257156244": "NRID"
                                    }]
                                }]
                            },
                            "item_1551265326081": {
                                "attribute_name": "Geo Location",
                                "attribute_value_mlt": [{
                                    "subitem_1551256775293": "123123123",
                                    "subitem_1551256842196": "123",
                                    "subitem_1551256822219": [{
                                        "subitem_1551256824945": "123",
                                        "subitem_1551256834732": "123",
                                        "subitem_1551256840435": "123",
                                        "subitem_1551256831892": "123"
                                    }],
                                    "subitem_1551256778926": [{
                                        "subitem_1551256783928": "123",
                                        "subitem_1551256814806": "123"
                                    }]
                                }]
                            },
                            "item_1551264822581": {
                                "attribute_name": "Subject",
                                "attribute_value_mlt": [{
                                    "subitem_1551257343002": "123",
                                    "subitem_1551257323812": "ak",
                                    "subitem_1551257315453": "123",
                                    "subitem_1551257329877": "MeSH"
                                }]
                            },
                            "item_1551265032053": {
                                "attribute_name": "Resource Type",
                                "attribute_value_mlt": [{
                                    "subitem_1551255877772": "departmental bulletin paper",
                                    "subitem_1551255930377": "123"
                                }]
                            },
                            "item_1551265075370": {
                                "attribute_name": "Version",
                                "attribute_value_mlt": [{
                                    "subitem_1551255975405": "123"
                                }]
                            },
                            "item_1551264418667": {
                                "attribute_name": "Contributor",
                                "attribute_value_mlt": [{
                                    "subitem_1551257272214": [{
                                        "subitem_1551257316910": "as",
                                        "subitem_1551257314588": "123"
                                    }],
                                    "subitem_1551257372442": [{
                                        "subitem_1551257375939": "as",
                                        "subitem_1551257374288": "123"
                                    }],
                                    "subitem_1551257339190": [{
                                        "subitem_1551257343979": "aa",
                                        "subitem_1551257342360": "123"
                                    }],
                                    "subitem_1551257036415": "Distributor",
                                    "subitem_1551257150927": [{
                                        "subitem_1551257172531": "ORCID",
                                        "subitem_1551257152742": "123",
                                        "subitem_1551257228080": "123"
                                    }],
                                    "subitem_1551257419251": [{
                                        "subitem_1551257421633": [{
                                            "subitem_1551261493409": "123",
                                            "subitem_1551261485670": "ISNI",
                                            "subitem_1551261472867": "123"
                                        }],
                                        "subitem_1551261534334": [{
                                            "subitem_1551261546333": "ab",
                                            "subitem_1551261542403": "123"
                                        }]
                                    }],
                                    "subitem_1551257245638": [{
                                        "subitem_1551257279831": "aa",
                                        "subitem_1551257276108": "123"
                                    }]
                                }]
                            },
                            "item_1551265790591": {
                                "attribute_name": "Degree Name",
                                "attribute_value_mlt": [{
                                    "subitem_1551256126428": "123",
                                    "subitem_1551256129013": "av"
                                }]
                            },
                            "item_1551264629907": {
                                "attribute_name": "Rights",
                                "attribute_value_mlt": [{
                                    "subitem_1551257025236": [{
                                        "subitem_1551257043769": "123",
                                        "subitem_1551257047388": "sq"
                                    }],
                                    "subitem_1551257030435": "123"
                                }]
                            },
                            "item_1551264326373": {
                                "attribute_name": "Alternative Title",
                                "attribute_value_mlt": [{
                                    "subitem_1551255721061": "ab",
                                    "subitem_1551255720400": "Test2"
                                }]
                            },
                            "item_1551266003379": {
                                "attribute_name": "File",
                                "attribute_value_mlt": [{
                                    "subitem_1551255558587": [{
                                        "subitem_1551255581435": "fulltext",
                                        "subitem_1551255570271": "123",
                                        "subitem_1551255628842": "123"
                                    }],
                                    "subitem_1551255750794": "NUT",
                                    "subitem_1551255854908": "123",
                                    "subitem_1551255820788": [{
                                        "subitem_1551255828320": "2019-06-13",
                                        "subitem_1551255833133": "Issued"
                                    }],
                                    "subitem_1551255788530": "123"
                                }]
                            },
                            "item_1551265553273": {
                                "attribute_name": "Number of Pages",
                                "attribute_value_mlt": [{
                                    "subitem_1551256248092": "123"
                                }]
                            },
                            "item_1551265973055": {
                                "attribute_name": "Conference",
                                "attribute_value_mlt": [{
                                    "subitem_1551255947515": [{
                                        "subitem_1551255951127": "123",
                                        "subitem_1551255953139": "ar"
                                    }],
                                    "subitem_1551255911301": [{
                                        "subitem_1551255924068": "ak",
                                        "subitem_1551255919792": "123"
                                    }],
                                    "subitem_1551255945595": "123",
                                    "subitem_1551255973390": "asm"
                                }]
                            },
                            "item_1551265147138": {
                                "attribute_name": "Identifier",
                                "attribute_value_mlt": [{
                                    "subitem_1551256116088": "123",
                                    "subitem_1551256122128": "HDL"
                                }]
                            },
                            "item_1551264605515": {
                                "attribute_name": "APC",
                                "attribute_value_mlt": [{
                                    "subitem_1551257776901": "Not required"
                                }]
                            },
                            "item_1551265302120": {
                                "attribute_name": "Temporal",
                                "attribute_value_mlt": [{
                                    "subitem_1551256918211": "123",
                                    "subitem_1551256920086": "ak"
                                }]
                            },
                            "item_1551265903092": {
                                "attribute_name": "Degree Grantor",
                                "attribute_value_mlt": [{
                                    "subitem_1551256037922": [{
                                        "subitem_1551256047619": "av",
                                        "subitem_1551256042287": "123"
                                    }],
                                    "subitem_1551256015892": [{
                                        "subitem_1551256027296": "123",
                                        "subitem_1551256029891": "123"
                                    }]
                                }]
                            },
                            "item_1551264308487": {
                                "attribute_name": "Title",
                                "attribute_value_mlt": [{
                                    "subitem_1551255647225": "Test1",
                                    "subitem_1551255648112": "en"
                                }]
                            },
                            "item_1551264340087": {
                                "attribute_name": "Creator",
                                "attribute_value_mlt": [{
                                    "subitem_1551255929209": [{
                                        "subitem_1551255964991": "en",
                                        "subitem_1551255938498": "123"
                                    }],
                                    "subitem_1551256025394": [{
                                        "subitem_1551256055588": "av",
                                        "subitem_1551256035730": "123"
                                    }],
                                    "subitem_1551255991424": [{
                                        "subitem_1551256007414": "aa",
                                        "subitem_1551256006332": "123"
                                    }],
                                    "subitem_1551255898956": [{
                                        "subitem_1551255907416": "vi",
                                        "subitem_1551255905565": "Zan"
                                    }],
                                    "subitem_1551256087090": [{
                                        "subitem_1551256089084": [{
                                            "subitem_1551256145018": "NRID",
                                            "subitem_1551256097891": "123",
                                            "subitem_1551256147368": "123"
                                        }],
                                        "subitem_1551256229037": [{
                                            "subitem_1551256259183": "123",
                                            "subitem_1551256259899": "an"
                                        }]
                                    }],
                                    "subitem_1551255789000": [{
                                        "subitem_1551255795486": "123",
                                        "subitem_1551255793478": "123",
                                        "subitem_1551255794292": "e-Rad"
                                    }]
                                }]
                            },
                            "item_1551264846237": {
                                "attribute_name": "Description",
                                "attribute_value_mlt": [{
                                    "subitem_1551255577890": "123",
                                    "subitem_1551255592625": "af",
                                    "subitem_1551255637472": "TableOfContents"
                                }]
                            },
                            "item_1551265569218": {
                                "attribute_name": "Page Start",
                                "attribute_value_mlt": [{
                                    "subitem_1551256198917": "123"
                                }]
                            },
                            "item_1551265178780": {
                                "attribute_name": "Identifier Registration",
                                "attribute_value_mlt": [{
                                    "subitem_1551256259586": "DataCite",
                                    "subitem_1551256250276": "123"
                                }]
                            },
                            "item_1551265738931": {
                                "attribute_name": "Dissertation Number",
                                "attribute_value_mlt": [{
                                    "subitem_1551256171004": "123"
                                }]
                            },
                            "item_1551265118680": {
                                "attribute_name": "Version Type",
                                "attribute_value_mlt": [{
                                    "subitem_1551256025676": "VoR"
                                }]
                            },
                            "item_1551264917614": {
                                "attribute_name": "Publisher",
                                "attribute_value_mlt": [{
                                    "subitem_1551255702686": "123",
                                    "subitem_1551255710277": "sq"
                                }]
                            },
                            "item_1551265811989": {
                                "attribute_name": "Date Granted",
                                "attribute_value_mlt": [{
                                    "subitem_1551256096004": "2019-06-20"
                                }]
                            },
                            "item_1551265409089": {
                                "attribute_name": "Source Identifier",
                                "attribute_value_mlt": [{
                                    "subitem_1551256405981": "123",
                                    "subitem_1551256409644": "NCID"
                                }]
                            },
                            "item_1551265603279": {
                                "attribute_name": "Page End",
                                "attribute_value_mlt": [{
                                    "subitem_1551256185532": "123"
                                }]
                            },
                            "item_1551265227803": {
                                "attribute_name": "Relation",
                                "attribute_value_mlt": [{
                                    "subitem_1551256465077": [{
                                        "subitem_1551256629524": "NAID",
                                        "subitem_1551256478339": "123"
                                    }],
                                    "subitem_1551256480278": [{
                                        "subitem_1551256513476": "af",
                                        "subitem_1551256498531": "123"
                                    }],
                                    "subitem_1551256387752": "123",
                                    "subitem_1551256388439": "references"
                                }]
                            },
                            "item_1551265385290": {
                                "attribute_name": "Funding Reference",
                                "attribute_value_mlt": [{
                                    "subitem_1551256665850": [{
                                        "subitem_1551256671920": "123",
                                        "subitem_1551256679403": "123"
                                    }],
                                    "subitem_1551256454316": [{
                                        "subitem_1551256614960": "123",
                                        "subitem_1551256619706": "GRID"
                                    }],
                                    "subitem_1551256462220": [{
                                        "subitem_1551256657859": "am",
                                        "subitem_1551256653656": "123"
                                    }],
                                    "subitem_1551256688098": [{
                                        "subitem_1551256694883": "ay",
                                        "subitem_1551256691232": "123"
                                    }]
                                }]
                            },
                            "item_1551265463411": {
                                "attribute_name": "Volume Number",
                                "attribute_value_mlt": [{
                                    "subitem_1551256328147": "123"
                                }]
                            },
                            "item_1551265520160": {
                                "attribute_name": "Issue Number",
                                "attribute_value_mlt": [{
                                    "subitem_1551256294723": "123"
                                }]
                            },
                            "item_title": "Test1",
                            "item_type_id": "75",
                            "control_number": "3",
                            "_oai": {
                                "id": "oai:invenio:recid/3"
                            },
                            "weko_shared_id": -1,
                            "owner": "1",
                            "custom_sort": {
                                "1561432655406": ""
                            },
                            "path": ["1561432655406"],
                            "publish_status": "1"
                        },
                        "pageStart": ["123"],
                        "file": {
                            "mimeType": ["NUT"],
                            "URI": [{
                                "objectType": "fulltext",
                                "value": "123"
                            }],
                            "version": ["123"],
                            "extent": ["123"],
                            "date": [{
                                "value": "2019-06-13",
                                "dateType": "Issued"
                            }]
                        },
                        "publish_status": "0",
                        "fundingReference": {
                            "awardTitle": ["123"],
                            "funderIdentifier": ["123"],
                            "funderName": ["123"],
                            "awardNumber": ["123"]
                        },
                        "weko_shared_id": -1,
                        "versionType": ["VoR"],
                        "custom_sort": {
                            "1561432655406": ""
                        },
                        "publisher": ["123"],
                        "_oai": {
                            "id": "oai:invenio:recid/3"
                        },
                        "relation_version_is_last": True
                    }
                }, {
                    "_index": "weko-jpcoar-v1.0.0",
                    "_type": "item",
                    "_id": "52283b6a-bc41-45a4-8ec2-c07c2e38e3e4",
                    "_score": 0.047463723,
                    "_source": {
                        "weko_creator_id": "1",
                        "identifierRegistration": [{
                            "identifierType": "DataCite",
                            "value": "123"
                        }],
                        "pageEnd": ["123"],
                        "volume": ["123"],
                        "publisher": ["123"],
                        "version": ["123"],
                        "numPages": ["123"],
                        "relation": {
                            "relatedTitle": ["123"],
                            "relatedIdentifier": [{
                                "identifierType": "NAID",
                                "value": "123"
                            }]
                        },
                        "title": ["Test1"],
                        "control_number": "5",
                        "apc": ["Not required"],
                        "accessRights": ["embargoed access"],
                        "temporal": ["123"],
                        "language": ["arm"],
                        "identifier": [{
                            "identifierType": "HDL",
                            "value": "123"
                        }],
                        "degreeGrantor": {
                            "nameIdentifier": ["123"],
                            "degreeGrantorName": ["123"]
                        },
                        "sourceIdentifier": [{
                            "identifierType": "NCID",
                            "value": "123"
                        }],
                        "_created": "2019-06-25T07:43:04.342245+00:00",
                        "date": [{
                            "value": "2019-06-19",
                            "dateType": "Submitted"
                        }],
                        "_updated": "2019-06-25T07:43:04.535207+00:00",
                        "publish_date": "2019-06-25",
                        "rights": ["123"],
                        "contributor": {
                            "contributorName": ["123"],
                            "nameIdentifier": ["123"],
                            "affiliation": {
                                "nameIdentifier": ["123"],
                                "affiliationName": ["123"]
                            },
                            "contributorAlternative": ["123"],
                            "familyName": ["123"],
                            "givenName": ["123"]
                        },
                        "creator": {
                            "nameIdentifier": ["123"],
                            "creatorName": ["Zan"],
                            "creatorAlternative": ["123"],
                            "givenName": ["123"],
                            "familyName": ["123"],
                            "affiliation": {
                                "nameIdentifier": ["123"],
                                "affiliationName": ["123"]
                            }
                        },
                        "geoLocation": {
                            "geoLocationPoint": {
                                "pointLongitude": ["123"],
                                "pointLatitude": ["123"]
                            },
                            "geoLocationPlace": ["123"],
                            "geoLocationBox": {
                                "eastBoundLongitude": ["123"],
                                "northBoundLatitude": ["123"],
                                "southBoundLatitude": ["123"],
                                "westBoundLongitude": ["123"]
                            }
                        },
                        "type": ["departmental bulletin paper"],
                        "sourceTitle": ["123"],
                        "issue": ["123"],
                        "dissertationNumber": ["123"],
                        "rightsHolder": {
                            "nameIdentifier": ["123"],
                            "rightsHolderName": ["123"]
                        },
                        "path": ["1561432655406"],
                        "itemtype": "Multiple",
                        "alternative": ["Test2"],
                        "description": ["123"],
                        "degreeName": ["123"],
                        "conference": {
                            "conferenceCountry": ["asm"],
                            "conferenceName": ["123"],
                            "conferenceSequence": ["123"],
                            "conferencePlace": ["123"]
                        },
                        "dateGranted": ["2019-06-20"],
                        "subject": [{
                            "subjectScheme": "MeSH",
                            "value": "123"
                        }],
                        "_item_metadata": {
                            "item_1551264822581": {
                                "attribute_name": "Subject",
                                "attribute_value_mlt": [{
                                    "subitem_1551257343002": "123",
                                    "subitem_1551257323812": "ak",
                                    "subitem_1551257315453": "123",
                                    "subitem_1551257329877": "MeSH"
                                }]
                            },
                            "item_1551265569218": {
                                "attribute_name": "Page Start",
                                "attribute_value_mlt": [{
                                    "subitem_1551256198917": "123"
                                }]
                            },
                            "item_1551264767789": {
                                "attribute_name": "Rights Holder",
                                "attribute_value_mlt": [{
                                    "subitem_1551257249371": [{
                                        "subitem_1551257257683": "sq",
                                        "subitem_1551257255641": "123"
                                    }],
                                    "subitem_1551257138324": "123",
                                    "subitem_1551257143244": [{
                                        "subitem_1551257145912": "123",
                                        "subitem_1551257232980": "123",
                                        "subitem_1551257156244": "NRID"
                                    }]
                                }]
                            },
                            "item_1551265326081": {
                                "attribute_name": "Geo Location",
                                "attribute_value_mlt": [{
                                    "subitem_1551256775293": "123123123",
                                    "subitem_1551256842196": "123",
                                    "subitem_1551256822219": [{
                                        "subitem_1551256824945": "123",
                                        "subitem_1551256834732": "123",
                                        "subitem_1551256840435": "123",
                                        "subitem_1551256831892": "123"
                                    }],
                                    "subitem_1551256778926": [{
                                        "subitem_1551256783928": "123",
                                        "subitem_1551256814806": "123"
                                    }]
                                }]
                            },
                            "item_1551264418667": {
                                "attribute_name": "Contributor",
                                "attribute_value_mlt": [{
                                    "subitem_1551257272214": [{
                                        "subitem_1551257316910": "as",
                                        "subitem_1551257314588": "123"
                                    }],
                                    "subitem_1551257372442": [{
                                        "subitem_1551257375939": "as",
                                        "subitem_1551257374288": "123"
                                    }],
                                    "subitem_1551257339190": [{
                                        "subitem_1551257343979": "aa",
                                        "subitem_1551257342360": "123"
                                    }],
                                    "subitem_1551257036415": "Distributor",
                                    "subitem_1551257245638": [{
                                        "subitem_1551257279831": "aa",
                                        "subitem_1551257276108": "123"
                                    }],
                                    "subitem_1551257150927": [{
                                        "subitem_1551257172531": "ORCID",
                                        "subitem_1551257152742": "123",
                                        "subitem_1551257228080": "123"
                                    }],
                                    "subitem_1551257419251": [{
                                        "subitem_1551257421633": [{
                                            "subitem_1551261493409": "123",
                                            "subitem_1551261485670": "ISNI",
                                            "subitem_1551261472867": "123"
                                        }],
                                        "subitem_1551261534334": [{
                                            "subitem_1551261546333": "ab",
                                            "subitem_1551261542403": "123"
                                        }]
                                    }]
                                }]
                            },
                            "item_1551264629907": {
                                "attribute_name": "Rights",
                                "attribute_value_mlt": [{
                                    "subitem_1551257025236": [{
                                        "subitem_1551257043769": "123",
                                        "subitem_1551257047388": "sq"
                                    }],
                                    "subitem_1551257030435": "123"
                                }]
                            },
                            "item_1551266003379": {
                                "attribute_name": "File",
                                "attribute_value_mlt": [{
                                    "subitem_1551255558587": [{
                                        "subitem_1551255581435": "fulltext",
                                        "subitem_1551255570271": "123",
                                        "subitem_1551255628842": "123"
                                    }],
                                    "subitem_1551255750794": "NUT",
                                    "subitem_1551255854908": "123",
                                    "subitem_1551255820788": [{
                                        "subitem_1551255828320": "2019-06-13",
                                        "subitem_1551255833133": "Issued"
                                    }],
                                    "subitem_1551255788530": "123"
                                }]
                            },
                            "item_1551265553273": {
                                "attribute_name": "Number of Pages",
                                "attribute_value_mlt": [{
                                    "subitem_1551256248092": "123"
                                }]
                            },
                            "item_1551265973055": {
                                "attribute_name": "Conference",
                                "attribute_value_mlt": [{
                                    "subitem_1551255947515": [{
                                        "subitem_1551255951127": "123",
                                        "subitem_1551255953139": "ar"
                                    }],
                                    "subitem_1551255911301": [{
                                        "subitem_1551255924068": "ak",
                                        "subitem_1551255919792": "123"
                                    }],
                                    "subitem_1551255945595": "123",
                                    "subitem_1551255973390": "asm"
                                }]
                            },
                            "item_1551265147138": {
                                "attribute_name": "Identifier",
                                "attribute_value_mlt": [{
                                    "subitem_1551256116088": "123",
                                    "subitem_1551256122128": "HDL"
                                }]
                            },
                            "item_1551265178780": {
                                "attribute_name": "Identifier Registration",
                                "attribute_value_mlt": [{
                                    "subitem_1551256259586": "DataCite",
                                    "subitem_1551256250276": "123"
                                }]
                            },
                            "item_1551265738931": {
                                "attribute_name": "Dissertation Number",
                                "attribute_value_mlt": [{
                                    "subitem_1551256171004": "123"
                                }]
                            },
                            "item_1551264917614": {
                                "attribute_name": "Publisher",
                                "attribute_value_mlt": [{
                                    "subitem_1551255702686": "123",
                                    "subitem_1551255710277": "sq"
                                }]
                            },
                            "item_1551264846237": {
                                "attribute_name": "Description",
                                "attribute_value_mlt": [{
                                    "subitem_1551255577890": "123",
                                    "subitem_1551255592625": "af",
                                    "subitem_1551255637472": "TableOfContents"
                                }]
                            },
                            "item_1551265409089": {
                                "attribute_name": "Source Identifier",
                                "attribute_value_mlt": [{
                                    "subitem_1551256405981": "123",
                                    "subitem_1551256409644": "NCID"
                                }]
                            },
                            "item_1551265603279": {
                                "attribute_name": "Page End",
                                "attribute_value_mlt": [{
                                    "subitem_1551256185532": "123"
                                }]
                            },
                            "item_1551265118680": {
                                "attribute_name": "Version Type",
                                "attribute_value_mlt": [{
                                    "subitem_1551256025676": "VoR"
                                }]
                            },
                            "item_1551264447183": {
                                "attribute_name": "Access Rights",
                                "attribute_value_mlt": [{
                                    "subitem_1551257578398": "123",
                                    "subitem_1551257553743": "embargoed access"
                                }]
                            },
                            "item_1551264974654": {
                                "attribute_name": "Date",
                                "attribute_value_mlt": [{
                                    "subitem_1551255753471": "2019-06-19",
                                    "subitem_1551255775519": "Submitted"
                                }]
                            },
                            "item_1551265438256": {
                                "attribute_name": "Source Title",
                                "attribute_value_mlt": [{
                                    "subitem_1551256349044": "123",
                                    "subitem_1551256350188": "ab"
                                }]
                            },
                            "pubdate": {
                                "attribute_name": "公開日",
                                "attribute_value": "2019-06-25"
                            },
                            "item_1551264605515": {
                                "attribute_name": "APC",
                                "attribute_value_mlt": [{
                                    "subitem_1551257776901": "Not required"
                                }]
                            },
                            "item_1551265032053": {
                                "attribute_name": "Resource Type",
                                "attribute_value_mlt": [{
                                    "subitem_1551255877772": "departmental bulletin paper",
                                    "subitem_1551255930377": "123"
                                }]
                            },
                            "item_1551265790591": {
                                "attribute_name": "Degree Name",
                                "attribute_value_mlt": [{
                                    "subitem_1551256126428": "123",
                                    "subitem_1551256129013": "av"
                                }]
                            },
                            "item_1551264326373": {
                                "attribute_name": "Alternative Title",
                                "attribute_value_mlt": [{
                                    "subitem_1551255721061": "ab",
                                    "subitem_1551255720400": "Test2"
                                }]
                            },
                            "item_1551264308487": {
                                "attribute_name": "Title",
                                "attribute_value_mlt": [{
                                    "subitem_1551255647225": "Test1",
                                    "subitem_1551255648112": "en"
                                }]
                            },
                            "item_1551265302120": {
                                "attribute_name": "Temporal",
                                "attribute_value_mlt": [{
                                    "subitem_1551256918211": "123",
                                    "subitem_1551256920086": "ak"
                                }]
                            },
                            "item_1551264340087": {
                                "attribute_name": "Creator",
                                "attribute_value_mlt": [{
                                    "subitem_1551255929209": [{
                                        "subitem_1551255964991": "en",
                                        "subitem_1551255938498": "123"
                                    }],
                                    "subitem_1551256025394": [{
                                        "subitem_1551256055588": "av",
                                        "subitem_1551256035730": "123"
                                    }],
                                    "subitem_1551255991424": [{
                                        "subitem_1551256007414": "aa",
                                        "subitem_1551256006332": "123"
                                    }],
                                    "subitem_1551255898956": [{
                                        "subitem_1551255907416": "vi",
                                        "subitem_1551255905565": "Zan"
                                    }],
                                    "subitem_1551256087090": [{
                                        "subitem_1551256089084": [{
                                            "subitem_1551256145018": "NRID",
                                            "subitem_1551256097891": "123",
                                            "subitem_1551256147368": "123"
                                        }],
                                        "subitem_1551256229037": [{
                                            "subitem_1551256259183": "123",
                                            "subitem_1551256259899": "an"
                                        }]
                                    }],
                                    "subitem_1551255789000": [{
                                        "subitem_1551255795486": "123",
                                        "subitem_1551255793478": "123",
                                        "subitem_1551255794292": "e-Rad"
                                    }]
                                }]
                            },
                            "item_1551265002099": {
                                "attribute_name": "Language",
                                "attribute_value_mlt": [{
                                    "subitem_1551255818386": "arm"
                                }]
                            },
                            "item_1551265075370": {
                                "attribute_name": "Version",
                                "attribute_value_mlt": [{
                                    "subitem_1551255975405": "123"
                                }]
                            },
                            "item_1551265903092": {
                                "attribute_name": "Degree Grantor",
                                "attribute_value_mlt": [{
                                    "subitem_1551256037922": [{
                                        "subitem_1551256047619": "av",
                                        "subitem_1551256042287": "123"
                                    }],
                                    "subitem_1551256015892": [{
                                        "subitem_1551256027296": "123",
                                        "subitem_1551256029891": "123"
                                    }]
                                }]
                            },
                            "item_1551265811989": {
                                "attribute_name": "Date Granted",
                                "attribute_value_mlt": [{
                                    "subitem_1551256096004": "2019-06-20"
                                }]
                            },
                            "item_1551265463411": {
                                "attribute_name": "Volume Number",
                                "attribute_value_mlt": [{
                                    "subitem_1551256328147": "123"
                                }]
                            },
                            "item_1551265227803": {
                                "attribute_name": "Relation",
                                "attribute_value_mlt": [{
                                    "subitem_1551256388439": "references",
                                    "subitem_1551256480278": [{
                                        "subitem_1551256513476": "af",
                                        "subitem_1551256498531": "123"
                                    }],
                                    "subitem_1551256387752": "123",
                                    "subitem_1551256465077": [{
                                        "subitem_1551256629524": "NAID",
                                        "subitem_1551256478339": "123"
                                    }]
                                }]
                            },
                            "item_1551265385290": {
                                "attribute_name": "Funding Reference",
                                "attribute_value_mlt": [{
                                    "subitem_1551256665850": [{
                                        "subitem_1551256671920": "123",
                                        "subitem_1551256679403": "123"
                                    }],
                                    "subitem_1551256454316": [{
                                        "subitem_1551256614960": "123",
                                        "subitem_1551256619706": "GRID"
                                    }],
                                    "subitem_1551256462220": [{
                                        "subitem_1551256657859": "am",
                                        "subitem_1551256653656": "123"
                                    }],
                                    "subitem_1551256688098": [{
                                        "subitem_1551256694883": "ay",
                                        "subitem_1551256691232": "123"
                                    }]
                                }]
                            },
                            "item_1551265520160": {
                                "attribute_name": "Issue Number",
                                "attribute_value_mlt": [{
                                    "subitem_1551256294723": "123"
                                }]
                            },
                            "item_title": "Test2",
                            "item_type_id": "75",
                            "control_number": "5",
                            "_oai": {
                                "id": "oai:invenio:recid/5"
                            },
                            "weko_shared_id": -1,
                            "owner": "1",
                            "custom_sort": {
                                "1561432655406": ""
                            },
                            "path": ["1561432655406"],
                            "publish_status": "0"
                        },
                        "pageStart": ["123"],
                        "file": {
                            "mimeType": ["NUT"],
                            "URI": [{
                                "objectType": "fulltext",
                                "value": "123"
                            }],
                            "version": ["123"],
                            "extent": ["123"],
                            "date": [{
                                "value": "2019-06-13",
                                "dateType": "Issued"
                            }]
                        },
                        "publish_status": "0",
                        "fundingReference": {
                            "awardTitle": ["123"],
                            "funderIdentifier": ["123"],
                            "funderName": ["123"],
                            "awardNumber": ["123"]
                        },
                        "weko_shared_id": -1,
                        "versionType": ["VoR"],
                        "custom_sort": {
                            "1561432655406": ""
                        },
                        "_oai": {
                            "id": "oai:invenio:recid/5"
                        }
                    }
                }]
            }
        }

        if not data or not data.get('hits'):
            return None
        hits = data.get('hits')
        rss_data = hits.get('hits')
        return build_rss_xml(rss_data)
