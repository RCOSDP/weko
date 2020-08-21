# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Aggregation classes."""

from __future__ import absolute_import, print_function

import datetime
from collections import OrderedDict
from itertools import tee
from uuid import uuid4

import six
from dateutil import parser
from elasticsearch.helpers import bulk
from elasticsearch_dsl import Index, Search
from flask import current_app
from invenio_search import current_search_client

from invenio_stats.models import StatsAggregation, StatsBookmark


def filter_robots(query):
    """Modify an elasticsearch query so that robot events are filtered out."""
    return query.filter('term', is_robot=False)


def filter_restricted(query):
    """Add term filter to query for checking restricted users."""
    return query.filter('term', is_restricted=False)


class StatAggregator(object):
    """Generic aggregation class.

    This aggregation class queries Elasticsearch events and creates a new
    elasticsearch document for each aggregated day/month/year... This enables
    to "compress" the events and keep only relevant information.

    The expected events shoud have at least those two fields:

    .. code-block:: json

        {
            "timestamp": "<ISO DATE TIME>",
            "field_on_which_we_aggregate": "<A VALUE>"
        }

    The resulting aggregation documents will be of the form:

    .. code-block:: json

        {
            "timestamp": "<ISO DATE TIME>",
            "field_on_which_we_aggregate": "<A VALUE>",
            "count": "<NUMBER OF OCCURENCE OF THIS EVENT>",
            "field_metric": "<METRIC CALCULATION ON A FIELD>"
        }

    This aggregator saves a bookmark document after each run. This bookmark
    is used to aggregate new events without having to redo the old ones.
    """

    def __init__(self, name, event, client=None,
                 aggregation_field=None,
                 metric_aggregation_fields=None,
                 copy_fields=None,
                 query_modifiers=None,
                 aggregation_interval='month',
                 index_interval='month', batch_size=7):
        """Construct aggregator instance.

        :param event: aggregated event.
        :param client: elasticsearch client.
        :param aggregation_field: field on which the aggregation will be done.
        :param metric_aggregation_fields: dictionary of fields on which a
            metric aggregation will be computed. The format of the dictionary
            is "destination field" ->
            tuple("metric type", "source field", "metric_options").
        :param copy_fields: list of fields which are copied from the raw events
            into the aggregation.
        :param query_modifiers: list of functions modifying the raw events
            query. By default the query_modifiers are [filter_robots].
        :param aggregation_interval: aggregation time window. default: month.
        :param index_interval: time window of the elasticsearch indices which
            will contain the resulting aggregations.
        :param batch_size: max number of days for which raw events are being
            fetched in one query. This number has to be coherent with the
            aggregation_interval.
        """
        self.name = name
        self.client = client or current_search_client
        self.event = event
        self.search_index_prefix = current_app.config['SEARCH_INDEX_PREFIX']. \
            strip('-')
        self.aggregation_alias = '{0}-stats-{1}'.format(
            self.search_index_prefix, self.event)
        self.bookmark_alias = '{0}-stats-{1}-bookmark'.format(
            self.search_index_prefix, self.event)
        self.aggregation_field = aggregation_field
        self.metric_aggregation_fields = metric_aggregation_fields or {}
        self.allowed_metrics = {
            'cardinality', 'min', 'max', 'avg', 'sum', 'extended_stats',
            'geo_centroid', 'percentiles', 'stats'}
        if any(v not in self.allowed_metrics
               for k, (v, _, _) in (metric_aggregation_fields or {}).items()):
            raise(ValueError('Metric aggregation type should be one of [{}]'
                             .format(', '.join(self.allowed_metrics))))

        self.copy_fields = copy_fields or {}
        self.aggregation_interval = aggregation_interval
        self.index_interval = index_interval
        self.query_modifiers = (query_modifiers if query_modifiers is not None
                                else [filter_robots])
        self.supported_intervals = OrderedDict([('hour', '%Y-%m-%dT%H'),
                                                ('day', '%Y-%m-%d'),
                                                ('month', '%Y-%m'),
                                                ('year', '%Y')])
        self.dt_rounding_map = {
            'hour': 'h', 'day': 'd', 'month': 'M', 'year': 'y'}
        if list(self.supported_intervals.keys()).index(aggregation_interval) \
                > \
                list(self.supported_intervals.keys()).index(index_interval):
            raise(ValueError('Aggregation interval should be'
                             ' shorter than index interval'))
        self.index_name_suffix = self.supported_intervals[index_interval]
        self.doc_id_suffix = self.supported_intervals[aggregation_interval]
        self.batch_size = batch_size
        self.event_index = '{0}-events-stats-{1}'.format(
            self.search_index_prefix, self.event)

    @property
    def bookmark_doc_type(self):
        """Get document type for the aggregation's bookmark."""
        return '{0}-bookmark'.format(self.name)

    @property
    def aggregation_doc_type(self):
        """Get document type for the aggregation."""
        return '{0}-{1}-aggregation'.format(
            self.event, self.aggregation_interval)

    def _get_oldest_event_timestamp(self):
        """Search for the oldest event timestamp."""
        # Retrieve the oldest event in order to start aggregation
        # from there
        query_events = Search(
            using=self.client,
            index=self.event_index
        )[0:1].sort(
            {'timestamp': {'order': 'asc'}}
        )
        result = query_events.execute()

        # There might not be any events yet if the first event have been
        # indexed but the indices have not been refreshed yet.
        if len(result) == 0:
            return None
        return parser.parse(result[0]['timestamp'])

    def get_bookmark(self):
        """Get last aggregation date."""
        if not Index(self.bookmark_alias,
                     using=self.client).exists():
            if not Index(self.event_index,
                         using=self.client).exists():
                return datetime.date.today()
            return self._get_oldest_event_timestamp()

        # retrieve the oldest bookmark
        query_bookmark = Search(
            using=self.client,
            index=self.bookmark_alias,
            doc_type=self.bookmark_doc_type
        )[0:1].sort(
            {'date': {'order': 'desc'}}
        )
        bookmarks = query_bookmark.execute()
        # if no bookmark is found but the index exist, the bookmark was somehow
        # lost or never written, so restart from the beginning
        if len(bookmarks) == 0:
            return self._get_oldest_event_timestamp()

        # change it to doc_id_suffix
        bookmark = datetime.datetime.strptime(bookmarks[0].date,
                                              self.doc_id_suffix)
        return bookmark

    def set_bookmark(self):
        """Set bookmark for starting next aggregation."""
        def _success_date():
            bookmark = {
                'date': self.new_bookmark or datetime.datetime.utcnow().
                strftime(self.doc_id_suffix)
            }

            yield dict(_id=uuid4(),
                       _index=self.last_index_written,
                       _type=self.bookmark_doc_type,
                       _source=bookmark)
        if self.last_index_written:
            db_iter, es_iter = tee(_success_date())
            StatsBookmark.save(db_iter)
            bulk(self.client,
                 es_iter,
                 stats_only=True)

    def _format_range_dt(self, d):
        """Format range filter datetime to the closest aggregation interval."""
        if not isinstance(d, six.string_types):
            d = d.isoformat()
        return '{0}||/{1}'.format(
            d, self.dt_rounding_map[self.aggregation_interval])

    def agg_iter(self, lower_limit=None, upper_limit=None):
        """Aggregate and return dictionary to be indexed in ES."""
        lower_limit = lower_limit or self.get_bookmark().isoformat()
        upper_limit = upper_limit or (
            datetime.datetime.utcnow().replace(microsecond=0).isoformat())
        aggregation_data = {}

        self.agg_query = Search(using=self.client,
                                index=self.event_index).\
            filter('range', timestamp={
                'gte': self._format_range_dt(lower_limit),
                'lte': self._format_range_dt(upper_limit)})

        # apply query modifiers
        for modifier in self.query_modifiers:
            self.agg_query = modifier(self.agg_query)

        hist = self.agg_query.aggs.bucket(
            'histogram',
            'date_histogram',
            field='timestamp',
            interval=self.aggregation_interval
        )
        terms = hist.bucket(
            'terms', 'terms', field=self.aggregation_field,
            size=current_app.config['STATS_ES_INTEGER_MAX_VALUE']
        )
        # FIXME: Paginate?
        top = terms.metric(
            'top_hit', 'top_hits', size=1, sort={'timestamp': 'desc'}
        )
        for dst, (metric, src, opts) in self.metric_aggregation_fields.items():
            terms.metric(dst, metric, field=src, **opts)

        results = self.agg_query.execute()
        index_name = None
        bookmark_name = None
        for interval in results.aggregations['histogram'].buckets:
            interval_date = datetime.datetime.strptime(
                interval['key_as_string'], '%Y-%m-%dT%H:%M:%S')
            for aggregation in interval['terms'].buckets:
                aggregation_data['timestamp'] = interval_date.isoformat()
                aggregation_data[self.aggregation_field] = aggregation['key']
                aggregation_data['count'] = aggregation['doc_count']

                if self.metric_aggregation_fields:
                    for f in self.metric_aggregation_fields:
                        aggregation_data[f] = aggregation[f]['value']

                doc = aggregation.top_hit.hits.hits[0]['_source']
                for destination, source in self.copy_fields.items():
                    if isinstance(source, six.string_types):
                        aggregation_data[destination] = doc[source]
                    else:
                        aggregation_data[destination] = source(
                            doc,
                            aggregation_data
                        )

                index_name = '{0}-stats-{1}-{2}'.\
                             format(self.search_index_prefix, self.event,
                                    interval_date.strftime(
                                        self.index_name_suffix))
                bookmark_name = '{0}-stats-bookmark-{1}-{2}'.\
                                format(self.search_index_prefix, self.event,
                                       interval_date.strftime(
                                           self.index_name_suffix))
                self.indices.add(index_name)
                rtn_data = dict(
                    _id='{0}-{1}'.
                        format(aggregation['key'],
                               interval_date.strftime(
                                   self.doc_id_suffix)),
                    _index=index_name,
                    _type=self.aggregation_doc_type,
                    _source=aggregation_data
                )
                # Save stats event into Database.
                StatsAggregation.save(rtn_data)

                yield rtn_data
        self.last_index_written = bookmark_name

    def run(self, start_date=None, end_date=None, update_bookmark=True):
        """Calculate statistics aggregations."""
        # If no events have been indexed there is nothing to aggregate
        if not Index(self.event_index, using=self.client).exists():
            return

        lower_limit = start_date or self.get_bookmark()
        # Stop here if no bookmark could be estimated.
        if lower_limit is None:
            return
        upper_limit = min(
            end_date or datetime.datetime.max,  # ignore if `None`
            datetime.datetime.utcnow().replace(microsecond=0),
            datetime.datetime.combine(
                lower_limit + datetime.timedelta(self.batch_size),
                datetime.datetime.min.time())
        )
        while upper_limit <= datetime.datetime.utcnow():
            self.indices = set()
            self.new_bookmark = upper_limit.strftime(self.doc_id_suffix)
            bulk(self.client,
                 self.agg_iter(lower_limit, upper_limit),
                 stats_only=True,
                 chunk_size=50)
            # Flush all indices which have been modified
            current_search_client.indices.flush(
                index=','.join(self.indices),
                wait_if_ongoing=True
            )
            if update_bookmark:
                self.set_bookmark()
            self.indices = set()
            lower_limit = lower_limit + datetime.timedelta(self.batch_size)
            upper_limit = min(
                end_date or datetime.datetime.max,  # ignore if `None``
                datetime.datetime.utcnow().replace(microsecond=0),
                lower_limit + datetime.timedelta(self.batch_size)
            )
            if lower_limit > upper_limit:
                break

    def list_bookmarks(self, start_date=None, end_date=None, limit=None):
        """List the aggregation's bookmarks."""
        query = Search(
            using=self.client,
            index=self.bookmark_alias,
            doc_type=self.bookmark_doc_type
        ).sort({'date': {'order': 'desc'}})

        range_args = {}
        if start_date:
            range_args['gte'] = self._format_range_dt(
                start_date.replace(microsecond=0))
        if end_date:
            range_args['lte'] = self._format_range_dt(
                end_date.replace(microsecond=0))
        if range_args:
            query = query.filter('range', date=range_args)

        return query[0:limit].execute() if limit else query.scan()

    def delete(self, start_date=None, end_date=None):
        """Delete aggregation documents."""
        aggs_query = Search(
            using=self.client,
            index=self.aggregation_alias,
            doc_type=self.aggregation_doc_type
        ).extra(_source=False)

        range_args = {}
        if start_date:
            range_args['gte'] = self._format_range_dt(
                start_date.replace(microsecond=0))
        if end_date:
            range_args['lte'] = self._format_range_dt(
                end_date.replace(microsecond=0))
        if range_args:
            aggs_query = aggs_query.filter('range', timestamp=range_args)

        bookmarks_query = Search(
            using=self.client,
            index=self.bookmark_alias,
            doc_type=self.bookmark_doc_type
        ).sort({'date': {'order': 'desc'}})

        if range_args:
            bookmarks_query = bookmarks_query.filter('range', date=range_args)

        def _delete_actions():
            for query in (aggs_query, bookmarks_query):
                affected_indices = set()
                for doc in query.scan():
                    affected_indices.add(doc.meta.index)
                    yield dict(_index=doc.meta.index,
                               _op_type='delete',
                               _id=doc.meta.id,
                               _type=doc.meta.doc_type)
                current_search_client.indices.flush(
                    index=','.join(affected_indices), wait_if_ongoing=True)
        bulk(self.client, _delete_actions(), refresh=True)
