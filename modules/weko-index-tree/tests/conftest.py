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

import pytest
from flask import Flask
from flask_babelex import Babel
from flask_celeryext import FlaskCeleryExt
from flask_menu import Menu
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import User
from invenio_accounts.testutils import create_test_user
from invenio_assets import InvenioAssets
from invenio_cache import InvenioCache
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_files_rest.models import Location
from invenio_i18n import InvenioI18N
from invenio_indexer import InvenioIndexer
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_mail import InvenioMail
from invenio_oaiserver import InvenioOAIServer
from invenio_pidrelations import InvenioPIDRelations
from invenio_records import InvenioRecords
from invenio_search import InvenioSearch
from mock import Mock, patch
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database

from weko_index_tree import WekoIndexTree
from weko_index_tree.admin import index_link_adminview


@pytest.yield_fixture()
def instance_path():
    """Temporary instance path."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.fixture()
def base_app(instance_path):
    """Flask application fixture."""
    app_ = Flask('testapp', instance_path=instance_path)
    app_.config.update(
        CELERY_ALWAYS_EAGER=True,
        CELERY_CACHE_BACKEND='memory',
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_RESULT_BACKEND='cache',
        JSONSCHEMAS_URL_SCHEME='http',
        SECRET_KEY='CHANGE_ME',
        SECURITY_PASSWORD_SALT='CHANGE_ME_ALSO',
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        SEARCH_ELASTIC_HOSTS=os.environ.get(
            'SEARCH_ELASTIC_HOSTS', 'elasticsearch'),
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
        INDEX_IMG='indextree/36466818-image.jpg',
        SEARCH_UI_SEARCH_INDEX='tenant1',
        INDEXER_DEFAULT_DOCTYPE='item-v1.0.0',
        INDEXER_FILE_DOC_TYPE='content',
    )
    FlaskCeleryExt(app_)
    Menu(app_)
    Babel(app_)
    InvenioDB(app_)
    InvenioAccounts(app_)
    InvenioAssets(app_)
    InvenioCache(app_)
    InvenioJSONSchemas(app_)
    InvenioSearch(app_)
    InvenioRecords(app_)
    InvenioIndexer(app_)
    InvenioI18N(app_)
    InvenioPIDRelations(app_)
    InvenioOAIServer(app_)
    InvenioMail(app_)
    WekoIndexTree(app_)

    return app_


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app


@pytest.fixture()
def db(app):
    """Database fixture."""
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()


@pytest.fixture()
def mock_users():
    """Create mock users."""
    mock_auth_user = Mock()
    mock_auth_user.get_id = lambda: '123'
    mock_auth_user.is_authenticated = True

    mock_anon_user = Mock()
    mock_anon_user.is_authenticated = False
    return {
        'anonymous': mock_anon_user,
        'authenticated': mock_auth_user
    }


@pytest.fixture()
def user():
    """Create a example user."""
    return create_test_user(email='test@test.org')


@pytest.fixture()
def location(app):
    """Create default location."""
    tmppath = tempfile.mkdtemp()
    with db_.session.begin_nested():
        Location.query.delete()
        loc = Location(name='local', uri=tmppath, default=True)
        db_.session.add(loc)
    db_.session.commit()
    return location
