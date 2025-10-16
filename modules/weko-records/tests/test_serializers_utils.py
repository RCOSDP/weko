import pytest
import copy
from lxml import etree
from mock import patch, MagicMock
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
def test_get_mapping(app, db, item_type, item_type_mapping):
    # mapping = json_data("data/item_type_mapping.json")
    result = get_mapping(1, 'jpcoar_mapping')
    assert result == {"item.@value": "item_1.interim"}

    result = get_mapping(1, 'jpcoar_mapping', item_type=item_type)
    assert result == {"item.@value": "item_1.interim"}

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

    item_data_1 = {
        "attribute_name": "Title",
        "attribute_value_mlt": [
            {
                "subitem_1551255647225": "タイトル日本語",
                "subitem_1551255648112": "ja"
            },
            {
                "subitem_1551255647225": "Title",
                "subitem_1551255648112": "en"
            },
            {
                "test": [{"test": ["test"]}],
                "test": [{"test": "test"}]
            },
        ],
    }
    item_data_2 = {
        "attribute_name": "Title",
        "attribute_value_mlt": {
            "test": [{"test": [{"key": "values"}]}],
        },
    }
    item_data_3 = {
        "attribute_name": "Title",
        "attribute_value_mlt": {
            "test": [{"test": [{"test": {"test": "test"}}]}],
        },
    }

    get_metadata_from_map(item_data_1, _item_id)
    get_metadata_from_map(item_data_2, _item_id)
    get_metadata_from_map(item_data_3, _item_id)

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

sample = OpenSearchDetailData(
    pid_fetcher = MagicMock(),
    search_result = MagicMock(),
    output_type = "atom",
    links = MagicMock(),
    item_links_factory = MagicMock(),
    kwargs = MagicMock(),
)

# class OpenSearchDetailData:
#     def output_open_search_detail_data(self): 
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_utils.py::test_output_open_search_detail_data -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_output_open_search_detail_data(app):
    with app.test_request_context():
        assert_str = '<title xmlns="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/" xmlns:prism="http://prismstandard.org/namespaces/basic/2.0/">WEKO OpenSearch: </title>'
        res = sample.output_open_search_detail_data()
        _tree = etree.fromstring(res)
        _record = str(etree.tostring(_tree.findall('title', namespaces=_tree.nsmap)[0]),"utf-8").replace('\n  ', '')
        assert _record == str(etree.tostring(etree.fromstring(assert_str)),"utf-8")


#     def _set_publication_date(self, fe, item_map, item_metadata):
def test__set_publication_date(app):
    sample_copy = copy.deepcopy(sample)
    fe = MagicMock()

    item_map = {
        "date.@value": "date.@value",
        "date.@attributes.dateType": "date.@attributes.dateType"
    }

    item_metadata = {"date": "date"}

    with patch("weko_records.serializers.utils.get_metadata_from_map", return_value=["date"]):
        sample_copy._set_publication_date(fe=fe, item_map=item_map, item_metadata=item_metadata)
    
    with patch("weko_records.serializers.utils.get_metadata_from_map", return_value={"date.@value": "date.@value"}):
        sample_copy._set_publication_date(fe=fe, item_map=item_map, item_metadata=item_metadata)
    
    with patch("weko_records.serializers.utils.get_metadata_from_map", return_value={"date.@value": ["date.@value"]}):
        sample_copy._set_publication_date(fe=fe, item_map=item_map, item_metadata=item_metadata)

    sample_copy.output_type = "test"
    sample_copy._set_publication_date(fe=fe, item_map=item_map, item_metadata=item_metadata)

    data1 = {
        "date.@attributes.dateType": ["Issued"],
        "date.@value": ["Issued"],
    }

    with patch("weko_records.serializers.utils.get_metadata_from_map", return_value=data1):
        sample_copy._set_publication_date(fe=fe, item_map=item_map, item_metadata=item_metadata)

    data2 = {
        "date.@attributes.dateType": "Issued",
        "date.@value": "Issued",
    }

    with patch("weko_records.serializers.utils.get_metadata_from_map", return_value=data2):
        sample_copy._set_publication_date(fe=fe, item_map=item_map, item_metadata=item_metadata)
    

#     def _set_source_identifier(self, fe, item_map, item_metadata):
def test__set_source_identifier(app):
    sample_copy = copy.deepcopy(sample)
    fe = MagicMock()
    fe.prism = MagicMock()

    def issn(item):
        return item
    
    fe.prism.issn = issn

    item_map = {
        "date.@value": "date.@value",
        "date.@attributes.dateType": "date.@attributes.dateType",
        "sourceIdentifier.@value": "sourceIdentifier",
        "sourceIdentifier.@attributes.identifierType": "sourceIdentifier.@attributes.identifierType",
    }

    item_metadata = {
        "sourceIdentifier": "sourceIdentifier",
        "@value": "@value",
        "sourceIdentifier.@value": "sourceIdentifier",
        "sourceIdentifier.@attributes.identifierType": "sourceIdentifier.@attributes.identifierType",
    }

    assert sample_copy._set_source_identifier(fe=fe, item_map=item_map, item_metadata=item_metadata) == None

    item_metadata["sourceIdentifier"] = {
        "sourceIdentifier": "sourceIdentifier",
    }

    item_metadata["@value"] = {
        "@value": "@value",
    }

    with patch("weko_records.serializers.utils.get_metadata_from_map", return_value=item_metadata):
        assert sample_copy._set_source_identifier(fe=fe, item_map=item_map, item_metadata=item_metadata) == None
    
    item_metadata["sourceIdentifier"] = [
        "sourceIdentifier"
    ]

    with patch("weko_records.serializers.utils.get_metadata_from_map", return_value=item_metadata):
        assert sample_copy._set_source_identifier(fe=fe, item_map=item_map, item_metadata=item_metadata) == None
    
    sample_copy.output_type = "not_atom"
    item_metadata["sourceIdentifier"] = "ISSN"

    with patch("weko_records.serializers.utils.get_metadata_from_map", return_value=item_metadata):
        assert sample_copy._set_source_identifier(fe=fe, item_map=item_map, item_metadata=item_metadata) == None

        item_metadata["sourceIdentifier.@attributes.identifierType"] = ["ISSN"]
        item_metadata["sourceIdentifier"] = ["ISSN"]

        assert sample_copy._set_source_identifier(fe=fe, item_map=item_map, item_metadata=item_metadata) == None
    

#     def _set_author_info(self, fe, item_map, item_metadata, request_lang):
def test__set_author_info(app):
    sample_copy = copy.deepcopy(sample)
    fe = MagicMock()

    item_map = {
        "creator.creatorName.@value": "creator.creatorName.@value",
    }

    item_metadata = {
        "creator.creatorName.@value": "creator.creatorName.@value",
        "creator": "creator.creatorName.@value",
        "creatorName": "creator.creatorName.@value",
        "creator.creatorNameLang": ["en"],
    }

    request_lang = "en"

    assert sample_copy._set_author_info(fe=fe, item_map=item_map, item_metadata=item_metadata, request_lang=request_lang) == None

    with patch("weko_records.serializers.utils.get_metadata_from_map", return_value=item_metadata):
        assert sample_copy._set_author_info(fe=fe, item_map=item_map, item_metadata=item_metadata, request_lang=request_lang) == None

        request_lang = False

        assert sample_copy._set_author_info(fe=fe, item_map=item_map, item_metadata=item_metadata, request_lang=request_lang) == None

        item_metadata["creator.creatorNameLang"] = "en"

        assert sample_copy._set_author_info(fe=fe, item_map=item_map, item_metadata=item_metadata, request_lang=request_lang) == None

        request_lang = "en"

        assert sample_copy._set_author_info(fe=fe, item_map=item_map, item_metadata=item_metadata, request_lang=request_lang) == None


# def _set_publisher(self, fe, item_map, item_metadata, request_lang): 
def test__set_publisher(app):
    sample_copy = copy.deepcopy(sample)
    fe = MagicMock()

    item_map = {
        "publisher.@value": "publisher.@value",
        "publisher.@attributes.xml:lang": "publisher.@attributes.xml:lang",
    }

    item_metadata = {
        "publisher": {
            "attribute_value_mlt": "attribute_value_mlt",
        },
        "@value": "test2",
    }

    request_lang = "publisher.@value"

    data1 = [["en", "publisher.@value"]]

    with patch("weko_records_ui.utils.get_pair_value", return_value=data1):
        assert sample_copy._set_publisher(fe=fe, item_map=item_map, item_metadata=item_metadata, request_lang=request_lang) == None


# def _set_description(self, fe, item_map, item_metadata, request_lang):
def test__set_description(app):
    sample_copy = copy.deepcopy(sample)
    fe = MagicMock()

    item_map = {
        "description.@value": "description.@value",
        "description.@attributes.xml:lang": "description.@attributes.xml:lang",
    }

    item_metadata = {
        "description": {
            "attribute_value_mlt": "attribute_value_mlt",
        },
        "@value": "test2",
    }

    request_lang = "description.@value"

    data1 = [["en", "description.@value"]]

    with patch("weko_records_ui.utils.get_pair_value", return_value=data1):
        assert sample_copy._set_description(fe=fe, item_map=item_map, item_metadata=item_metadata, request_lang=request_lang) == None


