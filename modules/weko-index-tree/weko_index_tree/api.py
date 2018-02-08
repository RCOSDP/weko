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

from invenio_db import db
from flask import current_app
from .models import Index, IndexTree


class IndexTrees(object):
    """Define API for index tree creation and update."""

    @classmethod
    def update(cls, tree=None):
        """Update the index tree structure. Create if not exists.

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
        """Create the indexes. Delete all indexes before creation.

        :param indexes: the index information.
        :returns: The :class:`Index` instance lists or None.
        """
        cls.delete_all()
        index_list = []
        try:
            with db.session.begin_nested():
                for i in indexes:
                    index_list.append(Index(id=i['id'], parent=i['parent'],
                                            children=i['children']))
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
        Index.query.delete()

    @classmethod
    def get_all_descendants(cls, parent_id):
        """Get all descendants of indexes.

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
