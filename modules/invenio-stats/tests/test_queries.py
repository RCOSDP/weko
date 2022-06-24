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
import json
from mock import patch

from invenio_stats.contrib.registrations import register_queries
from invenio_stats.queries import ESDateHistogramQuery, ESTermsQuery


@pytest.mark.skip('This test dont ever finish')
@pytest.mark.parametrize('aggregated_events',
                         [dict(file_number=1,
                               event_number=2,
                               start_date=datetime.date(2017, 1, 1),
                               end_date=datetime.date(2017, 1, 7))],
                         indirect=['aggregated_events'])
def test_histogram_query(app, event_queues, aggregated_events):
    """Test that the histogram query returns the correct
    results for each day."""
    # reading the configuration as it is registered from registrations.py
    query_configs = register_queries()
    histo_query = ESDateHistogramQuery(query_name='test_histo',
                                       **query_configs[0]['query_config'])
    results = histo_query.run(bucket_id='B0000000000000000000000000000001',
                              file_key='test.pdf',
                              start_date=datetime.datetime(2017, 1, 1),
                              end_date=datetime.datetime(2017, 1, 7))
    for day_result in results['buckets']:
        assert int(day_result['value']) == 2


@pytest.mark.parametrize('aggregated_events',
                         [dict(file_number=1,
                               event_number=7,
                               start_date=datetime.date(2017, 1, 1),
                               end_date=datetime.date(2017, 1, 7))],
                         indirect=['aggregated_events'])
@pytest.mark.parametrize("mock_execute, config_num, res_file",
                         [(["tests/data/ESTermsQuery_execute01.json"],
                           1,
                           "tests/data/ESTermsQuery_result01.json"),
                          (["tests/data/ESTermsQuery_execute02.json", 
                            "tests/data/ESTermsQuery_execute01.json"],
                           1,
                           "tests/data/ESTermsQuery_result02.json"),
                          (["tests/data/ESTermsQuery_execute03.json"],
                           16,
                           "tests/data/ESTermsQuery_result03.json")])
def test_terms_query(app,mock_es_execute, event_queues,
                     aggregated_events, mock_execute, config_num, res_file):
    """Test that the terms query returns the correct total count."""
    query_configs = register_queries()
    terms_query = ESTermsQuery(query_name='test_total_count',
                               **query_configs[config_num]['query_config'])

    with patch("invenio_stats.queries.Search.execute", side_effect=[mock_es_execute(data) for data in mock_execute]):
      results = terms_query.run(bucket_id='B0000000000000000000000000000001',
                                start_date=datetime.datetime(2017, 1, 1),
                                end_date=datetime.datetime(2017, 1, 7))
      with open(res_file, "r") as f:
            data = json.load(f)
      # assert int(results['buckets'][0]['value']) == 49
      assert results == data
