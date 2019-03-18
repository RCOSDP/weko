import requests

from . import config


class CrossRefOpenURL:
    """
    The Class retrieves the metadata from CrossRef.
    """
    ENDPOINT = 'openurl'
    JSON_FORMAT = 'json'
    XML_FORMAT = 'xml'
    # Set default value
    _response_format = JSON_FORMAT
    _timeout = config.WEKO_ITEMS_AUTOFILL_REQUEST_TIMEOUT
    _proxy = {
        'http': config.WEKO_ITEMS_AUTOFILL_SYS_HTTP_PROXY,
        'https': config.WEKO_ITEMS_AUTOFILL_SYS_HTTPS_PROXY
    }

    def __init__(self, pid, doi, response_format=None, timeout=None,
                 http_proxy=None, https_proxy=None):
        if not pid:
            raise ValueError('PID is required.')
        if not doi:
            raise ValueError('DOI is required.')
        self._pid = pid
        self._doi = doi.strip()
        if response_format:
            self._response_format = response_format
        if timeout:
            self._timeout = timeout
        if http_proxy:
            self._proxy['http'] = http_proxy
        if https_proxy:
            self._proxy['https'] = https_proxy

    def _create_endpoint(self):
        """
        Create endpoint
        :return: endpoint string.
        """
        endpoint_url = self.ENDPOINT + '?pid=' + self._pid
        endpoint_url = endpoint_url + '&id=doi:' + self._doi
        if self._response_format is not None:
            endpoint_url = endpoint_url + '&format=' + self._response_format
        return endpoint_url

    def _create_url(self):
        """
        Create request URL
        :return:
        """
        endpoint = self._create_endpoint()
        url = config.WEKO_ITEMS_AUTOFILL_CROSSREF_API_URL + '/' + endpoint
        return url

    @property
    def url(self):
        return self._create_url()

    def _do_http_request(self):
        return requests.get(self.url, timeout=self._timeout,
                            proxies=self._proxy)

    def get_data(self):
        """
        This method retrieves the metadata from CrossRef.
        """
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
