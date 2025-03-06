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
import traceback
import mimetypes
import os
import shutil
import tempfile
import time
import uuid
from collections import OrderedDict
from datetime import datetime, timedelta
from os.path import dirname, exists, join
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from elasticsearch import Elasticsearch
from elasticsearch.client.ingest import IngestClient
from flask import Blueprint, Flask
from flask_assets import assets
from flask_babelex import Babel
from flask_login import LoginManager, UserMixin
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
from invenio_communities.views.ui import blueprint as invenio_communities_blueprint
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
from invenio_oaiserver.models import Identify
from invenio_oaiserver.views.server import blueprint as invenio_oaiserver_blueprint
from invenio_pidrelations import InvenioPIDRelations
from invenio_pidrelations.contrib.records import RecordDraft
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidrelations.models import PIDRelation
from invenio_pidstore import InvenioPIDStore
from invenio_pidstore.models import PersistentIdentifier, PIDStatus, Redirect
from invenio_previewer import InvenioPreviewer
from invenio_records import InvenioRecords
from invenio_records_files.models import RecordsBuckets
from invenio_records_rest import InvenioRecordsREST
from invenio_records_rest.utils import PIDConverter
from invenio_records_ui import InvenioRecordsUI
from invenio_rest import InvenioREST
from invenio_search import InvenioSearch, current_search_client
from invenio_search_ui import InvenioSearchUI
from invenio_stats import InvenioStats
from invenio_stats.config import SEARCH_INDEX_PREFIX as index_prefix
from invenio_theme import InvenioTheme
from simplekv.memory.redisstore import RedisStore
from six import BytesIO
from sqlalchemy_utils.functions import create_database, database_exists, drop_database
from weko_admin import WekoAdmin
from weko_admin.models import AdminSettings, RankingSettings, SessionLifetime
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
from weko_items_ui.config import (
    WEKO_ITEMS_UI_FILE_SISE_PREVIEW_LIMIT,
    WEKO_ITEMS_UI_MS_MIME_TYPE,
)
from weko_items_ui.views import blueprint as weko_items_ui_blueprint
from weko_items_ui.views import blueprint_api as weko_items_ui_blueprint_api
from weko_records import WekoRecords
from weko_records.api import ItemsMetadata, ItemLink
from weko_records.models import (
    FeedbackMailList,
    ItemType,
    ItemTypeMapping,
    ItemTypeName,
    SiteLicenseInfo,
    SiteLicenseIpAddress,
)
from weko_records.utils import get_options_and_order_list
from weko_records_ui import WekoRecordsCitesREST, WekoRecordsUI
from weko_records_ui.config import (
    FOOTER_HEIGHT,
    HEADER_HEIGHT,
    JPAEXG_TTF_FILEPATH,
    JPAEXM_TTF_FILEPATH,
    METADATA_HEIGHT,
    PDF_COVERPAGE_LANG_FILENAME,
    PDF_COVERPAGE_LANG_FILEPATH,
    RECORDS_UI_ENDPOINTS,
    RECORDS_UI_EXPORT_FORMATS,
    TITLE_HEIGHT,
    URL_OA_POLICY_HEIGHT,
    WEKO_ADMIN_PDFCOVERPAGE_TEMPLATE,
    WEKO_PERMISSION_ROLE_COMMUNITY,
    WEKO_RECORDS_UI_CITES_REST_ENDPOINTS,
    WEKO_RECORDS_UI_DOWNLOAD_DAYS,
    WEKO_RECORDS_UI_EMAIL_ITEM_KEYS,
    WEKO_RECORDS_UI_GOOGLE_SCHOLAR_OUTPUT_RESOURCE_TYPE,
    WEKO_RECORDS_UI_ONETIME_DOWNLOAD_PATTERN,
    WEKO_RECORDS_UI_SECRET_KEY,
)
from weko_records_ui.models import (
    FileOnetimeDownload,
    FilePermission,
    PDFCoverPageSettings,
)
from weko_records_ui.views import blueprint as weko_records_ui_blueprint
from weko_search_ui import WekoSearchREST, WekoSearchUI
from weko_search_ui.config import WEKO_SEARCH_MAX_RESULT, RESOURCE_TYPE_URI
from weko_theme import WekoTheme
from weko_theme.views import blueprint as weko_theme_blueprint
from weko_user_profiles.models import UserProfile
from weko_workflow import WekoWorkflow
from weko_workflow.models import (
    Action,
    ActionStatus,
    ActionStatusPolicy,
    Activity,
    FlowAction,
    FlowDefine,
    GuestActivity,
    WorkFlow,
)
from weko_workflow.views import workflow_blueprint as weko_workflow_blueprint
from werkzeug.local import LocalProxy

from tests.helpers import create_record, json_data
from weko_schema_ui import WekoSchemaUI
from weko_schema_ui.config import (
    WEKO_SCHEMA_DDI_SCHEMA_NAME,
    WEKO_SCHEMA_JPCOAR_V1_SCHEMA_NAME,
)
from weko_schema_ui.models import OAIServerSchema
from weko_schema_ui.rest import create_blueprint
from weko_schema_ui.views import blueprint as weko_schema_ui_blueprint


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
    
    app_.config.update(
        SECRET_KEY="SECRET_KEY",
        SERVER_NAME="test_server",
        TESTING=True,
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     "SQLALCHEMY_DATABASE_URI", "sqlite:///test.db"
        # ),
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                           'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        CACHE_REDIS_URL=os.environ.get("CACHE_REDIS_URL", "redis://redis:6379/0"),
        CACHE_TYPE="redis",
        CACHE_REDIS_DB=0,
        CACHE_REDIS_HOST=os.environ.get("INVENIO_REDIS_HOST"),
        REDIS_PORT="6379",
        WEKO_SCHEMA_CACHE_PREFIX="cache_{schema_name}",
        RECORDS_UI_ENDPOINTS=RECORDS_UI_ENDPOINTS,
        RECORDS_UI_EXPORT_FORMATS=RECORDS_UI_EXPORT_FORMATS,
        WEKO_RECORDS_UI_CITES_REST_ENDPOINTS=WEKO_RECORDS_UI_CITES_REST_ENDPOINTS,
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
        THEME_SITEURL = 'https://localhost',
        WEKO_SCHEMA_REST_XSD_LOCATION_FOLDER="{0}/data/xsd/",
        BASE_EDIT_TEMPLATE="weko_theme/edit.html",
        WEKO_SCHEMA_UI_ADMIN_LIST="weko_schema_ui/admin/list.html",
        WEKO_SCHEMA_UI_ADMIN_UPLOAD="weko_schema_ui/admin/upload.html",
        INDEXER_DEFAULT_INDEX="{}-weko-item-v1.0.0".format("test"),
        SEARCH_UI_SEARCH_INDEX="{}-weko-item-v1.0.0".format("test"),
        INDEXER_DEFAULT_DOCTYPE="item-v1.0.0",
        INDEXER_DEFAULT_DOC_TYPE="item-v1.0.0",
        INDEXER_FILE_DOC_TYPE="content",
        SEARCH_ELASTIC_HOSTS="elasticsearch",
        SEARCH_INDEX_PREFIX="test-",
        WEKO_BUCKET_QUOTA_SIZE=50 * 1024 * 1024 * 1024,
        WEKO_MAX_FILE_SIZE=50 * 1024 * 1024 * 1024,
        INDEX_IMG="indextree/36466818-image.jpg",
        WEKO_SEARCH_MAX_RESULT=WEKO_SEARCH_MAX_RESULT,
        WEKO_DEPOSIT_REST_ENDPOINTS=WEKO_DEPOSIT_REST_ENDPOINTS,
        WEKO_INDEX_TREE_UPATED=True,
        WEKO_INDEX_TREE_REST_ENDPOINTS=WEKO_INDEX_TREE_REST_ENDPOINTS,
        I18N_LANGUAGES=[("ja", "Japanese"), ("en", "English")],
        WEKO_SCHEMA_JPCOAR_V1_SCHEMA_NAME=WEKO_SCHEMA_JPCOAR_V1_SCHEMA_NAME,
        WEKO_SCHEMA_DDI_SCHEMA_NAME=WEKO_SCHEMA_DDI_SCHEMA_NAME,
        OAISERVER_XSL_URL=None,
        RESOURCE_TYPE_URI=RESOURCE_TYPE_URI,
    )
    InvenioAccounts(app_)
    InvenioAssets(app_)
    InvenioAccess(app_)
    InvenioAdmin(app_)
    InvenioDB(app_)
    InvenioCache(app_)
    InvenioPIDStore(app_)
    InvenioPIDRelations(app_)
    InvenioSearch(app_)
    InvenioOAIServer(app_)
    InvenioSearchUI(app_)
    InvenioDeposit(app_)
    InvenioFilesREST(app_)
    InvenioIndexer(app_)
    InvenioRecords(app_)
    InvenioRecordsUI(app_)
    InvenioRecordsREST(app_)
    Babel(app_)
    Menu(app_)
    WekoRecords(app_)
    WekoItemsUI(app_)
    WekoRecordsUI(app_)
    WekoAdmin(app_)
    WekoSearchUI(app_)
    WekoIndexTree(app_)
    WekoIndexTreeREST(app_)
    WekoSchemaUI(app_)
    WekoDeposit(app_)
    WekoDepositREST(app_)
    # app_.register_blueprint(weko_schema_ui_blueprint)
    app_.register_blueprint(weko_records_ui_blueprint)
    app_.register_blueprint(invenio_files_rest_blueprint)  # invenio_files_rest
    app_.register_blueprint(invenio_oaiserver_blueprint)
    
    current_assets = LocalProxy(lambda: app_.extensions["invenio-assets"])
    current_assets.collect.collect()

    return app_


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app


@pytest.yield_fixture()
def client_rest(app):
    config = {
        "depid": {
            "pid_type": "depid",
            "pid_minter": "deposit",
            "pid_fetcher": "deposit",
            "record_class": "weko_schema_ui.api:WekoSchema",
            "record_serializers": {
                "application/json": (
                    "invenio_records_rest.serializers" ":json_v1_response"
                ),
            },
            "schemas_route": "/schemas/",
            "schema_route": "/schemas/<pid_value>",
            "schemas_put_route": "/schemas/put/<pid_value>/<path:key>",
            # 'schemas_formats_route': '/schemas/formats/',
            "default_media_type": "application/json",
            "max_result_window": 10000,
        },
    }
    app.register_blueprint(create_blueprint(config))
    with app.test_client() as client:
        yield client


@pytest.yield_fixture()
def client_rest2(app):
    config = {
        "depid": {
            "pid_type": "depid",
            "pid_minter": "deposit",
            "pid_fetcher": "deposit",
            "record_class": "weko_schema_ui.api:WekoSchema",
            "schemas_route": "/schemas/",
            "schema_route": "/schemas/<pid_value>",
            "schemas_put_route": "/schemas/put/<pid_value>/<path:key>",
            # 'schemas_formats_route': '/schemas/formats/',
            "default_media_type": "test",
            "max_result_window": 10000,
        },
    }
    app.register_blueprint(create_blueprint(config))
    with app.test_client() as client:
        yield client


@pytest.fixture()
def db(app):
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()


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

    ds.add_role_to_user(sysadmin, sysadmin_role)
    ds.add_role_to_user(repoadmin, repoadmin_role)
    ds.add_role_to_user(contributor, contributor_role)
    ds.add_role_to_user(comadmin, comadmin_role)
    ds.add_role_to_user(generaluser, general_role)
    ds.add_role_to_user(originalroleuser, originalrole)
    ds.add_role_to_user(originalroleuser2, originalrole)
    ds.add_role_to_user(originalroleuser2, repoadmin_role)

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

    schema_name = "ddi_mapping"
    form_data = dict()
    with open("tests/data/oaischema/ddi_mapping_form_data.json", "r") as f:
        form_data = json.load(f)

    xsd = dict()
    with open("tests/data/oaischema/ddi_mapping_xsd.json", "r") as f:
        xsd = json.load(f)

    namespaces = dict()
    with open("tests/data/oaischema/ddi_mapping_namespaces.json", "r") as f:
        namespaces = json.load(f)

    schema_location = (
        "https://ddialliance.org/Specification/DDI-Codebook/2.5/XMLSchema/codebook.xsd"
    )
    ddi25 = OAIServerSchema(
        id=uuid.uuid4(),
        schema_name=schema_name,
        form_data=form_data,
        xsd=json.dumps(xsd),
        namespaces=namespaces,
        schema_location=schema_location,
        isvalid=True,
        is_mapping=False,
        isfixed=False,
        version_id=1,
    )

    schema_name = "jpcoar_mapping"
    
    form_data = dict()
    with open("tests/data/oaischema/jpcoar_mapping_form_data.json", "r") as f:
        form_data = json.load(f)

    xsd = dict()
    with open("tests/data/oaischema/jpcoar_mapping_xsd.json", "r") as f:
        xsd = json.load(f)

    namespaces = dict()
    with open("tests/data/oaischema/jpcoar_mapping_namespaces.json", "r") as f:
        namespaces = json.load(f)
    
    schema_location = "https://github.com/JPCOAR/schema/blob/master/2.0/jpcoar_scm.xsd"
    jpcoarv2 = OAIServerSchema(
        id=uuid.uuid4(),
        schema_name=schema_name,
        form_data=form_data,
        xsd=json.dumps(xsd),
        namespaces=namespaces,
        schema_location=schema_location,
        isvalid=True,
        is_mapping=False,
        isfixed=False,
        version_id=1,
    )

    schema_name = "jpcoar_v1_mapping"
    
    form_data = dict()
    with open("tests/data/oaischema/jpcoar_v1_mapping_form_data.json", "r") as f:
        form_data = json.load(f)

    xsd = dict()
    with open("tests/data/oaischema/jpcoar_v1_mapping_xsd.json", "r") as f:
        xsd = json.load(f)

    namespaces = dict()
    with open("tests/data/oaischema/jpcoar_v1_mapping_namespaces.json", "r") as f:
        namespaces = json.load(f)

    schema_location = "https://github.com/JPCOAR/schema/blob/master/1.0/jpcoar_scm.xsd"
    jpcoarv1 = OAIServerSchema(
        id=uuid.uuid4(),
        schema_name=schema_name,
        form_data=form_data,
        xsd=json.dumps(xsd),
        namespaces=namespaces,
        schema_location=schema_location,
        isvalid=True,
        is_mapping=False,
        isfixed=False,
        version_id=1,
    )

    schema_name = "oai_dc_mapping"
    form_data = dict()
    with open("tests/data/oaischema/oai_dc_mapping_form_data.json", "r") as f:
        form_data = json.load(f)

    xsd = dict()
    with open("tests/data/oaischema/oai_dc_mapping_xsd.json", "r") as f:
        xsd = json.load(f)

    namespaces = dict()
    with open("tests/data/oaischema/oai_dc_mapping_namespaces.json", "r") as f:
        namespaces = json.load(f)

    schema_location = "http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd"
    oaidc = OAIServerSchema(
        id=uuid.uuid4(),
        schema_name=schema_name,
        form_data=form_data,
        xsd=json.dumps(xsd),
        namespaces=namespaces,
        schema_location=schema_location,
        isvalid=True,
        is_mapping=False,
        isfixed=False,
        version_id=1,
        target_namespace="oai_dc",
    )

    
    with db.session.begin_nested():
        db.session.add(ddi25)
        db.session.add(jpcoarv1)
        db.session.add(jpcoarv2)
        db.session.add(oaidc)
    db.session.commit()


@pytest.fixture()
def db_itemtype(app, db):
    item_type_name = ItemTypeName(
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
        name_id=1,
        harvesting_type=True,
        schema=item_type_schema,
        form=item_type_form,
        render=item_type_render,
        tag=1,
        version_id=1,
        is_deleted=False,
    )

    item_type_mapping = ItemTypeMapping(item_type_id=1, mapping=item_type_mapping)

    with db.session.begin_nested():
        db.session.add(item_type_name)
        db.session.add(item_type)
        db.session.add(item_type_mapping)

    return {"item_type_name": item_type_name, "item_type": item_type}


@pytest.fixture()
def db_itemtype_jdcat(app, db):
    item_type_name = ItemTypeName(
        name="テストアイテムタイプ", has_site_license=True, is_active=True
    )
    item_type_schema = dict()
    with open("tests/data/itemtype_jdcat_schema.json", "r") as f:
        item_type_schema = json.load(f)

    item_type_form = dict()
    with open("tests/data/itemtype_jdcat_form.json", "r") as f:
        item_type_form = json.load(f)

    item_type_render = dict()
    with open("tests/data/itemtype_jdcat_render.json", "r") as f:
        item_type_render = json.load(f)

    item_type_mapping = dict()
    with open("tests/data/itemtype_jdcat_mapping.json", "r") as f:
        item_type_mapping = json.load(f)

    item_type = ItemType(
        name_id=1,
        harvesting_type=True,
        schema=item_type_schema,
        form=item_type_form,
        render=item_type_render,
        tag=1,
        version_id=1,
        is_deleted=False,
    )

    item_type_mapping = ItemTypeMapping(item_type_id=1, mapping=item_type_mapping)

    with db.session.begin_nested():
        db.session.add(item_type_name)
        db.session.add(item_type)
        db.session.add(item_type_mapping)

    return {"item_type_name": item_type_name, "item_type": item_type}

@pytest.fixture()
def db_sessionlifetime(app, db):
    session_lifetime = SessionLifetime(lifetime=60, is_delete=False)
    with db.session.begin_nested():
        db.session.add(session_lifetime)

@pytest.yield_fixture()
def client(app):
    with app.test_client() as client:
        yield client


@pytest.fixture()
def esindex(app):
    current_search_client.indices.delete(index="test-*")
    # print(app.config["INDEXER_DEFAULT_INDEX"])
    with open("tests/data/mappings/v6/weko/item-v1.0.0.json", "r") as f:
        mapping = json.load(f)
    try:
        current_search_client.indices.create(
            app.config["INDEXER_DEFAULT_INDEX"], body=mapping
        )
        current_search_client.indices.put_alias(
            index=app.config["INDEXER_DEFAULT_INDEX"], name="test-weko"
        )
        
        es = Elasticsearch(
            [app.config['SEARCH_ELASTIC_HOSTS']],
            scheme="http",
            port=9200
        )
        p = IngestClient(es)
        p.put_pipeline(id='item-file-pipeline', body={
            'description': "Index contents of each file.",
            'processors' : [
                {
                    'foreach': {
                        'field': 'content',
                        'processor': {
                            'attachment': {
                                'indexed_chars' : -1,
                                'target_field': '_ingest._value.attachment',
                                'field': '_ingest._value.file',
                                'properties': [
                                    'content'
                                    ]
                                }
                            }
                        }
                    },
                {
                    'foreach': {
                        'field': 'content',
                        'processor': {
                            'remove': {
                                'field': '_ingest._value.file'
                                }
                            }
                        }
                    }
                ]})
    except:
        current_search_client.indices.create("test-weko-items", body=mapping)
        current_search_client.indices.put_alias(
            index="test-weko-items", name="test-weko"
        )
    try:
        # print index mapping
        # print(current_search_client.indices.get_mapping(index="test-weko"))
        yield current_search_client
    finally:
        current_search_client.indices.delete(index="test-*")


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

    with db.session.begin_nested():
        db.session.add(item_type_name)
        db.session.add(item_type)
        db.session.add(item_type_mapping)

    return {
        "item_type_name": item_type_name,
        "item_type": item_type,
        "item_type_mapping": item_type_mapping,
    }


@pytest.fixture()
def records(app, db, esindex, indextree, location, itemtypes, db_oaischema):
    indexer = WekoIndexer()
    indexer.get_es_index()
    results = []
    with app.test_request_context():
        i = 1
        filename = "helloworld.pdf"
        mimetype = "application/pdf"
        filepath = "tests/data/helloworld.pdf"
        results.append(make_record(db, indexer, i, filepath, filename, mimetype))
        
        i = 2
        filename = "helloworld.docx"
        mimetype = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        filepath = "tests/data/helloworld.docx"
        results.append(make_record(db, indexer, i, filepath, filename, mimetype))
        il = ItemLink(str(i))
        il.bulk_update([{"item_id": "1", "sele_id": "isVersionOf"}])

        i = 3
        filename = "helloworld.zip"
        mimetype = "application/zip"
        filepath = "tests/data/helloworld.zip"
        results.append(make_record(db, indexer, i, filepath, filename, mimetype))
        il = ItemLink(str(i))
        il.bulk_update([{"item_id": "1", "sele_id": "isCitedBy"}])

    # es = Elasticsearch("http://{}:9200".format(app.config["SEARCH_ELASTIC_HOSTS"]))
    # print(es.cat.indices())
    return indexer, results


def make_record(db, indexer, i, filepath, filename, mimetype):
    record_data = {
        "_oai": {
            "id": "oai:weko3.example.org:000000{:02d}".format(i),
            "sets": ["{}".format((i % 2) + 1)],
        },
        "path": ["{}".format((i % 2) + 1)],
        "owner": "1",
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
                },
                {
                    "subitem_1522300695726": "Issued",
                    "subitem_1522300722591": "2021-06-30",
                },
                {
                    "subitem_1522300695726": "Issued",
                    "subitem_1522300722591": "2021-06",
                },
                {
                    "subitem_1522300695726": "Issued",
                    "subitem_1522300722591": "2021",
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
                },
                {
                    "subitem_identifier_uri": "http://doi/001",
                    "subitem_identifier_type": "DOI",
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
                            "nameIdentifier": "000001",
                            "nameIdentifierURI": "https://orcid.org/",
                            "nameIdentifierScheme": "ORCID",
                        },
                        {
                            "nameIdentifier": "000001",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                            "nameIdentifierScheme": "CiNii",
                        },
                        {
                            "nameIdentifier": "000001",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                            "nameIdentifierScheme": "KAKEN2",
                        },
                    ],
                    "contributorMails": [{"contributorMail": "test1@nii.ac.jp"}],
                    "contributorNames": [
                        {"lang": "ja", "contributorName": "情報, 太郎"},
                        {"lang": "ja-Kana", "contributorName": "ジョウホウ, タロウ"},
                        {"lang": "en", "contributorName": "Joho, Taro"},
                    ],
                    "contributorAffiliations":[
                        {
                            "contributorAffiliationNames": [
                                {
                                    "contributorAffiliationName": "University",
                                    "contributorAffiliationNameLang": "en",
                                }
                            ],
                            "contributorAffiliationNameIdentifiers": [
                                {
                                    "contributorAffiliationNameIdentifier": "0000000123456788",
                                    "contributorAffiliationURI": "http://isni.org/isni/0000000123456788",
                                    "contributorAffiliationScheme": "ISNI",
                                }
                            ],
                        }
                    ]
                },
                {
                    "givenNames": [
                        {"givenName": "二郎", "givenNameLang": "ja"},
                        {"givenName": "ニロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Niro", "givenNameLang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "contributorType": "Distributor",
                    "nameIdentifiers": [
                        {
                            "nameIdentifier": "000002",
                            "nameIdentifierURI": "https://orcid.org/",
                            "nameIdentifierScheme": "ORCID",
                        },
                        {
                            "nameIdentifier": "000002",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                            "nameIdentifierScheme": "CiNii",
                        },
                        {
                            "nameIdentifier": "000002",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                            "nameIdentifierScheme": "KAKEN2",
                        },
                    ],
                    "contributorMails": [{"contributorMail": "test2@nii.ac.jp"}],
                    "contributorNames": [
                        {"lang": "ja", "contributorName": "情報, 二郎"},
                        {"lang": "ja-Kana", "contributorName": "ジョウホウ, ニロウ"},
                        {"lang": "en", "contributorName": "Joho, Niro"},
                    ],
                },
                {
                    "givenNames": [
                        {"givenName": "三郎", "givenNameLang": "ja"},
                        {"givenName": "サンロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Sanro", "givenNameLang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "contributorType": "Other",
                    "nameIdentifiers": [
                        {
                            "nameIdentifier": "000003",
                            "nameIdentifierURI": "https://orcid.org/",
                            "nameIdentifierScheme": "ORCID",
                        },
                        {
                            "nameIdentifier": "000003",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                            "nameIdentifierScheme": "CiNii",
                        },
                        {
                            "nameIdentifier": "000003",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                            "nameIdentifierScheme": "KAKEN2",
                        },
                    ],
                    "contributorMails": [{"contributorMail": "test3@nii.ac.jp"}],
                    "contributorNames": [
                        {"lang": "ja", "contributorName": "情報, 三郎"},
                        {"lang": "ja-Kana", "contributorName": "ジョウホウ, サンロウ"},
                        {"lang": "en", "contributorName": "Joho, Sanro"},
                    ],
                },
                {
                    "givenNames": [
                        {"givenName": "四郎", "givenNameLang": "ja"},
                        {"givenName": "シロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Siro", "givenNameLang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "contributorType": "DataCollector",
                    "nameIdentifiers": [
                        {
                            "nameIdentifier": "000004",
                            "nameIdentifierURI": "https://orcid.org/",
                            "nameIdentifierScheme": "ORCID",
                        },
                        {
                            "nameIdentifier": "000004",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                            "nameIdentifierScheme": "CiNii",
                        },
                        {
                            "nameIdentifier": "000004",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                            "nameIdentifierScheme": "KAKEN2",
                        },
                    ],
                    "contributorMails": [{"contributorMail": "test4@nii.ac.jp"}],
                    "contributorNames": [
                        {"lang": "ja", "contributorName": "情報, 四郎"},
                        {"lang": "ja-Kana", "contributorName": "ジョウホウ, シロウ"},
                        {"lang": "en", "contributorName": "Joho, Siro"},
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
                        "subitem_1522306436033": "001",
                    },
                    "subitem_1523320863692": [
                        {
                            "subitem_1523320867455": "en",
                            "subitem_1523320909613": "Related Title",
                        }
                    ],
                },
                {
                    "subitem_1522306207484": "isReferencedBy",
                    "subitem_1522306287251": {
                        "subitem_1522306382014": "arXiv",
                        "subitem_1522306436033": "002",
                    },
                    "subitem_1523320863692": [
                        {
                            "subitem_1523320867455": "en",
                            "subitem_1523320909613": "Related Title",
                        }
                    ],
                },
                {
                    "subitem_1522306207484": "isSupplementedBy",
                    "subitem_1522306287251": {
                        "subitem_1522306382014": "arXiv",
                        "subitem_1522306436033": "003",
                    },
                    "subitem_1523320863692": [
                        {
                            "subitem_1523320867455": "en",
                            "subitem_1523320909613": "Related Title",
                        }
                    ],
                },
                {
                    "subitem_1522306207484": "isPartOf",
                    "subitem_1522306287251": {
                        "subitem_1522306382014": "arXiv",
                        "subitem_1522306436033": "004",
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
        "item_filemeta": {
            "attribute_name": "File",
            "attribute_type": "file",
            "attribute_value_mlt": [
                {
                    "url": {
                        "url": "https://weko3.example.org/record/{0}/files/{1}".format(
                            i, filename
                        )
                    },
                    "date": [{"dateType": "Available", "dateValue": "2021-07-12"},
                             {"dateType": "Issued", "dateValue": "2021"}],
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
                            "nameIdentifier": "0001",
                            "nameIdentifierURI": "https://orcid.org/",
                            "nameIdentifierScheme": "ORCID",
                        },
                        {
                            "nameIdentifier": "0002",
                            "nameIdentifierURI": "https://e-rad.org/",
                            "nameIdentifierScheme": "e-Rad",
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
            },
            {
                "subitem_1522300695726": "Issued",
                "subitem_1522300722591": "2021-06-30",
            },
            {
                "subitem_1522300695726": "Issued",
                "subitem_1522300722591": "2021-06",
            },
            {
                "subitem_1522300695726": "Issued",
                "subitem_1522300722591": "2021",
            }
        ],
        "item_1617186702042": [{"subitem_1551255818386": "jpn"}],
        "item_1617186783814": [
            {
                "subitem_identifier_uri": "http://localhost",
                "subitem_identifier_type": "URI",
            },
            {
                "subitem_identifier_uri": "http://doi/001",
                "subitem_identifier_type": "DOI",
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
                "contributorAffiliations":[
                    {
                        "contributorAffiliationNames":[
                            {
                                "contributorAffiliationName":"University",
                                "contributorAffiliationNameLang":"en"
                            }
                        ],
                        "contributorAffiliationNameIdentifiers":[
                            {
                                "contributorAffiliationURI":"0000000123456788",
                                "contributorAffiliationScheme":"http://isni.org/isni/0000000123456788",
                                "contributorAffiliationNameIdentifier":"ISNI"
                            }
                        ]
                    }
                ]
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
        "item_filemeta": [
            {
                "url": {
                    "url": "https://weko3.example.org/record/{0}/files/{1}".format(
                        i, filename
                    )
                },
                "date": [{"dateType": "Available", "dateValue": "2021-07-12"},
                         {"dateType": "Issued", "dateValue": "2021"}],
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
    if i == 1:
        record_data['item_1617258105262']['attribute_value_mlt'][0]['resourcetype'] = 'experimental data'
        item_data['item_1617258105262']['resourcetype'] = 'experimental data'

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

    # print(record_data)
    record = WekoRecord.create(record_data, id_=rec_uuid)
    # print(current_search_client.indices.get_mapping(index="test-weko"))
    # from six import BytesIO
    import base64

    bucket = Bucket.create()
    record_buckets = RecordsBuckets.create(record=record.model, bucket=bucket)

    # stream = BytesIO(b"Hello, World")
    obj = None
    with open(filepath, "rb") as f:
        stream = BytesIO(f.read())
        record.files[filename] = stream
        record["item_filemeta"]["attribute_value_mlt"][0]["file"] = (
            base64.b64encode(stream.getvalue())
        ).decode("utf-8")
    with open(filepath, "rb") as f:
        obj = ObjectVersion.create(bucket=bucket.id, key=filename, stream=f)
    deposit = aWekoDeposit(record, record.model)
    deposit.commit()
    record["item_filemeta"]["attribute_value_mlt"][0]["version_id"] = str(
        obj.version_id
    )

    record_data["content"] = [
        {
            "date": [{"dateValue": "2021-07-12", "dateType": "Available"},
                     {"dateValue": "2021", "dateType": "Issued"}],
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
    record_v1["item_filemeta"]["attribute_value_mlt"][0]["file"] = (
        base64.b64encode(stream.getvalue())
    ).decode("utf-8")
    deposit_v1 = aWekoDeposit(record_v1, record_v1.model)
    deposit_v1.commit()
    record_v1["item_filemeta"]["attribute_value_mlt"][0]["version_id"] = str(
        obj_v1.version_id
    )

    record_data_v1 = copy.deepcopy(record_data)
    record_data_v1["content"] = [
        {
            "date": [{"dateValue": "2021-07-12", "dateType": "Available"},
                     {"dateValue": "2021", "dateType": "Issued"}],
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
