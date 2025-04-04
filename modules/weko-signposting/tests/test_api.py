from mock import patch
from flask import url_for

from weko_signposting.api import requested_signposting, outside_url


@patch('weko_signposting.api.outside_url',
       side_effect=['https://test.com/', 'https://test.com/records/1']
       )
@patch('weko_signposting.api.get_record_permalink',
       return_value='https://test.com/records/1'
       )
def test_requested_signposting(mock_permalink, mock_outside_url,
                               app, test_link_str, test_records
                               ):
    pid, record = test_records[0]
    with app.test_client() as client:
        url = '/records/1'
        res = client.head(url)
        result = test_link_str['link']
        test = res.headers['Link']
        assert result == test


def test_outside_url1(app):
    url = 'https://nginx/signposting'
    result = 'https://test.com/signposting'
    test = outside_url(url)
    assert test == result


def test_outside_url2(app):
    url = 'https://not_host.com/signposting'
    result = 'https://not_host.com/signposting'
    test = outside_url(url)
    assert test == result
