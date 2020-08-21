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
import os
from base64 import b64encode
from datetime import datetime, timedelta
from math import ceil

import click
import six
from dateutil import parser
from elasticsearch.helpers import bulk
from elasticsearch_dsl import Search
from flask import current_app, request, session
from flask_login import current_user
from geolite2 import geolite2
from invenio_cache import current_cache
from invenio_search import current_search_client
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
    reader = geolite2.reader()
    ip_data = reader.get(ip) or {}
    return ip_data.get('country', {}).get('iso_code')


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
        ip_address=request.remote_addr,
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
            index=index, body=aggs_query)['aggregations']

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
        order = True if agg_sort['order'] is 'desc' else False
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


def prepare_es_indexes(
    index_types,
    index_prefix=None,
    index_suffix=None,
    bookmark_index=False
):
    """Prepare event index data.

    :param index_types:
    :param index_prefix:
    :param index_suffix:
    :param bookmark_index:
    """
    search_index_prefix = current_app.config['SEARCH_INDEX_PREFIX'].strip('-')
    for event_type in index_types:
        if not event_type:
            continue

        # In case prepare indexes for the stats bookmark
        if bookmark_index:
            prefix = "stats-bookmark-{}"
        else:
            prefix = "stats-{}"

        event_type = prefix.format(event_type)

        # In case prepare indexes for the stats event
        if index_prefix:
            event_index = '{0}-{1}-{2}'.format(search_index_prefix,
                                               index_prefix,
                                               event_type)
        else:
            event_index = '{0}-{1}'.format(search_index_prefix, event_type)

        if index_suffix:
            event_index = '{0}-{1}'.format(event_index, index_suffix)
        yield event_index


def __build_event_es_data(events_data):
    """Build event data.

    :param events_data:
    """
    for data in events_data:
        yield dict(
            _id=data.source_id,
            _op_type=data.op_type,
            _index=data.index,
            _type=data.type,
            _source=data.source,
        )


def __build_aggregation_es_data(aggregation_data, flush_indices):
    """Build aggregation data.

    :param aggregation_data:
    """
    for data in aggregation_data:
        flush_indices.add(data.index)
        yield dict(
            _id=data.source_id,
            _index=data.index,
            _type=data.type,
            _source=data.source,
        )


def __build_bookmark_es_data(bookmark_data):
    """Build bookmark data.

    :param bookmark_data:
    """
    for data in bookmark_data:
        yield dict(
            _id=data.source_id,
            _index=data.index,
            _type=data.type,
            _source=data.source,
        )


def get_event_data_from_db(event_types, index_prefix, index_suffix):
    """Get event data from database.

    :param event_types:
    :param index_prefix:
    :param index_suffix:
    :return:
    """
    if index_suffix:
        events_index = prepare_es_indexes(
            event_types, index_prefix, index_suffix
        )
        rtn_data = []
        for event_index in events_index:
            data = StatsEvents.get_by_index(event_index)
            if data:
                rtn_data.extend(data)
    else:
        rtn_data = StatsEvents.get_all()
    return __build_event_es_data(rtn_data)


def get_aggregation_data_from_db(types, index_suffix, flush_indices):
    """Get aggregation data from database.

    :param types:
    :param index_suffix:
    :param flush_indices:
    :return:
    """
    if index_suffix:
        indexes = prepare_es_indexes(
            types, None, index_suffix
        )
        rtn_data = []
        for _index in indexes:
            data = StatsAggregation.get_by_index(_index)
            if data:
                rtn_data.extend(data)
    else:
        rtn_data = StatsAggregation.get_all()
    return __build_aggregation_es_data(rtn_data, flush_indices)


def get_bookmark_data_from_db(types, index_suffix, restore_bookmark):
    """Get bookmark data from database.

    :param types:
    :param index_suffix:
    :param restore_bookmark:
    :return:
    """
    if index_suffix:
        indexes = prepare_es_indexes(
            types, None, index_suffix, restore_bookmark
        )
        rtn_data = []
        for _index in indexes:
            data = StatsBookmark.get_by_index(_index)
            if data:
                rtn_data.extend(data)
    else:
        rtn_data = StatsBookmark.get_all()

    return __build_bookmark_es_data(rtn_data)


def cli_restore_es_data_from_db(
    restore_data,
    force,
    verbose,
    flush_indices=None
):
    """Restore ElasticSearch data based on Database.

    :param restore_data:
    :param force:
    :param verbose:
    :param flush_indices:
    """
    if restore_data:
        success, failed = bulk(
            current_search_client,
            restore_data,
            stats_only=force,
            chunk_size=50
        )
        if flush_indices:
            current_search_client.indices.flush(
                index=','.join(flush_indices),
                wait_if_ongoing=True
            )
        if verbose:
            click.secho('Success: {}'.format(str(success)), fg='green')
            if force:
                click.secho('Failed: {}'.format(str(failed)), fg='yellow')
            else:
                if len(failed) == 0:
                    click.secho('Error: 0', fg='red')
                else:
                    click.secho('Error: 0', fg='red')
                    for err in failed:
                        click.secho(str(err), fg='red')
    else:
        if verbose:
            click.secho('There is no stats data from Database.', fg='yellow')


def cli_delete_es_index(_index, force, verbose):
    """Delete ES index.

    :param _index:
    :param force:
    :param verbose:
    """
    result = current_search_client.indices.delete(
        index=_index,
        ignore=[400, 404] if force else [],
    )
    if verbose:
        if result and result.get('acknowledged'):
            click.secho("The {} is deleted".format(_index), fg='green')


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
        for file in res['buckets']:
            for index in file['buckets']:
                data = {}
                data['group_counts'] = {}  # Keep track of downloads per group
                data['file_key'] = file['key']
                data['index_list'] = index['key']
                data['total'] = index['value']
                data['admin'] = 0
                data['reg'] = 0
                data['login'] = 0
                data['no_login'] = 0
                data['site_license'] = 0
                for user in index['buckets']:
                    for license in user['buckets']:
                        if license['key'] == 1:
                            data['site_license'] += license['value']
                            break

                    userrole = user['key']
                    count = user['value']

                    if userrole == 'guest':
                        data['no_login'] += count
                    elif userrole == 'Contributor':
                        data['reg'] += count
                        data['login'] += count
                    elif 'Administrator' in userrole:
                        data['admin'] += count
                        data['login'] += count
                    else:
                        data['login'] += count

                    # Get groups counts
                    if 'field' in user['buckets'][0]:
                        for group_acc in user['buckets'][0]['buckets']:
                            group_list = group_acc['key']
                            data['group_counts'] = cls.calc_per_group_counts(
                                group_list, data['group_counts'], group_acc['value'])

                    # Keep track of groups seen
                    all_groups.update(data['group_counts'].keys())
                data_list.append(data)

    @classmethod
    def calc_file_per_using_report(cls, res, data_list):
        """Create response object for file_per_using_report."""
        # file-download
        for item in res['get-file-download-per-user-report']['buckets']:
            data = {}
            data['cur_user_id'] = item['key']
            data['total_download'] = item['value']
            data_list.update({item['key']: data})
        # file-preview
        for item in res['get-file-preview-per-user-report']['buckets']:
            data = {}
            data['cur_user_id'] = item['key']
            data['total_preview'] = item['value']
            if data_list.get(item['key']):
                data_list[item['key']].update(data)
            else:
                data_list.update({item['key']: data})

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
        result = {}
        all_list = []
        open_access_list = []
        all_groups = set()

        event = kwargs.get('event')
        year = kwargs.get('year')
        month = kwargs.get('month')

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
            current_app.logger.debug(e)

        result['date'] = query_month
        result['all'] = all_list
        result['open_access'] = open_access_list
        result['all_groups'] = list(all_groups)
        return result

    @classmethod
    def get_file_per_using_report(cls, **kwargs):
        """Get File Using Per User report."""
        result = {}
        all_list = {}
        all_res = {}

        year = kwargs.get('year')
        month = kwargs.get('month')

        try:
            query_month = str(year) + '-' + str(month).zfill(2)
            _, lastday = calendar.monthrange(year, month)
            params = {'start_date': query_month + '-01',
                      'end_date': query_month + '-' + str(lastday).zfill(2)
                      + 'T23:59:59'}

            all_query_name = ['get-file-download-per-user-report',
                              'get-file-preview-per-user-report']
            for query in all_query_name:
                all_query_cfg = current_stats.queries[query]
                all_query = all_query_cfg.\
                    query_class(**all_query_cfg.query_config)
                all_res[query] = all_query.run(**params)
            cls.Calculation(all_res, all_list)

        except Exception as e:
            current_app.logger.debug(e)

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

        try:
            if not start_date or not end_date:
                start_date, end_date = get_start_end_date(year, month)
                result['date'] = str(year) + '-' + str(month).zfill(2)
            params = {'start_date': start_date,
                      'end_date': end_date + 'T23:59:59',
                      'agg_size': kwargs.get('agg_size', 0),
                      'agg_sort': kwargs.get('agg_sort', {'value': 'desc'}),
                      'agg_filter': kwargs.get('agg_filter', None)}

            # Run query
            keyword_query_cfg = current_stats.queries['get-search-report']
            keyword_query = keyword_query_cfg.query_class(
                **keyword_query_cfg.query_config)
            raw_result = keyword_query.run(**params)

            all = []
            for report in raw_result['buckets']:
                current_report = {}
                current_report['search_key'] = report['key']
                current_report['count'] = report['value']
                all.append(current_report)
            result['all'] = all

        except Exception as e:
            current_app.logger.debug(e)
            return {}

        return result


class QueryCommonReportsHelper(object):
    """CommonReports helper class."""

    @classmethod
    def get_common_params(cls, **kwargs):
        """Get common params."""
        year = kwargs.get('year')
        month = kwargs.get('month')
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
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
                for item in res['top-view-total-per-host']['buckets']:
                    for hostaccess in item['buckets']:
                        data = {}
                        data['host'] = hostaccess['key']
                        data['ip'] = item['key']
                        data['count'] = hostaccess['value']
                        data_list.update({item['key']: data})
            elif 'top-view-total' in res:
                for item in res['top-view-total']['buckets']:
                    data_list.update({'count': item['value']})
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
                        if i['key'] == '':
                            other_list[k] += i['value']
                        else:
                            site_license_list[k] += i['value']
                            if i['key'] in mapper:
                                institution_name_list[mapper[i['key']]
                                                      ][k] = i['value']
                            else:
                                mapper[i['key']] = len(institution_name_list)
                                data = {}
                                data['name'] = i['key']
                                data[k] = i['value']
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
    first_level_field = 'record_index_list.index_id'
    second_level_field = 'record_index_list.index_name'

    @classmethod
    def get_nested_agg(cls, start_date, end_date):
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
        agg_query.aggs.bucket(cls.nested_path, 'nested',
                              path=cls.nested_path) \
            .bucket(cls.first_level_field, 'terms',
                    field=cls.first_level_field,
                    size=current_app.config['STATS_ES_INTEGER_MAX_VALUE']) \
            .bucket(cls.second_level_field, 'terms',
                    field=cls.second_level_field,
                    size=current_app.config['STATS_ES_INTEGER_MAX_VALUE'])
        return agg_query.execute().to_dict()

    @classmethod
    def parse_bucket_response(cls, res, date):
        """Parse raw aggregation response."""
        aggs = res['aggregations'][cls.nested_path]
        result = {'date': date, 'all': [], 'total': aggs['doc_count']}
        for id_agg in aggs[cls.first_level_field]['buckets']:
            for name_agg in id_agg[cls.second_level_field]['buckets']:
                result['all'].append({'index_name': name_agg['key'],
                                      'view_count': id_agg['doc_count']})
        return result

    @classmethod
    def get(cls, **kwargs):
        """Get record view per index report.

        Nested aggregations are currently unsupported so manually aggregating.
        """
        result = {}
        year = kwargs.get('year')
        month = kwargs.get('month')

        try:
            query_month = str(year) + '-' + str(month).zfill(2)
            _, lastday = calendar.monthrange(year, month)
            start_date = query_month + '-01'
            end_date = query_month + '-' + str(lastday).zfill(2) + 'T23:59:59'
            raw_result = cls.get_nested_agg(start_date, end_date)
            result = cls.parse_bucket_response(raw_result, query_month)

        except Exception as e:
            current_app.logger.debug(e)
            return {}

        return result


class QueryRecordViewReportHelper(object):
    """RecordViewReport helper class."""

    @classmethod
    def Calculation(cls, res, data_list):
        """Create response object."""
        for item in res['buckets']:
            for record in item['buckets']:
                data = {}
                data['record_id'] = item['key']
                data['index_names'] = record['key']
                data['total_all'] = record['value']
                data['total_not_login'] = 0
                for user in record['buckets']:
                    for pid in user['buckets']:
                        data['pid_value'] = pid['key']
                        for title in pid['buckets']:
                            data['record_name'] = title['key']
                    if user['key'] == 'guest':
                        data['total_not_login'] += user['value']
                data_list.append(data)

    @classmethod
    def get(cls, **kwargs):
        """Get record view report."""
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
            all_query_cfg = current_stats.queries['get-record-view-report']
            all_query = all_query_cfg.query_class(**all_query_cfg.query_config)
            # Limit size
            params.update({'agg_size': kwargs.get('agg_size', 0)})
            params.update({'agg_sort': kwargs.get('agg_sort',
                                                  {'value': 'desc'})})
            all_res = all_query.run(**params)
            cls.Calculation(all_res, all_list)

        except Exception as e:
            current_app.logger.debug(e)

        result['date'] = query_date
        result['all'] = all_list

        return result


class QueryItemRegReportHelper(object):
    """Helper for providing item registration report."""

    @classmethod
    def get(cls, **kwargs):
        """Get item registration report."""
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

        result = []
        if empty_date_flg or end_date >= start_date:
            try:
                if unit == 'Day':
                    if empty_date_flg:
                        params = {'interval': 'day'}
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
                            if page_index * \
                                    reports_per_page <= i < (page_index + 1) * reports_per_page:
                                start_date_string = d.strftime('%Y-%m-%d')
                                end_date_string = d.strftime('%Y-%m-%d')
                                params = {'interval': 'day',
                                          'start_date': start_date_string,
                                          'end_date': end_date_string,
                                          'is_restricted': False
                                          }
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
                                start_date_string = d.strftime('%Y-%m-%d')
                                d1 = d + delta - delta1
                                if d1 > end_date:
                                    d1 = end_date
                                end_date_string = d1.strftime('%Y-%m-%d')
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
                                res_total = query_total.run(**params)
                                temp['count'] = res_total[count_keyname]
                                result.append(temp)

                            d += delta
                elif unit == 'Year':
                    if empty_date_flg:
                        params = {'interval': 'year', 'is_restricted': False}
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
                                start_date_string = '{}-01-01'.format(
                                    start_year + i)
                                end_date_string = '{}-12-31'.format(
                                    start_year + i)
                                params = {'interval': 'year',
                                          'start_date': start_date_string,
                                          'end_date': end_date_string,
                                          'is_restricted': False
                                          }
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
                        start_date_string = start_date.strftime('%Y-%m-%d')
                        params.update({'start_date': start_date_string})
                    if end_date is not None:
                        end_date_string = end_date.strftime('%Y-%m-%d')
                        params.update({'end_date': end_date_string})
                    # Limit size
                    params.update({'agg_size': kwargs.get('agg_size', 0)})
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
                            if page_index * \
                                    reports_per_page <= i < (page_index + 1) * reports_per_page:
                                record_name = h['key'] if h['key'] != 'None' else ''

                                # TODO: Set appropriate column names
                                result.append({
                                    'col1': pid_value,
                                    'col2': record_name,
                                    'col3': h[count_keyname],
                                })
                            i += 1
                            # total results
                            total_results += 1

                elif unit == 'Host':
                    start_date_string = ''
                    end_date_string = ''
                    params = {'is_restricted': False}
                    if start_date is not None:
                        start_date_string = start_date.strftime('%Y-%m-%d')
                        params.update({'start_date': start_date_string})
                    if end_date is not None:
                        end_date_string = end_date.strftime('%Y-%m-%d')
                        params.update({'end_date': end_date_string})
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
                        start_date_string = start_date.strftime('%Y-%m-%d')
                        params.update({'start_date': start_date_string})
                    if end_date is not None:
                        end_date_string = end_date.strftime('%Y-%m-%d')
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
                else:
                    result = []
            except Exception as e:
                current_app.logger.debug(e)

        response = {
            'num_page': ceil(float(total_results) / reports_per_page),
            'page': page_index + 1,
            'data': result
        }
        return response
