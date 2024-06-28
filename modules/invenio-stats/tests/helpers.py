# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio Stats testing helpers."""

import datetime
import time

from invenio_queues.proxies import current_queues


def get_queue_size(queue_name):
    """Get the current number of messages in a queue."""
    queue = current_queues.queues[queue_name]
    time.sleep(1)  # necessary, queue returning random sizes otherwise
    _, size, _ = queue.queue.queue_declare(passive=True)
    return size


def mock_date(*date_parts):
    """Mocked 'datetime.utcnow()'."""

    class MockDate(datetime.datetime):
        """datetime.datetime mock."""

        @classmethod
        def utcnow(cls):
            """Override to return 'current_date'."""
            return cls(*date_parts)

    return MockDate
