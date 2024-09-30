# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test the dumpers API."""

from datetime import datetime
from uuid import UUID

import pytest
from sqlalchemy.dialects import mysql

from invenio_records.api import Record
from invenio_records.dumpers import SearchDumper, SearchDumperExt
from invenio_records.dumpers.indexedat import IndexedAtDumperExt
from invenio_records.dumpers.relations import RelationDumperExt
from invenio_records.models import RecordMetadataBase
from invenio_records.systemfields.relations import (
    PKListRelation,
    PKRelation,
    RelationsField,
)


@pytest.fixture()
def example_data():
    """Example record used for tests."""
    return {
        # "$schema": "",
        "id": "12345-abcde",
        "metadata": {
            "title": "My record",
            "date": "2020-09-20",
        },
        "pids": {
            "oaiid": {"value": "", "provider": "local"},
        },
    }


@pytest.fixture()
def es_hit():
    """Example record used for tests."""
    return {
        "_index": "testindex",
        "_id": "4beb3b3e-a935-442e-a47b-6d386947ea20",
        "_version": 5,
        "_seq_no": 0,
        "_primary_term": 1,
        "found": True,
        "_source": {
            "uuid": "4beb3b3e-a935-442e-a47b-6d386947ea20",
            "version_id": 4,
            "created": "2020-09-01T14:26:00+00:00",
            "updated": "2020-09-02T14:28:21.968149+00:00'",
            "id": "12345-abcde",
            "metadata": {
                "title": "My record",
                "date": "2020-09-20",
            },
            "pids": {
                "oaiid": {"value": "", "provider": "local"},
            },
        },
    }


def test_esdumper_without_model(testapp, db, example_data):
    """Test the Search dumper."""
    # Dump without a model.
    dump = Record(example_data).dumps(dumper=SearchDumper())
    for k in ["uuid", "version_id", "created", "updated"]:
        assert dump[k] is None  # keys is set to none without a model
    # Load without a model defined
    record = Record.loads(dump, loader=SearchDumper())
    assert record.model is None  # model will not be set
    assert record == example_data  # data is equivalent to initial data


def test_esdumper_with_model(testapp, db, example_data):
    """Test the Search dumper."""
    # Create a record
    record = Record.create(example_data)
    db.session.commit()

    # Dump it
    dump = record.dumps(dumper=SearchDumper())
    assert dump["uuid"] == str(record.id)
    assert dump["version_id"] == record.revision_id + 1
    assert dump["created"][:19] == record.created.isoformat()[:19]
    assert dump["updated"][:19] == record.updated.isoformat()[:19]

    # Load it
    new_record = Record.loads(dump, loader=SearchDumper())
    assert new_record == record
    assert new_record.id == record.id
    assert new_record.revision_id == record.revision_id
    assert new_record.created == record.created
    assert new_record.updated == record.updated
    assert new_record.model.json == record.model.json


def test_esdumper_with_extensions(testapp, db, example_data):
    """Test extensions implementation."""

    # Create a simple extension that adds a computed field.
    class TestExt(SearchDumperExt):
        def dump(self, record, data):
            data["count"] = len(data["mylist"])

        def load(self, data, record_cls):
            data.pop("count")

    dumper = SearchDumper(extensions=[TestExt()])

    # Create the record
    record = Record.create({"mylist": ["a", "b"]})
    db.session.commit()

    # Dump it
    dump = record.dumps(dumper=dumper)
    assert dump["count"] == 2

    # Load it
    new_record = Record.loads(dump, loader=dumper)
    assert "count" not in new_record


def test_esdumper_sa_datatypes(testapp, database):
    """Test to determine the data type of an SQLAlchemy field."""
    db = database

    class Model(db.Model, RecordMetadataBase):
        string = db.Column(db.String(255))
        text = db.Column(db.Text)
        biginteger = db.Column(db.BigInteger)
        integer = db.Column(db.Integer)
        boolean = db.Column(db.Boolean(name="boolean"))
        text_variant = db.Column(db.Text().with_variant(mysql.VARCHAR(255), "mysql"))

    assert SearchDumper._sa_type(Model, "biginteger") == int
    assert SearchDumper._sa_type(Model, "boolean") == bool
    assert SearchDumper._sa_type(Model, "created") == datetime
    assert SearchDumper._sa_type(Model, "id") == UUID
    assert SearchDumper._sa_type(Model, "integer") == int
    assert SearchDumper._sa_type(Model, "json") == dict
    assert SearchDumper._sa_type(Model, "text_variant") == str
    assert SearchDumper._sa_type(Model, "text") == str
    assert SearchDumper._sa_type(Model, "updated") == datetime
    assert SearchDumper._sa_type(Model, "invalid") is None


def test_relations_dumper(testapp, db, example_data):
    """Test relations dumper extension."""

    class RecordWithRelations(Record):
        relations = RelationsField(
            language=PKRelation(
                key="language", keys=["iso", "information.ethnicity"], record_cls=Record
            ),
            languages=PKListRelation(
                key="languages",
                keys=["iso", "information.ethnicity"],
                record_cls=Record,
            ),
        )

        dumper = SearchDumper(extensions=[RelationDumperExt("relations")])

    # Create the record
    en_language = Record.create(
        {
            "title": "English",
            "iso": "en",
            "information": {"native_speakers": "400 million", "ethnicity": "English"},
        }
    )
    fr_language = Record.create(
        {
            "title": "French",
            "iso": "fr",
            "information": {"native_speakers": "76.8 million", "ethnicity": "French"},
        }
    )
    db.session.commit()
    record = RecordWithRelations.create(
        {
            "foo": "bar",
            "mylist": ["a", "b"],
        }
    )
    record.relations.language = en_language
    record.relations.languages = [en_language, fr_language]
    db.session.commit()

    # Dump it
    dump = record.dumps()
    assert dump["foo"] == "bar"
    assert dump["mylist"] == ["a", "b"]
    assert dump["language"] == {
        "id": str(en_language.id),
        "iso": "en",
        "information": {"ethnicity": "English"},
        "@v": str(en_language.id) + "::" + str(en_language.revision_id),
    }
    assert dump["languages"] == [
        {
            "id": str(en_language.id),
            "iso": "en",
            "information": {"ethnicity": "English"},
            "@v": str(en_language.id) + "::" + str(en_language.revision_id),
        },
        {
            "id": str(fr_language.id),
            "iso": "fr",
            "information": {"ethnicity": "French"},
            "@v": str(fr_language.id) + "::" + str(fr_language.revision_id),
        },
    ]
    assert dump["uuid"] == str(record.id)
    assert dump["version_id"] == record.revision_id + 1
    assert dump["created"][:19] == record.created.isoformat()[:19]
    assert dump["updated"][:19] == record.updated.isoformat()[:19]

    # TODO: Implement loader
    # Load it
    # new_record = Record.loads(dump, loader=dumper)
    # assert 'count' not in new_record


def test_indexedtime_dumper(testapp, db, example_data):
    """Test relations dumper extension."""

    class RecordWithIndexedTime(Record):
        dumper = SearchDumper(extensions=[IndexedAtDumperExt()])

    # create the record
    record = RecordWithIndexedTime.create(
        {
            "foo": "bar",
            "mylist": ["a", "b"],
        }
    )
    db.session.commit()

    # dump it
    dump = record.dumps()
    assert dump["foo"] == "bar"
    assert dump["mylist"] == ["a", "b"]
    assert dump["uuid"] == str(record.id)
    assert dump["version_id"] == record.revision_id + 1
    assert dump["created"][:19] == record.created.isoformat()[:19]
    assert dump["updated"][:19] == record.updated.isoformat()[:19]
    # only feasible to check the date (not time)
    assert dump["indexed_at"][:19] == record.created.isoformat()[:19]

    # load it
    new_record = RecordWithIndexedTime.loads(dump)
    assert "indexed_at" not in new_record
