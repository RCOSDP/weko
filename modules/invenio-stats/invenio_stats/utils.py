# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Utilities for Invenio-Stats."""

from __future__ import absolute_import, print_function

import calendar
from itertools import islice
import operator
import os
import re
from base64 import b64encode
from datetime import datetime, timedelta
from math import ceil
import traceback
from typing import Generator, NoReturn, Union

import click
import netaddr
import six
from dateutil import parser
from elasticsearch import VERSION as ES_VERSION
from elasticsearch import exceptions as es_exceptions
from elasticsearch_dsl.aggs import A
from elasticsearch.helpers import bulk
from elasticsearch_dsl import Search, Q
from flask import current_app, request, session
from flask_login import current_user
from geolite2 import geolite2
from invenio_accounts.utils import get_user_ids_by_role
from invenio_cache import current_cache
from invenio_search import current_search_client
from weko_accounts.utils import get_remote_addr
from werkzeug.utils import import_string

from . import config
from .models import StatsAggregation, StatsBookmark, StatsEvents
from .permissions import stats_api_permission
from .proxies import current_stats


def get_anonymization_salt(ts):
    """Get the anonymization salt based on the event timestamp's day."""
    salt_key = 'stats:salt:{}'.format(ts.date().isoformat())
    salt = current_cache.get(salt_key)
    if not salt:
        salt_bytes = os.urandom(32)
        salt = b64encode(salt_bytes).decode('utf-8')
        current_cache.set(salt_key, salt, timeout=60 * 60 * 24)
    return salt


def get_geoip(ip):
    """Lookup country for IP address."""
    match = geolite2.reader().get(ip)
    return match.get('country', {}).get('iso_code') if match else None


def get_user():
    """User information.

    .. note::

       **Privacy note** A users IP address, user agent string, and user id
       (if logged in) is sent to a message queue, where it is stored for about
       5 minutes. The information is used to:

       - Detect robot visits from the user agent string.
       - Generate an anonymized visitor id (using a random salt per day).
       - Detect the users host contry based on the IP address.

       The information is then discarded.
    """
    return dict(
        ip_address=get_remote_addr(),
        user_agent=request.user_agent.string,
        user_id=(
            current_user.get_id() if current_user.is_authenticated else None
        ),
        session_id=session.get('sid_s')
    )


def obj_or_import_string(value, default=None):
    """Import string or return object.

    :params value: Import path or class object to instantiate.
    :params default: Default object to return if the import fails.
    :returns: The imported object.
    """
    if isinstance(value, six.string_types):
        return import_string(value)
    elif value:
        return value
    return default


def load_or_import_from_config(key, app=None, default=None):
    """Load or import value from config.

    :returns: The loaded value.
    """
    app = app or current_app
    imp = app.config.get(key)
    return obj_or_import_string(imp, default=default)


AllowAllPermission = type('Allow', (), {
    'can': lambda self: True,
    'allows': lambda *args: True,
})()


def default_permission_factory(query_name, params):
    """Default permission factory.

    It enables by default the statistics if they don't have a dedicated
    permission factory.
    """
    from invenio_stats import current_stats
    if current_stats.queries[query_name].permission_factory is None:
        return AllowAllPermission
    else:
        return current_stats.queries[query_name].permission_factory(
            query_name, params
        )


def weko_permission_factory(*args, **kwargs):  # All queries have same perms
    """Permission factory for weko queries."""

    def can(self):
        return current_user.is_authenticated and stats_api_permission.can()

    return type('WekoStatsPermissionChecker', (), {'can': can})()


def get_aggregations(index, aggs_query):
    """Get aggregations.

    :param index:
    :param aggs_query:
    :return:
    """
    results = {}
    if index and aggs_query and 'aggs' in aggs_query:
        from invenio_indexer.api import RecordIndexer
        results = RecordIndexer().client.search(
            index=index, body=aggs_query)

    return results


def get_start_end_date(year, month):
    """Get first of the month and last of the month."""
    query_month = str(year) + '-' + str(month).zfill(2)
    _, lastday = calendar.monthrange(year, month)
    start_date = query_month + '-01'
    end_date = query_month + '-' + str(lastday).zfill(2)  # + 'T23:59:59'
    return start_date, end_date


def agg_bucket_sort(agg_sort, buckets):
    """Bucket sort.

    :param agg_sort: dict with key_name and order.
    :param buckets: list of dicts to be ordered.
    """
    if agg_sort:
        order = True if agg_sort['order'] == 'desc' else False
        buckets = sorted(buckets,
                         key=lambda x: x[agg_sort['key_name']],
                         reverse=order)
    return buckets


def parse_bucket_response(raw_res, pretty_result=dict()):
    """Parsing bucket response."""
    if 'buckets' in raw_res:
        field_name = raw_res['field']
        value = raw_res['buckets'][0]['key']
        pretty_result[field_name] = value
        return parse_bucket_response(
            raw_res['buckets'][0], pretty_result)
    else:
        return pretty_result


def get_doctype(doc_type):
    """Configure doc_type value according to ES version."""
    return doc_type if ES_VERSION[0] < 7 else '_doc'


def is_valid_access():
    """
    Distinguish valid accesses for stats from incoming accesses.

    Regard all accesses as valid if `STATS_EXCLUDED_ADDRS` is set to `[]`.
    """
    ip_list = current_app.config['STATS_EXCLUDED_ADDRS']
    ipaddr = get_remote_addr()
    if ip_list and ipaddr:
        for i in range(len(ip_list)):
            if '/' in ip_list[i]:
                if netaddr.IPAddress(ipaddr) in netaddr.IPNetwork(ip_list[i]):
                    return False
            else:
                if ipaddr == ip_list[i]:
                    return False
    return True


def chunk_list(iterable, size):
    """
    Split a List into chunks of a specified size.

    Args:
        iterable (list): The List to be split.
        size (int): The size of each chunk.

    Yields:
        list: A chunk of the original List with the specified size.

    """
    it = iter(iterable)
    while True:
        chunk = list(islice(it, size))
        if not chunk:
            break
        yield chunk


class QueryFileReportsHelper(object):
    """Helper for parsing elasticsearch aggregations."""

    @classmethod
    def calc_per_group_counts(cls, group_names, current_stats, current_count):
        """Count the downloads for group."""
        groups = [g.strip() for g in group_names.split(',') if g]
        for group in groups:
            if group in current_stats:
                current_stats[group] += current_count
            else:
                current_stats[group] = current_count
        return current_stats

    @classmethod
    def calc_file_stats_reports(cls, res, data_list, all_groups):
        """Create response object for file_stats_reports."""
        mapper = {}
        for i in res['buckets']:
            key_str = '{}_{}'.format(i['file_key'], i['index_list'])
            if key_str in mapper:
                data = data_list[mapper[key_str]]
            else:
                mapper[key_str] = len(data_list)
                data = {}
                data['group_counts'] = {}  # Keep track of downloads per group
                data['file_key'] = i['file_key']
                data['index_list'] = i['index_list']
                data['total'] = 0
                data['admin'] = 0
                data['reg'] = 0
                data['login'] = 0
                data['no_login'] = 0
                data['site_license'] = 0
                data_list.append(data)

            count = i['count']
            data['total'] += count
            if i['site_license_flag'] == 1:
                data['site_license'] += count
            if i['userrole'] == 'guest':
                data['no_login'] += count
            elif i['userrole'] == 'Contributor':
                data['reg'] += count
                data['login'] += count
            elif i['userrole'] in current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER']+ current_app.config["WEKO_PERMISSION_ROLE_COMMUNITY"]:
                data['admin'] += count
                data['login'] += count
            else:
                data['login'] += count

            # Get groups counts
            if 'user_group_names' in i:
                group_list = i['user_group_names']
                data['group_counts'] = cls.calc_per_group_counts(
                    group_list, data['group_counts'], count)

            # Keep track of groups seen
            all_groups.update(data['group_counts'].keys())

    @classmethod
    def calc_file_per_using_report(cls, res, data_list):
        """Create response object for file_per_using_report."""
        # file-download
        for item in res['get-file-download-per-user-report']['buckets']:
            data = {}
            data['cur_user_id'] = item['cur_user_id']
            data['total_download'] = item['count']
            data_list.update({item['cur_user_id']: data})
        # file-preview
        for item in res['get-file-preview-per-user-report']['buckets']:
            data = {}
            data['cur_user_id'] = item['cur_user_id']
            data['total_preview'] = item['count']
            if data_list.get(item['cur_user_id']):
                data_list[item['cur_user_id']].update(data)
            else:
                data_list.update({item['cur_user_id']: data})

    @classmethod
    def Calculation(cls, res, data_list, all_groups=set()):
        """Calculation."""
        if 'buckets' in res and res['buckets'] is not None:
            cls.calc_file_stats_reports(res, data_list, all_groups)
        elif res['get-file-download-per-user-report'] is not None \
                and res['get-file-preview-per-user-report'] is not None:
            cls.calc_file_per_using_report(res, data_list)

    @classmethod
    def get_file_stats_report(cls, is_billing_item=False, **kwargs):
        """Get file download/preview report."""
        from weko_index_tree.utils import get_descendant_index_names
        from invenio_communities.models import Community

        result = {}
        all_list = []
        open_access_list = []
        all_groups = set()

        event = kwargs.get('event')
        year = kwargs.get('year')
        month = kwargs.get('month')
        repository_id = kwargs.get('repository_id')

        if repository_id and repository_id != 'Root Index':
            repository = Community.query.get(repository_id)
            index_list = get_descendant_index_names(repository.root_node_id) if repository else []

        try:
            query_month = str(year) + '-' + str(month).zfill(2)
            _, lastday = calendar.monthrange(year, month)
            all_params = {'start_date': query_month + '-01',
                          'end_date':
                          query_month + '-' + str(lastday).zfill(2)
                          + 'T23:59:59'}
            params = {'start_date': query_month + '-01',
                      'end_date':
                      query_month + '-' + str(lastday).zfill(2)
                      + 'T23:59:59',
                      'accessrole': 'open_access'}
            if repository_id and repository_id != 'Root Index':
                all_params['index_list'] = index_list
                params['index_list'] = index_list
            else:
                all_params['index_list'] = None
                params['index_list'] = None

            all_query_name = ''
            open_access_query_name = ''
            if event == 'file_download':
                all_query_name = 'get-file-download-report'
                open_access_query_name = 'get-file-download-open-access-report'
            elif event == 'file_preview':
                all_query_name = 'get-file-preview-report'
                open_access_query_name = 'get-file-preview-open-access-report'
            elif event in ['billing_file_download', 'billing_file_preview']:
                all_params['is_billing_item'] = is_billing_item
                all_query_name = 'get-' + event.replace('_', '-') + '-report'

            # all
            all_query_cfg = current_stats.queries[all_query_name]
            all_query = all_query_cfg.query_class(**all_query_cfg.query_config)
            all_res = all_query.run(**all_params)
            cls.Calculation(all_res, all_list, all_groups=all_groups)

            # open access -- Only run for non-billed items
            if open_access_query_name:
                open_access_query_cfg = current_stats.queries[open_access_query_name]
                open_access = open_access_query_cfg.query_class(
                    **open_access_query_cfg.query_config)
                open_access_res = open_access.run(**params)
                cls.Calculation(open_access_res, open_access_list)
        except Exception as e:
            current_app.logger.error(e)
            traceback.print_exc()

        result['date'] = query_month
        result['all'] = all_list
        result['open_access'] = open_access_list
        result['all_groups'] = list(all_groups)
        return result

    @classmethod
    def get_file_per_using_report(cls, **kwargs):
        """Get File Using Per User report."""
        from invenio_communities.models import Community
        result = {}
        all_list = {}
        all_res = {}

        year = kwargs.get('year')
        month = kwargs.get('month')
        repository_id = kwargs.get('repository_id')

        try:
            query_month = str(year) + '-' + str(month).zfill(2)
            _, lastday = calendar.monthrange(year, month)
            params = {'start_date': query_month + '-01',
                      'end_date': query_month + '-' + str(lastday).zfill(2)
                      + 'T23:59:59'}
            if repository_id and repository_id != 'Root Index':
                repository = Community.query.get(repository_id)
                user_ids = get_user_ids_by_role(repository.group_id) if repository_id else []
                params['user_ids'] = user_ids
            else:
                params['user_ids'] = None

            all_query_name = ['get-file-download-per-user-report',
                              'get-file-preview-per-user-report']
            for query in all_query_name:
                all_query_cfg = current_stats.queries[query]
                all_query = all_query_cfg.\
                    query_class(**all_query_cfg.query_config)
                all_res[query] = all_query.run(**params)
            cls.Calculation(all_res, all_list)

        except Exception as e:
            current_app.logger.error(e)
            traceback.print_exc()

        result['date'] = query_month
        result['all'] = all_list

        return result

    @classmethod
    def get(cls, **kwargs):
        """Get file reports."""
        event = kwargs.get('event')
        if event == 'file_download' or event == 'file_preview':
            return cls.get_file_stats_report(**kwargs)
        elif event in ['billing_file_download', 'billing_file_preview']:
            return cls.get_file_stats_report(is_billing_item=True, **kwargs)
        elif event == 'file_using_per_user':
            return cls.get_file_per_using_report(**kwargs)
        else:
            return []


class QuerySearchReportHelper(object):
    """Search Report helper."""

    @classmethod
    def parse_bucket_response(cls, raw_res, pretty_result):
        """Parsing bucket response."""
        if 'buckets' in raw_res:
            field_name = raw_res['field']
            value = raw_res['buckets'][0]['key']
            pretty_result[field_name] = value
            return cls.parse_bucket_response(
                raw_res['buckets'][0], pretty_result)
        else:
            return pretty_result

    @classmethod
    def get(cls, **kwargs):
        """Get number of searches per keyword."""
        result = {}
        year = kwargs.get('year')
        month = kwargs.get('month')
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        repository_id = kwargs.get('repository_id')

        try:
            if not start_date or not end_date:
                start_date, end_date = get_start_end_date(year, month)
                result['date'] = str(year) + '-' + str(month).zfill(2)
            params = {'start_date': start_date,
                      'end_date': end_date + 'T23:59:59',
                      'agg_size': kwargs.get('agg_size', 0),
                      'agg_filter': kwargs.get('agg_filter', None)}
            if repository_id and repository_id != 'Root Index':
                params['wildcard'] = {"referrer": f"*{repository_id}*"}

            # Run query
            keyword_query_cfg = current_stats.queries['get-search-report']
            keyword_query = keyword_query_cfg.query_class(
                **keyword_query_cfg.query_config)
            raw_result = keyword_query.run(**params)

            all = []
            for report in raw_result['buckets']:
                current_report = {}
                current_report['search_key'] = report['search_key']
                current_report['count'] = report['count']
                all.append(current_report)
            all = sorted(all, key=lambda x:x['count'], reverse=True)
            result['all'] = all
        except es_exceptions.NotFoundError as e:
            current_app.logger.debug(
                "Indexes do not exist yet:" + str(e.info['error']))
            result['all'] = []
        except Exception as e:
            current_app.logger.debug(e)
            result['all'] = []

        return result


class QueryCommonReportsHelper(object):
    """CommonReports helper class."""

    @classmethod
    def get_common_params(cls, **kwargs):
        """Get common params."""
        from invenio_communities.models import Community
        from weko_index_tree.utils import get_descendant_index_names
        year = kwargs.get('year')
        month = kwargs.get('month')
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        repository_id = kwargs.get('repository_id')
        if not start_date or not end_date:
            if month > 0 and month <= 12:
                query_date = str(year) + '-' + str(month).zfill(2)
                _, lastday = calendar.monthrange(year, month)
                params = {'start_date': query_date + '-01',
                          'end_date': query_date + '-'
                          + str(lastday).zfill(2) + 'T23:59:59'}
            else:
                query_date = 'all'
                params = {'interval': 'day'}
        else:
            query_date = start_date + '-' + end_date
            params = {'start_date': start_date,
                      'end_date': end_date + 'T23:59:59',
                      'agg_size': kwargs.get('agg_size', 0),
                      'agg_sort': kwargs.get('agg_sort', {'_term': 'desc'})}
        if repository_id and repository_id != 'Root Index':
            repository = Community.query.get(repository_id)
            index_list = get_descendant_index_names(repository.root_node_id)
            params['index_list'] = index_list
            params['wildcard'] = {"referrer": f"*{repository_id}*"}
        else:
            params['index_list'] = None
        return query_date, params

    @classmethod
    def get(cls, **kwargs):
        """Get file reports."""
        event = kwargs.get('event')
        if event == 'top_page_access':
            return cls.get_top_page_access_report(**kwargs)
        elif event == 'site_access':
            return cls.get_site_access_report(**kwargs)
        elif event == 'item_create':
            return cls.get_item_create_ranking(**kwargs)
        else:
            return []

    @classmethod
    def get_top_page_access_report(cls, **kwargs):
        """Get toppage access report."""
        def Calculation(res, data_list):
            """Calculation."""
            if 'top-view-total-per-host' in res:
                temp_data = []
                for item in res['top-view-total-per-host']['buckets']:
                    data = {}
                    data['host'] = item['hostname']
                    data['ip'] = item['remote_addr']
                    data['count'] = item['count']
                    temp_data.append(data)
                temp_data = sorted(temp_data, key=lambda x:x['count'], reverse=True)
                for item in temp_data:
                    data_list.update({item['ip']: item})
            elif 'top-view-total' in res:
                for item in res['top-view-total']['buckets']:
                    data_list.update({item['date']:{'count': item['value']}})
            else:
                data = {}
                data['errors'] = str(res)
                data_list = data

        result = {}
        all_list = {}
        all_res = {}
        query_month = ''

        try:
            query_month, params = cls.get_common_params(**kwargs)
            if query_month == 'all':
                all_query_name = ['top-view-total']
            else:
                all_query_name = ['top-view-total-per-host']

            for query in all_query_name:
                all_query_cfg = current_stats.queries[query]
                all_query = all_query_cfg.\
                    query_class(**all_query_cfg.query_config)
                all_res[query] = all_query.run(**params)

            Calculation(all_res, all_list)

        except Exception as e:
            current_app.logger.debug(e)

        result['date'] = query_month
        result['all'] = all_list

        return result

    @classmethod
    def get_site_access_report(cls, **kwargs):
        """Get site access report."""
        def Calculation(query_list, res, site_license_list, other_list,
                        institution_name_list):
            """Calculation."""
            mapper = {}
            for k in query_list:
                items = res.get(k)
                site_license_list[k] = 0
                other_list[k] = 0
                if items:
                    for i in items['buckets']:
                        if i['site_license_name'] == '':
                            other_list[k] += i['count']
                        else:
                            site_license_list[k] += i['count']
                            if i['site_license_name'] in mapper:
                                institution_name_list[
                                    mapper[i['site_license_name']]
                                    ][k] = i['count']
                            else:
                                mapper[i['site_license_name']] = len(institution_name_list)
                                data = {}
                                data['name'] = i['site_license_name']
                                data[k] = i['count']
                                institution_name_list.append(data)
            for k in query_list:
                for i in range(len(institution_name_list)):
                    if k not in institution_name_list[i]:
                        institution_name_list[i][k] = 0

        result = {}
        all_res = {}
        site_license_list = {}
        other_list = {}
        institution_name_list = []
        query_month = ''

        query_list = ['top_view', 'search', 'record_view',
                      'file_download', 'file_preview']
        try:
            query_month, params = cls.get_common_params(**kwargs)
            for q in query_list:
                query_cfg = current_stats.queries['get-' + q.replace('_', '-')
                                                  + '-per-site-license']
                query = query_cfg.query_class(**query_cfg.query_config)
                all_res[q] = query.run(**params)
            Calculation(query_list, all_res, site_license_list, other_list,
                        institution_name_list)

        except Exception as e:
            current_app.logger.debug(e)

        result['date'] = query_month
        result['site_license'] = [site_license_list]
        result['other'] = [other_list]
        result['institution_name'] = institution_name_list
        return result

    @classmethod
    def get_item_create_ranking(cls, **kwargs):
        """Get item create ranking."""
        def Calculation(res, result):
            """Calculation."""
            for item in res['buckets']:
                for pid in item['buckets']:
                    data = {}
                    data['create_date'] = item['key'] / 1000  # for utc change
                    data['pid_value'] = pid['key']
                    if 'buckets' in pid:
                        name = pid['buckets'][0]['key']
                    else:
                        name = ''
                    data['record_name'] = name
                    result.append(data)

        result = {}
        data_list = []
        query_date = ''
        try:
            query_date, params = cls.get_common_params(**kwargs)
            query_cfg = current_stats.queries['item-create-per-date']
            query = query_cfg.query_class(**query_cfg.query_config)
            res = query.run(**params)
            Calculation(res, data_list)
        except Exception as e:
            current_app.logger.debug(e)

        result['date'] = query_date
        result['all'] = data_list
        return result


class QueryRecordViewPerIndexReportHelper(object):
    """RecordViewPerIndex helper class."""

    nested_path = 'record_index_list'
    index_id_field = 'record_index_list.index_id'
    index_name_field = 'record_index_list.index_name'

    @classmethod
    def build_query(cls, start_date, end_date, after_key=None, index_list=None):
        """Get nested aggregation by index id."""
        agg_query = Search(
            using=current_search_client,
            index='{}-events-stats-record-view'.format(
                current_app.config['SEARCH_INDEX_PREFIX'].strip('-')),
            doc_type='stats-record-view')[0:0]  # FIXME: Get ALL results

        if start_date is not None and end_date is not None:
            time_range = {}
            time_range['gte'] = parser.parse(start_date).isoformat()
            time_range['lte'] = parser.parse(end_date).isoformat()
            agg_query = agg_query.filter(
                'range', **{'timestamp': time_range}).filter(
                'term', **{'is_restricted': False})
        if index_list:
            nested_query = Q(
                'nested',
                path=cls.nested_path,
                query=Q('terms', **{cls.index_name_field: index_list})
            )
            agg_query = agg_query.filter(nested_query)

        size = current_app.config['STATS_ES_INTEGER_MAX_VALUE']
        sources = [{cls.index_id_field: A('terms', field=cls.index_id_field)},
                   {cls.index_name_field: A('terms', field=cls.index_name_field)}]

        base_agg = agg_query.aggs.bucket(cls.nested_path, 'nested', path=cls.nested_path)
        if after_key:
            base_agg.bucket('my_buckets', 'composite', size=size, sources=sources, after=after_key)
        else:
            base_agg.bucket('my_buckets', 'composite', size=size, sources=sources)
        return agg_query

    @classmethod
    def parse_bucket_response(cls, aggs, result):
        """Parse raw aggregation response."""
        count = 0
        for data in aggs['my_buckets']['buckets']:
            result['all'].append({'index_name': data['key'][cls.index_name_field],
                                  'view_count': data['doc_count']})
            count += data['doc_count']
        return count

    @classmethod
    def get(cls, **kwargs):
        """Get record view per index report.

        Nested aggregations are currently unsupported so manually aggregating.
        """
        from weko_index_tree.utils import get_descendant_index_names
        from invenio_communities.models import Community

        result = {}
        year = kwargs.get('year')
        month = kwargs.get('month')
        repository_id = kwargs.get('repository_id')

        try:
            query_month = str(year) + '-' + str(month).zfill(2)
            _, lastday = calendar.monthrange(year, month)
            start_date = query_month + '-01'
            end_date = query_month + '-' + str(lastday).zfill(2) + 'T23:59:59'
            index_list = None
            if repository_id and repository_id != 'Root Index':
                repository = Community.query.get(repository_id)
                index_list = get_descendant_index_names(repository.root_node_id) if repository else []
            result = {'date': query_month, 'all': [], 'total': 0}
            first_search = True
            after_key = None
            total = 1
            count = 0
            while count < total and (after_key or first_search):
                agg_query = cls.build_query(start_date, end_date, after_key, index_list)
                current_app.logger.debug(agg_query.to_dict())
                temp_res = agg_query.execute().to_dict()
                aggs = temp_res['aggregations'][cls.nested_path]
                if 'after_key' in aggs['my_buckets']:
                    after_key = aggs['my_buckets']['after_key']
                else:
                    after_key = None
                if first_search:
                    first_search = False
                    result['total'] = aggs['doc_count']
                    total = aggs['doc_count']
                count += cls.parse_bucket_response(aggs, result)

        except Exception as e:
            current_app.logger.error(e)
            traceback.print_exc()
            return {}

        return result


class QueryRecordViewReportHelper(object):
    """RecordViewReport helper class."""

    @classmethod
    def Calculation(cls, res, data_list):
        """Create response object."""
        for item in res['buckets']:
            data = {
                'record_id': item['record_id'],
                'record_name': item['record_name'],
                'index_names': item['record_index_names'],
                'total_all': item['count'],
                'pid_value': item['pid_value'],
                'total_not_login': item['count']
                    if item['cur_user_id'] == 'guest' else 0
            }
            data_list.append(data)
        cls.correct_record_title(data_list)

    @classmethod
    def get_title(cls, lst_id):
        """
        Get title records based on given list id.

        @param lst_id:
        @return:
        """
        from invenio_db import db
        from invenio_records.models import RecordMetadata
        with db.session.no_autoflush:
            query = RecordMetadata.query.filter(
                RecordMetadata.id.in_(lst_id)).with_entities(RecordMetadata.id,
                                                             RecordMetadata.
                                                             json[
                                                                 'title'].
                                                             label(
                                                                 'title'))
            obj = query.all()
            return obj

    @classmethod
    def correct_record_title(cls, lst_data):
        """Correct title if many items has same id but diff title.

        @param lst_data:
        @return:
        """
        lst_data_dict = {}
        for i in lst_data:
            if lst_data_dict.get(i['record_id']):
                lst_data_dict[i['record_id']]['total_all'] += i['total_all']
                lst_data_dict[i['record_id']]['total_not_login'] += i[
                    'total_not_login']
                if lst_data_dict[i['record_id']]['record_name'] != i[
                        'record_name']:
                    lst_data_dict[i['record_id']]['same_title'] = False
            else:
                lst_data_dict[i['record_id']] = i
                lst_data_dict[i['record_id']]['same_title'] = True

        # Collect list need to get latest title
        values = list(lst_data_dict.values())
        lst_to_get_title = [i['record_id'] for i in values if
                            not i['same_title']]

        lst_titles = list(cls.get_title(lst_to_get_title))
        lst_titles_dict = {}
        [lst_titles_dict.update({str(i[0]): i[1][0]}) for i in lst_titles]

        for i in values:
            if not i['same_title']:
                i['record_name'] = lst_titles_dict[i['record_id']]
        values = sorted(values, key=operator.itemgetter("total_all"),
                        reverse=True)
        lst_data.clear()
        lst_data.extend(values)

    @classmethod
    def get(cls, **kwargs):
        """Get record view report."""
        from weko_index_tree.utils import get_descendant_index_names
        from invenio_communities.models import Community
        result = {}
        all_list = []
        query_date = ''

        try:
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            if not start_date or not end_date:
                year = kwargs.get('year')
                month = kwargs.get('month')
                query_date = str(year) + '-' + str(month).zfill(2)
                _, lastday = calendar.monthrange(year, month)
                start_date = query_date + '-01'
                end_date = query_date + '-' + str(lastday).zfill(2)
                query_date = start_date + '-' + end_date
            params = {'start_date': start_date,
                      'end_date': end_date + 'T23:59:59'}
            if not kwargs.get('ranking', False):
                # Limit size
                params.update({'agg_size': kwargs.get('agg_size', 0)})
            repository_id = kwargs.get('repository_id')
            if repository_id and repository_id != 'Root Index':
                repository = Community.query.get(repository_id)
                index_list = get_descendant_index_names(repository.root_node_id) if repository else []
                params['agg_filter'] = {'record_index_names': index_list}
            all_query_cfg = current_stats.queries['get-record-view-report']
            all_query = all_query_cfg.query_class(**all_query_cfg.query_config)

            all_res = all_query.run(**params)
            cls.Calculation(all_res, all_list)

        except es_exceptions.NotFoundError as e:
            current_app.logger.error(e)
            traceback.print_exc()
            result['all'] = []
        except Exception as e:
            current_app.logger.error(e)
            traceback.print_exc()

        result['date'] = query_date
        result['all'] = all_list

        return result


class QueryItemRegReportHelper(object):
    """Helper for providing item registration report."""

    @classmethod
    def get(cls, **kwargs):
        """Get item registration report."""
        from weko_index_tree.utils import get_descendant_index_names, get_item_ids_in_index
        from invenio_communities.models import Community

        target_report = kwargs.get('target_report').title()
        start_date = datetime.strptime(kwargs.get('start_date'), '%Y-%m-%d') \
            if kwargs.get('start_date') != '0' else None
        end_date = datetime.strptime(kwargs.get('end_date'), '%Y-%m-%d') \
            if kwargs.get('end_date') != '0' else None
        unit = kwargs.get('unit').title()
        empty_date_flg = True if not start_date or not end_date else False

        query_name = 'item-create-total'
        count_keyname = 'count'
        if target_report == config.TARGET_REPORTS['Item Detail']:
            if unit == 'Item':
                query_name = 'item-detail-item-total'
            else:
                query_name = 'item-detail-total' \
                    if not empty_date_flg or unit == 'Host' \
                    else 'bucket-item-detail-view-histogram'
        elif target_report == config.TARGET_REPORTS['Contents Download']:
            if unit == 'Item':
                query_name = 'get-file-download-per-item-report'
            else:
                query_name = 'get-file-download-per-host-report' \
                    if not empty_date_flg or unit == 'Host' \
                    else 'get-file-download-per-time-report'
        elif empty_date_flg:
            query_name = 'item-create-histogram'

        # total
        query_total_cfg = current_stats.queries[query_name]
        query_total = query_total_cfg.query_class(
            **query_total_cfg.query_config)

        d = start_date

        total_results = 0
        reports_per_page = kwargs.get('reports_per_page',
                                      int(getattr(config, 'REPORTS_PER_PAGE')))
        # get page_index from request params
        page_index = kwargs.get('page_index', 0)

        repository_id = kwargs.get('repository_id')
        if repository_id and repository_id != 'Root Index':
            repository = Community.query.get(repository_id)
            index_list = get_descendant_index_names(repository.root_node_id) if repository else []
            item_ids = get_item_ids_in_index(repository.root_node_id) if repository else []

        result = []
        if empty_date_flg or end_date >= start_date:
            try:
                if unit == 'Day':
                    if empty_date_flg:
                        params = {'interval': 'day'}
                        if repository_id and repository_id != 'Root Index':
                            params.update({'index_list': index_list,'item_ids': item_ids})
                        else:
                            params.update({'index_list': None,'item_ids': None})
                        res_total = query_total.run(**params)
                        # Get valuable items
                        items = []
                        for item in res_total['buckets']:
                            date = item['date'].split('T')[0]
                            if item['value'] > 0 \
                                    and (not start_date or date >= start_date.strftime('%Y-%m-%d')) \
                                    and (not end_date or date <= end_date.strftime('%Y-%m-%d')):
                                items.append(item)
                        # total results
                        total_results = len(items)
                        i = 0
                        for item in items:
                            if page_index * \
                                    reports_per_page <= i < (page_index + 1) * reports_per_page:
                                date = item['date'].split('T')[0]
                                result.append({
                                    'count': item['value'],
                                    'start_date': date,
                                    'end_date': date,
                                })
                            i += 1
                    else:
                        # total results
                        total_results = (end_date - start_date).days + 1
                        delta = timedelta(days=1)
                        for i in range(total_results):
                            if page_index * reports_per_page <= i < (
                                    page_index + 1) * reports_per_page:
                                d_start = d.replace(hour=0, minute=0, second=0,
                                                    microsecond=0)
                                d_end = d.replace(hour=23, minute=59, second=59,
                                                  microsecond=9999)
                                start_date_string = d_start.strftime(
                                    '%Y-%m-%d %H:%M:%S')
                                end_date_string = d_end.strftime(
                                    '%Y-%m-%d %H:%M:%S')
                                params = {'interval': 'day',
                                          'start_date': start_date_string,
                                          'end_date': end_date_string,
                                          'is_restricted': False
                                          }
                                if repository_id and repository_id != 'Root Index':
                                    params.update({'index_list': index_list,
                                                    'agg_filter': {'pid_value': item_ids}})
                                else:
                                    params.update({'index_list': None})
                                res_total = query_total.run(**params)
                                result.append({
                                    'count': res_total[count_keyname],
                                    'start_date': start_date_string,
                                    'end_date': end_date_string,
                                    'is_restricted': False
                                })
                            d += delta
                elif unit == 'Week':
                    delta = timedelta(days=7)
                    delta1 = timedelta(days=1)
                    if empty_date_flg:
                        params = {'interval': 'week', 'is_restricted': False}
                        if repository_id and repository_id != 'Root Index':
                            params.update({'index_list': index_list, 'item_ids': item_ids})
                        else:
                            params.update({'index_list': None, 'item_ids': None})
                        res_total = query_total.run(**params)
                        # Get valuable items
                        items = []
                        for item in res_total['buckets']:
                            date = item['date'].split('T')[0]
                            if item['value'] > 0 \
                                    and (not start_date or date >= start_date.strftime('%Y-%m-%d')) \
                                    and (not end_date or date <= end_date.strftime('%Y-%m-%d')):
                                items.append(item)
                        # total results
                        total_results = len(items)
                        i = 0
                        import pytz
                        for item in items:
                            if item == items[0]:
                                # Start date of data
                                d = parser.parse(item['date'])

                            if page_index * \
                                    reports_per_page <= i < (page_index + 1) * reports_per_page:
                                start_date_string = d.strftime('%Y-%m-%d')
                                d1 = d + delta - delta1
                                if end_date and d1 > end_date.replace(
                                        tzinfo=pytz.UTC):
                                    d1 = end_date
                                end_date_string = d1.strftime('%Y-%m-%d')
                                result.append({
                                    'count': item['value'],
                                    'start_date': start_date_string,
                                    'end_date': end_date_string,
                                    'is_restricted': False
                                })
                            d += delta
                            i += 1
                    else:
                        # total results
                        total_results = int(
                            (end_date - start_date).days / 7) + 1

                        d = start_date
                        for i in range(total_results):
                            if page_index * \
                                    reports_per_page <= i < (page_index + 1) * reports_per_page:
                                d_start = d.replace(hour=0, minute=0, second=0,
                                                    microsecond=0)
                                start_date_string = d_start.strftime('%Y-%m-%d %H:%M:%S')
                                d1 = d + delta - delta1
                                if d1 > end_date:
                                    d1 = end_date
                                d_end = d1.replace(hour=23, minute=59, second=59,
                                                  microsecond=9999)
                                end_date_string = d_end.strftime('%Y-%m-%d %H:%M:%S')
                                temp = {
                                    'start_date': start_date_string,
                                    'end_date': end_date_string,
                                    'is_restricted': False
                                }
                                params = {'interval': 'week',
                                          'start_date': temp['start_date'],
                                          'end_date': temp['end_date'],
                                          'is_restricted': False
                                          }
                                if repository_id and repository_id != 'Root Index':
                                    params.update({'index_list': index_list,
                                                    'agg_filter': {'pid_value': item_ids}})
                                else:
                                    params.update({'index_list': None})
                                res_total = query_total.run(**params)
                                temp['count'] = res_total[count_keyname]
                                result.append(temp)

                            d += delta
                elif unit == 'Year':
                    if empty_date_flg:
                        params = {'interval': 'year', 'is_restricted': False}
                        if repository_id and repository_id != 'Root Index':
                            params.update({'index_list': index_list, 'item_ids': item_ids})
                        else:
                            params.update({'index_list': None, 'item_ids': None})
                        res_total = query_total.run(**params)
                        # Get start day and end day
                        start_date_string = '{}-01-01'.format(
                            start_date.year) if start_date else None
                        end_date_string = '{}-12-31'.format(
                            end_date.year) if end_date else None
                        # Get valuable items
                        items = []
                        for item in res_total['buckets']:
                            date = item['date'].split('T')[0]
                            if item['value'] > 0 and (
                                    not start_date_string or date >= start_date_string) and (
                                    not end_date_string or date <= end_date_string):
                                items.append(item)
                        # total results
                        total_results = len(items)
                        i = 0
                        for item in items:
                            if page_index * \
                                    reports_per_page <= i < (page_index + 1) * reports_per_page:
                                event_date = parser.parse(item['date'])
                                result.append({
                                    'count': item['value'],
                                    'start_date': '{}-01-01'.format(event_date.year),
                                    'end_date': '{}-12-31'.format(event_date.year),
                                    'year': event_date.year,
                                    'is_restricted': False
                                })
                            i += 1
                    else:
                        start_year = start_date.year
                        end_year = end_date.year
                        # total results
                        total_results = end_year - start_year + 1
                        for i in range(total_results):
                            if page_index * \
                                    reports_per_page <= i < (page_index + 1) * reports_per_page:
                                start_date_string = '{}-01-01 00:00:00'.format(
                                    start_year + i)
                                end_date_string = '{}-12-31 23:59:59'.format(
                                    start_year + i)
                                params = {'interval': 'year',
                                          'start_date': start_date_string,
                                          'end_date': end_date_string,
                                          'is_restricted': False
                                          }
                                if repository_id and repository_id != 'Root Index':
                                    params.update({'index_list': index_list,
                                                    'agg_filter': {'pid_value': item_ids}})
                                else:
                                    params.update({'index_list': None})
                                res_total = query_total.run(**params)
                                result.append({
                                    'count': res_total[count_keyname],
                                    'start_date': start_date_string,
                                    'end_date': end_date_string,
                                    'year': start_year + i,
                                    'is_restricted': False
                                })
                elif unit == 'Item':
                    start_date_string = ''
                    end_date_string = ''
                    params = {'is_restricted': False}
                    if start_date is not None:
                        start_date_string = start_date.strftime('%Y-%m-%d 00:00:00')
                        params.update({'start_date': start_date_string})
                    if end_date is not None:
                        end_date_string = end_date.strftime('%Y-%m-%d 23:59:59')
                        params.update({'end_date': end_date_string})
                    if not kwargs.get('ranking', False):
                        # Limit size
                        params.update({'agg_size': kwargs.get('agg_size', 0)})
                    else:
                        params.update({'agg_sort': kwargs.get(
                            'agg_sort', {'_count': 'desc'})})
                    if repository_id and repository_id != 'Root Index':
                        params.update({'index_list': index_list})
                    else:
                        params.update({'index_list': None})
                    res_total = query_total.run(**params)  # pass args
                    i = 0
                    for item in res_total['buckets']:
                        # result.append({
                        #     'item_id': item['key'],
                        #     'item_name': item['buckets'][0]['key'],
                        #     'count': item[count_keyname],
                        # })
                        pid_value = item['key']
                        for h in item['buckets']:
                            if kwargs.get('ranking', False) \
                                or (page_index * reports_per_page <= i < (
                                    page_index + 1) * reports_per_page):
                                record_name = h['key'] if h['key'] != 'None'\
                                    else ''
                                # TODO: Set appropriate column names
                                result.append({
                                    'col1': pid_value,
                                    'col2': record_name,
                                    'col3': h[count_keyname],
                                })
                            i += 1
                            # total results
                            total_results += 1
                    if result:
                        result = cls.merge_items_results(result)
                        result = sorted(result, key=lambda k: k['col3'],
                                        reverse=True)
                elif unit == 'Host':
                    start_date_string = ''
                    end_date_string = ''
                    params = {'is_restricted': False}
                    if start_date is not None:
                        start_date_string = start_date.strftime('%Y-%m-%d 00:00:00')
                        params.update({'start_date': start_date_string})
                    if end_date is not None:
                        end_date_string = end_date.strftime('%Y-%m-%d 23:59:59')
                        params.update({'end_date': end_date_string})
                    if repository_id and repository_id != 'Root Index':
                        params.update({'index_list': index_list,
                                        'item_ids': item_ids,
                                        'agg_filter': {'pid_value': item_ids}})
                    else:
                        params.update({'index_list': None, 'item_ids': None})
                    res_total = query_total.run(**params)
                    i = 0
                    for item in res_total['buckets']:
                        for h in item['buckets']:
                            if page_index * \
                                    reports_per_page <= i < (page_index + 1) * reports_per_page:
                                hostname = h['key'] if h['key'] != 'None' else ''
                                result.append({
                                    'count': h[count_keyname],
                                    'start_date': start_date_string,
                                    'end_date': end_date_string,
                                    'domain': hostname,
                                    'ip': item['key']
                                })
                            i += 1
                            # total results
                            total_results += 1
                elif unit == 'User':
                    start_date_string = ''
                    end_date_string = ''
                    params = {}
                    if start_date is not None:
                        start_date_string = start_date.strftime('%Y-%m-%d 00:00:00')
                        params.update({'start_date': start_date_string})
                    if end_date is not None:
                        end_date_string = end_date.strftime('%Y-%m-%d 23:59:59')
                        params.update({'end_date': end_date_string})
                    # Limit size
                    params.update({'agg_size': kwargs.get('agg_size', 0)})
                    res_total = query_total.run(**params)
                    index_list = {}
                    for ip in res_total['buckets']:
                        for host in ip['buckets']:
                            for user in host['buckets']:
                                if not user['key'] in index_list:
                                    index_list[user['key']] = len(result)
                                    result.append({'user_id': user['key'],
                                                   'count': user['count']})
                                else:
                                    index = index_list[user['key']]
                                    result[index]['count'] += user['count']
                    if result:
                        result = sorted(result, key=lambda k: k['count'],
                                        reverse=True)
                else:
                    result = []
            except es_exceptions.NotFoundError as e:
                current_app.logger.error(e)
                traceback.print_exc()
                result = []
            except Exception as e:
                current_app.logger.error(e)
                traceback.print_exc()

        response = {
            'num_page': ceil(float(total_results) / reports_per_page),
            'page': page_index + 1,
            'data': result
        }
        return response

    @classmethod
    def merge_items_results(cls, results):
        """
        Merge items results after query.

        @param results:
        """
        new_result = []
        for i in results:
            index = -1
            for j in range(len(new_result)):
                if int(float(i['col1'])) == int(float(new_result[j]['col1'])):
                    index = j
            if index > -1:
                new_result[index]['col3'] += i['col3']
            else:
                new_result.append(i)
        return new_result if new_result else []


class QueryRankingHelper(object):
    """QueryRankingHelper helper class."""

    @classmethod
    def Calculation(cls, res, data_list):
        """Create response object."""
        for item in res['aggregations']['my_buckets']['buckets']:
            data = {
                'key': item['key'],
                'count': int(item['my_sum']['value'])
            }
            data_list.append(data)

    @classmethod
    def get(cls, **kwargs):
        """Get ranking data."""
        result = []

        try:
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            params = {
                'start_date': start_date,
                'end_date': end_date + 'T23:59:59',
                'agg_size': str(kwargs.get('agg_size', 10)),
                'event_type': kwargs.get('event_type', ''),
                'group_field': kwargs.get('group_field', ''),
                'count_field': kwargs.get('count_field', ''),
                'must_not': kwargs.get('must_not', ''),
                'new_items': False
            }
            all_query_cfg = current_stats.queries['get-ranking-data']
            all_query = all_query_cfg.query_class(**all_query_cfg.query_config)

            all_res = all_query.run(**params)

            cls.Calculation(all_res, result)

        except es_exceptions.NotFoundError as e:
            current_app.logger.debug(e)
        except Exception as e:
            current_app.logger.debug(e)

        return result

    @classmethod
    def get_new_items(cls, **kwargs):
        """Get new items."""
        result = []

        try:
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            params = {
                'start_date': start_date,
                'end_date': end_date,
                'agg_size': str(kwargs.get('agg_size', 10)),
                'must_not': kwargs.get('must_not', ''),
                'new_items': True
            }
            all_query_cfg = current_stats.queries['get-new-items-data']
            all_query = all_query_cfg.query_class(**all_query_cfg.query_config)

            all_res = all_query.run(**params)
            for r in all_res['hits']['hits']:
                if r.get('_source', {}).get('path'):
                    result.append(r['_source'])

        except es_exceptions.NotFoundError as e:
            current_app.logger.debug(e)
        except Exception as e:
            current_app.logger.debug(e)

        return result


class StatsCliUtil:
    """Stats CLI utilities."""

    EVENTS_TYPE = 0
    AGGREGATIONS_TYPE = 1

    def __init__(
        self, cli_type, stats_types, start_date=None,
        end_date=None, force=False, verbose=False
    ):
        """Stats CLI Utilities.

        :param cli_type:CLI type.
        :param stats_types:Stats type.
        :param start_date:Start date
        :param end_date:End date
        :param force:Force flag
        :param verbose:Verbose flag.
        """
        self.cli_type = cli_type
        self.stats_types = stats_types
        self.start_date = self.__parse_date(start_date)
        self.end_date = self.__parse_date(end_date, is_end_date=True)
        self.force = force
        self.verbose = verbose
        self.index_prefix = None
        self.affected_indices = None
        self.flush_indices = None
        self._search_index_prefix = current_app.config[
            'SEARCH_INDEX_PREFIX'].strip(
            '-')

        if self.cli_type == self.EVENTS_TYPE:
            self.index_prefix = current_app.config['STATS_EVENT_STRING']
        else:
            self.affected_indices = set()
            self.flush_indices = set()

    def delete_data(self, bookmark: bool = False) -> NoReturn:
        """Delete stats data in Elasticsearch.

        :param bookmark: set True if delete bookmark
        """
        for _index, _type in self.__prepare_es_indexes(delete=True):
            self.__cli_delete_es_index(_index, _type)
        if bookmark:
            if self.verbose:
                click.secho(
                    'Start deleting Bookmark data...',
                    fg='green'
                )
            _bookmark_index = "{}-stats-bookmarks".format(
                self._search_index_prefix)
            _bookmark_doc_type = get_doctype('aggregation-bookmark')
            self.__cli_delete_es_index(_bookmark_index, _bookmark_doc_type)

    def restore_data(self, bookmark: bool = False) -> NoReturn:
        """Restore stats data.

        :param bookmark: set True if restore bookmark
        """
        if self.cli_type == self.EVENTS_TYPE:
            data = self.__get_stats_data_from_db(StatsEvents)
        else:
            data = self.__get_stats_data_from_db(StatsAggregation)
        self.__cli_restore_es_data_from_db(data)

        if bookmark:
            if self.verbose:
                click.secho(
                    'Start to restore of Bookmark data '
                    'from the Database to Elasticsearch...',
                    fg='green'
                )
            bookmark_data = self.__get_stats_data_from_db(StatsBookmark,
                                                          bookmark)
            self.__cli_restore_es_data_from_db(bookmark_data)

    def __prepare_es_indexes(
        self, bookmark_index=False, delete=False
    ):
        """Prepare ElasticSearch index data.

        :param bookmark_index: set True if prepare the index for the bookmark
        :param delete: set True if prepare the index for the delete data feature
        """
        search_index_prefix = current_app.config['SEARCH_INDEX_PREFIX'].strip(
            '-')
        for _type in self.stats_types:
            if not _type:
                continue
            prefix = "stats-{}"
            search_type = prefix.format(_type)
            # In case prepare indexes for the stats bookmark
            if bookmark_index:
                _index = "{}-stats-bookmarks".format(search_index_prefix)
                _doc_type = get_doctype('aggregation-bookmark')
            # In case prepare indexes for the stats event
            elif self.index_prefix:
                _index = '{0}-{1}-{2}'.format(
                    search_index_prefix,
                    self.index_prefix,
                    search_type
                )
                _doc_type = search_type
            else:
                _index = '{0}-{1}'.format(search_index_prefix, search_type)
                _doc_type = '{0}-{1}-aggregation'.format(_type, "day")
            if not delete:
                yield _index
            else:
                yield _index, _doc_type

    def __build_es_data(self, data_list: list) -> Generator:
        """Build Elasticsearch data.

        :param data_list: Stats data from DB.
        """
        for data in data_list:
            if self.flush_indices is not None:
                self.flush_indices.add(data.index)
            es_data = dict(
                _id=data.source_id,
                _index=data.index,
                _type=data.type,
                _source=data.source,
            )
            if self.cli_type == self.EVENTS_TYPE:
                es_data['_op_type'] = "index"
            yield es_data

    def __get_data_from_db_by_stats_type(self, data_model, bookmark):
        rtn_data = []
        if not bookmark:
            indexes = self.__prepare_es_indexes(bookmark)
            for _index in indexes:
                data = data_model.get_by_index(_index, self.start_date,
                                               self.end_date)
                if data:
                    rtn_data.extend(data)
        else:
            for _type in self.stats_types:
                data = data_model.get_by_source_id(_type)
                if data:
                    rtn_data.extend(data)
        return rtn_data

    def __get_stats_data_from_db(
        self,
        data_model, bookmark: bool = False
    ) -> Generator:
        """Get bookmark data from database.

        :param data_model: Data model
        :param bookmark: set True if get stats data for the bookmark
        :return:
        """
        if self.stats_types:
            rtn_data = self.__get_data_from_db_by_stats_type(data_model,
                                                             bookmark)
        else:
            rtn_data = data_model.get_all(self.start_date, self.end_date)
        return self.__build_es_data(rtn_data)

    def __show_message(self, index_name, success, failed):
        """Show message.

        :param index_name:Elasticsearch index name.
        :param success:Success message.
        :param failed:failed message.
        """
        if index_name is not None:
            click.secho('====== {} ======'.format(str(index_name)), fg='green')
        click.secho('Success: {}'.format(str(success)), fg='green')
        if self.force:
            click.secho('Failed: {}'.format(str(failed)), fg='yellow')
        else:
            if len(failed) == 0:
                click.secho('Error: 0', fg='red')
            else:
                click.secho('Error:', fg='red')
                for err in failed:
                    click.secho(str(err), fg='red')

    def __cli_restore_es_data_from_db(
        self,
        restore_data: Generator,
        flush_indices: set = None
    ) -> NoReturn:
        """Restore ElasticSearch data based on Database.

        :param restore_data:
        :param flush_indices:
        """
        if restore_data:
            success, failed = bulk(
                current_search_client,
                restore_data,
                stats_only=self.force,
                chunk_size=50
            )
            if flush_indices:
                current_search_client.indices.flush(
                    index=','.join(flush_indices),
                    wait_if_ongoing=True
                )
            if self.verbose:
                self.__show_message(None, success, failed)
        else:
            if self.verbose:
                click.secho('There is no stats data from Database.',
                            fg='yellow')

    def __cli_delete_es_index(self, _index: str, doc_type: str) -> NoReturn:
        """Delete ES index.

        :param _index: Elasticsearch index.
        :param doc_type: document type.
        """
        query = Search(
            using=current_search_client,
            index=_index,
            doc_type=doc_type,
        ).params(raise_on_error=False, ignore=[400, 404])
        range_args = {}
        if self.start_date:
            range_args['gte'] = self.start_date
        if self.end_date:
            range_args['lte'] = self.end_date
        if range_args:
            query = query.filter('range', timestamp=range_args)

        def _delete_actions():
            for doc in query.scan():
                if self.affected_indices is not None:
                    self.affected_indices.add(doc.meta.index)
                yield dict(_index=doc.meta.index,
                           _op_type='delete',
                           _id=doc.meta.id,
                           _type=doc.meta.doc_type)
            if self.affected_indices is not None:
                current_search_client.indices.flush(
                    index=','.join(self.affected_indices), wait_if_ongoing=True)

        success, failed = bulk(
            current_search_client,
            _delete_actions(),
            stats_only=self.force,
            refresh=True
        )
        if self.verbose:
            self.__show_message(_index, success, failed)

    @staticmethod
    def __parse_date(
        _date: str, is_end_date: bool = False
    ) -> Union[datetime, None]:
        """Parse date.

        :param _date: a string date
        :param is_end_date: True if the end date.
        :return:
        """
        def _parse_day():
            _year, _month, _day = _date.split("-")
            rtn = datetime(year=int(_year), month=int(_month), day=int(_day))
            if is_end_date:
                rtn = rtn.replace(hour=23, minute=59, second=59)
            return rtn

        def _parse_month():
            _year, _month = _date.split("-")
            _start, _end = calendar.monthrange(int(_year), int(_month))
            if not is_end_date:
                _day = _start
            else:
                _day = _end
            rtn = datetime(year=int(_year), month=int(_month), day=int(_day))
            if is_end_date:
                rtn = rtn.replace(hour=23, minute=59, second=59)
            return rtn

        def _parse_year():
            if not is_end_date:
                rtn = datetime(year=int(_date), month=1, day=1)
            else:
                rtn = datetime(year=int(_date), month=12, day=31, hour=23,
                               minute=59, second=59)
            return rtn

        if not isinstance(_date, str):
            return
        day = r"^\d{4}-\d{1,2}-\d{1,2}$"
        month = r"^\d{4}-\d{1,2}$"
        year = r"^\d{4}$"
        date = _date
        if re.match(day, _date):
            date = _parse_day()
        elif re.match(month, _date):
            date = _parse_month()
        elif re.match(year, _date):
            date = _parse_year()
        return date
