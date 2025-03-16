# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO-Notifications is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""

from __future__ import absolute_import, print_function

import os
import shutil
import tempfile

import pytest
from flask import Flask
from flask_babelex import Babel
from flask_mail import Mail
from flask_menu import Menu
from sqlalchemy_utils.functions import create_database, database_exists
from werkzeug.local import LocalProxy


from invenio_access import InvenioAccess
from invenio_access.models import ActionUsers, ActionRoles
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import User, Role
from invenio_accounts.testutils import create_test_user
from invenio_admin import InvenioAdmin
from invenio_assets import InvenioAssets
from invenio_communities.models import Community
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_i18n import InvenioI18N
from invenio_pidrelations import InvenioPIDRelations
from invenio_pidstore import InvenioPIDStore
from invenio_records import InvenioRecords
from invenio_records_ui import InvenioRecordsUI
from invenio_search import InvenioSearch, current_search_client

from weko_index_tree import WekoIndexTree
from weko_index_tree.models import Index
from weko_deposit import WekoDeposit
from weko_deposit.api import WekoIndexer
from weko_items_ui import WekoItemsUI
from weko_records import WekoRecords
from weko_records_ui import WekoRecordsUI
from weko_schema_ui import WekoSchemaUI
from weko_theme import WekoTheme
from weko_user_profiles import WekoUserProfiles
from weko_user_profiles.models import UserProfile
from weko_user_profiles.config import USERPROFILES_LANGUAGE_DEFAULT, USERPROFILES_TIMEZONE_DEFAULT
from weko_workflow import WekoWorkflow

from weko_notifications import WekoNotifications
from weko_notifications.views import blueprint as weko_notifications_blueprint

from .helpers import json_data


@pytest.yield_fixture()
def instance_path():
    """Temporary instance path."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.fixture()
def base_app(instance_path):
    """Flask application fixture."""
    app_ = Flask(
        "testapp",
        instance_path=instance_path,
        static_folder=os.path.join(instance_path, "static")
    )
    app_.config.update(
        TESTING=True,
        SECRET_KEY="testing_key",
        SERVER_NAME="TEST_SERVER.localdomain",
        THEME_SITEURL="http://test_server.localdomain",
        SQLALCHEMY_DATABASE_URI=os.getenv(
            "SQLALCHEMY_DATABASE_URI",
            "postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest"),
        WEKO_NOTIFICATIONS=True,
    )
    Babel(app_)
    Mail(app_)
    Menu(app_)
    InvenioAccess(app_)
    InvenioAccounts(app_)
    InvenioAdmin(app_)
    InvenioAssets(app_)
    InvenioDB(app_)
    InvenioI18N(app_)
    InvenioPIDRelations(app_)
    InvenioPIDStore(app_)
    InvenioRecords(app_)
    InvenioRecordsUI(app_)
    InvenioSearch(app_)
    WekoDeposit(app_)
    WekoIndexer(app_)
    WekoIndexTree(app_)
    WekoItemsUI(app_)
    WekoRecords(app_)
    WekoRecordsUI(app_)
    WekoSchemaUI(app_)
    WekoTheme(app_)
    WekoUserProfiles(app_)
    WekoWorkflow(app_)

    current_assets = LocalProxy(lambda: app_.extensions["invenio-assets"])
    current_assets.collect.collect()

    yield app_

@pytest.fixture()
def app(base_app):
    """Flask application fixture."""
    WekoNotifications(base_app)
    base_app.register_blueprint(weko_notifications_blueprint)
    with base_app.app_context():
        yield base_app

@pytest.yield_fixture()
def client(app):
    with app.test_client() as client:
        yield client

@pytest.yield_fixture
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
    ds = app.extensions["invenio-accounts"].datastore
    user_count = User.query.filter_by(email="user@test.org").count()
    if user_count != 1:
        user = create_test_user(email="user@test.org")
        contributor = create_test_user(email="contributor@test.org")
        comadmin = create_test_user(email="comadmin@test.org")
        repoadmin = create_test_user(email="repoadmin@test.org")
        sysadmin = create_test_user(email="sysadmin@test.org")
        generaluser = create_test_user(email="generaluser@test.org")
        originalroleuser = create_test_user(email="originalroleuser@test.org")
        originalroleuser2 = create_test_user(email="originalroleuser2@test.org")
        student = create_test_user(email="student@test.org")
    else:
        user = User.query.filter_by(email="user@test.org").first()
        contributor = User.query.filter_by(email="contributor@test.org").first()
        comadmin = User.query.filter_by(email="comadmin@test.org").first()
        repoadmin = User.query.filter_by(email="repoadmin@test.org").first()
        sysadmin = User.query.filter_by(email="sysadmin@test.org").first()
        generaluser = User.query.filter_by(email="generaluser@test.org")
        originalroleuser = create_test_user(email="originalroleuser@test.org")
        originalroleuser2 = create_test_user(email="originalroleuser2@test.org")
        student = User.query.filter_by(email="student@test.org").first()

    role_count = Role.query.filter_by(name="System Administrator").count()
    if role_count != 1:
        sysadmin_role = ds.create_role(name="System Administrator")
        repoadmin_role = ds.create_role(name="Repository Administrator")
        contributor_role = ds.create_role(name="Contributor")
        comadmin_role = ds.create_role(name="Community Administrator")
        general_role = ds.create_role(name="General")
        originalrole = ds.create_role(name="Original Role")
        studentrole = ds.create_role(name="Student")
    else:
        sysadmin_role = Role.query.filter_by(name="System Administrator").first()
        repoadmin_role = Role.query.filter_by(name="Repository Administrator").first()
        contributor_role = Role.query.filter_by(name="Contributor").first()
        comadmin_role = Role.query.filter_by(name="Community Administrator").first()
        general_role = Role.query.filter_by(name="General").first()
        originalrole = Role.query.filter_by(name="Original Role").first()
        studentrole = Role.query.filter_by(name="Student").first()

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
            ActionUsers(action="superuser-access", user=sysadmin),
        ]
        db.session.add_all(action_users)
        action_roles = [
            ActionRoles(action="superuser-access", role=sysadmin_role),
            ActionRoles(action="admin-access", role=repoadmin_role),
            ActionRoles(action="schema-access", role=repoadmin_role),
            ActionRoles(action="index-tree-access", role=repoadmin_role),
            ActionRoles(action="indextree-journal-access", role=repoadmin_role),
            ActionRoles(action="item-type-access", role=repoadmin_role),
            ActionRoles(action="item-access", role=repoadmin_role),
            ActionRoles(action="files-rest-bucket-update", role=repoadmin_role),
            ActionRoles(action="files-rest-object-delete", role=repoadmin_role),
            ActionRoles(action="files-rest-object-delete-version", role=repoadmin_role),
            ActionRoles(action="files-rest-object-read", role=repoadmin_role),
            ActionRoles(action="search-access", role=repoadmin_role),
            ActionRoles(action="detail-page-acces", role=repoadmin_role),
            ActionRoles(action="download-original-pdf-access", role=repoadmin_role),
            ActionRoles(action="author-access", role=repoadmin_role),
            ActionRoles(action="items-autofill", role=repoadmin_role),
            ActionRoles(action="stats-api-access", role=repoadmin_role),
            ActionRoles(action="read-style-action", role=repoadmin_role),
            ActionRoles(action="update-style-action", role=repoadmin_role),
            ActionRoles(action="detail-page-acces", role=repoadmin_role),

            ActionRoles(action="admin-access", role=comadmin_role),
            ActionRoles(action="index-tree-access", role=comadmin_role),
            ActionRoles(action="indextree-journal-access", role=comadmin_role),
            ActionRoles(action="item-access", role=comadmin_role),
            ActionRoles(action="files-rest-bucket-update", role=comadmin_role),
            ActionRoles(action="files-rest-object-delete", role=comadmin_role),
            ActionRoles(action="files-rest-object-delete-version", role=comadmin_role),
            ActionRoles(action="files-rest-object-read", role=comadmin_role),
            ActionRoles(action="search-access", role=comadmin_role),
            ActionRoles(action="detail-page-acces", role=comadmin_role),
            ActionRoles(action="download-original-pdf-access", role=comadmin_role),
            ActionRoles(action="author-access", role=comadmin_role),
            ActionRoles(action="items-autofill", role=comadmin_role),
            ActionRoles(action="detail-page-acces", role=comadmin_role),
            ActionRoles(action="detail-page-acces", role=comadmin_role),

            ActionRoles(action="item-access", role=contributor_role),
            ActionRoles(action="files-rest-bucket-update", role=contributor_role),
            ActionRoles(action="files-rest-object-delete", role=contributor_role),
            ActionRoles(action="files-rest-object-delete-version", role=contributor_role),
            ActionRoles(action="files-rest-object-read", role=contributor_role),
            ActionRoles(action="search-access", role=contributor_role),
            ActionRoles(action="detail-page-acces", role=contributor_role),
            ActionRoles(action="download-original-pdf-access", role=contributor_role),
            ActionRoles(action="author-access", role=contributor_role),
            ActionRoles(action="items-autofill", role=contributor_role),
            ActionRoles(action="detail-page-acces", role=contributor_role),
            ActionRoles(action="detail-page-acces", role=contributor_role),
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
        {"email": sysadmin.email, "id": sysadmin.id, "obj": sysadmin},
        {"email": repoadmin.email, "id": repoadmin.id, "obj": repoadmin},
        {"email": comadmin.email, "id": comadmin.id, "obj": comadmin},
        {"email": contributor.email, "id": contributor.id, "obj": contributor},
        {"email": generaluser.email, "id": generaluser.id, "obj": generaluser},
        {"email": originalroleuser.email, "id": originalroleuser.id, "obj": originalroleuser},
        {"email": originalroleuser2.email, "id": originalroleuser2.id, "obj": originalroleuser2},
        {"email": user.email, "id": user.id, "obj": user},
        {"email": student.email,"id": student.id, "obj": student}
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
        otherPosition="test other position",
        phoneNumber="123-4567",
        instituteName="test institute",
        institutePosition="test institute position",
        instituteName2="test institute2",
        institutePosition2="test institute position2",
        instituteName3="",
        institutePosition3="",
        instituteName4="",
        institutePosition4="",
        instituteName5="",
        institutePosition5=""
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
        otherPosition="test other position",
        phoneNumber="123-4567",
        instituteName="test institute",
        institutePosition="test institute position",
        instituteName2="test institute2",
        institutePosition2="test institute position2",
        instituteName3="",
        institutePosition3="",
        instituteName4="",
        institutePosition4="",
        instituteName5="",
        institutePosition5=""
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
        otherPosition="test other position",
        phoneNumber="123-4567",
        instituteName="test institute",
        institutePosition="test institute position",
        instituteName2="test institute2",
        institutePosition2="test institute position2",
        instituteName3="",
        institutePosition3="",
        instituteName4="",
        institutePosition4="",
        instituteName5="",
        institutePosition5=""
    )
    db.session.add(not_validate_language)
    db.session.commit()
    return [all_data,repo_profile,not_validate_language]


@pytest.fixture()
def json_notifications():
    """Return a notifications instance."""

    after_registration = json_data("data/notifications/after_registration.json")
    after_registration_obo = json_data("data/notifications/after_registration_obo.json")
    offer_approval = json_data("data/notifications/offer_approval.json")
    after_approval = json_data("data/notifications/after_approval.json")
    after_rejection = json_data("data/notifications/after_rejection.json")

    return {
        "after_registration": after_registration,
        "after_registration_obo": after_registration_obo,
        "offer_approval": offer_approval,
        "after_approval": after_approval,
        "after_rejection": after_rejection,
    }
