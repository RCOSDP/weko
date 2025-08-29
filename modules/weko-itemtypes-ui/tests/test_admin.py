
from datetime import datetime
import os
from glob import glob
from os.path import join, dirname
from unittest.mock import MagicMock
from zipfile import ZIP_DEFLATED, ZipFile
import pytest
import uuid
import copy
from mock import patch
from io import BytesIO
from werkzeug.datastructures import FileStorage
from flask import url_for,make_response,json,current_app

from invenio_accounts.testutils import login_user_via_session
from invenio_pidstore.models import PersistentIdentifier
from weko_admin.models import BillingPermission
from weko_records.models import ItemMetadata, ItemTypeProperty
from weko_records.api import Mapping
from weko_records_ui.models import RocrateMapping
from weko_workflow.models import WorkFlow, FlowDefine

from tests.helpers import login

def assert_statuscode_with_role(response,is_admin,error_code=403):
    if is_admin:
        assert response.status_code != error_code
    else:
        assert response.status_code == error_code
# class ItemTypeMetaDataView(BaseView):
class TestItemTypeMetaDataView:
    
#     def index(self, item_type_id=0):
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_admin.py::TestItemTypeMetaDataView::test_index_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
    @pytest.mark.parametrize("index,is_permission",[
        (0,True),
        (1,True),
        (2,False),
        (3,False),
        (4,False),
        (5,False),
        (7,False)
    ])
    def test_index_acl(self,client,admin_view,users,index,is_permission):
        login_user_via_session(client=client,email=users[index]["email"])
        url = url_for("itemtypesregister.index")
        res = client.get(url)
        assert_statuscode_with_role(res,is_permission)
        url = url_for("itemtypesregister.index",item_type_id=10)#
        res = client.get(url)
        assert_statuscode_with_role(res,is_permission)
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_admin.py::TestItemTypeMetaDataView::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
    def test_index(self,client,admin_view,item_type,users,mocker):
        login_user_via_session(client=client,email=users[0]["email"])
        url = url_for("itemtypesregister.index",item_type_id=3)
        mock_render = mocker.patch("weko_itemtypes_ui.admin.ItemTypeMetaDataView.render",return_value=make_response())
        res = client.get(url)
        assert res.status_code == 200#
        itemtype_list_ = [(obj["item_type_name"],obj["item_type_name"].name,obj["item_type"].id,obj["item_type"].harvesting_type,obj["item_type"].is_deleted,obj["item_type"].tag) for obj in item_type]
        itemtype_list = sorted(itemtype_list_, key=lambda x: x[2])
        mock_render.assert_called_with(
            'weko_itemtypes_ui/admin/create_itemtype.html',
            item_type_list=itemtype_list,
            id=3,
            is_sys_admin=True,
            lang_code="en"
        )#
#     def render_itemtype(self, item_type_id=0):
    @pytest.mark.parametrize("index,is_permission",[
        (0,True),
        (1,True),
        (2,False),
        (3,False),
        (4,False),
        (5,False),
        (7,False)
    ])
    def test_render_itemtype_acl(self,client,admin_view,users,item_type,index,is_permission):
        login_user_via_session(client=client,email=users[index]["email"])
        url = url_for("itemtypesregister.render_itemtype",item_type_id=2)
        res = client.get(url)
        assert_statuscode_with_role(res,is_permission)
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_admin.py::TestItemTypeMetaDataView::test_render_itemtype -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
    def test_render_itemtype(self,client,admin_view,item_type,users,):
        login_user_via_session(client=client,email=users[0]["email"])
        
        url = url_for("itemtypesregister.render_itemtype",item_type_id=2)
        res = client.get(url)
        result = json.loads(res.data)
        assert result["edit_notes"] == {}
        assert result["table_row"] != []
        assert result["meta_list"] != {}
        
        
        # url = url_for("itemtypesregister.render_itemtype",item_type_id=0)
        # res = client.get(url)
        # result = json.loads(res.data)
        # assert result == {
        #         'table_row': [],
        #         'table_row_map': {},
        #         'meta_list': {},
        #         'schemaeditor': {
        #             'schema': {}
        #         },
        #         'edit_notes': {}
        #     }#
#     def delete_itemtype(self, item_type_id=0):
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_admin.py::TestItemTypeMetaDataView::test_delete_itemtype -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
    def test_delete_itemtype(self,client,admin_view,db,users,item_type,mocker):
        login_user_via_session(client=client,email=users[0]["email"])
        
        with patch("weko_itemtypes_ui.admin.is_import_running", return_value="is_import_running"):
            url = url_for("itemtypesregister.delete_itemtype")
            res = client.post(url)
            assert json.loads(res.data)["code"] == -1
            
        with patch("weko_itemtypes_ui.admin.is_import_running", return_value=None), \
            patch("weko_workflow.utils.get_cache_data", return_value=False):
            
            url = url_for("itemtypesregister.delete_itemtype",item_type_id=0)
            res = client.post(url)
            assert json.loads(res.data)["code"] == -1
            
            url = url_for("itemtypesregister.delete_itemtype",item_type_id=1)
            mock_flash = mocker.patch("weko_itemtypes_ui.admin.flash")
            res = client.post(url)
            mock_flash.assert_called_with("Cannot delete Item type for Harvesting.","error")
            assert json.loads(res.data)["code"] == -1
            
            item_type1 = item_type[0]["item_type"]
            item_type1.harvesting_type = False
            item_type2 = item_type[1]["item_type"]
            item_type2.harvesting_type = False
            db.session.merge(item_type1)
            db.session.merge(item_type2)
            item = ItemMetadata(item_type_id=item_type1.id,json={})
            
            db.session.add(item)
            db.session.commit()
            pid = PersistentIdentifier(
                pid_type="recid",
                pid_value="1",
                status="R",
                object_type="rec",
                object_uuid=item.id
            )
            db.session.add(pid)
            db.session.commit()
            mock_flash = mocker.patch("weko_itemtypes_ui.admin.flash")
            url = url_for("itemtypesregister.delete_itemtype",item_type_id=item_type1.id)
            res = client.post(url)
            mock_flash.assert_called_with("Cannot delete due to child existing item types.","error")
            assert json.loads(res.data)["code"] == -1

        with patch("weko_itemtypes_ui.admin.is_import_running", return_value=None), \
            patch("weko_workflow.utils.get_cache_data", return_value=True):
            mock_flash = mocker.patch("weko_itemtypes_ui.admin.flash")
            url = url_for("itemtypesregister.delete_itemtype",item_type_id=item_type2.id)
            res = client.post(url)
            mock_flash.assert_called_with("Item type cannot be deleted becase import is in progress.","error")
            assert json.loads(res.data)["code"] == -1

        with patch("weko_itemtypes_ui.admin.is_import_running", return_value=None), \
            patch("weko_workflow.utils.get_cache_data", return_value=False):
            mock_flash = mocker.patch("weko_itemtypes_ui.admin.flash")
            url = url_for("itemtypesregister.delete_itemtype",item_type_id=item_type2.id)
            res = client.post(url)
            mock_flash.assert_called_with("Deleted Item type successfully.")
            assert json.loads(res.data)["code"] == 0

# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_admin.py::TestItemTypeMetaDataView::test_register_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
#     def register(self, item_type_id=0):
    @pytest.mark.parametrize("index,is_permission",[
        (0,True),
        (1,True),
        (2,False),
        (3,False),
        (4,False),
        (5,False),
        (7,False)
    ])
    def test_register_acl(self,client,admin_view,users,item_type,index,is_permission):
        login_user_via_session(client=client,email=users[index]["email"])
        url = url_for("itemtypesregister.register",item_type_id=1)

        with patch("weko_itemtypes_ui.admin.is_import_running", return_value="is_import_running"):
            res = client.post(url,headers={"Content-Type":"application/json"})
            assert json.loads(res.data)=={'msg': 'Item type cannot be updated becase import is in progress.'}
            assert res.status_code == 400
        
        with patch("weko_itemtypes_ui.admin.is_import_running", return_value=None),\
            patch("weko_workflow.utils.get_cache_data", return_value=True):
            res = client.post(url,json={})
            if is_permission:
                assert res.status_code == 400
                result = json.loads(res.data)
                assert result["msg"] == 'Item type cannot be updated becase import is in progress.'
            else:
                assert res.status_code == 403

# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_admin.py::TestItemTypeMetaDataView::test_register -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
    def test_register(self,app,client,db,admin_view,users,item_type,mocker):
        login_user_via_session(client=client,email=users[0]["email"])
        login(app,client,obj=users[0]["obj"])
        with patch("weko_itemtypes_ui.admin.is_import_running", return_value=None),\
            patch("weko_workflow.utils.get_cache_data", return_value=False):
            mocker.patch("weko_records.api.after_record_insert.send")
            mocker.patch("weko_records.api.before_record_insert.send")
            url = url_for("itemtypesregister.register")
            res = client.post(url,headers={"Content-Type":"plain/text"})
            assert json.loads(res.data)["msg"] == "Header Error"
            
            data = {
                "table_row_map":{
                    "schema":{"object":"test schema"},
                    "form":["test form"],
                    "name":"new item type name",
                }
            }
            schema = copy.deepcopy(data["table_row_map"]["schema"])
            form = copy.deepcopy(data["table_row_map"]["form"])
            mocker.patch("weko_itemtypes_ui.admin.fix_json_schema",return_value=schema)
            mocker.patch("weko_itemtypes_ui.admin.update_text_and_textarea",return_value=(schema,form))
            
            # raise ValueError
            mocker.patch("weko_itemtypes_ui.admin.update_required_schema_not_exist_in_form",return_value={})
            res = client.post(url,json=data,headers={"Content-Type":"application/json"})
            assert res.status_code == 400
            result = json.loads(res.data)
            assert result["msg"] == "Failed to register Item type. Schema is in wrong format."
            
            
            flow_define = FlowDefine(id=1,flow_id=uuid.uuid4(),
                                flow_name='Registration Flow',
                                flow_user=1)
            with db.session.begin_nested():
                db.session.add(flow_define)
            db.session.commit()
            workflow = WorkFlow(flows_id=uuid.uuid4(),
                            flows_name='test workflow01',
                            itemtype_id=1,
                            index_tree_id=None,
                            flow_id=1,
                            is_deleted=False,
                            open_restricted=False,
                            location_id=None,
                            is_gakuninrdm=False)
            with db.session.begin_nested():
                db.session.add(workflow)
            db.session.commit()

        with patch("weko_itemtypes_ui.admin.is_import_running", return_value=None),\
            patch("weko_workflow.utils.get_cache_data", return_value=True):
            url = url_for("itemtypesregister.register",item_type_id=0)
            res = client.post(url,json=data,headers={"Content-Type":"application/json"})
            result = json.loads(res.data)
            res.status_code == 400
            assert result["msg"] == "Failed to register Item type. Schema is in wrong format."
        
        with patch("weko_itemtypes_ui.admin.is_import_running", return_value=None),\
            patch("weko_workflow.utils.get_cache_data", return_value=False):
            url = url_for("itemtypesregister.register",item_type_id=0)
            mocker.patch("weko_itemtypes_ui.admin.update_required_schema_not_exist_in_form",return_value=schema)
            res = client.post(url,json=data,headers={"Content-Type":"application/json"})
            result = json.loads(res.data)
            assert result["msg"] == "Successfuly registered Item type."
            assert result["redirect_url"] == "/admin/itemtypes/8"
        
#     def restore_itemtype(self, item_type_id=0):
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_admin.py::TestItemTypeMetaDataView::test_restore_itemtype -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
    def test_restore_itemtype(self,client,db,admin_view,users,item_type):
        login_user_via_session(client=client,email=users[0]["email"])
        url = url_for("itemtypesregister.restore_itemtype")
        
        res = client.post(url)
        result = json.loads(res.data)
        assert result["code"] == -1
        assert result["msg"] == 'An error has occurred.'
        
        url = url_for("itemtypesregister.restore_itemtype",item_type_id=1)
        res = client.post(url)
        result = json.loads(res.data)
        assert result["code"] == -1
        assert result["msg"] == 'An error has occurred.'
        
        item_type1 = item_type[0]["item_type"]
        item_type1.is_deleted=True
        db.session.merge(item_type1)
        db.session.commit()

        url = url_for("itemtypesregister.restore_itemtype",item_type_id=1)
        res = client.post(url)
        result = json.loads(res.data)
        assert result["code"] == 0
        assert result["msg"] == 'Restored Item type successfully.'
        
        item_type1 = item_type[0]["item_type"]
        item_type1.is_deleted=True
        db.session.merge(item_type1)
        db.session.commit()
        with patch("weko_itemtypes_ui.admin.ItemTypeNames.restore",side_effect=BaseException):
            res = client.post(url)
            result = json.loads(res.data)
            assert result["code"] == -1
            assert result["msg"] == 'Failed to restore Item type.'
        
#     def get_property_list(self, property_id=0):
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_admin.py::TestItemTypeMetaDataView::test_get_property_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
    def test_get_property_list(self,client,admin_view,db,itemtype_props,admin_settings,users,mocker):
        login_user_via_session(client=client,email=users[0]["email"])
        url = url_for("itemtypesregister.get_property_list")
        billing_permission = BillingPermission(user_id=1,is_active=True)
        db.session.add(billing_permission)
        db.session.commit()
        
        res = client.get(url,query_string={"lang":"en"})
        result = json.loads(res.data)
        test = {
            "system":{"2":{"name":"S_test2","schema":{},"form":{},"forms":{},"sort":None,"is_file":False}},
            "1":{"name":"test_name_en","schema":{"properties":{"filename":{"items":["test_file"]}}},"form":{"title_i18n":{"en":"test_name_en"}},"forms":{},"sort":None,"is_file":True},
            "3":{"name":"test3_exist_billing_file_prop","schema":{"billing_file_prop":True},"form":{},"forms":{},"sort":None,"is_file":False},
            "4":{"name":"test4_exist_system_prop","schema":{"system_prop":True},"form":{},"forms":{},"sort":None,"is_file":False},
            "defaults":{'1': {'name': 'Text Field', 'value': 'text'},'2': {'name': 'Text Area', 'value': 'textarea'},'3': {'name': 'Check Box', 'value': 'checkboxes'},'4': {'name': 'Radio Button', 'value': 'radios'},'5': {'name': 'List Box', 'value': 'select'},'6': {'name': 'Date', 'value': 'datetime'}},
        }
        assert result == test
        
        # settings.show_flag is false,billing_perm.is_active is false
        billing_permission.is_active=False
        db.session.merge(billing_permission)
        default_properties = admin_settings["default_properties"]
        default_properties.settings = {"show_flag": False}
        db.session.merge(default_properties)
        db.session.commit()
        res = client.get(url,query_string={"lang":"en"})
        result = json.loads(res.data)
        test = {
            "system":{"2":{"name":"S_test2","schema":{},"form":{},"forms":{},"sort":None,"is_file":False}},
            "1":{"name":"test_name_en","schema":{"properties":{"filename":{"items":["test_file"]}}},"form":{"title_i18n":{"en":"test_name_en"}},"forms":{},"sort":None,"is_file":True},
            "4":{"name":"test4_exist_system_prop","schema":{"system_prop":True},"form":{},"forms":{},"sort":None,"is_file":False},
            "defaults":{"0":{"name":"Date (Type-less）","value":"datetime"}}
        }
        assert result == test
        # adminsetting is None
        mocker.patch("weko_itemtypes_ui.admin.AdminSettings.get",return_value=None)
        res = client.get(url,query_string={"lang":"en"})
        result = json.loads(res.data)
        test = {
            "system":{"2":{"name":"S_test2","schema":{},"form":{},"forms":{},"sort":None,"is_file":False}},
            "1":{"name":"test_name_en","schema":{"properties":{"filename":{"items":["test_file"]}}},"form":{"title_i18n":{"en":"test_name_en"}},"forms":{},"sort":None,"is_file":True},
            "4":{"name":"test4_exist_system_prop","schema":{"system_prop":True},"form":{},"forms":{},"sort":None,"is_file":False},
            "defaults":{'1': {'name': 'Text Field', 'value': 'text'},'2': {'name': 'Text Area', 'value': 'textarea'},'3': {'name': 'Check Box', 'value': 'checkboxes'},'4': {'name': 'Radio Button', 'value': 'radios'},'5': {'name': 'List Box', 'value': 'select'},'6': {'name': 'Date', 'value': 'datetime'}},
        }
        assert result == test
        # 
        current_app.config.update(
            WEKO_ITEMTYPES_UI_SHOW_DEFAULT_PROPERTIES=False
        )
        res = client.get(url,query_string={"lang":"en"})
        result = json.loads(res.data)
        test = {
            "system":{"2":{"name":"S_test2","schema":{},"form":{},"forms":{},"sort":None,"is_file":False}},
            "1":{"name":"test_name_en","schema":{"properties":{"filename":{"items":["test_file"]}}},"form":{"title_i18n":{"en":"test_name_en"}},"forms":{},"sort":None,"is_file":True},
            "4":{"name":"test4_exist_system_prop","schema":{"system_prop":True},"form":{},"forms":{},"sort":None,"is_file":False},
            "defaults":{"0":{"name":"Date (Type-less）","value":"datetime"}}
        }
        assert result == test
#     def export(self,item_type_id):
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_admin.py::TestItemTypeMetaDataView::test_export -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
    def test_export(
        self, client, admin_view, db, users, create_item_type, mocker, caplog
    ):
        # Setup
        login_user_via_session(client=client,email=users[0]['email'])
        item_type_data = create_item_type(id=1)
        create_item_type(id=2)
        test_datetime = '2024-09-06T00:00:00+00:00'
        expected_files = [
            'ItemType.json',
            'ItemTypeName.json',
            'ItemTypeMapping.json',
            'ItemTypeProperty.json'
        ]
        expected_item_type = {
            'created': test_datetime,
            'updated': test_datetime,
            'id': 1,
            # 'name_id': 1,
            'harvesting_type': False,
            'schema': {},
            'form': {},
            'render': {},
            'tag': 1,
            'version_id': 1,
            'is_deleted': False
        }
        expected_item_type_name = {
            'created': test_datetime,
            'updated': test_datetime,
            'id': 1,
            'name': 'test item type 1',
            'has_site_license': True,
            'is_active': True,
        }
        expected_item_type_mapping = {
            'created': test_datetime,
            'updated': test_datetime,
            'id': 1,
            'item_type_id': 1,
            'mapping': {'test': 'test'},
            'version_id': 1
        }
        expected_item_type_property = [
            {
                'created': test_datetime,
                'updated': test_datetime,
                'id': 1,
                'name': 'test property 1',
                'schema': {'type': 'string'},
                'form': {'title_i18n': {'en': 'test property'}},
                'forms': ['test form'],
                'delflg': False,
                'sort': None,
            },
            {
                'created': test_datetime,
                'updated': test_datetime,
                'id': 2,
                'name': 'test property 2',
                'schema': {'type': 'string'},
                'form': {'title_i18n': {'en': 'test property'}},
                'forms': ['test form'],
                'delflg': False,
                'sort': None,
            }
        ]

        # Render the error screen if item type is not found
        url = url_for('itemtypesregister.export',item_type_id=100)
        mock_render = mocker.patch(
            'weko_itemtypes_ui.admin.ItemTypeMetaDataView.render',
            return_value=make_response()
        )
        with caplog.at_level('ERROR'):
            res = client.get(url)
        mock_render.assert_called_with('weko_itemtypes_ui/admin/error.html')
        assert 'item_type_id=100 is cannot export' in caplog.text

        # Assert the response is successful when the item type ID is valid
        url = url_for('itemtypesregister.export',item_type_id=1)
        response = client.get(url)
        assert response.status_code == 200

        # Verify that the JSON files in the ZIP archive contain expected data
        zip_file = ZipFile(BytesIO(response.data))
        assert sorted(zip_file.namelist()) == sorted(expected_files)
        with zip_file.open('ItemType.json') as f:
            item_type_json = json.load(f)
            assert item_type_json == expected_item_type
        with zip_file.open('ItemTypeName.json') as f:
            item_type_name_json = json.load(f)
            assert item_type_name_json == expected_item_type_name
        with zip_file.open('ItemTypeMapping.json') as f:
            item_type_mapping_json = json.load(f)
            assert item_type_mapping_json == expected_item_type_mapping
        with zip_file.open('ItemTypeProperty.json') as f:
            item_type_property_json = json.load(f)
            assert item_type_property_json == expected_item_type_property

        # Render the error screen if item type is for harvesting
        item_type = item_type_data['item_type']
        item_type.harvesting_type = True
        db.session.commit()
        url = url_for('itemtypesregister.export',item_type_id=1)
        with caplog.at_level('ERROR'):
            res = client.get(url)
        mock_render.assert_called_with('weko_itemtypes_ui/admin/error.html')
        assert 'item_type_id=1 is cannot export' in caplog.text

#     def item_type_import(self):
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_admin.py::TestItemTypeMetaDataView::test_item_type_import -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
    @patch('weko_itemtypes_ui.utils.fix_json_schema')
    @patch('weko_itemtypes_ui.admin.update_required_schema_not_exist_in_form')
    def test_item_type_import(
        self, mock_update_required_schema,
        mock_fix_json_schema, client, admin_view, users, create_itemtype_zip,
        caplog
    ):
        # Setup
        login_user_via_session(client=client,email=users[0]['email'])
        zip_file = create_itemtype_zip(id=1)
        url = url_for('itemtypesregister.item_type_import')
        test_datetime = '2024-09-06T00:00:00+00:00'

        # Error if 'item_type_name' is missing
        file = FileStorage(filename='test.zip',stream=BytesIO(b'test'))
        data = {
            'item_type_name': '',
            'file': (file, '')
        }
        res = client.post(url,data=data,content_type='multipart/form-data')
        assert json.loads(res.data)['msg'] == 'No item type name Error'

        # Error if 'input_file' is missing
        data = {
            'item_type_name': 'error test',
            'file': (BytesIO(b''), '')
        }
        res = client.post(url,data=data,content_type='multipart/form-data')
        assert json.loads(res.data)['msg'] == 'No file Error'

        # Error if 'input_file.mimetype' is missing
        file = FileStorage(
            filename='test.zip',stream=BytesIO(b'test'),content_type=''
        )
        data = {
            'item_type_name': 'error test',
            'file': (file, '')
        }
        res = client.post(url, data=data, content_type='multipart/form-data')
        assert json.loads(res.data)['msg'] == 'Illegal mimetype Error'

        # Assert that a debug log with the ignored file is generated
        file = BytesIO(zip_file.getvalue())
        extra_zip = BytesIO()
        file_contents = {}
        with ZipFile(file, 'r') as zip_in:
            for file_name in zip_in.namelist():
                with zip_in.open(file_name) as f:
                    content = f.read().decode('utf-8')
                    file_contents[file_name] = json.loads(content)
        file_contents['extra.json'] = {'extra': 'example'}
        with ZipFile(extra_zip, 'w', ZIP_DEFLATED) as zip_out:
            for file_name, content in file_contents.items():
                zip_out.writestr(file_name, json.dumps(content))
        extra_zip.seek(0)
        data = {
            'item_type_name': 'success test 1',
            'file': (extra_zip, 'test.zip')
        }
        with caplog.at_level('DEBUG'):
            res = client.post(url, data=data, content_type='multipart/form-data')
        assert 'extra.json is ignored' in caplog.text

        # Error if the required files are missing in the imported ZIP file
        file = BytesIO(zip_file.getvalue())
        insufficient_zip = BytesIO()
        file_contents = {}
        with ZipFile(file, 'r') as zip_in:
            for file_name in zip_in.namelist():
                with zip_in.open(file_name) as f:
                    content = f.read().decode('utf-8')
                    file_contents[file_name] = json.loads(content)
        del file_contents['ItemType.json']
        with ZipFile(insufficient_zip, 'w', ZIP_DEFLATED) as zip_out:
            for file_name, content in file_contents.items():
                zip_out.writestr(file_name, json.dumps(content))
        insufficient_zip.seek(0)
        data = {
            'item_type_name': 'error test',
            'file': (insufficient_zip, 'test.zip')
        }
        res = client.post(url, data=data, content_type='multipart/form-data')
        assert json.loads(res.data)['msg'] == (
            'Failed to import the item type. Zip file contents invalid.'
        )

        # Error if ItemType.json does not have a 'render' key
        file = BytesIO(zip_file.getvalue())
        no_render_zip = BytesIO()
        file_contents = {}
        with ZipFile(file, 'r') as zip_in:
            for file_name in zip_in.namelist():
                with zip_in.open(file_name) as f:
                    content = f.read().decode('utf-8')
                    file_contents[file_name] = json.loads(content)
        del file_contents['ItemType.json']['render']
        with ZipFile(no_render_zip, 'w', ZIP_DEFLATED) as zip_out:
            for file_name, content in file_contents.items():
                zip_out.writestr(file_name, json.dumps(content))
        no_render_zip.seek(0)
        data = {
            'item_type_name': 'error test',
            'file': (no_render_zip, 'test.zip')
        }
        res = client.post(url, data=data, content_type='multipart/form-data')
        assert res.status_code == 400
        assert json.loads(res.data)['msg'] == (
            'Failed to import the item type. '
            '"render" is missing or invalid in ItemType.json.'
        )
        
        # Error if 'render' value does not have a 'table_row' key
        file = BytesIO(zip_file.getvalue())
        no_table_row_zip = BytesIO()
        file_contents = {}
        with ZipFile(file, 'r') as zip_in:
            for file_name in zip_in.namelist():
                with zip_in.open(file_name) as f:
                    content = f.read().decode('utf-8')
                    file_contents[file_name] = json.loads(content)
        del file_contents['ItemType.json']['render']['table_row']
        with ZipFile(no_table_row_zip, 'w', ZIP_DEFLATED) as zip_out:
            for file_name, content in file_contents.items():
                zip_out.writestr(file_name, json.dumps(content))
        no_table_row_zip.seek(0)
        data = {
            'item_type_name': 'error test',
            'file': (no_table_row_zip, 'test.zip')
        }
        res = client.post(url, data=data, content_type='multipart/form-data')
        assert res.status_code == 400
        assert json.loads(res.data)['msg'] == (
            'Failed to import the item type. '
            '"table_row" is missing or invalid in "render".'
        )

        # Error if 'render' value does not have a 'meta_list' key
        file = BytesIO(zip_file.getvalue())
        no_meta_list_zip = BytesIO()
        file_contents = {}
        with ZipFile(file, 'r') as zip_in:
            for file_name in zip_in.namelist():
                with zip_in.open(file_name) as f:
                    content = f.read().decode('utf-8')
                    file_contents[file_name] = json.loads(content)
        del file_contents['ItemType.json']['render']['meta_list']
        with ZipFile(no_meta_list_zip, 'w', ZIP_DEFLATED) as zip_out:
            for file_name, content in file_contents.items():
                zip_out.writestr(file_name, json.dumps(content))
        no_meta_list_zip.seek(0)
        data = {
            'item_type_name': 'error test',
            'file': (no_meta_list_zip, 'test.zip')
        }
        res = client.post(url, data=data, content_type='multipart/form-data')
        assert res.status_code == 400
        assert json.loads(res.data)['msg'] == (
            'Failed to import the item type. '
            '"meta_list" is missing or invalid in "render".'
        )

        # Error if 'json_schema' is missing
        file = BytesIO(zip_file.getvalue())
        mock_fix_json_schema.return_value = None
        mock_update_required_schema.return_value = None
        data = {
            'item_type_name': 'error test',
            'file': (file, 'test.zip')
        }
        res = client.post(url, data=data, content_type='multipart/form-data')
        assert json.loads(res.data)['msg'] == (
            'Failed to import the item type. Schema is in wrong format.'
        )
        mock_fix_json_schema.return_value = (
            {'properties': {'filename': {'items': ['test_file']}}}
        )
        mock_update_required_schema.return_value = (
            {'filename': {'items': ['test_file']}}
        )

        # Import fails if forced-import is False and
        # item type has unknown properties
        with patch.dict(
            current_app.config,
            {'WEKO_ITEMTYPES_UI_FORCED_IMPORT_ENABLED': False}
        ):
            file = BytesIO(zip_file.getvalue())
            data = {
                'item_type_name': 'failure test',
                'file': (file, 'test.zip')
            }
            res = client.post(url, data=data, content_type='multipart/form-data')
            assert json.loads(res.data)['msg'] == (
                'Failed to import the item type. Unregistered properties detected.'
            )

        # Import suceeds if forced-import is False but
        # item type does not have unknown properties
        with patch(
            'weko_itemtypes_ui.admin.ItemTypeProps.get_record'
        ) as mock_get_record:
            with patch.dict(
                current_app.config,
                {'WEKO_ITEMTYPES_UI_FORCED_IMPORT_ENABLED': False}
            ):
                class MockProp:
                    updated = datetime(2024, 9, 6, 0, 0)
                mock_get_record.return_value = MockProp()
                file = BytesIO(zip_file.getvalue())
                data = {
                    'item_type_name': 'success test 2',
                    'file': (file, 'test.zip')
                }
                res = client.post(url, data=data, content_type='multipart/form-data')
                assert json.loads(res.data)['msg'] == (
                    'The item type imported successfully.'
                )

        # Import suceeds if forced-import is True, even when
        # item type has unknown properties
        with patch.dict(
            current_app.config,
            {'WEKO_ITEMTYPES_UI_FORCED_IMPORT_ENABLED': True}
        ):
            file = BytesIO(zip_file.getvalue())
            new_prop_zip = BytesIO()
            file_contents = {}
            with ZipFile(file, 'r') as zip_in:
                for file_name in zip_in.namelist():
                    with zip_in.open(file_name) as f:
                        content = f.read().decode('utf-8')
                        file_contents[file_name] = json.loads(content)
            file_contents['ItemType.json']['render']['table_row'] = ['row1', 'row2']
            file_contents['ItemType.json']['render']['meta_list'] = {
                'row1': {'input_type': 'cus_1'},
                'row2': {'input_type': 'cus_2'}
            }
            new_prop = {
                'id': 2,
                'name': 'test property 2',
                'schema': {'type': 'integer'},
                'form': {'title_i18n': {'en': 'test property 2'}},
                'forms': ['test form 2'],
                'delflg': False,
                'sort': None,
                'created': '2024-09-07T00:00:00+00:00',
                'updated': '2024-09-07T00:00:00+00:00'
            }
            file_contents['ItemTypeProperty.json'].append(new_prop)
            with ZipFile(new_prop_zip, 'w', ZIP_DEFLATED) as zip_out:
                for file_name, content in file_contents.items():
                    zip_out.writestr(file_name, json.dumps(content))
            new_prop_zip.seek(0)
            data = {
                'item_type_name': 'success test 3',
                'file': (new_prop_zip, 'test.zip')
            }
            res = client.post(url, data=data, content_type='multipart/form-data')
            assert json.loads(res.data)['msg'] == (
                'The item type imported successfully.'
            )

        # Import suceeds if forced-import is True and
        # item type does not have unknown properties
        with patch(
            'weko_itemtypes_ui.admin.ItemTypeProps.get_record'
        ) as mock_get_record:
            with patch.dict(
                current_app.config,
                {'WEKO_ITEMTYPES_UI_FORCED_IMPORT_ENABLED': True}
            ):
                class MockProp:
                    updated = datetime(2024, 9, 6, 0, 0)
                mock_get_record.return_value = MockProp()
                file = BytesIO(zip_file.getvalue())
                data = {
                    'item_type_name': 'success test 4',
                    'file': (file, 'test.zip')
                }
                res = client.post(url, data=data, content_type='multipart/form-data')
                assert json.loads(res.data)['msg'] == (
                    'The item type imported successfully.'
                )

        # Error if the database commit fails
        with patch(
            'weko_itemtypes_ui.admin.db.session.commit',
            side_effect=Exception('Commit error test')
        ):
            file = BytesIO(zip_file.getvalue())
            data = {
                'item_type_name': 'failure test',
                'file': (file, 'test.zip')
            }
            res = client.post(url, data=data, content_type='multipart/form-data')
            assert res.status_code == 400
            assert 'Failed to import the item type' in json.loads(res.data)['msg']
        
        # Import suceeds but duplicated IDs reported
        with patch.dict(
            current_app.config,
            {'WEKO_ITEMTYPES_UI_FORCED_IMPORT_ENABLED': True} 
        ):
            test_id = 1
            expected_json = {
                '1': {
                    'created': '2024-09-06T00:00:00+00:00',
                    'delflg': False,
                    'form': {'title_i18n': {'en': 'test property'}},
                    'forms': ['test form'],
                    'id': 1,
                    'name': 'test property 1',
                    'schema': {'type': 'string'},
                    'sort': None,
                    'updated': '2024-09-06T00:00:00+00:00'
                }
            }
            file = BytesIO(zip_file.getvalue())
            data = {
                'item_type_name': 'duplication test',
                'file': (file, 'test.zip')
            }
            res = client.post(url, data=data, content_type='multipart/form-data')
            file = BytesIO(zip_file.getvalue())
            data = {
                'item_type_name': 'duplication test2',
                'file': (file, 'test.zip')
            }
            class MockProp:
                id = test_id
                updated = datetime(2024, 9, 7, 0, 0)
            mock_get_record.return_value = MockProp()
            res = client.post(url, data=data, content_type='multipart/form-data')
            assert json.loads(res.data)['msg'] == (
                'The item type imported successfully, but these property '
                'IDs were duplicated and were not imported:'
            )
            assert json.loads(res.data)['duplicated_props'] == expected_json


# class ItemTypeSchema(SQLAlchemyAutoSchema):
#     class Meta:
# class ItemTypeNameSchema(SQLAlchemyAutoSchema):
#     class Meta:
# class ItemTypeMappingSchema(SQLAlchemyAutoSchema):
#     class Meta:
# class ItemTypePropertySchema(SQLAlchemyAutoSchema):
#     class Meta:
# class ItemTypePropertiesView(BaseView):
class TestItemTypePropertiesView():
#     def index(self, property_id=0):
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_admin.py::TestItemTypePropertiesView::test_index_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
    @pytest.mark.parametrize("index,is_permission",[
        (0,True),
        (1,False),
        (2,False),
        (3,False),
        (4,False),
        (5,False),
        (7,False)
    ])
    def test_index_acl(self,client,admin_view,users,index,is_permission):
        login_user_via_session(client,email=users[index]["email"])
        url = url_for("itemtypesproperties.index")
        res = client.get(url)
        assert_statuscode_with_role(res,is_permission)

# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_admin.py::TestItemTypePropertiesView::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
    def test_index(self,client,db,admin_view,users,itemtype_props,mocker):
        login_user_via_session(client,email=users[0]["email"])
        billing_permission = BillingPermission(user_id=1,is_active=False)
        db.session.add(billing_permission)
        db.session.commit()
        
        url = url_for("itemtypesproperties.index")
        test_props = itemtype_props.copy()
        test_props.pop(3)
        test_props.pop(2)
        mock_render = mocker.patch("weko_itemtypes_ui.admin.ItemTypePropertiesView.render",return_value=make_response())
        res = client.get(url)
        mock_render.assert_called_with(
            'weko_itemtypes_ui/admin/create_property.html',
            lists=test_props,
            lang_code="en"
        )
        
        billing_permission.is_active=True
        db.session.merge(billing_permission)
        db.session.commit()
        test_props=itemtype_props.copy()
        test_props.pop(3)
        
        mock_render = mocker.patch("weko_itemtypes_ui.admin.ItemTypePropertiesView.render",return_value=make_response())
        res = client.get(url)
        mock_render.assert_called_with(
            'weko_itemtypes_ui/admin/create_property.html',
            lists=test_props,
            lang_code="en"
        )
#     def get_property(self, property_id=0):
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_admin.py::TestItemTypePropertiesView::test_get_property -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
    @pytest.mark.parametrize("index,is_permission",[
        (0,True),
        (1,False),
        (2,False),
        (3,False),
        (4,False),
        (5,False),
        (7,False)
    ])
    def test_get_property_acl(self,client,admin_view,users,itemtype_props,index,is_permission):
        login_user_via_session(client,email=users[index]["email"])
        url = url_for("itemtypesproperties.get_property",property_id=1)
        res = client.get(url)
        assert_statuscode_with_role(res,is_permission)
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_admin.py::TestItemTypePropertiesView::test_get_property -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
    def test_get_property(self,client,admin_view,users,itemtype_props):
        login_user_via_session(client,email=users[0]["email"])
        url = url_for("itemtypesproperties.get_property",property_id=1)
        res = client.get(url)
        assert res.status_code == 200
        result = json.loads(res.data)
        assert result["id"] == 1
        assert result["name"] == "test1"
        assert result["schema"] == {"properties":{"filename":{"items":["test_file"]}}}
        assert result["form"] == {"title_i18n":{"en":"test_name_en"}}
        assert result["forms"] == {}
        
#     def custom_property_new(self, property_id=0):
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_admin.py::TestItemTypePropertiesView::test_custom_property_new -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
    @pytest.mark.parametrize("index,is_permission",[
        (0,True),
        (1,False),
        (2,False),
        (3,False),
        (4,False),
        (5,False),
        (7,False)
    ])
    def test_custom_property_new_acl(self,client,admin_view,users,index,is_permission):
        login_user_via_session(client,email=users[index]["email"])
        url = url_for("itemtypesproperties.custom_property_new")
        res = client.post(url,json={})
        assert_statuscode_with_role(res,is_permission)
        url = url_for("itemtypesproperties.custom_property_new",property_id=1)
        res = client.post(url,json={})
        assert_statuscode_with_role(res,is_permission)
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_admin.py::TestItemTypePropertiesView::test_custom_property_new -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
    def test_custom_property_new(self,client,admin_view,db,users,mocker):
        login_user_via_session(client,email=users[0]["email"])
        mocker.patch("weko_records.api.before_record_insert.send")
        mocker.patch("weko_records.api.after_record_insert.send")
        url = url_for("itemtypesproperties.custom_property_new")
        data = {
            "name":"new_prop",
            "schema":{"key_schema":"value_schema"},
            "form1":{"key_form1":"value_form1"},
            "form2":{"key_form2":"value_form2"}
        }
        res = client.post(url,json=data,headers={"Content-Type":"application/json"})
        assert res.status_code == 200
        assert json.loads(res.data)["msg"] == "Saved property successfully."
        result = obj = ItemTypeProperty.query.filter_by(id=1,
                                                       delflg=False).first()
        assert result.name == "new_prop"
        assert result.schema == {"key_schema":"value_schema"}
        
        # raise Exception
        with patch("weko_itemtypes_ui.admin.ItemTypeProps.create",side_effect=Exception):
            res = client.post(url,json=data,headers={"Content-Type":"application/json"})
            assert res.status_code == 200
            assert json.loads(res.data)["msg"] == 'Failed to save property.'
        
        # header is not application/json
        data = "test_data"
        res = client.post(url,headers={"Content-Type":"text/plain"})
        assert res.status_code ==200
        assert json.loads(res.data)["msg"] == "Header Error"
# class ItemTypeMappingView(BaseView):
class TestItemTypeMappingView:
#     def index(self, ItemTypeID=0):
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_admin.py::TestItemTypeMappingView::test_index_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
    @pytest.mark.parametrize("index,is_permission",[
        (0,True),
        (1,True),
        (2,False),
        (3,False),
        (4,False),
        (5,False),
        (7,False)
    ])
    def test_index_acl(self,client,admin_view,users,index,is_permission):
        login_user_via_session(client,email=users[index]["email"])
        url = url_for("itemtypesmapping.index")
        res = client.get(url)
        assert_statuscode_with_role(res,is_permission)
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_admin.py::TestItemTypeMappingView::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
    def test_index(self,app,client,admin_view,users,item_type,oaiserver_schema,mocker):
        login_user_via_session(client,email=users[0]["email"])
        login(app,client,obj=users[0]["obj"])
        url = url_for("itemtypesmapping.index")
        # not exist itemtypes
        with patch("weko_itemtypes_ui.admin.ItemTypes.get_latest",return_value=[]):
            mock_render = mocker.patch("weko_itemtypes_ui.admin.ItemTypeMappingView.render",return_value=make_response())
            res = client.get(url)
            mock_render.assert_called_with("weko_itemtypes_ui/admin/error.html")
        
        # item_type is None
        mock_render = mocker.patch("weko_itemtypes_ui.admin.redirect",return_value=make_response())
        res = client.get(url)
        mock_render.assert_called_with(
            "/admin/itemtypes/mapping/1"
        )
        
        url = url_for("itemtypesmapping.index",ItemTypeID=7)
        mock_render = mocker.patch("weko_itemtypes_ui.admin.ItemTypeMappingView.render",return_value=make_response())
        mocker.patch("weko_itemtypes_ui.admin.remove_xsd_prefix",return_value="called remove_xsd_prefix")
        res = client.get(url,headers={"Accept-Language":"ja"})
        mock_render.assert_called_with(
            "weko_itemtypes_ui/admin/create_mapping.html",
            lists=[data["item_type_name"] for data in item_type],
            hide_mapping_prop={},
            mapping_name="jpcoar_mapping",
            hide_itemtype_prop={"pubdate": {"type": "string","title": "PubDate","format": "datetime"},"test_not_form":{"title":"test_not_form_title"},"test_key1":{"title":"test_key1_no_title"},"test_key2":{"title":"test_key2_no_title"},"test_key3":{"title":"test_key3_no_title"},"test_key4":{"title":"test_key4_no_title"},"test_key5":{"title":"test_key5_no_title"},"test_key6":{"title":"test_key6_no_title"},"test_key7":{"title":"test_key7_no_title"},"test_key8":{"title":"test_key8_no_title"},"test_key9":{"title":"test_key9_no_title"},"test1_subkey1":{"title":"test1_subkey1_no_title"},"test2_subkey1":{"title":"test2_subkey1_no_title"},"test3_subkey1":{"title":"test3_subkey1_no_title"},"test4_subkey1":{"title":"test4_subkey1_no_title"},"test5_subkey1":{"title":"test5_subkey1_no_title"}},
            jpcoar_prop_lists="called remove_xsd_prefix",
            meta_system={
                "system_identifier_doi":{
                    "title_i18n":{"en":"system_identifier_doi_en"},
                    "title":"system_identifier_doi_en"
                },
                "system_identifier_hdl":{
                    "title_i18n":{
                        "en":"system_identifier_hdl_en",
                        "ja":"system_identifier_hdl_ja"},
                    "title":"system_identifier_hdl_ja"
                }
            },
            itemtype_list=[("pubdate","PubDate"),("test_key1","test1_ja"),("test_key2","test_key2_no_title"),("test_key3","test_key3_no_title"),("test_key4","test_key4_title"),("test_key5","test_key5_title"),("test_key6","test_key6_ja"),("test_key7","test_key7_no_title"),("test_key8","test_key8_no_title"),("test_key9","test_key9_title"),("test1_subkey1","test1_subkey1_title"),("test2_subkey1","test2_subkey1_no_title"),("test3_subkey1","test3_subkey1_no_title"),("test4_subkey1","test4.sub1.ja"),("test5_subkey1","test5.sub.title"),("test_not_form","test_not_form_title")],
            id=7,
            is_system_admin=True,
            lang_code="en"
        )
 # current_app.logger.error("lists:{}".format(lists))
            # # lists:[<ItemTypeName 1>, <ItemTypeName 2>, <ItemTypeName 3>, <ItemTypeName 4>, <ItemTypeName 5>, <ItemTypeName 6>, <ItemTypeName 7>, <ItemTypeName 8>, <ItemTypeName 9>, <ItemTypeName 10>, <ItemTypeName 11>, <ItemTypeName 12>, <ItemTypeName 13>, <ItemTypeName 14>, <ItemTypeName 15>, <ItemTypeName 16>, <ItemTypeName 22>, <ItemTypeName 32>, <ItemTypeName 33>, <ItemTypeName 34>, <ItemTypeName 35>, <ItemTypeName 36>, <ItemTypeName 37>, <ItemTypeName 38>, <ItemTypeName 39>, <ItemTypeName 40>, <ItemTypeName 41>, <ItemTypeName 31001>, <ItemTypeName 31002>, <ItemTypeName 31003>, <ItemTypeName 40001>]#
            # current_app.logger.error("item_type_mapping:{}".format(item_type_mapping['item_1663165432106']))
            # # current_app.logger.error("mapping_name:{}".format(mapping_name))
            # # current_app.logger.error("itemtype_prop:{}".format(itemtype_prop))
            # # item_type_mapping:{'pubdate': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'date': ''}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'date': ''}}, 'system_file': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'system_file': {'URI': {'@value': 'subitem_systemfile_filename_uri', '@attributes': {'label': 'subitem_systemfile_filename_label', 'objectType': 'subitem_systemfile_filename_type'}}, 'date': {'@value': 'subitem_systemfile_datetime_date', '@attributes': {'dateType': 'subitem_systemfile_datetime_type'}}, 'extent': {'@value': 'subitem_systemfile_size'}, 'version': {'@value': 'subitem_systemfile_version'}, 'mimeType': {'@value': 'subitem_systemfile_mimetype'}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'system_file': {'URI': {'@value': 'subitem_systemfile_filename_uri', '@attributes': {'label': 'subitem_systemfile_filename_label', 'objectType': 'subitem_systemfile_filename_type'}}, 'date': {'@value': 'subitem_systemfile_datetime_date', '@attributes': {'dateType': 'subitem_systemfile_datetime_type'}}, 'extent': {'@value': 'subitem_systemfile_size'}, 'version': {'@value': 'subitem_systemfile_version'}, 'mimeType': {'@value': 'subitem_systemfile_mimetype'}}}}, 'item_1551264308487': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'title': {'@value': 'subitem_1551255647225', '@attributes': {'xml:lang': 'subitem_1551255648112'}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'title': {'@value': 'subitem_1551255647225', '@attributes': {'xml:lang': 'subitem_1551255648112'}}}}, 'item_1551264326373': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'alternative': {'@value': 'subitem_1551255720400', '@attributes': {'xml:lang': 'subitem_1551255721061'}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'alternative': {'@value': 'subitem_1551255720400', '@attributes': {'xml:lang': 'subitem_1551255721061'}}}}, 'item_1551264340087': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'creator': {'givenName': {'@value': 'subitem_1551255991424.subitem_1551256006332', '@attributes': {'xml:lang': 'subitem_1551255991424.subitem_1551256007414'}}, 'familyName': {'@value': 'subitem_1551255929209.subitem_1551255938498', '@attributes': {'xml:lang': 'subitem_1551255929209.subitem_1551255964991'}}, 'affiliation': {'nameIdentifier': {'@value': 'subitem_1551256087090.subitem_1551256089084.subitem_1551256097891', '@attributes': {'nameIdentifierURI': 'subitem_1551256087090.subitem_1551256089084.subitem_1551256147368', 'nameIdentifierScheme': 'subitem_1551256087090.subitem_1551256089084.subitem_1551256145018'}}, 'affiliationName': {'@value': 'subitem_1551256087090.subitem_1551256229037.subitem_1551256259183', '@attributes': {'xml:lang': 'subitem_1551256087090.subitem_1551256229037.subitem_1551256259899'}}}, 'creatorName': {'@value': 'subitem_1551255898956.subitem_1551255905565', '@attributes': {'xml:lang': 'subitem_1551255898956.subitem_1551255907416'}}, 'nameIdentifier': {'@value': 'subitem_1551255789000.subitem_1551255793478', '@attributes': {'nameIdentifierURI': 'subitem_1551255789000.subitem_1551255795486', 'nameIdentifierScheme': 'subitem_1551255789000.subitem_1551255794292'}}, 'creatorAlternative': {'@value': 'subitem_1551256025394.subitem_1551256035730', '@attributes': {'xml:lang': 'subitem_1551256025394.subitem_1551256055588'}}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'creator': {'givenName': {'@value': 'subitem_1551255991424.subitem_1551256006332', '@attributes': {'xml:lang': 'subitem_1551255991424.subitem_1551256007414'}}, 'familyName': {'@value': 'subitem_1551255929209.subitem_1551255938498', '@attributes': {'xml:lang': 'subitem_1551255929209.subitem_1551255964991'}}, 'affiliation': {'nameIdentifier': {'@value': 'subitem_1551256087090.subitem_1551256089084.subitem_1551256097891', '@attributes': {'nameIdentifierURI': 'subitem_1551256087090.subitem_1551256089084.subitem_1551256147368', 'nameIdentifierScheme': 'subitem_1551256087090.subitem_1551256089084.subitem_1551256145018'}}, 'affiliationName': {'@value': 'subitem_1551256087090.subitem_1551256229037.subitem_1551256259183', '@attributes': {'xml:lang': 'subitem_1551256087090.subitem_1551256229037.subitem_1551256259899'}}}, 'creatorName': {'@value': 'subitem_1551255898956.subitem_1551255905565', '@attributes': {'xml:lang': 'subitem_1551255898956.subitem_1551255907416'}}, 'nameIdentifier': {'@value': 'subitem_1551255789000.subitem_1551255793478', '@attributes': {'nameIdentifierURI': 'subitem_1551255789000.subitem_1551255795486', 'nameIdentifierScheme': 'subitem_1551255789000.subitem_1551255794292'}}, 'creatorAlternative': {'@value': 'subitem_1551256025394.subitem_1551256035730', '@attributes': {'xml:lang': 'subitem_1551256025394.subitem_1551256055588'}}}}}, 'item_1551264418667': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'contributor': {'givenName': {'@value': 'subitem_1551257339190.subitem_1551257342360', '@attributes': {'xml:lang': 'subitem_1551257339190.subitem_1551257343979'}}, 'familyName': {'@value': 'subitem_1551257272214.subitem_1551257314588', '@attributes': {'xml:lang': 'subitem_1551257272214.subitem_1551257316910'}}, '@attributes': {'contributorType': 'subitem_1551257036415'}, 'affiliation': {'nameIdentifier': {'@value': 'subitem_1551257419251.subitem_1551257421633.subitem_1551261472867', '@attributes': {'nameIdentifierURI': 'subitem_1551257419251.subitem_1551257421633.subitem_1551261493409', 'nameIdentifierScheme': 'subitem_1551257419251.subitem_1551257421633.subitem_1551261485670'}}, 'affiliationName': {'@value': 'subitem_1551257419251.subitem_1551261534334.subitem_1551261542403', '@attributes': {'xml:lang': 'subitem_1551257419251.subitem_1551261534334.subitem_1551261546333'}}}, 'nameIdentifier': {'@value': 'subitem_1551257150927.subitem_1551257152742', '@attributes': {'nameIdentifierURI': 'subitem_1551257150927.subitem_1551257228080', 'nameIdentifierScheme': 'subitem_1551257150927.subitem_1551257172531'}}, 'contributorName': {'@value': 'subitem_1551257245638.subitem_1551257276108', '@attributes': {'xml:lang': 'subitem_1551257245638.subitem_1551257279831'}}, 'contributorAlternative': {'@value': 'subitem_1551257372442.subitem_1551257374288', '@attributes': {'xml:lang': 'subitem_1551257372442.subitem_1551257375939'}}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'contributor': {'givenName': {'@value': 'subitem_1551257339190.subitem_1551257342360', '@attributes': {'xml:lang': 'subitem_1551257339190.subitem_1551257343979'}}, 'familyName': {'@value': 'subitem_1551257272214.subitem_1551257314588', '@attributes': {'xml:lang': 'subitem_1551257272214.subitem_1551257316910'}}, '@attributes': {'contributorType': 'subitem_1551257036415'}, 'affiliation': {'nameIdentifier': {'@value': 'subitem_1551257419251.subitem_1551257421633.subitem_1551261472867', '@attributes': {'nameIdentifierURI': 'subitem_1551257419251.subitem_1551257421633.subitem_1551261493409', 'nameIdentifierScheme': 'subitem_1551257419251.subitem_1551257421633.subitem_1551261485670'}}, 'affiliationName': {'@value': 'subitem_1551257419251.subitem_1551261534334.subitem_1551261542403', '@attributes': {'xml:lang': 'subitem_1551257419251.subitem_1551261534334.subitem_1551261546333'}}}, 'nameIdentifier': {'@value': 'subitem_1551257150927.subitem_1551257152742', '@attributes': {'nameIdentifierURI': 'subitem_1551257150927.subitem_1551257228080', 'nameIdentifierScheme': 'subitem_1551257150927.subitem_1551257172531'}}, 'contributorName': {'@value': 'subitem_1551257245638.subitem_1551257276108', '@attributes': {'xml:lang': 'subitem_1551257245638.subitem_1551257279831'}}, 'contributorAlternative': {'@value': 'subitem_1551257372442.subitem_1551257374288', '@attributes': {'xml:lang': 'subitem_1551257372442.subitem_1551257375939'}}}}}, 'item_1551264447183': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'accessRights': {'@value': 'subitem_1551257553743', '@attributes': {'rdf:resource': 'subitem_1551257578398'}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'accessRights': {'@value': 'subitem_1551257553743', '@attributes': {'rdf:resource': 'subitem_1551257578398'}}}}, 'item_1551264605515': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'apc': {'@value': 'subitem_1551257776901'}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'apc': {'@value': 'subitem_1551257776901'}}}, 'item_1551264629907': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'rights': {'@value': 'subitem_1551257025236.subitem_1551257043769', '@attributes': {'xml:lang': 'subitem_1551257025236.subitem_1551257047388', 'rdf:resource': 'subitem_1551257030435'}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'rights': {'@value': 'subitem_1551257025236.subitem_1551257043769', '@attributes': {'xml:lang': 'subitem_1551257025236.subitem_1551257047388', 'rdf:resource': 'subitem_1551257030435'}}}}, 'item_1551264767789': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'rightsHolder': {'nameIdentifier': {'@value': 'subitem_1551257143244.subitem_1551257145912', '@attributes': {'nameIdentifierURI': 'subitem_1551257143244.subitem_1551257232980', 'nameIdentifierScheme': 'subitem_1551257143244.subitem_1551257156244'}}, 'rightsHolderName': {'@value': 'subitem_1551257249371.subitem_1551257255641', '@attributes': {'xml:lang': 'subitem_1551257249371.subitem_1551257257683'}}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'rightsHolder': {'nameIdentifier': {'@value': 'subitem_1551257143244.subitem_1551257145912', '@attributes': {'nameIdentifierURI': 'subitem_1551257143244.subitem_1551257232980', 'nameIdentifierScheme': 'subitem_1551257143244.subitem_1551257156244'}}, 'rightsHolderName': {'@value': 'subitem_1551257249371.subitem_1551257255641', '@attributes': {'xml:lang': 'subitem_1551257249371.subitem_1551257257683'}}}}}, 'item_1551264822581': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'subject': {'@value': 'subitem_1551257315453', '@attributes': {'xml:lang': 'subitem_1551257323812', 'subjectURI': 'subitem_1551257343002', 'subjectScheme': 'subitem_1551257329877'}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'subject': {'@value': 'subitem_1551257315453', '@attributes': {'xml:lang': 'subitem_1551257323812', 'subjectURI': 'subitem_1551257343002', 'subjectScheme': 'subitem_1551257329877'}}}}, 'item_1551264846237': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'description': {'@value': 'subitem_1551255577890', '@attributes': {'xml:lang': 'subitem_1551255592625', 'descriptionType': 'subitem_1551255637472'}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'description': {'@value': 'subitem_1551255577890', '@attributes': {'xml:lang': 'subitem_1551255592625', 'descriptionType': 'subitem_1551255637472'}}}}, 'item_1551264917614': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'publisher': {'@value': 'subitem_1551255702686', '@attributes': {'xml:lang': 'subitem_1551255710277'}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'publisher': {'@value': 'subitem_1551255702686', '@attributes': {'xml:lang': 'subitem_1551255710277'}}}}, 'item_1551264974654': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'date': {'@value': 'subitem_1551255753471', '@attributes': {'dateType': 'subitem_1551255775519'}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'date': {'@value': 'subitem_1551255753471', '@attributes': {'dateType': 'subitem_1551255775519'}}}}, 'item_1551265002099': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'language': {'@value': 'subitem_1551255818386'}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'language': {'@value': 'subitem_1551255818386'}}}, 'item_1551265032053': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'type': {'@value': 'resourcetype', '@attributes': {'rdf:resource': 'resourceuri'}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'type': {'@value': 'resourcetype', '@attributes': {'rdf:resource': 'resourceuri'}}}}, 'item_1551265118680': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'versionType': {'@value': 'subitem_1551256025676'}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'versionType': {'@value': 'subitem_1551256025676'}}}, 'item_1551265227803': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'relation': {'@attributes': {'relationType': 'subitem_1551256388439'}, 'relatedTitle': {'@value': 'subitem_1551256480278.subitem_1551256498531', '@attributes': {'xml:lang': 'subitem_1551256480278.subitem_1551256513476'}}, 'relatedIdentifier': {'@value': 'subitem_1551256465077.subitem_1551256478339', '@attributes': {'identifierType': 'subitem_1551256465077.subitem_1551256629524'}}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'relation': {'@attributes': {'relationType': 'subitem_1551256388439'}, 'relatedTitle': {'@value': 'subitem_1551256480278.subitem_1551256498531', '@attributes': {'xml:lang': 'subitem_1551256480278.subitem_1551256513476'}}, 'relatedIdentifier': {'@value': 'subitem_1551256465077.subitem_1551256478339', '@attributes': {'identifierType': 'subitem_1551256465077.subitem_1551256629524'}}}}}, 'item_1551265302120': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'temporal': {'@value': 'subitem_1551256918211', '@attributes': {'xml:lang': 'subitem_1551256920086'}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'temporal': {'@value': 'subitem_1551256918211', '@attributes': {'xml:lang': 'subitem_1551256920086'}}}}, 'item_1551265326081': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'geoLocation': {'geoLocationBox': {'eastBoundLongitude': {'@value': 'subitem_1551256822219.subitem_1551256831892'}, 'northBoundLatitude': {'@value': 'subitem_1551256822219.subitem_1551256840435'}, 'southBoundLatitude': {'@value': 'subitem_1551256822219.subitem_1551256834732'}, 'westBoundLongitude': {'@value': 'subitem_1551256822219.subitem_1551256824945'}}, 'geoLocationPlace': {'@value': 'subitem_1551256842196.subitem_1570008213846'}, 'geoLocationPoint': {'pointLatitude': {'@value': 'subitem_1551256778926.subitem_1551256814806'}, 'pointLongitude': {'@value': 'subitem_1551256778926.subitem_1551256783928'}}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'geoLocation': {'geoLocationBox': {'eastBoundLongitude': {'@value': 'subitem_1551256822219.subitem_1551256831892'}, 'northBoundLatitude': {'@value': 'subitem_1551256822219.subitem_1551256840435'}, 'southBoundLatitude': {'@value': 'subitem_1551256822219.subitem_1551256834732'}, 'westBoundLongitude': {'@value': 'subitem_1551256822219.subitem_1551256824945'}}, 'geoLocationPlace': {'@value': 'subitem_1551256842196.subitem_1570008213846'}, 'geoLocationPoint': {'pointLatitude': {'@value': 'subitem_1551256778926.subitem_1551256814806'}, 'pointLongitude': {'@value': 'subitem_1551256778926.subitem_1551256783928'}}}}}, 'item_1551265385290': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'fundingReference': {'awardTitle': {'@value': 'subitem_1551256688098.subitem_1551256691232', '@attributes': {'xml:lang': 'subitem_1551256688098.subitem_1551256694883'}}, 'funderName': {'@value': 'subitem_1551256462220.subitem_1551256653656', '@attributes': {'xml:lang': 'subitem_1551256462220.subitem_1551256657859'}}, 'awardNumber': {'@value': 'subitem_1551256665850.subitem_1551256671920', '@attributes': {'awardURI': 'subitem_1551256665850.subitem_1551256679403'}}, 'funderIdentifier': {'@value': 'subitem_1551256454316.subitem_1551256614960', '@attributes': {'funderIdentifierType': 'subitem_1551256454316.subitem_1551256619706'}}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'fundingReference': {'awardTitle': {'@value': 'subitem_1551256688098.subitem_1551256691232', '@attributes': {'xml:lang': 'subitem_1551256688098.subitem_1551256694883'}}, 'funderName': {'@value': 'subitem_1551256462220.subitem_1551256653656', '@attributes': {'xml:lang': 'subitem_1551256462220.subitem_1551256657859'}}, 'awardNumber': {'@value': 'subitem_1551256665850.subitem_1551256671920', '@attributes': {'awardURI': 'subitem_1551256665850.subitem_1551256679403'}}, 'funderIdentifier': {'@value': 'subitem_1551256454316.subitem_1551256614960', '@attributes': {'funderIdentifierType': 'subitem_1551256454316.subitem_1551256619706'}}}}}, 'item_1551265409089': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'sourceIdentifier': {'@value': 'subitem_1551256405981', '@attributes': {'identifierType': 'subitem_1551256409644'}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'sourceIdentifier': {'@value': 'subitem_1551256405981', '@attributes': {'identifierType': 'subitem_1551256409644'}}}}, 'item_1551265438256': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'sourceTitle': {'@value': 'subitem_1551256349044', '@attributes': {'xml:lang': 'subitem_1551256350188'}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'sourceTitle': {'@value': 'subitem_1551256349044', '@attributes': {'xml:lang': 'subitem_1551256350188'}}}}, 'item_1551265463411': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'volume': {'@value': 'subitem_1551256328147'}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'volume': {'@value': 'subitem_1551256328147'}}}, 'item_1551265520160': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'issue': {'@value': 'subitem_1551256294723'}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'issue': {'@value': 'subitem_1551256294723'}}}, 'item_1551265553273': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'numPages': {'@value': 'subitem_1551256248092'}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'numPages': {'@value': 'subitem_1551256248092'}}}, 'item_1551265569218': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'pageStart': {'@value': 'subitem_1551256198917'}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'pageStart': {'@value': 'subitem_1551256198917'}}}, 'item_1551265603279': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'pageEnd': {'@value': 'subitem_1551256185532'}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'pageEnd': {'@value': 'subitem_1551256185532'}}}, 'item_1551265738931': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'dissertationNumber': {'@value': 'subitem_1551256171004'}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'dissertationNumber': {'@value': 'subitem_1551256171004'}}}, 'item_1551265790591': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'degreeName': {'@value': 'subitem_1551256126428', '@attributes': {'xml:lang': 'subitem_1551256129013'}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'degreeName': {'@value': 'subitem_1551256126428', '@attributes': {'xml:lang': 'subitem_1551256129013'}}}}, 'item_1551265811989': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'dateGranted': {'@value': 'subitem_1551256096004'}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'dateGranted': {'@value': 'subitem_1551256096004'}}}, 'item_1551265903092': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'degreeGrantor': {'nameIdentifier': {'@value': 'subitem_1551256015892.subitem_1551256027296', '@attributes': {'nameIdentifierScheme': 'subitem_1551256015892.subitem_1551256029891'}}, 'degreeGrantorName': {'@value': 'subitem_1551256037922.subitem_1551256042287', '@attributes': {'xml:lang': 'subitem_1551256037922.subitem_1551256047619'}}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'degreeGrantor': {'nameIdentifier': {'@value': 'subitem_1551256015892.subitem_1551256027296', '@attributes': {'nameIdentifierScheme': 'subitem_1551256015892.subitem_1551256029891'}}, 'degreeGrantorName': {'@value': 'subitem_1551256037922.subitem_1551256042287', '@attributes': {'xml:lang': 'subitem_1551256037922.subitem_1551256047619'}}}}}, 'item_1570703628633': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'file': {'URI': {'@value': 'subitem_1551259623304.subitem_1551259665538', '@attributes': {'label': 'subitem_1551259623304.subitem_1551259762549', 'objectType': 'subitem_1551259623304.subitem_1551259670908'}}, 'date': {'@value': 'subitem_1551259970148.subitem_1551259972522', '@attributes': {'dateType': 'subitem_1551259970148.subitem_1551259979542'}}, 'extent': {'@value': 'subitem_1551259960284.subitem_1570697598267'}, 'mimeType': {'@value': 'subitem_1551259906932'}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'file': {'URI': {'@value': 'subitem_1551259623304.subitem_1551259665538', '@attributes': {'label': 'subitem_1551259623304.subitem_1551259762549', 'objectType': 'subitem_1551259623304.subitem_1551259670908'}}, 'date': {'@value': 'subitem_1551259970148.subitem_1551259972522', '@attributes': {'dateType': 'subitem_1551259970148.subitem_1551259979542'}}, 'extent': {'@value': 'subitem_1551259960284.subitem_1570697598267'}, 'mimeType': {'@value': 'subitem_1551259906932'}}}}, 'item_1581495656289': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'identifierRegistration': {'@value': 'subitem_1551256250276', '@attributes': {'identifierType': 'subitem_1551256259586'}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'identifierRegistration': {'@value': 'subitem_1551256250276', '@attributes': {'identifierType': 'subitem_1551256259586'}}}}, 'system_identifier_doi': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'identifier': {'@value': 'subitem_systemidt_identifier', '@attributes': {'identifierType': 'subitem_systemidt_identifier_type'}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'identifier': {'@value': 'subitem_systemidt_identifier', '@attributes': {'identifierType': 'subitem_systemidt_identifier_type'}}}}, 'system_identifier_hdl': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'identifier': {'@value': 'subitem_systemidt_identifier', '@attributes': {'identifierType': 'subitem_systemidt_identifier_type'}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'identifier': {'@value': 'subitem_systemidt_identifier', '@attributes': {'identifierType': 'subitem_systemidt_identifier_type'}}}}, 'system_identifier_uri': {'lom_mapping': '', 'lido_mapping': '', 'spase_mapping': '', 'jpcoar_mapping': {'identifier': {'@value': 'subitem_systemidt_identifier', '@attributes': {'identifierType': 'subitem_systemidt_identifier_type'}}}, 'junii2_mapping': '', 'oai_dc_mapping': '', 'display_lang_type': '', 'jpcoar_v1_mapping': {'identifier': {'@value': 'subitem_systemidt_identifier', '@attributes': {'identifierType': 'subitem_systemidt_identifier_type'}}}}}
            # # web_1            | [2022-09-15 02:50:30,987] ERROR in admin: mapping_name:jpcoar_mapping
            # # web_1            | [2022-09-15 02:50:30,988] ERROR in admin: itemtype_prop:{'pubdate': {'type': 'string', 'title': 'PubDate', 'format': 'datetime'}, 'system_file': {'type': 'object', 'title': 'File Information', 'format': 'object', 'properties': {'subitem_systemfile_size': {'type': 'string', 'title': 'SYSTEMFILE Size', 'format': 'text'}, 'subitem_systemfile_version': {'type': 'string', 'title': 'SYSTEMFILE Version', 'format': 'text'}, 'subitem_systemfile_datetime': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'subitem_systemfile_datetime_date': {'type': 'string', 'title': 'SYSTEMFILE DateTime Date', 'format': 'datetime'}, 'subitem_systemfile_datetime_type': {'enum': ['Accepted', 'Available', 'Collected', 'Copyrighted', 'Created', 'Issued', 'Submitted', 'Updated', 'Valid'], 'type': 'string', 'title': 'SYSTEMFILE DateTime Type', 'format': 'select'}}}, 'title': 'SYSTEMFILE DateTime', 'format': 'array'}, 'subitem_systemfile_filename': {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'subitem_systemfile_filename_uri': {'type': 'string', 'title': 'SYSTEMFILE Filename URI', 'format': 'text'}, 'subitem_systemfile_filename_type': {'enum': ['Abstract', 'Fulltext', 'Summary', 'Thumbnail', 'Other'], 'type': 'string', 'title': 'SYSTEMFILE Filename Type', 'format': 'select'}, 'subitem_systemfile_filename_label': {'type': 'string', 'title': 'SYSTEMFILE Filename Label', 'format': 'text'}}}, 'title': 'SYSTEMFILE Filename', 'format': 'array'}, 'subitem_systemfile_mimetype': {'type': 'string', 'title': 'SYSTEMFILE MimeType', 'format': 'text'}}, 'system_prop': True}, 'item_1663165432106': {'type': 'string', 'title': 'タイトル（日）', 'format': 'text'}, 'item_1663165460557': {'type': 'string', 'title': 'タイトル（ヨミ）', 'format': 'text'}, 'item_1663165461658': {'type': 'string', 'title': 'タイトル（他言語）', 'format': 'text'}, 'item_1663165498545': {'type': 'array', 'items': {'type': 'object', 'properties': {'interim': {'type': 'string'}}}, 'title': '著者（日）', 'maxItems': 9999, 'minItems': 1}, 'item_1663165499456': {'type': 'array', 'items': {'type': 'object', 'properties': {'interim': {'type': 'string'}}}, 'title': '著者（ヨミ）', 'maxItems': 9999, 'minItems': 1}, 'item_1663165500691': {'type': 'array', 'items': {'type': 'object', 'properties': {'interim': {'type': 'string'}}}, 'title': '著者（日）', 'maxItems': 9999, 'minItems': 1}, 'item_1663165613606': {'type': 'array', 'items': {'type': 'object', 'properties': {'interim': {'type': 'string'}}}, 'title': '権利情報', 'maxItems': 9999, 'minItems': 1}, 'item_1663165620772': {'type': 'array', 'items': {'type': 'object', 'properties': {'interim': {'type': 'string'}}}, 'title': '主題', 'maxItems': 9999, 'minItems': 1}, 'item_1663165621987': {'type': 'array', 'items': {'type': 'object', 'properties': {'interim': {'type': 'string'}}}, 'title': '出版者', 'maxItems': 9999, 'minItems': 1}, 'item_1663165623557': {'type': 'array', 'items': {'type': 'object', 'required': ['subitem_1551255818386'], 'properties': {'subitem_1551255818386': {'enum': [None, 'jpn', 'eng', 'fra', 'ita', 'spa', 'zho', 'rus', 'lat', 'msa', 'epo', 'ara', 'ell', 'kor'], 'type': ['null', 'string'], 'title': 'Language', 'format': 'select', 'currentEnum': ['jpn', 'eng', 'fra', 'ita', 'spa', 'zho', 'rus', 'lat', 'msa', 'epo', 'ara', 'ell', 'kor']}}}, 'title': '言語', 'maxItems': 9999, 'minItems': 1}, 'item_1663165658689': {'type': 'object', 'title': '資源タイプ', 'required': ['resourcetype', 'resourceuri'], 'properties': {'resourceuri': {'type': 'string', 'title': '資源タイプ識別子', 'format': 'text', 'title_i18n': {'en': 'Resource Type Identifier', 'ja': '資源タイプ識別子'}, 'title_i18n_temp': {'en': 'Resource Type Identifier', 'ja': '資源タイプ識別子'}}, 'resourcetype': {'enum': [None, 'conference paper', 'data paper', 'departmental bulletin paper', 'editorial', 'journal article', 'newspaper', 'periodical', 'review article', 'software paper', 'article', 'book', 'book part', 'cartographic material', 'map', 'conference object', 'conference proceedings', 'conference poster', 'dataset', 'interview', 'image', 'still image', 'moving image', 'video', 'lecture', 'patent', 'internal report', 'report', 'research report', 'technical report', 'policy report', 'report part', 'working paper', 'data management plan', 'sound', 'thesis', 'bachelor thesis', 'master thesis', 'doctoral thesis', 'interactive resource', 'learning object', 'manuscript', 'musical notation', 'research proposal', 'software', 'technical documentation', 'workflow', 'other'], 'type': ['null', 'string'], 'title': '資源タイプ', 'format': 'select', 'currentEnum': ['conference paper', 'data paper', 'departmental bulletin paper', 'editorial', 'journal article', 'newspaper', 'periodical', 'review article', 'software paper', 'article', 'book', 'book part', 'cartographic material', 'map', 'conference object', 'conference proceedings', 'conference poster', 'dataset', 'interview', 'image', 'still image', 'moving image', 'video', 'lecture', 'patent', 'internal report', 'report', 'research report', 'technical report', 'policy report', 'report part', 'working paper', 'data management plan', 'sound', 'thesis', 'bachelor thesis', 'master thesis', 'doctoral thesis', 'interactive resource', 'learning object', 'manuscript', 'musical notation', 'research proposal', 'software', 'technical documentation', 'workflow', 'other']}}}, 'system_identifier_doi': {'type': 'object', 'title': 'Persistent Identifier(DOI)', 'format': 'object', 'properties': {'subitem_systemidt_identifier': {'type': 'string', 'title': 'SYSTEMIDT Identifier', 'format': 'text'}, 'subitem_systemidt_identifier_type': {'enum': ['DOI', 'HDL', 'URI'], 'type': 'string', 'title': 'SYSTEMIDT Identifier Type', 'format': 'select'}}, 'system_prop': True}, 'system_identifier_hdl': {'type': 'object', 'title': 'Persistent Identifier(HDL)', 'format': 'object', 'properties': {'subitem_systemidt_identifier': {'type': 'string', 'title': 'SYSTEMIDT Identifier', 'format': 'text'}, 'subitem_systemidt_identifier_type': {'enum': ['DOI', 'HDL', 'URI'], 'type': 'string', 'title': 'SYSTEMIDT Identifier Type', 'format': 'select'}}, 'system_prop': True}, 'system_identifier_uri': {'type': 'object', 'title': 'Persistent Identifier(URI)', 'format': 'object', 'properties': {'subitem_systemidt_identifier': {'type': 'string', 'title': 'SYSTEMIDT Identifier', 'format': 'text'}, 'subitem_systemidt_identifier_type': {'enum': ['DOI', 'HDL', 'URI'], 'type': 'string', 'title': 'SYSTEMIDT Identifier Type', 'format': 'select'}}, 'system_prop': True}}
            # # current_app.logger.error("remove_xsd_prefix(jpcoar_lists),:{}".format(remove_xsd_prefix(jpcoar_lists)))
            # # current_app.logger.error("jpcoar_lists:{}".format(jpcoar_lists))
            # # current_app.logger.error("meta_system:{}".format(meta_system))
            # # current_app.logger.error("itemtype_list:{}".format(itemtype_list))
            # # current_app.logger.error("ItemTypeID:{}".format(ItemTypeID))
            # # current_app.logger.error("is_admin:{}".format(is_admin))
            # # current_app.logger.error("session.get('selected_language', 'en'):{}".format(session.get('selected_language', 'en')))
            # # meta_system:{'system_file': {'title': 'File Information', 'option': {'crtf': False, 'hidden': True, 'oneline': False, 'multiple': False, 'required': False, 'showlist': False}, 'input_type': 'cus_131', 'title_i18n': {'en': 'File Information', 'ja': 'ファイル情報'}, 'input_value': ''}, 'system_identifier_doi': {'title': 'Persistent Identifier(DOI)', 'option': {'crtf': False, 'hidden': True, 'oneline': False, 'multiple': False, 'required': False, 'showlist': False}, 'input_type': 'cus_130', 'title_i18n': {'en': 'Persistent Identifier(DOI)', 'ja': '永続識別子（DOI）'}, 'input_value': ''}, 'system_identifier_hdl': {'title': 'Persistent Identifier(HDL)', 'option': {'crtf': False, 'hidden': True, 'oneline': False, 'multiple': False, 'required': False, 'showlist': False}, 'input_type': 'cus_130', 'title_i18n': {'en': 'Persistent Identifier(HDL)', 'ja': '永続識別子（HDL）'}, 'input_value': ''}, 'system_identifier_uri': {'title': 'Persistent Identifier(URI)', 'option': {'crtf': False, 'hidden': True, 'oneline': False, 'multiple': False, 'required': False, 'showlist': False}, 'input_type': 'cus_130', 'title_i18n': {'en': 'Persistent Identifier(URI)', 'ja': '永続識別子（URI）'}, 'input_value': ''}}
            # # ERROR in admin: itemtype_list:[('pubdate', 'PubDate'), ('item_1663165432106', 'Title (ja)'), ('item_1663165460557', 'Title (Yomi)'), ('item_1663165461658', 'Title (Other)'), ('item_1663165498545', 'Author (ja)'), ('item_1663165499456', 'Author (Yomi)'), ('item_1663165500691', 'Author (other)'), ('item_1663165613606', 'Rights'), ('item_1663165620772', 'Subject'), ('item_1663165621987', 'Publisher'), ('item_1663165623557', 'Language'), ('item_1663165658689', 'Resource Type')]
            # # web_1            | [2022-09-15 02:45:23,832] ERROR in admin: ItemTypeID:40001
            # # web_1            | [2022-09-15 02:45:23,832] ERROR in admin: is_admin:True
            # # web_1            | [2022-09-15 02:45:23,833] ERROR in admin: session.get('selected_language', 'en'):en
#     def mapping_register(self):
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_admin.py::TestItemTypeMappingView::test_mapping_register_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
    @pytest.mark.parametrize("index,is_permission",[
        (0,True),
        (1,True),
        (2,False),
        (3,False),
        (4,False),
        (5,False),
        (7,False)
    ])
    def test_mapping_register_acl(self,client,admin_view,users,index,is_permission,mocker):
        login_user_via_session(client,email=users[index]["email"])
        url = url_for("itemtypesmapping.mapping_register")
        res = client.post(url,data="test",headers={"Content-Type":"text/plain"})
        assert_statuscode_with_role(res,is_permission)
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_admin.py::TestItemTypeMappingView::test_mapping_register -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
    def test_mapping_register(self,client,admin_view,users,item_type,mocker):
        mocker.patch("weko_records.api.before_record_insert.send")
        mocker.patch("weko_records.api.after_record_insert.send")
        login_user_via_session(client,email=users[0]["email"])
        url = url_for("itemtypesmapping.mapping_register")
        # header is not application/json
        res = client.post(url,data="test",headers={"Content-Type":"text/plain"})
        assert res.status_code == 200
        assert json.loads(res.data)["msg"] == "Header Error"
        
        data = {
            "item_type_id":1,
            "mapping":{"key":"test_mapping"}
        }
        # check_duplicate_mapping is not
        with patch("weko_itemtypes_ui.admin.check_duplicate_mapping",return_value=["item1","item2"]):
            res = client.post(url,json=data)
            assert res.status_code == 200
            result = json.loads(res.data)
            assert result["duplicate"] == True
            assert result["err_items"] == ["item1","item2"]
            assert result["msg"] == "Duplicate mapping as below:"
        
        with patch("weko_itemtypes_ui.admin.check_duplicate_mapping",return_value=[]):
            # nomal
            res = client.post(url,json=data)
            assert res.status_code==200
            assert json.loads(res.data)["msg"] == 'Successfully saved new mapping.'
            assert  Mapping.get_record(1) == {"key":"test_mapping"}
            
            # raise Exception
            with patch("weko_itemtypes_ui.admin.Mapping.create",side_effect=BaseException):
                res = client.post(url,json=data)
                assert json.loads(res.data)["msg"] == "Unexpected error occurred."
#     def schema_list(self, SchemaName=None):
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_admin.py::TestItemTypeMappingView::test_schema_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
    @pytest.mark.parametrize("index,is_permission",[
        (0,True),
        (1,True),
        (2,False),
        (3,False),
        (4,False),
        (5,False),
        (7,False)
    ])
    def test_schema_list_acl(self,client,admin_view,users,index,is_permission):
        login_user_via_session(client,email=users[index]["email"])
        url = url_for("itemtypesmapping.schema_list",SchemaName="not_exist_oai")
        res = client.get(url)
        assert_statuscode_with_role(res,is_permission)
# .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_admin.py::TestItemTypeMappingView::test_schema_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
    def test_schema_list(self,client,admin_view,users,oaiserver_schema):
        login_user_via_session(client,email=users[0]["email"])
        #test = {"oai_dc_mapping":{"dc:title": {"type": {"minOccurs": 1, "maxOccurs": 1, "attributes": [{"ref": "xml:lang", "name": "xml:lang", "use": "optional"}]}}, "dc:creator": {"type": {"minOccurs": 1, "maxOccurs": 1, "attributes": [{"ref": "xml:lang", "name": "xml:lang", "use": "optional"}]}}, "dc:subject": {"type": {"minOccurs": 1, "maxOccurs": 1, "attributes": [{"ref": "xml:lang", "name": "xml:lang", "use": "optional"}]}}, "dc:description": {"type": {"minOccurs": 1, "maxOccurs": 1, "attributes": [{"ref": "xml:lang", "name": "xml:lang", "use": "optional"}]}}, "dc:publisher": {"type": {"minOccurs": 1, "maxOccurs": 1, "attributes": [{"ref": "xml:lang", "name": "xml:lang", "use": "optional"}]}}, "dc:contributor": {"type": {"minOccurs": 1, "maxOccurs": 1, "attributes": [{"ref": "xml:lang", "name": "xml:lang", "use": "optional"}]}}, "dc:date": {"type": {"minOccurs": 1, "maxOccurs": 1, "attributes": [{"ref": "xml:lang", "name": "xml:lang", "use": "optional"}]}}, "dc:type": {"type": {"minOccurs": 1, "maxOccurs": 1, "attributes": [{"ref": "xml:lang", "name": "xml:lang", "use": "optional"}]}}, "dc:format": {"type": {"minOccurs": 1, "maxOccurs": 1, "attributes": [{"ref": "xml:lang", "name": "xml:lang", "use": "optional"}]}}, "dc:identifier": {"type": {"minOccurs": 1, "maxOccurs": 1, "attributes": [{"ref": "xml:lang", "name": "xml:lang", "use": "optional"}]}}, "dc:source": {"type": {"minOccurs": 1, "maxOccurs": 1, "attributes": [{"ref": "xml:lang", "name": "xml:lang", "use": "optional"}]}}, "dc:language": {"type": {"minOccurs": 1, "maxOccurs": 1, "attributes": [{"ref": "xml:lang", "name": "xml:lang", "use": "optional"}]}}, "dc:relation": {"type": {"minOccurs": 1, "maxOccurs": 1, "attributes": [{"ref": "xml:lang", "name": "xml:lang", "use": "optional"}]}}, "dc:coverage": {"type": {"minOccurs": 1, "maxOccurs": 1, "attributes": [{"ref": "xml:lang", "name": "xml:lang", "use": "optional"}]}}, "dc:rights": {"type": {"minOccurs": 1, "maxOccurs": 1, "attributes": [{"ref": "xml:lang", "name": "xml:lang", "use": "optional"}]}}}}
        test = {'oai_dc_mapping': {'contributor': {'type': {'attributes': [{'name': 'xml:lang', 'ref': 'xml:lang', 'use': 'optional'}], 'maxOccurs': 1, 'minOccurs': 1}}, 'coverage': {'type': {'attributes': [{'name': 'xml:lang', 'ref': 'xml:lang', 'use': 'optional'}], 'maxOccurs': 1, 'minOccurs': 1}}, 'creator': {'type': {'attributes': [{'name': 'xml:lang', 'ref': 'xml:lang', 'use': 'optional'}], 'maxOccurs': 1, 'minOccurs': 1}}, 'date': {'type': {'attributes': [{'name': 'xml:lang', 'ref': 'xml:lang', 'use': 'optional'}], 'maxOccurs': 1, 'minOccurs': 1}}, 'description': {'type': {'attributes': [{'name': 'xml:lang', 'ref': 'xml:lang', 'use': 'optional'}], 'maxOccurs': 1, 'minOccurs': 1}}, 'format': {'type': {'attributes': [{'name': 'xml:lang', 'ref': 'xml:lang', 'use': 'optional'}], 'maxOccurs': 1, 'minOccurs': 1}}, 'identifier': {'type': {'attributes': [{'name': 'xml:lang', 'ref': 'xml:lang', 'use': 'optional'}], 'maxOccurs': 1, 'minOccurs': 1}}, 'language': {'type': {'attributes': [{'name': 'xml:lang', 'ref': 'xml:lang', 'use': 'optional'}], 'maxOccurs': 1, 'minOccurs': 1}}, 'publisher': {'type': {'attributes': [{'name': 'xml:lang', 'ref': 'xml:lang', 'use': 'optional'}], 'maxOccurs': 1, 'minOccurs': 1}}, 'relation': {'type': {'attributes': [{'name': 'xml:lang', 'ref': 'xml:lang', 'use': 'optional'}], 'maxOccurs': 1, 'minOccurs': 1}}, 'rights': {'type': {'attributes': [{'name': 'xml:lang', 'ref': 'xml:lang', 'use': 'optional'}], 'maxOccurs': 1, 'minOccurs': 1}}, 'source': {'type': {'attributes': [{'name': 'xml:lang', 'ref': 'xml:lang', 'use': 'optional'}], 'maxOccurs': 1, 'minOccurs': 1}}, 'subject': {'type': {'attributes': [{'name': 'xml:lang', 'ref': 'xml:lang', 'use': 'optional'}], 'maxOccurs': 1, 'minOccurs': 1}}, 'title': {'type': {'attributes': [{'name': 'xml:lang', 'ref': 'xml:lang', 'use': 'optional'}], 'maxOccurs': 1, 'minOccurs': 1}}, 'type': {'type': {'attributes': [{'name': 'xml:lang', 'ref': 'xml:lang', 'use': 'optional'}], 'maxOccurs': 1, 'minOccurs': 1}}}} 
        url = url_for("itemtypesmapping.schema_list")
        # not exist SchemaName
        res = client.get(url)
        assert res.status_code == 200
        assert json.loads(res.data) == test
        
        # exist Schema
        url = url_for("itemtypesmapping.schema_list",SchemaName="oai_dc_mapping")
        res = client.get(url)
        assert res.status_code == 200
        assert json.loads(res.data) == test
        # not exist Schema
        url = url_for("itemtypesmapping.schema_list",SchemaName="not_exist_oai")
        res = client.get(url)
        assert res.status_code == 200
        assert json.loads(res.data) == {}


class TestItemTypeRocrateMappingView:
    # .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_admin.py::TestItemTypeRocrateMappingView::test_index_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
    @pytest.mark.parametrize('index, is_admin', [
        (0, True),
        (1, True),
        (2, False),
        (3, False),
        (4, False),
        (5, False),
        (7, False)
    ])
    def test_index_acl(self, client, admin_view, users, index, is_admin):
        login_user_via_session(client, email=users[index]['email'])
        url = url_for('itemtypesrocratemapping.index')
        res = client.get(url)
        assert_statuscode_with_role(res, is_admin)

    # .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_admin.py::TestItemTypeRocrateMappingView::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
    def test_index(self, client, admin_view, item_type, users, mocker):
        login_user_via_session(client=client, email=users[0]['email'])

        # item_type_id is none : redirect first item type
        url = url_for('itemtypesrocratemapping.index')
        res = client.get(url)
        assert res.status_code == 302
        assert res.headers['Location'] == 'http://test_server/admin/itemtypes/rocrate_mapping/1'

        # item_type_id is not exist : redirect first item type
        url100 = url_for('itemtypesrocratemapping.index', item_type_id=100)
        res = client.get(url100)
        assert res.status_code == 302
        assert res.headers['Location'] == 'http://test_server/admin/itemtypes/rocrate_mapping/1'

        # item_type_id is normal : 200
        url1 = url_for('itemtypesrocratemapping.index', item_type_id=1)
        res = client.get(url1)
        assert res.status_code == 200

        # Item type table has no record : render error screen
        with patch('weko_records.api.ItemTypes.get_latest', return_value=[]):
            mock_render = mocker.patch('weko_itemtypes_ui.admin.ItemTypeRocrateMappingView.render', return_value=make_response())
            url1 = url_for('itemtypesrocratemapping.index', item_type_id=1)
            res = client.get(url1)
            assert res.status_code == 200
            assert mock_render.call_args[0][0] == current_app.config['WEKO_ITEMTYPES_UI_ADMIN_ERROR_TEMPLATE']

        # Unexpected error : 500
        with patch('weko_records.api.ItemTypes.get_latest', side_effect=Exception('Unexpected error')):
            url1 = url_for('itemtypesrocratemapping.index', item_type_id=1)
            res = client.get(url1)
            assert res.status_code == 500

    # .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_admin.py::TestItemTypeRocrateMappingView::test_register_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
    @pytest.mark.parametrize('index, is_admin', [
        (0, True),
        (1, True),
        (2, False),
        (3, False),
        (4, False),
        (5, False),
        (7, False)
    ])
    def test_register_acl(self, client, admin_view, users, index, is_admin):
        login_user_via_session(client, email=users[index]['email'])
        url = url_for('itemtypesrocratemapping.register')
        data = {}
        res = client.post(url, json=data)
        assert_statuscode_with_role(res, is_admin)

    # .tox/c1/bin/pytest --cov=weko_itemtypes_ui tests/test_admin.py::TestItemTypeRocrateMappingView::test_register -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-itemtypes-ui/.tox/c1/tmp
    def test_register(self, client, admin_view, users, rocrate_mapping):
        login_user_via_session(client, email=users[0]['email'])
        url = url_for('itemtypesrocratemapping.register')

        # Create mapping
        data = {'item_type_id': 1, 'mapping': {'key1': 'new_value1'}}
        res = client.post(url, json=data)
        assert res.status_code == 200
        record = RocrateMapping.query.filter_by(item_type_id=1).one_or_none()
        assert record.mapping.get('key1') == 'new_value1'

        # Update mapping
        data = {'item_type_id': 2, 'mapping': {'key2': 'new_value2'}}
        res = client.post(url, json=data)
        assert res.status_code == 200
        record = RocrateMapping.query.filter_by(item_type_id=2).one_or_none()
        assert record.mapping.get('key2') == 'new_value2'

        # Content type is not json : 400
        data = 'text'
        headers = {'Content-Type': 'text/plain'}
        res = client.post(url, data=data, headers=headers)
        assert res.status_code == 400

        # Failed to register db : 500
        data = {}
        res = client.post(url, json=data)
        assert res.status_code == 500
