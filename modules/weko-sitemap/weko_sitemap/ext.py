# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# weko-sitemap is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-sitemap."""

from __future__ import absolute_import, print_function

from functools import wraps
from urllib.parse import urlparse

from flask import current_app, request, url_for
from flask_babelex import gettext as _
from flask_sitemap import Sitemap, sitemap_page_needed

from . import config


class WekoSitemap(object):
    """weko-sitemap extension."""

    # TODO: make this into a route, send request here from run button
    @sitemap_page_needed.connect
    def create_page(app, page, urlset):
        """Create sitemap page."""
        urlset = [{'loc': urlparse(request._base_url).hostname + url_for(url[0])}
                  for url in current_app._extensions['sitemap']._routes_without_params()]
        cache[page] = current_app.extensions['sitemap'].render_page(
            urlset=urlset)

    def load_page(self, fn):
        """Load sitemap page."""
        @wraps(fn)
        def loader(*args, **kwargs):
            page = kwargs.get('page')
            # TODO: use the cache here once the route above is set up
            # data = cache.get(page)
            # return data if data else fn(*args, **kwargs)
            urlset = [{'loc': urlparse(request.base_url).hostname + url_for(url[0])}
                      for url in current_app.extensions['sitemap']._routes_without_params()]
            return current_app.extensions['sitemap'].render_page(urlset=urlset)
        return loader

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions['weko-sitemap'] = self

        app.config['SITEMAP_INCLUDE_RULES_WITHOUT_PARAMS'] = True
        app.config['SITEMAP_BLUEPRINT_URL_PREFIX'] = '/weko/sitemaps'
        app.config['SITEMAP_ENDPOINT_URL'] = '/'
        app.config['SITEMAP_VIEW_DECORATORS'] = [self.load_page]
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
