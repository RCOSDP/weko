# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import json

from flask import current_app
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy_utils.types import JSONType

from invenio_db import db
from invenio_oauth2server.models import Client
from weko_records.models import ItemType, Timestamp
from weko_workflow.models import WorkFlow

from .errors import ErrorType, WekoSwordserverException

"""Models of weko-swordserver."""

class SwordItemTypeMapping(db.Model, Timestamp):
    """SwordItemTypeMapping Model

    Mapping for RO-Crate matadata to WEKO item type.
    When updating the mapping, the verion_id is incremented and the previous
    mapping moves to the history table.

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


    @classmethod
    def create(cls, name, mapping, item_type_id):
        """Create mapping.

        Create new mapping for item type. ID is autoincremented.
        mapping dict is dumped to JSON format.

        Args:
            name (str): Name of the mapping.
            mapping (dict): Mapping in JSON format.
            item_type_id (str): Target itemtype of the mapping.

        Returns:
            SwordItemTypeMapping: Created mapping object.

        Raises:
            SQLAlchemyError: An error occurred while creating the mapping.
        """
        mapping = json.dumps(mapping or {})
        obj = cls(
            name=name,
            mapping=mapping,
            item_type_id=item_type_id,
        )

        try:
            with db.session.begin_nested():
                db.session.add(obj)
            db.session.commit()
        except SQLAlchemyError as ex:
            current_app.logger.error(ex)
            db.session.rollback()
            raise

        return obj


    @classmethod
    def update(cls, id, name=None, mapping=None, item_type_id=None):
        """Update mapping.

        Update mapping by ID. Specify the value to be updated.
        The verion_id is incremented and the previousmapping moves to
        the history table.

        Args:
            id (int): Mapping ID.
            name (str, optional): Name of the mapping. Not required.
            mapping (dict, optional): Mapping in JSON format. Not required.
            item_type_id (str, optional):
                Target itemtype of the mapping. Not required.

        Returns:
            SwordItemTypeMapping: Updated mapping object.

        Raises:
            WekoSwordserverException: When mapping not found.
            SQLAlchemyError: An error occurred while updating the mapping.
        """
        obj = cls.get_mapping_by_id(id)
        if obj is None:
            raise WekoSwordserverException(
                "Mapping not defined.", errorType=ErrorType.MappingNotDefined)

        obj.name = name if name is not None else obj.name
        obj.mapping = json.dumps(
            mapping if mapping is not None else obj.mapping
        )
        obj.item_type_id = (
            item_type_id if item_type_id is not None else obj.item_type_id
        )

        try:
            db.session.commit()
        except SQLAlchemyError as ex:
            current_app.logger.error(ex)
            db.session.rollback()
            raise

        return obj

    @classmethod
    def delete(cls, id):
        """Delete mapping.

        Soft-delete mapping by ID.

        Args:
            id (int): Mapping ID.

        Returns:
            SwordItemTypeMapping: Deleted mapping object.
        """
        obj = cls.get_mapping_by_id(id)
        if obj is not None:
            obj.is_deleted = True
        db.session.commit()
        return obj


    @classmethod
    def get_mapping_by_id(cls, id, ignore_deleted=True):
        """Get mapping by mapping_id.

        Get mapping latest version by mapping_id.
        If ignore_deleted=True, return None if the mapping is deleted(default).
        Specify ignore_deleted=False to get the mapping even if it is deleted.

        Args:
            id (int): Mapping ID.
            ignore_deleted (bool, optional):
                Ignore deleted mapping. Default is True.

        Returns:
            SwordItemTypeMapping:
            Mapping object. If not found or deleted, return `None`.
        """

        obj = (
            cls.query
            .filter_by(id=id)
            .first()
        )

        if ignore_deleted and obj is not None and obj.is_deleted:
            return None
        return obj


class SwordClient(db.Model, Timestamp):
    """SwordClient Model

    client whitch is register items through the sword api.

    Columns:
        `client_id` (str): ID of the client. Primary key.\
            Foreign key referencing `Client.client_id`.
        `registration_type_index` (int): Type of registration to register an item.
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

    client_id = db.Column(
        db.String(255),
        db.ForeignKey(Client.client_id),
        primary_key=True,
        unique=True)
    """Id of the clients. Foreign key from Client."""

    registration_type_index = db.Column(
        db.Integer,
        unique=False,
        nullable=False
    )
    """Type of registration to register an item."""

    mapping_id = db.Column(
        db.Integer,
        db.ForeignKey(SwordItemTypeMapping.id),
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
        registration_type = str("")

        if self.registration_type_index == self.RegistrationType.DIRECT:
            registration_type = str("Direct")
        elif self.registration_type_index == self.RegistrationType.WORKFLOW:
            registration_type = str("Workflow")

        return registration_type


    @classmethod
    def register(cls, client_id, registration_type_index,
                        mapping_id, workflow_id=None):
        """Register client.

        Make ralaion between client, mapping, and workflow.

        Args:
            client_id (str): Client ID.
            registration_type_index (int): Type of registration.
            mapping_id (int): Mapping ID.
            workflow_id (int, optional):
                Workflow ID. Required when registration_type is workflow.

        Returns:
            SwordClient: Created client object.

        Raises:
            WekoSwordserverException: When workflow_id not specified
                even if the registration type is workflow.
            SQLAlchemyError: An error occurred while creating the client.
        """
        if registration_type_index is current_app.config.get(
            'WEKO_SWORDSERVER_REGISTRATION_TYPE'
        ).WORKFLOW and  workflow_id is None:
            raise WekoSwordserverException(
                "Workflow ID is required for workflow registration.",
                errorType=ErrorType.BadRequest
            )

        obj = cls(
            client_id=client_id,
            registration_type_index=registration_type_index,
            mapping_id=mapping_id,
            workflow_id=workflow_id
        )

        try:
            with db.session.begin_nested():
                db.session.add(obj)
            db.session.commit()
        except SQLAlchemyError as ex:
            current_app.logger.error(ex)
            db.session.rollback()
            raise

        return obj

    @classmethod
    def update(cls, client_id, registration_type_index=None,
                mapping_id=None, workflow_id=None):
        """Update client.

        Update relation between client, mapping, and workflow.
        Specify the value to be updated.

        Args:
            client_id (str, optional): Client ID.
            registration_type (int, optional): Type of registration.
            mapping_id (int, optional): Mapping ID.
            workflow_id (int, optional): Workflow ID.

        Returns:
            SwordClient: Updated client object.

        Raises:
            WekoSwordserverException: When client not found.
            SQLAlchemyError: An error occurred while updating the client.
        """
        obj = cls.get_client_by_id(client_id)
        if obj is None:
            raise WekoSwordserverException(
                "Client not found.", errorType=ErrorType.BadRequest)

        obj.registration_type_index = (
            registration_type_index
            if registration_type_index is not None
            else obj.registration_type_index
        )
        obj.mapping_id = (
            mapping_id if mapping_id is not None else obj.mapping_id
        )
        obj.workflow_id = (
            workflow_id if workflow_id is not None else obj.workflow_id
        )

        try:
            db.session.commit()
        except SQLAlchemyError as ex:
            current_app.logger.error(ex)
            db.session.rollback()
            raise

        return obj

    @classmethod
    def remove(cls, client_id):
        """Remove client.

        Args:
            client_id (str): Client ID.

        Returns:
            SwordClient: Removed client object.
        """
        obj = cls.get_client_by_id(client_id)
        if obj is not None:
            obj.delete()
        return obj


    @classmethod
    def get_client_by_id(cls, client_id):
        """Get client by client_id.

        Args:
            client_id (str): Client ID.

        Returns:
            SwordClient: Client object. If not found, return `None`.
        """
        obj = cls.query.filter_by(client_id=client_id).one_or_none()
        return obj
