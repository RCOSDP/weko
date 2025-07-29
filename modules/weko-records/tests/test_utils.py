# -*- coding: utf-8 -*-

from collections import OrderedDict
from datetime import datetime
import json
# from tkinter import W
import pytest
import os
import copy
import mock
from mock import patch, MagicMock
from tests.helpers import json_data

from invenio_accounts import testutils
from invenio_i18n.ext import current_i18n
from weko_admin.models import AdminSettings, SearchManagement
from weko_records.utils import (
    json_loader,
    copy_field_test,
    convert_range_value,
    convert_date_range_value,
    makeDateRangeValue,
    get_value_from_dict,
    get_values_from_dict,
    get_values_from_dict_with_condition,
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
    replace_fqdn_of_file_metadata,
    get_author_link,
    set_file_date)
from weko_records.api import ItemTypes, Mapping
from weko_records.models import ItemTypeName
from weko_workflow.models import Activity

# def json_loader(data, pid, owner_id=None):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_json_loader -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_json_loader(app, db, item_type, item_type2, item_type_mapping2, db_register, records, users, mocker):
    from weko_admin.config import WEKO_ADMIN_MANAGEMENT_OPTIONS

    item_type_scheme={"properties":{"control_number":{"type":"string"},"item_1":{"title":"item_1","type":"string"},"item_2":{"title":"item_2","type":"string"},"item_3":{"title":"item_3","type":"object","properties":{"item_3_1":{"title":"item_3_1","type":"string"},"iscreator":{"type":"string"}}},"item_4":{"title":"item_4","type":"object","properties":{"item_4_1":{"title":"item_4_1","type":"string"}}},"item_5":{"title":"item_5","type":"array","items":{"properties":{"filename":{"type":"string","title":"filename"},"iscreator":{"type":"string"}}},},"item_6":{"title":"item_6","type":"array","items":{"properties":{"item_6_1":{"title":"item_6_1","type":"string"}}},},"item_7":{"title":"item_7","type":"array","items":{"properties":{"nameIdentifiers":{"type":"array","items":{"properties":{"nameIdentifier":{"title":"name identifier","type":"string"},"nameIdentifierScheme":{"title":"name identifier scheme","type":"string"}}}}}}},"item_8":{"title":"item_8","type": "object","properties":{"nameIdentifiers":{"type":"array","items":{"properties":{"nameIdentifier":{"title":"name identifier","type":"string"},"nameIdentifierScheme":{"title":"name identifier scheme","type":"string"}}}}}}}}
    item_type_mapping = {"control_number":{},"item_1":{"jpcoar_mapping":""},"item_2":{"jpcoar_mapping":""},"item_3":{"jpcoar_mapping":{"item_3":{"@value":"item_3_1"}}},"item_4":{"jpcoar_mapping":{"item_4":{"@value":"item_4_1"}}},"item_5":{"jpcoar_mapping":{"item_5":{"@value":"filename"}}},"item_6":{"jpcoar_mapping":{"item_6":{"@value":"item_6_1"}}},"item_7":{"jpcoar_mapping":{"creator1":{"nameIdentifier":{"@value":"nameIdentifiers.nameIdentifier","@attributes":{"nameIdentifierScheme":"nameIdentifiers.nameIdentifierScheme"}}}}},"item_8":{"jpcoar_mapping":{"creator1":{"nameIdentifier":{"@value":"nameIdentifiers.nameIdentifier","@attributes":{"nameIdentifierScheme":"nameIdentifiers.nameIdentifierScheme"}}}}}}
    _pid = records[0][0]
    _pid2 = records[1][0]
    mocker.patch("weko_authors.api.WekoAuthors.get_pk_id_by_weko_id", return_value="2")
    mocker.patch("weko_authors.utils.update_data_for_weko_link")
    # not exist $schema
    data1={}
    result = json_loader(data1, _pid)
    assert result==None

    # not exist scheme, mapping
    data2={
        '$schema': 'http://schema/1/A-test'
    }
    with pytest.raises(Exception) as e:
        json_loader(data2, _pid)
    assert e.type==RuntimeError
    assert str(e.value)=="Item Type 1 does not exist."


    ItemTypes.create(
        name='test10',
        item_type_name=ItemTypeName(name='test10'),
        schema=item_type_scheme,
        render={},
        tag=1
    )
    class MockMapping:
        def dumps(self):
            return item_type_mapping
    mocker.patch("weko_records.utils.Mapping.get_record",return_value=MockMapping())


    # weko_shared_id!=-1, shared_user_id=-1, exist control_number
    data3={
        '$schema': 'http://schema/3',
        "pubdate":"2023-08-08",
        "title":"test_item1",
        "control_number":1,
        "weko_creator_id":1,
        "owner":"1",
        "weko_shared_ids":[1],
        "shared_user_ids":[],
        "item_1":"item_1_v",
        "item_2":"",
        "item_3":{"item_3_1":"item_3_1_v"},
        "item_4":{"item_4_1":"item_4_1_v"},
        "item_5":[{"filename":"item_5"}],
        "item_6":[{}],
        "item_7":[{},{"nameIdentifiers":[{"nameIdentifierScheme":"WEKO","nameIdentifier":"1234"}]}],
        "item_8":{"nameIdentifiers":[{"nameIdentifierScheme":"WEKO","nameIdentifier":"5678"}]}
    }
    app.config['WEKO_SCHEMA_JPCOAR_V1_SCHEMA_NAME'] = 'jpcoar_v1_mapping'
    app.config['WEKO_SCHEMA_DDI_SCHEMA_NAME'] = 'ddi_mapping'
    dc, jrc, is_edit = json_loader(data3,_pid)
    assert dc == OrderedDict([('item_1', {'attribute_name': 'item_1', 'attribute_value': 'item_1_v'}), ('item_2', {'attribute_name': 'item_2', 'attribute_value': ''}), ('item_3', {'attribute_name': 'item_3', 'attribute_type': 'creator', 'attribute_value_mlt': [{'item_3_1': 'item_3_1_v'}]}), ('item_4', {'attribute_name': 'item_4', 'attribute_value_mlt': [{'item_4_1': 'item_4_1_v'}]}), ('item_5', {'attribute_name': 'item_5', 'attribute_type': 'file', 'attribute_value_mlt': [{'filename': 'item_5'}]}), ('item_6', {'attribute_name': 'item_6', 'attribute_value_mlt': [{}]}), ('item_7', {'attribute_name': 'item_7', 'attribute_value_mlt': [{}, {'nameIdentifiers': [{'nameIdentifierScheme': 'WEKO', 'nameIdentifier': '1234'}]}]}), ('item_8', {'attribute_name': 'item_8', 'attribute_value_mlt': [{'nameIdentifiers': [{'nameIdentifierScheme': 'WEKO', 'nameIdentifier': '5678'}]}]}), ('item_title', 'test_item1'), ('item_type_id', '3'), ('control_number', '1'), 
                        ('author_link', ['2', '2']),("weko_link", {"2": "5678"}), ('weko_shared_ids', []), ('_oai', {'id': '1'}), ('owner', 1), ('owners', [1])])
    assert jrc == {'item_4': ['item_4_1_v'], 'creator1': {'nameIdentifier': ['1234', '5678']}, 'item_5': ['item_5'], 'item_3': ['item_3_1_v'], 'control_number': '1', '_oai': {'id': '1'}, '_item_metadata': OrderedDict([('item_1', {'attribute_name': 'item_1', 'attribute_value': 'item_1_v'}), ('item_2', {'attribute_name': 'item_2', 'attribute_value': ''}), ('item_3', {'attribute_name': 'item_3', 'attribute_type': 'creator', 'attribute_value_mlt': [{'item_3_1': 'item_3_1_v'}]}), ('item_4', {'attribute_name': 'item_4', 'attribute_value_mlt': [{'item_4_1': 'item_4_1_v'}]}), ('item_5', {'attribute_name': 'item_5', 'attribute_type': 'file', 'attribute_value_mlt': [{'filename': 'item_5'}]}), ('item_6', {'attribute_name': 'item_6', 'attribute_value_mlt': [{}]}), ('item_7', {'attribute_name': 'item_7', 'attribute_value_mlt': [{}, {'nameIdentifiers': [{'nameIdentifierScheme': 'WEKO', 'nameIdentifier': '1234'}]}]}), ('item_8', {'attribute_name': 'item_8', 'attribute_value_mlt': [{'nameIdentifiers': [{'nameIdentifierScheme': 'WEKO', 'nameIdentifier': '5678'}]}]}), ('item_title', 'test_item1'), ('item_type_id', '3'), ('control_number', '1'),
                        ('author_link', ['2', '2']),("weko_link", {"2": "5678"}), ('weko_shared_ids', []), ('_oai', {'id': '1'}), ('owner', 1), ('owners', [1])]), 'itemtype': 'test10', 'publish_date': None,
                        'author_link': ['2', '2'], "weko_link": {"2": "5678"}, 'weko_creator_id': '1', 'weko_shared_ids': []}
    assert is_edit == False


    # weko_shared_id!=-1, shared_user_id!=-1, sm.get is not none
    class MockSM:
        search_conditions=WEKO_ADMIN_MANAGEMENT_OPTIONS
    with patch("weko_records.utils.sm.get",return_value=MockSM()):
        data4={
            '$schema': 'http://schema/3',
            "pubdate":"2023-08-08",
            "title":"test_item2",
            "weko_shared_ids":[1],
            "shared_user_ids":[2],
            "item_1":"item_1_v",
            "item_2":"item_2_v",
            "item_3":{"item_3_1":"item_3_1_v"},
            "item_4":{"item_4_1":"item_4_1_v"},
            "item_5":[{"filename":"item_5"}],
            "item_6":[{"item_6_1":"item_6_1_v"}],
            "item_7":[{},{"nameIdentifiers":[{"nameIdentifierScheme":"WEKO","nameIdentifier":"1234"}]}],
            "item_8":{"nameIdentifiers":[{"nameIdentifierScheme":"WEKO","nameIdentifier":"5678"}]}
        }
        dc, jrc, is_edit = json_loader(data4,_pid)
        assert dc == OrderedDict([('item_1', {'attribute_name': 'item_1', 'attribute_value': 'item_1_v'}), ('item_2', {'attribute_name': 'item_2', 'attribute_value': 'item_2_v'}), ('item_3', {'attribute_name': 'item_3', 'attribute_type': 'creator', 'attribute_value_mlt': [{'item_3_1': 'item_3_1_v'}]}), ('item_4', {'attribute_name': 'item_4', 'attribute_value_mlt': [{'item_4_1': 'item_4_1_v'}]}), ('item_5', {'attribute_name': 'item_5', 'attribute_type': 'file', 'attribute_value_mlt': [{'filename': 'item_5'}]}), ('item_6', {'attribute_name': 'item_6', 'attribute_value_mlt': [{'item_6_1': 'item_6_1_v'}]}), ('item_7', {'attribute_name': 'item_7', 'attribute_value_mlt': [{}, {'nameIdentifiers': [{'nameIdentifierScheme': 'WEKO', 'nameIdentifier': '1234'}]}]}), ('item_8', {'attribute_name': 'item_8', 'attribute_value_mlt': [{'nameIdentifiers': [{'nameIdentifierScheme': 'WEKO', 'nameIdentifier': '5678'}]}]}), ('item_title', 'test_item2'), ('item_type_id', '3'), ('control_number', '1'),
                                ('author_link', ['2', '2']),("weko_link", {"2": "5678"}), ('weko_shared_ids', [2]), ('owner', 1), ('owners', [1])])
        assert jrc == {'item_6': ['item_6_1_v'], 'item_5': ['item_5'], 'creator1': {'nameIdentifier': ['1234', '5678']}, 'item_3': ['item_3_1_v'], 'item_4': ['item_4_1_v'], 'control_number': '1', '_oai': {'id': '1'}, '_item_metadata': OrderedDict([('item_1', {'attribute_name': 'item_1', 'attribute_value': 'item_1_v'}), ('item_2', {'attribute_name': 'item_2', 'attribute_value': 'item_2_v'}), ('item_3', {'attribute_name': 'item_3', 'attribute_type': 'creator', 'attribute_value_mlt': [{'item_3_1': 'item_3_1_v'}]}), ('item_4', {'attribute_name': 'item_4', 'attribute_value_mlt': [{'item_4_1': 'item_4_1_v'}]}), ('item_5', {'attribute_name': 'item_5', 'attribute_type': 'file', 'attribute_value_mlt': [{'filename': 'item_5'}]}), ('item_6', {'attribute_name': 'item_6', 'attribute_value_mlt': [{'item_6_1': 'item_6_1_v'}]}), ('item_7', {'attribute_name': 'item_7', 'attribute_value_mlt': [{}, {'nameIdentifiers': [{'nameIdentifierScheme': 'WEKO', 'nameIdentifier': '1234'}]}]}), ('item_8', {'attribute_name': 'item_8', 'attribute_value_mlt': [{'nameIdentifiers': [{'nameIdentifierScheme': 'WEKO', 'nameIdentifier': '5678'}]}]}), ('item_title', 'test_item2'), ('item_type_id', '3'), ('control_number', '1'),
                    ('author_link', ['2', '2']), ("weko_link" ,{"2": "5678"}), ('weko_shared_ids', [2]), ('owner', 1), ('owners', [1])]), 'itemtype': 'test10', 'publish_date': None,
                    'author_link': ['2', '2'], "weko_link" :{"2": "5678"}, 'weko_creator_id': '1', 'weko_shared_ids': [2]}
        assert is_edit == True
    with patch("weko_records.utils.COPY_NEW_FIELD",False):
        with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
            data5={
                '$schema': 'http://schema/3',
                "pubdate":"2023-08-08",
                "title":"test_item2",
                "shared_user_ids":[2],
                "item_1":"item_1_v",
                "item_2":"item_2_v",
                "item_3":{"item_3_1":"item_3_1_v"},
                "item_4":{"item_4_1":"item_4_1_v"},
                "item_5":[{"filename":"item_5"}],
                "item_6":[{"item_6_1":"item_6_1_v"}],
                "item_7":[{},{"nameIdentifiers":[{"nameIdentifierScheme":"WEKO","nameIdentifier":"1234"}]}],
                "item_8":{"nameIdentifiers":[{"nameIdentifierScheme":"WEKO","nameIdentifier":"5678"}]}
            }
            dc, jrc, is_edit = json_loader(data5, _pid)
            assert dc == OrderedDict([('item_1', {'attribute_name': 'item_1', 'attribute_value': 'item_1_v'}), ('item_2', {'attribute_name': 'item_2', 'attribute_value': 'item_2_v'}), ('item_3', {'attribute_name': 'item_3', 'attribute_type': 'creator', 'attribute_value_mlt': [{'item_3_1': 'item_3_1_v'}]}), ('item_4', {'attribute_name': 'item_4', 'attribute_value_mlt': [{'item_4_1': 'item_4_1_v'}]}), ('item_5', {'attribute_name': 'item_5', 'attribute_type': 'file', 'attribute_value_mlt': [{'filename': 'item_5'}]}), ('item_6', {'attribute_name': 'item_6', 'attribute_value_mlt': [{'item_6_1': 'item_6_1_v'}]}), ('item_7', {'attribute_name': 'item_7', 'attribute_value_mlt': [{}, {'nameIdentifiers': [{'nameIdentifierScheme': 'WEKO', 'nameIdentifier': '1234'}]}]}), ('item_8', {'attribute_name': 'item_8', 'attribute_value_mlt': [{'nameIdentifiers': [{'nameIdentifierScheme': 'WEKO', 'nameIdentifier': '5678'}]}]}), ('item_title', 'test_item2'), ('item_type_id', '3'), ('control_number', '1'),
                                    ('author_link', ['2', '2']),("weko_link", {"2": "5678"}), ('weko_shared_ids', [2]), ('owner', 2), ('owners', [2])])
            assert jrc == {'item_5': ['item_5'], 'item_4': ['item_4_1_v'], 'creator1': {'nameIdentifier': ['1234', '5678']}, 'item_6': ['item_6_1_v'], 'item_3': ['item_3_1_v'], 'control_number': '1', '_oai': {'id': '1'}, '_item_metadata': 
                OrderedDict([('item_1', {'attribute_name': 'item_1', 'attribute_value': 'item_1_v'}), 
                            ('item_2', {'attribute_name': 'item_2', 'attribute_value': 'item_2_v'}), 
                            ('item_3', {'attribute_name': 'item_3', 'attribute_type': 'creator', 'attribute_value_mlt': [{'item_3_1': 'item_3_1_v'}]}),
                            ('item_4', {'attribute_name': 'item_4', 'attribute_value_mlt': [{'item_4_1': 'item_4_1_v'}]}), 
                            ('item_5', {'attribute_name': 'item_5', 'attribute_type': 'file', 'attribute_value_mlt': [{'filename': 'item_5'}]}), 
                            ('item_6', {'attribute_name': 'item_6', 'attribute_value_mlt': [{'item_6_1': 'item_6_1_v'}]}), 
                            ('item_7', {'attribute_name': 'item_7', 'attribute_value_mlt': [{}, {'nameIdentifiers': [{'nameIdentifierScheme': 'WEKO', 'nameIdentifier': '1234'}]}]}), 
                            ('item_8', {'attribute_name': 'item_8', 'attribute_value_mlt': [{'nameIdentifiers': [{'nameIdentifierScheme': 'WEKO', 'nameIdentifier': '5678'}]}]}),
                            ('item_title', 'test_item2'), ('item_type_id', '3'), ('control_number', '1'), 
                            ('author_link', ['2', '2']),("weko_link", {"2": "5678"}), ('weko_shared_ids', [2]), ('owner', 2), ('owners', [2])]),
                            'itemtype': 'test10', 'publish_date': None, 
                            'author_link': ['2', '2'], "weko_link": {"2": "5678"}, 'weko_creator_id': '5', 'weko_shared_ids': [2]}
            assert is_edit == True
            
    with patch("weko_records.utils.COPY_NEW_FIELD",False):
        with patch("flask_login.utils._get_user", return_value=None):
            # jrc = {"weko_creator_id":"1", 'item_5': ['item_5'], 'item_6': ['item_6_1_v'], 'item_3': ['item_3_1_v'], 'item_4': ['item_4_1_v'], 'creator1': {'nameIdentifier': ['1234', '5678']}}
            # # with patch("weko_schema_ui.schema.SchemaTree.get_jpcoar_json", return_value=jrc):
            data6={
                '$schema': 'http://schema/3',
                "pubdate":"2023-08-08",
                "title":"test_item2",
                "weko_shared_id":2,
                "item_1":"item_1_v",
                "item_2":"item_2_v",
                "item_3":{"item_3_1":"item_3_1_v"},
                "item_4":{"item_4_1":"item_4_1_v"},
                "item_5":[{"filename":"item_5"}],
                "item_6":["item_6_1","item_6_1_v"],
                "item_7":[{},{"nameIdentifiers":[{"nameIdentifierScheme":"WEKO","nameIdentifier":"1234"}]}],
                "item_8":{"nameIdentifiers":[{"nameIdentifierScheme":"WEKO","nameIdentifier":"5678"}]},
            }
            dc, jrc, is_edit = json_loader(data6, _pid)
            assert dc == OrderedDict([('pubdate', {'attribute_name': 'Publish Date', 'attribute_value': '2023-08-08'}), ('item_1', {'attribute_name': 'item_1', 'attribute_value': 'item_1_v'}), ('item_2', {'attribute_name': 'item_2', 'attribute_value': 'item_2_v'}), ('item_3', {'attribute_name': 'item_3', 'attribute_type': 'creator', 'attribute_value_mlt': [{'item_3_1': 'item_3_1_v'}]}), ('item_4', {'attribute_name': 'item_4', 'attribute_value_mlt': [{'item_4_1': 'item_4_1_v'}]}), ('item_5', {'attribute_name': 'item_5', 'attribute_type': 'file', 'attribute_value_mlt': [{'filename': 'item_5'}]}), ('item_6', {'attribute_name': 'item_6', 'attribute_value': ["item_6_1","item_6_1_v"]}), ('item_7', {'attribute_name': 'item_7', 'attribute_value_mlt': [{}, {'nameIdentifiers': [{'nameIdentifierScheme': 'WEKO', 'nameIdentifier': '1234'}]}]}), ('item_8', {'attribute_name': 'item_8', 'attribute_value_mlt': [{'nameIdentifiers': [{'nameIdentifierScheme': 'WEKO', 'nameIdentifier': '5678'}]}]}), ('item_title', 'test_item2'), ('item_type_id', '3'), ('control_number', '1'),
                                    ('author_link', ['2', '2']),("weko_link", {"2": "5678"}), ('weko_shared_id', 2), ('owner', '1')])
            assert jrc == {'item_5': ['item_5'], 'item_4': ['item_4_1_v'], 'creator1': {'nameIdentifier': ['1234', '5678']}, 'item_6': ["item_6_1",'item_6_1_v'], 'item_3': ['item_3_1_v'], 'control_number': '1', '_oai': {'id': '1'}, '_item_metadata': 
                OrderedDict([('pubdate', {'attribute_name': 'Publish Date', 'attribute_value': '2023-08-08'}), 
                            ('item_1', {'attribute_name': 'item_1', 'attribute_value': 'item_1_v'}), 
                            ('item_2', {'attribute_name': 'item_2', 'attribute_value': 'item_2_v'}), 
                            ('item_3', {'attribute_name': 'item_3', 'attribute_type': 'creator', 'attribute_value_mlt': [{'item_3_1': 'item_3_1_v'}]}),
                            ('item_4', {'attribute_name': 'item_4', 'attribute_value_mlt': [{'item_4_1': 'item_4_1_v'}]}), 
                            ('item_5', {'attribute_name': 'item_5', 'attribute_type': 'file', 'attribute_value_mlt': [{'filename': 'item_5'}]}), 
                            ('item_6', {'attribute_name': 'item_6', 'attribute_value':["item_6_1","item_6_1_v"]}), 
                            ('item_7', {'attribute_name': 'item_7', 'attribute_value_mlt': [{}, {'nameIdentifiers': [{'nameIdentifierScheme': 'WEKO', 'nameIdentifier': '1234'}]}]}), 
                            ('item_8', {'attribute_name': 'item_8', 'attribute_value_mlt': [{'nameIdentifiers': [{'nameIdentifierScheme': 'WEKO', 'nameIdentifier': '5678'}]}]}),
                            ('item_title', 'test_item2'), ('item_type_id', '3'), ('control_number', '1'), 
                            ('author_link', ['2', '2']),("weko_link", {"2": "5678"}), ('weko_shared_id', 2), ('owner', '1')]),
                            'itemtype': 'test10', 'publish_date': '2023-08-08', 
                            'author_link': ['2', '2'], "weko_link": {"2": "5678"}, 'weko_creator_id': '1', 'weko_shared_id': 2}
            assert is_edit == True
    with patch("weko_records.utils.COPY_NEW_FIELD",False):
        with patch("flask_login.utils._get_user", return_value=users[7]["obj"]):
            with patch("flask_login.UserMixin.get_id", return_value=1):
                jrc = {"weko_creator_id":"1", 'item_5': ['item_5'], 'item_6': ['item_6_1_v'], 'item_3': ['item_3_1_v'],
                    'item_4': ['item_4_1_v'], 'creator1': {'nameIdentifier': ['1234', '5678']}}
                with patch("weko_schema_ui.schema.SchemaTree.get_jpcoar_json", return_value=jrc):
                    data={
                        '$schema': 'http://schema/3',
                        "pubdate":"2023-08-08",
                        "title":"test_item2",
                        "weko_shared_id":2,
                        "item_1":"item_1_v",
                        "item_2":"item_2_v",
                        "item_3":{"item_3_1":"item_3_1_v"},
                        "item_4":{"item_4_1":"item_4_1_v"},
                        "item_5":[{"filename":"item_5"}],
                        "item_6":["item_6_1","item_6_1_v"],
                        "item_7":[{},{"nameIdentifiers":[{"nameIdentifierScheme":"WEKO","nameIdentifier":"1234"}]}],
                        "item_8":{"nameIdentifiers":[{"nameIdentifierScheme":"WEKO","nameIdentifier":"5678"}]},
                    }
                    dc, jrc, is_edit = json_loader(data, _pid)
                    assert dc == OrderedDict([('pubdate', {'attribute_name': 'Publish Date', 'attribute_value': '2023-08-08'}), ('item_1', {'attribute_name': 'item_1', 'attribute_value': 'item_1_v'}), ('item_2', {'attribute_name': 'item_2', 'attribute_value': 'item_2_v'}), ('item_3', {'attribute_name': 'item_3', 'attribute_type': 'creator', 'attribute_value_mlt': [{'item_3_1': 'item_3_1_v'}]}), ('item_4', {'attribute_name': 'item_4', 'attribute_value_mlt': [{'item_4_1': 'item_4_1_v'}]}), ('item_5', {'attribute_name': 'item_5', 'attribute_type': 'file', 'attribute_value_mlt': [{'filename': 'item_5'}]}), ('item_6', {'attribute_name': 'item_6', 'attribute_value': ["item_6_1","item_6_1_v"]}), ('item_7', {'attribute_name': 'item_7', 'attribute_value_mlt': [{}, {'nameIdentifiers': [{'nameIdentifierScheme': 'WEKO', 'nameIdentifier': '1234'}]}]}), ('item_8', {'attribute_name': 'item_8', 'attribute_value_mlt': [{'nameIdentifiers': [{'nameIdentifierScheme': 'WEKO', 'nameIdentifier': '5678'}]}]}), ('item_title', 'test_item2'), ('item_type_id', '3'), ('control_number', '1'),
                                            ('author_link', ['2', '2']),("weko_link", {"2": "5678"}), ('weko_shared_id', 2), ('owner', 1)])
                    assert jrc == {'item_5': ['item_5'], 'item_4': ['item_4_1_v'], 'creator1': {'nameIdentifier': ['1234', '5678']}, 'item_6': ['item_6_1_v'], 'item_3': ['item_3_1_v'], 'control_number': '1', '_oai': {'id': '1'}, '_item_metadata': 
                        OrderedDict([('pubdate', {'attribute_name': 'Publish Date', 'attribute_value': '2023-08-08'}), 
                                    ('item_1', {'attribute_name': 'item_1', 'attribute_value': 'item_1_v'}), 
                                    ('item_2', {'attribute_name': 'item_2', 'attribute_value': 'item_2_v'}), 
                                    ('item_3', {'attribute_name': 'item_3', 'attribute_type': 'creator', 'attribute_value_mlt': [{'item_3_1': 'item_3_1_v'}]}),
                                    ('item_4', {'attribute_name': 'item_4', 'attribute_value_mlt': [{'item_4_1': 'item_4_1_v'}]}), 
                                    ('item_5', {'attribute_name': 'item_5', 'attribute_type': 'file', 'attribute_value_mlt': [{'filename': 'item_5'}]}), 
                                    ('item_6', {'attribute_name': 'item_6', 'attribute_value':["item_6_1","item_6_1_v"]}), 
                                    ('item_7', {'attribute_name': 'item_7', 'attribute_value_mlt': [{}, {'nameIdentifiers': [{'nameIdentifierScheme': 'WEKO', 'nameIdentifier': '1234'}]}]}), 
                                    ('item_8', {'attribute_name': 'item_8', 'attribute_value_mlt': [{'nameIdentifiers': [{'nameIdentifierScheme': 'WEKO', 'nameIdentifier': '5678'}]}]}),
                                    ('item_title', 'test_item2'), ('item_type_id', '3'), ('control_number', '1'), 
                                    ('author_link', ['2', '2']),("weko_link", {"2": "5678"}),  ('weko_shared_id', 2), ('owner', 1)]),
                                    'itemtype': 'test10', 'publish_date': '2023-08-08', 
                                    'author_link': ['2', '2'], "weko_link": {"2": "5678"},  'weko_shared_id': 2 ,'weko_creator_id': '1'}
                    assert is_edit == True
                    data={
                        '$schema': 'http://schema/3',
                        "owner":"1",
                        "pubdate":"2023-08-08",
                        "title":"test_item2",
                        "weko_shared_id":2,
                        "shared_user_id":2,
                        "item_1":"item_1_v",
                        "item_2":"item_2_v",
                        "item_3":{"item_3_1":"item_3_1_v"},
                        "item_4":{"item_4_1":"item_4_1_v"},
                        "item_5":[{"filename":"item_5"}],
                        "item_6":["item_6_1","item_6_1_v"],
                        "item_7":[{},{"nameIdentifiers":[{"nameIdentifierScheme":"WEKO","nameIdentifier":"1234"}]}],
                        "item_8":{"nameIdentifiers":[{"nameIdentifierScheme":"WEKO","nameIdentifier":"5678"}]},
                    }
                    with patch("weko_authors.utils.update_data_for_weko_link") as update_data_for_weko_link:
                        
                        dc, jrc, is_edit = json_loader(data, _pid)
                        assert is_edit == True
                        with patch("weko_authors.api.WekoAuthors.get_pk_id_by_weko_id", return_value="-1"):
                            dc, jrc, is_edit = json_loader(data, _pid)
                            assert is_edit == True
                        dc, jrc, is_edit = json_loader(data, _pid2)
                        assert is_edit == False
                        update_data_for_weko_link.assert_not_called()


# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_json_loader2 -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_json_loader2(app, db, users, item_type, item_type2, item_type3, item_type_mapping2, item_type_mapping3, records):
    _data1 = {}
    _data2 = {
        '$schema': 'http://schema/1/A-test'
    }
    _data3 = records[0][1]
    _data3['$schema'] = 'http://schema/2'
    _pid = records[0][0]

    _data4 = records[4][1]
    _data4['$schema'] = 'http://schema/2'

    _data5 = records[5][1]
    _data5['$schema'] = 'http://schema/2'

    _data6 = records[6][1]
    _data6['$schema'] = 'http://schema/2'

    _data7 = records[7][1]
    _data7['$schema'] = 'http://schema/2'

    _data8 = records[4][1]
    _data8['$schema'] = 'http://schema/2'
    _data8['author_link'] = ["4"]
    _data8['item_1'] = [{
        "attribute_name": "item_1",
        "attribute_value": "Item"
      }]
    
    _data9 = records[8][1]
    _data9['$schema'] = 'http://schema/3'

    _data10 = records[7][1]
    _data10['$schema'] = 'http://schema/2'
    _data10['weko_creator_id'] = '1'
    
    _dc_data = {
        '_oai': {'id': '1'},
        'author_link': [],
        'control_number': '1',
        'item_1': {'attribute_name': 'item_1',
                   'attribute_value_mlt': [{'attribute_name': 'item_1',
                                            'attribute_value': 'Item'}]},
        'item_title': ['Back to the Future'],
        'item_type_id': '2',
        'owner': 1,
        'owners':[1],
        'weko_shared_ids': []
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
            'weko_shared_ids': [],
            'owner': 1,
            'owners':[1]
        },
        '_oai': {'id': '1'},
        'author_link': [],
        'control_number': '1',
        'itemtype': 'test2',
        'publish_date': None,
        'weko_creator_id': '1',
        'weko_shared_ids': [],
        'owner': 1,
        'owners':[1]
    }

    _jrc_data_4 = {
        'control_number': '1',
        '_oai': {'id': '1'},
        '_item_metadata': {
            'item_1': {
                'attribute_name': 'item_1',
                'attribute_value_mlt': [
                    {'attribute_name': 'item_1',
                     'attribute_value': 'Item'}]
            },
            'item_title': ['weko_shared_ids_1'],
            'item_type_id': '2',
            'control_number': '1',
            'author_link': [],
            'weko_shared_ids': [],
            'owner': 1,
            'owners':[1]
        },
        'itemtype': 'test2',
        'publish_date': None,
        'weko_creator_id':'1',
        'author_link': [],
        'weko_shared_ids': []
    }

    _jrc_data_4_1 = {
        'control_number': '1',
        '_oai': {'id': '1'},
        '_item_metadata': {
            'item_1': {
                'attribute_name': 'item_1',
                'attribute_type': 'creator',
                'attribute_value_mlt': [
                    {'attribute_name': 'item_1',
                     'attribute_value': 'Item'}]
            },
            'item_title': ['weko_shared_ids_1'],
            'item_type_id': '2',
            'control_number': '1',
            'author_link': [],
            'weko_shared_ids': [],
            'owner': 1,
            'owners':[1]
        },
        'itemtype': 'test2',
        'publish_date': None,
        'weko_creator_id':'5',
        'author_link': [],
        'owner': 1,
        'owners': [1],
        'weko_shared_ids': []
    }

    _jrc_data_4_2 = {
        'control_number': '1',
        '_oai': {'id': '1'},
        '_item_metadata': {
            'item_1': {
                'attribute_name': 'item_1',
                'attribute_type': 'file',
                'attribute_value_mlt': [
                    {'attribute_name': 'item_1',
                     'attribute_value': 'Item'}]
            },
            'item_title': ['weko_shared_ids_1'],
            'item_type_id': '2',
            'control_number': '1',
            'author_link': [],
            'weko_shared_ids': [],
            'owner': 1,
            'owners':[1]
        },
        'itemtype': 'test2',
        'publish_date': None,
        'weko_creator_id':'5',
        'author_link': [],
        'owner': 1,
        'owners': [1],
        'weko_shared_ids': []
    }

    _jrc_data_4_3 = {
        'control_number': '1',
        '_oai': {'id': '1'},
        '_item_metadata': {
            'item_1': {
                'attribute_name': 'item_1',
                'attribute_type': 'file',
                'attribute_value': ['test']
            },
            'item_title': ['weko_shared_ids_1'],
            'item_type_id': '2',
            'control_number': '1',
            'author_link': [],
            'weko_shared_ids': [],
            'owner': 1,
            'owners':[1]
        },
        'item':['test'],
        'itemtype': 'test2',
        'publish_date': None,
        'weko_creator_id':'5',
        'author_link': [],
        'owner': 1,
        'owners': [1],
        'weko_shared_ids': []
    }

    _jrc_data_5 = {
        'control_number': '1',
        '_oai': {'id': '1'},
        '_item_metadata': {
            'item_1': {
                'attribute_name': 'item_1',
                'attribute_value_mlt': [
                    {'attribute_name': 'item_1',
                     'attribute_value': 'Item'}]
            },
            'item_title': ['weko_shared_ids_2'],
            'item_type_id': '2',
            'control_number': '1',
            'author_link': [],
            'weko_shared_ids': [1,2],
            'owner': 1,
            'owners':[1]
        },
        'itemtype': 'test2',
        'publish_date': None,
        'author_link': [],
        'weko_creator_id': '5',
        'weko_shared_ids': [1,2],
        'owner': 1,
        'owners':[1]
    }

    _dc_data_6 = {
        'control_number': '1',
        'author_link': [],
        'item_1': {'attribute_name': 'item_1',
                   'attribute_value_mlt': [{'attribute_name': 'item_1',
                                            'attribute_value': 'Item'}]},
        'item_title': ['weko_shared_ids_3'],
        'item_type_id': '2',
        'owner': 5,
        'owners':[5],
        'weko_shared_ids': [1,2]
    }

    _dc_data_7 = {
        'control_number': '1',
        'author_link': [],
        'item_1': {'attribute_name': 'item_1',
                   'attribute_value_mlt': [{'attribute_name': 'item_1',
                                            'attribute_value': 'Item'}]},
        'item_title': ['weko_shared_ids_4'],
        'item_type_id': '2',
        'owner': 1,
        'owners':[1],
        'weko_shared_ids': [1,2]
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
    dc, jrc, is_edit = json_loader(_data3, _pid, owner_id=1)
    assert dict(dc)==_dc_data
    assert dict(jrc)==_jrc_data
    assert is_edit==False

    # shared_user_ids=[]
    dc, jrc, is_edit = json_loader(_data4, _pid)
    jrc['_item_metadata'] = dict(jrc['_item_metadata'])
    assert dict(jrc)==_jrc_data_4
    
    # shared_user_ids=[{"user":1},{"user":2}] user=admin, weko_creator_id=1
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        dc, jrc, is_edit = json_loader(_data5, _pid, owner_id=1)
        jrc['_item_metadata'] = dict(jrc['_item_metadata'])
        assert dict(jrc)==_jrc_data_5

    # shared_user_ids=[{"user":1},{"user":2}] user=admin, owner未設定
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        dc, jrc, is_edit = json_loader(_data6, _pid)
        assert dict(dc)==_dc_data_6

    # shared_user_ids=[{"user":1},{"user":2}] user=admin, owner=1
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        dc, jrc, is_edit = json_loader(_data7, _pid, owner_id=1)
        assert dict(dc)==_dc_data_7
    
    # Exception発生
    ojson = ItemTypes.get_record(2)
    del ojson['properties']['item_1']
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        with patch("weko_records.api.ItemTypes.get_record", return_value=ojson):
            with pytest.raises(Exception):
                dc, jrc, is_edit = json_loader(_data4, _pid)
                assert e.type==KeyError
    
    # "object" == creator["type"]
    ojson = ItemTypes.get_record(2)
    ojson["properties"]["item_1"] = {'type': 'object', 'properties': ['iscreator']}
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        with patch("weko_records.api.ItemTypes.get_record", return_value=ojson):
            dc, jrc, is_edit = json_loader(_data4, _pid, owner_id=1)
            jrc['_item_metadata'] = dict(jrc['_item_metadata'])
            assert dict(jrc)==_jrc_data_4_1
    
    ojson["properties"]["item_1"] = {'type': 'object', 'properties': ['iscreator', 'other']}
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        with patch("weko_records.api.ItemTypes.get_record", return_value=ojson):
            dc, jrc, is_edit = json_loader(_data4, _pid, owner_id=1)
            jrc['_item_metadata'] = dict(jrc['_item_metadata'])
            assert dict(jrc)==_jrc_data_4_1

    _data4["weko_creator_id"] = '1'
    ojson["properties"]["item_1"] = {'type': 'object', 'properties': ['iscreator', 'other']}
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        with patch("weko_records.api.ItemTypes.get_record", return_value=ojson):
            dc, jrc, is_edit = json_loader(_data4, _pid, owner_id=1)
            jrc['_item_metadata'] = dict(jrc['_item_metadata'])
            assert dict(jrc)["weko_creator_id"]==_jrc_data_4_1["weko_creator_id"]
    
    
    # "array" == creator["type"]
    ojson["properties"]["item_1"] = {'type': 'array', 'items': {'properties': ['iscreator']}}
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        with patch("weko_records.api.ItemTypes.get_record", return_value=ojson):
            dc, jrc, is_edit = json_loader(_data4, _pid, owner_id=1)
            jrc['_item_metadata'] = dict(jrc['_item_metadata'])
            assert dict(jrc)==_jrc_data_4_1

    # "array" == item_data.get("type")
    ojson["properties"]["item_1"] = {'type': 'array', 'items': {'properties': ['filename']}}
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        with patch("weko_records.api.ItemTypes.get_record", return_value=ojson):
            dc, jrc, is_edit = json_loader(_data4, _pid, owner_id=1)
            jrc['_item_metadata'] = dict(jrc['_item_metadata'])
            assert dict(jrc)==_jrc_data_4_2

    # isinstance(v, list):
    ojson["properties"]["item_1"] = {'type': 'array', 'items': {'properties': ['filename']}}
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        with patch("weko_records.api.ItemTypes.get_record", return_value=ojson):
            dc, jrc, is_edit = json_loader(_data8, _pid, owner_id=1)
            jrc['_item_metadata'] = dict(jrc['_item_metadata'])
            assert dict(jrc)==_jrc_data_4_2

    # isinstance(v, list): 
    ojson["properties"]["item_1"] = {'type': 'array', 'items': {'properties': ['filename']}}
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        with patch("weko_records.api.ItemTypes.get_record", return_value=ojson):
            _data8['item_1'] = ["test"]
            dc, jrc, is_edit = json_loader(_data8, _pid, owner_id=1)
            jrc['_item_metadata'] = dict(jrc['_item_metadata'])
            assert dict(jrc)==_jrc_data_4_3

    app.config['WEKO_SCHEMA_JPCOAR_V1_SCHEMA_NAME'] = 'jpcoar_v1_mapping'
    app.config['WEKO_SCHEMA_DDI_SCHEMA_NAME'] = 'ddi_mapping'
    ojson = ItemTypes.get_record(2)
    # isinstance(v, str):
    ojson["properties"]["item_1"] = {'type': 'array', 'items': {'properties': ['filename']}}
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        with patch("weko_records.api.ItemTypes.get_record", return_value=ojson):
            _data8['item_1'] = "test"
            dc, jrc, is_edit = json_loader(_data8, _pid, owner_id=1)
            jrc['_item_metadata'] = dict(jrc['_item_metadata'])
            assert dict(jrc)["_item_metadata"]["item_1"]["attribute_value"]=="test"
    
    # pubdateを通すだけ
    ojson = ItemTypes.get_record(3)
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        with patch("weko_records.api.ItemTypes.get_record", return_value=ojson):
            with pytest.raises(Exception) as e:
                dc, jrc, is_edit = json_loader(_data9, _pid, owner_id=1)
         
    ojson["properties"]["item_1"] = {'type': 'array', 'items': {'properties': ['filename']}}
    ojson["properties"]["control_number"] = {'type': 'int', 'items': {'properties': 1}}
    ojson = ItemTypes.get_record(2)
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        with patch("weko_records.api.ItemTypes.get_record", return_value=ojson):
            _data8['control_number'] = 1
            dc, jrc, is_edit = json_loader(_data8, _pid, owner_id=1)
            jrc['_item_metadata'] = dict(jrc['_item_metadata'])
            assert dc['control_number'] == _pid.pid_value
    
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        with patch('weko_records.utils.SchemaTree.get_jpcoar_json', return_value={'item': [], 'weko_creator_id': '1'}):
            dc, jrc, is_edit = json_loader(_data10, _pid, owner_id=1)
            assert dict(jrc)['weko_creator_id']=='1'
    """
    ojson = ItemTypes.get_record(2)
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        with patch("weko_records.api.ItemTypes.get_record", return_value=ojson):
            data = {'dlt_dis_num_selected': '', 'dlt_index_sort_selected': '',
                    'dlt_keyword_sort_selected': '', 'sort_options':'',
                    'detail_condition':'', 'display_control':'',
                    'init_disp_setting': ''}
            sm = SearchManagement.create(data)
            with patch("weko_admin.models.SearchManagement.get", return_value=sm):
                dc, jrc, is_edit = json_loader(_data8, _pid, owner_id=1)
                jrc['_item_metadata'] = dict(jrc['_item_metadata'])
    """


# def json_loader(data, pid, owner_id=None):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_json_loader_with_out_workflow_activity -v -s -vv --cov-branch --cov-report=html --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_json_loader_with_out_workflow_activity(app, db, item_type, item_type2, item_type_mapping2,  records, users, mocker):
    from weko_admin.config import WEKO_ADMIN_MANAGEMENT_OPTIONS
    item_type_scheme={"properties":{ "control_number":{"type":"string"},"item_1":{"title":"item_1","type":"string"},"item_2":{"title":"item_2","type":"string"},"item_3":{"title":"item_3","type":"object","properties":{"item_3_1":{"title":"item_3_1","type":"string"},"iscreator":{"type":"string"}}},"item_4":{"title":"item_4","type":"object","properties":{"item_4_1":{"title":"item_4_1","type":"string"}}},"item_5":{"title":"item_5","type":"array","items":{"properties":{"filename":{"type":"string","title":"filename"},"iscreator":{"type":"string"}}},},"item_6":{"title":"item_6","type":"array","items":{"properties":{"item_6_1":{"title":"item_6_1","type":"string"}}},},"item_7":{"title":"item_7","type":"array","items":{"properties":{"nameIdentifiers":{"type":"array","items":{"properties":{"nameIdentifier":{"title":"name identifier","type":"string"},"nameIdentifierScheme":{"title":"name identifier scheme","type":"string"}}}}}}},"item_8":{"title":"item_8","type": "object","properties":{"nameIdentifiers":{"type":"array","items":{"properties":{"nameIdentifier":{"title":"name identifier","type":"string"},"nameIdentifierScheme":{"title":"name identifier scheme","type":"string"}}}}}}}}
    item_type_mapping = { "control_number":{},"item_1":{"jpcoar_mapping":""},"item_2":{"jpcoar_mapping":""},"item_3":{"jpcoar_mapping":{"item_3":{"@value":"item_3_1"}}},"item_4":{"jpcoar_mapping":{"item_4":{"@value":"item_4_1"}}},"item_5":{"jpcoar_mapping":{"item_5":{"@value":"filename"}}},"item_6":{"jpcoar_mapping":{"item_6":{"@value":"item_6_1"}}},"item_7":{"jpcoar_mapping":{"creator1":{"nameIdentifier":{"@value":"nameIdentifiers.nameIdentifier","@attributes":{"nameIdentifierScheme":"nameIdentifiers.nameIdentifierScheme"}}}}},"item_8":{"jpcoar_mapping":{"creator1":{"nameIdentifier":{"@value":"nameIdentifiers.nameIdentifier","@attributes":{"nameIdentifierScheme":"nameIdentifiers.nameIdentifierScheme"}}}}}}
    _pid = records[0][0]
    
    mocker.patch("weko_authors.api.WekoAuthors.get_pk_id_by_weko_id", return_value="2")
    mocker.patch("weko_authors.utils.update_data_for_weko_link")
    ItemTypes.create(
        name='test10',
        item_type_name=ItemTypeName(name='test10'),
        schema=item_type_scheme,
        render={},
        tag=1
    )
    class MockMapping:
        def dumps(self):
            return item_type_mapping
    mocker.patch("weko_records.utils.Mapping.get_record",return_value=MockMapping())

    with patch("weko_records.utils.COPY_NEW_FIELD",False):
        with patch("flask_login.utils._get_user", return_value=users[7]["obj"]):
            with patch("flask_login.UserMixin.get_id", return_value=1):
                jrc = {"weko_creator_id":"1", 'item_5': ['item_5'], 'item_6': ['item_6_1_v'], 'item_3': ['item_3_1_v'],
                    'item_4': ['item_4_1_v'], 'creator1': {'nameIdentifier': ['1234', '5678']}}
                with patch("weko_schema_ui.schema.SchemaTree.get_jpcoar_json", return_value=jrc):
                    data={
                        '$schema': 'http://schema/3',
                        "owner":"1",
                        "pubdate":"2023-08-08",
                        "title":"test_item2",
                        "weko_shared_id":2,
                        "item_1":"item_1_v",
                        "item_2":"item_2_v",
                        "item_3":{"item_3_1":"item_3_1_v"},
                        "item_4":{"item_4_1":"item_4_1_v"},
                        "item_5":[{"filename":"item_5"}],
                        "item_6":["item_6_1","item_6_1_v"],
                        "item_7":[{},{"nameIdentifiers":[{"nameIdentifierScheme":"WEKO","nameIdentifier":"1234"}]}],
                        "item_8":{"nameIdentifiers":[{"nameIdentifierScheme":"WEKO","nameIdentifier":"5678"}]},
                    }
                    dc, jrc, is_edit = json_loader(data, _pid)
                    assert dc == OrderedDict([('pubdate', {'attribute_name': 'Publish Date', 'attribute_value': '2023-08-08'}), ('item_1', {'attribute_name': 'item_1', 'attribute_value': 'item_1_v'}), ('item_2', {'attribute_name': 'item_2', 'attribute_value': 'item_2_v'}), ('item_3', {'attribute_name': 'item_3', 'attribute_type': 'creator', 'attribute_value_mlt': [{'item_3_1': 'item_3_1_v'}]}), ('item_4', {'attribute_name': 'item_4', 'attribute_value_mlt': [{'item_4_1': 'item_4_1_v'}]}), ('item_5', {'attribute_name': 'item_5', 'attribute_type': 'file', 'attribute_value_mlt': [{'filename': 'item_5'}]}), ('item_6', {'attribute_name': 'item_6', 'attribute_value': ['item_6_1', 'item_6_1_v']}), ('item_7', {'attribute_name': 'item_7', 'attribute_value_mlt': [{}, {'nameIdentifiers': [{'nameIdentifierScheme': 'WEKO', 'nameIdentifier': '1234'}]}]}), ('item_8', {'attribute_name': 'item_8', 'attribute_value_mlt': [{'nameIdentifiers': [{'nameIdentifierScheme': 'WEKO', 'nameIdentifier': '5678'}]}]}), ('item_title', 'test_item2'), ('item_type_id', '3'), ('control_number', '1'), ('author_link', ['2', '2']), ('weko_link', {'2': '5678'}), ('_oai', {'id': '1'}), ('weko_shared_id', 2), ('owner', 1)])
                    assert jrc == {'weko_creator_id': '1', 'item_5': ['item_5'], 'item_6': ['item_6_1_v'], 'item_3': ['item_3_1_v'], 'item_4': ['item_4_1_v'], 'creator1': {'nameIdentifier': ['1234', '5678']}, 'control_number': '1', '_oai': {'id': '1'}, '_item_metadata': OrderedDict([('pubdate', {'attribute_name': 'Publish Date', 'attribute_value': '2023-08-08'}), ('item_1', {'attribute_name': 'item_1', 'attribute_value': 'item_1_v'}), ('item_2', {'attribute_name': 'item_2', 'attribute_value': 'item_2_v'}), ('item_3', {'attribute_name': 'item_3', 'attribute_type': 'creator', 'attribute_value_mlt': [{'item_3_1': 'item_3_1_v'}]}), ('item_4', {'attribute_name': 'item_4', 'attribute_value_mlt': [{'item_4_1': 'item_4_1_v'}]}), ('item_5', {'attribute_name': 'item_5', 'attribute_type': 'file', 'attribute_value_mlt': [{'filename': 'item_5'}]}), ('item_6', {'attribute_name': 'item_6', 'attribute_value': ['item_6_1', 'item_6_1_v']}), ('item_7', {'attribute_name': 'item_7', 'attribute_value_mlt': [{}, {'nameIdentifiers': [{'nameIdentifierScheme': 'WEKO', 'nameIdentifier': '1234'}]}]}), ('item_8', {'attribute_name': 'item_8', 'attribute_value_mlt': [{'nameIdentifiers': [{'nameIdentifierScheme': 'WEKO', 'nameIdentifier': '5678'}]}]}), ('item_title', 'test_item2'), ('item_type_id', '3'), ('control_number', '1'), ('author_link', ['2', '2']), ('weko_link', {'2': '5678'}), ('_oai', {'id': '1'}), ('weko_shared_id', 2), ('owner', 1)]), 'itemtype': 'test10', 'publish_date': '2023-08-08', 'author_link': ['2', '2'], 'weko_link': {'2': '5678'}, 'weko_shared_id': 2}
                    assert is_edit == False


# def get_author_link(author_link, value)
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_get_author_link -v -s -vv --cov-branch --cov-report=term --cov-report=html --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_author_link():
    author_link = []
    value_list = [
        {
            "nameIdentifiers":[{
                "nameIdentifierScheme": 'WEKO', 
                "nameIdentifier": 'v1'
                }]
        },
        {
            "nameIdentifiers":[{
                "nameIdentifierScheme": 'WEKO3',
                "nameIdentifier": 'v2'
            }]
        }
    ]

    ret = get_author_link(author_link, value_list)
    assert ['v1'] == author_link

    author_link = []
    value_dict = {
            "nameIdentifiers":[{
                "nameIdentifierScheme": 'WEKO', 
                "nameIdentifier": 'v2'
                }]
    }
    ret = get_author_link(author_link, value_dict)
    assert ['v2'] == author_link

    author_link = []
    value_str = 'v2'
    ret = get_author_link(author_link, value_str)
    assert [] == author_link


# def copy_field_test(dc, map, jrc, iid=None):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_copy_field_test -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_copy_field_test(app, meta, k_v):
    _jrc = {}
    copy_field_test(meta[0], k_v, _jrc)
    assert _jrc=={
        'date_range1': [{'gte': '2000-01-01', 'lte': '2021-03-30'}],
        'text3': ['概要', 'その他', 'materials: text']
    }

    k_v1 = copy.deepcopy(k_v)
    del k_v1[1]
    k_v1[0]['inputType'] = "range"
    with patch("weko_records.utils.get_values_from_dict", return_value=[1,2,3,4,5]):
        with patch("weko_records.utils.convert_range_value", return_value=[1,2,3,4,5]):
            assert copy_field_test(meta[0], k_v1, _jrc) == None

            k_v1[0]['inputType'] = "geo_point"
            k_v1[0]['item_value']['1']['path']['lat'] = '99.99'
            k_v1[0]['item_value']['1']['path']['lon'] = '99.99'
            k_v1[0]['item_value']['1']['path_type']['lat'] = '99.99'
            k_v1[0]['item_value']['1']['path_type']['lon'] = '99.99'
            k_v1[0]['item_value']['12']['path']['lat'] = '99.99'
            k_v1[0]['item_value']['12']['path']['lon'] = '99.99'
            k_v1[0]['item_value']['12']['path_type']['lat'] = '99.99'
            k_v1[0]['item_value']['12']['path_type']['lon'] = '99.99'
            assert copy_field_test(meta[0], k_v1, _jrc) == None

            k_v1[0]['inputType'] = "geo_shape"
            k_v1[0]['item_value']['1']['path']['coordinates'] = '99.99'
            k_v1[0]['item_value']['1']['path']['type'] = '99.99'
            k_v1[0]['item_value']['1']['path_type']['coordinates'] = '99.99'
            k_v1[0]['item_value']['1']['path_type']['type'] = '99.99'
            k_v1[0]['item_value']['12']['path']['coordinates'] = '99.99'
            k_v1[0]['item_value']['12']['path']['type'] = '99.99'
            k_v1[0]['item_value']['12']['path_type']['coordinates'] = '99.99'
            k_v1[0]['item_value']['12']['path_type']['type'] = '99.99'
            assert copy_field_test(meta[0], k_v1, _jrc) == None

# def copy_field_test(dc, map, jrc, iid=None):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_copy_field_test_with_condition -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_copy_field_test_with_condition(app, meta01, k_v_with_c):
    _jrc = {}
    copy_field_test(meta01[0], k_v_with_c, _jrc)
    assert _jrc=={
        'date_range1': [{'gte': '2000-01-01', 'lte': '2021-03-30'}],
        'text1': ['東京大学史料編纂所', 'Historiographical Institute, the University of Tokyo'],
        'text3': ['概要日本語', '概要英語'],
        'text10': ['神奈川県立金沢文庫・称名寺', 'KANAGAWA PREFECTURAL KANAZAWA-BUNKO MUSEUM, Shomyoji Temple'],
        'text11': ['史資料: テキスト', 'materials: text']
    }

# def convert_range_value(start, end=None):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_convert_range_value -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_convert_range_value():
    assert convert_range_value('1')=={'gte': '1', 'lte': '1'}
    assert convert_range_value(None, '2')=={'gte': '2', 'lte': '2'}
    assert convert_range_value('1', '2')=={'gte': '1', 'lte': '2'}
    assert convert_range_value('2', '1')=={'gte': '1', 'lte': '2'}
    assert convert_range_value("1.1", "9.9")!={'gte': '1', 'lte': '2'}
    assert convert_range_value("9.9", "1.1")!={'gte': '1', 'lte': '2'}

    # Exception coverage
    try:
        assert convert_range_value('a', 'b')!={'gte': '1', 'lte': '2'}
    except:
        pass

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
    assert get_value_from_dict(meta[0], jsonpath[3], 'json')=='その他'
    assert get_value_from_dict(meta[0], jsonpath[3], 'xml')==None

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
    assert get_values_from_dict(
        meta[0], jsonpath[3], 'xml')==None

# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_get_values_from_dict_with_condition -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_values_from_dict_with_condition(app, meta01, jsonpath):
    assert get_values_from_dict_with_condition(meta01[0],
                                '$.item_1551264418667.attribute_value_mlt[*].subitem_1551257245638[*].subitem_1551257276108',
                                'json',
                                '$.item_1551264418667.attribute_value_mlt[*].subitem_1551257036415',
                                'Distributor', None)==['東京大学史料編纂所', 'Historiographical Institute, the University of Tokyo']
    assert get_values_from_dict_with_condition(meta01[0],
                                '$.item_1636460428217.attribute_value_mlt[*].subitem_1522657697257',
                                'json',
                                '$.item_1636460428217.attribute_value_mlt[*].subitem_1522657647525',
                                'Abstract', None)==['概要日本語', '概要英語']
    assert get_values_from_dict_with_condition(meta01[0],
                                '$.item_1551264418667.attribute_value_mlt[*].subitem_1551257245638[*].subitem_1551257276108',
                                'json',
                                '$.item_1551264418667.attribute_value_mlt[*].subitem_1551257036415',
                                'Other', None)==['神奈川県立金沢文庫・称名寺', 'KANAGAWA PREFECTURAL KANAZAWA-BUNKO MUSEUM, Shomyoji Temple']
    assert get_values_from_dict_with_condition(meta01[0],
                                '$.item_1636460428217.attribute_value_mlt[*].subitem_1522657697257',
                                'json',
                                '$.item_1636460428217.attribute_value_mlt[*].subitem_1522657647525',
                                'Other', None)==['史資料: テキスト', 'materials: text']
    assert get_values_from_dict_with_condition(meta01[0],
                                '$.item_1551264418667.attribute_value_mlt[*].subitem_1551257245638[*].subitem_1551257276108',
                                'json',
                                '$.item_1551264418667.attribute_value_mlt[*].subitem_1551257036415',
                                'TEST', None) is None
    assert get_values_from_dict_with_condition(meta01[0],
                                '$.item_1636460428217.attribute_value_mlt[*].subitem_1522657697257',
                                'json',
                                '$.item_1636460428217.attribute_value_mlt[*].subitem_1522657647525',
                                'TEST', None) is None
    assert get_values_from_dict_with_condition(meta01[0],
                                '$.item_1551264418667.attribute_value_mlt[*].subitem_1551257245638[*].subitem_1551257276108',
                                'json',
                                '$.item_type_id',
                                '12', None)==['東京大学史料編纂所', 'Historiographical Institute, the University of Tokyo', '神奈川県立金沢文庫・称名寺', 'KANAGAWA PREFECTURAL KANAZAWA-BUNKO MUSEUM, Shomyoji Temple']
    assert get_values_from_dict_with_condition(meta01[0],
                                '$.item_1551264418667.attribute_value_mlt[*].subitem_1551257245638[*].subitem_1551257276108',
                                'json',
                                'item_type_id',
                                'TEST', None) is None
    assert get_values_from_dict_with_condition(meta01[0], '', 'xml', '', '', None) is None
    assert get_values_from_dict_with_condition(meta01[0], '', 'pdf', '', '', None) is None

# def copy_value_xml_path(dc, xml_path, iid=None):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_copy_value_xml_path -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_copy_value_xml_path(meta):
    res = copy_value_xml_path(meta[0], '')
    assert res==None

    data1 = "<test>test<\test>"
    data2 = MagicMock()

    def text():
        return(9999)

    data3 = MagicMock()
    data3.text = text

    def findall(x, y):
        return [data3]

    data2.findall = findall

    with patch("lxml.etree.tostring", return_value=data1):
        with patch("invenio_oaiserver.response.getrecord", return_value=data1):
            with patch("weko_records.utils.ET.fromstring", return_value=data2):
                copy_value_xml_path(meta[0], ['/test', '/test/test'], iid=1)

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

    data1 = {
        "k": "k",
    }
    data2 = ['k', ['k']]

    assert get_all_items(_nlst, _klst, is_get_name=True) != None
    assert get_all_items(data1, [data2], is_get_name=True) != None

    data1['k'] = ['k']

    assert get_all_items(data1, [data2], is_get_name=True) != None

    data2 = ['k.k.k', ['k']]

    assert get_all_items(data1, [data2], is_get_name=True) != None


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

    solst, meta_options = get_options_and_order_list(1, item_type_data=item_type)
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
    record_hit=json_data(hit)
    settings = AdminSettings.get('items_display_settings')
    if not licence:
        i18n_app.config.update(
            WEKO_RECORDS_UI_LICENSE_DICT=False
        )
    await sort_meta_data_by_options(record_hit,settings,item_type)

params=[
    ("data/item_type/item_type_render4.json",
     "data/item_type/item_type_form4.json",
     "data/item_type/item_type_mapping3.json",
     "data/record_hit/record_hit6.json",
     True),
    ("data/item_type/item_type_render4.json",
     "data/item_type/item_type_form4.json",
     "data/item_type/item_type_mapping3.json",
     "data/record_hit/record_hit7.json",
     True),
    ("data/item_type/item_type_render4.json",
     "data/item_type/item_type_form4.json",
     "data/item_type/item_type_mapping3.json",
     "data/record_hit/record_hit8.json",
     True),
    ("data/item_type/item_type_render4.json",
     "data/item_type/item_type_form4.json",
     "data/item_type/item_type_mapping3.json",
     "data/record_hit/record_hit9.json",
     True)
]
@pytest.mark.parametrize("render,form,mapping,hit,licence",params)
@pytest.mark.asyncio
async def test_sort_meta_data_by_options_subRepository(i18n_app, db, admin_settings, mocker, item_type_mapping, item_type_mapping2,
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
    record_hit=json_data(hit)
    settings = AdminSettings.get('items_display_settings')
    if not licence:
        i18n_app.config.update(
            WEKO_RECORDS_UI_LICENSE_DICT=False
        )
    await sort_meta_data_by_options(record_hit,settings,item_type)


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
    settings = AdminSettings.get("items_display_settings")
    with patch("weko_records.serializers.utils.get_mapping",side_effect=Exception):
        await sort_meta_data_by_options(record_hit,settings,item_type)

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
    settings = AdminSettings.get("items_display_settings")
    await sort_meta_data_by_options(record_hit,settings,item_type)

#     def convert_data_to_dict(solst):
#     def get_author_comment(data_result, key, result, is_specify_newline_array):

#     def data_comment(result, data_result, stt_key, is_specify_newline_array):
# def test_data_comment(app):
#     result=[]
#     data_result = {'item_1617186331708': {'lang': ['ja', ' en'], 'lang_id': 'item_1617186331708.subitem_1551255648112'}, 'item_1617186385884': {'lang': ['en', ' ja'], 'lang_id': 'item_1617186385884.subitem_1551255721061'}, 'nameIdentifierScheme': {'nameIdentifierScheme': {'value': ['WEKO-,- ORCID-,- CiNii-,- KAKEN2-,- ORCID-,- CiNii-,- KAKEN2-,- ORCID-,- CiNii-,- KAKEN2']}}, 'nameIdentifierURI': {'nameIdentifierURI': {'value': ['https://orcid.org/-,- https://ci.nii.ac.jp/-,- https://kaken.nii.ac.jp/-,- https://orcid.org/-,- https://ci.nii.ac.jp/-,- https://kaken.nii.ac.jp/-,- https://orcid.org/-,- https://ci.nii.ac.jp/-,- https://kaken.nii.ac.jp/']}}, 'nameIdentifier': {'nameIdentifier': {'value': ['4-,- xxxxxxx-,- xxxxxxx-,- zzzzzzz-,- xxxxxxx-,- xxxxxxx-,- zzzzzzz-,- xxxxxxx-,- xxxxxxx-,- zzzzzzz']}}, 'creatorName': {'creatorName': {'value': ['Joho\t Taro', 'Joho\t Taro', 'Joho\t Taro']}}, 'familyName': {'familyName': {'value': ['Joho', 'Joho', 'Joho']}}, 'givenName': {'givenName': {'value': ['Taro', 'Taro', 'Taro']}}, 'affiliationNameIdentifier': {'affiliationNameIdentifier': {'value': ['0000000121691048']}}, 'affiliationNameIdentifierScheme': {'affiliationNameIdentifierScheme': {'value': ['ISNI']}}, 'affiliationNameIdentifierURI': {'affiliationNameIdentifierURI': {'value': ['http://isni.org/isni/0000000121691048']}}, 'affiliationName': {'affiliationName': {'value': ['University']}}, 'item_1617349709064.contributorNames': {'lang': ['ja', ' ja-Kana', ' en'], 'lang_id': 'item_1617349709064.contributorNames.lang'}, 'item_1617349709064.familyNames': {'lang': ['ja', ' ja-Kana', ' en'], 'lang_id': 'item_1617349709064.familyNames.familyNameLang'}, 'item_1617349709064.givenNames': {'lang': ['ja', ' ja-Kana', ' en'], 'lang_id': 'item_1617349709064.givenNames.givenNameLang'}, 'item_1617186499011': {'lang': ['ja'], 'lang_id': 'item_1617186499011.subitem_1522650717957'}, 'item_1617610673286.rightHolderNames': {'lang': ['ja'], 'lang_id': 'item_1617610673286.rightHolderNames.rightHolderLanguage'}, 'item_1617186609386': {'lang': ['ja'], 'lang_id': 'item_1617186609386.subitem_1522299896455'}, 'item_1617186626617': {'lang': ['en', ' ja'], 'lang_id': 'item_1617186626617.subitem_description_language'}, 'item_1617186643794': {'lang': ['en'], 'lang_id': 'item_1617186643794.subitem_1522300295150'}, 'item_1617186702042': {'lang': ['jpn'], 'lang_id': 'item_1617186702042.subitem_1551255818386'}, 'item_1617353299429.subitem_1523320863692': {'lang': ['en'], 'lang_id': 'item_1617353299429.subitem_1523320863692.subitem_1523320867455'}, 'item_1617186859717': {'lang': ['en'], 'lang_id': 'item_1617186859717.subitem_1522658018441'}, 'item_1617186901218.subitem_1522399412622': {'lang': ['en'], 'lang_id': 'item_1617186901218.subitem_1522399412622.subitem_1522399416691'}, 'item_1617186901218.subitem_1522399651758': {'lang': ['en'], 'lang_id': 'item_1617186901218.subitem_1522399651758.subitem_1522721910626'}, 'item_1617186941041': {'lang': ['en'], 'lang_id': 'item_1617186941041.subitem_1522650068558', 'stt': ['item_1617186941041.subitem_1522650091861'], 'item_1617186941041.subitem_1522650091861': {'value': ['Source Title']}}, 'item_1617186959569': {'stt': ['item_1617186959569.subitem_1551256328147'], 'item_1617186959569.subitem_1551256328147': {'value': ['1']}}, 'item_1617186981471': {'stt': ['item_1617186981471.subitem_1551256294723'], 'item_1617186981471.subitem_1551256294723': {'value': ['111']}}, 'item_1617186994930': {'stt': ['item_1617186994930.subitem_1551256248092'], 'item_1617186994930.subitem_1551256248092': {'value': ['12']}}, 'item_1617187024783': {'stt': ['item_1617187024783.subitem_1551256198917'], 'item_1617187024783.subitem_1551256198917': {'value': ['1']}}, 'item_1617187045071': {'stt': ['item_1617187045071.subitem_1551256185532'], 'item_1617187045071.subitem_1551256185532': {'value': ['3']}}, 'item_1617187112279': {'stt': ['item_1617187112279.subitem_1551256126428'], 'item_1617187112279.subitem_1551256126428': {'value': ['Degree Name']}, 'lang': ['en'], 'lang_id': 'item_1617187112279.subitem_1551256129013'}, 'item_1617187136212': {'stt': ['item_1617187136212.subitem_1551256096004'], 'item_1617187136212.subitem_1551256096004': {'value': ['2021-06-30']}}, 'item_1617944105607.subitem_1551256015892': {'stt': ['item_1617944105607.subitem_1551256015892.subitem_1551256027296', 'item_1617944105607.subitem_1551256015892.subitem_1551256029891'], 'item_1617944105607.subitem_1551256015892.subitem_1551256027296': {'value': ['xxxxxx']}, 'item_1617944105607.subitem_1551256015892.subitem_1551256029891': {'value': ['kakenhi']}}, 'item_1617944105607.subitem_1551256037922': {'stt': ['item_1617944105607.subitem_1551256037922.subitem_1551256042287'], 'item_1617944105607.subitem_1551256037922.subitem_1551256042287': {'value': ['Degree Grantor Name']}, 'lang': ['en'], 'lang_id': 'item_1617944105607.subitem_1551256037922.subitem_1551256047619'}, 'item_1617187187528.subitem_1599711633003': {'stt': ['item_1617187187528.subitem_1599711633003.subitem_1599711636923'], 'item_1617187187528.subitem_1599711633003.subitem_1599711636923': {'value': ['Conference Name']}, 'lang': ['ja'], 'lang_id': 'item_1617187187528.subitem_1599711633003.subitem_1599711645590'}, 'item_1617187187528': {'stt': ['item_1617187187528.subitem_1599711655652', 'item_1617187187528.subitem_1599711813532'], 'item_1617187187528.subitem_1599711655652': {'value': ['1']}, 'item_1617187187528.subitem_1599711813532': {'value': ['JPN']}}, 'item_1617187187528.subitem_1599711660052': {'stt': ['item_1617187187528.subitem_1599711660052.subitem_1599711680082'], 'item_1617187187528.subitem_1599711660052.subitem_1599711680082': {'value': ['Sponsor']}, 'lang': ['ja'], 'lang_id': 'item_1617187187528.subitem_1599711660052.subitem_1599711686511'}, 'item_1617187187528.subitem_1599711699392': {'stt': ['item_1617187187528.subitem_1599711699392.subitem_1599711731891', 'item_1617187187528.subitem_1599711699392.subitem_1599711727603', 'item_1617187187528.subitem_1599711699392.subitem_1599711712451', 'item_1617187187528.subitem_1599711699392.subitem_1599711743722', 'item_1617187187528.subitem_1599711699392.subitem_1599711739022', 'item_1617187187528.subitem_1599711699392.subitem_1599711704251', 'item_1617187187528.subitem_1599711699392.subitem_1599711735410'], 'item_1617187187528.subitem_1599711699392.subitem_1599711731891': {'value': ['2000']}, 'item_1617187187528.subitem_1599711699392.subitem_1599711727603': {'value': ['12']}, 'item_1617187187528.subitem_1599711699392.subitem_1599711712451': {'value': ['1']}, 'item_1617187187528.subitem_1599711699392.subitem_1599711743722': {'value': ['2020']}, 'item_1617187187528.subitem_1599711699392.subitem_1599711739022': {'value': ['12']}, 'item_1617187187528.subitem_1599711699392.subitem_1599711704251': {'value': ['2020/12/11']}, 'item_1617187187528.subitem_1599711699392.subitem_1599711735410': {'value': ['1']}, 'lang': ['ja'], 'lang_id': 'item_1617187187528.subitem_1599711699392.subitem_1599711745532'}, 'item_1617187187528.subitem_1599711758470': {'stt': ['item_1617187187528.subitem_1599711758470.subitem_1599711769260'], 'item_1617187187528.subitem_1599711758470.subitem_1599711769260': {'value': ['Conference Venue']}, 'lang': ['ja'], 'lang_id': 'item_1617187187528.subitem_1599711758470.subitem_1599711775943'}, 'item_1617187187528.subitem_1599711788485': {'stt': ['item_1617187187528.subitem_1599711788485.subitem_1599711798761'], 'item_1617187187528.subitem_1599711788485.subitem_1599711798761': {'value': ['Conference Place']}, 'lang': ['ja'], 'lang_id': 'item_1617187187528.subitem_1599711788485.subitem_1599711803382'}, 'item_1617620223087': {'lang': ['ja', ' en'], 'lang_id': 'item_1617620223087.subitem_1565671149650'}}
#     stt_key = ['item_1617186331708', 'item_1617186385884', 'nameIdentifierScheme', 'nameIdentifierURI', 'nameIdentifier', 'creatorName', 'familyName', 'givenName', 'affiliationNameIdentifier', 'affiliationNameIdentifierScheme', 'affiliationNameIdentifierURI', 'affiliationName', 'item_1617349709064.contributorNames', 'item_1617349709064.familyNames', 'item_1617349709064.givenNames', 'item_1617186499011', 'item_1617610673286.rightHolderNames', 'item_1617186609386', 'item_1617186626617', 'item_1617186643794', 'item_1617186702042', 'item_1617353299429.subitem_1523320863692', 'item_1617186859717', 'item_1617186901218.subitem_1522399412622', 'item_1617186901218.subitem_1522399651758', 'item_1617186941041', 'item_1617186959569', 'item_1617186981471', 'item_1617186994930', 'item_1617187024783', 'item_1617187045071', 'item_1617187112279', 'item_1617187136212', 'item_1617944105607.subitem_1551256015892', 'item_1617944105607.subitem_1551256037922', 'item_1617187187528.subitem_1599711633003', 'item_1617187187528', 'item_1617187187528.subitem_1599711660052', 'item_1617187187528.subitem_1599711699392', 'item_1617187187528.subitem_1599711758470', 'item_1617187187528.subitem_1599711788485', 'item_1617620223087']
#     is_specify_newline_array = [{'item_1617186331708.subitem_1551255648112': False}, {'item_1617186385884.subitem_1551255721061': False}, {'nameIdentifierScheme': True}, {'nameIdentifierURI': True}, {'nameIdentifier': True}, {'creatorName': True}, {'familyName': True}, {'givenName': True}, {'affiliationNameIdentifier': True}, {'affiliationNameIdentifierScheme': True}, {'affiliationNameIdentifierURI': True}, {'affiliationName': True}, {'item_1617349709064.contributorNames.lang': False}, {'item_1617349709064.familyNames.familyNameLang': False}, {'item_1617349709064.givenNames.givenNameLang': False}, {'item_1617186499011.subitem_1522650717957': False}, {'item_1617610673286.rightHolderNames.rightHolderLanguage': False}, {'item_1617186609386.subitem_1522299896455': False}, {'item_1617186626617.subitem_description_language': False}, {'item_1617186643794.subitem_1522300295150': False}, {'item_1617186702042.subitem_1551255818386': False}, {'item_1617353299429.subitem_1523320863692.subitem_1523320867455': False}, {'item_1617186859717.subitem_1522658018441': False}, {'item_1617186901218.subitem_1522399412622.subitem_1522399416691': False}, {'item_1617186901218.subitem_1522399651758.subitem_1522721910626': False}, {'item_1617186941041.subitem_1522650068558': False}, {'item_1617186941041.subitem_1522650091861': False}, {'item_1617186959569.subitem_1551256328147': False}, {'item_1617186981471.subitem_1551256294723': False}, {'item_1617186994930.subitem_1551256248092': False}, {'item_1617187024783.subitem_1551256198917': False}, {'item_1617187045071.subitem_1551256185532': False}, {'item_1617187112279.subitem_1551256126428': False}, {'item_1617187112279.subitem_1551256129013': False}, {'item_1617187136212.subitem_1551256096004': False}, {'item_1617944105607.subitem_1551256015892.subitem_1551256027296': False}, {'item_1617944105607.subitem_1551256015892.subitem_1551256029891': False}, {'item_1617944105607.subitem_1551256037922.subitem_1551256042287': False}, {'item_1617944105607.subitem_1551256037922.subitem_1551256047619': False}, {'item_1617187187528.subitem_1599711633003.subitem_1599711636923': True}, {'item_1617187187528.subitem_1599711633003.subitem_1599711645590': True}, {'item_1617187187528.subitem_1599711655652': True}, {'item_1617187187528.subitem_1599711660052.subitem_1599711680082': True}, {'item_1617187187528.subitem_1599711660052.subitem_1599711686511': True}, {'item_1617187187528.subitem_1599711699392.subitem_1599711731891': True}, {'item_1617187187528.subitem_1599711699392.subitem_1599711727603': True}, {'item_1617187187528.subitem_1599711699392.subitem_1599711712451': True}, {'item_1617187187528.subitem_1599711699392.subitem_1599711743722': True}, {'item_1617187187528.subitem_1599711699392.subitem_1599711739022': True}, {'item_1617187187528.subitem_1599711699392.subitem_1599711704251': True}, {'item_1617187187528.subitem_1599711699392.subitem_1599711735410': True}, {'item_1617187187528.subitem_1599711699392.subitem_1599711745532': True}, {'item_1617187187528.subitem_1599711758470.subitem_1599711769260': True}, {'item_1617187187528.subitem_1599711758470.subitem_1599711775943': True}, {'item_1617187187528.subitem_1599711788485.subitem_1599711798761': True}, {'item_1617187187528.subitem_1599711788485.subitem_1599711803382': True}, {'item_1617187187528.subitem_1599711813532': True}, {'item_1617620223087.subitem_1565671149650': False}]
#     _result = data_comment(result, data_result, stt_key, is_specify_newline_array)
#     _result = ['WEKO-,- ORCID-,- CiNii-,- KAKEN2-,- ORCID-,- CiNii-,- KAKEN2-,- ORCID-,- CiNii-,- KAKEN2', 'https://orcid.org/-,- https://ci.nii.ac.jp/-,- https://kaken.nii.ac.jp/-,- https://orcid.org/-,- https://ci.nii.ac.jp/-,- https://kaken.nii.ac.jp/-,- https://orcid.org/-,- https://ci.nii.ac.jp/-,- https://kaken.nii.ac.jp/', '4-,- xxxxxxx-,- xxxxxxx-,- zzzzzzz-,- xxxxxxx-,- xxxxxxx-,- zzzzzzz-,- xxxxxxx-,- xxxxxxx-,- zzzzzzz', 'Joho\t Taro,Joho\t Taro,Joho\t Taro', 'Joho,Joho,Joho', 'Taro,Taro,Taro', '0000000121691048', 'ISNI', 'http://isni.org/isni/0000000121691048', 'University,Source Title,1,111,12,1,3,Degree Name,2021-06-30,xxxxxx,kakenhi,Degree Grantor Name', 'Conference Name', '1', 'JPN', 'Sponsor', 'subitem_1599711743722', 'subitem_1599711743722', 'subitem_1599711743722', 'subitem_1599711743722', 'subitem_1599711743722', 'subitem_1599711743722', 'subitem_1599711743722', 'Conference Venue', 'Conference Place']

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

@pytest.mark.asyncio
async def test_sort_meta_data_by_options_sample_1(i18n_app, db, admin_settings):
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
    settings = AdminSettings.get("items_display_settings")

    data1 = {
        "key1.@attributes.xml:lang": "test",
    }

    data2 = MagicMock()
    data2.model = MagicMock()
    data2.model.form = {
        "key": "item_type_id",
        "title": "Title",
        "isShowList": True,
    }
    data2.model.render = {
        "meta_fix": {
            "meta_fix_9999": "meta_fix_9999",
            "item_type_id": {
                "option": {
                    "showlist": True,
                    "hidden": False,
                },
            },
        },
        "meta_list": {
            "meta_list_9999": "meta_list_9999",
        }
    }

    with patch("weko_records.serializers.utils.get_mapping", return_value=data1):
        with patch("weko_search_ui.utils.get_data_by_property", return_value=("1", "2")):
            await sort_meta_data_by_options(record_hit,settings,item_type)

            record_hit_2 = {
                "_source": {
                    "file": "file_9999",
                    "_comment": "_comment_9999",
                    "item_item_id": "8888",
                    "_item_metadata": {
                        "item_type_id": {
                            "attribute_value_mlt": [{
                                "value": "value_7777",
                                "url": {
                                    "label": "",
                                    "url": "url_9999",
                                    "value": "value_6666",
                                },
                                "filename": "filename_9999",
                                "version_id": "version_id_9999",
                                "accessrole": "open_restricted",
                                "subitem_thumbnail": ""
                            }],
                            "attribute_type": "file"
                        },
                    }
                }
            }

            data3 = copy.deepcopy(data2)
            data3.model.render["meta_fix"]["item_type_id"]["option"] = None

            await sort_meta_data_by_options(
                record_hit=record_hit_2,
                settings=settings,
                item_type_data=data3
            )

            await sort_meta_data_by_options(
                record_hit=record_hit_2,
                settings=settings,
                item_type_data=data2
            )

            record_hit_2["_source"]["_item_metadata"]["item_type_id"]["attribute_value_mlt"][0]["version_id"] = ""
            record_hit_2["_source"]["_item_metadata"]["item_type_id"]["attribute_value_mlt"][0]["accessrole"] = ""
            record_hit_2["_source"]["_item_metadata"]["item_type_id"]["attribute_value_mlt"][0]["url"]["label"] = ""

            await sort_meta_data_by_options(
                record_hit=record_hit_2,
                settings=settings,
                item_type_data=data2
            )

            data2.model.form["key"] = "1"

            await sort_meta_data_by_options(
                record_hit=record_hit_2,
                settings=settings,
                item_type_data=data2
            )

            data2.model.form["key"] = "item_type_id.item_type_id_9999"
            record_hit_2["_source"]["_item_metadata"]["item_type_id"]["attribute_value_mlt"][0]["version_id"] = "version_id_9999"
            record_hit_2["_source"]["_item_metadata"]["item_type_id"]["attribute_value_mlt"][0]["url"]["label"] = "label_9999"

            await sort_meta_data_by_options(
                record_hit=record_hit_2,
                settings=settings,
                item_type_data=data2
            )

            data2.model.form["key"] = "item_type_id"
            record_hit_2["_source"]["_item_metadata"]["item_type_id"]["attribute_type"] = "not_file"
            i18n_app.config["WEKO_RECORDS_UI_DEFAULT_MAX_WIDTH_THUMBNAIL"] = 99
            record_hit_2["_source"]["_item_metadata"]["item_type_id"]["attribute_value_mlt"][0]["subitem_thumbnail"] = [{"thumbnail_label": "thumbnail_label_9999"}]

            await sort_meta_data_by_options(
                record_hit=record_hit_2,
                settings=settings,
                item_type_data=data2
            )

            del record_hit_2["_source"]["_item_metadata"]["item_type_id"]["attribute_value_mlt"][0]["subitem_thumbnail"]

            await sort_meta_data_by_options(
                record_hit=record_hit_2,
                settings=settings,
                item_type_data=data2
            )

            # data4.model.form["key"] = "bibliographic_titles"

            data4 = MagicMock()
            data4.model = MagicMock()
            data4.model.form = {
                "key": "item_type_id",
                "title": "Title",
                "isShowList": True,
                "value": [{"value": "value"}],
            }
            data4.model.render = {
                "meta_fix": {
                    "meta_fix_9999": "meta_fix_9999",
                    "item_type_id": {
                        "option": {
                            "showlist": True,
                            "hidden": False,
                        },
                    },
                },
                "meta_list": {
                    "meta_list_9999": "meta_list_9999",
                }
            }

            await sort_meta_data_by_options(
                record_hit=record_hit_2,
                settings=settings,
                item_type_data=data4
            )

            # coverage
            # 806    if ojson is None:
            # 807        ojson = ItemTypes.get_record(item_type_id)
            try:
                await sort_meta_data_by_options(
                    record_hit=record_hit_2,
                    settings=settings,
                    item_type_data=None
                )
            except:
                pass


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


# def set_file_date(root_key, solst, metadata, attr_lst):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_set_file_date -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_set_file_date():
    root_key = "item_1617605131499"
    # with multi_lang
    solst = [["item_1617187187528[].subitem_1599711813532","Conference Country","開催国",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499","File","ファイル情報",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].filename","表示名","表示名",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].url","本文URL","本文URL",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].url.url","本文URL","本文URL",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].url.label","ラベル","ラベル",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].url.objectType","オブジェクトタイプ","オブジェクトタイプ",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].format","フォーマット","フォーマット",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].filesize","サイズ","サイズ",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].filesize[].value","サイズ","サイズ",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].fileDate","日付","日付",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].fileDate[].fileDateType","日付タイプ","日付タイプ",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].fileDate[].fileDateValue","日付","日付",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].version","バージョン情報","バージョン情報",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].displaytype","表示形式","表示形式",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].licensetype","ライセンス","ライセンス",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].licensefree","","自由ライセンス",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].accessrole","アクセス","アクセス",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].date[0].dateValue","公開日","公開日",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].groups","グループ","グループ",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617620223087","Heading","見出し",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""]]
    metadata = [{"url": {"url": "https://weko3.example.org/record/79/files/open_access.png" },"date": [{"dateType": "Available","dateValue": "2023-09-05" }],"format": "image/png","fileDate": [{"fileDateType": "Accepted","fileDateValue": "2023-09-02" }],"filename": "open_access.png","filesize": [{"value": "98 KB" }],"mimetype": "image/png","version_id": "5fc2d597-b658-4ae9-8ee5-8c3933eb0523","is_thumbnail": False,"future_date_message": "","download_preview_message": "","size": 98000.0,"file_order": 0}]
    attr_lst = [[[[{  "表示名": "open_access.png"}],[{"本文URL": [[[{"本文URL": "https://weko3.example.org/record/79/files/open_access.png"}]]]}],[{"フォーマット": "image/png"}],[{"サイズ": [[[[{  "サイズ": "98 KB"}]]]]}],[{"日付": [[[[{"日付タイプ": "Accepted"}],[{"日付": "2023-09-02"}]]]]}]]]]
    test = [[[[{"公開日": "2023-09-05"}],[{  "表示名": "open_access.png"}],[{"本文URL": [[[{"本文URL": "https://weko3.example.org/record/79/files/open_access.png"}]]]}],[{"フォーマット": "image/png"}],[{"サイズ": [[[[{  "サイズ": "98 KB"}]]]]}],[{"日付": [[[[{"日付タイプ": "Accepted"}],[{"日付": "2023-09-02"}]]]]}]]]]
    set_file_date(root_key, solst, metadata, attr_lst)
    assert test == attr_lst

    # data is not dict
    attr_lst = [[[[{  "表示名": "open_access.png"}],[{"本文URL": [[[{"本文URL": "https://weko3.example.org/record/79/files/open_access.png"}]]]}],[{"フォーマット": "image/png"}],[{"サイズ": [[[[{  "サイズ": "98 KB"}]]]]}],[{"日付": [[[[{"日付タイプ": "Accepted"}],[{"日付": "2023-09-02"}]]]]}]]]]
    metadata = ["not_dict_data"]
    test = [[[[{  "表示名": "open_access.png"}],[{"本文URL": [[[{"本文URL": "https://weko3.example.org/record/79/files/open_access.png"}]]]}],[{"フォーマット": "image/png"}],[{"サイズ": [[[[{  "サイズ": "98 KB"}]]]]}],[{"日付": [[[[{"日付タイプ": "Accepted"}],[{"日付": "2023-09-02"}]]]]}]]]]
    set_file_date(root_key, solst, metadata, attr_lst)
    assert test == attr_lst

    # without date data
    attr_lst = [[[[{  "表示名": "open_access.png"}],[{"本文URL": [[[{"本文URL": "https://weko3.example.org/record/79/files/open_access.png"}]]]}],[{"フォーマット": "image/png"}],[{"サイズ": [[[[{  "サイズ": "98 KB"}]]]]}],[{"日付": [[[[{"日付タイプ": "Accepted"}],[{"日付": "2023-09-02"}]]]]}]]]]
    metadata = [{"url": {"url": "https://weko3.example.org/record/79/files/open_access.png" },"format": "image/png","fileDate": [{"fileDateType": "Accepted","fileDateValue": "2023-09-02" }],"filename": "open_access.png","filesize": [{"value": "98 KB" }],"mimetype": "image/png","version_id": "5fc2d597-b658-4ae9-8ee5-8c3933eb0523","is_thumbnail": False,"future_date_message": "","download_preview_message": "","size": 98000.0,"file_order": 0}]
    test = [[[[{  "表示名": "open_access.png"}],[{"本文URL": [[[{"本文URL": "https://weko3.example.org/record/79/files/open_access.png"}]]]}],[{"フォーマット": "image/png"}],[{"サイズ": [[[[{  "サイズ": "98 KB"}]]]]}],[{"日付": [[[[{"日付タイプ": "Accepted"}],[{"日付": "2023-09-02"}]]]]}]]]]
    set_file_date(root_key, solst, metadata, attr_lst)
    assert test == attr_lst

    # without multi_lang
    solst = [["item_1617187187528[].subitem_1599711813532","Conference Country","開催国",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499","File","ファイル情報",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].filename","表示名","表示名",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].url","本文URL","本文URL",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].url.url","本文URL","本文URL",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].url.label","ラベル","ラベル",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].url.objectType","オブジェクトタイプ","オブジェクトタイプ",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].format","フォーマット","フォーマット",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].filesize","サイズ","サイズ",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].filesize[].value","サイズ","サイズ",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].fileDate","日付","日付",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].fileDate[].fileDateType","日付タイプ","日付タイプ",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].fileDate[].fileDateValue","日付","日付",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].version","バージョン情報","バージョン情報",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].displaytype","表示形式","表示形式",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].licensetype","ライセンス","ライセンス",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].licensefree","","自由ライセンス",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].accessrole","アクセス","アクセス",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].date[0].dateValue","Opendate","",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617605131499[].groups","グループ","グループ",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""],["item_1617620223087","Heading","見出し",{"required": False,"show_list": False,"specify_newline": False,"hide": False,"non_display": False},""]]
    metadata = [{"url": {"url": "https://weko3.example.org/record/79/files/open_access.png" },"date": [{"dateType": "Available","dateValue": "2023-09-05" }],"format": "image/png","fileDate": [{"fileDateType": "Accepted","fileDateValue": "2023-09-02" }],"filename": "open_access.png","filesize": [{"value": "98 KB" }],"mimetype": "image/png","version_id": "5fc2d597-b658-4ae9-8ee5-8c3933eb0523","is_thumbnail": False,"future_date_message": "","download_preview_message": "","size": 98000.0,"file_order": 0}]
    attr_lst = [[[[{  "表示名": "open_access.png"}],[{"本文URL": [[[{"本文URL": "https://weko3.example.org/record/79/files/open_access.png"}]]]}],[{"フォーマット": "image/png"}],[{"サイズ": [[[[{  "サイズ": "98 KB"}]]]]}],[{"日付": [[[[{"日付タイプ": "Accepted"}],[{"日付": "2023-09-02"}]]]]}]]]]
    test = [[[[{"Opendate": "2023-09-05"}],[{  "表示名": "open_access.png"}],[{"本文URL": [[[{"本文URL": "https://weko3.example.org/record/79/files/open_access.png"}]]]}],[{"フォーマット": "image/png"}],[{"サイズ": [[[[{  "サイズ": "98 KB"}]]]]}],[{"日付": [[[[{"日付タイプ": "Accepted"}],[{"日付": "2023-09-02"}]]]]}]]]]
    set_file_date(root_key, solst, metadata, attr_lst)
    assert test == attr_lst


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

    _nlst = [
        {
            'subitem_1': 'en_value',
            'subitem_1_lang': 'en',
            'creatorMail': "test_creatorMail",
        },
        {
            'subitem_1': 'ja_value',
            'subitem_1_lang': 'ja',
            'creatorMail': "test_creatorMail",
        },
        {
            'subitem_1': 'ja_value',
            'subitem_1_lang': ['ja'],
            'creatorMail': "test_creatorMail",
        },
        {
            'subitem_1': 'ja_value',
            'subitem_1_lang': {"ja": "ja"},
            'creatorMail': "test_creatorMail",
        },
        {
            'subitem_1': 'ja_value',
            'subitem_1_lang': {
                "item_name": "Language",
                "non_display": "non_display",
            },
            'creatorMail': "test_creatorMail",
        },
        {
            'subitem_1': 'ja_value',
            'subitem_1_lang': {
                "item_name": "Event",
                "non_display": "non_display",
            },
            'creatorMail': "test_creatorMail",
        },
    ]

    _klst = [
        [
            "item_1.subitem_1_lang",
            "Event",
            "en_item_1_title",
            {
                "required": False,
                "show_list": False,
                "specify_newline": False,
                "hide": False,
                "non_display": "AAAA",
            },
            "",
        ],
        [
            "creatorMail.mail",
            "item_1_title",
            "en_item_1_title",
            {
                "required": False,
                "show_list": True,
                "specify_newline": False,
                "hide": False,
                "non_display": "BBBB",
            },
            "",
        ],
        [
            "creatorMail.nameIdentifier",
            "item_1_lang",
            "en_item_1_lang",
            {
                "required": False,
                "show_list": False,
                "specify_newline": False,
                "hide": False,
                "non_display": "CCCC",
            },
            "",
        ],
    ]

    app.config["WEKO_RECORDS_TIME_PERIOD_TITLES"] = ["item_1_title", "item_1_lang"]

    get_attribute_value_all_items(
        'item_1',
        _nlst,
        _klst,
        is_author=False,
        hide_email_flag=True,
        non_display_flag=False,
        one_line_flag=True,
    )


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

    _old_render = {
        'meta_list': {"1": 1},
    }
    _new_render = {
        'meta_list': {"2": 2},
    }

    res = check_to_upgrade_version(_old_render, _new_render)
    assert res == True

    _new_render = {
        'meta_list': {"1": 1},
    }

    with patch("weko_records.utils.check_input_value", return_value=True):
        res = check_to_upgrade_version(_old_render, _new_render)
        assert res == True

# def remove_weko2_special_character(s: str):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_remove_weko2_special_character -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_remove_weko2_special_character():
    assert remove_weko2_special_character("HOGE")=="HOGE"
    assert remove_weko2_special_character("HOGE&EMPTY&HOGE")=="HOGEHOGE"
    assert remove_weko2_special_character("HOGE,&EMPTY&")=="HOGE"
    assert remove_weko2_special_character("&EMPTY&,HOGE")=="HOGE"
    assert remove_weko2_special_character("HOGE,&EMPTY&,HOGE")=="HOGE,,HOGE"

    with patch("re.sub", return_value=","):
        assert remove_weko2_special_character(",,,,") == ''

#     def __remove_special_character(_s_str: str):

# def selected_value_by_language(lang_array, value_array, lang_id, val_id, lang_selected, _item_metadata):
# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_selected_value_by_language -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_selected_value_by_language(app, meta):
    res = selected_value_by_language([], [], '', '', None, {})
    record = meta[0]
    assert res==None
    _val_id = 'item_1551264308487.subitem_1551255647225'
    res = selected_value_by_language([], [], '', _val_id, None, {}, hide_list=['invalid_subitem_key'])
    record = meta[0]
    assert res==None

    _val_id = 'item_1551264308487.subitem_1551255647225'
    res = selected_value_by_language([], [], '', _val_id, 'en', {}, hide_list=['item_1551264308487.subitem_1551255647225'])
    record = meta[0]
    assert res==None

    _val_id = 'item_1551264308487.subitem_1551255647225'
    res = selected_value_by_language([], ['タイトル日本語', 'Title'], '', _val_id, 'en', {}, hide_list=['invalid_subitem_key'])
    record = meta[0]
    assert res==None
    _lang_id = 'item_1551264308487.subitem_1551255648112'
    _val_id = 'item_1551264308487.subitem_1551255647225'
    res = selected_value_by_language(['ja', 'en'], ['タイトル日本語', 'Title'], _lang_id, _val_id, 'en', record)
    assert res=='Title'
    app.config['WEKO_RECORDS_UI_LANG_DISP_FLG'] = False
    _lang_id = 'item_1551264340087.subitem_1551255898956.subitem_1551255907416'
    _val_id = 'item_1551264340087.subitem_1551255898956.subitem_1551255905565'
    res = selected_value_by_language(['ja'], ['作者'], _lang_id, _val_id, 'en', record)
    assert res=='Creator'

    with patch("weko_records.utils.check_info_in_metadata", return_value="Mocked Value"): 
        res = selected_value_by_language(['ja'], ['作者'], _lang_id, _val_id, 'en', record)
        assert res=='Mocked Value'

    with patch("weko_records.utils.check_info_in_metadata", return_value='Creator'):
        res = selected_value_by_language(['en'], ['作者'], _lang_id, _val_id, 'en', record)
        assert res=='Creator'

    app.config['WEKO_RECORDS_UI_LANG_DISP_FLG'] = True
    res = selected_value_by_language(['ja'], ['作者'], _lang_id, _val_id, 'en', record)
    assert res=='Creator'
    with patch("weko_records.utils.check_info_in_metadata", return_value="en"):
        res = selected_value_by_language(["ja-Latn"], ['ja-Latn'], _lang_id, _val_id, 'en', record)
        assert res=='en'

    app.config['WEKO_RECORDS_UI_LANG_DISP_FLG'] = False
    _lang_id = 'item_1551264308487.subitem_1551255648112,item_1551264308488.subitem_1551255648113'
    _val_id = 'item_1551264308487.subitem_1551255647225,item_1551264308488.subitem_1551255647226'
    record['item_1551264308488'] = {
        "attribute_name": "Title",
        "attribute_value_mlt": [
            {
                "subitem_1551255647226": "タイトル日本語-2",
                "subitem_1551255648113": "ja"
            },
            {
                "subitem_1551255647226": "Title-2",
                "subitem_1551255648113": "en"
            }
        ]
    }
    res = selected_value_by_language(['ja', 'en', 'ja', 'en'], ['タイトル日本語', 'Title', 'タイトル日本語-2', 'Title-2'], _lang_id, _val_id, 'en', record)
    assert res=='Title'

    record["item_1551264308487"]["attribute_value_mlt"][0].pop("subitem_1551255648112")
    record["item_1551264308487"]["attribute_value_mlt"][1].pop("subitem_1551255648112")
    res = selected_value_by_language(['ja', 'en'], ['タイトル日本語', 'Title', 'タイトル日本語-2', 'Title-2'], _lang_id, _val_id, 'en', record)
    assert res=='タイトル日本語'

    record.pop("item_1551264308487")
    res = selected_value_by_language(['ja', 'en'], ['タイトル日本語-2', 'Title-2'], _lang_id, _val_id, 'en', record)
    assert res=='Title-2'

    with patch("weko_records.utils.check_info_in_metadata", return_value='Creator'):
            res = selected_value_by_language(['en'], ['作者'], _lang_id, _val_id, 'en', record, hide_list=['en'])
            assert res=='Creator'

# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_selected_value_by_language_2 -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_selected_value_by_language_2(app, meta):
    _lang_id = 'item_1551264308487.subitem_15512556481122'
    _val_id = 'item_1551264308487.subitem_15512556472252'

    with patch("weko_records.utils.check_info_in_metadata", return_value="en"):
        res = selected_value_by_language(["en"], ['ja'], _lang_id, _val_id, 'ja', meta[0])
        assert res=='en'

# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_selected_value_by_language_3 -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_selected_value_by_language_3(app):
    _lang_id = 'item_titles.subitem_title_language'
    _val_id = 'item_titles.subitem_title'
    meta = {'item_titles': {'attribute_name': 'タイトル', 'attribute_value_mlt': [{'subitem_title': 'title_with_nolang'}, {'subitem_title': 'title_en', 'subitem_title_language': 'en'}]}}
    res = selected_value_by_language(["en"], ['title_with_nolang','title_en'], _lang_id, _val_id, 'ja', meta)
    assert res!='title_en'
    assert res=='title_with_nolang'


    with patch("weko_records.utils.check_info_in_metadata", return_value="en"):
        res = selected_value_by_language(["ja-Latn"], ['ja-Latn'], _lang_id, _val_id, 'en', meta)
        assert res=='en'

def test_selected_value_by_language_2(app, meta):
    _lang_id = 'item_1551264308487.subitem_15512556481122'
    _val_id = 'item_1551264308487.subitem_15512556472252'

    with patch("weko_records.utils.check_info_in_metadata", return_value="en"):
        res = selected_value_by_language(["en"], ['ja'], _lang_id, _val_id, 'ja', meta[0])
        assert res=='en'

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
    _str_key_lang = 'item_30002_title0.subitem_title_language'
    _str_key_val = 'item_30002_title0.subitem_title'
    _lang = 'ja'
    _meta = {'path': ['1623632832836'], 'pubdate': '2024-12-26', 'item_30002_title0': {'subitem_title': 'title', 'subitem_title_language': 'ja'}, 'item_30002_resource_type13': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'item_30002_file35': [{'filename': '日本語.png'}], 'item_1735223788720': {'subitem_thumbnail': [{'thumbnail_label': 'jdcat.jsps.go.jp_about.png', 'thumbnail_url': '/api/files/d88a107f-c3a7-4ad6-81ca-4c34691682d1/jdcat.jsps.go.jp_about.png?versionId=37ad1676-9099-4f82-ba7a-35ef4f325b39'}]}}
    res = check_info_in_metadata(_str_key_lang, _str_key_val, _lang, _meta)
    assert res is not None
    assert res=='title'
    _str_key_lang = 'item_30002_title0.subitem_title_language'
    _str_key_val = 'item_30002_title0.subitem_title'
    _lang = 'ja'
    _meta = {'path': ['1623632832836'], 'pubdate': '2024-12-26', 'item_30002_title0': [{'subitem_title': 'title', 'subitem_title_language': 'ja'}], 'item_30002_resource_type13': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'item_30002_file35': [{'filename': '日本語.png'}], 'item_1735223788720': {'subitem_thumbnail': [{'thumbnail_label': 'jdcat.jsps.go.jp_about.png', 'thumbnail_url': '/api/files/d88a107f-c3a7-4ad6-81ca-4c34691682d1/jdcat.jsps.go.jp_about.png?versionId=37ad1676-9099-4f82-ba7a-35ef4f325b39'}]}}
    res = check_info_in_metadata(_str_key_lang, _str_key_val, _lang, _meta)
    assert res=='title'





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
    _source_title5 = {
        'ja': 'ja_test',
        'en': 'en_test',
        'id': 'id_test',
        'None Language': 'no_lang_test'
    }

    res = get_value_by_selected_lang({}, 'ja')
    assert res==None
    app.config['WEKO_RECORDS_UI_LANG_DISP_FLG'] = False
    res = get_value_by_selected_lang(_source_title1, 'ja')
    assert res=='ja_test'
    res = get_value_by_selected_lang(_source_title1, 'zh')
    assert res=='no_lang_test'
    res = get_value_by_selected_lang(_source_title2, 'zh')
    assert res=='no_lang_test'
    res = get_value_by_selected_lang(_source_title2, 'ja')
    assert res=='no_lang_test'
    res = get_value_by_selected_lang(_source_title3, 'en')
    assert res=='no_lang_test'
    res = get_value_by_selected_lang(_source_title4, 'th')
    assert res=='no_lang_test'
    res = get_value_by_selected_lang(_source_title5, 'ja')
    assert res=='ja_test'
    res = get_value_by_selected_lang(_source_title5, 'en')
    assert res=='en_test'
    res = get_value_by_selected_lang(_source_title5, 'zh')
    assert res=='en_test'
    app.config['WEKO_RECORDS_UI_LANG_DISP_FLG'] = True
    res = get_value_by_selected_lang(_source_title2, 'ja')
    assert res=='no_lang_test'
    res = get_value_by_selected_lang(_source_title3, 'en')
    assert res=='no_lang_test'



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
    assert res== [{'creatorName': ['en_name'], 'familyName': ['en_fname']}]

# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_get_show_list_author_test0 -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_show_list_author_test0(i18n_app):
    solst_dict_array=[{'key': 'pubdate', 'title': 'PubDate', 'title_ja': 'PubDate', 'option': {'required': True, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'multiple': False, 'required': True, 'showlist': False}, 'value': ''}, {'key': 'item_1617186331708', 'title': 'Title', 'title_ja': 'Title', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': True, 'showlist': False}, 'value': ''}, {'key': 'item_1617186331708.subitem_1551255647225', 'title': 'Title', 'title_ja': 'Title', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': True, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': '0-private-nooai-guest-4-0-public-oai-guest-1-ja-,- 0-private-nooai-guest-4-0-public-oai-guest-1-en'}, {'key': 'item_1617186331708.subitem_1551255648112', 'title': 'Language', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': True, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'ja-,- en'}, {'key': 'item_1617186385884', 'title': 'Alternative Title', 'title_ja': 'Alternative Title', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'value': ''}, {'key': 'item_1617186385884.subitem_1551255720400', 'title': 'Alternative Title', 'title_ja': 'Alternative Title', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'Alternative Title-,- Alternative Title'}, {'key': 'item_1617186385884.subitem_1551255721061', 'title': 'Language', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'en-,- ja'}, {'key': 'item_1617186419668', 'title': 'Creator', 'title_ja': 'Creator', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': True, 'hidden': False, 'oneline': True, 'multiple': True, 'required': False, 'showlist': True}, 'value': ''}, {'key': 'item_1617186419668.authorInputButton', 'title': '著者DBから入力', 'title_ja': '著者DBから入力', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617186419668.nameIdentifiers', 'title': '作成者識別子', 'title_ja': 'Creator Identifier', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617186419668.nameIdentifiers.nameIdentifierScheme', 'title': '作成者識別子Scheme', 'title_ja': 'Creator Identifier Scheme', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': 'WEKO-,- ORCID-,- CiNii-,- KAKEN2-,- ORCID-,- CiNii-,- KAKEN2-,- ORCID-,- CiNii-,- KAKEN2'}, {'key': 'item_1617186419668.nameIdentifiers.nameIdentifierURI', 'title': '作成者識別子URI', 'title_ja': 'Creator Identifier URI', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': 'https://orcid.org/-,- https://ci.nii.ac.jp/-,- https://nrid.nii.ac.jp/nrid/xxxxxxx-,- https://orcid.org/yyyyyy-,- https://ci.nii.ac.jp/author/yyyyyy-,- https://nrid.nii.ac.jp/nrid/yyyyyy-,- https://orcid.org/zzzzzzz-,- https://ci.nii.ac.jp/author/zzzzzzz-,- https://kaken.nii.ac.jp/'}, {'key': 'item_1617186419668.nameIdentifiers.nameIdentifier', 'title': '作成者識別子', 'title_ja': 'Creator Identifier', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': '4-,- xxxxxxx-,- xxxxxxx-,- xxxxxxx-,- yyyyyy-,- yyyyyy-,- yyyyyy-,- zzzzzzz-,- zzzzzzz-,- zzzzzzz'}, {'key': 'item_1617186419668.creatorNames', 'title': '作成者姓名', 'title_ja': 'Creator Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617186419668.creatorNames.creatorName', 'title': '姓名', 'title_ja': 'Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': '情報, 太郎-,- ジョウホウ\t タロウ-,- Joho\t Taro-,- 情報, 太郎-,- ジョウホウ\t タロウ-,- Joho\t Taro-,- 情報, 太郎-,- ジョウホウ\t タロウ-,- Joho\t Taro'}, {'key': 'item_1617186419668.creatorNames.creatorNameLang', 'title': '言語', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': 'ja-,- ja-Kana-,- en-,- ja-,- ja-Kana-,- en-,- ja-,- ja-Kana-,- en'}, {'key': 'item_1617186419668.familyNames', 'title': '作成者姓', 'title_ja': 'Creator Family Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617186419668.familyNames.familyName', 'title': '姓', 'title_ja': 'Family Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': '情報-,- ジョウホウ-,- Joho-,- 情報-,- ジョウホウ-,- Joho-,- 情報-,- ジョウホウ-,- Joho'}, {'key': 'item_1617186419668.familyNames.familyNameLang', 'title': '言語', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': 'ja-,- ja-Kana-,- en-,- ja-,- ja-Kana-,- en-,- ja-,- ja-Kana-,- en'}, {'key': 'item_1617186419668.givenNames', 'title': '作成者名', 'title_ja': 'Creator Given Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617186419668.givenNames.givenName', 'title': '名', 'title_ja': 'Given Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': '太郎-,- タロウ-,- Taro-,- 太郎-,- タロウ-,- Taro-,- 太郎-,- タロウ-,- Taro'}, {'key': 'item_1617186419668.givenNames.givenNameLang', 'title': '言語', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': 'ja-,- ja-Kana-,- en-,- ja-,- ja-Kana-,- en-,- ja-,- ja-Kana-,- en'}, {'key': 'item_1617186419668.creatorAlternatives', 'title': '作成者別名', 'title_ja': 'Creator Alternative Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617186419668.creatorAlternatives.creatorAlternative', 'title': '別名', 'title_ja': 'Alternative Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617186419668.creatorAlternatives.creatorAlternativeLang', 'title': '言語', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617186419668.creatorMails', 'title': '作成者メールアドレス', 'title_ja': 'Creator Email Address', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617186419668.creatorMails.creatorMail', 'title': 'メールアドレス', 'title_ja': 'Email Address', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': 'wekosoftware@nii.ac.jp-,- wekosoftware@nii.ac.jp-,- wekosoftware@nii.ac.jp'}, {'key': 'item_1617186419668.creatorAffiliations', 'title': '作成者所属', 'title_ja': 'Affiliation Name Identifier', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617186419668.creatorAffiliations.affiliationNameIdentifiers', 'title': '所属機関識別子', 'title_ja': 'Affiliation Name Identifier', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617186419668.creatorAffiliations.affiliationNameIdentifiers.affiliationNameIdentifier', 'title': '所属機関識別子', 'title_ja': 'Affiliation Name Identifier', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': '0000000121691048'}, {'key': 'item_1617186419668.creatorAffiliations.affiliationNameIdentifiers.affiliationNameIdentifierScheme', 'title': '所属機関識別子スキーマ', 'title_ja': 'Affiliation Name Identifier Scheme', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': 'ISNI'}, {'key': 'item_1617186419668.creatorAffiliations.affiliationNameIdentifiers.affiliationNameIdentifierURI', 'title': '所属機関識別子URI', 'title_ja': 'Affiliation Name Identifier URI', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': 'http://isni.org/isni/0000000121691048'}, {'key': 'item_1617186419668.creatorAffiliations.affiliationNames', 'title': '所属機関名', 'title_ja': 'Affiliation Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617186419668.creatorAffiliations.affiliationNames.affiliationName', 'title': '所属機関名', 'title_ja': 'Affiliation Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': 'University'}, {'key': 'item_1617186419668.creatorAffiliations.affiliationNames.affiliationNameLang', 'title': '言語', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': 'en'}, {'key': 'item_1617349709064', 'title': 'Contributor', 'title_ja': 'Contributor', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'value': ''}, {'key': 'item_1617349709064.contributorType', 'title': '寄与者タイプ', 'title_ja': 'Contributor Type', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'ContactPerson'}, {'key': 'item_1617349709064.nameIdentifiers', 'title': '寄与者識別子', 'title_ja': 'Contributor Identifier', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617349709064.nameIdentifiers.nameIdentifierScheme', 'title': '寄与者識別子Scheme', 'title_ja': 'Contributor Identifier Scheme', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'ORCID-,- CiNii-,- KAKEN2'}, {'key': 'item_1617349709064.nameIdentifiers.nameIdentifierURI', 'title': '寄与者識別子URI', 'title_ja': 'Contributor Identifier URI', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'https://orcid.org/-,- https://ci.nii.ac.jp/-,- https://kaken.nii.ac.jp/'}, {'key': 'item_1617349709064.nameIdentifiers.nameIdentifier', 'title': '寄与者識別子', 'title_ja': 'Contributor Identifier', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'xxxxxxx-,- xxxxxxx-,- xxxxxxx'}, {'key': 'item_1617349709064.contributorNames', 'title': '寄与者姓名', 'title_ja': 'Contributor Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617349709064.contributorNames.contributorName', 'title': '姓名', 'title_ja': 'Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': '情報, 太郎-,- ジョウホウ\t タロウ-,- Joho\t Taro'}, {'key': 'item_1617349709064.contributorNames.lang', 'title': '言語', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'ja-,- ja-Kana-,- en'}, {'key': 'item_1617349709064.familyNames', 'title': '寄与者姓', 'title_ja': 'Contributor Family Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617349709064.familyNames.familyName', 'title': '姓', 'title_ja': 'Family Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': '情報-,- ジョウホウ-,- Joho'}, {'key': 'item_1617349709064.familyNames.familyNameLang', 'title': '言語', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'ja-,- ja-Kana-,- en'}, {'key': 'item_1617349709064.givenNames', 'title': '寄与者名', 'title_ja': 'Contributor Given Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617349709064.givenNames.givenName', 'title': '名', 'title_ja': 'Given Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': '太郎-,- タロウ-,- Taro'}, {'key': 'item_1617349709064.givenNames.givenNameLang', 'title': '言語', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'ja-,- ja-Kana-,- en'}, {'key': 'item_1617349709064.contributorAlternatives', 'title': '寄与者別名', 'title_ja': 'Contributor Alternative Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617349709064.contributorAlternatives.contributorAlternative', 'title': '別名', 'title_ja': 'Alternative Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617349709064.contributorAlternatives.contributorAlternativeLang', 'title': '言語', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617349709064.contributorAffiliations', 'title': '寄与者所属', 'title_ja': 'Affiliation Name Identifier', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617349709064.contributorAffiliations.contributorAffiliationNameIdentifiers', 'title': '所属機関識別子', 'title_ja': 'Affiliation Name Identifier', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617349709064.contributorAffiliations.contributorAffiliationNameIdentifiers.contributorAffiliationNameIdentifier', 'title': '所属機関識別子', 'title_ja': 'Affiliation Name Identifier', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617349709064.contributorAffiliations.contributorAffiliationNameIdentifiers.contributorAffiliationScheme', 'title': '所属機関識別子スキーマ', 'title_ja': 'Affiliation Name Identifier Scheme', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617349709064.contributorAffiliations.contributorAffiliationNameIdentifiers.contributorAffiliationURI', 'title': '所属機関識別子URI', 'title_ja': 'Affiliation Name Identifier URI', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617349709064.contributorAffiliations.contributorAffiliationNames', 'title': '所属機関名', 'title_ja': 'Affiliation Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617349709064.contributorAffiliations.contributorAffiliationNames.contributorAffiliationName', 'title': '所属機関名', 'title_ja': 'Affiliation Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617349709064.contributorAffiliations.contributorAffiliationNames.contributorAffiliationNameLang', 'title': '言語', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617349709064.contributorMails', 'title': '寄与者メールアドレス', 'title_ja': 'Contributor Email Address', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617349709064.contributorMails.contributorMail', 'title': 'メールアドレス', 'title_ja': 'Email Address', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'wekosoftware@nii.ac.jp'}, {'key': 'item_1617349709064.authorInputButton', 'title': '著者DBから入力', 'title_ja': '著者DBから入力', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617186476635', 'title': 'Access Rights', 'title_ja': 'Access Rights', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': False}, 'value': ''}, {'key': 'item_1617186476635.subitem_1522299639480', 'title': 'アクセス権', 'title_ja': 'Access Rights', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'open access'}, {'key': 'item_1617186476635.subitem_1600958577026', 'title': 'アクセス権URI', 'title_ja': 'Access Rights URI', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'http://purl.org/coar/access_right/c_abf2'}, {'key': 'item_1617351524846', 'title': 'APC', 'title_ja': 'APC', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': False}, 'value': ''}, {'key': 'item_1617351524846.subitem_1523260933860', 'title': 'APC', 'title_ja': 'APC', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'Unknown'}, {'key': 'item_1617186499011', 'title': 'Rights', 'title_ja': 'Rights', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': True, 'multiple': True, 'required': False, 'showlist': False}, 'value': ''}, {'key': 'item_1617186499011.subitem_1522650717957', 'title': '言語', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'ja'}, {'key': 'item_1617186499011.subitem_1522650727486', 'title': '権利情報Resource', 'title_ja': 'Rights Information Resource', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'http://localhost'}, {'key': 'item_1617186499011.subitem_1522651041219', 'title': '権利情報', 'title_ja': 'Rights Information', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'Rights Information'}, {'key': 'item_1617610673286', 'title': 'Rights Holder', 'title_ja': 'Rights Holder', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'value': ''}, {'key': 'item_1617610673286.nameIdentifiers', 'title': '権利者識別子', 'title_ja': 'Right Holder Identifier', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617610673286.nameIdentifiers.nameIdentifierScheme', 'title': '権利者識別子Scheme', 'title_ja': 'Right Holder Identifier Scheme', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'ORCID'}, {'key': 'item_1617610673286.nameIdentifiers.nameIdentifierURI', 'title': '権利者識別子URI', 'title_ja': 'Right Holder Identifier URI', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'https://orcid.org/'}, {'key': 'item_1617610673286.nameIdentifiers.nameIdentifier', 'title': '権利者識別子', 'title_ja': 'Right Holder Identifier', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'xxxxxx'}, {'key': 'item_1617610673286.rightHolderNames', 'title': '権利者名', 'title_ja': 'Right Holder Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617610673286.rightHolderNames.rightHolderLanguage', 'title': '言語', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'ja'}, {'key': 'item_1617610673286.rightHolderNames.rightHolderName', 'title': '権利者名', 'title_ja': 'Right Holder Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'Right Holder Name'}, {'key': 'item_1617186609386', 'title': 'Subject', 'title_ja': 'Subject', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'value': ''}, {'key': 'item_1617186609386.subitem_1522299896455', 'title': '言語', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'ja'}, {'key': 'item_1617186609386.subitem_1522300014469', 'title': '主題Scheme', 'title_ja': 'Subject Scheme', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'Other'}, {'key': 'item_1617186609386.subitem_1522300048512', 'title': '主題URI', 'title_ja': 'Subject URI', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'http://localhost/'}, {'key': 'item_1617186609386.subitem_1523261968819', 'title': '主題', 'title_ja': 'Subject', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'Sibject1'}, {'key': 'item_1617186626617', 'title': 'Description', 'title_ja': 'Description', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'value': ''}, {'key': 'item_1617186626617.subitem_description_type', 'title': '内容記述タイプ', 'title_ja': 'Description Type', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'Abstract-,- Abstract'}, {'key': 'item_1617186626617.subitem_description', 'title': '内容記述', 'title_ja': 'Description', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'Description\nDescription\nDescription-,- 概要\n概要\n概要\n概要'}, {'key': 'item_1617186626617.subitem_description_language', 'title': '言語', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'en-,- ja'}, {'key': 'item_1617186643794', 'title': 'Publisher', 'title_ja': 'Publisher', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'value': ''}, {'key': 'item_1617186643794.subitem_1522300295150', 'title': '言語', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'en'}, {'key': 'item_1617186643794.subitem_1522300316516', 'title': '出版者', 'title_ja': 'Publisher', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'Publisher'}, {'key': 'item_1617186660861', 'title': 'Date', 'title_ja': 'Date', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': True, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'value': ''}, {'key': 'item_1617186660861.subitem_1522300695726', 'title': '日付タイプ', 'title_ja': 'Date Type', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': True, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': True}, 'value': 'Available'}, {'key': 'item_1617186660861.subitem_1522300722591', 'title': '日付', 'title_ja': 'Date', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': True, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': True}, 'value': '2021-06-30'}, {'key': 'item_1617186702042', 'title': 'Language', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'value': ''}, {'key': 'item_1617186702042.subitem_1551255818386', 'title': 'Language', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'jpn'}, {'key': 'item_1617258105262', 'title': 'Resource Type', 'title_ja': 'Resource Type', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': True, 'showlist': False}, 'value': ''}, {'key': 'item_1617258105262.resourcetype', 'title': '資源タイプ', 'title_ja': 'Resource Type', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': True, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'conference paper'}, {'key': 'item_1617258105262.resourceuri', 'title': '資源タイプ識別子', 'title_ja': 'Resource Type Identifier', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': True, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'http://purl.org/coar/resource_type/c_5794'}, {'key': 'item_1617349808926', 'title': 'Version', 'title_ja': 'Version', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': False}, 'value': ''}, {'key': 'item_1617349808926.subitem_1523263171732', 'title': 'バージョン情報', 'title_ja': 'Version', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'Version'}, {'key': 'item_1617265215918', 'title': 'Version Type', 'title_ja': 'Version Type', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': False}, 'value': ''}, {'key': 'item_1617265215918.subitem_1522305645492', 'title': '出版タイプ', 'title_ja': 'Version Type', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'AO'}, {'key': 'item_1617265215918.subitem_1600292170262', 'title': '出版タイプResource', 'title_ja': 'Version Type Resource', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'http://purl.org/coar/version/c_b1a7d7d4d402bcce'}, {'key': 'item_1617186783814', 'title': 'Identifier', 'title_ja': 'Identifier', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'value': ''}, {'key': 'item_1617186783814.subitem_identifier_uri', 'title': '識別子', 'title_ja': 'Identifier', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'http://localhost'}, {'key': 'item_1617186783814.subitem_identifier_type', 'title': '識別子タイプ', 'title_ja': 'Identifier Type', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'URI'}, {'key': 'item_1617186819068', 'title': 'Identifier Registration', 'title_ja': 'Identifier Registration', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': False}, 'value': ''}, {'key': 'item_1617186819068.subitem_identifier_reg_text', 'title': 'ID登録', 'title_ja': 'Identifier Registration', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617186819068.subitem_identifier_reg_type', 'title': 'ID登録タイプ', 'title_ja': 'Identifier Registration Type', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617353299429', 'title': 'Relation', 'title_ja': 'Relation', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'value': ''}, {'key': 'item_1617353299429.subitem_1522306207484', 'title': '関連タイプ', 'title_ja': 'Relation Type', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'isVersionOf'}, {'key': 'item_1617353299429.subitem_1522306287251', 'title': '関連識別子', 'title_ja': 'Relation Identifier', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617353299429.subitem_1522306287251.subitem_1522306382014', 'title': '識別子タイプ', 'title_ja': 'Identifier Type', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'arXiv'}, {'key': 'item_1617353299429.subitem_1522306287251.subitem_1522306436033', 'title': '関連識別子', 'title_ja': 'Relation Identifier', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'xxxxx'}, {'key': 'item_1617353299429.subitem_1523320863692', 'title': '関連名称', 'title_ja': 'Related Title', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617353299429.subitem_1523320863692.subitem_1523320867455', 'title': '言語', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'en'}, {'key': 'item_1617353299429.subitem_1523320863692.subitem_1523320909613', 'title': '関連名称', 'title_ja': 'Related Title', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'Related Title'}, {'key': 'item_1617186859717', 'title': 'Temporal', 'title_ja': 'Temporal', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'value': ''}, {'key': 'item_1617186859717.subitem_1522658018441', 'title': '言語', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'en'}, {'key': 'item_1617186859717.subitem_1522658031721', 'title': '時間的範囲', 'title_ja': 'Temporal', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'Temporal'}, {'key': 'item_1617186882738', 'title': 'Geo Location', 'title_ja': 'Geo Location', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'value': ''}, {'key': 'item_1617186882738.subitem_geolocation_point', 'title': '位置情報（点）', 'title_ja': 'Geo Location Point', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617186882738.subitem_geolocation_point.subitem_point_longitude', 'title': '経度', 'title_ja': 'Point Longitude', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617186882738.subitem_geolocation_point.subitem_point_latitude', 'title': '緯度', 'title_ja': 'Point Latitude', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617186882738.subitem_geolocation_box', 'title': '位置情報（空間）', 'title_ja': 'Geo Location Box', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617186882738.subitem_geolocation_box.subitem_west_longitude', 'title': '西部経度', 'title_ja': 'West Bound Longitude', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617186882738.subitem_geolocation_box.subitem_east_longitude', 'title': '東部経度', 'title_ja': 'East Bound Longitude', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617186882738.subitem_geolocation_box.subitem_south_latitude', 'title': '南部緯度', 'title_ja': 'South Bound Latitude', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617186882738.subitem_geolocation_box.subitem_north_latitude', 'title': '北部緯度', 'title_ja': 'North Bound Latitude', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617186882738.subitem_geolocation_place', 'title': '位置情報（自由記述）', 'title_ja': 'Geo Location Place', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617186882738.subitem_geolocation_place.subitem_geolocation_place_text', 'title': '位置情報（自由記述）', 'title_ja': 'Geo Location Place', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'Japan'}, {'key': 'item_1617186901218', 'title': 'Funding Reference', 'title_ja': 'Funding Reference', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'value': ''}, {'key': 'item_1617186901218.subitem_1522399143519', 'title': '助成機関識別子', 'title_ja': 'Funder Identifier', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617186901218.subitem_1522399143519.subitem_1522399281603', 'title': '助成機関識別子タイプ', 'title_ja': 'Funder Identifier Type', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'ISNI'}, {'key': 'item_1617186901218.subitem_1522399143519.subitem_1522399333375', 'title': '助成機関識別子', 'title_ja': 'Funder Identifier', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'http://xxx'}, {'key': 'item_1617186901218.subitem_1522399412622', 'title': '助成機関名', 'title_ja': 'Funder Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617186901218.subitem_1522399412622.subitem_1522399416691', 'title': '言語', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'en'}, {'key': 'item_1617186901218.subitem_1522399412622.subitem_1522737543681', 'title': '助成機関名', 'title_ja': 'Funder Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'Funder Name'}, {'key': 'item_1617186901218.subitem_1522399571623', 'title': '研究課題番号', 'title_ja': 'Award Number', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617186901218.subitem_1522399571623.subitem_1522399585738', 'title': '研究課題URI', 'title_ja': 'Award URI', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'Award URI'}, {'key': 'item_1617186901218.subitem_1522399571623.subitem_1522399628911', 'title': '研究課題番号', 'title_ja': 'Award Number', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'Award Number'}, {'key': 'item_1617186901218.subitem_1522399651758', 'title': '研究課題名', 'title_ja': 'Award Title', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617186901218.subitem_1522399651758.subitem_1522721910626', 'title': '言語', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'en'}, {'key': 'item_1617186901218.subitem_1522399651758.subitem_1522721929892', 'title': '研究課題名', 'title_ja': 'Award Title', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'Award Title'}, {'key': 'item_1617186920753', 'title': 'Source Identifier', 'title_ja': 'Source Identifier', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'value': ''}, {'key': 'item_1617186920753.subitem_1522646500366', 'title': '収録物識別子タイプ', 'title_ja': 'Source Identifier Type', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'ISSN'}, {'key': 'item_1617186920753.subitem_1522646572813', 'title': '収録物識別子', 'title_ja': 'Source Identifier', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'xxxx-xxxx-xxxx'}, {'key': 'item_1617186941041', 'title': 'Source Title', 'title_ja': 'Source Title', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': True}, 'value': ''}, {'key': 'item_1617186941041.subitem_1522650068558', 'title': '言語', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': False, 'hide': False}, 'value': 'en'}, {'key': 'item_1617186941041.subitem_1522650091861', 'title': '収録物名', 'title_ja': 'Source Title', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': False, 'hide': False}, 'value': 'Source Title'}, {'key': 'item_1617186959569', 'title': 'Volume Number', 'title_ja': 'Volume Number', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'value': ''}, {'key': 'item_1617186959569.subitem_1551256328147', 'title': 'Volume Number', 'title_ja': 'Volume Number', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': False, 'hide': False}, 'value': '1'}, {'key': 'item_1617186981471', 'title': 'Issue Number', 'title_ja': 'Issue Number', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'value': ''}, {'key': 'item_1617186981471.subitem_1551256294723', 'title': 'Issue Number', 'title_ja': 'Issue Number', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': False, 'hide': False}, 'value': '111'}, {'key': 'item_1617186994930', 'title': 'Number of Pages', 'title_ja': 'Number of Pages', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'value': ''}, {'key': 'item_1617186994930.subitem_1551256248092', 'title': 'Number of Pages', 'title_ja': 'Number of Pages', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': False, 'hide': False}, 'value': '12'}, {'key': 'item_1617187024783', 'title': 'Page Start', 'title_ja': 'Page Start', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'value': ''}, {'key': 'item_1617187024783.subitem_1551256198917', 'title': 'Page Start', 'title_ja': 'Page Start', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': False, 'hide': False}, 'value': '1'}, {'key': 'item_1617187045071', 'title': 'Page End', 'title_ja': 'Page End', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'value': ''}, {'key': 'item_1617187045071.subitem_1551256185532', 'title': 'Page End', 'title_ja': 'Page End', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': False, 'hide': False}, 'value': '3'}, {'key': 'item_1617187056579', 'title': 'Bibliographic Information', 'title_ja': 'Bibliographic Information', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'value': ''}, {'key': 'item_1617187056579.bibliographic_titles', 'title': '雑誌名', 'title_ja': 'Journal Title', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617187056579.bibliographic_titles.bibliographic_title', 'title': 'タイトル', 'title_ja': 'Title', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617187056579.bibliographic_titles.bibliographic_titleLang', 'title': '言語', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617187056579.bibliographicVolumeNumber', 'title': '巻', 'title_ja': 'Volume Number', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617187056579.bibliographicIssueNumber', 'title': '号', 'title_ja': 'Issue Number', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617187056579.bibliographicPageStart', 'title': '開始ページ', 'title_ja': 'Page Start', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617187056579.bibliographicPageEnd', 'title': '終了ページ', 'title_ja': 'Page End', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617187056579.bibliographicNumberOfPages', 'title': 'ページ数', 'title_ja': 'Number of Page', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617187056579.bibliographicIssueDates', 'title': '発行日', 'title_ja': 'Issue Date', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617187056579.bibliographicIssueDates.bibliographicIssueDate', 'title': '日付', 'title_ja': 'Date', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617187056579.bibliographicIssueDates.bibliographicIssueDateType', 'title': '日付タイプ', 'title_ja': 'Date Type', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617187087799', 'title': 'Dissertation Number', 'title_ja': 'Dissertation Number', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'value': ''}, {'key': 'item_1617187087799.subitem_1551256171004', 'title': 'Dissertation Number', 'title_ja': 'Dissertation Number', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617187112279', 'title': 'Degree Name', 'title_ja': 'Degree Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': True}, 'value': ''}, {'key': 'item_1617187112279.subitem_1551256126428', 'title': 'Degree Name', 'title_ja': 'Degree Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': False, 'hide': False}, 'value': 'Degree Name'}, {'key': 'item_1617187112279.subitem_1551256129013', 'title': 'Language', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': False, 'hide': False}, 'value': 'en'}, {'key': 'item_1617187136212', 'title': 'Date Granted', 'title_ja': 'Date Granted', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': False, 'required': False, 'showlist': True}, 'value': ''}, {'key': 'item_1617187136212.subitem_1551256096004', 'title': 'Date Granted', 'title_ja': 'Date Granted', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': False, 'hide': False}, 'value': '2021-06-30'}, {'key': 'item_1617944105607', 'title': 'Degree Grantor', 'title_ja': 'Degree Grantor', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': True}, 'value': ''}, {'key': 'item_1617944105607.subitem_1551256015892', 'title': 'Degree Grantor Name Identifier', 'title_ja': 'Degree Grantor Name Identifier', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617944105607.subitem_1551256015892.subitem_1551256027296', 'title': 'Degree Grantor Name Identifier', 'title_ja': 'Degree Grantor Name Identifier', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': False, 'hide': False}, 'value': 'xxxxxx'}, {'key': 'item_1617944105607.subitem_1551256015892.subitem_1551256029891', 'title': 'Degree Grantor Name Identifier Scheme', 'title_ja': 'Degree Grantor Name Identifier Scheme', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': False, 'hide': False}, 'value': 'kakenhi'}, {'key': 'item_1617944105607.subitem_1551256037922', 'title': 'Degree Grantor Name', 'title_ja': 'Degree Grantor Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617944105607.subitem_1551256037922.subitem_1551256042287', 'title': 'Degree Grantor Name', 'title_ja': 'Degree Grantor Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': False, 'hide': False}, 'value': 'Degree Grantor Name'}, {'key': 'item_1617944105607.subitem_1551256037922.subitem_1551256047619', 'title': 'Language', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': False, 'hide': False}, 'value': 'en'}, {'key': 'item_1617187187528', 'title': 'Conference', 'title_ja': 'Conference', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': True, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': True}, 'value': ''}, {'key': 'item_1617187187528.subitem_1599711633003', 'title': 'Conference Name', 'title_ja': 'Conference Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617187187528.subitem_1599711633003.subitem_1599711636923', 'title': 'Conference Name', 'title_ja': 'Conference Name', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': 'Conference Name'}, {'key': 'item_1617187187528.subitem_1599711633003.subitem_1599711645590', 'title': 'Language', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': 'ja'}, {'key': 'item_1617187187528.subitem_1599711655652', 'title': 'Conference Sequence', 'title_ja': 'Conference Sequence', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': '1'}, {'key': 'item_1617187187528.subitem_1599711660052', 'title': 'Conference Sponsor', 'title_ja': 'Conference Sponsor', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617187187528.subitem_1599711660052.subitem_1599711680082', 'title': 'Conference Sponsor', 'title_ja': 'Conference Sponsor', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': 'Sponsor'}, {'key': 'item_1617187187528.subitem_1599711660052.subitem_1599711686511', 'title': 'Language', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': 'ja'}, {'key': 'item_1617187187528.subitem_1599711699392', 'title': 'Conference Date', 'title_ja': 'Conference Date', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617187187528.subitem_1599711699392.subitem_1599711731891', 'title': 'Start Year', 'title_ja': 'Start Year', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': '2000'}, {'key': 'item_1617187187528.subitem_1599711699392.subitem_1599711727603', 'title': 'Start Month', 'title_ja': 'Start Month', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': '12'}, {'key': 'item_1617187187528.subitem_1599711699392.subitem_1599711712451', 'title': 'Start Day', 'title_ja': 'Start Day', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': '1'}, {'key': 'item_1617187187528.subitem_1599711699392.subitem_1599711743722', 'title': 'End Year', 'title_ja': 'End Year', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': '2020'}, {'key': 'item_1617187187528.subitem_1599711699392.subitem_1599711739022', 'title': 'End Month', 'title_ja': 'End Month', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': '12'}, {'key': 'item_1617187187528.subitem_1599711699392.subitem_1599711704251', 'title': 'Conference Date', 'title_ja': 'Conference Date', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': '2020/12/11'}, {'key': 'item_1617187187528.subitem_1599711699392.subitem_1599711735410', 'title': 'End Day', 'title_ja': 'End Day', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': '1'}, {'key': 'item_1617187187528.subitem_1599711699392.subitem_1599711745532', 'title': 'Language', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': 'ja'}, {'key': 'item_1617187187528.subitem_1599711758470', 'title': 'Conference Venue', 'title_ja': 'Conference Venue', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617187187528.subitem_1599711758470.subitem_1599711769260', 'title': 'Conference Venue', 'title_ja': 'Conference Venue', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': 'Conference Venue'}, {'key': 'item_1617187187528.subitem_1599711758470.subitem_1599711775943', 'title': 'Language', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': 'ja'}, {'key': 'item_1617187187528.subitem_1599711788485', 'title': 'Conference Place', 'title_ja': 'Conference Place', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617187187528.subitem_1599711788485.subitem_1599711798761', 'title': 'Conference Place', 'title_ja': 'Conference Place', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': 'Conference Place'}, {'key': 'item_1617187187528.subitem_1599711788485.subitem_1599711803382', 'title': 'Language', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': 'ja'}, {'key': 'item_1617187187528.subitem_1599711813532', 'title': 'Conference Country', 'title_ja': 'Conference Country', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': 'JPN'}, {'key': 'item_1617605131499', 'title': 'File', 'title_ja': 'File', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': True}, 'value': ''}, {'key': 'item_1617605131499.filename', 'title': '表示名', 'title_ja': 'FileName', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617605131499.url', 'title': '本文URL', 'title_ja': 'Text URL', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617605131499.url.url', 'title': '本文URL', 'title_ja': 'Text URL', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617605131499.url.label', 'title': 'ラベル', 'title_ja': 'Label', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617605131499.url.objectType', 'title': 'オブジェクトタイプ', 'title_ja': 'Object Type', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617605131499.format', 'title': 'フォーマット', 'title_ja': 'Format', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617605131499.filesize', 'title': 'サイズ', 'title_ja': 'Size', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617605131499.filesize.value', 'title': 'サイズ', 'title_ja': 'Size', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617605131499.fileDate', 'title': '日付', 'title_ja': 'Date', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617605131499.fileDate.fileDateType', 'title': '日付タイプ', 'title_ja': 'Date Type', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617605131499.fileDate.fileDateValue', 'title': '日付', 'title_ja': 'Date', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617605131499.version', 'title': 'バージョン情報', 'title_ja': 'Version Information', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617605131499.displaytype', 'title': '表示形式', 'title_ja': 'Preview', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617605131499.licensetype', 'title': 'ライセンス', 'title_ja': 'License', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617605131499.licensefree', 'title': '', 'title_ja': '自由ライセンス', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617605131499.accessrole', 'title': 'アクセス', 'title_ja': 'Access', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617605131499.date[0].dateValue', 'title': '公開日', 'title_ja': 'Opendate', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617605131499.groups', 'title': 'グループ', 'title_ja': 'Group', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'item_1617620223087', 'title': 'Heading', 'title_ja': 'Heading', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'crtf': False, 'hidden': False, 'oneline': False, 'multiple': True, 'required': False, 'showlist': False}, 'value': ''}, {'key': 'item_1617620223087.subitem_1565671149650', 'title': 'Language', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'ja-,- en'}, {'key': 'item_1617620223087.subitem_1565671169640', 'title': 'Banner Headline', 'title_ja': 'Banner Headline', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'Banner Headline-,- Banner Headline'}, {'key': 'item_1617620223087.subitem_1565671178623', 'title': 'Subheading', 'title_ja': 'Subheading', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False}, 'value': 'Subheading-,- Subheding'}, {'key': 'system_identifier_doi', 'title': 'Persistent Identifier(DOI)', 'title_ja': 'Persistent Identifier(DOI)', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'parentkey.subitem_systemidt_identifier', 'title': 'SYSTEMIDT Identifier', 'title_ja': 'SYSTEMIDT Identifier', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'parentkey.subitem_systemidt_identifier_type', 'title': 'SYSTEMIDT Identifier Type', 'title_ja': 'SYSTEMIDT Identifier Type', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'system_identifier_hdl', 'title': 'Persistent Identifier(HDL)', 'title_ja': 'Persistent Identifier(HDL)', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'parentkey.subitem_systemidt_identifier', 'title': 'SYSTEMIDT Identifier', 'title_ja': 'SYSTEMIDT Identifier', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'parentkey.subitem_systemidt_identifier_type', 'title': 'SYSTEMIDT Identifier Type', 'title_ja': 'SYSTEMIDT Identifier Type', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'system_identifier_uri', 'title': 'Persistent Identifier(URI)', 'title_ja': 'Persistent Identifier(URI)', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'parentkey.subitem_systemidt_identifier', 'title': 'SYSTEMIDT Identifier', 'title_ja': 'SYSTEMIDT Identifier', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'parentkey.subitem_systemidt_identifier_type', 'title': 'SYSTEMIDT Identifier Type', 'title_ja': 'SYSTEMIDT Identifier Type', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'system_file', 'title': 'File Information', 'title_ja': 'File Information', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'parentkey.subitem_systemfile_filename', 'title': 'SYSTEMFILE Filename', 'title_ja': 'SYSTEMFILE Filename', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'parentkey.subitem_systemfile_filename.subitem_systemfile_filename_label', 'title': 'SYSTEMFILE Filename Label', 'title_ja': 'SYSTEMFILE Filename Label', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'parentkey.subitem_systemfile_filename.subitem_systemfile_filename_type', 'title': 'SYSTEMFILE Filename Type', 'title_ja': 'SYSTEMFILE Filename Type', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'parentkey.subitem_systemfile_filename.subitem_systemfile_filename_uri', 'title': 'SYSTEMFILE Filename URI', 'title_ja': 'SYSTEMFILE Filename URI', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'parentkey.subitem_systemfile_mimetype', 'title': 'SYSTEMFILE MimeType', 'title_ja': 'SYSTEMFILE MimeType', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'parentkey.subitem_systemfile_size', 'title': 'SYSTEMFILE Size', 'title_ja': 'SYSTEMFILE Size', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'parentkey.subitem_systemfile_datetime', 'title': 'SYSTEMFILE DateTime', 'title_ja': 'SYSTEMFILE DateTime', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'parentkey.subitem_systemfile_datetime.subitem_systemfile_datetime_date', 'title': 'SYSTEMFILE DateTime Date', 'title_ja': 'SYSTEMFILE DateTime Date', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'parentkey.subitem_systemfile_datetime.subitem_systemfile_datetime_type', 'title': 'SYSTEMFILE DateTime Type', 'title_ja': 'SYSTEMFILE DateTime Type', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}, {'key': 'parentkey.subitem_systemfile_version', 'title': 'SYSTEMFILE Version', 'title_ja': 'SYSTEMFILE Version', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': None, 'value': ''}]
    hide_email_flag=False
    author_key='item_1617186419668'
    creates=[{'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ\t タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho\t Taro', 'creatorNameLang': 'en'}], 'creatorAffiliations': [{'affiliationNames': [{'affiliationName': 'University', 'affiliationNameLang': 'en'}], 'affiliationNameIdentifiers': [{'affiliationNameIdentifierURI': 'http://isni.org/isni/0000000121691048', 'affiliationNameIdentifier': '0000000121691048', 'affiliationNameIdentifierScheme': 'ISNI'}]}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifierScheme': 'WEKO', 'nameIdentifier': '4'}, {'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifier': 'xxxxxxx'}, {'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifier': 'xxxxxxx'}, {'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://nrid.nii.ac.jp/nrid/xxxxxxx', 'nameIdentifier': 'xxxxxxx'}]}, {'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ\t タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho\t Taro', 'creatorNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/yyyyyy', 'nameIdentifier': 'yyyyyy'}, {'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/author/yyyyyy', 'nameIdentifier': 'yyyyyy'}, {'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://nrid.nii.ac.jp/nrid/yyyyyy', 'nameIdentifier': 'yyyyyy'}]}, {'creatorMails': [{'creatorMail': 'wekosoftware@nii.ac.jp'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ\t タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho\t Taro', 'creatorNameLang': 'en'}], 'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifierScheme': 'ORCID', 'nameIdentifierURI': 'https://orcid.org/zzzzzzz', 'nameIdentifier': 'zzzzzzz'}, {'nameIdentifierScheme': 'CiNii', 'nameIdentifierURI': 'https://ci.nii.ac.jp/author/zzzzzzz', 'nameIdentifier': 'zzzzzzz'}, {'nameIdentifierScheme': 'KAKEN2', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifier': 'zzzzzzz'}]}]
    res = get_show_list_author(solst_dict_array, hide_email_flag, author_key, creates)
    assert res==[{'creatorName': ['Joho\t Taro'], 'familyName': ['Joho'], 'givenName': ['Taro'], 'affiliationName': ['University']},
                 {'creatorName': ['Joho\t Taro'], 'familyName': ['Joho'], 'givenName': ['Taro']},
                 {'creatorName': ['Joho\t Taro'], 'familyName': ['Joho'], 'givenName': ['Taro']}]

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
    assert res==[{'creatorName': ['en_name'], 'affiliationName': ['en_af'], 'creatorAlternative': ['en_al']}]

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

    with patch("weko_records.utils.get_value_by_selected_lang", return_value="test"):
        res = get_author_has_language(_create, {}, 'en', ['test1', 'test1'])
        assert res=={'test1': ['test']}

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

# .tox/c1/bin/pytest --cov=weko_records tests/test_utils.py::test_add_author2 -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_add_author_test(app):
    author_data={'creatorName': ['Joho\t Taro', 'Joho\t Taro', 'Joho\t Taro'], 'familyName': ['Joho', 'Joho', 'Joho'], 'givenName': ['Taro', 'Taro', 'Taro'], 'affiliationName': ['University']}
    stt_key=['item_1617186331708', 'item_1617186385884', 'nameIdentifierScheme', 'nameIdentifierURI', 'nameIdentifier', 'creatorName', 'familyName', 'givenName', 'affiliationNameIdentifier', 'affiliationNameIdentifierScheme', 'affiliationNameIdentifierURI', 'affiliationName']
    is_specify_newline_array=[{'item_1617186331708.subitem_1551255648112': False}, {'item_1617186385884.subitem_1551255721061': False}, {'nameIdentifierScheme': True}, {'nameIdentifierURI': True}, {'nameIdentifier': True}, {'creatorName': True}, {'familyName': True}, {'givenName': True}, {'affiliationNameIdentifier': True}, {'affiliationNameIdentifierScheme': True}, {'affiliationNameIdentifierURI': True}, {'affiliationName': True}]
    s={'key': 'item_1617186419668.creatorAffiliations.affiliationNames.affiliationNameLang', 'title': '言語', 'title_ja': 'Language', 'option': {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, 'parent_option': {'required': False, 'show_list': True, 'specify_newline': True, 'hide': False}, 'value': 'en'}
    value='en'
    data_result={'item_1617186331708': {'lang': ['ja', ' en'], 'lang_id': 'item_1617186331708.subitem_1551255648112'}, 'item_1617186385884': {'lang': ['en', ' ja'], 'lang_id': 'item_1617186385884.subitem_1551255721061'}, 'nameIdentifierScheme': {'nameIdentifierScheme': {'value': ['WEKO-,- ORCID-,- CiNii-,- KAKEN2-,- ORCID-,- CiNii-,- KAKEN2-,- ORCID-,- CiNii-,- KAKEN2']}}, 'nameIdentifierURI': {'nameIdentifierURI': {'value': ['https://orcid.org/-,- https://ci.nii.ac.jp/-,- https://kaken.nii.ac.jp/-,- https://orcid.org/-,- https://ci.nii.ac.jp/-,- https://kaken.nii.ac.jp/-,- https://orcid.org/-,- https://ci.nii.ac.jp/-,- https://kaken.nii.ac.jp/']}}, 'nameIdentifier': {'nameIdentifier': {'value': ['4-,- xxxxxxx-,- xxxxxxx-,- zzzzzzz-,- xxxxxxx-,- xxxxxxx-,- zzzzzzz-,- xxxxxxx-,- xxxxxxx-,- zzzzzzz']}}, 'creatorName': {'creatorName': {'value': ['Joho\t Taro', 'Joho\t Taro', 'Joho\t Taro']}}, 'familyName': {'familyName': {'value': ['Joho', 'Joho', 'Joho']}}, 'givenName': {'givenName': {'value': ['Taro', 'Taro', 'Taro']}}, 'affiliationNameIdentifier': {'affiliationNameIdentifier': {'value': ['0000000121691048']}}, 'affiliationNameIdentifierScheme': {'affiliationNameIdentifierScheme': {'value': ['ISNI']}}, 'affiliationNameIdentifierURI': {'affiliationNameIdentifierURI': {'value': ['http://isni.org/isni/0000000121691048']}}, 'affiliationName': {'affiliationName': {'value': ['University']}}}
    is_specify_newline=True
    is_hide=False
    is_show_list=True

    stt_key2=['item_1617186331708', 'item_1617186385884', 'nameIdentifierScheme', 'nameIdentifierURI', 'nameIdentifier', 'creatorName', 'familyName', 'givenName', 'affiliationNameIdentifier', 'affiliationNameIdentifierScheme', 'affiliationNameIdentifierURI', 'affiliationName']
    data_result2={'item_1617186331708': {'lang': ['ja', ' en'], 'lang_id': 'item_1617186331708.subitem_1551255648112'}, 'item_1617186385884': {'lang': ['en', ' ja'], 'lang_id': 'item_1617186385884.subitem_1551255721061'}, 'nameIdentifierScheme': {'nameIdentifierScheme': {'value': ['WEKO-,- ORCID-,- CiNii-,- KAKEN2-,- ORCID-,- CiNii-,- KAKEN2-,- ORCID-,- CiNii-,- KAKEN2']}}, 'nameIdentifierURI': {'nameIdentifierURI': {'value': ['https://orcid.org/-,- https://ci.nii.ac.jp/-,- https://kaken.nii.ac.jp/-,- https://orcid.org/-,- https://ci.nii.ac.jp/-,- https://kaken.nii.ac.jp/-,- https://orcid.org/-,- https://ci.nii.ac.jp/-,- https://kaken.nii.ac.jp/']}}, 'nameIdentifier': {'nameIdentifier': {'value': ['4-,- xxxxxxx-,- xxxxxxx-,- zzzzzzz-,- xxxxxxx-,- xxxxxxx-,- zzzzzzz-,- xxxxxxx-,- xxxxxxx-,- zzzzzzz']}}, 'creatorName': {'creatorName': {'value': ['Joho\t Taro', 'Joho\t Taro', 'Joho\t Taro']}}, 'familyName': {'familyName': {'value': ['Joho', 'Joho', 'Joho']}}, 'givenName': {'givenName': {'value': ['Taro', 'Taro', 'Taro']}}, 'affiliationNameIdentifier': {'affiliationNameIdentifier': {'value': ['0000000121691048']}}, 'affiliationNameIdentifierScheme': {'affiliationNameIdentifierScheme': {'value': ['ISNI']}}, 'affiliationNameIdentifierURI': {'affiliationNameIdentifierURI': {'value': ['http://isni.org/isni/0000000121691048']}}, 'affiliationName': {'affiliationName': {'value': ['University']}}}
    newline_array=[{'item_1617186331708.subitem_1551255648112': False}, {'item_1617186385884.subitem_1551255721061': False}, {'nameIdentifierScheme': True}, {'nameIdentifierURI': True}, {'nameIdentifier': True}, {'creatorName': True}, {'familyName': True}, {'givenName': True}, {'affiliationNameIdentifier': True}, {'affiliationNameIdentifierScheme': True}, {'affiliationNameIdentifierURI': True}, {'affiliationName': True}]
    _stt_key, _data_result, _newline_array = add_author(author_data,stt_key,is_specify_newline_array,s,value,data_result,is_specify_newline,is_hide,is_show_list)
    assert stt_key2 == _stt_key
    assert data_result2 == _data_result
    assert newline_array == _newline_array


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
def test_add_biographic(app):
    def get_bibliographic_list(x):
        return x

    sys_bibliographic = MagicMock()
    sys_bibliographic.get_bibliographic_list = get_bibliographic_list
    bibliographic_key = "test"
    s = {"key": "key"}
    stt_key = []
    data_result = {}
    is_specify_newline_array = []

    with patch("weko_records.utils.convert_bibliographic", return_value="test"):
        add_biographic(
            sys_bibliographic=sys_bibliographic,
            bibliographic_key=bibliographic_key,
            s=s,
            stt_key=stt_key,
            data_result=data_result,
            is_specify_newline_array=is_specify_newline_array
        )

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

