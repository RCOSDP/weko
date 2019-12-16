# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio serializer tests."""

from __future__ import absolute_import, print_function

import json

from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record
from marshmallow import Schema, fields

from invenio_records_rest.schemas.fields import \
    PersistentIdentifier as PIDField
from invenio_records_rest.serializers.json import JSONSerializer


def test_serialize():
    """Test JSON serialize."""
    class TestSchema(Schema):
        title = fields.Str(attribute='metadata.mytitle')
        id = PIDField(attribute='pid.pid_value')

    data = json.loads(JSONSerializer(TestSchema).serialize(
        PersistentIdentifier(pid_type='recid', pid_value='2'),
        Record({'mytitle': 'test'})
    ))
    assert data['title'] == 'test'
    assert data['id'] == '2'


def test_serialize_search():
    """Test JSON serialize."""
    class TestSchema(Schema):
        title = fields.Str(attribute='metadata.mytitle')
        id = PIDField(attribute='pid.pid_value')

    def fetcher(obj_uuid, data):
        assert obj_uuid in ['a', 'b']
        return PersistentIdentifier(pid_type='recid', pid_value=data['pid'])

    data = json.loads(JSONSerializer(TestSchema).serialize_search(
        fetcher,
        dict(
            hits=dict(
                hits=[
                    {'_source': dict(mytitle='test1', pid='1'), '_id': 'a',
                     '_version': 1},
                    {'_source': dict(mytitle='test2', pid='2'), '_id': 'b',
                     '_version': 1},
                ],
                total=2,
            ),
            aggregations={},
        )
    ))

    assert data['aggregations'] == {}
    assert 'links' in data
    assert data['hits'] == dict(
        hits=[
            dict(title='test1', id='1'),
            dict(title='test2', id='2'),
        ],
        total=2,
    )


def test_serialize_pretty(app):
    """Test pretty JSON."""
    class TestSchema(Schema):
        title = fields.Str(attribute='metadata.title')

    pid = PersistentIdentifier(pid_type='recid', pid_value='2'),
    rec = Record({'title': 'test'})

    with app.test_request_context():
        assert JSONSerializer(TestSchema).serialize(pid, rec) == \
            '{"title":"test"}'

    with app.test_request_context('/?prettyprint=1'):
        assert JSONSerializer(TestSchema).serialize(pid, rec) == \
            '{\n  "title": "test"\n}'
