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
from invenio_accounts.models import Role
# from invenio_communities.models import Community
from invenio_db import db
from flask import current_app, json


from .models import WidgetItem

class WidgetItems(object):
    """Define API for WidgetItems creation and update."""

    # @classmethod
    # def create(cls, data):
    #     """Create data."""
    #     try:
    #         dataObj = WidgetItem()
    #         with db.session.begin_nested():
    #             dataObj.default_dis_num = data.get('dlt_dis_num_selected')
    #             dataObj.default_dis_sort_index = data.get(
    #                 'dlt_index_sort_selected')
    #             dataObj.default_dis_sort_keyword = data.get(
    #                 'dlt_keyword_sort_selected')
    #             dataObj.sort_setting = data.get('sort_options')
    #             dataObj.search_conditions = data.get('detail_condition')
    #             dataObj.search_setting_all = data
    #             db.session.add(dataObj)
    #         db.session.commit()
    #     except BaseException as ex:
    #         db.session.rollback()
    #         current_app.logger.debug(ex)
    #         raise
    #     return cls
    @classmethod
    def build_object(cls, widget_items=None):
        if not isinstance(widget_items, dict):
            return
        data = dict()
        try:
            data["repository_id"] = widget_items.get('repository')
            data["widget_type"] = widget_items.get('widget_type')
            data["label"] = widget_items.get('label')
            data["label_color"] = widget_items.get('label_color')
            data["has_frame_border"] = widget_items.get('frame_border')
            data["frame_border_color"] = widget_items.get('frame_border_color')
            data["text_color"] = widget_items.get('text_color')
            data["background_color"] = widget_items.get('background_color')
            role = widget_items.get('browsing_role')
            data["browsing_role"] = ",".join(str(e) for e in role)
            role = widget_items.get('edit_role')
            data["edit_role"] = ",".join(str(e) for e in role)
            data["is_enabled"] = widget_items.get('enable')
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
        def _add_widget_item(data):
            with db.session.begin_nested():
                widget_item = WidgetItem(**data)
                db.session.add(widget_item)
            db.session.commit()

        if not isinstance(widget_items, dict):
            return

        data = cls.build_object(widget_items)
        is_ok = True
        try:
            _add_widget_item(data)
        # except IntegrityError as ie:
        #     if 'uix_position' in ''.join(ie.args):
        #         try:
        #             pid_info = cls.get_index(pid, with_count=True)
        #             data["position"] = 0 if not pid_info else \
        #                 (pid_info.position_max + 1
        #                  if pid_info.position_max is not None else 0)
        #             _add_index(data)
        #         except SQLAlchemyError as ex:
        #             is_ok = False
        #             current_app.logger.debug(ex)
        #     else:
        #         is_ok = False
        #         current_app.logger.debug(ie)
        except Exception as ex:
            is_ok = False
            current_app.logger.debug(ex)
        finally:
            del data
            if not is_ok:
                db.session.rollback()
        return is_ok

    @classmethod
    def update(cls, widget_items):
        data = cls.build_object(widget_items)
        if not data:
            return False
        widget_item = WidgetItem.update(widget_items.get('repository'),
                                        widget_items.get('widget_type'),
                                        widget_items.get('label'),
                                        **data)
        return (widget_item is not None)

    @classmethod
    def get_all_widget_items(cls):
        """
        Get all widget items in widget_item table.

        :return: List of widget item objects.
        """
        return db.session.query(WidgetItem).all()


    @classmethod
    def is_existed(cls, widget_items):
        if not isinstance(widget_items, dict):
            return False
        widget_item = WidgetItem.get(widget_items.get('repository'),
                                        widget_items.get('widget_type'),
                                        widget_items.get('label'))
        return (widget_item is not None)


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
    def parse_result(cls, in_result):
        """
        parse data to format which can be send to client
        
        Arguments:
            in_result {WidgetItems} -- [data need to be parse]
        """
        record = dict()
        record['repository_id'] = in_result.repository_id
        record['widget_type'] = in_result.widget_type
        record['label'] = in_result.label
        record['label_color'] = in_result.label_color
        record['has_frame_border'] = in_result.has_frame_border
        record['frame_border_color'] = in_result.frame_border_color
        record['text_color'] = in_result.text_color
        record['background_color'] = in_result.background_color
        record['browsing_role'] = in_result.browsing_role
        record['edit_role'] = in_result.edit_role
        record['is_enabled'] = in_result.is_enabled

        return record