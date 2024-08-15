# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test Invenio Records API."""


import copy
import uuid
from datetime import datetime, timedelta

import pytest
from jsonresolver import JSONResolver
from jsonresolver.contrib.jsonref import json_loader_factory
from jsonschema import FormatChecker
from jsonschema.exceptions import ValidationError
from sqlalchemy.orm.exc import NoResultFound

from invenio_records import Record
from invenio_records.errors import MissingModelError
from invenio_records.models import RecordMetadata
from invenio_records.validators import PartialDraft4Validator


def strip_ms(dt):
    """Strip microseconds."""
    return dt - timedelta(microseconds=dt.microsecond)


def test_get_records(testapp, db):
    """Test bulk record fetching."""
    # Create test records
    test_records = [
        Record.create({"title": "test1"}),
        Record.create({"title": "to_be_deleted"}),
        Record.create({"title": "test3"}),
    ]
    db.session.commit()
    test_ids = [record.id for record in test_records]

    # Fetch test records
    assert len(Record.get_records(test_ids)) == 3

    test_records[1].delete()

    # should not show deleted
    db.session.commit()
    assert len(Record.get_records(test_ids)) == 2

    # should show deleted
    assert len(Record.get_records(test_ids, with_deleted=True)) == 3


def test_revision_id_created_updated_properties(testapp, db):
    """Test properties."""
    record = Record.create({"title": "test"})
    assert record.revision_id == 0
    dt_c = record.created
    assert dt_c
    dt_u = record.updated
    assert dt_u
    record["title"] = "test 2"
    record.commit()
    db.session.commit()
    assert record.revision_id == 1
    assert strip_ms(record.created) == strip_ms(dt_c)
    assert strip_ms(record.updated) >= strip_ms(dt_u)

    assert dt_u.tzinfo is None
    utcnow = datetime.utcnow()
    assert dt_u > utcnow - timedelta(seconds=10)
    assert dt_u < utcnow + timedelta(seconds=10)


def test_delete(testapp, database):
    """Test delete a record."""
    db = database
    # Create a record, revise it and delete it.
    record = Record.create({"title": "test 1"})
    db.session.commit()
    record["title"] = "test 2"
    record.commit()
    db.session.commit()
    record.delete()
    db.session.commit()

    # Deleted records a not retrievable by default
    pytest.raises(NoResultFound, Record.get_record, record.id)

    # Deleted records can be retrieved if you explicit request it
    record = Record.get_record(record.id, with_deleted=True)

    # Deleted records are empty
    assert record == {}
    assert record.model.json is None

    # Deleted records *cannot* be modified
    record["title"] = "deleted"
    assert pytest.raises(MissingModelError, record.commit)

    # Deleted records *can* be reverted
    record = record.revert(-2)
    assert record["title"] == "test 2"
    db.session.commit()

    # The "undeleted" record can now be retrieve again
    record = Record.get_record(record.id)
    assert record["title"] == "test 2"

    # Force deleted record cannot be retrieved again
    record.delete(force=True)
    db.session.commit()
    pytest.raises(NoResultFound, Record.get_record, record.id, with_deleted=True)


def test_revisions(testapp, database):
    """Test revisions."""
    db = database
    # Create a record and make modifications to it.
    record = Record.create({"title": "test 1"})
    rec_uuid = record.id
    db.session.commit()
    record["title"] = "test 2"
    record.commit()
    db.session.commit()
    record["title"] = "test 3"
    record.commit()
    db.session.commit()

    # Get the record
    record = Record.get_record(rec_uuid)
    assert record["title"] == "test 3"
    assert record.revision_id == 2

    # Retrieve specific revisions
    rev1 = record.revisions[0]
    assert rev1["title"] == "test 1"
    assert rev1.revision_id == 0

    rev2 = record.revisions[1]
    assert rev2["title"] == "test 2"
    assert rev2.revision_id == 1

    # Latest revision is identical to record.
    rev_latest = record.revisions[-1]
    assert dict(rev_latest) == dict(record)

    # Revert to a specific revision
    record = record.revert(rev1.revision_id)
    assert record["title"] == "test 1"
    assert record.created == rev1.created
    assert record.updated != rev1.updated
    assert record.revision_id == 3
    db.session.commit()

    # Get the record again and check it
    record = Record.get_record(rec_uuid)
    assert record["title"] == "test 1"
    assert record.revision_id == 3

    # Make a change and ensure revision id is changed as well.
    record["title"] = "modification"
    record.commit()
    db.session.commit()
    assert record.revision_id == 4

    # Iterate over revisions
    assert len(record.revisions) == 5
    revs = list(record.revisions)
    assert revs[0]["title"] == "test 1"
    assert revs[1]["title"] == "test 2"
    assert revs[2]["title"] == "test 3"
    assert revs[3]["title"] == "test 1"
    assert revs[4]["title"] == "modification"

    assert 2 in record.revisions
    assert 5 not in record.revisions


def test_retrieve_proper_revision(testapp, database):
    """Check accessing revision with gaps

    Test checks if it's possible to access proper revision
    when revision numbers have 'gaps'
    """
    db = database
    record = Record.create({"title": "test 1"})
    db.session.commit()
    record["title"] = "test 2"
    record.commit()
    record["title"] = "test 3"
    record.commit()
    db.session.commit()
    record["title"] = "test 4"
    record.commit()
    db.session.commit()
    record["title"] = "test 5"
    record.commit()
    db.session.commit()

    assert len(record.revisions) == 4
    revs = list(record.revisions)
    assert revs[0]["title"] == "test 1"
    assert revs[0].revision_id == 0
    assert revs[1]["title"] == "test 3"
    assert revs[1].revision_id == 2
    assert revs[2]["title"] == "test 4"
    assert revs[2].revision_id == 3
    assert revs[3]["title"] == "test 5"
    assert revs[3].revision_id == 4

    # Access revision by revision_id
    rev_2 = record.revisions[2]
    assert rev_2["title"] == "test 3"
    assert rev_2.revision_id == 2

    # Access revision by negative list index
    assert rev_2 == record.revisions[-3]


def test_record_update_mutable(testapp, database):
    """Test updating mutables in a record."""
    db = database
    recid = uuid.UUID("262d2748-ba41-456f-a844-4d043a419a6f")

    # Create a new record with two mutables, a list and a dict
    rec = Record.create(
        {
            "title": "Title",
            "list": [
                "foo",
            ],
            "dict": {"moo": "boo"},
        },
        id_=recid,
    )
    # Make sure mutables are there before and after commit
    assert rec == {
        "title": "Title",
        "list": [
            "foo",
        ],
        "dict": {"moo": "boo"},
    }
    db.session.commit()
    db.session.expunge_all()
    rec = Record.get_record(recid)
    assert rec == {
        "title": "Title",
        "list": [
            "foo",
        ],
        "dict": {"moo": "boo"},
    }

    # Set the mutables under key
    rec["list"] = [
        "bar",
    ]
    rec["dict"] = {"eggs": "bacon"}
    rec.commit()
    # Make sure it commits to DB
    assert rec == {
        "title": "Title",
        "list": [
            "bar",
        ],
        "dict": {"eggs": "bacon"},
    }
    db.session.commit()
    db.session.expunge_all()
    rec = Record.get_record(recid)
    assert rec == {
        "title": "Title",
        "list": [
            "bar",
        ],
        "dict": {"eggs": "bacon"},
    }

    # Update the mutables under key
    rec["list"].append("spam")
    rec["dict"]["ham"] = "chicken"
    rec.commit()
    # Make sure it commits to DB
    assert rec == {
        "title": "Title",
        "list": ["bar", "spam"],
        "dict": {"eggs": "bacon", "ham": "chicken"},
    }
    db.session.commit()
    db.session.expunge_all()
    rec = Record.get_record(recid)
    assert rec == {
        "title": "Title",
        "list": ["bar", "spam"],
        "dict": {"eggs": "bacon", "ham": "chicken"},
    }


def test_missing_model(testapp, db):
    """Test revisions."""
    record = Record({})
    assert record.id is None
    assert record.revision_id is None
    assert record.created is None
    assert record.updated is None

    try:
        record.revisions
        assert False
    except MissingModelError:
        assert True

    pytest.raises(MissingModelError, record.commit)
    pytest.raises(MissingModelError, record.delete)
    pytest.raises(MissingModelError, record.revert, -1)


def test_record_replace_refs(testapp, db):
    """Test the replacement of JSON references using JSONResolver."""
    record = Record.create(
        {"one": {"$ref": "http://nest.ed/A"}, "three": {"$ref": "http://nest.ed/ABC"}}
    )
    testapp.extensions["invenio-records"].loader_cls = json_loader_factory(
        JSONResolver(plugins=["demo.json_resolver"])
    )

    record.enable_jsonref = False
    assert record.replace_refs() == record

    record.enable_jsonref = True
    out_json = record.replace_refs()
    assert out_json != record

    expected_json = {
        "one": {
            "letter": "A",
            "next": ".",
        },
        "three": {
            "letter": "A",
            "next": {
                "letter": "B",
                "next": {
                    "letter": "C",
                    "next": ".",
                },
            },
        },
    }
    assert out_json == expected_json


def test_replace_refs_deepcopy(testapp):
    """Test problem with replace_refs and deepcopy."""
    with testapp.app_context():
        assert copy.deepcopy(Record({"recid": 1}).replace_refs()) == {"recid": 1}


def test_record_dump(testapp, db):
    """Test record dump method."""
    with testapp.app_context():
        record = Record.create(
            {
                "foo": {
                    "bar": "Bazz",
                },
            }
        )
        record_dump = record.dumps()
        record_dump["foo"]["bar"] = "Spam"
        assert record_dump["foo"]["bar"] != record["foo"]["bar"]


def test_default_format_checker(testapp):
    """Test a default format checker."""
    checker = FormatChecker()
    checker.checks("foo")(lambda el: el.startswith("foo"))
    data = {
        # The key 'bar' will fail validation if the format checker is used.
        "bar": "bar",
        "$schema": {"properties": {"bar": {"format": "foo"}}},
    }

    class CustomRecord(Record):
        format_checker = checker

    assert pytest.raises(ValidationError, CustomRecord(data).validate)


def test_validate_with_format(testapp, db):
    """Test that validation can accept custom format rules."""
    with testapp.app_context():
        checker = FormatChecker()
        checker.checks("foo")(lambda el: el.startswith("foo"))
        data = {"bar": "foo", "$schema": {"properties": {"bar": {"format": "foo"}}}}

        # test record creation with valid data
        assert data == Record.create(data)
        record = Record.create(data, format_checker=checker)
        # test direct call to validate with valid data
        assert record.validate(format_checker=checker) is None
        # test commit with valid data
        record.commit(format_checker=checker)

        record["bar"] = "bar"
        # test direct call to validate with invalid data
        with pytest.raises(ValidationError) as excinfo:
            record.validate(format_checker=checker)
        assert "'bar' is not a 'foo'" in str(excinfo.value)
        # test commit with invalid data
        with pytest.raises(ValidationError) as excinfo:
            record.commit(format_checker=checker)
        assert "'bar' is not a 'foo'" in str(excinfo.value)

        data["bar"] = "bar"
        # test record creation with invalid data
        with pytest.raises(ValidationError) as excinfo:
            record = Record.create(data, format_checker=checker)
        assert "'bar' is not a 'foo'" in str(excinfo.value)


def test_validate_partial(testapp, db):
    """Test partial validation."""
    schema = {
        "properties": {
            "a": {"type": "string"},
            "b": {"type": "string"},
        },
        "required": ["b"],
    }
    data = {"a": "hello", "$schema": schema}
    with testapp.app_context():
        # Test validation on create()

        # normal validation should fail because 'b' is required
        with pytest.raises(ValidationError) as exc_info:
            Record.create(data)
        assert "'b' is a required property" == exc_info.value.message
        # validate with a less restrictive validator
        record = Record.create(data, validator=PartialDraft4Validator)
        # set wrong data types should fails in any case
        data_incorrect = copy.deepcopy(data)
        data_incorrect["a"] = 1
        with pytest.raises(ValidationError) as exc_info:
            Record.create(data_incorrect, validator=PartialDraft4Validator)
        assert "1 is not of type 'string'" == exc_info.value.message

        # Test validation on commit()

        # validation not passing with normal validator
        with pytest.raises(ValidationError) as exc_info:
            record.commit()
        assert "'b' is a required property" == exc_info.value.message
        # validation passing with less restrictive validator
        assert data == record.commit(validator=PartialDraft4Validator)
        # set wrong data types should fails in any case
        record["a"] = 1
        with pytest.raises(ValidationError) as exc_info:
            record.commit(validator=PartialDraft4Validator)


def test_reversed_works_for_revisions(testapp, database):
    db = database
    record = Record.create({"title": "test 1"})
    db.session.commit()

    record["title"] = "test 2"
    record.commit()
    record["title"] = "Test 3"
    db.session.commit()

    record["title"] = "test 4"
    record.commit()
    db.session.commit()

    reversed_revisions = list(reversed(record.revisions))
    reversed_revisions[0].revision_id == 3
    reversed_revisions[1].revision_id == 1
    reversed_revisions[2].revision_id == 0


def test_clear_none(testapp, db):
    """Test clear_none."""
    record = Record({"a": None})
    record.clear_none()
    assert record == {}


def test_undelete_no_get(testapp, db):
    """Test undelete a record."""
    record = Record.create({"title": "test"})
    db.session.commit()
    record.delete()
    db.session.commit()
    record.undelete()
    record.commit()
    db.session.commit()
    assert record == {"title": "test"}


def test_undelete_with_get(testapp, db):
    """Test undelete a record."""
    record = Record.create({"title": "test"})
    db.session.commit()
    record.delete()
    db.session.commit()
    record = Record.get_record(record.id, with_deleted=True)
    record.undelete()
    record.commit()
    db.session.commit()
    assert record == {}
