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

from .helpers import json_data

# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace

# class SwordItemTypeMapping:
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py::TestSwordItemTypeMapping -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
class TestSwordItemTypeMapping:
    # def get_mapping_by_id(cls, id, ignore_deleted=True):
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py::TestSwordItemTypeMapping::test_get_mapping_by_id -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_get_mapping_by_id(app, db, sword_mapping):
        obj = sword_mapping[0]["sword_mapping"]
        assert SwordItemTypeMapping.get_mapping_by_id(obj.id) == obj
        # not found
        assert SwordItemTypeMapping.get_mapping_by_id(999) is None
        # invalid id
        assert SwordItemTypeMapping.get_mapping_by_id(None) is None

    # def create(cls, name, mapping, item_type_id):
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py::TestSwordItemTypeMapping::test_create -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_create(app, db, item_type):
        obj = SwordItemTypeMapping.create(
            name="test1",
            mapping={"test": "test"},
            item_type_id=item_type[0]["item_type"].id
        )
        assert obj.id == 1
        assert (SwordItemTypeMappingModel.query.filter_by(id=obj.id).first()) == obj

        # one more
        obj = SwordItemTypeMapping.create(
            name="test2",
            mapping={"test": "test"},
            item_type_id=item_type[0]["item_type"].id
        )
        assert obj.id == 2
        assert (SwordItemTypeMappingModel.query
            .filter_by(id=obj.id)
            .first()) == obj

        # occurs DB error. invalid item_type_id
        with pytest.raises(SQLAlchemyError):
            SwordItemTypeMapping.create(
            name="test2",
            mapping={"test": "test"},
            item_type_id=999
            )
        assert SwordItemTypeMappingModel.query.filter_by(id=3).first() == None

    # def update(cls, id, name=None, mapping=None, item_type_id=None):
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py::TestSwordItemTypeMapping::test_update -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_update(app, db, item_type, sword_mapping):
        obj = SwordItemTypeMapping.update(
            id=sword_mapping[0]["id"],
            mapping={"test2": "test2"},
        )

        result = SwordItemTypeMappingModel.query.filter_by(id=obj.id).first()

        assert result == obj
        assert result.mapping == obj.mapping
        assert result.version_id == sword_mapping[0]["version_id"] + 1

    # def versions()
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py::TestSwordItemTypeMapping::test_versions -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_versions(app, db, sword_mapping):
        ItemTypeMappingVersion = SwordItemTypeMapping.versions()

        obj = sword_mapping[1]["sword_mapping"]
        obj.mapping = {"test2": "test2"}
        db.session.commit()

        versions = (
            ItemTypeMappingVersion.query
            .filter_by(id=2)
            .all()
        )
        assert len(versions) == 2
        assert versions[0].id == sword_mapping[1]["id"]
        assert versions[1].id == obj.id
        assert versions[0].mapping == sword_mapping[1]["mapping"]
        assert versions[1].mapping == obj.mapping
        assert versions[0].version_id == sword_mapping[1]["version_id"]
        assert versions[1].version_id == sword_mapping[1]["version_id"] + 1

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

        # workflow
        client = tokens[1]["client"]
        result = SwordClient.register(
            client_id=client.client_id,
            registration_type_id=SwordClientModel.RegistrationType.WORKFLOW,
            mapping_id=sword_mapping[1]["sword_mapping"].id,
            workflow_id=workflow["workflow"].id,
        )
        assert result.client_id == client.client_id
        assert result.registration_type == "Workflow"
        assert result.mapping_id == sword_mapping[1]["sword_mapping"].id
        assert result.workflow_id == workflow["workflow"].id

        # occurs DB error. invalid workflow_id
        with pytest.raises(SQLAlchemyError):
            SwordClient.register(
                client_id=client.client_id,
                registration_type_id=SwordClientModel.RegistrationType.WORKFLOW,
                mapping_id=sword_mapping[1]["sword_mapping"].id,
                workflow_id=999,
            )

    # def update(cls, client_id, registration_type=None, mapping_id=None, workflow_id):
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_api.py::TestSwordClient::test_update -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_update(app, db, tokens, sword_mapping, sword_client, workflow):
        client = sword_client[0]["sword_client"]
        obj = SwordClient.update(
            client_id=client.client_id,
            registration_type_id=SwordClientModel.RegistrationType.WORKFLOW,
            mapping_id=sword_mapping[1]["sword_mapping"].id,
            workflow_id=workflow["workflow"].id,
        )
        assert obj == SwordClientModel.query.filter_by(client_id=client.client_id).first()
        assert obj.client_id == client.client_id
        assert obj.registration_type == "Workflow"
        assert obj.mapping_id == sword_mapping[1]["sword_mapping"].id
        assert obj.workflow_id == workflow["workflow"].id

        client = sword_client[1]["sword_client"]
        obj = SwordClient.update(
            client_id=client.client_id,
            registration_type_id=SwordClientModel.RegistrationType.DIRECT,
            mapping_id=sword_mapping[0]["sword_mapping"].id,
        )
        assert obj == SwordClientModel.query.filter_by(client_id=client.client_id).first()
        assert obj.client_id == client.client_id
        assert obj.registration_type == "Direct"
        assert obj.mapping_id == sword_mapping[0]["sword_mapping"].id
