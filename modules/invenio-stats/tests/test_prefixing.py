# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test index prefix."""

import datetime
from unittest.mock import patch

from conftest import _create_file_download_event
from helpers import get_queue_size, mock_date
from invenio_queues.proxies import current_queues

from invenio_stats.processors import EventsIndexer, flag_machines, flag_robots
from invenio_stats.proxies import current_stats
from invenio_stats.queries import DateHistogramQuery, TermsQuery
from invenio_stats.tasks import aggregate_events


def test_index_prefix(
    config_with_index_prefix, app, search_clear, event_queues, queries_config
):
    # 1) publish events in the queue
    current_stats.publish(
        "file-download",
        [
            _create_file_download_event(date)
            for date in [(2018, 1, 1), (2018, 1, 2), (2018, 1, 3), (2018, 1, 4)]
        ],
    )

    queue = current_queues.queues["stats-file-download"]
    assert get_queue_size("stats-file-download") == 4

    # 2) preprocess events
    indexer = EventsIndexer(queue, preprocessors=[flag_machines, flag_robots])
    indexer.run()
    search_clear.indices.refresh(index="*")

    assert get_queue_size("stats-file-download") == 0

    index_prefix = config_with_index_prefix["SEARCH_INDEX_PREFIX"]
    index_name = index_prefix + "events-stats-file-download"

    assert search_clear.indices.exists(index_name + "-2018-01")
    assert search_clear.indices.exists_alias(name=index_name)

    # 3) aggregate events
    with patch("invenio_stats.aggregations.datetime", mock_date(2018, 1, 4)):
        aggregate_events(["file-download-agg"])
    search_clear.indices.refresh(index="*")
    search_clear.indices.exists(index_prefix + "stats-file-download-2018-01")

    # 4) queries
    histo_query_name = "bucket-file-download-histogram"
    histo_query = DateHistogramQuery(
        name=histo_query_name, **queries_config[histo_query_name]["params"]
    )
    results = histo_query.run(
        bucket_id="B0000000000000000000000000000001",
        file_key="test.pdf",
        start_date=datetime.datetime(2018, 1, 1),
        end_date=datetime.datetime(2018, 1, 3),
    )
    assert len(results["buckets"])
    for day_result in results["buckets"]:
        assert int(day_result["value"]) == 1

    terms_query_name = "bucket-file-download-total"
    terms_query = TermsQuery(
        name=terms_query_name, **queries_config[terms_query_name]["params"]
    )
    results = terms_query.run(
        bucket_id="B0000000000000000000000000000001",
        start_date=datetime.datetime(2018, 1, 1),
        end_date=datetime.datetime(2018, 1, 7),
    )
    assert int(results["buckets"][0]["value"]) == 4
