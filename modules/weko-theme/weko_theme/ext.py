# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Flask extension for weko-theme."""

from weko_records.utils import get_keywords_data_load
from weko_search_ui.api import get_search_detail_keyword

from . import config
from .views import blueprint


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
