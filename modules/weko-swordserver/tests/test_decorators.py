import pytest
import io
from werkzeug.datastructures import FileStorage
from werkzeug.local import LocalProxy
from flask_login.utils import login_user
from flask import request
from invenio_deposit.scopes import write_scope
from invenio_oauth2server.ext import verify_oauth_token_and_set_current_user
from unittest.mock import MagicMock
from weko_swordserver.errors import ErrorType, WekoSwordserverException
from weko_swordserver.decorators import (
    check_oauth,
    check_on_behalf_of,
    check_package_contents,
)

from weko_swordserver.decorators import check_package_contents
from werkzeug.local import LocalProxy

# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_decorators.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp

# def check_oauth(*scopes):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_decorators.py::test_check_oauth -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_check_oauth(app, client, users, tokens):
    headers = {}
    with app.test_request_context(headers=headers):
        res = check_oauth()(lambda x, y: x + y)(x=1, y=2)
        assert res == 3

    headers = {
        "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
    }
    with app.test_request_context(headers=headers):
        login_user(users[0]["obj"])
        verify_oauth_token_and_set_current_user()
        res = check_oauth(write_scope.id)(lambda x, y: x + y)(x=1, y=2)
        assert res == 3

    headers = {
        "Authorization": "Bearer {}".format(tokens[0]["token"].access_token),
    }
    with app.test_request_context(headers=headers):
        with pytest.raises(WekoSwordserverException) as e:
            res = check_oauth(write_scope.id)(lambda x, y: x + y)(x=1, y=2)

        assert e.value.errorType == ErrorType.AuthenticationFailed
        assert e.value.message == "Authentication is failed."


# def check_on_behalf_of():
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_decorators.py::test_check_on_behalf_of -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_check_on_behalf_of(app):

    # when accept on behalf of , "On-Behalf-Of" has been set
    app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_ON_BEHALF_OF"] = True
    with app.test_request_context(headers={"On-Behalf-Of": "test"}):
        res = check_on_behalf_of()(lambda x, y: x + y)(x=1, y=2)
        assert res == 3

    # when accept on behalf of ,but "On-Behalf-Of" did not set
    app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_ON_BEHALF_OF"] = True
    with app.test_request_context():
        res = check_on_behalf_of()(lambda x, y: x + y)(x=1, y=2)
        assert res == 3

    # when not accept on behalf of , "On-Behalf-Of" has been set
    app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_ON_BEHALF_OF"] = False
    with app.test_request_context(headers={"On-Behalf-Of": "test"}):
        with pytest.raises(WekoSwordserverException) as e:
            res = check_on_behalf_of()(lambda x, y: x + y)(x=1, y=2)
        assert e.value.errorType == ErrorType.OnBehalfOfNotAllowed
        assert e.value.message == "Not support On-Behalf-Of."

    # when not accept on behalf of , "On-Behalf-Of" did not set
    app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_ON_BEHALF_OF"] = False
    with app.test_request_context():
        res = check_on_behalf_of()(lambda x, y: x + y)(x=1, y=2)
        assert res == 3


# def check_package_contents():
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_decorators.py::test_check_package_contents -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_check_package_contents(app, client, make_crate, tokens, mocker):

    # error message:"Not accept packaging: "
    app.config["WEKO_SWORDSERVER_CONTENT_LENGTH"] = True
    maxSize = app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_MAX_UPLOAD_SIZE"] = 10000
    contentType = app.config.get(
        "WEKO_SWORDSERVER_SERVICEDOCUMENT_ACCEPT_ARCHIVE_FORMAT"
    )
    app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_ACCEPT_PACKAGING"] = [
        "http://purl.org/net/sword/3.0/package/Binary",
        "http://purl.org/net/sword/3.0/package/SimpleZip",
    ]
    zip = make_crate()
    mock_data = io.BytesIO(zip[0].read())
    mock_data.seek(0, io.SEEK_END)
    size = mock_data.tell()
    mock_data.seek(0, 0)
    mock_stream = MagicMock()
    mock_stream.read = MagicMock(side_effect=mock_data.read)
    mock_stream.seek = MagicMock(side_effect=mock_data.seek)
    mock_stream.tell = MagicMock(side_effect=mock_data.tell)
    mock_file = MagicMock(spec=FileStorage)
    mock_file.filename = "mockfile.zip"
    mock_file.stream = mock_stream
    mock_file.seek = MagicMock(side_effect=mock_stream.seek)
    mock_file.tell = MagicMock(side_effect=mock_stream.tell)
    mock_file.headers = {"Content-Type": contentType[0]}

    with app.test_request_context():
        original = request.files
        request.files = LocalProxy(lambda: {"file": mock_file})
        original_headers = request.headers
        request.headers = LocalProxy(
            lambda: {
                "Content-Length": str(size),
                "Content-Type": contentType[0],
                "Packaging": "XXXX",
            }
        )
        try:
            with pytest.raises(WekoSwordserverException) as e:
                res = check_package_contents()(lambda x, y: x + y)(x=1, y=2)
            assert e.value.errorType == ErrorType.PackagingFormatNotAcceptable
            assert e.value.message == f"Not accept packaging: XXXX"
        finally:
            request.files = original
            request.headers = original_headers

    # error message:"Not accept Content-Type:
    app.config["WEKO_SWORDSERVER_CONTENT_LENGTH"] = True
    maxSize = app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_MAX_UPLOAD_SIZE"] = 10000
    contentType = app.config.get(
        "WEKO_SWORDSERVER_SERVICEDOCUMENT_ACCEPT_ARCHIVE_FORMAT"
    )
    zip = make_crate()
    mock_data = io.BytesIO(zip[0].read())
    mock_data.seek(0, io.SEEK_END)
    size = mock_data.tell()
    mock_data.seek(0, 0)
    mock_stream = MagicMock()
    mock_stream.read = MagicMock(side_effect=mock_data.read)
    mock_stream.seek = MagicMock(side_effect=mock_data.seek)
    mock_stream.tell = MagicMock(side_effect=mock_data.tell)
    mock_file = MagicMock(spec=FileStorage)
    mock_file.filename = "mockfile.zip"
    mock_file.stream = mock_stream
    mock_file.seek = MagicMock(side_effect=mock_stream.seek)
    mock_file.tell = MagicMock(side_effect=mock_stream.tell)
    mock_file.headers = {"Content-Type": "application/json"}

    with app.test_request_context():
        original = request.files
        request.files = LocalProxy(lambda: {"file": mock_file})
        original_headers = request.headers
        request.headers = LocalProxy(
            lambda: {"Content-Length": str(size), "Content-Type": "application/json"}
        )
        try:
            with pytest.raises(WekoSwordserverException) as e:
                res = check_package_contents()(lambda x, y: x + y)(x=1, y=2)
            assert e.value.errorType == ErrorType.ContentTypeNotAcceptable
            assert e.value.message == f"Not accept Content-Type: application/json"
        finally:
            request.files = original
            request.headers = original_headers

    # error message:"Not accept Content-Type and file's Content-Type is None:
    app.config["WEKO_SWORDSERVER_CONTENT_LENGTH"] = True
    maxSize = app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_MAX_UPLOAD_SIZE"] = 10000
    contentType = app.config.get(
        "WEKO_SWORDSERVER_SERVICEDOCUMENT_ACCEPT_ARCHIVE_FORMAT"
    )
    zip = make_crate()
    mock_data = io.BytesIO(zip[0].read())
    mock_data.seek(0, io.SEEK_END)
    size = mock_data.tell()
    mock_data.seek(0, 0)
    mock_stream = MagicMock()
    mock_stream.read = MagicMock(side_effect=mock_data.read)
    mock_stream.seek = MagicMock(side_effect=mock_data.seek)
    mock_stream.tell = MagicMock(side_effect=mock_data.tell)
    mock_file = MagicMock(spec=FileStorage)
    mock_file.filename = "mockfile.zip"
    mock_file.stream = mock_stream
    mock_file.seek = MagicMock(side_effect=mock_stream.seek)
    mock_file.tell = MagicMock(side_effect=mock_stream.tell)
    mock_file.headers = {"Content-Type": None}

    with app.test_request_context():
        original = request.files
        request.files = LocalProxy(lambda: {"file": mock_file})
        original_headers = request.headers
        request.headers = LocalProxy(
            lambda: {"Content-Length": str(size), "Content-Type": "application/json"}
        )
        try:
            with pytest.raises(WekoSwordserverException) as e:
                res = check_package_contents()(lambda x, y: x + y)(x=1, y=2)
            assert e.value.errorType == ErrorType.ContentTypeNotAcceptable
            assert e.value.message == f"Not accept Content-Type: application/json"
        finally:
            request.files = original
            request.headers = original_headers

    # error message:"Content size is too large."
    app.config["WEKO_SWORDSERVER_CONTENT_LENGTH"] = True
    maxSize = app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_MAX_UPLOAD_SIZE"] = 1000
    zip = make_crate()
    mock_data = io.BytesIO(zip[0].read())
    mock_data.seek(0, io.SEEK_END)
    size = mock_data.tell()
    mock_data.seek(0, 0)
    mock_stream = MagicMock()
    mock_stream.read = MagicMock(side_effect=mock_data.read)
    mock_stream.seek = MagicMock(side_effect=mock_data.seek)
    mock_stream.tell = MagicMock(side_effect=mock_data.tell)
    mock_file = MagicMock(spec=FileStorage)
    mock_file.filename = "mockfile.zip"
    mock_file.stream = mock_stream
    mock_file.seek = MagicMock(side_effect=mock_stream.seek)
    mock_file.tell = MagicMock(side_effect=mock_stream.tell)

    with app.test_request_context():
        original_files = request.files
        request.files = LocalProxy(lambda: {"file": mock_file})
        original_headers = request.headers
        request.headers = LocalProxy(
            lambda: {"Content-Length": str(size), "Content-Type": "application/zip"}
        )
        try:
            with pytest.raises(WekoSwordserverException) as e:
                res = check_package_contents()(lambda x, y: x + y)(x=1, y=2)
            assert e.value.errorType == ErrorType.MaxUploadSizeExceeded
            assert (
                e.value.message
                == f"Content size is too large. (request:{size}, maxUploadSize:{maxSize})"
            )
        finally:
            request.files = original_files
            request.headers = original_headers

    # error message:"Content-Length is not equal to real content length."
    app.config["WEKO_SWORDSERVER_CONTENT_LENGTH"] = True
    zip = make_crate()
    mock_data = io.BytesIO(zip[0].read())
    mock_data.seek(0, io.SEEK_END)
    size = mock_data.tell()
    mock_data.seek(0, 0)
    mock_stream = MagicMock()
    mock_stream.read = MagicMock(side_effect=mock_data.read)
    mock_stream.seek = MagicMock(side_effect=mock_data.seek)
    mock_stream.tell = MagicMock(side_effect=mock_data.tell)
    mock_file = MagicMock(spec=FileStorage)
    mock_file.filename = "mockfile.zip"
    mock_file.stream = mock_stream
    mock_file.seek = MagicMock(side_effect=mock_stream.seek)
    mock_file.tell = MagicMock(side_effect=mock_stream.tell)

    with app.test_request_context():
        original = request.files
        request.files = LocalProxy(lambda: {"file": mock_file})
        original_headers = request.headers
        request.headers = LocalProxy(lambda: {"Content-Length": "1000"})
        try:
            with pytest.raises(WekoSwordserverException) as e:
                res = check_package_contents()(lambda x, y: x + y)(x=1, y=2)
            assert e.value.errorType == ErrorType.ContentMalformed
            assert (
                e.value.message
                == f"Content-Length is not match. (request:1000, real:{size})"
            )
        finally:
            request.files = original
            request.headers = original_headers

    # error message:"Content-Length is required."
    app.config["WEKO_SWORDSERVER_CONTENT_LENGTH"] = True
    zip = make_crate()
    mock_data = io.BytesIO(zip[0].read())
    mock_data.seek(0, io.SEEK_END)
    size = mock_data.tell()
    mock_data.seek(0, 0)
    mock_stream = MagicMock()
    mock_stream.read = MagicMock(side_effect=mock_data.read)
    mock_stream.seek = MagicMock(side_effect=mock_data.seek)
    mock_stream.tell = MagicMock(side_effect=mock_data.tell)
    mock_file = MagicMock(spec=FileStorage)
    mock_file.filename = "mockfile.zip"
    mock_file.stream = mock_stream
    mock_file.seek = MagicMock(side_effect=mock_stream.seek)
    mock_file.tell = MagicMock(side_effect=mock_stream.tell)

    with app.test_request_context():
        original = request.files
        request.files = LocalProxy(lambda: {"file": mock_file})
        try:
            with pytest.raises(WekoSwordserverException) as e:
                res = check_package_contents()(lambda x, y: x + y)(x=1, y=2)
            assert e.value.errorType == ErrorType.ContentMalformed
            assert e.value.message == "Content-Length is required."
        finally:
            request.files = original

    # error message:"Content size is too large."
    app.config["WEKO_SWORDSERVER_CONTENT_LENGTH"] = False
    maxSize = app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_MAX_UPLOAD_SIZE"] = 1000
    zip = make_crate()
    mock_data = io.BytesIO(zip[0].read())
    mock_data.seek(0, io.SEEK_END)
    size = mock_data.tell()
    mock_data.seek(0, 0)
    mock_stream = MagicMock()
    mock_stream.read = MagicMock(side_effect=mock_data.read)
    mock_stream.seek = MagicMock(side_effect=mock_data.seek)
    mock_stream.tell = MagicMock(side_effect=mock_data.tell)
    mock_file = MagicMock(spec=FileStorage)
    mock_file.filename = "mockfile.zip"
    mock_file.stream = mock_stream
    mock_file.seek = MagicMock(side_effect=mock_stream.seek)
    mock_file.tell = MagicMock(side_effect=mock_stream.tell)

    with app.test_request_context():
        original_files = request.files
        request.files = LocalProxy(lambda: {"file": mock_file})
        try:
            with pytest.raises(WekoSwordserverException) as e:
                res = check_package_contents()(lambda x, y: x + y)(x=1, y=2)
            assert e.value.errorType == ErrorType.MaxUploadSizeExceeded
            assert (
                e.value.message
                == f"Content size is too large. (request:{size}, maxUploadSize:{maxSize})"
            )
        finally:
            request.files = original_files

    # error message:"No file part."
    with app.test_request_context(data=None):
        with pytest.raises(WekoSwordserverException) as e:
            decorated_func = check_package_contents()(lambda x, y: x + y)
            decorated_func(x=1, y=2)
        assert e.value.errorType == ErrorType.ContentMalformed
        assert e.value.message == "No file part."

    # error message:"No selected file
    zip = make_crate()
    storage = FileStorage(filename="", stream=zip[0])
    with app.test_request_context(data=dict(file=storage)):
        with pytest.raises(WekoSwordserverException) as e:
            res = check_package_contents()(lambda x, y: x + y)(x=1, y=2)
        assert e.value.errorType == ErrorType.ContentMalformed
        assert e.value.message == "No selected file."

    # success case
    app.config["WEKO_SWORDSERVER_CONTENT_LENGTH"] = True
    maxSize = app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_MAX_UPLOAD_SIZE"] = 10000
    contentType = app.config.get(
        "WEKO_SWORDSERVER_SERVICEDOCUMENT_ACCEPT_ARCHIVE_FORMAT"
    )
    app.config["WEKO_SWORDSERVER_SERVICEDOCUMENT_ACCEPT_PACKAGING"] = [
        "http://purl.org/net/sword/3.0/package/Binary",
        "http://purl.org/net/sword/3.0/package/SimpleZip",
    ]
    zip = make_crate()
    mock_data = io.BytesIO(zip[0].read())
    mock_data.seek(0, io.SEEK_END)
    size = mock_data.tell()
    mock_data.seek(0, 0)
    mock_stream = MagicMock()
    mock_stream.read = MagicMock(side_effect=mock_data.read)
    mock_stream.seek = MagicMock(side_effect=mock_data.seek)
    mock_stream.tell = MagicMock(side_effect=mock_data.tell)
    mock_file = MagicMock(spec=FileStorage)
    mock_file.filename = "mockfile.zip"
    mock_file.stream = mock_stream
    mock_file.seek = MagicMock(side_effect=mock_stream.seek)
    mock_file.tell = MagicMock(side_effect=mock_stream.tell)
    mock_file.headers = {"Content-Type": contentType[0]}

    with app.test_request_context():
        original = request.files
        request.files = LocalProxy(lambda: {"file": mock_file})
        original_headers = request.headers
        request.headers = LocalProxy(
            lambda: {
                "Content-Length": str(size),
                "Content-Type": contentType[0],
                "Packaging": "http://purl.org/net/sword/3.0/package/Binary"
            }
        )
        res = check_package_contents()(lambda x, y: x + y)(x=1, y=2)
        assert res == 3
        request.files = original
        request.headers = original_headers
