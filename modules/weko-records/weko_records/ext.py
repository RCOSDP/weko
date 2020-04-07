# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""weko records extension."""

from . import config


class WekoRecords(object):
    """weko-records extension."""

    def __init__(self, app=None):
        """Extension initialization.

        :param app: The Flask application.
        """
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization.

        :param app: The Flask application.
        """
        self.init_config(app)
        app.extensions['weko-records'] = self

    def init_config(self, app):
        """Initialize configuration.

        :param app: The Flask application.
        """
        # Use theme's base template if theme is installed
        if 'BASE_TEMPLATE' in app.config:
            app.config.setdefault(
                'WEKO_RECORDS_BASE_TEMPLATE',
                app.config['BASE_TEMPLATE'],
            )
        for k in dir(config):
            if k.startswith('WEKO_RECORDS_'):
                app.config.setdefault(k, getattr(config, k))
