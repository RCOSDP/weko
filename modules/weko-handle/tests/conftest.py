# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# WEKO-Handle is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""

from __future__ import absolute_import, print_function

import json
from os.path import dirname, exists, join
import shutil
import tempfile
import os

import pytest
from flask import Flask
from flask_babelex import Babel
from sqlalchemy_utils.functions import create_database, database_exists
from invenio_db import InvenioDB
from invenio_db import db as db_

from weko_handle import WekoHandle
from weko_handle.views import blueprint


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
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     "SQLALCHEMY_DATABASE_URI", "sqlite:///test.db"
        # ),
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                           'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
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
        WEKO_INDEX_TREE_STYLE_OPTIONS={
            "id": "weko",
            "widths": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"],
        },
        WEKO_INDEX_TREE_UPATED=True,
        I18N_LANGUAGES=[("ja", "Japanese"), ("en", "English")],
        SERVER_NAME="TEST_SERVER",
        SEARCH_ELASTIC_HOSTS=os.environ.get("SEARCH_ELASTIC_HOSTS", "elasticsearch"),
        SEARCH_INDEX_PREFIX="test-",
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
        ]
    )
    # with ESTestServer(timeout=30) as server:
    Babel(app_)
    InvenioDB(app_)
    WekoHandle(app_)

    return app_


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app


@pytest.yield_fixture()
def client(app):
    """Get test client."""
    with app.test_client() as client:
        yield client


@pytest.yield_fixture()
def db(app):
    """Database fixture."""
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()
