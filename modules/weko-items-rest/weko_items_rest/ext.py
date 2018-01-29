# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Flask extension for weko-items-rest."""

from werkzeug.utils import cached_property

from . import config
from .utils import build_default_endpoint_prefixes, \
    load_or_import_from_config, obj_or_import_string
from .views import create_blueprint


class _RecordRESTState(object):
    """Record REST state."""

    def __init__(self, app):
        """Initialize state.

        :param app: The Flask application.
        """
        self.app = app

    @cached_property
    def loaders(self):
        """Load default read permission factory."""
        return load_or_import_from_config(
            'ITEMS_REST_DEFAULT_LOADERS', app=self.app
        )

    @cached_property
    def read_permission_factory(self):
        """Load default read permission factory."""
        return load_or_import_from_config(
            'ITEMS_REST_DEFAULT_READ_PERMISSION_FACTORY', app=self.app
        )

    @cached_property
    def create_permission_factory(self):
        """Load default create permission factory."""
        return load_or_import_from_config(
            'ITEMS_REST_DEFAULT_CREATE_PERMISSION_FACTORY', app=self.app
        )

    @cached_property
    def update_permission_factory(self):
        """Load default update permission factory."""
        return load_or_import_from_config(
            'ITEMS_REST_DEFAULT_UPDATE_PERMISSION_FACTORY', app=self.app
        )

    @cached_property
    def delete_permission_factory(self):
        """Load default delete permission factory."""
        return load_or_import_from_config(
            'ITEMS_REST_DEFAULT_DELETE_PERMISSION_FACTORY', app=self.app
        )

    @cached_property
    def default_endpoint_prefixes(self):
        """Map between pid_type and endpoint_prefix."""
        return build_default_endpoint_prefixes(
            self.app.config['ITEMS_REST_ENDPOINTS']
        )

    def reset_permission_factories(self):
        """Remove cached permission factories."""
        for key in ('read', 'create', 'update', 'delete'):
            full_key = '{0}_permission_factory'.format(key)
            if full_key in self.__dict__:
                del self.__dict__[full_key]


class WekoItemsREST(object):
    """weko-items-rest extension."""

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
        app.register_blueprint(
            create_blueprint(app.config['ITEMS_REST_ENDPOINTS'])
        )
        app.extensions['weko-items-rest'] = _RecordRESTState(app)

    def init_config(self, app):
        """Initialize configuration.

        :param app: The Flask application.
        """
        # Set up API endpoints for records.
        for k in dir(config):
            if k.startswith('ITEMS_REST_'):
                app.config.setdefault(k, getattr(config, k))

        # Resolve the Elasticsearch error handlers
        handlers = app.config['ITEMS_REST_ELASTICSEARCH_ERROR_HANDLERS']
        for k, v in handlers.items():
            handlers[k] = obj_or_import_string(v)
