# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Signposting is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""

import os
import shutil
import tempfile
import json
from unittest.mock import patch

import pytest
from flask import Flask
from sqlalchemy_utils.functions import create_database, database_exists

from invenio_access import InvenioAccess
from invenio_access.models import ActionRoles, ActionUsers
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import Role, User
from invenio_db import InvenioDB, db as db_
from invenio_db.utils import drop_alembic_version_table
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.models import Location
from invenio_records import InvenioRecords
from invenio_pidstore import InvenioPIDStore
from invenio_pidstore import current_pidstore
from invenio_accounts.testutils import create_test_user
from invenio_records_ui import InvenioRecordsUI

from weko_index_tree import WekoIndexTree
from weko_index_tree.api import Indexes
from weko_logging.audit import WekoLoggingUserActivity
from weko_signposting import WekoSignposting
from weko_signposting.views import blueprint
from weko_workflow import WekoWorkflow

from .helpers import create_record, json_data

@pytest.yield_fixture()
def instance_path():
    """Temporary instance path."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.fixture()
def base_app(instance_path):
    app_ = Flask(
        'testapp',
        instance_path=instance_path,
        static_folder=os.path.join(instance_path, "static"),
    )
    os.environ["INVENIO_WEB_HOST_NAME"] = "127.0.0.1"
    app_.config.update(
        THEME_SITEURL="https://localhost",
        SECRET_KEY="SECRET_KEY",
        SECURITY_PASSWORD_SALT='CHANGE_ME_ALSO',
        SERVER_NAME="TEST_SERVER",
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'
        # ),
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI','postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        SEARCH_UI_SEARCH_INDEX="test-weko",
        INDEXER_DEFAULT_DOCTYPE="item-v1.0.0",
        INDEXER_FILE_DOC_TYPE="content",
        TESTING=True,
        OAISERVER_METADATA_FORMATS=oaiserver,
        RECORDS_UI_ENDPOINTS=dict(
            recid_signposting=dict(
                pid_type='recid',
                route='/records/<pid_value>',
                view_imp='weko_signposting.api.requested_signposting',
                methods=['HEAD']
            ),
            recid=dict(
                pid_type='recid',
                route='/records/<pid_value>',
                view_imp='weko_records_ui.views.default_view_method',
                template='weko_records_ui/detail.html',
                record_class='weko_deposit.api:WekoRecord',
                permission_factory_imp='weko_records_ui.permissions'
                                    ':page_permission_factory',
            ),
        ),
    )
    InvenioAccess(app_)
    InvenioAccounts(app_)
    InvenioDB(app_)
    InvenioFilesREST(app_)
    InvenioRecords(app_)
    InvenioRecordsUI(app_)
    InvenioPIDStore(app_)
    WekoIndexTree(app_)
    WekoWorkflow(app_)
    WekoLoggingUserActivity(app_)
    return app_


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    WekoSignposting(base_app)
    with base_app.app_context():
        yield base_app


@pytest.yield_fixture()
def db(app):
    """Get setup database."""
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()
    drop_alembic_version_table()


@pytest.yield_fixture()
def client(app):
    """Get test client."""
    with app.test_client() as client:
        yield client


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
        noroleuser = create_test_user(email="noroleuser@test.org")
    else:
        user = User.query.filter_by(email="user@test.org").first()
        contributor = User.query.filter_by(email="contributor@test.org").first()
        comadmin = User.query.filter_by(email="comadmin@test.org").first()
        repoadmin = User.query.filter_by(email="repoadmin@test.org").first()
        sysadmin = User.query.filter_by(email="sysadmin@test.org").first()
        generaluser = User.query.filter_by(email="generaluser@test.org").first()
        originalroleuser = User.query.filter_by(email="originalroleuser@test.org").first()
        originalroleuser2 = User.query.filter_by(email="originalroleuser2@test.org").first()
        noroleuser = User.query.filter_by(email="noroleuser@test.org").first()

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
    ds.add_role_to_user(user, sysadmin_role)
    ds.add_role_to_user(user, repoadmin_role)
    ds.add_role_to_user(user, contributor_role)
    ds.add_role_to_user(user, comadmin_role)

    # Assign access authorization
    with db.session.begin_nested():
        action_users = [ActionUsers(action="superuser-access", user=sysadmin)]
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
        {"email": noroleuser.email, "id": noroleuser.id, "obj": noroleuser},
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

@pytest.fixture()
def db_records(db, instance_path, users):
    with db.session.begin_nested():
        Location.query.delete()
        loc = Location(name="local", uri=instance_path, default=True)
        db.session.add(loc)
    db.session.commit()

    record_data = json_data("data/test_records.json")
    item_data = json_data("data/test_items.json")
    record_num = len(record_data)
    result = []
    with db.session.begin_nested():
        for d in range(record_num):
            result.append(create_record(record_data[d], item_data[d]))
    db.session.commit()

    index_metadata = {
        "id": 1,
        "parent": 0,
        "value": "IndexA",
    }
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        Indexes.create(0, index_metadata)
    index_metadata = {
        "id": 2,
        "parent": 0,
        "value": "IndexB",
    }

    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        Indexes.create(0, index_metadata)

    yield result


@pytest.fixture(scope='module')
def celery_config():
    """Override pytest-invenio fixture.

    TODO: Remove this fixture if you add Celery support.
    """
    return {}


oaiserver = {
    'jpcoar_1.0': {
        'serializer': (
            'weko_schema_ui.utils:dumps_oai_etree', {
                'schema_type': 'jpcoar',
            }
        ),
        'namespace': 'https://irdb.nii.ac.jp/schema/jpcoar/1.0/',
        'schema': 'https://irdb.nii.ac.jp/schema/jpcoar/1.0/jpcoar_scm.xsd',
    },
    'oai_dc': {
        'serializer': (
            'weko_schema_ui.utils:dumps_oai_etree', {
                'schema_type': 'oai_dc',
            }
        ),
        'namespace': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
        'schema': 'http://www.openarchives.org/OAI/2.0/oai_dc.xsd',
    },
    'ddi': {
        'serializer': (
            'weko_schema_ui.utils:dumps_oai_etree', {
                'schema_type': 'ddi',
            }
        ),
        'namespace': 'ddi:codebook:2_5',
        'schema': 'https://ddialliance.org/Specification'
                  '/DDI-Codebook/2.5/XMLSchema/codebook.xsd',
    },
}
