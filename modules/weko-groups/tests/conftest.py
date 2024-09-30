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


"""Pytest for weko-groups configuration."""

import os
import shutil
import tempfile
import pytest
from mock import MagicMock, patch
from flask import Flask, json, jsonify, session, url_for
from flask_babel import Babel
from flask_breadcrumbs import Breadcrumbs
from flask_menu import Menu
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database

from invenio_admin import InvenioAdmin
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import User
from invenio_db import InvenioDB, db
from invenio_accounts.testutils import create_test_user
from invenio_accounts.models import User, Role
from invenio_access.models import ActionUsers
from invenio_access import InvenioAccess
from invenio_admin import InvenioAdmin
from invenio_i18n import InvenioI18N

from weko_groups import WekoGroups
from weko_groups.api import Group


@pytest.fixture
def app(request):
    """
    Flask application fixture.

    :param request: Request.
    :return: App object.
    """
    instance_path = tempfile.mkdtemp()
    app = Flask('weko_groups_app', instance_path=instance_path)
    app.config.update(
        LOGIN_DISABLED=False,
        MAIL_SUPPRESS_SEND=True,
        SECRET_KEY='1qertgyujk345678ijk',
        # SQLALCHEMY_DATABASE_URI=os.environ.get('SQLALCHEMY_DATABASE_URI',
        #                                        'sqlite:///test.db'),
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                           'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )
    Babel(app)
    Menu(app)
    InvenioAdmin(app)
    Breadcrumbs(app)
    InvenioDB(app)
    InvenioAccounts(app)
    WekoGroups(app)
    InvenioI18N(app)

    with app.app_context():
        if str(db.engine.url) != 'sqlite://' and \
           not database_exists(str(db.engine.url)):
            create_database(str(db.engine.url))
        db.create_all()

    def teardown():
        with app.app_context():
            if str(db.engine.url) != 'sqlite://':
                drop_database(str(db.engine.url))
        shutil.rmtree(instance_path)

    request.addfinalizer(teardown)
    return app


@pytest.fixture
def example_group(app):
    """
    Create example groups.

    :param app: An instance of :class:`~flask.Flask`.
    :return: App object.
    """
    with app.app_context():
        admin = User(email='test@example.com', password='test_password')
        member = User(email='test2@example.com', password='test_password')
        non_member = User(email='test3@example.com', password='test_password')
        db.session.add(admin)
        db.session.add(member)
        db.session.add(non_member)
        group = Group.create(name='test_group', admins=[admin])
        membership = group.invite(member)
        membership.accept()

        admin_id = admin.id
        member_id = member.id
        non_member_id = non_member.id
        group_id = group.id
        db.session.commit()

    app.get_admin = lambda: User.query.get(admin_id)
    app.get_member = lambda: User.query.get(member_id)
    app.get_non_member = lambda: User.query.get(non_member_id)
    app.get_group = lambda: Group.query.get(group_id)

    return app


@pytest.yield_fixture()
def instance_path():
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.fixture()
def base_app(instance_path):
    app_ = Flask("testapp", instance_path=instance_path)
    app_.config.update(
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        TESTING=True,
        SERVER_NAME="TEST_SERVER",
        SEARCH_INDEX_PREFIX='test-',
        INDEXER_DEFAULT_DOC_TYPE='testrecord',
        SEARCH_UI_SEARCH_INDEX='tenant1-weko',
        SECRET_KEY='SECRET_KEY',
        CACHE_REDIS_DB='0',
        CACHE_TYPE='0',
        WEKO_GRIDLAYOUT_BUCKET_UUID='61531203-4104-4425-a51b-d32881eeab22',
        FILES_REST_DEFAULT_STORAGE_CLASS="S",
        FILES_REST_STORAGE_CLASS_LIST={
            "S": "Standard",
            "A": "Archive",
        },
        FILES_REST_DEFAULT_QUOTA_SIZE=None,
        FILES_REST_DEFAULT_MAX_FILE_SIZE=None,
        FILES_REST_OBJECT_KEY_MAX_LEN=255,
    )
    Babel(app_)
    Menu(app_)
    Breadcrumbs(app_)
    InvenioDB(app_)
    InvenioAccounts(app_)
    WekoGroups(app_)
    InvenioAccess(app_)
    InvenioAdmin(app_)
    # Babel(app_)
    # InvenioDB(app_)
    # InvenioAccounts(app_)
    # InvenioAccess(app_)
    # InvenioFilesREST(app_)
    #WekoAdmin(app_)
    # app_.register_blueprint(blueprint)
    # app_.register_blueprint(blueprint_api)


    return app_


@pytest.yield_fixture()
def app_2(base_app):
    with base_app.app_context():
        yield base_app


@pytest.fixture()
def db_2(app_2):
    from invenio_db import db as db_
    """Database fixture."""
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()


@pytest.yield_fixture()
def client_request_args(app_2):
    with app_2.test_client() as client:
        with patch("flask.templating._render", return_value=""):
            r = client.get(
                "/",
                query_string={
                    "q": "q",
                    "page": 1,
                    "count": 20,
                    "lang": "en",
                    "remote_addr": "0.0.0.0",
                    "referrer": "test",
                    "host": "127.0.0.1",
                },
            )
            yield r


@pytest.fixture()
def users(app, db_2):
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
    else:
        user = User.query.filter_by(email='user@test.org').first()
        contributor = User.query.filter_by(email='contributor@test.org').first()
        comadmin = User.query.filter_by(email='comadmin@test.org').first()
        repoadmin = User.query.filter_by(email='repoadmin@test.org').first()
        sysadmin = User.query.filter_by(email='sysadmin@test.org').first()
        generaluser = User.query.filter_by(email='generaluser@test.org')
        originalroleuser = create_test_user(email='originalroleuser@test.org')
        originalroleuser2 = create_test_user(email='originalroleuser2@test.org')

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
    ds.add_role_to_user(originalroleuser2, repoadmin_role)

    # Assign access authorization
    with db_2.session.begin_nested():
        action_users = [
            ActionUsers(action='superuser-access', user=sysadmin)
        ]
        db_2.session.add_all(action_users)

    return [
        {'email': contributor.email, 'id': contributor.id, 'obj': contributor},
        {'email': repoadmin.email, 'id': repoadmin.id, 'obj': repoadmin},
        {'email': sysadmin.email, 'id': sysadmin.id, 'obj': sysadmin},
        {'email': comadmin.email, 'id': comadmin.id, 'obj': comadmin},
        {'email': generaluser.email, 'id': generaluser.id, 'obj': sysadmin},
        {'email': originalroleuser.email, 'id': originalroleuser.id, 'obj': originalroleuser},
        {'email': originalroleuser2.email, 'id': originalroleuser2.id, 'obj': originalroleuser2},
        {'email': user.email, 'id': user.id, 'obj': user},
    ]

