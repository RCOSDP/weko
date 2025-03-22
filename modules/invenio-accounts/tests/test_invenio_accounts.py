# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from __future__ import absolute_import, print_function

import os

from mock import patch
import pytest
import requests
from flask import Flask
from flask_babelex import Babel
from flask_mail import Mail
from flask_security import url_for_security
from invenio_db import InvenioDB, db

from invenio_accounts import InvenioAccounts, InvenioAccountsREST, testutils
from invenio_accounts.models import Role, User


def test_version():
    """Test version import."""
    from invenio_accounts import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
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
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI', 'sqlite:///'+os.path.join(instance_path,'test.db')),
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI', 'sqlite:///:memory:'),
        SERVER_NAME='example.com',
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        ACCOUNTS_JWT_ALOGORITHM = 'HS256',
        ACCOUNTS_JWT_SECRET_KEY = None
    )

    Babel(app)
    Mail(app)
    InvenioDB(app)
    ext = InvenioAccounts(app)
    assert 'invenio-accounts' in app.extensions
    assert 'security' in app.blueprints.keys()

    app = Flask('testapp')
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
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI', 'sqlite:///'+os.path.join(instance_path,'test.db')),
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI', 'sqlite:///:memory:'),
        SERVER_NAME='example.com',
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        ACCOUNTS_JWT_ALOGORITHM = 'HS256',
        ACCOUNTS_JWT_SECRET_KEY = None
    )

    Babel(app)
    Mail(app)
    InvenioDB(app)
    ext = InvenioAccounts()
    assert 'invenio-accounts' not in app.extensions
    assert 'security' not in app.blueprints.keys()
    ext.init_app(app)
    assert 'invenio-accounts' in app.extensions
    assert 'security' in app.blueprints.keys()


def test_init_rest():
    """Test REST extension initialization."""
    app = Flask('testapp')
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
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI', 'sqlite:///'+os.path.join(instance_path,'test.db')),
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI', 'sqlite:///:memory:'),
        SERVER_NAME='example.com',
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        ACCOUNTS_JWT_ALOGORITHM = 'HS256',
        ACCOUNTS_JWT_SECRET_KEY = None
    )

    Babel(app)
    Mail(app)
    InvenioDB(app)
    ext = InvenioAccountsREST(app)
    assert 'invenio-accounts' in app.extensions
    assert 'security' not in app.blueprints.keys()

    app = Flask('testapp')
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
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI', 'sqlite:///'+os.path.join(instance_path,'test.db')),
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI', 'sqlite:///:memory:'),
        SERVER_NAME='example.com',
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        ACCOUNTS_JWT_ALOGORITHM = 'HS256',
        ACCOUNTS_JWT_SECRET_KEY = None
    )
    Babel(app)
    Mail(app)
    InvenioDB(app)
    ext = InvenioAccountsREST()
    assert 'invenio-accounts' not in app.extensions
    assert 'security' not in app.blueprints.keys()
    ext.init_app(app)
    assert 'invenio-accounts' in app.extensions
    assert 'security' not in app.blueprints.keys()

    app = Flask('testapp')
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
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI', 'sqlite:///'+os.path.join(instance_path,'test.db')),
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI', 'sqlite:///:memory:'),
        SERVER_NAME='example.com',
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        ACCOUNTS_JWT_ALOGORITHM = 'HS256',
        ACCOUNTS_JWT_SECRET_KEY = None
    )
    app.config['ACCOUNTS_REGISTER_BLUEPRINT'] = True
    Babel(app)
    Mail(app)
    InvenioDB(app)
    ext = InvenioAccountsREST()
    assert 'invenio-accounts' not in app.extensions
    assert 'security' not in app.blueprints.keys()
    ext.init_app(app)
    assert 'invenio-accounts' in app.extensions
    assert 'security' in app.blueprints.keys()


# def test_alembic(app):
#     """Test alembic recipes."""
#     ext = app.extensions['invenio-db']

#     if db.engine.name == 'sqlite':
#         raise pytest.skip('Upgrades are not supported on SQLite.')

#     assert not ext.alembic.compare_metadata()
#     db.drop_all()
#     ext.alembic.upgrade()

#     assert not ext.alembic.compare_metadata()
#     ext.alembic.downgrade(target='e12419831262')
#     ext.alembic.upgrade()

#     assert not ext.alembic.compare_metadata()


def test_datastore_usercreate(app):
    """Test create user."""
    ds = app.extensions['invenio-accounts'].datastore

    with app.app_context():
        u1 = ds.create_user(email='info@inveniosoftware.org', password='1234',
                            active=True)
        ds.commit()
        u2 = ds.find_user(email='info@inveniosoftware.org')
        assert u1 == u2
        assert 1 == \
            User.query.filter_by(email='info@inveniosoftware.org').count()


def test_datastore_rolecreate(app):
    """Test create user."""
    ds = app.extensions['invenio-accounts'].datastore

    with app.app_context():
        r1 = ds.create_role(name='superuser', description='1234')
        ds.commit()
        r2 = ds.find_role('superuser')
        assert r1 == r2
        assert 1 == \
            Role.query.filter_by(name='superuser').count()


def test_datastore_assignrole(app):
    """Create and assign user to role."""
    ds = app.extensions['invenio-accounts'].datastore

    with app.app_context():
        u = ds.create_user(email='info@inveniosoftware.org', password='1234',
                           active=True)
        r = ds.create_role(name='superuser', description='1234')
        ds.add_role_to_user(u, r)
        ds.commit()
        u = ds.get_user('info@inveniosoftware.org')
        assert len(u.roles) == 1
        assert u.roles[0].name == 'superuser'


def test_view(app):
    """Test view."""
    with app.app_context():
        login_url = url_for_security('login')

    with app.test_client() as client:
        res = client.get(login_url)
        assert res.status_code == 200


def test_configuration(base_app):
    """Test configuration."""
    app = base_app
    app.config['ACCOUNTS_USE_CELERY'] = 'deadbeef'
    InvenioAccounts(app)
    assert 'deadbeef' == app.config['ACCOUNTS_USE_CELERY']


# .tox/c1/bin/pytest --cov=invenio_accounts tests/test_invenio_accounts.py::test_cookies -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-accounts/.tox/c1/tmp
def test_cookies(cookie_app, users):
    """Test cookies set on login."""
    u = users[0]

    with cookie_app.app_context():
        with cookie_app.test_client() as client:
            res = client.post(
                url_for_security('login'),
                data=dict(email=u['email'], password=u['password'], remember=True),
            )
            assert res.status_code == 302
            cookies = {c.name: c for c in client.cookie_jar}
            assert 'session' in cookies
            assert 'remember_token' not in cookies

            # Cookie must be HTTP only, secure and have a domain specified.
            for c in cookies.values():
                assert c.path == '/'
                assert c.domain_specified is True, 'no domain in {}'.format(c.name)
                assert c.has_nonstandard_attr('HttpOnly')
                assert c.secure is True


def test_kvsession_store_init(app):
    """Test KV session configuration was loaded correctly."""
    if os.environ.get('CI', 'false') == 'true':
        from simplekv.memory.redisstore import \
            RedisStore as kvsession_store_class
    else:
        from simplekv.memory import DictStore as kvsession_store_class

    assert isinstance(app.kvsession_store, kvsession_store_class)


# .tox/c1/bin/pytest --cov=invenio_accounts tests/test_invenio_accounts.py::test_headers_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-accounts/.tox/c1/tmp
def test_headers_info(app, users):
    """Test if session and user id is set response header."""
    u = users[0]
    with app.app_context():
        with app.test_client() as client:
            url = url_for_security('change_password')
            response = client.get(url)
            # Not logged in, so only session id available
            assert not testutils.client_authenticated(client)
            assert 'X-Session-ID' in response.headers
            assert 'X-User-ID' not in response.headers
            # Login
            testutils.login_user_via_session(client, email=u['email'])
            response = client.get(url)
            cookie = requests.utils.dict_from_cookiejar(client.cookie_jar)
            assert response.headers['X-Session-ID'] == \
                cookie['session'].split('.')[0]
            assert int(response.headers['X-User-ID']) == u['id']
