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

import copy
import json
from os.path import dirname, exists, join
import mimetypes
import os
import shutil
import tempfile
import time
import uuid
from datetime import datetime
from collections import OrderedDict
from unittest.mock import patch
from datetime import timedelta
from kombu import Exchange, Queue
from sqlalchemy.sql import func

import pytest
from elasticsearch import Elasticsearch
from flask import Flask ,request
from flask_babelex import Babel
from flask_login import LoginManager, UserMixin
from flask_menu import Menu
from invenio_access import InvenioAccess
from invenio_access.models import ActionRoles, ActionUsers
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import Role, User
from invenio_accounts.testutils import create_test_user, login_user_via_session
from invenio_admin import InvenioAdmin
from invenio_assets import InvenioAssets
from invenio_cache import InvenioCache
from invenio_communities.models import Community
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_deposit import InvenioDeposit
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.models import Bucket, Location, ObjectVersion
from invenio_files_rest.views import blueprint as invenio_files_rest_blueprint
from invenio_i18n import InvenioI18N
from invenio_indexer import InvenioIndexer
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_oaiserver import InvenioOAIServer
from invenio_oaiserver.views.server import blueprint as invenio_oaiserver_blueprint
from invenio_oaiserver.models import Identify
from invenio_oauth2server import InvenioOAuth2Server, InvenioOAuth2ServerREST
from invenio_oauth2server.models import Client, Token
from invenio_oauth2server.views import settings_blueprint as oauth2server_settings_blueprint
from invenio_pidrelations import InvenioPIDRelations
from invenio_pidrelations.models import PIDRelation
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidrelations.contrib.records import RecordDraft
from invenio_pidstore import InvenioPIDStore
from invenio_pidstore.models import PersistentIdentifier, PIDStatus, Redirect
from invenio_previewer import InvenioPreviewer
from invenio_records import InvenioRecords
from invenio_records_files.models import RecordsBuckets
from invenio_records_rest.utils import PIDConverter
from invenio_records_ui import InvenioRecordsUI
from invenio_rest import InvenioREST
from invenio_search import InvenioSearch, current_search_client
from invenio_search_ui import InvenioSearchUI
from invenio_stats.config import SEARCH_INDEX_PREFIX as index_prefix
from invenio_theme import InvenioTheme
from simplekv.memory.redisstore import RedisStore
from six import BytesIO
from sqlalchemy_utils.functions import create_database, database_exists, drop_database
from weko_admin import WekoAdmin
from weko_admin.models import SessionLifetime, RankingSettings
from weko_admin.models import AdminSettings
from weko_deposit import WekoDeposit, WekoDepositREST
from weko_deposit.api import WekoDeposit as aWekoDeposit
from weko_deposit.api import WekoIndexer, WekoRecord, _FormatSysBibliographicInformation
from weko_deposit.config import _PID
from weko_deposit.config import DEPOSIT_REST_ENDPOINTS
from weko_deposit.config import DEPOSIT_REST_ENDPOINTS as _DEPOSIT_REST_ENDPOINTS
from weko_deposit.config import WEKO_BUCKET_QUOTA_SIZE
from weko_deposit.config import WEKO_DEPOSIT_REST_ENDPOINTS
from weko_deposit.config import (
    WEKO_DEPOSIT_REST_ENDPOINTS as _WEKO_DEPOSIT_REST_ENDPOINTS,
)
from weko_deposit.storage import WekoFileStorage
from weko_deposit.views import blueprint
from weko_groups import WekoGroups
from weko_index_tree import WekoIndexTree, WekoIndexTreeREST
from weko_index_tree.api import Indexes
from weko_index_tree.config import (
    WEKO_INDEX_TREE_REST_ENDPOINTS as _WEKO_INDEX_TREE_REST_ENDPOINTS,
)
from weko_index_tree.models import Index, IndexStyle
from weko_items_ui import WekoItemsUI
from weko_items_ui.config import WEKO_ITEMS_UI_MS_MIME_TYPE,WEKO_ITEMS_UI_FILE_SISE_PREVIEW_LIMIT
from weko_records import WekoRecords
from weko_records.api import ItemsMetadata, FilesMetadata
from weko_records_ui.ext import WekoRecordsREST
from weko_records.models import ItemType, ItemTypeMapping, ItemTypeName, SiteLicenseInfo, FeedbackMailList,SiteLicenseIpAddress
from weko_records.utils import get_options_and_order_list
from weko_records_ui.config import WEKO_ADMIN_PDFCOVERPAGE_TEMPLATE,RECORDS_UI_ENDPOINTS,WEKO_RECORDS_UI_SECRET_KEY,WEKO_RECORDS_UI_ONETIME_DOWNLOAD_PATTERN
from weko_records_ui.models import FileSecretDownload, PDFCoverPageSettings,FileOnetimeDownload, FilePermission #RocrateMapping
from weko_records_ui.scopes import item_read_scope
from weko_records_ui.utils import _create_secret_download_url, _generate_secret_download_url
from weko_schema_ui.config import (
    WEKO_SCHEMA_DDI_SCHEMA_NAME,
    WEKO_SCHEMA_JPCOAR_V1_SCHEMA_NAME,
)
from weko_schema_ui import WekoSchemaUI
from weko_schema_ui.models import OAIServerSchema
from werkzeug.local import LocalProxy

from weko_records_ui import WekoRecordsUI, WekoRecordsCitesREST
from weko_records_ui.views import blueprint as weko_records_ui_blueprint
from weko_records_ui.config import (
    WEKO_RECORDS_UI_GOOGLE_SCHOLAR_OUTPUT_RESOURCE_TYPE,
    JPAEXM_TTF_FILEPATH,
    URL_OA_POLICY_HEIGHT,
    FOOTER_HEIGHT,
    METADATA_HEIGHT,
    TITLE_HEIGHT,
    HEADER_HEIGHT,
    JPAEXG_TTF_FILEPATH,
    PDF_COVERPAGE_LANG_FILEPATH,
    PDF_COVERPAGE_LANG_FILENAME,
    WEKO_RECORDS_UI_DOWNLOAD_DAYS,
    WEKO_RECORDS_UI_CITES_REST_ENDPOINTS,
    RECORDS_UI_EXPORT_FORMATS,
    WEKO_PERMISSION_ROLE_COMMUNITY,
    WEKO_RECORDS_UI_EMAIL_ITEM_KEYS,
)
from weko_search_ui import WekoSearchUI
from weko_search_ui.config import WEKO_SEARCH_MAX_RESULT
from weko_theme import WekoTheme
from weko_user_profiles.models import UserProfile
from weko_workflow.models import (
    Action,
    ActionStatus,
    ActionStatusPolicy,
    Activity,
    GuestActivity,
    FlowAction,
    FlowDefine,
    WorkFlow,
)
from weko_workflow.config import WEKO_WORKFLOW_DATE_FORMAT
from weko_workflow.scopes import activity_scope
from weko_workflow.views import workflow_blueprint as weko_workflow_blueprint
from werkzeug.utils import secure_filename

from tests.helpers import fill_oauth2_headers



@pytest.yield_fixture()
def instance_path():
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
    app_.url_map.converters["pid"] = PIDConverter
    WEKO_INDEX_TREE_REST_ENDPOINTS = copy.deepcopy(_WEKO_INDEX_TREE_REST_ENDPOINTS)
    WEKO_INDEX_TREE_REST_ENDPOINTS["tid"]["index_route"] = "/tree/index/<int:index_id>"
    # initialize InvenioDeposit first in order to detect any invalid dependency
    WEKO_DEPOSIT_REST_ENDPOINTS = copy.deepcopy(DEPOSIT_REST_ENDPOINTS)
    WEKO_DEPOSIT_REST_ENDPOINTS["depid"][
        "rdc_route"
    ] = "/deposits/redirect/<{0}:pid_value>".format(_PID)
    WEKO_DEPOSIT_REST_ENDPOINTS["depid"][
        "pub_route"
    ] = "/deposits/publish/<{0}:pid_value>".format(_PID)

    # os.environ['FPDF_FONT_DIR'] = "/code/modules/weko-records-ui/weko_records_ui/fonts/"
    app_.config.update(
        CELERY_ALWAYS_EAGER=True,
        CELERY_CACHE_BACKEND="memory",
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_RESULT_BACKEND="cache",
        CACHE_REDIS_URL=os.environ.get("CACHE_REDIS_URL", "redis://redis:6379/0"),
        CACHE_REDIS_DB=0,
        CACHE_REDIS_HOST="redis",
        REDIS_PORT="6379",
        JSONSCHEMAS_URL_SCHEME="http",
        SECRET_KEY="CHANGE_ME",
        SECURITY_PASSWORD_SALT="CHANGE_ME_ALSO",
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "SQLALCHEMY_DATABASE_URI", "sqlite:///test.db"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        SQLALCHEMY_ECHO=False,
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        DEPOSIT_SEARCH_API="/api/search",
        SECURITY_PASSWORD_HASH="plaintext",
        SECURITY_PASSWORD_SCHEMES=["plaintext"],
        SECURITY_DEPRECATED_PASSWORD_SCHEMES=[],
        OAUTHLIB_INSECURE_TRANSPORT=True,
        OAUTH2_CACHE_TYPE="simple",
        ACCOUNTS_JWT_ENABLE=False,
        INDEXER_DEFAULT_INDEX="{}-weko-item-v1.0.0".format("test"),
        INDEXER_DEFAULT_DOCTYPE="item-v1.0.0",
        INDEXER_DEFAULT_DOC_TYPE="item-v1.0.0",
        INDEXER_FILE_DOC_TYPE="content",
        WEKO_BUCKET_QUOTA_SIZE=WEKO_BUCKET_QUOTA_SIZE,
        WEKO_MAX_FILE_SIZE=WEKO_BUCKET_QUOTA_SIZE,
        INDEX_IMG="indextree/36466818-image.jpg",
        WEKO_SEARCH_MAX_RESULT=WEKO_SEARCH_MAX_RESULT,
        WEKO_DEPOSIT_REST_ENDPOINTS=WEKO_DEPOSIT_REST_ENDPOINTS,
        WEKO_INDEX_TREE_STYLE_OPTIONS={
            "id": "weko",
            "widths": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"],
        },
        WEKO_INDEX_TREE_UPATED=True,
        WEKO_INDEX_TREE_REST_ENDPOINTS=WEKO_INDEX_TREE_REST_ENDPOINTS,
        I18N_LANGUAGES=[("ja", "Japanese"), ("en", "English"), ('fr', 'French')],
        SERVER_NAME="TEST_SERVER",
        SEARCH_ELASTIC_HOSTS="elasticsearch",
        SEARCH_INDEX_PREFIX="test-",
        WEKO_SCHEMA_JPCOAR_V1_SCHEMA_NAME=WEKO_SCHEMA_JPCOAR_V1_SCHEMA_NAME,
        WEKO_SCHEMA_DDI_SCHEMA_NAME=WEKO_SCHEMA_DDI_SCHEMA_NAME,
        RECORDS_UI_ENDPOINTS=RECORDS_UI_ENDPOINTS,
        WEKO_RECORDS_UI_CITES_REST_ENDPOINTS=WEKO_RECORDS_UI_CITES_REST_ENDPOINTS,
        RECORDS_UI_EXPORT_FORMATS=RECORDS_UI_EXPORT_FORMATS,
        WEKO_PERMISSION_ROLE_USER=[
            "System Administrator",
            "Repository Administrator",
            "Contributor",
            "General",
            "Community Administrator",
        ],
        WEKO_PERMISSION_SUPER_ROLE_USER=[
            "System Administrator",
            "Repository Administrator",
        ],
        WEKO_PERMISSION_ROLE_COMMUNITY=WEKO_PERMISSION_ROLE_COMMUNITY,
        OAISERVER_XSL_URL=None,
        WEKO_RECORDS_UI_DOWNLOAD_DAYS=WEKO_RECORDS_UI_DOWNLOAD_DAYS,
        PDF_COVERPAGE_LANG_FILEPATH=PDF_COVERPAGE_LANG_FILEPATH,
        PDF_COVERPAGE_LANG_FILENAME=PDF_COVERPAGE_LANG_FILENAME,
        # JPAEXG_TTF_FILEPATH=JPAEXG_TTF_FILEPATH,
        # JPAEXG_TTF_FILEPATH = "/code/modules/weko-records-ui/weko_records_ui/fonts/ipaexg00201/ipaexg.ttf",
        JPAEXG_TTF_FILEPATH="tests/fonts/ipaexg.ttf",
        # JPAEXM_TTF_FILEPATH=JPAEXM_TTF_FILEPATH,
        JPAEXM_TTF_FILEPATH="tests/fonts/ipaexm.ttf",
        URL_OA_POLICY_HEIGHT=URL_OA_POLICY_HEIGHT,
        HEADER_HEIGHT=HEADER_HEIGHT,
        TITLE_HEIGHT=TITLE_HEIGHT,
        FOOTER_HEIGHT=FOOTER_HEIGHT,
        METADATA_HEIGHT=METADATA_HEIGHT,
        WEKO_RECORDS_UI_GOOGLE_SCHOLAR_OUTPUT_RESOURCE_TYPE=WEKO_RECORDS_UI_GOOGLE_SCHOLAR_OUTPUT_RESOURCE_TYPE,
        WEKO_RECORDS_UI_EMAIL_ITEM_KEYS=WEKO_RECORDS_UI_EMAIL_ITEM_KEYS,
        WEKO_ITEMS_UI_FILE_SISE_PREVIEW_LIMIT=WEKO_ITEMS_UI_FILE_SISE_PREVIEW_LIMIT,
        WEKO_ITEMS_UI_MS_MIME_TYPE=WEKO_ITEMS_UI_MS_MIME_TYPE,
        WEKO_RECORDS_UI_SECRET_KEY=WEKO_RECORDS_UI_SECRET_KEY,
        WEKO_RECORDS_UI_ONETIME_DOWNLOAD_PATTERN=WEKO_RECORDS_UI_ONETIME_DOWNLOAD_PATTERN,
        WEKO_ADMIN_PDFCOVERPAGE_TEMPLATE=WEKO_ADMIN_PDFCOVERPAGE_TEMPLATE,
        INDEXER_MQ_QUEUE = Queue("indexer", exchange=Exchange("indexer", type="direct"), routing_key="indexer",queue_arguments={"x-queue-type":"quorum"}),
        WEKO_WORKFLOW_DATE_FORMAT = WEKO_WORKFLOW_DATE_FORMAT,
        WEKO_RECORDS_UI_MAIL_TEMPLATE_SECRET_GENRE_ID = 1,
        SEARCH_UI_SEARCH_INDEX="test-weko",
        FILES_REST_ROLES_ENV = [
            'INVENIO_ROLE_SYSTEM',
            'INVENIO_ROLE_REPOSITORY',
            'INVENIO_ROLE_COMMUNITY'
        ]
    )
    #with ESTestServer(timeout=30) as server:
    client = Elasticsearch(['localhost:9200'])
    InvenioSearch(app_, client=client)
    Babel(app_)
    InvenioAccounts(app_)
    InvenioAccess(app_)
    InvenioAdmin(app_)
    InvenioAssets(app_)
    InvenioCache(app_)
    InvenioDB(app_)
    InvenioDeposit(app_)
    InvenioFilesREST(app_)
    InvenioJSONSchemas(app_)
    InvenioIndexer(app_)
    InvenioOAIServer(app_)
    InvenioPIDStore(app_)
    InvenioPreviewer(app_)
    InvenioRecords(app_)
    InvenioRecordsUI(app_)
    
    InvenioSearch(app_)
    InvenioSearchUI(app_)
    InvenioPIDRelations(app_)
    InvenioI18N(app_)
    InvenioTheme(app_)
    InvenioREST(app_)
    InvenioOAuth2Server(app_)
    InvenioOAuth2ServerREST(app_)
    WekoRecords(app_)
    WekoItemsUI(app_)
    WekoRecordsUI(app_)
    WekoRecordsCitesREST(app_)
    WekoAdmin(app_)
    WekoSearchUI(app_)
    WekoTheme(app_)
    WekoGroups(app_)
    WekoIndexTree(app_)
    WekoIndexTreeREST(app_)
    WekoSchemaUI(app_)
    #Menu(app_)
    app_.register_blueprint(weko_records_ui_blueprint)
    app_.register_blueprint(weko_workflow_blueprint)
    app_.register_blueprint(invenio_files_rest_blueprint)  # invenio_files_rest
    app_.register_blueprint(invenio_oaiserver_blueprint)
    app_.register_blueprint(oauth2server_settings_blueprint)
    # rest_blueprint = create_blueprint(app_, WEKO_DEPOSIT_REST_ENDPOINTS)
    # app_.register_blueprint(rest_blueprint)
    WekoDeposit(app_)
    WekoDepositREST(app_)
    WekoRecordsREST(app_)

    current_assets = LocalProxy(lambda: app_.extensions["invenio-assets"])
    current_assets.collect.collect()
    return app_


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app

@pytest.fixture()
def esindex(app):
    current_search_client.indices.delete(index='test-*')
    with open("tests/data/mappings/item-v1.0.0.json","r") as f:
        mapping = json.load(f)
    try:
        current_search_client.indices.create(app.config["INDEXER_DEFAULT_INDEX"],body=mapping)
        current_search_client.indices.put_alias(index=app.config["INDEXER_DEFAULT_INDEX"], name="test-weko")
    except:
        current_search_client.indices.create("test-weko-items",body=mapping)
        current_search_client.indices.put_alias(index="test-weko-items", name="test-weko")
    # print(current_search_client.indices.get_alias())

    try:
        yield current_search_client
    finally:
        current_search_client.indices.delete(index='test-*')


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
        generaluser = User.query.filter_by(email="generaluser@test.org").first()
        # originalroleuser = create_test_user(email="originalroleuser@test.org")
        # originalroleuser2 = create_test_user(email="originalroleuser2@test.org")
        originalroleuser = User.query.filter_by(email="originalroleuser@test.org").first()
        originalroleuser2 = User.query.filter_by(email="originalroleuser2@test.org").first()

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
        ds.add_role_to_user(user, general_role)

    ret = [
        {"email": contributor.email, "id": contributor.id, "obj": contributor},
        {"email": repoadmin.email, "id": repoadmin.id, "obj": repoadmin},
        {"email": sysadmin.email, "id": sysadmin.id, "obj": sysadmin},
        {"email": comadmin.email, "id": comadmin.id, "obj": comadmin},
        {"email": generaluser.email, "id": generaluser.id, "obj": generaluser},
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

    db.session.expunge_all()


    yield ret
    #return ret


@pytest.fixture()
def indextree(client, users):
    index_metadata = {
        "id": 1,
        "parent": 0,
        "value": "Index(public_state = True,harvest_public_state = True)",
    }

    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        ret = Indexes.create(0, index_metadata)
        index = Index.get_index_by_id(1)
        index.public_state = True
        index.harvest_public_state = True

    index_metadata = {
        "id": 2,
        "parent": 0,
        "value": "Index(public_state = True,harvest_public_state = False)",
    }

    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        Indexes.create(0, index_metadata)
        index = Index.get_index_by_id(2)
        index.public_state = True
        index.harvest_public_state = False

    index_metadata = {
        "id": 3,
        "parent": 0,
        "value": "Index(public_state = False,harvest_public_state = True)",
    }

    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        Indexes.create(0, index_metadata)
        index = Index.get_index_by_id(3)
        index.public_state = False
        index.harvest_public_state = True

    index_metadata = {
        "id": 4,
        "parent": 0,
        "value": "Index(public_state = False,harvest_public_state = False)",
    }

    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        Indexes.create(0, index_metadata)
        index = Index.get_index_by_id(4)
        index.public_state = False
        index.harvest_public_state = False


@pytest.fixture()
def indexstyle(app, db):
    record = IndexStyle(
        id=app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'],
        width='100',
        height='800',
        index_link_enabled=False
    )
    with db.session.begin_nested():
        db.session.add(record)


@pytest.fixture()
def location(app, db):
    """Create default location."""
    tmppath = tempfile.mkdtemp()

    location = Location.query.filter_by(name="testloc").count()
    if location != 1:
        loc = Location(name="testloc", uri=tmppath, default=True)
        db.session.add(loc)
        db.session.commit()
    else:
        loc = Location.query.filter_by(name="testloc").first()

    yield loc

    shutil.rmtree(tmppath)


@pytest.fixture()
def itemtypes(app, db):
    item_type_name = ItemTypeName(
        id=1, name="テストアイテムタイプ", has_site_license=True, is_active=True
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

    item_type_mapping = ItemTypeMapping(id=1, item_type_id=1, mapping=item_type_mapping)

    item_type_name_31001 = ItemTypeName(
        id=31001, name="利用申請", has_site_license=True, is_active=True
    )
    item_type_schema_31001 = dict()
    with open("tests/data/itemtype_schema_31001.json", "r") as f:
        item_type_schema_31001 = json.load(f)

    item_type_form_31001 = dict()
    with open("tests/data/itemtype_form_31001.json", "r") as f:
        item_type_form_31001 = json.load(f)

    item_type_render_31001 = dict()
    with open("tests/data/itemtype_render_31001.json", "r") as f:
        item_type_render_31001 = json.load(f)

    item_type_mapping_31001 = dict()
    with open("tests/data/itemtype_mapping_31001.json", "r") as f:
        item_type_mapping_31001 = json.load(f)

    item_type_31001 = ItemType(
        id=31001,
        name_id=31001,
        harvesting_type=True,
        schema=item_type_schema_31001,
        form=item_type_form_31001,
        render=item_type_render_31001,
        tag=1,
        version_id=1,
        is_deleted=False,
    )

    item_type_mapping_31001 = ItemTypeMapping(id=31001, item_type_id=31001, mapping=item_type_mapping_31001)

    item_type_name_31002 = ItemTypeName(
        id=31002, name="二段階利用申請", has_site_license=True, is_active=True
    )
    item_type_schema_31002 = dict()
    with open("tests/data/itemtype_schema_31002.json", "r") as f:
        item_type_schema_31002 = json.load(f)

    item_type_form_31002 = dict()
    with open("tests/data/itemtype_form_31002.json", "r") as f:
        item_type_form_31002 = json.load(f)

    item_type_render_31002 = dict()
    with open("tests/data/itemtype_render_31002.json", "r") as f:
        item_type_render_31002 = json.load(f)

    item_type_mapping_31002 = dict()
    with open("tests/data/itemtype_mapping_31002.json", "r") as f:
        item_type_mapping_31002 = json.load(f)

    item_type_31002 = ItemType(
        id=31002,
        name_id=31002,
        harvesting_type=True,
        schema=item_type_schema_31002,
        form=item_type_form_31002,
        render=item_type_render_31002,
        tag=1,
        version_id=1,
        is_deleted=False,
    )

    item_type_mapping_31002 = ItemTypeMapping(id=31002, item_type_id=31002, mapping=item_type_mapping_31002)


    with db.session.begin_nested():
        db.session.add(item_type_name)
        db.session.add(item_type)
        db.session.add(item_type_mapping)
        db.session.add(item_type_name_31001)
        db.session.add(item_type_31001)
        db.session.add(item_type_mapping_31001)
        db.session.add(item_type_name_31002)
        db.session.add(item_type_31002)
        db.session.add(item_type_mapping_31002)

    return {
        "item_type_name": item_type_name,
        "item_type": item_type,
        "item_type_mapping": item_type_mapping,
    }


@pytest.fixture()
def oaischema(app, db):
    schema_name = "jpcoar_mapping"
    form_data = {"name": "jpcoar", "file_name": "jpcoar_scm.xsd", "root_name": "jpcoar"}
    xsd = '{"dc:title": {"type": {"maxOccurs": "unbounded", "minOccurs": 1, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, \
            "dcterms:alternative": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, \
            "jpcoar:creator": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}, \
            "jpcoar:nameIdentifier": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "nameIdentifierScheme", "ref": null, \
            "restriction": {"enumeration": ["e-Rad", "NRID", "ORCID", "ISNI", "VIAF", "AID", "kakenhi", "Ringgold", "GRID"]}}, {"use": "optional", "name": "nameIdentifierURI", "ref": null}]}}, \
            "jpcoar:creatorName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, \
            "jpcoar:familyName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, \
            "jpcoar:givenName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, \
            "jpcoar:creatorAlternative": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, \
            "jpcoar:affiliation": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}, \
            "jpcoar:nameIdentifier": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "nameIdentifierScheme", "ref": null, "restriction": {"enumeration": ["e-Rad", "NRID", "ORCID", "ISNI", "VIAF", "AID", "kakenhi", "Ringgold", "GRID"]}}, {"use": "optional", "name": "nameIdentifierURI", "ref": null}]}}, \
            "jpcoar:affiliationName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}}}, \
            "jpcoar:contributor": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "contributorType", "ref": null, "restriction": {"enumeration": ["ContactPerson", "DataCollector", "DataCurator", "DataManager", "Distributor", "Editor", "HostingInstitution", "Producer", "ProjectLeader", "ProjectManager", "ProjectMember", "RegistrationAgency", "RegistrationAuthority", "RelatedPerson", "Researcher", "ResearchGroup", "Sponsor", "Supervisor", "WorkPackageLeader", "Other"]}}]}, \
            "jpcoar:nameIdentifier": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "nameIdentifierScheme", "ref": null, "restriction": {"enumeration": ["e-Rad", "NRID", "ORCID", "ISNI", "VIAF", "AID", "kakenhi", "Ringgold", "GRID"]}}, {"use": "optional", "name": "nameIdentifierURI", "ref": null}]}}, \
            "jpcoar:contributorName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, \
            "jpcoar:familyName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, \
            "jpcoar:givenName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, \
            "jpcoar:contributorAlternative": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, \
            "jpcoar:affiliation": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}, "jpcoar:nameIdentifier": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "nameIdentifierScheme", "ref": null, "restriction": {"enumeration": ["e-Rad", "NRID", "ORCID", "ISNI", "VIAF", "AID", "kakenhi", "Ringgold", "GRID"]}}, {"use": "optional", "name": "nameIdentifierURI", "ref": null}]}}, \
            "jpcoar:affiliationName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}}}, \
            "dcterms:accessRights": {"type": {"maxOccurs": 1, "minOccurs": 0, "attributes": [{"use": "required", "name": "rdf:resource", "ref": "rdf:resource"}], "restriction": {"enumeration": ["embargoed access", "metadata only access", "open access", "restricted access"]}}}, "rioxxterms:apc": {"type": {"maxOccurs": 1, "minOccurs": 0, "restriction": {"enumeration": ["Paid", "Partially waived", "Fully waived", "Not charged", "Not required", "Unknown"]}}}, \
            "dc:rights": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "rdf:resource", "ref": "rdf:resource"}, {"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:rightsHolder": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}, "jpcoar:nameIdentifier": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "nameIdentifierScheme", "ref": null, "restriction": {"enumeration": ["e-Rad", "NRID", "ORCID", "ISNI", "VIAF", "AID", "kakenhi", "Ringgold", "GRID"]}}, {"use": "optional", "name": "nameIdentifierURI", "ref": null}]}}, "jpcoar:rightsHolderName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}}, \
            "jpcoar:subject": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}, {"use": "optional", "name": "subjectURI", "ref": null}, {"use": "required", "name": "subjectScheme", "ref": null, "restriction": {"enumeration": ["BSH", "DDC", "LCC", "LCSH", "MeSH", "NDC", "NDLC", "NDLSH", "Sci-Val", "UDC", "Other"]}}]}}, \
            "datacite:description": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}, {"use": "required", "name": "descriptionType", "ref": null, "restriction": {"enumeration": ["Abstract", "Methods", "TableOfContents", "TechnicalInfo", "Other"]}}]}}, "dc:publisher": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "datacite:date": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "dateType", "ref": null, "restriction": {"enumeration": ["Accepted", "Available", "Collected", "Copyrighted", "Created", "Issued", "Submitted", "Updated", "Valid"]}}]}}, "dc:language": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "restriction": {"patterns": ["^[a-z]{3}$"]}}}, "dc:type": {"type": {"maxOccurs": 1, "minOccurs": 1, "attributes": [{"use": "required", "name": "rdf:resource", "ref": "rdf:resource"}], "restriction": {"enumeration": ["conference paper", "data paper", "departmental bulletin paper", "editorial", "journal article", "newspaper", "periodical", "review article", "software paper", "article", "book", "book part", "cartographic material", "map", "conference object", "conference proceedings", "conference poster", "dataset", "aggregated data", "clinical trial data", "compiled data", "encoded data", "experimental data", "genomic data", "geospatial data", "laboratory notebook", "measurement and test data", "observational data", "recorded data", "simulation data", "survey data", "interview", "image", "still image", "moving image", "video", "lecture", "patent", "internal report", "report", "research report", "technical report", "policy report", "report part", "working paper", "data management plan", "sound", "thesis", "bachelor thesis", "master thesis", "doctoral thesis", "interactive resource", "learning object", "manuscript", "musical notation", "research proposal", "software", "technical documentation", "workflow", "other"]}}}, "datacite:version": {"type": {"maxOccurs": 1, "minOccurs": 0}}, \
            "oaire:versiontype": {"type": {"maxOccurs": 1, "minOccurs": 0, "attributes": [{"use": "required", "name": "rdf:resource", "ref": "rdf:resource"}], "restriction": {"enumeration": ["AO", "SMUR", "AM", "P", "VoR", "CVoR", "EVoR", "NA"]}}}, \
            "jpcoar:identifier": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "identifierType", "ref": null, "restriction": {"enumeration": ["DOI", "HDL", "URI"]}}]}}, \
            "jpcoar:identifierRegistration": {"type": {"maxOccurs": 1, "minOccurs": 0, "attributes": [{"use": "required", "name": "identifierType", "ref": null, "restriction": {"enumeration": ["JaLC", "Crossref", "DataCite", "PMID"]}}]}}, \
            "jpcoar:relation": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "relationType", "ref": null, "restriction": {"enumeration": ["isVersionOf", "hasVersion", "isPartOf", "hasPart", "isReferencedBy", "references", "isFormatOf", "hasFormat", "isReplacedBy", "replaces", "isRequiredBy", "requires", "isSupplementTo", "isSupplementedBy", "isIdenticalTo", "isDerivedFrom", "isSourceOf"]}}]}, "jpcoar:relatedIdentifier": {"type": {"maxOccurs": 1, "minOccurs": 0, "attributes": [{"use": "required", "name": "identifierType", "ref": null, "restriction": {"enumeration": ["ARK", "arXiv", "DOI", "HDL", "ICHUSHI", "ISBN", "J-GLOBAL", "Local", "PISSN", "EISSN", "NAID", "PMID", "PURL", "SCOPUS", "URI", "WOS"]}}]}}, \
            "jpcoar:relatedTitle": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}}, \
            "dcterms:temporal": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, \
            "datacite:geoLocation": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}, "datacite:geoLocationPoint": {"type": {"maxOccurs": 1, "minOccurs": 0}, \
            "datacite:pointLongitude": {"type": {"maxOccurs": 1, "minOccurs": 1, "restriction": {"maxInclusive": 180, "minInclusive": -180}}}, \
            "datacite:pointLatitude": {"type": {"maxOccurs": 1, "minOccurs": 1, "restriction": {"maxInclusive": 90, "minInclusive": -90}}}}, \
            "datacite:geoLocationBox": {"type": {"maxOccurs": 1, "minOccurs": 0}, "datacite:westBoundLongitude": {"type": {"maxOccurs": 1, "minOccurs": 1, "restriction": {"maxInclusive": 180, "minInclusive": -180}}}, "datacite:eastBoundLongitude": {"type": {"maxOccurs": 1, "minOccurs": 1, "restriction": {"maxInclusive": 180, "minInclusive": -180}}}, "datacite:southBoundLatitude": {"type": {"maxOccurs": 1, "minOccurs": 1, "restriction": {"maxInclusive": 90, "minInclusive": -90}}}, "datacite:northBoundLatitude": {"type": {"maxOccurs": 1, "minOccurs": 1, "restriction": {"maxInclusive": 90, "minInclusive": -90}}}}, "datacite:geoLocationPlace": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}}}, "jpcoar:fundingReference": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}, "datacite:funderIdentifier": {"type": {"maxOccurs": 1, "minOccurs": 0, "attributes": [{"use": "required", "name": "funderIdentifierType", "ref": null, "restriction": {"enumeration": ["Crossref Funder", "GRID", "ISNI", "Other"]}}]}}, "jpcoar:funderName": {"type": {"maxOccurs": "unbounded", "minOccurs": 1, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "datacite:awardNumber": {"type": {"maxOccurs": 1, "minOccurs": 0, "attributes": [{"use": "optional", "name": "awardURI", "ref": null}]}}, "jpcoar:awardTitle": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}}, "jpcoar:sourceIdentifier": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "identifierType", "ref": null, "restriction": {"enumeration": ["PISSN", "EISSN", "ISSN", "NCID"]}}]}}, "jpcoar:sourceTitle": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:volume": {"type": {"maxOccurs": 1, "minOccurs": 0}}, "jpcoar:issue": {"type": {"maxOccurs": 1, "minOccurs": 0}}, "jpcoar:numPages": {"type": {"maxOccurs": 1, "minOccurs": 0}}, "jpcoar:pageStart": {"type": {"maxOccurs": 1, "minOccurs": 0}}, "jpcoar:pageEnd": {"type": {"maxOccurs": 1, "minOccurs": 0}}, "dcndl:dissertationNumber": {"type": {"maxOccurs": 1, "minOccurs": 0}}, "dcndl:degreeName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "dcndl:dateGranted": {"type": {"maxOccurs": 1, "minOccurs": 0}}, "jpcoar:degreeGrantor": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}, "jpcoar:nameIdentifier": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "nameIdentifierScheme", "ref": null, "restriction": {"enumeration": ["e-Rad", "NRID", "ORCID", "ISNI", "VIAF", "AID", "kakenhi", "Ringgold", "GRID"]}}, {"use": "optional", "name": "nameIdentifierURI", "ref": null}]}}, "jpcoar:degreeGrantorName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}}, "jpcoar:conference": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}, "jpcoar:conferenceName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:conferenceSequence": {"type": {"maxOccurs": 1, "minOccurs": 0}}, "jpcoar:conferenceSponsor": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:conferenceDate": {"type": {"maxOccurs": 1, "minOccurs": 0, "attributes": [{"use": "optional", "name": "startMonth", "ref": null, "restriction": {"maxInclusive": 12, "minInclusive": 1, "totalDigits": 2}}, {"use": "optional", "name": "endYear", "ref": null, "restriction": {"maxInclusive": 2200, "minInclusive": 1400, "totalDigits": 4}}, {"use": "optional", "name": "startDay", "ref": null, "restriction": {"maxInclusive": 31, "minInclusive": 1, "totalDigits": 2}}, {"use": "optional", "name": "endDay", "ref": null, "restriction": {"maxInclusive": 31, "minInclusive": 1, "totalDigits": 2}}, {"use": "optional", "name": "endMonth", "ref": null, "restriction": {"maxInclusive": 12, "minInclusive": 1, "totalDigits": 2}}, {"use": "optional", "name": "xml:lang", "ref": "xml:lang"}, {"use": "optional", "name": "startYear", "ref": null, "restriction": {"maxInclusive": 2200, "minInclusive": 1400, "totalDigits": 4}}]}}, "jpcoar:conferenceVenue": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:conferencePlace": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:conferenceCountry": {"type": {"maxOccurs": 1, "minOccurs": 0, "restriction": {"patterns": ["^[A-Z]{3}$"]}}}}, "jpcoar:file": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}, "jpcoar:URI": {"type": {"maxOccurs": 1, "minOccurs": 0, "attributes": [{"use": "optional", "name": "label", "ref": null}, {"use": "optional", "name": "objectType", "ref": null, "restriction": {"enumeration": ["abstract", "dataset", "fulltext", "software", "summary", "thumbnail", "other"]}}]}}, "jpcoar:mimeType": {"type": {"maxOccurs": 1, "minOccurs": 0}}, "jpcoar:extent": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}}, "datacite:date": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "dateType", "ref": null, "restriction": {"enumeration": ["Accepted", "Available", "Collected", "Copyrighted", "Created", "Issued", "Submitted", "Updated", "Valid"]}}]}}, "datacite:version": {"type": {"maxOccurs": 1, "minOccurs": 0}}}, "custom:system_file": {"type": {"minOccurs": 0, "maxOccurs": "unbounded"}, "jpcoar:URI": {"type": {"minOccurs": 0, "maxOccurs": 1, "attributes": [{"name": "objectType", "ref": null, "use": "optional", "restriction": {"enumeration": ["abstract", "summary", "fulltext", "thumbnail", "other"]}}, {"name": "label", "ref": null, "use": "optional"}]}}, "jpcoar:mimeType": {"type": {"minOccurs": 0, "maxOccurs": 1}}, "jpcoar:extent": {"type": {"minOccurs": 0, "maxOccurs": "unbounded"}}, "datacite:date": {"type": {"minOccurs": 1, "maxOccurs": "unbounded", "attributes": [{"name": "dateType", "ref": null, "use": "required", "restriction": {"enumeration": ["Accepted", "Available", "Collected", "Copyrighted", "Created", "Issued", "Submitted", "Updated", "Valid"]}}]}}, "datacite:version": {"type": {"minOccurs": 0, "maxOccurs": 1}}}}'
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
    jpcoar_mapping = OAIServerSchema(
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
    jpcoar_v1_mapping = OAIServerSchema(
        id=uuid.uuid4(),
        schema_name="jpcoar_v1_mapping",
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
        db.session.add(jpcoar_mapping)
        db.session.add(jpcoar_v1_mapping)


@pytest.fixture()
def oaiidentify(app, db):
    identify = Identify(outPutSetting=True,emails="wekosoftware@nii.ac.jp",repositoryName="test repository")
    with db.session.begin_nested():
        db.session.add(identify)


@pytest.fixture()
def db_sessionlifetime(app, db):
    session_lifetime = SessionLifetime(lifetime=60, is_delete=False)
    with db.session.begin_nested():
        db.session.add(session_lifetime)


@pytest.fixture()
def records(app, db, esindex, indextree, location, itemtypes, oaischema):
    indexer = WekoIndexer()
    indexer.get_es_index()
    results = []
    # with app.test_request_context():
    i = 1
    filename = "helloworld.pdf"
    mimetype = "application/pdf"
    filepath = "tests/data/helloworld.pdf"

    shared_ids = []
    results.append(make_record(db, indexer, i, filepath, filename, mimetype, shared_ids, file_head=True))

    i = 2
    filename = "helloworld.docx"
    mimetype = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    filepath = "tests/data/helloworld.docx"
    shared_ids = [1]
    results.append(make_record(db, indexer, i, filepath, filename, mimetype, shared_ids, file_head=False))

    i = 3
    filename = "helloworld.zip"
    mimetype = "application/zip"
    filepath = "tests/data/helloworld.zip"
    shared_ids = [1,2]
    results.append(make_record(db, indexer, i, filepath, filename, mimetype, shared_ids, file_head=False))

    i = 4
    files = [
        {
            "filename": "helloworld.pdf",
            "mimetype": "application/pdf",
            "filepath": "tests/data/helloworld.pdf",
            "accessrole": "open_access",
        },
        {
            "filename": "helloworld.txt",
            "mimetype": "text/plain",
            "filepath": "tests/data/helloworld.txt",
            "accessrole": "open_no",
        },
    ]
    results.append(make_record_v2(db, indexer, i, files))

    i = 5
    files = [
        {
            "filename": "helloworld.pdf",
            "mimetype": "application/pdf",
            "filepath": "tests/data/helloworld.pdf",
            "accessrole": "open_no",
        },
    ]
    results.append(make_record_v2(db, indexer, i, files))

    i = 6
    files = []
    results.append(make_record_v2(db, indexer, i, files))

    i = 7
    files = [
        {
            "filename": "helloworld.pdf",
            "mimetype": "application/pdf",
            "filepath": "tests/data/helloworld.pdf",
            "accessrole": "open_access",
        },
    ]
    thumbnail = {
        "filename": "image01.jpg",
        "filepath": "tests/data/image01.jpg",
    }
    results.append(make_record_v2(db, indexer, i, files, thumbnail))

    return indexer, results


def make_record(db, indexer, i, filepath, filename, mimetype, shared_ids, file_head):
    record_data = {
        "_oai": {"id": "oai:weko3.example.org:000000{:02d}".format(i), "sets": ["{}".format((i % 2) + 1)]},
        "path": ["{}".format((i % 2) + 1)],
        "owner": 1,
        "recid": "{}".format(i),
        "title": [
            "ja_conference paperITEM00000009(public_open_access_open_access_simple)"
        ],
        "pubdate": {"attribute_name": "PubDate", "attribute_value": "2021-08-06"},
        "_buckets": {"deposit": "27202db8-aefc-4b85-b5ae-4921ac151ddf"},
        "_deposit": {
            "id": "{}".format(i),
            "pid": {"type": "depid", "value": "{}".format(i), "revision_id": 0},
            "owners": [1],
            "status": "published",
        },
        "item_title": "ja_conference paperITEM00000009(public_open_access_open_access_simple)",
        "author_link": ["4"],
        "item_type_id": "1",
        "publish_date": "2021-08-06",
        "publish_status": "0",
        "weko_shared_ids": shared_ids,
        "item_1617186331708": {
            "attribute_name": "Title",
            "attribute_value_mlt": [
                {
                    "subitem_1551255647225": "ja_conference paperITEM00000009(public_open_access_open_access_simple)",
                    "subitem_1551255648112": "ja",
                },
                {
                    "subitem_1551255647225": "en_conference paperITEM00000009(public_open_access_simple)",
                    "subitem_1551255648112": "en",
                },
            ],
        },
        "item_1617186385884": {
            "attribute_name": "Alternative Title",
            "attribute_value_mlt": [
                {
                    "subitem_1551255720400": "Alternative Title",
                    "subitem_1551255721061": "en",
                },
                {
                    "subitem_1551255720400": "Alternative Title",
                    "subitem_1551255721061": "ja",
                },
            ],
        },
        "item_1617186419668": {
            "attribute_name": "Creator",
            "attribute_type": "creator",
            "attribute_value_mlt": [
                {
                    "givenNames": [
                        {"givenName": "太郎", "givenNameLang": "ja"},
                        {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Taro", "givenNameLang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                    "creatorNames": [
                        {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                        {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                        {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                    ],
                    "nameIdentifiers": [
                        {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://orcid.org/",
                            "nameIdentifierScheme": "ORCID",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                            "nameIdentifierScheme": "CiNii",
                        },
                        {
                            "nameIdentifier": "zzzzzzz",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                            "nameIdentifierScheme": "KAKEN2",
                        },
                    ],
                    "creatorAffiliations": [
                        {
                            "affiliationNames": [
                                {
                                    "affiliationName": "University",
                                    "affiliationNameLang": "en",
                                }
                            ],
                            "affiliationNameIdentifiers": [
                                {
                                    "affiliationNameIdentifier": "0000000121691048",
                                    "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                    "affiliationNameIdentifierScheme": "ISNI",
                                }
                            ],
                        }
                    ],
                },
                {
                    "givenNames": [
                        {"givenName": "太郎", "givenNameLang": "ja"},
                        {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Taro", "givenNameLang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                    "creatorNames": [
                        {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                        {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                        {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                    ],
                    "nameIdentifiers": [
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://orcid.org/",
                            "nameIdentifierScheme": "ORCID",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                            "nameIdentifierScheme": "CiNii",
                        },
                        {
                            "nameIdentifier": "zzzzzzz",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                            "nameIdentifierScheme": "KAKEN2",
                        },
                    ],
                },
                {
                    "givenNames": [
                        {"givenName": "太郎", "givenNameLang": "ja"},
                        {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Taro", "givenNameLang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                    "creatorNames": [
                        {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                        {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                        {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                    ],
                    "nameIdentifiers": [
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://orcid.org/",
                            "nameIdentifierScheme": "ORCID",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                            "nameIdentifierScheme": "CiNii",
                        },
                        {
                            "nameIdentifier": "zzzzzzz",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                            "nameIdentifierScheme": "KAKEN2",
                        },
                    ],
                },
            ],
        },
        "item_1617186476635": {
            "attribute_name": "Access Rights",
            "attribute_value_mlt": [
                {
                    "subitem_1522299639480": "open access",
                    "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
                }
            ],
        },
        "item_1617186499011": {
            "attribute_name": "Rights",
            "attribute_value_mlt": [
                {
                    "subitem_1522650717957": "ja",
                    "subitem_1522650727486": "http://localhost",
                    "subitem_1522651041219": "Rights Information",
                }
            ],
        },
        "item_1617186609386": {
            "attribute_name": "Subject",
            "attribute_value_mlt": [
                {
                    "subitem_1522299896455": "ja",
                    "subitem_1522300014469": "Other",
                    "subitem_1522300048512": "http://localhost/",
                    "subitem_1523261968819": "Sibject1",
                }
            ],
        },
        "item_1617186626617": {
            "attribute_name": "Description",
            "attribute_value_mlt": [
                {
                    "subitem_description": "Description\nDescription<br/>Description",
                    "subitem_description_type": "Abstract",
                    "subitem_description_language": "en",
                },
                {
                    "subitem_description": "概要\n概要\n概要\n概要",
                    "subitem_description_type": "Abstract",
                    "subitem_description_language": "ja",
                },
            ],
        },
        "item_1617186643794": {
            "attribute_name": "Publisher",
            "attribute_value_mlt": [
                {"subitem_1522300295150": "en", "subitem_1522300316516": "Publisher"}
            ],
        },
        "item_1617186660861": {
            "attribute_name": "Date",
            "attribute_value_mlt": [
                {
                    "subitem_1522300695726": "Available",
                    "subitem_1522300722591": "2021-06-30",
                }
            ],
        },
        "item_1617186702042": {
            "attribute_name": "Language",
            "attribute_value_mlt": [{"subitem_1551255818386": "jpn"}],
        },
        "item_1617186783814": {
            "attribute_name": "Identifier",
            "attribute_value_mlt": [
                {
                    "subitem_identifier_uri": "http://localhost",
                    "subitem_identifier_type": "URI",
                }
            ],
        },
        "item_1617186859717": {
            "attribute_name": "Temporal",
            "attribute_value_mlt": [
                {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
            ],
        },
        "item_1617186882738": {
            "attribute_name": "Geo Location",
            "attribute_value_mlt": [
                {
                    "subitem_geolocation_place": [
                        {"subitem_geolocation_place_text": "Japan"}
                    ]
                }
            ],
        },
        "item_1617186901218": {
            "attribute_name": "Funding Reference",
            "attribute_value_mlt": [
                {
                    "subitem_1522399143519": {
                        "subitem_1522399281603": "ISNI",
                        "subitem_1522399333375": "http://xxx",
                    },
                    "subitem_1522399412622": [
                        {
                            "subitem_1522399416691": "en",
                            "subitem_1522737543681": "Funder Name",
                        }
                    ],
                    "subitem_1522399571623": {
                        "subitem_1522399585738": "Award URI",
                        "subitem_1522399628911": "Award Number",
                    },
                    "subitem_1522399651758": [
                        {
                            "subitem_1522721910626": "en",
                            "subitem_1522721929892": "Award Title",
                        }
                    ],
                }
            ],
        },
        "item_1617186920753": {
            "attribute_name": "Source Identifier",
            "attribute_value_mlt": [
                {
                    "subitem_1522646500366": "ISSN",
                    "subitem_1522646572813": "xxxx-xxxx-xxxx",
                }
            ],
        },
        "item_1617186941041": {
            "attribute_name": "Source Title",
            "attribute_value_mlt": [
                {"subitem_1522650068558": "en", "subitem_1522650091861": "Source Title"}
            ],
        },
        "item_1617186959569": {
            "attribute_name": "Volume Number",
            "attribute_value_mlt": [{"subitem_1551256328147": "1"}],
        },
        "item_1617186981471": {
            "attribute_name": "Issue Number",
            "attribute_value_mlt": [{"subitem_1551256294723": "111"}],
        },
        "item_1617186994930": {
            "attribute_name": "Number of Pages",
            "attribute_value_mlt": [{"subitem_1551256248092": "12"}],
        },
        "item_1617187024783": {
            "attribute_name": "Page Start",
            "attribute_value_mlt": [{"subitem_1551256198917": "1"}],
        },
        "item_1617187045071": {
            "attribute_name": "Page End",
            "attribute_value_mlt": [{"subitem_1551256185532": "3"}],
        },
        "item_1617187112279": {
            "attribute_name": "Degree Name",
            "attribute_value_mlt": [
                {"subitem_1551256126428": "Degree Name", "subitem_1551256129013": "en"}
            ],
        },
        "item_1617187136212": {
            "attribute_name": "Date Granted",
            "attribute_value_mlt": [{"subitem_1551256096004": "2021-06-30"}],
        },
        "item_1617187187528": {
            "attribute_name": "Conference",
            "attribute_value_mlt": [
                {
                    "subitem_1599711633003": [
                        {
                            "subitem_1599711636923": "Conference Name",
                            "subitem_1599711645590": "ja",
                        }
                    ],
                    "subitem_1599711655652": "1",
                    "subitem_1599711660052": [
                        {
                            "subitem_1599711680082": "Sponsor",
                            "subitem_1599711686511": "ja",
                        }
                    ],
                    "subitem_1599711699392": {
                        "subitem_1599711704251": "2020/12/11",
                        "subitem_1599711712451": "1",
                        "subitem_1599711727603": "12",
                        "subitem_1599711731891": "2000",
                        "subitem_1599711735410": "1",
                        "subitem_1599711739022": "12",
                        "subitem_1599711743722": "2020",
                        "subitem_1599711745532": "ja",
                    },
                    "subitem_1599711758470": [
                        {
                            "subitem_1599711769260": "Conference Venue",
                            "subitem_1599711775943": "ja",
                        }
                    ],
                    "subitem_1599711788485": [
                        {
                            "subitem_1599711798761": "Conference Place",
                            "subitem_1599711803382": "ja",
                        }
                    ],
                    "subitem_1599711813532": "JPN",
                }
            ],
        },
        "item_1617258105262": {
            "attribute_name": "Resource Type",
            "attribute_value_mlt": [
                {
                    "resourceuri": "http://purl.org/coar/resource_type/c_5794",
                    "resourcetype": "conference paper",
                }
            ],
        },
        "item_1617265215918": {
            "attribute_name": "Version Type",
            "attribute_value_mlt": [
                {
                    "subitem_1522305645492": "AO",
                    "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
                }
            ],
        },
        "item_1617349709064": {
            "attribute_name": "Contributor",
            "attribute_value_mlt": [
                {
                    "givenNames": [
                        {"givenName": "太郎", "givenNameLang": "ja"},
                        {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Taro", "givenNameLang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "contributorType": "ContactPerson",
                    "nameIdentifiers": [
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://orcid.org/",
                            "nameIdentifierScheme": "ORCID",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                            "nameIdentifierScheme": "CiNii",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                            "nameIdentifierScheme": "KAKEN2",
                        },
                    ],
                    "contributorMails": [{"contributorMail": "wekosoftware@nii.ac.jp"}],
                    "contributorNames": [
                        {"lang": "ja", "contributorName": "情報, 太郎"},
                        {"lang": "ja-Kana", "contributorName": "ジョウホウ, タロウ"},
                        {"lang": "en", "contributorName": "Joho, Taro"},
                    ],
                }
            ],
        },
        "item_1617349808926": {
            "attribute_name": "Version",
            "attribute_value_mlt": [{"subitem_1523263171732": "Version"}],
        },
        "item_1617351524846": {
            "attribute_name": "APC",
            "attribute_value_mlt": [{"subitem_1523260933860": "Unknown"}],
        },
        "item_1617353299429": {
            "attribute_name": "Relation",
            "attribute_value_mlt": [
                {
                    "subitem_1522306207484": "isVersionOf",
                    "subitem_1522306287251": {
                        "subitem_1522306382014": "arXiv",
                        "subitem_1522306436033": "xxxxx",
                    },
                    "subitem_1523320863692": [
                        {
                            "subitem_1523320867455": "en",
                            "subitem_1523320909613": "Related Title",
                        }
                    ],
                }
            ],
        },
        "item_1617605131499": {
            "attribute_name": "File",
            "attribute_type": "file",
            "attribute_value_mlt": [
                {
                    "url": {"url": "https://weko3.example.org/record/{0}/files/{1}".format(
                            i, filename
                        )},
                    "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                    "format": "text/plain",
                    "filename": "{}".format(filename),
                    "filesize": [{"value": "1 KB"}],
                    "mimetype": "{}".format(mimetype),
                    "accessrole": "open_access",
                    "version_id": "c1502853-c2f9-455d-8bec-f6e630e54b21",
                    "displaytype": "simple",
                }
            ],
        },
        "item_1617610673286": {
            "attribute_name": "Rights Holder",
            "attribute_value_mlt": [
                {
                    "nameIdentifiers": [
                        {
                            "nameIdentifier": "xxxxxx",
                            "nameIdentifierURI": "https://orcid.org/",
                            "nameIdentifierScheme": "ORCID",
                        }
                    ],
                    "rightHolderNames": [
                        {
                            "rightHolderName": "Right Holder Name",
                            "rightHolderLanguage": "ja",
                        }
                    ],
                }
            ],
        },
        "item_1617620223087": {
            "attribute_name": "Heading",
            "attribute_value_mlt": [
                {
                    "subitem_1565671149650": "ja",
                    "subitem_1565671169640": "Banner Headline",
                    "subitem_1565671178623": "Subheading",
                },
                {
                    "subitem_1565671149650": "en",
                    "subitem_1565671169640": "Banner Headline",
                    "subitem_1565671178623": "Subheding",
                },
            ],
        },
        "item_1617944105607": {
            "attribute_name": "Degree Grantor",
            "attribute_value_mlt": [
                {
                    "subitem_1551256015892": [
                        {
                            "subitem_1551256027296": "xxxxxx",
                            "subitem_1551256029891": "kakenhi",
                        }
                    ],
                    "subitem_1551256037922": [
                        {
                            "subitem_1551256042287": "Degree Grantor Name",
                            "subitem_1551256047619": "en",
                        }
                    ],
                }
            ],
        },
        "relation_version_is_last": True,
    }

    item_data = {
        "id": "{}".format(i),
        "pid": {"type": "recid", "value": "{}".format(i), "revision_id": 0},
        "path": ["{}".format((i % 2) + 1)],
        "owner": 1,
        "title": "ja_conference paperITEM00000009(public_open_access_open_access_simple)",
        "owners": [1],
        "status": "draft",
        "$schema": "https://localhost:8443/items/jsonschema/1",
        "pubdate": "2021-08-06",
        "feedback_mail_list": [{"email": "wekosoftware@nii.ac.jp", "author_id": ""}],
        "item_1617186331708": [
            {
                "subitem_1551255647225": "ja_conference paperITEM00000009(public_open_access_open_access_simple)",
                "subitem_1551255648112": "ja",
            },
            {
                "subitem_1551255647225": "en_conference paperITEM00000009(public_open_access_simple)",
                "subitem_1551255648112": "en",
            },
        ],
        "item_1617186385884": [
            {
                "subitem_1551255720400": "Alternative Title",
                "subitem_1551255721061": "en",
            },
            {
                "subitem_1551255720400": "Alternative Title",
                "subitem_1551255721061": "ja",
            },
        ],
        "item_1617186419668": [
            {
                "givenNames": [
                    {"givenName": "太郎", "givenNameLang": "ja"},
                    {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                    {"givenName": "Taro", "givenNameLang": "en"},
                ],
                "familyNames": [
                    {"familyName": "情報", "familyNameLang": "ja"},
                    {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                    {"familyName": "Joho", "familyNameLang": "en"},
                ],
                "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                "creatorNames": [
                    {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                    {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                    {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                ],
                "nameIdentifiers": [
                    {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://orcid.org/",
                        "nameIdentifierScheme": "ORCID",
                    },
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://ci.nii.ac.jp/",
                        "nameIdentifierScheme": "CiNii",
                    },
                    {
                        "nameIdentifier": "zzzzzzz",
                        "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                        "nameIdentifierScheme": "KAKEN2",
                    },
                ],
                "creatorAffiliations": [
                    {
                        "affiliationNames": [
                            {
                                "affiliationName": "University",
                                "affiliationNameLang": "en",
                            }
                        ],
                        "affiliationNameIdentifiers": [
                            {
                                "affiliationNameIdentifier": "0000000121691048",
                                "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                "affiliationNameIdentifierScheme": "ISNI",
                            }
                        ],
                    }
                ],
            },
            {
                "givenNames": [
                    {"givenName": "太郎", "givenNameLang": "ja"},
                    {"givenName": "タロ", "givenNameLang": "ja-Kana"},
                    {"givenName": "Taro", "givenNameLang": "en"},
                ],
                "familyNames": [
                    {"familyName": "情報", "familyNameLang": "ja"},
                    {"familyName": "ジウホウ", "familyNameLang": "ja-Kana"},
                    {"familyName": "Joho", "familyNameLang": "en"},
                ],
                "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                "creatorNames": [
                    {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                    {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                    {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                ],
                "nameIdentifiers": [
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://orcid.org/",
                        "nameIdentifierScheme": "ORCID",
                    },
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://ci.nii.ac.jp/",
                        "nameIdentifierScheme": "CiNii",
                    },
                    {
                        "nameIdentifier": "zzzzzzz",
                        "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                        "nameIdentifierScheme": "KAKEN2",
                    },
                ],
            },
            {
                "givenNames": [
                    {"givenName": "太郎", "givenNameLang": "ja"},
                    {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                    {"givenName": "Taro", "givenNameLang": "en"},
                ],
                "familyNames": [
                    {"familyName": "情報", "familyNameLang": "ja"},
                    {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                    {"familyName": "Joho", "familyNameLang": "en"},
                ],
                "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                "creatorNames": [
                    {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                    {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                    {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                ],
                "nameIdentifiers": [
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://orcid.org/",
                        "nameIdentifierScheme": "ORCID",
                    },
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://ci.nii.ac.jp/",
                        "nameIdentifierScheme": "CiNii",
                    },
                    {
                        "nameIdentifier": "zzzzzzz",
                        "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                        "nameIdentifierScheme": "KAKEN2",
                    },
                ],
            },
        ],
        "item_1617186476635": {
            "subitem_1522299639480": "open access",
            "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
        },
        "item_1617186499011": [
            {
                "subitem_1522650717957": "ja",
                "subitem_1522650727486": "http://localhost",
                "subitem_1522651041219": "Rights Information",
            }
        ],
        "item_1617186609386": [
            {
                "subitem_1522299896455": "ja",
                "subitem_1522300014469": "Other",
                "subitem_1522300048512": "http://localhost/",
                "subitem_1523261968819": "Sibject1",
            }
        ],
        "item_1617186626617": [
            {
                "subitem_description": "Description\nDescription<br/>Description",
                "subitem_description_type": "Abstract",
                "subitem_description_language": "en",
            },
            {
                "subitem_description": "概要\n概要\n概要\n概要",
                "subitem_description_type": "Abstract",
                "subitem_description_language": "ja",
            },
        ],
        "item_1617186643794": [
            {"subitem_1522300295150": "en", "subitem_1522300316516": "Publisher"}
        ],
        "item_1617186660861": [
            {
                "subitem_1522300695726": "Available",
                "subitem_1522300722591": "2021-06-30",
            }
        ],
        "item_1617186702042": [{"subitem_1551255818386": "jpn"}],
        "item_1617186783814": [
            {
                "subitem_identifier_uri": "http://localhost",
                "subitem_identifier_type": "URI",
            }
        ],
        "item_1617186859717": [
            {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
        ],
        "item_1617186882738": [
            {"subitem_geolocation_place": [{"subitem_geolocation_place_text": "Japan"}]}
        ],
        "item_1617186901218": [
            {
                "subitem_1522399143519": {
                    "subitem_1522399281603": "ISNI",
                    "subitem_1522399333375": "http://xxx",
                },
                "subitem_1522399412622": [
                    {
                        "subitem_1522399416691": "en",
                        "subitem_1522737543681": "Funder Name",
                    }
                ],
                "subitem_1522399571623": {
                    "subitem_1522399585738": "Award URI",
                    "subitem_1522399628911": "Award Number",
                },
                "subitem_1522399651758": [
                    {
                        "subitem_1522721910626": "en",
                        "subitem_1522721929892": "Award Title",
                    }
                ],
            }
        ],
        "item_1617186920753": [
            {"subitem_1522646500366": "ISSN", "subitem_1522646572813": "xxxx-xxxx-xxxx"}
        ],
        "item_1617186941041": [
            {"subitem_1522650068558": "en", "subitem_1522650091861": "Source Title"}
        ],
        "item_1617186959569": {"subitem_1551256328147": "1"},
        "item_1617186981471": {"subitem_1551256294723": "111"},
        "item_1617186994930": {"subitem_1551256248092": "12"},
        "item_1617187024783": {"subitem_1551256198917": "1"},
        "item_1617187045071": {"subitem_1551256185532": "3"},
        "item_1617187112279": [
            {"subitem_1551256126428": "Degree Name", "subitem_1551256129013": "en"}
        ],
        "item_1617187136212": {"subitem_1551256096004": "2021-06-30"},
        "item_1617187187528": [
            {
                "subitem_1599711633003": [
                    {
                        "subitem_1599711636923": "Conference Name",
                        "subitem_1599711645590": "ja",
                    }
                ],
                "subitem_1599711655652": "1",
                "subitem_1599711660052": [
                    {"subitem_1599711680082": "Sponsor", "subitem_1599711686511": "ja"}
                ],
                "subitem_1599711699392": {
                    "subitem_1599711704251": "2020/12/11",
                    "subitem_1599711712451": "1",
                    "subitem_1599711727603": "12",
                    "subitem_1599711731891": "2000",
                    "subitem_1599711735410": "1",
                    "subitem_1599711739022": "12",
                    "subitem_1599711743722": "2020",
                    "subitem_1599711745532": "ja",
                },
                "subitem_1599711758470": [
                    {
                        "subitem_1599711769260": "Conference Venue",
                        "subitem_1599711775943": "ja",
                    }
                ],
                "subitem_1599711788485": [
                    {
                        "subitem_1599711798761": "Conference Place",
                        "subitem_1599711803382": "ja",
                    }
                ],
                "subitem_1599711813532": "JPN",
            }
        ],
        "item_1617258105262": {
            "resourceuri": "http://purl.org/coar/resource_type/c_5794",
            "resourcetype": "conference paper",
        },
        "item_1617265215918": {
            "subitem_1522305645492": "AO",
            "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
        },
        "item_1617349709064": [
            {
                "givenNames": [
                    {"givenName": "太郎", "givenNameLang": "ja"},
                    {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                    {"givenName": "Taro", "givenNameLang": "en"},
                ],
                "familyNames": [
                    {"familyName": "情報", "familyNameLang": "ja"},
                    {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                    {"familyName": "Joho", "familyNameLang": "en"},
                ],
                "contributorType": "ContactPerson",
                "nameIdentifiers": [
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://orcid.org/",
                        "nameIdentifierScheme": "ORCID",
                    },
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://ci.nii.ac.jp/",
                        "nameIdentifierScheme": "CiNii",
                    },
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                        "nameIdentifierScheme": "KAKEN2",
                    },
                ],
                "contributorMails": [{"contributorMail": "wekosoftware@nii.ac.jp"}],
                "contributorNames": [
                    {"lang": "ja", "contributorName": "情報, 太郎"},
                    {"lang": "ja-Kana", "contributorName": "ジョウホ, タロウ"},
                    {"lang": "en", "contributorName": "Joho, Taro"},
                ],
            }
        ],
        "item_1617349808926": {"subitem_1523263171732": "Version"},
        "item_1617351524846": {"subitem_1523260933860": "Unknown"},
        "item_1617353299429": [
            {
                "subitem_1522306207484": "isVersionOf",
                "subitem_1522306287251": {
                    "subitem_1522306382014": "arXiv",
                    "subitem_1522306436033": "xxxxx",
                },
                "subitem_1523320863692": [
                    {
                        "subitem_1523320867455": "en",
                        "subitem_1523320909613": "Related Title",
                    }
                ],
            }
        ],
        "item_1617605131499": [
            {
                "url": {
                    "url": "https://weko3.example.org/record/{0}/files/{1}".format(i,filename)
                },
                "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                "format": "{}".format(mimetype),
                "filename": "{}".format(filename),
                "filesize": [{"value": "1 KB"}],
                "mimetype": "{}".format(mimetype),
                "accessrole": "open_access",
                "version_id": "c1502853-c2f9-455d-8bec-f6e630e54b21",
                "displaytype": "simple",
            }
        ],
        "item_1617610673286": [
            {
                "nameIdentifiers": [
                    {
                        "nameIdentifier": "xxxxxx",
                        "nameIdentifierURI": "https://orcid.org/",
                        "nameIdentifierScheme": "ORCID",
                    }
                ],
                "rightHolderNames": [
                    {
                        "rightHolderName": "Right Holder Name",
                        "rightHolderLanguage": "ja",
                    }
                ],
            }
        ],
        "item_1617620223087": [
            {
                "subitem_1565671149650": "ja",
                "subitem_1565671169640": "Banner Headline",
                "subitem_1565671178623": "Subheading",
            },
            {
                "subitem_1565671149650": "en",
                "subitem_1565671169640": "Banner Headline",
                "subitem_1565671178623": "Subheding",
            },
        ],
        "item_1617944105607": [
            {
                "subitem_1551256015892": [
                    {
                        "subitem_1551256027296": "xxxxxx",
                        "subitem_1551256029891": "kakenhi",
                    }
                ],
                "subitem_1551256037922": [
                    {
                        "subitem_1551256042287": "Degree Grantor Name",
                        "subitem_1551256047619": "en",
                    }
                ],
            }
        ],
    }

    rec_uuid = uuid.uuid4()

    recid = PersistentIdentifier.create(
        "recid",
        str(i),
        object_type="rec",
        object_uuid=rec_uuid,
        status=PIDStatus.REGISTERED,
    )
    depid = PersistentIdentifier.create(
        "depid",
        str(i),
        object_type="rec",
        object_uuid=rec_uuid,
        status=PIDStatus.REGISTERED,
    )
    parent = None
    doi = None
    hdl = None
    recid_v1 = PersistentIdentifier.create(
        "recid",
        str(i + 0.1),
        object_type="rec",
        object_uuid=rec_uuid,
        status=PIDStatus.REGISTERED,
    )
    rec_uuid2 = uuid.uuid4()
    depid_v1 = PersistentIdentifier.create(
        "depid",
        str(i + 0.1),
        object_type="rec",
        object_uuid=rec_uuid2,
        status=PIDStatus.REGISTERED,
    )
    parent = PersistentIdentifier.create(
        "parent",
        "parent:{}".format(i),
        object_type="rec",
        object_uuid=rec_uuid2,
        status=PIDStatus.REGISTERED,
    )

    h1 = PIDVersioning(parent=parent)
    h1.insert_child(child=recid)
    h1.insert_child(child=recid_v1)
    RecordDraft.link(recid, depid)
    RecordDraft.link(recid_v1, depid_v1)

    if i % 2 == 1:
        doi = PersistentIdentifier.create(
            "doi",
            "https://doi.org/10.xyz/{}".format((str(i)).zfill(10)),
            object_type="rec",
            object_uuid=rec_uuid,
            status=PIDStatus.REGISTERED,
        )
        hdl = PersistentIdentifier.create(
            "hdl",
            "https://hdl.handle.net/0000/{}".format((str(i)).zfill(10)),
            object_type="rec",
            object_uuid=rec_uuid,
            status=PIDStatus.REGISTERED,
        )

    record = WekoRecord.create(record_data, id_=rec_uuid)
    # from six import BytesIO
    import base64

    bucket = Bucket.create()
    record_buckets = RecordsBuckets.create(record=record.model, bucket=bucket)

    # stream = BytesIO(b"Hello, World")
    obj = None
    with open(filepath, "rb") as f:
        stream = BytesIO(f.read())
        record.files[filename] = stream
        record["item_1617605131499"]["attribute_value_mlt"][0]["file"] = (
            base64.b64encode(stream.getvalue())
        ).decode("utf-8")
    with open(filepath, "rb") as f:
        obj = ObjectVersion.create(bucket=bucket.id, key=filename, stream=f)
        FilesMetadata.create(data={'file': filename, 'display_name': filename}, id_=i, pid=i, con=bytes('test content {}'.format(i), 'utf-8'))
    deposit = aWekoDeposit(record, record.model)
    deposit.commit()
    record["item_1617605131499"]["attribute_value_mlt"][0]["version_id"] = str(
        obj.version_id
    )

    record_data["content"] = [
        {
            "date": [{"dateValue": "2021-07-12", "dateType": "Available"}],
            "accessrole": "open_access",
            "displaytype": "simple",
            "filename": filename,
            "attachment": {},
            "format": mimetype,
            "mimetype": mimetype,
            "filesize": [{"value": "1 KB"}],
            "version_id": "{}".format(obj.version_id),
            "url": {"url": "http://localhost/record/{0}/files/{1}".format(i, filename)},
            "file": (base64.b64encode(stream.getvalue())).decode("utf-8"),
        }
    ]
    indexer.upload_metadata(record_data, rec_uuid, 1, False)
    item = ItemsMetadata.create(item_data, id_=rec_uuid, item_type_id=1)

    record_v1 = WekoRecord.create(record_data, id_=rec_uuid2)
    # from six import BytesIO
    import base64

    bucket_v1 = Bucket.create()
    record_buckets = RecordsBuckets.create(record=record_v1.model, bucket=bucket_v1)
    # stream = BytesIO(b"Hello, World")
    record_v1.files[filename] = stream
    obj_v1 = ObjectVersion.create(bucket=bucket_v1.id, key=filename, stream=stream)
    record_v1["item_1617605131499"]["attribute_value_mlt"][0]["file"] = (
        base64.b64encode(stream.getvalue())
    ).decode("utf-8")
    deposit_v1 = aWekoDeposit(record_v1, record_v1.model)
    deposit_v1.commit()
    record_v1["item_1617605131499"]["attribute_value_mlt"][0]["version_id"] = str(
        obj_v1.version_id
    )

    record_data_v1 = copy.deepcopy(record_data)
    record_data_v1["content"] = [
        {
            "date": [{"dateValue": "2021-07-12", "dateType": "Available"}],
            "accessrole": "open_access",
            "displaytype": "simple",
            "filename": filename,
            "attachment": {},
            "format": mimetype,
            "mimetype": mimetype,
            "filesize": [{"value": "1 KB"}],
            "version_id": "{}".format(obj_v1.version_id),
            "url": {"url": "http://localhost/record/{0}/files/{1}".format(i, filename)},
            "file": (base64.b64encode(stream.getvalue())).decode("utf-8"),
        }
    ]
    indexer.upload_metadata(record_data_v1, rec_uuid2, 1, False)
    item_v1 = ItemsMetadata.create(item_data, id_=rec_uuid2, item_type_id=1)

    # db.session.expunge_all()

    return {
        "depid": depid,
        "recid": recid,
        "parent": parent,
        "doi": doi,
        "hdl": hdl,
        "record": record,
        "record_data": record_data,
        "item": item,
        "item_data": item_data,
        "deposit": deposit,
        "filename": filename,
        "mimetype": mimetype,
        "obj": obj,
    }

def make_record_v2(db, indexer, i, files, thumbnail=None):
    record_data = {
        "_oai": {"id": f"oai:weko3.example.org:000000{i:02}", "sets": [f"{(i % 2) + 1}"]},
        "path": [f"{(i % 2) + 1}"],
        "owner": "1",
        "recid": f"{i}",
        "title": [
            "ja_conference paperITEM00000009(public_open_access_open_access_simple)"
        ],
        "pubdate": {"attribute_name": "PubDate", "attribute_value": "2024-02-15"},
        "_buckets": {"deposit": "27202db8-aefc-4b85-b5ae-4921ac151ddf"},
        "_deposit": {
            "id": f"{i}",
            "pid": {"type": "depid", "value": f"{i}", "revision_id": 0},
            "owners": [1],
            "status": "published",
        },
        "item_title": "ja_conference paperITEM00000009(public_open_access_open_access_simple)",
        "author_link": ["4"],
        "item_type_id": "1",
        "publish_date": "2024-01-31",
        "publish_status": "0",
        "weko_shared_id": -1,
        "item_1617186331708": {
            "attribute_name": "Title",
            "attribute_value_mlt": [
                {
                    "subitem_1551255647225": "ja_conference paperITEM00000009(public_open_access_open_access_simple)",
                    "subitem_1551255648112": "ja",
                },
                {
                    "subitem_1551255647225": "en_conference paperITEM00000009(public_open_access_simple)",
                    "subitem_1551255648112": "en",
                },
            ],
        },
        "item_1617186385884": {
            "attribute_name": "Alternative Title",
            "attribute_value_mlt": [
                {
                    "subitem_1551255720400": "Alternative EN Title",
                    "subitem_1551255721061": "en",
                },
                {
                    "subitem_1551255720400": "Alternative JA Title",
                    "subitem_1551255721061": "ja",
                },
            ],
        },
        "item_1617186419668": {
            "attribute_name": "Creator",
            "attribute_type": "creator",
            "attribute_value_mlt": [
                {
                    "givenNames": [
                        {"givenName": "太郎", "givenNameLang": "ja"},
                        {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Taro", "givenNameLang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                    "creatorNames": [
                        {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                        {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                        {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                    ],
                    "nameIdentifiers": [
                        {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://orcid.org/",
                            "nameIdentifierScheme": "ORCID",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                            "nameIdentifierScheme": "CiNii",
                        },
                        {
                            "nameIdentifier": "zzzzzzz",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                            "nameIdentifierScheme": "KAKEN2",
                        },
                    ],
                    "creatorAffiliations": [
                        {
                            "affiliationNames": [
                                {
                                    "affiliationName": "University",
                                    "affiliationNameLang": "en",
                                }
                            ],
                            "affiliationNameIdentifiers": [
                                {
                                    "affiliationNameIdentifier": "0000000121691048",
                                    "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                    "affiliationNameIdentifierScheme": "ISNI",
                                }
                            ],
                        }
                    ],
                },
                {
                    "givenNames": [
                        {"givenName": "太郎", "givenNameLang": "ja"},
                        {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Taro", "givenNameLang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                    "creatorNames": [
                        {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                        {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                        {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                    ],
                    "nameIdentifiers": [
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://orcid.org/",
                            "nameIdentifierScheme": "ORCID",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                            "nameIdentifierScheme": "CiNii",
                        },
                        {
                            "nameIdentifier": "zzzzzzz",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                            "nameIdentifierScheme": "KAKEN2",
                        },
                    ],
                },
                {
                    "givenNames": [
                        {"givenName": "太郎", "givenNameLang": "ja"},
                        {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Taro", "givenNameLang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                    "creatorNames": [
                        {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                        {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                        {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                    ],
                    "nameIdentifiers": [
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://orcid.org/",
                            "nameIdentifierScheme": "ORCID",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                            "nameIdentifierScheme": "CiNii",
                        },
                        {
                            "nameIdentifier": "zzzzzzz",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                            "nameIdentifierScheme": "KAKEN2",
                        },
                    ],
                },
            ],
        },
        "item_1617186476635": {
            "attribute_name": "Access Rights",
            "attribute_value_mlt": [
                {
                    "subitem_1522299639480": "open access",
                    "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
                }
            ],
        },
        "item_1617186626617": {
            "attribute_name": "Description",
            "attribute_value_mlt": [
                {
                    "subitem_description": "Description\nDescription<br/>Description",
                    "subitem_description_type": "Abstract",
                    "subitem_description_language": "en",
                },
                {
                    "subitem_description": "概要\n概要\n概要\n概要",
                    "subitem_description_type": "Abstract",
                    "subitem_description_language": "ja",
                },
            ],
        },
        "item_1617186643794": {
            "attribute_name": "Publisher",
            "attribute_value_mlt": [
                {"subitem_1522300295150": "en", "subitem_1522300316516": "Publisher"}
            ],
        },
        "item_1617186660861": {
            "attribute_name": "Date",
            "attribute_value_mlt": [
                {
                    "subitem_1522300695726": "Available",
                    "subitem_1522300722591": "2024-01-31",
                }
            ],
        },
        "item_1617186702042": {
            "attribute_name": "Language",
            "attribute_value_mlt": [{"subitem_1551255818386": "jpn"}],
        },
        "item_1617605131499": {
            "attribute_name": "File",
            "attribute_type": "file",
            "attribute_value_mlt": [],
        },
        "relation_version_is_last": True,
    }

    item_data = {
        "id": f"{i}",
        "pid": {"type": "recid", "value": f"{i}", "revision_id": 0},
        "path": [f"{(i % 2) + 1}"],
        "owner": "1",
        "title": "ja_conference paperITEM00000009(public_open_access_open_access_simple)",
        "owners": [1],
        "status": "draft",
        "$schema": "https://localhost:8443/items/jsonschema/1",
        "pubdate": "2021-08-06",
        "feedback_mail_list": [{"email": "wekosoftware@nii.ac.jp", "author_id": ""}],
        "item_1617186331708": [
            {
                "subitem_1551255647225": "ja_conference paperITEM00000009(public_open_access_open_access_simple)",
                "subitem_1551255648112": "ja",
            },
            {
                "subitem_1551255647225": "en_conference paperITEM00000009(public_open_access_simple)",
                "subitem_1551255648112": "en",
            },
        ],
        "item_1617186385884": [
            {
                "subitem_1551255720400": "Alternative Title",
                "subitem_1551255721061": "en",
            },
            {
                "subitem_1551255720400": "Alternative Title",
                "subitem_1551255721061": "ja",
            },
        ],
        "item_1617186419668": [
            {
                "givenNames": [
                    {"givenName": "太郎", "givenNameLang": "ja"},
                    {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                    {"givenName": "Taro", "givenNameLang": "en"},
                ],
                "familyNames": [
                    {"familyName": "情報", "familyNameLang": "ja"},
                    {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                    {"familyName": "Joho", "familyNameLang": "en"},
                ],
                "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                "creatorNames": [
                    {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                    {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                    {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                ],
                "nameIdentifiers": [
                    {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://orcid.org/",
                        "nameIdentifierScheme": "ORCID",
                    },
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://ci.nii.ac.jp/",
                        "nameIdentifierScheme": "CiNii",
                    },
                    {
                        "nameIdentifier": "zzzzzzz",
                        "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                        "nameIdentifierScheme": "KAKEN2",
                    },
                ],
                "creatorAffiliations": [
                    {
                        "affiliationNames": [
                            {
                                "affiliationName": "University",
                                "affiliationNameLang": "en",
                            }
                        ],
                        "affiliationNameIdentifiers": [
                            {
                                "affiliationNameIdentifier": "0000000121691048",
                                "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                "affiliationNameIdentifierScheme": "ISNI",
                            }
                        ],
                    }
                ],
            },
            {
                "givenNames": [
                    {"givenName": "太郎", "givenNameLang": "ja"},
                    {"givenName": "タロ", "givenNameLang": "ja-Kana"},
                    {"givenName": "Taro", "givenNameLang": "en"},
                ],
                "familyNames": [
                    {"familyName": "情報", "familyNameLang": "ja"},
                    {"familyName": "ジウホウ", "familyNameLang": "ja-Kana"},
                    {"familyName": "Joho", "familyNameLang": "en"},
                ],
                "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                "creatorNames": [
                    {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                    {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                    {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                ],
                "nameIdentifiers": [
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://orcid.org/",
                        "nameIdentifierScheme": "ORCID",
                    },
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://ci.nii.ac.jp/",
                        "nameIdentifierScheme": "CiNii",
                    },
                    {
                        "nameIdentifier": "zzzzzzz",
                        "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                        "nameIdentifierScheme": "KAKEN2",
                    },
                ],
            },
            {
                "givenNames": [
                    {"givenName": "太郎", "givenNameLang": "ja"},
                    {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                    {"givenName": "Taro", "givenNameLang": "en"},
                ],
                "familyNames": [
                    {"familyName": "情報", "familyNameLang": "ja"},
                    {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                    {"familyName": "Joho", "familyNameLang": "en"},
                ],
                "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                "creatorNames": [
                    {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                    {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                    {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                ],
                "nameIdentifiers": [
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://orcid.org/",
                        "nameIdentifierScheme": "ORCID",
                    },
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://ci.nii.ac.jp/",
                        "nameIdentifierScheme": "CiNii",
                    },
                    {
                        "nameIdentifier": "zzzzzzz",
                        "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                        "nameIdentifierScheme": "KAKEN2",
                    },
                ],
            },
        ],
        "item_1617186476635": {
            "subitem_1522299639480": "open access",
            "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
        },
        "item_1617186499011": [
            {
                "subitem_1522650717957": "ja",
                "subitem_1522650727486": "http://localhost",
                "subitem_1522651041219": "Rights Information",
            }
        ],
        "item_1617186609386": [
            {
                "subitem_1522299896455": "ja",
                "subitem_1522300014469": "Other",
                "subitem_1522300048512": "http://localhost/",
                "subitem_1523261968819": "Sibject1",
            }
        ],
        "item_1617186626617": [
            {
                "subitem_description": "Description\nDescription<br/>Description",
                "subitem_description_type": "Abstract",
                "subitem_description_language": "en",
            },
            {
                "subitem_description": "概要\n概要\n概要\n概要",
                "subitem_description_type": "Abstract",
                "subitem_description_language": "ja",
            },
        ],
        "item_1617186643794": [
            {"subitem_1522300295150": "en", "subitem_1522300316516": "Publisher"}
        ],
        "item_1617186660861": [
            {
                "subitem_1522300695726": "Available",
                "subitem_1522300722591": "2021-06-30",
            }
        ],
        "item_1617186702042": [{"subitem_1551255818386": "jpn"}],
        "item_1617186783814": [
            {
                "subitem_identifier_uri": "http://localhost",
                "subitem_identifier_type": "URI",
            }
        ],
        "item_1617186859717": [
            {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
        ],
        "item_1617186882738": [
            {"subitem_geolocation_place": [{"subitem_geolocation_place_text": "Japan"}]}
        ],
        "item_1617186901218": [
            {
                "subitem_1522399143519": {
                    "subitem_1522399281603": "ISNI",
                    "subitem_1522399333375": "http://xxx",
                },
                "subitem_1522399412622": [
                    {
                        "subitem_1522399416691": "en",
                        "subitem_1522737543681": "Funder Name",
                    }
                ],
                "subitem_1522399571623": {
                    "subitem_1522399585738": "Award URI",
                    "subitem_1522399628911": "Award Number",
                },
                "subitem_1522399651758": [
                    {
                        "subitem_1522721910626": "en",
                        "subitem_1522721929892": "Award Title",
                    }
                ],
            }
        ],
        "item_1617186920753": [
            {"subitem_1522646500366": "ISSN", "subitem_1522646572813": "xxxx-xxxx-xxxx"}
        ],
        "item_1617186941041": [
            {"subitem_1522650068558": "en", "subitem_1522650091861": "Source Title"}
        ],
        "item_1617186959569": {"subitem_1551256328147": "1"},
        "item_1617186981471": {"subitem_1551256294723": "111"},
        "item_1617186994930": {"subitem_1551256248092": "12"},
        "item_1617187024783": {"subitem_1551256198917": "1"},
        "item_1617187045071": {"subitem_1551256185532": "3"},
        "item_1617187112279": [
            {"subitem_1551256126428": "Degree Name", "subitem_1551256129013": "en"}
        ],
        "item_1617187136212": {"subitem_1551256096004": "2021-06-30"},
        "item_1617187187528": [
            {
                "subitem_1599711633003": [
                    {
                        "subitem_1599711636923": "Conference Name",
                        "subitem_1599711645590": "ja",
                    }
                ],
                "subitem_1599711655652": "1",
                "subitem_1599711660052": [
                    {"subitem_1599711680082": "Sponsor", "subitem_1599711686511": "ja"}
                ],
                "subitem_1599711699392": {
                    "subitem_1599711704251": "2020/12/11",
                    "subitem_1599711712451": "1",
                    "subitem_1599711727603": "12",
                    "subitem_1599711731891": "2000",
                    "subitem_1599711735410": "1",
                    "subitem_1599711739022": "12",
                    "subitem_1599711743722": "2020",
                    "subitem_1599711745532": "ja",
                },
                "subitem_1599711758470": [
                    {
                        "subitem_1599711769260": "Conference Venue",
                        "subitem_1599711775943": "ja",
                    }
                ],
                "subitem_1599711788485": [
                    {
                        "subitem_1599711798761": "Conference Place",
                        "subitem_1599711803382": "ja",
                    }
                ],
                "subitem_1599711813532": "JPN",
            }
        ],
        "item_1617258105262": {
            "resourceuri": "http://purl.org/coar/resource_type/c_5794",
            "resourcetype": "conference paper",
        },
        "item_1617265215918": {
            "subitem_1522305645492": "AO",
            "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
        },
        "item_1617349709064": [
            {
                "givenNames": [
                    {"givenName": "太郎", "givenNameLang": "ja"},
                    {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                    {"givenName": "Taro", "givenNameLang": "en"},
                ],
                "familyNames": [
                    {"familyName": "情報", "familyNameLang": "ja"},
                    {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                    {"familyName": "Joho", "familyNameLang": "en"},
                ],
                "contributorType": "ContactPerson",
                "nameIdentifiers": [
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://orcid.org/",
                        "nameIdentifierScheme": "ORCID",
                    },
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://ci.nii.ac.jp/",
                        "nameIdentifierScheme": "CiNii",
                    },
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                        "nameIdentifierScheme": "KAKEN2",
                    },
                ],
                "contributorMails": [{"contributorMail": "wekosoftware@nii.ac.jp"}],
                "contributorNames": [
                    {"lang": "ja", "contributorName": "情報, 太郎"},
                    {"lang": "ja-Kana", "contributorName": "ジョウホ, タロウ"},
                    {"lang": "en", "contributorName": "Joho, Taro"},
                ],
            }
        ],
        "item_1617349808926": {"subitem_1523263171732": "Version"},
        "item_1617351524846": {"subitem_1523260933860": "Unknown"},
        "item_1617353299429": [
            {
                "subitem_1522306207484": "isVersionOf",
                "subitem_1522306287251": {
                    "subitem_1522306382014": "arXiv",
                    "subitem_1522306436033": "xxxxx",
                },
                "subitem_1523320863692": [
                    {
                        "subitem_1523320867455": "en",
                        "subitem_1523320909613": "Related Title",
                    }
                ],
            }
        ],
        "item_1617605131499": [],
        "item_1617610673286": [
            {
                "nameIdentifiers": [
                    {
                        "nameIdentifier": "xxxxxx",
                        "nameIdentifierURI": "https://orcid.org/",
                        "nameIdentifierScheme": "ORCID",
                    }
                ],
                "rightHolderNames": [
                    {
                        "rightHolderName": "Right Holder Name",
                        "rightHolderLanguage": "ja",
                    }
                ],
            }
        ],
        "item_1617620223087": [
            {
                "subitem_1565671149650": "ja",
                "subitem_1565671169640": "Banner Headline",
                "subitem_1565671178623": "Subheading",
            },
            {
                "subitem_1565671149650": "en",
                "subitem_1565671169640": "Banner Headline",
                "subitem_1565671178623": "Subheding",
            },
        ],
        "item_1617944105607": [
            {
                "subitem_1551256015892": [
                    {
                        "subitem_1551256027296": "xxxxxx",
                        "subitem_1551256029891": "kakenhi",
                    }
                ],
                "subitem_1551256037922": [
                    {
                        "subitem_1551256042287": "Degree Grantor Name",
                        "subitem_1551256047619": "en",
                    }
                ],
            }
        ],
    }

    items = []
    for file in files:
        items.append({
            "url": {"url": f"https://weko3.example.org/record/{i}/files/{file.get('filename')}"},
            "date": [{"dateType": "Available", "dateValue": "2024-01-01"}],
            "format": "text/plain",
            "filename": f"{file.get('filename')}",
            "filesize": [{"value": "1 KB"}],
            "mimetype": f"{file.get('mimetype')}",
            "accessrole": f"{file.get('accessrole', 'open_access')}",
            "version_id": "c1502853-c2f9-455d-8bec-f6e630e54b21",
            "displaytype": "simple",
        })
        FilesMetadata.create(data=file, id_=i, pid=i, con=bytes('test content {}'.format(i), 'utf-8'))
    record_data["item_1617605131499"]["attribute_value_mlt"] = items
    item_data["item_1617605131499"] = items

    rec_uuid = uuid.uuid4()

    recid = PersistentIdentifier.create(
        "recid",
        str(i),
        object_type="rec",
        object_uuid=rec_uuid,
        status=PIDStatus.REGISTERED,
    )
    depid = PersistentIdentifier.create(
        "depid",
        str(i),
        object_type="rec",
        object_uuid=rec_uuid,
        status=PIDStatus.REGISTERED,
    )
    parent = None
    doi = None
    hdl = None
    recid_v1 = PersistentIdentifier.create(
        "recid",
        str(i + 0.1),
        object_type="rec",
        object_uuid=rec_uuid,
        status=PIDStatus.REGISTERED,
    )
    rec_uuid2 = uuid.uuid4()
    depid_v1 = PersistentIdentifier.create(
        "depid",
        str(i + 0.1),
        object_type="rec",
        object_uuid=rec_uuid2,
        status=PIDStatus.REGISTERED,
    )
    parent = PersistentIdentifier.create(
        "parent",
        "parent:{}".format(i),
        object_type="rec",
        object_uuid=rec_uuid2,
        status=PIDStatus.REGISTERED,
    )

    h1 = PIDVersioning(parent=parent)
    h1.insert_child(child=recid)
    h1.insert_child(child=recid_v1)
    RecordDraft.link(recid, depid)
    RecordDraft.link(recid_v1, depid_v1)

    if i % 2 == 1:
        doi = PersistentIdentifier.create(
            "doi",
            "https://doi.org/10.xyz/{}".format((str(i)).zfill(10)),
            object_type="rec",
            object_uuid=rec_uuid,
            status=PIDStatus.REGISTERED,
        )
        hdl = PersistentIdentifier.create(
            "hdl",
            "https://hdl.handle.net/0000/{}".format((str(i)).zfill(10)),
            object_type="rec",
            object_uuid=rec_uuid,
            status=PIDStatus.REGISTERED,
        )

    record = WekoRecord.create(record_data, id_=rec_uuid)
    import base64

    bucket = Bucket.create()
    record_buckets = RecordsBuckets.create(record=record.model, bucket=bucket)

    if thumbnail:
        files.append(thumbnail)

    obj = None
    record_data["content"] = []
    for num, file in enumerate(files):
        filepath = file.get("filepath")
        filename = file.get("filename")
        mimetype = file.get("mimetype")
        accessrole = file.get("accessrole", "open_access")

        with open(filepath, "rb") as f:
            stream = BytesIO(f.read())
            record.files[filename] = stream
            if len(record["item_1617605131499"]["attribute_value_mlt"]) > num:
                record["item_1617605131499"]["attribute_value_mlt"][num]["file"] = (
                    base64.b64encode(stream.getvalue())
                ).decode("utf-8")

        with open(filepath, "rb") as f:
            obj = ObjectVersion.create(bucket=bucket.id, key=filename, stream=f)

        record_data["content"].append(
            {
                "date": [{"dateValue": "2024-01-31", "dateType": "Available"}],
                "accessrole": f"{accessrole}",
                "displaytype": "simple",
                "filename": f"{filename}",
                "attachment": {},
                "format": f"{mimetype}",
                "mimetype": f"{mimetype}",
                "filesize": [{"value": "1 KB"}],
                "version_id": f"{obj.version_id}",
                "url": {"url": f"http://localhost/record/{i}/files/{filename}"},
                "file": (base64.b64encode(stream.getvalue())).decode("utf-8"),
            }
        )
    indexer.upload_metadata(record_data, rec_uuid, 1, False)
    item = ItemsMetadata.create(item_data, id_=rec_uuid, item_type_id=40001)
    deposit = aWekoDeposit(record, record.model)
    deposit.commit()

    return {
        "depid": depid,
        "recid": recid,
        "parent": parent,
        "doi": doi,
        "hdl": hdl,
        "record": record,
        "record_data": record_data,
        "deposit": deposit,
        "files": files,
    }


@pytest.fixture()
def records_restricted(app, db, workflows_restricted, records ,users):
    indexer , results = records

    # with app.test_request_context():
    i = len(results) + 1
    # i = 4
    filename = "helloworld_open_restricted.pdf"
    mimetype = "application/pdf"
    filepath = "tests/data/helloworld.pdf"
    wf1 :WorkFlow = workflows_restricted.get("workflow_workflow1")
    wf2 :WorkFlow = workflows_restricted.get("workflow_workflow2")
    results.append(make_record_restricted(db, indexer, i, filepath, filename, mimetype 
                                        ,"none_loggin" ,wf2.id))
    i = i + 1
    results.append(make_record_restricted(db, indexer, i, filepath, filename, mimetype 
                                        ,str(users[0]["id"]) #contributer
                                        ,wf1.id))
    i = i + 1
    roles = [{"role":1},{"role":2}]
    results.append(make_record_restricted_open_login(db, indexer, i, filepath, filename, mimetype
                                                     ,str(users[0]["id"])
                                                     ,wf1.id
                                                     ,roles))
    i = i + 1
    roles = []
    results.append(make_record_restricted_open_login(db, indexer, i, filepath, filename, mimetype
                                                     ,str(users[0]["id"])
                                                     ,wf1.id
                                                     ,roles))

    return indexer, results

def make_record_restricted(db, indexer, i, filepath, filename, mimetype ,userId ,workflowId):
    """ make open_resirected record"""
    record_data = {
        "_oai": {"id": "oai:weko3.example.org:000000{:02d}".format(i), "sets": ["{}".format((i % 2) + 1)]},
        "path": ["{}".format((i % 2) + 1)],
        "owner": 1,
        "recid": "{}".format(i),
        "title": [
            "ja_conference paperITEM00000009(public_open_access_open_access_simple)"
        ],
        "pubdate": {"attribute_name": "PubDate", "attribute_value": "2021-08-06"},
        "_buckets": {"deposit": "27202db8-aefc-4b85-b5ae-4921ac151ddf"},
        "_deposit": {
            "id": "{}".format(i),
            "pid": {"type": "depid", "value": "{}".format(i), "revision_id": 0},
            "owners": [1],
            "status": "published",
        },
        "item_title": "ja_conference paperITEM00000009(public_open_access_open_access_simple)",
        "author_link": ["4"],
        "item_type_id": "1",
        "publish_date": "2021-08-06",
        "publish_status": "0",
        "weko_shared_ids": [],
        "item_1617186331708": {
            "attribute_name": "Title",
            "attribute_value_mlt": [
                {
                    "subitem_1551255647225": "ja_conference paperITEM00000009(public_open_access_open_access_simple)",
                    "subitem_1551255648112": "ja",
                },
                {
                    "subitem_1551255647225": "en_conference paperITEM00000009(public_open_access_simple)",
                    "subitem_1551255648112": "en",
                },
            ],
        },
        "item_1617186385884": {
            "attribute_name": "Alternative Title",
            "attribute_value_mlt": [
                {
                    "subitem_1551255720400": "Alternative Title",
                    "subitem_1551255721061": "en",
                },
                {
                    "subitem_1551255720400": "Alternative Title",
                    "subitem_1551255721061": "ja",
                },
            ],
        },
        "item_1617186419668": {
            "attribute_name": "Creator",
            "attribute_type": "creator",
            "attribute_value_mlt": [
                {
                    "givenNames": [
                        {"givenName": "太郎", "givenNameLang": "ja"},
                        {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Taro", "givenNameLang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                    "creatorNames": [
                        {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                        {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                        {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                    ],
                    "nameIdentifiers": [
                        {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://orcid.org/",
                            "nameIdentifierScheme": "ORCID",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                            "nameIdentifierScheme": "CiNii",
                        },
                        {
                            "nameIdentifier": "zzzzzzz",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                            "nameIdentifierScheme": "KAKEN2",
                        },
                    ],
                    "creatorAffiliations": [
                        {
                            "affiliationNames": [
                                {
                                    "affiliationName": "University",
                                    "affiliationNameLang": "en",
                                }
                            ],
                            "affiliationNameIdentifiers": [
                                {
                                    "affiliationNameIdentifier": "0000000121691048",
                                    "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                    "affiliationNameIdentifierScheme": "ISNI",
                                }
                            ],
                        }
                    ],
                },
                {
                    "givenNames": [
                        {"givenName": "太郎", "givenNameLang": "ja"},
                        {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Taro", "givenNameLang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                    "creatorNames": [
                        {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                        {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                        {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                    ],
                    "nameIdentifiers": [
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://orcid.org/",
                            "nameIdentifierScheme": "ORCID",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                            "nameIdentifierScheme": "CiNii",
                        },
                        {
                            "nameIdentifier": "zzzzzzz",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                            "nameIdentifierScheme": "KAKEN2",
                        },
                    ],
                },
                {
                    "givenNames": [
                        {"givenName": "太郎", "givenNameLang": "ja"},
                        {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Taro", "givenNameLang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                    "creatorNames": [
                        {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                        {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                        {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                    ],
                    "nameIdentifiers": [
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://orcid.org/",
                            "nameIdentifierScheme": "ORCID",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                            "nameIdentifierScheme": "CiNii",
                        },
                        {
                            "nameIdentifier": "zzzzzzz",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                            "nameIdentifierScheme": "KAKEN2",
                        },
                    ],
                },
            ],
        },
        "item_1617186476635": {
            "attribute_name": "Access Rights",
            "attribute_value_mlt": [
                {
                    "subitem_1522299639480": "open access",
                    "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
                }
            ],
        },
        "item_1617186499011": {
            "attribute_name": "Rights",
            "attribute_value_mlt": [
                {
                    "subitem_1522650717957": "ja",
                    "subitem_1522650727486": "http://localhost",
                    "subitem_1522651041219": "Rights Information",
                }
            ],
        },
        "item_1617186609386": {
            "attribute_name": "Subject",
            "attribute_value_mlt": [
                {
                    "subitem_1522299896455": "ja",
                    "subitem_1522300014469": "Other",
                    "subitem_1522300048512": "http://localhost/",
                    "subitem_1523261968819": "Sibject1",
                }
            ],
        },
        "item_1617186626617": {
            "attribute_name": "Description",
            "attribute_value_mlt": [
                {
                    "subitem_description": "Description\nDescription<br/>Description",
                    "subitem_description_type": "Abstract",
                    "subitem_description_language": "en",
                },
                {
                    "subitem_description": "概要\n概要\n概要\n概要",
                    "subitem_description_type": "Abstract",
                    "subitem_description_language": "ja",
                },
            ],
        },
        "item_1617186643794": {
            "attribute_name": "Publisher",
            "attribute_value_mlt": [
                {"subitem_1522300295150": "en", "subitem_1522300316516": "Publisher"}
            ],
        },
        "item_1617186660861": {
            "attribute_name": "Date",
            "attribute_value_mlt": [
                {
                    "subitem_1522300695726": "Available",
                    "subitem_1522300722591": "2021-06-30",
                }
            ],
        },
        "item_1617186702042": {
            "attribute_name": "Language",
            "attribute_value_mlt": [{"subitem_1551255818386": "jpn"}],
        },
        "item_1617186783814": {
            "attribute_name": "Identifier",
            "attribute_value_mlt": [
                {
                    "subitem_identifier_uri": "http://localhost",
                    "subitem_identifier_type": "URI",
                }
            ],
        },
        "item_1617186859717": {
            "attribute_name": "Temporal",
            "attribute_value_mlt": [
                {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
            ],
        },
        "item_1617186882738": {
            "attribute_name": "Geo Location",
            "attribute_value_mlt": [
                {
                    "subitem_geolocation_place": [
                        {"subitem_geolocation_place_text": "Japan"}
                    ]
                }
            ],
        },
        "item_1617186901218": {
            "attribute_name": "Funding Reference",
            "attribute_value_mlt": [
                {
                    "subitem_1522399143519": {
                        "subitem_1522399281603": "ISNI",
                        "subitem_1522399333375": "http://xxx",
                    },
                    "subitem_1522399412622": [
                        {
                            "subitem_1522399416691": "en",
                            "subitem_1522737543681": "Funder Name",
                        }
                    ],
                    "subitem_1522399571623": {
                        "subitem_1522399585738": "Award URI",
                        "subitem_1522399628911": "Award Number",
                    },
                    "subitem_1522399651758": [
                        {
                            "subitem_1522721910626": "en",
                            "subitem_1522721929892": "Award Title",
                        }
                    ],
                }
            ],
        },
        "item_1617186920753": {
            "attribute_name": "Source Identifier",
            "attribute_value_mlt": [
                {
                    "subitem_1522646500366": "ISSN",
                    "subitem_1522646572813": "xxxx-xxxx-xxxx",
                }
            ],
        },
        "item_1617186941041": {
            "attribute_name": "Source Title",
            "attribute_value_mlt": [
                {"subitem_1522650068558": "en", "subitem_1522650091861": "Source Title"}
            ],
        },
        "item_1617186959569": {
            "attribute_name": "Volume Number",
            "attribute_value_mlt": [{"subitem_1551256328147": "1"}],
        },
        "item_1617186981471": {
            "attribute_name": "Issue Number",
            "attribute_value_mlt": [{"subitem_1551256294723": "111"}],
        },
        "item_1617186994930": {
            "attribute_name": "Number of Pages",
            "attribute_value_mlt": [{"subitem_1551256248092": "12"}],
        },
        "item_1617187024783": {
            "attribute_name": "Page Start",
            "attribute_value_mlt": [{"subitem_1551256198917": "1"}],
        },
        "item_1617187045071": {
            "attribute_name": "Page End",
            "attribute_value_mlt": [{"subitem_1551256185532": "3"}],
        },
        "item_1617187112279": {
            "attribute_name": "Degree Name",
            "attribute_value_mlt": [
                {"subitem_1551256126428": "Degree Name", "subitem_1551256129013": "en"}
            ],
        },
        "item_1617187136212": {
            "attribute_name": "Date Granted",
            "attribute_value_mlt": [{"subitem_1551256096004": "2021-06-30"}],
        },
        "item_1617187187528": {
            "attribute_name": "Conference",
            "attribute_value_mlt": [
                {
                    "subitem_1599711633003": [
                        {
                            "subitem_1599711636923": "Conference Name",
                            "subitem_1599711645590": "ja",
                        }
                    ],
                    "subitem_1599711655652": "1",
                    "subitem_1599711660052": [
                        {
                            "subitem_1599711680082": "Sponsor",
                            "subitem_1599711686511": "ja",
                        }
                    ],
                    "subitem_1599711699392": {
                        "subitem_1599711704251": "2020/12/11",
                        "subitem_1599711712451": "1",
                        "subitem_1599711727603": "12",
                        "subitem_1599711731891": "2000",
                        "subitem_1599711735410": "1",
                        "subitem_1599711739022": "12",
                        "subitem_1599711743722": "2020",
                        "subitem_1599711745532": "ja",
                    },
                    "subitem_1599711758470": [
                        {
                            "subitem_1599711769260": "Conference Venue",
                            "subitem_1599711775943": "ja",
                        }
                    ],
                    "subitem_1599711788485": [
                        {
                            "subitem_1599711798761": "Conference Place",
                            "subitem_1599711803382": "ja",
                        }
                    ],
                    "subitem_1599711813532": "JPN",
                }
            ],
        },
        "item_1617258105262": {
            "attribute_name": "Resource Type",
            "attribute_value_mlt": [
                {
                    "resourceuri": "http://purl.org/coar/resource_type/c_5794",
                    "resourcetype": "conference paper",
                }
            ],
        },
        "item_1617265215918": {
            "attribute_name": "Version Type",
            "attribute_value_mlt": [
                {
                    "subitem_1522305645492": "AO",
                    "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
                }
            ],
        },
        "item_1617349709064": {
            "attribute_name": "Contributor",
            "attribute_value_mlt": [
                {
                    "givenNames": [
                        {"givenName": "太郎", "givenNameLang": "ja"},
                        {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Taro", "givenNameLang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "contributorType": "ContactPerson",
                    "nameIdentifiers": [
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://orcid.org/",
                            "nameIdentifierScheme": "ORCID",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                            "nameIdentifierScheme": "CiNii",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                            "nameIdentifierScheme": "KAKEN2",
                        },
                    ],
                    "contributorMails": [{"contributorMail": "wekosoftware@nii.ac.jp"}],
                    "contributorNames": [
                        {"lang": "ja", "contributorName": "情報, 太郎"},
                        {"lang": "ja-Kana", "contributorName": "ジョウホウ, タロウ"},
                        {"lang": "en", "contributorName": "Joho, Taro"},
                    ],
                }
            ],
        },
        "item_1617349808926": {
            "attribute_name": "Version",
            "attribute_value_mlt": [{"subitem_1523263171732": "Version"}],
        },
        "item_1617351524846": {
            "attribute_name": "APC",
            "attribute_value_mlt": [{"subitem_1523260933860": "Unknown"}],
        },
        "item_1617353299429": {
            "attribute_name": "Relation",
            "attribute_value_mlt": [
                {
                    "subitem_1522306207484": "isVersionOf",
                    "subitem_1522306287251": {
                        "subitem_1522306382014": "arXiv",
                        "subitem_1522306436033": "xxxxx",
                    },
                    "subitem_1523320863692": [
                        {
                            "subitem_1523320867455": "en",
                            "subitem_1523320909613": "Related Title",
                        }
                    ],
                }
            ],
        },
        "item_1617605131499": {
            "attribute_name": "File",
            "attribute_type": "file",
            "attribute_value_mlt": [
                {
                    "url": {"url": "https://weko3.example.org/record/{0}/files/{1}".format(
                            i, filename
                        )},
                    "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                    "format": "text/plain",
                    "filename": "{}".format(filename),
                    "filesize": [{"value": "1 KB"}],
                    "mimetype": "{}".format(mimetype),
                    "accessrole": "open_restricted",
                    "version_id": "c1502853-c2f9-455d-8bec-f6e630e54b21",
                    "displaytype": "simple",
                    "terms": 'term_free',# if i==4 else '100',
                    "terms_content": 'test terms_content' if i==4 else 'test2 terms context',
                }
            ],
        },
        "item_1617610673286": {
            "attribute_name": "Rights Holder",
            "attribute_value_mlt": [
                {
                    "nameIdentifiers": [
                        {
                            "nameIdentifier": "xxxxxx",
                            "nameIdentifierURI": "https://orcid.org/",
                            "nameIdentifierScheme": "ORCID",
                        }
                    ],
                    "rightHolderNames": [
                        {
                            "rightHolderName": "Right Holder Name",
                            "rightHolderLanguage": "ja",
                        }
                    ],
                }
            ],
        },
        "item_1617620223087": {
            "attribute_name": "Heading",
            "attribute_value_mlt": [
                {
                    "subitem_1565671149650": "ja",
                    "subitem_1565671169640": "Banner Headline",
                    "subitem_1565671178623": "Subheading",
                },
                {
                    "subitem_1565671149650": "en",
                    "subitem_1565671169640": "Banner Headline",
                    "subitem_1565671178623": "Subheding",
                },
            ],
        },
        "item_1617944105607": {
            "attribute_name": "Degree Grantor",
            "attribute_value_mlt": [
                {
                    "subitem_1551256015892": [
                        {
                            "subitem_1551256027296": "xxxxxx",
                            "subitem_1551256029891": "kakenhi",
                        }
                    ],
                    "subitem_1551256037922": [
                        {
                            "subitem_1551256042287": "Degree Grantor Name",
                            "subitem_1551256047619": "en",
                        }
                    ],
                }
            ],
        },
        "relation_version_is_last": True,
    }

    item_data = {
        "id": "{}".format(i),
        "pid": {"type": "recid", "value": "{}".format(i), "revision_id": 0},
        "path": ["{}".format((i % 2) + 1)],
        "owner": 1,
        "title": "ja_conference paperITEM00000009(public_open_access_open_access_simple)",
        "owners": [1],
        "status": "draft",
        "$schema": "https://localhost:8443/items/jsonschema/1",
        "pubdate": "2021-08-06",
        "feedback_mail_list": [{"email": "wekosoftware@nii.ac.jp", "author_id": ""}],
        "item_1617186331708": [
            {
                "subitem_1551255647225": "ja_conference paperITEM00000009(public_open_access_open_access_simple)",
                "subitem_1551255648112": "ja",
            },
            {
                "subitem_1551255647225": "en_conference paperITEM00000009(public_open_access_simple)",
                "subitem_1551255648112": "en",
            },
        ],
        "item_1617186385884": [
            {
                "subitem_1551255720400": "Alternative Title",
                "subitem_1551255721061": "en",
            },
            {
                "subitem_1551255720400": "Alternative Title",
                "subitem_1551255721061": "ja",
            },
        ],
        "item_1617186419668": [
            {
                "givenNames": [
                    {"givenName": "太郎", "givenNameLang": "ja"},
                    {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                    {"givenName": "Taro", "givenNameLang": "en"},
                ],
                "familyNames": [
                    {"familyName": "情報", "familyNameLang": "ja"},
                    {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                    {"familyName": "Joho", "familyNameLang": "en"},
                ],
                "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                "creatorNames": [
                    {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                    {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                    {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                ],
                "nameIdentifiers": [
                    {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://orcid.org/",
                        "nameIdentifierScheme": "ORCID",
                    },
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://ci.nii.ac.jp/",
                        "nameIdentifierScheme": "CiNii",
                    },
                    {
                        "nameIdentifier": "zzzzzzz",
                        "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                        "nameIdentifierScheme": "KAKEN2",
                    },
                ],
                "creatorAffiliations": [
                    {
                        "affiliationNames": [
                            {
                                "affiliationName": "University",
                                "affiliationNameLang": "en",
                            }
                        ],
                        "affiliationNameIdentifiers": [
                            {
                                "affiliationNameIdentifier": "0000000121691048",
                                "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                "affiliationNameIdentifierScheme": "ISNI",
                            }
                        ],
                    }
                ],
            },
            {
                "givenNames": [
                    {"givenName": "太郎", "givenNameLang": "ja"},
                    {"givenName": "タロ", "givenNameLang": "ja-Kana"},
                    {"givenName": "Taro", "givenNameLang": "en"},
                ],
                "familyNames": [
                    {"familyName": "情報", "familyNameLang": "ja"},
                    {"familyName": "ジウホウ", "familyNameLang": "ja-Kana"},
                    {"familyName": "Joho", "familyNameLang": "en"},
                ],
                "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                "creatorNames": [
                    {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                    {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                    {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                ],
                "nameIdentifiers": [
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://orcid.org/",
                        "nameIdentifierScheme": "ORCID",
                    },
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://ci.nii.ac.jp/",
                        "nameIdentifierScheme": "CiNii",
                    },
                    {
                        "nameIdentifier": "zzzzzzz",
                        "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                        "nameIdentifierScheme": "KAKEN2",
                    },
                ],
            },
            {
                "givenNames": [
                    {"givenName": "太郎", "givenNameLang": "ja"},
                    {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                    {"givenName": "Taro", "givenNameLang": "en"},
                ],
                "familyNames": [
                    {"familyName": "情報", "familyNameLang": "ja"},
                    {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                    {"familyName": "Joho", "familyNameLang": "en"},
                ],
                "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                "creatorNames": [
                    {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                    {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                    {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                ],
                "nameIdentifiers": [
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://orcid.org/",
                        "nameIdentifierScheme": "ORCID",
                    },
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://ci.nii.ac.jp/",
                        "nameIdentifierScheme": "CiNii",
                    },
                    {
                        "nameIdentifier": "zzzzzzz",
                        "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                        "nameIdentifierScheme": "KAKEN2",
                    },
                ],
            },
        ],
        "item_1617186476635": {
            "subitem_1522299639480": "open access",
            "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
        },
        "item_1617186499011": [
            {
                "subitem_1522650717957": "ja",
                "subitem_1522650727486": "http://localhost",
                "subitem_1522651041219": "Rights Information",
            }
        ],
        "item_1617186609386": [
            {
                "subitem_1522299896455": "ja",
                "subitem_1522300014469": "Other",
                "subitem_1522300048512": "http://localhost/",
                "subitem_1523261968819": "Sibject1",
            }
        ],
        "item_1617186626617": [
            {
                "subitem_description": "Description\nDescription<br/>Description",
                "subitem_description_type": "Abstract",
                "subitem_description_language": "en",
            },
            {
                "subitem_description": "概要\n概要\n概要\n概要",
                "subitem_description_type": "Abstract",
                "subitem_description_language": "ja",
            },
        ],
        "item_1617186643794": [
            {"subitem_1522300295150": "en", "subitem_1522300316516": "Publisher"}
        ],
        "item_1617186660861": [
            {
                "subitem_1522300695726": "Available",
                "subitem_1522300722591": "2021-06-30",
            }
        ],
        "item_1617186702042": [{"subitem_1551255818386": "jpn"}],
        "item_1617186783814": [
            {
                "subitem_identifier_uri": "http://localhost",
                "subitem_identifier_type": "URI",
            }
        ],
        "item_1617186859717": [
            {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
        ],
        "item_1617186882738": [
            {"subitem_geolocation_place": [{"subitem_geolocation_place_text": "Japan"}]}
        ],
        "item_1617186901218": [
            {
                "subitem_1522399143519": {
                    "subitem_1522399281603": "ISNI",
                    "subitem_1522399333375": "http://xxx",
                },
                "subitem_1522399412622": [
                    {
                        "subitem_1522399416691": "en",
                        "subitem_1522737543681": "Funder Name",
                    }
                ],
                "subitem_1522399571623": {
                    "subitem_1522399585738": "Award URI",
                    "subitem_1522399628911": "Award Number",
                },
                "subitem_1522399651758": [
                    {
                        "subitem_1522721910626": "en",
                        "subitem_1522721929892": "Award Title",
                    }
                ],
            }
        ],
        "item_1617186920753": [
            {"subitem_1522646500366": "ISSN", "subitem_1522646572813": "xxxx-xxxx-xxxx"}
        ],
        "item_1617186941041": [
            {"subitem_1522650068558": "en", "subitem_1522650091861": "Source Title"}
        ],
        "item_1617186959569": {"subitem_1551256328147": "1"},
        "item_1617186981471": {"subitem_1551256294723": "111"},
        "item_1617186994930": {"subitem_1551256248092": "12"},
        "item_1617187024783": {"subitem_1551256198917": "1"},
        "item_1617187045071": {"subitem_1551256185532": "3"},
        "item_1617187112279": [
            {"subitem_1551256126428": "Degree Name", "subitem_1551256129013": "en"}
        ],
        "item_1617187136212": {"subitem_1551256096004": "2021-06-30"},
        "item_1617187187528": [
            {
                "subitem_1599711633003": [
                    {
                        "subitem_1599711636923": "Conference Name",
                        "subitem_1599711645590": "ja",
                    }
                ],
                "subitem_1599711655652": "1",
                "subitem_1599711660052": [
                    {"subitem_1599711680082": "Sponsor", "subitem_1599711686511": "ja"}
                ],
                "subitem_1599711699392": {
                    "subitem_1599711704251": "2020/12/11",
                    "subitem_1599711712451": "1",
                    "subitem_1599711727603": "12",
                    "subitem_1599711731891": "2000",
                    "subitem_1599711735410": "1",
                    "subitem_1599711739022": "12",
                    "subitem_1599711743722": "2020",
                    "subitem_1599711745532": "ja",
                },
                "subitem_1599711758470": [
                    {
                        "subitem_1599711769260": "Conference Venue",
                        "subitem_1599711775943": "ja",
                    }
                ],
                "subitem_1599711788485": [
                    {
                        "subitem_1599711798761": "Conference Place",
                        "subitem_1599711803382": "ja",
                    }
                ],
                "subitem_1599711813532": "JPN",
            }
        ],
        "item_1617258105262": {
            "resourceuri": "http://purl.org/coar/resource_type/c_5794",
            "resourcetype": "conference paper",
        },
        "item_1617265215918": {
            "subitem_1522305645492": "AO",
            "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
        },
        "item_1617349709064": [
            {
                "givenNames": [
                    {"givenName": "太郎", "givenNameLang": "ja"},
                    {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                    {"givenName": "Taro", "givenNameLang": "en"},
                ],
                "familyNames": [
                    {"familyName": "情報", "familyNameLang": "ja"},
                    {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                    {"familyName": "Joho", "familyNameLang": "en"},
                ],
                "contributorType": "ContactPerson",
                "nameIdentifiers": [
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://orcid.org/",
                        "nameIdentifierScheme": "ORCID",
                    },
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://ci.nii.ac.jp/",
                        "nameIdentifierScheme": "CiNii",
                    },
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                        "nameIdentifierScheme": "KAKEN2",
                    },
                ],
                "contributorMails": [{"contributorMail": "wekosoftware@nii.ac.jp"}],
                "contributorNames": [
                    {"lang": "ja", "contributorName": "情報, 太郎"},
                    {"lang": "ja-Kana", "contributorName": "ジョウホ, タロウ"},
                    {"lang": "en", "contributorName": "Joho, Taro"},
                ],
            }
        ],
        "item_1617349808926": {"subitem_1523263171732": "Version"},
        "item_1617351524846": {"subitem_1523260933860": "Unknown"},
        "item_1617353299429": [
            {
                "subitem_1522306207484": "isVersionOf",
                "subitem_1522306287251": {
                    "subitem_1522306382014": "arXiv",
                    "subitem_1522306436033": "xxxxx",
                },
                "subitem_1523320863692": [
                    {
                        "subitem_1523320867455": "en",
                        "subitem_1523320909613": "Related Title",
                    }
                ],
            }
        ],
        "item_1617605131499": [
            {
                "url": {
                    "url": "https://weko3.example.org/record/{0}/files/{1}".format(i,filename)
                },
                "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                "format": "{}".format(mimetype),
                "filename": "{}".format(filename),
                "filesize": [{"value": "1 KB"}],
                "mimetype": "{}".format(mimetype),
                "accessrole": "open_restricted",
                "version_id": "c1502853-c2f9-455d-8bec-f6e630e54b21",
                "displaytype": "simple",
                "terms": 'term_free', #if i==4 else '100',
                "terms_content": 'test terms_content' if i==4 else 'test2 terms context',
            }
        ],
        "item_1617610673286": [
            {
                "nameIdentifiers": [
                    {
                        "nameIdentifier": "xxxxxx",
                        "nameIdentifierURI": "https://orcid.org/",
                        "nameIdentifierScheme": "ORCID",
                    }
                ],
                "rightHolderNames": [
                    {
                        "rightHolderName": "Right Holder Name",
                        "rightHolderLanguage": "ja",
                    }
                ],
            }
        ],
        "item_1617620223087": [
            {
                "subitem_1565671149650": "ja",
                "subitem_1565671169640": "Banner Headline",
                "subitem_1565671178623": "Subheading",
            },
            {
                "subitem_1565671149650": "en",
                "subitem_1565671169640": "Banner Headline",
                "subitem_1565671178623": "Subheding",
            },
        ],
        "item_1617944105607": [
            {
                "subitem_1551256015892": [
                    {
                        "subitem_1551256027296": "xxxxxx",
                        "subitem_1551256029891": "kakenhi",
                    }
                ],
                "subitem_1551256037922": [
                    {
                        "subitem_1551256042287": "Degree Grantor Name",
                        "subitem_1551256047619": "en",
                    }
                ],
            }
        ],
    }

    rec_uuid = uuid.uuid4()

    recid = PersistentIdentifier.create(
        "recid",
        str(i),
        object_type="rec",
        object_uuid=rec_uuid,
        status=PIDStatus.REGISTERED,
    )
    depid = PersistentIdentifier.create(
        "depid",
        str(i),
        object_type="rec",
        object_uuid=rec_uuid,
        status=PIDStatus.REGISTERED,
    )
    parent = None
    doi = None
    hdl = None
    recid_v1 = PersistentIdentifier.create(
        "recid",
        str(i + 0.1),
        object_type="rec",
        object_uuid=rec_uuid,
        status=PIDStatus.REGISTERED,
    )
    rec_uuid2 = uuid.uuid4()
    depid_v1 = PersistentIdentifier.create(
        "depid",
        str(i + 0.1),
        object_type="rec",
        object_uuid=rec_uuid2,
        status=PIDStatus.REGISTERED,
    )
    parent = PersistentIdentifier.create(
        "parent",
        "parent:{}".format(i),
        object_type="rec",
        object_uuid=rec_uuid2,
        status=PIDStatus.REGISTERED,
    )

    h1 = PIDVersioning(parent=parent)
    h1.insert_child(child=recid)
    h1.insert_child(child=recid_v1)
    RecordDraft.link(recid, depid)
    RecordDraft.link(recid_v1, depid_v1)

    if i % 2 == 1:
        doi = PersistentIdentifier.create(
            "doi",
            "https://doi.org/10.xyz/{}".format((str(i)).zfill(10)),
            object_type="rec",
            object_uuid=rec_uuid,
            status=PIDStatus.REGISTERED,
        )
        hdl = PersistentIdentifier.create(
            "hdl",
            "https://hdl.handle.net/0000/{}".format((str(i)).zfill(10)),
            object_type="rec",
            object_uuid=rec_uuid,
            status=PIDStatus.REGISTERED,
        )

    record = WekoRecord.create(record_data, id_=rec_uuid)
    # from six import BytesIO
    import base64

    bucket = Bucket.create()
    record_buckets = RecordsBuckets.create(record=record.model, bucket=bucket)

    # stream = BytesIO(b"Hello, World")
    obj = None
    with open(filepath, "rb") as f:
        stream = BytesIO(f.read())
        record.files[filename] = stream
        record["item_1617605131499"]["attribute_value_mlt"][0]["file"] = (
            base64.b64encode(stream.getvalue())
        ).decode("utf-8")
    with open(filepath, "rb") as f:
        obj = ObjectVersion.create(bucket=bucket.id, key=filename, stream=f)
    deposit = aWekoDeposit(record, record.model)
    deposit.commit()
    record["item_1617605131499"]["attribute_value_mlt"][0]["version_id"] = str(
        obj.version_id
    )

    record_data["content"] = [
        {
            "date": [{"dateValue": "2021-07-12", "dateType": "Available"}],
            "accessrole": "open_restricted",
            #"provide" : [{"role": userId, "workflow": workflowId }],
            #"terms"	:"term_free","termsDescription":"利用規約本文",
            "displaytype": "simple",
            "filename": filename,
            "attachment": {},
            "format": mimetype,
            "mimetype": mimetype,
            "filesize": [{"value": "1 KB"}],
            "version_id": "{}".format(obj.version_id),
            "url": {"url": "http://localhost/record/{0}/files/{1}".format(i, filename)},
            "file": (base64.b64encode(stream.getvalue())).decode("utf-8"),
        }
    ]

    indexer.upload_metadata(record_data, rec_uuid, 1, False)
    item = ItemsMetadata.create(item_data, id_=rec_uuid, item_type_id=1)

    record_v1 = WekoRecord.create(record_data, id_=rec_uuid2)
    # from six import BytesIO
    import base64

    bucket_v1 = Bucket.create()
    record_buckets = RecordsBuckets.create(record=record_v1.model, bucket=bucket_v1)
    # stream = BytesIO(b"Hello, World")
    record_v1.files[filename] = stream
    obj_v1 = ObjectVersion.create(bucket=bucket_v1.id, key=filename, stream=stream)
    record_v1["item_1617605131499"]["attribute_value_mlt"][0]["file"] = (
        base64.b64encode(stream.getvalue())
    ).decode("utf-8")
    deposit_v1 = aWekoDeposit(record_v1, record_v1.model)
    deposit_v1.commit()
    record_v1["item_1617605131499"]["attribute_value_mlt"][0]["version_id"] = str(
        obj_v1.version_id
    )

    record_data_v1 = copy.deepcopy(record_data)
    record_data_v1["content"] = [
        {
            "date": [{"dateValue": "2021-07-12", "dateType": "Available"}],
            "accessrole": "open_restricted",
            "provide" : [{"role" :userId, "workflow": workflowId }],
            "terms"	:"term_free","termsDescription":"利用規約本文",
            "displaytype": "simple",
            "filename": filename,
            "attachment": {},
            "format": mimetype,
            "mimetype": mimetype,
            "filesize": [{"value": "1 KB"}],
            "version_id": "{}".format(obj_v1.version_id),
            "url": {"url": "http://localhost/record/{0}/files/{1}".format(i, filename)},
            "file": (base64.b64encode(stream.getvalue())).decode("utf-8"),
        }
    ]
    indexer.upload_metadata(record_data_v1, rec_uuid2, 1, False)
    item_v1 = ItemsMetadata.create(item_data, id_=rec_uuid2, item_type_id=1)

    db.session.flush()
    # db.session.expunge_all()

    return {
        "depid": depid,
        "recid": recid,
        "parent": parent,
        "doi": doi,
        "hdl": hdl,
        "record": record,
        "record_data": record_data,
        "item": item,
        "item_data": item_data,
        "deposit": deposit,
        "filename": filename,
        "mimetype": mimetype,
        "obj": obj,
    }

def make_record_restricted_open_login(db, indexer, i, filepath, filename, mimetype ,userId ,workflowId, roles):
    """ make open_resirected open_date record"""
    record_data = {
        "_oai": {"id": "oai:weko3.example.org:000000{:02d}".format(i), "sets": ["{}".format((i % 2) + 1)]},
        "path": ["{}".format((i % 2) + 1)],
        "owner": 1,
        "recid": "{}".format(i),
        "title": [
            "ja_conference paperITEM00000009(public_open_access_open_access_simple)"
        ],
        "pubdate": {"attribute_name": "PubDate", "attribute_value": "2021-08-06"},
        "_buckets": {"deposit": "27202db8-aefc-4b85-b5ae-4921ac151ddf"},
        "_deposit": {
            "id": "{}".format(i),
            "pid": {"type": "depid", "value": "{}".format(i), "revision_id": 0},
            "owners": [1],
            "status": "published",
        },
        "item_title": "ja_conference paperITEM00000009(public_open_access_open_access_simple)",
        "author_link": ["4"],
        "item_type_id": "1",
        "publish_date": "2021-08-06",
        "publish_status": "0",
        "weko_shared_ids": [],
        "item_1617186331708": {
            "attribute_name": "Title",
            "attribute_value_mlt": [
                {
                    "subitem_1551255647225": "ja_conference paperITEM00000009(public_open_access_open_access_simple)",
                    "subitem_1551255648112": "ja",
                },
                {
                    "subitem_1551255647225": "en_conference paperITEM00000009(public_open_access_simple)",
                    "subitem_1551255648112": "en",
                },
            ],
        },
        "item_1617186385884": {
            "attribute_name": "Alternative Title",
            "attribute_value_mlt": [
                {
                    "subitem_1551255720400": "Alternative Title",
                    "subitem_1551255721061": "en",
                },
                {
                    "subitem_1551255720400": "Alternative Title",
                    "subitem_1551255721061": "ja",
                },
            ],
        },
        "item_1617186419668": {
            "attribute_name": "Creator",
            "attribute_type": "creator",
            "attribute_value_mlt": [
                {
                    "givenNames": [
                        {"givenName": "太郎", "givenNameLang": "ja"},
                        {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Taro", "givenNameLang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                    "creatorNames": [
                        {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                        {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                        {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                    ],
                    "nameIdentifiers": [
                        {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://orcid.org/",
                            "nameIdentifierScheme": "ORCID",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                            "nameIdentifierScheme": "CiNii",
                        },
                        {
                            "nameIdentifier": "zzzzzzz",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                            "nameIdentifierScheme": "KAKEN2",
                        },
                    ],
                    "creatorAffiliations": [
                        {
                            "affiliationNames": [
                                {
                                    "affiliationName": "University",
                                    "affiliationNameLang": "en",
                                }
                            ],
                            "affiliationNameIdentifiers": [
                                {
                                    "affiliationNameIdentifier": "0000000121691048",
                                    "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                    "affiliationNameIdentifierScheme": "ISNI",
                                }
                            ],
                        }
                    ],
                },
                {
                    "givenNames": [
                        {"givenName": "太郎", "givenNameLang": "ja"},
                        {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Taro", "givenNameLang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                    "creatorNames": [
                        {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                        {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                        {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                    ],
                    "nameIdentifiers": [
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://orcid.org/",
                            "nameIdentifierScheme": "ORCID",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                            "nameIdentifierScheme": "CiNii",
                        },
                        {
                            "nameIdentifier": "zzzzzzz",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                            "nameIdentifierScheme": "KAKEN2",
                        },
                    ],
                },
                {
                    "givenNames": [
                        {"givenName": "太郎", "givenNameLang": "ja"},
                        {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Taro", "givenNameLang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                    "creatorNames": [
                        {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                        {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                        {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                    ],
                    "nameIdentifiers": [
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://orcid.org/",
                            "nameIdentifierScheme": "ORCID",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                            "nameIdentifierScheme": "CiNii",
                        },
                        {
                            "nameIdentifier": "zzzzzzz",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                            "nameIdentifierScheme": "KAKEN2",
                        },
                    ],
                },
            ],
        },
        "item_1617186476635": {
            "attribute_name": "Access Rights",
            "attribute_value_mlt": [
                {
                    "subitem_1522299639480": "open access",
                    "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
                }
            ],
        },
        "item_1617186499011": {
            "attribute_name": "Rights",
            "attribute_value_mlt": [
                {
                    "subitem_1522650717957": "ja",
                    "subitem_1522650727486": "http://localhost",
                    "subitem_1522651041219": "Rights Information",
                }
            ],
        },
        "item_1617186609386": {
            "attribute_name": "Subject",
            "attribute_value_mlt": [
                {
                    "subitem_1522299896455": "ja",
                    "subitem_1522300014469": "Other",
                    "subitem_1522300048512": "http://localhost/",
                    "subitem_1523261968819": "Sibject1",
                }
            ],
        },
        "item_1617186626617": {
            "attribute_name": "Description",
            "attribute_value_mlt": [
                {
                    "subitem_description": "Description\nDescription<br/>Description",
                    "subitem_description_type": "Abstract",
                    "subitem_description_language": "en",
                },
                {
                    "subitem_description": "概要\n概要\n概要\n概要",
                    "subitem_description_type": "Abstract",
                    "subitem_description_language": "ja",
                },
            ],
        },
        "item_1617186643794": {
            "attribute_name": "Publisher",
            "attribute_value_mlt": [
                {"subitem_1522300295150": "en", "subitem_1522300316516": "Publisher"}
            ],
        },
        "item_1617186660861": {
            "attribute_name": "Date",
            "attribute_value_mlt": [
                {
                    "subitem_1522300695726": "Available",
                    "subitem_1522300722591": "2021-06-30",
                }
            ],
        },
        "item_1617186702042": {
            "attribute_name": "Language",
            "attribute_value_mlt": [{"subitem_1551255818386": "jpn"}],
        },
        "item_1617186783814": {
            "attribute_name": "Identifier",
            "attribute_value_mlt": [
                {
                    "subitem_identifier_uri": "http://localhost",
                    "subitem_identifier_type": "URI",
                }
            ],
        },
        "item_1617186859717": {
            "attribute_name": "Temporal",
            "attribute_value_mlt": [
                {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
            ],
        },
        "item_1617186882738": {
            "attribute_name": "Geo Location",
            "attribute_value_mlt": [
                {
                    "subitem_geolocation_place": [
                        {"subitem_geolocation_place_text": "Japan"}
                    ]
                }
            ],
        },
        "item_1617186901218": {
            "attribute_name": "Funding Reference",
            "attribute_value_mlt": [
                {
                    "subitem_1522399143519": {
                        "subitem_1522399281603": "ISNI",
                        "subitem_1522399333375": "http://xxx",
                    },
                    "subitem_1522399412622": [
                        {
                            "subitem_1522399416691": "en",
                            "subitem_1522737543681": "Funder Name",
                        }
                    ],
                    "subitem_1522399571623": {
                        "subitem_1522399585738": "Award URI",
                        "subitem_1522399628911": "Award Number",
                    },
                    "subitem_1522399651758": [
                        {
                            "subitem_1522721910626": "en",
                            "subitem_1522721929892": "Award Title",
                        }
                    ],
                }
            ],
        },
        "item_1617186920753": {
            "attribute_name": "Source Identifier",
            "attribute_value_mlt": [
                {
                    "subitem_1522646500366": "ISSN",
                    "subitem_1522646572813": "xxxx-xxxx-xxxx",
                }
            ],
        },
        "item_1617186941041": {
            "attribute_name": "Source Title",
            "attribute_value_mlt": [
                {"subitem_1522650068558": "en", "subitem_1522650091861": "Source Title"}
            ],
        },
        "item_1617186959569": {
            "attribute_name": "Volume Number",
            "attribute_value_mlt": [{"subitem_1551256328147": "1"}],
        },
        "item_1617186981471": {
            "attribute_name": "Issue Number",
            "attribute_value_mlt": [{"subitem_1551256294723": "111"}],
        },
        "item_1617186994930": {
            "attribute_name": "Number of Pages",
            "attribute_value_mlt": [{"subitem_1551256248092": "12"}],
        },
        "item_1617187024783": {
            "attribute_name": "Page Start",
            "attribute_value_mlt": [{"subitem_1551256198917": "1"}],
        },
        "item_1617187045071": {
            "attribute_name": "Page End",
            "attribute_value_mlt": [{"subitem_1551256185532": "3"}],
        },
        "item_1617187112279": {
            "attribute_name": "Degree Name",
            "attribute_value_mlt": [
                {"subitem_1551256126428": "Degree Name", "subitem_1551256129013": "en"}
            ],
        },
        "item_1617187136212": {
            "attribute_name": "Date Granted",
            "attribute_value_mlt": [{"subitem_1551256096004": "2021-06-30"}],
        },
        "item_1617187187528": {
            "attribute_name": "Conference",
            "attribute_value_mlt": [
                {
                    "subitem_1599711633003": [
                        {
                            "subitem_1599711636923": "Conference Name",
                            "subitem_1599711645590": "ja",
                        }
                    ],
                    "subitem_1599711655652": "1",
                    "subitem_1599711660052": [
                        {
                            "subitem_1599711680082": "Sponsor",
                            "subitem_1599711686511": "ja",
                        }
                    ],
                    "subitem_1599711699392": {
                        "subitem_1599711704251": "2020/12/11",
                        "subitem_1599711712451": "1",
                        "subitem_1599711727603": "12",
                        "subitem_1599711731891": "2000",
                        "subitem_1599711735410": "1",
                        "subitem_1599711739022": "12",
                        "subitem_1599711743722": "2020",
                        "subitem_1599711745532": "ja",
                    },
                    "subitem_1599711758470": [
                        {
                            "subitem_1599711769260": "Conference Venue",
                            "subitem_1599711775943": "ja",
                        }
                    ],
                    "subitem_1599711788485": [
                        {
                            "subitem_1599711798761": "Conference Place",
                            "subitem_1599711803382": "ja",
                        }
                    ],
                    "subitem_1599711813532": "JPN",
                }
            ],
        },
        "item_1617258105262": {
            "attribute_name": "Resource Type",
            "attribute_value_mlt": [
                {
                    "resourceuri": "http://purl.org/coar/resource_type/c_5794",
                    "resourcetype": "conference paper",
                }
            ],
        },
        "item_1617265215918": {
            "attribute_name": "Version Type",
            "attribute_value_mlt": [
                {
                    "subitem_1522305645492": "AO",
                    "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
                }
            ],
        },
        "item_1617349709064": {
            "attribute_name": "Contributor",
            "attribute_value_mlt": [
                {
                    "givenNames": [
                        {"givenName": "太郎", "givenNameLang": "ja"},
                        {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Taro", "givenNameLang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "contributorType": "ContactPerson",
                    "nameIdentifiers": [
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://orcid.org/",
                            "nameIdentifierScheme": "ORCID",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                            "nameIdentifierScheme": "CiNii",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                            "nameIdentifierScheme": "KAKEN2",
                        },
                    ],
                    "contributorMails": [{"contributorMail": "wekosoftware@nii.ac.jp"}],
                    "contributorNames": [
                        {"lang": "ja", "contributorName": "情報, 太郎"},
                        {"lang": "ja-Kana", "contributorName": "ジョウホウ, タロウ"},
                        {"lang": "en", "contributorName": "Joho, Taro"},
                    ],
                }
            ],
        },
        "item_1617349808926": {
            "attribute_name": "Version",
            "attribute_value_mlt": [{"subitem_1523263171732": "Version"}],
        },
        "item_1617351524846": {
            "attribute_name": "APC",
            "attribute_value_mlt": [{"subitem_1523260933860": "Unknown"}],
        },
        "item_1617353299429": {
            "attribute_name": "Relation",
            "attribute_value_mlt": [
                {
                    "subitem_1522306207484": "isVersionOf",
                    "subitem_1522306287251": {
                        "subitem_1522306382014": "arXiv",
                        "subitem_1522306436033": "xxxxx",
                    },
                    "subitem_1523320863692": [
                        {
                            "subitem_1523320867455": "en",
                            "subitem_1523320909613": "Related Title",
                        }
                    ],
                }
            ],
        },
        "item_1617605131499": {
            "attribute_name": "File",
            "attribute_type": "file",
            "attribute_value_mlt": [
                {
                    "url": {"url": "https://weko3.example.org/record/{0}/files/{1}".format(
                            i, filename
                        )},
                    "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                    "format": "text/plain",
                    "filename": "{}".format(filename),
                    "filesize": [{"value": "1 KB"}],
                    "mimetype": "{}".format(mimetype),
                    "accessrole": "open_login",
                    "roles": roles,
                    "version_id": "c1502853-c2f9-455d-8bec-f6e630e54b21",
                    "displaytype": "simple",
                    "provide": [{"workflow": 1, "role": 1}],
                    "terms": 'term_free' if i%2==0 else '100',
                    "terms_content": 'test terms_content' if i%2==0 else 'terms context',
                }
            ],
        },
        "item_1617610673286": {
            "attribute_name": "Rights Holder",
            "attribute_value_mlt": [
                {
                    "nameIdentifiers": [
                        {
                            "nameIdentifier": "xxxxxx",
                            "nameIdentifierURI": "https://orcid.org/",
                            "nameIdentifierScheme": "ORCID",
                        }
                    ],
                    "rightHolderNames": [
                        {
                            "rightHolderName": "Right Holder Name",
                            "rightHolderLanguage": "ja",
                        }
                    ],
                }
            ],
        },
        "item_1617620223087": {
            "attribute_name": "Heading",
            "attribute_value_mlt": [
                {
                    "subitem_1565671149650": "ja",
                    "subitem_1565671169640": "Banner Headline",
                    "subitem_1565671178623": "Subheading",
                },
                {
                    "subitem_1565671149650": "en",
                    "subitem_1565671169640": "Banner Headline",
                    "subitem_1565671178623": "Subheding",
                },
            ],
        },
        "item_1617944105607": {
            "attribute_name": "Degree Grantor",
            "attribute_value_mlt": [
                {
                    "subitem_1551256015892": [
                        {
                            "subitem_1551256027296": "xxxxxx",
                            "subitem_1551256029891": "kakenhi",
                        }
                    ],
                    "subitem_1551256037922": [
                        {
                            "subitem_1551256042287": "Degree Grantor Name",
                            "subitem_1551256047619": "en",
                        }
                    ],
                }
            ],
        },
        "relation_version_is_last": True,
    }

    item_data = {
        "id": "{}".format(i),
        "pid": {"type": "recid", "value": "{}".format(i), "revision_id": 0},
        "path": ["{}".format((i % 2) + 1)],
        "owner": 1,
        "title": "ja_conference paperITEM00000009(public_open_access_open_access_simple)",
        "owners": [1],
        "status": "draft",
        "$schema": "https://localhost:8443/items/jsonschema/1",
        "pubdate": "2021-08-06",
        "feedback_mail_list": [{"email": "wekosoftware@nii.ac.jp", "author_id": ""}],
        "item_1617186331708": [
            {
                "subitem_1551255647225": "ja_conference paperITEM00000009(public_open_access_open_access_simple)",
                "subitem_1551255648112": "ja",
            },
            {
                "subitem_1551255647225": "en_conference paperITEM00000009(public_open_access_simple)",
                "subitem_1551255648112": "en",
            },
        ],
        "item_1617186385884": [
            {
                "subitem_1551255720400": "Alternative Title",
                "subitem_1551255721061": "en",
            },
            {
                "subitem_1551255720400": "Alternative Title",
                "subitem_1551255721061": "ja",
            },
        ],
        "item_1617186419668": [
            {
                "givenNames": [
                    {"givenName": "太郎", "givenNameLang": "ja"},
                    {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                    {"givenName": "Taro", "givenNameLang": "en"},
                ],
                "familyNames": [
                    {"familyName": "情報", "familyNameLang": "ja"},
                    {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                    {"familyName": "Joho", "familyNameLang": "en"},
                ],
                "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                "creatorNames": [
                    {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                    {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                    {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                ],
                "nameIdentifiers": [
                    {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://orcid.org/",
                        "nameIdentifierScheme": "ORCID",
                    },
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://ci.nii.ac.jp/",
                        "nameIdentifierScheme": "CiNii",
                    },
                    {
                        "nameIdentifier": "zzzzzzz",
                        "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                        "nameIdentifierScheme": "KAKEN2",
                    },
                ],
                "creatorAffiliations": [
                    {
                        "affiliationNames": [
                            {
                                "affiliationName": "University",
                                "affiliationNameLang": "en",
                            }
                        ],
                        "affiliationNameIdentifiers": [
                            {
                                "affiliationNameIdentifier": "0000000121691048",
                                "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                "affiliationNameIdentifierScheme": "ISNI",
                            }
                        ],
                    }
                ],
            },
            {
                "givenNames": [
                    {"givenName": "太郎", "givenNameLang": "ja"},
                    {"givenName": "タロ", "givenNameLang": "ja-Kana"},
                    {"givenName": "Taro", "givenNameLang": "en"},
                ],
                "familyNames": [
                    {"familyName": "情報", "familyNameLang": "ja"},
                    {"familyName": "ジウホウ", "familyNameLang": "ja-Kana"},
                    {"familyName": "Joho", "familyNameLang": "en"},
                ],
                "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                "creatorNames": [
                    {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                    {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                    {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                ],
                "nameIdentifiers": [
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://orcid.org/",
                        "nameIdentifierScheme": "ORCID",
                    },
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://ci.nii.ac.jp/",
                        "nameIdentifierScheme": "CiNii",
                    },
                    {
                        "nameIdentifier": "zzzzzzz",
                        "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                        "nameIdentifierScheme": "KAKEN2",
                    },
                ],
            },
            {
                "givenNames": [
                    {"givenName": "太郎", "givenNameLang": "ja"},
                    {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                    {"givenName": "Taro", "givenNameLang": "en"},
                ],
                "familyNames": [
                    {"familyName": "情報", "familyNameLang": "ja"},
                    {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                    {"familyName": "Joho", "familyNameLang": "en"},
                ],
                "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                "creatorNames": [
                    {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                    {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                    {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                ],
                "nameIdentifiers": [
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://orcid.org/",
                        "nameIdentifierScheme": "ORCID",
                    },
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://ci.nii.ac.jp/",
                        "nameIdentifierScheme": "CiNii",
                    },
                    {
                        "nameIdentifier": "zzzzzzz",
                        "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                        "nameIdentifierScheme": "KAKEN2",
                    },
                ],
            },
        ],
        "item_1617186476635": {
            "subitem_1522299639480": "open access",
            "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
        },
        "item_1617186499011": [
            {
                "subitem_1522650717957": "ja",
                "subitem_1522650727486": "http://localhost",
                "subitem_1522651041219": "Rights Information",
            }
        ],
        "item_1617186609386": [
            {
                "subitem_1522299896455": "ja",
                "subitem_1522300014469": "Other",
                "subitem_1522300048512": "http://localhost/",
                "subitem_1523261968819": "Sibject1",
            }
        ],
        "item_1617186626617": [
            {
                "subitem_description": "Description\nDescription<br/>Description",
                "subitem_description_type": "Abstract",
                "subitem_description_language": "en",
            },
            {
                "subitem_description": "概要\n概要\n概要\n概要",
                "subitem_description_type": "Abstract",
                "subitem_description_language": "ja",
            },
        ],
        "item_1617186643794": [
            {"subitem_1522300295150": "en", "subitem_1522300316516": "Publisher"}
        ],
        "item_1617186660861": [
            {
                "subitem_1522300695726": "Available",
                "subitem_1522300722591": "2021-06-30",
            }
        ],
        "item_1617186702042": [{"subitem_1551255818386": "jpn"}],
        "item_1617186783814": [
            {
                "subitem_identifier_uri": "http://localhost",
                "subitem_identifier_type": "URI",
            }
        ],
        "item_1617186859717": [
            {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
        ],
        "item_1617186882738": [
            {"subitem_geolocation_place": [{"subitem_geolocation_place_text": "Japan"}]}
        ],
        "item_1617186901218": [
            {
                "subitem_1522399143519": {
                    "subitem_1522399281603": "ISNI",
                    "subitem_1522399333375": "http://xxx",
                },
                "subitem_1522399412622": [
                    {
                        "subitem_1522399416691": "en",
                        "subitem_1522737543681": "Funder Name",
                    }
                ],
                "subitem_1522399571623": {
                    "subitem_1522399585738": "Award URI",
                    "subitem_1522399628911": "Award Number",
                },
                "subitem_1522399651758": [
                    {
                        "subitem_1522721910626": "en",
                        "subitem_1522721929892": "Award Title",
                    }
                ],
            }
        ],
        "item_1617186920753": [
            {"subitem_1522646500366": "ISSN", "subitem_1522646572813": "xxxx-xxxx-xxxx"}
        ],
        "item_1617186941041": [
            {"subitem_1522650068558": "en", "subitem_1522650091861": "Source Title"}
        ],
        "item_1617186959569": {"subitem_1551256328147": "1"},
        "item_1617186981471": {"subitem_1551256294723": "111"},
        "item_1617186994930": {"subitem_1551256248092": "12"},
        "item_1617187024783": {"subitem_1551256198917": "1"},
        "item_1617187045071": {"subitem_1551256185532": "3"},
        "item_1617187112279": [
            {"subitem_1551256126428": "Degree Name", "subitem_1551256129013": "en"}
        ],
        "item_1617187136212": {"subitem_1551256096004": "2021-06-30"},
        "item_1617187187528": [
            {
                "subitem_1599711633003": [
                    {
                        "subitem_1599711636923": "Conference Name",
                        "subitem_1599711645590": "ja",
                    }
                ],
                "subitem_1599711655652": "1",
                "subitem_1599711660052": [
                    {"subitem_1599711680082": "Sponsor", "subitem_1599711686511": "ja"}
                ],
                "subitem_1599711699392": {
                    "subitem_1599711704251": "2020/12/11",
                    "subitem_1599711712451": "1",
                    "subitem_1599711727603": "12",
                    "subitem_1599711731891": "2000",
                    "subitem_1599711735410": "1",
                    "subitem_1599711739022": "12",
                    "subitem_1599711743722": "2020",
                    "subitem_1599711745532": "ja",
                },
                "subitem_1599711758470": [
                    {
                        "subitem_1599711769260": "Conference Venue",
                        "subitem_1599711775943": "ja",
                    }
                ],
                "subitem_1599711788485": [
                    {
                        "subitem_1599711798761": "Conference Place",
                        "subitem_1599711803382": "ja",
                    }
                ],
                "subitem_1599711813532": "JPN",
            }
        ],
        "item_1617258105262": {
            "resourceuri": "http://purl.org/coar/resource_type/c_5794",
            "resourcetype": "conference paper",
        },
        "item_1617265215918": {
            "subitem_1522305645492": "AO",
            "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
        },
        "item_1617349709064": [
            {
                "givenNames": [
                    {"givenName": "太郎", "givenNameLang": "ja"},
                    {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                    {"givenName": "Taro", "givenNameLang": "en"},
                ],
                "familyNames": [
                    {"familyName": "情報", "familyNameLang": "ja"},
                    {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                    {"familyName": "Joho", "familyNameLang": "en"},
                ],
                "contributorType": "ContactPerson",
                "nameIdentifiers": [
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://orcid.org/",
                        "nameIdentifierScheme": "ORCID",
                    },
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://ci.nii.ac.jp/",
                        "nameIdentifierScheme": "CiNii",
                    },
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                        "nameIdentifierScheme": "KAKEN2",
                    },
                ],
                "contributorMails": [{"contributorMail": "wekosoftware@nii.ac.jp"}],
                "contributorNames": [
                    {"lang": "ja", "contributorName": "情報, 太郎"},
                    {"lang": "ja-Kana", "contributorName": "ジョウホ, タロウ"},
                    {"lang": "en", "contributorName": "Joho, Taro"},
                ],
            }
        ],
        "item_1617349808926": {"subitem_1523263171732": "Version"},
        "item_1617351524846": {"subitem_1523260933860": "Unknown"},
        "item_1617353299429": [
            {
                "subitem_1522306207484": "isVersionOf",
                "subitem_1522306287251": {
                    "subitem_1522306382014": "arXiv",
                    "subitem_1522306436033": "xxxxx",
                },
                "subitem_1523320863692": [
                    {
                        "subitem_1523320867455": "en",
                        "subitem_1523320909613": "Related Title",
                    }
                ],
            }
        ],
        "item_1617605131499": [
            {
                "url": {
                    "url": "https://weko3.example.org/record/{0}/files/{1}".format(i,filename)
                },
                "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                "format": "{}".format(mimetype),
                "filename": "{}".format(filename),
                "filesize": [{"value": "1 KB"}],
                "mimetype": "{}".format(mimetype),
                "accessrole": "open_login",
                "roles": roles,
                "version_id": "c1502853-c2f9-455d-8bec-f6e630e54b21",
                "displaytype": "simple",
                "provide": [{"workflow": 1, "role": 1}],
                "terms": 'term_free' if i%2==0 else '100',
                "terms_content": 'test terms_content' if i%2==0 else 'terms context',
            }
        ],
        "item_1617610673286": [
            {
                "nameIdentifiers": [
                    {
                        "nameIdentifier": "xxxxxx",
                        "nameIdentifierURI": "https://orcid.org/",
                        "nameIdentifierScheme": "ORCID",
                    }
                ],
                "rightHolderNames": [
                    {
                        "rightHolderName": "Right Holder Name",
                        "rightHolderLanguage": "ja",
                    }
                ],
            }
        ],
        "item_1617620223087": [
            {
                "subitem_1565671149650": "ja",
                "subitem_1565671169640": "Banner Headline",
                "subitem_1565671178623": "Subheading",
            },
            {
                "subitem_1565671149650": "en",
                "subitem_1565671169640": "Banner Headline",
                "subitem_1565671178623": "Subheding",
            },
        ],
        "item_1617944105607": [
            {
                "subitem_1551256015892": [
                    {
                        "subitem_1551256027296": "xxxxxx",
                        "subitem_1551256029891": "kakenhi",
                    }
                ],
                "subitem_1551256037922": [
                    {
                        "subitem_1551256042287": "Degree Grantor Name",
                        "subitem_1551256047619": "en",
                    }
                ],
            }
        ],
    }

    rec_uuid = uuid.uuid4()

    recid = PersistentIdentifier.create(
        "recid",
        str(i),
        object_type="rec",
        object_uuid=rec_uuid,
        status=PIDStatus.REGISTERED,
    )
    depid = PersistentIdentifier.create(
        "depid",
        str(i),
        object_type="rec",
        object_uuid=rec_uuid,
        status=PIDStatus.REGISTERED,
    )
    parent = None
    doi = None
    hdl = None
    recid_v1 = PersistentIdentifier.create(
        "recid",
        str(i + 0.1),
        object_type="rec",
        object_uuid=rec_uuid,
        status=PIDStatus.REGISTERED,
    )
    rec_uuid2 = uuid.uuid4()
    depid_v1 = PersistentIdentifier.create(
        "depid",
        str(i + 0.1),
        object_type="rec",
        object_uuid=rec_uuid2,
        status=PIDStatus.REGISTERED,
    )
    parent = PersistentIdentifier.create(
        "parent",
        "parent:{}".format(i),
        object_type="rec",
        object_uuid=rec_uuid2,
        status=PIDStatus.REGISTERED,
    )

    h1 = PIDVersioning(parent=parent)
    h1.insert_child(child=recid)
    h1.insert_child(child=recid_v1)
    RecordDraft.link(recid, depid)
    RecordDraft.link(recid_v1, depid_v1)

    if i % 2 == 1:
        doi = PersistentIdentifier.create(
            "doi",
            "https://doi.org/10.xyz/{}".format((str(i)).zfill(10)),
            object_type="rec",
            object_uuid=rec_uuid,
            status=PIDStatus.REGISTERED,
        )
        hdl = PersistentIdentifier.create(
            "hdl",
            "https://hdl.handle.net/0000/{}".format((str(i)).zfill(10)),
            object_type="rec",
            object_uuid=rec_uuid,
            status=PIDStatus.REGISTERED,
        )

    record = WekoRecord.create(record_data, id_=rec_uuid)
    # from six import BytesIO
    import base64

    bucket = Bucket.create()
    record_buckets = RecordsBuckets.create(record=record.model, bucket=bucket)

    # stream = BytesIO(b"Hello, World")
    obj = None
    with open(filepath, "rb") as f:
        stream = BytesIO(f.read())
        record.files[filename] = stream
        record["item_1617605131499"]["attribute_value_mlt"][0]["file"] = (
            base64.b64encode(stream.getvalue())
        ).decode("utf-8")
    with open(filepath, "rb") as f:
        obj = ObjectVersion.create(bucket=bucket.id, key=filename, stream=f)
    deposit = aWekoDeposit(record, record.model)
    deposit.commit()
    record["item_1617605131499"]["attribute_value_mlt"][0]["version_id"] = str(
        obj.version_id
    )

    record_data["content"] = [
        {
            "date": [{"dateValue": "2021-07-12", "dateType": "Available"}],
            "accessrole": "open_login",
            "roles" : roles,
            "terms"	:"term_free","termsDescription":"利用規約本文",
            "displaytype": "simple",
            "filename": filename,
            "attachment": {},
            "format": mimetype,
            "mimetype": mimetype,
            "filesize": [{"value": "1 KB"}],
            "version_id": "{}".format(obj.version_id),
            "url": {"url": "http://localhost/record/{0}/files/{1}".format(i, filename)},
            "file": (base64.b64encode(stream.getvalue())).decode("utf-8"),
        }
    ]
    indexer.upload_metadata(record_data, rec_uuid, 1, False)
    item = ItemsMetadata.create(item_data, id_=rec_uuid, item_type_id=1)

    record_v1 = WekoRecord.create(record_data, id_=rec_uuid2)
    # from six import BytesIO
    import base64

    bucket_v1 = Bucket.create()
    record_buckets = RecordsBuckets.create(record=record_v1.model, bucket=bucket_v1)
    # stream = BytesIO(b"Hello, World")
    record_v1.files[filename] = stream
    obj_v1 = ObjectVersion.create(bucket=bucket_v1.id, key=filename, stream=stream)
    record_v1["item_1617605131499"]["attribute_value_mlt"][0]["file"] = (
        base64.b64encode(stream.getvalue())
    ).decode("utf-8")
    deposit_v1 = aWekoDeposit(record_v1, record_v1.model)
    deposit_v1.commit()
    record_v1["item_1617605131499"]["attribute_value_mlt"][0]["version_id"] = str(
        obj_v1.version_id
    )

    record_data_v1 = copy.deepcopy(record_data)
    record_data_v1["content"] = [
        {
            "date": [{"dateValue": "2021-07-12", "dateType": "Available"}],
            "accessrole": "open_login",
            "roles" : roles,
            "terms"	:"term_free","termsDescription":"利用規約本文",
            "displaytype": "simple",
            "filename": filename,
            "attachment": {},
            "format": mimetype,
            "mimetype": mimetype,
            "filesize": [{"value": "1 KB"}],
            "version_id": "{}".format(obj_v1.version_id),
            "url": {"url": "http://localhost/record/{0}/files/{1}".format(i, filename)},
            "file": (base64.b64encode(stream.getvalue())).decode("utf-8"),
        }
    ]
    indexer.upload_metadata(record_data_v1, rec_uuid2, 1, False)
    item_v1 = ItemsMetadata.create(item_data, id_=rec_uuid2, item_type_id=1)

    db.session.flush()
    # db.session.expunge_all()

    return {
        "depid": depid,
        "recid": recid,
        "parent": parent,
        "doi": doi,
        "hdl": hdl,
        "record": record,
        "record_data": record_data,
        "item": item,
        "item_data": item_data,
        "deposit": deposit,
        "filename": filename,
        "mimetype": mimetype,
        "obj": obj,
    }


@pytest.fixture()
def workflow_actions(app, db):
    # workflow_action
    action_datas = dict()
    with open("tests/data/actions.json", "r") as f:
        action_datas = json.load(f)
    actions_db = list()
    with db.session.begin_nested():
        for data in action_datas:
            actions_db.append(Action(**data))
        db.session.add_all(actions_db)

    #workflow_action_status
    actionstatus_datas = dict()
    with open("tests/data/action_status.json") as f:
        actionstatus_datas = json.load(f)
    actionstatus_db = list()
    with db.session.begin_nested():
        for data in actionstatus_datas:
            actionstatus_db.append(ActionStatus(**data))
        db.session.add_all(actionstatus_db)


@pytest.fixture()
def workflows(app, db, workflow_actions, itemtypes, users, records):
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

    def_workflow = WorkFlow(
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
    data_usage_workflow = WorkFlow(
        flows_id=uuid.uuid4(),
        flows_name="Data Usage Report",
        itemtype_id=1,
        index_tree_id=None,
        flow_id=1,
        is_deleted=False,
        open_restricted=False,
        location_id=None,
        is_gakuninrdm=False,
    )
    def_activity = Activity(
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
        shared_user_ids=[],
        extra_info={},
        action_order=6,
    )
    data_usage_activity = Activity(
        item_id=records[1][0]['record'].id,
        activity_id="usage_application_activity_id_dummy1",
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
        title="Data Usage Report",
        shared_user_ids=[],
        extra_info={
            "related_title": "Data Usage Report",
            "record_id": 1,
            "file_name": records[1][0]["filename"],
            "guest_mail": "guest@nii.co.jp",
            "user_mail": "user@nii.co.jp"
        },
        action_order=6,
    )
    guest_activity = GuestActivity(
        user_mail="guest@nii.co.jp",
        record_id=1,
        file_name=records[1][0]["filename"],
        activity_id='',
        token='',
        expiration_date=datetime.now()
    )

    with db.session.begin_nested():
        db.session.add(flow_define)
        db.session.add(flow_action1)
        db.session.add(flow_action2)
        db.session.add(flow_action3)
        db.session.add(def_workflow)
        db.session.add(data_usage_workflow)
        db.session.add(def_activity)
        db.session.add(data_usage_activity)
        db.session.add(guest_activity)

    return {
        "flow_define": flow_define,
        "workflow": def_workflow,
        "data_usage_wf": data_usage_workflow,
        "activity": def_activity,
        "guest_activity": guest_activity,
        "data_usage_activity": data_usage_activity,
        "flow_action1": flow_action1,
        "flow_action2": flow_action2,
        "flow_action3": flow_action3,
    }

@pytest.fixture()
def workflows_restricted(db ,workflow_actions, itemtypes,users, records):
    workflows = {}

    flow_id1 = uuid.uuid4()
    flow_id2 = uuid.uuid4()
    flow_id3 = uuid.uuid4()
    flow_id4 = uuid.uuid4()

    #workflow_flow_define
    flow_define1 = FlowDefine(
        flow_id=flow_id1, flow_name="登録のみF", flow_user=1, flow_status="A"
    )
    flow_define2 = FlowDefine(
        flow_id=flow_id2, flow_name="利用規約のみF", flow_user=1, flow_status="M"
    )
    flow_define3 = FlowDefine(
        flow_id=flow_id3, flow_name="利用申請F", flow_user=1, flow_status="A"
    )
    flow_define4 = FlowDefine(
        flow_id=flow_id4, flow_name="2段階利用申請F", flow_user=1, flow_status="A"
    )

    # workflow_flow_action
    flow_action1_1 = FlowAction(
        status="N",
        flow_id=flow_id1,
        action_id=1,
        action_version="1.0.0",
        action_order=1,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": False, "inform_approval": False, "request_approval": False},
    )
    flow_action1_2 = FlowAction(
        status="N",
        flow_id=flow_id1,
        action_id=2,
        action_version="1.0.0",
        action_order=3,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": False, "inform_approval": False, "request_approval": False},
    )
    flow_action1_3 = FlowAction(
        status="N",
        flow_id=flow_id1,
        action_id=3,
        action_version="1.0.1",
        action_order=2,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": False, "inform_approval": True, "request_approval": False},
    )
    flow_action2_1 = FlowAction(
        status="N",
        flow_id=flow_id2,
        action_id=1,
        action_version="1.0.0",
        action_order=1,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={},
    )
    flow_action2_2 = FlowAction(
        status="N",
        flow_id=flow_id2,
        action_id=2,
        action_version="1.0.0",
        action_order=2,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={},
    )
    flow_action3_1 = FlowAction(
        status="N",
        flow_id=flow_id3,
        action_id=1,
        action_version="1.0.0",
        action_order=1,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": False, "inform_approval": False, "request_approval": False},
    )
    flow_action3_2 = FlowAction(
        status="N",
        flow_id=flow_id3,
        action_id=2,
        action_version="1.0.0",
        action_order=4,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": False, "inform_approval": False, "request_approval": False},
    )
    flow_action3_3 = FlowAction(
        status="N",
        flow_id=flow_id3,
        action_id=3,
        action_version="1.0.1",
        action_order=2,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": False, "inform_approval": False, "request_approval": False},
    )
    flow_action3_4 = FlowAction(
        status="N",
        flow_id=flow_id3,
        action_id=4,
        action_version="2.0.0",
        action_order=3,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": True, "inform_approval": True, "request_approval": True},
    )
    flow_action4_1 = FlowAction(
        status="N",
        flow_id=flow_id4,
        action_id=1,
        action_version="1.0.0",
        action_order=1,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": False, "inform_approval": False, "request_approval": False},
    )
    flow_action4_2 = FlowAction(
        status="N",
        flow_id=flow_id4,
        action_id=2,
        action_version="1.0.0",
        action_order=5,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": False, "inform_approval": False, "request_approval": False},
    )
    flow_action4_3 = FlowAction(
        status="N",
        flow_id=flow_id4,
        action_id=3,
        action_version="1.0.1",
        action_order=2,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": False, "inform_approval": False, "request_approval": False},
    )
    flow_action4_4 = FlowAction(
        status="N",
        flow_id=flow_id4,
        action_id=4,
        action_version="2.0.0",
        action_order=3,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": True, "inform_approval": True, "request_approval": True},
    )
    flow_action4_5 = FlowAction(
        status="N",
        flow_id=flow_id4,
        action_id=4,
        action_version="2.0.0",
        action_order=4,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": True, "inform_approval": True, "request_approval": True},
    )


    with db.session.begin_nested():
        db.session.add_all([flow_define1,flow_define2,flow_define3,flow_define4])

    #workflow_workflow
    workflow_workflow1 = WorkFlow(
        flows_id=flow_id1,
        flows_name="利用登録",
        itemtype_id=31001,
        index_tree_id=None,
        flow_id=flow_define1.id,
        flow_define=flow_define1,
        is_deleted=False,
        open_restricted=True,
        # location_id=location.id,
        # location=location,
        is_gakuninrdm=False,
    )
    workflow_workflow2 = WorkFlow(
        flows_id=flow_id2,
        flows_name="利用規約のみ",
        itemtype_id=31001,
        index_tree_id=None,
        flow_id=flow_define2.id,
        flow_define=flow_define2,
        is_deleted=False,
        open_restricted=True,
        # location_id=location.id,
        # location=location,
        is_gakuninrdm=False,
    )
    workflow_workflow3 = WorkFlow(
        flows_id=flow_id3,
        flows_name="利用申請",
        itemtype_id=31001,
        index_tree_id=None,
        flow_id=flow_define3.id,
        flow_define=flow_define3,
        is_deleted=False,
        open_restricted=True,
        # location_id=location.id,
        # location=location,
        is_gakuninrdm=False,
    )
    workflow_workflow4 = WorkFlow(
        flows_id=flow_id4,
        flows_name="2段階利用申請",
        itemtype_id=31002,
        index_tree_id=None,
        flow_id=flow_define4.id,
        flow_define=flow_define4,
        is_deleted=False,
        open_restricted=True,
        # location_id=location.id,
        # location=location,
        is_gakuninrdm=False,
    )
    db.session.flush()

    with db.session.begin_nested():
        db.session.add_all([flow_action1_1,flow_action1_2,flow_action1_3])
        db.session.add_all([flow_action2_1,flow_action2_2])
        db.session.add_all([flow_action3_1,flow_action3_2,flow_action3_3,flow_action3_4])
        db.session.add_all([flow_action4_1,flow_action4_2,flow_action4_3,flow_action4_4,flow_action4_5])
        db.session.add_all([workflow_workflow1, workflow_workflow2, workflow_workflow3, workflow_workflow4])

    workflows.update({
		"flow_define1"       : flow_define1      
		,"flow_define2"       : flow_define2      
		,"flow_define3"       : flow_define3      
		,"flow_define4"       : flow_define4      
		,"flow_action1_1"     : flow_action1_1    
		,"flow_action1_2"     : flow_action1_2    
		,"flow_action1_3"     : flow_action1_3    
		,"flow_action2_1"     : flow_action2_1    
		,"flow_action2_2"     : flow_action2_2    
		,"flow_action3_1"     : flow_action3_1    
		,"flow_action3_2"     : flow_action3_2    
		,"flow_action3_3"     : flow_action3_3    
		,"flow_action3_4"     : flow_action3_4    
		,"flow_action4_1"     : flow_action4_1    
		,"flow_action4_2"     : flow_action4_2    
		,"flow_action4_3"     : flow_action4_3    
		,"flow_action4_4"     : flow_action4_4    
		,"flow_action4_5"     : flow_action4_5    
		,"workflow_workflow1" : workflow_workflow1
		,"workflow_workflow2" : workflow_workflow2
		,"workflow_workflow3" : workflow_workflow3
		,"workflow_workflow4" : workflow_workflow4
    })

    return workflows


@pytest.fixture()
def pdfcoverpagesetting(db):
    with db.session.begin_nested():
        setting = PDFCoverPageSettings("enable", "string", "Weko Univ", "", "center")
        db.session.add(setting)


@pytest.fixture()
def site_license_info(app, db):
    record = SiteLicenseInfo(
        organization_id=1,
        organization_name='test',
        domain_name='domain',
        mail_address='nii@nii.co.jp',
        receive_mail_flag=False)
    with db.session.begin_nested():
        db.session.add(record)
    return record

@pytest.fixture()
def site_license_ipaddr(app, db,site_license_info):
    record1 = SiteLicenseIpAddress(organization_id=1,organization_no=1,start_ip_address="192.168.0.0",finish_ip_address="192.168.0.255")
    # record2 = SiteLicenseIpAddress(organization_id=1,start_ip_address="192.168.1.0",finish_ip_address="192.168.2.255")   
    with db.session.begin_nested():
        db.session.add(record1)
        # db.session.add(record2)
    return record1

@pytest.fixture()
def db_fileonetimedownload(app, db):
    record = FileOnetimeDownload(
        file_name="helloworld.pdf",
        user_mail="wekosoftware@nii.ac.jp",
        record_id='1',
        download_count=10,
        expiration_date=0,
        extra_info=str({"is_guest": True, "send_usage_report": True, "usage_application_activity_id": ""})
    )
    db.session.add(record)
    return record


@pytest.fixture()
def db_file_permission(app, db,users,records_restricted):
    indexer, results = records_restricted
    recid0 = results[0]["recid"]
    filename0 = results[0]["filename"]
    record0 = FilePermission(
        user_id=1, record_id=recid0.pid_value, file_name=filename0,
        usage_application_activity_id="usage_application_activity_id_dummy1",
        usage_report_activity_id=None, status=1, 
    )
    email = list(filter(lambda x : x['email'] if x['id'] == record0.user_id else None,users))[0]['email']
    record0_onetime=FileOnetimeDownload(user_mail=email
                                        ,record_id=recid0.pid_value
                                        ,file_name=filename0
                                        ,download_count=1
                                        ,expiration_date=1
                                        ,extra_info=str({}))
    recid1 = results[1]["recid"]
    filename1 = results[1]["filename"]
    record1 = FilePermission(
        user_id=1, record_id=recid1.pid_value, file_name=filename1,
                 usage_application_activity_id="usage_application_activity_id_dummy1",
                 usage_report_activity_id="usage_report_activity_id_dummy1",status=1,
    )
    email = list(filter(lambda x : x['email'] if x['id'] == record1.user_id else None,users))[0]['email']
    record1_onetime=FileOnetimeDownload(user_mail=email
                                        ,record_id=recid1.pid_value
                                        ,file_name=filename1
                                        ,download_count=1
                                        ,expiration_date=1
                                        ,extra_info=str({}))
    recid2 = results[2]["recid"]
    filename2 = results[2]["filename"]
    record2 = FilePermission(
        user_id=1, record_id=recid2.pid_value, file_name=filename2,
                 usage_application_activity_id="usage_application_activity_id_dummy1",
                 usage_report_activity_id="usage_report_activity_id_dummy1",status=1,
    )
    email = list(filter(lambda x : x['email'] if x['id'] == record2.user_id else None,users))[0]['email']
    record2_onetime=FileOnetimeDownload(user_mail=email
                                        ,record_id=recid2.pid_value
                                        ,file_name=filename2
                                        ,download_count=1
                                        ,expiration_date=1
                                        ,extra_info=str({}))
    
    # not approved yet
    recid3 = results[len(results)-1]["recid"]
    filename3 = results[len(results)-1]["filename"]
    record3 = FilePermission(
        user_id=users[0]['id'], record_id=recid3.pid_value, file_name=filename3,
        usage_application_activity_id="usage_application_activity_id_dummy1",
        usage_report_activity_id=None, status=-1, 
    )

    recid4 = results[len(results)-1]["recid"]
    filename4 = results[len(results)-1]["filename"]
    record4 = FilePermission(
        user_id=users[0]['id'], record_id=recid4.pid_value, file_name=filename4,
        usage_application_activity_id="usage_application_activity_id_dummy1",
        usage_report_activity_id=None, status=1, 
    )
    email = list(filter(lambda x : x['email'] if x['id'] == record4.user_id else None,users))[0]['email']
    record4_onetime=FileOnetimeDownload(user_mail =email
                                        ,record_id=recid4.pid_value
                                        ,file_name=filename4
                                        ,download_count =1
                                        ,expiration_date=1
                                        ,extra_info=str({}))
    
    recid5 = results[len(results)-1]["recid"]
    filename5 = results[len(results)-1]["filename"]
    record5 = FilePermission(
        user_id=users[0]['id'], record_id=recid5.pid_value, file_name=filename5,
        usage_application_activity_id="usage_application_activity_id_dummy1",
        usage_report_activity_id=None, status=1, 
    )
    email = list(filter(lambda x : x['email'] if x['id'] == record5.user_id else None,users))[0]['email']
    record5_onetime=FileOnetimeDownload(user_mail=email
                                        ,record_id=recid5.pid_value
                                        ,file_name=filename5
                                        ,download_count=1
                                        ,expiration_date=1
                                        ,extra_info=str({}))
    with db.session.begin_nested():
        db.session.add(record0)
        db.session.add(record1)
        db.session.add(record2)
        db.session.add(record3)
        db.session.add(record4)
        db.session.add(record5)
        db.session.add(record0_onetime)
        db.session.add(record1_onetime)
        db.session.add(record2_onetime)
        # db.session.add(record3_onetime)
        db.session.add(record4_onetime)
        db.session.add(record5_onetime)
    
    return [record0,record1,record2,record3,record4,record5]

@pytest.fixture()
def db_FilePermission(app, db):
    file_permission = FilePermission(
        user_id=1,
        record_id=99,
        file_name="test",
        usage_application_activity_id="test",
        usage_report_activity_id="test",
        status=-1
    )
    with db.session.begin_nested():
        db.session.add(file_permission)
    return file_permission


@pytest.fixture()
def db_FileOneTimeDownload(app, db):
    file_one_time_download = FileOnetimeDownload(
        file_name="test",
        user_mail="test@test",
        record_id=99,
        download_count=1,
        expiration_date=99,
    )
    with db.session.begin_nested():
        db.session.add(file_one_time_download)
    return file_one_time_download

    
@pytest.fixture()
def db_admin_settings(db):
    with db.session.begin_nested():
        db.session.add(AdminSettings(id=1,name='items_display_settings',settings={"items_display_email": False, "items_search_author": "name", "item_display_open_date": False}))
        db.session.add(AdminSettings(id=2,name='storage_check_settings',settings={"day": 0, "cycle": "weekly", "threshold_rate": 80}))
        db.session.add(AdminSettings(id=3,name='site_license_mail_settings',settings={"auto_send_flag": False}))
        db.session.add(AdminSettings(id=4,name='default_properties_settings',settings={"show_flag": True}))
        db.session.add(AdminSettings(id=5,name='item_export_settings',settings={"allow_item_exporting": True, "enable_contents_exporting": True}))
    db.session.commit()

@pytest.fixture()
def db_restricted_access_secret(db):
    with db.session.begin_nested():
        db.session.add(AdminSettings(id=6,name='restricted_access',settings={"secret_URL_file_download": {"secret_enable": True, "secret_download_limit": 1, "secret_expiration_date": 1, "secret_download_limit_unlimited_chk": False, "secret_expiration_date_unlimited_chk": False}}))
    db.session.commit()

@pytest.fixture()
def db_community(db , users ,indextree):
    from invenio_communities.models import Community
    comm : Community
    with db.session.begin_nested():
        comm = Community(
            id="community"
            ,id_role = users[0]["id"]
            ,root_node_id=Index.get_index_by_id(1).id
            ,id_user = users[0]["id"]
        )
        db.session.add(comm)
        db.session.flush()

    return comm

@pytest.fixture()
def db_mailTemplateGenre(db):
    from invenio_mail.models import MailTemplateGenres
    with db.session.begin_nested():
        db.session.add(MailTemplateGenres(id=1,name='Notification of secret URL provision'))
    db.session.commit()

@pytest.fixture()
def db_mailtemplates(db):
    from invenio_mail.models import MailTemplates
    with db.session.begin_nested():
        db.session.add(MailTemplates(id=1,mail_subject="test_subject",mail_body="test_mail_body",default_mail=True,mail_genre_id=1))
    db.session.commit()

@pytest.fixture()
def make_record_need_restricted_access(app, db, workflows, users):
    """make open_resirected record."""

    record_data_list = []
    with open('tests/data/need_restricted_access_records_metadata.json', 'r') as f:
        record_data_list = json.load(f)

    # 1. Not restricted access.
    rec_id11 = 11
    rec_id11_1 = 11.1
    rec_uuid11 = uuid.uuid4()
    rec_uuid11_1 = uuid.uuid4()
    recid11 = PersistentIdentifier.create('recid', str(rec_id11), object_type='rec', object_uuid=rec_uuid11, status=PIDStatus.REGISTERED,)
    recid11_1 = PersistentIdentifier.create('recid', str(rec_id11_1), object_type='rec', object_uuid=rec_uuid11_1, status=PIDStatus.REGISTERED,)
    depid11 = PersistentIdentifier.create('depid', str(rec_id11), object_type='rec', object_uuid=rec_uuid11, status=PIDStatus.REGISTERED,)
    depid11_1 = PersistentIdentifier.create('depid', str(rec_id11_1), object_type='rec', object_uuid=rec_uuid11_1, status=PIDStatus.REGISTERED,)
    parent11 = PersistentIdentifier.create('parent', f'parent:{rec_id11}', object_type='rec', object_uuid=rec_uuid11, status=PIDStatus.REGISTERED,)
    rel11 = PIDRelation.create(parent11, recid11, 2, 0)
    rel11_1 = PIDRelation.create(parent11, recid11_1, 2, 1)
    dep_rel11 = PIDRelation.create(recid11, depid11, 3)
    dep_rel11_1 = PIDRelation.create(recid11_1, depid11_1, 3)
    record11 = WekoRecord.create(record_data_list[0], id_=rec_uuid11)

    activity11 = Activity(
        activity_id='11',
        item_id=rec_uuid11_1,
        workflow_id=1,
        flow_id=workflows['flow_define'].id,
        activity_start=datetime.strptime('2023/07/01 10:00:00.000', '%Y/%m/%d %H:%M:%S.%f'),
        activity_end=datetime.strptime('2023/07/01 11:00:00.000', '%Y/%m/%d %H:%M:%S.%f'),
        activity_status='F',
        title='test1',
        action_order=1,
    )

    # 2. Normal data
    rec_id12 = 12
    rec_id12_1 = 12.1
    rec_uuid12 = uuid.uuid4()
    rec_uuid12_1 = uuid.uuid4()
    recid12 = PersistentIdentifier.create('recid', str(rec_id12), object_type='rec', object_uuid=rec_uuid12, status=PIDStatus.REGISTERED,)
    recid12_1 = PersistentIdentifier.create('recid', str(rec_id12_1), object_type='rec', object_uuid=rec_uuid12_1, status=PIDStatus.REGISTERED,)
    depid12 = PersistentIdentifier.create('depid', str(rec_id12), object_type='rec', object_uuid=rec_uuid12, status=PIDStatus.REGISTERED,)
    depid12_1 = PersistentIdentifier.create('depid', str(rec_id12_1), object_type='rec', object_uuid=rec_uuid12_1, status=PIDStatus.REGISTERED,)
    parent12 = PersistentIdentifier.create('parent', f'parent:{rec_id12}', object_type='rec', object_uuid=rec_uuid12, status=PIDStatus.REGISTERED,)
    rel12 = PIDRelation.create(parent12, recid12, 2, 0)
    rel12_1 = PIDRelation.create(parent12, recid12_1, 2, 1)
    dep_rel12 = PIDRelation.create(recid12, depid12, 3)
    dep_rel12_1 = PIDRelation.create(recid12_1, depid12_1, 3)
    record12 = WekoRecord.create(record_data_list[1], id_=rec_uuid12)

    activity12 = Activity(
        activity_id='12',
        item_id=rec_uuid12_1,
        workflow_id=1,
        flow_id=workflows['flow_define'].id,
        activity_start=datetime.strptime('2023/07/01 10:00:00.000', '%Y/%m/%d %H:%M:%S.%f'),
        activity_end=datetime.strptime('2023/07/01 11:00:00.000', '%Y/%m/%d %H:%M:%S.%f'),
        activity_status='F',
        title='test2',
        action_order=1,
    )

    # 3. Restricted Access is approved.
    rec_id13 = 13
    rec_id13_1 = 13.1
    rec_uuid13 = uuid.uuid4()
    rec_uuid13_1 = uuid.uuid4()
    recid13 = PersistentIdentifier.create('recid', str(rec_id13), object_type='rec', object_uuid=rec_uuid13, status=PIDStatus.REGISTERED,)
    recid13_1 = PersistentIdentifier.create('recid', str(rec_id13_1), object_type='rec', object_uuid=rec_uuid13_1, status=PIDStatus.REGISTERED,)
    depid13 = PersistentIdentifier.create('depid', str(rec_id13), object_type='rec', object_uuid=rec_uuid13, status=PIDStatus.REGISTERED,)
    depid13_1 = PersistentIdentifier.create('depid', str(rec_id13_1), object_type='rec', object_uuid=rec_uuid13_1, status=PIDStatus.REGISTERED,)
    parent13 = PersistentIdentifier.create('parent', f'parent:{rec_id13}', object_type='rec', object_uuid=rec_uuid13, status=PIDStatus.REGISTERED,)
    rel13 = PIDRelation.create(parent13, recid13, 2, 0)
    rel13_1 = PIDRelation.create(parent13, recid13_1, 2, 1)
    dep_rel13 = PIDRelation.create(recid13, depid13, 3)
    dep_rel13_1 = PIDRelation.create(recid13_1, depid13_1, 3)
    record13 = WekoRecord.create(record_data_list[2], id_=rec_uuid13)

    activity13 = Activity(
        activity_id='13',
        item_id=rec_uuid13_1,
        workflow_id=1,
        flow_id=workflows['flow_define'].id,
        activity_start=datetime.strptime('2023/07/01 10:00:00.000', '%Y/%m/%d %H:%M:%S.%f'),
        activity_end=datetime.strptime('2023/07/01 11:00:00.000', '%Y/%m/%d %H:%M:%S.%f'),
        activity_status='F',
        title='test3',
        action_order=1,
    )

    file_permission13 = FilePermission(
        user_id=users[0]['id'],
        record_id=rec_id13,
        file_name='dummy.txt',
        usage_application_activity_id='13',
        usage_report_activity_id=None,
        status=1,   # Approved
    )
    file13_onetime = FileOnetimeDownload(
        user_mail=users[0]['email'],
        record_id=rec_id13,
        file_name='dummy.txt',
        download_count=1,
        expiration_date=1,
    )

    # 4. Restricted Access is not approved.
    rec_id14 = 14
    rec_id14_1 = 14.1
    rec_uuid14 = uuid.uuid4()
    rec_uuid14_1 = uuid.uuid4()
    recid14 = PersistentIdentifier.create('recid', str(rec_id14), object_type='rec', object_uuid=rec_uuid14, status=PIDStatus.REGISTERED,)
    recid14_1 = PersistentIdentifier.create('recid', str(rec_id14_1), object_type='rec', object_uuid=rec_uuid14_1, status=PIDStatus.REGISTERED,)
    depid14 = PersistentIdentifier.create('depid', str(rec_id14), object_type='rec', object_uuid=rec_uuid14, status=PIDStatus.REGISTERED,)
    depid14_1 = PersistentIdentifier.create('depid', str(rec_id14_1), object_type='rec', object_uuid=rec_uuid14_1, status=PIDStatus.REGISTERED,)
    parent14 = PersistentIdentifier.create('parent', f'parent:{rec_id14}', object_type='rec', object_uuid=rec_uuid14, status=PIDStatus.REGISTERED,)
    rel14 = PIDRelation.create(parent14, recid14, 2, 0)
    rel14_1 = PIDRelation.create(parent14, recid14_1, 2, 1)
    dep_rel14 = PIDRelation.create(recid14, depid14, 3)
    dep_rel14_1 = PIDRelation.create(recid14_1, depid14_1, 3)
    record14 = WekoRecord.create(record_data_list[3], id_=rec_uuid14)

    activity14 = Activity(
        activity_id='14',
        item_id=rec_uuid14_1,
        workflow_id=1,
        flow_id=workflows['flow_define'].id,
        activity_start=datetime.strptime('2023/07/01 10:00:00.000', '%Y/%m/%d %H:%M:%S.%f'),
        activity_end=datetime.strptime('2023/07/01 11:00:00.000', '%Y/%m/%d %H:%M:%S.%f'),
        activity_status='F',
        title='test4',
        action_order=1,
    )

    file_permission14 = FilePermission(
        user_id=users[0]['id'],
        record_id=rec_id14,
        file_name='dummy.txt',
        usage_application_activity_id='14',
        usage_report_activity_id=None,
        status=0,   # Processing
    )

    # 5. Restricted Access is not applied.
    rec_id15 = 15
    rec_id15_1 = 15.1
    rec_uuid15 = uuid.uuid4()
    rec_uuid15_1 = uuid.uuid4()
    recid15 = PersistentIdentifier.create('recid', str(rec_id15), object_type='rec', object_uuid=rec_uuid15, status=PIDStatus.REGISTERED,)
    recid15_1 = PersistentIdentifier.create('recid', str(rec_id15_1), object_type='rec', object_uuid=rec_uuid15_1, status=PIDStatus.REGISTERED,)
    parent15 = PersistentIdentifier.create('parent', f'parent:{rec_id15}', object_type='rec', object_uuid=rec_uuid15, status=PIDStatus.REGISTERED,)
    depid15 = PersistentIdentifier.create('depid', str(rec_id15), object_type='rec', object_uuid=rec_uuid15, status=PIDStatus.REGISTERED,)
    depid15_1 = PersistentIdentifier.create('depid', str(rec_id15_1), object_type='rec', object_uuid=rec_uuid15_1, status=PIDStatus.REGISTERED,)
    rel15 = PIDRelation.create(parent15, recid15, 2, 0)
    rel15_1 = PIDRelation.create(parent15, recid15_1, 2, 1)
    dep_rel15 = PIDRelation.create(recid15, depid15, 3)
    dep_rel15_1 = PIDRelation.create(recid15_1, depid15_1, 3)
    record15 = WekoRecord.create(record_data_list[4], id_=rec_uuid15)

    activity15 = Activity(
        activity_id='15',
        item_id=rec_uuid15_1,
        workflow_id=1,
        flow_id=workflows['flow_define'].id,
        activity_start=datetime.strptime('2023/07/01 10:00:00.000', '%Y/%m/%d %H:%M:%S.%f'),
        activity_end=datetime.strptime('2023/07/01 11:00:00.000', '%Y/%m/%d %H:%M:%S.%f'),
        activity_status='F',
        title='test5',
        action_order=1,
    )

    # 6. Activity is not completed.
    rec_id16 = 16
    rec_id16_1 = 16.1
    rec_uuid16 = uuid.uuid4()
    rec_uuid16_1 = uuid.uuid4()
    recid16 = PersistentIdentifier.create('recid', str(rec_id16), object_type='rec', object_uuid=rec_uuid16, status=PIDStatus.REGISTERED,)
    recid16_1 = PersistentIdentifier.create('recid', str(rec_id16_1), object_type='rec', object_uuid=rec_uuid16_1, status=PIDStatus.REGISTERED,)
    depid16 = PersistentIdentifier.create('depid', str(rec_id16), object_type='rec', object_uuid=rec_uuid16, status=PIDStatus.REGISTERED,)
    depid16_1 = PersistentIdentifier.create('depid', str(rec_id16_1), object_type='rec', object_uuid=rec_uuid16_1, status=PIDStatus.REGISTERED,)
    parent16 = PersistentIdentifier.create('parent', f'parent:{rec_id16}', object_type='rec', object_uuid=rec_uuid16, status=PIDStatus.REGISTERED,)
    rel16 = PIDRelation.create(parent16, recid16, 2, 0)
    rel16_1 = PIDRelation.create(parent16, recid16_1, 2, 1)
    dep_rel16 = PIDRelation.create(recid15, depid16, 3)
    dep_rel16_1 = PIDRelation.create(recid15_1, depid16_1, 3)
    record16 = WekoRecord.create(record_data_list[5], id_=rec_uuid16)

    activity16 = Activity(
        activity_id='16',
        item_id=rec_uuid16_1,
        workflow_id=1,
        flow_id=workflows['flow_define'].id,
        activity_start=datetime.strptime('2023/07/01 10:00:00.000', '%Y/%m/%d %H:%M:%S.%f'),
        activity_end=datetime.strptime('2023/07/01 11:00:00.000', '%Y/%m/%d %H:%M:%S.%f'),
        activity_status='C',
        title='test6',
        action_order=1,
    )
    
    guest_activity_12 = GuestActivity(
        user_mail="guest@example.org",
        record_id=12,
        file_name="dummy.txt",
        activity_id="A-00000000-1234",
        token='',
        expiration_date=datetime.now()
    )

    with db.session.begin_nested():
        db.session.add(activity11)
        db.session.add(activity12)
        db.session.add(activity13)
        db.session.add(file_permission13)
        db.session.add(file13_onetime)
        db.session.add(activity14)
        db.session.add(file_permission14)
        db.session.add(activity15)
        db.session.add(activity16)
        db.session.add(guest_activity_12)
    db.session.commit()

    return {
        'FileOnetimeDownload': {'13': file13_onetime},
    }


@pytest.fixture()
def client_oauth(users):
    """Create client."""
    # create resource_owner -> client_1
    client_ = Client(
        client_id='client_test_u1c1',
        client_secret='client_test_u1c1',
        name='client_test_u1c1',
        description='',
        is_confidential=False,
        user=users[2]['obj'],
        _redirect_uris='',
        _default_scopes='',
    )
    with db_.session.begin_nested():
        db_.session.add(client_)
    db_.session.commit()
    return client_


@pytest.fixture()
def create_oauth_token(client, client_oauth, users):
    """Create token."""
    token1_ = Token(
        client=client_oauth,
        user=users[2]['obj'],   # sysadmin
        token_type='u',
        access_token='dev_access_1',
        refresh_token='dev_refresh_1',
        expires=datetime.now() + timedelta(hours=10),
        is_personal=False,
        is_internal=True,
        _scopes=item_read_scope.id,
    )
    token2_ = Token(
        client=client_oauth,
        user=users[0]['obj'],   # contributor
        token_type='u',
        access_token='dev_access_2',
        refresh_token='dev_refresh_2',
        expires=datetime.now() + timedelta(hours=10),
        is_personal=False,
        is_internal=True,
        _scopes=item_read_scope.id,
    )
    token3_ = Token(
        client=client_oauth,
        user=users[7]['obj'],   # user
        token_type='u',
        access_token='dev_access_3',
        refresh_token='dev_refresh_3',
        expires=datetime.now() + timedelta(hours=10),
        is_personal=False,
        is_internal=True,
        _scopes=item_read_scope.id,
    )
    with db_.session.begin_nested():
        db_.session.add(token1_)
        db_.session.add(token2_)
        db_.session.add(token3_)
    db_.session.commit()
    return [token1_, token2_, token3_]

@pytest.fixture()
def create_oauth_token_activity_scope(client, client_oauth, users):
    """Create token."""
    token1_ = Token(
        client=client_oauth,
        user=users[2]['obj'],   # sysadmin
        token_type='u',
        access_token='dev_access_activity_scope_1',
        refresh_token='dev_refresh_activity_scope_1',
        expires=datetime.now() + timedelta(hours=10),
        is_personal=False,
        is_internal=True,
        _scopes=activity_scope.id,
    )
    token2_ = Token(
        client=client_oauth,
        user=users[0]['obj'],   # contributor
        token_type='u',
        access_token='dev_access_activity_scope_2',
        refresh_token='dev_refresh_activity_scope_2',
        expires=datetime.now() + timedelta(hours=10),
        is_personal=False,
        is_internal=True,
        _scopes=activity_scope.id,
    )
    token3_ = Token(
        client=client_oauth,
        user=users[7]['obj'],   # user
        token_type='u',
        access_token='dev_access_activity_scope_3',
        refresh_token='dev_refresh_activity_scope_3',
        expires=datetime.now() + timedelta(hours=10),
        is_personal=False,
        is_internal=True,
        _scopes=activity_scope.id,
    )
    with db_.session.begin_nested():
        db_.session.add(token1_)
        db_.session.add(token2_)
        db_.session.add(token3_)
    db_.session.commit()
    return [token1_, token2_, token3_]


@pytest.fixture()
def json_headers():
    """JSON headers."""
    return [('Content-Type', 'application/json'), ('Accept', 'application/json')]


@pytest.fixture()
def oauth_headers(client, json_headers, create_oauth_token, create_oauth_token_activity_scope):
    """Authentication headers (with a valid oauth2 token).

    It uses the token associated with the first user.
    """
    return [
        fill_oauth2_headers(json_headers, create_oauth_token[0]),   # sysadmin (item_read_scope)
        fill_oauth2_headers(json_headers, create_oauth_token[1]),   # contributor (item_read_scope)
        fill_oauth2_headers(json_headers, create_oauth_token[2]),   # user (item_read_scope)
        json_headers,                                               # not login
        fill_oauth2_headers(json_headers, create_oauth_token_activity_scope[0]),    # sysadmin (activity_scope)
        fill_oauth2_headers(json_headers, create_oauth_token_activity_scope[1]),    # contributor (activity_scope)
        fill_oauth2_headers(json_headers, create_oauth_token_activity_scope[2]),    # user (activity_scope)
    ]

@pytest.fixture()
def records_rest(app, db):
    rec_uuid = uuid.uuid4()

    depid = PersistentIdentifier.create(
        'depid',
        '1',
        object_type='rec',
        object_uuid=rec_uuid,
        status=PIDStatus.REGISTERED
    )

    with open('tests/data/rocrate/records_metadata.json', 'r') as f:
        record_data = json.load(f)
    record = WekoRecord.create(record_data, id_=rec_uuid)

    return {
        'depid': depid,
        'record': record,
    }


@pytest.fixture()
def db_rocrate_mapping(db):
    item_type_name = ItemTypeName(id=40001, name='test item type', has_site_license=True, is_active=True)
    with db.session.begin_nested():
        db.session.add(item_type_name)
    db.session.commit()

    item_type_schema = dict()
    with open('tests/data/itemtype_schema.json', 'r') as f:
        item_type_schema = json.load(f)

    item_type_form = dict()
    with open('tests/data/itemtype_form.json', 'r') as f:
        item_type_form = json.load(f)
        item_type_form[10].pop('items')
        item_type_form[11]['items'][1]['isHide'] = True
        item_type_form[15]['items'][0].pop('title_i18n')
        item_type_form[15]['items'][0]['title'] = ''
        item_type_form[17]['items'][0].pop('title_i18n')

    item_type_render = dict()
    with open('tests/data/itemtype_render.json', 'r') as f:
        item_type_render = json.load(f)
        item_type_render['meta_list']['item_1617186385884']['option']['hidden'] = True


    item_type = ItemType(
        id=40001,
        name_id=40001,
        harvesting_type=True,
        schema=item_type_schema,
        form=item_type_form,
        render=item_type_render,
        tag=1,
        version_id=1,
        is_deleted=False,
    )

    with db.session.begin_nested():
        db.session.add(item_type)
    db.session.commit()

    with open('tests/data/rocrate/rocrate_mapping.json', 'r') as f:
        mapping = json.load(f)
    rocrate_mapping = RocrateMapping(item_type_id=40001, mapping=mapping)

    with db.session.begin_nested():
        db.session.add(rocrate_mapping)
    db.session.commit()


@pytest.fixture()
def indices(app, db):
    """Create indices."""

    latest_index = db.session.query(
        func.max(Index.position).label("max_position")
    ).one()
        
    index = Index(
        id=1234567890,
        index_name="index_name",
        index_name_english="index_name_english",
        display_no=1,
        harvest_public_state=True,
        image_name="image_name",
        public_state=True,
        position=latest_index.max_position + 1,
    )

    db.session.add(index)
    db.session.commit()

    return [index]


@pytest.fixture()
def communities(app, indices, users, db):
    """Create communities."""
    user_record = users[0]
    user_obj = user_record["obj"]

    community = Community(
        id="community_sample",
        id_role=user_obj.roles[0].id,
        id_user=user_record["id"],
        title='Community 1',
        description='Community 1 description',
        page=1,
        curation_policy='curation_policy',
        community_header='community_header',
        community_footer='community_footer',
        last_record_accepted=datetime.now(),
        root_node_id=indices[0].id,
    )

    db.session.add(community)
    db.session.commit()
    return [community]