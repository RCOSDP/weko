# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Function registering signal-receiving/event-emitting functions."""

from __future__ import absolute_import, print_function

from flask import current_app

from .proxies import current_stats
from .utils import obj_or_import_string


class EventEmmiter(object):
    """Receive a signal and send an event."""

    def __init__(self, name, builders):
        """Contructor."""
        self.name = name
        self.builders = builders

    def __call__(self, *args, **kwargs):
        """Receive a signal and send an event."""
        # Send the event only if it is registered
        try:
            if self.name in current_stats.events:
                event = {}
                for builder in self.builders:
                    event = builder(event, *args, **kwargs)
                    if event is None:
                        return
                current_stats.publish(self.name, [event])
        except Exception:
            current_app.logger.exception(u'Error building event')


def register_receivers(app, config):
    """Register signal receivers which send events."""
    for event_name, event_config in config.items():
        event_builders = [
            obj_or_import_string(func)
            for func in event_config.get('event_builders', [])
        ]

        signal = obj_or_import_string(event_config['signal'])
        if isinstance(signal, list):
            for sig in signal:
                sig = obj_or_import_string(sig)
                sig.connect(
                    EventEmmiter(event_name, event_builders), sender=app,
                    weak=False)
        else:
            signal.connect(
                EventEmmiter(
                    event_name,
                    event_builders),
                sender=app,
                weak=False)
