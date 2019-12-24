# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Flask extension for the Invenio-Records-REST."""

from __future__ import absolute_import, print_function

from werkzeug.utils import cached_property

from . import config
from .utils import build_default_endpoint_prefixes, \
    load_or_import_from_config, obj_or_import_string
from .views import create_blueprint


class _RecordRESTState(object):
    """Record REST state."""

    def __init__(self, app):
        """Initialize state."""
        self.app = app

    @cached_property
    def loaders(self):
        """Load default read permission factory."""
        return load_or_import_from_config(
            'RECORDS_REST_DEFAULT_LOADERS', app=self.app
        )

    @cached_property
    def read_permission_factory(self):
        """Load default read permission factory."""
        return load_or_import_from_config(
            'RECORDS_REST_DEFAULT_READ_PERMISSION_FACTORY', app=self.app
        )

    @cached_property
    def create_permission_factory(self):
        """Load default create permission factory."""
        return load_or_import_from_config(
            'RECORDS_REST_DEFAULT_CREATE_PERMISSION_FACTORY', app=self.app
        )

    @cached_property
    def update_permission_factory(self):
        """Load default update permission factory."""
        return load_or_import_from_config(
            'RECORDS_REST_DEFAULT_UPDATE_PERMISSION_FACTORY', app=self.app
        )

    @cached_property
    def delete_permission_factory(self):
        """Load default delete permission factory."""
        return load_or_import_from_config(
            'RECORDS_REST_DEFAULT_DELETE_PERMISSION_FACTORY', app=self.app
        )

    @cached_property
    def list_permission_factory(self):
        """Load default read permission factory."""
        return load_or_import_from_config(
            'RECORDS_REST_DEFAULT_LIST_PERMISSION_FACTORY', app=self.app
        )

    @cached_property
    def default_endpoint_prefixes(self):
        """Map between pid_type and endpoint_prefix."""
        return build_default_endpoint_prefixes(
            self.app.config['RECORDS_REST_ENDPOINTS']
        )

    def reset_permission_factories(self):
        """Remove cached permission factories."""
        for key in ('read', 'create', 'update', 'delete'):
            full_key = '{0}_permission_factory'.format(key)
            if full_key in self.__dict__:
                del self.__dict__[full_key]


class InvenioRecordsREST(object):
    """Invenio-Records-REST extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions['invenio-records-rest'] = _RecordRESTState(app)

    def init_config(self, app):
        """Initialize configuration."""
        # Set up API endpoints for records.
        for k in dir(config):
            if k.startswith('RECORDS_REST_'):
                app.config.setdefault(k, getattr(config, k))

        # Resolve the Elasticsearch error handlers
        handlers = app.config['RECORDS_REST_ELASTICSEARCH_ERROR_HANDLERS']
        for k, v in handlers.items():
            handlers[k] = obj_or_import_string(v)
