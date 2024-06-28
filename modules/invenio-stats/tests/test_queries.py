# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Query tests."""

import datetime

import pytest

from invenio_stats.queries import DateHistogramQuery, TermsQuery


@pytest.mark.parametrize(
    "aggregated_events",
    [
        {
            "file_number": 1,
            "event_number": 2,
            "start_date": datetime.date(2017, 1, 1),
            "end_date": datetime.date(2017, 1, 7),
        }
    ],
    indirect=["aggregated_events"],
)
def test_histogram_query(app, event_queues, aggregated_events, queries_config):
    """Test histogram query daily results."""
    # reading the configuration as it is registered from registrations.py
    histo_query = DateHistogramQuery(
        name="test_histo", **queries_config["bucket-file-download-histogram"]["params"]
    )
    results = histo_query.run(
        bucket_id="B0000000000000000000000000000001",
        file_key="test.pdf",
        start_date=datetime.datetime(2017, 1, 1),
        end_date=datetime.datetime(2017, 1, 7),
    )
    for day_result in results["buckets"]:
        assert int(day_result["value"]) == 2


@pytest.mark.parametrize(
    "aggregated_events",
    [
        {
            "file_number": 1,
            "event_number": 7,
            "start_date": datetime.date(2017, 1, 1),
            "end_date": datetime.date(2017, 1, 7),
        }
    ],
    indirect=["aggregated_events"],
)
def test_terms_query(app, event_queues, aggregated_events, queries_config):
    """Test that the terms query returns the correct total count."""
    terms_query = TermsQuery(
        name="test_total_count",
        **queries_config["bucket-file-download-total"]["params"]
    )
    results = terms_query.run(
        bucket_id="B0000000000000000000000000000001",
        start_date=datetime.datetime(2017, 1, 1),
        end_date=datetime.datetime(2017, 1, 7),
    )
    assert int(results["buckets"][0]["value"]) == 49
