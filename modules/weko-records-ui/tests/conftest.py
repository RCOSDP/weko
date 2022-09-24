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
import shutil
import tempfile
import copy
from unittest.mock import patch

import pytest
from flask import Flask
from flask_menu import Menu
from flask_babelex import Babel
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import User, Role
from invenio_accounts.testutils import create_test_user
from invenio_access import InvenioAccess
from invenio_access.models import ActionRoles, ActionUsers
from invenio_admin import InvenioAdmin
from invenio_assets import InvenioAssets
from invenio_db import InvenioDB, db as db_
from invenio_cache import InvenioCache
from invenio_deposit import InvenioDeposit
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.views import blueprint as invenio_files_rest_blueprint
from invenio_files_rest.models import Bucket, Location, ObjectVersion
from invenio_i18n import InvenioI18N
from invenio_indexer import InvenioIndexer
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_pidrelations import InvenioPIDRelations
from invenio_pidstore import InvenioPIDStore
from invenio_records import InvenioRecords
from invenio_records_rest.utils import PIDConverter
from invenio_search import InvenioSearch
from invenio_search_ui import InvenioSearchUI
from invenio_stats.config import SEARCH_INDEX_PREFIX as index_prefix
from six import BytesIO
from simplekv.memory.redisstore import RedisStore
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database
from weko_admin import WekoAdmin
from weko_items_ui import WekoItemsUI
from weko_records import WekoRecords
# from weko_records_ui import WekoRecordsUI
from weko_search_ui import WekoSearchUI
from weko_search_ui.config import WEKO_SEARCH_MAX_RESULT
from weko_theme import WekoTheme
from weko_groups import WekoGroups

from weko_deposit import WekoDeposit, WekoDepositREST
from weko_deposit.api import WekoRecord
from weko_deposit.views import blueprint
from weko_deposit.api import WekoDeposit as aWekoDeposit
from weko_deposit.config import WEKO_BUCKET_QUOTA_SIZE, \
    WEKO_DEPOSIT_REST_ENDPOINTS, _PID, DEPOSIT_REST_ENDPOINTS

from flask_login import LoginManager, UserMixin


@pytest.yield_fixture()
def instance_path():
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)




@pytest.fixture()
def base_app(instance_path):
    """Flask application fixture."""
    app_ = Flask('testapp', instance_path=instance_path)
    app_.url_map.converters['pid'] = PIDConverter
    # initialize InvenioDeposit first in order to detect any invalid dependency
    WEKO_DEPOSIT_REST_ENDPOINTS = copy.deepcopy(DEPOSIT_REST_ENDPOINTS)
    WEKO_DEPOSIT_REST_ENDPOINTS['depid']['rdc_route'] = '/deposits/redirect/<{0}:pid_value>'.format(_PID)
    WEKO_DEPOSIT_REST_ENDPOINTS['depid']['pub_route'] = '/deposits/publish/<{0}:pid_value>'.format(_PID)

    app_.config.update(
        CELERY_ALWAYS_EAGER=True,
        CELERY_CACHE_BACKEND='memory',
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_RESULT_BACKEND='cache',
        CACHE_REDIS_URL='redis://redis:6379/0',
        CACHE_REDIS_DB=0,
        CACHE_REDIS_HOST="redis",
        REDIS_PORT='6379',
        JSONSCHEMAS_URL_SCHEME='http',
        SECRET_KEY='CHANGE_ME',
        SECURITY_PASSWORD_SALT='CHANGE_ME_ALSO',
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI',
        #     'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/invenio'),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        SEARCH_ELASTIC_HOSTS=os.environ.get(
            'SEARCH_ELASTIC_HOSTS', None),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        SQLALCHEMY_ECHO=False,
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        DEPOSIT_SEARCH_API='/api/search',
        SECURITY_PASSWORD_HASH='plaintext',
        SECURITY_PASSWORD_SCHEMES=['plaintext'],
        SECURITY_DEPRECATED_PASSWORD_SCHEMES=[],
        OAUTHLIB_INSECURE_TRANSPORT=True,
        OAUTH2_CACHE_TYPE='simple',
        ACCOUNTS_JWT_ENABLE=False,
        INDEXER_DEFAULT_INDEX='{}-weko-item-v1.0.0'.format(
            index_prefix),
        INDEXER_DEFAULT_DOCTYPE='item-v1.0.0',
        INDEXER_DEFAULT_DOC_TYPE='item-v1.0.0',
        INDEXER_FILE_DOC_TYPE='content',
        WEKO_BUCKET_QUOTA_SIZE=WEKO_BUCKET_QUOTA_SIZE,
        WEKO_MAX_FILE_SIZE=WEKO_BUCKET_QUOTA_SIZE,
        INDEX_IMG='indextree/36466818-image.jpg',
        WEKO_SEARCH_MAX_RESULT=WEKO_SEARCH_MAX_RESULT,
        WEKO_DEPOSIT_REST_ENDPOINTS=WEKO_DEPOSIT_REST_ENDPOINTS,
        WEKO_INDEX_TREE_STYLE_OPTIONS={
            'id': 'weko',
            'widths': ['1', '2', '3', '4', '5', '6', '7', '8',
                       '9', '10', '11']
        },
        WEKO_INDEX_TREE_UPATED=True,
        I18N_LANGUAGE=[("ja", "Japanese"), ("en", "English")],
        SERVER_NAME = 'TEST_SERVER',
        WEKO_PERMISSION_ROLE_USER = ['System Administrator',
                             'Repository Administrator',
                             'Contributor',
                             'General',
                             'Community Administrator'],

WEKO_PERMISSION_SUPER_ROLE_USER = ['System Administrator',
                                   'Repository Administrator'],
    # WEKO_ITEMS_UI_DATA_REGISTRATION = '',
    # WEKO_ITEMS_UI_APPLICATION_ITEM_TYPES_LIST=['デフォルトアイテムタイプ（フル）'],
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
    WekoRecords(app_)
    WekoItemsUI(app_)
    # WekoRecordsUI(app_)
    WekoAdmin(app_)
    WekoSearchUI(app_)
    WekoTheme(app_)
    WekoGroups(app_)
    Menu(app_)
    # app_.register_blueprint(blueprint)
    app_.register_blueprint(invenio_files_rest_blueprint) # invenio_files_rest
    # rest_blueprint = create_blueprint(app_, WEKO_DEPOSIT_REST_ENDPOINTS)
    # app_.register_blueprint(rest_blueprint)
    WekoDeposit(app_)
    WekoDepositREST(app_)
    return app_


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app


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






