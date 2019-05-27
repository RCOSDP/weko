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

from ast import literal_eval as make_tuple
from datetime import datetime
from itertools import islice, zip_longest

from celery import shared_task, task
from celery.utils.log import get_task_logger
from flask import current_app
from flask_sitemap import sitemap_page_needed

from . import config
from .signals import sitemap_finished

logger = get_task_logger(__name__)


@shared_task
def link_success_handler(retval):
    """Register task stats into invenio-stats."""
    current_app.logger.info('[{0}] [{1} {2}] SUCCESS'.format(0, 'Sitemap update', retval[0]['task_id']))
    exec_data = retval[0]
    exec_data['total_records'] = exec_data['total']
    del exec_data['total']
    sitemap_finished.send(current_app._get_current_object(),
                          exec_data=exec_data, user_data=retval[1])


@shared_task
def link_error_handler(request, exc, traceback):
    """Register task stats into invenio-stats for failure."""
    args = make_tuple(request.argsrepr)  # Cannot access original args
    start_time = datetime.strptime(args[1], '%Y-%m-%dT%H:%M:%S')
    end_time = datetime.now()
    sitemap_finished.send(current_app._get_current_object(),
                          exec_data={
                            'task_state': 'FAILURE',
                            'start_time': start_time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                            'end_time': end_time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                            'total_records': 0,
                            'execution_time': str(end_time - start_time),
                            'task_name': 'sitemap',
                            'repository_name': 'weko',  # TODO: Grab from config
                            'task_id': request.id
                             },
                          user_data=args[2])


@shared_task(ignore_results=True)
def update_sitemap(baseurl, start_time, user_data):
    """Update sitemap cache."""
    with current_app.app_context():
        current_app.logger.info('[{0}] [{1}] START'.format(0, 'Sitemap update'))
        start_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S')
        current_app.config['SERVER_NAME'] = baseurl
        flask_sitemap = current_app.extensions['sitemap']
        size = current_app.config['SITEMAP_MAX_URL_COUNT']
        args = [iter(flask_sitemap._generate_all_urls())] * size
        run = zip_longest(*args)
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
            current_app.logger.info('[{0}] [{1} {2}] '.format(0, 'Created page #', 1))
            end_time = datetime.now()
            return ({'total': len(urlset),
                     'start_time': start_time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                     'end_time': end_time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                     'execution_time': str(end_time - start_time),
                     'task_name': 'sitemap',
                     'repository_name': 'weko',  # TODO: Grab from config
                     'task_id': update_sitemap.request.id,
                     'task_state': 'SUCCESS'},
                    user_data)

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
        current_app.logger.info('[{0}] [{1} {2}] '.format(0, 'Created page #', 1))
        for urlset_ in run:
            kwargs['page'] += 1
            current_app.logger.info('[{0}] [{1} {2}] '.format(0, 'Created page #', kwargs['page']))
            urlset_ = [url for url in urlset_ if url is not None]
            total += len(urlset_)
            sitemap_page_needed.send(current_app._get_current_object(),
                                     page=kwargs['page'], urlset=urlset_)

        current_app.logger.info('[{0}] [{1}] DONE'.format(0, 'Sitemap update'))
        end_time = datetime.now()
        return ({'total': len(urlset),
                 'start_time': start_time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                 'end_time': end_time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                 'execution_time': str(end_time - start_time),
                 'task_name': 'sitemap',
                 'repository_name': 'weko',  # TODO: Grab from config
                 'task_id': update_sitemap.request.id,
                 'task_state': 'SUCCESS'},
                user_data)
