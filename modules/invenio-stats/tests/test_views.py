# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test view functions."""
import json
import uuid
import pytest

from invenio_accounts.testutils import login_user_via_session
from invenio_stats.views import QueryFileStatsCount, dbsession_clean
from flask import url_for
from mock import patch

CONTRIBUTOR = 0
REPO_ADMIN = 1
SYSTEM_ADMIN = 2
COM_ADMIN = 3

# class WekoQuery(ContentNegotiatedMethodView):

# class StatsQueryResource(WekoQuery):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_stats_query_resource_guest -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_stats_query_resource_guest(client, db, query_entrypoints,
                              role_users, custom_permission_factory,
                              sample_histogram_query_data):
    """Test post request to stats API."""
    headers = [('Content-Type', 'application/json'),
                ('Accept', 'application/json')]
    resp = client.post(
        url_for('invenio_stats.stat_query'),
        headers=headers,
        data=json.dumps(sample_histogram_query_data))
    assert resp.status_code==401

# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_stats_query_resource_com -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_stats_query_resource_com(client, db, query_entrypoints,
                              role_users, custom_permission_factory,
                              sample_histogram_query_data):
    headers = [('Content-Type', 'application/json'),
                ('Accept', 'application/json')]
    login_user_via_session(client=client, email=role_users[COM_ADMIN]["email"])
    resp = client.post(
        url_for('invenio_stats.stat_query'),
        headers=headers,
        data=json.dumps(sample_histogram_query_data))
    assert resp.status_code==403

# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_stats_query_resource_admin -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_stats_query_resource_admin(client, db, es, query_entrypoints,
                              role_users, custom_permission_factory,
                              sample_histogram_query_data):
    headers = [('Content-Type', 'application/json'),
                ('Accept', 'application/json')]
    login_user_via_session(client=client, email=role_users[SYSTEM_ADMIN]["email"])
    resp = client.post(
        url_for('invenio_stats.stat_query'),
        headers=headers,
        data=json.dumps(sample_histogram_query_data))
    assert resp.status_code==200

    resp = client.post(
        url_for('invenio_stats.stat_query'),
        headers=headers,
        data=json.dumps(None))
    assert resp.status_code==200

    sample_histogram_query_data['mystat']['stat'] = 'test-query'
    resp = client.post(
        url_for('invenio_stats.stat_query'),
        headers=headers,
        data=json.dumps(sample_histogram_query_data))
    assert resp.status_code==400

    sample_histogram_query_data['mystat'] = None
    resp = client.post(
        url_for('invenio_stats.stat_query'),
        headers=headers,
        data=json.dumps(sample_histogram_query_data))
    assert resp.status_code==400

# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_stats_query_resource_error -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_stats_query_resource_error(client, db, query_entrypoints,
                              role_users, custom_permission_factory,
                              sample_histogram_query_data):
    headers = [('Content-Type', 'application/json'),
                ('Accept', 'application/json')]
    login_user_via_session(client=client, email=role_users[SYSTEM_ADMIN]["email"])
    resp = client.post(
        url_for('invenio_stats.stat_query'),
        headers=headers,
        data=json.dumps(sample_histogram_query_data))
    assert resp.status_code==200

    with patch("invenio_stats.queries.ESDateHistogramQuery.run", side_effect=ValueError("test key error")):
        resp = client.post(
            url_for('invenio_stats.stat_query'),
            headers=headers,
            data=json.dumps(sample_histogram_query_data))
        assert resp.status_code==400


class mockPIDVersioning:
    class mockChild:
        def __init__(self, child):
            self.child = child
            pass

        def all(self):
            return [self.child]

    def __init__(self, child):
        self.exists = True
        self.children = self.mockChild(child)
        pass

# class QueryRecordViewCount(WekoQuery):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_query_record_view_count -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_query_record_view_count(client, db, es, records):
    _uuid = str(records[0][0].object_uuid)
    
    # get
    res = client.get(
        url_for('invenio_stats.get_record_view_count', record_id=_uuid))
    assert res.status_code==200

    # post
    _data1 = {'date': 'total'}
    _data2 = {'date': '2022-09'}
    headers = [('Content-Type', 'application/json'), ('Accept', 'application/json')]
    res = client.post(
        url_for('invenio_stats.get_record_view_count', record_id=_uuid),
        headers=headers, data=json.dumps(_data1))
    assert res.status_code==200

    res = client.post(
        url_for('invenio_stats.get_record_view_count', record_id=_uuid),
        headers=headers, data=json.dumps(_data2))
    assert res.status_code==200

    _res_data = {
        "count": 10,
        "buckets": [
            {
                "key": "country1",
                "count": 3
            },
            {
                "key": "country2",
                "count": 2
            }
        ]
    }
    with patch("invenio_stats.views.PIDVersioning", side_effect=mockPIDVersioning):
        with patch("invenio_stats.queries.ESTermsQuery.run", return_value=_res_data):
            res = client.get(
                url_for('invenio_stats.get_record_view_count', record_id=_uuid))
            assert res.status_code==200

# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_query_record_view_count_error -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_query_record_view_count_error(client, db, records):
    _uuid = uuid.uuid4()
    res = client.get(
        url_for('invenio_stats.get_record_view_count', record_id=_uuid))
    assert res.status_code==200

    _uuid = str(records[0][0].object_uuid)
    res = client.get(
        url_for('invenio_stats.get_record_view_count', record_id=_uuid))
    assert res.status_code==200

    # GET:Invalid uuid
    res = client.get(
        url_for('invenio_stats.get_record_view_count', record_id='test'))
    assert res.status_code==400

    # POST:Invalid uuid
    res = client.post(
        url_for('invenio_stats.get_record_view_count', record_id='test'),
        data=json.dumps({'date': 'total'}),
        content_type='application/json',
    )
    assert res.status_code==400

    # POST:Invalid request data
    res = client.post('/api/stats/{}'.format(_uuid))
    assert res.status_code==400


# class QueryFileStatsCount(WekoQuery):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_query_file_stats_count -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_query_file_stats_count(client, db):
    _uuid = uuid.uuid4()

    # get_data
    res = QueryFileStatsCount.get_data(QueryFileStatsCount, bucket_id=_uuid, file_key='test.pdf', root_file_id=uuid.uuid4())
    assert res=={'download_total': 0, 'preview_total': 0, 'country_list': []}

    # get
    res = client.get(
        url_for('invenio_stats.get_file_stats_count', bucket_id=_uuid, file_key='test{URL_SLASH}test.pdf'))
    assert res.status_code==200

    _res_data = {
        "value": 20,
        "buckets": [
            {
                "key": "country1",
                "value": 3,

            },
            {
                "key": "country2",
                "value": 2
            }
        ]
    }
    with patch("invenio_stats.queries.ESWekoFileStatsQuery.run", return_value=_res_data):
        res = client.get(
            url_for('invenio_stats.get_file_stats_count', bucket_id=_uuid, file_key='test.pdf'))
        assert res.status_code==200

    _res_data = {
        "value": 20,
        "buckets": [
            {
                "key": "country1",
                "count": 3,

            }
        ]
    }
    with patch("invenio_stats.queries.ESWekoFileStatsQuery.run", return_value=_res_data):
        res = client.get(
            url_for('invenio_stats.get_file_stats_count', bucket_id=_uuid, file_key='test.pdf'))
        assert res.status_code==200

    # post
    _data1 = {'date': 'total'}
    _data2 = {'date': '2022-09'}
    headers = [('Content-Type', 'application/json'), ('Accept', 'application/json')]
    res = client.post(
        url_for('invenio_stats.get_file_stats_count', bucket_id=_uuid, file_key='test.pdf'),
        headers=headers, data=json.dumps(_data1))
    assert res.status_code==200
    res = client.post(
        url_for('invenio_stats.get_file_stats_count', bucket_id=_uuid, file_key='test.pdf'),
        headers=headers, data=json.dumps(_data2))
    assert res.status_code==200


# class QueryItemRegReport(WekoQuery):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_query_item_reg_report -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 403),
        (1, 200),
        (2, 200),
        (3, 403),
        (4, 403)
    ],
)
def test_query_item_reg_report(client, role_users, id, status_code):
    # get
    login_user_via_session(client=client, email=role_users[id]["email"])
    res = client.get(
        url_for('invenio_stats.get_item_registration_report',
                target_report='1', start_date='0', end_date='0', unit='Year'))
    assert res.status_code==status_code

    res = client.get(
        url_for('invenio_stats.get_item_registration_report',
                target_report='1', start_date='0', end_date='0', unit='Year', p='A'))
    assert res.status_code==status_code

# class QueryRecordViewReport(WekoQuery):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_query_record_view_report -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 403),
        (1, 200),
        (2, 200),
        (3, 403),
        (4, 403)
    ],
)
def test_query_record_view_report(client, role_users, id, status_code):
    # get
    login_user_via_session(client=client, email=role_users[id]["email"])
    res = client.get(
        url_for('invenio_stats.get_record_view_report', year=2022, month=9))
    assert res.status_code==status_code


# class QueryRecordViewPerIndexReport(WekoQuery):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_query_record_view_per_index_report -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 403),
        (1, 200),
        (2, 200),
        (3, 403),
        (4, 403)
    ],
)
def test_query_record_view_per_index_report(client, role_users, id, status_code):
    # get
    login_user_via_session(client=client, email=role_users[id]["email"])
    res = client.get(
        url_for('invenio_stats.get_record_view_per_index_report', year=2022, month=9))
    assert res.status_code==status_code


# class QueryFileReports(WekoQuery):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_query_record_view_per_index_report -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 403),
        (1, 200),
        (2, 200),
        (3, 403),
        (4, 403)
    ],
)
def test_query_file_reports(client, role_users, id, status_code):
    # get
    login_user_via_session(client=client, email=role_users[id]["email"])
    res = client.get(
        url_for('invenio_stats.get_file_reports', event='file_download', year=2022, month=9))
    assert res.status_code==status_code


# class QueryCommonReports(WekoQuery):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_query_common_reports -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_query_common_reports(client):
    # get
    res = client.get(
        url_for('invenio_stats.get_common_report', event='top_page_access', year=2022, month=9))
    assert res.status_code==200


# class QueryCeleryTaskReport(WekoQuery):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_query_celery_task_report -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 403),
        (1, 200),
        (2, 200),
        (3, 403),
        (4, 403)
    ],
)
def test_query_celery_task_report(client, role_users, id, status_code):
    # get
    login_user_via_session(client=client, email=role_users[id]["email"])
    res = client.get(
        url_for('invenio_stats.get_celery_task_report', task_name='harvest'))
    assert res.status_code==status_code

    _res_data = {
        "buckets": [
            {
                "key": "task1",
                "field": "test_field1",
                "buckets": [
                    {
                        "key": "task1-1",
                        "field": "test_field1-1"
                    }
                ]
            }
        ]
    }
    with patch("invenio_stats.queries.ESTermsQuery.run", return_value=_res_data):
        res = client.get(
            url_for('invenio_stats.get_celery_task_report', task_name='harvest'))
        assert res.status_code==status_code


# class QuerySearchReport(ContentNegotiatedMethodView):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_query_search_report -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 403),
        (1, 200),
        (2, 200),
        (3, 403),
        (4, 403)
    ],
)
def test_query_search_report(client, role_users, id, status_code):
    # get
    login_user_via_session(client=client, email=role_users[id]["email"])
    res = client.get(
        url_for('invenio_stats.get_search_report', year=2022, month=9))
    assert res.status_code==status_code


# def dbsession_clean(exception):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_dbsession_clean -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_dbsession_clean(app):
    with patch("invenio_db.db.session.commit", side_effect=Exception):
        assert not dbsession_clean(None)
        assert not dbsession_clean('')