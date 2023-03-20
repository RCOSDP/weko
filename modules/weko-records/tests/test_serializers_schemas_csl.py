import pytest
import copy
from mock import patch, MagicMock
from tests.helpers import json_data

import weko_records.config as config
from weko_records.api import ItemTypeProps
from weko_records.serializers.schemas.csl import RecordSchemaCSLJSON, get_data_from_mapping

# class RecordSchemaCSLJSON(Schema):
#     def get_version(self, obj):
#     def get_issue_date(self, obj):
#     def get_page(self, obj):
#     def get_doi(self, obj):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_schemas_csl.py::test_record_schema_csljson -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
params=[
    ("data/item_type/item_type_render1.json",
     "data/item_type/item_type_form1.json",
     "data/item_type/item_type_mapping1.json",
     "data/record_hit/record_hit1.json",
     True)]
@pytest.mark.parametrize("render, form, mapping, hit, licence", params)
def test_record_schema_csljson(app, db, db_index, render, form, mapping, hit, licence):
    _obj = {
        'metadata': json_data(hit)['_source']['_item_metadata'],
        'mapping_dict': {
            'datacite:date': ['item_date', 'subitem_date_value'],
            'datacite:date__lang': ['en'],
            'jpcoar:pageStart': ['item_bibliographic', 'bibliographic_pageStart'],
            'jpcoar:pageStart__lang': ['en'],
            'jpcoar:pageEnd': ['item_bibliographic', 'bibliographic_pageEnd'],
            'jpcoar:pageEnd__lang': ['en']
        },
        'item_date': [
            {
                'subitem_date_value': '2021-10-26',
                'subitem_date_type': 'Available'
            },
            {
                'subitem_date_value': '2021-10-26',
                'subitem_date_type': 'Issued'
            }
        ],
        'item_bibliographic': [
            {
                "bibliographic_titles":[
                    {
                        "bibliographic_titleLang":"en",
                        "bibliographic_title":"this is test bibliographic title"
                    }
                ],
                "bibliographic_volume": "10",
                "bibliographic_issue": "7",
                "bibliographic_pageStart": "1",
                "bibliographic_pageEnd": "11"
            }
        ]
    }
    ItemTypeProps.create(
        property_id=1,
        name='prop1',
        schema={            
            'properties': {
                'subitem_version': {
                    'format': 'text',
                    'title': 'Version',
                    'type': 'string'
                }
            }
        },
        form_single={'key': 'item1'},
        form_array=[{'key': 'item1'}]
    )

    # get_version
    config.WEKO_ITEMPROPS_SCHEMAID_VERSION = 1
    _recordschema = RecordSchemaCSLJSON()
    ver = RecordSchemaCSLJSON.get_version(_recordschema, _obj)
    assert ver=='1.0.0'

    # get_issue_date
    with app.test_request_context():
        issue_date = RecordSchemaCSLJSON.get_issue_date(_recordschema, _obj)
        assert issue_date=={'date-parts': [[2021, 10, 26]]}

    # get_issue_date
    with app.test_request_context():
        page = RecordSchemaCSLJSON.get_page(_recordschema, _obj)
        assert page=='1-11'

    # get_doi


# def get_data_from_mapping(key, obj):
def test_get_data_from_mapping(i18n_app):
    key = "key1"
    key_2 = "key_2"
    obj = {
        "mapping_dict": {
            key: [key_2, "content_b"],
            "key1__lang": "key1__lang_1",
            "content_4": "content_44",
        },
        key_2: {
            key: ["content_c", "content_d"],
            "key1__lang": "key1__lang_2",
            "content_5": {
                "mapping_dict": {
                    key: [key_2, "content_b"],
                    "key1__lang": "key1__lang_1",
                    "content_4": "content_44",
                },
                key_2: {
                    key: ["content_cc", "content_dd"],
                    "key1__lang": "key1__lang_2",
                    "content_5": "content_5555",
                    "content_b": "if_value_key_in_meta",
                }
            },
            "content_b": "if_value_key_in_meta",
        }
    }

    assert get_data_from_mapping(key=key, obj=obj) != None

    obj[key_2]["1"] = "en"
    assert get_data_from_mapping(key=key, obj=obj) != None

    del obj[key_2]["content_b"]
    assert get_data_from_mapping(key=key, obj=obj) != None

    obj[key_2]["content_b"] = "if_value_key_in_meta"
    obj_2 = copy.deepcopy(obj)
    obj_2[key_2] = [obj_2[key_2]]
    assert get_data_from_mapping(key=key, obj=obj_2) != None

    with patch("weko_records.serializers.schemas.csl.current_i18n"):
        assert get_data_from_mapping(key=key, obj=obj) != None


# class RecordSchemaCSLJSON(Schema):
test = RecordSchemaCSLJSON()

# def get_version(self, obj): 
def test_get_version_RecordSchemaCSLJSON(app):
    obj = MagicMock()

    with patch("weko_records.serializers.schemas.csl._get_itemdata", return_value=""):
        with patch("weko_records.serializers.schemas.csl.get_attribute_schema", return_value=""):
            assert test.get_version(obj) != None

    with patch("weko_records.serializers.schemas.csl._get_itemdata", return_value=[1,2]):

        schema = {
            "properties": {}
        }

        with patch("weko_records.serializers.schemas.csl.get_attribute_schema", return_value=schema):
            assert test.get_version(obj) != None

            with patch("weko_records.serializers.schemas.csl._get_mapping_data", return_value=(1, None)):
                assert test.get_version(obj) != None

    with patch("weko_records.serializers.schemas.csl.get_attribute_schema", return_value=schema):
        assert test.get_version({"metadata": ""}) != None


# def get_issue_date(self, obj): 
def test_get_issue_date_RecordSchemaCSLJSON(app):
    obj = MagicMock()

    with patch("weko_records.serializers.schemas.csl.get_data_from_mapping", return_value=""):
        assert test.get_issue_date(obj) != None


# def get_page(self, obj): 
def test_get_page_RecordSchemaCSLJSON(app):
    obj = MagicMock()

    with patch("weko_records.serializers.schemas.csl.get_data_from_mapping", return_value=""):
        assert test.get_page(obj) != None


# def get_doi(self, obj): 
def test_get_doi_RecordSchemaCSLJSON(app):
    data1 = MagicMock()
    data1.pid_doi = MagicMock()
    data1.pid_doi.pid_value = "pid_value_9999"
    data1.pid_doi.pid_type = "pid_type_9999"

    obj = {
        "record": data1,
        "metadata": {
            "identifier_data": "identifier_data_9999"
        },
    }

    with patch("weko_records.serializers.schemas.csl.get_data_from_mapping", return_value="identifier_data"):
        assert test.get_doi(obj) != None

    fields = MagicMock()

    def samplefunc(item):
        return "doi.org"

    fields.Method = samplefunc

    # with patch("marshmallow.fields.Method", return_value="doi.org"):
    with patch("weko_records.serializers.schemas.csl.fields.Method", return_value="doi.org"):
        test2 = RecordSchemaCSLJSON()