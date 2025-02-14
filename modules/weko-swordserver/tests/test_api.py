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

from weko_swordserver.api import SwordItemTypeMapping, SwordClient
from weko_swordserver.models import SwordItemTypeMappingModel, SwordClientModel
from weko_swordserver.errors import ErrorType, WekoSwordserverException
from .helpers import json_data

# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace

# class SwordItemTypeMapping:
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py::TestSwordItemTypeMapping -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
class TestSwordItemTypeMapping:
    # def get_mapping_by_id(cls, id, ignore_deleted=True):
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py::TestSwordItemTypeMapping::test_get_mapping_by_id -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_get_mapping_by_id(app, db, sword_mapping):
        obj = sword_mapping[0]["sword_mapping"]
        assert SwordItemTypeMapping.get_mapping_by_id(obj.id) is obj
        assert SwordItemTypeMapping.get_mapping_by_id(obj.id).is_deleted is False

        # not found
        assert SwordItemTypeMapping.get_mapping_by_id(999) is None

        # Retrieval with include_deleted=False
        obj.is_deleted = True
        db.session.commit()
        mapping = SwordItemTypeMapping.get_mapping_by_id(obj.id, include_deleted=False)
        assert mapping is None

        # Retrieve with include_deleted=True
        obj.is_deleted = True
        db.session.commit()
        mapping = SwordItemTypeMapping.get_mapping_by_id(obj.id, include_deleted=True)
        assert mapping.id == obj.id
        assert mapping.is_deleted is True

    # def create(cls, name, mapping, item_type_id):
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py::TestSwordItemTypeMapping::test_create -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_create(app, db, item_type):
        # one
        obj = SwordItemTypeMapping.create(
            name="test1",
            mapping={"test": "test"},
            item_type_id=item_type[0]["item_type"].id,
        )
        assert obj.id == 1
        assert (SwordItemTypeMappingModel.query.filter_by(id=obj.id).first()) == obj

        # one more
        obj = SwordItemTypeMapping.create(
            name="test2",
            mapping={"test": "test"},
            item_type_id=item_type[0]["item_type"].id,
        )
        assert obj.id == 2
        assert (SwordItemTypeMappingModel.query.filter_by(id=obj.id).first()) == obj

        # occurs DB error. invalid item_type_id
        with pytest.raises(SQLAlchemyError) as e:
            SwordItemTypeMapping.create(
                name="test2", mapping={"test": "test"}, item_type_id=999
            )
        assert isinstance(e.value, SQLAlchemyError)
        assert SwordItemTypeMappingModel.query.filter_by(id=3).first() == None

    # def update(cls, id, name=None, mapping=None, item_type_id=None):
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py::TestSwordItemTypeMapping::test_update -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_update(app, db, item_type, sword_mapping):
        # Update Successful
        obj = SwordItemTypeMapping.update(
            id=sword_mapping[0]["id"],
            name="test2",
            mapping={"test2": "test2"},
            item_type_id=sword_mapping[0]["item_type_id"],
        )

        result = SwordItemTypeMappingModel.query.filter_by(id=obj.id).first()
        assert result == obj
        assert result.name == "test2"
        assert result.mapping == obj.mapping
        assert result.version_id == sword_mapping[0]["version_id"] + 1

        # Update with non-existent id
        with pytest.raises(WekoSwordserverException) as e:
            SwordItemTypeMapping.update(
                name="test2", id=999, mapping=None, item_type_id=sword_mapping[0]["item_type_id"]
            )
        assert e.value.errorType == ErrorType.ServerError
        assert e.value.message == "Mapping not defined."

        # Update with invalid item_type_id
        with pytest.raises(SQLAlchemyError) as e:
            SwordItemTypeMapping.update(name="test2", id=sword_mapping[0]["id"], mapping=None, item_type_id=999)
        assert isinstance(e.value, SQLAlchemyError)

    # def versions()
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py::TestSwordItemTypeMapping::test_versions -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_versions(app, db, sword_mapping):

        obj = sword_mapping[1]["sword_mapping"]
        obj.mapping = {"test2": "test2"}
        db.session.commit()

        versions = obj.versions.all()
        assert len(versions) == 2
        assert versions[0].id == sword_mapping[1]["id"]
        assert versions[1].id == obj.id
        assert versions[0].mapping == sword_mapping[1]["mapping"]
        assert versions[1].mapping == obj.mapping
        assert versions[0].version_id == sword_mapping[1]["version_id"]
        assert versions[1].version_id == sword_mapping[1]["version_id"] + 1

    # delete(cls, id):
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py::TestSwordItemTypeMapping::test_delete -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_delete(app, db, sword_mapping):
        # Successful delete
        SwordItemTypeMapping.delete(id=sword_mapping[2]["id"])
        assert (
            SwordItemTypeMappingModel.query.filter_by(id=3).first().is_deleted == True
        )

        # Delete with non-existent id
        res = SwordItemTypeMapping.delete(id=999)
        assert res == None


#  .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py::TestSwordClient -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
class TestSwordClient:
    # def get_client_by_id(cls, client_id):
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py::TestSwordClient::test_get_client_by_id -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_get_client_by_id(app, db, sword_client):
        # direct
        obj = sword_client[0]["sword_client"]
        result = SwordClient.get_client_by_id(obj.client_id)
        assert result == obj
        assert result.registration_type == "Direct"

        assert SwordClient.get_client_by_id("999") is None
        assert SwordClient.get_client_by_id(None) is None

        # workflow
        obj = sword_client[1]["sword_client"]
        result = SwordClient.get_client_by_id(obj.client_id)
        assert result == obj
        assert result.registration_type == "Workflow"

        assert SwordClient.get_client_by_id("999") is None
        assert SwordClient.get_client_by_id(None) is None

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
        assert result.client_id == client.client_id
        assert result.registration_type == "Direct"
        assert result.mapping_id == sword_mapping[0]["sword_mapping"].id
        assert result.workflow_id == None

        # direct with non-existent client_id
        with pytest.raises(SQLAlchemyError) as e:
            result = SwordClient.register(
                client_id=999,
                registration_type_id=SwordClientModel.RegistrationType.DIRECT,
                mapping_id=sword_mapping[0]["sword_mapping"].id,
            )
        assert isinstance(e.value, SQLAlchemyError)

        # workflow
        client = tokens[1]["client"]
        result = SwordClient.register(
            client_id=client.client_id,
            registration_type_id=SwordClientModel.RegistrationType.WORKFLOW,
            mapping_id=sword_mapping[1]["sword_mapping"].id,
            workflow_id=workflow[1]["workflow"].id,
        )
        assert result.client_id == client.client_id
        assert result.registration_type == "Workflow"
        assert result.mapping_id == sword_mapping[1]["sword_mapping"].id
        assert result.workflow_id == workflow[1]["workflow"].id

        # workflow with non-existent workflow_id
        client = tokens[1]["client"]
        with pytest.raises(SQLAlchemyError) as e:
            result = SwordClient.register(
                client_id=client.client_id,
                registration_type_id=SwordClientModel.RegistrationType.WORKFLOW,
                mapping_id=sword_mapping[1]["sword_mapping"].id,
                workflow_id=999,
            )
        assert isinstance(e.value, SQLAlchemyError)

        # workflow workflow_id did not set
        client = tokens[1]["client"]
        with pytest.raises(WekoSwordserverException) as e:
            result = SwordClient.register(
                client_id=client.client_id,
                registration_type_id=SwordClientModel.RegistrationType.WORKFLOW,
                mapping_id=sword_mapping[1]["sword_mapping"].id,
            )
        assert e.value.errorType == ErrorType.BadRequest
        assert e.value.message == "Workflow ID is required for workflow registration."

    # def update(cls, client_id, registration_type=None, mapping_id=None, workflow_id):
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py::TestSwordClient::test_update -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_update(app, db, tokens, sword_mapping, sword_client, workflow):

        # Successful update workflow to direct
        client = sword_client[1]["sword_client"]
        obj = SwordClient.update(
            client_id=client.client_id,
            registration_type_id=SwordClientModel.RegistrationType.DIRECT,
            mapping_id=sword_mapping[0]["sword_mapping"].id,
        )
        assert (
            obj == SwordClientModel.query.filter_by(client_id=client.client_id).first()
        )
        assert obj.client_id == client.client_id
        assert obj.registration_type_id == SwordClientModel.RegistrationType.DIRECT
        assert obj.mapping_id == sword_mapping[0]["sword_mapping"].id
        assert obj.workflow_id == None

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
        obj = SwordClient.update(
            client_id=client.client_id,
            registration_type_id=SwordClientModel.RegistrationType.WORKFLOW,
            mapping_id=sword_mapping[1]["sword_mapping"].id,
            workflow_id=workflow[1]["workflow"].id,
        )
        assert (
            obj == SwordClientModel.query.filter_by(client_id=client.client_id).first()
        )
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
        client = sword_client[0]["sword_client"]
        result = SwordClient.get_client_by_id(client.client_id)
        assert result == client
        assert result.registration_type_id == SwordClientModel.RegistrationType.DIRECT

        # Get client by valid ID (Workflow registration)
        client = sword_client[1]["sword_client"]
        result = SwordClient.get_client_by_id(client.client_id)
        assert result == client
        assert result.registration_type_id == SwordClientModel.RegistrationType.WORKFLOW

        # Get client by non-existent ID
        result = SwordClient.get_client_by_id("non_existent_client_id")
        assert result is None


