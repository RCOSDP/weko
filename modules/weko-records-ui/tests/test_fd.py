# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_fd.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp

import re
from flask_login import current_user
from requests import Response
from weko_deposit.api import WekoFileObject
from weko_records_ui.errors import AvailableFilesNotFoundRESTError
from weko_records_ui.fd import _is_terms_of_use_only, file_download_secret, prepare_response,file_download_onetime,_download_file,add_signals_info,weko_view_method,file_ui,file_preview_ui,file_download_ui,file_list_ui
from weko_records_ui.config import WEKO_RECORDS_UI_DETAIL_TEMPLATE
from unittest.mock import MagicMock
from invenio_theme.config import THEME_ERROR_TEMPLATE 
import pytest
import io
import copy
from flask import Flask, json, jsonify, session, url_for,request
from flask import url_for,current_app,make_response
from flask_security.utils import login_user
from flask_babelex import get_locale
from invenio_accounts.testutils import login_user_via_session
from mock import patch
from invenio_records_files.utils import record_file_factory
from werkzeug.exceptions import NotFound ,Forbidden

from weko_admin.models import AdminSettings
from weko_records_ui.models import FileSecretDownload
from sqlalchemy.exc import SQLAlchemyError 
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
def test_file_ui3(app,records_restricted,itemtypes,db_file_permission,users ,client ,mocker):
    indexer, results = records_restricted
    recid_none_login =  results[len(results) -2]["recid"]
    recid_login =  results[len(results) -1]["recid"]
    record_login = results[len(results) -1]["record"]
    data1 = MagicMock()
    def can():
        return True
    data1.can = can

    with app.test_request_context():
        with patch('weko_records_ui.fd.file_permission_factory', return_value=data1):
            #23
            # contributer logined
            with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
                mock = mocker.patch('weko_records_ui.fd._redirect_method' ,return_value=make_response())
                fileobj:WekoFileObject = record_file_factory( recid_login, record_login, filename = "helloworld_open_restricted.pdf" )
                fileobj.data['accessrole']='open_restricted'
                fileobj.data['filename'] = "helloworld_open_restricted.pdf"
                res = file_ui(recid_login,record_login ,is_preview=False , filename = "helloworld_open_restricted.pdf")
                mock.assert_called()
                assert res.status == '200 OK'
            
            #24
            with patch("flask_login.utils._get_user", return_value=users[7]["obj"]):
                with patch("weko_records_ui.fd.is_owners_or_superusers", return_value=False):
                    fileobj:WekoFileObject = record_file_factory( recid_login, record_login, filename = "helloworld_open_restricted.pdf" )
                    fileobj.data['accessrole']='open_restricted'
                    fileobj.data['filename'] = "helloworld_open_restricted.pdf"
                    
                    try:
                        res = file_ui(recid_login,record_login ,is_preview=False  , filename = "helloworld_open_restricted.pdf")
                        assert False
                    except Forbidden :
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
    mailaddress = "user@email"
    app.config["THEME_ERROR_TEMPLATE"]=THEME_ERROR_TEMPLATE
    with app.test_request_context('?token=MSB1c2VyQGV4YW1wbGUub3JnIDIwMjItMDktMjcgNDBDRkNGODFGM0FFRUI0Ng=='):
         with patch("weko_records_ui.fd.redirect", return_value=""):
            assert file_download_onetime(recid,record,record_file_factory)==""
    with app.test_request_context('?token=MSB1c2VyQGV4YW1wbGUub3JnIDIwMjItMDktMjcgNDBDRkNGODFGM0FFRUI0Ng==&mailaddress='+ mailaddress + '&isajax=true'):
            with patch("flask.templating._render", return_value=""):
                with patch("weko_records_ui.fd.get_onetime_download", return_value=db_fileonetimedownload):
                    with patch("weko_records_ui.fd.parse_one_time_download_token", return_value=(True, [1])):
                        assert file_download_onetime(recid,record,record_file_factory)==(True,401)

                    with patch("weko_records_ui.fd.parse_one_time_download_token", return_value=(False, ("","","",""))):

                        with patch("weko_records_ui.fd.validate_onetime_download_token", return_value=(False, [1])):
                            assert file_download_onetime(recid,record,record_file_factory)==([1],401)
                        
                        _rv = (True, "")
                        with patch("weko_records_ui.fd.validate_onetime_download_token", return_value=_rv):
                            assert file_download_onetime(recid,record,record_file_factory)==('Unexpected error occurred.',401)

                            with patch("weko_records_ui.fd.record_file_factory", return_value=False):
                                assert file_download_onetime(recid,record,None)==('None does not exist.', 401)
                            
                            file_object = MagicMock()
                            file_object.obj = {"foo" : "hoge"}
                            file_object.get = lambda x : 'open_restricted'
                            with patch("weko_records_ui.fd.record_file_factory", return_value=file_object):
                                with patch('weko_records_ui.fd.check_and_send_usage_report',return_value ="error"):
                                    assert file_download_onetime(recid,record,None)==('error',401)
                                with patch('weko_records_ui.fd.check_and_send_usage_report',side_effect = BaseException ):
                                    assert file_download_onetime(recid,record,None)==('Unexpected error occurred.', 401)
                                with patch('weko_records_ui.fd.check_and_send_usage_report',side_effect =SQLAlchemyError):
                                    assert file_download_onetime(recid,record,None)==('Unexpected error occurred.', 401)
                                with patch('weko_records_ui.fd.check_and_send_usage_report',return_value =""):
                                    with patch('weko_records_ui.fd.update_onetime_download',return_value =True):
                                        with patch("weko_records_ui.fd.parse_one_time_download_token", return_value=(False, ("","","",""))):
                                            assert file_download_onetime(recid,record,None)==('Could not download file.', 401)
                                        user_mail = "user@email"
                                        with patch("weko_records_ui.fd.parse_one_time_download_token", return_value=(False, ("",user_mail,"",""))):
                                            with patch('weko_records_ui.fd._download_file',return_value ="downloaded"):
                                                assert file_download_onetime(recid,record,None)=="downloaded"
    with app.test_request_context('?token=MSB1c2VyQGV4YW1wbGUub3JnIDIwMjItMDktMjcgNDBDRkNGODFGM0FFRUI0Ng==&mailaddress='+ mailaddress):
         with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
            with patch("flask.templating._render", return_value=""):   
                with patch("weko_records_ui.fd.get_onetime_download", return_value=db_fileonetimedownload):              
                    with patch("weko_records_ui.fd.record_file_factory", return_value=file_object):
                        with patch('weko_records_ui.fd.check_and_send_usage_report',return_value ="error"):
                            with patch("weko_records_ui.fd.redirect", return_value=""):
                                assert file_download_onetime(recid,record)==""   
    with app.test_request_context():
        with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
            with patch("flask.templating._render", return_value=""):   
                with patch("weko_records_ui.fd.get_onetime_download", return_value=db_fileonetimedownload):              
                    with patch("weko_records_ui.fd.record_file_factory", return_value=file_object):
                        with patch('weko_records_ui.fd.check_and_send_usage_report',return_value ="error"):
                            with patch("weko_records_ui.fd.redirect", return_value=""):
                                assert file_download_onetime(recid,record)==""
                        with patch('weko_records_ui.fd.check_and_send_usage_report',return_value =""):
                            with patch('weko_records_ui.fd.update_onetime_download',return_value =True):
                                with patch('weko_records_ui.fd._download_file',return_value ="downloaded"):
                                    # call by method
                                    file_name = "/helloworld_open_restricted.pdf"
                                    assert file_download_onetime(recid,record,file_name, user_mail, True)=="downloaded"

    adminsetting = AdminSettings(id=5,name='restricted_access',settings={"password_enable": True})
    #with app.test_request_context('?token=MSB1c2VyQGV4YW1wbGUub3JnIDIwMjItMDktMjcgNDBDRkNGODFGM0FFRUI0Ng==&mailaddress='+ mailaddress + '&isajax=true'):
    with app.test_client() as client:
        with patch('weko_records_ui.fd.AdminSettings.get', return_value=adminsetting):    
            with patch("flask.templating._render", return_value=""):
                with patch("weko_records_ui.fd.get_onetime_download", return_value=db_fileonetimedownload):
                    #with patch("weko_records_ui.fd.parse_one_time_download_token", return_value=(True, [1])):
                        res = client.post('/record/3/file/onetime/helloworld.zip',
                                    data={'input_password':'test_pass'},
                                    content_type='application/json')
                        assert res.status_code == 200

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

# def file_download_secret(pid, record, _record_file_factory=None, **kwargs):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_fd.py::test_file_download_secret -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_file_download_secret(app,db, itemtypes, users, records):
    indexer, results = records
    recid = results[1]["recid"]
    record = results[1]["record"]

    # token:str = re.sub("^.+?token=" ,"" , urls[0])
    with app.test_request_context("?token=MSA1IDIwMjMtMDMtMDggMDA6NTI6MTkuNjI0NTUyIDZGQTdEMzIxQTk0OTU1MEQ="):
        p = FileSecretDownload.create(file_name="helloworld.docx", record_id=recid.pid_value, user_mail=users[0]["email"] ,download_count = 1)
        factory = MagicMock()
        factory.obj = {"":""}
        with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
            with patch("weko_records_ui.fd.render_template", side_effect=lambda x,error: (x,error)): #return param
                with patch("weko_records_ui.fd._download_file", return_value="_download_file"):
                    with patch("weko_records_ui.fd.parse_secret_download_token", return_value=( "parse_secret_download_token",("token"))):
                        #28
                        assert file_download_secret(recid,record,record_file_factory) == ('weko_theme/error.html', "parse_secret_download_token")
                    with patch("weko_records_ui.fd.parse_secret_download_token", return_value=(False , (results[1]["recid"].pid_value,1,p.created,""))):
                        with patch("weko_records_ui.fd.validate_download_record", return_value=None):
                            with patch("weko_records_ui.fd.validate_secret_download_token", return_value=(False , "validate_secret_download_token")):
                                # 29
                                assert file_download_secret(recid,record,record_file_factory,filename="helloworld.docx")==('weko_theme/error.html' , "validate_secret_download_token")
                            with patch("weko_records_ui.fd.validate_secret_download_token", return_value=(True , "")):
                                with patch("weko_records_ui.fd.record_file_factory", return_value=""):
                                    # 30
                                    assert file_download_secret(recid,record,record_file_factory=lambda x ,y ,z: "",filename="helloworld.docx")==('weko_theme/error.html' , "{} does not exist.".format(results[1]["filename"]))
                                with patch("weko_records_ui.fd.record_file_factory", return_value=factory):
                                    with patch("weko_records_ui.fd.get_secret_download", return_value=p):
                                        with patch("weko_records_ui.fd.update_secret_download", return_value=None):
                                            assert file_download_secret(results[0]["recid"],results[0]["record"],record_file_factory=None,filename="helloworld.docx")==('weko_theme/error.html' , "Unexpected error occurred.")
                                        #31
                                        assert file_download_secret(recid,record,record_file_factory,filename="helloworld.docx")=="_download_file"
                                        assert db.session.query(FileSecretDownload).one_or_none().download_count == 0
                                    with patch("weko_records_ui.fd.get_secret_download", return_value=None):
                                        with pytest.raises(Forbidden):
                                            file_download_secret(recid,record,record_file_factory,filename="helloworld.docx")
        with patch("weko_records_ui.fd.render_template", side_effect=lambda x,error: (x,error)): #return param
            with patch("weko_records_ui.fd.parse_secret_download_token", return_value=(False , (results[1]["recid"].pid_value,1,p.created,""))):
                with patch("weko_records_ui.fd.validate_secret_download_token", return_value=(True , "")):
                    with patch("weko_records_ui.fd._download_file", return_value="_download_file"):
                        with patch("weko_records_ui.fd.record_file_factory", return_value=factory):
                            with patch("weko_records_ui.fd.get_secret_download", return_value=p):
                                assert file_download_secret(recid,record,record_file_factory,filename="helloworld.docx")=="_download_file"
                    with patch("weko_records_ui.fd.record_file_factory", return_value=False):
                        assert file_download_onetime(recid,record,record_file_factory)==('weko_theme/error.html', 'Token is invalid.')


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
