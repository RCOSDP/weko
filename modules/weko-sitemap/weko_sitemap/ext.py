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

"""Module of weko-sitemap."""

from __future__ import absolute_import, print_function

import gzip
from datetime import datetime
from functools import wraps
from io import BytesIO
from itertools import islice, zip_longest
from urllib.parse import urlparse

from flask import Blueprint, Response, current_app, render_template, request, \
    url_for
from flask_sitemap import Sitemap, sitemap_page_needed
from invenio_cache import current_cache
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.models import RecordMetadata
from sqlalchemy import Float, cast

from . import config


class WekoSitemap(Sitemap):
    """Weko-sitemap extension."""

    @sitemap_page_needed.connect
    def create_page(app, page, urlset):
        """Create sitemap page and save to cache."""
        page_name = 'sitemap_' + str(page).zfill(4)  # Cache key
        page_dic = dict(page=current_app.extensions['sitemap'].render_page(urlset=urlset),
                        lastmod=datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z'))
        current_app.extensions['weko-sitemap'].set_cache_page(
            page_name, page_dic)

    def load_page(self, fn):
        """Load sitemap page."""
        @wraps(fn)
        def loader(*args, **kwargs):
            page = kwargs.get('page')
            data = current_cache.get('sitemap_' + str(page).zfill(4))
            # current_app.extensions['sitemap'].gzip_response(data['page'])
            return data['page'] if data else fn(*args, **kwargs)
        return loader

    def clear_cache_pages(self):
        """Clear all cached pages."""
        page_keys = current_cache.get(self.cached_pages_set_key) or set()
        for page in page_keys:
            current_cache.delete(page)
        current_cache.delete(self.cached_pages_set_key)

    def set_cache_page(self, key, value):
        """Set the page into the cache."""
        # Check if there is a set of keys, if not create one_or_none
        current_key_set = current_cache.get(self.cached_pages_set_key) or set()
        current_key_set.add(key)
        current_cache.set(self.cached_pages_set_key, current_key_set)
        current_cache.set(
            key, value,
            timeout=current_app.config['WEKO_SITEMAP_CACHE_TIMEOUT'])

    @staticmethod
    def get_cache_page(key):
        """Get page from cache."""
        current_cache.get(key)

    def sitemap(self):
        """Override - Render sitemap from cache sitemap.xml."""
        return render_template('flask_sitemap/sitemapindex.xml',
                               sitemaps=self._load_cache_pages())

    def page(self, page):
        """Override to get sitemap page from cache if it exists."""
        sitemap_page = current_cache.get('sitemap_' + str(page).zfill(4))
        if sitemap_page:
            return self.gzip_response(sitemap_page['page'])
            # return sitemap_page['page']
        return flask_sitemap.render_page(urlset=[None])

    def gzip_response(self, data):
        """Override - Gzip response data and create new Response instance."""
        gzip_buffer = BytesIO()
        gzip_file = gzip.GzipFile(mode='wb', fileobj=gzip_buffer)
        gzip_file.write(data.encode('utf-8'))
        gzip_file.close()
        response = Response()
        response.data = gzip_buffer.getvalue()
        response.headers['Content-Type'] = 'application/x-gzip'
        # response.headers['Content-Encoding'] = 'gzip' # Breaks Chrome if set
        response.headers['Content-Length'] = len(response.data)
        return response

    def _generate_all_item_urls(self):
        """Make url set for all items."""
        self.clear_cache_pages()  # Clear cache
        q = (db.session
               .query(PersistentIdentifier, RecordMetadata)
               .join(RecordMetadata, RecordMetadata.id == PersistentIdentifier.object_uuid)
               .filter(PersistentIdentifier.status == PIDStatus.REGISTERED, PersistentIdentifier.pid_type == 'recid')
               .order_by(cast(PersistentIdentifier.pid_value, Float).asc())
               .limit(current_app.config['WEKO_SITEMAP_TOTAL_MAX_URL_COUNT']))

        for recid, rm in q.yield_per(1000):
            yield {
                'loc': url_for('invenio_records_ui.recid',
                               pid_value=recid.pid_value,
                               _external=True),
                'lastmod': rm.updated.strftime('%Y-%m-%dT%H:%M:%S%z')
            }

    def _load_cache_pages(self):
        """Get pages from cache instead of re-creating them."""
        kwargs = dict(
            _external=True,
            _scheme=current_app.config.get('WEKO_SITEMAP_URL_SCHEME')
        )
        kwargs['page'] = 0
        page_keys = current_cache.get(self.cached_pages_set_key) or set()
        for page_number in page_keys:
            kwargs['page'] += 1
            page = current_cache.get(page_number)
            if page:
                yield {'loc': url_for('flask_sitemap.page', **kwargs),
                       'lastmod': page['lastmod']}

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        self.cached_pages_set_key = 'sitemap_page_keys'  # Keep track of cached pages
        app.extensions['weko-sitemap'] = self
        app.config['SITEMAP_VIEW_DECORATORS'] = [self.load_page]

        ext = Sitemap(app=app)
        ext.register_generator(self._generate_all_item_urls)

        ext.blueprint = Blueprint('flask_sitemap',
                                  'flask_sitemap', template_folder='templates')
        ext.blueprint.add_url_rule(  # Return cached sitemap or update it
            app.config.get('SITEMAP_ENDPOINT_URL'),
            'sitemap',
            ext._decorate(self.sitemap),
        )
        ext.blueprint.add_url_rule(
            app.config.get('SITEMAP_ENDPOINT_PAGE_URL'),
            'page',
            self.page  # Do not decorate
        )
        app.register_blueprint(
            ext.blueprint,
            url_prefix=app.config.get('SITEMAP_BLUEPRINT_URL_PREFIX')
        )

    def init_config(self, app):
        """Initialize configuration."""
        # Use theme's base template if theme is installed
        if 'BASE_TEMPLATE' in app.config:
            app.config.setdefault(
                'WEKO_SITEMAP_BASE_TEMPLATE',
                app.config['BASE_TEMPLATE'],
            )
        for k in dir(config):
            if k.startswith('WEKO_SITEMAP_') or k.startswith('SITEMAP_'):
                app.config.setdefault(k, getattr(config, k))
