# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-swordserver."""

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from invenio_db import db

from .errors import ErrorType, WekoSwordserverException
from .models import SwordItemTypeMappingModel, SwordClientModel


class SwordItemTypeMapping():
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
        obj = SwordItemTypeMappingModel(
            name=name,
            mapping=mapping or {},
            item_type_id=item_type_id,
        )

        try:
            with db.session.begin_nested():
                db.session.add(obj)
            db.session.commit()
        except SQLAlchemyError as ex:
            db.session.rollback()
            raise

        return obj


    @classmethod
    def update(cls, id, name, mapping, item_type_id):
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
        obj = SwordItemTypeMapping.get_mapping_by_id(id)
        if obj is None:
            current_app.logger.error(
                f"Mapping not found. ID: {id}"
            )
            raise WekoSwordserverException(
                "Mapping not defined.", errorType=ErrorType.ServerError)

        obj.name = name
        obj.mapping = mapping or {}
        obj.item_type_id = item_type_id

        try:
            db.session.commit()
        except SQLAlchemyError as ex:
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
        obj = SwordItemTypeMapping.get_mapping_by_id(id)
        if obj is not None:
            obj.is_deleted = True
            db.session.commit()
        return obj


    @classmethod
    def get_mapping_by_id(cls, id, include_deleted=False):
        """Get mapping by mapping_id.

        Get mapping latest version by mapping_id.
        If include_deleted=False, return None if the mapping is deleted(default).
        Specify include_deleted=True to get the mapping even if it is deleted.

        Args:
            id (int): Mapping ID.
            include_deleted (bool, optional):
                Include deleted mapping. Default is False.

        Returns:
            SwordItemTypeMapping:
            Mapping object. If not found or deleted, return `None`.
        """

        obj = (
            SwordItemTypeMappingModel.query
            .filter_by(id=id)
            .first()
        )

        if not include_deleted and obj is not None and obj.is_deleted:
            return None
        return obj


class SwordClient():

    @classmethod
    def register(cls, client_id, registration_type_id,
                        mapping_id, workflow_id=None):
        """Register client.

        Make ralaion between client, mapping, and workflow.

        Args:
            client_id (str): Client ID.
            registration_type_id (int): Type of registration.
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
        if registration_type_id is current_app.config.get(
            'WEKO_SWORDSERVER_REGISTRATION_TYPE'
        ).WORKFLOW and  workflow_id is None:
            current_app.logger.error(
                "Workflow ID is required for workflow registration."
            )
            raise WekoSwordserverException(
                "Workflow ID is required for workflow registration.",
                errorType=ErrorType.BadRequest
            )

        obj = SwordClientModel(
            client_id=client_id,
            registration_type_id=registration_type_id,
            mapping_id=mapping_id,
            workflow_id=workflow_id
        )

        try:
            with db.session.begin_nested():
                db.session.add(obj)
            db.session.commit()
        except SQLAlchemyError as ex:
            db.session.rollback()
            raise

        return obj


    @classmethod
    def update(cls, client_id, registration_type_id,
                mapping_id, workflow_id=None):
        """Update client.

        Update relation between client, mapping, and workflow.
        Specify the value to be updated.

        Args:
            client_id (str, optional): Client ID.
            registration_type_id (int, optional): Type of registration.
            mapping_id (int, optional): Mapping ID.
            workflow_id (int, optional): Workflow ID.

        Returns:
            SwordClient: Updated client object.

        Raises:
            WekoSwordserverException: When client not found.
            SQLAlchemyError: An error occurred while updating the client.
        """
        obj = SwordClient.get_client_by_id(client_id)
        if obj is None:
            current_app.logger.error(
                f"Client not found. ID: {client_id}"
            )
            raise WekoSwordserverException(
                "Client not found.", errorType=ErrorType.BadRequest)

        if (
            registration_type_id == SwordClientModel.RegistrationType.WORKFLOW
            and workflow_id is None
        ):
            current_app.logger.error(
                "Workflow ID is required for workflow registration."
            )
            raise WekoSwordserverException(
                "Workflow ID is required for workflow registration.",
                errorType=ErrorType.BadRequest
            )

        obj.registration_type_id = registration_type_id
        obj.mapping_id = mapping_id
        obj.workflow_id = workflow_id

        try:
            db.session.commit()
        except SQLAlchemyError as ex:
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
        obj = SwordClient.get_client_by_id(client_id)
        if obj is not None:
            try:
                db.session.delete(obj)
                db.session.commit()
            except SQLAlchemyError as ex:
                db.session.rollback()
                raise
        return obj


    @classmethod
    def get_client_by_id(cls, client_id):
        """Get client by client_id.

        Args:
            client_id (str): Client ID.

        Returns:
            SwordClient: Client object. If not found, return `None`.
        """
        obj = SwordClientModel.query.filter_by(client_id=client_id).one_or_none()
        return obj
