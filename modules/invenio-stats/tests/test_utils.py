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

from sqlalchemy.exc import UnsupportedCompilationError
from mock import patch
from datetime import datetime
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
    assert get_anonymization_salt(datetime(2022, 1, 1))

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

# def weko_permission_factory(*args, **kwargs):

# def get_aggregations(index, aggs_query):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils.py::test_get_aggregations -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_get_aggregations(app):
    res = get_aggregations('', {})
    assert res=={}

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

# class QueryFileReportsHelper(object):
#     def calc_per_group_counts(cls, group_names, current_stats, current_count):
#     def calc_file_stats_reports(cls, res, data_list, all_groups):
#     def calc_file_per_using_report(cls, res, data_list):
#     def Calculation(cls, res, data_list, all_groups=set()):
#     def get_file_stats_report(cls, is_billing_item=False, **kwargs):
#     def get_file_per_using_report(cls, **kwargs):
#     def get(cls, **kwargs):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils.py::test_query_file_reports_helper -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_query_file_reports_helper(app):
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
            }
        ]
    }
    _data_list = []
    _all_group = set()
    QueryFileReportsHelper.Calculation(_res, _data_list, _all_group)
    assert _data_list==[
        {'admin': 0, 'file_key': 'test1.pdf', 'group_counts': {'test1': 1, 'test2': 1}, 'index_list': 'index1', 'login': 0, 'no_login': 1, 'reg': 0, 'site_license': 1, 'total': 1},
        {'admin': 0, 'file_key': 'test2.pdf', 'group_counts': {'test2': 2, 'test3': 2}, 'index_list': 'index2', 'login': 2, 'no_login': 0, 'reg': 2, 'site_license': 0, 'total': 2},
        {'admin': 3, 'file_key': 'test3.pdf', 'group_counts': {'test3': 3}, 'index_list': 'index3', 'login': 3, 'no_login': 0, 'reg': 0, 'site_license': 0, 'total': 3}]
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


# class QuerySearchReportHelper(object):
#     def parse_bucket_response(cls, raw_res, pretty_result):
#     def get(cls, **kwargs):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils.py::test_query_search_report_helper -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_query_search_report_helper(app):
    # parse_bucket_response
    _raw_res = {
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
    res = QuerySearchReportHelper.parse_bucket_response(_raw_res, {})
    assert res=={'name1': 3, 'name2': 2}

    # get
    res = QuerySearchReportHelper.get(
        year=2022, month=10, start_date='2022-10-01', end_date='2022-10-31')
    assert res=={'all': []}


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
def test_query_common_reports_helper(app):
    # get_common_params
    res = QueryCommonReportsHelper.get_common_params(
        year=2022, month=10, start_date='2022-10-01', end_date='2022-10-10')
    assert res==('2022-10-01-2022-10-10', {'agg_size': 0, 'agg_sort': {'_term': 'desc'}, 'end_date': '2022-10-10T23:59:59', 'start_date': '2022-10-01'})
    res = QueryCommonReportsHelper.get_common_params(year=2022, month=10)
    assert res==('2022-10', {'end_date': '2022-10-31T23:59:59', 'start_date': '2022-10-01'})
    res = QueryCommonReportsHelper.get_common_params(year=2022, month=-1)
    assert res==('all', {'interval': 'day'})

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
def test_query_record_view_per_index_report_helper(app):
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
    assert res=={}


# class QueryRecordViewReportHelper(object):
#     def Calculation(cls, res, data_list):
#     def get_title(cls, lst_id):
#     def correct_record_title(cls, lst_data):
#     def get(cls, **kwargs):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils.py::test_query_record_view_report_helper -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_query_record_view_report_helper(app, db):
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

    # need to fix
    # Calculation
    with pytest.raises(Exception) as e:
        QueryRecordViewReportHelper.Calculation(_res, _data_list)
    assert e.type==UnsupportedCompilationError

    # get
    res = QueryRecordViewReportHelper.get(year=2022, month=9)
    assert res=={'all': [], 'date': '2022-09-01-2022-09-30'}

# class QueryItemRegReportHelper(object):
#     def get(cls, **kwargs):
#     def merge_items_results(cls, results):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils.py::test_query_item_reg_report_helper -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_query_item_reg_report_helper(app, db):
    # need to fix
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

# class QueryRankingHelper(object):
#     def Calculation(cls, res, data_list):
#     def get(cls, **kwargs):
#     get_new_items(cls, **kwargs):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils.py::test_query_ranking_helper -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_query_ranking_helper(app, db):
    # need to fix
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
