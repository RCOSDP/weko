# -*- coding: utf-8 -*-

from collections import OrderedDict
import json
import pytest
import os
from mock import patch
from tests.helpers import json_data

from weko_admin.models import AdminSettings

from weko_records.utils import json_loader, convert_date_range_value, convert_range_value, \
    copy_value_json_path, copy_values_json_path, makeDateRangeValue, remove_weko2_special_character, \
        sort_meta_data_by_options
from weko_records.api import ItemTypes, Mapping
from weko_records.models import ItemTypeName

# def json_loader(data, pid, owner_id=None):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_json_loader -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_json_loader(app, db, item_type, item_type2, item_type_mapping2, records):
    _data1 = {}
    _data2 = {
        '$schema': 'http://schema/1/A-test'
    }
    _data3 = records[0][1]
    _data3['$schema'] = 'http://schema/2'
    _pid = records[0][0]

    _dc_data = {
        '_oai': {'id': '1'},
        'author_link': [],
        'control_number': '1',
        'item_1': {'attribute_name': 'item_1',
                   'attribute_value_mlt': [{'attribute_name': 'item_1',
                                            'attribute_value': 'Item'}]},
        'item_title': ['Back to the Future'],
        'item_type_id': '2',
        'owner': '1',
        'weko_shared_id': -1
    }
    _jrc_data = {
        '_item_metadata': {
            'item_1': {
                'attribute_name': 'item_1',
                'attribute_value_mlt': [
                    {'attribute_name': 'item_1',
                     'attribute_value': 'Item'}]
            },
            'item_title': ['Back to the Future'],
            'item_type_id': '2',
            'control_number': '1',
            'author_link': [],
            '_oai': {'id': '1'},
            'weko_shared_id': -1,
            'owner': '1'
        },
        '_oai': {'id': '1'},
        'author_link': [],
        'control_number': '1',
        'itemtype': 'test2',
        'publish_date': None,
        'weko_creator_id': '1',
        'weko_shared_id': -1
    }

    # do nothing
    result = json_loader(_data1, _pid)
    assert result==None
    # no item type
    with pytest.raises(Exception) as e:
        json_loader(_data2, _pid)
    assert e.type==RuntimeError
    assert str(e.value)=="Item Type 1 does not exist."
    # running
    app.config['WEKO_SCHEMA_JPCOAR_V1_SCHEMA_NAME'] = 'jpcoar_v1_mapping'
    app.config['WEKO_SCHEMA_DDI_SCHEMA_NAME'] = 'ddi_mapping'
    dc, jrc, is_edit = json_loader(_data3, _pid)
    assert dc==_dc_data
    assert jrc==_jrc_data
    assert is_edit==False

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
                                                            'lte': '2000-12-01'}
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
#     def find_key(node):
# def get_all_items(nlst, klst, is_get_name=False):
#     def get_name(key):
#     def get_items(nlst):
# def get_all_items2(nlst, klst):
#     def get_items(nlst):
# def to_orderdict(alst, klst, is_full_key=False):
# def get_options_and_order_list(item_type_id, ojson=None):

# async def sort_meta_data_by_options(
params=[
    ("data/item_type/item_type_render1.json",
     "data/item_type/item_type_form1.json",
     "data/item_type/item_type_mapping1.json",
     "data/record_hit/record_hit1.json",
     True),
    ("data/item_type/item_type_render2.json",
     "data/item_type/item_type_form2.json",
     "data/item_type/item_type_mapping2.json",
     "data/record_hit/record_hit2.json",
     False),
    ("data/item_type/item_type_render3.json",
     "data/item_type/item_type_form3.json",
     "data/item_type/item_type_mapping2.json",
     "data/record_hit/record_hit3.json",
     False),
    ("data/item_type/item_type_render_title.json",
     "data/item_type/item_type_form_title.json",
     "data/item_type/item_type_mapping_title.json",
     "data/record_hit/record_hit_title1.json",
     False),
    ("data/item_type/item_type_render_title.json",
     "data/item_type/item_type_form_title.json",
     "data/item_type/item_type_mapping_title.json",
     "data/record_hit/record_hit_title2.json",
     False),
    ("data/item_type/item_type_render_title.json",
     "data/item_type/item_type_form_title.json",
     "data/item_type/item_type_mapping_title.json",
     "data/record_hit/record_hit_title3.json",
     False),
]
@pytest.mark.parametrize("render,form,mapping,hit,licence",params)
@pytest.mark.asyncio
async def test_sort_meta_data_by_options(i18n_app, db, admin_settings, mocker,
                                         render, form, mapping, hit,licence):
    import asyncio
    mocker.patch("weko_records_ui.permissions.check_file_download_permission", return_value=True)
    _item_type_name=ItemTypeName(name="test")
    item_type = ItemTypes.create(
        name="test",
        item_type_name=_item_type_name,
        schema=json_data("data/item_type/item_type_schema.json"),
        render=json_data(render),
        form=json_data(form),
        tag=1
    )
    item_type_mapping = Mapping.create(
        item_type_id=item_type.id,
        mapping=json_data(mapping)
    )
    record_hit=json_data(hit)
    settings = AdminSettings.get('items_display_settings')
    if not licence:
        i18n_app.config.update(
            WEKO_RECORDS_UI_LICENSE_DICT=False
        )
    await sort_meta_data_by_options(record_hit,settings,item_type_mapping,item_type)


@pytest.mark.asyncio
async def test_sort_meta_data_by_options_exception(i18n_app, db, admin_settings):
    record_hit = {
        "_source":{
            "item_item_id":"",
            "_item_metadata":{}
        }
    }
    _item_type_name=ItemTypeName(name="test")
    item_type=ItemTypes.create(
        name="test",
        item_type_name=_item_type_name,
        schema={},
        render={},
        form={},
        tag=1
    )
    item_type_mapping=Mapping.create(
        item_type_id=item_type.id,
        mapping={}
    )
    settings = AdminSettings.get("items_display_settings")
    with patch("weko_records.serializers.utils.get_mapping",side_effect=Exception):
        await sort_meta_data_by_options(record_hit,settings,item_type_mapping,item_type)

@pytest.mark.asyncio
async def test_sort_meta_data_by_options_no_item_type_id(i18n_app, db, admin_settings):
    record_hit = {
        "_source":{
            "item_item_id":"",
            "_item_metadata":{}
        }
    }
    _item_type_name=ItemTypeName(name="test")
    item_type=ItemTypes.create(
        name="test",
        item_type_name=_item_type_name,
        schema={},
        render={},
        form={},
        tag=1
    )
    item_type_mapping=Mapping.create(
        item_type_id=item_type.id,
        mapping={}
    )
    settings = AdminSettings.get("items_display_settings")
    await sort_meta_data_by_options(record_hit,settings,item_type_mapping,item_type)

#     def convert_data_to_dict(solst):
#     def get_author_comment(data_result, key, result, is_specify_newline_array):
#     def data_comment(result, data_result, stt_key, is_specify_newline_array):
#     def get_comment(solst_dict_array, hide_email_flag, _item_metadata, src, solst):
#         def get_option_value(option_type, parent_option, child_option):
#     def get_file_comments(record, files):
#         def __get_label_extension():
#     def get_file_thumbnail(thumbnails):
#     def append_parent_key(key, attribute_value_mlt):
#         def get_parent_key(key):
#         def append_parent_key_all_type(parent_key, attr_val_mlt):
#         def append_parent_key_for_dict(parent_key, attr_val_mlt):
#         def append_parent_key_for_list(parent_key, attr_val_mlt):
#     def get_title_option(solst_dict_array):
# def get_keywords_data_load(str):
# def is_valid_openaire_type(resource_type, communities):
# def check_has_attribute_value(node):
# def get_attribute_value_all_items(
#     def get_name_mapping():
#     def get_name(key, multi_lang_flag=True):
#     def change_temporal_format(value):
#     def change_date_format(value):
#     def get_value(data):
#     def to_sort_dict(alst, klst):
#     def set_attribute_value(nlst):
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

#     def __remove_special_character(_s_str: str):
# def selected_value_by_language(
# def check_info_in_metadata(str_key_lang, str_key_val, str_lang, metadata):
# def get_value_and_lang_by_key(key, data_json, data_result, stt_key):
# def get_value_by_selected_lang(source_title, current_lang):
# def get_show_list_author(solst_dict_array, hide_email_flag, author_key, creates):
# def format_creates(creates, hide_creator_keys):
# def get_creator(create, result_end, hide_creator_keys, current_lang):
# def get_creator_by_languages(creates_key, create):
# def get_affiliation(affiliations, result_end, current_lang, affiliation_key):
# def get_author_has_language(creator, result_end, current_lang, map_keys):
# def add_author(
# def convert_bibliographic(data_sys_bibliographic):
# def add_biographic(
# def custom_record_medata_for_export(record_metadata: dict):
# def replace_fqdn(url_path: str, host_url: str = None) -> str:
# def replace_fqdn_of_file_metadata(file_metadata_lst: list, file_url: list = None):
