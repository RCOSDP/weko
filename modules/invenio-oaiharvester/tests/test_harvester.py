
import pytest
import responses
import json
import pytz
from datetime import datetime
from lxml import etree
from mock import patch
import copy
import xmltodict
import dateutil
from collections import OrderedDict
from weko_records.api import Mapping
from weko_records.models import ItemType,ItemTypeName
from weko_records.serializers.utils import get_full_mapping
from invenio_oaiharvester.harvester import (
    list_sets,
    list_records,
    map_field,
    subitem_recs,
    parsing_metadata,
    add_title,
    add_alternative,
    add_creator_jpcoar,
    add_contributor_jpcoar,
    add_access_right,
    add_apc,
    add_right,
    add_rights_holder,
    add_subject,
    add_description,
    add_publisher,
    add_publisher_jpcoar,
    add_date,
    add_date_dcterms,
    add_language,
    add_resource_type,
    add_version,
    add_version_type,
    add_identifier,
    add_identifier_registration,
    add_relation,
    add_temporal,
    add_geo_location,
    add_funding_reference,
    add_source_identifier,
    add_source_title,
    add_volume,
    add_issue,
    add_num_page,
    add_page_start,
    add_page_end,
    add_dissertation_number,
    add_degree_name,
    add_date_granted,
    add_degree_grantor,
    add_conference,
    add_edition,
    add_volumeTitle,
    add_originalLanguage,
    add_extent,
    add_format,
    add_holdingAgent,
    add_datasetSeries,
    add_file,
    add_catalog,
    add_creator_dc,
    add_contributor_dc,
    add_title_dc,
    add_subject_dc,
    add_description_dc,
    add_publisher_dc,
    add_resource_type_dc,
    add_date_dc,
    add_identifier_dc,
    add_language_dc,
    add_relation_dc,
    add_rights_dc,
    add_coverage_dc,
    add_source_dc,
    add_format_dc,
    to_dict,
    map_sets,
    add_data_by_key,
    BaseMapper,
    DCMapper,
    JPCOARMapper,
    DDIMapper,
    JsonMapper,
    BIOSAMPLEMapper,
    BIOPROJECTMapper
)
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp

# def list_sets(url, encoding='utf-8'):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_list_sets -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
@responses.activate
def test_list_sets():
    namespaces = {"x": 'http://www.openarchives.org/OAI/2.0/', 'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
    # first request
    body1 = \
        '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">'\
            '<request verb="ListSets">https://192.168.56.103/oai</request>'\
            '<ListSets>'\
                '<set>'\
                    '<setSpec>test_repo1</setSpec>'\
                '</set>'\
                '<set>'\
                    '<setSpec>test_repo2</setSpec>'\
                '</set>'\
            '<resumptionToken>test_token</resumptionToken>'\
            '</ListSets>'\
        '</OAI-PMH>'
    # second request
    body2 = \
        '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">'\
            '<request verb="ListSets">https://192.168.56.103/oai</request>'\
            '<ListSets>'\
                '<set>'\
                    '<setSpec>test_repo3</setSpec>'\
                '</set>'\
                '<set>'\
                    '<setSpec>test_repo4</setSpec>'\
                '</set>'\
            '</ListSets>'\
        '</OAI-PMH>'
    responses.add(
        responses.GET,
        "https://test.org/?verb=ListSets",
        body=body1,
        content_type='text/xml'
    )
    responses.add(
        responses.GET,
        "https://test.org/?verb=ListSets&resumptionToken=test_token",
        body=body2,
        content_type='text/xml'
    )
    url = "https://test.org/"
    sets = list_sets(url)
    specs = [s.xpath("./x:setSpec[1]",namespaces=namespaces)[0].text for s in sets]
    assert specs == ["test_repo1","test_repo2","test_repo3","test_repo4"]
    
# def list_records(
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_list_records -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
@responses.activate
def test_list_records():
    # result with resumptiontoken
    body1 = \
        '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">'\
        '<responseDate>2023-03-01T10:54:40Z</responseDate>'\
        '<request verb="ListRecords" metadataPrefix="jpcoar_1.0">https://192.168.56.103/oai</request>'\
        '<ListRecords>'\
        '<resumptionToken>test_token</resumptionToken>'\
        '<record>test_record1</record>'\
        '<record>test_record2</record>'\
        '</ListRecords>'\
        '</OAI-PMH>'
    # result without resummptiontoken
    body2 = \
        '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">'\
        '<responseDate>2023-03-01T10:54:40Z</responseDate>'\
        '<request verb="ListRecords" metadataPrefix="jpcoar_1.0">https://192.168.56.103/oai</request>'\
        '<ListRecords>'\
        '<record>test_record3</record>'\
        '<record>test_record4</record>'\
        '</ListRecords>'\
        '</OAI-PMH>'
    responses.add(
        responses.GET,
        "https://test.org/?verb=ListRecords&from=2023-01-10&until=2023-10-01&metadataPrefix=jpcoar_1.0&set=*",
        body=body1,
        content_type='text/xml'
    )
    responses.add(
        responses.GET,
        "https://test.org/?verb=ListRecords&metadataPrefix=jpcoar_1.0&set=*&resumptionToken=test_token",
        body=body2,
        content_type='text/xml'
    )
    # resumptiontoken is none
    records, rtoken = list_records("https://test.org/","2023-01-10","2023-10-01","jpcoar_1.0","*",resumption_token=None)
    result = [str(etree.tostring(record),"utf-8") for record in records]
    assert result == ['<record xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">test_record1</record>', '<record xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">test_record2</record>']
    assert rtoken == "test_token"
    
    # resumptiontoken is not none
    records, rtoken = list_records("https://test.org/","2023-01-10","2023-10-01","jpcoar_1.0","*",resumption_token="test_token")
    result = [str(etree.tostring(record),"utf-8") for record in records]
    assert result == ['<record xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">test_record3</record>', '<record xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">test_record4</record>']
    assert rtoken == None


# def map_field(schema):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_map_field -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_map_field():
    schema = {
        "properties":{
            "pubdate":{ "type": "string", "title": "PubDate", "format": "datetime" },
            "item_1551264308487":{"type":"array","items":{},"title":"Title"}
        }
    }
    result = map_field(schema)
    assert result == {"Title":"item_1551264308487"}
    
# def subitem_recs(subitems, subitem_key_list, schema, oai_key_list, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_subitem_recs -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_subitem_recs(app):
    TEXT = "#text"
    # nomal
    subitems = {}
    subitem_key_list = ["subitem_text"]
    schema = {"items": {"properties": {"subitem_text": {"format": "text","type": "string","title": "test"}}}}
    oai_key_list = [TEXT]
    metadata = OrderedDict([('#text', 'test')])
    subitem_recs(subitems, subitem_key_list, schema, oai_key_list, metadata)
    assert subitems == {"subitem_text": "test"}
    # subitem key loss
    subitems = {}
    subitem_key_list = []
    schema = {"items": {"properties": {"subitem_text": {"format": "text","type": "string","title": "test"}}}}
    oai_key_list = [TEXT]
    metadata = OrderedDict([('#text', 'test')])
    subitem_recs(subitems, subitem_key_list, schema, oai_key_list, metadata)
    assert subitems == {}
    # oai key loss
    subitems = {}
    subitem_key_list = ["subitem_text"]
    schema = {"items": {"properties": {"subitem_text": {"format": "text","type": "string","title": "test"}}}}
    oai_key_list = []
    metadata = OrderedDict([('#text', 'test')])
    subitem_recs(subitems, subitem_key_list, schema, oai_key_list, metadata)
    assert subitems == {}
    # schema loss
    subitems = {}
    subitem_key_list = ["subitem_text"]
    schema = {}
    oai_key_list = [TEXT]
    metadata = OrderedDict([('#text', 'test')])
    subitem_recs(subitems, subitem_key_list, schema, oai_key_list, metadata)
    assert subitems == {}
    # schema and schema key is not match (case 1)
    subitems = {}
    subitem_key_list = ["subitem_text"]
    schema = {"items": {"properties": {"subitem_text_1": {"format": "text","type": "string","title": "test"}}}}
    oai_key_list = [TEXT]
    metadata = OrderedDict([('#text', 'test')])
    subitem_recs(subitems, subitem_key_list, schema, oai_key_list, metadata)
    assert subitems == {}
    # schema and schema key is not match (case 2)
    subitems = {}
    subitem_key_list = ["subitem_text"]
    schema = {"items": {"properties": {"subitem_level_1": {"properties" : {"subitem_text": {"format": "text","type": "string","title": "test"}}}}}}
    oai_key_list = ["level_1", TEXT]
    metadata = OrderedDict([('level_1', OrderedDict([('#text', 'test')]))])
    subitem_recs(subitems, subitem_key_list, schema, oai_key_list, metadata)
    assert subitems == {}
    # schema and schema key is not match (case 3)
    subitems = {}
    subitem_key_list = ["subitem_level_1", "subitem_value"]
    schema = {"items": {"properties": {"subitem_level_1": {"properties" : {"subitem_text": {"format": "text","type": "string","title": "test"}}}}}}
    oai_key_list = ["level_1", TEXT]
    metadata = OrderedDict([('level_1', OrderedDict([('#text', 'test')]))])
    subitem_recs(subitems, subitem_key_list, schema, oai_key_list, metadata)
    assert subitems == {}
    # schema and schema key is not match (case 4)
    subitems = {}
    subitem_key_list = ["subitem_level_1", "subitem_value"]
    schema = {"items": {"properties": {"subitem_text": {"properties" : {"subitem_value": {"format": "text","type": "string","title": "test"}}}}}}
    oai_key_list = ["level_1", TEXT]
    metadata = OrderedDict([('level_1', OrderedDict([('#text', 'test')]))])
    subitem_recs(subitems, subitem_key_list, schema, oai_key_list, metadata)
    assert subitems == {}
    # schema and schema key is not match (case 5)
    subitems = {}
    subitem_key_list = ["subitem_text"]
    schema = {"items": {"properties": {"subitem_level_1": {"items" : {"properties": {"subitem_text": {"format": "text","type": "string","title": "test"}}}}}}}
    oai_key_list = ["level_1", TEXT]
    metadata = OrderedDict([('level_1', [OrderedDict([('#text', 'test')])])])
    subitem_recs(subitems, subitem_key_list, schema, oai_key_list, metadata)
    assert subitems == {}
    # schema and schema key is not match (case 6)
    subitems = {}
    subitem_key_list = ["subitem_level_1", "subitem_value"]
    schema = {"items": {"properties": {"subitem_level_1": {"items" : {"properties": {"subitem_text": {"format": "text","type": "string","title": "test"}}}}}}}
    oai_key_list = ["level_1", TEXT]
    metadata = OrderedDict([('level_1', [OrderedDict([('#text', 'test')])])])
    subitem_recs(subitems, subitem_key_list, schema, oai_key_list, metadata)
    assert subitems == {}
    # schema and schema key is not match (case 7)
    subitems = {}
    subitem_key_list = ["subitem_level_1", "subitem_value"]
    schema = {"items": {"properties": {"subitem_text": {"items" : {"properties": {"subitem_value": {"format": "text","type": "string","title": "test"}}}}}}}
    oai_key_list = ["level_1", TEXT]
    metadata = OrderedDict([('level_1', [OrderedDict([('#text', 'test')])])])
    subitem_recs(subitems, subitem_key_list, schema, oai_key_list, metadata)
    assert subitems == {}
    # metadata and oai key is not match (case 1)
    subitems = {}
    subitem_key_list = ["subitem_text"]
    schema = {"items": {"properties": {"subitem_text": {"format": "text","type": "string","title": "test"}}}}
    oai_key_list = ["value"]
    metadata = OrderedDict([('#text', 'test')])
    subitem_recs(subitems, subitem_key_list, schema, oai_key_list, metadata)
    assert subitems == {}
    # metadata and oai key is not match (case 2)
    subitems = {}
    subitem_key_list = ["subitem_level_1", "subitem_text"]
    schema = {"items": {"properties": {"subitem_level_1": {"properties" : {"subitem_text": {"format": "text","type": "string","title": "test"}}}}}}
    oai_key_list = ["level_1", "value"]
    metadata = OrderedDict([('level_1', OrderedDict([('#text', 'test')]))])
    subitem_recs(subitems, subitem_key_list, schema, oai_key_list, metadata)
    assert subitems == {}
    # metadata and oai key is not match (case 3)
    subitems = {}
    subitem_key_list = ["subitem_level_1", "subitem_text"]
    schema = {"items": {"properties": {"subitem_level_1": {"properties" : {"subitem_text": {"format": "text","type": "string","title": "test"}}}}}}
    oai_key_list = ["level", TEXT]
    metadata = OrderedDict([('level_1', OrderedDict([('#text', 'test')]))])
    subitem_recs(subitems, subitem_key_list, schema, oai_key_list, metadata)
    assert subitems == {}
    # metadata and oai key is not match (case 4)
    subitems = {}
    subitem_key_list = ["subitem_level_1", "subitem_text"]
    schema = {"items": {"properties": {"subitem_level_1": {"properties" : {"subitem_text": {"format": "text","type": "string","title": "test"}}}}}}
    oai_key_list = ["level_1", "level_2", TEXT]
    metadata = OrderedDict([('level_1', OrderedDict([('#text', 'test')]))])
    subitem_recs(subitems, subitem_key_list, schema, oai_key_list, metadata)
    assert subitems == {}
    # metadata and oai key is not match (case 5)
    subitems = {}
    subitem_key_list = ["subitem_level_1", "subitem_text"]
    schema = {"items": {"properties": {"subitem_level_1": {"items" : {"properties": {"subitem_text": {"format": "text","type": "string","title": "test"}}}}}}}
    oai_key_list = ["level_1"]
    metadata = OrderedDict([('level_1', [OrderedDict([('#text', 'test')])])])
    subitem_recs(subitems, subitem_key_list, schema, oai_key_list, metadata)
    assert subitems == {}
    # metadata and oai key is not match (case 6)
    subitems = {}
    subitem_key_list = ["subitem_level_1", "subitem_text"]
    schema = {"items": {"properties": {"subitem_level_1": {"items" : {"properties": {"subitem_text": {"format": "text","type": "string","title": "test"}}}}}}}
    oai_key_list = ["level_1", "level_2"]
    metadata = OrderedDict([('level_1', [OrderedDict([('#text', 'test')])])])
    subitem_recs(subitems, subitem_key_list, schema, oai_key_list, metadata)
    assert subitems == {}
    # metadata and schema is not match (case 1)
    subitems = {}
    subitem_key_list = ["subitem_text"]
    schema = {"items": {"properties": {"subitem_text": {"format": "text","type": "string","title": "test"}}}}
    oai_key_list = [TEXT]
    metadata = OrderedDict([('test_value', [OrderedDict([('#text', 'test')])])])
    subitem_recs(subitems, subitem_key_list, schema, oai_key_list, metadata)
    assert subitems == {}
    # metadata and schema is not match (case 2)
    subitems = {}
    subitem_key_list = ["subitem_level_1", "subitem_text"]
    schema = {"items": {"properties": {"subitem_level_1": {"items" : {"properties": {"subitem_text": {"format": "text","type": "string","title": "test"}}}}}}}
    oai_key_list = ["level_1", TEXT]
    metadata = OrderedDict([('#text', 'test')])
    subitem_recs(subitems, subitem_key_list, schema, oai_key_list, metadata)
    assert subitems == {}
    # metadata and schema is not match (case 3)
    subitems = {}
    subitem_key_list = ["subitem_level_1", "subitem_text"]
    schema = {"items": {"properties": {"subitem_level_1": {"properties": {"subitem_text": {"format": "text","type": "string","title": "test"}}}}}}
    oai_key_list = ["level_1", TEXT]
    metadata = OrderedDict([('#text', 'test')])
    subitem_recs(subitems, subitem_key_list, schema, oai_key_list, metadata)
    assert subitems == {}


# def parsing_metadata(mappin, props, patterns, metadata, res):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_parsing_metadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_parsing_metadata(db_itemtype):
    item_type = ItemType.query.filter_by(id=10).first()
    item_type_mapping = Mapping.get_record(item_type.id)
    mappin = get_full_mapping(item_type_mapping, "jpcoar_mapping")
    props = item_type.schema.get("properties")

    patterns = [("not_exist_key","not_exist_value")]
    # not mapping
    res = {}
    result1, result2 = parsing_metadata(mappin, props, patterns, None, res)
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
    result1, result2 = parsing_metadata(mappin2, props, patterns, None, res)
    assert result1 == None
    assert result2 == None

    # subitems is [], mappin.get(elem) is None, subitems[0] not in item_schema
    metadata = [OrderedDict([('@xml:lang', 'ja'),('#text', 'test full item')])]
    patterns = [
        ('title.@value', '#text'),
        ('title.@attributes.xml:lang', '@xml:lang'),
        ('title.#text',"test_prop")
    ]
    mappin3 = {
        "title.@value": [
            "item_1551264308487"
        ],
        "title.#text":["test_key1.test_key2"]}
    res = {}
    result1, result2 = parsing_metadata(mappin3, props, patterns, metadata, res)
    assert result1 == "item_1551264308487"
    assert result2 == []

    # submetadata is list
    metadata = [OrderedDict([('jpcoar:givenName', OrderedDict([('@xml:lang', 'ja'), ('#text', '太郎1')]))])]
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
    props = {"main_item":{"properties":{
        "test_item1":{"properties":{"test_item":{"items":{"properties":{"item_key1":{'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'subitem_1551256006332': {'type': 'string', 'title': 'Creator Given Name', 'format': 'text', 'title_i18n': {'en': 'Creator Given Name', 'ja': '作成者名'}, 'title_i18n_temp': {'en': 'Creator Given Name', 'ja': '作成者名'}}, 'subitem_1551256007414': {'enum': [None,'ja','en'], 'type': ['null', 'string'], 'title': 'Language', 'format': 'select', 'currentEnum': ['ja','en']}}}, 'title': 'Creator Given Name', 'format': 'array'}}}}}},
        }}}
    submeta1 = [[{'subitem_1551256006332': '太郎1'}]]
    submeta2 = [[{'subitem_1551256006332': '太郎2'}]]
    submeta3 = [[{'subitem_1551256006332': '太郎3'}]]
    with patch("invenio_oaiharvester.harvester.subitem_recs",side_effect=[submeta1,submeta2,submeta3]):
        result1, result2 = parsing_metadata(mappin, props, patterns, metadata, res)
        assert result1 == "main_item"
        assert result2 == [{'test_item1': [[{'subitem_1551256006332': '太郎1'}], {'subitem_1551256006332': '太郎2'}, [{'subitem_1551256006332': '太郎3'}]]}]
    
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
        "main_item":{"properties":{
            "test_item1":{"properties":{"test_item":{"properties":{"test_key":"value"}}}
            }}
        }
    }
    submeta1 = {'test_key': 'value1'}
    submeta2 = {'test_key': 'value2'}
    with patch("invenio_oaiharvester.harvester.subitem_recs",side_effect=[submeta1,submeta2]):
        result1, result2 = parsing_metadata(mappin, props, patterns, metadata, res)
        assert result1 == "main_item"
        assert result2 == [{"test_item1":{"test_key":"value2"}}]

    
@pytest.fixture()
def mapper_jpcoar(db_itemtype):
    def factory(type):
        xml_str='<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><GetRecord><record><header><identifier>oai:weko3.example.org:00000001</identifier><datestamp>2023-02-20T06:24:47Z</datestamp><setSpec>1557819692844:1557819733276</setSpec><setSpec>1557820086539</setSpec></header><metadata><jpcoar:jpcoar xmlns:datacite="https://schema.datacite.org/meta/kernel-4/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcndl="http://ndl.go.jp/dcndl/terms/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:jpcoar="https://github.com/JPCOAR/schema/blob/master/1.0/" xmlns:oaire="http://namespace.openaire.eu/schema/oaire/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rioxxterms="http://www.rioxx.net/schema/v2.0/rioxxterms/" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="https://github.com/JPCOAR/schema/blob/master/1.0/" xsi:schemaLocation="https://github.com/JPCOAR/schema/blob/master/1.0/jpcoar_scm.xsd"><dc:title xml:lang="ja">test full item</dc:title><dcterms:alternative xml:lang="en">other title</dcterms:alternative><jpcoar:creator><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/1234" nameIdentifierScheme="ORCID">1234</jpcoar:nameIdentifier><jpcoar:creatorName xml:lang="ja">テスト, 太郎</jpcoar:creatorName><jpcoar:familyName xml:lang="ja">テスト</jpcoar:familyName><jpcoar:givenName xml:lang="ja">太郎</jpcoar:givenName><jpcoar:creatorAlternative xml:lang="ja">テスト　別郎</jpcoar:creatorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="http://www.isni.org/isni/5678" nameIdentifierScheme="ISNI">5678</jpcoar:nameIdentifier></jpcoar:affiliation></jpcoar:creator><jpcoar:contributor contributorType="ContactPerson"><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/5678" nameIdentifierScheme="ORCID">5678</jpcoar:nameIdentifier><jpcoar:contributorName xml:lang="en">test, smith</jpcoar:contributorName><jpcoar:familyName xml:lang="en">test</jpcoar:familyName><jpcoar:givenName xml:lang="en">smith</jpcoar:givenName><jpcoar:contributorAlternative xml:lang="en">other smith</jpcoar:contributorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="http://www.isni.org/isni/1234" nameIdentifierScheme="ISNI">1234</jpcoar:nameIdentifier></jpcoar:affiliation></jpcoar:contributor><dcterms:accessRights rdf:resource="http://purl.org/coar/access_right/c_14cb">metadata only access</dcterms:accessRights><rioxxterms:apc>Paid</rioxxterms:apc><dc:rights xml:lang="ja" rdf:resource="テスト権利情報Resource">テスト権利情報</dc:rights><jpcoar:rightsHolder><jpcoar:rightsHolderName xml:lang="ja">テスト　太郎</jpcoar:rightsHolderName></jpcoar:rightsHolder><jpcoar:subject xml:lang="ja" subjectURI="http://bsh.com" subjectScheme="BSH">テスト主題</jpcoar:subject><datacite:description xml:lang="en" descriptionType="Abstract">this is test abstract.</datacite:description><dc:publisher xml:lang="ja">test publisher</dc:publisher><datacite:date dateType="Accepted">2022-10-20</datacite:date><datacite:date dateType="Issued">2022-10-19</datacite:date><dc:language>jpn</dc:language><dc:type rdf:resource="http://purl.org/coar/resource_type/c_2fe3">newspaper</dc:type><datacite:version>1.1</datacite:version><oaire:version rdf:resource="http://purl.org/coar/version/c_b1a7d7d4d402bcce">AO</oaire:version><jpcoar:identifier identifierType="DOI">1111</jpcoar:identifier><jpcoar:identifier identifierType="DOI">https://doi.org/1234/0000000001</jpcoar:identifier><jpcoar:identifier identifierType="URI">https://192.168.56.103/records/1</jpcoar:identifier><jpcoar:identifierRegistration identifierType="JaLC">1234/0000000001</jpcoar:identifierRegistration><jpcoar:relation relationType="isVersionOf"><jpcoar:relatedIdentifier identifierType="ARK">1111111</jpcoar:relatedIdentifier><jpcoar:relatedTitle xml:lang="ja">関連情報テスト</jpcoar:relatedTitle></jpcoar:relation><jpcoar:relation relationType="isVersionOf"><jpcoar:relatedIdentifier identifierType="URI">https://192.168.56.103/records/3</jpcoar:relatedIdentifier></jpcoar:relation><dcterms:temporal xml:lang="ja">1 to 2</dcterms:temporal><datacite:geoLocation><datacite:geoLocationPoint><datacite:pointLongitude>12345</datacite:pointLongitude><datacite:pointLatitude>67890</datacite:pointLatitude></datacite:geoLocationPoint><datacite:geoLocationBox><datacite:westBoundLongitude>123</datacite:westBoundLongitude><datacite:eastBoundLongitude>456</datacite:eastBoundLongitude><datacite:southBoundLatitude>789</datacite:southBoundLatitude><datacite:northBoundLatitude>1112</datacite:northBoundLatitude></datacite:geoLocationBox><datacite:geoLocationPlace>テスト位置情報</datacite:geoLocationPlace></datacite:geoLocation><jpcoar:fundingReference><datacite:funderIdentifier funderIdentifierType="Crossref Funder">22222</datacite:funderIdentifier><jpcoar:funderName xml:lang="ja">テスト助成機関</jpcoar:funderName><datacite:awardNumber awardURI="https://test.research.com">1111</datacite:awardNumber><jpcoar:awardTitle xml:lang="ja">テスト研究</jpcoar:awardTitle></jpcoar:fundingReference><jpcoar:sourceIdentifier identifierType="PISSN">test source Identifier</jpcoar:sourceIdentifier><jpcoar:sourceTitle xml:lang="ja">test collectibles</jpcoar:sourceTitle><jpcoar:sourceTitle xml:lang="ja">test title book</jpcoar:sourceTitle><jpcoar:volume>5</jpcoar:volume><jpcoar:volume>1</jpcoar:volume><jpcoar:issue>2</jpcoar:issue><jpcoar:issue>2</jpcoar:issue><jpcoar:numPages>333</jpcoar:numPages><jpcoar:numPages>555</jpcoar:numPages><jpcoar:pageStart>123</jpcoar:pageStart><jpcoar:pageStart>789</jpcoar:pageStart><jpcoar:pageEnd>456</jpcoar:pageEnd><jpcoar:pageEnd>234</jpcoar:pageEnd><dcndl:dissertationNumber>9999</dcndl:dissertationNumber><dcndl:degreeName xml:lang="ja">テスト学位</dcndl:degreeName><dcndl:dateGranted>2022-10-19</dcndl:dateGranted><jpcoar:degreeGrantor><jpcoar:nameIdentifier nameIdentifierScheme="kakenhi">学位授与機関識別子テスト</jpcoar:nameIdentifier><jpcoar:degreeGrantorName xml:lang="ja">学位授与機関</jpcoar:degreeGrantorName></jpcoar:degreeGrantor><jpcoar:conference><jpcoar:conferenceName xml:lang="ja">テスト会議</jpcoar:conferenceName><jpcoar:conferenceSequence>12345</jpcoar:conferenceSequence><jpcoar:conferenceSponsor xml:lang="ja">テスト機関</jpcoar:conferenceSponsor><jpcoar:conferenceDate endDay="1" endYear="2005" endMonth="12" startDay="11" xml:lang="ja" startYear="2000" startMonth="4">12</jpcoar:conferenceDate><jpcoar:conferenceVenue xml:lang="ja">テスト会場</jpcoar:conferenceVenue><jpcoar:conferenceCountry>JPN</jpcoar:conferenceCountry></jpcoar:conference><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test1.txt</jpcoar:URI><jpcoar:mimeType>text/plain</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:date dateType="Accepted">2022-10-20</datacite:date><datacite:version>1.0</datacite:version></jpcoar:file><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test2</jpcoar:URI><jpcoar:mimeType>application/octet-stream</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:version>1.2</datacite:version></jpcoar:file><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test3.png</jpcoar:URI><jpcoar:mimeType>image/png</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:version>2.1</datacite:version></jpcoar:file></jpcoar:jpcoar></metadata></record></GetRecord></OAI-PMH>'
        
        tree = etree.fromstring(xml_str)
        record = tree.findall("./GetRecord/record",namespaces=tree.nsmap)[0]
        xml = etree.tostring(record,encoding="utf-8").decode()
        self_json = xmltodict.parse(xml)
        tags = self_json["record"]["metadata"]["jpcoar:jpcoar"]
        item_type = ItemType.query.filter_by(id=10).first()
        item_type_mapping = Mapping.get_record(item_type.id)
        item_map = get_full_mapping(item_type_mapping, "jpcoar_mapping")
        res = {"$schema":item_type.id,"pubdate":dateutil.parser.parse(str(self_json["record"]["header"].get("datestamp"))).date()}
        
        if not isinstance(tags[type],list):
            metadata = [tags[type]]
        else:
            metadata = tags[type]
        return item_type.schema.get("properties"),item_map,res,metadata
    return factory

@pytest.fixture()
def mapper_dc(db_itemtype):
    def factory(type):
        xml_str='<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2023-03-01T02:07:10Z</responseDate><request metadataPrefix="oai_dc" identifier="oai:weko3.example.org:00000001" verb="GetRecord">https://192.168.56.103/oai</request><GetRecord><record><header><identifier>oai:weko3.example.org:00000001</identifier><datestamp>2023-02-20T06:24:47Z</datestamp><setSpec>1557819692844:1557819733276</setSpec><setSpec>1557820086539</setSpec></header><metadata><oai_dc:dc xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" xmlns="http://www.w3.org/2001/XMLSchema" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd"><dc:title xml:lang="ja">test full item</dc:title><dc:creator>テスト, 太郎</dc:creator><dc:creator>1</dc:creator><dc:creator>1234</dc:creator><dc:subject>テスト主題</dc:subject><dc:description>this is test abstract.</dc:description><dc:publisher>test publisher</dc:publisher><dc:contributor>test, smith</dc:contributor><dc:contributor>2</dc:contributor><dc:contributor>5678</dc:contributor><dc:date>2022-10-20</dc:date><dc:type>conference paper</dc:type><dc:identifier>1111</dc:identifier><dc:source>test collectibles</dc:source><dc:language>jpn</dc:language><dc:relation>1111111</dc:relation><dc:coverage>1 to 2</dc:coverage><dc:rights>metadata only access</dc:rights><dc:format>text/plain</dc:format></oai_dc:dc></metadata></record></GetRecord></OAI-PMH>'

        tree = etree.fromstring(xml_str)
        record = tree.findall("./GetRecord/record",namespaces=tree.nsmap)[0]
        xml = etree.tostring(record,encoding="utf-8").decode()
        self_json = xmltodict.parse(xml)
        tags = self_json["record"]["metadata"]["oai_dc:dc"]
        item_type = ItemType.query.filter_by(id=12).first()
        item_type_mapping = Mapping.get_record(item_type.id)
        item_map = get_full_mapping(item_type_mapping, "oai_dc_mapping")
        res = {"$schema":item_type.id,"pubdate":dateutil.parser.parse(str(self_json["record"]["header"].get("datestamp"))).date()}
        if not isinstance(tags[type],list):
            metadata = [tags[type]]
        else:
            metadata = tags[type]
        return item_type.schema.get("properties"),item_map,res,metadata
    return factory


def xmltoTestData(key, xml):
    res = xmltodict.parse(xml)['record'][key]
    if isinstance(res, list):
        return res
    else:
        return [res]

# def add_title(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_title -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_title(app):
    xml = """
            <record>
                <dc:title xml:lang="en">test_en</dc:title>
            </record>
          """
    schema = {"item_key": {"items": {"type": "object","properties": {"subitem_title": {"format": "text","type": "string","title": "タイトル","title_i18n": {"en": "Title", "ja": "タイトル"}},"subitem_title_language": {"editAble": True,"type": ["null", "string"],"format": "select","currentEnum": [None, "en", "ja"],"enum": [None, "en", "ja"],"title": "言語","title_i18n": {"en": "Language", "ja": "言語"}}}}}}
    mapping = {'title.@value': ['item_key.subitem_title'], 'title.@attributes.xml:lang': ['item_key.subitem_title_language']}
    res = {}
    metadata = xmltoTestData('dc:title', xml)
    add_title(schema, mapping, res, metadata)
    assert res == {'title': 'test_en', 'item_key': [{'subitem_title': 'test_en', 'subitem_title_language': 'en'}]}

    xml = """
            <record>
                <dc:title xml:lang="ja">test_ja</dc:title>
                <dc:title>test</dc:title>
                <dc:title xml:lang="en">test_en</dc:title>
            </record>
          """
    res = {}
    metadata = xmltoTestData('dc:title', xml)
    add_title(schema, mapping, res, metadata)
    assert res == {'title': 'test_ja', 'item_key': [{'subitem_title': 'test_ja', 'subitem_title_language': 'ja'}, {'subitem_title': 'test'}, {'subitem_title': 'test_en', 'subitem_title_language': 'en'}]}

    xml = """
            <record>
                <dc:title>test</dc:title>
                <dc:title xml:lang="en">test_en</dc:title>
            </record>
          """
    res = {}
    metadata = xmltoTestData('dc:title', xml)
    add_title(schema, mapping, res, metadata)
    assert res == {'title': 'test', 'item_key': [{'subitem_title': 'test'}, {'subitem_title': 'test_en', 'subitem_title_language': 'en'}]}

# def add_alternative(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_alternative -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_alternative(app):
    xml = """
            <record>
                <dcterms:alternative xml:lang="en">test_en</dcterms:alternative>
            </record>
          """
    res = {}
    schema = {"item_key": {"items": {"type": "object","properties": {"subitem_alternative_title": {"format": "text","title": "その他のタイトル","type": "string","title_i18n": {"en": "Alternative Title", "ja": "その他のタイトル"}},"subitem_alternative_title_language": {"editAble": True,"type": ["null", "string"],"format": "select","currentEnum": [None, "en", "ja"],"enum": [None, "en", "ja"],"title": "言語","title_i18n": {"en": "Language", "ja": "言語"}}}}}}
    mapping = {'alternative.@value': ['item_key.subitem_alternative_title'], 'alternative.@attributes.xml:lang': ['item_key.subitem_alternative_title_language']}
    res = {}
    metadata = xmltoTestData('dcterms:alternative', xml)
    add_alternative(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_alternative_title': 'test_en', 'subitem_alternative_title_language': 'en'}]}

    xml = """
            <record>
                <dcterms:alternative xml:lang="en">test_en</dcterms:alternative>
                <dcterms:alternative xml:lang="ja">test_ja</dcterms:alternative>
                <dcterms:alternative>test</dcterms:alternative>
            </record>
          """
    res = {}
    metadata = xmltoTestData('dcterms:alternative', xml)
    add_alternative(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_alternative_title': 'test_en', 'subitem_alternative_title_language': 'en'}, {'subitem_alternative_title': 'test_ja', 'subitem_alternative_title_language': 'ja'}, {'subitem_alternative_title': 'test'}]}

    xml = """
            <record>
                <dcterms:alternative xml:lang="ja">test_ja</dcterms:alternative>
                <dcterms:alternative>test</dcterms:alternative>
                <dcterms:alternative xml:lang="en">test_en</dcterms:alternative>
            </record>
          """
    res = {}
    metadata = xmltoTestData('dcterms:alternative', xml)
    add_alternative(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_alternative_title': 'test_ja', 'subitem_alternative_title_language': 'ja'}, {'subitem_alternative_title': 'test'}, {'subitem_alternative_title': 'test_en', 'subitem_alternative_title_language': 'en'}]}

    xml = """
            <record>
                <dcterms:alternative>test</dcterms:alternative>
            </record>
          """
    res = {}
    metadata = xmltoTestData('dcterms:alternative', xml)
    add_alternative(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_alternative_title': 'test'}]}

# def add_creator_jpcoar(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_creator_jpcoar -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_creator_jpcoar(app):
    schema = {"item_key": {"items": {"system_prop": True,"type": "object","properties": {"iscreator": {"format": "text", "title": "iscreator", "type": "string"},"creatorType": {"type": "string","format": "text","title": "作成者タイプ","title_i18n": {"en": "Creator Type", "ja": "作成者タイプ"}},"creatorAlternatives": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"creatorAlternativeLang": {"editAble": True,"type": ["null", "string"],"format": "select","enum": [None, "en", "ja"],"currentEnum": [None, "en", "ja"],"title": "言語","title_i18n": {"en": "Language", "ja": "言語"}},"creatorAlternative": {"format": "text","title": "別名","title_i18n": {"en": "Alternative Name", "ja": "別名"},"type": "string"}}},"title": "作成者別名"},"creatorNames": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"creatorNameLang": {"editAble": True,"type": ["null", "string"],"format": "select","enum": [None, "en", "ja"],"currentEnum": [None, "en", "ja"],"title": "言語","title_i18n": {"en": "Language", "ja": "言語"}},"creatorNameType": {"type": ["null", "string"],"format": "select","enum": [None, "Personal", "Organizational"],"currentEnum": [None, "Personal", "Organizational"],"title": "名前タイプ","title_i18n": {"en": "Name Type", "ja": "名前タイプ"}},"creatorName": {"format": "text","title": "姓名","type": "string","title_i18n": {"en": "Name", "ja": "姓名"}}}},"title": "作成者姓名"},"nameIdentifiers": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"nameIdentifierScheme": {"type": ["null", "string"],"format": "select","currentEnum": [],"enum": [],"title": "作成者識別子Scheme","title_i18n": {"en": "IdentifierScheme","ja": "作成者識別子Scheme"}},"nameIdentifier": {"format": "text","title": "作成者識別子","title_i18n": {"en": "Creator Name Identifier","ja": "作成者識別子"},"type": "string"},"nameIdentifierURI": {"format": "text","title": "作成者識別子URI","title_i18n": {"en": "Creator Name Identifier URI","ja": "作成者識別子URI"},"type": "string"}}},"title": "作成者識別子"},"creatorAffiliations": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"affiliationNameIdentifiers": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"affiliationNameIdentifierScheme": {"type": ["null", "string"],"format": "select","enum": [None, "kakenhi", "ISNI", "Ringgold", "GRID"],"currentEnum": [None, "kakenhi", "ISNI", "Ringgold", "GRID"],"title": "所属機関識別子Scheme","title_i18n": {"en": "Affiliation Name Identifier Scheme","ja": "所属機関識別子Scheme"}},"affiliationNameIdentifier": {"format": "text","title": "所属機関識別子","title_i18n": {"en": "Affiliation Name Identifier","ja": "所属機関識別子"},"type": "string"},"affiliationNameIdentifierURI": {"format": "text","title": "所属機関識別子URI","title_i18n": {"en": "Affiliation Name Identifier URI","ja": "所属機関識別子URI"},"type": "string"}}},"title": "所属機関識別子"},"affiliationNames": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"affiliationName": {"format": "text","title": "所属機関名","title_i18n": {"en": "Affiliation Name","ja": "所属機関名"},"type": "string"},"affiliationNameLang": {"editAble": True,"type": ["null", "string"],"format": "select","enum": [None, "en", "ja"],"currentEnum": [None, "en", "ja"],"title": "言語","title_i18n": {"en": "Language","ja": "言語"}}}},"title": "所属機関名"}}},"title": "作成者所属"},"creatorMails": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"creatorMail": {"format": "text","title": "メールアドレス","title_i18n": {"en": "Email Address", "ja": "メールアドレス"},"type": "string"}}},"title": "作成者メールアドレス"},"givenNames": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"givenNameLang": {"editAble": True,"type": ["null", "string"],"format": "select","enum": [None, "en", "ja"],"currentEnum": [None, "en", "ja"],"title": "言語","title_i18n": {"en": "Language", "ja": "言語"}},"givenName": {"format": "text","title": "名","title_i18n": {"en": "Given Name", "ja": "名"},"type": "string"}}},"title": "作成者名"},"familyNames": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"familyNameLang": {"editAble": True,"type": ["null", "string"],"format": "select","currentEnum": [None, "en", "ja"],"enum": [None, "en", "ja"],"title": "言語","title_i18n": {"en": "Language", "ja": "言語"}},"familyName": {"format": "text","title": "姓","type": "string","title_i18n": {"en": "Family Name", "ja": "姓"}}}},"title": "作成者姓"}}}}}
    mapping = {
        'creator.givenName.@value': ['item_key.givenNames.givenName'],
        'creator.givenName.@attributes.xml:lang': ['item_key.givenNames.givenNameLang'],
        'creator.familyName.@value': ['item_key.familyNames.familyName'],
        'creator.familyName.@attributes.xml:lang': ['item_key.familyNames.familyNameLang'],
        'creator.creatorName.@value': ['item_key.creatorNames.creatorName'],
        'creator.creatorName.@attributes.xml:lang': ['item_key.creatorNames.creatorNameLang'],
        'creator.creatorName.@attributes.nameType': ['item_key.creatorNames.creatorNameType'],
        'creator.creatorAlternative.@value': ['item_key.creatorAlternatives.creatorAlternative'],
        'creator.creatorAlternative.@attributes.xml:lang': ['item_key.creatorAlternatives.creatorAlternativeLang'],
        'creator.@attributes.creatorType': ['item_key.creatorType'],
        'creator.nameIdentifier.@value': ['item_key.nameIdentifiers.nameIdentifier'],
        'creator.nameIdentifier.@attributes.nameIdentifierURI': ['item_key.nameIdentifiers.nameIdentifierURI'],
        'creator.nameIdentifier.@attributes.nameIdentifierScheme': ['item_key.nameIdentifiers.nameIdentifierScheme'],
        'creator.affiliation.nameIdentifier.@value': ['item_key.creatorAffiliations.affiliationNameIdentifiers.affiliationNameIdentifier'],
        'creator.affiliation.nameIdentifier.@attributes.nameIdentifierURI': ['item_key.creatorAffiliations.affiliationNameIdentifiers.affiliationNameIdentifierURI'],
        'creator.affiliation.nameIdentifier.@attributes.nameIdentifierScheme': ['item_key.creatorAffiliations.affiliationNameIdentifiers.affiliationNameIdentifierScheme'],
        'creator.affiliation.affiliationName.@value': ['item_key.creatorAffiliations.affiliationNames.affiliationName'],
        'creator.affiliation.affiliationName.@attributes.xml:lang': ['item_key.creatorAffiliations.affiliationNames.affiliationNameLang']
    }
    xml = """
            <record>
                <jpcoar:creator creatorType="Test type">
                    <jpcoar:nameIdentifier nameIdentifierScheme="ROR" 
                        nameIdentifierURI="https://ror.org/weko1">
                        weko1
                    </jpcoar:nameIdentifier>
                    <jpcoar:creatorName xml:lang="en">Test creator name 1</jpcoar:creatorName>
                    <jpcoar:familyName xml:lang="en">Test family name 1</jpcoar:familyName>
                    <jpcoar:givenName xml:lang="en">Test given name 1</jpcoar:givenName>
                    <jpcoar:creatorAlternative xml:lang="en">Test alternative name</jpcoar:creatorAlternative>
                    <jpcoar:affiliation>
                        <jpcoar:nameIdentifier nameIdentifierScheme="GRID" 
                            nameIdentifierURI="https://affiliation.name.id/uri">
                            Test affiliation name identifier
                        </jpcoar:nameIdentifier>
                        <jpcoar:affiliationName xml:lang="en">Test affiliation name</jpcoar:affiliationName>
                    </jpcoar:affiliation>
                </jpcoar:creator>
            </record>
          """
    res = {}
    metadata = xmltoTestData('jpcoar:creator', xml)
    add_creator_jpcoar(schema, mapping, res, metadata)
    assert res == {'item_key': [{'creatorType': 'Test type', 'givenNames': [{'givenName': 'Test given name 1', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': 'Test family name 1', 'familyNameLang': 'en'}], 'creatorNames': [{'creatorName': 'Test creator name 1', 'creatorNameLang': 'en'}], 'creatorAlternatives': [{'creatorAlternative': 'Test alternative name', 'creatorAlternativeLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'weko1', 'nameIdentifierURI': 'https://ror.org/weko1', 'nameIdentifierScheme': 'ROR'}], 'creatorAffiliations': [{'affiliationNameIdentifiers': [{'affiliationNameIdentifier': 'Test affiliation name identifier', 'affiliationNameIdentifierURI': 'https://affiliation.name.id/uri', 'affiliationNameIdentifierScheme': 'GRID'}], 'affiliationNames': [{'affiliationName': 'Test affiliation name', 'affiliationNameLang': 'en'}]}]}]}

    xml = """
            <record>
                <jpcoar:creator>
                    <jpcoar:affiliation>
                        <jpcoar:affiliationName>Test affiliation name none</jpcoar:affiliationName>
                        <jpcoar:affiliationName xml:lang="en">Test affiliation name en</jpcoar:affiliationName>
                    </jpcoar:affiliation>
                </jpcoar:creator>
            </record>
          """
    res = {}
    metadata = xmltoTestData('jpcoar:creator', xml)
    add_creator_jpcoar(schema, mapping, res, metadata)
    assert res == {'item_key': [{'creatorAffiliations': [{'affiliationNames': [{'affiliationName': 'Test affiliation name none'}, {'affiliationName': 'Test affiliation name en', 'affiliationNameLang': 'en'}]}]}]}

# def add_contributor_jpcoar(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_contributor_jpcoar -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_contributor_jpcoar(app):
    schema = {"item_key": {"items": {"system_prop": True,"type": "object","properties": {"contributorType": {"enum": [None,"ContactPerson","DataCollector","DataCurator","DataManager","Distributor","Editor","HostingInstitution","Producer","ProjectLeader","ProjectManager","ProjectMember","RelatedPerson","Researcher","ResearchGroup","Sponsor","Supervisor","WorkPackageLeader","Other"],"format": "select","title": "寄与者タイプ","type": ["null", "string"]},"nameIdentifiers": {"format": "array","items": {"format": "object","properties": {"nameIdentifier": {"format": "text","title": "寄与者識別子","type": "string"},"nameIdentifierScheme": {"format": "select","title": "寄与者識別子Scheme","type": ["null", "string"]},"nameIdentifierURI": {"format": "text","title": "寄与者識別子URI","type": "string"}},"type": "object"},"title": "寄与者識別子","type": "array"},"contributorNames": {"format": "array","items": {"format": "object","properties": {"contributorName": {"format": "text","title": "姓名","type": "string"},"lang": {"editAble": True,"enum": [None, "en", "ja"],"format": "select","title": "言語","type": ["null", "string"]},"nameType": {"editAble": False,"enum": [None, "Personal", "Organizational"],"format": "select","title": "名前タイプ","type": ["null", "string"]}},"type": "object"},"title": "寄与者姓名","type": "array"},"familyNames": {"format": "array","items": {"format": "object","properties": {"familyNameLang": {"editAble": True,"enum": [None, "en", "ja"],"format": "select","title": "言語","type": ["null", "string"]},"familyName": {"format": "text","title": "姓","type": "string"}},"type": "object"},"title": "寄与者姓","type": "array"},"givenNames": {"format": "array","items": {"format": "object","properties": {"givenName": {"format": "text","title": "名","type": "string"},"givenNameLang": {"editAble": True,"enum": [None, "en", "ja"],"format": "select","title": "言語","type": ["null", "string"]}},"type": "object"},"title": "寄与者名","type": "array"},"contributorAlternatives": {"format": "array","items": {"format": "object","properties": {"contributorAlternativeLang": {"editAble": True,"enum": [None, "en", "ja"],"format": "select","title": "言語","type": ["null", "string"]},"contributorAlternative": {"format": "text","title": "別名","type": "string"}},"type": "object"},"title": "寄与者別名","type": "array"},"contributorAffiliations": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"contributorAffiliationNameIdentifiers": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"contributorAffiliationScheme": {"type": ["null", "string"],"format": "select","enum": [None, "kakenhi", "ISNI", "Ringgold", "GRID"],"title": "所属機関識別子Scheme"},"contributorAffiliationNameIdentifier": {"format": "text","title": "所属機関識別子","type": "string"},"contributorAffiliationURI": {"format": "text","title": "所属機関識別子URI","type": "string"}}},"title": "所属機関識別子"},"contributorAffiliationNames": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"contributorAffiliationName": {"format": "text","title": "所属機関名","type": "string"},"contributorAffiliationNameLang": {"editAble": True,"type": ["null", "string"],"format": "select","enum": [None, "en", "ja"],"title": "言語"}}},"title": "所属機関名"}}},"title": "寄与者所属"},"contributorMails": {"format": "array","items": {"format": "object","properties": {"contributorMail": {"format": "text","title": "メールアドレス","type": "string"}},"type": "object"},"title": "寄与者メールアドレス","type": "array"}}}}}
    mapping = {
        'contributor.@attributes.contributorType': ['item_key.contributorType'],
        'contributor.nameIdentifier.@value': ['item_key.nameIdentifiers.nameIdentifier'],
        'contributor.nameIdentifier.@attributes.nameIdentifierURI': ['item_key.nameIdentifiers.nameIdentifierURI'],
        'contributor.nameIdentifier.@attributes.nameIdentifierScheme': ['item_key.nameIdentifiers.nameIdentifierScheme'],
        'contributor.givenName.@value': ['item_key.givenNames.givenName'],
        'contributor.givenName.@attributes.xml:lang': ['item_key.givenNames.givenNameLang'],
        'contributor.familyName.@value': ['item_key.familyNames.familyName'],
        'contributor.familyName.@attributes.xml:lang': ['item_key.familyNames.familyNameLang'],
        'contributor.contributorName.@value': ['item_key.contributorNames.contributorName'],
        'contributor.contributorName.@attributes.xml:lang': ['item_key.contributorNames.lang'],
        'contributor.contributorName.@attributes.nameType': ['item_key.contributorNames.nameType'],
        'contributor.contributorAlternative.@value': ['item_key.contributorAlternatives.contributorAlternative'],
        'contributor.contributorAlternative.@attributes.xml:lang': ['item_key.contributorAlternatives.contributorAlternativeLang'],
        'contributor.affiliation.nameIdentifier.@value': ['item_key.contributorAffiliations.contributorAffiliationNameIdentifiers.contributorAffiliationNameIdentifier'],
        'contributor.affiliation.nameIdentifier.@attributes.nameIdentifierURI': ['item_key.contributorAffiliations.contributorAffiliationNameIdentifiers.contributorAffiliationURI'],
        'contributor.affiliation.nameIdentifier.@attributes.nameIdentifierScheme': ['item_key.contributorAffiliations.contributorAffiliationNameIdentifiers.contributorAffiliationScheme'],
        'contributor.affiliation.affiliationName.@value': ['item_key.contributorAffiliations.contributorAffiliationNames.contributorAffiliationName'],
        'contributor.affiliation.affiliationName.@attributes.xml:lang': ['item_key.contributorAffiliations.contributorAffiliationNames.contributorAffiliationNameLang']
    }
    xml = """
            <record>
                <jpcoar:contributor contributorType="Editor">
                    <jpcoar:nameIdentifier nameIdentifierScheme="ORCID" 
                        nameIdentifierURI="https://orcid.org/0000-0001-0002-0003">
                        0000-0001-0002-0003
                    </jpcoar:nameIdentifier> 
                    <jpcoar:contributorName xml:lang="ja">山田, 一郎</jpcoar:contributorName>
                    <jpcoar:contributorName xml:lang="en">Yamada, Ichiro</jpcoar:contributorName> 
                    <jpcoar:familyName xml:lang="ja">山田</jpcoar:familyName>
                    <jpcoar:givenName xml:lang="ja">一郎</jpcoar:givenName>
                    <jpcoar:affiliation> 
                        <jpcoar:nameIdentifier nameIdentifierScheme="ROR">https://ror.org/057zh3y96</jpcoar:nameIdentifier>
                        <jpcoar:affiliationName xml:lang="ja">東京大学</jpcoar:affiliationName>
                        <jpcoar:affiliationName xml:lang="en">The University of Tokyo</jpcoar:affiliationName>
                    </jpcoar:affiliation>
                </jpcoar:contributor>
            </record>
          """
    res = {}
    metadata = xmltoTestData('jpcoar:contributor', xml)
    add_contributor_jpcoar(schema, mapping, res, metadata)
    assert res == {'item_key': [{'contributorType': 'Editor', 'givenNames': [{'givenName': '一郎', 'givenNameLang': 'ja'}], 'familyNames': [{'familyName': '山田', 'familyNameLang': 'ja'}], 'contributorNames': [{'contributorName': '山田, 一郎', 'lang': 'ja'},{'contributorName': 'Yamada, Ichiro', 'lang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': '0000-0001-0002-0003', 'nameIdentifierURI': 'https://orcid.org/0000-0001-0002-0003', 'nameIdentifierScheme': 'ORCID'}], 'contributorAffiliations': [{'contributorAffiliationNameIdentifiers': [{'contributorAffiliationNameIdentifier': 'https://ror.org/057zh3y96', 'contributorAffiliationScheme': 'ROR'}], 'contributorAffiliationNames': [{'contributorAffiliationName': '東京大学', 'contributorAffiliationNameLang': 'ja'}, {'contributorAffiliationName': 'The University of Tokyo', 'contributorAffiliationNameLang': 'en'}]}]}]}

# def add_access_right(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_access_right -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_access_right(app):
    schema = {'item_key': {"system_prop": True,"type": "object","title": "アクセス権","properties": {"subitem_access_right": {"type": ["null", "string"],"format": "select","enum": [None,"embargoed access","metadata only access","open access","restricted access"],"currentEnum": [None,"embargoed access","metadata only access","open access","restricted access"],"title": "アクセス権","title_i18n": {"en": "Access Rights", "ja": "アクセス権"}},"subitem_access_right_uri": {"format": "text","title": "アクセス権URI","title_i18n": {"en": "Access Rights URI", "ja": "アクセス権URI"},"type": "string"}}}}
    mapping = {
        'accessRights.@value': ['item_key.subitem_access_right'],
        'accessRights.@attributes.rdf:resource': ['item_key.subitem_access_right_uri']
    }
    xml = """
            <record>
                <dcterms:accessRights rdf:resource="http://purl.org/coar/access_right/c_abf2">
                    open access
                </dcterms:accessRights>
            </record>
          """
    res = {}
    metadata = xmltoTestData('dcterms:accessRights', xml)
    add_access_right(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_access_right': 'open access', 'subitem_access_right_uri': 'http://purl.org/coar/access_right/c_abf2'}]}

# def add_apc(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_apc -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_apc(app):
    schema = {'item_key': {"type": "object","title": "APC","properties": {"subitem_apc": {"title": "APC","title_i18n": {"en": "APC", "ja": "APC"},"type": ["null", "string"],"format": "select","enum": [None,"Paid","Partially waived","Fully waived","Not charged","Not required","Unknown"],"currentEnum": [None,"Paid","Partially waived","Fully waived","Not charged","Not required","Unknown"]}}}}
    mapping = {
        'apc.@value': ['item_key.subitem_apc']
    }
    xml = """
            <record>
                <rioxxterms:apc>Paid</rioxxterms:apc>
            </record>
          """
    res = {}
    metadata = xmltoTestData('rioxxterms:apc', xml)
    add_apc(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_apc': 'Paid'}]}

# def add_right(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_right -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_right(app):
    schema = {'item_key': {'items': {"type": "object","properties": {"subitem_rights": {"format": "text", "title": "権利情報", "type": "string"},"subitem_rights_language": {"editAble": True,"type": ["null", "string"],"format": "select","enum": [None, "en", "ja"],"title": "言語",},"subitem_rights_resource": {"format": "text","title": "権利情報Resource","type": "string"}}}}}
    mapping = {
        'rights.@value': ['item_key.subitem_rights'],
        'rights.@attributes.xml:lang': ['item_key.subitem_rights_language'],
        'rights.@attributes.rdf:resource': ['item_key.subitem_rights_resource']
    }
    xml = """
            <record>
                <dc:rights xml:lang="en" 
                    rdf:resource="https://creativecommons.org/licenses/by/4.0/deed.en">
                    Creative Commons Attribution 4.0 International
                </dc:rights> 
                <dc:rights xml:lang="en">Copyright (c) 1997 American Physical Society</dc:rights> 
                <dc:rights xml:lang="en">(c) ACM 2016. This is the author's version of the work. It is posted here for your personal use. Not for redistribution. The definitive Version of Record was published in http://doi.org/10.1145/123456789
                </dc:rights>
            </record>
          """
    res = {}
    metadata = xmltoTestData('dc:rights', xml)
    add_right(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_rights': 'Creative Commons Attribution 4.0 International', 'subitem_rights_language': 'en', 'subitem_rights_resource': 'https://creativecommons.org/licenses/by/4.0/deed.en'}, {'subitem_rights': 'Copyright (c) 1997 American Physical Society', 'subitem_rights_language': 'en'}, {'subitem_rights': "(c) ACM 2016. This is the author's version of the work. It is posted here for your personal use. Not for redistribution. The definitive Version of Record was published in http://doi.org/10.1145/123456789", 'subitem_rights_language': 'en'}]}

# def add_subject(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_subject -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_subject(app):
    schema = {'item_key': {'items': {"type": "object","properties": {"subitem_subject": {"format": "text","title": "主題","title_i18n": {"en": "Subject", "ja": "主題"},"type": "string"},"subitem_subject_language": {"editAble": True,"type": ["null", "string"],"format": "select","enum": [None ,'ja', 'en'],"currentEnum": [None ,'ja', 'en'],"title": "言語","title_i18n": {"en": "Language", "ja": "言語"}},"subitem_subject_scheme": {"type": ["null", "string"],"format": "select","enum": [None,"BSH","DDC","e-Rad_field","JEL","LCC","LCSH","MeSH","NDC","NDLC","NDLSH","SciVal","UDC","Other"],"currentEnum": [None,"BSH","DDC","e-Rad_field","JEL","LCC","LCSH","MeSH","NDC","NDLC","NDLSH","SciVal","UDC","Other"],"title": "主題Scheme","title_i18n": {"en": "Subject Scheme", "ja": "主題Scheme"}},"subitem_subject_uri": {"format": "text","title": "主題URI","title_i18n": {"en": "Subject URI", "ja": "主題URI"},"type": "string"}}}}}
    mapping = {
        'subject.@value': ['item_key.subitem_subject'],
        'subject.@attributes.xml:lang': ['item_key.subitem_subject_language'],
        'subject.@attributes.subjectURI': ['item_key.subitem_subject_uri'],
        'subject.@attributes.subjectScheme': ['item_key.subitem_subject_scheme']
    }
    xml = """
            <record>
                <jpcoar:subject subjectScheme="NDC">007</jpcoar:subject>
                <jpcoar:subject xml:lang="ja" subjectScheme="NDLSH" 
                    subjectURI="https://id.ndl.go.jp/auth/ndlsh/01009109">
                    社会情報学
                </jpcoar:subject>
            </record>
          """
    res = {}
    metadata = xmltoTestData('jpcoar:subject', xml)
    add_subject(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_subject': '007', 'subitem_subject_scheme': 'NDC'}, {'subitem_subject': '社会情報学', 'subitem_subject_language': 'ja', 'subitem_subject_uri': 'https://id.ndl.go.jp/auth/ndlsh/01009109', 'subitem_subject_scheme': 'NDLSH'}]}

# def add_description(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_description -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_description(app):
    schema = {'item_key': {'items': {"type": "object","properties": {"subitem_description": {"format": "textarea","title": "内容記述","type": "string"},"subitem_description_language": {"editAble": True,"type": ["null", "string"],"format": "select","enum": [None ,'ja', 'en'],"title": "言語"},"subitem_description_type": {"type": ["null", "string"],"format": "select","enum": [None,"Abstract","Methods","TableOfContents","TechnicalInfo","Other"],"title": "内容記述タイプ"}}}}}
    mapping = {
        'description.@value': ['item_key.subitem_description'],
        'description.@attributes.xml:lang': ['item_key.subitem_description_language'],
        'description.@attributes.descriptionType': ['item_key.subitem_description_type']
    }
    xml = """
            <record>
                <datacite:description xml:lang="ja" descriptionType="Abstract">
                    Test description
                </datacite:description>
            </record>
          """
    res = {}
    metadata = xmltoTestData('datacite:description', xml)
    add_description(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_description': 'Test description', 'subitem_description_language': 'ja', 'subitem_description_type': 'Abstract'}]}

# def add_publisher(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_publisher -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_publisher(app):
    schema = {'item_key': {'items': {"type": "object","properties": {"subitem_publisher": {"format": "text","title": "出版者","title_i18n": {"en": "Publisher", "ja": "出版者"},"type": "string"},"subitem_publisher_language": {"editAble": True,"type": ["null", "string"],"format": "select","enum": [None ,'ja', 'en'],"currentEnum": [None ,'ja', 'en'],"title": "言語","title_i18n": {"en": "Language", "ja": "言語"}}}}}}
    mapping = {
        'publisher.@value': ['item_key.subitem_publisher'],
        'publisher.@attributes.xml:lang': ['item_key.subitem_publisher_language']
    }
    xml = """
            <record>
                <dc:publisher xml:lang="en">Elsevier</dc:publisher>
                <dc:publisher xml:lang="ja">日本物理学会</dc:publisher>
            </record>
          """
    res = {}
    metadata = xmltoTestData('dc:publisher', xml)
    add_publisher(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_publisher': 'Elsevier', 'subitem_publisher_language': 'en'}, {'subitem_publisher': '日本物理学会', 'subitem_publisher_language': 'ja'}]}

# def add_publisher_jpcoar(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_publisher_jpcoar -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_publisher_jpcoar(app):
    schema = {'item_key': {'items': {"type": "object","format": "object","title": "publisher_information","properties": {"publisher_names": {"type": "array","format": "array","title": "出版者名","items": {"type": "object","format": "object","properties": {"publisher_name": {"type": "string","format": "text","title": "出版者名","title_i18n": {"ja": "出版者名", "en": "Publisher Name"}},"publisher_name_language": {"type": "string","format": "select","enum": [None, 'ja', 'en'],"title": "言語","title_i18n": {"ja": "言語", "en": "Language"}}}}},"publisher_descriptions": {"type": "array","format": "array","title": "出版者注記","items": {"type": "object","format": "object","properties": {"publisher_description": {"type": "string","format": "text","title": "出版者注記","title_i18n": {"ja": "出版者注記","en": "Publisher Description"}},"publisher_description_language": {"type": ["null", "string"],"format": "select","enum": [None, 'ja', 'en'],"title": "言語","title_i18n": {"ja": "言語", "en": "Language"}}}}},"publisher_locations": {"type": "array","format": "array","title": "出版地","items": {"type": "object","format": "object","properties": {"publisher_location": {"type": "string","format": "text","title": "出版地","title_i18n": {"ja": "出版地", "en": "Publication Place"}},"publisher_location_language": {"type": ["null", "string"],"format": "select","enum": [None, 'ja', 'en'],"title": "言語","title_i18n": {"ja": "言語", "en": "Language"}}}}},"publication_places": {"type": "array","format": "array","title": "出版地（国名コード）","items": {"type": "object","format": "object","properties": {"publication_place": {"type": "string","format": "text","title": "出版地（国名コード）","title_i18n": {"ja": "出版地（国名コード）","en": "Publication Place (Country code)"}},"publication_place_language": {"type": ["null", "string"],"format": "select","enum": [None, 'ja', 'en'],"title": "言語","title_i18n": {"ja": "言語", "en": "Language"}}}}}}}}}
    mapping = {
        'publisher_jpcoar.publisherName.@value': ['item_key.publisher_names.publisher_name'],
        'publisher_jpcoar.publisherName.@attributes.xml:lang': ['item_key.publisher_names.publisher_name_language'],
        'publisher_jpcoar.publisherDescription.@value': ['item_key.publisher_descriptions.publisher_description'],
        'publisher_jpcoar.publisherDescription.@attributes.xml:lang': ['item_key.publisher_descriptions.publisher_description_language'],
        'publisher_jpcoar.location.@value': ['item_key.publisher_locations.publisher_location'],
        'publisher_jpcoar.location.@attributes.xml:lang': ['item_key.publisher_locations.publisher_location_language'],
        'publisher_jpcoar.publicationPlace.@value': ['item_key.publication_places.publication_place'],
        'publisher_jpcoar.publicationPlace.@attributes.xml:lang': ['item_key.publication_places.publication_place_language']
    }
    xml = """
            <record>
                <jpcoar:publisher>
                    <jpcoar:publisherName xml:lang="ja">霞ケ関出版</jpcoar:publisherName>
                    <jpcoar:publisherDescription xml:lang="ja">印刷</jpcoar:publisherDescription>
                    <dcndl:location xml:lang="ja">東京</dcndl:location>
                    <dcndl:publicationPlace>JPN</dcndl:publicationPlace> 
                </jpcoar:publisher>
            </record>
          """
    res = {}
    metadata = xmltoTestData('jpcoar:publisher', xml)
    add_publisher_jpcoar(schema, mapping, res, metadata)
    assert res == {'item_key': [{'publisher_names': [{'publisher_name': '霞ケ関出版', 'publisher_name_language': 'ja'}], 'publisher_descriptions': [{'publisher_description': '印刷', 'publisher_description_language': 'ja'}], 'publisher_locations': [{'publisher_location': '東京', 'publisher_location_language': 'ja'}], 'publication_places': [{'publication_place': 'JPN'}]}]}

# def add_date(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_date -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_date(app):
    schema = {'item_key': {'items': {"type": "object","properties": {"subitem_date_issued_datetime": {"format": "datetime","title": "日付","type": "string"},"subitem_date_issued_type": {"type": ["null", "string"],"format": "select","enum": [None,"Accepted","Available","Collected","Copyrighted","Created","Issued","Submitted","Updated","Valid"],"title": "日付タイプ"}}}}}
    mapping = {
        'date.@value': ['item_key.subitem_date_issued_datetime'],
        'date.@attributes.dateType': ['item_key.subitem_date_issued_type']
    }
    xml = """
            <record>
                <datacite:date dateType="Issued">2015-10-01</datacite:date>
                <datacite:date dateType="Available">2016-01-01</datacite:date>
            </record>
          """
    res = {}
    metadata = xmltoTestData('datacite:date', xml)
    add_date(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_date_issued_datetime': '2015-10-01', 'subitem_date_issued_type': 'Issued'}, {'subitem_date_issued_datetime': '2016-01-01', 'subitem_date_issued_type': 'Available'}]}

# def add_date_dcterms(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_date_dcterms -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_date_dcterms(app):
    schema = {'item_key': {'items': {"system_prop": False,"type": "object","title": "dcterms_date","properties": {"subitem_dcterms_date": {"type": "string","format": "text","title": "日付（リテラル）","title_i18n": {"en": "Date Literal", "ja": "日付（リテラル）"},},"subitem_dcterms_date_language": {"editAble": True,"type": ["null", "string"],"format": "select","enum": [None, 'ja', 'en'],"title": "言語"}}}}}
    mapping = {
        'date_dcterms.@value': ['item_key.subitem_dcterms_date'],
        'date_dcterms.@attributes.xml:lang': ['item_key.subitem_dcterms_date_language']
    }
    xml = """
            <record>
                <dcterms:date xml:lang="ja">宝暦年間</dcterms:date>
                <dcterms:date>19--</dcterms:date>
            </record>
          """
    res = {}
    metadata = xmltoTestData('dcterms:date', xml)
    add_date_dcterms(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_dcterms_date': '宝暦年間', 'subitem_dcterms_date_language': 'ja'}, {'subitem_dcterms_date': '19--'}]}

# def add_edition(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_edition -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_edition(app):
    schema = {'item_key': {'items': {"type": "object","format": "object","title": "edition","properties": {"edition": {"type": "string","format": "text","title": "版","title_i18n": {"ja": "版", "en": "Edition"},},"edition_language": {"type": "string","format": "select","enum": [None, 'ja', 'en'],"title": "言語","title_i18n": {"en": "Language", "ja": "言語"}}}}}}
    mapping = {
        'edition.@value': ['item_key.edition'],
        'edition.@attributes.xml:lang': ['item_key.edition_language']
    }
    xml = """
            <record>
                <dcndl:edition xml:lang="ja">改訂新版</dcndl:edition>
                <dcndl:edition xml:lang="ja">宮城野の一部を改刻した改題本</dcndl:edition>
            </record>
          """
    res = {}
    metadata = xmltoTestData('dcndl:edition', xml)
    add_edition(schema, mapping, res, metadata)
    assert res == {'item_key': [{'edition': '改訂新版', 'edition_language': 'ja'}, {'edition': '宮城野の一部を改刻した改題本', 'edition_language': 'ja'}]}

# def add_volumeTitle(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_volumeTitle -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_volumeTitle(app):
    schema = {'item_key': {'items': {"type": "object","format": "object","title": "volume_title","properties": {"volume_title": {"type": "string","format": "text","title": "部編名","title_i18n": {"ja": "部編名", "en": "Volume Title"},},"volume_title_language": {"type": "string","format": "select","enum": [None, 'ja', 'en', 'ja-Kana'],"title": "Language","title_i18n": {"ja": "言語", "en": "Language"}}}}}}
    mapping = {
        'volumeTitle.@value': ['item_key.volume_title'],
        'volumeTitle.@attributes.xml:lang': ['item_key.volume_title_language']
    }
    xml = """
            <record>
                <dcndl:volumeTitle xml:lang="ja">近畿.△2 三重・和歌山・大阪・兵庫</dcndl:volumeTitle>
                <dcndl:volumeTitle xml:lang="ja-Kana">キンキ.△2 ミエ ワカヤマ オオサカ ヒョウゴ</dcndl:volumeTitle>
            </record>
          """
    res = {}
    metadata = xmltoTestData('dcndl:volumeTitle', xml)
    add_volumeTitle(schema, mapping, res, metadata)
    assert res == {'item_key': [{'volume_title': '近畿.△2 三重・和歌山・大阪・兵庫', 'volume_title_language': 'ja'}, {'volume_title': 'キンキ.△2 ミエ ワカヤマ オオサカ ヒョウゴ', 'volume_title_language': 'ja-Kana'}]}

# def add_originalLanguage(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_originalLanguage -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_originalLanguage(app):
    schema = {'item_key': {'items': {"type": "object","format": "object","title": "original_language","properties": {"original_language": {"type": "string","format": "text","title": "Original Language","title_i18n": {"ja": "原文の言語", "en": "Volume Title"}}}}}}
    mapping = {
        'originalLanguage.@value': ['item_key.original_language']
    }
    xml = """
            <record>
                <dcndl:originalLanguage>eng</dcndl:originalLanguage>
                <dcndl:originalLanguage>jpn</dcndl:originalLanguage>
            </record>
          """
    res = {}
    metadata = xmltoTestData('dcndl:originalLanguage', xml)
    add_originalLanguage(schema, mapping, res, metadata)
    assert res == {'item_key': [{'original_language': 'eng'}, {'original_language': 'jpn'}]}

# def add_extent(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_extent -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_extent(app):
    schema = {'item_key': {'items': {"type": "object","format": "object","title": "dcterms_extent","properties": {"dcterms_extent": {"type": "string","format": "text","title": "Extent","title_i18n": {"ja": "大きさ", "en": "Extent"},},"dcterms_extent_language": {"type": "string","format": "select","enum": [None, 'ja', 'en'],"title": "Language","title_i18n": {"ja": "言語", "en": "Language"}}}}}}
    mapping = {
        'extent.@value': ['item_key.dcterms_extent'],
        'extent.@attributes.xml:lang': ['item_key.dcterms_extent_language']
    }
    xml = """
            <record>
                <dcterms:extent xml:lang="ja">図版△;△19cm</dcterms:extent>
                <dcterms:extent xml:lang="ja">22cm△+△CD-ROM1 枚（12cm）</dcterms:extent>
            </record>
          """
    res = {}
    metadata = xmltoTestData('dcterms:extent', xml)
    add_extent(schema, mapping, res, metadata)
    assert res == {'item_key': [{'dcterms_extent': '図版△;△19cm', 'dcterms_extent_language': 'ja'}, {'dcterms_extent': '22cm△+△CD-ROM1 枚（12cm）', 'dcterms_extent_language': 'ja'}]}

# def add_format(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_format -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_format(app):
    schema = {'item_key': {'items': {"type": "object","format": "object","title": "jpcoar_format","properties": {"jpcoar_format": {"type": "string","format": "text","title": "物理的形態","title_i18n": {"ja": "物理的形態", "en": "Physical Format"},},"jpcoar_format_language": {"type": "string","format": "select","enum": [None, 'ja', 'en'],"title": "Language","title_i18n": {"ja": "言語", "en": "Language"}}}}}}
    mapping = {
        'format.@value': ['item_key.jpcoar_format'],
        'format.@attributes.xml:lang': ['item_key.jpcoar_format_language']
    }
    xml = """
            <record>
                <jpcoar:format>折本</jpcoar:format>
            </record>
          """
    res = {}
    metadata = xmltoTestData('jpcoar:format', xml)
    add_format(schema, mapping, res, metadata)
    assert res == {'item_key': [{'jpcoar_format': '折本'}]}

# def add_holdingAgent(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_holdingAgent -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_holdingAgent(app):
    schema = {'item_key': {"type": "object","format": "object","title": "holding_agent_name","properties": {"holding_agent_names": {"type": "array","format": "array","title": "所蔵機関名","items": {"type": "object","format": "object","properties": {"holding_agent_name": {"type": "string","format": "text","title": "所蔵機関名","title_i18n": {"ja": "所蔵機関名","en": "Holding Agent Name"}},"holding_agent_name_language": {"type": "string","format": "select","enum": [None, 'ja', 'en'],"title": "Language","title_i18n": {"ja": "言語", "en": "Language"}}}}},"holding_agent_name_identifier": {"type": "object","format": "object","title": "所蔵機関識別子","properties": {"holding_agent_name_identifier_value": {"type": "string","format": "text","title": "所蔵機関識別子","title_i18n": {"ja": "所蔵機関識別子","en": "Holding Agent Name Identifier"}},"holding_agent_name_identifier_scheme": {"type": "string","format": "select","enum": [None,"kakenhi","ISNI","Ringgold","GRID","ROR","FANO","ISIL","MARC","OCLC"],"title": "所蔵機関識別子スキーマ","title_i18n": {"ja": "所蔵機関識別子スキーマ","en": "Holding Agent Name Identifier Schema"}},"holding_agent_name_identifier_uri": {"type": "string","format": "text","title": "所蔵機関識別子URI","title_i18n": {"ja": "所蔵機関識別子URI","en": "Holding Agent Name Identifier URI"}}}}}}}
    mapping = {
        'holdingAgent.holdingAgentName.@value': ['item_key.holding_agent_names.holding_agent_name'],
        'holdingAgent.holdingAgentName.@attributes.xml:lang': ['item_key.holding_agent_names.holding_agent_name_language'],
        'holdingAgent.holdingAgentNameIdentifier.@value': ['item_key.holding_agent_name_identifier.holding_agent_name_identifier_value'],
        'holdingAgent.holdingAgentNameIdentifier.@attributes.nameIdentifierScheme': ['item_key.holding_agent_name_identifier.holding_agent_name_identifier_scheme'],
        'holdingAgent.holdingAgentNameIdentifier.@attributes.nameIdentifierURI': ['item_key.holding_agent_name_identifier.holding_agent_name_identifier_uri']
    }
    xml = """
            <record>
                <jpcoar:holdingAgent>
                    <jpcoar:holdingAgentNameIdentifier nameIdentifierScheme="ROR">https://ror.org/057zh3y96</jpcoar:holdingAgentNameIdentifier>
                    <jpcoar:holdingAgentName xml:lang="en">The University of Tokyo</jpcoar:holdingAgentName>
                </jpcoar:holdingAgent>
            </record>
          """
    res = {}
    metadata = xmltoTestData('jpcoar:holdingAgent', xml)
    add_holdingAgent(schema, mapping, res, metadata)
    assert res == {'item_key': [{'holding_agent_names': [{'holding_agent_name': 'The University of Tokyo', 'holding_agent_name_language': 'en'}], 'holding_agent_name_identifier': {'holding_agent_name_identifier_value': 'https://ror.org/057zh3y96', 'holding_agent_name_identifier_scheme': 'ROR'}}]}

# def add_datasetSeries(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_datasetSeries -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_datasetSeries(app):
    schema = {'item_key': {'items': {"type": "object","format": "object","properties": {"jpcoar_dataset_series": {"type": ["null", "string"],"format": "select","enum": [None, "True", "False"],"title": "Dataset Series"}}}}}
    mapping = {
        'datasetSeries.@value': ['item_key.jpcoar_dataset_series']
    }
    xml = """
            <record>
                <jpcoar:datasetSeries>True</jpcoar:datasetSeries>
            </record>
          """
    res = {}
    metadata = xmltoTestData('jpcoar:datasetSeries', xml)
    add_datasetSeries(schema, mapping, res, metadata)
    assert res == {'item_key': [{'jpcoar_dataset_series': 'True'}]}

# def add_catalog(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_catalog -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_catalog(app):
    schema = {'item_key': {'items': {"type": "object","format": "object","title": "catalog","properties": {"catalog_contributors": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"contributor_type": {"type": "string","format": "select","enum": ["HostingInstitution"],"currentEnum": ["HostingInstitution"],"title": "Hosting Institution Type","title_i18n": {"ja": "提供機関タイプ","en": "Hosting Institution Type"}},"contributor_names": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"contributor_name": {"type": "string","format": "text","title": "Hosting Institution Name","title_i18n": {"ja": "提供機関名","en": "Hosting Institution Name"}},"contributor_name_language": {"type": ["null", "string"],"format": "select","enum": [None, 'ja', 'en'],"title": "Language","title_i18n": {"ja": "言語","en": "Language"}}}},"title": "Hosting Institution Name"}}},"title": "Hosting Institution"},"catalog_identifiers": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"catalog_identifier": {"type": "string","format": "text","title": "Identifier","title_i18n": {"ja": "識別子", "en": "Identifier"}},"catalog_identifier_type": {"type": ["null", "string"],"format": "select","enum": ["DOI", "HDL", "URI"],"currentEnum": ["DOI", "HDL", "URI"],"title": "Identifier Type","title_i18n": {"ja": "識別子タイプ", "en": "Identifier Type"}}}},"title": "Identifier"},"catalog_titles": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"catalog_title": {"type": "string","format": "text","title": "Title","title_i18n": {"ja": "タイトル", "en": "Title"}},"catalog_title_language": {"type": "string","format": "select","enum": [None, 'ja', 'en', 'ja-Kana'],"title": "Language","title_i18n": {"ja": "言語", "en": "Language"}}}},"title": "Title"},"catalog_descriptions": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"catalog_description": {"type": "string","format": "text","title": "Description","title_i18n": {"ja": "内容記述", "en": "Description"}},"catalog_description_language": {"type": "string","format": "select","enum": [None, 'ja', 'en'],"title": "Language","title_i18n": {"ja": "言語", "en": "Language"}},"catalog_description_type": {"type": "string","format": "select","enum": ["Abstract","Methods","TableOfContents","TechnicalInfo","Other",],"currentEnum": ["Abstract","Methods","TableOfContents","TechnicalInfo","Other",],"title": "Description Type","title_i18n": {"ja": "内容記述タイプ", "en": "Description Type"}}}},"title": "Description"},"catalog_subjects": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"catalog_subject": {"type": "string","format": "text","title": "Subject","title_i18n": {"ja": "主題", "en": "Subject"}},"catalog_subject_language": {"type": "string","format": "select","enum": [None, 'ja', 'en'],"title": "Language","title_i18n": {"ja": "言語", "en": "Language"}},"catalog_subject_uri": {"type": "string","format": "text","title": "Subject URI","title_i18n": {"ja": "主題URI", "en": "Subject URI"}},"catalog_subject_scheme": {"type": "string","format": "select","enum": ["BSH","DDC","e-Rad","LCC","LCSH","MeSH","NDC","NDLC","NDLSH","SciVal","UDC","Other",],"currentEnum": ["BSH","DDC","e-Rad","LCC","LCSH","MeSH","NDC","NDLC","NDLSH","SciVal","UDC","Other",],"title": "Subject Scheme","title_i18n": {"ja": "主題スキーマ", "en": "Subject Scheme"}}}},"title": "Subject"},"catalog_licenses": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"catalog_license": {"type": "string","format": "text","title": "License","title_i18n": {"ja": "ライセンス", "en": "License"}},"catalog_license_language": {"type": "string","format": "select","enum": [None, 'ja', 'en'],"title": "Language","title_i18n": {"ja": "言語", "en": "Language"}},"catalog_license_type": {"type": "string","format": "select","enum": ["file", "metadata", "thumbnail"],"currentEnum": ["file", "metadata", "thumbnail"],"title": "License Type","title_i18n": {"ja": "ライセンスタイプ", "en": "License Type"}},"catalog_license_rdf_resource": {"type": "string","format": "text","title": "RDF Resource","title_i18n": {"ja": "RDFリソース", "en": "RDF Resource"}}}},"title": "License"},"catalog_rights": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"catalog_rights_right": {"type": "string","format": "text","title": "Rights","title_i18n": {"ja": "権利情報", "en": "Rights"}},"catalog_right_language": {"type": "string","format": "select","enum": [None, 'ja', 'en'],"title": "Language","title_i18n": {"ja": "言語", "en": "Language"}},"catalog_right_rdf_resource": {"type": "string","format": "text","title": "RDF Resource","title_i18n": {"ja": "RDFリソース", "en": "RDF Resource"}}}},"title": "Rights"},"catalog_access_rights": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"catalog_access_right": {"type": "string","format": "select","enum": ["embargoed access","metadata only access","restricted access","open access",],"currentEnum": ["embargoed access","metadata only access","restricted access","open access",],"title": "Access Rights","title_i18n": {"ja": "アクセス権", "en": "Access Rights"}},"catalog_access_right_rdf_resource": {"type": "string","format": "text","title": "RDF Resource","title_i18n": {"ja": "RDFリソース", "en": "RDF Resource"}}}},"title": "Access Rights"},"catalog_file": {"type": "object","format": "object","properties": {"catalog_file_uri": {"type": "object","format": "object","properties": {"catalog_file_uri_value": {"type": "string","format": "text","title": "Thumbnail URI","title_i18n": {"ja": "代表画像URI", "en": "Thumbnail URI"},},"catalog_file_object_type": {"type": "string","format": "select","enum": ["thumbnail"],"currentEnum": ["thumbnail"],"title": "Object Type","title_i18n": {"ja": "オブジェクトタイプ", "en": "Object Type"}}}}}}}}}}
    mapping = {
        'catalog.contributor.@attributes.contributorType': ['item_key.catalog_contributors.contributor_type'],
        'catalog.contributor.contributorName.@value': ['item_key.catalog_contributors.contributor_names.contributor_name'],
        'catalog.contributor.contributorName.@attributes.xml:lang': ['item_key.catalog_contributors.contributor_names.contributor_name_language'],
        'catalog.identifier.@value': ['item_key.catalog_identifiers.catalog_identifier'],
        'catalog.identifier.@attributes.identifierType': ['item_key.catalog_identifiers.catalog_identifier_type'],
        'catalog.title.@value': ['item_key.catalog_titles.catalog_title'],
        'catalog.title.@attributes.xml:lang': ['item_key.catalog_titles.catalog_title_language'],
        'catalog.description.@value': ['item_key.catalog_descriptions.catalog_description'],
        'catalog.description.@attributes.xml:lang': ['item_key.catalog_descriptions.catalog_description_language'],
        'catalog.description.@attributes.descriptionType': ['item_key.catalog_descriptions.catalog_description_type'],
        'catalog.subject.@value': ['item_key.catalog_subjects.catalog_subject'],
        'catalog.subject.@attributes.xml:lang': ['item_key.catalog_subjects.catalog_subject_language'],
        'catalog.subject.@attributes.subjectURI': ['item_key.catalog_subjects.catalog_subject_uri'],
        'catalog.subject.@attributes.subjectScheme': ['item_key.catalog_subjects.catalog_subject_scheme'],
        'catalog.license.@value': ['item_key.catalog_licenses.catalog_license'],
        'catalog.license.@attributes.xml:lang': ['item_key.catalog_licenses.catalog_license_language'],
        'catalog.license.@attributes.licenseType': ['item_key.catalog_licenses.catalog_license_type'],
        'catalog.license.@attributes.rdf:resource': ['item_key.catalog_licenses.catalog_license_rdf_resource'],
        'catalog.rights.@value': ['item_key.catalog_rights.catalog_rights_right'],
        'catalog.rights.@attributes.xml:lang': ['item_key.catalog_rights.catalog_right_language'],
        'catalog.rights.@attributes.rdf:resource': ['item_key.catalog_rights.catalog_right_rdf_resource'],
        'catalog.accessRights.@value': ['item_key.catalog_access_rights.catalog_access_right'],
        'catalog.accessRights.@attributes.rdf:resource': ['item_key.catalog_access_rights.catalog_access_right_rdf_resource'],
        'catalog.file.URI.@value': ['item_key.catalog_file.catalog_file_uri.catalog_file_uri_value'],
        'catalog.file.URI.@attributes.objectType': ['item_key.catalog_file.catalog_file_uri.catalog_file_object_type']
    }
    xml = """
            <record>
                <jpcoar:catalog>
                    <jpcoar:contributor contributorType="HostingInstitution">
                        <jpcoar:contributorName xml:lang="ja">東京大学</jpcoar:contributorName>
                        <jpcoar:contributorName xml:lang="en">The University of Tokyo</jpcoar:contributorName>
                    </jpcoar:contributor>
                    <jpcoar:identifier identifierType="URI">https://da.dl.itc.u-tokyo.ac.jp/portal/</jpcoar:identifier>
                    <dc:title xml:lang="ja">東京大学学術資産等アーカイブズポータル</dc:title>
                    <dc:title xml:lang="ja-Kana">トウキョウダイガクガクジュツシサントウアーカイブズポータル</dc:title>
                    <dc:title xml:lang="en">UTokyo Academic Archives Portal</dc:title>
                    <datacite:description xml:lang="ja" descriptionType="Other">東京大学学術資産等アーカイブズポータルは、 「東京大学デジタルアーカイブズ構築事業」により構築されたポータルサイトです。当事業によりデジタル化された資料だけでなく、これまで学内の様々な部局が個別にデジタル化し公開してきたコレクションを、横断的に検索することができます。</datacite:description>
                    <jpcoar:subject subjectScheme="Other">書籍等</jpcoar:subject>
                    <jpcoar:subject xml:lang="ja">人文学</jpcoar:subject>
                    <jpcoar:subject subjectURI="https://da.dl.itc.u-tokyo.ac.jp/">自然史・理工学</jpcoar:subject>
                    <jpcoar:license xml:lang="ja" licenseType="metadata" rdf:resource="https://da.dl.itc.u-tokyo.ac.jp/portal/help/collection">連携コレクション一覧</jpcoar:license>
                    <dc:rights xml:lang="ja">著作権の帰属はコレクションによって異なる</dc:rights>
                    <dcterms:accessRights rdf:resource="http://purl.org/coar/access_right/c_abf2">open access</dcterms:accessRights>
                    <jpcoar:file>
                        <jpcoar:URI objectType="thumbnail">https://xxx.xxx.xxx.xxx/xxx/thumbnail.jpg</jpcoar:URI>
                    </jpcoar:file>
                </jpcoar:catalog>
            </record>
          """
    res = {}
    metadata = xmltoTestData('jpcoar:catalog', xml)
    add_catalog(schema, mapping, res, metadata)
    assert res == {'item_key': [{'catalog_contributors': [{'contributor_type': 'HostingInstitution', 'contributor_names': [{'contributor_name': '東京大学', 'contributor_name_language': 'ja'}, {'contributor_name': 'The University of Tokyo', 'contributor_name_language': 'en'}]}], 'catalog_identifiers': [{'catalog_identifier': 'https://da.dl.itc.u-tokyo.ac.jp/portal/', 'catalog_identifier_type': 'URI'}], 'catalog_titles': [{'catalog_title': '東京大学学術資産等アーカイブズポータル', 'catalog_title_language': 'ja'}, {'catalog_title': 'トウキョウダイガクガクジュツシサントウアーカイブズポータル', 'catalog_title_language': 'ja-Kana'}, {'catalog_title': 'UTokyo Academic Archives Portal', 'catalog_title_language': 'en'}], 'catalog_descriptions': [{'catalog_description': '東京大学学術資産等アーカイブズポータルは、 「東京大学デジタルアーカイブズ構築事業」により構築されたポータルサイトです。当事業によりデジタル化された資料だけでなく、これまで学内の様々な部局が個別にデジタル化し公開してきたコレクションを、横断的に検索することができます。', 'catalog_description_type': 'Other', 'catalog_description_language': 'ja'}], 'catalog_subjects': [{'catalog_subject': '書籍等', 'catalog_subject_scheme': 'Other'}, {'catalog_subject': '人文学', 'catalog_subject_language': 'ja'}, {'catalog_subject': '自然史・理工学', 'catalog_subject_uri': 'https://da.dl.itc.u-tokyo.ac.jp/'}], 'catalog_licenses': [{'catalog_license': '連携コレクション一覧', 'catalog_license_language': 'ja', 'catalog_license_type': 'metadata', 'catalog_license_rdf_resource': 'https://da.dl.itc.u-tokyo.ac.jp/portal/help/collection'}], 'catalog_rights': [{'catalog_rights_right': '著作権の帰属はコレクションによって異なる', 'catalog_right_language': 'ja'}], 'catalog_access_rights': [{'catalog_access_right': 'open access', 'catalog_access_right_rdf_resource': 'http://purl.org/coar/access_right/c_abf2'}], 'catalog_file': {'catalog_file_uri': {'catalog_file_uri_value': 'https://xxx.xxx.xxx.xxx/xxx/thumbnail.jpg', 'catalog_file_object_type': 'thumbnail'}}}]}

# def add_language(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_language(app):
    schema = {'item_key': {'items': {"type": "object","properties": {"subitem_language": {"editAble": True,"type": ["null", "string"],"format": "select","enum": [None, 'jpn', 'eng'],"title": "言語"}}}}}
    mapping = {
        'language.@value': ['item_key.subitem_language']
    }
    xml = """
            <record>
                <dc:language>eng</dc:language>
                <dc:language>jpn</dc:language>
            </record>
          """
    res = {}
    metadata = xmltoTestData('dc:language', xml)
    add_language(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_language': 'eng'}, {'subitem_language': 'jpn'}]}

# def add_version(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_version -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_version(app):
    schema = {'item_key': {"type": "object","title": "バージョン情報","properties": {"subitem_version": {"format": "text","title": "バージョン情報","title_i18n": {"en": "Version", "ja": "バージョン情報"},"type": "string"}}}}
    mapping = {
        'version.@value': ['item_key.subitem_version']
    }
    xml = """
            <record>
                <datacite:version>1.2</datacite:version>
            </record>
          """
    res = {}
    metadata = xmltoTestData('datacite:version', xml)
    add_version(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_version': '1.2'}]}

# def add_version_type(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_version_type -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_version_type(app):
    schema = {'item_key': {"system_prop": True,"type": "object","title": "出版タイプ","properties": {"subitem_version_type": {"type": ["null", "string"],"format": "select","enum": [None, "AO", "SMUR", "AM", "P", "VoR", "CVoR", "EVoR", "NA"],"title": "出版タイプ","title_i18n": {"en": "Version Type", "ja": "出版タイプ"}},"subitem_version_resource": {"format": "text","title": "出版タイプResource","title_i18n": {"en": "Version Type Resource","ja": "出版タイプResource"},"type": "string"}}}}
    mapping = {
        'versiontype.@value': ['item_key.subitem_version_type'],
        'versiontype.@attributes.rdf:resource': ['item_key.subitem_version_resource']
    }
    xml = """
            <record>
                <oaire:version rdf:resource="http://purl.org/coar/version/c_ab4af688f83e57aa">AM</oaire:version>
            </record>
          """
    res = {}
    metadata = xmltoTestData('oaire:version', xml)
    add_version_type(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_version_type': 'AM', 'subitem_version_resource': 'http://purl.org/coar/version/c_ab4af688f83e57aa'}]}
    
# def add_identifier_registration(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_identifier_registration -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_identifier_registration(app):
    schema = {'item_key': {"type": "object","title": "identifier_registration","properties": {"subitem_identifier_reg_text": {"format": "text","title": "ID登録","title_i18n": {"en": "Identifier Registration", "ja": "ID登録"},"type": "string"},"subitem_identifier_reg_type": {"type": ["null", "string"],"format": "select","enum": [None, "JaLC", "Crossref", "DataCite", "PMID【現在不使用】"],"title": "ID登録タイプ","title_i18n": {"en": "Identifier Registration Type","ja": "ID登録タイプ"}}}}}
    mapping = {
        'identifierRegistration.@value': ['item_key.subitem_identifier_reg_text'],
        'identifierRegistration.@attributes.identifierType': ['item_key.subitem_identifier_reg_type']
    }
    xml = """
            <record>
                <jpcoar:identifierRegistration identifierType="JaLC">10.18926/AMO/54590</jpcoar:identifierRegistration>
            </record>
          """
    res = {}
    metadata = xmltoTestData('jpcoar:identifierRegistration', xml)
    add_identifier_registration(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_identifier_reg_text': '10.18926/AMO/54590', 'subitem_identifier_reg_type': 'JaLC'}]}
    
# def add_temporal(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_temporal -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_temporal(app):
    schema = {'item_key': {'items': {"type": "object","properties": {"subitem_temporal_text": {"format": "text","title": "時間的範囲","type": "string"},"subitem_temporal_language": {"editAble": True,"type": ["null", "string"],"format": "select","enum": [None, 'ja', 'en'],"title": "言語"}}}}}
    mapping = {
        'temporal.@value': ['item_key.subitem_temporal_text'],
        'temporal.@attributes.xml:lang': ['item_key.subitem_temporal_language']
    }
    xml = """
            <record>
                <dcterms:temporal xml:lang="ja">奈良時代</dcterms:temporal>
                <dcterms:temporal xml:lang="en">A.D. 1800 - A.D. 1850</dcterms:temporal>
            </record>
          """
    res = {}
    metadata = xmltoTestData('dcterms:temporal', xml)
    add_temporal(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_temporal_text': '奈良時代', 'subitem_temporal_language': 'ja'}, {'subitem_temporal_text': 'A.D. 1800 - A.D. 1850', 'subitem_temporal_language': 'en'}]}

# def add_source_identifier(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_source_identifier -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_source_identifier(app):
    schema = {'item_key': {'items': {"type": "object","properties": {"subitem_source_identifier": {"format": "text","title": "収録物識別子","type": "string"},"subitem_source_identifier_type": {"type": ["null", "string"],"format": "select","enum": [None, "PISSN", "EISSN", "ISSN", "NCID"],"title": "収録物識別子タイプ"}}}}}
    mapping = {
        'sourceIdentifier.@value': ['item_key.subitem_source_identifier'],
        'sourceIdentifier.@attributes.identifierType': ['item_key.subitem_source_identifier_type']
    }
    xml = """
            <record>
                <jpcoar:sourceIdentifier identifierType="PISSN">1234-5678</jpcoar:sourceIdentifier>
                <jpcoar:sourceIdentifier identifierType="NCID">AN12345678</jpcoar:sourceIdentifier>
            </record>
          """
    res = {}
    metadata = xmltoTestData('jpcoar:sourceIdentifier', xml)
    add_source_identifier(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_source_identifier': '1234-5678', 'subitem_source_identifier_type': 'PISSN'}, {'subitem_source_identifier': 'AN12345678', 'subitem_source_identifier_type': 'NCID'}]}
    
# def add_file(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_file -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_file(app):
    schema = {'item_key': {'items': {"system_prop": True,"type": "object","properties": {"url": {"type": "object","format": "object","properties": {"objectType": {"type": ["null", "string"],"format": "select","enum": [None,"abstract","dataset","fulltext","iiif","software","summary","thumbnail","other"],"title": "オブジェクトタイプ"},"label": {"format": "text", "title": "ラベル", "type": "string"},"url": {"format": "text", "title": "本文URL", "type": "string"}},"title": "本文URL"},"format": {"format": "text", "title": "フォーマット", "type": "string"},"filesize": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"value": {"format": "text","title": "サイズ","type": "string"}}},"title": "サイズ"},"version": {"format": "text", "title": "バージョン情報", "type": "string"},"accessrole": {"type": ["null", "string"],"format": "radios","enum": [None, "open_access", "open_date", "open_login", "open_no"],"title": "アクセス"},"displaytype": {"type": ["null", "string"],"format": "select","enum": [None, "detail", "simple", "preview"],"title": "表示形式"},"filename": {"type": ["null", "string"],"format": "text","enum": [],"title": "ファイル名"},"licensefree": {"format": "textarea","title": "自由ライセンス","type": "string"},"licensetype": {"type": ["null", "string"],"format": "select","enum": [],"title": "ライセンス"},"groups": {"type": ["null", "string"],"format": "select","enum": [],"title": "グループ"},"fileDate": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"fileDateType": {"type": ["null", "string"],"format": "select","enum": [None,"Accepted","Available","Collected","Copyrighted","Created","Issued","Submitted","Updated","Valid"],"title": "日付タイプ"},"fileDateValue": {"format": "datetime","title": "日付","type": "string"}}},"title": "日付"},"date": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"dateType": {"type": ["null", "string"],"format": "select","enum": [None, "Available"],"title": "タイプ"},"dateValue": {"format": "datetime","title": "公開日","type": "string"}}},"title": "公開日"}}}}}
    mapping = {
        'file.version.@value': ['item_key.version'],
        'file.mimeType.@value': ['item_key.format'],
        'file.extent.@value': ['item_key.filesize.value'],
        'file.date.@value': ['item_key.fileDate.fileDateValue'],
        'file.date.@attributes.dateType': ['item_key.fileDate.fileDateType'],
        'file.URI.@value': ['item_key.url.url'],
        'file.URI.@attributes.objectType': ['item_key.url.objectType'],
        'file.URI.@attributes.label': ['item_key.url.label']
    }
    xml = """
            <record>
                <jpcoar:file>
                    <jpcoar:URI objectType="fulltext" label="70_5_331.pdf">
                        http://ousar.lib.okayama-u.ac.jp/jpcoar:files/public/5/54590/20161108092537681027/70_5_331.pdf
                    </jpcoar:URI>
                    <jpcoar:mimeType>application/pdf</jpcoar:mimeType>
                    <jpcoar:extent>3MB</jpcoar:extent>
                    <jpcoar:extent>15 pages</jpcoar:extent>
                    <datacite:date dateType="Issued">2015-10-01</datacite:date>
                </jpcoar:file>
                <jpcoar:file>
                    <jpcoar:URI objectType="dataset" label="supplemental data">
                        http://xxx.xxx.xxx.xxx/xxx/researchdata.zip
                    </jpcoar:URI>
                    <jpcoar:mimeType>application/zip</jpcoar:mimeType>
                    <jpcoar:extent>3MB</jpcoar:extent>
                    <datacite:date dateType="Created">2016-01-01</datacite:date>
                    <datacite:version>1.2</datacite:version>
                </jpcoar:file>
            </record>
          """
    res = {}
    metadata = xmltoTestData('jpcoar:file', xml)
    add_file(schema, mapping, res, metadata)
    assert res == {'item_key': [{'url': {'url': 'http://ousar.lib.okayama-u.ac.jp/jpcoar:files/public/5/54590/20161108092537681027/70_5_331.pdf', 'label': '70_5_331.pdf', 'objectType': 'fulltext'}, 'format': 'application/pdf', 'filesize': [{'value': '3MB'}, {'value': '15 pages'}], 'fileDate': [{'fileDateValue': '2015-10-01', 'fileDateType': 'Issued'}]}, {'url': {'url': 'http://xxx.xxx.xxx.xxx/xxx/researchdata.zip', 'label': 'supplemental data', 'objectType': 'dataset'}, 'format': 'application/zip', 'filesize': [{'value': '3MB'}], 'fileDate': [{'fileDateValue': '2016-01-01', 'fileDateType': 'Created'}], 'version': '1.2'}]}

# def add_identifier(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_identifier -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_identifier(app):
    schema = {'item_key': {'items': {"type": "object","properties": {"subitem_identifier_uri": {"format": "text","title": "識別子","type": "string"},"subitem_identifier_type": {"type": ["null", "string"],"format": "select","enum": [None, "DOI", "HDL", "URI"],"title": "識別子タイプ"}}}}}
    mapping = {
        'identifier.@value': ['item_key.subitem_identifier_uri'],
        'identifier.@attributes.identifierType': ['item_key.subitem_identifier_type']
    }
    xml = """
            <record>
                <jpcoar:identifier identifierType="HDL">http://hdl.handle.net/2115/64495</jpcoar:identifier>
            </record>
          """
    res = {}
    metadata = xmltoTestData('jpcoar:identifier', xml)
    add_identifier(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_identifier_uri': 'http://hdl.handle.net/2115/64495', 'subitem_identifier_type': 'HDL'}]}

# def add_source_title(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_source_title -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_source_title(app):
    schema = {'item_key': {'items': {"type": "object","properties": {"subitem_source_title": {"format": "text","title": "収録物名","type": "string"},"subitem_source_title_language": {"editAble": True,"type": ["null", "string"],"format": "select","enum": [None, 'ja', 'en'],"title": "言語"}}}}}
    mapping = {
        'sourceTitle.@value': ['item_key.subitem_source_title'],
        'sourceTitle.@attributes.xml:lang': ['item_key.subitem_source_title_language']
    }
    xml = """
            <record>
                <jpcoar:sourceTitle xml:lang="ja">看護総合科学研究会誌</jpcoar:sourceTitle>
                <jpcoar:sourceTitle xml:lang="en">Journal of Comprehensive Nursing Research</jpcoar:sourceTitle>
            </record>
          """
    res = {}
    metadata = xmltoTestData('jpcoar:sourceTitle', xml)
    add_source_title(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_source_title': '看護総合科学研究会誌', 'subitem_source_title_language': 'ja'}, {'subitem_source_title': 'Journal of Comprehensive Nursing Research', 'subitem_source_title_language': 'en'}]}
    
# def add_volume(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_volume -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_volume(app):
    schema = {'item_key': {'items': {"type": "object","title": "巻","properties": {"subitem_volume": {"format": "text","title": "巻","title_i18n": {"en": "Volume", "ja": "巻"},"type": "string"}}}}}
    mapping = {
        'volume.@value': ['item_key.subitem_volume']
    }
    xml = """
            <record>
                <jpcoar:volume>1</jpcoar:volume>
            </record>
          """
    res = {}
    metadata = xmltoTestData('jpcoar:volume', xml)
    add_volume(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_volume': '1'}]}
    
# def add_issue(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_issue -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_issue(app):
    schema = {'item_key': {'items': {"type": "object","title": "号","properties": {"subitem_issue": {"format": "text","title": "号","title_i18n": {"en": "Issue", "ja": "号"},"type": "string"}}}}}
    mapping = {
        'issue.@value': ['item_key.subitem_issue']
    }
    xml = """
            <record>
                <jpcoar:issue>1</jpcoar:issue>
            </record>
          """
    res = {}
    metadata = xmltoTestData('jpcoar:issue', xml)
    add_issue(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_issue': '1'}]}

# def add_num_page(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_num_page -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_num_page(app):
    schema = {'item_key': {'items': {"type": "object","title": "ページ数","properties": {"subitem_number_of_pages": {"format": "text","title": "ページ数","title_i18n": {"ja": "ページ数", "en": "Number of Pages"},"type": "string"}}}}}
    mapping = {
        'numPages.@value': ['item_key.subitem_number_of_pages']
    }
    xml = """
            <record>
                <jpcoar:numPages>12</jpcoar:numPages>
            </record>
          """
    res = {}
    metadata = xmltoTestData('jpcoar:numPages', xml)
    add_num_page(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_number_of_pages': '12'}]}

# def add_page_start(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_page_start -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_page_start(app):
    schema = {'item_key': {'items': {"type": "object","title": "開始ページ","properties": {"subitem_start_page": {"format": "text","title": "開始ページ","title_i18n": {"en": "Start Page", "ja": "開始ページ"},"type": "string"}}}}}
    mapping = {
        'pageStart.@value': ['item_key.subitem_start_page']
    }
    xml = """
            <record>
                <jpcoar:pageStart>1</jpcoar:pageStart>
            </record>
          """
    res = {}
    metadata = xmltoTestData('jpcoar:pageStart', xml)
    add_page_start(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_start_page': '1'}]}

# def add_page_end(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_page_end -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_page_end(app):
    schema = {'item_key': {'items': {"type": "object","title": "終了ページ","properties": {"subitem_end_page": {"format": "text","title": "終了ページ","title_i18n": {"en": "End Page", "ja": "終了ページ"},"type": "string"}}}}}
    mapping = {
        'pageEnd.@value': ['item_key.subitem_end_page']
    }
    xml = """
            <record>
                <jpcoar:pageEnd>12</jpcoar:pageEnd>
            </record>
          """
    res = {}
    metadata = xmltoTestData('jpcoar:pageEnd', xml)
    add_page_end(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_end_page': '12'}]}
    
# def add_dissertation_number(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_dissertation_number -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_dissertation_number(app):
    schema = {'item_key': {"type": "object","title": "dissertation_number","properties": {"subitem_dissertationnumber": {"format": "text","title": "学位授与番号","title_i18n": {"en": "Dissertation Number", "ja": "学位授与番号"},"type": "string"}}}}
    mapping = {
        'dissertationNumber.@value': ['item_key.subitem_dissertationnumber']
    }
    xml = """
            <record>
                <dcndl:dissertationNumber>甲第5384号</dcndl:dissertationNumber>
            </record>
          """
    res = {}
    metadata = xmltoTestData('dcndl:dissertationNumber', xml)
    add_dissertation_number(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_dissertationnumber': '甲第5384号'}]}

# def add_date_granted(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_date_granted -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_date_granted(app):
    schema = {'item_key': {"type": "object","title": "学位授与年月日","properties": {"subitem_dategranted": {"format": "datetime","title": "学位授与年月日","title_i18n": {"en": "Date Granted", "ja": "学位授与年月日"},"type": "string"}}}}
    mapping = {
        'dateGranted.@value': ['item_key.subitem_dategranted']
    }
    xml = """
            <record>
                <dcndl:dateGranted>2016-03-25</dcndl:dateGranted>
            </record>
          """
    res = {}
    metadata = xmltoTestData('dcndl:dateGranted', xml)
    add_date_granted(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_dategranted': '2016-03-25'}]}
    
# def add_conference(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_conference -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_conference(app):
    schema = {'item_key': {'items': {"type": "object","properties": {"subitem_conference_names": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"subitem_conference_name_language": {"type": ["null", "string"],"format": "select","enum": [None, 'ja', 'en'],"title": "言語"},"subitem_conference_name": {"format": "text","title": "会議名","type": "string"}}},"title": "会議名"},"subitem_conference_sequence": {"format": "text","title": "回次","type": "string"},"subitem_conference_sponsors": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"subitem_conference_sponsor_language": {"type": ["null", "string"],"format": "select","enum": [None, 'ja', 'en'],"title": "言語"},"subitem_conference_sponsor": {"format": "text","title": "主催機関","type": "string"}}},"title": "主催機関"},"subitem_conference_date": {"type": "object","format": "object","properties": {"subitem_conference_start_year": {"format": "text","title": "開始年","type": "string"},"subitem_conference_start_month": {"format": "text","title": "開始月","type": "string"},"subitem_conference_start_day": {"format": "text","title": "開始日","type": "string"},"subitem_conference_end_year": {"format": "text","title": "終了年","type": "string"},"subitem_conference_end_month": {"format": "text","title": "終了月","type": "string"},"subitem_conference_end_day": {"format": "text","title": "終了日","type": "string"},"subitem_conference_period": {"format": "text","title": "開催期間","type": "string"},"subitem_conference_date_language": {"type": ["null", "string"],"format": "select","enum": [None, 'ja', 'en'],"title": "言語"}},"title": "開催期間"},"subitem_conference_venues": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"subitem_conference_venue_language": {"type": ["null", "string"],"format": "select","enum": [None, 'ja', 'en'],"title": "言語"},"subitem_conference_venue": {"format": "text","title": "開催会場","type": "string"}}},"title": "開催会場"},"subitem_conference_places": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"subitem_conference_place_language": {"type": ["null", "string"],"format": "select","enum": [None, 'ja', 'en'],"title": "言語"},"subitem_conference_place": {"format": "text","title": "開催地","type": "string"}}},"title": "開催地"},"subitem_conference_country": {"type": ["null", "string"],"format": "select","enum": [None,"JPN","ABW","AFG"],"title": "開催国"}}}}}
    mapping = {
        'conference.conferenceCountry.@value': ['item_key.subitem_conference_country'],
        'conference.conferenceSequence.@value': ['item_key.subitem_conference_sequence'],
        'conference.conferencePlace.@value': ['item_key.subitem_conference_places.subitem_conference_place'],
        'conference.conferencePlace.@attributes.xml:lang': ['item_key.subitem_conference_places.subitem_conference_place_language'],
        'conference.conferenceSponsor.@value': ['item_key.subitem_conference_sponsors.subitem_conference_sponsor'],
        'conference.conferenceSponsor.@attributes.xml:lang': ['item_key.subitem_conference_sponsors.subitem_conference_sponsor_language'],
        'conference.conferenceName.@value': ['item_key.subitem_conference_names.subitem_conference_name'],
        'conference.conferenceName.@attributes.xml:lang': ['item_key.subitem_conference_names.subitem_conference_name_language'],
        'conference.conferenceDate.@value': ['item_key.subitem_conference_date.subitem_conference_period'],
        'conference.conferenceDate.@attributes.startYear': ['item_key.subitem_conference_date.subitem_conference_start_year'],
        'conference.conferenceDate.@attributes.startMonth': ['item_key.subitem_conference_date.subitem_conference_start_month'],
        'conference.conferenceDate.@attributes.startDay': ['item_key.subitem_conference_date.subitem_conference_start_day'],
        'conference.conferenceDate.@attributes.endYear': ['item_key.subitem_conference_date.subitem_conference_end_year'],
        'conference.conferenceDate.@attributes.endMonth': ['item_key.subitem_conference_date.subitem_conference_end_month'],
        'conference.conferenceDate.@attributes.endDay': ['item_key.subitem_conference_date.subitem_conference_end_day'],
        'conference.conferenceDate.@attributes.xml:lang': ['item_key.subitem_conference_date.subitem_conference_date_language'],
        'conference.conferenceVenue.@value': ['item_key.subitem_conference_venues.subitem_conference_venue'],
        'conference.conferenceVenue.@attributes.xml:lang': ['item_key.subitem_conference_venues.subitem_conference_venue_language']
    }
    xml = """
            <record>
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
            </record>
          """
    res = {}
    metadata = xmltoTestData('jpcoar:conference', xml)
    add_conference(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_conference_names': [{'subitem_conference_name': 'RDA Seventh Plenary Meeting', 'subitem_conference_name_language': 'en'}], 'subitem_conference_sequence': '7', 'subitem_conference_sponsors': [{'subitem_conference_sponsor': 'The Research Data Alliance', 'subitem_conference_sponsor_language': 'en'}], 'subitem_conference_date': {'subitem_conference_period': 'February 29th to March 4th, 2016', 'subitem_conference_date_language': 'en', 'subitem_conference_start_year': '2016', 'subitem_conference_start_month': '02', 'subitem_conference_start_day': '29', 'subitem_conference_end_year': '2016', 'subitem_conference_end_month': '03', 'subitem_conference_end_day': '04'}, 'subitem_conference_venues': [{'subitem_conference_venue': 'Hitotsubashi Hall', 'subitem_conference_venue_language': 'en'}], 'subitem_conference_places': [{'subitem_conference_place': 'Tokyo', 'subitem_conference_place_language': 'en'}], 'subitem_conference_country': 'JPN'}]}
    
# def add_degree_grantor(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_degree_grantor -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_degree_grantor(app):
    schema = {'item_key': {'items': {"type": "object","properties": {"subitem_degreegrantor": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"subitem_degreegrantor_language": {"editAble": True,"type": ["null", "string"],"format": "select","enum": [None, 'ja', 'en'],"title": "言語"},"subitem_degreegrantor_name": {"format": "text","title": "学位授与機関名","type": "string"}}},"title": "学位授与機関名"},"subitem_degreegrantor_identifier": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"subitem_degreegrantor_identifier_name": {"format": "text","title": "学位授与機関識別子","type": "string"},"subitem_degreegrantor_identifier_scheme": {"type": ["null", "string"],"format": "select","enum": [None, "kakenhi"],"title": "学位授与機関識別子Scheme"}}},"title": "学位授与機関識別子"}}}}}
    mapping = {
        'degreeGrantor.nameIdentifier.@value': ['item_key.subitem_degreegrantor_identifier.subitem_degreegrantor_identifier_name'],
        'degreeGrantor.nameIdentifier.@attributes.nameIdentifierScheme': ['item_key.subitem_degreegrantor_identifier.subitem_degreegrantor_identifier_scheme'],
        'degreeGrantor.degreeGrantorName.@value': ['item_key.subitem_degreegrantor.subitem_degreegrantor_name'],
        'degreeGrantor.degreeGrantorName.@attributes.xml:lang': ['item_key.subitem_degreegrantor.subitem_degreegrantor_language']
    }
    xml = """
            <record>
                <jpcoar:degreeGrantor>
                    <jpcoar:nameIdentifier nameIdentifierScheme="kakenhi">32653</jpcoar:nameIdentifier>
                    <jpcoar:degreeGrantorName xml:lang="ja">東京女子医科大学</jpcoar:degreeGrantorName>
                </jpcoar:degreeGrantor>
                <jpcoar:degreeGrantor>
                    <jpcoar:nameIdentifier nameIdentifierScheme="kakenhi">32689</jpcoar:nameIdentifier>
                    <jpcoar:degreeGrantorName xml:lang="ja">早稲田大学</jpcoar:degreeGrantorName>
                </jpcoar:degreeGrantor>
            </record>
          """
    res = {}
    metadata = xmltoTestData('jpcoar:degreeGrantor', xml)
    add_degree_grantor(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_degreegrantor_identifier': [{'subitem_degreegrantor_identifier_name': '32653', 'subitem_degreegrantor_identifier_scheme': 'kakenhi'}], 'subitem_degreegrantor': [{'subitem_degreegrantor_name': '東京女子医科大学', 'subitem_degreegrantor_language': 'ja'}]},{'subitem_degreegrantor_identifier': [{'subitem_degreegrantor_identifier_name': '32689', 'subitem_degreegrantor_identifier_scheme': 'kakenhi'}], 'subitem_degreegrantor': [{'subitem_degreegrantor_name': '早稲田大学', 'subitem_degreegrantor_language': 'ja'}]}]}
    
# def add_degree_name(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_degree_name -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_degree_name(app):
    schema = {'item_key': {'items': {"type": "object","title": "学位名","properties": {"subitem_degreename": {"format": "text","title": "学位名","type": "string",},"subitem_degreename_language": {"editAble": True,"type": ["null", "string"],"format": "select","enum": [None, 'ja', 'en'],"title": "言語"}}}}}
    mapping = {
        'degreeName.@value': ['item_key.subitem_degreename'],
        'degreeName.@attributes.xml:lang': ['item_key.subitem_degreename_language']
    }
    xml = """
            <record>
                <dcndl:degreeName xml:lang="en">Doctor of Philosophy in Letters</dcndl:degreeName>
                <dcndl:degreeName xml:lang="ja">博士（文学）</dcndl:degreeName>
            </record>
          """
    res = {}
    metadata = xmltoTestData('dcndl:degreeName', xml)
    add_degree_name(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_degreename': 'Doctor of Philosophy in Letters', 'subitem_degreename_language': 'en'}, {'subitem_degreename': '博士（文学）', 'subitem_degreename_language': 'ja'}]}
    
# def add_funding_reference(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_funding_reference -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_funding_reference(app):
    schema = {'item_key': {'items': {"type": "object","properties": {"subitem_funder_identifiers": {"type": "object","format": "object","properties": {"subitem_funder_identifier_type": {"type": ["null", "string"],"format": "select","enum": [None,"Crossref Funder","e-Rad_funder","GRID","ISNI","ROR","Other"],"title": "識別子タイプ"},"subitem_funder_identifier": {"format": "text","title": "助成機関識別子","type": "string"}, "subitem_funder_identifier_type_uri": {"format": "text","title": "識別子タイプURI","type": "string"}},"title": "助成機関識別子"},"subitem_funder_names": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"subitem_funder_name_language": {"type": ["null", "string"],"format": "select","enum": [None, 'ja', 'en'],"title": "言語"},"subitem_funder_name": {"format": "text","title": "助成機関名","type": "string"}}},"title": "助成機関名"},"subitem_funding_stream_identifiers": {"type": "object","format": "object","properties": {"subitem_funding_stream_identifier_type": {"type": ["null", "string"],"format": "select","enum": ["Crossref Funder", "JGN_fundingStream"],"title": "プログラム情報識別子タイプ"},"subitem_funding_stream_identifier_type_uri": {"format": "text","title": "プログラム情報識別子タイプURI","type": "string"},"subitem_funding_stream_identifier": {"format": "text","title": "プログラム情報識別子","type": "string"}},"title": "プログラム情報識別子"},"subitem_funding_streams": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"subitem_funding_stream_language": {"type": ["null", "string"],"format": "select","enum": [None, 'ja', 'en'],"title": "言語"},"subitem_funding_stream": {"format": "text","title": "プログラム情報","type": "string"}}},"title": "プログラム情報"},"subitem_award_numbers": {"type": "object","format": "object","properties": {"subitem_award_uri": {"format": "text","type": "string","title": "研究課題番号URI"},"subitem_award_number": {"format": "text","title": "研究課題番号","type": "string"},"subitem_award_number_type": {"type": ["null", "string"],"format": "select","enum": [None, "JGN"],"title": "研究課題番号タイプ"}},"title": "研究課題番号"},"subitem_award_titles": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"subitem_award_title_language": {"type": ["null", "string"],"format": "select","enum": [None, 'ja', 'en'],"title": "言語"},"subitem_award_title": {"format": "text","title": "研究課題名","type": "string"}}},"title": "研究課題名"}}}}}
    mapping = {
        'fundingReference.funderName.@value': ['item_key.subitem_funder_names.subitem_funder_name'],
        'fundingReference.funderName.@attributes.xml:lang': ['item_key.subitem_funder_names.subitem_funder_name_language'],
        'fundingReference.funderIdentifier.@value': ['item_key.subitem_funder_identifiers.subitem_funder_identifier'],
        'fundingReference.funderIdentifier.@attributes.funderIdentifierType': ['item_key.subitem_funder_identifiers.subitem_funder_identifier_type'],
        'fundingReference.funderIdentifier.@attributes.funderIdentifierTypeURI': ['item_key.subitem_funder_identifiers.subitem_funder_identifier_type_uri'],
        'fundingReference.fundingStreamIdentifier.@value': ['item_key.subitem_funding_stream_identifiers.subitem_funding_stream_identifier'],
        'fundingReference.fundingStreamIdentifier.@attributes.fundingStreamIdentifierType': ['item_key.subitem_funding_stream_identifiers.subitem_funding_stream_identifier_type'],
        'fundingReference.fundingStreamIdentifier.@attributes.fundingStreamIdentifierTypeURI': ['item_key.subitem_funding_stream_identifiers.subitem_funding_stream_identifier_type_uri'],
        'fundingReference.fundingStream.@value': ['item_key.subitem_funding_streams.subitem_funding_stream'],
        'fundingReference.fundingStream.@attributes.xml:lang': ['item_key.subitem_funding_streams.subitem_funding_stream_language'],
        'fundingReference.awardNumber.@value': ['item_key.subitem_award_numbers.subitem_award_number'],
        'fundingReference.awardNumber.@attributes.awardURI': ['item_key.subitem_award_numbers.subitem_award_uri'],
        'fundingReference.awardNumber.@attributes.awardNumberType': ['item_key.subitem_award_numbers.subitem_award_number_type'],
        'fundingReference.awardTitle.@value': ['item_key.subitem_award_titles.subitem_award_title'],
        'fundingReference.awardTitle.@attributes.xml:lang': ['item_key.subitem_award_titles.subitem_award_title_language']
    }
    xml = """
            <record>
                <jpcoar:fundingReference>
                    <jpcoar:funderIdentifier funderIdentifierType ="e-Rad_funder" funderIdentifierTypeURI="https://www.e-rad.go.jp/datasets/files/haibunkikan.csv">
                    1020
                    </jpcoar:funderIdentifier>
                    <jpcoar:funderName xml:lang="ja">
                    国立研究開発法人科学技術振興機構（JST）
                    </jpcoar:funderName>
                    <jpcoar:funderName xml:lang="en">
                    Japan Science and Technology Agency（JST）
                    </jpcoar:funderName>
                    <jpcoar:fundingStreamIdentifier fundingStreamIdentifierType="JGN_fundingStream">
                    MJBF
                    </jpcoar:fundingStreamIdentifier>
                    <jpcoar:fundingStream xml:lang="en">
                    Belmont Forum
                    </jpcoar:fundingStream>
                    <jpcoar:awardNumber awardURI="https://doi.org/10.52926/JPMJBF1801" awardNumberType="JGN">
                    JPMJBF1801
                    </jpcoar:awardNumber>
                    <jpcoar:awardTitle xml:lang="ja">
                    実践としての変革(Transformation):気候変動の影響を受けやすい環境下での持続可能性に向けた公平かつ超学際的な方法論の開発(TAPESTRY)
                    </jpcoar:awardTitle>
                </jpcoar:fundingReference>
            </record>
          """
    res = {}
    metadata = xmltoTestData('jpcoar:fundingReference', xml)
    add_funding_reference(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_funder_identifiers': {'subitem_funder_identifier': '1020', 'subitem_funder_identifier_type': 'e-Rad_funder', 'subitem_funder_identifier_type_uri': 'https://www.e-rad.go.jp/datasets/files/haibunkikan.csv'}, 'subitem_funder_names': [{'subitem_funder_name': '国立研究開発法人科学技術振興機構（JST）', 'subitem_funder_name_language': 'ja'}, {'subitem_funder_name': 'Japan Science and Technology Agency（JST）', 'subitem_funder_name_language': 'en'}], 'subitem_funding_stream_identifiers': {'subitem_funding_stream_identifier': 'MJBF', 'subitem_funding_stream_identifier_type': 'JGN_fundingStream'}, 'subitem_funding_streams': [{'subitem_funding_stream': 'Belmont Forum', 'subitem_funding_stream_language': 'en'}], 'subitem_award_numbers': {'subitem_award_number': 'JPMJBF1801', 'subitem_award_uri': 'https://doi.org/10.52926/JPMJBF1801', 'subitem_award_number_type': 'JGN'}, 'subitem_award_titles': [{'subitem_award_title': '実践としての変革(Transformation):気候変動の影響を受けやすい環境下での持続可能性に向けた公平かつ超学際的な方法論の開発(TAPESTRY)', 'subitem_award_title_language': 'ja'}]}]}

# def add_geo_location(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_geo_location -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_geo_location(app):
    schema = {'item_key': {'items': {"type": "object","properties": {"subitem_geolocation_point": {"title": "位置情報（点）","type": "object","format": "object","properties": {"subitem_point_longitude": {"format": "text","title": "経度","type": "string"},"subitem_point_latitude": {"format": "text","title": "緯度","type": "string"}}},"subitem_geolocation_box": {"title": "位置情報（空間）","type": "object","format": "object","properties": {"subitem_west_longitude": {"format": "text","title": "西部経度","type": "string"},"subitem_east_longitude": {"format": "text","title": "東部経度","type": "string"},"subitem_south_latitude": {"format": "text","title": "南部緯度","type": "string"},"subitem_north_latitude": {"format": "text","title": "北部緯度","type": "string"}}},"subitem_geolocation_place": {"format": "array","title": "位置情報（自由記述）","type": "array","items": {"format": "object","type": "object","properties": {"subitem_geolocation_place_text": {"format": "text","title": "位置情報（自由記述）","type": "string"}}}}}}}}
    mapping = {
        'geoLocation.geoLocationPoint.pointLongitude.@value': ['item_key.subitem_geolocation_point.subitem_point_longitude'],
        'geoLocation.geoLocationPoint.pointLatitude.@value': ['item_key.subitem_geolocation_point.subitem_point_latitude'],
        'geoLocation.geoLocationPlace.@value': ['item_key.subitem_geolocation_place.subitem_geolocation_place_text'],
        'geoLocation.geoLocationBox.westBoundLongitude.@value': ['item_key.subitem_geolocation_box.subitem_west_longitude'],
        'geoLocation.geoLocationBox.southBoundLatitude.@value': ['item_key.subitem_geolocation_box.subitem_south_latitude'],
        'geoLocation.geoLocationBox.northBoundLatitude.@value': ['item_key.subitem_geolocation_box.subitem_north_latitude'],
        'geoLocation.geoLocationBox.eastBoundLongitude.@value': ['item_key.subitem_geolocation_box.subitem_east_longitude']
    }
    xml = """
            <record>
                <datacite:geoLocation>
                    <datacite:geoLocationPoint>
                        <datacite:pointLongitude>-180</datacite:pointLongitude>
                        <datacite:pointLatitude>80</datacite:pointLatitude>
                    </datacite:geoLocationPoint>
                </datacite:geoLocation>
                <datacite:geoLocation>
                    <datacite:geoLocationBox>
                        <datacite:westBoundLongitude>-71.032</datacite:westBoundLongitude>
                        <datacite:eastBoundLongitude>-68.211</datacite:eastBoundLongitude>
                        <datacite:southBoundLatitude>41.090</datacite:southBoundLatitude>
                        <datacite:northBoundLatitude>42.893</datacite:northBoundLatitude>
                    </datacite:geoLocationBox>
                </datacite:geoLocation>
                <datacite:geoLocation>
                    <datacite:geoLocationPlace>Disko Bay</datacite:geoLocationPlace>
                </datacite:geoLocation>
            </record>
          """
    res = {}
    metadata = xmltoTestData('datacite:geoLocation', xml)
    add_geo_location(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_geolocation_point': {'subitem_point_longitude': '-180', 'subitem_point_latitude': '80'}}, {'subitem_geolocation_box': {'subitem_west_longitude': '-71.032', 'subitem_south_latitude': '41.090', 'subitem_north_latitude': '42.893', 'subitem_east_longitude': '-68.211'}}, {'subitem_geolocation_place': [{'subitem_geolocation_place_text': 'Disko Bay'}]}]}
    

# def add_relation(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_relation -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_relation(app):
    schema = {'item_key': {'items': {"type": "object","properties": {"subitem_relation_name": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"subitem_relation_name_language": {"editAble": True,"type": ["null", "string"],"format": "select","enum": [None, 'ja', 'en'],"title": "言語"},"subitem_relation_name_text": {"format": "text","title": "関連名称","type": "string"}}},"title": "関連名称"},"subitem_relation_type": {"type": ["null", "string"],"format": "select","enum": [None,"isVersionOf","hasVersion","isPartOf","hasPart","isReferencedBy","references","isFormatOf","hasFormat","isReplacedBy","replaces","isRequiredBy","requires","isSupplementedBy","isSupplementTo","isIdenticalTo","isDerivedFrom","isSourceOf","isCitedBy","Cites","inSeries"],"title": "関連タイプ"},"subitem_relation_type_id": {"type": "object","format": "object","properties": {"subitem_relation_type_id_text": {"format": "text","title": "関連識別子","type": "string"},"subitem_relation_type_select": {"type": ["null", "string"],"format": "select","enum": [None,"ARK","arXiv","DOI","HDL","ICHUSHI","ISBN","J-GLOBAL","Local","PISSN","EISSN","ISSN","NAID","NCID","PMID","PURL","SCOPUS","URI","WOS","CRID"],"title": "識別子タイプ"}},"title": "関連識別子"}}}}}
    mapping = {
        'relation.@attributes.relationType': ['item_key.subitem_relation_type'],
        'relation.relatedTitle.@value': ['item_key.subitem_relation_name.subitem_relation_name_text'],
        'relation.relatedTitle.@attributes.xml:lang': ['item_key.subitem_relation_name.subitem_relation_name_language'],
        'relation.relatedIdentifier.@value': ['item_key.subitem_relation_type_id.subitem_relation_type_id_text'],
        'relation.relatedIdentifier.@attributes.identifierType': ['item_key.subitem_relation_type_id.subitem_relation_type_select']
    }
    xml = """
            <record>
                <jpcoar:relation relationType="isVersionOf">
                    <jpcoar:relatedIdentifier identifierType="DOI">
                        https://doi.org/10.1371/journal.pone.0170224
                    </jpcoar:relatedIdentifier>
                </jpcoar:relation>
                <jpcoar:relation relationType="isSupplementTo">
                    <jpcoar:relatedIdentifier identifierType="HDL">https://hdl.handle.net/1912/6236</jpcoar:relatedIdentifier>
                </jpcoar:relation>
                <jpcoar:relation relationType="isFormatOf">
                    <jpcoar:relatedIdentifier identifierType="NCID">BC03765035</jpcoar:relatedIdentifier>
                    <jpcoar:relatedTitle xml:lang="ja">一辭題開方式省過乗明平方以下定式有無法</jpcoar:relatedTitle>
                </jpcoar:relation>
            </record>
          """
    res = {}
    metadata = xmltoTestData('jpcoar:relation', xml)
    add_relation(schema, mapping, res, metadata)
    assert res == {'item_key': [{'subitem_relation_type': 'isVersionOf', 'subitem_relation_type_id': {'subitem_relation_type_id_text': 'https://doi.org/10.1371/journal.pone.0170224', 'subitem_relation_type_select': 'DOI'}}, {'subitem_relation_type': 'isSupplementTo', 'subitem_relation_type_id': {'subitem_relation_type_id_text': 'https://hdl.handle.net/1912/6236', 'subitem_relation_type_select': 'HDL'}}, {'subitem_relation_type': 'isFormatOf', 'subitem_relation_type_id': {'subitem_relation_type_id_text': 'BC03765035', 'subitem_relation_type_select': 'NCID'}, 'subitem_relation_name': [{'subitem_relation_name_text': '一辭題開方式省過乗明平方以下定式有無法', 'subitem_relation_name_language': 'ja'}]}]}
    
# def add_rights_holder(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_rights_holder -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_rights_holder(app):
    schema = {'item_key': {'items': {"system_prop": True,"type": "object","properties": {"nameIdentifiers": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"nameIdentifierScheme": {"type": ["null", "string"],"format": "select","title": "権利者識別子Scheme"},"nameIdentifier": {"format": "text","title": "権利者識別子","type": "string"},"nameIdentifierURI": {"format": "text","title": "権利者識別子URI","type": "string"}}},"title": "権利者識別子"},"rightHolderNames": {"type": "array","format": "array","items": {"type": "object","format": "object","properties": {"rightHolderLanguage": {"editAble": True,"type": ["null", "string"],"format": "select","enum": [None, 'ja', 'en'],"title": "言語"},"rightHolderName": {"format": "text","title": "権利者名","type": "string"}}},"title": "権利者名"}}}}}
    mapping = {
        'rightsHolder.rightsHolderName.@value': ['item_key.rightHolderNames.rightHolderName'],
        'rightsHolder.rightsHolderName.@attributes.xml:lang': ['item_key.rightHolderNames.rightHolderLanguage'],
        'rightsHolder.nameIdentifier.@value': ['item_key.nameIdentifiers.nameIdentifier'],
        'rightsHolder.nameIdentifier.@attributes.nameIdentifierURI': ['item_key.nameIdentifiers.nameIdentifierURI'],
        'rightsHolder.nameIdentifier.@attributes.nameIdentifierScheme': ['item_key.nameIdentifiers.nameIdentifierScheme']
    }
    xml = """
            <record>
                <jpcoar:rightsHolder> 
                    <jpcoar:nameIdentifier nameIdentifierScheme="ISNI" 
                        nameIdentifierURI="http://isni.org/isni/00000004043815">
                        0000000404381592
                    </jpcoar:nameIdentifier> 
                    <jpcoar:rightsHolderName xml:lang="en">American Physical Society</jpcoar:rightsHolderName>
                </jpcoar:rightsHolder>
            </record>
          """
    res = {}
    metadata = xmltoTestData('jpcoar:rightsHolder', xml)
    add_rights_holder(schema, mapping, res, metadata)
    assert res == {'item_key': [{'rightHolderNames': [{'rightHolderName': 'American Physical Society', 'rightHolderLanguage': 'en'}], 'nameIdentifiers': [{'nameIdentifier': '0000000404381592', 'nameIdentifierURI': 'http://isni.org/isni/00000004043815', 'nameIdentifierScheme': 'ISNI'}]}]}

# def add_resource_type(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_resource_type -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_resource_type(mapper_jpcoar):
    schema = {'item_key': {"system_prop": True,"type": "object","properties": {"resourceuri": {"format": "text","title": "資源タイプ識別子","title_i18n": {"en": "Resource Type Identifier", "ja": "資源タイプ識別子"},"type": "string"},"resourcetype": {"type": ["null", "string"],"format": "select","enum": [None,"conference paper","data paper","departmental bulletin paper","editorial","journal","journal article","newspaper"],"title": "資源タイプ","title_i18n": {"en": "Resource Type", "ja": "資源タイプ "}}}}}
    mapping = {
        'type.@value': ['item_key.resourcetype'],
        'type.@attributes.rdf:resource': ['item_key.resourceuri']
    }
    xml = """
            <record>
                <dc:type rdf:resource="http://purl.org/coar/resource_type/c_6501">journal article</dc:type>
            </record>
          """
    res = {}
    metadata = xmltoTestData('dc:type', xml)
    add_resource_type(schema, mapping, res, metadata)
    assert res == {'item_key': [{'resourcetype': 'journal article', 'resourceuri': 'http://purl.org/coar/resource_type/c_6501'}]}


# def add_creator_dc(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_creator_dc -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_creator_dc(mapper_dc):
    schema, mapping, res, metadata = mapper_dc("dc:creator")
    add_creator_dc(schema, mapping, res, metadata)
    assert "item_1593074267803" in res
    assert res["item_1593074267803"] == [{'creatorNames': [{'creatorName': 'テスト, 太郎'}]}, {'creatorNames': [{'creatorName': '1'}]}, {'creatorNames': [{'creatorName': '1234'}]}]
    
# def add_data_by_key(schema, res, resource_list, key):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_data_by_key -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_data_by_key():
    schema = {
        "properties":{
            "pubdate": { "type": "string", "title": "PubDate", "format": "datetime" },
            "item_1551264308487":{
                "type":"array","title":"Title",
                "items":{
                    "type":"object",
                    "properties":{
                        "subitem_1551255647225":{
                            "type": "string",
                            "title": "Title",
                            "format": "text"
                        },
                        "subitem_1551255648112":{
                            "enum":[None,"ja","en"],
                            "type":["null","string"],
                            "title":"Language",
                            "format":"select",
                            "currentEnum":["ja","en"]
                        }
                    }
                }
            }
        }
    }
    res = {}
    result = add_data_by_key(schema,res,[],"PubDate")
    assert result == None
    assert res == {}
    
    resource_list = [
        OrderedDict([("#text","test_title"),("@xml:lang","ja")]), # it is OrderedDict
        {"test":"value"} # it is not OrderedDict, str
    ]
    test = {"item_1551264308487":[{"subitem_1551255647225":"test_title","subitem_1551255648112":"ja"},{}]}
    result = add_data_by_key(schema,res,resource_list,"Title")
    assert res == test
    
    resource_list = "other_title"
    test = {"item_1551264308487":[{"subitem_1551255647225":"test_title","subitem_1551255648112":"ja"},{},{"subitem_1551255647225":"other_title"}]}
    result = add_data_by_key(schema,res,resource_list,"Title")
    assert res == test
    
# def add_source_dc(schema, res, source_list):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_source_dc -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_source_dc(mapper_dc):
    schema, mapping, res, metadata = mapper_dc("dc:source")
    add_source_dc(schema, mapping, res, metadata)
    assert "item_1617186941041" in res
    assert res["item_1617186941041"] == [{'subitem_1522650091861': 'test collectibles'}]
    
# def add_coverage_dc(schema, res, coverage_list):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_coverage_dc -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_coverage_dc(mapper_dc):
    schema, mapping, res, metadata = mapper_dc("dc:coverage")
    add_coverage_dc(schema, mapping, res, metadata)
    assert "item_1617186859717" in res
    assert res["item_1617186859717"] == [{'subitem_1522658031721': '1 to 2'}]
    
# def add_format_dc(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_format_dc -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_format_dc(mapper_dc):
    schema, mapping, res, metadata = mapper_dc("dc:format")
    add_format_dc(schema, mapping, res, metadata)
    assert "item_1617605131499" in res
    assert res["item_1617605131499"] == [{'format': 'text/plain'}]
    
# def add_contributor_dc(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_contributor_dc -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_contributor_dc(mapper_dc):
    schema, mapping, res, metadata = mapper_dc("dc:contributor")
    add_contributor_dc(schema, mapping, res, metadata)
    assert "item_1617349709064" in res
    assert res["item_1617349709064"] == [{'contributorNames': [{'contributorName': 'test, smith'}]}, {'contributorNames': [{'contributorName': '2'}]}, {'contributorNames': [{'contributorName': '5678'}]}]
    
# def add_relation_dc(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_relation_dc -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_relation_dc(mapper_dc):
    schema, mapping, res, metadata = mapper_dc("dc:relation")
    add_relation_dc(schema, mapping, res, metadata)
    assert "item_1617353299429" in res
    assert res["item_1617353299429"] == [{'subitem_1522306287251': {'subitem_1522306436033': '1111111'}}]
    
# def add_rights_dc(schema, res, rights, lang='', rights_resource=''):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_rights_dc -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_rights_dc(mapper_dc):
    # TODO:メソッドの引数が他となぜか違う
    schema, mapping, res, metadata = mapper_dc("dc:relation")
    add_rights_dc(schema, mapping, res, metadata)
    assert "item_1617186499011" in res
    assert res["item_1617186499011"] == [{'subitem_1522650717957': '1111111'}]

# def add_identifier_dc(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_identifier_dc -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_identifier_dc(mapper_dc):
    schema, mapping, res, metadata = mapper_dc("dc:identifier")
    add_identifier_dc(schema, mapping, res, metadata)
    assert "item_1617186783814" in res
    assert res["item_1617186783814"] == [{'subitem_identifier_uri': '1111'}]
    
# def add_description_dc(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_description_dc -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_description_dc(mapper_dc):
    schema, mapping, res, metadata = mapper_dc("dc:description")
    add_description_dc(schema, mapping, res, metadata)
    assert "item_1617186626617" in res
    assert res["item_1617186626617"] == [{'subitem_description': 'this is test abstract.'}]
    
# def add_subject_dc(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_subject_dc -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_subject_dc(mapper_dc):
    schema, mapping, res, metadata = mapper_dc("dc:subject")
    add_subject_dc(schema, mapping, res, metadata)
    assert "item_1617186609386" in res
    assert res["item_1617186609386"] == [{'subitem_1523261968819': 'テスト主題'}]
    
# def add_title_dc(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_title_dc -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_title_dc(mapper_dc):
    schema, mapping, res, metadata = mapper_dc("dc:title")
    res1 = copy.deepcopy(res)
    add_title_dc(schema, mapping, res1, metadata)
    assert "item_1617186331708" in res1
    assert res1["item_1617186331708"] == [{'subitem_1551255647225': 'test full item', 'subitem_1551255648112': 'ja'}]
    assert "title" in res1
    assert res1["title"] == "test full item"
    
    res2 = copy.deepcopy(res)
    add_title_dc(schema, mapping, res2, ["test full item"])
    assert "item_1617186331708" in res2
    assert res2["item_1617186331708"] == [{'subitem_1551255647225': 'test full item'}]
    assert "title" in res2
    assert res2["title"] == "test full item"
    
    res3 = copy.deepcopy(res)
    add_title_dc(schema, mapping, res3, [["test full item"]])
    assert "item_1617186331708" in res3
    assert res3["item_1617186331708"] == [{'subitem_1551255647225': 'test full item', 'subitem_1551255648112': 'test full item'}]
    assert "title" not in res3
    
    with patch("invenio_oaiharvester.harvester.parsing_metadata",return_value=(None,None)):
        res4 = copy.deepcopy(res)
        add_title_dc(schema, mapping, res4, metadata)
        assert "item_1617186331708" not in res4
        assert "title" not in res4

# def add_language_dc(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_language_dc -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_language_dc(mapper_dc):
    schema, mapping, res, metadata = mapper_dc("dc:language")
    add_language_dc(schema, mapping, res, metadata)
    assert "item_1617186702042" in res
    assert res["item_1617186702042"] == [{'subitem_1551255818386': 'jpn'}]

# def add_date_dc(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_date_dc -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_date_dc(mapper_dc):
    schema, mapping, res, metadata = mapper_dc("dc:date")
    add_date_dc(schema, mapping, res, metadata)
    assert "item_1617186660861" in res
    assert res["item_1617186660861"] == [{'subitem_1522300722591': '2022-10-20'}]
    
# def add_publisher_dc(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_publisher_dc -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_publisher_dc(mapper_dc):
    schema, mapping, res, metadata = mapper_dc("dc:publisher")
    add_publisher_dc(schema, mapping, res, metadata)
    assert "item_1617186643794" in res
    assert res["item_1617186643794"] == [{'subitem_1522300316516': 'test publisher'}]

# def add_resource_type_dc(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_resource_type_dc -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_resource_type_dc(mapper_dc):
    schema, mapping, res, metadata = mapper_dc("dc:type")
    add_resource_type_dc(schema, mapping, res, metadata)
    assert "item_1617258105262" in res
    assert res["item_1617258105262"] == [{'resourcetype': 'conference paper'}]

# def to_dict(input_ordered_dict):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_to_dict -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_to_dict():
    result = to_dict({"test_key":"test_value","test_list":["test1","test2"]})
    assert result == {"test_key":"test_value","test_list":["test1","test2"]}

# def map_sets(sets, encoding='utf-8'):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_map_sets -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_map_sets():
    xml_str = \
    '<root>'\
    '<set>'\
    '<setSpec>user-test_community1</setSpec>'\
    '<setName>test_community_title1</setName>'\
    '</set>'\
    '<set>'\
    '<setSpec>user-test_community2</setSpec>'\
    '<setName> </setName>'\
    '</set>'\
    '<set>'\
    '</set>'\
    '</root>'

    tree = etree.fromstring(xml_str)
    sets = tree.findall("set")
    
    result = map_sets(sets)
    assert type(result) is OrderedDict
    assert result["user-test_community1"] == "test_community_title1"
    assert result["user-test_community2"] == " "
    
# class BaseMapper:
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::TestBaseMapper -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
class TestBaseMapper:
#     def update_itemtype_map(cls):
#     def __init__(self, xml):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::TestBaseMapper::test_init -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
    def test_init(self,app,db):
        xml_str='<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><GetRecord><record><header><identifier>oai:weko3.example.org:00000001</identifier><datestamp>2023-02-20T06:24:47Z</datestamp><setSpec>1557819692844:1557819733276</setSpec><setSpec>1557820086539</setSpec></header><metadata><jpcoar:jpcoar xmlns:datacite="https://schema.datacite.org/meta/kernel-4/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcndl="http://ndl.go.jp/dcndl/terms/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:jpcoar="https://github.com/JPCOAR/schema/blob/master/1.0/" xmlns:oaire="http://namespace.openaire.eu/schema/oaire/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rioxxterms="http://www.rioxx.net/schema/v2.0/rioxxterms/" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="https://github.com/JPCOAR/schema/blob/master/1.0/" xsi:schemaLocation="https://github.com/JPCOAR/schema/blob/master/1.0/jpcoar_scm.xsd"><dc:title xml:lang="ja">test full item</dc:title><dcterms:alternative xml:lang="en">other title</dcterms:alternative><jpcoar:creator><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/1234" nameIdentifierScheme="ORCID">1234</jpcoar:nameIdentifier><jpcoar:creatorName xml:lang="ja">テスト, 太郎</jpcoar:creatorName><jpcoar:familyName xml:lang="ja">テスト</jpcoar:familyName><jpcoar:givenName xml:lang="ja">太郎</jpcoar:givenName><jpcoar:creatorAlternative xml:lang="ja">テスト　別郎</jpcoar:creatorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="http://www.isni.org/isni/5678" nameIdentifierScheme="ISNI">5678</jpcoar:nameIdentifier></jpcoar:affiliation></jpcoar:creator><jpcoar:contributor contributorType="ContactPerson"><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/5678" nameIdentifierScheme="ORCID">5678</jpcoar:nameIdentifier><jpcoar:contributorName xml:lang="en">test, smith</jpcoar:contributorName><jpcoar:familyName xml:lang="en">test</jpcoar:familyName><jpcoar:givenName xml:lang="en">smith</jpcoar:givenName><jpcoar:contributorAlternative xml:lang="en">other smith</jpcoar:contributorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="http://www.isni.org/isni/1234" nameIdentifierScheme="ISNI">1234</jpcoar:nameIdentifier></jpcoar:affiliation></jpcoar:contributor><dcterms:accessRights rdf:resource="http://purl.org/coar/access_right/c_14cb">metadata only access</dcterms:accessRights><rioxxterms:apc>Paid</rioxxterms:apc><dc:rights xml:lang="ja" rdf:resource="テスト権利情報Resource">テスト権利情報</dc:rights><jpcoar:rightsHolder><jpcoar:rightsHolderName xml:lang="ja">テスト　太郎</jpcoar:rightsHolderName></jpcoar:rightsHolder><jpcoar:subject xml:lang="ja" subjectURI="http://bsh.com" subjectScheme="BSH">テスト主題</jpcoar:subject><datacite:description xml:lang="en" descriptionType="Abstract">this is test abstract.</datacite:description><dc:publisher xml:lang="ja">test publisher</dc:publisher><datacite:date dateType="Accepted">2022-10-20</datacite:date><datacite:date dateType="Issued">2022-10-19</datacite:date><dc:language>jpn</dc:language><dc:type rdf:resource="http://purl.org/coar/resource_type/c_2fe3">newspaper</dc:type><datacite:version>1.1</datacite:version><oaire:version rdf:resource="http://purl.org/coar/version/c_b1a7d7d4d402bcce">AO</oaire:version><jpcoar:identifier identifierType="DOI">1111</jpcoar:identifier><jpcoar:identifier identifierType="DOI">https://doi.org/1234/0000000001</jpcoar:identifier><jpcoar:identifier identifierType="URI">https://192.168.56.103/records/1</jpcoar:identifier><jpcoar:identifierRegistration identifierType="JaLC">1234/0000000001</jpcoar:identifierRegistration><jpcoar:relation relationType="isVersionOf"><jpcoar:relatedIdentifier identifierType="ARK">1111111</jpcoar:relatedIdentifier><jpcoar:relatedTitle xml:lang="ja">関連情報テスト</jpcoar:relatedTitle></jpcoar:relation><jpcoar:relation relationType="isVersionOf"><jpcoar:relatedIdentifier identifierType="URI">https://192.168.56.103/records/3</jpcoar:relatedIdentifier></jpcoar:relation><dcterms:temporal xml:lang="ja">1 to 2</dcterms:temporal><datacite:geoLocation><datacite:geoLocationPoint><datacite:pointLongitude>12345</datacite:pointLongitude><datacite:pointLatitude>67890</datacite:pointLatitude></datacite:geoLocationPoint><datacite:geoLocationBox><datacite:westBoundLongitude>123</datacite:westBoundLongitude><datacite:eastBoundLongitude>456</datacite:eastBoundLongitude><datacite:southBoundLatitude>789</datacite:southBoundLatitude><datacite:northBoundLatitude>1112</datacite:northBoundLatitude></datacite:geoLocationBox><datacite:geoLocationPlace>テスト位置情報</datacite:geoLocationPlace></datacite:geoLocation><jpcoar:fundingReference><datacite:funderIdentifier funderIdentifierType="Crossref Funder">22222</datacite:funderIdentifier><jpcoar:funderName xml:lang="ja">テスト助成機関</jpcoar:funderName><datacite:awardNumber awardURI="https://test.research.com">1111</datacite:awardNumber><jpcoar:awardTitle xml:lang="ja">テスト研究</jpcoar:awardTitle></jpcoar:fundingReference><jpcoar:sourceIdentifier identifierType="PISSN">test source Identifier</jpcoar:sourceIdentifier><jpcoar:sourceTitle xml:lang="ja">test collectibles</jpcoar:sourceTitle><jpcoar:sourceTitle xml:lang="ja">test title book</jpcoar:sourceTitle><jpcoar:volume>5</jpcoar:volume><jpcoar:volume>1</jpcoar:volume><jpcoar:issue>2</jpcoar:issue><jpcoar:issue>2</jpcoar:issue><jpcoar:numPages>333</jpcoar:numPages><jpcoar:numPages>555</jpcoar:numPages><jpcoar:pageStart>123</jpcoar:pageStart><jpcoar:pageStart>789</jpcoar:pageStart><jpcoar:pageEnd>456</jpcoar:pageEnd><jpcoar:pageEnd>234</jpcoar:pageEnd><dcndl:dissertationNumber>9999</dcndl:dissertationNumber><dcndl:degreeName xml:lang="ja">テスト学位</dcndl:degreeName><dcndl:dateGranted>2022-10-19</dcndl:dateGranted><jpcoar:degreeGrantor><jpcoar:nameIdentifier nameIdentifierScheme="kakenhi">学位授与機関識別子テスト</jpcoar:nameIdentifier><jpcoar:degreeGrantorName xml:lang="ja">学位授与機関</jpcoar:degreeGrantorName></jpcoar:degreeGrantor><jpcoar:conference><jpcoar:conferenceName xml:lang="ja">テスト会議</jpcoar:conferenceName><jpcoar:conferenceSequence>12345</jpcoar:conferenceSequence><jpcoar:conferenceSponsor xml:lang="ja">テスト機関</jpcoar:conferenceSponsor><jpcoar:conferenceDate endDay="1" endYear="2005" endMonth="12" startDay="11" xml:lang="ja" startYear="2000" startMonth="4">12</jpcoar:conferenceDate><jpcoar:conferenceVenue xml:lang="ja">テスト会場</jpcoar:conferenceVenue><jpcoar:conferenceCountry>JPN</jpcoar:conferenceCountry></jpcoar:conference><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test1.txt</jpcoar:URI><jpcoar:mimeType>text/plain</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:date dateType="Accepted">2022-10-20</datacite:date><datacite:version>1.0</datacite:version></jpcoar:file><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test2</jpcoar:URI><jpcoar:mimeType>application/octet-stream</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:version>1.2</datacite:version></jpcoar:file><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test3.png</jpcoar:URI><jpcoar:mimeType>image/png</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:version>2.1</datacite:version></jpcoar:file></jpcoar:jpcoar></metadata></record></GetRecord></OAI-PMH>'
        tree = etree.fromstring(xml_str)
        record = tree.findall("./GetRecord/record",namespaces=tree.nsmap)[0]
        xml = etree.tostring(record,encoding="utf-8").decode()
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
        mapper = BaseMapper(xml)
        assert hasattr(mapper, "itemtype") == False
        
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
        mapper = BaseMapper(xml)
        assert hasattr(mapper, "itemtype") == True
        assert mapper.itemtype == item_type2

#     def is_deleted(self):
#     def identifier(self):
#     def datestamp(self):
#     def specs(self):
#     def map_itemtype(self, type_tag):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::TestBaseMapper::test_map_itemtype -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
    def test_map_itemtype(self,db):
        item_type_name1 = ItemTypeName(
            id=10, name="Journal Article", has_site_license=True, is_active=True
        )
        item_type1 = ItemType(
            id=10,name_id=10,harvesting_type=True,schema={},form={},render={},tag=1,version_id=1,is_deleted=False,
        )
        db.session.add(item_type_name1)
        db.session.add(item_type1)
        db.session.commit()
        
        # not exist type
        xml_str='<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><GetRecord><record><header><identifier>oai:weko3.example.org:00000001</identifier><datestamp>2023-02-20T06:24:47Z</datestamp><setSpec>1557819692844:1557819733276</setSpec><setSpec>1557820086539</setSpec></header><metadata><jpcoar:jpcoar xmlns:datacite="https://schema.datacite.org/meta/kernel-4/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcndl="http://ndl.go.jp/dcndl/terms/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:jpcoar="https://github.com/JPCOAR/schema/blob/master/1.0/" xmlns:oaire="http://namespace.openaire.eu/schema/oaire/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rioxxterms="http://www.rioxx.net/schema/v2.0/rioxxterms/" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="https://github.com/JPCOAR/schema/blob/master/1.0/" xsi:schemaLocation="https://github.com/JPCOAR/schema/blob/master/1.0/jpcoar_scm.xsd"><dc:title xml:lang="ja">test full item</dc:title><dcterms:alternative xml:lang="en">other title</dcterms:alternative><jpcoar:creator><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/1234" nameIdentifierScheme="ORCID">1234</jpcoar:nameIdentifier><jpcoar:creatorName xml:lang="ja">テスト, 太郎</jpcoar:creatorName><jpcoar:familyName xml:lang="ja">テスト</jpcoar:familyName><jpcoar:givenName xml:lang="ja">太郎</jpcoar:givenName><jpcoar:creatorAlternative xml:lang="ja">テスト　別郎</jpcoar:creatorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="http://www.isni.org/isni/5678" nameIdentifierScheme="ISNI">5678</jpcoar:nameIdentifier></jpcoar:affiliation></jpcoar:creator><jpcoar:contributor contributorType="ContactPerson"><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/5678" nameIdentifierScheme="ORCID">5678</jpcoar:nameIdentifier><jpcoar:contributorName xml:lang="en">test, smith</jpcoar:contributorName><jpcoar:familyName xml:lang="en">test</jpcoar:familyName><jpcoar:givenName xml:lang="en">smith</jpcoar:givenName><jpcoar:contributorAlternative xml:lang="en">other smith</jpcoar:contributorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="http://www.isni.org/isni/1234" nameIdentifierScheme="ISNI">1234</jpcoar:nameIdentifier></jpcoar:affiliation></jpcoar:contributor><dcterms:accessRights rdf:resource="http://purl.org/coar/access_right/c_14cb">metadata only access</dcterms:accessRights><rioxxterms:apc>Paid</rioxxterms:apc><dc:rights xml:lang="ja" rdf:resource="テスト権利情報Resource">テスト権利情報</dc:rights><jpcoar:rightsHolder><jpcoar:rightsHolderName xml:lang="ja">テスト　太郎</jpcoar:rightsHolderName></jpcoar:rightsHolder><jpcoar:subject xml:lang="ja" subjectURI="http://bsh.com" subjectScheme="BSH">テスト主題</jpcoar:subject><datacite:description xml:lang="en" descriptionType="Abstract">this is test abstract.</datacite:description><dc:publisher xml:lang="ja">test publisher</dc:publisher><datacite:date dateType="Accepted">2022-10-20</datacite:date><datacite:date dateType="Issued">2022-10-19</datacite:date><dc:language>jpn</dc:language><datacite:version>1.1</datacite:version><oaire:version rdf:resource="http://purl.org/coar/version/c_b1a7d7d4d402bcce">AO</oaire:version><jpcoar:identifier identifierType="DOI">1111</jpcoar:identifier><jpcoar:identifier identifierType="DOI">https://doi.org/1234/0000000001</jpcoar:identifier><jpcoar:identifier identifierType="URI">https://192.168.56.103/records/1</jpcoar:identifier><jpcoar:identifierRegistration identifierType="JaLC">1234/0000000001</jpcoar:identifierRegistration><jpcoar:relation relationType="isVersionOf"><jpcoar:relatedIdentifier identifierType="ARK">1111111</jpcoar:relatedIdentifier><jpcoar:relatedTitle xml:lang="ja">関連情報テスト</jpcoar:relatedTitle></jpcoar:relation><jpcoar:relation relationType="isVersionOf"><jpcoar:relatedIdentifier identifierType="URI">https://192.168.56.103/records/3</jpcoar:relatedIdentifier></jpcoar:relation><dcterms:temporal xml:lang="ja">1 to 2</dcterms:temporal><datacite:geoLocation><datacite:geoLocationPoint><datacite:pointLongitude>12345</datacite:pointLongitude><datacite:pointLatitude>67890</datacite:pointLatitude></datacite:geoLocationPoint><datacite:geoLocationBox><datacite:westBoundLongitude>123</datacite:westBoundLongitude><datacite:eastBoundLongitude>456</datacite:eastBoundLongitude><datacite:southBoundLatitude>789</datacite:southBoundLatitude><datacite:northBoundLatitude>1112</datacite:northBoundLatitude></datacite:geoLocationBox><datacite:geoLocationPlace>テスト位置情報</datacite:geoLocationPlace></datacite:geoLocation><jpcoar:fundingReference><datacite:funderIdentifier funderIdentifierType="Crossref Funder">22222</datacite:funderIdentifier><jpcoar:funderName xml:lang="ja">テスト助成機関</jpcoar:funderName><datacite:awardNumber awardURI="https://test.research.com">1111</datacite:awardNumber><jpcoar:awardTitle xml:lang="ja">テスト研究</jpcoar:awardTitle></jpcoar:fundingReference><jpcoar:sourceIdentifier identifierType="PISSN">test source Identifier</jpcoar:sourceIdentifier><jpcoar:sourceTitle xml:lang="ja">test collectibles</jpcoar:sourceTitle><jpcoar:sourceTitle xml:lang="ja">test title book</jpcoar:sourceTitle><jpcoar:volume>5</jpcoar:volume><jpcoar:volume>1</jpcoar:volume><jpcoar:issue>2</jpcoar:issue><jpcoar:issue>2</jpcoar:issue><jpcoar:numPages>333</jpcoar:numPages><jpcoar:numPages>555</jpcoar:numPages><jpcoar:pageStart>123</jpcoar:pageStart><jpcoar:pageStart>789</jpcoar:pageStart><jpcoar:pageEnd>456</jpcoar:pageEnd><jpcoar:pageEnd>234</jpcoar:pageEnd><dcndl:dissertationNumber>9999</dcndl:dissertationNumber><dcndl:degreeName xml:lang="ja">テスト学位</dcndl:degreeName><dcndl:dateGranted>2022-10-19</dcndl:dateGranted><jpcoar:degreeGrantor><jpcoar:nameIdentifier nameIdentifierScheme="kakenhi">学位授与機関識別子テスト</jpcoar:nameIdentifier><jpcoar:degreeGrantorName xml:lang="ja">学位授与機関</jpcoar:degreeGrantorName></jpcoar:degreeGrantor><jpcoar:conference><jpcoar:conferenceName xml:lang="ja">テスト会議</jpcoar:conferenceName><jpcoar:conferenceSequence>12345</jpcoar:conferenceSequence><jpcoar:conferenceSponsor xml:lang="ja">テスト機関</jpcoar:conferenceSponsor><jpcoar:conferenceDate endDay="1" endYear="2005" endMonth="12" startDay="11" xml:lang="ja" startYear="2000" startMonth="4">12</jpcoar:conferenceDate><jpcoar:conferenceVenue xml:lang="ja">テスト会場</jpcoar:conferenceVenue><jpcoar:conferenceCountry>JPN</jpcoar:conferenceCountry></jpcoar:conference><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test1.txt</jpcoar:URI><jpcoar:mimeType>text/plain</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:date dateType="Accepted">2022-10-20</datacite:date><datacite:version>1.0</datacite:version></jpcoar:file><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test2</jpcoar:URI><jpcoar:mimeType>application/octet-stream</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:version>1.2</datacite:version></jpcoar:file><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test3.png</jpcoar:URI><jpcoar:mimeType>image/png</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:version>2.1</datacite:version></jpcoar:file></jpcoar:jpcoar></metadata></record></GetRecord></OAI-PMH>'        
        tree = etree.fromstring(xml_str)
        record = tree.findall("./GetRecord/record",namespaces=tree.nsmap)[0]
        xml = etree.tostring(record,encoding="utf-8").decode()
        mapper = BaseMapper(xml)
        mapper.map_itemtype("jpcoar:jpcoar")
        assert hasattr(mapper, "itemtype") == False
        
        BaseMapper.update_itemtype_map()
        # "news paper" is  in RESOURCE_TYPE_MAP and itemtype_map
        # "conference paper" is  in RESOURCE_TYPE_MAP, not in itemtype_map
        # "other type" is not in RESOURCE_TYPE_MAP, not OrederedDict
        xml_str='<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><GetRecord><record><header><identifier>oai:weko3.example.org:00000001</identifier><datestamp>2023-02-20T06:24:47Z</datestamp><setSpec>1557819692844:1557819733276</setSpec><setSpec>1557820086539</setSpec></header><metadata><jpcoar:jpcoar xmlns:datacite="https://schema.datacite.org/meta/kernel-4/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcndl="http://ndl.go.jp/dcndl/terms/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:jpcoar="https://github.com/JPCOAR/schema/blob/master/1.0/" xmlns:oaire="http://namespace.openaire.eu/schema/oaire/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rioxxterms="http://www.rioxx.net/schema/v2.0/rioxxterms/" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="https://github.com/JPCOAR/schema/blob/master/1.0/" xsi:schemaLocation="https://github.com/JPCOAR/schema/blob/master/1.0/jpcoar_scm.xsd"><dc:title xml:lang="ja">test full item</dc:title><dcterms:alternative xml:lang="en">other title</dcterms:alternative><jpcoar:creator><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/1234" nameIdentifierScheme="ORCID">1234</jpcoar:nameIdentifier><jpcoar:creatorName xml:lang="ja">テスト, 太郎</jpcoar:creatorName><jpcoar:familyName xml:lang="ja">テスト</jpcoar:familyName><jpcoar:givenName xml:lang="ja">太郎</jpcoar:givenName><jpcoar:creatorAlternative xml:lang="ja">テスト　別郎</jpcoar:creatorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="http://www.isni.org/isni/5678" nameIdentifierScheme="ISNI">5678</jpcoar:nameIdentifier></jpcoar:affiliation></jpcoar:creator><jpcoar:contributor contributorType="ContactPerson"><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/5678" nameIdentifierScheme="ORCID">5678</jpcoar:nameIdentifier><jpcoar:contributorName xml:lang="en">test, smith</jpcoar:contributorName><jpcoar:familyName xml:lang="en">test</jpcoar:familyName><jpcoar:givenName xml:lang="en">smith</jpcoar:givenName><jpcoar:contributorAlternative xml:lang="en">other smith</jpcoar:contributorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="http://www.isni.org/isni/1234" nameIdentifierScheme="ISNI">1234</jpcoar:nameIdentifier></jpcoar:affiliation></jpcoar:contributor><dcterms:accessRights rdf:resource="http://purl.org/coar/access_right/c_14cb">metadata only access</dcterms:accessRights><rioxxterms:apc>Paid</rioxxterms:apc><dc:rights xml:lang="ja" rdf:resource="テスト権利情報Resource">テスト権利情報</dc:rights><jpcoar:rightsHolder><jpcoar:rightsHolderName xml:lang="ja">テスト　太郎</jpcoar:rightsHolderName></jpcoar:rightsHolder><jpcoar:subject xml:lang="ja" subjectURI="http://bsh.com" subjectScheme="BSH">テスト主題</jpcoar:subject><datacite:description xml:lang="en" descriptionType="Abstract">this is test abstract.</datacite:description><dc:publisher xml:lang="ja">test publisher</dc:publisher><datacite:date dateType="Accepted">2022-10-20</datacite:date><datacite:date dateType="Issued">2022-10-19</datacite:date><dc:language>jpn</dc:language><dc:type rdf:resource="http://purl.org/coar/resource_type/c_2fe3">newspaper</dc:type><dc:type rdf:resource="http://purl.org/coar/resource_type/c_2fe3">conference paper</dc:type><dc:type>other type</dc:type><datacite:version>1.1</datacite:version><oaire:version rdf:resource="http://purl.org/coar/version/c_b1a7d7d4d402bcce">AO</oaire:version><jpcoar:identifier identifierType="DOI">1111</jpcoar:identifier><jpcoar:identifier identifierType="DOI">https://doi.org/1234/0000000001</jpcoar:identifier><jpcoar:identifier identifierType="URI">https://192.168.56.103/records/1</jpcoar:identifier><jpcoar:identifierRegistration identifierType="JaLC">1234/0000000001</jpcoar:identifierRegistration><jpcoar:relation relationType="isVersionOf"><jpcoar:relatedIdentifier identifierType="ARK">1111111</jpcoar:relatedIdentifier><jpcoar:relatedTitle xml:lang="ja">関連情報テスト</jpcoar:relatedTitle></jpcoar:relation><jpcoar:relation relationType="isVersionOf"><jpcoar:relatedIdentifier identifierType="URI">https://192.168.56.103/records/3</jpcoar:relatedIdentifier></jpcoar:relation><dcterms:temporal xml:lang="ja">1 to 2</dcterms:temporal><datacite:geoLocation><datacite:geoLocationPoint><datacite:pointLongitude>12345</datacite:pointLongitude><datacite:pointLatitude>67890</datacite:pointLatitude></datacite:geoLocationPoint><datacite:geoLocationBox><datacite:westBoundLongitude>123</datacite:westBoundLongitude><datacite:eastBoundLongitude>456</datacite:eastBoundLongitude><datacite:southBoundLatitude>789</datacite:southBoundLatitude><datacite:northBoundLatitude>1112</datacite:northBoundLatitude></datacite:geoLocationBox><datacite:geoLocationPlace>テスト位置情報</datacite:geoLocationPlace></datacite:geoLocation><jpcoar:fundingReference><datacite:funderIdentifier funderIdentifierType="Crossref Funder">22222</datacite:funderIdentifier><jpcoar:funderName xml:lang="ja">テスト助成機関</jpcoar:funderName><datacite:awardNumber awardURI="https://test.research.com">1111</datacite:awardNumber><jpcoar:awardTitle xml:lang="ja">テスト研究</jpcoar:awardTitle></jpcoar:fundingReference><jpcoar:sourceIdentifier identifierType="PISSN">test source Identifier</jpcoar:sourceIdentifier><jpcoar:sourceTitle xml:lang="ja">test collectibles</jpcoar:sourceTitle><jpcoar:sourceTitle xml:lang="ja">test title book</jpcoar:sourceTitle><jpcoar:volume>5</jpcoar:volume><jpcoar:volume>1</jpcoar:volume><jpcoar:issue>2</jpcoar:issue><jpcoar:issue>2</jpcoar:issue><jpcoar:numPages>333</jpcoar:numPages><jpcoar:numPages>555</jpcoar:numPages><jpcoar:pageStart>123</jpcoar:pageStart><jpcoar:pageStart>789</jpcoar:pageStart><jpcoar:pageEnd>456</jpcoar:pageEnd><jpcoar:pageEnd>234</jpcoar:pageEnd><dcndl:dissertationNumber>9999</dcndl:dissertationNumber><dcndl:degreeName xml:lang="ja">テスト学位</dcndl:degreeName><dcndl:dateGranted>2022-10-19</dcndl:dateGranted><jpcoar:degreeGrantor><jpcoar:nameIdentifier nameIdentifierScheme="kakenhi">学位授与機関識別子テスト</jpcoar:nameIdentifier><jpcoar:degreeGrantorName xml:lang="ja">学位授与機関</jpcoar:degreeGrantorName></jpcoar:degreeGrantor><jpcoar:conference><jpcoar:conferenceName xml:lang="ja">テスト会議</jpcoar:conferenceName><jpcoar:conferenceSequence>12345</jpcoar:conferenceSequence><jpcoar:conferenceSponsor xml:lang="ja">テスト機関</jpcoar:conferenceSponsor><jpcoar:conferenceDate endDay="1" endYear="2005" endMonth="12" startDay="11" xml:lang="ja" startYear="2000" startMonth="4">12</jpcoar:conferenceDate><jpcoar:conferenceVenue xml:lang="ja">テスト会場</jpcoar:conferenceVenue><jpcoar:conferenceCountry>JPN</jpcoar:conferenceCountry></jpcoar:conference><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test1.txt</jpcoar:URI><jpcoar:mimeType>text/plain</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:date dateType="Accepted">2022-10-20</datacite:date><datacite:version>1.0</datacite:version></jpcoar:file><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test2</jpcoar:URI><jpcoar:mimeType>application/octet-stream</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:version>1.2</datacite:version></jpcoar:file><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test3.png</jpcoar:URI><jpcoar:mimeType>image/png</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:version>2.1</datacite:version></jpcoar:file></jpcoar:jpcoar></metadata></record></GetRecord></OAI-PMH>'
        tree = etree.fromstring(xml_str)
        record = tree.findall("./GetRecord/record",namespaces=tree.nsmap)[0]
        xml = etree.tostring(record,encoding="utf-8").decode()
        mapper = BaseMapper(xml)
        mapper.map_itemtype("jpcoar:jpcoar")
        assert hasattr(mapper, "itemtype") == True
        assert mapper.itemtype == item_type1

# class DCMapper(BaseMapper):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::TestDCMapper -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
class TestDCMapper:
#     def __init__(self, xml):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::TestDCMapper::test_init -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
    def test_init(self,app,db):
        xml_str = '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2023-03-01T02:07:10Z</responseDate><request metadataPrefix="oai_dc" identifier="oai:weko3.example.org:00000001" verb="GetRecord">https://192.168.56.103/oai</request><GetRecord><record><header><identifier>oai:weko3.example.org:00000001</identifier><datestamp>2023-02-20T06:24:47Z</datestamp><setSpec>1557819692844:1557819733276</setSpec><setSpec>1557820086539</setSpec></header><metadata><oai_dc:dc xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" xmlns="http://www.w3.org/2001/XMLSchema" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd"><dc:title xml:lang="ja">test full item</dc:title><dc:creator>テスト, 太郎</dc:creator><dc:creator>1</dc:creator><dc:creator>1234</dc:creator><dc:subject>テスト主題</dc:subject><dc:description>this is test abstract.</dc:description><dc:publisher>test publisher</dc:publisher><dc:contributor>test, smith</dc:contributor><dc:contributor>2</dc:contributor><dc:contributor>5678</dc:contributor><dc:date>2022-10-20</dc:date><dc:type>conference paper</dc:type><dc:identifier>1111</dc:identifier><dc:source>test collectibles</dc:source><dc:language>jpn</dc:language><dc:relation>1111111</dc:relation><dc:coverage>1 to 2</dc:coverage><dc:rights>metadata only access</dc:rights><dc:format>text/plain</dc:format></oai_dc:dc></metadata></record></GetRecord></OAI-PMH>'
        tree = etree.fromstring(xml_str)
        record = tree.findall("./GetRecord/record",namespaces=tree.nsmap)[0]
        xml = etree.tostring(record,encoding="utf-8").decode()
        item_type_name1 = ItemTypeName(
            id=10, name="Multiple", has_site_license=True, is_active=True
        )
        item_type1 = ItemType(
            id=10,name_id=10,harvesting_type=True,schema={},form={},render={},tag=1,version_id=1,is_deleted=False,
        )
        db.session.add(item_type_name1)
        db.session.add(item_type1)
        db.session.commit()
        mapper = DCMapper(xml)
        assert hasattr(mapper,"itemtype")
        assert "Multiple" in BaseMapper.itemtype_map
    
#     def map(self):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::TestDCMapper::test_map -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
    def test_map(self,db_itemtype):
        
        deleted_xml = '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2023-03-01T02:07:10Z</responseDate><request metadataPrefix="oai_dc" identifier="oai:weko3.example.org:00000001" verb="GetRecord">https://192.168.56.103/oai</request><GetRecord><record><header status="deleted"><identifier>oai:weko3.example.org:00000001</identifier><datestamp>2023-02-20T06:24:47Z</datestamp></header></record></GetRecord></OAI-PMH>'
        tree = etree.fromstring(deleted_xml)
        record = tree.findall("./GetRecord/record",namespaces=tree.nsmap)[0]
        xml = etree.tostring(record,encoding="utf-8").decode()
        mapper = DCMapper(xml)
        mapper.itemtype = ItemType.query.filter_by(id=12).one()
        
        result = mapper.map()
        assert result == {}
        
        xml_str = '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2023-03-01T02:07:10Z</responseDate><request metadataPrefix="oai_dc" identifier="oai:weko3.example.org:00000001" verb="GetRecord">https://192.168.56.103/oai</request><GetRecord><record><header><identifier>oai:weko3.example.org:00000001</identifier><datestamp>2023-02-20T06:24:47Z</datestamp><setSpec>1557819692844:1557819733276</setSpec><setSpec>1557820086539</setSpec></header><metadata><oai_dc:dc xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" xmlns="http://www.w3.org/2001/XMLSchema" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd"><dc:title xml:lang="ja">test full item</dc:title><dc:creator>テスト, 太郎</dc:creator><dc:creator>1</dc:creator><dc:creator>1234</dc:creator><dc:subject>テスト主題</dc:subject><dc:description>this is test abstract.</dc:description><dc:publisher>test publisher</dc:publisher><dc:contributor>test, smith</dc:contributor><dc:contributor>2</dc:contributor><dc:contributor>5678</dc:contributor><dc:date>2022-10-20</dc:date><dc:type>conference paper</dc:type><dc:identifier>1111</dc:identifier><dc:source>test collectibles</dc:source><dc:language>jpn</dc:language><dc:relation>1111111</dc:relation><dc:coverage>1 to 2</dc:coverage><dc:rights>metadata only access</dc:rights><dc:format>text/plain</dc:format></oai_dc:dc></metadata></record></GetRecord></OAI-PMH>'
        tree = etree.fromstring(xml_str)
        record = tree.findall("./GetRecord/record",namespaces=tree.nsmap)[0]
        xml = etree.tostring(record,encoding="utf-8").decode()
        mapper = DCMapper(xml)
        mapper.itemtype = ItemType.query.filter_by(id=12).one()
        
        test = {'$schema': 12, 'pubdate': '2023-02-20', 'item_1617186331708': [{'subitem_1551255647225': 'test full item', 'subitem_1551255648112': 'ja'}], 'title': 'test full item', 'item_1593074267803': [{'creatorNames': [{'creatorName': 'テスト, 太郎'}]}, {'creatorNames': [{'creatorName': '1'}]}, {'creatorNames': [{'creatorName': '1234'}]}], 'item_1617186609386': [{'subitem_1523261968819': 'テスト主題'}], 'item_1617186626617': [{'subitem_description': 'this is test abstract.'}], 'item_1617186643794': [{'subitem_1522300316516': 'test publisher'}], 'item_1617349709064': [{'contributorNames': [{'contributorName': 'test, smith'}]}, {'contributorNames': [{'contributorName': '2'}]}, {'contributorNames': [{'contributorName': '5678'}]}], 'item_1617186660861': [{'subitem_1522300722591': '2022-10-20'}], 'item_1617258105262': [{'resourcetype': 'conference paper'}], 'item_1617186783814': [{'subitem_identifier_uri': '1111'}], 'item_1617186941041': [{'subitem_1522650091861': 'test collectibles'}], 'item_1617186702042': [{'subitem_1551255818386': 'jpn'}], 'item_1617353299429': [{'subitem_1522306287251': {'subitem_1522306436033': '1111111'}}], 'item_1617186859717': [{'subitem_1522658031721': '1 to 2'}], 'item_1617186499011': [{'subitem_1522650717957': 'metadata only access'}], 'item_1617605131499': [{'format': 'text/plain'}]}
        result = mapper.map()
        assert result == test

# class JPCOARMapper(BaseMapper):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::TestJPCOARMapper -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
class TestJPCOARMapper:
#     def __init__(self, xml):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::TestJPCOARMapper::test_init -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
    def test_init(self,app,db):
        xml_str = '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><GetRecord><record><header><identifier>oai:weko3.example.org:00000001</identifier><datestamp>2023-02-20T06:24:47Z</datestamp><setSpec>1557819692844:1557819733276</setSpec><setSpec>1557820086539</setSpec></header><metadata><jpcoar:jpcoar xmlns:datacite="https://schema.datacite.org/meta/kernel-4/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcndl="http://ndl.go.jp/dcndl/terms/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:jpcoar="https://github.com/JPCOAR/schema/blob/master/1.0/" xmlns:oaire="http://namespace.openaire.eu/schema/oaire/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rioxxterms="http://www.rioxx.net/schema/v2.0/rioxxterms/" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="https://github.com/JPCOAR/schema/blob/master/1.0/" xsi:schemaLocation="https://github.com/JPCOAR/schema/blob/master/1.0/jpcoar_scm.xsd"><dc:title xml:lang="ja">test full item</dc:title><dcterms:alternative xml:lang="en">other title</dcterms:alternative><jpcoar:creator><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/1234" nameIdentifierScheme="ORCID">1234</jpcoar:nameIdentifier><jpcoar:creatorName xml:lang="ja">テスト, 太郎</jpcoar:creatorName><jpcoar:familyName xml:lang="ja">テスト</jpcoar:familyName><jpcoar:givenName xml:lang="ja">太郎</jpcoar:givenName><jpcoar:creatorAlternative xml:lang="ja">テスト　別郎</jpcoar:creatorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="http://www.isni.org/isni/5678" nameIdentifierScheme="ISNI">5678</jpcoar:nameIdentifier></jpcoar:affiliation></jpcoar:creator><jpcoar:contributor contributorType="ContactPerson"><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/5678" nameIdentifierScheme="ORCID">5678</jpcoar:nameIdentifier><jpcoar:contributorName xml:lang="en">test, smith</jpcoar:contributorName><jpcoar:familyName xml:lang="en">test</jpcoar:familyName><jpcoar:givenName xml:lang="en">smith</jpcoar:givenName><jpcoar:contributorAlternative xml:lang="en">other smith</jpcoar:contributorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="http://www.isni.org/isni/1234" nameIdentifierScheme="ISNI">1234</jpcoar:nameIdentifier></jpcoar:affiliation></jpcoar:contributor><dcterms:accessRights rdf:resource="http://purl.org/coar/access_right/c_14cb">metadata only access</dcterms:accessRights><rioxxterms:apc>Paid</rioxxterms:apc><dc:rights xml:lang="ja" rdf:resource="テスト権利情報Resource">テスト権利情報</dc:rights><jpcoar:rightsHolder><jpcoar:rightsHolderName xml:lang="ja">テスト　太郎</jpcoar:rightsHolderName></jpcoar:rightsHolder><jpcoar:subject xml:lang="ja" subjectURI="http://bsh.com" subjectScheme="BSH">テスト主題</jpcoar:subject><datacite:description xml:lang="en" descriptionType="Abstract">this is test abstract.</datacite:description><dc:publisher xml:lang="ja">test publisher</dc:publisher><datacite:date dateType="Accepted">2022-10-20</datacite:date><datacite:date dateType="Issued">2022-10-19</datacite:date><dc:language>jpn</dc:language><dc:type rdf:resource="http://purl.org/coar/resource_type/c_2fe3">newspaper</dc:type><datacite:version>1.1</datacite:version><oaire:version rdf:resource="http://purl.org/coar/version/c_b1a7d7d4d402bcce">AO</oaire:version><jpcoar:identifier identifierType="DOI">1111</jpcoar:identifier><jpcoar:identifier identifierType="DOI">https://doi.org/1234/0000000001</jpcoar:identifier><jpcoar:identifier identifierType="URI">https://192.168.56.103/records/1</jpcoar:identifier><jpcoar:identifierRegistration identifierType="JaLC">1234/0000000001</jpcoar:identifierRegistration><jpcoar:relation relationType="isVersionOf"><jpcoar:relatedIdentifier identifierType="ARK">1111111</jpcoar:relatedIdentifier><jpcoar:relatedTitle xml:lang="ja">関連情報テスト</jpcoar:relatedTitle></jpcoar:relation><jpcoar:relation relationType="isVersionOf"><jpcoar:relatedIdentifier identifierType="URI">https://192.168.56.103/records/3</jpcoar:relatedIdentifier></jpcoar:relation><dcterms:temporal xml:lang="ja">1 to 2</dcterms:temporal><datacite:geoLocation><datacite:geoLocationPoint><datacite:pointLongitude>12345</datacite:pointLongitude><datacite:pointLatitude>67890</datacite:pointLatitude></datacite:geoLocationPoint><datacite:geoLocationBox><datacite:westBoundLongitude>123</datacite:westBoundLongitude><datacite:eastBoundLongitude>456</datacite:eastBoundLongitude><datacite:southBoundLatitude>789</datacite:southBoundLatitude><datacite:northBoundLatitude>1112</datacite:northBoundLatitude></datacite:geoLocationBox><datacite:geoLocationPlace>テスト位置情報</datacite:geoLocationPlace></datacite:geoLocation><jpcoar:fundingReference><datacite:funderIdentifier funderIdentifierType="Crossref Funder">22222</datacite:funderIdentifier><jpcoar:funderName xml:lang="ja">テスト助成機関</jpcoar:funderName><datacite:awardNumber awardURI="https://test.research.com">1111</datacite:awardNumber><jpcoar:awardTitle xml:lang="ja">テスト研究</jpcoar:awardTitle></jpcoar:fundingReference><jpcoar:sourceIdentifier identifierType="PISSN">test source Identifier</jpcoar:sourceIdentifier><jpcoar:sourceTitle xml:lang="ja">test collectibles</jpcoar:sourceTitle><jpcoar:sourceTitle xml:lang="ja">test title book</jpcoar:sourceTitle><jpcoar:volume>5</jpcoar:volume><jpcoar:volume>1</jpcoar:volume><jpcoar:issue>2</jpcoar:issue><jpcoar:issue>2</jpcoar:issue><jpcoar:numPages>333</jpcoar:numPages><jpcoar:numPages>555</jpcoar:numPages><jpcoar:pageStart>123</jpcoar:pageStart><jpcoar:pageStart>789</jpcoar:pageStart><jpcoar:pageEnd>456</jpcoar:pageEnd><jpcoar:pageEnd>234</jpcoar:pageEnd><dcndl:dissertationNumber>9999</dcndl:dissertationNumber><dcndl:degreeName xml:lang="ja">テスト学位</dcndl:degreeName><dcndl:dateGranted>2022-10-19</dcndl:dateGranted><jpcoar:degreeGrantor><jpcoar:nameIdentifier nameIdentifierScheme="kakenhi">学位授与機関識別子テスト</jpcoar:nameIdentifier><jpcoar:degreeGrantorName xml:lang="ja">学位授与機関</jpcoar:degreeGrantorName></jpcoar:degreeGrantor><jpcoar:conference><jpcoar:conferenceName xml:lang="ja">テスト会議</jpcoar:conferenceName><jpcoar:conferenceSequence>12345</jpcoar:conferenceSequence><jpcoar:conferenceSponsor xml:lang="ja">テスト機関</jpcoar:conferenceSponsor><jpcoar:conferenceDate endDay="1" endYear="2005" endMonth="12" startDay="11" xml:lang="ja" startYear="2000" startMonth="4">12</jpcoar:conferenceDate><jpcoar:conferenceVenue xml:lang="ja">テスト会場</jpcoar:conferenceVenue><jpcoar:conferenceCountry>JPN</jpcoar:conferenceCountry></jpcoar:conference><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test1.txt</jpcoar:URI><jpcoar:mimeType>text/plain</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:date dateType="Accepted">2022-10-20</datacite:date><datacite:version>1.0</datacite:version></jpcoar:file><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test2</jpcoar:URI><jpcoar:mimeType>application/octet-stream</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:version>1.2</datacite:version></jpcoar:file><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test3.png</jpcoar:URI><jpcoar:mimeType>image/png</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:version>2.1</datacite:version></jpcoar:file></jpcoar:jpcoar></metadata></record></GetRecord></OAI-PMH>'
        tree = etree.fromstring(xml_str)
        record = tree.findall("./GetRecord/record",namespaces=tree.nsmap)[0]
        xml = etree.tostring(record,encoding="utf-8").decode()
        item_type_name1 = ItemTypeName(
            id=10, name="Multiple", has_site_license=True, is_active=True
        )
        item_type1 = ItemType(
            id=10,name_id=10,harvesting_type=True,schema={},form={},render={},tag=1,version_id=1,is_deleted=False,
        )
        db.session.add(item_type_name1)
        db.session.add(item_type1)
        db.session.commit()
        mapper = JPCOARMapper(xml)
        assert hasattr(mapper,"itemtype")
        assert "Multiple" in BaseMapper.itemtype_map
    
#     def map(self):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::TestJPCOARMapper::test_map -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
    def test_map(self,db_itemtype):
        
        deleted_xml = '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2023-03-01T02:07:10Z</responseDate><request metadataPrefix="jpcoar_1.0" identifier="oai:weko3.example.org:00000001" verb="GetRecord">https://192.168.56.103/oai</request><GetRecord><record><header status="deleted"><identifier>oai:weko3.example.org:00000001</identifier><datestamp>2023-02-20T06:24:47Z</datestamp></header></record></GetRecord></OAI-PMH>'
        tree = etree.fromstring(deleted_xml)
        record = tree.findall("./GetRecord/record",namespaces=tree.nsmap)[0]
        xml = etree.tostring(record,encoding="utf-8").decode()
        mapper = JPCOARMapper(xml)
        mapper.itemtype = ItemType.query.filter_by(id=12).one()
        
        result = mapper.map()
        assert result == {}
        
        xml_str = '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><GetRecord><record><header><identifier>oai:weko3.example.org:00000001</identifier><datestamp>2023-02-20T06:24:47Z</datestamp><setSpec>1557819692844:1557819733276</setSpec><setSpec>1557820086539</setSpec></header><metadata><jpcoar:jpcoar xmlns:datacite="https://schema.datacite.org/meta/kernel-4/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcndl="http://ndl.go.jp/dcndl/terms/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:jpcoar="https://github.com/JPCOAR/schema/blob/master/1.0/" xmlns:oaire="http://namespace.openaire.eu/schema/oaire/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rioxxterms="http://www.rioxx.net/schema/v2.0/rioxxterms/" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="https://github.com/JPCOAR/schema/blob/master/1.0/" xsi:schemaLocation="https://github.com/JPCOAR/schema/blob/master/1.0/jpcoar_scm.xsd"><dc:title xml:lang="ja">test full item</dc:title><dcterms:alternative xml:lang="en">other title</dcterms:alternative><jpcoar:creator><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/1234" nameIdentifierScheme="ORCID">1234</jpcoar:nameIdentifier><jpcoar:creatorName xml:lang="ja">テスト, 太郎</jpcoar:creatorName><jpcoar:familyName xml:lang="ja">テスト</jpcoar:familyName><jpcoar:givenName xml:lang="ja">太郎</jpcoar:givenName><jpcoar:creatorAlternative xml:lang="ja">テスト　別郎</jpcoar:creatorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="http://www.isni.org/isni/5678" nameIdentifierScheme="ISNI">5678</jpcoar:nameIdentifier></jpcoar:affiliation></jpcoar:creator><jpcoar:contributor contributorType="ContactPerson"><jpcoar:nameIdentifier nameIdentifierURI="https://orcid.org/5678" nameIdentifierScheme="ORCID">5678</jpcoar:nameIdentifier><jpcoar:contributorName xml:lang="en">test, smith</jpcoar:contributorName><jpcoar:familyName xml:lang="en">test</jpcoar:familyName><jpcoar:givenName xml:lang="en">smith</jpcoar:givenName><jpcoar:contributorAlternative xml:lang="en">other smith</jpcoar:contributorAlternative><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="http://www.isni.org/isni/1234" nameIdentifierScheme="ISNI">1234</jpcoar:nameIdentifier></jpcoar:affiliation></jpcoar:contributor><dcterms:accessRights rdf:resource="http://purl.org/coar/access_right/c_14cb">metadata only access</dcterms:accessRights><rioxxterms:apc>Paid</rioxxterms:apc><dc:rights xml:lang="ja" rdf:resource="テスト権利情報Resource">テスト権利情報</dc:rights><jpcoar:rightsHolder><jpcoar:rightsHolderName xml:lang="ja">テスト　太郎</jpcoar:rightsHolderName></jpcoar:rightsHolder><jpcoar:subject xml:lang="ja" subjectURI="http://bsh.com" subjectScheme="BSH">テスト主題</jpcoar:subject><datacite:description xml:lang="en" descriptionType="Abstract">this is test abstract.</datacite:description><dc:publisher xml:lang="ja">test publisher</dc:publisher><datacite:date dateType="Accepted">2022-10-20</datacite:date><datacite:date dateType="Issued">2022-10-19</datacite:date><dc:language>jpn</dc:language><dc:type rdf:resource="http://purl.org/coar/resource_type/c_2fe3">newspaper</dc:type><datacite:version>1.1</datacite:version><oaire:version rdf:resource="http://purl.org/coar/version/c_b1a7d7d4d402bcce">AO</oaire:version><jpcoar:identifier identifierType="DOI">1111</jpcoar:identifier><jpcoar:identifier identifierType="DOI">https://doi.org/1234/0000000001</jpcoar:identifier><jpcoar:identifier identifierType="URI">https://192.168.56.103/records/1</jpcoar:identifier><jpcoar:identifierRegistration identifierType="JaLC">1234/0000000001</jpcoar:identifierRegistration><jpcoar:relation relationType="isVersionOf"><jpcoar:relatedIdentifier identifierType="ARK">1111111</jpcoar:relatedIdentifier><jpcoar:relatedTitle xml:lang="ja">関連情報テスト</jpcoar:relatedTitle></jpcoar:relation><jpcoar:relation relationType="isVersionOf"><jpcoar:relatedIdentifier identifierType="URI">https://192.168.56.103/records/3</jpcoar:relatedIdentifier></jpcoar:relation><dcterms:temporal xml:lang="ja">1 to 2</dcterms:temporal><datacite:geoLocation><datacite:geoLocationPoint><datacite:pointLongitude>12345</datacite:pointLongitude><datacite:pointLatitude>67890</datacite:pointLatitude></datacite:geoLocationPoint><datacite:geoLocationBox><datacite:westBoundLongitude>123</datacite:westBoundLongitude><datacite:eastBoundLongitude>456</datacite:eastBoundLongitude><datacite:southBoundLatitude>789</datacite:southBoundLatitude><datacite:northBoundLatitude>1112</datacite:northBoundLatitude></datacite:geoLocationBox><datacite:geoLocationPlace>テスト位置情報</datacite:geoLocationPlace></datacite:geoLocation><jpcoar:fundingReference><datacite:funderIdentifier funderIdentifierType="Crossref Funder">22222</datacite:funderIdentifier><jpcoar:funderName xml:lang="ja">テスト助成機関</jpcoar:funderName><datacite:awardNumber awardURI="https://test.research.com">1111</datacite:awardNumber><jpcoar:awardTitle xml:lang="ja">テスト研究</jpcoar:awardTitle></jpcoar:fundingReference><jpcoar:sourceIdentifier identifierType="PISSN">test source Identifier</jpcoar:sourceIdentifier><jpcoar:sourceTitle xml:lang="ja">test collectibles</jpcoar:sourceTitle><jpcoar:sourceTitle xml:lang="ja">test title book</jpcoar:sourceTitle><jpcoar:volume>5</jpcoar:volume><jpcoar:volume>1</jpcoar:volume><jpcoar:issue>2</jpcoar:issue><jpcoar:issue>2</jpcoar:issue><jpcoar:numPages>333</jpcoar:numPages><jpcoar:numPages>555</jpcoar:numPages><jpcoar:pageStart>123</jpcoar:pageStart><jpcoar:pageStart>789</jpcoar:pageStart><jpcoar:pageEnd>456</jpcoar:pageEnd><jpcoar:pageEnd>234</jpcoar:pageEnd><dcndl:dissertationNumber>9999</dcndl:dissertationNumber><dcndl:degreeName xml:lang="ja">テスト学位</dcndl:degreeName><dcndl:dateGranted>2022-10-19</dcndl:dateGranted><jpcoar:degreeGrantor><jpcoar:nameIdentifier nameIdentifierScheme="kakenhi">学位授与機関識別子テスト</jpcoar:nameIdentifier><jpcoar:degreeGrantorName xml:lang="ja">学位授与機関</jpcoar:degreeGrantorName></jpcoar:degreeGrantor><jpcoar:conference><jpcoar:conferenceName xml:lang="ja">テスト会議</jpcoar:conferenceName><jpcoar:conferenceSequence>12345</jpcoar:conferenceSequence><jpcoar:conferenceSponsor xml:lang="ja">テスト機関</jpcoar:conferenceSponsor><jpcoar:conferenceDate endDay="1" endYear="2005" endMonth="12" startDay="11" xml:lang="ja" startYear="2000" startMonth="4">12</jpcoar:conferenceDate><jpcoar:conferenceVenue xml:lang="ja">テスト会場</jpcoar:conferenceVenue><jpcoar:conferenceCountry>JPN</jpcoar:conferenceCountry></jpcoar:conference><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test1.txt</jpcoar:URI><jpcoar:mimeType>text/plain</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:date dateType="Accepted">2022-10-20</datacite:date><datacite:version>1.0</datacite:version></jpcoar:file><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test2</jpcoar:URI><jpcoar:mimeType>application/octet-stream</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:version>1.2</datacite:version></jpcoar:file><jpcoar:file><jpcoar:URI>https://weko3.example.org/record/1/files/test3.png</jpcoar:URI><jpcoar:mimeType>image/png</jpcoar:mimeType><jpcoar:extent>18 B</jpcoar:extent><datacite:version>2.1</datacite:version></jpcoar:file></jpcoar:jpcoar></metadata></record></GetRecord></OAI-PMH>'
        tree = etree.fromstring(xml_str)
        record = tree.findall("./GetRecord/record",namespaces=tree.nsmap)[0]
        xml = etree.tostring(record,encoding="utf-8").decode()
        mapper = JPCOARMapper(xml)
        mapper.itemtype = ItemType.query.filter_by(id=10).one()
        
        test = {'$schema': 10, 'pubdate': '2023-02-20', 'item_1551264308487': [{'subitem_1551255647225': 'test full item', 'subitem_1551255648112': 'ja'}], 'title': 'test full item', 'item_1551264326373': [{'subitem_1551255720400': 'other title', 'subitem_1551255721061': 'en'}], 'item_1551264340087': [{'subitem_1551255991424': [{'subitem_1551256006332': '太郎', 'subitem_1551256007414': 'ja'}], 'subitem_1551255929209': [{'subitem_1551255938498': 'テスト', 'subitem_1551255964991': 'ja'}], 'subitem_1551255898956': [{'subitem_1551255905565': 'テスト, 太郎', 'subitem_1551255907416': 'ja'}], 'subitem_1551256025394': [{'subitem_1551256035730': 'テスト\u3000別郎', 'subitem_1551256055588': 'ja'}]}], 'item_1551264418667': [{'subitem_1551257036415': 'ContactPerson', 'subitem_1551257339190': [{'subitem_1551257342360': '', 'subitem_1551257343979': 'en'}], 'subitem_1551257272214': [{'subitem_1551257314588': 'test', 'subitem_1551257316910': 'en'}], 'subitem_1551257245638': [{'subitem_1551257276108': 'test, smith', 'subitem_1551257279831': 'en'}], 'subitem_1551257372442': [{'subitem_1551257374288': 'other smith', 'subitem_1551257375939': 'en'}]}], 'item_1551264447183': [{'subitem_1551257553743': 'metadata only access', 'subitem_1551257578398': 'http://purl.org/coar/access_right/c_14cb'}], 'item_1551264605515': [{'subitem_1551257776901': 'Paid'}], 'item_1551264629907': [{'subitem_1551257025236': [{'subitem_1551257043769': 'テスト権利情報', 'subitem_1551257047388': 'ja'}], 'subitem_1551257030435': 'テスト権利情報Resource'}], 'item_1551264767789': [{'subitem_1551257249371': [{'subitem_1551257255641': 'テスト\u3000太郎', 'subitem_1551257257683': 'ja'}]}], 'item_1551264822581': [{'subitem_1551257315453': 'テスト主題', 'subitem_1551257323812': 'ja', 'subitem_1551257343002': 'http://bsh.com', 'subitem_1551257329877': 'BSH'}], 'item_1551264846237': [{'subitem_1551255577890': 'this is test abstract.', 'subitem_1551255592625': 'en', 'subitem_1551255637472': 'Abstract'}], 'item_1551264917614': [{'subitem_1551255702686': 'test publisher', 'subitem_1551255710277': 'ja'}], 'item_1551264974654': [{'subitem_1551255753471': '2022-10-20', 'subitem_1551255775519': 'Accepted'}, {'subitem_1551255753471': '2022-10-19', 'subitem_1551255775519': 'Issued'}], 'item_1551265002099': [{'subitem_1551255818386': 'jpn'}], 'item_1551265032053': [{'resourcetype': 'newspaper', 'resourceuri': 'http://purl.org/coar/resource_type/c_2fe3'}], 'item_1551265075370': [{'subitem_1551255975405': '1.1'}], 'item_1551265118680': [{'subitem_1551256025676': 'AO'}], 'system_identifier_doi': [{'subitem_systemidt_identifier': '1111', 'subitem_systemidt_identifier_type': 'DOI'}, {'subitem_systemidt_identifier': 'https://doi.org/1234/0000000001', 'subitem_systemidt_identifier_type': 'DOI'}, {'subitem_systemidt_identifier': 'https://192.168.56.103/records/1', 'subitem_systemidt_identifier_type': 'URI'}], 'item_1581495499605': [{'subitem_1551256250276': '1234/0000000001', 'subitem_1551256259586': 'JaLC'}], 'item_1551265227803': [{'subitem_1551256388439': 'isVersionOf', 'subitem_1551256480278': [{'subitem_1551256498531': '関連情報テスト', 'subitem_1551256513476': 'ja'}], 'subitem_1551256465077': [{'subitem_1551256478339': '1111111', 'subitem_1551256629524': 'ARK'}]}, {'subitem_1551256388439': 'isVersionOf', 'subitem_1551256465077': [{'subitem_1551256478339': 'https://192.168.56.103/records/3', 'subitem_1551256629524': 'URI'}]}], 'item_1551265302120': [{'subitem_1551256918211': '1 to 2', 'subitem_1551256920086': 'ja'}], 'item_1551265385290': [{'subitem_1551256462220': [{'subitem_1551256653656': 'テスト助成機関', 'subitem_1551256657859': 'ja'}], 'subitem_1551256454316': [{'subitem_1551256614960': '22222', 'subitem_1551256619706': 'Crossref Funder'}], 'subitem_1551256688098': [{'subitem_1551256691232': 'テスト研究', 'subitem_1551256694883': 'ja'}], 'subitem_1551256665850': [{'subitem_1551256671920': '1111', 'subitem_1551256679403': 'https://test.research.com'}]}], 'item_1551265409089': [{'subitem_1551256405981': 'test source Identifier', 'subitem_1551256409644': 'PISSN'}], 'item_1551265438256': [{'subitem_1551256349044': 'test collectibles', 'subitem_1551256350188': 'ja'}, {'subitem_1551256349044': 'test title book', 'subitem_1551256350188': 'ja'}], 'item_1551265463411': [{'subitem_1551256328147': '5'}, {'subitem_1551256328147': '1'}], 'item_1551265520160': [{'subitem_1551256294723': '2'}, {'subitem_1551256294723': '2'}], 'item_1551265553273': [{'subitem_1551256248092': '333'}, {'subitem_1551256248092': '555'}], 'item_1551265569218': [{'subitem_1551256198917': '123'}, {'subitem_1551256198917': '789'}, {'subitem_1551256198917': '456'}, {'subitem_1551256198917': '234'}], 'item_1551265738931': [{'subitem_1551256171004': '9999'}], 'item_1551265790591': [{'subitem_1551256126428': 'テスト学位', 'subitem_1551256129013': 'ja'}], 'item_1551265811989': [{'subitem_1551256096004': '2022-10-19'}], 'item_1551265903092': [{'subitem_1551256015892': [{'subitem_1551256027296': '学位授与機関識別子テスト', 'subitem_1551256029891': 'kakenhi'}], 'subitem_1551256037922': [{'subitem_1551256042287': '学位授与機関', 'subitem_1551256047619': 'ja'}]}], 'item_1551265973055': [{'subitem_1599711813532': 'JPN', 'subitem_1599711655652': '12345', 'subitem_1599711633003': [{'subitem_1599711636923': 'テスト会議', 'subitem_1599711645590': 'ja'}]}], 'item_1570069138259': [{'subitem_1551255854908': '1.0', 'subitem_1551255750794': 'text/plain', 'subitem_1551255788530': [{'subitem_1570068579439': '18 B'}], 'subitem_1551255820788': [{'subitem_1551255828320': '2022-10-20', 'subitem_1551255833133': 'Accepted'}], 'subitem_1551255558587': [{'subitem_1551255570271': 'https://weko3.example.org/record/1/files/test1.txt'}]}, {'subitem_1551255854908': '1.2', 'subitem_1551255750794': 'application/octet-stream', 'subitem_1551255788530': [{'subitem_1570068579439': '18 B'}], 'subitem_1551255558587': [{'subitem_1551255570271': 'https://weko3.example.org/record/1/files/test2'}]}, {'subitem_1551255854908': '2.1', 'subitem_1551255750794': 'image/png', 'subitem_1551255788530': [{'subitem_1570068579439': '18 B'}], 'subitem_1551255558587': [{'subitem_1551255570271': 'https://weko3.example.org/record/1/files/test3.png'}]}]}
        result = mapper.map()
        assert result == test

    # .tox/c1/bin/pytest -v --cov=invenio_oaiharvester tests/test_harvester.py::TestJPCOARMapper::test_map_2 -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
    def test_map_2(self,db_itemtype):
        xml_str = '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2023-06-15T08:09:48Z</responseDate><request metadataPrefix="jpcoar_2.0" identifier="oai:weko3.example.org:00000026" verb="GetRecord">https://localhost/oai</request><GetRecord><record><header><identifier>oai:weko3.example.org:00000026</identifier><datestamp>2023-06-15T08:01:19Z</datestamp><setSpec>1686726684832</setSpec></header><metadata><jpcoar:jpcoar xmlns:datacite="https://schema.datacite.org/meta/kernel-4/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcndl="http://ndl.go.jp/dcndl/terms/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:jpcoar="https://github.com/JPCOAR/schema/blob/master/2.0/" xmlns:oaire="http://namespace.openaire.eu/schema/oaire/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rioxxterms="http://www.rioxx.net/schema/v2.0/rioxxterms/" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="https://github.com/JPCOAR/schema/blob/master/2.0/" xsi:schemaLocation="https://github.com/JPCOAR/schema/blob/master/2.0/jpcoar_scm.xsd"><dc:title xml:lang="en">thesis_test_today</dc:title><jpcoar:creator creatorType="creator_type_test"><jpcoar:creatorName nameType="Personal" xml:lang="en">creator_name_test</jpcoar:creatorName><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="creator_aff_name_identifier_uri_test" nameIdentifierScheme="ROR">creator_aff_name_identifier</jpcoar:nameIdentifier><jpcoar:affiliationName xml:lang="en">creator_aff_name</jpcoar:affiliationName></jpcoar:affiliation></jpcoar:creator><jpcoar:contributor><jpcoar:contributorName nameType="Organizational" xml:lang="ja">contributor_name_test</jpcoar:contributorName><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="contrib_aff_name_id_uri_test" nameIdentifierScheme="GRID">contrib_aff_name_id_test</jpcoar:nameIdentifier><jpcoar:affiliationName xml:lang="en">contrib_aff_name_test</jpcoar:affiliationName></jpcoar:affiliation></jpcoar:contributor><jpcoar:subject xml:lang="en" subjectURI="subject_uri_test" subjectScheme="DDC">subject_test</jpcoar:subject><datacite:date>2023-06-15</datacite:date><dc:type rdf:resource="http://purl.org/coar/resource_type/c_46ec">thesis</dc:type><jpcoar:identifier identifierType="URI">https://localhost/records/26</jpcoar:identifier><jpcoar:relation relationType="inSeries"><jpcoar:relatedIdentifier identifierType="WOS">related_identifier_test</jpcoar:relatedIdentifier><jpcoar:relatedTitle xml:lang="en">related_title_test</jpcoar:relatedTitle></jpcoar:relation><jpcoar:fundingReference><jpcoar:funderIdentifier funderIdentifierType="Crossref Funder" funderIdentifierTypeURI="funder_identifier_type_uri_test">funder_identifier_test</jpcoar:funderIdentifier><jpcoar:awardNumber awardURI="award_number_uri_test" awardNumberType="JGN">award_number_test</jpcoar:awardNumber><jpcoar:fundingStreamIdentifier fundingStreamIdentifierType="Crossref Funder" fundingStreamIdentifierTypeURI="funding_stream_identifier_type_uri_test">funding_stream_identifier_test</jpcoar:fundingStreamIdentifier><jpcoar:fundingStream xml:lang="en">funding_stream_test</jpcoar:fundingStream></jpcoar:fundingReference><jpcoar:publisher><jpcoar:publisherName xml:lang="en">publisher_test</jpcoar:publisherName><jpcoar:publisherDescription xml:lang="ja">description_test</jpcoar:publisherDescription><dcndl:location>location_test</dcndl:location><dcndl:publicationPlace>publication_place_test</dcndl:publicationPlace></jpcoar:publisher><dcterms:date>2016</dcterms:date><dcndl:edition xml:lang="en">edition_test</dcndl:edition><dcndl:volumeTitle xml:lang="ja">volume_title_test</dcndl:volumeTitle><dcndl:originalLanguage>original_language_test</dcndl:originalLanguage><dcterms:extent xml:lang="en">extent_test</dcterms:extent><jpcoar:format xml:lang="en">format_test</jpcoar:format><jpcoar:holdingAgent><jpcoar:holdingAgentNameIdentifier nameIdentifierURI="holding_agent_name_identifier_uri_test" nameIdentifierScheme="ROR">holding_agent_name_identifier_test</jpcoar:holdingAgentNameIdentifier><jpcoar:holdingAgentName xml:lang="en">holding_agent_name_test</jpcoar:holdingAgentName></jpcoar:holdingAgent><jpcoar:datasetSeries>True</jpcoar:datasetSeries><jpcoar:catalog><jpcoar:contributor contributorType="HostingInstitution"><jpcoar:contributorName xml:lang="en">catalog_contributor_test</jpcoar:contributorName></jpcoar:contributor><jpcoar:identifier identifierType="DOI">catalog_identifier_test</jpcoar:identifier><dc:title xml:lang="en">catalog_title_test</dc:title><datacite:description xml:lang="ja" descriptionType="Abstract">catalog_description_test</datacite:description><jpcoar:subject xml:lang="en" subjectURI="catalog_subject_uri_test" subjectScheme="DDC">catalog_subject_test</jpcoar:subject><jpcoar:license xml:lang="en" licenseType="file" rdf:resource="catalog_rdf_license_test">catalog_license_test</jpcoar:license><dc:rights xml:lang="en" rdf:resource="catalog_rdf_rights_test">catalog_rights_test</dc:rights><dcterms:accessRights rdf:resource="catalog_rdf_access_rights_test">metadata only access</dcterms:accessRights><jpcoar:file><jpcoar:URI objectType="open access">catalog_file_test</jpcoar:URI></jpcoar:file></jpcoar:catalog></jpcoar:jpcoar></metadata></record></GetRecord></OAI-PMH>'
        tree = etree.fromstring(xml_str)
        record = tree.findall("./GetRecord/record",namespaces=tree.nsmap)[0]
        xml = etree.tostring(record,encoding="utf-8").decode()
        mapper = JPCOARMapper(xml)
        mapper.json["record"]["metadata"]["jpcoar:jpcoar"] = OrderedDict(
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
                ("dc:title", OrderedDict([("@xml:lang", "ja"), ("#text", "test full item")])),
                (
                    "dcterms:alternative",
                    OrderedDict([("@xml:lang", "en"), ("#text", "other title")]),
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
        result = mapper.map()

        # assert condition will be updated once update_item_type.py be updated with jpcoar2 properties created
        # right now jpcoar2 items added to harvester.py is being covered by this test case and there are no errors
        # 
        assert result

    # .tox/c1/bin/pytest -v --cov=invenio_oaiharvester tests/test_harvester.py::TestJPCOARMapper::test_map_3 -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
    def test_map_3(self,db_itemtype):
        xml_str = '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2023-06-15T08:09:48Z</responseDate><request metadataPrefix="jpcoar_2.0" identifier="oai:weko3.example.org:00000026" verb="GetRecord">https://localhost/oai</request><GetRecord><record><header><identifier>oai:weko3.example.org:00000026</identifier><datestamp>2023-06-15T08:01:19Z</datestamp><setSpec>1686726684832</setSpec></header><metadata><jpcoar:jpcoar xmlns:datacite="https://schema.datacite.org/meta/kernel-4/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcndl="http://ndl.go.jp/dcndl/terms/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:jpcoar="https://github.com/JPCOAR/schema/blob/master/2.0/" xmlns:oaire="http://namespace.openaire.eu/schema/oaire/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rioxxterms="http://www.rioxx.net/schema/v2.0/rioxxterms/" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="https://github.com/JPCOAR/schema/blob/master/2.0/" xsi:schemaLocation="https://github.com/JPCOAR/schema/blob/master/2.0/jpcoar_scm.xsd"><dc:title xml:lang="en">thesis_test_today</dc:title><jpcoar:creator creatorType="creator_type_test"><jpcoar:creatorName nameType="Personal" xml:lang="en">creator_name_test</jpcoar:creatorName><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="creator_aff_name_identifier_uri_test" nameIdentifierScheme="ROR">creator_aff_name_identifier</jpcoar:nameIdentifier><jpcoar:affiliationName xml:lang="en">creator_aff_name</jpcoar:affiliationName></jpcoar:affiliation></jpcoar:creator><jpcoar:contributor><jpcoar:contributorName nameType="Organizational" xml:lang="ja">contributor_name_test</jpcoar:contributorName><jpcoar:affiliation><jpcoar:nameIdentifier nameIdentifierURI="contrib_aff_name_id_uri_test" nameIdentifierScheme="GRID">contrib_aff_name_id_test</jpcoar:nameIdentifier><jpcoar:affiliationName xml:lang="en">contrib_aff_name_test</jpcoar:affiliationName></jpcoar:affiliation></jpcoar:contributor><jpcoar:subject xml:lang="en" subjectURI="subject_uri_test" subjectScheme="DDC">subject_test</jpcoar:subject><datacite:date>2023-06-15</datacite:date><dc:type rdf:resource="http://purl.org/coar/resource_type/c_46ec">thesis</dc:type><jpcoar:identifier identifierType="URI">https://localhost/records/26</jpcoar:identifier><jpcoar:relation relationType="inSeries"><jpcoar:relatedIdentifier identifierType="WOS">related_identifier_test</jpcoar:relatedIdentifier><jpcoar:relatedTitle xml:lang="en">related_title_test</jpcoar:relatedTitle></jpcoar:relation><jpcoar:fundingReference><jpcoar:funderIdentifier funderIdentifierType="Crossref Funder" funderIdentifierTypeURI="funder_identifier_type_uri_test">funder_identifier_test</jpcoar:funderIdentifier><jpcoar:awardNumber awardURI="award_number_uri_test" awardNumberType="JGN">award_number_test</jpcoar:awardNumber><jpcoar:fundingStreamIdentifier fundingStreamIdentifierType="Crossref Funder" fundingStreamIdentifierTypeURI="funding_stream_identifier_type_uri_test">funding_stream_identifier_test</jpcoar:fundingStreamIdentifier><jpcoar:fundingStream xml:lang="en">funding_stream_test</jpcoar:fundingStream></jpcoar:fundingReference><jpcoar:publisher><jpcoar:publisherName xml:lang="en">publisher_test</jpcoar:publisherName><jpcoar:publisherDescription xml:lang="ja">description_test</jpcoar:publisherDescription><dcndl:location>location_test</dcndl:location><dcndl:publicationPlace>publication_place_test</dcndl:publicationPlace></jpcoar:publisher><dcterms:date>2016</dcterms:date><dcndl:edition xml:lang="en">edition_test</dcndl:edition><dcndl:volumeTitle xml:lang="ja">volume_title_test</dcndl:volumeTitle><dcndl:originalLanguage>original_language_test</dcndl:originalLanguage><dcterms:extent xml:lang="en">extent_test</dcterms:extent><jpcoar:format xml:lang="en">format_test</jpcoar:format><jpcoar:holdingAgent><jpcoar:holdingAgentNameIdentifier nameIdentifierURI="holding_agent_name_identifier_uri_test" nameIdentifierScheme="ROR">holding_agent_name_identifier_test</jpcoar:holdingAgentNameIdentifier><jpcoar:holdingAgentName xml:lang="en">holding_agent_name_test</jpcoar:holdingAgentName></jpcoar:holdingAgent><jpcoar:datasetSeries>True</jpcoar:datasetSeries><jpcoar:catalog><jpcoar:contributor contributorType="HostingInstitution"><jpcoar:contributorName xml:lang="en">catalog_contributor_test</jpcoar:contributorName></jpcoar:contributor><jpcoar:identifier identifierType="DOI">catalog_identifier_test</jpcoar:identifier><dc:title xml:lang="en">catalog_title_test</dc:title><datacite:description xml:lang="ja" descriptionType="Abstract">catalog_description_test</datacite:description><jpcoar:subject xml:lang="en" subjectURI="catalog_subject_uri_test" subjectScheme="DDC">catalog_subject_test</jpcoar:subject><jpcoar:license xml:lang="en" licenseType="file" rdf:resource="catalog_rdf_license_test">catalog_license_test</jpcoar:license><dc:rights xml:lang="en" rdf:resource="catalog_rdf_rights_test">catalog_rights_test</dc:rights><dcterms:accessRights rdf:resource="catalog_rdf_access_rights_test">metadata only access</dcterms:accessRights><jpcoar:file><jpcoar:URI objectType="open access">catalog_file_test</jpcoar:URI></jpcoar:file></jpcoar:catalog></jpcoar:jpcoar></metadata></record></GetRecord></OAI-PMH>'
        tree = etree.fromstring(xml_str)
        record = tree.findall("./GetRecord/record",namespaces=tree.nsmap)[0]
        xml = etree.tostring(record,encoding="utf-8").decode()
        mapper = JPCOARMapper(xml)
        mapper.json["record"]["metadata"]["jpcoar:jpcoar"] = OrderedDict(
            [
                (
                    "dcndl:edition",
                    OrderedDict(
                        [
                            ("@xml:lang", "ja"),
                            ("#text", "edition_test"),
                        ]
                    )
                ),
            ]
        )
        result = mapper.map()

        # assert condition will be updated once update_item_type.py be updated with jpcoar2 properties created
        # right now jpcoar2 items added to harvester.py is being covered by this test case and there are no errors
        # 
        assert result 

# class DDIMapper(BaseMapper):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::TestDDIMapper -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
class TestDDIMapper:
#     def __init__(self, xml):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::TestDDIMapper::test_init -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
    def test_init(self,app,db):
        xml_str = '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2023-03-02T04:08:53Z</responseDate><request metadataPrefix="ddi" verb="GetRecord" identifier="oai:weko3.example.org:00000075">https://192.168.56.103/oai</request><GetRecord><record><header><identifier>oai:weko3.example.org:00000075</identifier><datestamp>2023-03-02T04:06:46Z</datestamp><setSpec>1557820086539</setSpec></header><metadata><codeBook xmlns:dc="http://purl.org/dc/terms/" xmlns:fn="http://www.w3.org/2005/xpath-functions" xmlns:saxon="http://xml.apache.org/xslt" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="ddi:codebook:2_5" xsi:schemaLocation="https://ddialliance.org/Specification/DDI-Codebook/2.5/XMLSchema/codebook.xsd"><stdyDscr><citation xml:lang="ja"><titlStmt><titl xml:lang="ja">test ddi full item</titl><altTitl xml:lang="ja">other ddi title</altTitl><IDNo agency="test_id_agency" xml:lang="ja">test_study_id</IDNo></titlStmt><rspStmt><AuthEnty ID="4" xml:lang="ja" affiliation="author.affiliation">テスト, 太郎</AuthEnty></rspStmt><prodStmt><producer xml:lang="ja">test_publisher</producer><copyright xml:lang="ja">test_rights</copyright><fundAg ID="test_found_ageny" xml:lang="ja">test_founder_name</fundAg><grantNo>test_grant_no</grantNo></prodStmt><distStmt><distrbtr URI="https://test.distributor.affiliation" abbr="TDN" xml:lang="ja" affiliation="Test Distributor Affiliation">Test Distributor Name</distrbtr></distStmt><serStmt><serName xml:lang="ja">test_series</serName></serStmt><verStmt><version date="2023-03-07" xml:lang="ja">1.2</version></verStmt><biblCit xml:lang="ja">test.input.content</biblCit><holdings URI="https://192.168.56.103/records/75"/></citation><stdyInfo xml:lang="ja"><subject><topcClas vocab="test_topic_vocab" vocabURI="http://test.topic.vocab" xml:lang="ja">Test Topic</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">人口</topcClas></subject><sumDscr><timePrd event="start">2023-03-01</timePrd><timePrd event="end">2023-03-03</timePrd><collDate event="start">2023-03-01</collDate><collDate event="end">2023-03-06</collDate><geogCover xml:lang="ja">test_geographic_coverage</geogCover><anlyUnit xml:lang="ja">個人</anlyUnit><universe xml:lang="ja">test parent set</universe><dataKind xml:lang="ja">量的調査</dataKind></sumDscr></stdyInfo><stdyInfo xml:lang="en"><subject><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Demography</topcClas></subject><abstract xml:lang="en">this is description for ddi item. this is description for ddi item.</abstract><sumDscr><timePrd event="start">2023-03-01</timePrd><timePrd event="end">2023-03-03</timePrd><collDate event="start">2023-03-01</collDate><collDate event="end">2023-03-06</collDate><anlyUnit xml:lang="en">test_unit_of_analysis</anlyUnit><anlyUnit xml:lang="en">Individual</anlyUnit><dataKind xml:lang="en">quantatitive research</dataKind></sumDscr></stdyInfo><method xml:lang="ja"><dataColl><sampProc xml:lang="ja">test sampling procedure</sampProc><sampProc xml:lang="ja">母集団/ 全数調査</sampProc><collMode xml:lang="ja">test collection method</collMode><collMode xml:lang="ja">インタビュー</collMode></dataColl><anlyInfo><respRate xml:lang="ja">test sampling procedure_sampling_rate</respRate></anlyInfo></method><method xml:lang="en"><dataColl><sampProc xml:lang="en">Total universe/Complete enumeration</sampProc><collMode xml:lang="en">Interview</collMode></dataColl><anlyInfo/></method><dataAccs xml:lang="jp"><setAvail><avlStatus xml:lang="jp">オープンアクセス</avlStatus></setAvail><notes>jpn</notes></dataAccs><dataAccs xml:lang="en"><setAvail><avlStatus xml:lang="en">open access</avlStatus></setAvail><notes>jpn</notes></dataAccs><othrStdyMat xml:lang="ja"><relStdy ID="test_related_study_identifier" xml:lang="ja">test_related_study_title</relStdy><relPubl ID="test_related_publication_identifier" xml:lang="ja">test_related_publication_title</relPubl></othrStdyMat></stdyDscr></codeBook></metadata></record></GetRecord></OAI-PMH>'
        tree = etree.fromstring(xml_str)
        record = tree.findall("./GetRecord/record",namespaces=tree.nsmap)[0]
        xml = etree.tostring(record,encoding="utf-8").decode()
        item_type_name1 = ItemTypeName(
            id=10, name="Multiple", has_site_license=True, is_active=True
        )
        item_type1 = ItemType(
            id=10,name_id=10,harvesting_type=True,schema={},form={},render={},tag=1,version_id=1,is_deleted=False,
        )
        db.session.add(item_type_name1)
        db.session.add(item_type1)
        db.session.commit()
        mapper = DDIMapper(xml)
        assert hasattr(mapper,"itemtype")
        assert "Multiple" in BaseMapper.itemtype_map
        assert mapper.record_title == ""
        
#     def ddi_harvest_processing(self, harvest_data, res):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::TestDDIMapper::test_ddi_harvest_processing -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
    def test_ddi_harvest_processing(self,db_itemtype):
        data = OrderedDict([
            ('@xmlns:dc', 'http://purl.org/dc/terms/'), 
            ('@xmlns:fn', 'http://www.w3.org/2005/xpath-functions'), 
            ('@xmlns:saxon', 'http://xml.apache.org/xslt'), 
            ('@xmlns:xhtml', 'http://www.w3.org/1999/xhtml'), 
            ('@xmlns:xs', 'http://www.w3.org/2001/XMLSchema'), 
            ('@xmlns', 'ddi:codebook:2_5'), 
            ('@xsi:schemaLocation', 'https://ddialliance.org/Specification/DDI-Codebook/2.5/XMLSchema/codebook.xsd'), 
            ('stdyDscr', OrderedDict([
                ('citation', OrderedDict([
                    ('@xml:lang', 'ja'), 
                    ('titlStmt', [
                        'titlSmt_top1',
                        'titlSmt_top2',
                        OrderedDict([
                        ('titl', OrderedDict([
                            ('@xml:lang', 'ja'), 
                            ('#text', 'test ddi full item'),
                        ])), 
                        ('altTitl', OrderedDict([
                            ('@xml:lang', 'ja'), 
                            ('#text', 'other ddi title')
                        ])), 
                        ('IDNo', OrderedDict([
                            ('@agency', 'test_id_agency'), 
                            ('@xml:lang', 'ja'), 
                            ('#text', 'test_study_id')
                        ]))
                    ])]), 
                    ('rspStmt', OrderedDict([
                        ('AuthEnty', OrderedDict([
                            ('@ID', '4'), 
                            ('@xml:lang', 'ja'), 
                            ('@affiliation', 'author.affiliation'), 
                            ('#text', 'テスト, 太郎')
                        ]))
                    ])), 
                    ('rspStmt', OrderedDict([
                        ('AuthEnty', OrderedDict([
                            ('@ID', '4'), 
                            ('@xml:lang', 'ja'), 
                            ('@affiliation', 'author.affiliation'), 
                            ('#text', 'テスト, 太郎')
                        ]))
                    ])),
                    ('prodStmt', OrderedDict([
                        ('producer', OrderedDict([
                            ('@xml:lang', 'ja'), 
                            ('#text', 'test_publisher')
                        ])), 
                        ('copyright', OrderedDict([
                            ('@xml:lang', 'ja'),
                            ('@description','this is rights description.'),
                            ('@from','today'),
                            ('#text', 'test_rights')
                        ])), 
                        ('fundAg', OrderedDict([
                            ('@ID', 'test_found_ageny'), 
                            ('@xml:lang', 'ja'), 
                            ('#text', 'test_founder_name')
                        ])), 
                        ('grantNo', 'test_grant_no')
                    ])), 
                    ('distStmt', OrderedDict([
                        ('distrbtr', OrderedDict([
                            ('@URI', 'https://test.distributor.affiliation'), 
                            ('@abbr', 'TDN'), 
                            ('@xml:lang', 'ja'), 
                            ('@affiliation', 'Test Distributor Affiliation'), 
                            ('#text', 'Test Distributor Name')
                        ]))
                    ])),
                    ('serStmt', OrderedDict([
                        ('serName', OrderedDict([
                            ('@xml:lang', 'ja'),
                            ('#text', 'test_series')
                        ]))
                    ])), 
                    ('notes', OrderedDict([
                        ('#text','test_text'),
                        ('@sub_text','sub_test_text')
                    ])),
                    ('verStmt', OrderedDict([
                        ('version', OrderedDict([
                            ('@date', '2023-03-07'), 
                            ('@xml:lang', 'ja'), 
                            ('#text', '1.2')
                        ]))
                    ])), 
                    ('biblCit', OrderedDict([
                        ('@xml:lang', 'ja'), 
                        ('#text', 'test.input.content')
                    ])), 
                    ('holdings', [
                        OrderedDict([
                            ('@URI', 'https://192.168.56.103/records/75')
                        ]),
                        OrderedDict([
                            ('#text','http://doi.org/test_doi')
                        ]),
                        OrderedDict([
                            ('#text','http://hdl.handle.net/test_doi')
                        ]),
                        OrderedDict([
                            ('#text','http://other_prefix')
                        ])
                    ])
                ])), 
                ('stdyInfo', [
                    OrderedDict([
                        ('@xml:lang', 'ja'), 
                        ('subject', OrderedDict([
                            ('topcClas', [
                                OrderedDict([
                                    ('@vocab', 'test_topic_vocab'), 
                                    ('@vocabURI', 'http://test.topic.vocab'), 
                                    ('@xml:lang', 'ja'), 
                                    ('#text', 'Test Topic')
                                ]), 
                                OrderedDict([
                                    ('@vocab', 'CESSDA Topic Classification'), 
                                    ('@vocabURI', 'https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification'), 
                                    ('@xml:lang', 'ja'), 
                                    ('#text', '人口')
                                ]),
                                "test_str_value"
                            ])
                        ])), 
                        ('sumDscr', OrderedDict([
                            ('timePrd', [
                                OrderedDict([
                                    ('@event', 'start'), 
                                    ('#text', '2023-03-01')
                                ]), 
                                OrderedDict([
                                    ('@event', 'end'), 
                                    ('#text', '2023-03-03')
                                ])
                            ]), 
                            ('collDate', [
                                OrderedDict([
                                    ('@event', 'start'), 
                                    ('#text', '2023-03-01')
                                ]), 
                                OrderedDict([
                                    ('@event', 'end'), 
                                    ('#text', '2023-03-06')
                                ])
                            ]), 
                            ('geogCover', OrderedDict([
                                ('@xml:lang', 'ja'), 
                                ('#text', 'test_geographic_coverage')
                            ])), 
                            ('anlyUnit', OrderedDict([
                                ('@xml:lang', 'ja'), 
                                ('#text', '個人')
                            ])), 
                            ('universe', OrderedDict([
                                ('@xml:lang', 'ja'), 
                                ('#text', 'test parent set')
                            ])), 
                            ('dataKind', OrderedDict([
                                ('@xml:lang', 'ja'), 
                                ('#text', '量的調査')
                            ]))
                        ]))
                    ]), 
                    OrderedDict([
                        ('@xml:lang', 'en'), 
                        ('subject', OrderedDict([
                            ('topcClas', OrderedDict([
                                ('@vocab', 'CESSDA Topic Classification'), 
                                ('@vocabURI', 'https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification'), 
                                ('@xml:lang', 'en'), 
                                ('#text', 'Demography')
                            ]))
                        ])), 
                        ('abstract', [
                            OrderedDict([
                                ('@xml:lang', 'en'), 
                                ('@subvalue','this is description for ddi item.\nthis is description for ddi item.'),
                                ('#text', '<p>this is description for ddi item.</p> \n<p>this is description for ddi item.</p>')
                            ]),
                            ]), 
                        ('sumDscr', OrderedDict([
                            ('timePrd', [
                                OrderedDict([
                                    ('@event', 'start'), 
                                    ('#text', '2023-03-01')
                                ]), 
                                OrderedDict([
                                    ('@event', 'end'), 
                                    ('#text', '2023-03-03')
                                ])
                            ]), 
                            ('collDate', [
                                OrderedDict([
                                    ('@event', 'start'), 
                                    ('#text', '2023-03-01')
                                ]), 
                                OrderedDict([
                                    ('@event', 'end'), 
                                    ('#text', '2023-03-06')
                                ])
                            ]), 
                            ('anlyUnit', [
                                OrderedDict([
                                    ('@xml:lang', 'en'), 
                                    ('#text', 'test_unit_of_analysis')
                                ]), 
                                OrderedDict([
                                    ('@xml:lang', 'en'), 
                                    ('#text', 'Individual')
                                ])
                            ]), 
                            ('dataKind', OrderedDict([
                                ('@xml:lang', 'en'), 
                                ('#text', 'quantatitive research')
                            ]))
                        ]))
                    ])
                ]), 
                ('method', [
                    OrderedDict([
                        ('@xml:lang', 'ja'), 
                        ('dataColl', OrderedDict([
                            ('sampProc', [
                                OrderedDict([
                                    ('@xml:lang', 'ja'), 
                                    ('#text', 'test sampling procedure')
                                ]), 
                                OrderedDict([
                                    ('@xml:lang', 'ja'), 
                                    ('#text', '母集団/ 全数調査')
                                ])
                            ]), 
                            ('collMode', [
                                OrderedDict([
                                    ('@xml:lang', 'ja'), 
                                    ('#text', 'test collection method')
                                ]), 
                                OrderedDict([
                                    ('@xml:lang', 'ja'), 
                                    ('#text', 'インタビュー')
                                ])
                            ])
                        ])), 
                        ('anlyInfo', OrderedDict([
                            ('respRate', OrderedDict([
                                ('@xml:lang', 'ja'), 
                                ('#text', 'test sampling procedure_sampling_rate')
                            ]))
                        ]))
                    ]), 
                    OrderedDict([
                        ('@xml:lang', 'en'), 
                        ('dataColl', OrderedDict([
                            ('sampProc', OrderedDict([
                                ('@xml:lang', 'en'), 
                                ('#text', 'Total universe/Complete enumeration')
                            ])), 
                            ('collMode', OrderedDict([
                                ('@xml:lang', 'en'), 
                                ('#text', 'Interview')
                            ]))
                        ])), 
                        ('anlyInfo', None)
                    ])
                ]), 
                ('dataAccs', [
                    OrderedDict([
                        ('@xml:lang', 'jp'), 
                        ('setAvail', OrderedDict([
                            ('avlStatus', OrderedDict([
                                ('@xml:lang', 'jp'), 
                                ('#text', 'オープンアクセス')
                            ]))
                        ])), 
                        ('notes', 'jpn')
                    ]), 
                    OrderedDict([
                        ('@xml:lang', 'en'), 
                        ('setAvail', OrderedDict([
                            ('avlStatus', OrderedDict([
                                ('@xml:lang', 'en'), 
                                ('#text', 'open access')
                            ]))
                        ])), 
                        ('notes', 'jpn')
                    ])
                ]),
                ('othrStdyMat', OrderedDict([
                    ('@xml:lang', 'ja'), 
                    ('relStdy', OrderedDict([
                        ('@ID', 'test_related_study_identifier'), 
                        ('@xml:lang', 'ja'), 
                        ('#text', 'test_related_study_title')
                    ]))
                    #('relPubl', OrderedDict([
                    #    ('@ID', 'test_related_publication_identifier'), 
                    #    ('@xml:lang', 'ja'), 
                    #    ('#text', 'test_related_publication_title')
                    #]))
                ]))
            ])),
            ('stdyDscr.othrStdyMat.relStdy',OrderedDict([
                ('@ID', 'test_related_study_identifier_out1'), 
                ('@xml:lang', 'ja'), 
                ('#text', 'test_related_study_title')
            ])),
            ('stdyDscr.othrStdyMat.relPubl',OrderedDict([
                        ('@ID', 'test_related_publication_identifier_out1'), 
                        ('@xml:lang', 'ja'), 
                        ('#text', 'test_related_publication_title_out')])),
            ('stdyDscr.citation.holdings',[OrderedDict([
                            ('#text', 'test_url')
                        ])])
            
        ])
        xml_str = '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2023-03-02T04:08:53Z</responseDate><request metadataPrefix="ddi" verb="GetRecord" identifier="oai:weko3.example.org:00000075">https://192.168.56.103/oai</request><GetRecord><record><header><identifier>oai:weko3.example.org:00000075</identifier><datestamp>2023-03-02T04:06:46Z</datestamp><setSpec>1557820086539</setSpec></header><metadata><codeBook xmlns:dc="http://purl.org/dc/terms/" xmlns:fn="http://www.w3.org/2005/xpath-functions" xmlns:saxon="http://xml.apache.org/xslt" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="ddi:codebook:2_5" xsi:schemaLocation="https://ddialliance.org/Specification/DDI-Codebook/2.5/XMLSchema/codebook.xsd"><stdyDscr><citation xml:lang="ja"><titlStmt><titl xml:lang="ja">test ddi full item</titl><altTitl xml:lang="ja">other ddi title</altTitl><IDNo agency="test_id_agency" xml:lang="ja">test_study_id</IDNo></titlStmt><rspStmt><AuthEnty ID="4" xml:lang="ja" affiliation="author.affiliation">テスト, 太郎</AuthEnty><AuthEnty ID="4" xml:lang="ja" affiliation="author.affiliation">テスト, 太郎</AuthEnty></rspStmt><prodStmt><producer xml:lang="ja">test_publisher</producer><copyright xml:lang="ja" description="this is rights description." from="today">test_rights</copyright><fundAg ID="test_found_ageny" xml:lang="ja">test_founder_name</fundAg><grantNo>test_grant_no</grantNo></prodStmt><distStmt><distrbtr URI="https://test.distributor.affiliation" abbr="TDN" xml:lang="ja" affiliation="Test Distributor Affiliation">Test Distributor Name</distrbtr></distStmt><serStmt><serName xml:lang="ja">test_series</serName></serStmt><notes sub_text="sub_test_text">test_text</notes><verStmt><version date="2023-03-07" xml:lang="ja">1.2</version></verStmt><biblCit xml:lang="ja">test.input.content</biblCit><holdings URI="https://192.168.56.103/records/75" /><holdings>http://doi.org/test_doi</holdings><holdings>http://hdl.handle.net/test_doi</holdings><holdings>http://other_prefix</holdings></citation><stdyInfo xml:lang="ja"><subject><topcClas vocab="test_topic_vocab" vocabURI="http://test.topic.vocab" xml:lang="ja">Test Topic</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">人口</topcClas></subject><sumDscr><timePrd event="start">2023-03-01</timePrd><timePrd event="end">2023-03-03</timePrd><collDate event="start">2023-03-01</collDate><collDate event="end">2023-03-06</collDate><geogCover xml:lang="ja">test_geographic_coverage</geogCover><anlyUnit xml:lang="ja">個人</anlyUnit><universe xml:lang="ja">test parent set</universe><dataKind xml:lang="ja">量的調査</dataKind></sumDscr></stdyInfo><stdyInfo xml:lang="en"><subject><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Demography</topcClas></subject><abstract xml:lang="en" subvalue="this is description for ddi item.\nthis is description for ddi item.">this is description for ddi item. this is description for ddi item.</abstract><sumDscr><timePrd event="start">2023-03-01</timePrd><timePrd event="end">2023-03-03</timePrd><collDate event="start">2023-03-01</collDate><collDate event="end">2023-03-06</collDate><anlyUnit xml:lang="en">test_unit_of_analysis</anlyUnit><anlyUnit xml:lang="en">Individual</anlyUnit><dataKind xml:lang="en">quantatitive research</dataKind></sumDscr></stdyInfo><method xml:lang="ja"><dataColl><sampProc xml:lang="ja">test sampling procedure</sampProc><sampProc xml:lang="ja">母集団/ 全数調査</sampProc><collMode xml:lang="ja">test collection method</collMode><collMode xml:lang="ja">インタビュー</collMode></dataColl><anlyInfo><respRate xml:lang="ja">test sampling procedure_sampling_rate</respRate></anlyInfo></method><method xml:lang="en"><dataColl><sampProc xml:lang="en">Total universe/Complete enumeration</sampProc><collMode xml:lang="en">Interview</collMode></dataColl><anlyInfo /></method><dataAccs xml:lang="jp"><setAvail><avlStatus xml:lang="jp">オープンアクセス</avlStatus></setAvail><notes>jpn</notes></dataAccs><dataAccs xml:lang="en"><setAvail><avlStatus xml:lang="en">open access</avlStatus></setAvail><notes>jpn</notes></dataAccs><othrStdyMat xml:lang="ja"><relStdy ID="test_related_study_identifier" xml:lang="ja">test_related_study_title</relStdy><relPubl ID="test_related_publication_identifier" xml:lang="ja">test_related_publication_title</relPubl></othrStdyMat></stdyDscr></codeBook></metadata></record></GetRecord></OAI-PMH>'
        tree = etree.fromstring(xml_str)
        record = tree.findall("./GetRecord/record",namespaces=tree.nsmap)[0]
        xml = etree.tostring(record,encoding="utf-8").decode()
        mapper = DDIMapper(xml)
        mapper.map_itemtype('codeBook')
        test = {'$schema': 11, 'pubdate': str(mapper.datestamp()), 'item_1586157591881': [{'subitem_1586156939407': 'titlSmt_top1'}, {'subitem_1586156939407': 'titlSmt_top2'}, {'subitem_1586156939407': 'test_study_id', 'subitem_1591256665864': 'test_id_agency', 'subitem_1586311767281': 'ja'}], 'item_1551264308487': [{'subitem_1551255647225': 'test ddi full item', 'subitem_1551255648112': 'ja'}], 'item_1551264326373': [{'subitem_1551255720400': 'other ddi title', 'subitem_1551255721061': 'ja'}], 'item_1593074267803': [{'creatorNames': [{'creatorName': 'テスト, 太郎', 'creatorNameLang': 'ja'}], 'nameIdentifiers': [{'nameIdentifier': '4'}], 'creatorAffiliations': [{'affiliationNames': [{'affiliationName': 'author.affiliation'}]}]}], 'item_1551264917614': [{'subitem_1551255702686': 'test_publisher', 'subitem_1551255710277': 'ja'}], 'item_1551264629907': [{'subitem_1602213569986': {'subitem_1602213569987': 'test_rights'}, 'subitem_1602213570623': 'ja', 'subitem_1602213569989': {'subitem_1602213569990': {'subitem_1602213569988': 'this is rights description.'}}, 'subitem_1602213569991': {'subitem_1602213569992': 'today'}}], 'item_1602145817646': [{'subitem_1602142814330': 'test_founder_name', 'subitem_1602142815328': 'ja'}], 'item_1602145850035': [{'subitem_1602142123771': 'test_grant_no'}], 'item_1592405734122': [{'subitem_1592369405220': 'Test Distributor Name', 'subitem_1591320914113': 'https://test.distributor.affiliation', 'subitem_1591320889728': 'TDN', 'subitem_1592369407829': 'ja', 'subitem_1591320890384': 'Test Distributor Affiliation'}], 'item_1588254290498': [{'subitem_1587462181884': 'test_series', 'subitem_1587462183075': 'ja'}], 'item_1645678901234': [{'interim': 'test_text', 'subitem_165678901234567': 'sub_test_text'}], 'item_1551265075370': [{'subitem_1591254914934': '1.2', 'subitem_1591254915862': '2023-03-07', 'subitem_1591254915406': 'ja'}], 'item_1592880868902': [{'subitem_1586228465211': 'test.input.content', 'subitem_1586228490356': 'ja'}], 'item_1612345678910': [{'subitem_1623456789123': 'http://doi.org/test_doi'}, {'subitem_1623456789123': 'http://hdl.handle.net/test_doi'}, {'subitem_1623456789123': 'http://other_prefix'}], 'item_1551264822581': [{'subitem_1592472785169': 'Test Topic', 'subitem_1592472786088': 'test_topic_vocab', 'subitem_1592472786560': 'http://test.topic.vocab', 'subitem_1592472785698': 'ja'}, {'subitem_1592472785169': '人口', 'subitem_1592472786088': 'CESSDA Topic Classification', 'subitem_1592472786560': 'https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification', 'subitem_1592472785698': 'ja'}, {'subitem_1592472785169': 'test_str_value'}, {'subitem_1592472785169': 'Demography', 'subitem_1592472786088': 'CESSDA Topic Classification', 'subitem_1592472786560': 'https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification', 'subitem_1592472785698': 'en'}], 'item_1602145192334': [{'subitem_1602144573160': '2023-03-01', 'subitem_1602144587621': 'start'}, {'subitem_1602144573160': '2023-03-03', 'subitem_1602144587621': 'end'}], 'item_1586253152753': [{'subitem_1602144573160': '2023-03-01', 'subitem_1602144587621': 'start'}, {'subitem_1602144573160': '2023-03-06', 'subitem_1602144587621': 'end'}], 'item_1570068313185': [{'subitem_1586419454219': 'test_geographic_coverage', 'subitem_1586419462229': 'ja'}], 'item_1586253224033': [{'subitem_1596608607860': '個人', 'subitem_1596608609366': 'ja'}, {'subitem_1596608607860': 'test_unit_of_analysis', 'subitem_1596608609366': 'en'}, {'subitem_1596608607860': 'Individual', 'subitem_1596608609366': 'en'}], 'item_1586253249552': [{'subitem_1596608974429': 'test parent set', 'subitem_1596608975087': 'ja'}], 'item_1588260046718': [{'subitem_1591178807921': '量的調査', 'subitem_1591178808409': 'ja'}, {'subitem_1591178807921': 'quantatitive research', 'subitem_1591178808409': 'en'}], 'item_1551264846237': [{'subitem_1551255577890': 'this is description for ddi item.\nthis is description for ddi item.', 'subitem_1551255592625': 'en'}], 'item_1586253334588': [{'subitem_1596609826487': 'test sampling procedure', 'subitem_1596609827068': 'ja'}, {'subitem_1596609826487': '母集団/ 全数調査', 'subitem_1596609827068': 'ja'}, {'subitem_1596609826487': 'Total universe/Complete enumeration', 'subitem_1596609827068': 'en'}], 'item_1586253349308': [{'subitem_1596610500817': 'test collection method', 'subitem_1596610501381': 'ja'}, {'subitem_1596610500817': 'インタビュー', 'subitem_1596610501381': 'ja'}, {'subitem_1596610500817': 'Interview', 'subitem_1596610501381': 'en'}], 'item_1586253589529': [{'subitem_1596609826487': 'test sampling procedure_sampling_rate', 'subitem_1596609827068': 'ja'}], 'item_1588260178185': [{'subitem_1522650727486': 'オープンアクセス', 'subitem_1522650717957': 'jp'}, {'subitem_1522650727486': 'open access', 'subitem_1522650717957': 'en'}], 'item_1551265002099': [{'subitem_1551255818386': 'jpn'}], 'item_1592405736602': [{'subitem_1602215239359': 'test_related_study_title', 'subitem_1602215240520': 'test_related_study_identifier', 'subitem_1602215239925': 'ja'}, {'subitem_1602215239359': 'test_related_study_title', 'subitem_1602215240520': 'test_related_study_identifier_out1', 'subitem_1602215239925': 'ja'}], 'item_1592405735401': [{'subitem_1602214558730': 'test_related_publication_title_out', 'subitem_1602214560358': 'test_related_publication_identifier_out1', 'subitem_1602214559588': 'ja'}]}
        res = {"$schema":mapper.itemtype.id,"pubdate":str(mapper.datestamp())}
        mapper.ddi_harvest_processing(data,res)
        assert res == test
        
        data = OrderedDict([
            ('@xmlns:dc', 'http://purl.org/dc/terms/'), 
            ('@xmlns:fn', 'http://www.w3.org/2005/xpath-functions'), 
            ('@xmlns:saxon', 'http://xml.apache.org/xslt'), 
            ('@xmlns:xhtml', 'http://www.w3.org/1999/xhtml'), 
            ('@xmlns:xs', 'http://www.w3.org/2001/XMLSchema'), 
            ('@xmlns', 'ddi:codebook:2_5'), 
            ('@xsi:schemaLocation', 'https://ddialliance.org/Specification/DDI-Codebook/2.5/XMLSchema/codebook.xsd'), 
            ('stdyDscr', OrderedDict([
                ('citation', OrderedDict([
                    ('raise_error',OrderedDict([
                        ('#text','error_value')
                    ]))
                ]))
            ]))
        ])
        xml_str = '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2023-03-02T04:08:53Z</responseDate><request metadataPrefix="ddi" verb="GetRecord" identifier="oai:weko3.example.org:00000075">https://192.168.56.103/oai</request><GetRecord><record><header><identifier>oai:weko3.example.org:00000075</identifier><datestamp>2023-03-02T04:06:46Z</datestamp><setSpec>1557820086539</setSpec></header><metadata><codeBook xmlns:dc="http://purl.org/dc/terms/" xmlns:fn="http://www.w3.org/2005/xpath-functions" xmlns:saxon="http://xml.apache.org/xslt" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="ddi:codebook:2_5" xsi:schemaLocation="https://ddialliance.org/Specification/DDI-Codebook/2.5/XMLSchema/codebook.xsd"><stdyDscr><citation xml:lang="ja"><raise_error>error_value</raise_error></citation></stdyDscr></codeBook></metadata></record></GetRecord></OAI-PMH>'
        tree = etree.fromstring(xml_str)
        record = tree.findall("./GetRecord/record",namespaces=tree.nsmap)[0]
        xml = etree.tostring(record,encoding="utf-8").decode()
        mapper = DDIMapper(xml)
        mapper.map_itemtype('codeBook')
        res = {"$schema":mapper.itemtype.id,"pubdate":str(mapper.datestamp())}
        with pytest.raises(Exception):
            mapper.ddi_harvest_processing(data,res)
        assert res == {"$schema":mapper.itemtype.id,"pubdate":str(mapper.datestamp())}
    
#         def get_mapping_ddi():
#         def merge_dict(result, target, val, keys):
#         def merge_data_by_mapping_keys(parent_key, data_mapping):
#         def parse_to_obj_data_by_mapping_keys(vals, keys):
#             def get_same_key_from_form(sub_key):
#             def parse_each_obj(parse_data):
#         def get_all_key(prefix):
#         def convert_to_lst(src_lst):
#         def get_all_keys_forms():
#         def handle_identifier(identifier):
#     def map_itemtype(self, type_tag):
#     def map(self):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::TestDDIMapper::test_map -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
    def test_map(self, db_itemtype):
        # is_deleted = True
        deleted_xml = '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2023-03-02T04:08:53Z</responseDate><request metadataPrefix="ddi" verb="GetRecord" identifier="oai:weko3.example.org:00000075">https://192.168.56.103/oai</request><GetRecord><record><header status="deleted"><identifier>oai:weko3.example.org:00000075</identifier><datestamp>2023-03-02T04:06:46Z</datestamp><setSpec>1557820086539</setSpec></header></record></GetRecord></OAI-PMH>'
        tree = etree.fromstring(deleted_xml)
        record = tree.findall("./GetRecord/record",namespaces=tree.nsmap)[0]
        xml = etree.tostring(record,encoding="utf-8").decode()
        mapper = DDIMapper(xml)
        result = mapper.map()
        assert result == {}
        
        # json["record"]["metadata"]["codeBook"] is none
        without_codebook_xml = '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2023-03-02T04:08:53Z</responseDate><request metadataPrefix="ddi" verb="GetRecord" identifier="oai:weko3.example.org:00000075">https://192.168.56.103/oai</request><GetRecord><record><header><identifier>oai:weko3.example.org:00000075</identifier><datestamp>2023-03-02T04:06:46Z</datestamp><setSpec>1557820086539</setSpec></header><metadata><codeBook></codeBook></metadata></record></GetRecord></OAI-PMH>'
        tree = etree.fromstring(without_codebook_xml)
        record = tree.findall("./GetRecord/record",namespaces=tree.nsmap)[0]
        xml = etree.tostring(record,encoding="utf-8").decode()
        mapper = DDIMapper(xml)
        result = mapper.map()
        assert result == None
        
        
        xml_str = '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"><responseDate>2023-03-02T04:08:53Z</responseDate><request metadataPrefix="ddi" verb="GetRecord" identifier="oai:weko3.example.org:00000075">https://192.168.56.103/oai</request><GetRecord><record><header><identifier>oai:weko3.example.org:00000075</identifier><datestamp>2023-03-02T04:06:46Z</datestamp><setSpec>1557820086539</setSpec></header><metadata><codeBook xmlns:dc="http://purl.org/dc/terms/" xmlns:fn="http://www.w3.org/2005/xpath-functions" xmlns:saxon="http://xml.apache.org/xslt" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="ddi:codebook:2_5" xsi:schemaLocation="https://ddialliance.org/Specification/DDI-Codebook/2.5/XMLSchema/codebook.xsd"><stdyDscr><citation xml:lang="ja"><titlStmt><titl xml:lang="ja">test ddi full item</titl><altTitl xml:lang="ja">other ddi title</altTitl><IDNo agency="test_id_agency" xml:lang="ja">test_study_id</IDNo></titlStmt><rspStmt><AuthEnty ID="4" xml:lang="ja" affiliation="author.affiliation">テスト, 太郎</AuthEnty></rspStmt><prodStmt><producer xml:lang="ja">test_publisher</producer><copyright xml:lang="ja">test_rights</copyright><fundAg ID="test_found_ageny" xml:lang="ja">test_founder_name</fundAg><grantNo>test_grant_no</grantNo></prodStmt><distStmt><distrbtr URI="https://test.distributor.affiliation" abbr="TDN" xml:lang="ja" affiliation="Test Distributor Affiliation">Test Distributor Name</distrbtr></distStmt><serStmt><serName xml:lang="ja">test_series</serName></serStmt><verStmt><version date="2023-03-07" xml:lang="ja">1.2</version></verStmt><biblCit xml:lang="ja">test.input.content</biblCit><holdings URI="https://192.168.56.103/records/75"/></citation><stdyInfo xml:lang="ja"><subject><topcClas vocab="test_topic_vocab" vocabURI="http://test.topic.vocab" xml:lang="ja">Test Topic</topcClas><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="ja">人口</topcClas></subject><sumDscr><timePrd event="start">2023-03-01</timePrd><timePrd event="end">2023-03-03</timePrd><collDate event="start">2023-03-01</collDate><collDate event="end">2023-03-06</collDate><geogCover xml:lang="ja">test_geographic_coverage</geogCover><anlyUnit xml:lang="ja">個人</anlyUnit><universe xml:lang="ja">test parent set</universe><dataKind xml:lang="ja">量的調査</dataKind></sumDscr></stdyInfo><stdyInfo xml:lang="en"><subject><topcClas vocab="CESSDA Topic Classification" vocabURI="https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification" xml:lang="en">Demography</topcClas></subject><abstract xml:lang="en">this is description for ddi item. this is description for ddi item.</abstract><sumDscr><timePrd event="start">2023-03-01</timePrd><timePrd event="end">2023-03-03</timePrd><collDate event="start">2023-03-01</collDate><collDate event="end">2023-03-06</collDate><anlyUnit xml:lang="en">test_unit_of_analysis</anlyUnit><anlyUnit xml:lang="en">Individual</anlyUnit><dataKind xml:lang="en">quantatitive research</dataKind></sumDscr></stdyInfo><method xml:lang="ja"><dataColl><sampProc xml:lang="ja">test sampling procedure</sampProc><sampProc xml:lang="ja">母集団/ 全数調査</sampProc><collMode xml:lang="ja">test collection method</collMode><collMode xml:lang="ja">インタビュー</collMode></dataColl><anlyInfo><respRate xml:lang="ja">test sampling procedure_sampling_rate</respRate></anlyInfo></method><method xml:lang="en"><dataColl><sampProc xml:lang="en">Total universe/Complete enumeration</sampProc><collMode xml:lang="en">Interview</collMode></dataColl><anlyInfo/></method><dataAccs xml:lang="jp"><setAvail><avlStatus xml:lang="jp">オープンアクセス</avlStatus></setAvail><notes>jpn</notes></dataAccs><dataAccs xml:lang="en"><setAvail><avlStatus xml:lang="en">open access</avlStatus></setAvail><notes>jpn</notes></dataAccs><othrStdyMat xml:lang="ja"><relStdy ID="test_related_study_identifier" xml:lang="ja">test_related_study_title</relStdy><relPubl ID="test_related_publication_identifier" xml:lang="ja">test_related_publication_title</relPubl></othrStdyMat></stdyDscr></codeBook></metadata></record></GetRecord></OAI-PMH>'
        tree = etree.fromstring(xml_str)
        record = tree.findall("./GetRecord/record",namespaces=tree.nsmap)[0]
        xml = etree.tostring(record,encoding="utf-8").decode()
        mapper = DDIMapper(xml)
        test = {'$schema': 11, 'pubdate': '2023-03-02', 'item_1551264308487': [{'subitem_1551255647225': 'test ddi full item', 'subitem_1551255648112': 'ja'}], 'item_1551264326373': [{'subitem_1551255720400': 'other ddi title', 'subitem_1551255721061': 'ja'}], 'item_1586157591881': [{'subitem_1586156939407': 'test_study_id', 'subitem_1591256665864': 'test_id_agency', 'subitem_1586311767281': 'ja'}], 'item_1593074267803': [{'creatorNames': [{'creatorName': 'テスト, 太郎', 'creatorNameLang': 'ja'}], 'nameIdentifiers': [{'nameIdentifier': '4'}], 'creatorAffiliations': [{'affiliationNames': [{'affiliationName': 'author.affiliation'}]}]}], 'item_1551264917614': [{'subitem_1551255702686': 'test_publisher', 'subitem_1551255710277': 'ja'}], 'item_1551264629907': [{'subitem_1602213569986': {'subitem_1602213569987': 'test_rights'}, 'subitem_1602213570623': 'ja'}], 'item_1602145817646': [{'subitem_1602142814330': 'test_founder_name', 'subitem_1602142815328': 'ja'}], 'item_1602145850035': [{'subitem_1602142123771': 'test_grant_no'}], 'item_1592405734122': [{'subitem_1592369405220': 'Test Distributor Name', 'subitem_1591320914113': 'https://test.distributor.affiliation', 'subitem_1591320889728': 'TDN', 'subitem_1592369407829': 'ja', 'subitem_1591320890384': 'Test Distributor Affiliation'}], 'item_1588254290498': [{'subitem_1587462181884': 'test_series', 'subitem_1587462183075': 'ja'}], 'item_1551265075370': [{'subitem_1591254914934': '1.2', 'subitem_1591254915862': '2023-03-07', 'subitem_1591254915406': 'ja'}], 'item_1592880868902': [{'subitem_1586228465211': 'test.input.content', 'subitem_1586228490356': 'ja'}], 'item_1551264822581': [{'subitem_1592472785169': 'Test Topic', 'subitem_1592472786088': 'test_topic_vocab', 'subitem_1592472786560': 'http://test.topic.vocab', 'subitem_1592472785698': 'ja'}, {'subitem_1592472785169': '人口', 'subitem_1592472786088': 'CESSDA Topic Classification', 'subitem_1592472786560': 'https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification', 'subitem_1592472785698': 'ja'}, {'subitem_1592472785169': 'Demography', 'subitem_1592472786088': 'CESSDA Topic Classification', 'subitem_1592472786560': 'https://vocabularies.cessda.eu/urn/urn:ddi:int.cessda.cv:TopicClassification', 'subitem_1592472785698': 'en'}], 'item_1602145192334': [{'subitem_1602144573160': '2023-03-01', 'subitem_1602144587621': 'start'}, {'subitem_1602144573160': '2023-03-03', 'subitem_1602144587621': 'end'}], 'item_1586253152753': [{'subitem_1602144573160': '2023-03-01', 'subitem_1602144587621': 'start'}, {'subitem_1602144573160': '2023-03-06', 'subitem_1602144587621': 'end'}], 'item_1570068313185': [{'subitem_1586419454219': 'test_geographic_coverage', 'subitem_1586419462229': 'ja'}], 'item_1586253224033': [{'subitem_1596608607860': '個人', 'subitem_1596608609366': 'ja'}, {'subitem_1596608607860': 'test_unit_of_analysis', 'subitem_1596608609366': 'en'}, {'subitem_1596608607860': 'Individual', 'subitem_1596608609366': 'en'}], 'item_1586253249552': [{'subitem_1596608974429': 'test parent set', 'subitem_1596608975087': 'ja'}], 'item_1588260046718': [{'subitem_1591178807921': '量的調査', 'subitem_1591178808409': 'ja'}, {'subitem_1591178807921': 'quantatitive research', 'subitem_1591178808409': 'en'}], 'item_1551264846237': [{'subitem_1551255577890': 'this is description for ddi item. this is description for ddi item.', 'subitem_1551255592625': 'en'}], 'item_1586253334588': [{'subitem_1596609826487': 'test sampling procedure', 'subitem_1596609827068': 'ja'}, {'subitem_1596609826487': '母集団/ 全数調査', 'subitem_1596609827068': 'ja'}, {'subitem_1596609826487': 'Total universe/Complete enumeration', 'subitem_1596609827068': 'en'}], 'item_1586253349308': [{'subitem_1596610500817': 'test collection method', 'subitem_1596610501381': 'ja'}, {'subitem_1596610500817': 'インタビュー', 'subitem_1596610501381': 'ja'}, {'subitem_1596610500817': 'Interview', 'subitem_1596610501381': 'en'}], 'item_1586253589529': [{'subitem_1596609826487': 'test sampling procedure_sampling_rate', 'subitem_1596609827068': 'ja'}], 'item_1588260178185': [{'subitem_1522650727486': 'オープンアクセス', 'subitem_1522650717957': 'jp'}, {'subitem_1522650727486': 'open access', 'subitem_1522650717957': 'en'}], 'item_1551265002099': [{'subitem_1551255818386': 'jpn'}], 'item_1592405736602': [{'subitem_1602215239359': 'test_related_study_title', 'subitem_1602215240520': 'test_related_study_identifier', 'subitem_1602215239925': 'ja'}], 'item_1592405735401': [{'subitem_1602214558730': 'test_related_publication_title', 'subitem_1602214560358': 'test_related_publication_identifier', 'subitem_1602214559588': 'ja'}], 'title': 'test ddi full item', 'type': [{'resourcetype': 'dataset', 'resourceuri': 'http://purl.org/coar/resource_type/c_ddb1'}]}
        result = mapper.map()

        assert result == test


def test_biosample01(db_itemtype):

    record = {'record': {'header': {}}}
    with open("tests/data/test_jsonld/biosample_data01.jsonld", "r") as f:
        json_data = json.load(f)
        record['record']['metadata'] = json_data
    record['record']['header']['identifier'] = json_data['identifier']
    record['record']['header']['datestamp'] = (datetime.fromtimestamp(
            1674085174, tz=pytz.utc)).strftime("%Y/%m/%dT%H:%M:%SZ")

    mapper = BIOSAMPLEMapper(record)

    result = mapper.map()
    with open("tests/data/test_jsonld/biosample_record01.json", "r") as f:
        test = json.load(f)
        assert result == test


def test_biosample02(db_itemtype):

    record = {'record': {'header': {}}}
    with open("tests/data/test_jsonld/biosample_data02.jsonld", "r") as f:
        json_data = json.load(f)
        record['record']['metadata'] = json_data
    record['record']['header']['identifier'] = json_data['identifier']
    record['record']['header']['datestamp'] = (datetime.fromtimestamp(
            1674085174, tz=pytz.utc)).strftime("%Y/%m/%dT%H:%M:%SZ")

    mapper = BIOSAMPLEMapper(record)
    mapper.map_itemtype("")
    result = mapper.map()
    with open("tests/data/test_jsonld/biosample_record02.json", "r") as f:
        test = json.load(f)
        assert result == test


def test_biosample_empty_data(db_itemtype):

    record = {'record': {'header': {}}}
    record['record']['header']['identifier'] = 'TEST_ID_BIOSAMPLE'
    record['record']['header']['datestamp'] = (datetime.fromtimestamp(
            1674085174, tz=pytz.utc)).strftime("%Y/%m/%dT%H:%M:%SZ")
    record['record']['metadata'] = {}
    mapper = BIOSAMPLEMapper(record)

    result = mapper.map()
    assert result == {
        "$schema": 32102,
        "pubdate": "2023-01-18",
        "item_1723721669989": {
            "resourcetype": "dataset"
        }
    }


def test_biosample_deleted(db_itemtype):

    record = {'record': {'header': {}}}
    with open("tests/data/test_jsonld/biosample_data01.jsonld", "r") as f:
        json_data = json.load(f)
        record['record']['metadata'] = json_data
    record['record']['header']['identifier'] = json_data['identifier']
    record['record']['header']['datestamp'] = (datetime.fromtimestamp(
            1674085174, tz=pytz.utc)).strftime("%Y/%m/%dT%H:%M:%SZ")
    record['record']['header']['@status'] = 'deleted'

    BaseMapper.update_itemtype_map()
    mapper = BIOSAMPLEMapper(record)

    result = mapper.map()
    assert result == {}


def test_bioproject(db_itemtype):

    record = {'record': {'header': {}}}
    with open("tests/data/test_jsonld/bioproject_data01.jsonld", "r") as f:
        json_data = json.load(f)
        record['record']['metadata'] = json_data
    record['record']['header']['identifier'] = json_data['identifier']
    record['record']['header']['datestamp'] = (datetime.fromtimestamp(
            1674085174, tz=pytz.utc)).strftime("%Y/%m/%dT%H:%M:%SZ")

    mapper = BIOPROJECTMapper(record)

    result = mapper.map()
    with open("tests/data/test_jsonld/bioproject_record01.json", "r") as f:
        test = json.load(f)
        assert result == test


def test_bioproject_empty_data(db_itemtype):

    record = {'record': {'header': {}}}
    record['record']['header']['identifier'] = 'TEST_ID_BIOSAMPLE'
    record['record']['header']['datestamp'] = (datetime.fromtimestamp(
            1674085174, tz=pytz.utc)).strftime("%Y/%m/%dT%H:%M:%SZ")
    record['record']['metadata'] = {}

    mapper = BIOPROJECTMapper(record)

    result = mapper.map()
    assert result == {
        "$schema": 32103,
        "pubdate": "2023-01-18",
        "item_1723373560614": {
            "resourcetype": "dataset"
        }
    }


def test_bioproject_deleted(db_itemtype):

    record = {'record': {'header': {}}}
    with open("tests/data/test_jsonld/bioproject_data01.jsonld", "r") as f:
        json_data = json.load(f)
        record['record']['metadata'] = json_data
    record['record']['header']['identifier'] = json_data['identifier']
    record['record']['header']['datestamp'] = (datetime.fromtimestamp(
            1674085174, tz=pytz.utc)).strftime("%Y/%m/%dT%H:%M:%SZ")
    record['record']['header']['@status'] = 'deleted'

    mapper = BIOPROJECTMapper(record)

    result = mapper.map()
    assert result == {}


