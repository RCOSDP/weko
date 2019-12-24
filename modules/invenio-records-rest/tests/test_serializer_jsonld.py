# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
# Copyright (C) 2017 RERO.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio JSON-LD serializer tests."""

from __future__ import absolute_import, print_function

import json

from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record
from marshmallow import Schema, fields

from invenio_records_rest.serializers.jsonld import JSONLDSerializer


class _TestSchema(Schema):
    """Test schema."""

    title = fields.Str(attribute='metadata.title')
    recid = fields.Str(attribute='metadata.recid')
    id = fields.Str(attribute='pid.pid_value')


CONTEXT = {
    '@context': {
        "dct": "http://purl.org/dc/terms/",
        '@base': 'http://localhost/record/',
        'recid': '@id',
        'title': 'dct:title'
    }
}


def test_serialize():
    """Test JSON serialize."""
    data = json.loads(
        JSONLDSerializer(CONTEXT, schema_class=_TestSchema).serialize(
            PersistentIdentifier(pid_type='recid', pid_value='2'),
            Record({'title': 'mytitle', 'recid': '2'})
        )
    )

    assert data == {
        '@id': 'http://localhost/record/2',
        'http://purl.org/dc/terms/title': [{'@value': 'mytitle'}]
    }

    data = json.loads(JSONLDSerializer(
        CONTEXT, schema_class=_TestSchema, expanded=False).serialize(
            PersistentIdentifier(pid_type='recid', pid_value='2'),
            Record({'title': 'mytitle', 'recid': '2'})
        )
    )

    assert data == {
        '@context': {
            '@base': 'http://localhost/record/',
            'dct': 'http://purl.org/dc/terms/',
            'recid': '@id',
            'title': 'dct:title'
        },
        'recid': '2',
        'title': 'mytitle'
    }


def test_serialize_search():
    """Test JSON serialize."""
    def fetcher(obj_uuid, data):
        assert obj_uuid in ['1', '2']
        return PersistentIdentifier(pid_type='recid', pid_value=data['recid'])

    data = json.loads(JSONLDSerializer(
        CONTEXT, schema_class=_TestSchema, expanded=True).serialize_search(
            fetcher,
            dict(
                hits=dict(
                    hits=[
                        {'_source': dict(title='title1', recid='1'),
                         '_id': '1', '_version': 1},
                        {'_source': dict(title='title2', recid='2'),
                         '_id': '2', '_version': 1},
                    ],
                    total=2,
                ),
                aggregations={},
            )
    ))

    assert data['aggregations'] == {}
    assert 'links' in data
    assert data['hits'] == dict(
        hits=[{
            '@id': 'http://localhost/record/1',
            'http://purl.org/dc/terms/title': [{
                '@value': 'title1'
                }]
            }, {
            '@id': 'http://localhost/record/2',
            'http://purl.org/dc/terms/title': [{
                '@value': 'title2'}
            ]}],
        total=2
    )
