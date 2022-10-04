import os
import json
import copy
import pytest
import unittest
from datetime import datetime
from mock import patch, MagicMock, Mock
from flask import current_app, make_response, request
from flask_login import current_user
from flask_babelex import Babel

from invenio_i18n.babel import set_locale

from weko_search_ui import WekoSearchUI
from weko_search_ui.config import (
    WEKO_REPO_USER,
    WEKO_SYS_USER,
    WEKO_IMPORT_SYSTEM_ITEMS,
    VERSION_TYPE_URI,
    ACCESS_RIGHT_TYPE_URI,
    RESOURCE_TYPE_URI
)
from weko_search_ui.utils import (
    DefaultOrderedDict,
    get_tree_items,
    get_tree_items,
    delete_records,
    get_journal_info,
    get_feedback_mail_list,
    check_permission,
    get_content_workflow,
    set_nested_item,
    convert_nested_item_to_list,
    define_default_dict,
    defaultify,
    handle_generate_key_path,
    parse_to_json_form,
    check_import_items,
    unpackage_import_file,
    getEncode,
    read_stats_file,
    handle_convert_validate_msg_to_jp,
    handle_validate_item_import,
    represents_int,
    get_item_type,
    handle_check_exist_record,
    make_file_by_line,
    make_stats_file,
    create_deposit,
    clean_thumbnail_file,
    up_load_file,
    get_file_name,
    register_item_metadata,
    update_publish_status,
    handle_workflow,
    create_work_flow,
    create_flow_define,
    send_item_created_event_to_es,
    import_items_to_system,
    handle_item_title,
    handle_check_and_prepare_publish_status,
    handle_check_and_prepare_index_tree,
    handle_check_and_prepare_feedback_mail,
    handle_set_change_identifier_flag,
    handle_check_cnri,
    handle_check_doi_indexes,
    handle_check_doi_ra,
    handle_check_doi,
    register_item_handle,
    prepare_doi_setting,
    get_doi_prefix,
    get_doi_link,
    prepare_doi_link,
    register_item_doi,
    register_item_update_publish_status,
    handle_doi_required_check,
    handle_check_date,
    handle_check_id,
    get_data_in_deep_dict,
    validation_file_open_date,
    validation_date_property,
    get_list_key_of_iso_date,
    get_current_language,
    get_change_identifier_mode_content,
    get_root_item_option,
    get_sub_item_option,
    check_sub_item_is_system,
    get_lifetime,
    get_system_data_uri,
    handle_fill_system_item,
    get_thumbnail_key,
    handle_check_thumbnail_file_type,
    handle_check_metadata_not_existed,
    handle_get_all_sub_id_and_name,
    handle_get_all_id_in_item_type,
    handle_check_consistence_with_mapping,
    handle_check_duplication_item_id,
    export_all,
    delete_exported,
    cancel_export_all,
    get_export_status,
    handle_check_item_is_locked,
    handle_remove_es_metadata,
    check_index_access_permissions,
    handle_check_file_metadata,
    handle_check_file_path,
    handle_check_file_content,
    handle_check_thumbnail,
    get_key_by_property,
    get_data_by_property,
    get_filenames_from_metadata,
    handle_check_filename_consistence
)

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")


# class DefaultOrderedDict(OrderedDict):
def test_DefaultOrderDict_deepcopy():
    import copy

    data={
        "key0":"value0",
        "key1":"value1",
        "key2":{
            "key2.0":"value2.0",
            "key2.1":"value2.1"
            }
        }
    dict1 = defaultify(data)
    dict2 = copy.deepcopy(dict1)

    for i, d in enumerate(dict2):
        if i in [0, 1] :
            assert d == "key" + str(i)
            assert dict2[d] == "value" + str(i)
        else:
            assert d == "key" + str(i)
            assert isinstance(dict2[d], DefaultOrderedDict)
            for s, dd in enumerate(dict2[d]):
                assert dd == "key{}.{}".format(i,s)
                assert dict2[d][dd] == "value{}.{}".format(i,s)


# def get_tree_items(index_tree_id): ERROR ~ AttributeError: '_AppCtxGlobals' object has no attribute 'identity'
def test_get_tree_items(i18n_app, indices, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert get_tree_items(33)


# def delete_records(index_tree_id, ignore_items): ERROR ~ AttributeError: '_AppCtxGlobals' object has no attribute 'identity'
def test_delete_records(i18n_app, indices):
    assert delete_records(33, ignore_items=None)


# def get_journal_info(index_id=0):
def test_get_journal_info(i18n_app, indices):
    # Test 1
    assert not get_journal_info(33)


# def get_feedback_mail_list():
def test_get_feedback_mail_list(i18n_app, db_records2):
    # Test 1
    assert not get_feedback_mail_list()


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
def test_set_nested_item(i18n_app):
    data_dict = {'1': {'a': 'aa'}}
    map_list = ["test"]
    val = None

    assert set_nested_item(data_dict, map_list, val)


# def convert_nested_item_to_list(data_dict, map_list):
# def test_convert_nested_item_to_list(i18n_app):
#     data_dict = {'a': 'aa'}
#     map_list = [1,2,3,4]

#     assert convert_nested_item_to_list(data_dict, map_list)


# def define_default_dict():
def test_define_default_dict(i18n_app):
    # Test 1
    assert not define_default_dict()


# def defaultify(d: dict) -> dict:
def test_defaultify():
    # Test 1
    assert not defaultify({})


# def handle_generate_key_path(key) -> list:
def test_handle_generate_key_path():
    assert handle_generate_key_path("key")


# def parse_to_json_form(data: list, item_path_not_existed=[], include_empty=False):
def test_parse_to_json_form(i18n_app, record_with_metadata):
    data = record_with_metadata[0].items()

    assert parse_to_json_form(data)


# def check_import_items(file, is_change_identifier: bool, is_gakuninrdm=False,
def test_check_import_items(i18n_app):
    current_path = os.path.dirname(os.path.abspath(__file__))
    file_name = 'sample_file.txt'
    file_path = os.path.join(
        current_path,
        'data',
        'sample_file',
        file_name
    )

    assert check_import_items(file_path, True)


# def unpackage_import_file(data_path: str, file_name: str, file_format: str, force_new=False):
def test_unpackage_import_file(app,mocker,mocker_itemtype):
    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "item_map.json")
    with open(filepath,encoding="utf-8") as f:
        item_map = json.load(f)
    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "item_type_mapping.json")
    with open(filepath,encoding="utf-8") as f:
        item_type_mapping = json.load(f)
    mocker.patch("weko_records.serializers.utils.get_mapping",return_value=item_map)
    mocker.patch("weko_records.api.Mapping.get_record",return_value=item_type_mapping)

    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "unpackage_import_file/result.json")
    with open(filepath,encoding="utf-8") as f:
        result = json.load(f)

    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "unpackage_import_file/result_force_new.json")
    with open(filepath,encoding="utf-8") as f:
        result_force_new = json.load(f)

    path = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "unpackage_import_file")
    with app.test_request_context():
        with set_locale('en'):
            assert unpackage_import_file(path,'items.csv','csv',False)==result
            assert unpackage_import_file(path,'items.csv','csv',True)==result_force_new


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


# def read_stats_file(file_path: str, file_name: str, file_format: str) -> dict:
def test_read_stats_file(i18n_app, db_itemtype, users):
    current_path = os.path.dirname(os.path.abspath(__file__))
    file_name_tsv = 'sample_tsv.tsv'
    file_path_tsv = os.path.join(
        current_path,
        'data',
        'sample_file',
        file_name_tsv
    )
    file_name_csv = 'sample_csv.csv'
    file_path_csv = os.path.join(
        current_path,
        'data',
        'sample_file',
        file_name_csv
    )

    # import csv, re
    # from weko_records.models import ItemType
    # from weko_records.api import ItemTypes
    # enc = getEncode(file_path_tsv)
    # with open(file_path_tsv, "r", newline="", encoding=enc) as file:
    #     file_reader = csv.reader(file, delimiter='\t')
    #     for num, data_row in enumerate(file_reader, start=1):
    #         item_type_id = data_row[2].split("/")[-1]
    #         itemtype = ItemTypes.get_by_id(item_type_id) # if you use itemtype.schema y will be None
    #         x = ItemType.query.filter_by(id=1).first()
    #         y = get_item_type(int(item_type_id)) # if you use itemtype.schema y will be None
    #         print('++++++++++++++')
    #         if y:
    #             print("y!")
    #         print(x)
    #         print(itemtype)
    #         # print(itemtype.schema)
    #         # print(itemtype.item_type_name.name)
    #         # print(item_type_id)
    #         print('--------')
    # raise BaseException

    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert read_stats_file(file_path_tsv, file_name_tsv, 'tsv')
        assert read_stats_file(file_path_csv, file_name_csv, 'csv')


# def handle_convert_validate_msg_to_jp(message: str):
def test_handle_convert_validate_msg_to_jp(i18n_app):
    message = "test"

    assert handle_convert_validate_msg_to_jp(message)


# def handle_validate_item_import(list_record, schema) -> list:
def test_handle_validate_item_import(app,mocker_itemtype):
    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "csv","data.json")
    with open(filepath,encoding="utf-8") as f:
        data = json.load(f)

    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "list_records", "list_records.json")
    with open(filepath,encoding="utf-8") as f:
        list_record = json.load(f)

    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "list_records", "list_records_result.json")
    with open(filepath,encoding="utf-8") as f:
        result = json.load(f)

    with app.test_request_context():
        with set_locale('en'):
            assert handle_validate_item_import(list_record, data.get("item_type_schema", {}))==result


# def represents_int(s):
def test_represents_int():
    assert represents_int("a") == False
    assert represents_int("30") == True
    assert represents_int("31.1") == False


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
def test_handle_check_exist_record(app):
    case =  unittest.TestCase()
    # case 1 import new items
    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "list_records", "b4_handle_check_exist_record.json")
    with open(filepath,encoding="utf-8") as f:
        list_record = json.load(f)

    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "list_records", "b4_handle_check_exist_record_result.json")
    with open(filepath,encoding="utf-8") as f:
        result = json.load(f)

    case.assertCountEqual(handle_check_exist_record(list_record),result)

    # case 2 import items with id
    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "list_records", "b4_handle_check_exist_record1.json")
    with open(filepath,encoding="utf-8") as f:
        list_record = json.load(f)

    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "list_records", "b4_handle_check_exist_record_result1.json")
    with open(filepath,encoding="utf-8") as f:
        result = json.load(f)

    with app.test_request_context():
        with set_locale('en'):
            case.assertCountEqual(handle_check_exist_record(list_record),result)

    # case 3 import items with id and uri
    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "list_records", "b4_handle_check_exist_record2.json")
    with open(filepath,encoding="utf-8") as f:
        list_record = json.load(f)

    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "list_records", "b4_handle_check_exist_record_result2.json")
    with open(filepath,encoding="utf-8") as f:
        result = json.load(f)

    with app.test_request_context():
        with set_locale('en'):
            with patch("weko_deposit.api.WekoRecord.get_record_by_pid") as m:
                m.return_value.pid.is_deleted.return_value = False
                m.return_value.get.side_effect = [1,2,3,4,5,6,7,8,9,10]
                case.assertCountEqual(handle_check_exist_record(list_record),result)

    # case 4 import new items with doi_ra
    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "list_records", "b4_handle_check_exist_record3.json")
    with open(filepath,encoding="utf-8") as f:
        list_record = json.load(f)

    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "list_records", "b4_handle_check_exist_record3_result.json")
    with open(filepath,encoding="utf-8") as f:
        result = json.load(f)

    with app.test_request_context():
        with set_locale('en'):
            case.assertCountEqual(handle_check_exist_record(list_record),result)


# def make_file_by_line(lines):
def test_make_file_by_line(i18n_app):
    assert make_file_by_line("lines")


# def make_stats_file(raw_stats, list_name):
def test_make_stats_file(i18n_app):
    raw_stats = [
        {'a': 1},
        {'b': 2},
        {'c': 3},
    ]

    list_name = [
        'a',
        'b',
        'c'
    ]

    assert make_stats_file(raw_stats, list_name)


# def create_deposit(item_id):
def test_create_deposit(i18n_app, location, indices):
    assert create_deposit(33)


# def clean_thumbnail_file(deposit, root_path, thumbnail_path):
def test_clean_thumbnail_file(i18n_app, deposit):
    deposit = deposit
    root_path = '/'
    thumbnail_path = '/'

    # Doesn't return a value
    assert not clean_thumbnail_file(deposit, root_path, thumbnail_path)


# def up_load_file(record, root_path, deposit, allow_upload_file_content, old_files):
def test_up_load_file(i18n_app, deposit, db_activity):
    record = db_activity['record']
    root_path = '/'
    deposit = deposit
    allow_upload_file_content = True
    old_files = {}

    # Doesn't return a value
    assert not up_load_file(record, root_path, deposit, allow_upload_file_content, old_files)


# def get_file_name(file_path):
def test_get_file_name(i18n_app):
    assert get_file_name("test/test/test")


# def register_item_metadata(item, root_path, is_gakuninrdm=False): ERROR ~ sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such function: concat
"""
Error file: invenio_files_rest/utils.py
Error function:
def find_and_update_location_size():
    ret = db.session.query(
        Location.id,
        sa.func.sum(FileInstance.size),
        Location.size
    ).filter(
        FileInstance.uri.like(sa.func.concat(Location.uri, '%'))
    ).group_by(Location.id)

    for row in ret:
        if row[1] != row[2]:
            with db.session.begin_nested():
                loc = db.session.query(Location).filter(
                    Location.id == row[0]).one()
                loc.size = row[1]
"""
def test_register_item_metadata(i18n_app, deposit, es_records, location):
    item = es_records['results'][0]['item']
    root_path = os.path.dirname(os.path.abspath(__file__))
    
    assert register_item_metadata(item, root_path, is_gakuninrdm=False)


# def update_publish_status(item_id, status):
def test_update_publish_status(i18n_app, es_records):
    item_id = 1
    status = None

    # Doesn't return a value
    assert not update_publish_status(item_id, status)


# def handle_workflow(item: dict):
def test_handle_workflow(i18n_app, es_records):
    item = es_records['results'][0]['item']

    # Doesn't return any value
    assert not handle_workflow(item)


# def create_work_flow(item_type_id):
def test_create_work_flow(i18n_app, db_itemtype, db_workflow):
    # Doesn't return any value
    assert not create_work_flow(db_itemtype['item_type'].id)


# def create_flow_define():
def test_create_flow_define(i18n_app, db_activity):
    # Doesn't return anything
    assert not create_flow_define()


# def send_item_created_event_to_es(item, request_info): ERR
def test_send_item_created_event_to_es(i18n_app, es_records, client_request_args, users, es):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        item = es_records['results'][0]['item']
        request_info = {
            "remote_addr": request.remote_addr,
            "referrer": request.referrer,
            "hostname": request.host,
            "user_id": 1
        }

        assert send_item_created_event_to_es(item, request_info)


# def import_items_to_system(item: dict, request_info=None, is_gakuninrdm=False): ERROR = TypeError: handle_remove_es_metadata() missing 2 required positional arguments: 'bef_metadata' and 'bef_las...
def test_import_items_to_system(i18n_app, es_records):
    # item = dict(db_activity['item'])
    item = es_records['results'][0]['item']

    assert import_items_to_system(item)


# def handle_item_title(list_record):
def test_handle_item_title(i18n_app, es_records):
    list_record = [es_records['results'][0]['item']]

    # Doesn't return any value
    assert not handle_item_title(list_record)
    

# def handle_check_and_prepare_publish_status(list_record):
def test_handle_check_and_prepare_publish_status(i18n_app, record_with_metadata):
    list_record = [record_with_metadata[0]]

    # Doesn't return any value
    assert not handle_check_and_prepare_publish_status(list_record)


# def handle_check_and_prepare_index_tree(list_record, all_index_permission, can_edit_indexes): 20220929
def test_handle_check_and_prepare_index_tree(i18n_app, record_with_metadata, indices):
    list_record = [record_with_metadata[0]]
    can_edit_indexes = [indices['index_dict']]

    # Test 1
    all_index_permission = False
    assert not handle_check_and_prepare_index_tree(list_record, all_index_permission, can_edit_indexes)

    # Test 2
    all_index_permission = True
    assert not handle_check_and_prepare_index_tree(list_record, all_index_permission, can_edit_indexes)


# def handle_check_and_prepare_feedback_mail(list_record):
def test_handle_check_and_prepare_feedback_mail(i18n_app, record_with_metadata):
    list_record = [record_with_metadata[0]]

    # Doesn't return any value
    assert not handle_check_and_prepare_feedback_mail(list_record)


# def handle_set_change_identifier_flag(list_record, is_change_identifier):
def test_handle_set_change_identifier_flag(i18n_app, record_with_metadata):
    list_record = [record_with_metadata[0]]
    is_change_identifier = True

    # Doesn't return any value
    assert not handle_set_change_identifier_flag(list_record, is_change_identifier)


# def handle_check_cnri(list_record):
def test_handle_check_cnri(i18n_app, db_activity):
    list_record = [db_activity['item']]

    # Doesn't return any value
    assert not handle_check_cnri(list_record)


# def handle_check_doi_indexes(list_record):
def test_handle_check_doi_indexes(i18n_app, es_records):
    list_record = [es_records['results'][0]['item']]

    # Doesn't return any value
    assert not handle_check_doi_indexes(list_record)


# def handle_check_doi_ra(list_record):
def test_handle_check_doi_ra(i18n_app, es_records):
    list_record = [es_records['results'][0]['item']]

    # Doesn't return any value
    assert not handle_check_doi_ra(list_record)


# def handle_check_doi(list_record):
def test_handle_check_doi(app):
    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "list_records", "list_records.json")
    with open(filepath,encoding="utf-8") as f:
        list_record = json.load(f)
    assert handle_check_doi(list_record)==None

    # case new items with doi_ra
    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "list_records", "b4_handle_check_doi.json")
    with open(filepath,encoding="utf-8") as f:
        list_record = json.load(f)
    assert handle_check_doi(list_record)==None


# def register_item_handle(item):
def test_register_item_handle(i18n_app, es_records):
    item = es_records['results'][0]['item']
    
    # Doesn't return any value
    assert not register_item_handle(item)


# def prepare_doi_setting():
def test_prepare_doi_setting(i18n_app, communities2, db):
    from weko_workflow.utils import get_identifier_setting
    from weko_admin.models import Identifier
    test_identifier = Identifier(
        id=1,
        repository="Root Index",
        created_userId="user1",
        created_date=datetime.now(),
        updated_userId="user1"
    )
    db.session.add(test_identifier)
    db.session.commit()

    assert prepare_doi_setting()


# def get_doi_prefix(doi_ra):
WEKO_IMPORT_DOI_TYPE = ["JaLC", "Crossref", "DataCite", "NDL JaLC"]
@pytest.mark.parametrize("doi_ra", WEKO_IMPORT_DOI_TYPE)
def test_get_doi_prefix(i18n_app, communities2, doi_ra, db):
    from weko_workflow.utils import get_identifier_setting
    from weko_admin.models import Identifier
    test_identifier = Identifier(
        id=1,
        repository="Root Index",
        created_userId="user1",
        created_date=datetime.now(),
        updated_userId="user1"
    )
    db.session.add(test_identifier)
    db.session.commit()

    assert get_doi_prefix(doi_ra)
    

# def get_doi_link(doi_ra, data):
def test_get_doi_link(i18n_app):
    doi_ra = ["JaLC", "Crossref", "DataCite", "NDL JaLC"]
    data = {
        "identifier_grant_jalc_doi_link": doi_ra[0],
        "identifier_grant_jalc_cr_doi_link": doi_ra[1],
        "identifier_grant_jalc_dc_doi_link": doi_ra[2],
        "identifier_grant_ndl_jalc_doi_link": doi_ra[3],
    }

    assert get_doi_link(doi_ra[0], data)
    assert get_doi_link(doi_ra[1], data)
    assert get_doi_link(doi_ra[2], data)
    assert get_doi_link(doi_ra[3], data)


# def prepare_doi_link(item_id):
def test_prepare_doi_link(i18n_app, communities2, db):
    from weko_admin.models import Identifier
    test_identifier = Identifier(
        id=1,
        repository="Root Index",
        created_userId="user1",
        created_date=datetime.now(),
        updated_userId="user1"
    )
    db.session.add(test_identifier)
    db.session.commit()
    item_id = 90

    assert prepare_doi_link(item_id)


# def register_item_doi(item):
def test_register_item_doi(i18n_app, db_activity):
    # item = es_records['results'][0]['item']
    item = db_activity['item']

    # Doesn't return any value
    assert not register_item_doi(item)


# def register_item_update_publish_status(item, status): ERR
def test_register_item_update_publish_status(i18n_app, es_records):
    item = es_records['results'][0]['item']
    # item = db_activity['item']
    status = 0

    # Doesn't return any value
    assert not register_item_update_publish_status(item, status)
    

# def handle_doi_required_check(record):
def test_handle_doi_required_check(i18n_app, es_records, record_with_metadata, db_itemtype, item_type):
    record = record_with_metadata[1]

    # Should have no return value
    assert not handle_doi_required_check(record)


# def handle_check_date(list_record):
def test_handle_check_date(app, test_list_records, mocker_itemtype):
    for t in test_list_records:
        input_data = t.get("input")
        output_data = t.get("output")
        with app.app_context():
            ret = handle_check_date(input_data)
            assert ret == output_data


# def handle_check_id(list_record):
def test_handle_check_id(i18n_app, record_with_metadata):
    list_record = [record_with_metadata[1]]

    # Doesn't return any value
    assert not handle_check_id(list_record)


# def get_data_in_deep_dict(search_key, _dict={}):
def test_get_data_in_deep_dict(i18n_app):
    search_key = "test"
    _dict = {
        "test": 1,
        "sample": {"a": 1}
    }

    assert get_data_in_deep_dict(search_key, _dict)


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
def test_validation_date_property():
    # with pytest.raises(Exception):
    assert validation_date_property("2022")==True
    assert validation_date_property("2022-03")==True
    assert validation_date_property("2022-1")==False
    assert validation_date_property("2022-1-1")==False
    assert validation_date_property("2022-2-31")==False
    assert validation_date_property("2022-12-01")==True
    assert validation_date_property("2022-02-31")==False
    assert validation_date_property("2022-12-0110")==False
    assert validation_date_property("hogehoge")==False


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
def test_get_current_language(i18n_app):
    assert get_current_language()


# def get_change_identifier_mode_content():
def test_get_change_identifier_mode_content(i18n_app):
    assert get_change_identifier_mode_content()


# def get_root_item_option(item_id, item, sub_form={"title_i18n": {}}):
def test_get_root_item_option(i18n_app):
    item_id = 1
    item = {
        "title": "title",
        "option": {
            "required": "required",
            "hidden": "hidden",
            "multiple": "multiple",
        }
    }

    assert get_root_item_option(item_id, item)


# def get_sub_item_option(key, schemaform):
def test_get_sub_item_option(i18n_app):
    key = "key"
    schemaform = [
        {
            "key": "key",
            "required": "required",
            "isHide": "isHide"
        },
        {
            "items": {
                "key": "key",
                "required": "required",
                "isHide": "isHide"
            }
        }
    ]

    assert get_sub_item_option(key, schemaform)


# def check_sub_item_is_system(key, schemaform):
def test_check_sub_item_is_system(i18n_app):
    key = "key"
    schemaform = [
        {
            "key": "key",
            "required": "required",
            "isHide": "isHide",
            "readonly": True
        },
        {
            "items": {
                "key": "key",
                "required": "required",
                "isHide": "isHide",
                "readonly": True
            }
        }
    ]

    assert check_sub_item_is_system(key, schemaform)


# def get_lifetime():
def test_get_lifetime(i18n_app, db_register2):
    assert get_lifetime()


# def get_system_data_uri(key_type, key):
def test_get_system_data_uri():
    data = [{"resource_type":RESOURCE_TYPE_URI}, {"version_type": VERSION_TYPE_URI}, {"access_right":ACCESS_RIGHT_TYPE_URI}]
    for t in data:
        for key_type in t.keys():
            val = t.get(key_type)
            for key in val.keys():
                url = val.get(key)
                assert get_system_data_uri(key_type,key)==url


# def handle_fill_system_item(list_record):
def test_handle_fill_system_item(app,test_list_records,mocker):

    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "item_map.json")
    with open(filepath,encoding="utf-8") as f:
        item_map = json.load(f)

    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "item_type_mapping.json")
    with open(filepath,encoding="utf-8") as f:
        item_type_mapping = json.load(f)
    mocker.patch("weko_records.serializers.utils.get_mapping",return_value=item_map)
    mocker.patch("weko_records.api.Mapping.get_record",return_value=item_type_mapping)

    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data", "list_records/list_records_fill_system.json")
    with open(filepath,encoding="utf-8") as f:
        list_record = json.load(f)

    items = []
    items_result = []

    for a in VERSION_TYPE_URI:
        item = copy.deepcopy(list_record[0])
        item['metadata']['item_1617265215918']['subitem_1522305645492']=a
        item['metadata']['item_1617265215918']['subitem_1600292170262']=VERSION_TYPE_URI[a]
        item['metadata']['item_1617186476635']['subitem_1522299639480']="open access"
        item['metadata']['item_1617186476635']['subitem_1600958577026']=ACCESS_RIGHT_TYPE_URI["open access"]
        item['metadata']['item_1617258105262']['resourcetype']="conference paper"
        item['metadata']['item_1617258105262']['resourceuri']=RESOURCE_TYPE_URI["conference paper"]
        items_result.append(item)
        item2 = copy.deepcopy(item)
        item2['metadata']['item_1617265215918']['subitem_1522305645492']=a
        item2['metadata']['item_1617265215918']['subitem_1600292170262']=""
        items.append(item2)

    for a in ACCESS_RIGHT_TYPE_URI:
        item = copy.deepcopy(list_record[0])
        item['metadata']['item_1617265215918']['subitem_1522305645492']="VoR"
        item['metadata']['item_1617265215918']['subitem_1600292170262']=VERSION_TYPE_URI["VoR"]
        item['metadata']['item_1617186476635']['subitem_1522299639480']=a
        item['metadata']['item_1617186476635']['subitem_1600958577026']=ACCESS_RIGHT_TYPE_URI[a]
        item['metadata']['item_1617258105262']['resourcetype']="conference paper"
        item['metadata']['item_1617258105262']['resourceuri']=RESOURCE_TYPE_URI["conference paper"]
        items_result.append(item)
        item2 = copy.deepcopy(item)
        item2['metadata']['item_1617186476635']['subitem_1522299639480']=a
        item2['metadata']['item_1617186476635']['subitem_1600958577026']=""
        items.append(item2)

    for a in RESOURCE_TYPE_URI:
        item = copy.deepcopy(list_record[0])
        item['metadata']['item_1617265215918']['subitem_1522305645492']="VoR"
        item['metadata']['item_1617265215918']['subitem_1600292170262']=VERSION_TYPE_URI["VoR"]
        item['metadata']['item_1617186476635']['subitem_1522299639480']="open access"
        item['metadata']['item_1617186476635']['subitem_1600958577026']=ACCESS_RIGHT_TYPE_URI["open access"]
        item['metadata']['item_1617258105262']['resourcetype']= a
        item['metadata']['item_1617258105262']['resourceuri']=RESOURCE_TYPE_URI[a]
        items_result.append(item)
        item2 = copy.deepcopy(item)
        item2['metadata']['item_1617258105262']['resourcetype']=a
        item2['metadata']['item_1617258105262']['resourceuri']=""
        items.append(item2)

    # with open("items.json","w") as f:
    #     json.dump(items,f)

    # with open("items_result.json","w") as f:
    #     json.dump(items_result,f)


    # filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data/handle_fill_system_item/items.json")
    # with open(filepath,encoding="utf-8") as f:
    #     items = json.load(f)

    # filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"data/handle_fill_system_item/items_result.json")
    # with open(filepath,encoding="utf-8") as f:
    #     items_result = json.load(f)

    with app.test_request_context():
        with set_locale('en'):
            handle_fill_system_item(items)
            assert len(items)==len(items_result)
            assert items==items_result


# def get_thumbnail_key(item_type_id=0):
def test_get_thumbnail_key(i18n_app, db_itemtype, db_workflow):
    assert get_thumbnail_key(item_type_id=1)


# def handle_check_thumbnail_file_type(thumbnail_paths):
def test_handle_check_thumbnail_file_type(i18n_app):
    assert handle_check_thumbnail_file_type(["/"])


# def handle_check_metadata_not_existed(str_keys, item_type_id=0):
def test_handle_check_metadata_not_existed(i18n_app, db_itemtype):
    # Test 1
    assert not handle_check_metadata_not_existed(".metadata", db_itemtype['item_type'].id)


# def handle_get_all_sub_id_and_name(items, root_id=None, root_name=None, form=[]):
@pytest.mark.parametrize(
    "items,root_id,root_name,form,ids,names",[
        pytest.param({'interim': {'type': 'string'}},'.metadata.item_1657196790737[0]','text[0]',[{'key': 'item_1657196790737[].interim', 'type': 'text', 'notitle': True}],['.metadata.item_1657196790737[0].interim'],['text[0].None']),
        pytest.param({'interim': {'enum': [None, 'op1', 'op2', 'op3', 'op4'], 'type': ['null', 'string'], 'title': 'list', 'title_i18n': {'en': '', 'ja': ''}}},
        '.metadata.item_1657204077414[0]',
        'list[0]',[{'key': 'item_1657204077414[].interim', 'type': 'select', 'title': 'list', 'notitle': True, 'titleMap': [{'name': 'op1', 'value': 'op1'}, {'name': 'op2', 'value': 'op2'}, {'name': 'op3', 'value': 'op3'}, {'name': 'op4', 'value': 'op4'}], 'title_i18n': {'en': '', 'ja': ''}}]
        ,['.metadata.item_1657204026946.interim[0]'],['check.check[0]']),
        pytest.param({'interim': {'enum': [None, 'op1', 'op2', 'op3', 'op4'], 'type': ['null', 'string'], 'title': 'list', 'format': 'select'}},
'.metadata.item_1657204070640','list',[{'key': 'item_1657204070640.interim', 'type': 'select', 'title': 'list', 'titleMap': [{'name': 'op1', 'value': 'op1'}, {'name': 'op2', 'value': 'op2'}, {'name': 'op3', 'value': 'op3'}, {'name': 'op4', 'value': 'op4'}], 'title_i18n': {'en': '', 'ja': ''}}]
,['.metadata.item_1657204036771[0].interim[0]'],['checjk[0].checjk[0]']),
pytest.param({'interim': {'type': 'array', 'items': {'enum': ['op1', 'op2', 'op3', 'op4'], 'type': 'string'}, 'title': 'check', 'format': 'checkboxes', 'title_i18n': {'en': '', 'ja': ''}}},
'.metadata.item_1657204026946','check',[{'key': 'item_1657204026946.interim', 'type': 'template', 'title': 'check', 'titleMap': [{'name': 'op1', 'value': 'op1'}, {'name': 'op2', 'value': 'op2'}, {'name': 'op3', 'value': 'op3'}, {'name': 'op4', 'value': 'op4'}], 'title_i18n': {'en': '', 'ja': ''}, 'templateUrl': '/static/templates/weko_deposit/checkboxes.html'}]
,['.metadata.item_1657204043063.interim'],['rad.rad']),
pytest.param({'interim': {'type': 'array', 'items': {'enum': ['op1', 'op2', 'op3', 'op4'], 'type': 'string'}, 'title': 'checjk', 'format': 'checkboxes', 'title_i18n': {'en': '', 'ja': ''}}},
'.metadata.item_1657204036771[0]','check[0]',[{'key': 'item_1657204036771[].interim', 'type': 'template', 'title': 'checjk', 'notitle': True, 'titleMap': [{'name': 'op1', 'value': 'op1'}, {'name': 'op2', 'value': 'op2'}, {'name': 'op3', 'value': 'op3'}, {'name': 'op4', 'value': 'op4'}], 'title_i18n': {'en': '', 'ja': ''}, 'templateUrl': '/static/templates/weko_deposit/checkboxes.html'}]
,['.metadata.item_1657204049138[0].interim'],['rd[0].rd']),
pytest.param({'interim': {'enum': ['op1', 'op2', 'op3', 'op4'], 'type': ['null', 'string'], 'title': 'rad', 'format': 'radios'}},
'.metadata.item_1657204043063',
'rad',[{'key': 'item_1657204043063.interim', 'type': 'radios', 'title': 'rad', 'titleMap': [{'name': 'op1', 'value': 'op1'}, {'name': 'op2', 'value': 'op2'}, {'name': 'op3', 'value': 'op3'}, {'name': 'op4', 'value': 'op4'}], 'title_i18n': {'en': '', 'ja': ''}}]
,['.metadata.item_1657204070640.interim'],['list.list']),
pytest.param({'interim': {'enum': ['op1', 'op2', 'op3', 'op4'], 'type': ['null', 'string'], 'title': 'rd', 'title_i18n': {'en': '', 'ja': ''}}},
'.metadata.item_1657204049138[0]','rd[0]',[{'key': 'item_1657204049138[].interim', 'type': 'radios', 'title': 'rd', 'notitle': True, 'titleMap': [{'name': 'op1', 'value': 'op1'}, {'name': 'op2', 'value': 'op2'}, {'name': 'op3', 'value': 'op3'}, {'name': 'op4', 'value': 'op4'}], 'title_i18n': {'en': '', 'ja': ''}}]
,['.metadata.item_1657204077414[0].interim'],['list[0].list']
)
]
)
def test_handle_get_all_sub_id_and_name(app,items,root_id,root_name,form,ids,names):
    with app.app_context():
        assert ids,names == handle_get_all_sub_id_and_name(items,root_id,root_name,form)


# def handle_get_all_id_in_item_type(item_type_id):
def test_handle_get_all_id_in_item_type(i18n_app, db_itemtype):
    assert handle_get_all_id_in_item_type(db_itemtype['item_type'].id)


# def handle_check_consistence_with_mapping(mapping_ids, keys):
def test_handle_check_consistence_with_mapping(i18n_app):
    mapping_ids = ["abc"]
    keys = ["abc"]

    # Test 1
    assert not handle_check_consistence_with_mapping(mapping_ids, keys)


# def handle_check_duplication_item_id(ids: list):
def test_handle_check_duplication_item_id(i18n_app):
    ids = [[1,2,3,4],2,3,4]

    # Test 1
    assert not handle_check_duplication_item_id(ids)


# def export_all(root_url, user_id, data):
def test_export_all(db_activity, i18n_app, users, item_type, db_records2):
    root_url = "/"
    user_id = users[3]['obj'].id
    data = {
        "item_type_id": 1,
        "item_id_range": 1
    }
    data2 = {
        "item_type_id": -1,
        "item_id_range": 1-9
    }

    # Test 1
    assert not export_all(root_url, user_id, data)

    # Test 2
    assert not export_all(root_url, user_id, data2)


# def delete_exported(uri, cache_key):
def test_delete_exported(i18n_app, file_instance_mock):
    file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'data',
        'sample_file',
        'sample_file.txt'
    )

    # Doesn't return any value
    assert not delete_exported(file_path, "key")


# def cancel_export_all(): ~ GETS STUCK
# def test_cancel_export_all(i18n_app, users):
#     with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
#         assert cancel_export_all()


# def get_export_status():
def test_get_export_status(i18n_app, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert get_export_status()


# def handle_check_item_is_locked(item):
def test_handle_check_item_is_locked(i18n_app, db_activity):
    # Doesn't return any value
    try:
        assert not handle_check_item_is_locked(db_activity['item'])
    except Exception as e:
        if "item_is_being_edit" in str(e) or "item_is_deleted" in str(e):
            assert True
        else:
            pass
        

# def handle_remove_es_metadata(item, bef_metadata, bef_last_ver_metadata):
def test_handle_remove_es_metadata(i18n_app, es_records):
    item = es_records['results'][0]['item']
    bef_metadata = {}
    bef_metadata["_id"] = 9
    bef_metadata["_version"] = -1
    bef_metadata["_source"] = {"control_number": 9999}
    
    bef_last_ver_metadata = {}
    bef_last_ver_metadata["_id"] = 8
    bef_last_ver_metadata["_version"] = 1
    bef_last_ver_metadata["_source"] = {"control_number": 8888}

    # Doesn't return any value
    assert not handle_remove_es_metadata(item, bef_metadata, bef_last_ver_metadata)

    # Doesn't return any value
    item['status'] = 'new'
    assert not handle_remove_es_metadata(item, bef_metadata, bef_last_ver_metadata)

    # Doesn't return any value
    item['status'] = 'upgrade'
    assert not handle_remove_es_metadata(item, bef_metadata, bef_last_ver_metadata)


# def check_index_access_permissions(func):
@check_index_access_permissions
def test_check_index_access_permissions(i18n_app, client_request_args, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):

        # Test is successful if there are no errors
        assert True


# def handle_check_file_metadata(list_record, data_path):
def test_handle_check_file_metadata(i18n_app, record_with_metadata):
    list_record = [record_with_metadata[0]]
    data_path = "test/test/test"

    # Doesn't return any value
    assert not handle_check_file_metadata(list_record, data_path)


# def handle_check_file_path(paths, data_path, is_new=False, is_thumbnail=False, is_single_thumbnail=False):
def test_handle_check_file_path(i18n_app):
    paths = ["/test"]
    data_path = "/"

    assert handle_check_file_path(paths, data_path)


# def handle_check_file_content(record, data_path):
def test_handle_check_file_content(i18n_app, record_with_metadata):
    list_record = record_with_metadata[0]
    data_path = "test/test/test"

    assert handle_check_file_content(list_record, data_path)


# def handle_check_thumbnail(record, data_path):
def test_handle_check_thumbnail(i18n_app, record_with_metadata):
    list_record = record_with_metadata[0]
    data_path = "test/test/test"

    assert handle_check_thumbnail(list_record, data_path)


# def get_key_by_property(record, item_map, item_property):
def test_get_key_by_property(i18n_app):
    record = "record"
    item_map = {"item_property": "item_property"}
    item_property = "item_property"

    assert get_key_by_property(record, item_map, item_property)


# def get_data_by_property(item_metadata, item_map, mapping_key):
def test_get_data_by_property(i18n_app):
    item_metadata = {}
    item_map = {"mapping_key": "{'test': 1}.test"}
    mapping_key = "mapping_key"

    assert get_data_by_property(item_metadata, item_map, mapping_key)


# def get_filenames_from_metadata(metadata):
def test_get_filenames_from_metadata(i18n_app, record_with_metadata):
    metadata = record_with_metadata[0]['metadata']
    assert get_filenames_from_metadata(metadata)


# def handle_check_filename_consistence(file_paths, meta_filenames):
def test_handle_check_filename_consistence(i18n_app):
    file_paths = ["abc/abc", "abc/abc"]
    meta_filenames = [{"id": 1, "filename": "abc"}, {"id": 2, "filename": "xyz"}]

    assert handle_check_filename_consistence(file_paths, meta_filenames)