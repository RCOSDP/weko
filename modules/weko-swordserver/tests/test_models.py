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

from weko_swordserver.models import SwordItemTypeMapping, SwordClient

# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_models.py -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace

@pytest.fixture
def sword_mapping(db, item_type):
    sword_mapping = []
    for i in range(1, 3):
        obj = SwordItemTypeMapping(
            # id=i,
            name=f"test{i}",
            mapping={"test": "test"},
            item_type_id=item_type["item_type"].id,
            version_id=i,
            is_deleted=False
        )
        with db.session.begin_nested():
            db.session.add(obj)

        sword_mapping.append({
            "id": obj.id,
            "sword_mapping": obj,
            "name": obj.name,
            "mapping": obj.mapping,
            "item_type_id": obj.item_type_id,
            "version_id": obj.version_id,
            "is_deleted": obj.is_deleted
        })

    db.session.commit()

    return sword_mapping

@pytest.fixture
def sword_client(db, tokens, sword_mapping, workflow):
    client = tokens[0]["client"]
    sword_client1 = SwordClient(
        client_id=client.client_id,
        registration_type_index=SwordClient.RegistrationType.DIRECT,
        mapping_id=sword_mapping[0]["sword_mapping"].id,
    )
    client = tokens[1]["client"]
    sword_client2 = SwordClient(
        client_id=client.client_id,
        registration_type_index=SwordClient.RegistrationType.WORKFLOW,
        mapping_id=sword_mapping[1]["sword_mapping"].id,
        workflow_id=workflow["workflow"].id,
    )

    with db.session.begin_nested():
        db.session.add(sword_client1)
    db.session.commit()

    return [{"sword_client": sword_client1}, {"sword_client": sword_client2}]

# class SwordItemTypeMapping:
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_models.py::TestSwordItemTypeMapping -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
class TestSwordItemTypeMapping:
    # def get_mapping_by_id(id):
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_models.py::TestSwordItemTypeMapping::test_get_mapping_by_id -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_get_mapping_by_id(app, db, sword_mapping):
        obj = sword_mapping[0]["sword_mapping"]
        assert SwordItemTypeMapping.get_mapping_by_id(obj.id) == obj
        # not found
        assert SwordItemTypeMapping.get_mapping_by_id(999) is None
        # invalid id
        assert SwordItemTypeMapping.get_mapping_by_id(None) is None

    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_models.py::TestSwordItemTypeMapping::test_create -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_create(app, db, item_type):
        obj = SwordItemTypeMapping.create(
            name="test1",
            mapping={"test": "test"},
            item_type_id=item_type["item_type"].id
        )
        assert obj.id == 1
        assert (SwordItemTypeMapping.query.filter_by(id=obj.id).first()) == obj

        # one more
        obj2 = SwordItemTypeMapping.create(
            name="test2",
            mapping={"test": "test"},
            item_type_id=item_type["item_type"].id
        )
        assert obj2.id == 2
        assert (SwordItemTypeMapping.query
            .filter_by(id=obj2.id)
            .first()) == obj2

        # occurs DB error
        ex = SQLAlchemyError("test_error")
        with patch("weko_swordserver.models.db.session.commit") as mock_session:
            mock_session.side_effect = ex
            with pytest.raises(SQLAlchemyError):
                SwordItemTypeMapping.create(
                name="test2",
                mapping={"test": "test"},
                item_type_id=item_type["item_type"].id
                )
            assert (SwordItemTypeMapping.query.filter_by(id=3).first()) == None

    def test_update(app, db, item_type, sword_mapping):
        obj = SwordItemTypeMapping.update(
            id=sword_mapping[0]["id"],
            mapping={"test2": "test2"},
        )

        result = SwordItemTypeMapping.query.filter_by(id=obj.id).first()

        assert result == obj
        assert result.mapping == obj.mapping
        assert result.version_id == 2

    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_models.py::TestSwordItemTypeMapping::test_get_all_versions_by_id -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_get_all_versions_by_id(app, db, sword_mapping):
        ItemTypeMappingVersion = version_class(SwordItemTypeMapping)

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
        assert versions[0].version_id == 1
        assert versions[1].version_id == 2

class TestSwordClient:
    def test_get_client_by_id(app, db, sword_client):
        obj = sword_client[0]["sword_client"]
        result = SwordClient.get_client_by_id(obj.client_id)
        assert result == obj
        assert result.registration_type == "Direct"

        assert SwordClient.get_client_by_id("999") is None
        assert SwordClient.get_client_by_id(None) is None

