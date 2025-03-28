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
from .views import blueprint_ui


class WekoNotifications(object):
    """WEKO-Notifications extension."""

    def __init__(self, app=None):
        """Extension initialization.

        Args:
            app (flask.Flask | None): The Flask application.
        """
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization.

        Args:
            app (flask.Flask): The Flask application.
        """
        self.init_config(app)
        app.extensions["weko-notifications"] = self

        if app.config["WEKO_NOTIFICATIONS"]:
            app.register_blueprint(blueprint_ui)

    def init_config(self, app):
        """Initialize configuration.

        Args:
            app (flask.Flask): The Flask application.
        """

        app.config.setdefault(
            "WEKO_NOTIFICATIONS_BASE_TEMPLATE",
            app.config.get("BASE_TEMPLATE", "weko_notifications/base.html")
        )

        app.config.setdefault(
            "WEKO_NOTIFICATIONS_SETTINGS_TEMPLATE",
            app.config.get(
                "SETTINGS_TEMPLATE",
                "weko_notifications/settings/base.html"
            )
        )

        app.config.setdefault(
            "WEKO_NOTIFICATIONS", config.WEKO_NOTIFICATIONS
        )

        for k in dir(config):
            if k.startswith("WEKO_NOTIFICATIONS_"):
                app.config.setdefault(k, getattr(config, k))
