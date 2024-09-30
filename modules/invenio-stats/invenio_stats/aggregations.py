# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2019 CERN.
# Copyright (C)      2022 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Aggregation classes."""

import math
from datetime import datetime, timezone
from celery.utils.log import get_task_logger
from dateutil import parser
from dateutil.relativedelta import relativedelta
from flask import current_app
from invenio_search import current_search_client
from invenio_search.engine import dsl, search
from invenio_search.utils import prefix_index
from invenio_db import db

from .models import StatsAggregation, StatsBookmark
from .utils import get_bucket_size
from .bookmark import SUPPORTED_INTERVALS, BookmarkAPI, format_range_dt


INTERVAL_ROUNDING = {
    "hour": ("minute", "second", "microsecond"),
    "day": ("hour", "minute", "second", "microsecond"),
    "month": ("day", "hour", "minute", "second", "microsecond"),
}

INTERVAL_DELTAS = {
    "hour": relativedelta(hours=1),
    "day": relativedelta(days=1),
    "month": relativedelta(months=1),
}


def filter_robots(query):
    """Modify a search query so that robot events are filtered out."""
    return query.filter("term", is_robot=False)


def filter_restricted(query):
    """Add term filter to query for checking restricted users."""
    return query.filter('term', is_restricted=False)


ALLOWED_METRICS = {
    "avg",
    "cardinality",
    "extended_stats",
    "geo_centroid",
    "max",
    "min",
    "percentiles",
    "stats",
    "sum",
}


class StatAggregator(object):
    """Generic aggregation class.

    This aggregation class queries search events and creates a new
    search document for each aggregated day/month/year... This enables
    to "compress" the events and keep only relevant information.

    The expected events should have at least those two fields:

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
            "count": "<NUMBER OF OCCURRENCE OF THIS EVENT>",
            "field_metric": "<METRIC CALCULATION ON A FIELD>",
            "updated_timestamp": "<ISO DATE TIME>"
        }

    This aggregator saves a bookmark document after each run. This bookmark
    is used to aggregate new events without having to redo the old ones.

    Note the difference between the `timestamp` and the `updated_timestamp`. The first one identifies
    the date that is being calculated. The second one is to identify when the aggregation was modified.
    That might be useful if there are more actions depending on that action, like reindexing.
    """

    def __init__(
        self,
        name,
        event,
        client=None,
        field=None,
        metric_fields=None,
        copy_fields=None,
        query_modifiers=None,
        interval="day",
        index_interval="month",
        max_bucket_size=10000,
    ):
        """Construct aggregator instance.

        :param event: aggregated event.
        :param client: search client.
        :param field: field on which the aggregation will be done.
        :param metric_fields: dictionary of fields on which a
            metric aggregation will be computed. The format of the dictionary
            is "destination field" ->
            tuple("metric type", "source field", "metric_options").
        :param copy_fields: list of fields which are copied from the raw events
            into the aggregation.
        :param query_modifiers: list of functions modifying the raw events
            query. By default the query_modifiers are [filter_robots].
        :param interval: aggregation time window. default: month.
        :param index_interval: time window of the search indices which
            will contain the resulting aggregations.
        """
        self.name = name
        self.event = event
        self.event_index = prefix_index(f"events-stats-{event}")
        self.client = client or current_search_client
        self.index = prefix_index(f"stats-{event}")
        self.field = field
        self.metric_fields = metric_fields or {}
        self.interval = interval
        self.doc_id_suffix = SUPPORTED_INTERVALS[interval]
        self.index_interval = index_interval
        self.index_name_suffix = SUPPORTED_INTERVALS[index_interval]
        self.copy_fields = copy_fields or {}
        self.query_modifiers = (
            query_modifiers if query_modifiers is not None else [filter_robots]
        )
        self.bookmark_api = BookmarkAPI(self.name, self.interval)
        self.max_bucket_size = max_bucket_size

        self.bookmark_alias = prefix_index(f"stats-{event}-bookmark")

        if any(v not in ALLOWED_METRICS for k, (v, _, _) in self.metric_fields.items()):
            raise (
                ValueError(
                    "Metric aggregation type should be one of [{}]".format(
                        ", ".join(ALLOWED_METRICS)
                    )
                )
            )

        if list(SUPPORTED_INTERVALS.keys()).index(interval) > list(
            SUPPORTED_INTERVALS.keys()
        ).index(index_interval):
            raise (
                ValueError("Aggregation interval should be shorter than index interval")
            )

    def _get_oldest_event_timestamp(self):
        """Search for the oldest event timestamp."""
        # Retrieve the oldest event in order to start aggregation
        # from there
        query_events = (
            dsl.Search(using=self.client, index=self.event_index)
            .sort({"timestamp": {"order": "asc"}})
            .extra(size=1)
        )
        result = query_events.execute()
        # There might not be any events yet if the first event have been
        # indexed but the indices have not been refreshed yet.
        if len(result) == 0:
            return None
        return parser.parse(result[0]["timestamp"])

    def _split_date_range(self, lower_limit, upper_limit):
        """Return dict of rounded dates in range, split by aggregation interval.

        .. code-block:: python

            self._split_date_range(
                datetime(2023, 1, 10, 12, 34),
                datetime(2023, 1, 13, 11, 20),
            ) == {
                "2023-01-10": datetime.datetime(2023, 1, 10, 12, 34),
                "2023-01-11": datetime.datetime(2023, 1, 11, 12, 34),
                "2023-01-12": datetime.datetime(2023, 1, 12, 12, 34),
                "2023-01-13": datetime.datetime(2023, 1, 13, 11, 20),
            }
        """
        res = {}
        current_interval = lower_limit
        delta = INTERVAL_DELTAS[self.interval]
        while current_interval < upper_limit:
            dt_key = current_interval.strftime(SUPPORTED_INTERVALS[self.interval])
            res[dt_key] = current_interval
            current_interval += delta

        dt_key = upper_limit.strftime(SUPPORTED_INTERVALS[self.interval])
        res[dt_key] = upper_limit
        return res

    def agg_iter(self, dt, previous_bookmark, manual=False):
        """Aggregate and return dictionary to be indexed in the search engine."""
        logger = get_task_logger(__name__)

        rounded_dt = format_range_dt(dt, self.interval)
        agg_query = (
            dsl.Search(using=self.client, index=self.event_index).filter(
                # Filter for the specific interval (hour, day, month)
                "term",
                timestamp=rounded_dt,
            )
            # we're only interested in the aggregated results but not the search hits,
            # so we tell the search to ignore them to save some bandwidth
            .extra(size=0)
        )
        # apply query modifiers
        for modifier in self.query_modifiers:
            agg_query = modifier(agg_query)

        total_buckets = get_bucket_size(
            self.client,
            self.event_index,
            self.field,
            start_date=rounded_dt,
            end_date=rounded_dt,
        )

        num_partitions = max(
            int(math.ceil(float(total_buckets) / self.max_bucket_size)), 1
        )
        for p in range(num_partitions):
            terms = agg_query.aggs.bucket(
                "terms",
                "terms",
                field=self.field,
                include={"partition": p, "num_partitions": num_partitions},
                size=self.max_bucket_size,
            )
            terms.metric("top_hit", "top_hits", size=1, sort={"timestamp": "desc"})
            for dst, (metric, src, opts) in self.metric_fields.items():
                terms.metric(dst, metric, field=src, **opts)
            # Let's get also the last time that the event happened
            terms.metric("last_update", "max", field="updated_timestamp")

            logger.debug(f"agg_query query: {agg_query}")
            results = agg_query.execute(
                # NOTE: Without this, the aggregation changes above, do not
                # invalidate the search's response cache, and thus you would
                # always get the same results for each partition.
                ignore_cache=True,
            )
            logger.debug("agg_query result: %s", len(results))
            for aggregation in results.aggregations["terms"].buckets:
                doc = aggregation.top_hit.hits.hits[0]["_source"].to_dict()
                aggregation = aggregation.to_dict()
                interval_date = datetime.strptime(
                    doc["timestamp"], "%Y-%m-%dT%H:%M:%S"
                ).replace(**dict.fromkeys(INTERVAL_ROUNDING[self.interval], 0))

                # Skip events that have been previously aggregated.
                # The`updated_timestamp` field was introduced with v4.0.0, and it will
                # not exist in events created earlier
                last_update_aggr = aggregation["last_update"].get("value_as_string", None)
                if last_update_aggr and previous_bookmark:
                    last_date = datetime.fromisoformat(last_update_aggr.rstrip("Z"))
                    if last_date < previous_bookmark:
                        continue

                aggregation_data = {}
                aggregation_data["timestamp"] = interval_date.isoformat()
                aggregation_data[self.field] = aggregation["key"]
                aggregation_data["count"] = aggregation["doc_count"]
                aggregation_data["updated_timestamp"] = datetime.now(timezone.utc).isoformat()
                aggregation_data['event_type'] = self.event

                if self.metric_fields:
                    for f in self.metric_fields:
                        aggregation_data[f] = aggregation[f]["value"]

                for destination, source in self.copy_fields.items():
                    if isinstance(source, str):
                        if source == 'root_file_id' and source not in doc:
                            if 'file_id' in doc:
                                aggregation_data[destination] = doc['file_id']
                        else:
                            aggregation_data[destination] = doc.get(source, '')
                    else:
                        aggregation_data[destination] = source(doc, aggregation_data)

                index_name = prefix_index(f"stats-{self.event}")
                logger.debug(f"index_name: {index_name}")

                if manual:
                    res =  (
                        dsl.Search(using=self.client, index=index_name).filter(
                        'term',
                        unique_id=aggregation['key'])
                        .execute()
                    )

                    if res.hits.total.value > 0:
                        index_name = res.hits.hits[0]['_index']

                rtn_data = {
                    "_id": "{0}-{1}".format(
                        aggregation["key"], interval_date.strftime(self.doc_id_suffix)
                    ),
                    "_index": index_name,
                    "_source": aggregation_data,
                }
                if current_app.config['STATS_WEKO_DB_BACKUP_AGGREGATION']:
                    # Save stats aggregation into Database.
                    StatsAggregation.save(rtn_data, delete=True)

                yield rtn_data

    def _upper_limit(self, end_date):
        if end_date is not None and end_date.tzinfo is not None:
            end_date = end_date.replace(tzinfo=None)

        return min(
            end_date or datetime.max,
            datetime.now().replace(tzinfo=None)
        )

    def run(self, start_date=None, end_date=None, update_bookmark=True, manual=False):
        """Calculate statistics aggregations."""
        # If no events have been indexed there is nothing to aggregate
        if not dsl.Index(self.event_index, using=self.client).exists():
            return
        logger = get_task_logger(__name__)
        previous_bookmark = self.bookmark_api.get_bookmark()
        lower_limit = (
            start_date or previous_bookmark or self._get_oldest_event_timestamp()
        )
        logger.debug("lower_limit: %s", lower_limit)
        # Stop here if no bookmark could be estimated.
        if lower_limit is None:
            return

        upper_limit = self._upper_limit(end_date)
        logger.debug("upper_limit: %s", upper_limit)
        dates = self._split_date_range(lower_limit, upper_limit)
        # Let's get the timestamp before we start the aggregation.
        # This will be used for the next iteration. Some events might be processed twice
        if not end_date:
            end_date = datetime.utcnow().isoformat()

        results = []
        for dt_key, dt in sorted(dates.items()):
            results.append(
                search.helpers.bulk(
                    self.client,
                    self.agg_iter(dt, previous_bookmark, manual),
                    stats_only=True,
                    chunk_size=50,
                )
            )
        if update_bookmark:
            self.bookmark_api.set_bookmark(
                upper_limit.strftime("%Y-%m-%dT%H:%M:%S")
                or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
            )
        return results

    def list_bookmarks(self, start_date=None, end_date=None, limit=None):
        """List the aggregation's bookmarks."""
        return self.bookmark_api.list_bookmarks(start_date, end_date, limit)

    def delete(self, start_date=None, end_date=None):
        """Delete aggregation documents."""
        aggs_query = dsl.Search(
            using=self.client,
            index=self.index,
        ).extra(_source=False)

        range_args = {}
        if start_date:
            range_args["gte"] = format_range_dt(start_date, self.interval)
        if end_date:
            range_args["lte"] = format_range_dt(end_date, self.interval)
        if range_args:
            aggs_query = aggs_query.filter("range", timestamp=range_args)

        def _delete_actions():
            affected_indices = set()
            for doc in aggs_query.scan():
                affected_indices.add(doc.meta.index)
                yield {
                    "_index": doc.meta.index,
                    "_op_type": "delete",
                    "_id": doc.meta.id,
                }
            current_search_client.indices.flush(
                index=",".join(affected_indices), wait_if_ongoing=True
            )

        bookmark_query = StatsBookmark.query.filter_by(source_id=self.name)

        if start_date:
            bookmark_query = bookmark_query.filter(StatsBookmark.date >= start_date)
        if end_date:
            bookmark_query = bookmark_query.filter(StatsBookmark.date <= end_date)

        bookmark_query.delete(synchronize_session=False)

        search.helpers.bulk(self.client, _delete_actions(), refresh=True)
        db.session.commit()
