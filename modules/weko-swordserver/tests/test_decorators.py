

from unittest.mock import patch,MagicMock
import pytest
from werkzeug.datastructures import FileStorage
from werkzeug.local import LocalProxy
from flask_login.utils import login_user
from flask import current_app, request
from io import BytesIO

from invenio_deposit.scopes import write_scope
from invenio_oauth2server.ext import verify_oauth_token_and_set_current_user

from weko_swordserver.errors import ErrorType, WekoSwordserverException
from weko_swordserver.decorators import check_oauth, check_on_behalf_of,check_package_contents

# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_decorators.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp

# def check_oauth(*scopes):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_decorators.py::test_check_oauth -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_check_oauth(app,client,users,tokens):
    headers = {}
    with app.test_request_context(headers=headers):
        res = check_oauth()(lambda x,y:x+y)(x=1,y=2)
        assert res == 3

    headers = {
        "Authorization":"Bearer {}".format(tokens[0]["token"].access_token),
    }
    with app.test_request_context(headers=headers):
        login_user(users[0]["obj"])
        verify_oauth_token_and_set_current_user()
        res = check_oauth(write_scope.id)(lambda x,y:x+y)(x=1,y=2)
        assert res == 3

    headers = {
        "Authorization":"Bearer {}".format(tokens[0]["token"].access_token),
    }
    with app.test_request_context(headers=headers):
        with pytest.raises(WekoSwordserverException) as e:
            res = check_oauth(write_scope.id)(lambda x,y:x+y)(x=1,y=2)
            assert e.errorType == ErrorType.AuthenticationFailed
            assert e.message == "Authentication is failed."


# def check_on_behalf_of():
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_decorators.py::test_check_on_behalf_of -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_check_on_behalf_of(app):
    # TODO: when accept on behalf of
    app.config['WEKO_SWORDSERVER_SERVICEDOCUMENT_ON_BEHALF_OF'] = True


    # when not accept on behalf of
    app.config['WEKO_SWORDSERVER_SERVICEDOCUMENT_ON_BEHALF_OF'] = False
    with app.test_request_context():
        res = check_on_behalf_of()(lambda x,y: x+y)(x=1,y=2)
        assert res == 3
    with app.test_request_context(headers={"On-Behalf-Of":"test"}):
        with pytest.raises(WekoSwordserverException) as e:
            res = check_on_behalf_of()(lambda x,y: x+y)(x=1,y=2)
            assert e.errorType == ErrorType.OnBehalfOfNotAllowed
            assert e.message == "Not support On-Behalf-Of."


# def check_package_contents():
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_decorators.py::test_check_package_contents -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_check_package_contents(app,make_zip,make_crate,tokens,mocker):
    # when not required content length
    app.config['WEKO_SWORDSERVER_CONTENT_LENGTH'] = False
    with app.test_request_context():
        with pytest.raises(WekoSwordserverException) as e:
            res = check_package_contents()(lambda x,y:x+y)(x=1,y=2)
            assert e.errorType == ErrorType.ContentMalformed
            assert e.message == "No file part."
    zip = make_zip()
    storage=FileStorage(filename="",stream=zip)
    with app.test_request_context(data=dict(file=storage)):
        with pytest.raises(WekoSwordserverException) as e:
            res = check_package_contents()(lambda x,y:x+y)(x=1,y=2)
            assert e.errorType == ErrorType.ContentMalformed
            assert e.message == "No selected file."

    # TODO: when required content length
    app.config['WEKO_SWORDSERVER_CONTENT_LENGTH'] = True

    # 20
    maxUploadSize = 10

    mock_data = BytesIO(b"0" * (maxUploadSize))
    mock_file = MagicMock(spec=FileStorage, filename="mockfile.zip", stream=mock_data)
    mock_file.seek = MagicMock(side_effect=mock_data.seek)
    mock_file.tell = MagicMock(side_effect=mock_data.tell)
    mock_file.seek(0, 2)
    mock_file.size = mock_data.tell()
    mock_file.seek(0, 0)

    mock_headers = {
        "Authorization":"Bearer {}".format(tokens[0]["token"].access_token),
        "Content-Disposition": f"attachment; filename={mock_file.filename}",
        "Packaging": "http://purl.org/net/sword/3.0/package/Binary",
        "Content-Type": "application/zip",
        "Content-Length": mock_file.size,
    }
    mock_file.headers = mock_headers

    request_headers_proxy = LocalProxy(lambda: mock_headers)
    request_files_proxy = LocalProxy(lambda: {"file": mock_file})

    with app.test_request_context():
        original_headers = request.headers
        original_files = request.files

        request.headers = request_headers_proxy
        request.files = request_files_proxy

        accept_packaging = ["http://purl.org/net/sword/3.0/package/Binary",
                            "http://purl.org/net/sword/3.0/package/SimpleZip",
                            "http://purl.org/net/sword/3.0/package/SWORDBagIt"]
        try:
            with patch.dict("flask.current_app.config",
                            {"WEKO_SWORDSERVER_CONTENT_LENGTH": True,
                             "WEKO_SWORDSERVER_SERVICEDOCUMENT_MAX_UPLOAD_SIZE": maxUploadSize,
                             "WEKO_SWORDSERVER_SERVICEDOCUMENT_ACCEPT_PACKAGING": accept_packaging[-2:]}):
                with pytest.raises(WekoSwordserverException) as e:
                    check_package_contents()(lambda x, y: x + y)(x=1, y=2)
                assert e.value.errorType == ErrorType.PackagingFormatNotAcceptable
                assert e.value.message == (
                    f"Not accept packaging: {accept_packaging[0]}"
                )
        finally:
            request.headers = original_headers
            request.files = original_files

    # 21
    maxUploadSize = 10

    mock_data = BytesIO(b"0" * (maxUploadSize))
    mock_file = MagicMock(spec=FileStorage, filename="mockfile.jpg", stream=mock_data)
    mock_file.seek = MagicMock(side_effect=mock_data.seek)
    mock_file.tell = MagicMock(side_effect=mock_data.tell)
    mock_file.seek(0, 2)
    mock_file.size = mock_data.tell()
    mock_file.seek(0, 0)

    mock_headers = {
        "Authorization":"Bearer {}".format(tokens[0]["token"].access_token),
        "Content-Disposition": f"attachment; filename={mock_file.filename}",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
        "Content-Type": "application/jpeg",
        "Content-Length": mock_file.size,
    }
    mock_file.headers = mock_headers

    request_headers_proxy = LocalProxy(lambda: mock_headers)
    request_files_proxy = LocalProxy(lambda: {"file": mock_file})

    with app.test_request_context():
        original_headers = request.headers
        original_files = request.files

        request.headers = request_headers_proxy
        request.files = request_files_proxy

        try:
            with patch.dict("flask.current_app.config",
                            {"WEKO_SWORDSERVER_CONTENT_LENGTH": True,
                             "WEKO_SWORDSERVER_SERVICEDOCUMENT_MAX_UPLOAD_SIZE": maxUploadSize}):
                with pytest.raises(WekoSwordserverException) as e:
                    check_package_contents()(lambda x, y: x + y)(x=1, y=2)
                assert e.value.errorType == ErrorType.ContentTypeNotAcceptable
                assert e.value.message == (
                    f"Not accept Content-Type: application/jpeg"
                )
        finally:
            request.headers = original_headers
            request.files = original_files

    # 22
    maxUploadSize = 10

    mock_data = BytesIO(b"0" * (maxUploadSize + 1))
    mock_file = MagicMock(spec=FileStorage, filename="mockfile.zip", stream=mock_data)
    mock_file.seek = MagicMock(side_effect=mock_data.seek)
    mock_file.tell = MagicMock(side_effect=mock_data.tell)
    mock_file.seek(0, 2)
    mock_file.size = mock_data.tell()
    mock_file.seek(0, 0)

    mock_headers = {
        "Authorization":"Bearer {}".format(tokens[0]["token"].access_token),
        "Content-Disposition": f"attachment; filename={mock_file.filename}",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
        "Content-Length": mock_file.size,
    }
    mock_file.headers = mock_headers

    request_headers_proxy = LocalProxy(lambda: mock_headers)
    request_files_proxy = LocalProxy(lambda: {"file": mock_file})

    with app.test_request_context():
        original_headers = request.headers
        original_files = request.files

        request.headers = request_headers_proxy
        request.files = request_files_proxy

        try:
            with patch.dict("flask.current_app.config",
                            {"WEKO_SWORDSERVER_CONTENT_LENGTH": True,
                             "WEKO_SWORDSERVER_SERVICEDOCUMENT_MAX_UPLOAD_SIZE": maxUploadSize}):
                with pytest.raises(WekoSwordserverException) as e:
                    check_package_contents()(lambda x, y: x + y)(x=1, y=2)
                assert e.value.errorType == ErrorType.MaxUploadSizeExceeded
                assert e.value.message == (
                    f"Content size is too large. "
                    f"(request:{maxUploadSize+1}, maxUploadSize:{maxUploadSize})"
                )
        finally:
            request.headers = original_headers
            request.files = original_files

    # 23-27
    maxUploadSize = 10

    mock_data = BytesIO(b"0" * (maxUploadSize))
    mock_file = MagicMock(spec=FileStorage, filename="mockfile.zip", stream=mock_data)
    mock_file.seek = MagicMock(side_effect=mock_data.seek)
    mock_file.tell = MagicMock(side_effect=mock_data.tell)

    mock_headers = {
        "Authorization":"Bearer {}".format(tokens[0]["token"].access_token),
        "Content-Disposition": f"attachment; filename={mock_file.filename}",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
        "Content-Type": "application/zip",
    }
    mock_file.headers = mock_headers

    request_headers_proxy = LocalProxy(lambda: mock_headers)
    request_files_proxy = LocalProxy(lambda: {"file": mock_file})

    with app.test_request_context():
        original_headers = request.headers
        original_files = request.files

        request.headers = request_headers_proxy
        request.files = request_files_proxy

        accept_packaging = ["http://purl.org/net/sword/3.0/package/Binary",
                            "http://purl.org/net/sword/3.0/package/SimpleZip",
                            "http://purl.org/net/sword/3.0/package/SWORDBagIt"]
        try:
            with patch.dict("flask.current_app.config",
                            {"WEKO_SWORDSERVER_CONTENT_LENGTH": False,
                             "WEKO_SWORDSERVER_SERVICEDOCUMENT_MAX_UPLOAD_SIZE": maxUploadSize,
                             "WEKO_SWORDSERVER_SERVICEDOCUMENT_ACCEPT_PACKAGING": accept_packaging[-2:]}):
                res = check_package_contents()(lambda x, y: x + y)(x=1, y=2)
                assert res == 3
        finally:
            request.headers = original_headers
            request.files = original_files

    # 28,29
    maxUploadSize = 10

    mock_data = BytesIO(b"0" * (maxUploadSize))
    mock_file = MagicMock(spec=FileStorage, filename="mockfile.zip", stream=mock_data)
    mock_file.seek = MagicMock(side_effect=mock_data.seek)
    mock_file.tell = MagicMock(side_effect=mock_data.tell)

    mock_headers = {
        "Authorization":"Bearer {}".format(tokens[0]["token"].access_token),
        "Content-Disposition": f"attachment; filename={mock_file.filename}",
        "Packaging": "http://purl.org/net/sword/3.0/package/SWORDBagIt",
        "Content-Type": "application/zip",
    }
    mock_file.headers = mock_headers

    request_headers_proxy = LocalProxy(lambda: mock_headers)
    request_files_proxy = LocalProxy(lambda: {"file": mock_file})

    with app.test_request_context():
        original_headers = request.headers
        original_files = request.files

        request.headers = request_headers_proxy
        request.files = request_files_proxy

        accept_packaging = ["http://purl.org/net/sword/3.0/package/Binary",
                            "http://purl.org/net/sword/3.0/package/SimpleZip",
                            "http://purl.org/net/sword/3.0/package/SWORDBagIt"]
        try:
            with patch.dict("flask.current_app.config",
                            {"WEKO_SWORDSERVER_CONTENT_LENGTH": False,
                             "WEKO_SWORDSERVER_SERVICEDOCUMENT_MAX_UPLOAD_SIZE": maxUploadSize,
                             "WEKO_SWORDSERVER_SERVICEDOCUMENT_ACCEPT_PACKAGING": accept_packaging[-2:]}):
                res = check_package_contents()(lambda x, y: x + y)(x=1, y=2)
                assert res == 3
        finally:
            request.headers = original_headers
            request.files = original_files

    # 30
    maxUploadSize = 10

    mock_data = BytesIO(b"0" * (maxUploadSize))
    mock_file = MagicMock(spec=FileStorage, filename="mockfile.zip", stream=mock_data)
    mock_file.seek = MagicMock(side_effect=mock_data.seek)
    mock_file.tell = MagicMock(side_effect=mock_data.tell)

    mock_headers = {
        "Authorization":"Bearer {}".format(tokens[0]["token"].access_token),
        "Content-Disposition": f"attachment; filename={mock_file.filename}",
        "Packaging": "http://purl.org/net/sword/3.0/package/Binary",
        "Content-Type": "application/zip",
    }
    mock_file.headers = mock_headers

    request_headers_proxy = LocalProxy(lambda: mock_headers)
    request_files_proxy = LocalProxy(lambda: {"file": mock_file})

    with app.test_request_context():
        original_headers = request.headers
        original_files = request.files

        request.headers = request_headers_proxy
        request.files = request_files_proxy

        accept_packaging = ["http://purl.org/net/sword/3.0/package/Binary",
                            "http://purl.org/net/sword/3.0/package/SimpleZip",
                            "http://purl.org/net/sword/3.0/package/SWORDBagIt"]
        try:
            with patch.dict("flask.current_app.config",
                            {"WEKO_SWORDSERVER_CONTENT_LENGTH": False,
                             "WEKO_SWORDSERVER_SERVICEDOCUMENT_MAX_UPLOAD_SIZE": maxUploadSize,
                             "WEKO_SWORDSERVER_SERVICEDOCUMENT_ACCEPT_PACKAGING": accept_packaging[-2:]}):
                with pytest.raises(WekoSwordserverException) as e:
                    check_package_contents()(lambda x, y: x + y)(x=1, y=2)
                assert e.value.errorType == ErrorType.PackagingFormatNotAcceptable
                assert e.value.message == (
                    f"Not accept packaging: {accept_packaging[0]}"
                )
        finally:
            request.headers = original_headers
            request.files = original_files

    # 31
    maxUploadSize = 10

    mock_data = BytesIO(b"0" * (maxUploadSize))
    mock_file = MagicMock(spec=FileStorage, filename="mockfile.jpg", stream=mock_data)
    mock_file.seek = MagicMock(side_effect=mock_data.seek)
    mock_file.tell = MagicMock(side_effect=mock_data.tell)

    mock_headers = {
        "Authorization":"Bearer {}".format(tokens[0]["token"].access_token),
        "Content-Disposition": f"attachment; filename={mock_file.filename}",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
        "Content-Type": "application/jpeg",
    }
    mock_file.headers = mock_headers

    request_headers_proxy = LocalProxy(lambda: mock_headers)
    request_files_proxy = LocalProxy(lambda: {"file": mock_file})

    with app.test_request_context():
        original_headers = request.headers
        original_files = request.files

        request.headers = request_headers_proxy
        request.files = request_files_proxy

        try:
            with patch.dict("flask.current_app.config",
                            {"WEKO_SWORDSERVER_CONTENT_LENGTH": False,
                             "WEKO_SWORDSERVER_SERVICEDOCUMENT_MAX_UPLOAD_SIZE": maxUploadSize}):
                with pytest.raises(WekoSwordserverException) as e:
                    check_package_contents()(lambda x, y: x + y)(x=1, y=2)
                assert e.value.errorType == ErrorType.ContentTypeNotAcceptable
                assert e.value.message == (
                    f"Not accept Content-Type: application/jpeg"
                )
        finally:
            request.headers = original_headers
            request.files = original_files

    # 32
    maxUploadSize = 10

    mock_data = BytesIO(b"0" * (maxUploadSize + 1))
    mock_file = MagicMock(spec=FileStorage, filename="mockfile.zip", stream=mock_data)
    mock_file.seek = MagicMock(side_effect=mock_data.seek)
    mock_file.tell = MagicMock(side_effect=mock_data.tell)

    mock_headers = {
        "Authorization":"Bearer {}".format(tokens[0]["token"].access_token),
        "Content-Disposition": f"attachment; filename={mock_file.filename}",
        "Packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
    }
    mock_file.headers = mock_headers

    request_headers_proxy = LocalProxy(lambda: mock_headers)
    request_files_proxy = LocalProxy(lambda: {"file": mock_file})

    with app.test_request_context():
        original_headers = request.headers
        original_files = request.files

        request.headers = request_headers_proxy
        request.files = request_files_proxy

        try:
            with patch.dict("flask.current_app.config",
                            {"WEKO_SWORDSERVER_CONTENT_LENGTH": False,
                             "WEKO_SWORDSERVER_SERVICEDOCUMENT_MAX_UPLOAD_SIZE": maxUploadSize}):
                with pytest.raises(WekoSwordserverException) as e:
                    check_package_contents()(lambda x, y: x + y)(x=1, y=2)
                assert e.value.errorType == ErrorType.MaxUploadSizeExceeded
                assert e.value.message == (
                    f"Content size is too large. "
                    f"(request:{maxUploadSize+1}, maxUploadSize:{maxUploadSize})"
                )
        finally:
            request.headers = original_headers
            request.files = original_files

    # 33
    headers = {}
    with app.test_request_context(headers=headers):
        with pytest.raises(WekoSwordserverException) as e:
            check_package_contents()(lambda x,y:x+y)(x=1,y=2)
            print("assert result:")
        assert e.value.errorType == ErrorType.ContentMalformed
        assert e.value.message == "No file part."
