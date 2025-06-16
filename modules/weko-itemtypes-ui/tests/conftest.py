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

import copy
import json
import os
import re
import shutil
import tempfile
import time
import uuid
from datetime import datetime
from os.path import dirname, exists, join
from re import T
from glob import glob

import pytest
from click.testing import CliRunner
from flask import Blueprint, Flask
from flask_assets import assets
from flask_admin import Admin
from flask_babelex import Babel
from flask_menu import Menu
from invenio_access import InvenioAccess
from invenio_access.models import ActionRoles, ActionUsers
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import Role, User
from invenio_accounts.testutils import create_test_user, login_user_via_session
from invenio_accounts.views.settings import blueprint as invenio_accounts_blueprint
from invenio_admin import InvenioAdmin
from invenio_admin.views import blueprint as invenio_admin_blueprint
from invenio_assets import InvenioAssets
from invenio_assets.cli import collect, npm
from invenio_cache import InvenioCache
from invenio_communities import InvenioCommunities
from invenio_communities.models import Community
from invenio_communities.views.ui import blueprint as invenio_communities_blueprint
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_deposit import InvenioDeposit
from invenio_deposit.config import (
    DEPOSIT_DEFAULT_JSONSCHEMA,
    DEPOSIT_DEFAULT_STORAGE_CLASS,
    DEPOSIT_JSONSCHEMAS_PREFIX,
    DEPOSIT_RECORDS_UI_ENDPOINTS,
    DEPOSIT_REST_ENDPOINTS,
)
from invenio_deposit.ext import InvenioDeposit, InvenioDepositREST
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.config import FILES_REST_STORAGE_CLASS_LIST
from invenio_files_rest.models import Location
from invenio_i18n import InvenioI18N
from invenio_indexer import InvenioIndexer
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_oaiserver import InvenioOAIServer
from invenio_pidrelations import InvenioPIDRelations
from invenio_pidrelations.config import PIDRELATIONS_RELATION_TYPES
from invenio_pidrelations.models import PIDRelation
from invenio_pidstore import InvenioPIDStore
from invenio_pidstore.models import PersistentIdentifier, PIDStatus, Redirect
from invenio_records import InvenioRecords
from invenio_records_rest import InvenioRecordsREST
from invenio_rest import InvenioREST
from invenio_search import InvenioSearch, RecordsSearch, current_search, current_search_client
from invenio_stats import InvenioStats
from invenio_stats.config import SEARCH_INDEX_PREFIX as index_prefix
from invenio_theme import InvenioTheme
from kombu import Exchange, Queue
from unittest.mock import patch
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy_utils.functions import create_database, database_exists
from weko_admin import WekoAdmin
from weko_admin.config import WEKO_ADMIN_DEFAULT_ITEM_EXPORT_SETTINGS
from weko_admin.models import RankingSettings, SessionLifetime, AdminSettings
from weko_authors.models import Authors, AuthorsAffiliationSettings, AuthorsPrefixSettings
from weko_deposit import WekoDeposit
from weko_deposit.api import WekoIndexer
from weko_deposit.config import DEPOSIT_RECORDS_API, WEKO_DEPOSIT_ITEMS_CACHE_PREFIX
from weko_groups import WekoGroups
from weko_index_tree import WekoIndexTree, WekoIndexTreeREST
from weko_index_tree.api import Indexes
from weko_index_tree.config import WEKO_INDEX_TREE_DEFAULT_DISPLAY_NUMBER, WEKO_INDEX_TREE_REST_ENDPOINTS
from weko_index_tree.models import Index
from weko_items_ui import WekoItemsUI
from weko_items_ui.views import blueprint as weko_items_ui_blueprint
from weko_items_ui.views import blueprint_api as weko_items_ui_blueprint_api
from weko_records import WekoRecords
from weko_records.models import ItemType, ItemTypeMapping, ItemTypeName,ItemTypeProperty
from weko_records_ui import WekoRecordsUI
from weko_records_ui.config import WEKO_RECORDS_UI_LICENSE_DICT
from weko_records_ui.models import RocrateMapping
from weko_schema_ui import WekoSchemaUI
from weko_schema_ui.models import OAIServerSchema
from weko_search_ui import WekoSearchREST, WekoSearchUI
from weko_search_ui.config import (
    INDEXER_DEFAULT_DOCTYPE,
    INDEXER_FILE_DOC_TYPE,
    RECORDS_REST_SORT_OPTIONS,
    SEARCH_UI_SEARCH_INDEX,
    WEKO_SEARCH_REST_ENDPOINTS,
)
from weko_theme import WekoTheme
from weko_user_profiles.config import WEKO_USERPROFILES_GENERAL_ROLE, WEKO_USERPROFILES_ROLES
from weko_user_profiles.models import UserProfile
from weko_workflow import WekoWorkflow
from weko_workflow.models import Action, ActionStatus, ActionStatusPolicy, Activity, FlowAction, FlowDefine, WorkFlow
from weko_workflow.views import workflow_blueprint as weko_workflow_blueprint
from werkzeug.local import LocalProxy

from weko_itemtypes_ui import WekoItemtypesUI
from weko_itemtypes_ui.admin import itemtype_meta_data_adminview,itemtype_properties_adminview,itemtype_mapping_adminview,itemtype_rocrate_mapping_adminview
from weko_logging.audit import WekoLoggingUserActivity
from tests.helpers import json_data

"""Pytest configuration."""

import shutil
import tempfile

import pytest
from flask import Flask
from flask_babelex import Babel
from invenio_assets import InvenioAssets
from invenio_i18n import InvenioI18N
from invenio_theme import InvenioTheme
from weko_records import WekoRecords


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
        SECRET_KEY="SECRET_KEY",
        TESTING=True,
        SERVER_NAME="test_server",
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     "SQLALCHEMY_DATABASE_URI", "sqlite:///test.db"
        # ),
        SQLALCHEMY_DATABASE_URI=os.getenv(
            'SQLALCHEMY_DATABASE_URI', 'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        ACCOUNTS_USERINFO_HEADERS=True,
        WEKO_PERMISSION_SUPER_ROLE_USER=[
            "System Administrator",
            "Repository Administrator",
        ],
        WEKO_PERMISSION_ROLE_COMMUNITY=["Community Administrator"],
        THEME_SITEURL="https://localhost",
        WEKO_THEME_DEFAULT_COMMUNITY="Root Index",
        #  WEKO_ITEMS_UI_BASE_TEMPLATE = 'weko_items_ui/base.html',
        #  WEKO_ITEMS_UI_INDEX_TEMPLATE= 'weko_items_ui/item_index.html',
        CACHE_TYPE="redis",
        ACCOUNTS_SESSION_REDIS_DB_NO=1,
        CACHE_REDIS_HOST=os.environ.get("INVENIO_REDIS_HOST"),
        REDIS_PORT="6379",
        WEKO_BUCKET_QUOTA_SIZE=50 * 1024 * 1024 * 1024,
        WEKO_MAX_FILE_SIZE=50 * 1024 * 1024 * 1024,
        SEARCH_ELASTIC_HOSTS=os.environ.get("INVENIO_ELASTICSEARCH_HOST"),
        SEARCH_INDEX_PREFIX="{}-".format('test'),
        SEARCH_CLIENT_CONFIG=dict(timeout=120, max_retries=10),
        OAISERVER_ID_PREFIX="oai:inveniosoftware.org:recid/",
        OAISERVER_RECORD_INDEX="_all",
        OAISERVER_REGISTER_SET_SIGNALS=True,
        OAISERVER_METADATA_FORMATS={
            "jpcoar_1.0": {
                "serializer": (
                    "weko_schema_ui.utils:dumps_oai_etree",
                    {
                        "schema_type": "jpcoar_v1",
                    },
                ),
                "namespace": "https://irdb.nii.ac.jp/schema/jpcoar/1.0/",
                "schema": "https://irdb.nii.ac.jp/schema/jpcoar/1.0/jpcoar_scm.xsd",
            }
        },
        DEPOSIT_RECORDS_UI_ENDPOINTS=DEPOSIT_RECORDS_UI_ENDPOINTS,
        DEPOSIT_REST_ENDPOINTS=DEPOSIT_REST_ENDPOINTS,
        DEPOSIT_DEFAULT_STORAGE_CLASS=DEPOSIT_DEFAULT_STORAGE_CLASS,

        WEKO_RECORDS_UI_LICENSE_DICT=WEKO_RECORDS_UI_LICENSE_DICT,
        INDEXER_DEFAULT_INDEX="{}-weko-item-v1.0.0".format(
            'test'
        ),
        WEKO_INDEX_TREE_REST_ENDPOINTS=WEKO_INDEX_TREE_REST_ENDPOINTS,
        WEKO_ADMIN_DEFAULT_ITEM_EXPORT_SETTINGS=WEKO_ADMIN_DEFAULT_ITEM_EXPORT_SETTINGS,
        FILES_REST_STORAGE_CLASS_LIST=FILES_REST_STORAGE_CLASS_LIST,
        FILES_REST_DEFAULT_QUOTA_SIZE=None,
        FILES_REST_DEFAULT_MAX_FILE_SIZE=None,
        DEPOSIT_RECORDS_API=DEPOSIT_RECORDS_API,
        RECORDS_REST_SORT_OPTIONS=RECORDS_REST_SORT_OPTIONS,
        PIDRELATIONS_RELATION_TYPES=PIDRELATIONS_RELATION_TYPES,
        WEKO_USERPROFILES_ROLES=WEKO_USERPROFILES_ROLES,
        EMAIL_DISPLAY_FLG = True,
        SEARCH_UI_SEARCH_INDEX="test-weko",
        WEKO_USERPROFILES_GENERAL_ROLE=WEKO_USERPROFILES_GENERAL_ROLE,
        CACHE_REDIS_DB = 0,
        WEKO_DEPOSIT_ITEMS_CACHE_PREFIX=WEKO_DEPOSIT_ITEMS_CACHE_PREFIX,
        INDEXER_DEFAULT_DOCTYPE=INDEXER_DEFAULT_DOCTYPE,
        INDEXER_FILE_DOC_TYPE=INDEXER_FILE_DOC_TYPE,
        WEKO_INDEX_TREE_DEFAULT_DISPLAY_NUMBER=WEKO_INDEX_TREE_DEFAULT_DISPLAY_NUMBER,
        DEPOSIT_DEFAULT_JSONSCHEMA=DEPOSIT_DEFAULT_JSONSCHEMA,
        DEPOSIT_JSONSCHEMAS_PREFIX=DEPOSIT_JSONSCHEMAS_PREFIX,
        WEKO_SEARCH_REST_ENDPOINTS=WEKO_SEARCH_REST_ENDPOINTS,
        INDEXER_MQ_QUEUE = Queue("indexer", exchange=Exchange("indexer", type="direct"), routing_key="indexer",queue_arguments={"x-queue-type":"quorum"}),
        I18N_LANGUAGES=[("ja", "Japanese"), ("en", "English")],
    )

    app_.config['WEKO_SEARCH_REST_ENDPOINTS']['recid']['search_index']='test-weko'
    # tmp = app_.config['RECORDS_REST_SORT_OPTIONS']['tenant1-weko']
    # app_.config['RECORDS_REST_SORT_OPTIONS']['test-weko']=tmp
    # Babel(app_)
    InvenioI18N(app_)
    InvenioAssets(app_)
    #InvenioAdmin(app_)
    InvenioDB(app_)
    InvenioAccounts(app_)
    InvenioAccess(app_)
    # InvenioTheme(app_)
    # InvenioREST(app_)

    # InvenioCache(app_)

    # InvenioDeposit(app_)
    # InvenioPIDStore(app_)
    # InvenioPIDRelations(app_)
    InvenioRecords(app_)
    # InvenioRecordsREST(app_)
    InvenioFilesREST(app_)
    InvenioJSONSchemas(app_)
    # InvenioOAIServer(app_)

    search = InvenioSearch(app_)

    # WekoSchemaUI(app_)
    InvenioStats(app_)

    # InvenioAdmin(app_)
    Menu(app_)
    WekoRecords(app_)
    WekoDeposit(app_)
    WekoWorkflow(app_)
    WekoGroups(app_)
    WekoAdmin(app_)
    # WekoTheme(app_)
    # WekoRecordsUI(app_)
    # InvenioCommunities(app_)

    InvenioIndexer(app_)
    # WekoSearchREST(app_)
    # WekoIndexTree(app_)
    # WekoIndexTreeREST(app_)
    WekoRecords(app_)
    WekoSearchUI(app_)
    # ext.init_config(app_)
    WekoItemsUI(app_)
    WekoLoggingUserActivity(app_)
    # app_.register_blueprint(invenio_accounts_blueprint)
    # app_.register_blueprint(weko_theme_blueprint)
    # app_.register_blueprint(weko_items_ui_blueprint)
    # app_.register_blueprint(invenio_communities_blueprint)
    # app_.register_blueprint(weko_workflow_blueprint)

    # runner = CliRunner()
    # result = runner.invoke(collect, [],obj=weko_items_ui_blueprint)
    # Run build
    # result = runner.invoke(assets, ['build'],obj=weko_items_ui_blueprint)
    # result = runner.invoke(npm,obj=weko_items_ui_blueprint)

    current_assets = LocalProxy(lambda: app_.extensions["invenio-assets"])
    current_assets.collect.collect()

    return app_


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app



@pytest.yield_fixture()
def client_api(app):
    app.register_blueprint(weko_items_ui_blueprint_api, url_prefix="/api/items")
    with app.test_client() as client:
        yield client



@pytest.yield_fixture()
def client(app):
    """make a test client.

    Args:
        app (Flask): flask app.

    Yields:
        FlaskClient: test client
    """
    app.register_blueprint(weko_items_ui_blueprint, url_prefix="/items")
    with app.test_client() as client:
        yield client

@pytest.fixture()
def admin_view(app):
    WekoItemtypesUI(app)
    admin = Admin(app)
    meta_viewclass=itemtype_meta_data_adminview["view_class"]
    admin.add_view(meta_viewclass(**itemtype_meta_data_adminview["kwargs"]))
    properties_viewclass = itemtype_properties_adminview["view_class"]
    admin.add_view(properties_viewclass(**itemtype_properties_adminview["kwargs"]))
    mapping_viewclass = itemtype_mapping_adminview["view_class"]
    admin.add_view(mapping_viewclass(**itemtype_mapping_adminview["kwargs"]))
    rocratemapping_viewclass = itemtype_rocrate_mapping_adminview["view_class"]
    admin.add_view(rocratemapping_viewclass(**itemtype_rocrate_mapping_adminview["kwargs"]))


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
def item_type(app,db):
    files = [p.split("/")[-1] for p in glob(join(dirname(__file__),"data/item_types","*"))]
    itemtype_data = {}
    for file in files:
        if re.search(r"itemtype",file):
            num = re.search(r"itemtype(\d)",file).group(1)
            ty = re.search(r"_(.*).json",file).group(1)
            if num not in itemtype_data:
                itemtype_data[num]={}
            itemtype_data[num][ty]="data/item_types/"+file
    itemtype_list = []
    for num in range(len(itemtype_data)):
        data = itemtype_data[str(num)]
        id = int(num)+1
        item_type_name = ItemTypeName(
            id=id, name="テストアイテムタイプ"+str(id), has_site_license=True, is_active=True
        )


        schema = json_data(data["schema"])
        form = json_data(data["form"])
        render = json_data(data["render"])
        mapping = json_data(data["mapping"])

        item_type = ItemType(
            id=id,
            name_id=item_type_name.id,
            harvesting_type=True,
            schema=schema,
            form=form,
            render=render,
            tag=1,
            version_id=1,
            is_deleted=False,
        )

        item_type_mapping = ItemTypeMapping(id=id, item_type_id=item_type.id, mapping=mapping)

        with db.session.begin_nested():
            db.session.add(item_type_name)
            db.session.add(item_type)
            db.session.add(item_type_mapping)
        itemtype_list.append(
            {"item_type_name":item_type_name,"item_type":item_type,"item_type_mapping":item_type_mapping}
        )
    db.session.commit()
    return itemtype_list
@pytest.fixture()
def itemtype_props(app,db):
    data = json_data("data/item_type_props.json")

    props = list()
    for d in data:
        prop = ItemTypeProperty(**data[d])
        props.append(prop)
    db.session.add_all(props)
    db.session.commit()
    return props


@pytest.fixture()
def admin_settings(db):
    with db.session.begin_nested():
        items_display = AdminSettings(id=1,name='items_display_settings',settings={"items_display_email": False, "items_search_author": "name", "item_display_open_date": False})
        storage_check = AdminSettings(id=2,name='storage_check_settings',settings={"day": 0, "cycle": "weekly", "threshold_rate": 80})
        site_license_mail = AdminSettings(id=3,name='site_license_mail_settings',settings={"auto_send_flag": False})
        default_properties = AdminSettings(id=4,name='default_properties_settings',settings={"show_flag": True})
        item_expost = AdminSettings(id=5,name='item_export_settings',settings={"allow_item_exporting": True, "enable_contents_exporting": True})
        db.session.add(items_display)
        db.session.add(storage_check)
        db.session.add(site_license_mail)
        db.session.add(default_properties)
        db.session.add(item_expost)
    db.session.commit()

    return {"items_display":items_display,"storage_check":storage_check,"site_license_mail":site_license_mail,"default_properties":default_properties,"item_expost":item_expost}

@pytest.fixture()
def oaiserver_schema(db):
    id = uuid.uuid4()
    schema = OAIServerSchema(
        id = id,
        schema_name="oai_dc_mapping",
        form_data={"name":"oai_dc_mapping","xsd_file":"http://dublincore.org/schemas/xmls/simpledc20021212.xsd","file_name":"oai_dc.xsd","root_name":"dc"},
        xsd="{\"dc:title\": {\"type\": {\"minOccurs\": 1, \"maxOccurs\": 1, \"attributes\": [{\"ref\": \"xml:lang\", \"name\": \"xml:lang\", \"use\": \"optional\"}]}}, \"dc:creator\": {\"type\": {\"minOccurs\": 1, \"maxOccurs\": 1, \"attributes\": [{\"ref\": \"xml:lang\", \"name\": \"xml:lang\", \"use\": \"optional\"}]}}, \"dc:subject\": {\"type\": {\"minOccurs\": 1, \"maxOccurs\": 1, \"attributes\": [{\"ref\": \"xml:lang\", \"name\": \"xml:lang\", \"use\": \"optional\"}]}}, \"dc:description\": {\"type\": {\"minOccurs\": 1, \"maxOccurs\": 1, \"attributes\": [{\"ref\": \"xml:lang\", \"name\": \"xml:lang\", \"use\": \"optional\"}]}}, \"dc:publisher\": {\"type\": {\"minOccurs\": 1, \"maxOccurs\": 1, \"attributes\": [{\"ref\": \"xml:lang\", \"name\": \"xml:lang\", \"use\": \"optional\"}]}}, \"dc:contributor\": {\"type\": {\"minOccurs\": 1, \"maxOccurs\": 1, \"attributes\": [{\"ref\": \"xml:lang\", \"name\": \"xml:lang\", \"use\": \"optional\"}]}}, \"dc:date\": {\"type\": {\"minOccurs\": 1, \"maxOccurs\": 1, \"attributes\": [{\"ref\": \"xml:lang\", \"name\": \"xml:lang\", \"use\": \"optional\"}]}}, \"dc:type\": {\"type\": {\"minOccurs\": 1, \"maxOccurs\": 1, \"attributes\": [{\"ref\": \"xml:lang\", \"name\": \"xml:lang\", \"use\": \"optional\"}]}}, \"dc:format\": {\"type\": {\"minOccurs\": 1, \"maxOccurs\": 1, \"attributes\": [{\"ref\": \"xml:lang\", \"name\": \"xml:lang\", \"use\": \"optional\"}]}}, \"dc:identifier\": {\"type\": {\"minOccurs\": 1, \"maxOccurs\": 1, \"attributes\": [{\"ref\": \"xml:lang\", \"name\": \"xml:lang\", \"use\": \"optional\"}]}}, \"dc:source\": {\"type\": {\"minOccurs\": 1, \"maxOccurs\": 1, \"attributes\": [{\"ref\": \"xml:lang\", \"name\": \"xml:lang\", \"use\": \"optional\"}]}}, \"dc:language\": {\"type\": {\"minOccurs\": 1, \"maxOccurs\": 1, \"attributes\": [{\"ref\": \"xml:lang\", \"name\": \"xml:lang\", \"use\": \"optional\"}]}}, \"dc:relation\": {\"type\": {\"minOccurs\": 1, \"maxOccurs\": 1, \"attributes\": [{\"ref\": \"xml:lang\", \"name\": \"xml:lang\", \"use\": \"optional\"}]}}, \"dc:coverage\": {\"type\": {\"minOccurs\": 1, \"maxOccurs\": 1, \"attributes\": [{\"ref\": \"xml:lang\", \"name\": \"xml:lang\", \"use\": \"optional\"}]}}, \"dc:rights\": {\"type\": {\"minOccurs\": 1, \"maxOccurs\": 1, \"attributes\": [{\"ref\": \"xml:lang\", \"name\": \"xml:lang\", \"use\": \"optional\"}]}}}",
        namespaces={"":"http://www.w3.org/2001/XMLSchema","dc":"http://purl.org/dc/elements/1.1/","xml":"http://www.w3.org/XML/1998/namespace","oai_dc":"http://www.openarchives.org/OAI/2.0/oai_dc/"},
        schema_location="http://www.openarchives.org/OAI/2.0/oai_dc/",
        isvalid=True,
        is_mapping=False,
        isfixed=False,
        version_id=1,
        target_namespace="oai_dc"
    )
    db.session.add(schema)
    db.session.commit()
    return schema


@pytest.fixture()
def db_itemtype1(app, db):
    item_type_name = ItemTypeName(
        id=1, name="テストアイテムタイプ1", has_site_license=True, is_active=True
    )
    item_type_schema = dict()
    with open("tests/data/item_types/itemtype_schema0.json", "r") as f:
        item_type_schema = json.load(f)

    item_type_form = dict()
    with open("tests/data/item_types/itemtype_form0.json", "r") as f:
        item_type_form = json.load(f)

    item_type_render = dict()
    with open("tests/data/item_types/itemtype_render0.json", "r") as f:
        item_type_render = json.load(f)

    item_type_mapping = dict()
    with open("tests/data/item_types/itemtype_mapping0.json", "r") as f:
        item_type_mapping = json.load(f)

    item_type = ItemType(
        id=1,
        name_id=1,
        harvesting_type=True,
        schema=item_type_schema,
        form=item_type_form,
        render=item_type_render,
        tag=1,
        version_id=1,
        is_deleted=False,
    )

    item_type_mapping = ItemTypeMapping(id=1, item_type_id=1, mapping=item_type_mapping)

    with db.session.begin_nested():
        db.session.add(item_type_name)
        db.session.add(item_type)
        db.session.add(item_type_mapping)
    db.session.commit()
    return {
        "item_type_name": item_type_name,
        "item_type": item_type,
        "item_type_mapping": item_type_mapping,
    }



@pytest.fixture()
def db_itemtype2(app, db):
    item_type_name = ItemTypeName(
        id=2, name="テストアイテムタイプ2", has_site_license=True, is_active=True
    )
    item_type_schema = dict()
    with open("tests/data/item_types/itemtype1_schema.json", "r") as f:
        item_type_schema = json.load(f)

    item_type_form = dict()
    with open("tests/data/item_types/itemtype1_form.json", "r") as f:
        item_type_form = json.load(f)

    item_type_render = dict()
    with open("tests/data/item_types/itemtype1_render.json", "r") as f:
        item_type_render = json.load(f)

    item_type_mapping = dict()
    with open("tests/data/item_types/itemtype1_mapping.json", "r") as f:
        item_type_mapping = json.load(f)

    item_type = ItemType(
        id=2,
        name_id=2,
        harvesting_type=True,
        schema=item_type_schema,
        form=item_type_form,
        render=item_type_render,
        tag=1,
        version_id=1,
        is_deleted=False,
    )

    item_type_mapping = ItemTypeMapping(id=2, item_type_id=2, mapping=item_type_mapping)

    with db.session.begin_nested():
        db.session.add(item_type_name)
        db.session.add(item_type)
        db.session.add(item_type_mapping)

    return {
        "item_type_name": item_type_name,
        "item_type": item_type,
        "item_type_mapping": item_type_mapping,
    }




@pytest.fixture()
def db_itemtype2(app, db):
    item_type_name = ItemTypeName(
        id=3, name="テストアイテムタイプ3", has_site_license=True, is_active=True
    )
    item_type_schema = dict()
    with open("tests/data/item_types/itemtype2_schema.json", "r") as f:
        item_type_schema = json.load(f)

    item_type_form = dict()
    with open("tests/data/item_types/itemtype2_form.json", "r") as f:
        item_type_form = json.load(f)

    item_type_render = dict()
    with open("tests/data/item_types/itemtype2_render.json", "r") as f:
        item_type_render = json.load(f)

    item_type_mapping = dict()
    with open("tests/data/item_types/itemtype2_mapping.json", "r") as f:
        item_type_mapping = json.load(f)

    item_type = ItemType(
        id=3,
        name_id=3,
        harvesting_type=True,
        schema=item_type_schema,
        form=item_type_form,
        render=item_type_render,
        tag=1,
        version_id=1,
        is_deleted=False,
    )

    item_type_mapping = ItemTypeMapping(id=3, item_type_id=3, mapping=item_type_mapping)

    with db.session.begin_nested():
        db.session.add(item_type_name)
        db.session.add(item_type)
        db.session.add(item_type_mapping)

    return {
        "item_type_name": item_type_name,
        "item_type": item_type,
        "item_type_mapping": item_type_mapping,
    }



@pytest.fixture()
def db_itemtype1(app, db):
    item_type_name = ItemTypeName(
        id=4, name="テストアイテムタイプ4", has_site_license=True, is_active=True
    )
    item_type_schema = dict()
    with open("tests/data/item_types/itemtype3_schema.json", "r") as f:
        item_type_schema = json.load(f)

    item_type_form = dict()
    with open("tests/data/item_types/itemtype3_form.json", "r") as f:
        item_type_form = json.load(f)

    item_type_render = dict()
    with open("tests/data/item_types/itemtype3_render.json", "r") as f:
        item_type_render = json.load(f)

    item_type_mapping = dict()
    with open("tests/data/item_types/itemtype3_mapping.json", "r") as f:
        item_type_mapping = json.load(f)

    item_type = ItemType(
        id=4,
        name_id=4,
        harvesting_type=True,
        schema=item_type_schema,
        form=item_type_form,
        render=item_type_render,
        tag=1,
        version_id=1,
        is_deleted=False,
    )

    item_type_mapping = ItemTypeMapping(id=4, item_type_id=4, mapping=item_type_mapping)

    with db.session.begin_nested():
        db.session.add(item_type_name)
        db.session.add(item_type)
        db.session.add(item_type_mapping)

    return {
        "item_type_name": item_type_name,
        "item_type": item_type,
        "item_type_mapping": item_type_mapping,
    }


@pytest.fixture()
def db_itemtype5(app, db):
    item_type_name = ItemTypeName(
        id=5, name="テストアイテムタイプ5", has_site_license=True, is_active=True
    )
    item_type_schema = dict()
    with open("tests/data/item_types/itemtype4_schema.json", "r") as f:
        item_type_schema = json.load(f)

    item_type_form = dict()
    with open("tests/data/item_types/itemtype4_form.json", "r") as f:
        item_type_form = json.load(f)

    item_type_render = dict()
    with open("tests/data/item_types/itemtype4_render.json", "r") as f:
        item_type_render = json.load(f)

    item_type_mapping = dict()
    with open("tests/data/item_types/itemtype4_mapping.json", "r") as f:
        item_type_mapping = json.load(f)

    item_type = ItemType(
        id=5,
        name_id=5,
        harvesting_type=True,
        schema=item_type_schema,
        form=item_type_form,
        render=item_type_render,
        tag=1,
        version_id=1,
        is_deleted=False,
    )

    item_type_mapping = ItemTypeMapping(id=5, item_type_id=5, mapping=item_type_mapping)

    with db.session.begin_nested():
        db.session.add(item_type_name)
        db.session.add(item_type)
        db.session.add(item_type_mapping)

    return {
        "item_type_name": item_type_name,
        "item_type": item_type,
        "item_type_mapping": item_type_mapping,
    }




@pytest.fixture()
def db_itemtype6(app, db):
    item_type_name = ItemTypeName(
        id=6, name="テストアイテムタイプ6", has_site_license=True, is_active=True
    )
    item_type_schema = dict()
    with open("tests/data/item_types/itemtype5_schema.json", "r") as f:
        item_type_schema = json.load(f)

    item_type_form = dict()
    with open("tests/data/item_types/itemtype5_form.json", "r") as f:
        item_type_form = json.load(f)

    item_type_render = dict()
    with open("tests/data/item_types/itemtype5_render.json", "r") as f:
        item_type_render = json.load(f)

    item_type_mapping = dict()
    with open("tests/data/item_types/itemtype5_mapping.json", "r") as f:
        item_type_mapping = json.load(f)

    item_type = ItemType(
        id=6,
        name_id=6,
        harvesting_type=True,
        schema=item_type_schema,
        form=item_type_form,
        render=item_type_render,
        tag=1,
        version_id=1,
        is_deleted=False,
    )

    item_type_mapping = ItemTypeMapping(id=6, item_type_id=6, mapping=item_type_mapping)

    with db.session.begin_nested():
        db.session.add(item_type_name)
        db.session.add(item_type)
        db.session.add(item_type_mapping)

    return {
        "item_type_name": item_type_name,
        "item_type": item_type,
        "item_type_mapping": item_type_mapping,
    }


@pytest.fixture()
def rocrate_mapping(db, item_type):
    mapping = {'key1': 'value1'}
    rocrate_mapping1 = RocrateMapping(2, mapping)
    with db.session.begin_nested():
        db.session.add(rocrate_mapping1)
