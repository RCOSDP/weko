from datetime import datetime, timezone
import os
import random
import string
import sys
import hashlib
import traceback
import tempfile
import shutil
import copy
import orjson
from urllib.parse import urlparse, urljoin, uses_relative, uses_netloc

from botocore.exceptions import BotoCoreError, ClientError
from boto3.s3.transfer import TransferConfig
from email_validator import validate_email
from flask import current_app, request

from flask_login import current_user
from flask_mail import Message
from flask_babelex import lazy_gettext as _
from sqlalchemy import func, String

from invenio_mail.admin import _load_mail_cfg_from_db, _set_flask_mail_cfg
from invenio_files_rest.models import Bucket, ObjectVersion, FileInstance
from invenio_files_rest.utils import parse_storage_host
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.api import Record
from weko_logging.activity_logger import UserActivityLogger
from invenio_db import db

from weko_records.api import RequestMailList
from weko_records.models import ItemApplication
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


def get_s3_bucket_list():
    """Get S3 bucket list.
    Returns:
        list: S3 bucket name list.
    """
    if not current_user or not current_user.is_authenticated:
        raise Exception(_("Not authenticated user."))

    profile = UserProfile.get_by_userid(current_user.id)
    if not profile:
        raise Exception(_('S3 setting none. Please check your profile.'))

    if not profile.client_credentials_configured:
        raise Exception(_('S3 setting none. Please check your profile.'))

    response = None
    try:
        s3_client = profile.create_s3_client()
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
        current_app.logger.error(e)
        traceback.print_exc()
        raise Exception(_('Getting Bucket List failed.'))


def copy_bucket_to_s3(
        pid, filename, org_bucket_id, checked, bucket_name
    ):
    """
    Copy file to S3 bucket.
    Args:
        pid (str): Persistent identifier value.
        filename (str): File name.
        org_bucket_id (int): Original bucket ID.
        checked (str): Create bucket option.
        bucket_name (str): Destination bucket name.
    Returns:
        str: File URI.
    """

    def _is_same_storage_service(source_s3_client, destination_s3_client):
        """Check if source and destination storage service are the same.
        Args:
            source_s3_client (boto3.client): Boto3 S3 client instance for source.
            destination_s3_client (boto3.client): Boto3 S3 client instance for destination.
        Returns:
            bool: True if same service, False otherwise.
        """
        source_url_info = urlparse(source_s3_client.meta.endpoint_url)
        destination_url_info = urlparse(destination_s3_client.meta.endpoint_url)
        source_service = parse_storage_host(source_url_info.netloc)
        destination_service = parse_storage_host(destination_url_info.netloc)
        if source_service["service"] is None or destination_service["service"] is None:
            return source_url_info.netloc == destination_url_info.netloc
        return source_service["service"] == destination_service["service"]

    # Add s3 to uses_relative and uses_netloc
    if not "s3" in uses_relative:
        uses_relative.append("s3")
    if not "s3" in uses_netloc:
        uses_netloc.append("s3")

    # Get profile
    profile = UserProfile.get_by_userid(current_user.id)
    if not profile or not profile.client_credentials_configured:
        raise Exception(_('S3 setting none. Please check your profile.'))

    # Create file info
    source_bucket = Bucket.query.get(org_bucket_id)
    source_content_info = ObjectVersion.get(bucket=source_bucket, key=filename)
    source_file_instance = FileInstance.get(source_content_info.file_id)

    # source_location = source_file_instance.get_location_by_file_instance()
    source_location = db.session.query(Location).filter(
        func.cast(source_file_instance.uri, String).like(Location.uri + "%")) \
        .order_by(func.length(Location.uri).desc()) \
        .first()
    if source_location is None:
        source_location = Location.get_default()

    # Create S3 client
    destination_s3_client = profile.create_s3_client()

    # Create bucket if not exist
    if checked == 'create':
        create_storage_bucket(
            destination_s3_client,
            profile.s3_endpoint_url,
            profile.s3_region_name,
            bucket_name
        )

    # get bucket region
    try:
        location_response = destination_s3_client.get_bucket_location(Bucket=bucket_name)
        bucket_region = location_response.get('LocationConstraint')
        # bucket on us-east-1
        if bucket_region is None:
            bucket_region = 'us-east-1'
    except Exception as e:
        traceback.print_exc()
        raise Exception(_('Getting region failed.'))

    # Create URI from endpoint URL
    # ex: https://bucket_name.s3.us-east-1.amazonaws.com/
    destination_url = destination_s3_client.meta.endpoint_url

    # Check if service is aws or wasabi
    can_use_virtual_hosted_style = False
    if not destination_url or destination_url.endswith('amazonaws.com') \
        or destination_url.endswith('wasabisys.com'):
        can_use_virtual_hosted_style = True

    uri = ""
    if not can_use_virtual_hosted_style:
        # path style
        url = urlparse(destination_url)
        uri = f"{url.scheme}://{url.netloc}/{bucket_name}/"
    else:
        # virtual hosted style
        url = urlparse(destination_url)
        uri = f"{url.scheme}://{bucket_name}.{url.netloc}/"

    current_app.logger.debug(f"Profile endpoint URL: {profile.s3_endpoint_url}")
    current_app.logger.debug(f"Profile region name: {profile.s3_region_name}")

    # Get TransferConfig from config
    transfer_setting = {
        "multipart_threshold": current_app.config.get("WEKO_RECORDS_UI_S3_TRANSFER_MULTIPART_THRESHOLD", 8 * 1024 * 1024),
        "multipart_chunksize": current_app.config.get("WEKO_RECORDS_UI_S3_TRANSFER_MULTIPART_CHUNKSIZE", 8 * 1024 * 1024),
        "use_threads": current_app.config.get("WEKO_RECORDS_UI_S3_TRANSFER_USE_THREADS", True),
        "max_concurrency": current_app.config.get("WEKO_RECORDS_UI_S3_TRANSFER_MAX_CONCURRENCY", 10),
    }
    s3_transfer_config = TransferConfig(**transfer_setting)

    if source_location.type is None:
        # local to S3

        #upload file
        try:
            destination_s3_client.upload_file(
                source_file_instance.uri,
                bucket_name,
                filename,
                Config=s3_transfer_config
            )
            return urljoin(uri, filename)
        except Exception as e:
            traceback.print_exc()
            raise Exception(_('Uploading file failed.'))

    else:
        # S3 to S3

        s3_client_source = source_location.create_s3_client()
        # コピー元とコピー先の情報
        source_bucket_name = None
        source_file_key = None
        file_instance_uri = source_file_instance.uri
        parsed_uri = urlparse(file_instance_uri.strip())
        if source_location.type == "s3":
            # Get source bucket name and file key
            # ex: s3://bucket_name/prefix/file_name
            source_bucket_name = parsed_uri.netloc
            source_file_key = parsed_uri.path.lstrip("/")
        elif source_location.type == "s3_vh":
            # Get source bucket name and file key
            if parsed_uri.netloc.startswith("s3."):
                # https://s3.region-code.amazonaws.com/bucket-name/key-name
                # ex: https://s3.us-east-1.amazonaws.com/bucket_name/file_name
                path = parsed_uri.path.lstrip("/")
                parts = path.split("/")
                source_bucket_name = parts[0]
                source_file_key = "/".join(parts[1:])
            else:
                # https://bucket-name.s3.region-code.amazonaws.com/key-name
                # ex: https://bucket_name.s3.us-east-1.amazonaws.com/file_name
                netloc = parsed_uri.netloc
                source_file_key = parsed_uri.path.lstrip("/")
                parts = netloc.split('.')
                source_bucket_name = parts[0]

        current_app.logger.debug(f'destination_bucket: {bucket_name}')
        current_app.logger.debug(f'destination_key: {filename}')
        destination_bucket = bucket_name
        destination_key = filename

        # Validate source file bucket and key
        if not source_bucket_name or not source_file_key:
            raise Exception(_("The source bucket or file cannot be found."))

        copy_source = {
            "Bucket": source_bucket_name,
            "Key": source_file_key
        }
        current_app.logger.debug(f"copy_source: {copy_source}")

        try:
            s3_client_source.head_object(
                Bucket=copy_source["Bucket"],
                Key=copy_source["Key"]
            )
        except Exception as e:
            traceback.print_exc()
            raise Exception(_('The source file cannot be found.'))
        try:
            if _is_same_storage_service(
                s3_client_source,
                destination_s3_client
            ):
                # Same storage service
                destination_s3_client.copy(
                    copy_source,
                    destination_bucket,
                    destination_key,
                    SourceClient=s3_client_source,
                    Config=s3_transfer_config
                )
            else:
                # Different storage service
                # Check file size
                source_file_size = source_file_instance.size
                # Upload file size limit from config
                file_size_limit = current_app.config.get(
                    "WEKO_RECORDS_UI_S3_CROSS_COPY_MAX_FILE_SIZE",
                    20 * 1024 * 1024 * 1024
                )
                if source_file_size < file_size_limit:
                    obj = s3_client_source.get_object(
                        Bucket=copy_source["Bucket"],
                        Key=copy_source["Key"]
                    )
                    body = obj["Body"]
                    destination_s3_client.upload_fileobj(
                        body, destination_bucket, destination_key,
                        Config=s3_transfer_config
                    )
                else:
                    raise Exception(_("The source file size exceeds the limit for cross-service copy."))
        except (ClientError, BotoCoreError) as e:
            current_app.logger.error(e)
            current_app.logger.error(traceback.format_exc())
            raise Exception(_('Uploading file failed.'))
        except Exception as e:
            current_app.logger.error(e)
            current_app.logger.error(traceback.format_exc())
            raise

        # Return file URI
        return urljoin(uri, filename)

def create_storage_bucket(s3_client, endpoint_url, region_name, bucket_name):
    """Create storage bucket.
    Args:
        s3_client (boto3.client): Boto3 S3 client instance.
        endpoint_url (str): S3 endpoint URL.
        region_name (str): S3 region name.
        bucket_name (str): Bucket name.
    Raises:
        Exception: Bucket already exists.
        Exception: Creating Bucket failed.
    """
    # Check if bucket exists
    if bucket_exists(s3_client, bucket_name):
        raise Exception(_('Bucket already exists.'))

    # Check if AWS S3
    is_aws = not endpoint_url or endpoint_url.endswith('amazonaws.com')

    # create bucket
    try:
        region_name = region_name or s3_client.meta.region_name
        if not region_name or region_name == 'us-east-1':
            s3_client.create_bucket(Bucket=bucket_name) # default region（us-east-1）
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={
                    'LocationConstraint': region_name
                }
            )

        # Set public access block
        if is_aws:
            s3_client.put_public_access_block(
                Bucket=bucket_name,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': False,
                    'IgnorePublicAcls': False,
                    'BlockPublicPolicy': False,
                    'RestrictPublicBuckets': False
                }
            )
        # Set bucket policy
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
            Policy=orjson.dumps(public_policy).decode('utf-8')
        )
    except Exception as e:
        current_app.logger.error(e)
        traceback.print_exc()
        raise Exception(_('Creating Bucket failed.'))


def bucket_exists(s3_client, bucket_name):
    # Check if bucket exists
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        return True # Bucket exists
    except Exception:
        return False


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
        current_app.logger.error(e)
        traceback.print_exc()
        raise Exception(_("Cannot update because the corresponding item is being edited."))

    from weko_workflow.api import WorkActivity

    # get workflow
    pid_value = org_pid
    record_class = import_string("weko_deposit.api:WekoDeposit")
    resolver = Resolver(pid_type="recid",
                        object_type="rec",
                        getter=record_class.get_record)
    recid, deposit = resolver.resolve(pid_value)
    latest_pid = PIDVersioning(child=recid).last_child
    item_uuid = latest_pid.object_uuid

    org_bucket = Bucket.query.get(org_bucket_id)
    org_obj = ObjectVersion.get(bucket=org_bucket, key=file_name)
    org_fileinstance = FileInstance.get(org_obj.file_id)

    current_app.logger.debug(f"item_uuid: {item_uuid}")
    current_app.logger.debug(f"recid.object_uuid: {recid.object_uuid}")

    latest_activity = WorkActivity().get_workflow_activity_by_item_id(item_uuid)

    # Get location
    location = None
    if latest_activity:
        workflow = WorkFlow().get_workflow_by_id(
            workflow_id=latest_activity.workflow_id
        )
        current_app.logger.debug(f"workflow: {workflow}")
        location_id = workflow.location_id if workflow else None
        if location_id:
            location = Location.query.get(location_id)
    else:
        location = db.session.query(Location).filter(
            func.cast(org_fileinstance.uri, String).like(Location.uri + "%")) \
            .order_by(func.length(Location.uri).desc()) \
            .first()

    if not location:
        location = Location.get_default()

    current_app.logger.debug(f"location_id: {location.id}")
    current_app.logger.debug(f"location.type: {location.type}")

    if location.type is None:
    # weko local storage
        file_place = "local"
    else:
    # S3 storage
        file_place = "S3"

        new_bucket = Bucket.create(
            location=location,
            storage_class=current_app.config["DEPOSIT_DEFAULT_STORAGE_CLASS"]
        )
        org_bucket.sync(new_bucket)
        current_obj = ObjectVersion.get(bucket=new_bucket, key=file_name)

        new_obj = ObjectVersion.create(bucket=new_bucket, key=file_name)
        new_fileinstance = FileInstance.create()
        new_obj.file_id = new_fileinstance.id
        new_obj.root_file_id = new_fileinstance.id

        current_obj.remove()

        new_bucket_id = str(new_bucket.id)
        new_version_id = str(new_obj.version_id)
        file_instance_uuid = str(new_fileinstance.id)
        # Create file key
        new_file_key = os.path.join(
            file_instance_uuid[0:2], file_instance_uuid[2:4],
            file_instance_uuid[4:], "data"
        )

        # AWSクライアントの設定
        bucket_name = None
        prev_file_key = None
        file_instance_uri = org_fileinstance.uri
        parsed_uri = urlparse(file_instance_uri.strip())
        if location.type == "s3":
            # Get source bucket name and file key
            # ex: s3://bucket_name/prefix/file_name
            bucket_name = parsed_uri.netloc
            prev_file_key = parsed_uri.path.lstrip("/")
        else:
            if parsed_uri.netloc.startswith("s3."):
                # https://s3.region-code.amazonaws.com/bucket-name/key-name
                # ex: https://s3.us-east-1.amazonaws.com/bucket_name/file_name
                path = parsed_uri.path.lstrip("/")
                parts = path.split("/")
                bucket_name = parts[0]
                prev_file_key = "/".join(parts[1:])
            else:
                # https://bucket-name.s3.region-code.amazonaws.com/key-name
                # ex: https://bucket_name.s3.us-east-1.amazonaws.com/file_name
                netloc = parsed_uri.netloc
                prev_file_key = parsed_uri.path.lstrip("/")
                parts = netloc.split(".")
                bucket_name = parts[0]

        if len(prev_file_key.split("/")) > len(new_file_key.split("/")):
            # Adjust new_file_key depth to match prev_file_key depth
            new_key_depth = len(new_file_key.split("/"))
            prev_key_parts = prev_file_key.split("/")
            new_file_key = "/".join(
                prev_key_parts[:-new_key_depth]) + new_file_key

        if not bucket_name or not new_file_key:
            raise Exception(_("The source bucket or file cannot be found."))

        try:
            s3_client = location.create_s3_client()
            # 署名付きURLの生成
            url = s3_client.generate_presigned_url(
                ClientMethod="put_object",
                Params = {
                    "Bucket" : bucket_name,
                    "Key" : new_file_key,
                    "ContentType" : "binary/octet-stream"
                },
                ExpiresIn = 300,
                HttpMethod = "PUT"
            )
        except Exception as e:
            current_app.logger.error(e)
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
    record_class = import_string("weko_deposit.api:WekoDeposit")
    resolver = Resolver(pid_type="recid",
                        object_type="rec",
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
                    current_app.logger.debug(value['attribute_value_mlt'][0])
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
