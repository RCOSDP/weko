# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Event processor tests."""

import logging
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from dateutil import parser
from time import mktime
from pytz import utc

import pytest
from tests.conftest import _create_file_download_event
from tests.helpers import get_queue_size
from invenio_queues.proxies import current_queues
from invenio_search import current_search
from invenio_search.engine import dsl

from invenio_stats.contrib.event_builders import (
    build_file_unique_id,
    file_download_event_builder,
)
from invenio_stats.processors import (
    EventsIndexer,
    anonymize_user,
    flag_machines,
    flag_robots,
    hash_id,
)
from invenio_stats.proxies import current_stats
from invenio_stats.tasks import process_events


@pytest.mark.parametrize(
    [
        "ip_addess",
        "user_id",
        "session_id",
        "user_agent",
        "timestamp",
        "exp_country",
        "exp_visitor_id",
        "exp_unique_session_id",
    ],
    [
        # Minimal
        (
            "131.169.180.47",
            None,
            None,
            None,
            datetime(2018, 1, 1, 12),
            "DE",
            "1850abef504ce64cb6b38fa60fe8f90aede1d2d2e9013735554af946",
            "1850abef504ce64cb6b38fa60fe8f90aede1d2d2e9013735554af946",
        ),
        # User id
        (
            "188.184.37.205",
            "100",
            None,
            None,
            datetime(2018, 1, 1, 12),
            "CH",
            "eaf6a44a598ea63c659e6e46722e2d11d0d7487694ec504ade273b9d",
            "c6b85f117cd0636a07f1cf250a30d86714ec45e55a1110441d1a9e2b",
        ),
        # User id + session id + user agent, different IP address
        (
            "23.22.39.120",
            "100",
            "foo",
            "bar",
            datetime(2018, 1, 1, 12),
            "US",
            "eaf6a44a598ea63c659e6e46722e2d11d0d7487694ec504ade273b9d",
            "c6b85f117cd0636a07f1cf250a30d86714ec45e55a1110441d1a9e2b",
        ),
        # User id, different hour
        (
            "23.22.39.120",
            "100",
            None,
            None,
            datetime(2018, 1, 1, 15),
            "US",
            "eaf6a44a598ea63c659e6e46722e2d11d0d7487694ec504ade273b9d",
            "77536991d991e6e8251999fc6a8d78ec1be42847da3c8774221a03a0",
        ),
        # User id, same hour different minute
        (
            "23.22.39.120",
            "100",
            None,
            None,
            datetime(2018, 1, 1, 15, 30),
            "US",
            "eaf6a44a598ea63c659e6e46722e2d11d0d7487694ec504ade273b9d",
            "77536991d991e6e8251999fc6a8d78ec1be42847da3c8774221a03a0",
        ),
        # Session id
        (
            "131.169.180.47",
            None,
            "foo",
            None,
            datetime(2018, 1, 1, 12),
            "DE",
            "a78cc092c88fb4d060a873217f2cd466c2776f672a99ee06317c2858",
            "ca28702a6ece34d18c6f6498ef79d77492a6bd653ac886beb5018880",
        ),
        # Session id + user agent
        (
            "131.169.180.47",
            None,
            "foo",
            "bar",
            datetime(2018, 1, 1, 12),
            "DE",
            "a78cc092c88fb4d060a873217f2cd466c2776f672a99ee06317c2858",
            "ca28702a6ece34d18c6f6498ef79d77492a6bd653ac886beb5018880",
        ),
        # Session id + user agent + different hour
        (
            "131.169.180.47",
            None,
            "foo",
            "bar",
            datetime(2018, 1, 1, 15),
            "DE",
            "a78cc092c88fb4d060a873217f2cd466c2776f672a99ee06317c2858",
            "ceb752c8b51c8c4a9c18a9d4404e9fb570fbf83195631ab3efb46b31",
        ),
        # User agent
        (
            "188.184.37.205",
            None,
            None,
            "bar",
            datetime(2018, 1, 1, 12),
            "CH",
            "e9c48686d21c21a9ee5b9eba58b1d86c9460272809b6de71649f6ce7",
            "e9c48686d21c21a9ee5b9eba58b1d86c9460272809b6de71649f6ce7",
        ),
        # Differnet ip address
        (
            "131.169.180.47",
            None,
            None,
            "bar",
            datetime(2018, 1, 1, 12),
            "DE",
            "602e9bc738b422d5a19283e20fc31ec540a12d42b04ad7073d943fb2",
            "602e9bc738b422d5a19283e20fc31ec540a12d42b04ad7073d943fb2",
        ),
        # Different hour
        (
            "131.169.180.47",
            None,
            None,
            "bar",
            datetime(2018, 1, 1, 15),
            "DE",
            "4b30c060f422f304b073759553d4161a14784e0ddcf57284f55d7cae",
            "4b30c060f422f304b073759553d4161a14784e0ddcf57284f55d7cae",
        ),
        # No result ip address
        (
            "0.0.0.0",
            None,
            None,
            None,
            datetime(2018, 1, 1, 12),
            None,
            "1850abef504ce64cb6b38fa60fe8f90aede1d2d2e9013735554af946",
            "1850abef504ce64cb6b38fa60fe8f90aede1d2d2e9013735554af946",
        ),
    ],
)
def test_anonymize_user(
    mock_anonymization_salt,
    ip_addess,
    user_id,
    session_id,
    user_agent,
    timestamp,
    exp_country,
    exp_visitor_id,
    exp_unique_session_id,
):
    """Test anonymize_user preprocessor."""
    event = anonymize_user(
        {
            "ip_address": ip_addess,
            "user_id": user_id,
            "session_id": session_id,
            "user_agent": user_agent,
            "timestamp": timestamp.isoformat(),
        }
    )
    assert "user_id" not in event
    assert "user_agent" not in event
    assert "ip_address" not in event
    assert "session_id" not in event
    assert event["country"] == exp_country
    assert event["visitor_id"] == exp_visitor_id
    assert event["unique_session_id"] == exp_unique_session_id


def test_anonymiation_salt(app):
    """Test anonymization salt for different days."""
    with app.app_context():
        event = anonymize_user(
            {
                "ip_address": "131.169.180.47",
                "user_id": "100",
                "timestamp": datetime(2018, 1, 1, 12).isoformat(),
            }
        )
        event_same_day = anonymize_user(
            {
                "ip_address": "131.169.180.47",
                "user_id": "100",
                "timestamp": datetime(2018, 1, 1, 21).isoformat(),
            }
        )
        event_other_day = anonymize_user(
            {
                "ip_address": "131.169.180.47",
                "user_id": "100",
                "timestamp": datetime(2018, 1, 2, 12).isoformat(),
            }
        )

        # Same user, same day -> identical visitor id
        assert event["visitor_id"] == event_same_day["visitor_id"]
        # Same user, same day, different hour -> different unique session id
        assert event["unique_session_id"] != event_same_day["unique_session_id"]
        # Same user, different day -> different visitor id
        assert event["visitor_id"] != event_other_day["visitor_id"]
        # Same user, different day and hour -> different unique session id
        assert event["unique_session_id"] != event_other_day["unique_session_id"]


def test_flag_robots(app, mock_user_ctx, request_headers, objects):
    with app.app_context():
        """Test flag_robots preprocessor."""

        def build_event(headers):
            with app.test_request_context(headers=headers):
                event = file_download_event_builder({}, app, objects[0])
            return flag_robots(event)

        assert build_event(request_headers["user"])["is_robot"] is False
        assert build_event(request_headers["machine"])["is_robot"] is False
        assert build_event(request_headers["robot"])["is_robot"] is True


def test_flag_machines(app, mock_user_ctx, request_headers, objects):
    with app.app_context():
        """Test machines preprocessor."""

        def build_event(headers):
            with app.test_request_context(headers=headers):
                event = file_download_event_builder({}, app, objects[0])
            return flag_machines(event)

        assert build_event(request_headers["user"])["is_machine"] is False
        assert build_event(request_headers["robot"])["is_machine"] is False
        assert build_event(request_headers["machine"])["is_machine"] is True


def test_referrer(app, mock_user_ctx, request_headers, objects):
    with app.app_context():
        """Test referrer header."""
        request_headers["user"]["REFERER"] = "example.com"
        with app.test_request_context(headers=request_headers["user"]):
            event = file_download_event_builder({}, app, objects[0])
        assert event["referrer"] == "example.com"


def test_events_indexer_preprocessors(app, mock_event_queue):
    """Check that EventsIndexer calls properly the preprocessors."""

    def test_preprocessor1(event):
        event["test1"] = 42
        event["visitor_id"] = "testuser1"
        return event

    def test_preprocessor2(event):
        event["test2"] = 21
        return event

    indexer = EventsIndexer(
        mock_event_queue,
        preprocessors=[build_file_unique_id, test_preprocessor1, test_preprocessor2],
    )

    # Generate the events
    received_docs = []

    def bulk(client, generator, *args, **kwargs):
        received_docs.extend(generator)

    with patch("invenio_stats.processors.datetime", mock_date(2017, 6, 2, 12)):
        with patch("invenio_search.engine.search.helpers.bulk", side_effect=bulk):
            indexer.run()

    # Process the events as we expect them to be
    expected_docs = []
    for event in mock_event_queue.queued_events:
        event = build_file_unique_id(event)
        event = test_preprocessor1(event)
        event = test_preprocessor2(event)
        event["updated_timestamp"] = "2017-06-02T12:00:00"
        _id = hash_id("2017-01-01T00:00:00", event)
        expected_docs.append(
            {
                "_id": _id,
                "_op_type": "index",
                "_index": "events-stats-file-download-2017-01",
                "_source": event,
            }
        )
    assert len(received_docs) == 100


def test_events_indexer_id_windowing(app, mock_event_queue):
    """Check that EventsIndexer applies time windows to ids."""

    indexer = EventsIndexer(mock_event_queue, preprocessors=[], double_click_window=180)

    # Generated docs will be registered in this list
    received_docs = []

    def bulk(client, generator, *args, **kwargs):
        received_docs.extend(generator)

    mock_event_queue.consume.return_value = [
        _create_file_download_event(date)
        for date in [
            # Those two events will be in the same window
            (2017, 6, 1, 0, 11, 3),
            (2017, 6, 1, 0, 9, 1),
            # Those two events will be in the same window
            (2017, 6, 2, 0, 12, 10),
            (2017, 6, 2, 0, 13, 3),
            (2017, 6, 2, 0, 30, 3),
        ]
    ]

    with patch("invenio_search.engine.search.helpers.bulk", side_effect=bulk):
        indexer.run()

    assert len(received_docs) == 5
    ids = set(doc["_id"] for doc in received_docs)
    assert len(ids) == 3


def test_double_clicks(app, mock_event_queue, es):
    """Test that events occurring within a time window are counted as 1."""
    event_type = "file-download"
    events = [
        _create_file_download_event(date)
        for date in [
            (2000, 6, 1, 10, 0, 10),
            (2000, 6, 1, 10, 0, 11),
            (2000, 6, 1, 10, 0, 19),
            (2000, 6, 1, 10, 0, 22),
        ]
    ]
    current_queues.declare()
    current_stats.publish(event_type, events)
    process_events(["file-download"])
    current_search.flush_and_refresh(index="*")
    res = es.search(
        index='test-events-stats-file-download-0001',
    )
    assert res["hits"]["total"]["value"] == 2


@pytest.mark.skip('This test dont ever finish')
def test_failing_processors(app, es, event_queues, caplog):
    """Test events that raise an exception when processed."""
    search_obj = dsl.Search(using=es)

    current_queues.declare()
    current_stats.publish(
        "file-download",
        [
            _create_file_download_event(date)
            for date in [(2018, 1, 1), (2018, 1, 2), (2018, 1, 3), (2018, 1, 4)]
        ],
    )

    def _raises_on_second_call(doc):
        if _raises_on_second_call.calls == 1:
            _raises_on_second_call.calls += 1
            raise Exception("mocked-exception")
        _raises_on_second_call.calls += 1
        return doc

    _raises_on_second_call.calls = 0

    queue = current_queues.queues["stats-file-download"]
    indexer = EventsIndexer(queue, preprocessors=[_raises_on_second_call])

    current_search.flush_and_refresh(index="*")
    assert get_queue_size("stats-file-download") == 4
    assert not es.indices.exists("events-stats-file-download-2018-01")
    assert not es.indices.exists("events-stats-file-download-2018-01")
    assert not es.indices.exists("events-stats-file-download-2018-01")
    assert not es.indices.exists("events-stats-file-download-2018-01")
    assert not es.indices.exists_alias(name="events-stats-file-download")

    with caplog.at_level(logging.ERROR):
        indexer.run()  # 2nd event raises exception and is dropped

    # Check that the error was logged
    error_logs = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(error_logs) == 1
    assert error_logs[0].msg == "Error while processing event"
    assert error_logs[0].exc_info[1].args[0] == "mocked-exception"

    current_search.flush_and_refresh(index="*")
    assert get_queue_size("stats-file-download") == 0
    assert search_obj.index("events-stats-file-download").count() == 3
    assert search_obj.index("events-stats-file-download-2018-01").count() == 3


def test_events_indexer_actionsiter(app, mock_event_queue, caplog):
    def preprocessor_1(msg):
        msg['preprocessed_1'] = True
        return msg

    def preprocessor_2(msg):
        if msg.get('filter_out'):
            return None
        if msg.get('raise_exception'):
            raise Exception("Test exception")
        msg['preprocessed_2'] = True
        return msg

    indexer_with_window = EventsIndexer(
        mock_event_queue,
        preprocessors=[preprocessor_1, preprocessor_2],
        double_click_window=10
    )

    indexer_without_window = EventsIndexer(
        mock_event_queue,
        preprocessors=[preprocessor_1, preprocessor_2],
        double_click_window=0
    )

    mock_messages = [
        {"timestamp": "2023-09-13T10:00:00", "event_type": "file-download", "file_id": "123", "user_id": "user1", "unique_id": "unique1"},
        {"timestamp": "2023-09-13T10:00:05", "event_type": "file-download", "file_id": "123", "user_id": "user2", "filter_out": True, "unique_id": "unique2"},
        {"timestamp": "2023-09-13T10:00:10", "event_type": "file-download", "file_id": "124", "user_id": "user3", "unique_id": "unique3"},
        {"timestamp": "2023-09-13T10:00:15", "event_type": "file-download", "file_id": "125", "user_id": "user4", "unique_id": "unique4", "raise_exception": True}
    ]
    mock_event_queue.consume.return_value = mock_messages

    with patch('invenio_stats.processors.datetime') as mock_datetime, \
         patch('invenio_stats.processors.current_app') as mock_app, \
         patch('invenio_stats.processors.mktime') as mock_mktime, \
         patch('invenio_stats.processors.utc') as mock_utc, \
         patch('invenio_stats.processors.StatsEvents.save') as mock_db_save:

        mock_datetime.now.return_value = datetime(2023, 9, 13, 10, 1, 0, tzinfo=timezone.utc)
        mock_mktime.return_value = 1234567890.0
        mock_utc.localize.return_value = datetime(2023, 9, 13, 10, 0, 0, tzinfo=timezone.utc)

        # Test with STATS_WEKO_DB_BACKUP_EVENTS = False
        mock_app.config = {'STATS_WEKO_DB_BACKUP_EVENTS': False}
        actions_with_window = list(indexer_with_window.actionsiter())
        actions_without_window = list(indexer_without_window.actionsiter())

        # Verify that StatsEvents.save was not called
        mock_db_save.assert_not_called()

        # Test with STATS_WEKO_DB_BACKUP_EVENTS = True
        mock_app.config = {'STATS_WEKO_DB_BACKUP_EVENTS': True}
        actions_with_backup = list(indexer_with_window.actionsiter())

        # Verify that StatsEvents.save was called
        mock_db_save.assert_called()

    # Common assertions
    # Check if the correct number of actions were generated
    assert len(actions_with_window) == 2, "Expected 2 actions"

    # Verify preprocessor execution
    assert 'preprocessed_1' in actions_with_window[0]['_source']
    assert 'preprocessed_2' in actions_with_window[0]['_source']
    assert actions_with_window[1]['_source'].get('preprocessed_2') == True

    # Check if filtered messages are skipped
    assert not any(action['_source']['unique_id'] == 'unique2' for action in actions_with_window), "Message with 'filter_out' should be skipped"

    # Verify timestamp handling
    assert actions_with_window[0]['_source']['timestamp'] == "2023-09-13T10:00:00"
    assert actions_with_window[0]['_source']['updated_timestamp'] == "2023-09-13T10:01:00+00:00"

    # Check action properties
    for action in actions_with_window:
        assert action['_op_type'] == 'index', "Operation type should be 'index'"
        assert action['_index'].endswith('file-download'), "Index should be related to 'file-download'"
        assert 'file_id' in action['_source'], "Source should contain 'file_id'"
        assert action['_source']['event_type'] == 'file-download', "Event type should match the routing key"

    # Test empty queue
    mock_event_queue.consume.return_value = []
    assert list(indexer_with_window.actionsiter()) == [], "Empty queue should return no actions"

    # Verify that actions are the same with and without database backup
    assert actions_with_window == actions_with_backup, "Database backup should not affect action generation"

    print("All assertions passed. EventsIndexer actionsiter functionality verified.")


def test_events_indexer_run(app, es):
    """
    Test the EventsIndexer run functionality,
    ensuring correct indexing and processing of events for different event types.
    """

    # Skip database operation
    with patch.dict(app.config, {'STATS_WEKO_DB_BACKUP_EVENTS': False}):
        es_client = es
        double_click_window = 30

        event_types = ['celery-task', 'item-create', 'top-view', 'record-view', 'file-download', 'file-preview', 'search']

        for et_index, event_type in enumerate(event_types):
            # Create separate event queue for each event_type
            mock_events = []
            routing_key = f"stats-{event_type}"
            base_time = datetime(2023, 1 + et_index, 1, 12, 0, 0)

            for i in range(10):
                event = {
                    "timestamp": (base_time + timedelta(seconds=i*10)).replace(microsecond=0).replace(tzinfo=None).isoformat(),
                    "event_type": event_type,
                    "file_id": f"file_{event_type}",
                    "user_id": f"user_{event_type}",
                    "visitor_id": f"visitor_{event_type}",
                    "unique_id": f"unique_{event_type}",
                }
                mock_events.append(event)

            # Create separate mock_event_queue for each event_type
            type_specific_mock_queue = MagicMock()
            type_specific_mock_queue.consume.return_value = mock_events
            type_specific_mock_queue.routing_key = routing_key

            # Initialize EventsIndexer
            indexer = EventsIndexer(type_specific_mock_queue, double_click_window=double_click_window, client=es_client)

            # Run the indexer
            success, failed = indexer.run()

            # Assert bulk indexing operation success
            assert success == 10, f"{event_type}: Expected 10 documents to be indexed successfully, but {success} were indexed"
            assert failed == 0, f"{event_type}: Expected no failed indexing operations, but {failed} failed"

            # Refresh the index
            es_client.indices.refresh(index=indexer.index)

            # Check total document count in the index
            total_docs = es_client.count(index=indexer.index)['count']
            print(f"Total documents in {event_type} index {indexer.index}: {total_docs}")

            # Assert document count (4 due to double click window setting)
            assert total_docs == 4, f"Expected 4 documents due to double click window, but found {total_docs}"

            # Check random documents
            for i in range(10):
                event = mock_events[i]
                original_ts = parser.parse(event["timestamp"]).replace(tzinfo=None)

                if double_click_window > 0:
                    timestamp = mktime(utc.localize(original_ts).utctimetuple())
                    processed_ts = datetime.fromtimestamp(
                        timestamp // indexer.double_click_window * indexer.double_click_window
                    )
                else:
                    processed_ts = original_ts

                event_id = hash_id(processed_ts.isoformat(), event)

                try:
                    doc = es_client.get(index=indexer.index, id=event_id)
                    print(f"{event_type} document {event_id} content: {doc}")

                    # Assert document is indexed
                    assert doc['found'] is True, f"{event_type}: Document {event_id} should be indexed"

                    source = doc['_source']
                    # Assert event_type matches
                    assert source['event_type'] == event_type, f"{event_type}: Document {event_id} 'event_type' mismatch"

                    # Verify other fields
                    expected_fields = ['timestamp', 'file_id', 'visitor_id', 'unique_id', 'is_robot', 'unique_session_id', 'updated_timestamp']
                    for field in expected_fields:
                        assert field in source, f"{event_type}: Document {event_id} should contain '{field}' field"

                except Exception as e:
                    pytest.fail(f"{event_type}: Error checking document {event_id}: {str(e)}")

