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
    """Update `updated` property with current time on `before_update` event."""
    target.updated = datetime.utcnow()


class IndexTree(db.Model, Timestamp):
    """Represent an index tree structure.

    The IndexTree object contains a ``created`` and  a ``updated``
    properties that are automatically updated.
    """

    __tablename__ = 'index_tree'

    id = db.Column(
        db.Integer(),
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


class Index(db.Model, Timestamp):
    """Represent an index.

    The Index object contains a ``created`` and  a ``updated``
    properties that are automatically updated.
    """

    __tablename__ = 'index'

    id = db.Column(
        db.Text,
        primary_key=True,
        unique=True
    )
    """Identifier of the index."""

    parent = db.Column(
        db.Text,
        nullable=False,
        default=''
    )
    """Parent Information of the index."""

    children = db.Column(
        db.Text,
        nullable=False,
        default=''
    )
    """Children Information of the index."""
