# -*- coding: utf-8 -*-

from collections import OrderedDict
import json
import pytest
import os

from weko_records.utils import convert_date_range_value, convert_range_value, \
    copy_value_json_path, copy_values_json_path, makeDateRangeValue, remove_weko2_special_character


@pytest.fixture
def identifiers():
    identifier = ['oai:weko3.example.org:00000965']
    return identifiers

@pytest.fixture
def k_v():
    k_v = [{'id': 'date_range1', 'mapping': [], 'contents': '', 'inputType': 'dateRange', 'input_Type': 'range', 'item_value':{'1': {'path': {'gte': '', 'lte': ''}, 'path_type': {'gte': 'json', 'lte': 'json'}}, '12': {'path': {'gte': '$.item_1551265302120.attribute_value_mlt[*].subitem_1551256918211', 'lte': '$.item_1551265302120.attribute_value_mlt[*].subitem_1551256918211'}, 'path_type': {'gte': 'json', 'lte': 'json'}}}, 'mappingFlg': False, 'inputVal_to': '', 'mappingName': '', 'inputVal_from': '', 'contents_value': {'en': 'date_EN_1', 'ja': 'date_JA_1'}, 'useable_status': True, 'default_display': True}, {"id": "text3", "mapping": [], "contents": "", "inputVal": "", "inputType": "text", "input_Type": "text", "item_value":  {"1": {"path": "", "path_type": "json"}, "12": {"path": "$.item_1551264846237.attribute_value_mlt[*].subitem_1551255577890", "path_type": "json"}, "20": {"path": "$.item_1551264846237.attribute_value_mlt[*].subitem_1551255577890", "path_type": "json"}}, "mappingFlg": False, "mappingName": "", "contents_value": {"en": "Summary", "ja": "概要"}, "useable_status": True, "default_display": True}
           ]
    return k_v

@pytest.fixture
def jsonpath():
    return ['$.item_1551264418667.attribute_value_mlt[*].subitem_1551257245638[*].subitem_1551257276108', '$.item_1551265302120.attribute_value_mlt[*].subitem_1551256918211', 
    '$.item_1551264846237.attribute_value_mlt[*].subitem_1551255577890',
    '$.item_1551264846237.attribute_value_mlt[1:3].subitem_1551255577890']

@pytest.fixture
def meta():
    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data", "meta00.json")
    with open(filepath, encoding="utf-8") as f:
            input_data = json.load(f)
    return input_data

# def json_loader(data, pid, owner_id=None):
# def copy_field_test(dc, map, jrc, iid=None):
# def convert_range_value(start, end=None):

def test_convert_range_value():
    assert convert_range_value('1', '2') == {'gte': '1', 'lte': '2'}


# def convert_date_range_value(start, end=None):

def test_convert_date_range_value():
    assert convert_date_range_value('1762-01-26/1762-02-23') == {'gte': '1762-01-26',
                                                                 'lte': '1762-02-23'}
    assert convert_date_range_value('2000-01-01/2021-03-30') == {'gte': '2000-01-01',
                                                                 'lte': '2021-03-30'}
    assert convert_date_range_value(' 1762-01-26/1762-02-23 ') == {'gte': '1762-01-26',
                                                                   'lte': '1762-02-23'}
    assert convert_date_range_value('2000-01/2021-03') == {'gte': '2000-01',
                                                           'lte': '2021-03'}
    assert convert_date_range_value('2000/2021') == {'gte': '2000',
                                                     'lte': '2021'}
    assert convert_date_range_value('2000-01-01') == {'gte': '2000-01-01',
                                                      'lte': '2000-01-01'}
    assert convert_date_range_value('2000-01') == {'gte': '2000-01',
                                                   'lte': '2000-01'}
    assert convert_date_range_value('2000') == {'gte': '2000',
                                                'lte': '2000'}
    assert convert_date_range_value('2000-01-01', '2000-12-01') == {'gte': '2000-01-01',
                                                                    'lte': '2000-12-01'}
    assert convert_date_range_value(None, '2000-12-01') == {'gte': '2000-12-01',
    assert convert_date_range_value(
        '1979-01-01/1960-01-01') == {'gte': '1960-01-01', 'lte': '1979-01-01'}
    assert convert_date_range_value(
        '1979-1-1/1960-1-1') == {'gte': '1960-1-1', 'lte': '1979-1-1'}
    assert convert_date_range_value('2021/12/1')=={'gte': '2021-12-1', 'lte': '2021-12-1'}


# def makeDateRangeValue(start, end):

def test_makeDateRangeValue():
    assert makeDateRangeValue('1979', '1960') == {
        'gte': '1960', 'lte': '1979'}
    assert makeDateRangeValue('1979-01-01', '1960-01-01') == {
        'gte': '1960-01-01', 'lte': '1979-01-01'}
    assert makeDateRangeValue('1979-01', '1960-01') == {
        'gte': '1960-01', 'lte': '1979-01'}
    assert makeDateRangeValue('1979-01-01', '1979-12-30') == {
        'gte': '1979-01-01', 'lte': '1979-12-30'}
    assert makeDateRangeValue('1979-01-01', '1979-01-01') == {
        'gte': '1979-01-01', 'lte': '1979-01-01'}
    assert makeDateRangeValue('1979/01/01', '1979/12/30') == {
        'gte': '1979-01-01', 'lte': '1979-12-30'}
    assert makeDateRangeValue('0000-00-00', '0000-00-00') == None





# def get_value_from_dict(dc, path, path_type, iid=None):
# def get_values_from_dict(dc, path, path_type, iid=None):
# def copy_value_xml_path(dc, xml_path, iid=None):
# def copy_value_json_path(meta, jsonpath):

def test_copy_value_json_path(meta, jsonpath):
    assert copy_value_json_path(meta[0], jsonpath[0]) == ['寄与者','Contributor']
    assert copy_value_json_path(
        meta[0], jsonpath[1]) == ['2000-01-01/2021-03-30']
    assert copy_value_json_path(
        meta[0], jsonpath[2]) == ['概要', 'その他', 'materials: text']


# def copy_values_json_path(meta, jsonpath):

def test_copy_values_json_path(meta, jsonpath):
    assert copy_values_json_path(meta[0], jsonpath[0]) == [
        '寄与者', 'Contributor']
    assert copy_values_json_path(meta[0], jsonpath[1]) == [
        '2000-01-01/2021-03-30']
    assert copy_values_json_path(meta[0], jsonpath[2]) == [
        '概要', 'その他', 'materials: text']
    assert copy_values_json_path(meta[0], jsonpath[3]) == [
        'その他', 'materials: text']

# def set_timestamp(jrc, created, updated):
# def sort_records(records, form):
# def sort_op(record, kd, form):
# def find_items(form):
# def get_all_items(nlst, klst, is_get_name=False):
# def get_all_items2(nlst, klst):
# def to_orderdict(alst, klst, is_full_key=False):
# def get_options_and_order_list(item_type_id, ojson=None):
# def get_keywords_data_load(str):
# def is_valid_openaire_type(resource_type, communities):
# def check_has_attribute_value(node):
# def get_attribute_value_all_items(
# def check_input_value(old, new):
# def remove_key(removed_key, item_val):
# def remove_keys(excluded_keys, item_val):
# def remove_multiple(schema):
# def check_to_upgrade_version(old_render, new_render):
# def remove_weko2_special_character(s: str):

def test_remove_weko2_special_character():
    assert remove_weko2_special_character("HOGE")=="HOGE"
    assert remove_weko2_special_character("HOGE&EMPTY&HOGE")=="HOGEHOGE"
    assert remove_weko2_special_character("HOGE,&EMPTY&")=="HOGE"
    assert remove_weko2_special_character("&EMPTY&,HOGE")=="HOGE"
    assert remove_weko2_special_character("HOGE,&EMPTY&,HOGE")=="HOGE,,HOGE"


# def selected_value_by_language(lang_array, value_array, lang_id, val_id,
# def check_info_in_metadata(str_key_lang, str_key_val, str_lang, metadata):
# def get_value_and_lang_by_key(key, data_json, data_result, stt_key):
# def get_value_by_selected_lang(source_title, current_lang):
# def get_show_list_author(solst_dict_array, hide_email_flag, author_key,
# def format_creates(creates, hide_creator_keys):
# def get_creator(create, result_end, hide_creator_keys, current_lang):
# def get_creator_by_languages(creates_key, create):
# def get_affiliation(affiliations, result_end, current_lang, affiliation_key):
# def get_author_has_language(creator, result_end, current_lang, map_keys):
# def add_author(author_data, stt_key, is_specify_newline_array, s, value,
# def convert_bibliographic(data_sys_bibliographic):
# def add_biographic(sys_bibliographic, bibliographic_key, s, stt_key,
# def custom_record_medata_for_export(record_metadata: dict):
# def replace_fqdn(url_path: str, host_url: str = None) -> str:
# def replace_fqdn_of_file_metadata(file_metadata_lst: list,











    