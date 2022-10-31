# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Aggregation tests."""

import datetime
import time

import pytest
from tests.conftest import _create_file_download_event
from elasticsearch_dsl import Index, Search
from invenio_search import current_search, current_search_client
from mock import patch

from invenio_stats import current_stats
from invenio_stats.aggregations import StatAggregator, filter_robots, BookmarkAPI
from invenio_stats.processors import EventsIndexer
from invenio_stats.tasks import aggregate_events, process_events

# def filter_robots(query):
# def filter_restricted(query):
# def format_range_dt(dt, interval):

# class BookmarkAPI:
#     def __init__(self, client, agg_type, agg_interval):
#     def _ensure_index_exists(func):
#         def wrapped(self, *args, **kwargs):
#     def set_bookmark(self, value):
#     def get_bookmark(self):
#     def list_bookmarks(self, start_date=None, end_date=None, limit=None):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_aggregations.py::test_BookmarkAPI -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_BookmarkAPI(app):
    bookmark_api = BookmarkAPI(current_search_client,
                               'file-download-agg',
                               'day')
    bookmark_api.set_bookmark('2021-01-01')
    time.sleep(10)
    res = bookmark_api.get_bookmark()
    assert res==datetime.datetime(2021, 1, 1)

    res = bookmark_api.list_bookmarks(start_date='2021-01-01', end_date='2021-02-01')
    for b in res:
        assert b.date=='2021-01-01'

# class StatAggregator(object):
#     def __init__(self, name, event, client=None,
#     def aggregation_doc_type(self):
#     def _get_oldest_event_timestamp(self):
#     def agg_iter(self, lower_limit=None, upper_limit=None, manual=False):
#     def run(self, start_date=None, end_date=None, update_bookmark=True, manual=False):
#     def list_bookmarks(self, start_date=None, end_date=None, limit=None):
#     def delete(self, start_date=None, end_date=None):
#         def _delete_actions():
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_aggregations.py::test_wrong_intervals -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_wrong_intervals(app):
    """Test aggregation with aggregation_interval > index_interval."""
    with pytest.raises(ValueError):
        StatAggregator('test-agg', 'test', current_search_client,
                       aggregation_interval='month', index_interval='day')

# .tox/c1/bin/pytest --cov=invenio_stats tests/test_aggregations.py::test_StatAggregator -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_StatAggregator(app):
    """Test bookmark reading."""
    stat_agg = StatAggregator(name='file-download-agg',
                              client=current_search_client,
                              event='file-download',
                              aggregation_field='file_id',
                              aggregation_interval='day')
    stat_agg.run()

# def test_overwriting_aggregations(app, mock_event_queue, es_with_templates):
#     """Check that the StatAggregator correctly starts from bookmark.

#     1. Create sample file download event and process it.
#     2. Run aggregator and write count, in aggregation index.
#     3. Create new events and repeat procedure to assert that the
#         results within the interval of the previous events
#         overwrite the aggregation,
#         by checking that the document version has increased.
#     """
#     class NewDate(datetime.datetime):
#         """datetime.datetime mock."""
#         # Aggregate at 12:00, thus the day will be aggregated again later
#         current_date = (2017, 6, 2, 12)

#         @classmethod
#         def utcnow(cls):
#             return cls(*cls.current_date)

#     # Send some events
#     event_type = 'file-download'
#     mock_event_queue.consume.return_value = [
#         _create_file_download_event(date) for date in
#         [(2017, 6, 1), (2017, 6, 2, 10)]
#     ]

#     indexer = EventsIndexer(
#         mock_event_queue
#     )
#     indexer.run()
#     current_search_client.indices.refresh(index='*')

#     # Aggregate events
#     with patch('datetime.datetime', NewDate):
#         aggregate_events(['file-download-agg'])
#     current_search_client.indices.refresh(index='*')

#     # Send new events, some on the last aggregated day and some far
#     # in the future.
#     res = current_search_client.search(index='stats-file-download',
#                                        version=True)
#     for hit in res['hits']['hits']:
#         if 'file_id' in hit['_source'].keys():
#             assert hit['_version'] == 1

#     mock_event_queue.consume.return_value = [
#         _create_file_download_event(date) for date in
#         [(2017, 6, 2, 15),  # second event on the same date
#          (2017, 7, 1)]
#     ]
#     indexer = EventsIndexer(
#         mock_event_queue
#     )
#     indexer.run()
#     current_search_client.indices.refresh(index='*')

#     # Aggregate again. The aggregation should start from the last bookmark.
#     NewDate.current_date = (2017, 7, 2)
#     with patch('datetime.datetime', NewDate):
#         aggregate_events(['file-download-agg'])
#     current_search_client.indices.refresh(index='*')

#     res = current_search_client.search(
#         index='stats-file-download',
#         doc_type='file-download-day-aggregation',
#         version=True
#     )
#     for hit in res['hits']['hits']:
#         if hit['_source']['timestamp'] == '2017-06-02T00:00:00':
#             assert hit['_version'] == 2
#             assert hit['_source']['count'] == 2
#         else:
#             assert hit['_version'] == 1


# def test_aggregation_without_events(app, es_with_templates):
#     """Check that the aggregation doesn't crash if there are no events.

#     This scenario happens when celery starts aggregating but no events
#     have been created yet.
#     """
#     # Aggregate events
#     StatAggregator(name='file-download-agg',
#                    event='file-download',
#                    aggregation_field='file_id',
#                    aggregation_interval='day',
#                    query_modifiers=[]).run()
#     assert not Index(
#         'stats-file-download', using=current_search_client
#     ).exists()
#     # Create the index but without any event. This happens when the events
#     # have been indexed but are not yet searchable (before index refresh).
#     Index('events-stats-file-download-2017',
#           using=current_search_client).create()
#     # Wait for the index to be available
#     time.sleep(1)
#     # Aggregate events
#     StatAggregator(name='test-file-download',
#                    event='file-download',
#                    aggregation_field='file_id',
#                    aggregation_interval='day',
#                    query_modifiers=[]).run()
#     assert not Index(
#         'stats-file-download', using=current_search_client
#     ).exists()


# def test_bookmark_removal(app, es_with_templates, mock_event_queue):
#     """Remove aggregation bookmark and restart aggregation.

#     This simulates the scenario where aggregations have been created but the
#     the bookmarks have not been set due to an error.
#     """
#     mock_event_queue.consume.return_value = [
#         _create_file_download_event(date) for date in
#         [(2017, 6, 2, 15),  # second event on the same date
#          (2017, 7, 1)]
#     ]
#     indexer = EventsIndexer(
#         mock_event_queue
#     )
#     indexer.run()
#     current_search_client.indices.refresh(index='*')

#     def aggregate_and_check_version(expected_version):
#         # Aggregate events
#         StatAggregator(name='file-download-agg',
#                        event='file-download',
#                        aggregation_field='file_id',
#                        aggregation_interval='day',
#                        query_modifiers=[]).run()
#         current_search_client.indices.refresh(index='*')
#         res = current_search_client.search(
#             index='stats-file-download',
#             doc_type='file-download-day-aggregation',
#             version=True
#         )
#         for hit in res['hits']['hits']:
#             assert hit['_version'] == expected_version

#     aggregate_and_check_version(1)
#     aggregate_and_check_version(1)
#     # Delete all bookmarks
#     bookmarks = Search(
#         using=current_search_client,
#         index='stats-file-download',
#         doc_type='file-download-agg-bookmark').query('match_all')
#     for bookmark in bookmarks:
#         res = current_search_client.delete(
#             index=bookmark.meta.index, id=bookmark.meta.id,
#             doc_type='file-download-agg-bookmark'
#         )
#     current_search_client.indices.refresh(index='*')
#     # the aggregations should have been overwritten
#     aggregate_and_check_version(2)


# @pytest.mark.parametrize('indexed_events',
#                          [dict(file_number=5,
#                                event_number=1,
#                                start_date=datetime.date(2015, 1, 28),
#                                end_date=datetime.date(2015, 2, 3))],
#                          indirect=['indexed_events'])
# def test_date_range(app, es, event_queues, indexed_events):
#     aggregate_events(['file-download-agg'])
#     current_search_client.indices.refresh(index='*')

#     query = Search(using=current_search_client,
#                    index='stats-file-download')[0:30].sort('file_id')
#     results = query.execute()

#     total_count = 0
#     for result in results:
#         if 'file_id' in result:
#             total_count += result.count
#     assert total_count == 30


# @pytest.mark.parametrize('indexed_events',
#                          [dict(file_number=1,
#                                event_number=2,
#                                robot_event_number=3,
#                                start_date=datetime.date(2015, 1, 28),
#                                end_date=datetime.date(2015, 1, 30))],
#                          indirect=['indexed_events'])
# @pytest.mark.parametrize("with_robots", [(True), (False)])
# def test_filter_robots(app, es, event_queues, indexed_events, with_robots):
#     """Test the filter_robots query modifier."""
#     query_modifiers = []
#     if not with_robots:
#         query_modifiers = [filter_robots]
#     StatAggregator(name='file-download-agg',
#                    client=current_search_client,
#                    event='file-download',
#                    aggregation_field='file_id',
#                    aggregation_interval='day',
#                    query_modifiers=query_modifiers).run()
#     current_search_client.indices.refresh(index='*')
#     query = Search(
#         using=current_search_client,
#         index='stats-file-download',
#         doc_type='file-download-day-aggregation'
#     )[0:30].sort('file_id')
#     results = query.execute()
#     assert len(results) == 3
#     for result in results:
#         if 'file_id' in result:
#             assert result.count == (5 if with_robots else 2)


# @pytest.mark.skip('This test dont ever finish')
# def test_metric_aggregations(app, event_queues, es_with_templates):
#     """Test aggregation metrics."""
#     es = es_with_templates
#     current_stats.publish(
#         'file-download',
#         [_create_file_download_event(date, user_id='1') for date in
#          [(2018, 1, 1, 12, 10), (2018, 1, 1, 12, 20), (2018, 1, 1, 12, 30),
#           (2018, 1, 1, 13, 10), (2018, 1, 1, 13, 20), (2018, 1, 1, 13, 30),
#           (2018, 1, 1, 14, 10), (2018, 1, 1, 14, 20), (2018, 1, 1, 14, 30),
#           (2018, 1, 1, 15, 10), (2018, 1, 1, 15, 20), (2018, 1, 1, 15, 30)]])
#     process_events(['file-download'])
#     es.indices.refresh(index='*')

#     StatAggregator(name='file-download-agg',
#                    client=current_search_client,
#                    event='file-download',
#                    aggregation_field='file_id',
#                    metric_aggregation_fields={
#                        'unique_count': ('cardinality', 'unique_session_id',
#                                         {'precision_threshold': 1000}),
#                        'volume': ('sum', 'size', {})
#                    },
#                    aggregation_interval='day').run()
#     es.indices.refresh(index='*')

#     query = Search(
#         using=current_search_client,
#         index='stats-file-download',
#         doc_type='file-download-day-aggregation'
#     )

#     results = query.execute()
#     assert len(results) == 1
#     assert results[0].count == 12  # 3 views over 4 differnet hour slices
#     assert results[0].unique_count == 4  # 4 different hour slices accessed
#     assert results[0].volume == 9000 * 12
