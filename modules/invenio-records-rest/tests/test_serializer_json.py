# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio serializer tests."""

from __future__ import absolute_import, print_function

import json

from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record
from marshmallow import Schema, fields

from invenio_records_rest.schemas.fields import \
    PersistentIdentifier as PIDField
from invenio_records_rest.serializers.json import JSONSerializer

from weko_records.models import ItemType, ItemTypeName, ItemTypeMapping

def hide_item_type(db):
    # item_1717569452044, item_1717639687882.subitem_link_text is hidden item
    with open('tests/data/item_type_with_hide/schema.json') as f:
        schema = json.load(f)

    with open('tests/data/item_type_with_hide/form.json') as f:
        form = json.load(f)
    
    with open('tests/data/item_type_with_hide/render.json') as f:
        render = json.load(f)
    
    with open('tests/data/item_type_with_hide/mapping.json') as f:
        mapping = json.load(f)
        
    item_type_name = ItemTypeName(id=1, name='hide_itemtype', has_site_license=True, is_active=True)
    item_type = ItemType(
        id=1, name_id=1, harvesting_type=True, schema=schema, form=form, render=render, tag=1, version_id=1, is_deleted=False
    )
    item_type_mapping = ItemTypeMapping(id=1, item_type_id=1, mapping=mapping)
    with db.session.begin_nested():
        db.session.add(item_type_name)
        db.session.add(item_type)
        db.session.add(item_type_mapping)
    db.session.commit()

# .tox/c1/bin/pytest --cov=invenio_records_rest tests/test_serializer_json.py::test_serialize -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-records-rest/.tox/c1/tmp
def test_serialize(db):
    """Test JSON serialize."""
    class TestSchema(Schema):
        title = fields.Str(attribute='metadata.mytitle')
        id = PIDField(attribute='pid.pid_value')

    data = json.loads(JSONSerializer(TestSchema).serialize(
        PersistentIdentifier(pid_type='recid', pid_value='2'),
        Record({'mytitle': 'test'})
    ))
    assert data['title'] == 'test'
    assert data['id'] == '2'
    
    # item_type_id not in record
    class TestSchema(Schema):
        id=fields.Integer(attribute='pid.pid_value')
        metadata = fields.Raw()
    record_data = {'recid':'2','$schema':'https://test.org/schema/deposits/deposit-v1.0.0.json','status':'draft'}
    data = json.loads(JSONSerializer(TestSchema).serialize(
        PersistentIdentifier(pid_type='recid', pid_value=2),
        Record(record_data)
    ))
    assert data['metadata'] == record_data
    assert data['id'] == 2
    
    # item_type_id in record
    record_data = {
        '_oai':{'id':'oai:weko3.example.org:00000001'},
        'path':['1'],
        'owner':'1',
        'recid':'1',
        'title':['test_item'],
        'pubdate':{'attribute_name':'PubDate','attribute_value':'2024-05-28'},
        '_buckets': {'deposit': '0af4f217-7ed8-4813-94c5-24d9bc3ec8f8'},
        '_deposit': {
            'id': '1',
            'pid': {'type': 'depid','value': '1','revision_id': 0},
            'owner': '1',
            'owners': [1],
            'status': 'published',
            'created_by': 1,
            'owners_ext': {'email': 'test_user@test.org','username': '','displayname': ''}
        },
        'item_title':'test_item',
        'item_type_id':'1',
        'publish_status':'0',
        'item_1717569423159': {'attribute_name': 'Title','attribute_value_mlt': [{'subitem_title': 'hide作成者2','subitem_title_language': 'ja'}]},
        'item_1717569433997': {'attribute_name': '資源タイプ','attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_5794','resourcetype': 'conference paper'}]},
        'item_1717569452044': {'attribute_name':'作成者','attribute_type':'creator','attribute_value_mlt':[{'givenNames': [{'givenName': '太郎','givenNameLang': 'ja'}],'familyNames': [{'familyName': 'テスト','familyNameLang': 'ja'}],'creatorMails': [{'creatorMail': 'test.taro@test.org'}],'creatorNames': [{'creatorName': 'テスト, 太郎','creatorNameLang': 'ja'}],'nameIdentifiers': [{'nameIdentifier': '1','nameIdentifierScheme': 'WEKO'}]},{'givenNames': [{'givenName': '次郎','givenNameLang': 'ja'},{'givenName': 'ziro','givenNameLang': 'en'}],'familyNames': [{'familyName': 'テスト','familyNameLang': 'ja'},{'familyName': 'test','familyNameLang': 'en'}],'creatorMails': [{'creatorMail': 'test.ziro@test.org'}],'creatorNames': [{'creatorName': 'テスト, 次郎','creatorNameLang': 'ja'},{'creatorName': 'test, ziro','creatorNameLang': 'en'}],'nameIdentifiers': [{'nameIdentifier': '2','nameIdentifierScheme': 'WEKO'}]}]},
        'item_1717639687882': {'attribute_name':'URL','attribute_value_mlt':[{'subitem_link_url':'https://test.com','subitem_link_text':'test_link','subitem_link_language':'en'}]},
        'relation_version_is_last': True
    }
    test_data = {
        '_oai':{'id':'oai:weko3.example.org:00000001'},
        'path':['1'],
        'owner':'1',
        'recid':'1',
        'title':['test_item'],
        'pubdate':{'attribute_name':'PubDate','attribute_value':'2024-05-28'},
        '_buckets': {'deposit': '0af4f217-7ed8-4813-94c5-24d9bc3ec8f8'},
        '_deposit': {
            'id': '1',
            'pid': {'type': 'depid','value': '1','revision_id': 0},
            'owner': '1',
            'owners': [1],
            'status': 'published',
            'created_by': 1,
        },
        'item_title':'test_item',
        'item_type_id':'1',
        'publish_status':'0',
        'item_1717569423159': {'attribute_name': 'Title','attribute_value_mlt': [{'subitem_title': 'hide作成者2','subitem_title_language': 'ja'}]},
        'item_1717569452044': {'attribute_name':'作成者','attribute_type':'creator','attribute_value_mlt':[{'givenNames': [{'givenName': '太郎','givenNameLang': 'ja'}],'familyNames': [{'familyName': 'テスト','familyNameLang': 'ja'}],'creatorNames': [{}],'nameIdentifiers': [{'nameIdentifier': '1','nameIdentifierScheme': 'WEKO'}]},{'givenNames': [{'givenName': '次郎','givenNameLang': 'ja'},{'givenName': 'ziro','givenNameLang': 'en'}],'familyNames': [{'familyName': 'テスト','familyNameLang': 'ja'},{'familyName': 'test','familyNameLang': 'en'}],'creatorNames': [{},{}],'nameIdentifiers': [{'nameIdentifier': '2','nameIdentifierScheme': 'WEKO'}]}]},        'item_1717639687882': {'attribute_name':'URL','attribute_value_mlt':[{'subitem_link_url':'https://test.com','subitem_link_language':'en'}]},
        'relation_version_is_last': True
    }
    hide_item_type(db)
    data = json.loads(JSONSerializer(TestSchema).serialize(
        PersistentIdentifier(pid_type='recid', pid_value=1),
        Record(json.loads(json.dumps(record_data)))
    ))
    assert data['metadata'] == test_data
    assert data['id'] == 1

# .tox/c1/bin/pytest --cov=invenio_records_rest tests/test_serializer_json.py::test_serialize_search -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-records-rest/.tox/c1/tmp
def test_serialize_search(app, db):
    """Test JSON serialize."""
    class TestSchema(Schema):
        title = fields.Str(attribute='metadata.mytitle')
        id = PIDField(attribute='pid.pid_value')

    def fetcher(obj_uuid, data):
        assert obj_uuid in ['a', 'b']
        return PersistentIdentifier(pid_type='recid', pid_value=data['pid'])

    data = json.loads(JSONSerializer(TestSchema).serialize_search(
        fetcher,
        dict(
            hits=dict(
                hits=[
                    {'_source': dict(mytitle='test1', pid='1'), '_id': 'a',
                     '_version': 1},
                    {'_source': dict(mytitle='test2', pid='2'), '_id': 'b',
                     '_version': 1},
                ],
                total=2,
            ),
            aggregations={},
        )
    ))

    assert data['aggregations'] == {}
    assert 'links' in data
    assert data['hits'] == dict(
        hits=[
            dict(title='test1', id='1'),
            dict(title='test2', id='2'),
        ],
        total=2,
    )
    
    def fetcher(obj_uuid, data):
        return PersistentIdentifier(pid_type='recid', pid_value=data['control_number'])
    class TestSchema(Schema):
        id=fields.Integer(attribute='pid.pid_value')
        metadata = fields.Raw()
        
    hits = [{
        '_id':'a','_version': 1,
        '_source':{
            '_item_metadata': {
                '_oai':{'id':'oai:weko3.example.org:00000001'},
                'path':['1'],
                'owner':'1',
                'recid':'1',
                'title':['test_item'],
                'pubdate':{'attribute_name':'PubDate','attribute_value':'2024-05-28'},
                '_buckets': {'deposit': '0af4f217-7ed8-4813-94c5-24d9bc3ec8f8'},
                '_deposit': {
                    'id': '1',
                    'pid': {'type': 'depid','value': '1','revision_id': 0},
                    'owner': '1',
                    'owners': [1],
                    'status': 'published',
                    'created_by': 1,
                    'owners_ext': {'email': 'test_user@test.org','username': '','displayname': ''}
                },
                'item_title':'test_item',
                'item_type_id':'1',
                'publish_status':'0',
                'item_1717569423159': {'attribute_name': 'Title','attribute_value_mlt': [{'subitem_title': 'hide作成者2','subitem_title_language': 'ja'}]},
                'item_1717569433997': {'attribute_name': '資源タイプ','attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_5794','resourcetype': 'conference paper'}]},
                'item_1717569452044': {'attribute_name':'作成者','attribute_type':'creator','attribute_value_mlt':[{'givenNames': [{'givenName': '太郎','givenNameLang': 'ja'}],'familyNames': [{'familyName': 'テスト','familyNameLang': 'ja'}],'creatorMails': [{'creatorMail': 'test.taro@test.org'}],'creatorNames': [{'creatorName': 'テスト, 太郎','creatorNameLang': 'ja'}],'nameIdentifiers': [{'nameIdentifier': '1','nameIdentifierScheme': 'WEKO'}]},{'givenNames': [{'givenName': '次郎','givenNameLang': 'ja'},{'givenName': 'ziro','givenNameLang': 'en'}],'familyNames': [{'familyName': 'テスト','familyNameLang': 'ja'},{'familyName': 'test','familyNameLang': 'en'}],'creatorMails': [{'creatorMail': 'test.ziro@test.org'}],'creatorNames': [{'creatorName': 'テスト, 次郎','creatorNameLang': 'ja'},{'creatorName': 'test, ziro','creatorNameLang': 'en'}],'nameIdentifiers': [{'nameIdentifier': '2','nameIdentifierScheme': 'WEKO'}]}]},
                'item_1717639687882': {'attribute_name':'URL','attribute_value_mlt':[{'subitem_link_url':'https://test.com','subitem_link_text':'test_link','subitem_link_language':'en'}]},
                'relation_version_is_last': True
            },
            'feedback_mail_list':['test.taro@test.org'],
            'creator':{
                'givenName': ['太郎'], 'familyName':['テスト'], 'creatorName': ['テスト, 太郎'], 'nameIdentifier':['1']
            },
            'weko_creator_id':'1',
            'type':[ 'conference paper'],
            'title': ['test_item'],
            'itemtype':'hide_itemtype',
            'control_number': '1',
            'weko_shared_id':-1,
            'relation_version_is_last': True
        }
    }]
    hide_item_type(db)
    with app.test_request_context():
        # not has permission
        data = json.loads(JSONSerializer(TestSchema).serialize_search(
            fetcher,
            {'hits':{'hits':json.loads(json.dumps(hits)),'total':1}},
            aggregation={}
        ))
        assert data['aggregations'] == {}
        assert 'links' in data
        res_metadata = data['hits']['hits'][0]
        assert res_metadata['metadata']['_item_metadata']['item_1717569452044']['attribute_value_mlt'][0]['creatorNames'][0] == {}
        assert 'creatorName' not in res_metadata['metadata']['creator']
        assert 'subitem_link_text' not in res_metadata['metadata']['_item_metadata']['item_1717639687882']['attribute_value_mlt'][0]
        assert 'type' not in res_metadata['metadata']
        assert res_metadata['metadata']['feedback_mail_list'] == []
        
        # has permission
        from flask_login import login_user
        from invenio_accounts.testutils import create_test_user
        login_user(create_test_user(email='user@test.org'))
        data = json.loads(JSONSerializer(TestSchema).serialize_search(
            fetcher,
            {'hits':{'hits':json.loads(json.dumps(hits)),'total':1}},
            aggregation={}
        ))
        assert data['aggregations'] == {}
        assert 'links' in data
        res_metadata = data['hits']['hits'][0]
        assert res_metadata['metadata']['_item_metadata']['item_1717569452044']['attribute_value_mlt'][0]['creatorNames'][0] != {}
        assert 'creatorName' in res_metadata['metadata']['creator']
        assert 'subitem_link_text' in res_metadata['metadata']['_item_metadata']['item_1717639687882']['attribute_value_mlt'][0]
        assert 'type' in res_metadata['metadata']
        assert res_metadata['metadata']['feedback_mail_list'] == []


def test_serialize_pretty(app, db):
    """Test pretty JSON."""
    class TestSchema(Schema):
        title = fields.Str(attribute='metadata.title')

    pid = PersistentIdentifier(pid_type='recid', pid_value='2'),
    rec = Record({'title': 'test'})

    with app.test_request_context():
        assert JSONSerializer(TestSchema).serialize(pid, rec) == \
            '{"title":"test"}'

    with app.test_request_context('/?prettyprint=1'):
        assert JSONSerializer(TestSchema).serialize(pid, rec) == \
            '{\n  "title": "test"\n}'
