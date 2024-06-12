from smtplib import SMTPException
from mock import patch
import pytest
from flask import current_app
import uuid
from pytest_mock import mocker
from sqlalchemy.exc import SQLAlchemyError

from weko_records.models import ItemApplication
from weko_records_ui.api import send_request_mail, create_captcha_image, get_item_provide_list, validate_captcha_answer
from weko_records_ui.api import send_request_mail, create_captcha_image
from weko_records_ui.errors import AuthenticationRequiredError, ContentsNotFoundError, InternalServerError, InvalidCaptchaError, InvalidEmailError, RequiredItemNotExistError
from weko_redis.redis import RedisConnection

# def send_request_mail(item_id, mail_info):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_api.py::test_send_request_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_send_request_mail(app, make_request_maillist):

    redis_connection = RedisConnection()
    datastore = redis_connection.connection(db=app.config['CACHE_REDIS_DB'])
    datastore.hmset(b'test_key',{b'authorization_token':b'token'})

    correct_mail_info = {
        'from': 'test1@example.com',
        'subject': 'test_subject',
        'message': 'test_message',
        'key': 'test_key',
        'authorization_token': 'token'
    }

    # TestCase: missing 'key' in request body
    item_id = make_request_maillist[0]
    with pytest.raises(RequiredItemNotExistError):
        send_request_mail(item_id, {
            'from': 'test1@example.com',
            'subject': 'test_subject',
            'message': 'test_message',
            'authorization_token': 'token'})

    # TestCase: 'key' is empty
    item_id = make_request_maillist[0]
    with pytest.raises(RequiredItemNotExistError):
        send_request_mail(item_id, {
            'from': 'test1@example.com',
            'subject': 'test_subject',
            'message': 'test_message',
            'key': '',
            'authorization_token': 'token'})

    # TestCase: missing 'authorization_token' in reuqest body
    item_id = make_request_maillist[0]
    with pytest.raises(RequiredItemNotExistError):
        send_request_mail(item_id, {
            'from': 'test1@example.com',
            'subject': 'test_subject',
            'message': 'test_message',
            'key': 'test_key'})

    # TestCase: empty 'authorization_token'
    item_id = make_request_maillist[0]
    with pytest.raises(RequiredItemNotExistError):
        send_request_mail(item_id, {
            'from': 'test1@example.com',
            'subject': 'test_subject',
            'message': 'test_message',
            'key': 'test_key',
            'authorization_token': ''})

    # TestCase: 'authorization_token' is wrong
    item_id = make_request_maillist[0]
    with pytest.raises(AuthenticationRequiredError):
        send_request_mail(item_id, {
            'from': 'test1@example.com',
            'subject': 'test_subject',
            'message': 'test_message',
            'key': 'test_key',
            'authorization_token': 'token1'})

    # TestCase: Empty mail list
    item_id = make_request_maillist[1]
    with pytest.raises(ContentsNotFoundError):
        send_request_mail(item_id, correct_mail_info)

    # TestCase: missing 'from' in request body
    item_id = make_request_maillist[0]
    with pytest.raises(RequiredItemNotExistError):
        send_request_mail(item_id, {
            'subject': 'test_subject',
            'message': 'test_message',
            'key': 'test_key',
            'authorization_token': 'token'})
        
    # TestCase: 'from' is empty
    item_id = make_request_maillist[0]
    with pytest.raises(RequiredItemNotExistError):
        send_request_mail(item_id, {
            'from': '',
            'subject': 'test_subject',
            'message': 'test_message',
            'key': 'test_key',
            'authorization_token': 'token'})

    # TestCase: Invalid 'from' format
    item_id = make_request_maillist[0]

    with pytest.raises(InvalidEmailError):
        send_request_mail(item_id, {
            'from': 'あああああ',
            'subject': 'test_subject',
            'message': 'test_message',
            'key': 'test_key',
            'authorization_token': 'token'})

    # TestCase: missing 'subject' in request body
    item_id = make_request_maillist[0]
    with pytest.raises(RequiredItemNotExistError):
        send_request_mail(item_id, {
            'from': 'test1@example.com',
            'message': 'test_message',
            'key': 'test_key',
            'authorization_token': 'token'})

    # TestCase: 'subject' is empty
    item_id = make_request_maillist[0]
    with pytest.raises(RequiredItemNotExistError):
        send_request_mail(item_id, {
            'from': 'test1@example.com',
            'subject': '',
            'message': 'test_message',
            'key': 'test_key',
            'authorization_token': 'token'})

    # TestCase: missing 'message' in reuqest body
    item_id = make_request_maillist[0]
    with pytest.raises(RequiredItemNotExistError):
        send_request_mail(item_id, {
            'from': 'test1@example.com',
            'subject': 'test_subject',
            'key': 'test_key',
            'authorization_token': 'token'})

    # TestCase: empty 'message'
    item_id = make_request_maillist[0]
    with pytest.raises(RequiredItemNotExistError):
        send_request_mail(item_id, {
            'from': 'test1@example.com',
            'subject': 'test_subject',
            'message': '',
            'key': 'test_key',
            'authorization_token': 'token'})

    # TestCase: Request Mail Successful
    #mocker.patch('flask_mail._Mail.send')
    item_id = make_request_maillist[0]
    msg_body = correct_mail_info['from'] + current_app.config.get("WEKO_RECORDS_UI_REQUEST_MESSAGE") + correct_mail_info['message']
    res_test ={
        "from": correct_mail_info['from'],
        "subject": correct_mail_info['subject'],
        "message": msg_body
    }
    with app.test_request_context():
        with patch ("flask_mail._Mail.send"):
           status, response = send_request_mail(item_id, correct_mail_info)
        assert status == True
        assert response == res_test

    # TestCase: exception occured
    item_id = make_request_maillist[0]
    with app.test_request_context():
        with patch("flask_mail._Mail.send", side_effect=SMTPException):
            with pytest.raises(InternalServerError):
                send_request_mail(item_id, correct_mail_info)


# def validate_captcha_answer(captcha_answer):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_api.py::test_validate_captcha_answer -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_validate_captcha_answer(app):

    redis_connection = RedisConnection()
    datastore = redis_connection.connection(db=app.config['CACHE_REDIS_DB'])

    datastore.hmset(b'test_key',{b'calculation_result':b'100'})

    # TestCase: missing 'key' in request body
    with pytest.raises(RequiredItemNotExistError):
        validate_captcha_answer({
            'calculation_result': 100
        })

    # TestCase: empty 'key' in request body
    with pytest.raises(RequiredItemNotExistError):
        validate_captcha_answer({
            'key': '',
            'calculation_result': 100
        })

    # TestCase: missing 'calculation_result' in request body
    with pytest.raises(RequiredItemNotExistError):
        validate_captcha_answer({
            'key': 'test_key'
        })

    # TestCase: wrong 'calculation_result'
    datastore.hmset(b'test_key',{b'calculation_result':b'100'})
    with pytest.raises(InvalidCaptchaError):
        validate_captcha_answer({
            'key': 'test_key',
            'calculation_result': 99
        })
    # check redis is empty
    captcha_info = datastore.hgetall('test_key')
    assert captcha_info == {}

    # TestCase: correct calculation result
    datastore.hmset(b'test_key',{b'calculation_result':b'100'})
    status, response = validate_captcha_answer({
        'key': 'test_key',
        'calculation_result': 100
    })
    assert status == True
    assert 'authorization_token' in response.keys()
# def create_captcha_image(item_id, mail_info):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_api.py::test_create_captcha_image -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_create_captcha_image(app):
    with app.test_request_context():
        status, response = create_captcha_image()
        assert status == True
        assert 'key' in response.keys()
        assert 'image' in response.keys()
        assert response.get('ttl') == 600
# def get_item_provide_list(item_id):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_api.py::test_get_item_provide_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_item_provide_list(mocker, db):
    assert get_item_provide_list(None)=={}
    item_id_1 = uuid.uuid4()
    item_id_2 = uuid.uuid4()
    item_application_1 = ItemApplication(id = 1, item_id = item_id_1, item_application = {"workflow":"1", "terms":"term_free", "termsDescription":"利用規約自由入力"})

    with db.session.begin_nested():
        db.session.add(item_application_1)
    db.session.commit()
    assert get_item_provide_list(item_id_1) == {"workflow":"1", "terms":"term_free", "termsDescription":"利用規約自由入力"}
    assert get_item_provide_list(item_id_2) == {}

    # error
    mocker.patch("flask_sqlalchemy.BaseQuery.first", side_effect=SQLAlchemyError)
    assert get_item_provide_list(item_id_1) == {}