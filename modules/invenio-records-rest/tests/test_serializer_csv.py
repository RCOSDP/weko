# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""CSV Core serializer tests."""

from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record
from invenio_rest.serializer import BaseSchema as Schema
from marshmallow import fields

from invenio_records_rest.serializers.csv import CSVSerializer

RECORD_1 = {
    "number": 2,
    "title": {
        "title": "A title",
        "subtitle": "The subtitle",
    },
    "description": "A very, very 'long' description, with some \"quotes\".",
    "langs": ["en", "fr", "de"],
    "extra": {
        "key": "A value",
        "value": "And special chars:¥,§, Æ, ®,m²☯⊋",
    },
    "related": [
        {"pid": "55", "label": "Relation A"},
        {"pid": "56", "label": "Relation B"},
        {"pid": "52", "label": "Relation C"},
    ],
}

RECORD_2 = {
    "number": 2,
    "title": {
        "title": "A title 2",
        "subtitle": "The subtitle 2",
    },
    "description": "A very, very 'long' description, with some \"quotes\".",
    "langs": ["en", "fr", "de"],
    "extra": {
        "key": "An extra value",
        "value": "And special chars:¥,§, Æ, ®,m²☯⊋",
    },
    "related": [
        {"pid": "55", "label": "Relation A"},
        {"pid": "56", "label": "Relation B"},
        {"pid": "52", "label": "Relation C"},
        {"pid": "78", "label": "Relation D"},
    ],
}


class SimpleSchema(Schema):
    """Test schema."""

    number = fields.Raw(attribute="metadata.number")
    title = fields.Raw(attribute="metadata.title")
    description = fields.Raw(attribute="metadata.description")
    langs = fields.Raw(attribute="metadata.langs")
    extra = fields.Raw(attribute="metadata.extra")
    related = fields.Raw(attribute="metadata.related")


def test_serialize():
    """Test JSON serialize."""

    EXCLUDE_FIELDS = [
        "extra",
        "related_1_pid",
        "related_1_label",
    ]

    pid = PersistentIdentifier(pid_type="recid", pid_value="2")
    rec = Record(RECORD_1)
    data = CSVSerializer(SimpleSchema, csv_excluded_fields=EXCLUDE_FIELDS).serialize(
        pid, rec
    )

    headers, row_1 = list(data)
    assert (
        "description,langs_0,langs_1,langs_2,number,related_0_label,"
        "related_0_pid,related_2_label,related_2_pid,title_subtitle,"
        "title_title" == headers.rstrip()
    )
    assert (
        '"A very, very \'long\' description, with some ""quotes"".",'
        "en,fr,de,2,Relation A,55,Relation C,52,The subtitle,"
        "A title" == row_1.rstrip()
    )


def test_serialize_with_extra_col_other_separator():
    """Test JSON serialize."""

    EXCLUDE_FIELDS = [
        "related.1.pid",
        "related.1.label",
    ]

    INCLUDE_FIELDS = ["langs", "title.title", "title.subtitle"]

    pid = PersistentIdentifier(pid_type="recid", pid_value="2")
    rec = Record(RECORD_2)
    data = CSVSerializer(
        SimpleSchema, csv_excluded_fields=EXCLUDE_FIELDS, header_separator="."
    ).serialize(pid, rec)

    headers, row_1 = list(data)
    assert (
        "description,extra.key,extra.value,langs.0,langs.1,langs.2,number,"
        "related.0.label,related.0.pid,related.2.label,related.2.pid,"
        "related.3.label,related.3.pid,title.subtitle,"
        "title.title" == headers.rstrip()
    )
    assert (
        '"A very, very \'long\' description, with some ""quotes"".",An'
        ' extra value,"And special chars:¥,§, Æ, ®,m²☯⊋",en,fr,de,2,'
        "Relation A,55,"
        "Relation C,52,"
        "Relation D,78,The subtitle 2,A title 2" == row_1.rstrip()
    )

    data = CSVSerializer(
        SimpleSchema, csv_included_fields=INCLUDE_FIELDS, header_separator="."
    ).serialize(pid, rec)

    headers, row_1 = list(data)
    assert "langs.0,langs.1,langs.2," "title.subtitle,title.title" == headers.rstrip()
    assert "en,fr,de,The subtitle 2,A title 2" == row_1.rstrip()


def test_serialize_search():
    """Test CSV serialize."""

    EXCLUDE_FIELDS = [
        "extra",
        "related_1_pid",
        "related_1_label",
    ]

    def fetcher(obj_uuid, data):
        assert obj_uuid in ["a", "b", "c", "d", "e"]
        return PersistentIdentifier(pid_type="doi", pid_value="a")

    hits = [
        {
            "_source": RECORD_1,
            "_id": "a",
            "_version": 1,
        },
        {"_source": RECORD_2, "_id": "b", "_version": 1},
        {
            "_source": RECORD_2,
            "_id": "c",
            "_version": 1,
        },
        {"_source": RECORD_2, "_id": "d", "_version": 1},
        {"_source": RECORD_2, "_id": "e", "_version": 1},
    ]

    data = CSVSerializer(
        SimpleSchema, csv_excluded_fields=EXCLUDE_FIELDS
    ).serialize_search(
        fetcher,
        dict(
            hits=dict(
                hits=hits,
                total=len(hits),
            ),
            aggregations={},
        ),
    )
    headers, row_1, row_2, row_3, row_4, row_5 = list(data)
    assert (
        "description,langs_0,langs_1,langs_2,number,related_0_label,"
        "related_0_pid,related_2_label,related_2_pid,related_3_label,"
        "related_3_pid,title_subtitle,title_title" == headers.rstrip()
    )

    expected_row_1 = (
        "\"A very, very 'long' description, with "
        'some ""quotes"".",en,fr,de,2,Relation A,55,'
        "Relation C,52,,,The subtitle,A title"
    )
    assert expected_row_1 == row_1.rstrip()

    expected_next_rows = (
        "\"A very, very 'long' description, with "
        'some ""quotes"".",en,fr,de,2,Relation A,55,'
        "Relation C,52,Relation D,78,The subtitle 2,A title 2"
    )
    assert expected_next_rows == row_2.rstrip()
    assert expected_next_rows == row_3.rstrip()
    assert expected_next_rows == row_4.rstrip()
    assert expected_next_rows == row_5.rstrip()
