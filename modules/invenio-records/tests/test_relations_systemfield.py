# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Tests for relations system field."""

from collections.abc import Iterable

import pytest

from invenio_records.api import Record
from invenio_records.systemfields import PKRelation, RelationsField, SystemFieldsMixin
from invenio_records.systemfields.relations import (
    InvalidRelationValue,
    PKListRelation,
    PKNestedListRelation,
    RelationsMapping,
)
from invenio_records.systemfields.relations.errors import InvalidCheckValue


def test_relations_field_pk_relation(testapp, db, languages):
    """RelationsField tests for PKRelation."""

    Language, languages = languages
    en_lang = languages["en"]
    fr_lang = languages["fr"]

    class Record1(Record, SystemFieldsMixin):
        relations = RelationsField(
            language=PKRelation(key="language", keys=["iso"], record_cls=Language),
        )

    # Class-field check
    assert isinstance(Record1.relations, RelationsField)
    assert isinstance(Record1.relations.language, PKRelation)

    # Empty initialization
    record = Record1({})
    assert record == {}
    assert isinstance(record.relations, RelationsMapping)
    assert callable(record.relations.language)
    assert record.relations.language() is None

    # Initialize from dictionary data
    record = Record1({"language": {"id": str(en_lang.id)}})
    res = record.relations.language()
    assert isinstance(res, Language)
    assert res == en_lang

    # Initialize from field data
    record = Record1({}, relations={"language": str(en_lang.id)})
    assert record["language"]["id"] == str(en_lang.id)
    res = record.relations.language()
    assert isinstance(res, Language)
    assert res == en_lang

    # Set via record data
    record = Record1.create({})
    record["language"] = {"id": str(en_lang.id)}
    res = record.relations.language()
    assert isinstance(res, Language)
    assert res == en_lang
    record.commit()  # validates
    res = record.relations.language()
    assert isinstance(res, Language)
    assert res == en_lang

    record["language"] = {"id": "invalid"}
    with pytest.raises(InvalidRelationValue):
        record.commit()  # fails validation

    # Set via attribute
    record = Record1.create({})
    record.relations.language = str(en_lang.id)
    assert record["language"]["id"] == str(en_lang.id)
    res = record.relations.language()
    assert isinstance(res, Language)
    assert res == en_lang

    # Update existing value
    record.relations.language = str(fr_lang.id)
    assert record["language"]["id"] == str(fr_lang.id)
    res = record.relations.language()
    assert isinstance(res, Language)
    assert res == fr_lang

    # Set invalid value
    with pytest.raises(InvalidRelationValue):
        record.relations.language = "invalid"
    # Check that old value is still there
    assert record["language"]["id"] == str(fr_lang.id)
    res = record.relations.language()
    assert isinstance(res, Language)
    assert res == fr_lang

    # Dereference relation
    record.relations.language.dereference()
    assert record["language"] == {
        "id": str(fr_lang.id),
        "iso": "fr",  # only stores the "iso" field
        "@v": str(fr_lang.id) + "::" + str(fr_lang.revision_id),
    }

    # Commit clean dereferened fields
    record.commit()
    assert record["language"] == {"id": str(fr_lang.id)}

    # Commit to DB and refetch
    db.session.commit()
    record = Record1.get_record(record.id)
    assert record["language"] == {"id": str(fr_lang.id)}
    res = record.relations.language()
    assert isinstance(res, Language)
    assert res == fr_lang

    # Clear field
    record.relations.language = None
    assert "language" not in record
    assert record.relations.language() is None
    record.commit()


def test_relations_field_pk_list_relation(testapp, db, languages):
    """RelationsField tests for PKListRelation."""

    Language, languages = languages
    en_lang = languages["en"]
    fr_lang = languages["fr"]
    es_lang = languages["es"]

    class Record1(Record, SystemFieldsMixin):
        relations = RelationsField(
            languages=PKListRelation(
                key="languages",
                keys=["iso", "information.ethnicity"],
                record_cls=Language,
            ),
        )

    # Class-field check
    assert isinstance(Record1.relations, RelationsField)
    assert isinstance(Record1.relations.languages, PKListRelation)

    # Empty initialization
    record = Record1({})
    assert record == {}
    assert isinstance(record.relations, RelationsMapping)
    assert callable(record.relations.languages)
    assert record.relations.languages() is None

    # Initialize from dictionary data
    record = Record1({"languages": [{"id": str(en_lang.id)}]})
    res_iter = record.relations.languages()
    assert isinstance(res_iter, Iterable)
    res = next(res_iter)
    assert res == en_lang

    # Initialize from field data
    record = Record1({}, relations={"languages": [str(en_lang.id)]})
    assert record["languages"] == [{"id": str(en_lang.id)}]
    res_iter = record.relations.languages()
    assert isinstance(res_iter, Iterable)
    res = next(res_iter)
    assert res == en_lang

    # Set via record dictionary data
    record = Record1.create({})
    record["languages"] = [{"id": str(en_lang.id)}]
    res_iter = record.relations.languages()
    assert isinstance(res_iter, Iterable)
    res = next(res_iter)
    assert res == en_lang
    record.commit()  # validates
    res_iter = record.relations.languages()
    assert isinstance(res_iter, Iterable)
    res = next(res_iter)
    assert res == en_lang
    record["languages"] = {"id": "invalid"}
    with pytest.raises(InvalidRelationValue):
        record.commit()  # fails validation

    # Set via attribute
    record = Record1.create({})
    record.relations.languages = [str(en_lang.id)]
    assert record["languages"][0]["id"] == str(en_lang.id)
    res_iter = record.relations.languages()
    assert isinstance(res_iter, Iterable)
    res = next(res_iter)
    assert res == en_lang

    # Update existing value
    record.relations.languages = [str(fr_lang.id)]
    assert record["languages"][0]["id"] == str(fr_lang.id)
    res_iter = record.relations.languages()
    assert isinstance(res_iter, Iterable)
    res = next(res_iter)
    assert res == fr_lang

    # Set invalid value
    for v in ("invalid", ["invalid"]):
        with pytest.raises(InvalidRelationValue):
            record.relations.languages = v
        # Check that old value is still there
        assert record["languages"][0]["id"] == str(fr_lang.id)
        res_iter = record.relations.languages()
        assert isinstance(res_iter, Iterable)
        res = next(res_iter)
        assert res == fr_lang

    # Dereference relation
    record.relations.languages.dereference()
    assert record["languages"] == [
        {
            "id": str(fr_lang.id),
            "iso": "fr",  # only stores the "iso" field
            "information": {"ethnicity": "French"},
            "@v": str(fr_lang.id) + "::" + str(fr_lang.revision_id),
        }
    ]

    # Commit clean dereferened fields
    record.commit()
    assert record["languages"] == [{"id": str(fr_lang.id)}]

    # Commit to DB and refetch
    db.session.commit()
    record = Record1.get_record(record.id)
    assert record["languages"] == [{"id": str(fr_lang.id)}]
    res_iter = record.relations.languages()
    assert isinstance(res_iter, Iterable)
    res = next(res_iter)
    assert res == fr_lang

    # Clear field
    record.relations.languages = None
    assert "languages" not in record
    assert record.relations.languages() is None
    record.commit()


def test_relations_field_pk_list_relation_of_objects(testapp, db, languages):
    """RelationsField tests for PKListRelation with a list of objects."""

    Language, languages = languages
    en_lang = languages["en"]
    fr_lang = languages["fr"]
    es_lang = languages["es"]

    class Record1(Record, SystemFieldsMixin):
        relations = RelationsField(
            array_of_objects=PKListRelation(
                key="array_of_objects",
                keys=["iso"],
                record_cls=Language,
                relation_field="language",
            ),
        )

    # Class-field check
    assert isinstance(Record1.relations, RelationsField)
    assert isinstance(Record1.relations.array_of_objects, PKListRelation)

    # Empty initialization
    record = Record1({})
    assert record == {}
    assert isinstance(record.relations, RelationsMapping)
    assert callable(record.relations.array_of_objects)
    assert record.relations.array_of_objects() is None

    # Initialize from dictionary data
    record = Record1(
        {
            "array_of_objects": [
                {
                    "field1": "no language",
                    "field2": "random string",
                    "field3": {"nestedField": "nested string"},
                },
                {"language": {"id": str(en_lang.id)}, "field1": "string"},
                {"language": {"id": str(fr_lang.id)}, "field2": "string2"},
                {"language": {"id": str(en_lang.id)}, "field1": "string"},
            ]
        }
    )

    res_iter = record.relations.array_of_objects()
    assert isinstance(res_iter, Iterable)
    res = next(res_iter)
    assert res == en_lang
    res = next(res_iter)
    assert res == fr_lang
    res = next(res_iter)
    assert res == en_lang

    # Initialize from field data
    record = Record1(
        {"metadata": {"title": "random title"}},
        relations={
            "array_of_objects": [
                {
                    "field1": "no language",
                    "field2": "random string",
                    "field3": {"nestedField": "nested string"},
                },
                {"language": str(en_lang.id), "field1": "string"},
                {"language": str(fr_lang.id), "field2": "string2"},
                {"language": str(en_lang.id), "field1": "string"},
            ]
        },
    )
    with pytest.raises(KeyError):
        record["array_of_objects"][0]["language"]["id"]
    assert record["array_of_objects"][1]["language"]["id"] == str(en_lang.id)
    assert record["array_of_objects"][2]["language"]["id"] == str(fr_lang.id)
    assert record["array_of_objects"][3]["language"]["id"] == str(en_lang.id)
    res_iter = record.relations.array_of_objects()
    assert isinstance(res_iter, Iterable)
    res = next(res_iter)
    assert res == en_lang
    res = next(res_iter)
    assert res == fr_lang
    res = next(res_iter)
    assert res == en_lang

    # Set via record dictionary data
    record = Record1.create({})
    record["array_of_objects"] = [
        {
            "field1": "no language",
            "field2": "random string",
            "field3": {"nestedField": "nested string"},
        },
        {"language": {"id": str(en_lang.id)}, "field1": "string"},
        {"language": {"id": str(fr_lang.id)}, "field2": "string2"},
        {"language": {"id": str(en_lang.id)}, "field1": "string"},
    ]
    res_iter = record.relations.array_of_objects()
    assert isinstance(res_iter, Iterable)
    res = next(res_iter)
    assert res == en_lang
    res = next(res_iter)
    assert res == fr_lang

    record.commit()  # validates
    res_iter = record.relations.array_of_objects()
    assert isinstance(res_iter, Iterable)
    res = next(res_iter)
    assert res == en_lang
    res = next(res_iter)
    assert res == fr_lang

    record["array_of_objects"] = [
        {
            "field1": "no language",
            "field2": "random string",
            "field3": {"nestedField": "nested string"},
            "language": {"id": "invalid"},
        },
        {"field1": "testString"},
    ]
    with pytest.raises(InvalidRelationValue):
        record.commit()  # fails validation

    # Set via attribute
    record = Record1.create({})
    record.relations.array_of_objects = [
        {
            "field1": "no language",
            "field2": "random string",
            "field3": {"nestedField": "nested string"},
        },
        {"language": str(en_lang.id), "field1": "string"},
        {"language": str(fr_lang.id), "field2": "string2"},
        {"language": str(en_lang.id), "field1": "string"},
    ]

    assert record["array_of_objects"][1]["language"]["id"] == str(en_lang.id)
    assert record["array_of_objects"][2]["language"]["id"] == str(fr_lang.id)
    assert record["array_of_objects"][3]["language"]["id"] == str(en_lang.id)
    res_iter = record.relations.array_of_objects()
    assert isinstance(res_iter, Iterable)
    res = next(res_iter)
    assert res == en_lang
    res = next(res_iter)
    assert res == fr_lang
    res = next(res_iter)
    assert res == en_lang

    # Update existing value
    record.relations.array_of_objects = [
        {
            "field2": "random string",
            "field3": {"nestedField": "nested string"},
            "language": str(en_lang.id),
        },
        {"language": str(es_lang.id), "field1": "string"},
        {"language": str(en_lang.id), "field1": "string"},
    ]
    assert record["array_of_objects"][0]["language"]["id"] == str(en_lang.id)
    assert record["array_of_objects"][1]["language"]["id"] == str(es_lang.id)
    res_iter = record.relations.array_of_objects()
    assert isinstance(res_iter, Iterable)
    res = next(res_iter)
    assert res == en_lang
    res = next(res_iter)
    assert res == es_lang

    # Set invalid value
    with pytest.raises(InvalidRelationValue):
        record.relations.array_of_objects = "invalid"
    # Check that old value is still there
    assert record["array_of_objects"][0]["language"]["id"] == str(en_lang.id)
    assert record["array_of_objects"][1]["language"]["id"] == str(es_lang.id)
    res_iter = record.relations.array_of_objects()
    assert isinstance(res_iter, Iterable)
    res = next(res_iter)
    assert res == en_lang
    res = next(res_iter)
    assert res == es_lang

    # Dereference relation
    record.relations.array_of_objects.dereference()
    assert record["array_of_objects"] == [
        {
            "field2": "random string",
            "field3": {"nestedField": "nested string"},
            "language": {
                "id": str(en_lang.id),
                "iso": "en",
                "@v": str(en_lang.id) + "::" + str(en_lang.revision_id),
            },
        },
        {
            "language": {
                "id": str(es_lang.id),
                "iso": "es",
                "@v": str(es_lang.id) + "::" + str(es_lang.revision_id),
            },
            "field1": "string",
        },
        {
            "language": {
                "id": str(en_lang.id),
                "iso": "en",
                "@v": str(en_lang.id) + "::" + str(en_lang.revision_id),
            },
            "field1": "string",
        },
    ]

    # Commit clean dereferenced fields
    record.commit()
    assert record["array_of_objects"][0]["language"]["id"] == str(en_lang.id)
    assert record["array_of_objects"][1]["language"]["id"] == str(es_lang.id)
    assert record["array_of_objects"][2]["language"]["id"] == str(en_lang.id)

    # Commit to DB and refetch
    db.session.commit()
    record = Record1.get_record(record.id)
    assert record["array_of_objects"][0]["language"]["id"] == str(en_lang.id)
    assert record["array_of_objects"][1]["language"]["id"] == str(es_lang.id)
    assert record["array_of_objects"][2]["language"]["id"] == str(en_lang.id)
    res_iter = record.relations.array_of_objects()
    assert isinstance(res_iter, Iterable)
    res = next(res_iter)
    assert res == en_lang
    res = next(res_iter)
    assert res == es_lang
    res = next(res_iter)
    assert res == en_lang

    # Clear field
    record.relations.array_of_objects = None
    assert "array_of_objects" not in record
    assert record.relations.array_of_objects() is None
    record.commit()


def test_nested_relations_field(testapp, db, languages):
    """Tests deeply nested relations."""

    Language, languages = languages
    en_lang = languages["en"]
    fr_lang = languages["fr"]
    es_lang = languages["es"]
    it_lang = languages["it"]

    class Record1(Record, SystemFieldsMixin):
        relations = RelationsField(
            deep_single=PKRelation(key="metadata.deep.language", record_cls=Language),
            deep_list=PKListRelation(
                key="metadata.deep.languages", record_cls=Language
            ),
            deep_sibling=PKRelation(
                key="metadata.deep.dark.language", record_cls=Language
            ),
        )

    # Set all fields
    record = Record1.create({})
    record.relations.deep_single = en_lang
    record.relations.deep_list = [en_lang, fr_lang, es_lang]
    record.relations.deep_sibling = it_lang

    assert record == {
        "metadata": {
            "deep": {
                "language": {"id": str(en_lang.id)},
                "languages": [
                    {"id": str(en_lang.id)},
                    {"id": str(fr_lang.id)},
                    {"id": str(es_lang.id)},
                ],
                "dark": {
                    "language": {"id": str(it_lang.id)},
                },
            }
        }
    }
    record.commit()


def test_relations_field_pk_nested_list_of_objects_w_related_field(
    testapp, db, languages
):
    """RelationsField tests for PKListRelation with a list of objects."""

    Language, languages = languages
    en_lang = languages["en"]
    fr_lang = languages["fr"]
    es_lang = languages["es"]

    class Record1(Record, SystemFieldsMixin):
        # end result should be
        # {
        #   nested_array: [
        #       {languages: [en, fr]},
        #       {languages: [en, es]}
        #   ]
        # }
        relations = RelationsField(
            nested_array_of_objects=PKNestedListRelation(
                key="nested_array_of_objects",
                keys=["iso"],
                record_cls=Language,
                relation_field="languages",
            ),
        )

    def _test_iterators(record):
        res_iter = record.relations.nested_array_of_objects()
        assert isinstance(res_iter, Iterable)
        # first inner list
        res_inner_iter = next(res_iter)
        assert isinstance(res_inner_iter, Iterable)
        res = next(res_inner_iter)
        assert res == en_lang
        res = next(res_inner_iter)
        assert res == es_lang
        with pytest.raises(StopIteration):  # finished first iterator
            res = next(res_inner_iter)
        # second inner list
        res_inner_iter = next(res_iter)
        assert isinstance(res_inner_iter, Iterable)
        res = next(res_inner_iter)
        assert res == fr_lang
        res = next(res_inner_iter)
        assert res == en_lang
        with pytest.raises(StopIteration):  # finished second iterator
            res = next(res_inner_iter)

    def _test_inner_values(record):
        with pytest.raises(KeyError):
            record["nested_array_of_objects"][0]["languages"][0]["id"]
        assert record["nested_array_of_objects"][1]["languages"][0]["id"] == (
            str(en_lang.id)
        )
        assert record["nested_array_of_objects"][1]["languages"][1]["id"] == (
            str(es_lang.id)
        )
        assert record["nested_array_of_objects"][2]["languages"][0]["id"] == (
            str(fr_lang.id)
        )
        assert record["nested_array_of_objects"][2]["languages"][1]["id"] == (
            str(en_lang.id)
        )

    # Class-field check
    assert isinstance(Record1.relations, RelationsField)
    assert isinstance(Record1.relations.nested_array_of_objects, PKNestedListRelation)

    # Empty initialization
    record = Record1({})
    assert record == {}
    assert isinstance(record.relations, RelationsMapping)
    assert callable(record.relations.nested_array_of_objects)
    assert record.relations.nested_array_of_objects() is None

    # Initialize from dictionary data
    record = Record1(
        {
            "nested_array_of_objects": [
                {
                    "field1": "no language",
                    "field2": "random string",
                    "field3": {"nestedField": "nested string"},
                },
                {
                    "languages": [{"id": str(en_lang.id)}, {"id": str(es_lang.id)}],
                    "field1": "string",
                },
                {
                    "languages": [{"id": str(fr_lang.id)}, {"id": str(en_lang.id)}],
                    "field2": "string2",
                },
            ]
        }
    )

    _test_iterators(record)

    # Initialize from field data
    record = Record1(
        {"metadata": {"title": "random title"}},
        relations={
            "nested_array_of_objects": [
                {
                    "field1": "no language",
                    "field2": "random string",
                    "field3": {"nestedField": "nested string"},
                },
                {"languages": [str(en_lang.id), str(es_lang.id)], "field1": "string"},
                {"languages": [str(fr_lang.id), str(en_lang.id)], "field2": "string2"},
            ]
        },
    )
    _test_inner_values(record)
    _test_iterators(record)

    # Set via record dictionary data
    record = Record1.create({})
    record["nested_array_of_objects"] = [
        {
            "field1": "no language",
            "field2": "random string",
            "field3": {"nestedField": "nested string"},
        },
        {
            "languages": [{"id": str(en_lang.id)}, {"id": str(es_lang.id)}],
            "field1": "string",
        },
        {
            "languages": [{"id": str(fr_lang.id)}, {"id": str(en_lang.id)}],
            "field2": "string2",
        },
    ]

    _test_iterators(record)

    record.commit()  # validates

    _test_iterators(record)

    # fails with non-list types
    record["nested_array_of_objects"] = [
        {
            "field1": "no language",
            "field2": "random string",
            "field3": {"nestedField": "nested string"},
            "languages": {"id": str(es_lang.id)},
        },
        {"field1": "testString"},
    ]
    with pytest.raises(InvalidRelationValue):
        record.commit()  # fails validation

    # fails with invalid values
    record["nested_array_of_objects"] = [
        {
            "field1": "no language",
            "field2": "random string",
            "field3": {"nestedField": "nested string"},
            "languages": [{"id": "invalid"}],
        },
        {"field1": "testString"},
    ]
    with pytest.raises(InvalidRelationValue):
        record.commit()  # fails validation

    # Set via attribute
    record = Record1.create({})
    record.relations.nested_array_of_objects = [
        {
            "field1": "no language",
            "field2": "random string",
            "field3": {"nestedField": "nested string"},
        },
        {"languages": [str(en_lang.id), str(es_lang.id)], "field1": "string"},
        {"languages": [str(fr_lang.id), str(en_lang.id)], "field2": "string2"},
    ]
    _test_inner_values(record)
    _test_iterators(record)

    # Update existing value
    record.relations.nested_array_of_objects = [
        {"languages": [str(fr_lang.id), str(en_lang.id)], "field2": "string2"}
    ]
    assert record["nested_array_of_objects"][0]["languages"][0]["id"] == (
        str(fr_lang.id)
    )
    assert record["nested_array_of_objects"][0]["languages"][1]["id"] == (
        str(en_lang.id)
    )
    res_iter = record.relations.nested_array_of_objects()
    assert isinstance(res_iter, Iterable)
    # first inner list
    res_inner_iter = next(res_iter)
    assert isinstance(res_inner_iter, Iterable)
    res = next(res_inner_iter)
    assert res == fr_lang
    res = next(res_inner_iter)
    assert res == en_lang
    with pytest.raises(StopIteration):  # finished first iterator
        res = next(res_inner_iter)

    # Set invalid value
    with pytest.raises(InvalidRelationValue):
        record.relations.nested_array_of_objects = "invalid"
    # Check that old value is still there
    assert record["nested_array_of_objects"][0]["languages"][0]["id"] == (
        str(fr_lang.id)
    )
    assert record["nested_array_of_objects"][0]["languages"][1]["id"] == (
        str(en_lang.id)
    )
    res_iter = record.relations.nested_array_of_objects()
    assert isinstance(res_iter, Iterable)
    # first inner list
    res_inner_iter = next(res_iter)
    assert isinstance(res_inner_iter, Iterable)
    res = next(res_inner_iter)
    assert res == fr_lang
    res = next(res_inner_iter)
    assert res == en_lang
    with pytest.raises(StopIteration):  # finished first iterator
        res = next(res_inner_iter)

    # Dereference relation
    record.relations.nested_array_of_objects.dereference()
    assert record["nested_array_of_objects"] == [
        {
            "languages": [  # last updated values are fr + en
                {
                    "id": str(fr_lang.id),
                    "iso": "fr",
                    "@v": str(fr_lang.id) + "::" + str(fr_lang.revision_id),
                },
                {
                    "id": str(en_lang.id),
                    "iso": "en",
                    "@v": str(en_lang.id) + "::" + str(en_lang.revision_id),
                },
            ],
            "field2": "string2",
        },
    ]

    # Commit clean dereferenced fields
    record.commit()
    assert record["nested_array_of_objects"][0]["languages"][0]["id"] == (
        str(fr_lang.id)
    )
    assert record["nested_array_of_objects"][0]["languages"][1]["id"] == (
        str(en_lang.id)
    )

    # Commit to DB and refetch
    db.session.commit()
    record = Record1.get_record(record.id)
    assert record["nested_array_of_objects"][0]["languages"][0]["id"] == (
        str(fr_lang.id)
    )
    assert record["nested_array_of_objects"][0]["languages"][1]["id"] == (
        str(en_lang.id)
    )
    res_iter = record.relations.nested_array_of_objects()
    assert isinstance(res_iter, Iterable)
    # first inner list
    res_inner_iter = next(res_iter)
    assert isinstance(res_inner_iter, Iterable)
    res = next(res_inner_iter)
    assert res == fr_lang
    res = next(res_inner_iter)
    assert res == en_lang
    with pytest.raises(StopIteration):  # finished first iterator
        res = next(res_inner_iter)

    # Clear field
    record.relations.nested_array_of_objects = None
    assert "nested_array_of_objects" not in record
    assert record.relations.nested_array_of_objects() is None
    record.commit()


def test_relations_field_pk_nested_list_of_objects_wo_related_field(
    testapp, db, languages
):
    """RelationsField tests for PKListRelation with a list of objects."""

    Language, languages = languages
    en_lang = languages["en"]
    fr_lang = languages["fr"]
    es_lang = languages["es"]

    class Record1(Record, SystemFieldsMixin):
        # end result should be
        # {
        #   nested_languages: [
        #       [en, fr],
        #       [es, fr],
        #   ]
        # }
        relations = RelationsField(
            nested_languages=PKNestedListRelation(
                key="nested_languages",
                keys=["iso"],
                record_cls=Language,
            ),
        )

    def _test_iterators(record):
        res_iter = record.relations.nested_languages()
        assert isinstance(res_iter, Iterable)
        # first inner list
        res_inner_iter = next(res_iter)
        assert isinstance(res_inner_iter, Iterable)
        res = next(res_inner_iter)
        assert res == en_lang
        res = next(res_inner_iter)
        assert res == es_lang
        with pytest.raises(StopIteration):  # finished first iterator
            res = next(res_inner_iter)
        # second inner list
        res_inner_iter = next(res_iter)
        assert isinstance(res_inner_iter, Iterable)
        res = next(res_inner_iter)
        assert res == fr_lang
        res = next(res_inner_iter)
        assert res == en_lang
        with pytest.raises(StopIteration):  # finished second iterator
            res = next(res_inner_iter)

    def _test_inner_values(record):
        assert record["nested_languages"][0][0]["id"] == (str(en_lang.id))
        assert record["nested_languages"][0][1]["id"] == (str(es_lang.id))
        assert record["nested_languages"][1][0]["id"] == (str(fr_lang.id))
        assert record["nested_languages"][1][1]["id"] == (str(en_lang.id))

    # Class-field check
    assert isinstance(Record1.relations, RelationsField)
    assert isinstance(Record1.relations.nested_languages, PKNestedListRelation)

    # Empty initialization
    record = Record1({})
    assert record == {}
    assert isinstance(record.relations, RelationsMapping)
    assert callable(record.relations.nested_languages)
    assert record.relations.nested_languages() is None

    # Initialize from dictionary data
    record = Record1(
        {
            "nested_languages": [
                [{"id": str(en_lang.id)}, {"id": str(es_lang.id)}],
                [{"id": str(fr_lang.id)}, {"id": str(en_lang.id)}],
            ]
        }
    )

    _test_iterators(record)

    # Initialize from field data
    record = Record1(
        {"metadata": {"title": "random title"}},
        relations={
            "nested_languages": [
                [str(en_lang.id), str(es_lang.id)],
                [str(fr_lang.id), str(en_lang.id)],
            ]
        },
    )
    _test_inner_values(record)
    _test_iterators(record)

    # Set via record dictionary data
    record = Record1.create({})
    record["nested_languages"] = [
        [{"id": str(en_lang.id)}, {"id": str(es_lang.id)}],
        [{"id": str(fr_lang.id)}, {"id": str(en_lang.id)}],
    ]

    _test_iterators(record)

    record.commit()  # validates

    _test_iterators(record)

    # fails with non-list types
    record["nested_languages"] = [{"id": str(es_lang.id)}]
    with pytest.raises(InvalidRelationValue):
        record.commit()  # fails validation

    # fails with invalid values
    record["nested_languages"] = [[{"id": "invalid"}]]
    with pytest.raises(InvalidRelationValue):
        record.commit()  # fails validation

    # Set via attribute
    record = Record1.create({})
    record.relations.nested_languages = [
        [str(en_lang.id), str(es_lang.id)],
        [str(fr_lang.id), str(en_lang.id)],
    ]
    _test_inner_values(record)
    _test_iterators(record)

    # Update existing value
    record.relations.nested_languages = [
        [str(fr_lang.id), str(en_lang.id)],
    ]
    assert record["nested_languages"][0][0]["id"] == (str(fr_lang.id))
    assert record["nested_languages"][0][1]["id"] == (str(en_lang.id))
    res_iter = record.relations.nested_languages()
    assert isinstance(res_iter, Iterable)
    # first inner list
    res_inner_iter = next(res_iter)
    assert isinstance(res_inner_iter, Iterable)
    res = next(res_inner_iter)
    assert res == fr_lang
    res = next(res_inner_iter)
    assert res == en_lang
    with pytest.raises(StopIteration):  # finished first iterator
        res = next(res_inner_iter)

    # Set invalid value
    with pytest.raises(InvalidRelationValue):
        record.relations.nested_languages = "invalid"
    # Check that old value is still there
    assert record["nested_languages"][0][0]["id"] == (str(fr_lang.id))
    assert record["nested_languages"][0][1]["id"] == (str(en_lang.id))
    res_iter = record.relations.nested_languages()
    assert isinstance(res_iter, Iterable)
    # first inner list
    res_inner_iter = next(res_iter)
    assert isinstance(res_inner_iter, Iterable)
    res = next(res_inner_iter)
    assert res == fr_lang
    res = next(res_inner_iter)
    assert res == en_lang
    with pytest.raises(StopIteration):  # finished first iterator
        res = next(res_inner_iter)

    # Dereference relation
    record.relations.nested_languages.dereference()
    assert record["nested_languages"] == [
        [  # last updated values are fr + en
            {
                "id": str(fr_lang.id),
                "iso": "fr",
                "@v": str(fr_lang.id) + "::" + str(fr_lang.revision_id),
            },
            {
                "id": str(en_lang.id),
                "iso": "en",
                "@v": str(en_lang.id) + "::" + str(en_lang.revision_id),
            },
        ],
    ]

    # Commit clean dereferenced fields
    record.commit()
    assert record["nested_languages"][0][0]["id"] == (str(fr_lang.id))
    assert record["nested_languages"][0][1]["id"] == (str(en_lang.id))

    # Commit to DB and refetch
    db.session.commit()
    record = Record1.get_record(record.id)
    assert record["nested_languages"][0][0]["id"] == (str(fr_lang.id))
    assert record["nested_languages"][0][1]["id"] == (str(en_lang.id))
    res_iter = record.relations.nested_languages()
    assert isinstance(res_iter, Iterable)
    # first inner list
    res_inner_iter = next(res_iter)
    assert isinstance(res_inner_iter, Iterable)
    res = next(res_inner_iter)
    assert res == fr_lang
    res = next(res_inner_iter)
    assert res == en_lang
    with pytest.raises(StopIteration):  # finished first iterator
        res = next(res_inner_iter)

    # Clear field
    record.relations.nested_languages = None
    assert "nested_languages" not in record
    assert record.relations.nested_languages() is None
    record.commit()


def test_relations_field_pk_relation_with_value_check(testapp, db, languages):
    """RelationsField tests for PKRelation with value_check param."""

    Language, languages = languages
    en_lang = languages["en"]
    fr_lang = languages["fr"]
    es_lang = languages["es"]
    oe_lang = languages["oe"]

    # Incorrect record definition with 1 non-list value to check
    class Record1(Record, SystemFieldsMixin):
        relations = RelationsField(
            language=PKRelation(
                key="language",
                keys=["iso"],
                record_cls=Language,
                value_check=dict(information=dict(ethnicity="English")),
            )
        )

    # Correct record definition with a list of values to check for
    class Record2(Record, SystemFieldsMixin):
        relations = RelationsField(
            language=PKRelation(
                key="language",
                keys=["iso"],
                record_cls=Language,
                value_check=dict(information=dict(ethnicity=["English", "French"])),
            )
        )

    # Wrong record definition, value_check must contain existing fields in the
    # vocabulary value
    class Record3(Record, SystemFieldsMixin):
        relations = RelationsField(
            language=PKRelation(
                key="language",
                keys=["iso"],
                record_cls=Language,
                value_check=dict(wrong_value=dict(ethnicity=["English"])),
            )
        )

    # Correct record definition with multiple values to check
    class Record4(Record, SystemFieldsMixin):
        relations = RelationsField(
            language=PKRelation(
                key="language",
                keys=["iso"],
                record_cls=Language,
                value_check=dict(information=dict(ethnicity=["English"]), iso=["oe"]),
            )
        )

    record = Record1.create({})
    record["language"] = {"id": str(en_lang.id)}
    # Fails because value_check must be a list
    with pytest.raises(InvalidCheckValue):
        record.commit()  # validates

    record = Record2.create({})
    record["language"] = {"id": str(es_lang.id)}
    # Fails because only ethnicity accepted is English and French
    with pytest.raises(InvalidCheckValue):
        record.commit()  # validates

    record["language"] = {"id": str(fr_lang.id)}
    record.commit()  # validates
    res = record.relations.language()
    assert isinstance(res, Language)
    assert res == fr_lang

    record = Record3.create({})
    record["language"] = {"id": str(en_lang.id)}
    # Fails because wrong_value is not a field of the language vocabulary
    with pytest.raises(InvalidCheckValue):
        record.commit()  # validates

    record = Record4.create({})
    record["language"] = {"id": str(en_lang.id)}
    # Fails because only records with English ethnicity and 'oe' as iso are
    # accepted
    with pytest.raises(InvalidCheckValue):
        record.commit()  # validates

    record["language"] = {"id": str(oe_lang.id)}
    record.commit()  # validates
    res = record.relations.language()
    assert isinstance(res, Language)
    assert res == oe_lang


def test_relations_field_pk_list_relation_with_value_check(testapp, db, languages):
    """RelationsField tests for PKListRelation with value_check param."""

    Language, languages = languages
    en_lang = languages["en"]
    fr_lang = languages["fr"]
    es_lang = languages["es"]
    oe_lang = languages["oe"]

    # Incorrect record definition with 1 non-list value to check
    class Record1(Record, SystemFieldsMixin):
        relations = RelationsField(
            languages=PKListRelation(
                key="languages",
                keys=["iso", "information.ethnicity"],
                record_cls=Language,
                value_check=dict(information=dict(ethnicity="English")),
            )
        )

    # Correct record definition with a list of values to check for
    class Record2(Record, SystemFieldsMixin):
        relations = RelationsField(
            languages=PKListRelation(
                key="languages",
                keys=["iso", "information.ethnicity"],
                record_cls=Language,
                value_check=dict(information=dict(ethnicity=["English", "French"])),
            )
        )

    # Wrong record definition, value_check must contain existing fields in the
    # vocabulary value
    class Record3(Record, SystemFieldsMixin):
        relations = RelationsField(
            languages=PKListRelation(
                key="languages",
                keys=["iso", "information.ethnicity"],
                record_cls=Language,
                value_check=dict(wrong_value=dict(ethnicity=["English"])),
            )
        )

    # Correct record definition with multiple values to check
    class Record4(Record, SystemFieldsMixin):
        relations = RelationsField(
            languages=PKListRelation(
                key="languages",
                keys=["iso", "information.ethnicity"],
                record_cls=Language,
                value_check=dict(information=dict(ethnicity=["English"]), iso=["oe"]),
            )
        )

    record = Record1.create({})
    record["languages"] = [{"id": str(fr_lang.id)}]
    # Fails because value_check must be a list
    with pytest.raises(InvalidCheckValue):
        record.commit()  # validates

    record = Record2.create({})
    record["languages"] = [{"id": str(es_lang.id)}, {"id": str(en_lang.id)}]
    # Fails because only ethnicity accepted is English and French
    with pytest.raises(InvalidCheckValue):
        record.commit()  # validates

    record["languages"] = [{"id": str(fr_lang.id)}, {"id": str(en_lang.id)}]
    record.commit()  # validates
    res_iter = record.relations.languages()
    assert isinstance(res_iter, Iterable)
    res = next(res_iter)
    assert res == fr_lang

    record = Record3.create({})
    record["languages"] = [{"id": str(en_lang.id)}]
    # Fails because wrong_value is not a field of the language vocabulary
    with pytest.raises(InvalidCheckValue):
        record.commit()  # validates

    record = Record4.create({})
    record["languages"] = [{"id": str(en_lang.id)}]
    # Fails because only records with English ethnicity and 'oe' as iso are
    # accepted
    with pytest.raises(InvalidCheckValue):
        record.commit()  # validates

    record["languages"] = [{"id": str(oe_lang.id)}]
    record.commit()  # validates
    res_iter = record.relations.languages()
    assert isinstance(res_iter, Iterable)
    res = next(res_iter)
    assert res == oe_lang


def test_relations_field_pk_nested_list_of_obj_w_related_field_w_value_check(
    testapp, db, languages
):
    """RelationsField tests for PKListRelation with a list of objects and
    with the value_check param."""

    Language, languages = languages
    en_lang = languages["en"]
    fr_lang = languages["fr"]
    es_lang = languages["es"]
    oe_lang = languages["oe"]

    # Incorrect record definition with 1 non-list value to check
    class Record1(Record, SystemFieldsMixin):
        relations = RelationsField(
            nested_array_of_objects=PKNestedListRelation(
                key="nested_array_of_objects",
                keys=["iso"],
                record_cls=Language,
                relation_field="languages",
                value_check=dict(information=dict(ethnicity="English")),
            ),
        )

    # Correct record definition with a list of values to check for
    class Record2(Record, SystemFieldsMixin):
        relations = RelationsField(
            nested_array_of_objects=PKNestedListRelation(
                key="nested_array_of_objects",
                keys=["iso"],
                record_cls=Language,
                relation_field="languages",
                value_check=dict(information=dict(ethnicity=["English", "French"])),
            ),
        )

    # Wrong record definition, value_check must contain existing fields in the
    # vocabulary value
    class Record3(Record, SystemFieldsMixin):
        relations = RelationsField(
            nested_array_of_objects=PKNestedListRelation(
                key="nested_array_of_objects",
                keys=["iso"],
                record_cls=Language,
                relation_field="languages",
                value_check=dict(wrong_value=dict(ethnicity=["English"])),
            ),
        )

    # Correct record definition with multiple values to check
    class Record4(Record, SystemFieldsMixin):
        relations = RelationsField(
            nested_array_of_objects=PKNestedListRelation(
                key="nested_array_of_objects",
                keys=["iso"],
                record_cls=Language,
                relation_field="languages",
                value_check=dict(information=dict(ethnicity=["English"]), iso=["oe"]),
            ),
        )

    record = Record1.create({})
    record["nested_array_of_objects"] = [
        {
            "languages": [{"id": str(en_lang.id)}, {"id": str(es_lang.id)}],
            "field1": "string",
        },
        {
            "languages": [{"id": str(fr_lang.id)}, {"id": str(en_lang.id)}],
            "field2": "string2",
        },
    ]
    # Fails because value_check must be a list
    with pytest.raises(InvalidCheckValue):
        record.commit()  # validates

    record = Record2.create({})
    record["nested_array_of_objects"] = [
        {
            "languages": [{"id": str(en_lang.id)}, {"id": str(es_lang.id)}],
            "field1": "string",
        },
        {
            "languages": [{"id": str(fr_lang.id)}, {"id": str(en_lang.id)}],
            "field2": "string2",
        },
    ]
    # Fails because only ethnicity accepted is English and French
    with pytest.raises(InvalidCheckValue):
        record.commit()  # validates

    record["nested_array_of_objects"] = [
        {
            "languages": [{"id": str(en_lang.id)}, {"id": str(fr_lang.id)}],
            "field1": "string",
        },
        {
            "languages": [{"id": str(fr_lang.id)}, {"id": str(en_lang.id)}],
            "field2": "string2",
        },
    ]

    record.commit()  # validates
    res_iter = record.relations.nested_array_of_objects()
    assert isinstance(res_iter, Iterable)
    # first inner list
    res_inner_iter = next(res_iter)
    assert isinstance(res_inner_iter, Iterable)
    res = next(res_inner_iter)
    assert res == en_lang
    res = next(res_inner_iter)
    assert res == fr_lang
    with pytest.raises(StopIteration):  # finished first iterator
        res = next(res_inner_iter)
    # second inner list
    res_inner_iter = next(res_iter)
    assert isinstance(res_inner_iter, Iterable)
    res = next(res_inner_iter)
    assert res == fr_lang
    res = next(res_inner_iter)
    assert res == en_lang
    with pytest.raises(StopIteration):  # finished second iterator
        res = next(res_inner_iter)

    record = Record3.create({})
    record["nested_array_of_objects"] = [
        {
            "languages": [{"id": str(en_lang.id)}, {"id": str(fr_lang.id)}],
            "field1": "string",
        },
        {
            "languages": [{"id": str(fr_lang.id)}, {"id": str(en_lang.id)}],
            "field2": "string2",
        },
    ]
    # Fails because wrong_value is not a field of the language vocabulary
    with pytest.raises(InvalidCheckValue):
        record.commit()  # validates

    record = Record4.create({})
    record["nested_array_of_objects"] = [
        {"languages": [{"id": str(en_lang.id)}], "field1": "string"}
    ]
    # Fails because only ethnicity accepted is English
    with pytest.raises(InvalidCheckValue):
        record.commit()  # validates

    record["nested_array_of_objects"] = [
        {"languages": [{"id": str(oe_lang.id)}], "field1": "string"}
    ]
    res_iter = record.relations.nested_array_of_objects()
    assert isinstance(res_iter, Iterable)
    # first inner list
    res_inner_iter = next(res_iter)
    assert isinstance(res_inner_iter, Iterable)
    res = next(res_inner_iter)
    assert res == oe_lang
    with pytest.raises(StopIteration):  # finished first iterator
        next(res_inner_iter)
