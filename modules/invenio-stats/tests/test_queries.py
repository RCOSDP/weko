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
import copy
from mock import patch

from invenio_stats.aggregations import filter_robots
from invenio_stats.contrib.registrations import register_queries
from invenio_stats.errors import InvalidRequestInputError
from invenio_stats.queries import (
    ESQuery,
    ESDateHistogramQuery,
    ESTermsQuery,
    ESWekoFileStatsQuery,
    ESWekoTermsQuery
)

# class ESQuery(object):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_queries.py::test_query -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_query(app):
    query = ESQuery('test_name', 'test_type', 'test_index')

    # extract_date
    with pytest.raises(ValueError):
        assert query.extract_date('')
    with pytest.raises(TypeError):
        assert query.extract_date(None)

    # run
    with pytest.raises(NotImplementedError):
        assert query.run()



# class ESDateHistogramQuery(ESQuery):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_queries.py::test_date_histogram_query -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_date_histogram_query(app):
    config_num = 8      # query_name='bucket-file-download-histogram'
    query_configs = register_queries()
    histogram_config = query_configs[config_num]['query_config']
    # __init__
    with pytest.raises(ValueError):
        ESDateHistogramQuery(
            query_name='test_total_count',
            **histogram_config,
            metric_fields={'value': ('test', '', {})}
        )

    # validate_arguments
    query = ESDateHistogramQuery(
        query_name='test_total_count',
        **histogram_config
    )
    with pytest.raises(InvalidRequestInputError):
        query.validate_arguments('test_interval', None, None)
    with pytest.raises(InvalidRequestInputError):
        query.validate_arguments('year', None, None)
    assert not query.validate_arguments('year', None, None, bucket_id='test_id', file_key='test_key')

    # build_query
    query = ESDateHistogramQuery(
        query_name='test_total_count',
        **histogram_config
    )
    assert query.build_query('month', datetime.date(2023, 1, 1), datetime.date(2023, 3, 31)).to_dict() == {'query': {'bool': {'filter': [{'range': {'timestamp': {'gte': '2023-01-01', 'lte': '2023-03-31'}}}]}}, 'aggs': {'histogram': {'date_histogram': {'field': 'timestamp', 'interval': 'month', 'time_zone': 'Asia/Tokyo'}, 'aggs': {'value': {'sum': {'field': 'count'}}, 'top_hit': {'top_hits': {'size': 1, 'sort': {'timestamp': 'desc'}}}}}}, 'from': 0, 'size': 0}
    assert query.build_query('month', datetime.date(2023, 1, 1), None).to_dict() == {'query': {'bool': {'filter': [{'range': {'timestamp': {'gte': '2023-01-01'}}}]}}, 'aggs': {'histogram': {'date_histogram': {'field': 'timestamp', 'interval': 'month', 'time_zone': 'Asia/Tokyo'}, 'aggs': {'value': {'sum': {'field': 'count'}}, 'top_hit': {'top_hits': {'size': 1, 'sort': {'timestamp': 'desc'}}}}}}, 'from': 0, 'size': 0}
    assert query.build_query('month', None, datetime.date(2023, 1, 1)).to_dict() == {'query': {'bool': {'filter': [{'range': {'timestamp': {'lte': '2023-01-01'}}}]}}, 'aggs': {'histogram': {'date_histogram': {'field': 'timestamp', 'interval': 'month', 'time_zone': 'Asia/Tokyo'}, 'aggs': {'value': {'sum': {'field': 'count'}}, 'top_hit': {'top_hits': {'size': 1, 'sort': {'timestamp': 'desc'}}}}}}, 'from': 0, 'size': 0}
    assert query.build_query('month', None, None, file_key='test_key').to_dict() == {'query': {'bool': {'filter': [{'term': {'file_key': 'test_key'}}]}}, 'aggs': {'histogram': {'date_histogram': {'field': 'timestamp', 'interval': 'month', 'time_zone': 'Asia/Tokyo'}, 'aggs': {'value': {'sum': {'field': 'count'}}, 'top_hit': {'top_hits': {'size': 1, 'sort': {'timestamp': 'desc'}}}}}}, 'from': 0, 'size': 0}

    query = ESDateHistogramQuery(
        query_name='test_total_count',
        **histogram_config,
        query_modifiers=[filter_robots]
    )
    assert query.build_query('month', None, None).to_dict() == {'query': {'bool': {'filter': [{'term': {'is_robot': False}}]}}, 'aggs': {'histogram': {'date_histogram': {'field': 'timestamp', 'interval': 'month', 'time_zone': 'Asia/Tokyo'}, 'aggs': {'value': {'sum': {'field': 'count'}}, 'top_hit': {'top_hits': {'size': 1, 'sort': {'timestamp': 'desc'}}}}}}, 'from': 0, 'size': 0}

    test_config = copy.deepcopy(histogram_config)
    test_config.pop('copy_fields')
    query = ESDateHistogramQuery(
        query_name='test_total_count',
        **test_config
    )
    assert query.build_query('month', None, None).to_dict() == {'aggs': {'histogram': {'date_histogram': {'field': 'timestamp', 'interval': 'month', 'time_zone': 'Asia/Tokyo'}, 'aggs': {'value': {'sum': {'field': 'count'}}}}}, 'from': 0, 'size': 0}

    # process_query_result
    _res1 = {
        "aggregations": {
            "histogram": {
                "buckets": [
                    {
                        "key": "key1",
                        "key_as_string": "2023-01-01",
                        "value": {"value": 1},
                        "top_hit": {
                            "hits": {
                                "hits": [
                                    {
                                        "_source": {
                                            "bucket_id": "bucket1",
                                            "file_key": "file1",
                                            "test_value": "value1"
                                        }
                                    }
                                ]
                            }
                        }
                    }
                ]
            }
        }
    }
    _res2 = {
        "aggregations": {
            "histogram": {
                "buckets": [
                    {
                        "key": "key1",
                        "key_as_string": "2023-01-01",
                        "value": {"value": 1},
                        "top_hit": {
                            "hits": {
                                "hits": []
                            }
                        }
                    }
                ]
            }
        }
    }
    test_config = copy.deepcopy(histogram_config)
    test_config['copy_fields']['test_value'] = lambda res, data: data['test_value']
    query = ESDateHistogramQuery(
        query_name='test_total_count',
        **test_config
    )
    assert query.process_query_result(_res1, 'month', None, None) == {'interval': 'month', 'key_type': 'date', 'start_date': None, 'end_date': None, 'buckets': [{'key': 'key1', 'date': '2023-01-01', 'value': 1, 'bucket_id': 'bucket1', 'file_key': 'file1', 'test_value': 'value1'}]}
    assert query.process_query_result(_res1, 'month', datetime.date(2023, 1, 1), datetime.date(2023, 1, 2)) == {'interval': 'month', 'key_type': 'date', 'start_date': '2023-01-01', 'end_date': '2023-01-02', 'buckets': [{'key': 'key1', 'date': '2023-01-01', 'value': 1, 'bucket_id': 'bucket1', 'file_key': 'file1', 'test_value': 'value1'}]}
    assert query.process_query_result(_res2, 'month', None, None) == {'interval': 'month', 'key_type': 'date', 'start_date': None, 'end_date': None, 'buckets': [{'key': 'key1', 'date': '2023-01-01', 'value': 1}]}


# class ESTermsQuery(ESQuery):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_queries.py::test_terms_query -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
@pytest.mark.parametrize('aggregated_file_download_events',
                         [dict(file_number=1,
                               event_number=7,
                               start_date=datetime.date(2017, 1, 1),
                               end_date=datetime.date(2017, 1, 7))],
                         indirect=['aggregated_file_download_events'])
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
                     aggregated_file_download_events, mock_execute, config_num, res_file):
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

# .tox/c1/bin/pytest --cov=invenio_stats tests/test_queries.py::test_terms_query2 -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_terms_query2(app):
    config_num = 0        # query_name='get-celery-task-report'
    query_configs = register_queries()
    terms_config = query_configs[config_num]['query_config']
    
    # validate_arguments
    query = ESTermsQuery(
        query_name='test_total_count',
        **terms_config
    )
    with pytest.raises(InvalidRequestInputError):
        query.validate_arguments(None, None)
    assert not query.validate_arguments(None, None, task_name='task1')

    # build_query
    query = ESTermsQuery(
        query_name='test_total_count',
        **terms_config,
        query_modifiers=[filter_robots]
    )
    assert query.build_query(datetime.datetime(2023, 1, 1), None).to_dict() == {'query': {'bool': {'filter': [{'range': {'timestamp': {'gte': '2023-01-01T00:00:00', 'time_zone': 'Asia/Tokyo'}}}, {'term': {'is_robot': False}}]}}, 'aggs': {'value': {'sum': {'field': 'count'}}, 'task_id': {'terms': {'field': 'task_id', 'size': 6000}, 'aggs': {'value': {'sum': {'field': 'count'}}, 'task_name': {'terms': {'field': 'task_name', 'size': 6000}, 'aggs': {'value': {'sum': {'field': 'count'}}, 'start_time': {'terms': {'field': 'start_time', 'size': 6000}, 'aggs': {'value': {'sum': {'field': 'count'}}, 'end_time': {'terms': {'field': 'end_time', 'size': 6000}, 'aggs': {'value': {'sum': {'field': 'count'}}, 'total_records': {'terms': {'field': 'total_records', 'size': 6000}, 'aggs': {'value': {'sum': {'field': 'count'}}, 'task_state': {'terms': {'field': 'task_state', 'size': 6000}, 'aggs': {'value': {'sum': {'field': 'count'}}}}}}}}}}}}}}}, 'from': 0, 'size': 0}

    test_config = copy.deepcopy(terms_config)
    test_config.pop('aggregated_fields')
    query = ESTermsQuery(
        query_name='test_total_count',
        **test_config
    )
    assert query.build_query(None, datetime.datetime(2023, 1, 1)).to_dict() == {'query': {'bool': {'filter': [{'range': {'timestamp': {'lte': '2023-01-01T00:00:00', 'time_zone': 'Asia/Tokyo'}}}]}}, 'aggs': {'value': {'sum': {'field': 'count'}}}, 'from': 0, 'size': 0}

    # process_query_result
    _res = {
        "aggregations": {
            "value": {"value": "v1"},
            "top_hit": {
                "hits": {
                    "hits": [
                        {
                            "_source": {
                                "record_id": "1",
                                "test_value": "value1"
                            }
                        }
                    ]
                }
            },
            "buckets": [
                {
                    "doc_count": 10,
                    "key": {
                        "group": "group1",
                        "count": 1
                    }
                },
                {
                    "doc_count": 5,
                    "key": {
                        "group": "group1",
                        "count": 1
                    }
                }
            ]
        }
    }
    test_config = copy.deepcopy(terms_config)
    test_config['copy_fields'] = {
        'record_id': 'record_id',
        'test_value': lambda res, data: data['test_value']
    }
    test_config['group_fields'] = ['group', 'count']
    query = ESTermsQuery(
        query_name='test_total_count',
        **test_config
    )
    assert query.process_query_result(_res, None, None) == {'start_date': None, 'end_date': None, 'record_id': '1', 'test_value': 'value1', 'value': 'v1', 'buckets': [{'group': 'group1', 'count': 15}]}

    test_config = copy.deepcopy(terms_config)
    test_config.pop('aggregated_fields')
    query = ESTermsQuery(
        query_name='test_total_count',
        **test_config
    )
    assert query.process_query_result(_res, None, None) == {'start_date': None, 'end_date': None, 'value': 'v1'}


# .tox/c1/bin/pytest --cov=invenio_stats tests/test_queries.py::test_weko_file_stats_query -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_weko_file_stats_query(app):
    config_num = 9        # query_name='bucket-file-download-total'
    query_configs = register_queries()
    filestats_config = query_configs[config_num]['query_config']

    # build_query
    test_config = copy.deepcopy(filestats_config)
    test_config.pop('main_query')
    test_config.pop('aggregated_fields')
    query = ESWekoFileStatsQuery(
        query_name='test_total_count',
        **test_config,
        query_modifiers=[filter_robots]
    )
    assert query.build_query(datetime.datetime(2023, 1, 1), None).to_dict() == {'query': {'bool': {'filter': [{'range': {'timestamp': {'gte': '2023-01-01T00:00:00', 'time_zone': 'Asia/Tokyo'}}}, {'term': {'is_robot': False}}]}}, 'aggs': {'value': {'sum': {'field': 'count'}}}, 'from': 0, 'size': 0}

    test_config['group_fields'] = ['file_key', 'count']
    test_config['copy_fields'] = {'file_key': 'file_key'}
    query = ESWekoFileStatsQuery(
        query_name='test_total_count',
        **test_config
    )
    assert query.build_query(None, datetime.datetime(2023, 1, 1)).to_dict() == {'query': {'bool': {'filter': [{'range': {'timestamp': {'lte': '2023-01-01T00:00:00', 'time_zone': 'Asia/Tokyo'}}}]}}, 'aggs': {'value': {'sum': {'field': 'count'}}, 'my_buckets': {'composite': {'size': 6000, 'sources': [{'file_key': {'terms': {'field': 'file_key'}}}, {'count': {'terms': {'field': 'count'}}}]}}, 'top_hit': {'top_hits': {'size': 1, 'sort': {'timestamp': 'desc'}}}}, 'from': 0, 'size': 0}
    assert query.build_query(None, None, after_key='test_key').to_dict() == {'aggs': {'value': {'sum': {'field': 'count'}}, 'my_buckets': {'composite': {'size': 6000, 'sources': [{'file_key': {'terms': {'field': 'file_key'}}}, {'count': {'terms': {'field': 'count'}}}], 'after': 'test_key'}}, 'top_hit': {'top_hits': {'size': 1, 'sort': {'timestamp': 'desc'}}}}, 'from': 0, 'size': 0}


# .tox/c1/bin/pytest --cov=invenio_stats tests/test_queries.py::test_weko_terms_query -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_weko_terms_query(app):
    config_num = 1        # query_name='get-search-report'
    query_configs = register_queries()
    weko_terms_config = query_configs[config_num]['query_config']

    # build_query
    test_config = copy.deepcopy(weko_terms_config)
    test_config.pop('group_fields')
    test_config['copy_fields'] = {
        'record_id': 'record_id',
        'test_value': lambda res, data: data['test_value']
    }
    query = ESWekoTermsQuery(
        query_name='test_total_count',
        **test_config,
        query_modifiers=[filter_robots]
    )
    assert query.build_query(datetime.datetime(2023, 1, 1), None).to_dict() == {'query': {'bool': {'filter': [{'range': {'timestamp': {'gte': '2023-01-01T00:00:00', 'time_zone': 'Asia/Tokyo'}}}, {'term': {'is_robot': False}}]}}, 'aggs': {'value': {'sum': {'field': 'count'}}, 'top_hit': {'top_hits': {'size': 1, 'sort': {'timestamp': 'desc'}}}}, 'from': 0, 'size': 0}

    test_config = copy.deepcopy(weko_terms_config)
    test_config['required_filters'] = {'required1': 'required1', 'required2': 'required2'}
    query = ESWekoTermsQuery(
        query_name='test_total_count',
        **test_config
    )
    assert query.build_query(None, datetime.datetime(2023, 1, 1), after_key='test_key', required1='v1', agg_filter={'agg': 'agg1'}).to_dict() == {'query': {'bool': {'filter': [{'range': {'timestamp': {'lte': '2023-01-01T00:00:00', 'time_zone': 'Asia/Tokyo'}}}, {'term': {'required1': 'v1'}}, {'terms': {'agg': 'agg1'}}]}}, 'aggs': {'value': {'sum': {'field': 'count'}}, 'my_buckets': {'composite': {'size': 6000, 'sources': [{'search_key': {'terms': {'field': 'search_key'}}}, {'count': {'terms': {'field': 'count'}}}], 'after': 'test_key'}}}, 'from': 0, 'size': 0}
