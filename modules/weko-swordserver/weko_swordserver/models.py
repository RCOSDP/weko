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
from weko_records.models import ItemType, Timestamp, ItemTypeJsonldMapping
from weko_workflow.models import WorkFlow

"""Models of weko-swordserver."""


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
        db.ForeignKey(ItemTypeJsonldMapping.id),
        unique=False,
        nullable=False)
    """Mapping ID of the client. Foreign key from SwordItemTypeMapping."""

    workflow_id = db.Column(
        db.Integer,
        db.ForeignKey(WorkFlow.id),
        unique=False,
        nullable=True)
    """Workflow ID of the client. Foreign key from WorkFlow."""

    active = db.Column(
        db.Boolean,
        unique=False,
        nullable=True)

    meta_data_api = db.Column(
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

    @property
    def registration_type(self):
        """Registration type name of the client."""
        registration_type = ""

        if self.registration_type_id == self.RegistrationType.DIRECT:
            registration_type = "Direct"
        elif self.registration_type_id == self.RegistrationType.WORKFLOW:
            registration_type = "Workflow"

        return registration_type
