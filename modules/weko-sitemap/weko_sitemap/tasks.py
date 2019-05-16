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

"""Task for updating sitemap cache."""

from celery import shared_task, task
from celery.utils.log import get_task_logger
from datetime import datetime
from flask import current_app
from flask_sitemap import sitemap_page_needed
from itertools import islice, zip_longest

from . import config

logger = get_task_logger(__name__)


@shared_task(ignore_results=True)
def update_sitemap(baseurl):
    """Update sitemap cache."""
    current_app.logger.info('START - updating sitemap cache...')
    with current_app.app_context():
        current_app.config['SERVER_NAME'] = baseurl
        flask_sitemap = current_app.extensions['sitemap']
        size = current_app.config['SITEMAP_MAX_URL_COUNT']
        args = [iter(flask_sitemap._generate_all_urls())] * size
        run = zip_longest(*args)
        start_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z')
        try:
            urlset = next(run)
        except StopIteration:
            # Special case with empty list of urls.
            urlset = [None]

        # Number of URLs is less than the maximum
        if urlset[-1] is None:
            urlset = [url for url in urlset if url is not None]
            sitemap_page_needed.send(current_app._get_current_object(),
                                     page=1, urlset=urlset)
            # sitemap_page_needed.send(current_app._get_current_object(), \
            #    page=1, urlset=[urlset[0]])
            return {'total': len(urlset),
                    'start_time': start_time,
                    'end_time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z')}

        # Number of URLs is more than maximum, have to page them
        kwargs = dict(
            _external=True,
            _scheme=current_app.config.get('SITEMAP_URL_SCHEME')
        )
        kwargs['page'] = 1
        urlset = [url for url in urlset if url is not None]
        total = len(urlset)  # Keep track of number processed

        sitemap_page_needed.send(current_app._get_current_object(),
                                 page=1, urlset=urlset)
        for urlset_ in run:
            kwargs['page'] += 1
            urlset_ = [url for url in urlset_ if url is not None]
            total += len(urlset_)
            sitemap_page_needed.send(current_app._get_current_object(),
                                     page=kwargs['page'], urlset=urlset_)

        current_app.logger.info('DONE - sitemap cache updated.')
        return {'total': total,
                'start_time': start_time,
                'end_time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z')}
