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

"""Amazon Product Advertising API."""

from base64 import b64encode
import urllib
import urllib3
import hmac
import time
import xml.etree.ElementTree as ET
from flask import current_app

from hashlib import sha256

from .utils import cached_api_json


class AmazonApi:
    _id_type = ''
    _item_id = ''
    _query = {}

    def __init__(self, access_key_id=None, secret_access_key=None,
                 associate_tag=None, region=None, service=None, operation=None,
                 id_type=None, item_id=None, timeout=None):
        """

        :rtype: object
        """
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.associate_tag = associate_tag

        if service is None:
            self.service = current_app.config[
                'WEKO_ITEMS_AUTOFILL_DEFAULT_SERVICE']
        else:
            self.service = service

        if operation is None:
            self.operation = current_app.config[
                'WEKO_ITEMS_AUTOFILL_DEFAULT_OPERATION']
        else:
            self.operation = operation

        if region is None:
            self.region = current_app.config[
                'WEKO_ITEMS_AUTOFILL_DEFAULT_REGION']
        else:
            self.region = region

        self._id_type = id_type
        self._item_id = item_id
        self.timeout = timeout

    def _validate(self):
        """ Validate input data
        """
        if self.access_key_id is None:
            raise TypeError("AWSAccessKeyId is not defined.")
        if self.secret_access_key is None:
            raise TypeError("AWSSecretAccessKey is not defined.")
        if self.associate_tag is None:
            raise TypeError("AssociateTag is not defined.")

    def _build_query(self):
        query = {
            'Service': 'AWSECommerceService',
            'Operation': self.operation,
            'ResponseGroup': 'Large',
            'SearchIndex': 'All',
            'IdType': self._id_type,
            'ItemId': self._item_id,
            'AWSAccessKeyId': self.access_key_id,
            'AssociateTag': self.associate_tag,
            'Timestamp': time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        return query

    def _api_url(self, query):
        query_strings = urllib.parse.urlencode(query)

        service_domain = \
            current_app.config['WEKO_ITEMS_AUTOFILL_SERVICE_DOMAINS'][
                self.region]

        # Generate the string to be signed
        signature_data = 'GET\n' + service_domain \
                         + current_app.config[
                             'WEKO_ITEMS_AUTOFILL_SERVICE_URI'] + '?' \
                         + query_strings
        print("signature_data=%s" % signature_data)

        # Convert unicode to UTF8 bytes for hmac library
        self.secret_access_key = self.secret_access_key.encode('utf-8')
        signature_data = signature_data.encode('utf-8')

        # Calculate sha256 signature
        print("Signature encode=%s" % signature_data)
        signature_digest = hmac.new(self.secret_access_key, signature_data,
                                    sha256).digest()
        # Base64 encode and urlencode
        signature = urllib.parse.quote(b64encode(signature_digest))

        url = (current_app.config['WEKO_ITEMS_AUTOFILL_API_PROTOCOL']
               + service_domain
               + current_app.config[
                   'WEKO_ITEMS_AUTOFILL_SERVICE_URI'] + '?' + query_strings
               + '&Signature=%s' % signature)

        return url

    def _call_api(self, api_url):
        if current_app.config['WEKO_ITEMS_AUTOFILL_PROXY']:
            api_request = urllib3.ProxyManager(
                current_app.config['WEKO_ITEMS_AUTOFILL_PROXY'])
        else:
            api_request = urllib3.PoolManager()

        try:
            print("Amazon URL: %s" % api_url)
            return api_request.request('GET', api_url, timeout=urllib3.Timeout(
                connect=current_app.config[
                    'WEKO_ITEMS_AUTOFILL_DEFAULT_TIMEOUT']))
        except Exception as e:
            print('Fail to get data from API:', e)

    # @cached_api_json
    def search(self, id_type=None, item_id=None, **query):
        if id_type is not None:
            self._id_type = id_type
        if item_id is not None:
            self._item_id = item_id
        if query:
            self._query = query
        else:
            self._query = self._build_query()

        api_url = self._api_url(self._query)

        api_response = self._call_api(api_url)
        response = self._parse(api_response)
        return response

    def _parse(self, api_response):
        if api_response.data:
            response_data = api_response.data
            if type(api_response.data) is bytes:
                response_data = api_response.data.decode("utf-8")

            if api_response.status != 200:
                root = ET.fromstring(response_data)
                namespaces = root.tag.split('}')[0].strip('{')
                namespaces = '{' + namespaces + '}'
                for error in root.findall('{}Error'.format(namespaces)):
                    error_code = error.find('{}Code'.format(namespaces))
                    error_msg = error.find('{}Message'.format(namespaces))
                    response_data = error_code.text + ' - ' + error_msg.text
            else:
                # root = ET.fromstring(response_data)
                # namespaces = root.tag.split('}')[0].strip('{')
                # namespaces = '{' + namespaces + '}'
                # for item in root.findall('{}Item'.format(namespaces)):
                #     print(item)
                response_data = {}
            return response_data
