# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Registration of contrib events."""
from flask import current_app
from invenio_search import current_search_client

from invenio_stats.aggregations import StatAggregator, filter_restricted
from invenio_stats.contrib.event_builders import build_celery_task_unique_id, \
    build_file_unique_id, build_item_create_unique_id, \
    build_record_unique_id, build_search_detail_condition, \
    build_search_unique_id, build_top_unique_id, copy_record_index_list, \
    copy_search_keyword, copy_search_type, copy_user_group_list
from invenio_stats.processors import EventsIndexer, anonymize_user, \
    flag_restricted, flag_robots
from invenio_stats.queries import ESDateHistogramQuery, ESTermsQuery, \
    ESWekoFileStatsQuery, ESWekoTermsQuery, ESWekoRankingQuery, ESWekoFileRankingQuery

from weko_schema_ui.models import PublishStatus

def register_events():
    """Register sample events."""
    return [
        dict(
            event_type='celery-task',
            templates='invenio_stats.contrib.celery_task',
            processor_class=EventsIndexer,
            processor_config=dict(
                preprocessors=[
                    flag_restricted,
                    flag_robots,
                    anonymize_user,
                    build_celery_task_unique_id
                ],
                suffix="%Y",
            )),
        dict(
            event_type='file-download',
            templates='invenio_stats.contrib.file_download',
            processor_class=EventsIndexer,
            processor_config=dict(
                preprocessors=[
                    flag_restricted,
                    flag_robots,
                    anonymize_user,
                    build_file_unique_id
                ],
                double_click_window=30,
                suffix="%Y",
            )),
        dict(
            event_type='file-preview',
            templates='invenio_stats.contrib.file_preview',
            processor_class=EventsIndexer,
            processor_config=dict(
                preprocessors=[
                    flag_restricted,
                    flag_robots,
                    anonymize_user,
                    build_file_unique_id
                ],
                double_click_window=30,
                suffix="%Y",
            )),
        dict(
            event_type='item-create',
            templates='invenio_stats.contrib.item_create',
            processor_class=EventsIndexer,
            processor_config=dict(
                preprocessors=[
                    flag_restricted,
                    flag_robots,
                    anonymize_user,
                    build_item_create_unique_id
                ],
                suffix="%Y",
            )),
        dict(
            event_type='record-view',
            templates='invenio_stats.contrib.record_view',
            processor_class=EventsIndexer,
            processor_config=dict(
                preprocessors=[
                    flag_restricted,
                    flag_robots,
                    anonymize_user,
                    build_record_unique_id
                ],
                double_click_window=30,
                suffix="%Y",
            )),
        dict(
            event_type='top-view',
            templates='invenio_stats.contrib.top_view',
            processor_class=EventsIndexer,
            processor_config=dict(
                preprocessors=[
                    flag_restricted,
                    flag_robots,
                    anonymize_user,
                    build_top_unique_id
                ],
                double_click_window=30,
                suffix="%Y",
            )),
        dict(
            event_type='search',
            templates='invenio_stats.contrib.search',
            processor_class=EventsIndexer,
            processor_config=dict(
                preprocessors=[
                    flag_restricted,
                    flag_robots,
                    anonymize_user,
                    build_search_detail_condition,
                    build_search_unique_id
                ],
                double_click_window=30,
                suffix="%Y",
            ))
    ]


def register_aggregations():
    """Register sample aggregations."""
    return [dict(
        aggregation_name='celery-task-agg',
        templates='invenio_stats.contrib.aggregations.aggr_celery_task',
        aggregator_class=StatAggregator,
        aggregator_config=dict(
            client=current_search_client,
            event='celery-task',
            aggregation_field='unique_id',
            aggregation_interval='day',
            index_interval='year',
            query_modifiers=[filter_restricted],
            copy_fields=dict(
                task_id='task_id',
                task_name='task_name',
                task_state='task_state',
                start_time='start_time',
                end_time='end_time',
                total_records='total_records',
                repository_name='repository_name',
                execution_time='execution_time',
            ),
            metric_aggregation_fields={
                'unique_count': ('cardinality', 'unique_session_id',
                                 {'precision_threshold': 1000}),
                'volume': ('sum', 'size', {}),
            },
        )),
        dict(
            aggregation_name='search-agg',
            templates='invenio_stats.contrib.aggregations.aggr_search',
            aggregator_class=StatAggregator,
            aggregator_config=dict(
                client=current_search_client,
                event='search',
                aggregation_field='unique_id',
                aggregation_interval='day',
                index_interval='year',
                query_modifiers=[filter_restricted],
                copy_fields=dict(
                    country='country',
                    referrer='referrer',
                    search_key=copy_search_keyword,
                    search_type=copy_search_type,
                    site_license_name='site_license_name',
                    site_license_flag='site_license_flag'
                    # count='count',
                ),
                metric_aggregation_fields={
                    'unique_count': ('cardinality', 'unique_session_id',
                                     {'precision_threshold': 1000}),
                },
            )), dict(
        aggregation_name='file-download-agg',
        templates='invenio_stats.contrib.aggregations.aggr_file_download',
        aggregator_class=StatAggregator,
        aggregator_config=dict(
            client=current_search_client,
            event='file-download',
            aggregation_field='unique_id',
            aggregation_interval='day',
            index_interval='year',
            query_modifiers=[filter_restricted],
            copy_fields=dict(
                country='country',
                item_id='item_id',
                item_title='item_title',
                file_key='file_key',
                bucket_id='bucket_id',
                file_id='file_id',
                root_file_id='root_file_id',
                accessrole='accessrole',
                userrole='userrole',
                index_list='index_list',
                is_billing_item='is_billing_item',
                billing_file_price='billing_file_price',
                user_group_names=copy_user_group_list,
                site_license_name='site_license_name',
                site_license_flag='site_license_flag',
                cur_user_id='cur_user_id',
                hostname='hostname',
                remote_addr='remote_addr',
            ),
            metric_aggregation_fields={
                'unique_count': ('cardinality', 'unique_session_id',
                                 {'precision_threshold': 1000}),
                'volume': ('sum', 'size', {}),
            },
        )), dict(
        aggregation_name='file-preview-agg',
        templates='invenio_stats.contrib.aggregations.aggr_file_preview',
        aggregator_class=StatAggregator,
        aggregator_config=dict(
            client=current_search_client,
            event='file-preview',
            aggregation_field='unique_id',
            query_modifiers=[filter_restricted],
            aggregation_interval='day',
            index_interval='year',
            copy_fields=dict(
                country='country',
                item_id='item_id',
                item_title='item_title',
                file_key='file_key',
                bucket_id='bucket_id',
                file_id='file_id',
                root_file_id='root_file_id',
                accessrole='accessrole',
                userrole='userrole',
                index_list='index_list',
                is_billing_item='is_billing_item',
                billing_file_price='billing_file_price',
                user_group_names=copy_user_group_list,
                site_license_name='site_license_name',
                site_license_flag='site_license_flag',
                cur_user_id='cur_user_id',
                hostname='hostname',
                remote_addr='remote_addr',
            ),
            metric_aggregation_fields={
                'unique_count': ('cardinality', 'unique_session_id',
                                 {'precision_threshold': 1000}),
                'volume': ('sum', 'size', {}),
            },
        )), dict(
        aggregation_name='item-create-agg',
        templates='invenio_stats.contrib.aggregations.aggr_item_create',
        aggregator_class=StatAggregator,
        aggregator_config=dict(
            client=current_search_client,
            event='item-create',
            aggregation_field='unique_id',
            aggregation_interval='day',
            index_interval='year',
            query_modifiers=[filter_restricted],
            copy_fields=dict(
                country='country',
                hostname='hostname',
                cur_user_id='cur_user_id',
                remote_addr='remote_addr',
                pid_type='pid_type',
                pid_value='pid_value',
                record_name='record_name',
            ),
            metric_aggregation_fields={
                'unique_count': ('cardinality', 'unique_session_id',
                                 {'precision_threshold': 1000}),
            },
        )), dict(
        aggregation_name='record-view-agg',
        templates='invenio_stats.contrib.aggregations.aggr_record_view',
        aggregator_class=StatAggregator,
        aggregator_config=dict(
            client=current_search_client,
            event='record-view',
            aggregation_field='unique_id',
            aggregation_interval='day',
            index_interval='year',
            query_modifiers=[filter_restricted],
            copy_fields=dict(
                country='country',
                hostname='hostname',
                remote_addr='remote_addr',
                record_id='record_id',
                record_name='record_name',
                record_index_names=copy_record_index_list,
                pid_type='pid_type',
                pid_value='pid_value',
                cur_user_id='cur_user_id',
                site_license_name='site_license_name',
                site_license_flag='site_license_flag'
            ),
            metric_aggregation_fields={
                'unique_count': ('cardinality', 'unique_session_id',
                                 {'precision_threshold': 1000}),
            },
        )), dict(
        aggregation_name='top-view-agg',
        templates='invenio_stats.contrib.aggregations.aggr_top_view',
        aggregator_class=StatAggregator,
        aggregator_config=dict(
            client=current_search_client,
            event='top-view',
            aggregation_field='unique_id',
            aggregation_interval='day',
            index_interval='year',
            query_modifiers=[filter_restricted],
            copy_fields=dict(
                country='country',
                hostname='hostname',
                remote_addr='remote_addr',
                site_license_name='site_license_name',
                site_license_flag='site_license_flag'
            ),
            metric_aggregation_fields={
                'unique_count': ('cardinality', 'unique_session_id',
                                 {'precision_threshold': 1000}),
            },
        ))]


def register_queries():
    """Register queries."""
    search_index_prefix = current_app.config['SEARCH_INDEX_PREFIX'].strip('-')
    return [
        dict(
            query_name='get-celery-task-report',
            query_class=ESTermsQuery,
            query_config=dict(
                index='{}-stats-celery-task'.format(search_index_prefix),
                doc_type='celery-task-day-aggregation',
                aggregated_fields=['task_id', 'task_name', 'start_time',
                                   'end_time', 'total_records', 'task_state'],
                required_filters=dict(
                    task_name='task_name',
                ),
            )
        ),
        dict(
            query_name='get-search-report',
            query_class=ESWekoTermsQuery,
            query_config=dict(
                index='{}-stats-search'.format(search_index_prefix),
                doc_type='search-day-aggregation',
                group_fields=['search_key', 'count'],
            )
        ),
        dict(
            query_name='get-file-download-report',
            query_class=ESTermsQuery,
            query_config=dict(
                index='{}-stats-file-download'.format(search_index_prefix),
                doc_type='file-download-day-aggregation',
                group_fields=['file_key', 'index_list', 'userrole',
                              'site_license_flag', 'count'],
                required_filters=dict(
                    index_list='index_list',
                ),
            )
        ),
        dict(
            query_name='get-billing-file-download-report',
            query_class=ESTermsQuery,
            query_config=dict(
                index='{}-stats-file-download'.format(search_index_prefix),
                doc_type='file-download-day-aggregation',
                group_fields=['file_key', 'index_list',
                              'userrole', 'site_license_flag',
                              'user_group_names', 'count'],
                required_filters=dict(
                    is_billing_item='is_billing_item',
                    index_list='index_list',
                ),
            )
        ),
        dict(
            query_name='get-file-download-open-access-report',
            query_class=ESTermsQuery,
            query_config=dict(
                index='{}-stats-file-download'.format(search_index_prefix),
                doc_type='file-download-day-aggregation',
                group_fields=['file_key', 'index_list', 'userrole',
                              'site_license_flag', 'count'],
                required_filters=dict(
                    accessrole='accessrole',
                    index_list='index_list',
                ),
            )
        ),
        dict(
            query_name='get-file-preview-report',
            query_class=ESTermsQuery,
            query_config=dict(
                index='{}-stats-file-preview'.format(search_index_prefix),
                doc_type='file-preview-day-aggregation',
                group_fields=['file_key', 'index_list', 'userrole',
                              'site_license_flag', 'count'],
                required_filters=dict(
                    index_list='index_list',
                )
            )
        ),
        dict(
            query_name='get-billing-file-preview-report',
            query_class=ESTermsQuery,
            query_config=dict(
                index='{}-stats-file-preview'.format(search_index_prefix),
                doc_type='file-preview-day-aggregation',
                group_fields=['file_key', 'index_list',
                              'userrole', 'site_license_flag',
                              'user_group_names', 'count'],
                required_filters=dict(
                    is_billing_item='is_billing_item',
                    index_list='index_list',
                ),
            )
        ),
        dict(
            query_name='get-file-preview-open-access-report',
            query_class=ESTermsQuery,
            query_config=dict(
                index='{}-stats-file-preview'.format(search_index_prefix),
                doc_type='file-preview-day-aggregation',
                group_fields=['file_key', 'index_list', 'userrole',
                              'site_license_flag', 'count'],
                required_filters=dict(
                    accessrole='accessrole',
                    # is_billing_item='is_billing_item',
                    index_list='index_list',
                ),
            )
        ),
        dict(
            query_name='bucket-file-download-histogram',
            query_class=ESDateHistogramQuery,
            query_config=dict(
                index='{}-stats-file-download'.format(search_index_prefix),
                doc_type='file-download-day-aggregation',
                copy_fields=dict(
                    bucket_id='bucket_id',
                    file_key='file_key',
                ),
                required_filters=dict(
                    bucket_id='bucket_id',
                    file_key='file_key',
                ),
            )
        ),
        dict(
            query_name='bucket-file-download-total',
            query_class=ESWekoFileStatsQuery,
            query_config=dict(
                index='{}-stats-file-download'.format(search_index_prefix),
                doc_type='file-download-day-aggregation',
                copy_fields=dict(),
                main_fields=['bucket_id', 'file_key', 'root_file_id'],
                main_query={
                    "query": {
                        "bool": {
                            "should": [
                                {
                                    "bool": {
                                        "filter": [
                                            {
                                                "term": {
                                                    "bucket_id": {
                                                        "value": "@bucket_id",
                                                        "boost": 1
                                                    }
                                                }
                                            },
                                            {
                                                "term": {
                                                    "file_key": {
                                                        "value": "@file_key",
                                                        "boost": 1
                                                    }
                                                }
                                            },
                                            {
                                                "bool": {
                                                    "must_not": {
                                                        "exists": {
                                                            "field": "root_file_id"
                                                        }
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                },
                                {
                                    "bool": {
                                        "filter": [
                                            {
                                                "term": {
                                                    "root_file_id": {
                                                        "value": "@root_file_id",
                                                        "boost": 1
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                }
                            ],
                            "adjust_pure_negative": True,
                            "boost": 1
                        }
                    }
                },
                aggregated_fields=['country'],
            )
        ),
        dict(
            query_name='bucket-file-preview-histogram',
            query_class=ESDateHistogramQuery,
            query_config=dict(
                index='{}-stats-file-preview'.format(search_index_prefix),
                doc_type='file-preview-day-aggregation',
                copy_fields=dict(
                    bucket_id='bucket_id',
                    file_key='file_key',
                ),
                required_filters=dict(
                    bucket_id='bucket_id',
                    file_key='file_key',
                ),
            )
        ),
        dict(
            query_name='bucket-file-preview-total',
            query_class=ESWekoFileStatsQuery,
            query_config=dict(
                index='{}-stats-file-preview'.format(search_index_prefix),
                doc_type='file-preview-day-aggregation',
                copy_fields=dict(),
                main_fields=['bucket_id', 'file_key', 'root_file_id'],
                main_query={
                    "query": {
                        "bool": {
                            "should": [
                                {
                                    "bool": {
                                        "filter": [
                                            {
                                                "term": {
                                                    "bucket_id": {
                                                        "value": "@bucket_id",
                                                        "boost": 1
                                                    }
                                                }
                                            },
                                            {
                                                "term": {
                                                    "file_key": {
                                                        "value": "@file_key",
                                                        "boost": 1
                                                    }
                                                }
                                            },
                                            {
                                                "bool": {
                                                    "must_not": {
                                                        "exists": {
                                                            "field": "root_file_id"
                                                        }
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                },
                                {
                                    "bool": {
                                        "filter": [
                                            {
                                                "term": {
                                                    "root_file_id": {
                                                        "value": "@root_file_id",
                                                        "boost": 1
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                }
                            ],
                            "adjust_pure_negative": True,
                            "boost": 1
                        }
                    }
                },
                aggregated_fields=['country'],
            )
        ),
        dict(
            query_name='get-file-download-per-user-report',
            query_class=ESTermsQuery,
            query_config=dict(
                index='{}-stats-file-download'.format(search_index_prefix),
                doc_type='file-download-day-aggregation',
                group_fields=['cur_user_id', 'count'],
                required_filters=dict(
                    user_ids='cur_user_id',
                )
            )
        ),
        dict(
            query_name='get-file-preview-per-user-report',
            query_class=ESTermsQuery,
            query_config=dict(
                index='{}-stats-file-preview'.format(search_index_prefix),
                doc_type='file-preview-day-aggregation',
                group_fields=['cur_user_id', 'count'],
                required_filters=dict(
                    user_ids='cur_user_id',
                )
            )
        ),
        dict(
            query_name='get-record-view-report',
            query_class=ESWekoTermsQuery,
            query_config=dict(
                index='{}-stats-record-view'.format(search_index_prefix),
                doc_type='record-view-day-aggregation',
                group_fields=['record_id', 'record_index_names',
                               'cur_user_id', 'pid_value', 'record_name', 'count'],
            )
        ),
        dict(
            query_name='bucket-record-view-histogram',
            query_class=ESDateHistogramQuery,
            query_config=dict(
                index='{}-stats-record-view'.format(search_index_prefix),
                doc_type='record-view-day-aggregation',
                copy_fields=dict(
                    record_id='record_id',
                ),
                required_filters=dict(
                    record_id='record_id',
                ),
            )
        ),
        dict(
            query_name='bucket-record-view-total',
            query_class=ESTermsQuery,
            query_config=dict(
                index='{}-stats-record-view'.format(search_index_prefix),
                doc_type='record-view-day-aggregation',
                copy_fields=dict(
                    record_id='record_id',
                ),
                required_filters=dict(
                    record_id='record_id',
                ),
                metric_fields=dict(
                    count=('sum', 'count', {}),
                    unique_count=('sum', 'unique_count', {}),
                ),
                aggregated_fields=['country'],
            )
        ),
        dict(
            query_name='item-create-total',
            query_class=ESWekoTermsQuery,
            query_config=dict(
                index='{}-stats-item-create'.format(search_index_prefix),
                doc_type='item-create-day-aggregation',
                metric_fields=dict(
                    count=('sum', 'count', {}),
                ),
                aggregated_fields=['remote_addr', 'hostname', 'cur_user_id'],
            )
        ),
        dict(
            query_name='item-create-per-date',
            query_class=ESWekoTermsQuery,
            query_config=dict(
                index='{}-stats-item-create'.format(search_index_prefix),
                doc_type='item-create-day-aggregation',
                metric_fields=dict(
                    count=('sum', 'count', {}),
                ),
                aggregated_fields=['timestamp', 'pid_value', 'record_name'],
            )
        ),
        dict(
            query_name='item-create-histogram',
            query_class=ESDateHistogramQuery,
            query_config=dict(
                index='{}-stats-item-create'.format(search_index_prefix),
                doc_type='item-create-day-aggregation',
                aggregated_fields=['timestamp'],
                required_filters=dict(
                    item_ids='pid_value',
                )
            )
        ),
        dict(
            query_name='item-detail-total',
            query_class=ESTermsQuery,
            query_config=dict(
                index='{}-stats-record-view'.format(search_index_prefix),
                doc_type='record-view-day-aggregation',
                metric_fields=dict(
                    count=('sum', 'count', {}),
                ),
                aggregated_fields=['remote_addr', 'hostname'],
                required_filters=dict(
                    index_list='record_index_names',
                ),
            )
        ),
        dict(
            query_name='get-file-download-per-host-report',
            query_class=ESTermsQuery,
            query_config=dict(
                index='{}-stats-file-download'.format(search_index_prefix),
                doc_type='file-download-day-aggregation',
                metric_fields=dict(
                    count=('sum', 'count', {}),
                ),
                aggregated_fields=['remote_addr', 'hostname'],
                required_filters=dict(
                    index_list='index_list',
                ),
            )
        ),
        # For query item details (id, name, count)
        dict(
            query_name='item-detail-item-total',
            query_class=ESTermsQuery,
            query_config=dict(
                index='{}-stats-record-view'.format(search_index_prefix),
                doc_type='record-view-day-aggregation',
                metric_fields=dict(
                    count=('sum', 'count', {}),
                ),
                aggregated_fields=['pid_value', 'record_name'],
                required_filters=dict(
                    index_list='record_index_names',
                ),  
            )
        ),
        dict(
            query_name='get-file-download-per-item-report',
            query_class=ESTermsQuery,
            query_config=dict(
                index='{}-stats-file-download'.format(search_index_prefix),
                doc_type='file-download-day-aggregation',
                metric_fields=dict(
                    count=('sum', 'count', {}),
                ),
                aggregated_fields=['item_id', 'item_title'],
                required_filters=dict(
                    index_list='index_list',
                ),
            )
        ),
        dict(
            query_name='bucket-item-detail-view-histogram',
            query_class=ESDateHistogramQuery,
            query_config=dict(
                index='{}-stats-record-view'.format(search_index_prefix),
                doc_type='record-view-day-aggregation',
                aggregated_fields=['timestamp'],
                required_filters=dict(
                    index_list='record_index_names',
                ),
            )
        ),
        dict(
            query_name='get-file-download-per-time-report',
            query_class=ESDateHistogramQuery,
            query_config=dict(
                index='{}-stats-file-download'.format(search_index_prefix),
                doc_type='file-download-day-aggregation',
                aggregated_fields=['timestamp'],
                required_filters=dict(
                    index_list='index_list',
                ),
            )
        ),
        dict(
            query_name='top-view-total-per-host',
            query_class=ESTermsQuery,
            query_config=dict(
                index='{}-stats-top-view'.format(search_index_prefix),
                doc_type='top-view-day-aggregation',
                group_fields=['remote_addr', 'hostname', 'count']
            )
        ),
        dict(
            query_name='top-view-total',
            query_class=ESDateHistogramQuery,
            query_config=dict(
                index='{}-stats-top-view'.format(search_index_prefix),
                doc_type='top-view-day-aggregation',
                aggregated_fields=['remote_addr', 'hostname']
            )
        ),
        dict(
            query_name='get-top-view-per-site-license',
            query_class=ESTermsQuery,
            query_config=dict(
                index='{}-stats-top-view'.format(search_index_prefix),
                doc_type='top-view-day-aggregation',
                group_fields=['site_license_name', 'count'],
            )
        ),
        dict(
            query_name='get-record-view-per-site-license',
            query_class=ESTermsQuery,
            query_config=dict(
                index='{}-stats-record-view'.format(search_index_prefix),
                doc_type='record-view-day-aggregation',
                group_fields=['site_license_name', 'count'],
                required_filters=dict(
                    index_list='record_index_names',
                )
            )
        ),
        dict(
            query_name='get-search-per-site-license',
            query_class=ESWekoTermsQuery,
            query_config=dict(
                index='{}-stats-search'.format(search_index_prefix),
                doc_type='search-day-aggregation',
                group_fields=['site_license_name', 'count'],
            )
        ),
        dict(
            query_name='get-file-download-per-site-license',
            query_class=ESTermsQuery,
            query_config=dict(
                index='{}-stats-file-download'.format(search_index_prefix),
                doc_type='file-download-day-aggregation',
                group_fields=['site_license_name', 'count'],
                required_filters=dict(
                    index_list='index_list',
                )
            )
        ),
        dict(
            query_name='get-file-preview-per-site-license',
            query_class=ESTermsQuery,
            query_config=dict(
                index='{}-stats-file-preview'.format(search_index_prefix),
                doc_type='file-preview-day-aggregation',
                group_fields=['site_license_name', 'count'],
                required_filters=dict(
                    index_list='index_list',
                )
            )
        ),
        dict(
            query_name='get-ranking-data',
            query_class=ESWekoRankingQuery,
            query_config=dict(
                index='{}-stats-{}',
                doc_type='{}-day-aggregation',
                main_fields=['start_date', 'end_date', 'group_field', 'agg_size', 'count_field'],
                metric_fields=dict(),
                main_query={
                    "size": 0,
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "range": {
                                        "timestamp": {
                                            "gte": "@start_date",
                                            "lte": "@end_date",
                                            "time_zone": "@time_zone"
                                        }
                                    }
                                }
                            ],
                            "must_not": "@must_not"
                        }
                    },
                    "aggs": {
                        "my_buckets": {
                            "terms": {
                                "field": "@group_field",
                                "size": "@agg_size",
                                "order": {
                                    "my_sum": "desc" 
                                }
                            },
                            "aggs": {
                                "my_sum": {
                                    "sum": {
                                        "field": "@count_field" 
                                    }
                                }
                            }
                        }
                    }
                }
            )
        ),
        dict(
            query_name='get-new-items-data',
            query_class=ESWekoRankingQuery,
            query_config=dict(
                index='{}-weko',
                doc_type='item-v1.0.0',
                main_fields=['start_date', 'end_date', 'agg_size'],
                metric_fields=dict(),
                main_query={
                    "size": "@agg_size",
                    "sort": [
                        {
                            "publish_date":{
                                "order": "desc"
                            }
                        }
                    ],
                    "query":{
                        "bool":{
                            "must":[
                                {
                                    "range": {
                                        "publish_date": {
                                            "gte": "@start_date",
                                            "lte": "@end_date"
                                        }
                                    }
                                },
                                {
                                    "term": {
                                        "relation_version_is_last": True
                                    }
                                },
                                {
                                    "terms": {
                                        "publish_status": [
                                            PublishStatus.PUBLIC.value,
                                            PublishStatus.PRIVATE.value
                                        ]
                                    }
                                }
                            ],
                            "must_not": "@must_not"
                        }
                    }
                }
            )
        ),
        dict(
            query_name='item-file-download-aggs',
            query_class=ESWekoFileRankingQuery,
            query_config=dict(
                index='{}-events-stats-file-download'.format(search_index_prefix),
                doc_type='stats-file-download',
                copy_fields=dict(),
                metric_fields=dict(
                    download_ranking=('terms', 'file_key', {})
                ),
                main_fields=['item_id'],
                main_query={
                    "query": {
                        "bool": {
                            "filter": [
                                {
                                    "term": {
                                        "item_id": {
                                            "value": "@item_id",
                                            "boost": 1
                                        }
                                    }
                                },
                                {
                                    "terms": {
                                        "root_file_id": "@root_file_id_list"
                                    }
                                }
                            ]
                        }
                    },
                    "size": 0
                },
            )
        ),
    ]
