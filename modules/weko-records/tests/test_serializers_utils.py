import pytest
import uuid
import json
import base64
import copy
from lxml import etree
from tests.helpers import json_data
from mock import patch, MagicMock
from werkzeug import ImmutableMultiDict
from werkzeug.datastructures import MultiDict, CombinedMultiDict
from invenio_pidstore.models import PersistentIdentifier
from invenio_accounts.testutils import login_user_via_session
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
    get_wekolog,
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
    _item_id = 'item_1551265302121'
    result = get_metadata_from_map(meta[0]['item_1551265302121'], _item_id)
    assert result == {'item_1551265302121' : 'testtest'}
    _item_id = 'pubdate'
    result = get_metadata_from_map(meta[0]['item_1551265302122'], _item_id)
    assert result == {'pubdate.key' : 'test1'}
    result = get_metadata_from_map(meta[0]['item_15512653021233'], _item_id)
    assert result == {'pubdate.mlt' : 'test'}
    result = get_metadata_from_map(meta[0]['item_15512653021234'], _item_id)
    assert result == {'pubdate.key' : ['test1', 'test2', 'test3']}
    result = get_metadata_from_map(meta[0]['item_15512653021235'], _item_id)
    assert result == {'pubdate.key.subkey' : 'abcd'}

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

# def get_wekolog(hit, log_term):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_utils.py::test_get_wekolog -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_wekolog(db, record1):
    hit = {'_id': record1[0].object_uuid }
    result = get_wekolog(hit, '2022-01')
    assert result == {'terms': '2022-01', 'view': '0', 'download': '0'}

# def get_wekolog(hit, log_term):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_utils.py::test_get_wekolog_2 -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_wekolog_2(db, record2):
    hit = {'_id': record2[0].object_uuid }
    result = get_wekolog(hit, '2022-01')
    assert result == {'terms': '2022-01', 'view': '0', 'download': '0'}

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
def test_open_search_detail_data(app, db, db_index, record1, render, form, mapping, hit, licence):
    def fetcher(obj_uuid, data):
        assert obj_uuid=="1"
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
    Mapping.create(
        item_type_id=_item_type.id,
        mapping=json_data(mapping)
    )
    _data = {
        'lang': 'en',
        'log_term': '2021-01'
    }
    hit_data = json_data(hit)
    hit_data['_id'] = record1[0].object_uuid
    _search_result = {'hits': {'total': 1, 'hits': [hit_data]}}
    detail = OpenSearchDetailData(fetcher, _search_result, 'rss')
    with app.test_request_context(headers=[('Accept-Language','en')], query_string=_data):
        res = detail.output_open_search_detail_data()
        res = res.decode('utf-8')
        cnt = 1 if res.find('wekolog:terms') else 0
        cnt += 1 if res.find('wekolog:view') else 0
        cnt += 1 if res.find('wekolog:download') else 0
        assert True if cnt == 3 else False

    _data = {
        'lang': 'en',
        'index_id': "1"
    }
    hit_data1 = copy.deepcopy(hit_data)
    hit_data1['_source']['_item_metadata']['pubdate']['attribute_value'] = ""
    _search_result = {'hits': {'total': 1, 'hits': [hit_data1]}}
    detail = OpenSearchDetailData(fetcher, _search_result, 'rss')
    with app.test_request_context(headers=[('Accept-Language','en')], query_string=_data):
        res = detail.output_open_search_detail_data()
        res = res.decode('utf-8')
        cnt = 1 if res.find('wekolog:terms') == -1 else 0
        cnt += 1 if res.find('wekolog:view') == -1 else 0
        cnt += 1 if res.find('wekolog:download') == -1 else 0
        assert True if cnt == 3 else False

    _search_result = {'hits': {'total': 0, 'hits': []}}
    data = OpenSearchDetailData(fetcher, _search_result, 'rss')
    with app.test_request_context():
        assert data.output_open_search_detail_data()

    # test for atom
    _data = {
        'lang': 'en',
        'index_id': 1,
    }
    _search_result = {'hits': {'total': 2, 'hits': [hit_data, hit_data]}}
    data = OpenSearchDetailData(fetcher, _search_result, 'atom')
    with app.test_request_context(headers=[('Accept-Language','en')], query_string=_data):
        assert data.output_open_search_detail_data()
        with patch("weko_records.api.Mapping.get_record", return_value=dict()):
            assert data.output_open_search_detail_data()
        with patch("weko_records.serializers.utils.get_metadata_from_map", return_value=None):
            assert data.output_open_search_detail_data()

    hit_data2 = json_data("data/record_hit/record_hit1_2.json")
    _search_result = {'hits': {'total': 1, 'hits': [hit_data2]}}
    data = OpenSearchDetailData(fetcher, _search_result, 'atom')
    with app.test_request_context(headers=[('Accept-Language','en')], query_string=_data):
        assert data.output_open_search_detail_data()

    hit_data3 = copy.deepcopy(hit_data)
    hit_data3['_source']['_item_metadata'] = {
        "item_type_id":"1",
        "control_number": "1",
        "item_title":"Test title",
    }
    _search_result = {'hits': {'total': 1, 'hits': [hit_data3]}}
    data = OpenSearchDetailData(fetcher, _search_result, 'atom')
    with app.test_request_context(headers=[('Accept-Language','en')], query_string=_data):
        assert data.output_open_search_detail_data()

    _data = {
        'lang': 'ja',
        'index_id': "aaa",
        'idx': "bbb",
    }
    hit_data4 = copy.deepcopy(hit_data)
    hit_data4['_source']['_item_metadata']['path'] = ["9999"]
    _search_result = {'hits': {'total': 1, 'hits': [hit_data4]}}
    data = OpenSearchDetailData(fetcher, _search_result, 'atom')
    with app.test_request_context(headers=[('Accept-Language','ja')], query_string=_data):
        assert data.output_open_search_detail_data()
    
    # test for atom with Yhandle
    _data = {
        'lang': 'ja',
        'index_id': "1",
        'idx': "bbb",
    }
    _search_result = {'hits': {'total': 1, 'hits': [hit_data]}}
    data = OpenSearchDetailData(fetcher, _search_result, 'atom')
    with app.test_request_context(headers=[('Accept-Language','ja')], query_string=_data):
        with patch("invenio_pidstore.models.PersistentIdentifier.get_by_object", return_value=PersistentIdentifier(pid_type='yhdl', pid_value="http://test.com/1000/00000001/")):
            res = data.output_open_search_detail_data()
            res = res.decode('utf-8')
            assert res.find('<link href="http://test.com/1000/00000001/"/>') > 0
    _data['index_id'] = "aaa"
    with app.test_request_context(headers=[('Accept-Language','ja')], query_string=_data):
        with patch("invenio_pidstore.models.PersistentIdentifier.get_by_object", return_value=PersistentIdentifier(pid_type='yhdl', pid_value="http://test.com/1000/00000001")):
            res = data.output_open_search_detail_data()
            res = res.decode('utf-8')
            assert res.find('<link href="http://test.com/1000/00000001/"/>') > 0


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
    item_map = {
        'volume.@value': 'item_1617186959569.subitem_1551256328147',
        'issue.@value': 'item_1617186981471.subitem_1551256294723',
        'pageStart.@value': 'item_1617187024783.subitem_1551256198917',
        'pageEnd.@value': 'item_1617187045071.subitem_1551256185532',
    }
    item_metadata = {
        'item_type_id': '1',
        'item_title': 'test',
        'control_number': '1',
        'path': ['1'],
        'item_1617186959569': {'attribute_name': 'Volume Number', 'attribute_value_mlt': [{'subitem_1551256328147': '21'}]},
        'item_1617186981471': {'attribute_name': 'Issue Number', 'attribute_value_mlt': [{'subitem_1551256294723': '13'}]},
        'item_1617187024783': {'attribute_name': 'Page Start', 'attribute_value_mlt': [{'subitem_1551256198917': '167'}]},
        'item_1617187045071': {'attribute_name': 'Page End', 'attribute_value_mlt': [{'subitem_1551256185532': '223'}]},
        'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2025-06-01'},
    }
    hit = {
        '_source': {
            '_item_metadata': item_metadata,
            '_oai': {'id': 'dummy_oai'},
            'itemtype': 'dummy_itemtype',
            '_created': None,
            '_updated': None,
        }
    }
    with patch("weko_records.api.Mapping.get_record", return_value={}), \
         patch("weko_records.serializers.utils.get_mapping", return_value=item_map), \
         patch("weko_records.serializers.utils.get_metadata_from_map", side_effect=[
             {'item_1617186959569.subitem_1551256328147': ['21']},   # volume
             {'item_1617186981471.subitem_1551256294723': ['13']},   # issue
             {'item_1617187024783.subitem_1551256198917': ['167']},  # pageStart
             {'item_1617187045071.subitem_1551256185532': ['223']},  # pageEnd
         ]), \
         patch("weko_records.serializers.utils.Index.query") as mock_index_query:
        mock_index_query.filter_by.return_value.one_or_none.return_value = MagicMock(index_name='dummy_index', index_name_english='dummy_index_en')
        sample_copy = copy.deepcopy(sample)
        with app.test_request_context():
            sample_copy.search_result = {'hits': {'total': 1, 'hits': [hit]}}
            sample_copy.output_type = "atom"
            xml = sample_copy.output_open_search_detail_data()
            assert b'<prism:volume>21</prism:volume>' in xml
            assert b'<prism:number>13</prism:number>' in xml
            assert b'<prism:startingPage>167</prism:startingPage>' in xml
            assert b'<prism:endingPage>223</prism:endingPage>' in xml

@pytest.mark.parametrize(
    "item_map, item_metadata_key, xml_tag",
    [
        ({'volume.@value': 'volume_key'}, 'volume_key', 'prism:volume'),
        ({'issue.@value': 'issue_key'}, 'issue_key', 'prism:number'),
        ({'pageStart.@value': 'page_start_key'}, 'page_start_key', 'prism:startingPage'),
        ({'pageEnd.@value': 'page_end_key'}, 'page_end_key', 'prism:endingPage'),
    ]
)

# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_utils.py::test_output_open_search_detail_data_field_false -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_output_open_search_detail_data_field_false(app, item_map, item_metadata_key, xml_tag):
    # item_id does not exist in item_metadata
    item_metadata = {
        'item_type_id': '1',
        'item_title': 'test',
        'control_number': '1',
        'path': ['1'],
        'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2025-06-01'},
    }
    hit = {
        '_source': {
            '_item_metadata': item_metadata,
            '_oai': {'id': 'dummy_oai'},
            'itemtype': 'dummy_itemtype',
            '_created': None,
            '_updated': None,
        }
    }
    with patch("weko_records.api.Mapping.get_record", return_value={}), \
         patch("weko_records.serializers.utils.get_mapping", return_value=item_map), \
         patch("weko_records.serializers.utils.get_metadata_from_map", return_value={item_metadata_key: ['val']}), \
         patch("weko_records.serializers.utils.Index.query") as mock_index_query:
        mock_index_query.filter_by.return_value.one_or_none.return_value = MagicMock(index_name='dummy_index', index_name_english='dummy_index_en')
        sample_copy = copy.deepcopy(sample)
        with app.test_request_context():
            sample_copy.search_result = {'hits': {'total': 1, 'hits': [hit]}}
            sample_copy.output_type = "atom"
            xml = sample_copy.output_open_search_detail_data()
            assert f'<{xml_tag}>' not in xml.decode()

    # get_metadata_from_map returns a non-dict value
    item_metadata2 = dict(item_metadata)
    item_metadata2[item_metadata_key.split('.')[0]] = {'attribute_name': 'dummy', 'attribute_value_mlt': [{'dummy': 'val'}]}
    hit2 = copy.deepcopy(hit)
    hit2['_source']['_item_metadata'] = item_metadata2
    with patch("weko_records.api.Mapping.get_record", return_value={}), \
         patch("weko_records.serializers.utils.get_mapping", return_value=item_map), \
         patch("weko_records.serializers.utils.get_metadata_from_map", return_value=None), \
         patch("weko_records.serializers.utils.Index.query") as mock_index_query:
        mock_index_query.filter_by.return_value.one_or_none.return_value = MagicMock(index_name='dummy_index', index_name_english='dummy_index_en')
        sample_copy = copy.deepcopy(sample)
        with app.test_request_context():
            sample_copy.search_result = {'hits': {'total': 1, 'hits': [hit2]}}
            sample_copy.output_type = "atom"
            xml = sample_copy.output_open_search_detail_data()
            assert f'<{xml_tag}>' not in xml.decode()

    # get_metadata_from_map returns a string value
    with patch("weko_records.api.Mapping.get_record", return_value={}), \
         patch("weko_records.serializers.utils.get_mapping", return_value=item_map), \
        patch("weko_records.serializers.utils.get_metadata_from_map", return_value={item_metadata_key: 'abc'}), \
        patch("weko_records.serializers.utils.Index.query") as mock_index_query:
        mock_index_query.filter_by.return_value.one_or_none.return_value = MagicMock(index_name='dummy_index', index_name_english='dummy_index_en')
        sample_copy = copy.deepcopy(sample)
        with app.test_request_context():
            sample_copy.search_result = {'hits': {'total': 1, 'hits': [hit2]}}
            sample_copy.output_type = "atom"
            xml = sample_copy.output_open_search_detail_data()
            assert f'<{xml_tag}>abc</{xml_tag}>'.encode() in xml

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
