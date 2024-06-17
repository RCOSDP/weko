# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2020 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Record models."""

import uuid
from copy import deepcopy
from datetime import datetime

from invenio_db import db
from sqlalchemy.dialects import mysql, postgresql
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy_utils.types import JSONType, UUIDType


class Timestamp(object):
    """Timestamp model mix-in with fractional seconds support.

    SQLAlchemy-Utils timestamp model does not have support for fractional
    seconds.
    """

    created = db.Column(
        db.DateTime().with_variant(mysql.DATETIME(fsp=6), "mysql"),
        default=datetime.utcnow,
        nullable=False,
    )
    updated = db.Column(
        db.DateTime().with_variant(mysql.DATETIME(fsp=6), "mysql"),
        default=datetime.utcnow,
        nullable=False,
    )


@db.event.listens_for(Timestamp, "before_update", propagate=True)
def timestamp_before_update(mapper, connection, target):
    """Update `updated` property with current time on `before_update` event."""
    target.updated = datetime.utcnow()


class RecordMetadataBase(Timestamp):
    """Represent a base class for record metadata.

    The RecordMetadata object contains a ``created`` and  a ``updated``
    properties that are automatically updated.
    """

    encoder = None
    """"Class-level attribute to set a JSON data encoder/decoder.

    This allows customizing you to e.g. convert specific entries to complex
    Python objects. For instance you could convert ISO-formatted datetime
    objects into Python datetime objects.
    """

    id = db.Column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4,
    )
    """Record identifier."""

    json = db.Column(
        db.JSON()
        .with_variant(
            postgresql.JSONB(none_as_null=True),
            "postgresql",
        )
        .with_variant(
            JSONType(),
            "sqlite",
        )
        .with_variant(
            JSONType(),
            "mysql",
        ),
        default=lambda: dict(),
        nullable=True,
    )
    """Store metadata in JSON format.

    When you create a new ``Record`` the ``json`` field value should never be
    ``NULL``. Default value is an empty dict. ``NULL`` value means that the
    record metadata has been deleted.
    """

    # Enables SQLAlchemy version counter (not the same as SQLAlchemy-Continuum)
    version_id = db.Column(db.Integer, nullable=False)
    """Used by SQLAlchemy for optimistic concurrency control."""

    __mapper_args__ = {"version_id_col": version_id}

    def __init__(self, data=None, **kwargs):
        """Initialize the model specifically by setting the."""
        if data is not None:
            self.data = data
        super(RecordMetadataBase, self).__init__(self, **kwargs)

    @hybrid_property
    def is_deleted(self):
        """Boolean flag to determine if a record is soft deleted."""
        return self.json == None  # noqa

    @is_deleted.setter
    def is_deleted(self, value):
        """Boolean flag to set record as soft deleted.

        This propert sets the JSON colum to None. The hybrid property *cannot*
        be used to undelete a record by setting the property to False.
        """
        if value is True:
            self.json = None
        else:
            self.json = {}

    @property
    def data(self):
        """Get data by decoding the JSON.

        This allows a subclass to override
        """
        # We make a deepcopy in order to completely disconnect updates on the
        # record dict from the model's JSON. Otherwise changes made by the
        # encoder/decode, and updates by users are propagated to the model's
        # json field (circumventing the encoder) and likely causing the JSON
        # serialization errors when saving to the DB.
        return self.decode(self.json)

    @data.setter
    def data(self, value):
        """Set data by encoding the JSON.

        This allows a subclass to override
        """
        self.json = self.encode(value)
        flag_modified(self, "json")

    @classmethod
    def encode(cls, value):
        """Encode a JSON document."""
        data = deepcopy(value)
        return cls.encoder.encode(data) if cls.encoder else data

    @classmethod
    def decode(cls, json):
        """Decode a JSON document."""
        data = deepcopy(json)
        return cls.encoder.decode(data) if cls.encoder else data


class RecordMetadata(db.Model, RecordMetadataBase):
    """Represent a record metadata."""

    __tablename__ = "records_metadata"

    # Enables SQLAlchemy-Continuum versioning
    __versioned__ = {}


__all__ = (
    "RecordMetadata",
    "RecordMetadataBase",
)
