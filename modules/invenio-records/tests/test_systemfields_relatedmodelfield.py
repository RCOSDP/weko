# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2021 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test for related model system fields."""

from collections import namedtuple
from copy import deepcopy

import pytest

from invenio_records.api import Record
from invenio_records.systemfields import (
    RelatedModelField,
    RelatedModelFieldContext,
    SystemFieldsMixin,
    relatedmodelfield,
)


#
# Fixtures
#
@pytest.fixture()
def patch_inspect(monkeypatch):
    """Monkey patch sqlalchemy.inspect"""
    # Used to avoid having to create DB tables
    MockResult = namedtuple("MockResult", ["persistent"])

    def mock_inspect(obj):
        return MockResult(persistent=getattr(obj, "persistent", False))

    monkeypatch.setattr(relatedmodelfield, "inspect", mock_inspect)

    return mock_inspect


@pytest.fixture()
def patch_db(monkeypatch):
    """Monkey patch session_merge"""

    # Used to avoid having to create DB tables
    class MockSession:
        @staticmethod
        def merge(obj):
            obj = deepcopy(obj)
            obj.persistent = True
            return obj

    class MockDb:
        session = MockSession

    monkeypatch.setattr(relatedmodelfield, "db", MockDb)


@pytest.fixture()
def MyModel():
    """Create a model class."""

    class MyModel:
        def __init__(self, val):
            self._val = val

        @classmethod
        def dump_obj(cls, field, record, obj):
            field.set_dictkey(record, {"akey": obj._val})

        @classmethod
        def load_obj(cls, field, record):
            data = field.get_dictkey(record)
            if data:
                return cls(data["akey"])
            return None

        def __eq__(self, o):
            return self._val == o._val

    return MyModel


@pytest.fixture()
def MyRecord(MyModel):
    """A record with a related model system field."""

    class MyRecord(Record, SystemFieldsMixin):
        myobj = RelatedModelField(MyModel)

    return MyRecord


#
# Tests
#
def test_field(MyRecord, MyModel):
    """Test class behaviour."""
    assert isinstance(MyRecord.myobj, RelatedModelFieldContext)


def test_setting_related_obj(testapp, db, MyRecord, MyModel):
    """Set the related object"""
    # via attr access
    record = MyRecord({})
    record.myobj = MyModel("a")
    assert record["myobj"] == {"akey": "a"}
    record.myobj = MyModel("b")
    assert record["myobj"] == {"akey": "b"}

    # via __init__() with a myobj argument
    record = MyRecord({}, myobj=MyModel("c"))
    assert record["myobj"] == {"akey": "c"}

    # via create() with a myobj argument
    record = MyRecord.create({}, myobj=MyModel("c"))
    assert record["myobj"] == {"akey": "c"}


def test_change_key(testapp, db, MyModel):
    """Change key where the record is stored."""

    class Record1(Record, SystemFieldsMixin):
        myobj = RelatedModelField(MyModel, key="custom")

    assert Record1({}, myobj=MyModel("a"))["custom"] == {"akey": "a"}


def test_custom_dump_load(testapp, db, MyModel):
    """Change custom dump/load function."""

    # A custom dumper function
    def my_dump(field, record, obj):
        field.set_dictkey(record, {"custom": obj._val})

    # A custom loader function
    def my_load(field, record):
        data = field.get_dictkey(record)
        if data:
            return MyModel(data["custom"])
        return None

    class Record1(Record, SystemFieldsMixin):
        myobj = RelatedModelField(MyModel, load=my_load, dump=my_dump)

    # Dumping
    record = Record1({}, myobj=MyModel("a"))
    assert record["myobj"] == {"custom": "a"}

    # Loading
    record = Record1(dict(record))
    assert record.myobj == MyModel("a")


def test_serialize_on_commit(testapp, db, MyRecord, MyModel):
    """Test serialize on commit."""
    obj = MyModel("a")
    record = MyRecord.create({}, myobj=obj)
    assert record["myobj"] == {"akey": "a"}

    # Change related object outside the APIs
    obj._val = "b"
    assert record["myobj"] == {"akey": "a"}

    # Now commit and check that latest value are serialized.
    record.commit()
    assert record["myobj"] == {"akey": "b"}


def test_required(testapp, db, MyModel, MyRecord):
    """Test required property."""

    class Record1(Record, SystemFieldsMixin):
        myobj = RelatedModelField(MyModel, required=True)

    # Test that an error is raised when required
    pytest.raises(RuntimeError, Record1.create({}).commit)
    # Test that no error is raised (MyRecord does not require the obj)
    assert MyRecord.create({}).commit() == {}


def test_field_context(MyModel):
    """Test the field context."""

    class MyFieldCtx(RelatedModelFieldContext):
        def test(self):
            return True

    class Record1(Record, SystemFieldsMixin):
        myobj = RelatedModelField(MyModel, context_cls=MyFieldCtx)

    assert Record1.myobj.test()


def test_ctx_session_merge(MyRecord, MyModel, patch_inspect, patch_db):
    """Test the session_merge."""
    record = MyRecord(dict(MyRecord({}, myobj=MyModel("a"))))
    assert patch_inspect(record.myobj).persistent is False
    MyRecord.myobj.session_merge(record)
    assert patch_inspect(record.myobj).persistent is True
