# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Inbox-Sender is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-inbox-sender."""

from __future__ import absolute_import, print_function

from flask_babelex import gettext as _

from . import config


class WekoInboxSender(object):
    """WEKO-Inbox-Sender extension."""

    def __init__(self, app=None):
        """Extension initialization.

        :param app: The Flask application. (Default: ``None``)
        """
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions['weko-inbox-sender'] = self

    def init_config(self, app):
        """Initialize configuration."""
        # Use theme's base template if theme is installed
        if 'BASE_TEMPLATE' in app.config:
            app.config.setdefault(
                'WEKO_INBOX_SENDER_BASE_TEMPLATE',
                app.config['BASE_TEMPLATE'],
            )
        for k in dir(config):
            if k.startswith('WEKO_INBOX_SENDER_'):
                app.config.setdefault(k, getattr(config, k))

        app.config.setdefault('INBOX_URL',
                              getattr(config, 'INBOX_URL'))
        app.config.setdefault('NGINX_HOST',
                              getattr(config, 'NGINX_HOST'))
