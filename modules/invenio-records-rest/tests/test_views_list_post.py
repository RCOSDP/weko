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
from invenio_search import RecordsSearch
from invenio_records_rest.views import RecordsListResource

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

#.tox/c1/bin/pytest --cov=invenio_records_rest tests/test_views_list_post.py::test_RecordsListResource_get -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/invenio-records-rest/.tox/c1/tmp
def test_RecordsListResource_get(app, i18n_app, db, es, test_data, search_url, search_class):
    """Test VALID record creation request (POST .../records/)."""

    app.config.update(
        CACHE_REDIS_HOST='redis',
        REDIS_PORT='6379'
    )

    json_data = {
        "hits": {
            "total": 1,
            "hits": [
                {
                    "_id": "f7d87c57-e3d0-4f8a-a40e-cd8167690462",
                    "_version": "1.0",
                    "_source": {
                        "control_number": 1,
                        "_item_metadata": {
                            "owner": "1"
                        }
                    }
                }
            ]
        }
    }
    search_result = response.Response(Search(), json_data)
    cache_name = "anonymous_user"
    mock_user = MagicMock()
    mock_user.is_authenticated = False

    with app.test_client() as client, \
        patch('weko_admin.utils.get_facet_search_query', return_value=MagicMock()), \
        patch('weko_search_ui.permissions.search_permission.can', return_value=MagicMock()), \
        patch('flask_login.utils._get_user', return_value=mock_user), \
        patch("elasticsearch_dsl.Search.execute", return_value=search_result) as mock_execute:
            redis_connection = RedisConnection()
            sessionstore = redis_connection.connection(db=app.config['ACCOUNTS_SESSION_REDIS_DB_NO'], kv = True)
            cache_key = f"{cache_name}_url_args"
            cache_data = {'page': '1', 'q':''}
            sessionstore.put(cache_key, (json.dumps(cache_data)).encode('utf-8'))

            res = client.get(search_url, query_string=dict(page=1, size=2, q=""))
            assert res.status_code == 200

            cache_key = f"{cache_name}_url_args"
            sessionstore.delete(cache_key)
            res = client.get(search_url, query_string=dict(page=1, size=2, q=""))
            assert res.status_code == 200

            cache_key = f"{cache_name}_url_args"
            cache_data = {'page': '1', 'q':''}
            sessionstore.put(cache_key, (json.dumps(cache_data)).encode('utf-8'))
            cache_key = cache_name
            cache_data = {"10000": {"control_number": 1}}
            sessionstore.put(cache_key, (json.dumps(cache_data)).encode('utf-8'))
            res = client.get(search_url, query_string=dict(page=10000,q=""))
            assert res.status_code == 200

            cache_key = f"{cache_name}_url_args"
            cache_data = {'page': '1', 'q':''}
            sessionstore.put(cache_key, (json.dumps(cache_data)).encode('utf-8'))
            cache_key = cache_name
            cache_data = {"1": {"control_number": [1]}, "2": {"control_number": 1}}
            sessionstore.put(cache_key, (json.dumps(cache_data)).encode('utf-8'))
            res = client.get(search_url, query_string=dict(page=10000, q=""))
            assert res.status_code == 200
            with patch("weko_index_tree.api.Indexes.get_child_list_recursive",return_value = [1235]) as recursive, \
                 patch("invenio_records_rest.views.RecordsListResource._do_custom_sort") as do:
                    res = client.get(search_url, query_string=dict(page=1, size=2, format="rss", recursive=1, idx=[1234,1235], sort="custom_sort"))
                    assert res.status_code == 200
                    assert do.assert_called
                    assert recursive.assert_not_called
                    res = client.get(search_url, query_string=dict(page=1, size=2, format="rss", recursive=1, index_id=[1234,1235], sort="custom_sort"))
                    assert res.status_code == 200
                    assert do.assert_not_called
                    with patch("weko_index_tree.api.Indexes.get_index",return_value=[1235]):
                        search_result.hits.total = 10001
                        res = client.get(search_url, query_string=dict(page=1, size=2, format="rss", recursive=1, idx=[1234,1235], sort="custom_sort"))
                        assert res.status_code == 200
                        assert do.assert_not_called
                        assert recursive.assert_called
                        res = client.get(search_url, query_string=dict(page=1, size=2, recursive=1, idx=[1234,1235], sort="custom_sort"))
                        assert res.status_code == 302
                        res = client.get(search_url, query_string=dict(page=1, size=2, format='', recursive=1, idx=[1234,1235], sort="custom_sort"))
                        assert res.status_code == 302
                        res = client.get(search_url, query_string=dict(page=1, size=2, format="html", recursive=1, idx=[1234,1235], sort="custom_sort"))
                        assert res.status_code == 302



#.tox/c1/bin/pytest --cov=invenio_records_rest tests/test_views_list_post.py::test__override_params_for_customsort -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/invenio-records-rest/.tox/c1/tmp
@pytest.mark.parametrize(
    "is_asc, expect",
    [
        (True, [{'path': {'mode': 'min', 'order': 'asc'}}, {'_created': {'order': 'asc', 'unmapped_type': 'long'}}]),
        (False, [{'path': {'mode': 'max', 'order': 'desc'}}, {'_created': {'order': 'desc', 'unmapped_type': 'long'}}]),
    ]
)
def test__override_params_for_customsort(app, is_asc, expect):
    test_class = RecordsSearch()
    test_class2 = RecordsListResource.__new__(RecordsListResource)
    test_class2.max_result_window = 10000
    result=test_class2._override_params_for_customsort(test_class,is_asc)
    assert result._sort == expect

#.tox/c1/bin/pytest --cov=invenio_records_rest tests/test_views_list_post.py::test__do_custom_sort -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/invenio-records-rest/.tox/c1/tmp
@pytest.mark.parametrize(
    "is_asc, size, page, format, q, expect_len, expect_start, expect_end",
    [
        (True, 20, 1, "rss", None, 20, "2000020", "2000001"),
        (True, 20, 1, "rss", "test", 20, "2000001", "2000020"),
        (True, 20, 1, "atom", None, 20, "2000020", "2000001"),
        (True, 20, 1, "atom", "test", 20, "2000001", "2000020"),
        (True, 20, 1, "jpcoar", None, 20, "2000020", "2000001"),
        (True, 20, 1, "jpcoar", "test", 20, "2000001", "2000020"),
        (True, 20, 1, "html", None, 20, "2000001", "2000020"),
        (True, 20, 1, "html", "test", 20, "2000001", "2000020"),
        (True, 30, 3, "rss", None, 30, "2000090", "2000061"),
        (True, 30, 3, "rss", "test", 30, "2000061", "2000090"),
        (True, 30, 3, "atom", None, 30, "2000090", "2000061"),
        (True, 30, 3, "atom", "test", 30, "2000061", "2000090"),
        (True, 30, 3, "jpcoar", None, 30, "2000090", "2000061"),
        (True, 30, 3, "jpcoar", "test", 30, "2000061", "2000090"),
        (True, 30, 3, "html", None, 30, "2000061", "2000090"),
        (True, 30, 3, "html", "test", 30, "2000061", "2000090"),
        (False, 20, 1, "rss", None, 20, "2000081", "2000100"),
        (False, 20, 1, "rss", "test", 20, "2000100", "2000081"),
        (False, 20, 1, "atom", None, 20, "2000081", "2000100"),
        (False, 20, 1, "atom", "test", 20, "2000100", "2000081"),
        (False, 20, 1, "jpcoar", None, 20, "2000081", "2000100"),
        (False, 20, 1, "jpcoar", "test", 20, "2000100", "2000081"),
        (False, 20, 1, "html", None, 20, "2000100", "2000081"),
        (False, 20, 1, "html", "test", 20, "2000100", "2000081"),
        (False, 30, 3, "rss", None, 30, "2000011", "2000040"),
        (False, 30, 3, "rss", "test", 30, "2000040", "2000011"),
        (False, 30, 3, "atom", None, 30, "2000011", "2000040"),
        (False, 30, 3, "atom", "test", 30, "2000040", "2000011"),
        (False, 30, 3, "jpcoar", None, 30, "2000011", "2000040"),
        (False, 30, 3, "jpcoar", "test", 30, "2000040", "2000011"),
        (False, 30, 3, "html", None, 30, "2000040", "2000011"),
        (False, 30, 3, "html", "test", 30, "2000040", "2000011"),
        (True, 100, 100, "rss", None,  0, "", ""),
        (True, 20, 1, "json", None, 20, "2000001", "2000020")
    ],
)
def test__do_custom_sort(app, is_asc, size, page, format, q, expect_len,
                         expect_start, expect_end, prepare_search_result):
    search_result_dict, target, return_value = prepare_search_result
    query_string = f"/?format={format}"
    if q is not None:
        query_string += f"&q={q}"
    with app.test_request_context(query_string), \
         patch("weko_index_tree.api.Indexes.get_item_sort",
               return_value=return_value):
        RecordsListResource._do_custom_sort(
            search_result_dict,target, is_asc, page, size)
        if expect_len > 0:
            assert len(search_result_dict["hits"]["hits"]) == expect_len
            assert search_result_dict[
                "hits"]["hits"][0]["_source"]["control_number"] == expect_start
            assert search_result_dict[
                "hits"]["hits"][size-1]["_source"]["control_number"] == expect_end
        else:
            assert search_result_dict["hits"]["hits"] == []

#.tox/c1/bin/pytest --cov=invenio_records_rest tests/test_views_list_post.py::test__customsort_priority -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/invenio-records-rest/.tox/c1/tmp
def test__customsort_priority(prepare_search_result2):
    search_result_dict, target, return_value = prepare_search_result2
    custom_sort = {}
    hit = next(
            h for h in search_result_dict["hits"]["hits"]
            if h["_source"]["control_number"] == "2000035"
        )

    hit2 = next(
            h for h in search_result_dict["hits"]["hits"]
            if h["_source"]["control_number"] == "2000070"
        )
    with patch("weko_index_tree.api.Indexes.get_item_sort",return_value = return_value) as get_item_sort:
        result = RecordsListResource._customsort_priority(hit,target,True,custom_sort)
        expect = (1623632832836, 0, return_value.get("2000035"), '2026-03-30T04:08:30.080849+00:00', 2000035)
        assert result == expect

        result = RecordsListResource._customsort_priority(hit2,target,True,custom_sort)
        expect = (1623632832836, 0, return_value.get("2000070"), '2026-03-30T04:08:30.080849+00:00', 2000070)
        assert result == expect
        assert get_item_sort.assert_called_once

    custom_sort = {}
    with patch("weko_index_tree.api.Indexes.get_item_sort",return_value = None):
        result = RecordsListResource._customsort_priority(hit,target,True,custom_sort)
        expect = (1623632832836, 1, None, '2026-03-30T04:08:30.080849+00:00', 2000035)
        assert result == expect

