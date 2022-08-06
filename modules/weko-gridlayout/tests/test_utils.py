import pytest

from weko_gridlayout.utils import main_design_has_main_widget

# .tox/c1/bin/pytest --cov=weko_gridlayout tests/test_utils.py::test_filter_condition -v --cov-branch --cov-report=term -s --basetemp=/code/modules/weko-gridlayout/.tox/c1/tmp -vv

# def get_widget_type_list():
# def delete_item_in_preview_widget_item(data_id, json_data):
# def convert_popular_data(source_data, des_data):
# def update_general_item(item, data_result):
# def update_menu_item(item, data_result):
# def update_access_counter_item(item, data_result):
# def update_new_arrivals_item(item, data_result):
# def get_default_language():
# def get_unregister_language():
# def get_register_language():
# def get_system_language():
# def build_data(data):
# def _escape_html_multi_lang_setting(multi_lang_setting: dict):
# def build_data_setting(data):
# def _build_access_counter_setting_data(result, setting):
# def _build_new_arrivals_setting_data(result, setting):
# def _build_notice_setting_data(result, setting):
# def _build_header_setting_data(result, setting):
# def build_multi_lang_data(widget_id, multi_lang_json):
# def convert_widget_data_to_dict(widget_data):
# def convert_widget_multi_lang_to_dict(multi_lang_data):
# def convert_data_to_design_pack(widget_data, list_multi_lang_data):
# def convert_data_to_edit_pack(data):
# def build_rss_xml(data=None, index_id=0, page=1, count=20, term=0, lang=''):
# def find_rss_value(data, keyword):
# def get_rss_data_source(source, keyword):
# def get_elasticsearch_result_by_date(start_date, end_date):
# def validate_main_widget_insertion(repository_id, new_settings, page_id=0):
# def get_widget_design_page_with_main(repository_id):
# def main_design_has_main_widget(repository_id):

def test_main_design_has_main_widget(db_register):
    assert main_design_has_main_widget('Root Index')==True
    assert main_design_has_main_widget('test')==False
    assert main_design_has_main_widget('')==False
    

# def has_main_contents_widget(settings):

#def test_has_main_contents_widget(db_register):



# def get_widget_design_setting(repository_id, current_language, page_id=None):
#     def validate_response():
#     def get_widget_response(_page_id):
# def compress_widget_response(response):
# def delete_widget_cache(repository_id, page_id=None):
#     def __init__(self):
#     def initialize_widget_bucket(self):
#     def __validate(self, file_stream, file_name, community_id="0", file_size=0):
#     def save_file(self, file_stream, file_name: str, mimetype: str,
#     def get_file(self, file_name, community_id=0):
# def validate_upload_file(community_id: str):