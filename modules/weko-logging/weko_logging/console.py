# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Logging is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Weko logging module.

This extension is enabled by default and automatically installed via
``invenio_base.apps`` and ``invenio_base.api_apps`` entry points.
"""

import sys
import logging
import inspect
import traceback

from . import config
from .ext import WekoLoggingBase
from .utils import wekoLoggingFilter
from .resource import WEKO_COMMON_MESSAGE

class WekoLoggingConsole(WekoLoggingBase):
    """Invenio-Logging extension for console."""

    def init_app(self, app):
        """Flask application initialization.

        Method to initialize the Flask application.
        """
        self.init_config(app)

        if not app.config["WEKO_LOGGING_CONSOLE"]:
            return

        self.install_handler(app)

        app.extensions["weko-logging-console"] = self

    def init_config(self, app):
        """Initialize config.

        Method to initialize the configuration of the Flask application.
        """
        for k in dir(config):
            if k.startswith("WEKO_LOGGING_CONSOLE"):
                app.config.setdefault(k, getattr(config, k))

    def install_handler(self, app):
        """Install logging handler.

        Method to install the logging handler in the Flask application.
        Configure the log level and format of the log output.

        Args:
            app (Flask): \
                The Flask application.

        Returns:
            None
        """
        # Configure python logging
        if app.config["WEKO_LOGGING_CONSOLE_LEVEL"] is not None:
            app.logger.setLevel(app.config["WEKO_LOGGING_CONSOLE_LEVEL"])

        format = '[%(asctime)s,%(msecs)03d][%(levelname)s] weko - '\
                 '(id %(user_id)s, ip %(ip_address)s) - %(message)s '\
                 '[file %(pathname)s line %(lineno)d in %(funcName)s]'
        datefmt = '%Y-%m-%d %H:%M:%S'
        formatter = logging.Formatter(fmt=format, datefmt=datefmt)

        if app.logger.handlers:
            # if app.logger has handlers, set level and formatter
            for h in app.logger.handlers:
                if app.config["WEKO_LOGGING_CONSOLE_LEVEL"] is not None:
                    h.setLevel(app.config["WEKO_LOGGING_CONSOLE_LEVEL"])

                h.setFormatter(formatter)
        else:
            # if app.logger has no handlers, add StreamHandler
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            app.logger.addHandler(handler)

        # Add user_id, ip_address to log record
        app.logger.addFilter(wekoLoggingFilter)

    @staticmethod
    def weko_logger_base(app=None, key=None, param=None, ex=None, **kwargs):
        """Log message with key.

        Method to output logs in current_app.logger using the resource.

        Args:
            app (Flask): \
                The Flask application.
                Not required.
            key (str): \
                key of message.
                Not required if param is specified.
            param (dict): \
                message parameters.
                Not required if key is specified.
            ex (Exception): \
                exception object.
                Not required.
            **kwargs (dict): \
                message parameters.
                If you want to replace the placeholder in the message,
                specify the key-value pair here.
        Returns:
            None
        """

        if app is None:
            from flask import current_app
            app = current_app

        # check if console logging is enabled
        if not app.config.get("WEKO_LOGGING_CONSOLE"):
            return

        # get message parameters from common resource
        if not param:
            param = WEKO_COMMON_MESSAGE.get(key, None)
        if not param:
            return

        msgid = param.get('msgid', None)
        msgstr = param.get('msgstr', None)
        loglevel = param.get('loglevel', None)

        msg = msgid + ' : ' + msgstr

        frame, extra = None, {}
        try:
            frame = sys._getframe(2)
            extra = {
                'wpathname': frame.f_code.co_filename,
                'wlineno': frame.f_lineno,
                'wfuncName': frame.f_code.co_name,
            }
        except Exception as ex:
            frame = inspect.stack()[2]
            extra = {
                'wpathname': frame.filename,
                'wlineno': frame.lineno,
                'wfuncName': frame.function,
            }

        # output log by msglvl
        if loglevel == 'ERROR':
            app.logger.error(msg.format(**kwargs), extra=extra)
        elif loglevel == 'WARN':
            app.logger.warning(msg.format(**kwargs), extra=extra)
        elif loglevel == 'INFO':
            app.logger.info(msg.format(**kwargs), extra=extra)
        elif loglevel == 'DEBUG':
            app.logger.debug(msg.format(**kwargs), extra=extra)
        else:
            pass

        if ex:
            app.logger.error(
                ex.__class__.__name__ + ": " + str(ex), extra=extra)
            traceback.print_exc()


