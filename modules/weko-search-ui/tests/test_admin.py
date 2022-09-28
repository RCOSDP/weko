import pytest
from mock import patch
import codecs
import io
import csv
import json
from flask import url_for, current_app, make_response, request
from datetime import datetime

import os
from flask_login import current_user

from invenio_accounts.testutils import login_user_via_session

from weko_search_ui.admin import (
    ItemManagementBulkDelete,
    ItemManagementCustomSort,
    ItemManagementBulkSearch,
    ItemImportView,
    ItemBulkExport
)


# class ItemManagementBulkDelete(BaseView):
#     def index(self): ~ ERROR
def test_ItemManagementBulkDelete_index(i18n_app, users, client_request_args, db_records2):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        test = ItemManagementBulkDelete()
        assert test.index()

#     def check(self): ~ GOOD
def test_ItemManagementBulkDelete_check(i18n_app, users, client_request_args, db_records2):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        test = ItemManagementBulkDelete()
        assert test.check()


# class ItemManagementCustomSort(BaseView):
#     def index(self): ~ ERROR
def test_ItemManagementCustomSort_index(i18n_app, users, client_request_args, db_records2):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        test = ItemManagementCustomSort()
        assert test.index()

#     def save_sort(self): ~ GOOD
def test_ItemManagementCustomSort_save_sort(i18n_app, users, client_request_args, db_records2):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        test = ItemManagementCustomSort()
        assert test.save_sort()


# class ItemManagementBulkSearch(BaseView):
#     def index(self): ~ ERROR
def test_ItemManagementBulkSearch_index(i18n_app, users, client_request_args, db_records2):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        test = ItemManagementBulkSearch()
        assert test.index()

#     def is_visible(): ~ GOOD
def test_ItemManagementBulkSearch_is_visible(i18n_app, users, client_request_args, db_records2):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        test = ItemManagementBulkSearch()
        assert not test.is_visible()


# class ItemImportView(BaseView):
#     def index(self): ~ ERROR
def test_ItemImportView_index(i18n_app, users, client_request_args, db_records2):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        test = ItemImportView()
        assert test.index()

#     def check(self) -> jsonify: ~ UnboundLocalError: local variable 'task' referenced before assignment
def test_ItemImportView_check(i18n_app, users, client_request_args, db_records2):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        test = ItemImportView()
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

#     def export_template(self): ~ GOOD
def test_ItemImportView_export_template(i18n_app, users, client_request_args, db_records2):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        test = ItemImportView()
        assert test.export_template()

#     def check_import_available(self): ~ GETS STUCK
# def test_ItemImportView_check_import_available(i18n_app, users, client_request_args, db_records2):
#     with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
#         test = ItemImportView()
#         assert test.check_import_available()


# class ItemBulkExport(BaseView):
#     def index(self): ~ AttributeError: 'NoneType' object has no attribute 'base_template'
def test_ItemBulkExport_index(i18n_app, users, client_request_args, db_records2):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        test = ItemBulkExport()
        assert test.index()

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

    # normal test1
    data = {
        "item_type_id":17
    }
    res = client.post(url, json=data)
    with open("tests/item_type/export_template_17.csv","r") as f:
        result = f.read()
        io_obj = io.StringIO(result)
    # assert res.get_data(as_text=True) == codecs.BOM_UTF8.decode("utf8")+codecs.BOM_UTF8.decode()+io_obj.getvalue()
    assert compare_csv(res.get_data(as_text=True),codecs.BOM_UTF8.decode("utf8")+codecs.BOM_UTF8.decode()+io_obj.getvalue())


    # normal test1
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


user_list = [
    -1,# guest(no login)
    0, 1, 2, 3, 4 # users' id
]

accessible_user_list = [2, 3, 4]

@pytest.mark.parametrize('id', user_list)
def test_import_items_access(app, client, db_sessionlifetime, users, id):
    if id != -1:
        login_user_via_session(client=client, email=users[id]['email'])
    url = "/admin/items/import/import"
    input = {}

    res = client.post(url, json=input)
    # check guest
    if id == -1:
        http_host = app.config.get('SERVER_NAME')
        base_url = 'http://{0}/'.format(http_host)
        assert res.status_code == 302
        assert res.location == url_for("security.login", next=base_url+"admin/items/import/import", _external=True)
    # check not authorized users
    if id in (0, 1):
        assert res.status_code == 403
    # check authorized users
    if id in (2, 3, 4):
        assert res.status_code != 403


@pytest.mark.parametrize('id', user_list)
def test_download_import_access(app, client, users, id):
    if id != -1:
        login_user_via_session(client=client, email=users[id]['email'])
    url = "/admin/items/import/export_import"
    input = {}

    res = client.post(url, json=input)
    # check guest
    if id == -1:
        http_host = app.config.get('SERVER_NAME')
        base_url = 'http://{0}/'.format(http_host)
        assert res.status_code == 302
        assert res.location == url_for("security.login",
            next=base_url+"admin/items/import/export_import",
            _external=True)
    # check not authorized users
    if id in (0, 1):
        assert res.status_code == 403
    # check authorized users
    if id in (2, 3, 4):
        assert res.status_code != 403


@pytest.mark.parametrize('id', accessible_user_list)
def test_import_items_with_listrecords_without_import_task_data(app, client, users, db_register, id):
    login_user_via_session(client=client, email=users[id]['email'])
    url = "/admin/items/import/import"

    list_records_data = dict()
    with open("tests/data/list_records/list_records.json", "r") as f:
        list_records_data = json.load(f)
    input = {"data_path": "/tmp/weko_import_20220819045602",
             "list_record": list_records_data}

    with patch("weko_search_ui.admin.chord"):
        res = client.post(url, json=input)
        data = json.loads(res.get_data(as_text=True))
        assert data["status"] == "success"
        assert data["data"]["tasks"] == []
        assert data["data"]["import_start_time"] is not None


result_data = [
    None,
    [],
    [{}],
    [
		{
			'No':1,
			'Start Date':'2022-08-25 04:54:19',
			'End Date':'2022-08-25 04:54:37',
			'Item Id':'',
			'Action':'End',
			'Work Flow Status':'Done'
		},
		{
			'No':2,
			'Start Date':'2022-08-25 04:54:36',
			'End Date':'2022-08-25 04:55:21',
			'Item Id':'',
			'Action':'End',
			'Work Flow Status':'Done'
		}]
]

@pytest.mark.parametrize('result_data', result_data)
@pytest.mark.parametrize('id', accessible_user_list)
def test_download_import(app, client, users, db_register, id, result_data):
    login_user_via_session(client=client, email=users[id]['email'])
    url = "/admin/items/import/export_import"

    input = {"list_result": result_data}
    now = str(datetime.date(datetime.now()))
    file_format = current_app.config.get('WEKO_ADMIN_OUTPUT_FORMAT', 'tsv').lower()

    res = client.post(url, json=input)
    assert res.mimetype == "text/{}".format(file_format)
    assert res.headers["Content-disposition"] == "attachment; filename=List_Download {}.{}".format(now, file_format)


data_check = [
    [], [{"errors": "test errors"}]
]

@pytest.mark.parametrize('id', accessible_user_list)
@pytest.mark.parametrize('data_check', data_check)
def test_import_items_list_record_data_check(app, client, users, db_register, id, data_check):
    login_user_via_session(client=client, email=users[id]['email'])
    url = "/admin/items/import/import"
    input = {"data_path": "/tmp/weko_import_20220819045602",
             "list_record": data_check}

    res = client.post(url, json=input)
    data = json.loads(res.get_data(as_text=True))
    assert data["status"] == "success"
    assert data["data"]["tasks"] == []
    assert data["data"]["import_start_time"] == ""
