# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test Invenio Records."""

from copy import copy
from datetime import date, timedelta

import pytest
from jsonschema.exceptions import ValidationError

from invenio_records import Record


@pytest.fixture()
def encoder():
    """Return a simple encoder."""

    class CustomEncoder:
        @classmethod
        def encode(cls, data):
            if "date" in data.get("nested", {}):
                data["nested"]["date"] = data["nested"]["date"].isoformat()
            return data

        @classmethod
        def decode(cls, data):
            if "date" in data.get("nested", {}):
                datestr = data["nested"]["date"]
                data["nested"]["date"] = date(
                    int(datestr[0:4]),
                    int(datestr[5:7]),
                    int(datestr[8:10]),
                )
            return data

    return CustomEncoder


@pytest.fixture()
def schema():
    """A test schema."""
    return {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "nested": {"type": "object", "properties": {"date": {"type": "string"}}},
        },
    }


@pytest.fixture()
def testdate():
    """A test date."""
    return date(2020, 9, 3)


@pytest.fixture()
def testdatestr(testdate):
    """Test date as a string."""
    return testdate.isoformat()


@pytest.fixture()
def record_cls(encoder):
    """Mock the record class with an encoder."""
    Record.model_cls.encoder = encoder
    yield Record
    Record.model_cls.encoder = None


def test_noencoding(testapp, db, record_cls):
    """Simple sanity check."""
    data = {"title": "Title"}
    rec = record_cls.create(data)
    assert dict(rec) == rec.model.json
    assert rec.model.data == rec.model.json


def test_encoding(testapp, db, record_cls, testdate, testdatestr):
    """Test encoding/decoding in custom classes."""
    # Create a record with a Python date inside (record_cls has an encoder
    # which will encode/decode the "date" field if present).
    data = {"title": "Title", "nested": {"date": testdate}}
    rec = record_cls.create(data)
    db.session.commit()

    # Record and data should still hold a python date
    assert data["nested"]["date"] == testdate
    assert rec["nested"]["date"] == testdate

    # The underlying model JSON field should have a string instead.
    assert rec.model.json["nested"]["date"] == testdatestr

    # Decoding the data: Get the record again
    rec = record_cls.get_record(rec.id)

    # Record and data should still hold a python date
    assert rec["nested"]["date"] == testdate

    # The underlying model JSON field should have a string instead.
    assert rec.model.json["nested"]["date"] == testdatestr


def test_encoding_with_versioning(testapp, database, record_cls, testdate):
    """Test reverting a revision."""
    db = database
    # Create a record and a new revision
    rec = record_cls.create({"title": "Title", "nested": {"date": testdate}})
    db.session.commit()

    # Change record (making a new revision)
    newdate = rec["nested"]["date"] + timedelta(days=1)
    rec["nested"]["date"] = newdate
    rec.commit()
    db.session.commit()

    # Record and model should have the new date.
    assert rec["nested"]["date"] == newdate
    assert rec.model.json["nested"]["date"] == newdate.isoformat()

    # Now revert the record and check against initial date.
    rec = rec.revert(0)
    assert rec["nested"]["date"] == testdate
    assert rec.model.json["nested"]["date"] == testdate.isoformat()


def test_encoding_with_schema(testapp, database, record_cls, testdate, schema):
    """Test that schema validation works on JSON, not on dict."""
    db = database

    # Create a record
    rec = record_cls.create(
        {
            "$schema": schema,
            "title": "Title",
            "nested": {"date": testdate},
        }
    )
    db.session.commit()
    # No assertion: because JSONSchema validation will raise an Exception
    # if it fails to operate the date

    # Try on record update as well (since commit() also validates)
    newdate = rec["nested"]["date"] + timedelta(days=1)
    rec["nested"]["date"] = newdate
    rec.commit()
    db.session.commit()
    # No assertion: because JSONSchema validation will raise an Exception
    # if it fails to operate the date


def test_encoding_with_schema_fail(testapp, database, testdate, schema):
    """Test that validation fails when not using encoder."""
    db = database

    data = {
        "$schema": schema,
        "title": "Title",
        "nested": {"date": testdate},
    }

    assert pytest.raises(ValidationError, Record.create, data)

    # Create empty record so we can test Record.commit()
    rec = Record.create({})
    db.session.commit()

    rec.update(data)
    assert pytest.raises(ValidationError, rec.commit)
