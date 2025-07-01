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

"""Pytest for weko admin configuration."""

import os
import shutil
import tempfile
import uuid
import json
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
from invenio_accounts.utils import jwt_create_token
from invenio_indexer import InvenioIndexer
import pytest
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.minters import recid_minter
from invenio_records import Record
from invenio_oaiserver.minters import oaiid_minter

from flask import Flask
from flask_babelex import Babel
from flask_mail import Mail
from flask_menu import Menu
from flask.cli import ScriptInfo
from flask_celeryext import FlaskCeleryExt
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database
from simplekv.memory.redisstore import RedisStore

from invenio_accounts import InvenioAccounts
from invenio_accounts.models import User, Role
from invenio_accounts.testutils import create_test_user
from invenio_access.models import ActionUsers, ActionRoles
from invenio_access import InvenioAccess
from invenio_admin import InvenioAdmin
from invenio_cache import InvenioCache
from invenio_communities.models import Community
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.models import FileInstance, Location
from invenio_i18n import InvenioI18N
from invenio_mail.models import MailConfig
from invenio_oaiserver.ext import InvenioOAIServer
from invenio_oauth2server.models import Client, Token
from invenio_pidrelations import InvenioPIDRelations
from invenio_pidstore import InvenioPIDStore
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.ext import InvenioRecords
from invenio_records.models import RecordMetadata
from invenio_search import RecordsSearch,InvenioSearch,current_search_client

from weko_authors import WekoAuthors
from weko_authors.models import Authors
from weko_index_tree import WekoIndexTree
from weko_index_tree.models import Index, IndexStyle
from weko_items_ui.config import WEKO_ITEMS_UI_CRIS_LINKAGE_RESEARCHMAP_MERGE_MODE_DEFAULT
from weko_records_ui import WekoRecordsUI
from weko_records_ui.config import WEKO_PERMISSION_SUPER_ROLE_USER
from weko_records import WekoRecords
from weko_records.models import SiteLicenseInfo, SiteLicenseIpAddress,ItemType,ItemTypeName,ItemTypeJsonldMapping
from weko_redis.redis import RedisConnection
from weko_schema_ui import WekoSchemaUI
from weko_search_ui import WekoSearchUI
from weko_swordserver.models import SwordClientModel
from weko_theme import WekoTheme
from weko_workflow import WekoWorkflow
from weko_workflow.models import Action, ActionStatus,FlowDefine,FlowAction,WorkFlow,Activity,ActivityAction

from weko_admin import WekoAdmin
from weko_admin.models import SessionLifetime,SiteInfo,SearchManagement,\
        AdminLangSettings,ApiCertificate,StatisticTarget,StatisticUnit,\
        FeedbackMailSetting,FeedbackMailHistory,FeedbackMailFailed,AdminSettings,\
        FacetSearchSetting,BillingPermission,LogAnalysisRestrictedIpAddress,\
        LogAnalysisRestrictedCrawlerList,StatisticsEmail,RankingSettings, Identifier
from weko_admin.views import blueprint_api

from .helpers import json_data, create_record


@pytest.yield_fixture()
def instance_path():
    """Temporary instance path."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)

@pytest.fixture()
def cache_config():
    """Generate cache configuration."""
    CACHE_TYPE = os.environ.get("CACHE_TYPE", "simple")
    config = {"CACHE_TYPE": CACHE_TYPE}

    if CACHE_TYPE == "simple":
        pass
    elif CACHE_TYPE == "redis":
        config.update(
            CACHE_REDIS_URL=os.environ.get(
                "CACHE_REDIS_URL", "redis://localhost:6379/0"
            )
        )
    elif CACHE_TYPE == "memcached":
        config.update(
            CACHE_MEMCACHED_SERVERS=os.environ.get(
                "CACHE_MEMCACHED_SERVERS", "localhost:11211"
            ).split(",")
        )
    return config

@pytest.fixture()
def base_app(instance_path, cache_config,request ,search_class):
    """Flask application fixture."""
    os.environ['INVENIO_ELASTICSEARCH_HOST']='elasticsearch_test'
    app_ = Flask('test_weko_admin_app', instance_path=instance_path)
    app_.config.update(
        SERVER_NAME='test_server',
        ACCOUNTS_USE_CELERY=False,
        SECRET_KEY='SECRET_KEY',
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #      'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                          'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        #SEARCH_ELASTIC_HOSTS=os.environ.get(
        #    'SEARCH_ELASTIC_HOSTS', None),
        SEARCH_ELASTIC_HOSTS=os.environ.get("SEARCH_ELASTIC_HOSTS", "elasticsearch"),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        SQLALCHEMY_ECHO=False,
        TEST_USER_EMAIL='test_user@example.com',
        TEST_USER_PASSWORD='test_password',
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        GOOGLE_TRACKING_ID_USER="test_google_tracking_id",
        ADDTHIS_USER_ID="test_addthis_user_id",
        I18N_LANGUAGES=[("ja","Japanese"), ("en","English")],
        CACHE_REDIS_URL=os.environ.get("CACHE_REDIS_URL", "redis://redis:6379/0"),
        CACHE_REDIS_DB='0',
        CACHE_REDIS_HOST="redis",
        REDIS_PORT='6379',
        ACCOUNTS_SESSION_REDIS_DB_NO = 1,
        CACHE_TYPE="redis",
        SEARCH_UI_SEARCH_INDEX="test-weko",
        WEKO_AUTHORS_ES_INDEX_NAME="test_weko-authors",
        INDEXER_DEFAULT_INDEX="{}-weko-item-v1.0.0".format("test"),
        INDEXER_DEFAULT_DOCTYPE="item-v1.0.0",
        INDEXER_FILE_DOC_TYPE="content",
        THEME_SITEURL = 'https://localhost',
        CRAWLER_REDIS_DB=3,
        CRAWLER_REDIS_TTL=86400,
        WEKO_THEME_INSTANCE_DATA_DIR="data",
        SEARCH_INDEX_PREFIX="test-",
        INDEXER_DEFAULT_DOC_TYPE="item-v1.0.0",
        WEKO_PERMISSION_SUPER_ROLE_USER=WEKO_PERMISSION_SUPER_ROLE_USER,
        WEKO_ITEMS_UI_CRIS_LINKAGE_RESEARCHMAP_MERGE_MODE_DEFAULT=WEKO_ITEMS_UI_CRIS_LINKAGE_RESEARCHMAP_MERGE_MODE_DEFAULT
    )
    app_.testing = True
    app_.login_manager = dict(_login_disabled=True)
    Babel(app_)
    InvenioI18N(app_)
    InvenioDB(app_)
    Mail(app_)
    Menu(app_)
    InvenioDB(app_)
    InvenioAccounts(app_)
    InvenioAccess(app_)
    InvenioAdmin(app_)
    InvenioCache(app_)
    InvenioPIDRelations(app_)
    InvenioPIDStore(app_)
    InvenioFilesREST(app_)
    WekoWorkflow(app_)
    WekoAuthors(app_)
    WekoRecords(app_)
    WekoRecordsUI(app_)
    WekoIndexTree(app_)
    WekoTheme(app_)

    FlaskCeleryExt(app_)
    WekoSearchUI(app_)
    WekoSchemaUI(app_)
    #search = InvenioSearch(app_, client=MockEs())
    InvenioSearch(app_)
    #search.register_mappings(search_class.Meta.index, 'tests.mock_module.mappings')
    InvenioIndexer(app_)
    InvenioRecords(app_, client=MockEs())
    InvenioOAIServer(app_)
    yield app_


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""

    with base_app.app_context():
        yield base_app


@pytest.yield_fixture()
def db(app):
    # if not database_exists(str(db_.engine.url)) and \
    #         app.config['SQLALCHEMY_DATABASE_URI'] != 'sqlite://':
    #     create_database(db_.engine.url)
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()

@pytest.yield_fixture()
def i18n_app(app):
    with app.test_request_context(
        headers=[('Accept-Language','ja')]):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        yield app

def _database_setup(app, request):
    """Set up the database."""
    with app.app_context():
        if not database_exists(str(db.engine.url)):
            create_database(str(db.engine.url))
        db.create_all()

    def teardown():
        with app.app_context():
            if database_exists(str(db.engine.url)):
                drop_database(str(db.engine.url))
            # Delete sessions in kvsession store
            if hasattr(app, 'kvsession_store') and \
                    isinstance(app.kvsession_store, RedisStore):
                app.kvsession_store.redis.flushall()

    request.addfinalizer(teardown)
    return a

@pytest.yield_fixture()
def api(app):
    app.register_blueprint(blueprint_api, url_prefix='/api/admin')
    with app.test_client() as client:
        yield client

@pytest.yield_fixture()
def client(app):
    """Get test client."""
    WekoAdmin(app)
    with app.test_client() as client:
        yield client

@pytest.yield_fixture()
def admin_app(instance_path):
    base_app = Flask(__name__, instance_path=instance_path)
    base_app.config.update(
        SECRET_KEY='SECRET KEY',
        SESSION_TYPE='memcached',
        SERVER_NAME='test_server',
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                          'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        WEKO_ADMIN_FACET_SEARCH_SETTING={"name_en": "","name_jp": "","mapping": "","active": True,"aggregations": [],"display_number": 5,"is_open": True,"search_condition": "OR","ui_type": "CheckboxList"},
        WEKO_ADMIN_FACET_SEARCH_SETTING_TEMPLATE="weko_admin/admin/facet_search_setting.html"
    )
    base_app.testing = True
    InvenioDB(base_app)
    InvenioAccounts(base_app)
    InvenioAccess(base_app)

    with base_app.app_context():
        yield base_app

@pytest.yield_fixture()
def admin_db(admin_app):
    if not database_exists(str(db_.engine.url)):
                create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()


@pytest.fixture()
def esindex(app):
    current_search_client.indices.delete(index="test-*")
    with open("tests/data/item-v1.0.0.json","r") as f:
        mapping = json.load(f)

    try:
        current_search_client.indices.create(
            app.config["INDEXER_DEFAULT_INDEX"], body=mapping
        )
        current_search_client.indices.put_alias(
            index=app.config["INDEXER_DEFAULT_INDEX"], name="test-weko"
        )
    except:
        current_search_client.indices.create("test-weko-items", body=mapping)
        current_search_client.indices.put_alias(
            index="test-weko-items", name="test-weko"
        )

    try:
        yield current_search_client
    finally:
        current_search_client.indices.delete(index="test-*")

@pytest.fixture
def script_info(app):
    return ScriptInfo(create_app=lambda info: app)

@pytest.fixture
def redis_connect(app):
    redis_connection = RedisConnection().connection(db=app.config['CACHE_REDIS_DB'], kv = True)
    return redis_connection

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

@pytest.fixture()
def session_lifetime(db):
    lifetime = SessionLifetime(lifetime=100)
    db.session.add(lifetime)
    db.session.commit()
    return lifetime

@pytest.fixture()
def site_info(db):
    siteinfos = list()
    siteinfo1 = SiteInfo(
        copy_right="test_copy_right1",
        description="test site info1.",
        keyword="test keyword1",
        favicon="test,favicon1",
        favicon_name="test favicon name1",
        site_name=[{"name":"name11"}],
        notify={"name":"notify11"},
        google_tracking_id_user="11",
        ogp_image="/var/tmp/test_dir",
        ogp_image_name="test ogp image name1"
    )
    db.session.add(siteinfo1)

    siteinfos.append(siteinfo1)
    siteinfo2 = SiteInfo(
        copy_right="test_copy_right2",
        description="test site info2.",
        keyword="test keyword2",
        favicon="test favicon2",
        favicon_name="test favicon name2",
        site_name={"name":"name21"},
        notify={"name":"notify21"},
    )
    siteinfos.append(siteinfo2)
    db.session.commit()
    return siteinfos

@pytest.fixture()
def file_instance(db):
    file = FileInstance(
        uri="/var/tmp/test_dir",
        storage_class="S",
        size=18,
    )
    db.session.add(file)
    db.session.commit()

@pytest.fixture()
def site_license(db):
    license=dict()
    result = SiteLicenseInfo(
        organization_id=0,
        organization_name="test data",
        receive_mail_flag="T",
        mail_address="test@mail.com",
        domain_name="test_domain",
    )
    db.session.add(result)
    addr1 = SiteLicenseIpAddress(
        organization_id=0,
        organization_no=0,
        start_ip_address="123.456.789.012",
        finish_ip_address="987.654.321.098"
    )
    #addr2 = SiteLicenseIpAddress(
    #    organization_id=0,
    #    start_ip_address="567.890.123.456",
    #    finish_ip_address="543.210.987.654"
    #)
    db.session.add(addr1)
    #db.session.add(addr2)
    license["Info"]=result
    #license["address"] = [addr1,addr2]
    license["address"] = [addr1]
    db.session.commit()
    yield [license]

@pytest.fixture()
def item_type(db):
    item_type_name1 = ItemTypeName(name='テストアイテムタイプ1',
                                  has_site_license=True,
                                  is_active=True)
    item_type_name2 = ItemTypeName(name='テストアイテムタイプ2',
                                  has_site_license=False,
                                  is_active=True)
    with db.session.begin_nested():
        db.session.add(item_type_name1)
        db.session.add(item_type_name2)
    item_type1 = ItemType(name_id=1,harvesting_type=True,
                     schema={},
                     form={},
                     render={},
                     tag=1,version_id=1,is_deleted=False)
    item_type2 = ItemType(name_id=2,harvesting_type=True,
                     schema={},
                     form={},
                     render={},
                     tag=1,version_id=1,is_deleted=False)
    with db.session.begin_nested():
        db.session.add(item_type1)
        db.session.add(item_type2)

    return [{"obj":item_type1,"name":item_type_name1},{"obj":item_type2,"name":item_type_name2}]

@pytest.fixture()
def search_management(db):
    searchmanagement = SearchManagement(
        default_dis_num=20,
        default_dis_sort_index="controlnumber_asc",
        default_dis_sort_keyword="createdate_desc",
        sort_setting={},
        search_conditions={},
        search_setting_all={},
        display_control={"display_community":{"id":"display_community","status":True},"display_index_tree":{"id":"display_index_tree","status":True},"display_facet_search":{"id":"display_facet_search","status":True}},
        init_disp_setting={"init_disp_index":"","init_disp_screen_setting":"0","init_disp_index_disp_method":"0"}
    )
    db.session.add(searchmanagement)
    db.session.commit()
    return searchmanagement

@pytest.fixture()
def language_setting(db):
    en = AdminLangSettings(
        lang_code="en",
        lang_name="English",
        is_registered=True,
        sequence=1,
        is_active=True
    )
    zh = AdminLangSettings(
        lang_code="zh",
        lang_name="中文",
        is_registered=False,
        sequence=0,
        is_active=False
    )
    ja = AdminLangSettings(
        lang_code="ja",
        lang_name="日本語",
        is_registered=True,
        sequence=2,
        is_active=True
    )
    db.session.add(en)
    db.session.add(zh)
    db.session.add(ja)
    db.session.commit()
    return {"en":en,"zh":zh,"ja":ja}

@pytest.fixture()
def api_certificate(db):
    api = ApiCertificate(
        api_code="crf",
        api_name="CrossRef",
        cert_data="test.test@test.org"
    )
    db.session.add(api)
    db.session.commit()
    return api

@pytest.fixture()
def statistic_target(db):
    targets = list()
    targets.append(StatisticTarget(
        target_id="1",
        target_name="Item registration report",
        target_unit="1,2,3,5"
    ))
    targets.append(StatisticTarget(
        target_id="2",
        target_name="Item detail view report",
        target_unit="1,2,3,4,5"
    ))
    targets.append(StatisticTarget(
        target_id="3",
        target_name="Contents download report",
        target_unit="1,2,3,5"
    ))
    db.session.add_all(targets)
    db.session.commit()
    return targets

@pytest.fixture()
def statistic_unit(db):
    units = list()
    units.append(StatisticUnit(unit_id="1",unit_name="Day"))
    units.append(StatisticUnit(unit_id="2",unit_name="Week"))
    units.append(StatisticUnit(unit_id="3",unit_name="Year"))
    units.append(StatisticUnit(unit_id="4",unit_name="Item"))
    units.append(StatisticUnit(unit_id="5",unit_name="Host"))
    db.session.add_all(units)
    db.session.commit()
    return units

@pytest.fixture()
def location(app, db, instance_path):
    with db.session.begin_nested():
        Location.query.delete()
        loc = Location(name='local', uri=instance_path, default=True)
        db.session.add(loc)
    db.session.commit()
    return loc

@pytest.fixture()
def records(db,location):
    record_data = json_data("data/test_records.json")
    item_data = json_data("data/test_items.json")

    record_num = len(record_data)
    result = []
    for d in range(record_num):
        result.append(create_record(record_data[d], item_data[d]))
        db.session.commit()

    yield result

@pytest.fixture()
def authors(db):
    authors_data = json_data("data/test_authors.json")
    author_list = []
    for data in authors_data:
        author_list.append(Authors(json=data))
    db.session.add_all(author_list)
    db.session.commit()
    return author_list

@pytest.fixture()
def feedback_mail_settings(db,authors):
    setting = FeedbackMailSetting(
        account_author="{},{},".format(authors[0].id,authors[1].id),
        manual_mail={"email":["test.manual1@test.org","test.manual2@test.org"]},
        is_sending_feedback=True,
        root_url="http://test_server",
        repository_id="Root Index"
    )
    db.session.add(setting)
    db.session.commit()
    setting_not_manual = FeedbackMailSetting(
        account_author="{}".format(authors[1].id),
        manual_mail={"email":[]},
        is_sending_feedback=True,
        root_url="http://test_server",
        repository_id="Root Index"
    )
    return [setting, setting_not_manual]

@pytest.fixture()
def site_infos(db):
    site_info = SiteInfo(
        copy_right="test_copy_right",
        description="this is test description.",
        keyword="test_keyword",
        favicon="/static/favicon.ico",
        favicon_name="JAIRO Cloud icon",
        site_name=[{"name":"test_site","index":"0","language":"en"},{"name":"テスト サイト","index":"1","language":"ja"}],
        notify=[{"language":"en","notify_name":""}],
        google_tracking_id_user="test_tracking_id",
        addthis_user_id="ra-5d8af23e9a3a2633",
        ogp_image=None,
        ogp_image_name=None
    )
    db.session.add(site_info)
    db.session.commit()
    return site_info

@pytest.fixture()
def feedback_mail_histories(db):

    history1 = FeedbackMailHistory(
        start_time=datetime(2022,10,1,1,2,3,45678),
        end_time=datetime(2022,10,1,2,3,4,56789),
        stats_time="2022-10",
        count=2,
        error=0,
        is_latest=True
    )
    db.session.add(history1)

    history2 = FeedbackMailHistory(
        start_time=datetime(2022,10,1,1,2,3,45678),
        end_time=datetime(2022,10,1,2,3,4,56789),
        stats_time="2022-11",
        count=2,
        error=0,
        is_latest=True
    )
    db.session.add(history2)
    db.session.commit()
    return [history1, history2]

@pytest.fixture()
def feedback_mail_faileds(db, feedback_mail_histories, authors):
    failed1 = FeedbackMailFailed(
        history_id=feedback_mail_histories[0].id,
        author_id=authors[0].id,
        mail="test.test1@test.org"
    )
    db.session.add(failed1)

    db.session.commit()
    return [failed1]

@pytest.fixture()
def indexes(db):
    index_data = json_data("data/indexes.json")
    index_db = list()
    for data in index_data:
        index_db.append(Index(**data))
    db.session.add_all(index_db)
    db.session.commit()
    return index_db

@pytest.fixture()
def index_style(db):
    style = IndexStyle(
        id="weko",
        width="3",
        index_link_enabled=False
    )
    db.session.add(style)
    db.session.commit()
    return style

@pytest.fixture()
def admin_settings(db):
    settings = list()
    settings.append(AdminSettings(id=1,name='items_display_settings',settings={"items_display_email": False, "items_search_author": "name", "item_display_open_date": False}))
    settings.append(AdminSettings(id=2,name='storage_check_settings',settings={"day": 0, "cycle": "weekly", "threshold_rate": 80}))
    settings.append(AdminSettings(id=3,name='site_license_mail_settings',settings={"Root Index": {"auto_send_flag": False}}))
    settings.append(AdminSettings(id=4,name='default_properties_settings',settings={"show_flag": True}))
    settings.append(AdminSettings(id=5,name='item_export_settings',settings={"allow_item_exporting": True, "enable_contents_exporting": True}))
    settings.append(AdminSettings(id=6,name="restricted_access",settings={"content_file_download": {"expiration_date": 30,"expiration_date_unlimited_chk": False,"download_limit": 10,"download_limit_unlimited_chk": False,},"usage_report_workflow_access": {"expiration_date_access": 500,"expiration_date_access_unlimited_chk": False,},"terms_and_conditions": []}))
    settings.append(AdminSettings(id=7,name="display_stats_settings",settings={"display_stats":False}))
    settings.append(AdminSettings(id=8,name='convert_pdf_settings',settings={"path":"/tmp/file","pdf_ttl":1800}))
    settings.append(AdminSettings(id=9,name="elastic_reindex_settings",settings={"has_errored": False}))
    settings.append(AdminSettings(id=10,name="sword_api_setting",settings={ "default_format": "TSV","data_format":{ "TSV":{"register_format": "Direct"},"XML":{"workflow": '31001',  "register_format": "Workflow"}}}))
    settings.append(AdminSettings(id=11,name="report_email_schedule_settings",settings={"details":"","enabled":False,"frequency":"daily"}))
    settings.append(AdminSettings(id=12,name="cris_linkage",settings={'researchmap_cidkey_contents':'','researchmap_pkey_contents':'','merge_mode':''}))
    db.session.add_all(settings)
    db.session.commit()
    return settings

@pytest.fixture()
def oauth2server_client(db):
    oauth2server_clients = list()
    oauth2server_clients.append(Client(name=1,description=1,website=1,user_id=1,client_id="1",client_secret="KDjy6ntGKUX",is_confidential=True,is_internal=False,_redirect_uris="https://" ,_default_scopes="NULL"))
    oauth2server_clients.append(Client(name=2,description=2,website=2,user_id=2,client_id="2",client_secret="KDjy6ntGKUX",is_confidential=True,is_internal=False,_redirect_uris="https://" ,_default_scopes="NULL"))

@pytest.fixture()
def sword_item_type_mappings(db, item_type):
    sword_item_type_mappings = list()
    sword_item_type_mappings.append(ItemTypeJsonldMapping(id=1,name="sample1",mapping="{data:{}}",item_type_id=item_type[0]["obj"].id,version_id=6,is_deleted=False))
    sword_item_type_mappings.append(ItemTypeJsonldMapping(id=2,name="sample2",mapping="{data:{}}",item_type_id=item_type[0]["obj"].id,version_id=6,is_deleted=False))
    db.session.add_all(sword_item_type_mappings)
    db.session.commit()
    return sword_item_type_mappings

@pytest.fixture()
def actions(db):
    action_datas = json_data("data/actions.json")
    action_db = list()
    for data in action_datas:
        action_db.append(Action(**data))
    db.session.add_all(action_db)

    status_datas = json_data("data/action_status.json")
    status_db = list()
    for data in status_datas:
        status_db.append(ActionStatus(**data))
    db.session.add_all(status_db)

    db.session.commit()

    return action_db, status_db

@pytest.fixture()
def flows(db,item_type,actions,users):
    flow_define = FlowDefine(flow_id=uuid.uuid4(),
                             flow_name='Registration Flow',
                             flow_user=1)
    db.session.add(flow_define)
    db.session.commit()
    flow_action1 = FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=1,
                     action_version='1.0.0',
                     action_order=1,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={})
    flow_action2 = FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=3,
                     action_version='1.0.0',
                     action_order=2,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={})
    flow_action3 = FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=5,
                     action_version='1.0.0',
                     action_order=3,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={})
    db.session.add(flow_action1)
    db.session.add(flow_action2)
    db.session.add(flow_action3)
    db.session.commit()

    workflow = WorkFlow(flows_id=uuid.uuid4(),
                        flows_name='test workflow1',
                        itemtype_id=item_type[0]["obj"].id,
                        index_tree_id=None,
                        flow_id=flow_define.id,
                        is_deleted=False,
                        open_restricted=False,
                        location_id=None,
                        is_gakuninrdm=False)
    db.session.add(workflow)
    workflow_31001 = WorkFlow(id=31001,flows_id=uuid.uuid4(),
                    flows_name='test workflow31001',
                    itemtype_id=item_type[0]["obj"].id,
                    index_tree_id=None,
                    flow_id=flow_define.id,
                    is_deleted=False,
                    open_restricted=False,
                    location_id=None,
                    is_gakuninrdm=False)
    db.session.add(workflow_31001)
    db.session.commit()
    return {"flow":flow_define,"flow_actions":[flow_action1,flow_action2,flow_action3],"workflow":[workflow, workflow_31001]}

@pytest.fixture()
def activities(db,flows,records,users):
    activity_item1 = Activity(activity_id='1',item_id=records[0][2].id,workflow_id=flows["workflow"][0].id, flow_id=flows["flow"].id,
                    action_id=1, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item1', shared_user_id=-1, extra_info={},
                    action_order=1,
                    )
    db.session.add(activity_item1)
    activity_31001 = Activity(activity_id='31001',workflow_id=flows["workflow"][1].id, flow_id=flows["flow"].id,
                    action_id=1, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item31001', shared_user_id=-1, extra_info={},
                    action_order=1,
                    )
    db.session.add(activity_31001)
    activity_item_guest = Activity(activity_id='2',item_id=records[0][2].id,workflow_id=flows["workflow"][0].id, flow_id=flows["flow"].id,
                    action_id=1, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item1', shared_user_id=-1, extra_info={"is_guest":True,"guest_mail":"test.guest@test.org","file_name":"test_file"},
                    action_order=1,
                    )

    db.session.add(activity_item_guest)
    activity_usage = Activity(activity_id='3',item_id=records[0][2].id,workflow_id=flows["workflow"][0].id, flow_id=flows["flow"].id,
                    action_id=1, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item1', shared_user_id=-1,
                    extra_info={"usage_activity_id":"3","usage_application_record_data":{"subitem_restricted_access_name":"test_access_name",}},
                    action_order=1,
                    )
    db.session.add(activity_usage)
    db.session.commit()
    activity_action1_1 = ActivityAction(activity_id=activity_item1.activity_id,
                                            action_id=1,action_status="M",
                                            action_handler=1, action_order=1)
    activity_action1_2 = ActivityAction(activity_id=activity_item1.activity_id,
                                            action_id=3,action_status="M",
                                            action_handler=1, action_order=2)
    activity_action1_3 = ActivityAction(activity_id=activity_item1.activity_id,
                                            action_id=5,action_status="M",
                                            action_handler=1, action_order=3)
    db.session.add(activity_action1_1)
    db.session.add(activity_action1_2)
    db.session.add(activity_action1_3)

    db.session.commit()

    return [activity_item1, activity_31001, activity_item_guest, activity_usage]

@pytest.fixture()
def facet_search_settings(db):
    language = FacetSearchSetting(
        name_en="Data Language",
        name_jp="データの言語",
        mapping="language",
        aggregations=[],
        active=True,
        ui_type='SelectBox',
        display_number="1",
        is_open=True,
        search_condition='OR'

    )
    access = FacetSearchSetting(
        name_en="Access",
        name_jp="アクセス制限",
        mapping="accessRights",
        aggregations=[],
        active=False,
        ui_type='CheckboxList',
        display_number="1",
        is_open=True,
        search_condition='AND'
    )
    data_type = FacetSearchSetting(
        name_en="Data Type",
        name_jp="データタイプ",
        mapping="description.value",
        aggregations=[{"agg_value":"Other","agg_mapping":"description.descriptionType"}],
        active=True,
        ui_type='CheckboxList',
        display_number="1",
        is_open=True,
        search_condition='AND'
    )

    fields_raw = FacetSearchSetting(
        name_en="raw_test",
        name_jp="raw_test",
        mapping="fields.raw",
        aggregations=[],
        active=True,
        ui_type='CheckboxList',
        display_number="1",
        is_open=True,
        search_condition='AND'
    )

    temporal = FacetSearchSetting(
        name_en="Time Period(s)",
        name_jp="対象時期",
        mapping="temporal",
        aggregations=[],
        active=True,
        ui_type='RangeSlider',
        display_number="1",
        is_open=True,
        search_condition='AND'
    )
    db.session.add(language)
    db.session.add(access)
    db.session.add(data_type)
    db.session.add(fields_raw)
    db.session.add(temporal)
    db.session.commit()

@pytest.fixture()
def billing_permissions(db):
    permission1 = BillingPermission(
        user_id=1,
        is_active=True
    )
    db.session.add(permission1)
    permission2 = BillingPermission(
        user_id=2,
        is_active=False
    )
    db.session.add(permission2)
    db.session.commit()
    return [permission1,permission2]

@pytest.fixture()
def log_crawler_list(db):
    crawler1 = LogAnalysisRestrictedCrawlerList(
        list_url="https://bitbucket.org/niijp/jairo-crawler-list/raw/master/test_Crawler-List_ip_blacklist.txt",
        is_active=True
    )
    crawler2 = LogAnalysisRestrictedCrawlerList(
        list_url="https://bitbucket.org/niijp/jairo-crawler-list/raw/master/test_Crawler-List_useragent.txt",
        is_active=True
    )

    db.session.add(crawler1)
    db.session.add(crawler2)
    db.session.commit()
    return [crawler1,crawler2]

@pytest.fixture()
def restricted_ip_addr(db):
    ip_addr1 = LogAnalysisRestrictedIpAddress(
        ip_address="123.456.789.012"
    )
    db.session.add(ip_addr1)
    db.session.commit()
    return [ip_addr1]

@pytest.fixture()
def statistic_email_addrs(db):
    addr1 = StatisticsEmail(
        email_address="test.taro@test.org"
    )
    db.session.add(addr1)
    db.session.commit()
    return [addr1]

@pytest.fixture()
def ranking_settings(db):
    ranking = RankingSettings(
        id=0,
        is_show=True,
        new_item_period=14,
        statistical_period=365,
        display_rank=10,
        rankings={"new_items":True,"most_reviewed_items":True,"most_downloaded_items":True,"most_searched_keywords":True,"created_most_items_user":True}
    )
    db.session.add(ranking)
    db.session.commit()
    return ranking

@pytest.fixture()
def mail_config(db):
    config = MailConfig(
        id=1,
        mail_server="test_server",
        mail_port=25,
        mail_use_tls=False,
        mail_use_ssl=False,
        mail_default_sender="test_sender"
    )
    db.session.add(config)
    db.session.commit()

    return config

@pytest.fixture()
def identifier(db):
    iden = Identifier(
        repository="Root Index",
        jalc_flag=True,
        jalc_crossref_flag=True,
        jalc_datacite_flag=True,
        ndl_jalc_flag=True,
        jalc_doi="1234",
        jalc_crossref_doi="2345",
        jalc_datacite_doi="3456",
        ndl_jalc_doi="4567",
        suffix="test_suffix",
        created_userId="1",
        created_date=datetime(2022,12,1,11,22,33,4444),
        updated_userId="1",
        updated_date=datetime(2022,12,10,11,22,33,4444),
    )
    db.session.add(iden)
    db.session.commit()
    return iden

@pytest.yield_fixture()
def i18n_app(app):
    with app.test_request_context(headers=[("Accept-Language", "ja")]):
        app.extensions["invenio-oauth2server"] = 1
        app.extensions["invenio-queues"] = 1
        yield app

@pytest.yield_fixture(scope='session')
def search_class():
    """Search class."""
    yield TestSearch
class MockEs():
    def __init__(self,**keywargs):
        self.indices = self.MockIndices()
        self.es = Elasticsearch()
        self.cluster = self.MockCluster()
    def index(self, id="",version="",version_type="",index="",doc_type="",body="",**arguments):
        return {"_shards":{"failed":0} }
    # def delete(self,id="",index="",doc_type="",**kwargs):
    #     return Response(response=json.dumps({}),status=500)
    def search(self,index="",doc_type="",body={},**kwargs):
        return {"took":2,"timed_out":False,"_shards":{"total":1,"successful":1,"skipped":0,"failed":0},"hits":{"total":67,"max_score":1,"hits":[{"_index":"test-weko-item-v1.0.0","_type":"item-v1.0.0","_id":"oaiset-1669370353014","_score":1,"_source":{"query":{"query_string":{"query":"path:\"1669370353014\""}}}}]}}

    @property
    def transport(self):
        return self.es.transport
    class MockIndices():
        def __init__(self,**keywargs):
            self.mapping = dict()
        # def delete(self,index="", ignore=""):
        #     pass
        # def delete_template(self,index=""):
        #     pass
        # def create(self,index="",body={},ignore=""):
        #     self.mapping[index] = body
        # def put_alias(self,index="", name="", ignore=""):
        #     pass
        # def put_template(self,name="", body={}, ignore=""):
        #     pass
        # def refresh(self,index=""):
        #     pass
        # def exists(self, index="", **kwargs):
        #     if index in self.mapping:
        #         return True
        #     else:
        #         return False
        # def flush(self,index="",wait_if_ongoing=""):
        #     pass
        # def delete_alias(self, index="", name="",ignore=""):
        #     pass
        # def search(self,index="",doc_type="",body={},**kwargs):
        #     pass
        def put_mapping(self,index="",doc_type="", body={}, ignore=""):
            pass

    class MockCluster():
        def __init__(self,**kwargs):
            pass
        # def health(self, wait_for_status="", request_timeout=0):
        #     pass
class TestSearch(RecordsSearch):
    """Test record search."""

    class Meta:
        """Test configuration."""

        index = "test"
        doc_types = "item-v1.0.0"

    def __init__(self, **kwargs):
        """Add extra options."""
        super(TestSearch, self).__init__(**kwargs)
        self._extra.update(**{'_source': {'excludes': ['_access']}})

@pytest.fixture()
def reindex_settings(i18n_app):
    record0 = _create_record(i18n_app, {
        '_oai': {'sets': ['1669370353014']}, 'title_statement': {'title': 'Test0'},
        '$schema': {"test-weko-item-v1.0.0": "https://127.0.0.1/schema/deposits/deposit-v1.0.0.json"}
    })
    record1 = _create_record(i18n_app, {
        '_oai': {'sets': ['1669959650594']}, 'title_statement': {'title': 'Test0'},
        '$schema': {"test-weko-item-v1.0.0": "https://127.0.0.1/schema/deposits/deposit-v1.0.0.json"}
    })
    settings = list()
    settings.append(PersistentIdentifier(object_uuid=record0.id,pid_type="oai",pid_value="oai:weko3.example.org:00000001",status="R",object_type="rec"))
    settings.append(PersistentIdentifier(object_uuid=record1.id,pid_type="oai",pid_value="oai:weko3.example.org:00000002",status="R",object_type="rec"))
    settings.append(RecordMetadata(id="{069a5c8b-b3df-4909-98a2-713527c8db50}",json={"_oai": {"id": "oai:weko3.example.org:00000005.1", "sets": []}, "path": ["1669370353013"], "owner": "1", "recid": "5.1", "title": ["タイトル"], "pubdate": {"attribute_name": "PubDate", "attribute_value": "2022-11-30"}, "_buckets": {"deposit": "07beac8f-6518-4894-923b-4160d3ab4c24"}, "_deposit": {"id": "5.1", "pid": {"type": "depid", "value": "5.1", "revision_id": 0}, "owner": "1", "owners": [1], "status": "published", "created_by": 1}, "item_title": "タイトル", "author_link": [], "item_type_id": "40002", "publish_date": "2022-11-30", "publish_status": "0", "weko_shared_id": -1, "item_1617186331708": {"attribute_name": "Title", "attribute_value_mlt": [{"subitem_1551255647225": "タイトル", "subitem_1551255648112": "ja"}]}, "item_1617258105262": {"attribute_name": "Resource Type", "attribute_value_mlt": [{"resourceuri": "http://purl.org/coar/resource_type/c_beb9", "resourcetype": "data paper"}]}, "item_1669786983830": {"attribute_name": "new_changed", "attribute_value_mlt": [{"subitem_1669370027424": [{"subitem_1669370032950": "new_text", "subitem_1669370036614": "new_text"}], "subitem_1669370028622": "2022-10-31"}]}, "relation_version_is_last": True},version_id=1))
    settings.append(RecordMetadata(id="{06a3949a-44eb-477f-91bd-a2e8fe018e22}",json={"_oai": {"id": "oai:weko3.example.org:00000016.1", "sets": []}, "path": ["1669370353013"], "owner": "1", "recid": "16.1", "title": ["タイトル"], "pubdate": {"attribute_name": "PubDate", "attribute_value": "2022-12-02"}, "_buckets": {"deposit": "bc52eca2-fab8-4de5-b54a-d6991cf27f8f"}, "_deposit": {"id": "16.1", "pid": {"type": "depid", "value": "16.1", "revision_id": 0}, "owner": "1", "owners": [1], "status": "published", "created_by": 1}, "item_title": "タイトル", "author_link": [], "item_type_id": "40004", "publish_date": "2022-12-02", "publish_status": "0", "weko_shared_id": -1, "item_1617186331708": {"attribute_name": "Title", "attribute_value_mlt": [{"subitem_1551255647225": "タイトル", "subitem_1551255648112": "ja"}]}, "item_1617258105262": {"attribute_name": "Resource Type", "attribute_value_mlt": [{"resourceuri": "http://purl.org/coar/resource_type/c_6501", "resourcetype": "journal article"}]}, "item_1669942968526": {"attribute_name": "", "attribute_value_mlt": [{"subitem_1669942715232": "a"}]}, "item_1669942969646": {"attribute_name": "", "attribute_value_mlt": [{"subitem_1669942715232": "a"}]}, "item_1669942970526": {"attribute_name": "", "attribute_value_mlt": [{"subitem_1669940015843": ["a"]}]}, "item_1669942972286": {"attribute_name": "", "attribute_value_mlt": [{"subitem_1669942715232": "a"}]}, "item_1669943008966": {"attribute_name": "", "attribute_value_mlt": [{"subitem_1669942715232": "2022-12-02"}]}, "item_1669943105542": {"attribute_name": "", "attribute_value_mlt": [{"subitem_1669943076184": "a"}]}, "item_1669943517557": {"attribute_name": "", "attribute_value_mlt": [{"subitem_1669941342567": [{"subitem_1669942576264": "a", "subitem_1669942583842": "a", "subitem_1669942586009": ["a"], "subitem_1669942602505": "a"}]}]}, "relation_version_is_last": True},version_id=1))
    db_.session.add_all(settings)
    db_.session.commit()
    return db_

def _create_record(app, item_dict, mint_oaiid=True):
    """Create test record."""
    indexer = RecordIndexer()
    with app.test_request_context():
        record_id = uuid.uuid4()
        recid = recid_minter(record_id, item_dict)
        if mint_oaiid:
            oaiid_minter(record_id, item_dict)
        record = Record.create(item_dict, id_=record_id)
        indexer.index(record)
        return record


def facet_search_setting(db):
    datas = json_data("data/facet_search_setting.json")
    settings = list()

    for setting in datas:
        settings.append(FacetSearchSetting(**datas[setting]))
    with db.session.begin_nested():
        db.session.add_all(settings)

@pytest.fixture()
def community(db, users, indexes):
    user1 = users[2]["obj"]
    index = indexes[0]
    db.session.commit()
    comm1 = Community.create(community_id='comm1', role_id=user1.roles[0].id,
                             id_user=user1.id, title='Title1',
                             description='Description1',
                             root_node_id=index.id,
                             group_id=user1.roles[0].id)
    db.session.add(comm1)
    db.session.commit()
    return comm1

@pytest.fixture
def tokens(app,users,db):
    scopes = [
        "deposit:write deposit:actions item:create",
        "deposit:write deposit:actions item:create user:activity",
        "deposit:write user:activity",
        ""
    ]
    tokens = []

    for i, scope in enumerate(scopes):
        user = users[i]
        user_id = str(user["id"])

        test_client = Client(
            client_id=f"dev{user_id}",
            client_secret=f"dev{user_id}",
            name="Test name",
            description="test description",
            is_confidential=False,
            user_id=user_id,
            _default_scopes="deposit:write"
        )
        test_token = Token(
            client=test_client,
            user_id=user_id,
            token_type="bearer",
            access_token=jwt_create_token(user_id=user_id),
            expires=datetime.now() + timedelta(hours=10),
            is_personal=False,
            is_internal=False,
            _scopes=scope
        )

        db.session.add(test_client)
        db.session.add(test_token)
        tokens.append({"token":test_token, "client":test_client, "scope":scope})

    db.session.commit()

    return tokens


@pytest.fixture
def sword_mapping(db, item_type):
    sword_mapping = []
    for i in range(1, 4):
        obj = ItemTypeJsonldMapping(
            name=f"test{i}",
            mapping=json_data("data/ro-crate_mapping.json"),
            item_type_id=item_type[1]["obj"].id,
            is_deleted=False
        )
        with db.session.begin_nested():
            db.session.add(obj)

        sword_mapping.append({
            "id": obj.id,
            "sword_mapping": obj,
            "name": obj.name,
            "mapping": obj.mapping,
            "item_type_id": obj.item_type_id,
            "version_id": obj.version_id,
            "is_deleted": obj.is_deleted
        })

    db.session.commit()

    return sword_mapping

@pytest.fixture
def sword_client(db, tokens, sword_mapping, flows):
    client = tokens[0]["client"]
    sword_client1 = SwordClientModel(
        client_id=client.client_id,
        active=True,
        registration_type_id=SwordClientModel.RegistrationType.DIRECT,
        mapping_id=sword_mapping[0]["sword_mapping"].id,
        duplicate_check=False,
        meta_data_api=[],
    )
    client = tokens[1]["client"]
    sword_client2 = SwordClientModel(
        client_id=client.client_id,
        active=True,
        registration_type_id=SwordClientModel.RegistrationType.WORKFLOW,
        mapping_id=sword_mapping[1]["sword_mapping"].id,
        workflow_id=flows["workflow"][1].id,
        duplicate_check=True,
        meta_data_api=[],
    )
    client = tokens[2]["client"]
    sword_client3 = SwordClientModel(
        client_id=client.client_id,
        active=False,
        registration_type_id=SwordClientModel.RegistrationType.DIRECT,
        mapping_id=sword_mapping[0]["sword_mapping"].id,
        duplicate_check=False,
        meta_data_api=[],
    )

    with db.session.begin_nested():
        db.session.add(sword_client1)
        db.session.add(sword_client2)
        db.session.add(sword_client3)
    db.session.commit()

    return [
        {"sword_client": sword_client1},
        {"sword_client": sword_client2},
        {"sword_client": sword_client3}
    ]
