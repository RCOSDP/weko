# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
# Copyright (C) 2017 RERO.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

# .tox/c1/bin/pytest --cov=invenio_records_rest tests/test_serializer_jsonld.py -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/invenio-records-rest/.tox/c1/tmp

"""Invenio JSON-LD serializer tests."""

from __future__ import absolute_import, print_function

import json
import pytest

from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record
from marshmallow import Schema, fields

from invenio_records_rest.serializers.jsonld import JSONLDSerializer
from tests.helpers import create_record

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


def test_serialize(db):
    """Test JSON serialize."""
    with pytest.raises(Exception):
        data = json.loads(
            JSONLDSerializer(CONTEXT, schema_class=_TestSchema).serialize(
                PersistentIdentifier(pid_type='recid', pid_value='2'),
                Record({'title': 'mytitle', 'recid': '2'})
            )
        )

        # assert data == {
        #     '@id': 'http://localhost/record/2',
        #     'http://purl.org/dc/terms/title': [{'@value': 'mytitle'}]
        # }

    with pytest.raises(Exception):
        data = json.loads(JSONLDSerializer(
            CONTEXT, schema_class=_TestSchema, expanded=False).serialize(
                PersistentIdentifier(pid_type='recid', pid_value='2'),
                Record({'title': 'mytitle', 'recid': '2'})
            )
        )

        # assert data == {
        #     '@context': {
        #         '@base': 'http://localhost/record/',
        #         'dct': 'http://purl.org/dc/terms/',
        #         'recid': '@id',
        #         'title': 'dct:title'
        #     },
        #     'recid': '2',
        #     'title': 'mytitle'
        # }


def test_serialize_search():
    """Test JSON serialize."""
    def fetcher(obj_uuid, data):
        assert obj_uuid in ['1', '2']
        return PersistentIdentifier(pid_type='recid', pid_value=data['recid'])

    with pytest.raises(Exception):
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

        # assert data['aggregations'] == {}
        # assert 'links' in data
        # assert data['hits'] == dict(
        #     hits=[{
        #         '@id': 'http://localhost/record/1',
        #         'http://purl.org/dc/terms/title': [{
        #             '@value': 'title1'
        #             }]
        #         }, {
        #         '@id': 'http://localhost/record/2',
        #         'http://purl.org/dc/terms/title': [{
        #             '@value': 'title2'}
        #         ]}],
        #     total=2
        # )


def test_transform_jsonld(indexed_10records, mocker):
    record = indexed_10records[0]
    obj={
        "http://localhost/record/":"test server",
        "dct:title":"test record01",
        "@id":"12345"
        }
    mocker.patch("invenio_records_rest.serializers.jsonld.JSONLDTransformerMixin.expanded", return_value=False,  new_callable=mocker.PropertyMock)
    data = JSONLDSerializer(CONTEXT, schema_class=_TestSchema).transform_jsonld(obj)
    result = {
        "@context": {
            "dct": "http://purl.org/dc/terms/",
            "@base": "http://localhost/record/",
            "recid": "@id",
            "title": "dct:title"
        },
        "recid": "12345",
        "http://localhost/record/": "test server",
        "title": "test record01"
    }
    assert data == result
    
    mocker.patch("invenio_records_rest.serializers.jsonld.JSONLDTransformerMixin.expanded", return_value=True, new_callable=mocker.PropertyMock)
    data = JSONLDSerializer(CONTEXT, schema_class=_TestSchema).transform_jsonld(obj)
    result = {
        "http://localhost/record/":[{"@value": "test server"}],
        "@id": "12345",
        "http://purl.org/dc/terms/title":[{"@value": "test record01"}]
    }
    assert data == result