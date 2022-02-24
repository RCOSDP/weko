from flask import Flask
from weko_inbox_sender.api import get_payloaddata_publish
from mock import patch


def mock_func2(recid):
    print("test mock2")
    return recid


def mock_func(recid_p):
    print("test mock")
    return recid_p


def mock_func3():
    print("test mock3")
    return "2"


def mock_func4():
    print("test mock4")
    return "4"


@patch('weko_inbox_sender.utils.get_record_permalink', mock_func)
@patch('weko_inbox_sender.utils.get_recid_p', mock_func2)
@patch('weko_inbox_sender.utils.get_url_root', mock_func3)
@patch('weko_inbox_sender.utils.inbox_url', mock_func4)
def test_get_payload_publish(app, test_records, user):
    with app.test_client() as client:
        pid, record = test_records[0]
        assert get_payloaddata_publish(record) == {"test": 1}
