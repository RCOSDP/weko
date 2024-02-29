# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Record creation."""

from __future__ import absolute_import, print_function

import json
import os

import mock
import pytest
from tests.conftest import IndexFlusher
from tests.helpers import _mock_validate_fail, assert_hits_len, get_json, record_url
from mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError
from weko_redis.redis import RedisConnection
from elasticsearch_dsl import response, Search

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

        # Create record
        res = client.post(
            search_url, data=json.dumps(test_data[0]), headers=HEADERS)
        assert res.status_code == 201

        # Check that the returned record matches the given data
        data = get_json(res)
        for k in test_data[0].keys():
            assert data['metadata'][k] == test_data[0][k]

        # Recid has been added in control number
        assert data['metadata']['control_number']

        # Check location header
        assert res.headers['Location'] == data['links']['self']

        # Record can be retrieved.
        assert client.get(record_url(data['id'])).status_code == 200

        IndexFlusher(search_class).flush_and_wait()
        # Record shows up in search
        res = client.get(search_url,
                         query_string={"control_number":
                                       data['metadata']['control_number']})
        assert_hits_len(res, 1)


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

        # Invalid accept type
        headers = [('Content-Type', 'application/json'),
                   ('Accept', 'video/mp4')]
        res = client.post(
            search_url, data=json.dumps(test_data[0]), headers=headers)
        assert res.status_code == 406
        # check that nothing is indexed
        res = client.get(search_url, query_string=dict(page=1, size=2))
        assert_hits_len(res, 0)

        # Invalid content-type
        headers = [('Content-Type', 'video/mp4'),
                   ('Accept', 'application/json')]
        res = client.post(
            search_url, data=json.dumps(test_data[0]), headers=headers)
        assert res.status_code == 415
        res = client.get(search_url, query_string=dict(page=1, size=2))
        assert_hits_len(res, 0)

        # Invalid JSON
        res = client.post(search_url, data='{fdssfd', headers=HEADERS)
        assert res.status_code == 400
        res = client.get(search_url, query_string=dict(page=1, size=2))
        assert_hits_len(res, 0)

        # No data
        res = client.post(search_url, headers=HEADERS)
        assert res.status_code == 400
        res = client.get(search_url, query_string=dict(page=1, size=2))
        assert_hits_len(res, 0)

        # Posting a list instead of dictionary
        pytest.raises(
            TypeError, client.post, search_url, data='[]', headers=HEADERS)

        # Bad internal error:
        with patch('invenio_records_rest.views.db.session.commit') as m:
            m.side_effect = SQLAlchemyError()

            pytest.raises(
                SQLAlchemyError,
                client.post, search_url, data=json.dumps(test_data[0]),
                headers=HEADERS)


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
        assert res.status_code == 400


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
        assert res.status_code == 400
        data = get_json(res)
        assert data['message']

@pytest.yield_fixture()
def i18n_app(app):
    with app.test_request_context(
        headers=[('Accept-Language','ja')]):
        app.extensions['invenio-i18n'] = MagicMock()
        app.extensions['invenio-i18n'].language = "ja"
        yield app
@pytest.yield_fixture()
def radis_app(app):
    app.config.update(
        CACHE_TYPE="redis",
        ACCOUNTS_SESSION_REDIS_DB_NO=1,
        CACHE_REDIS_HOST=os.environ.get("INVENIO_REDIS_HOST"),
        REDIS_PORT="6379"
    )
    yield app
def test_RecordsListResource_get(app, i18n_app, radis_app, db, es, test_data, search_url, search_class):
    """Test VALID record creation request (POST .../records/)."""
    json_data = {
        "took": 137,
        "timed_out": "false",
        "_shards": {
            "total": 3,
            "successful": 3,
            "skipped": 0,
            "failed": 0
        },
        "hits": {
            "total": 3,
            "max_score": 1,
            "hits": [
                {
                    "_index": "tenant1-weko-item-v1.0.0",
                    "_type": "item-v1.0.0",
                    "_id": "f7d87c57-e3d0-4f8a-a40e-cd8167690462",
                    "_version": "1.0",
                    "_score": 1,
                    "_source": {
                        "control_number": 1,
                        "_item_metadata": {
                            "owner": "1"
                        },
                        "_oai": {
                            "id": "oai:weko3.example.org:00000001"
                        },
                        "content": [
                            {
                                "filename": "test1.pdf"
                            }
                        ]
                    }
                },
                {
                    "_index": "tenant1-weko-item-v1.0.0",
                    "_type": "item-v1.0.0",
                    "_id": "f7d87c57-e3d0-4f8a-a40e-cd8167690462",
                    "_version": "1.0",
                    "_score": 1,
                    "_source": {
                        "control_number": 1,
                        "_item_metadata": {
                            "owner": "1"
                        },
                        "_oai": {
                            "id": "oai:weko3.example.org:00000001"
                        },
                        "content": [
                            {
                                "filename": "test2.pdf"
                            }
                        ]
                    }
                },
                {
                    "_index": "tenant1-weko-item-v1.0.0",
                    "_type": "item-v1.0.0",
                    "_id": "f7d87c57-e3d0-4f8a-a40e-cd8167690462",
                    "_version": "1.0",
                    "_score": 1,
                    "_source": {
                        "control_number": 1,
                        "_item_metadata": {
                            "owner": "1"
                        },
                        "_oai": {
                            "id": "oai:weko3.example.org:00000001"
                        },
                        "content": [
                            {
                                "filename": "test3.pdf"
                            }
                        ]
                    }
                }
            ]
        }
    }
    search_result = response.Response(Search(), json_data)
    cache_name = "anonymous_user"
    mock_user = MagicMock()
    mock_user.is_authenticated = False

    with app.test_client() as client:
        with patch('weko_admin.utils.get_facet_search_query', return_value=MagicMock()):
            with patch('weko_search_ui.permissions.search_permission.can', return_value=MagicMock()):
                with patch("flask_login.utils._get_user", return_value=mock_user):
                    with patch("elasticsearch_dsl.Search.execute", return_value=search_result):
                        redis_connection = RedisConnection()
                        sessionstore = redis_connection.connection(db=app.config['ACCOUNTS_SESSION_REDIS_DB_NO'], kv = True)
                        cache_key = f"{cache_name}_url_args"
                        cache_data = {'page': '1'}
                        sessionstore.put(cache_key, (json.dumps(cache_data)).encode('utf-8'))
                        res = client.get(search_url, query_string=dict(page=1, size=2))
                        assert res.status_code == 200

                        cache_key = f"{cache_name}_url_args"
                        sessionstore.delete(cache_key)
                        res = client.get(search_url, query_string=dict(page=1, size=2))
                        assert res.status_code == 200

                        cache_key = f"{cache_name}_url_args"
                        cache_data = {'page': '1'}
                        sessionstore.put(cache_key, (json.dumps(cache_data)).encode('utf-8'))
                        cache_key = cache_name
                        cache_data = {"10000": {"control_number": 1}}
                        sessionstore.put(cache_key, (json.dumps(cache_data)).encode('utf-8'))
                        res = client.get(search_url, query_string=dict(page=10000))
                        assert res.status_code == 200

                        cache_key = f"{cache_name}_url_args"
                        cache_data = {'page': '1'}
                        sessionstore.put(cache_key, (json.dumps(cache_data)).encode('utf-8'))
                        cache_key = cache_name
                        cache_data = {"1": {"control_number": [1]}, "2": {"control_number": 1}}
                        sessionstore.put(cache_key, (json.dumps(cache_data)).encode('utf-8'))
                        res = client.get(search_url, query_string=dict(page=10000))
                        assert res.status_code == 200
