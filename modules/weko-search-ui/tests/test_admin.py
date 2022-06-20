import pytest
import codecs
import io
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
    assert res.get_data(as_text=True) == codecs.BOM_UTF8.decode("utf8")+codecs.BOM_UTF8.decode()+io_obj.getvalue()
    

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
    assert res.get_data(as_text=True) == codecs.BOM_UTF8.decode("utf8")+codecs.BOM_UTF8.decode()+io_obj.getvalue()
    