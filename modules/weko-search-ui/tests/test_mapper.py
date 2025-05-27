import pytest
import xmltodict
import uuid
from datetime import date
from mock import patch
from unittest.mock import MagicMock
from collections import OrderedDict

from weko_records.api import Mapping
from weko_records.models import ItemType,ItemTypeName
from weko_records.serializers.utils import get_full_mapping
from weko_search_ui.mapper import (
    get_subitem_text_key,
    get_subitem_lang_key,
    subitem_recs,
    parsing_metadata,
    add_title,
    add_alternative,
    add_creator_jpcoar,
    add_contributor_jpcoar,
    add_access_right,
    add_right,
    add_subject,
    add_description,
    add_publisher,
    add_publisher_jpcoar,
    add_date,
    add_date_dcterms,
    add_language,
    add_version,
    add_version_type,
    add_identifier_registration,
    add_temporal,
    add_source_identifier,
    add_source_title,
    add_volume,
    add_issue,
    add_num_page,
    add_page_start,
    add_page_end,
    add_dissertation_number,
    add_date_granted,
    add_edition,
    add_volumeTitle,
    add_originalLanguage,
    add_extent,
    add_format,
    add_holdingAgent,
    add_datasetSeries,
    add_resource_type,
    add_relation,
    add_geo_location,
    add_degree_grantor,
    add_degree_name,
    add_conference,
    add_funding_reference,
    add_rights_holder,
    add_file,
    add_identifier,
    add_catalog,
    BaseMapper,
    JPCOARV2Mapper,
    JsonMapper,
    JsonLdMapper
)
from .helpers import json_data

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp

# def get_subitem_text_key(*element_names)
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_get_subitem_text_key -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    ["keywords", "expected_key"],
    [
        pytest.param(["item", "subitem"], "item.subitem.#text"),
        pytest.param([], "")
    ],
)
def test_get_subitem_text_key(keywords, expected_key):
    assert get_subitem_text_key(*keywords) == expected_key


# def get_subitem_lang_key(*element_names)
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_get_subitem_lang_key -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    ["keywords", "expected_key"],
    [
        pytest.param(["item", "subitem"], "item.subitem.@xml:lang"),
        pytest.param([], "")
    ],
)
def test_get_subitem_lang_key(keywords, expected_key):
    assert get_subitem_lang_key(*keywords) == expected_key


# def subitem_recs(schema, keys, value, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_subitem_recs -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_subitem_recs(app):
    # Case01: "items.perperty" in schema. len(keys) > 2,_subitem is not false
    schema = {"items":{"properties":{"item_key1":{'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'subitem_1551256006332': {'type': 'string', 'title': 'Creator Given Name', 'format': 'text', 'title_i18n': {'en': 'Creator Given Name', 'ja': '作成者名'}, 'title_i18n_temp': {'en': 'Creator Given Name', 'ja': '作成者名'}}, 'subitem_1551256007414': {'enum': [None,'ja','en'], 'type': ['null', 'string'], 'title': 'Language', 'format': 'select', 'currentEnum': ['ja','en']}}}, 'title': 'Creator Given Name', 'format': 'array'}}}}
    value = "jpcoar:givenName.#text"
    keys = ["item_key1",'subitem_1551256006332']
    metadata = OrderedDict([('jpcoar:givenName', OrderedDict([('@xml:lang', 'ja'), ('#text', '太郎')]))])
    result = subitem_recs(schema, keys, value, metadata)
    assert result == [[{'subitem_1551256006332': '太郎'}]]

    # Case02: "items.perperty" in schema. len(keys) > 2,_subitem is false
    schema = {"items":{"properties":{"item_key1":{'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'subitem_1551256006332': {'type': 'string', 'title': 'Creator Given Name', 'format': 'text', 'title_i18n': {'en': 'Creator Given Name', 'ja': '作成者名'}, 'title_i18n_temp': {'en': 'Creator Given Name', 'ja': '作成者名'}}, 'subitem_1551256007414': {'enum': [None,'ja','en'], 'type': ['null', 'string'], 'title': 'Language', 'format': 'select', 'currentEnum': ['ja','en']}}}, 'title': 'Creator Given Name', 'format': 'array'}}}}
    value = "jpcoar:givenName.#text"
    keys = ["item_key1",'subitem_1551256006332']
    metadata = OrderedDict([('jpcoar:givenName', "")])
    result = subitem_recs(schema, keys, value, metadata)
    assert result == []

    # Case03: metadata.get(value[0]) is list
    value = "jpcoar:givenName.#text"
    keys = ['subitem_1551256006332']
    schema = {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'subitem_1551256006332': {'type': 'string', 'title': 'Creator Given Name', 'format': 'text', 'title_i18n': {'en': 'Creator Given Name', 'ja': '作成者名'}, 'title_i18n_temp': {'en': 'Creator Given Name', 'ja': '作成者名'}}, 'subitem_1551256007414': {'enum': [None,'ja','en'], 'type': ['null', 'string'], 'title': 'Language', 'format': 'select', 'currentEnum': ['ja','en']}}}, 'title': 'Creator Given Name', 'format': 'array'}
    metadata = OrderedDict([('jpcoar:givenName', ["太郎",OrderedDict([('@xml:lang', 'ja'), ('#text', '次郎')])])])
    result = subitem_recs(schema, keys, value, metadata)
    assert result == [{'subitem_1551256006332': '太郎'}, {'subitem_1551256006332': '次郎'}]

    # Case04: "." not in value, metadata is not str and OrderedDict
    schema = {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'subitem_1551257342360': {'type': 'string', 'title': 'Contributor Given Name', 'format': 'text', 'title_i18n': {'en': 'Contributor Given Name', 'ja': '寄与者名'}, 'title_i18n_temp': {'en': 'Contributor Given Name', 'ja': '寄与者名'}}, 'subitem_1551257343979': {'enum': [None, 'ja','en'], 'type': ['null', 'string'], 'title': 'Language', 'format': 'select', 'currentEnum': ['ja','en']}}}, 'title': 'Contributor Given Name', 'format': 'array'}
    keys = ['subitem_1551257342360']
    value = "#text"
    metadata = []
    result = subitem_recs(schema, keys, value, metadata)
    assert result == []

    # Case05: "properties" in schema
    ## len(keys) > 1
    keys = ["test_key1","test_key2"]
    schema = {"properties":{"test_key1":{"properties":{"test_key2":"value"}}}}
    metadata = OrderedDict([("#text","value")])
    result = subitem_recs(schema, keys, value, metadata)
    assert result == {'test_key2': 'value'}

    # Case06: len(keys) = 1
    keys = ["test_key"]
    schema = {"properties":{"test_key":"value"}}
    result = subitem_recs(schema, keys, value, metadata)
    assert result == {'test_key': 'value'}

    ###  "." in value, len(value.split(".")) > 2
    value = "test.#text"
    metadata = OrderedDict([("#text","value")])
    result = subitem_recs(schema, keys, value, metadata)
    assert result == {}

    #### str
    metadata = OrderedDict([("test","value")])
    result = subitem_recs(schema, keys, value, metadata)
    assert result == {"test_key":"value"}

    #### list
    metadata = OrderedDict([("test",[OrderedDict([("#text","value")]),OrderedDict([("#text","value2")])])])
    result = subitem_recs(schema, keys, value, metadata)
    assert result == {"test_key":"value"}

    #### ordereddict
    metadata = OrderedDict([("test",OrderedDict([("#text","value")]))])
    result = subitem_recs(schema, keys, value, metadata)
    assert result == {"test_key":"value"}

    #### other
    metadata = OrderedDict([("test",1)])
    result = subitem_recs(schema, keys, value, metadata)
    assert result == {}

    ## "." not in value
    ### metadata is OrderedDict
    value = "#text"
    metadata = OrderedDict([("#text","value")])
    result = subitem_recs(schema, keys, value, metadata)
    assert result == {'test_key': 'value'}

    ### metadata is not str, OrderedDict
    metadata = []
    result = subitem_recs(schema, keys, value, metadata)
    assert result == {}

    # not item_key, "." in value
    ## len(value.split(".")) > 2, value[0] not in metadata
    schema = {'type': 'string', 'title': 'Version', 'format': 'text', 'title_i18n': {'en': 'Version', 'ja': 'バージョン情報'}, 'title_i18n_temp': {'en': 'Version', 'ja': 'バージョン情報'}}
    keys = []
    value = "not_exist_key.datacite:version.#text"
    metadata = OrderedDict([("datacite:version",[OrderedDict([("#text","1.2")]),OrderedDict([("#text","1.3")])])])
    result = subitem_recs(schema, keys, value, metadata)
    assert result == None

    ## metadata.get(value[0]) is list
    value = "datacite:version.#text"
    metadata = OrderedDict([("datacite:version",[OrderedDict([("#text","1.2")]),OrderedDict([("#text","1.3")])])])
    result = subitem_recs(schema, keys, value, metadata)
    assert result == "1.2"

    ## metadata.get(value[0]) is OrderedDict
    metadata = OrderedDict([("datacite:version",OrderedDict([("#text","1.2")]))])
    result = subitem_recs(schema, keys, value, metadata)
    assert result == "1.2"

    ## metadata.get(value[0]) is not OrderedDict,list,str
    metadata = OrderedDict([("datacite:version",1)])
    result = subitem_recs(schema, keys, value, metadata)
    assert result == None

    with app.test_request_context():
        schema = {'type': 'string', 'title': 'Version', 'format': 'text', 'title_i18n': {'en': 'Version', 'ja': 'バージョン情報'}, 'title_i18n_temp': {'en': 'Version', 'ja': 'バージョン情報'}}
        keys = ["test_key"]
        result = subitem_recs(schema, keys, value, metadata)
        assert result == None


# def subitem_recs(schema, keys, value, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_subitem_recs2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    ["schema", "value", "keys", "metadata", "expected_result"],
    [
        pytest.param(
            # Case01: "items.perperty" in schema. len(keys) > 2,_subitem is not false
            {"type": "array", "items": {"type": "object", "properties": {"item_key1": {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'subitem_1551256006332': {'type': 'string', 'title': 'Creator Given Name', 'format': 'text', 'title_i18n': {'en': 'Creator Given Name', 'ja': '作成者名'}, 'title_i18n_temp': {'en': 'Creator Given Name', 'ja': '作成者名'}}, 'subitem_1551256007414': {'enum': [None,'ja','en'], 'type': ['null', 'string'], 'title': 'Language', 'format': 'select', 'currentEnum': ['ja','en']}}}, 'title': 'Creator Given Name', 'format': 'array'}}}},
            "jpcoar:givenName.#text",
            ["item_key1",'subitem_1551256006332'],
            {'jpcoar:givenName': {"@xml:lang": "ja", '#text': '太郎'}},
            [[{'subitem_1551256006332': '太郎'}]]
        ),
        pytest.param(
            # Case02: "items.perperty" in schema. len(keys) > 2,_subitem is false
            {"items":{"properties":{"item_key1":{'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'subitem_1551256006332': {'type': 'string', 'title': 'Creator Given Name', 'format': 'text', 'title_i18n': {'en': 'Creator Given Name', 'ja': '作成者名'}, 'title_i18n_temp': {'en': 'Creator Given Name', 'ja': '作成者名'}}, 'subitem_1551256007414': {'enum': [None,'ja','en'], 'type': ['null', 'string'], 'title': 'Language', 'format': 'select', 'currentEnum': ['ja','en']}}}, 'title': 'Creator Given Name', 'format': 'array'}}}},
            "jpcoar:givenName.#text",
            ["item_key1",'subitem_1551256006332'],
            {"jpcoar:givenName": ""},
            []
        ),
        pytest.param(
            # Case03: metadata.get(value[0]) is list
            {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'subitem_1551256006332': {'type': 'string', 'title': 'Creator Given Name', 'format': 'text', 'title_i18n': {'en': 'Creator Given Name', 'ja': '作成者名'}, 'title_i18n_temp': {'en': 'Creator Given Name', 'ja': '作成者名'}}, 'subitem_1551256007414': {'enum': [None,'ja','en'], 'type': ['null', 'string'], 'title': 'Language', 'format': 'select', 'currentEnum': ['ja','en']}}}, 'title': 'Creator Given Name', 'format': 'array'},
            "jpcoar:givenName.#text",
            ['subitem_1551256006332'],
            {'jpcoar:givenName': ["太郎", {'@xml:lang': 'ja', '#text': '次郎'}]},
            [{'subitem_1551256006332': '太郎'}, {'subitem_1551256006332': '次郎'}]
        ),
        pytest.param(
            # Case04: "." not in value, metadata is not str and OrderedDict
            {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'subitem_1551257342360': {'type': 'string', 'title': 'Contributor Given Name', 'format': 'text', 'title_i18n': {'en': 'Contributor Given Name', 'ja': '寄与者名'}, 'title_i18n_temp': {'en': 'Contributor Given Name', 'ja': '寄与者名'}}, 'subitem_1551257343979': {'enum': [None, 'ja','en'], 'type': ['null', 'string'], 'title': 'Language', 'format': 'select', 'currentEnum': ['ja','en']}}}, 'title': 'Contributor Given Name', 'format': 'array'},
            "#text",
            ['subitem_1551257342360'],
            [],
            []
        ),
        pytest.param(
            # Case05: "properties" in schema (len(keys) > 1)
            {"type": "object", "properties": {"test_key1": {"type": "object", "properties": {"test_key2": {"type": "string"}}}}},
            "#text",
            ["test_key1","test_key2"],
            {"#text": "value"},
            {'test_key2': 'value'}
        ),
        pytest.param(
            # Case06: "properties" in schema (len(keys) == 1)
            {"properties":{"test_key":"value"}},
            "#text",
            ["test_key"],
            {"#text": "value"},
            {'test_key': 'value'}
        ),
        pytest.param(
            # Case07: "properties" in schema (len(keys) == 1 and "." in value, len(value.split(".")) > 2)
            {"type": "object", "properties":{"test_key": {"type": "string", "format": "text"}}},
            "test.#text",
            ["test_key"],
            {"#text": "value"},
            None
        ),
        pytest.param(
            # Case08: "properties" in schema (len(keys) == 1 and "." in value, len(value.split(".")) > 2)
            #### str
            {"properties":{"test_key":"value"}},
            "test.#text",
            ["test_key"],
            {"text": "value"},
            {"test_key":"value"}
        ),
        pytest.param(
            # Case09: "properties" in schema (len(keys) == 1 and "." in value, len(value.split(".")) > 2)
            #### list
            {"properties":{"test_key":"value"}},
            "test.#text",
            ["test_key"],
            {"test": [{"#text","value"}, {"#text","value2"}]},
            None
        ),
        pytest.param(
            # Case10: "properties" in schema (len(keys) == 1 and "." in value, len(value.split(".")) > 2)
            #### dict
            {"properties":{"test_key":"value"}},
            "test.#text",
            ["test_key"],
            {"test": {"#text","value"}},
            None
        ),
        pytest.param(
            # Case11: "properties" in schema (len(keys) == 1 and "." in value, len(value.split(".")) > 2)
            #### other
            {"properties":{"test_key":"value"}},
            "test.#text",
            ["test_key"],
            {"test": 1},
            None
        ),
        pytest.param(
            # Case12: "properties" in schema (len(keys) == 1 and "." in value, len(value.split(".")) > 2)
            ## "." not in value
            ### metadata is OrderedDict
            {"properties":{"test_key":"value"}},
            "#text",
            ["test_key"],
            {"#text": "value"},
            {'test_key': 'value'}
        ),
        pytest.param(
            # Case13: "properties" in schema (len(keys) == 1 and "." in value, len(value.split(".")) > 2)
            ## "." not in value
            ### metadata is not str, OrderedDict
            {"properties":{"test_key":"value"}},
            "#text",
            ["test_key"],
            [],
            {}
        ),
        pytest.param(
            # Case14: not item_key, "." in value
            ## len(value.split(".")) > 2, value[0] not in metadata
            {'type': 'string', 'title': 'Version', 'format': 'text', 'title_i18n': {'en': 'Version', 'ja': 'バージョン情報'}, 'title_i18n_temp': {'en': 'Version', 'ja': 'バージョン情報'}},
            "not_exist_key.datacite:version.#text",
            [],
            {"datacite:version": [{"#text","1.2"}, {"#text","1.3"}]},
            None
        ),
        pytest.param(
            # Case15: not item_key, "." in value
            ## metadata.get(value[0]) is list
            {'type': 'string', 'title': 'Version', 'format': 'text', 'title_i18n': {'en': 'Version', 'ja': 'バージョン情報'}, 'title_i18n_temp': {'en': 'Version', 'ja': 'バージョン情報'}},
            "datacite:version.#text",
            [],
            {"datacite:version": [{"#text": "1.2"}, {"#text","1.3"}]},
            "1.2"
        ),
        pytest.param(
            # Case16: not item_key, "." in value
            ## metadata.get(value[0]) is OrderedDict
            {'type': 'string', 'title': 'Version', 'format': 'text', 'title_i18n': {'en': 'Version', 'ja': 'バージョン情報'}, 'title_i18n_temp': {'en': 'Version', 'ja': 'バージョン情報'}},
            "datacite:version.#text",
            [],
            {"datacite:version": {"#text","1.2"}},
            "1.2"
        ),
        pytest.param(
            # Case17: not item_key, "." in value
            ## metadata.get(value[0]) is not OrderedDict,list,str
            {'type': 'string', 'title': 'Version', 'format': 'text', 'title_i18n': {'en': 'Version', 'ja': 'バージョン情報'}, 'title_i18n_temp': {'en': 'Version', 'ja': 'バージョン情報'}},
            "datacite:version.#text",
            [],
            {"datacite:version",1},
            None
        ),
        pytest.param(
            # Case18: ?
            ## metadata.get(value[0]) is not OrderedDict,list,str
            {'type': 'string', 'title': 'Version', 'format': 'text', 'title_i18n': {'en': 'Version', 'ja': 'バージョン情報'}, 'title_i18n_temp': {'en': 'Version', 'ja': 'バージョン情報'}},
            "datacite:version.#text",
            ["test_key"],
            {"datacite:version",1},
            None
        ),
    ],
)
def test_subitem_recs2(schema, keys, value, metadata, expected_result):
    result = subitem_recs(schema, keys, value, metadata)
    if expected_result is None:
        assert result is None
    else:
        assert result == expected_result


# def parsing_metadata(mappin, props, patterns, metadata, res):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_parsing_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_parsing_metadata(db_itemtype):
    item_type = db_itemtype['item_type']
    item_type_mapping = Mapping.get_record(item_type.id)
    mappin = get_full_mapping(item_type_mapping, "jpcoar_mapping")
    props = item_type.schema.get("properties")
    metadata = [{'@xml:lang': 'ja', '#text': 'test full item'}]

    patterns = [("not_exist_key","not_exist_value")]
    # Mapping key, value set does not exists
    res = {}
    result1, result2 = parsing_metadata(mappin, props, patterns, metadata, res)
    assert result1 == None
    assert result2 == None
    assert res == {}

    patterns = [
        ('title.@value', '#text'),
        ('title.@attributes.xml:lang', '@xml:lang')
    ]

    mappin2 = {"title.@value":[".subitem_1551255647225"]}
    # item_key is false
    res = {}
    result1, result2 = parsing_metadata(mappin2, props, patterns, metadata, res)
    assert result1 == None
    assert result2 == None

    # subitems is [], mappin.get(elem) is None, subitems[0] not in item_schema
    patterns = [
        ('title.@value', '#text'),
        ('title.@attributes.xml:lang', '@xml:lang'),
        ('title.#text',"test_prop")
    ]
    mappin3 = {
        "title.@value": ["item_1551264308487"],
        "title.#text":["test_key1.test_key2"]}
    res = {}
    result1, result2 = parsing_metadata(mappin3, props, patterns, metadata, res)
    assert result1 is None
    assert result2 is None

    # submetadata is list
    metadata = [{'jpcoar:givenName': {'@xml:lang': 'ja', '#text': '太郎1'}}]
    patterns = [
        ("jpcoar:test_item1","jpcoar:givenName.#text"),
        ("jpcoar:test_item2","jpcoar:givenName.#text"),
        ("jpcoar:test_item3","jpcoar:givenName.#text")
    ]
    mappin = {
        "jpcoar:test_item1":["main_item.test_item1.item_key1.subitem_1551256006332"],
        "jpcoar:test_item2":["main_item.test_item1.item_key1.subitem_1551256006332"],
        "jpcoar:test_item3":["main_item.test_item1.item_key1.subitem_1551256006332"]
    }
    schema = {
        "main_item":{
            "type": "object",
            "properties":{
                "type": "object",
                "test_item1":{
                    "type": "object",
                    "properties":{
                        "type": "array",
                        "test_item": {
                            "items": {
                                "type": "object",
                                "properties":{
                                    "item_key1":{
                                        'type': 'array',
                                        'items': {
                                            'type': 'object',
                                            'properties': {
                                                'subitem_1551256006332': {
                                                    'type': 'string',
                                                    'format': 'text'
                                                },
                                                'subitem_1551256007414': {
                                                    'enum': [None,'ja','en'],
                                                    'type': ['null', 'string'],
                                                    'format': 'select',
                                                    'currentEnum': ['ja','en']}
                                            }
                                        },
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    submeta1 = [[{'subitem_1551256006332': '太郎1'}]]
    submeta2 = [[{'subitem_1551256006332': '太郎2'}]]
    submeta3 = [[{'subitem_1551256006332': '太郎3'}]]
    res = {}
    with patch("weko_search_ui.mapper.subitem_recs",side_effect=[submeta1,submeta2,submeta3]):
        result1, result2 = parsing_metadata(mappin, schema, patterns, metadata, res)
        assert result1 == "main_item"
        assert result2 == [{'test_item1': [[{'subitem_1551256006332': '太郎1'}], {'subitem_1551256006332': '太郎2'}, [{'subitem_1551256006332': '太郎3'}]]}]
        assert res == {"main_item": {'test_item1': [[{'subitem_1551256006332': '太郎1'}], {'subitem_1551256006332': '太郎2'}, [{'subitem_1551256006332': '太郎3'}]]}}

    # submetadata is dict
    res = {}
    metadata = OrderedDict([("#text","value")])
    patterns = [
        ("jpcoar:test_item1","#text"),
        ("jpcoar:test_item2","#text"),
    ]
    mappin = {
        "jpcoar:test_item1":["main_item.test_item1.test_key"],
        "jpcoar:test_item2":["main_item.test_item1.test_key"],
    }
    props = {
        "main_item": {
            "type": "object",
            "properties": {
                "test_item1": {
                    "type": "object",
                    "properties": {
                        "test_item": {
                            "type": "object",
                            "properties": {
                                "test_key": {
                                    "type": "string",
                                    "format": "text"
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    submeta1 = {'test_key': 'value1'}
    submeta2 = {'test_key': 'value2'}
    with patch("weko_search_ui.mapper.subitem_recs",side_effect=[submeta1,submeta2]):
        result1, result2 = parsing_metadata(mappin, props, patterns, metadata, res)
        assert result1 == "main_item"
        assert result2 == [{"test_item1":{"test_key":"value2"}}]
        assert res == {"main_item": {"test_item1":{"test_key":"value2"}}}


# def add_title(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_title -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_title(mapper_jpcoar):

    # Case01: Parse multiple title and lang
    schema, mapping, _, metadata = mapper_jpcoar("dc:title")
    res = {}
    add_title(schema, mapping, res, metadata)
    assert res == {
        "title": 'テスト用 フルアイテム',
        "item_1551264308487":[
            {'subitem_1551255647225': 'テスト用 フルアイテム', 'subitem_1551255648112': 'ja'},
            {'subitem_1551255647225': 'テストヨウ フルアイテム', 'subitem_1551255648112': 'ja-Kana'},
            {'subitem_1551255647225': 'test full item', 'subitem_1551255648112': 'en'}
        ]
    }

    # Case02: Parse title only
    res = {}
    add_title(schema, mapping, res, ["test full item1", "test full item2"])
    assert res == {
        "title": "test full item1",
        "item_1551264308487": [
            {'subitem_1551255647225': 'test full item1'},
            {'subitem_1551255647225': 'test full item2'}
        ]
    }

    # Case03: Parse single title
    res = {}
    add_title(schema, mapping, res, [{"#text": "test single title", "@xml:lang": "en"}])
    assert res == {
        "title": "test single title",
        "item_1551264308487": [
            {'subitem_1551255647225': 'test single title', 'subitem_1551255648112': 'en'}
        ]
    }

    # Case04: Parse empty title
    res = {}
    add_title(schema, mapping, res, [])
    assert res == {}

    # Case05: Check that no metadata is created if parsing fails
    with patch("weko_search_ui.mapper.parsing_metadata", return_value=(None,None)):
        res = {}
        add_title(schema, mapping, res, ["test full item"])
        assert res == {}


# def add_alternative(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_alternative -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_alternative(mapper_jpcoar):
    # Case01: Parse multiple alternative and lang
    schema, mapping, _, metadata = mapper_jpcoar("dcterms:alternative")
    res = {}
    add_alternative(schema, mapping, res, metadata)
    assert res == {
        "item_1551264326373":[
            {'subitem_1551255720400': 'その他タイトル', 'subitem_1551255721061': 'ja'},
            {'subitem_1551255720400': 'ソノタタイトル', 'subitem_1551255721061': 'ja-Kana'},
            {'subitem_1551255720400': 'other title', 'subitem_1551255721061': 'en'}
        ]
    }

    # Case02: Parse alternative (no lang attribute)
    res = {}
    add_alternative(schema, mapping, res, ["test full item1", "test full item2"])
    assert res == {
        "item_1551264326373":[
            {'subitem_1551255720400': 'test full item1'},
            {'subitem_1551255720400': 'test full item2'}
        ]
    }

    # Case03: Parse single alternative
    res = {}
    add_alternative(schema, mapping, res, [{"#text": "other single title", "@xml:lang": "en"}])
    assert res == {
        "item_1551264326373": [
            {'subitem_1551255720400': 'other single title', 'subitem_1551255721061': 'en'}
        ]
    }

    # Case04: Parse empty alternative
    res = {}
    add_alternative(schema, mapping, res, [])
    assert res == {}


# def add_creator_jpcoar(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_creator_jpcoar -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_creator_jpcoar(mapper_jpcoar):
    res = {}
    schema, mapping, _, metadata = mapper_jpcoar("jpcoar:creator")
    # add_creator_jpcoar(schema, mapping, res, metadata)
    # assert res == {
    #     "item_1551264340087": [
    #         {
    #             "subitem_1551255789000": [
    #                 {"subitem_1551255793478": "1234", "subitem_1551255795486": "https://orcid.org/1234", "subitem_1551255794292": "ORCID"}
    #             ],
    #             'subitem_1551255898956': [
    #                 {'subitem_1551255905565': 'テスト, 太郎', 'subitem_1551255907416': 'ja'},
    #                 {'subitem_1551255905565': 'test, tarou', 'subitem_1551255907416': 'en'}
    #             ],
    #             'subitem_1551255929209': [
    #                 {'subitem_1551255938498': 'テスト', 'subitem_1551255964991': 'ja'},
    #                 {'subitem_1551255938498': 'test', 'subitem_1551255964991': 'en'}
    #             ],
    #             'subitem_1551255991424': [
    #                 {'subitem_1551256006332': '太郎', 'subitem_1551256007414': 'ja'},
    #                 {'subitem_1551256006332': 'tarou', 'subitem_1551256007414': 'en'}
    #             ],
    #             'subitem_1551256025394': [
    #                 {'subitem_1551256035730': 'テスト 別郎', 'subitem_1551256055588': 'ja'},
    #                 {'subitem_1551256035730': 'test betsurou', 'subitem_1551256055588': 'en'}
    #             ],
    #             "subitem_1551256087090": [
    #                 {
    #                     "subitem_1551256089084": [
    #                         {"subitem_1551256097891": "5678", "subitem_1551256147368": "http://www.isni.org/isni/5678", "subitem_1551256145018": "ISNI"}
    #                     ],
    #                     "subitem_1551256229037": [
    #                         {"subitem_1551256259183": "東京大学", "subitem_1551256259899": "ja"},
    #                         {"subitem_1551256259183": "The University of Tokyo", "subitem_1551256259899": "en"}
    #                     ]
    #                 }, {
    #                     "subitem_1551256089084": [
    #                         {"subitem_1551256097891": "1111", "subitem_1551256147368": "http://www.isni.org/isni/1111", "subitem_1551256145018": "ISNI"}
    #                     ],
    #                     "subitem_1551256229037": [
    #                         {"subitem_1551256259183": "東北大学", "subitem_1551256259899": "ja"},
    #                         {"subitem_1551256259183": "The University of Tohoku", "subitem_1551256259899": "en"}
    #                     ]
    #                 }
    #             ]
    #         }, {
    #             "subitem_1551255789000": [
    #                 {"subitem_1551255793478": "2345", "subitem_1551255795486": "https://orcid.org/2345", "subitem_1551255794292": "ORCID"}
    #             ],
    #             'subitem_1551255898956': [
    #                 {'subitem_1551255905565': 'テスト, 次郎', 'subitem_1551255907416': 'ja'},
    #                 {'subitem_1551255905565': 'test, jiro', 'subitem_1551255907416': 'en'}
    #             ],
    #             'subitem_1551255929209': [
    #                 {'subitem_1551255938498': 'テスト', 'subitem_1551255964991': 'ja'},
    #                 {'subitem_1551255938498': 'test', 'subitem_1551255964991': 'en'}
    #             ],
    #             'subitem_1551255991424': [
    #                 {'subitem_1551256006332': '次郎', 'subitem_1551256007414': 'ja'},
    #                 {'subitem_1551256006332': 'jiro', 'subitem_1551256007414': 'en'}
    #             ],
    #             'subitem_1551256025394': [
    #                 {'subitem_1551256035730': 'テスト 別郎2', 'subitem_1551256055588': 'ja'},
    #                 {'subitem_1551256035730': 'test betsurou2', 'subitem_1551256055588': 'en'}
    #             ],
    #             "subitem_1551256087090": [
    #                 {
    #                     "subitem_1551256089084": [
    #                         {"subitem_1551256097891": "0018000<", "subitem_1551256147368": "http://www.isni.org/isni/0018000", "subitem_1551256145018": "ISNI"}
    #                     ],
    #                     "subitem_1551256229037": [
    #                         {"subitem_1551256259183": "京都大学", "subitem_1551256259899": "ja"},
    #                         {"subitem_1551256259183": "The University of Kyoto", "subitem_1551256259899": "en"}
    #                     ]
    #                 }
    #             ]
    #         }
    #     ]
    # }

    # Case04: Parse empty creator
    res = {}
    add_creator_jpcoar(schema, mapping, res, [])
    assert res == {}


# def add_contributor_jpcoar(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_contributor_jpcoar -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_contributor_jpcoar(mapper_jpcoar):
    # # Case01: parse multiple contributors
    # res = {}
    schema, mapping, _, metadata = mapper_jpcoar("jpcoar:contributor")
    # add_contributor_jpcoar(schema, mapping, res, metadata)

    # assert res == {
    #     "item_1551264418667": [
    #         {
    #             'subitem_1551257036415': 'ContactPerson',
    #             "subitem_1551257150927": [
    #                 {"subitem_1551257152742": "5678", "subitem_1551257172531": "ORCID", "subitem_1551257228080": "https://orcid.org/5678"}
    #             ],
    #             'subitem_1551257339190': [
    #                 {'subitem_1551257342360': 'smith', 'subitem_1551257343979': 'en'}
    #             ],
    #             'subitem_1551257272214': [
    #                 {'subitem_1551257314588': 'test', 'subitem_1551257316910': 'en'}
    #             ],
    #             'subitem_1551257245638': [
    #                 {'subitem_1551257276108': 'test, smith', 'subitem_1551257279831': 'en'}
    #             ],
    #             'subitem_1551257372442': [
    #                 {'subitem_1551257374288': 'other smith', 'subitem_1551257375939': 'en'}
    #             ]
    #         }
    #     ]
    # }

    # Case04: Parse empty creator
    res = {}
    add_contributor_jpcoar(schema, mapping, res, [])
    assert res == {}


# def add_access_right(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_access_right -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_access_right(mapper_jpcoar):
    # Case01: Parse access right
    schema, mapping, _, metadata = mapper_jpcoar("dcterms:accessRights")
    res = {}
    add_access_right(schema, mapping, res, metadata)
    assert res == {
        "item_1551264447183": {
            'subitem_1551257553743': 'metadata only access',
            'subitem_1551257578398': 'http://purl.org/coar/access_right/c_14cb'
        }
    }

    # Case02: Parse empty access right
    schema, mapping, _, metadata = mapper_jpcoar("dcterms:accessRights")
    res = {}
    add_access_right(schema, mapping, res, [])
    assert res == {}


# def add_right(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_right -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_right(mapper_jpcoar):
    # Case01: Parse multiple right and lang
    schema, mapping, _, metadata = mapper_jpcoar("dc:rights")
    res = {}
    add_right(schema, mapping, res, metadata)
    assert res == {
        "item_1551264629907": [
            {'subitem_1551257043769': 'テスト権利情報', 'subitem_1551257047388': 'ja', 'subitem_1551257030435': 'テスト権利情報Resource'},
            {'subitem_1551257043769': 'Creative Commons Attribution 4.0 International', 'subitem_1551257047388': 'en', 'subitem_1551257030435': 'https://creativecommons.org/licenses/by/4.0/deed.en'},
            {'subitem_1551257043769': 'Copyright (c) 1997 American Physical Society', 'subitem_1551257047388': 'en'},
        ]
    }

    # Case02: Parse rights (with no attributes)
    res = {}
    add_right(schema, mapping, res, ['テスト権利情報1', 'テスト権利情報2'])
    assert res == {
        "item_1551264629907":[
            {'subitem_1551257043769': 'テスト権利情報1'},
            {'subitem_1551257043769': 'テスト権利情報2'}
        ]
    }

    # Case03: Parse single right
    res = {}
    add_right(schema, mapping, res, [{"#text": "single rights", "@xml:lang": "en", "@rdf:resource": "sample resource"}])
    assert res == {
        "item_1551264629907": [
            {'subitem_1551257043769': 'single rights', 'subitem_1551257047388': 'en', 'subitem_1551257030435': 'sample resource'}
        ]
    }

    # Case04: Parse empty right
    res = {}
    add_right(schema, mapping, res, [])
    assert res == {}


# def add_rights_holder(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_rights_holder -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_rights_holder(mapper_jpcoar):
    # Case01: Parse multiple right holders with attributes
    schema, mapping, _, metadata = mapper_jpcoar("jpcoar:rightsHolder")
    res = {}
    add_rights_holder(schema, mapping, res, metadata)
    assert res == {
        "item_1551264767789": [
            {
                'subitem_1551257249371': [
                    {'subitem_1551257255641': 'テスト 太郎', 'subitem_1551257257683': 'ja'},
                    {'subitem_1551257255641': 'テスト タロウ', 'subitem_1551257257683': 'ja-Kana'},
                    {'subitem_1551257255641': 'test taro', 'subitem_1551257257683': 'en'}
                ],
                'subitem_1551257143244': [
                    {'subitem_1551257156244': 'ISNI', 'subitem_1551257232980': 'http://isni.org/isni/00000004043815', 'subitem_1551257145912': '0000000404381592'},
                    {'subitem_1551257156244': 'ORCID', 'subitem_1551257232980': 'https://orcid.org/0000-0001-0002-0003', 'subitem_1551257145912': '0000-0001-0003-0004'}
                ]
            }, {
                'subitem_1551257249371': [
                    {'subitem_1551257255641': 'テスト 次郎', 'subitem_1551257257683': 'ja'},
                    {'subitem_1551257255641': 'テスト ジロウ', 'subitem_1551257257683': 'ja-Kana'},
                    {'subitem_1551257255641': 'test jiro', 'subitem_1551257257683': 'en'}
                ],
                'subitem_1551257143244': [
                    {'subitem_1551257156244': 'VIAF', 'subitem_1551257232980': 'https://viaf.org/processed/NDL%7C00437663', 'subitem_1551257145912': 'NDL|00437663'},
                    {'subitem_1551257156244': 'ROR', 'subitem_1551257232980': 'https://ror.org/04z20hw90', 'subitem_1551257145912': '04z20hw90'}
                ]
            }
        ]
    }

    # Case02: Parse rights holders (with no attributes)
    xml_data = xmltodict.parse("""
        <testdocument>
            <jpcoar:rightsHolder>
                <jpcoar:nameIdentifier>0000-0001-0003-0001</jpcoar:nameIdentifier>
                <jpcoar:rightsHolderName>test rights holder name1</jpcoar:rightsHolderName>
            </jpcoar:rightsHolder>
            <jpcoar:rightsHolder>
                <jpcoar:nameIdentifier>0000-0001-0003-0002</jpcoar:nameIdentifier>
                <jpcoar:rightsHolderName>test rights holder name2</jpcoar:rightsHolderName>
            </jpcoar:rightsHolder>
        </testdocument>
    """)['testdocument']['jpcoar:rightsHolder']
    res = {}
    add_rights_holder(schema, mapping, res, xml_data)
    assert res == {
        "item_1551264767789": [
            {
                'subitem_1551257249371': [
                    {'subitem_1551257255641': 'test rights holder name1'}
                ],
                'subitem_1551257143244': [
                    {'subitem_1551257145912': '0000-0001-0003-0001'}
                ]
            }, {
                'subitem_1551257249371': [
                    {'subitem_1551257255641': 'test rights holder name2'}
                ],
                'subitem_1551257143244': [
                    {'subitem_1551257145912': '0000-0001-0003-0002'}
                ]
            },
        ]
    }

    # Case03: Parse single right holder
    res = {}
    xml_data = xmltodict.parse("""
        <testdocument>
            <jpcoar:rightsHolder>
                <jpcoar:nameIdentifier nameIdentifierScheme="ISNI"
                    nameIdentifierURI="http://isni.org/isni/00000004043815">0000000404381592</jpcoar:nameIdentifier>
                <jpcoar:rightsHolderName xml:lang="en">American Physical Society</jpcoar:rightsHolderName>
            </jpcoar:rightsHolder>
        </testdocument>
    """)['testdocument']['jpcoar:rightsHolder']
    add_rights_holder(schema, mapping, res, [xml_data])
    assert res == {
        "item_1551264767789": [
            {
                'subitem_1551257249371': [
                    {'subitem_1551257255641': 'American Physical Society', 'subitem_1551257257683': 'en'},
                ],
                'subitem_1551257143244': [
                    {'subitem_1551257156244': 'ISNI', 'subitem_1551257232980': 'http://isni.org/isni/00000004043815', 'subitem_1551257145912': '0000000404381592'},
                ]
            }
        ]
    }

    # Case04: Parse empty right holder
    res = {}
    add_rights_holder(schema, mapping, res, [])
    assert res == {}


# def add_subject(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_subject -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_subject(mapper_jpcoar):
    # Case01: Parse multiple subject and attributes
    schema, mapping, _, metadata = mapper_jpcoar("jpcoar:subject")
    res = {}
    add_subject(schema, mapping, res, metadata)
    assert res == {
        "item_1551264822581": [
            {'subitem_1551257315453': 'テスト主題', 'subitem_1551257323812': 'ja', 'subitem_1551257343002': 'http://bsh.com', 'subitem_1551257329877': 'BSH'},
            {'subitem_1551257315453': '社会情報学', 'subitem_1551257323812': 'ja', 'subitem_1551257343002': "https://id.ndl.go.jp/auth/ndlsh/01009109", 'subitem_1551257329877': 'NDLSH'},
            {'subitem_1551257315453': '007', 'subitem_1551257329877': "NDC"}
        ]
    }

    # Case02: Parse subjects (with no attributes)
    res = {}
    add_subject(schema, mapping, res, ['テスト主題1', 'テスト主題2'])
    assert res == {
        "item_1551264822581":[
            {'subitem_1551257315453': 'テスト主題1'},
            {'subitem_1551257315453': 'テスト主題2'}
        ]
    }

    # Case03: Parse single subject
    res = {}
    add_subject(schema, mapping, res, [{"#text": "single subject", "@xml:lang": "en", "@subjectScheme": "e-Rad_field", "@subjectURI": "https://sample.go.jp/01009109"}])
    assert res == {
        "item_1551264822581": [
            {'subitem_1551257315453': 'single subject', 'subitem_1551257323812': 'en', 'subitem_1551257343002': 'https://sample.go.jp/01009109', 'subitem_1551257329877': 'e-Rad_field'}
        ]
    }

    # Case04: Parse empty subject
    res = {}
    add_subject(schema, mapping, res, [])
    assert res == {}


# def add_description(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_description -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_description(mapper_jpcoar):
    # Case01: Parse multiple description and attributes
    schema, mapping, _, metadata = mapper_jpcoar("datacite:description")
    res = {}
    add_description(schema, mapping, res, metadata)
    assert res == {
        "item_1551264846237": [
            {'subitem_1551255577890': 'this is test abstract.', 'subitem_1551255592625': 'en', 'subitem_1551255637472': 'Abstract'},
            {'subitem_1551255577890': '技術情報テスト', 'subitem_1551255637472': 'TechnicalInfo'},
            {'subitem_1551255577890': 'this is test method.', 'subitem_1551255592625': 'en', 'subitem_1551255637472': 'Methods'}
        ]
    }

    # Case02: Parse description (with no attributes)
    res = {}
    add_description(schema, mapping, res, ['テスト内容記述1', 'テスト内容記述2'])
    assert res == {
        "item_1551264846237":[
            {'subitem_1551255577890': 'テスト内容記述1'},
            {'subitem_1551255577890': 'テスト内容記述2'}
        ]
    }

    # Case03: Parse single description
    res = {}
    add_description(schema, mapping, res, [{"#text": "this is test single abstract.", "@xml:lang": "en", "@descriptionType": "TableOfContents"}])
    assert res == {
        "item_1551264846237": [
            {'subitem_1551255577890': 'this is test single abstract.', 'subitem_1551255592625': 'en', 'subitem_1551255637472': 'TableOfContents'}
        ]
    }

    # Case04: Parse empty description
    res = {}
    add_description(schema, mapping, res, [])
    assert res == {}


# def add_publisher(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_publisher -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_publisher(mapper_jpcoar):
    # Case01: Parse multiple publisher and attributes
    schema, mapping, _, metadata = mapper_jpcoar("dc:publisher")
    res = {}
    add_publisher(schema, mapping, res, metadata)
    assert res == {
        "item_1551264917614": [
            {'subitem_1551255702686': 'test publisher', 'subitem_1551255710277': 'ja'},
            {'subitem_1551255702686': 'Elsevier', 'subitem_1551255710277': 'en'},
            {'subitem_1551255702686': '日本物理学会', 'subitem_1551255710277': 'ja'}
        ]
    }

    # Case02: Parse publisher (with no attributes)
    res = {}
    add_publisher(schema, mapping, res, ['テスト出版者1', 'テスト出版者2'])
    assert res == {
        "item_1551264917614":[
            {'subitem_1551255702686': 'テスト出版者1'},
            {'subitem_1551255702686': 'テスト出版者2'}
        ]
    }

    # Case03: Parse single publisher
    res = {}
    add_publisher(schema, mapping, res, [{"#text": "single publisher", "@xml:lang": "en"}])
    assert res == {
        "item_1551264917614": [
            {'subitem_1551255702686': 'single publisher', 'subitem_1551255710277': 'en'}
        ]
    }

    # Case04: Parse empty publisher
    res = {}
    add_publisher(schema, mapping, res, [])
    assert res == {}


# def add_publisher(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_publisher_jpcoar -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_publisher_jpcoar():
    schema = {
        "item_publisher_jpcoar": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "publisherName": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "format": "text"
                                },
                                "lang": {
                                    "enum": [None, "ja", "en"],
                                    "type": ["null", "string"],
                                    "format": "select",
                                    "currentEnum": ["ja", "en"]
                                }
                            }
                        }
                    },
                    "description": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "subitem_description": {
                                    "type": "string",
                                    "format": "text",
                                },
                                "lang": {
                                    "enum": [None, "ja", "en"],
                                    "type": ["null", "string"],
                                    "format": "select",
                                    "currentEnum": ["ja", "en"]
                                }
                            }
                        }
                    },
                    "location": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "subitem_location": {
                                    "type": "string",
                                    "format": "text",
                                },
                                "lang": {
                                    "enum": [None, "ja", "en"],
                                    "type": ["null", "string"],
                                    "format": "select",
                                    "currentEnum": ["ja", "en"]
                                }
                            }
                        }
                    },
                    "publicationPlace": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "subitem_publicationPlace": {
                                    "type": "string",
                                    "format": "text",
                                },
                                "lang": {
                                    "enum": [None, "ja", "en"],
                                    "type": ["null", "string"],
                                    "format": "select",
                                    "currentEnum": ["ja", "en"]
                                }
                            }
                        }
                    }
                }
            },
            "title": "Format",
            "maxItems": 9999,
            "minItems": 1
        }
    }

    mapping = {
        "publisher_jpcoar.publisherName.@value": ["item_publisher_jpcoar.publisherName.name"],
        "publisher_jpcoar.publisherName.@attributes.xml:lang": ["item_publisher_jpcoar.publisherName.lang"],
        "publisher_jpcoar.publisherDescription.@value": ["item_publisher_jpcoar.description.subitem_description"],
        "publisher_jpcoar.publisherDescription.@attributes.xml:lang": ["item_publisher_jpcoar.description.lang"],
        "publisher_jpcoar.location.@value": ["item_publisher_jpcoar.location.subitem_location"],
        "publisher_jpcoar.location.@attributes.xml:lang": ["item_publisher_jpcoar.location.lang"],
        "publisher_jpcoar.publicationPlace.@value": ["item_publisher_jpcoar.publicationPlace.subitem_publicationPlace"],
        "publisher_jpcoar.publicationPlace.@attributes.xml:lang": ["item_publisher_jpcoar.publicationPlace.lang"],
    }

    # Case01: Parse multiple publisher (with attributes)
    xml_data = xmltodict.parse("""
        <testdocument>
            <jpcoar:publisher>
                <jpcoar:publisherName xml:lang="ja">テスト出版1</jpcoar:publisherName>
                <jpcoar:publisherName xml:lang="en">test publisher1</jpcoar:publisherName>
                <jpcoar:publisherDescription xml:lang="ja">印刷</jpcoar:publisherDescription>
                <jpcoar:publisherDescription xml:lang="ja">四・五編</jpcoar:publisherDescription>
                <dcndl:location xml:lang="ja">東京</dcndl:location>
                <dcndl:location xml:lang="en">Tokyo</dcndl:location>
                <dcndl:publicationPlace xml:lang="en">JPN</dcndl:publicationPlace>
                <dcndl:publicationPlace xml:lang="en">USA</dcndl:publicationPlace>
            </jpcoar:publisher>
            <jpcoar:publisher>
                <jpcoar:publisherName xml:lang="ja">テスト出版2</jpcoar:publisherName>
                <jpcoar:publisherName xml:lang="en">test publisher2</jpcoar:publisherName>
                <jpcoar:publisherDescription xml:lang="ja">印刷</jpcoar:publisherDescription>
                <jpcoar:publisherDescription xml:lang="ja">二・六編</jpcoar:publisherDescription>
                <dcndl:location xml:lang="ja">名古屋</dcndl:location>
                <dcndl:location xml:lang="en">Nagoya</dcndl:location>
                <dcndl:publicationPlace xml:lang="en">JPN</dcndl:publicationPlace>
                <dcndl:publicationPlace xml:lang="en">USA</dcndl:publicationPlace>
            </jpcoar:publisher>
        </testdocument>
    """)['testdocument']['jpcoar:publisher']
    res = {}
    add_publisher_jpcoar(schema, mapping, res, xml_data)
    assert res == {
        "item_publisher_jpcoar": [
            {
                "publisherName": [
                    {"name": "テスト出版1", "lang": "ja"},
                    {"name": "test publisher1", "lang": "en"},
                ],
                "description": [
                    {"subitem_description": "印刷", "lang": "ja"},
                    {"subitem_description": "四・五編", "lang": "ja"},
                ],
                "location": [
                    {"subitem_location": "東京", "lang": "ja"},
                    {"subitem_location": "Tokyo", "lang": "en"},
                ],
                "publicationPlace": [
                    {"subitem_publicationPlace": "JPN", "lang": "en"},
                    {"subitem_publicationPlace": "USA", "lang": "en"},
                ]
            }, {
                "publisherName": [
                    {"name": "テスト出版2", "lang": "ja"},
                    {"name": "test publisher2", "lang": "en"},
                ],
                "description": [
                    {"subitem_description": "印刷", "lang": "ja"},
                    {"subitem_description": "二・六編", "lang": "ja"},
                ],
                "location": [
                    {"subitem_location": "名古屋", "lang": "ja"},
                    {"subitem_location": "Nagoya", "lang": "en"},
                ],
                "publicationPlace": [
                    {"subitem_publicationPlace": "JPN", "lang": "en"},
                    {"subitem_publicationPlace": "USA", "lang": "en"},
                ]
            }
        ]
    }

    # Case02: Parse publisher (without attributes)
    # xml_data = xmltodict.parse("""
    #     <testdocument>
    #         <jpcoar:publisher>
    #             <jpcoar:publisherName>テスト出版1</jpcoar:publisherName>
    #             <jpcoar:publisherName>test publisher1</jpcoar:publisherName>
    #             <jpcoar:publisherDescription>印刷</jpcoar:publisherDescription>
    #             <jpcoar:publisherDescription>四・五編</jpcoar:publisherDescription>
    #             <dcndl:location>東京</dcndl:location>
    #             <dcndl:location>Tokyo</dcndl:location>
    #             <dcndl:publicationPlace>JPN</dcndl:publicationPlace>
    #             <dcndl:publicationPlace>USA</dcndl:publicationPlace>
    #         </jpcoar:publisher>
    #         <jpcoar:publisher>
    #             <jpcoar:publisherName>テスト出版2</jpcoar:publisherName>
    #             <jpcoar:publisherName>test publisher2</jpcoar:publisherName>
    #             <jpcoar:publisherDescription>印刷</jpcoar:publisherDescription>
    #             <jpcoar:publisherDescription>二・六編</jpcoar:publisherDescription>
    #             <dcndl:location>名古屋</dcndl:location>
    #             <dcndl:location>Nagoya</dcndl:location>
    #             <dcndl:publicationPlace>JPN</dcndl:publicationPlace>
    #         </jpcoar:publisher>
    #     </testdocument>
    # """)['testdocument']['jpcoar:publisher']
    # res = {}
    # add_publisher_jpcoar(schema, mapping, res, xml_data)
    # assert res == {
    #     "item_publisher_jpcoar": [
    #         {
    #             "publisherName": [
    #                 {"name": "テスト出版1"},
    #                 {"name": "test publisher1"},
    #             ],
    #             "description": [
    #                 {"subitem_description": "印刷"},
    #                 {"subitem_description": "四・五編"},
    #             ],
    #             "location": [
    #                 {"subitem_location": "東京"},
    #                 {"subitem_location": "Tokyo"},
    #             ],
    #             "publicationPlace": [
    #                 {"subitem_publicationPlace": "JPN"},
    #                 {"subitem_publicationPlace": "USA"},
    #             ]
    #         }, {
    #             "publisherName": [
    #                 {"name": "テスト出版2"},
    #                 {"name": "test publisher2"},
    #             ],
    #             "description": [
    #                 {"subitem_description": "印刷"},
    #                 {"subitem_description": "二・六編"},
    #             ],
    #             "location": [
    #                 {"subitem_location": "名古屋"},
    #                 {"subitem_location": "Nagoya"},
    #             ],
    #             "publicationPlace": [
    #                 {"subitem_publicationPlace": "JPN"},
    #             ]
    #         }
    #     ]
    # }

    # Case03: Parse single publisher
    res = {}
    xml_data = xmltodict.parse("""
        <testdocument>
            <jpcoar:publisher>
                <jpcoar:publisherName xml:lang="ja">霞ケ関出版</jpcoar:publisherName>
                <jpcoar:publisherDescription xml:lang="ja">印刷</jpcoar:publisherDescription>
                <dcndl:location xml:lang="ja">東京</dcndl:location>
                <dcndl:publicationPlace>JPN</dcndl:publicationPlace>
            </jpcoar:publisher>
        </testdocument>
    """)['testdocument']['jpcoar:publisher']
    add_publisher_jpcoar(schema, mapping, res, [xml_data])
    assert res ==  {
        "item_publisher_jpcoar": [
            {
                "publisherName": [
                    {"name": "霞ケ関出版", "lang": "ja"},
                ],
                "description": [
                    {"subitem_description": "印刷", "lang": "ja"}
                ],
                "location": [
                    {"subitem_location": "東京", "lang": "ja"}
                ],
                "publicationPlace": [
                    {"subitem_publicationPlace": "JPN"}
                ]
            }
        ]
    }

    # Case04: Parse empty publisher
    res = {}
    add_publisher_jpcoar(schema, mapping, res, [])
    assert res == {}


# def add_date(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_date -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_date(mapper_jpcoar):
    # Case01: Parse multiple publisher and attributes
    schema, mapping, _, metadata = mapper_jpcoar("datacite:date")
    res = {}
    add_date(schema, mapping, res, metadata)
    assert res == {
        "item_1551264974654": [
            {'subitem_1551255753471': '2022-10-20', 'subitem_1551255775519': 'Accepted'},
            {'subitem_1551255753471': '2022-10-19', 'subitem_1551255775519': 'Issued'},
            {'subitem_1551255753471': '2023-03-02/2023-06-02', 'subitem_1551255775519': 'Collected'},
        ]
    }

    # Case02: Parse publisher (with no attributes)
    res = {}
    add_date(schema, mapping, res, ['2022-10-20', '2022-10-19'])
    assert res == {
        "item_1551264974654":[
            {'subitem_1551255753471': '2022-10-20'},
            {'subitem_1551255753471': '2022-10-19'}
        ]
    }

    # Case03: Parse single publisher
    res = {}
    add_date(schema, mapping, res, [{"#text": "2022-10-21", "@dateType": "Copyrighted"}])
    assert res == {
        "item_1551264974654": [
            {'subitem_1551255753471': '2022-10-21', 'subitem_1551255775519': 'Copyrighted'}
        ]
    }

    # Case04: Parse empty publisher
    res = {}
    add_date(schema, mapping, res, [])
    assert res == {}


# def add_date_dcterms(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_date_dcterms -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_date_dcterms():
    schema = {
        "date_dcterms": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "format": "text",
                    },
                    "lang": {
                        "enum": [None, "ja", "en"],
                        "type": ["null", "string"],
                        "format": "select",
                        "currentEnum": ["ja", "en"]
                    }
                }
            },
            "title": "Datetime(dcterms)",
            "maxItems": 9999,
            "minItems": 1
        }
    }

    mapping = {
        "date_dcterms.@value": ["date_dcterms.date"],
        "date_dcterms.@attributes.xml:lang": ["date_dcterms.lang"]
    }

    # Case01: Parse multiple date(dc) with attributes
    xml_data = xmltodict.parse(
        """
        <testdocument>
            <dcterms:date xml:lang="zh-tw">崇禎17</dcterms:date>
            <dcterms:date xml:lang="ja">宝暦年間</dcterms:date>
            <dcterms:date xml:lang="ja">寛政壬子</dcterms:date>
        </testdocument>
        """
    )['testdocument']['dcterms:date']
    res = {}
    add_date_dcterms(schema, mapping, res, xml_data)
    assert res == {
        "date_dcterms": [
            {'date': '崇禎17', 'lang': 'zh-tw'},
            {'date': '宝暦年間', 'lang': 'ja'},
            {'date': '寛政壬子', 'lang': 'ja'}
        ]
    }

    # Case02: Parse date(dcterms) (without attributes)
    res = {}
    add_date_dcterms(schema, mapping, res, ['dc_date1', 'dc_date2'])
    assert res == {
        "date_dcterms":[
            {'date': 'dc_date1'},
            {'date': 'dc_date2'}
        ]
    }

    # Case03: Parse single date(dcterms)
    res = {}
    single_xml_data = xmltodict.parse(
        """
        <testdocument>
            <dcterms:date xml:lang="ja">享和3</dcterms:date>
        </testdocument>
        """
    )['testdocument']['dcterms:date']
    add_date_dcterms(schema, mapping, res, [single_xml_data])
    assert res == {
        "date_dcterms":[
            {'date': '享和3', 'lang': 'ja'}
        ]
    }

    # Case04: Parse empty date(dcterms)
    res = {}
    add_date_dcterms(schema, mapping, res, [])
    assert res == {}


# def add_language(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_language(mapper_jpcoar):
    # Case01: Parse multiple language and attributes
    schema, mapping, _, metadata = mapper_jpcoar("dc:language")
    res = {}
    add_language(schema, mapping, res, metadata)
    assert res == {
        "item_1551265002099": [
            {'subitem_1551255818386': 'eng'},
            {'subitem_1551255818386': 'jpn'},
            {'subitem_1551255818386': 'ger'},
        ]
    }

    # Case02: Parse single language
    res = {}
    add_language(schema, mapping, res, ['jpn'])
    assert res == {
        "item_1551265002099": [
            {'subitem_1551255818386': 'jpn'}
        ]
    }

    # Case03: Parse empty language
    res = {}
    add_language(schema, mapping, res, [])
    assert res == {}


# def add_resource_type(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_resource_type -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_resource_type(mapper_jpcoar):
    # Case01: Parse resource type
    schema, mapping, _, metadata = mapper_jpcoar("dc:type")
    res = {}
    add_resource_type(schema, mapping, res, metadata)
    assert res == {
        "item_1551265032053": {
            'resourcetype': 'newspaper',
            'resourceuri': 'http://purl.org/coar/resource_type/c_2fe3'
        }
    }

    # Case02: Parse resource type (with no attributes)
    res = {}
    add_resource_type(schema, mapping, res, ['newspaper'])
    assert res == {
        "item_1551265032053": {
            'resourcetype': 'newspaper'
        }
    }

    # Case03: Parse empty resource type
    res = {}
    add_resource_type(schema, mapping, res, [])
    assert res == {}


# def add_version(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_version -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_version(mapper_jpcoar):
    # Case01: Parse version
    schema, mapping, _, metadata = mapper_jpcoar("datacite:version")
    res = {}
    add_version(schema, mapping, res, metadata)
    assert res == {
        "item_1551265075370": {
            'subitem_1551255975405': '1.1'
        }
    }

    # Case02: Parse empty version
    res = {}
    add_version(schema, mapping, res, [])
    assert res == {}


# def add_version_type(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_version_type -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_version_type(mapper_jpcoar):
    # Case01: Parse version type
    schema, mapping, _, metadata = mapper_jpcoar("oaire:version")
    res = {}
    add_version_type(schema, mapping, res, metadata)
    assert res == {
        "item_1551265118680": {
            'subitem_1551256025676': 'AO',
            'subitem_1600292170262': 'http://purl.org/coar/version/c_b1a7d7d4d402bcce'
        }
    }

    # Case02: Parse version type (with no attributes)
    res = {}
    add_version_type(schema, mapping, res, ['VoR'])
    assert res == {
        "item_1551265118680": {
            'subitem_1551256025676': 'VoR'
        }
    }

    # Case03: Parse empty resource type
    res = {}
    add_version_type(schema, mapping, res, [])
    assert res == {}


# def add_identifier(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_identifier -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_identifier(mapper_jpcoar):
    # TODO: ref harvester
    # Case01: Parse multiple identifier and attributes
    schema, mapping, _, metadata = mapper_jpcoar("jpcoar:identifier")
    res = {}
    add_identifier(schema, mapping, res, metadata)
    assert res == {
        "item_1617186783814": [
            {'subitem_identifier_uri': '1111', 'subitem_identifier_type': 'DOI'},
            {'subitem_identifier_uri': 'https://doi.org/1234/0000000001', 'subitem_identifier_type': 'DOI'},
            {'subitem_identifier_uri': 'https://192.168.56.103/records/1', 'subitem_identifier_type': 'URI'}
        ]
    }

    # Case02: Parse identifier (with no attributes)
    res = {}
    add_identifier(schema, mapping, res, ['https://doi.org/1234/0000000002', 'https://192.168.56.103/records/2'])
    assert res == {
        "item_1617186783814":[
            {'subitem_identifier_uri': 'https://doi.org/1234/0000000002'},
            {'subitem_identifier_uri': 'https://192.168.56.103/records/2'}
        ]
    }

    # Case03: Parse single identifier
    res = {}
    add_identifier(schema, mapping, res, [{"#text": "http://hdl.handle.net/2115/64495", "@identifierType": "HDL"}])
    assert res == {
        "item_1617186783814":[
            {'subitem_identifier_uri': 'http://hdl.handle.net/2115/64495', 'subitem_identifier_type': 'HDL'}
        ]
    }

    # Case04: Parse empty identifier
    res = {}
    add_identifier(schema, mapping, res, [])
    assert res == {}


# def add_identifier_registration(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_identifier_registration -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_identifier_registration(mapper_jpcoar):
    # Case01: Parse identifier registration
    schema, mapping, _, metadata = mapper_jpcoar("jpcoar:identifierRegistration")
    res = {}
    add_identifier_registration(schema, mapping, res, metadata)
    assert res == {
        "item_1581495499605": {
            'subitem_1551256250276': '1234/0000000001',
            'subitem_1551256259586': 'JaLC'
        }
    }

    # Case02: Parse identifier registration (with no attributes)
    res = {}
    add_identifier_registration(schema, mapping, res, ['10.18926/AMO/54590'])
    assert res == {
        "item_1581495499605": {
            'subitem_1551256250276': '10.18926/AMO/54590'
        }
    }

    # Case03: Parse empty identifier registration
    res = {}
    add_identifier_registration(schema, mapping, res, [])
    assert res == {}


# def add_relation(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_relation -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_relation(mapper_jpcoar):
    # Case01: Parse multiple relations (with attributes)
    res = {}
    schema, mapping, _, metadata = mapper_jpcoar("jpcoar:relation")
    add_relation(schema, mapping, res, metadata)
    assert res == {
        "item_1551265227803": [
            {
                'subitem_1551256388439': 'isVersionOf',
                'subitem_1551256480278': [
                    {'subitem_1551256498531': '関連テスト', 'subitem_1551256513476': 'ja'},
                    {'subitem_1551256498531': 'relation test', 'subitem_1551256513476': 'en'}
                ],
                'subitem_1551256465077': [
                    {'subitem_1551256478339': '1111111', 'subitem_1551256629524': 'ARK'}
                ]
            }, {
                'subitem_1551256388439': 'isVersionOf',
                'subitem_1551256465077': [
                    {'subitem_1551256478339': 'https://192.168.56.103/records/3', 'subitem_1551256629524': 'URI'}
                ]
            }
        ]
    }

    # Case02: Parse relations (without attributes)
    # xml_data = xmltodict.parse(
    #     """
    #     <testdocument>
    #         <jpcoar:relation>
    #             <jpcoar:relatedIdentifier>https://doi.org/10.1371/journal.pone.0170224</jpcoar:relatedIdentifier>
    #         </jpcoar:relation>
    #         <jpcoar:relation>
    #             <jpcoar:relatedIdentifier>https://da.dl.itc.u-tokyo.ac.jp/portal/collection/kokubunken</jpcoar:relatedIdentifier>
    #             <jpcoar:relatedTitle>総合図書館所蔵古典籍（国文研デジタル化分）</jpcoar:relatedTitle>
    #             <jpcoar:relatedTitle>related title sample</jpcoar:relatedTitle>
    #         </jpcoar:relation>
    #     </testdocument>
    #     """
    # )['testdocument']["jpcoar:relation"]
    # res = {}
    # add_relation(schema, mapping, res, xml_data)
    # assert res == {
    #     "item_1551265227803": [
    #         {
    #             "subitem_1551256465077": [
    #                 {"subitem_1551256478339": "https://doi.org/10.1371/journal.pone.0170224"}
    #             ]
    #         }, {
    #             "subitem_1551256480278": [
    #                 {"subitem_1551256498531": "総合図書館所蔵古典籍（国文研デジタル化分）"},
    #                 {"subitem_1551256498531": "related title sample"}
    #             ],
    #             "subitem_1551256465077": [
    #                 {"subitem_1551256478339": "https://da.dl.itc.u-tokyo.ac.jp/portal/collection/kokubunken"}
    #             ]
    #         }
    #     ]
    # }

    # Case03: Parse single relation
    res = {}
    xml_data = xmltodict.parse("""
        <testdocument>
            <jpcoar:relation relationType="isFormatOf">
                <jpcoar:relatedIdentifier identifierType="NCID">BC03765035</jpcoar:relatedIdentifier>
                <jpcoar:relatedTitle xml:lang="ja">一辭題開方式省過乗明平方以下定式有無法</jpcoar:relatedTitle>
            </jpcoar:relation>
        </testdocument>
    """)['testdocument']['jpcoar:relation']
    add_relation(schema, mapping, res, [xml_data])
    assert res ==  {
        "item_1551265227803": [
            {
                "subitem_1551256388439": "isFormatOf",
                "subitem_1551256465077": [
                    {"subitem_1551256629524": "NCID", "subitem_1551256478339": "BC03765035"}
                ],
                "subitem_1551256480278": [
                    {"subitem_1551256498531": "一辭題開方式省過乗明平方以下定式有無法", "subitem_1551256513476": "ja"}
                ]
            }
        ]
    }

    # Case04: Parse empty publisher
    res = {}
    add_relation(schema, mapping, res, [])
    assert res == {}


# def add_temporal(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_temporal -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_temporal(mapper_jpcoar):
    # Case01: Parse multiple identifier and attributes
    schema, mapping, _, metadata = mapper_jpcoar("dcterms:temporal")
    res = {}
    add_temporal(schema, mapping, res, metadata)
    assert res == {
        "item_1551265302120": [
            {'subitem_1551256918211': '1 to 2', 'subitem_1551256920086': 'ja'},
            {'subitem_1551256918211': '奈良時代', 'subitem_1551256920086': 'ja'},
            {'subitem_1551256918211': 'A.D. 1800 - A.D. 1850', 'subitem_1551256920086': 'en'}
        ]
    }

    # Case02: Parse identifier (with no attributes)
    res = {}
    add_temporal(schema, mapping, res, ['飛鳥時代', 'A.D. 1700 - A.D. 1750'])
    assert res == {
        "item_1551265302120":[
            {'subitem_1551256918211': '飛鳥時代'},
            {'subitem_1551256918211': 'A.D. 1700 - A.D. 1750'}
        ]
    }

    # Case03: Parse single identifier
    res = {}
    add_temporal(schema, mapping, res, [{"#text": "A.D. 2020 - A.D. 2024", "@xml:lang": "en"}])
    assert res == {
        "item_1551265302120":[
            {'subitem_1551256918211': 'A.D. 2020 - A.D. 2024', 'subitem_1551256920086': 'en'}
        ]
    }

    # Case04: Parse empty identifier
    res = {}
    add_temporal(schema, mapping, res, [])
    assert res == {}


# def add_geo_location(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_geo_location -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_geo_location(mapper_jpcoar):
    res = {}
    schema, mapping, _, metadata = mapper_jpcoar("datacite:geoLocation")
    # add_geo_location(schema, mapping, res, metadata)
    # assert res == {
    #     "item_1570068313185": [
    #         {
    #             "subitem_1551256822219": {
    #                 "subitem_1551256831892": "45.6",
    #                 "subitem_1551256840435": "111.2",
    #                 "subitem_1551256834732": "78.9",
    #                 "subitem_1551256824945": "123",
    #             },
    #             "subitem_1551256842196": [
    #                 {"subitem_1570008213846": "テスト位置情報"}
    #             ],
    #             "subitem_1551256778926": {
    #                 "subitem_1551256814806": "67.890",
    #                 "subitem_1551256783928": "123.45",
    #             }
    #         }
    #     ]
    # }

    # Case04: Parse empty geo location
    res = {}
    add_geo_location(schema, mapping, res, [])
    assert res == {}



# def add_funding_reference(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_funding_reference -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_funding_reference(mapper_jpcoar):
    # Case01: Parse multiple funding reference and attributes
    res = {}
    schema, mapping, _, metadata = mapper_jpcoar("jpcoar:fundingReference")
    add_funding_reference(schema, mapping, res, metadata)
    assert res == {
        "item_1551265385290": [
            {
                'subitem_1551256462220': [
                    {'subitem_1551256653656': 'テスト助成機関', 'subitem_1551256657859': 'ja'}
                ],
                'subitem_1551256454316': [
                    {'subitem_1551256614960': '22222', 'subitem_1551256619706': 'Crossref Funder', "subitem_1551256619707": ""}
                ],
                'subitem_1551256688098': [
                    {'subitem_1551256691232': 'テスト研究', 'subitem_1551256694883': 'ja'}
                ],
                'subitem_1551256665850': [
                    {'subitem_1551256671920': '1111', 'subitem_1551256679403': 'https://test.research.com', "subitem_1551256671921": ""}
                ]
            }, {
                'subitem_1551256462220': [
                    {'subitem_1551256653656': '国立研究開発法人科学技術振興機構（JST）', 'subitem_1551256657859': 'ja'},
                    {'subitem_1551256653656': 'Japan Science and Technology Agency（JST）', 'subitem_1551256657859': 'en'}
                ],
                'subitem_1551256454317': [
                    {'subitem_1551256614961': 'MJBF', 'subitem_1551256619709': "JGN_fundingStream", "subitem_1551256619708": "https://sample/10.13039/501100020963"}
                ],
                'subitem_1551256454316': [
                    {'subitem_1551256614960': '1020', 'subitem_1551256619706': 'Crossref Funder', "subitem_1551256619707": "https://www.e-rad.go.jp/datasets/files/haibunkikan.csv"}
                ],
                "subitem_1551256462221": [
                    {"subitem_1551256653657": "Belmont Forum", "subitem_1551256657860": "en"},
                    {"subitem_1551256653657": "ベルモント・フォーラム", "subitem_1551256657860": "ja"}
                ],
                'subitem_1551256688098': [
                    {'subitem_1551256691232': '実践としての変革(Transformation):気候変動の影響を受けやすい環境下での持続可能性に向けた公平かつ超学際的な方法論の開発(TAPESTRY)', 'subitem_1551256694883': 'ja'},
                    {'subitem_1551256691232': 'Transformation as Practice: Developing an equitable and transdisciplinary methodology for sustainability in climate change-sensitive environments.', 'subitem_1551256694883': 'en'}
                ],
                'subitem_1551256665850': [
                    {'subitem_1551256671920': 'JPMJBF1801', 'subitem_1551256679403': 'https://doi.org/10.52926/JPMJBF1801', "subitem_1551256671921": "JGN"}
                ]
            }
        ]
    }

    # Case02: Parse funding reference (without attributes)
    # xml_data = xmltodict.parse("""
    #     <testdocument>
    #         <jpcoar:fundingReference>
    #             <jpcoar:funderIdentifier>1025</jpcoar:funderIdentifier>
    #             <jpcoar:funderName>日本学術振興会</jpcoar:funderName>
    #             <jpcoar:fundingStream>科学研究費助成事業</jpcoar:fundingStream>
    #             <jpcoar:awardNumber>JP18049069</jpcoar:awardNumber>
    #             <jpcoar:awardTitle>情報爆発時代の情報検索基盤技術</jpcoar:awardTitle>
    #         </jpcoar:fundingReference>
    #         <jpcoar:fundingReference>
    #             <jpcoar:funderIdentifier>http://data.crossref.org/fundingdata/funder/10.13039/501100001700</jpcoar:funderIdentifier>
    #             <jpcoar:funderName>文部科学省</jpcoar:funderName>
    #             <jpcoar:funderName>Ministry of Education, Culture, Sports, Science and Technology</jpcoar:funderName>
    #             <jpcoar:fundingStreamIdentifier>http://data.crossref.org/fundingdata/funder/10.13039/501100001691</jpcoar:fundingStreamIdentifier>
    #             <jpcoar:fundingStream>科学研究費補助金</jpcoar:fundingStream>
    #             <jpcoar:awardNumber>JP15H05814</jpcoar:awardNumber>
    #             <jpcoar:awardTitle>科学研究費補助金新学術領域（研究領域提案型）「太陽地球圏環境予測：我々が生きる宇宙の理解とその変動に対応する社会基盤の形成」計画研究A02「太陽嵐の発生機構の解明と予測」</jpcoar:awardTitle>
    #         </jpcoar:fundingReference>
    #     </testdocument>
    # """)['testdocument']['jpcoar:fundingReference']
    # res = {}
    # add_funding_reference(schema, mapping, res, xml_data)
    # assert res == {
    #     "item_1551265385290": [
    #         {
    #             'subitem_1551256454316': [
    #                 {'subitem_1551256614960': '1025'}
    #             ],
    #             'subitem_1551256462220': [
    #                 {'subitem_1551256653656': '日本学術振興会'},
    #             ],
    #             "subitem_1551256462221": [
    #                 {"subitem_1551256653657": "科学研究費助成事業"},
    #             ],
    #             'subitem_1551256665850': [
    #                 {'subitem_1551256671920': 'JP18049069'}
    #             ],
    #             'subitem_1551256688098': [
    #                 {'subitem_1551256691232': '情報爆発時代の情報検索基盤技術'},
    #             ],
    #         }, {
    #             'subitem_1551256454316': [
    #                 {'subitem_1551256614960': 'http://data.crossref.org/fundingdata/funder/10.13039/501100001700'}
    #             ],
    #             'subitem_1551256462220': [
    #                 {'subitem_1551256653656': '文部科学省'},
    #                 {'subitem_1551256653656': 'Ministry of Education, Culture, Sports, Science and Technology'},
    #             ],
    #             'subitem_1551256454317': [
    #                 {'subitem_1551256614961': 'http://data.crossref.org/fundingdata/funder/10.13039/501100001691'}
    #             ],
    #             "subitem_1551256462221": [
    #                 {"subitem_1551256653657": "科学研究費補助金"},
    #             ],
    #             'subitem_1551256665850': [
    #                 {'subitem_1551256671920': 'JP15H05814'}
    #             ],
    #             'subitem_1551256688098': [
    #                 {'subitem_1551256691232': '科学研究費補助金新学術領域（研究領域提案型）「太陽地球圏環境予測：我々が生きる宇宙の理解とその変動に対応する社会基盤の形成」計画研究A02「太陽嵐の発生機構の解明と予測」'},
    #             ],
    #         }
    #     ]
    # }

    # Case03: Parse single funding reference
    res = {}
    xml_data = xmltodict.parse("""
        <testdocument>
            <jpcoar:fundingReference>
                <jpcoar:funderIdentifier funderIdentifierType="Crossref Funder">http://data.crossref.org/fundingdata/funder/10.13039/501100001700</jpcoar:funderIdentifier>
                <jpcoar:funderName xml:lang="ja">文部科学省</jpcoar:funderName>
                <jpcoar:fundingStreamIdentifier fundingStreamIdentifierType="Crossref Funder">http://data.crossref.org/fundingdata/funder/10.13039/501100001691</jpcoar:fundingStreamIdentifier>
                <jpcoar:fundingStream xml:lang="ja">科学研究費補助金</jpcoar:fundingStream>
                <jpcoar:awardNumber awardURI="https://kaken.nii.ac.jp/ja/grant/KAKENHI-PLANNED-15H05814/">JP15H05814</jpcoar:awardNumber>
                <jpcoar:awardTitle xml:lang="ja">科学研究費補助金新学術領域（研究領域提案型）「太陽地球圏環境予測：我々が生きる宇宙の理解とその変動に対応する社会基盤の形成」計画研究A02「太陽嵐の発生機構の解明と予測」</jpcoar:awardTitle>
            </jpcoar:fundingReference>
        </testdocument>
    """)['testdocument']['jpcoar:fundingReference']
    add_funding_reference(schema, mapping, res, [xml_data])
    assert res ==  {
        "item_1551265385290": [
            {
                'subitem_1551256454316': [
                    {'subitem_1551256614960': 'http://data.crossref.org/fundingdata/funder/10.13039/501100001700', 'subitem_1551256619706': 'Crossref Funder', "subitem_1551256619707": ""}
                ],
                'subitem_1551256462220': [
                    {'subitem_1551256653656': '文部科学省', 'subitem_1551256657859': 'ja'},
                ],
                'subitem_1551256454317': [
                    {'subitem_1551256614961': 'http://data.crossref.org/fundingdata/funder/10.13039/501100001691', 'subitem_1551256619709': "Crossref Funder", "subitem_1551256619708": ""}
                ],
                "subitem_1551256462221": [
                    {"subitem_1551256653657": "科学研究費補助金", "subitem_1551256657860": "ja"}
                ],
                'subitem_1551256665850': [
                    {'subitem_1551256671920': 'JP15H05814', 'subitem_1551256679403': 'https://kaken.nii.ac.jp/ja/grant/KAKENHI-PLANNED-15H05814/', "subitem_1551256671921": ""}
                ],
                'subitem_1551256688098': [
                    {'subitem_1551256691232': '科学研究費補助金新学術領域（研究領域提案型）「太陽地球圏環境予測：我々が生きる宇宙の理解とその変動に対応する社会基盤の形成」計画研究A02「太陽嵐の発生機構の解明と予測」', 'subitem_1551256694883': 'ja'},
                ]
            }
        ]
    }

    # Case04: Parse empty funding reference
    res = {}
    add_funding_reference(schema, mapping, res, [{}])
    assert res == {}


# def add_source_identifier(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_source_identifier -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_source_identifier(mapper_jpcoar):
    # Case01: Parse multiple source identifier and attributes
    schema, mapping, _, metadata = mapper_jpcoar("jpcoar:sourceIdentifier")
    res = {}
    add_source_identifier(schema, mapping, res, metadata)
    assert res == {
        "item_1551265409089": [
            {'subitem_1551256405981': 'test source Identifier', 'subitem_1551256409644': 'PISSN'},
            {'subitem_1551256405981': '1234-5678', 'subitem_1551256409644': 'PISSN'},
            {'subitem_1551256405981': 'AN12345678', 'subitem_1551256409644': 'NCID'},
        ]
    }

    # Case02: Parse source identifier (with no attributes)
    res = {}
    add_source_identifier(schema, mapping, res, ['1234-5547', 'BBN12345678'])
    assert res == {
        "item_1551265409089":[
            {'subitem_1551256405981': '1234-5547'},
            {'subitem_1551256405981': 'BBN12345678'}
        ]
    }

    # Case03: Parse single source identifier
    res = {}
    add_source_identifier(schema, mapping, res, [{"#text": "1234-1124", "@identifierType": "PISSN"}])
    assert res == {
        "item_1551265409089":[
            {'subitem_1551256405981': '1234-1124', 'subitem_1551256409644': 'PISSN'}
        ]
    }

    # Case04: Parse empty source identifier
    res = {}
    add_source_identifier(schema, mapping, res, [])
    assert res == {}


# def add_source_title(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_source_title -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_source_title(mapper_jpcoar):
    # Case01: Parse multiple source title and attributes
    schema, mapping, _, metadata = mapper_jpcoar("jpcoar:sourceTitle")
    res = {}
    add_source_title(schema, mapping, res, metadata)
    assert res == {
        "item_1551265438256": [
            {'subitem_1551256349044': 'test collectibles', 'subitem_1551256350188': 'ja'},
            {'subitem_1551256349044': 'test title book', 'subitem_1551256350188': 'ja'},
            {'subitem_1551256349044': 'Journal of Comprehensive Nursing Research', 'subitem_1551256350188': 'en'}
        ]
    }

    # Case02: Parse source title (with no attributes)
    res = {}
    add_source_title(schema, mapping, res, ['source title1', 'source title2'])
    assert res == {
        "item_1551265438256":[
            {'subitem_1551256349044': 'source title1'},
            {'subitem_1551256349044': 'source title2'}
        ]
    }

    # Case03: Parse single source title
    res = {}
    add_source_title(schema, mapping, res, [{"#text": "看護総合科学研究会誌", "@xml:lang": "ja"}])
    assert res == {
        "item_1551265438256":[
            {'subitem_1551256349044': '看護総合科学研究会誌', 'subitem_1551256350188': 'ja'}
        ]
    }

    # Case04: Parse empty source title
    res = {}
    add_source_title(schema, mapping, res, [])
    assert res == {}


# def add_volume(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_volume -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_volume(mapper_jpcoar):
    # Case01: Parse volume
    schema, mapping, _, metadata = mapper_jpcoar("jpcoar:volume")
    res = {}
    add_volume(schema, mapping, res, metadata)
    assert res == {
        "item_1551265463411": {
            'subitem_1551256328147': '5'
        }
    }

    # Case02: Parse empty volume
    res = {}
    add_volume(schema, mapping, res, [])
    assert res == {}


# def add_issue(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_issue -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_issue(mapper_jpcoar):
    # Case01: Parse issue
    schema, mapping, _, metadata = mapper_jpcoar("jpcoar:issue")
    res = {}
    add_issue(schema, mapping, res, metadata)
    assert res == {
        "item_1551265520160": {
            'subitem_1551256294723': '2'
        }
    }

    # Case02: Parse empty issue
    res = {}
    add_issue(schema, mapping, res, [])
    assert res == {}


# def add_num_page(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_num_page -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_num_page(mapper_jpcoar):
    # Case01: Parse num pages
    schema, mapping, _, metadata = mapper_jpcoar("jpcoar:numPages")
    res = {}
    add_num_page(schema, mapping, res, metadata)
    assert res == {
        "item_1551265553273": {
            'subitem_1551256248092': '333'
        }
    }

    # Case02: Parse empty num pages
    res = {}
    add_num_page(schema, mapping, res, [])
    assert res == {}


# def add_page_start(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_page_start -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_page_start(mapper_jpcoar):
    # Case01: Parse page start
    schema, mapping, _, metadata = mapper_jpcoar("jpcoar:pageStart")
    res = {}
    add_page_start(schema, mapping, res, metadata)
    assert res == {
        "item_1551265569218": {
            'subitem_1551256198917': '123'
        }
    }

    # Case02: Parse empty page start
    res = {}
    add_page_start(schema, mapping, res, [])
    assert res == {}


# def add_page_end(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_page_end -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_page_end(mapper_jpcoar):
    # Case01: Parse page end
    schema, mapping, _, metadata = mapper_jpcoar("jpcoar:pageEnd")
    res = {}
    add_page_end(schema, mapping, res, metadata)
    assert res == {
        "item_1551265603279": {
            'subitem_1551256185532': '456'
        }
    }

    # Case02: Parse empty page end
    res = {}
    add_page_end(schema, mapping, res, [])
    assert res == {}


# def add_dissertation_number(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_dissertation_number -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_dissertation_number(mapper_jpcoar):
    # Case01: Parse dissertation number
    schema, mapping, _, metadata = mapper_jpcoar("dcndl:dissertationNumber")
    res = {}
    add_dissertation_number(schema, mapping, res, metadata)
    assert res == {
        "item_1551265738931": {
            'subitem_1551256171004': '甲第9999号'
        }
    }

    # Case02: Parse empty dissertation number
    res = {}
    add_dissertation_number(schema, mapping, res, [])
    assert res == {}


# def add_degree_name(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_degree_name -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_degree_name(mapper_jpcoar):
    # Case01: Parse multiple degree names and attributes
    schema, mapping, _, metadata = mapper_jpcoar("dcndl:degreeName")
    res = {}
    add_degree_name(schema, mapping, res, metadata)
    assert res == {
        "item_1551265790591": [
            {'subitem_1551256126428': 'テスト学位', 'subitem_1551256129013': 'ja'},
            {'subitem_1551256126428': 'Doctor of Philosophy in Letters', 'subitem_1551256129013': 'en'},
            {'subitem_1551256126428': '博士（文学）', 'subitem_1551256129013': 'ja'},
        ]
    }

    # Case02: Parse degree name (with no attributes)
    xml_data = xmltodict.parse("""
        <testdocument>
            <dcndl:degreeName>テスト学位名1</dcndl:degreeName>
            <dcndl:degreeName>テスト学位名2</dcndl:degreeName>
        </testdocument>
    """)["testdocument"]["dcndl:degreeName"]
    res = {}
    add_degree_name(schema, mapping, res, xml_data)
    assert res == {
        "item_1551265790591":[
            {"subitem_1551256126428": "テスト学位名1"},
            {"subitem_1551256126428": "テスト学位名2"}
        ]
    }

    # Case03: Parse single degree name
    res = {}
    xml_data = xmltodict.parse("""
        <testdocument>
            <dcndl:degreeName xml:lang="en">test single degree name</dcndl:degreeName>
        </testdocument>
    """)["testdocument"]["dcndl:degreeName"]
    add_degree_name(schema, mapping, res, [xml_data])
    assert res == {
        "item_1551265790591":[
            {"subitem_1551256126428": "test single degree name", "subitem_1551256129013": "en"}
        ]
    }

    # Case04: Parse empty degree name
    res = {}
    add_degree_name(schema, mapping, res, [])
    assert res == {}


# def add_date_granted(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_date_granted -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_date_granted(mapper_jpcoar):
    # Case01: Parse date granted
    schema, mapping, _, metadata = mapper_jpcoar("dcndl:dateGranted")
    res = {}
    add_date_granted(schema, mapping, res, metadata)
    assert res == {
        "item_1551265811989": {
            'subitem_1551256096004': '2022-10-19'
        }
    }

    # Case02: Parse empty date granted
    res = {}
    add_date_granted(schema, mapping, res, [])
    assert res == {}


# def add_degree_grantor(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_degree_grantor -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_degree_grantor(mapper_jpcoar):
    # Case01: Parse multiple degree grantors and attributes
    schema, mapping, _, metadata = mapper_jpcoar("jpcoar:degreeGrantor")
    res = {}
    add_degree_grantor(schema, mapping, res, metadata)
    assert res == {
        "item_1551265903092": [
            {
                'subitem_1551256015892': [
                    {'subitem_1551256027296': '学位授与機関識別子テスト1', 'subitem_1551256029891': 'kakenhi'}
                ],
                'subitem_1551256037922': [
                    {'subitem_1551256042287': '学位授与機関1', 'subitem_1551256047619': 'ja'},
                    {'subitem_1551256042287': 'degree grantor1', 'subitem_1551256047619': 'en'}
                ]
            }, {
                'subitem_1551256015892': [
                    {'subitem_1551256027296': '学位授与機関識別子テスト2', 'subitem_1551256029891': 'kakenhi'}
                ],
                'subitem_1551256037922': [
                    {'subitem_1551256042287': '学位授与機関2', 'subitem_1551256047619': 'ja'},
                    {'subitem_1551256042287': 'degree grantor2', 'subitem_1551256047619': 'en'}
                ]
            }
        ]
    }

    # Case02: Parse degree grantor (without attributes)
    # single_xml_data = xmltodict.parse(
    #     """
    #     <testdocument>
    #         <jpcoar:degreeGrantor>
    #             <jpcoar:nameIdentifier>32653</jpcoar:nameIdentifier>
    #             <jpcoar:degreeGrantorName>東京女子医科大学</jpcoar:degreeGrantorName>
    #         </jpcoar:degreeGrantor>
    #         <jpcoar:degreeGrantor>
    #             <jpcoar:nameIdentifier>00012</jpcoar:nameIdentifier>
    #             <jpcoar:degreeGrantorName>sample grantor</jpcoar:degreeGrantorName>
    #             <jpcoar:degreeGrantorName>サンプル学位授与機関</jpcoar:degreeGrantorName>
    #         </jpcoar:degreeGrantor>
    #     </testdocument>
    #     """
    # )['testdocument']["jpcoar:degreeGrantor"]
    # res = {}
    # add_degree_grantor(schema, mapping, res, single_xml_data)
    # assert res == {
    #     "item_1551265903092": [
    #         {
    #             "subitem_1551256015892": [
    #                 {"subitem_1551256027296": "32653"}
    #             ],
    #             "subitem_1551256037922": [
    #                 {"subitem_1551256042287": "東京女子医科大学"}
    #             ]
    #         }, {
    #             "subitem_1551256015892": [
    #                 {"subitem_1551256027296": "00012"}
    #             ],
    #             "subitem_1551256037922": [
    #                 {"subitem_1551256042287": "sample grantor"},
    #                 {"subitem_1551256042287": "サンプル学位授与機関"}
    #             ]
    #         }
    #     ]
    # }

    # Case03: Parse single degree grantor
    single_xml_data = xmltodict.parse(
        """
        <testdocument>
            <jpcoar:degreeGrantor>
                <jpcoar:nameIdentifier nameIdentifierScheme="kakenhi">32653</jpcoar:nameIdentifier>
                <jpcoar:degreeGrantorName xml:lang="ja">東京女子医科大学</jpcoar:degreeGrantorName>
            </jpcoar:degreeGrantor>
        </testdocument>
        """
    )['testdocument']["jpcoar:degreeGrantor"]
    res = {}
    add_degree_grantor(schema, mapping, res, [single_xml_data])
    assert res == {
        "item_1551265903092":[
            {
                'subitem_1551256015892': [
                    {'subitem_1551256027296': '32653', 'subitem_1551256029891': 'kakenhi'}
                ],
                'subitem_1551256037922': [
                    {'subitem_1551256042287': '東京女子医科大学', 'subitem_1551256047619': 'ja'},
                ]
            }
        ]
    }

    # Case04: Parse empty degree grantor
    res = {}
    add_degree_grantor(schema, mapping, res, [])
    assert res == {}


# def add_conference(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_conference -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_conference(mapper_jpcoar):
    res = {}
    schema, mapping, _, metadata = mapper_jpcoar("jpcoar:conference")
    add_conference(schema, mapping, res, metadata)
    # Case01: Parse multiple conferences with attributes
    assert res == {
        "item_1551265973055": [
            {
                'subitem_1599711813532': 'JPN',
                'subitem_1599711655652': '12345',
                'subitem_1599711633003': [
                    {'subitem_1599711636923': 'テスト会議1', 'subitem_1599711645590': 'ja'},
                    {'subitem_1599711636923': 'test conference1', 'subitem_1599711645590': 'en'}
                ],
                "subitem_1599711660052": [
                    {"subitem_1599711680082": "テスト機関1", "subitem_1599711686511": "ja"},
                    {"subitem_1599711680082": "test conference sponsor1", "subitem_1599711686511": "en"}
                ],
                "subitem_1599711699392": {
                    "subitem_1599711704251": "12",
                    "subitem_1599711712451": "11",
                    "subitem_1599711727603": "4",
                    "subitem_1599711731891": "2000",
                    "subitem_1599711735410": "1",
                    "subitem_1599711739022": "12",
                    "subitem_1599711743722": "2005",
                    "subitem_1599711745532": "ja"
                },
                "subitem_1599711758470": [
                    {"subitem_1599711769260": "テスト会場1", "subitem_1599711775943": "ja"},
                    {"subitem_1599711769260": "test conference venue1", "subitem_1599711775943": "en"}
                ],
                "subitem_1599711788485": [
                    {"subitem_1599711798761": "東京", "subitem_1599711803382": "ja"},
                    {"subitem_1599711798761": "Tokyo", "subitem_1599711803382": "en"}
                ]
            },
            {
                'subitem_1599711813532': 'JPN',
                'subitem_1599711655652': '3456',
                'subitem_1599711633003': [
                    {'subitem_1599711636923': 'テスト会議2', 'subitem_1599711645590': 'ja'},
                    {'subitem_1599711636923': 'test conference2', 'subitem_1599711645590': 'en'}
                ],
                "subitem_1599711660052": [
                    {"subitem_1599711680082": "テスト機関2", "subitem_1599711686511": "ja"},
                    {"subitem_1599711680082": "test conference sponsor2", "subitem_1599711686511": "en"}
                ],
                "subitem_1599711699392": {
                    "subitem_1599711704251": "11",
                    "subitem_1599711712451": "11",
                    "subitem_1599711727603": "4",
                    "subitem_1599711731891": "2000",
                    "subitem_1599711735410": "2",
                    "subitem_1599711739022": "12",
                    "subitem_1599711743722": "2005",
                    "subitem_1599711745532": "ja"
                },
                "subitem_1599711758470": [
                    {"subitem_1599711769260": "テスト会場2", "subitem_1599711775943": "ja"},
                    {"subitem_1599711769260": "test conference venue2", "subitem_1599711775943": "en"}
                ],
                "subitem_1599711788485": [
                    {"subitem_1599711798761": "名古屋", "subitem_1599711803382": "ja"},
                    {"subitem_1599711798761": "Nagoya", "subitem_1599711803382": "en"}
                ]
            }
        ]
    }

    # # Case02: Parse degree grantor (with no attributes)
    # res = {}
    # add_degree_grantor(schema, mapping, res, ['テスト学位名1', 'テスト学位名2'])
    # assert res == {
    #     "item_1551265790591":[
    #         {'subitem_1551256126428': 'テスト学位名1'},
    #         {'subitem_1551256126428': 'テスト学位名2'}
    #     ]
    # }

    # Case03: Parse single conference
    single_xml_data = xmltodict.parse(
        """
        <testdocument>
            <jpcoar:conference>
                <jpcoar:conferenceName xml:lang="en">RDA Seventh Plenary Meeting</jpcoar:conferenceName>
                <jpcoar:conferenceSequence>7</jpcoar:conferenceSequence>
                <jpcoar:conferenceSponsor xml:lang="en">The Research Data Alliance</jpcoar:conferenceSponsor>
                <jpcoar:conferenceDate xml:lang="en" startDay="29" startMonth="02" startYear="2016" endDay="04"
                    endMonth="03" endYear="2016">February 29th to March 4th, 2016</jpcoar:conferenceDate>
                <jpcoar:conferenceVenue xml:lang="en">Hitotsubashi Hall</jpcoar:conferenceVenue>
                <jpcoar:conferencePlace xml:lang="en">Tokyo</jpcoar:conferencePlace>
                <jpcoar:conferenceCountry>JPN</jpcoar:conferenceCountry>
            </jpcoar:conference>
        </testdocument>
        """
    )['testdocument']["jpcoar:conference"]
    res = {}
    add_conference(schema, mapping, res, [single_xml_data])
    assert res == {
        "item_1551265973055": [
            {
                'subitem_1599711813532': 'JPN',
                'subitem_1599711655652': '7',
                'subitem_1599711633003': [
                    {'subitem_1599711636923': 'RDA Seventh Plenary Meeting', 'subitem_1599711645590': 'en'}
                ],
                "subitem_1599711660052": [
                    {"subitem_1599711680082": "The Research Data Alliance", "subitem_1599711686511": "en"}
                ],
                "subitem_1599711699392": {
                    "subitem_1599711704251": "February 29th to March 4th, 2016",
                    "subitem_1599711712451": "29",
                    "subitem_1599711727603": "02",
                    "subitem_1599711731891": "2016",
                    "subitem_1599711735410": "04",
                    "subitem_1599711739022": "03",
                    "subitem_1599711743722": "2016",
                    "subitem_1599711745532": "en"
                },
                "subitem_1599711758470": [
                    {"subitem_1599711769260": "Hitotsubashi Hall", "subitem_1599711775943": "en"}
                ],
                "subitem_1599711788485": [
                    {"subitem_1599711798761": "Tokyo", "subitem_1599711803382": "en"}
                ]
            }
        ]
    }

    # Case04: Parse empty conference
    res = {}
    add_conference(schema, mapping, res, [])
    assert res == {}


# def add_edition(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_edition -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_edition():
    schema = {
        "editions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "format": "text",
                    },
                    "lang": {
                        "enum": [None, "ja", "en"],
                        "type": ["null", "string"],
                        "format": "select",
                        "currentEnum": ["ja", "en"]
                    }
                }
            },
            "title": "Edition",
            "maxItems": 9999,
            "minItems": 1
        }
    }

    mapping = {
        "edition.@value": ["editions.name"],
        "edition.@attributes.xml:lang": ["editions.lang"]
    }

    # Case01: Parse multiple editions and attributes
    xml_data = xmltodict.parse(
        """
        <testdocument>
            <dcndl:edition xml:lang="ja">改訂新版</dcndl:edition>
            <dcndl:edition xml:lang="ja">宮城野の一部を改刻した改題本</dcndl:edition>
            <dcndl:edition xml:lang="ja">萬暦34年序重刻本の翻刻</dcndl:edition>
        </testdocument>
        """
    )['testdocument']['dcndl:edition']
    res = {}
    add_edition(schema, mapping, res, xml_data)
    assert res == {
        "editions": [
            {'name': '改訂新版', 'lang': 'ja'},
            {'name': '宮城野の一部を改刻した改題本', 'lang': 'ja'},
            {'name': '萬暦34年序重刻本の翻刻', 'lang': 'ja'}
        ]
    }

    # Case02: Parse editions (without attributes)
    xml_data = xmltodict.parse(
        """
        <testdocument>
            <dcndl:edition>edition1</dcndl:edition>
            <dcndl:edition>edition2</dcndl:edition>
        </testdocument>
        """
    )['testdocument']['dcndl:edition']
    res = {}
    add_edition(schema, mapping, res, xml_data)
    assert res == {
        "editions":[
            {'name': 'edition1'},
            {'name': 'edition2'}
        ]
    }

    # Case03: Parse single edition
    res = {}
    single_xml_data = xmltodict.parse(
        """
        <testdocument>
            <dcndl:edition xml:lang="en">single edition</dcndl:edition>
        </testdocument>
        """
    )['testdocument']['dcndl:edition']
    add_edition(schema, mapping, res, [single_xml_data])
    assert res == {
        "editions":[
            {'name': 'single edition', 'lang': 'en'}
        ]
    }

    # Case04: Parse empty edition
    res = {}
    add_edition(schema, mapping, res, [])
    assert res == {}


# def add_volumeTitle(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_volumeTitle -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_volumeTitle():
    schema = {
        "item_volumeTitle": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "format": "text",
                    },
                    "lang": {
                        "enum": [None, "ja", "en"],
                        "type": ["null", "string"],
                        "format": "select",
                        "currentEnum": ["ja", "en"]
                    }
                }
            },
            "title": "Volume Title",
            "maxItems": 9999,
            "minItems": 1
        }
    }

    mapping = {
        "volumeTitle.@value": ["item_volumeTitle.name"],
        "volumeTitle.@attributes.xml:lang": ["item_volumeTitle.lang"]
    }

    # Case01: Parse multiple volume titles and attributes
    xml_data = xmltodict.parse(
        """
        <testdocument>
            <dcndl:volumeTitle xml:lang="ja">近畿. 2 三重・和歌山・大阪・兵庫</dcndl:volumeTitle>
            <dcndl:volumeTitle xml:lang="ja-Kana">キンキ. 2 ミエ ワカヤマ オオサカ ヒョウゴ</dcndl:volumeTitle>
            <dcndl:volumeTitle xml:lang="en">volume titles</dcndl:volumeTitle>
        </testdocument>
        """
    )['testdocument']['dcndl:volumeTitle']
    res = {}
    add_volumeTitle(schema, mapping, res, xml_data)
    assert res == {
        "item_volumeTitle": [
            {'name': '近畿. 2 三重・和歌山・大阪・兵庫', 'lang': 'ja'},
            {'name': 'キンキ. 2 ミエ ワカヤマ オオサカ ヒョウゴ', 'lang': 'ja-Kana'},
            {'name': 'volume titles', 'lang': 'en'}
        ]
    }

    # Case02: Parse volume titles (with no attributes)
    res = {}
    add_volumeTitle(schema, mapping, res, ['volumeTitle1', 'volumeTitle2'])
    assert res == {
        "item_volumeTitle":[
            {'name': 'volumeTitle1'},
            {'name': 'volumeTitle2'}
        ]
    }

    # Case03: Parse single volume title
    res = {}
    single_xml_data = xmltodict.parse(
        """
        <testdocument>
            <dcndl:volumeTitle xml:lang="en">single volume title</dcndl:volumeTitle>
        </testdocument>
        """
    )['testdocument']['dcndl:volumeTitle']
    add_volumeTitle(schema, mapping, res, [single_xml_data])
    assert res == {
        "item_volumeTitle":[
            {'name': 'single volume title', 'lang': 'en'}
        ]
    }

    # Case04: Parse empty volume title
    res = {}
    add_volumeTitle(schema, mapping, res, [])
    assert res == {}


# def add_originalLanguage(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_originalLanguage -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_originalLanguage():
    schema = {
        "item_originalLanguage": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "val": {
                        "type": "string",
                        "format": "text",
                    }
                }
            },
            "title": "Original Language",
            "maxItems": 9999,
            "minItems": 1
        }
    }

    mapping = {
        "originalLanguage.@value": ["item_originalLanguage.val"]
    }

    # Case01: Parse multiple original languages
    xml_data = xmltodict.parse(
        """
        <testdocument>
            <dcndl:originalLanguage>eng</dcndl:originalLanguage>
            <dcndl:originalLanguage>jpn</dcndl:originalLanguage>
            <dcndl:originalLanguage>ger</dcndl:originalLanguage>
        </testdocument>
        """
    )['testdocument']['dcndl:originalLanguage']
    res = {}
    add_originalLanguage(schema, mapping, res, xml_data)
    assert res == {
        "item_originalLanguage": [
            {'val': 'eng'},
            {'val': 'jpn'},
            {'val': 'ger'},
        ]
    }

    # Case02: Parse single original language
    res = {}
    single_xml_data = xmltodict.parse(
        """
        <testdocument>
            <dcndl:originalLanguage>jpn</dcndl:originalLanguage>
        </testdocument>
        """
    )['testdocument']['dcndl:originalLanguage']
    add_originalLanguage(schema, mapping, res, [single_xml_data])
    assert res == {
        "item_originalLanguage": [
            {'val': 'jpn'}
        ]
    }

    # Case03: Parse empty language
    res = {}
    add_originalLanguage(schema, mapping, res, [])
    assert res == {}


# def add_extent(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_extent -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_extent():
    schema = {
        "item_extent": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "val": {
                        "type": "string",
                        "format": "text",
                    },
                    "lang": {
                        "enum": [None, "ja", "en"],
                        "type": ["null", "string"],
                        "format": "select",
                        "currentEnum": ["ja", "en"]
                    }
                }
            },
            "title": "Extent",
            "maxItems": 9999,
            "minItems": 1
        }
    }

    mapping = {
        "extent.@value": ["item_extent.val"],
        "extent.@attributes.xml:lang": ["item_extent.lang"]
    }

    # Case01: Parse multiple extents and attributes
    xml_data = xmltodict.parse(
        """
        <testdocument>
            <dcterms:extent xml:lang="ja">図版 ; 19cm</dcterms:extent>
            <dcterms:extent xml:lang="ja">1枚 ; 92×172cm</dcterms:extent>
            <dcterms:extent xml:lang="ja">22cm + CD-ROM1 枚（12cm）</dcterms:extent>
        </testdocument>
        """
    )['testdocument']['dcterms:extent']
    res = {}
    add_extent(schema, mapping, res, xml_data)
    assert res == {
        "item_extent": [
            {'val': '図版 ; 19cm', 'lang': 'ja'},
            {'val': '1枚 ; 92×172cm', 'lang': 'ja'},
            {'val': '22cm + CD-ROM1 枚（12cm）', 'lang': 'ja'}
        ]
    }

    # Case02: Parse extents (with no attributes)
    res = {}
    add_extent(schema, mapping, res, ['extent1', 'extent2'])
    assert res == {
        "item_extent":[
            {'val': 'extent1'},
            {'val': 'extent2'}
        ]
    }

    # Case03: Parse single extent
    res = {}
    single_xml_data = xmltodict.parse(
        """
        <testdocument>
            <dcterms:extent xml:lang="en">single extent</dcterms:extent>
        </testdocument>
        """
    )['testdocument']['dcterms:extent']
    add_extent(schema, mapping, res, [single_xml_data])
    assert res == {
        "item_extent":[
            {'val': 'single extent', 'lang': 'en'}
        ]
    }

    # Case04: Parse empty extent
    res = {}
    add_extent(schema, mapping, res, [])
    assert res == {}


# def add_format(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_format -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_format():
    schema = {
        "item_format": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "subitem_val": {
                        "type": "string",
                        "format": "text",
                    },
                    "lang": {
                        "enum": [None, "ja", "en"],
                        "type": ["null", "string"],
                        "format": "select",
                        "currentEnum": ["ja", "en"]
                    }
                }
            },
            "title": "Format",
            "maxItems": 9999,
            "minItems": 1
        }
    }

    mapping = {
        "format.@value": ["item_format.subitem_val"],
        "format.@attributes.xml:lang": ["item_format.lang"]
    }

    # Case01: Parse multiple formats and attributes
    xml_data = xmltodict.parse(
        """
        <testdocument>
            <jpcoar:format xml:lang="ja">折本</jpcoar:format>
            <jpcoar:format xml:lang="ja">畳物</jpcoar:format>
            <jpcoar:format xml:lang="ja">帙入</jpcoar:format>
        </testdocument>
        """
    )['testdocument']['jpcoar:format']
    res = {}
    add_format(schema, mapping, res, xml_data)
    assert res == {
        "item_format": [
            {'subitem_val': '折本', 'lang': 'ja'},
            {'subitem_val': '畳物', 'lang': 'ja'},
            {'subitem_val': '帙入', 'lang': 'ja'}
        ]
    }

    # Case02: Parse formats (with no attributes)
    xml_data = xmltodict.parse(
        """
        <testdocument>
            <jpcoar:format>format1</jpcoar:format>
            <jpcoar:format>format2</jpcoar:format>
        </testdocument>
        """
    )['testdocument']['jpcoar:format']
    res = {}
    add_format(schema, mapping, res, xml_data)
    assert res == {
        "item_format":[
            {'subitem_val': 'format1'},
            {'subitem_val': 'format2'}
        ]
    }

    # Case03: Parse single format
    res = {}
    single_xml_data = xmltodict.parse(
        """
        <testdocument>
            <jpcoar:format xml:lang="en">single format</jpcoar:format>
        </testdocument>
        """
    )['testdocument']['jpcoar:format']
    add_format(schema, mapping, res, [single_xml_data])
    assert res == {
        "item_format":[
            {'subitem_val': 'single format', 'lang': 'en'}
        ]
    }

    # Case04: Parse empty format
    res = {}
    add_format(schema, mapping, res, [])
    assert res == {}


# def add_holdingAgent(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_holdingAgent -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_holdingAgent():
    schema = {
        "item_holdingAgent": {
            "type": "object",
            "properties": {
                "holdingAgentNameIdentifier": {
                    "type": "object",
                    "properties": {
                        "identifier": {
                            "type": "string",
                            "format": "text"
                        },
                        "scheme": {
                            "enum": [None, "ISNI", "Ringgold", "ROR"],
                            "type": ["null", "string"],
                            "format": "select",
                            "currentEnum": ["ISNI", "Ringgold", "ROR"]
                        },
                        "uri": {
                            "type": "string",
                            "format": "text"
                        }
                    }
                },
                "holdingAgentName": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "format": "text"
                            },
                            "lang": {
                                "enum": [None, "ja", "en"],
                                "type": ["null", "string"],
                                "format": "select",
                                "currentEnum": ["ja", "en"]
                            }
                        }
                    }
                }
            },
            "title": "Holding Agent",
            "maxItems": 9999,
            "minItems": 1
        }
    }

    mapping = {
        "holdingAgent.holdingAgentNameIdentifier.@value": ["item_holdingAgent.holdingAgentNameIdentifier.identifier"],
        "holdingAgent.holdingAgentNameIdentifier.@attributes.nameIdentifierScheme": ["item_holdingAgent.holdingAgentNameIdentifier.scheme"],
        "holdingAgent.holdingAgentNameIdentifier.@attributes.nameIdentifierURI": ["item_holdingAgent.holdingAgentNameIdentifier.uri"],
        "holdingAgent.holdingAgentName.@value": ["item_holdingAgent.holdingAgentName.name"],
        "holdingAgent.holdingAgentName.@attributes.xml:lang": ["item_holdingAgent.holdingAgentName.lang"],
    }

    # Case01: Parse holding agent and attributes
    xml_data = xmltodict.parse(
        """
        <testdocument>
            <jpcoar:holdingAgent>
                <jpcoar:holdingAgentNameIdentifier nameIdentifierScheme="ROR" nameIdentifierURI="https://ror.org/057zh3y96">057zh3y96</jpcoar:holdingAgentNameIdentifier>
                <jpcoar:holdingAgentName xml:lang="ja">東京大学</jpcoar:holdingAgentName>
                <jpcoar:holdingAgentName xml:lang="en">The University of Tokyo</jpcoar:holdingAgentName>
            </jpcoar:holdingAgent>
        </testdocument>
        """
    )['testdocument']['jpcoar:holdingAgent']
    res = {}
    add_holdingAgent(schema, mapping, res, [xml_data])
    assert res == {
        "item_holdingAgent": {
            "holdingAgentNameIdentifier": {
                "identifier": "057zh3y96",
                "scheme": "ROR",
                "uri": "https://ror.org/057zh3y96"
            },
            "holdingAgentName": [
                {"name": "東京大学", "lang": "ja"},
                {"name": "The University of Tokyo", "lang": "en"}
            ]
        }
    }

    # # Case02: Parse holding agent (without attributes)
    # xml_data = xmltodict.parse(
    #     """
    #     <testdocument>
    #         <jpcoar:holdingAgent>
    #             <jpcoar:holdingAgentNameIdentifier>057zh3y96</jpcoar:holdingAgentNameIdentifier>
    #             <jpcoar:holdingAgentName>東京大学</jpcoar:holdingAgentName>
    #             <jpcoar:holdingAgentName>The University of Tokyo</jpcoar:holdingAgentName>
    #         </jpcoar:holdingAgent>
    #     </testdocument>
    #     """
    # )['testdocument']['jpcoar:holdingAgent']
    # res = {}
    # add_holdingAgent(schema, mapping, res, xml_data)
    # assert res == {
    #     "item_holdingAgent": {
    #         "holdingAgentNameIdentifier": {
    #             "identifier": "057zh3y96"
    #         },
    #         "holdingAgentName": [
    #             {"name": "東京大学"},
    #             {"name": "The University of Tokyo"}
    #         ]
    #     }
    # }

    # Case03: Parse empty holding agent
    res = {}
    add_holdingAgent(schema, mapping, res, [])
    assert res == {}


# def add_datasetSeries(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_datasetSeries -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_datasetSeries():
    schema = {
        "item_datasetSeries": {
            "type": "object",
            "properties": {
                "subitem_val": {
                    "enum": [None, "True", "False"],
                    "type": ["null", "string"],
                    "format": "select",
                    "currentEnum": ["True", "False"],
                },
            },
            "title": "datasetSeries",
            "maxItems": 9999,
            "minItems": 1
        }
    }

    mapping = {
        "datasetSeries.@value": ["item_datasetSeries.subitem_val"],
    }

    # Case01: Parse datasetSeries
    xml_data = xmltodict.parse(
        """
        <testdocument>
            <jpcoar:datasetSeries>True</jpcoar:datasetSeries>
        </testdocument>
        """
    )['testdocument']['jpcoar:datasetSeries']
    res = {}
    add_datasetSeries(schema, mapping, res, [xml_data])
    assert res == {
        "item_datasetSeries": {'subitem_val': 'True'}
    }

    # Case02: Parse empty datasetSeries
    res = {}
    add_datasetSeries(schema, mapping, res, [])
    assert res == {}


# def add_file(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_file -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_file(mapper_jpcoar):
    # Case01: Parse multiple files with attributes
    res = {}
    schema, mapping, _, metadata = mapper_jpcoar("jpcoar:file")
    add_file(schema, mapping, res, metadata)
    assert res == {
        "item_1570069138259": [
            {
                "filename": "test1.txt",
                'subitem_1551255854908': '1.0',
                'subitem_1551255750794': 'text/plain',
                'subitem_1551255788530': [
                    {'subitem_1570068579439': '18 KB'},
                    {'subitem_1570068579439': '18432 B'}
                ],
                'subitem_1551255820788': [
                    {'subitem_1551255828320': '2022-10-20', 'subitem_1551255833133': 'Accepted'},
                    {'subitem_1551255828320': '2022-10-21', 'subitem_1551255833133': 'Available'},
                    {'subitem_1551255828320': '2004-03-02/2005-06-02', 'subitem_1551255833133': 'Collected'}
                ],
                'url': {
                    'url': 'https://weko3.example.org/record/1/files/test1.txt',
                    "objectType": "abstract",
                    "label": "test1.txt"
                },
            }, {
                "filename": "test2",
                'subitem_1551255854908': '1.2',
                'subitem_1551255750794': 'application/octet-stream',
                'subitem_1551255788530': [
                    {'subitem_1570068579439': '19 MB'},
                    {'subitem_1570068579439': '19456 KB'}
                ],
                'url': {
                    'url': 'https://weko3.example.org/record/1/files/test2',
                    "objectType": "dataset",
                    "label": "test2"
                }
            }, {
                "filename": "test3.png",
                'subitem_1551255854908': '2.1',
                'subitem_1551255750794': 'image/png',
                'subitem_1551255820788': [
                    {'subitem_1551255828320': '2015-10-01', 'subitem_1551255833133': 'Issued'}
                ],
                'url': {
                    'url': 'https://weko3.example.org/record/1/files/test3.png',
                    "objectType": "fulltext",
                    "label": "test3.png"
                }
            }
        ],
        "files_info": [{
            "key": "item_1570069138259",
            "items": [
                {
                    "filename": "test1.txt",
                    'subitem_1551255854908': '1.0',
                    'subitem_1551255750794': 'text/plain',
                    'subitem_1551255788530': [
                        {'subitem_1570068579439': '18 KB'},
                        {'subitem_1570068579439': '18432 B'}
                    ],
                    'subitem_1551255820788': [
                        {'subitem_1551255828320': '2022-10-20', 'subitem_1551255833133': 'Accepted'},
                        {'subitem_1551255828320': '2022-10-21', 'subitem_1551255833133': 'Available'},
                        {'subitem_1551255828320': '2004-03-02/2005-06-02', 'subitem_1551255833133': 'Collected'}
                    ],
                    'url': {
                        'url': 'https://weko3.example.org/record/1/files/test1.txt',
                        "objectType": "abstract",
                        "label": "test1.txt"
                    },
                }, {
                    "filename": "test2",
                    'subitem_1551255854908': '1.2',
                    'subitem_1551255750794': 'application/octet-stream',
                    'subitem_1551255788530': [
                        {'subitem_1570068579439': '19 MB'},
                        {'subitem_1570068579439': '19456 KB'}
                    ],
                    'url': {
                        'url': 'https://weko3.example.org/record/1/files/test2',
                        "objectType": "dataset",
                        "label": "test2"
                    }
                }, {
                    "filename": "test3.png",
                    'subitem_1551255854908': '2.1',
                    'subitem_1551255750794': 'image/png',
                    'subitem_1551255820788': [
                        {'subitem_1551255828320': '2015-10-01', 'subitem_1551255833133': 'Issued'}
                    ],
                    'url': {
                        'url': 'https://weko3.example.org/record/1/files/test3.png',
                        "objectType": "fulltext",
                        "label": "test3.png"
                    }
                }
            ]
        }]
    }

    # # Case02: Parse files (without attributes)
    # xml_data = xmltodict.parse(
    #     """
    #     <testdocument>
    #         <jpcoar:file>
    #             <jpcoar:URI>https://weko3.example.org/record/1/files/test1.txt</jpcoar:URI>
    #             <jpcoar:mimeType>text/plain</jpcoar:mimeType>
    #             <jpcoar:extent>18 KB</jpcoar:extent>
    #             <jpcoar:extent>18432 B</jpcoar:extent>
    #             <datacite:date>2022-10-20</datacite:date>
    #             <datacite:date>2022-10-21</datacite:date>
    #             <datacite:date>2004-03-02/2005-06-02</datacite:date>
    #             <datacite:version>1.0</datacite:version>
    #         </jpcoar:file>
    #         <jpcoar:file>
    #             <jpcoar:URI>https://weko3.example.org/record/1/files/test2</jpcoar:URI>
    #             <jpcoar:mimeType>application/octet-stream</jpcoar:mimeType>
    #             <jpcoar:extent>19 MB</jpcoar:extent>
    #             <jpcoar:extent>19456 KB</jpcoar:extent>
    #             <datacite:version>1.2</datacite:version>
    #         </jpcoar:file>
    #         <jpcoar:file>
    #             <jpcoar:URI>https://weko3.example.org/record/1/files/test3.png</jpcoar:URI>
    #             <jpcoar:mimeType>image/png</jpcoar:mimeType>
    #             <datacite:date>2015-10-01</datacite:date>
    #             <datacite:version>2.1</datacite:version>
    #         </jpcoar:file>
    #     </testdocument>
    #     """
    # )['testdocument']["jpcoar:file"]
    # res = {}
    # add_file(schema, mapping, res, xml_data)
    # assert res == {
    #     "item_1570069138259": [
    #         {
    #             "filename": "test1.txt",
    #             'subitem_1551255854908': '1.0',
    #             'subitem_1551255750794': 'text/plain',
    #             'subitem_1551255788530': [
    #                 {'subitem_1570068579439': '18 KB'},
    #                 {'subitem_1570068579439': '18432 B'}
    #             ],
    #             'subitem_1551255820788': [
    #                 {'subitem_1551255828320': '2022-10-20'},
    #                 {'subitem_1551255828320': '2022-10-21'},
    #                 {'subitem_1551255828320': '2004-03-02/2005-06-02'}
    #             ],
    #             'url': {
    #                 'url': 'https://weko3.example.org/record/1/files/test1.txt',
    #             },
    #         }, {
    #             "filename": "test2",
    #             'subitem_1551255854908': '1.2',
    #             'subitem_1551255750794': 'application/octet-stream',
    #             'subitem_1551255788530': [
    #                 {'subitem_1570068579439': '19 MB'},
    #                 {'subitem_1570068579439': '19456 KB'}
    #             ],
    #             'url': {
    #                 'url': 'https://weko3.example.org/record/1/files/test2',
    #             }
    #         }, {
    #             "filename": "test3.png",
    #             'subitem_1551255854908': '2.1',
    #             'subitem_1551255750794': 'image/png',
    #             'subitem_1551255820788': [
    #                 {'subitem_1551255828320': '2015-10-01'}
    #             ],
    #             'url': {
    #                 'url': 'https://weko3.example.org/record/1/files/test3.png',
    #             }
    #         }
    #     ],
    #     "files_info": [{
    #         "key": "item_1570069138259",
    #         "items": [
    #             {
    #                 "filename": "test1.txt",
    #                 'subitem_1551255854908': '1.0',
    #                 'subitem_1551255750794': 'text/plain',
    #                 'subitem_1551255788530': [
    #                     {'subitem_1570068579439': '18 KB'},
    #                     {'subitem_1570068579439': '18432 B'}
    #                 ],
    #                 'subitem_1551255820788': [
    #                     {'subitem_1551255828320': '2022-10-20'},
    #                     {'subitem_1551255828320': '2022-10-21'},
    #                     {'subitem_1551255828320': '2004-03-02/2005-06-02'}
    #                 ],
    #                 'url': {
    #                     'url': 'https://weko3.example.org/record/1/files/test1.txt',
    #                 },
    #             }, {
    #                 "filename": "test2",
    #                 'subitem_1551255854908': '1.2',
    #                 'subitem_1551255750794': 'application/octet-stream',
    #                 'subitem_1551255788530': [
    #                     {'subitem_1570068579439': '19 MB'},
    #                     {'subitem_1570068579439': '19456 KB'}
    #                 ],
    #                 'url': {
    #                     'url': 'https://weko3.example.org/record/1/files/test2',
    #                 }
    #             }, {
    #                 "filename": "test3.png",
    #                 'subitem_1551255854908': '2.1',
    #                 'subitem_1551255750794': 'image/png',
    #                 'subitem_1551255820788': [
    #                     {'subitem_1551255828320': '2015-10-01'}
    #                 ],
    #                 'url': {
    #                     'url': 'https://weko3.example.org/record/1/files/test3.png',
    #                 }
    #             }
    #         ]
    #     }]
    # }

    # Case03: Parse single file
    single_xml_data = xmltodict.parse(
        """
        <testdocument>
            <jpcoar:file>
                <jpcoar:URI objectType="fulltext" label="70_5_331.pdf">http://ousar.lib.okayama-u.ac.jp/jpcoar:files/public/5/54590/20161108092537681027/70_5_331.pdf</jpcoar:URI>
                <jpcoar:mimeType>application/pdf</jpcoar:mimeType>
                <jpcoar:extent>3MB</jpcoar:extent>
                <datacite:version>1.2</datacite:version>
                <datacite:date dateType="Issued">2015-10-01</datacite:date>
            </jpcoar:file>
        </testdocument>
        """
    )['testdocument']["jpcoar:file"]
    res = {}
    add_file(schema, mapping, res, [single_xml_data])
    assert res == {
        "item_1570069138259": [
            {
                "filename": "70_5_331.pdf",
                'subitem_1551255854908': '1.2',
                'subitem_1551255750794': 'application/pdf',
                'subitem_1551255788530': [
                    {'subitem_1570068579439': '3MB'}
                ],
                'subitem_1551255820788': [
                    {'subitem_1551255828320': '2015-10-01', 'subitem_1551255833133': 'Issued'}
                ],
                'url': {
                    'url': 'http://ousar.lib.okayama-u.ac.jp/jpcoar:files/public/5/54590/20161108092537681027/70_5_331.pdf',
                    "objectType": "fulltext",
                    "label": "70_5_331.pdf"
                },
            }
        ],
        "files_info": [{
            "key": "item_1570069138259",
            "items": [
                {
                    "filename": "70_5_331.pdf",
                    'subitem_1551255854908': '1.2',
                    'subitem_1551255750794': 'application/pdf',
                    'subitem_1551255788530': [
                        {'subitem_1570068579439': '3MB'}
                    ],
                    'subitem_1551255820788': [
                        {'subitem_1551255828320': '2015-10-01', 'subitem_1551255833133': 'Issued'}
                    ],
                    'url': {
                        'url': 'http://ousar.lib.okayama-u.ac.jp/jpcoar:files/public/5/54590/20161108092537681027/70_5_331.pdf',
                        "objectType": "fulltext",
                        "label": "70_5_331.pdf"
                    },
                }
            ]
        }]
    }

    # Case04: Parse empty file
    res = {}
    add_file(schema, mapping, res, [])
    assert res == {}


# def add_catalog(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::test_add_catalog -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_add_catalog():
    schema = {
        "item_catalog": {
            "type": "object",
            "properties": {
                "contibutors": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "contributorType": {
                                "enum": [None, "HostingInstitution"],
                                "type": ["null", "string"],
                                "format": "select",
                                "currentEnum": ["HostingInstitution"]
                            },
                            "names": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                            "format": "text"
                                        },
                                        "lang": {
                                            "enum": [None, "ja", "en"],
                                            "type": ["null", "string"],
                                            "format": "select",
                                            "currentEnum": ["ja", "en"]
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "identifier": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "identifierType": {
                                "enum": [None, "DOI", "HDL", "URI"],
                                "type": ["null", "string"],
                                "format": "select",
                                "currentEnum": ["DOI", "HDL", "URI"]
                            },
                            "value": {
                                "type": "string",
                                "format": "text"
                            }
                        }
                    }
                },
                "title": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "format": "text"
                            },
                            "lang": {
                                "enum": [None, "ja", "en"],
                                "type": ["null", "string"],
                                "format": "select",
                                "currentEnum": ["ja", "en"]
                            }
                        }
                    }
                },
                "description": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "value": {
                                "type": "string",
                                "format": "text",
                            },
                            "descriptionType": {
                                "enum": [None, "Abstract", "Methods", "TableOfContents", "TechnicalInfo", "Other"],
                                "type": ["null", "string"],
                                "format": "select",
                                "currentEnum": ["Abstract", "Methods", "TableOfContents", "TechnicalInfo", "Other"]
                            },
                            "lang": {
                                "enum": [None, "ja", "en"],
                                "type": ["null", "string"],
                                "format": "select",
                                "currentEnum": ["ja", "en"]
                            }
                        }
                    }
                },
                "subject": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "value": {
                                "type": "string",
                                "format": "text",
                            },
                            "subjectScheme": {
                                "enum": [None, "BSH", "DDC", "e-Rad_field"],
                                "type": ["null", "string"],
                                "format": "select",
                                "currentEnum": ["BSH", "DDC", "e-Rad_field"]
                            },
                            "subjectURI": {
                                "type": "string",
                                "format": "text",
                            },
                            "lang": {
                                "enum": [None, "ja", "en"],
                                "type": ["null", "string"],
                                "format": "select",
                                "currentEnum": ["ja", "en"]
                            }
                        }
                    }
                },
                "license": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "value": {
                                "type": "string",
                                "format": "text",
                            },
                            "licenseType": {
                                "enum": [None, "file", "metadata", "thumbnail"],
                                "type": ["null", "string"],
                                "format": "select",
                                "currentEnum": ["file", "metadata", "thumbnail"]
                            },
                            "resource": {
                                "type": "string",
                                "format": "text",
                            },
                            "lang": {
                                "enum": [None, "ja", "en"],
                                "type": ["null", "string"],
                                "format": "select",
                                "currentEnum": ["ja", "en"]
                            }
                        }
                    }
                },
                "rights": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "value": {
                                "type": "string",
                                "format": "text",
                            },
                            "resource": {
                                "type": "string",
                                "format": "text",
                            },
                            "lang": {
                                "enum": [None, "ja", "en"],
                                "type": ["null", "string"],
                                "format": "select",
                                "currentEnum": ["ja", "en"]
                            }
                        }
                    }
                },
                "accessRights": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "value": {
                                "type": "string",
                                "format": "text",
                            },
                            "resource": {
                                "type": "string",
                                "format": "text",
                            }
                        }
                    }
                },
                "file": {
                    "type": "object",
                    "properties": {
                        "uri": {
                            "type": "object",
                            "properties": {
                                "value": {
                                    "type": "string",
                                    "format": "text",
                                },
                                "objectType": {
                                    "enum": [None, "thumbnail"],
                                    "type": ["null", "string"],
                                    "format": "select",
                                    "currentEnum": ["thumbnail"]
                                }
                            }
                        }
                    }
                }
            }
        },
        "title": "Catalog",
    }

    mapping = {
        "catalog.contributor.@attributes.contributorType": ["item_catalog.contibutor.contributorType"],
        "catalog.contributor.contributorName.@value": ["item_catalog.contibutor.names.name"],
        "catalog.contributor.contributorName.@attributes.xml:lang": ["item_catalog.contibutor.names.lang"],
        "catalog.identifier.@value": ["item_catalog.identifier.value"],
        "catalog.identifier.@attributes.identifierType": ["item_catalog.identifier.identifierType"],
        "catalog.title.@value": ["item_catalog.title.name"],
        "catalog.title.@attributes.xml:lang": ["item_catalog.title.lang"],
        "catalog.description.@value": ["item_catalog.description.value"],
        "catalog.description.@attributes.xml:lang": ["item_catalog.description.lang"],
        "catalog.description.@attributes.descriptionType": ["item_catalog.description.descriptionType"],
        "catalog.subject.@value": ["item_catalog.subject.value"],
        "catalog.subject.@attributes.xml:lang": ["item_catalog.subject.lang"],
        "catalog.subject.@attributes.subjectURI": ["item_catalog.subject.subjectURI"],
        "catalog.subject.@attributes.subjectScheme": ["item_catalog.subject.subjectScheme"],
        "catalog.license.@value": ["item_catalog.license.value"],
        "catalog.license.@attributes.xml:lang": ["item_catalog.license.lang"],
        "catalog.license.@attributes.licenseType": ["item_catalog.license.licenseType"],
        "catalog.license.@attributes.rdf:resource": ["item_catalog.license.resource"],
        "catalog.rights.@value": ["item_catalog.rights.value"],
        "catalog.rights.@attributes.xml:lang": ["item_catalog.rights.lang"],
        "catalog.rights.@attributes.rdf:resource": ["item_catalog.rights.resource"],
        "catalog.accessRights.@value": ["item_catalog.accessRights.value"],
        "catalog.accessRights.@attributes.rdf:resource": ["item_catalog.accessRights.resource"],
        "catalog.file.URI.@value": ["item_catalog.file.uri.value"],
        "catalog.file.URI.@attributes.objectType": ["item_catalog.file.uri.objectType"],
    }

    # Case01: Parse catalog and attributes
    # xml_data = xmltodict.parse(
    #     """
    #     <testdocument>
    #         <jpcoar:catalog>
    #             <jpcoar:contributor contributorType="HostingInstitution">
    #                 <jpcoar:contributorName xml:lang="ja">東京大学</jpcoar:contributorName>
    #                 <jpcoar:contributorName xml:lang="en">The University of Tokyo</jpcoar:contributorName>
    #             </jpcoar:contributor>
    #             <jpcoar:contributor contributorType="HostingInstitution">
    #                 <jpcoar:contributorName xml:lang="ja">京都大学</jpcoar:contributorName>
    #             </jpcoar:contributor>
    #             <jpcoar:identifier identifierType="DOI">DOI_sample1</jpcoar:identifier>
    #             <jpcoar:identifier identifierType="URI">https://da.dl.itc.u-tokyo.ac.jp/portal/</jpcoar:identifier>
    #             <dc:title xml:lang="ja">東京大学学術資産等アーカイブズポータル</dc:title>
    #             <dc:title xml:lang="ja-Kana">トウキョウダイガクガクジュツシサントウアーカイブズポータル</dc:title>
    #             <dc:title xml:lang="en">UTokyo Academic Archives Portal</dc:title>
    #             <datacite:description xml:lang="ja" descriptionType="Other">東京大学学術資産等アーカイブズポータルは、 「東京大学デジタルアーカイブズ構築事業」により構築されたポータルサイトです。当事業によりデジタル化された資料だけでなく、これまで学内の様々な部局が個別にデジタル化し公開してきたコレクションを、横断的に検索することができます。</datacite:description>
    #             <datacite:description xml:lang="ja" descriptionType="Abstract">記述サンプル1</datacite:description>
    #             <jpcoar:subject subjectScheme="Other">書籍等</jpcoar:subject>
    #             <jpcoar:subject subjectScheme="Other">人文学</jpcoar:subject>
    #             <jpcoar:subject subjectScheme="Other">自然史・理工学</jpcoar:subject>
    #             <jpcoar:subject subjectScheme="Other">公文書</jpcoar:subject>
    #             <jpcoar:subject subjectScheme="Other">文化財</jpcoar:subject>
    #             <jpcoar:license xml:lang="ja" licenseType="metadata" rdf:resource="https://da.dl.itc.u-tokyo.ac.jp/portal/help/collection">連携コレクション一覧</jpcoar:license>
    #             <jpcoar:license xml:lang="en" licenseType="file" rdf:resource="https://rightsstatements.org/page/NoC-CR/1.0/">NO COPYRIGHT - CONTRACTUAL RESTRICTIONS</jpcoar:license>
    #             <dc:rights xml:lang="ja">著作権の帰属はコレクションによって異なる</dc:rights>
    #             <dc:rights xml:lang="ja">サンプル権利1</dc:rights>
    #             <dcterms:accessRights rdf:resource="http://purl.org/coar/access_right/c_abf2">open access</dcterms:accessRights>
    #             <jpcoar:file>
    #                 <jpcoar:URI objectType="thumbnail">https://xxx.xxx.xxx.xxx/xxx/thumbnail.jpg</jpcoar:URI>
    #             </jpcoar:file>
    #         </jpcoar:catalog>
    #     </testdocument>
    #     """
    # )['testdocument']["jpcoar:catalog"]
    # res = {}
    # add_catalog(schema, mapping, res, xml_data)
    # assert res == {
    #     "item_catalog": {
    #         "contibutor": [
    #             {
    #                 "contributorType": "HostingInstitution",
    #                 "names": [
    #                     {"name": "東京大学", "lang": "ja"},
    #                     {"name": "The University of Tokyo", "lang": "en"},
    #                 ]
    #             }, {
    #                 "contributorType": "HostingInstitution",
    #                 "names": [
    #                     {"name": "京都大学", "lang": "ja"},
    #                 ]
    #             }
    #         ],
    #         "identifier": [
    #             {"identifierType": "DOI", "value": "DOI_sample1"},
    #             {"identifierType": "URI", "value": "https://da.dl.itc.u-tokyo.ac.jp/portal/"},
    #         ],
    #         "title": [
    #             {"name": "東京大学学術資産等アーカイブズポータル", "lang": "ja"},
    #             {"name": "トウキョウダイガクガクジュツシサントウアーカイブズポータル", "lang": "ja-Kana"},
    #             {"name": "UTokyo Academic Archives Portal", "lang": "en"},
    #         ],
    #         "description": [
    #             {"lang": "ja", "descriptionType": "Other", "value": "東京大学学術資産等アーカイブズポータルは、 「東京大学デジタルアーカイブズ構築事業」により構築されたポータルサイトです。当事業によりデジタル化された資料だけでなく、これまで学内の様々な部局が個別にデジタル化し公開してきたコレクションを、横断的に検索することができます。"},
    #             {"lang": "ja", "descriptionType": "Abstract", "value": "記述サンプル1"}
    #         ],
    #         "subject": [
    #             {"subjectScheme": "Other", "value": "書籍等"},
    #             {"subjectScheme": "Other", "value": "人文学"},
    #             {"subjectScheme": "Other", "value": "自然史・理工学"},
    #             {"subjectScheme": "Other", "value": "公文書"},
    #             {"subjectScheme": "Other", "value": "文化財"}
    #         ],
    #         "license": [
    #             {"value": "連携コレクション一覧", "licenseType": "metadata", "resource": "https://da.dl.itc.u-tokyo.ac.jp/portal/help/collection", "lang": "ja"},
    #             {"value": "NO COPYRIGHT - CONTRACTUAL RESTRICTIONS", "licenseType": "file", "resource": "https://rightsstatements.org/page/NoC-CR/1.0/", "lang": "en"},
    #         ],
    #         "rights": [
    #             {"value": ">著作権の帰属はコレクションによって異なる", "lang": "ja"},
    #             {"value": ">サンプル権利1", "lang": "ja"},
    #         ],
    #         "accessRights": {
    #             "value": "open access",
    #             "resource": "http://purl.org/coar/access_right/c_abf2"
    #         },
    #         "file": {
    #             "uri": {
    #                 "value": "https://xxx.xxx.xxx.xxx/xxx/thumbnail.jpg",
    #                 "objectType": "thumbnail"
    #             }
    #         }
    #     }
    # }

    # Case02: Parse catalog (without attributes)
    # TODO: test after bugfix

    # Case03: Parse single catalog
    # TODO: test after bugfix

    # Case04: Parse empty degree grantor
    res = {}
    add_catalog(schema, mapping, res, [])
    assert res == {}


# class BaseMapper:
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::TestBaseMapper -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
class TestBaseMapper:
#     def update_itemtype_map(cls):
#     def __init__(self, xml):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::TestBaseMapper::test_init -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
    def test_init(self,app,db):
        xml_str="""
        <jpcoar:jpcoar xmlns:datacite="https://schema.datacite.org/meta/kernel-4/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcndl="http://ndl.go.jp/dcndl/terms/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:jpcoar="https://github.com/JPCOAR/schema/blob/master/1.0/" xmlns:oaire="http://namespace.openaire.eu/schema/oaire/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rioxxterms="http://www.rioxx.net/schema/v2.0/rioxxterms/" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="https://github.com/JPCOAR/schema/blob/master/1.0/" xsi:schemaLocation="https://github.com/JPCOAR/schema/blob/master/1.0/jpcoar_scm.xsd">
            <dc:title xml:lang="ja">test full item</dc:title>
            <dcterms:alternative xml:lang="en">other title</dcterms:alternative>
            <jpcoar:creator>
                <jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/1234" nameIdentifierScheme="ORCID">1234</jpcoar:nameIdentifier>
                <jpcoar:creatorName xml:lang="ja">テスト, 太郎</jpcoar:creatorName>
                <jpcoar:familyName xml:lang="ja">テスト</jpcoar:familyName>
                <jpcoar:givenName xml:lang="ja">太郎</jpcoar:givenName>
                <jpcoar:creatorAlternative xml:lang="ja">テスト　別郎</jpcoar:creatorAlternative>
                <jpcoar:affiliation>
                    <jpcoar:nameIdentifier nameIdentifierURI="http://www.isni.org/isni/5678" nameIdentifierScheme="ISNI">5678</jpcoar:nameIdentifier>
                </jpcoar:affiliation>
            </jpcoar:creator>
            <jpcoar:contributor contributorType="ContactPerson">
                <jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/5678" nameIdentifierScheme="ORCID">5678</jpcoar:nameIdentifier>
                <jpcoar:contributorName xml:lang="en">test, smith</jpcoar:contributorName>
                <jpcoar:familyName xml:lang="en">test</jpcoar:familyName>
                <jpcoar:givenName xml:lang="en">smith</jpcoar:givenName>
                <jpcoar:contributorAlternative xml:lang="en">other smith</jpcoar:contributorAlternative>
                <jpcoar:affiliation>
                    <jpcoar:nameIdentifier nameIdentifierURI="http://www.isni.org/isni/1234" nameIdentifierScheme="ISNI">1234</jpcoar:nameIdentifier>
                </jpcoar:affiliation>
            </jpcoar:contributor>
            <dcterms:accessRights rdf:resource="http://purl.org/coar/access_right/c_14cb">metadata only access</dcterms:accessRights>
            <dc:rights xml:lang="ja" rdf:resource="テスト権利情報Resource">テスト権利情報</dc:rights>
            <jpcoar:rightsHolder>
                <jpcoar:rightsHolderName xml:lang="ja">テスト　太郎</jpcoar:rightsHolderName>
            </jpcoar:rightsHolder>
            <jpcoar:subject xml:lang="ja" subjectURI="http://bsh.com" subjectScheme="BSH">テスト主題</jpcoar:subject>
            <datacite:description xml:lang="en" descriptionType="Abstract">this is test abstract.</datacite:description>
            <dc:publisher xml:lang="ja">test publisher</dc:publisher>
            <datacite:date dateType="Accepted">2022-10-20</datacite:date>
            <datacite:date dateType="Issued">2022-10-19</datacite:date>
            <dc:language>jpn</dc:language>
            <dc:type rdf:resource="http://purl.org/coar/resource_type/c_2fe3">newspaper</dc:type>
            <datacite:version>1.1</datacite:version>
            <oaire:version rdf:resource="http://purl.org/coar/version/c_b1a7d7d4d402bcce">AO</oaire:version>
            <jpcoar:identifier identifierType="DOI">1111</jpcoar:identifier>
            <jpcoar:identifier identifierType="DOI">https://doi.org/1234/0000000001</jpcoar:identifier>
            <jpcoar:identifier identifierType="URI">https://192.168.56.103/records/1</jpcoar:identifier>
            <jpcoar:identifierRegistration identifierType="JaLC">1234/0000000001</jpcoar:identifierRegistration>
            <jpcoar:relation relationType="isVersionOf">
                <jpcoar:relatedIdentifier identifierType="ARK">1111111</jpcoar:relatedIdentifier>
                <jpcoar:relatedTitle xml:lang="ja">関連情報テスト</jpcoar:relatedTitle>
            </jpcoar:relation>
            <jpcoar:relation relationType="isVersionOf">
                <jpcoar:relatedIdentifier identifierType="URI">https://192.168.56.103/records/3</jpcoar:relatedIdentifier>
            </jpcoar:relation>
            <dcterms:temporal xml:lang="ja">1 to 2</dcterms:temporal>
            <datacite:geoLocation>
                <datacite:geoLocationPoint>
                    <datacite:pointLongitude>12345</datacite:pointLongitude>
                    <datacite:pointLatitude>67890</datacite:pointLatitude>
                </datacite:geoLocationPoint>
                <datacite:geoLocationBox>
                    <datacite:westBoundLongitude>123</datacite:westBoundLongitude>
                    <datacite:eastBoundLongitude>456</datacite:eastBoundLongitude>
                    <datacite:southBoundLatitude>789</datacite:southBoundLatitude>
                    <datacite:northBoundLatitude>1112</datacite:northBoundLatitude>
                </datacite:geoLocationBox>
                <datacite:geoLocationPlace>テスト位置情報</datacite:geoLocationPlace>
            </datacite:geoLocation>
            <jpcoar:fundingReference>
                <datacite:funderIdentifier funderIdentifierType="Crossref Funder">22222</datacite:funderIdentifier>
                <jpcoar:funderName xml:lang="ja">テスト助成機関</jpcoar:funderName>
                <datacite:awardNumber awardURI="https://test.research.com">1111</datacite:awardNumber>
                <jpcoar:awardTitle xml:lang="ja">テスト研究</jpcoar:awardTitle>
            </jpcoar:fundingReference>
            <jpcoar:sourceIdentifier identifierType="PISSN">test source Identifier</jpcoar:sourceIdentifier>
            <jpcoar:sourceTitle xml:lang="ja">test collectibles</jpcoar:sourceTitle>
            <jpcoar:sourceTitle xml:lang="ja">test title book</jpcoar:sourceTitle>
            <jpcoar:volume>5</jpcoar:volume>
            <jpcoar:issue>2</jpcoar:issue>
            <jpcoar:numPages>333</jpcoar:numPages>
            <jpcoar:pageStart>123</jpcoar:pageStart>
            <jpcoar:pageEnd>456</jpcoar:pageEnd>
            <dcndl:dissertationNumber>9999</dcndl:dissertationNumber>
            <dcndl:degreeName xml:lang="ja">テスト学位</dcndl:degreeName>
            <dcndl:dateGranted>2022-10-19</dcndl:dateGranted>
            <jpcoar:degreeGrantor>
                <jpcoar:nameIdentifier nameIdentifierScheme="kakenhi">学位授与機関識別子テスト</jpcoar:nameIdentifier>
                <jpcoar:degreeGrantorName xml:lang="ja">学位授与機関</jpcoar:degreeGrantorName>
            </jpcoar:degreeGrantor>
            <jpcoar:conference>
                <jpcoar:conferenceName xml:lang="ja">テスト会議</jpcoar:conferenceName>
                <jpcoar:conferenceSequence>12345</jpcoar:conferenceSequence>
                <jpcoar:conferenceSponsor xml:lang="ja">テスト機関</jpcoar:conferenceSponsor>
                <jpcoar:conferenceDate endDay="1" endYear="2005" endMonth="12" startDay="11" xml:lang="ja" startYear="2000" startMonth="4">12</jpcoar:conferenceDate>
                <jpcoar:conferenceVenue xml:lang="ja">テスト会場</jpcoar:conferenceVenue>
                <jpcoar:conferenceCountry>JPN</jpcoar:conferenceCountry>
            </jpcoar:conference>
            <jpcoar:file>
                <jpcoar:URI>https://weko3.example.org/record/1/files/test1.txt</jpcoar:URI>
                <jpcoar:mimeType>text/plain</jpcoar:mimeType>
                <jpcoar:extent>18 B</jpcoar:extent>
                <datacite:date dateType="Accepted">2022-10-20</datacite:date>
                <datacite:version>1.0</datacite:version>
            </jpcoar:file>
            <jpcoar:file>
                <jpcoar:URI>https://weko3.example.org/record/1/files/test2</jpcoar:URI>
                <jpcoar:mimeType>application/octet-stream</jpcoar:mimeType>
                <jpcoar:extent>18 B</jpcoar:extent>
                <datacite:version>1.2</datacite:version>
            </jpcoar:file>
            <jpcoar:file>
                <jpcoar:URI>https://weko3.example.org/record/1/files/test3.png</jpcoar:URI>
                <jpcoar:mimeType>image/png</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent>
                <datacite:version>2.1</datacite:version>
            </jpcoar:file>
        </jpcoar:jpcoar>"""
        # not exist item_type with name "Multiple" or "Others"
        item_type_name1 = ItemTypeName(
            id=10, name="test_itemtype", has_site_license=True, is_active=True
        )
        item_type1 = ItemType(
            id=10,name_id=10,harvesting_type=True,schema={},form={},render={},tag=1,version_id=1,is_deleted=False,
        )
        db.session.add(item_type_name1)
        db.session.add(item_type1)
        db.session.commit()
        mapper = BaseMapper(xml_str)
        assert mapper.itemtype is None

        # exist item_type with name "Multiple" or "Others"
        item_type_name2 = ItemTypeName(
            id=11, name="Multiple", has_site_license=True, is_active=True
        )
        item_type2 = ItemType(
            id=11,name_id=11,harvesting_type=True,schema={},form={},render={},tag=1,version_id=1,is_deleted=False,
        )
        db.session.add(item_type_name2)
        db.session.add(item_type2)
        db.session.commit()
        BaseMapper.update_itemtype_map()
        mapper = BaseMapper(xml_str)
        assert mapper.itemtype == item_type2


# update_itemtype_map(cls)
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::TestBaseMapper::test_update_itemtype_map -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
    def test_update_itemtype_map(self, db_itemtype_jpcoar):
        BaseMapper.update_itemtype_map()
        item_type_name = db_itemtype_jpcoar["item_type_multiple_name"].name
        assert item_type_name in BaseMapper.itemtype_map
        assert type(BaseMapper.itemtype_map[item_type_name]) == ItemType


# class JPCOARV2Mapper(BaseMapper):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::TestJPCOARV2Mapper -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
class TestJPCOARV2Mapper:
#     def map(self):
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::TestJPCOARV2Mapper::test_map -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
    def test_map(self,db_itemtype):
        deleted_xml = ''
        mapper = JPCOARV2Mapper(deleted_xml)
        result = mapper.map(12)
        assert result == {"pubdate": date.today().isoformat()}

        # xml_str = '<jpcoar:jpcoar xmlns:datacite="https://schema.datacite.org/meta/kernel-4/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcndl="http://ndl.go.jp/dcndl/terms/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:jpcoar="https://github.com/JPCOAR/schema/blob/master/1.0/" xmlns:oaire="http://namespace.openaire.eu/schema/oaire/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rioxxterms="http://www.rioxx.net/schema/v2.0/rioxxterms/" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="https://github.com/JPCOAR/schema/blob/master/1.0/" xsi:schemaLocation="https://github.com/JPCOAR/schema/blob/master/1.0/jpcoar_scm.xsd"><dc:title xml:lang="ja">test full item</dc:title><dcterms:alternative xml:lang="en">other title</dcterms:alternative><jpcoar:creator><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/1234" nameIdentifierScheme="ORCID">1234</jpcoar:nameIdentifier><jpcoar:creatorName xml:lang="ja">テスト, 太郎</jpcoar:creatorName><jpcoar:familyName xml:lang="ja">テスト</jpcoar:familyName><jpcoar:givenName xml:lang="ja">太郎</jpcoar:givenName><jpcoar:creatorAlternative xml:lang="ja">テスト　別郎</jpcoar:creatorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="http://www.isni.org/isni/5678" nameIdentifierScheme="ISNI">5678</jpcoar:nameIdentifier></jpcoar:affiliation></jpcoar:creator><jpcoar:contributor contributorType="ContactPerson"><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/5678" nameIdentifierScheme="ORCID">5678</jpcoar:nameIdentifier><jpcoar:contributorName xml:lang="en">test, smith</jpcoar:contributorName><jpcoar:familyName xml:lang="en">test</jpcoar:familyName><jpcoar:givenName xml:lang="en">smith</jpcoar:givenName><jpcoar:contributorAlternative xml:lang="en">other smith</jpcoar:contributorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="http://www.isni.org/isni/1234" nameIdentifierScheme="ISNI">1234</jpcoar:nameIdentifier></jpcoar:affiliation></jpcoar:contributor><dcterms:accessRights rdf:resource="http://purl.org/coar/access_right/c_14cb">metadata only access</dcterms:accessRights><rioxxterms:apc>Paid</rioxxterms:apc><dc:rights xml:lang="ja" rdf:resource="テスト権利情報Resource">テスト権利情報</dc:rights><jpcoar:rightsHolder><jpcoar:rightsHolderName xml:lang="ja">テスト　太郎</jpcoar:rightsHolderName></jpcoar:rightsHolder><jpcoar:subject xml:lang="ja" subjectURI="http://bsh.com" subjectScheme="BSH">テスト主題</jpcoar:subject><datacite:description xml:lang="en" descriptionType="Abstract">this is test abstract.</datacite:description><dc:publisher xml:lang="ja">test publisher</dc:publisher><datacite:date dateType="Accepted">2022-10-20</datacite:date><datacite:date dateType="Issued">2022-10-19</datacite:date><dc:language>jpn</dc:language><dc:type rdf:resource="http://purl.org/coar/resource_type/c_2fe3">newspaper</dc:type><datacite:version>1.1</datacite:version><oaire:version rdf:resource="http://purl.org/coar/version/c_b1a7d7d4d402bcce">AO</oaire:version><jpcoar:identifier identifierType="DOI">1111</jpcoar:identifier><jpcoar:identifier identifierType="DOI">https://doi.org/1234/0000000001</jpcoar:identifier><jpcoar:identifier identifierType="URI">https://192.168.56.103/records/1</jpcoar:identifier><jpcoar:identifierRegistration identifierType="JaLC">1234/0000000001</jpcoar:identifierRegistration><jpcoar:relation relationType="isVersionOf"><jpcoar:relatedIdentifier identifierType="ARK">1111111</jpcoar:relatedIdentifier><jpcoar:relatedTitle xml:lang="ja">関連情報テスト</jpcoar:relatedTitle></jpcoar:relation><jpcoar:relation relationType="isVersionOf"><jpcoar:relatedIdentifier identifierType="URI">https://192.168.56.103/records/3</jpcoar:relatedIdentifier></jpcoar:relation><dcterms:temporal xml:lang="ja">1 to 2</dcterms:temporal><datacite:geoLocation><datacite:geoLocationPoint><datacite:pointLongitude>12345</datacite:pointLongitude><datacite:pointLatitude>67890</datacite:pointLatitude></datacite:geoLocationPoint><datacite:geoLocationBox><datacite:westBoundLongitude>123</datacite:westBoundLongitude><datacite:eastBoundLongitude>456</datacite:eastBoundLongitude><datacite:southBoundLatitude>789</datacite:southBoundLatitude><datacite:northBoundLatitude>1112</datacite:northBoundLatitude></datacite:geoLocationBox><datacite:geoLocationPlace>テスト位置情報</datacite:geoLocationPlace></datacite:geoLocation><jpcoar:fundingReference><datacite:funderIdentifier funderIdentifierType="Crossref Funder">22222</datacite:funderIdentifier><jpcoar:funderName xml:lang="ja">テスト助成機関</jpcoar:funderName><datacite:awardNumber awardURI="https://test.research.com">1111</datacite:awardNumber><jpcoar:awardTitle xml:lang="ja">テスト研究</jpcoar:awardTitle></jpcoar:fundingReference><jpcoar:sourceIdentifier identifierType="PISSN">test source Identifier</jpcoar:sourceIdentifier><jpcoar:sourceTitle xml:lang="ja">test collectibles</jpcoar:sourceTitle><jpcoar:sourceTitle xml:lang="ja">test title book</jpcoar:sourceTitle><jpcoar:volume>5</jpcoar:volume><jpcoar:volume>1</jpcoar:volume><jpcoar:issue>2</jpcoar:issue><jpcoar:issue>2</jpcoar:issue><jpcoar:numPages>333</jpcoar:numPages><jpcoar:numPages>555</jpcoar:numPages><jpcoar:pageStart>123</jpcoar:pageStart><jpcoar:pageStart>789</jpcoar:pageStart><jpcoar:pageEnd>456</jpcoar:pageEnd><jpcoar:pageEnd>234</jpcoar:pageEnd><dcndl:dissertationNumber>9999</dcndl:dissertationNumber><dcndl:degreeName xml:lang="ja">テスト学位</dcndl:degreeName><dcndl:dateGranted>2022-10-19</dcndl:dateGranted><jpcoar:degreeGrantor><jpcoar:nameIdentifier nameIdentifierScheme="kakenhi">学位授与機関識別子テスト</jpcoar:nameIdentifier><jpcoar:degreeGrantorName xml:lang="ja">学位授与機関</jpcoar:degreeGrantorName></jpcoar:degreeGrantor><jpcoar:conference><jpcoar:conferenceName xml:lang="ja">テスト会議</jpcoar:conferenceName><jpcoar:conferenceSequence>12345</jpcoar:conferenceSequence><jpcoar:conferenceSponsor xml:lang="ja">テスト機関</jpcoar:conferenceSponsor><jpcoar:conferenceDate endDay="1" endYear="2005" endMonth="12" startDay="11" xml:lang="ja" startYear="2000" startMonth="4">12</jpcoar:conferenceDate><jpcoar:conferenceVenue xml:lang="ja">テスト会場</jpcoar:conferenceVenue><jpcoar:conferenceCountry>JPN</jpcoar:conferenceCountry></jpcoar:conference><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test1.txt</jpcoar:URI><jpcoar:mimeType>text/plain</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:date dateType="Accepted">2022-10-20</datacite:date><datacite:version>1.0</datacite:version></jpcoar:file><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test2</jpcoar:URI><jpcoar:mimeType>application/octet-stream</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:version>1.2</datacite:version></jpcoar:file><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test3.png</jpcoar:URI><jpcoar:mimeType>image/png</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:version>2.1</datacite:version></jpcoar:file></jpcoar:jpcoar>'
        # mapper = JPCOARV2Mapper(xml_str)
        # test = {'$schema': 10, "pubdate": date.today().isoformat(), 'item_1551264308487': [{'subitem_1551255647225': 'test full item', 'subitem_1551255648112': 'ja'}], 'title': 'test full item', 'item_1551264326373': [{'subitem_1551255720400': 'other title', 'subitem_1551255721061': 'en'}], 'item_1551264340087': [{'subitem_1551255991424': [{'subitem_1551256006332': '太郎', 'subitem_1551256007414': 'ja'}], 'subitem_1551255929209': [{'subitem_1551255938498': 'テスト', 'subitem_1551255964991': 'ja'}], 'subitem_1551255898956': [{'subitem_1551255905565': 'テスト, 太郎', 'subitem_1551255907416': 'ja'}], 'subitem_1551256025394': [{'subitem_1551256035730': 'テスト\u3000別郎', 'subitem_1551256055588': 'ja'}]}], 'item_1551264418667': [{'subitem_1551257036415': 'ContactPerson', 'subitem_1551257339190': [{'subitem_1551257342360': '', 'subitem_1551257343979': 'en'}], 'subitem_1551257272214': [{'subitem_1551257314588': 'test', 'subitem_1551257316910': 'en'}], 'subitem_1551257245638': [{'subitem_1551257276108': 'test, smith', 'subitem_1551257279831': 'en'}], 'subitem_1551257372442': [{'subitem_1551257374288': 'other smith', 'subitem_1551257375939': 'en'}]}], 'item_1551264447183': [{'subitem_1551257553743': 'metadata only access', 'subitem_1551257578398': 'http://purl.org/coar/access_right/c_14cb'}], 'item_1551264605515': [{'subitem_1551257776901': 'Paid'}], 'item_1551264629907': [{'subitem_1551257025236': [{'subitem_1551257043769': 'テスト権利情報', 'subitem_1551257047388': 'ja'}], 'subitem_1551257030435': 'テスト権利情報Resource'}], 'item_1551264767789': [{'subitem_1551257249371': [{'subitem_1551257255641': 'テスト\u3000太郎', 'subitem_1551257257683': 'ja'}]}], 'item_1551264822581': [{'subitem_1551257315453': 'テスト主題', 'subitem_1551257323812': 'ja', 'subitem_1551257343002': 'http://bsh.com', 'subitem_1551257329877': 'BSH'}], 'item_1551264846237': [{'subitem_1551255577890': 'this is test abstract.', 'subitem_1551255592625': 'en', 'subitem_1551255637472': 'Abstract'}], 'item_1551264917614': [{'subitem_1551255702686': 'test publisher', 'subitem_1551255710277': 'ja'}], 'item_1551264974654': [{'subitem_1551255753471': '2022-10-20', 'subitem_1551255775519': 'Accepted'}, {'subitem_1551255753471': '2022-10-19', 'subitem_1551255775519': 'Issued'}], 'item_1551265002099': [{'subitem_1551255818386': 'jpn'}], 'item_1551265032053': [{'resourcetype': 'newspaper', 'resourceuri': 'http://purl.org/coar/resource_type/c_2fe3'}], 'item_1551265075370': [{'subitem_1551255975405': '1.1'}], 'item_1551265118680': [{'subitem_1551256025676': 'AO'}], 'system_identifier_doi': [{'subitem_systemidt_identifier': '1111', 'subitem_systemidt_identifier_type': 'DOI'}, {'subitem_systemidt_identifier': 'https://doi.org/1234/0000000001', 'subitem_systemidt_identifier_type': 'DOI'}, {'subitem_systemidt_identifier': 'https://192.168.56.103/records/1', 'subitem_systemidt_identifier_type': 'URI'}], 'item_1581495499605': [{'subitem_1551256250276': '1234/0000000001', 'subitem_1551256259586': 'JaLC'}], 'item_1551265227803': [{'subitem_1551256388439': 'isVersionOf', 'subitem_1551256480278': [{'subitem_1551256498531': '関連情報テスト', 'subitem_1551256513476': 'ja'}], 'subitem_1551256465077': [{'subitem_1551256478339': '1111111', 'subitem_1551256629524': 'ARK'}]}, {'subitem_1551256388439': 'isVersionOf', 'subitem_1551256465077': [{'subitem_1551256478339': 'https://192.168.56.103/records/3', 'subitem_1551256629524': 'URI'}]}], 'item_1551265302120': [{'subitem_1551256918211': '1 to 2', 'subitem_1551256920086': 'ja'}], 'item_1551265385290': [{'subitem_1551256462220': [{'subitem_1551256653656': 'テスト助成機関', 'subitem_1551256657859': 'ja'}], 'subitem_1551256454316': [{'subitem_1551256614960': '22222', 'subitem_1551256619706': 'Crossref Funder'}], 'subitem_1551256688098': [{'subitem_1551256691232': 'テスト研究', 'subitem_1551256694883': 'ja'}], 'subitem_1551256665850': [{'subitem_1551256671920': '1111', 'subitem_1551256679403': 'https://test.research.com'}]}], 'item_1551265409089': [{'subitem_1551256405981': 'test source Identifier', 'subitem_1551256409644': 'PISSN'}], 'item_1551265438256': [{'subitem_1551256349044': 'test collectibles', 'subitem_1551256350188': 'ja'}, {'subitem_1551256349044': 'test title book', 'subitem_1551256350188': 'ja'}], 'item_1551265463411': [{'subitem_1551256328147': '5'}, {'subitem_1551256328147': '1'}], 'item_1551265520160': [{'subitem_1551256294723': '2'}, {'subitem_1551256294723': '2'}], 'item_1551265553273': [{'subitem_1551256248092': '333'}, {'subitem_1551256248092': '555'}], 'item_1551265569218': [{'subitem_1551256198917': '123'}, {'subitem_1551256198917': '789'}, {'subitem_1551256198917': '456'}, {'subitem_1551256198917': '234'}], 'item_1551265738931': [{'subitem_1551256171004': '9999'}], 'item_1551265790591': [{'subitem_1551256126428': 'テスト学位', 'subitem_1551256129013': 'ja'}], 'item_1551265811989': [{'subitem_1551256096004': '2022-10-19'}], 'item_1551265903092': [{'subitem_1551256015892': [{'subitem_1551256027296': '学位授与機関識別子テスト', 'subitem_1551256029891': 'kakenhi'}], 'subitem_1551256037922': [{'subitem_1551256042287': '学位授与機関', 'subitem_1551256047619': 'ja'}]}], 'item_1551265973055': [{'subitem_1599711813532': 'JPN', 'subitem_1599711655652': '12345', 'subitem_1599711633003': [{'subitem_1599711636923': 'テスト会議', 'subitem_1599711645590': 'ja'}]}], 'item_1570069138259': [{'subitem_1551255854908': '1.0', 'subitem_1551255750794': 'text/plain', 'subitem_1551255788530': [{'subitem_1570068579439': '18 B'}], 'subitem_1551255820788': [{'subitem_1551255828320': '2022-10-20', 'subitem_1551255833133': 'Accepted'}], 'subitem_1551255558587': [{'subitem_1551255570271': 'https://weko3.example.org/record/1/files/test1.txt'}]}, {'subitem_1551255854908': '1.2', 'subitem_1551255750794': 'application/octet-stream', 'subitem_1551255788530': [{'subitem_1570068579439': '18 B'}], 'subitem_1551255558587': [{'subitem_1551255570271': 'https://weko3.example.org/record/1/files/test2'}]}, {'subitem_1551255854908': '2.1', 'subitem_1551255750794': 'image/png', 'subitem_1551255788530': [{'subitem_1570068579439': '18 B'}], 'subitem_1551255558587': [{'subitem_1551255570271': 'https://weko3.example.org/record/1/files/test3.png'}]}]}
        # result = mapper.map(10)
        # assert result == test

    # .tox/c1/bin/pytest -v --cov=weko_search_ui tests/test_mapper.py::TestJPCOARV2Mapper::test_map_2 -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
    def test_map_2(self,db_itemtype):
        xml_str = '<jpcoar:jpcoar xmlns:datacite="https://schema.datacite.org/meta/kernel-4/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcndl="http://ndl.go.jp/dcndl/terms/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:jpcoar="https://github.com/JPCOAR/schema/blob/master/2.0/" xmlns:oaire="http://namespace.openaire.eu/schema/oaire/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rioxxterms="http://www.rioxx.net/schema/v2.0/rioxxterms/" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="https://github.com/JPCOAR/schema/blob/master/2.0/" xsi:schemaLocation="https://github.com/JPCOAR/schema/blob/master/2.0/jpcoar_scm.xsd"><dc:title xml:lang="en">thesis_test_today</dc:title><jpcoar:creator creatorType="creator_type_test"><jpcoar:creatorName nameType="Personal" xml:lang="en">creator_name_test</jpcoar:creatorName><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="creator_aff_name_identifier_uri_test" nameIdentifierScheme="ROR">creator_aff_name_identifier</jpcoar:nameIdentifier><jpcoar:affiliationName xml:lang="en">creator_aff_name</jpcoar:affiliationName></jpcoar:affiliation></jpcoar:creator><jpcoar:contributor><jpcoar:contributorName nameType="Organizational" xml:lang="ja">contributor_name_test</jpcoar:contributorName><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="contrib_aff_name_id_uri_test" nameIdentifierScheme="GRID">contrib_aff_name_id_test</jpcoar:nameIdentifier><jpcoar:affiliationName xml:lang="en">contrib_aff_name_test</jpcoar:affiliationName></jpcoar:affiliation></jpcoar:contributor><jpcoar:subject xml:lang="en" subjectURI="subject_uri_test" subjectScheme="DDC">subject_test</jpcoar:subject><datacite:date>2023-06-15</datacite:date><dc:type rdf:resource="http://purl.org/coar/resource_type/c_46ec">thesis</dc:type><jpcoar:identifier identifierType="URI">https://localhost/records/26</jpcoar:identifier><jpcoar:relation relationType="inSeries"><jpcoar:relatedIdentifier identifierType="WOS">related_identifier_test</jpcoar:relatedIdentifier><jpcoar:relatedTitle xml:lang="en">related_title_test</jpcoar:relatedTitle></jpcoar:relation><jpcoar:fundingReference><jpcoar:funderIdentifier funderIdentifierType="Crossref Funder" funderIdentifierTypeURI="funder_identifier_type_uri_test">funder_identifier_test</jpcoar:funderIdentifier><jpcoar:awardNumber awardURI="award_number_uri_test" awardNumberType="JGN">award_number_test</jpcoar:awardNumber><jpcoar:fundingStreamIdentifier fundingStreamIdentifierType="Crossref Funder" fundingStreamIdentifierTypeURI="funding_stream_identifier_type_uri_test">funding_stream_identifier_test</jpcoar:fundingStreamIdentifier><jpcoar:fundingStream xml:lang="en">funding_stream_test</jpcoar:fundingStream></jpcoar:fundingReference><jpcoar:publisher><jpcoar:publisherName xml:lang="en">publisher_test</jpcoar:publisherName><jpcoar:publisherDescription xml:lang="ja">description_test</jpcoar:publisherDescription><dcndl:location>location_test</dcndl:location><dcndl:publicationPlace>publication_place_test</dcndl:publicationPlace></jpcoar:publisher><dcterms:date>2016</dcterms:date><dcndl:edition xml:lang="en">edition_test</dcndl:edition><dcndl:volumeTitle xml:lang="ja">volume_title_test</dcndl:volumeTitle><dcndl:originalLanguage>original_language_test</dcndl:originalLanguage><dcterms:extent xml:lang="en">extent_test</dcterms:extent><jpcoar:format xml:lang="en">format_test</jpcoar:format><jpcoar:holdingAgent><jpcoar:holdingAgentNameIdentifier nameIdentifierURI="holding_agent_name_identifier_uri_test" nameIdentifierScheme="ROR">holding_agent_name_identifier_test</jpcoar:holdingAgentNameIdentifier><jpcoar:holdingAgentName xml:lang="en">holding_agent_name_test</jpcoar:holdingAgentName></jpcoar:holdingAgent><jpcoar:datasetSeries>True</jpcoar:datasetSeries><jpcoar:catalog><jpcoar:contributor contributorType="HostingInstitution"><jpcoar:contributorName xml:lang="en">catalog_contributor_test</jpcoar:contributorName></jpcoar:contributor><jpcoar:identifier identifierType="DOI">catalog_identifier_test</jpcoar:identifier><dc:title xml:lang="en">catalog_title_test</dc:title><datacite:description xml:lang="ja" descriptionType="Abstract">catalog_description_test</datacite:description><jpcoar:subject xml:lang="en" subjectURI="catalog_subject_uri_test" subjectScheme="DDC">catalog_subject_test</jpcoar:subject><jpcoar:license xml:lang="en" licenseType="file" rdf:resource="catalog_rdf_license_test">catalog_license_test</jpcoar:license><dc:rights xml:lang="en" rdf:resource="catalog_rdf_rights_test">catalog_rights_test</dc:rights><dcterms:accessRights rdf:resource="catalog_rdf_access_rights_test">metadata only access</dcterms:accessRights><jpcoar:file><jpcoar:URI objectType="open access">catalog_file_test</jpcoar:URI></jpcoar:file></jpcoar:catalog></jpcoar:jpcoar>'
        mapper = JPCOARV2Mapper(xml_str)
        mapper.json["jpcoar:jpcoar"] = OrderedDict(
            [
                ("@xmlns:datacite", "https://schema.datacite.org/meta/kernel-4/"),
                ("@xmlns:dc", "http://purl.org/dc/elements/1.1/"),
                ("@xmlns:dcndl", "http://ndl.go.jp/dcndl/terms/"),
                ("@xmlns:dcterms", "http://purl.org/dc/terms/"),
                ("@xmlns:jpcoar", "https://github.com/JPCOAR/schema/blob/master/1.0/"),
                ("@xmlns:oaire", "http://namespace.openaire.eu/schema/oaire/"),
                ("@xmlns:rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
                ("@xmlns:rioxxterms", "http://www.rioxx.net/schema/v2.0/rioxxterms/"),
                ("@xmlns:xs", "http://www.w3.org/2001/XMLSchema"),
                ("@xmlns", "https://github.com/JPCOAR/schema/blob/master/1.0/"),
                (
                    "@xsi:schemaLocation",
                    "https://github.com/JPCOAR/schema/blob/master/1.0/jpcoar_scm.xsd",
                ),
                ("dc:title", {"@xml:lang": "ja", "#text": "test full item"}),
                (
                    "dcterms:alternative",
                    {"@xml:lang": "en", "#text": "other title"},
                ),
                (
                    "jpcoar:creator",
                    OrderedDict(
                        [
                            ("@creatorType", "creatorType_test"),
                            (
                                "jpcoar:nameIdentifier",
                                OrderedDict(
                                    [
                                        ("@nameIdentifierURI", "https://orcid.org/1234"),
                                        ("@nameIdentifierScheme", "ORCID"),
                                        ("#text", "1234"),
                                    ]
                                ),
                            ),
                            (
                                "jpcoar:creatorName",
                                OrderedDict
                                (
                                    [
                                        ("@xml:lang", "ja"),
                                        ("#text", "テスト, 太郎"),
                                        ("@nameType", "Personal"),
                                    ]
                                ),
                            ),
                            (
                                "jpcoar:familyName",
                                OrderedDict([("@xml:lang", "ja"), ("#text", "テスト")]),
                            ),
                            (
                                "jpcoar:givenName",
                                OrderedDict([("@xml:lang", "ja"), ("#text", "太郎")]),
                            ),
                            (
                                "jpcoar:creatorAlternative",
                                OrderedDict([("@xml:lang", "ja"), ("#text", "テスト\u3000別郎")]),
                            ),
                            (
                                "jpcoar:affiliation",
                                OrderedDict(
                                    [
                                        (
                                            "jpcoar:nameIdentifier",
                                            OrderedDict(
                                                [
                                                    (
                                                        "@nameIdentifierURI",
                                                        "http://www.isni.org/isni/5678",
                                                    ),
                                                    ("@nameIdentifierScheme", "ISNI"),
                                                    ("#text", "5678"),
                                                ]
                                            ),
                                        )
                                    ]
                                ),
                            ),
                        ]
                    ),
                ),
                (
                    "jpcoar:contributor",
                    OrderedDict(
                        [
                            ("@contributorType", "ContactPerson"),
                            (
                                "jpcoar:nameIdentifier",
                                OrderedDict(
                                    [
                                        ("@nameIdentifierURI", "https://orcid.org/5678"),
                                        ("@nameIdentifierScheme", "ORCID"),
                                        ("#text", "5678"),
                                    ]
                                ),
                            ),
                            (
                                "jpcoar:contributorName",
                                OrderedDict(
                                    [
                                        ("@xml:lang", "en"),
                                        ("#text", "test, smith"),
                                        ("@nameType", "Personal"),
                                    ]
                                ),
                            ),
                            (
                                "jpcoar:familyName",
                                OrderedDict([("@xml:lang", "en"), ("#text", "test")]),
                            ),
                            (
                                "jpcoar:givenName",
                                OrderedDict([("@xml:lang", "en"), ("#text", "smith")]),
                            ),
                            (
                                "jpcoar:contributorAlternative",
                                OrderedDict([("@xml:lang", "en"), ("#text", "other smith")]),
                            ),
                            (
                                "jpcoar:affiliation",
                                OrderedDict(
                                    [
                                        (
                                            "jpcoar:nameIdentifier",
                                            OrderedDict(
                                                [
                                                    (
                                                        "@nameIdentifierURI",
                                                        "http://www.isni.org/isni/1234",
                                                    ),
                                                    ("@nameIdentifierScheme", "ISNI"),
                                                    ("#text", "1234"),
                                                ]
                                            ),
                                        )
                                    ]
                                ),
                            ),
                        ]
                    ),
                ),
                (
                    "dcterms:accessRights",
                    OrderedDict(
                        [
                            ("@rdf:resource", "http://purl.org/coar/access_right/c_14cb"),
                            ("#text", "metadata only access"),
                        ]
                    ),
                ),
                ("rioxxterms:apc", "Paid"),
                (
                    "dc:rights",
                    OrderedDict(
                        [
                            ("@xml:lang", "ja"),
                            ("@rdf:resource", "テスト権利情報Resource"),
                            ("#text", "テスト権利情報"),
                        ]
                    ),
                ),
                (
                    "jpcoar:rightsHolder",
                    OrderedDict(
                        [
                            (
                                "jpcoar:rightsHolderName",
                                OrderedDict([("@xml:lang", "ja"), ("#text", "テスト\u3000太郎")]),
                            )
                        ]
                    ),
                ),
                (
                    "jpcoar:subject",
                    OrderedDict(
                        [
                            ("@xml:lang", "ja"),
                            ("@subjectURI", "http://bsh.com"),
                            ("@subjectScheme", "BSH"),
                            ("#text", "テスト主題"),
                        ]
                    ),
                ),
                (
                    "datacite:description",
                    OrderedDict(
                        [
                            ("@xml:lang", "en"),
                            ("@descriptionType", "Abstract"),
                            ("#text", "this is test abstract."),
                        ]
                    ),
                ),
                (
                    "dc:publisher",
                    OrderedDict([("@xml:lang", "ja"), ("#text", "test publisher")]),
                ),
                (
                    "datacite:date",
                    [
                        OrderedDict([("@dateType", "Accepted"), ("#text", "2022-10-20")]),
                        OrderedDict([("@dateType", "Issued"), ("#text", "2022-10-19")]),
                    ],
                ),
                ("dc:language", "jpn"),
                (
                    "dc:type",
                    OrderedDict(
                        [
                            ("@rdf:resource", "http://purl.org/coar/resource_type/c_2fe3"),
                            ("#text", "newspaper"),
                        ]
                    ),
                ),
                ("datacite:version", "1.1"),
                (
                    "oaire:version",
                    OrderedDict(
                        [
                            (
                                "@rdf:resource",
                                "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
                            ),
                            ("#text", "AO"),
                        ]
                    ),
                ),
                (
                    "jpcoar:identifier",
                    [
                        OrderedDict([("@identifierType", "DOI"), ("#text", "1111")]),
                        OrderedDict(
                            [
                                ("@identifierType", "DOI"),
                                ("#text", "https://doi.org/1234/0000000001"),
                            ]
                        ),
                        OrderedDict(
                            [
                                ("@identifierType", "URI"),
                                ("#text", "https://192.168.56.103/records/1"),
                            ]
                        ),
                    ],
                ),
                (
                    "jpcoar:identifierRegistration",
                    OrderedDict([("@identifierType", "JaLC"), ("#text", "1234/0000000001")]),
                ),
                (
                    "jpcoar:relation",
                    [
                        OrderedDict(
                            [
                                ("@relationType", "isVersionOf"),
                                (
                                    "jpcoar:relatedIdentifier",
                                    OrderedDict(
                                        [("@identifierType", "ARK"), ("#text", "1111111")]
                                    ),
                                ),
                                (
                                    "jpcoar:relatedTitle",
                                    OrderedDict([("@xml:lang", "ja"), ("#text", "関連情報テスト")]),
                                ),
                            ]
                        ),
                        OrderedDict(
                            [
                                ("@relationType", "isVersionOf"),
                                (
                                    "jpcoar:relatedIdentifier",
                                    OrderedDict(
                                        [
                                            ("@identifierType", "URI"),
                                            ("#text", "https://192.168.56.103/records/3"),
                                        ]
                                    ),
                                ),
                            ]
                        ),
                    ],
                ),
                ("dcterms:temporal", OrderedDict([("@xml:lang", "ja"), ("#text", "1 to 2")])),
                (
                    "datacite:geoLocation",
                    OrderedDict(
                        [
                            (
                                "datacite:geoLocationPoint",
                                OrderedDict(
                                    [
                                        ("datacite:pointLongitude", "12345"),
                                        ("datacite:pointLatitude", "67890"),
                                    ]
                                ),
                            ),
                            (
                                "datacite:geoLocationBox",
                                OrderedDict(
                                    [
                                        ("datacite:westBoundLongitude", "123"),
                                        ("datacite:eastBoundLongitude", "456"),
                                        ("datacite:southBoundLatitude", "789"),
                                        ("datacite:northBoundLatitude", "1112"),
                                    ]
                                ),
                            ),
                            ("datacite:geoLocationPlace", "テスト位置情報"),
                        ]
                    ),
                ),
                (
                    "jpcoar:fundingReference",
                    OrderedDict(
                        [
                            (
                                "jpcoar:fundingStreamIdentifier",
                                OrderedDict(
                                    [
                                        ("@fundingStreamIdentifierType", "Crossref Funder"),
                                        ("@fundingStreamIdentifierTypeURI", "fundingStreamIdentifierTypeURI_test"),
                                    ]
                                ),
                            ),
                            (
                                "jpcoar:fundingStream",
                                OrderedDict(
                                    [
                                        ("@xml:lang", "ja"),
                                        ("#text", "fundingStream_test")
                                    ]
                                )
                            ),
                            (
                                "jpcoar:funderIdentifier",
                                OrderedDict(
                                    [
                                        ("@funderIdentifierType", "Crossref Funder"),
                                        ("@funderIdentifierTypeURI", "funderIdentifierTypeURI_test"),
                                        ("#text", "22222"),
                                    ]
                                ),
                            ),
                            (
                                "jpcoar:funderName",
                                OrderedDict([("@xml:lang", "ja"), ("#text", "テスト助成機関")]),
                            ),
                            (
                                "jpcoar:awardNumber",
                                OrderedDict(
                                    [
                                        ("@awardURI", "https://test.research.com"),
                                        ("#text", "1111"),
                                        ("@awardNumberType", "JGN"),
                                    ]
                                ),
                            ),
                            (
                                "jpcoar:awardTitle",
                                OrderedDict([("@xml:lang", "ja"), ("#text", "テスト研究")]),
                            ),
                        ]
                    ),
                ),
                (
                    "jpcoar:sourceIdentifier",
                    OrderedDict(
                        [("@identifierType", "PISSN"), ("#text", "test source Identifier")]
                    ),
                ),
                (
                    "jpcoar:sourceTitle",
                    [
                        OrderedDict([("@xml:lang", "ja"), ("#text", "test collectibles")]),
                        OrderedDict([("@xml:lang", "ja"), ("#text", "test title book")]),
                    ],
                ),
                ("jpcoar:volume", ["5", "1"]),
                ("jpcoar:issue", ["2", "2"]),
                ("jpcoar:numPages", ["333", "555"]),
                ("jpcoar:pageStart", ["123", "789"]),
                ("jpcoar:pageEnd", ["456", "234"]),
                ("dcndl:dissertationNumber", "9999"),
                ("dcndl:degreeName", OrderedDict([("@xml:lang", "ja"), ("#text", "テスト学位")])),
                ("dcndl:dateGranted", "2022-10-19"),
                (
                    "jpcoar:degreeGrantor",
                    OrderedDict(
                        [
                            (
                                "jpcoar:nameIdentifier",
                                OrderedDict(
                                    [
                                        ("@nameIdentifierScheme", "kakenhi"),
                                        ("#text", "学位授与機関識別子テスト"),
                                    ]
                                ),
                            ),
                            (
                                "jpcoar:degreeGrantorName",
                                OrderedDict([("@xml:lang", "ja"), ("#text", "学位授与機関")]),
                            ),
                        ]
                    ),
                ),
                (
                    "jpcoar:conference",
                    OrderedDict(
                        [
                            (
                                "jpcoar:conferenceName",
                                OrderedDict([("@xml:lang", "ja"), ("#text", "テスト会議")]),
                            ),
                            ("jpcoar:conferenceSequence", "12345"),
                            (
                                "jpcoar:conferenceSponsor",
                                OrderedDict([("@xml:lang", "ja"), ("#text", "テスト機関")]),
                            ),
                            (
                                "jpcoar:conferenceDate",
                                OrderedDict(
                                    [
                                        ("@endDay", "1"),
                                        ("@endYear", "2005"),
                                        ("@endMonth", "12"),
                                        ("@startDay", "11"),
                                        ("@xml:lang", "ja"),
                                        ("@startYear", "2000"),
                                        ("@startMonth", "4"),
                                        ("#text", "12"),
                                    ]
                                ),
                            ),
                            (
                                "jpcoar:conferenceVenue",
                                OrderedDict([("@xml:lang", "ja"), ("#text", "テスト会場")]),
                            ),
                            ("jpcoar:conferenceCountry", "JPN"),
                        ]
                    ),
                ),
                (
                    "jpcoar:file",
                    [
                        OrderedDict(
                            [
                                (
                                    "jpcoar:URI",
                                    "https://weko3.example.org/record/1/files/test1.txt",
                                ),
                                ("jpcoar:mimeType", "text/plain"),
                                ("jpcoar:extent", "18 B"),
                                (
                                    "datacite:date",
                                    OrderedDict(
                                        [("@dateType", "Accepted"), ("#text", "2022-10-20")]
                                    ),
                                ),
                                ("datacite:version", "1.0"),
                            ]
                        ),
                        OrderedDict(
                            [
                                (
                                    "jpcoar:URI",
                                    "https://weko3.example.org/record/1/files/test2",
                                ),
                                ("jpcoar:mimeType", "application/octet-stream"),
                                ("jpcoar:extent", "18 B"),
                                ("datacite:version", "1.2"),
                            ]
                        ),
                        OrderedDict(
                            [
                                (
                                    "jpcoar:URI",
                                    "https://weko3.example.org/record/1/files/test3.png",
                                ),
                                ("jpcoar:mimeType", "image/png"),
                                ("jpcoar:extent", "18 B"),
                                ("datacite:version", "2.1"),
                            ]
                        ),
                    ],
                ),
                (
                    "jpcoar:publisher",
                    OrderedDict(
                        [
                            (
                                "jpcoar:publisherName",
                                OrderedDict(
                                    [
                                        ("@xml:lang", "ja"),
                                        ("#text", "publisher_name_test"),
                                    ]
                                ),
                            ),
                            (
                                "jpcoar:publisherDescription",
                                OrderedDict(
                                    [
                                        ("@xml:lang", "ja"),
                                        ("#text", "publisher_description_test"),
                                    ]
                                ),
                            ),
                            (
                                "dcndl:location",
                                OrderedDict(
                                    [
                                        ("#text", "location_test"),
                                    ]
                                ),
                            ),
                            (
                                "dcndl:publicationPlace",
                                OrderedDict(
                                    [
                                        ("#text", "publication_place_test"),
                                    ]
                                ),
                            ),
                        ]
                    ),
                ),
                (
                    "dcterms:date",
                    OrderedDict(
                        [
                            ("@xml:lang", "ja"),
                            ("#text", "test full item"),
                        ]
                    )
                ),
                (
                    "dcndl:edition",
                    OrderedDict(
                        [
                            ("@xml:lang", "ja"),
                            ("#text", "edition_test"),
                        ]
                    )
                ),
                (
                    "dcndl:volumeTitle",
                    OrderedDict(
                        [
                            ("@xml:lang", "ja"),
                            ("#text", "volumeTitle_test"),
                        ]
                    )
                ),
                (
                    "dcndl:originalLanguage",
                    OrderedDict(
                        [
                            ("#text", "originalLanguage_test"),
                        ]
                    )
                ),
                (
                    "dcterms:extent",
                    OrderedDict(
                        [
                            ("@xml:lang", "ja"),
                            ("#text", "extent_test"),
                        ]
                    )
                ),
                (
                    "jpcoar:format",
                    OrderedDict(
                        [
                            ("@xml:lang", "ja"),
                            ("#text", "format_test"),
                        ]
                    )
                ),
                (
                    "jpcoar:holdingAgent",
                    OrderedDict(
                        [
                            (
                                "jpcoar:holdingAgentNameIdentifier",
                                OrderedDict(
                                    [
                                        ("@nameIdentifierScheme", "ROR"),
                                        ("@nameIdentifierURI", "nameIdentifierURI_test"),
                                    ]
                                ),
                            ),
                            (
                                "jpcoar:holdingAgentName",
                                OrderedDict(
                                    [
                                        ("@xml:lang", "ja"),
                                        ("#text", "holdingAgentName_test"),
                                    ]
                                ),
                            ),
                        ]
                    ),
                ),
                (
                    "jpcoar:datasetSeries",
                    OrderedDict(
                        [
                            ("@datasetSeriesType", "True"),
                        ]
                    )
                ),
                (
                    "jpcoar:catalog",
                    OrderedDict(
                        [
                            (
                                "jpcoar:contributorName",
                                OrderedDict(
                                    [
                                        ("@xml:lang", "ja"),
                                        ("#text", "contributorName_test"),
                                    ]
                                ),
                            ),
                            (
                                "jpcoar:identifier",
                                OrderedDict(
                                    [
                                        ("@identifierType", "DOI"),
                                    ]
                                ),
                            ),
                            (
                                "dc:title",
                                OrderedDict(
                                    [
                                        ("@xml:lang", "ja"),
                                        ("#text", "title_test")
                                    ]
                                ),
                            ),
                            (
                                "datacite:description",
                                OrderedDict(
                                    [
                                        ("@xml:lang", "ja"),
                                        ("#text", "description_test"),
                                        ("@descriptionType", "Abstract"),
                                    ]
                                ),
                            ),
                            (
                                "jpcoar:subject",
                                OrderedDict(
                                    [
                                        ("@xml:lang", "ja"),
                                        ("#text", "subject_test"),
                                        ("@subjectScheme", "DDC"),
                                        ("@subjectURI", "subjectURI_test"),
                                    ]
                                ),
                            ),
                            (
                                "jpcoar:license",
                                OrderedDict(
                                    [
                                        ("@xml:lang", "ja"),
                                        ("#text", "license_test"),
                                        ("@licenseType", "file"),
                                        ("@rdf:resource", "http://purl.org/coar/access_right/c_14cb"),
                                    ]
                                ),
                            ),
                            (
                                "dc:rights",
                                OrderedDict(
                                    [
                                        ("@xml:lang", "ja"),
                                        ("#text", "rights_test"),
                                        ("@rdf:resource", "http://purl.org/coar/access_right/c_14cb"),
                                    ]
                                ),
                            ),
                            (
                                "dcterms:accessRights",
                                OrderedDict(
                                    [
                                        ("@accessRights", "open access"),
                                        ("@rdf:resource", "http://purl.org/coar/access_right/c_14cb"),
                                    ]
                                ),
                            ),
                            (
                                "jpcoar:file",
                                OrderedDict(
                                    [
                                        (
                                            "jpcoar:URI",
                                            OrderedDict(
                                                [
                                                    ("@objectType", "thumbnail"),
                                                ]
                                            ),
                                        ),
                                    ]
                                ),
                            ),
                        ]
                    ),
                ),
            ]
        )
        result = mapper.map(db_itemtype["item_type_name"].name)

        # assert condition will be updated once update_item_type.py be updated with jpcoar2 properties created
        # right now jpcoar2 items added to harvester.py is being covered by this test case and there are no errors

        assert result

    # .tox/c1/bin/pytest -v --cov=weko_search_ui tests/test_mapper.py::TestJPCOARV2Mapper::test_map_3 -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
    def test_map_3(self,db_itemtype):
        xml_str = '<jpcoar:jpcoar xmlns:datacite="https://schema.datacite.org/meta/kernel-4/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcndl="http://ndl.go.jp/dcndl/terms/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:jpcoar="https://github.com/JPCOAR/schema/blob/master/2.0/" xmlns:oaire="http://namespace.openaire.eu/schema/oaire/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rioxxterms="http://www.rioxx.net/schema/v2.0/rioxxterms/" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="https://github.com/JPCOAR/schema/blob/master/2.0/" xsi:schemaLocation="https://github.com/JPCOAR/schema/blob/master/2.0/jpcoar_scm.xsd"><dc:title xml:lang="en">thesis_test_today</dc:title><jpcoar:creator creatorType="creator_type_test"><jpcoar:creatorName nameType="Personal" xml:lang="en">creator_name_test</jpcoar:creatorName><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="creator_aff_name_identifier_uri_test" nameIdentifierScheme="ROR">creator_aff_name_identifier</jpcoar:nameIdentifier><jpcoar:affiliationName xml:lang="en">creator_aff_name</jpcoar:affiliationName></jpcoar:affiliation></jpcoar:creator><jpcoar:contributor><jpcoar:contributorName nameType="Organizational" xml:lang="ja">contributor_name_test</jpcoar:contributorName><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="contrib_aff_name_id_uri_test" nameIdentifierScheme="GRID">contrib_aff_name_id_test</jpcoar:nameIdentifier><jpcoar:affiliationName xml:lang="en">contrib_aff_name_test</jpcoar:affiliationName></jpcoar:affiliation></jpcoar:contributor><jpcoar:subject xml:lang="en" subjectURI="subject_uri_test" subjectScheme="DDC">subject_test</jpcoar:subject><datacite:date>2023-06-15</datacite:date><dc:type rdf:resource="http://purl.org/coar/resource_type/c_46ec">thesis</dc:type><jpcoar:identifier identifierType="URI">https://localhost/records/26</jpcoar:identifier><jpcoar:relation relationType="inSeries"><jpcoar:relatedIdentifier identifierType="WOS">related_identifier_test</jpcoar:relatedIdentifier><jpcoar:relatedTitle xml:lang="en">related_title_test</jpcoar:relatedTitle></jpcoar:relation><jpcoar:fundingReference><jpcoar:funderIdentifier funderIdentifierType="Crossref Funder" funderIdentifierTypeURI="funder_identifier_type_uri_test">funder_identifier_test</jpcoar:funderIdentifier><jpcoar:awardNumber awardURI="award_number_uri_test" awardNumberType="JGN">award_number_test</jpcoar:awardNumber><jpcoar:fundingStreamIdentifier fundingStreamIdentifierType="Crossref Funder" fundingStreamIdentifierTypeURI="funding_stream_identifier_type_uri_test">funding_stream_identifier_test</jpcoar:fundingStreamIdentifier><jpcoar:fundingStream xml:lang="en">funding_stream_test</jpcoar:fundingStream></jpcoar:fundingReference><jpcoar:publisher><jpcoar:publisherName xml:lang="en">publisher_test</jpcoar:publisherName><jpcoar:publisherDescription xml:lang="ja">description_test</jpcoar:publisherDescription><dcndl:location>location_test</dcndl:location><dcndl:publicationPlace>publication_place_test</dcndl:publicationPlace></jpcoar:publisher><dcterms:date>2016</dcterms:date><dcndl:edition xml:lang="en">edition_test</dcndl:edition><dcndl:volumeTitle xml:lang="ja">volume_title_test</dcndl:volumeTitle><dcndl:originalLanguage>original_language_test</dcndl:originalLanguage><dcterms:extent xml:lang="en">extent_test</dcterms:extent><jpcoar:format xml:lang="en">format_test</jpcoar:format><jpcoar:holdingAgent><jpcoar:holdingAgentNameIdentifier nameIdentifierURI="holding_agent_name_identifier_uri_test" nameIdentifierScheme="ROR">holding_agent_name_identifier_test</jpcoar:holdingAgentNameIdentifier><jpcoar:holdingAgentName xml:lang="en">holding_agent_name_test</jpcoar:holdingAgentName></jpcoar:holdingAgent><jpcoar:datasetSeries>True</jpcoar:datasetSeries><jpcoar:catalog><jpcoar:contributor contributorType="HostingInstitution"><jpcoar:contributorName xml:lang="en">catalog_contributor_test</jpcoar:contributorName></jpcoar:contributor><jpcoar:identifier identifierType="DOI">catalog_identifier_test</jpcoar:identifier><dc:title xml:lang="en">catalog_title_test</dc:title><datacite:description xml:lang="ja" descriptionType="Abstract">catalog_description_test</datacite:description><jpcoar:subject xml:lang="en" subjectURI="catalog_subject_uri_test" subjectScheme="DDC">catalog_subject_test</jpcoar:subject><jpcoar:license xml:lang="en" licenseType="file" rdf:resource="catalog_rdf_license_test">catalog_license_test</jpcoar:license><dc:rights xml:lang="en" rdf:resource="catalog_rdf_rights_test">catalog_rights_test</dc:rights><dcterms:accessRights rdf:resource="catalog_rdf_access_rights_test">metadata only access</dcterms:accessRights><jpcoar:file><jpcoar:URI objectType="open access">catalog_file_test</jpcoar:URI></jpcoar:file></jpcoar:catalog></jpcoar:jpcoar>'
        mapper = JPCOARV2Mapper(xml_str)
        mapper.json["jpcoar:jpcoar"] = OrderedDict(
            [
                (
                    "dcndl:edition",
                    {
                        "@xml:lang": "ja",
                        "#text": "edition_test",
                    }
                ),
            ]
        )
        result = mapper.map(db_itemtype["item_type_name"].name)

        # assert condition will be updated once update_item_type.py be updated with jpcoar2 properties created
        # right now jpcoar2 items added to harvester.py is being covered by this test case and there are no errors

        assert result

    # .tox/c1/bin/pytest -v --cov=weko_search_ui tests/test_mapper.py::TestJPCOARV2Mapper::test_map_4 -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
    def test_map_4(self,db_itemtype_jpcoar):
        xml_str = '<jpcoar:jpcoar xmlns:datacite="https://schema.datacite.org/meta/kernel-4/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcndl="http://ndl.go.jp/dcndl/terms/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:jpcoar="https://github.com/JPCOAR/schema/blob/master/2.0/" xmlns:oaire="http://namespace.openaire.eu/schema/oaire/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rioxxterms="http://www.rioxx.net/schema/v2.0/rioxxterms/" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="https://github.com/JPCOAR/schema/blob/master/2.0/" xsi:schemaLocation="https://github.com/JPCOAR/schema/blob/master/2.0/jpcoar_scm.xsd"><dc:title xml:lang="en">thesis_test_today</dc:title><jpcoar:creator creatorType="creator_type_test"><jpcoar:creatorName nameType="Personal" xml:lang="en">creator_name_test</jpcoar:creatorName><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="creator_aff_name_identifier_uri_test" nameIdentifierScheme="ROR">creator_aff_name_identifier</jpcoar:nameIdentifier><jpcoar:affiliationName xml:lang="en">creator_aff_name</jpcoar:affiliationName></jpcoar:affiliation></jpcoar:creator><jpcoar:contributor><jpcoar:contributorName nameType="Organizational" xml:lang="ja">contributor_name_test</jpcoar:contributorName><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="contrib_aff_name_id_uri_test" nameIdentifierScheme="GRID">contrib_aff_name_id_test</jpcoar:nameIdentifier><jpcoar:affiliationName xml:lang="en">contrib_aff_name_test</jpcoar:affiliationName></jpcoar:affiliation></jpcoar:contributor><jpcoar:subject xml:lang="en" subjectURI="subject_uri_test" subjectScheme="DDC">subject_test</jpcoar:subject><datacite:date>2023-06-15</datacite:date><dc:type rdf:resource="http://purl.org/coar/resource_type/c_46ec">thesis</dc:type><jpcoar:identifier identifierType="URI">https://localhost/records/26</jpcoar:identifier><jpcoar:relation relationType="inSeries"><jpcoar:relatedIdentifier identifierType="WOS">related_identifier_test</jpcoar:relatedIdentifier><jpcoar:relatedTitle xml:lang="en">related_title_test</jpcoar:relatedTitle></jpcoar:relation><jpcoar:fundingReference><jpcoar:funderIdentifier funderIdentifierType="Crossref Funder" funderIdentifierTypeURI="funder_identifier_type_uri_test">funder_identifier_test</jpcoar:funderIdentifier><jpcoar:awardNumber awardURI="award_number_uri_test" awardNumberType="JGN">award_number_test</jpcoar:awardNumber><jpcoar:fundingStreamIdentifier fundingStreamIdentifierType="Crossref Funder" fundingStreamIdentifierTypeURI="funding_stream_identifier_type_uri_test">funding_stream_identifier_test</jpcoar:fundingStreamIdentifier><jpcoar:fundingStream xml:lang="en">funding_stream_test</jpcoar:fundingStream></jpcoar:fundingReference><jpcoar:publisher><jpcoar:publisherName xml:lang="en">publisher_test</jpcoar:publisherName><jpcoar:publisherDescription xml:lang="ja">description_test</jpcoar:publisherDescription><dcndl:location>location_test</dcndl:location><dcndl:publicationPlace>publication_place_test</dcndl:publicationPlace></jpcoar:publisher><dcterms:date>2016</dcterms:date><dcndl:edition xml:lang="en">edition_test</dcndl:edition><dcndl:volumeTitle xml:lang="ja">volume_title_test</dcndl:volumeTitle><dcndl:originalLanguage>original_language_test</dcndl:originalLanguage><dcterms:extent xml:lang="en">extent_test</dcterms:extent><jpcoar:format xml:lang="en">format_test</jpcoar:format><jpcoar:holdingAgent><jpcoar:holdingAgentNameIdentifier nameIdentifierURI="holding_agent_name_identifier_uri_test" nameIdentifierScheme="ROR">holding_agent_name_identifier_test</jpcoar:holdingAgentNameIdentifier><jpcoar:holdingAgentName xml:lang="en">holding_agent_name_test</jpcoar:holdingAgentName></jpcoar:holdingAgent><jpcoar:datasetSeries>True</jpcoar:datasetSeries><jpcoar:catalog><jpcoar:contributor contributorType="HostingInstitution"><jpcoar:contributorName xml:lang="en">catalog_contributor_test</jpcoar:contributorName></jpcoar:contributor><jpcoar:identifier identifierType="DOI">catalog_identifier_test</jpcoar:identifier><dc:title xml:lang="en">catalog_title_test</dc:title><datacite:description xml:lang="ja" descriptionType="Abstract">catalog_description_test</datacite:description><jpcoar:subject xml:lang="en" subjectURI="catalog_subject_uri_test" subjectScheme="DDC">catalog_subject_test</jpcoar:subject><jpcoar:license xml:lang="en" licenseType="file" rdf:resource="catalog_rdf_license_test">catalog_license_test</jpcoar:license><dc:rights xml:lang="en" rdf:resource="catalog_rdf_rights_test">catalog_rights_test</dc:rights><dcterms:accessRights rdf:resource="catalog_rdf_access_rights_test">metadata only access</dcterms:accessRights><jpcoar:file><jpcoar:URI objectType="open access">catalog_file_test</jpcoar:URI></jpcoar:file></jpcoar:catalog></jpcoar:jpcoar>'
        mapper = JPCOARV2Mapper(xml_str)
        mapper.json["jpcoar:jpcoar"] = OrderedDict(
            [
                (
                    "dcndl:edition",
                    {
                        "@xml:lang": "ja",
                        "#text": "edition_test",
                    }
                ),
            ]
        )
        result = mapper.map("")
        assert list(result.keys()) == ["pubdate"]

        # assert condition will be updated once update_item_type.py be updated with jpcoar2 properties created
        # right now jpcoar2 items added to harvester.py is being covered by this test case and there are no errors

        assert result


# def JsonMapper:
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::TestJsonMapper -v -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
class TestJsonMapper:
    # def _create_item_map(self):
    # .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::TestJsonMapper::test_create_item_map -v -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
    def test_create_item_map(self, app, db, item_type2):
        schema = json_data("data/jsonld/item_type_schema.json")
        item_type2.model.schema = schema
        db.session.commit()

        item_map = JsonMapper({}, item_type2.model.id)._create_item_map()

        assert item_map["PubDate"] == "pubdate"
        assert item_map["Title.タイトル"] == "item_30001_title0.subitem_title"
        assert item_map["Title.言語"] == "item_30001_title0.subitem_title_language"
        assert item_map["Resource Type.資源タイプ識別子"] == "item_30001_resource_type11.resourceuri"
        assert item_map["Resource Type.資源タイプ"] == "item_30001_resource_type11.resourcetype"
        assert item_map["Creator.作成者姓名.姓名"] == "item_30001_creator2.creatorNames.creatorName"
        assert item_map["Creator.作成者所属.所属機関名.所属機関名"] == "item_30001_creator2.creatorAffiliations.affiliationNames.affiliationName"
        assert item_map["File.本文URL.ラベル"] == "item_30001_file22.url.label"
        assert item_map["File.ファイル名"] == "item_30001_file22.filename"

        item_map = JsonMapper({}, item_type2.model.id)._create_item_map(detail=True)

        assert item_map["Title"] == "item_30001_title0"
        assert item_map["Resource Type"] == "item_30001_resource_type11"
        assert item_map["Creator"] == "item_30001_creator2"
        assert item_map["Creator.作成者姓名"] == "item_30001_creator2.creatorNames"
        assert item_map["Creator.作成者所属"] == "item_30001_creator2.creatorAffiliations"
        assert item_map["Creator.作成者所属.所属機関名"] == "item_30001_creator2.creatorAffiliations.affiliationNames"
        assert item_map["File"] == "item_30001_file22"
        assert item_map["File.本文URL"] == "item_30001_file22.url"

    # def _get_property_type(self, path):
    # .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::TestJsonMapper::test_get_property_type -v -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
    def test_get_property_type(self, app, db, item_type2):
        schema = json_data("data/jsonld/item_type_schema.json")
        item_type2.model.schema = schema
        db.session.commit()

        mapper = JsonMapper({}, item_type2.model.id)

        assert "string" in mapper._get_property_type("pubdate")
        assert "array" in mapper._get_property_type("item_30001_title0")
        assert "string" in mapper._get_property_type("item_30001_title0.subitem_title")
        assert "string" in mapper._get_property_type("item_30001_title0.subitem_title_language")
        assert "object" in mapper._get_property_type("item_30001_resource_type11")
        assert "string" in mapper._get_property_type("item_30001_resource_type11.resourceuri")
        assert "string" in mapper._get_property_type("item_30001_resource_type11.resourcetype")
        assert "array" in mapper._get_property_type("item_30001_creator2")
        assert "array" in mapper._get_property_type("item_30001_creator2.creatorNames")
        assert "string" in mapper._get_property_type("item_30001_creator2.creatorNames.creatorName")
        assert "array" in mapper._get_property_type("item_30001_creator2.creatorAffiliations")
        assert "array" in mapper._get_property_type("item_30001_creator2.creatorAffiliations.affiliationNames")
        assert "string" in mapper._get_property_type("item_30001_creator2.creatorAffiliations.affiliationNames.affiliationName")
        assert "array" in mapper._get_property_type("item_30001_file22")
        assert "object" in mapper._get_property_type("item_30001_file22.url")
        assert "string" in mapper._get_property_type("item_30001_file22.url.label")
        assert "string" in mapper._get_property_type("item_30001_file22.filename")

    # def required_properties(self):
    # .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::TestJsonMapper::test_required_properties -v -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
    def test_required_properties(self, app, db, item_type2):
        schema = json_data("data/jsonld/item_type_schema.json")
        item_type2.model.schema = schema
        db.session.commit()

        json_mapping = json_data("data/jsonld/ro-crate_mapping.json")

        required = JsonLdMapper(item_type2.model.id, json_mapping).required_properties()
        assert required["PubDate"] == "pubdate"
        assert required["Title"] == "item_30001_title0"
        assert required["Title.タイトル"] == "item_30001_title0.subitem_title"
        assert required["Title.言語"] == "item_30001_title0.subitem_title_language"
        assert required["Resource Type"] == "item_30001_resource_type11"
        assert required["Resource Type.資源タイプ識別子"] == "item_30001_resource_type11.resourceuri"
        assert required["Resource Type.資源タイプ"] == "item_30001_resource_type11.resourcetype"


# def JsonLdMapper:
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::TestJsonLdMapper -v -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
class TestJsonLdMapper:
    def test_is_valid(self, app, db, item_type2):
        schema = json_data("data/jsonld/item_type_schema.json")
        item_type2.model.schema = schema
        db.session.commit()

        json_mapping = json_data("data/jsonld/ro-crate_mapping.json")

        assert JsonLdMapper(item_type2.model.id, json_mapping).is_valid

    # def validate(self):
    # .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::TestJsonLdMapper::test_validate -v -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
    def test_validate(self, app, db, item_type2):
        schema = json_data("data/jsonld/item_type_schema.json")
        item_type2.model.schema = schema
        db.session.commit()

        json_mapping = json_data("data/jsonld/ro-crate_mapping.json")

        assert JsonLdMapper(item_type2.model.id, json_mapping).validate() is None

    # def to_item_metadata(self, json_ld):
    # .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::TestJsonLdMapper::test_to_item_metadata -v -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
    def test_to_item_metadata(self, app, db, item_type2, item_type_mapping2):
        app.config.update({"WEKO_SWORDSERVER_METADATA_FILE_ROCRATE": "ro-crate-metadata.json"})
        schema = json_data("data/jsonld/item_type_schema.json")
        item_type2.model.schema = schema
        mapping = json_data("data/jsonld/item_type_mapping.json")
        item_type_mapping2.model.mapping = mapping
        db.session.commit()
        json_mapping = json_data("data/jsonld/ro-crate_mapping.json")
        json_ld = json_data("data/jsonld/ro-crate-metadata.json")

        with app.test_request_context():
            mapper = JsonLdMapper(item_type2.model.id, json_mapping)
            item_metadatas, format = mapper.to_item_metadata(json_ld)

            item_metadata, system_info = item_metadatas[0]
            assert format == "ro-crate"
            assert system_info["cnri"] == "1234/5678"
            assert system_info["doi_ra"] == "DataCite"
            assert system_info["doi"] == "10.1234/5678"
            assert system_info["non_extract"] == ["data.csv"]
            assert system_info["save_as_is"] == False
            assert item_metadata["pubdate"] == "2021-10-15"
            assert item_metadata["path"] == [1623632832836]
            assert item_metadata["publish_status"] == "public"
            assert item_metadata["edit_mode"] == "Keep"
            assert item_metadata["item_30001_title0"][0]["subitem_title"] == "The Sample Dataset for WEKO"
            assert item_metadata["item_30001_title0"][0]["subitem_title_language"] == "en"
            assert item_metadata["item_30001_title0"][1]["subitem_title"] == "WEKO用サンプルデータセット"
            assert item_metadata["item_30001_title0"][1]["subitem_title_language"] == "ja"
            assert item_metadata["item_30001_resource_type11"]["resourceuri"] == "http://purl.org/coar/resource_type/c_6501"
            assert item_metadata["item_30001_resource_type11"]["resourcetype"] == "journal article"
            assert item_metadata["item_30001_file22"][0]["filename"] == "sample.rst"
            assert item_metadata["item_30001_file22"][0]["url"]["label"] == "sample.rst"
            assert item_metadata["item_30001_file22"][0]["url"]["url"] == "https://example.repo.nii.ac.jp/records/123456789/files/sample.rst"
            assert item_metadata["item_30001_file22"][0]["filesize"][0]["value"] == "333 B"
            assert item_metadata["item_30001_file22"][1]["filename"] == "data.csv"
            assert item_metadata["item_30001_file22"][1]["url"]["label"] == "data.csv"
            assert item_metadata["item_30001_file22"][1]["url"]["url"] == "https://example.repo.nii.ac.jp/records/123456789/files/data.csv"
            assert item_metadata["item_30001_file22"][1]["filesize"][0]["value"] == "1234 B"
            assert item_metadata["item_30001_creator2"][0]["creatorNames"][0]["creatorName"] == "John Doe"
            assert item_metadata["item_30001_creator2"][0]["creatorAffiliations"][0]["affiliationNames"][0]["affiliationName"] == "University of Manchester"
            assert item_metadata["feedback_mail_list"] == [{"email": "wekosoftware@nii.ac.jp", "author_id": ""}]
            assert item_metadata["files_info"][0]["key"] == "item_30001_file22"
            assert item_metadata["item_30001_relation14"][0]["subitem_relation_type_id"]["subitem_relation_type_select"] == "DOI"

            list_record = []
            list_record.append({
                "$schema": f"/items/jsonschema/{item_type2.model.id}",
                "metadata": item_metadata,
                "item_type_name": item_type2.model.item_type_name.name,
                "item_type_id": item_type2.model.id,
                "publish_status": item_metadata.get("publish_status"),
            })
            from weko_search_ui.utils import handle_validate_item_import
            list_record = handle_validate_item_import(list_record, schema)

            assert list_record[0].get("errors") is None

        json_ld = json_data("data/jsonld/ro-crate-metadata2.json")

        with app.test_request_context():
            mapper = JsonLdMapper(item_type2.model.id, json_mapping)
            item_metadatas, format = mapper.to_item_metadata(json_ld)

            assert format == "ro-crate"
            assert len(item_metadatas) == 2
            thesis, system_info = item_metadatas[0]

            assert system_info["_id"] == "_:JournalPaper1"
            assert system_info["link_data"][0]["item_id"] == "_:EvidenceData1"
            assert system_info["link_data"][0]["sele_id"] == "isSupplementedBy"
            assert thesis["pubdate"] == "2021-10-15"
            assert thesis["path"] == [1623632832836]
            assert thesis["item_30001_title0"][0]["subitem_title"] == "The Sample Dataset for WEKO"
            assert thesis["item_30001_title0"][1]["subitem_title"] == "WEKO用サンプルデータセット"
            assert thesis["files_info"][0]["key"] == "item_30001_file22"

            evidence, system_info = item_metadatas[1]
            assert system_info["_id"] == "_:EvidenceData1"
            assert system_info["link_data"][0]["item_id"] == "_:JournalPaper1"
            assert system_info["link_data"][0]["sele_id"] == "isSupplementTo"
            assert system_info["non_extract"] == ["data.csv"]
            assert evidence["pubdate"] == "2021-10-15"
            assert evidence["path"] == [1623632832836]
            assert evidence["item_30001_title0"][0]["subitem_title"] == "The Sample Dataset for WEKO, evidence part"
            assert evidence["item_30001_title0"][1]["subitem_title"] == "WEKO用サンプルデータセットのエビデンス部分"

            list_record = [
                {
                    "$schema": f"/items/jsonschema/{item_type2.model.id}",
                    "metadata": item_metadata,
                    "item_type_name": item_type2.model.item_type_name.name,
                    "item_type_id": item_type2.model.id,
                    "publish_status": item_metadata.get("publish_status"),
                } for item_metadata, system_info in item_metadatas
            ]
            list_record = handle_validate_item_import(list_record, schema)

            assert list_record[0].get("errors") is None
            assert list_record[1].get("errors") is None

    # def deconstruct_json_ld(json_ld):
    # .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::TestJsonLdMapper::test__deconstruct_json_ld -v -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
    def test__deconstruct_json_ld(self, app):
        app.config.update({"WEKO_SWORDSERVER_METADATA_FILE_ROCRATE": "ro-crate-metadata.json"})

        json_ld = json_data("data/jsonld/ro-crate-metadata.json")
        deconstructed_metadata, format = JsonLdMapper._deconstruct_json_ld(json_ld)
        metadata, system_info =  deconstructed_metadata[0]

        assert format == "ro-crate"
        assert system_info["cnri"] == "1234/5678"
        assert system_info["doi_ra"] == "DataCite"
        assert system_info["doi"] == "10.1234/5678"
        assert system_info["non_extract"] == ["data/data.csv"]
        assert system_info["save_as_is"] == False
        assert metadata["@id"] == "./"
        assert metadata["name"] == "The Sample Dataset for WEKO"
        assert metadata["description"] == "This is a sample dataset for WEKO in order to demonstrate the RO-Crate metadata."
        assert metadata["datePublished"] == "2021-10-15"
        assert metadata["dc:title[0].value"] == "The Sample Dataset for WEKO"
        assert metadata["dc:title[0].language"] == "en"
        assert metadata["dc:title[1].value"] == "WEKO用サンプルデータセット"
        assert metadata["dc:title[1].language"] == "ja"
        assert metadata["dc:type.@id"] == "http://purl.org/coar/resource_type/c_6501"
        assert metadata["dc:type.name"] == "journal article"
        assert metadata["creator[0].affiliation.name"] == "University of Manchester"
        assert metadata["hasPart[0].@id"] == "data/sample.rst"
        assert metadata["hasPart[0].name"] == "sample.rst"
        assert metadata["hasPolicy[0].permission[0].duty[0].assignee"] == "http://example.org/rightsholder"
        assert not any("@type" in key for key in metadata.keys())

        json_ld = json_data("data/jsonld/ro-crate-metadata2.json")
        deconstructed_metadata, format = JsonLdMapper._deconstruct_json_ld(json_ld)
        thesis, system_info =  deconstructed_metadata[0]

        assert format == "ro-crate"
        assert system_info["_id"] == "_:JournalPaper1"
        assert system_info["link_data"][0]["item_id"] == "_:EvidenceData1"
        assert system_info["link_data"][0]["sele_id"] == "isSupplementedBy"
        assert system_info["link_data"][1]["item_id"] == "https://example.repo.nii.ac.jp/records/123456789"
        assert system_info["link_data"][1]["sele_id"] == "isSupplementedBy"
        assert thesis["@id"] == "_:JournalPaper1"
        assert thesis["dc:title[0].value"] == "The Sample Dataset for WEKO"
        assert thesis["dc:title[1].value"] == "WEKO用サンプルデータセット"
        assert thesis["hasPart[0].wk:textExtraction"] == True
        assert thesis["dc:type.@id"] == "http://purl.org/coar/resource_type/c_6501"

        evidence, system_info = deconstructed_metadata[1]

        assert system_info["_id"] == "_:EvidenceData1"
        assert system_info["link_data"][0]["item_id"] == "_:JournalPaper1"
        assert system_info["link_data"][0]["sele_id"] == "isSupplementTo"
        assert system_info["non_extract"] == ["data/data.csv"]
        assert evidence["@id"] == "_:EvidenceData1"
        assert evidence["dc:title[0].value"] == "The Sample Dataset for WEKO, evidence part"
        assert evidence["dc:title[1].value"] == "WEKO用サンプルデータセットのエビデンス部分"
        assert evidence["hasPart[0].wk:textExtraction"] == False
        assert evidence["dc:type.@id"] == "http://purl.org/coar/resource_type/c_1843"

        with pytest.raises(ValueError) as ex:
            deconstructed_metadata, format = JsonLdMapper._deconstruct_json_ld({})
        ex.match('Invalid json-ld format: "@context" is invalid.')

    # def to_rocrate_metadata(self, metadata):
    # .tox/c1/bin/pytest --cov=weko_search_ui tests/test_mapper.py::TestJsonLdMapper::test_to_rocrate_metadata -v -vv -s --cov-branch --cov-report=xml --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
    def test_to_rocrate_metadata(self, app, db, item_type2, item_type_mapping2, mocker):
        metadata = {
            "_oai": {
                "id": "oai:weko3.example.org:02000007",
                "sets": [
                "1623632832836"
                ]
            },
            "path": [
                "1623632832836"
            ],
            "owner": "1",
            "recid": "2000007",
            "title": [
                "The Sample Dataset for WEKO"
            ],
            "pubdate": {
                "attribute_name": "PubDate",
                "attribute_value": "2025-03-06"
            },
            "_buckets": {
                "deposit": "0fd192c1-8de8-46c2-b73c-66495e40b62d"
            },
            "_deposit": {
                "id": "2000007",
                "pid": {
                "type": "depid",
                "value": "2000007",
                "revision_id": 0
                },
                "owner": "1",
                "owners": [
                1
                ],
                "status": "published",
                "created_by": 1,
                "owners_ext": {
                "email": "wekosoftware@nii.ac.jp",
                "username": None,
                "displayname": "ADMIN"
                }
            },
            "item_title": "The Sample Dataset for WEKO",
            "author_link": [
                "1",
                "2"
            ],
            "item_type_id": "30001",
            "publish_date": "2025-03-06",
            "control_number": "2000007",
            "publish_status": "0",
            "weko_shared_id": -1,
            "item_30001_file22": {
                "attribute_name": "File",
                "attribute_type": "file",
                "attribute_value_mlt": [
                {
                    "url": {
                        "url": "https://weko3.example.org/record/2000007/files/sample.rst",
                        "objectType": "abstract",
                        "label": "sample.rst"
                    },
                    "date": [
                    {
                        "dateType": "Available",
                        "dateValue": "2025-03-06"
                    }
                    ],
                    "format": "application/octet-stream",
                    "version": "1",
                    "filename": "sample.rst",
                    "filesize": [
                    {
                        "value": "333 B"
                    }
                    ],
                    "mimetype": "application/octet-stream",
                    "accessrole": "open_access",
                    "version_id": "272c4651-711e-427d-8096-b1b20e27820e"
                },
                {
                    "url": {
                        "url": "https://weko3.example.org/record/2000007/files/data.csv",
                        "objectType": "dataset",
                        "label": "data.csv"
                    },
                    "date": [
                    {
                        "dateType": "Available",
                        "dateValue": "2025-03-10"
                    }
                    ],
                    "format": "text/csv",
                    "version": "1",
                    "fileDate": [
                    {
                        "fileDateType": "Created",
                        "fileDateValue": "2025-01-27"
                    }
                    ],
                    "filename": "data.csv",
                    "filesize": [
                    {
                        "value": "475 B"
                    }
                    ],
                    "mimetype": "text/csv",
                    "accessrole": "open_date",
                    "version_id": "ac7990f5-a6de-4b61-b34d-34bd0d0240ee"
                }
                ]
            },
            "item_30001_title0": {
                "attribute_name": "Title",
                "attribute_value_mlt": [
                {
                    "subitem_title": "The Sample Dataset for WEKO",
                    "subitem_title_language": "en"
                },
                {
                    "subitem_title": "WEKO用サンプルデータセット",
                    "subitem_title_language": "ja"
                }
                ]
            },
            "item_30001_creator2": {
                "attribute_name": "Creator",
                "attribute_type": "creator",
                "attribute_value_mlt": [
                {
                    "givenNames": [
                    {
                        "givenName": "John",
                        "givenNameLang": "en"
                    }
                    ],
                    "familyNames": [
                    {
                        "familyName": "Doe",
                        "familyNameLang": "en"
                    }
                    ],
                    "creatorMails": [
                    {
                        "creatorMail": "john.doe@example.org"
                    }
                    ],
                    "creatorNames": [
                    {
                        "creatorName": "Doe, John",
                        "creatorNameLang": "en",
                        "creatorNameType": "Personal"
                    }
                    ],
                    "nameIdentifiers": [
                    {
                        "nameIdentifier": "1",
                        "nameIdentifierScheme": "WEKO"
                    }
                    ],
                    "creatorAffiliations": [
                    {
                        "affiliationNames": [
                        {
                            "affiliationName": "University of Manchester",
                            "affiliationNameLang": "en"
                        }
                        ]
                    }
                    ]
                }
                ]
            },
            "item_30001_contributor3": {
                "attribute_name": "Contributor",
                "attribute_value_mlt": [
                {
                    "givenNames": [
                    {
                        "givenName": "Kenji",
                        "givenNameLang": "en"
                    },
                    {
                        "givenName": "健司",
                        "givenNameLang": "ja"
                    }
                    ],
                    "familyNames": [
                    {
                        "familyName": "Ichikawa",
                        "familyNameLang": "en"
                    },
                    {
                        "familyName": "市川",
                        "familyNameLang": "ja"
                    }
                    ],
                    "nameIdentifiers": [
                    {
                        "nameIdentifier": "2",
                        "nameIdentifierScheme": "WEKO"
                    }
                    ],
                    "contributorMails": [
                    {
                        "contributorMail": "kenji.ichikawa@example.org"
                    }
                    ],
                    "contributorNames": [
                    {
                        "lang": "en",
                        "nameType": "Personal",
                        "contributorName": "Ichikawa, Kenji"
                    },
                    {
                        "lang": "ja",
                        "nameType": "Personal",
                        "contributorName": "市川, 健司"
                    }
                    ]
                }
                ]
            },
            "relation_version_is_last": True,
            "item_30001_resource_type11": {
                "attribute_name": "Resource Type",
                "attribute_value_mlt": [
                {
                    "resourceuri": "http://purl.org/coar/resource_type/c_6501",
                    "resourcetype": "journal article"
                }
                ]
            },
            "item_30001_identifier_registration13": {
                "attribute_name": "Identifier Registration",
                "attribute_value_mlt": [
                {
                    "subitem_identifier_reg_text": "<Empty>/0002000007",
                    "subitem_identifier_reg_type": "JaLC"
                }
                ]
            },
            "item_30001_bibliographic_information17": {
                "attribute_name": "Bibliographic Information",
                "attribute_value_mlt": [
                {
                    "bibliographicPageStart": "32"
                }
                ]
            }
        }

        mock_pid = MagicMock()
        item_uuid = uuid.uuid4()
        mock_pid.object_uuid = item_uuid
        mock_pid_model = mocker.patch("weko_search_ui.mapper.PersistentIdentifier.get")
        mock_pid_model.return_value = mock_pid

        # case without Extra
        schema = json_data("data/jsonld/item_type_schema.json")
        item_type2.model.schema = schema
        mapping = json_data("data/jsonld/item_type_mapping.json")
        item_type_mapping2.model.mapping = mapping
        db.session.commit()
        json_mapping = json_data("data/jsonld/ro-crate_mapping.json")

        mock_mail_list = mocker.patch(
            "weko_search_ui.mapper.FeedbackMailList.get_mail_list_by_item_id",
            return_value=[{"email": "wekosoftware@nii.ac.jp"}]
        )
        mock_itemlink = mocker.patch(
            "weko_search_ui.mapper.ItemLink.get_item_link_info",
            return_value=[{"item_links": "2000011", "value": "isSupplementedBy"}]
        )

        rocrate = JsonLdMapper(
            item_type2.model.id, json_mapping).to_rocrate_metadata(metadata)
        ro_crate_metadata = rocrate.metadata.generate()

        # mapped metadata
        graph = ro_crate_metadata["@graph"][0]
        assert graph["datePublished"] == metadata["pubdate"]["attribute_value"]
        assert graph["name"] == metadata["item_title"]
        assert graph["identifier"] == metadata["recid"]

        # wk-context
        assert graph["wk:index"] == metadata["path"]
        assert graph["wk:editMode"] == "Keep"
        assert graph["wk:feedbackMail"] == ["wekosoftware@nii.ac.jp"]
        assert graph["wk:metadataAutoFill"] == False
        if metadata.get("publish_status") == "0":
            assert graph["wk:publishStatus"] == "public"
        elif metadata.get("publish_status") == "1":
            assert graph["wk:publishStatus"] == "private"
        assert "wk:itemLinks" in graph
        link = None
        for item in ro_crate_metadata["@graph"]:
            if item.get("@id") == graph.get("wk:itemLinks")[0]["@id"]:
                link = item
        assert link["identifier"] == "http://test_server/records/2000011"
        assert link["value"] == "isSupplementedBy"

        # files
        haspart_0 = graph["hasPart"][0]["@id"]
        file_0 = None
        haspart_1 = graph["hasPart"][1]["@id"]
        file_1 = None
        for item in ro_crate_metadata["@graph"]:
            if item.get("@id") == haspart_0:
                file_0 = item
            elif item.get("@id") == haspart_1:
                file_1 = item
        assert haspart_0 == "data/sample.rst"
        assert file_0["name"] == "sample.rst"
        assert haspart_1 == "data/data.csv"
        assert file_1["name"] == "data.csv"

        # case no filename mapping
        json_mapping_no_filename = json_data(
            "data/jsonld/ro-crate_mapping_no_filename.json")

        rocrate = JsonLdMapper(
            item_type2.model.id, json_mapping_no_filename
        ).to_rocrate_metadata(metadata)
        ro_crate_metadata = rocrate.metadata.generate()

        # mapped metadata
        graph = ro_crate_metadata["@graph"][0]
        assert graph["datePublished"] == metadata["pubdate"]["attribute_value"]
        assert graph["name"] == metadata["item_title"]
        assert graph["identifier"] == metadata["recid"]

        # wk-context
        assert "wk:publishStatus" in graph
        assert "wk:index" in graph
        assert "wk:editMode" in graph
        assert "wk:feedbackMail" in graph
        assert "wk:itemLinks" in graph
        assert "wk:metadataAutoFill" in graph
        assert graph["wk:index"] == metadata["path"]
        if metadata.get("publish_status") == "0":
            assert graph["wk:publishStatus"] == "public"
        elif metadata.get("publish_status") == "1":
            assert graph["wk:publishStatus"] == "private"

        # files
        haspart_0 = graph["hasPart"][0]["@id"]
        file_0 = None
        haspart_1 = graph["hasPart"][1]["@id"]
        file_1 = None
        for item in ro_crate_metadata["@graph"]:
            if item.get("@id") == haspart_0:
                file_0 = item
            elif item.get("@id") == haspart_1:
                file_1 = item
        assert "name" not in file_0
        assert "name" not in file_1

        # case item_link
        mock_item_link_info = [
            dict(item_links="link_1", value="value_1"),
            dict(item_links="link_2", value="value_2")
        ]
        with patch(
            "weko_search_ui.mapper.ItemLink.get_item_link_info",
            return_value=mock_item_link_info):

            rocrate = JsonLdMapper(
                item_type2.model.id, json_mapping).to_rocrate_metadata(metadata)
            ro_crate_metadata = rocrate.metadata.generate()

            # mapped metadata
            graph = ro_crate_metadata["@graph"][0]
            assert graph["datePublished"] == metadata["pubdate"]["attribute_value"]
            assert graph["name"] == metadata["item_title"]
            assert graph["identifier"] == metadata["recid"]

            # wk-context
            assert "wk:publishStatus" in graph
            assert "wk:index" in graph
            assert "wk:editMode" in graph
            assert "wk:feedbackMail" in graph
            assert "wk:itemLinks" in graph
            assert "wk:metadataAutoFill" in graph
            assert graph["wk:index"] == metadata["path"]
            if metadata.get("publish_status") == "0":
                assert graph["wk:publishStatus"] == "public"
            elif metadata.get("publish_status") == "1":
                assert graph["wk:publishStatus"] == "private"
            assert len(graph["wk:itemLinks"]) == 2

            # files
            haspart_0 = graph["hasPart"][0]["@id"]
            file_0 = None
            haspart_1 = graph["hasPart"][1]["@id"]
            file_1 = None
            for item in ro_crate_metadata["@graph"]:
                if item.get("@id") == haspart_0:
                    file_0 = item
                elif item.get("@id") == haspart_1:
                    file_1 = item
            assert file_0["name"] == "sample.rst"
            assert file_1["name"] == "data.csv"

        # case Extra(attribute_value_mlt)
        key = "item_1744171568909"
        multi_metadata = {
            "attribute_name": "Extra",
            "attribute_value_mlt": [
                {
                    "interim": "エクストラ_multi"
                }
            ]
        }
        schema = json_data("data/jsonld/item_type_schema_multi.json")
        item_type2.model.schema = schema
        db.session.commit()
        metadata.update(**{key:multi_metadata})

        rocrate = JsonLdMapper(
            item_type2.model.id, json_mapping).to_rocrate_metadata(metadata)
        ro_crate_metadata = rocrate.metadata.generate()

        # mapped metadata
        graph = ro_crate_metadata["@graph"][0]
        assert graph["datePublished"] == metadata["pubdate"]["attribute_value"]
        assert graph["name"] == metadata["item_title"]
        assert graph["identifier"] == metadata["recid"]

        # wk-context
        assert "wk:publishStatus" in graph
        assert "wk:index" in graph
        assert "wk:editMode" in graph
        assert "wk:feedbackMail" in graph
        assert "wk:itemLinks" in graph
        assert "wk:metadataAutoFill" in graph
        assert graph["wk:index"] == metadata["path"]
        if metadata.get("publish_status") == "0":
            assert graph["wk:publishStatus"] == "public"
        elif metadata.get("publish_status") == "1":
            assert graph["wk:publishStatus"] == "private"

        # files, extra
        haspart_0 = graph["hasPart"][0]["@id"]
        file_0 = None
        haspart_1 = graph["hasPart"][1]["@id"]
        file_1 = None
        extra_key = graph["additionalProperty"]["@id"]
        extra = None
        for item in ro_crate_metadata["@graph"]:
            if item.get("@id") == haspart_0:
                file_0 = item
            elif item.get("@id") == haspart_1:
                file_1 = item
            elif item.get("@id") == extra_key:
                extra = item

        assert file_0["name"] == "sample.rst"
        assert file_1["name"] == "data.csv"
        # Extra
        assert extra["value"] == multi_metadata["attribute_value_mlt"][0]['interim']

        # case Extra(attribute_value)
        single_metadata = {
            "attribute_name": "extra_field",
            "attribute_value": "エクストラ_single"
        }
        metadata.update(**{key:single_metadata})
        schema = json_data("data/jsonld/item_type_schema_multi.json")
        item_type2.model.schema = schema
        db.session.commit()

        rocrate = JsonLdMapper(
            item_type2.model.id, json_mapping).to_rocrate_metadata(metadata)
        ro_crate_metadata = rocrate.metadata.generate()

        # mapped metadata
        graph = ro_crate_metadata["@graph"][0]
        assert graph["datePublished"] == metadata["pubdate"]["attribute_value"]
        assert graph["name"] == metadata["item_title"]
        assert graph["identifier"] == metadata["recid"]

        # wk-context
        assert "wk:publishStatus" in graph
        assert "wk:index" in graph
        assert "wk:editMode" in graph
        assert "wk:feedbackMail" in graph
        assert "wk:itemLinks" in graph
        assert "wk:metadataAutoFill" in graph
        assert graph["wk:index"] == metadata["path"]
        if metadata.get("publish_status") == "0":
            assert graph["wk:publishStatus"] == "public"
        elif metadata.get("publish_status") == "1":
            assert graph["wk:publishStatus"] == "private"

        # files, extra
        haspart_0 = graph["hasPart"][0]["@id"]
        file_0 = None
        haspart_1 = graph["hasPart"][1]["@id"]
        file_1 = None
        extra_key = graph["additionalProperty"]["@id"]
        extra = None
        for item in ro_crate_metadata["@graph"]:
            if item.get("@id") == haspart_0:
                file_0 = item
            elif item.get("@id") == haspart_1:
                file_1 = item
            elif item.get("@id") == extra_key:
                extra = item

        assert file_0["name"] == "sample.rst"
        assert file_1["name"] == "data.csv"
        # Extra(attribute_value)
        assert extra["value"] == single_metadata["attribute_value"]
