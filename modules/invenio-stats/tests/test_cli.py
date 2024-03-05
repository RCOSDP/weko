# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""CLI tests."""

import datetime

import pytest
from mock import patch
from click.testing import CliRunner
from tests.conftest import _create_file_download_event, _create_record_view_event
from elasticsearch_dsl import Search

from invenio_stats import current_stats
from invenio_stats.cli import stats

# def _events_process(event_types=None, eager=False):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_cli.py::test_events_process -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_events_process(app, script_info, es, event_queues):
    """Test "events process" CLI command."""
    search = Search(using=es)
    runner = CliRunner()

    # Invalid argument
    result = runner.invoke(
        stats, ['events', 'process', 'invalid-event-type', '--eager'],
        obj=script_info)
    assert result.exit_code == 2
    assert 'Invalid event type(s):' in result.output

    current_stats.publish(
        'file-download',
        [_create_file_download_event(date) for date in
         [(2018, 1, 1, 10), (2018, 1, 1, 12), (2018, 1, 1, 14)]])
    current_stats.publish(
        'record-view',
        [_create_record_view_event(date) for date in
         [(2018, 1, 1, 10), (2018, 1, 1, 12), (2018, 1, 1, 14)]])

    result = runner.invoke(
        stats, ['events', 'process', 'file-download', '--eager'],
        obj=script_info)
    assert result.exit_code == 0

    es.indices.refresh(index='test-*')

    assert not es.indices.exists('events-stats-record-view-2018-01-01')
    assert not es.indices.exists_alias(name='events-stats-record-view')

    result = runner.invoke(
        stats, ['events', 'process', 'record-view', '--eager'],
        obj=script_info)
    assert result.exit_code == 0

    es.indices.refresh(index='test-*')

    # Create some more events
    current_stats.publish(
        'file-download', [_create_file_download_event((2018, 2, 1, 12))])
    current_stats.publish(
        'record-view', [_create_record_view_event((2018, 2, 1, 10))])

    # Process all event types via a celery task
    result = runner.invoke(
        stats, ['events', 'process'], obj=script_info)
    assert result.exit_code == 0

    es.indices.refresh(index='test-*')

# def _events_delete(event_types, start_date, end_date, force, verbose):
# def _events_restore(event_types, start_date, end_date, force, verbose):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_cli.py::test_events_delete_restore -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_events_delete_restore(app, script_info, es, event_queues):
    search = Search(using=es)
    runner = CliRunner()

    current_stats.publish(
        'file-download',
        [_create_file_download_event(date) for date in
         [(2018, 1, 1, 10), (2018, 1, 2, 12), (2018, 1, 3, 14)]])
    current_stats.publish(
        'record-view',
        [_create_record_view_event(date) for date in
         [(2018, 1, 1, 10), (2018, 1, 2, 12), (2018, 1, 3, 14)]])

    result = runner.invoke(
        stats, ['events', 'delete', 'file-download', '--start-date=2018-01-01', '--end-date=2018-01-02', '--force', '--verbose', '--yes-i-know'],
        obj=script_info)
    assert result
    result = runner.invoke(
        stats, ['events', 'restore', 'file-download', '--start-date=2018-01-01', '--end-date=2018-01-02', '--force', '--verbose'],
        obj=script_info)
    assert result

# def _aggregations_process(aggregation_types=None, start_date=None, end_date=None, update_bookmark=False, eager=False):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_cli.py::test_aggregations_process -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
@pytest.mark.parametrize('indexed_file_download_events',
                         [dict(file_number=1,
                               event_number=1,
                               robot_event_number=0,
                               start_date=datetime.date(2018, 1, 1),
                               end_date=datetime.date(2018, 2, 15))],
                         indirect=['indexed_file_download_events'])
def test_aggregations_process(script_info, event_queues, es, indexed_file_download_events):
    """Test "aggregations process" CLI command."""
    search = Search(using=es)
    runner = CliRunner()

    # Invalid argument
    result = runner.invoke(
        stats, ['aggregations', 'process', 'invalid-aggr-type', '--eager'],
        obj=script_info)
    assert result.exit_code == 2
    assert 'Invalid aggregation type(s):' in result.output

    result = runner.invoke(
        stats, ['aggregations', 'process', 'file-download-agg',
                '--start-date=2018-01-01', '--end-date=2018-01-10',
                '--eager'],
        obj=script_info)
    assert result.exit_code == 1

    agg_alias = search.index('stats-file-download')

    es.indices.refresh(index='test-*')

    # Run again over same period, but update the bookmark
    result = runner.invoke(
        stats, ['aggregations', 'process', 'file-download-agg',
                '--start-date=2018-01-01', '--end-date=2018-01-10',
                '--eager', '--update-bookmark'],
        obj=script_info)
    assert result.exit_code == 1

    es.indices.refresh(index='test-*')

    # Run over all the events via celery task
    result = runner.invoke(
        stats, ['aggregations', 'process', 'file-download-agg',
                '--update-bookmark'],
        obj=script_info)
    assert result

    es.indices.refresh(index='test-*')


# def _aggregations_delete(aggregation_types=None, start_date=None, end_date=None):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_cli.py::test_aggregations_delete -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
@pytest.mark.parametrize('aggregated_file_download_events',
                         [dict(file_number=1,
                               event_number=1,
                               robot_event_number=0,
                               start_date=datetime.date(2018, 1, 1),
                               end_date=datetime.date(2018, 1, 31))],
                         indirect=['aggregated_file_download_events'])
def test_aggregations_delete(script_info, event_queues, es, aggregated_file_download_events):
    search = Search(using=es)
    runner = CliRunner()

    es.indices.refresh(index='test-*')
    agg_alias = search.index('stats-file-download')

    result = runner.invoke(
        stats, ['aggregations', 'delete', 'file-download-agg',
                '--start-date=2018-01-01', '--end-date=2018-01-10', '--yes'],
        obj=script_info)
    assert result

    es.indices.refresh(index='test-*')
    agg_alias = search.index('stats-file-download')

    # Delete all aggregations
    result = runner.invoke(
        stats, ['aggregations', 'delete', '--yes'],
        obj=script_info)
    assert result

    es.indices.refresh(index='test-*')
    agg_alias = search.index('stats-file-download')


# def _aggregations_list_bookmarks(aggregation_types=None, start_date=None, end_date=None, limit=None):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_cli.py::test_aggregations_list_bookmarks -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
@pytest.mark.parametrize('aggregated_file_download_events',
                         [dict(file_number=1,
                               event_number=1,
                               robot_event_number=0,
                               start_date=datetime.date(2018, 1, 1),
                               end_date=datetime.date(2018, 1, 31))],
                         indirect=['aggregated_file_download_events'])
def test_aggregations_list_bookmarks(script_info, event_queues, es,
                                     aggregated_file_download_events):
    """Test "aggregations list-bookmarks" CLI command."""
    search = Search(using=es)
    runner = CliRunner()

    es.indices.refresh(index='test-*')
    agg_alias = search.index('stats-file-download')

    result = runner.invoke(
        stats, ['aggregations', 'list-bookmarks', 'file-download-agg'],
        obj=script_info)
    assert result

# def _aggregations_delete_index(aggregation_types=None, bookmark=False, start_date=None, end_date=None, force=False, verbose=False
# def _aggregations_restore(aggregation_types=None, bookmark=False, start_date=None, end_date=None, force=False, verbose=False):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_cli.py::test_aggregations_deleteindex_restore -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_aggregations_deleteindex_restore(app, script_info, event_queues, es):
    search = Search(using=es)
    runner = CliRunner()

    result = runner.invoke(
        stats, ['aggregations', 'delete-index', 'file-download-agg', '--start-date=2018-01-01', '--end-date=2018-01-10', '--force', '--verbose', '--yes-i-know'],
        obj=script_info)
    assert result

    result = runner.invoke(
        stats, ['aggregations', 'restore', 'file-download-agg', '--start-date=2018-01-01', '--end-date=2018-01-10', '--force', '--verbose'],
        obj=script_info)
    assert result


# def _partition_create(year, month):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_cli.py::test_partition_create -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_partition_create(db, script_info, event_queues, es):
    search = Search(using=es)
    runner = CliRunner()

    with patch("invenio_stats.cli.get_stats_events_partition_tables",return_value=['stats_events_202201', 'stats_events_202202']):
        with patch("invenio_stats.cli.make_stats_events_partition_table",return_value='stats_events_202201'):
            result = runner.invoke(
                stats, ['partition', 'create', '2022', '1'],
                obj=script_info)
            assert result

            result = runner.invoke(
                stats, ['partition', 'create', '2022'],
                obj=script_info)
            assert result

            result = runner.invoke(
                stats, ['partition', 'create', '20220', '1'],
                obj=script_info)
            assert result

        with patch("invenio_stats.cli.make_stats_events_partition_table",return_value='stats_events_202203'):
            result = runner.invoke(
                stats, ['partition', 'create', '2022', '3'],
                obj=script_info)
            assert result