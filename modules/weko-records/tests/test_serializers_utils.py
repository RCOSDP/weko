import pytest
from tests.helpers import json_data

from invenio_pidstore.models import PersistentIdentifier
from weko_records.api import ItemTypeProps, ItemTypes, Mapping
from weko_records.models import ItemTypeName
from weko_records.serializers.utils import (
    get_mapping,
    get_full_mapping,
    get_mapping_inactive_show_list,
    get_metadata_from_map,
    get_attribute_schema,
    get_item_type_name_id,
    get_item_type_name,
    OpenSearchDetailData)

# def get_mapping(item_type_mapping, mapping_type):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_utils.py::test_get_mapping -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_mapping():
    mapping = json_data("data/item_type_mapping.json")
    result = get_mapping(mapping, 'jpcoar_mapping')
    data = json_data("data/get_mapping.json")
    assert result == data

# def get_full_mapping(item_type_mapping, mapping_type):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_utils.py::test_get_full_mapping -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_full_mapping():
    mapping = json_data("data/item_type_mapping.json")
    result = get_full_mapping(mapping, 'jpcoar_mapping')
    data = json_data("data/get_fll_mapping.json")
    assert result == data

# def get_mapping_inactive_show_list(item_type_mapping, mapping_type):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_utils.py::test_get_mapping_inactive_show_list -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_mapping_inactive_show_list():
    mapping = json_data("data/item_type_mapping.json")
    result = get_mapping_inactive_show_list(mapping, 'jpcoar_mapping')
    data = json_data("data/get_mapping_inactive_show_list.json")
    assert result == data

# def get_metadata_from_map(item_data, item_id):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_utils.py::test_get_metadata_from_map -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_metadata_from_map(meta):
    _item_id = 'pubdate'
    result = get_metadata_from_map(meta[0]['pubdate'], _item_id)
    assert result == {'pubdate': '2021-10-26'}
    _item_id = 'item_1551264308487'
    result = get_metadata_from_map(meta[0]['item_1551264308487'], _item_id)
    assert result == {'item_1551264308487.subitem_1551255647225': ['タイトル日本語', 'Title'], 'item_1551264308487.subitem_1551255648112': ['ja', 'en']}

# def get_attribute_schema(schema_id):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_utils.py::test_get_attribute_schema -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_attribute_schema(db):
    _prop = ItemTypeProps.create(
        property_id=1,
        name='prop1',
        schema={'item1': {}},
        form_single={'key': 'item1'},
        form_array=[{'key': 'item1'}]
    )

    result = get_attribute_schema(1)
    assert result == {'item1': {}}
    result = get_attribute_schema(2)
    assert result == None

# def get_item_type_name_id(item_type_id):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_utils.py::test_get_item_type_name_id -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_item_type_name_id(db, item_type):
    result = get_item_type_name_id(1)
    assert result == 1
    result = get_item_type_name_id(2)
    assert result == 0

# def get_item_type_name(item_type_id):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_utils.py::test_get_item_type_name -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_item_type_name(db, item_type):
    result = get_item_type_name(1)
    assert result == 'test'
    result = get_item_type_name(2)
    assert result == None

# class OpenSearchDetailData:
#     def output_open_search_detail_data(self):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_utils.py::test_open_search_detail_data -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
params=[
    ("data/item_type/item_type_render1.json",
     "data/item_type/item_type_form1.json",
     "data/item_type/item_type_mapping1.json",
     "data/record_hit/record_hit1.json",
     True)]
@pytest.mark.parametrize("render, form, mapping, hit, licence", params)
def test_open_search_detail_data(app, db, db_index, render, form, mapping, hit, licence):
    def fetcher(obj_uuid, data):
        assert obj_uuid in ['a', 'b']
        return PersistentIdentifier(pid_type='recid', pid_value=data['pid'])

    _item_type_name=ItemTypeName(name="test")
    _item_type = ItemTypes.create(
        name="test",
        item_type_name=_item_type_name,
        schema=json_data("data/item_type/item_type_schema.json"),
        render=json_data(render),
        form=json_data(form),
        tag=1
    )
    _item_type_mapping = Mapping.create(
        item_type_id=_item_type.id,
        mapping=json_data(mapping)
    )
    _search_result = {'hits': {'total': 1, 'hits': [json_data(hit)]}}
    data = OpenSearchDetailData(fetcher, _search_result, 'rss')
    with app.test_request_context():
        assert data.output_open_search_detail_data()
