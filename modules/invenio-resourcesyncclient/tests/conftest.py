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
import json
import uuid
from datetime import datetime as dt

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
from invenio_deposit.config import (
    DEPOSIT_DEFAULT_STORAGE_CLASS,
    DEPOSIT_RECORDS_UI_ENDPOINTS,
    DEPOSIT_REST_ENDPOINTS,
    DEPOSIT_DEFAULT_JSONSCHEMA,
    DEPOSIT_JSONSCHEMAS_PREFIX,
)
from invenio_i18n import InvenioI18N
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.models import Bucket, Location, ObjectVersion
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_pidrelations import InvenioPIDRelations
from invenio_pidstore import InvenioPIDStore
from invenio_records import InvenioRecords
from invenio_records_rest import InvenioRecordsREST
from invenio_search import InvenioSearch, current_search_client
from weko_admin import WekoAdmin
from weko_admin.models import SessionLifetime
from weko_index_tree.models import Index
from weko_deposit import WekoDeposit
from weko_records import WekoRecords
from weko_records.models import ItemType, ItemTypeMapping, ItemTypeName
from weko_records_ui.config import WEKO_PERMISSION_SUPER_ROLE_USER
from weko_search_ui import WekoSearchUI
from weko_schema_ui.models import OAIServerSchema


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
        CACHE_REDIS_URL=os.environ.get(
            "CACHE_REDIS_URL", "redis://redis:6379/0"
        ),
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
        INVENIO_RESYNC_INDEXES_STATUS={
            'automatic': 'Automatic',
            'manual': 'Manual'
        },
        WEKO_BUCKET_QUOTA_SIZE=50 * 1024 * 1024 * 1024,
        WEKO_MAX_FILE_SIZE=50 * 1024 * 1024 * 1024,
        INDEXER_DEFAULT_INDEX="{}-weko-item-v1.0.0".format("test"),
        SEARCH_UI_SEARCH_INDEX="{}-weko".format("test"),
        SEARCH_ELASTIC_HOSTS="elasticsearch",
        SEARCH_INDEX_PREFIX="test-",
        INDEXER_DEFAULT_DOCTYPE='item-v1.0.0',
        INDEXER_FILE_DOC_TYPE='content',
        WEKO_SCHEMA_JPCOAR_V1_SCHEMA_NAME='jpcoar_v1_mapping',
        WEKO_SCHEMA_DDI_SCHEMA_NAME='ddi_mapping',
        DEPOSIT_DEFAULT_JSONSCHEMA=DEPOSIT_DEFAULT_JSONSCHEMA,
        DEPOSIT_JSONSCHEMAS_PREFIX=DEPOSIT_JSONSCHEMAS_PREFIX,
        DEPOSIT_RECORDS_UI_ENDPOINTS=DEPOSIT_RECORDS_UI_ENDPOINTS,
        DEPOSIT_REST_ENDPOINTS=DEPOSIT_REST_ENDPOINTS,
        DEPOSIT_DEFAULT_STORAGE_CLASS=DEPOSIT_DEFAULT_STORAGE_CLASS,
        WEKO_PERMISSION_SUPER_ROLE_USER=WEKO_PERMISSION_SUPER_ROLE_USER
    )

    Babel(app_)
    Menu(app_)
    InvenioAccounts(app_)
    InvenioAccess(app_)
    InvenioAdmin(app_)
    InvenioDB(app_)
    InvenioJSONSchemas(app_)
    InvenioPIDStore(app_)
    InvenioPIDRelations(app_)
    InvenioFilesREST(app_)
    InvenioSearch(app_)
    InvenioRecords(app_)
    InvenioRecordsREST(app_)
    INVENIOResourceSyncClient(app_)
    InvenioI18N(app_)
    WekoAdmin(app_)
    WekoDeposit(app_)
    WekoRecords(app_)
    WekoSearchUI(app_)

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
def esindex(app):
    current_search_client.indices.delete(index='test-*')
    with open("tests/data/item-v1.0.0.json","r") as f:
        mapping = json.load(f)
    try:
        current_search_client.indices.create(app.config["INDEXER_DEFAULT_INDEX"],body=mapping)
        current_search_client.indices.put_alias(index=app.config["INDEXER_DEFAULT_INDEX"], name="test-weko")
    except:
        current_search_client.indices.create("test-weko-items",body=mapping)
        current_search_client.indices.put_alias(index="test-weko-items", name="test-weko")

    try:
        yield current_search_client
    finally:
        current_search_client.indices.delete(index='test-*')


@pytest.fixture()
def location(app, db, instance_path):
    with db.session.begin_nested():
        Location.query.delete()
        loc = Location(name='local', uri=instance_path, default=True)
        db.session.add(loc)
    db.session.commit()
    return loc


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


@pytest.fixture()
def db_itemtype(app, db):
    # Multiple
    item_type_multiple_name = ItemTypeName(
        id=10, name="Multiple", has_site_license=True, is_active=True
    )
    item_type_multiple_schema = dict()
    with open("tests/data/itemtype_multiple_schema.json", "r") as f:
        item_type_multiple_schema = json.load(f)

    item_type_multiple_form = dict()
    with open("tests/data/itemtype_multiple_form.json", "r") as f:
        item_type_multiple_form = json.load(f)

    item_type_multiple_render = dict()
    with open("tests/data/itemtype_multiple_render.json", "r") as f:
        item_type_multiple_render = json.load(f)

    item_type_multiple_mapping = dict()
    with open("tests/data/itemtype_multiple_mapping.json", "r") as f:
        item_type_multiple_mapping = json.load(f)

    item_type_multiple = ItemType(
        id=10,
        name_id=10,
        harvesting_type=True,
        schema=item_type_multiple_schema,
        form=item_type_multiple_form,
        render=item_type_multiple_render,
        tag=1,
        version_id=1,
        is_deleted=False,
    )

    item_type_multiple_mapping = ItemTypeMapping(id=10, item_type_id=10, mapping=item_type_multiple_mapping)

    # BioSample
    item_type_biosample_name = ItemTypeName(
        id=32102, name="Biosample", has_site_license=True, is_active=True
    )
    item_type_biosample_schema = dict()
    with open("tests/data/itemtype_biosample_schema.json", "r") as f:
        item_type_biosample_schema = json.load(f)

    item_type_biosample_form = dict()
    with open("tests/data/itemtype_biosample_form.json", "r") as f:
        item_type_biosample_form = json.load(f)

    item_type_biosample_render = dict()
    with open("tests/data/itemtype_biosample_render.json", "r") as f:
        item_type_biosample_render = json.load(f)

    item_type_biosample_mapping = dict()
    with open("tests/data/itemtype_biosample_mapping.json", "r") as f:
        item_type_biosample_mapping = json.load(f)
    item_type_biosample = ItemType(
        id=32102,
        name_id=32102,
        harvesting_type=True,
        schema=item_type_biosample_schema,
        form=item_type_biosample_form,
        render=item_type_biosample_render,
        tag=1,
        version_id=1,
        is_deleted=False,
    )

    item_type_biosample_mapping = ItemTypeMapping(id=32102, item_type_id=32102, mapping=item_type_biosample_mapping)

    # BioProject
    item_type_bioproject_name = ItemTypeName(
        id=32103, name="Bioproject", has_site_license=True, is_active=True
    )
    item_type_bioproject_schema = dict()
    with open("tests/data/itemtype_bioproject_schema.json", "r") as f:
        item_type_bioproject_schema = json.load(f)

    item_type_bioproject_form = dict()
    with open("tests/data/itemtype_bioproject_form.json", "r") as f:
        item_type_bioproject_form = json.load(f)

    item_type_bioproject_render = dict()
    with open("tests/data/itemtype_bioproject_render.json", "r") as f:
        item_type_bioproject_render = json.load(f)

    item_type_bioproject_mapping = dict()
    with open("tests/data/itemtype_bioproject_mapping.json", "r") as f:
        item_type_bioproject_mapping = json.load(f)
    item_type_bioproject = ItemType(
        id=32103,
        name_id=32103,
        harvesting_type=True,
        schema=item_type_bioproject_schema,
        form=item_type_bioproject_form,
        render=item_type_bioproject_render,
        tag=1,
        version_id=1,
        is_deleted=False,
    )

    item_type_bioproject_mapping = ItemTypeMapping(id=32103, item_type_id=32103, mapping=item_type_bioproject_mapping)

    with db.session.begin_nested():
        db.session.add(item_type_multiple_name)
        db.session.add(item_type_multiple)
        db.session.add(item_type_multiple_mapping)
        db.session.add(item_type_biosample_name)
        db.session.add(item_type_biosample)
        db.session.add(item_type_biosample_mapping)
        db.session.add(item_type_bioproject_name)
        db.session.add(item_type_bioproject)
        db.session.add(item_type_bioproject_mapping)
    db.session.commit()

    return {
        "item_type_multiple_name": item_type_multiple_name,
        "item_type_multiple": item_type_multiple,
        "item_type_multiple_mapping": item_type_multiple_mapping,
        "item_type_biosample_name": item_type_biosample_name,
        "item_type_biosample": item_type_biosample,
        "item_type_biosample_mapping": item_type_biosample_mapping,
        "item_type_bioproject_name": item_type_bioproject_name,
        "item_type_bioproject": item_type_bioproject,
        "item_type_bioproject_mapping": item_type_bioproject_mapping,
    }


@pytest.fixture()
def db_oaischema(app, db):
    schema_name = "jpcoar_mapping"
    form_data = {"name": "jpcoar", "file_name": "jpcoar_scm.xsd", "root_name": "jpcoar"}
    xsd = '{"dc:title": {"type": {"maxOccurs": "unbounded", "minOccurs": 1, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "dcterms:alternative": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:creator": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}, "jpcoar:nameIdentifier": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "nameIdentifierScheme", "ref": null, "restriction": {"enumeration": ["e-Rad", "NRID", "ORCID", "ISNI", "VIAF", "AID", "kakenhi", "Ringgold", "GRID"]}}, {"use": "optional", "name": "nameIdentifierURI", "ref": null}]}}, "jpcoar:creatorName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:familyName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:givenName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:creatorAlternative": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:affiliation": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}, "jpcoar:nameIdentifier": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "nameIdentifierScheme", "ref": null, "restriction": {"enumeration": ["e-Rad", "NRID", "ORCID", "ISNI", "VIAF", "AID", "kakenhi", "Ringgold", "GRID"]}}, {"use": "optional", "name": "nameIdentifierURI", "ref": null}]}}, "jpcoar:affiliationName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}}}, "jpcoar:contributor": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "contributorType", "ref": null, "restriction": {"enumeration": ["ContactPerson", "DataCollector", "DataCurator", "DataManager", "Distributor", "Editor", "HostingInstitution", "Producer", "ProjectLeader", "ProjectManager", "ProjectMember", "RegistrationAgency", "RegistrationAuthority", "RelatedPerson", "Researcher", "ResearchGroup", "Sponsor", "Supervisor", "WorkPackageLeader", "Other"]}}]}, "jpcoar:nameIdentifier": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "nameIdentifierScheme", "ref": null, "restriction": {"enumeration": ["e-Rad", "NRID", "ORCID", "ISNI", "VIAF", "AID", "kakenhi", "Ringgold", "GRID"]}}, {"use": "optional", "name": "nameIdentifierURI", "ref": null}]}}, "jpcoar:contributorName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:familyName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:givenName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:contributorAlternative": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:affiliation": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}, "jpcoar:nameIdentifier": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "nameIdentifierScheme", "ref": null, "restriction": {"enumeration": ["e-Rad", "NRID", "ORCID", "ISNI", "VIAF", "AID", "kakenhi", "Ringgold", "GRID"]}}, {"use": "optional", "name": "nameIdentifierURI", "ref": null}]}}, "jpcoar:affiliationName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}}}, "dcterms:accessRights": {"type": {"maxOccurs": 1, "minOccurs": 0, "attributes": [{"use": "required", "name": "rdf:resource", "ref": "rdf:resource"}], "restriction": {"enumeration": ["embargoed access", "metadata only access", "open access", "restricted access"]}}}, "rioxxterms:apc": {"type": {"maxOccurs": 1, "minOccurs": 0, "restriction": {"enumeration": ["Paid", "Partially waived", "Fully waived", "Not charged", "Not required", "Unknown"]}}}, "dc:rights": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "rdf:resource", "ref": "rdf:resource"}, {"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:rightsHolder": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}, "jpcoar:nameIdentifier": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "nameIdentifierScheme", "ref": null, "restriction": {"enumeration": ["e-Rad", "NRID", "ORCID", "ISNI", "VIAF", "AID", "kakenhi", "Ringgold", "GRID"]}}, {"use": "optional", "name": "nameIdentifierURI", "ref": null}]}}, "jpcoar:rightsHolderName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}}, "jpcoar:subject": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}, {"use": "optional", "name": "subjectURI", "ref": null}, {"use": "required", "name": "subjectScheme", "ref": null, "restriction": {"enumeration": ["BSH", "DDC", "LCC", "LCSH", "MeSH", "NDC", "NDLC", "NDLSH", "Sci-Val", "UDC", "Other"]}}]}}, "datacite:description": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}, {"use": "required", "name": "descriptionType", "ref": null, "restriction": {"enumeration": ["Abstract", "Methods", "TableOfContents", "TechnicalInfo", "Other"]}}]}}, "dc:publisher": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "datacite:date": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "dateType", "ref": null, "restriction": {"enumeration": ["Accepted", "Available", "Collected", "Copyrighted", "Created", "Issued", "Submitted", "Updated", "Valid"]}}]}}, "dc:language": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "restriction": {"patterns": ["^[a-z]{3}$"]}}}, "dc:type": {"type": {"maxOccurs": 1, "minOccurs": 1, "attributes": [{"use": "required", "name": "rdf:resource", "ref": "rdf:resource"}], "restriction": {"enumeration": ["conference paper", "data paper", "departmental bulletin paper", "editorial", "journal article", "newspaper", "periodical", "review article", "software paper", "article", "book", "book part", "cartographic material", "map", "conference object", "conference proceedings", "conference poster", "dataset", "aggregated data", "clinical trial data", "compiled data", "encoded data", "experimental data", "genomic data", "geospatial data", "laboratory notebook", "measurement and test data", "observational data", "recorded data", "simulation data", "survey data", "interview", "image", "still image", "moving image", "video", "lecture", "patent", "internal report", "report", "research report", "technical report", "policy report", "report part", "working paper", "data management plan", "sound", "thesis", "bachelor thesis", "master thesis", "doctoral thesis", "interactive resource", "learning object", "manuscript", "musical notation", "research proposal", "software", "technical documentation", "workflow", "other"]}}}, "datacite:version": {"type": {"maxOccurs": 1, "minOccurs": 0}}, "oaire:versiontype": {"type": {"maxOccurs": 1, "minOccurs": 0, "attributes": [{"use": "required", "name": "rdf:resource", "ref": "rdf:resource"}], "restriction": {"enumeration": ["AO", "SMUR", "AM", "P", "VoR", "CVoR", "EVoR", "NA"]}}}, "jpcoar:identifier": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "identifierType", "ref": null, "restriction": {"enumeration": ["DOI", "HDL", "URI"]}}]}}, "jpcoar:identifierRegistration": {"type": {"maxOccurs": 1, "minOccurs": 0, "attributes": [{"use": "required", "name": "identifierType", "ref": null, "restriction": {"enumeration": ["JaLC", "Crossref", "DataCite", "PMID"]}}]}}, "jpcoar:relation": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "relationType", "ref": null, "restriction": {"enumeration": ["isVersionOf", "hasVersion", "isPartOf", "hasPart", "isReferencedBy", "references", "isFormatOf", "hasFormat", "isReplacedBy", "replaces", "isRequiredBy", "requires", "isSupplementTo", "isSupplementedBy", "isIdenticalTo", "isDerivedFrom", "isSourceOf"]}}]}, "jpcoar:relatedIdentifier": {"type": {"maxOccurs": 1, "minOccurs": 0, "attributes": [{"use": "required", "name": "identifierType", "ref": null, "restriction": {"enumeration": ["ARK", "arXiv", "DOI", "HDL", "ICHUSHI", "ISBN", "J-GLOBAL", "Local", "PISSN", "EISSN", "NAID", "PMID", "PURL", "SCOPUS", "URI", "WOS"]}}]}}, "jpcoar:relatedTitle": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}}, "dcterms:temporal": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "datacite:geoLocation": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}, "datacite:geoLocationPoint": {"type": {"maxOccurs": 1, "minOccurs": 0}, "datacite:pointLongitude": {"type": {"maxOccurs": 1, "minOccurs": 1, "restriction": {"maxInclusive": 180, "minInclusive": -180}}}, "datacite:pointLatitude": {"type": {"maxOccurs": 1, "minOccurs": 1, "restriction": {"maxInclusive": 90, "minInclusive": -90}}}}, "datacite:geoLocationBox": {"type": {"maxOccurs": 1, "minOccurs": 0}, "datacite:westBoundLongitude": {"type": {"maxOccurs": 1, "minOccurs": 1, "restriction": {"maxInclusive": 180, "minInclusive": -180}}}, "datacite:eastBoundLongitude": {"type": {"maxOccurs": 1, "minOccurs": 1, "restriction": {"maxInclusive": 180, "minInclusive": -180}}}, "datacite:southBoundLatitude": {"type": {"maxOccurs": 1, "minOccurs": 1, "restriction": {"maxInclusive": 90, "minInclusive": -90}}}, "datacite:northBoundLatitude": {"type": {"maxOccurs": 1, "minOccurs": 1, "restriction": {"maxInclusive": 90, "minInclusive": -90}}}}, "datacite:geoLocationPlace": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}}}, "jpcoar:fundingReference": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}, "datacite:funderIdentifier": {"type": {"maxOccurs": 1, "minOccurs": 0, "attributes": [{"use": "required", "name": "funderIdentifierType", "ref": null, "restriction": {"enumeration": ["Crossref Funder", "GRID", "ISNI", "Other"]}}]}}, "jpcoar:funderName": {"type": {"maxOccurs": "unbounded", "minOccurs": 1, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "datacite:awardNumber": {"type": {"maxOccurs": 1, "minOccurs": 0, "attributes": [{"use": "optional", "name": "awardURI", "ref": null}]}}, "jpcoar:awardTitle": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}}, "jpcoar:sourceIdentifier": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "identifierType", "ref": null, "restriction": {"enumeration": ["PISSN", "EISSN", "ISSN", "NCID"]}}]}}, "jpcoar:sourceTitle": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:volume": {"type": {"maxOccurs": 1, "minOccurs": 0}}, "jpcoar:issue": {"type": {"maxOccurs": 1, "minOccurs": 0}}, "jpcoar:numPages": {"type": {"maxOccurs": 1, "minOccurs": 0}}, "jpcoar:pageStart": {"type": {"maxOccurs": 1, "minOccurs": 0}}, "jpcoar:pageEnd": {"type": {"maxOccurs": 1, "minOccurs": 0}}, "dcndl:dissertationNumber": {"type": {"maxOccurs": 1, "minOccurs": 0}}, "dcndl:degreeName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "dcndl:dateGranted": {"type": {"maxOccurs": 1, "minOccurs": 0}}, "jpcoar:degreeGrantor": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}, "jpcoar:nameIdentifier": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "nameIdentifierScheme", "ref": null, "restriction": {"enumeration": ["e-Rad", "NRID", "ORCID", "ISNI", "VIAF", "AID", "kakenhi", "Ringgold", "GRID"]}}, {"use": "optional", "name": "nameIdentifierURI", "ref": null}]}}, "jpcoar:degreeGrantorName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}}, "jpcoar:conference": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}, "jpcoar:conferenceName": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:conferenceSequence": {"type": {"maxOccurs": 1, "minOccurs": 0}}, "jpcoar:conferenceSponsor": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:conferenceDate": {"type": {"maxOccurs": 1, "minOccurs": 0, "attributes": [{"use": "optional", "name": "startMonth", "ref": null, "restriction": {"maxInclusive": 12, "minInclusive": 1, "totalDigits": 2}}, {"use": "optional", "name": "endYear", "ref": null, "restriction": {"maxInclusive": 2200, "minInclusive": 1400, "totalDigits": 4}}, {"use": "optional", "name": "startDay", "ref": null, "restriction": {"maxInclusive": 31, "minInclusive": 1, "totalDigits": 2}}, {"use": "optional", "name": "endDay", "ref": null, "restriction": {"maxInclusive": 31, "minInclusive": 1, "totalDigits": 2}}, {"use": "optional", "name": "endMonth", "ref": null, "restriction": {"maxInclusive": 12, "minInclusive": 1, "totalDigits": 2}}, {"use": "optional", "name": "xml:lang", "ref": "xml:lang"}, {"use": "optional", "name": "startYear", "ref": null, "restriction": {"maxInclusive": 2200, "minInclusive": 1400, "totalDigits": 4}}]}}, "jpcoar:conferenceVenue": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:conferencePlace": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "optional", "name": "xml:lang", "ref": "xml:lang"}]}}, "jpcoar:conferenceCountry": {"type": {"maxOccurs": 1, "minOccurs": 0, "restriction": {"patterns": ["^[A-Z]{3}$"]}}}}, "jpcoar:file": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}, "jpcoar:URI": {"type": {"maxOccurs": 1, "minOccurs": 0, "attributes": [{"use": "optional", "name": "label", "ref": null}, {"use": "optional", "name": "objectType", "ref": null, "restriction": {"enumeration": ["abstract", "dataset", "fulltext", "software", "summary", "thumbnail", "other"]}}]}}, "jpcoar:mimeType": {"type": {"maxOccurs": 1, "minOccurs": 0}}, "jpcoar:extent": {"type": {"maxOccurs": "unbounded", "minOccurs": 0}}, "datacite:date": {"type": {"maxOccurs": "unbounded", "minOccurs": 0, "attributes": [{"use": "required", "name": "dateType", "ref": null, "restriction": {"enumeration": ["Accepted", "Available", "Collected", "Copyrighted", "Created", "Issued", "Submitted", "Updated", "Valid"]}}]}}, "datacite:version": {"type": {"maxOccurs": 1, "minOccurs": 0}}}, "custom:system_file": {"type": {"minOccurs": 0, "maxOccurs": "unbounded"}, "jpcoar:URI": {"type": {"minOccurs": 0, "maxOccurs": 1, "attributes": [{"name": "objectType", "ref": null, "use": "optional", "restriction": {"enumeration": ["abstract", "summary", "fulltext", "thumbnail", "other"]}}, {"name": "label", "ref": null, "use": "optional"}]}}, "jpcoar:mimeType": {"type": {"minOccurs": 0, "maxOccurs": 1}}, "jpcoar:extent": {"type": {"minOccurs": 0, "maxOccurs": "unbounded"}}, "datacite:date": {"type": {"minOccurs": 1, "maxOccurs": "unbounded", "attributes": [{"name": "dateType", "ref": null, "use": "required", "restriction": {"enumeration": ["Accepted", "Available", "Collected", "Copyrighted", "Created", "Issued", "Submitted", "Updated", "Valid"]}}]}}, "datacite:version": {"type": {"minOccurs": 0, "maxOccurs": 1}}}}'
    namespaces = {
        "": "https://github.com/JPCOAR/schema/blob/master/1.0/",
        "dc": "http://purl.org/dc/elements/1.1/",
        "xs": "http://www.w3.org/2001/XMLSchema",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "xml": "http://www.w3.org/XML/1998/namespace",
        "dcndl": "http://ndl.go.jp/dcndl/terms/",
        "oaire": "http://namespace.openaire.eu/schema/oaire/",
        "jpcoar": "https://github.com/JPCOAR/schema/blob/master/1.0/",
        "dcterms": "http://purl.org/dc/terms/",
        "datacite": "https://schema.datacite.org/meta/kernel-4/",
        "rioxxterms": "http://www.rioxx.net/schema/v2.0/rioxxterms/",
    }
    schema_location = "https://github.com/JPCOAR/schema/blob/master/1.0/jpcoar_scm.xsd"
    jpcoar_mapping = OAIServerSchema(
        id=uuid.uuid4(),
        schema_name=schema_name,
        form_data=form_data,
        xsd=xsd,
        namespaces=namespaces,
        schema_location=schema_location,
        isvalid=True,
        is_mapping=False,
        isfixed=False,
        version_id=1,
    )
    jpcoar_v1_mapping = OAIServerSchema(
        id=uuid.uuid4(),
        schema_name='jpcoar_v1_mapping',
        form_data=form_data,
        xsd=xsd,
        namespaces=namespaces,
        schema_location=schema_location,
        isvalid=True,
        is_mapping=False,
        isfixed=False,
        version_id=1,
    )
    with db.session.begin_nested():
        db.session.add(jpcoar_mapping)
        db.session.add(jpcoar_v1_mapping)


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
        resync_mode="Incremental",
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
    resync_handler4 = ResyncIndexes(
        id=40,
        status="Automatic",
        index_id=2,
        repository_name="root",
        from_date=None,
        to_date=None,
        resync_save_dir="",
        resync_mode="Incremental",
        saving_format="JPCOAR-XML",
        base_url="base_test4",
        is_running=None,
        interval_by_day=1,
        task_id=None,
        result='[{"uri": "tests/data/test_records.json", "timestamp": 1664550000, "ln": [{"rel": "file", "href": "tests/data/test_records.json"}]}]'
    )
    resync_handler5 = ResyncIndexes(
        id=50,
        status="Automatic",
        index_id=2,
        repository_name="root",
        from_date=None,
        to_date=None,
        resync_save_dir="",
        resync_mode="Audit",
        saving_format="JPCOAR-XML",
        base_url="base_test5",
        is_running=None,
        interval_by_day=1,
        task_id=None,
        result='[{"uri": "tests/data/test_records.json", "timestamp": 1664550000, "ln": [{"rel": "file", "href": "tests/data/test_records.json"}]}]'
    )
    resync_handler6 = ResyncIndexes(
        id=60,
        status="Automatic",
        index_id=2,
        repository_name="root",
        from_date=None,
        to_date=None,
        resync_save_dir="",
        resync_mode="Audit",
        saving_format="BIOSAMPLE-JSON-LD",
        base_url="base_test6",
        is_running=None,
        interval_by_day=1,
        task_id=None,
        result='[{"uri": "tests/data/biosample_data01.jsonld",' +
                    ' "timestamp": 1664550000, "ln": [{"rel": "file",' +
                    ' "href": "tests/data/biosample_data01.jsonld"}]}]'
    )
    resync_handler7 = ResyncIndexes(
        id=70,
        status="Automatic",
        index_id=2,
        repository_name="root",
        from_date=None,
        to_date=None,
        resync_save_dir="",
        resync_mode="Audit",
        saving_format="BIOPROJECT-JSON-LD",
        base_url="base_test7",
        is_running=None,
        interval_by_day=1,
        task_id=None,
        result='[{"uri": "tests/data/bioproject_data01.jsonld",' +
                    ' "timestamp": 1664550000, "ln": [{"rel": "file",' +
                    ' "href": "tests/data/bioproject_data01.jsonld"}]}]'
    )
    resync_handler8 = ResyncIndexes(
        id=80,
        status="Manual",
        index_id=2,
        repository_name="root",
        from_date=dt.strptime('2024-11-27 00:00:00', '%Y-%m-%d %H:%M:%S'),
        to_date=None,
        resync_save_dir="",
        resync_mode="Incremental",
        saving_format="JPCOAR-XML",
        base_url="base_test2",
        is_running=None,
        interval_by_day=1,
        task_id='test_task',
        result=None
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
        db.session.add(resync_handler4)
        db.session.add(resync_handler5)
        db.session.add(resync_handler6)
        db.session.add(resync_handler7)
        db.session.add(resync_handler8)
        db.session.add(resync_log)
    db.session.commit()
