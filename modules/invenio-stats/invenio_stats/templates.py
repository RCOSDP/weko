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
    """Register elasticsearch templates for events."""
    event_templates = [current_stats._events_config[e]
                       ['templates']
                       for e in
                       current_stats._events_config]
    aggregation_templates = [current_stats._aggregations_config[a]
                             ['templates']
                             for a in
                             current_stats._aggregations_config]
    return event_templates + aggregation_templates
