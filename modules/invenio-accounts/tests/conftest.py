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

from invenio_access import InvenioAccess
import pytest
from flask import Flask
from flask.cli import ScriptInfo
from flask_admin import Admin
from flask_babelex import Babel
from flask_celeryext import FlaskCeleryExt
from flask_mail import Mail
from flask_menu import Menu
from invenio_access.models import ActionRoles, ActionUsers
from invenio_accounts.models import Role
from invenio_db import InvenioDB, db
from invenio_i18n import InvenioI18N
from simplekv.memory.redisstore import RedisStore
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database

from invenio_accounts import InvenioAccounts
from invenio_accounts.admin import role_adminview, session_adminview, \
    user_adminview
from invenio_accounts.testutils import create_test_user


def _app_factory(config=None):
    """Application factory."""
    instance_path = tempfile.mkdtemp()
    app = Flask('testapp', instance_path=instance_path)
    app.config.update(
        ACCOUNTS_USE_CELERY=False,
        task_always_eager=True,
        CELERY_CACHE_BACKEND="memory",
        task_eager_propagates=True,
        CELERY_RESULT_BACKEND="cache",
        LOGIN_DISABLED=False,
        MAIL_SUPPRESS_SEND=True,
        SECRET_KEY="CHANGE_ME",
        SECURITY_PASSWORD_SALT="CHANGE_ME_ALSO",
        SECURITY_CONFIRM_EMAIL_WITHIN="2 seconds",
        SECURITY_RESET_PASSWORD_WITHIN="2 seconds",
        DB_VERSIONING=False,
        DB_VERSIONING_USER_MODEL=None,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                          'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI', 'sqlite:///'+os.path.join(instance_path,'test.db')),
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI', 'sqlite:///:memory:'),
        SERVER_NAME='example.com',
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        ACCOUNTS_JWT_ALOGORITHM = 'HS256',
        ACCOUNTS_JWT_SECRET_KEY = 'None'
    )

    # Set key value session store to use Redis when running on TravisCI.
    if os.environ.get('CI', 'false') == 'true':
        app.config.update(
            ACCOUNTS_SESSION_REDIS_URL='redis://localhost:6379/0',
        )

    app.config.update(config or {})
    Menu(app)
    Babel(app)
    Mail(app)
    InvenioDB(app)
    return app


def _database_setup(app, request):
    """Set up the database."""
    with app.app_context():
        if not database_exists(str(db.engine.url)):
            create_database(str(db.engine.url))
        db.create_all()

    def teardown():
        with app.app_context():
            if database_exists(str(db.engine.url)):
                drop_database(str(db.engine.url))
            # Delete sessions in kvsession store
            if hasattr(app, 'kvsession_store') and \
                    isinstance(app.kvsession_store, RedisStore):
                app.kvsession_store.redis.flushall()
        shutil.rmtree(app.instance_path)

    request.addfinalizer(teardown)
    return app


@pytest.yield_fixture()
def base_app(request):
    """Flask application fixture."""
    app = _app_factory()
    _database_setup(app, request)
    yield app


@pytest.yield_fixture()
def app(request):
    """Flask application fixture with Invenio Accounts."""
    app = _app_factory()
    app.config.update(ACCOUNTS_USERINFO_HEADERS=True)
    InvenioAccess(app)
    InvenioAccounts(app)

    from invenio_accounts.views.settings import blueprint
    app.register_blueprint(blueprint)

    _database_setup(app, request)
    yield app


@pytest.fixture
def script_info(app):
    """Get ScriptInfo object for testing CLI."""
    return ScriptInfo(create_app=lambda info: app)


@pytest.fixture
def task_app(request):
    """Flask application with Celery enabled."""
    app = _app_factory(dict(
        ACCOUNTS_USE_CELERY=True,
        MAIL_SUPPRESS_SEND=True,
    ))
    FlaskCeleryExt(app)
    InvenioAccounts(app)
    _database_setup(app, request)
    return app


@pytest.fixture
def cookie_app(request):
    """Flask application  enabled."""
    app = _app_factory(dict(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_DOMAIN='example.com',
    ))
    InvenioAccounts(app)
    _database_setup(app, request)
    return app


@pytest.fixture
def admin_view(app):
    """Admin view fixture."""
    assert isinstance(role_adminview, dict)
    assert isinstance(user_adminview, dict)
    assert isinstance(session_adminview, dict)

    assert 'model' in role_adminview
    assert 'modelview' in role_adminview
    assert 'model' in user_adminview
    assert 'modelview' in user_adminview
    assert 'model' in session_adminview
    assert 'modelview' in session_adminview

    admin = Admin(app, name="Test")

    user_adminview_copy = dict(user_adminview)
    user_model = user_adminview_copy.pop('model')
    user_view = user_adminview_copy.pop('modelview')
    admin.add_view(user_view(user_model, db.session, **user_adminview_copy))

    admin.add_view(session_adminview['modelview'](
        session_adminview['model'], db.session,
        category=session_adminview['category']))


@pytest.fixture()
def app_i18n(app):
    """Init invenio-i18n."""
    InvenioI18N(app)
    return app


@pytest.fixture()
def users(app):
    """Create users."""
    with app.app_context():
        user1 = create_test_user(email='info@inveniosoftware.org',
                                 password='tester')
        user1_email = user1.email
        user1_id = user1.id
        user1_pw = user1.password_plaintext
        user2 = create_test_user(email='info2@inveniosoftware.org',
                                 password='tester2')
        user2_email = user2.email
        user2_id = user2.id
        user2_pw = user2.password_plaintext
        user3 = create_test_user(email='admin1@inveniosoftware.org',
                                 password='tester3')
        user3_email = user3.email
        user3_id = user3.id
        user3_pw = user3.password_plaintext

        ds = app.extensions["invenio-accounts"].datastore
        role_count = Role.query.filter_by(name="System Administrator").count()
        if role_count != 1:
            sysadmin_role = ds.create_role(name="System Administrator")
        else:
            sysadmin_role = Role.query.filter_by(name="System Administrator").first()

        # Assign access authorization
        with db.session.begin_nested():
            action_users = [
                ActionUsers(action="superuser-access", user=user3),
            ]
            db.session.add_all(action_users)
            action_roles = [
                ActionRoles(action="superuser-access", role=sysadmin_role)
            ]
            db.session.add_all(action_roles)
            ds.add_role_to_user(user3, sysadmin_role)

    return [
        {'email': user1_email, 'id': user1_id,
         'password': user1_pw, 'obj': user1},
        {'email': user2_email, 'id': user2_id,
         'password': user2_pw, 'obj': user2},
        {'email': user3_email, 'id': user3_id,
         'password': user3_pw, 'obj': user3},
    ]
