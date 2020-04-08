# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Schema models."""

import uuid
from collections import OrderedDict

from invenio_db import db
from invenio_records.models import Timestamp
from sqlalchemy.dialects import postgresql
from sqlalchemy_utils.types import JSONType, UUIDType


class OAIServerSchema(db.Model, Timestamp):
    """Represent a OAIServer Schema.

    The OAIServer object contains a ``created`` and  a ``updated``
    properties that are automatically updated.
    """

    # Enables SQLAlchemy-Continuum versioning
    __versioned__ = {}

    __tablename__ = 'oaiserver_schema'

    id = db.Column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4,
    )
    """schema identifier."""

    schema_name = db.Column(
        db.String(255),
        nullable=False,
        unique=True
    )
    """Mapping Name of schema"""

    form_data = db.Column(
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
    """Data(schema name,root name,description) of form."""

    xsd = db.Column(
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
        default=lambda: OrderedDict(),
        nullable=False
    )
    """Xsd schema"""

    namespaces = db.Column(
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
    """NameSpace for xml"""

    schema_location = db.Column(
        db.String(255)
    )
    """Schema Url"""

    isvalid = db.Column(
        db.Boolean(name='isvalid'),
        nullable=False,
        default=lambda: False
    )

    is_mapping = db.Column(
        db.Boolean(name='is_mapping'),
        nullable=False,
        default=lambda: False
    )

    isfixed = db.Column(
        db.Boolean(name='isfixed'),
        nullable=False,
        default=lambda: False
    )

    version_id = db.Column(db.Integer, nullable=False)
    """Used by SQLAlchemy for optimistic concurrency control."""

    target_namespace = db.Column(db.String(255), default='')

    __mapper_args__ = {
        'version_id_col': version_id
    }


__all__ = (
    'OAIServerSchema',
)
