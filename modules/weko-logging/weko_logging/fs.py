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


class ColorFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[36m',    # シアン
        'INFO': '\033[34m',     # 青
        'WARNING': '\033[33m',  # 黄
        'ERROR': '\033[31;1m',    # 赤
        'BLACK': '\033[30;2m',    # 黒
    }
    RESET = '\033[0m'

    def format(self, record):
        if record.pathname.startswith("/code/"):
            record.pathname = record.pathname[6:]
        levelname = record.levelname
        color = self.COLORS.get(levelname, self.RESET)
        record.levelname = f"{color}{levelname}{self.RESET}"
        return super().format(record)


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

        self.init_logger(app)

    def init_logger(self, app):
        format = '[%(asctime)s,%(msecs)03d][%(levelname)s] \033[32mweko\033[0m - '\
                '%(message)s [file %(pathname)s:%(lineno)d in %(funcName)s]'
        datefmt = '%Y-%m-%d %H:%M:%S'
        formatter = ColorFormatter(fmt=format, datefmt=datefmt)

        app.logger.setLevel("INFO")
        if app.logger.handlers:
            # if app.logger has handlers, set level and formatter
            for h in app.logger.handlers:
                h.setLevel("INFO")
                h.setFormatter(formatter)

        # blueメソッドを追加
        import inspect
        def blue(self, msg, *args, **kwargs):
            BLUE = ColorFormatter.COLORS['DEBUG']
            RESET = ColorFormatter.RESET
            frame = inspect.currentframe()
            try:
                outer = inspect.getouterframes(frame)
                if len(outer) > 1:
                    caller_frame = outer[1]
                    filename = caller_frame.filename
                    lineno = caller_frame.lineno
                    funcname = caller_frame.function
                    if filename.startswith("/code/"):
                        filename = filename[6:]
                    msg = f"{msg} [file {filename}:{lineno} in {funcname}]\n"
            except IndexError:
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            self.info(f"{BLUE}{msg}{RESET}", *args, **kwargs)

        from types import MethodType
        app.logger.blue = MethodType(blue, app.logger)

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
