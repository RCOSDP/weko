# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

# .tox/c1/bin/pytest --cov=invenio_records_rest tests/test_views_item_put.py -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/invenio-records-rest/.tox/c1/tmp

"""Record PUT tests."""

from __future__ import absolute_import, print_function

import json

import mock
import pytest
from .conftest import IndexFlusher
from tests.helpers import _mock_validate_fail, assert_hits_len, get_json, record_url
from invenio_records.models import RecordMetadata


@pytest.mark.parametrize('content_type', [
    'application/json', 'application/json;charset=utf-8'
])
def test_valid_put(app, es, test_records, content_type, search_url,
                   search_class):
    """Test VALID record patch request (PATCH .../records/<record_id>)."""
    HEADERS = [
        ('Accept', 'application/json'),
        ('Content-Type', content_type)
    ]

    pid, record = test_records[0]

    record['year'] = 1234

    with app.test_client() as client:
        url = record_url(pid)
        res = client.put(url, data=json.dumps(record.dumps()), headers=HEADERS)
        assert res.status_code == 200

        # Check that the returned record matches the given data
        assert get_json(res)['metadata']['year'] == 1234
        # IndexFlusher(search_class).flush_and_wait()
        # res = client.get(search_url, query_string={"year": 1234})
        # assert_hits_len(res, 1)
        # Retrieve record via get request
        assert get_json(client.get(url))['metadata']['year'] == 1234


@pytest.mark.parametrize('content_type', [
    'application/json', 'application/json;charset=utf-8'
])
def test_valid_put_etag(app, es, test_records, content_type, search_url,
                        search_class):
    """Test concurrency control with etags."""
    HEADERS = [
        ('Accept', 'application/json'),
        ('Content-Type', content_type)
    ]

    pid, record = test_records[0]
    obj_id = pid.object_uuid

    record['year'] = 1234

    with app.test_client() as client:
        url = record_url(pid)
        assert RecordMetadata.query.filter_by(id=obj_id).first().json['year']==2015
        res = client.put(
            url,
            data=json.dumps(record.dumps()),
            headers={
                'Content-Type': 'application/json',
                'If-Match': '"{0}"'.format(record.revision_id)
            })
        assert res.status_code == 200
        assert get_json(client.get(url))['metadata']['year'] == 1234

        # IndexFlusher(search_class).flush_and_wait()
        # res = client.get(search_url, query_string={"year": 1234})
        # assert_hits_len(res, 1)


@pytest.mark.parametrize('content_type', [
    'application/json', 'application/json;charset=utf-8'
])
def test_put_on_deleted(app, db, es, test_data, content_type, search_url,
                        search_class):
    """Test putting to a deleted record."""
    with app.test_client() as client:
        HEADERS = [
            ('Accept', 'application/json'),
            ('Content-Type', content_type)
        ]
        HEADERS.append(('Content-Type', content_type))

        # Create record
        res = client.post(
            search_url, data=json.dumps(test_data[0]), headers=HEADERS)
        assert res.status_code == 200

        url = record_url(get_json(res)['id'])
        assert client.delete(url).status_code == 204
        # IndexFlusher(search_class).flush_and_wait()
        # res = client.get(search_url,
        #                  query_string={'title': test_data[0]['title']})
        # assert_hits_len(res, 0)

        with pytest.raises(AttributeError):
            res = client.put(url, data='{}', headers=HEADERS)
            # assert res.status_code == 410


@pytest.mark.parametrize('charset', [
    '', ';charset=utf-8'
])
def test_invalid_put(app, es, test_records, charset, search_url):
    """Test INVALID record put request (PUT .../records/<record_id>)."""
    HEADERS = [
        ('Accept', 'application/json'),
        ('Content-Type',
         'application/json{0}'.format(charset)),
    ]

    pid, record = test_records[0]

    record['year'] = 1234
    test_data = record.dumps()

    with app.test_client() as client:
        url = record_url(pid)

        # Non-existing record
        res = client.put(
            record_url('0'), data=json.dumps(test_data), headers=HEADERS)
        assert res.status_code == 404
        # res = client.get(search_url, query_string={"year": 1234})
        # assert_hits_len(res, 0)

        # Invalid accept mime type.
        headers = [('Content-Type', 'application/json{0}'.format(charset)),
                   ('Accept', 'video/mp4')]
        res = client.put(url, data=json.dumps(test_data), headers=headers)
        assert res.status_code == 406

        # Invalid content type
        headers = [('Content-Type', 'video/mp4{0}'.format(charset)),
                   ('Accept', 'application/json')]
        res = client.put(url, data=json.dumps(test_data), headers=headers)
        assert res.status_code == 415

        # Invalid JSON
        res = client.put(url, data='{invalid-json', headers=HEADERS)
        assert res.status_code == 400

        # Invalid ETag
        res = client.put(
            url,
            data=json.dumps(test_data),
            headers={'Content-Type': 'application/json{0}'.format(charset),
                     'If-Match': '"2"'}
        )
        assert res.status_code == 412


@mock.patch('invenio_records.api.Record.validate', _mock_validate_fail)
@pytest.mark.parametrize('content_type', [
    'application/json', 'application/json;charset=utf-8'
])
def test_validation_error(app, test_records, content_type):
    """Test when record validation fail."""
    HEADERS = [
        ('Accept', 'application/json'),
        ('Content-Type', content_type)
    ]

    pid, record = test_records[0]
    obj_id = pid.object_uuid

    record['year'] = 1234

    with app.test_client() as client:
        assert RecordMetadata.query.filter_by(id=obj_id).first().json['year']==2015
        url = record_url(pid)
        res = client.put(url, data=json.dumps(record.dumps()), headers=HEADERS)
        assert res.status_code == 200
        assert RecordMetadata.query.filter_by(id=obj_id).first().json['year']==2015
