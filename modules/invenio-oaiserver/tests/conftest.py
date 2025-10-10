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
from os.path import join, dirname
from mock import patch

from elasticsearch import Elasticsearch
from flask import Flask
from flask_celeryext import FlaskCeleryExt
from flask_babelex import Babel
from sqlalchemy_utils.functions import create_database, database_exists
from elasticsearch_dsl import response, Search

from invenio_access import InvenioAccess
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import User, Role
from invenio_accounts.testutils import create_test_user
from invenio_access.models import ActionUsers,ActionRoles
from invenio_communities.config import COMMUNITIES_OAI_FORMAT
from invenio_communities.models import Community
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_indexer import InvenioIndexer
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_marc21 import InvenioMARC21
from invenio_pidstore import InvenioPIDStore
from invenio_records import InvenioRecords
from invenio_search import InvenioSearch
from weko_records.api import ItemTypes
from weko_records.models import ItemTypeName
from weko_records_ui.config import WEKO_RECORDS_UI_LICENSE_DICT
from weko_index_tree.models import Index

from invenio_oaiserver import InvenioOAIServer
from invenio_oaiserver.models import Identify, OAISet
from invenio_oaiserver.views.server import blueprint
from invenio_oaiserver.provider import OAIIDProvider
from .helpers import load_records, remove_records, create_record_oai

@pytest.yield_fixture()
def instance_path():
    """Temporary instance path."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)

@pytest.fixture()
def base_app(instance_path):
    app_ = Flask(
        "testapp",
        instance_path=instance_path,
        static_folder=join(instance_path, "static"),
    )
    app_.config.update(
        CELERY_ALWAYS_EAGER=True,
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_CACHE_BACKEND='memory',
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_TASK_EAGER_PROPAGATES=True,
        CELERY_RESULT_BACKEND='cache',
        JSONSCHEMAS_HOST='inveniosoftware.org',
        TESTING=True,
        SECRET_KEY='CHANGE_ME',
        # SQLALCHEMY_DATABASE_URI=os.environ.get('SQLALCHEMY_DATABASE_URI',
        #                                         'sqlite:///test.db'),
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                         'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
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
        WEKO_RECORDS_UI_LICENSE_DICT=WEKO_RECORDS_UI_LICENSE_DICT,
        INDEXER_DEFAULT_DOCTYPE='item-v1.0.0',
        INDEXER_FILE_DOC_TYPE='content',
        INDEXER_DEFAULT_INDEX="{}-weko-item-v1.0.0".format("test"),
        SEARCH_UI_SEARCH_INDEX="{}-weko".format("test"),
        SEARCH_ELASTIC_HOSTS="elasticsearch",
        SEARCH_INDEX_PREFIX="test-",
        COMMUNITIES_OAI_FORMAT=COMMUNITIES_OAI_FORMAT,
    )
    if not hasattr(app_, 'cli'):
        from flask_cli import FlaskCLI
        FlaskCLI(app_)
    InvenioDB(app_)
    Babel(app_)
    FlaskCeleryExt(app_)
    InvenioAccess(app_)
    InvenioAccounts(app_)
    InvenioJSONSchemas(app_)
    InvenioRecords(app_)
    InvenioPIDStore(app_)
    InvenioMARC21(app_)
    InvenioIndexer(app_)
    InvenioOAIServer(app_)

    app_.register_blueprint(blueprint)

    return app_

@pytest.yield_fixture()
def app(base_app):
    with base_app.app_context():
        yield base_app

@pytest.yield_fixture()
def client(app):
    with app.test_client() as client:
        yield client

@pytest.yield_fixture()
def db(app):
    """Database fixture."""
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()

@pytest.fixture()
def users(app, db):
    """Create users."""
    ds = app.extensions['invenio-accounts'].datastore
    user_count = User.query.filter_by(email='user@test.org').count()
    if user_count != 1:
        user = create_test_user(email='user@test.org')
        contributor = create_test_user(email='contributor@test.org')
        comadmin = create_test_user(email='comadmin@test.org')
        repoadmin = create_test_user(email='repoadmin@test.org')
        sysadmin = create_test_user(email='sysadmin@test.org')
        generaluser = create_test_user(email='generaluser@test.org')
        originalroleuser = create_test_user(email='originalroleuser@test.org')
        originalroleuser2 = create_test_user(email='originalroleuser2@test.org')
        student = create_test_user(email='student@test.org')
    else:
        user = User.query.filter_by(email='user@test.org').first()
        contributor = User.query.filter_by(email='contributor@test.org').first()
        comadmin = User.query.filter_by(email='comadmin@test.org').first()
        repoadmin = User.query.filter_by(email='repoadmin@test.org').first()
        sysadmin = User.query.filter_by(email='sysadmin@test.org').first()
        generaluser = User.query.filter_by(email='generaluser@test.org')
        originalroleuser = create_test_user(email='originalroleuser@test.org')
        originalroleuser2 = create_test_user(email='originalroleuser2@test.org')
        student = User.query.filter_by(email='student@test.org').first()

    role_count = Role.query.filter_by(name='System Administrator').count()
    if role_count != 1:
        sysadmin_role = ds.create_role(name='System Administrator')
        repoadmin_role = ds.create_role(name='Repository Administrator')
        contributor_role = ds.create_role(name='Contributor')
        comadmin_role = ds.create_role(name='Community Administrator')
        general_role = ds.create_role(name='General')
        originalrole = ds.create_role(name='Original Role')
        studentrole = ds.create_role(name='Student')
    else:
        sysadmin_role = Role.query.filter_by(name='System Administrator').first()
        repoadmin_role = Role.query.filter_by(name='Repository Administrator').first()
        contributor_role = Role.query.filter_by(name='Contributor').first()
        comadmin_role = Role.query.filter_by(name='Community Administrator').first()
        general_role = Role.query.filter_by(name='General').first()
        originalrole = Role.query.filter_by(name='Original Role').first()
        studentrole = Role.query.filter_by(name='Student').first()

    ds.add_role_to_user(sysadmin, sysadmin_role)
    ds.add_role_to_user(repoadmin, repoadmin_role)
    ds.add_role_to_user(contributor, contributor_role)
    ds.add_role_to_user(comadmin, comadmin_role)
    ds.add_role_to_user(generaluser, general_role)
    ds.add_role_to_user(originalroleuser, originalrole)
    ds.add_role_to_user(originalroleuser2, originalrole)
    ds.add_role_to_user(originalroleuser2, repoadmin_role)
    ds.add_role_to_user(student,studentrole)

    # Assign access authorization
    with db.session.begin_nested():
        action_users = [
            ActionUsers(action='superuser-access', user=sysadmin),
        ]
        db.session.add_all(action_users)
        action_roles = [
            ActionRoles(action='superuser-access', role=sysadmin_role),
            ActionRoles(action='admin-access', role=repoadmin_role),
            ActionRoles(action='schema-access', role=repoadmin_role),
            ActionRoles(action='index-tree-access', role=repoadmin_role),
            ActionRoles(action='indextree-journal-access', role=repoadmin_role),
            ActionRoles(action='item-type-access', role=repoadmin_role),
            ActionRoles(action='item-access', role=repoadmin_role),
            ActionRoles(action='files-rest-bucket-update', role=repoadmin_role),
            ActionRoles(action='files-rest-object-delete', role=repoadmin_role),
            ActionRoles(action='files-rest-object-delete-version', role=repoadmin_role),
            ActionRoles(action='files-rest-object-read', role=repoadmin_role),
            ActionRoles(action='search-access', role=repoadmin_role),
            ActionRoles(action='detail-page-acces', role=repoadmin_role),
            ActionRoles(action='download-original-pdf-access', role=repoadmin_role),
            ActionRoles(action='author-access', role=repoadmin_role),
            ActionRoles(action='items-autofill', role=repoadmin_role),
            ActionRoles(action='stats-api-access', role=repoadmin_role),
            ActionRoles(action='read-style-action', role=repoadmin_role),
            ActionRoles(action='update-style-action', role=repoadmin_role),
            ActionRoles(action='detail-page-acces', role=repoadmin_role),

            ActionRoles(action='admin-access', role=comadmin_role),
            ActionRoles(action='index-tree-access', role=comadmin_role),
            ActionRoles(action='indextree-journal-access', role=comadmin_role),
            ActionRoles(action='item-access', role=comadmin_role),
            ActionRoles(action='files-rest-bucket-update', role=comadmin_role),
            ActionRoles(action='files-rest-object-delete', role=comadmin_role),
            ActionRoles(action='files-rest-object-delete-version', role=comadmin_role),
            ActionRoles(action='files-rest-object-read', role=comadmin_role),
            ActionRoles(action='search-access', role=comadmin_role),
            ActionRoles(action='detail-page-acces', role=comadmin_role),
            ActionRoles(action='download-original-pdf-access', role=comadmin_role),
            ActionRoles(action='author-access', role=comadmin_role),
            ActionRoles(action='items-autofill', role=comadmin_role),
            ActionRoles(action='detail-page-acces', role=comadmin_role),
            ActionRoles(action='detail-page-acces', role=comadmin_role),

            ActionRoles(action='item-access', role=contributor_role),
            ActionRoles(action='files-rest-bucket-update', role=contributor_role),
            ActionRoles(action='files-rest-object-delete', role=contributor_role),
            ActionRoles(action='files-rest-object-delete-version', role=contributor_role),
            ActionRoles(action='files-rest-object-read', role=contributor_role),
            ActionRoles(action='search-access', role=contributor_role),
            ActionRoles(action='detail-page-acces', role=contributor_role),
            ActionRoles(action='download-original-pdf-access', role=contributor_role),
            ActionRoles(action='author-access', role=contributor_role),
            ActionRoles(action='items-autofill', role=contributor_role),
            ActionRoles(action='detail-page-acces', role=contributor_role),
            ActionRoles(action='detail-page-acces', role=contributor_role),
        ]
        db.session.add_all(action_roles)
    index = Index()
    db.session.add(index)
    db.session.commit()
    comm = Community.create(community_id="comm01", role_id=sysadmin_role.id,
                            id_user=sysadmin.id, title="test community",
                            description=("this is test community"),
                            root_node_id=index.id)
    db.session.commit()

    return [
        {'email': sysadmin.email, 'id': sysadmin.id, 'obj': sysadmin},
        {'email': repoadmin.email, 'id': repoadmin.id, 'obj': repoadmin},
        {'email': comadmin.email, 'id': comadmin.id, 'obj': comadmin},
        {'email': contributor.email, 'id': contributor.id, 'obj': contributor},
        {'email': generaluser.email, 'id': generaluser.id, 'obj': generaluser},
        {'email': originalroleuser.email, 'id': originalroleuser.id, 'obj': originalroleuser},
        {'email': originalroleuser2.email, 'id': originalroleuser2.id, 'obj': originalroleuser2},
        {'email': user.email, 'id': user.id, 'obj': user},
        {'email': student.email,'id': student.id, 'obj': student}
    ]

@pytest.yield_fixture()
def es_app(app):
    with open(join(dirname(__file__),"data/mappings/item-v1.0.0.json"),"r") as f:
    #with open(join(dirname(__file__),"data/v6/records/record-v1.0.0.json"),"r") as f:
        mapping = json.load(f)
    es = Elasticsearch("http://{}:9200".format(app.config["SEARCH_ELASTIC_HOSTS"]))

    es.indices.create(
        index=app.config["INDEXER_DEFAULT_INDEX"],
        body=mapping, ignore=[400, 404]
    )

    es.indices.put_alias(
        index=app.config["INDEXER_DEFAULT_INDEX"],
        name=app.config["SEARCH_UI_SEARCH_INDEX"],
        ignore=[400, 404],
    )
    search = InvenioSearch(app, client=es)
    #search.register_mappings('items', 'tests.data')
    yield app

    es.indices.delete_alias(
        index=app.config["INDEXER_DEFAULT_INDEX"],
        name=app.config["SEARCH_UI_SEARCH_INDEX"],
        ignore=[400, 404],
    )
    es.indices.delete(
        index=app.config["INDEXER_DEFAULT_INDEX"],
        ignore=[400, 404])

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
def item_type(app, db):
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
def records(app, db):
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
            "_oai":{"sets":[]},
            "item_type_id":"1"
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
            },
            "_oai":{"sets":[]},
            "item_type_id":"1"
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
        },
        {
            "path":["1557819692844"],
            "publish_date":"2000-08-09",
            "publish_status": 2,
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
            "publish_status": -1,
            "json":{
              "_source":{
                  "_item_metadata":{}
                  }
              },
            "_oai":{"sets":[]},
            "item_type_id":"1"
        },
        {
            "path":["1557819692844"],
            "publish_date":"2000-08-09",
            "publish_status": 1,
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
        {"title":"listrecords if3_2"},
        {"title":"publis_status_2"},
        {"title":"publis_status_-1"},
        {"title":"publis_status_1"},
    ]
    for i in range(len(record_data)):
        returns.append(create_record_oai(record_data[i], item_data[i]))
    db.session.commit()
    yield returns


@pytest.fixture()
def identify(app, db):
    iden = Identify(
            id=1,
            outPutSetting=True,
            emails="test@test.org",
            repositoryName="test_repository"
        )
    db.session.add(iden)
    db.session.commit()

    return [iden]

@pytest.fixture()
def oaiset(app, db,without_oaiset_signals):
    oai = OAISet(id=1,
        spec='test',
        name='test_name',
        description='some test description',
        search_pattern='test search')

    db.session.add(oai)
    db.session.commit()
    return [oai]

@pytest.fixture()
def indexes(app,db):
    index1 = Index(
        parent=0,
        position=1,
        index_name_english="test_index1",
        index_link_name_english="test_index_link1",
        harvest_public_state=True,
        public_state=True,
        browsing_role="3,-99"
    )
    index1 = Index(
        parent=0,
        position=1,
        index_name_english="test_index1",
        index_link_name_english="test_index_link1",
        harvest_public_state=True,
        public_state=True,
        browsing_role="3,-99"
    )
