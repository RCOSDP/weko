from unittest.mock import MagicMock
import pytest
from mock import patch
from werkzeug.datastructures import MultiDict

from weko_workflow.config import WEKO_WORKFLOW_FILTER_PARAMS
from weko_workflow.utils import (
    filter_all_condition,
    filter_condition,
    get_record_by_root_ver,
    get_url_root,
    register_hdl,
    IdentifierHandle,
    get_current_language,
    get_term_and_condition_content,
    get_identifier_setting,
    saving_doi_pidstore,
)
from weko_workflow.api import GetCommunity, UpdateItem, WorkActivity, WorkActivityHistory, WorkFlow
from weko_workflow.models import Activity

#  # def get_current_language():
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  def test_get_current_language(app):
#      assert get_current_language()==""
#  
#  # def get_term_and_condition_content(item_type_name):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_term_and_condition_content -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  def test_get_term_and_condition_content():
#      assert get_term_and_condition_content()==""
#  
#  # def get_identifier_setting(community_id):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  def test_get_identifier_setting():
#      assert get_identifier_setting()==""
#  
#  # def saving_doi_pidstore(item_id,
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  def test_saving_doi_pidstore():
#      assert saving_doi_pidstore()==""
#  
#  # def register_hdl(activity_id):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_register_hdl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  def test_register_hdl(app,db_records,db_itemtype):
#      recid,depid,record,item,parent,doi = db_records[0]
#      assert recid.pid_value=="1"
#      activity_id='A-00000800-00000'
#      act = Activity(
#                  activity_id=activity_id,
#                  item_id=record.id,
#              )
#      with patch("weko_workflow.api.WorkActivity.get_activity_detail",return_value=act):
#          with patch("weko_handle.api.Handle.register_handle",return_value="handle:00.000.12345/0000000001"):
#              with app.test_request_context():
#                  register_hdl(activity_id)
#                  pid = IdentifierHandle(parent.object_uuid).check_pidstore_exist(pid_type='hdl')
#                  assert pid[0].object_uuid == parent.object_uuid
#                  pid = IdentifierHandle(recid.object_uuid).check_pidstore_exist(pid_type='hdl')
#                  assert pid[0].object_uuid == recid.object_uuid
#      
#      recid,depid, record, item,parent,doi = db_records[1]
#      assert recid.pid_value=="1.0"
#      activity_id='A-00000800-00000'
#      act = Activity(
#                  activity_id=activity_id,
#                  item_id=record.id,
#              )
#      with patch("weko_workflow.api.WorkActivity.get_activity_detail",return_value=act):
#          with patch("weko_handle.api.Handle.register_handle",return_value="handle:00.000.12345/0000000001"):
#              with app.test_request_context():
#                  register_hdl(activity_id)
#                  pid = IdentifierHandle(parent.object_uuid).check_pidstore_exist(pid_type='hdl')
#                  assert pid[0].object_uuid == parent.object_uuid
#                  pid = IdentifierHandle(recid.object_uuid).check_pidstore_exist(pid_type='hdl')
#                  assert pid == []
#      
#      recid,depid, record, item,parent,doi = db_records[2]
#      assert recid.pid_value=="1.1"
#      activity_id='A-00000800-00000'
#      act = Activity(
#                  activity_id=activity_id,
#                  item_id=record.id,
#              )
#      with patch("weko_workflow.api.WorkActivity.get_activity_detail",return_value=act):
#          with patch("weko_handle.api.Handle.register_handle",return_value="handle:00.000.12345/0000000001"):
#              with app.test_request_context():
#                  register_hdl(activity_id)
#                  # register_hdl uses parent object_uuid.
#                  pid = IdentifierHandle(parent.object_uuid).check_pidstore_exist(pid_type='hdl')
#                  assert pid[0].object_uuid == parent.object_uuid
#                  # register_hdl does not use recid object_uuid.
#                  pid = IdentifierHandle(recid.object_uuid).check_pidstore_exist(pid_type='hdl')
#                  assert pid==[]
#      
#  
#                  
#  
#  
#  # def register_hdl_by_item_id(deposit_id, item_uuid, url_root):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def register_hdl_by_handle(hdl, item_uuid, item_uri):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def item_metadata_validation(item_id, identifier_type, record=None,
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def merge_doi_error_list(current, new):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def validation_item_property(mapping_data, properties):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def handle_check_required_data(mapping_data, mapping_key):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def handle_check_required_pattern_and_either(mapping_data, mapping_keys,
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def validattion_item_property_required(
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def validattion_item_property_either_required(
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def check_required_data(data, key, repeatable=False):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_activity_id_of_record_without_version(pid_object=None):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def check_suffix_identifier(idt_regis_value, idt_list, idt_type_list):
#  #     def __init__(self, item_id=None, record=None):
#  #     def get_data_item_type(self):
#  #     def get_data_by_mapping(self, mapping_key, ignore_empty=False,
#  #     def get_first_data_by_mapping(self, mapping_key):
#  #     def get_first_property_by_mapping(self, mapping_key, ignore_empty=False):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_sub_item_value(atr_vm, key):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_item_value_in_deep(data, keys):
#  #     def __init__(self, item_id):
#  #     def get_pidstore(self, pid_type='doi', object_uuid=None):
#  #     def check_pidstore_exist(self, pid_type, chk_value=None):
#  #     def register_pidstore(self, pid_type, reg_value):
#  #     def delete_pidstore_doi(self, pid_value=None):
#  #     def remove_idt_registration_metadata(self):
#  #     def update_idt_registration_metadata(self, input_value, input_type):
#  #     def get_idt_registration_data(self):
#  #     def commit(self, key_id, key_val, key_typ, atr_nam, atr_val, atr_typ):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def delete_bucket(bucket_id):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def merge_buckets_by_records(main_record_id,
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def delete_unregister_buckets(record_uuid):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def set_bucket_default_size(record_uuid):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def is_show_autofill_metadata(item_type_name):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def is_hidden_pubdate(item_type_name):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_parent_pid_with_type(pid_type, object_uuid):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def filter_all_condition(all_args):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  def test_filter_all_condition(app, mocker):
#      dic = MultiDict()
#      for key in WEKO_WORKFLOW_FILTER_PARAMS:
#          dic.add("{}_0".format(key), "{}_0".format(key))
#      for key in WEKO_WORKFLOW_FILTER_PARAMS:
#          dic.add("{}_1".format(key), "{}_1".format(key))
#      dic.add("dummy_0", "dummy2")
#      print(dic)
#      with app.test_request_context():
#          # mocker.patch("flask.request.args.get", side_effect=dic)
#          assert filter_all_condition(dic) == {
#              "createdfrom": ["createdfrom_0", "createdfrom_1"],
#              "createdto": ["createdto_0", "createdto_1"],
#              "workflow": ["workflow_0", "workflow_1"],
#              "user": ["user_0", "user_1"],
#              "item": ["item_0", "item_1"],
#              "status": ["status_0", "status_1"],
#              "tab": ["tab_0", "tab_1"],
#              "sizewait": ["sizewait_0", "sizewait_1"],
#              "sizetodo": ["sizetodo_0", "sizetodo_1"],
#              "sizeall": ["sizeall_0", "sizeall_1"],
#              "pagesall": ["pagesall_0", "pagesall_1"],
#              "pagestodo": ["pagestodo_0", "pagestodo_1"],
#              "pageswait": ["pageswait_0", "pageswait_1"],
#          }
#  
#          # mocker.patch("flask.request.args.get", side_effect=MultiDict())
#          assert filter_all_condition(MultiDict()) == {}
#  
#  
#  # def filter_condition(json, name, condition):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  def test_filter_condition():
#      json = {}
#      filter_condition(json, "name", "condition")
#      assert json == {"name": ["condition"]}
#  
#      json = {"name": ["condition"]}
#      filter_condition(json, "name", "condition")
#      assert json == {"name": ["condition", "condition"]}
#  
#  
#  # def get_actionid(endpoint):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def convert_record_to_item_metadata(record_metadata):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def prepare_edit_workflow(post_activity, recid, deposit):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def handle_finish_workflow(deposit, current_pid, recid):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def delete_cache_data(key: str):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def update_cache_data(key: str, value: str, timeout=None):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_cache_data(key: str):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def check_an_item_is_locked(item_id=None):
#  #     def check(workers):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_account_info(user_id):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def check_existed_doi(doi_link):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_url_root --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
#  def test_get_url_root(app):
#      app.config["THEME_SITEURL"] = "https://weko3.ir.rcos.nii.ac.jp"
#      app.config["SERVER_NAME"] = "TEST_SERVER"
#      with app.app_context():
#          assert get_url_root() == "https://weko3.ir.rcos.nii.ac.jp/"
#          app.config["THEME_SITEURL"] = "https://weko3.ir.rcos.nii.ac.jp/"
#          assert get_url_root() == "https://weko3.ir.rcos.nii.ac.jp/"
#  
#      app.config["THEME_SITEURL"] = "https://weko3.ir.rcos.nii.ac.jp"
#      app.config["SERVER_NAME"] = "TEST_SERVER"
#      with app.test_request_context():
#          assert get_url_root() == "http://TEST_SERVER/"
#  
#  
#  # def get_record_by_root_ver(pid_value):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_record_by_root_ver -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
#  def test_get_record_by_root_ver(app, db_records):
#      app.config.update(
#          DEPOSIT_DEFAULT_STORAGE_CLASS="S",
#      )
#      record, files = get_record_by_root_ver("1")
#  
#      assert files == []
#      assert record == {'_oai': {'id': 'oai:weko3.example.org:00000001', 'sets': ['1']}, 'path': ['1'], 'owner': '1', 'recid': '1', 'title': ['title'], 'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2022-08-20'}, '_buckets': {'deposit': '3e99cfca-098b-42ed-b8a0-20ddd09b3e02'}, '_deposit': {'id': '1', 'pid': {'type': 'depid', 'value': '1', 'revision_id': 0}, 'owner': '1', 'owners': [1], 'status': 'published', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}}, 'item_title': 'title', 'author_link': [], 'item_type_id': '1', 'publish_date': '2022-08-20', 'publish_status': '0', 'weko_shared_id': -1, 'item_1617186331708': {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'title', 'subitem_1551255648112': 'ja'}]}, "item_1617186819068": {"attribute_name": "Identifier Registration","attribute_value_mlt": [{"subitem_identifier_reg_text" :"test/0000000001","subitem_identifier_reg_type": "JaLC"}]},'item_1617258105262': {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}]}, 'relation_version_is_last': True}
#  
#  
#  # def get_disptype_and_ver_in_metainfo(metadata):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def set_files_display_type(record_metadata, files):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_thumbnails(files, allow_multi_thumbnail=True):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_allow_multi_thumbnail(item_type_id, activity_id=None):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def is_usage_application_item_type(activity_detail):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def is_usage_application(activity_detail):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def send_mail_reminder(mail_info):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def send_mail_approval_done(mail_info):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def send_mail_registration_done(mail_info):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def send_mail_request_approval(mail_info):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def send_mail(subject, recipient, body):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def email_pattern_registration_done(user_role, item_type_name):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def email_pattern_request_approval(item_type_name, next_action):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def email_pattern_approval_done(item_type_name):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_mail_data(file_name):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_subject_and_content(file_path):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_file_path(file_name):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def replace_characters(data, content):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_register_info(activity_id):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_approval_dates(mail_info):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_item_info(item_id):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_site_info_name():
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_default_mail_sender():
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def set_mail_info(item_info, activity_detail, guest_user=False):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def process_send_reminder_mail(activity_detail, mail_template):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def process_send_notification_mail(
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_application_and_approved_date(activities, columns):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_workflow_item_type_names(activities: list):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def create_usage_report(activity_id):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def create_record_metadata(
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def modify_item_metadata(
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def replace_title_subitem(subitem_title, subitem_item_title_language):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_shema_dict(properties, data_dict):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def create_deposit(item_id):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def update_activity_action(activity_id, owner_id):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def check_continue(response, activity_id):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def auto_fill_title(item_type_name):
#  #     def _get_title(title_key):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def exclude_admin_workflow(workflow_list):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def is_enable_item_name_link(action_endpoint, item_type_name):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def save_activity_data(data: dict) -> NoReturn:
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def send_mail_url_guest_user(mail_info: dict) -> bool:
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def generate_guest_activity_token_value(
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def init_activity_for_guest_user(
#  #     def _get_guest_activity():
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def send_usage_application_mail_for_guest_user(guest_mail: str, temp_url: str):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def validate_guest_activity_token(
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def validate_guest_activity_expired(activity_id: str) -> str:
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def create_onetime_download_url_to_guest(activity_id: str,
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def delete_guest_activity(activity_id: str) -> bool:
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_activity_display_info(activity_id: str):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def __init_activity_detail_data_for_guest(activity_id: str, community_id: str):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def prepare_data_for_guest_activity(activity_id: str) -> dict:
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def recursive_get_specified_properties(properties):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_approval_keys():
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def process_send_mail(mail_info, mail_pattern_name):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def cancel_expired_usage_reports():
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def process_send_approval_mails(activity_detail, actions_mail_setting,
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_usage_data(item_type_id, activity_detail, user_profile=None):
#  #     def __build_metadata_for_usage_report(record_data: Union[dict, list],
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def update_approval_date(activity):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def create_record_metadata_for_user(usage_application_activity, usage_report):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_current_date():
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_sub_key_by_system_property_key(system_property_key, item_type_id):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def update_system_data_for_item_metadata(item_id, sub_system_data_key,
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def update_approval_date_for_deposit(deposit, sub_approval_date_key,
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def update_system_data_for_activity(activity, sub_system_data_key,
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def check_authority_by_admin(activity):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_record_first_version(deposit):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_files_and_thumbnail(activity_id, item):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_pid_and_record(item_id):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_items_metadata_by_activity_detail(activity_detail):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_main_record_detail(activity_id,
#  #     def check_record(record):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def prepare_doi_link_workflow(item_id, doi_input):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def get_pid_value_by_activity_detail(activity_detail):
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  # def check_doi_validation_not_pass(item_id, activity_id,
#  # .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_current_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
#  
#  
#  def test_get_index_id():
#      """Get index ID base on activity id"""
#      # from weko_workflow.api import WorkActivity, WorkFlow
#  
#      # activity = WorkActivity()
#      # activity_detail = activity.get_activity_detail(activity_id)
#  
#      # workflow = WorkFlow()
#      # workflow_detail = workflow.get_workflow_by_id(
#      #     activity_detail.workflow_id)
#  
#      # index_tree_id = workflow_detail.index_tree_id
#  
#      # if index_tree_id:
#      #     from .api import Indexes
#      #     index_result = Indexes.get_index(index_tree_id)
#      #     if not index_result:
#      #         index_tree_id = None
#      # else:
#      #     index_tree_id = None
#      raise BaseException
