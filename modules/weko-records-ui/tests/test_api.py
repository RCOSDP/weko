from smtplib import SMTPException
from mock import patch
import pytest
from flask import url_for,current_app,make_response
import uuid
from pytest_mock import mocker
from sqlalchemy.exc import SQLAlchemyError
from unittest.mock import patch, MagicMock

from invenio_accounts.testutils import login_user_via_session, create_test_user
from weko_records.models import ItemApplication
from weko_records_ui.api import send_request_mail, create_captcha_image, get_item_provide_list, validate_captcha_answer, get_s3_bucket_list, copy_bucket_to_s3, get_file_place_info, replace_file_bucket
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

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_api.py::test_get_s3_bucket_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_s3_bucket_list(app, db, users, client):

    # login for using currentuser
    login(client,obj=users[0]["obj"])

    with db.session.begin_nested():
        p = UserProfile()
        p.user_id = '1'
        p.access_key = '1'
        p.secret_key = '1'
        p.s3_endpoint_url = '1'
        db.session.add(p)

        user_profile = p

        with patch("weko_user_profiles.models.UserProfile.get_by_userid", return_value=user_profile):
            # s3 list_buckets error
            with pytest.raises(Exception):
                result_list = get_s3_bucket_list()

            # success
            mock_response_success = {
                'ResponseMetadata': {
                    'HTTPStatusCode': 200
                },
                'Buckets': [
                    {'Name': 'bucket1'},
                    {'Name': 'bucket2'},
                    {'Name': 'bucket3'}
                ]
            }
            with patch('boto3.client') as mock_client:
                instance = mock_client.return_value
                instance.list_buckets.return_value = mock_response_success

                result_list = get_s3_bucket_list()
                assert result_list == ['bucket1', 'bucket2', 'bucket3']

            # success no buckets
            mock_response_success_no_buckets = {
                'ResponseMetadata': {
                    'HTTPStatusCode': 200
                }
            }
            with patch('boto3.client') as mock_client:
                instance = mock_client.return_value
                instance.list_buckets.return_value = mock_response_success_no_buckets

                result_list = get_s3_bucket_list()
                assert result_list == []

            # response_error
            mock_response_error = {
                'ResponseMetadata': {
                    'HTTPStatusCode': 500
                }
            }
            with patch('boto3.client') as mock_client:
                with pytest.raises(Exception):
                    instance = mock_client.return_value
                    instance.list_buckets.return_value = mock_response_error

                    result_list = get_s3_bucket_list()

        # no profile
        with pytest.raises(Exception):
            result_list = get_s3_bucket_list()

    # profile exists but no access_key
    with db.session.begin_nested():
        p2 = UserProfile()
        p2.user_id = '2'
        p2.access_key = ''
        p2.secret_key = '2'
        p2.s3_endpoint_url = '2'
        db.session.add(p2)

        user_profile2 = p2
        with patch("weko_user_profiles.models.UserProfile.get_by_userid", return_value=user_profile2):
            with pytest.raises(Exception):
                result_list = get_s3_bucket_list()


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_api.py::test_copy_bucket_to_s3 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_copy_bucket_to_s3(app, db, users, client, records):

    # login for using currentuser
    login(client,obj=users[0]["obj"])

    mock_response = {
        'LocationConstraint': 'us-west-2',
    }
    mock_response2 = {
    }
    with db.session.begin_nested():
        p = UserProfile()
        p.user_id = '1'
        p.access_key = '1'
        p.secret_key = '1'
        p.s3_endpoint_url = 'https://s3.ap-southeast-2.amazonaws.com/'
        db.session.add(p)

        user_profile = p

        # local to s3
        with patch("weko_user_profiles.models.UserProfile.get_by_userid", return_value=user_profile):
            with patch('boto3.client') as mock_client:
                instance = mock_client.return_value
                instance.get_bucket_location.return_value = mock_response

                pid = PersistentIdentifier.query.filter_by(
                    pid_type="recid", pid_value='1'
                ).first()
                records_buckets = RecordsBuckets.query.filter_by(
                    record_id=pid.object_uuid).first()
                org_bucket = Bucket.query.get(records_buckets.bucket_id)
                org_obj = ObjectVersion.get(bucket=org_bucket, key='helloworld.pdf')
                org_fileinstance = FileInstance.get(org_obj.file_id)

                # success create
                uri = copy_bucket_to_s3(pid=1, filename='helloworld.pdf',
                                        org_bucket_id=records_buckets.bucket_id,
                                        checked='create', bucket_name='sample1')
                assert uri

                # success select
                uri = copy_bucket_to_s3(pid=1, filename='helloworld.pdf',
                                        org_bucket_id=records_buckets.bucket_id,
                                        checked='select', bucket_name='sample1')
                assert uri

                with pytest.raises(Exception):
                    # bucket create error
                    instance.create_bucket.side_effect = Exception("error")
                    uri = copy_bucket_to_s3(pid=1, filename='helloworld.pdf',
                                            org_bucket_id=records_buckets.bucket_id,
                                            checked='create', bucket_name='sample1')

                with pytest.raises(Exception):
                    # upload file error
                    instance.upload_file.side_effect = Exception("error")
                    uri = copy_bucket_to_s3(pid=1, filename='helloworld.pdf',
                                            org_bucket_id=records_buckets.bucket_id,
                                            checked='select', bucket_name='sample1')

                with pytest.raises(Exception):
                    # get bucket location error
                    instance.get_bucket_location.side_effect = Exception("error")
                    uri = copy_bucket_to_s3(pid=1, filename='helloworld.pdf',
                                            org_bucket_id=records_buckets.bucket_id,
                                            checked='select', bucket_name='sample1')


        # no profile
        with pytest.raises(Exception):
                uri = copy_bucket_to_s3(pid=1, filename='helloworld.pdf',
                                        org_bucket_id=records_buckets.bucket_id,
                                        checked='create', bucket_name='sample1')

        # s3 to s3
        with patch("weko_user_profiles.models.UserProfile.get_by_userid", return_value=user_profile):
            with patch('boto3.client') as mock_client:
                pid = PersistentIdentifier.query.filter_by(
                    pid_type="recid", pid_value='1'
                ).first()
                records_buckets = RecordsBuckets.query.filter_by(
                    record_id=pid.object_uuid).first()
                org_bucket = Bucket.query.get(records_buckets.bucket_id)
                org_obj = ObjectVersion.get(bucket=org_bucket, key='helloworld.pdf')
                org_fileinstance = FileInstance.get(org_obj.file_id)
                loc_s3 = Location(
                    name="testloc-s3",
                    uri="s3://bucket-name/",
                    default=False,
                    type="s3",
                    s3_endpoint_url="https://s3.us-west-2.amazonaws.com/",
                )
                db.session.add(loc_s3)
                parts = loc_s3.uri.split('/')
                org_fileinstance.uri = 's3://bucket-name/' + "/".join(parts[2:])
                instance = mock_client.return_value
                instance.get_bucket_location.return_value = mock_response

                # success create
                uri = copy_bucket_to_s3(pid=1, filename='helloworld.pdf',
                                        org_bucket_id=records_buckets.bucket_id,
                                        checked='create', bucket_name='sample1')
                assert uri

                with pytest.raises(Exception):
                    # copy error
                    instance.copy.side_effect = Exception("error")
                    uri = copy_bucket_to_s3(pid=1, filename='helloworld.pdf',
                                            org_bucket_id=records_buckets.bucket_id,
                                            checked='select', bucket_name='sample1')

                with pytest.raises(Exception):
                    # head_object error
                    instance.head_object.side_effect = Exception("error")
                    uri = copy_bucket_to_s3(pid=1, filename='helloworld.pdf',
                                            org_bucket_id=records_buckets.bucket_id,
                                            checked='select', bucket_name='sample1')



    # profile exists but no access_key
    with db.session.begin_nested():
        p2 = UserProfile()
        p2.user_id = '2'
        p2.access_key = ''
        p2.secret_key = '2'
        p2.s3_endpoint_url = 'https://s3.us-west-2.amazonaws.com/'
        db.session.add(p2)

        user_profile2 = p2
        with patch("weko_user_profiles.models.UserProfile.get_by_userid", return_value=user_profile2):
            with pytest.raises(Exception):
                uri = copy_bucket_to_s3(pid=1, filename='helloworld.pdf',
                                        org_bucket_id=records_buckets.bucket_id,
                                        checked='create', bucket_name='sample1')

    # region setting exists
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
                instance.create_bucket.return_value = mock_response2
                instance.get_bucket_location.return_value = mock_response2
                instance.upload_file.return_value = mock_response2

                pid = PersistentIdentifier.query.filter_by(
                    pid_type="recid", pid_value='1'
                ).first()
                records_buckets = RecordsBuckets.query.filter_by(
                    record_id=pid.object_uuid).first()

                uri = copy_bucket_to_s3(pid=1, filename='helloworld.pdf',
                                        org_bucket_id=records_buckets.bucket_id,
                                        checked='create', bucket_name='sample1')
                assert uri


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_api.py::test_get_file_place_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_file_place_info(app, db, users, client, records):

    pid = PersistentIdentifier.query.filter_by(
        pid_type="recid", pid_value='1'
    ).first()
    records_buckets = RecordsBuckets.query.filter_by(
        record_id=pid.object_uuid).first()

    mock_response = 'http:return_url'

    with db.session.begin_nested():

        # location weko local
        # success
        file_place, url, new_bucket_id, new_version_id  = get_file_place_info(org_pid=1,
                                                                                org_bucket_id=records_buckets.bucket_id,
                                                                                file_name='helloworld.pdf')
        assert file_place == 'local'



        # location type:s3
        l2=Location.get_default()
        l2.uri='s3://test/'
        l2.access_key='access_key'
        l2.secret_key='secret_key'
        l2.type='s3'
        l2.s3_endpoint_url='https://test.s3.ap-southeast-2.amazonaws.com/'

        with patch('boto3.client') as mock_client:
            instance = mock_client.return_value
            instance.generate_presigned_url.return_value = mock_response

            file_place, url, new_bucket_id, new_version_id  = get_file_place_info(org_pid=1,
                                                                                  org_bucket_id=records_buckets.bucket_id,
                                                                                  file_name='helloworld.pdf')
            assert file_place == 'S3'

        # location type:s3_path
        # ex: https://bucket_name.s3.us-east-1.amazonaws.com/file_name
        l2=Location.get_default()
        l2.uri='https://test.s3.ap-southeast-2.amazonaws.com/'
        l2.access_key='access_key'
        l2.secret_key='secret_key'
        l2.type='s3_path'
        l2.s3_endpoint_url='https://test.s3.ap-southeast-2.amazonaws.com/'

        with patch('boto3.client') as mock_client:
            instance = mock_client.return_value
            instance.generate_presigned_url.return_value = mock_response

            file_place, url, new_bucket_id, new_version_id  = get_file_place_info(org_pid=1,
                                                                                  org_bucket_id=records_buckets.bucket_id,
                                                                                  file_name='helloworld.pdf')
            assert file_place == 'S3'

        # ex: https://s3.amazonaws.com/bucket_name/file_name
        l2.uri='https://s3.ap-southeast-2.amazonaws.com/test/'
        l2.s3_endpoint_url='https://s3.ap-southeast-2.amazonaws.com/test/'

        with patch('boto3.client') as mock_client:
            instance = mock_client.return_value
            instance.generate_presigned_url.return_value = mock_response

            file_place, url, new_bucket_id, new_version_id  = get_file_place_info(org_pid=1,
                                                                                  org_bucket_id=records_buckets.bucket_id,
                                                                                  file_name='helloworld.pdf')
            assert file_place == 'S3'


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
