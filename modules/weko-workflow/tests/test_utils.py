import pytest
from mock import patch
from werkzeug.datastructures import MultiDict

from weko_workflow.config import WEKO_WORKFLOW_FILTER_PARAMS
from weko_workflow.utils import filter_all_condition, filter_condition, get_url_root,get_record_by_root_ver

# def get_current_language():
# def get_term_and_condition_content(item_type_name):
# def get_identifier_setting(community_id):
# def saving_doi_pidstore(item_id,
# def register_hdl(activity_id):
# def register_hdl_by_item_id(deposit_id, item_uuid, url_root):
# def register_hdl_by_handle(hdl, item_uuid, item_uri):
# def item_metadata_validation(item_id, identifier_type, record=None,
# def merge_doi_error_list(current, new):
# def validation_item_property(mapping_data, properties):
# def handle_check_required_data(mapping_data, mapping_key):
# def handle_check_required_pattern_and_either(mapping_data, mapping_keys,
# def validattion_item_property_required(
# def validattion_item_property_either_required(
# def check_required_data(data, key, repeatable=False):
# def get_activity_id_of_record_without_version(pid_object=None):
# def check_suffix_identifier(idt_regis_value, idt_list, idt_type_list):
#     def __init__(self, item_id=None, record=None):
#     def get_data_item_type(self):
#     def get_data_by_mapping(self, mapping_key, ignore_empty=False,
#     def get_first_data_by_mapping(self, mapping_key):
#     def get_first_property_by_mapping(self, mapping_key, ignore_empty=False):
# def get_sub_item_value(atr_vm, key):
# def get_item_value_in_deep(data, keys):
#     def __init__(self, item_id):
#     def get_pidstore(self, pid_type='doi', object_uuid=None):
#     def check_pidstore_exist(self, pid_type, chk_value=None):
#     def register_pidstore(self, pid_type, reg_value):
#     def delete_pidstore_doi(self, pid_value=None):
#     def remove_idt_registration_metadata(self):
#     def update_idt_registration_metadata(self, input_value, input_type):
#     def get_idt_registration_data(self):
#     def commit(self, key_id, key_val, key_typ, atr_nam, atr_val, atr_typ):
# def delete_bucket(bucket_id):
# def merge_buckets_by_records(main_record_id,
# def delete_unregister_buckets(record_uuid):
# def set_bucket_default_size(record_uuid):
# def is_show_autofill_metadata(item_type_name):
# def is_hidden_pubdate(item_type_name):
# def get_parent_pid_with_type(pid_type, object_uuid):
# def filter_all_condition(all_args):


def test_filter_all_condition(app, mocker):
    dic = MultiDict()
    for key in WEKO_WORKFLOW_FILTER_PARAMS:
        dic.add("{}_0".format(key), "{}_0".format(key))
    for key in WEKO_WORKFLOW_FILTER_PARAMS:
        dic.add("{}_1".format(key), "{}_1".format(key))
    dic.add("dummy_0", "dummy2")
    print(dic)
    with app.test_request_context():
        # mocker.patch("flask.request.args.get", side_effect=dic)
        assert filter_all_condition(dic) == {
            "createdfrom": ["createdfrom_0", "createdfrom_1"],
            "createdto": ["createdto_0", "createdto_1"],
            "workflow": ["workflow_0", "workflow_1"],
            "user": ["user_0", "user_1"],
            "item": ["item_0", "item_1"],
            "status": ["status_0", "status_1"],
            "tab": ["tab_0", "tab_1"],
            "sizewait": ["sizewait_0", "sizewait_1"],
            "sizetodo": ["sizetodo_0", "sizetodo_1"],
            "sizeall": ["sizeall_0", "sizeall_1"],
            "pagesall": ["pagesall_0", "pagesall_1"],
            "pagestodo": ["pagestodo_0", "pagestodo_1"],
            "pageswait": ["pageswait_0", "pageswait_1"],
        }

        # mocker.patch("flask.request.args.get", side_effect=MultiDict())
        assert filter_all_condition(MultiDict()) == {}


# def filter_condition(json, name, condition):


def test_filter_condition():
    json = {}
    filter_condition(json, "name", "condition")
    assert json == {"name": ["condition"]}

    json = {"name": ["condition"]}
    filter_condition(json, "name", "condition")
    assert json == {"name": ["condition", "condition"]}


# def get_actionid(endpoint):
# def convert_record_to_item_metadata(record_metadata):
# def prepare_edit_workflow(post_activity, recid, deposit):
# def handle_finish_workflow(deposit, current_pid, recid):
# def delete_cache_data(key: str):
# def update_cache_data(key: str, value: str, timeout=None):
# def get_cache_data(key: str):
# def check_an_item_is_locked(item_id=None):
#     def check(workers):
# def get_account_info(user_id):
# def check_existed_doi(doi_link):

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_url_root --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_url_root(app):
    app.config["THEME_SITEURL"] = "https://weko3.ir.rcos.nii.ac.jp"
    app.config["SERVER_NAME"] = "TEST_SERVER"
    with app.app_context():
        assert get_url_root() == "https://weko3.ir.rcos.nii.ac.jp/"
        app.config["THEME_SITEURL"] = "https://weko3.ir.rcos.nii.ac.jp/"
        assert get_url_root() == "https://weko3.ir.rcos.nii.ac.jp/"

    app.config["THEME_SITEURL"] = "https://weko3.ir.rcos.nii.ac.jp"
    app.config["SERVER_NAME"] = "TEST_SERVER"
    with app.test_request_context():
        assert get_url_root() == "http://TEST_SERVER/"


# def get_record_by_root_ver(pid_value):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_utils.py::test_get_record_by_root_ver -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_record_by_root_ver(app,db_records):
    app.config.update(DEPOSIT_DEFAULT_STORAGE_CLASS = 'S',
   )
    record, files = get_record_by_root_ver("1")

    assert files == []
    assert record == ({'_oai': {'id': 'oai:weko3.example.org:00000001', 'sets': ['1']}, 'path': ['1'], 'owner': '1', 'recid': '1', 'title': ['title'], 'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2022-08-20'}, '_buckets': {'deposit': '3e99cfca-098b-42ed-b8a0-20ddd09b3e02'}, '_deposit': {'id': '1', 'pid': {'type': 'depid', 'value': '1', 'revision_id': 0}, 'owner': '1', 'owners': [1], 'status': 'published', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}}, 'item_title': 'title', 'author_link': [], 'item_type_id': '1', 'publish_date': '2022-08-20', 'publish_status': '0', 'weko_shared_id': -1, 'item_1617186331708': {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'title', 'subitem_1551255648112': 'ja'}]}, 'item_1617258105262': {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}]}, 'relation_version_is_last': True}, [])

#({'_buckets': {'deposit': '3e99cfca-098b-42ed-b8a0-20ddd09b3e02'},'_deposit': {'created_by': 1,'id': '1','owner': '1','owners': [1],'owners_ext': {'displayname': '','email': 'wekosoftware@nii.ac.jp','username': ''},'pid': {'revision_id': 0, 'type': 'depid', 'value': '1'},'status': 'published'},'_oai': {'id': 'oai:weko3.example.org:00000001', 'sets': ['1']},'author_link': [],'item_1617186331708': {'attribute_name': 'Title','attribute_value_mlt': [{'subitem_1551255647225': 'title','subitem_1551255648112': 'ja'}]},'item_1617258105262': {'attribute_name': 'Resource Type','attribute_value_mlt': [{'resourcetype': 'conference paper','resourceuri': 'http://purl.org/coar/resource_type/c_5794'}]},'item_title': 'title','item_type_id': '1','owner': '1','path': ['1'],'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2022-08-20'},'publish_date': '2022-08-20','publish_status': '0','recid': '1','relation_version_is_last': True,'title': ['title'],'weko_shared_id': -1},[])


# def get_disptype_and_ver_in_metainfo(metadata):
# def set_files_display_type(record_metadata, files):
# def get_thumbnails(files, allow_multi_thumbnail=True):
# def get_allow_multi_thumbnail(item_type_id, activity_id=None):
# def is_usage_application_item_type(activity_detail):
# def is_usage_application(activity_detail):
# def send_mail_reminder(mail_info):
# def send_mail_approval_done(mail_info):
# def send_mail_registration_done(mail_info):
# def send_mail_request_approval(mail_info):
# def send_mail(subject, recipient, body):
# def email_pattern_registration_done(user_role, item_type_name):
# def email_pattern_request_approval(item_type_name, next_action):
# def email_pattern_approval_done(item_type_name):
# def get_mail_data(file_name):
# def get_subject_and_content(file_path):
# def get_file_path(file_name):
# def replace_characters(data, content):
# def get_register_info(activity_id):
# def get_approval_dates(mail_info):
# def get_item_info(item_id):
# def get_site_info_name():
# def get_default_mail_sender():
# def set_mail_info(item_info, activity_detail, guest_user=False):
# def process_send_reminder_mail(activity_detail, mail_template):
# def process_send_notification_mail(
# def get_application_and_approved_date(activities, columns):
# def get_workflow_item_type_names(activities: list):
# def create_usage_report(activity_id):
# def create_record_metadata(
# def modify_item_metadata(
# def replace_title_subitem(subitem_title, subitem_item_title_language):
# def get_shema_dict(properties, data_dict):
# def create_deposit(item_id):
# def update_activity_action(activity_id, owner_id):
# def check_continue(response, activity_id):
# def auto_fill_title(item_type_name):
#     def _get_title(title_key):
# def exclude_admin_workflow(workflow_list):
# def is_enable_item_name_link(action_endpoint, item_type_name):
# def save_activity_data(data: dict) -> NoReturn:
# def send_mail_url_guest_user(mail_info: dict) -> bool:
# def generate_guest_activity_token_value(
# def init_activity_for_guest_user(
#     def _get_guest_activity():
# def send_usage_application_mail_for_guest_user(guest_mail: str, temp_url: str):
# def validate_guest_activity_token(
# def validate_guest_activity_expired(activity_id: str) -> str:
# def create_onetime_download_url_to_guest(activity_id: str,
# def delete_guest_activity(activity_id: str) -> bool:
# def get_activity_display_info(activity_id: str):
# def __init_activity_detail_data_for_guest(activity_id: str, community_id: str):
# def prepare_data_for_guest_activity(activity_id: str) -> dict:
# def recursive_get_specified_properties(properties):
# def get_approval_keys():
# def process_send_mail(mail_info, mail_pattern_name):
# def cancel_expired_usage_reports():
# def process_send_approval_mails(activity_detail, actions_mail_setting,
# def get_usage_data(item_type_id, activity_detail, user_profile=None):
#     def __build_metadata_for_usage_report(record_data: Union[dict, list],
# def update_approval_date(activity):
# def create_record_metadata_for_user(usage_application_activity, usage_report):
# def get_current_date():
# def get_sub_key_by_system_property_key(system_property_key, item_type_id):
# def update_system_data_for_item_metadata(item_id, sub_system_data_key,
# def update_approval_date_for_deposit(deposit, sub_approval_date_key,
# def update_system_data_for_activity(activity, sub_system_data_key,
# def check_authority_by_admin(activity):
# def get_record_first_version(deposit):
# def get_files_and_thumbnail(activity_id, item):
# def get_pid_and_record(item_id):
# def get_items_metadata_by_activity_detail(activity_detail):
# def get_main_record_detail(activity_id,
#     def check_record(record):
# def prepare_doi_link_workflow(item_id, doi_input):
# def get_pid_value_by_activity_detail(activity_detail):
# def check_doi_validation_not_pass(item_id, activity_id,
