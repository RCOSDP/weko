# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Celery background tasks."""

from __future__ import absolute_import, print_function

from celery import shared_task
from celery.utils.log import get_task_logger
from dateutil.parser import parse as dateutil_parse

from .proxies import current_stats


@shared_task
def process_events(event_types):
    """Index statistics events."""
    results = []
    for e in event_types:
        processor = current_stats.events[e].processor_class(
            **current_stats.events[e].processor_config)
        results.append((e, processor.run()))
    return results


@shared_task
def aggregate_events(aggregations, start_date=None, end_date=None,
                     update_bookmark=True, manual=False):
    """Aggregate indexed events."""
    start_date = dateutil_parse(start_date) if start_date else None
    end_date = dateutil_parse(end_date) if end_date else None
    logger = get_task_logger(__name__)
    logger.debug("aggregate_events start_date:{}".format(start_date))
    logger.debug("aggregate_events end_date:{}".format(end_date))

    results = []
    for a in aggregations:
        aggr_cfg = current_stats.aggregations[a]
        aggregator = aggr_cfg.aggregator_class(
            name=aggr_cfg.name, **aggr_cfg.aggregator_config)
        results.append(aggregator.run(start_date, end_date, update_bookmark, manual))
    return results
