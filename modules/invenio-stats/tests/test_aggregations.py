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

from unittest.mock import patch

import pytest
import json
from .conftest import _create_file_download_event
from .helpers import mock_date
from invenio_search import current_search, current_search_client
from invenio_search.engine import dsl, search

from invenio_stats import current_stats
from invenio_stats.aggregations import StatAggregator, filter_robots, BookmarkAPI
from invenio_stats.processors import EventsIndexer
from invenio_stats.tasks import aggregate_events, process_events

from datetime import timedelta
from invenio_stats.models import StatsBookmark
from freezegun import freeze_time
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
    with app.app_context():
        bookmark_api = BookmarkAPI(current_search_client,
                                "file-download-agg",
                                "day")
        bookmark_api.set_bookmark("2021-01-01")
        time.sleep(10)
        res = bookmark_api.get_bookmark()
        assert res==datetime.datetime(2021, 1, 1)

        res = bookmark_api.list_bookmarks(start_date="2021-01-01", end_date="2021-02-01")
        for b in res:
            assert b.date=="2021-01-01"

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
def test_wrong_intervals(app, es):
    """Test aggregation with interval > index_interval."""
    with pytest.raises(ValueError):
        StatAggregator(
            "test-agg", "test", es, interval="month", index_interval="day"
        )


# .tox/c1/bin/pytest --cov=invenio_stats tests/test_aggregations.py::test_StatAggregator -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_StatAggregator(app, es):
    """Test bookmark reading."""
    stat_agg = StatAggregator(
        name="file-download-agg",
        client=es,
        event="file-download",
        field="file_id",
        interval="day",
    )

    with patch("invenio_stats.aggregations.datetime", mock_date(2017, 1, 7, 11, 10, 9)):
        stat_agg.run()
    current_search.flush_and_refresh(index="*")


def test_overwriting_aggregations(app, es, mock_event_queue):
    """Check that the StatAggregator correctly starts from bookmark.

    1. Create sample file download event and process it.
    2. Run aggregator and write count, in aggregation index.
    3. Create new events and repeat procedure to assert that the
        results within the interval of the previous events
        overwrite the aggregation,
        by checking that the document version has increased.
    4. Run one more time, without any new events, and ensure that the
        aggregations have not been overwritten
    """
    # Send some events
    mock_event_queue.consume.return_value = [
        _create_file_download_event(date) for date in [(2017, 6, 1), (2017, 6, 2, 10)]
    ]
    # Note that the events use the current time. Let's mock that as well
    with patch("invenio_stats.processors.datetime", mock_date(2017, 6, 2, 11)):
        indexer = EventsIndexer(mock_event_queue)
        indexer.run()
    current_search.flush_and_refresh(index="*")

    # Aggregate events
    with patch("invenio_stats.aggregations.datetime", mock_date(2017, 6, 2, 12)):
        aggregate_events(["file-download-agg"])
    current_search.flush_and_refresh(index="*")

    # Send new events, some on the last aggregated day and some far
    # in the future.
    res = es.search(index="stats-file-download", version=True)
    for hit in res["hits"]["hits"]:
        if "file_id" in hit["_source"].keys():
            assert hit["_version"] == 1

    mock_event_queue.consume.return_value = [
        _create_file_download_event(date)
        for date in [(2017, 6, 2, 15), (2017, 7, 1)]  # second event on the same date
    ]
    with patch("invenio_stats.processors.datetime", mock_date(2017, 7, 1, 5)):
        indexer = EventsIndexer(mock_event_queue)
        indexer.run()
    current_search.flush_and_refresh(index="*")
    # Aggregate again. The aggregation should start from the last bookmark.
    with patch("invenio_stats.aggregations.datetime", mock_date(2017, 7, 1, 6)):
        d = aggregate_events(["file-download-agg"])
    assert d == [
        [
            (1, 0),
            (0, 0),
            (0, 0),
            (0, 0),
            (0, 0),
            (0, 0),
            (0, 0),
            (0, 0),
            (0, 0),
            (0, 0),
            (0, 0),
            (0, 0),
            (0, 0),
            (0, 0),
            (0, 0),
            (0, 0),
            (0, 0),
            (0, 0),
            (0, 0),
            (0, 0),
            (0, 0),
            (0, 0),
            (0, 0),
            (0, 0),
            (0, 0),
            (0, 0),
            (0, 0),
            (0, 0),
            (0, 0),
            (1, 0),
        ]
    ]
    current_search.flush_and_refresh(index="*")
    res = es.search(index="stats-file-download", version=True)
    for hit in res["hits"]["hits"]:
        if hit["_source"]["timestamp"].startswith("2017-06-02"):
            assert hit["_version"] == 2
            assert hit["_source"]["count"] == 2
        else:
            assert hit["_version"] == 1

    # Run one more time, one hour later, and ensure that the aggregation does not modify anything
    with patch("invenio_stats.aggregations.datetime", mock_date(2017, 7, 1, 7)):
        d = aggregate_events(["file-download-agg"])
    assert d == [[(0, 0)]]


def test_aggregation_without_events(app, es):
    """Check that the aggregation doesn't crash if there are no events.

    This scenario happens when celery starts aggregating but no events
    have been created yet.
    """
    # Aggregate events
    with patch("invenio_stats.aggregations.datetime", mock_date(2017, 9, 9)):
        StatAggregator(
            name="file-download-agg",
            event="file-download",
            field="file_id",
            interval="day",
            query_modifiers=[],
        ).run()
    assert not dsl.Index("stats-file-download", using=es).exists()
    # Create the index but without any event. This happens when the events
    # have been indexed but are not yet searchable (before index refresh).
    dsl.Index("events-stats-file-download-2017", using=es).create()

    # Wait for the index to be available
    current_search.flush_and_refresh(index="*")

    # Aggregate events
    with patch("invenio_stats.aggregations.datetime", mock_date(2017, 9, 9)):
        StatAggregator(
            name="test-file-download",
            event="file-download",
            field="file_id",
            interval="day",
            query_modifiers=[],
        ).run()
    assert not dsl.Index("stats-file-download", using=es).exists()


def test_bookmark_removal(app, es, mock_event_queue):
    """Remove aggregation bookmark and restart aggregation.

    This simulates the scenario where aggregations have been created but the
    the bookmarks have not been set due to an error.
    """
    mock_event_queue.consume.return_value = [
        _create_file_download_event(date)
        for date in [(2017, 6, 2, 15), (2017, 7, 1)]  # second event on the same date
    ]
    indexer = EventsIndexer(mock_event_queue)
    indexer.run()
    current_search.flush_and_refresh(index="*")

    def aggregate_and_check_version(expected_version):
        with patch("invenio_stats.aggregations.datetime", mock_date(2017, 7, 10)):
            StatAggregator(
                field="file_id",
                interval="day",
                name="file-download-agg",
                event="file-download",
                query_modifiers=[],
            ).run()
        current_search.flush_and_refresh(index="*")
        res = es.search(index="stats-file-download", version=True)
        for hit in res["hits"]["hits"]:
            assert hit["_version"] == expected_version

    aggregate_and_check_version(1)
    aggregate_and_check_version(1)

    # Delete all bookmarks
    es.indices.delete(index="stats-bookmarks")
    current_search.flush_and_refresh(index="*")
    # the aggregations should have been overwritten
    aggregate_and_check_version(2)


@pytest.mark.parametrize(
    "indexed_events",
    [
        {
            "file_number": 5,
            "event_number": 1,
            "start_date": datetime.date(2015, 1, 28),
            "end_date": datetime.date(2015, 2, 3),
        }
    ],
    indirect=["indexed_events"],
)
def test_date_range(app, es, event_queues, indexed_events):
    """Test date ranges."""
    with patch("invenio_stats.aggregations.datetime", mock_date(2015, 2, 4)):
        aggregate_events(["file-download-agg"])
    current_search.flush_and_refresh(index="*")
    query = dsl.Search(using=es, index="stats-file-download")[0:30].sort(
        "file_id"
    )
    results = query.execute()

    total_count = 0
    for result in results:
        if "file_id" in result:
            total_count += result.count
    assert total_count == 30


@pytest.mark.parametrize(
    "indexed_events",
    [
        {
            "file_number": 1,
            "event_number": 2,
            "robot_event_number": 3,
            "start_date": datetime.date(2015, 1, 28),
            "end_date": datetime.date(2015, 1, 30),
        }
    ],
    indirect=["indexed_events"],
)
@pytest.mark.parametrize("with_robots", [(True), (False)])
def test_filter_robots(app, es, event_queues, indexed_events, with_robots):
    """Test the filter_robots query modifier."""
    query_modifiers = []
    if not with_robots:
        query_modifiers = [filter_robots]

    with patch("invenio_stats.aggregations.datetime", mock_date(2015, 2, 1)):
        StatAggregator(
            name="file-download-agg",
            client=es,
            event="file-download",
            field="file_id",
            interval="day",
            query_modifiers=query_modifiers,
        ).run()

    current_search.flush_and_refresh(index="*")
    query = dsl.Search(using=es, index="stats-file-download")[0:30].sort(
        "file_id"
    )
    results = query.execute()
    assert len(results) == 3
    for result in results:
        if "file_id" in result:
            assert result.count == (5 if with_robots else 2)


def test_metric_aggregations(app, es, event_queues):
    """Test aggregation metrics."""
    current_stats.publish(
        "file-download",
        [
            _create_file_download_event(date, user_id="1")
            for date in [
                (2018, 1, 1, 12, 10),
                (2018, 1, 1, 12, 20),
                (2018, 1, 1, 12, 30),
                (2018, 1, 1, 13, 10),
                (2018, 1, 1, 13, 20),
                (2018, 1, 1, 13, 30),
                (2018, 1, 1, 14, 10),
                (2018, 1, 1, 14, 20),
                (2018, 1, 1, 14, 30),
                (2018, 1, 1, 15, 10),
                (2018, 1, 1, 15, 20),
                (2018, 1, 1, 15, 30),
            ]
        ],
    )
    process_events(["file-download"])
    current_search.flush_and_refresh(index="*")

    stat_agg = StatAggregator(
        name="file-download-agg",
        client=es,
        event="file-download",
        field="file_id",
        metric_fields={
            "unique_count": (
                "cardinality",
                "unique_session_id",
                {"precision_threshold": 3000},
            ),
            "volume": ("sum", "size", {}),
        },
        interval="day",
    )
    with patch("invenio_stats.aggregations.datetime", mock_date(2018, 1, 2)):
        stat_agg.run()
    current_search.flush_and_refresh(index="*")

    query = dsl.Search(using=es, index="stats-file-download")
    results = query.execute()
    assert len(results) == 1
    assert results[0].count == 12  # 3 views over 4 differnet hour slices
    assert results[0].unique_count == 4  # 4 different hour slices accessed
    assert results[0].volume == 9000 * 12


def setup_elasticsearch_events(es, event_type, base_time, count=3):
    """Helper function to set up mock events in Elasticsearch."""
    events = []
    for i in range(count):
        event = {
            "_op_type": "index",
            "_index": f"test-events-stats-{event_type}",
            "_source": {
                "timestamp": (base_time + timedelta(seconds=i*10)).replace(microsecond=0).replace(tzinfo=None).isoformat(),
                "event_type": event_type,
                "file_id": f"file_{event_type}",
                "user_id": f"user_{event_type}",
                "visitor_id": f"visitor_{event_type}",
                "unique_id": f"unique_{event_type}",
                "size": 1000,
                "root_file_id": f"root_file_{event_type}",
                "updated_timestamp": (base_time + timedelta(seconds=i*10)).replace(microsecond=0).replace(tzinfo=None).isoformat(),
                "is_robot": "false",
            }
        }
        if event_type == 'celery-task':
            del event["_source"]["root_file_id"]
        if event_type == 'file-download':
            del event["_source"]["root_file_id"]
            del event["_source"]["file_id"]
            
        events.append(event)
    search.helpers.bulk(es, events)
    es.indices.refresh(index=f"test-events-stats-{event_type}")

def setup_elasticsearch_aggregations(es, event_type="file-download", count=10):
    """Insert test data into the specified Elasticsearch index for testing the branch logic of 'if res.hits.total.value > 0'."""
    events = []
    for i in range(count):
        event = {
                "_op_type": "index",
                "_index": f"test-stats-{event_type}",
                "_id": f"test_doc_{i}",
                "_source": {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "unique_id": f"unique_{event_type}",   
                    "event_type": f"{event_type}",
                    "file_id": f"file_{i}",
                    "user_id": f"user_{i}",
                    "size": 1000 + i,
                    "root_file_id": f"root_file_{i}"
                }
        }
        events.append(event)
    search.helpers.bulk(es, events)
    es.indices.refresh(index=f"test-stats-{event_type}")

def run_aggregation_test(es, event_type, base_time, previous_bookmark, manual, metric_fields):
    """Run the aggregation test for the given event_type and bookmark."""
    stat_agg = StatAggregator(
        name=f"{event_type}-agg",
        client=es,
        event=event_type,
        field="unique_id",
        interval="day",
        metric_fields=metric_fields,
        copy_fields={
            "copied_root_file_id": "root_file_id",
            "custom_field": lambda doc, agg: f"custom_{doc['unique_id']}"
        }
    )
    
    for DA_BACKUP in [True, False]:
        with freeze_time(base_time + timedelta(days=1)), \
            patch("invenio_stats.aggregations.current_app") as mock_app:
            mock_app.config = {'STATS_WEKO_DB_BACKUP_AGGREGATION': DA_BACKUP}

            results = list(stat_agg.agg_iter(dt=base_time, previous_bookmark=previous_bookmark, manual=manual))

            print(f"Aggregation results for {event_type} (manual: {manual}): {results}")

            if metric_fields:
                for result in results:
                    aggregation = result["_source"]
                    assert aggregation["event_type"] == event_type, "Event type mismatch"
                    assert aggregation["count"] > 0, "Expected non-zero count"
                    assert aggregation.get("timestamp", "").startswith(base_time.strftime("%Y-%m-%d")), "Incorrect aggregation timestamp"
                    assert all(field in aggregation for field in ["updated_timestamp", "total_size", "unique_users", "custom_field"]), "Missing aggregation fields"
            else:
                print(f"empty fields result length: {len(results)}")

def test_agg_iter(app, es, caplog):
    """Test agg_iter with multiple event types."""
    import logging
    caplog.set_level(logging.DEBUG)

    app.config['STATS_WEKO_DB_BACKUP_EVENTS'] = True
    app.config['STATS_WEKO_DB_BACKUP_AGGREGATION'] = True

    setup_elasticsearch_aggregations(es)

    event_types = ['celery-task', 'item-create', 'top-view', 'record-view', 'file-download', 'file-preview', 'search']

    for et_index, event_type in enumerate(event_types):
        base_time = datetime.datetime(2023, 1 + et_index, 1, 12, 0, 0)

        print(f"\nTesting event type: {event_type}")
        setup_elasticsearch_events(es, event_type, base_time)

        print("\nTesting with empty metric_fields")
        for scenario in ["no_bookmark", "old_bookmark", "new_bookmark"]:
            previous_bookmark = None
            if scenario == "old_bookmark":
                previous_bookmark = base_time - timedelta(days=2)
            elif scenario == "new_bookmark":
                previous_bookmark = base_time + timedelta(days=2)

            for manual in [False, True]:
                for mf in [False, True]:
                    metric_fields = {
                        "total_size": ("sum", "size", {}),
                        "unique_users": ("cardinality", "user_id", {"precision_threshold": 100})
                    } if mf else {}
                    run_aggregation_test(es, event_type, base_time, previous_bookmark, manual, metric_fields=metric_fields)

        agg_index_name = f"{app.config['SEARCH_INDEX_PREFIX']}stats-{event_type}"
        agg_search_result = es.search(index=agg_index_name, body={"query": {"match_all": {}}})
        print(f"Documents in aggregation index {agg_index_name}: {agg_search_result['hits']['total']['value']}")

    print("\nCaptured logs:")
    for record in caplog.records:
        print(f"{record.levelname}: {record.message}")


@pytest.fixture(scope='function')
def setup_test_data(app, es, db):
    """Pytest fixture to set up test data for various event types."""
    event_types = ['celery-task', 'item-create', 'top-view', 'record-view', 
                   'file-download', 'file-preview', 'search']
    base_time = datetime.datetime(2023, 1, 1, 12, 0, 0)
    
    for event_type in event_types:
        setup_elasticsearch_events(es, event_type, base_time)

    yield

    # Cleanup code can be added here if necessary


def print_specific_tables_data(db_, tables_to_print):
    """Print data from specified tables in the database."""
    # Get all table names from the database
    inspector = db_.inspect(db_.engine)
    all_table_names = inspector.get_table_names()
    
    # Filter tables to print
    tables_to_print = [table for table in all_table_names if table in tables_to_print]
    print(f"Tables to print: {tables_to_print}")

    # Print data from each specified table
    for table_name in tables_to_print:
        print(f"\nData from table '{table_name}':")
        query = f"SELECT * FROM {table_name}"
        result = db_.session.execute(query)
        rows = result.fetchall()
        
        if rows:
            for row in rows:
                print(dict(row))
        else:
            print(f"No data in table '{table_name}'")
            
    
def test_aggregator_run(app, es, db, setup_test_data):
    """Comprehensive test for StatAggregator run method across multiple event types."""
    event_types = ['celery-task', 'item-create', 'top-view', 'record-view', 'file-download', 'file-preview', 'search']
    base_time = datetime.datetime(2023, 1, 1, 12, 0, 0)
    
    for event_type in event_types:
        # Initialize StatAggregator for each event type
        aggregator = StatAggregator(
            name=f'{event_type}-agg',
            event=event_type,
            client=es,
            field='unique_id',
            interval='day',
            metric_fields={
                "total_size": ("sum", "size", {}),
                "unique_users": ("cardinality", "user_id", {"precision_threshold": 100})
            }
        )
        
        # Test Case 1: Index does not exist
        with patch.object(dsl.Index, 'exists', return_value=False):
            result = aggregator.run()
            assert result is None, f"Expected None when index doesn't exist for {event_type}"

        # Setup test data
        setup_elasticsearch_events(es, event_type, base_time, count=10)
        
        # Test Case 2: lower_limit is None
        with patch.object(aggregator, '_get_oldest_event_timestamp', return_value=None):
            result = aggregator.run()
            assert result is None, f"Expected None when lower_limit is None for {event_type}"

        # Test Case 3: Normal run
        with freeze_time(base_time + timedelta(days=3)):
            aggregator.run()

        # Test Case 4: Run with end_date provided
        with freeze_time(base_time + timedelta(days=7)):
            with patch.object(datetime.datetime, 'utcnow', return_value=base_time + timedelta(days=5)):
                aggregator.run(end_date=base_time + timedelta(days=5))
        
        # Verify bookmark was updated
        bookmark = StatsBookmark.query.filter_by(source_id=f'{event_type}-agg').order_by(StatsBookmark.updated.desc()).first()
        assert bookmark is not None, f"Bookmark not found for {event_type}"
        source_data = json.loads(bookmark.source)
        assert source_data['date'] == (base_time + timedelta(days=5)).strftime('%Y-%m-%dT%H:%M:%S'), f"Incorrect bookmark date for {event_type}"

        # Test Case 5: Run with update_bookmark set to False
        with freeze_time(base_time + timedelta(days=7)):
            aggregator.run(update_bookmark=False)
        
        # Verify bookmark was not updated
        bookmark = StatsBookmark.query.filter_by(source_id=f'{event_type}-agg').order_by(StatsBookmark.updated.desc()).first()
        assert bookmark is not None, f"Bookmark not found for {event_type}"
        source_data = json.loads(bookmark.source)
        assert source_data['date'] == (base_time + timedelta(days=5)).strftime('%Y-%m-%dT%H:%M:%S'), f"Bookmark should remain unchanged for {event_type}"

        # Verify final aggregation results
        current_search.flush_and_refresh(index='*')
        search = dsl.Search(using=es, index=f'test-stats-{event_type}')
        results = search.execute()

        assert results.hits.total.value > 0, f"No aggregation results found for {event_type}"

        for hit in results:
            assert all(field in hit for field in ['timestamp', 'count', 'total_size', 'unique_users']), f"Missing fields in aggregation result for {event_type}"
            assert hit.event_type == event_type, f"Incorrect event_type in aggregation result for {event_type}"
            

def test_aggregator_delete(app, es, db, setup_test_data):
    """Test the delete functionality of StatAggregator."""
    event_type = 'file-download'
    base_time = datetime.datetime(2023, 1, 1, 12, 0, 0)
    
    # Initialize the StatAggregator
    aggregator = StatAggregator(
        name=f'{event_type}-agg',
        event=event_type,
        client=es,
        field='unique_id',
        interval='day',
        metric_fields={
            "total_size": ("sum", "size", {}),
            "unique_users": ("cardinality", "user_id", {"precision_threshold": 100})
        }
    )
    
    # Run aggregations for multiple dates
    for days in range(10):
        with freeze_time(base_time + timedelta(days=days)):
            setup_elasticsearch_events(es, event_type, base_time + timedelta(days=days), count=5)
            aggregator.run()
    
    current_search.flush_and_refresh(index='*')
    
    # Verify initial state
    initial_agg_count = es.count(index=f'test-stats-{event_type}')['count']
    initial_bookmark_count = StatsBookmark.query.filter_by(source_id=f'{event_type}-agg').count()
    
    assert initial_agg_count > 0, "No initial aggregations found"
    assert initial_bookmark_count > 0, "No initial bookmarks found"
    
    # Test Case 1: Delete all
    print(f"Count before delete: {es.count(index=f'test-stats-{event_type}')['count']}")
    print_specific_tables_data(db, "stats_bookmark")
    aggregator.delete()
    current_search.flush_and_refresh(index='*')
    
    print(f"Count after delete: {es.count(index=f'test-stats-{event_type}')['count']}")
    print_specific_tables_data(db, "stats_bookmark")
    assert es.count(index=f'test-stats-{event_type}')['count'] == 0, "Not all aggregations were deleted"
    assert StatsBookmark.query.filter_by(source_id=f'{event_type}-agg').count() == 0, "Not all bookmarks were deleted"

    # Regenerate aggregations for next tests
    for days in range(10):
        with freeze_time(base_time + timedelta(days=days)):
            setup_elasticsearch_events(es, event_type, base_time + timedelta(days=days), count=5)
            aggregator.run()
    
    current_search.flush_and_refresh(index='*')

    # Test Case 2: Delete using start_date
    print(f"Count before delete: {es.count(index=f'test-stats-{event_type}')['count']}")
    print_specific_tables_data(db, "stats_bookmark")
    
    start_date = base_time + timedelta(days=5)
    aggregator.delete(start_date=start_date)
    current_search.flush_and_refresh(index='*')

    print(f"Count after delete: {es.count(index=f'test-stats-{event_type}')['count']}")
    print_specific_tables_data(db, "stats_bookmark")
    remaining_aggs = es.search(index=f'test-stats-{event_type}')['hits']['hits']
    assert all(agg['_source']['timestamp'] < start_date.isoformat() for agg in remaining_aggs), "Aggregations after start_date were not deleted"
    
    remaining_bookmarks = StatsBookmark.query.filter_by(source_id=f'{event_type}-agg').all()
    assert all(bookmark.date < start_date for bookmark in remaining_bookmarks), "Bookmarks after start_date were not deleted"

    # Test Case 3: Delete using end_date
    print(f"Count before delete: {es.count(index=f'test-stats-{event_type}')['count']}")
    print_specific_tables_data(db, "stats_bookmark")
    end_date = base_time + timedelta(days=3)
    aggregator.delete(end_date=end_date)
    current_search.flush_and_refresh(index='*')

    print(f"Count after delete: {es.count(index=f'test-stats-{event_type}')['count']}")
    print_specific_tables_data(db, "stats_bookmark")
    remaining_aggs = es.search(index=f'test-stats-{event_type}')['hits']['hits']
    assert all(agg['_source']['timestamp'] > end_date.isoformat() for agg in remaining_aggs), "Aggregations before end_date were not deleted"
    
    remaining_bookmarks = StatsBookmark.query.filter_by(source_id=f'{event_type}-agg').all()
    assert all(bookmark.date > end_date for bookmark in remaining_bookmarks), "Bookmarks before end_date were not deleted"

    # Test Case 4: Delete using both start_date and end_date
    print(f"Count before delete: {es.count(index=f'test-stats-{event_type}')['count']}")
    print_specific_tables_data(db, "stats_bookmark")
    start_date = base_time + timedelta(days=1)
    end_date = base_time + timedelta(days=8)
    aggregator.delete(start_date=start_date, end_date=end_date)
    current_search.flush_and_refresh(index='*')

    print(f"Count after delete: {es.count(index=f'test-stats-{event_type}')['count']}")
    print_specific_tables_data(db, "stats_bookmark")
    remaining_aggs = es.search(index=f'test-stats-{event_type}')['hits']['hits']
    assert all(agg['_source']['timestamp'] < start_date.isoformat() or agg['_source']['timestamp'] > end_date.isoformat() for agg in remaining_aggs), "Aggregations within specified range were not deleted"
    
    remaining_bookmarks = StatsBookmark.query.filter_by(source_id=f'{event_type}-agg').all()
    assert all(bookmark.date < start_date or bookmark.date > end_date for bookmark in remaining_bookmarks), "Bookmarks within specified range were not deleted"