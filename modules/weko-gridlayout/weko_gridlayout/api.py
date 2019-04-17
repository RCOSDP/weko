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

        data = dict()
        is_ok = True
        try:
            data["repository"] = widget_items.get('repository')
            data["widget_type"] = widget_items.get('widget_type')
            data["label"] = widget_items.get('label')
            data["label_color"] = widget_items.get('label_color')
            data["frame_border"] = True
            # data["frame_border"] = data["frame_border"]
            data["frame_border_color"] = widget_items.get('frame_border_color')
            data["text_color"] = widget_items.get('text_color')
            data["background_color"] = widget_items.get('background_color')
            role = cls.get_account_role()
            data["browsing_role"] = \
                ",".join(list(map(lambda x: str(x['id']), role)))
            data["edit_role"] = data["browsing_role"]

            data["enable"] = True


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
