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

import shutil
import os
import tempfile
import os

import pytest
from flask import Flask
from flask import session, url_for
from flask_babelex import Babel

from invenio_accounts import InvenioAccounts
from invenio_accounts.testutils import create_test_user, login_user_via_session
from invenio_access import InvenioAccess
from invenio_access.models import ActionUsers
from sqlalchemy_utils.functions import create_database, database_exists
from invenio_db import InvenioDB, db as db_
from invenio_search import RecordsSearch
from invenio_stats.config import SEARCH_INDEX_PREFIX as index_prefix
from invenio_records_rest import InvenioRecordsREST
from invenio_pidstore import InvenioPIDStore
from invenio_i18n.ext import InvenioI18N, current_i18n
from invenio_records_rest import InvenioRecordsREST

from weko_search_ui import WekoSearchUI, WekoSearchREST
from weko_search_ui.config import SEARCH_UI_SEARCH_INDEX

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
        DB_VERSIONING=False,
        DB_VERSIONING_USER_MODEL=None,
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "SQLALCHEMY_DATABASE_URI", "sqlite:///test.db"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        SECRET_KEY="SECRET_KEY",
        TESTING=True,
        INDEX_IMG='indextree/36466818-image.jpg',
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        WEKO_SEARCH_REST_ENDPOINTS = dict(
            recid=dict(
                pid_type='recid',
                pid_minter='recid',
                pid_fetcher='recid',
                search_class=RecordsSearch,
                search_index=SEARCH_UI_SEARCH_INDEX,
                search_type='item-v1.0.0',
                search_factory_imp='weko_search_ui.query.weko_search_factory',
                # record_class='',
                record_serializers={
                    'application/json': ('invenio_records_rest.serializers'
                                        ':json_v1_response'),
                },
                search_serializers={
                    'application/json': ('weko_records.serializers'
                                        ':json_v1_search'),
                },
                index_route='/index/',
                links_factory_imp='weko_search_ui.links:default_links_factory',
                default_media_type='application/json',
                max_result_window=10000,
            ),
        ),
        JSON_AS_ASCII=False,
        BABEL_DEFAULT_LOCALE="en",
        BABEL_DEFAULT_LANGUAGE="en",
        BABEL_DEFAULT_TIMEZONE="Asia/Tokyo",
        I18N_LANGUAGES=[("ja", "Japanese"), ("en", "English")],
        I18N_SESSION_KEY="my_session_key",
    )
    Babel(app_)
    InvenioDB(app_)
    InvenioI18N(app_)
    InvenioAccounts(app_)
    InvenioAccess(app_)
    InvenioRecordsREST(app_)
    InvenioPIDStore(app_)
    WekoSearchUI(app_)

    return app_


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app

@pytest.yield_fixture()
def client_rest(app):
    WekoSearchREST(app)
    with app.test_client() as client:
        yield client

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
def users(app, db):
    """Create users."""
    ds = app.extensions['invenio-accounts'].datastore
    user = create_test_user(email='test@test.org')
    contributor = create_test_user(email='test2@test.org')
    comadmin = create_test_user(email='test3@test.org')
    repoadmin = create_test_user(email='test4@test.org')
    sysadmin = create_test_user(email='test5@test.org')

    r1 = ds.create_role(name='System Administrator')
    ds.add_role_to_user(sysadmin, r1)
    r2 = ds.create_role(name='Repository Administrator')
    ds.add_role_to_user(repoadmin, r2)
    r3 = ds.create_role(name='Contributor')
    ds.add_role_to_user(contributor, r3)
    r4 = ds.create_role(name='Community Administrator')
    ds.add_role_to_user(comadmin, r4)

    # Assign access authorization
    with db.session.begin_nested():
        action_users = [
            ActionUsers(action='superuser-access', user=sysadmin)
        ]
        db.session.add_all(action_users)

    return [
        {'email': user.email, 'id': user.id,
         'password': user.password_plaintext, 'obj': user},
        {'email': contributor.email, 'id': contributor.id,
         'password': contributor.password_plaintext, 'obj': contributor},
        {'email': comadmin.email, 'id': comadmin.id,
         'password': comadmin.password_plaintext, 'obj': comadmin},
        {'email': repoadmin.email, 'id': repoadmin.id,
         'password': repoadmin.password_plaintext, 'obj': repoadmin},
        {'email': sysadmin.email, 'id': sysadmin.id,
         'password': sysadmin.password_plaintext, 'obj': sysadmin},
    ]
