# -*- coding: utf-8 -*-
"""Pytest for weko-logging configuration."""

from datetime import datetime
import logging
import shutil
import tempfile

import pytest
import os
import shutil
import tempfile
import pytest

from flask import Flask
from flask_babelex import Babel
from flask_menu import Menu
from sqlalchemy_utils.functions import create_database, database_exists

from invenio_access import InvenioAccess
from invenio_access.models import ActionUsers, ActionRoles
from invenio_accounts.ext import InvenioAccounts
from invenio_accounts.models import User, Role
from invenio_accounts.testutils import create_test_user
from invenio_admin import InvenioAdmin
from invenio_assets import InvenioAssets
from invenio_cache import InvenioCache
from invenio_communities.models import Community
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_files_rest.ext import InvenioFilesREST
from invenio_files_rest.models import Location
from invenio_i18n import InvenioI18N

from weko_admin import WekoAdmin
from weko_redis.redis import RedisConnection
from weko_theme import WekoTheme
from weko_index_tree.models import Index

from weko_logging.audit import WekoLoggingUserActivity
from weko_logging.views import blueprint as logging_blueprint

@pytest.fixture()
def instance_path():
    """Temporary instance path."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)

@pytest.fixture()
def base_app(instance_path):
    """Flask application fixture."""
    app_ = Flask('test_weko_logging_app', instance_path=instance_path)
    app_.config.update(
        SERVER_NAME='test_server',
        ACCOUNTS_USE_CELERY=False,
        SECRET_KEY='SECRET_KEY',
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI','postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),

        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        SQLALCHEMY_ECHO=False,
        TEST_USER_EMAIL='test_user@example.com',
        TEST_USER_PASSWORD='test_password',
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        GOOGLE_TRACKING_ID_USER="test_google_tracking_id",
        ADDTHIS_USER_ID="test_addthis_user_id",
        I18N_LANGUAGES=[("ja","Japanese"), ("en","English")],
        THEME_SITEURL = 'https://localhost',
        WEKO_THEME_INSTANCE_DATA_DIR="data",
        WEKO_LOGGING_FS_PYWARNINGS=None,
        CACHE_REDIS_URL=os.environ.get("CACHE_REDIS_URL", "redis://redis:6379/0"),
        CACHE_REDIS_DB='0',
        CACHE_REDIS_HOST="redis",
        REDIS_PORT='6379',
        ACCOUNTS_SESSION_REDIS_DB_NO = 1,
        CACHE_TYPE="redis",
        WEKO_LOGGING_USER_ACTIVITY_DB_SETTING = {
            "log_level": "INFO",
            "delete": {
                "when": "months",
                "interval": 3
            }
        },
        WEKO_LOGGING_USER_ACTIVITY_STREAM_SETTING = {
            "log_level": "INFO"
        }
    )
    app_.testing = True
    app_.login_manager = dict(_login_disabled=True)
    Babel(app_)
    Menu(app_)
    InvenioAccess(app_)
    InvenioAccounts(app_)
    InvenioAdmin(app_)
    InvenioAssets(app_)
    InvenioCache(app_)
    InvenioDB(app_)
    InvenioFilesREST(app_)
    InvenioI18N(app_)
    WekoAdmin(app_)
    WekoTheme(app_)
    WekoLoggingUserActivity(app_)
    app_.register_blueprint(logging_blueprint)
    yield app_



@pytest.fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app

@pytest.fixture()
def db(app):
    # if not database_exists(str(db_.engine.url)) and \
    #         app.config['SQLALCHEMY_DATABASE_URI'] != 'sqlite://':
    #     create_database(db_.engine.url)
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()


@pytest.fixture()
def client(app):
    """Get test client."""
    with app.test_client() as client:
        yield client

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


@pytest.fixture(scope="function", autouse=True)
def tmppath():
    """Make a temporary directory."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


@pytest.fixture(scope="function", autouse=True)
def pywarnlogger():
    """Rest the py.warnings logger."""
    logger = logging.getLogger("py.warnings")
    yield logger
    logger.handlers = []

@pytest.fixture
def redis_connect(app):
    redis_connection = RedisConnection().connection(db=app.config['CACHE_REDIS_DB'], kv = True)
    return redis_connection

@pytest.fixture()
def location(app, db):
    """Create default location."""
    tmppath = tempfile.mkdtemp()
    with db.session.begin_nested():
        Location.query.delete()
        loc = Location(name='local', uri=tmppath, default=True)
        db.session.add(loc)
    db.session.commit()
    return location


@pytest.fixture()
def mock_async_result_factory():
    """Mock async result factory."""
    class MockAsyncResult():
        def __init__(self, task_id, _state, result):
            self.task_id = task_id
            self.task_state = _state
            self.result = result
        @property
        def state(self):
            return self.task_state
        @property
        def status(self):
            return self.task_state
        def successful(self):
            return self.task_state == "SUCCESS"
        def failed(self):
            return self.task_state == "FAILURE"

    def factory(task_id, state, result):
        return MockAsyncResult(task_id, state, result)

    return factory


@pytest.fixture()
def indices(app, db):
    """Create indices."""

    index = Index(
        id=1234567890,
        index_name="index_name",
        index_name_english="index_name_english",
        display_no=1,
        harvest_public_state=True,
        image_name="image_name",
        public_state=True,
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
