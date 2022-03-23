import pytest
import json
import os

from flask import session, url_for,current_app

from weko_records.api import ItemTypes
from weko_search_ui.utils import (
    check_permission,
    get_content_workflow,
    getEncode,
    validation_file_open_date,
    check_import_items,
    unpackage_import_file,
    read_stats_csv,
    handle_check_date,
    get_list_key_of_iso_date,
    handle_validate_item_import,
    get_item_type,
)
from invenio_i18n.ext import InvenioI18N, current_i18n
from invenio_i18n.babel import set_locale
from weko_search_ui.config import (
    WEKO_REPO_USER,
    WEKO_SYS_USER,
)
from unittest.mock import patch, Mock, MagicMock
from weko_search_ui import WekoSearchUI
from flask_babelex import Babel

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")

@pytest.fixture()
def test_records():
    results = []
    #
    results.append(
        {
            "input": os.path.join(FIXTURE_DIR, "records", "successRecord00.json"),
            "output": "",
        }
    )
    results.append(
        {
            "input": os.path.join(FIXTURE_DIR, "records", "successRecord01.json"),
            "output": "",
        }
    )
    results.append(
        {
            "input": os.path.join(FIXTURE_DIR, "records", "successRecord02.json"),
            "output": "",
        }
    )
    # 存在しない日付が設定されている
    results.append(
        {
            "input": os.path.join(FIXTURE_DIR, "records", "noExistentDate00.json"),
            "output": "Please specify Open Access Date with YYYY-MM-DD.",
        }
    )
    # 日付がYYYY-MM-DD でない
    results.append(
        {
            "input": os.path.join(FIXTURE_DIR, "records", "wrongDateFormat00.json"),
            "output": "Please specify Open Access Date with YYYY-MM-DD.",
        }
    )
    results.append(
        {
            "input": os.path.join(FIXTURE_DIR, "records", "wrongDateFormat01.json"),
            "output": "Please specify Open Access Date with YYYY-MM-DD.",
        }
    )
    results.append(
        {
            "input": os.path.join(FIXTURE_DIR, "records", "wrongDateFormat02.json"),
            "output": "Please specify Open Access Date with YYYY-MM-DD.",
        }
    )

    return results

@pytest.fixture()
def test_list_records():
    tmp = []
    results = []
    tmp.append(
        {
            "input": os.path.join(FIXTURE_DIR, "list_records", "list_records.json"),
            "output": os.path.join(
                FIXTURE_DIR, "list_records", "list_records_result.json"
            ),
        }
    )
    tmp.append(
        {
            "input": os.path.join(FIXTURE_DIR, "list_records", "list_records00.json"),
            "output": os.path.join(
                FIXTURE_DIR, "list_records", "list_records00_result.json"
            ),
        }
    )
    tmp.append(
        {
            "input": os.path.join(FIXTURE_DIR, "list_records", "list_records01.json"),
            "output": os.path.join(
                FIXTURE_DIR, "list_records", "list_records01_result.json"
            ),
        }
    )
    tmp.append(
        {
            "input": os.path.join(FIXTURE_DIR, "list_records", "list_records02.json"),
            "output": os.path.join(
                FIXTURE_DIR, "list_records", "list_records02_result.json"
            ),
        }
    )

    tmp.append(
        {
            "input": os.path.join(FIXTURE_DIR, "list_records", "list_records03.json"),
            "output": os.path.join(
                FIXTURE_DIR, "list_records", "list_records03_result.json"
            ),
        }
    )

    for t in tmp:
        with open(t.get("input"), encoding="utf-8") as f:
            input_data = json.load(f)
        with open(t.get("output"), encoding="utf-8") as f:
            output_data = json.load(f)
        results.append({"input": input_data, "output": output_data})
    return results

@pytest.fixture()
def test_importdata():
    files = [os.path.join(FIXTURE_DIR,'import00.zip')
    ]
    return files

@pytest.fixture()
def mocker_itemtype(mocker):
    item_type = Mock()
    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "item_type/15_render.json"
    )
    with open(filepath, encoding="utf-8") as f:
        render = json.load(f)
    item_type.render = render

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "item_type/15_schema.json"
    )
    with open(filepath, encoding="utf-8") as f:
        schema = json.load(f)
    item_type.schema = schema

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "item_type/15_form.json"
    )
    with open(filepath, encoding="utf-8") as f:
        form = json.load(f)
    item_type.form = form

    item_type.item_type_name.name="デフォルトアイテムタイプ（フル）"
    item_type.item_type_name.item_type.first().id=15

    mocker.patch("weko_records.api.ItemTypes.get_by_id", return_value=item_type)


#def get_tree_items(index_tree_id):
#def delete_records(index_tree_id, ignore_items):
#def get_journal_info(index_id=0):
#def get_feedback_mail_list():

# def check_permission():
def test_check_permission(mocker):
    user = MagicMock()
    user.roles = []
    mocker.patch('flask_login.utils._get_user',return_value=user)
    assert check_permission() == False

    user.roles = [WEKO_SYS_USER]
    mocker.patch('flask_login.utils._get_user',return_value=user)
    assert check_permission() == True

    user.roles = [WEKO_REPO_USER]
    mocker.patch('flask_login.utils._get_user',return_value=user)
    assert check_permission() == True

    user.roles = ["ROLE"]
    mocker.patch('flask_login.utils._get_user',return_value=user)
    assert check_permission() == False

    user.roles = ["ROLE",WEKO_SYS_USER]
    mocker.patch('flask_login.utils._get_user',return_value=user)
    assert check_permission() == True

# def get_content_workflow(item):
def test_get_content_workflow():
    item = MagicMock()

    item.flowname = 'flowname'
    item.id = 'id'
    item.flow_id='flow_id'
    item.flow_define.flow_name='flow_name'
    item.itemtype.item_type_name.name='item_type_name'

    result = dict()
    result["flows_name"] = item.flows_name
    result["id"] = item.id
    result["itemtype_id"] = item.itemtype_id
    result["flow_id"] = item.flow_id
    result["flow_name"] = item.flow_define.flow_name
    result["item_type_name"] = item.itemtype.item_type_name.name
    
    assert get_content_workflow(item) == result

# def set_nested_item(data_dict, map_list, val):
# def convert_nested_item_to_list(data_dict, map_list):
# def define_default_dict():
# def defaultify(d: dict) -> dict:
# def handle_generate_key_path(key) -> list:
# def parse_to_json_form(data: list, item_path_not_existed=[], include_empty=False):

#def check_import_items(file, is_change_identifier: bool, is_gakuninrdm=False):
def test_check_import_items(app,test_importdata,mocker_itemtype):
    app.config['WEKO_SEARCH_UI_IMPORT_TMP_PREFIX'] = 'importtest'
    with app.app_context():
        for file in test_importdata:
            assert check_import_items(file,False,False)==''

# def unpackage_import_file(data_path: str, csv_file_name: str, force_new=False):

# def getEncode(filepath):
def test_getEncode():
    csv_files = [
        {"file":"eucjp_lf_items.csv","enc":"euc-jp"},
        {"file":"iso2022jp_lf_items.csv","enc":"iso-2022-jp"},
        {"file":"sjis_lf_items.csv","enc":"shift_jis"},
        {"file":"utf8_cr_items.csv","enc":"utf-8"},
        {"file":"utf8_crlf_items.csv","enc":"utf-8"},
        {"file":"utf8_lf_items.csv","enc":"utf-8"},
        {"file":"utf8bom_lf_items.csv","enc":"utf-8"},
        {"file":"utf16be_bom_lf_items.csv","enc":"utf-16be"},
        {"file":"utf16le_bom_lf_items.csv","enc":"utf-16le"},
        # {"file":"utf32be_bom_lf_items.csv","enc":"utf-32"},
        # {"file":"utf32le_bom_lf_items.csv","enc":"utf-32"},
         {"file":"big5.txt","enc":""},
        
    ]
    
    for f in csv_files:
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "csv",f['file'])
        print(filepath)
        assert getEncode(filepath) == f['enc']


# def read_stats_csv(csv_file_path: str, csv_file_name: str) -> dict:

def test_read_stats_csv(app,mocker_itemtype):
    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "csv","data.json")
    csv_file_name = "utf8_lf_items.csv"
    csv_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "csv",csv_file_name)
    with open(filepath,encoding="utf-8") as f:
        data = json.load(f)

    with app.test_request_context():
        with set_locale('en'):
            assert read_stats_csv(csv_file_path,csv_file_name) == data

# def handle_convert_validate_msg_to_jp(message: str):
# def handle_validate_item_import(list_record, schema) -> list:

def test_handle_validate_item_import():
    handle_validate_item_import()

# def represents_int(s):

# def get_item_type(item_type_id=0) -> dict:
def test_get_item_type(mocker_itemtype):
    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "item_type/15_get_item_type_result.json"
    )
    with open(filepath, encoding="utf-8") as f:
        except_result = json.load(f)
    result = get_item_type(15)
    assert result['is_lastest']==except_result['is_lastest']
    assert result['name']==except_result['name']
    assert result['item_type_id']==except_result['item_type_id']
    assert result['schema']==except_result['schema']
    assert result==except_result

    assert get_item_type(0) == {}


# def handle_check_exist_record(list_record) -> list:
# def make_csv_by_line(lines):
# def make_stats_csv(raw_stats, list_name):
# def create_deposit(item_id):
# def clean_thumbnail_file(deposit, root_path, thumbnail_path):
# def up_load_file(record, root_path, deposit, allow_upload_file_content, old_files):
# def get_file_name(file_path):
# def register_item_metadata(item, root_path, is_gakuninrdm=False):
# def update_publish_status(item_id, status):
# def handle_workflow(item: dict):
# def create_work_flow(item_type_id):
# def create_flow_define():
# def import_items_to_system(item: dict, request_info=None, is_gakuninrdm=False):
# def handle_item_title(list_record):
# def handle_check_and_prepare_publish_status(list_record):
# def handle_check_and_prepare_index_tree(list_record):
# def handle_check_and_prepare_feedback_mail(list_record):
# def handle_set_change_identifier_flag(list_record, is_change_identifier):
# def handle_check_cnri(list_record):
# def handle_check_doi_indexes(list_record):
# def handle_check_doi_ra(list_record):
# def handle_check_doi(list_record):
# def register_item_handle(item):
# def prepare_doi_setting():
# def get_doi_prefix(doi_ra):
# def get_doi_link(doi_ra, data):
# def prepare_doi_link(item_id):
# def register_item_doi(item):
# def register_item_update_publish_status(item, status):
# def handle_doi_required_check(record):

# def handle_check_date(list_record):
def test_handle_check_date(app, test_list_records, mocker_itemtype):
    for t in test_list_records:
        input_data = t.get("input")
        output_data = t.get("output")
        with app.app_context():
            ret = handle_check_date(input_data)
            assert ret == output_data

# def get_data_in_deep_dict(search_key, _dict={}):
# def validation_file_open_date(record):
def test_validation_file_open_date(app, test_records):
    for t in test_records:
        filepath = t.get("input")
        result = t.get("output")
        with open(filepath, encoding="utf-8") as f:
            ret = json.load(f)
        with app.app_context():
            assert validation_file_open_date(ret) == result


# def validation_date_property(date_str):

# def get_list_key_of_iso_date(schemaform):
def test_get_list_key_of_iso_date():
    form = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "item_type", "form00.json"
    )
    result = [
        "item_1617186660861.subitem_1522300722591",
        "item_1617187056579.bibliographicIssueDates.bibliographicIssueDate",
        "item_1617187136212.subitem_1551256096004",
        "item_1617605131499.fileDate.fileDateValue",
    ]
    with open(form, encoding="utf-8") as f:
        df = json.load(f)
    assert get_list_key_of_iso_date(df) == result


# def get_current_language():
# def get_change_identifier_mode_content():
# def get_root_item_option(item_id, item, sub_form={"title_i18n": {}}):
# def get_sub_item_option(key, schemaform):
# def check_sub_item_is_system(key, schemaform):
# def get_lifetime():
# def get_system_data_uri(key_type, key):
# def handle_fill_system_item(list_record):
# def get_thumbnail_key(item_type_id=0):
# def handle_check_thumbnail_file_type(thumbnail_paths):
# def handle_check_metadata_not_existed(str_keys, item_type_id=0):
# def handle_get_all_sub_id_and_name(items, root_id=None, root_name=None, form=[]):
# def handle_get_all_id_in_item_type(item_type_id):
# def handle_check_consistence_with_mapping(mapping_ids, keys):
# def handle_check_duplication_item_id(ids: list):
# def export_all(root_url):
# def delete_exported(uri, cache_key):
# def cancel_export_all():
# def get_export_status():
# def handle_check_item_is_locked(item):
# def handle_remove_es_metadata(item, bef_metadata, bef_last_ver_metadata):
# def check_index_access_permissions(func):
# def handle_check_file_metadata(list_record, data_path):
# def handle_check_file_path(
# def handle_check_file_content(record, data_path):
# def handle_check_thumbnail(record, data_path):
# def get_key_by_property(record, item_map, item_property):
# def get_data_by_property(item_metadata, item_map, mapping_key):
# def get_filenames_from_metadata(metadata):
# def handle_check_filename_consistence(file_paths, meta_filenames):
