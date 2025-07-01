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

"""Flask extension for weko-items-ui."""

from . import config
from .signals import cris_researchmap_linkage_request ,receiver

class _WekoItemsUIState(object):
    """WekoItemsUI state."""

    def __init__(self, app, permission):
        """Initialize state.

        :param app: The Flask application.
        :param permission: The permission to restrict access.
        """
        self.app = app
        self.permission = permission


class WekoItemsUI(object):
    """weko-items-ui extension."""

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
        from .permissions import item_permission
        from .views import blueprint, check_ranking_show
        self.init_config(app)
        app.register_blueprint(blueprint)
        state = _WekoItemsUIState(app, item_permission)
        app.extensions['weko-items-ui'] = state
        app.jinja_env.globals.update(check_ranking_show=check_ranking_show)
        cris_researchmap_linkage_request.connect(receiver=receiver)

    def init_config(self, app):
        """Initialize configuration.

        :param app: The Flask application.
        """
        # Use theme's base template if theme is installed
        if 'BASE_PAGE_TEMPLATE' in app.config:
            app.config.setdefault(
                'WEKO_ITEMS_UI_BASE_TEMPLATE',
                app.config['BASE_PAGE_TEMPLATE'],
            )
        for k in dir(config):
            if k.startswith('WEKO_ITEMS_UI_'):
                app.config.setdefault(k, getattr(config, k))

class WekoItemsREST(object):
    """weko-items-ui-rest extension."""

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
        from .rest import create_blueprint
        self.init_config(app)
        blueprint_restapi = create_blueprint(
            app.config['WEKO_ITEMS_UI_REST_ENDPOINTS']
        )
        app.register_blueprint(blueprint_restapi)
        app.extensions['weko-items-ui-rest'] = self

    def init_config(self, app):
        """Initialize configuration.

        :param app: An instance of :class:`flask.Flask`.
        """
        for k in dir(config):
            if k.startswith('WEKO_ITEMS_UI_'):
                app.config.setdefault(k, getattr(config, k))