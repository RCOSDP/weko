# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# INVENIO-ResourceSyncClient is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module of invenio-resourcesyncclient."""

from __future__ import absolute_import, print_function
from . import config


from flask_babel import gettext as _

# https://stackoverflow.com/questions/48391750/disable-python-requests-ssl-validation-for-an-imported-module/48391751#48391751
import os
os.environ['CURL_CA_BUNDLE'] = ''


class INVENIOResourceSyncClient(object):
    """INVENIO-ResourceSyncClient extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        # TODO: This is an example of translation string with comment. Please
        # remove it.
        # NOTE: This is a note to a translator.
        _('A translation string')
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions['invenio-resourcesyncclient'] = self

    def init_config(self, app):
        """Initialize configuration."""
        # Use theme's base template if theme is installed
        if 'BASE_TEMPLATE' in app.config:
            app.config.setdefault(
                'INVENIO_RESOURCESYNCCLIENT_BASE_TEMPLATE',
                app.config['BASE_TEMPLATE'],
            )
        for k in dir(config):
            if k.startswith('INVENIO_RESOURCESYNCCLIENT_'):
                app.config.setdefault(k, getattr(config, k))
