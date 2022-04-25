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
import json

import pytest
from flask import Flask, url_for
from flask_babelex import Babel
from invenio_db import InvenioDB, db as db_
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import User, Role
from invenio_accounts.testutils import create_test_user, login_user_via_session
from invenio_access import InvenioAccess
from invenio_access.models import ActionUsers
from invenio_indexer import InvenioIndexer
from invenio_search import InvenioSearch
from invenio_stats.config import SEARCH_INDEX_PREFIX as index_prefix
from simplekv.memory.redisstore import RedisStore
from sqlalchemy import inspect
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database

from weko_authors.views import blueprint_api
from weko_authors import WekoAuthors
from weko_authors.models import Authors, AuthorsPrefixSettings
from weko_search_ui import WekoSearchUI


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
        SECRET_KEY='SECRET_KEY',
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=os.environ.get(
           'SQLALCHEMY_DATABASE_URI',
           'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/invenio'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        INDEX_IMG='indextree/36466818-image.jpg',
        SEARCH_UI_SEARCH_INDEX='tenant1-weko',
        WEKO_AUTHORS_AFFILIATION_IDENTIFIER_ITEM_OTHER=4,
        WEKO_AUTHORS_LIST_SCHEME_AFFILIATION=[
            'ISNI', 'GRID', 'Ringgold', 'kakenhi', 'Other'],
    )
    Babel(app_)
    InvenioDB(app_)
    InvenioAccounts(app_)
    InvenioAccess(app_)
    InvenioIndexer(app_)
    InvenioSearch(app_)
    WekoAuthors(app_)
    WekoSearchUI(app_)

    # app_.register_blueprint(blueprint)
    app_.register_blueprint(blueprint_api, url_prefix='/api/authors')
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
    # drop_database(str(db_.engine.url))


@pytest.yield_fixture()
def client(app):
    """Get test client."""
    with app.test_client() as client:
        yield client


@pytest.fixture()
def users(app, db):
    """Create users."""
    ds = app.extensions['invenio-accounts'].datastore
    user_count = User.query.filter_by(email='test@test.org').count()
    if user_count != 1:
        user = create_test_user(email='test@test.org')
        contributor = create_test_user(email='test2@test.org')
        comadmin = create_test_user(email='test3@test.org')
        repoadmin = create_test_user(email='test4@test.org')
        sysadmin = create_test_user(email='test5@test.org')

    else:
        user = User.query.filter_by(email='test@test.org').first()
        contributor = User.query.filter_by(email='test2@test.org').first()
        comadmin = User.query.filter_by(email='test3@test.org').first()
        repoadmin = User.query.filter_by(email='test4@test.org').first()
        sysadmin = User.query.filter_by(email='test5@test.org').first()

    role_count = Role.query.filter_by(name='System Administrator').count()
    if role_count != 1:
        r1 = ds.create_role(name='System Administrator')
        r2 = ds.create_role(name='Repository Administrator')
        r3 = ds.create_role(name='Contributor')
        r4 = ds.create_role(name='Community Administrator')

    else:
        r1 = Role.query.filter_by(name='System Administrator').first()
        r2 = Role.query.filter_by(name='Repository Administrator').first()
        r3 = Role.query.filter_by(name='Contributor').first()
        r4 = Role.query.filter_by(name='Community Administrator').first()

    ds.add_role_to_user(sysadmin, r1)
    ds.add_role_to_user(repoadmin, r2)
    ds.add_role_to_user(contributor, r3)
    ds.add_role_to_user(comadmin, r4)

    # Assign access authorization
    with db.session.begin_nested():
        action_users = [
            ActionUsers(action='superuser-access', user=sysadmin),
            ActionUsers(action='author-access', user=contributor),
            ActionUsers(action='author-access', user=comadmin),
            ActionUsers(action='author-access', user=repoadmin)
        ]
        db.session.add_all(action_users)

    return [
        {'email': user.email, 'id': user.id,
         'obj': user},
        {'email': contributor.email, 'id': contributor.id,
         'obj': contributor},
        {'email': comadmin.email, 'id': comadmin.id,
         'obj': comadmin},
        {'email': repoadmin.email, 'id': repoadmin.id,
         'obj': repoadmin},
        {'email': sysadmin.email, 'id': sysadmin.id,
         'obj': sysadmin},
    ]


@pytest.fixture()
def id_prefix(client, users):
    """Create test prefix."""
    # login for create prefix
    login_user_via_session(client=client, email=users[4]['email'])
    input = {'name': 'testprefix', 'scheme': 'testprefix',
             'url': 'https://testprefix/##'}
    client.put('/api/authors/add_prefix',
               data=json.dumps(input),
               content_type='application/json')
    client.get(url_for('security.logout'))
    authors_prefix = AuthorsPrefixSettings.query.filter_by(
                        name='testprefix').first()
    return authors_prefix.id


@pytest.fixture()
def create_author(db):
    def _create_author(data):
        with db.session.begin_nested():
            new_id = Authors.get_sequence(db.session)
            data["id"] = str(new_id)
            data["pk_id"] = str(new_id)
            author = Authors(id=new_id, json=data)
            db.session.add(author)
        return new_id

    # Return new author's id
    return _create_author
def user():
    """Create a example user."""
    return create_test_user(email='test@test.org')


def object_as_dict(obj):
    """Make a dict from SQLAlchemy object."""
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}
