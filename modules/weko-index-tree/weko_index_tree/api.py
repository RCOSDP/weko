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
        :returns: The :class:`IndexTree` instance.
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
        """Update the index tree structure. Create if not exists.

        :param indexes: the index tree structure in JSON format.
        :returns: The :class:`IndexTree` instance.
        """
        cls.delete_all()
        index_list = []
        current_app.logger.debug(indexes)
        current_app.logger.debug(indexes[0])
        for i in indexes:
            current_app.logger.debug(i)
            current_app.logger.debug(i['id'])
        try:
            with db.session.begin_nested():
                for i in indexes:
                    index_list.append(Index(id=i['id'], parent=i['parent'],
                                            children=i['children']))
                    # db.session.add(Index(id=i['id'], parent=i['parent'],children=i['children']))
                    current_app.logger.debug(i)
                current_app.logger.debug(index_list)
                db.session.add_all(index_list)
            db.session.commit()
        except Exception as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
            current_app.logger.debug(index_list)
            return None
        return index_list

    @classmethod
    def delete_all(cls):
        """Delete all rows of indexes."""
        # # with db.session.no_autoflush:
        # #     indexes = Index.query.all()
        # # current_app.logger.debug(len(indexes))
        # if len(indexes) > 0:
        with db.session.begin_nested():
            # db.session.qdelete_all(indexes)
            Index.query.delete()
        # db.session.commit()
