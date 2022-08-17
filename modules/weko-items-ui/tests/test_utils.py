# def get_list_username():
# def get_list_email():
# def get_user_info_by_username(username):
# def validate_user(username, email):
# def get_user_info_by_email(email):
# def get_user_information(user_id):
# def get_user_permission(user_id):
# def get_current_user():
# def find_hidden_items(item_id_list, idx_paths=None):
# def parse_ranking_results(index_info,
# def parse_ranking_new_items(result_data):
# def parse_ranking_record(result_data):
# def validate_form_input_data(
# def parse_node_str_to_json_schema(node_str: str):
# def update_json_schema_with_required_items(node: dict, json_data: dict):
#     :param node: json schema return from def parse_node_str_to_json_schema
# def update_json_schema_by_activity_id(json_data, activity_id):
# def update_schema_form_by_activity_id(schema_form, activity_id):
# def recursive_prepare_either_required_list(schema_form, either_required_list):
# def recursive_update_schema_form_with_condition(
#     def prepare_either_condition_required(group_idx, key):
#     def set_on_change(elem):
# def package_export_file(item_type_data):
# def make_stats_csv(item_type_id, recids, list_item_role):
#         def __init__(self, record_ids):
#         def get_max_ins(self, attr):
#         def get_max_ins_feedback_mail(self):
#         def get_max_items(self, item_attrs):
#         def get_subs_item(self,
# def get_list_file_by_record_id(recid):
# def write_bibtex_files(item_types_data, export_path):
# def write_csv_files(item_types_data, export_path, list_item_role):
# def check_item_type_name(name):
# def export_items(post_data):
# def _get_max_export_items():
# def _export_item(record_id,
#     def del_hide_sub_metadata(keys, metadata):
# def _custom_export_metadata(record_metadata: dict, hide_item: bool = True,
# def get_new_items_by_date(start_date: str, end_date: str, ranking=False) -> dict:
# def update_schema_remove_hidden_item(schema, render, items_name):
# def get_files_from_metadata(record):
# def to_files_js(record):
# def update_sub_items_by_user_role(item_type_id, schema_form):
# def remove_excluded_items_in_json_schema(item_id, json_schema):
# def get_excluded_sub_items(item_type_name):
# def get_current_user_role():
# def is_need_to_show_agreement_page(item_type_name):
# def update_index_tree_for_record(pid_value, index_tree_id):
# def validate_user_mail(users, activity_id, request_data, keys, result):
# def check_approval_email(activity_id, user):
# def check_approval_email_in_flow(activity_id, users):
# def update_action_handler(activity_id, action_order, user_id):
# def validate_user_mail_and_index(request_data):
# def recursive_form(schema_form):
# def set_multi_language_name(item, cur_lang):
# def get_data_authors_prefix_settings():
# def get_data_authors_affiliation_settings():
# def hide_meta_data_for_role(record):
# def get_ignore_item_from_mapping(_item_type_id):
# def get_mapping_name_item_type_by_key(key, item_type_mapping):
# def get_mapping_name_item_type_by_sub_key(key, item_type_mapping):
# def get_hide_list_by_schema_form(item_type_id=None, schemaform=None):
# def get_hide_parent_keys(item_type_id=None, meta_list=None):
# def get_hide_parent_and_sub_keys(item_type):
# def get_item_from_option(_item_type_id):
# def get_options_list(item_type_id, json_item=None):
# def get_options_and_order_list(item_type_id, item_type_mapping=None,
# def hide_table_row_for_csv(table_row, hide_key):
# def is_schema_include_key(schema):
# def isExistKeyInDict(_key, _dict):
# def set_validation_message(item, cur_lang):
# def translate_validation_message(item_property, cur_lang):
# def get_workflow_by_item_type_id(item_type_name_id, item_type_id):
# def validate_bibtex(record_ids):
# def make_bibtex_data(record_ids):
# def translate_schema_form(form_element, cur_lang):
# def get_ranking(settings):
# def __sanitize_string(s: str):
# def sanitize_input_data(data):
# def save_title(activity_id, request_data):
# def get_key_title_in_item_type_mapping(item_type_mapping):
# def get_title_in_request(request_data, key, key_child):
# def hide_form_items(item_type, schema_form):
# def hide_thumbnail(schema_form):
#     def is_thumbnail(items):
# def get_ignore_item(_item_type_id, item_type_mapping=None,
# def make_stats_csv_with_permission(item_type_id, recids,
#     def _get_root_item_option(item_id, item, sub_form={'title_i18n': {}}):
#         def __init__(self, record_ids, records_metadata):
#             def hide_metadata_email(record):
#         def get_max_ins(self, attr):
#         def get_max_ins_feedback_mail(self):
#         def get_max_items(self, item_attrs):
#         def get_subs_item(self,
# def check_item_is_being_edit(
# def check_item_is_deleted(recid):
# def permission_ranking(result, pid_value_permissions, display_rank, list_name,
# def has_permission_edit_item(record, recid):