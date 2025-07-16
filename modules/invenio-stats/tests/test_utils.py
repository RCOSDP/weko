# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test utility functions."""

import pytest
import uuid
import json

from invenio_stats.models import StatsEvents, StatsAggregation, StatsBookmark

from sqlalchemy.exc import UnsupportedCompilationError
from mock import patch, MagicMock
import datetime
from invenio_stats.errors import UnknownQueryError
from invenio_stats.utils import (
    get_anonymization_salt,
    get_geoip,
    get_user,
    obj_or_import_string,
    load_or_import_from_config,
    default_permission_factory,
    weko_permission_factory,
    get_aggregations,
    get_start_end_date,
    agg_bucket_sort,
    parse_bucket_response,
    get_doctype,
    is_valid_access,
    chunk_list,
    QueryFileReportsHelper,
    QuerySearchReportHelper,
    QueryCommonReportsHelper,
    QueryRecordViewPerIndexReportHelper,
    QueryRecordViewReportHelper,
    QueryItemRegReportHelper,
    QueryRankingHelper,
    StatsCliUtil,
    )

# def get_anonymization_salt(ts):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils.py::test_get_anonymization_salt -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_get_anonymization_salt(app):
    assert get_anonymization_salt(datetime.datetime(2022, 1, 1))

# def get_geoip(ip):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils.py::test_get_geoip -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_get_geoip():
    """Test looking up IP address."""
    assert get_geoip("74.125.67.100") == 'US'

# def get_user():
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils.py::test_get_user -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_get_user(app, mock_users, request_headers):
    """Test the get_user function."""
    header = request_headers['user']
    with patch(
                'invenio_stats.utils.current_user',
                mock_users['authenticated']
            ), app.test_request_context(
                headers=header, environ_base={'REMOTE_ADDR': '142.0.0.1'}
            ):
        user = get_user()
    assert user['user_id'] == mock_users['authenticated'].get_id()
    assert user['user_agent'] == header['USER_AGENT']
    assert user['ip_address'] == '142.0.0.1'

# def obj_or_import_string(value, default=None):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils.py::test_obj_or_import_string -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def myfunc():
    """Example function."""
    pass

def test_obj_or_import_string(app):
    """Test obj_or_import_string."""
    assert not obj_or_import_string(value=None)
    assert myfunc == obj_or_import_string(value=myfunc)

# def load_or_import_from_config(key, app=None, default=None):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils.py::test_load_or_import_from_config -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_load_or_import_from_config(app):
    assert load_or_import_from_config('STATS_PERMISSION_FACTORY', app)

# def default_permission_factory(query_name, params):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils.py::test_default_permission_factory -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_default_permission_factory(app):
    # need to fix
    with pytest.raises(Exception) as e:
        default_permission_factory('test', {})==None
    assert e.type==KeyError

    assert default_permission_factory('get-search-report', {}).can()==True

# def weko_permission_factory(*args, **kwargs):

# def get_aggregations(index, aggs_query):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils.py::test_get_aggregations -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_get_aggregations(app, es):
    res = get_aggregations('', {})
    assert res=={}

    res = get_aggregations('test-stats-search', {'aggs': {}})
    assert res=={'_shards': {'failed': 0, 'skipped': 0, 'successful': 5, 'total': 5}, 'hits': {'hits': [], 'max_score': None, 'total': 0}, 'timed_out': False, 'took': 0}

# def get_start_end_date(year, month):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils.py::test_get_start_end_date -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_get_start_end_date(app):
    start_date, end_date = get_start_end_date(2022, 10)
    assert start_date=='2022-10-01'
    assert end_date=='2022-10-31'

# def agg_bucket_sort(agg_sort, buckets):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils.py::test_agg_bucket_sort -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_agg_bucket_sort(app):
    _agg_sort = {'order': 'desc', 'key_name': 'name'}
    _buckets = [{'name': 10}, {'name': 3}, {'name': 9}]

    res = agg_bucket_sort(_agg_sort, _buckets)
    assert res==[{'name': 10}, {'name': 9}, {'name': 3}]

    res = agg_bucket_sort(None, _buckets)
    assert res==[{'name': 10}, {'name': 3}, {'name': 9}]


# def parse_bucket_response(raw_res, pretty_result=dict()):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils.py::test_parse_bucket_response -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_parse_bucket_response(app):
    _raw_res = {'buckets': [{'key': 'test_value'}], 'field': 'test_name'}

    res = parse_bucket_response(_raw_res, {})
    assert res=={'test_name': 'test_value'}

# def get_doctype(doc_type):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils.py::test_get_doctype -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_get_doctype(app):
    assert get_doctype('test_doc')=='test_doc'

# def is_valid_access():
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils.py::test_is_valid_access -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_is_valid_access(app):
    res = is_valid_access()
    assert res==True

    with patch("invenio_stats.utils.get_remote_addr", return_value='0.0.0.0'):
        app.config['STATS_EXCLUDED_ADDRS'] = ['0.0.0.0']
        res = is_valid_access()
        assert res==False

        app.config['STATS_EXCLUDED_ADDRS'] = ['0.0.0.1']
        res = is_valid_access()
        assert res==True

        app.config['STATS_EXCLUDED_ADDRS'] = ['0.0.0.0/0.0.0.1']
        res = is_valid_access()
        assert res==False

        app.config['STATS_EXCLUDED_ADDRS'] = ['2.0.0.2/30']
        res = is_valid_access()
        assert res==True

# def chunk_list(iterable, size):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils.py::test_chunk_list -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
@pytest.mark.parametrize("iterable, size, expected", [
    (range(5), 2, [[0, 1], [2, 3], [4]]),
    ([], 2, []),
    (range(5), 5, [[0, 1, 2, 3, 4]]),
    (range(5), 1, [[0], [1], [2], [3], [4]]),
])
def test_chunk_list(iterable, size, expected):
    result = list(chunk_list(iterable, size))
    assert result == expected

# class QueryFileReportsHelper(object):
#     def calc_per_group_counts(cls, group_names, current_stats, current_count):
#     def calc_file_stats_reports(cls, res, data_list, all_groups):
#     def calc_file_per_using_report(cls, res, data_list):
#     def Calculation(cls, res, data_list, all_groups=set()):
#     def get_file_stats_report(cls, is_billing_item=False, **kwargs):
#     def get_file_per_using_report(cls, **kwargs):
#     def get(cls, **kwargs):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils.py::test_query_file_reports_helper -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
@pytest.mark.parametrize('aggregated_file_download_events',
                         [dict(file_number=1,
                               event_number=1,
                               start_date=datetime.date(2022, 10, 3),
                               end_date=datetime.date(2022, 10, 3))],
                         indirect=['aggregated_file_download_events'])
def test_query_file_reports_helper(app, event_queues, aggregated_file_download_events):
    # calc_per_group_counts
    res = QueryFileReportsHelper.calc_per_group_counts('test1, test1, test2', {}, 1)
    assert res=={'test1': 2, 'test2': 1}

    # Calculation
    _res = {
        'buckets': [
            {
                'file_key': 'test1.pdf',
                'index_list': 'index1',
                'count': 1,
                'site_license_flag': 1,
                'userrole': 'guest',
                'user_group_names': 'test1, test2'
            },
            {
                'file_key': 'test2.pdf',
                'index_list': 'index2',
                'count': 2,
                'site_license_flag': 0,
                'userrole': 'Contributor',
                'user_group_names': 'test2, test3'
            },
            {
                'file_key': 'test3.pdf',
                'index_list': 'index3',
                'count': 3,
                'site_license_flag': 0,
                'userrole': 'System Administrator',
                'user_group_names': 'test3'
            },
            {
                'file_key': 'test3.pdf',
                'index_list': 'index3',
                'count': 4,
                'site_license_flag': 0,
                'userrole': ''
            }
        ]
    }
    _data_list = []
    _all_group = set()
    QueryFileReportsHelper.Calculation(_res, _data_list, _all_group)
    assert _data_list==[
        {'group_counts': {'test1': 1, 'test2': 1}, 'file_key': 'test1.pdf', 'index_list': 'index1', 'total': 1, 'admin': 0, 'reg': 0, 'login': 0, 'no_login': 1, 'site_license': 1},
        {'group_counts': {'test2': 2, 'test3': 2}, 'file_key': 'test2.pdf', 'index_list': 'index2', 'total': 2, 'admin': 0, 'reg': 2, 'login': 2, 'no_login': 0, 'site_license': 0},
        {'group_counts': {'test3': 3}, 'file_key': 'test3.pdf', 'index_list': 'index3', 'total': 7, 'admin': 3, 'reg': 0, 'login': 7, 'no_login': 0, 'site_license': 0}]
    assert _all_group=={'test3', 'test1', 'test2'}

    _res = {
        'get-file-download-per-user-report': {
            'buckets': [
                {
                    'cur_user_id': 1,
                    'count': 2
                },
                {
                    'cur_user_id': 2,
                    'count': 3
                },
                {
                    'cur_user_id': 3,
                    'count': 4
                }
            ]
        },
        'get-file-preview-per-user-report': {
            'buckets': [
                {
                    'cur_user_id': 1,
                    'count': 5
                },
                {
                    'cur_user_id': 4,
                    'count': 1
                }
            ]
        }
    }
    _data_list = {}
    QueryFileReportsHelper.Calculation({
        'get-file-download-per-user-report': None,
        'get-file-preview-per-user-report': None},
        _data_list)
    assert _data_list=={}
    QueryFileReportsHelper.Calculation(_res, _data_list)
    assert _data_list=={
        1: {'cur_user_id': 1, 'total_download': 2, 'total_preview': 5},
        2: {'cur_user_id': 2, 'total_download': 3},
        3: {'cur_user_id': 3, 'total_download': 4},
        4: {'cur_user_id': 4, 'total_preview': 1}}


    # get_file_stats_report
    res = QueryFileReportsHelper.get_file_stats_report(event='file_downlaod', year=2022, month=10)
    assert res=={'all': [], 'all_groups': [], 'date': '2022-10', 'open_access': []}
    res = QueryFileReportsHelper.get_file_stats_report(event='file_preview', year=2022, month=10)
    assert res=={'all': [], 'all_groups': [], 'date': '2022-10', 'open_access': []}
    res = QueryFileReportsHelper.get_file_stats_report(event='billing_file_download', year=2022, month=10)
    assert res=={'all': [], 'all_groups': [], 'date': '2022-10', 'open_access': []}

    res = QueryFileReportsHelper.get_file_stats_report(event='file_downlaod', year=2022, month=10, repository_id='com1')
    assert res=={'all': [], 'all_groups': [], 'date': '2022-10', 'open_access': []}
    res = QueryFileReportsHelper.get_file_stats_report(event='file_downlaod', year=2022, month=10, repository_id='Root Index')
    assert res=={'all': [], 'all_groups': [], 'date': '2022-10', 'open_access': []}

    # get_file_per_using_report
    res = QueryFileReportsHelper.get_file_per_using_report(year=2022, month=10)
    assert res=={'all': {}, 'date': '2022-10'}

    # get
    res = QueryFileReportsHelper.get(year=2022, month=10, event='file_download')
    assert res=={'all': [], 'all_groups': [], 'date': '2022-10', 'open_access': []}
    res = QueryFileReportsHelper.get(year=2022, month=10, event='billing_file_download')
    assert res=={'all': [], 'all_groups': [], 'date': '2022-10', 'open_access': []}
    res = QueryFileReportsHelper.get(year=2022, month=10, event='file_using_per_user')
    assert res=={'all': {}, 'date': '2022-10'}
    res = QueryFileReportsHelper.get(year=2022, month=10, event='test')
    assert res==[]

@patch("weko_index_tree.utils.get_descendant_index_names")
@patch("invenio_communities.models.Community")
def test_query_file_reports_helper_error(mock_Community, mock_get_descendant_index_names, app, mocker):
    # get
    res = QueryFileReportsHelper.get(year=2022, month=10, event='file_download')
    assert res=={'all': [], 'all_groups': [], 'date': '2022-10', 'open_access': []}
    res = QueryFileReportsHelper.get(year=2022, month=10, event='billing_file_download')
    assert res=={'all': [], 'all_groups': [], 'date': '2022-10', 'open_access': []}
    res = QueryFileReportsHelper.get(year=2022, month=10, event='file_using_per_user')
    assert res=={'all': {}, 'date': '2022-10'}
    res = QueryFileReportsHelper.get(year=2022, month=10, event='test')
    assert res==[]

    mock_Community.query.get.return_value = MagicMock(root_node_id=1, group_id=1)
    mock_get_descendant_index_names.return_value = []
    res = QueryFileReportsHelper.get(event='file_download', year=2022, month=10, repository_id='com1')
    assert res=={'all': [], 'all_groups': [], 'date': '2022-10', 'open_access': []}
    res = QueryFileReportsHelper.get(event='file_download', year=2022, month=10, repository_id='Root Index')
    assert res=={'all': [], 'all_groups': [], 'date': '2022-10', 'open_access': []}
    res = QueryFileReportsHelper.get(event='file_using_per_user', year=2022, month=10, repository_id='com1')
    assert res=={'all': {}, 'date': '2022-10'}
    res = QueryFileReportsHelper.get(event='file_using_per_user', year=2022, month=10, repository_id='Root Index')
    assert res=={'all': {}, 'date': '2022-10'}

# class QuerySearchReportHelper(object):
#     def parse_bucket_response(cls, raw_res, pretty_result):
#     def get(cls, **kwargs):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils.py::test_query_search_report_helper -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_query_search_report_helper(app, es):
    # parse_bucket_response
    _raw_res1 = {
        'field': 'name1',
        'buckets': [
            {
                'key': 3,
                'field': 'name2',
                'buckets': [
                    {
                        'key': 2
                    }
                ]
            }
        ]
    }
    _raw_res2 = {
        'field': 'name1',
        'buckets': [
            {
                'key': 3,
                'search_key': 'key1',
                'count': 4,
                'field': 'name2',
                'buckets': [
                    {
                        'key': 2
                    }
                ]
            },
            {
                'key': 8,
                'search_key': 'key2',
                'count': 7,
                'field': 'name3',
                'buckets': [
                    {
                        'key': 9
                    }
                ]
            }
        ]
    }
    res = QuerySearchReportHelper.parse_bucket_response(_raw_res1, {})
    assert res=={'name1': 3, 'name2': 2}

    # get
    with patch('invenio_stats.queries.ESWekoTermsQuery.run', return_value=_raw_res1):
        res = QuerySearchReportHelper.get(
            year=2022, month=10, start_date='2022-10-01', end_date='2022-10-31')
        assert res=={'all': []}

    with patch('invenio_stats.queries.ESWekoTermsQuery.run', return_value=_raw_res2):
        res = QuerySearchReportHelper.get(
            year=2022, month=10, start_date='2022-10-01', end_date='2022-10-31')
        assert res=={'all': [{'search_key': 'key2', 'count': 7}, {'search_key': 'key1', 'count': 4}]}

    with patch('invenio_stats.queries.ESWekoTermsQuery.run', return_value=_raw_res2):
        res = QuerySearchReportHelper.get(
            year=2022, month=10, start_date='2022-10-01', end_date='2022-10-31', repository_id='com1')
        assert res=={'all': [{'search_key': 'key2', 'count': 7}, {'search_key': 'key1', 'count': 4}]}

    with patch('invenio_stats.queries.ESWekoTermsQuery.run', return_value=_raw_res2):
        res = QuerySearchReportHelper.get(
            year=2022, month=10, start_date='2022-10-01', end_date='2022-10-31', repository_id='Root Index')
        assert res=={'all': [{'search_key': 'key2', 'count': 7}, {'search_key': 'key1', 'count': 4}]}

def test_query_search_report_helper_error(app):
    res = QuerySearchReportHelper.get(
        year=2022, month=10, start_date=None, end_date=None)
    assert res=={'all': [], 'date': '2022-10'}


# class QueryCommonReportsHelper(object):
#     def get_common_params(cls, **kwargs):
#     def get(cls, **kwargs):
#     def get_top_page_access_report(cls, **kwargs):
#         def Calculation(res, data_list):
#     def get_site_access_report(cls, **kwargs):
#         def Calculation(query_list, res, site_license_list, other_list,
#     def get_item_create_ranking(cls, **kwargs):
#         def Calculation(res, result):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils.py::test_query_common_reports_helper -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
@patch("weko_index_tree.utils.get_descendant_index_names")
@patch("invenio_communities.models.Community")
def test_query_common_reports_helper(mock_Community, mock_get_descendant_index_names, app, es):
    # get
    _res = {
        'buckets': [
            {
                'hostname': 'name1',
                'remote_addr': 'localhost',
                'count': 3
            },
            {
                'hostname': 'name2',
                'remote_addr': 'localhost',
                'count': 2
            }
        ]
    }
    with patch('invenio_stats.queries.ESTermsQuery.run', return_value=_res):
        res = QueryCommonReportsHelper.get(event='top_page_access', year=2022, month=10, start_date='2022-10-01', end_date='2022-10-10')
        assert res=={'date': '2022-10-01-2022-10-10', 'all': {'localhost': {'host': 'name2', 'ip': 'localhost', 'count': 2}}}

        mock_Community.query.get.return_value = MagicMock(root_node_id=1)
        mock_get_descendant_index_names.return_value = ['index1']
        res = QueryCommonReportsHelper.get(event='top_page_access', year=2022, month=10, start_date='2022-10-01', end_date='2022-10-10', repository_id='com1')
        assert res=={'date': '2022-10-01-2022-10-10', 'all': {'localhost': {'host': 'name2', 'ip': 'localhost', 'count': 2}}}

    _res = {
        "interval": "year",
        "key_type": "date",
        "start_date": None,
        "end_date": None,
        "buckets": [
            {
                "key": 1704034800000,
                "date": "2024-01-01T00:00:00.000+09:00",
                "value": 56.0
            }
        ]
    }
    with patch('invenio_stats.queries.ESDateHistogramQuery.run', return_value=_res):
        res = QueryCommonReportsHelper.get(event='top_page_access', year=2022, month=-1)
        assert res=={'date': 'all', 'all': {'2024-01-01T00:00:00.000+09:00':{'count':56.0}}}

    _res = {
        'buckets': [
            {
                'site_license_name': '',
                'count': 1
            },
            {
                'site_license_name': 'name1',
                'count': 2
            }
        ]
    }
    with patch('invenio_stats.queries.ESTermsQuery.run', return_value=_res):
        res = QueryCommonReportsHelper.get(event='site_access', year=2022, month=10)
        assert res=={'date': '2022-10', 'site_license': [{'top_view': 2, 'search': 2, 'record_view': 2, 'file_download': 2, 'file_preview': 2}], 'other': [{'top_view': 1, 'search': 1, 'record_view': 1, 'file_download': 1, 'file_preview': 1}], 'institution_name': [{'name': 'name1', 'top_view': 2, 'search': 2, 'record_view': 2, 'file_download': 2, 'file_preview': 2}]}

    _res = {
        'buckets': [
            {
                'key': 1640995200,
                'buckets': [
                    {
                        'key': 'key1.1',
                    },
                    {
                        'key': 'key1.2',
                        'buckets': [
                            {
                                'key': 'key1.2.1'
                            }
                        ]
                    }
                ]
            }
        ]
    }
    with patch('invenio_stats.queries.ESWekoTermsQuery.run', return_value=_res):
        res = QueryCommonReportsHelper.get(event='item_create', year=2022, month=-1)
        assert res=={'date': 'all', 'all': [{'create_date': 1640995.2, 'pid_value': 'key1.1', 'record_name': ''}, {'create_date': 1640995.2, 'pid_value': 'key1.2', 'record_name': 'key1.2.1'}]}

    res = QueryCommonReportsHelper.get(event='')
    assert res==[]

def test_query_common_reports_helper_error(app):
    # get
    res = QueryCommonReportsHelper.get(event='top_page_access')
    assert res=={'all': {}, 'date': ''}
    res = QueryCommonReportsHelper.get(event='site_access')
    assert res=={'date': '', 'institution_name': [], 'other': [{}], 'site_license': [{}]}
    res = QueryCommonReportsHelper.get(event='item_create')
    assert res=={'all': [], 'date': ''}
    res = QueryCommonReportsHelper.get(event='')
    assert res==[]


# class QueryRecordViewPerIndexReportHelper(object):
#     def build_query(cls, start_date, end_date, after_key=None):
#     def parse_bucket_response(cls, aggs, result):
#     def get(cls, **kwargs):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils.py::test_query_record_view_per_index_report_helper -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
@patch("weko_index_tree.utils.get_descendant_index_names")
@patch("invenio_communities.models.Community")
def test_query_record_view_per_index_report_helper(mock_Community, mock_get_descendant_index_names, app, es):
    mock_Community.query.get.return_value = MagicMock(root_node_id=1)
    mock_get_descendant_index_names.return_value = ['index1']

    # build_query
    res = QueryRecordViewPerIndexReportHelper.build_query(None, None, 'test_key')
    assert res.to_dict()=={'aggs': {'record_index_list': {'nested': {'path': 'record_index_list'}, 'aggs': {'my_buckets': {'composite': {'size': 6000, 'sources': [{'record_index_list.index_id': {'terms': {'field': 'record_index_list.index_id'}}}, {'record_index_list.index_name': {'terms': {'field': 'record_index_list.index_name'}}}], 'after': 'test_key'}}}}}, 'from': 0, 'size': 0}
    res = QueryRecordViewPerIndexReportHelper.build_query(None, None, index_list=['index1'])
    assert res.to_dict()=={'query': {'bool': {'filter': [{'nested': {'path': 'record_index_list', 'query': {'terms': {'record_index_list.index_name': ['index1']}}}}]}}, 'from': 0, 'size': 0, 'aggs': {'record_index_list': {'nested': {'path': 'record_index_list'}, 'aggs': {'my_buckets': {'composite': {'size': 6000, 'sources': [{'record_index_list.index_id': {'terms': {'field': 'record_index_list.index_id'}}}, {'record_index_list.index_name': {'terms': {'field': 'record_index_list.index_name'}}}]}}}}}}

    # parse_bucket_response
    _aggs = {
        'my_buckets': {
            'buckets': [
                {
                    'key': {
                        'record_index_list.index_name': 'name1'
                    },
                    'doc_count': 2
                },
                {
                    'key': {
                        'record_index_list.index_name': 'name2'
                    },
                    'doc_count': 3
                }
                ,
                {
                    'key': {
                        'record_index_list.index_name': 'name1'
                    },
                    'doc_count': 4
                }
            ]
        }
    }
    _result = {'all': []}
    res = QueryRecordViewPerIndexReportHelper.parse_bucket_response(_aggs, _result)
    assert res==9
    assert _result=={'all': [{'index_name': 'name1', 'view_count': 2}, {'index_name': 'name2', 'view_count': 3}, {'index_name': 'name1', 'view_count': 4}]}

    # get
    res = QueryRecordViewPerIndexReportHelper.get(year=2022, month=10)
    assert res=={'all': [], 'date': '2022-10', 'total': 0}
    res = QueryRecordViewPerIndexReportHelper.get(year=2022, month=10, repository_id='com1')
    assert res=={'all': [], 'date': '2022-10', 'total': 0}

def test_query_record_view_per_index_report_helper_error(app):
    # get
    res = QueryRecordViewPerIndexReportHelper.get(year=2022, month=10)
    assert res=={}


# class QueryRecordViewReportHelper(object):
#     def Calculation(cls, res, data_list):
#     def get_title(cls, lst_id):
#     def correct_record_title(cls, lst_data):
#     def get(cls, **kwargs):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils.py::test_query_record_view_report_helper -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
@patch("weko_index_tree.utils.get_descendant_index_names")
@patch("invenio_communities.models.Community")
def test_query_record_view_report_helper(mock_Community, mock_get_descendant_index_names, app, es, db, records):
    mock_Community.query.get.return_value = MagicMock(root_node_id=1)
    mock_get_descendant_index_names.return_value = ['index1']
    _id1 = str(uuid.uuid4())
    _id2 = str(uuid.uuid4())
    # Calculation
    _res = {
        'buckets': [
            {
                'record_id': _id1,
                'record_name': 'test name1',
                'record_index_names': 'test index1',
                'count': 2,
                'pid_value': 1,
                'cur_user_id': 1
            },
            {
                'record_id': _id2,
                'record_name': 'test name2',
                'record_index_names': 'test index1',
                'count': 1,
                'pid_value': 2,
                'cur_user_id': 1
            }
        ]
    }
    _data_list = []
    # Calculation
    with pytest.raises(Exception) as e:
        QueryRecordViewReportHelper.Calculation(_res, _data_list)
    assert e.type==UnsupportedCompilationError

    # correct_record_title
    _res = [['2', ['name2old']]]
    lst_data = [
        {
            'record_id': '1',
            'total_all': 5,
            'total_not_login': 2,
            'record_name': 'name1'
        },
        {
            'record_id': '1',
            'total_all': 3,
            'total_not_login': 1,
            'record_name': 'name1'
        },
        {
            'record_id': '2',
            'total_all': 7,
            'total_not_login': 3,
            'record_name': 'name2'
        },
        {
            'record_id': '2',
            'total_all': 7,
            'total_not_login': 3,
            'record_name': 'name2new'
        }
    ]
    with patch('invenio_stats.utils.QueryRecordViewReportHelper.get_title', return_value=_res):
        QueryRecordViewReportHelper.correct_record_title(lst_data)
        assert lst_data==[{'record_id': '2', 'total_all': 14, 'total_not_login': 6, 'record_name': 'name2old', 'same_title': False}, {'record_id': '1', 'total_all': 8, 'total_not_login': 3, 'record_name': 'name1', 'same_title': True}]

    # get
    res = QueryRecordViewReportHelper.get(year=2022, month=9)
    assert res=={'all': [], 'date': '2022-09-01-2022-09-30'}
    res = QueryRecordViewReportHelper.get(year=2022, month=9, repository_id='com1')
    assert res=={'all': [], 'date': '2022-09-01-2022-09-30'}


# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils.py::test_query_record_view_report_helper_error -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_query_record_view_report_helper_error(app, db):
    # get
    res = QueryRecordViewReportHelper.get(start_date='2022-09-01', end_date='2022-09-30', ranking=True)
    assert res=={'all': [], 'date': ''}

    res = QueryRecordViewReportHelper.get()
    assert res=={'all': [], 'date': 'None-None'}

# class QueryItemRegReportHelper(object):
#     def get(cls, **kwargs):
#     def merge_items_results(cls, results):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils.py::test_query_item_reg_report_helper -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
@patch("weko_index_tree.utils.get_item_ids_in_index")
@patch("weko_index_tree.utils.get_descendant_index_names")
@patch("invenio_communities.models.Community")
def test_query_item_reg_report_helper(mock_Community, mock_get_descendant_index_names, mock_get_item_ids_in_index, app, db, event_queues,es):
    mock_Community.query.get.return_value = MagicMock(root_node_id=1)
    mock_get_descendant_index_names.return_value = ['test_index-/-index1']
    mock_get_item_ids_in_index.return_value = ['item1', 'item2']
    # get
    from invenio_search import current_search_client
    res = QueryItemRegReportHelper.get(target_report='1', unit='Day', start_date='2022-09-01', end_date='2022-09-15')
    assert res=={'num_page': 2, 'page': 1, 'data': [{'count': 0.0, 'start_date': '2022-09-01 00:00:00', 'end_date': '2022-09-01 23:59:59', 'is_restricted': False}, {'count': 0.0, 'start_date': '2022-09-02 00:00:00', 'end_date': '2022-09-02 23:59:59', 'is_restricted': False}, {'count': 0.0, 'start_date': '2022-09-03 00:00:00', 'end_date': '2022-09-03 23:59:59', 'is_restricted': False}, {'count': 0.0, 'start_date': '2022-09-04 00:00:00', 'end_date': '2022-09-04 23:59:59', 'is_restricted': False}, {'count': 0.0, 'start_date': '2022-09-05 00:00:00', 'end_date': '2022-09-05 23:59:59', 'is_restricted': False}, {'count': 0.0, 'start_date': '2022-09-06 00:00:00', 'end_date': '2022-09-06 23:59:59', 'is_restricted': False}, {'count': 0.0, 'start_date': '2022-09-07 00:00:00', 'end_date': '2022-09-07 23:59:59', 'is_restricted': False}, {'count': 0.0, 'start_date': '2022-09-08 00:00:00', 'end_date': '2022-09-08 23:59:59', 'is_restricted': False}, {'count': 0.0, 'start_date': '2022-09-09 00:00:00', 'end_date': '2022-09-09 23:59:59', 'is_restricted': False}, {'count': 0.0, 'start_date': '2022-09-10 00:00:00', 'end_date': '2022-09-10 23:59:59', 'is_restricted': False}]}
    res = QueryItemRegReportHelper.get(target_report='1', unit='Day', start_date='2022-09-01', end_date='2022-09-15', repository_id='com1')
    assert res=={'num_page': 2, 'page': 1, 'data': [{'count': 0.0, 'start_date': '2022-09-01 00:00:00', 'end_date': '2022-09-01 23:59:59', 'is_restricted': False}, {'count': 0.0, 'start_date': '2022-09-02 00:00:00', 'end_date': '2022-09-02 23:59:59', 'is_restricted': False}, {'count': 0.0, 'start_date': '2022-09-03 00:00:00', 'end_date': '2022-09-03 23:59:59', 'is_restricted': False}, {'count': 0.0, 'start_date': '2022-09-04 00:00:00', 'end_date': '2022-09-04 23:59:59', 'is_restricted': False}, {'count': 0.0, 'start_date': '2022-09-05 00:00:00', 'end_date': '2022-09-05 23:59:59', 'is_restricted': False}, {'count': 0.0, 'start_date': '2022-09-06 00:00:00', 'end_date': '2022-09-06 23:59:59', 'is_restricted': False}, {'count': 0.0, 'start_date': '2022-09-07 00:00:00', 'end_date': '2022-09-07 23:59:59', 'is_restricted': False}, {'count': 0.0, 'start_date': '2022-09-08 00:00:00', 'end_date': '2022-09-08 23:59:59', 'is_restricted': False}, {'count': 0.0, 'start_date': '2022-09-09 00:00:00', 'end_date': '2022-09-09 23:59:59', 'is_restricted': False}, {'count': 0.0, 'start_date': '2022-09-10 00:00:00', 'end_date': '2022-09-10 23:59:59', 'is_restricted': False}]}

    _res = {
        'buckets': [
            {
                'date': '2022-10-01T00:00:00',
                'value': 1
            },
            {
                'date': '2022-10-01T01:00:00',
                'value': 0
            },
        ]
    }
    with patch('invenio_stats.queries.ESDateHistogramQuery.run', return_value=_res):
        res = QueryItemRegReportHelper.get(target_report='1', unit='Day', start_date='0', end_date='0')
        assert res=={'num_page': 1, 'page': 1, 'data': [{'count': 1, 'start_date': '2022-10-01', 'end_date': '2022-10-01'}]}
        res = QueryItemRegReportHelper.get(target_report='1', unit='Day', start_date='0', end_date='0', repository_id='com1')
        assert res=={'num_page': 1, 'page': 1, 'data': [{'count': 1, 'start_date': '2022-10-01', 'end_date': '2022-10-01'}]}


    res = QueryItemRegReportHelper.get(target_report='1', unit='Week', start_date='2022-09-01', end_date='2022-09-15')
    assert res=={'num_page': 1, 'page': 1, 'data': [{'start_date': '2022-09-01 00:00:00', 'end_date': '2022-09-07 23:59:59', 'is_restricted': False, 'count': 0.0}, {'start_date': '2022-09-08 00:00:00', 'end_date': '2022-09-14 23:59:59', 'is_restricted': False, 'count': 0.0}, {'start_date': '2022-09-15 00:00:00', 'end_date': '2022-09-15 23:59:59', 'is_restricted': False, 'count': 0.0}]}
    res = QueryItemRegReportHelper.get(target_report='1', unit='Week', start_date='2022-09-01', end_date='2022-09-15', repository_id='com1')
    assert res=={'num_page': 1, 'page': 1, 'data': [{'start_date': '2022-09-01 00:00:00', 'end_date': '2022-09-07 23:59:59', 'is_restricted': False, 'count': 0.0}, {'start_date': '2022-09-08 00:00:00', 'end_date': '2022-09-14 23:59:59', 'is_restricted': False, 'count': 0.0}, {'start_date': '2022-09-15 00:00:00', 'end_date': '2022-09-15 23:59:59', 'is_restricted': False, 'count': 0.0}]}

    _res = {
        'buckets': [
            {
                'date': '2022-10-01T00:00:00',
                'value': 1
            },
            {
                'date': '2022-10-01T01:00:00',
                'value': 0
            },
        ]
    }
    with patch('invenio_stats.queries.ESDateHistogramQuery.run', return_value=_res):
        res = QueryItemRegReportHelper.get(target_report='1', unit='Week', start_date='0', end_date='0')
        assert res=={'num_page': 1, 'page': 1, 'data': [{'count': 1, 'start_date': '2022-10-01', 'end_date': '2022-10-07', 'is_restricted': False}]}
        res = QueryItemRegReportHelper.get(target_report='1', unit='Week', start_date='0', end_date='0', repository_id='com1')
        assert res=={'num_page': 1, 'page': 1, 'data': [{'count': 1, 'start_date': '2022-10-01', 'end_date': '2022-10-07', 'is_restricted': False}]}

    res = QueryItemRegReportHelper.get(target_report='1', unit='User', start_date='2022-09-01', end_date='2022-10-15')
    assert res=={'data': [], 'num_page': 0, 'page': 1}
    res = QueryItemRegReportHelper.get(target_report='1', unit='User', start_date='2022-09-01', end_date='2022-10-15', repository_id='com1')
    assert res=={'data': [], 'num_page': 0, 'page': 1}

    _res = {
        'buckets': [
            {
                'buckets': [
                    {
                        'buckets': [
                            {
                                'key': '1',
                                'count': 2
                            },
                            {
                                'key': '1',
                                'count': 3
                            },
                            {
                                'key': '2',
                                'count': 4
                            }
                        ]
                    }
                ]
            }
        ]
    }
    with patch('invenio_stats.queries.ESDateHistogramQuery.run', return_value=_res):
        res = QueryItemRegReportHelper.get(target_report='1', unit='User', start_date='0', end_date='0')
        assert res=={'num_page': 0, 'page': 1, 'data': [{'user_id': '1', 'count': 5}, {'user_id': '2', 'count': 4}]}
        res = QueryItemRegReportHelper.get(target_report='1', unit='User', start_date='0', end_date='0', repository_id='com1')
        assert res=={'num_page': 0, 'page': 1, 'data': [{'user_id': '1', 'count': 5}, {'user_id': '2', 'count': 4}]}

    res = QueryItemRegReportHelper.get(target_report='1', unit='Year', start_date='2022-09-01', end_date='2022-09-15')
    assert res=={'num_page': 1, 'page': 1, 'data': [{'count': 0.0, 'start_date': '2022-01-01 00:00:00', 'end_date': '2022-12-31 23:59:59', 'year': 2022, 'is_restricted': False}]}
    res = QueryItemRegReportHelper.get(target_report='1', unit='Year', start_date='2022-09-01', end_date='2022-09-15', repository_id='com1')
    assert res=={'num_page': 1, 'page': 1, 'data': [{'count': 0.0, 'start_date': '2022-01-01 00:00:00', 'end_date': '2022-12-31 23:59:59', 'year': 2022, 'is_restricted': False}]}

    _res = {
        'buckets': [
            {
                'date': '2022-10-01T00:00:00',
                'value': 1
            },
            {
                'date': '2022-10-01T01:00:00',
                'value': 0
            },
        ]
    }
    with patch('invenio_stats.queries.ESDateHistogramQuery.run', return_value=_res):
        res = QueryItemRegReportHelper.get(target_report='1', unit='Year', start_date='0', end_date='0')
        assert res=={'num_page': 1, 'page': 1, 'data': [{'count': 1, 'start_date': '2022-01-01', 'end_date': '2022-12-31', 'year': 2022, 'is_restricted': False}]}
        res = QueryItemRegReportHelper.get(target_report='1', unit='Year', start_date='0', end_date='0', repository_id='com1')
        assert res=={'num_page': 1, 'page': 1, 'data': [{'count': 1, 'start_date': '2022-01-01', 'end_date': '2022-12-31', 'year': 2022, 'is_restricted': False}]}

    current_search_client.create(
        index="test-stats-record-view",
        doc_type="record-view-day-aggregation",
        id=1,
        body={
          "timestamp" : "2022-09-15T01:00:00",
          "unique_id" : "68a04d6c-fc25-39de-a9d6-31a24a46892c",
          "count" : 14,
          "unique_count" : 1,
          "country" : None,
          "hostname" : "None",
          "remote_addr" : "192.168.56.1",
          "record_id" : "1599b017-ac02-4155-a6c5-f8565e31f998",
          "record_name" : "test_record1",
          "record_index_names" : "test_index-/-index1",
          "pid_type" : "recid",
          "pid_value" : "5",
          "cur_user_id" : "guest",
          "site_license_name" : "",
          "site_license_flag" : False
        }
    )
    current_search_client.indices.refresh()
    res = QueryItemRegReportHelper.get(target_report='2', unit='Day', start_date='0', end_date='0')
    assert res=={'data': [{"count":14.0, "end_date":"2022-09-15","start_date":"2022-09-15"}], 'num_page': 1, 'page': 1}
    res = QueryItemRegReportHelper.get(target_report='2', unit='Day', start_date='0', end_date='0', repository_id='com1')
    assert res=={'data': [{"count":14.0, "end_date":"2022-09-15","start_date":"2022-09-15"}], 'num_page': 1, 'page': 1}
    res = QueryItemRegReportHelper.get(target_report='2', unit='Item', start_date='2022-09-01', end_date='2022-09-15')
    assert res=={'data': [{"col1":"5","col2":"test_record1","col3":14.0}], 'num_page': 1, 'page': 1}
    res = QueryItemRegReportHelper.get(target_report='2', unit='Item', start_date='2022-09-01', end_date='2022-09-15', repository_id='com1')
    assert res=={'data': [{"col1":"5","col2":"test_record1","col3":14.0}], 'num_page': 1, 'page': 1}
    res = QueryItemRegReportHelper.get(target_report='2', unit='Host', start_date='2022-09-01', end_date='2022-09-15')
    assert res=={'data': [{"count":14.0,"domain":"","end_date":"2022-09-15 23:59:59","ip":"192.168.56.1","start_date":"2022-09-01 00:00:00"}], 'num_page': 1, 'page': 1}
    res = QueryItemRegReportHelper.get(target_report='2', unit='Host', start_date='2022-09-01', end_date='2022-09-15', repository_id='com1')
    assert res=={'data': [{"count":14.0,"domain":"","end_date":"2022-09-15 23:59:59","ip":"192.168.56.1","start_date":"2022-09-01 00:00:00"}], 'num_page': 1, 'page': 1}
    res = QueryItemRegReportHelper.get(target_report='3', unit='Day', start_date='0', end_date='0')
    assert res=={'data': [], 'num_page': 0, 'page': 1}
    res = QueryItemRegReportHelper.get(target_report='3', unit='Day', start_date='0', end_date='0', repository_id='com1')
    assert res=={'data': [], 'num_page': 0, 'page': 1}

    _res = {
        'buckets': [
            {
                'key': '1',
                'buckets': [
                    {
                        'key': 'name1',
                        'count': 1
                    }
                ]
            }
        ]
    }
    with patch('invenio_stats.queries.ESTermsQuery.run', return_value=_res):
        res = QueryItemRegReportHelper.get(target_report='3', unit='Item', start_date='0', end_date='0', ranking=True)
        assert res=={'num_page': 1, 'page': 1, 'data': [{'col1': '1', 'col2': 'name1', 'col3': 1}]}
        res = QueryItemRegReportHelper.get(target_report='3', unit='Item', start_date='0', end_date='0', ranking=True, repository_id='com1')
        assert res=={'num_page': 1, 'page': 1, 'data': [{'col1': '1', 'col2': 'name1', 'col3': 1}]}

    _res = {
        'buckets': [
            {
                'key': 'localhost',
                'buckets': [
                    {
                        'key': 'mayPC',
                        'count': 1
                    }
                ]
            }
        ]
    }
    with patch('invenio_stats.queries.ESTermsQuery.run', return_value=_res):
        res = QueryItemRegReportHelper.get(target_report='3', unit='Host', start_date='0', end_date='0')
        assert res=={'num_page': 1, 'page': 1, 'data': [{'count': 1, 'start_date': '', 'end_date': '', 'domain': 'mayPC', 'ip': 'localhost'}]}
        res = QueryItemRegReportHelper.get(target_report='3', unit='Host', start_date='0', end_date='0', repository_id='com1')
        assert res=={'num_page': 1, 'page': 1, 'data': [{'count': 1, 'start_date': '', 'end_date': '', 'domain': 'mayPC', 'ip': 'localhost'}]}

    res = QueryItemRegReportHelper.get(target_report='3', unit='Test', start_date='0', end_date='0')
    assert res=={'data': [], 'num_page': 0, 'page': 1}

    # merge_items_results
    _results = [
        {
            'col1': 1.0,
            'col3': 2
        },
        {
            'col1': 1.0,
            'col3': 3
        },
        {
            'col1': 2.0,
            'col3': 4
        }
    ]
    res = QueryItemRegReportHelper.merge_items_results(_results)
    assert res==[{'col1': 1.0, 'col3': 5}, {'col1': 2.0, 'col3': 4}]

def test_query_item_reg_report_helper_error(app, db):
    # get
    res = QueryItemRegReportHelper.get(target_report='1', unit='Day', start_date='2022-09-01', end_date='2022-09-15')
    assert res=={'data': [], 'num_page': 2, 'page': 1}
    res = QueryItemRegReportHelper.get(target_report='1', unit='Day', start_date='0', end_date='0')
    assert res=={'data': [], 'num_page': 0, 'page': 1}
    res = QueryItemRegReportHelper.get(target_report='1', unit='Week', start_date='2022-09-01', end_date='2022-09-15')
    assert res=={'data': [], 'num_page': 1, 'page': 1}
    res = QueryItemRegReportHelper.get(target_report='1', unit='Week', start_date='0', end_date='0')
    assert res=={'data': [], 'num_page': 0, 'page': 1}
    res = QueryItemRegReportHelper.get(target_report='1', unit='User', start_date='2022-09-01', end_date='2022-10-15')
    assert res=={'data': [], 'num_page': 0, 'page': 1}
    res = QueryItemRegReportHelper.get(target_report='1', unit='Year', start_date='2022-09-01', end_date='2022-09-15')
    assert res=={'data': [], 'num_page': 1, 'page': 1}
    res = QueryItemRegReportHelper.get(target_report='1', unit='Year', start_date='0', end_date='0')
    assert res=={'data': [], 'num_page': 0, 'page': 1}
    res = QueryItemRegReportHelper.get(target_report='2', unit='Day', start_date='0', end_date='0')
    assert res=={'data': [], 'num_page': 0, 'page': 1}
    res = QueryItemRegReportHelper.get(target_report='2', unit='Item', start_date='2022-09-01', end_date='2022-09-15')
    assert res=={'data': [], 'num_page': 0, 'page': 1}
    res = QueryItemRegReportHelper.get(target_report='2', unit='Host', start_date='2022-09-01', end_date='2022-09-15')
    assert res=={'data': [], 'num_page': 0, 'page': 1}
    res = QueryItemRegReportHelper.get(target_report='3', unit='Day', start_date='0', end_date='0')
    assert res=={'data': [], 'num_page': 0, 'page': 1}
    res = QueryItemRegReportHelper.get(target_report='3', unit='Item', start_date='0', end_date='0')
    assert res=={'data': [], 'num_page': 0, 'page': 1}
    res = QueryItemRegReportHelper.get(target_report='3', unit='Host', start_date='0', end_date='0')
    assert res=={'data': [], 'num_page': 0, 'page': 1}

# class QueryRankingHelper(object):
#     def Calculation(cls, res, data_list):
#     def get(cls, **kwargs):
#     get_new_items(cls, **kwargs):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils.py::test_query_ranking_helper -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_query_ranking_helper(app, db, es):
    # Calculation
    _res = {
        'aggregations': {
            'my_buckets': {
                'buckets': [
                    {
                        'key': 'key1',
                        'my_sum': {
                            'value': 1
                        }
                    }
                ]
            }
        }
    }
    data_list = []
    QueryRankingHelper.Calculation(_res, data_list)
    assert data_list==[{'key': 'key1', 'count': 1}]

    # get
    res = QueryRankingHelper.get(event_type='record-view', group_field='pid_value', count_field='count', start_date='2022-09-01', end_date='2022-09-15')
    assert res==[]

    # get_new_items
    _res = {
        'hits': {
            'hits': [
                {
                    '_source': {
                        'path': 'path1'
                    }
                },
                {
                     '_source': {}
                }
            ]
        }
    }
    with patch('invenio_stats.queries.ESWekoRankingQuery.run', return_value=_res):
        res = QueryRankingHelper.get_new_items(must_not=json.dumps([{"wildcard": {"control_number": "*.*"}}]), start_date='2022-09-01', end_date='2022-09-15')
        assert res==[{'path': 'path1'}]

def test_query_ranking_helper_error(app, db):
    # get
    res = QueryRankingHelper.get(event_type='record-view', group_field='pid_value', count_field='count', start_date='2022-09-01', end_date='2022-09-15')
    assert res==[]
    # get_new_items
    res = QueryRankingHelper.get_new_items(must_not=json.dumps([{"wildcard": {"control_number": "*.*"}}]), start_date='2022-09-01', end_date='2022-09-15')
    assert res==[]


# class StatsCliUtil:
#     def __init__(
#     def delete_data(self, bookmark: bool = False) -> NoReturn:
#     def restore_data(self, bookmark: bool = False) -> NoReturn:
#     def __prepare_es_indexes(
#     def __build_es_data(self, data_list: list) -> Generator:
#     def __get_data_from_db_by_stats_type(self, data_model, bookmark):
#     def __get_stats_data_from_db(
#     def __show_message(self, index_name, success, failed):
#     def __cli_restore_es_data_from_db(
#     def __cli_delete_es_index(self, _index: str, doc_type: str) -> NoReturn:
#         def _delete_actions():
#     def __parse_date(
#         def _parse_day():
#         def _parse_month():
#         def _parse_year():
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils.py::test_StatsCliUtil -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_StatsCliUtil(app, db):
    _empty_types = [None]
    _event_types = ['file-download']
    _agg_types = ['file-download-agg']
    _return_event = [
        StatsEvents(
            index='stats-file-download',
            source_id='1',
            type='file-download',
            source=''
        )
    ]
    _return_agg = [
        StatsAggregation(
            index='test_index_agg',
            source_id='1',
            type='file-download-agg',
            source=''
        )
    ]
    _return_bookmark = [
        StatsBookmark(
            index='test_index_bookmark',
            source_id='1',
            type='bookmark',
            source=''
        )
    ]
    stats_cli = StatsCliUtil(
        StatsCliUtil.EVENTS_TYPE, _event_types, 202201
    )
    assert stats_cli.start_date == None

    stats_cli = StatsCliUtil(
        StatsCliUtil.EVENTS_TYPE, _event_types, '2022-01-01', '2022-01-03'
    )
    assert stats_cli.start_date == datetime.datetime(2022, 1, 1)
    assert stats_cli.end_date == datetime.datetime(2022, 1, 3, 23, 59, 59)

    stats_cli = StatsCliUtil(
        StatsCliUtil.EVENTS_TYPE, _event_types, '2022-01', '2022-03'
    )
    assert stats_cli.start_date == datetime.datetime(2022, 1, 5)
    assert stats_cli.end_date == datetime.datetime(2022, 3, 31, 23, 59, 59)

    stats_cli = StatsCliUtil(
        StatsCliUtil.EVENTS_TYPE, _event_types, '2022', '2023'
    )
    assert stats_cli.start_date == datetime.datetime(2022, 1, 1)
    assert stats_cli.end_date == datetime.datetime(2023, 12, 31, 23, 59, 59)

    # delete_data
    stats_cli = StatsCliUtil(
        StatsCliUtil.EVENTS_TYPE, _event_types, verbose=False, start_date='2022-01-01', end_date='2022-01-03'
    )
    assert not stats_cli.delete_data(True)

    stats_cli = StatsCliUtil(
        StatsCliUtil.EVENTS_TYPE, _event_types, verbose=False
    )
    assert not stats_cli.delete_data(True)



    stats_cli = StatsCliUtil(
        StatsCliUtil.EVENTS_TYPE, _empty_types, verbose=False
    )
    assert not stats_cli.delete_data(True)

    stats_cli = StatsCliUtil(
        StatsCliUtil.EVENTS_TYPE, _event_types, verbose=False
    )
    assert not stats_cli.delete_data(False)

    stats_cli = StatsCliUtil(
        StatsCliUtil.AGGREGATIONS_TYPE, _agg_types, verbose=False
    )
    assert not stats_cli.delete_data(True)

    with patch("invenio_stats.utils.len", return_value=2):
        stats_cli = StatsCliUtil(
            StatsCliUtil.EVENTS_TYPE, _event_types, verbose=True, force=False
        )
        assert not stats_cli.delete_data(True)

    stats_cli = StatsCliUtil(
        StatsCliUtil.EVENTS_TYPE, _event_types, verbose=True, force=False
    )
    assert not stats_cli.delete_data(True)

    stats_cli = StatsCliUtil(
        StatsCliUtil.EVENTS_TYPE, _event_types, verbose=True, force=True
    )
    assert not stats_cli.delete_data(True)

    # restore_data
    stats_cli = StatsCliUtil(
        StatsCliUtil.EVENTS_TYPE, _event_types, verbose=False
    )
    assert not stats_cli.restore_data(True)

    with pytest.raises(TypeError) as e:
        stats_cli = StatsCliUtil(
            StatsCliUtil.EVENTS_TYPE, _empty_types, verbose=False
        )
        assert not stats_cli.restore_data(True)

    stats_cli = StatsCliUtil(
        StatsCliUtil.EVENTS_TYPE, _event_types, verbose=False
    )
    assert not stats_cli.restore_data(False)

    stats_cli = StatsCliUtil(
        StatsCliUtil.AGGREGATIONS_TYPE, _agg_types, verbose=False
    )
    assert not stats_cli.restore_data(True)

    with pytest.raises(TypeError) as e:
        stats_cli = StatsCliUtil(
            StatsCliUtil.EVENTS_TYPE, _empty_types, verbose=True, start_date='2022-01-01', end_date='2022-01-03'
        )
        assert not stats_cli.restore_data(True)

    stats_cli = StatsCliUtil(
        StatsCliUtil.EVENTS_TYPE, None, verbose=True, start_date='2022-01-01', end_date='2022-01-03'
    )
    assert not stats_cli.restore_data(True)

    with patch("invenio_stats.models.StatsEvents.get_all", return_value=_return_event):
        with pytest.raises(Exception) as e:
            stats_cli = StatsCliUtil(
                StatsCliUtil.EVENTS_TYPE, None, verbose=True, start_date='2022-01-01', end_date='2022-01-03'
            )
            assert not stats_cli.restore_data(True)
