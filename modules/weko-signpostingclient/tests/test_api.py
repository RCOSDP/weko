
from mock import patch
from weko_signpostingclient.api import\
    request_signposting, create_data_from_signposting,\
    make_signposting_url


def mock_request(url):
    class MockRequest:
        def __init__(self, url):
            self.url = url
            self.headers = {'Link': 'linked header'}

        def raise_for_status(self):
            if self.url == 'url_invalid':
                raise requests.exceptions.RequestException
    return MockRequest(url=url)


@patch('weko_signpostingclient.api.make_signposting_url',
       return_value="xxx"
       )
@patch('weko_signpostingclient.api.requests.head', side_effect=mock_request)
def test_request_signposting(mock_head, mock_url, test_maked_data):
    uri = "https://test.com"
    result = test_maked_data
    with patch('weko_signpostingclient.api.create_data_from_signposting',
               return_value=test_maked_data
               ):
        test = request_signposting(uri)
        assert test == result


def test_make_signposting_url(app):
    # 未実装につき後回し
    uri = 'https://localhost/records/1'
    result = 'https://nginx/records/1/signposting'
    test = make_signposting_url(uri)
    assert test == result


def test_make_signposting_url(app):
    uri = 'https://test.com/records/2'
    result = 'https://test.com/records/2/signposting'
    test = make_signposting_url(uri)
    assert test == result


def test_create_data_from_signposting1(test_link_str, test_maked_data):
    link = test_link_str

    data = test_maked_data

    result = create_data_from_signposting(link)

    assert data == result
