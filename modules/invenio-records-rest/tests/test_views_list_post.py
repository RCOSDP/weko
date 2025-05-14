# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

# .tox/c1/bin/pytest --cov=invenio_records_rest tests/test_views_list_post.py -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/invenio-records-rest/.tox/c1/tmp

"""Record creation."""

from __future__ import absolute_import, print_function

import json

import mock
import pytest
from tests.conftest import IndexFlusher
from tests.helpers import _mock_validate_fail, assert_hits_len, get_json, record_url
from mock import patch
from sqlalchemy.exc import SQLAlchemyError

from invenio_records.models import RecordMetadata


# .tox/c1/bin/pytest --cov=invenio_records_rest tests/test_views_list_post.py -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/invenio-records-rest/.tox/c1/tmp
@pytest.mark.parametrize('content_type', [
    'application/json', 'application/json;charset=utf-8'
])
def test_valid_create(app, db, es, test_data, search_url, search_class,
                      content_type):
    """Test VALID record creation request (POST .../records/)."""
    with app.test_client() as client:
        HEADERS = [
            ('Accept', 'application/json'),
            ('Content-Type', content_type)
        ]
        HEADERS.append(('Content-Type', content_type))

        assert len(RecordMetadata.query.all()) == 0

        # Create record
        res = client.post(
            search_url, data=json.dumps(test_data[0]), headers=HEADERS)
        assert res.status_code == 200

        # Check that the returned record matches the given data
        data = get_json(res)
        for k in test_data[0].keys():
            assert data['metadata'][k] == test_data[0][k]

        # Recid has been added in control number
        assert len(RecordMetadata.query.all()) == 1
        assert data['metadata']['control_number'] == '1'

        # Check location header
        assert res.headers['Location'] == data['links']['self']

        # Record can be retrieved.
        assert client.get(record_url(data['id'])).status_code == 200

        # IndexFlusher(search_class).flush_and_wait()
        # Record shows up in search
        #with patch('weko_search_ui.permissions.search_permission.can', return_value=True):
        #    res = client.get(search_url,
        #                    query_string={"control_number":
        #                                data['metadata']['control_number']})
        #    assert_hits_len(res, 1)


@pytest.mark.parametrize('content_type', [
    'application/json', 'application/json;charset=utf-8'
])
def test_invalid_create(app, db, es, test_data, search_url, content_type):
    """Test INVALID record creation request (POST .../records/)."""
    with app.test_client() as client:
        HEADERS = [
            ('Accept', 'application/json'),
            ('Content-Type', content_type)
        ]

        assert len(RecordMetadata.query.all()) == 0

        # Invalid content-type
        headers = [('Content-Type', 'video/mp4'),
                   ('Accept', 'application/json')]
        res = client.post(
            search_url, data=json.dumps(test_data[0]), headers=headers)
        assert res.status_code == 415
        #res = client.get(search_url, query_string=dict(page=1, size=2))
        #assert_hits_len(res, 0)
        assert len(RecordMetadata.query.all()) == 0

        # Invalid JSON
        res = client.post(search_url, data='{fdssfd', headers=HEADERS)
        assert res.status_code == 400
        #res = client.get(search_url, query_string=dict(page=1, size=2))
        #assert_hits_len(res, 0)
        assert len(RecordMetadata.query.all()) == 0

        # No data
        res = client.post(search_url, headers=HEADERS)
        assert res.status_code == 400
        #res = client.get(search_url, query_string=dict(page=1, size=2))
        #assert_hits_len(res, 0)
        assert len(RecordMetadata.query.all()) == 0

        # Posting a list instead of dictionary
        res = client.post(search_url, data='[]', headers=HEADERS)
        assert res.status_code == 500

        # Bad internal error:
        with patch('invenio_records_rest.views.db.session.commit') as m:
            m.side_effect = SQLAlchemyError()
            res = client.post(search_url, data=json.dumps(test_data[0]), headers=HEADERS)
            assert res.status_code == 500
            assert len(RecordMetadata.query.all()) == 0

        # Invalid accept type
        headers = [('Content-Type', 'application/json'),
                   ('Accept', 'video/mp4')]
        res = client.post(
            search_url, data=json.dumps(test_data[0]), headers=headers)
        assert res.status_code == 406
        # check that nothing is indexed
        #res = client.get(search_url, query_string=dict(page=1, size=2))
        #assert_hits_len(res, 0)
        assert len(RecordMetadata.query.all()) == 1


@mock.patch('invenio_records.api.Record.validate', _mock_validate_fail)
@pytest.mark.parametrize('content_type', [
    'application/json', 'application/json;charset=utf-8'
])
def test_validation_error(app, db, test_data, search_url, content_type):
    """Test when record validation fail."""
    with app.test_client() as client:
        HEADERS = [
            ('Accept', 'application/json'),
            ('Content-Type', content_type)
        ]

        # Create record
        res = client.post(
            search_url, data=json.dumps(test_data[0]), headers=HEADERS)
        assert res.status_code == 500


@pytest.mark.parametrize('content_type', [
    'application/json', 'application/json;charset=utf-8'
])
def test_jsonschema_validation_error(app, db, search_url, content_type):
    """Test when jsonschema validation fails."""
    record = {
        'title': 1,
        '$schema': {
            'properties': {
                'title': {'type': 'string'}
            }
        }
    }
    with app.test_client() as client:
        HEADERS = [
            ('Accept', 'application/json'),
            ('Content-Type', content_type)
        ]

        # Create record
        res = client.post(
            search_url, data=json.dumps(record), headers=HEADERS)
        assert res.status_code == 500
        data = get_json(res)
        assert data['message']
