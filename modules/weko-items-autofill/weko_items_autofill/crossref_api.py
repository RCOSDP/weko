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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""CrossRef API."""

import requests
from time import sleep

from . import config


class HTTPRequest:

    def __init__(self, throttle=True):
        self.throttle = throttle
        # Expect to be able to perform 50 requests a second
        self.rate_limits = {
            'X-Rate-Limit-Limit': 50,
            'X-Rate-Limit-Interval': 1
        }

    def _update_rate_limits(self, headers):

        self.rate_limits['X-Rate-Limit-Limit'] = int(
            headers.get('X-Rate-Limit-Limit', 50))

        interval_value = int(headers.get('X-Rate-Limit-Interval', '1s')[:-1])
        interval_scope = headers.get('X-Rate-Limit-Interval', '1s')[-1]

        if interval_scope == 'm':
            interval_value = interval_value * 60

        if interval_scope == 'h':
            interval_value = interval_value * 60 * 60

        self.rate_limits['X-Rate-Limit-Interval'] = interval_value

    @property
    def throttling_time(self):
        return self.rate_limits['X-Rate-Limit-Interval'] / self.rate_limits[
            'X-Rate-Limit-Limit']

    def do_http_request(self, method, endpoint, data=None, files=None,
                        timeout=10, only_headers=False, custom_header=None,
                        authorization=None):
        if only_headers is True:
            return requests.head(endpoint)

        if method == 'post':
            action = requests.post
        else:
            action = requests.get

        headers = dict()
        # Put the Authorization API token to request header
        if authorization:
            headers['Authorization'] = authorization
        # Put contact info to request header
        if custom_header:
            headers['User-Agent'] = custom_header
        else:
            headers['User-Agent'] = str(ApiEtiquette())

        # Perform call API
        if method == 'post':
            result = action(endpoint, data=data, files=files, timeout=timeout,
                            headers=headers)
        else:
            result = action(endpoint, params=data, timeout=timeout,
                            headers=headers)

        if self.throttle is True:
            self._update_rate_limits(result.headers)
            sleep(self.throttling_time)

        return result


class ApiEtiquette:
    """Specify contact information in User-Agent header.
    This way API Provider can contact if they see a problem"""

    def __init__(self):
        self.application_name = 'undefined'
        self.application_version = 'undefined'
        self.application_url = 'undefined'
        self.contact_email = 'anonymous'

    def __str__(self):
        contact_info = '%s/%s (%s; mailto:%s)' % (
            self.application_name,
            self.application_version,
            self.application_url,
            self.contact_email
        )

        return contact_info


def build_url_endpoint(endpoint, context=None):
    endpoint = '/'.join([i for i in [context, endpoint] if i])
    api = config.WEKO_ITEMS_AUTOFILL_CROSSREF_API_URL
    return '%s/%s' % (api, endpoint)


class EndPoint:
    ENDPOINT = ''

    def __init__(self, request_url=None, request_params=None, context=None,
                 etiquette=None, authorization=None, throttle=True):
        self.do_http_request = HTTPRequest(throttle=throttle).do_http_request
        self.etiquette = etiquette or ApiEtiquette()
        self.authorization = authorization or config \
            .WEKO_ITEMS_AUTOFILL_CROSSREF_API_TOKEN
        self.request_url = request_url or build_url_endpoint(self.ENDPOINT,
                                                             context)
        self.request_params = request_params or dict()
        self.context = context or ''

    @property
    def _rate_limits(self):
        request_url = str(self.request_url)

        result = self.do_http_request(
            'get',
            request_url,
            only_headers=False,
            custom_header=str(self.etiquette),
            authorization=''
        )

        rate_limits = {
            'X-Rate-Limit-Limit': result.headers.get('X-Rate-Limit-Limit',
                                                     'undefined'),
            'X-Rate-Limit-Interval': result.headers.get('X-Rate-Limit-Interval',
                                                        'undefined')
        }

        return rate_limits

    def _escaped_paging(self):
        escape_paging = ['offset', 'rows']
        request_params = dict(self.request_params)

        for item in escape_paging:
            try:
                del (request_params[item])
            except KeyError:
                pass

        return request_params

    @property
    def x_rate_limit_limit(self):

        return self._rate_limits.get('X-Rate-Limit-Limit', 'undefined')

    @property
    def x_rate_limit_interval(self):

        return self._rate_limits.get('X-Rate-Limit-Interval', 'undefined')


class Works(EndPoint):
    """A class to search metadata for the specified Crossref DOI."""
    STATUS_OK = 'ok'
    ENDPOINT = 'works'

    def doi(self, doi, only_message=False):
        """
        This method retrieve the DOI metadata related to a given DOI
        number.

        args: Crossref DOI id (String)

        return: JSON
        """
        request_url = build_url_endpoint(
            '/'.join([self.ENDPOINT, doi])
        )
        request_params = {}

        result = self.do_http_request(
            'get',
            request_url,
            data=request_params,
            custom_header=str(self.etiquette)
        )

        if result.status_code == 404:
            return

        result = result.json()

        return result['message'] if only_message is True else result
