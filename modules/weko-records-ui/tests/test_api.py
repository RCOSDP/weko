import json

from smtplib import SMTPException
from mock import patch
import pytest
from botocore.exceptions import ClientError
from flask import url_for,current_app,make_response
from flask_login import UserMixin
import uuid
from pytest_mock import mocker
from sqlalchemy.exc import SQLAlchemyError
from unittest.mock import patch, MagicMock

from invenio_accounts.testutils import login_user_via_session, create_test_user
from weko_records.models import ItemApplication
from weko_records_ui.api import (
    bucket_exists,
    copy_bucket_to_s3,
    create_captcha_image,
    create_storage_bucket,
    get_file_place_info,
    get_item_provide_list,
    get_s3_bucket_list,
    send_request_mail,
    validate_captcha_answer,
)
from weko_records_ui.errors import AuthenticationRequiredError, ContentsNotFoundError, InternalServerError, InvalidCaptchaError, InvalidEmailError, RequiredItemNotExistError
from weko_redis.redis import RedisConnection
from weko_user_profiles.models import UserProfile
from .helpers import login, logout
from invenio_records_files.models import RecordsBuckets
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_files_rest.models import Location
from werkzeug.datastructures import FileStorage
from io import BytesIO
from invenio_files_rest.models import Bucket, ObjectVersion, FileInstance
from invenio_records.api import Record

# def send_request_mail(item_id, mail_info):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_api.py::test_send_request_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_send_request_mail(app, make_request_maillist):

    redis_connection = RedisConnection()
    datastore = redis_connection.connection(db=app.config['CACHE_REDIS_DB'])
    datastore.delete(b'test_key')
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
    datastore.delete(b'test_key')
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

    # TestCase: empty 'calculation_result' in request body
    with pytest.raises(RequiredItemNotExistError):
        validate_captcha_answer({
            'key': 'test_key',
            'calculation_result': ''
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


# def get_s3_bucket_list():
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_api.py::test_get_s3_bucket_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_s3_bucket_list(app, db, users, client, mocker):
    class FakeUser(UserMixin):
        def __init__(self, id):
            self.id = id
            self.name = "Test User"

        @property
        def is_authenticated(self):
            return False

    # Test case (Neg): not login
    # with pytest.raises(AuthenticationRequiredError):
    login_user_via_session(client, user=FakeUser(1))
    with pytest.raises(Exception):
        get_s3_bucket_list()

    # login for using currentuser (with no user profile)
    login(client, obj=users[0]["obj"])

    # Test case (Neg): no user profile
    with pytest.raises(Exception):
        get_s3_bucket_list()

    # Test case (Neg): client credentials info is incomplete
    mock_profile = mocker.Mock()
    mock_profile.client_credentials_configured = False
    mock_profile.create_s3_client = mocker.Mock()
    mocker.patch(
        "weko_user_profiles.models.UserProfile.get_by_userid",
        return_value=mock_profile
    )
    with pytest.raises(Exception):
        get_s3_bucket_list()

    # prepare user profile with complete client credentials info
    mock_profile.client_credentials_configured = True
    mock_boto3_client = mock_profile.create_s3_client()

    # Test case (Neg): s3 list_buckets error
    mock_boto3_client.list_buckets.side_effect = Exception("error")
    with pytest.raises(Exception):
        get_s3_bucket_list()

    # Test case (Pos): s3 list_buckets success (with buckets)
    mock_response_success = {
        "ResponseMetadata": {"HTTPStatusCode": 200},
        "Buckets": [
            {"Name": "bucket1"},
            {"Name": "bucket2"},
            {"Name": "bucket3"}
        ]
    }
    mock_boto3_client.list_buckets.side_effect = None
    mock_boto3_client.list_buckets.return_value = mock_response_success

    result_list = get_s3_bucket_list()
    assert result_list == ["bucket1", "bucket2", "bucket3"]

    # Test case (Pos): s3 list_buckets success (no buckets)
    mock_response_success_no_buckets = {
        "ResponseMetadata": {"HTTPStatusCode": 200}
    }
    mock_boto3_client.list_buckets.side_effect = None
    mock_boto3_client.list_buckets.return_value = mock_response_success_no_buckets
    result_list = get_s3_bucket_list()
    assert result_list == []

    # Test case (Neg): s3 list_buckets response error
    mock_response_error = {
        "ResponseMetadata": {"HTTPStatusCode": 500}
    }
    mock_boto3_client.list_buckets.side_effect = None
    mock_boto3_client.list_buckets.return_value = mock_response_error
    with pytest.raises(Exception):
        get_s3_bucket_list()


# def copy_bucket_to_s3(pid, filename, org_bucket_id, checked, bucket_name):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_api.py::test_copy_bucket_to_s3 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_copy_bucket_to_s3(
    app, db, users_storage_info, client, records, mocker
):
    # Prepare user profile with complete client credentials info
    pid = PersistentIdentifier.query.filter_by(
        pid_type="recid", pid_value='1'
    ).first()
    records_buckets = RecordsBuckets.query.filter_by(
        record_id=pid.object_uuid
    ).first()
    app.config.update({
        "FILES_REST_STORAGE_SERVICE_PATTERN": {
            "aws_s3": [
                r"^s3\.amazonaws\.com$",
                r"^s3\.(?P<region>.+)\.amazonaws\.com$",
                r"^(?P<bucket>.+)\.s3\.(?P<region>.+)\.amazonaws\.com$"
            ],
        }
    })

    # Get user profile
    user_profile_s3 = users_storage_info["s3_storage_user"] # S3 storage profile (Repository)
    s3_storage_user = user_profile_s3["user_info"]["obj"]
    s3_storage_user_profile = user_profile_s3["profile_obj"]
    s3_storage_region_name = s3_storage_user_profile.s3_region_name
    login(client, obj=s3_storage_user)

    # Mock UserProfile.create_s3_client to return mock boto3 client
    mock_profile_boto3_client = mocker.Mock()
    mocker.patch("weko_user_profiles.models.UserProfile.create_s3_client", return_value=mock_profile_boto3_client)
    mock_profile_boto3_client.meta.endpoint_url = s3_storage_user_profile.s3_endpoint_url
    mock_profile_boto3_client.upload_file.return_value = None
    mock_profile_boto3_client.get_bucket_location.return_value = {
        "LocationConstraint": s3_storage_user_profile.s3_region_name,
    }

    # Mock create_storage_bucket to return None
    mock_create_storage_bucket = mocker.patch("weko_records_ui.api.create_storage_bucket", return_value=None)

    # Test Case (Pos): local to s3 with create
    uri = copy_bucket_to_s3(
        pid=1, filename="helloworld.pdf",
        org_bucket_id=records_buckets.bucket_id,
        checked="create", bucket_name="sample1"
    )
    mock_create_storage_bucket.assert_called_once() # check create_storage_bucket called
    mock_profile_boto3_client.upload_file.assert_called_once() # check upload_file called
    assert uri == "https://s3.ap-southeast-2.amazonaws.com/sample1/helloworld.pdf"

    # Test Case (Pos): local to s3 with select
    mock_create_storage_bucket.reset_mock()
    mock_profile_boto3_client.upload_file.reset_mock()
    uri = copy_bucket_to_s3(
        pid=1, filename="helloworld.pdf",
        org_bucket_id=records_buckets.bucket_id,
        checked="select", bucket_name="sample1"
    )
    mock_create_storage_bucket.assert_not_called() # check create_storage_bucket not called
    mock_profile_boto3_client.upload_file.assert_called_once() # check upload_file called
    assert uri == "https://s3.ap-southeast-2.amazonaws.com/sample1/helloworld.pdf"

    # Test Case (Neg): create bucket error
    with pytest.raises(Exception):
        # bucket create error
        mock_create_storage_bucket.reset_mock()
        mock_create_storage_bucket.side_effect = Exception("error")
        copy_bucket_to_s3(
            pid=1, filename="helloworld.pdf",
            org_bucket_id=records_buckets.bucket_id,
            checked="create", bucket_name="sample1"
        )
    mock_create_storage_bucket.side_effect = None

    # Test Case (Neg): s3 upload error
    with pytest.raises(Exception):
        # upload file error
        mock_profile_boto3_client.upload_file.reset_mock()
        mock_profile_boto3_client.upload_file.side_effect = Exception("error")
        copy_bucket_to_s3(
            pid=1, filename="helloworld.pdf",
            org_bucket_id=records_buckets.bucket_id,
            checked="select", bucket_name="sample1"
        )
    mock_profile_boto3_client.upload_file.side_effect = None

    # Test Case (Neg): s3 get bucket location error
    with pytest.raises(Exception):
        # get bucket location error
        mock_profile_boto3_client.get_bucket_location.side_effect = Exception("error")
        copy_bucket_to_s3(
            pid=1, filename="helloworld.pdf",
            org_bucket_id=records_buckets.bucket_id,
            checked="select", bucket_name="sample1"
        )
    # Reset side effect
    mock_profile_boto3_client.get_bucket_location.side_effect = None

    # Test Case (Neg): profile not exists
    with patch("weko_user_profiles.models.UserProfile.get_by_userid", return_value=None):
        # no profile
        with pytest.raises(Exception):
                copy_bucket_to_s3(
                    pid=1, filename="helloworld.pdf",
                    org_bucket_id=records_buckets.bucket_id,
                    checked="create", bucket_name="sample1"
                )

    # Test Case (Neg): profile exists but no s3 setting
    mock_user_profile = mocker.Mock()
    mock_user_profile.client_credentials_configured = False
    with patch("weko_user_profiles.models.UserProfile.get_by_userid", return_value=mock_user_profile):
        # no s3 setting
        with pytest.raises(Exception):
            copy_bucket_to_s3(
                pid=1, filename="helloworld.pdf",
                org_bucket_id=records_buckets.bucket_id,
                checked="create", bucket_name="sample1"
            )

    mocker_boto3_client_src = mocker.Mock()
    mocker_boto3_client_src.head_object.return_value = True
    mocker_boto3_client_src.copy.return_value = None
    mocker_boto3_client_src.meta.endpoint_url = "https://s3.us-west-2.amazonaws.com"

    # Prepare s3 storage file instance
    mock_file_instance_s3 = mocker.Mock()
    mock_file_instance_s3.uri = "s3://bucket-name/helloworld.pdf"

    # Test Case (Pos): source_location is None
    loc_s3_vh = Location(
        name="testloc-s3-vh-path",
        uri="https://s3.us-west-2.amazonaws.com/bucket-name/",
        default=False,
        type="s3_vh",
        access_key="access_key",
        secret_key="secret_key",
        s3_region_name="us-west-2",
    )
    with patch("invenio_files_rest.models.FileInstance.get", return_value=mock_file_instance_s3):
        mocker.patch.object(loc_s3_vh, "create_s3_client", return_value=mocker_boto3_client_src)
        uri = copy_bucket_to_s3(
            pid=1, filename="helloworld.pdf",
            org_bucket_id=records_buckets.bucket_id,
            checked="create", bucket_name="sample1"
        )
        assert uri == f"https://s3.{s3_storage_region_name}.amazonaws.com/sample1/helloworld.pdf"
        mock_profile_boto3_client.copy.assert_not_called()
        mock_profile_boto3_client.copy.reset_mock()

    # Test Case (Pos): storage s3 to s3 (path style)
    mock_get_default = mocker.patch("invenio_files_rest.models.Location.get_default")
    loc_s3 = Location(
        name="testloc-s3",
        uri="s3://bucket-name/",
        default=False,
        type="s3",
        s3_endpoint_url="https://s3.us-west-2.amazonaws.com/",
        access_key="access_key",
        secret_key="secret_key",
        s3_region_name="us-west-2",
    )
    mock_get_default.return_value = loc_s3
    with patch("invenio_files_rest.models.FileInstance.get", return_value=mock_file_instance_s3):
        mocker.patch.object(loc_s3, "create_s3_client", return_value=mocker_boto3_client_src)
        uri = copy_bucket_to_s3(
            pid=1, filename="helloworld.pdf",
            org_bucket_id=records_buckets.bucket_id,
            checked="create", bucket_name="sample1"
        )
        assert uri == f"https://s3.{s3_storage_region_name}.amazonaws.com/sample1/helloworld.pdf"
        mock_profile_boto3_client.copy.assert_called_once()
        mock_profile_boto3_client.copy.reset_mock()

    # Test Case (Pos): s3 to s3 (virtual host style)
    loc_s3_vh = Location(
        name="testloc-s3-vh",
        uri="https://bucket-name.s3.us-west-2.amazonaws.com/",
        default=False,
        type="s3_vh",
        access_key="access_key",
        secret_key="secret_key",
        s3_region_name="us-west-2",
    )
    mock_get_default.return_value = loc_s3_vh
    with patch("invenio_files_rest.models.FileInstance.get", return_value=mock_file_instance_s3):
        mocker.patch.object(loc_s3_vh, "create_s3_client", return_value=mocker_boto3_client_src)
        uri = copy_bucket_to_s3(
            pid=1, filename="helloworld.pdf",
            org_bucket_id=records_buckets.bucket_id,
            checked="create", bucket_name="sample1"
        )
        assert uri == f"https://s3.{s3_storage_region_name}.amazonaws.com/sample1/helloworld.pdf"
        mock_profile_boto3_client.copy.assert_called_once()
        mock_profile_boto3_client.copy.reset_mock()

    # Test Case (Pos): s3 to s3 (virtual host style, path style uri)
    loc_s3_vh = Location(
        name="testloc-s3-vh-path",
        uri="https://s3.us-west-2.amazonaws.com/bucket-name/",
        default=False,
        type="s3_vh",
        access_key="access_key",
        secret_key="secret_key",
        s3_region_name="us-west-2",
    )
    mock_get_default.return_value = loc_s3_vh
    with patch("invenio_files_rest.models.FileInstance.get", return_value=mock_file_instance_s3):
        mocker.patch.object(loc_s3_vh, "create_s3_client", return_value=mocker_boto3_client_src)
        uri = copy_bucket_to_s3(
            pid=1, filename="helloworld.pdf",
            org_bucket_id=records_buckets.bucket_id,
            checked="create", bucket_name="sample1"
        )
        assert uri == f"https://s3.{s3_storage_region_name}.amazonaws.com/sample1/helloworld.pdf"
        mock_profile_boto3_client.copy.assert_called_once()
        mock_profile_boto3_client.copy.reset_mock()

    # Test Case (Pos): bucket_region is None
    mock_get_default.return_value = loc_s3_vh
    mock_profile_boto3_client.get_bucket_location.return_value = {
        "LocationConstraint": None
    }
    with patch("invenio_files_rest.models.FileInstance.get", return_value=mock_file_instance_s3):
        mocker.patch.object(loc_s3_vh, "create_s3_client", return_value=mocker_boto3_client_src)
        uri = copy_bucket_to_s3(
            pid=1, filename="helloworld.pdf",
            org_bucket_id=records_buckets.bucket_id,
            checked="create", bucket_name="sample1"
        )
        assert uri == f"https://s3.{s3_storage_region_name}.amazonaws.com/sample1/helloworld.pdf"
        mock_profile_boto3_client.copy.assert_called_once()
        mock_profile_boto3_client.copy.reset_mock()
    mock_profile_boto3_client.get_bucket_location.return_value = {
        "LocationConstraint": s3_storage_user_profile.s3_region_name
    }

    # Test Case (Pos): can_use_virtual_hosted_style
    mock_profile_boto3_client.meta.endpoint_url = "https://s3.ap-southeast-2.amazonaws.com"
    with patch("invenio_files_rest.models.FileInstance.get", return_value=mock_file_instance_s3):
        mocker.patch.object(loc_s3_vh, "create_s3_client", return_value=mocker_boto3_client_src)
        uri = copy_bucket_to_s3(
            pid=1, filename="helloworld.pdf",
            org_bucket_id=records_buckets.bucket_id,
            checked="create", bucket_name="sample1"
        )
        assert uri == f"https://sample1.s3.{s3_storage_region_name}.amazonaws.com/helloworld.pdf"
        mock_profile_boto3_client.copy.assert_called_once()
        mock_profile_boto3_client.copy.reset_mock()
    mock_profile_boto3_client.meta.endpoint_url = s3_storage_user_profile.s3_endpoint_url

    # Test Case (Pos): netloc startswith "s3."
    mock_file_instance_s3.uri = "https://s3.ap-southeast-2.amazonaws.com/bucket_name/file_name"
    with patch("invenio_files_rest.models.FileInstance.get", return_value=mock_file_instance_s3):
        mocker.patch.object(loc_s3_vh, "create_s3_client", return_value=mocker_boto3_client_src)
        uri = copy_bucket_to_s3(
            pid=1, filename="helloworld.pdf",
            org_bucket_id=records_buckets.bucket_id,
            checked="create", bucket_name="sample1"
        )
        assert uri == f"https://s3.{s3_storage_region_name}.amazonaws.com/sample1/helloworld.pdf"
        mock_profile_boto3_client.copy.assert_called_once()
        mock_profile_boto3_client.copy.reset_mock()
    mock_file_instance_s3.uri = "s3://bucket-name/helloworld.pdf"

    # Test Case (Neg): location type is other
    loc_s3_other = Location(
        name="testloc-s3-vh",
        uri="https://bucket-name.s3.us-west-2.amazonaws.com/",
        default=False,
        type="s3_other",
        access_key="access_key",
        secret_key="secret_key",
        s3_region_name="us-west-2",
    )
    mock_get_default.return_value = loc_s3_other
    with patch("invenio_files_rest.models.FileInstance.get", return_value=mock_file_instance_s3):
        mocker.patch.object(loc_s3_vh, "create_s3_client", return_value=mocker_boto3_client_src)
        with pytest.raises(Exception) as e:
            uri = copy_bucket_to_s3(
                pid=1, filename="helloworld.pdf",
                org_bucket_id=records_buckets.bucket_id,
                checked="create", bucket_name="sample1"
            )
        assert "The source bucket or file key is not set." in str(e.value)
        mock_profile_boto3_client.copy.reset_mock()

    # Test Case (Neg): s3 to s3, head object not found
    mock_get_default.return_value = loc_s3
    mocker_boto3_client_src.head_object.side_effect = Exception("Not found")
    with patch("invenio_files_rest.models.FileInstance.get", return_value=mock_file_instance_s3):
        mocker.patch.object(loc_s3, "create_s3_client", return_value=mocker_boto3_client_src)
        with pytest.raises(Exception):
            copy_bucket_to_s3(
                pid=1, filename="helloworld.pdf",
                org_bucket_id=records_buckets.bucket_id,
                checked="create", bucket_name="sample1"
            )
    mocker_boto3_client_src.head_object.side_effect = None

    # Test Case (Neg): s3 to s3, head object not found
    mock_get_default.return_value = loc_s3
    mocker_boto3_client_src.head_object.return_value = True
    mock_profile_boto3_client.copy.side_effect = Exception("Copy error")
    with patch("invenio_files_rest.models.FileInstance.get", return_value=mock_file_instance_s3):
        mocker.patch.object(loc_s3, "create_s3_client", return_value=mocker_boto3_client_src)
        with pytest.raises(Exception):
            copy_bucket_to_s3(
                pid=1, filename="helloworld.pdf",
                org_bucket_id=records_buckets.bucket_id,
                checked="create", bucket_name="sample1"
            )

    # Test Case: region setting exists
    with db.session.begin_nested():
        p3 = UserProfile()
        p3.user_id = '3'
        p3.access_key = '3'
        p3.secret_key = '3'
        p3.s3_endpoint_url = 'https://s3.us-west-2.amazonaws.com/'
        p3.s3_region_name = 'us-west-2'
        db.session.add(p3)

        user_profile3 = p3

        with patch("weko_user_profiles.models.UserProfile.get_by_userid", return_value=user_profile3):
            with patch('boto3.client') as mock_client:
                instance = mock_client.return_value
                instance.create_bucket.return_value = {}
                instance.get_bucket_location.return_value = {}
                instance.upload_file.return_value = {}

                pid = PersistentIdentifier.query.filter_by(
                    pid_type="recid", pid_value='1'
                ).first()
                records_buckets = RecordsBuckets.query.filter_by(
                    record_id=pid.object_uuid).first()

                uri = copy_bucket_to_s3(pid=1, filename='helloworld.pdf',
                                        org_bucket_id=records_buckets.bucket_id,
                                        checked='create', bucket_name='sample1')
                assert uri


# def copy_bucket_to_s3(pid, filename, org_bucket_id, checked, bucket_name):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_api.py::test_copy_bucket_to_s3_cross_service -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_copy_bucket_to_s3_cross_service(
    app, db, users_storage_info, client, records, mocker
):
    # Prepare user profile with complete client credentials info
    pid = PersistentIdentifier.query.filter_by(
        pid_type="recid", pid_value='1'
    ).first()
    records_buckets = RecordsBuckets.query.filter_by(
        record_id=pid.object_uuid
    ).first()
    app.config.update({
        "FILES_REST_STORAGE_SERVICE_PATTERN": {
            "aws_s3": [
                r"^s3\.amazonaws\.com$",
                r"^s3\.(?P<region>.+)\.amazonaws\.com$",
                r"^(?P<bucket>.+)\.s3\.(?P<region>.+)\.amazonaws\.com$"
            ],
            "other_s3": [
                r"^s3\.custom\.endpoint\.com$",
                r"^s3\.(?P<region>.+)\.custom\.endpoint\.com$",
                r"^(?P<bucket>.+)\.s3\.(?P<region>.+)\.custom\.endpoint\.com$"
            ]
        }
    })

    # Get user profile
    user_profile_s3 = users_storage_info["not_s3_storage_user"] # Other S3 storage profile (Repository)
    non_s3_storage_user = user_profile_s3["user_info"]["obj"]
    non_s3_storage_user_profile = user_profile_s3["profile_obj"]
    non_s3_storage_region_name = non_s3_storage_user_profile.s3_region_name
    login(client, obj=non_s3_storage_user)

    # Mock UserProfile.create_s3_client to return mock boto3 client
    mock_profile_boto3_client = mocker.Mock()
    mocker.patch("weko_user_profiles.models.UserProfile.create_s3_client", return_value=mock_profile_boto3_client)
    mock_profile_boto3_client.meta.endpoint_url = non_s3_storage_user_profile.s3_endpoint_url
    mock_profile_boto3_client.upload_file.return_value = None
    mock_profile_boto3_client.get_bucket_location.return_value = {
        "LocationConstraint": non_s3_storage_user_profile.s3_region_name,
    }
    mock_profile_boto3_client.upload_fileobj.return_value = None

    mocker_boto3_client_src = mocker.Mock()
    mocker_boto3_client_src.head_object.return_value = True
    mocker_boto3_client_src.copy.return_value = None
    mocker_boto3_client_src.meta.endpoint_url = "https://s3.us-west-2.amazonaws.com"
    mocker_boto3_client_src.get_object.return_value = {"Body": mocker.Mock()}

    # Prepare s3 storage file instance
    mock_file_instance_s3 = mocker.Mock()
    mock_file_instance_s3.uri = "s3://bucket-name/helloworld.pdf"
    mock_file_instance_s3.size = 1234

    mock_get_default = mocker.patch("invenio_files_rest.models.Location.get_default", return_value=non_s3_storage_user_profile)

    # Test Case (Pos): storage s3 to other s3 (path style)
    loc_s3 = Location(
        name="testloc-s3",
        uri="s3://bucket-name/",
        default=False,
        type="s3",
        s3_endpoint_url="https://s3.us-west-2.amazonaws.com/",
        access_key="access_key",
        secret_key="secret_key",
        s3_region_name="us-west-2",
    )
    mock_get_default.return_value = loc_s3
    with patch("invenio_files_rest.models.FileInstance.get", return_value=mock_file_instance_s3):
        mocker.patch.object(loc_s3, "create_s3_client", return_value=mocker_boto3_client_src)
        uri = copy_bucket_to_s3(
            pid=1, filename="helloworld.pdf",
            org_bucket_id=records_buckets.bucket_id,
            checked="select", bucket_name="sample1"
        )
        assert uri == non_s3_storage_user_profile.s3_endpoint_url + "sample1/helloworld.pdf"
        mock_profile_boto3_client.copy.assert_not_called()
        mock_profile_boto3_client.upload_fileobj.assert_called_once()
        mock_profile_boto3_client.upload_fileobj.reset_mock()

    mock_create_storage_bucket = mocker.patch("weko_records_ui.api.create_storage_bucket", return_value=None)

    # Test Case (Pos): s3 to other s3 (virtual host style)
    loc_s3_vh = Location(
        name="testloc-s3-vh",
        uri="https://bucket-name.s3.us-west-2.amazonaws.com/",
        default=False,
        type="s3_vh",
        access_key="access_key",
        secret_key="secret_key",
        s3_region_name="us-west-2",
    )
    mock_get_default.return_value = loc_s3_vh
    with patch("invenio_files_rest.models.FileInstance.get", return_value=mock_file_instance_s3):
        mocker.patch.object(loc_s3_vh, "create_s3_client", return_value=mocker_boto3_client_src)
        uri = copy_bucket_to_s3(
            pid=1, filename="helloworld.pdf",
            org_bucket_id=records_buckets.bucket_id,
            checked="create", bucket_name="sample1"
        )
        assert uri == non_s3_storage_user_profile.s3_endpoint_url + "sample1/helloworld.pdf"
        mock_create_storage_bucket.assert_called_once()
        mock_profile_boto3_client.upload_fileobj.assert_called_once()
        mock_profile_boto3_client.upload_fileobj.reset_mock()

    # Test Case (Pos): s3 to other s3 (virtual host style, path style uri)
    loc_s3_vh = Location(
        name="testloc-s3-vh-path",
        uri="https://s3.us-west-2.amazonaws.com/bucket-name/",
        default=False,
        type="s3_vh",
        access_key="access_key",
        secret_key="secret_key",
        s3_region_name="us-west-2",
    )
    mock_get_default.return_value = loc_s3_vh
    with patch("invenio_files_rest.models.FileInstance.get", return_value=mock_file_instance_s3):
        mocker.patch.object(loc_s3_vh, "create_s3_client", return_value=mocker_boto3_client_src)
        uri = copy_bucket_to_s3(
            pid=1, filename="helloworld.pdf",
            org_bucket_id=records_buckets.bucket_id,
            checked="create", bucket_name="sample1"
        )
        assert uri == non_s3_storage_user_profile.s3_endpoint_url + "sample1/helloworld.pdf"
        mock_profile_boto3_client.upload_fileobj.assert_called_once()
        mock_profile_boto3_client.upload_fileobj.reset_mock()

    # Test Case (Neg): uploading file ClientError
    loc_s3_vh = Location(
        name="testloc-s3-vh-path",
        uri="https://s3.us-west-2.amazonaws.com/bucket-name/",
        default=False,
        type="s3_vh",
        access_key="access_key",
        secret_key="secret_key",
        s3_region_name="us-west-2",
    )
    mock_get_default.return_value = loc_s3_vh
    with patch("invenio_files_rest.models.FileInstance.get", return_value=mock_file_instance_s3):
        mocker.patch.object(loc_s3_vh, "create_s3_client", return_value=mocker_boto3_client_src)
        mock_profile_boto3_client.upload_fileobj.side_effect = ClientError(
            error_response={"Error": {"Code": "403", "Message": "Forbidden"}},
            operation_name="UploadFileObj"
        )
        with pytest.raises(Exception) as e:
            uri = copy_bucket_to_s3(
                pid=1, filename="helloworld.pdf",
                org_bucket_id=records_buckets.bucket_id,
                checked="create", bucket_name="sample1"
            )
        assert "Uploading file failed. Please make sure you have write permissions or that the bucket is writable." == str(e.value)
        mock_profile_boto3_client.upload_fileobj.reset_mock()
        mock_profile_boto3_client.upload_fileobj.side_effect = None

    # Test Case (Neg): file size is too large
    loc_s3_vh = Location(
        name="testloc-s3-vh-path",
        uri="https://s3.us-west-2.amazonaws.com/bucket-name/",
        default=False,
        type="s3_vh",
        access_key="access_key",
        secret_key="secret_key",
        s3_region_name="us-west-2",
    )
    mock_get_default.return_value = loc_s3_vh
    mock_file_instance_s3.size = 20 * 1024 * 1024 * 1024 + 1
    with patch("invenio_files_rest.models.FileInstance.get", return_value=mock_file_instance_s3):
        mocker.patch.object(loc_s3_vh, "create_s3_client", return_value=mocker_boto3_client_src)
        with pytest.raises(Exception) as e:
            uri = copy_bucket_to_s3(
                pid=1, filename="helloworld.pdf",
                org_bucket_id=records_buckets.bucket_id,
                checked="create", bucket_name="sample1"
            )
        assert "The source file size exceeds the limit for cross-service copy." == str(e.value)
        mock_profile_boto3_client.upload_fileobj.reset_mock()

    # Test Case (Pos): WEKO_RECORDS_UI_S3_CROSS_COPY_MAX_FILE_SIZE is bigger than config value
    app.config["WEKO_RECORDS_UI_S3_CROSS_COPY_MAX_FILE_SIZE"] = 40 * 1024 * 1024 * 1024  # 40 GB
    with patch("invenio_files_rest.models.FileInstance.get", return_value=mock_file_instance_s3):
        mocker.patch.object(loc_s3_vh, "create_s3_client", return_value=mocker_boto3_client_src)
        uri = copy_bucket_to_s3(
            pid=1, filename="helloworld.pdf",
            org_bucket_id=records_buckets.bucket_id,
            checked="create", bucket_name="sample1"
        )
        assert uri == non_s3_storage_user_profile.s3_endpoint_url + "sample1/helloworld.pdf"
        mock_profile_boto3_client.upload_fileobj.assert_called_once()
        mock_profile_boto3_client.upload_fileobj.reset_mock()


# def create_storage_bucket(s3_client, endpoint_url, region_name, bucket_name):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_api.py::test_create_storage_bucket_bucket_exists -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_create_storage_bucket_bucket_exists(mocker):
    mock_s3_client = mocker.Mock()
    # Simulate bucket exists
    mocker.patch("weko_records_ui.api.bucket_exists", return_value=True)
    with pytest.raises(Exception) as excinfo:
        create_storage_bucket(mock_s3_client, "https://s3.amazonaws.com", "us-east-1", "test-bucket")
    assert "Bucket already exists" in str(excinfo.value)


# def create_storage_bucket(s3_client, endpoint_url, region_name, bucket_name):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_api.py::test_create_storage_bucket_success_default_region -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_create_storage_bucket_success_default_region(mocker):
    mock_s3_client = mocker.Mock()
    # Simulate bucket does not exist
    mocker.patch("weko_records_ui.api.bucket_exists", return_value=False)
    mock_s3_client.meta.region_name = "us-east-1"
    # Patch methods
    mock_s3_client.create_bucket = mocker.Mock()
    mock_s3_client.put_public_access_block = mocker.Mock()
    mock_s3_client.put_bucket_policy = mocker.Mock()

    # Should not raise
    create_storage_bucket(mock_s3_client, "https://s3.amazonaws.com", None, "test-bucket")
    mock_s3_client.create_bucket.assert_called_once_with(Bucket="test-bucket")
    mock_s3_client.put_public_access_block.assert_called_once_with(
        Bucket="test-bucket",
        PublicAccessBlockConfiguration={
            'BlockPublicAcls': False,
            'IgnorePublicAcls': False,
            'BlockPublicPolicy': False,
            'RestrictPublicBuckets': False
        })
    mock_s3_client.put_bucket_policy.assert_called_once_with(
        Bucket="test-bucket",
        Policy=json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "Public",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": ["s3:*"],
                    "Resource": "arn:aws:s3:::test-bucket/*"
                }
            ]
        })
    )


# def create_storage_bucket(s3_client, endpoint_url, region_name, bucket_name):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_api.py::test_create_storage_bucket_success_non_default_region -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_create_storage_bucket_success_non_default_region(mocker):
    mock_s3_client = mocker.Mock()
    mocker.patch("weko_records_ui.api.bucket_exists", return_value=False)
    mock_s3_client.meta.region_name = "ap-northeast-1"
    mock_s3_client.create_bucket = mocker.Mock()
    mock_s3_client.put_public_access_block = mocker.Mock()
    mock_s3_client.put_bucket_policy = mocker.Mock()
    create_storage_bucket(mock_s3_client, "https://s3.amazonaws.com", "ap-northeast-1", "test-bucket")
    mock_s3_client.create_bucket.assert_called_once_with(
        Bucket="test-bucket",
        CreateBucketConfiguration={'LocationConstraint': "ap-northeast-1"}
    )
    mock_s3_client.put_public_access_block.assert_called_once()
    mock_s3_client.put_bucket_policy.assert_called_once()


# def create_storage_bucket(s3_client, endpoint_url, region_name, bucket_name):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_api.py::test_create_storage_bucket_success_non_aws_endpoint -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_create_storage_bucket_success_non_aws_endpoint(mocker):
    mock_s3_client = mocker.Mock()
    mocker.patch("weko_records_ui.api.bucket_exists", return_value=False)
    mock_s3_client.meta.region_name = "us-east-1"
    mock_s3_client.create_bucket = mocker.Mock()
    mock_s3_client.put_public_access_block = mocker.Mock()
    mock_s3_client.put_bucket_policy = mocker.Mock()
    # Non-AWS endpoint
    create_storage_bucket(mock_s3_client, "https://custom.endpoint.com", "us-east-1", "test-bucket")
    mock_s3_client.create_bucket.assert_called_once_with(Bucket="test-bucket")
    mock_s3_client.put_public_access_block.assert_not_called()
    mock_s3_client.put_bucket_policy.assert_called_once()


# def create_storage_bucket(s3_client, endpoint_url, region_name, bucket_name):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_api.py::test_create_storage_bucket_create_bucket_exception -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_create_storage_bucket_create_bucket_exception(app, mocker):
    mock_s3_client = mocker.Mock()
    mocker.patch("weko_records_ui.api.bucket_exists", return_value=False)
    mock_s3_client.meta.region_name = "us-east-1"
    mock_s3_client.create_bucket.side_effect = Exception("fail")
    mock_s3_client.put_public_access_block = mocker.Mock()
    mock_s3_client.put_bucket_policy = mocker.Mock()
    with app.test_request_context():
        with pytest.raises(Exception) as excinfo:
            create_storage_bucket(mock_s3_client, "https://s3.amazonaws.com", None, "test-bucket")
        assert "Creating Bucket failed" in str(excinfo.value)


# def bucket_exists(s3_client, bucket_name):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_api.py::test_bucket_exists -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_bucket_exists(mocker):
    # Test case (Pos): Test bucket_exists when the bucket exists.
    # Mock the S3 client
    mock_s3_client = mocker.Mock()
    mock_s3_client.head_bucket = mocker.Mock(return_value=None)  # No exception means bucket exists

    # Call the function
    result = bucket_exists(mock_s3_client, "test-bucket")

    # Assertions
    mock_s3_client.head_bucket.assert_called_once_with(Bucket="test-bucket")
    assert result is True

    # Test case (Neg): Test bucket_exists when the bucket does not exist.
    # Mock the S3 client
    mock_s3_client = mocker.Mock()
    mock_s3_client.head_bucket = mocker.Mock(side_effect=Exception("Bucket does not exist"))
    # Call the function
    result = bucket_exists(mock_s3_client, "test-bucket")

    # Assertions
    mock_s3_client.head_bucket.assert_called_once_with(Bucket="test-bucket")
    assert result is False


# def get_file_place_info(org_pid, org_bucket_id, file_name):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_api.py::test_get_file_place_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_file_place_info(app, db, users, client, records, mocker):
    # Get pid and records_buckets
    pid = PersistentIdentifier.query.filter_by(
        pid_type="recid", pid_value='1'
    ).first()
    records_buckets = RecordsBuckets.query.filter_by(
        record_id=pid.object_uuid).first()

    # Test case (Neg): item has been locked
    with patch("weko_records_ui.api.handle_check_item_is_locked") as mock_handle_check_item_is_locked:
        mock_handle_check_item_is_locked.side_effect = Exception("item is locked")
        with pytest.raises(Exception):
            get_file_place_info(
                org_pid=1,
                org_bucket_id=records_buckets.bucket_id,
                file_name="helloworld.pdf"
            )

    mock_response = "http:return_url"
    mock_boto3_s3_client = mocker.patch("weko_records_ui.api.Location.create_s3_client")
    mock_generate_presigned_url = mocker.MagicMock()
    mock_boto3_s3_client.return_value = mock_generate_presigned_url
    mock_generate_presigned_url.generate_presigned_url = \
        MagicMock(return_value=mock_response)

    with db.session.begin_nested():
        # Test case (Pos): location type: local (location from fileinstance uri)
        actual = get_file_place_info(
            org_pid=1,
            org_bucket_id=records_buckets.bucket_id,
            file_name="helloworld.pdf"
        )
        assert actual[0] == "local" # file_place
        assert actual[1] is None # url
        assert actual[2] is None # new_bucket_id
        assert actual[3] is None # new_version_id

        # Test case (Pos): location type: local (location from workflow)
        with patch("weko_workflow.api.WorkActivity") as mock_cls_workactivity, \
            patch("weko_records_ui.api.Location") as mock_cls_location:
            mock_instance_workactivity = mock_cls_workactivity.return_value
            mock_activity = MagicMock()
            mock_activity.workflow_id = 2
            mock_instance_workactivity.get_workflow_activity_by_item_id = \
                MagicMock(return_value=mock_activity)

            mock_cls_workflow = mocker.patch("weko_records_ui.api.WorkFlow")
            mock_instance_workflow = mock_cls_workflow.return_value
            mock_workflow = MagicMock()
            mock_workflow.location_id = 3
            mock_instance_workflow.get_workflow_by_id = \
                MagicMock(return_value=mock_workflow)

            mock_location = Location()
            mock_location.uri="file://test/"
            mock_location.type=None
            mock_cls_location.query.get.return_value = mock_location

            actual = get_file_place_info(
                org_pid=1,
                org_bucket_id=records_buckets.bucket_id,
                file_name='helloworld.pdf'
            )
            mock_cls_workactivity.assert_called_once()
            mock_instance_workactivity.get_workflow_activity_by_item_id.assert_called_once()
            mock_cls_workflow.assert_called_once()
            mock_instance_workflow.get_workflow_by_id.assert_called_once_with(workflow_id=2)
            mock_cls_location.query.get.assert_called_once_with(3)
            assert actual[0] == "local" # file_place
            assert actual[1] is None # url
            assert actual[2] is None # new_bucket_id
            assert actual[3] is None # new_version_id

        # Test Case (Pos): location type: s3 (location from default location)
        with patch("weko_workflow.api.WorkActivity") as mock_cls_workactivity:
            mock_instance_workactivity = mock_cls_workactivity.return_value
            mock_activity = MagicMock()
            mock_activity.workflow_id = 2
            mock_instance_workactivity.get_workflow_activity_by_item_id = \
                MagicMock(return_value=mock_activity)

            mock_cls_workflow = mocker.patch("weko_records_ui.api.WorkFlow")
            mock_instance_workflow = mock_cls_workflow.return_value
            mock_workflow = MagicMock()
            mock_workflow.location_id = None # workflow has no location_id
            mock_instance_workflow.get_workflow_by_id = \
                MagicMock(return_value=mock_workflow)

            actual = get_file_place_info(
                org_pid=1,
                org_bucket_id=records_buckets.bucket_id,
                file_name='helloworld.pdf'
            )
            mock_cls_workactivity.assert_called_once()
            mock_instance_workactivity.get_workflow_activity_by_item_id.assert_called_once()
            mock_cls_workflow.assert_called_once()
            mock_instance_workflow.get_workflow_by_id.assert_called_once_with(workflow_id=2)
            assert actual[0] == "local" # file_place
            assert actual[1] is None # url
            assert actual[2] is None # new_bucket_id
            assert actual[3] is None # new_version_id

        # Test case (Pos): location type: s3 (location from fileinstance uri)
        # Test case (Pos): location type: local (location from workflow)
        with patch("weko_workflow.api.WorkActivity") as mock_cls_workactivity, \
            patch("weko_records_ui.api.Location") as mock_cls_location:
            mock_instance_workactivity = mock_cls_workactivity.return_value
            mock_activity = MagicMock()
            mock_activity.workflow_id = 2
            mock_instance_workactivity.get_workflow_activity_by_item_id = \
                MagicMock(return_value=mock_activity)

            mock_cls_workflow = mocker.patch("weko_records_ui.api.WorkFlow")
            mock_instance_workflow = mock_cls_workflow.return_value
            mock_workflow = MagicMock()
            mock_workflow.location_id = 3
            mock_instance_workflow.get_workflow_by_id = \
                MagicMock(return_value=mock_workflow)

            # ex: s3://bucket_name/file_name
            mock_location = Location()
            mock_location.id = 1
            mock_location.uri="s3://test/"
            mock_location.access_key="access_key"
            mock_location.secret_key="secret_key"
            mock_location.type="s3"
            mock_location.s3_endpoint_url="https://test.s3.ap-southeast-2.amazonaws.com/"
            mock_cls_location.query.get.return_value = mock_location

            with patch('weko_records_ui.api.FileInstance.get') as mock_file_instance:
                file_instance = FileInstance.create()
                file_instance.uri = "s3://test"
                mock_file_instance.return_value = file_instance
                actual = get_file_place_info(
                    org_pid=1,
                    org_bucket_id=records_buckets.bucket_id,
                    file_name='helloworld.pdf'
                )
                mock_cls_workactivity.assert_called_once()
                mock_instance_workactivity.get_workflow_activity_by_item_id.assert_called_once()
                mock_cls_workflow.assert_called_once()
                mock_instance_workflow.get_workflow_by_id.assert_called_once_with(workflow_id=2)
                mock_cls_location.query.get.assert_called_once_with(3)

                pid = PersistentIdentifier.query.filter_by(
                    pid_type="recid", pid_value='1'
                ).first()
                records_buckets = RecordsBuckets.query.filter_by(
                    record_id=pid.object_uuid).first()
                assert actual[0] == 'S3' # file_place
                assert actual[1] == mock_response # url
                assert actual[2] is not None # new_bucket_id
                assert actual[3] is not None # new_version_id

                # Test case (Pos): location type = s3_vh
                mock_cls_workactivity.reset_mock()
                mock_instance_workactivity.get_workflow_activity_by_item_id.reset_mock()
                mock_cls_workflow.reset_mock()
                mock_instance_workflow.reset_mock()
                mock_cls_location.reset_mock()

                mock_location.type="s3_vh"
                mock_location.s3_endpoint_url="https://bucket_name.s3.us-east-1.amazonaws.com/"
                mock_cls_location.query.get.return_value = mock_location

                file_instance.uri = "https://bucket_name.s3.us-east-1.amazonaws.com"
                mock_file_instance.return_value = file_instance
                actual = get_file_place_info(
                    org_pid=1,
                    org_bucket_id=records_buckets.bucket_id,
                    file_name='helloworld.pdf'
                )
                mock_cls_workactivity.assert_called_once()
                mock_instance_workactivity.get_workflow_activity_by_item_id.assert_called_once()
                mock_cls_workflow.assert_called_once()
                mock_instance_workflow.get_workflow_by_id.assert_called_once_with(workflow_id=2)
                mock_cls_location.query.get.assert_called_once_with(3)

                pid = PersistentIdentifier.query.filter_by(
                    pid_type="recid", pid_value='1'
                ).first()
                records_buckets = RecordsBuckets.query.filter_by(
                    record_id=pid.object_uuid).first()
                assert actual[0] == 'S3' # file_place
                assert actual[1] == mock_response # url
                assert actual[2] is not None # new_bucket_id
                assert actual[3] is not None # new_version_id

                # Test case (Pos): location type = s3_path
                mock_cls_workactivity.reset_mock()
                mock_instance_workactivity.get_workflow_activity_by_item_id.reset_mock()
                mock_cls_workflow.reset_mock()
                mock_instance_workflow.reset_mock()
                mock_cls_location.reset_mock()

                mock_location.type="s3_path"
                mock_location.s3_endpoint_url="https://s3.ap-southeast-2.amazonaws.com/test/"
                mock_cls_location.query.get.return_value = mock_location

                file_instance.uri = "https://s3.ap-southeast-2.amazonaws.com/test/a/b/c/d/e/f"
                mock_file_instance.return_value = file_instance

                actual = get_file_place_info(
                    org_pid=1,
                    org_bucket_id=records_buckets.bucket_id,
                    file_name='helloworld.pdf'
                )
                mock_cls_workactivity.assert_called_once()
                mock_instance_workactivity.get_workflow_activity_by_item_id.assert_called_once()
                mock_cls_workflow.assert_called_once()
                mock_instance_workflow.get_workflow_by_id.assert_called_once_with(workflow_id=2)
                mock_cls_location.query.get.assert_called_once_with(3)

                pid = PersistentIdentifier.query.filter_by(
                    pid_type="recid", pid_value='1'
                ).first()
                records_buckets = RecordsBuckets.query.filter_by(
                    record_id=pid.object_uuid).first()
                assert actual[0] == 'S3' # file_place
                assert actual[1] == mock_response # url
                assert actual[2] is not None # new_bucket_id
                assert actual[3] is not None # new_version_id

                # Test Case (Neg): error in generating url
                mock_generate_presigned_url.generate_presigned_url.side_effect \
                    = Exception("error")
                with pytest.raises(Exception) as e:
                    actual = get_file_place_info(
                        org_pid=1,
                        org_bucket_id=records_buckets.bucket_id,
                        file_name='helloworld.pdf'
                    )
                assert "Unexpected error occurred." in str(e.value)

                # Test Case (Neg): without bucket name
                file_instance.uri = "https://s3.ap-southeast-2.amazonaws.com"
                mock_file_instance.return_value = file_instance
                with pytest.raises(Exception) as e:
                    actual = get_file_place_info(
                        org_pid=1,
                        org_bucket_id=records_buckets.bucket_id,
                        file_name='helloworld.pdf'
                    )
                assert "The file cannot be found." in str(e.value)


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_api.py::test_replace_file_bucket -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_replace_file_bucket_local(app, db, users, client, records):

    pid = PersistentIdentifier.query.filter_by(
        pid_type="recid", pid_value='1'
    ).first()
    records_buckets = RecordsBuckets.query.filter_by(
        record_id=pid.object_uuid).first()
    file_obj = ObjectVersion.get(bucket=records_buckets.bucket_id, key='helloworld.pdf')

    # テスト用のデータを用意
    test_data = b'Hello, World!' # バイナリデータ
    # BytesIOオブジェクトを作成
    virtual_file = BytesIO(test_data)
    # FileStorageオブジェクトを作成
    file = FileStorage(stream=virtual_file, filename='helloworld.pdf', content_type='application/pdf')

    url = url_for("weko_records_ui.replace_file")

    with patch("weko_records_ui.api.import_items_to_system", return_value={"success": True, "recid": {}}):

        login(client,obj=users[0]["obj"])

        # location weko local
        res = client.post(
            url,
            data={
                'pid': '1',
                'bucket_id': records_buckets.bucket_id,
                'file_name': 'helloworld.pdf',
                'file_size': 2000,
                'file_checksum': None,
                'new_bucket_id': None,
                'new_version_id': None,
                'file': file,
                'return_file_place': 'local',
            },
        )
        assert res.status_code == 200

def test_replace_file_bucket_S3(app, db, users, client, records):

    pid = PersistentIdentifier.query.filter_by(
        pid_type="recid", pid_value='1'
    ).first()
    records_buckets = RecordsBuckets.query.filter_by(
        record_id=pid.object_uuid).first()
    file_obj = ObjectVersion.get(bucket=records_buckets.bucket_id, key='helloworld.pdf')

    # テスト用のデータを用意
    test_data = b'Hello, World!' # バイナリデータ
    # BytesIOオブジェクトを作成
    virtual_file = BytesIO(test_data)
    # FileStorageオブジェクトを作成
    file = FileStorage(stream=virtual_file, filename='helloworld.pdf', content_type='application/pdf')

    url = url_for("weko_records_ui.replace_file")

    with patch("weko_records_ui.api.import_items_to_system", return_value={"success": True, "recid": {}}):

        login(client,obj=users[0]["obj"])
        # location type:s3
        l2=Location.get_default()
        l2.uri='s3://test/'
        l2.access_key='access_key'
        l2.secret_key='secret_key'
        l2.type='s3'
        l2.s3_endpoint_url='https://s3.ap-southeast-2.amazonaws.com/'

        res = client.post(
            url,
            data={
                'return_file_place': 'S3',
                'pid': '1',
                'bucket_id': records_buckets.bucket_id,
                'file_name': 'helloworld.pdf',
                'file_size': 100,
                'file_checksum': '86266081366d3c950c1cb31fbd9e1c38e4834fa52b568753ce28c87bc31252cd',
                'new_bucket_id': records_buckets.bucket_id,
                'new_version_id': file_obj.version_id,
                'file': None,
            },
        )
        assert res.status_code == 200
