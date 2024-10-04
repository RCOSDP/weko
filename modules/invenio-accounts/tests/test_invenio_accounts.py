# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2023 CERN.
# Copyright (C) 2021      TU Wien.
# Copyright (C) 2024 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

import pytest
import os
import requests
from flask import Flask
from flask_mail import Mail
from flask_menu import current_menu
from flask_security import url_for_security
from invenio_db import InvenioDB, db
from invenio_i18n import Babel

from invenio_accounts import InvenioAccounts, InvenioAccountsREST, testutils
from invenio_accounts.models import Role, User
from invenio_accounts.views.settings import create_settings_blueprint


def test_version():
    """Test version import."""
    from invenio_accounts import __version__

    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask("testapp")
    app.config.update(
        # SECRET_KEY="CHANGEME",
        ACCOUNTS_USE_CELERY=False,
        task_always_eager=True,
        CELERY_CACHE_BACKEND="memory",
        task_eager_propagates=True,
        CELERY_RESULT_BACKEND="cache",
        LOGIN_DISABLED=False,
        MAIL_SUPPRESS_SEND=True,
        SECRET_KEY="CHANGE_ME",
        # SECURITY_PASSWORD_SALT="CHANGE_ME_ALSO",
        SECURITY_PASSWORD_SINGLE_HASH=False,
        SECURITY_CONFIRM_EMAIL_WITHIN="2 seconds",
        SECURITY_RESET_PASSWORD_WITHIN="2 seconds",
        DB_VERSIONING=False,
        DB_VERSIONING_USER_MODEL=None,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                  'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
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
    assert "invenio-accounts" in app.extensions
    assert "security" in app.blueprints.keys()

    app = Flask("testapp")
    app.config.update(
        # SECRET_KEY="CHANGEME",
        ACCOUNTS_USE_CELERY=False,
        task_always_eager=True,
        CELERY_CACHE_BACKEND="memory",
        task_eager_propagates=True,
        CELERY_RESULT_BACKEND="cache",
        LOGIN_DISABLED=False,
        MAIL_SUPPRESS_SEND=True,
        SECRET_KEY="CHANGE_ME",
        # SECURITY_PASSWORD_SALT="CHANGE_ME_ALSO",
        SECURITY_PASSWORD_SINGLE_HASH=False,
        SECURITY_CONFIRM_EMAIL_WITHIN="2 seconds",
        SECURITY_RESET_PASSWORD_WITHIN="2 seconds",
        DB_VERSIONING=False,
        DB_VERSIONING_USER_MODEL=None,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                  'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
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
    assert "invenio-accounts" not in app.extensions
    assert "security" not in app.blueprints.keys()
    ext.init_app(app)
    assert "invenio-accounts" in app.extensions
    assert "security" in app.blueprints.keys()


def test_init_rest():
    """Test REST extension initialization."""
    app = Flask("testapp")
    app.config.update(
        # SECRET_KEY="CHANGEME"",
        ACCOUNTS_USE_CELERY=False,
        task_always_eager=True,
        CELERY_CACHE_BACKEND="memory",
        task_eager_propagates=True,
        CELERY_RESULT_BACKEND="cache",
        LOGIN_DISABLED=False,
        MAIL_SUPPRESS_SEND=True,
        SECRET_KEY="CHANGE_ME",
        # SECURITY_PASSWORD_SALT="CHANGE_ME_ALSO",
        SECURITY_PASSWORD_SINGLE_HASH=False,
        SECURITY_CONFIRM_EMAIL_WITHIN="2 seconds",
        SECURITY_RESET_PASSWORD_WITHIN="2 seconds",
        DB_VERSIONING=False,
        DB_VERSIONING_USER_MODEL=None,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                  'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
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
    assert "invenio-accounts" in app.extensions
    assert "security" not in app.blueprints.keys()
    assert "security_email_templates" in app.blueprints.keys()

    app = Flask("testapp")
    app.config.update(
        # SECRET_KEY="CHANGEME"",
        ACCOUNTS_USE_CELERY=False,
        task_always_eager=True,
        CELERY_CACHE_BACKEND="memory",
        task_eager_propagates=True,
        CELERY_RESULT_BACKEND="cache",
        LOGIN_DISABLED=False,
        MAIL_SUPPRESS_SEND=True,
        SECRET_KEY="CHANGE_ME",
        # SECURITY_PASSWORD_SALT="CHANGE_ME_ALSO",
        SECURITY_PASSWORD_SINGLE_HASH=False,
        SECURITY_CONFIRM_EMAIL_WITHIN="2 seconds",
        SECURITY_RESET_PASSWORD_WITHIN="2 seconds",
        DB_VERSIONING=False,
        DB_VERSIONING_USER_MODEL=None,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                  'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
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
    assert "invenio-accounts" not in app.extensions
    assert "security" not in app.blueprints.keys()
    ext.init_app(app)
    assert "invenio-accounts" in app.extensions
    assert "security" not in app.blueprints.keys()
    assert "security_email_templates" in app.blueprints.keys()

    app = Flask("testapp")
    app.config.update(
        # SECRET_KEY="CHANGEME"",
        ACCOUNTS_USE_CELERY=False,
        task_always_eager=True,
        CELERY_CACHE_BACKEND="memory",
        task_eager_propagates=True,
        CELERY_RESULT_BACKEND="cache",
        LOGIN_DISABLED=False,
        MAIL_SUPPRESS_SEND=True,
        SECRET_KEY="CHANGE_ME",
        # SECURITY_PASSWORD_SALT="CHANGE_ME_ALSO",
        SECURITY_PASSWORD_SINGLE_HASH=False,
        SECURITY_CONFIRM_EMAIL_WITHIN="2 seconds",
        SECURITY_RESET_PASSWORD_WITHIN="2 seconds",
        DB_VERSIONING=False,
        DB_VERSIONING_USER_MODEL=None,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                  'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        SERVER_NAME='example.com',
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        ACCOUNTS_JWT_ALOGORITHM = 'HS256',
        ACCOUNTS_JWT_SECRET_KEY = None,
        ACCOUNTS_REGISTER_BLUEPRINT=True
    )
    Babel(app)
    Mail(app)
    InvenioDB(app)
    ext = InvenioAccountsREST()
    assert "invenio-accounts" not in app.extensions
    assert "security" not in app.blueprints.keys()
    ext.init_app(app)
    assert "invenio-accounts" in app.extensions
    assert "security" in app.blueprints.keys()
    assert "security_email_templates" in app.blueprints.keys()

    app = Flask("testapp")
    app.config.update(
        # SECRET_KEY="CHANGEME"",
        ACCOUNTS_USE_CELERY=False,
        task_always_eager=True,
        CELERY_CACHE_BACKEND="memory",
        task_eager_propagates=True,
        CELERY_RESULT_BACKEND="cache",
        LOGIN_DISABLED=False,
        MAIL_SUPPRESS_SEND=True,
        SECRET_KEY="CHANGE_ME",
        # SECURITY_PASSWORD_SALT="CHANGE_ME_ALSO",
        SECURITY_PASSWORD_SINGLE_HASH=False,
        SECURITY_CONFIRM_EMAIL_WITHIN="2 seconds",
        SECURITY_RESET_PASSWORD_WITHIN="2 seconds",
        DB_VERSIONING=False,
        DB_VERSIONING_USER_MODEL=None,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                  'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        SERVER_NAME='example.com',
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        ACCOUNTS_JWT_ALOGORITHM = 'HS256',
        ACCOUNTS_JWT_SECRET_KEY = None,
        ACCOUNTS_REGISTER_BLUEPRINT=False
    )
    Babel(app)
    Mail(app)
    InvenioDB(app)
    ext = InvenioAccountsREST()
    assert "invenio-accounts" not in app.extensions
    assert "security" not in app.blueprints.keys()
    ext.init_app(app)
    assert "invenio-accounts" in app.extensions
    assert "security" not in app.blueprints.keys()
    assert "security_email_templates" in app.blueprints.keys()


def test_accounts_settings_blueprint(base_app):
    """Test settings blueprint when ACCOUNTS_REGISTER_BLUEPRINT is False."""
    app = base_app
    app.config["ACCOUNTS_REGISTER_BLUEPRINT"] = False
    InvenioAccounts(app)
    # register settings blueprint
    # app.register_blueprint(blueprint)
    create_settings_blueprint(app)
    with app.app_context():
        with app.test_client() as client:
            client.get("/account/settings")
            menu = current_menu.submenu("settings.change_password", auto_create=False)
            assert not menu


@pytest.mark.skip(reason="Mergepoint is on invenio-access.")
def test_alembic(app):
    """Test alembic recipes."""
    ext = app.extensions["invenio-db"]

    if db.engine.name == "sqlite":
        raise pytest.skip("Upgrades are not supported on SQLite.")

    assert not ext.alembic.compare_metadata()
    db.drop_all()
    ext.alembic.upgrade()

    assert not ext.alembic.compare_metadata()
    ext.alembic.downgrade(target="e12419831262")
    ext.alembic.upgrade()

    assert not ext.alembic.compare_metadata()


def test_datastore_usercreate(app):
    """Test create user."""
    ds = app.extensions["invenio-accounts"].datastore

    u1 = ds.create_user(email="info@inveniosoftware.org", password="1234", active=True)
    ds.commit()
    u2 = ds.find_user(email="info@inveniosoftware.org")
    assert u1 == u2
    assert 1 == User.query.filter_by(email="info@inveniosoftware.org").count()


def test_datastore_rolecreate(app):
    """Test create role."""
    ds = app.extensions["invenio-accounts"].datastore

    r1 = ds.create_role(name="superuser", description="1234")
    ds.commit()
    r2 = ds.find_role("superuser")
    assert r1 == r2
    assert 1 == Role.query.filter_by(name="superuser").count()


def test_datastore_update_role(app):
    """Test update role."""
    ds = app.extensions["invenio-accounts"].datastore

    r1 = ds.create_role(id="1", name="superuser", description="1234")
    ds.commit()
    r2 = ds.find_role("superuser")
    assert r1 == r2
    assert 1 == Role.query.filter_by(name="superuser").count()
    assert r2.is_managed is True

    r1 = ds.update_role(
        Role(
            id="1", name="megauser", description="updated description", is_managed=False
        )
    )
    ds.commit()
    r2 = ds.find_role("megauser")
    assert r1 == r2
    assert r2.description == "updated description"
    assert r2.is_managed is False
    assert 1 == Role.query.filter_by(name="megauser").count()
    assert 0 == Role.query.filter_by(name="superuser").count()


def test_datastore_assignrole(app):
    """Create and assign user to role."""
    ds = app.extensions["invenio-accounts"].datastore

    u = ds.create_user(email="info@inveniosoftware.org", password="1234", active=True)
    r = ds.create_role(name="superuser", description="1234")
    ds.add_role_to_user(u, r)
    ds.commit()
    u = ds.get_user("info@inveniosoftware.org")
    assert len(u.roles) == 1
    assert u.roles[0].name == "superuser"


def test_view(app):
    """Test view."""
    login_url = url_for_security("login")

    with app.test_client() as client:
        res = client.get(login_url)
        assert res.status_code == 200


def test_configuration(base_app):
    """Test configuration."""
    app = base_app
    app.config["ACCOUNTS_USE_CELERY"] = "deadbeef"
    InvenioAccounts(app)
    assert "deadbeef" == app.config["ACCOUNTS_USE_CELERY"]


def test_cookies(cookie_app, users):
    """Test cookies set on login."""
    u = users[0]

    with cookie_app.test_client() as client:
        res = client.post(
            url_for_security("login"),
            data=dict(email=u["email"], password=u["password"], remember=True),
        )
        assert res.status_code == 302
        cookies = {c.name: c for c in client.cookie_jar}
        assert "session" in cookies
        assert "remember_token" not in cookies

        # Cookie must be HTTP only, secure and have a domain specified.
        for c in cookies.values():
            assert c.path == "/"
            assert c.domain_specified is True, "no domain in {}".format(c.name)
            assert c.has_nonstandard_attr("HttpOnly")
            assert c.secure is True


def test_kvsession_store_init_with_default_factory(app):
    from simplekv.memory import DictStore as kvsession_store_class

    assert isinstance(app.kvsession_store, kvsession_store_class)


def test_kvsession_store_init_with_redis_url(app_with_redis_url):
    from simplekv.memory.redisstore import RedisStore as kvsession_store_class

    assert isinstance(app_with_redis_url.kvsession_store, kvsession_store_class)


def test_headers_info(app, users):
    """Test if session and user id is set response header."""
    u = users[0]
    url = url_for_security("change_password")
    with app.test_client() as client:
        response = client.get(url)
        # Not logged in, so only session id available
        assert not testutils.client_authenticated(client)
        assert "X-Session-ID" in response.headers
        assert "X-User-ID" not in response.headers
        # Login
        testutils.login_user_via_session(client, email=u["email"])
        response = client.get(url)
        cookie = requests.utils.dict_from_cookiejar(client.cookie_jar)
        assert response.headers["X-Session-ID"] == cookie["session"].split(".")[0]
        assert int(response.headers["X-User-ID"]) == u["id"]
