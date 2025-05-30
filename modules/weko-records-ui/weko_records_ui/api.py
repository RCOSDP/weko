from datetime import datetime, timezone
import os
import random
import string
import sys
import hashlib
import traceback
import boto3
import tempfile
import shutil
import copy
import json
from email_validator import validate_email
from flask import current_app, request

from flask_login import current_user
from flask_mail import Message
from flask_babelex import lazy_gettext as _

from invenio_mail.admin import _load_mail_cfg_from_db, _set_flask_mail_cfg
from invenio_files_rest.models import Bucket, ObjectVersion, FileInstance
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.api import Record
from weko_logging.activity_logger import UserActivityLogger
from invenio_db import db

from weko_records.api import RequestMailList
from weko_records_ui.captcha import get_captcha_info
from weko_records_ui.errors import (
    AuthenticationRequiredError, ContentsNotFoundError, InternalServerError,
    InvalidCaptchaError, InvalidEmailError, RequiredItemNotExistError
)
from weko_redis.redis import RedisConnection
from weko_user_profiles.models import UserProfile
from invenio_files_rest.models import Bucket, ObjectVersion, FileInstance
from invenio_pidstore.models import PersistentIdentifier
from werkzeug.utils import import_string
from invenio_pidstore.resolver import Resolver
from invenio_records.api import Record
from invenio_pidrelations.contrib.versioning import PIDVersioning
from weko_workflow.api import WorkFlow
from weko_items_ui.utils import get_workflow_by_item_type_id
from weko_records.api import ItemTypes
from invenio_files_rest.models import Location
from weko_search_ui.utils import handle_check_item_is_locked, check_replace_file_import_items, import_items_to_system
from invenio_records_files.models import RecordsBuckets

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
        UserActivityLogger.info(
            operation="FILE_REQUEST_MAIL",
            target_key=item_id
        )
    except Exception:
        current_app.logger.exception('Sending Email handles unexpected error.')
        exec_info = sys.exc_info()
        tb_info = traceback.format_tb(exec_info[2])
        UserActivityLogger.error(
            operation="FILE_REQUEST_MAIL",
            target_key=item_id,
            remarks=tb_info[0]
        )
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
        raise Exception(_('S3 setting none. Please check your profile.'))
    endpoint_url = profile.s3_endpoint_url
    access_key = profile.access_key
    secret_key = profile.secret_key
    if (endpoint_url is None or endpoint_url == "") or \
        (access_key is None or access_key == "") or \
        (secret_key is None or secret_key == ""):
        raise Exception(_('S3 setting none. Please check your profile.'))

    s3_client = boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )

    try:
        response = s3_client.list_buckets()
        if response['ResponseMetadata']['HTTPStatusCode'] != 200:
            raise Exception
        else:
            buckets = response.get('Buckets')
            if buckets:
                bucket_name_list = [bucket['Name'] for bucket in buckets]
            else:
                bucket_name_list = []
        return bucket_name_list
    except Exception as e:
        current_app.logger.info(f'response: {response}')
        traceback.print_exc()
        raise Exception(_('Getting Bucket List failed.'))

def copy_bucket_to_s3(
        pid, filename, org_bucket_id, checked, bucket_name
    ):
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
    location = None
    if file_path.startswith('http'):
        # ex: https://bucket_name.s3.us-east-1.amazonaws.com/
        parts = file_path.split('/')
        location_url = parts[0] + '//' + parts[2]
        location = Location.query.filter(
            Location.uri.like(f"{location_url}%")
        ).first()
    elif file_path.startswith('s3://'):
        # s3://bucket_name/file_name
        parts = file_path.split('/')
        location_url = parts[0] + '//' + parts[2]
        location = Location.query.filter(
            Location.uri.like(f"{location_url}%")
        ).first()
    else:
        # local
        parts = file_path.split('/')
        if len(parts) > 1:
            location_url = parts[0] + '/'
            location = Location.query.filter(
                Location.uri.like(f"{location_url}%")
            ).first()
        if location is None:
            # use default location
            location = Location.get_default()
    current_app.logger.info(f'location: {location}')

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
                public_access_block_config = {
                    'BlockPublicAcls': False,
                    'IgnorePublicAcls': False,
                    'BlockPublicPolicy': False,
                    'RestrictPublicBuckets': False
                }
                s3_client.put_public_access_block(
                    Bucket=bucket_name,
                    PublicAccessBlockConfiguration=public_access_block_config
                )
                public_policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Sid": "Public",
                            "Effect": "Allow",
                            "Principal": "*",
                            "Action": ["s3:*"],
                            "Resource": f"arn:aws:s3:::{bucket_name}/*"
                        }
                    ]
                }

                s3_client.put_bucket_policy(
                    Bucket=bucket_name,
                    Policy=json.dumps(public_policy)
                )
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
                public_access_block_config = {
                    'BlockPublicAcls': False,
                    'IgnorePublicAcls': False,
                    'BlockPublicPolicy': False,
                    'RestrictPublicBuckets': False
                }
                s3_client.put_public_access_block(
                    Bucket=bucket_name,
                    PublicAccessBlockConfiguration=public_access_block_config
                )
                public_policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Sid": "Public",
                            "Effect": "Allow",
                            "Principal": "*",
                            "Action": ["s3:*"],
                            "Resource": f"arn:aws:s3:::{bucket_name}/*"
                        }
                    ]
                }

                s3_client.put_bucket_policy(
                    Bucket=bucket_name,
                    Policy=json.dumps(public_policy)
                )
        except Exception as e:
            traceback.print_exc()
            raise Exception(_('Creating Bucket failed.'))

    # get bucket region
    s3_client = boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )
    try:
        location_response = s3_client.get_bucket_location(Bucket=bucket_name)
        bucket_region = location_response.get('LocationConstraint')
        # bucket on us-east-1
        if bucket_region is None:
            bucket_region = 'us-east-1'
    except Exception as e:
        traceback.print_exc()
        raise Exception(_('Getting region failed.'))

    #make uri
    # ex: https://bucket_name.s3.us-east-1.amazonaws.com/
    parts = endpoint_url.split('/')
    sub_parts = parts[2].split('.')
    if len(sub_parts) > 3:
        end_uri = ".".join(sub_parts[3:])
    else:
        end_uri = sub_parts[3]

    uri = parts[0] + '//' + bucket_name + '.' + sub_parts[1] + '.' + bucket_region + '.' + end_uri +'/'

    current_app.logger.info(f'location: {location}')

    if location.type is None:
        # local to S3

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
            traceback.print_exc()
            raise Exception(_('Uploading file failed.'))

    else:
        # S3 to S3

        s3_client = boto3.client(
            's3',
            aws_access_key_id=location.access_key,
            aws_secret_access_key=location.secret_key,
        )
        # コピー元とコピー先の情報
        org_bucket_name = None
        if location.type == "s3":
            # S3のバケット名を取得
            org_bucket_name = location.uri.split('/')[2]
            base = location.uri.split('/')[0] + '//' + org_bucket_name
            file_path = org_bucket_name + org_fileinstance.uri.replace(base, '')
        elif location.type == "s3_vh":
            if location.uri.startswith('https://s3.'):
                # ex: https://s3.us-east-1.amazonaws.com/bucket_name/file_name
                parts = location.uri.split('/')
                org_bucket_name = parts[3]
                base = parts[0] + '//' + parts[2] + '/' + org_bucket_name
                file_path = (
                    org_bucket_name
                    + org_fileinstance.uri.replace(base, '')
                )
            else:
                # ex: https://bucket_name.s3.us-east-1.amazonaws.com/file_name
                parts = location.uri.split('/')
                sub_parts = parts[2].split('.')
                org_bucket_name = sub_parts[0]
                base = parts[0] + '//' + parts[2]
                file_path = (
                    org_bucket_name
                    + org_fileinstance.uri.replace(base, '')
                )

        current_app.logger.info(f'org_bucket_name: {org_bucket_name}')
        current_app.logger.info(f'base: {base}')
        current_app.logger.info(f'file_path: {file_path}')
        source_bucket = org_bucket_name
        source_key = file_path
        destination_bucket = bucket_name
        destination_key = filename

        # コピーの実行
        copy_source = {
            'Bucket': source_bucket,
            'Key': source_key
        }
        current_app.logger.info(f'copy_source: {copy_source}')

        try:
            s3_client.head_object(Bucket=source_bucket, Key=source_key)
        except s3_client.exceptions.NoSuchKey:
            traceback.print_exc()
            raise Exception(_('The source file cannot be found.'))
        try:
            s3_client.copy(
                copy_source,
                destination_bucket,
                destination_key
            )
            return uri + filename
        except Exception as e:
            traceback.print_exc()
            current_app.logger.error(e)
            raise Exception(_('Uploading file failed.'))


def get_file_place_info(org_pid, org_bucket_id, file_name):

    file_place = None
    url = None
    new_bucket_id = None
    new_version_id = None

    # check item locked
    try:
        item = {"id": org_pid}
        handle_check_item_is_locked(item)
    except Exception as e:
        traceback.print_exc()
        raise Exception(_('Cannot update because the corresponding item is being edited.'))

    from weko_workflow.api import WorkActivity

    # get workflow
    pid_value = org_pid
    record_class = import_string('weko_deposit.api:WekoDeposit')
    resolver = Resolver(pid_type='recid',
                        object_type='rec',
                        getter=record_class.get_record)
    recid, deposit = resolver.resolve(pid_value)
    activity = WorkActivity()
    latest_pid = PIDVersioning(child=recid).last_child
    item_uuid = latest_pid.object_uuid
    item_type_id = deposit.get('item_type_id')
    item_type = ItemTypes.get_by_id(item_type_id)

    latest_activity = activity.get_workflow_activity_by_item_id(item_uuid)

    if latest_activity:
        workflow = WorkFlow().get_workflow_by_id(workflow_id=latest_activity.workflow_id)

    else:
        latest_activity = activity.get_workflow_activity_by_item_id(
            recid.object_uuid
        )
        workflow = get_workflow_by_item_type_id(item_type.name_id,
                                                item_type_id)
        current_app.logger.info(
            f"workflow: {workflow}"
        )

    if workflow is None:
        location_id = None
    else:
        location_id = workflow.location_id

    if location_id is None:
        location = Location.get_default()
    else:
        location = Location.query.get(location_id)


    org_bucket = Bucket.query.get(org_bucket_id)
    org_obj = ObjectVersion.get(bucket=org_bucket, key=file_name)
    org_fileinstance = FileInstance.get(org_obj.file_id)

    if location.type is None:
    # weko local strage
        file_place = 'local'
    else:
    # S3 strage
        file_place = 'S3'

        new_bucket = Bucket.create(location=location, storage_class=current_app.config[
                'DEPOSIT_DEFAULT_STORAGE_CLASS'
            ])
        org_bucket.sync(new_bucket)
        current_obj = ObjectVersion.get(bucket=new_bucket, key=file_name)
        current_fileinstance = FileInstance.get(current_obj.file_id)

        new_obj = ObjectVersion.create(bucket=new_bucket, key=file_name)
        new_fileinstance = FileInstance.create()
        new_obj.file_id = new_fileinstance.id
        new_obj.root_file_id = new_fileinstance.id

        current_obj.remove()

        new_bucket_id = str(new_bucket.id)
        new_version_id = str(new_obj.version_id)
        uuid_str = str(new_fileinstance.id)
        uuid_lst = list(uuid_str)
        directory_path = "".join(uuid_lst[0:2]) + "/" + "".join(uuid_lst[2:4]) + "/" + "".join(uuid_lst[4:])


        # AWSクライアントの設定
        if location.type == "s3":
            region = location.s3_region_name
            uri_list = location.uri.split('/')
            bucket_name = uri_list[2]
            if len(uri_list) >= 4:
                pre = '/'.join(uri_list[3:]) + '/' * (not '/'.join(uri_list[3:]).endswith('/'))
                directory_path = pre + directory_path
        else:
            region = location.s3_region_name
            if location.uri.startswith('https://s3'):
                # ex: https://s3.us-east-1.amazonaws.com/bucket_name/file_name
                parts = location.uri.split('/')
                bucket_name = parts[3]
                if len(parts) >= 5:
                    pre = '/'.join(parts[4:]) + '/' * (not '/'.join(parts[4:]).endswith('/'))
                    directory_path = pre + directory_path
            else:
                # ex: https://bucket_name.s3.us-east-1.amazonaws.com/file_name
                parts = location.uri.split('/')
                sub_parts = parts[2].split('.')
                bucket_name = sub_parts[0]
                if len(sub_parts) >= 3:
                    pre = '/'.join(parts[3:]) + '/' * (not '/'.join(parts[3:]).endswith('/'))
                    directory_path = pre + directory_path

        if region is None:
                s3 = boto3.client('s3',
                                aws_access_key_id=location.access_key,
                                aws_secret_access_key=location.secret_key,)
        else:
            s3 = boto3.client('s3',
                            aws_access_key_id=location.access_key,
                            aws_secret_access_key=location.secret_key,
                            region_name=region,)

        try:
            # 署名付きURLの生成
            url = s3.generate_presigned_url(
                ClientMethod = 'put_object',
                Params = {'Bucket' : bucket_name,
                'Key' : bucket_name + "/" + directory_path + "/" + 'data',
                'ContentType' : 'binary/octet-stream'},
                ExpiresIn = 300,
                HttpMethod = 'PUT'
            )
        except Exception as e:
            traceback.print_exc()
            raise Exception(_("Unexpected error occurred."))

    return file_place, url, new_bucket_id, new_version_id


def replace_file_bucket(org_pid, org_bucket_id, file=None,
                        file_name=None, file_size=None,
                        file_checksum=None,
                        new_bucket_id=None, new_version_id=None):
    # need for weko strage: file, file_name, file_size
    # need for S3 strage: file_name, file_size,
    #                     file_checksum,
    #                     new_bucket_id, new_version_id

    result = False

    # get workflow
    pid_value = org_pid
    record_class = import_string('weko_deposit.api:WekoDeposit')
    resolver = Resolver(pid_type='recid',
                        object_type='rec',
                        getter=record_class.get_record)
    recid, deposit = resolver.resolve(pid_value)
    latest_pid = PIDVersioning(child=recid).last_child
    item_uuid = latest_pid.object_uuid
    item_type_id = deposit.get('item_type_id')
    item_type = ItemTypes.get_by_id(item_type_id)

    # check item locked
    try:
        item = {"id": org_pid}
        handle_check_item_is_locked(item)
    except Exception as e:
        current_app.logger.exception(_('Cannot update because the corresponding item is being edited.'))
        raise Exception(_('Cannot update because the corresponding item is being edited.'))


    pid = PersistentIdentifier.query.filter_by(
        pid_type="recid", pid_value=org_pid
    ).first()
    metadata = Record.get_record(pid.object_uuid)

    # ファイルサイズ取得
    size = file_size
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    idx = 0

    # 1KB = 1024B なので、sizeを1024で割りながら単位を進める
    while size >= 1024 and idx < len(units) - 1:
        size /= 1024.0
        idx += 1

    # 中間のファイルサイズを表示する際の条件を追加
    if size < 1024:
        file_size_str = f"{size:.0f} {units[idx]}"
    else:
        file_size_str = f"{size:.1f} {units[idx]}"


    # 整形されたデータを格納するための辞書
    formatted_data = {}
    file_matadata_key = None
    if new_bucket_id is None:
        # 機関にファイル情報とアップ
        # 各属性を処理
        for key, value in metadata.items():
            # "attribute_name"を含む場合、属性を省いて値をセット
            if isinstance(value, dict) and 'attribute_name' in value:
                if 'attribute_value' in value:
                    formatted_data[key] = value['attribute_value']
                elif 'attribute_value_mlt' in value:
                    print(value['attribute_value_mlt'][0])
                    if (
                        len(value['attribute_value_mlt']) > 0
                        and 'resourcetype' in value['attribute_value_mlt'][0]
                    ):
                        formatted_data[key] = value['attribute_value_mlt'][0]
                    else:
                        formatted_data[key] = value['attribute_value_mlt']
                else:
                    formatted_data[key] = value
                if (
                    isinstance(formatted_data[key], list)
                    and len(formatted_data[key]) > 0
                    and 'filename' in formatted_data[key][0]
                ):
                    file_matadata_key = key
            else:
                formatted_data[key] = value
        if file_matadata_key is not None:
            for filedata in formatted_data[file_matadata_key]:

                if filedata['filename'] == file_name:
                    filedata.get('url', {}).pop('url', None)
                    filedata['filesize'] = [{"value": file_size_str}]
    else:
        # ファイルはアップ済み
        # メタデータ更新
        # 各属性を処理
        for key, value in metadata.items():
            # "attribute_name"を含む場合、属性を省いて値をセット
            if isinstance(value, dict) and 'attribute_name' in value:
                if 'attribute_value' in value:
                    formatted_data[key] = value['attribute_value']
                elif 'attribute_value_mlt' in value:
                    if (
                        len(value['attribute_value_mlt']) > 0
                        and 'resourcetype' in value['attribute_value_mlt'][0]
                    ):
                        formatted_data[key] = value['attribute_value_mlt'][0]
                    else:
                        formatted_data[key] = value['attribute_value_mlt']
                else:
                    formatted_data[key] = value
                if (
                    isinstance(formatted_data[key], list)
                    and len(formatted_data[key]) > 0
                    and 'filename' in formatted_data[key][0]
                ):
                    file_matadata_key = key
            else:
                if isinstance(value, dict) and 'deposit' in value:
                    formatted_data[key]  = {"deposit":new_bucket_id}
                else:
                    formatted_data[key] = value
        if file_matadata_key is not None:
            for filedata in formatted_data[file_matadata_key]:
                if filedata['filename'] == file_name:
                    filedata.get('url', {}).pop('url', None)
                    filedata['filesize'] = [{"value": file_size_str}]
                    filedata['version_id'] = new_version_id

    if new_bucket_id is None:
        # weko local strage
        # ファイルの仮保存
        temp_path = os.path.join(
            tempfile.gettempdir(),
            current_app.config.get("WEKO_SEARCH_UI_IMPORT_TMP_PREFIX")
                    + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")[:-3]
        )
        os.mkdir(temp_path)
        file_path = temp_path + "/" + file_name
        file.save(file_path)


        try:
            # list_recordの作成
            formatted_data.pop("item_title")
            formatted_data.pop("owner")
            formatted_data.pop("title")

            list_record = [
                {
                    "$schema": f"/items/jsonschema/{item_type.id}",
                    "id": org_pid,
                    "uri": request.host_url + "records/" + str(org_pid),
                    "_id": org_pid,
                    "metadata": formatted_data,
                    "item_type_name": item_type.item_type_name.name,
                    "item_type_id": item_type.id,
                    "publish_status": "public" if formatted_data.get("publish_status") == "0" else "private",
                    "edit_mode": "upgrade",
                    "link_data": {},
                    "file_path": [file_path],
                }
            ]

            check_result = check_replace_file_import_items(list_record, temp_path)
            current_app.logger.info(f'チェック結果{check_result}')
            if check_result.get("error"):
                current_app.logger.info(f'エラー{check_result.get("error")}')
                raise Exception(f'{check_result.get("error")}')
            else:
                item = check_result.get("list_record")[0]
                if not item or item.get("errors"):
                    error_msg = (
                        ", ".join(item.get("errors"))
                        if item and item.get("errors")
                        else "item_missing"
                    )
                    current_app.logger.error(f"Error in check_import_items: {error_msg}")
                import_result = import_items_to_system(item, file_replace_owner=current_user.id)
                if not import_result.get("success"):
                    current_app.logger.error(
                        f"Error in import_items_to_system: {item.get('error_id')}"
                    )
                    raise Exception(f"Error in import_items_to_system: {item.get('error_id')}")
                result = True

        except Exception as e:
            # エラー処理
            traceback.print_exc()
            raise Exception(f"{e}")

        finally:
            # ディレクトリを削除
            if os.path.exists(temp_path):
                shutil.rmtree(temp_path)
    else:
        # S3 strage
        # list_recordの作成
        formatted_data.pop("item_title")
        formatted_data.pop("owner")
        formatted_data.pop("title")

        list_record = [
            {
                "$schema": f"/items/jsonschema/{item_type.id}",
                "id": org_pid,
                "uri": request.host_url + "records/" + str(org_pid),
                "_id": org_pid,
                "metadata": formatted_data,
                "item_type_name": item_type.item_type_name.name,
                "item_type_id": item_type.id,
                "publish_status": "public" if formatted_data.get("publish_status") == "0" else "private",
                "edit_mode": "upgrade",
                "link_data": {},
            }
        ]
        formatted_data_copy = copy.deepcopy(formatted_data)

        try:
            check_result = check_replace_file_import_items(list_record)
            current_app.logger.info(f'チェック結果{check_result}')
            if check_result.get("error"):
                current_app.logger.info(f'エラー{check_result.get("error")}')
                raise Exception(f'{check_result.get("error")}')
            else:
                item = check_result.get("list_record")[0]
                if not item or item.get("errors"):
                    error_msg = (
                        ", ".join(item.get("errors"))
                        if item and item.get("errors")
                        else "item_missing"
                    )
                    current_app.logger.error(f"Error in check_import_items: {error_msg}")
                import_result = import_items_to_system(item, file_replace_owner=current_user.id)
                if not import_result.get("success"):
                    current_app.logger.error(
                        f"Error in import_items_to_system: {item.get('error_id')}"
                    )
                    raise Exception(f"Error in import_items_to_system: {item.get('error_id')}")
        except Exception as e:
            # エラー処理
            traceback.print_exc()
            raise Exception(f"{e}")

        # records_bucketsの更新
        recid, deposit = resolver.resolve(pid_value)
        latest_pid = PIDVersioning(child=recid).last_child
        item_uuid = latest_pid.object_uuid

        records_buckets = RecordsBuckets.query.filter_by(
            record_id=item_uuid).first()
        records_buckets.bucket_id = new_bucket_id
        pid = PersistentIdentifier.get('recid', pid_value)
        org_records_buckets = RecordsBuckets.query.filter_by(
            record_id=pid.object_uuid).first()
        org_records_buckets.bucket_id = new_bucket_id

        # fileinstanceの更新
        before_bucket = Bucket.query.get(new_bucket_id)
        before_obj = ObjectVersion.get(bucket=before_bucket, key=file_name)
        before_fileinstance = FileInstance.get(before_obj.file_id)

        after_bucket = Bucket.query.get(new_bucket_id)
        after_obj = ObjectVersion.get(bucket=after_bucket, key=file_name)
        after_fileinstance = FileInstance.get(after_obj.file_id)
        location = Location.query.get(after_bucket.default_location)
        uuid_str = str(after_fileinstance.id)
        uuid_lst = list(uuid_str)
        directory_path = "".join(uuid_lst[0:2]) + "/" + "".join(uuid_lst[2:4]) + "/" + "".join(uuid_lst[4:])
        file_uri = location.uri + directory_path + "/" + 'data'
        after_fileinstance.set_uri(uri=file_uri, size=file_size, checksum='sha256:' + file_checksum, )

        before_json = before_fileinstance.json
        after_json = {}
        for key, value in before_json:
            if key == 'url':
                after_json[key] = { "url": file_uri}
            elif key == 'filesize':
                after_json[key] = [{ "value": file_size_str}]
            elif key == 'version_id':
                after_json[key] = new_version_id
            else:
                after_json[key] = value
        after_fileinstance.json = after_json
        db.session.commit()

        # version:Keepで再更新
        # list_recordの作成
        list_record = [
            {
                "$schema": f"/items/jsonschema/{item_type.id}",
                "id": org_pid,
                "uri": request.host_url + "records/" + str(org_pid),
                "_id": org_pid,
                "metadata": formatted_data_copy,
                "item_type_name": item_type.item_type_name.name,
                "item_type_id": item_type.id,
                "publish_status": "public" if formatted_data_copy.get("publish_status") == "0" else "private",
                "edit_mode": "keep",
                "link_data": {},
            }
        ]

        try:
            check_result = check_replace_file_import_items(list_record)
            current_app.logger.info(f'チェック結果{check_result}')
            if check_result.get("error"):
                current_app.logger.info(f'エラー{check_result.get("error")}')
                raise Exception(f'{check_result.get("error")}')
            else:
                item = check_result.get("list_record")[0]
                if not item or item.get("errors"):
                    error_msg = (
                        ", ".join(item.get("errors"))
                        if item and item.get("errors")
                        else "item_missing"
                    )
                    current_app.logger.error(f"Error in check_import_items: {error_msg}")
                import_result = import_items_to_system(item, file_replace_owner=current_user.id)
                if not import_result.get("success"):
                    current_app.logger.error(
                        f"Error in import_items_to_system: {item.get('error_id')}"
                    )
                    raise Exception(f"Error in import_items_to_system: {item.get('error_id')}")
        except Exception as e:
            # エラー処理
            traceback.print_exc()
            raise Exception(f"{e}")

        # record_metadata update
        metadata = Record.get_record(pid.object_uuid)
        for key, value in metadata.items():
            if isinstance(value, dict) and 'attribute_name' in value:
                if 'attribute_value_mlt' in value:
                    if (
                        len(value['attribute_value_mlt']) > 0
                        and 'url' in value['attribute_value_mlt'][0]
                    ):
                        for file_list in value['attribute_value_mlt']:
                            if file_list['filename'] == file_name:
                                file_list['version_id'] = new_version_id
            else:
                if isinstance(value, dict) and 'deposit' in value:
                    value['deposit'] = new_bucket_id
        metadata.commit()
        result = True

    return result
