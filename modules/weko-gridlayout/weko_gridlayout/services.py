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
import pickle
import json
from datetime import date, datetime, timedelta
from operator import itemgetter

from flask import Markup, current_app, session
from flask_babelex import gettext as _
from flask_login import current_user
from invenio_communities.models import Community
from invenio_db import db
from invenio_i18n.ext import current_i18n
from invenio_stats.utils import QueryRankingHelper
from sqlalchemy.orm.exc import NoResultFound
from weko_admin.config import WEKO_ADMIN_DEFAULT_LIFETIME
from weko_index_tree.api import Indexes

from .config import WEKO_GRIDLAYOUT_ACCESS_COUNTER_TYPE, \
    WEKO_GRIDLAYOUT_DEFAULT_LANGUAGE_CODE, \
    WEKO_GRIDLAYOUT_DEFAULT_WIDGET_LABEL, WEKO_GRIDLAYOUT_MENU_WIDGET_TYPE, \
    WEKO_GRIDLAYOUT_WIDGET_ITEM_LOCK_KEY
from .models import WidgetDesignPage, WidgetDesignPageMultiLangData, \
    WidgetDesignSetting, WidgetItem, WidgetMultiLangData
from .utils import build_data, build_multi_lang_data, build_rss_xml, \
    convert_data_to_design_pack, convert_data_to_edit_pack, \
    convert_widget_data_to_dict, delete_widget_cache, \
    get_elasticsearch_result_by_date, update_general_item, \
    validate_main_widget_insertion


class WidgetItemServices:
    """Services for Widget item setting."""

    @classmethod
    def get_widget_by_id(cls, widget_id):
        """Get widget by identifier.

        Arguments:
            widget_id {int} -- id of widget item

        """
        return WidgetItem.get_by_id(widget_id)

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
        if not data or not data.get('data'):
            result['message'] = 'No data saved!'
            return result
        widget_data = data.get('data')

        if data.get('flag_edit'):
            # Update Widget.
            result = cls.__edit_widget(data)
        else:
            # Create Widget.
            respond = cls.create(build_data(widget_data))
            if respond['error']:
                result['message'] = respond['error']
            else:
                result['message'] = 'Widget item saved successfully.'
                result['success'] = True
        return result

    @classmethod
    def __edit_widget(cls, data, ):
        widget_data = data.get('data')
        services = WidgetDesignServices
        is_used_in_widget_design = services.is_used_in_widget_design(
            data.get('data_id'))

        result = cls.__validate(data, is_used_in_widget_design)

        if result['success']:
            respond = cls.update_by_id(
                data.get('data_id'),
                build_data(widget_data))
            if respond['error']:
                result['message'] = respond['error']
            # Update widget design using the widget data.
            if is_used_in_widget_design:
                services.handle_change_item_in_preview_widget_item(
                    data.get('data_id'), widget_data)
            result['message'] = 'Widget item updated successfully.'
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
        multi_lang_data = pickle.loads(pickle.dumps(widget_data.get('multiLangSetting'), -1))
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

        multi_lang_data = pickle.loads(pickle.dumps(widget_data.get('multiLangSetting'), -1))
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

        if WidgetDesignServices.is_used_in_widget_design(widget_id):
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

    @classmethod
    def get_locked_widget_info(cls, widget_id, widget_item=None,
                               locked_value=None):
        """Get locked widget info.

        @param widget_id: widget identifier.
        @param widget_item:Widget Item
        @param locked_value:locked value
        @return:
        """
        if widget_item is None:
            widget_item = cls.get_widget_by_id(widget_id)
        if widget_item.locked:
            session_timeout = WEKO_ADMIN_DEFAULT_LIFETIME
            if widget_item.updated + timedelta(
                    minutes=session_timeout) < datetime.utcnow():
                return None
            if int(widget_item.locked_by_user) != int(current_user.get_id()):
                return widget_item
            else:
                lock_key = WEKO_GRIDLAYOUT_WIDGET_ITEM_LOCK_KEY.format(
                    widget_id)
                if locked_value and session.get(lock_key) != locked_value:
                    return widget_item
                elif session.get(lock_key) and not locked_value:
                    return session[lock_key]

        return None

    @classmethod
    def lock_widget(cls, widget_id, locked_value):
        """Lock widget.

        @param widget_id: widget identifier.
        @param locked_value:
        """
        lock_key = WEKO_GRIDLAYOUT_WIDGET_ITEM_LOCK_KEY.format(widget_id)
        session[lock_key] = locked_value
        locked_data = {
            "locked": True,
            "locked_by_user": int(current_user.get_id())
        }
        WidgetItem.update_by_id(widget_id, locked_data)

    @classmethod
    def unlock_widget(cls, widget_id):
        """Unlock widget.

        @param widget_id:
        """
        lock_key = WEKO_GRIDLAYOUT_WIDGET_ITEM_LOCK_KEY.format(widget_id)
        if lock_key in session:
            del session[lock_key]
        unlocked_data = {
            "locked": False,
            "locked_by_user": None
        }
        return WidgetItem.update_by_id(widget_id, unlocked_data)

    @classmethod
    def __validate(cls, data, is_used_in_widget_design=False):
        """Validate edit widget.

        @param data: Widget data.
        @param is_used_in_widget_design: Is used in widget design.
        @return:
        """
        result = {
            'message': '',
            'success': False
        }
        widget_data = data.get('data')
        old_widget_data = cls.get_widget_by_id(data.get('data_id'))
        # Check the widget is used in widget design.
        if (str(old_widget_data.repository_id) != str(
                widget_data.get('repository'))
                and is_used_in_widget_design):
            result['message'] = _("Cannot update repository "
                                  "of this widget because "
                                  "it's setting in Widget Design.")
        elif cls.get_locked_widget_info(data.get('data_id'), old_widget_data,
                                        data.get('locked_value')):
            result['message'] = _("Widget is locked by another user.")

        if not result['message']:
            result['success'] = True
        return result


class WidgetDesignServices:
    """Services for Widget item setting."""

    @classmethod
    def get_repository_list(cls):
        """Get repository list from Community table.

        :return: Repository list.
        """
        result = {
            "repositories": [],
            "error": ""
        }
        is_super = set(role.name for role in current_user.roles) & \
            set(current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER'])
        try:
            with db.session.no_autoflush:
                if is_super:
                    communities = Community.query.all()
                    result['repositories'].append({"id": "Root Index", "title": ""})
                else:
                    communities = Community.get_repositories_by_user(current_user)
            if communities:
                for community in communities:
                    community_result = dict()
                    community_result['id'] = community.id
                    community_result['title'] = community.title
                    result['repositories'].append(community_result)
        except Exception as e:
            current_app.logger.error(f"Error getting repository list: {e}")
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
        :param model: WidgetDesignSetting model
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
                    settings = json.loads(settings) \
                        if isinstance(settings, str) else settings
                    for item in settings:
                        widget_preview = dict()
                        widget_preview["widget_id"] = item.get("widget_id")
                        widget_preview["x"] = item.get("x")
                        widget_preview["y"] = item.get("y")
                        widget_preview["width"] = item.get("width")
                        widget_preview["height"] = item.get("height")
                        widget_preview["id"] = item.get("id")
                        widget_preview["type"] = item.get("type")
                        widget_preview["name"] = item.get("name")
                        if item.get('type') == \
                                WEKO_GRIDLAYOUT_ACCESS_COUNTER_TYPE \
                                and item.get('created_date'):
                            widget_preview["created_date"] = \
                                item.get("created_date")
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
            settings = json.loads(settings) \
                if isinstance(settings, str) else settings
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
            json_data = json.loads(setting_data) \
                if isinstance(setting_data, str) else setting_data
            if isinstance(json_data, list):
                for item in json_data:
                    widget_item = \
                        WidgetItemServices.get_widget_data_by_widget_id(
                            item.get('widget_id'))
                    item.update(widget_item.get('settings'))
                    if item.get('type') == WEKO_GRIDLAYOUT_ACCESS_COUNTER_TYPE:
                        today = date.today().strftime("%Y-%m-%d")
                        item['created_date'] = today
                        if not item.get('count_start_date'):
                            item['count_start_date'] = item['created_date'] if item.get('created_date') else today
            setting_data = json.dumps(json_data)

            # Main contents can only be in one page design or main design
            valid = validate_main_widget_insertion(
                repository_id, json_data, page_id=page_id)

            if page_id and repository_id and setting_data and valid:  # Page
                # Delete the widget page design is cached
                delete_widget_cache("", page_id)
                result["result"] = WidgetDesignPage.update_settings(
                    page_id, setting_data)
            elif repository_id and setting_data and valid:  # Main design
                # Delete the widget design is cached
                delete_widget_cache(repository_id)
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
            widget_item = WidgetItemServices.get_widget_by_id(widget_id)
            repo_id = widget_item.repository_id
            data = [WidgetDesignSetting.select_by_repository_id(repo_id)]

            # Must update all pages as well as main layout
            data += [{'repository_id': page.repository_id,
                      'settings': page.settings,
                      'page_id': page.id}
                     for page in WidgetDesignPage.get_by_repository_id(repo_id)
                     ]

            success = True
            for model in data:  # FIXME: May be confusing to update both here
                if model.get('settings'):
                    json_data = json.loads(model.get('settings')) if isinstance(
                        model.get('settings'), str) else model.get('settings')
                    update_data = cls.update_item_in_preview_widget_item(
                        widget_id, data_result, json_data)
                    if model.get('page_id'):  # Update page
                        if not WidgetDesignPage.update_settings(
                                model.get('page_id', 0), update_data):
                            success = False
                        else:
                            # Delete the widget page design is cached
                            delete_widget_cache("", model.get('page_id'))
                    else:  # Update main layout
                        if not WidgetDesignSetting.update(
                                repo_id, update_data):
                            success = False
                        else:
                            # Delete the widget design is cached
                            delete_widget_cache(repo_id)
            return success
        except Exception as e:
            current_app.logger.error(e)
            return False

    @classmethod
    def is_used_in_widget_design(cls, widget_id):
        """Validate widget item.

        :param: widget id
        :return: true if widget item is used in widget design else return false
        """
        try:
            if not widget_id:
                return False
            widget_item = WidgetItemServices.get_widget_by_id(widget_id)
            repo_id = widget_item.repository_id
            data = [WidgetDesignSetting.select_by_repository_id(repo_id)]

            # Must check all pages too
            data += [{'repository_id': page.repository_id,
                      'settings': page.settings}
                     for page in
                     WidgetDesignPage.get_by_repository_id(repo_id)]

            for model in data:
                if model.get('settings'):
                    json_data = json.loads(model.get('settings')) \
                        if isinstance(model.get('settings'), str) \
                        else model.get('settings')
                    for item in json_data:
                        if str(item.get('widget_id')) == str(widget_id):
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

        :param data: Widget design page data.
        :return: formatted data of WidgetDesignPage.
        """
        result = {
            'result': True,
            'error': ''
        }
        is_edit = data.get('is_edit', False)
        if is_edit:
            page_id = data.get('page_id', 0)
        else:
            page_id = 0
        repository_id = data.get('repository_id', 0)
        title = data.get('title')
        url = data.get('url')
        content = data.get('content')
        settings = data.get('settings')
        multi_lang_data = data.get('multi_lang_data')
        is_main_layout = data.get('is_main_layout')
        try:
            WidgetDesignPage.create_or_update(
                repository_id, Markup.escape(title), url,
                Markup.escape(content), page_id=page_id,
                settings=settings, multi_lang_data=multi_lang_data,
                is_main_layout=is_main_layout
            )

            # Update Main Layout Id for widget design setting and widget item
            if is_main_layout and is_edit:
                cls._update_main_layout_id_for_widget(repository_id)

        except ValueError as ex:
            result['result'] = False
            result['error'] = 'Unable to save page: {}'.format(str(ex))
        except Exception as ex:
            current_app.logger.error(ex)
            result['result'] = False
            result['error'] = _('Unable to save page: Unexpected error.')
        return result

    @classmethod
    def _update_main_layout_id_for_widget(cls, repository_id):
        with db.session.no_autoflush:
            design_page = WidgetDesignPage.query.filter_by(
                repository_id=repository_id,
                is_main_layout=True).one_or_none()
            page_id = None
            if design_page:
                page_id = design_page.id

            if page_id:
                cls._update_main_layout_page_id_for_widget_design(
                    repository_id,
                    page_id
                )
                cls.__update_main_layout_page_id_for_widget_item(
                    repository_id,
                    page_id
                )

    @classmethod
    def _update_main_layout_page_id_for_widget_design(
        cls, repository_id, page_id
    ):
        with db.session.no_autoflush:
            widget_design = WidgetDesignSetting.select_by_repository_id(
                repository_id)
            if widget_design:
                settings = json.loads(widget_design.get('settings', '[]')) \
                    if isinstance(widget_design.get('settings', '[]'), str) \
                    else widget_design.get('settings')
                if settings:
                    settings = cls._update_page_id_for_widget_design_setting(
                        settings,
                        page_id)
                    WidgetDesignSetting.update(repository_id,
                                               json.dumps(settings))

    @classmethod
    def _update_page_id_for_widget_design_setting(cls, settings, page_id):
        default_page_id = "0"
        new_settings = list()
        for item in settings:
            if item.get('type') == WEKO_GRIDLAYOUT_MENU_WIDGET_TYPE:
                menu_show_pages = item.get('menu_show_pages')
                if menu_show_pages and default_page_id in menu_show_pages:
                    new_menu_show_pages = [
                        page_id if x == default_page_id else x for x in
                        menu_show_pages]
                    item['menu_show_pages'] = new_menu_show_pages
            new_settings.append(item)

        return new_settings

    @classmethod
    def __update_main_layout_page_id_for_widget_item(cls, repository_id,
                                                     page_id):
        widget_item_id_list = WidgetItem.get_id_by_repository_and_type(
            repository_id, WEKO_GRIDLAYOUT_MENU_WIDGET_TYPE)
        if widget_item_id_list:
            for widget_id in widget_item_id_list:
                widget_item = WidgetItem.get_by_id(widget_id)
                if widget_item.settings:
                    cls._update_page_id_for_widget_item_setting(
                        page_id, widget_item)

    @classmethod
    def _update_page_id_for_widget_item_setting(cls, page_id,
                                                widget_item):
        settings = json.loads(widget_item.settings) \
            if isinstance(widget_item.settings, str) else widget_item.settings
        default_page_id = "0"
        if settings and settings.get('menu_show_pages'):
            menu_show_pages = settings.get('menu_show_pages')
            if default_page_id in menu_show_pages:
                new_menu_show_pages = [
                    page_id if x == default_page_id else x for x in
                    menu_show_pages
                ]
                settings['menu_show_pages'] = new_menu_show_pages
                widget_item.settings = settings
                WidgetItem.update_setting_by_id(
                    widget_item.widget_id, json.dumps(settings))

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
            delete_result = WidgetDesignPageMultiLangData.delete_by_page_id(
                page_id)
            if delete_result:
                result['result'] = WidgetDesignPage.delete(page_id)
        except Exception as e:
            current_app.logger.error(e)
            result['error'] = _('Unable to delete page.')
        return result

    @classmethod
    # TODO: Return the selected language title here!
    def get_page_list(cls, repository_id, language):
        """Get WidgetDesignPage list.

        :param repository_id: Identifier of the repository.
        :param language: The default language.
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
                    'is_main_layout': page.is_main_layout,
                })

        except Exception as e:
            current_app.logger.error(e)
            result['error'] = _('Unable to retrieve page list.')
        return result

    @classmethod
    def get_page(cls, page_id, repository_id):   # TODO: Localization ?
        """Get WidgetDesignPage list.

        :param page_id: Identifier of the page design.
        :param repository_id: Identifier of the repository.
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
                'is_main_layout': page.is_main_layout
            }

        except NoResultFound:
            if str(page_id) == '0':
                url = '/'
                if repository_id != current_app.config[
                        'WEKO_THEME_DEFAULT_COMMUNITY']:
                    url += '?c=' + repository_id
                result['data'] = {
                    'id': page_id,
                    'title': 'Main Layout',
                    'url': url,
                    'content': '',
                    'repository_id': repository_id,
                    'multi_lang_data': {},
                    'is_main_layout': True
                }
            else:
                result['error'] = _('Unable to retrieve page: Page not found.')
        except Exception as e:
            current_app.logger.error(e)
            result['error'] = _('Unable to retrieve page: Unexpected error.')
        return result


class WidgetDataLoaderServices:
    """Services for load data to page."""
    @classmethod
    def _get_index_info(cls, index_json, index_info):
        for index in index_json:
            index_info[index["id"]] = {
                'index_name': index["name"],
                'parent': str(index["pid"])
            }
            if index["children"]:
                cls._get_index_info(index["children"], index_info)

    @classmethod
    def get_new_arrivals_data(cls, widget_id):
        """Get new arrivals data from DB.

        Returns:
            dictionary -- new arrivals data

        """
        from weko_items_ui.utils import get_permission_record


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
            res = QueryRankingHelper.get_new_items(
                start_date=start_date,
                end_date=end_date,
                agg_size=int(number_result) + 100,
                must_not=json.dumps([{"wildcard": {"control_number": "*.*"}}])
            )
            if not res:
                res['error'] = 'Cannot search data'
                return res

            index_json = Indexes.get_browsing_tree_ignore_more()
            index_info = {}
            cls._get_index_info(index_json, index_info)
            has_permission_indexes = list(index_info.keys())
            data = get_permission_record('new_items', res, int(number_result), has_permission_indexes)

            for d in data:
                d['name'] = d['title']
            result['data'] = data
        except Exception as e:
            result['error'] = str(e)
        return result

    @classmethod
    def get_arrivals_rss(cls, data, term, count):
        """Get New Arrivals RSS.

        :dictionary: elastic search data

        """
        from weko_items_ui.utils import find_hidden_items
        lang = current_i18n.language
        if not data or not data.get('hits'):
            return build_rss_xml(data=None, term=term, count=0, lang=lang)
        hits = data.get('hits')
        es_data = [record for record in hits.get(
            'hits', []) if record.get('_source').get('path')]
        item_id_list = list(map(itemgetter('_id'), es_data))
        hidden_items = find_hidden_items(item_id_list)

        rss_data = []
        for es_item in es_data:
            if es_item['_id'] in hidden_items:
                continue
            rss_data.append(es_item)
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
                                {
                                    'url': page.url,
                                    'title': title,
                                    'is_main_layout': page.is_main_layout,
                                }
                            )
                        except NoResultFound:
                            pass
            except Exception as e:
                current_app.logger.error(e)
                result['endpoints'] = []
        return result
