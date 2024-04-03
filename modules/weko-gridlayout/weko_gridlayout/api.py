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

"""API for weko-admin."""
import orjson

from flask import current_app
from invenio_accounts.models import Role
from invenio_db import db
from sqlalchemy.exc import SQLAlchemyError

from .models import WidgetItem


class WidgetItems(object):
    """Define API for WidgetItems creation and update."""

    @classmethod
    def build_general_data(cls, data_object, widget_items, is_update=False):
        """Build general data of object.

        :param data_object: object data
        :param widget_items: widget item
        :param is_update: Update flag
        """
        try:
            data_object["repository_id"] = widget_items.get('repository')
            data_object["widget_type"] = widget_items.get('widget_type')
            role = widget_items.get('browsing_role')
            if type(role) is list:
                data_object["browsing_role"] = ",".join(str(e) for e in role)
            else:
                data_object["browsing_role"] = role
            role = widget_items.get('edit_role')
            if type(role) is list:
                data_object["edit_role"] = ",".join(str(e) for e in role)
            else:
                data_object["edit_role"] = role
            data_object["is_enabled"] = widget_items.get('enable')
        except Exception as ex:
            current_app.logger.debug(ex)

    @classmethod
    def build_settings_data(cls, widget_object, widget_items):
        """Build setting data.

        :param widget_object: Widget data object.
        :param widget_items: Widget item setting.
        """
        data_object_settings = dict()
        data_object_settings["label_color"] = widget_items.get(
            'label_color')
        data_object_settings["has_frame_border"] = widget_items.get(
            'frame_border')
        data_object_settings["frame_border_color"] = widget_items.get(
            'frame_border_color')
        data_object_settings["text_color"] = widget_items.get('text_color')
        data_object_settings["background_color"] = widget_items.get(
            'background_color')
        widget_object['settings'] = orjson.dumps(data_object_settings).decode()

    @classmethod
    def build_object(cls, widget_items=None, is_update=False):
        """Build widget item object.

        :param widget_items: Widget Item
        :param is_update: Update flag
        :return: Widget item object
        """
        if not isinstance(widget_items, dict):
            return
        data = dict()
        try:
            cls.build_general_data(data, widget_items, is_update)
            cls.build_settings_data(data, widget_items)
        except Exception as ex:
            current_app.logger.debug(ex)
            return
        return data

    @classmethod
    def create(cls, widget_items=None):
        """Create the widget_items.

        :param widget_items: the widget item information.
        :returns: The :class:`widget item` instance lists or None.
        """
        def _add_widget_item(widget_setting):
            with db.session.begin_nested():
                widget_item = WidgetItem(**widget_setting)
                db.session.add(widget_item)
            db.session.commit()

        if not isinstance(widget_items, dict):
            return

        data = cls.build_object(widget_items)
        is_ok = True
        try:
            _add_widget_item(data)
        except Exception as ex:
            is_ok = False
            current_app.logger.debug(ex)
        finally:
            del data
            if not is_ok:
                db.session.rollback()
        return is_ok

    @classmethod
    def update(cls, widget_items, widget_id):
        """Update widget item.

        :param widget_items: Widget items receive from client
        :param widget_id: id of widget items
        :return: true if update success else return false
        """
        data = cls.build_object(widget_items)
        if not data:
            return False
        WidgetItem.update_by_id(widget_id.get('id'), **data)
        return True

    @classmethod
    def update_by_id(cls, widget_items, widget_id):
        """Update widget item.

        :param widget_items: Widget items receive from client
        :param widget_id: id of widget items
        :return: true if update success else return false
        """
        data = cls.build_object(widget_items, True)
        if not data:
            return False
        WidgetItem.update_by_id(widget_id.get('id'), **data)
        return True

    @classmethod
    def delete(cls, widget_id):
        """Delete widget_item.

        :param widget_id: id of widget item to delete
        :return:  true
        """
        WidgetItem.delete(widget_id.get('repository'),
                          widget_id.get('widget_type'),
                          widget_id.get('label'),
                          widget_id.get('language'))
        return True

    @classmethod
    def get_all_widget_items(cls):
        """
        Get all widget items in widget_item table.

        :return: List of widget item objects.
        """
        return db.session.query(WidgetItem).all()

    @classmethod
    def validate_exist_multi_language(cls, item, data):
        """Validate existed data between item and data.

        Arguments:
            item {WidgetItem} -- Data recieve from client
            data {WidgetItem} -- Data item in data base

        Returns:
            true if exist else false

        """
        multi_langdata = item.get('multiLangSetting')
        if multi_langdata is None:
            return False
        for k, v in multi_langdata.items():
            if data.get(k):
                current_language_data = data.get(k)
                if v.get('label') == current_language_data.get('label'):
                    return True

        return False

    @classmethod
    def is_existed(cls, widget_items, widget_item_id):
        """Check widget item is existed or not.

        :param widget_items:  Widget item
        :param widget_item_id: Id of widget item

        :return:  true if it is existed else return false
        """
        if not isinstance(widget_items, dict):
            return False
        list_widget_items = WidgetItem.get_by_repo_and_type(
            widget_items.get('repository'),
            widget_items.get('widget_type'))

        sample_lang_data = widget_items.get('multiLangSetting')
        if type(list_widget_items) is list:
            for item in list_widget_items:
                item = cls.parse_result(item)
                if widget_item_id == item.get('id'):
                    continue
                if cls.validate_exist_multi_language(item, sample_lang_data):
                    return True
        return False

    @classmethod
    def get_account_role(cls):
        """Get account role."""
        def _get_dict(x):
            dt = dict()
            for k, v in x.__dict__.items():
                if not k.startswith('__') and not k.startswith('_') \
                        and "description" not in k:
                    if not v:
                        v = ""
                    if isinstance(v, int) or isinstance(v, str):
                        dt[k] = v
            return dt

        try:
            with db.session.no_autoflush:
                role = Role.query.all()
            return list(map(_get_dict, role)) + [{"id": -99, "name": "Guest"}]
        except SQLAlchemyError:
            return

    @classmethod
    def parse_result(cls, in_result):
        """Parse data to format which can be send to client.

        Arguments:
            in_result {WidgetItems} -- [data need to be parse]

        """
        record = dict()
        settings = orjson.loads(in_result.settings)
        record['id'] = in_result.id
        record['repository_id'] = in_result.repository_id
        record['widget_type'] = in_result.widget_type
        record['label'] = in_result.label
        record['language'] = in_result.language
        record['label_color'] = settings.get('label_color')
        record['has_frame_border'] = settings.get('has_frame_border')
        record['frame_border_color'] = settings.get('frame_border_color')
        record['text_color'] = settings.get('text_color')
        record['background_color'] = settings.get('background_color')
        record['browsing_role'] = in_result.browsing_role
        record['edit_role'] = in_result.edit_role
        record['is_enabled'] = in_result.is_enabled
        record['multiLangSetting'] = settings.get('multiLangSetting')
        return record
