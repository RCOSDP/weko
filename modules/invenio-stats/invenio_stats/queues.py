# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Celery background tasks."""

from .proxies import current_stats


def declare_queues():
    """Index statistics events."""
    return [
        {"name": "stats-{0}".format(event), "exchange": current_stats.exchange}
        for event in current_stats.events_config
    ]
