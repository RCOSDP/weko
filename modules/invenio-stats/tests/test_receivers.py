# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Signal receivers tests."""

import logging

from blinker import Namespace
from helpers import get_queue_size
from invenio_queues.proxies import current_queues

from invenio_stats import InvenioStats
from invenio_stats.proxies import current_stats


def test_register_receivers(app):
    """Test signal-receiving/event-emitting functions registration."""
    try:
        _signals = Namespace()
        my_signal = _signals.signal("my-signal")

        def event_builder1(event, sender_app, signal_param, *args, **kwargs):
            event.update({"event_param1": signal_param})
            return event

        def event_builder2(event, sender_app, signal_param, *args, **kwargs):
            event.update({"event_param2": event["event_param1"] + 1})
            return event

        # NOTE: event_0 already exists from the mocked events decorate further.
        app.config["STATS_EVENTS"]["event_0"].update(
            {"signal": my_signal, "event_builders": [event_builder1, event_builder2]}
        )

        InvenioStats(app)
        current_queues.declare()
        my_signal.send(app, signal_param=42)
        my_signal.send(app, signal_param=42)
        events = [event for event in current_stats.consume("event_0")]
        # two events should have been created from the sent events. They should
        # have been both processed by the two event builders.
        assert events == [{"event_param1": 42, "event_param2": 43}] * 2
    finally:
        current_queues.delete()


def test_failing_receiver(app, caplog):
    """Test failing signal receiver function."""
    try:
        _signals = Namespace()
        my_signal = _signals.signal("my-signal")

        def failing_event_builder(event, sender_app):
            raise Exception("builder-exception")

        # NOTE: event_0 already exists from the mocked events decorate further.
        app.config["STATS_EVENTS"]["event_0"].update(
            {"signal": my_signal, "event_builders": [failing_event_builder]}
        )

        InvenioStats(app)
        current_queues.declare()

        with caplog.at_level(logging.ERROR):
            my_signal.send(app)

        error_logs = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(error_logs) == 1
        assert error_logs[0].msg == "Error building event"
        assert error_logs[0].exc_info[1].args[0] == "builder-exception"

        # Check that no event was sent to the queue
        assert get_queue_size("stats-event_0") == 0
    finally:
        current_queues.delete()
