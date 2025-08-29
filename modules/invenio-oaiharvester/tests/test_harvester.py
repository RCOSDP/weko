
import pytest
import responses
from lxml import etree
from mock import patch, MagicMock
import copy
import xmltodict
import dateutil
from collections import OrderedDict
from requests.exceptions import HTTPError
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
    # add_apc,
    add_right,
    add_subject,
    add_description,
    add_publisher,
    add_date,
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
    DDIMapper
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
    # test case 1, 4
    # resumptiontoken is none
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
    responses.add(
        responses.GET,
        "https://test.org/?verb=ListRecords&from=2023-01-10&until=2023-10-01&metadataPrefix=jpcoar_1.0&set=*",
        body=body1,
        content_type='text/xml'
    )
    records, rtoken = list_records("https://test.org/","2023-01-10","2023-10-01","jpcoar_1.0","*",resumption_token=None)
    result = [str(etree.tostring(record),"utf-8") for record in records]
    assert result == ['<record xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">test_record1</record>', '<record xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">test_record2</record>']
    assert rtoken == "test_token"

    # test case 2, 3
    # resumptiontoken is not none
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
       "https://test.org/?verb=ListRecords&resumptionToken=test_token",
        body=body2,
        content_type='text/xml'
    )
    records, rtoken = list_records("https://test.org/","2023-01-10","2023-10-01","jpcoar_1.0","*",resumption_token="test_token")
    result = [str(etree.tostring(record),"utf-8") for record in records]
    assert result == ['<record xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">test_record3</record>', '<record xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">test_record4</record>']
    assert rtoken == None

    # test case 5
    # HTTP Error
    responses.add(
        responses.GET,
        "https://400_test.org/?verb=ListRecords&from=2023-11-10&until=2023-10-01&metadataPrefix=jpcoar_1.0&set=*",
        status=404
    )
    with pytest.raises(HTTPError) as e:
        list_records("https://400_test.org/","2023-11-10","2023-10-01","jpcoar_1.0","*",resumption_token=None)

    # test case 6
    # 500 Error
    responses.add(
        responses.GET,
        "https://500_test.org/?verb=ListRecords&set=*",
        status=500
    )
    with pytest.raises(HTTPError) as e:
        list_records("https://500_test.org/",None,None,None,"*",resumption_token=None)


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
    
# def subitem_recs(schema, keys, value, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_subitem_recs -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_subitem_recs(db_itemtype):
    
    # "items.perperty" in schema. len(keys) > 2,_subitem is not false
    schema = {"items":{"properties":{"item_key1":{'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'subitem_1551256006332': {'type': 'string', 'title': 'Creator Given Name', 'format': 'text', 'title_i18n': {'en': 'Creator Given Name', 'ja': '作成者名'}, 'title_i18n_temp': {'en': 'Creator Given Name', 'ja': '作成者名'}}, 'subitem_1551256007414': {'enum': [None,'ja','en'], 'type': ['null', 'string'], 'title': 'Language', 'format': 'select', 'currentEnum': ['ja','en']}}}, 'title': 'Creator Given Name', 'format': 'array'}}}}
    value = "jpcoar:givenName.#text"
    keys = ["item_key1",'subitem_1551256006332']
    metadata = OrderedDict([('jpcoar:givenName', OrderedDict([('@xml:lang', 'ja'), ('#text', '太郎')]))])
    result = subitem_recs(schema, keys, value, metadata)
    assert result == [[{'subitem_1551256006332': '太郎'}]]
    
    # "items.perperty" in schema. len(keys) > 2,_subitem is false
    schema = {"items":{"properties":{"item_key1":{'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'subitem_1551256006332': {'type': 'string', 'title': 'Creator Given Name', 'format': 'text', 'title_i18n': {'en': 'Creator Given Name', 'ja': '作成者名'}, 'title_i18n_temp': {'en': 'Creator Given Name', 'ja': '作成者名'}}, 'subitem_1551256007414': {'enum': [None,'ja','en'], 'type': ['null', 'string'], 'title': 'Language', 'format': 'select', 'currentEnum': ['ja','en']}}}, 'title': 'Creator Given Name', 'format': 'array'}}}}
    value = "jpcoar:givenName.#text"
    keys = ["item_key1",'subitem_1551256006332']
    metadata = OrderedDict([('jpcoar:givenName', "")])
    result = subitem_recs(schema, keys, value, metadata)
    assert result == []
    
    value = "jpcoar:givenName.#text"
    keys = ['subitem_1551256006332']
    schema = {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'subitem_1551256006332': {'type': 'string', 'title': 'Creator Given Name', 'format': 'text', 'title_i18n': {'en': 'Creator Given Name', 'ja': '作成者名'}, 'title_i18n_temp': {'en': 'Creator Given Name', 'ja': '作成者名'}}, 'subitem_1551256007414': {'enum': [None,'ja','en'], 'type': ['null', 'string'], 'title': 'Language', 'format': 'select', 'currentEnum': ['ja','en']}}}, 'title': 'Creator Given Name', 'format': 'array'}
    # metadata.get(value[0]) is list
    metadata = OrderedDict([('jpcoar:givenName', ["太郎",OrderedDict([('@xml:lang', 'ja'), ('#text', '次郎')])])])
    result = subitem_recs(schema, keys, value, metadata)
    assert result == [{'subitem_1551256006332': '太郎'}, {'subitem_1551256006332': '次郎'}]
    
    # "." not in value, metadata is not str and OrderedDict
    schema = {'type': 'array', 'items': {'type': 'object', 'format': 'object', 'properties': {'subitem_1551257342360': {'type': 'string', 'title': 'Contributor Given Name', 'format': 'text', 'title_i18n': {'en': 'Contributor Given Name', 'ja': '寄与者名'}, 'title_i18n_temp': {'en': 'Contributor Given Name', 'ja': '寄与者名'}}, 'subitem_1551257343979': {'enum': [None, 'ja','en'], 'type': ['null', 'string'], 'title': 'Language', 'format': 'select', 'currentEnum': ['ja','en']}}}, 'title': 'Contributor Given Name', 'format': 'array'}
    keys = ['subitem_1551257342360']
    value = "#text"
    metadata = []
    result = subitem_recs(schema, keys, value, metadata)
    assert result == []
    
    # "properties" in schema
    ## len(keys) > 1
    keys = ["test_key1","test_key2"]
    schema = {"properties":{"test_key1":{"properties":{"test_key2":"value"}}}}
    metadata = OrderedDict([("#text","value")])
    result = subitem_recs(schema, keys, value, metadata)
    assert result == {'test_key2': 'value'}
    
    ## len(keys) = 1
    keys = ["test_key"]
    schema = {"properties":{"test_key":"value"}}
    result = subitem_recs(schema, keys, value, metadata)
    assert result == {'test_key': 'value'}
    
    ### "." in value, len(value.split(".")) > 2
    value = "test.#text"
    metadata = OrderedDict([("#text","value")])
    result = subitem_recs(schema, keys, value, metadata)
    assert result == None
    
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
    
    
    schema = {'type': 'string', 'title': 'Version', 'format': 'text', 'title_i18n': {'en': 'Version', 'ja': 'バージョン情報'}, 'title_i18n_temp': {'en': 'Version', 'ja': 'バージョン情報'}}
    keys = ["test_key"]
    result = subitem_recs(schema, keys, value, metadata)
    assert result == None


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

# def add_title(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_title -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_title(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("dc:title")
    res1 = copy.deepcopy(res)
    add_title(schema, mapping, res1, metadata)
    
    assert "item_1551264308487" in res1
    assert res1["item_1551264308487"] == [{'subitem_1551255647225': 'test full item', 'subitem_1551255648112': 'ja'}]
    assert "title" in res1
    assert res1["title"] == "test full item"
    
    res2 = copy.deepcopy(res)
    add_title(schema, mapping, res2, ["test full item"])
    assert "item_1551264308487" in res2
    assert res2["item_1551264308487"] == [{'subitem_1551255647225': 'test full item'}]
    assert "title" in res2
    assert res2["title"] == "test full item"
    
    res3 = copy.deepcopy(res)
    add_title(schema, mapping, res3, [["test full item"]])
    assert "item_1551264308487" in res3
    assert res3["item_1551264308487"] == [{'subitem_1551255647225': 'test full item','subitem_1551255648112': 'test full item'}]
    assert "title" not in res3

    with patch("invenio_oaiharvester.harvester.parsing_metadata",return_value=(None,None)):
        res4 = copy.deepcopy(res)
        add_title(schema, mapping, res4, ["test full item"])
        assert "item_1551264308487" not in res4
        assert "title" not in res4

# def add_alternative(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_alternative -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_alternative(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("dcterms:alternative")
    res1 = copy.deepcopy(res)
    add_alternative(schema, mapping, res1, metadata)
    assert "item_1551264326373" in res1
    assert res1["item_1551264326373"] == [{'subitem_1551255720400': 'other title', 'subitem_1551255721061': 'en'}]

# def add_creator_jpcoar(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_creator_jpcoar -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_creator_jpcoar(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("jpcoar:creator")
    res1 = copy.deepcopy(res)
    add_creator_jpcoar(schema, mapping, res1, metadata)
    
    assert "item_1551264340087" in res1
    assert res1["item_1551264340087"] == [{'subitem_1551255991424': [{'subitem_1551256006332': '太郎', 'subitem_1551256007414': 'ja'}], 'subitem_1551255929209': [{'subitem_1551255938498': 'テスト', 'subitem_1551255964991': 'ja'}], 'subitem_1551255898956': [{'subitem_1551255905565': 'テスト, 太郎', 'subitem_1551255907416': 'ja'}], 'subitem_1551256025394': [{'subitem_1551256035730': 'テスト\u3000別郎', 'subitem_1551256055588': 'ja'}]}]
    
# def add_contributor_jpcoar(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_contributor_jpcoar -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_contributor_jpcoar(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("jpcoar:contributor")
    res1 = copy.deepcopy(res)
    add_contributor_jpcoar(schema, mapping, res1, metadata)
    
    assert "item_1551264418667" in res1
    assert res1["item_1551264418667"] == [{'subitem_1551257036415': 'ContactPerson', 'subitem_1551257339190': [{'subitem_1551257342360': '', 'subitem_1551257343979': 'en'}], 'subitem_1551257272214': [{'subitem_1551257314588': 'test', 'subitem_1551257316910': 'en'}], 'subitem_1551257245638': [{'subitem_1551257276108': 'test, smith', 'subitem_1551257279831': 'en'}], 'subitem_1551257372442': [{'subitem_1551257374288': 'other smith', 'subitem_1551257375939': 'en'}]}]

# def add_access_right(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_access_right -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_access_right(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("dcterms:accessRights")
    res1 = copy.deepcopy(res)
    
    add_access_right(schema, mapping, res1, metadata)
    assert "item_1551264447183" in res1
    assert res1["item_1551264447183"] == [{'subitem_1551257553743': 'metadata only access', 'subitem_1551257578398': 'http://purl.org/coar/access_right/c_14cb'}]

# def add_apc(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_apc -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_apc(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("rioxxterms:apc")
    res1 = copy.deepcopy(res)
    add_apc(schema, mapping, res1, metadata)
    assert "item_1551264605515" in res1
    assert res1["item_1551264605515"] == [{'subitem_1551257776901': 'Paid'}]
    
# def add_right(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_right -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_right(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("dc:rights")
    res1 = copy.deepcopy(res)
    add_right(schema,mapping,res1,metadata)
    
    assert "item_1551264629907" in res1
    assert res1["item_1551264629907"] == [{'subitem_1551257025236': [{'subitem_1551257043769': 'テスト権利情報', 'subitem_1551257047388': 'ja'}], 'subitem_1551257030435': 'テスト権利情報Resource'}]
    
# def add_subject(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_subject -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_subject(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("jpcoar:subject")
    res1 = copy.deepcopy(res)
    add_subject(schema, mapping, res1, metadata)
    
    assert "item_1551264822581" in res1
    assert res1["item_1551264822581"] == [{'subitem_1551257315453': 'テスト主題', 'subitem_1551257323812': 'ja', 'subitem_1551257343002': 'http://bsh.com', 'subitem_1551257329877': 'BSH'}]
    
# def add_description(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_description -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_description(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("datacite:description")
    res1 = copy.deepcopy(res)
    
    add_description(schema, mapping, res1, metadata)
    assert "item_1551264846237" in res1
    assert res1["item_1551264846237"] == [{'subitem_1551255577890': 'this is test abstract.', 'subitem_1551255592625': 'en', 'subitem_1551255637472': 'Abstract'}]

# def add_publisher(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_publisher -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_publisher(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("dc:publisher")
    res1 = copy.deepcopy(res)
    add_publisher(schema, mapping, res1, metadata)
    assert "item_1551264917614" in res1
    assert res1["item_1551264917614"] == [{'subitem_1551255702686': 'test publisher', 'subitem_1551255710277': 'ja'}]

# def add_date(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_date -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_date(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("datacite:date")
    res1 = copy.deepcopy(res)
    add_date(schema, mapping, res1, metadata)
    assert "item_1551264974654" in res1
    assert res1["item_1551264974654"]  == [{'subitem_1551255753471': '2022-10-20', 'subitem_1551255775519': 'Accepted'}, {'subitem_1551255753471': '2022-10-19', 'subitem_1551255775519': 'Issued'}]
    
# def add_language(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_language -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_language(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("dc:language")
    res1 = copy.deepcopy(res)
    add_language(schema, mapping, res1, metadata)
    assert "item_1551265002099" in res1
    assert res1["item_1551265002099"] == [{'subitem_1551255818386': 'jpn'}]
    
# def add_version(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_version -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_version(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("datacite:version")
    res1 = copy.deepcopy(res)
    add_version(schema, mapping, res1, metadata)
    assert "item_1551265075370" in res1
    assert res1["item_1551265075370"] == [{'subitem_1551255975405': '1.1'}]
    
# def add_version_type(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_version_type -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_version_type(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("oaire:version")
    res1 = copy.deepcopy(res)
    add_version_type(schema, mapping, res1, metadata)
    assert "item_1551265118680" in res1
    assert res1["item_1551265118680"] == [{'subitem_1551256025676': 'AO'}]
    
# def add_identifier_registration(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_identifier_registration -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_identifier_registration(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("jpcoar:identifierRegistration")
    res1 = copy.deepcopy(res)
    add_identifier_registration(schema, mapping, res1, metadata)
    assert "item_1581495499605" in res1
    assert res1["item_1581495499605"]==[{'subitem_1551256250276': '1234/0000000001', 'subitem_1551256259586': 'JaLC'}]
    
# def add_temporal(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_temporal -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_temporal(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("dcterms:temporal")
    res1 = copy.deepcopy(res)
    add_temporal(schema, mapping, res1, metadata)
    assert "item_1551265302120" in res1
    assert res1["item_1551265302120"] == [{'subitem_1551256918211': '1 to 2', 'subitem_1551256920086': 'ja'}]

# def add_source_identifier(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_source_identifier -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_source_identifier(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("jpcoar:sourceIdentifier")
    add_source_identifier(schema, mapping, res, metadata)
    assert "item_1551265409089" in res
    assert res["item_1551265409089"] == [{'subitem_1551256405981': 'test source Identifier', 'subitem_1551256409644': 'PISSN'}]
    
# def add_file(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_file -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_file(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("jpcoar:file")
    test = [
        {'subitem_1551255854908': '1.0', 'subitem_1551255750794': 'text/plain', 'subitem_1551255788530': [{'subitem_1570068579439': '18 B'}], 'subitem_1551255820788': [{'subitem_1551255828320': '2022-10-20', 'subitem_1551255833133': 'Accepted'}], 'subitem_1551255558587': [{'subitem_1551255570271': 'https://weko3.example.org/record/1/files/test1.txt'}]}, 
        {'subitem_1551255854908': '1.2', 'subitem_1551255750794': 'application/octet-stream', 'subitem_1551255788530': [{'subitem_1570068579439': '18 B'}], 'subitem_1551255558587': [{'subitem_1551255570271': 'https://weko3.example.org/record/1/files/test2'}]},
        {'subitem_1551255854908': '2.1', 'subitem_1551255750794': 'image/png', 'subitem_1551255788530': [{'subitem_1570068579439': '18 B'}], 'subitem_1551255558587': [{'subitem_1551255570271': 'https://weko3.example.org/record/1/files/test3.png'}]}
    ]
    add_file(schema, mapping, res, metadata)
    assert "item_1570069138259" in res
    assert res["item_1570069138259"] == test

# def add_identifier(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_identifier -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_identifier(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("jpcoar:identifier")
    add_identifier(schema, mapping, res, metadata)
    assert "system_identifier_doi" in res
    assert res["system_identifier_doi"] == [{'subitem_systemidt_identifier': '1111', 'subitem_systemidt_identifier_type': 'DOI'}, {'subitem_systemidt_identifier': 'https://doi.org/1234/0000000001', 'subitem_systemidt_identifier_type': 'DOI'}, {'subitem_systemidt_identifier': 'https://192.168.56.103/records/1', 'subitem_systemidt_identifier_type': 'URI'}]

# def add_source_title(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_source_title -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_source_title(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("jpcoar:sourceTitle")
    add_source_title(schema, mapping, res, metadata)
    assert "item_1551265438256" in res
    assert res["item_1551265438256"] == [{'subitem_1551256349044': 'test collectibles', 'subitem_1551256350188': 'ja'}, {'subitem_1551256349044': 'test title book', 'subitem_1551256350188': 'ja'}]
    
# def add_volume(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_volume -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_volume(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("jpcoar:volume")
    add_volume(schema, mapping, res, metadata)
    assert "item_1551265463411" in res    
    assert res["item_1551265463411"] == [{'subitem_1551256328147': '5'}, {'subitem_1551256328147': '1'}]
    
# def add_issue(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_issue -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_issue(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("jpcoar:issue")
    add_issue(schema, mapping, res, metadata)
    assert "item_1551265520160" in res
    assert res["item_1551265520160"] == [{'subitem_1551256294723': '2'}, {'subitem_1551256294723': '2'}]

# def add_num_page(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_num_page -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_num_page(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("jpcoar:numPages")
    add_num_page(schema, mapping, res, metadata)
    assert "item_1551265553273" in res
    assert res["item_1551265553273"] == [{'subitem_1551256248092': '333'}, {'subitem_1551256248092': '555'}]

# def add_page_start(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_page_start -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_page_start(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("jpcoar:pageStart")
    add_page_start(schema, mapping, res, metadata)
    assert "item_1551265569218" in res
    assert res["item_1551265569218"] == [{'subitem_1551256198917': '123'}, {'subitem_1551256198917': '789'}]

# def add_page_end(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_page_end -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_page_end(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("jpcoar:pageEnd")
    add_page_end(schema, mapping, res, metadata)
    assert "item_1551265569218" in res
    assert res["item_1551265569218"] == [{'subitem_1551256198917': '456'}, {'subitem_1551256198917': '234'}]
    
# def add_dissertation_number(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_dissertation_number -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_dissertation_number(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("dcndl:dissertationNumber")
    add_dissertation_number(schema, mapping, res, metadata)
    assert "item_1551265738931" in res
    assert res["item_1551265738931"] == [{'subitem_1551256171004': '9999'}]

# def add_date_granted(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_date_granted -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_date_granted(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("dcndl:dateGranted")
    add_date_granted(schema, mapping, res, metadata)
    assert "item_1551265811989" in res
    assert res["item_1551265811989"] == [{'subitem_1551256096004': '2022-10-19'}]
    
# def add_conference(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_conference -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_conference(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("jpcoar:conference")
    add_conference(schema, mapping, res, metadata)
    assert "item_1551265973055" in res
    assert res["item_1551265973055"] == [{'subitem_1599711813532': 'JPN', 'subitem_1599711655652': '12345', 'subitem_1599711633003': [{'subitem_1599711636923': 'テスト会議', 'subitem_1599711645590': 'ja'}]}]
    
# def add_degree_grantor(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_degree_grantor -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_degree_grantor(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("jpcoar:degreeGrantor")
    add_degree_grantor(schema, mapping, res, metadata)
    assert "item_1551265903092" in res
    assert res["item_1551265903092"] == [{'subitem_1551256015892': [{'subitem_1551256027296': '学位授与機関識別子テスト', 'subitem_1551256029891': 'kakenhi'}], 'subitem_1551256037922': [{'subitem_1551256042287': '学位授与機関', 'subitem_1551256047619': 'ja'}]}]
    
# def add_degree_name(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_degree_name -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_degree_name(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("dcndl:degreeName")
    add_degree_name(schema, mapping, res, metadata)
    assert "item_1551265790591" in res
    assert res["item_1551265790591"] == [{'subitem_1551256126428': 'テスト学位', 'subitem_1551256129013': 'ja'}]
    
# def add_funding_reference(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_funding_reference -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_funding_reference(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("jpcoar:fundingReference")
    add_funding_reference(schema, mapping, res, metadata)
    assert "item_1551265385290" in res
    assert res["item_1551265385290"] == [{'subitem_1551256462220': [{'subitem_1551256653656': 'テスト助成機関', 'subitem_1551256657859': 'ja'}], 'subitem_1551256454316': [{'subitem_1551256614960': '22222', 'subitem_1551256619706': 'Crossref Funder'}], 'subitem_1551256688098': [{'subitem_1551256691232': 'テスト研究', 'subitem_1551256694883': 'ja'}], 'subitem_1551256665850': [{'subitem_1551256671920': '1111', 'subitem_1551256679403': 'https://test.research.com'}]}]

# def add_geo_location(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_geo_location -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_geo_location(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("datacite:geoLocation")
    add_geo_location(schema, mapping, res, metadata)
    assert "item_key:item_1570068313185" not in res
    

# def add_relation(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_relation -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_relation(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("jpcoar:relation")
    add_relation(schema, mapping, res, metadata)
    assert "item_1551265227803" in res
    assert res["item_1551265227803"] == [{'subitem_1551256388439': 'isVersionOf', 'subitem_1551256480278': [{'subitem_1551256498531': '関連情報テスト', 'subitem_1551256513476': 'ja'}], 'subitem_1551256465077': [{'subitem_1551256478339': '1111111', 'subitem_1551256629524': 'ARK'}]}, {'subitem_1551256388439': 'isVersionOf', 'subitem_1551256465077': [{'subitem_1551256478339': 'https://192.168.56.103/records/3', 'subitem_1551256629524': 'URI'}]}]
    
# def add_rights_holder(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_rights_holder -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_rights_holder(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("jpcoar:rightsHolder")
    add_rights_holder(schema, mapping, res, metadata)
    assert "item_1551264767789" in res
    assert res["item_1551264767789"] == [{'subitem_1551257249371': [{'subitem_1551257255641': 'テスト\u3000太郎', 'subitem_1551257257683': 'ja'}]}]

# def add_resource_type(schema, mapping, res, metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiharvester tests/test_harvester.py::test_add_resource_type -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiharvester/.tox/c1/tmp
def test_add_resource_type(mapper_jpcoar):
    schema, mapping, res, metadata = mapper_jpcoar("dc:type")
    add_resource_type(schema, mapping, res, metadata)
    assert "item_1551265032053" in res
    assert res["item_1551265032053"] == [{'resourcetype': 'newspaper', 'resourceuri': 'http://purl.org/coar/resource_type/c_2fe3'}]


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

