# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Query processing classes."""

import json
from datetime import datetime

import pickle
import dateutil.parser
import six
from elasticsearch_dsl import Search
from elasticsearch_dsl.aggs import A
from flask import current_app
from invenio_search import current_search_client

from .errors import InvalidRequestInputError
from .utils import chunk_list


class ESQuery(object):
    """Elasticsearch query."""

    def __init__(self, query_name, doc_type, index, client=None,
                 *args, **kwargs):
        """Constructor.

        :param doc_type: queried document type.
        :param index: queried index.
        :param client: elasticsearch client used to query.
        """
        super(ESQuery, self).__init__()
        self.index = index
        self.client = client or current_search_client
        self.query_name = query_name
        self.doc_type = doc_type

    def extract_date(self, date):
        """Extract date from string if necessary.

        :returns: the extracted date.
        """
        if isinstance(date, six.string_types):
            try:
                date = dateutil.parser.parse(date)
            except ValueError:
                raise ValueError(
                    'Invalid date format for statistic {}.'.format(self.query_name)
                )
        if not isinstance(date, datetime):
            raise TypeError(
                'Invalid date type for statistic {}.'.format(self.query_name)
            )
        return date

    def run(self, *args, **kwargs):
        """Run the query."""
        raise NotImplementedError()


class ESDateHistogramQuery(ESQuery):
    """Elasticsearch date histogram query."""

    allowed_intervals = ['year', 'quarter', 'month', 'week', 'day']
    """Allowed intervals for the histogram aggregation."""

    def __init__(self, time_field='timestamp', copy_fields=None,
                 query_modifiers=None, required_filters=None,
                 metric_fields=None, *args, **kwargs):
        """Constructor.

        :param time_field: name of the timestamp field.
        :param copy_fields: list of fields to copy from the top hit document
            into the resulting aggregation.
        :param query_modifiers: List of functions accepting a ``query`` and
            ``**kwargs`` (same as provided to the ``run`` method), that will
            be applied to the aggregation query.
        :param required_filters: Dict of "mandatory query parameter" ->
            "filtered field".
        :param metric_fields: Dict of "destination field" ->
            tuple("metric type", "source field", "metric_options").
        """
        super(ESDateHistogramQuery, self).__init__(*args, **kwargs)
        self.time_field = time_field
        self.copy_fields = copy_fields or {}
        self.query_modifiers = query_modifiers or []
        self.required_filters = required_filters or {}
        self.metric_fields = metric_fields or {'value': ('sum', 'count', {})}
        self.allowed_metrics = {
            'cardinality', 'min', 'max', 'avg', 'sum', 'extended_stats',
            'geo_centroid', 'percentiles', 'stats'}
        if any(v not in self.allowed_metrics
               for k, (v, _, _) in (self.metric_fields or {}).items()):
            raise(ValueError('Metric type should be one of [{}]'
                             .format(', '.join(self.allowed_metrics))))

    def validate_arguments(self, interval, start_date, end_date, **kwargs):
        """Validate query arguments."""
        if interval not in self.allowed_intervals:
            raise InvalidRequestInputError(
                'Invalid aggregation time interval for statistic {}.'.format(self.query_name)
            )
        if set(kwargs) < set(self.required_filters):
            raise InvalidRequestInputError(
                'Missing one of the required parameters {0} in '
                'query {1}'.format(set(self.required_filters.keys()),
                                   self.query_name)
            )

    def build_query(self, interval, start_date, end_date, **kwargs):
        """Build the elasticsearch query."""
        agg_query = Search(using=self.client,
                           index=self.index,
                           doc_type=self.doc_type)[0:0]
        if start_date is not None or end_date is not None:
            time_range = {}
            if start_date is not None:
                time_range['gte'] = start_date.isoformat()
            if end_date is not None:
                time_range['lte'] = end_date.isoformat()
            agg_query = agg_query.filter(
                'range',
                **{self.time_field: time_range})

        for modifier in self.query_modifiers:
            agg_query = modifier(agg_query, **kwargs)

        try:
            base_agg = agg_query.aggs.bucket(
                'histogram',
                'date_histogram',
                field=self.time_field,
                interval=interval,
                time_zone=str(current_app.config['STATS_WEKO_DEFAULT_TIMEZONE']())
            )
        except AttributeError:
            base_agg = agg_query.aggs.bucket(
                'histogram',
                'date_histogram',
                field=self.time_field,
                interval=interval,
                time_zone=current_app.config.get('BABEL_DEFAULT_TIMEZONE', 'Asia/Tokyo')
            )

        for destination, (metric, field, opts) in self.metric_fields.items():
            base_agg.metric(destination, metric, field=field, **opts)

        if self.copy_fields:
            base_agg.metric(
                'top_hit', 'top_hits', size=1, sort={'timestamp': 'desc'}
            )

        for query_param, filtered_field in self.required_filters.items():
            if query_param in kwargs:
                value = kwargs[query_param]
                if value is None:
                    continue
                if isinstance(value, list):
                    max_clause_count = current_app.config.get('OAISERVER_ES_MAX_CLAUSE_COUNT', 1024)
                    if len(value) > max_clause_count:
                        should_clauses = []
                        for i in range(0, len(value), max_clause_count):
                            should_clauses.append({'terms': {filtered_field: value[i:i + max_clause_count]}})
                        agg_query = agg_query.filter('bool', should=should_clauses)
                    else:
                        agg_query = agg_query.filter('terms', **{filtered_field: value})
                else:
                    agg_query = agg_query.filter('term', **{filtered_field: value})

        return agg_query

    def process_query_result(self, query_result, interval,
                             start_date, end_date):
        """Build the result using the query result."""
        def build_buckets(agg):
            """Build recursively result buckets."""
            bucket_result = dict(
                key=agg['key'],
                date=agg['key_as_string'],
            )
            for metric in self.metric_fields:
                bucket_result[metric] = agg[metric]['value']
            if self.copy_fields and agg['top_hit']['hits']['hits']:
                doc = agg['top_hit']['hits']['hits'][0]['_source']
                for destination, source in self.copy_fields.items():
                    if isinstance(source, six.string_types):
                        bucket_result[destination] = doc[source]
                    else:
                        bucket_result[destination] = source(bucket_result, doc)
            return bucket_result

        # Add copy_fields
        buckets = query_result['aggregations']['histogram']['buckets']
        return dict(
            interval=interval,
            key_type='date',
            start_date=start_date.isoformat() if start_date else None,
            end_date=end_date.isoformat() if end_date else None,
            buckets=[build_buckets(b) for b in buckets]
        )

    def run(self, interval='day', start_date=None,
            end_date=None, **kwargs):
        """Run the query."""
        start_date = self.extract_date(start_date) if start_date else None
        end_date = self.extract_date(end_date) if end_date else None
        self.validate_arguments(interval, start_date, end_date, **kwargs)

        agg_query = self.build_query(interval, start_date,
                                     end_date, **kwargs)

        query_result = agg_query.execute().to_dict()
        res = self.process_query_result(query_result, interval,
                                        start_date, end_date)
        return res


class ESTermsQuery(ESQuery):
    """Elasticsearch sum query."""

    def __init__(self, time_field='timestamp', copy_fields=None,
                 query_modifiers=None, required_filters=None,
                 aggregated_fields=None, metric_fields=None,
                 group_fields=None, *args, **kwargs):
        """Constructor.

        :param time_field: name of the timestamp field.
        :param copy_fields: list of fields to copy from the top hit document
            into the resulting aggregation.
        :param query_modifiers: List of functions accepting a ``query`` and
            ``**kwargs`` (same as provided to the ``run`` method), that will
            be applied to the aggregation query.
        :param required_filters: Dict of "mandatory query parameter" ->
            "filtered field".
        :param aggregated_fields: List of fields which will be used in the
            terms aggregations.
        :param metric_fields: Dict of "destination field" ->
            tuple("metric type", "source field").
        :param group_fields: group fields.
        """
        super(ESTermsQuery, self).__init__(*args, **kwargs)
        self.time_field = time_field
        self.copy_fields = copy_fields or {}
        self.query_modifiers = query_modifiers or []
        self.required_filters = required_filters or {}
        self.aggregated_fields = aggregated_fields or []
        self.metric_fields = metric_fields or {'value': ('sum', 'count', {})}
        self.group_fields = group_fields or []

    def validate_arguments(self, start_date, end_date, **kwargs):
        """Validate query arguments."""
        if set(kwargs) < set(self.required_filters):
            raise InvalidRequestInputError(
                'Missing one of the required parameters {0} in '
                'query {1}'.format(set(self.required_filters.keys()),
                                   self.query_name)
            )

    def build_query(self, start_date, end_date, **kwargs):
        """Build the elasticsearch query."""
        agg_query = Search(using=self.client,
                           index=self.index,
                           doc_type=self.doc_type)[0:0]
        if start_date or end_date:
            time_range = {}
            if start_date:
                time_range['gte'] = start_date.isoformat()
            if end_date:
                time_range['lte'] = end_date.isoformat()
            try:
                time_range['time_zone'] = str(
                    current_app.config['STATS_WEKO_DEFAULT_TIMEZONE']())
            except AttributeError:
                time_range['time_zone'] = current_app.config.get('BABEL_DEFAULT_TIMEZONE', 'Asia/Tokyo')
            agg_query = agg_query.filter(
                'range',
                **{self.time_field: time_range})

        for modifier in self.query_modifiers:
            agg_query = modifier(agg_query, **kwargs)

        base_agg = agg_query.aggs

        def _apply_metric_aggs(agg):
            for dst, (metric, field, opts) in self.metric_fields.items():
                agg.metric(dst, metric, field=field, **opts)

        size = kwargs.get('agg_size') if kwargs.get('agg_size') else \
            current_app.config['STATS_ES_INTEGER_MAX_VALUE']
        _apply_metric_aggs(base_agg)
        if self.group_fields:
            sources = []
            for f in self.group_fields:
                sources.append({f: A('terms', field=f)})
            if kwargs.get('after_key'):
                base_agg.bucket(
                    'my_buckets', 'composite', size=size, sources=sources, after=kwargs.get('after_key')
                )
            else:
                base_agg.bucket(
                    'my_buckets', 'composite', size=size, sources=sources
                )
        else:
            if self.aggregated_fields:
                cur_agg = base_agg
                for term in self.aggregated_fields:
                    cur_agg = cur_agg.bucket(term, 'terms', field=term, size=size)
                    _apply_metric_aggs(cur_agg)

        if self.copy_fields:
            base_agg.metric(
                'top_hit', 'top_hits', size=1, sort={'timestamp': 'desc'}
            )

        for query_param, filtered_field in self.required_filters.items():
            if query_param in kwargs:
                value = kwargs[query_param]
                if value is None:
                    continue
                if isinstance(value, list):
                    max_clause_count = current_app.config.get('OAISERVER_ES_MAX_CLAUSE_COUNT', 1024)
                    if len(value) > max_clause_count:
                        should_clauses = []
                        for i in range(0, len(value), max_clause_count):
                            should_clauses.append({'terms': {filtered_field: value[i:i + max_clause_count]}})
                        agg_query = agg_query.filter('bool', should=should_clauses)
                    else:
                        agg_query = agg_query.filter('terms', **{filtered_field: value})
                else:
                    agg_query = agg_query.filter('term', **{filtered_field: value})
        return agg_query

    def process_query_result(self, query_result, start_date, end_date):
        """Build the result using the query result."""
        def build_buckets(agg, fields, bucket_result):
            """Build recursively result buckets."""
            # Add metric results for current bucket
            for metric in self.metric_fields:
                bucket_result[metric] = agg[metric].get('value')
            if self.group_fields:
                temp_data = {}
                count = 0
                for item in agg['buckets']:
                    key_str = ''
                    for key in self.group_fields:
                        if key != 'count':
                            key_str += '{}_'.format(item['key'][key])
                        else:
                            count = item['key']['count'] * item['doc_count']
                    if key_str in temp_data:
                        temp_data[key_str]['count'] += count
                    else:
                        temp_data[key_str] = item['key']
                        temp_data[key_str]['count'] = count
                bucket_result.update(dict(
                    buckets=[temp_data[key_str] for key_str in temp_data.keys()]
                ))
            elif fields:
                current_level = fields[0]
                bucket_result.update(dict(
                    type='bucket',
                    field=current_level,
                    key_type='terms',
                    buckets=[build_buckets(b, fields[1:], dict(key=b['key']))
                             for b in agg[current_level]['buckets']]
                ))
            return bucket_result

        # Add copy_fields
        aggs = query_result['aggregations']
        result = dict(
            start_date=start_date.isoformat() if start_date else None,
            end_date=end_date.isoformat() if end_date else None,
        )
        if self.copy_fields and aggs['top_hit']['hits']['hits']:
            doc = aggs['top_hit']['hits']['hits'][0]['_source']
            for destination, source in self.copy_fields.items():
                if isinstance(source, six.string_types):
                    result[destination] = doc[source]
                else:
                    result[destination] = source(result, doc)

        return build_buckets(aggs, self.aggregated_fields, result)

    def run(self, start_date=None, end_date=None, **kwargs):
        """Run the query."""
        start_date = self.extract_date(start_date) if start_date else None
        end_date = self.extract_date(end_date) if end_date else None
        self.validate_arguments(start_date, end_date, **kwargs)
        if self.group_fields:
            first_search = True
            after_key = None
            total = 1
            count = 0
            query_result = {}
            res_list = []
            res_count = {}
            while count < total and (after_key or first_search):
                agg_query = self.build_query(start_date, end_date, after_key=after_key, **kwargs)
                current_app.logger.debug('agg_query: {}'.format(agg_query.to_dict()))
                temp_res = agg_query.execute().to_dict()
                if 'after_key' in temp_res['aggregations']['my_buckets']:
                    after_key = temp_res['aggregations']['my_buckets']['after_key']
                else:
                    after_key = None
                if first_search:
                    first_search = False
                    total = temp_res['hits']['total']
                    for metric in self.metric_fields:
                        res_count[metric] = temp_res['aggregations'][metric]
                count += len(temp_res['aggregations']['my_buckets']['buckets'])
                res_list += pickle.loads(pickle.dumps(temp_res['aggregations']['my_buckets']['buckets'], -1))
            query_result['aggregations'] = {'buckets': res_list}
            for metric in self.metric_fields:
                query_result['aggregations'][metric] = res_count[metric]
        else:
            agg_query = self.build_query(start_date, end_date, **kwargs)
            current_app.logger.debug(agg_query.to_dict())
            query_result = agg_query.execute().to_dict()
        res = self.process_query_result(query_result, start_date, end_date)
        return res


class ESWekoFileStatsQuery(ESTermsQuery):
    """Weko ES Query for File Stats."""

    def __init__(self, main_fields=None, main_query=None, *args, **kwargs):
        """Constructor.

        :param main_fields: name of the timestamp field.
        :param main_query: list of fields to copy from the top hit document
            into the resulting aggregation.
        """
        super(ESWekoFileStatsQuery, self).__init__(*args, **kwargs)
        self.main_fields = main_fields or []
        self.main_query = main_query or {}

    def build_query(self, start_date, end_date, **kwargs):
        """Build the elasticsearch query."""
        agg_query = Search(using=self.client,
                           index=self.index,
                           doc_type=self.doc_type)[0:0]
        if self.main_query:
            query_q = self.main_query
            for _field in self.main_fields:
                query_q = json.dumps(query_q).replace(
                    "@{}".format(_field), kwargs[_field])
                query_q = json.loads(query_q)
            agg_query.update_from_dict(query_q)

        if start_date or end_date:
            time_range = {}
            if start_date:
                time_range['gte'] = start_date.isoformat()
            if end_date:
                time_range['lte'] = end_date.isoformat()
            try:
                time_range['time_zone'] = str(
                    current_app.config['STATS_WEKO_DEFAULT_TIMEZONE']())
            except AttributeError:
                time_range['time_zone'] = current_app.config.get('BABEL_DEFAULT_TIMEZONE', 'Asia/Tokyo')
            agg_query = agg_query.filter(
                'range',
                **{self.time_field: time_range})

        for modifier in self.query_modifiers:
            agg_query = modifier(agg_query, **kwargs)

        base_agg = agg_query.aggs

        def _apply_metric_aggs(agg):
            for dst, (metric, field, opts) in self.metric_fields.items():
                agg.metric(dst, metric, field=field, **opts)

        size = kwargs.get('agg_size') if kwargs.get('agg_size') else \
            current_app.config['STATS_ES_INTEGER_MAX_VALUE']
        _apply_metric_aggs(base_agg)
        if self.group_fields:
            sources = []
            for f in self.group_fields:
                sources.append({f: A('terms', field=f)})
            if kwargs.get('after_key'):
                base_agg.bucket(
                    'my_buckets', 'composite', size=size, sources=sources, after=kwargs.get('after_key')
                )
            else:
                base_agg.bucket(
                    'my_buckets', 'composite', size=size, sources=sources
                )
        else:
            if self.aggregated_fields:
                cur_agg = base_agg
                for term in self.aggregated_fields:
                    cur_agg = cur_agg.bucket(term, 'terms', field=term, size=size)
                    _apply_metric_aggs(cur_agg)

        if self.copy_fields:
            base_agg.metric(
                'top_hit', 'top_hits', size=1, sort={'timestamp': 'desc'}
            )

        return agg_query


class ESWekoTermsQuery(ESTermsQuery):
    """Weko ES Terms Query."""

    def build_query(self, start_date, end_date, **kwargs):
        """Build the elasticsearch query with."""
        agg_query = Search(using=self.client,
                           index=self.index,
                           doc_type=self.doc_type)[0:0]

        if start_date is not None or end_date is not None:
            time_range = {}
            if start_date is not None:
                time_range['gte'] = start_date.isoformat()
            if end_date is not None:
                time_range['lte'] = end_date.isoformat()
            try:
                time_range['time_zone'] = str(
                    current_app.config['STATS_WEKO_DEFAULT_TIMEZONE']())
            except AttributeError:
                time_range['time_zone'] = current_app.config.get('BABEL_DEFAULT_TIMEZONE', 'Asia/Tokyo')

            agg_query = agg_query.filter(
                'range',
                **{self.time_field: time_range})

        for modifier in self.query_modifiers:
            agg_query = modifier(agg_query, **kwargs)

        base_agg = agg_query.aggs

        def _apply_metric_aggs(agg):
            for dst, (metric, field, opts) in self.metric_fields.items():
                agg.metric(dst, metric, field=field, **opts)

        size = kwargs.get('agg_size') if kwargs.get('agg_size') else \
            current_app.config['STATS_ES_INTEGER_MAX_VALUE']
        _apply_metric_aggs(base_agg)
        if self.group_fields:
            sources = []
            for f in self.group_fields:
                sources.append({f: A('terms', field=f)})
            if kwargs.get('after_key'):
                base_agg.bucket(
                    'my_buckets', 'composite', size=size, sources=sources, after=kwargs.get('after_key')
                )
            else:
                base_agg.bucket(
                    'my_buckets', 'composite', size=size, sources=sources
                )
        else:
            if self.aggregated_fields:
                cur_agg = base_agg
                for term in self.aggregated_fields:  # Added size and sort
                    cur_agg = cur_agg.bucket(
                        term, 'terms', field=term, size=size,
                        order=kwargs.get('agg_sort', {"_count": "desc"})
                    )
                    _apply_metric_aggs(cur_agg)

        if self.copy_fields:
            base_agg.metric(
                'top_hit', 'top_hits', size=1, sort={'timestamp': 'desc'}
            )

        for query_param, filtered_field in self.required_filters.items():
            if query_param in kwargs:
                agg_query = agg_query.filter(
                    'term', **{filtered_field: kwargs[query_param]}
                )

        if kwargs.get('agg_filter'):
            max_clause_count = current_app.config.get('OAISERVER_ES_MAX_CLAUSE_COUNT', 1024)
            field, values = next(iter(kwargs.get('agg_filter').items()))
            if isinstance(values, list):
                chunks = list(chunk_list(values, max_clause_count))
                should_clauses = [{'terms': {field: chunk}} for chunk in chunks]
                agg_query = agg_query.filter('bool', should=should_clauses, minimum_should_match=1)
            else:
                agg_query = agg_query.filter('terms', **kwargs.get('agg_filter'))

        if kwargs.get('wildcard'):
            agg_query = agg_query.filter('wildcard', **kwargs.get('wildcard'))

        return agg_query


class ESWekoRankingQuery(ESTermsQuery):
    """Weko ES Query for Ranking Page."""

    def __init__(self, main_fields=None, main_query=None, *args, **kwargs):
        """Constructor.

        :param main_fields: name of the timestamp field.
        :param main_query: list of fields to copy from the top hit document
            into the resulting aggregation.
        """
        super(ESWekoRankingQuery, self).__init__(*args, **kwargs)
        self.main_fields = main_fields or []
        self.main_query = main_query or {}

    def build_query(self, **kwargs):
        """Build the elasticsearch query."""
        search_index_prefix = current_app.config['SEARCH_INDEX_PREFIX'].strip('-')
        es_index = self.index.format(search_index_prefix, kwargs.get("event_type"))
        es_doc_type = self.doc_type.format(kwargs.get("event_type")) if self.doc_type else ''
        agg_query = Search(using=self.client,
                           index=es_index,
                           doc_type=es_doc_type)[0:0]

        query_q = json.dumps(self.main_query)
        for _field in self.main_fields:
            query_q = query_q.replace(
                "@{}".format(_field), kwargs.get(_field, ""))

        try:
            query_q = query_q.replace(
                "@time_zone", str(current_app.config['STATS_WEKO_DEFAULT_TIMEZONE']())
            )
        except AttributeError:
            query_q = query_q.replace(
                "@time_zone", current_app.config.get('BABEL_DEFAULT_TIMEZONE', 'Asia/Tokyo')
            )
        query_q = json.loads(query_q)
        if kwargs.get("must_not"):
            query_q['query']['bool']['must_not'] = json.loads(kwargs.get('must_not'))
        else:
            del query_q['query']['bool']['must_not']
        agg_query.update_from_dict(query_q)
        return agg_query

    def run(self, start_date=None, end_date=None, **kwargs):
        """Run the query."""
        if kwargs['new_items']:
            kwargs['start_date'] = start_date
            kwargs['end_date'] = end_date
        else:
            start_date = self.extract_date(start_date) if start_date else None
            end_date = self.extract_date(end_date) if end_date else None
            self.validate_arguments(start_date, end_date, **kwargs)

            kwargs['start_date'] = start_date.isoformat()
            kwargs['end_date'] = end_date.isoformat()
        agg_query = self.build_query(**kwargs)

        query_result = agg_query.execute().to_dict()

        return query_result


class ESWekoFileRankingQuery(ESTermsQuery):
    """Weko ES Query for File Download Ranking."""

    def __init__(self, main_fields=None, main_query=None, *args, **kwargs):
        """Constructor.

        :param main_fields: name of the timestamp field.
        :param main_query: list of fields to copy from the top hit document
            into the resulting aggregation.
        """
        super(ESWekoFileRankingQuery, self).__init__(*args, **kwargs)
        self.main_fields = main_fields or []
        self.main_query = main_query or {}

    def build_query(self, start_date, end_date, **kwargs):
        """Build the elasticsearch query."""
        agg_query = Search(
            using=self.client,
            index=self.index,
            doc_type=self.doc_type
        )[0:0]
        if self.main_query:
            query_q = self.main_query
            for _field in self.main_fields:
                query_q = json.dumps(query_q).replace(
                    "@{}".format(_field), kwargs[_field])
                query_q = json.loads(query_q)

            if 'root_file_id_list' in kwargs.keys():
                query_q['query']['bool']['filter'][1]['terms']['root_file_id'] = kwargs['root_file_id_list']

            agg_query.update_from_dict(query_q)

        if start_date or end_date:
            time_range = {}
            if start_date:
                time_range['gte'] = start_date.isoformat()
            if end_date:
                time_range['lte'] = end_date.isoformat()
            try:
                time_range['time_zone'] = str(
                    current_app.config['STATS_WEKO_DEFAULT_TIMEZONE']())
            except AttributeError:
                time_range['time_zone'] = current_app.config.get('BABEL_DEFAULT_TIMEZONE', 'Asia/Tokyo')
            agg_query = agg_query.filter(
                'range',
                **{self.time_field: time_range})

        for dst, (metric, field, opts) in self.metric_fields.items():
            agg_query.aggs.metric(dst, metric, field=field, **opts)

        return agg_query

    def process_query_result(self, query_result, start_date, end_date):
        """Build the result using the query result."""
        def build_buckets(agg, fields, bucket_result):
            """Build recursively result buckets."""
            # Add metric results for current bucket
            for metric in self.metric_fields:
                bucket_result[metric] = agg[metric]
            return bucket_result

        # Add copy_fields
        aggs = query_result['aggregations']
        result = dict(
            start_date=start_date.isoformat() if start_date else None,
            end_date=end_date.isoformat() if end_date else None,
        )

        return build_buckets(aggs, self.aggregated_fields, result)

    def run(self, start_date=None, end_date=None, **kwargs):
        """Run the query."""
        start_date = self.extract_date(start_date) if start_date else None
        end_date = self.extract_date(end_date) if end_date else None
        self.validate_arguments(start_date, end_date, **kwargs)

        agg_query = self.build_query(start_date, end_date, **kwargs)
        current_app.logger.debug(agg_query.to_dict())
        query_result = agg_query.execute().to_dict()

        return self.process_query_result(query_result, start_date, end_date)
