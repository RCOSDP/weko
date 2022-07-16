import pytest
from weko_records_ui.permissions import check_created_id

#def page_permission_factory(record, *args, **kwargs):
#    def can(self):
#def file_permission_factory(record, *args, **kwargs):
#    def can(self):
#def check_file_download_permission(record, fjson, is_display_file_info=False):
#    def site_license_check():
#    def get_email_list_by_ids(user_id_list):
#    def __check_user_permission(user_id_list):
#def check_open_restricted_permission(record, fjson):
#def is_open_restricted(file_data):
#def check_content_clickable(record, fjson):
#def check_permission_period(permission):
#def get_permission(record, fjson):
#def check_original_pdf_download_permission(record):
#def check_user_group_permission(group_id):
#def check_publish_status(record):
#def check_created_id(record):



def test_check_created_id(users,app):


    record =  {'_oai': {'id': 'oai:weko3.example.org:00000001', 'sets': ['1657555088462']}, 'path': ['1657555088462'], 'owner': '1', 'recid': '1', 'title': ['a'], 'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2022-07-12'}, '_buckets': {'deposit': '35004d51-8938-4e77-87d7-0c9e176b8e7b'}, '_deposit': {'id': '1', 'pid': {'type': 'depid', 'value': '1', 'revision_id': 0}, 'owner': '1', 'owners': [1], 'status': 'published', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}}, 'item_title': 'a', 'author_link': [], 'item_type_id': '15', 'publish_date': '2022-07-12', 'publish_status': '0', 'weko_shared_id': -1, 'item_1617186331708': {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'a', 'subitem_1551255648112': 'ja'}]}, 'item_1617258105262': {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}]}, 'relation_version_is_last': True}
    with app.test_request_context():
        assert check_created_id(record) == False

#def check_usage_report_in_permission(permission):
#def check_create_usage_report(record, file_json):
#def __get_file_permission(record_id, file_name):
