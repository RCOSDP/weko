# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module for managing queues."""

from itertools import chain

from werkzeug.utils import cached_property

from . import config
from .errors import DuplicateQueueError
from .queue import Queue


class _InvenioQueuesState(object):
    """State object for Invenio queues."""

    def __init__(self, app, connection_pool, entry_point_group):
        self.app = app
        self._queues = None
        self.connection_pool = connection_pool
        self.entry_point_group = entry_point_group

    @cached_property
    def queues(self):
        # NOTE: import iter_entry_points here so it can be mocked in tests
        from pkg_resources import iter_entry_points

        if self._queues is None:
            self._queues = dict()
            from_entry_point = [
                ep.load()() for ep in iter_entry_points(group=self.entry_point_group)
            ]

            for queue in chain(
                from_entry_point, [self.app.config["QUEUES_DEFINITIONS"]]
            ):
                for cfg in queue:
                    if cfg["name"] in self._queues:
                        raise DuplicateQueueError(
                            "Duplicate queue {0} found".format(cfg["name"])
                        )

                    self._queues[cfg["name"]] = Queue(
                        cfg["exchange"], cfg["name"], self.connection_pool
                    )

        return self._queues

    def _action(self, action, queues=None):
        for q in queues or self.queues:
            getattr(self.queues[q].queue, action)()

    def declare(self, **kwargs):
        """Declare queue for all or specific event types."""
        self._action("declare", **kwargs)

    def delete(self, **kwargs):
        """Delete queue for all or specific event types."""
        self._action("delete", **kwargs)

    def purge(self, force=False, **kwargs):
        """Purge queue for all or specific event types."""
        try:
            self._action("purge", **kwargs)
        except Exception:
            if not force:
                raise


class InvenioQueues(object):
    """Invenio-Queues extension."""

    def __init__(self, app=None, **kwargs):
        """Initialize extension."""
        if app:
            self.init_app(app, **kwargs)

    def __getattr__(self, name):
        """Proxy to state object."""
        return getattr(object.__getattribute__(self, "_state"), name)

    def init_app(self, app, entry_point_group="invenio_queues.queues"):
        """Initialize application."""
        self.init_config(app)
        state = _InvenioQueuesState(
            app,
            app.config["QUEUES_CONNECTION_POOL"],
            entry_point_group=entry_point_group,
        )
        self._state = state
        app.extensions["invenio-queues"] = state
        return app

    def init_config(self, app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith("QUEUES_"):
                app.config.setdefault(k, getattr(config, k))
