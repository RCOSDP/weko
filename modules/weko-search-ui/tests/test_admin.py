import pytest
from mock import patch
import codecs
import io
import csv
import json
from flask import url_for, current_app
from datetime import datetime

from invenio_accounts.testutils import login_user_via_session


# class ItemManagementBulkDelete(BaseView):
#     def index(self):
#     def check(self):
# class ItemManagementCustomSort(BaseView):
#     def index(self):
#     def save_sort(self):
# class ItemManagementBulkSearch(BaseView):
#     def index(self):
#     def is_visible():
# class ItemImportView(BaseView):
#     def index(self):
#     def check(self) -> jsonify:
#     def get_check_status(self) -> jsonify:
#     def download_check(self):
#     def import_items(self) -> jsonify:
#     def get_status(self):
#     def download_import(self):
#     def get_disclaimer_text(self):
#     def export_template(self):
#     def check_import_available(self):
# class ItemBulkExport(BaseView):
#     def index(self):
#     def export_all(self):
#     def check_export_status(self):
#     def cancel_export(self):
#     def download(self):

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


user_results = [
    (0,403),
    (1,403),
    (2,403),
    (3,200),
    (4,200),
]

@pytest.mark.parametrize('id, status_code', user_results)
def test_import_items_login(app, client, admin_view, users, id, status_code):
    login_user_via_session(client=client, email=users[id]['email'])
    url = "/admin/items/import/import"
    input = {}

    res = client.post(url, json=input)
    assert res.status_code == status_code


def test_import_items_guest(client, db_sessionlifetime, admin_view):
    url = "/admin/items/import/import"
    input = {}

    res = client.post(url, json=input)
    assert res.status_code == 302
    assert res.location == url_for("security.login", next="/admin/items/import/import", _external=True)


@pytest.mark.parametrize('id, status_code', user_results)
def test_download_import_login(app, client, admin_view, users, id, status_code):
    login_user_via_session(client=client, email=users[id]['email'])
    url = "/admin/items/import/export_import"
    input = {}

    res = client.post(url, json=input)
    assert res.status_code == status_code


def test_download_import_guest(client, db_sessionlifetime, admin_view):
    url = "/admin/items/import/export_import"
    input = {}

    res = client.post(url, json=input)
    assert res.status_code == 302
    assert res.location == url_for("security.login", next="/admin/items/import/import", _external=True)


def test_import_items(app, client, admin_view, users, db_register):
    login_user_via_session(client=client, email=users[4]['email'])
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
        assert data["data"]["tasks"] is not None
        assert data["data"]["import_start_time"] is not None


def test_download_import(app, client, admin_view, users, db_register):
    login_user_via_session(client=client, email=users[4]['email'])
    url = "/admin/items/import/export_import"

    input = {"list_result": [
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
		}]}
    now = str(datetime.date(datetime.now()))
    file_format = current_app.config.get('WEKO_ADMIN_OUTPUT_FORMAT', 'tsv').lower()

    res = client.post(url, json=input)

    assert res.mimetype == "text/{}".format(file_format)
    assert res.headers["Content-disposition"] == "attachment; filename=List_Download {}.{}".format(now, file_format)
