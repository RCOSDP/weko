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
from .models import SwordClientModel


class SwordClient():

    @classmethod
    def register(cls, client_id, registration_type_id,
                        mapping_id, active, meta_data_api, workflow_id=None):
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
            workflow_id=workflow_id,
            active=active,
            meta_data_api=meta_data_api
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

    @classmethod
    def get_client_id_all(cls):
        """Get client_id all. """
        model = SwordClientModel
        query = model.query.with_entities(model.client_id)
        return query.all()
