# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test Invenio Records."""

import json
import os
import uuid

import pytest
from flask import Flask
from invenio_db.utils import drop_alembic_version_table
from jsonschema.exceptions import ValidationError
from sqlalchemy.orm.exc import NoResultFound

from invenio_records import InvenioRecords, Record
from invenio_records.errors import MissingModelError


def test_version():
    """Test version import."""
    from invenio_records import __version__

    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask("testapp")
    ext = InvenioRecords(app)
    assert "invenio-records" in app.extensions

    app = Flask("testapp")
    ext = InvenioRecords()
    assert "invenio-records" not in app.extensions
    ext.init_app(app)
    assert "invenio-records" in app.extensions


def test_db(testapp, db):
    """Test database backend."""
    with testapp.app_context():
        assert "records_metadata" in db.metadata.tables
        assert "records_metadata_version" in db.metadata.tables
        assert "transaction" in db.metadata.tables

    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "field": {"type": "boolean"},
            "hello": {"type": "array"},
        },
        "required": ["title"],
    }
    data = {"title": "Test", "$schema": schema}
    from invenio_records.models import RecordMetadata as RM

    # Create a record
    with testapp.app_context():
        assert RM.query.count() == 0

        record_uuid = Record.create(data).id
        db.session.commit()

        assert RM.query.count() == 1
        db.session.commit()

    # Retrieve created record
    with testapp.app_context():
        record = Record.get_record(record_uuid)
        assert record.dumps() == data
        with pytest.raises(NoResultFound):
            Record.get_record(uuid.uuid4())
        record["field"] = True
        record = record.patch([{"op": "add", "path": "/hello", "value": ["world"]}])
        assert record["hello"] == ["world"]
        record.commit()
        db.session.commit()

    with testapp.app_context():
        record2 = Record.get_record(record_uuid)
        assert record2.model.version_id == 2
        assert record2["field"]
        assert record2["hello"] == ["world"]
        db.session.commit()

    # Cannot commit record without model (i.e. Record.create_record)
    with testapp.app_context():
        record3 = Record({"title": "Not possible"})
        with pytest.raises(MissingModelError):
            record3.commit()

    # Check invalid schema values
    with testapp.app_context():
        v_schema = {
            "$id": "https://example.com/geographical-location.schema.json",
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Longitude and Latitude Values",
            "description": "A geographical coordinate.",
            "required": ["latitude", "longitude"],
            "type": "object",
            "properties": {
                "latitude": {"type": "number", "minimum": -90, "maximum": 90},
                "longitude": {"type": "number", "minimum": -180, "maximum": 180},
            },
        }

        data = {
            "$schema": v_schema,
            "latitude": 42,
            "longitude": 42,
        }
        record_with_schema = Record.create(data).commit()
        db.session.commit()

        record_with_schema["latitude"] = "invalid"
        with pytest.raises(ValidationError):
            record_with_schema.commit()

    # Allow types overriding on schema validation
    with testapp.app_context():
        data = {"title": "Test", "hello": tuple(["foo", "bar"]), "$schema": schema}
        testapp.config["RECORDS_VALIDATION_TYPES"] = {}
        with pytest.raises(ValidationError):
            Record.create(data).commit()

        testapp.config["RECORDS_VALIDATION_TYPES"] = {"array": (list, tuple)}
        record_uuid = Record.create(data).commit()
        db.session.commit()
