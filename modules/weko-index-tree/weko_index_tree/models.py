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

"""Models for weko-index-tree."""

from datetime import datetime

from flask import current_app
from invenio_db import db
from invenio_i18n.ext import current_i18n
from sqlalchemy.dialects import mysql, postgresql
from sqlalchemy_utils.types import JSONType
from weko_records.models import Timestamp

# from sqlalchemy_utils.types import UUIDType
# from invenio_records.models import RecordMetadata


class Index(db.Model, Timestamp):
    """
    Represent an index.

    The Index object contains a ``created`` and  a ``updated``
    properties that are automatically updated.
    """

    __tablename__ = 'index'

    __table_args__ = (
        db.UniqueConstraint('parent', 'position', name='uix_position'),
    )

    id = db.Column(db.BigInteger, primary_key=True, unique=True)
    """Identifier of the index."""

    parent = db.Column(db.BigInteger, nullable=False, default=0)
    """Parent Information of the index."""

    position = db.Column(db.Integer, nullable=False, default=0)
    """Children position of parent."""

    index_name = db.Column(db.Text, nullable=True, default='')
    """Name of the index."""

    index_name_english = db.Column(db.Text, nullable=False, default='')
    """English Name of the index."""

    index_link_name = db.Column(db.Text, nullable=True, default='')
    """Name of the index link."""

    index_link_name_english = db.Column(db.Text, nullable=False, default='')
    """English Name of the index link."""

    harvest_spec = db.Column(db.Text, nullable=True, default='')
    """Harvest Spec."""

    index_link_enabled = db.Column(
        db.Boolean(
            name='index_link_enabled'),
        nullable=False,
        default=False)
    """Index link enable flag."""

    comment = db.Column(db.Text, nullable=True, default='')
    """Comment of the index."""

    more_check = db.Column(db.Boolean(name='more_check'), nullable=False,
                           default=False)
    """More Status of the index."""

    display_no = db.Column(db.Integer, nullable=False, default=0)
    """Display number of the index."""

    harvest_public_state = db.Column(db.Boolean(name='harvest_public_state'),
                                     nullable=False, default=True)
    """Harvest public State of the index."""

    display_format = db.Column(db.Text, nullable=True, default='1')
    """The Format of Search Resault."""

    image_name = db.Column(db.Text, nullable=False, default='')
    """The Name of upload image."""

    public_state = db.Column(db.Boolean(name='public_state'), nullable=False,
                             default=False)
    """Public State of the index."""

    public_date = db.Column(
        db.DateTime().with_variant(mysql.DATETIME(fsp=6), "mysql"),
        nullable=True)
    """Public Date of the index."""

    recursive_public_state = db.Column(
        db.Boolean(name='recs_public_state'), nullable=True, default=False)
    """Recursive Public State of the index."""

    rss_status = db.Column(
        db.Boolean(name='rss_status'), nullable=True, default=False)
    """RSS Icon Status of the index."""

    coverpage_state = db.Column(
        db.Boolean(
            name='coverpage_state'),
        nullable=True,
        default=False)
    """PDF Cover Page State of the index."""

    recursive_coverpage_check = db.Column(
        db.Boolean(
            name='recursive_coverpage_check'),
        nullable=True,
        default=False)
    """Recursive PDF Cover Page State of the index."""

    browsing_role = db.Column(db.Text, nullable=True)
    """Browsing role of the index."""

    recursive_browsing_role = db.Column(
        db.Boolean(name='recs_browsing_role'), nullable=True, default=False)
    """Recursive Browsing Role of the index."""

    contribute_role = db.Column(db.Text, nullable=True)
    """Contribute Role of the index."""

    recursive_contribute_role = db.Column(
        db.Boolean(name='recs_contribute_role'), nullable=True, default=False)
    """Recursive Browsing Role of the index."""

    browsing_group = db.Column(db.Text, nullable=True)
    """Browsing Group of the index."""

    recursive_browsing_group = db.Column(
        db.Boolean(name='recs_browsing_group'), nullable=True, default=False)
    """Recursive Browsing Group of the index."""

    contribute_group = db.Column(db.Text, nullable=True)
    """Contribute Group of the index."""

    recursive_contribute_group = db.Column(
        db.Boolean(name='recs_contribute_group'), nullable=True, default=False)
    """Recursive Browsing Group of the index."""

    owner_user_id = db.Column(db.Integer, nullable=True, default=0)
    """Owner user id of the index."""

    # item_custom_sort = db.Column(db.Text, nullable=True, default='')

    item_custom_sort = db.Column(
        db.JSON().with_variant(
            postgresql.JSONB(none_as_null=True),
            'postgresql',
        ).with_variant(
            JSONType(),
            'sqlite',
        ).with_variant(
            JSONType(),
            'mysql',
        ),
        default=lambda: dict(),
        nullable=True
    )
    """The sort of item by custom setting"""

    biblio_flag = db.Column(db.Boolean(name='biblio_flag'),
                            nullable=True,
                            default=False)
    """Flag of Items' statistics of the index."""

    online_issn = db.Column(db.Text, nullable=True, default='')
    """Online ISSN of the index."""


    cnri = db.Column(db.Text, nullable=True)
    """cnri of the index."""

    index_url = db.Column(db.Text, nullable=True)
    """index_url Group of the index."""

    is_deleted = db.Column(
        db.Boolean(name='is_deleted'),
        nullable=False,
        default=False
    )
    """Delete status of the index."""

    def __iter__(self):
        """Iter."""
        for name in dir(Index):
            if not name.startswith('__') and not name.startswith('_') \
                    and name not in dir(Timestamp):
                value = getattr(self, name)
                if value is None:
                    value = ""
                if isinstance(value, str) or isinstance(value, bool) \
                        or isinstance(value, datetime) \
                        or isinstance(value, int):
                    yield (name, value)
    # format setting for community admin page

    def __str__(self):
        """Representation."""
        if current_i18n.language == 'ja' and self.index_name:
            return 'Index <id={}, name={}>'.format(
                self.id,
                self.index_name.replace(
                    "\n", r"<br\>").replace("&EMPTY&", ""))
        else:
            return 'Index <id={}, name={}>'.format(
                self.id,
                self.index_name_english.replace(
                    "\n", r"<br\>").replace("&EMPTY&", ""))

    @classmethod
    def have_children(cls, id, with_deleted=False):
        """Have Children."""
        children = cls.query.filter_by(parent=id)
        if not with_deleted:
            children = children.filter_by(is_deleted=False)
        children = children.all()
        return False if (children is None or len(children) == 0) else True

    @classmethod
    def get_all(cls, with_deleted=False):
        """Get all Indexes."""
        query = cls.query
        if not with_deleted:
            query = query.filter_by(is_deleted=False)
        query_result = query.all()
        result = []
        if query_result:
            for index in query_result:
                data = {
                    'id': index.id,
                    'index_name': index.index_name
                }
                result.append(data)
        return result if result else []

    @classmethod
    def get_index_by_id(cls, index, with_deleted=False):
        """Get all Indexes.

        Args:
            index (int): Identifier of the index.
            with_deleted (bool): If True, include deleted indexes.

        Returns:
            Index: The index model object if found, otherwise None.
        """
        query = cls.query.filter_by(id=index)
        if not with_deleted:
            query = query.filter_by(is_deleted=False)
        obj = query.one_or_none()
        return obj if isinstance(obj, cls) else None


class IndexStyle(db.Model, Timestamp):
    """Index style."""

    __tablename__ = 'index_style'

    id = db.Column(db.String(100), primary_key=True)
    """identifier for index style setting."""

    width = db.Column(db.Text, nullable=False, default='')
    """Index area width."""

    height = db.Column(db.Text, nullable=False, default='')
    """Index area height."""

    index_link_enabled = db.Column(db.Boolean(name='index_link_enabled'),
                                   nullable=False, default=False)

    @classmethod
    def create(cls, community_id, **data):
        """Create."""
        try:
            with db.session.begin_nested():
                obj = cls(id=community_id, **data)
                db.session.add(obj)
            db.session.commit()
            return obj
        except Exception as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
        return

    @classmethod
    def get(cls, community_id):
        """Get a style."""
        return cls.query.filter_by(id=community_id).one_or_none()

    @classmethod
    def update(cls, community_id, **data):
        """
        Update the index detail info.

        :param index_id: Identifier of the index.
        :param detail: new index info for update.
        :return: Updated index info
        """
        try:
            with db.session.begin_nested():
                style = cls.get(community_id)
                if not style:
                    return

                for k, v in data.items():
                    if "width" in k or "height" in k:
                        setattr(style, k, v)
                db.session.merge(style)
            db.session.commit()
            return style
        except Exception as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
        return


__all__ = ('Index',
           'IndexStyle',)
