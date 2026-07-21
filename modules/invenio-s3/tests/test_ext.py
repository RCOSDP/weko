import pytest
from flask import Flask
from invenio_files_rest.models import Location
from invenio_s3.ext import InvenioS3


@pytest.fixture
def app():
    """Flaskアプリケーションのテスト用インスタンスを作成。"""
    app = Flask("testapp")
    app.config['S3_ACCESS_KEY_ID'] = 'test-access-key'
    app.config['S3_SECRET_ACCESS_KEY'] = 'test-secret-key'
    app.config['S3_ENDPOINT_URL'] = 'http://localhost:9000'
    app.config['S3_REGION_NAME'] = 'us-east-1'
    app.config['S3_SIGNATURE_VERSION'] = 's3v4'
    app.config['S3_LOCATION_TYPE_S3_PATH_VALUE'] = 's3_path'
    app.config['S3_LOCATION_TYPE_S3_VIRTUAL_HOST_VALUE'] = 's3_virtual_host'
    return app


@pytest.fixture
def location():
    """Locationモデルのモックを作成。"""
    return Location(
        name='testloc',
        uri='s3://testbucket',
        default=True,
        type='s3',
        access_key='location-access-key',
        secret_key='location-secret-key',
        readonly_access_key='location-readonly-access-key',
        readonly_secret_key='location-readonly-secret-key',
        s3_endpoint_url='http://localhost:9000',
        s3_region_name='us-east-1',
        s3_signature_version='s3v4'
    )


def test_init_s3fs_info_with_global_config(app, location):
    """グローバル設定を使用してS3FS情報を初期化するテスト。"""
    with app.app_context():
        invenio_s3 = InvenioS3(app)
        info = invenio_s3.init_s3fs_info(location)
        assert info['key'] == 'location-access-key'
        assert info['secret'] == 'location-secret-key'
        assert info['client_kwargs']['endpoint_url'] == 'http://localhost:9000'
        assert info['client_kwargs']['region_name'] == 'us-east-1'
        assert info['config_kwargs']['signature_version'] == 's3v4'

        info = invenio_s3.init_s3fs_info(location, mode='rb')
        assert info['key'] == 'location-readonly-access-key'
        assert info['secret'] == 'location-readonly-secret-key'
        assert info['client_kwargs']['endpoint_url'] == 'http://localhost:9000'
        assert info['client_kwargs']['region_name'] == 'us-east-1'
        assert info['config_kwargs']['signature_version'] == 's3v4'


def test_init_s3fs_info_with_location_config(app, location):
    """Location設定を使用してS3FS情報を初期化するテスト。"""
    location.type = app.config['S3_LOCATION_TYPE_S3_VIRTUAL_HOST_VALUE']
    with app.app_context():
        invenio_s3 = InvenioS3(app)
        info = invenio_s3.init_s3fs_info(location)
        assert info['key'] == 'location-access-key'
        assert info['secret'] == 'location-secret-key'
        assert info['client_kwargs']['endpoint_url'] == 'http://localhost:9000'
        assert info['client_kwargs']['region_name'] == 'us-east-1'
        assert info['config_kwargs']['signature_version'] == 's3v4'

        info = invenio_s3.init_s3fs_info(location, mode='rb')
        assert info['key'] == 'location-readonly-access-key'
        assert info['secret'] == 'location-readonly-secret-key'
        assert info['client_kwargs']['endpoint_url'] == 'http://localhost:9000'
        assert info['client_kwargs']['region_name'] == 'us-east-1'
        assert info['config_kwargs']['signature_version'] == 's3v4'


def test_init_s3fs_info_with_typo_correction(app):
    """Typoがある設定キーを修正するテスト。"""
    app.config['S3_ACCCESS_KEY_ID'] = 'typo-access-key'
    app.config['S3_SECRECT_ACCESS_KEY'] = 'typo-secret-key'
    app.config['S3_READONLY_ACCESS_KEY_ID'] = 'typo-readonly-access-key'
    app.config['S3_READONLY_SECRET_ACCESS_KEY'] = 'typo-readonly-secret-key'
    with app.app_context():
        invenio_s3 = InvenioS3(app)
        location = Location(
            name='testloc',
            uri='s3://testbucket',
            default=True,
            type='s3',
            access_key='',
            secret_key='',
            readonly_access_key='',
            readonly_secret_key='',
            s3_endpoint_url='http://localhost:9000',
            s3_region_name='us-east-1',
            s3_signature_version='s3v4'
        )
        info = invenio_s3.init_s3fs_info(location)
        assert info['key'] == 'typo-access-key'
        assert info['secret'] == 'typo-secret-key'

        info = invenio_s3.init_s3fs_info(location, mode='rb')
        assert info['key'] == 'typo-readonly-access-key'
        assert info['secret'] == 'typo-readonly-secret-key'
