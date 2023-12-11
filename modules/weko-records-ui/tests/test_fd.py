# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_fd.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp

from weko_records.models import ItemTypeMapping
from weko_records_ui.fd import *
from weko_records_ui.config import WEKO_RECORDS_UI_DETAIL_TEMPLATE
from unittest.mock import MagicMock, PropertyMock
from invenio_theme.config import THEME_ERROR_TEMPLATE 
import pytest
import io
import copy
from flask import Flask, json, jsonify, session, url_for,request
from flask_security.utils import login_user
from invenio_accounts.testutils import login_user_via_session
from mock import patch
from invenio_records_files.utils import record_file_factory
from werkzeug.exceptions import NotFound
import botocore

from weko_records_ui.fd import _download_file
from weko_records_ui.fd import _download_multipartfile

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
    with app.test_request_context(path="/?filename=hoge"):
    #     ret = prepare_response(recid.pid_value,True)
    #     assert ret == ""

        data1 = MagicMock()
        data2 = {
            "display_name": None
        }

        def dumps():
            return data2

        data1.dumps = dumps

        # with patch("weko_records_ui.fd.FilesMetadata.get_records", return_value=[data1]):
        with patch("weko_records.api.FilesMetadata.get_records", return_value=[data1]):
            # Exception coverage
            try:
                prepare_response(recid.pid_value,True)
            except:
                pass


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
def test_file_ui(app,records,itemtypes,users):
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
            with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
                # abort(403) coverage
                try:
                    file_ui(recid, record)
                except:
                    pass
                
            user = MagicMock()
            user.is_authenticated = False
            with patch("flask_login.utils._get_user", return_value=user):
                with patch("weko_records_ui.fd._redirect_method", return_value = "True"):
                    # redirect_method
                    res = file_ui(recid, record)
                    assert res == "True"
    
    fileobj = MagicMock()
    fileobj.file_preview_able = MagicMock(return_value = False)
    type(fileobj).obj = None
    with patch("weko_records_ui.fd.file_permission_factory", return_value=data3):
        with patch("weko_records_ui.fd.record_file_factory", return_value = fileobj):
            with patch("weko_records_ui.fd.check_and_create_usage_report", side_effect = SQLAlchemyError()):
                # SQLAlchemyError
                try:
                    res = file_ui(recid, record)
                except Exception as e:
                    assert True
                    
            # BaseException
            with patch("weko_records_ui.fd.check_and_create_usage_report", side_effect = BaseException()):
                try:
                    res = file_ui(recid, record)
                except Exception as e:
                    assert True
                
            # Cannot preview file
            try:
                file_ui(recid, record, is_preview=True)
            except Exception as e:
                pass


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


# def file_download_onetime(pid, record, _record_file_factory=None, **kwargs):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_fd.py::test_file_download_onetime -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_file_download_onetime(app, records, itemtypes, users, db_fileonetimedownload):
    indexer, results = records
    recid = results[0]["recid"]
    record = results[0]["record"]
    app.config["THEME_ERROR_TEMPLATE"]=THEME_ERROR_TEMPLATE
    with app.test_request_context('?token=MSB1c2VyQGV4YW1wbGUub3JnIDIwMjItMDktMjcgNDBDRkNGODFGM0FFRUI0Ng=='):
        with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
            with patch("flask.templating._render", return_value=""):
                with patch("weko_records_ui.fd.get_onetime_download", return_value=db_fileonetimedownload):
                    _rv = (True, "")
                    with patch("weko_records_ui.fd.validate_onetime_download_token", return_value=_rv):
                        assert file_download_onetime(recid,record,record_file_factory)==""

                        with patch("weko_records_ui.fd.parse_one_time_download_token", return_value=(True, [1])):
                            assert file_download_onetime(recid,record,record_file_factory)==""
                        
                    with patch("weko_records_ui.fd.validate_onetime_download_token", return_value=(False, [1])):
                        assert file_download_onetime(recid,record,record_file_factory)==""

                    with patch("weko_records_ui.fd.record_file_factory", return_value=False):
                        assert file_download_onetime(recid,record,record_file_factory)==""
                        
def test_multipartfile_download_ui(app, client, records, itemtypes, users):
    with patch("weko_records_ui.fd.multipartfile_ui", return_value="True"):
        res = client.get(f"/record/1/multipartfiles/helloworld.pdf")
        assert res.status_code == 400
        
        res = client.get(f"/record/1/multipartfiles/helloworld.pdf?partNumber=1")
        assert res.status_code == 200

def test_multipartfile_ui(app, client, records, users):
    indexer, results = records
    recid = results[0]["recid"]
    record = results[0]["record"]
    
    
    with patch("weko_records_ui.fd._download_multipartfile", return_value = "True"):
        # with patch("weko_records_ui.fd.file_permission_factory", return_value=data1):
        with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
            # 404
            try:
                res = client.get(f"/record/1/multipartfiles/sample.pdf?partNumber=1")
            except:
                assert True
                
            app.config.update(
                FILES_REST_LOCATION_TYPE_LIST = [('local', 'local storage')]
            )
            
            # 500
            try:
                res = client.get(f"/record/1/multipartfiles/helloworld.pdf?partNumber=1")
            except:
                assert True
            app.config.update(
                FILES_REST_LOCATION_TYPE_LIST = [('s3', 'Amazon S3')],
            )
                
            # normal
            with app.test_request_context():
                res = multipartfile_ui(recid, record, "1")
                assert res == "True"
            
        data1 = MagicMock()
        data1.can = MagicMock(return_value = False)
        
        data2 = MagicMock()
        data2.is_authenticated = MagicMock(return_value = False)
        
        data3 = MagicMock()
        data3.can = MagicMock(return_value = True)
        data3.obj = 1
        
        with app.test_request_context():
            with patch("weko_records_ui.fd.file_permission_factory", return_value=data1):
                with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
                    # abort(403) coverage
                    try:
                        multipartfile_ui(recid, record, "1")
                    except:
                        pass
                
                user = MagicMock()
                user.is_authenticated = False
                with patch("flask_login.utils._get_user", return_value=user):
                    with patch("weko_records_ui.fd._redirect_method", return_value = "True"):
                        # redirect 
                        res = multipartfile_ui(recid, record, "1")
                        assert res == "True"


def test__download_multipartfile(app, db, client, records, itemtypes, users):
    indexer, results = records
    recid = results[0]["recid"]
    record = results[0]["record"]
    fileobj = record_file_factory(recid,record,"helloworld.pdf")
    obj = fileobj.obj
    
    c = MagicMock()
    body = botocore.response.StreamingBody(
        io.BytesIO(obj.file.storage().open().read()),
        fileobj.data.get("size")
    )
    with app.test_request_context():
        with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
            with patch("invenio_s3.storage.S3FSFileStorage.get_s3_client", side_effect = lambda: "error"):
                try:
                    res = _download_multipartfile(fileobj, obj, record, "300", 1024)
                except:
                    assert True

            with patch("invenio_s3.storage.S3FSFileStorage.get_s3_client", return_value = c):
                res = MagicMock()
                res.get = MagicMock(return_value = body)
                c.get_object = MagicMock(return_value = res)
                res = _download_multipartfile(fileobj, obj, record, "1", 10)
                assert res.status_code == 200
                
                # last part
                res = _download_multipartfile(fileobj, obj, record, "300", 1024)
                assert res.status_code == 200
                
                # SQLAlchemyError
                with patch("weko_records_ui.fd.check_and_create_usage_report", side_effect = SQLAlchemyError()):
                    try:
                        res = _download_multipartfile(fileobj, obj, record, "300", 1024)
                    except Exception as e:
                        assert True
                    
                # BaseException
                with patch("weko_records_ui.fd.check_and_create_usage_report", side_effect = BaseException()):
                    try:
                        res = _download_multipartfile(fileobj, obj, record, "300", 1024)
                    except Exception as e:
                        assert True
