from weko_signpostingclient.api import request_signposting,create_data_from_signposting


def test_request_signposting():
    uri = "https://test.com"

    result = request_signposting(uri)
    data = [{'url':'https://url1.com', 'rel': 'cite-as'},
            {'url':'https://meta_json', 'rel': 'describedby', 'type': 'application/json'}
            ]
    assert result == data


def test_create_data_from_signposting1():
    link = '<https://url.com> ; rel="cite-as", <https://meta_json>, rel: "describedby", type: "application/json"'
    
    data = [{'url':'https://url1.com', 'rel': 'cite-as'},
            {'url':'https://meta_json', 'rel': 'describedby', 'type': 'application/json'}
            ]
    
    result = create_data_from_signposting(link)
    
    assert data == result


def test_make_signposting_url():
    # 未実装につき後回し
    pass
