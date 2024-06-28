# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Celery background tasks."""

from .proxies import current_stats


def register_templates():
    """Register search templates for events."""
    event_templates = [
        event["templates"] for event in current_stats.events_config.values()
    ]
    aggregation_templates = [
        agg["templates"] for agg in current_stats.aggregations_config.values()
    ]

    return event_templates + aggregation_templates
