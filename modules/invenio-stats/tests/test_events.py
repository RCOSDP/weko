# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Events tests."""
import pytest

from invenio_queues.proxies import current_queues

from invenio_stats.proxies import current_stats


@pytest.mark.skip('This test dont ever finish')
def test_event_queues_declare(app, event_entrypoints):
    """Test that event queues are declared properly."""
    try:
        for event in current_stats.events.values():
            assert not event.queue.exists
        current_queues.declare()
        for event in current_stats.events.values():
            assert event.queue.exists
    finally:
        current_queues.delete()


@pytest.mark.skip('This test dont ever finish')
def test_publish_and_consume_events(app, event_entrypoints):
    """Test that events are published and consumed properly."""
    try:
        event_type = 'file-download'
        events = [{"payload": "test {}".format(idx)} for idx in range(3)]
        current_queues.declare()
        current_stats.publish(event_type, events)
        assert list(current_stats.consume(event_type)) == events
    finally:
        current_queues.delete()
