# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO-Notifications is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-notifications."""

from __future__ import absolute_import, print_function

from flask_babelex import gettext as _

from . import config


class WekoNotifications(object):
    """WEKO-Notifications extension."""

    def __init__(self, app=None):
        """Extension initialization.

        Args:
            app (flask.Flask | None): Flask application instance.
        """
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions['weko-notifications'] = self

    def init_config(self, app):
        """Initialize configuration."""
        # Use theme's base template if theme is installed
        if 'BASE_TEMPLATE' in app.config:
            app.config.setdefault(
                'WEKO_NOTIFICATIONS_BASE_TEMPLATE',
                app.config['BASE_TEMPLATE'],
            )
        for k in dir(config):
            if k.startswith('WEKO_NOTIFICATIONS_'):
                app.config.setdefault(k, getattr(config, k))
