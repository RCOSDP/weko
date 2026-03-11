# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import pytest
from unittest.mock import patch
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy_continuum import version_class

from weko_swordserver.api import SwordClient
# from weko_swordserver.models import SwordItemTypeMappingModel
from weko_swordserver.models import SwordClientModel
from weko_swordserver.errors import ErrorType, WekoSwordserverException
from .helpers import json_data

# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace


# class SwordClient:
#  .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py::TestSwordClient -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
class TestSwordClient:
    # def register(cls, client_id, registration_type_id, mapping_id, workflow_id):
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py::TestSwordClient::test_register -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_register(app, db, tokens, sword_mapping, workflow):
        # direct
        client = tokens[0]["client"]
        result = SwordClient.register(
            client_id=client.client_id,
            registration_type_id=SwordClientModel.RegistrationType.DIRECT,
            mapping_id=sword_mapping[0]["sword_mapping"].id,
        )
        obj = SwordClientModel.query.filter_by(client_id=client.client_id).first()
        assert obj == result
        assert obj.client_id == client.client_id
        assert obj.active == True
        assert obj.registration_type == "Direct"
        assert obj.mapping_id == sword_mapping[0]["sword_mapping"].id
        assert obj.workflow_id == None
        assert obj.duplicate_check == False
        assert obj.meta_data_api == []

        # direct with non-existent client_id
        with pytest.raises(SQLAlchemyError) as e:
            result = SwordClient.register(
                client_id=999,
                registration_type_id=SwordClientModel.RegistrationType.DIRECT,
                mapping_id=sword_mapping[0]["sword_mapping"].id,
                active=False,
                meta_data_api=[],
            )
        assert isinstance(e.value, SQLAlchemyError)

        # workflow
        client = tokens[1]["client"]
        result = SwordClient.register(
            client_id=client.client_id,
            active=False,
            registration_type_id=SwordClientModel.RegistrationType.WORKFLOW,
            mapping_id=sword_mapping[1]["sword_mapping"].id,
            workflow_id=workflow[1]["workflow"].id,
            duplicate_check=False,
            meta_data_api=["CrossRef"]
        )
        obj = SwordClientModel.query.filter_by(client_id=client.client_id).first()
        assert obj == result
        assert obj.client_id == client.client_id
        assert obj.active == False
        assert obj.registration_type == "Workflow"
        assert obj.mapping_id == sword_mapping[1]["sword_mapping"].id
        assert obj.workflow_id == workflow[1]["workflow"].id
        assert obj.duplicate_check == False
        assert obj.meta_data_api == ["CrossRef"]

        # workflow with non-existent workflow_id
        client = tokens[1]["client"]
        with pytest.raises(SQLAlchemyError) as e:
            result = SwordClient.register(
                client_id=client.client_id,
                registration_type_id=SwordClientModel.RegistrationType.WORKFLOW,
                mapping_id=sword_mapping[1]["sword_mapping"].id,
                workflow_id=999,
                active=False,
                meta_data_api=[],
            )
        assert isinstance(e.value, SQLAlchemyError)

        # workflow workflow_id did not set
        client = tokens[1]["client"]
        with pytest.raises(WekoSwordserverException) as e:
            result = SwordClient.register(
                client_id=client.client_id,
                registration_type_id=SwordClientModel.RegistrationType.WORKFLOW,
                mapping_id=sword_mapping[1]["sword_mapping"].id,
                active=False,
                meta_data_api=[],
            )
        assert e.value.errorType == ErrorType.BadRequest
        assert e.value.message == "Workflow ID is required for workflow registration."

    # def update(cls, client_id, registration_type=None, mapping_id=None, workflow_id):
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py::TestSwordClient::test_update -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_update(app, db, tokens, sword_mapping, sword_client, workflow):

        # Successful update workflow to direct
        client = sword_client[1]["sword_client"]
        result = SwordClient.update(
            client_id=client.client_id,
            active=False,
            registration_type_id=SwordClientModel.RegistrationType.DIRECT,
            mapping_id=sword_mapping[0]["sword_mapping"].id,
            duplicate_check=True,
            meta_data_api=["CrossRef"]
        )

        obj = SwordClientModel.query.filter_by(client_id=client.client_id).first()

        assert obj == result
        assert obj.client_id == client.client_id
        assert obj.active == False
        assert obj.registration_type == "Direct"
        assert obj.mapping_id == sword_mapping[0]["sword_mapping"].id
        assert obj.workflow_id == None
        assert obj.duplicate_check == True
        assert obj.meta_data_api == ["CrossRef"]

        # Update workflow to direct with non-existent client_id
        client = sword_client[0]["sword_client"]
        with pytest.raises(WekoSwordserverException) as e:
            SwordClient.update(
                client_id="non_existent_client_id",
                registration_type_id=SwordClientModel.RegistrationType.DIRECT,
                mapping_id=sword_mapping[0]["sword_mapping"].id,
            )
        assert e.value.errorType == ErrorType.BadRequest
        assert e.value.message == "Client not found."

        # Update to workflow to workflow without workflow_id
        client = sword_client[0]["sword_client"]
        with pytest.raises(WekoSwordserverException) as e:
            SwordClient.update(
                client_id=client.client_id,
                registration_type_id=SwordClientModel.RegistrationType.WORKFLOW,
                mapping_id=sword_mapping[0]["sword_mapping"].id,
            )
        assert e.value.errorType == ErrorType.BadRequest
        assert e.value.message == "Workflow ID is required for workflow registration."

        # Update DIRECT with invalid mapping_id
        client = sword_client[0]["sword_client"]
        with pytest.raises(SQLAlchemyError) as e:
            SwordClient.update(
                client_id=client.client_id,
                registration_type_id=SwordClientModel.RegistrationType.DIRECT,
                mapping_id=999,
            )
        assert isinstance(e.value, SQLAlchemyError)

        # Successful update direct to workflow
        client = sword_client[0]["sword_client"]
        result = SwordClient.update(
            client_id=client.client_id,
            registration_type_id=SwordClientModel.RegistrationType.WORKFLOW,
            mapping_id=sword_mapping[1]["sword_mapping"].id,
            workflow_id=workflow[1]["workflow"].id,
        )

        obj = SwordClientModel.query.filter_by(client_id=client.client_id).first()
        assert obj == result
        assert obj.client_id == client.client_id
        assert obj.registration_type_id == SwordClientModel.RegistrationType.WORKFLOW
        assert obj.mapping_id == sword_mapping[1]["sword_mapping"].id
        assert obj.workflow_id == workflow[1]["workflow"].id

    # def remove(cls, client_id):
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py::TestSwordClient::test_remove -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_remove(app, db, sword_client):
        # Successful removal
        client = sword_client[0]["sword_client"]
        count = SwordClientModel.query.count()
        obj = SwordClient.remove(client_id=client.client_id)
        assert obj == client
        assert (
            SwordClientModel.query.filter_by(client_id=client.client_id).first() is None
        )
        assert SwordClientModel.query.count() == count - 1

        # Exception during removal
        client = sword_client[1]["sword_client"]
        with patch('weko_swordserver.api.db.session.commit', side_effect=SQLAlchemyError):
            with pytest.raises(SQLAlchemyError):
                SwordClient.remove(client_id=client.client_id)
            assert SwordClientModel.query.filter_by(client_id=client.client_id).first() is not None

        # Removal of non-existent client
        obj = SwordClient.remove(client_id="non_existent_client_id")
        assert obj is None

    # def get_client_by_id(cls, client_id):
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py::TestSwordClient::test_get_client_by_id -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_get_client_by_id(self, db, sword_client):
        # Get client by valid ID (Direct registration)
        obj = sword_client[0]["sword_client"]
        result = SwordClient.get_client_by_id(obj.client_id)
        assert result == obj
        assert result.registration_type_id == SwordClientModel.RegistrationType.DIRECT
        assert result.registration_type == "Direct"


        # Get client by valid ID (Workflow registration)
        obj = sword_client[1]["sword_client"]
        result = SwordClient.get_client_by_id(obj.client_id)
        assert result == obj
        assert result.registration_type_id == SwordClientModel.RegistrationType.WORKFLOW
        assert result.registration_type == "Workflow"

        # Get client by non-existent ID
        result = SwordClient.get_client_by_id("non_existent_client_id")
        assert result is None


    # def get_client_id_all(cls):
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py::TestSwordClient::test_get_client_id_all -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_get_client_id_all(app, db, sword_client):
        lst = SwordClient.get_client_id_all()
        assert len(lst) == 3
        assert lst[0] == sword_client[0]["sword_client"].client_id
        assert lst[1] == sword_client[1]["sword_client"].client_id
        assert lst[2] == sword_client[2]["sword_client"].client_id


    # def get_clients_by_mapping_id(cls, mapping_id):
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py::TestSwordClient::test_get_clients_by_mapping_id -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_get_clients_by_mapping_id(app, db, sword_client):
        # Get clients by valid mapping ID
        obj = sword_client[0]["sword_client"]
        result = SwordClient.get_clients_by_mapping_id(obj.mapping_id)
        assert len(result) == 2
        assert result[0].client_id == sword_client[0]["sword_client"].client_id
        assert result[1].client_id == sword_client[2]["sword_client"].client_id

        # Get clients by non-existent mapping ID
        result = SwordClient.get_clients_by_mapping_id(999)
        assert len(result) == 0
