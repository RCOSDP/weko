import codecs
import io
import csv
import os
import json
import pytest
from mock import patch, MagicMock, Mock
from flask_login import current_user
from mock import patch
from jinja2.exceptions import TemplateNotFound
from flask import Flask, json, jsonify, session, url_for,current_app, make_response, request

from invenio_accounts.testutils import login_user_via_session

from weko_index_tree.models import Index
from weko_search_ui.admin import (
    ItemManagementBulkDelete,
    ItemManagementCustomSort,
    ItemManagementBulkSearch,
    ItemImportView,
    ItemBulkExport
)


# class ItemManagementBulkDelete(BaseView):
#     def index(self):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_admin.py::test_ItemManagementBulkDelete_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_ItemManagementBulkDelete_index(i18n_app, es, users, indices):
    i18n_app.config['WEKO_SEARCH_TYPE_INDEX'] = 'index'
    with i18n_app.test_client() as client:
        with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
            with pytest.raises(Exception) as e:
                res = client.get("/admin/items/bulk/delete/",
                                content_type="application/json")
                assert e.type==TemplateNotFound
        with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
            with patch('weko_search_ui.admin.get_doi_items_in_index', return_value=[1]):
                with patch('weko_search_ui.admin.get_editing_items_in_index', return_value=[2]):
                    with patch('weko_search_ui.admin.delete_records', return_value=[]):
                        res = client.put("/admin/items/bulk/delete/?recursively=true&q=33",
                                        content_type="application/json")
                        assert res.status_code==200

#     def check(self):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_admin.py::test_ItemManagementBulkDelete_check -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_ItemManagementBulkDelete_check(i18n_app, users,db_records2):
    import secrets
    i18n_app.config['WEKO_SEARCH_TYPE_INDEX'] = 'index'
    currect_token = secrets.token_hex()
    with i18n_app.test_client() as client:
        with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
            res = client.get("/admin/items/bulk/delete/check",
                             content_type="application/json",
                             headers={"X-CSRFToken":currect_token})
            assert res.status_code==200
            res = client.get("/admin/items/bulk/delete/check?q=33",
                            content_type="application/json",
                             headers={"X-CSRFToken":currect_token})
            assert res.status_code==200
            with patch('weko_search_ui.admin.is_index_locked', return_value=False):
                with patch('weko_search_ui.admin.get_doi_items_in_index', return_value=[1]):
                    res = client.get("/admin/items/bulk/delete/check?q=33",
                                    content_type="application/json",
                                    headers={"X-CSRFToken":currect_token})
                    assert res.status_code==200
                with patch('weko_search_ui.admin.get_doi_items_in_index', return_value=[]):
                    res = client.get("/admin/items/bulk/delete/check?q=33",
                                    content_type="application/json",
                                    headers={"X-CSRFToken":currect_token})
                    assert res.status_code==200


# class ItemManagementCustomSort(BaseView):
class TestItemManagementCustomSort:
    # .tox/c1/bin/pytest --cov=weko_search_ui tests/test_admin.py::TestItemManagementCustomSort::test_index_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
    def test_index_acl(self,client, users, db_records2):
        user = users[3]['obj']
        assert user.roles[0].name=='System Administrator' 
        
        url = url_for("items/custom_sort.index", _external=True)
        with patch("flask.templating._render", return_value=""):
            res = client.get(url)
            assert res.status == '302 FOUND'

        with patch("flask_login.utils._get_user", return_value=user):
            with patch("flask.templating._render", return_value=""):
                res = client.get(url)
                assert res.status == '200 OK'

#     def save_sort(self): ~ GOOD
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_admin.py::test_ItemManagementCustomSort_save_sort -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_ItemManagementCustomSort_save_sort(i18n_app, users, db_records2):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        test = ItemManagementCustomSort()
        with patch("flask.templating._render", return_value=""):
            assert test.save_sort()

        with patch.object(request, "get_json", return_value={"q_id": "1", "sort": [{"custom_sort": {"1": 1}}, {"custom_sort": {"2": 2}}]}):
            with patch("weko_index_tree.api.Indexes.set_item_sort_custom", return_value=Index(id=1)):
                res = test.save_sort()
                res_data = json.loads(res.get_data(as_text=True))
                assert res.status_code == 200
                assert res_data["message"] == "Data is successfully updated."

            with patch("weko_index_tree.api.Indexes.set_item_sort_custom", return_value=None):
                res = test.save_sort()
                res_data = json.loads(res.get_data(as_text=True))
                assert res.status_code == 405
                assert res_data["message"] == "Data update failed."

            with patch("weko_index_tree.api.Indexes.set_item_sort_custom", side_effect=Exception):
                res = test.save_sort()
                res_data = json.loads(res.get_data(as_text=True))
                assert res.status_code == 405
                assert res_data["message"] == "Error."


# class ItemManagementBulkSearch(BaseView):
class TestItemManagementBulkSearch:
    # .tox/c1/bin/pytest --cov=weko_search_ui tests/test_admin.py::TestItemManagementBulkSearch::test_index_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
    def test_index_acl(self,client, users, db_records2):
        user = users[3]['obj']
        assert user.roles[0].name=='System Administrator' 
        
        url = url_for("items/search.index", _external=True)
        with patch("flask.templating._render", return_value=""):
            res = client.get(url)
            assert res.status == '302 FOUND'

        with patch("flask_login.utils._get_user", return_value=user):
            with patch("flask.templating._render", return_value=""):
                res = client.get(url, query_string={"item_management": "update"})
                assert res.status == '200 OK'

    # .tox/c1/bin/pytest --cov=weko_search_ui tests/test_admin.py::TestItemManagementBulkSearch::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
    def test_index(self, i18n_app, users, indices2, mocker):
        i18n_app.config['WEKO_SEARCH_TYPE_INDEX'] = 'index'
        user = users[3]['obj']

        with i18n_app.test_client() as client:
            url = url_for("items/search.index", _external=True)
            with patch("flask_login.utils._get_user", return_value=user):
                with patch("flask.templating._render", return_value=""):
                    mock_execute_search_with_pagination = mocker.patch("weko_search_ui.utils.execute_search_with_pagination")
                    mock_execute_search_with_pagination.return_value = []
                    
                    # management_type is bulk delete
                    res = client.get(url, query_string={"item_management": "delete", "q": 3})
                    assert res.status == '200 OK'

                    # management_type is bulk update
                    res = client.get(url, query_string={"item_management": "update"})
                    assert res.status == '200 OK'
                    
                    # management_type is not found
                    res = client.get(url)
                    assert res.status == '500 INTERNAL SERVER ERROR'


#     def is_visible(): ~ GOOD
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_admin.py::test_ItemManagementBulkSearch_is_visible -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_ItemManagementBulkSearch_is_visible(i18n_app, users, db_records2):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        test = ItemManagementBulkSearch()
        assert not test.is_visible()


# class ItemImportView(BaseView):
class TestItemImportView:
    # .tox/c1/bin/pytest --cov=weko_search_ui tests/test_admin.py::TestItemImportView::test_index_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
    def test_index_acl(self,client, users, db_records2):
        user = users[3]['obj']
        assert user.roles[0].name=='System Administrator' 
        
        url = url_for("items/import.index", _external=True)
        with patch("flask.templating._render", return_value=""):
            res = client.get(url)
            assert res.status == '302 FOUND'

        with patch("flask_login.utils._get_user", return_value=user):
            with patch("flask.templating._render", return_value=""):
                res = client.get(url)
                assert res.status == '200 OK'
                
# def check(self) -> jsonify: ~ UnboundLocalError: local variable 'task' referenced before assignment request.form needed
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_admin.py::test_ItemImportView_check -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_ItemImportView_check(i18n_app, users, client,client_request_args):
    file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'data',
        'sample_file',
        'sample_csv.csv'
    )

    csv_data = open(file_path, "rb")
    data = {"file": (csv_data, "sample_csv.csv")}
    
    client.post(
        "/",
        data=data,
        buffered=True,
        content_type="multipart/form-data",
    )

    rf = request.form.to_dict()
    rf['username'] = "test_user"

    # mimetype = 'application/json'
    # headers = {
    #     'Content-Type': mimetype,
    #     'Accept': mimetype
    # }
    # data = {
    #     'Data': [20.0, 30.0, 401.0, 50.0],
    #     'Date': ['2017-08-11', '2017-08-12', '2017-08-13', '2017-08-14'],
    #     'Day': 4
    # }

    # client.post(
    #     '/',
    #     data=json.dumps(data),
    #     headers=headers
    # )

    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        test = ItemImportView()
        task = MagicMock()
        task.task_id = 1
        with patch("weko_search_ui.tasks.check_import_items_task.apply_async",return_Value=task):
            assert test.check()

#     def get_check_status(self) -> jsonify: ~ GOOD
def test_ItemImportView_get_check_status(i18n_app, users, client_request_args, db_records2):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        test = ItemImportView()
        assert test.get_check_status()

#     def download_check(self): ~ GOOD
def test_ItemImportView_download_check(i18n_app, users, client_request_args, db_records2):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        test = ItemImportView()
        assert test.download_check()

#     def import_items(self) -> jsonify: ~ GOOD
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_admin.py::test_ItemImportView_import_items -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_ItemImportView_import_items(i18n_app, users, client_request_args, db_records2):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        test = ItemImportView()
        assert test.import_items()

#     def get_status(self): ~ GOOD
def test_ItemImportView_get_status(i18n_app, users, client_request_args, db_records2):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        test = ItemImportView()
        assert test.get_status()

#     def download_import(self): ~ GOOD
def test_ItemImportView_download_import(i18n_app, users, client_request_args, db_records2):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        test = ItemImportView()
        assert test.download_import()

#     def get_disclaimer_text(self): ~ GOOD
def test_ItemImportView_get_disclaimer_text(i18n_app, users, client_request_args, db_records2):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        test = ItemImportView()
        assert test.get_disclaimer_text()

#     def export_template(self):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_admin.py::test_ItemImportView_export_template -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_ItemImportView_export_template(i18n_app, users, item_type):
    _data = {
        'item_type_id': 1
    }
    with i18n_app.test_client() as client:
        with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
            res = client.post("/admin/items/import/export_template",
                              data=json.dumps(_data),
                              content_type="application/json")
            assert res.status_code==200


#     def check_import_available(self): ~ GETS STUCK
# def test_ItemImportView_check_import_available(i18n_app, users, client_request_args, db_records2):
#     with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
#         test = ItemImportView()
#         assert test.check_import_available()


# class ItemBulkExport(BaseView):

#     def index(self): ~ AttributeError: 'NoneType' object has no attribute 'base_template'
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_admin.py::test_ItemBulkExport_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_ItemBulkExport_index(i18n_app, users, client_request_args, db_records2,mocker):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        mock_render = mocker.patch("weko_search_ui.admin.ItemBulkExport.render",return_value=make_response())
        test = ItemBulkExport()
        res = test.index()
        assert res.status_code == 200
        mock_render.assert_called_with("weko_search_ui/admin/export.html")
        

#     def export_all(self): ~ GETS STUCK
# def test_ItemBulkExport_export_all(i18n_app, users, client_request_args, db_records2):
#     with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
#         test = ItemBulkExport()
#         assert test.export_all()

#     def check_export_status(self): ~ GETS STUCK
# def test_ItemBulkExport_check_export_status(i18n_app, users, client_request_args, db_records2):
#     with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
#         test = ItemBulkExport()
#         assert test.check_export_status()

#     def cancel_export(self): ~ GETS STUCK
# def test_ItemBulkExport_cancel_export(i18n_app, users, client_request_args, db_records2):
#     with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
#         test = ItemBulkExport()
#         assert test.cancel_export()

#     def download(self): ~ GETS STUCK
# def test_ItemBulkExport_download(i18n_app, users, client_request_args, db_records2):
#     with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
#         test = ItemBulkExport()
#         assert test.cancel_export()
class MockAsyncResult:
    def __init__(self,task_id):
        self.task_id=task_id
    @property
    def state(self):
        return self.task_id.replace("_task","")
    def successful(self):
        return self.state == "SUCCESS"
    def failed(self):
        return self.state == "FAILED"
class TestItemBulkExport:
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_admin.py::TestItemBulkExport::test_check_export_status -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
    def test_check_export_status(self,app,client,users, redis_connect,mocker):
        
        mocker.patch("weko_search_ui.utils.AsyncResult",side_effect=MockAsyncResult)
        mocker.patch("weko_search_ui.admin.check_celery_is_run",return_value=True)
        with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
            cache_key = app.config["WEKO_ADMIN_CACHE_PREFIX"].format(
                name="KEY_EXPORT_ALL", user_id=current_user.get_id()
            )
            datastore = redis_connect
            datastore.put(cache_key, "SUCCESS_task".encode("utf-8"), ttl_secs=30)
            
            url = url_for("items/bulk-export.check_export_status")

            res = client.get(url)
            assert json.loads(res.data) == {'data': {
                'celery_is_run': True, 
                'error_message': None, 
                'export_run_msg': None, 
                'export_status': False, 
                'status': 'SUCCESS', 
                'uri_status': False}}

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_admin.py::TestItemBulkExport::test_cancel_export -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
    def test_cancel_export(self, app, client, users, redis_connect, mocker):
        url = url_for("items/bulk-export.cancel_export")
        with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
            mocker.patch("weko_search_ui.admin.cancel_export_all",return_value=True)
            mocker.patch("weko_search_ui.admin.get_export_status",return_value=(False,"","","","REVOKED",))
            res = client.get(url)
            assert json.loads(res.data) == {"data":{"cancel_status":True,"export_status":False,"status":"REVOKED"}}

def compare_csv(data1, data2):
    def _str2csv(data):
        f = io.StringIO()
        f.write(data)
        f.seek(0)
        csv_data = [row for row in csv.reader(f)]
        return csv_data
    
    csv1 = _str2csv(data1)
    csv2 = _str2csv(data2)
    for i, row in enumerate(csv1):
        for t, w in enumerate(row):
            if "," in w:
                if not set([a.strip() for a in w.split(",")]) == set([a.strip() for a in csv2[i][t].split(",")]):
                    print("data at {i}:{t} don't mathch:{d1} - {d2}".format(i=i,t=t,d1=w,d2=csv2[i][t]))
                    return False
            else:
                if not w == csv2[i][t]:
                    print("data at {i}:{t} don't mathch:{d1} - {d2}".format(i=i,t=t,d1=w,d2=csv2[i][t]))
                    return False
    return True

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_admin.py::test_export_template -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_export_template(app, client, users, item_type):
    
    url="/admin/items/import/export_template"

    # data = {}
    
    # with app.test_client() as client:
    login_user_via_session(client=client, email=users[4]["email"])
    
    # no data test
    res = client.post(url, json={})
    assert res.get_data(as_text=True) == ""
    
    # not item_type_id test
    data = {
        "item_type_id":-1
    }
    res = client.post(url, json=data)
    assert res.get_data(as_text=True) == ""

    # no item_type test
    data = {
        "item_type_id":100
    }
    res = client.post(url, json=data)
    assert res.get_data(as_text=True) == ""

    # nomal test1
    data = {
        "item_type_id":17
    }
    res = client.post(url, json=data)
    with open("tests/item_type/export_template_17.csv","r") as f:
        result = f.read()
        io_obj = io.StringIO(result)
    # assert res.get_data(as_text=True) == codecs.BOM_UTF8.decode("utf8")+codecs.BOM_UTF8.decode()+io_obj.getvalue()
    assert compare_csv(res.get_data(as_text=True),codecs.BOM_UTF8.decode("utf8")+codecs.BOM_UTF8.decode()+io_obj.getvalue())
    

    # nomal test1
    # exist thumbnail with items
    # exist item not in form item
    # exist item in meta_system
    # exist item not in table_row_map
    data = {
        "item_type_id":18
    }
    res = client.post(url, json=data)
    with open("tests/item_type/export_template_18.csv","r") as f:
        result = f.read()
        io_obj = io.StringIO(result)
    # assert res.get_data(as_text=True) == codecs.BOM_UTF8.decode("utf8")+codecs.BOM_UTF8.decode()+io_obj.getvalue()
    assert compare_csv(res.get_data(as_text=True), codecs.BOM_UTF8.decode("utf8")+codecs.BOM_UTF8.decode()+io_obj.getvalue())
