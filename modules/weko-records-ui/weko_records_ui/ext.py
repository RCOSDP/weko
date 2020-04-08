# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Flask extension for weko-records-ui."""

from . import config
from .rest import create_blueprint
from .views import blueprint


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
        self.init_config(app)
        app.register_blueprint(blueprint)
        app.extensions['weko-records-ui'] = self

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
        self.init_config(app)
        blueprint = create_blueprint(
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
