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

class Indexes(object):
    """Define API for index tree creation and update."""

    @classmethod
    def create(cls, pid=None, indexes=None):
        """
        Create the indexes. Delete all indexes before creation.

        :param pid: parent index id.
        :param indexes: the index information.
        :returns: The :class:`Index` instance lists or None.
        """

        def _add_index(data):
            with db.session.begin_nested():
                index = Index(**data)
                db.session.add(index)
            db.session.commit()

        if not isinstance(indexes, dict):
            return

        data = dict()
        is_ok = True
        try:
            cid = indexes.get('id')

            if not cid:
                return

            data["id"] = cid
            data["parent"] = pid
            data["index_name"] = indexes.get('value')
            data["index_name_english"] = indexes.get('value')
            data["index_link_name_english"] = data["index_name_english"]
            data["owner_user_id"] = current_user.get_id()
            role = cls.get_account_role()
            data["browsing_role"] = \
                ",".join(list(map(lambda x: str(x['id']), role)))
            data["contribute_role"] = data["browsing_role"]

            data["more_check"] = False
            data["display_no"] = current_app.config['WEKO_INDEX_TREE_DEFAULT_DISPLAY_NUMBER']

            group_list = ''
            groups = Group.query.all()
            for group in groups:
                if not group_list:
                    group_list = str(group.id)
                else:
                    group_list = group_list + ',' + str(group.id)

            data["browsing_group"] = group_list
            data["contribute_group"] = group_list

            if int(pid) == 0:
                pid_info = cls.get_root_index_count()
                data["position"] = 0 if not pid_info else \
                    (0 if pid_info.position_max is None
                        else pid_info.position_max + 1)
            else:
                pid_info = cls.get_index(pid, with_count=True)

                if pid_info:
                    data["position"] = 0 if pid_info.position_max is None \
                        else pid_info.position_max + 1
                    iobj = pid_info.Index
                    data["harvest_public_state"] = iobj.harvest_public_state

                    data["display_format"] = iobj.display_format
                    data["image_name"] = iobj.image_name

                    if iobj.recursive_public_state:
                        data["public_state"] = iobj.public_state
                        data["public_date"] = iobj.public_date
                        data["recursive_public_state"] = iobj.recursive_public_state
                    if iobj.recursive_browsing_role:
                        data["browsing_role"] = iobj.browsing_role
                        data["recursive_browsing_role"] = iobj.recursive_browsing_role
                    if iobj.recursive_contribute_role:
                        data["contribute_role"] = iobj.contribute_role
                        data["recursive_contribute_role"] = iobj.recursive_contribute_role
                    if iobj.recursive_browsing_group:
                        data["browsing_group"] = iobj.browsing_group
                        data["recursive_browsing_group"] = iobj.recursive_browsing_group
                    if iobj.recursive_contribute_group:
                        data["contribute_group"] = iobj.contribute_group
                        data["recursive_contribute_group"] = iobj.recursive_contribute_group

                else:
                    return

            _add_index(data)
        except IntegrityError as ie:
            if 'uix_position' in ''.join(ie.args):
                try:
                    pid_info = cls.get_index(pid, with_count=True)
                    data["position"] = 0 if not pid_info else \
                        (pid_info.position_max + 1
                            if pid_info.position_max is not None else 0)
                    _add_index(data)
                except SQLAlchemyError as ex:
                    is_ok = False
                    current_app.logger.debug(ex)
            else:
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
    def update(cls, index_id, **data):
        """
        Update the index detail info.

        :param index_id: Identifier of the index.
        :param detail: new index info for update.
        :return: Updated index info
        """
        try:
            with db.session.begin_nested():
                index = cls.get_index(index_id)
                if not index:
                    return

                for k, v in data.items():
                    if isinstance(getattr(index, k), int):
                        if isinstance(v, str) and len(v) == 0:
                            continue
                    if isinstance(v, dict):
                        v = ",".join(map(lambda x: str(x["id"]), v["allow"]))
                    if "public_date" in k:
                        if len(v) > 0:
                            v = datetime.strptime(v, '%Y%m%d')
                        else:
                            v = None
                    if "have_children" in k:
                        continue
                    setattr(index, k, v)
                index.owner_user_id = current_user.get_id()
                db.session.merge(index)
            db.session.commit()
            return index
        except Exception as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
        return

    @classmethod
    def delete(cls, index_id, del_self=False):
        """
        Delete the index by index id.

        :param index_id: Identifier of the index.
        :return: bool True: Delete success None: Delete failed
        """
        try:
            if del_self:
                with db.session.begin_nested():
                    slf = cls.get_index(index_id)
                    if not slf:
                        return

                    dct = db.session.query(Index).filter(Index.parent == index_id).\
                        update({Index.parent: slf.parent,
                                Index.owner_user_id: current_user.get_id(),
                                Index.updated: datetime.utcnow()},
                               synchronize_session='fetch')
                    db.session.delete(slf)
                    db.session.commit()
                    return dct
            else:
                with db.session.no_autoflush:
                    recursive_t = cls.recs_query(pid=index_id)
                    obj = db.session.query(recursive_t).\
                    union_all(db.session.query(Index.parent, Index.id,
                                               literal_column("''", db.Text).label("path"),
                                               literal_column("''", db.Text).label("name"),
                                               literal_column("''", db.Text).label("name_en"),
                                               literal_column("0", db.Integer).label("lev")).
                              filter(Index.id == index_id)).all()

                if obj:
                    p_lst = [o.cid for o in obj]
                    with db.session.begin_nested():
                        dct = db.session.query(Index).filter(Index.id.in_(p_lst)).\
                            delete(synchronize_session='fetch')
                    db.session.commit()
                    return dct
        except Exception as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
            return None
        return 0

    @classmethod
    def delete_by_action(cls, action, index_id, path):
        from weko_deposit.api import WekoDeposit
        if "move" == action:
            result = cls.delete(index_id, True)
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
            result = cls.delete(index_id)
            if result is not None:
                # delete indexes all
                WekoDeposit.delete_by_index_tree_id(path)
        return result

    @classmethod
    def move(cls, index_id, **data):

        def _update_index(parent=None):
            with db.session.begin_nested():
                index = Index.query.filter_by(id=index_id).one()
                index.position = position_max
                index.owner_user_id = user_id
                flag_modified(index, 'position')
                flag_modified(index, 'owner_user_id')
                if parent:
                    index.parent = parent
                    flag_modified(index, 'parent')
                db.session.merge(index)
            db.session.commit()

        is_ok = True
        user_id = current_user.get_id()
        position_max = 0

        if isinstance(data, dict):
            pre_parent = data.get('pre_parent')
            parent = data.get('parent')
            if not pre_parent or not parent:
                return False

            try:
                # move index on the same hierarchy
                if str(pre_parent) == str(parent):
                    parent_info = cls.get_index(pre_parent, with_count=True)
                    position = int(data.get('position'))
                    pmax = parent_info.position_max \
                        if parent_info.position_max is not None else 0

                    if position >= pmax:
                        position_max = pmax + 1
                        try:
                            _update_index()
                        except IntegrityError as ie:
                            if 'uix_position' in ''.join(ie.args):
                                try:
                                    position_max += 1
                                    _update_index()
                                except SQLAlchemyError as ex:
                                    is_ok = False
                                    current_app.logger.debug(ex)
                            else:
                                is_ok = False
                                current_app.logger.debug(ie)
                        except Exception as ex:
                            is_ok = False
                            current_app.logger.debug(ex)
                        finally:
                            if not is_ok:
                                db.session.rollback()
                    else:
                        position_max = position
                        try:
                            with db.session.begin_nested():
                                nlst = Index.query.filter_by(parent=parent).\
                                    order_by(Index.position).with_for_update().all()
                                n = t = -1

                                for i in range(len(nlst)):
                                    db.session.delete(nlst[i])
                                    if nlst[i].id == index_id:
                                        n = i
                                    if position == nlst[i].position:
                                        t = i
                                # if the index has been deleted.
                                if n < 0:
                                    raise Exception()

                                pre_index = nlst.pop(n)
                                if n < t:
                                    t -= 1
                                if t < 0:
                                    t = position - 1

                                nlst.insert(t + 1, pre_index)
                                db.session.flush()
                                for i in range(len(nlst)):
                                    nid = Index()
                                    for k in dict(nid).keys():
                                        setattr(nid, k, getattr(nlst[i], k))
                                    nid.position = i
                                    nid.owner_user_id = user_id
                                    db.session.add(nid)
                            db.session.commit()
                        except Exception as ex:
                            is_ok = False
                            current_app.logger.debug(ex)
                        finally:
                            if not is_ok:
                                db.session.rollback()
                else:
                    slf_path = cls.get_self_path(index_id)
                    parent_info = cls.get_index(parent, with_count=True)
                    position_max = parent_info.position_max + 1 \
                        if parent_info.position_max is not None else 0
                    try:
                        _update_index(parent)
                    except IntegrityError as ie:
                        if 'uix_position' in ''.join(ie.args):
                            try:
                                parent_info = cls.get_index(parent, with_count=True)
                                position_max = parent_info.position_max + 1 \
                                    if parent_info.position_max is not None else 0
                                _update_index()
                            except SQLAlchemyError as ex:
                                is_ok = False
                                current_app.logger.debug(ex)
                        else:
                            is_ok = False
                            current_app.logger.debug(ie)
                    except Exception as ex:
                        is_ok = False
                        current_app.logger.debug(ex)
                    finally:
                        if not is_ok:
                            db.session.rollback()

                    # move items
                    target = cls.get_self_path(index_id)
                    from weko_deposit.api import WekoDeposit
                    WekoDeposit.update_by_index_tree_id(slf_path.path, target.path)
            except Exception:
                is_ok = False
        return is_ok

    @classmethod
    @cached_index_tree_json(timeout=None,)
    def get_index_tree(cls,pid=0):
        """Get index tree json"""
        return get_tree_json(cls.get_recursive_tree(pid), pid)

    @classmethod
    def get_browsing_tree(cls,pid=0):
        tree = cls.get_index_tree(pid)
        reset_tree(tree=tree)
        return tree

    @classmethod
    def get_more_browsing_tree(cls, pid=0, more_ids=[]):
        tree = cls.get_index_tree(pid)
        reset_tree(tree=tree, more_ids=more_ids)
        return tree

    @classmethod
    def get_browsing_tree_paths(cls,pid=0):
        id_list = get_index_id_list(cls.get_browsing_tree(pid), [])
        paths = []
        if id_list:
            for id in id_list:
                paths.append(Indexes.get_self_path(id).path)

        return paths

    @classmethod
    def get_contribute_tree(cls, pid,root_node_id=0):
        """"""
        from weko_deposit.api import WekoRecord
        record = WekoRecord.get_record_by_pid(pid)
        tree = cls.get_index_tree(root_node_id)
        if record.get('_oai'):
            reset_tree(tree=tree, path=record.get('path'))
        else:
            reset_tree(tree=tree, path=[])

        return tree

    @classmethod
    def get_recursive_tree(cls, pid=0):
        """"""
        with db.session.begin_nested():
            recursive_t = cls.recs_tree_query(pid)
            if pid != 0:
                recursive_t = cls.recs_root_tree_query(pid)
            qlst = [recursive_t.c.pid, recursive_t.c.cid,
                    recursive_t.c.position, recursive_t.c.name,
                    recursive_t.c.public_state, recursive_t.c.public_date,
                    recursive_t.c.browsing_role, recursive_t.c.contribute_role,
                    recursive_t.c.browsing_group, recursive_t.c.contribute_group,
                    recursive_t.c.more_check, recursive_t.c.display_no
                    ]
            obj = db.session.query(*qlst). \
                order_by(recursive_t.c.lev,
                         recursive_t.c.pid,
                         recursive_t.c.cid).all()
        return obj

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

    @classmethod
    def get_root_index_count(cls):
        with db.session.begin_nested():
            obj = db.session.query(Index.parent,
                                   func.max(Index.position).
                                   label('position_max')).\
                filter_by(parent=0).group_by(Index.parent).one_or_none()
        return obj

    @classmethod
    def get_account_role(cls):

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
    def get_path_list(cls, node_lst):
        """
        Get index tree info.

        :param node_lst: Identifier list of the index.
        :return: the list of index.
        """
        recursive_t = cls.recs_query()
        q = db.session.query(recursive_t).filter(
            recursive_t.c.cid.in_(node_lst)).all()
        return q

    @classmethod
    def get_path_name(cls, node_path):
        """
        Get index title info.

        :param node_path: Identifier list of the index.
        :return: the list of index.
        """
        recursive_t = cls.recs_query()
        q = db.session.query(recursive_t).filter(
            recursive_t.c.path.in_(node_path)). \
            order_by(recursive_t.c.path).all()
        return q

    @classmethod
    def get_self_list(cls, node_path):
        """
        Get index list info.

        :param node_path: Identifier of the index.
        :return: the list of index.
        """
        index = node_path.rfind('/')
        pid = node_path[index + 1:]
        recursive_t = cls.recs_query()
        q = db.session.query(recursive_t).filter(
            db.or_(recursive_t.c.pid == pid,
                   recursive_t.c.cid == pid)). \
            order_by(recursive_t.c.path).all()
        return q

    @classmethod
    def get_all_path_list(cls, node_path):
        """
        Get child of index list info.

        :param node_path: Identifier of the index.
        :return: the list of index.
        """

        # def get_path_list(node_path):
        #     """
        #     Get index list info.
        #
        #     :param node_path: Identifier of the index.
        #     :return: the list of index.
        #     """
        #     node_path = str(node_path)
        #     index = node_path.rfind('/')
        #     pid = node_path[index + 1:]
        #     recursive_t = cls.recs_query()
        #     q = db.session.query(recursive_t).filter(
        #         db.or_(recursive_t.c.pid == pid,
        #                recursive_t.c.cid == pid)). \
        #         order_by(recursive_t.c.path).all()
        #     if q and len(q) >1:
        #         path_list.append(q[0].path)
        #         q = q[1:]
        #         for inx in q:
        #             get_path_list(inx.path)
        #     else:
        #         path_list.append(q[0].path)
        #     return path_list
        #
        # path_list=[]
        # path = get_path_list(node_path)
        path = Indexes.get_browsing_tree_paths(node_path)

        return path

    @classmethod
    def get_self_path(cls, node_id):
        """
        Get index view path info.
        :param node_id: Identifier of the index.
        :return: the type of Index.
        """
        try:
            recursive_t = cls.recs_query()
            return db.session.query(recursive_t).filter(
                recursive_t.c.cid == str(node_id)).one_or_none()
        except Exception as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
            return False


    @classmethod
    def recs_query(cls, pid=0):
        """
        Init select condition of index.

        :return: the query of db.session.
        """
        recursive_t = db.session.query(
            Index.parent.label("pid"),
            Index.id.label("cid"),
            func.cast(Index.id, db.Text).label("path"),
            Index.index_name.label("name"),
            # add by ryuu at 1108 start
            Index.index_name_english.label("name_en"),
            # add by ryuu at 1108 end
            literal_column("1", db.Integer).label("lev")).filter(
            Index.parent == pid). \
            cte(name="recursive_t", recursive=True)

        rec_alias = aliased(recursive_t, name="rec")
        test_alias = aliased(Index, name="t")
        recursive_t = recursive_t.union_all(
            db.session.query(
                test_alias.parent,
                test_alias.id,
                rec_alias.c.path + '/' + func.cast(test_alias.id, db.Text),
                rec_alias.c.name + '/' + test_alias.index_name,
                # add by ryuu at 1108 start
                rec_alias.c.name_en + '/' + test_alias.index_name_english,
                # add by ryuu at 1108 end
                rec_alias.c.lev + 1).filter(
                test_alias.parent == rec_alias.c.cid)
        )

        return recursive_t

    @classmethod
    def recs_tree_query(cls, pid=0,):
        """
        Init select condition of index.

        :return: the query of db.session.
        """
        lang = current_i18n.language
        if lang == 'ja':
            recursive_t = db.session.query(
                Index.parent.label("pid"),
                Index.id.label("cid"),
                func.cast(Index.id, db.Text).label("path"),
                func.coalesce(Index.index_name, Index.index_name_english).label("name"),
                Index.position,
                Index.public_state,
                Index.public_date,
                Index.browsing_role,
                Index.contribute_role,
                Index.browsing_group,
                Index.contribute_group,
                Index.more_check,
                Index.display_no,
                literal_column("1", db.Integer).label("lev")).filter(
                Index.parent == pid). \
                cte(name="recursive_t", recursive=True)

            rec_alias = aliased(recursive_t, name="rec")
            test_alias = aliased(Index, name="t")
            recursive_t = recursive_t.union_all(
                db.session.query(
                    test_alias.parent,
                    test_alias.id,
                    rec_alias.c.path + '/' + func.cast(test_alias.id, db.Text),
                    func.coalesce(test_alias.index_name, test_alias.index_name_english),
                    test_alias.position,
                    test_alias.public_state,
                    test_alias.public_date,
                    test_alias.browsing_role,
                    test_alias.contribute_role,
                    test_alias.browsing_group,
                    test_alias.contribute_group,
                    test_alias.more_check,
                    test_alias.display_no,
                    rec_alias.c.lev + 1).filter(
                    test_alias.parent == rec_alias.c.cid)
            )
        else:
            recursive_t = db.session.query(
                Index.parent.label("pid"),
                Index.id.label("cid"),
                func.cast(Index.id, db.Text).label("path"),
                Index.index_name_english.label("name"),
                Index.position,
                Index.public_state,
                Index.public_date,
                Index.browsing_role,
                Index.contribute_role,
                Index.browsing_group,
                Index.contribute_group,
                Index.more_check,
                Index.display_no,
                literal_column("1", db.Integer).label("lev")).filter(
                Index.parent == pid). \
                cte(name="recursive_t", recursive=True)

            rec_alias = aliased(recursive_t, name="rec")
            test_alias = aliased(Index, name="t")
            recursive_t = recursive_t.union_all(
                db.session.query(
                    test_alias.parent,
                    test_alias.id,
                    rec_alias.c.path + '/' + func.cast(test_alias.id, db.Text),
                    test_alias.index_name_english,
                    test_alias.position,
                    test_alias.public_state,
                    test_alias.public_date,
                    test_alias.browsing_role,
                    test_alias.contribute_role,
                    test_alias.browsing_group,
                    test_alias.contribute_group,
                    test_alias.more_check,
                    test_alias.display_no,
                    rec_alias.c.lev + 1).filter(
                    test_alias.parent == rec_alias.c.cid)
            )

        return recursive_t

    @classmethod
    def recs_root_tree_query(cls, pid=0, ):
        """
        Init select condition of index.

        :return: the query of db.session.
        """
        lang = current_i18n.language
        if lang == 'ja':
            recursive_t = db.session.query(
                Index.parent.label("pid"),
                Index.id.label("cid"),
                func.cast(Index.id, db.Text).label("path"),
                func.coalesce(Index.index_name, Index.index_name_english).label("name"),
                Index.position,
                Index.public_state,
                Index.public_date,
                Index.browsing_role,
                Index.contribute_role,
                Index.browsing_group,
                Index.contribute_group,
                Index.more_check,
                Index.display_no,
                literal_column("1", db.Integer).label("lev")).filter(
                Index.id == pid). \
                cte(name="recursive_t", recursive=True)

            rec_alias = aliased(recursive_t, name="rec")
            test_alias = aliased(Index, name="t")
            recursive_t = recursive_t.union_all(
                db.session.query(
                    test_alias.parent,
                    test_alias.id,
                    rec_alias.c.path + '/' + func.cast(test_alias.id, db.Text),
                    func.coalesce(test_alias.index_name, test_alias.index_name_english),
                    test_alias.position,
                    test_alias.public_state,
                    test_alias.public_date,
                    test_alias.browsing_role,
                    test_alias.contribute_role,
                    test_alias.browsing_group,
                    test_alias.contribute_group,
                    test_alias.more_check,
                    test_alias.display_no,
                    rec_alias.c.lev + 1).filter(
                    test_alias.parent == rec_alias.c.cid)
            )
        else:
            recursive_t = db.session.query(
                Index.parent.label("pid"),
                Index.id.label("cid"),
                func.cast(Index.id, db.Text).label("path"),
                Index.index_name_english.label("name"),
                Index.position,
                Index.public_state,
                Index.public_date,
                Index.browsing_role,
                Index.contribute_role,
                Index.browsing_group,
                Index.contribute_group,
                Index.more_check,
                Index.display_no,
                literal_column("1", db.Integer).label("lev")).filter(
                Index.id == pid). \
                cte(name="recursive_t", recursive=True)

            rec_alias = aliased(recursive_t, name="rec")
            test_alias = aliased(Index, name="t")
            recursive_t = recursive_t.union_all(
                db.session.query(
                    test_alias.parent,
                    test_alias.id,
                    rec_alias.c.path + '/' + func.cast(test_alias.id, db.Text),
                    test_alias.index_name_english,
                    test_alias.position,
                    test_alias.public_state,
                    test_alias.public_date,
                    test_alias.browsing_role,
                    test_alias.contribute_role,
                    test_alias.browsing_group,
                    test_alias.contribute_group,
                    test_alias.more_check,
                    test_alias.display_no,
                    rec_alias.c.lev + 1).filter(
                    test_alias.parent == rec_alias.c.cid)
            )

        return recursive_t

    @classmethod
    def get_harvest_public_state(cls, path):
        try:
            last_path = path.pop(-1).split('/')
            qry = db.session.\
                query(func.every(Index.harvest_public_state).
                      label('parent_state')).filter(Index.id.in_(last_path))
            for i in range(len(path)):
                path[i] = path[i].split('/')
                path[i] = db.session.\
                    query(func.every(Index.harvest_public_state)).\
                    filter(Index.id.in_(path[i]))
            smt = qry.union_all(*path).subquery()
            result = db.session.query(func.bool_or(smt.c.parent_state).label('parent_state')).one()
            return result.parent_state
        except Exception as se:
            current_app.logger.debug(se)
            return False

    @classmethod
    def set_item_sort_custom(cls, index_id, sort_json={}):
        """Set custom sort"""

        # change type of custom sort data
        sort_dict_db = dict(sort_json)

        for k,v in sort_dict_db.items():
            if v != "":
                sort_dict_db[k] = int(v)
            else:
                sort_dict_db[k] = 0

        try:
            with db.session.begin_nested():
                index = cls.get_index(index_id)
                if not index:
                    return
                index.item_custom_sort = sort_dict_db
                db.session.merge(index)
            db.session.commit()
            return index
        except Exception as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
        return

    @classmethod
    def update_item_sort_custom_es(cls, index_path, sort_json=[]):
        """
        Set custom sort
        :param index_path selected index path
        :param sort_json custom setted item sort

        """
        try:
            upd_item_sort_q = {
                "query": {
                    "match": {
                        "path.tree": "@index"
                    }
                }
            }
            query_q = json.dumps(upd_item_sort_q).replace("@index", index_path)
            query_q = json.loads(query_q)
            indexer = RecordIndexer()
            res = indexer.client.search(index="weko", body=query_q)

            for d in sort_json:
                for h in res.get("hits").get("hits"):
                    if int(h.get('_source').get('control_number')) == int(d.get("id")):
                        body = {
                            'doc': {
                                'custom_sort': d.get('custom_sort'),
                            }
                        }
                        indexer.client.update(
                            index="weko",
                            doc_type="item",
                            id=h.get("_id"),
                            body=body
                        )
                        break

        except Exception as ex:
            current_app.logger.debug(ex)
        return

    @classmethod
    def get_item_sort(cls, index_id):
        """
        :param index_id: search index id
        :return: sort list

        """
        item_custom_sort=db.session.query(Index.item_custom_sort).filter(Index.id == index_id).one()

        return item_custom_sort[0]

    @classmethod
    def have_children(cls, index_id):
        return Index.get_children(index_id)
