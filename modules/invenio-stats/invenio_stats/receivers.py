# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
# Copyright (C)      2022 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Function registering signal-receiving/event-emitting functions."""

from flask import current_app
from invenio_base.utils import obj_or_import_string

from .proxies import current_stats


class EventEmitter(object):
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
            current_app.logger.exception("Error building event")


def build_event_emitter(event_name, events_config=None):
    """Create a stats event emitter for the registered name as per configuration.

    :param event_name: The name of the event for which the emitter should be built.
    :param events_config: The configuration to use for building the event emitter,
                          defaults to ``current_stats.events_config``.
    :return: An initialized ``EventEmitter`` instance.
    """
    events_config = events_config or current_stats.events_config

    if event_name not in events_config:
        current_app.logger.warn(
            f"Tried to build event emitter for unregistered event '{event_name}'"
        )
        return None

    event_builders = [
        obj_or_import_string(builder)
        for builder in events_config[event_name].get("event_builders", [])
    ]

    return EventEmitter(event_name, event_builders)


def register_receivers(app, config):
    """Register signal receivers which send events."""
    for event_name, event_config in config.items():
        event_emitter = build_event_emitter(event_name, config)
        signal = obj_or_import_string(event_config["signal"])
        signal.connect(event_emitter, sender=app, weak=False)


# for backwards compatibility
EventEmmiter = EventEmitter
