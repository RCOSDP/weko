from . import config
import requests


class CiNiiURL:
    """
    The Class retrieves the metadata from CiNii.
    """
    ENDPOINT = 'naid'
    POST_FIX = '.json'
    # Set default value
    _timeout = config.WEKO_ITEMS_AUTOFILL_REQUEST_TIMEOUT
    _proxy = {
        'http': config.WEKO_ITEMS_AUTOFILL_SYS_HTTP_PROXY,
        'https': config.WEKO_ITEMS_AUTOFILL_SYS_HTTPS_PROXY
    }

    def __init__(self, naid, timeout=None, http_proxy=None, https_proxy=None):
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
        """
        Create endpoint
        :return: endpoint string.
        """
        endpoint_url = self.ENDPOINT + '/' + self._naid + self.POST_FIX
        return endpoint_url

    def _create_url(self):
        """
        Create request URL
        :return:
        """
        endpoint = self._create_endpoint()
        url = config.WEKO_ITEMS_AUTOFILL_CiNii_API_URL + '/' + endpoint
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
