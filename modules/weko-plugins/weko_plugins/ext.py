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

"""Flask extension for weko-plugins."""

import os
import sys

from flask import current_app
from flask_plugins import PluginManager, get_enabled_plugins
from werkzeug.local import LocalProxy
from . import config
from .views import blueprint

current_plugins = LocalProxy(lambda: current_app.extensions['weko-plugins'])

class WekoPlugins(object):
    """weko-plugins extension."""

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
        self.plugin_manager = PluginManager()
        sys.path.append('/code')
        root_path = app.root_path
        app.root_path = os.path.join('/code', 'plugins')
        self.plugin_manager.init_app(app,
                                     base_app_folder='plugins',
                                     plugin_folder='plugin')
        app.root_path = root_path
        app.register_blueprint(blueprint)
        # Register Jinja2 template filters for plugins formatting
        app.add_template_global(current_plugins, name='current_plugins')
        app.extensions['weko-plugins'] = self

    def init_config(self, app):
        """Initialize configuration.

        :param app: The Flask application.
        """
        # Use theme's base template if theme is installed
        if 'BASE_EDIT_TEMPLATE' in app.config:
            app.config.setdefault(
                'WEKO_PLUGINS_BASE_TEMPLATE',
                app.config['BASE_EDIT_TEMPLATE'],
            )
        for k in dir(config):
            if k.startswith('WEKO_PLUGINS_'):
                app.config.setdefault(k, getattr(config, k))

    def get_enabled_plugins(self):
        """
        return all enabled plugins list
        :return: Pluging List Info
        """
        plugins = get_enabled_plugins()
        return tuple(map(lambda plugin: (plugin.name, plugin.identifier) if plugin.enabled else None, plugins))
