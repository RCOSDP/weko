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
from datetime import date, timedelta

from flask import Markup, current_app
from flask_babelex import gettext as _
from invenio_db import db
from invenio_i18n.ext import current_i18n
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from .config import WEKO_GRIDLAYOUT_DEFAULT_LANGUAGE_CODE, \
    WEKO_GRIDLAYOUT_DEFAULT_WIDGET_LABEL
from .models import WidgetDesignPage, WidgetDesignSetting, WidgetItem, \
    WidgetMultiLangData
from .utils import build_data, build_multi_lang_data, build_rss_xml, \
    convert_data_to_design_pack, convert_data_to_edit_pack, \
    convert_widget_data_to_dict, convert_widget_multi_lang_to_dict, \
    get_elasticsearch_result_by_date, update_general_item, \
    validate_main_widget_insertion


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
            if (str(old_repo) != str(widget_data.get('repository'))
                and WidgetDesignServices.validate_admin_widget_item_setting(
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
                    if (dict_data.get('label') == label
                            and dict_data.get('lang_code') == lang_code):
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
        result = convert_data_to_design_pack(widget_data, multi_lang_data)
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
        converted_data = convert_data_to_design_pack(
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
            if isinstance(widget_item_list, list):
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
                    if (isinstance(languages, dict)
                            and lang_code_default is not None):
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

    # TODO: Change to allow specifying which model to retrieve from
    @classmethod
    def get_widget_preview(cls, repository_id, default_language,
                           model=WidgetDesignSetting):
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
            widget_setting = model.select_by_repository_id(
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
                        if isinstance(languages, dict) and lang_code_default \
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
        :param model: Detrmine whether we should get the data from
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
                result['widget-settings'] = cls._get_setting(settings,
                                                             current_language)
        except Exception as e:
            result['error'] = str(e)
        return result

    @classmethod
    def _get_setting(cls, settings, current_language):
        """Extract the design from model."""
        result_settings = []
        if settings:
            settings = json.loads(settings)
            for widget_item in settings:
                widget = cls._get_design_base_on_current_language(
                    current_language,
                    widget_item)
                result_settings.append(widget)
        return result_settings

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
            if (isinstance(languages, dict)
                    and languages.get(default_language_code)):
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
        page_id = data.get('page_id')  # Save design to page rather than layout
        setting_data = data.get('settings')
        try:
            json_data = json.loads(setting_data)
            if isinstance(json_data, list):
                for item in json_data:
                    widget_item = \
                        WidgetItemServices.get_widget_data_by_widget_id(
                            item.get('widget_id'))
                    item.update(widget_item.get('settings'))
            setting_data = json.dumps(json_data)

            # Main contents can only be in one page design or main design
            valid = validate_main_widget_insertion(
                repository_id, json_data, page_id=page_id)

            if page_id and repository_id and setting_data and valid:  # Page
                result["result"] = WidgetDesignPage.update_settings(
                    page_id, setting_data)
            elif repository_id and setting_data and valid:  # Main design
                if WidgetDesignSetting.select_by_repository_id(repository_id):
                    result["result"] = WidgetDesignSetting.update(
                        repository_id, setting_data)
                else:
                    result["result"] = WidgetDesignSetting.create(
                        repository_id, setting_data)
            else:
                if not valid:  # Tried to insert main contents into two places
                    result['error'] = _(
                        'Failed to save design:\n \
                        Main contents may only be set to one layout.'
                    )
                else:
                    result['error'] = _(
                        'Failed to save design:\n Check input values.')
        except Exception as e:
            current_app.logger.info(e)
            result['error'] = _('Failed to save design: Unexpected error.')
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
        if isinstance(json_data, list):
            for item in json_data:
                if str(item.get('widget_id')) == str(widget_id):
                    update_general_item(item, data_result)
        data = json.dumps(json_data)
        return data

    @classmethod
    def handle_change_item_in_preview_widget_item(cls, widget_id, data_result):
        """Handle change when edit widget item effect to widget design and page.

        Arguments:
            data_id {widget_item} -- [id of widget item]
            data_result {widget_item} -- [data is sent by client]

        Returns:
            [False] -- [handle failed]
            [True] -- [handle success]

        """
        try:
            repo_id = WidgetItemServices.get_repo_by_id(widget_id)
            data = [WidgetDesignSetting.select_by_repository_id(repo_id)]

            # Must update all pages as well as main layout
            data += [{'repository_id': page.repository_id,
                      'settings': page.settings,
                      'page_id': page.id}
                     for page in WidgetDesignPage.get_by_repository_id(repo_id)]

            success = True
            for model in data:  # FIXME: May be confusing to update both here
                if model.get('settings'):
                    json_data = json.loads(model.get('settings'))
                    update_data = cls.update_item_in_preview_widget_item(
                        widget_id, data_result, json_data)
                    if model.get('page_id'):  # Update page
                        if not WidgetDesignPage.update_settings(
                                model.get('page_id', 0), update_data):
                            success = False
                    else:  # Update main layout
                        if not WidgetDesignSetting.update(
                                repo_id, update_data):
                            success = False
            return success
        except Exception as e:
            current_app.logger.error(e)
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
                data = [WidgetDesignSetting.select_by_repository_id(repo_id)]

                # Must check all pages too
                data += [{'repository_id': page.repository_id,
                          'settings': page.settings}
                         for page in WidgetDesignPage.get_by_repository_id(repo_id)]

                for model in data:
                    if model.get('settings'):
                        json_data = json.loads(model.get('settings'))
                        for item in json_data:
                            if str(item.get('widget_id')) == \
                                    str(widget_item_id):
                                return True
            return False
        except Exception as e:
            current_app.logger.error('Failed to validate record: ', e)
            return True


class WidgetDesignPageServices:
    """Services for WidgetDesignPage."""

    @classmethod
    def get_widget_design_setting(cls, page_id: str, current_language: str):
        """Get Widget design setting by page id.

        :param page_id: Identifier of the repository.
        :param current_language: The default language.
        :return: Widget page design setting.
        """
        result = {
            'widget-settings': [],
            'error': ''
        }
        try:
            page = WidgetDesignPage.get_by_id(page_id)
            if page:
                result['widget-settings'] = \
                    WidgetDesignServices._get_setting(
                        page.settings, current_language)
        except NoResultFound:
            result['error'] = _('Unable to retrieve page: Page not found.')
        except Exception as e:
            current_app.logger.error(e)
            result['error'] = _('Unable to retrieve page: Unexpected error.')
        return result

    @classmethod
    def add_or_update_page(cls, data):
        """Add a WidgetDesignPage.

        :param repository_id: Identifier of the repository.
        :param default_language: The default language.
        :return: formatted data of WidgetDesignPage.
        """
        result = {
            'result': False,
            'error': ''
        }
        page_id = data.get('page_id', 0)
        repository_id = data.get('repository_id', 0)
        title = data.get('title')
        url = data.get('url')
        content = data.get('content')
        settings = data.get('settings')
        multi_lang_data = data.get('multi_lang_data')
        try:
            result['result'] = WidgetDesignPage.create_or_update(
                repository_id, Markup.escape(title), url, Markup.escape(content), page_id=page_id,
                settings=settings, multi_lang_data=multi_lang_data
            )
        except IntegrityError:
            result['error'] = _('Unable to save page: URL already exists.')
        except Exception as e:
            result['error'] = _('Unable to save page: Unexpected error.')
        return result

    @classmethod
    def delete_page(cls, page_id):
        """Delete a WidgetDesignPage.

        :param page_id: WidgetDesignPage identifier
        :return: True if successful, else False
        """
        result = {
            'result': False,
            'error': ''
        }
        try:
            result['result'] = WidgetDesignPage.delete(page_id)
        except Exception as e:
            result['error'] = _('Unable to delete page.')
        return result

    @classmethod
    # TODO: Return the selected language title here!
    def get_page_list(cls, repository_id, language):
        """Get WidgetDesignPage list.

        :param repository_id: Identifier of the repository.
        :param default_language: The default language.
        :return: formatted data of WidgetDesignPage.
        """
        result = {
            'data': [],
            'error': ''
        }
        try:
            pages = WidgetDesignPage.get_by_repository_id(repository_id)

            for page in pages:
                title = page.multi_lang_data[language].title if \
                    language and language in page.multi_lang_data else \
                    page.title
                result['data'].append({
                    'id': page.id,
                    'name': title,
                })

        except Exception as e:
            result['error'] = _('Unable to retrieve page list.')
        return result

    @classmethod
    def get_page(cls, page_id):   # TODO: Localization ?
        """Get WidgetDesignPage list.

        :param page_id: Identifier of the repository.
        :param default_language: The default language.
        :return: formatted data of WidgetDesignPage.
        """
        result = {
            'data': {},
            'error': ''
        }
        try:
            page = WidgetDesignPage.get_by_id(page_id)
            multi_lang_data = {
                lang: page.multi_lang_data[lang].title
                for lang in page.multi_lang_data
            }
            result['data'] = {
                'id': page.id,
                'title': page.title,
                'url': page.url,
                'content': page.content,
                'repository_id': page.repository_id,
                'multi_lang_data': multi_lang_data,
            }

        except NoResultFound:
            result['error'] = _('Unable to retrieve page: Page not found.')
        except Exception as e:
            current_app.logger.error(e)
            result['error'] = _('Unable to retrieve page: Unexpected error.')
        return result


class WidgetDataLoaderServices:
    """Services for load data to page."""

    @classmethod
    def get_new_arrivals_data(cls, widget_id):
        """Get new arrivals data from DB.

        Returns:
            dictionary -- new arrivals data

        """
        result = {
            'data': '',
            'error': ''
        }
        if not widget_id:
            result['error'] = 'Widget is not exist'
            return result
        try:
            data = list()
            widget = WidgetItemServices.get_widget_data_by_widget_id(widget_id)
            setting = widget.get('settings')
            if not setting:
                result['error'] = 'Widget is not exist'
                return result
            number_result = setting.get('display_result')
            new_date = setting.get('new_dates')

            if not number_result or not new_date:
                result['error'] = 'Widget is not exist'
                return result

            try:
                term = int(new_date)
            except Exception:
                term = 0
            current_date = date.today()
            end_date = current_date.strftime("%Y-%m-%d")
            start_date = (current_date - timedelta(days=term)).strftime(
                "%Y-%m-%d")
            rd = get_elasticsearch_result_by_date(start_date, end_date)
            hits = rd.get('hits')
            if not hits:
                result['error'] = 'Cannot search data'
                return result
            es_data = hits.get('hits')
            for es_item in es_data:
                if len(data) >= int(number_result):
                    break
                new_data = dict()
                source = es_item.get('_source')
                if not source:
                    continue
                item_metadata = source.get('_item_metadata')
                if not item_metadata:
                    continue
                new_data['name'] = item_metadata.get('item_title')
                new_data['url'] = '/records/' + item_metadata.get(
                    'control_number')
                data.append(new_data)
            result['data'] = data
        except Exception as e:
            result['error'] = str(e)
        return result

    @classmethod
    def get_arrivals_rss(cls, data, term, count):
        """Get New Arrivals RSS.

        :dictionary: elastic search data

        """
        lang = current_i18n.language
        if not data or not data.get('hits'):
            return build_rss_xml(data=None, term=term, count=0, lang=lang)
        hits = data.get('hits')
        rss_data = hits.get('hits')
        return build_rss_xml(data=rss_data, term=term, count=count, lang=lang)

    @classmethod
    def get_widget_page_endpoints(cls, widget_id, language):
        """Get endpoints for a particular menu widget."""
        result = {'endpoints': []}

        if widget_id:
            # current_app.config['WEKO_GRIDLAYOUT_MENU_WIDGET_TYPE']
            menu_type = 'Menu'
            try:
                widget = \
                    WidgetItemServices.get_widget_data_by_widget_id(widget_id)
                repository_id = widget.get('repository_id')
                show_pages_ids = widget['settings'].get('menu_show_pages')
                # Allow for pages with no settings to display
                if show_pages_ids and repository_id and \
                        widget.get('widget_type') == menu_type:
                    for page_id in show_pages_ids:
                        try:
                            page = WidgetDesignPage.get_by_id(page_id)
                            title = page.title  # Get title based on language
                            if language and language in page.multi_lang_data:
                                title = page.multi_lang_data[language].title
                            result['endpoints'].append(
                                {'url': page.url, 'title': title})
                        except NoResultFound:
                            pass
            except Exception as e:
                current_app.logger.error(e)
                result['endpoints'] = []
        return result


# Utlils or all of the fucntions
def get_design_setting(model):
    """Extract the widget design setting from the model."""
    widget_setting = model.settings
    if widget_setting:
        settings = widget_setting.get('settings')
        if settings:
            settings = json.loads(settings)
            for widget_item in settings:
                widget = cls._get_design_base_on_current_language(
                    current_language,
                    widget_item)
                result["widget-settings"].append(widget)
