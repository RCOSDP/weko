# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Weko logging user audit logger app."""

import logging

from weko_logging import config
from weko_logging.views import blueprint
from weko_logging.handler import UserActivityLogHandler
from weko_logging.ext import WekoLoggingBase

class WekoLoggingUserActivity(WekoLoggingBase):
    """WEKO-Logging extension. Filesystem handler."""

    def init_app(self, app):
        """
        Initialize the Flask application.

        Args:
            app (Flask): The Flask application.
        """
        self.init_config(app)
        app.register_blueprint(blueprint)
        user_logger = self.init_logger(app)
        app.extensions["weko-logging-activity"] = user_logger

    def init_config(self, app):
        """
        Initialize configuration.

        Args:
            app (Flask): The Flask application.
        """
        for k in dir(config):
            if k.startswith("WEKO_LOGGING") and not k.startswith("WEKO_LOGGING_FS"):
                app.config.setdefault(k, getattr(config, k))

    def init_logger(self, app):
        """
        Install log handler on Flask application.

        Args:
            app (Flask): The Flask application.

        Returns:
            logging.Logger: The user activity logger.
        """
        user_logger = logging.getLogger("user-activity")
        user_logger.setLevel(logging.INFO)
        user_logger.handlers.clear()
        stream_handler_settings = app.config.get(
            "WEKO_LOGGING_USER_ACTIVITY_STREAM_SETTING", {}
        )

        stream_handler = logging.StreamHandler()
        stream_log_level = get_level_from_string(
            stream_handler_settings.get("log_level", "ERROR")
        )
        stream_handler.setLevel(stream_log_level)
        stream_handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] - %(levelname)s - %(filename)s - %(name)s - %(funcName)s - %(message)s "
                "[in %(pathname)s:%(lineno)d]"
            )
        )
        user_logger.addHandler(stream_handler)

        db_handler = UserActivityLogHandler(app)
        db_handler_settings = app.config.get(
            "WEKO_LOGGING_USER_ACTIVITY_DB_SETTING", {}
        )
        db_log_level = get_level_from_string(
            db_handler_settings.get("log_level", "ERROR")
        )
        db_handler.setLevel(db_log_level)

        # Add handler to application logger
        user_logger.addHandler(db_handler)
        return user_logger


def get_level_from_string(level):
    """
    Get log level from string.

    Args:
        level (str): The log level string.

    Returns:
        int: The log level.
    """
    return getattr(logging, level.upper(), logging.ERROR)
