# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

from sqlalchemy.dialects import postgresql
from sqlalchemy_utils.types import JSONType

from invenio_db import db
from invenio_oauth2server.models import Client
from weko_records.models import ItemType, Timestamp
from weko_workflow.models import WorkFlow


"""Models of weko-swordserver."""

class SwordItemTypeMappingModel(db.Model, Timestamp):
    """SwordItemTypeMapping Model

    Mapping for RO-Crate matadata to WEKO item type.
    When updating the mapping, the verion_id is incremented and the previous
    mapping moves to the history table.

    Operation methods are defined in api.py.

    Columns:
        `id` (int): ID of the mapping. Primary key, autoincrement.
        `name` (str): Name of the mapping.
        `mapping` (JSON): Mapping in JSON format.
        `item_type_id` (str): Target itemtype of the mapping.\
            Foreign key referencing `ItemType.id`.
        `version_id` (int): Version ID of the mapping.
        `is_deleted` (bool): Sofr-delete status of the mapping.
    """

    # Enables SQLAlchemy-Continuum versioning
    __versioned__ = {}

    __tablename__ = 'sword_item_type_mappings'

    id = db.Column(
        db.Integer,
        primary_key=True,
        unique=True,
        autoincrement=True
    )
    """ID of the mapping."""

    name = db.Column(db.String(255), nullable=False)
    """Name of the mapping."""

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
    """Mapping in JSON format. Foreign key from ItemType."""

    item_type_id = db.Column(
        db.Integer(),
        db.ForeignKey(ItemType.id),
        nullable=False)
    """Target itemtype of the mapping."""

    version_id = db.Column(db.Integer, nullable=False)
    """Version id of the mapping."""

    is_deleted = db.Column(
        db.Boolean(name='is_deleted'),
        nullable=False,
        default=False)
    """Sofr-delete status of the mapping."""

    __mapper_args__ = {
        'version_id_col': version_id
    }


class SwordClientModel(db.Model, Timestamp):
    """SwordClient Model

    client whitch is register items through the sword api.

    Columns:
        `client_id` (str): ID of the client. Primary key.\
            Foreign key referencing `Client.client_id`.
        `registration_type_id` (int): Type of registration to register an item.
        `mapping_id` (int): Mapping ID of the client.\
            Foreign key referencing `SwordItemTypeMapping.id`.
        `workflow_id` (int, optional): Workflow ID of the client.\
            Foreign key referencing `WorkFlow.id`.

    Nested Classes:
        `RegistrationType` (enum.IntEnum): Enum class for registration type.
            - `Direct` (1): Direct registration.
            - `Workfolw` (2): Workflow registration.
    """

    class RegistrationType:
        """Solution to register item."""

        DIRECT = 1
        WORKFLOW = 2

    __tablename__ = 'sword_clients'
    # __table_args__ = (
    #     db.Index("idx_client_id", "client_id"),
    # )

    id = db.Column(
        db.Integer,
        primary_key=True,
        unique=True,
        autoincrement=True
    )
    """ID of the Sword Client Setting."""

    client_id = db.Column(
        db.String(255),
        db.ForeignKey(Client.client_id),
        unique=True,
        nullable=False
    )
    """Id of the clients. Foreign key from Client."""

    registration_type_id = db.Column(
        db.SmallInteger,
        unique=False,
        nullable=False
    )
    """Type of registration to register an item."""

    mapping_id = db.Column(
        db.Integer,
        db.ForeignKey(SwordItemTypeMappingModel.id),
        unique=False,
        nullable=False)
    """Mapping ID of the client. Foreign key from SwordItemTypeMapping."""

    workflow_id = db.Column(
        db.Integer,
        db.ForeignKey(WorkFlow.id),
        unique=False,
        nullable=True)
    """Workflow ID of the client. Foreign key from WorkFlow."""


    @property
    def registration_type(self):
        """Registration type name of the client."""
        registration_type = ""

        if self.registration_type_id == self.RegistrationType.DIRECT:
            registration_type = "Direct"
        elif self.registration_type_id == self.RegistrationType.WORKFLOW:
            registration_type = "Workflow"

        return registration_type
