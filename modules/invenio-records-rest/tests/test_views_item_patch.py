# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

# .tox/c1/bin/pytest --cov=invenio_records_rest tests/test_views_item_patch.py -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/invenio-records-rest/.tox/c1/tmp

"""Patch tests."""

from __future__ import absolute_import, print_function

import json

import mock
import pytest
from tests.conftest import IndexFlusher
from tests.helpers import _mock_validate_fail, assert_hits_len, get_json, record_url
from invenio_records.models import RecordMetadata

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
    obj_id = pid.object_uuid

    # Check that
    assert record.patch(test_patch)

    with app.test_client() as client:
        # Check that patch and record is not the same value for year.
        url = record_url(pid)
        previous_year = get_json(client.get(url))['metadata']['year']

        # Patch record
        assert RecordMetadata.query.filter_by(id=obj_id).first().json['year']==2015
        res = client.patch(url, data=json.dumps(test_patch), headers=HEADERS)
        assert res.status_code == 200
        assert RecordMetadata.query.filter_by(id=obj_id).first().json['year']==1985

        # Check that year changed.
        new_year = get_json(client.get(url))['metadata']['year']
        assert previous_year != new_year
        # IndexFlusher(search_class).flush_and_wait()
        #res = client.get(search_url, query_string={'year': new_year})
        #assert_hits_len(res, 1)


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
        assert res.status_code == 200
        _id = get_json(res)['id']
        # Delete record.
        url = record_url(_id)
        assert client.delete(url).status_code == 204

        # check patch response for deleted resource
        with pytest.raises(AttributeError):
            res = client.patch(url, data=json.dumps(test_patch), headers=HEADERS)
            #assert res.status_code == 410
            #IndexFlusher(search_class).flush_and_wait()
            #res = client.get(search_url,
            #                 query_string={'title': test_data[0]['title']})
            #assert_hits_len(res, 0)


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
    obj_id = pid.object_uuid

    with app.test_client() as client:
        url = record_url(pid)

        # Non-existing record
        res = client.patch(
            record_url('0'), data=json.dumps(test_patch), headers=HEADERS)
        assert res.status_code == 404
        # IndexFlusher(search_class).flush_and_wait()
        # res = client.get(search_url)
        # assert_hits_len(res, 0)

        # Invalid accept mime type.
        assert RecordMetadata.query.filter_by(id=obj_id).first().json['year']==2015
        # headers = [('Content-Type',
        #             'application/json-patch+json{0}'.format(charset)),
        #            ('Accept', 'video/mp4')]
        # res = client.patch(url, data=json.dumps(test_patch), headers=headers)
        # assert res.status_code == 406
        # assert RecordMetadata.query.filter_by(id=obj_id).first().json['year']==2015

        # Invalid content type
        headers = [('Content-Type', 'video/mp4{0}'.format(charset)),
                   ('Accept', 'application/json')]
        res = client.patch(url, data=json.dumps(test_patch), headers=headers)
        assert res.status_code == 415
        assert RecordMetadata.query.filter_by(id=obj_id).first().json['year']==2015

        # Invalid Patch
        res = client.patch(
            url,
            data=json.dumps([{'invalid': 'json-patch{0}'.format(charset)}]),
            headers=HEADERS)
        assert res.status_code == 200
        assert RecordMetadata.query.filter_by(id=obj_id).first().json['year']==2015

        # Invalid JSON
        res = client.patch(url, data='{', headers=HEADERS)
        assert res.status_code == 400
        assert RecordMetadata.query.filter_by(id=obj_id).first().json['year']==2015

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
        assert RecordMetadata.query.filter_by(id=obj_id).first().json['year']==2015


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
        assert res.status_code == 200
