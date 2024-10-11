# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import enum

from invenio_db import db
from sqlalchemy.dialects import postgresql
from sqlalchemy_utils.types import JSONType

from invenio_oauth2server.models import Client
from weko_records.models import ItemType, Timestamp
from weko_workflow.models import WorkFlow

"""swordserver models."""

class SwordItemTypeMapping(db.Model, Timestamp):
    """SwordItemTypeMapping Model

    Mapping of RO-Crate matadata to WEKO item type.

    Columns:
        id (int): ID of the mapping.
        name (str): Name of the mapping.
        mapping (JSON): Mapping in JSON format.
        item_type (str): Target itemtype of the mapping.\
            Foreign key referencing `ItemType.id`.
        version_id (int): Version ID of the mapping.
        is_deleted (bool): Delete status of the mapping.
    """

    __tablename__ = 'sword_item_type_mappings'

    id = db.Column(db.Integer, primary_key=True, unique=True)
    """ID of the mapping."""

    name = db.Column(db.String(255), nullable=False)
    """Name of the mapping."""

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
        default=lambda: {},
        nullable=False
    )
    """Mapping in JSON format. Foreign key of ItemType."""

    item_type = db.Column(
        db.String(255),
        db.ForeignKey(ItemType.id),
        nullable=False)
    """Target itemtype of the mapping."""

    version_id = db.Column(db.Integer, primary_key=True)
    """Version id of the mapping."""

    is_deleted = db.Column(
        db.Boolean(name='is_deleted'),
        nullable=False,
        default=False)
    """Delete status of the mapping."""

    # __mapper_args__ = {
    #     'version_id_col': version_id
    # }


class SwordClient(db.Model, Timestamp):
    """SwordClient Model

    client whitch is register items through the sword api.

    Columns:
        `client_id` (str): ID of the client.\
            Foreign key referencing `Client.client_id`.
        `registration_type` (int): Type of registration to register an item.
        `mapping_id` (int): Mapping ID of the client.\
            Foreign key referencing `SwordItemTypeMapping.id`.
        `workflow_id` (int, optional): Workflow ID of the client.\
            Foreign key referencing `WorkFlow.id`.
        `is_deleted` (bool): Delete status of the client.

    Nested Classes:
        `RegistrationType` (enum.IntEnum): Enum class for registration type.
            - `Direct` (1): Direct registration.
            - `Workfolw` (2): Workflow registration.
    """

    class RegistrationType(enum.IntEnum):
        """Solution to register item."""

        Direct = 1
        Workfolw = 2

    __tablename__ = 'sword_clients'

    client_id = db.Column(
        db.String(255),
        db.ForeignKey(Client.client_id),
        primary_key=True,
        unique=True)
    """Id of the clients. foreign key of Client."""

    registration_type = db.Column(db.SmallInteger, unique=False, nullable=False)
    """Type of registration to register an item."""

    mapping_id = db.Column(
        db.Integer,
        db.ForeignKey(SwordItemTypeMapping.id),
        unique=False,
        nullable=False)
    """Mapping ID of the client. foreign key of SwordItemTypeMapping."""

    workflow_id = db.Column(
        db.Integer,
        db.ForeignKey(WorkFlow.id),
        unique=False,
        nullable=True)
    """Workflow ID of the client. foreign key of WorkFlow."""

    is_deleted = db.Column(
        db.Boolean(name='is_deleted'),
        nullable=False,
        default=False)
    """Delete status of the client."""

