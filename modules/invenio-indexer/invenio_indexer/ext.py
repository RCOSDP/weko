# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2022 CERN.
# Copyright (C) 2016 TIND.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Flask exension for Invenio-Indexer."""

from flask import current_app
from werkzeug.utils import cached_property, import_string

from . import config
from .cli import run  # noqa
from .registry import IndexerRegistry
from .signals import before_record_index


class InvenioIndexer(object):
    """Invenio-Indexer extension."""

    def __init__(self, app=None):
        """Extension initialization.

        :param app: The Flask application. (Default: ``None``)
        """
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization.

        :param app: The Flask application.
        """
        self.init_config(app)
        self.registry = IndexerRegistry()
        app.extensions["invenio-indexer"] = self

        hooks = app.config.get("INDEXER_BEFORE_INDEX_HOOKS", [])
        for hook in hooks:
            if isinstance(hook, str):
                hook = import_string(hook)
            before_record_index.connect_via(app)(hook)

    def init_config(self, app):
        """Initialize configuration.

        :param app: The Flask application.
        """
        for k in dir(config):
            if k.startswith("INDEXER_"):
                app.config.setdefault(k, getattr(config, k))

    @cached_property
    def record_to_index(self):
        """Import the configurable 'record_to_index' function."""
        return import_string(current_app.config.get("INDEXER_RECORD_TO_INDEX"))
