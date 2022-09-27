import pytest
from weko_records_ui.utils import validate_download_record,is_private_index,get_file_info_list,replace_license_free,is_show_email_of_creator,hide_by_itemtype,hide_by_email,hide_by_file,hide_item_metadata_email_only,get_workflows,get_billing_file_download_permission,get_list_licence,restore,soft_delete,is_billing_item,get_groups_price,get_record_permalink,get_google_detaset_meta,get_google_scholar_meta,display_oaiset_path,get_terms,get_roles,check_items_settings

from unittest.mock import MagicMock
import copy
import pytest
import io
from flask import Flask, json, jsonify, session, url_for
from flask_security.utils import login_user
from invenio_accounts.testutils import login_user_via_session
from mock import patch
from weko_deposit.api import WekoRecord
from werkzeug.exceptions import NotFound

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp

# def check_items_settings(settings=None):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_check_items_settings -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_check_items_settings(app):
    with app.test_request_context():
        assert check_items_settings()==None


# def get_record_permalink(record):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_record_permalink -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_record_permalink(app,records):
    indexer, results = records
    record = results[0]["record"]
    assert get_record_permalink(record) == 'https://doi.org/10.xyz/0000000001'

# def get_groups_price(record: dict) -> list:
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_groups_price -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_groups_price(app,records):
    indexer, results = records
    record = results[0]["record"]
    assert get_groups_price(record)==[]

# def get_billing_file_download_permission(groups_price: list) -> dict:
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_billing_file_download_permission():
    assert get_billing_file_download_permission()==""

# def get_min_price_billing_file_download(groups_price: list,
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp

# def is_billing_item(item_type_id):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_is_billing_item -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_is_billing_item(app,itemtypes):
    assert is_billing_item(1)==False

# def soft_delete(recid):
#     def get_cache_data(key: str):
#     def check_an_item_is_locked(item_id=None):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_soft_delete -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_soft_delete(app,records):
    indexer, results = records
    record = results[0]["record"]
    assert soft_delete(record.pid.pid_value)==None


# def restore(recid):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_restore -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_restore(app,records):
    indexer, results = records
    record = results[0]["record"]
    assert restore(record.pid.pid_value)==None


# def get_list_licence():
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_list_licence -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_list_licence(app):
    with app.test_request_context():
        assert get_list_licence()==[{'value': 'license_free', 'name': 'write your own license'}, {'value': 'license_12', 'name': 'Creative Commons CC0 1.0 Universal Public Domain Designation'}, {'value': 'license_6', 'name': 'Creative Commons Attribution 3.0 Unported (CC BY 3.0)'}, {'value': 'license_7', 'name': 'Creative Commons Attribution-ShareAlike 3.0 Unported (CC BY-SA 3.0)'}, {'value': 'license_8', 'name': 'Creative Commons Attribution-NoDerivs 3.0 Unported (CC BY-ND 3.0)'}, {'value': 'license_9', 'name': 'Creative Commons Attribution-NonCommercial 3.0 Unported (CC BY-NC 3.0)'}, {'value': 'license_10', 'name': 'Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0)'}, {'value': 'license_11', 'name': 'Creative Commons Attribution-NonCommercial-NoDerivs 3.0 Unported (CC BY-NC-ND 3.0)'}, {'value': 'license_0', 'name': 'Creative Commons Attribution 4.0 International (CC BY 4.0)'}, {'value': 'license_1', 'name': 'Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)'}, {'value': 'license_2', 'name': 'Creative Commons Attribution-NoDerivatives 4.0 International (CC BY-ND 4.0)'}, {'value': 'license_3', 'name': 'Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)'}, {'value': 'license_4', 'name': 'Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)'}, {'value': 'license_5', 'name': 'Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)'}]

# def get_license_pdf(license, item_metadata_json, pdf, file_item_id, footer_w,
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp

# def get_pair_value(name_keys, lang_keys, datas):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp

# def hide_item_metadata(record, settings=None, item_type_mapping=None,
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp

# def hide_item_metadata_email_only(record):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_hide_item_metadata_email_only -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_hide_item_metadata_email_only(app,records,users):
    indexer, results = records
    record = results[0]["record"]
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert hide_item_metadata_email_only(record)==False

# def hide_by_file(item_metadata):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_hide_by_file -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_hide_by_file(app,records):
    indexer, results = records
    record = results[0]["item"]
    assert hide_by_file(copy.deepcopy(record))==record

# def hide_by_email(item_metadata):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_hide_by_email -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_hide_by_email(app,records):
    indexer, results = records
    record = results[0]["item"]
    assert hide_by_email(copy.deepcopy(record))==record

# def hide_by_itemtype(item_metadata, hidden_items):
#     def del_hide_sub_metadata(keys, metadata):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_hide_by_itemtype -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_hide_by_itemtype(app,records):
    indexer, results = records
    record = results[0]["item"]
    assert hide_by_itemtype(copy.deepcopy(record),[])==""

# def is_show_email_of_creator(item_type_id):
#     def get_creator_id(item_type_id):
#     def item_type_show_email(item_type_id):
#     def item_setting_show_email():
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_is_show_email_of_creator -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_is_show_email_of_creator(app,itemtypes):
    assert is_show_email_of_creator(1)==False


# def replace_license_free(record_metadata, is_change_label=True):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_replace_license_free -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_replace_license_free(app,records):
    indexer, results = records
    record = results[0]["record"]
    assert replace_license_free(copy.deepcopy(record))==""

# def get_file_info_list(record):
#     def get_file_size(p_file):
#     def set_message_for_file(p_file):
#     def get_data_by_key_array_json(key, array_json, get_key):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_file_info_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_file_info_list(app,records):
    indexer, results = records
    record = results[0]["record"]
    assert get_file_info_list(record)==""

# def check_and_create_usage_report(record, file_object):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp

# def create_usage_report_for_user(onetime_download_extra_info: dict):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp

# def get_data_usage_application_data(record_metadata, data_result: dict):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp

# def send_usage_report_mail_for_user(guest_mail: str, temp_url: str):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp

# def check_and_send_usage_report(extra_info, user_mail):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp

# def generate_one_time_download_url(
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp

# def parse_one_time_download_token(token: str) -> Tuple[str, Tuple]:
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp

# def validate_onetime_download_token(
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp

# def is_private_index(record):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_is_private_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_is_private_index(app,records):
    indexer, results = records
    record = results[0]["record"]
    assert is_private_index(record)==""

# def validate_download_record(record: dict):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_validate_download_record -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_validate_download_record(app,records):
    indexer, results = records
    record = results[0]["record"]
    assert validate_download_record(record)==""


# def get_onetime_download(file_name: str, record_id: str,
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp

# def create_onetime_download_url(
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp

# def update_onetime_download(**kwargs) -> NoReturn:
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp

# def get_workflows():
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_workflows -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_workflows(app,users):
    with app.test_request_context():
        with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
            assert get_workflows()==""

# def get_roles():
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_roles -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_roles(app,users):
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert get_roles()==""

# def get_terms():
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_terms -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_terms(app):
    with app.test_request_context():
        assert get_terms()== [{'id': 'term_free', 'name': 'Free Input'}]


# def display_oaiset_path(record_metadata):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_display_oaiset_path -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_display_oaiset_path(app,records,itemtypes,oaischema,users):
    indexer, results = records
    record = results[0]["record_data"]
    with patch("flask_login.utils._get_user", return_value=users[1]["obj"]):
        assert display_oaiset_path(record)==""


# def get_google_scholar_meta(record):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_google_scholar_meta -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_google_scholar_meta(app,records,itemtypes,oaischema):
    indexer, results = records
    record = results[0]["record"]
    assert get_google_scholar_meta(record)==""

# def get_google_detaset_meta(record):
# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_utils.py::test_get_google_detaset_meta -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_get_google_detaset_meta(app,records,itemtypes,oaischema):
    indexer, results = records
    record = results[0]["record"]
    assert get_google_detaset_meta(record)==""
