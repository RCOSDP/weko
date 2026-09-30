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
    assert resp.status_code==200

# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_stats_query_resource_contributor -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_stats_query_resource_contributor(client, db, query_entrypoints,
                              role_users, custom_permission_factory,
                              sample_histogram_query_data):
    headers = [('Content-Type', 'application/json'),
                ('Accept', 'application/json')]
    login_user_via_session(client=client, email=role_users[CONTRIBUTOR]["email"])
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


class mockPermissionChecker:
    def __init__(self, result):
        self.result = result

    def can(self):
        return self.result


def patch_page_permission(result):
    """Patch the record detail page permission used by the stats views."""
    return patch(
        "weko_records_ui.permissions.page_permission_factory",
        return_value=mockPermissionChecker(result))

# class QueryRecordViewCount(WekoQuery):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_query_record_view_count -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_query_record_view_count(client, db, es, records):
    with patch_page_permission(True):
        _test_query_record_view_count(client, records)


def _test_query_record_view_count(client, records):
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
    # リクエストの後はフィクスチャのオブジェクトがセッションから外れるので先に控える
    record_uuid = str(records[0][0].object_uuid)
    with patch_page_permission(True):
        # record does not exist
        _uuid = uuid.uuid4()
        res = client.get(
            url_for('invenio_stats.get_record_view_count', record_id=_uuid))
        assert res.status_code==404
        res = client.post(
            url_for('invenio_stats.get_record_view_count', record_id=_uuid),
            data=json.dumps({'date': 'total'}),
            content_type='application/json',
        )
        assert res.status_code==404

        res = client.get(
            url_for('invenio_stats.get_record_view_count', record_id=record_uuid))
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
        res = client.post('/api/stats/{}'.format(record_uuid))
        assert res.status_code==400
        for _data in [{}, {'date': 'test'}, {'date': 202209}, []]:
            res = client.post(
                url_for('invenio_stats.get_record_view_count',
                        record_id=record_uuid),
                data=json.dumps(_data),
                content_type='application/json',
            )
            assert res.status_code==400


# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_query_record_view_count_permission -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_query_record_view_count_permission(client, db, records):
    _uuid = str(records[0][0].object_uuid)
    url = url_for('invenio_stats.get_record_view_count', record_id=_uuid)
    headers = [('Content-Type', 'application/json'),
               ('Accept', 'application/json')]

    # the permission of the record detail page is checked
    with patch_page_permission(True) as mock_factory:
        res = client.get(url)
        assert res.status_code==200
        assert str(mock_factory.call_args[0][0].id) == _uuid

        res = client.post(url, headers=headers,
                          data=json.dumps({'date': 'total'}))
        assert res.status_code==200
        assert str(mock_factory.call_args[0][0].id) == _uuid

    # users who cannot view the record are rejected
    with patch_page_permission(False):
        res = client.get(url)
        assert res.status_code==403

        res = client.post(url, headers=headers,
                          data=json.dumps({'date': 'total'}))
        assert res.status_code==403


# class QueryFileStatsCount(WekoQuery):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_query_file_stats_count -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_query_file_stats_count(client, db, records, bucket):
    with patch_page_permission(True):
        _test_query_file_stats_count(client, db, records, bucket)


def _link_bucket(db, record, bucket):
    from invenio_records_files.models import RecordsBuckets
    RecordsBuckets.create(record=record.model, bucket=bucket)
    db.session.commit()


def _test_query_file_stats_count(client, db, records, bucket):
    _link_bucket(db, records[0][1], bucket)
    _uuid = bucket.id

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


# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_query_file_stats_count_permission -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_query_file_stats_count_permission(client, db, records, bucket):
    _link_bucket(db, records[0][1], bucket)
    # リクエストの後はフィクスチャのオブジェクトがセッションから外れるので先に控える
    record_id = records[0][1].id
    url = url_for('invenio_stats.get_file_stats_count',
                  bucket_id=bucket.id, file_key='test.pdf')
    headers = [('Content-Type', 'application/json'),
               ('Accept', 'application/json')]

    # the permission of the record detail page is checked
    with patch_page_permission(True) as mock_factory:
        res = client.get(url)
        assert res.status_code==200
        assert mock_factory.call_args[0][0].id == record_id

        res = client.post(url, headers=headers,
                          data=json.dumps({'date': 'total'}))
        assert res.status_code==200
        assert mock_factory.call_args[0][0].id == record_id

    # users who cannot view the record are rejected
    with patch_page_permission(False):
        res = client.get(url)
        assert res.status_code==403

        res = client.post(url, headers=headers,
                          data=json.dumps({'date': 'total'}))
        assert res.status_code==403


# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_query_file_stats_count_error -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_query_file_stats_count_error(client, db, records, bucket):
    headers = [('Content-Type', 'application/json'),
               ('Accept', 'application/json')]
    with patch_page_permission(True):
        # bucket without record
        url = url_for('invenio_stats.get_file_stats_count',
                      bucket_id=uuid.uuid4(), file_key='test.pdf')
        res = client.get(url)
        assert res.status_code==404
        res = client.post(url, headers=headers,
                          data=json.dumps({'date': 'total'}))
        assert res.status_code==404

        # invalid bucket id
        url = url_for('invenio_stats.get_file_stats_count',
                      bucket_id='test', file_key='test.pdf')
        res = client.get(url)
        assert res.status_code==400
        res = client.post(url, headers=headers,
                          data=json.dumps({'date': 'total'}))
        assert res.status_code==400

        # invalid request data
        _link_bucket(db, records[0][1], bucket)
        url = url_for('invenio_stats.get_file_stats_count',
                      bucket_id=bucket.id, file_key='test.pdf')
        res = client.post(url)
        assert res.status_code==400
        for _data in [{}, {'date': 'test'}, {'date': 202209}, []]:
            res = client.post(url, headers=headers,
                              data=json.dumps(_data))
            assert res.status_code==400


# class QueryItemRegReport(WekoQuery):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_query_item_reg_report -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 403),
        (1, 200),
        (2, 200),
        (3, 200),
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

    res = client.get(
        url_for('invenio_stats.get_item_registration_report',
                target_report='1', start_date='0', end_date='0', unit='Year', repo='comm1'))
    assert res.status_code==status_code

# class QueryRecordViewReport(WekoQuery):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_query_record_view_report -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 403),
        (1, 200),
        (2, 200),
        (3, 200),
        (4, 403)
    ],
)
def test_query_record_view_report(client, role_users, id, status_code):
    # get
    login_user_via_session(client=client, email=role_users[id]["email"])
    res = client.get(
        url_for('invenio_stats.get_record_view_report', year=2022, month=9))
    assert res.status_code==status_code

    res = client.get(
        url_for('invenio_stats.get_record_view_report', year=2022, month=9, repository_id='comm1'))
    assert res.status_code==status_code


# class QueryRecordViewPerIndexReport(WekoQuery):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_query_record_view_per_index_report -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 403),
        (1, 200),
        (2, 200),
        (3, 200),
        (4, 403)
    ],
)
def test_query_record_view_per_index_report(client, role_users, id, status_code):
    # get
    login_user_via_session(client=client, email=role_users[id]["email"])
    res = client.get(
        url_for('invenio_stats.get_record_view_per_index_report', year=2022, month=9))
    assert res.status_code==status_code

    res = client.get(
        url_for('invenio_stats.get_record_view_per_index_report', year=2022, month=9, repository_id='comm1'))
    assert res.status_code==status_code


# class QueryFileReports(WekoQuery):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_query_record_view_per_index_report -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 403),
        (1, 200),
        (2, 200),
        (3, 200),
        (4, 403)
    ],
)
def test_query_file_reports(client, role_users, id, status_code):
    # get
    login_user_via_session(client=client, email=role_users[id]["email"])
    res = client.get(
        url_for('invenio_stats.get_file_reports', event='file_download', year=2022, month=9))
    assert res.status_code==status_code

    res = client.get(
        url_for('invenio_stats.get_file_reports', event='file_download', year=2022, month=9, repository_id='comm1'))
    assert res.status_code==status_code


# class QueryCommonReports(WekoQuery):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_query_common_reports -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 403),
        (1, 200),
        (2, 200),
        (3, 200),
        (4, 403)
    ],
)
def test_query_common_reports(client, role_users, id, status_code):
    # The endpoint requires stats-api-access now.
    login_user_via_session(client=client, email=role_users[id]["email"])
    res = client.get(
        url_for('invenio_stats.get_common_report', event='top_page_access', year=2022, month=9))
    assert res.status_code==status_code

    res = client.get(
        url_for('invenio_stats.get_common_report', event='top_page_access', year=2022, month=9, repository_id='comm1'))
    assert res.status_code==status_code


# class QueryCeleryTaskReport(WekoQuery):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_query_celery_task_report -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 403),
        (1, 200),
        (2, 200),
        (3, 200),
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
        (3, 200),
        (4, 403)
    ],
)
def test_query_search_report(client, role_users, id, status_code):
    # get
    login_user_via_session(client=client, email=role_users[id]["email"])
    res = client.get(
        url_for('invenio_stats.get_search_report', year=2022, month=9))
    assert res.status_code==status_code

    res = client.get(
        url_for('invenio_stats.get_search_report', year=2022, month=9, repository_id='comm1'))
    assert res.status_code==status_code


# def dbsession_clean(exception):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_views.py::test_dbsession_clean -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_dbsession_clean(app):
    with patch("invenio_db.db.session.commit", side_effect=Exception):
        assert not dbsession_clean(None)
        assert not dbsession_clean('')
