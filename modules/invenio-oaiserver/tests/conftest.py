# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration."""

from __future__ import absolute_import, print_function

import os
import shutil
import tempfile
import pytest
import json

from elasticsearch import Elasticsearch
from flask import Flask
from flask_celeryext import FlaskCeleryExt
from flask_babelex import Babel
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database
from elasticsearch_dsl import response, Search
from invenio_db import InvenioDB, db
from invenio_indexer import InvenioIndexer
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_marc21 import InvenioMARC21
from invenio_pidstore import InvenioPIDStore
from invenio_records import InvenioRecords
from invenio_search import InvenioSearch, RecordsSearch
from weko_records.api import ItemTypes
from weko_records.models import ItemTypeName
from weko_records_ui.config import WEKO_RECORDS_UI_LICENSE_DICT

from invenio_oaiserver import InvenioOAIServer
from invenio_oaiserver.views.server import blueprint
from invenio_oaiserver.provider import OAIIDProvider
from .helpers import load_records, remove_records, create_record_oai


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


@pytest.yield_fixture(scope='session')
def search_class():
    """Search class."""
    yield TestSearch

class MockEs():
    def __init__(self,**keywargs):
        self.indices = self.MockIndices()
        self.es = Elasticsearch()
        self.cluster = self.MockCluster()
    def index(self, id="", version="", version_type="", index="", doc_type="", body="", **arguments):
        pass
    def delete(self, id="", index="", doc_type="", **kwargs):
        return response.Response(response=json.dumps({}),status=500)
    def clear_scroll(self, scroll_id):
        pass
    def search(self, index="", body="",**kwargs):
        pass

    @property
    def transport(self):
        return self.es.transport
    class MockIndices():
        def __init__(self, **keywargs):
            self.mapping = dict()
        def delete(self, index="", ignore=""):
            pass
        def delete_template(self, index=""):
            pass
        def create(self, index="", body={}, ignore=""):
            self.mapping[index] = body
        def put_alias(self, index="", name="", ignore=""):
            pass
        def put_template(self, name="", body={}, ignore=""):
            pass
        def refresh(self, index=""):
            pass
        def exists(self, index="", **kwargs):
            if index in self.mapping:
                return True
            else:
                return False
        def flush(self, index="", wait_if_ongoing=""):
            pass
        def delete_alias(self, index="", name="", ignore=""):
            pass
        def put_mapping(self, index="", doc_type="", body="", ignore=""):
            pass
        # def search(self,index="",doc_type="",body={},**kwargs):
        #     pass


    class MockCluster():
        def __init__(self,**kwargs):
            pass
        def health(self, wait_for_status="", request_timeout=0):
            pass


@pytest.yield_fixture
def app(search_class):
    """Flask application fixture."""
    instance_path = tempfile.mkdtemp()
    app = Flask('testapp', instance_path=instance_path)
    app.config.update(
        CELERY_ALWAYS_EAGER=True,
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_CACHE_BACKEND='memory',
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_TASK_EAGER_PROPAGATES=True,
        CELERY_RESULT_BACKEND='cache',
        JSONSCHEMAS_HOST='inveniosoftware.org',
        TESTING=True,
        SECRET_KEY='CHANGE_ME',
        SQLALCHEMY_DATABASE_URI=os.environ.get('SQLALCHEMY_DATABASE_URI',
                                               'sqlite:///test.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        SERVER_NAME='app',
        OAISERVER_ID_PREFIX='oai:inveniosoftware.org:recid/',
        OAISERVER_RECORD_INDEX='_all',
        OAISERVER_REGISTER_SET_SIGNALS=True,
        OAISERVER_METADATA_FORMATS = {
            'jpcoar_1.0': {
            'serializer': (
                'weko_schema_ui.utils:dumps_oai_etree', {
                    'schema_type': 'jpcoar_v1',
                }
            ),
            'namespace': 'https://irdb.nii.ac.jp/schema/jpcoar/1.0/',
            'schema': 'https://irdb.nii.ac.jp/schema/jpcoar/1.0/jpcoar_scm.xsd',
            }
        },
        WEKO_RECORDS_UI_LICENSE_DICT=WEKO_RECORDS_UI_LICENSE_DICT
    )
    if not hasattr(app, 'cli'):
        from flask_cli import FlaskCLI
        FlaskCLI(app)
    InvenioDB(app)
    Babel(app)
    FlaskCeleryExt(app)
    InvenioJSONSchemas(app)
    InvenioRecords(app)
    InvenioPIDStore(app)
    InvenioMARC21(app)
    #client = Elasticsearch(hosts=[os.environ.get('ES_HOST', 'localhost')])
    # search = InvenioSearch(app, client=client)

    search = InvenioSearch(app, client=MockEs())
    search.register_mappings('records', 'tests.data')
    InvenioIndexer(app)
    InvenioOAIServer(app)

    app.register_blueprint(blueprint)

    with app.app_context():
        if str(db.engine.url) != 'sqlite://' and \
           not database_exists(str(db.engine.url)):
            create_database(str(db.engine.url))
        db.create_all()
        list(search.create(ignore=[400]))
        search.flush_and_refresh('_all')

    with app.app_context():
        yield app

    with app.app_context():
        db.session.close()
        if str(db.engine.url) != 'sqlite://':
            drop_database(str(db.engine.url))
        list(search.delete(ignore=[404]))
        search.client.indices.delete("*-percolators")
    shutil.rmtree(instance_path)


def mock_record_validate(self):
    """Mock validation."""
    pass


@pytest.yield_fixture
def authority_data(app):
    """Test indexation using authority data."""
    schema = 'http://localhost:5000/marc21/authority/ad-v1.0.0.json'
    with app.test_request_context():
        records = load_records(app=app, filename='data/marc21/authority.xml',
                               schema=schema)
    yield records
    with app.test_request_context():
        remove_records(app, records)


@pytest.yield_fixture
def bibliographic_data(app):
    """Test indexation using bibliographic data."""
    schema = 'http://localhost:5000/marc21/bibliographic/bd-v1.0.0.json'
    with app.test_request_context():
        records = load_records(app=app,
                               filename='data/marc21/bibliographic.xml',
                               schema=schema)
    yield records
    with app.test_request_context():
        remove_records(app, records)


@pytest.yield_fixture
def without_oaiset_signals(app):
    """Temporary disable oaiset signals."""
    from invenio_oaiserver import current_oaiserver
    current_oaiserver.unregister_signals_oaiset()
    yield
    current_oaiserver.register_signals_oaiset()


@pytest.fixture
def schema():
    """Get record schema."""
    return {
        'allOf': [{
            'type': 'object',
            'properties': {
                'title_statement': {
                    'type': 'object',
                    'properties': {
                        'title': {'type': 'string'}
                    }
                },
                'genre': {'type': 'string'},
            },
        }, {
            '$ref': 'http://inveniosoftware.org/schemas/'
                    'oaiserver/internal-v1.1.0.json',
        }]
    }


@pytest.fixture()
def mock_execute():
    def factory(data):
        dummy = response.Response(Search(), data)
        return dummy
    return factory

@pytest.fixture()
def item_type(app):
    _item_type_name=ItemTypeName(name="test")
    _render={
        "meta_fix":{},
        "meta_list":{}
    }
    return ItemTypes.create(
        name='test',
        item_type_name=_item_type_name,
        schema={},
        render=_render,
        form={},
        tag=1
    )
@pytest.fixture()
def records(app):
    returns = list()
    record_data=[
        {
            "path":["1557819692844"],
            "publish_date":"2100-01-01",
            "publish_status":0,
            "json":{
                "_source":{
                    "_item_metadata":{
                        "system_identifier_doi":{
                            "attribute_value_mlt":[
                                {
                                    "subitem_systemidt_identifier_type":"DOI"
                                }
                            ]
                        }
                    }
                }
            },
        },
        {
          "publish_date":"2000-08-09",
          "publish_status":0,
          "json":{
              "_source":{
                  "_item_metadata":{
                      "system_identifier_doi":{
                          "attribute_value_mlt":[
                              {"subitem_systemidt_identifier_type":"test doi"}
                          ]
                      }
                    }
                }
            }
        },
        {
            "path":["1557819692844"],
            "publish_date":"2000-08-09",
            "publish_status":0,
            "json":{
              "_source":{
                  "_item_metadata":{
                      "system_identifier_doi":{
                          "attribute_value_mlt":[
                              {"subitem_systemidt_identifier_type":"test doi"}
                          ]
                      }
                    }
                  }
              },
            "_oai":{"sets":[]},
            "system_identifier_doi":"DOI",
            "item_type_id":"1"
        },
        {
            "path":["1557819692844"],
            "publish_date":"2000-08-09",
            "publish_status":0,
            "json":{
              "_source":{
                  "_item_metadata":{}
                  }
              },
            "_oai":{"sets":[]},
            "item_type_id":"1"
        }
    ]
    item_data = [
        {"title":"listrecords if1"},
        {"title":"listrecords if2"},
        {"title":"listrecords if3"},
        {"title":"listrecords if3_2"}
    ]
    for i in range(len(record_data)):
        returns.append(create_record_oai(record_data[i],item_data[i]))
    db.session.commit()
    yield returns
