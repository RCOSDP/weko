# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration."""

from __future__ import absolute_import, print_function

import copy
import json
import os
import shutil
import sys
import tempfile
from os.path import dirname, join
import pytz
import uuid

import pytest
from mock import patch
from elasticsearch import Elasticsearch
from elasticsearch import VERSION as ES_VERSION
from elasticsearch.exceptions import RequestError
from elasticsearch_dsl import response, Search
from flask import Flask, url_for, Response
from flask_login import LoginManager, UserMixin
from tests.helpers import create_record

from invenio_access.models import ActionRoles, ActionUsers
from invenio_accounts import InvenioAccounts
from invenio_accounts.testutils import create_test_user
from invenio_access import InvenioAccess
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_i18n import InvenioI18N

from invenio_indexer import InvenioIndexer
from invenio_indexer.api import RecordIndexer
from invenio_indexer.signals import before_record_index
from invenio_pidstore import InvenioPIDStore
from invenio_records import InvenioRecords
from invenio_rest import InvenioREST
from invenio_search import InvenioSearch, RecordsSearch, current_search, \
    current_search_client
from sqlalchemy_utils.functions import create_database, database_exists
from weko_admin.models import AdminSettings,FacetSearchSetting
from weko_records import WekoRecords
from weko_records.models import ItemTypeName, ItemType, ItemTypeMapping
from weko_redis.redis import RedisConnection
from weko_records_ui.config import (
    WEKO_PERMISSION_ROLE_COMMUNITY,
    WEKO_PERMISSION_SUPER_ROLE_USER,
    WEKO_RECORDS_UI_LICENSE_DICT
)
from weko_index_tree.models import Index

from invenio_records_rest import InvenioRecordsREST, config
from invenio_records_rest.facets import terms_filter
from invenio_records_rest.utils import PIDConverter, deny_all
from invenio_records_rest.views import create_blueprint_from_app

sys.path.append(os.path.dirname(__file__))


class TestSearch(RecordsSearch):
    """Test record search."""

    class Meta:
        """Test configuration."""

        index = 'invenio-records-rest'
        doc_types = None

    def __init__(self, **kwargs):
        """Add extra options."""
        super(TestSearch, self).__init__(**kwargs)
        self._extra.update(**{'_source': {'excludes': ['_access']}})


class IndexFlusher(object):
    """Simple object to flush an index."""

    def __init__(self, search_class):
        """Initialize instance."""
        self.search_class = search_class

    def flush_and_wait(self):
        """Flush index and wait until operation is fully done."""
        current_search.flush_and_refresh(self.search_class.Meta.index)


@pytest.yield_fixture(scope='session')
def search_class():
    """Search class."""
    yield TestSearch


@pytest.yield_fixture()
def search_url():
    """Search class."""
    yield url_for('invenio_records_rest.recid_list')

class MockEs():
    def __init__(self,**keywargs):
        self.indices = self.MockIndices()
        self.es = Elasticsearch()
        self.cluster = self.MockCluster()
    def index(self, id="",version="",version_type="",index="",doc_type="",body="",**arguments):
        pass
    def delete(self,id="",index="",doc_type="",**kwargs):
        return Response(response=json.dumps({}),status=500)
    @property
    def transport(self):
        return self.es.transport
    class MockIndices():
        def __init__(self,**keywargs):
            self.mapping = dict()
        def delete(self,index="", ignore=""):
            pass
        def delete_template(self,index=""):
            pass
        def create(self,index="",body={},ignore=""):
            self.mapping[index] = body
        def put_alias(self,index="", name="", ignore=""):
            pass
        def put_template(self,name="", body={}, ignore=""):
            pass
        def refresh(self,index=""):
            pass
        def exists(self, index="", **kwargs):
            if index in self.mapping:
                return True
            else:
                return False
        def flush(self,index="",wait_if_ongoing=""):
            pass
        def delete_alias(self, index="", name="",ignore=""):
            pass
        
        # def search(self,index="",doc_type="",body={},**kwargs):
        #     pass
    class MockCluster():
        def __init__(self,**kwargs):
            pass
        def health(self, wait_for_status="", request_timeout=0):
            pass
@pytest.yield_fixture()
def app(request):
    """Flask application fixture.

    Note that RECORDS_REST_ENDPOINTS is used during application creation to
    create blueprints on the fly, hence once you have this fixture in a test,
    it's too late to customize the configuration variable. You can however
    customize it using parameterized tests:

    .. code-block:: python

    @pytest.mark.parametrize('app', [dict(
        endpoint=dict(
            search_class='conftest:TestSearch',
        )
    def test_mytest(app, db, es):
        # ...

    This will parameterize the default 'recid' endpoint in
    RECORDS_REST_ENDPOINTS.

    Alternatively:

    .. code-block:: python

    @pytest.mark.parametrize('app', [dict(
        records_rest_endpoints=dict(
            recid=dict(
                search_class='conftest:TestSearch',
            )
        )
    def test_mytest(app, db, es):
        # ...

    This will fully parameterize RECORDS_REST_ENDPOINTS.
    """
    instance_path = tempfile.mkdtemp()
    app = Flask('testapp', instance_path=instance_path)
    app.config.update(
        SECRET_KEY="SECRET_KEY",
        PRESERVE_CONTEXT_ON_EXCEPTION=False,
        DEBUG=False,
        ACCOUNTS_JWT_ENABLE=False,
        INDEXER_DEFAULT_DOC_TYPE="item-v1.0.0",
        INDEXER_DEFAULT_INDEX="{}-weko-item-v1.0.0".format("test"),
        SEARCH_ELASTIC_HOSTS=os.environ.get("SEARCH_ELASTIC_HOSTS", "elasticsearch"),
        RECORDS_REST_ENDPOINTS=copy.deepcopy(config.RECORDS_REST_ENDPOINTS),
        RECORDS_REST_DEFAULT_CREATE_PERMISSION_FACTORY=None,
        RECORDS_REST_DEFAULT_DELETE_PERMISSION_FACTORY=None,
        RECORDS_REST_DEFAULT_READ_PERMISSION_FACTORY=None,
        RECORDS_REST_DEFAULT_UPDATE_PERMISSION_FACTORY=None,
        RECORDS_REST_DEFAULT_RESULTS_SIZE=10,
        #RECORDS_REST_DEFAULT_SEARCH_INDEX=search_class.Meta.index,
        RECORDS_REST_DEFAULT_SEARCH_INDEX="test-weko",
        RECORDS_REST_FACETS={
            #search_class.Meta.index: {
            "test-weko": {
                'aggs': {
                    'stars': {'terms': {'field': 'stars'}}
                    #'control_number':{'terms':{'field':'control_number'}}
                },
                'post_filters': {
                    #'stars': terms_filter('stars'),
                    'control_number':terms_filter('control_number')
                },
                
            }
        },
        RECORDS_REST_SORT_OPTIONS={
            #search_class.Meta.index: dict(
            "test-weko": dict(
                year=dict(
                    fields=['year'],
                ),
                control_number=dict(
                    fields=['control_number']
                )
            )
        },
        SERVER_NAME='localhost:5000',
        SEARCH_INDEX_PREFIX='test-',
        SEARCH_UI_SEARCH_INDEX="{}-weko".format("test"),
        #SEARCH_UI_SEARCH_INDEX=search_class.Meta.index,
        CACHE_TYPE="redis",
        CACHE_REDIS_DB=0,
        CACHE_REDIS_HOST="redis",
        REDIS_PORT="6379",
        ACCOUNTS_SESSION_REDIS_DB_NO=1,
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'
        # ),
        #SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
        #                                  'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                           'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        TESTING=True,
        WEKO_PERMISSION_SUPER_ROLE_USER=WEKO_PERMISSION_SUPER_ROLE_USER,
        WEKO_PERMISSION_ROLE_COMMUNITY=WEKO_PERMISSION_ROLE_COMMUNITY,
        EMAIL_DISPLAY_FLG = True,
        WEKO_RECORDS_UI_LICENSE_DICT=WEKO_RECORDS_UI_LICENSE_DICT,
    )

    #app.config['RECORDS_REST_ENDPOINTS']['recid']['search_class'] = \
    #    search_class
    app.config['RECORDS_REST_ENDPOINTS']['recid']['search_index']='test-weko'
    app.config['RECORDS_REST_ENDPOINTS']['recid']['search_type']='item-v1.0.0'
    #app.config['RECORDS_REST_ENDPOINTS']['recid']['search_factory_imp']="weko_search_ui.query.es_search_factory"

    # Parameterize application.
    if hasattr(request, 'param'):
        if 'endpoint' in request.param:
            app.config['RECORDS_REST_ENDPOINTS']['recid'].update(
                request.param['endpoint'])
        if 'records_rest_endpoints' in request.param:
            original_endpoint = app.config['RECORDS_REST_ENDPOINTS']['recid']
            del app.config['RECORDS_REST_ENDPOINTS']['recid']
            for new_endpoint_prefix, new_endpoint_value in \
                    request.param['records_rest_endpoints'].items():
                new_endpoint = dict(original_endpoint)
                new_endpoint.update(new_endpoint_value)
                app.config['RECORDS_REST_ENDPOINTS'][new_endpoint_prefix] = \
                    new_endpoint
        if 'max_result_window' in request.param:
            app.config['RECORDS_REST_ENDPOINTS']['recid']['max_result_window'] = request.param['max_result_window']

    app.url_map.converters['pid'] = PIDConverter
    InvenioAccounts(app)
    InvenioAccess(app)
    InvenioDB(app)
    InvenioREST(app)
    InvenioRecords(app)
    InvenioIndexer(app)
    InvenioI18N(app)
    InvenioPIDStore(app)
    
    WekoRecords(app)
    search = InvenioSearch(app)
    #search = InvenioSearch(app, client=MockEs())
    #search.register_mappings(search_class.Meta.index, 'mock_module.mappings')
    InvenioRecordsREST(app)
    app.register_blueprint(create_blueprint_from_app(app))

    with app.app_context():
        yield app

    # Teardown instance path.
    shutil.rmtree(instance_path)


@pytest.yield_fixture()
def db(app):
    """Database fixture."""
    if not database_exists(str(db_.engine.url)) and \
            app.config['SQLALCHEMY_DATABASE_URI'] != 'sqlite://':
        create_database(db_.engine.url)
    db_.create_all()

    yield db_

    db_.session.remove()
    db_.drop_all()


@pytest.yield_fixture()
def es(app):
    """Elasticsearch fixture."""
    list(current_search.delete(ignore=[404]))
    try:
        list(current_search.create())
    except RequestError:
        list(current_search.delete(ignore=[404]))
        list(current_search.create(ignore=[400]))
    current_search_client.indices.refresh()
    yield current_search_client
    list(current_search.delete(ignore=[404]))

@pytest.fixture()
def esindex(app):
    with open("tests/data/item-v1.0.0.json","r") as f:
        mapping = json.load(f)
        
    current_search_client.indices.delete(index="test-*")
    try:
        current_search_client.indices.create(
            app.config["INDEXER_DEFAULT_INDEX"], body=mapping
        )
        current_search_client.indices.put_alias(
            index=app.config["INDEXER_DEFAULT_INDEX"], name="test-weko"
        )
    except:
        current_search_client.indices.create("test-weko-items", body=mapping)
        current_search_client.indices.put_alias(
            index="test-weko-items", name="test-weko"
        )
    try:
        yield current_search_client
    finally:
        current_search_client.indices.delete(index="test-*")

@pytest.fixture()
def redis_connect(app):
    redis_connection = RedisConnection().connection(db=app.config['CACHE_REDIS_DB'], kv = True)
    return redis_connection

@pytest.fixture()
def account_redis(app):
    redis_connection = RedisConnection().connection(db=app.config['ACCOUNTS_SESSION_REDIS_DB_NO'], kv = True)
    return redis_connection


def record_indexer_receiver(sender, json=None, record=None, index=None,
                            **kwargs):
    """Mock-receiver of a before_record_index signal."""
    if ES_VERSION[0] == 2:
        suggest_byyear = {}
        suggest_byyear['context'] = {
            'year': json['year']
        }
        suggest_byyear['input'] = [json['title'], ]
        suggest_byyear['output'] = json['title']
        suggest_byyear['payload'] = copy.deepcopy(json)

        suggest_title = {}
        suggest_title['input'] = [json['title'], ]
        suggest_title['output'] = json['title']
        suggest_title['payload'] = copy.deepcopy(json)

        json['suggest_byyear'] = suggest_byyear
        json['suggest_title'] = suggest_title

    elif ES_VERSION[0] >= 5:
        suggest_byyear = {}
        suggest_byyear['contexts'] = {
            'year': [str(json['year'])]
        }
        suggest_byyear['input'] = [json['title'], ]

        suggest_title = {}
        suggest_title['input'] = [json['title'], ]
        json['suggest_byyear'] = suggest_byyear
        json['suggest_title'] = suggest_title

    return json


@pytest.yield_fixture()
def indexer(app, es):
    """Create a record indexer."""
    InvenioIndexer(app)
    before_record_index.connect(record_indexer_receiver, sender=app)
    yield RecordIndexer()


@pytest.yield_fixture(scope='session')
def test_data():
    """Load test records."""
    path = 'data/testrecords.json'
    with open(join(dirname(__file__), path)) as fp:
        records = json.load(fp)
    yield records


@pytest.yield_fixture()
def test_records(db, test_data):
    """Load test records."""
    result = []
    for r in test_data:
        result.append(create_record(r))
    db.session.commit()
    yield result


@pytest.yield_fixture()
def indexed_records(app, esindex, test_records):
    """Get a function to wait for records to be flushed to index."""
    InvenioIndexer(app)
    before_record_index.connect(record_indexer_receiver, sender=app)
    indexer=RecordIndexer()
    for pid, record in test_records:
        indexer.index_by_id(record.id)
    current_search.flush_and_refresh(index='test-weko')
    yield test_records


def record_data_with_itemtype(id, index_path):
    dep_id = uuid.uuid4()
    record_data = {
        "path":[index_path],
        "owner":"1",
        "recid":str(id),
        "title":["test_item{}".format(id)],
        "pubdate":{"attribute_name":"PubDate","attribute_value":"2023-10-25"},
        "_buckets":{"deposit":str(dep_id)},
        "_deposit":{"id":str(id),"pid":{"type":"depid","value":str(id),"revision_id":0},"owners":[1],"status":"published","created_by":1},
        "item_title":"test_item{}".format(id),
        "author_link":[],
        "item_type_id":"15",
        "publish_date":"2023-10-25",
        "publish_status":"0",
        "weko_shared_id":-1,
        "item_1617186331708":{"attribute_name":"Title","attribute_value_mlt":[{"subitem_1551255647225":"test_item{}".format(id),"subitem_1551255648112":"ja"}]},
        "item_1617258105262":{"attribute_name":"Resource Type","attribute_value_mlt":[{"resourceuri":"http://purl.org/coar/resource_type/c_5794","resourcetype":"conference paper"}]},
        "relation_version_is_last":True
    }
    return record_data

@pytest.fixture()
def record_data10(indexes):
    index_path = indexes.id
    result = list()
    for i in range(1,11):
        result.append(record_data_with_itemtype(i, index_path))
    return result

def register_record(id, indexer, index_path):
    record_data = record_data_with_itemtype(id, index_path)
    pid, record = create_record(record_data)
    index, doc_type = indexer.record_to_index(record)
    es_data = {
        "title":record_data["title"],
        "control_number": str(id),
        "item_type":"test_item_type15",
        "publish_status":"0",
        "_created": pytz.utc.localize(record.created).isoformat() ,
        "_updated": pytz.utc.localize(record.updated).isoformat() ,
        "_item_metadata":record_data
    }
    indexer.client.index(
        id=str(record.id),
        version=record.revision_id,
        version_type=indexer._version_type,
        index=index,
        doc_type=doc_type,
        body=es_data
    )
    return pid, record

@pytest.fixture()
def indexed_10records(app, db, esindex, item_type, indexes):
    index_path = indexes.id
    result = []
    InvenioIndexer(app)
    indexer = RecordIndexer()
    for i in range(1,11):
        pid, record = register_record(i, indexer, index_path)
        result.append((pid, record))
    db.session.commit()
    current_search.flush_and_refresh(index="test-weko")
    return result

@pytest.fixture()
def indexed_100records(app, db, esindex, item_type,indexes):
    index_path = indexes.id
    result = []
    InvenioIndexer(app)
    indexer=RecordIndexer()
    for i in range(1,101):
        pid, record = register_record(i, indexer, index_path)
        result.append((pid,record))
    db.session.commit()
    current_search.flush_and_refresh(index='test-weko')
    
    return result


@pytest.yield_fixture(scope='session')
def test_patch():
    """A JSON patch."""
    yield [{'op': 'replace', 'path': '/year', 'value': 1985}]


@pytest.yield_fixture
def default_permissions(app):
    """Test default deny all permission."""
    for key in ['RECORDS_REST_DEFAULT_CREATE_PERMISSION_FACTORY',
                'RECORDS_REST_DEFAULT_UPDATE_PERMISSION_FACTORY',
                'RECORDS_REST_DEFAULT_DELETE_PERMISSION_FACTORY',
                'RECORDS_REST_DEFAULT_READ_PERMISSION_FACTORY']:
        app.config[key] = getattr(config, key)

    lm = LoginManager(app)

    # Allow easy login for tests purposes :-)
    class User(UserMixin):
        def __init__(self, id):
            self.id = id

    @lm.request_loader
    def load_user(request):
        uid = request.args.get('user', type=int)
        if uid:
            return User(uid)
        return None

    yield app

    app.extensions['invenio-records-rest'].reset_permission_factories()

@pytest.fixture()
def search_user(app, db):
    ds = app.extensions["invenio-accounts"].datastore
    user_email = "test@test.org"
    test_user = create_test_user(email=user_email)
    test_role = ds.create_role(name="Test Role")
    ds.add_role_to_user(test_user, test_role)
    search_role = ActionRoles(action="search-access", role=test_role)
    db.session.add(search_role)
    db.session.commit()
    return {"obj":test_user, "email":user_email}

@pytest.fixture()
def mock_es_execute():
    def _dummy_response(data):
        if isinstance(data, str):
            with open(data, "r") as f:
                data = json.load(f)
        dummy=response.Response(Search(), data)
        return dummy
    return _dummy_response

@pytest.fixture()
def item_type_mapping(db):
    path = "data/itemtypemapping.json"

    with open(join(dirname(__file__), path), "r") as f:
        data = json.load(f)
    with db.session.begin_nested():
        item=ItemTypeMapping(**data)
        db.session.add(item)

@pytest.fixture()
def item_type(db):
    item_type_name=ItemTypeName(id=15,name="test_item_type15")
    with open("tests/item_type/15_form.json", "r") as f:
        form = json.load(f)
        
    with open("tests/item_type/15_schema.json", "r") as f:
        schema = json.load(f)
    
    with open("tests/item_type/15_render.json", "r") as f:
        render = json.load(f)
    
    item_type = ItemType(
        id=15,
        name_id=15,
        harvesting_type=True,
        schema=schema,
        form=form,
        render=render,
        tag=1,
        version_id=1,
        is_deleted=False,
    )
    
    with open("tests/item_type/15_mapping.json", "r") as f:
        mapping = json.load(f)
    
    item_type_mapping = ItemTypeMapping(id=15, item_type_id=15, mapping=mapping)
    
    with db.session.begin_nested():
        db.session.add(item_type_name)
        db.session.add(item_type)
        db.session.add(item_type_mapping)
    
    return item_type, item_type_mapping

@pytest.fixture()
def admin_settings(db):
    setting_data = {
        "items_display_settings":{"items_display_email":True,"items_search_author":"name"},
    }
    setting_list=[]
    for field, data in setting_data.items():
        setting_list.append(
            AdminSettings(name=field,settings=data)
        )
    db.session.add_all(setting_list)
    db.session.commit()


@pytest.fixture()
def facet_search(db):
    control_number = FacetSearchSetting(
        name_en="control_number",
        name_jp="control_number",
        mapping="control_number",
        aggregations=[],
        active=True,
        ui_type="SelectBox",
        display_number=1,
        is_open=True
    )
    db.session.add(control_number)
    db.session.commit()
    
@pytest.yield_fixture()
def aggs_and_facet(redis_connect, facet_search):
    test_redis_key = "test_facet_search_query_has_permission"
    redis_connect.delete(test_redis_key)
    with patch("weko_admin.utils.get_query_key_by_permission", return_value=test_redis_key):
        yield
    redis_connect.delete(test_redis_key)

@pytest.fixture()
def indexes(app, db):
    index1 = Index(
        parent=0,
        position=1,
        index_name_english="test_index1",
        index_link_name_english="test_index_link1",
        harvest_public_state=True,
        public_state=True,
        browsing_role="3,-99"
    )
    db.session.add(index1)
    db.session.commit()
    return index1