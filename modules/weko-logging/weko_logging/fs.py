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
        if app.config['WEKO_LOGGING_FS_LOGFILE'] is None:
            return
        self.install_handler(app)
        app.extensions['weko-logging-fs'] = self

    def init_config(self, app):
        """
        Initialize configuration.

        :param app: The flask application.
        """
        app.config.setdefault(
            'WEKO_LOGGING_FS_LEVEL',
            'DEBUG' if app.debug else getattr(config, 'WEKO_LOGGING_FS_LEVEL')
        )
        for k in dir(config):
            if k.startswith('WEKO_LOGGING_FS'):
                app.config.setdefault(k, getattr(config, k))

        # Support injecting instance path and/or sys.prefix
        # first os.environ
        if app.config['WEKO_LOGGING_FS_LOGFILE'] is not None:
            if 'LOGGING_FS_LOGFILE' in os.environ:
                app.config['WEKO_LOGGING_FS_LOGFILE'] = os.environ.get(
                    'LOGGING_FS_LOGFILE', app.config['WEKO_LOGGING_FS_LOGFILE'].format(
                        instance_path=app.instance_path, sys_prefix=sys.prefix,))
            else:
                app.config['WEKO_LOGGING_FS_LOGFILE'] = \
                    app.config['WEKO_LOGGING_FS_LOGFILE'].format(
                        instance_path=app.instance_path,
                        sys_prefix=sys.prefix,
                )

    def install_handler(self, app):
        """
        Install log handler on Flask application.

        :param app: The flask application.
        """
        # Check if directory exists.
        basedir = dirname(app.config['WEKO_LOGGING_FS_LOGFILE'])
        if not exists(basedir):
            os.makedirs(basedir, exist_ok=True)
            # raise ValueError(
            #    'Log directory {0} does not exists.'.format(basedir))

        handler = TimedRotatingFileHandler(
            app.config['WEKO_LOGGING_FS_LOGFILE'],
            when=app.config['WEKO_LOGGING_FS_WHEN'],
            interval=app.config['WEKO_LOGGING_FS_INTERVAL'],
            backupCount=app.config['WEKO_LOGGING_FS_BACKUPCOUNT'],
            delay=True,
        )
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        handler.setLevel(app.config['WEKO_LOGGING_FS_LEVEL'])

        # Add handler to application logger
        app.logger.addHandler(handler)

        if app.config['WEKO_LOGGING_FS_PYWARNINGS']:
            self.capture_pywarnings(handler)
