from invenio_oauth2server.models import Token
from mock import patch
from flask import Blueprint
from pytest import fail

from sqlalchemy.exc import SQLAlchemyError
from weko_records.rest import (
    create_error_handlers,
    create_blueprint,
)

# .tox/c1/bin/pytest --cov=weko_records tests/test_rest.py::test_create_error_handlers -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko_records/.tox/c1/tmp
# def create_error_handlers(blueprint):
def test_create_error_handlers(app):
    blueprint = Blueprint(
        'weko_records_rest',
        __name__,
        url_prefix='',
    )
    assert create_error_handlers(blueprint) == None

# .tox/c1/bin/pytest --cov=weko_records tests/test_rest.py::test_create_blueprint -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko_records/.tox/c1/tmp
# def create_blueprint(endpoints):
def test_create_blueprint(app):
    endpoints = {
        'oa_status_callback': {
            'route': '/<string:version>/oa_status/callback',
            'default_media_type': 'application/json',
        },
        'dummy_endpoint': {
            'route': '/dummy',
            'default_media_type': 'application/json',
        }
    }
    assert create_blueprint(endpoints) != None

# OaStatusCallback
# .tox/c1/bin/pytest --cov=weko_records tests/test_rest.py::test_OaStatusCallback_post_v1 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_OaStatusCallback_post_v1(app, tokens, users):
    """Test OaStatusCallback.post_v1 method."""

    app.register_blueprint(create_blueprint(app.config['WEKO_RECORDS_REST_ENDPOINTS']))

    version = 'v1'
    invalid_version = 'v0'

    correct_request_body = {
        "articles":[
            {
                "id": 1,
                "wos_record_status": "aaa",
                "weko_url": "https://example.org/records/1"
            }
        ]
    }
    correct_request_body2 = {
        "articles":[
            {
                "id": 1,
                "wos_record_status": "aaa",
                "weko_url": "https://example.org/records/1"
            },
            {
                "id": 2,
                "wos_record_status": "bbb",
            }
        ]
    }

    token = tokens[0]["token"].access_token
    headers = {
        "Authorization":"Bearer {}".format(token),
    }
    with app.test_client() as client:

        # TestCase: invalid token
        try:
            res = client.post(
                f'/{version}/oa_status/callback',
                headers = {"Authorization":"Bearer xxxxxxxxx"},
                json = correct_request_body,
                content_type='application/json',
            )
        except:
            fail()
        assert res.status_code == 401

        # TestCase: invalid version
        try:
            res = client.post(
                f'/{invalid_version}/oa_status/callback',
                headers = headers,
                json = correct_request_body,
                content_type='application/json',
            )
        except:
            fail()
        assert res.status_code == 400

        # TestCase: invalid request
        try:
            res = client.post(
                f'/{version}/oa_status/callback',
                headers = headers,
                json = {},
                content_type='application/json',
            )
        except:
            fail()
        assert res.status_code == 400

        # TestCase: 'id' not found
        try:
            res = client.post(
                f'/{version}/oa_status/callback',
                headers = headers,
                json = {
                    "articles":[{"wos_record_status": "aaa"}]
                },
                content_type='application/json',
            )
        except:
            fail()
        assert res.status_code == 200

        # TestCase: Insert
        try:
            res = client.post(
                f'/{version}/oa_status/callback',
                headers = headers,
                json = correct_request_body,
                content_type='application/json',
            )
        except:
            fail()
        assert res.status_code == 200

        # TestCase: Update
        try:
            res = client.post(
                f'/{version}/oa_status/callback',
                headers = headers,
                json = correct_request_body2,
                content_type='application/json',
            )
        except:
            fail()
        assert res.status_code == 200

        # TestCase: SQLAlchemyError
        with patch('weko_records.rest.OaStatus.get_oa_status', side_effect=SQLAlchemyError):
            try:
                res = client.post(
                    f'/{version}/oa_status/callback',
                    headers = headers,
                    json = correct_request_body,
                    content_type='application/json',
                )
            except:
                fail()
            assert res.status_code == 500

        # TestCase: Exception
        with patch('weko_records.rest.OaStatus.get_oa_status', side_effect=Exception):
            try:
                res = client.post(
                    f'/{version}/oa_status/callback',
                    headers = headers,
                    json = correct_request_body,
                    content_type='application/json',
                )
            except:
                fail()
            assert res.status_code == 500

        with patch('weko_records.rest.db.session') as mock_db_session:
            exception = Exception("Test exception")
            mock_db_session.commit.side_effect = exception
            try:
                res = client.post(
                    f'/{version}/oa_status/callback',
                    headers = headers,
                    json = correct_request_body,
                    content_type='application/json',
                )
            except:
                fail()
            assert res.status_code != 200
