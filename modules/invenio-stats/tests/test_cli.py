# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""CLI tests."""

import datetime
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from conftest import _create_file_download_event, _create_record_view_event
from helpers import mock_date
from invenio_search import current_search
from invenio_search.engine import dsl

from invenio_stats import current_stats
from invenio_stats.cli import stats


def test_events_process(search_clear, script_info, event_queues):
    """Test "events process" CLI command."""
    search_obj = dsl.Search(using=search_clear)
    runner = CliRunner()

    # Invalid argument
    result = runner.invoke(
        stats, ["events", "process", "invalid-event-type", "--eager"], obj=script_info
    )
    assert result.exit_code == 2
    assert "Invalid event type(s):" in result.output

    current_stats.publish(
        "file-download",
        [
            _create_file_download_event(date)
            for date in [(2018, 1, 1, 10), (2018, 1, 1, 12), (2018, 1, 1, 14)]
        ],
    )
    current_stats.publish(
        "record-view",
        [
            _create_record_view_event(date)
            for date in [(2018, 1, 1, 10), (2018, 1, 1, 12), (2018, 1, 1, 14)]
        ],
    )

    result = runner.invoke(
        stats, ["events", "process", "file-download", "--eager"], obj=script_info
    )
    assert result.exit_code == 0

    current_search.flush_and_refresh(index="*")

    assert search_obj.index("events-stats-file-download-2018-01").count() == 3
    assert search_obj.index("events-stats-file-download").count() == 3
    assert not search_clear.indices.exists("events-stats-record-view-2018-01")
    assert not search_clear.indices.exists_alias(name="events-stats-record-view")

    result = runner.invoke(
        stats, ["events", "process", "record-view", "--eager"], obj=script_info
    )
    assert result.exit_code == 0

    current_search.flush_and_refresh(index="*")
    assert search_obj.index("events-stats-file-download-2018-01").count() == 3
    assert search_obj.index("events-stats-file-download").count() == 3
    assert search_obj.index("events-stats-record-view-2018-01").count() == 3
    assert search_obj.index("events-stats-record-view").count() == 3

    # Create some more events
    current_stats.publish(
        "file-download", [_create_file_download_event((2018, 2, 1, 12))]
    )
    current_stats.publish("record-view", [_create_record_view_event((2018, 2, 1, 10))])

    current_search.flush_and_refresh(index="*")
    # Process all event types via a celery task
    result = runner.invoke(stats, ["events", "process"], obj=script_info)
    assert result.exit_code == 0

    current_search.flush_and_refresh(index="*")
    assert search_obj.index("events-stats-file-download-2018-01").count() == 3
    assert search_obj.index("events-stats-file-download-2018-02").count() == 1
    assert search_obj.index("events-stats-file-download").count() == 4
    assert search_obj.index("events-stats-record-view-2018-01").count() == 3
    assert search_obj.index("events-stats-record-view-2018-02").count() == 1
    assert search_obj.index("events-stats-record-view").count() == 4


@pytest.mark.parametrize(
    "indexed_events",
    [
        {
            "file_number": 1,
            "event_number": 1,
            "robot_event_number": 0,
            "start_date": datetime.date(2018, 1, 1),
            "end_date": datetime.date(2018, 2, 15),
        }
    ],
    indirect=["indexed_events"],
)
def test_aggregations_process(script_info, event_queues, search_clear, indexed_events):
    """Test "aggregations process" CLI command."""
    search_obj = dsl.Search(using=search_clear)
    runner = CliRunner()

    # Invalid argument
    result = runner.invoke(
        stats,
        ["aggregations", "process", "invalid-aggr-type", "--eager"],
        obj=script_info,
    )
    assert result.exit_code == 2
    assert "Invalid aggregation type(s):" in result.output

    result = runner.invoke(
        stats,
        [
            "aggregations",
            "process",
            "file-download-agg",
            "--start-date=2018-01-01",
            "--end-date=2018-01-10",
            "--eager",
        ],
        obj=script_info,
    )
    assert result.exit_code == 0

    agg_alias = search_obj.index("stats-file-download")

    current_search.flush_and_refresh(index="*")
    assert agg_alias.count() == 10
    assert search_clear.indices.exists(
        "stats-bookmarks"
    )  # the bookmark indexed is created
    assert (
        search_obj.index("stats-bookmarks").count() == 0
    )  # And it should not have any entries
    assert search_obj.index("stats-file-download-2018-01").count() == 10

    # Run again over same period, but update the bookmark
    result = runner.invoke(
        stats,
        [
            "aggregations",
            "process",
            "file-download-agg",
            "--start-date=2018-01-01",
            "--end-date=2018-01-10",
            "--eager",
            "--update-bookmark",
        ],
        obj=script_info,
    )
    assert result.exit_code == 0

    current_search.flush_and_refresh(index="*")
    assert agg_alias.count() == 10
    assert search_obj.index("stats-file-download-2018-01").count() == 10
    assert (
        search_obj.index("stats-bookmarks").count() == 1
    )  # There is a single bookmark per run

    # Run over all the events via celery task
    with patch("invenio_stats.aggregations.datetime", mock_date(2018, 2, 15)):
        result = runner.invoke(
            stats,
            ["aggregations", "process", "file-download-agg", "--update-bookmark"],
            obj=script_info,
        )
        assert result.exit_code == 0

    current_search.flush_and_refresh(index="*")
    assert agg_alias.count() == 46
    assert (
        search_obj.index("stats-bookmarks").count() == 2
    )  # This time there are two, since we had two different dates
    assert search_obj.index("stats-file-download-2018-01").count() == 31
    assert search_obj.index("stats-file-download-2018-02").count() == 15


@pytest.mark.parametrize(
    "aggregated_events",
    [
        {
            "file_number": 1,
            "event_number": 1,
            "robot_event_number": 0,
            "start_date": datetime.date(2018, 1, 1),
            "end_date": datetime.date(2018, 1, 31),
        }
    ],
    indirect=["aggregated_events"],
)
def test_aggregations_delete(
    script_info, event_queues, search_clear, aggregated_events
):
    """Test "aggregations process" CLI command."""
    search_obj = dsl.Search(using=search_clear)
    runner = CliRunner()

    current_search.flush_and_refresh(index="*")
    agg_alias = search_obj.index("stats-file-download")
    assert agg_alias.count() == 31
    assert (
        search_obj.index("stats-bookmarks").count() == 1
    )  # There is a single bookmark per run
    assert search_obj.index("stats-file-download-2018-01").count() == 31

    result = runner.invoke(
        stats,
        [
            "aggregations",
            "delete",
            "file-download-agg",
            "--start-date=2018-01-01",
            "--end-date=2018-01-10",
            "--yes",
        ],
        obj=script_info,
    )
    assert result.exit_code == 0

    current_search.flush_and_refresh(index="*")
    agg_alias = search_obj.index("stats-file-download")

    assert agg_alias.count() == 21
    assert search_obj.index("stats-bookmarks").count() == 1
    assert search_obj.index("stats-file-download-2018-01").count() == 21

    # Delete all aggregations
    result = runner.invoke(
        stats, ["aggregations", "delete", "file-download-agg", "--yes"], obj=script_info
    )
    assert result.exit_code == 0

    current_search.flush_and_refresh(index="*")
    agg_alias = search_obj.index("stats-file-download")
    assert agg_alias.count() == 0
    assert search_obj.index("stats-file-download-2018-01").count() == 0


@pytest.mark.parametrize(
    "aggregated_events",
    [
        {
            "file_number": 1,
            "event_number": 1,
            "robot_event_number": 0,
            "start_date": datetime.date(2018, 1, 1),
            "end_date": datetime.date(2018, 1, 31),
        }
    ],
    indirect=["aggregated_events"],
)
def test_aggregations_list_bookmarks(
    script_info, event_queues, search_clear, aggregated_events
):
    """Test "aggregations list-bookmarks" CLI command."""
    search_obj = dsl.Search(using=search_clear)
    runner = CliRunner()

    current_search.flush_and_refresh(index="*")
    agg_alias = search_obj.index("stats-file-download")
    assert agg_alias.count() == 31
    assert search_obj.index("stats-bookmarks").count() == 1
    assert search_obj.index("stats-file-download-2018-01").count() == 31

    bookmarks = [b.date for b in search_obj.index("stats-bookmarks").scan()]

    result = runner.invoke(
        stats,
        ["aggregations", "list-bookmarks", "file-download-agg", "--limit", "31"],
        obj=script_info,
    )
    assert result.exit_code == 0
    assert all(b in result.output for b in bookmarks)

    result = runner.invoke(
        stats, ["aggregations", "list-bookmarks", "file-download-agg"], obj=script_info
    )
    assert result.exit_code == 0
    assert all(b in result.output for b in sorted(bookmarks)[-5:])
