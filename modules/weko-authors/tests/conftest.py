# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 National Institute of Informatics.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration."""
import os,sys
import shutil
import tempfile
import json
import uuid
from os.path import dirname, join
from datetime import datetime
from elasticsearch import Elasticsearch
from sqlalchemy import inspect

import pytest
from flask import Flask, url_for, Response
from flask_babelex import Babel
from sqlalchemy_utils.functions import create_database, database_exists

from invenio_access import InvenioAccess
from invenio_access.models import ActionUsers,ActionRoles
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import User, Role
from invenio_accounts.testutils import create_test_user, login_user_via_session

from invenio_admin import InvenioAdmin
from invenio_assets import InvenioAssets
from invenio_cache import InvenioCache
from invenio_communities.models import Community
# from invenio_db import InvenioDB, db as db_
from invenio_db import InvenioDB
from invenio_oauth2server import InvenioOAuth2Server, InvenioOAuth2ServerREST
from invenio_db import db as db_
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.models import Location, FileInstance
from invenio_indexer import InvenioIndexer
from invenio_search import InvenioSearch,RecordsSearch
from weko_authors.config import WEKO_AUTHORS_REST_ENDPOINTS
from weko_search_ui import WekoSearchUI
from weko_index_tree.models import Index
from flask_limiter import Limiter
from flask_menu import Menu
from weko_authors.views import blueprint_api
from weko_authors.rest import create_blueprint
from weko_authors import WekoAuthors
from weko_authors.models import Authors, AuthorsPrefixSettings, AuthorsAffiliationSettings
from weko_accounts import WekoAccounts
from weko_theme import WekoTheme
import weko_authors.mappings.v2


sys.path.append(os.path.dirname(__file__))

class TestSearch(RecordsSearch):
    """Test record search."""

    class Meta:
        """Test configuration."""

        index = 'records'
        doc_types = None

    def __init__(self, **kwargs):
        """Add extra options."""
        super(TestSearch, self).__init__(**kwargs)
        self._extra.update(**{'_source': {'excludes': ['_access']}})


@pytest.yield_fixture(scope='session')
def search_class():
    """Search class."""
    yield TestSearch


@pytest.yield_fixture()
def instance_path():
    """Temporary instance path."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


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


@pytest.fixture()
def base_app(request, instance_path,search_class):
    """Flask application fixture."""
    app_ = Flask('testapp', instance_path=instance_path)
    app_.config.update(
        SECRET_KEY='SECRET_KEY',
        TESTING=True,
        SERVER_NAME='app',
        SQLALCHEMY_DATABASE_URI=os.environ.get(
           'SQLALCHEMY_DATABASE_URI',
           'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        INDEX_IMG='indextree/36466818-image.jpg',
        SEARCH_UI_SEARCH_INDEX='test-weko',
        WEKO_AUTHORS_ES_INDEX_NAME='test-authors',
        WEKO_AUTHORS_AFFILIATION_IDENTIFIER_ITEM_OTHER=4,
        WEKO_AUTHORS_LIST_SCHEME_AFFILIATION=[
            'ISNI', 'GRID', 'Ringgold', 'kakenhi', 'Other'],
        WEKO_API_LIMIT_RATE_DEFAULT=["100 per minute"],
        CELERY_ALWAYS_EAGER=True,
        CELERY_CACHE_BACKEND="memory",
        WEKO_AUTHORS_IMPORT_CACHE_RESULT_OVER_MAX_FILE_PATH_KEY = "authors_import_result_file_of_over_path",
        WEKO_AUTHORS_EXPORT_TEMP_FOLDER_PATH =   "/var/tmp/authors_export",
        WEKO_AUTHORS_IMPORT_CACHE_USER_TSV_FILE_KEY = 'authors_import_user_file_key',
        WEKO_AUTHORS_IMPORT_TEMP_FOLDER_PATH = "var/tmp/authors_import",
        WEKO_AUTHORS_FILE_MAPPING_FOR_PREFIX =["scheme", "name", "url", "is_deleted"],
        WEKO_AUTHORS_IMPORT_TMP_PREFIX = 'authors_import_',
        WEKO_AUTHORS_IMPORT_BATCH_SIZE = 100,
        WEKO_AUTHORS_IMPORT_MAX_NUM_OF_DISPLAYS = 1000,
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_RESULT_BACKEND="cache",
        CACHE_REDIS_URL=os.environ.get("CACHE_REDIS_URL", "redis://redis:6379/0"),
        CACHE_REDIS_DB='0',
        CACHE_REDIS_HOST="redis",
        SEARCH_ELASTIC_HOSTS=os.environ.get("INVENIO_ELASTICSEARCH_HOST"),
        SEARCH_INDEX_PREFIX="{}-".format('test'),
        SEARCH_CLIENT_CONFIG=dict(timeout=120, max_retries=10),
        WEKO_AUTHORS_EXPORT_TARGET_CACHE_KEY="weko_authors_export_target",
        WEKO_AUTHORS_EXPORT_CACHE_STOP_POINT_KEY="weko_authors_export_stop_point",
        WEKO_AUTHORS_EXPORT_CACHE_TEMP_FILE_PATH_KEY="weko_authors_export_temp_file_path_key",
        WEKO_AUTHORS_IMPORT_CACHE_BAND_CHECK_USER_FILE_PATH_KEY = "authors_import_band_check_user_file_path",
        WEKO_AUTHORS_IMPORT_CACHE_RESULT_FILE_PATH_KEY = "authors_import_result_file_path",
        WEKO_AUTHORS_IMPORT_CACHE_RESULT_SUMMARY_KEY= "result_summary_key",
        WEKO_AUTHORS_IMPORT_CACHE_OVER_MAX_TASK_KEY = "authors_import_over_max_task",
    )
    Babel(app_)
    Menu(app_)
    InvenioDB(app_)
    InvenioCache(app_)
    InvenioAccounts(app_)
    InvenioAccess(app_)
    InvenioAdmin(app_)
    InvenioAssets(app_)
    InvenioIndexer(app_)
    InvenioFilesREST(app_)
    if hasattr(request, 'param'):
        if 'is_es' in request.param:
            search = InvenioSearch(app_)
    else:
        search = InvenioSearch(app_, client=MockEs())
        search.register_mappings(search_class.Meta.index, 'mock_module.mapping')
    WekoTheme(app_)
    WekoAuthors(app_)
    WekoSearchUI(app_)
    WekoAccounts(app_)
    InvenioOAuth2Server(app_)
    InvenioOAuth2ServerREST(app_)


    # app_.register_blueprint(blueprint)
    app_.register_blueprint(blueprint_api, url_prefix='/api/authors')
    return app_


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app


@pytest.fixture()
def base_app2(instance_path,search_class):
    """Flask application fixture for ES."""
    app_ = Flask('testapp', instance_path=instance_path)
    WEKO_AUTHORS_FILE_MAPPING_FOR_AFFILIATION ={
        "json_id": "affiliationInfo",
        "child": [
            {
                "json_id": "identifierInfo",
                "child": [
                    {
                        "json_id": "affiliationIdType",
                        "label_en": "Affiliation Identifier Scheme",
                        "label_jp": "外部所属機関ID 識別子",
                        "validation": {
                            "validator": {
                                "class_name": "weko_authors.contrib.validation",
                                "func_name": "validate_affiliation_identifier_scheme"
                            },
                            "required": {
                                "if": [
                                    "affiliationId"
                                ]
                            }
                        }
                    },
                    {
                        "json_id": "affiliationId",
                        "label_en": "Affiliation Identifier",
                        "label_jp": "外部所属機関ID",
                        "validation": {
                            "required": {
                                "if": [
                                    "affiliationIdType"
                                ]
                            }
                        }
                    },
                    {
                        "json_id": "identifierShowFlg",
                        "label_en": "Affiliation Identifier Display",
                        "label_jp": "外部所属機関ID 表示／非表示",
                        "mask": {
                            "true": "Y",
                            "false": "N"
                        }
                    }
                ]
            },
            {
                "json_id": "affiliationNameInfo",
                "child": [
                    {
                        "json_id": "affiliationName",
                        "label_en": "Affiliation Name",
                        "label_jp": "外部所属機関名"
                    },
                    {
                        "json_id": "affiliationNameLang",
                        "label_en": "Language",
                        "label_jp": "言語",
                        "validation": {
                            "map": [
                                "ja",
                                "ja-Kana",
                                "en",
                                "fr",
                                "it",
                                "de",
                                "es",
                                "zh-cn",
                                "zh-tw",
                                "ru",
                                "la",
                                "ms",
                                "eo",
                                "ar",
                                "el",
                                "ko"
                            ]
                        }
                    },
                    {
                        "json_id": "affiliationNameShowFlg",
                        "label_en": "Affiliation Name Display",
                        "label_jp": "外部所属機関名・言語 表示／非表示",
                        "mask": {
                            "true": "Y",
                            "false": "N"
                        },
                        "validation": {
                            "map": [
                                "Y",
                                "N"
                            ]
                        }
                    }
                ]
            },
            {
                "json_id": "affiliationPeriodInfo",
                "child": [
                    {
                        "json_id": "periodStart",
                        "label_en": "Affiliation Period Start",
                        "label_jp": "外部所属機関 所属期間 開始日",
                        "validation": {
                            "validator": {
                                "class_name": "weko_authors.contrib.validation",
                                "func_name": "validate_affiliation_period_start"
                            }
                        }
                    },
                    {
                        "json_id": "periodEnd",
                        "label_en": "Affiliation Period End",
                        "label_jp": "外部所属機関 所属期間 終了日",
                        "validation": {
                            "validator": {
                                "class_name": "weko_authors.contrib.validation",
                                "func_name": "validate_affiliation_period_end"
                            }
                        }
                    }
                ]
            }
        ]
    }

    app_.config.update(
        SECRET_KEY='SECRET_KEY',
        TESTING=True,
        SERVER_NAME='app2',
        SQLALCHEMY_DATABASE_URI=os.environ.get(
           'SQLALCHEMY_DATABASE_URI',
           'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #    'SQLALCHEMY_DATABASE_URI',
        #    'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/invenio'),
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        INDEX_IMG='indextree/36466818-image.jpg',
        INDEXER_DEFAULT_INDEX="{}-authors-author-v1.0.0".format(
            'test'
        ),
        SEARCH_UI_SEARCH_INDEX='test-weko',
        WEKO_AUTHORS_ES_INDEX_NAME='test-authors',
        WEKO_AUTHORS_AFFILIATION_IDENTIFIER_ITEM_OTHER=4,
        WEKO_AUTHORS_LIST_SCHEME_AFFILIATION=[
            'ISNI', 'GRID', 'Ringgold', 'kakenhi', 'Other'],
        CELERY_ALWAYS_EAGER=True,
        CELERY_CACHE_BACKEND="memory",
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_RESULT_BACKEND="cache",
        CACHE_REDIS_URL='redis://redis:6379/0',
        CACHE_REDIS_DB='0',
        CACHE_REDIS_HOST="redis",
        SEARCH_ELASTIC_HOSTS=os.environ.get("SEARCH_ELASTIC_HOSTS", "elasticsearch"),
        WEKO_AUTHORS_EXPORT_BATCH_SIZE=2,
        WEKO_AUTHORS_FILE_MAPPING_FOR_AFFILIATION=WEKO_AUTHORS_FILE_MAPPING_FOR_AFFILIATION,
        WEKO_AUTHORS_BULK_EXPORT_MAX_RETRY=2,
        WEKO_AUTHORS_BULK_EXPORT_RETRY_INTERVAL=1,
        WEKO_AUTHORS_IMPORT_TEMP_FOLDER_PATH='/data',
        WEKO_AUTHORS_CACHE_TTL=100,
        WEKO_AUTHORS_IMPORT_BATCH_SIZE=2,
        WEKO_AUTHORS_IMPORT_MAX_RETRY=2,
        WEKO_AUTHORS_IMPORT_RETRY_INTERVAL=1,
        WEKO_AUTHORS_IMPORT_CACHE_RESULT_SUMMARY_KEY= "result_summary_key",
        WEKO_AUTHORS_BULK_IMPORT_RETRY_INTERVAL= 1,
        WEKO_AUTHORS_EXPORT_CACHE_URL_KEY= 'weko_authors_exported_url',
        WEKO_AUTHORS_EXPORT_CACHE_STOP_POINT_KEY= 'weko_authors_export_stop_point',
        WEKO_AUTHORS_IMPORT_CACHE_FORCE_CHANGE_MODE_KEY= 'authors_import_force_change',
    )
    Babel(app_)
    InvenioDB(app_)
    InvenioCache(app_)
    InvenioAccounts(app_)
    InvenioAccess(app_)
    InvenioAdmin(app_)
    InvenioAssets(app_)
    InvenioIndexer(app_)
    InvenioFilesREST(app_)

    search = InvenioSearch(app_)
    search.register_mappings(search_class.Meta.index, 'mock_module.mapping')
    WekoTheme(app_)
    WekoAuthors(app_)
    WekoSearchUI(app_)

    # app_.register_blueprint(blueprint)
    app_.register_blueprint(blueprint_api, url_prefix='/api/authors')
    return app_


@pytest.yield_fixture()
def app2(base_app2):
    """Flask application fixture."""
    with base_app2.app_context():
        yield base_app2


@pytest.yield_fixture()
def db(app):
    """Database fixture."""
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()
    # drop_database(str(db_.engine.url))


@pytest.yield_fixture()
def client(app):
    """Get test client."""
    with app.test_client() as client:
        yield client

from invenio_search import current_search_client
@pytest.fixture()
def esindex(app):
    current_search_client.indices.delete(index='test-*')
    with open("tests/mock_module/mapping/v6/authors/author-v1.0.0.json","r") as f:
        mapping = json.load(f)
    with app.test_request_context():
        current_search_client.indices.create("test-authors-author-v1.0.0",body=mapping)
        current_search_client.indices.put_alias(index="test-authors-author-v1.0.0", name=app.config["WEKO_AUTHORS_ES_INDEX_NAME"])

    yield current_search_client

    # with app.test_request_context():
    #     current_search_client.indices.delete_alias(index="test-authors-author-v1.0.0", name=app.config["WEKO_AUTHORS_ES_INDEX_NAME"])
    #     current_search_client.indices.delete(index="test-authors-author-v1.0.0", ignore=[400, 404])


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


@pytest.fixture()
def create_author(app, db, esindex):
    def _create_author(data, next_id):
        data["pk_id"] = str(next_id)
        es_data = json.loads(json.dumps(data))
        es_id = uuid.uuid4()
        data["id"] = str(es_id)
        with db.session.begin_nested():
            author = Authors(id=next_id, json=data)
            db.session.add(author)
        db.session.commit()
            
        current_search_client.index(
            index=app.config["WEKO_AUTHORS_ES_INDEX_NAME"],
            doc_type=app.config['WEKO_AUTHORS_ES_DOC_TYPE'],
            id=es_id,
            body=es_data,
            refresh='true')
        return es_id

    # Return new author's id
    return _create_author


def user():
    """Create a example user."""
    return create_test_user(email='test@test.org')


def object_as_dict(obj):
    """Make a dict from SQLAlchemy object."""
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}


def json_data(filename):
    with open(join(dirname(__file__),filename), "r") as f:
        return json.load(f)


@pytest.fixture()
def authors(app,db,esindex):
    datas = json_data("data/author.json")
    returns = list()
    for data in datas:
        returns.append(Authors(
            gather_flg=data.get("gather_flg", 0),
            is_deleted=data.get("is_deleted", False),
            json=data
        ))
        es_id = data["id"]
        es_data = json.loads(json.dumps(data))
        es_data["id"]=""
        current_search_client.index(
            index=app.config["WEKO_AUTHORS_ES_INDEX_NAME"],
            doc_type=app.config['WEKO_AUTHORS_ES_DOC_TYPE'],
            id=es_id,
            body=es_data,
            refresh='true')
    
    db.session.add_all(returns)
    db.session.commit()
    return returns

@pytest.fixture()
def authors2(app,db,esindex):
    datas = json_data("data/author2.json")
    returns = list()
    for data in datas:
        returns.append(Authors(
            gather_flg=0,
            is_deleted=False,
            json=data
        ))
        es_id = data["id"]
        es_data = json.loads(json.dumps(data))
        es_data["id"]=""
        current_search_client.index(
            index=app.config["WEKO_AUTHORS_ES_INDEX_NAME"],
            doc_type=app.config['WEKO_AUTHORS_ES_DOC_TYPE'],
            id=es_id,
            body=es_data,
            refresh='true')
    
    db.session.add_all(returns)
    db.session.commit()
    return returns


@pytest.fixture()
def location(app,db):
    """Create default location."""
    tmppath = tempfile.mkdtemp()
    with db.session.begin_nested():
        Location.query.delete()
        loc = Location(name='local', uri=tmppath, default=True)
        db.session.add(loc)
    db.session.commit()
    return loc


@pytest.fixture()
def authors_prefix_settings(db):
    apss = list()
    apss.append(AuthorsPrefixSettings(name="WEKO",scheme="WEKO"))
    apss.append(AuthorsPrefixSettings(name="ORCID",scheme="ORCID",url="https://orcid.org/##"))
    apss.append(AuthorsPrefixSettings(name="CiNii",scheme="CiNii",url="https://ci.nii.ac.jp/author/##"))
    apss.append(AuthorsPrefixSettings(name="KAKEN2",scheme="KAKEN2",url="https://nrid.nii.ac.jp/nrid/##"))
    apss.append(AuthorsPrefixSettings(name="ROR",scheme="ROR",url="https://ror.org/##"))
    db.session.add_all(apss)
    db.session.commit()
    return apss

@pytest.fixture()
def authors_affiliation_settings(db):
    aass = list()
    aass.append(AuthorsAffiliationSettings(name="ISNI",scheme="ISNI",url="http://www.isni.org/isni/##"))
    aass.append(AuthorsAffiliationSettings(name="GRID",scheme="GRID",url="https://www.grid.ac/institutes/##"))
    aass.append(AuthorsAffiliationSettings(name="Ringgold",scheme="Ringgold"))
    aass.append(AuthorsAffiliationSettings(name="kakenhi",scheme="kakenhi"))
    db.session.add_all(aass)
    db.session.commit()
    
    return aass

@pytest.fixture()
def file_instance(db):
    file = FileInstance(
        uri="/var/tmp/test_dir",
        storage_class="S",
        size=18,
    )
    db.session.add(file)
    db.session.commit()


# @pytest.fixture()
# def esindex(app2):
#     from invenio_search import current_search_client as client
#     index_name = app2.config["INDEXER_DEFAULT_INDEX"]
#     alias_name = "test-author-alias"

#     with open("tests/data/mappings/author-v1.0.0.json","r") as f:
#         mapping = json.load(f)

#     with app2.test_request_context():
#         client.indices.create(index=index_name, body=mapping, ignore=[400])
#         client.indices.put_alias(index=index_name, name=alias_name)

#     yield client

#     with app2.test_request_context():
#         client.indices.delete_alias(index=index_name, name=alias_name)
#         client.indices.delete(index=index_name, ignore=[400, 404])
        
from invenio_oauth2server.models import Client

@pytest.fixture()
def client_model(client_api, users):
    """Create client."""
    with db_.session.begin_nested():
        # create resource_owner -> client_1
        client_ = Client(
            client_id='client_test_u1c1',
            client_secret='client_test_u1c1',
            name='client_test_u1c1',
            description='',
            is_confidential=False,
            user=users[0]['obj'],
            _redirect_uris='',
            _default_scopes='',
        )
        db_.session.add(client_)
    db_.session.commit()
    return client_

@pytest.yield_fixture()
def client_api(app):
    app.register_blueprint(create_blueprint(app.config['WEKO_AUTHORS_REST_ENDPOINTS']))
    with app.test_client() as client:
        yield client

from invenio_oauth2server.models import Token
from datetime import timedelta
@pytest.fixture()
def create_token_user_noroleuser(client_api, client_model, users):
    """Create token."""
    with db_.session.begin_nested():
        token_ = Token(
            client=client_model,
            user=next((user for user in users if user["id"] == 9), None)['obj'],
            token_type='bearer',
            access_token='dev_access_create_token_user_noroleuser',
            # refresh_token='',
            expires=datetime.now() + timedelta(hours=10),
            is_personal=True,
            is_internal=False,
            _scopes="author:create author:delete author:search author:update",
        )
        db_.session.add(token_)
    db_.session.commit()
    return token_

@pytest.fixture()
def create_token_user_sysadmin(client_api, client_model, users):
    """Create token."""
    print(next((user for user in users if user["id"] == 5), None)['obj'])
    with db_.session.begin_nested():
        token_ = Token(
            client=client_model,
            user=next((user for user in users if user["id"] == 5), None)['obj'],
            token_type='bearer',
            access_token='dev_access_create_token_user_sysadmin',
            # refresh_token='',
            expires=datetime.now() + timedelta(hours=10),
            is_personal=True,
            is_internal=False,
            _scopes="author:create author:delete author:search author:update",
        )
        db_.session.add(token_)
    db_.session.commit()
    return token_

@pytest.fixture()
def create_token_user_sysadmin_without_scope(client_api, client_model, users):
    """Create token."""
    print(next((user for user in users if user["id"] == 5), None)['obj'])
    with db_.session.begin_nested():
        token_ = Token(
            client=client_model,
            user=next((user for user in users if user["id"] == 5), None)['obj'],
            token_type='bearer',
            access_token='dev_access_create_token_user_sysadmin_without_scope',
            # refresh_token='',
            expires=datetime.now() + timedelta(hours=10),
            is_personal=True,
            is_internal=False,
            _scopes="",
        )
        db_.session.add(token_)
    db_.session.commit()
    return token_

@pytest.fixture()
def json_headers():
    """JSON headers."""
    return [('Content-Type', 'application/json'),
            ('Accept', 'application/json')]

from copy import deepcopy
def fill_oauth2_headers(json_headers, token):
    """Create authentication headers (with a valid oauth2 token)."""
    headers = deepcopy(json_headers)
    headers.append(
        ('Authorization', 'Bearer {0}'.format(token.access_token))
    )
    return headers

@pytest.fixture()
def auth_headers_noroleuser(client_api, json_headers, create_token_user_noroleuser):
    """Authentication headers (with a valid oauth2 token).
    It uses the token associated with the first user.
    """
    return fill_oauth2_headers(json_headers, create_token_user_noroleuser)

@pytest.fixture()
def auth_headers_sysadmin(client_api, json_headers, create_token_user_sysadmin):
    """Authentication headers (with a valid oauth2 token).
    It uses the token associated with the first user.
    """
    return fill_oauth2_headers(json_headers, create_token_user_sysadmin)

@pytest.fixture()
def auth_headers_sysadmin_without_scope(client_api, json_headers, create_token_user_sysadmin_without_scope):
    """Authentication headers (with a valid oauth2 token).
    It uses the token associated with the first user.
    """
    return fill_oauth2_headers(json_headers, create_token_user_sysadmin_without_scope)

@pytest.fixture
def author_records_for_test(app, esindex, db):
    record_1_data = {
        "emailInfo": [{"email": "sample@xxx.co.jp"}],
        "authorIdInfo": [
            {"idType": "2", "authorId": "https://orcid.org/##", "authorIdShowFlg": "true"},
            {"idType": "1", "authorId": "1", "authorIdShowFlg": "true"}
        ],
        "authorNameInfo": [
            {"language": "en", "firstName": "Test_1", "familyName": "User_1", "nameFormat": "familyNmAndNm", "nameShowFlg": "true"}
        ],
        "affiliationInfo": [{
            "identifierInfo": [{"affiliationId": "https://ror.org/##", "affiliationIdType": "3", "identifierShowFlg": "true"}],
            "affiliationNameInfo": [{"affiliationName": "NII", "affiliationNameLang": "en", "affiliationNameShowFlg": "true"}]
        }]
    }

    record_2_data = {
        "emailInfo": [{"email": "sample@xxx.co.jp"}],
        "authorIdInfo": [
            {"idType": "2", "authorId": "https://orcid.org/##", "authorIdShowFlg": "true"},
            {"idType": "1", "authorId": "2", "authorIdShowFlg": "true"}
        ],
        "authorNameInfo": [
            {"language": "en", "firstName": "Test_2", "familyName": "User_2", "nameFormat": "familyNmAndNm", "nameShowFlg": "true"}
        ],
        "affiliationInfo": [{
            "identifierInfo": [{"affiliationId": "https://ror.org/##", "affiliationIdType": "3", "identifierShowFlg": "true"}],
            "affiliationNameInfo": [{"affiliationName": "NII", "affiliationNameLang": "en", "affiliationNameShowFlg": "true"}]
        }]
    }

    record_3_data = {
        "emailInfo": [{"email": "sample@xxx.co.jp"}],
        "authorIdInfo": [
            {"idType": "2", "authorId": "https://orcid.org/##", "authorIdShowFlg": "true"},
            {"idType": "1", "authorId": "3", "authorIdShowFlg": "true"}
        ],
        "authorNameInfo": [
            {"language": "en", "firstName": "Test_3", "familyName": "User_3", "nameFormat": "familyNmAndNm", "nameShowFlg": "true"}
        ],
        "affiliationInfo": [{
            "identifierInfo": [{"affiliationId": "https://ror.org/##", "affiliationIdType": "3", "identifierShowFlg": "true"}],
            "affiliationNameInfo": [{"affiliationName": "NII", "affiliationNameLang": "en", "affiliationNameShowFlg": "true"}]
        }]
    }
    record_4_data = {
        "emailInfo": [{"email": "sample@xxx.co.jp"}],
        "authorIdInfo": [
            {"idType": "2", "authorId": "https://orcid.org/##", "authorIdShowFlg": "true"},
            {"idType": "1", "authorId": "4", "authorIdShowFlg": "true"}
        ],
        "authorNameInfo": [
            {"language": "en", "firstName": "Test_3", "familyName": "User_3", "nameFormat": "familyNmAndNm", "nameShowFlg": "true"}
        ],
        "affiliationInfo": [{
            "identifierInfo": [{"affiliationId": "https://ror.org/##", "affiliationIdType": "3", "identifierShowFlg": "true"}],
            "affiliationNameInfo": [{"affiliationName": "NII", "affiliationNameLang": "en", "affiliationNameShowFlg": "true"}]
        }]
    }
    from weko_authors.api import WekoAuthors
    record_1 = WekoAuthors.create(record_1_data)
    record_2 = WekoAuthors.create(record_2_data)
    record_3 = WekoAuthors.create(record_3_data)
    record_3 = WekoAuthors.create(record_4_data)
    
    esindex.indices.refresh(index=app.config['WEKO_AUTHORS_ES_INDEX_NAME'])
    result=[]
    for i in range(4):
        search_results = esindex.search(
            index=app.config['WEKO_AUTHORS_ES_INDEX_NAME'],
            body={"query": {"term": {"pk_id": i+1}}},
            size=1
        )
        if search_results["hits"]["total"] > 0:
            
            result.append(search_results["hits"]["hits"][0]["_id"])

    return {
        "1": result[0],
        "2": result[1],
        "3": result[2],
        "4": result[3]
    }