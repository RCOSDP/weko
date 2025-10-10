# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""

from __future__ import absolute_import, print_function

import shutil
import json
import subprocess
import tempfile
import os
from os.path import join, dirname
from io import BytesIO
import uuid
from zipfile import ZipFile, ZIP_DEFLATED
from datetime import datetime, timedelta

from invenio_theme import InvenioTheme
import pytest
from flask import Flask
from flask_babelex import Babel
from flask_mail import Mail
from flask_menu import Menu
from sqlalchemy_utils.functions import create_database, database_exists
from werkzeug.local import LocalProxy

from invenio_access import InvenioAccess
from invenio_access.models import ActionUsers,ActionRoles
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import User, Role
from invenio_accounts.utils import jwt_create_token
from invenio_accounts.testutils import create_test_user
from invenio_admin import InvenioAdmin
from invenio_assets import InvenioAssets
from invenio_cache import InvenioCache
from invenio_communities.ext import InvenioCommunities
from invenio_communities.models import Community
from invenio_communities.views.ui import blueprint as invenio_communities_blueprint
from invenio_deposit import InvenioDeposit
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.models import Bucket, Location
from invenio_pidrelations import InvenioPIDRelations
from invenio_pidstore import InvenioPIDStore
from invenio_i18n import InvenioI18N
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_oauth2server import InvenioOAuth2Server
from invenio_oauth2server.models import Client, Token
from invenio_records import InvenioRecords
from invenio_records_ui import InvenioRecordsUI
from invenio_search import InvenioSearch, current_search_client

from weko_accounts import WekoAccounts
from weko_admin import WekoAdmin
from weko_admin.models import AdminSettings, Identifier,SessionLifetime
from weko_authors import WekoAuthors
from weko_deposit import WekoDeposit
from weko_deposit.api import WekoIndexer
from weko_index_tree.ext import WekoIndexTree
from weko_index_tree.models import Index
from weko_items_ui.ext import WekoItemsUI
from weko_records.models import ItemTypeName, ItemType,ItemTypeMapping, ItemTypeJsonldMapping
from weko_schema_ui.ext import WekoSchemaUI
from weko_search_ui import WekoSearchUI
from weko_swordserver.models import SwordClientModel
from weko_theme.ext import WekoTheme
from weko_workflow import WekoWorkflow
from weko_workflow.models import Action, ActionStatus, FlowAction, FlowDefine, WorkFlow
from weko_swordserver import WekoSWORDServer
from weko_swordserver.views import blueprint as weko_swordserver_blueprint
from weko_logging.audit import WekoLoggingUserActivity

from .helpers import json_data, create_record

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
        static_folder=join(instance_path, "static")
    )
    app_.config.update(
        TESTING=True,
        SECRET_KEY='testing_key',
        SERVER_NAME='TEST_SERVER.localdomain',
        SQLALCHEMY_DATABASE_URI=os.getenv(
            'SQLALCHEMY_DATABASE_URI',
            'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        OAUTH2_CACHE_TYPE='simple',
        OAUTHLIB_INSECURE_TRANSPORT=True,
        SEARCH_ELASTIC_HOSTS=os.environ.get("SEARCH_ELASTIC_HOSTS", "elasticsearch"),
        CACHE_TYPE="redis",
        CACHE_REDIS_URL="redis://redis:6379/0",
        CACHE_REDIS_DB="0",
        CACHE_REDIS_HOST="redis",
        REDIS_PORT="6379",
        WEKO_BUCKET_QUOTA_SIZE = 50 * 1024 * 1024 * 1024,
        WEKO_MAX_FILE_SIZE=50 * 1024 * 1024 * 1024,
        WEKO_MAX_FILE_SIZE_FOR_ES = 1 * 1024 * 1024,
        DEPOSIT_DEFAULT_JSONSCHEMA = 'deposits/deposit-v1.0.0.json',
        SEARCH_UI_SEARCH_INDEX="test-weko",
        INDEXER_DEFAULT_DOCTYPE="item-v1.0.0",
        INDEXER_FILE_DOC_TYPE="content",
        INDEXER_DEFAULT_INDEX="{}-weko-item-v1.0.0".format("test"),
        WEKO_SCHEMA_JPCOAR_V1_SCHEMA_NAME = 'jpcoar_v1_mapping',
        WEKO_SCHEMA_JPCOAR_V2_SCHEMA_NAME='jpcoar_mapping',
        WEKO_SCHEMA_DDI_SCHEMA_NAME='ddi_mapping',
        WEKO_SCHEMA_JPCOAR_V2_NAMEIDSCHEME_REPLACE = {'e-Rad':'e-Rad_Researcher'},
        WEKO_SCHEMA_JPCOAR_V2_RESOURCE_TYPE_REPLACE={
            'periodical':'journal',
            'interview':'other',
            'internal report':'other',
            'report part':'other',
        },
        THEME_SITEURL="https://localhost",
        WEKO_ITEMS_UI_INDEX_PATH_SPLIT="///",
        WEKO_MIMETYPE_WHITELIST_FOR_ES = [
            'text/plain',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/pdf',
        ]
    )
    Babel(app_)
    Mail(app_)
    # Menu(app_)
    InvenioDB(app_)
    InvenioI18N(app_)
    InvenioAccess(app_)
    InvenioAccounts(app_)
    InvenioAdmin(app_)
    InvenioAssets(app_)
    InvenioCache(app_)
    InvenioDeposit(app_)
    InvenioFilesREST(app_)
    InvenioJSONSchemas(app_)
    InvenioOAuth2Server(app_)
    InvenioRecords(app_)
    InvenioSearch(app_)
    InvenioTheme(app_)
    InvenioPIDRelations(app_)
    InvenioPIDStore(app_)
    WekoAccounts(app_)
    WekoSearchUI(app_)
    WekoWorkflow(app_)
    WekoAdmin(app_)
    WekoAuthors(app_)
    WekoDeposit(app_)
    WekoIndexTree(app_)
    WekoItemsUI(app_)
    WekoSchemaUI(app_)
    WekoTheme(app_)
    WekoLoggingUserActivity(app_)

    # InvenioCommunities(app_)
    app_.register_blueprint(invenio_communities_blueprint)

    current_assets = LocalProxy(lambda: app_.extensions["invenio-assets"])
    current_assets.collect.collect()

    yield app_

@pytest.yield_fixture()
def app(base_app):
    """Flask application"""
    WekoSWORDServer(base_app)
    base_app.register_blueprint(weko_swordserver_blueprint)
    with base_app.app_context():
        yield base_app

@pytest.yield_fixture()
def client(app):
    with app.test_client() as client:
        yield client

@pytest.yield_fixture()
def esindex(app):
    app.config.update(
        WEKO_AUTHORS_ES_INDEX_NAME="test-weko-author"
    )
    current_search_client.indices.delete(index="test-*")
    mapping_author = json_data("data/author-v1.0.0.json")
    try:
        current_search_client.indices.create(
            app.config["WEKO_AUTHORS_ES_INDEX_NAME"], body=mapping_author
        )
        current_search_client.indices.put_alias(
            index=app.config["WEKO_AUTHORS_ES_INDEX_NAME"],name="test-weko-authors"
        )
    except:
        current_search_client.indices.create("test-weko-author", body=mapping_author)
        current_search_client.indices.put_alias(
            index="test-weko-author", name="test-weko-authors"
        )

    mapping_item = json_data("data/item-v1.0.0.json")
    try:
        current_search_client.indices.create(
            app.config["INDEXER_DEFAULT_INDEX"], body=mapping_item
        )
        current_search_client.indices.put_alias(
            index=app.config["INDEXER_DEFAULT_INDEX"], name="test-weko"
        )
    except:
        current_search_client.indices.create("test-weko-item-v1.0.0", body=mapping_item)
        current_search_client.indices.put_alias(
            index="test-weko-item-v1.0.0", name="test-weko"
        )

    try:
        yield current_search_client
    finally:
        current_search_client.indices.delete(index="test-*")


@pytest.yield_fixture
def db(app):
    """Database fixture."""
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()
    # drop_database(str(db_.engine.url))

@pytest.fixture
def tokens(app,users,db):
    scopes = [
        "deposit:write deposit:actions item:create",
        "deposit:write deposit:actions item:create user:activity",
        "deposit:write user:activity",
        ""
    ]
    tokens = []

    for i, scope in enumerate(scopes):
        user = users[i]
        user_id = str(user["id"])

        test_client = Client(
            client_id=f"dev{user_id}",
            client_secret=f"dev{user_id}",
            name="Test name",
            description="test description",
            is_confidential=False,
            user_id=user_id,
            _default_scopes="deposit:write"
        )
        test_token = Token(
            client=test_client,
            user_id=user_id,
            token_type="bearer",
            access_token=jwt_create_token(user_id=user_id),
            expires=datetime.now() + timedelta(hours=10),
            is_personal=False,
            is_internal=False,
            _scopes=scope
        )

        db.session.add(test_client)
        db.session.add(test_token)
        tokens.append({"token":test_token, "client":test_client, "scope":scope})

    db.session.commit()

    return tokens


@pytest.fixture()
def personal_token(app, users, db):
    tokens = []

    for i, user in enumerate(users):
        user_id = str(user["id"])
        test_client = Client(
            client_id=f"dev{user_id}",
            client_secret=f"dev{user_id}",
            name="Test name",
            description="test description",
            user_id=user_id,
            is_internal=True,
        )
        test_token = Token(
            client=test_client,
            user_id=user_id,
            token_type="bearer",
            access_token=jwt_create_token(user_id=user_id),
            expires=datetime.now() + timedelta(hours=10),
            is_personal=True,
            is_internal=True,
        )

        db.session.add(test_client)
        db.session.add(test_token)
        tokens.append({"token":test_token, "client":test_client})

    db.session.commit()

    return tokens


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
    db.session.commit()
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
def item_type(app, db):

    item_type_name = ItemTypeName(id=1,
        name="デフォルトアイテムタイプ（フル）", has_site_license=True, is_active=True
    )

    item_type = ItemType(
        id=1,
        name_id=1,
        harvesting_type=True,
        schema=json_data("data/item_type/schema_1.json"),
        form=json_data("data/item_type/form_1.json"),
        render=json_data("data/item_type/render_1.json"),
        tag=1,
        version_id=1,
        is_deleted=False,
    )
    item_type_mapping = ItemTypeMapping(
        id=1,
        item_type_id=1,
        mapping=json_data("data/item_type/mapping_1.json")
    )

    item_type_name_2 = ItemTypeName(id=2,
        name="デフォルトアイテムタイプ（SWORD）", has_site_license=True, is_active=True
    )

    item_type_2 = ItemType(
        id=2,
        name_id=2,
        harvesting_type=True,
        schema=json_data("data/item_type/schema_2.json"),
        form=json_data("data/item_type/form_2.json"),
        render=json_data("data/item_type/render_2.json"),
        tag=2,
        version_id=1,
        is_deleted=False,
    )
    item_type_mapping_2 = ItemTypeMapping(
        id=2,
        item_type_id=2,
        mapping=json_data("data/item_type/mapping_2.json")
    )

    with db.session.begin_nested():
        db.session.add(item_type_name)
        db.session.add(item_type)
        db.session.add(item_type_mapping)
        db.session.add(item_type_name_2)
        db.session.add(item_type_2)
        db.session.add(item_type_mapping_2)

    db.session.commit()

    return [
        {"item_type_name": item_type_name, "item_type": item_type, "item_type_mapping":item_type_mapping},
        {"item_type_name": item_type_name_2, "item_type": item_type_2, "item_type_mapping":None}
    ]

@pytest.fixture()
def doi_identifier(app, db):
    identifier = Identifier(
        id=1,
        repository="Root Index",
        jalc_flag=True,
        jalc_crossref_flag=True,
        jalc_datacite_flag=True,
        ndl_jalc_flag=True,
        jalc_doi="1234",
        jalc_crossref_doi="2345",
        jalc_datacite_doi="3456",
        ndl_jalc_doi="4567",
        created_userId=1,
        created_date=datetime.now(),
        updated_userId=1,
        updated_date=datetime.now()
    )
    db.session.add(identifier)
    db.session.commit()
    return identifier


@pytest.fixture()
def index(app, db):
    index_1 = Index(
        id=1234567891011,
        parent=0,
        position=11,
        index_name="test_index",
        index_name_english="test_index",
        index_link_name_english="New Index",
        index_link_enabled=False,
        more_check=False,
        display_no=5,
        harvest_public_state=True,
        image_name="",
        public_state=False,
    )
    index_2 = Index(
        id=1623632832836,
        parent=0,
        position=12,
        index_name="test_index_ld",
        index_name_english="test_index_ld",
        index_link_name_english="New Index LD",
        index_link_enabled=False,
        more_check=False,
        display_no=5,
        harvest_public_state=True,
        image_name="",
        public_state=False,
    )
    db.session.add(index_1)
    db.session.add(index_2)
    db.session.commit()

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
def records(db,location):
    record_data = json_data("data/records/test_records.json")
    item_data = json_data("data/records/test_items.json")
    record_num = len(record_data)
    result = []
    for d in range(record_num):
        result.append(create_record(record_data[d], item_data[d]))
        db.session.commit()
    return result

@pytest.fixture()
def admin_settings(db):
    settings = []
    settings.append(AdminSettings(id=1,name='items_display_settings',settings={"items_display_email": False, "items_search_author": "name", "item_display_open_date": False}))
    settings.append(AdminSettings(id=2,name='storage_check_settings',settings={"day": 0, "cycle": "weekly", "threshold_rate": 80}))
    settings.append(AdminSettings(id=3,name='site_license_mail_settings',settings={"auto_send_flag": False}))
    settings.append(AdminSettings(id=4,name='default_properties_settings',settings={"show_flag": True}))
    settings.append(AdminSettings(id=5,name='item_export_settings',settings={"allow_item_exporting": True, "enable_contents_exporting": True}))
    settings.append(AdminSettings(id=6,name="restricted_access",settings={"content_file_download": {"expiration_date": 30,"expiration_date_unlimited_chk": False,"download_limit": 10,"download_limit_unlimited_chk": False,},"usage_report_workflow_access": {"expiration_date_access": 500,"expiration_date_access_unlimited_chk": False,},"terms_and_conditions": []}))
    settings.append(AdminSettings(id=7,name="display_stats_settings",settings={"display_stats":False}))
    settings.append(AdminSettings(id=8,name='convert_pdf_settings',settings={"path":"/tmp/file","pdf_ttl":1800}))
    settings.append(AdminSettings(id=9,name="elastic_reindex_settings",settings={"has_errored": False}))
    settings.append(AdminSettings(id=10,name="sword_api_setting",settings={"TSV/CSV": {"item_type": "15", "registration_type": "Direct", "duplicate_check": False}, "XML": {"workflow": "1", "item_type": "15", "registration_type": "Workflow", "duplicate_check": False}}))
    db.session.add_all(settings)
    db.session.commit()
    return settings


@pytest.fixture()
def bucket(app, db, location):
    bucket = Bucket.create()
    return bucket

@pytest.fixture()
def es_records(app, esindex, records):
    for recid, depid, record, item, parent, doi, deposit in records:
        esindex.index(
            index=app.config["INDEXER_DEFAULT_INDEX"],
            doc_type="item-v1.0.0",
            id=record.id,
            body=record,
            refresh="true"
        )
    return records

@pytest.fixture()
def sessionlifetime(app, db):
    session_lifetime = SessionLifetime(lifetime=60, is_delete=False)
    with db.session.begin_nested():
        db.session.add(session_lifetime)

@pytest.fixture()
def make_zip():
    def factory():
        fp = BytesIO()
        with ZipFile(fp, 'w', compression=ZIP_DEFLATED) as new_zip:
            for dir, subdirs, files in os.walk("tests/data/zip_data/data"):
                new_zip.write(dir,dir.split("/")[-1])
                for file in files:
                    new_zip.write(os.path.join(dir, file),os.path.join(dir.split("/")[-1],file))
        fp.seek(0)
        return fp
    return factory

@pytest.fixture()
def make_crate():
    def factory():
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, "crate.zip")
        shutil.make_archive(zip_path.replace(".zip", ""), 'zip', "tests/data/zip_crate/")
        file_size = os.path.getsize(zip_path)
        with open(zip_path, 'rb') as f:
            fp = BytesIO(f.read())
        shutil.rmtree(temp_dir)
        fp.seek(0)
        return fp, file_size
    return factory

@pytest.fixture()
def make_crate2():
    def factory():
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, "crate.zip")
        shutil.make_archive(zip_path.replace(".zip", ""), 'zip', "tests/data/zip_crate2/")
        file_size = os.path.getsize(zip_path)
        with open(zip_path, 'rb') as f:
            fp = BytesIO(f.read())
        shutil.rmtree(temp_dir)
        fp.seek(0)
        return fp, file_size
    return factory

@pytest.fixture()
def install_node_module(app):
    current_path = os.getcwd()
    os.chdir(app.instance_path+'/static')
    assert subprocess.call('npm install bootstrap-sass@3.3.5 font-awesome@4.4.0 angular@1.4.9 angular-gettext angular-loading-bar@0.9.0 bootstrap-datepicker@1.7.1 almond@0.3.1 jquery@1.9.1 d3@3.5.17 invenio-search-js@1.3.1', shell=True) == 0
    os.chdir(current_path)

@pytest.yield_fixture()
def indexer(app):
    """Create a record indexer."""
    InvenioRecordsUI(app)
    WekoIndexer(app)
    # before_record_index.connect(record_indexer_receiver, sender=app)
    app.extensions['invenio-indexer'] = WekoIndexer()
    yield WekoIndexer()

@pytest.fixture()
def action_data(db):
    action_datas={}
    with open('tests/data/actions.json', 'r') as f:
        action_datas = json.load(f)
    actions_db = []
    with db.session.begin_nested():
        for data in action_datas:
            actions_db.append(Action(**data))
        db.session.add_all(actions_db)
    db.session.commit()

    actionstatus_datas = {}
    with open('tests/data/action_status.json') as f:
        actionstatus_datas = json.load(f)
    actionstatus_db = []
    with db.session.begin_nested():
        for data in actionstatus_datas:
            actionstatus_db.append(ActionStatus(**data))
        db.session.add_all(actionstatus_db)
    db.session.commit()
    return actions_db, actionstatus_db


@pytest.fixture()
def workflow(app, db, item_type, action_data, users):
    flow_define = FlowDefine(
        id=1,
        flow_id=uuid.uuid4(),
        flow_name="Registration Flow",
        flow_user=users[0]["obj"].id,
        flow_status="A"
    )

    flow_define_2 = FlowDefine(
        id=2,
        flow_id=uuid.uuid4(),
        flow_name='Registration Flow with approval',
        flow_user=users[0]["obj"].id,
        flow_status="A"
    )
    with db.session.begin_nested():
        db.session.add(flow_define)
        db.session.add(flow_define_2)
    db.session.commit()

    # setting flow action(start, item register, item link, end)
    flow_actions = []
    # start
    flow_actions.append(FlowAction(
        status='N',
        flow_id=flow_define.flow_id,
        action_id=1,
        action_version='1.0.0',
        action_order=1,
        action_condition='',
        action_status='A',
        action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
        send_mail_setting={}
    ))
    # item register
    flow_actions.append(FlowAction(
        status='N',
        flow_id=flow_define.flow_id,
        action_id=3,
        action_version='1.0.0',
        action_order=2,
        action_condition='',
        action_status='A',
        action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
        send_mail_setting={}
    ))
    # item link
    flow_actions.append(FlowAction(
        status='N',
        flow_id=flow_define.flow_id,
        action_id=5,
        action_version='1.0.0',
        action_order=3,
        action_condition='',
        action_status='A',
        action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
        send_mail_setting={}
    ))
    # end
    flow_actions.append(FlowAction(
        status='N',
        flow_id=flow_define.flow_id,
        action_id=2,
        action_version='1.0.0',
        action_order=4,
        action_condition='',
        action_status='A',
        action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
        send_mail_setting={}
    ))
    with db.session.begin_nested():
        db.session.add_all(flow_actions)
    db.session.commit()

    # setting flow action(start, item register, oa policy, item link, identifier grant, approval, end)
    flow_actions_2 = []
    # start
    flow_actions_2.append(FlowAction(
        status='N',
        flow_id=flow_define_2.flow_id,
        action_id=1,
        action_version='1.0.0',
        action_order=1,
        action_condition='',
        action_status='A',
        action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
        send_mail_setting={}
    ))
    # item register
    flow_actions_2.append(FlowAction(
        status='N',
        flow_id=flow_define_2.flow_id,
        action_id=3,
        action_version='1.0.0',
        action_order=2,
        action_condition='',
        action_status='A',
        action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
        send_mail_setting={}
    ))
    # oa policy
    flow_actions_2.append(FlowAction(
        status='N',
        flow_id=flow_define_2.flow_id,
        action_id=6,
        action_version='1.0.0',
        action_order=3,
        action_condition='',
        action_status='A',
        action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
        send_mail_setting={}
    ))
    # item link
    flow_actions_2.append(FlowAction(
        status='N',
        flow_id=flow_define_2.flow_id,
        action_id=5,
        action_version='1.0.0',
        action_order=4,
        action_condition='',
        action_status='A',
        action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
        send_mail_setting={}
    ))
    # identifier grant
    flow_actions_2.append(FlowAction(
        status='N',
        flow_id=flow_define_2.flow_id,
        action_id=7,
        action_version='1.0.0',
        action_order=5,
        action_condition='',
        action_status='A',
        action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
        send_mail_setting={}
    ))
    # approval
    flow_actions_2.append(FlowAction(
        status='N',
        flow_id=flow_define_2.flow_id,
        action_id=4,
        action_version='1.0.0',
        action_order=6,
        action_condition='',
        action_status='A',
        action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
        send_mail_setting={}
    ))
    # end
    flow_actions_2.append(FlowAction(
        status='N',
        flow_id=flow_define_2.flow_id,
        action_id=2,
        action_version='1.0.0',
        action_order=7,
        action_condition='',
        action_status='A',
        action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
        send_mail_setting={}
    ))
    with db.session.begin_nested():
        db.session.add_all(flow_actions_2)
    db.session.commit()

    # setting workflow
    workflow = WorkFlow(
        flows_id=uuid.uuid4(),
        flows_name='test workflow01',
        itemtype_id=item_type[0]["item_type"].id,
        index_tree_id=None,
        flow_id=1,
        is_deleted=False,
        open_restricted=False,
        location_id=None,
        is_gakuninrdm=False
    )
    workflow_2 = WorkFlow(
        flows_id=uuid.uuid4(),
        flows_name='test workflow02',
        itemtype_id=item_type[1]["item_type"].id,
        index_tree_id=1623632832836,
        flow_id=2,
        is_deleted=False,
        open_restricted=False,
        location_id=None,
        is_gakuninrdm=False
    )
    with db.session.begin_nested():
        db.session.add(workflow)
        db.session.add(workflow_2)
    db.session.commit()

    return [
        {"flow": flow_define, "flow_action": flow_actions, "workflow": workflow},
        {"flow": flow_define_2, "flow_action": flow_actions_2, "workflow": workflow_2}
        ]


@pytest.fixture
def sword_mapping(db, item_type):
    sword_mapping = []
    for i in range(1, 4):
        obj = ItemTypeJsonldMapping(
            name=f"test{i}",
            mapping=json_data("data/jsonld/ro-crate_mapping.json"),
            item_type_id=item_type[1]["item_type"].id,
            is_deleted=False
        )
        with db.session.begin_nested():
            db.session.add(obj)

        sword_mapping.append({
            "id": obj.id,
            "sword_mapping": obj,
            "name": obj.name,
            "mapping": obj.mapping,
            "item_type_id": obj.item_type_id,
            "version_id": obj.version_id,
            "is_deleted": obj.is_deleted
        })

    db.session.commit()

    return sword_mapping

@pytest.fixture
def sword_client(db, tokens, sword_mapping, workflow):
    client = tokens[0]["client"]
    sword_client1 = SwordClientModel(
        client_id=client.client_id,
        active=True,
        registration_type_id=SwordClientModel.RegistrationType.DIRECT,
        mapping_id=sword_mapping[0]["sword_mapping"].id,
        duplicate_check=False,
        meta_data_api=[],
    )
    client = tokens[1]["client"]
    sword_client2 = SwordClientModel(
        client_id=client.client_id,
        active=True,
        registration_type_id=SwordClientModel.RegistrationType.WORKFLOW,
        mapping_id=sword_mapping[1]["sword_mapping"].id,
        workflow_id=workflow[1]["workflow"].id,
        duplicate_check=True,
        meta_data_api=[],
    )
    client = tokens[2]["client"]
    sword_client3 = SwordClientModel(
        client_id=client.client_id,
        active=False,
        registration_type_id=SwordClientModel.RegistrationType.DIRECT,
        mapping_id=sword_mapping[0]["sword_mapping"].id,
        duplicate_check=False,
        meta_data_api=[],
    )

    with db.session.begin_nested():
        db.session.add(sword_client1)
        db.session.add(sword_client2)
        db.session.add(sword_client3)
    db.session.commit()

    return [
        {"sword_client": sword_client1},
        {"sword_client": sword_client2},
        {"sword_client": sword_client3}
    ]
