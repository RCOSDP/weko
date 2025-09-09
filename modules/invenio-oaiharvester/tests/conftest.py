# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Pytest configuration."""

from __future__ import absolute_import, print_function

import os
import json
import shutil
import tempfile
import uuid
from datetime import datetime
from os.path import join
from mock import patch
import copy

import pytest
from flask import Flask
from flask.cli import ScriptInfo
from flask_celeryext import FlaskCeleryExt
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import User
from invenio_accounts.testutils import create_test_user
from invenio_db import InvenioDB, db
from invenio_files_rest.models import Location
from invenio_i18n import InvenioI18N
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_pidrelations import InvenioPIDRelations
from invenio_records import InvenioRecords
from sqlalchemy_utils.functions import create_database, database_exists
from weko_index_tree.models import Index
from weko_search_ui import WekoSearchUI
from weko_theme import WekoTheme
from invenio_access import InvenioAccess
from invenio_access.models import ActionUsers, ActionRoles
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import User, Role
from invenio_accounts.testutils import create_test_user
from invenio_cache import InvenioCache
from invenio_deposit import InvenioDeposit
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.models import Location
from invenio_i18n import InvenioI18N
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_pidstore import InvenioPIDStore
from invenio_pidrelations import InvenioPIDRelations
from invenio_records import InvenioRecords
from invenio_records_rest import InvenioRecordsREST
from invenio_search import InvenioSearch, current_search_client
from sqlalchemy_utils.functions import create_database, database_exists
from invenio_pidstore.models import PersistentIdentifier, PIDStatus, RecordIdentifier
from invenio_pidrelations.models import PIDRelation
from weko_records.models import ItemType, ItemTypeMapping, ItemTypeName
from weko_index_tree.models import Index
from weko_search_ui import WekoSearchUI
from weko_schema_ui.models import OAIServerSchema
from weko_theme import WekoTheme
from weko_deposit import WekoDeposit
from weko_records import WekoRecords
from weko_records.api import ItemsMetadata
from weko_records_ui.config import WEKO_PERMISSION_SUPER_ROLE_USER


from invenio_oaiharvester import InvenioOAIHarvester
from invenio_oaiharvester.models import OAIHarvestConfig, HarvestSettings



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
        SECRET_KEY="CHANGE_ME",
        SECURITY_PASSWORD_SALT="CHANGE_ME_ALSO",
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI',
        #     'sqlite:///test.db'),
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                          'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        TESTING=True,
        INDEX_IMG='indextree/36466818-image.jpg',
        INDEXER_DEFAULT_INDEX="{}-weko-item-v1.0.0".format("test"),
        SEARCH_UI_SEARCH_INDEX="{}-weko".format("test"),
        SERVER_NAME="TEST_SERVER",
        SEARCH_ELASTIC_HOSTS="elasticsearch",
        SEARCH_INDEX_PREFIX="test-",
        INDEXER_DEFAULT_DOCTYPE='item-v1.0.0',
        INDEXER_FILE_DOC_TYPE='content',
        WEKO_BUCKET_QUOTA_SIZE=50 * 1024 * 1024 * 1024,
        WEKO_MAX_FILE_SIZE=50 * 1024 * 1024 * 1024,
        FILES_REST_DEFAULT_STORAGE_CLASS='S',
        FILES_REST_STORAGE_CLASS_LIST={
            'S': 'Standard',
            'A': 'Archive',
        },
        DEPOSIT_DEFAULT_JSONSCHEMA='deposits/deposit-v1.0.0.json',
        WEKO_SCHEMA_JPCOAR_V1_SCHEMA_NAME='jpcoar_v1_mapping',
        WEKO_SCHEMA_DDI_SCHEMA_NAME='ddi_mapping',
        WEKO_PERMISSION_SUPER_ROLE_USER=WEKO_PERMISSION_SUPER_ROLE_USER,
    )
    FlaskCeleryExt(app_)
    InvenioAccounts(app_)
    InvenioAccess(app_)
    InvenioCache(app_)
    InvenioDB(app_)
    InvenioDeposit(app_)
    InvenioI18N(app_)
    InvenioPIDStore(app_)
    InvenioJSONSchemas(app_)
    InvenioPIDRelations(app_)
    InvenioFilesREST(app_)
    InvenioSearch(app_)
    InvenioRecords(app_)
    InvenioRecordsREST(app_)
    WekoSearchUI(app_)
    WekoTheme(app_)
    WekoDeposit(app_)
    WekoRecords(app_)
    InvenioOAIHarvester(app_)

    return app_


@pytest.yield_fixture()
def app(base_app):
    with base_app.app_context():
        yield base_app


@pytest.yield_fixture()
def client(app):
    with app.test_client() as client:
        yield client


@pytest.fixture()
def db(app):
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
@pytest.fixture
def test_indices(app, db):
    def base_index(id, parent, position, public_date=None, coverpage_state=False, recursive_browsing_role=False,
                   recursive_contribute_role=False, recursive_browsing_group=False,
                   recursive_contribute_group=False, online_issn='',harvest_spec=""):
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
            online_issn=online_issn,
            harvest_spec=harvest_spec
        )

    with db.session.begin_nested():
        db.session.add(base_index(1, 0, 0, datetime(2022, 1, 1), True, True, True, True, True, '1234-5678'))
        db.session.add(base_index(2, 0, 1))
        db.session.add(base_index(3, 0, 2))
        db.session.add(base_index(11, 1, 0))
        db.session.add(base_index(21, 2, 0))
        db.session.add(base_index(22, 2, 1)),
        db.session.add(base_index(12, 1, 1,harvest_spec="11"))
    db.session.commit()


@pytest.fixture()
def script_info(app):
    """Get ScriptInfo object for testing CLI."""
    return ScriptInfo(create_app=lambda info: app)


@pytest.fixture()
def sample_config(app, db):
    source_name = "arXiv"
    with app.app_context():
        source = OAIHarvestConfig(
            name=source_name,
            baseurl="http://export.arxiv.org/oai2",
            metadataprefix="arXiv",
            setspecs="physics",
        )
        source.save()
        db.session.commit()
    return source_name


@pytest.fixture()
def location(app, db):
    """Create default location."""
    tmppath = tempfile.mkdtemp()

    location = Location.query.filter_by(name="testloc").count()
    if location != 1:
        loc = Location(name="testloc", uri=tmppath, default=True)
        db.session.add(loc)
        db.session.commit()
    else:
        loc = Location.query.filter_by(name="testloc").first()

    yield loc

    shutil.rmtree(tmppath)


@pytest.fixture()
def harvest_setting(app, db, test_indices):
    setting_list = []

    jpcoar_setting = HarvestSettings(
        id=1,
        repository_name="jpcoar_test",
        base_url="http://export.arxiv.org/oai2",
        from_date=datetime(2022, 10, 1),
        until_date=datetime(2022, 10, 2),
        metadata_prefix="jpcoar_1.0",
        index_id=1,
        update_style="0",
        auto_distribution="1"
    )
    with db.session.begin_nested():
        db.session.add(jpcoar_setting)
    setting_list.append(jpcoar_setting)

    ddi_setting = HarvestSettings(
        id=2,
        repository_name="ddi_test",
        base_url="http://export.arxiv.org/oai2",
        from_date=datetime(2022, 10, 1),
        until_date=datetime(2022, 10, 2),
        metadata_prefix="oai_ddi25",
        index_id=1,
        update_style="0",
        auto_distribution="1"
    )
    with db.session.begin_nested():
        db.session.add(ddi_setting)
    setting_list.append(ddi_setting)

    dc_setting = HarvestSettings(
        id=3,
        repository_name="dc_test",
        base_url="http://export.arxiv.org/oai2",
        from_date=datetime(2022, 10, 1),
        until_date=datetime(2022, 10, 2),
        metadata_prefix="oai_dc",
        index_id=1,
        update_style="0",
        auto_distribution="1"
    )
    with db.session.begin_nested():
        db.session.add(dc_setting)
    setting_list.append(dc_setting)

    other_setting = HarvestSettings(
        id=4,
        repository_name="other_test",
        base_url="http://export.arxiv.org/oai2",
        from_date=datetime(2022, 10, 1),
        until_date=datetime(2022, 10, 2),
        metadata_prefix="other_prefix",
        index_id=1,
        update_style="0",
        auto_distribution="1"
    )
    with db.session.begin_nested():
        db.session.add(other_setting)
    setting_list.append(other_setting)

    db.session.commit()

    return setting_list


@pytest.fixture()
def sample_record_xml():
    raw_xml = open(os.path.join(
        os.path.dirname(__file__),
        "data/sample_arxiv_response.xml"
    )).read()
    return raw_xml


@pytest.fixture()
def sample_record_xml_utf8():
    raw_xml = open(os.path.join(
        os.path.dirname(__file__),
        "data/sample_arxiv_response_utf8.xml"
    )).read()
    return raw_xml


@pytest.fixture()
def sample_record_xml_oai_dc():
    raw_xml = open(os.path.join(
        os.path.dirname(__file__),
        "data/sample_oai_dc_response.xml"
    )).read()
    return raw_xml


@pytest.fixture()
def sample_empty_set():
    raw_xml = open(os.path.join(
        os.path.dirname(__file__),
        "data/sample_empty_response.xml"
    )).read()
    return raw_xml


@pytest.fixture
def sample_list_xml():
    raw_physics_xml = open(os.path.join(
        os.path.dirname(__file__),
        "data/sample_arxiv_response_listrecords_physics.xml"
    )).read()
    return raw_physics_xml


@pytest.fixture
def sample_list_xml_cs():
    raw_cs_xml = open(os.path.join(
        os.path.dirname(__file__),
        "data/sample_arxiv_response_listrecords_cs.xml"
    )).read()
    return raw_cs_xml

@pytest.fixture
def sample_list_xml_no_sets():
    raw_cs_xml = open(os.path.join(
        os.path.dirname(__file__),
        "data/sample_arxiv_response_listrecords_no_sets.xml"
    )).read()
    return raw_cs_xml


@pytest.fixture
def sample_jpcoar_list_xml():
    raw_cs_xml = open(os.path.join(
        os.path.dirname(__file__),
        "data/oai.xml"
    )).read()
    return raw_cs_xml


@pytest.fixture()
def location(app, db):
    """Create default location."""
    tmppath = tempfile.mkdtemp()
    with db.session.begin_nested():
        Location.query.delete()
        loc = Location(name='local', uri=tmppath, default=True)
        db.session.add(loc)
    db.session.commit()
    return loc


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

    # Harvesting DDI
    item_type_ddi_name = ItemTypeName(
        id=11, name="Harvesting DDI", has_site_license=True, is_active=True
    )
    item_type_ddi_schema = dict()
    with open("tests/data/itemtype_ddi_schema.json", "r") as f:
        item_type_ddi_schema = json.load(f)

    item_type_ddi_form = dict()
    with open("tests/data/itemtype_ddi_form.json", "r") as f:
        item_type_ddi_form = json.load(f)

    item_type_ddi_render = dict()
    with open("tests/data/itemtype_ddi_render.json", "r") as f:
        item_type_ddi_render = json.load(f)

    item_type_ddi_mapping = dict()
    with open("tests/data/itemtype_ddi_mapping.json", "r") as f:
        item_type_ddi_mapping = json.load(f)
    item_type_ddi = ItemType(
        id=11,
        name_id=11,
        harvesting_type=True,
        schema=item_type_ddi_schema,
        form=item_type_ddi_form,
        render=item_type_ddi_render,
        tag=1,
        version_id=1,
        is_deleted=False,
    )

    item_type_ddi_mapping = ItemTypeMapping(id=11, item_type_id=11, mapping=item_type_ddi_mapping)

    # Harvesting DC
    item_type_dc_name = ItemTypeName(
        id=12, name="Harvesting dc", has_site_license=True, is_active=True
    )
    item_type_dc_schema = dict()
    with open("tests/data/itemtype_dc_schema.json", "r") as f:
        item_type_dc_schema = json.load(f)

    item_type_dc_form = dict()
    with open("tests/data/itemtype_dc_form.json", "r") as f:
        item_type_dc_form = json.load(f)

    item_type_dc_render = dict()
    with open("tests/data/itemtype_dc_render.json", "r") as f:
        item_type_dc_render = json.load(f)

    item_type_dc_mapping = dict()
    with open("tests/data/itemtype_dc_mapping.json", "r") as f:
        item_type_dc_mapping = json.load(f)

    item_type_dc = ItemType(
        id=12,
        name_id=12,
        harvesting_type=True,
        schema=item_type_dc_schema,
        form=item_type_dc_form,
        render=item_type_dc_render,
        tag=1,
        version_id=1,
        is_deleted=False,
    )
    item_type_dc_mapping = ItemTypeMapping(id=12, item_type_id=12, mapping=item_type_dc_mapping)

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
        db.session.add(item_type_ddi_name)
        db.session.add(item_type_ddi)
        db.session.add(item_type_ddi_mapping)
        db.session.add(item_type_dc_name)
        db.session.add(item_type_dc)
        db.session.add(item_type_dc_mapping)
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
        "item_type_ddi_name": item_type_ddi_name,
        "item_type_ddi": item_type_ddi,
        "item_type_ddi_mapping": item_type_ddi_mapping,
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


@pytest.fixture(scope="function", autouse=True)
def reset_class_value():
    yield
    from invenio_oaiharvester.harvester import (
        BaseMapper,DCMapper,DDIMapper
    )
    BaseMapper.itemtype_map = {}
    BaseMapper.identifiers = []

    DCMapper.itemtype_map = {}
    DCMapper.identifiers = []
    DDIMapper.itemtype_map = {}
    DDIMapper.identifiers = []


def create_record(db, record_data, item_data):
    from weko_deposit.api import WekoDeposit, WekoRecord
    with db.session.begin_nested():
        record_data = copy.deepcopy(record_data)
        item_data = copy.deepcopy(item_data)
        rec_uuid = uuid.uuid4()
        recid = PersistentIdentifier.create('recid', record_data["recid"],object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
        depid = PersistentIdentifier.create('depid', record_data["recid"],object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
        rel = PIDRelation.create(recid,depid,3)
        db.session.add(rel)
        parent=None
        doi = None

        if '.' in record_data["recid"]:
            parent = PersistentIdentifier.get("recid",int(float(record_data["recid"])))
            recid_p = PIDRelation.get_child_relations(parent).one_or_none()
            PIDRelation.create(recid_p.parent, recid,2)
        else:
            parent = PersistentIdentifier.create('parent', "parent:{}".format(record_data["recid"]),object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
            rel = PIDRelation.create(parent, recid,2,0)
            db.session.add(rel)
            RecordIdentifier.next()
        if record_data.get("_oai").get("id"):
            oaiid = PersistentIdentifier.create('oai', record_data["_oai"]["id"],pid_provider="oai",object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
            hvstid = PersistentIdentifier.create('hvstid', record_data["_oai"]["id"],object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
        if "item_1612345678910" in record_data:
            for i in range(len(record_data["item_1612345678910"]["attribute_value_mlt"])):
                data = record_data["item_1612345678910"]["attribute_value_mlt"][i]
                PersistentIdentifier.create(data.get("subitem_16345678901234").lower(),data.get("subitem_1623456789123"),object_type='rec', object_uuid=rec_uuid,status=PIDStatus.REGISTERED)
        record = WekoRecord.create(record_data, id_=rec_uuid)
        item = ItemsMetadata.create(item_data, id_=rec_uuid)
        deposit = WekoDeposit(record, record.model)

        deposit.commit()

    return recid, depid, record, item, parent, doi, deposit

@pytest.fixture()
def db_records(app,db):
    record_datas = list()
    with open("tests/data/test_record/record_metadata.json") as f:
        record_datas = json.load(f)

    item_datas = list()
    with open("tests/data/test_record/item_metadata.json") as f:
        item_datas = json.load(f)

    for i in range(len(record_datas)):
        recid, depid, record, item, parent, doi, deposit = create_record(db,record_datas[i],item_datas[i])
