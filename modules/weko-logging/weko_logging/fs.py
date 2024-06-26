# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Weko logging filesystem handler.

This extension is automatically installed via ``invenio_base.apps`` and
``invenio_base.api_apps`` entry points.
"""

import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from os.path import dirname, exists

from . import config
from .ext import WekoLoggingBase


class WekoLoggingFS(WekoLoggingBase):
    """WEKO-Logging extension. Filesystem handler."""

    def init_app(self, app):
        """
        Flask application initialization.

        :param app: The flask application.
        """
        self.init_config(app)
        if app.config["WEKO_LOGGING_FS_LOGFILE"] is None:
            return
        self.install_handler(app)
        app.extensions["weko-logging-fs"] = self

    def init_config(self, app):
        """
        Initialize configuration.

        :param app: The flask application.
        """

        app.config.setdefault(
            "WEKO_LOGGING_FS_LEVEL",
            "DEBUG" if app.debug else getattr(config, "WEKO_LOGGING_FS_LEVEL"),
        )
        for k in dir(config):
            if k.startswith("WEKO_LOGGING_FS"):
                app.config.setdefault(k, getattr(config, k))

        # Support injecting instance path and/or sys.prefix
        # first os.environ
        if app.config["WEKO_LOGGING_FS_LOGFILE"] is not None:
            if "LOGGING_FS_LOGFILE" in os.environ:
                app.config["WEKO_LOGGING_FS_LOGFILE"] = os.environ.get(
                    "LOGGING_FS_LOGFILE",
                    app.config["WEKO_LOGGING_FS_LOGFILE"].format(
                        instance_path=app.instance_path,
                        sys_prefix=sys.prefix,
                    ),
                )
            else:
                app.config["WEKO_LOGGING_FS_LOGFILE"] = app.config[
                    "WEKO_LOGGING_FS_LOGFILE"
                ].format(
                    instance_path=app.instance_path,
                    sys_prefix=sys.prefix,
                )

    def install_handler(self, app):
        """
        Install log handler on Flask application.

        :param app: The flask application.
        """
        basedir = dirname(app.config["WEKO_LOGGING_FS_LOGFILE"])
        if not exists(basedir):
            raise ValueError("Log directory {0} does not exist.".format(basedir))

        # # Check if directory exists.
        # filepath = app.config['WEKO_LOGGING_FS_LOGFILE']
        # basedir = dirname(filepath)
        # if not exists(basedir):
        #     os.makedirs(basedir, exist_ok=True)

        # if not exists(filepath):
        #     _file = pathlib.Path(filepath)
        #     _file.touch(mode=0o777, exist_ok=True)

        # Avoid duplicated logger
        # if TimedRotatingFileHandler not in [x.__class__ for x in app.logger.handlers]:
        handler = TimedRotatingFileHandler(
            app.config["WEKO_LOGGING_FS_LOGFILE"],
            when=app.config["WEKO_LOGGING_FS_WHEN"],
            interval=app.config["WEKO_LOGGING_FS_INTERVAL"],
            backupCount=app.config["WEKO_LOGGING_FS_BACKUPCOUNT"],
            delay=True,
        )

        handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] - %(levelname)s - %(filename)s - %(name)s - %(funcName)s - %(message)s "
                "[in %(pathname)s:%(lineno)d]"
            )
        )
        handler.setLevel(app.config["WEKO_LOGGING_FS_LEVEL"])
        # Add handler to application logger
        app.logger.addHandler(handler)
        # default_handler.setLevel(app.config['WEKO_LOGGING_FS_LEVEL'])
        # formatter2 = logging.Formatter(
        #         '[%(asctime)s] - %(levelname)s - %(filename)s - %(name)s - %(funcName)s - %(message)s '
        #         '[in %(pathname)s:%(lineno)d]')
        #     default_handler.setFormatter(formatter2)
        #     app.logger.addHandler(default_handler)
        if app.config["WEKO_LOGGING_FS_PYWARNINGS"]:
            self.capture_pywarnings(handler)
