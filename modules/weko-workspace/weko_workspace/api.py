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

"""WEKO3 module docstring."""

import requests
import urllib.parse
from . import config



class JamasURL:
    """The Class retrieves the metadata from Jamas."""

    ENDPOINT = 'api/sru?operation=searchRetrieve&version=1.2&startRecord=1'
    POST_FIX = '&recordPacking=xml&recordSchema=pam&query='
    # Set default value
    _timeout = config.WEKO_WORKSPACE_REQUEST_TIMEOUT
    _proxy = {
        'http': config.WEKO_WORKSPACE_SYS_HTTP_PROXY,
        'https': config.WEKO_WORKSPACE_SYS_HTTPS_PROXY
    }
    def __init__(self, doi, timeout=None, http_proxy=None, https_proxy=None):
        """Init JamasURL API.

        :param doi:
        :param timeout:
        :param http_proxy:
        :param https_proxy:
        """
        if not doi:
            raise ValueError('DOI is required.')
        self._doi = doi
        self._doi = doi.strip()
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
        endpoint_encode = 'prism.doi==' + self._doi
        encoded_string = urllib.parse.quote(endpoint_encode, encoding='utf-8', safe='')
        endpoint_url = self.ENDPOINT + self.POST_FIX + encoded_string
        return endpoint_url


    def _create_url(self):
        """Create request URL.

        :return:
        """
        endpoint = self._create_endpoint()

        url =  config.WEKO_WORKSPACE_JAMAS_API_URL + endpoint
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
        """This method retrieves the metadata from Jamas."""
        response = {
            'response': '',
            'error': ''
        }
        try:
            result = self._do_http_request()
            if result.status_code == 200:
                response['response'] = result.text
        except Exception as e:
            response['error'] = str(e)
        return response


class CiNiiURL:
    """The Class retrieves the metadata from CiNii."""

    ENDPOINT = 'doi='
    POST_FIX = '&format=json'
    # Set default value
    _timeout = config.WEKO_WORKSPACE_REQUEST_TIMEOUT
    _proxy = {
        'http': config.WEKO_WORKSPACE_SYS_HTTP_PROXY,
        'https': config.WEKO_WORKSPACE_SYS_HTTPS_PROXY
    }
    def __init__(self, doi, timeout=None, http_proxy=None, https_proxy=None):
        """Init CiNiiURL API.

        :param doi:
        :param timeout:
        :param http_proxy:
        :param https_proxy:
        """
        if not doi:
            raise ValueError('DOI is required.')
        self._doi = doi
        self._doi = doi.strip()
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
        endpoint_url = self.ENDPOINT + self._doi + self.POST_FIX
        return endpoint_url


    def _create_url(self):
        """Create request URL.

        :return:
        """
        endpoint = self._create_endpoint()

        url =  config.WEKO_WORKSPACE_CiNii_API_URL + '?' + endpoint
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
        """This method retrieves the metadata from CiNii."""
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


class JALCURL:
    """The Class retrieves the metadata from JALC."""

    _timeout = config.WEKO_WORKSPACE_REQUEST_TIMEOUT
    _proxy = {
        'http': config.WEKO_WORKSPACE_SYS_HTTP_PROXY,
        'https': config.WEKO_WORKSPACE_SYS_HTTPS_PROXY
    }
    def __init__(self, doi, timeout=None, http_proxy=None, https_proxy=None):
        """Init JALCURL API.

        :param doi:
        :param timeout:
        :param http_proxy:
        :param https_proxy:
        """
        if not doi:
            raise ValueError('DOI is required.')
        self._doi = doi
        self._doi = doi.strip()
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
        endpoint_url = self._doi
        return endpoint_url


    def _create_url(self):
        """Create request URL.

        :return:
        """
        endpoint = self._create_endpoint()
        url =  config.WEKO_WORKSPACE_JALC_API_URL + endpoint
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
        """This method retrieves the metadata from Jalc."""
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

class DATACITEURL:
    """The Class retrieves the metadata from Datacite."""

    _timeout = config.WEKO_WORKSPACE_REQUEST_TIMEOUT
    _proxy = {
        'http': config.WEKO_WORKSPACE_SYS_HTTP_PROXY,
        'https': config.WEKO_WORKSPACE_SYS_HTTPS_PROXY
    }
    def __init__(self, doi, timeout=None, http_proxy=None, https_proxy=None):
        """Init DataciteURL API.

        :param doi:
        :param timeout:
        :param http_proxy:
        :param https_proxy:
        """
        if not doi:
            raise ValueError('DOI is required.')
        self._doi = doi
        self._doi = doi.strip()
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
        endpoint_url = self._doi
        return endpoint_url


    def _create_url(self):
        """Create request URL.

        :return:
        """
        endpoint = self._create_endpoint()

        url =  config.WEKO_WORKSPACE_DATACITE_API_URL + endpoint
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
        """This method retrieves the metadata from Datacite."""
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
