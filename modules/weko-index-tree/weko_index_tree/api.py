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

import re
from datetime import datetime

from flask import current_app
from flask_login import current_user
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import literal_column, func

from .models import Index, IndexTree


class IndexTrees(object):
    """Define API for index tree creation and update."""

    @classmethod
    def update(cls, tree=None):
        """
        Update the index tree structure. Create if not exists.

        :param tree: the index tree structure in JSON format.
        :returns: The :class:`IndexTree` instance or None.
        """
        assert tree
        index_tree = cls.get()
        try:
            with db.session.begin_nested():
                if index_tree is None:
                    # create
                    index_tree = IndexTree(tree=tree)
                    db.session.add(index_tree)
                else:
                    # update
                    index_tree.tree = tree
            db.session.commit()
        except Exception:
            db.session.rollback()
            return None
        return index_tree

    @classmethod
    def get(cls):
        """Get the index tree structure.

        :returns: The :class:`IndexTree` instance or None.
        """
        with db.session.no_autoflush:
            return IndexTree.query.one_or_none()


class Indexes(object):
    """Define API for index tree creation and update."""

    @classmethod
    def create(cls, indexes=[]):
        """
        Create the indexes. Delete all indexes before creation.

        :param indexes: the index information.
        :returns: The :class:`Index` instance lists or None.
        """
        cls.delete_all()
        index_list = []
        try:
            with db.session.begin_nested():
                for i in indexes:
                    index = Index.query.filter_by(id=i['id']).first()
                    if index is not None:
                        index.parent = i['parent']
                        index.children = i['children']
                        index.is_delete = False
                        db.session.merge(index)
                    else:
                        index_list.append(
                            Index(id=i['id'],
                                  parent=i['parent'],
                                  children=i['children'],
                                  owner_user_id=current_user.get_id(),
                                  ins_user_id=current_user.get_id(),
                                  ins_date=datetime.utcnow()))
                if len(index_list) > 0:
                    db.session.add_all(index_list)
            db.session.commit()
        except Exception as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
            return None
        return index_list

    @classmethod
    def delete_all(cls):
        """Delete all indexes."""

        Index.query.update({'is_delete': True})

    @classmethod
    def get_all_descendants(cls, parent_id):
        """
        Get all descendants of indexes.

        :param parent_id: Identifier of the parent index.
        :returns: Type of dictionary.
            Format: {'child1':['child1', 'grandson1', ...],
                    'child2':['child2', 'grandson2', ...],
                    ...}
        """
        result = {}
        with db.session.no_autoflush:
            indexes = Index.query.filter_by(parent=parent_id)
        for i in indexes:
            if i.children is '':
                result[i.id] = [i.id]
            else:
                result[i.id] = [i.id] + i.children.split(',')
        current_app.logger.debug(result)
        return result

    @classmethod
    def get_detail_by_id(cls, index_id):
        """
        Get detail info of index by index_id.

        :param index_id: Identifier of the index.
        :return: Type of Index.
        """
        index = Index.query.filter_by(id=index_id, is_delete=False).first()
        return index

    @classmethod
    def upt_detail_by_id(cls, index_id, **detail):
        """
        Update the index detail info.

        :param index_id: Identifier of the index.
        :param detail: new index info for update.
        :return: Updated index info
        """
        try:
            with db.session.begin_nested():
                index = Index.query.filter_by(id=index_id).first()
                if index is None:
                    return None
                for k in detail.keys():
                    setattr(index, k, detail.get(k))
                index.mod_user_id = current_user.get_id()
                index.mod_date = datetime.utcnow()
                db.session.merge(index)
            db.session.commit()
        except Exception as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
            return None
        return index

    @classmethod
    def get_Thumbnail_by_id(cls, index_id):
        """
        Get the thumbnail of index by index id.

        :param index_id: Identifier of the index.
        :return: the binary data of thumbnail.
        """
        try:
            index = Index.query.filter_by(id=index_id).first()
        except Exception as ex:
            return None
        return index.thumbnail

    @classmethod
    def del_by_indexid(cls, index_id):
        """
        Delete the index by index id.

        :param index_id: Identifier of the index.
        :return: bool True: Delete success None: Delete failed
        """
        try:
            with db.session.begin_nested():
                index = Index.query.filter_by(id=index_id).first()
                if index is None:
                    return None
                index.is_delete = True
                index.del_date = datetime.utcnow()
                index.del_user_id = current_user.get_id()
                db.session.merge(index)
            db.session.commit()
        except Exception as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
            return None
        return True

    @classmethod
    def get_path_list(cls, node_lst):
        """
        Get index tree info.

        :param node_lst: Identifier list of the index.
        :return: the list of index.
        """
        recursive_t = cls.recu_query()
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
        recursive_t = cls.recu_query()
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
        recursive_t = cls.recu_query()
        q = db.session.query(recursive_t).filter(
            db.or_(recursive_t.c.pid == pid,
                   recursive_t.c.cid == pid)). \
            order_by(recursive_t.c.path).all()
        return q

    @classmethod
    def get_self_path(cls, node_id):
        """
        Get index view path info.

        :param node_id: Identifier of the index.
        :return: the type of Index.
        """
        recursive_t = cls.recu_query()
        return db.session.query(recursive_t).filter(
            recursive_t.c.cid == str(node_id)).one_or_none()

    @classmethod
    def recu_query(cls):
        """
        Init select condition of index.

        :return: the query of db.session.
        """
        recursive_t = db.session.query(
            Index.parent.label("pid"),
            Index.id.label("cid"),
            func.cast(Index.id, db.Text).label("path"),
            Index.index_name.label("name"),
            literal_column("1", db.Integer).label("lev")).filter(
            Index.parent == 0,
            Index.is_delete == False). \
            cte(name="recursive_t", recursive=True)

        rec_alias = aliased(recursive_t, name="rec")
        test_alias = aliased(Index, name="t")
        recursive_t = recursive_t.union_all(
            db.session.query(
                test_alias.parent,
                test_alias.id,
                rec_alias.c.path + '/' + func.cast(test_alias.id, db.Text),
                rec_alias.c.name + '/' + test_alias.index_name,
                rec_alias.c.lev + 1).filter(
                test_alias.parent == rec_alias.c.cid,
                test_alias.is_delete == False)
        )

        return recursive_t

    @classmethod
    def has_children(cls, parent_id):
        """
        Check if has children branch

        :param parent_id: Identifier of the index.
        :return: the count of the children branch
        """
        children_count = Index.query.filter_by(parent=parent_id).count()
        return children_count

    @classmethod
    def get_all_descendants_id(cls, parent_id):
        """
        Get all of descendants id for parent

        :param parent_id: Identifier of the index.
        :return: the id list of all descendant
        """
        descendant = Index.query.filter_by(id=parent_id).one_or_none()
        if descendant is None:
            return None
        return descendant.split(',')


class ItemRecord(RecordIndexer):
    @staticmethod
    def get_es_index():
        """
        Get the index and doc type of Elasticsearch.

        :return: index,doc_type.
        """
        index, doc_type = current_app.config['SEARCH_UI_SEARCH_INDEX'], \
                          current_app.config['INDEXER_DEFAULT_DOCTYPE']
        return index, doc_type

    def get_count_by_index_id(self, tree_path):
        """
        Get the count of item which belong to the index

        :param tree_path: Identifier of the index.
        :return: The count of item.
        """
        search_query = {
            "query": {
                "term": {
                    "path.tree": tree_path
                }
            }
        }
        index, doc_type = ItemRecord.get_es_index()
        search_result = self.client.count(index=index,
                                          doc_type=doc_type,
                                          body=search_query)
        return search_result.get('count')

    def del_items_by_index_id(self, index_id, with_children=False):
        """
        Delete item record for ES and DB by index_id.

        :param index_id: The index id for delete.
        :param with_children: True: delete the children of the index.
                               False: move the children to parent leaf.
        :return: The count of delete and update.
                  Format: count_del, count_upt.
        """
        count_del, count_upt = 0, 0
        search_query = {
            "query": {
                "wildcard": {
                    "path.tree": '*' + index_id + '*'
                }
            },
            "_source": "path"
        }
        index, doc_type = ItemRecord.get_es_index()
        search_result = self.client.search(index=index,
                                           doc_type=doc_type,
                                           body=search_query)
        search_records = search_result.get('hits')
        search_count = search_records.get('total')
        if search_count <= 0:
            return count_del, count_upt
        regx_match = '/' + index_id
        search_records = search_records.get('hits')
        for record in search_records:
            record_id = record.get('_id')
            record_path = record.get('_source').get('path')
            upt_tree = []
            for path in record_path:
                if not with_children:
                    # move descendants to forebear
                    upt_tree.append(re.sub(regx_match, '', path))
                else:
                    # delete all descendants
                    if re.search(regx_match, path) is None:
                        upt_tree.append(path)
            if len(upt_tree) == 0:
                self.delete_by_id(record_id)
                count_del += 1
            else:
                self.client.update(index=index,
                                   doc_type=doc_type,
                                   id=record_id,
                                   body={"doc": {"path": upt_tree}})
            count_upt += 1
        return count_del, count_upt
