# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Event processor tests."""

import logging
from datetime import datetime

import pytest
from tests.conftest import _create_file_download_event
from elasticsearch_dsl import Search
from tests.helpers import get_queue_size
from invenio_queues.proxies import current_queues
from mock import patch

from invenio_stats.contrib.event_builders import build_file_unique_id, \
    file_download_event_builder
from invenio_stats.processors import EventsIndexer, anonymize_user, \
    flag_machines, flag_robots, hash_id
from invenio_stats.proxies import current_stats
from invenio_stats.tasks import process_events


@pytest.mark.parametrize(
    ['ip_addess', 'user_id', 'session_id', 'user_agent', 'timestamp',
     'exp_country', 'exp_visitor_id', 'exp_unique_session_id'],
    [
        # Minimal
        ('131.169.180.47', None, None, None, datetime(2018, 1, 1, 12),
         'DE',
         '1850abef504ce64cb6b38fa60fe8f90aede1d2d2e9013735554af946',
         '1850abef504ce64cb6b38fa60fe8f90aede1d2d2e9013735554af946'),
        # User id
        ('188.184.37.205', '100', None, None, datetime(2018, 1, 1, 12),
         'CH',
         'eaf6a44a598ea63c659e6e46722e2d11d0d7487694ec504ade273b9d',
         'c6b85f117cd0636a07f1cf250a30d86714ec45e55a1110441d1a9e2b'),
        # User id + session id + user agent, different IP address
        ('23.22.39.120', '100', 'foo', 'bar', datetime(2018, 1, 1, 12),
         'US',
         'eaf6a44a598ea63c659e6e46722e2d11d0d7487694ec504ade273b9d',
         'c6b85f117cd0636a07f1cf250a30d86714ec45e55a1110441d1a9e2b'),
        # User id, different hour
        ('23.22.39.120', '100', None, None, datetime(2018, 1, 1, 15),
         'US',
         'eaf6a44a598ea63c659e6e46722e2d11d0d7487694ec504ade273b9d',
         '77536991d991e6e8251999fc6a8d78ec1be42847da3c8774221a03a0'),
        # User id, same hour different minute
        ('23.22.39.120', '100', None, None, datetime(2018, 1, 1, 15, 30),
         'US',
         'eaf6a44a598ea63c659e6e46722e2d11d0d7487694ec504ade273b9d',
         '77536991d991e6e8251999fc6a8d78ec1be42847da3c8774221a03a0'),
        # Session id
        ('131.169.180.47', None, 'foo', None, datetime(2018, 1, 1, 12),
         'DE',
         'a78cc092c88fb4d060a873217f2cd466c2776f672a99ee06317c2858',
         'ca28702a6ece34d18c6f6498ef79d77492a6bd653ac886beb5018880'),
        # Session id + user agent
        ('131.169.180.47', None, 'foo', 'bar', datetime(2018, 1, 1, 12),
         'DE',
         'a78cc092c88fb4d060a873217f2cd466c2776f672a99ee06317c2858',
         'ca28702a6ece34d18c6f6498ef79d77492a6bd653ac886beb5018880'),
        # Session id + user agent + different hour
        ('131.169.180.47', None, 'foo', 'bar', datetime(2018, 1, 1, 15),
         'DE',
         'a78cc092c88fb4d060a873217f2cd466c2776f672a99ee06317c2858',
         'ceb752c8b51c8c4a9c18a9d4404e9fb570fbf83195631ab3efb46b31'),
        # User agent
        ('188.184.37.205', None, None, 'bar', datetime(2018, 1, 1, 12),
         'CH',
         'e9c48686d21c21a9ee5b9eba58b1d86c9460272809b6de71649f6ce7',
         'e9c48686d21c21a9ee5b9eba58b1d86c9460272809b6de71649f6ce7'),
        # Differnet ip address
        ('131.169.180.47', None, None, 'bar', datetime(2018, 1, 1, 12),
         'DE',
         '602e9bc738b422d5a19283e20fc31ec540a12d42b04ad7073d943fb2',
         '602e9bc738b422d5a19283e20fc31ec540a12d42b04ad7073d943fb2'),
        # Different hour
        ('131.169.180.47', None, None, 'bar', datetime(2018, 1, 1, 15),
         'DE',
         '4b30c060f422f304b073759553d4161a14784e0ddcf57284f55d7cae',
         '4b30c060f422f304b073759553d4161a14784e0ddcf57284f55d7cae'),
        # No result ip address
        ('0.0.0.0', None, None, None, datetime(2018, 1, 1, 12),
         None,
         '1850abef504ce64cb6b38fa60fe8f90aede1d2d2e9013735554af946',
         '1850abef504ce64cb6b38fa60fe8f90aede1d2d2e9013735554af946'),
    ]
)
def test_anonymize_user(mock_anonymization_salt,
                        ip_addess, user_id, session_id, user_agent, timestamp,
                        exp_country, exp_visitor_id, exp_unique_session_id):
    """Test anonymize_user preprocessor."""
    event = anonymize_user({
        'ip_address': ip_addess,
        'user_id': user_id,
        'session_id': session_id,
        'user_agent': user_agent,
        'timestamp': timestamp.isoformat(),
    })
    assert 'user_id' not in event
    assert 'user_agent' not in event
    assert 'ip_address' not in event
    assert 'session_id' not in event
    assert event['country'] == exp_country
    assert event['visitor_id'] == exp_visitor_id
    assert event['unique_session_id'] == exp_unique_session_id


def test_anonymiation_salt(app):
    """Test anonymization salt for different days."""
    event = anonymize_user({
        'ip_address': '131.169.180.47', 'user_id': '100',
        'timestamp': datetime(2018, 1, 1, 12).isoformat(),
    })
    event_same_day = anonymize_user({
        'ip_address': '131.169.180.47', 'user_id': '100',
        'timestamp': datetime(2018, 1, 1, 21).isoformat(),
    })
    event_other_day = anonymize_user({
        'ip_address': '131.169.180.47', 'user_id': '100',
        'timestamp': datetime(2018, 1, 2, 12).isoformat(),
    })

    # Same user, same day -> identical visitor id
    assert event['visitor_id'] == event_same_day['visitor_id']
    # Same user, same day, different hour -> different unique session id
    assert event['unique_session_id'] != event_same_day['unique_session_id']
    # Same user, different day -> different visitor id
    assert event['visitor_id'] != event_other_day['visitor_id']
    # Same user, different day and hour -> different unique session id
    assert event['unique_session_id'] != event_other_day['unique_session_id']


# def test_flag_robots(app, mock_user_ctx, request_headers, objects):
#     """Test flag_robots preprocessor."""
#     def build_event(headers):
#         with app.test_request_context(headers=headers):
#             event = file_download_event_builder({}, app, objects[0])
#         return flag_robots(event)

#     assert build_event(request_headers['user'])['is_robot'] is False
#     assert build_event(request_headers['machine'])['is_robot'] is False
#     assert build_event(request_headers['robot'])['is_robot'] is True


# def test_flag_machines(app, mock_user_ctx, request_headers, objects):
#     """Test machines preprocessor."""
#     def build_event(headers):
#         with app.test_request_context(headers=headers):
#             event = file_download_event_builder({}, app, objects[0])
#         return flag_machines(event)

#     assert build_event(request_headers['user'])['is_machine'] is False
#     assert build_event(request_headers['robot'])['is_machine'] is False
#     assert build_event(request_headers['machine'])['is_machine'] is True


# def test_referrer(app, mock_user_ctx, request_headers, objects):
#     """Test referrer header."""
#     request_headers['user']['REFERER'] = 'example.com'
#     with app.test_request_context(headers=request_headers['user']):
#         event = file_download_event_builder({}, app, objects[0])
#     assert event['referrer'] == 'example.com'


def test_events_indexer_preprocessors(app, mock_event_queue):
    """Check that EventsIndexer calls properly the preprocessors."""
    def test_preprocessor1(event):
        event['test1'] = 42
        event['visitor_id'] = 'testuser1'
        return event

    def test_preprocessor2(event):
        event['test2'] = 21
        return event

    indexer = EventsIndexer(
        mock_event_queue,
        preprocessors=[build_file_unique_id,
                       test_preprocessor1,
                       test_preprocessor2]
    )

    # Generate the events
    received_docs = []

    def bulk(client, generator, *args, **kwargs):
        received_docs.extend(generator)

    with patch('elasticsearch.helpers.bulk', side_effect=bulk):
        indexer.run()

    # Process the events as we expect them to be
    expected_docs = []
    for event in mock_event_queue.queued_events:
        event = build_file_unique_id(event)
        event = test_preprocessor1(event)
        event = test_preprocessor2(event)
        _id = hash_id('2017-01-01T00:00:00', event)
        expected_docs.append(dict(
            _id=_id,
            _op_type='index',
            _index='events-stats-file-download-2017-01-01',
            _type='stats-file-download',
            _source=event,
        ))

    assert len(received_docs) == 100


def test_events_indexer_id_windowing(app, mock_event_queue):
    """Check that EventsIndexer applies time windows to ids."""

    indexer = EventsIndexer(mock_event_queue, preprocessors=[],
                            double_click_window=180)

    # Generated docs will be registered in this list
    received_docs = []

    def bulk(client, generator, *args, **kwargs):
        received_docs.extend(generator)

    mock_event_queue.consume.return_value = [
        _create_file_download_event(date) for date in
        [
            # Those two events will be in the same window
            (2017, 6, 1, 0, 11, 3), (2017, 6, 1, 0, 9, 1),
            # Those two events will be in the same window
            (2017, 6, 2, 0, 12, 10), (2017, 6, 2, 0, 13, 3),
            (2017, 6, 2, 0, 30, 3)
        ]
    ]

    with patch('elasticsearch.helpers.bulk', side_effect=bulk):
        indexer.run()

    assert len(received_docs) == 5
    ids = set(doc['_id'] for doc in received_docs)
    assert len(ids) == 3


def test_double_clicks(app, mock_event_queue, es):
    """Test that events occurring within a time window are counted as 1."""
    event_type = 'file-download'
    events = [_create_file_download_event(date) for date in
              [(2000, 6, 1, 10, 0, 10),
               (2000, 6, 1, 10, 0, 11),
               (2000, 6, 1, 10, 0, 19),
               (2000, 6, 1, 10, 0, 22)]]
    current_queues.declare()
    current_stats.publish(event_type, events)
    process_events(['file-download'])
    es.indices.refresh(index='*')
    res = es.search(
        index='test-events-stats-file-download-0001',
    )
    assert res['hits']['total'] == 2


@pytest.mark.skip('This test dont ever finish')
def test_failing_processors(app, event_queues, es_with_templates, caplog):
    """Test events that raise an exception when processed."""
    es = es_with_templates
    search = Search(using=es)

    current_queues.declare()
    current_stats.publish(
        'file-download',
        [_create_file_download_event(date) for date in
         [(2018, 1, 1), (2018, 1, 2), (2018, 1, 3), (2018, 1, 4)]])

    def _raises_on_second_call(doc):
        if _raises_on_second_call.calls == 1:
            _raises_on_second_call.calls += 1
            raise Exception('mocked-exception')
        _raises_on_second_call.calls += 1
        return doc
    _raises_on_second_call.calls = 0

    queue = current_queues.queues['stats-file-download']
    indexer = EventsIndexer(queue, preprocessors=[_raises_on_second_call])

    assert get_queue_size('stats-file-download') == 4
    assert not es.indices.exists('events-stats-file-download-2018-01-01')
    assert not es.indices.exists('events-stats-file-download-2018-01-02')
    assert not es.indices.exists('events-stats-file-download-2018-01-03')
    assert not es.indices.exists('events-stats-file-download-2018-01-04')
    assert not es.indices.exists_alias(name='events-stats-file-download')

    with caplog.at_level(logging.ERROR):
        indexer.run()  # 2nd event raises exception and is dropped

    # Check that the error was logged
    error_logs = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(error_logs) == 1
    assert error_logs[0].msg == 'Error while processing event'
    assert error_logs[0].exc_info[1].args[0] == 'mocked-exception'

    es.indices.refresh(index='*')
    assert get_queue_size('stats-file-download') == 0
    assert search.index('events-stats-file-download').count() == 3
    assert search.index('events-stats-file-download-2018-01-01').count() == 1
    assert not es.indices.exists('events-stats-file-download-2018-01-02')
    assert search.index('events-stats-file-download-2018-01-03').count() == 1
    assert search.index('events-stats-file-download-2018-01-04').count() == 1
