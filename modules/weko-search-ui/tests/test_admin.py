# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_admin.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
import codecs
import io
import csv
import os
import json
import pytest
from unittest.mock import patch, MagicMock, Mock
from flask_login import current_user
from jinja2.exceptions import TemplateNotFound
from flask import Flask, json, jsonify, session, url_for,current_app, make_response, request

from invenio_accounts.testutils import login_user_via_session

from werkzeug.datastructures import FileStorage
from weko_index_tree.models import Index
from weko_records.models import ItemTypeJsonldMapping
from weko_search_ui.admin import (
    ItemManagementBulkDelete,
    ItemManagementCustomSort,
    ItemManagementBulkSearch,
    ItemImportView,
    ItemBulkExport,
    ItemRocrateImportView
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
                        with patch('weko_search_ui.admin.call_external_system') as mock_external:
                            res = client.put("/admin/items/bulk/delete/?recursively=true&q=33",
                                            content_type="application/json")
                            assert res.status_code==200
                            mock_external.assert_not_called()
                    with patch('weko_search_ui.admin.delete_records', return_value=[3]):
                        with patch('weko_search_ui.admin.call_external_system') as mock_external:
                            with patch('weko_search_ui.admin.WekoRecord.get_record_by_pid'):
                                res = client.put("/admin/items/bulk/delete/?recursively=true&q=33",
                                                content_type="application/json")
                                assert res.status_code==200
                                mock_external.assert_called()
                                for call in mock_external.call_args_list:
                                    assert call[1]["old_record"] is not None
                                    assert "new_record" not in call[1]


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
                res = client.get(url)
                assert res.status == '200 OK'

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
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_admin.py::test_ItemImportView_get_check_status -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_ItemImportView_get_check_status(i18n_app, users, client_request_args, db_records3):
    _data = {
        'task_id': 1
    }

    with i18n_app.test_client() as client:
        with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
            # data false
            res = client.post("/admin/items/import/get_check_status",
                                data=json.dumps({}),
                                content_type="application/json")
            assert res.status_code == 200

            # list_record none
            mock_result = {"start_date": "2025-03-19", "end_date": "2025-03-19"}
            mock_async_result = MagicMock()
            mock_async_result.status = "SUCCESS"
            mock_async_result.result = mock_result
            from weko_search_ui.tasks import import_item
            import_item.AsyncResult = MagicMock(return_value=mock_async_result)
            res = client.post("/admin/items/import/get_check_status",
                              data=json.dumps(_data),
                              content_type="application/json")
            result = json.loads(res.data)
            assert result["status"]=="success"

            # duplicate True
            mock_result = {"start_date": "2025-03-19", "end_date": "2025-03-19",
                   "list_record": [{"metadata":{"subitem_identifier_uri":[{"subitem_identifier_uri":"test"}]}}]}
            mock_async_result.result = mock_result
            res = client.post("/admin/items/import/get_check_status",
                              data=json.dumps(_data),
                              content_type="application/json")
            result = json.loads(res.data)
            assert result["status"]=="success"

            # duplicate False
            mock_result = {"start_date": "2025-03-19", "end_date": "2025-03-19",
                   "list_record": [{"metadata":{"subitem_identifier_uri":[{"subitem_identifier_uri":"http://localhost"}]}}]}
            mock_async_result.result = mock_result
            res = client.post("/admin/items/import/get_check_status",
                              data=json.dumps(_data),
                              content_type="application/json")
            result = json.loads(res.data)
            assert result["status"]=="warning"

            # error
            mock_async_result.result = None
            res = client.post("/admin/items/import/get_check_status",
                              data=json.dumps(_data),
                              content_type="application/json")
            result = json.loads(res.data)
            assert result["error"]=="Internal server error"

            # PENDING
            mock_async_result.result = None
            mock_async_result.status = "PENDING"
            res = client.post("/admin/items/import/get_check_status",
                              data=json.dumps(_data),
                              content_type="application/json")
            assert res.status_code == 200

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


#     def import_items(self) -> jsonify: ~ GOOD
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_admin.py::test_ItemImportView_import_items_doi -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_ItemImportView_import_items_doi(i18n_app, users, client, client_request_args, db_records2):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        data = {"list_record": [{"id": "1"}], "data_path": "/tmp/weko_import_20250319102601371", "list_doi": ["10.5109/16119"]}
        with patch("flask.request.get_json", return_value=data):
            with patch("weko_search_ui.admin.create_flow_define"):
                with patch("weko_search_ui.admin.handle_workflow"):
                    with patch("weko_search_ui.admin.handle_doi", side_effect=Exception) as mock_handle_doi:
                        with patch("weko_search_ui.admin.db.session.rollback"):
                            with patch("weko_search_ui.admin.remove_temp_dir_task"):
                                test = ItemImportView()
                                test.import_items()
                                mock_handle_doi.assert_called_once()


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


# class ItemRocrateImportView(BaseView):
class TestItemRocrateImportView:
    # .tox/c1/bin/pytest --cov=weko_search_ui tests/test_admin.py::TestItemRocrateImportView::test_index_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
    def test_index_acl(self,client, users, db_records2):
        user = users[3]['obj']
        assert user.roles[0].name=='System Administrator'

        url = url_for("items/rocrate_import.index", _external=True)
        with patch("flask.templating._render", return_value=""):
            res = client.get(url)
            assert res.status == '302 FOUND'

        with patch("flask_login.utils._get_user", return_value=user):
            with patch("flask.templating._render", return_value=""):
                res = client.get(url)
                assert res.status == '200 OK'

# def check(self) -> jsonify: ~ UnboundLocalError: local variable 'task' referenced before assignment request.form needed
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_admin.py::test_ItemRocrateImportView_check -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_ItemRocrateImportView_check(i18n_app, users, client, client_request_args, mocker):
    file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data",
        "rocrate_import",
        "new_crate_v2.zip"
    )
    url = url_for("items/rocrate_import.check")
    print(f"url: {url}")
    with open(file_path, "rb") as f:
        zip_storage = FileStorage(
            filename="new_crate_v2.zip",
            stream=io.BytesIO(f.read()),
            content_type="application/zip"
        )
        data = {
            "file": zip_storage,
            "is_change_identifier": "false",
            "mapping_id": 1
        }
        headers = {
            "Content-Disposition":"attachment; filename=new_crate_v2.zip",
            "Packaging":"http://purl.org/net/sword/3.0/package/SimpleZip"
        }

        mocker.patch("flask_login.utils._get_user", return_value=users[3]['obj'])
        mocker.patch("weko_search_ui.admin.validate_csrf_header")
        task = MagicMock()
        task.task_id = 1
        mock_check = mocker.patch("weko_search_ui.admin.check_rocrate_import_items_task.apply_async",return_value=task)
        res = client.post(
            url,
            data=data,
            content_type="multipart/form-data",
            headers=headers
        )
        mock_check.assert_called_once()
        print(f"res.data: {res.data}")
        assert res.status_code == 200

#     def get_check_status(self) -> jsonify: ~ GOOD
def test_ItemRocrateImportView_get_check_status(i18n_app, users, client_request_args, db_records2):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        test = ItemRocrateImportView()
        assert test.get_check_status()

#     def download_check(self): ~ GOOD
def test_ItemRocrateImportView_download_check(i18n_app, users, client_request_args, db_records2):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        test = ItemRocrateImportView()
        assert test.download_check()

#     def import_items(self) -> jsonify: ~ GOOD
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_admin.py::test_ItemRocrateImportView_import_items -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_ItemRocrateImportView_import_items(i18n_app, users, client_request_args, db_records2):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        test = ItemRocrateImportView()
        assert test.import_items()

#     def get_status(self): ~ GOOD
def test_ItemRocrateImportView_get_status(i18n_app, users, client_request_args, db_records2):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        test = ItemRocrateImportView()
        assert test.get_status()

#     def download_import(self): ~ GOOD
def test_ItemRocrateImportView_download_import(i18n_app, users, client_request_args, db_records2):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        test = ItemRocrateImportView()
        assert test.download_import()

#     def get_disclaimer_text(self): ~ GOOD
def test_ItemRocrateImportView_get_disclaimer_text(i18n_app, users, client_request_args, db_records2):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        test = ItemRocrateImportView()
        assert test.get_disclaimer_text()

#     def all_mappings(self):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_admin.py::test_ItemRocrateImportView_all_mappings -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_ItemRocrateImportView_all_mappings(i18n_app, users):
    map1 = ItemTypeJsonldMapping(
        id=1,
        name="sample1",
        mapping="{data:{}}",
        item_type_id=30001,
        version_id=6,
        is_deleted=False
    )
    expect = [{
                "id": 1,
                "name": "sample1",
                "item_type_id": 30001
            }]

    with i18n_app.test_client() as client:
        with patch("flask_login.utils._get_user",
                   return_value=users[3]['obj']):
            with patch("weko_search_ui.admin.JsonldMapping.get_all",
                       return_value=[map1]):
                res = client.get("/admin/items/rocrate_import/all_mappings",
                                 content_type="application/json")
                assert res.status_code==200
                assert res.json == expect


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
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_admin.py::test_ItemBulkExport_export_all -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_ItemBulkExport_export_all(users, client, redis_connect, mocker):
    url = url_for('items/bulk-export.export_all')
    start_time_str = '2024/05/01 12:55:36'
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        mocker.patch("weko_search_ui.admin.check_celery_is_run",return_value=True)
        mocker.patch("weko_search_ui.admin.check_session_lifetime",return_value=True)
        with patch("weko_search_ui.admin.get_export_status",
                   return_value=(True, '', '', '', 'STARTED', start_time_str, '')):
            res = client.post(url)
            assert json.loads(res.data) == {'data': {
                'celery_is_run': True,
                'is_lifetime': True,
                'error_message': '',
                'export_run_msg': '',
                'export_status': True,
                'finish_time': '',
                'start_time': start_time_str,
                'status': 'STARTED',
                'uri_status': False
            }}

        task = MagicMock()
        task.task_id = 1
        mocker.patch('weko_search_ui.tasks.export_all_task.apply_async',
                     return_value=task)
        file_json = {
            'start_time': start_time_str,
            'finish_time': '',
            'export_path': '',
            'cancel_flg': False,
            'write_file_status': {
                '1': 'started'
            }
        }
        cache_key = current_app.config["WEKO_ADMIN_CACHE_PREFIX"].format(
            name='KEY_EXPORT_ALL',
            user_id=current_user.get_id()
        )
        cache_uri_key = current_app.config["WEKO_ADMIN_CACHE_PREFIX"].format(
            name='URI_EXPORT_ALL',
            user_id=current_user.get_id()
        )
        cache_msg_key = current_app.config["WEKO_ADMIN_CACHE_PREFIX"].format(
            name='MSG_EXPORT_ALL',
            user_id=current_user.get_id()
        )
        run_msg_key = current_app.config["WEKO_ADMIN_CACHE_PREFIX"].format(
            name='RUN_MSG_EXPORT_ALL',
            user_id=current_user.get_id()
        )
        file_cache_key = current_app.config["WEKO_ADMIN_CACHE_PREFIX"].format(
            name='RUN_MSG_EXPORT_ALL_FILE_CREATE',
            user_id=current_user.get_id()
        )
        datastore = redis_connect
        datastore.delete(cache_key)
        datastore.put(cache_uri_key, 'test_uri'.encode('utf-8'), ttl_secs=30)
        datastore.put(cache_msg_key, ''.encode('utf-8'), ttl_secs=30)
        datastore.put(run_msg_key, ''.encode('utf-8'), ttl_secs=30)
        datastore.put(file_cache_key, json.dumps(file_json).encode('utf-8'), ttl_secs=30)
        mocker.patch("weko_search_ui.utils.AsyncResult",side_effect=MockAsyncResult)
        res = client.post(url)
        assert json.loads(res.data) == {'data': {
            'celery_is_run': True,
            'is_lifetime': True,
            'error_message': '',
            'export_run_msg': '',
            'export_status': True,
            'finish_time': '',
            'start_time': start_time_str,
            'status': 'STARTED',
            'uri_status': True
        }}

        with patch("weko_search_ui.admin.get_export_status",
                   return_value=(False, '', '', '', 'STARTED', start_time_str, '')):
            res = client.post(url)
            assert json.loads(res.data) == {'data': {
                'celery_is_run': True,
                'is_lifetime': True,
                'error_message': '',
                'export_run_msg': '',
                'export_status': False,
                'finish_time': '',
                'start_time': start_time_str,
                'status': 'STARTED',
                'uri_status': False
            }}

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

        mocker.patch("weko_search_ui.admin.check_celery_is_run",return_value=True)
        mocker.patch("weko_search_ui.admin.check_session_lifetime",return_value=True)
        start_time_str = '2024/05/01 12:55:36'
        with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
            url = url_for("items/bulk-export.check_export_status")
            with patch('weko_search_ui.admin.get_export_status',
                       return_value=(True, '', '', '', 'STARTED', start_time_str, '')):
                res = client.get(url)
                assert json.loads(res.data) == {'data': {
                    'celery_is_run': True,
                    'is_lifetime': True,
                    'error_message': '',
                    'export_run_msg': '',
                    'export_status': True,
                    'finish_time': '',
                    'start_time': start_time_str,
                    'status': 'STARTED',
                    'uri_status': False
                }}

            with patch('weko_search_ui.admin.get_export_status',
                       return_value=(True, 'test_uri', '', '', 'STARTED', start_time_str, '')):
                res = client.get(url)
                assert json.loads(res.data) == {'data': {
                    'celery_is_run': True,
                    'is_lifetime': True,
                    'error_message': '',
                    'export_run_msg': '',
                    'export_status': True,
                    'finish_time': '',
                    'start_time': start_time_str,
                    'status': 'STARTED',
                    'uri_status': True
                }}

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_admin.py::TestItemBulkExport::test_cancel_export -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
    def test_cancel_export(self, app, client, users, redis_connect, mocker):
        url = url_for("items/bulk-export.cancel_export")
        with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
            mocker.patch("weko_search_ui.admin.cancel_export_all",return_value=True)
            mocker.patch("weko_search_ui.admin.get_export_status",return_value=(False,"","","","REVOKED","","",))
            res = client.get(url)
            assert json.loads(res.data) == {"data":{"cancel_status":True,"export_status":False,"status":"REVOKED"}}

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_admin.py::TestItemBulkExport::test_download -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
    def test_download(self, client, users, mocker, create_file_instance):
        url = url_for('items/bulk-export.download')
        with patch('flask_login.utils._get_user', return_value=users[3]['obj']):
            file_path = create_file_instance
            # export_status is False, download_uri is not None
            with patch('weko_search_ui.admin.get_export_status',
                       return_value=(False, file_path, '', '', '', '', '')):
                res = client.get(url)
                assert res.headers['Content-Disposition'].split('; ')[1].replace('filename=', '') == 'export-all.zip'
                assert res.headers['Content-Type'] == 'application/octet-stream'
                assert res.status_code == 200
            # export_status is False, download_uri is None
            with patch('weko_search_ui.admin.get_export_status',
                       return_value=(False, None, '', '', '', '', '')):
                res = client.get(url)
                assert 'Content-Disposition' not in res.headers
                assert res.headers['Content-Type'] != 'application/octet-stream'
                assert res.status_code == 200
            # export_status is True, download_uri is not None
            with patch('weko_search_ui.admin.get_export_status',
                       return_value=(True, file_path, '', '', '', '', '')):
                res = client.get(url)
                assert 'Content-Disposition' not in res.headers
                assert res.headers['Content-Type'] != 'application/octet-stream'
                assert res.status_code == 200
            # export_stauts is True, download_uri is None
            with patch('weko_search_ui.admin.get_export_status',
                       return_value=(True, None, '', '', '', '', '')):
                res = client.get(url)
                assert 'Content-Disposition' not in res.headers
                assert res.headers['Content-Type'] != 'application/octet-strean'
                assert res.status_code == 200

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
