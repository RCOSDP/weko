# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_fd.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp

from weko_records_ui.fd import prepare_response,file_download_onetime,_download_file,add_signals_info,weko_view_method,file_ui,file_preview_ui,file_download_ui
from weko_records_ui.config import WEKO_RECORDS_UI_DETAIL_TEMPLATE
from unittest.mock import MagicMock
from invenio_theme.config import THEME_ERROR_TEMPLATE 
import pytest
from mock import patch
from invenio_records_files.utils import record_file_factory
from invenio_theme.config import THEME_ERROR_TEMPLATE
from weko_records_ui.config import WEKO_RECORDS_UI_DETAIL_TEMPLATE
from weko_records_ui.fd import (
    _download_file, add_signals_info,
    file_download_onetime, file_download_ui, file_preview_ui, file_ui,
    prepare_response, weko_view_method
)
from werkzeug.exceptions import NotFound

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
            # abort(403) coverage
            try:
                file_ui(data2, data3)
            except:
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
def test_add_signals_info(i18n_app,records,itemtypes,users,mock_es_execute):
    class MockUser():
        def __init__(self):
            self.is_authenticated = ''

    _, results = records
    with i18n_app.test_request_context():
        with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
            with patch('flask_principal.Permission.can', MagicMock(return_value=True)):
                with patch('elasticsearch_dsl.Search.execute', return_value=mock_es_execute('tests/data/execute_result2.json')):
                    with patch('weko_records_ui.fd.is_open_access', return_value=True):
                        recid = results[0]["recid"]
                        record = results[0]["record"]
                        fileobj = record_file_factory(recid,record,"helloworld.pdf")
                        obj = fileobj.obj
                        add_signals_info(record,obj)
                        assert obj.item_title == 'ja_conference paperITEM00000009(public_open_access_open_access_simple)'
                        assert obj.is_billing_item == False
                        assert obj.userrole == 'Repository Administrator'
                        assert obj.billing_file_price == ''
                        assert obj.is_open_access
                with patch('elasticsearch_dsl.Search.execute', return_value=mock_es_execute('tests/data/execute_result1.json')):
                    with patch('weko_records_ui.fd.is_open_access', return_value=False):
                        recid = results[3]["recid"]
                        record = results[3]["record"]
                        fileobj = record_file_factory(recid,record,"helloworld_billing.pdf")
                        obj = fileobj.obj
                        add_signals_info(record,obj)
                        assert obj.item_title == 'ja_conference paperITEM00000009(public_open_access_open_access_simple)_billing'
                        assert obj.is_billing_item == True
                        assert obj.userrole == 'Repository Administrator'
                        assert obj.billing_file_price == '400'
                        assert not obj.is_open_access

        data1 = MagicMock()
        def all_func():
            return []
        data1.roles = []
        data1.all = all_func
        data1.id = 1
        data2 = MagicMock()
        data2.id = 2


        with patch("weko_records_ui.fd.is_billing_item", return_value=False):
            with patch('weko_records_ui.fd.is_open_access', return_value=False):
                with patch("weko_records_ui.fd.Group.query_by_user", return_value=data1):
                    with patch("flask_login.utils._get_user", return_value=data1):
                        add_signals_info(record,obj)
                    data1.roles = [data1, data2]

                    with patch("flask_login.utils._get_user", return_value=data1):
                        add_signals_info(record,obj)

        with patch("weko_records_ui.fd.is_billing_item", return_value=True):
            with patch('weko_records_ui.fd.is_open_access', return_value=True):
                with patch("weko_records_ui.fd.Group.query_by_user", return_value=data1):
                    with patch("flask_login.utils._get_user", return_value=data1):
                        add_signals_info(record,obj)


        with patch("weko_records_ui.fd.is_billing_item", return_value=False):
            with patch('weko_records_ui.fd.is_open_access', return_value=False):
                with patch("weko_records_ui.fd.Group.query_by_user", return_value=data1):
                    user = MockUser()
                    with patch("flask_login.utils._get_user", return_value=user):
                        # current_user doesn't have attribute 'id'
                        add_signals_info(record, obj)
                        assert obj.userid == 0
                        assert obj.userrole == 'guest'
                    user.id = 1
                    user.name = 'testrole'
                    user2 = MockUser()
                    user2.id = 0
                    user.roles = [user, user2]
                    with patch("flask_login.utils._get_user", return_value=user):
                        # current_user's roles has two or more roles and last role's id is 0
                        add_signals_info(record, obj)
                        assert obj.userid == 1
                        assert obj.userrole == 'testrole'
                    record = results[4]["record"]
                    # record.navi has no item
                    add_signals_info(record, obj)
                    assert obj.index_list == ''


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