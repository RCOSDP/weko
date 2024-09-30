# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
# Copyright (C) 2021 RERO.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test for system fields."""

import pytest

from invenio_records.api import Record
from invenio_records.dumpers import SearchDumper
from invenio_records.systemfields import (
    ConstantField,
    DictField,
    SystemField,
    SystemFieldsMixin,
)


#
# Fixtures
#
@pytest.fixture()
def testschema():
    """The JSONSchema used for tests."""
    return {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
        },
        "required": ["title"],
    }


@pytest.fixture()
def SystemRecord():
    """System record is a base class."""

    class SystemRecord(Record, SystemFieldsMixin):
        # Only defined in SystemRecord:
        test = ConstantField("test", "test")
        # Defined in both SystemRecord and MyRecord:
        base = ConstantField("base", "systemrecord")

    return SystemRecord


@pytest.fixture()
def MyRecord(SystemRecord, testschema):
    """My record class inheriting from SystemRecord."""

    class MyRecord(SystemRecord):
        # Defined in only MyRecord
        schema = ConstantField("$schema", testschema)
        # Defined in both SystemRecord and MyRecord
        base = ConstantField("base", "myrecord")

    return MyRecord


@pytest.fixture()
def record(MyRecord, db):
    """Create a record instance of MyRecord."""
    return MyRecord.create({"title": "test"})


@pytest.fixture()
def sysrecord(SystemRecord, db):
    """Create a record instance of SystemRecord."""
    return SystemRecord.create({"title": "test"})


@pytest.fixture()
def ExtensionRecord():
    """Create an ExtensionRecord class to test extensions being called."""

    class ExtensionField(SystemField):
        called = []

        def pre_init(self, record, data, model=None, **kwargs):
            self.called.append("pre_init")

        def post_init(self, record, data, model=None, field_data=None):
            self.called.append("post_init")

        def pre_dump(self, record, dumper=None):
            self.called.append("pre_dump")

        def post_load(self, record, loader=None):
            self.called.append("post_load")

        def pre_create(self, record):
            self.called.append("pre_create")

        def post_create(self, record):
            self.called.append("post_create")

        def pre_commit(self, record):
            self.called.append("pre_commit")

        def post_commit(self, record):
            self.called.append("post_commit")

        def pre_delete(self, record, force=False):
            self.called.append("pre_delete")

        def post_delete(self, record, force=False):
            self.called.append("post_delete")

        def pre_revert(self, record, revision):
            self.called.append("pre_revert")

        def post_revert(self, new_record, revision):
            self.called.append("post_revert")

    class ExtensionRecord(Record, SystemFieldsMixin):
        dumper = SearchDumper()
        ext = ExtensionField()

    return ExtensionRecord


#
# Tests
#
def test_constant_field(testapp, record, MyRecord, testschema):
    """Test the constant field."""
    # Test that constant field value was set, and is accessible
    assert record["$schema"] == testschema
    assert record.schema == testschema

    # Test that constant fields cannot have values assigned.
    try:
        record.schema = testschema
        assert False
    except AttributeError:
        pass

    # Explicit remove the set value ($schema) after the record creation.
    record = MyRecord({"title": "test"})
    del record["$schema"]

    # Now test, that accessing the field returns None.
    assert record.schema is None


def test_constant_field_deletion(testapp, db, record, MyRecord, testschema):
    """Test the constant field."""
    # Test that constant field value was set, and is accessible
    db.session.commit()
    record.delete()
    db.session.commit()

    record = MyRecord.get_record(record.id, with_deleted=True)
    assert record.schema is None


def test_field_overwriting(testapp, record, sysrecord):
    """Test that field overwriting."""
    # field 'base' is defined in both classes, thus MyRecord overwrites
    # SystemRecord.
    assert record.base == "myrecord"
    assert sysrecord.base == "systemrecord"


def test_field_inheritance(testapp, record, sysrecord):
    """Test that field inheritance."""
    # field 'test' is defined only in base class, but available on both.
    assert record.test == "test"
    assert sysrecord.test == "test"


def test_field_class_access(testapp, MyRecord):
    """Test that class access is returning the field."""
    assert isinstance(MyRecord.schema, ConstantField)
    assert isinstance(MyRecord.test, ConstantField)
    assert isinstance(MyRecord.base, ConstantField)


def test_attrname_injection(testapp, MyRecord):
    """Test that class access is returning the field."""
    assert MyRecord.schema.attr_name == "schema"
    assert MyRecord.test.attr_name == "test"
    assert MyRecord.base.attr_name == "base"


def test_systemfields_mro(testapp):
    """Test overwriting of system fields according to MRO."""

    class A(Record, SystemFieldsMixin):
        test = ConstantField("test", "a")

    class B(A):
        test = ConstantField("test", "b")

    class C(A):
        pass

    class D(B, C):
        test = ConstantField("test", "d")

    class E(B, C):
        pass

    class F(C):
        pass

    class G(C, B):
        pass

    # A defines field itself
    assert A({}).test == "a"
    # B inherits from A  (overwrites field)
    assert B({}).test == "b"
    # C inherits from A
    assert C({}).test == "a"
    # D inherits from B and C (overwrites field)
    assert D({}).test == "d"
    # E inherits from B and C
    assert E({}).test == "b"
    # F inherits from C which inherits from A.
    assert F({}).test == "a"
    # G inherits from C (which inherits from A) and B.
    assert G({}).test == "b"


def test_extension_pre_init(testapp, db, ExtensionRecord):
    """Test pre init hook."""
    rec = ExtensionRecord({})
    assert ExtensionRecord.ext.called == ["pre_init", "post_init"]


def test_extension_post_create(testapp, db, ExtensionRecord):
    """Test post create hook."""
    rec = ExtensionRecord.create({})
    assert ExtensionRecord.ext.called == [
        "pre_init",
        "post_init",
        "pre_create",
        "post_create",
    ]


def test_extension_pre_dump(testapp, db, ExtensionRecord):
    """Test pre dump hook."""
    rec = ExtensionRecord({}).dumps()
    assert ExtensionRecord.ext.called == ["pre_init", "post_init", "pre_dump"]


def test_extension_post_load(testapp, db, ExtensionRecord):
    """Test post load hook."""
    dump = ExtensionRecord({}).dumps()
    rec = ExtensionRecord.loads(dump)
    assert ExtensionRecord.ext.called == [
        "pre_init",
        "post_init",
        "pre_dump",
        "pre_init",
        "post_init",
        "post_load",
    ]


def test_extension_commit(testapp, db, ExtensionRecord):
    """Test commit hooks."""
    rec = ExtensionRecord.create({})
    rec.commit()
    assert ExtensionRecord.ext.called == [
        "pre_init",
        "post_init",
        "pre_create",
        "post_create",
        "pre_commit",
        "post_commit",
    ]


def test_extension_delete(testapp, db, ExtensionRecord):
    """Test pre/post delete hook."""
    rec = ExtensionRecord.create({})
    db.session.commit()
    rec.delete()
    assert ExtensionRecord.ext.called == [
        "pre_init",
        "post_init",
        "pre_create",
        "post_create",
        "pre_delete",
        "post_delete",
    ]


def test_extension_revert(testapp, database, ExtensionRecord):
    """Test pre/post revert hook."""
    db = database
    rec = ExtensionRecord.create({})
    db.session.commit()
    rec.commit()
    db.session.commit()
    assert rec.revision_id == 1
    rec.revert(0)
    assert ExtensionRecord.ext.called == [
        "pre_init",
        "post_init",
        "pre_create",
        "post_create",
        "pre_commit",
        "post_commit",
        "pre_revert",
        "pre_init",
        "post_init",
        "post_revert",
    ]


def test_base_systemfield_base(testapp):
    """Test default implementation of system field."""

    class TestRecord(Record, SystemFieldsMixin):
        field = SystemField()

    # Test to please the test coverage gods
    assert pytest.raises(AttributeError, getattr, TestRecord({}), "field")
    # A core system field doesn't support assignment, so you can't pass args
    # in constructor as well
    assert pytest.raises(AttributeError, TestRecord, {}, field={})


def test_systemfield_initialization(testapp):
    """Test default implementation of system field."""

    class TestField(SystemField):
        def __set__(self, instance, value):
            instance["arg_value"] = value

    class TestRecord(Record, SystemFieldsMixin):
        afield = TestField()

    # Init method
    assert TestRecord({}, afield="testval")["arg_value"] == "testval"

    # Create method
    record = TestRecord.create({}, afield="testval")
    assert record["arg_value"] == "testval"


def test_default_key(testapp):
    """Test default key name."""

    class TestRecord(Record, SystemFieldsMixin):
        afield = ConstantField(value="test")

    assert TestRecord({})["afield"] == "test"


#
# DictField
#
def test_dict_field_simple():
    """Simple tests for the DictField."""

    class Record1(Record, SystemFieldsMixin):
        metadata = DictField("metadata")

    assert isinstance(Record1.metadata, DictField)

    # Creation
    assert Record1({}, metadata={"title": 1}) == {"metadata": {"title": 1}}
    # Access key exists
    assert Record1({"metadata": {"title": 1}}).metadata == {"title": 1}
    # Access key doesn't exists
    assert Record1({}).metadata is None

    # Double tap - metadata wins over default data.
    assert Record1({"metadata": {"title": 2}, "a": "b"}, metadata={"title": 1}) == {
        "metadata": {"title": 1},
        "a": "b",
    }


def test_dictfield_default_key(testapp):
    """Test default key name."""

    class TestRecord(Record, SystemFieldsMixin):
        afield = DictField()

    assert TestRecord({}, afield={"test": 1})["afield"] == {"test": 1}


def test_dict_field_complex_key():
    """More complex tests for the DictField."""

    class Record1(Record, SystemFieldsMixin):
        metadata = DictField("metadata.a.b")

    # Creation
    record = Record1({}, metadata={"title": 1})
    assert record == {"metadata": {"a": {"b": {"title": 1}}}}
    # Access key exists
    assert record.metadata == {"title": 1}
    # Access key doesn't exists
    assert Record1({}).metadata is None

    # Cannot handle lists
    pytest.raises(KeyError, Record1, {"metadata": []}, metadata={"title": 1})
    pytest.raises(KeyError, Record1, {"metadata": {"a": []}}, metadata={"title": 1})


def test_dict_field_create_if_missing():
    """More complex tests for the DictField."""

    class Record1(Record, SystemFieldsMixin):
        metadata = DictField("metadata.a.b", create_if_missing=False)

    # If subkey doesn't exists, it fails with create_if_missing=False
    pytest.raises(KeyError, Record1, {}, metadata={"title": 1})
    pytest.raises(KeyError, Record1, {"metadata": []}, metadata={"title": 1})
    # Subkey exists, all good:
    assert Record1({"metadata": {"a": {}}}, metadata={"title": 1})


def test_dict_field_clear_none():
    """Test dict field with clearing none/empty values."""

    class Record1(Record, SystemFieldsMixin):
        metadata = DictField("metadata", clear_none=True)

    record = Record1({"a": None}, metadata={"a": None, "title": 1, "b": {"c": None}})
    assert record == {"a": None, "metadata": {"title": 1}}

    record = Record1({}, metadata={"a": None})
    assert record == {"metadata": {}}


def test_dict_field_deleted(testapp, database):
    """Test dict field with clearing none/empty values."""
    db = database

    class Record1(Record, SystemFieldsMixin):
        metadata = DictField()

    record = Record1.create({}, metadata={"title": 1})
    db.session.commit()
    record.delete()
    db.session.commit()

    # Loading a deleted record
    record = Record1.get_record(record.id, with_deleted=True)
    assert record.metadata is None
