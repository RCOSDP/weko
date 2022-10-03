import codecs
import io
import csv
import os
import json
import pytest
from flask import current_app, make_response, request
from flask_login import current_user
from mock import patch

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

# def check(self) -> jsonify: ~ UnboundLocalError: local variable 'task' referenced before assignment request.form needed
def test_ItemImportView_check(i18n_app, users, client, client_request_args):
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

def test_export_template(app, client, admin_view, users, item_type):
    
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
