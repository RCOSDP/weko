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

"""Record models."""

import uuid
from datetime import datetime

from invenio_db import db
from sqlalchemy.dialects import mysql, postgresql
from sqlalchemy.sql.expression import desc
from sqlalchemy.types import LargeBinary
from sqlalchemy_utils.types import JSONType, UUIDType


class Timestamp(object):
    """Timestamp model mix-in with fractional seconds support.

    SQLAlchemy-Utils timestamp model does not have support for
    fractional seconds.
    """

    created = db.Column(
        db.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mysql'),
        default=datetime.utcnow,
        nullable=False
    )
    updated = db.Column(
        db.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mysql'),
        default=datetime.utcnow,
        nullable=False
    )


@db.event.listens_for(Timestamp, 'before_update', propagate=True)
def timestamp_before_update(mapper, connection, target):
    """Update `updated` property with current time on `before_update` event."""
    target.updated = datetime.utcnow()


class ItemType(db.Model, Timestamp):
    """Represent an item type.

    The ItemType object contains a ``created`` and  a ``updated``
    properties that are automatically updated.
    """

    # Enables SQLAlchemy-Continuum versioning
    __versioned__ = {}

    __tablename__ = 'item_type'

    id = db.Column(
        db.Integer(),
        primary_key=True,
        autoincrement=True
    )
    """Identifier of item type."""

    name_id = db.Column(
        db.Integer(),
        db.ForeignKey(
            'item_type_name.id',
            name='fk_item_type_name_id'
        ),
        nullable=False
    )
    """Name identifier of item type."""

    item_type_name = db.relationship(
        'ItemTypeName',
        backref=db.backref('item_type', lazy='dynamic',
                           order_by=desc('item_type.tag'))
    )
    """Name information from ItemTypeName class."""

    harvesting_type = db.Column(db.Boolean(name='harvesting_type'),
        nullable=False,
        default=False)

    schema = db.Column(
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
    """Store schema in JSON format. When you create a new ``item type`` the
    ``schema`` field value should never be ``NULL``. Default value is an
    empty dict. ``NULL`` value means that the record metadata has been
    deleted. """

    form = db.Column(
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
    """Store schema form in JSON format.
    When you create a new ``item type`` the ``form`` field value should never be
    ``NULL``. Default value is an empty dict. ``NULL`` value means that the
    record metadata has been deleted.
    """

    render = db.Column(
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
    """Store page render information in JSON format. When you create a new
    ``item type`` the ``render`` field value should never be ``NULL``.
    Default value is an empty dict. ``NULL`` value means that the record
    metadata has been deleted. """

    tag = db.Column(db.Integer, nullable=False)
    """Tag of item type."""

    version_id = db.Column(db.Integer, nullable=False)
    """Used by SQLAlchemy for optimistic concurrency control."""

    __mapper_args__ = {
        'version_id_col': version_id
    }


class ItemTypeName(db.Model, Timestamp):
    """Represent an item type name.

    The ItemTypeName object contains a ``created`` and  a ``updated``
    properties that are automatically updated.
    """

    __tablename__ = 'item_type_name'

    id = db.Column(
        db.Integer(),
        primary_key=True,
        autoincrement=True
    )
    """Name identifier of item type."""

    name = db.Column(
        db.Text,
        nullable=False,
        unique=True
    )
    """Name of item type."""

    has_site_license = db.Column(db.Boolean(name='has_site_license'),
                                 default=True, nullable=False)
    """site license identify."""


class ItemTypeMapping(db.Model, Timestamp):
    """Represent a record metadata.

    The ItemTypeMapping object contains a ``created`` and  a ``updated``
    properties that are automatically updated.
    """

    # Enables SQLAlchemy-Continuum versioning
    __versioned__ = {}

    __tablename__ = 'item_type_mapping'

    id = db.Column(
        db.Integer(),
        primary_key=True,
        autoincrement=True
    )
    """Record identifier."""

    item_type_id = db.Column(db.Integer)
    """ID of item type."""

    mapping = db.Column(
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
    """Store mapping in JSON format.
     When you create a new ``Record`` the ``mapping`` field value
     should never be ``NULL``. Default value is an empty dict.
     ``NULL`` value means that the record metadata has been deleted.
    """

    version_id = db.Column(db.Integer, nullable=False)
    """Used by SQLAlchemy for optimistic concurrency control."""

    __mapper_args__ = {
        'version_id_col': version_id
    }


class ItemMetadata(db.Model, Timestamp):
    """Represent a record metadata.

    The ItemMetadata object contains a ``created`` and  a ``updated``
    properties that are automatically updated.
    """

    # Enables SQLAlchemy-Continuum versioning
    __versioned__ = {}

    __tablename__ = 'item_metadata'

    id = db.Column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4,
    )
    """Item identifier."""

    item_type_id = db.Column(db.Integer())
    """ID of item type."""

    json = db.Column(
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
    """Store metadata in JSON format.

    When you create a new ``Record`` the ``json`` field value should never be
    ``NULL``. Default value is an empty dict. ``NULL`` value means that the
    record metadata has been deleted.
    """

    version_id = db.Column(db.Integer, nullable=False)
    """Used by SQLAlchemy for optimistic concurrency control."""

    __mapper_args__ = {
        'version_id_col': version_id
    }


class FileMetadata(db.Model, Timestamp):
    """Represent a record metadata.

    The FileMetadata object contains a ``created`` and  a ``updated``
    properties that are automatically updated.
    """

    # Enables SQLAlchemy-Continuum versioning
    __versioned__ = {}

    __tablename__ = 'file_metadata'

    id = db.Column(
        db.Integer(),
        autoincrement=True,
        primary_key=True
    )

    pid = db.Column(
        db.Integer()
    )
    """Record identifier."""

    # uid = db.Column(
    #     UUIDType,
    #     default=uuid.uuid4
    # )

    contents = db.Column(
        LargeBinary,
        nullable=True
    )

    json = db.Column(
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
    """Store metadata in JSON format.

    When you create a new ``Record`` the ``json`` field value should never be
    ``NULL``. Default value is an empty dict. ``NULL`` value means that the
    record metadata has been deleted.
    """

    version_id = db.Column(db.Integer, nullable=False)
    """Used by SQLAlchemy for optimistic concurrency control."""

    __mapper_args__ = {
        'version_id_col': version_id
    }


class ItemTypeProperty(db.Model, Timestamp):
    """Represent an itemtype property.

    The ItemTypeProperty object contains a ``created`` and  a
    ``updated`` properties that are automatically updated.
    """

    __tablename__ = 'item_type_property'

    id = db.Column(
        db.Integer(),
        primary_key=True,
        autoincrement=True
    )
    """Identifier of itemtype property."""

    name = db.Column(
        db.Text,
        nullable=False,
        unique=True
    )
    """Name identifier of itemtype property."""

    schema = db.Column(
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
    """Store schema in JSON format. When you create a new
    ``ItemTypeProperty`` the ``schema`` field value should never be ``NULL``.
    Default value is an empty dict. ``NULL`` value means that the record
    metadata has been deleted. """

    form = db.Column(
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
    """Store schema form (single) in JSON format. When you create a new
    ``ItemTypeProperty`` the ``form`` field value should never be ``NULL``.
    Default value is an empty dict. ``NULL`` value means that the record
    metadata has been deleted. """

    forms = db.Column(
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
    """Store schema form (array) in JSON format. When you create a new
    ``ItemTypeProperty`` the ``forms`` field value should never be ``NULL``.
    Default value is an empty dict. ``NULL`` value means that the record
    metadata has been deleted. """

    delflg = db.Column(db.Boolean(name='delFlg'),
                       default=False, nullable=False)
    """record delete flag"""

    sort = db.Column(db.Integer, nullable=True, unique=True)
    """Sort number of itemtype property."""

class SiteLicenseInfo(db.Model, Timestamp):
    """Represent a SiteLicenseInfo data.

    The SiteLicenseInfo object contains a ``created`` and  a ``updated``
    properties that are automatically updated.
    """
    __tablename__ = 'sitelicense_info'

    organization_id = db.Column(
        db.Integer(),
        primary_key=True,
        autoincrement=True
    )

    organization_name = db.Column(
        db.Text,
        nullable=False
    )

    domain_name = db.Column(
        db.Text,
        nullable=True
    )

    mail_address = db.Column(
        db.String(255),
        nullable=True
    )

    # Relationships definitions
    addresses = db.relationship(
        'SiteLicenseIpAddress', backref='SiteLicenseInfo')
    """Relationship to SiteLicenseIpAddress."""

    def __iter__(self):
        sl = {}
        for name in dir(SiteLicenseInfo):
            if not name.startswith('__') and not name.startswith('_'):
                value = getattr(self, name)
                if isinstance(value, list):
                    ip_lst = []
                    for lst in value:
                        if isinstance(lst, SiteLicenseIpAddress):
                            ip_lst.append(dict(lst))
                    yield (name, ip_lst)
                elif isinstance(value, str):
                    yield (name, value)


class SiteLicenseIpAddress(db.Model, Timestamp):
    """Represent a SiteLicenseIpAddress data.

    The SiteLicenseIpAddress object contains a ``created`` and  a
    ``updated`` properties that are automatically updated.
    """
    __tablename__ = 'sitelicense_ip_address'

    organization_id = db.Column(
        db.Integer(),
        db.ForeignKey(SiteLicenseInfo.organization_id, ondelete='RESTRICT'),
        primary_key=True
    )

    organization_no = db.Column(
        db.Integer(),
        primary_key=True,
        autoincrement=True
    )

    start_ip_address = db.Column(
        db.String(16),
        nullable=False
    )

    finish_ip_address = db.Column(
        db.String(16),
        nullable=False
    )

    def __iter__(self):
        for name in dir(SiteLicenseIpAddress):
            if not name.startswith('__') and not name.startswith('_'):
                value = getattr(self, name)
                if isinstance(value, str):
                    yield (name, value)


__all__ = (
    'Timestamp',
    'ItemType',
    'ItemTypeName',
    'ItemTypeMapping',
    'ItemTypeProperty',
    'ItemMetadata',
    'FileMetadata',
    'SiteLicenseInfo',
    'SiteLicenseIpAddress',
)
