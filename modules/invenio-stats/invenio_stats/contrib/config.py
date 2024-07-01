# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Config for contributed events, aggregations and queries."""

from invenio_stats.aggregations import StatAggregator
from invenio_stats.contrib.event_builders import (
    build_file_unique_id,
    build_record_unique_id,
)
from invenio_stats.processors import EventsIndexer, anonymize_user, flag_robots
from invenio_stats.queries import DateHistogramQuery, TermsQuery

EVENTS_CONFIG = {
    "file-download": {
        "templates": "invenio_stats.contrib.file_download",
        "signal": "invenio_files_rest.signals.file_downloaded",
        "event_builders": [
            "invenio_stats.contrib.event_builders.file_download_event_builder"
        ],
        "cls": EventsIndexer,
        "params": {
            "preprocessors": [flag_robots, anonymize_user, build_file_unique_id]
        },
    },
    "record-view": {
        "templates": "invenio_stats.contrib.record_view",
        "signal": "invenio_records_ui.signals.record_viewed",
        "event_builders": [
            "invenio_stats.contrib.event_builders.record_view_event_builder"
        ],
        "cls": EventsIndexer,
        "params": {
            "preprocessors": [flag_robots, anonymize_user, build_record_unique_id]
        },
    },
}

AGGREGATIONS_CONFIG = {
    "file-download-agg": {
        "templates": "invenio_stats.contrib.aggregations.aggr_file_download",
        "cls": StatAggregator,
        "params": {
            "event": "file-download",
            "field": "unique_id",
            "interval": "day",
            "index_interval": "month",
            "copy_fields": {
                "file_key": "file_key",
                "bucket_id": "bucket_id",
                "file_id": "file_id",
            },
            "metric_fields": {
                "unique_count": (
                    "cardinality",
                    "unique_session_id",
                    {"precision_threshold": 1000},
                ),
                "volume": ("sum", "size", {}),
            },
        },
    },
    "record-view-agg": {
        "templates": "invenio_stats.contrib.aggregations.aggr_record_view",
        "cls": StatAggregator,
        "params": {
            "event": "record-view",
            "field": "unique_id",
            "interval": "day",
            "index_interval": "month",
            "copy_fields": {
                "record_id": "record_id",
                "pid_type": "pid_type",
                "pid_value": "pid_value",
            },
            "metric_fields": {
                "unique_count": (
                    "cardinality",
                    "unique_session_id",
                    {"precision_threshold": 1000},
                ),
            },
        },
    },
}


QUERIES_CONFIG = {
    "bucket-file-download-histogram": {
        "cls": DateHistogramQuery,
        "params": {
            "index": "stats-file-download",
            "copy_fields": {
                "bucket_id": "bucket_id",
                "file_key": "file_key",
            },
            "required_filters": {
                "bucket_id": "bucket_id",
                "file_key": "file_key",
            },
        },
    },
    "bucket-file-download-total": {
        "cls": TermsQuery,
        "params": {
            "index": "stats-file-download",
            "required_filters": {
                "bucket_id": "bucket_id",
            },
            "aggregated_fields": ["file_key"],
        },
    },
}
