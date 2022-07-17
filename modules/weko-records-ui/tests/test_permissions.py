import pytest
from weko_records_ui.permissions import check_created_id
from invenio_accounts.models import User, Role

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


import mock  # python2, after pip install mock
from unittest import mock  # python3 
from invenio_accounts.testutils import create_test_user
from flask_security import login_user
from flask_login import current_user

def test_check_created_id(users,app):
    datastore = app.extensions["invenio-accounts"].datastore
    login_manager = app.login_manager

    @login_manager.user_loader
    def load_user(user_id):
        user = datastore.find_user(id=user_id)    
        return user

    @app.route("/foo_login/<username>")
    def login(username):
        user = datastore.find_user(email=username)
        login_user(user)
        return "Logged In"

    record =  {'_oai': {'id': 'oai:weko3.example.org:00000001', 'sets': ['1657555088462']}, 'path': ['1657555088462'], 'owner': '1', 'recid': '1', 'title': ['a'], 'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2022-07-12'}, '_buckets': {'deposit': '35004d51-8938-4e77-87d7-0c9e176b8e7b'}, '_deposit': {'id': '1', 'pid': {'type': 'depid', 'value': '1', 'revision_id': 0}, 'owner': '1', 'owners': [1], 'status': 'published', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}}, 'item_title': 'a', 'author_link': [], 'item_type_id': '15', 'publish_date': '2022-07-12', 'publish_status': '0', 'weko_shared_id': -1, 'item_1617186331708': {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'a', 'subitem_1551255648112': 'ja'}]}, 'item_1617258105262': {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}]}, 'relation_version_is_last': True}
    assert record.get('_deposit', {}).get('created_by') == 1
    assert record.get('item_type_id') == 15
    assert record.get('weko_shared_id') == -1
    with app.test_request_context(headers=[('Accept-Language','en')]):
        with app.test_client() as client:
            sysadmin_role = Role.query.filter_by(name='System Administrator').first()
            repoadmin_role = Role.query.filter_by(name='Repository Administrator').first()
            contributor_role = Role.query.filter_by(name='Contributor').first()
            comadmin_role = Role.query.filter_by(name='Community Administrator').first()
            originalrole = Role.query.filter_by(name='Original Role').first()

            assert current_user.is_authenticated == False
            assert check_created_id(record) == False
            client.get("/foo_login/user@test.org", follow_redirects=True)       
            assert current_user.is_authenticated == True
            assert current_user.id == 1
            assert current_user.roles == []
            assert check_created_id(record) == False
            client.get("/foo_login/contributor@test.org", follow_redirects=True)       
            assert current_user.is_authenticated == True
            assert current_user.id == 2
            assert current_user.roles[0] == contributor_role
            assert check_created_id(record) == False
            client.get("/foo_login/comadmin@test.org", follow_redirects=True)       
            assert current_user.is_authenticated == True
            assert current_user.id == 3
            assert current_user.roles[0] == comadmin_role
            assert check_created_id(record) == True
            client.get("/foo_login/repoadmin@test.org", follow_redirects=True)       
            assert current_user.is_authenticated == True
            assert current_user.id == 4
            assert current_user.roles[0] == repoadmin_role
            assert check_created_id(record) == True
            client.get("/foo_login/sysadmin@test.org", follow_redirects=True)       
            assert current_user.is_authenticated == True
            assert current_user.id == 5
            assert current_user.roles[0] == sysadmin_role
            assert check_created_id(record) == True
            client.get("/foo_login/originalroleuser@test.org", follow_redirects=True)       
            assert current_user.is_authenticated == True
            assert current_user.id == 6
            assert current_user.roles[0] == originalrole
            assert check_created_id(record) == False

#def check_usage_report_in_permission(permission):
#def check_create_usage_report(record, file_json):
#def __get_file_permission(record_id, file_name):
