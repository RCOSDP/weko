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

"""WEKO3 module docstring."""
import traceback
import requests
from flask import current_app
from flask_babelex import gettext as _

from . import config


class CrossRefOpenURL:
    """The Class retrieves the metadata from CrossRef."""

    ENDPOINT = 'openurl'
    JSON_FORMAT = 'json'
    XML_FORMAT = 'xml'
    # Set default value
    _response_format = XML_FORMAT
    _timeout = config.WEKO_ITEMS_AUTOFILL_REQUEST_TIMEOUT
    _proxy = {
        'http': config.WEKO_ITEMS_AUTOFILL_SYS_HTTP_PROXY,
        'https': config.WEKO_ITEMS_AUTOFILL_SYS_HTTPS_PROXY
    }

    def __init__(self, pid, doi, response_format=None, timeout=None,
                 http_proxy=None, https_proxy=None):
        """Init CrossrefOpenURL API.

        :param pid:
        :param doi:
        :param response_format:
        :param timeout:
        :param http_proxy:
        :param https_proxy:
        """
        if not pid:
            raise ValueError(_('PID is not set.'))
        if not doi:
            raise ValueError(_('DOI is not specified.'))
        self._pid = pid
        self._doi = "/".join(doi.strip().strip("/").split("/")[-2:])
        if response_format:
            self._response_format = response_format
        if timeout:
            self._timeout = timeout
        if http_proxy:
            self._proxy['http'] = http_proxy
        if https_proxy:
            self._proxy['https'] = https_proxy

    def _create_endpoint(self):
        """Create endpoint.

        :return: endpoint string.
        """
        endpoint_url = self.ENDPOINT + '?pid=' + self._pid
        endpoint_url = endpoint_url + '&id=doi:' + self._doi
        if self._response_format is not None:
            endpoint_url = endpoint_url + '&format=' + self._response_format
        return endpoint_url

    def _create_url(self):
        """Create request URL.

        :return:
        """
        endpoint = self._create_endpoint()
        url = config.WEKO_ITEMS_AUTOFILL_CROSSREF_API_URL + '/' + endpoint
        return url

    @property
    def url(self):
        """URL property.

        :return: Request URL
        """
        return self._create_url()

    def _do_http_request(self):
        return requests.get(self.url, timeout=self._timeout,
                            proxies=self._proxy)

    def get_data(self):
        """This method retrieves the metadata from CrossRef."""
        response = {
            'response': '',
            'error': ''
        }
        try:
            result = self._do_http_request()
            if result.status_code == 200:
                response['response'] = result.text
                current_app.logger.debug(f"CrossRef result: {response['response']}")
        except Exception as e:
            current_app.logger.error(e)
            current_app.logger.error(traceback.format_exc())
            response['error'] = str(e)
        return response


class CiNiiURL:
    """The Class retrieves the metadata from CiNii."""

    ENDPOINT = 'crid'
    POST_FIX = '.json'
    # Set default value
    _timeout = config.WEKO_ITEMS_AUTOFILL_REQUEST_TIMEOUT
    _proxy = {
        'http': config.WEKO_ITEMS_AUTOFILL_SYS_HTTP_PROXY,
        'https': config.WEKO_ITEMS_AUTOFILL_SYS_HTTPS_PROXY
    }

    def __init__(self, naid, timeout=None, http_proxy=None, https_proxy=None):
        """Init CiNiiURL API.

        :param naid:
        :param timeout:
        :param http_proxy:
        :param https_proxy:
        """
        if not naid:
            raise ValueError('NAID is required.')
        self._naid = naid
        self._naid = naid.strip()
        if timeout:
            self._timeout = timeout
        if http_proxy:
            self._proxy['http'] = http_proxy
        if https_proxy:
            self._proxy['https'] = https_proxy

    def _create_endpoint(self):
        """Create endpoint.

        :return: endpoint string.
        """
        endpoint_url = self.ENDPOINT + '/' + self._naid + self.POST_FIX
        return endpoint_url

    def _create_url(self):
        """Create request URL.

        :return:
        """
        endpoint = self._create_endpoint()
        url = config.WEKO_ITEMS_AUTOFILL_CiNii_API_URL + '/' + endpoint
        return url

    @property
    def url(self):
        """URL property.

        :return: Request URL
        """
        return self._create_url()

    def _do_http_request(self):
        return requests.get(self.url, timeout=self._timeout,
                            proxies=self._proxy)

    def get_data(self):
        """This method retrieves the metadata from CrossRef."""
        response = {
            'response': '',
            'error': ''
        }
        try:
            result = self._do_http_request()
            if result.status_code == 200:
                response['response'] = result.json()
        except Exception as e:
            response['error'] = str(e)
        return response
