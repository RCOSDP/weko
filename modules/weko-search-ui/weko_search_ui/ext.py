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

"""Flask extension for weko-search-ui."""

from . import config
from .views import blueprint
from .rest import create_blueprint

class WekoSearchUI(object):
    """weko-search-ui extension."""

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
        app.extensions['weko-search-ui'] = self

        # to integrate search and search index url
        from .views import search
        app.view_functions['invenio_search_ui.search'] = search

    def init_config(self, app):
        """Initialize configuration.

        :param app: The Flask application.
        """
        # Use theme's base template if theme is installed
        if 'BASE_PAGE_TEMPLATE' in app.config:
            app.config.setdefault(
                'WEKO_SEARCH_UI_BASE_PAGE_TEMPLATE',
                app.config['BASE_PAGE_TEMPLATE'],
            )

        app.config.setdefault( 'INDEX_IMG', app.config['INDEX_IMG'])

        app.config.update(
            SEARCH_UI_SEARCH_TEMPLATE=getattr(
                config,
                'WEKO_SEARCH_UI_SEARCH_TEMPLATE'),
            SEARCH_UI_JSTEMPLATE_RESULTS=getattr(
                config,
                'WEKO_SEARCH_UI_JSTEMPLATE_RESULTS'),
            SEARCH_UI_JSTEMPLATE_RESULTS_BASIC=getattr(
                config,
                'WEKO_SEARCH_UI_JSTEMPLATE_RESULTS_BASIC'),
            SEARCH_UI_JSTEMPLATE_COUNT=getattr(
                config,
                'WEKO_SEARCH_UI_JSTEMPLATE_COUNT'),
        )

        for k in dir(config):
            if k.startswith('WEKO_SEARCH_UI_'):
                app.config.setdefault(k, getattr(config, k))


class WekoSearchREST(object):
    """
      Index Search Rest Obj
    """

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
        blueprint = create_blueprint(app,
                                     app.config['WEKO_SEARCH_REST_ENDPOINTS']
                                     )
        app.register_blueprint(blueprint)
        app.extensions['weko-search-rest'] = self
