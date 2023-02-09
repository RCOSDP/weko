import pytest
from tests.helpers import json_data

import weko_records.config as config
from weko_records.api import ItemTypeProps
from weko_records.serializers.schemas.csl import RecordSchemaCSLJSON

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
