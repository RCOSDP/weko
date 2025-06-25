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

    Attributes:
        id (int):
            ID of the Sword Client Setting. Primary key. Auto incremented.
        client_id (str):
            ID of the client. Primary key.
            Foreign key referencing `Client.client_id`.
        oauth_client (Client):
            Relationship to OAuth Client.
        active (bool):
            Active status of the application.
        registration_type_id (int):
            Type of registration to register an item.
        registration_type (str):
            Registration type name of the client.
            Can be either "Direct" or "Workflow".
        mapping_id (int):
            Mapping ID of the client.
            Foreign key referencing `ItemTypeJsonldMapping.id`.
        mapping (ItemTypeJsonldMapping):
            Relationship to ItemTypeJsonldMapping.
        workflow_id (int, optional): Workflow ID of the client.\
            Foreign key referencing `WorkFlow.id`.
        workflow (WorkFlow):
            Relationship to WorkFlow.
            This is optional and can be null if no workflow is associated.
        duplicate_check (bool):
            Duplicate check status of the application.
        meta_data_api (list):
            Priority of use for metadata collection web API.
    """

    class RegistrationType:
        """Solution to register item.

        Attributes:
            DIRECT (int): Direct registration; 1.
            WORKFLOW (int): Workflow registration; 2.
        """

        DIRECT = 1
        WORKFLOW = 2

    __tablename__ = 'sword_clients'

    id = db.Column(
        db.Integer,
        primary_key=True,
        unique=True,
        autoincrement=True
    )
    """int: ID of the Sword Client Setting. Primary key. Auto incremented."""

    client_id = db.Column(
        db.String(255),
        db.ForeignKey(Client.client_id, ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    """str: Id of the clients. Foreign key from Client."""

    oauth_client = db.relationship(
        Client, backref=db.backref("sword_client", lazy="dynamic")
    )
    """Relationship to OAuth Client."""

    active = db.Column(
        db.Boolean(name="active"),
        unique=False,
        nullable=True
    )
    """bool: Active status of the application."""

    registration_type_id = db.Column(
        db.SmallInteger,
        unique=False,
        nullable=False
    )
    """int: Type of registration to register an item."""

    mapping_id = db.Column(
        db.Integer,
        db.ForeignKey(ItemTypeJsonldMapping.id),
        unique=False,
        nullable=False)
    """int: Mapping ID of the client. Foreign key from SwordItemTypeMapping."""

    mapping = db.relationship(
        ItemTypeJsonldMapping,
        backref=db.backref("sword_client", lazy="dynamic")
    )
    """Relationship to ItemTypeJsonldMapping."""

    workflow_id = db.Column(
        db.Integer,
        db.ForeignKey(WorkFlow.id),
        unique=False,
        nullable=True
    )
    """int: Workflow ID of the client. Foreign key from WorkFlow."""

    workflow = db.relationship(
        WorkFlow,
        backref=db.backref("sword_client", lazy="dynamic")
    )
    """Relationship to WorkFlow."""

    duplicate_check = db.Column(
        db.Boolean(name="duplicate_check"),
        unique=False,
        nullable=False
    )
    """bool: Duplicate check status of the application."""

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
        default=lambda: {},
        nullable=True
    )
    """list: Priority of use for metadata collection web API."""

    @property
    def registration_type(self):
        """Registration type name of the client."""
        registration_type = ""

        if self.registration_type_id == self.RegistrationType.DIRECT:
            registration_type = "Direct"
        elif self.registration_type_id == self.RegistrationType.WORKFLOW:
            registration_type = "Workflow"

        return registration_type
