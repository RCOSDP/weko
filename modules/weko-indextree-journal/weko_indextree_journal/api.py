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

"""API for weko-index-tree."""

from datetime import datetime
from copy import deepcopy
from flask import current_app, json
from flask_login import current_user
from invenio_db import db
from invenio_accounts.models import Role
from sqlalchemy.orm import aliased
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.sql.expression import func, literal_column
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from weko_groups.api import Group
from .models import Index
from .utils import get_tree_json, cached_index_tree_json, reset_tree, get_index_id_list
from invenio_i18n.ext import current_i18n
from invenio_indexer.api import RecordIndexer

class Journals(object):
    """Define API for journal creation and update."""

    @classmethod
    def create(cls, index_id=None, journals=None):
        """
        Create the journals. Delete all journals before creation.

        :param index_id: the index id.
        :param journals: the journal information.
        :returns: The :class:`Journal` instance lists or None.
        """

        def _add_journal(data):
            with db.session.begin_nested():
                journal = Journal(**data)
                db.session.add(journal)
            db.session.commit()

        if not isinstance(journals, dict):
            return

        data = dict()
        is_ok = True
        try:
            cid = journals.get('id')

            if not cid:
                return

            data["id"] = cid

            # check index id.
            index_info = cls.get_index(index_id, with_count=True)
            if index_info:
                data["index_id"] = index_id
            else:
                return

            _add_index(data)
        except IntegrityError as ie:
            is_ok = False
            current_app.logger.debug(ie)
        except Exception as ex:
            is_ok = False
            current_app.logger.debug(ex)
        finally:
            del data
            if not is_ok:
                db.session.rollback()
        return is_ok

    @classmethod
    def update(cls, journal_id, **data):
        """
        Update the journal detail info.

        :param journal_id: Identifier of the journal.
        :param detail: new journal info for update.
        :return: Updated journal info
        """
        try:
            with db.session.begin_nested():
                journal = cls.get_journal(journal_id)
                if not journal:
                    return

                for k, v in data.items():
                    if isinstance(getattr(journal, k), int):
                        if isinstance(v, str) and len(v) == 0:
                            continue

                    if isinstance(v, dict):
                        v = ",".join(map(lambda x: str(x["id"]), v["allow"]))
                    
                    setattr(journal, k, v)
                journal.owner_user_id = current_user.get_id()
                db.session.merge(journal)
            db.session.commit()
            return journal
        except Exception as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
        return

    @classmethod
    def delete(cls, journal_id):
        """
        Delete the journal by journal id.

        :param journal_id: Identifier of the journal.
        :return: bool True: Delete success None: Delete failed
        """
        try:
            with db.session.begin_nested():
                slf = cls.get_journal(journal_id)
                if not slf:
                    return
                    
                db.session.delete(slf)
                db.session.commit()
                return dct
        except Exception as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
            return None
        return 0

    @classmethod
    def delete_by_action(cls, action, journal_id, path):
        from weko_deposit.api import WekoDeposit
        if "move" == action:
            result = cls.delete(journal_id, True)
            if result is not None:
                # move indexes all
                target = path.split('/')
                if len(target) >= 2:
                    target.pop(-2)
                    target = "/".join(target)
                else:
                    target = ""
                WekoDeposit.update_by_index_tree_id(path, target)
        else:
            result = cls.delete(journal_id)
            if result is not None:
                # delete indexes all
                WekoDeposit.delete_by_index_tree_id(path)
        return result

    @classmethod
    def get_index_with_role(cls, index_id):

        def _get_allow_deny(allow, role):
            alw = []
            deny = []
            if isinstance(role, list):
                while role:
                    tmp = role.pop(0)
                    if str(tmp["id"]) in allow:
                        alw.append(tmp)
                    else:
                        deny.append(tmp)
            return alw, deny

        def _get_group_allow_deny(allow_group_id=[], groups=[]):
            allow = []
            deny = []
            if not groups:
                return allow, deny
            for group in groups:
                if str(group.id) in allow_group_id:
                    allow.append({'id':str(group.id), 'name':group.name})
                else:
                    deny.append({'id': str(group.id), 'name': group.name})

            return allow, deny

        index = dict(cls.get_index(index_id))

        role = cls.get_account_role()
        allow = index["browsing_role"].split(',') \
            if len(index["browsing_role"]) else None
        if allow:
            allow, deny = _get_allow_deny(allow, deepcopy(role))
        else:
            allow = role
            deny = []
        index["browsing_role"] = dict(allow=allow, deny=deny)

        allow = index["contribute_role"].split(',') \
            if len(index["contribute_role"]) else None
        if allow:
            allow, deny = _get_allow_deny(allow, role)
        else:
            allow = role
            deny = []
        index["contribute_role"] = dict(allow=allow, deny=deny)

        if index["public_date"]:
            index["public_date"] = index["public_date"].strftime('%Y%m%d')

        group_list = Group.query.all()

        allow_group_id = index["browsing_group"].split(',') \
            if len(index["browsing_group"]) else []
        allow_group, deny_group = _get_group_allow_deny(allow_group_id,
                                                        deepcopy(group_list))
        index["browsing_group"] = dict(allow=allow_group, deny=deny_group)

        allow_group_id = index["contribute_group"].split(',') \
            if len(index["contribute_group"]) else []
        allow_group, deny_group = _get_group_allow_deny(allow_group_id,
                                                        deepcopy(group_list))
        index["contribute_group"] = dict(allow=allow_group, deny=deny_group)

        return index

    @classmethod
    def get_index(cls, index_id, with_count=False):
        with db.session.begin_nested():
            if with_count:
                stmt = db.session.query(Index.parent, func.max(Index.position).
                                        label('position_max'))\
                    .filter(Index.parent == index_id)\
                    .group_by(Index.parent).subquery()
                obj = db.session.query(Index, stmt.c.position_max). \
                    outerjoin(stmt, Index.id == stmt.c.parent).\
                    filter(Index.id == index_id).one_or_none()
            else:
                obj = db.session.query(Index).\
                    filter_by(id=index_id).one_or_none()

        return obj