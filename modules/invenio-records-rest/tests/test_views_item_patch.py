# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Patch tests."""

from __future__ import absolute_import, print_function

import json

import mock
import pytest
from conftest import IndexFlusher
from helpers import _mock_validate_fail, assert_hits_len, get_json, record_url


@pytest.mark.parametrize('content_type', [
    'application/json-patch+json', 'application/json-patch+json;charset=utf-8'
])
def test_valid_patch(app, es, test_records, test_patch, content_type,
                     search_url, search_class):
    """Test VALID record patch request (PATCH .../records/<record_id>)."""
    HEADERS = [
        ('Accept', 'application/json'),
        ('Content-Type', content_type)
    ]
    pid, record = test_records[0]

    # Check that
    assert record.patch(test_patch)

    with app.test_client() as client:
        # Check that patch and record is not the same value for year.
        url = record_url(pid)
        previous_year = get_json(client.get(url))['metadata']['year']

        # Patch record
        res = client.patch(url, data=json.dumps(test_patch), headers=HEADERS)
        assert res.status_code == 200

        # Check that year changed.
        new_year = get_json(client.get(url))['metadata']['year']
        assert previous_year != new_year
        IndexFlusher(search_class).flush_and_wait()
        res = client.get(search_url, query_string={'year': new_year})
        assert_hits_len(res, 1)


@pytest.mark.parametrize('content_type', [
    'application/json-patch+json', 'application/json-patch+json;charset=utf-8'
])
def test_patch_deleted(app, db, es, test_data, test_patch, content_type,
                       search_url, search_class):
    """Test patching deleted record."""
    HEADERS = [
        ('Accept', 'application/json'),
        ('Content-Type', content_type)
    ]

    with app.test_client() as client:
        # Create record
        res = client.post(
            search_url, data=json.dumps(test_data[0]), headers=HEADERS)
        assert res.status_code == 201
        _id = get_json(res)['id']
        # Delete record.
        url = record_url(_id)
        assert client.delete(url).status_code == 204

        # check patch response for deleted resource
        res = client.patch(url, data=json.dumps(test_patch), headers=HEADERS)
        assert res.status_code == 410
        IndexFlusher(search_class).flush_and_wait()
        res = client.get(search_url,
                         query_string={'title': test_data[0]['title']})
        assert_hits_len(res, 0)


@pytest.mark.parametrize('charset', [
    '', ';charset=utf-8'
])
def test_invalid_patch(app, es, test_records, test_patch, charset, search_url,
                       search_class):
    """Test INVALID record put request (PUT .../records/<record_id>)."""
    HEADERS = [
        ('Accept', 'application/json'),
        ('Content-Type',
         'application/json-patch+json{0}'.format(charset))
    ]
    pid, record = test_records[0]

    with app.test_client() as client:
        url = record_url(pid)

        # Non-existing record
        res = client.patch(
            record_url('0'), data=json.dumps(test_patch), headers=HEADERS)
        assert res.status_code == 404
        IndexFlusher(search_class).flush_and_wait()
        res = client.get(search_url)
        assert_hits_len(res, 0)

        # Invalid accept mime type.
        headers = [('Content-Type',
                    'application/json-patch+json{0}'.format(charset)),
                   ('Accept', 'video/mp4')]
        res = client.patch(url, data=json.dumps(test_patch), headers=headers)
        assert res.status_code == 406

        # Invalid content type
        headers = [('Content-Type', 'video/mp4{0}'.format(charset)),
                   ('Accept', 'application/json')]
        res = client.patch(url, data=json.dumps(test_patch), headers=headers)
        assert res.status_code == 415

        # Invalid Patch
        res = client.patch(
            url,
            data=json.dumps([{'invalid': 'json-patch{0}'.format(charset)}]),
            headers=HEADERS)
        assert res.status_code == 400

        # Invalid JSON
        res = client.patch(url, data='{', headers=HEADERS)
        assert res.status_code == 400

        # Invalid ETag
        res = client.patch(
            url,
            data=json.dumps(test_patch),
            headers={
                'Content-Type': 'application/json-patch+json{0}'.format(
                    charset),
                'If-Match': '"2"'
            }
        )
        assert res.status_code == 412


@mock.patch('invenio_records.api.Record.validate', _mock_validate_fail)
@pytest.mark.parametrize('content_type', [
    'application/json-patch+json', 'application/json-patch+json;charset=utf-8'
])
def test_validation_error(app, test_records, test_patch, content_type):
    """Test VALID record patch request (PATCH .../records/<record_id>)."""
    HEADERS = [
        ('Accept', 'application/json'),
        ('Content-Type', content_type)
    ]
    pid, record = test_records[0]

    # Check that
    assert record.patch(test_patch)

    with app.test_client() as client:
        # Check that patch and record is not the same value for year.
        url = record_url(pid)
        previous_year = get_json(client.get(url))['metadata']['year']

        # Patch record
        res = client.patch(url, data=json.dumps(test_patch), headers=HEADERS)
        assert res.status_code == 400
