# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Signal receivers tests."""

import pytest
import logging

from blinker import Namespace
from tests.helpers import get_queue_size
from invenio_queues.proxies import current_queues

from invenio_stats import InvenioStats
from invenio_stats.proxies import current_stats


@pytest.mark.skip('This test dont ever finish')
def test_register_receivers(base_app, event_entrypoints):
    """Test signal-receiving/event-emitting functions registration."""
    try:
        _signals = Namespace()
        my_signal = _signals.signal('my-signal')

        def event_builder1(event, sender_app, signal_param, *args, **kwargs):
            event.update(dict(event_param1=signal_param))
            return event

        def event_builder2(event, sender_app, signal_param, *args, **kwargs):
            event.update(dict(event_param2=event['event_param1'] + 1))
            return event

        base_app.config.update(dict(
            STATS_EVENTS=dict(
                event_0=dict(
                    signal=my_signal,
                    event_builders=[event_builder1, event_builder2]
                )
            )
        ))
        InvenioStats(base_app)
        current_queues.declare()
        my_signal.send(base_app, signal_param=42)
        my_signal.send(base_app, signal_param=42)
        events = [event for event in current_stats.consume('event_0')]
        # two events should have been created from the sent events. They should
        # have been both processed by the two event builders.
        assert events == [{'event_param1': 42, 'event_param2': 43}] * 2
    finally:
        current_queues.delete()


@pytest.mark.skip('This test dont ever finish')
def test_failing_receiver(base_app, event_entrypoints, caplog):
    """Test failing signal receiver function."""
    try:
        _signals = Namespace()
        my_signal = _signals.signal('my-signal')

        def failing_event_builder(event, sender_app):
            raise Exception('builder-exception')

        base_app.config.update(dict(
            STATS_EVENTS=dict(
                event_0=dict(
                    signal=my_signal,
                    event_builders=[failing_event_builder]
                )
            )
        ))
        InvenioStats(base_app)
        current_queues.declare()

        with caplog.at_level(logging.ERROR):
            my_signal.send(base_app)

        error_logs = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(error_logs) == 1
        assert error_logs[0].msg == 'Error building event'
        assert error_logs[0].exc_info[1].args[0] == 'builder-exception'

        # Check that no event was sent to the queue
        assert get_queue_size('stats-event_0') == 0
    finally:
        current_queues.delete()
