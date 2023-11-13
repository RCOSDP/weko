# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2020 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio Queues utility functions."""

from flask import current_app
from kombu import Connection
from kombu.pools import connections


def get_connection_pool():
    """Retrieve the broker connection pool."""
    broker_url = current_app.config.get("QUEUES_BROKER_URL") or current_app.config.get(
        "BROKER_URL", "amqp://"
    )
    return connections[Connection(broker_url)]
