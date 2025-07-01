# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO-Notifications is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-notifications."""

from __future__ import absolute_import, print_function

from flask import request
from flask_babelex import gettext as _

from . import config
from .utils import inbox_url
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

            @app.after_request
            def inbox_link(response):
                """Add inbox link to the response headers."""
                endpoint = request.endpoint
                method = request.method
                if endpoint != "weko_theme.index" or method != "HEAD":
                    return response

                inbox_link = inbox_url(app=app, _external=True)
                links = [
                    link.strip()
                    for link in response.headers.get("Link", "").split(",")
                    if link
                ] + [f'<{inbox_link}>; rel="{config.COAR_NOTIFY_LINK_REL}"']
                response.headers["Link"] = ", ".join(links)

                return response

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
