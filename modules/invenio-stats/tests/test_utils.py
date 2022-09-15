# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test utility functions."""

import pytest

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
    StatsCliUtil,
    )

# def get_anonymization_salt(ts):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_utils.py::test_get_anonymization_salt -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_get_anonymization_salt(app):
    res = get_anonymization_salt(datetime(2022, 1, 1))
    assert res=='DCP8arc0HLs8cvUN40DyjZZQIlKSETmsL05feCZyYRM='

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
    with pytest.raises(Exception) as e:
        default_permission_factory('test', {})==None
    assert e.type==UnknownQueryError

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
    res = QueryFileReportsHelper.get(year='2022', month='10', event='file_download')
    assert res=={'all': [], 'all_groups': [], 'date': '2022-10', 'open_access': []}
    res = QueryFileReportsHelper.get(year='2022', month='10', event='billing_file_download')
    assert res=={'all': [], 'all_groups': [], 'date': '2022-10', 'open_access': []}
    res = QueryFileReportsHelper.get(year='2022', month='10', event='file_using_per_user')
    assert res=={'all': [], 'all_groups': [], 'date': '2022-10', 'open_access': []}
    res = QueryFileReportsHelper.get(year='2022', month='10', event='test')
    assert res==[]

# class QuerySearchReportHelper(object):
#     def parse_bucket_response(cls, raw_res, pretty_result):
#     def get(cls, **kwargs):
# class QueryCommonReportsHelper(object):
#     def get_common_params(cls, **kwargs):
#     def get(cls, **kwargs):
#     def get_top_page_access_report(cls, **kwargs):
#         def Calculation(res, data_list):
#     def get_site_access_report(cls, **kwargs):
#         def Calculation(query_list, res, site_license_list, other_list,
#     def get_item_create_ranking(cls, **kwargs):
#         def Calculation(res, result):
# class QueryRecordViewPerIndexReportHelper(object):
#     def build_query(cls, start_date, end_date, after_key=None):
#     def parse_bucket_response(cls, aggs, result):
#     def get(cls, **kwargs):
# class QueryRecordViewReportHelper(object):
#     def Calculation(cls, res, data_list):
#     def get_title(cls, lst_id):
#     def correct_record_title(cls, lst_data):
#     def get(cls, **kwargs):
# class QueryItemRegReportHelper(object):
#     def get(cls, **kwargs):
#     def merge_items_results(cls, results):
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
