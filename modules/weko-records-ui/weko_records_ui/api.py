from datetime import datetime
import os
import random
import string
import boto3
import uuid
import json
import subprocess
import requests
import traceback
from email_validator import validate_email
from flask import current_app, url_for
from flask_login import current_user
from flask_mail import Message
import hashlib
from invenio_mail.admin import _load_mail_cfg_from_db, _set_flask_mail_cfg
from flask_babelex import lazy_gettext as _
from invenio_db import db

from weko_records.api import RequestMailList, ItemsMetadata
from weko_records_ui.captcha import get_captcha_info
from weko_records_ui.errors import AuthenticationRequiredError, ContentsNotFoundError, InternalServerError, InvalidCaptchaError, InvalidEmailError, RequiredItemNotExistError
from weko_redis.redis import RedisConnection
from weko_user_profiles.models import UserProfile
from weko_deposit.api import WekoDeposit, WekoRecord
from invenio_files_rest.models import Bucket, ObjectVersion, FileInstance
from invenio_files_rest.errors import FileSizeError
from invenio_files_rest.tasks import remove_file_data
from invenio_files_rest.utils import _location_has_quota, delete_file_instance
from invenio_pidstore.models import PersistentIdentifier
from werkzeug.utils import import_string
from invenio_pidstore.resolver import Resolver
from sqlalchemy.exc import SQLAlchemyError
from weko_workflow.utils import prepare_edit_workflow, handle_finish_workflow
from weko_items_ui.views import prepare_edit_item
from weko_deposit.pidstore import get_record_identifier
from weko_workflow.headless import HeadlessActivity
from weko_deposit.api import WekoIndexer
from weko_swordserver.errors import ErrorType, WekoSwordserverException
from invenio_records.api import Record
from invenio_pidrelations.contrib.versioning import PIDVersioning
from weko_workflow.api import WorkActivity, WorkFlow as WorkFlows
from weko_workflow.errors import WekoWorkflowException

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


def get_s3_bucket_list():

    profile = UserProfile.get_by_userid(current_user.id)
    if not profile:
        raise RequiredItemNotExistError(_('S3 setting none. Please check your profile.'))
    endpoint_url = profile.s3_endpoint_url
    access_key = profile.access_key
    secret_key = profile.secret_key
    if (endpoint_url is None or endpoint_url == "") or \
        (access_key is None or access_key == "") or \
        (secret_key is None or secret_key == ""):
        raise RequiredItemNotExistError(_('S3 setting none. Please check your profile.'))

    s3_client = boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )

    try:
        response = s3_client.list_buckets()
        buckets = response['Buckets']

        bucket_name_list = [bucket['Name'] for bucket in buckets]
        return bucket_name_list
    except Exception as e:
        raise Exception(_('Getting Bucket List failed.') + str(e))

def copy_bucket_to_s3(pid, filename, org_bucket_id, checked, bucket_name):
    #get progfile
    profile = UserProfile.get_by_userid(current_user.id)
    if not profile:
        raise Exception(_('S3 setting none. Please check your profile.'))
    endpoint_url = profile.s3_endpoint_url
    access_key = profile.access_key
    secret_key = profile.secret_key
    if profile.s3_region_name:
        region_name = profile.s3_region_name
    else:
        region_name = None
    if (endpoint_url is None or endpoint_url == "") or \
        (access_key is None or access_key == "") or \
        (secret_key is None or secret_key == ""):
        raise Exception(_('S3 setting none. Please check your profile.'))

    # #create file info
    org_bucket = Bucket.query.get(org_bucket_id)
    org_obj = ObjectVersion.get(bucket=org_bucket, key=filename)
    org_fileinstance = FileInstance.get(org_obj.file_id)

    file_path = org_fileinstance.uri
    if os.path.exists(file_path) == False:
        raise Exception(_('This file is not from institutional storage.'))

    # create bucket
    if checked == 'create':
        try:
            if region_name is None:
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name='us-east-1',
                )
                response = s3_client.create_bucket(Bucket=bucket_name) # default region（us-east-1）
            else:
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name = region_name,
                )
                response = s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={
                    'LocationConstraint': region_name
                    }
                )

        except Exception as e:
            current_app.logger.exception(_('Creating Bucket failed.') + str(e))
            raise Exception(_('Creating Bucket failed.') + str(e))

    # get bucket region
    s3_client = boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )
    try:
        location_response = s3_client.get_bucket_location(Bucket=bucket_name)
        bucket_region = location_response['LocationConstraint']
        # bucket on us-east-1
        if bucket_region is None:
            bucket_region = 'us-east-1'
    except Exception as e:
        current_app.logger.exception(_('Getting region failed.') + str(e))
        raise Exception(_('Getting region failed.') + str(e))

    #make uri
    uri = 'https://' + bucket_name + '.s3.' + bucket_region + '.amazonaws.com/'

    #upload file
    s3_client = boto3.client(
        's3',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )
    try:
        s3_client.upload_file(file_path, bucket_name, filename)
        return uri + filename
    except Exception as e:
        current_app.logger.exception(_('Uploading file failed.') + str(e))
        raise Exception(_('Uploading file failed.') + str(e))

def replace_file_bucket(org_pid, org_bucket_id, file):
    print('置き換え本処理')
    from weko_workflow.api import WorkActivity

    item_id = org_pid

    pid = PersistentIdentifier.query.filter_by(
        pid_type="recid", pid_value=org_pid
    ).first()
    metadata = Record.get_record(pid.object_uuid)

    # ファイルサイズ取得
    file.seek(0, 2) # ストリームの末尾に移動
    size = file.tell() # 現在の位置はファイルサイズ
    file.seek(0) # ストリームの位置を戻す
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    idx = 0
    # 1KB = 1024B なので、sizeを1024で割りながら単位を進める
    while size >= 1024 and idx < len(units) - 1:
        size /= 1024.0
        idx += 1
    file_size_str = f"{size:.0f} {units[idx]}"

    # 整形されたデータを格納するための辞書
    formatted_data = {}
    file_matadata_key = None
    # 各属性を処理
    for key, value in metadata.items():
        # "attribute_name"を含む場合、属性を省いて値をセット
        if isinstance(value, dict) and 'attribute_name' in value:
            if 'attribute_value' in value:
                formatted_data[key] = value['attribute_value']
            elif '_resource_type' in key: # 'key' が '_resource_type' を含む場合
                formatted_data[key] = value['attribute_value_mlt'][0]
            elif 'attribute_value_mlt' in value:
                formatted_data[key] = value['attribute_value_mlt']
            else:
                formatted_data[key] = value
            if (
                isinstance(formatted_data[key], list)
                and len(formatted_data[key]) > 1
                and 'filename' in formatted_data[key][0]
            ):
                file_matadata_key = key
        else:
            formatted_data[key] = value
    if file_matadata_key is not None:
        for filedata in formatted_data[file_matadata_key]:

            if filedata['filename'] == file.filename:
                filedata.get('url', {}).pop('url', None)
                filedata['filesize'] = [{"value": file_size_str}]
    current_app.logger.info(f'フォーマットデータ{formatted_data[file_matadata_key]}')


    # 整形されたデータを出力
    result_json_string = json.dumps(formatted_data, ensure_ascii=False)

    try:
        headless = HeadlessActivity(True)
        url, current_action, recid = headless.auto(
            user_id=current_user.get_id(), item_id=item_id,
            # index=None, metadata={file_matadata_key: formatted_data[file_matadata_key]},
            index=None, metadata=formatted_data,
            files=[file], comment=None,
            link_data=None, grant_data=None
        )
    except WekoWorkflowException as ex:
        current_app.logger.exception(_('Unable to update as no suitable workflow is available.'))
        raise Exception(_('Unable to update as no suitable workflow is available.'))
    except Exception as ex:
        traceback.print_exc()
        raise WekoSwordserverException(
            f"An error occurred while {headless.current_action}.",
            ErrorType.ServerError
        ) from ex

    return True
