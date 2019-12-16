# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module for metadata storage."""

from __future__ import absolute_import, print_function

from jsonref import JsonRef
from jsonresolver import JSONResolver
from jsonresolver.contrib.jsonref import json_loader_factory
from jsonresolver.contrib.jsonschema import ref_resolver_factory
from jsonschema import validate

from . import config
from .views import blueprint

class _RecordsState(object):
    """State for record JSON resolver."""

    def __init__(self, app, entry_point_group=None):
        """Initialize state."""
        self.app = app
        self.app.register_blueprint(blueprint)
        self.resolver = JSONResolver(entry_point_group=entry_point_group)
        self.ref_resolver_cls = ref_resolver_factory(self.resolver)
        self.loader_cls = json_loader_factory(self.resolver)

    def validate(self, data, schema, **kwargs):
        """Validate data using schema with ``JSONResolver``."""
        if not isinstance(schema, dict):
            schema = {'$ref': schema}
        return validate(
            data,
            schema,
            resolver=self.ref_resolver_cls.from_schema(schema),
            types=self.app.config.get('RECORDS_VALIDATION_TYPES', {}),
            **kwargs
        )

    def replace_refs(self, data):
        """Replace the JSON reference objects with ``JsonRef``."""
        return JsonRef.replace_refs(data, loader=self.loader_cls())


class InvenioRecords(object):
    """Invenio-Records extension."""

    def __init__(self, app=None, **kwargs):
        """Extension initialization."""
        if app:
            self._state = self.init_app(app, **kwargs)

    def init_app(self, app,
                 entry_point_group='invenio_records.jsonresolver', **kwargs):
        """Flask application initialization.

        :param app: The Flask application.
        :param entry_point_group: The entrypoint for jsonresolver extensions.
            (Default: ``'invenio_records.jsonresolver'``)
        """
        self.init_config(app)
        state = _RecordsState(app, entry_point_group=entry_point_group)
        app.extensions['invenio-records'] = state
        return state

    def init_config(self, app):
        """Initialize configuration.

        :param app: The Flask application.
        """
        app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', True)
        for k in dir(config):
            if k.startswith('RECORDS_'):
                app.config.setdefault(k, getattr(config, k))
