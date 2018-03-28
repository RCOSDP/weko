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

from invenio_db import db
from sqlalchemy.dialects import mysql, postgresql
from sqlalchemy.inspection import inspect
from sqlalchemy_utils.types import JSONType


class Timestamp(object):
    """Timestamp model mix-in with fractional seconds support.

    SQLAlchemy-Utils timestamp model does not have support for fractional
    seconds.
    """

    created = db.Column(
        db.DateTime().with_variant(mysql.DATETIME(fsp=6), "mysql"),
        default=datetime.utcnow,
        nullable=False
    )
    updated = db.Column(
        db.DateTime().with_variant(mysql.DATETIME(fsp=6), "mysql"),
        default=datetime.utcnow,
        nullable=False
    )


@db.event.listens_for(Timestamp, 'before_update', propagate=True)
def timestamp_before_update(mapper, connection, target):
    """
    Update `updated` property with current time on `before_update` event.

    :param mapper;
    :param connection:
    :param target:
    """
    target.updated = datetime.utcnow()


class IndexTree(db.Model, Timestamp):
    """Represent an index tree structure.

    The IndexTree object contains a ``created`` and  a ``updated``
    properties that are automatically updated.
    """

    __tablename__ = 'index_tree'

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )
    """Identifier of the index tree."""

    tree = db.Column(
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
    """Store the index tree structure in JSON format."""


class Serializer(object):
    """
    Serializer for JSON serializable

    """

    def serialize(self):
        """
        Get all props for a model

        :return: the dict of props
        """
        return {c: getattr(self, c) for c in inspect(self).attrs.keys()}

    @staticmethod
    def serialize_list(l):
        """
        Get all props for inputted model.

        :param l: the list of object
        :return: the dict of props
        """
        return [m.serialize() for m in l]


class Index(db.Model, Timestamp, Serializer):
    """
    Represent an index.

    The Index object contains a ``created`` and  a ``updated``
    properties that are automatically updated.
    """

    __tablename__ = 'index'

    id = db.Column(db.BigInteger, primary_key=True, unique=True)
    """Identifier of the index."""

    parent = db.Column(db.BigInteger, nullable=False, default=0)
    """Parent Information of the index."""

    children = db.Column(db.Text, nullable=False, default='')
    """Children Information of the index."""

    index_name = db.Column(db.Text, nullable=False, default='')
    """Name of the index."""

    index_name_english = db.Column(db.Text, nullable=False, default='')
    """English Name of the index."""

    comment = db.Column(db.Text, nullable=True, default='')
    """Comment of the index."""

    contents = db.Column(db.Integer, nullable=True, default=0)
    """Contents of the index."""

    private_contents = db.Column(db.Integer, nullable=True, default=0)
    """Private Contents of the index."""

    public_state = db.Column(db.Boolean(name='public_state'), nullable=True,
                             default=False)
    """Public State of the index."""

    public_date = db.Column(
        db.DateTime().with_variant(mysql.DATETIME(fsp=6), "mysql"),
        nullable=True)
    """Public Date of the index."""

    recursive_public_state = db.Column(
        db.Boolean(name='pubdate_recursive'), nullable=True, default=False)
    """Recursive Public State of the index."""

    rss_display = db.Column(db.Boolean(name='rss_display'), nullable=True,
                            default=False)
    """RSS Display of the index."""

    create_cover_flag = db.Column(db.Boolean(name='create_cover_flag'),
                                  nullable=True, default=False)
    """Create pdf cover flag of the index."""

    create_cover_recursive = db.Column(
        db.Boolean(name='create_cover_recursive'),
        nullable=True, default=False)
    """Create pdf recursive cover flag of the index."""

    harvest_public_state = db.Column(db.Boolean(name='harvest_public_state'),
                                     nullable=True, default=False)
    """Harvest public state of the index."""

    online_issn = db.Column(db.Text, nullable=True, default='')
    """Online issn of the index."""

    biblio_flag = db.Column(db.Boolean(name='biblioFlag'), nullable=True,
                            default=False)
    """Biblio flag of the index."""

    display_type = db.Column(db.Integer, nullable=True, default=0)
    """Display Type of the index."""

    select_index_list_display = db.Column(
        db.Boolean(name='select_index_list_display'), nullable=True,
        default=False)
    """Select Index List Display of the index."""

    select_index_list_name = db.Column(db.Text, nullable=True, default='')
    """Select Index List Name of the index."""

    select_index_list_name_english = db.Column(db.Text, nullable=True,
                                               default='')
    """Select Index List Name of the index."""

    exclusive_acl_role = db.Column(db.Text, nullable=True, default='')
    """Exclusive Acl Role of the index."""

    acl_role = db.Column(db.Text, nullable=True, default='')
    """Acl Role of the index."""

    exclusive_acl_room_auth = db.Column(db.Text, nullable=True, default='')
    """Exclusive Acl Room Auth of the index."""

    exclusive_acl_group = db.Column(db.Text, nullable=True, default='')
    """Exclusive Acl Group of the index."""

    acl_group = db.Column(db.Text, nullable=True, default='')
    """Acl Group of the index."""

    exclusive_access_role = db.Column(
        db.Text, nullable=True, default='')
    """Exclusive Access Role of the index."""

    access_role = db.Column(db.Text, nullable=True, default='')
    """Access Role of the index."""

    aclRoleIds_recursive = db.Column(db.Boolean(name='aclRoleIds'),
                                     nullable=True, default=False)
    """aclRoleIds of the index."""

    exclusive_tree_room_auth = db.Column(db.Text, nullable=True, default='')
    """Exclusive Tree Room Auth of the index."""

    aclRoomAuth_recursive = db.Column(db.Boolean(name='aclRoomAuth'),
                                      nullable=True, default=False)
    """Acl RoomAuth of the index."""

    exclusive_access_group = db.Column(db.Text, nullable=True, default='')
    """Exclusive Access Group of the index."""

    access_group = db.Column(db.Text, nullable=True, default='')
    """Access Group of the index."""

    aclGroupIds_recursive = db.Column(db.Boolean(name='aclGroupIds'),
                                      nullable=True, default=False)
    """Acl GroupIds of the index."""

    opensearch_uri = db.Column(db.Text, nullable=True, default='')
    """Open Search URI of the index."""

    thumbnail = db.Column(db.LargeBinary, nullable=True)
    """Thumbnail of the index."""

    thumbnail_name = db.Column(db.Text, nullable=True, default='')
    """Thumbnail Name of the index."""

    thumbnail_mime_type = db.Column(db.Text, nullable=True, default='')
    """Thumbnail MIME Type of the index."""

    owner_user_id = db.Column(db.Integer, nullable=True, default=0)
    """Owner user id of the index."""

    ins_user_id = db.Column(db.Integer, nullable=True, default=0)
    """Insert user id of the index."""

    mod_user_id = db.Column(db.Integer, nullable=True, default=0)
    """Modify user id of the index."""

    del_user_id = db.Column(db.Integer, nullable=True, default=0)
    """Delete user id of the index."""

    ins_date = db.Column(
        db.DateTime().with_variant(mysql.DATETIME(fsp=6), "mysql"),
        nullable=True, default=datetime.utcnow)
    """Insert date of the index."""

    mod_date = db.Column(
        db.DateTime().with_variant(mysql.DATETIME(fsp=6), "mysql"),
        nullable=True)
    """Modify date of the index."""

    del_date = db.Column(
        db.DateTime().with_variant(mysql.DATETIME(fsp=6), "mysql"),
        nullable=True)
    """Delete date of the index."""

    is_delete = db.Column(db.Boolean(name='delete_flag'), nullable=True,
                          default=False)
    """Delete flag of the index."""

    def serialize(self):
        """
        Serialize the object.

        :return: The dict of object.
        """
        obj = Serializer.serialize(self)
        del obj['is_delete']
        del obj['del_date']
        del obj['mod_date']
        del obj['ins_date']
        del obj['del_user_id']
        del obj['ins_user_id']
        del obj['owner_user_id']
        del obj['updated']
        del obj['created']
        del obj['thumbnail']
        return obj
