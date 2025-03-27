# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# weko-sitemap is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""

from __future__ import absolute_import, print_function

import shutil
import tempfile
import os
from os.path import dirname, join
import json
import copy
import uuid

import pytest
from flask import Flask, current_app
from flask_babelex import Babel
from flask_menu import Menu
from flask_celeryext import FlaskCeleryExt

from invenio_admin import InvenioAdmin
from invenio_cache import InvenioCache

from weko_sitemap import WekoSitemap
from weko_sitemap.views import blueprint
from weko_sitemap.config import WEKO_SITEMAP_ADMIN_TEMPLATE
from weko_admin import WekoAdmin
from weko_admin.models import SessionLifetime
from weko_theme import WekoTheme
from invenio_assets import InvenioAssets
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import User, Role
from invenio_accounts.testutils import create_test_user, login_user_via_session
from invenio_access.models import ActionUsers
from invenio_access import InvenioAccess
from invenio_access.models import ActionUsers, ActionRoles
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_pidstore import InvenioPIDStore
from sqlalchemy_utils.functions import create_database, database_exists, drop_database

from invenio_pidrelations.models import PIDRelation
from invenio_pidstore.models import PersistentIdentifier, PIDStatus,RecordIdentifier
from invenio_pidstore.errors import PIDDoesNotExistError
from weko_deposit.api import WekoDeposit,WekoRecord
from weko_records.api import ItemsMetadata
from invenio_records_ui import InvenioRecordsUI 

@pytest.fixture(scope='module')
def celery_config():
    """Override pytest-invenio fixture.

    TODO: Remove this fixture if you add Celery support.
    """
    return {}


@pytest.yield_fixture()
def instance_path():
    """Temporary instance path."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.fixture()
def create_app(instance_path):
    """Application factory fixture."""
    def factory(**config):
        app = Flask('testapp', instance_path=instance_path, static_folder=os.path.join(instance_path, "static"),)
        app.config.update(**config)
        Babel(app)
        WekoSitemap(app)
        app.register_blueprint(blueprint)
        return app
    return factory

@pytest.fixture()
def base_app(instance_path):
    app_ = Flask('testapp', instance_path=instance_path, static_folder=os.path.join(instance_path, "static"),)
    app_.config.update(
        SERVER_NAME='TEST_SERVER',
        THEME_SITEURL = 'https://localhost',
        ACCOUNTS_JWT_ENABLE=True,
        SECRET_KEY='SECRET_KEY',
        SECURITY_PASSWORD_SALT="CHANGE_ME_ALSO",
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     "SQLALCHEMY_DATABASE_URI", "sqlite:///test.db"
        # ),
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                           'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        SQLALCHEMY_ECHO=False,
        TESTING=True,
        WEKO_SITEMAP_ADMIN_TEMPLATE=WEKO_SITEMAP_ADMIN_TEMPLATE,
        CELERY_ALWAYS_EAGER=True,
        CELERY_CACHE_BACKEND="memory",
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_RESULT_BACKEND="cache",
        CACHE_REDIS_URL=os.environ.get("CACHE_REDIS_URL", "redis://redis:6379/0"),
        CACHE_REDIS_DB='0',
        CACHE_REDIS_HOST="redis",
        REDIS_PORT='6379',
        ACCOUNTS_SESSION_REDIS_DB_NO = 1,
    )
    Babel(app_)
    Menu(app_)
    FlaskCeleryExt(app_)
    InvenioDB(app_)
    InvenioCache(app_)
    InvenioAdmin(app_)
    InvenioAssets(app_)
    InvenioAccounts(app_)
    InvenioAccess(app_)
    InvenioPIDStore(app_)
    InvenioRecordsUI(app_)
    WekoTheme(app_)
    WekoSitemap(app_)
    WekoAdmin(app_)
    app_.register_blueprint(blueprint)
    return app_

@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app

@pytest.yield_fixture()
def db(app):
    """Get setup database."""
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()

@pytest.yield_fixture()
def client(app):
    """Get test client."""
    with app.test_client() as client:
        yield client

@pytest.fixture()
def user(app, db):
    """Create a example user."""
    return create_test_user(email='test@test.org')


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
        noroleuser = create_test_user(email='noroleuser@test.org')
    else:
        user = User.query.filter_by(email='user@test.org').first()
        contributor = User.query.filter_by(email='contributor@test.org').first()
        comadmin = User.query.filter_by(email='comadmin@test.org').first()
        repoadmin = User.query.filter_by(email='repoadmin@test.org').first()
        sysadmin = User.query.filter_by(email='sysadmin@test.org').first()
        generaluser = User.query.filter_by(email='generaluser@test.org')
        originalroleuser = create_test_user(email='originalroleuser@test.org')
        originalroleuser2 = create_test_user(email='originalroleuser2@test.org')
        noroleuser = create_test_user(email='noroleuser@test.org')
        
    role_count = Role.query.filter_by(name='System Administrator').count()
    if role_count != 1:
        sysadmin_role = ds.create_role(name='System Administrator')
        repoadmin_role = ds.create_role(name='Repository Administrator')
        contributor_role = ds.create_role(name='Contributor')
        comadmin_role = ds.create_role(name='Community Administrator')
        general_role = ds.create_role(name='General')
        originalrole = ds.create_role(name='Original Role')
    else:
        sysadmin_role = Role.query.filter_by(name='System Administrator').first()
        repoadmin_role = Role.query.filter_by(name='Repository Administrator').first()
        contributor_role = Role.query.filter_by(name='Contributor').first()
        comadmin_role = Role.query.filter_by(name='Community Administrator').first()
        general_role = Role.query.filter_by(name='General').first()
        originalrole = Role.query.filter_by(name='Original Role').first()

    ds.add_role_to_user(sysadmin, sysadmin_role)
    ds.add_role_to_user(repoadmin, repoadmin_role)
    ds.add_role_to_user(contributor, contributor_role)
    ds.add_role_to_user(comadmin, comadmin_role)
    ds.add_role_to_user(generaluser, general_role)
    ds.add_role_to_user(originalroleuser, originalrole)
    ds.add_role_to_user(originalroleuser2, originalrole)
    ds.add_role_to_user(user, sysadmin_role)
    ds.add_role_to_user(user, repoadmin_role)
    ds.add_role_to_user(user, contributor_role)
    ds.add_role_to_user(user, comadmin_role)
    
    # Assign access authorization
    with db.session.begin_nested():
        action_users = [
            ActionUsers(action='superuser-access', user=sysadmin)
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

    return [
        {'email': noroleuser.email, 'id': noroleuser.id, 'obj': noroleuser},
        {'email': contributor.email, 'id': contributor.id, 'obj': contributor},
        {'email': repoadmin.email, 'id': repoadmin.id, 'obj': repoadmin},
        {'email': sysadmin.email, 'id': sysadmin.id, 'obj': sysadmin},
        {'email': comadmin.email, 'id': comadmin.id, 'obj': comadmin},
        {'email': generaluser.email, 'id': generaluser.id, 'obj': sysadmin},
        {'email': originalroleuser.email, 'id': originalroleuser.id, 'obj': originalroleuser},
        {'email': originalroleuser2.email, 'id': originalroleuser2.id, 'obj': originalroleuser2},
        {'email': user.email, 'id': user.id, 'obj': user},
    ]

@pytest.fixture()
def db_sessionlifetime(app, db):
    session_lifetime = SessionLifetime(lifetime=60, is_delete=False)
    with db.session.begin_nested():
        db.session.add(session_lifetime)

@pytest.fixture()
def records(app, db):
    current_app.config.update(
        SEARCH_UI_SEARCH_INDEX="test-weko",
        INDEXER_DEFAULT_DOCTYPE="item-v1.0.0",
        INDEXER_FILE_DOC_TYPE="content",
    )
    
    item_datas = list()
    with open(join(dirname(__file__),"data/test_items.json"), "r") as f:
        item_datas = json.load(f)
    record_datas = list()
    with open(join(dirname(__file__),"data/test_records.json"), "r") as f:
        record_datas = json.load(f)
        
    result = list()
    record_num = len(record_datas)
    for i in range(record_num):
        record_data = copy.deepcopy(record_datas[i])
        item_data = copy.deepcopy(item_datas[i])
        rec_uuid = uuid.uuid4()
        recid = PersistentIdentifier.create('recid', record_data["recid"],object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
        depid = PersistentIdentifier.create('depid', record_data["recid"],object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
        rel = PIDRelation.create(recid,depid,3)
        db.session.add(rel)
        parent=None
        doi = None
        if "item_1617186819068" in record_data:
            doi_url = "https://doi.org/"+record_data["item_1617186819068"]["attribute_value_mlt"][0]["subitem_identifier_reg_text"]
            try:
                PersistentIdentifier.get("doi",doi_url)
            except PIDDoesNotExistError:
                doi = PersistentIdentifier.create('doi',doi_url,object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
        if '.' in record_data["recid"]:
            parent = PersistentIdentifier.get("recid",int(float(record_data["recid"])))
            recid_p = PIDRelation.get_child_relations(parent).one_or_none()
            PIDRelation.create(recid_p.parent, recid,2)
        else:
            parent = PersistentIdentifier.create('parent', "parent:{}".format(record_data["recid"]),object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
            rel = PIDRelation.create(parent, recid,2,0)
            db.session.add(rel)
            RecordIdentifier.next()
        record = WekoRecord.create(record_data, id_=rec_uuid)
        item = ItemsMetadata.create(item_data, id_=rec_uuid)
        deposit = WekoDeposit(record, record.model)
        deposit.commit()
        
        result.append([recid, depid, record, item, parent, doi, deposit])
    return result