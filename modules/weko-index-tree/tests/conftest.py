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
from os.path import dirname, exists, join
import shutil
import tempfile
import json
import uuid
from datetime import date, datetime, timedelta
from kombu import Exchange, Queue

import pytest
from mock import Mock, patch
from flask import Flask
from flask_babelex import Babel, lazy_gettext as _
from flask_celeryext import FlaskCeleryExt
from flask_menu import Menu
from werkzeug.local import LocalProxy
from .helpers import create_record, json_data, fill_oauth2_headers

from invenio_deposit.config import (
    DEPOSIT_DEFAULT_STORAGE_CLASS,
    DEPOSIT_RECORDS_UI_ENDPOINTS,
    DEPOSIT_REST_ENDPOINTS,
    DEPOSIT_DEFAULT_JSONSCHEMA,
    DEPOSIT_JSONSCHEMAS_PREFIX,
)
from invenio_stats.contrib.event_builders import (
    build_file_unique_id,
    build_record_unique_id,
    file_download_event_builder
)
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import User, Role
from invenio_accounts.testutils import create_test_user, login_user_via_session
from invenio_access.models import ActionUsers
from invenio_access import InvenioAccess
from invenio_access.models import ActionUsers, ActionRoles
from invenio_assets import InvenioAssets
from invenio_cache import InvenioCache
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_files_rest.models import Location
from invenio_i18n import InvenioI18N
from invenio_indexer import InvenioIndexer
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_mail import InvenioMail
from invenio_oaiserver import InvenioOAIServer
from invenio_oaiserver.models import OAISet
from invenio_oauth2server import InvenioOAuth2Server, InvenioOAuth2ServerREST
from invenio_oauth2server.models import Client, Token
from invenio_pidrelations import InvenioPIDRelations
from invenio_records import InvenioRecords
from invenio_search import InvenioSearch
from sqlalchemy_utils.functions import create_database, database_exists, drop_database
from simplekv.memory.redisstore import RedisStore
from invenio_oaiharvester.models import HarvestSettings
from invenio_stats import InvenioStats
from invenio_admin import InvenioAdmin
from invenio_search import RecordsSearch
from invenio_pidstore import InvenioPIDStore, current_pidstore
from invenio_records_rest.utils import PIDConverter
from invenio_records.models import RecordMetadata
from invenio_deposit.api import Deposit
from invenio_communities.models import Community
from invenio_search import current_search_client, current_search
from invenio_queues.proxies import current_queues
from invenio_files_rest.permissions import bucket_listmultiparts_all, \
    bucket_read_all, bucket_read_versions_all, bucket_update_all, \
    location_update_all, multipart_delete_all, multipart_read_all, \
    object_delete_all, object_delete_version_all, object_read_all, \
    object_read_version_all
from invenio_files_rest.models import Bucket
from invenio_db.utils import drop_alembic_version_table

from weko_admin.models import AdminLangSettings
from weko_schema_ui.models import OAIServerSchema
from weko_index_tree.api import Indexes
from weko_accounts import WekoAccounts
from weko_logging.audit import WekoLoggingUserActivity
from weko_records.api import ItemTypes
from weko_records.models import ItemTypeName, ItemType
from weko_records_ui.models import PDFCoverPageSettings
from weko_records_ui.config import WEKO_PERMISSION_SUPER_ROLE_USER, WEKO_PERMISSION_ROLE_COMMUNITY, EMAIL_DISPLAY_FLG
from weko_groups import WekoGroups
from weko_workflow import WekoWorkflow
from weko_workflow.models import Activity, ActionStatus, Action, WorkFlow, FlowDefine, FlowAction
from weko_index_tree.models import Index
from weko_index_tree.views import blueprint_api
from weko_index_tree.rest import create_blueprint
from weko_index_tree.scopes import create_index_scope
from weko_search_ui import WekoSearchUI
from weko_redis.redis import RedisConnection
from weko_admin.models import SessionLifetime


@pytest.yield_fixture()
def instance_path():
    """Temporary instance path."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.fixture()
def base_app(instance_path):
    """Flask application fixture."""
    app_ = Flask('testapp', instance_path=instance_path,static_folder=join(instance_path, "static"))
    app_.config.update(
        ACCOUNTS_JWT_ENABLE=False,
        SECRET_KEY='SECRET_KEY',
        WEKO_INDEX_TREE_UPDATED=True,
        TESTING=True,
        FILES_REST_DEFAULT_QUOTA_SIZE = None,
        FILES_REST_DEFAULT_STORAGE_CLASS = 'S',
        FILES_REST_STORAGE_CLASS_LIST = {
            'S': 'Standard',
            'A': 'Archive',
        },
        CACHE_REDIS_URL=os.environ.get("CACHE_REDIS_URL", "redis://redis:6379/0"),
        CACHE_TYPE="redis",
        CACHE_REDIS_DB='0',
        CACHE_REDIS_HOST="redis",
        WEKO_INDEX_TREE_STATE_PREFIX="index_tree_expand_state",
        REDIS_PORT='6379',
        DEPOSIT_DEFAULT_JSONSCHEMA=DEPOSIT_DEFAULT_JSONSCHEMA,
        SERVER_NAME='TEST_SERVER',
        LOGIN_DISABLED=False,
        INDEXER_DEFAULT_DOCTYPE='item-v1.0.0',
        INDEXER_FILE_DOC_TYPE='content',
        INDEXER_DEFAULT_INDEX="{}-weko-item-v1.0.0".format(
            'test'
        ),
        INDEX_IMG='indextree/36466818-image.jpg',
        INDEXER_MQ_QUEUE = Queue("indexer", exchange=Exchange("indexer", type="direct"), routing_key="indexer",queue_arguments={"x-queue-type":"quorum"}),
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                          'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        SEARCH_ELASTIC_HOSTS=os.environ.get(
            'SEARCH_ELASTIC_HOSTS', 'elasticsearch'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        JSONSCHEMAS_HOST='inveniosoftware.org',
        ACCOUNTS_USERINFO_HEADERS=True,
        I18N_LANGUAGES=[("ja", "Japanese"), ("en", "English")],
        WEKO_INDEX_TREE_INDEX_LOCK_KEY_PREFIX="lock_index_",
        WEKO_INDEX_TREE_DEFAULT_DISPLAY_NUMBER = 5,
        WEKO_PERMISSION_SUPER_ROLE_USER=WEKO_PERMISSION_SUPER_ROLE_USER,
        WEKO_PERMISSION_ROLE_COMMUNITY=WEKO_PERMISSION_ROLE_COMMUNITY,
        EMAIL_DISPLAY_FLG=EMAIL_DISPLAY_FLG,
        THEME_SITEURL="https://localhost",
        DEPOSIT_RECORDS_UI_ENDPOINTS=DEPOSIT_RECORDS_UI_ENDPOINTS,
        DEPOSIT_REST_ENDPOINTS=DEPOSIT_REST_ENDPOINTS,
        DEPOSIT_DEFAULT_STORAGE_CLASS=DEPOSIT_DEFAULT_STORAGE_CLASS,
        # SEARCH_UI_SEARCH_INDEX=SEARCH_UI_SEARCH_INDEX,
        SEARCH_UI_SEARCH_INDEX="test-weko",
        # SEARCH_ELASTIC_HOSTS=os.environ.get("INVENIO_ELASTICSEARCH_HOST"),
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
        WEKO_RECORDS_UI_LICENSE_DICT=[
            {
                'name': _('write your own license'),
                'value': 'license_free',
            },
            # version 0
            {
                'name': _(
                    'Creative Commons CC0 1.0 Universal Public Domain Designation'),
                'code': 'CC0',
                'href_ja': 'https://creativecommons.org/publicdomain/zero/1.0/deed.ja',
                'href_default': 'https://creativecommons.org/publicdomain/zero/1.0/',
                'value': 'license_12',
                'src': '88x31(0).png',
                'src_pdf': 'cc-0.png',
                'href_pdf': 'https://creativecommons.org/publicdomain/zero/1.0/'
                            'deed.ja',
                'txt': 'This work is licensed under a Public Domain Dedication '
                    'International License.'
            },
            # version 3.0
            {
                'name': _('Creative Commons Attribution 3.0 Unported (CC BY 3.0)'),
                'code': 'CC BY 3.0',
                'href_ja': 'https://creativecommons.org/licenses/by/3.0/deed.ja',
                'href_default': 'https://creativecommons.org/licenses/by/3.0/',
                'value': 'license_6',
                'src': '88x31(1).png',
                'src_pdf': 'by.png',
                'href_pdf': 'http://creativecommons.org/licenses/by/3.0/',
                'txt': 'This work is licensed under a Creative Commons Attribution'
                       ' 3.0 International License.'
            },
            {
                'name': _(
                    'Creative Commons Attribution-ShareAlike 3.0 Unported '
                    '(CC BY-SA 3.0)'),
                'code': 'CC BY-SA 3.0',
                'href_ja': 'https://creativecommons.org/licenses/by-sa/3.0/deed.ja',
                'href_default': 'https://creativecommons.org/licenses/by-sa/3.0/',
                'value': 'license_7',
                'src': '88x31(2).png',
                'src_pdf': 'by-sa.png',
                'href_pdf': 'http://creativecommons.org/licenses/by-sa/3.0/',
                'txt': 'This work is licensed under a Creative Commons Attribution'
                    '-ShareAlike 3.0 International License.'
            },
            {
                'name': _(
                    'Creative Commons Attribution-NoDerivs 3.0 Unported (CC BY-ND 3.0)'),
                'code': 'CC BY-ND 3.0',
                'href_ja': 'https://creativecommons.org/licenses/by-nd/3.0/deed.ja',
                'href_default': 'https://creativecommons.org/licenses/by-nd/3.0/',
                'value': 'license_8',
                'src': '88x31(3).png',
                'src_pdf': 'by-nd.png',
                'href_pdf': 'http://creativecommons.org/licenses/by-nd/3.0/',
                'txt': 'This work is licensed under a Creative Commons Attribution'
                    '-NoDerivatives 3.0 International License.'

            },
            {
                'name': _(
                    'Creative Commons Attribution-NonCommercial 3.0 Unported'
                    ' (CC BY-NC 3.0)'),
                'code': 'CC BY-NC 3.0',
                'href_ja': 'https://creativecommons.org/licenses/by-nc/3.0/deed.ja',
                'href_default': 'https://creativecommons.org/licenses/by-nc/3.0/',
                'value': 'license_9',
                'src': '88x31(4).png',
                'src_pdf': 'by-nc.png',
                'href_pdf': 'http://creativecommons.org/licenses/by-nc/3.0/',
                'txt': 'This work is licensed under a Creative Commons Attribution'
                    '-NonCommercial 3.0 International License.'
            },
            {
                'name': _(
                    'Creative Commons Attribution-NonCommercial-ShareAlike 3.0 '
                    'Unported (CC BY-NC-SA 3.0)'),
                'code': 'CC BY-NC-SA 3.0',
                'href_ja': 'https://creativecommons.org/licenses/by-nc-sa/3.0/deed.ja',
                'href_default': 'https://creativecommons.org/licenses/by-nc-sa/3.0/',
                'value': 'license_10',
                'src': '88x31(5).png',
                'src_pdf': 'by-nc-sa.png',
                'href_pdf': 'http://creativecommons.org/licenses/by-nc-sa/3.0/',
                'txt': 'This work is licensed under a Creative Commons Attribution'
                    '-NonCommercial-ShareAlike 3.0 International License.'
            },
            {
                'name': _(
                    'Creative Commons Attribution-NonCommercial-NoDerivs '
                    '3.0 Unported (CC BY-NC-ND 3.0)'),
                'code': 'CC BY-NC-ND 3.0',
                'href_ja': 'https://creativecommons.org/licenses/by-nc-nd/3.0/deed.ja',
                'href_default': 'https://creativecommons.org/licenses/by-nc-nd/3.0/',
                'value': 'license_11',
                'src': '88x31(6).png',
                'src_pdf': 'by-nc-nd.png',
                'href_pdf': 'http://creativecommons.org/licenses/by-nc-nd/3.0/',
                'txt': 'This work is licensed under a Creative Commons Attribution'
                    '-NonCommercial-ShareAlike 3.0 International License.'
            },
            # version 4.0
            {
                'name': _('Creative Commons Attribution 4.0 International (CC BY 4.0)'),
                'code': 'CC BY 4.0',
                'href_ja': 'https://creativecommons.org/licenses/by/4.0/deed.ja',
                'href_default': 'https://creativecommons.org/licenses/by/4.0/',
                'value': 'license_0',
                'src': '88x31(1).png',
                'src_pdf': 'by.png',
                'href_pdf': 'http://creativecommons.org/licenses/by/4.0/',
                'txt': 'This work is licensed under a Creative Commons Attribution'
                    ' 4.0 International License.'
            },
            {
                'name': _(
                    'Creative Commons Attribution-ShareAlike 4.0 International '
                    '(CC BY-SA 4.0)'),
                'code': 'CC BY-SA 4.0',
                'href_ja': 'https://creativecommons.org/licenses/by-sa/4.0/deed.ja',
                'href_default': 'https://creativecommons.org/licenses/by-sa/4.0/',
                'value': 'license_1',
                'src': '88x31(2).png',
                'src_pdf': 'by-sa.png',
                'href_pdf': 'http://creativecommons.org/licenses/by-sa/4.0/',
                'txt': 'This work is licensed under a Creative Commons Attribution'
                    '-ShareAlike 4.0 International License.'
            },
            {
                'name': _(
                    'Creative Commons Attribution-NoDerivatives 4.0 International '
                    '(CC BY-ND 4.0)'),
                'code': 'CC BY-ND 4.0',
                'href_ja': 'https://creativecommons.org/licenses/by-nd/4.0/deed.ja',
                'href_default': 'https://creativecommons.org/licenses/by-nd/4.0/',
                'value': 'license_2',
                'src': '88x31(3).png',
                'src_pdf': 'by-nd.png',
                'href_pdf': 'http://creativecommons.org/licenses/by-nd/4.0/',
                'txt': 'This work is licensed under a Creative Commons Attribution'
                    '-NoDerivatives 4.0 International License.'
            },
            {
                'name': _(
                    'Creative Commons Attribution-NonCommercial 4.0 International'
                    ' (CC BY-NC 4.0)'),
                'code': 'CC BY-NC 4.0',
                'href_ja': 'https://creativecommons.org/licenses/by-nc/4.0/deed.ja',
                'href_default': 'https://creativecommons.org/licenses/by-nc/4.0/',
                'value': 'license_3',
                'src': '88x31(4).png',
                'src_pdf': 'by-nc.png',
                'href_pdf': 'http://creativecommons.org/licenses/by-nc/4.0/',
                'txt': 'This work is licensed under a Creative Commons Attribution'
                    '-NonCommercial 4.0 International License.'
            },
            {
                'name': _(
                    'Creative Commons Attribution-NonCommercial-ShareAlike 4.0'
                    ' International (CC BY-NC-SA 4.0)'),
                'code': 'CC BY-NC-SA 4.0',
                'href_ja': 'https://creativecommons.org/licenses/by-nc-sa/4.0/deed.ja',
                'href_default': 'https://creativecommons.org/licenses/by-nc-sa/4.0/',
                'value': 'license_4',
                'src': '88x31(5).png',
                'src_pdf': 'by-nc-sa.png',
                'href_pdf': 'http://creativecommons.org/licenses/by-nc-sa/4.0/',
                'txt': 'This work is licensed under a Creative Commons Attribution'
                    '-NonCommercial-ShareAlike 4.0 International License.'
            },
            {
                'name': _(
                    'Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 '
                    'International (CC BY-NC-ND 4.0)'),
                'code': 'CC BY-NC-ND 4.0',
                'href_ja': 'https://creativecommons.org/licenses/by-nc-nd/4.0/deed.ja',
                'href_default': 'https://creativecommons.org/licenses/by-nc-nd/4.0/',
                'value': 'license_5',
                'src': '88x31(6).png',
                'src_pdf': 'by-nc-nd.png',
                'href_pdf': 'http://creativecommons.org/licenses/by-nc-nd/4.0/',
                'txt': 'This work is licensed under a Creative Commons Attribution'
                    '-NonCommercial-ShareAlike 4.0 International License.'
            },
        ],
        WEKO_ITEMS_UI_OUTPUT_REGISTRATION_TITLE="",
        WEKO_ITEMS_UI_MULTIPLE_APPROVALS=True,
        WEKO_THEME_DEFAULT_COMMUNITY="Root Index",
        WEKO_SEARCH_REST_ENDPOINTS = dict(
            recid=dict(
                pid_type='recid',
                pid_minter='recid',
                pid_fetcher='recid',
                search_class=RecordsSearch,
                # search_index="test-weko",
                # search_index=SEARCH_UI_SEARCH_INDEX,
                search_index="tenant1",
                search_type='item-v1.0.0',
                search_factory_imp='weko_search_ui.query.weko_search_factory',
                # record_class='',
                record_serializers={
                    'application/json': ('invenio_records_rest.serializers'
                                        ':json_v1_response'),
                },
                search_serializers={
                    'application/json': ('weko_records.serializers'
                                        ':json_v1_search'),
                },
                index_route='/index/',
                tree_route='/index',
                get_index_tree='/<string:version>/tree/index/<int:index_id>',
                get_index_root_tree='/<string:version>/tree/index',
                item_tree_route='/index/<string:pid_value>',
                index_move_route='/index/move/<int:index_id>',
                links_factory_imp='weko_search_ui.links:default_links_factory',
                default_media_type='application/json',
                max_result_window=10000,
            ),
        ),
        WEKO_INDEX_TREE_REST_ENDPOINTS = dict(
            tid=dict(
                record_class='weko_index_tree.api:Indexes',
                index_route='/tree/index/<int:index_id>',
                get_index_tree='/<string:version>/tree/index/<int:index_id>',
                get_index_root_tree='/<string:version>/tree/index',
                get_parent_index_tree='/<string:version>/tree/index/<int:index_id>/parent',
                tree_route='/tree',
                item_tree_route='/tree/<string:pid_value>',
                index_move_route='/tree/move/<int:index_id>',
                default_media_type='application/json',
                api_get_all_index_jp_en='/<string:version>/tree',
                api_get_index_tree='/<string:version>/tree/<int:index_id>',
                api_create_index='/<string:version>/tree/index/',
                api_update_index='/<string:version>/tree/index/<int:index_id>',
                api_delete_index='/<string:version>/tree/index/<int:index_id>',
                create_permission_factory_imp='weko_index_tree.permissions:index_tree_permission',
                read_permission_factory_imp='weko_index_tree.permissions:index_tree_permission',
                update_permission_factory_imp='weko_index_tree.permissions:index_tree_permission',
                delete_permission_factory_imp='weko_index_tree.permissions:index_tree_permission',
            )
        ),
        WEKO_INDEX_TREE_STYLE_OPTIONS = {
            'id': 'weko',
            'widths': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11']
        },
        WEKO_INDEX_TREE_INDEX_ADMIN_TEMPLATE = 'weko_index_tree/admin/index_edit_setting.html',
        WEKO_INDEX_TREE_LIST_API = "/api/tree",
        WEKO_INDEX_TREE_API = "/api/tree/index/",
        WEKO_THEME_INSTANCE_DATA_DIR="data",
        WEKO_HANDLE_ALLOW_REGISTER_CNRI=False,
        WEKO_ADMIN_PERMISSION_ROLE_COMMUNITY="Community Administrator"
    )
    app_.url_map.converters['pid'] = PIDConverter

    FlaskCeleryExt(app_)
    Menu(app_)
    Babel(app_)
    InvenioDB(app_)
    InvenioAccounts(app_)
    InvenioAccess(app_)
    InvenioAssets(app_)
    InvenioCache(app_)
    InvenioJSONSchemas(app_)
    InvenioSearch(app_)
    InvenioRecords(app_)
    InvenioIndexer(app_)
    InvenioI18N(app_)
    InvenioPIDRelations(app_)
    InvenioOAIServer(app_)
    InvenioMail(app_)
    InvenioStats(app_)
    InvenioAdmin(app_)
    InvenioPIDStore(app_)
    InvenioOAuth2Server(app_)
    InvenioOAuth2ServerREST(app_)
    WekoSearchUI(app_)
    WekoWorkflow(app_)
    WekoGroups(app_)
    WekoAccounts(app_)
    WekoLoggingUserActivity(app_)

    current_assets = LocalProxy(lambda: app_.extensions["invenio-assets"])
    current_assets.collect.collect()

    return app_


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
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
def without_session_remove():
    with patch("weko_search_ui.views.db.session.remove"):
        with patch("weko_search_ui.rest.db.session.remove"):
            yield

@pytest.yield_fixture()
def i18n_app(app):
    with app.test_request_context(
        headers=[('Accept-Language','ja')]):
        app.extensions['invenio-oauth2server'] = 1
        yield app


    # args=[
    #         ('index_id', 33),
    #         ('page', 1),
    #         ('count', 20),
    #         ('term', 14),
    #         ('lang', 'en'),
    #     ]


@pytest.yield_fixture()
def client_rest(app):
    app.register_blueprint(create_blueprint(app, app.config['WEKO_INDEX_TREE_REST_ENDPOINTS']))
    with app.test_client() as client:
        yield client


@pytest.yield_fixture()
def client_api(app):
    app.register_blueprint(blueprint_api, url_prefix='/api')
    with app.test_client() as client:
        yield client


@pytest.yield_fixture()
def client_request_args(app):
    app.register_blueprint(create_blueprint(app, app.config['WEKO_INDEX_TREE_REST_ENDPOINTS']))
    with app.test_client() as client:
        r = client.get('/', query_string={
            'index_id': '33',
            'page': 1,
            'count': 20,
            'term': 14,
            'lang': 'en',
            'parent_id': 33,
            'index_info': {}
            })
        yield r


@pytest.fixture()
def location(app):
    """Create default location."""
    tmppath = tempfile.mkdtemp()
    with db_.session.begin_nested():
        Location.query.delete()
        loc = Location(name='local', uri=tmppath, default=True)
        db_.session.add(loc)
    db_.session.commit()
    return location


@pytest.fixture()
def user(app, db):
    """Create a example user."""
    return create_test_user(email='test@test.org')


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
        noroleuser = create_test_user(email='noroleuser@test.org')
    else:
        user = User.query.filter_by(email='user@test.org').first()
        contributor = User.query.filter_by(email='contributor@test.org').first()
        comadmin = User.query.filter_by(email='comadmin@test.org').first()
        repoadmin = User.query.filter_by(email='repoadmin@test.org').first()
        sysadmin = User.query.filter_by(email='sysadmin@test.org').first()
        generaluser = User.query.filter_by(email='generaluser@test.org').first()
        originalroleuser = User.query.filter_by(email='originalroleuser@test.org').first()
        originalroleuser2 = User.query.filter_by(email='originalroleuser2@test.org').first()
        noroleuser = User.query.filter_by(email='noroleuser@test.org').first()

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
    ds.add_role_to_user(user, sysadmin_role)
    ds.add_role_to_user(user, repoadmin_role)
    ds.add_role_to_user(user, contributor_role)
    ds.add_role_to_user(user, comadmin_role)

    # Assign access authorization
    with db.session.begin_nested():
        action_users = [
            ActionUsers(action='superuser-access', user=sysadmin)
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

    return [
        {'email': noroleuser.email, 'id': noroleuser.id, 'obj': noroleuser},
        {'email': contributor.email, 'id': contributor.id, 'obj': contributor},
        {'email': repoadmin.email, 'id': repoadmin.id, 'obj': repoadmin},
        {'email': sysadmin.email, 'id': sysadmin.id, 'obj': sysadmin},
        {'email': comadmin.email, 'id': comadmin.id, 'obj': comadmin},
        {'email': generaluser.email, 'id': generaluser.id, 'obj': sysadmin},
        {'email': originalroleuser.email, 'id': originalroleuser.id, 'obj': originalroleuser},
        {'email': originalroleuser2.email, 'id': originalroleuser2.id, 'obj': originalroleuser2},
        {'email': user.email, 'id': user.id, 'obj': user},
    ]


@pytest.fixture
def indices(app, db):
    with db.session.begin_nested():
        # Create a test Indices
        testIndexOne = Index(
            index_name="testIndexOne",
            browsing_role="1,2,3,4,-98,-99",
            public_state=True,
            id=11,
            position=0
        )
        testIndexTwo = Index(
            index_name="testIndexTwo",
            browsing_group="group_test1",
            public_state=True,
            id=22,
            position=1
        )
        testIndexThree = Index(
            index_name="testIndexThree",
            browsing_role="1,2,3,4,-98,-99",
            public_state=True,
            harvest_public_state=True,
            id=33,
            position=2,
            public_date=datetime.today() - timedelta(days=1)
        )
        testIndexPrivate = Index(
            index_name="testIndexPrivate",
            public_state=False,
            id=55,
            position=3
        )
        testIndexThreeChild = Index(
            index_name="testIndexThreeChild",
            browsing_role="1,2,3,4,-98,-99",
            parent=33,
            index_link_enabled=True,
            index_link_name="test_link",
            public_state=True,
            harvest_public_state=False,
            id=44,
            position=0,
            public_date=datetime.today() - timedelta(days=1)
        )
        testIndexMore = Index(
            index_name="testIndexMore",
            parent=33,
            public_state=True,
            id=45,
            position=1
        )
        testIndexSix = Index(
            index_name="testIndexSix",
            browsing_role="1,2,3,4,-98,-99",
            public_state=True,
            id=66,
            position=4
        )


        db.session.add(testIndexOne)
        db.session.add(testIndexTwo)
        db.session.add(testIndexThree)
        db.session.add(testIndexThreeChild)
        db.session.add(testIndexMore)
        db.session.add(testIndexPrivate)
        db.session.add(testIndexSix)

    return {
        'index_dict': dict(testIndexThree),
        'index_non_dict': testIndexThree,
        'index_non_dict_child': testIndexThreeChild,
        'testIndexOne':testIndexOne,
        'testIndexTwo':testIndexTwo,
        'testIndexThree':testIndexThree,
        'testIndexThreeChild':testIndexThreeChild,
        'testIndexMore':testIndexMore,
        'testIndexPrivate':testIndexPrivate,
    }


@pytest.fixture
def test_indices(app, db):
    def base_index(id, parent, position, harvest_public_state=True, public_state=True, public_date=None, coverpage_state=False, recursive_browsing_role=False,
                   recursive_contribute_role=False, recursive_browsing_group=False,
                   recursive_contribute_group=False, online_issn='', is_deleted=False):
        _browsing_role = "3,-99"
        _contribute_role = "1,2,3,4,-98,-99"
        _group = "g1,g2"
        return Index(
            id=id,
            parent=parent,
            position=position,
            index_name="テストインデックス {}".format(id),
            index_name_english="Test index {}".format(id),
            index_link_name="Test index link {}_ja".format(id),
            index_link_name_english="Test index link {}_en".format(id),
            index_link_enabled=True,
            more_check=False,
            display_no=position,
            harvest_public_state=harvest_public_state,
            public_state=public_state,
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
            is_deleted=is_deleted,
        )

    with db.session.begin_nested():
        db.session.query(Index).delete()
    db.session.commit()

    with db.session.begin_nested():
        db.session.add(base_index(1, 0, 0, True, True, datetime(2022, 1, 1), True, True, True, True, True, '1234-5678'))
        db.session.add(base_index(2, 0, 1))
        db.session.add(base_index(3, 0, 2))
        db.session.add(base_index(11, 1, 0))
        db.session.add(base_index(21, 2, 0))
        db.session.add(base_index(22, 2, 1))
        db.session.add(base_index(31, 3, 0, public_state=False))
        db.session.add(base_index(32, 3, 1, is_deleted=True))
        db.session.add(base_index(33, 3, 2, harvest_public_state=False, is_deleted=True))
        db.session.add(base_index(100, 0, 3, is_deleted=True))
        db.session.add(base_index(101, 100, 0, coverpage_state=True, is_deleted=True))
    db.session.commit()

@pytest.fixture
def indices_for_api(app, db):
    with db.session.begin_nested():
        sample_index = Index(
            id=1623632832836,
            parent=0,
            position=0,
            index_name="サンプルインデックス",
            index_name_english="Sample Index",
            browsing_role="3,-98,-99",
            contribute_role="1,2,3,4,-98",
            browsing_group="",
            contribute_group="",
            public_state=False,
            harvest_public_state=False,
            owner_user_id=1,
            created=datetime(2021, 6, 14, 1, 7, 10, 647996),
            updated=datetime(2024, 6, 12, 12, 21, 26, 526676)
        )

        parent_index = Index(
            id=1740974499997,
            parent=0,
            position=1,
            index_name="親インデックス",
            index_name_english="parent index",
            browsing_role="3,4,-98,-99",
            contribute_role="3,4,-98,-99",
            browsing_group="",
            contribute_group="",
            public_state=True,
            harvest_public_state=True,
            owner_user_id=1,
            created=datetime(2025, 3, 3, 4, 1, 40, 933902),
            updated=datetime(2025, 3, 3, 4, 2, 30, 157607)
        )

        child_index_1 = Index(
            id=1740974554289,
            parent=1740974499997,
            position=0,
            index_name="子インデックス 1",
            index_name_english="child index 1",
            browsing_role="3,4,-98,-99",
            contribute_role="3,4,-98,-99",
            browsing_group="",
            contribute_group="",
            public_state=False,
            harvest_public_state=True,
            owner_user_id=1,
            created=datetime(2025, 3, 3, 4, 2, 35, 229217),
            updated=datetime(2025, 3, 3, 4, 3, 6, 841368)
        )

        child_index_2 = Index(
            id=1740974612379,
            parent=1740974499997,
            position=1,
            index_name="子インデックス 2",
            index_name_english="child index 2",
            browsing_role="3,4,-98,-99",
            contribute_role="3,4,-98,-99",
            browsing_group="",
            contribute_group="",
            public_state=True,
            harvest_public_state=True,
            owner_user_id=1,
            created=datetime(2025, 3, 3, 4, 3, 33, 316001),
            updated=datetime(2025, 3, 3, 4, 3, 58, 104842)
        )

        child_index_3 = Index(
            id=1740974612380,
            parent=1740974612379,
            position=1,
            index_name="子インデックス 3",
            index_name_english="child index 3",
            browsing_role="3,4,-98,-99",
            contribute_role="3,4,-98,-99",
            browsing_group="",
            contribute_group="",
            public_state=False,
            harvest_public_state=True,
            owner_user_id=1,
            created=datetime(2025, 3, 3, 4, 3, 33, 316001),
            updated=datetime(2025, 3, 3, 4, 3, 58, 104842)
        )

        comm_index = Index(
            id=1745385873579,
            parent=0,
            position=2,
            index_name="コミュニティインデックス",
            index_name_english="Community Index",
            browsing_role="",
            contribute_role="",
            browsing_group="",
            contribute_group="",
            public_state=True,
            harvest_public_state=True,
            owner_user_id=1,
            created=datetime(2025, 3, 3, 4, 3, 33, 316001),
            updated=datetime(2025, 3, 3, 4, 3, 58, 104842)
        )

        comm_child_index = Index(
            id=1745385873580,
            parent=1745385873579,
            position=0,
            index_name="コミュニティ子インデックス",
            index_name_english="Community Child Index",
            browsing_role="3,4,-98,-99",
            contribute_role="3,4,-98,-99",
            browsing_group="",
            contribute_group="",
            public_state=True,
            harvest_public_state=True,
            owner_user_id=1,
            created=datetime(2025, 3, 3, 4, 3, 33, 316001),
            updated=datetime(2025, 3, 3, 4, 3, 58, 104842)
        )

        db.session.add(sample_index)
        db.session.add(parent_index)
        db.session.add(child_index_1)
        db.session.add(child_index_2)
        db.session.add(child_index_3)
        db.session.add(comm_index)
        db.session.add(comm_child_index)

    return {
        'sample_index': sample_index,
        'parent_index': parent_index,
        'child_index_1': child_index_1,
        'child_index_2': child_index_2,
        "child_index_3": child_index_3,
        "comm_index": comm_index,
        "comm_child_index": comm_child_index
    }

@pytest.yield_fixture
def without_oaiset_signals(app):
    """Temporary disable oaiset signals."""
    from invenio_oaiserver import current_oaiserver
    current_oaiserver.unregister_signals_oaiset()
    yield
    current_oaiserver.register_signals_oaiset()


@pytest.fixture()
def esindex(app,db_records):
    with open("tests/data/mappings/item-v1.0.0.json","r") as f:
        mapping = json.load(f)

    search = LocalProxy(lambda: app.extensions["invenio-search"])

    with app.test_request_context():
        try:
            search.client.indices.create(app.config["INDEXER_DEFAULT_INDEX"],body=mapping)
            search.client.indices.put_alias(index=app.config["INDEXER_DEFAULT_INDEX"], name="test-weko")
        except:
            search.client.indices.create("test-weko-items",body=mapping)
            search.client.indices.put_alias(index="test-weko-items", name="test-weko")
        # print(current_search_client.indices.get_alias())

    for depid, recid, parent, doi, record, item in db_records:
        search.client.index(index='test-weko-item-v1.0.0', doc_type='item-v1.0.0', id=record.id, body=record,refresh='true')


    yield search

    with app.test_request_context():
        try:
            search.client.indices.delete_alias(index=app.config["INDEXER_DEFAULT_INDEX"], name="test-weko")
            search.client.indices.delete(index=app.config["INDEXER_DEFAULT_INDEX"], ignore=[400, 404])
        except:
            search.client.indices.delete_alias(index="test-weko-items", name="test-weko")
            search.client.indices.delete(index="test-weko-items", ignore=[400, 404])


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
            'id': 1,
            'parent': 0,
            'value': 'IndexA',
        }
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        Indexes.create(0, index_metadata)
    index_metadata = {
            'id': 2,
            'parent': 0,
            'value': 'IndexB',
        }

    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        Indexes.create(0, index_metadata)


    yield result


@pytest.fixture
def redis_connect(app):
    redis_connection = RedisConnection().connection(db=app.config['CACHE_REDIS_DB'], kv = True)
    return redis_connection


@pytest.fixture()
def db_register(app, db):
    action_datas=dict()
    with open('tests/data/actions.json', 'r') as f:
        action_datas = json.load(f)
    actions_db = list()
    with db.session.begin_nested():
        for data in action_datas:
            actions_db.append(Action(**data))
        db.session.add_all(actions_db)

    actionstatus_datas = dict()
    with open('tests/data/action_status.json') as f:
        actionstatus_datas = json.load(f)
    actionstatus_db = list()
    with db.session.begin_nested():
        for data in actionstatus_datas:
            actionstatus_db.append(ActionStatus(**data))
        db.session.add_all(actionstatus_db)

    index = Index(
        public_state=True
    )

    index_private = Index(
        id=999,
        public_state=False,
        public_date=datetime.strptime('2099/04/24 0:00:00','%Y/%m/%d %H:%M:%S')
    )

    flow_define = FlowDefine(flow_id=uuid.uuid4(),
                             flow_name='Registration Flow',
                             flow_user=1)

    item_type_name = ItemTypeName(name='test item type',
                                  has_site_license=True,
                                  is_active=True)

    item_type = ItemType(name_id=1,harvesting_type=True,
                         schema={'type':'test schema'},
                         form={'type':'test form'},
                         render={'type':'test render'},
                         tag=1,version_id=1,is_deleted=False)

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

    workflow = WorkFlow(flows_id=uuid.uuid4(),
                        flows_name='test workflow1',
                        itemtype_id=1,
                        index_tree_id=1,
                        flow_id=1,
                        is_deleted=False,
                        open_restricted=False,
                        location_id=None,
                        is_gakuninrdm=False,
                        repository_id=1)

    activity = Activity(activity_id='1',workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=1,
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_ids=[], extra_info={},
                    action_order=6)

    with db.session.begin_nested():
        db.session.add(index)
        db.session.add(flow_define)
        db.session.add(item_type_name)
        db.session.add(item_type)
        db.session.add(flow_action1)
        db.session.add(flow_action2)
        db.session.add(flow_action3)
        db.session.add(workflow)
        db.session.add(activity)

    # return {'flow_define':flow_define,'item_type_name':item_type_name,'item_type':item_type,'flow_action':flow_action,'workflow':workflow,'activity':activity}
    return {
        'flow_define': flow_define,
        'item_type': item_type,
        'workflow': workflow,
        'activity': activity,
        'indices': {
            'index': index,
            'index_private': index_private,
        }
    }


@pytest.fixture()
def db_register2(app, db):
    session_lifetime = SessionLifetime(lifetime=60,is_delete=False)

    with db.session.begin_nested():
        db.session.add(session_lifetime)


@pytest.fixture()
def records(db):
    with db.session.begin_nested():
        id1 = uuid.UUID('b7bdc3ad-4e7d-4299-bd87-6d79a250553f')
        rec1 = RecordMetadata(
            id=id1,
            json=json_data("data/record01.json"),
            version_id=1
        )

        id2 = uuid.UUID('362e800c-08a2-425d-a2b6-bcae7d5c3701')
        rec2 = RecordMetadata(
            id=id2,
            json=json_data("data/record02.json"),
            version_id=2
        )

        id3 = uuid.UUID('3ead53d0-8e4a-489e-bb6c-d88433a029c2')
        rec3 = RecordMetadata(
            id=id3,
            json=json_data("data/record03.json"),
            version_id=3
        )

        db.session.add(rec1)
        db.session.add(rec2)
        db.session.add(rec3)

        search_query_result = json_data("data/search_result.json")

    return(search_query_result)


@pytest.fixture()
def pdfcoverpage(app, db):
    with db.session.begin_nested():
        pdf_cover_sample = PDFCoverPageSettings(
            avail='enable',
            header_display_type='string',
            header_output_string='test',
            header_output_image='test',
            header_display_position='center'
        )

        db.session.add(pdf_cover_sample)

    return pdf_cover_sample


@pytest.fixture()
def item_type(app, db):
    _item_type_name = ItemTypeName(name='test')

    _render = {
        'meta_list': {},
        'table_row_map': {
            'schema': {
                'properties': {
                    'item_1': {}
                }
            }
        },
        'table_row': ['1']
    }

    return ItemTypes.create(
        name='test',
        item_type_name=_item_type_name,
        schema={},
        render=_render,
        tag=1
    )


@pytest.fixture()
def item_type2(app, db):
    _item_type_name = ItemTypeName(name='test2')

    _render = {
        'meta_list': {},
        'table_row_map': {
            'schema': {
                'properties': {
                    'item_1': {}
                }
            }
        },
        'table_row': ['1']
    }

    return ItemTypes.create(
        name='test2',
        item_type_name=_item_type_name,
        schema={},
        render=_render,
        tag=1
    )


@pytest.fixture()
def mock_execute(app):
    def factory(data):
        if isinstance(data, str):
            data = json_data(data)
        dummy = response.Response(Search(), data)
        return dummy
    return factory


# @pytest.fixture()
# def records2(db):
#     record_data = json_data("data/test_records.json")
#     item_data = json_data("data/test_items.json")
#     record_num = len(record_data)
#     result = []
#     for d in range(record_num):
#         result.append(create_record(record_data[d], item_data[d]))
#     db.session.commit()
#     yield result


@pytest.fixture()
def count_json_data():
    data = [{
        "public_state": True,
        "doc_count": 99,
        "no_available": 9
    }]
    return data

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
    oaischema = OAIServerSchema(
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
    with db.session.begin_nested():
        db.session.add(oaischema)


@pytest.fixture()
def communities(app, db, users, test_indices):
    """Create some example communities."""
    comm1 = Community(
        id='comm1',
        id_user=users[3]['id'],
        title='Test Comm Title',
        root_node_id=1,
        id_role=users[3]['obj'].roles[0].id
    )
    comm2 = Community(
        id='comm2',
        id_user=users[1]['id'],
        title='Test Comm Title',
        root_node_id=1,
        id_role=users[1]['obj'].roles[0].id
    )
    with db.session.begin_nested():
        db.session.add(comm1)
        db.session.add(comm2)
    db.session.commit()

    return comm1


@pytest.fixture()
def mock_users():
    """Create mock users."""
    mock_auth_user = Mock()
    mock_auth_user.get_id = lambda: '123'
    mock_auth_user.is_authenticated = True

    mock_anon_user = Mock()
    mock_anon_user.is_authenticated = False
    return {
        'anonymous': mock_anon_user,
        'authenticated': mock_auth_user
    }


@pytest.yield_fixture()
def mock_user_ctx(mock_users):
    """Run in a mock authenticated user context."""
    with patch('invenio_stats.utils.current_user',
               mock_users['authenticated']):
        yield


@pytest.yield_fixture()
def es(app):
    """Provide elasticsearch access, create and clean indices.

    Don't create template so that the test or another fixture can modify the
    enabled events.
    """
    current_search_client.indices.delete(index='*')
    current_search_client.indices.delete_template('*')
    list(current_search.create())
    try:
        yield current_search_client
    finally:
        current_search_client.indices.delete(index='*')
        current_search_client.indices.delete_template('*')


def generate_events(
        app,
        index_id='33',
        page=1,
        count=20,
        term=14,
        lang='en',
        ):
    """Queued events for processing tests."""
    current_queues.declare()

    def _unique_ts_gen():
        ts = 0
        while True:
            ts += 1
            yield ts

    def generator_list():
        unique_ts = _unique_ts_gen()

        def build_event(is_robot=False):
            ts = next(unique_ts)
            return dict(
                timestamp=datetime.datetime.combine(
                    entry_date,
                    datetime.time(minute=ts % 60,
                                    second=ts % 60)).
                isoformat(),
                index_id='33',
                page=1,
                count=20,
                term=14,
                lang='en',
            )

            yield build_event(True)

    mock_queue = Mock()
    mock_queue.consume.return_value = generator_list()
    # mock_queue.routing_key = 'stats-file-download'
    mock_queue.routing_key = 'generate-sample'

    EventsIndexer(
        mock_queue,
        preprocessors=[
            build_file_unique_id
        ],
        double_click_window=0
    ).run()
    current_search_client.indices.refresh(index='*')


@pytest.yield_fixture()
def generate_request(app, es, mock_user_ctx, request):
    """Parametrized pre indexed sample events."""
    generate_events(app=app, **request.param)
    yield


@pytest.yield_fixture()
def dummy_location(db):
    """File system location."""
    tmppath = tempfile.mkdtemp()

    loc = Location(
        name='testloc',
        uri=tmppath,
        default=True
    )
    db.session.add(loc)
    db.session.commit()

    yield loc

    shutil.rmtree(tmppath)


@pytest.fixture()
def bucket(db, dummy_location):
    """File system location."""
    b1 = Bucket.create()
    db.session.commit()
    return b1


@pytest.yield_fixture()
def permissions(db, bucket):
    """Permission for users."""
    users = {
        None: None,
    }

    for user in [
            'auth', 'location', 'bucket',
            'objects', 'objects-read-version']:
        users[user] = create_test_user(
            email='{0}@invenio-software.org'.format(user),
            password='pass1',
            active=True
        )

    location_perms = [
        location_update_all,
        bucket_read_all,
        bucket_read_versions_all,
        bucket_update_all,
        bucket_listmultiparts_all,
        object_read_all,
        object_read_version_all,
        object_delete_all,
        object_delete_version_all,
        multipart_read_all,
        multipart_delete_all,
    ]

    bucket_perms = [
        bucket_read_all,
        object_read_all,
        bucket_update_all,
        object_delete_all,
        multipart_read_all,
    ]

    objects_perms = [
        object_read_all,
    ]

    for perm in location_perms:
        db.session.add(ActionUsers(
            action=perm.value,
            user=users['location']))
    for perm in bucket_perms:
        db.session.add(ActionUsers(
            action=perm.value,
            argument=str(bucket.id),
            user=users['bucket']))
    for perm in objects_perms:
        db.session.add(ActionUsers(
            action=perm.value,
            argument=str(bucket.id),
            user=users['objects']))
    db.session.commit()

    yield users


@pytest.fixture()
def client(client_api, users):
    """Create client."""
    with db_.session.begin_nested():
        # create resource_owner -> client_1
        client_ = Client(
            client_id='client_test_u1c1',
            client_secret='client_test_u1c1',
            name='client_test_u1c1',
            description='',
            is_confidential=False,
            user=users[0]['obj'],
            _redirect_uris='',
            _default_scopes='',
        )
        db_.session.add(client_)
    db_.session.commit()
    return client_


@pytest.fixture()
def create_token_user_1(client_api, client, users):
    """Create token."""
    with db_.session.begin_nested():
        token_ = Token(
            client=client,
            user=users[0]['obj'],
            token_type='u',
            access_token='dev_access_1',
            refresh_token='dev_refresh_1',
            expires=datetime.now() + timedelta(hours=10),
            is_personal=False,
            is_internal=True,
            _scopes=create_index_scope.id,
        )
        db_.session.add(token_)
    db_.session.commit()
    return token_

@pytest.fixture()
def create_token_user_noroleuser(client_api, client, users):
    """Create token."""
    with db_.session.begin_nested():
        token_ = Token(
            client=client,
            user=next((user for user in users if user["id"] == 9), None)['obj'],
            token_type='bearer',
            access_token='dev_access_create_token_user_noroleuser',
            # refresh_token='',
            expires=datetime.now() + timedelta(hours=10),
            is_personal=True,
            is_internal=False,
            _scopes="index:read",
        )
        db_.session.add(token_)
    db_.session.commit()
    return token_

@pytest.fixture()
def create_token_user_noroleuser_1(client_api, client, users):
    """Create token."""
    with db_.session.begin_nested():
        token_ = Token(
            client=client,
            user=next((user for user in users if user["id"] == 9), None)['obj'],
            token_type='bearer',
            access_token='dev_access_create_token_user_noroleuser_1',
            # refresh_token='',
            expires=datetime.now() + timedelta(hours=10),
            is_personal=True,
            is_internal=False,
            _scopes="index:update index:delete index:read index:create",
        )
        db_.session.add(token_)
    db_.session.commit()
    return token_

@pytest.fixture()
def create_token_user_sysadmin(client_api, client, users):
    """Create token."""
    with db_.session.begin_nested():
        token_ = Token(
            client=client,
            user=next((user for user in users if user["id"] == 5), None)['obj'],
            token_type='bearer',
            access_token='dev_access_create_token_user_sysadmin',
            # refresh_token='',
            expires=datetime.now() + timedelta(hours=10),
            is_personal=True,
            is_internal=False,
            _scopes="index:update index:delete index:read index:create",
        )
        db_.session.add(token_)
    db_.session.commit()
    return token_


@pytest.fixture()
def create_token_user_sysadmin_without_scope(client_api, client, users):
    """Create token."""
    with db_.session.begin_nested():
        token_ = Token(
            client=client,
            user=next((user for user in users if user["id"] == 5), None)['obj'],
            token_type='bearer',
            access_token='dev_access_create_token_user_sysadmin_without_scope',
            # refresh_token='',
            expires=datetime.now() + timedelta(hours=10),
            is_personal=True,
            is_internal=False,
            _scopes="",
        )
        db_.session.add(token_)
    db_.session.commit()
    return token_

@pytest.fixture()
def create_tokens(client_api, client, users):
    """Create tokens for users that exist in roles_scopes."""
    tokens = {}
    roles_scopes = {
        "noroleuser": "index:read",
        "contributor": "index:read",
        "repoadmin": "index:update index:delete index:read index:create",
        "sysadmin": "index:update index:delete index:read index:create",
        "comadmin": "index:update index:delete index:read index:create"
    }

    with db_.session.begin_nested():
        for user_data in users:
            role_name = user_data["email"].split("@")[0]

            if role_name not in roles_scopes:
                continue

            user_obj = user_data["obj"]
            access_token = f"dev_access_{role_name}"
            scopes = roles_scopes[role_name]

            token_ = Token(
                client=client,
                user=user_obj,
                token_type='bearer',
                access_token=access_token,
                expires=datetime.now() + timedelta(hours=10),
                is_personal=True,
                is_internal=False,
                _scopes=scopes,
            )
            db_.session.add(token_)
            tokens[role_name] = token_

    db_.session.commit()
    return tokens

@pytest.fixture()
def create_auth_headers(client_api, json_headers, create_tokens):
    """Generate authentication headers for each user role."""
    auth_headers = {}

    for role, token in create_tokens.items():
        auth_headers[role] = fill_oauth2_headers(json_headers, token)

    return auth_headers

@pytest.fixture()
def json_headers():
    """JSON headers."""
    return [('Content-Type', 'application/json'),
            ('Accept', 'application/json')]


@pytest.fixture()
def auth_headers(client_api, json_headers, create_token_user_1):
    """Authentication headers (with a valid oauth2 token).

    It uses the token associated with the first user.
    """
    return fill_oauth2_headers(json_headers, create_token_user_1)

@pytest.fixture()
def auth_headers_noroleuser_1(client_api, json_headers, create_token_user_noroleuser_1):
    """Authentication headers (with a valid oauth2 token).

    It uses the token associated with the first user.
    """
    return fill_oauth2_headers(json_headers, create_token_user_noroleuser_1)

@pytest.fixture()
def auth_headers_noroleuser(client_api, json_headers, create_token_user_noroleuser):
    """Authentication headers (with a valid oauth2 token).

    It uses the token associated with the first user.
    """
    return fill_oauth2_headers(json_headers, create_token_user_noroleuser)

@pytest.fixture()
def auth_headers_sysadmin_without_scope(client_api, json_headers, create_token_user_sysadmin_without_scope):
    """Authentication headers (with a valid oauth2 token).

    It uses the token associated with the first user.
    """
    return fill_oauth2_headers(json_headers, create_token_user_sysadmin_without_scope)

@pytest.fixture()
def auth_headers_sysadmin(client_api, json_headers, create_token_user_sysadmin):
    """Authentication headers (with a valid oauth2 token).

    It uses the token associated with the first user.
    """
    return fill_oauth2_headers(json_headers, create_token_user_sysadmin)

@pytest.fixture()
def admin_lang_setting(db):
    AdminLangSettings.create("en","English", True, 0, True)
    AdminLangSettings.create("ja","日本語", True, 1, True)
    AdminLangSettings.create("zh","中文", False, 0, True)


@pytest.fixture()
def index_thumbnail(app,instance_path):
    dir_path = os.path.join(instance_path,
    app.config['WEKO_THEME_INSTANCE_DATA_DIR'],'indextree')
    thumbnail_path = os.path.join(
                        dir_path,
                        "test_thumbnail.txt"
                    )
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)

    with open(thumbnail_path, "w") as f:
        f.write("test")

    return thumbnail_path


@pytest.fixture()
def community_for_api(db, users, indices_for_api):
    comm = Community(
        id='comm_for_api',
        id_user=users[4]['id'],
        title='Test Comm Title',
        root_node_id=indices_for_api['comm_index'].id,
        id_role=users[4]['obj'].roles[0].id,
        group_id=users[4]['obj'].roles[0].id
    )
    db.session.add(comm)
    db.session.commit()
