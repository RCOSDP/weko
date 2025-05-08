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

import os
import json
import shutil
import tempfile
import copy
import uuid
from unittest.mock import patch, MagicMock
from collections import OrderedDict
from elasticsearch import Elasticsearch
import time
from datetime import datetime

import pytest
from flask import Flask
from flask_menu import Menu
from flask_babelex import Babel
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import User, Role
from invenio_access.models import ActionRoles, ActionUsers
from invenio_accounts.testutils import create_test_user
from invenio_access import InvenioAccess
from invenio_access.models import ActionUsers
from invenio_admin import InvenioAdmin
from invenio_assets import InvenioAssets
from invenio_db import InvenioDB, db as db_
from invenio_cache import InvenioCache
from invenio_communities.models import Community
from weko_user_profiles.models import UserProfile
from invenio_deposit import InvenioDeposit
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.views import blueprint as invenio_files_rest_blueprint
from invenio_files_rest.models import Bucket, Location, ObjectVersion
from invenio_pidstore.models import PersistentIdentifier, PIDStatus, Redirect
from invenio_i18n import InvenioI18N
from weko_index_tree.api import Indexes
from weko_index_tree.models import Index
from invenio_indexer import InvenioIndexer
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_pidrelations import InvenioPIDRelations
from invenio_pidstore import InvenioPIDStore
from invenio_records import InvenioRecords
from invenio_records_rest import InvenioRecordsREST
from invenio_records_rest.utils import PIDConverter
from invenio_search import InvenioSearch
from invenio_search_ui import InvenioSearchUI
from invenio_stats.config import SEARCH_INDEX_PREFIX as index_prefix
from six import BytesIO
from simplekv.memory.redisstore import RedisStore
from sqlalchemy_utils.functions import create_database, database_exists, drop_database
from weko_admin import WekoAdmin
from weko_admin.models import AdminSettings
from weko_items_ui import WekoItemsUI
from weko_records import WekoRecords

# from weko_records_ui import WekoRecordsUI
from weko_search_ui import WekoSearchUI
from weko_search_ui.config import WEKO_SEARCH_MAX_RESULT
from weko_index_tree import WekoIndexTree, WekoIndexTreeREST

from weko_theme import WekoTheme
from weko_groups import WekoGroups
from invenio_pidrelations.models import PIDRelation
from weko_records.models import ItemType, ItemTypeMapping, ItemTypeName
from weko_records.api import ItemsMetadata, WekoRecord
from weko_schema_ui.models import OAIServerSchema
from weko_schema_ui.config import WEKO_SCHEMA_JPCOAR_V1_SCHEMA_NAME,WEKO_SCHEMA_DDI_SCHEMA_NAME
from weko_deposit import WekoDeposit, WekoDepositREST
from weko_records.utils import get_options_and_order_list
from weko_user_profiles.models import UserProfile
from weko_user_profiles.config import USERPROFILES_LANGUAGE_DEFAULT, \
    USERPROFILES_TIMEZONE_DEFAULT
from weko_workflow.models import Action, ActionStatus,Activity, WorkFlow,FlowAction,FlowDefine
from weko_deposit.api import WekoRecord,_FormatSysBibliographicInformation
from weko_deposit.views import blueprint
from weko_deposit.storage import WekoFileStorage
from weko_deposit.api import WekoDeposit as aWekoDeposit, WekoIndexer
from weko_deposit.config import (
    WEKO_BUCKET_QUOTA_SIZE,
    WEKO_DEPOSIT_REST_ENDPOINTS as _WEKO_DEPOSIT_REST_ENDPOINTS,
    _PID,
    DEPOSIT_REST_ENDPOINTS as _DEPOSIT_REST_ENDPOINTS,
)
from weko_index_tree.config import (
    WEKO_INDEX_TREE_REST_ENDPOINTS as _WEKO_INDEX_TREE_REST_ENDPOINTS,
)
from invenio_accounts.testutils import login_user_via_session

from tests.helpers import json_data, create_record


@pytest.yield_fixture()
def instance_path():
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.fixture()
def base_app(instance_path):
    """Flask application fixture."""

    app_ = Flask('testapp', instance_path=instance_path)
    app_.url_map.converters["pid"] = PIDConverter
    # initialize InvenioDeposit first in order to detect any invalid dependency
    # WEKO_DEPOSIT_REST_ENDPOINTS = copy.deepcopy(_DEPOSIT_REST_ENDPOINTS)
    DEPOSIT_REST_ENDPOINTS = copy.deepcopy(_DEPOSIT_REST_ENDPOINTS)
    WEKO_DEPOSIT_REST_ENDPOINTS = copy.deepcopy(_WEKO_DEPOSIT_REST_ENDPOINTS)
    WEKO_DEPOSIT_REST_ENDPOINTS["depid"][
        "rdc_route"
    ] = "/deposits/redirect/<{0}:pid_value>".format(_PID)
    WEKO_DEPOSIT_REST_ENDPOINTS["depid"][
        "pub_route"
    ] = "/deposits/publish/<{0}:pid_value>".format(_PID)
    WEKO_INDEX_TREE_REST_ENDPOINTS = copy.deepcopy(_WEKO_INDEX_TREE_REST_ENDPOINTS)
    WEKO_INDEX_TREE_REST_ENDPOINTS["tid"]["index_route"] = "/tree/index/<int:index_id>"

    app_.config.update(
        CELERY_ALWAYS_EAGER=True,
        CELERY_CACHE_BACKEND="memory",
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_RESULT_BACKEND="cache",
        CACHE_REDIS_URL=os.environ.get(
            "CACHE_REDIS_URL", "redis://redis:6379/0"
        ),
        CACHE_REDIS_DB=0,
        CACHE_REDIS_HOST="redis",
        REDIS_PORT="6379",
        JSONSCHEMAS_URL_SCHEME="http",
        SECRET_KEY="CHANGE_ME",
        SECURITY_PASSWORD_SALT="CHANGE_ME_ALSO",
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI',
            'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     "SQLALCHEMY_DATABASE_URI", "sqlite:///test.db"
        # ),
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
        SEARCH_UI_SEARCH_INDEX="{}-weko".format("test"),
        INDEXER_DEFAULT_DOCTYPE="item-v1.0.0",
        INDEXER_DEFAULT_DOC_TYPE="item-v1.0.0",
        INDEXER_FILE_DOC_TYPE="content",
        WEKO_BUCKET_QUOTA_SIZE=WEKO_BUCKET_QUOTA_SIZE,
        WEKO_MAX_FILE_SIZE=WEKO_BUCKET_QUOTA_SIZE,
        INDEX_IMG="indextree/36466818-image.jpg",
        WEKO_SEARCH_MAX_RESULT=WEKO_SEARCH_MAX_RESULT,
        DEPOSIT_REST_ENDPOINTS=DEPOSIT_REST_ENDPOINTS,
        WEKO_DEPOSIT_REST_ENDPOINTS=WEKO_DEPOSIT_REST_ENDPOINTS,
        WEKO_INDEX_TREE_STYLE_OPTIONS={
            "id": "weko",
            "widths": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"],
        },
        WEKO_INDEX_TREE_UPATED=True,
        WEKO_INDEX_TREE_REST_ENDPOINTS=WEKO_INDEX_TREE_REST_ENDPOINTS,
        I18N_LANGUAGES=[("ja", "Japanese"), ("en", "English"),("da", "Danish")],
        SERVER_NAME="TEST_SERVER",
        SEARCH_ELASTIC_HOSTS=os.environ.get("SEARCH_ELASTIC_HOSTS", "elasticsearch"),
        SEARCH_INDEX_PREFIX="test-",
        WEKO_SCHEMA_JPCOAR_V1_SCHEMA_NAME=WEKO_SCHEMA_JPCOAR_V1_SCHEMA_NAME,
        WEKO_SCHEMA_DDI_SCHEMA_NAME=WEKO_SCHEMA_DDI_SCHEMA_NAME,
        WEKO_PERMISSION_SUPER_ROLE_USER=[
            "System Administrator",
            "Repository Administrator",
        ],
        WEKO_PERMISSION_ROLE_COMMUNITY=["Community Administrator"],
        WEKO_SCHEMA_JPCOAR_V2_SCHEMA_NAME="jpcoar_mapping",
        WEKO_SCHEMA_JPCOAR_V2_RESOURCE_TYPE_REPLACE={
            "periodical": "journal",
            "interview": "other",
            "internal report": "other",
            "report part": "other",
            "conference object": "conference output",
        }
    )
    # with ESTestServer(timeout=30) as server:
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
    InvenioPIDStore(app_)
    InvenioRecords(app_)
    # client = Elasticsearch(['localhost:%s'%server.port])
    # InvenioSearch(app_, client=client)
    InvenioSearch(app_)
    InvenioSearchUI(app_)
    InvenioPIDRelations(app_)
    InvenioI18N(app_)
    InvenioRecordsREST(app_)
    WekoRecords(app_)
    WekoItemsUI(app_)
    # WekoRecordsUI(app_)
    WekoAdmin(app_)
    WekoSearchUI(app_)
    WekoTheme(app_)
    WekoGroups(app_)
    WekoIndexTree(app_)
    WekoIndexTreeREST(app_)
    Menu(app_)
    # app_.register_blueprint(blueprint)
    app_.register_blueprint(invenio_files_rest_blueprint)  # invenio_files_rest
    # rest_blueprint = create_blueprint(app_, WEKO_DEPOSIT_REST_ENDPOINTS)
    # app_.register_blueprint(rest_blueprint)
    WekoDeposit(app_)
    WekoDepositREST(app_)
    return app_


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with open("tests/data/mappings/item-v1.0.0.json", "r") as f:
        mapping = json.load(f)
    es = Elasticsearch("http://{}:9200".format(base_app.config["SEARCH_ELASTIC_HOSTS"]))
    es.indices.create(
        index=base_app.config["INDEXER_DEFAULT_INDEX"], body=mapping, ignore=[400, 404]
    )
    es.indices.put_alias(
        index=base_app.config["INDEXER_DEFAULT_INDEX"],
        name=base_app.config["SEARCH_UI_SEARCH_INDEX"],
        ignore=[400, 404],
    )
    with base_app.app_context():
        yield base_app
    es.indices.delete_alias(
        index=base_app.config["INDEXER_DEFAULT_INDEX"],
        name=base_app.config["SEARCH_UI_SEARCH_INDEX"],
        ignore=[400, 404],
    )
    es.indices.delete(index=base_app.config["INDEXER_DEFAULT_INDEX"], ignore=[400, 404])

@pytest.yield_fixture()
def i18n_app(app):
    with app.test_request_context(
        headers=[('Accept-Language','ja')]):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        app.extensions['invenio-search'] = MagicMock()
        app.extensions['invenio-i18n'] = MagicMock()
        app.extensions['invenio-i18n'].language = "ja"
        yield app

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


@pytest.fixture()
def records(db):
    record_data = json_data("data/test_records.json")
    item_data = json_data("data/test_items.json")
    record_num = len(record_data)
    result = []
    for d in range(record_num):
        result.append(create_record(record_data[d], item_data[d]))
    db.session.commit()
    yield result


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
def wekofs_testpath(location):
    """Temporary path for WekoFileStorage."""
    return os.path.join(location.uri, 'subpath/data')

@pytest.fixture()
def wekofs(location, wekofs_testpath):
    """Instance of WekoFileStorage."""
    return WekoFileStorage(wekofs_testpath)

@pytest.fixture()
def bucket(db, location):
    """File system location."""
    bucket = Bucket.create(location)
    db.session.commit()
    return bucket


@pytest.fixture()
def testfile(db, bucket):
    """File system location."""
    obj = ObjectVersion.create(bucket, "testfile", stream=BytesIO(b"atest"))
    db.session.commit()
    return obj


@pytest.fixture()
def record(app, db):
    """Create a record."""
    metadata = {"title": "fuu"}
    record = WekoRecord.create(metadata)
    record.commit()
    db.session.commit()
    return record


@pytest.fixture()
def generic_file(app, record):
    """Add a generic file to the record."""
    stream = BytesIO(b"test example")
    filename = "generic_file.txt"
    record.files[filename] = stream
    record.files.dumps()
    record.commit()
    db_.session.commit()
    return filename


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
        
    index = Index()
    db.session.add(index)
    db.session.commit()
    comm = Community.create(community_id="test_com", role_id=sysadmin_role.id,
                            id_user=sysadmin.id, title="test community",
                            description=("this is test community"),
                            root_node_id=index.id)
    db.session.commit()
    
    yield [
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
def deposit(app, location):
    bucket = Bucket(
        default_location=1,
        default_storage_class="S",
        size=0,
        quota_size=app.config["WEKO_BUCKET_QUOTA_SIZE"],
        max_file_size=app.config["WEKO_MAX_FILE_SIZE"],
        locked=False,
        deleted=False,
        location=location,
    )
    with patch("weko_deposit.api.Bucket.create", return_value=bucket):
        deposit = aWekoDeposit.create({})
        return deposit.pid.pid_value


@pytest.fixture()
def db_index(client, users):
    index_metadata = {
        "id": 1,
        "parent": 0,
        "value": "Index(public_state = True,harvest_public_state = True)",
    }

    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        index = Index.get_index_by_id(1)
        if (index is None):
            Indexes.create(0, index_metadata)
            index = Index.get_index_by_id(1)
            index.public_state = True
            index.harvest_public_state = True

    index_metadata = {
        "id": 2,
        "parent": 0,
        "value": "Index(public_state = True,harvest_public_state = False)",
    }

    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        index = Index.get_index_by_id(2)
        if (index is None):
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
        index = Index.get_index_by_id(3)
        if (index is None):
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
        index = Index.get_index_by_id(4)
        if (index is None):
            Indexes.create(0, index_metadata)
            index = Index.get_index_by_id(4)
            index.public_state = False
            index.harvest_public_state = False


@pytest.fixture()
def db_itemtype(app, db):
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

    _item_type_mapping_mapping = dict()
    with open("tests/data/itemtype_mapping.json", "r") as f:
        item_type_mapping_mapping = json.load(f)

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
    created_date = datetime.strptime("2020/01/01 0:00:00.000",'%Y/%m/%d %H:%M:%S.%f')
    updated_date = datetime.strptime("2021/01/01 0:00:00.000",'%Y/%m/%d %H:%M:%S.%f')

    item_type_mapping = ItemTypeMapping(created=created_date, updated=updated_date, id=1, item_type_id=1, mapping=item_type_mapping_mapping)

    with db.session.begin_nested():
        db.session.add(item_type_name)
        db.session.add(item_type)
        db.session.add(item_type_mapping)
    db.session.commit()
    return {
        "item_type_name": item_type_name,
        "item_type": item_type,
        "item_type_mapping": item_type_mapping,
    }


@pytest.fixture()
def es_records(app, db, location, db_itemtype, db_oaischema):
    indexer = WekoIndexer()
    indexer.get_es_index()
    results = []
    item_metadata = {}
    db.session.begin_nested()

    with app.test_request_context():
        def format_number(i, fill_num=None):
            int_part, decimal_part = divmod(i, 1)
            if fill_num:
                int_part_str = str(int(int_part)).zfill(fill_num)
            else:
                int_part_str = str(int(int_part))
            if decimal_part != 0:
                int_part_str += f".{decimal_part:.10f}".strip('0')
            return int_part_str

        def create_record(i, index_id):
            record_data =  {"_oai": {"id": "oai:weko3.example.org:000000{}".format(format_number(i, 2)), "sets": ["{}".format(index_id)]}, "path": ["{}".format(index_id)], "owner": "1", "recid": "{}".format(i), "title": ["title"], "pubdate": {"attribute_name": "PubDate", "attribute_value": "2022-08-20"}, "_buckets": {"deposit": "3e99cfca-098b-42ed-b8a0-20ddd09b3e02"}, "_deposit": {"id": "{}".format(i), "pid": {"type": "depid", "value": "{}".format(i), "revision_id": 0}, "owner": "1", "owners": [1], "status": "draft", "created_by": 1, "owners_ext": {"email": "wekosoftware@nii.ac.jp", "username": "", "displayname": ""}}, "item_title": "title", "author_link": [], "item_type_id": "1", "publish_date": "2022-08-20", "publish_status": "0", "weko_shared_ids": [], "item_1617186331708": {"attribute_name": "Title", "attribute_value_mlt": [{"subitem_1551255647225": "タイトル", "subitem_1551255648112": "ja"},{"subitem_1551255647225": "title", "subitem_1551255648112": "en"}]}, "item_1617258105262": {"attribute_name": "Resource Type", "attribute_value_mlt": [{"resourceuri": "http://purl.org/coar/resource_type/c_5794", "resourcetype": "conference paper"}]}, "relation_version_is_last": True if not "." in str(i) else False, 'item_1617605131499': {'attribute_name': 'File', 'attribute_type': 'file', 'attribute_value_mlt': [{'url': {'url': 'https://weko3.example.org/record/{}/files/hello.txt'.format(i)}, 'date': [{'dateType': 'Available', 'dateValue': '2022-09-07'}], 'format': 'plain/text', 'filename': 'hello.txt', 'filesize': [{'value': '146 KB'}], 'accessrole': 'open_access', 'version_id': '', 'mimetype': 'application/pdf',"file": "",}]}}

            item_data = {"id": "{}".format(i), "pid": {"type": "depid", "value": "{}".format(i), "revision_id": 0}, "lang": "ja", "owner": "1", "title": "title", "owners": [1], "status": "published", "$schema": "/items/jsonschema/1", "pubdate": "2022-08-20", "created_by": 1, "owners_ext": {"email": "wekosoftware@nii.ac.jp", "username": "", "displayname": ""}, "shared_user_ids": [], "item_1617186331708": [{"subitem_1551255647225": "タイトル", "subitem_1551255648112": "ja"},{"subitem_1551255647225": "title", "subitem_1551255648112": "en"}], "item_1617258105262": {"resourceuri": "http://purl.org/coar/resource_type/c_5794", "resourcetype": "conference paper"}}
   
            rec_uuid = uuid.uuid4()

            recid = PersistentIdentifier.create('recid', str(i), object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
            depid = PersistentIdentifier.create('depid', str(i), object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
            rel = PIDRelation.create(recid, depid, 3)
            db.session.add(recid)
            db.session.add(depid)
            db.session.add(rel)

            parent = None
            doi = None
            hdl = None
            parent = PersistentIdentifier.create('parent', "parent:{}".format(i),object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
            db.session.add(parent)
            rel = PIDRelation.create(parent,recid,2,0)
            db.session.add(rel)
            if(i%2==1):
                doi = PersistentIdentifier.create('doi', "https://doi.org/10.xyz/{}".format(format_number(i, 10)),object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
                hdl = PersistentIdentifier.create('hdl', "https://hdl.handle.net/0000/{}".format(format_number(i, 10)),object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)

            record = WekoRecord.create(record_data, id_=rec_uuid)
            # from six import BytesIO
            from invenio_files_rest.models import Bucket
            from invenio_records_files.models import RecordsBuckets
            import base64
            bucket = Bucket.create()
            record_buckets = RecordsBuckets.create(record=record.model, bucket=bucket)
            stream = BytesIO(b'Hello, World')
            record.files['hello.txt'] = stream
            obj=ObjectVersion.create(bucket=bucket.id, key='hello.txt',stream=stream)
            record['item_1617605131499']['attribute_value_mlt'][0]['file'] = (base64.b64encode(stream.getvalue())).decode('utf-8')
            deposit = aWekoDeposit(record, record.model)
            deposit.commit()
            
            record['item_1617605131499']['attribute_value_mlt'][0]['version_id'] = str(obj.version_id)
            record.commit()

            record_data['content']= [{"date":[{"dateValue":"2021-07-12","dateType":"Available"}],"accessrole":"open_access","displaytype" : "simple","filename" : "hello.txt","attachment" : {},"format" : "text/plain","mimetype" : "text/plain","filesize" : [{"value" : "1 KB"}],"version_id" : "{}".format(obj.version_id),"url" : {"url":"http://localhost/record/{}/files/hello.txt".format(i)},"file":(base64.b64encode(stream.getvalue())).decode('utf-8')}]
            indexer.upload_metadata(record_data, rec_uuid, 1, False)
            item = ItemsMetadata.create(item_data, id_=rec_uuid)
            item.commit()
            
            record_info = {'depid':depid, 'recid':recid, 'parent': parent, 'doi':doi, 'hdl': hdl, 'record':record, 'record_data':record_data, 'item':item , 'item_data':item_data, 'deposit': deposit}
            results.append(record_info)

        for i in range(1, 10):
            create_record(i, (i % 2) + 1)
        create_record(10, 4)
        create_record(10.1, 3)
        create_record(10.2, 4)

    time.sleep(3)
    # es = Elasticsearch("http://{}:9200".format(app.config["SEARCH_ELASTIC_HOSTS"]))
    # print(es.cat.indices())

    db.session.commit()
    db.session.expunge_all()
    
    return indexer, results

@pytest.fixture()
def es_records_1(app, db, db_index, location, db_itemtype, db_oaischema):

    indexer = WekoIndexer()
    indexer.get_es_index()
    result = None
    with app.test_request_context():
        record_data =  {"_oai": {"id": "oai:weko3.example.org:000000{:02d}".format(0), "sets": ["1"]}, "path": ["1"], "owner": "1", "recid": "1", "title": ["title"], "pubdate": {"attribute_name": "PubDate", "attribute_value": "2022-08-20"}, "_buckets": {"deposit": "3e99cfca-098b-42ed-b8a0-20ddd09b3e02"}, "_deposit": {"id": "1", "pid": {"type": "depid", "value": "1", "revision_id": 0}, "owner": "1", "owners": [1], "status": "draft", "created_by": 1, "owners_ext": {"email": "wekosoftware@nii.ac.jp", "username": "", "displayname": ""}}, "item_title": "title", "author_link": [], "item_type_id": "1", "publish_date": "2022-08-20", "publish_status": "0", "weko_shared_ids": [1,2,3], "item_1617186331708": {"attribute_name": "Title", "attribute_value_mlt": [{"subitem_1551255647225": "タイトル", "subitem_1551255648112": "ja"},{"subitem_1551255647225": "title", "subitem_1551255648112": "en"}]}, "item_1617258105262": {"attribute_name": "Resource Type", "attribute_value_mlt": [{"resourceuri": "http://purl.org/coar/resource_type/c_5794", "resourcetype": "conference paper"}]}, "relation_version_is_last": True, 'item_1617605131499': {'attribute_name': 'File', 'attribute_type': 'file', 'attribute_value_mlt': [{'url': {'url': 'https://weko3.example.org/record/1/files/hello.txt'}, 'date': [{'dateType': 'Available', 'dateValue': '2023-09-07'}], 'format': 'plain/text', 'filename': 'hello.txt', 'filesize': [{'value': '146 KB'}], 'accessrole': 'open_access', 'version_id': '', 'mimetype': 'application/pdf',"file": "",}]}}

        item_data = {"id": "0", "pid": {"type": "depid", "value": "0", "revision_id": 0}, "lang": "ja", "owner": "1", "title": "title", "owners": [1], "status": "published", "$schema": "/items/jsonschema/1", "pubdate": "2022-08-20", "created_by": 1, "owners_ext": {"email": "wekosoftware@nii.ac.jp", "username": "", "displayname": ""}, "shared_user_ids": [{"user":1},{"user":2},{"user":3}], "item_1617186331708": [{"subitem_1551255647225": "タイトル", "subitem_1551255648112": "ja"},{"subitem_1551255647225": "title", "subitem_1551255648112": "en"}], "item_1617258105262": {"resourceuri": "http://purl.org/coar/resource_type/c_5794", "resourcetype": "conference paper"}}

        rec_uuid = uuid.uuid4()

        recid = PersistentIdentifier.create('recid', "1", object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
        depid = PersistentIdentifier.create('depid', "1", object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
        rel = PIDRelation.create(recid,depid,3)
        db.session.add(rel)
        db.session.commit()
        parent = None
        doi = None
        parent = PersistentIdentifier.create('parent', "parent:0",object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
        rel = PIDRelation.create(parent,recid,2,0)
        db.session.add(rel)
        
        record = WekoRecord.create(record_data, id_=rec_uuid)
        # from six import BytesIO
        from invenio_files_rest.models import Bucket
        from invenio_records_files.models import RecordsBuckets
        import base64
        bucket = Bucket.create()
        record_buckets = RecordsBuckets.create(record=record.model, bucket=bucket)
        stream = BytesIO(b'Hello, World')
        record.files['hello.txt'] = stream
        obj=ObjectVersion.create(bucket=bucket.id, key='hello.txt',stream=stream)
        record['item_1617605131499']['attribute_value_mlt'][0]['file'] = (base64.b64encode(stream.getvalue())).decode('utf-8')
        deposit = aWekoDeposit(record, record.model)
        deposit.commit()
        record['item_1617605131499']['attribute_value_mlt'][0]['version_id'] = str(obj.version_id)
        
        record_data['content']= [{"date":[{"dateValue":"2021-07-12","dateType":"Available"}],"accessrole":"open_access","displaytype" : "simple","filename" : "hello.txt","attachment" : {},"format" : "text/plain","mimetype" : "text/plain","filesize" : [{"value" : "1 KB"}],"version_id" : "{}".format(obj.version_id),"url" : {"url":"http://localhost/record/0/files/hello.txt"},"file":(base64.b64encode(stream.getvalue())).decode('utf-8')}]
        indexer.upload_metadata(record_data, rec_uuid, 1, False)
        item = ItemsMetadata.create(item_data, id_=rec_uuid)
        
        result = {"depid":depid, "recid":recid, "parent": parent, "doi":doi, "record":record, "record_data":record_data,"item":item , "item_data":item_data,"deposit": deposit}

    time.sleep(3)
    db.session.commit()
    
    return indexer, result

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
        schema_name='jpcoar_v1_mapping',
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
def prepare_formatsysbib():
    meta=[{'bibliographicPageEnd': '100', 'bibliographic_titles': [{'bibliographic_title': '雑誌タイトル', 'bibliographic_titleLang': 'ja'},{'bibliographic_title': 'Journal Title', 'bibliographic_titleLang': 'en'}], 'bibliographicPageStart': '1', 'bibliographicIssueDates': {'bibliographicIssueDate': '2022-08-29', 'bibliographicIssueDateType': 'Issued'}, 'bibliographicIssueNumber': '12', 'bibliographicVolumeNumber': '1', 'bibliographicNumberOfPages': '99'}]
    props = [['pubdate', 'PubDate', 'PubDate', {'required': True, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186331708', 'Title', 'Title', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186331708[].subitem_1551255647225', 'Title', 'Title', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186331708[].subitem_1551255648112', 'Language', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186385884', 'Alternative Title', 'Alternative Title', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186385884[].subitem_1551255720400', 'Alternative Title', 'Alternative Title', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186385884[].subitem_1551255721061', 'Language', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186419668', 'Creator', 'Creator', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186419668[].authorInputButton', '著者DBから入力', '著者DBから入力', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186419668[].nameIdentifiers', '作成者識別子', 'Creator Identifier', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186419668[].nameIdentifiers[].nameIdentifierScheme', '作成者識別子Scheme', 'Creator Identifier Scheme', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186419668[].nameIdentifiers[].nameIdentifierURI', '作成者識別子URI', 'Creator Identifier URI', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186419668[].nameIdentifiers[].nameIdentifier', '作成者識別子', 'Creator Identifier', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186419668[].creatorNames', '作成者姓名', 'Creator Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186419668[].creatorNames[].creatorName', '姓名', 'Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186419668[].creatorNames[].creatorNameLang', '言語', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186419668[].familyNames', '作成者姓', 'Creator Family Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186419668[].familyNames[].familyName', '姓', 'Family Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186419668[].familyNames[].familyNameLang', '言語', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186419668[].givenNames', '作成者名', 'Creator Given Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186419668[].givenNames[].givenName', '名', 'Given Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186419668[].givenNames[].givenNameLang', '言語', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186419668[].creatorAlternatives', '作成者別名', 'Creator Alternative Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186419668[].creatorAlternatives[].creatorAlternative', '別名', 'Alternative Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186419668[].creatorAlternatives[].creatorAlternativeLang', '言語', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186419668[].creatorMails', '作成者メールアドレス', 'Creator Email Address', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186419668[].creatorMails[].creatorMail', 'メールアドレス', 'Email Address', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186419668[].creatorAffiliations', '作成者所属', 'Affiliation Name Identifier', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186419668[].creatorAffiliations[].affiliationNameIdentifiers', '所属機関識別子', 'Affiliation Name Identifier', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186419668[].creatorAffiliations[].affiliationNameIdentifiers[].affiliationNameIdentifier', '所属機関識別子', 'Affiliation Name Identifier', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186419668[].creatorAffiliations[].affiliationNameIdentifiers[].affiliationNameIdentifierScheme', '所属機関識別子スキーマ', 'Affiliation Name Identifier Scheme', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186419668[].creatorAffiliations[].affiliationNameIdentifiers[].affiliationNameIdentifierURI', '所属機関識別子URI', 'Affiliation Name Identifier URI', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186419668[].creatorAffiliations[].affiliationNames', '所属機関名', 'Affiliation Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186419668[].creatorAffiliations[].affiliationNames[].affiliationName', '所属機関名', 'Affiliation Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186419668[].creatorAffiliations[].affiliationNames[].affiliationNameLang', '言語', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349709064', 'Contributor', 'Contributor', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349709064[].contributorType', '寄与者タイプ', 'Contributor Type', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349709064[].nameIdentifiers', '寄与者識別子', 'Contributor Identifier', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349709064[].nameIdentifiers[].nameIdentifierScheme', '寄与者識別子Scheme', 'Contributor Identifier Scheme', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349709064[].nameIdentifiers[].nameIdentifierURI', '寄与者識別子URI', 'Contributor Identifier URI', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349709064[].nameIdentifiers[].nameIdentifier', '寄与者識別子', 'Contributor Identifier', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349709064[].contributorNames', '寄与者姓名', 'Contributor Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349709064[].contributorNames[].contributorName', '姓名', 'Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349709064[].contributorNames[].lang', '言語', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349709064[].familyNames', '寄与者姓', 'Contributor Family Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349709064[].familyNames[].familyName', '姓', 'Family Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349709064[].familyNames[].familyNameLang', '言語', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349709064[].givenNames', '寄与者名', 'Contributor Given Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349709064[].givenNames[].givenName', '名', 'Given Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349709064[].givenNames[].givenNameLang', '言語', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349709064[].contributorAlternatives', '寄与者別名', 'Contributor Alternative Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349709064[].contributorAlternatives[].contributorAlternative', '別名', 'Alternative Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349709064[].contributorAlternatives[].contributorAlternativeLang', '言語', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349709064[].contributorAffiliations', '寄与者所属', 'Affiliation Name Identifier', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349709064[].contributorAffiliations[].contributorAffiliationNameIdentifiers', '所属機関識別子', 'Affiliation Name Identifier', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349709064[].contributorAffiliations[].contributorAffiliationNameIdentifiers[].contributorAffiliationNameIdentifier', '所属機関識別子', 'Affiliation Name Identifier', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349709064[].contributorAffiliations[].contributorAffiliationNameIdentifiers[].contributorAffiliationScheme', '所属機関識別子スキーマ', 'Affiliation Name Identifier Scheme', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349709064[].contributorAffiliations[].contributorAffiliationNameIdentifiers[].contributorAffiliationURI', '所属機関識別子URI', 'Affiliation Name Identifier URI', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349709064[].contributorAffiliations[].contributorAffiliationNames', '所属機関名', 'Affiliation Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349709064[].contributorAffiliations[].contributorAffiliationNames[].contributorAffiliationName', '所属機関名', 'Affiliation Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349709064[].contributorAffiliations[].contributorAffiliationNames[].contributorAffiliationNameLang', '言語', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349709064[].contributorMails', '寄与者メールアドレス', 'Contributor Email Address', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349709064[].contributorMails[].contributorMail', 'メールアドレス', 'Email Address', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349709064[].authorInputButton', '著者DBから入力', '著者DBから入力', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186476635', 'Access Rights', 'Access Rights', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186476635.subitem_1522299639480', 'アクセス権', 'Access Rights', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186476635.subitem_1600958577026', 'アクセス権URI', 'Access Rights URI', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617351524846', 'APC', 'APC', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617351524846.subitem_1523260933860', 'APC', 'APC', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186499011', 'Rights', 'Rights', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186499011[].subitem_1522650717957', '言語', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186499011[].subitem_1522650727486', '権利情報Resource', 'Rights Information Resource', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186499011[].subitem_1522651041219', '権利情報', 'Rights Information', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617610673286', 'Rights Holder', 'Rights Holder', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617610673286[].nameIdentifiers', '権利者識別子', 'Right Holder Identifier', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617610673286[].nameIdentifiers[].nameIdentifierScheme', '権利者識別子Scheme', 'Right Holder Identifier Scheme', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617610673286[].nameIdentifiers[].nameIdentifierURI', '権利者識別子URI', 'Right Holder Identifier URI', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617610673286[].nameIdentifiers[].nameIdentifier', '権利者識別子', 'Right Holder Identifier', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617610673286[].rightHolderNames', '権利者名', 'Right Holder Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617610673286[].rightHolderNames[].rightHolderLanguage', '言語', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617610673286[].rightHolderNames[].rightHolderName', '権利者名', 'Right Holder Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186609386', 'Subject', 'Subject', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186609386[].subitem_1522299896455', '言語', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186609386[].subitem_1522300014469', '主題Scheme', 'Subject Scheme', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186609386[].subitem_1522300048512', '主題URI', 'Subject URI', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186609386[].subitem_1523261968819', '主題', 'Subject', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186626617', 'Description', 'Description', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186626617[].subitem_description_type', '内容記述タイプ', 'Description Type', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186626617[].subitem_description', '内容記述', 'Description', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186626617[].subitem_description_language', '言語', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186643794', 'Publisher', 'Publisher', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186643794[].subitem_1522300295150', '言語', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186643794[].subitem_1522300316516', '出版者', 'Publisher', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186660861', 'Date', 'Date', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186660861[].subitem_1522300695726', '日付タイプ', 'Date Type', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186660861[].subitem_1522300722591', '日付', 'Date', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186702042', 'Language', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186702042[].subitem_1551255818386', 'Language', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617258105262', 'Resource Type', 'Resource Type', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617258105262.resourcetype', '資源タイプ', 'Resource Type', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617258105262.resourceuri', '資源タイプ識別子', 'Resource Type Identifier', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349808926', 'Version', 'Version', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617349808926.subitem_1523263171732', 'バージョン情報', 'Version', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617265215918', 'Version Type', 'Version Type', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617265215918.subitem_1522305645492', '出版タイプ', 'Version Type', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617265215918.subitem_1600292170262', '出版タイプResource', 'Version Type Resource', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186783814', 'Identifier', 'Identifier', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186783814[].subitem_identifier_uri', '識別子', 'Identifier', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186783814[].subitem_identifier_type', '識別子タイプ', 'Identifier Type', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186819068', 'Identifier Registration', 'Identifier Registration', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186819068.subitem_identifier_reg_text', 'ID登録', 'Identifier Registration', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186819068.subitem_identifier_reg_type', 'ID登録タイプ', 'Identifier Registration Type', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617353299429', 'Relation', 'Relation', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617353299429[].subitem_1522306207484', '関連タイプ', 'Relation Type', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617353299429[].subitem_1522306287251', '関連識別子', 'Relation Identifier', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617353299429[].subitem_1522306287251.subitem_1522306382014', '識別子タイプ', 'Identifier Type', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617353299429[].subitem_1522306287251.subitem_1522306436033', '関連識別子', 'Relation Identifier', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617353299429[].subitem_1523320863692', '関連名称', 'Related Title', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617353299429[].subitem_1523320863692[].subitem_1523320867455', '言語', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617353299429[].subitem_1523320863692[].subitem_1523320909613', '関連名称', 'Related Title', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186859717', 'Temporal', 'Temporal', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186859717[].subitem_1522658018441', '言語', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186859717[].subitem_1522658031721', '時間的範囲', 'Temporal', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186882738', 'Geo Location', 'Geo Location', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186882738[].subitem_geolocation_point', '位置情報（点）', 'Geo Location Point', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186882738[].subitem_geolocation_point.subitem_point_longitude', '経度', 'Point Longitude', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186882738[].subitem_geolocation_point.subitem_point_latitude', '緯度', 'Point Latitude', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186882738[].subitem_geolocation_box', '位置情報（空間）', 'Geo Location Box', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186882738[].subitem_geolocation_box.subitem_west_longitude', '西部経度', 'West Bound Longitude', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186882738[].subitem_geolocation_box.subitem_east_longitude', '東部経度', 'East Bound Longitude', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186882738[].subitem_geolocation_box.subitem_south_latitude', '南部緯度', 'South Bound Latitude', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186882738[].subitem_geolocation_box.subitem_north_latitude', '北部緯度', 'North Bound Latitude', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186882738[].subitem_geolocation_place', '位置情報（自由記述）', 'Geo Location Place', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186882738[].subitem_geolocation_place[].subitem_geolocation_place_text', '位置情報（自由記述）', 'Geo Location Place', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186901218', 'Funding Reference', 'Funding Reference', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186901218[].subitem_1522399143519', '助成機関識別子', 'Funder Identifier', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186901218[].subitem_1522399143519.subitem_1522399281603', '助成機関識別子タイプ', 'Funder Identifier Type', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186901218[].subitem_1522399143519.subitem_1522399333375', '助成機関識別子', 'Funder Identifier', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186901218[].subitem_1522399412622', '助成機関名', 'Funder Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186901218[].subitem_1522399412622[].subitem_1522399416691', '言語', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186901218[].subitem_1522399412622[].subitem_1522737543681', '助成機関名', 'Funder Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186901218[].subitem_1522399571623', '研究課題番号', 'Award Number', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186901218[].subitem_1522399571623.subitem_1522399585738', '研究課題URI', 'Award URI', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186901218[].subitem_1522399571623.subitem_1522399628911', '研究課題番号', 'Award Number', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186901218[].subitem_1522399651758', '研究課題名', 'Award Title', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186901218[].subitem_1522399651758[].subitem_1522721910626', '言語', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186901218[].subitem_1522399651758[].subitem_1522721929892', '研究課題名', 'Award Title', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186920753', 'Source Identifier', 'Source Identifier', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186920753[].subitem_1522646500366', '収録物識別子タイプ', 'Source Identifier Type', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186920753[].subitem_1522646572813', '収録物識別子', 'Source Identifier', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186941041', 'Source Title', 'Source Title', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186941041[].subitem_1522650068558', '言語', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186941041[].subitem_1522650091861', '収録物名', 'Source Title', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186959569', 'Volume Number', 'Volume Number', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186959569.subitem_1551256328147', 'Volume Number', 'Volume Number', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186981471', 'Issue Number', 'Issue Number', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186981471.subitem_1551256294723', 'Issue Number', 'Issue Number', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186994930', 'Number of Pages', 'Number of Pages', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617186994930.subitem_1551256248092', 'Number of Pages', 'Number of Pages', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187024783', 'Page Start', 'Page Start', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187024783.subitem_1551256198917', 'Page Start', 'Page Start', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187045071', 'Page End', 'Page End', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187045071.subitem_1551256185532', 'Page End', 'Page End', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187056579', 'Bibliographic Information', 'Bibliographic Information', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187056579.bibliographic_titles', '雑誌名', 'Journal Title', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187056579.bibliographic_titles[].bibliographic_title', 'タイトル', 'Title', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187056579.bibliographic_titles[].bibliographic_titleLang', '言語', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187056579.bibliographicVolumeNumber', '巻', 'Volume Number', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187056579.bibliographicIssueNumber', '号', 'Issue Number', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187056579.bibliographicPageStart', '開始ページ', 'Page Start', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187056579.bibliographicPageEnd', '終了ページ', 'Page End', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187056579.bibliographicNumberOfPages', 'ページ数', 'Number of Page', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187056579.bibliographicIssueDates', '発行日', 'Issue Date', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187056579.bibliographicIssueDates.bibliographicIssueDate', '日付', 'Date', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187056579.bibliographicIssueDates.bibliographicIssueDateType', '日付タイプ', 'Date Type', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187087799', 'Dissertation Number', 'Dissertation Number', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187087799.subitem_1551256171004', 'Dissertation Number', 'Dissertation Number', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187112279', 'Degree Name', 'Degree Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187112279[].subitem_1551256126428', 'Degree Name', 'Degree Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187112279[].subitem_1551256129013', 'Language', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187136212', 'Date Granted', 'Date Granted', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187136212.subitem_1551256096004', 'Date Granted', 'Date Granted', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617944105607', 'Degree Grantor', 'Degree Grantor', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617944105607[].subitem_1551256015892', 'Degree Grantor Name Identifier', 'Degree Grantor Name Identifier', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617944105607[].subitem_1551256015892[].subitem_1551256027296', 'Degree Grantor Name Identifier', 'Degree Grantor Name Identifier', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617944105607[].subitem_1551256015892[].subitem_1551256029891', 'Degree Grantor Name Identifier Scheme', 'Degree Grantor Name Identifier Scheme', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617944105607[].subitem_1551256037922', 'Degree Grantor Name', 'Degree Grantor Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617944105607[].subitem_1551256037922[].subitem_1551256042287', 'Degree Grantor Name', 'Degree Grantor Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617944105607[].subitem_1551256037922[].subitem_1551256047619', 'Language', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187187528', 'Conference', 'Conference', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187187528[].subitem_1599711633003', 'Conference Name', 'Conference Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187187528[].subitem_1599711633003[].subitem_1599711636923', 'Conference Name', 'Conference Name', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187187528[].subitem_1599711633003[].subitem_1599711645590', 'Language', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187187528[].subitem_1599711655652', 'Conference Sequence', 'Conference Sequence', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187187528[].subitem_1599711660052', 'Conference Sponsor', 'Conference Sponsor', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187187528[].subitem_1599711660052[].subitem_1599711680082', 'Conference Sponsor', 'Conference Sponsor', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187187528[].subitem_1599711660052[].subitem_1599711686511', 'Language', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187187528[].subitem_1599711699392', 'Conference Date', 'Conference Date', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187187528[].subitem_1599711699392.subitem_1599711731891', 'Start Year', 'Start Year', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187187528[].subitem_1599711699392.subitem_1599711727603', 'Start Month', 'Start Month', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187187528[].subitem_1599711699392.subitem_1599711712451', 'Start Day', 'Start Day', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187187528[].subitem_1599711699392.subitem_1599711743722', 'End Year', 'End Year', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187187528[].subitem_1599711699392.subitem_1599711739022', 'End Month', 'End Month', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187187528[].subitem_1599711699392.subitem_1599711704251', 'Conference Date', 'Conference Date', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187187528[].subitem_1599711699392.subitem_1599711735410', 'End Day', 'End Day', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187187528[].subitem_1599711699392.subitem_1599711745532', 'Language', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187187528[].subitem_1599711758470', 'Conference Venue', 'Conference Venue', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187187528[].subitem_1599711758470[].subitem_1599711769260', 'Conference Venue', 'Conference Venue', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187187528[].subitem_1599711758470[].subitem_1599711775943', 'Language', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187187528[].subitem_1599711788485', 'Conference Place', 'Conference Place', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187187528[].subitem_1599711788485[].subitem_1599711798761', 'Conference Place', 'Conference Place', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187187528[].subitem_1599711788485[].subitem_1599711803382', 'Language', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617187187528[].subitem_1599711813532', 'Conference Country', 'Conference Country', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617605131499', 'File', 'File', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617605131499[].filename', '表示名', 'FileName', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617605131499[].url', '本文URL', 'Text URL', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617605131499[].url.url', '本文URL', 'Text URL', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617605131499[].url.label', 'ラベル', 'Label', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617605131499[].url.objectType', 'オブジェクトタイプ', 'Object Type', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617605131499[].format', 'フォーマット', 'Format', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617605131499[].filesize', 'サイズ', 'Size', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617605131499[].filesize[].value', 'サイズ', 'Size', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617605131499[].fileDate', '日付', 'Date', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617605131499[].fileDate[].fileDateType', '日付タイプ', 'Date Type', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617605131499[].fileDate[].fileDateValue', '日付', 'Date', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617605131499[].version', 'バージョン情報', 'Version Information', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617605131499[].displaytype', '表示形式', 'Preview', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617605131499[].licensetype', 'ライセンス', 'License', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617605131499[].licensefree', '', '自由ライセンス', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617605131499[].accessrole', 'アクセス', 'Access', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617605131499[].date[0].dateValue', '公開日', 'Opendate', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617605131499[].groups', 'グループ', 'Group', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617620223087', 'Heading', 'Heading', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617620223087[].subitem_1565671149650', 'Language', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617620223087[].subitem_1565671169640', 'Banner Headline', 'Banner Headline', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1617620223087[].subitem_1565671178623', 'Subheading', 'Subheading', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1662046377046', 'サムネイル', 'thumbnail', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1662046377046.subitem_thumbnail', 'URI', 'URI', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1662046377046.subitem_thumbnail[].thumbnail_url', 'URI', 'URI', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1662046377046.subitem_thumbnail[].thumbnail_label', 'ラベル', 'Label', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1662130103088', '見出し', '', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1662130103088.subitem_heading_banner_headline', '大見出し', 'Heading', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1662130103088.subitem_heading_headline', '小見出し', 'Subheading', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['item_1662130103088.subitem_heading_language', '言語', 'Language', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['system_identifier_doi', 'Persistent Identifier(DOI)', 'Persistent Identifier(DOI)', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['parentkey.subitem_systemidt_identifier', 'SYSTEMIDT Identifier', 'SYSTEMIDT Identifier', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['parentkey.subitem_systemidt_identifier_type', 'SYSTEMIDT Identifier Type', 'SYSTEMIDT Identifier Type', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['system_identifier_hdl', 'Persistent Identifier(HDL)', 'Persistent Identifier(HDL)', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['parentkey.subitem_systemidt_identifier', 'SYSTEMIDT Identifier', 'SYSTEMIDT Identifier', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['parentkey.subitem_systemidt_identifier_type', 'SYSTEMIDT Identifier Type', 'SYSTEMIDT Identifier Type', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['system_identifier_uri', 'Persistent Identifier(URI)', 'Persistent Identifier(URI)', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['parentkey.subitem_systemidt_identifier', 'SYSTEMIDT Identifier', 'SYSTEMIDT Identifier', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['parentkey.subitem_systemidt_identifier_type', 'SYSTEMIDT Identifier Type', 'SYSTEMIDT Identifier Type', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['system_file', 'File Information', 'File Information', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['parentkey.subitem_systemfile_filename', 'SYSTEMFILE Filename', 'SYSTEMFILE Filename', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['parentkey.subitem_systemfile_filename[].subitem_systemfile_filename_label', 'SYSTEMFILE Filename Label', 'SYSTEMFILE Filename Label', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['parentkey.subitem_systemfile_filename[].subitem_systemfile_filename_type', 'SYSTEMFILE Filename Type', 'SYSTEMFILE Filename Type', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['parentkey.subitem_systemfile_filename[].subitem_systemfile_filename_uri', 'SYSTEMFILE Filename URI', 'SYSTEMFILE Filename URI', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['parentkey.subitem_systemfile_mimetype', 'SYSTEMFILE MimeType', 'SYSTEMFILE MimeType', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['parentkey.subitem_systemfile_size', 'SYSTEMFILE Size', 'SYSTEMFILE Size', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['parentkey.subitem_systemfile_datetime', 'SYSTEMFILE DateTime', 'SYSTEMFILE DateTime', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['parentkey.subitem_systemfile_datetime[].subitem_systemfile_datetime_date', 'SYSTEMFILE DateTime Date', 'SYSTEMFILE DateTime Date', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['parentkey.subitem_systemfile_datetime[].subitem_systemfile_datetime_type', 'SYSTEMFILE DateTime Type', 'SYSTEMFILE DateTime Type', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, ''], ['parentkey.subitem_systemfile_version', 'SYSTEMFILE Version', 'SYSTEMFILE Version', {'required': False, 'show_list': False, 'specify_newline': False, 'hide': False, 'non_display': False}, '']]
    return meta, props

@pytest.fixture()
def prepare_creator():
    creator ={'givenNames': [{'givenName': '太郎', 'givenNameLang': 'ja'}, {'givenName': 'タロウ', 'givenNameLang': 'ja-Kana'}, {'givenName': 'Taro', 'givenNameLang': 'en'}], 'familyNames': [{'familyName': '情報', 'familyNameLang': 'ja'}, {'familyName': 'ジョウホウ', 'familyNameLang': 'ja-Kana'}, {'familyName': 'Joho', 'familyNameLang': 'en'}], 'creatorNames': [{'creatorName': '情報, 太郎', 'creatorNameLang': 'ja'}, {'creatorName': 'ジョウホウ, タロウ', 'creatorNameLang': 'ja-Kana'}, {'creatorName': 'Joho, Taro', 'creatorNameLang': 'en'}], 'nameIdentifiers': [{'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://orcid.org/', 'nameIdentifierScheme': 'ORCID'}, {'nameIdentifier': 'xxxxxxx', 'nameIdentifierURI': 'https://ci.nii.ac.jp/', 'nameIdentifierScheme': 'CiNii'}, {'nameIdentifier': 'zzzzzzz', 'nameIdentifierURI': 'https://kaken.nii.ac.jp/', 'nameIdentifierScheme': 'KAKEN2'}], 'creatorAffiliations': [{'affiliationNames': [{'affiliationName': '所属機関', 'affiliationNameLang': 'ja'}, {'affiliationName': 'Affilication Name', 'affiliationNameLang': 'en'}], 'affiliationNameIdentifiers': [{'affiliationNameIdentifier': 'xxxxxx', 'affiliationNameIdentifierURI': 'xxxxx', 'affiliationNameIdentifierScheme': 'ISNI'}]}], 'creatorAlternatives': [{'creatorAlternative': 'Alternative Name', 'creatorAlternativeLang': 'en'}, {'creatorAlternative': '別名', 'creatorAlternativeLang': 'ja'}]}
    return creator

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
def db_userprofile(app, db, users):
    profiles = {}
    with db.session.begin_nested(): 
        user = users[1]['obj']
        p = UserProfile()
        p.user_id = user.id
        p._username = (user.email).split("@")[0]
        p._displayname = p._username
        profiles[user.email] = p
        db.session.add(p)
    return profiles

@pytest.fixture()
def db_actions(app,db):
    action_datas=dict()
    with open('tests/data/actions.json', 'r') as f:
        action_datas = json.load(f)
    actions_db = list()
    with db.session.begin_nested():
        for data in action_datas:
            actions_db.append(Action(**data))
        db.session.add_all(actions_db)
    db.session.commit()

    actionstatus_datas = dict()
    with open('tests/data/action_status.json') as f:
        actionstatus_datas = json.load(f)
    actionstatus_db = list()
    with db.session.begin_nested():
        for data in actionstatus_datas:
            actionstatus_db.append(ActionStatus(**data))
        db.session.add_all(actionstatus_db)
    db.session.commit()
    return actions_db, actionstatus_db


@pytest.fixture()
def db_activity(app, db,users,location,db_itemtype,db_actions):
    flow_define = FlowDefine(id=1,flow_id=uuid.uuid4(),
                             flow_name='Registration Flow',
                             flow_user=1)
    with db.session.begin_nested():
        db.session.add(flow_define)
    db.session.commit()

    flow_action1 = FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=1,
                     action_version='1.0.0',
                     action_order=1,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={})
    flow_action2 = FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=3,
                     action_version='1.0.0',
                     action_order=2,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={})
    flow_action3 = FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=5,
                     action_version='1.0.0',
                     action_order=3,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={})
    with db.session.begin_nested():
        db.session.add(flow_action1)
        db.session.add(flow_action2)
        db.session.add(flow_action3)
    db.session.commit()
    no_location_workflow = WorkFlow(flows_id=uuid.uuid4(),
                        flows_name='test workflow1',
                        itemtype_id=1,
                        index_tree_id=None,
                        flow_id=1,
                        is_deleted=False,
                        open_restricted=False,
                        location_id=None,
                        is_gakuninrdm=False)
    location_workflow = WorkFlow(flows_id=uuid.uuid4(),
                        flows_name='test workflow2',
                        itemtype_id=1,
                        index_tree_id=None,
                        flow_id=1,
                        is_deleted=False,
                        open_restricted=False,
                        location_id=int(location.id),
                        is_gakuninrdm=False)
    with db.session.begin_nested():
        db.session.add(no_location_workflow)
        db.session.add(location_workflow)
    no_location_activity = Activity(activity_id='1',workflow_id=no_location_workflow.id, flow_id=flow_define.id,
                    action_id=1, activity_login_user=1,
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_ids=[], extra_info={},
                    action_order=1,
                    )
    location_activity = Activity(activity_id='2',workflow_id=location_workflow.id, flow_id=flow_define.id,
                    action_id=1, activity_login_user=1,
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_ids=[], extra_info={},
                    action_order=1,
                    )
    with db.session.begin_nested():
        db.session.add(no_location_activity)
        db.session.add(location_activity)
    
    #db.session.ex
    db.session.commit()
    
    return no_location_activity, location_activity

@pytest.fixture()
def db_user_profiles(db,users):
    all_data = UserProfile(
        user_id=users[2]["id"],
        _username="sysadmin",
        _displayname="sysadmin user",
        fullname="test taro",
        timezone=USERPROFILES_TIMEZONE_DEFAULT,
        language=USERPROFILES_LANGUAGE_DEFAULT,
        university="test university",
        department="test department",
        position = "test position",
        otherPosition="test other position",
        phoneNumber="123-4567",
        instituteName="test institute",
        institutePosition="test institute position",
        instituteName2="test institute2",
        institutePosition2="test institute position2",
        instituteName3="",
        institutePosition3="",
        instituteName4="",
        institutePosition4="",
        instituteName5="",
        institutePosition5=""
    )
    db.session.add(all_data)
    db.session.commit()
    return all_data
