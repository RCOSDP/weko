# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test Relations fields."""

from collections.abc import Iterable

import pytest

from invenio_records.api import Record
from invenio_records.systemfields import (
    MultiRelationsField,
    RelationsField,
    SystemFieldsMixin,
)
from invenio_records.systemfields.relations import (
    InvalidRelationValue,
    PKListRelation,
    RelationsMapping,
)


def test_multirelations_field(testapp, db, languages):
    """MultiRelationsField tests."""

    Language, languages = languages
    en_lang = languages["en"]
    fr_lang = languages["fr"]

    def _assert_iter_and_lang_from_record(record):
        res_iter = record.relations.languages()
        assert isinstance(res_iter, Iterable)
        res = next(res_iter)
        assert res == en_lang

        res_iter = record.relations.inner_languages()
        assert isinstance(res_iter, Iterable)
        res = next(res_iter)
        assert res == fr_lang

    class Record1(Record, SystemFieldsMixin):
        relations = MultiRelationsField(
            languages=PKListRelation(
                key="languages",
                keys=["iso", "information.ethnicity"],
                record_cls=Language,
            ),
            inner=RelationsField(
                inner_languages=PKListRelation(
                    key="inner.inner_languages",
                    keys=["iso", "information.ethnicity"],
                    record_cls=Language,
                ),
            ),
        )

    # Class-field check
    # ---------------------------------------------------------------
    assert isinstance(Record1.relations, RelationsField)
    assert isinstance(Record1.relations.languages, PKListRelation)
    assert isinstance(Record1.relations.inner_languages, PKListRelation)
    with pytest.raises(AttributeError):
        Record1.inner  # keys are flattened, accessing this field gives an error

    # Empty initialization
    # ---------------------------------------------------------------
    record = Record1({})
    assert record == {}
    assert isinstance(record.relations, RelationsMapping)
    assert callable(record.relations.languages)
    assert callable(record.relations.inner_languages)
    assert record.relations.languages() is None
    assert record.relations.inner_languages() is None

    # Initialize from dictionary data
    # ---------------------------------------------------------------
    record = Record1(
        {
            "languages": [{"id": str(en_lang.id)}],
            "inner": {
                "inner_languages": [{"id": str(fr_lang.id)}],
            },
        }
    )
    _assert_iter_and_lang_from_record(record)

    # Initialize from field data
    # ---------------------------------------------------------------
    record = Record1(
        {},
        relations={
            "languages": [str(en_lang.id)],
            "inner": {
                "inner_languages": [str(fr_lang.id)],
            },
        },
    )
    assert record["languages"] == [{"id": str(en_lang.id)}]
    assert record["inner"]["inner_languages"] == [{"id": str(fr_lang.id)}]
    _assert_iter_and_lang_from_record(record)

    # Set via record dictionary data
    # ---------------------------------------------------------------
    record = Record1.create({})
    record["languages"] = [{"id": str(en_lang.id)}]
    record["inner"] = {}
    record["inner"]["inner_languages"] = [{"id": str(fr_lang.id)}]
    _assert_iter_and_lang_from_record(record)
    record.commit()  # validates
    _assert_iter_and_lang_from_record(record)

    record["languages"] = {"id": "invalid"}
    with pytest.raises(InvalidRelationValue):
        record.commit()  # fails validation
    record["languages"] = [{"id": str(en_lang.id)}]
    record["inner"]["inner_languages"] = {"id": "invalid"}
    with pytest.raises(InvalidRelationValue):
        record.commit()  # fails validation

    # Set via attribute
    # ---------------------------------------------------------------
    record = Record1.create({})
    record.relations.languages = [str(en_lang.id)]
    record.relations.inner_languages = [str(fr_lang.id)]

    assert record["languages"][0]["id"] == str(en_lang.id)
    assert record["inner"]["inner_languages"][0]["id"] == str(fr_lang.id)
    _assert_iter_and_lang_from_record(record)

    # Update existing value
    # ---------------------------------------------------------------
    record.relations.languages = [str(fr_lang.id)]
    record.relations.inner_languages = [str(en_lang.id)]
    assert record["languages"][0]["id"] == str(fr_lang.id)
    assert record["inner"]["inner_languages"][0]["id"] == str(en_lang.id)

    res_iter = record.relations.languages()
    assert isinstance(res_iter, Iterable)
    res = next(res_iter)
    assert res == fr_lang

    res_iter = record.relations.inner_languages()
    assert isinstance(res_iter, Iterable)
    res = next(res_iter)
    assert res == en_lang

    # Set invalid value
    # ---------------------------------------------------------------
    record = Record1.create({})
    record.relations.languages = [str(en_lang.id)]
    record.relations.inner_languages = [str(fr_lang.id)]

    for v in ("invalid", ["invalid"]):
        with pytest.raises(InvalidRelationValue):
            record.relations.languages = v

        with pytest.raises(InvalidRelationValue):
            record.relations.inner_languages = v
        # Check that old value is still there
        assert record["languages"][0]["id"] == str(en_lang.id)
        assert record["inner"]["inner_languages"][0]["id"] == str(fr_lang.id)
        _assert_iter_and_lang_from_record(record)

    # Dereference relation
    # ---------------------------------------------------------------
    record.relations.languages.dereference()
    assert record["languages"] == [
        {
            "id": str(en_lang.id),
            "iso": "en",  # only stores the "iso" field
            "information": {"ethnicity": "English"},
            "@v": str(en_lang.id) + "::" + str(en_lang.revision_id),
        }
    ]
    record.relations.inner_languages.dereference()
    assert record["inner"]["inner_languages"] == [
        {
            "id": str(fr_lang.id),
            "iso": "fr",  # only stores the "iso" field
            "information": {"ethnicity": "French"},
            "@v": str(fr_lang.id) + "::" + str(fr_lang.revision_id),
        }
    ]

    # Commit clean dereferened fields
    # ---------------------------------------------------------------
    record.commit()
    assert record["languages"] == [{"id": str(en_lang.id)}]
    assert record["inner"]["inner_languages"][0]["id"] == str(fr_lang.id)

    # Commit to DB and refetch
    # ---------------------------------------------------------------
    db.session.commit()
    record = Record1.get_record(record.id)
    assert record["languages"] == [{"id": str(en_lang.id)}]
    assert record["inner"]["inner_languages"][0]["id"] == str(fr_lang.id)
    _assert_iter_and_lang_from_record(record)

    # Clear field
    # ---------------------------------------------------------------
    record.relations.languages = None
    assert "languages" not in record
    assert record.relations.languages() is None

    record.relations.inner_languages = None
    assert "inner_languages" not in record
    assert record.relations.inner_languages() is None

    record.commit()
