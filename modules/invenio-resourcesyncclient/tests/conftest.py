# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# INVENIO-ResourceSyncClient is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""

from __future__ import absolute_import, print_function

from os.path import join
import shutil
import tempfile
import os
import datetime

import pytest
from flask import Flask
from flask_babelex import Babel
from flask_menu import Menu
from sqlalchemy_utils.functions import create_database, database_exists
from invenio_access import InvenioAccess
from invenio_access.models import ActionRoles, ActionUsers
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import Role, User
from invenio_accounts.testutils import create_test_user
from invenio_admin import InvenioAdmin
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_i18n import InvenioI18N
from weko_admin import WekoAdmin
from weko_admin.models import SessionLifetime
from weko_index_tree.models import Index


from invenio_resourcesyncclient import INVENIOResourceSyncClient
from invenio_resourcesyncclient.views import blueprint
from invenio_resourcesyncclient.models import ResyncIndexes, ResyncLogs

@pytest.fixture(scope='module')
def celery_config():
    """Override pytest-invenio fixture.

    TODO: Remove this fixture if you add Celery support.
    """
    return {}


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
        static_folder=join(instance_path, "static"),
    )
    app_.config.update(
        SERVER_NAME="test_server",
        TESTING=True,
        CELERY_ALWAYS_EAGER=True,
        CELERY_CACHE_BACKEND="memory",
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_RESULT_BACKEND="cache",
        CACHE_REDIS_URL="redis://redis:6379/0",
        CACHE_REDIS_DB=0,
        CACHE_REDIS_HOST="redis",
        REDIS_PORT="6379",
        JSONSCHEMAS_URL_SCHEME="http",
        SECRET_KEY="CHANGE_ME",
        SECURITY_PASSWORD_SALT="CHANGE_ME_ALSO",
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "SQLALCHEMY_DATABASE_URI", "sqlite:///test.db"
        ),
        INVENIO_RESYNC_INDEXES_STATUS={
            'automatic': 'Automatic',
            'manual': 'Manual'
        }
    )

    Babel(app_)
    Menu(app_)
    InvenioAccounts(app_)
    InvenioAccess(app_)
    InvenioAdmin(app_)
    InvenioDB(app_)
    INVENIOResourceSyncClient(app_)
    InvenioI18N(app_)
    WekoAdmin(app_)

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


@pytest.fixture()
def session_time(app, db):
    session_lifetime = SessionLifetime(lifetime=60,is_delete=False)
    
    with db.session.begin_nested():
        db.session.add(session_lifetime)


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
    else:
        user = User.query.filter_by(email="user@test.org").first()
        contributor = User.query.filter_by(email="contributor@test.org").first()
        comadmin = User.query.filter_by(email="comadmin@test.org").first()
        repoadmin = User.query.filter_by(email="repoadmin@test.org").first()
        sysadmin = User.query.filter_by(email="sysadmin@test.org").first()
        generaluser = User.query.filter_by(email="generaluser@test.org")
        originalroleuser = create_test_user(email="originalroleuser@test.org")
        originalroleuser2 = create_test_user(email="originalroleuser2@test.org")

    role_count = Role.query.filter_by(name="System Administrator").count()
    if role_count != 1:
        sysadmin_role = ds.create_role(name="System Administrator")
        repoadmin_role = ds.create_role(name="Repository Administrator")
        contributor_role = ds.create_role(name="Contributor")
        comadmin_role = ds.create_role(name="Community Administrator")
        general_role = ds.create_role(name="General")
        originalrole = ds.create_role(name="Original Role")
    else:
        sysadmin_role = Role.query.filter_by(name="System Administrator").first()
        repoadmin_role = Role.query.filter_by(name="Repository Administrator").first()
        contributor_role = Role.query.filter_by(name="Contributor").first()
        comadmin_role = Role.query.filter_by(name="Community Administrator").first()
        general_role = Role.query.filter_by(name="General").first()
        originalrole = Role.query.filter_by(name="Original Role").first()

    ds.add_role_to_user(sysadmin, sysadmin_role)
    ds.add_role_to_user(repoadmin, repoadmin_role)
    ds.add_role_to_user(contributor, contributor_role)
    ds.add_role_to_user(comadmin, comadmin_role)
    ds.add_role_to_user(generaluser, general_role)
    ds.add_role_to_user(originalroleuser, originalrole)
    ds.add_role_to_user(originalroleuser2, originalrole)
    ds.add_role_to_user(originalroleuser2, repoadmin_role)

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
            ActionRoles(
                action="files-rest-object-delete-version", role=contributor_role
            ),
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

    return [
        {"email": contributor.email, "id": contributor.id, "obj": contributor},
        {"email": repoadmin.email, "id": repoadmin.id, "obj": repoadmin},
        {"email": sysadmin.email, "id": sysadmin.id, "obj": sysadmin},
        {"email": comadmin.email, "id": comadmin.id, "obj": comadmin},
        {"email": generaluser.email, "id": generaluser.id, "obj": sysadmin},
        {
            "email": originalroleuser.email,
            "id": originalroleuser.id,
            "obj": originalroleuser,
        },
        {
            "email": originalroleuser2.email,
            "id": originalroleuser2.id,
            "obj": originalroleuser2,
        },
        {"email": user.email, "id": user.id, "obj": user},
    ]



@pytest.fixture
def test_indices(app, db):
    def base_index(id, parent, position, public_date=None, coverpage_state=False, recursive_browsing_role=False,
                   recursive_contribute_role=False, recursive_browsing_group=False,
                   recursive_contribute_group=False, online_issn=''):
        _browsing_role = "3,-98,-99"
        _contribute_role = "1,2,3,4,-98,-99"
        _group = "g1,g2"
        return Index(
            id=id,
            parent=parent,
            position=position,
            index_name="Test index {}".format(id),
            index_name_english="Test index {}".format(id),
            index_link_name="Test index link {}".format(id),
            index_link_name_english="Test index link {}".format(id),
            index_link_enabled=False,
            more_check=False,
            display_no=position,
            harvest_public_state=True,
            public_state=True,
            public_date=public_date,
            recursive_public_state=True if not public_date else False,
            coverpage_state=coverpage_state,
            recursive_coverpage_check=True if coverpage_state else False,
            browsing_role=_browsing_role,
            recursive_browsing_role=recursive_browsing_role,
            contribute_role=_contribute_role,
            recursive_contribute_role=recursive_contribute_role,
            browsing_group=_group,
            recursive_browsing_group=recursive_browsing_group,
            contribute_group=_group,
            recursive_contribute_group=recursive_contribute_group,
            biblio_flag=True if not online_issn else False,
            online_issn=online_issn
        )
    
    with db.session.begin_nested():
        db.session.add(base_index(1, 0, 0))
        db.session.add(base_index(2, 0, 1))
        db.session.add(base_index(3, 0, 2))
    db.session.commit()


@pytest.fixture
def test_resync(app, db, test_indices):
    resync_handler1 = ResyncIndexes(
        id=10,
        status="Automatic",
        index_id=2,
        repository_name="root",
        from_date=None,
        to_date=None,
        resync_save_dir="",
        resync_mode="Baseline",
        saving_format="JPCOAR-XML",
        base_url="base_test1",
        is_running=None,
        interval_by_day=1,
        task_id=None,
        result=[1, 2]
    )
    resync_handler2 = ResyncIndexes(
        id=20,
        status="Manual",
        index_id=2,
        repository_name="root",
        from_date=None,
        to_date=None,
        resync_save_dir="",
        resync_mode="Baseline",
        saving_format="JPCOAR-XML",
        base_url="base_test2",
        is_running=None,
        interval_by_day=1,
        task_id='test_task',
        result=None
    )
    resync_handler3 = ResyncIndexes(
        id=30,
        status="Automatic",
        index_id=2,
        repository_name="root",
        from_date=None,
        to_date=None,
        resync_save_dir="",
        resync_mode="Baseline",
        saving_format="JPCOAR-XML",
        base_url="base_test3",
        is_running=None,
        interval_by_day=1,
        task_id=None,
        result='[{"uri": "tests/data/test_records.json", "timestamp": 1664550000, "ln": [{"rel": "file", "href": "tests/data/test_records.json"}]}]'
    )

    resync_log = ResyncLogs(
        id=10,
        resync_indexes_id=10,
        log_type="",
        task_id=None,
        start_time=datetime.datetime(2022, 10, 1),
        end_time=datetime.datetime(2022, 10, 2),
        status="Success",
        errmsg=None,
        counter=None
    )

    with db.session.begin_nested():
        db.session.add(resync_handler1)
        db.session.add(resync_handler2)
        db.session.add(resync_handler3)
        db.session.add(resync_log)
    db.session.commit()