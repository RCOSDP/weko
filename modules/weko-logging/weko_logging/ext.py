# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Extensions for weko-logging."""

import logging


class WekoLoggingBase(object):
    """WEKO-Logging extension for console."""

    def __init__(self, app=None):
        """Extension initialization.

        :param app: The flask application.
        """
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize app.

        :param app: The flask application.
        """

    @staticmethod
    def capture_pywarnings(handler):
        """
        Log python system warnings.

        :param handler: Log handler object.
        """
        logger = logging.getLogger('py.warnings')
        # Check for previously installed handlers.
        for h in logger.handlers:
            if isinstance(h, handler.__class__):
                return
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)
