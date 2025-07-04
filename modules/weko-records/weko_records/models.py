# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Records is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Record models."""

import uuid
from datetime import datetime

from invenio_accounts.models import User
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
    When you create a new ``item type`` the ``form`` field value should never
    be ``NULL``. Default value is an empty dict. ``NULL`` value means that the
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

    edit_notes = db.relationship('ItemTypeEditHistory',
                                 order_by='ItemTypeEditHistory.created',
                                 backref='item_type')
    """Used to reference whole edit history."""

    is_deleted = db.Column(
        db.Boolean(name='deleted'),
        nullable=False,
        default=False
    )
    """Status of item type."""

    __mapper_args__ = {
        'version_id_col': version_id
    }

    @property
    def latest_edit_history(self):
        """Get latest edit note of self."""
        return self.edit_notes[-1].notes if self.edit_notes else {}


class ItemTypeEditHistory(db.Model, Timestamp):
    """Represent an item type edit history.

    The ItemTypeEditHistory object contains a ``created`` and  a ``updated``
    properties that are automatically updated.
    """

    __tablename__ = 'item_type_edit_history'

    id = db.Column(
        db.Integer(),
        primary_key=True,
        autoincrement=True
    )
    """Identifier of item type edit history."""

    item_type_id = db.Column(
        db.Integer(),
        db.ForeignKey(ItemType.id),
        nullable=False
    )
    """Identifier for item type."""

    user_id = db.Column(
        db.Integer(),
        db.ForeignKey(User.id),
        nullable=False
    )
    """Identifier for author of item type."""

    notes = db.Column(
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
    """Edit notes for item type."""

    @classmethod
    def get_latest_by_item_type_id(cls, item_type_id=0):
        """Get latest notes for item type."""
        pass


class ItemTypeName(db.Model, Timestamp):
    """Represent an item type name.

    The ItemTypeName object contains a ``created`` and  a ``updated``
    properties that are automatically updated.
    """

    __tablename__ = 'item_type_name'

    __table_args__ = (
        db.Index('uq_item_type_name_name', 'name',
                 unique=True,
                 postgresql_where=db.Column('is_active')
                 ),
    )

    id = db.Column(
        db.Integer(),
        primary_key=True,
        autoincrement=True
    )
    """Name identifier of item type."""

    name = db.Column(
        db.Text,
        nullable=False
    )
    """Name of item type."""

    has_site_license = db.Column(db.Boolean(name='has_site_license'),
                                 default=True, nullable=False)
    """site license identify."""

    is_active = db.Column(
        db.Boolean(name='active'),
        nullable=False,
        default=True
    )
    """Status of item type."""


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


class ItemTypeJsonldMapping(db.Model, Timestamp):
    """Jsonld Mapping Model

    Mapping for JSON-LD matadata to WEKO item type. <br>
    When updating the mapping, the verion_id is incremented and the previous
    mapping moves to the history table.

    Operation methods are defined in api.py.

    Attributes:
        id (int): ID of the mapping. Primary key, autoincrement.
        name (str): Name of the mapping.
        mapping (dict): Mapping in JSON format.
        item_type_id (str): Target itemtype of the mapping.
            Foreign key referencing `ItemType.id`.
        item_type (ItemType): Relationship to the ItemType.
        version_id (int): Version ID of the mapping.
        is_deleted (bool): Sofr-delete status of the mapping.
    """

    # Enables SQLAlchemy-Continuum versioning
    __versioned__ = {}

    __tablename__ = 'jsonld_mappings'

    id = db.Column(
        db.Integer,
        primary_key=True,
        unique=True,
        autoincrement=True
    )
    """int: ID of the mapping."""

    name = db.Column(db.String(255), nullable=False)
    """str: Name of the mapping."""

    mapping = db.Column(
        db.JSON().with_variant(
            postgresql.JSONB(none_as_null=False),
            'postgresql',
        ).with_variant(
            JSONType(),
            'sqlite',
        ).with_variant(
            JSONType(),
            'mysql',
        ),
        default=lambda: {},
        nullable=False
    )
    """dict: Mapping in JSON format. Foreign key from ItemType."""

    item_type_id = db.Column(
        db.Integer(),
        db.ForeignKey(ItemType.id),
        nullable=False,
        index=True
    )
    """int: Target itemtype of the mapping."""

    item_type = db.relationship(
        'ItemType',
        backref=db.backref('jsonld_mappings', lazy='dynamic'),
        foreign_keys=[item_type_id]
    )
    """Relationship to the ItemType."""

    version_id = db.Column(db.Integer, nullable=False)
    """int: Version id of the mapping."""

    is_deleted = db.Column(
        db.Boolean(name='is_deleted'),
        nullable=False,
        default=False)
    """bool: Sofr-delete status of the mapping."""

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

    receive_mail_flag = db.Column(
        db.String(1),
        default='F',
        nullable=False
    )

    repository_id = db.Column(
        db.String(100),
        nullable=False,
        default='Root Index'
    )

    # Relationships definitions
    addresses = db.relationship(
        'SiteLicenseIpAddress', backref='SiteLicenseInfo')
    """Relationship to SiteLicenseIpAddress."""

    def __iter__(self):
        """TODO: __iter__."""
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
        primary_key=True
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
        """TODO: __iter__."""
        for name in dir(SiteLicenseIpAddress):
            if not name.startswith('__') and not name.startswith('_'):
                value = getattr(self, name)
                if isinstance(value, str):
                    yield (name, value)


class FeedbackMailList(db.Model, Timestamp):
    """Represent an feedback mail list.

    Stored table stored list email address base on item_id
    """

    __tablename__ = 'feedback_mail_list'

    id = db.Column(
        db.Integer(),
        primary_key=True,
        autoincrement=True
    )
    """Feedback mail list identifier."""

    item_id = db.Column(
        UUIDType,
        nullable=False,
        default=uuid.uuid4,
    )
    """Item identifier."""

    mail_list = db.Column(
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
    """List of feedback mail in json format."""
    account_author = db.Column(
        db.Text,
        nullable=False,
        default=''
    )
    """Author identifier."""

    repository_id = db.Column(
        db.String(100),
        nullable=False,
        default='Root Index'
    )

class RequestMailList(db.Model, Timestamp):
    """Represent an request mail list.

    Stored table stored list email address base on item_id
    """

    __tablename__ = 'request_mail_list'

    id = db.Column(
        db.Integer(),
        primary_key=True,
        autoincrement=True
    )

    """Request mail list identifier."""

    item_id = db.Column(
        UUIDType,
        nullable=False,
        default=uuid.uuid4,
    )
    """Item identifier."""

    mail_list = db.Column(
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
    """List of request mail in json format."""


class ItemReference(db.Model, Timestamp):
    """Model of item reference relations."""

    __tablename__ = 'item_reference'

    src_item_pid = db.Column(
        db.String(255),
        nullable=False,
        primary_key=True
    )
    """PID of source item."""

    dst_item_pid = db.Column(
        db.String(255),
        nullable=False,
        primary_key=True
    )
    """PID for destination item."""

    reference_type = db.Column(
        db.String(50),
        nullable=False
    )
    """参照元と参照先のアイテム間の関連内容。"""

    def __repr__(self):
        """Text representation of a ItemReference relation."""
        return "<ItemReference Relation: (records/{r.src_item_pid}) -> " \
               "(records/{r.dst_item_pid}) " \
               "(Type: {r.reference_type})>".format(r=self)

    @classmethod
    def get_src_references(cls, pid):
        """Get all relations where given PID is a src."""
        return cls.query.filter(cls.src_item_pid == pid)

    @classmethod
    def get_dst_references(cls, pid):
        """Get all relations where given PID is a dst."""
        return cls.query.filter(cls.dst_item_pid == pid)

    @classmethod
    def relation_exists(cls, src_pid, dst_pid, reference_type):
        """Determine if given relation already exists."""
        return ItemReference.query.filter_by(
            src_item_pid=src_pid,
            dst_item_pid=dst_pid,
            reference_type=reference_type).count() > 0

class OaStatus(db.Model, Timestamp):
    """Model of OA status."""

    __tablename__ = 'oa_status'

    oa_article_id = db.Column(
        db.Integer(),
        primary_key=True
    )
    """article identifier in OA asist."""

    oa_status = db.Column(
        db.Text,
        nullable=True
    )
    """OA status."""

    weko_item_pid = db.Column(
        db.String(255),
        nullable=True
    )
    """WEKO item PID."""

    @classmethod
    def get_oa_status(cls, oa_article_id):
        """Get OA status by article id."""
        return cls.query.filter(cls.oa_article_id == oa_article_id).first() if oa_article_id else None

    @classmethod
    def get_oa_status_by_weko_item_pid(cls, weko_item_pid):
        """Get OA status by weko item pid."""
        return cls.query.filter(cls.weko_item_pid == weko_item_pid).first() if weko_item_pid else None


__all__ = (
    'Timestamp',
    'ItemType',
    'ItemTypeEditHistory',
    'ItemTypeName',
    'ItemTypeMapping',
    'ItemTypeProperty',
    'ItemMetadata',
    'FileMetadata',
    'SiteLicenseInfo',
    'SiteLicenseIpAddress',
    'FeedbackMailList',
    'ItemReference',
    'OaStatus',
)
