from mock import patch
from unittest.mock import MagicMock
import pytest
import io
from flask import Flask, json, jsonify, session, url_for, current_app
from flask_security.utils import login_user
from invenio_accounts.testutils import login_user_via_session
from pytest_mock import mocker

from weko_records_ui.api import send_request_mail, create_captcha_image
from weko_records_ui.errors import ContentsNotFoundError, InternalServerError, InvalidCaptchaError, InvalidEmailError
from weko_redis.redis import RedisConnection

# def send_request_mail(item_id, mail_info):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_api.py::test_send_request_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_send_request_mail(app, make_request_maillist):

    mail_info = {'from': 'test1@example.com',
                 'subject': 'test_subject',
                 'message': 'test_message',
                 'key': '',
                 'calculation_result': 1}
    item_id = make_request_maillist[0]

    with pytest.raises(ContentsNotFoundError):
        send_request_mail(item_id,mail_info)

    mail_info = {'from': 'test1@example.com',
                 'subject': 'test_subject',
                 'message': 'test_message',
                 'key': 'test_key',
                 'calculation_result': '1'}
    item_id = make_request_maillist[0]

    redis_connection = RedisConnection()
    datastore = redis_connection.connection(db=app.config['CACHE_REDIS_DB'])
    datastore.hmset(b'test_key',{b'calculation_result':b'10'})

    with pytest.raises(InvalidCaptchaError):
        send_request_mail(item_id,mail_info)

    mail_info = {'from': 'test1@example.com',
                'subject': 'test_subject',
                'message': 'test_message',
                'key': 'test_key',
                'calculation_result': 1}
    item_id = make_request_maillist[1]

    redis_connection = RedisConnection()
    datastore = redis_connection.connection(db=app.config['CACHE_REDIS_DB'])
    datastore.hmset(b'test_key',{b'calculation_result':b'1'})

    with pytest.raises(ContentsNotFoundError):
        send_request_mail(item_id,mail_info)

    mail_info = {'from': 'あああああ',
                'subject': 'test_subject',
                'message': 'test_message',
                'key': 'test_key',
                'calculation_result': 1}
    item_id = make_request_maillist[0]

    with pytest.raises(InvalidEmailError):
        send_request_mail(item_id,mail_info)

    #mocker.patch('flask_mail._Mail.send')
    mail_info = {'from': 'test1@example.com',
                 'subject': 'test_subject',
                 'message': 'test_message',
                 'key': 'test_key',
                 'calculation_result': 1}
    item_id = make_request_maillist[0]
    msg_sender = mail_info['from']
    msg_subject = mail_info['subject']
    msg_body = msg_sender + current_app.config.get("WEKO_RECORDS_UI_REQUEST_MESSAGE") + mail_info['message']
    res_test ={
        "from": msg_sender,
        "subject": msg_subject,
        "message": msg_body
    }
    with app.test_request_context():
        with patch ("flask_mail._Mail.send"):
            res = send_request_mail(item_id,mail_info)
            assert res == res_test

# def create_captcha_image(item_id, mail_info):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_api.py::test_create_captcha_image -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_create_captcha_image(app):
    with app.test_request_context():
        ret = create_captcha_image()
        assert ret[0] == True
