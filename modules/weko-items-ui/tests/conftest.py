# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Pytest configuration."""

import json
import os
from re import T
import shutil
import tempfile
import uuid
import time
from datetime import datetime
from os.path import dirname, exists, join
import copy
import pytest
from kombu import Exchange, Queue
from mock import patch
from click.testing import CliRunner
from flask import Blueprint, Flask
from flask_assets import assets
from flask_babelex import Babel
from flask_menu import Menu
from invenio_access import InvenioAccess
from invenio_access.models import ActionRoles, ActionUsers
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import Role, User
from invenio_accounts.testutils import create_test_user, login_user_via_session
from invenio_accounts.views.settings import blueprint as invenio_accounts_blueprint
from invenio_admin import InvenioAdmin
from invenio_admin.views import blueprint as invenio_admin_blueprint
from invenio_assets import InvenioAssets
from invenio_assets.cli import collect, npm
from invenio_cache import InvenioCache
from invenio_communities import InvenioCommunities
from invenio_communities.models import Community
from invenio_communities.views.ui import blueprint as invenio_communities_blueprint
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_deposit import InvenioDeposit
from invenio_deposit.config import (
    DEPOSIT_DEFAULT_STORAGE_CLASS,
    DEPOSIT_RECORDS_UI_ENDPOINTS,
    DEPOSIT_REST_ENDPOINTS,
    DEPOSIT_DEFAULT_JSONSCHEMA,
    DEPOSIT_JSONSCHEMAS_PREFIX,
)
from invenio_files_rest.models import Location, Bucket,ObjectVersion,FileInstance
from invenio_records_files.api import RecordsBuckets
from invenio_deposit.ext import InvenioDeposit, InvenioDepositREST
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.config import FILES_REST_STORAGE_CLASS_LIST
from invenio_files_rest.models import Location
from invenio_i18n import InvenioI18N
from invenio_indexer import InvenioIndexer
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_oaiserver import InvenioOAIServer
from invenio_pidrelations import InvenioPIDRelations
from celery.messaging import establish_connection
from invenio_pidrelations.models import PIDRelation
from invenio_pidstore import InvenioPIDStore
from invenio_pidstore.models import PersistentIdentifier, PIDStatus, Redirect
from invenio_records import InvenioRecords
from invenio_records_rest import InvenioRecordsREST
from invenio_rest import InvenioREST
from invenio_search import InvenioSearch, RecordsSearch, current_search, current_search_client
from invenio_stats import InvenioStats
from invenio_stats.config import SEARCH_INDEX_PREFIX as index_prefix
from invenio_theme import InvenioTheme
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy_utils.functions import create_database, database_exists
from weko_admin import WekoAdmin
from weko_admin.config import WEKO_ADMIN_DEFAULT_ITEM_EXPORT_SETTINGS
from weko_admin.models import SessionLifetime,RankingSettings
from weko_deposit import WekoDeposit
from weko_deposit.api import WekoIndexer
from weko_deposit.config import DEPOSIT_RECORDS_API,WEKO_DEPOSIT_ITEMS_CACHE_PREFIX
from weko_index_tree import WekoIndexTree, WekoIndexTreeREST
from weko_index_tree.api import Indexes
from weko_index_tree.models import Index
from weko_index_tree.config import WEKO_INDEX_TREE_REST_ENDPOINTS,WEKO_INDEX_TREE_DEFAULT_DISPLAY_NUMBER
from weko_records import WekoRecords
from weko_records.models import ItemType, ItemTypeMapping, ItemTypeName
from weko_records_ui import WekoRecordsUI
from weko_records_ui.config import WEKO_RECORDS_UI_LICENSE_DICT
from weko_schema_ui import WekoSchemaUI
from weko_schema_ui.models import OAIServerSchema
from weko_search_ui import WekoSearchREST, WekoSearchUI
from weko_search_ui.config import WEKO_SEARCH_REST_ENDPOINTS,RECORDS_REST_SORT_OPTIONS,INDEXER_DEFAULT_DOCTYPE,INDEXER_FILE_DOC_TYPE
from weko_theme import WekoTheme
from weko_theme.views import blueprint as weko_theme_blueprint
from weko_user_profiles.models import UserProfile
from weko_user_profiles.config import WEKO_USERPROFILES_ROLES,WEKO_USERPROFILES_GENERAL_ROLE
from weko_search_ui.config import SEARCH_UI_SEARCH_INDEX
from weko_workflow import WekoWorkflow
from weko_authors.models import AuthorsPrefixSettings,Authors,AuthorsAffiliationSettings
from weko_workflow.models import (
    Action,
    ActionStatus,
    ActionStatusPolicy,
    Activity,
    FlowAction,
    FlowDefine,
    WorkFlow,
)
from weko_workflow.views import workflow_blueprint as weko_workflow_blueprint
from werkzeug.local import LocalProxy

from tests.helpers import create_record, json_data
from weko_items_ui import WekoItemsUI
from weko_items_ui.views import blueprint as weko_items_ui_blueprint
from weko_items_ui.views import blueprint_api as weko_items_ui_blueprint_api
from weko_groups import WekoGroups

from invenio_pidrelations.config import PIDRELATIONS_RELATION_TYPES


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=OFF;")
    cursor.close()


@event.listens_for(Session, "after_begin")
def receive_after_begin(session, transaction, connection):
    connection.execute("PRAGMA foreign_keys=OFF;")


@pytest.yield_fixture()
def instance_path():
    """Temporary instance path."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.fixture()
def base_app(instance_path):
    """Flask application fixture."""
    app_ = Flask(
        "testapp",
        instance_path=instance_path,
        static_folder=join(instance_path, "static"),
    )
    app_.config.update(
        SECRET_KEY="SECRET_KEY",
        TESTING=True,
        SERVER_NAME="test_server",
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "SQLALCHEMY_DATABASE_URI", "sqlite:///test.db"
        ),
        #SQLALCHEMY_DATABASE_URI='postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest',
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        ACCOUNTS_USERINFO_HEADERS=True,
        WEKO_PERMISSION_SUPER_ROLE_USER=[
            "System Administrator",
            "Repository Administrator",
        ],
        WEKO_PERMISSION_ROLE_COMMUNITY=["Community Administrator"],
        THEME_SITEURL="https://localhost",
        WEKO_THEME_DEFAULT_COMMUNITY="Root Index",
        #  WEKO_ITEMS_UI_BASE_TEMPLATE = 'weko_items_ui/base.html',
        #  WEKO_ITEMS_UI_INDEX_TEMPLATE= 'weko_items_ui/item_index.html',
        CACHE_TYPE="redis",
        ACCOUNTS_SESSION_REDIS_DB_NO=1,
        CACHE_REDIS_HOST=os.environ.get("INVENIO_REDIS_HOST"),
        REDIS_PORT="6379",
        WEKO_BUCKET_QUOTA_SIZE=50 * 1024 * 1024 * 1024,
        WEKO_MAX_FILE_SIZE=50 * 1024 * 1024 * 1024,
        SEARCH_ELASTIC_HOSTS=os.environ.get("INVENIO_ELASTICSEARCH_HOST"),
        SEARCH_INDEX_PREFIX="{}-".format('test'),
        SEARCH_CLIENT_CONFIG=dict(timeout=120, max_retries=10),
        OAISERVER_ID_PREFIX="oai:inveniosoftware.org:recid/",
        OAISERVER_RECORD_INDEX="_all",
        OAISERVER_REGISTER_SET_SIGNALS=True,
        OAISERVER_METADATA_FORMATS={
            "jpcoar_1.0": {
                "serializer": (
                    "weko_schema_ui.utils:dumps_oai_etree",
                    {
                        "schema_type": "jpcoar_v1",
                    },
                ),
                "namespace": "https://irdb.nii.ac.jp/schema/jpcoar/1.0/",
                "schema": "https://irdb.nii.ac.jp/schema/jpcoar/1.0/jpcoar_scm.xsd",
            }
        },
        DEPOSIT_RECORDS_UI_ENDPOINTS=DEPOSIT_RECORDS_UI_ENDPOINTS,
        DEPOSIT_REST_ENDPOINTS=DEPOSIT_REST_ENDPOINTS,
        DEPOSIT_DEFAULT_STORAGE_CLASS=DEPOSIT_DEFAULT_STORAGE_CLASS,
        
        WEKO_RECORDS_UI_LICENSE_DICT=WEKO_RECORDS_UI_LICENSE_DICT,
        INDEXER_DEFAULT_INDEX="{}-weko-item-v1.0.0".format(
            'test'
        ),
        WEKO_INDEX_TREE_REST_ENDPOINTS=WEKO_INDEX_TREE_REST_ENDPOINTS,
        WEKO_ADMIN_DEFAULT_ITEM_EXPORT_SETTINGS=WEKO_ADMIN_DEFAULT_ITEM_EXPORT_SETTINGS,
        FILES_REST_STORAGE_CLASS_LIST=FILES_REST_STORAGE_CLASS_LIST,
        FILES_REST_DEFAULT_QUOTA_SIZE=None,
        FILES_REST_DEFAULT_MAX_FILE_SIZE=None,
        DEPOSIT_RECORDS_API=DEPOSIT_RECORDS_API,
        RECORDS_REST_SORT_OPTIONS=RECORDS_REST_SORT_OPTIONS,
        PIDRELATIONS_RELATION_TYPES=PIDRELATIONS_RELATION_TYPES,
        WEKO_USERPROFILES_ROLES=WEKO_USERPROFILES_ROLES,
        EMAIL_DISPLAY_FLG = True,
        SEARCH_UI_SEARCH_INDEX="test-weko",
        WEKO_USERPROFILES_GENERAL_ROLE=WEKO_USERPROFILES_GENERAL_ROLE,
        CACHE_REDIS_DB = 0,
        WEKO_DEPOSIT_ITEMS_CACHE_PREFIX=WEKO_DEPOSIT_ITEMS_CACHE_PREFIX,
        INDEXER_DEFAULT_DOCTYPE=INDEXER_DEFAULT_DOCTYPE,
        INDEXER_FILE_DOC_TYPE=INDEXER_FILE_DOC_TYPE,
        WEKO_INDEX_TREE_DEFAULT_DISPLAY_NUMBER=WEKO_INDEX_TREE_DEFAULT_DISPLAY_NUMBER,
        DEPOSIT_DEFAULT_JSONSCHEMA=DEPOSIT_DEFAULT_JSONSCHEMA,
        DEPOSIT_JSONSCHEMAS_PREFIX=DEPOSIT_JSONSCHEMAS_PREFIX,
        WEKO_SEARCH_REST_ENDPOINTS=WEKO_SEARCH_REST_ENDPOINTS,
        INDEXER_MQ_QUEUE = Queue("indexer", exchange=Exchange("indexer", type="direct"), routing_key="indexer",queue_arguments={"x-queue-type":"quorum"}),
    )
    
    app_.config['WEKO_SEARCH_REST_ENDPOINTS']['recid']['search_index']='test-weko'
    # tmp = app_.config['RECORDS_REST_SORT_OPTIONS']['tenant1-weko']
    # app_.config['RECORDS_REST_SORT_OPTIONS']['test-weko']=tmp
    # Babel(app_)
    InvenioI18N(app_)
    InvenioAssets(app_)
    InvenioDB(app_)
    InvenioAccounts(app_)
    InvenioAccess(app_)
    # InvenioTheme(app_)
    # InvenioREST(app_)

    # InvenioCache(app_)

    # InvenioDeposit(app_)
    # InvenioPIDStore(app_)
    # InvenioPIDRelations(app_)
    InvenioRecords(app_)
    # InvenioRecordsREST(app_)
    InvenioFilesREST(app_)
    InvenioJSONSchemas(app_)
    # InvenioOAIServer(app_)

    search = InvenioSearch(app_)
 
    # WekoSchemaUI(app_)
    InvenioStats(app_)

    # InvenioAdmin(app_)
    Menu(app_)
    WekoRecords(app_)
    WekoDeposit(app_)
    WekoWorkflow(app_)
    WekoGroups(app_)
    # WekoAdmin(app_)
    # WekoTheme(app_)
    # WekoRecordsUI(app_)
    # InvenioCommunities(app_)

    InvenioIndexer(app_)
    # WekoSearchREST(app_)
    # WekoIndexTree(app_)
    # WekoIndexTreeREST(app_)
    WekoRecords(app_)
    WekoSearchUI(app_)
    # ext.init_config(app_)
    WekoItemsUI(app_)

    # app_.register_blueprint(invenio_accounts_blueprint)
    # app_.register_blueprint(weko_theme_blueprint)
    # app_.register_blueprint(weko_items_ui_blueprint)
    # app_.register_blueprint(invenio_communities_blueprint)
    # app_.register_blueprint(weko_workflow_blueprint)

    # runner = CliRunner()
    # result = runner.invoke(collect, [],obj=weko_items_ui_blueprint)
    # Run build
    # result = runner.invoke(assets, ['build'],obj=weko_items_ui_blueprint)
    # result = runner.invoke(npm,obj=weko_items_ui_blueprint)

    current_assets = LocalProxy(lambda: app_.extensions["invenio-assets"])
    current_assets.collect.collect()

    return app_



@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app


@pytest.yield_fixture()
def client_api(app):
    app.register_blueprint(weko_items_ui_blueprint_api, url_prefix="/api/items")
    with app.test_client() as client:
        yield client



@pytest.yield_fixture()
def client(app):
    """make a test client.

    Args:
        app (Flask): flask app.

    Yields:
        FlaskClient: test client
    """
    app.register_blueprint(weko_items_ui_blueprint, url_prefix="/items")
    with app.test_client() as client:
        yield client


@pytest.fixture()
def db(app):
    """Database fixture."""
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()

@pytest.fixture()
def esindex(app,db_records):
    current_search_client.indices.delete(index='test-*')
    with open("tests/data/mappings/item-v1.0.0.json","r") as f:
        mapping = json.load(f)
    with open("tests/data/mappings/record-view-v1.json","r") as f:
        mapping_record_view = json.load(f)

    search = LocalProxy(lambda: app.extensions["invenio-search"])

    with app.test_request_context():
        current_search_client.indices.create(app.config["INDEXER_DEFAULT_INDEX"],body=mapping)
        current_search_client.indices.put_alias(index=app.config["INDEXER_DEFAULT_INDEX"], name="test-weko")
        # print(current_search_client.indices.get_alias())
        current_search_client.indices.create("test-stats-record-view-000001",body=mapping_record_view)
        current_search_client.indices.put_alias(index="test-stats-record-view-000001",name="test-stats-record-view")
    
    for depid, recid, parent, doi, record, item in db_records:
        current_search_client.index(index='test-weko-item-v1.0.0', doc_type='item-v1.0.0', id=record.id, body=record,refresh='true')
    
    yield current_search_client

    with app.test_request_context():
        current_search_client.indices.delete_alias(index=app.config["INDEXER_DEFAULT_INDEX"], name="test-weko")
        current_search_client.indices.delete(index=app.config["INDEXER_DEFAULT_INDEX"], ignore=[400, 404])
        #current_search_client.indices.delete_alias(index="test-stats-record-view-000001",name="test-stats-record-view")
        #current_search_client.indices.delete(index="test-stats-record-view-000001", ignore=[400,400])


@pytest.fixture()
def users(app, db):
    """Create users."""
    ds = app.extensions["invenio-accounts"].datastore
    user_count = User.query.filter_by(email="user@test.org").count()
    if user_count != 1:
        user = create_test_user(email="user@test.org")
        contributor = create_test_user(email="contributor@test.org")
        comadmin = create_test_user(email="comadmin@test.org")
        repoadmin = create_test_user(email="repoadmin@test.org")
        sysadmin = create_test_user(email="sysadmin@test.org")
        generaluser = create_test_user(email="generaluser@test.org")
        originalroleuser = create_test_user(email="originalroleuser@test.org")
        originalroleuser2 = create_test_user(email="originalroleuser2@test.org")
    else:
        user = User.query.filter_by(email="user@test.org").first()
        contributor = User.query.filter_by(email="contributor@test.org").first()
        comadmin = User.query.filter_by(email="comadmin@test.org").first()
        repoadmin = User.query.filter_by(email="repoadmin@test.org").first()
        sysadmin = User.query.filter_by(email="sysadmin@test.org").first()
        generaluser = User.query.filter_by(email="generaluser@test.org")
        originalroleuser = create_test_user(email="originalroleuser@test.org")
        originalroleuser2 = create_test_user(email="originalroleuser2@test.org")

    role_count = Role.query.filter_by(name="System Administrator").count()
    if role_count != 1:
        sysadmin_role = ds.create_role(name="System Administrator")
        repoadmin_role = ds.create_role(name="Repository Administrator")
        contributor_role = ds.create_role(name="Contributor")
        comadmin_role = ds.create_role(name="Community Administrator")
        general_role = ds.create_role(name="General")
        originalrole = ds.create_role(name="Original Role")
    else:
        sysadmin_role = Role.query.filter_by(name="System Administrator").first()
        repoadmin_role = Role.query.filter_by(name="Repository Administrator").first()
        contributor_role = Role.query.filter_by(name="Contributor").first()
        comadmin_role = Role.query.filter_by(name="Community Administrator").first()
        general_role = Role.query.filter_by(name="General").first()
        originalrole = Role.query.filter_by(name="Original Role").first()



    # Assign access authorization
    with db.session.begin_nested():
        action_users = [
            ActionUsers(action="superuser-access", user=sysadmin),
        ]
        db.session.add_all(action_users)
        action_roles = [
            ActionRoles(action="superuser-access", role=sysadmin_role),
            ActionRoles(action="admin-access", role=repoadmin_role),
            ActionRoles(action="schema-access", role=repoadmin_role),
            ActionRoles(action="index-tree-access", role=repoadmin_role),
            ActionRoles(action="indextree-journal-access", role=repoadmin_role),
            ActionRoles(action="item-type-access", role=repoadmin_role),
            ActionRoles(action="item-access", role=repoadmin_role),
            ActionRoles(action="files-rest-bucket-update", role=repoadmin_role),
            ActionRoles(action="files-rest-object-delete", role=repoadmin_role),
            ActionRoles(action="files-rest-object-delete-version", role=repoadmin_role),
            ActionRoles(action="files-rest-object-read", role=repoadmin_role),
            ActionRoles(action="search-access", role=repoadmin_role),
            ActionRoles(action="detail-page-acces", role=repoadmin_role),
            ActionRoles(action="download-original-pdf-access", role=repoadmin_role),
            ActionRoles(action="author-access", role=repoadmin_role),
            ActionRoles(action="items-autofill", role=repoadmin_role),
            ActionRoles(action="stats-api-access", role=repoadmin_role),
            ActionRoles(action="read-style-action", role=repoadmin_role),
            ActionRoles(action="update-style-action", role=repoadmin_role),
            ActionRoles(action="detail-page-acces", role=repoadmin_role),
            ActionRoles(action="admin-access", role=comadmin_role),
            ActionRoles(action="index-tree-access", role=comadmin_role),
            ActionRoles(action="indextree-journal-access", role=comadmin_role),
            ActionRoles(action="item-access", role=comadmin_role),
            ActionRoles(action="files-rest-bucket-update", role=comadmin_role),
            ActionRoles(action="files-rest-object-delete", role=comadmin_role),
            ActionRoles(action="files-rest-object-delete-version", role=comadmin_role),
            ActionRoles(action="files-rest-object-read", role=comadmin_role),
            ActionRoles(action="search-access", role=comadmin_role),
            ActionRoles(action="detail-page-acces", role=comadmin_role),
            ActionRoles(action="download-original-pdf-access", role=comadmin_role),
            ActionRoles(action="author-access", role=comadmin_role),
            ActionRoles(action="items-autofill", role=comadmin_role),
            ActionRoles(action="detail-page-acces", role=comadmin_role),
            ActionRoles(action="detail-page-acces", role=comadmin_role),
            ActionRoles(action="item-access", role=contributor_role),
            ActionRoles(action="files-rest-bucket-update", role=contributor_role),
            ActionRoles(action="files-rest-object-delete", role=contributor_role),
            ActionRoles(
                action="files-rest-object-delete-version", role=contributor_role
            ),
            ActionRoles(action="files-rest-object-read", role=contributor_role),
            ActionRoles(action="search-access", role=contributor_role),
            ActionRoles(action="detail-page-acces", role=contributor_role),
            ActionRoles(action="download-original-pdf-access", role=contributor_role),
            ActionRoles(action="author-access", role=contributor_role),
            ActionRoles(action="items-autofill", role=contributor_role),
            ActionRoles(action="detail-page-acces", role=contributor_role),
            ActionRoles(action="detail-page-acces", role=contributor_role),
        ]
        db.session.add_all(action_roles)
        ds.add_role_to_user(sysadmin, sysadmin_role)
        ds.add_role_to_user(repoadmin, repoadmin_role)
        ds.add_role_to_user(contributor, contributor_role)
        ds.add_role_to_user(comadmin, comadmin_role)
        ds.add_role_to_user(generaluser, general_role)
        ds.add_role_to_user(originalroleuser, originalrole)
        ds.add_role_to_user(originalroleuser2, originalrole)
        ds.add_role_to_user(originalroleuser2, repoadmin_role)
        

    return [
        {"email": contributor.email, "id": contributor.id, "obj": contributor},
        {"email": repoadmin.email, "id": repoadmin.id, "obj": repoadmin},
        {"email": sysadmin.email, "id": sysadmin.id, "obj": sysadmin},
        {"email": comadmin.email, "id": comadmin.id, "obj": comadmin},
        {"email": generaluser.email, "id": generaluser.id, "obj": sysadmin},
        {
            "email": originalroleuser.email,
            "id": originalroleuser.id,
            "obj": originalroleuser,
        },
        {
            "email": originalroleuser2.email,
            "id": originalroleuser2.id,
            "obj": originalroleuser2,
        },
        {"email": user.email, "id": user.id, "obj": user},
    ]



@pytest.fixture()
def db_oaischema(app, db):
    schema_name = "jpcoar_mapping"
    form_data = {"name": "jpcoar", "file_name": "jpcoar_scm.xsd", "root_name": "jpcoar"}
    xsd = '{"dc:title": {"type": {"maxOccurs": "unbounded", "minOccurs": 1, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "dcterms:alternative": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:creator": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}, "jpcoar:nameIdentifier": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "nameIdentifierScheme", "ref": null, "restriction": {"enumeration": ["e-Rad", "NRID", "ORCID", "ISNI", "VIAF", "AID", "kakenhi", "Ringgold", "GRID"]}}, {"use": "optional", "name": "nameIdentifierURI", "ref": null}]}}, "jpcoar:creatorName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:familyName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:givenName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:creatorAlternative": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:affiliation": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}, "jpcoar:nameIdentifier": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "nameIdentifierScheme", "ref": null, "restriction": {"enumeration": ["e-Rad", "NRID", "ORCID", "ISNI", "VIAF", "AID", "kakenhi", "Ringgold", "GRID"]}}, {"use": "optional", "name": "nameIdentifierURI", "ref": null}]}}, "jpcoar:affiliationName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}}}, "jpcoar:contributor": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "contributorType", "ref": null, "restriction": {"enumeration": ["ContactPerson", "DataCollector", "DataCurator", "DataManager", "Distributor", "Editor", "HostingInstitution", "Producer", "ProjectLeader", "ProjectManager", "ProjectMember", "RegistrationAgency", "RegistrationAuthority", "RelatedPerson", "Researcher", "ResearchGroup", "Sponsor", "Supervisor", "WorkPackageLeader", "Other"]}}]}, "jpcoar:nameIdentifier": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "nameIdentifierScheme", "ref": null, "restriction": {"enumeration": ["e-Rad", "NRID", "ORCID", "ISNI", "VIAF", "AID", "kakenhi", "Ringgold", "GRID"]}}, {"use": "optional", "name": "nameIdentifierURI", "ref": null}]}}, "jpcoar:contributorName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:familyName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:givenName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:contributorAlternative": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:affiliation": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}, "jpcoar:nameIdentifier": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "nameIdentifierScheme", "ref": null, "restriction": {"enumeration": ["e-Rad", "NRID", "ORCID", "ISNI", "VIAF", "AID", "kakenhi", "Ringgold", "GRID"]}}, {"use": "optional", "name": "nameIdentifierURI", "ref": null}]}}, "jpcoar:affiliationName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}}}, "dcterms:accessRights": {"type": {"maxOccurs": 1, "minOccurs": 0, "attributes": [{"use": "required", "name": "rdf:resource", "ref": "rdf:resource"}], "restriction": {"enumeration": ["embargoed access", "metadata only access", "open access", "restricted access"]}}}, "rioxxterms:apc": {"type": {"maxOccurs": 1, "minOccurs": 0, "restriction": {"enumeration": ["Paid", "Partially waived", "Fully waived", "Not charged", "Not required", "Unknown"]}}}, "dc:rights": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "rdf:resource", "ref": "rdf:resource"}, {"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:rightsHolder": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}, "jpcoar:nameIdentifier": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "nameIdentifierScheme", "ref": null, "restriction": {"enumeration": ["e-Rad", "NRID", "ORCID", "ISNI", "VIAF", "AID", "kakenhi", "Ringgold", "GRID"]}}, {"use": "optional", "name": "nameIdentifierURI", "ref": null}]}}, "jpcoar:rightsHolderName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}}, "jpcoar:subject": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}, {"use": "optional", "name": "subjectURI", "ref": null}, {"use": "required", "name": "subjectScheme", "ref": null, "restriction": {"enumeration": ["BSH", "DDC", "LCC", "LCSH", "MeSH", "NDC", "NDLC", "NDLSH", "Sci-Val", "UDC", "Other"]}}]}}, "datacite:description": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}, {"use": "required", "name": "descriptionType", "ref": null, "restriction": {"enumeration": ["Abstract", "Methods", "TableOfContents", "TechnicalInfo", "Other"]}}]}}, "dc:publisher": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "datacite:date": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "dateType", "ref": null, "restriction": {"enumeration": ["Accepted", "Available", "Collected", "Copyrighted", "Created", "Issued", "Submitted", "Updated", "Valid"]}}]}}, "dc:language": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "restriction": {"patterns": ["^[a-z]{3}$"]}}}, "dc:type": {"type": {"maxOccurs": 1, "minOccurs": 1, "attributes": [{"use": "required", "name": "rdf:resource", "ref": "rdf:resource"}], "restriction": {"enumeration": ["conference paper", "data paper", "departmental bulletin paper", "editorial", "journal article", "newspaper", "periodical", "review article", "software paper", "article", "book", "book part", "cartographic material", "map", "conference object", "conference proceedings", "conference poster", "dataset", "aggregated data", "clinical trial data", "compiled data", "encoded data", "experimental data", "genomic data", "geospatial data", "laboratory notebook", "measurement and test data", "observational data", "recorded data", "simulation data", "survey data", "interview", "image", "still image", "moving image", "video", "lecture", "patent", "internal report", "report", "research report", "technical report", "policy report", "report part", "working paper", "data management plan", "sound", "thesis", "bachelor thesis", "master thesis", "doctoral thesis", "interactive resource", "learning object", "manuscript", "musical notation", "research proposal", "software", "technical documentation", "workflow", "other"]}}}, "datacite:version": {"type": {"maxOccurs": 1, "minOccurs": 0}}, "oaire:versiontype": {"type": {"maxOccurs": 1, "minOccurs": 0, "attributes": [{"use": "required", "name": "rdf:resource", "ref": "rdf:resource"}], "restriction": {"enumeration": ["AO", "SMUR", "AM", "P", "VoR", "CVoR", "EVoR", "NA"]}}}, "jpcoar:identifier": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "identifierType", "ref": null, "restriction": {"enumeration": ["DOI", "HDL", "URI"]}}]}}, "jpcoar:identifierRegistration": {"type": {"maxOccurs": 1, "minOccurs": 0, "attributes": [{"use": "required", "name": "identifierType", "ref": null, "restriction": {"enumeration": ["JaLC", "Crossref", "DataCite", "PMID"]}}]}}, "jpcoar:relation": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "relationType", "ref": null, "restriction": {"enumeration": ["isVersionOf", "hasVersion", "isPartOf", "hasPart", "isReferencedBy", "references", "isFormatOf", "hasFormat", "isReplacedBy", "replaces", "isRequiredBy", "requires", "isSupplementTo", "isSupplementedBy", "isIdenticalTo", "isDerivedFrom", "isSourceOf"]}}]}, "jpcoar:relatedIdentifier": {"type": {"maxOccurs": 1, "minOccurs": 0, "attributes": [{"use": "required", "name": "identifierType", "ref": null, "restriction": {"enumeration": ["ARK", "arXiv", "DOI", "HDL", "ICHUSHI", "ISBN", "J-GLOBAL", "Local", "PISSN", "EISSN", "NAID", "PMID", "PURL", "SCOPUS", "URI", "WOS"]}}]}}, "jpcoar:relatedTitle": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}}, "dcterms:temporal": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "datacite:geoLocation": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}, "datacite:geoLocationPoint": {"type": {"maxOccurs": 1, "minOccurs": 0}, "datacite:pointLongitude": {"type": {"maxOccurs": 1, "minOccurs": 1, "restriction": {"maxInclusive": 180, "minInclusive": -180}}}, "datacite:pointLatitude": {"type": {"maxOccurs": 1, "minOccurs": 1, "restriction": {"maxInclusive": 90, "minInclusive": -90}}}}, "datacite:geoLocationBox": {"type": {"maxOccurs": 1, "minOccurs": 0}, "datacite:westBoundLongitude": {"type": {"maxOccurs": 1, "minOccurs": 1, "restriction": {"maxInclusive": 180, "minInclusive": -180}}}, "datacite:eastBoundLongitude": {"type": {"maxOccurs": 1, "minOccurs": 1, "restriction": {"maxInclusive": 180, "minInclusive": -180}}}, "datacite:southBoundLatitude": {"type": {"maxOccurs": 1, "minOccurs": 1, "restriction": {"maxInclusive": 90, "minInclusive": -90}}}, "datacite:northBoundLatitude": {"type": {"maxOccurs": 1, "minOccurs": 1, "restriction": {"maxInclusive": 90, "minInclusive": -90}}}}, "datacite:geoLocationPlace": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}}}, "jpcoar:fundingReference": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}, "datacite:funderIdentifier": {"type": {"maxOccurs": 1, "minOccurs": 0, "attributes": [{"use": "required", "name": "funderIdentifierType", "ref": null, "restriction": {"enumeration": ["Crossref Funder", "GRID", "ISNI", "Other"]}}]}}, "jpcoar:funderName": {"type": {"maxOccurs": "unbounded", "minOccurs": 1, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "datacite:awardNumber": {"type": {"maxOccurs": 1, "minOccurs": 0, "attributes": [{"use": "optional", "name": "awardURI", "ref": null}]}}, "jpcoar:awardTitle": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}}, "jpcoar:sourceIdentifier": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "identifierType", "ref": null, "restriction": {"enumeration": ["PISSN", "EISSN", "ISSN", "NCID"]}}]}}, "jpcoar:sourceTitle": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:volume": {"type": {"maxOccurs": 1, "minOccurs": 0}}, "jpcoar:issue": {"type": {"maxOccurs": 1, "minOccurs": 0}}, "jpcoar:numPages": {"type": {"maxOccurs": 1, "minOccurs": 0}}, "jpcoar:pageStart": {"type": {"maxOccurs": 1, "minOccurs": 0}}, "jpcoar:pageEnd": {"type": {"maxOccurs": 1, "minOccurs": 0}}, "dcndl:dissertationNumber": {"type": {"maxOccurs": 1, "minOccurs": 0}}, "dcndl:degreeName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "dcndl:dateGranted": {"type": {"maxOccurs": 1, "minOccurs": 0}}, "jpcoar:degreeGrantor": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}, "jpcoar:nameIdentifier": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "nameIdentifierScheme", "ref": null, "restriction": {"enumeration": ["e-Rad", "NRID", "ORCID", "ISNI", "VIAF", "AID", "kakenhi", "Ringgold", "GRID"]}}, {"use": "optional", "name": "nameIdentifierURI", "ref": null}]}}, "jpcoar:degreeGrantorName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}}, "jpcoar:conference": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}, "jpcoar:conferenceName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:conferenceSequence": {"type": {"maxOccurs": 1, "minOccurs": 0}}, "jpcoar:conferenceSponsor": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:conferenceDate": {"type": {"maxOccurs": 1, "minOccurs": 0, "attributes": [{"use": "optional", "name": "startMonth", "ref": null, "restriction": {"maxInclusive": 12, "minInclusive": 1, "totalDigits": 2}}, {"use": "optional", "name": "endYear", "ref": null, "restriction": {"maxInclusive": 2200, "minInclusive": 1400, "totalDigits": 4}}, {"use": "optional", "name": "startDay", "ref": null, "restriction": {"maxInclusive": 31, "minInclusive": 1, "totalDigits": 2}}, {"use": "optional", "name": "endDay", "ref": null, "restriction": {"maxInclusive": 31, "minInclusive": 1, "totalDigits": 2}}, {"use": "optional", "name": "endMonth", "ref": null, "restriction": {"maxInclusive": 12, "minInclusive": 1, "totalDigits": 2}}, {"use": "optional", "name": "xml:lang", "ref": "xml:lang"}, {"use": "optional", "name": "startYear", "ref": null, "restriction": {"maxInclusive": 2200, "minInclusive": 1400, "totalDigits": 4}}]}}, "jpcoar:conferenceVenue": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:conferencePlace": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:conferenceCountry": {"type": {"maxOccurs": 1, "minOccurs": 0, "restriction": {"patterns": ["^[A-Z]{3}$"]}}}}, "jpcoar:file": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}, "jpcoar:URI": {"type": {"maxOccurs": 1, "minOccurs": 0, "attributes": [{"use": "optional", "name": "label", "ref": null}, {"use": "optional", "name": "objectType", "ref": null, "restriction": {"enumeration": ["abstract", "dataset", "fulltext", "software", "summary", "thumbnail", "other"]}}]}}, "jpcoar:mimeType": {"type": {"maxOccurs": 1, "minOccurs": 0}}, "jpcoar:extent": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}}, "datacite:date": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "dateType", "ref": null, "restriction": {"enumeration": ["Accepted", "Available", "Collected", "Copyrighted", "Created", "Issued", "Submitted", "Updated", "Valid"]}}]}}, "datacite:version": {"type": {"maxOccurs": 1, "minOccurs": 0}}}, "custom:system_file": {"type": {"minOccurs": 0, "maxOccurs": "unbounded"}, "jpcoar:URI": {"type": {"minOccurs": 0, "maxOccurs": 1, "attributes": [{"name": "objectType", "ref": null, "use": "optional", "restriction": {"enumeration": ["abstract", "summary", "fulltext", "thumbnail", "other"]}}, {"name": "label", "ref": null, "use": "optional"}]}}, "jpcoar:mimeType": {"type": {"minOccurs": 0, "maxOccurs": 1}}, "jpcoar:extent": {"type": {"minOccurs": 0, "maxOccurs": "unbounded"}}, "datacite:date": {"type": {"minOccurs": 1, "maxOccurs": "unbounded", "attributes": [{"name": "dateType", "ref": null, "use": "required", "restriction": {"enumeration": ["Accepted", "Available", "Collected", "Copyrighted", "Created", "Issued", "Submitted", "Updated", "Valid"]}}]}}, "datacite:version": {"type": {"minOccurs": 0, "maxOccurs": 1}}}}'
    namespaces = {
        "": "https://github.com/JPCOAR/schema/blob/master/1.0/",
        "dc": "http://purl.org/dc/elements/1.1/",
        "xs": "http://www.w3.org/2001/XMLSchema",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "xml": "http://www.w3.org/XML/1998/namespace",
        "dcndl": "http://ndl.go.jp/dcndl/terms/",
        "oaire": "http://namespace.openaire.eu/schema/oaire/",
        "jpcoar": "https://github.com/JPCOAR/schema/blob/master/1.0/",
        "dcterms": "http://purl.org/dc/terms/",
        "datacite": "https://schema.datacite.org/meta/kernel-4/",
        "rioxxterms": "http://www.rioxx.net/schema/v2.0/rioxxterms/",
    }
    schema_location = "https://github.com/JPCOAR/schema/blob/master/1.0/jpcoar_scm.xsd"
    oaischema = OAIServerSchema(
        id=uuid.uuid4(),
        schema_name=schema_name,
        form_data=form_data,
        xsd=xsd,
        namespaces=namespaces,
        schema_location=schema_location,
        isvalid=True,
        is_mapping=False,
        isfixed=False,
        version_id=1,
    )
    with db.session.begin_nested():
        db.session.add(oaischema)


@pytest.fixture()
def db_userprofile(app, db):
    profiles = {}
    with db.session.begin_nested():
        users = User.query.all()
        for user in users:
            p = UserProfile()
            p.user_id = user.id
            p._username = (user.email).split("@")[0]
            profiles[user.email] = p
            db.session.add(p)
    return profiles

@pytest.fixture()
def db_itemtype2(app, db):
    item_type_name = ItemTypeName(id=2,
        name="テストアイテムタイプ2", has_site_license=True, is_active=True
    )
    item_type_schema = dict()
    with open("tests/data/itemtype1_schema.json", "r") as f:
        item_type_schema = json.load(f)

    item_type_form = dict()
    with open("tests/data/itemtype1_form.json", "r") as f:
        item_type_form = json.load(f)

    item_type_render = dict()
    with open("tests/data/itemtype1_render.json", "r") as f:
        item_type_render = json.load(f)

    item_type_mapping = dict()
    with open("tests/data/itemtype1_mapping.json", "r") as f:
        item_type_mapping = json.load(f)

    item_type = ItemType(id=2,
        name_id=2,
        harvesting_type=True,
        schema=item_type_schema,
        form=item_type_form,
        render=item_type_render,
        tag=1,
        version_id=1,
        is_deleted=False,
    )

    item_type_mapping = ItemTypeMapping(id=2,item_type_id=2, mapping=item_type_mapping)

    with db.session.begin_nested():
        db.session.add(item_type_name)
        db.session.add(item_type)
        db.session.add(item_type_mapping)

    return {"item_type_name": item_type_name, "item_type": item_type, "item_type_mapping":item_type_mapping}

@pytest.fixture()
def db_itemtype3(app, db):
    item_type_name = ItemTypeName(id=3,
        name="テストアイテムタイプ3", has_site_license=True, is_active=True
    )
    item_type_schema = dict()
    with open("tests/data/itemtype2_schema.json", "r") as f:
        item_type_schema = json.load(f)

    item_type_form = dict()
    with open("tests/data/itemtype2_form.json", "r") as f:
        item_type_form = json.load(f)

    item_type_render = dict()
    with open("tests/data/itemtype2_render.json", "r") as f:
        item_type_render = json.load(f)

    item_type_mapping = dict()
    with open("tests/data/itemtype2_mapping.json", "r") as f:
        item_type_mapping = json.load(f)

    item_type = ItemType(
        id=3,
        name_id=3,
        harvesting_type=True,
        schema=item_type_schema,
        form=item_type_form,
        render=item_type_render,
        tag=1,
        version_id=1,
        is_deleted=False,
    )

    item_type_mapping = ItemTypeMapping(id=3,item_type_id=3, mapping=item_type_mapping)

    with db.session.begin_nested():
        db.session.add(item_type_name)
        db.session.add(item_type)
        db.session.add(item_type_mapping)

    return {"item_type_name": item_type_name, "item_type": item_type, "item_type_mapping":item_type_mapping}

@pytest.fixture()
def db_itemtype4(app, db):
    item_type_name = ItemTypeName(id=4,
        name="テストアイテムタイプ4", has_site_license=True, is_active=True
    )
    item_type_schema = dict()
    with open("tests/data/itemtype3_schema.json", "r") as f:
        item_type_schema = json.load(f)

    item_type_form = dict()
    with open("tests/data/itemtype3_form.json", "r") as f:
        item_type_form = json.load(f)

    item_type_render = dict()
    with open("tests/data/itemtype3_render.json", "r") as f:
        item_type_render = json.load(f)

    item_type_mapping = dict()
    with open("tests/data/itemtype3_mapping.json", "r") as f:
        item_type_mapping = json.load(f)

    item_type = ItemType(
        id=4,
        name_id=4,
        harvesting_type=True,
        schema=item_type_schema,
        form=item_type_form,
        render=item_type_render,
        tag=1,
        version_id=1,
        is_deleted=False,
    )

    item_type_mapping = ItemTypeMapping(id=4,item_type_id=4, mapping=item_type_mapping)

    with db.session.begin_nested():
        db.session.add(item_type_name)
        db.session.add(item_type)
        db.session.add(item_type_mapping)

    return {"item_type_name": item_type_name, "item_type": item_type, "item_type_mapping":item_type_mapping}

@pytest.fixture()
def db_itemtype5(app, db):
    item_type_name = ItemTypeName(id=5,
        name="テストアイテムタイプ5", has_site_license=True, is_active=True
    )
    item_type_schema = dict()
    with open("tests/data/itemtype4_schema.json", "r") as f:
        item_type_schema = json.load(f)

    item_type_form = dict()
    with open("tests/data/itemtype4_form.json", "r") as f:
        item_type_form = json.load(f)

    item_type_render = dict()
    with open("tests/data/itemtype4_render.json", "r") as f:
        item_type_render = json.load(f)

    item_type_mapping = dict()
    with open("tests/data/itemtype4_mapping.json", "r") as f:
        item_type_mapping = json.load(f)

    item_type = ItemType(
        id=5,
        name_id=5,
        harvesting_type=True,
        schema=item_type_schema,
        form=item_type_form,
        render=item_type_render,
        tag=1,
        version_id=1,
        is_deleted=False,
    )

    item_type_mapping = ItemTypeMapping(id=5,item_type_id=5, mapping=item_type_mapping)

    with db.session.begin_nested():
        db.session.add(item_type_name)
        db.session.add(item_type)
        db.session.add(item_type_mapping)

    return {"item_type_name": item_type_name, "item_type": item_type, "item_type_mapping":item_type_mapping}


@pytest.fixture()
def db_itemtype6(app):
    item_type_name = ItemTypeName(id=6, name="テストアイテムタイプ6", has_site_license=True, is_active=True)

    item_type_schema = dict()
    with open("tests/data/itemtype5_schema.json", "r") as f:
        item_type_schema = json.load(f)

    item_type_form = dict()
    with open("tests/data/itemtype5_form.json", "r") as f:
        item_type_form = json.load(f)

    item_type_render = dict()
    with open("tests/data/itemtype5_render.json", "r") as f:
        item_type_render = json.load(f)

    item_type_mapping = dict()
    with open("tests/data/itemtype5_mapping.json", "r") as f:
        item_type_mapping = json.load(f)

    item_type = ItemType(
        id=6,
        name_id=6,
        harvesting_type=True,
        schema=item_type_schema,
        form=item_type_form,
        render=item_type_render,
        tag=1,
        version_id=1,
        is_deleted=False,
    )

    item_type_mapping = ItemTypeMapping(id=6, item_type_id=6, mapping=item_type_mapping)

    return {"item_type_name": item_type_name, "item_type": item_type, "item_type_mapping": item_type_mapping}


@pytest.fixture()
def db_itemtype(app, db):
    item_type_name = ItemTypeName(id=1,
        name="テストアイテムタイプ", has_site_license=True, is_active=True
    )
    item_type_schema = dict()
    with open("tests/data/itemtype_schema.json", "r") as f:
        item_type_schema = json.load(f)

    item_type_form = dict()
    with open("tests/data/itemtype_form.json", "r") as f:
        item_type_form = json.load(f)

    item_type_render = dict()
    with open("tests/data/itemtype_render.json", "r") as f:
        item_type_render = json.load(f)

    item_type_mapping = dict()
    with open("tests/data/itemtype_mapping.json", "r") as f:
        item_type_mapping = json.load(f)

    item_type = ItemType(
        id=1,
        name_id=1,
        harvesting_type=True,
        schema=item_type_schema,
        form=item_type_form,
        render=item_type_render,
        tag=1,
        version_id=1,
        is_deleted=False,
    )

    item_type_mapping = ItemTypeMapping(id=1,item_type_id=1, mapping=item_type_mapping)

    with db.session.begin_nested():
        db.session.add(item_type_name)
        db.session.add(item_type)
        db.session.add(item_type_mapping)

    return {"item_type_name": item_type_name, "item_type": item_type, "item_type_mapping":item_type_mapping}


@pytest.fixture()
def db_records(db,instance_path,users):
    with db.session.begin_nested():
        Location.query.delete()
        loc = Location(name="local", uri=instance_path, default=True)
        db.session.add(loc)
    db.session.commit()

    record_data = json_data("data/test_records.json")
    item_data = json_data("data/test_items.json")
    record_num = len(record_data)
    result = []
    with db.session.begin_nested():
        for d in range(record_num):
            result.append(create_record(record_data[d], item_data[d]))
    db.session.commit()

    index_metadata = {
            'id': 1,
            'parent': 0,
            'value': 'Index(public_state = True,harvest_public_state = True)'
        }
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        ret = Indexes.create(0, index_metadata)
        index = Index.get_index_by_id(1)
        index.public_state = True
        index.harvest_public_state = True
        index.item_custom_sort = {"1":1}
    
    index_metadata = {
            'id': 2,
            'parent': 0,
            'value': 'Index(public_state = True,harvest_public_state = False)',
        }
    
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        Indexes.create(0, index_metadata)
        index = Index.get_index_by_id(2)
        index.public_state = True
        index.harvest_public_state = False
        index.item_custom_sort = {"1":1}
    
    index_metadata = {
            'id': 3,
            'parent': 0,
            'value': 'Index(public_state = False,harvest_public_state = True)',
    }
    
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        Indexes.create(0, index_metadata)
        index = Index.get_index_by_id(3)
        index.public_state = False
        index.harvest_public_state = True
        index.item_custom_sort = {"1":1}
    
    index_metadata = {
            'id': 4,
            'parent': 0,
            'value': 'Index(public_state = False,harvest_public_state = False)',
    }
    
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        Indexes.create(0, index_metadata)
        index = Index.get_index_by_id(4)
        index.public_state = False
        index.harvest_public_state = False
        index.item_custom_sort = {"1":1}

 
    yield result

@pytest.fixture()
def db_records2(db,instance_path,users):
    record_data = json_data("data/test_records2.json")
    item_data = json_data("data/test_items2.json")
    record_num = len(record_data)
    result = []
    with db.session.begin_nested():
        for d in range(record_num):
            result.append(create_record(record_data[d], item_data[d]))
    db.session.commit()
 
    yield result

@pytest.fixture()
def db_records_file(app,db,instance_path,users):
    index_metadata = {
        'id': 1,
        'parent': 0,
        'value': 'Index(public_state = True,harvest_public_state = True)'
    }
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        ret = Indexes.create(0, index_metadata)
        index = Index.get_index_by_id(1)
        index.public_state = True
        index.harvest_public_state = True
    with db.session.begin_nested():
        Location.query.delete()
        loc = Location(name="local", uri=instance_path, default=True)
        db.session.add(loc)
    db.session.commit()
    record_data = json_data("data/record_file/record_metadata.json")
    item_data = json_data("data/record_file/item_metadata.json")
    with db.session.begin_nested():
        depid, recid,parent,doi,record, item=create_record(record_data, item_data)
    db.session.commit()
    
    return depid, recid,parent,doi,record, item

@pytest.fixture()
def db_workflow(app, db, db_itemtype, users):
    action_datas = dict()
    with open("tests/data/actions.json", "r") as f:
        action_datas = json.load(f)
    actions_db = list()
    with db.session.begin_nested():
        for data in action_datas:
            actions_db.append(Action(**data))
        db.session.add_all(actions_db)

    actionstatus_datas = dict()
    with open("tests/data/action_status.json") as f:
        actionstatus_datas = json.load(f)
    actionstatus_db = list()
    with db.session.begin_nested():
        for data in actionstatus_datas:
            actionstatus_db.append(ActionStatus(**data))
        db.session.add_all(actionstatus_db)

    flow_id = uuid.uuid4()
    flow_define = FlowDefine(
        flow_id=flow_id, flow_name="Registration Flow", flow_user=1, flow_status="A"
    )
    flow_action1 = FlowAction(
        status="N",
        flow_id=flow_id,
        action_id=1,
        action_version="1.0.0",
        action_order=1,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={},
    )
    flow_action2 = FlowAction(
        status="N",
        flow_id=flow_id,
        action_id=3,
        action_version="1.0.0",
        action_order=2,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={},
    )
    flow_action3 = FlowAction(
        status="N",
        flow_id=flow_id,
        action_id=5,
        action_version="1.0.0",
        action_order=3,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={},
    )

    workflow = WorkFlow(
        flows_id=uuid.uuid4(),
        flows_name="test workflow1",
        itemtype_id=1,
        index_tree_id=None,
        flow_id=1,
        is_deleted=False,
        open_restricted=False,
        location_id=None,
        is_gakuninrdm=False,
    )
    activity = Activity(
        activity_id="A-00000000-00000",
        workflow_id=1,
        flow_id=flow_define.id,
        action_id=1,
        activity_login_user=1,
        activity_update_user=1,
        activity_start=datetime.strptime(
            "2022/04/14 3:01:53.931", "%Y/%m/%d %H:%M:%S.%f"
        ),
        activity_community_id=3,
        activity_confirm_term_of_use=True,
        title="test",
        shared_user_id=-1,
        extra_info={},
        action_order=6,
    )

    with db.session.begin_nested():
        db.session.add(flow_define)
        db.session.add(flow_action1)
        db.session.add(flow_action2)
        db.session.add(flow_action3)
        db.session.add(workflow)
        db.session.add(activity)

    return {
        "flow_define": flow_define,
        "workflow": workflow,
        "activity": activity,
        "flow_action1": flow_action1,
        "flow_action2": flow_action2,
        "flow_action3": flow_action3,
    }


@pytest.fixture()
def db_sessionlifetime(app, db):
    session_lifetime = SessionLifetime(lifetime=60, is_delete=False)
    with db.session.begin_nested():
        db.session.add(session_lifetime)


@pytest.fixture()
def db_activity(db, db_records, db_itemtype, db_workflow, users):
    user = users[3]["obj"]
    depid, recid, parent, doi, record, item = db_records[0]
    rec_uuid = uuid.uuid4()
    draft = PersistentIdentifier.create(
        "recid",
        "{}.0".format((parent.pid_value).split(":")[1]),
        object_type="rec",
        object_uuid=rec_uuid,
        status=PIDStatus.REGISTERED,
    )
    rel = PIDRelation.create(parent, draft, 2)
    flow_define = db_workflow["flow_define"]
    workflow = db_workflow["workflow"]
    activity = Activity(
        activity_id="A-00000000-00001",
        workflow_id=workflow.id,
        flow_id=flow_define.id,
        action_id=2,
        activity_login_user=user.id,
        action_status=ActionStatusPolicy.ACTION_DOING,
        activity_update_user=user.id,
        item_id=draft.object_uuid,
        activity_start=datetime.strptime(
            "2022/04/14 3:01:53.931", "%Y/%m/%d %H:%M:%S.%f"
        ),
        activity_confirm_term_of_use=True,
        title="test",
        shared_user_id=-1,
        extra_info={},
        action_order=6,
    )
    with db.session.begin_nested():
        db.session.add(activity)
        db.session.add(rel)

    return {"activity": activity, "recid": recid}


@pytest.fixture()
def db_author(db):
    prefix1 = AuthorsPrefixSettings(name="WEKO",scheme="WEKO",url="")
    prefix2 = AuthorsPrefixSettings(name="ORCID",scheme="ORCID",url="https://orcid.org/##")
    prefix3 = AuthorsPrefixSettings(name="CiNii",scheme="CiNii",url="https://ci.nii.ac.jp/author/##")
    prefix4 = AuthorsPrefixSettings(name="KAKEN2",scheme="KAKEN2",url="https://nrid.nii.ac.jp/nrid/##")
    prefix5 = AuthorsPrefixSettings(name="ROR",scheme="ROR",url="https://ror.org/##")

    affiliation_prefix1 =AuthorsAffiliationSettings(name="ISNI",scheme="ISNI",url="http://www.isni.org/isni/##")
    affiliation_prefix2 =AuthorsAffiliationSettings(name="GRID",scheme="GRID",url="https://www.grid.ac/institutes/#")
    affiliation_prefix3 =AuthorsAffiliationSettings(name="Ringgold",scheme="Ringgold",url="")
    affiliation_prefix4 =AuthorsAffiliationSettings(name="kakenhi",scheme="kakenhi",url="")

    author_json = {"affiliationInfo": [{"affiliationNameInfo": [{"affiliationName": "xxx", "affiliationNameLang": "ja", "affiliationNameShowFlg": "true"}], "identifierInfo": [{"affiliationId": "xxx", "affiliationIdType": "1", "identifierShowFlg": "true"}]}], "authorIdInfo": [{"authorId": "1", "authorIdShowFlg": "true", "idType": "1"}, {"authorId": "xxxx", "authorIdShowFlg": "true", "idType": "2"}], "authorNameInfo": [{"familyName": "LAST", "firstName": "FIRST", "fullName": "LAST FIRST", "language": "en", "nameFormat": "familyNmAndNm", "nameShowFlg": "true"}], "emailInfo": [{"email": "hoge@hoge"}], "gather_flg": 0, "id": {"_id": "sBXZ7oIBMJ49WnxY8sLQ", "_index": "tenant1-authors-author-v1.0.0", "_primary_term": 4, "_seq_no": 0, "_shards": {"failed": 0, "successful": 1, "total": 2}, "_type": "author-v1.0.0", "_version": 1, "result": "created"}, "is_deleted": "false", "pk_id": "1"}
    author1 = Authors(json=author_json)


    with db.session.begin_nested():
        db.session.add(prefix1)
        db.session.add(prefix2)
        db.session.add(prefix3)
        db.session.add(prefix4)
        db.session.add(prefix5)
        db.session.add(affiliation_prefix1)
        db.session.add(affiliation_prefix2)
        db.session.add(affiliation_prefix3)
        db.session.add(affiliation_prefix4)
        db.session.add(author1)
    
    return {"author_prefix":[prefix1,prefix2,prefix3,prefix4,prefix5],"affiliation_prefix":[affiliation_prefix1,affiliation_prefix2,affiliation_prefix3,affiliation_prefix4],"author":[author1]}

@pytest.fixture()
def db_ranking(db):
    ranking_settings = RankingSettings(is_show=True,new_item_period=12,statistical_period=365,display_rank=10,rankings={"new_items": True, "most_reviewed_items": True, "most_downloaded_items": True, "most_searched_keywords": True, "created_most_items_user": True})
    with db.session.begin_nested():
        db.session.add(ranking_settings)

    return {"settings":ranking_settings}

# @pytest.fixture(autouse=True)
# def slow_down_tests():
#     yield
#     time.sleep(1)


# @pytest.fixture()
# def queue(app):
#     """Get queue object for testing bulk operations."""
#     queue = app.config["INDEXER_MQ_QUEUE"]

#     with app.app_context():
#         with establish_connection() as c:
#             q = queue(c)
#             q.declare()
#             q.purge()

#     return queue

@pytest.fixture()
def communities(app, db, users):
    """Create example communities."""

    comm0 = Community.create(
        community_id="comm1",
        role_id=4,
        root_node_id=1,
        id_user = 4,
    )
    db.session.add(comm0)

    return comm0