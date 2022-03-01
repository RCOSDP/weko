from flask import Flask
from weko_inbox_sender.api import \
    get_payloaddata_publish, create_payload, send_notification_inbox
from weko_inbox_sender.config import INBOX_VERIFY_TLS_CERTIFICATE
from mock import patch, MagicMock


def mock_perma(recid):
    return 'http://test.com/records/'+str(recid)


def mock_recid_p(recid_p):
    return recid_p


def mock_root():
    return 'http://test.com/'


def mock_inbox(url=None):
    if url is None:
        return 'http://test.com/inbox'
    else:
        return url


@patch('weko_inbox_sender.api.get_record_permalink', mock_perma)
@patch('weko_inbox_sender.api.get_recid_p', mock_recid_p)
@patch('weko_inbox_sender.api.get_url_root', mock_root)
def test_get_payload_publish(app, test_records, user, test_pushdata):
    print(test_pushdata)
    with patch("weko_inbox_sender.api.current_user.get_id",
               return_value=user.id
               ):
        with app.test_client() as client:
            pid, record = test_records[0]
            assert get_payloaddata_publish(record) == test_pushdata


def test_create_payload(test_pushdata, test_payload):
    print(test_payload)
    data = test_pushdata
    result = test_payload
    uuid_test = test_payload['id']

    with patch('weko_inbox_sender.api.uuid.uuid4',
               return_value=uuid_test
               ):
        test = create_payload(data,
                              'ANNOUNCE_STANDALONE',
                              'coar-notify:EndorsementAction'
                              )
        print(test)
        assert test == result


@patch('weko_inbox_sender.api.inbox_url', mock_inbox)
def test_send_notification_inbox(test_payload):
    mock_sender = MagicMock()
    payload = test_payload
    inbox = test_payload['target']['inbox']
    with patch('weko_inbox_sender.api.ldnlib.Sender',
               return_value=mock_sender
               ):
        send_notification_inbox(payload)
        args, kwargs = mock_sender.send.call_args
        assert args[0] == inbox
        assert args[1] == payload
        assert kwargs == {'verify': INBOX_VERIFY_TLS_CERTIFICATE}
