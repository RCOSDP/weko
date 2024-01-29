from datetime import datetime
import random
import string
from email_validator import validate_email
from flask import current_app
from flask_mail import Message
import hashlib
from invenio_db import db
from invenio_mail.admin import _load_mail_cfg_from_db, _set_flask_mail_cfg


from weko_records.api import RequestMailList
from weko_records.models import ItemApplication
from weko_records_ui.captcha import get_captcha_info
from weko_records_ui.errors import AuthenticationRequiredError, ContentsNotFoundError, InternalServerError, InvalidCaptchaError, InvalidEmailError, RequiredItemNotExistError
from weko_redis.redis import RedisConnection

def send_request_mail(item_id, mail_info):

    # Validate token
    captcha_key = mail_info.get('key')
    authorization_token = mail_info.get('authorization_token')
    if not captcha_key or not authorization_token:
        raise RequiredItemNotExistError()

    redis_connection = RedisConnection()
    datastore = redis_connection.connection(db=current_app.config['CACHE_REDIS_DB'])
    captcha_info = datastore.hgetall(captcha_key)
    encoded_token = captcha_info.get('authorization_token'.encode())
    if encoded_token is None or authorization_token is None or \
        (encoded_token.decode() != authorization_token):
        raise AuthenticationRequiredError()

    # Get mail recipients
    recipients_json = RequestMailList.get_mail_list_by_item_id(item_id)
    recipients_email = [ele['email'] for ele in recipients_json]
    if not recipients_email:
        raise ContentsNotFoundError()

    # Get request mail info
    msg_sender = mail_info.get('from')
    msg_subject = mail_info.get('subject')
    msg_message = mail_info.get('message')
    if not msg_sender or not msg_subject or not msg_message:
        raise RequiredItemNotExistError()
    msg_body = msg_sender + current_app.config.get("WEKO_RECORDS_UI_REQUEST_MESSAGE") + mail_info['message']

    # Validate request mail sender
    try :
        validate_email(msg_sender, check_deliverability=False)
    except Exception:
        # Invalid email
        raise InvalidEmailError() # 400 Error
    
    try:
        mail_cfg = _load_mail_cfg_from_db()
        _set_flask_mail_cfg(mail_cfg)
        msg = Message(
            msg_subject,
            recipients=recipients_email,
            body=msg_body
        )
        current_app.extensions['mail'].send(msg)
        notification_msg_body = current_app.config.get("WEKO_RECORDS_UI_NOTIFICATION_MESSAGE") + mail_info['message']
        notification_msg = Message(
            msg_subject,
            recipients = [msg_sender],
            body = notification_msg_body
        )
        current_app.extensions['mail'].send(notification_msg)
    except Exception:
        current_app.logger.exception('Sending Email handles unexpected error.')
        raise InternalServerError() # 500

    # Create response
    res_json = {
        "from": msg_sender,
        "subject": msg_subject,
        "message": msg_body
    }
    return True, res_json

def validate_captcha_answer(captcha_answer):

    expiration_seconds = current_app.config.get('WEKO_RECORDS_UI_CAPTCHA_EXPIRATION_SECONDS', 900)

    # Validate CAPTCHA
    captcha_key = captcha_answer.get('key')
    calculation_result = captcha_answer.get('calculation_result')
    if not captcha_key or (not calculation_result and calculation_result != 0):
        raise RequiredItemNotExistError()

    redis_connection = RedisConnection()
    datastore = redis_connection.connection(db=current_app.config['CACHE_REDIS_DB'])
    captcha_answer = datastore.hgetall(captcha_key)
    encoded_calc_answer = captcha_answer.get('calculation_result'.encode())
    # if calculation validation failed
    if encoded_calc_answer is None or calculation_result is None or \
        (int(encoded_calc_answer.decode()) != calculation_result):
        # delete Redis info
        datastore.delete(captcha_key)
        raise InvalidCaptchaError()

    authorization_token = captcha_answer.get('authorization_token'.encode())

    # Reset expiration seconds
    datastore.expire(captcha_key, expiration_seconds)

    # Create response
    res_json = {
        "authorization_token": authorization_token
    }
    return True, res_json

def create_captcha_image():

    expiration_seconds = current_app.config.get('WEKO_RECORDS_UI_CAPTCHA_EXPIRATION_SECONDS', 900)
    ttl = min(expiration_seconds, current_app.config.get('WEKO_RECORDS_UI_CAPTCHA_TTL_SECONDS', expiration_seconds))

    # Get CAPTCHA info
    captcha_info = get_captcha_info()

    # Create key
    current_dt = datetime.now()
    random_salt = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(10)])
    key = hashlib.sha1((current_dt.strftime('%Y/%m/%d-%H:%M:%S') + random_salt).encode()).hexdigest()

    # Create Authorization custom token
    random_salt = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(10)])
    authorization_token = hashlib.sha256((current_dt.strftime('%Y/%m/%d-%H:%M:%S') + random_salt).encode()).hexdigest()

    # Set calculation answer and authorization token
    redis_connection = RedisConnection()
    datastore = redis_connection.connection(db=current_app.config['CACHE_REDIS_DB'])
    datastore.hset(key, 'calculation_result', captcha_info['answer'])
    datastore.hset(key, 'authorization_token', authorization_token)
    datastore.expire(key, expiration_seconds)

    # Create response
    res_json = {
        "key": key,
        'image': captcha_info['image'],
        'ttl': ttl 
    }
    return True, res_json

def get_item_provide_list(item_id):
    if not item_id:
        return {}

    item_application_info = None
    try:
        with db.session.no_autoflush:
            item_application_info = db.session.query(ItemApplication) \
                .filter_by(item_id=item_id).first()
    except Exception:
        current_app.logger.exception('Item provide list query failed.')

    if item_application_info:
        return item_application_info.item_application
    else:
        return {}