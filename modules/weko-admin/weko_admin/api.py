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


from .models import ChunkItem

class ChunkItems(object):
    """Define API for ChunkItems creation and update."""

    # @classmethod
    # def create(cls, data):
    #     """Create data."""
    #     try:
    #         dataObj = ChunkItem()
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
    def create(cls, pid=None, chunk_items=None):
        """Create the chunk_items. Delete all chunk_items before creation.

        :param pid: parent chunk item id.
        :param chunk_items: the chunk item information.
        :returns: The :class:`chunk item` instance lists or None.
        """
        def _add_chunk_item(data):
            with db.session.begin_nested():
                chunk_item = ChunkItem(**data)
                db.session.add(chunk_item)
            db.session.commit()

        if not isinstance(chunk_items, dict):
            return

        data = dict()
        is_ok = True
        try:
            data["repository"] = chunk_items.get('repository')
            data["chunk_type"] = chunk_items.get('chunk_type')
            data["label_color"] = chunk_items.get('label_color')
            data["frame_border"] = True
            # data["frame_border"] = data["frame_border"]
            data["frame_border_color"] = chunk_items.get('frame_border_color')
            data["text_color"] = chunk_items.get('text_color')
            data["background_color"] = chunk_items.get('background_color')
            role = cls.get_account_role()
            data["browsing_role"] = \
                ",".join(list(map(lambda x: str(x['id']), role)))
            data["edit_role"] = data["browsing_role"]

            data["enable"] = True


            _add_chunk_item(data)
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
