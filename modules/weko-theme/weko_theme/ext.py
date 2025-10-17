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

"""Flask extension for weko-theme."""

from . import config


class WekoTheme(object):
    """weko-theme extension."""

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
        from weko_records.utils import get_keywords_data_load
        from weko_search_ui.api import get_search_detail_keyword
        from .views import blueprint
        self.init_config(app)
        app.register_blueprint(blueprint)
        app.extensions['weko-theme'] = self
        app.add_template_filter(get_keywords_data_load, name='item_type_all')
        app.add_template_filter(
            get_search_detail_keyword,
            name='detail_conditions')

    def init_config(self, app):
        """Initialize configuration.

        :param app: The Flask application.
        """
        for k in dir(config):
            app.config.setdefault(k, getattr(config, k))
        if "ADMIN_UI_SKIN" in app.config:
            app.config.update(
                ADMIN_UI_SKIN='skin-red',
            )
        else:
            app.config.setdefault("ADMIN_UI_SKIN", "skin-green")

        app.config.setdefault('WEKO_SHOW_INDEX_FOR_AUTHENTICATED_USER',
                              getattr(config, 'WEKO_SHOW_INDEX_FOR_AUTHENTICATED_USER'))


        app.config.setdefault('DISPLAY_LOGIN',
                              getattr(config, 'DISPLAY_LOGIN'))
        
        app.config.setdefault('ENABLE_COOKIE_CONSENT',
                              getattr(config, 'ENABLE_COOKIE_CONSENT'))