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
import shutil
import tempfile
import json
from os.path import dirname, exists, join
import pytest
from flask import Flask
from flask_babelex import Babel
from flask_celeryext import FlaskCeleryExt
from flask.cli import ScriptInfo
from flask_menu import Menu
from invenio_i18n import InvenioI18N
from invenio_access import InvenioAccess
from invenio_accounts import InvenioAccounts
from invenio_admin import InvenioAdmin
from invenio_access.models import ActionRoles, ActionUsers
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import Role, User
from invenio_accounts.testutils import create_test_user
from invenio_assets import InvenioAssets
from invenio_cache import InvenioCache
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_deposit import InvenioDeposit
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.models import Location
from invenio_indexer import InvenioIndexer
from invenio_mail import InvenioMail
from invenio_oaiserver import InvenioOAIServer
from invenio_records import InvenioRecords
from invenio_search import InvenioSearch
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database
from weko_index_tree.models import Index

import copy
import uuid
from invenio_pidstore.models import PersistentIdentifier,PIDStatus,RecordIdentifier
from invenio_pidrelations.models import PIDRelation
from weko_records.api import ItemsMetadata

from invenio_communities import InvenioCommunities
from invenio_communities.models import Community
from invenio_communities.views.api import blueprint as api_blueprint
from invenio_communities.views.ui import blueprint as ui_blueprint


@pytest.yield_fixture()
def instance_path():
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)

@pytest.fixture()
def base_app(instance_path, request):
    """Flask application fixture."""
    app_ = Flask('testapp', instance_path=instance_path,static_folder=join(instance_path, "static"),)
    app_.config.update(
        TESTING=True,
        CELERY_ALWAYS_EAGER=True,
        CELERY_CACHE_BACKEND="memory",
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_RESULT_BACKEND="cache",
        COMMUNITIES_MAIL_ENABLED=False,
        SECRET_KEY='CHANGE_ME',
        SECURITY_PASSWORD_SALT='CHANGE_ME_ALSO',
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI',
        #     'sqlite:///test.db'),
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                          'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        SEARCH_ELASTIC_HOSTS=os.environ.get(
            'SEARCH_ELASTIC_HOSTS', None),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        OAISERVER_REGISTER_RECORD_SIGNALS=True,
        OAISERVER_REGISTER_SET_SIGNALS=False,
        OAISERVER_ID_PREFIX='oai:localhost:recid/',
        SERVER_NAME='test_server',
        THEME_SITEURL='https://inveniosoftware.org',
        MAIL_SUPPRESS_SEND=True,
        SEARCH_INDEX_PREFIX="test-",
        INDEXER_DEFAULT_DOCTYPE='item-v1.0.0',
        INDEXER_DEFAULT_INDEX="{}-weko-item-v1.0.0".format("test"),
        SEARCH_UI_SEARCH_INDEX="{}-weko".format("test"),
    )
    FlaskCeleryExt(app_)
    Menu(app_)
    Babel(app_)
    InvenioI18N(app_)
    InvenioDB(app_)
    InvenioDeposit(app_)
    InvenioAccounts(app_)
    InvenioAssets(app_)
    InvenioAccess(app_)
    #InvenioAdmin(app_)
    InvenioCache(app_)
    InvenioSearch(app_)
    InvenioRecords(app_)
    InvenioIndexer(app_)
    InvenioOAIServer(app_)
    InvenioFilesREST(app_)
    InvenioCommunities(app_)
    InvenioMail(app_)

    app_.register_blueprint(ui_blueprint)
    app_.register_blueprint(api_blueprint, url_prefix='/api/communities')

    return app_

@pytest.yield_fixture()
def app(base_app):
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
    db_.drop_all()


@pytest.fixture()
def user():
    """Create a example user."""
    return create_test_user(email='test@test.org')

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
        subrepoadmin = create_test_user(email="subrepoadmin@test.org")
    else:
        user = User.query.filter_by(email="user@test.org").first()
        contributor = User.query.filter_by(email="contributor@test.org").first()
        comadmin = User.query.filter_by(email="comadmin@test.org").first()
        repoadmin = User.query.filter_by(email="repoadmin@test.org").first()
        sysadmin = User.query.filter_by(email="sysadmin@test.org").first()
        generaluser = User.query.filter_by(email="generaluser@test.org")
        originalroleuser = create_test_user(email="originalroleuser@test.org")
        originalroleuser2 = create_test_user(email="originalroleuser2@test.org")
        subrepoadmin = User.query.filter_by(email="subrepoadmin@test.org").first()

    role_count = Role.query.filter_by(name="System Administrator").count()
    if role_count != 1:
        sysadmin_role = ds.create_role(name="System Administrator")
        repoadmin_role = ds.create_role(name="Repository Administrator")
        contributor_role = ds.create_role(name="Contributor")
        comadmin_role = ds.create_role(name="Community Administrator")
        general_role = ds.create_role(name="General")
        originalrole = ds.create_role(name="Original Role")
        group_role = ds.create_role(name="Group Role")
    else:
        sysadmin_role = Role.query.filter_by(name="System Administrator").first()
        repoadmin_role = Role.query.filter_by(name="Repository Administrator").first()
        contributor_role = Role.query.filter_by(name="Contributor").first()
        comadmin_role = Role.query.filter_by(name="Community Administrator").first()
        general_role = Role.query.filter_by(name="General").first()
        originalrole = Role.query.filter_by(name="Original Role").first()
        group_role = Role.query.filter_by(name="Group Role").first()



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
        ds.add_role_to_user(sysadmin, sysadmin_role)
        ds.add_role_to_user(repoadmin, repoadmin_role)
        ds.add_role_to_user(contributor, contributor_role)
        ds.add_role_to_user(comadmin, comadmin_role)
        ds.add_role_to_user(generaluser, general_role)
        ds.add_role_to_user(originalroleuser, originalrole)
        ds.add_role_to_user(originalroleuser2, originalrole)
        ds.add_role_to_user(originalroleuser2, repoadmin_role)
        ds.add_role_to_user(subrepoadmin, group_role)
        ds.add_role_to_user(subrepoadmin, comadmin_role)



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
        {"email": subrepoadmin.email, "id": subrepoadmin.id, "obj": subrepoadmin},
    ]


@pytest.fixture()
def location(app,db):
    """Create default location."""
    tmppath = tempfile.mkdtemp()
    with db.session.begin_nested():
        Location.query.delete()
        loc = Location(name='local', uri=tmppath, default=True)
        db.session.add(loc)
    db.session.commit()
    return location

@pytest.fixture()
def communities(app, db, users):
    """Create some example communities."""
    #user1 = db_.session.merge(user)
    #ds = app.extensions['invenio-accounts'].datastore
    #r = ds.create_role(name='superuser', description='1234')
    #ds.add_role_to_user(user1, r)
    #ds.commit()
    user1 = users[2]["obj"]
    r = Role.query.filter_by(name="System Administrator").first()
    index = Index()
    db.session.add(index)
    db.session.commit()
    comm0 = Community.create(community_id='comm1', role_id=r.id,
                             id_user=user1.id, title='Title1',
                             description='Description1',
                             root_node_id=index.id,
                             group_id=1)
    comm1 = Community.create(community_id='comm2', role_id=r.id,
                             id_user=user1.id, title='A',
                             root_node_id=index.id,
                             group_id=1)
    comm2 = Community.create(community_id='oth3', role_id=r.id,
                             id_user=user1.id,
                             root_node_id=index.id,
                             group_id=1)
    return comm0, comm1, comm2

@pytest.fixture
def script_info(app):
    """Get ScriptInfo object for testing CLI."""
    return ScriptInfo(create_app=lambda info: app)

@pytest.yield_fixture()
def disable_request_email(app):
    """Fixture for disabling request emails."""
    orig = app.config['COMMUNITIES_MAIL_ENABLED']
    app.config['COMMUNITIES_MAIL_ENABLED'] = False
    yield
    app.config['COMMUNITIES_MAIL_ENABLED'] = orig


@pytest.fixture()
def communities_for_filtering(app, db, user):
    """Create some example communities."""
    user1 = db_.session.merge(user)
    ds = app.extensions['invenio-accounts'].datastore
    r = ds.create_role(name='superuser', description='1234')
    ds.add_role_to_user(user1, r)
    ds.commit()

    index = Index()
    db.session.add(index)
    db.session.commit()
    comm0 = Community.create(community_id='comm1', role_id=r.id,
                             id_user=user1.id, title='Test1',
                             description=('Beautiful is better than ugly. '
                                          'Explicit is better than implicit.'),
                             root_node_id=index.id,
                             group_id=1)
    comm1 = Community.create(community_id='comm2', role_id=r.id,
                             id_user=user1.id, title='Testing case 2',
                             description=('Flat is better than nested. '
                                          'Sparse is better than dense.'),
                             root_node_id=index.id,
                             group_id=1)
    comm2 = Community.create(community_id='oth3', role_id=r.id,
                             id_user=user1.id, title='A word about testing',
                             description=('Errors should never pass silently. '
                                          'Unless explicitly silenced.'),
                             root_node_id=index.id,
                             group_id=1)
    return comm0, comm1, comm2

@pytest.yield_fixture()
def client(app):
    with app.test_client() as client:
        yield client

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

        #deposit.commit()

    return recid, depid, record, item, parent, doi, deposit

@pytest.fixture()
def db_records(app,db,mocker):
    mocker.patch("invenio_records.api.before_record_insert.send")
    mocker.patch("invenio_records.api.after_record_insert.send")
    record_datas = list()
    with open("tests/data/test_record/record_metadata.json") as f:
        record_datas = json.load(f)

    item_datas = list()
    with open("tests/data/test_record/item_metadata.json") as f:
        item_datas = json.load(f)

    recid, depid, record, item, parent, doi, deposit = create_record(db,record_datas[0],item_datas[0])

    return recid, depid, record, item, parent, doi, deposit
