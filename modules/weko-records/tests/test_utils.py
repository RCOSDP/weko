# -*- coding: utf-8 -*-

from collections import OrderedDict
from datetime import datetime
import json
# from tkinter import W
import pytest
import os
from mock import patch
from tests.helpers import json_data

from invenio_accounts import testutils
from invenio_i18n.ext import current_i18n
from weko_admin.models import AdminSettings
from weko_records.utils import (
    json_loader,
    copy_field_test,
    convert_range_value,
    convert_date_range_value,
    makeDateRangeValue,
    get_value_from_dict,
    get_values_from_dict,
    copy_value_xml_path,
    copy_value_json_path,
    copy_values_json_path,
    set_timestamp,
    sort_records,
    sort_op,
    find_items,
    get_all_items,
    get_all_items2,
    to_orderdict,
    get_options_and_order_list,
    sort_meta_data_by_options,
    get_keywords_data_load,
    is_valid_openaire_type,
    check_has_attribute_value,
    get_attribute_value_all_items,
    check_input_value,
    remove_key,
    remove_keys,
    remove_multiple,
    check_to_upgrade_version,
    remove_weko2_special_character,
    selected_value_by_language,
    check_info_in_metadata,
    get_value_and_lang_by_key,
    get_value_by_selected_lang,
    get_show_list_author,
    format_creates,
    get_creator,
    get_creator_by_languages,
    get_affiliation,
    get_author_has_language,
    add_author,
    convert_bibliographic,
    add_biographic,
    custom_record_medata_for_export,
    replace_fqdn,
    replace_fqdn_of_file_metadata)
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
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_copy_field_test -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_copy_field_test(app, meta, k_v):
    _jrc = {}
    copy_field_test(meta[0], k_v, _jrc)
    assert _jrc=={
        'date_range1': [{'gte': '2000-01-01', 'lte': '2021-03-30'}],
        'text3': ['概要', 'その他', 'materials: text']
    }

# def convert_range_value(start, end=None):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_convert_range_value -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_convert_range_value():
    assert convert_range_value('1')=={'gte': '1', 'lte': '1'}
    assert convert_range_value(None, '2')=={'gte': '2', 'lte': '2'}
    assert convert_range_value('1', '2')=={'gte': '1', 'lte': '2'}

# def convert_date_range_value(start, end=None):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_convert_date_range_value -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_convert_date_range_value():
    assert convert_date_range_value(
        '1762-01-26/1762-02-23')=={'gte': '1762-01-26', 'lte': '1762-02-23'}
    assert convert_date_range_value(
        '2000-01-01/2021-03-30')=={'gte': '2000-01-01', 'lte': '2021-03-30'}
    assert convert_date_range_value(
        ' 1762-01-26/1762-02-23 ')=={'gte': '1762-01-26', 'lte': '1762-02-23'}
    assert convert_date_range_value(
        '2000-01/2021-03')=={'gte': '2000-01', 'lte': '2021-03'}
    assert convert_date_range_value(
        '2000/2021')=={'gte': '2000', 'lte': '2021'}
    assert convert_date_range_value(
        '2000-01-01')=={'gte': '2000-01-01', 'lte': '2000-01-01'}
    assert convert_date_range_value(
        '2000-01')=={'gte': '2000-01', 'lte': '2000-01'}
    assert convert_date_range_value(
        '2000')=={'gte': '2000', 'lte': '2000'}
    assert convert_date_range_value(
        '2000-01-01', '2000-12-01')=={'gte': '2000-01-01', 'lte': '2000-12-01'}
    assert convert_date_range_value(
        None, '2000-12-01')=={'gte': '2000-12-01', 'lte': '2000-12-01'}
    assert convert_date_range_value(
        '1979-01-01/1960-01-01')=={'gte': '1960-01-01', 'lte': '1979-01-01'}
    assert convert_date_range_value(
        '1979-1-1/1960-1-1')=={'gte': '1960-1-1', 'lte': '1979-1-1'}
    assert convert_date_range_value('2021/12/1')=={'gte': '2021-12-1', 'lte': '2021-12-1'}

# def makeDateRangeValue(start, end):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_makeDateRangeValue -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_makeDateRangeValue():
    assert makeDateRangeValue(
        '1979', '1960')=={'gte': '1960', 'lte': '1979'}
    assert makeDateRangeValue(
        '1979-01-01', '1960-01-01')=={'gte': '1960-01-01', 'lte': '1979-01-01'}
    assert makeDateRangeValue(
        '1979-01', '1960-01')=={'gte': '1960-01', 'lte': '1979-01'}
    assert makeDateRangeValue(
        '1979-01-01', '1979-12-30')=={'gte': '1979-01-01', 'lte': '1979-12-30'}
    assert makeDateRangeValue(
        '1979-01-01', '1979-01-01')=={'gte': '1979-01-01', 'lte': '1979-01-01'}
    assert makeDateRangeValue(
        '1979/01/01', '1979/12/30')=={'gte': '1979-01-01', 'lte': '1979-12-30'}
    assert makeDateRangeValue(
        '0000-00-00', '0000-00-00') == None

# def get_value_from_dict(dc, path, path_type, iid=None):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_get_value_from_dict -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_value_from_dict(app, meta, jsonpath):
    assert get_value_from_dict(meta[0], jsonpath[0], 'json')=='寄与者'
    assert get_value_from_dict(meta[0], jsonpath[1], 'json')=='2000-01-01/2021-03-30'
    assert get_value_from_dict(meta[0], jsonpath[2], 'json')=='概要'
    assert get_value_from_dict(meta[0], jsonpath[3], 'json')=='その他'

# def get_values_from_dict(dc, path, path_type, iid=None):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_get_values_from_dict -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_values_from_dict(app, meta, jsonpath):
    assert get_values_from_dict(
        meta[0], jsonpath[0], 'json')==['寄与者', 'Contributor']
    assert get_values_from_dict(
        meta[0], jsonpath[1], 'json')==['2000-01-01/2021-03-30']
    assert get_values_from_dict(
        meta[0], jsonpath[2], 'json')==['概要', 'その他', 'materials: text']
    assert get_values_from_dict(
        meta[0], jsonpath[3], 'json')==['その他', 'materials: text']

# def copy_value_xml_path(dc, xml_path, iid=None):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_copy_value_xml_path -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_copy_value_xml_path(meta):
    res = copy_value_xml_path(meta[0], '')
    assert res==None

# def copy_value_json_path(meta, jsonpath):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_copy_value_json_path -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_copy_value_json_path(meta, jsonpath):
    assert copy_value_json_path(
        meta[0], jsonpath[0])==['寄与者', 'Contributor']
    assert copy_value_json_path(
        meta[0], jsonpath[1])==['2000-01-01/2021-03-30']
    assert copy_value_json_path(
        meta[0], jsonpath[2])==['概要', 'その他', 'materials: text']
    assert copy_value_json_path(
        meta[0], jsonpath[3])==['その他', 'materials: text']

# def copy_values_json_path(meta, jsonpath):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_copy_values_json_path -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_copy_values_json_path(meta, jsonpath):
    assert copy_values_json_path(
        meta[0], jsonpath[0])==['寄与者', 'Contributor']
    assert copy_values_json_path(
        meta[0], jsonpath[1])==['2000-01-01/2021-03-30']
    assert copy_values_json_path(
        meta[0], jsonpath[2])==['概要', 'その他', 'materials: text']
    assert copy_values_json_path(
        meta[0], jsonpath[3])==['その他', 'materials: text']

# def set_timestamp(jrc, created, updated):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_set_timestamp -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_set_timestamp():
    _jrc = {}
    _created = datetime.strptime('2000-01-01', '%Y-%m-%d')
    _updated = datetime.strptime('2000-12-31', '%Y-%m-%d')
    set_timestamp(_jrc, _created, _updated)
    assert _jrc=={'_created': '2000-01-01T00:00:00+00:00', '_updated': '2000-12-31T00:00:00+00:00'}
    set_timestamp(_jrc, None, _updated)
    assert _jrc=={'_created': None, '_updated': '2000-12-31T00:00:00+00:00'}
    set_timestamp(_jrc, _created, None)
    assert _jrc=={'_created': '2000-01-01T00:00:00+00:00', '_updated': None}

# def sort_records(records, form):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_sort_records -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_sort_records():
    _form = [
        {
            'key': 'item_1',
            'title': 'item_1_title',
            'title_i18n': {
                'ja': 'ja_item_1_title',
                'en': 'en_item_1_title'
            }
        },
        {
            'key': 'item_2',
            'title': 'item_2_title',
            'title_i18n': {
                'ja': 'ja_item_2_title',
                'en': 'en_item_2_title'
            }
        }
    ]
    _records1 = {
        '$schema': 'http://nii.co.jp/1',
        'item_2': 'item_2_value',
        'item_1': {'key1': 'value1'}
    }
    _records2 = [
        {
            'item_2': 'item_2_value',
            'item_1': 'item_1_value'
        }
    ]

    res = sort_records(_records1, _form)
    assert res==_records1
    res = sort_records(_records2, _form)
    assert res==_records2

# def sort_op(record, kd, form):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_sort_op -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_sort_op():
    _form = [
        {
            'key': 'item_1',
            'title': 'item_1_title',
            'title_i18n': {
                'ja': 'ja_item_1_title',
                'en': 'en_item_1_title'
            }
        },
        {
            'key': 'item_2',
            'title': 'item_2_title',
            'title_i18n': {
                'ja': 'ja_item_2_title',
                'en': 'en_item_2_title'
            }
        }
    ]
    _record1 = {
        '$schema': 'http://nii.co.jp/1',
        'old_item_1': 'item_1_value'
    }
    _record2 = [
        {
            'item_2': 'item_2_value',
            'item_1': 'item_1_value'
        }
    ]
    _record3 = {
        '$schema': 'http://nii.co.jp/1',
        'old_item_2': {'key2': 'item_2_value'},
        'old_item_1': {'key1': 'item_1_value'}
    }
    _kd = {'item_1': 'old_item_1', 'item_2': 'old_item_2'}

    with pytest.raises(Exception) as e:
        sort_op(_record1, _kd, _form)
    assert e.type==TypeError
    res = sort_op(_record2, _kd, _form)
    assert res==_record2
    res = sort_op(_record3, _kd, _form)
    assert res=={'old_item_2': {'index': 2, 'key2': 'item_2_value'},
    'old_item_1': {'index': 1, 'key1': 'item_1_value'}}

# def find_items(form):
#     def find_key(node):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_find_items -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_find_items():
    _form = [
        {
            'key': 'item_1',
            'title': 'item_1_title',
            'title_i18n': {
                'ja': 'ja_item_1_title',
                'en': 'en_item_1_title'
            }
        }
    ]
    res = find_items(_form)
    assert res==[['item_1', 'item_1_title', 'en_item_1_title', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False, }, '']]


# def get_all_items(nlst, klst, is_get_name=False):
#     def get_name(key):
#     def get_items(nlst):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_get_all_items -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_all_items():
    _nlst = [
        {
            'subitem_1': 'en_value',
            'subitem_1_lang': 'en'
        },
        {
            'subitem_1': 'ja_value',
            'subitem_1_lang': 'ja'
        }
    ]
    _klst = [['item_1.subitem_1', 'item_1_title', 'en_item_1_title', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False, }, ''],
    ['item_1.subitem_1_lang', 'item_1_lang', 'en_item_1_lang', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False, }, '']]

    res = get_all_items(_nlst, _klst)
    assert res==[[{'item_1.subitem_1': 'en_value', 'item_1.subitem_1_lang': 'en'}], [{'item_1.subitem_1': 'ja_value', 'item_1.subitem_1_lang': 'ja'}]]


# def get_all_items2(nlst, klst):
#     def get_items(nlst):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_get_all_items2 -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_all_items2():
    _nlst = [
        {
            'subitem_1': 'en_value',
            'subitem_1_lang': 'en'
        },
        {
            'subitem_1': 'ja_value',
            'subitem_1_lang': 'ja'
        }
    ]
    _klst = [['item_1.subitem_1', 'item_1_title', 'en_item_1_title', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False, }, ''],
    ['item_1.subitem_1_lang', 'item_1_lang', 'en_item_1_lang', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False, }, '']]

    res = get_all_items2(_nlst, _klst)
    assert res==[{'subitem_1': 'en_value'}, {'subitem_1_lang': 'en'},
    {'subitem_1': 'ja_value'}, {'subitem_1_lang': 'ja'}]

# def to_orderdict(alst, klst, is_full_key=False):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_to_orderdict -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_to_orderdict():
    _alst = [
        {
            'subitem_1': 'en_value',
            'subitem_1_lang': 'en'
        },
        {
            'subitem_1': 'ja_value',
            'subitem_1_lang': 'ja'
        }
    ]
    _klst = [['item_1.subitem_1', 'item_1_title', 'en_item_1_title', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False, }, '']]

    to_orderdict(_alst, _klst)
    assert _alst==_alst

# def get_options_and_order_list(item_type_id, ojson=None):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_get_options_and_order_list -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_options_and_order_list(app, db, item_type):
    solst, meta_options = get_options_and_order_list(1)
    assert solst==[]
    assert meta_options=={}

# async def sort_meta_data_by_options(
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_sort_meta_data_by_options -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
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
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_get_keywords_data_load -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_keywords_data_load(app, db, item_type, item_type2):
    res = get_keywords_data_load('')
    assert res==[('test', 1), ('test2', 2)]

# def is_valid_openaire_type(resource_type, communities):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_is_valid_openaire_type -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_is_valid_openaire_type(app, db):
    # need to fix
    with pytest.raises(Exception) as e:
        is_valid_openaire_type({'openaire_subtype': ''}, [])
    assert e.type==NameError
    assert str(e.value)=="name 'current_openaire' is not defined"
    res = is_valid_openaire_type({}, [])
    assert res==True

# def check_has_attribute_value(node):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_check_has_attribute_value -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_check_has_attribute_value(app):
    res = check_has_attribute_value([''])
    assert res==False
    res = check_has_attribute_value({'test': 'v'})
    assert res==True

# def get_attribute_value_all_items(
#     def get_name_mapping():
#     def get_name(key, multi_lang_flag=True):
#     def change_temporal_format(value):
#     def change_date_format(value):
#     def get_value(data):
#     def to_sort_dict(alst, klst):
#     def set_attribute_value(nlst):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_get_attribute_value_all_items -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_attribute_value_all_items(app):
    _nlst = [
        {
            'subitem_1': 'en_value',
            'subitem_1_lang': 'en'
        },
        {
            'subitem_1': 'ja_value',
            'subitem_1_lang': 'ja'
        }
    ]
    _klst = [['item_1.subitem_1', 'item_1_title', 'en_item_1_title', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False, }, ''],
    ['item_1.subitem_1_lang', 'item_1_lang', 'en_item_1_lang', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False, }, '']]

    res = get_attribute_value_all_items('item_1', _nlst, _klst)
    assert res==[[[[{'en_item_1_title': 'en_value'}], [{'en_item_1_lang': 'en'}]]], [[[{'en_item_1_title': 'ja_value'}], [{'en_item_1_lang': 'ja'}]]]]

# def check_input_value(old, new):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_check_input_value -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_check_input_value():
    res = check_input_value({'key': {'input_value': 'same'}}, {'key': {'input_value': 'same'}})
    assert res==False
    res = check_input_value({'key': {'input_value': 'old'}}, {'key': {'input_value': 'new'}})
    assert res==True

# def remove_key(removed_key, item_val):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_remove_key -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_remove_key():
    res = remove_key('key', [])
    assert res==None
    _item_val = {'key1': 'value1', 'key2': 'value2', 'key3': {'key1': 'value1', 'key2': 'value2'}}
    remove_key('key1', _item_val)
    assert _item_val=={'key2': 'value2', 'key3': {'key2': 'value2'}}

# def remove_keys(excluded_keys, item_val):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_remove_keys -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_remove_keys():
    res = remove_keys(['key'], [])
    assert res==None
    _item_val = {'key1': 'value1', 'key2': 'value2', 'key3': {'key1': 'value1', 'key2': 'value2'}}
    remove_keys(['key1', 'key2'], _item_val)
    assert _item_val=={'key3': {}}

# def remove_multiple(schema):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_remove_multiple -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_remove_multiple():
    _schema = {
        'properties': {
            'item_1': {
                'maxItems': 99,
                'minItems': 1,
                'title': 'title_1'
            },
            'item_2': {
                'maxItems': 99,
                'minItems': 1,
                'items': [
                    {
                        'subitem_1': {'title': 'subtitle_1'},
                        'subitem_2': {'title': 'subtitle_2'}
                    }
                ]
            }
        }
    }

    remove_multiple(_schema)
    assert _schema=={'properties': {'item_1': {'title': 'title_1'},
    'item_2': [{'subitem_1': {'title': 'subtitle_1'}, 'subitem_2': {'title': 'subtitle_2'}}]}}

# def check_to_upgrade_version(old_render, new_render):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_check_to_upgrade_version -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_check_to_upgrade_version(app):
    _old_render = {
        'meta_fix': {},
        'meta_list': {},
        'table_row_map': {
            'schema': {
                'properties': {
                    'item_1': {
                        'type': 'string',
                        'title': 'item_1',
                        'format': 'text'
                    }
                }
            }
        },
        'table_row': ['1']
    }
    _new_render = {
        'meta_fix': {},
        'meta_list': {},
        'table_row_map': {
            'schema': {
                'properties': {
                    'item_2': {
                        'type': 'string',
                        'title': 'item_2',
                        'format': 'text'
                    }
                }
            }
        },
        'table_row': ['2']
    }

    res = check_to_upgrade_version(_old_render, _old_render)
    assert res==False
    res = check_to_upgrade_version(_old_render, _new_render)
    assert res==True

# def remove_weko2_special_character(s: str):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_remove_weko2_special_character -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_remove_weko2_special_character():
    assert remove_weko2_special_character("HOGE")=="HOGE"
    assert remove_weko2_special_character("HOGE&EMPTY&HOGE")=="HOGEHOGE"
    assert remove_weko2_special_character("HOGE,&EMPTY&")=="HOGE"
    assert remove_weko2_special_character("&EMPTY&,HOGE")=="HOGE"
    assert remove_weko2_special_character("HOGE,&EMPTY&,HOGE")=="HOGE,,HOGE"

#     def __remove_special_character(_s_str: str):

# def selected_value_by_language(lang_array, value_array, lang_id, val_id, lang_selected, _item_metadata):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_selected_value_by_language -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_selected_value_by_language(app, meta):
    res = selected_value_by_language([], [], '', '', None, {})
    assert res==None
    _lang_id = 'item_1551264308487.subitem_1551255648112'
    _val_id = 'item_1551264308487.subitem_1551255647225'
    res = selected_value_by_language(['ja', 'en'], ['タイトル日本語', 'Title'], _lang_id, _val_id, 'en', meta[0])
    assert res=='Title'
    app.config['WEKO_RECORDS_UI_LANG_DISP_FLG'] = False
    _lang_id = 'item_1551264340087.subitem_1551255898956.subitem_1551255907416'
    _val_id = 'item_1551264340087.subitem_1551255898956.subitem_1551255905565'
    res = selected_value_by_language(['ja'], ['作者'], _lang_id, _val_id, 'en', meta[0])
    assert res=='作者'
    app.config['WEKO_RECORDS_UI_LANG_DISP_FLG'] = True
    res = selected_value_by_language(['en'], ['Creator'], _lang_id, _val_id, 'en', meta[0])
    assert res=='Creator'

# def check_info_in_metadata(str_key_lang, str_key_val, str_lang, metadata):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_check_info_in_metadata -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_check_info_in_metadata(app, meta):
    res = check_info_in_metadata('', '', None, {})
    assert res==None
    _str_key_lang = 'item_1551264308487.subitem_1551255648112'
    _str_key_val = 'item_1551264308487.subitem_1551255647225'
    res = check_info_in_metadata(_str_key_lang, _str_key_val, 'en', meta[0])
    assert res=='Title'
    # need to fix
    #res = check_info_in_metadata(_str_key_lang, _str_key_val, None, meta[0])
    #assert res=='タイトル日本語'
    _str_key_lang = 'item_1551264418667.subitem_1551257245638.subitem_1551257279831'
    _str_key_val = 'item_1551264418667.subitem_1551257245638.subitem_1551257276108'
    res = check_info_in_metadata(_str_key_lang, _str_key_val, 'en', meta[0])
    assert res=='Contributor'

# def get_value_and_lang_by_key(key, data_json, data_result, stt_key):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_get_value_and_lang_by_key -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_value_and_lang_by_key(app):
    _data_json = [
        {
            'key': 'item_1.subitem_1.subitem_2',
            'title': 'Language',
            'title_en': 'Language',
            'title_ja': '言語',
            'value': 'lang1-,-lang2'
        },
        {
            'key': 'item_2.subitem_1.subitem_2',
            'title': 'Title',
            'title_en': 'Title',
            'title_ja': 'タイトル',
            'value': 'title1-,-title2'
        }
    ]
    res = get_value_and_lang_by_key(None, None, None, None)
    assert res==None
    data_result, stt_key = get_value_and_lang_by_key('item_1.subitem_1', _data_json, {}, [])
    assert data_result=={}
    assert stt_key==[]
    data_result, stt_key = get_value_and_lang_by_key('item_1.subitem_1.subitem_2', _data_json, {}, [])
    assert data_result=={
        'item_1.subitem_1': {'lang': ['lang1', 'lang2'], 'lang_id': 'item_1.subitem_1.subitem_2'}}
    assert stt_key==['item_1.subitem_1']
    data_result, stt_key = get_value_and_lang_by_key('item_2.subitem_1.subitem_2', _data_json, data_result, stt_key)
    assert data_result=={
        'item_1.subitem_1': {'lang': ['lang1', 'lang2'], 'lang_id': 'item_1.subitem_1.subitem_2'},
        'item_2.subitem_1': {'item_2.subitem_1.subitem_2': {'value': ['title1', 'title2']},
        'stt': ['item_2.subitem_1.subitem_2']}}
    assert stt_key==['item_1.subitem_1', 'item_2.subitem_1']

# def get_value_by_selected_lang(source_title, current_lang):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_get_value_by_selected_lang -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_value_by_selected_lang(app):
    _source_title1 = {
        'None Language': 'no_lang_test',
        'ja': 'ja_test',
        'en': 'en_test',
        'ja-Latn': 'ja_latn_test',
        'zh': None
    }
    _source_title2 = {
        'None Language': 'no_lang_test',
        'id': 'id_test',
        'en': 'en_test'
    }
    _source_title3 = {
        'None Language': 'no_lang_test',
        'ja': 'ja_test',
        'id': 'id_test'
    }
    _source_title4 = {
        'None Language': 'no_lang_test'
    }

    res = get_value_by_selected_lang({}, 'ja')
    assert res==None
    app.config['WEKO_RECORDS_UI_LANG_DISP_FLG'] = False
    res = get_value_by_selected_lang(_source_title1, 'ja')
    assert res=='ja_test'
    res = get_value_by_selected_lang(_source_title1, 'zh')
    assert res=='ja_latn_test'
    res = get_value_by_selected_lang(_source_title2, 'zh')
    assert res=='en_test'
    res = get_value_by_selected_lang(_source_title2, 'ja')
    assert res=='en_test'
    res = get_value_by_selected_lang(_source_title3, 'en')
    assert res=='ja_test'
    res = get_value_by_selected_lang(_source_title4, 'th')
    assert res=='no_lang_test'
    app.config['WEKO_RECORDS_UI_LANG_DISP_FLG'] = True
    res = get_value_by_selected_lang(_source_title2, 'ja')
    assert res=='id_test'
    res = get_value_by_selected_lang(_source_title3, 'en')
    assert res=='id_test'

# def get_show_list_author(solst_dict_array, hide_email_flag, author_key, creates):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_get_show_list_author -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_show_list_author(i18n_app):
    _solst_dict_array = [
        {
            'key': 'create.creatorNames[].creatorName',
            'option': {
                'show_list': True,
                'hide': False
            },
            'parent_option': {
                'show_list': True,
                'hide': False
            }
        },
        {
            'key': 'create.creatorNames[].creatorNameLang',
            'option': {
                'show_list': False,
                'hide': True
            },
            'parent_option': {
                'show_list': False,
                'hide': True
            }
        },
        {
            'key': 'create.creatorMails[].creatorMail',
            'option': {
                'show_list': True,
                'hide': False
            },
            'parent_option': {
                'show_list': True,
                'hide': False
            }
        },
        {
            'key': 'create.familyNames[].familyName',
            'option': {
                'show_list': True,
                'hide': False
            },
            'parent_option': {
                'show_list': True,
                'hide': False
            }
        },
        {
            'key': 'create.familyNames[].familyNameLang',
            'option': {
                'show_list': False,
                'hide': True
            },
            'parent_option': {
                'show_list': False,
                'hide': True
            }
        }
    ]
    _author_key = 'create'
    _creates = [{
        'creatorNames': [
            {
                'creatorName': 'ja_name',
                'creatorNameLang': 'ja'
            },
            {
                'creatorName': 'en_name',
                'creatorNameLang': 'en'
            },
            {
                'creatorName': 'no_lang_name'
            }
        ],
        'familyNames': [
            {
                'familyName': 'no_lang_fname',
            },
            {
                'familyName': 'en_fname',
                'familyNameLang': 'en'
            }
        ],
        'creatorMails': [{
            'creatorMail': 'nii@mail.co.jp'
        }]
    }]

    res = get_show_list_author(_solst_dict_array, False, _author_key, _creates)
    assert res=={'creatorName': ['en_name'], 'familyName': ['en_fname']}

# def format_creates(creates, hide_creator_keys):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_format_creates -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_format_creates(i18n_app):
    _creates = [{
        'creatorNames': [
            {
                'creatorName': 'ja_name',
                'creatorNameLang': 'ja'
            },
            {
                'creatorName': 'en_name',
                'creatorNameLang': 'en'
            },
            {
                'creatorName': 'no_lang_name'
            }
        ],
        'familyNames': [
            {
                'familyName': 'no_lang_fname',
            },
            {
                'familyName': 'en_fname',
                'familyNameLang': 'en'
            }
        ],
        'creatorAlternatives': [
            {
                'creatorAlternative': 'en_al',
                'al_lang': 'en'
            },
            {
                'creatorAlternative': 'ja_al',
                'al_lang': 'ja'
            }
        ],
        'creatorAffiliations': [{
            'affiliationNames': [
                {
                    'affiliationName': 'en_af',
                    'af_lang': 'en'
                },
                {
                    'affiliationName': 'ja_af',
                    'af_lang': 'ja'
                }
            ]
        }]
    }]
    _hide_creator_keys = ['familyNames']
    
    res = format_creates(_creates, _hide_creator_keys)
    assert res=={'creatorName': ['en_name'], 'affiliationName': ['en_af'], 'creatorAlternative': ['en_al']}

# def get_creator(create, result_end, hide_creator_keys, current_lang):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_get_creator -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_creator(app):
    _create = {
        'creatorNames': [
            {
                'creatorName': 'ja_name',
                'creatorNameLang': 'ja'
            },
            {
                'creatorName': 'en_name',
                'creatorNameLang': 'en'
            },
            {
                'creatorName': 'no_lang_name'
            }
        ],
        'familyNames': [
            {
                'familyName': 'no_lang_fname',
            },
            {
                'familyName': 'en_fname',
                'familyNameLang': 'en'
            }
        ]
    }
    _hide_creator_keys = ['familyNames']
    res = get_creator(_create, {}, _hide_creator_keys, 'en')
    assert res=={'creatorName': ['en_name']}

# def get_creator_by_languages(creates_key, create):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_get_creator_by_languages -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_creator_by_languages(app):
    _creates_key = {
        'item_1': ['subitem_value', 'subitem_lang'],
        'item_2': ['subitem_value', 'subitem_lang']
    }
    _create = {
        'item_1': [
            {
                'subitem_id': 1,
                'subitem_value': 'ja_value_1',
                'subitem_lang': 'ja'
            },
            {
                'subitem_id': 1,
                'subitem_value': 'en_value_1',
                'subitem_lang': 'en'
            },
            {
                'subitem_id': 1,
                'subitem_value': 'no_lang_value_1'
            }
        ],
        'item_2': [
            {
                'subitem_id': 2,
                'subitem_value': 'no_lang_value_2',
            },
            {
                'subitem_id': 2,
                'subitem_value': 'en_value_2',
                'subitem_lang': 'en'
            }
        ],
        'item_3': [
            {
                'subitem_id': 3,
                'subitem_value': 'en',
            },
            {
                'subitem_id': 3,
                'subitem_value': 'en_value_2',
                'subitem_lang': 'en'
            }
        ]
    }
    res = get_creator_by_languages(_creates_key, _create)
    assert res=={
        'ja': {'item_1': 'ja_value_1'},
        'en': {'item_1': 'en_value_1', 'item_2': 'en_value_2'},
        'None Language': {'item_1': 'no_lang_value_1', 'item_2': 'no_lang_value_2'}}

# def get_affiliation(affiliations, result_end, current_lang, affiliation_key):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_get_affiliation -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_affiliation(app):
    _affiliations = [{
        'affiliationNames': [
            {
                'affiliationName': 'en_af',
                'af_lang': 'en'
            },
            {
                'affiliationName': 'ja_af',
                'af_lang': 'ja'
            }
        ]
    }]
    res = get_affiliation(_affiliations, {}, 'en', ['affiliationName', 'af_lang'])
    assert res=={'affiliationName': ['en_af']}
    res = get_affiliation(_affiliations, {}, 'en', ['affiliationName2', 'af_lang'])
    assert res=={}

# def get_author_has_language(creator, result_end, current_lang, map_keys):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_get_author_has_language -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_author_has_language(app):
    _create = [
        {
            'affiliationName': 'en_af',
            'af_lang': 'en'
        },
        {
            'affiliationName': 'ja_af',
            'af_lang': 'ja'
        }
    ]
    res = get_author_has_language(_create, {}, 'en', ['affiliationName', 'af_lang'])
    assert res=={'affiliationName': ['en_af']}
    
    res = get_author_has_language(_create, {}, 'fr', ['affiliationName', 'af_lang'])
    assert res=={'affiliationName': ['en_af']}
    
    res = get_author_has_language(_create, {}, 'en', ['affiliationName', 'af_lang2'])
    assert res=={'affiliationName': ['en_af']}
    
    res = get_author_has_language(_create, {}, 'en', ['affiliationName2', 'af_lang2'])
    assert res=={}

# def add_author(author_data, stt_key, is_specify_newline_array, s, value, data_result, is_specify_newline, is_hide, is_show_list):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_add_author -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_add_author(app):
    _data = {'creatorName': 'test1'}
    _s1 = {'key': 'item_1.names[].creatorName'}
    _s2 = {'key': 'item_1.ids[].nameIdentifier'}
    
    stt_key, data_result, newline_array = add_author(_data, [], [], _s1, 'value1', {}, False, False, True)
    assert stt_key==['creatorName']
    assert data_result=={'creatorName': {'creatorName': {'value': 'test1'}}}
    assert newline_array==[{'creatorName': False}]
    stt_key, data_result, newline_array = add_author(_data, [], [], _s2, 'value1', {}, True, False, True)
    assert stt_key==['nameIdentifier']
    assert data_result=={'nameIdentifier': {'nameIdentifier': {'value': ['value1']}}}
    assert newline_array==[{'nameIdentifier': True}]

# def convert_bibliographic(data_sys_bibliographic):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_convert_bibliographic -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_convert_bibliographic():
    _biblio = [
        {
            'title_attribute_name': 'title1',
            'magazine_attribute_name': [
                {'key': 'name1'},
                {'key': 'name2'}
            ]
        },
        {
            'title_attribute_name': 'title2',
            'magazine_attribute_name': [
                {'key': 'name3'}
            ]
        }
    ]

    res = convert_bibliographic(_biblio)
    assert res=='title1, key name1, key name2, title2, key name3'
    _biblio2 = [
        {
            'magazine_attribute_name': [
                {'key': 'name1'},
                {'key': 'name2'}
            ]
        },
        {
            'magazine_attribute_name': [
                {'key': 'name3'}
            ]
        }
    ]

    res2 = convert_bibliographic(_biblio2)
    assert res2=='key name1, key name2, key name3'


# def add_biographic(sys_bibliographic, bibliographic_key, s, stt_key, data_result, 

# def custom_record_medata_for_export(record_metadata: dict):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_custom_record_medata_for_export -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_custom_record_medata_for_export(app, db, item_type):
    with app.app_context():
        user = testutils.create_test_user('test@example.org')
        with patch("flask_login.utils._get_user", return_value=user):
            meta = custom_record_medata_for_export({'item_type_id': 1, '_oai': {}})
            assert meta==None

# def replace_fqdn(url_path: str, host_url: str = None):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_replace_fqdn -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_replace_fqdn(app):
    assert app.config.get("THEME_SITEURL")=='https://localhost'
    url = replace_fqdn('http://test/a')
    assert url=='https://localhost/a'
    url = replace_fqdn('http://localhost/a')
    assert url=='https://localhost/a'
    url = replace_fqdn('http://test/a', 'https://nii.co.jp/')
    assert url=='https://nii.co.jp/a'
    url = replace_fqdn('http://weko3.ir.rcos.nii.ac.jp/a', 'https://weko3.ir.rcos.nii.co.jp/')
    assert url=='https://weko3.ir.rcos.nii.co.jp/a'
    url = replace_fqdn('http://weko3.ir.rcos.nii.ac.jp/a', 'https://weko3.ir.rcos.nii.co.jp')
    assert url=='https://weko3.ir.rcos.nii.co.jp/a'


# def replace_fqdn_of_file_metadata(file_metadata_lst: list, file_url: list = None):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_replace_fqdn_of_file_metadata -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_replace_fqdn_of_file_metadata(app):
    _file_metadata_list1 = [
        {
            'url': {'url': 'http://test/a'}
        },
        {
            'url': {'url': 'http://test/b'}
        }
    ]
    _file_metadata_list2 = [
        {
            'url': {'url': 'http://test/a'},
            'version_id': '1'
        },
        {
            'url': {'url': 'http://test/b'},
            'version_id': '1'
        }
    ]
    
    _file_url = []
    replace_fqdn_of_file_metadata(_file_metadata_list1)
    assert _file_metadata_list1==[{'url': {'url': 'http://test/a'}}, {'url': {'url': 'http://test/b'}}]
    replace_fqdn_of_file_metadata(_file_metadata_list1, _file_url)
    assert _file_url==['http://test/a', 'http://test/b']
    replace_fqdn_of_file_metadata(_file_metadata_list2)
    assert _file_metadata_list2==[{'url': {'url': 'https://localhost/a'}, 'version_id': '1'}, {'url': {'url': 'https://localhost/b'}, 'version_id': '1'}]
    