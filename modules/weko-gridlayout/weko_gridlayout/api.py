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
import json

from flask import current_app
from invenio_accounts.models import Role
from invenio_db import db
from sqlalchemy.exc import SQLAlchemyError

from .models import WidgetItem


class WidgetItems(object):
    """Define API for WidgetItems creation and update."""

    @classmethod
    def build_general_object(cls, data_object, widget_items,
                             data_object_settings):
        """Build general field of object.

        :param data_object: object data
        :param widget_items: widget item
        :param data_object_settings: object data setting
        """
        try:
            data_object["repository_id"] = widget_items.get('repository')
            data_object["widget_type"] = widget_items.get('widget_type')
            data_object["label"] = widget_items.get('label')
            data_object_settings["label_color"] = widget_items.get(
                'label_color')
            data_object_settings["has_frame_border"] = widget_items.get(
                'frame_border')
            data_object_settings["frame_border_color"] = widget_items.get(
                'frame_border_color')
            data_object_settings["text_color"] = widget_items.get('text_color')
            data_object_settings["background_color"] = widget_items.get(
                'background_color')
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
            data_object['settings'] = json.dumps(data_object_settings)
        except Exception as ex:
            current_app.logger.debug(ex)

    @classmethod
    def build_free_description_type(cls, widget_items, data_object_settings):
        """Build field of object type Free description.

        :param widget_items: widget items
        :param data_object_settings: data object settings
        """
        try:
            settings = widget_items.get('settings')
            data_object_settings["description"] = settings.get(
                'description')
        except Exception as ex:
            current_app.logger.debug(ex)

    @classmethod
    def build_notice_type(cls, widget_items, data_object_settings):
        """Build field of object type Notice.

        :param widget_items: widget items
        :param data_object_settings: data object settings
        """
        try:
            settings = widget_items.get('settings')
            data_object_settings["description"] = settings.get('description')
            if settings.get('more_description'):
                data_object_settings["read_more"] = settings.get('read_more')
                data_object_settings["more_description"] = settings.get(
                    'more_description')
                data_object_settings["hide_the_rest"] = settings.get(
                    'hide_the_rest')
        except Exception as ex:
            current_app.logger.debug(ex)

    @classmethod
    def build_object(cls, widget_items=None):
        """Build widget item object.

        :param widget_items: Widget Item
        :return: Widget item object
        """
        if not isinstance(widget_items, dict):
            return
        data = dict()
        try:
            data_setting = dict()
            if str(widget_items.get("widget_type")) == "Free description":
                cls.build_free_description_type(widget_items,
                                                data_setting)
            elif str(widget_items.get("widget_type")) == "Notice":
                cls.build_notice_type(widget_items, data_setting)
            cls.build_general_object(data, widget_items, data_setting)
        except Exception as ex:
            current_app.logger.debug(ex)
            return
        return data

    @classmethod
    def create(cls, widget_items=None):
        """Create the widget_items. Delete all widget_items before creation.

        :param widget_items: the widget item information.
        :returns: The :class:`widget item` instance lists or None.
        """
        def _add_widget_item(widget_setting):
            print(widget_setting)
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
        WidgetItem.update(widget_id.get('repository'),
                          widget_id.get('widget_type'), widget_id.get('label'),
                          **data)
        return True

    @classmethod
    def delete(cls, widget_id):
        """Delete widget_item.

        :param widget_id: id of widget item to delete
        :return:  true
        """
        WidgetItem.delete(widget_id.get('repository'),
                          widget_id.get('widget_type'), widget_id.get('label'))
        return True

    @classmethod
    def get_all_widget_items(cls):
        """
        Get all widget items in widget_item table.

        :return: List of widget item objects.
        """
        return db.session.query(WidgetItem).all()

    @classmethod
    def is_existed(cls, widget_items):
        """Check widget item is existed or not.

        :param widget_items:  Widget item
        :return:  true if it is existed else return false
        """
        if not isinstance(widget_items, dict):
            return False
        widget_item = WidgetItem.get(widget_items.get('repository'),
                                     widget_items.get('widget_type'),
                                     widget_items.get('label'))
        return widget_item is not None

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
            return list(map(_get_dict, role)) + [{"id": 99, "name": "Guest"}]
        except SQLAlchemyError:
            return

    @classmethod
    def parse_general_data(cls, record, in_result, record_setting):
        """Parse general data.

        :param record: data after parse
        :param in_result: data parser
        :param record_setting: data settings after parse
        """
        record['repository_id'] = in_result.repository_id
        record['widget_type'] = in_result.widget_type
        record['label'] = in_result.label
        record['label_color'] = record_setting.get('label_color')
        record['has_frame_border'] = record_setting.get('has_frame_border')
        record['frame_border_color'] = record_setting.get('frame_border_color')
        record['text_color'] = record_setting.get('text_color')
        record['background_color'] = record_setting.get('background_color')
        record['browsing_role'] = in_result.browsing_role
        record['edit_role'] = in_result.edit_role
        record['is_enabled'] = in_result.is_enabled

    @classmethod
    def parse_free_description(cls, record, record_setting):
        """Parse data item type Free description.

        :param record: data after parse
        :param record_setting: data settings after parse
        """
        settings = dict()
        settings['description'] = record_setting.get('description')
        record['settings'] = settings

    @classmethod
    def parse_notice_description(cls, record, record_setting):
        """Parse data item type Notice.

        :param record: data after parse
        :param record_setting: data settings after parse
        """
        settings = dict()
        settings['description'] = record_setting.get('description')
        settings['read_more'] = record_setting.get('read_more')
        settings['more_description'] = record_setting.get('more_description')
        settings['hide_the_rest'] = record_setting.get('hide_the_rest')
        record['settings'] = settings

    @classmethod
    def parse_result(cls, in_result):
        """Parse data to format which can be send to client.

        Arguments:
            in_result {WidgetItems} -- [data need to be parse]
        """
        record = dict()
        settings = json.loads(in_result.settings)
        cls.parse_general_data(record, in_result, settings)
        if str(record['widget_type']) == "Free description":
            cls.parse_free_description(record, settings)
        elif str(record['widget_type']) == "Notice":
            cls.parse_notice_description(record, settings)
        return record
