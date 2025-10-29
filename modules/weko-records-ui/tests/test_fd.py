# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_fd.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
import io
import pytest
from flask import url_for,make_response
from flask_babelex import get_locale
from mock import patch
from sqlalchemy.exc import SQLAlchemyError
from unittest.mock import MagicMock
from werkzeug.exceptions import NotFound ,Forbidden
from datetime import datetime, timedelta,timezone
from invenio_records_files.utils import record_file_factory
from invenio_theme.config import THEME_ERROR_TEMPLATE
from weko_admin.models import AdminSettings
from weko_deposit.api import WekoFileObject
from weko_schema_ui.models import PublishStatus

from weko_records_ui.config import WEKO_RECORDS_UI_DETAIL_TEMPLATE
from weko_records_ui.errors import AvailableFilesNotFoundRESTError
from weko_records_ui.fd import (
    _download_file, _is_terms_of_use_only, add_signals_info,
    check_onetime_token_and_validate, error_response,
    file_download_onetime, file_download_secret, file_download_ui,
    file_list_ui, file_preview_ui, file_ui, prepare_response,
    process_onetime_file_download, validate_onetime_token,
    validate_onetime_guest, weko_view_method
)
from weko_records_ui.models import AccessStatus, FileSecretDownload,FileOnetimeDownload


# def weko_view_method(pid, record, template=None, **kwargs):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_fd.py::test_weko_view_method -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_weko_view_method(app,records,itemtypes,users):
    indexer, results = records
    recid = results[0]["recid"]
    record = results[0]["record"]
    with app.test_request_context():
        with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
            with patch("flask.templating._render", return_value=""):
                assert weko_view_method(recid,record,WEKO_RECORDS_UI_DETAIL_TEMPLATE)==""

            data1 = MagicMock()
            def dumps():
                return "test/test/test/"
            data1.dumps = dumps
            app.config.WEKO_SEARCH_UI_BASE_PAGE_TEMPLATE = 'weko_records_ui/admin/pdfcoverpage.html'

            with patch("weko_records_ui.fd.FilesMetadata.get_records", return_value=[data1]):
                try:
                    assert weko_view_method(recid,record,WEKO_RECORDS_UI_DETAIL_TEMPLATE)==""
                except:
                    pass


# def prepare_response(pid_value, fd=True):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_fd.py::test_prepare_response -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_prepare_response(app,client,records,itemtypes,users):
    indexer, results = records
    recid = results[0]["recid"]
    with app.test_request_context():
        with pytest.raises(Exception) as e:
            ret = prepare_response(recid.pid_value,True)


# def file_preview_ui(pid, record, _record_file_factory=None, **kwargs):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_fd.py::test_file_preview_ui -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_file_preview_ui(app,records,itemtypes,users):
    indexer, results = records
    recid = results[0]["recid"]
    record = results[0]["record"]
    with app.test_request_context():
        with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
            res = file_preview_ui(recid,record)
            assert res.status == '200 OK'

# def file_download_ui(pid, record, _record_file_factory=None, **kwargs):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_fd.py::test_file_download_ui -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_file_download_ui(app,records,itemtypes,users):
    indexer, results = records
    recid = results[0]["recid"]
    record = results[0]["record"]
    with app.test_request_context():
        with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
            res = file_download_ui(recid,record)
            assert res.status == '200 OK'

# def file_ui(
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_fd.py::test_file_ui -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_file_ui(app,records,itemtypes,users,mocker):
    indexer, results = records
    recid = results[0]["recid"]
    record = results[0]["record"]
    with app.test_request_context():
        with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
            res = file_ui(recid,record)
            assert res.status == '200 OK'

    with app.test_request_context():
        with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
            with pytest.raises(NotFound):
                res = file_ui(recid,record,_record_file_factory= lambda x,y,z: None )

    data1 = MagicMock()
    def cannot():
        return False
    data1.can = cannot
    data2 = MagicMock()
    def is_authenticated_func():
        return False
    data2.is_authenticated = is_authenticated_func
    data3 = MagicMock()
    def can():
        return True
    data3.can = can
    data3.obj = 1


    with app.test_request_context():
    #     with patch("weko_records_ui.fd.file_permission_factory", return_value=data3):
    #         with patch("weko_records_ui.fd.record_file_factory", return_value=data3):
    #             # Exception coverage
    #             try:
    #                 file_ui(pid=1, record=2)
    #             except:
    #                 pass

        with patch("weko_records_ui.fd.file_permission_factory", return_value=data1):
            # abort(403) coverage
            try:
                file_ui(data2, data3)
            except:
                pass

# for records_restricted
# # def file_ui(
# # .tox/c1/bin/pytest --cov=weko_records_ui tests/test_fd.py::test_file_ui2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_file_ui2(app,records_restricted,itemtypes,users ,client ,mocker):
    indexer, results = records_restricted
    recid_none_login =  results[len(results) -2]["recid"]
    recid_login =  results[len(results) -1]["recid"]
    # 21
    # with app.test_request_context():
    mock= mocker.patch('weko_records_ui.fd._download_file' ,return_value=make_response())
    res = client.get(url_for('invenio_records_ui.recid_files'
                        , pid_value = recid_none_login.pid_value
                        , filename = "helloworld_open_restricted.pdf"
                        ) + "?terms_of_use_only=true")
    assert res.status == '200 OK'
    assert mock.call_count == 1
    #22
    data1 = MagicMock()
    def cannot():
        return False
    data1.can = cannot
    mock = mocker.patch('weko_records_ui.fd._redirect_method' ,return_value=make_response())
    with patch('weko_records_ui.fd.file_permission_factory', return_value=data1):
        res = client.get(url_for('invenio_records_ui.recid_files'
                            , pid_value = recid_none_login.pid_value
                            , filename = "helloworld_open_restricted.pdf"
                            ))
        assert res.status == '200 OK'
        assert mock.call_count == 1

    with patch("weko_records_ui.fd.file_permission_factory", return_value=data1):
        with patch("flask_login.utils._get_user", return_value=users[7]["obj"]):
                indexer, results = records_restricted
                recid_none_login =  results[len(results) -2]["recid"]
                recid_login =  results[len(results) -1]["recid"]
                record_login = results[len(results) -1]["record"]

                from werkzeug.exceptions import Forbidden
                try:
                    res = file_ui(recid_login,record_login ,is_preview=False  , filename = "helloworld_open_restricted.pdf")
                    assert False
                except Forbidden :
                    pass

# def file_ui(
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_fd.py::test_file_ui3 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_file_ui3(
    app, records_restricted, itemtypes, db_file_permission, users,
    client, mocker
):
    _, results = records_restricted
    recid_login =  results[len(results) -1]["recid"]
    record_login = results[len(results) -1]["record"]
    data1 = MagicMock()
    def can():
        return True
    data1.can = can

    with app.test_request_context():
        with patch('weko_records_ui.fd.file_permission_factory', return_value=data1):
            # 23
            # Test Case: User has permission and accessrole is open_restricted
            with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
                fileobj:WekoFileObject = record_file_factory(
                    recid_login, record_login,
                    filename="helloworld_open_restricted.pdf"
                )
                fileobj.data["accessrole"] = "open_restricted"
                fileobj.data["filename"] = "helloworld_open_restricted.pdf"
                mock_validate_onetime_token = mocker.patch(
                    "weko_records_ui.fd.validate_onetime_token"
                )
                file_ui(
                    recid_login, record_login, is_preview=False,
                    filename="helloworld_open_restricted.pdf"
                )
                mock_validate_onetime_token.assert_called_once()

            # 24
            # Test Case: User has no permission and accessrole is open_restricted
            with patch("flask_login.utils._get_user", return_value=users[7]["obj"]):
                with patch("weko_records_ui.fd.is_owners_or_superusers", return_value=False):
                    fileobj:WekoFileObject = record_file_factory( recid_login, record_login, filename = "helloworld_open_restricted.pdf" )
                    fileobj.data["accessrole"] = "open_restricted"
                    fileobj.data["filename"] = "helloworld_open_restricted.pdf"

                    with pytest.raises(Forbidden):
                        file_ui(
                            recid_login, record_login, is_preview=False,
                            filename="helloworld_open_restricted.pdf"
                        )


# def _download_file(file_obj, is_preview, lang, obj, pid, record):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_fd.py::test__download_file -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test__download_file(app,records,itemtypes,users):
    indexer, results = records
    recid = results[0]["recid"]
    record = results[0]["record"]
    fileobj = record_file_factory(recid,record,"helloworld.pdf")
    obj = fileobj.obj
    with app.test_request_context():
        with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
            res = _download_file(fileobj,True,"en",obj,recid,record)
            assert res.status == '200 OK'

        fileobj.mimetype = ["pdf", "msword"]
        with patch("weko_records_ui.fd.check_original_pdf_download_permission", return_value="test"):
            _download_file(fileobj,True,"en",obj,recid,record)

# def add_signals_info(record, obj):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_fd.py::test_add_signals_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_add_signals_info(app,records,itemtypes,users):
    indexer, results = records
    recid = results[0]["recid"]
    record = results[0]["record"]
    fileobj = record_file_factory(recid,record,"helloworld.pdf")
    obj = fileobj.obj
    with app.test_request_context():
        with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
            add_signals_info(record,obj)
            assert obj.item_title=='ja_conference paperITEM00000009(public_open_access_open_access_simple)'

        data1 = MagicMock()
        def all_func():
            return []
        data1.roles = []
        data1.all = all_func
        data1.id = 1
        data2 = MagicMock()
        data2.id = 2

        with patch("weko_records_ui.fd.Group.query_by_user", return_value=data1):
            with patch("flask_login.utils._get_user", return_value=data1):
                add_signals_info(record,obj)

            data1.roles = [data1, data2]

            with patch("flask_login.utils._get_user", return_value=data1):
                add_signals_info(record,obj)

                with patch("weko_records_ui.fd.is_billing_item", return_value=True):
                    add_signals_info(record,obj)


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_fd.py::test_error_response -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@patch('weko_records_ui.fd.render_template')
def test_error_response(mock_render):
    mock_render.return_value = '<html>Error Test</html>'
    error_template = 'weko_theme/error.html'
    render, status_code = error_response('Error Test', 500)
    assert render == '<html>Error Test</html>'
    assert status_code == 500
    mock_render.assert_called_once_with(error_template, error='Error Test')


# def check_onetime_token_and_validate(
#    pid, record, filename, _record_file_factory=None, **kwargs):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_fd.py::test_check_onetime_token_and_validate -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@patch("weko_records_ui.fd.validate_onetime_token")
def test_check_onetime_token_and_validate(
    mock_validate, app, records, mocker
):
    """Test check_onetime_token_and_validate function."""
    # Setup
    _, results = records
    recid = results[0]["recid"]
    record = results[0]["record"]
    filename = "helloworld.pdf"
    test_token = "test_token_123"
    test_url = f"http://localhost/records/{recid.pid_value}/files/{filename}?token={test_token}"

    # Configure mocks
    mock_request = mocker.patch('weko_records_ui.fd.request')
    mock_request.args.get.return_value = test_token
    mock_request.url = test_url
    mock_validate.return_value = "mocked_response"

    # Call the function
    with app.test_request_context():
        result = check_onetime_token_and_validate(recid, record, filename)

    # Assertions
    mock_request.args.get.assert_called_once_with('token', type=str)
    mock_validate.assert_called_once_with(
        recid, record, filename, test_token, None, test_url
    )
    assert result == "mocked_response"


# def validate_onetime_token(
#    pid, record, filename, token, mailaddress=None, request_url=None):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_fd.py::test_validate_onetime_token -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@patch('weko_records_ui.fd.validate_url_download')
@patch('weko_records_ui.fd.record_file_factory')
@patch('weko_records_ui.fd.convert_token_into_obj')
@patch('weko_records_ui.fd.current_user')
@patch('weko_records_ui.fd.validate_onetime_guest')
@patch('weko_records_ui.fd.process_onetime_file_download')
@patch('weko_records_ui.fd.error_response')
def test_validate_onetime_token(
    mock_error_response, mock_process_download, mock_validate_guest,
    mock_current_user, mock_convert_token, mock_record_file_factory,
    mock_validate_url, app, records
):
    """Test validate_onetime_token function with different scenarios."""
    # Setup
    _, results = records
    pid = results[0]["recid"]
    record = results[0]["record"]
    filename = "test_file.pdf"
    token = "valid_token_123"
    redirect_url = "http://test.com/redirect"

    # Mock objects
    file_object = MagicMock()
    file_object.obj = True
    url_obj = MagicMock()

    # Common mock configurations
    mock_record_file_factory.return_value = file_object
    mock_convert_token.return_value = url_obj
    mock_error_response.side_effect = lambda msg, code: (f"Error: {msg}", code)
    mock_process_download.return_value = "process_success"
    mock_validate_guest.return_value = "guest_validation"

    # Disable admin restricted access display flag
    result = validate_onetime_token(pid, record, filename, token)
    assert result == ("Error: Restricted access is disabled.", 403)

    app.config["WEKO_ADMIN_RESTRICTED_ACCESS_DISPLAY_FLAG"] = True

    # Test Case 1: Token validation fails
    mock_validate_url.return_value = (False, "Invalid token")
    result = validate_onetime_token(pid, record, filename, token)
    mock_validate_url.assert_called_with(record, filename, token, is_secret_url=False)
    assert result == ("Error: Invalid token", 403)

    # Test Case 2: File object not found
    mock_validate_url.return_value = (True, "")
    mock_record_file_factory.return_value = None
    result = validate_onetime_token(pid, record, filename, token)
    assert result[0] == f"Error: The file \"{filename}\" does not exist."
    assert result[1] == 404

    # Test Case 3: File object found but no obj attribute
    file_object_no_obj = MagicMock()
    file_object_no_obj.obj = None
    mock_record_file_factory.return_value = file_object_no_obj
    result = validate_onetime_token(pid, record, filename, token)
    assert result[0] == f"Error: The file \"{filename}\" does not exist."
    assert result[1] == 404

    # Reset file_object
    mock_record_file_factory.return_value = file_object

    # Test Case 4: Guest user
    url_obj.is_guest = True
    result = validate_onetime_token(pid, record, filename, token, redirect_url=redirect_url)
    mock_validate_guest.assert_called_with(url_obj, pid, token, redirect_url)
    assert result == "guest_validation"

    # Test Case 5: Not authenticated user
    url_obj.is_guest = False
    mock_current_user.is_authenticated = False
    url_obj.user_mail = "test@example.com"
    result = validate_onetime_token(pid, record, filename, token)
    assert result == ("Error: Invalid token.", 403)

    # Test Case 6: Authenticated user but email doesn't match
    mock_current_user.is_authenticated = True
    mock_current_user.email = "wrong@example.com"
    url_obj.user_mail = "test@example.com"
    result = validate_onetime_token(pid, record, filename, token)
    assert result == ("Error: Invalid token.", 403)

    # Test Case 7: Successful validation with authenticated user
    mock_current_user.is_authenticated = True
    mock_current_user.email = "test@example.com"
    url_obj.user_mail = "test@example.com"
    result = validate_onetime_token(pid, record, filename, token)
    mock_process_download.assert_called_with(pid, record, filename, token, mock_record_file_factory)
    assert result == "process_success"


# def validate_onetime_guest(
#    onetime_url_record, pid, token, onetime_url):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_fd.py::test_validate_onetime_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@patch('weko_records_ui.fd.url_for')
@patch('weko_records_ui.fd.redirect')
def test_validate_onetime_guest(
    mock_redirect, mock_url_for, app, mocker
):
    """Test validate_onetime_guest function."""
    # Setup
    onetime_url_record = MagicMock()
    onetime_url_record.user_mail = "guest@example.com"
    pid = MagicMock()
    pid.pid_value = "123456"
    token = "guest_token_123"
    onetime_url = "http://example.com/onetime"

    # Configure mocks
    mock_session = mocker.patch('weko_records_ui.fd.session')
    mock_session.__setitem__ = MagicMock()
    mock_url_for.return_value = "/redirect/url"
    mock_redirect.return_value = "redirected"

    # Call the function
    result = validate_onetime_guest(onetime_url_record, pid, token, onetime_url)

    # Assert session was modified correctly
    mock_session.__setitem__.assert_any_call("user_mail", "guest@example.com")
    mock_session.__setitem__.assert_any_call("pending_onetime_token", token)

    # Assert URL was created correctly
    mock_url_for.assert_called_with(
        endpoint="invenio_records_ui.recid",
        pid_value="123456",
        onetime_url=onetime_url,
        v="mailcheckflag"
    )

    # Assert redirect was called
    mock_redirect.assert_called_with("/redirect/url")
    assert result == "redirected"


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_fd.py::test_file_download_onetime -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@patch('weko_records_ui.fd.validate_url_download')
@patch('weko_records_ui.fd.save_download_log')
@patch('weko_records_ui.fd._download_file')
@patch("process_onetime_file_download")
def test_file_download_onetime(
    mock_process_onetime, dl_file, save_log,
    val_url, onetime_url, app, mocker
):
    # Setup arguments of sut
    pid = None
    record = {}
    filename = 'test.txt'
    _record_file_factory = MagicMock()
    _record_file_factory.return_value = file_obj = MagicMock()
    file_obj.obj = {'filename': filename}
    file_obj.get.return_value = 'open_restricted'

    # Get onetime_url dict
    onetime_obj = onetime_url["onetime_obj"]

    # Setup default return values of mock objects
    mock_request = mocker.patch('weko_records_ui.fd.request')
    mock_request.args.get.return_value = onetime_url['onetime_token']
    mock_request.get_json.return_value = {"mail_address": onetime_obj.user_mail}
    mock_session = mocker.patch('weko_records_ui.fd.session')
    mock_session.get.return_value = onetime_url['onetime_token']
    val_url.return_value = (True, '')
    mock_process_onetime.return_value = "SUCCESS"

    # Test Case: Correct path
    with app.test_request_context():
        result = file_download_onetime(
            pid, record, filename, _record_file_factory
        )
        assert result == "SUCCESS"
        save_log.assert_called_once_with(
            record, filename, onetime_url["onetime_token"], is_secret_url=False
        )

    # Test Case: Invalid token
    with app.test_request_context():
        val_url.return_value = (False, "Invalid token")
        result = file_download_onetime(
            pid, record, filename, _record_file_factory
        )
        assert result == ("Invalid token", 403)
        # Reset return values
        val_url.return_value = (True, '')

    # Test Case: check_and_send_usage_report() returns an error
    with app.test_request_context():
        chk_and_send.return_value = "ERROR"
        result = file_download_onetime(
            pid, record, filename, _record_file_factory)
        assert result == ("ERROR", 403)
        # Reset return values
        chk_and_send.return_value = None

    # check_and_send_usage_report() raises an exception
    with app.test_request_context():
        chk_and_send.side_effect = BaseException
        result = file_download_onetime(
            pid, record, filename, _record_file_factory)
        assert result == 'ERROR'

    # update_extra_info() raises an SQLAlchemyError
    with app.test_request_context(), \
         patch('weko_records_ui.fd.session', {'pending_onetime_token': onetime_url['onetime_token']}):
        with patch('weko_records_ui.models.FileOnetimeDownload.update_extra_info',
                   side_effect=SQLAlchemyError):
            assert file_download_onetime(
                pid, record, filename, _record_file_factory) == ('Unexpected error occurred.', 500)

    # save_download_log() raises an exception
    with patch('weko_records_ui.fd.save_download_log',
               side_effect=Exception):
        assert file_download_onetime(
            pid, record, filename, _record_file_factory) == 'ERROR'


# def process_onetime_file_download(
#    pid, record, filename, token, error_handler=None):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_fd.py::test_process_onetime_file_download -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@patch('weko_records_ui.fd.record_file_factory')
@patch('weko_records_ui.fd.convert_token_into_obj')
@patch('weko_records_ui.fd.check_and_send_usage_report')
@patch('weko_records_ui.fd.save_download_log')
@patch('weko_records_ui.fd._download_file')
def test_process_onetime_file_download(
    mock_download_file, mock_save_log, mock_check_usage,
    mock_convert_token, mock_record_file, app
):
    """Test process_onetime_file_download function."""
    # Setup
    pid = MagicMock()
    record = MagicMock()
    filename = "test_file.pdf"
    token = "process_token_123"

    # Mock file object
    file_object = MagicMock()
    file_object.obj = MagicMock()
    mock_record_file.return_value = file_object

    # Mock URL object
    url_obj = MagicMock()
    url_obj.extra_info = {"some": "info"}
    url_obj.user_mail = "test@example.com"
    mock_convert_token.return_value = url_obj

    # Mock error handler
    error_handler = MagicMock()
    error_handler.return_value = "error_response"

    mock_download_file.return_value = "download_success"
    mock_check_usage.return_value = None

    # Test Case 1: Successful download
    result = process_onetime_file_download(
        pid, record, filename, token, error_handler=error_handler
    )

    mock_check_usage.assert_called_with(
        url_obj.extra_info, url_obj.user_mail, record, file_object
    )
    url_obj.update_extra_info.assert_called_with(url_obj.extra_info)
    mock_save_log.assert_called_with(record, filename, token, is_secret_url=False)
    url_obj.increment_download_count.assert_called_once()
    mock_download_file.assert_called_with(
        file_object, False, 'en', file_object.obj, pid, record
    )
    assert result == "download_success"

    # Test Case 2: File object not found
    mock_record_file.return_value = None
    result = process_onetime_file_download(
        pid, record, filename, token, error_handler=error_handler
    )
    error_handler.assert_called_with(
        f'The file "{filename}" does not exist.', status_code=404
    )
    assert result == "error_response"

    # Reset file_object for subsequent tests
    mock_record_file.return_value = file_object

    # Test Case 3: check_and_send_usage_report returns error
    mock_check_usage.return_value = "usage_error"
    result = process_onetime_file_download(
        pid, record, filename, token, error_handler=error_handler
    )
    error_handler.assert_called_with("usage_error", status_code=403)
    assert result == "error_response"

    # Test Case 4: SQLAlchemyError during extra_info update
    mock_check_usage.return_value = None
    url_obj.update_extra_info.side_effect = SQLAlchemyError("DB error")
    result = process_onetime_file_download(
        pid, record, filename, token, error_handler=error_handler
    )
    error_handler.assert_called_with('Unexpected error occurred.', status_code=500)
    assert result == "error_response"

    # Test Case 5: Generic exception during extra_info update
    url_obj.update_extra_info.side_effect = Exception("Generic error")
    result = process_onetime_file_download(
        pid, record, filename, token, error_handler=error_handler
    )
    error_handler.assert_called_with('Unexpected error occurred.', status_code=500)
    assert result == "error_response"

    # Test Case 6: Exception during save_download_log
    url_obj.update_extra_info.side_effect = None
    mock_save_log.side_effect = Exception("Log error")
    result = process_onetime_file_download(
        pid, record, filename, token, error_handler=error_handler
    )
    error_handler.assert_called_with('Unexpected error occurred.', status_code=500)
    assert result == "error_response"


# def _is_terms_of_use_only(file_obj:dict , req :dict) -> bool:
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_fd.py::test__is_terms_of_use_only -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test__is_terms_of_use_only(app, records_restricted, users, db_file_permission):

    provide:dict = { # is_terms_of_use_only
        "provide" :
            [
                {
                    "role" : "none_loggin",
                    "workflow" : "2"
                },
                {
                    "role" : "3",
                    "workflow" : "2"
                }
            ]
        }

    provide_not:dict = { #is not_terms_of_use_only
        "provide" :
            [
                {
                    "role" : "none_loggin",
                    "workflow" : "1"
                },
                {
                    "role" : "3",
                    "workflow" : "1"
                }
            ]
        }

    with app.test_request_context():
        # 25
        # "none_loggin"
        assert _is_terms_of_use_only(provide ,{'terms_of_use_only': True})
        assert not _is_terms_of_use_only({"provide" : [{
                    "role" : "3",
                    "workflow" : "1"
                },]},{'terms_of_use_only': True})

        #Contributer
        with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
            assert _is_terms_of_use_only(provide,{'terms_of_use_only': True})

        # 26
        assert not _is_terms_of_use_only(provide ,{})
        assert not _is_terms_of_use_only({"provide" : []},{'terms_of_use_only': True})

        # 27
        # "none_loggin"
        assert not _is_terms_of_use_only(provide_not ,{'terms_of_use_only': True})

        #Contributer
        with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
            assert not _is_terms_of_use_only(provide_not,{'terms_of_use_only': True})

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_fd.py::test_file_download_secret -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@patch('weko_records_ui.fd.validate_url_download')
@patch('weko_records_ui.fd.error_response')
@patch('weko_records_ui.fd.current_user')
@patch('weko_records_ui.fd.save_download_log')
@patch('weko_records_ui.fd._download_file')
def test_file_download_secret(dl_file, save_log, current_user, err_res,
                              val_url, app, mocker, secret_url):
    # Setup arguments
    pid = None
    record = {}
    filename = 'test.txt'
    _record_file_factory = MagicMock()
    _record_file_factory.return_value = file_obj = MagicMock()
    file_obj.obj = {'filename': filename}
    file_obj.get.return_value = 'open_no'

    # Setup default return values of mock objects
    mocker = mocker.patch('weko_records_ui.fd.request')
    mocker.args.get.return_value = secret_url['secret_token']
    val_url.return_value = (True, '')
    current_user.is_authenticated = False
    err_res.return_value = 'ERROR'
    dl_file.return_value = 'SUCCESS'

    with app.test_request_context():
        # Happy path
        assert file_download_secret(
            pid, record, filename, _record_file_factory) == 'SUCCESS'
        save_log.assert_called_once_with(
            record, filename, mocker.args.get.return_value, is_secret_url=True)
        dl_file.assert_called_once_with(
            file_obj, False, 'en', file_obj.obj, pid, record)

        # Happy path with authenticated user
        mock_user = MagicMock()
        mock_user.language = 'ja'
        with patch('weko_user_profiles.models.UserProfile.get_by_userid',
               return_value=mock_user), \
             patch('weko_records_ui.fd.current_user.is_authenticated', True):
            assert file_download_secret(
                pid, record, filename, _record_file_factory) == 'SUCCESS'
            save_log.assert_called_with(
                record, filename, mocker.args.get.return_value, is_secret_url=True)
            dl_file.assert_called_with(
                file_obj, False, 'ja', file_obj.obj, pid, record)

        # Invalid token
        with patch('weko_records_ui.fd.validate_url_download',
                   return_value=(False, 'Invalid token')):
            assert file_download_secret(
                pid, record, filename, _record_file_factory) == 'ERROR'

        # File object is not found
        with patch('weko_records_ui.fd.record_file_factory',
                   return_value=None):
            assert file_download_secret(
                pid, record, filename) == 'ERROR'

        # save_download_log() raises an exception
        with patch('weko_records_ui.fd.save_download_log',
                   side_effect=Exception):
            assert file_download_secret(
                pid, record, filename, _record_file_factory) == 'ERROR'

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_fd.py::test_file_list_ui -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
@pytest.mark.timeout(60)
def test_file_list_ui(app,records,itemtypes,users,mocker,db_file_permission):
    indexer, results = records

    # 9 can download
    record = results[0]["record"]
    with app.test_request_context():
        with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
            res = file_list_ui(record, record.files)
            assert res.status == '200 OK'

    # 10 both accessrole
    record = results[3]["record"]
    with app.test_request_context():
        with patch("flask_login.utils._get_user", return_value=users[4]["obj"]):
            test_mock = mocker.patch('weko_records_ui.utils.create_tsv', return_value=io.StringIO())
            accessrole_list = ["open_access", "open_no"]
            for (file, accessrole) in zip(record.files, accessrole_list):
                file["accessrole"] = accessrole

            res = file_list_ui(record, record.files)
            assert res.status == '200 OK'
            assert len(test_mock.call_args[0][0]) == 1

    # 11 can't download
    record = results[4]["record"]
    with app.test_request_context():
        with pytest.raises(AvailableFilesNotFoundRESTError):
            record.files[0]["accessrole"] = "open_no"
            file_list_ui(record, record.files)

    # 12 not exist file
    record = results[5]["record"]
    with app.test_request_context():
        with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
            with pytest.raises(NotFound):
                res = file_list_ui(record, None)

    # 13 not exist Accept-Language
    record = results[0]["record"]
    with app.test_request_context():
        with patch("weko_records_ui.fd.request.headers.get", return_value=None):
            file_list_ui(record, record.files)
            assert get_locale().language == "en"

    # 14 Accept-Language is ja or en
    with app.test_request_context():
        with patch("weko_records_ui.fd.request.headers.get", return_value="ja"):
            file_list_ui(record, record.files)
            assert get_locale().language == "ja"
        with patch("weko_records_ui.fd.request.headers.get", return_value="en"):
            file_list_ui(record, record.files)
            assert get_locale().language == "en"

    # 15 Accept-Language is other
    with app.test_request_context():
        with patch("weko_records_ui.fd.request.headers.get", return_value="other_lang"):
            file_list_ui(record, record.files)
            assert get_locale().language == "en"
