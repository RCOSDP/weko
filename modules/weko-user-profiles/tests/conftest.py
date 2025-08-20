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
from flask import Flask, current_app
from flask_admin import Admin
from flask_babelex import Babel
from flask_mail import Mail
from flask_menu import Menu
from sqlalchemy_utils.functions import create_database, database_exists

from invenio_access import InvenioAccess
from invenio_access.models import ActionUsers,ActionRoles
from invenio_accounts import InvenioAccounts
from invenio_accounts.views import blueprint as accounts_blueprint
from invenio_accounts.models import User, Role
from invenio_accounts.testutils import create_test_user
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_communities.models import Community

from weko_index_tree.models import Index
from weko_notifications import WekoNotifications

from weko_user_profiles import WekoUserProfiles
from weko_user_profiles.views import blueprint_ui_init,blueprint_api_init
from weko_user_profiles.views import blueprint as blueprint_profile
from weko_user_profiles.models import UserProfile
from weko_user_profiles.config import USERPROFILES_LANGUAGE_DEFAULT, \
    USERPROFILES_TIMEZONE_DEFAULT
from weko_user_profiles.admin import user_profile_adminview


@pytest.yield_fixture()
def instance_path():
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.yield_fixture()
def base_app(instance_path):
    """Flask application fixture."""
    app_ = Flask(__name__, instance_path=instance_path)

    app_.config.update(
        ACCOUNTS_USE_CELERY=False,
        LOGIN_DISABLED=False,
        SECRET_KEY='testing_key',
        SERVER_NAME='TEST_SERVER.localdomain',
        THEME_SITEURL="https://localhost",
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                           'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        TEST_USER_EMAIL='test_user@example.com',
        TEST_USER_PASSWORD='test_password',
        WEKO_ADMIN_PROFILE_SETTING_TEMPLATE = 'weko_admin/admin/profiles_settings.html',
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )
    Babel(app_)
    Mail(app_)
    Menu(app_)
    InvenioDB(app_)
    InvenioAccess(app_)
    InvenioAccounts(app_)
    WekoUserProfiles(app_)
    WekoNotifications(app_)

    app_.register_blueprint(accounts_blueprint)

    yield app_

@pytest.yield_fixture()
def app(base_app):
    """Flask application."""
    with base_app.app_context():
        yield base_app

@pytest.fixture()
def admin_app(app,db):
    admin = Admin(app,name="Test")
    model = user_profile_adminview.get("model")
    view = user_profile_adminview.get("modelview")
    data = {"category":user_profile_adminview.get("category")}
    admin.add_view(view(model,db.session,**data))


@pytest.yield_fixture()
def client(app):
    with app.test_client() as client:
        yield client

@pytest.yield_fixture()
def req_context(app):
    with app.test_request_context():
        yield app

@pytest.fixture()
def register_bp():
    current_app.register_blueprint(blueprint_ui_init)
    current_app.register_blueprint(blueprint_api_init)
    current_app.register_blueprint(blueprint_profile)

@pytest.yield_fixture
def db(app):
    """Database fixture."""
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()
    # drop_database(str(db_.engine.url))


@pytest.fixture
def app_with_csrf(base_app):
    """Flask application with CSRF security enabled."""
    base_app.config.update(
        WTF_CSRF_ENABLED=True,
    )
    return _init_userprofiles_app(base_app)


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
    index = Index()
    db.session.add(index)
    db.session.commit()
    comm = Community.create(community_id="comm01", role_id=sysadmin_role.id,
                            id_user=sysadmin.id, title="test community",
                            description=("this is test community"),
                            root_node_id=index.id)
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

@pytest.fixture()
def user_profiles(db,users):
    all_data = UserProfile(
        user_id=users[0]["id"],
        _username="sysadmin",
        _displayname="sysadmin user",
        fullname="test taro",
        timezone=USERPROFILES_TIMEZONE_DEFAULT,
        language=USERPROFILES_LANGUAGE_DEFAULT,
        university="test university",
        department="test department",
        position = "test position",
        item1="test other position",
        item2="123-4567",
        item3="test institute",
        item4="test institute position",
        item5="test institute2",
        item6="test institute position2",
        item7="",
        item8="",
        item9="",
        item10="",
        item11="",
        item12="",
        item13="",
        item14="",
        item15="",
        item16=""
    )
    db.session.add(all_data)
    repo_profile = UserProfile(
        user_id=users[1]["id"],
        _username="repoadmin",
        _displayname="repoadmin user",
        fullname="test taro",
        timezone=USERPROFILES_TIMEZONE_DEFAULT,
        language=USERPROFILES_LANGUAGE_DEFAULT,
        university="test university",
        department="test department",
        position = "test position",
        item1="test other position",
        item2="123-4567",
        item3="test institute",
        item4="test institute position",
        item5="test institute2",
        item6="test institute position2",
        item7="",
        item8="",
        item9="",
        item10="",
        item11="",
        item12="",
        item13="",
        item14="",
        item15="",
        item16=""
    )
    db.session.add(repo_profile)
    not_validate_language = UserProfile(
        user_id=users[2]["id"],
        _username="comadmin",
        _displayname="comadmin user",
        fullname="test taro",
        timezone=USERPROFILES_TIMEZONE_DEFAULT,
        language="not exist language",
        university="test university",
        department="test department",
        position = "test position",
        item1="test other position",
        item2="123-4567",
        item3="test institute",
        item4="test institute position",
        item5="test institute2",
        item6="test institute position2",
        item7="",
        item8="",
        item9="",
        item10="",
        item11="",
        item12="",
        item13="",
        item14="",
        item15="",
        item16=""
    )
    db.session.commit()
    return [
        all_data,
        repo_profile,
        not_validate_language,
    ]

@pytest.fixture()
def setup_data(db):
    # Create a user
    user = User(
        email="sysadmin@test.org",
        active=True
    )
    db.session.add(user)
    db.session.commit()

    # Create a user profile
    profile_get_info = UserProfile(
        user_id=user.id,
        _username="sysadmin",
        _displayname="sysadmin user",
        fullname="test taro",
        timezone="Etc/GMT",
        language="ja",
        university="test university",
        department="test department",
        position="test position",
        item1="test other position",
        item2="123-4567",
        item3="test institute",
        item4="test institute position",
        item5="test institute2",
        item6="test institute position2",
        item7="test institute3",
        item8="test institute position3",
        item9="test institute4",
        item10="test institute position4",
        item11="test institute5",
        item12="test institute position5",
        item13="item 13",
        item14="item 14",
        item15="item 15",
        item16="item 16"
    )
    db.session.add(profile_get_info)
    db.session.commit()
    return[profile_get_info]