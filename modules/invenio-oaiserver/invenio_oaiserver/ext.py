# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2022 CERN.
# Copyright (C) 2021-2022 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio-OAIServer extension implementation."""

from invenio_base.utils import obj_or_import_string
from sqlalchemy.event import contains, listen, remove

from . import config


class _AppState(object):
    """State for Invenio-OAIServer."""

    def __init__(self, app, cache=None):
        """Initialize state.

        :param app: An instance of :class:`flask.Flask`.
        """
        self.app = app
        self.cache = cache
        if self.app.config["OAISERVER_REGISTER_RECORD_SIGNALS"]:
            self.register_signals()

    @property
    def search_cls(self):
        """Get OAI Search class."""
        return obj_or_import_string(self.app.config["OAISERVER_SEARCH_CLS"])

    @property
    def oaiid_fetcher(self):
        """Get OAI ID fetcher."""
        return obj_or_import_string(self.app.config["OAISERVER_ID_FETCHER"])

    @property
    def record_sets_fetcher(self):
        """Get OAI record sets fetcher."""
        return obj_or_import_string(self.app.config["OAISERVER_RECORD_SETS_FETCHER"])

    @property
    def record_cls(self):
        """Get the record class for record retrieval."""
        return obj_or_import_string(self.app.config["OAISERVER_RECORD_CLS"])

    @property
    def record_fetcher(self):
        """Get the record fetcher class for record serialization."""
        return obj_or_import_string(self.app.config["OAISERVER_GETRECORD_FETCHER"])

    @property
    def set_records_query_fetcher(self):
        """Get query to retrieve records based on set."""
        return obj_or_import_string(
            self.app.config["OAISERVER_SET_RECORDS_QUERY_FETCHER"]
        )

    @property
    def last_update_key(self):
        """Get record update key."""
        return self.app.config["OAISERVER_LAST_UPDATE_KEY"]

    @property
    def created_key(self):
        """Get record created key."""
        return self.app.config["OAISERVER_CREATED_KEY"]

    @property
    def sets(self):
        """Get list of sets."""
        if self.cache:
            return self.cache.get(self.app.config["OAISERVER_CACHE_KEY"])

    @sets.setter
    def sets(self, values):
        """Set list of sets."""
        # if cache server is configured, save sets list
        if self.cache:
            self.cache.set(self.app.config["OAISERVER_CACHE_KEY"], values)

    def register_signals(self):
        """Register signals."""
        if self.app.config["OAISERVER_REGISTER_SET_SIGNALS"]:
            self.register_signals_oaiset()

    def register_signals_oaiset(self):
        """Register OAISet signals to update records."""
        from .models import OAISet
        from .receivers import (
            after_delete_oai_set,
            after_insert_oai_set,
            after_update_oai_set,
        )

        listen(OAISet, "after_insert", after_insert_oai_set)
        listen(OAISet, "after_update", after_update_oai_set)
        listen(OAISet, "after_delete", after_delete_oai_set)

    def unregister_signals(self):
        """Unregister signals."""
        # Unregister Record signals
        self.unregister_signals_oaiset()

    def unregister_signals_oaiset(self):
        """Unregister signals oaiset."""
        from .models import OAISet
        from .receivers import (
            after_delete_oai_set,
            after_insert_oai_set,
            after_update_oai_set,
        )

        if contains(OAISet, "after_insert", after_insert_oai_set):
            remove(OAISet, "after_insert", after_insert_oai_set)
            remove(OAISet, "after_update", after_update_oai_set)
            remove(OAISet, "after_delete", after_delete_oai_set)


class InvenioOAIServer(object):
    """Invenio-OAIServer extension."""

    def __init__(self, app=None, **kwargs):
        """Extension initialization.

        :param app: An instance of :class:`flask.Flask`. (Default: ``None``)
        """
        if app:
            self.init_app(app, **kwargs)

    def init_app(self, app, **kwargs):
        """Flask application initialization.

        :param app: An instance of :class:`flask.Flask`.
        """
        self.init_config(app)
        state = _AppState(app=app, cache=kwargs.get("cache"))
        app.extensions["invenio-oaiserver"] = state

    def init_config(self, app):
        """Initialize configuration.

        :param app: An instance of :class:`flask.Flask`.
        """
        app.config.setdefault(
            "OAISERVER_BASE_TEMPLATE",
            app.config.get("BASE_TEMPLATE", "invenio_oaiserver/base.html"),
        )

        app.config.setdefault(
            "OAISERVER_REPOSITORY_NAME",
            app.config.get("THEME_SITENAME", "Invenio-OAIServer"),
        )

        for k in dir(config):
            if k.startswith("OAISERVER_"):
                app.config.setdefault(k, getattr(config, k))

        # warn user if ID_PREFIX is not set
        if app.config.get("OAISERVER_ID_PREFIX") is None:
            import socket
            import warnings

            app.config["OAISERVER_ID_PREFIX"] = "oai:{0}:".format(socket.gethostname())
            warnings.warn(
                """Please specify the OAISERVER_ID_PREFIX configuration."""
                """default value is: {0}""".format(
                    app.config.get("OAISERVER_ID_PREFIX")
                )
            )
