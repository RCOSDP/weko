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

"""Flask extension for weko-records-ui."""

from invenio_oauth2server.ext import verify_oauth_token_and_set_current_user

from . import config
from .rest import create_blueprint, create_blueprint_cites
from .views import blueprint
from weko_admin import config as admin_config


class WekoRecordsUI(object):
    """weko-records-ui extension."""

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
        from .views import blueprint
        self.init_config(app)
        app.register_blueprint(blueprint)
        app.extensions['weko-records-ui'] = self
        app.before_request(verify_oauth_token_and_set_current_user)

    def init_config(self, app):
        """Initialize configuration.

        :param app: The Flask application.
        """
        # Use theme's base template if theme is installed
        if 'BASE_PAGE_TEMPLATE' in app.config:
            app.config.setdefault(
                'WEKO_RECORDS_UI_BASE_TEMPLATE',
                app.config['BASE_PAGE_TEMPLATE'],
            )
        for k in dir(config):
            if k.startswith('WEKO_RECORDS_UI_'):
                app.config.setdefault(k, getattr(config, k))
        app.config.setdefault('ITEM_SEARCH_FLG',
                              getattr(config, 'ITEM_SEARCH_FLG'))
        app.config.setdefault('EMAIL_DISPLAY_FLG',
                              getattr(config, 'EMAIL_DISPLAY_FLG'))

class WekoRecordsREST(object):
    """weko-record-ui-rest extension."""

    def __init__(self, app=None):
        """Extension initialization.

        :param app: An instance of :class:`flask.Flask`.
        """
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization.

        Initialize the REST endpoints. Connect all signals if
        `DEPOSIT_REGISTER_SIGNALS` is True.

        :param app: An instance of :class:`flask.Flask`.
        """
        from .rest import create_blueprint
        self.init_config(app)
        blueprint = create_blueprint(
            app.config['WEKO_RECORDS_UI_REST_ENDPOINTS']
        )
        app.register_blueprint(blueprint)
        app.extensions['weko-records-ui-rest'] = self

    def init_config(self, app):
        """Initialize configuration.

        :param app: An instance of :class:`flask.Flask`.
        """
        for k in dir(config):
            if k.startswith('WEKO_RECORDS_UI_'):
                app.config.setdefault(k, getattr(config, k))
        for k in dir(admin_config):
            if k.startswith('WEKO_ADMIN_'):
                app.config.setdefault(k, getattr(admin_config, k))

class WekoRecordsREST(object):
    """weko-record-ui-rest extension."""

    def __init__(self, app=None):
        """Extension initialization.

        :param app: An instance of :class:`flask.Flask`.
        """
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization.

        Initialize the REST endpoints. Connect all signals if
        `DEPOSIT_REGISTER_SIGNALS` is True.

        :param app: An instance of :class:`flask.Flask`.
        """
        self.init_config(app)
        blueprint = create_blueprint(
            app.config['WEKO_RECORDS_UI_REST_ENDPOINTS']
        )
        app.register_blueprint(blueprint)
        app.extensions['weko-records-ui-rest'] = self

    def init_config(self, app):
        """Initialize configuration.

        :param app: An instance of :class:`flask.Flask`.
        """
        for k in dir(config):
            if k.startswith('WEKO_RECORDS_UI_'):
                app.config.setdefault(k, getattr(config, k))
        for k in dir(admin_config):
            if k.startswith('WEKO_ADMIN_'):
                app.config.setdefault(k, getattr(admin_config, k))


class WekoRecordsCitesREST(object):
    """weko-record-ui-rest extension."""

    def __init__(self, app=None):
        """Extension initialization.

        :param app: An instance of :class:`flask.Flask`.
        """
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization.

        Initialize the REST endpoints.  Connect all signals if
        `DEPOSIT_REGISTER_SIGNALS` is True.

        :param app: An instance of :class:`flask.Flask`.
        """
        from .rest import create_blueprint_cites
        self.init_config(app)
        blueprint = create_blueprint_cites(
            app.config['WEKO_RECORDS_UI_CITES_REST_ENDPOINTS']
        )
        app.register_blueprint(blueprint)
        app.extensions['weko-records-ui-cites-rest'] = self

    def init_config(self, app):
        """Initialize configuration.

        :param app: An instance of :class:`flask.Flask`.
        """
        for k in dir(config):
            if k.startswith('WEKO_RECORDS_UI_CITES_'):
                app.config.setdefault(k, getattr(config, k))
