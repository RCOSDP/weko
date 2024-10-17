# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import pytest
from unittest.mock import patch
from sqlalchemy.exc import SQLAlchemyError

from weko_swordserver.models import SwordItemTypeMapping, SwordClient

# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_models.py -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace

@pytest.fixture
def sword_mapping(db, item_type):
    sword_mapping1 = SwordItemTypeMapping(
        id=1,
        name="test1",
        mapping={"test": "test"},
        itemtype_id=item_type["item_type"].id,
        version_id=1,
        is_deleted=False
    )
    sword_mapping2 = SwordItemTypeMapping(
        id=2,
        name="test2",
        mapping={"test": "test"},
        itemtype_id=item_type["item_type"].id,
        version_id=1,
        is_deleted=True
    )
    sword_mapping3 = SwordItemTypeMapping(
        id=2,
        name="test2",
        mapping={"test": "test"},
        itemtype_id=item_type["item_type"].id,
        version_id=2,
        is_deleted=False
    )

    with db.session.begin_nested():
        db.session.add(sword_mapping1)
    db.session.commit()

    return [
        {"sword_mapping": sword_mapping1},
        {"sword_mapping": sword_mapping2},
        {"sword_mapping": sword_mapping3},
        ]

@pytest.fixture
def sword_client(db, tokens, sword_mapping, workflow):
    client = tokens["client"]
    sword_client1 = SwordClient(
        client_id=client.client_id,
        registration_type_index=SwordClient.RegistrationType.DIRECT,
        mapping_id=sword_mapping[0]["sword_mapping"].id,
        workflow_id=workflow["workflow"].id,
    )

    with db.session.begin_nested():
        db.session.add(sword_client1)
    db.session.commit()

    return [{"sword_client": sword_client1}]

# class SwordItemTypeMapping:
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_models.py::TestSwordItemTypeMapping -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
class TestSwordItemTypeMapping:
    # def get_mapping_by_id(id):
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_models.py::TestSwordItemTypeMapping::test_get_mapping_by_id -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_get_mapping_by_id(app, db, sword_mapping):
        obj = sword_mapping[0]["sword_mapping"]
        assert SwordItemTypeMapping.get_mapping_by_id(obj.id) == obj

        assert SwordItemTypeMapping.get_mapping_by_id(999) is None

        assert SwordItemTypeMapping.get_mapping_by_id(None) is None

    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_models.py::TestSwordItemTypeMapping::test_create -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_create(app, db, item_type):
        obj = SwordItemTypeMapping.create(
            name="test1",
            mapping={"test": "test"},
            itemtype_id=item_type["item_type"].id
        )

        assert (SwordItemTypeMapping.query
            .filter_by(id=obj.id)
            .order_by(SwordItemTypeMapping.version_id.desc())
            .first()) == obj

        ex = SQLAlchemyError("test_error")
        with patch("weko_swordserver.models.db.session.commit") as mock_session:
            mock_session.side_effect = ex
            with pytest.raises(SQLAlchemyError):
                SwordItemTypeMapping.create(
                name="test2",
                mapping={"test": "test"},
                itemtype_id=item_type["item_type"].id
                )


class TestSwordClient:
    def test_get_client_by_id(app, db, sword_client):
        obj = sword_client[0]["sword_client"]
        result = SwordClient.get_client_by_id(obj.client_id)
        assert result == obj
        assert result.registration_type == "Direct"

        assert SwordClient.get_client_by_id("999") is None
        assert SwordClient.get_client_by_id(None) is None

