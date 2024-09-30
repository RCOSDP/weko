# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test for model field.

This tests needs to live in it's own file to have a clean database session.
"""

import pytest
from sqlalchemy_utils.types import UUIDType

from invenio_records.api import Record
from invenio_records.dumpers import SearchDumper
from invenio_records.dumpers.relations import RelationDumperExt
from invenio_records.models import RecordMetadataBase
from invenio_records.systemfields import (
    ModelField,
    ModelRelation,
    RelationsField,
    SystemFieldsMixin,
)
from invenio_records.systemfields.relations.modelrelations import (
    InvalidRelationValue,
    ModelRelation,
)


@pytest.fixture(scope="module")
def Record3Metadata(database):
    """."""
    db = database

    class Record3Metadata(db.Model, RecordMetadataBase):
        __tablename__ = "record3_metadata"

    Record3Metadata.__table__.create(db.engine)
    return Record3Metadata


@pytest.fixture(scope="module")
def Record2Metadata(Record3Metadata, database):
    """."""
    db = database

    class Record2Metadata(db.Model, RecordMetadataBase):
        __tablename__ = "record2_metadata"

        record3_id = db.Column(UUIDType, db.ForeignKey(Record3Metadata.id))

    Record2Metadata.__table__.create(db.engine)
    return Record2Metadata


def test_model_relation(testapp, database, Record3Metadata, Record2Metadata):
    """Test model field with clearing none/empty values."""
    db = database

    class Record3(Record, SystemFieldsMixin):
        model_cls = Record3Metadata
        dumper = SearchDumper()

    class Record2(Record, SystemFieldsMixin):
        model_cls = Record2Metadata
        dumper = SearchDumper(
            extensions=[
                RelationDumperExt("relations"),
            ]
        )
        record3_id = ModelField("record3_id")
        relations = RelationsField(
            record3=ModelRelation(
                Record3,
                "record3_id",
                "record3",
                keys=["title"],
            )
        )

    # Set relation via model field
    rec3 = Record3.create({"title": "this is record 3", "description": "n/a"})
    rec3.commit()

    rec2 = Record2.create({"title": "this is record 2"})
    rec2.record3_id = rec3.id
    rec2.relations.dereference()
    rec2.commit()

    # We do not store the dereferenced data in the record.
    assert "record3" not in rec2

    # Dumping dereferences the data:
    dump = rec2.dumps()
    assert dump["record3_id"] == str(rec3.id)
    assert dump["record3"] == {
        "id": str(rec3.id),
        "title": "this is record 3",
        "@v": f"{rec3.id}::{rec3.revision_id}",
    }

    rec2 = Record2.create({"title": "this is record 2"})
    rec2.relations.dereference()
    rec2.commit()
    assert rec2.record3_id is None

    # Set relation via relations field (record and model class)
    rec2 = Record2.create({"title": "this is record 2"})
    rec2.relations.record3 = rec3
    rec2.relations.record3 = rec3.model
    rec2.commit()

    # Set and invalid object
    assert pytest.raises(
        InvalidRelationValue,
        setattr,
        rec2.relations,
        "record3",
        "someid",
    )

    # Unset a relation
    rec2 = Record2.create({"title": "this is record 2"})
    rec2.relations.record3 = rec3
    rec2.commit()
    del rec2.relations.record3
    assert rec2.record3_id is None
