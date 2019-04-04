# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# weko-sitemap is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-sitemap."""

from __future__ import absolute_import, print_function

from flask_babelex import gettext as _

from . import config

from flask_sitemap import Sitemap


class WekoSitemap(object):
    """weko-sitemap extension."""

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
        app.extensions['weko-sitemap'] = self

        app.config['SITEMAP_INCLUDE_RULES_WITHOUT_PARAMS'] = True
        app.config['SITEMAP_BLUEPRINT_URL_PREFIX'] = '/weko-sitemap/'
        ext = Sitemap(app=app)

    def init_config(self, app):
        """Initialize configuration."""
        # Use theme's base template if theme is installed
        if 'BASE_TEMPLATE' in app.config:
            app.config.setdefault(
                'WEKO_SITEMAP_BASE_TEMPLATE',
                app.config['BASE_TEMPLATE'],
            )
        for k in dir(config):
            if k.startswith('WEKO_SITEMAP_'):
                app.config.setdefault(k, getattr(config, k))
