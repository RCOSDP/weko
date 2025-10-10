# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_admin.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp

from unittest.mock import MagicMock
import pytest
import io
from flask import Flask, json, jsonify, session, url_for
from flask_security.utils import login_user
from invenio_accounts.testutils import login_user_via_session
from mock import patch
from invenio_pidstore.errors import PIDDoesNotExistError
from weko_records_ui.models import PDFCoverPageSettings

# class ItemSettingView(BaseView):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_admin.py::test_check_open_restricted_permission -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
class TestItemSettingView():
#     def index(self):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_admin.py::TestItemSettingView::test_index_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
    def test_index_acl(self,client,db_sessionlifetime,users):
        url = url_for("itemsetting.index", _external=True)
        res = client.get(url)
        assert res.status == '302 FOUND'

        with patch("flask_login.utils._get_user", return_value=users[1]['obj']):
            with patch("flask.templating._render", return_value=""):
                res = client.get(url)
                assert res.status == '200 OK'
        
        with patch("flask_login.utils._get_user", return_value=users[1]['obj']):
            with patch("flask.templating._render", return_value=""):
                res = client.post(url)
                assert res.status == '200 OK'

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_admin.py::TestItemSettingView::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
    def test_index(self,app,client,db_sessionlifetime,users,db_admin_settings):
        url = url_for("itemsetting.index", _external=True)
        with patch("flask_login.utils._get_user", return_value=users[1]['obj']):
            with patch("flask.templating._render", return_value=""):
                data = {"submit": "a"}
                res = client.post(url,data=data)
                assert res.status == '200 OK'

                with patch("weko_records_ui.admin.check_items_settings", side_effect = BaseException()):
                    res = client.post(url,data=data)
                    assert res.status == '400 BAD REQUEST'
        
                data = {"submit": "set_search_author_form","displayRadios":"1", "openDateDisplayRadios":"1"}
                res = client.post(url,data=data)
                assert res.status == '200 OK'


                data = {"submit": "set_search_author_form","displayRadios":"1", "openDateDisplayRadios":"0"}
                res = client.post(url,data=data)
                assert res.status == '200 OK'

                data = {"submit": "set_search_author_form","displayRadios":"0", "openDateDisplayRadios":"1"}
                res = client.post(url,data=data)
                assert res.status == '200 OK'

                data = {"submit": "set_search_author_form","displayRadios":"0", "openDateDisplayRadios":"0"}
                res = client.post(url,data=data)
                assert res.status == '200 OK'

                data = {"submit": "set_search_author_form","displayRadios":"0"}
                res = client.post(url,data=data)
                assert res.status == '200 OK'

                data = {"submit": "set_search_author_form","openDateDisplayRadios":"0"}
                res = client.post(url,data=data)
                assert res.status == '200 OK'


# class PdfCoverPageSettingView(BaseView):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_admin.py::TestPdfCoverPageSettingView -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
class TestPdfCoverPageSettingView():
#     def index(self):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_admin.py::TestPdfCoverPageSettingView::test_index_eror -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
    def test_index_error(self,client,db_sessionlifetime,users):
        url = url_for("pdfcoverpage.index", _external=True)
        res = client.get(url)
        assert res.status == '302 FOUND'

        with patch("flask_login.utils._get_user", return_value=users[1]['obj']):
            with patch("flask.templating._render", return_value=""):
                with patch('weko_records_ui.admin.db.session.commit') as m:
                    m.side_effect = Exception('')
                    res = client.get(url)
                    assert PDFCoverPageSettings.find(1) == None

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_admin.py::TestPdfCoverPageSettingView::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
    def test_index(self,client,db_sessionlifetime,users):
        url = url_for("pdfcoverpage.index", _external=True)
        res = client.get(url)
        assert res.status == '302 FOUND'
        with patch("flask_login.utils._get_user", return_value=users[1]['obj']):
            with patch("flask.templating._render", return_value=""):
                res = client.get(url)
                assert res.status == '200 OK'
                assert PDFCoverPageSettings.find(1) is not None

                res = client.get(url)
                assert res.status == '200 OK'

# class InstitutionNameSettingView(BaseView):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_admin.py::TestInstitutionNameSettingView -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
class TestInstitutionNameSettingView:
#     def index(self):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_admin.py::TestInstitutionNameSettingView::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
    def test_index(self,client,db_sessionlifetime,users):
        url = url_for("others.index", _external=True)
        res = client.get(url)
        assert res.status == '302 FOUND'

        with patch("flask_login.utils._get_user", return_value=users[1]['obj']):
            with patch("flask.templating._render", return_value=""):
                res = client.get(url)
                assert res.status == '200 OK'
        
        data = {"institution_name": "test"}
        with patch("flask_login.utils._get_user", return_value=users[1]['obj']):
            with patch("flask.templating._render", return_value=""):
                res = client.post(url,data=data)
                assert res.status == '200 OK'

# class ItemManagementBulkUpdate(BaseView):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_admin.py::TestItemManagementBulkUpdate -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
class TestItemManagementBulkUpdate:
#     def index(self):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_admin.py::TestItemManagementBulkUpdate::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
    def test_index(self,client,db_sessionlifetime,users):
        url = url_for("items/bulk/update.index", _external=True)
        with patch("weko_records_ui.views.get_search_detail_keyword", return_value={}):
            res = client.get(url)
            assert res.status == '302 FOUND'

            with patch("flask_login.utils._get_user", return_value=users[0]['obj']):
                with patch("flask.templating._render", return_value=""):
                    res = client.get(url)
                    assert res.status == '403 FORBIDDEN'
            
            with patch("flask_login.utils._get_user", return_value=users[1]['obj']):
                with patch("flask.templating._render", return_value=""):
                    res = client.get(url)
                    assert res.status == '200 OK'
        
#     def get_items_metadata(self):
#         def get_file_data(meta):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_admin.py::TestItemManagementBulkUpdate::test_get_items_metadata_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
    def test_get_items_metadata_acl(self,client,db_sessionlifetime,users):
        url = url_for("items/bulk/update.get_items_metadata", _external=True)
        res = client.get(url)
        assert res.status == '302 FOUND'

        with patch("flask_login.utils._get_user", return_value=users[0]['obj']):
            with patch("flask.templating._render", return_value=""):
                res = client.get(url)
                assert res.status == '403 FORBIDDEN'
        
        with patch("flask_login.utils._get_user", return_value=users[1]['obj']):
            res = client.get(url)
            assert res.status == '200 OK'

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_admin.py::TestItemManagementBulkUpdate::test_get_items_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
    def test_get_items_metadata(self,client,db_sessionlifetime,users,records):
        indexer, results = records
        url = url_for("items/bulk/update.get_items_metadata", pids="1",_external=True)
        with patch("flask_login.utils._get_user", return_value=users[1]['obj']):
            res = client.get(url)
            assert res.status == '200 OK'
            data = json.loads(res.data)
            assert data['1']["contents"]=={'item_1617605131499': [{'accessrole': 'open_access', 'date': [{'dateType': 'Available', 'dateValue': '2021-07-12'}], 'displaytype': 'simple', 'filename': 'helloworld.pdf', 'filesize': [{'value': '1 KB'}], 'format': 'application/pdf', 'mimetype': 'application/pdf', 'url': {'url': 'https://localhost/record/1/files/helloworld.pdf'}, 'version_id': 'c1502853-c2f9-455d-8bec-f6e630e54b21'}]}


        url = url_for("items/bulk/update.get_items_metadata", pids="1/2/3",_external=True)
        with patch("flask_login.utils._get_user", return_value=users[1]['obj']):
            res = client.get(url)
            assert res.status == '200 OK'
            data = json.loads(res.data)
            assert data['1']
            assert data['2']
            assert data['3']
    
        url = url_for("items/bulk/update.get_items_metadata", pids="",_external=True)
        with patch("flask_login.utils._get_user", return_value=users[1]['obj']):
            with pytest.raises(PIDDoesNotExistError):
                    res = client.get(url)

        # record.get('path') is not list
        record = results[0]['record']
        record['path'] = ""
        url = url_for("items/bulk/update.get_items_metadata", pids="1",_external=True)
        with patch("flask_login.utils._get_user", return_value=users[1]['obj']):
            with patch("weko_deposit.api.WekoRecord.get_record_by_pid", return_value=record):
                res = client.get(url)
        
        # meta is None
        url = url_for("items/bulk/update.get_items_metadata", pids="1",_external=True)
        with patch("flask_login.utils._get_user", return_value=users[1]['obj']):
            with patch("weko_deposit.api.ItemsMetadata.get_record", return_value=None):
                res = client.get(url)

        meta = {"A":"","B":[],"C":[{"a":""},{"filename":"helloworld.pdf"}]}
        url = url_for("items/bulk/update.get_items_metadata", pids="1",_external=True)
        with patch("flask_login.utils._get_user", return_value=users[1]['obj']):
            with patch("weko_deposit.api.ItemsMetadata.get_record", return_value=meta):
                res = client.get(url)