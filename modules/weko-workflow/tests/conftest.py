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

from copy import deepcopy
import os, sys
import shutil
import tempfile
import json
import uuid
from datetime import datetime
from six import BytesIO
import base64
from mock import patch

import pytest
from flask import Flask, session, url_for, Response
from flask_babelex import Babel, lazy_gettext as _
from flask_menu import Menu
from elasticsearch import Elasticsearch
from invenio_theme import InvenioTheme
from invenio_theme.views import blueprint as invenio_theme_blueprint
from invenio_assets import InvenioAssets
from invenio_access import InvenioAccess
from invenio_access.models import ActionUsers,ActionRoles
from invenio_accounts.testutils import create_test_user
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import User, Role
from invenio_accounts.views.settings import blueprint \
    as invenio_accounts_blueprint
from invenio_i18n import InvenioI18N
from invenio_cache import InvenioCache
from invenio_admin import InvenioAdmin
from invenio_admin.views import blueprint as invenio_admin_blueprint
from invenio_db import InvenioDB, db as db_
from invenio_stats import InvenioStats
from invenio_search import RecordsSearch,InvenioSearch
from invenio_communities import InvenioCommunities
from invenio_communities.views.ui import blueprint as invenio_communities_blueprint
from invenio_communities.models import Community
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_records_ui import InvenioRecordsUI
from weko_search_ui.config import WEKO_SYS_USER
from weko_records_ui import WekoRecordsUI
from weko_admin import WekoAdmin
from weko_admin.models import SessionLifetime,Identifier
from weko_admin.views import blueprint as weko_admin_blueprint
from weko_records.models import ItemTypeName, ItemType,FeedbackMailList,ItemTypeMapping,ItemTypeProperty
from weko_records.api import Mapping
from weko_records_ui.models import FilePermission
from weko_user_profiles import WekoUserProfiles
from weko_index_tree.models import Index
from weko_logging.audit import WekoLoggingUserActivity
from weko_workflow import WekoWorkflow
from weko_search_ui import WekoSearchUI
from weko_workflow.models import Activity, ActionStatus, Action, ActivityAction, WorkFlow, FlowDefine, FlowAction, ActionFeedbackMail, ActionIdentifier,FlowActionRole, ActivityHistory,GuestActivity, WorkflowRole
from weko_workflow.views import workflow_blueprint as weko_workflow_blueprint
from weko_workflow.config import WEKO_WORKFLOW_ACTION_START,WEKO_WORKFLOW_ACTION_END,WEKO_WORKFLOW_ACTION_ITEM_REGISTRATION,WEKO_WORKFLOW_ACTION_APPROVAL,WEKO_WORKFLOW_ACTION_ITEM_LINK,WEKO_WORKFLOW_ACTION_OA_POLICY_CONFIRMATION,WEKO_WORKFLOW_ACTION_IDENTIFIER_GRANT,WEKO_WORKFLOW_ACTION_ITEM_REGISTRATION_USAGE_APPLICATION,WEKO_WORKFLOW_ACTION_GUARANTOR,WEKO_WORKFLOW_ACTION_ADVISOR,WEKO_WORKFLOW_ACTION_ADMINISTRATOR,WEKO_WORKFLOW_ACTIVITYLOG_XLS_COLUMNS, DOI_VALIDATION_INFO, DOI_VALIDATION_INFO_CROSSREF, DOI_VALIDATION_INFO_DATACITE, DOI_VALIDATION_INFO_JALC
from weko_workflow.utils import generate_guest_activity_token_value
from weko_theme.views import blueprint as weko_theme_blueprint
from simplekv.memory.redisstore import RedisStore
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database
from tests.helpers import json_data, create_record, create_activity, create_flow
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy import event
from invenio_files_rest.models import Location, Bucket,ObjectVersion
from invenio_files_rest import InvenioFilesREST
from invenio_records import InvenioRecords
from invenio_oauth2server import InvenioOAuth2Server
from invenio_pidrelations import InvenioPIDRelations
from invenio_pidstore import InvenioPIDStore
from weko_index_tree.api import Indexes
from kombu import Exchange, Queue
from weko_index_tree.models import Index
from weko_schema_ui.models import OAIServerSchema
from weko_schema_ui.config import WEKO_SCHEMA_JPCOAR_V1_SCHEMA_NAME,WEKO_SCHEMA_DDI_SCHEMA_NAME
from weko_index_tree.config import WEKO_INDEX_TREE_REST_ENDPOINTS,WEKO_INDEX_TREE_DEFAULT_DISPLAY_NUMBER
from weko_user_profiles.models import UserProfile
from weko_user_profiles.config import WEKO_USERPROFILES_ROLES,WEKO_USERPROFILES_GENERAL_ROLE
from weko_authors.models import Authors
from invenio_records_files.api import RecordsBuckets
from weko_redis.redis import RedisConnection
from weko_items_ui import WekoItemsUI
from weko_admin.models import SiteInfo
from weko_admin import WekoAdmin
from weko_deposit import WekoDeposit
from weko_admin.models import AdminSettings
from weko_notifications.models import NotificationsUserSettings

sys.path.append(os.path.dirname(__file__))
# @event.listens_for(Engine, "connect")
# def set_sqlite_pragma(dbapi_connection, connection_record):
#     cursor = dbapi_connection.cursor()
#     cursor.execute("PRAGMA foreign_keys=OFF;")
#     cursor.close()

# @event.listens_for(Session, 'after_begin')
# def receive_after_begin(session, transaction, connection):
#     connection.execute("PRAGMA foreign_keys=OFF;")
class TestSearch(RecordsSearch):
    """Test record search."""

    class Meta:
        """Test configuration."""

        index = 'invenio-records-rest'
        doc_types = None

    def __init__(self, **kwargs):
        """Add extra options."""
        super(TestSearch, self).__init__(**kwargs)
        self._extra.update(**{'_source': {'excludes': ['_access']}})

@pytest.yield_fixture(scope='session')
def search_class():
    """Search class."""
    yield TestSearch

@pytest.yield_fixture()
def instance_path():
    """Temporary instance path."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)

class MockEs():
    def __init__(self,**keywargs):
        self.indices = self.MockIndices()
        self.es = Elasticsearch()
        self.cluster = self.MockCluster()
    def index(self, id="",version="",version_type="",index="",doc_type="",body="",**arguments):
        pass
    def delete(self,id="",index="",doc_type="",**kwargs):
        return Response(response=json.dumps({}),status=500)
    @property
    def transport(self):
        return self.es.transport
    class MockIndices():
        def __init__(self,**keywargs):
            self.mapping = dict()
        def delete(self,index="", ignore=""):
            pass
        def delete_template(self,index=""):
            pass
        def create(self,index="",body={},ignore=""):
            self.mapping[index] = body
        def put_alias(self,index="", name="", ignore=""):
            pass
        def put_template(self,name="", body={}, ignore=""):
            pass
        def refresh(self,index=""):
            pass
        def exists(self, index="", **kwargs):
            if index in self.mapping:
                return True
            else:
                return False
        def flush(self,index="",wait_if_ongoing=""):
            pass
        def delete_alias(self, index="", name="",ignore=""):
            pass

        # def search(self,index="",doc_type="",body={},**kwargs):
        #     pass
    class MockCluster():
        def __init__(self,**kwargs):
            pass
        def health(self, wait_for_status="", request_timeout=0):
            pass

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
def admin_settings(db):
    settings = list()
    settings.append(AdminSettings(id=1,name='workspace_workflow_settings',settings={ "item_type_id": "30002",
                            "work_flow_id": "1", "workFlow_select_flg":"1"}))
    db.session.add_all(settings)
    db.session.commit()
    return settings


@pytest.fixture()
def base_app(instance_path, search_class, cache_config):
    """Flask application fixture."""
    app_ = Flask('testapp', instance_path=instance_path)
    app_.config.update(
        SECRET_KEY='SECRET_KEY',
        TESTING=True,
        SERVER_NAME='TEST_SERVER.localdomain',
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                           'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        ACCOUNTS_USERINFO_HEADERS=True,
        WEKO_PERMISSION_SUPER_ROLE_USER=['System Administrator',
                                         'Repository Administrator'],
        WEKO_PERMISSION_ROLE_COMMUNITY=['Community Administrator'],
        THEME_SITEURL = 'https://localhost',
        CACHE_REDIS_URL='redis://redis:6379/0',
        CACHE_REDIS_DB='0',
        CACHE_REDIS_HOST="redis",
        REDIS_PORT='6379',
        ACCOUNTS_SESSION_REDIS_DB_NO = 1,
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
        WEKO_ITEMS_UI_MS_MIME_TYPE = {
            'ms_word': ['application/msword',
                        'application/vnd.openxmlformats-officedocument.'
                        'wordprocessingml.document',
                        'application/vnd.openxmlformats-officedocument.'
                        'wordprocessingml.template',
                        'application/vnd.ms-word.document.macroEnabled.12',
                        'application/vnd.ms-word.template.macroEnabled.12'
                        ],
            'ms_powerpoint': ['application/vnd.ms-powerpoint',
                              'application/vnd.openxmlformats-officedocument.'
                              'presentationml.presentation',
                              'application/vnd.openxmlformats-officedocument.'
                              'presentationml.template',
                              'application/vnd.openxmlformats-officedocument.'
                              'presentationml.slideshow',
                              'application/vnd.ms-powerpoint.addin.macroEnabled.12',
                              'application/vnd.ms-powerpoint.presentation.'
                              'macroEnabled.12',
                              'applcation/vnd.ms-powerpoint.template.macroEnabled.12',
                              'application/vnd.ms-powerpoint.slideshow.macroEnabled.12'
                              ],
            'ms_excel': ['application/vnd.ms-excel',
                         'application/vnd.openxmlformats-officedocument.'
                         'spreadsheetml.sheet',
                         'application/vnd.openxmlformats-officedocument.'
                         'spreadsheetml.template',
                         'application/vnd.ms-excel.sheet.macroEnabled.12',
                         'application/vnd.ms-excel.template.macroEnabled.12',
                         'application/vnd.ms-excel.addin.macroEnabled.12',
                         'application/vnd.ms-excel.sheet.binary.macroEnabled.12']
        },
        WEKO_ITEMS_UI_FILE_SISE_PREVIEW_LIMIT = {
            'ms_word': 30,
            'ms_powerpoint': 20,
            'ms_excel': 10
        },
        WEKO_ITEMS_UI_OUTPUT_REGISTRATION_TITLE="",
        WEKO_ITEMS_UI_MULTIPLE_APPROVALS=True,
        WEKO_THEME_DEFAULT_COMMUNITY="Root Index",
        DEPOSIT_DEFAULT_STORAGE_CLASS = 'S',
        WEKO_USERPROFILES_ROLES=[
            'Administrator','General','Graduated Student','Student'
        ],
        WEKO_ITEMS_UI_USAGE_APPLICATION_ITEM_TYPES_LIST = [],
        WEKO_HANDLE_ALLOW_REGISTER_CNRI=True,
        I18N_LANGUAGES=[("ja","Japanese"), ("en","English")],
        WEKO_BUCKET_QUOTA_SIZE=50 * 1024 * 1024 * 1024,
        WEKO_MAX_FILE_SIZE=50 * 1024 * 1024 * 1024,
        SEARCH_UI_SEARCH_INDEX="test-weko",
        INDEXER_DEFAULT_DOCTYPE="item-v1.0.0",
        INDEXER_FILE_DOC_TYPE="content",
        INDEXER_DEFAULT_DOC_TYPE='testrecord',
        INDEXER_DEFAULT_INDEX=search_class.Meta.index,
        WEKO_SCHEMA_JPCOAR_V1_SCHEMA_NAME=WEKO_SCHEMA_JPCOAR_V1_SCHEMA_NAME,
        WEKO_SCHEMA_JPCOAR_V2_SCHEMA_NAME='jpcoar_mapping',
        WEKO_SCHEMA_JPCOAR_V2_RESOURCE_TYPE_REPLACE={
            'periodical':'journal',
            'interview':'other',
            'internal report':'other',
            'report part':'other',
        },
        WEKO_SCHEMA_DDI_SCHEMA_NAME=WEKO_SCHEMA_DDI_SCHEMA_NAME,
        DEPOSIT_DEFAULT_JSONSCHEMA = 'deposits/deposit-v1.0.0.json',
        WEKO_RECORDS_UI_SECRET_KEY = "secret",
        WEKO_RECORDS_UI_ONETIME_DOWNLOAD_PATTERN = "filename={} record_id={} user_mail={} date={}",
        WEKO_WORKFLOW_ACTION_START=WEKO_WORKFLOW_ACTION_START,
        WEKO_WORKFLOW_ACTION_END=WEKO_WORKFLOW_ACTION_END,
        WEKO_WORKFLOW_ACTION_ITEM_REGISTRATION=WEKO_WORKFLOW_ACTION_ITEM_REGISTRATION,
        WEKO_WORKFLOW_ACTION_APPROVAL=WEKO_WORKFLOW_ACTION_APPROVAL,
        WEKO_WORKFLOW_ACTION_ITEM_LINK=WEKO_WORKFLOW_ACTION_ITEM_LINK,
        WEKO_WORKFLOW_ACTION_OA_POLICY_CONFIRMATION=WEKO_WORKFLOW_ACTION_OA_POLICY_CONFIRMATION,
        WEKO_WORKFLOW_ACTION_IDENTIFIER_GRANT=WEKO_WORKFLOW_ACTION_IDENTIFIER_GRANT,
        WEKO_WORKFLOW_ACTION_ITEM_REGISTRATION_USAGE_APPLICATION=WEKO_WORKFLOW_ACTION_ITEM_REGISTRATION_USAGE_APPLICATION,
        WEKO_WORKFLOW_ACTION_GUARANTOR=WEKO_WORKFLOW_ACTION_GUARANTOR,
        WEKO_WORKFLOW_ACTION_ADVISOR=WEKO_WORKFLOW_ACTION_ADVISOR,
        WEKO_WORKFLOW_ACTION_ADMINISTRATOR=WEKO_WORKFLOW_ACTION_ADMINISTRATOR,
        WEKO_WORKFLOW_GAKUNINRDM_DATA=[
            {
                'workflow_id': -1,
                'workflow_name': 'GRDM_デフォルトワークフロー',
                'item_type_id': 1,
                'flow_id': -1,
                'flow_name': 'GRDM_デフォルトフロー',
                'action_endpoint_list': [
                    'begin_action',
                    'item_login',
                    'item_link',
                    'identifier_grant',
                    'approval',
                    'end_action'
                ]
            }
        ],
        DELETE_ACTIVITY_LOG_ENABLE=True,
        WEKO_WORKFLOW_ACTIVITYLOG_XLS_COLUMNS=WEKO_WORKFLOW_ACTIVITYLOG_XLS_COLUMNS,
        WEKO_SYS_USER=WEKO_SYS_USER,
        RECORDS_UI_ENDPOINTS=dict(
            # recid=dict(
            #     pid_type='recid',
            #     route='/records/<pid_value>',
            #     template='invenio_records_ui/detail.html',
            # ),
            # recid_previewer=dict(
            #     pid_type='recid',
            #     route='/records/<pid_value>/preview/<filename>',
            #     view_imp='invenio_previewer.views:preview',
            #     record_class='invenio_records_files.api:Record',
            # ),
            recid_files=dict(
                pid_type='recid',
                route='/record/<pid_value>/files/<filename>',
                view_imp='invenio_records_files.utils.file_download_ui',
                record_class='invenio_records_files.api:Record',
            ),
        ),
        DOI_VALIDATION_INFO_JALC=DOI_VALIDATION_INFO_JALC,
        WEKO_WORKFLOW_IDENTIFIER_GRANT_IS_WITHDRAWING = -2,
    )

    app_.testing = True
    Babel(app_)
    InvenioI18N(app_)
    Menu(app_)
    # InvenioTheme(app_)
    InvenioAccess(app_)
    InvenioAccounts(app_)
    InvenioFilesREST(app_)
    InvenioCache(app_)
    InvenioDB(app_)
    InvenioStats(app_)
    InvenioAssets(app_)
    InvenioAdmin(app_)
    InvenioPIDRelations(app_)
    InvenioJSONSchemas(app_)
    InvenioPIDStore(app_)
    InvenioRecords(app_)
    InvenioRecordsUI(app_)
    WekoRecordsUI(app_)
    search = InvenioSearch(app_, client=MockEs())
    search.register_mappings(search_class.Meta.index, 'mock_module.mappings')
    # InvenioCommunities(app_)
    # WekoAdmin(app_)
    WekoSearchUI(app_)
    WekoWorkflow(app_)
    WekoUserProfiles(app_)
    WekoDeposit(app_)
    WekoItemsUI(app_)
    WekoAdmin(app_)
    InvenioOAuth2Server(app_)
    # WekoRecordsUI(app_)
    # app_.register_blueprint(invenio_theme_blueprint)
    app_.register_blueprint(invenio_communities_blueprint)
    # app_.register_blueprint(invenio_admin_blueprint)
    # app_.register_blueprint(invenio_accounts_blueprint)
    # app_.register_blueprint(weko_theme_blueprint)
    # app_.register_blueprint(weko_admin_blueprint)
    app_.register_blueprint(weko_workflow_blueprint)

    return app_


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
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
    drop_database(str(db_.engine.url))

@pytest.yield_fixture()
def logging_client(app):
    """make a test client.
    Args:
        app (Flask): flask app.
    Yields:
        FlaskClient: test client
    """
    test = WekoLoggingUserActivity()
    test.init_app(app)
    yield app

@pytest.yield_fixture()
def client(app):
    """make a test client.
    Args:
        app (Flask): flask app.
    Yields:
        FlaskClient: test client
    """
    with app.test_client() as client:
        yield client

@pytest.yield_fixture()
def guest(client):
    with client.session_transaction() as sess:
        sess['guest_token'] = "test_guest_token"
        sess['guest_email'] = "guest@test.org"
        sess['guest_url'] = url_for("weko_workflow.display_guest_activity",file_name="test_file")
    yield client

@pytest.yield_fixture()
def req_context(client,app):
    with app.test_request_context():
        yield client

@pytest.fixture
def redis_connect(app):
    redis_connection = RedisConnection().connection(db=app.config['CACHE_REDIS_DB'], kv = True)
    redis_connection.put('updated_json_schema_A-00000001-10001',bytes('test', 'utf-8'))
    return redis_connection

@pytest.fixture()
def without_remove_session(app):
    with patch("weko_workflow.views.db.session.remove"):
        yield

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
                            root_node_id=index.id,
                            group_id=comadmin_role.id)
    db.session.commit()
    return [
        {'email': contributor.email, 'id': contributor.id, 'obj': contributor},
        {'email': repoadmin.email, 'id': repoadmin.id, 'obj': repoadmin},
        {'email': sysadmin.email, 'id': sysadmin.id, 'obj': sysadmin},
        {'email': comadmin.email, 'id': comadmin.id, 'obj': comadmin},
        {'email': generaluser.email, 'id': generaluser.id, 'obj': generaluser},
        {'email': originalroleuser.email, 'id': originalroleuser.id, 'obj': originalroleuser},
        {'email': originalroleuser2.email, 'id': originalroleuser2.id, 'obj': originalroleuser2},
        {'email': user.email, 'id': user.id, 'obj': user},
        {'email': student.email,'id': student.id, 'obj': student}
    ]

@pytest.fixture()
def activity_acl_users(app, db):
    ds = app.extensions['invenio-accounts'].datastore

    sysadmin_role = ds.create_role(name='System Administrator')
    repoadmin_role = ds.create_role(name='Repository Administrator')
    comadmin_role = ds.create_role(name='Community Administrator')
    test_role01 = ds.create_role(name='test_role01')
    test_role02 = ds.create_role(name='test_role02')
    test_role03 = ds.create_role(name='test_role03')

    sysadmin = create_test_user(email='sysadmin@test.org')
    repoadmin = create_test_user(email='repoadmin@test.org')
    test_role01_user = create_test_user(email='test_role01_user@test.org')
    test_role01_comadmin = create_test_user(email='test_role01_comadmin@test.org')
    test_role02_user = create_test_user(email='test_role02_user@test.org')
    test_role03_comadmin = create_test_user(email='test_role03_comadmin@test.org')
    no_role_user = create_test_user(email='no_role@test.org')

    ds.add_role_to_user(sysadmin,sysadmin_role)
    ds.add_role_to_user(repoadmin, repoadmin_role)
    ds.add_role_to_user(test_role01_user,test_role01)
    ds.add_role_to_user(test_role01_comadmin,test_role01)
    ds.add_role_to_user(test_role01_comadmin,comadmin_role)
    ds.add_role_to_user(test_role02_user,test_role02)
    ds.add_role_to_user(test_role03_comadmin, test_role03)
    ds.add_role_to_user(test_role03_comadmin, comadmin_role)

    """
    root
      ┣━ com_index
      ┃     ┣━ com_index_child01
      ┃     ┗━ com_index_child02
      ┗━ not_com_index
    """
    indexes = [
        Index(id=1,parent=0,position=0,index_name="com_index",display_no=5,public_state=True),
        Index(id=2,parent=1,position=0,index_name="com_index_child01",display_no=5,public_state=True),
        Index(id=3,parent=1,position=1,index_name="com_index_child02",display_no=5,public_state=True),
        Index(id=4,parent=0,position=1,index_name="not_com_index",display_no=5,public_state=True)
    ]
    db.session.add_all(indexes)
    db.session.commit()

    test_role01_com = Community.create(community_id="test_role01_com", role_id=test_role01.id,
                            id_user=sysadmin.id, title="test community",
                            description=("this is test community"),
                            root_node_id=indexes[0].id)
    db.session.commit()
    return {
        "users":[sysadmin, repoadmin, test_role01_user, test_role01_comadmin, test_role02_user, test_role03_comadmin, no_role_user],
        "roles":[sysadmin_role, repoadmin_role, comadmin_role, test_role01, test_role02, test_role03],
        "indexes": indexes,
        "comunities":[test_role01_com]
    }

@pytest.fixture()
def workflow_with_action_role(db, action_data, item_type, activity_acl_users):

    users = activity_acl_users["users"]
    roles = activity_acl_users["roles"]

    workflows = []
    # no set action role(user)
    workflows.append(create_flow(db, 1, "normal_flow","normal_workflow", None, None, item_type))

    # action_role of action with action_id 1 is test_role01
    workflows.append(create_flow(db, 2, "test_role01_role_flow","test_role01_role_workfow",{5:{"value":roles[3].id,"flg":False}},None, item_type))

    # action_role of action with action_id 1 is test_role02
    workflows.append(create_flow(db, 3, "test_role02_role_flow","test_role02_role_workfow",{5:{"value":roles[4].id,"flg":False}},None,item_type))

    # action_role of action with action_id 1 is test_role01 and deny
    workflows.append(create_flow(db, 4, "test_role01_role_deny_flow","test_role01_role_deny_workfow",{5:{"value":roles[3].id,"flg":True}},None,item_type))

    # action_role of action with action_id 1 is test_role02 and deny
    workflows.append(create_flow(db, 5, "test_role02_role_deny_flow","test_role02_role_deny_workfow",{5:{"value":roles[4].id,"flg":True}},None,item_type))

    # action_user of action with action_id 1 is test_role01_user
    workflows.append(create_flow(db, 6,"test_role01_user_flow","test_role01_user_workflow",None,{5:{"value":users[2].id,"flg":False}},item_type))

    # action_user of action with action_id 1 is test_role02_user
    workflows.append(create_flow(db, 7,"test_role02_user_flow","test_role02_user_workflow",None,{5:{"value":users[4].id,"flg":False}},item_type))

    # action_user of action with action_id 1 is test_role01_user and deny
    workflows.append(create_flow(db, 8,"test_role01_user_deny_flow","test_role01_user_deny_workflow",None,{5:{"value":users[2].id,"flg":True}},item_type))

    # action_user of action with action_id 1 is test_role02_user and deny
    workflows.append(create_flow(db, 9,"test_role02_user_deny_flow","test_role02_user_deny_workflow",None,{5:{"value":users[4].id,"flg":True}},item_type))
    return workflows


@pytest.fixture()
def activity_acl(db, workflow_with_action_role, activity_acl_users):
    users = activity_acl_users["users"]
    workflows = workflow_with_action_role
    activites = [
        create_activity(db,"sysadmin_入力待ち",1,["4"],users[0],-1,workflows[0],'M',3),
        create_activity(db,"sysadmin_承認待ち",2,["4"],users[0],-1,workflows[0],'M',4),
        create_activity(db,"sysadmin_キャンセル",3,["4"],users[0],-1,workflows[0],'C',3),
        create_activity(db,"sysadmin_完了",4,["4"],users[0],-1,workflows[0],'F',5),
        create_activity(db,"sysadmin_入力中_actionrole(test_role01)",5,["4"],users[0],-1,workflows[1],'M',3),
        create_activity(db,"test_role01_comadmin_入力中_権限内",6,["2"],users[3],-1,workflows[0],'M',3),
        create_activity(db,"test_role01_comadmin_承認待ち_権限内",7,["2"],users[3],-1,workflows[0],'M',4),
        create_activity(db,"test_role01_comadmin_キャンセル_権限内",8,["2"],users[3],-1,workflows[0],'C',3),
        create_activity(db,"test_role01_comadmin_完了_権限内",9,["2"],users[3],-1,workflows[0],'F',5),
        create_activity(db,"test_role01_comadmin_入力中_権限内_actionrole(test_role02)",10,["2"],users[3],-1,workflows[2],'M',3),
        create_activity(db,"test_role01_comadmin_入力中_権限内_!actionrole(test_role01)",11,["2"],users[3],-1,workflows[3],'M',3),
        create_activity(db,"test_role01_comadmin_入力中_権限外",12,["4"],users[3],-1,workflows[0],'M',3),
        create_activity(db,"test_role01_comadmin_承認待ち_権限外",13,["4"],users[3],-1,workflows[0],'M',4),
        create_activity(db,"test_role01_comadmin_入力中_権限外_actionrole(test_role01)",14,["4"],users[3],-1,workflows[1],'M',3),
        create_activity(db,"test_role01_comadmin_入力中_権限外_actionrole(test_role02)",15,["4"],users[3],-1,workflows[2],'M',3),
        create_activity(db,"test_role01_comadmin_入力中_権限外_代理(test_role01_user)",16,["4"],users[3],3,workflows[0],'M',3),
        create_activity(db,"test_role01_comadmin_承認待ち_権限外_代理(test_role01_user)",17,["4"],users[3],3,workflows[0],'M',4),
        create_activity(db,"test_role01_comadmin_入力中_権限外_actionrole(test_role01)_代理(test_role01_user)",18,["4"],users[3],3,workflows[1],'M',3),
        create_activity(db,"test_role01_comadmin_入力中_権限外_actionrole(test_role02)_代理(test_role01_user)",19,["4"],users[3],3,workflows[2],'M',3),
        create_activity(db,"test_role01_comadmin_入力中_権限外_!actionrole(test_role01)",20,["4"],users[3],-1,workflows[3],'M',3),
        create_activity(db,"test_role01_comadmin_入力中_権限外_!actionrole(test_role01)_代理(test_role01_user)",21,["4"],users[3],3,workflows[3],'M',3),
        create_activity(db,"test_role01_user_入力中_権限内",22,["2"],users[2],-1,workflows[0],'M',3),
        create_activity(db,"test_role01_user_承認待ち_権限内",23,["2"],users[2],-1,workflows[0],'M',4),
        create_activity(db,"test_role01_user_キャンセル_権限内",24,["2"],users[2],-1,workflows[0],'C',3),
        create_activity(db,"test_role01_user_完了_権限内",25,["2"],users[2],-1,workflows[0],'F',5),
        create_activity(db,"test_role01_user_入力中_権限内_!actionrole(test_role01)",26,["2"],users[2],-1,workflows[3],'M',3),
        create_activity(db,"test_role01_user_入力中_権限外",27,["4"],users[2],-1,workflows[0],'M',3),
        create_activity(db,"test_role01_user_承認待ち_権限外",28,["4"],users[2],-1,workflows[0],'M',4),
        create_activity(db,"test_role01_user_キャンセル_権限外",29,["4"],users[2],-1,workflows[0],'C',3),
        create_activity(db,"test_role01_user_完了_権限外",30,["4"],users[2],-1,workflows[0],'F',5),
        create_activity(db,"test_role01_user_入力中_権限外_index未選択",31,[],users[2],-1,workflows[0],'M',2),
        create_activity(db,"test_role01_user_入力中_権限外_index未選択_代理(test_role01_comadmin)",32,[],users[2],4,workflows[0],'M',2),
        create_activity(db,"test_role01_user_入力前_権限外",33,None,users[2],-1,workflows[0],'M',2),
        create_activity(db,"test_role01_user_入力中_権限外_actionrole(test_role01)",34,["4"],users[2],-1,workflows[1],'M',3),
        create_activity(db,"test_role01_user_入力中_権限外_actionrole(test_role02)",35,["4"],users[2],-1,workflows[2],'M',3),
        create_activity(db,"test_role01_user_入力中_権限外_!actionrole(test_role01)",36,["4"],users[2],-1,workflows[3],'M',3),
        create_activity(db,"test_role01_user_入力中_権限外_!actionrole(test_role02)",37,["4"],users[2],-1,workflows[4],'M',3),
        create_activity(db,"test_role01_user_入力中_権限外_代理(test_role01_comadmin)",38,["4"],users[2],4,workflows[0],'M',3),
        create_activity(db,"test_role01_user_承認待ち_権限外_代理(test_role01_comadmin)",39,["4"],users[2],4,workflows[0],'M',4),
        create_activity(db,"test_role01_user_入力中_権限外_actionrole(test_role02)_代理(test_role01_comadmin)",40,["4"],users[2],4,workflows[2],'M',3),
        create_activity(db,"test_role01_user_入力中_権限外_!actionrole(test_role01)_代理(test_role01_comadmin)",41,["4"],users[2],4,workflows[3],'M',3),
        create_activity(db,"test_role01_user_入力中_権限内+外",42,["2","4"],users[2],-1,workflows[0],'M',3),
        create_activity(db,"test_role03_comadmin_入力中_com所属なし",43,["2"],users[5],-1,workflows[0],'M',3),

    ]

    return activites



@pytest.fixture()
def action_data(db):
    action_datas=dict()
    with open('tests/data/actions.json', 'r') as f:
        action_datas = json.load(f)
    actions_db = list()
    with db.session.begin_nested():
        for data in action_datas:
            actions_db.append(Action(**data))
        db.session.add_all(actions_db)
    db.session.commit()

    actionstatus_datas = dict()
    with open('tests/data/action_status.json') as f:
        actionstatus_datas = json.load(f)
    actionstatus_db = list()
    with db.session.begin_nested():
        for data in actionstatus_datas:
            actionstatus_db.append(ActionStatus(**data))
        db.session.add_all(actionstatus_db)
    db.session.commit()
    return actions_db, actionstatus_db

@pytest.fixture()
def db_itemtype(app, db):
    item_type_name = ItemTypeName(id=1,
        name="テストアイテムタイプ", has_site_license=True, is_active=True
    )
    item_type_schema = dict()
    with open("tests/data/itemtype_schema.json", "r") as f:
        item_type_schema = json.load(f)

    item_type_form = dict()
    with open("tests/data/itemtype_form.json", "r") as f:
        item_type_form = json.load(f)

    item_type_render = dict()
    with open("tests/data/itemtype_render.json", "r") as f:
        item_type_render = json.load(f)

    item_type_mapping = dict()
    with open("tests/data/itemtype_mapping.json", "r") as f:
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

    item_type_mapping = ItemTypeMapping(id=1,item_type_id=1, mapping=item_type_mapping)

    with db.session.begin_nested():
        db.session.add(item_type_name)
        db.session.add(item_type)
        db.session.add(item_type_mapping)

    return {"item_type_name": item_type_name, "item_type": item_type, "item_type_mapping":item_type_mapping}


@pytest.fixture()
def db_itemtype2(app, db):
    item_type_name = ItemTypeName(id=15,
        name="テストアイテムタイプ2", has_site_license=True, is_active=True
    )
    item_type_schema = dict()
    with open("tests/data/itemtype_schema.json", "r") as f:
        item_type_schema = json.load(f)

    item_type_form = dict()
    with open("tests/data/itemtype_form.json", "r") as f:
        item_type_form = json.load(f)

    item_type_render = dict()
    with open("tests/data/itemtype_render.json", "r") as f:
        item_type_render = json.load(f)

    item_type_mapping = dict()
    with open("tests/data/itemtype_mapping.json", "r") as f:
        item_type_mapping = json.load(f)

    item_type = ItemType(
        id=15,
        name_id=15,
        harvesting_type=True,
        schema=item_type_schema,
        form=item_type_form,
        render=item_type_render,
        tag=1,
        version_id=1,
        is_deleted=False,
    )

    item_type_mapping = ItemTypeMapping(id=15,item_type_id=15, mapping=item_type_mapping)

    with db.session.begin_nested():
        db.session.add(item_type_name)
        db.session.add(item_type)
        db.session.add(item_type_mapping)

    return {"item_type_name": item_type_name, "item_type": item_type, "item_type_mapping":item_type_mapping}


@pytest.fixture()
def item_type(db):
    item_type_name = ItemTypeName(name='テストアイテムタイプ',
                                  has_site_license=True,
                                  is_active=True)
    with db.session.begin_nested():
        db.session.add(item_type_name)
    item_type = ItemType(name_id=1,harvesting_type=True,
                         schema=json_data("data/item_type/15_schema.json"),
                         form=json_data("data/item_type/15_form.json"),
                         render=json_data("data/item_type/15_render.json"),
                         tag=1,version_id=1,is_deleted=False)
    itemtype_property_data = json_data("data/itemtype_properties.json")[0]
    item_type_property = ItemTypeProperty(
        name=itemtype_property_data["name"],
        schema=itemtype_property_data["schema"],
        form=itemtype_property_data["form"],
        forms=itemtype_property_data["forms"],
        delflg=False
    )
    with db.session.begin_nested():
        db.session.add(item_type)
        db.session.add(item_type_property)
    mappin = Mapping.create(
        item_type.id,
        mapping = json_data("data/item_type/item_type_mapping.json")
    )
    db.session.commit()
    return item_type

@pytest.fixture()
def identifier(db):
    doi_identifier = Identifier(id=1, repository='Root Index',jalc_flag= True,jalc_crossref_flag= True,jalc_datacite_flag=True,ndl_jalc_flag=True,
        jalc_doi='123',jalc_crossref_doi='1234',jalc_datacite_doi='12345',ndl_jalc_doi='123456',suffix='def',
        created_userId='1',created_date=datetime.strptime('2022-09-28 04:33:42','%Y-%m-%d %H:%M:%S'),
        updated_userId='1',updated_date=datetime.strptime('2022-09-28 04:33:42','%Y-%m-%d %H:%M:%S')
    )
    db.session.add(doi_identifier)
    db.session.commit()
    return doi_identifier

@pytest.fixture()
def db_register(app, db, db_records, users, action_data, item_type):
    flow_define = FlowDefine(flow_id=uuid.uuid4(),
                             flow_name='Registration Flow',
                             flow_user=1)
    del_flow_define = FlowDefine(flow_id=uuid.uuid4(),
                                flow_name='Delete Flow',
                                flow_user=1,
                                flow_type='2')
    app_flow_define = FlowDefine(flow_id=uuid.uuid4(),
                                flow_name='Delete Approval Flow',
                                flow_user=1,
                                flow_type='2')
    with db.session.begin_nested():
        db.session.add(flow_define)
        db.session.add(del_flow_define)
        db.session.add(app_flow_define)
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
    del_flow_action1 = FlowAction(status='N',
                     flow_id=del_flow_define.flow_id,
                     action_id=1,
                     action_version='1.0.0',
                     action_order=1,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2025/05/01 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={})
    del_flow_action2 = FlowAction(status='N',
                     flow_id=del_flow_define.flow_id,
                     action_id=2,
                     action_version='1.0.0',
                     action_order=2,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2025/05/01 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={})
    app_flow_action1 = FlowAction(status='N',
                     flow_id=app_flow_define.flow_id,
                     action_id=1,
                     action_version='1.0.0',
                     action_order=1,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2025/05/01 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={})
    app_flow_action2 = FlowAction(status='N',
                     flow_id=app_flow_define.flow_id,
                     action_id=4,
                     action_version='1.0.0',
                     action_order=2,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2025/05/01 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={})
    app_flow_action3 = FlowAction(status='N',
                     flow_id=app_flow_define.flow_id,
                     action_id=2,
                     action_version='1.0.0',
                     action_order=3,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2025/05/01 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={})

    with db.session.begin_nested():
        db.session.add(flow_action1)
        db.session.add(flow_action2)
        db.session.add(flow_action3)
        db.session.add(del_flow_action1)
        db.session.add(del_flow_action2)
        db.session.add(app_flow_action1)
        db.session.add(app_flow_action2)
        db.session.add(app_flow_action3)
    db.session.commit()
    workflow = WorkFlow(flows_id=uuid.uuid4(),
                        flows_name='test workflow1',
                        itemtype_id=1,
                        index_tree_id=None,
                        flow_id=1,
                        is_deleted=False,
                        open_restricted=False,
                        location_id=None,
                        is_gakuninrdm=False)
    del_workflow = WorkFlow(flows_id=uuid.uuid4(),
                        flows_name='test delete workflow',
                        itemtype_id=1,
                        index_tree_id=None,
                        flow_id=1,
                        delete_flow_id=del_flow_define.id,
                        is_deleted=False,
                        open_restricted=False,
                        location_id=None,
                        is_gakuninrdm=False)
    app_del_workflow = WorkFlow(flows_id=uuid.uuid4(),
                        flows_name='test delete approval workflow',
                        itemtype_id=1,
                        index_tree_id=None,
                        flow_id=1,
                        delete_flow_id=app_flow_define.id,
                        is_deleted=False,
                        open_restricted=False,
                        location_id=None,
                        is_gakuninrdm=False)
    activity = Activity(activity_id='1',workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=1,
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_id=-1, extra_info={},
                    action_order=1,
                    )
    activity2 = Activity(activity_id='A-00000001-10001',workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=1,
                    action_status = 'M',
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_id=-1, extra_info={},
                    action_order=6)

    activity3 = Activity(activity_id='A-00000001-10002',workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=1,
                    action_status = 'C',
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_id=-1, extra_info={},
                    action_order=6)
    del_activity = Activity(activity_id='A-00000001-10010',workflow_id=2, flow_id=del_flow_define.id,
                    action_id=1, activity_login_user=1,
                    activity_update_user=1,
                    activity_start=datetime.strptime('2025/05/02 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_id=-1, extra_info={},
                    action_order=1,
                    )
    app_del_activity = Activity(activity_id='A-00000001-10011',workflow_id=3, flow_id=app_flow_define.id,
                    action_id=1, activity_login_user=1,
                    activity_update_user=1,
                    activity_start=datetime.strptime('2025/05/02 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_id=-1, extra_info={},
                    action_order=1,
                    )
    activity_item1 = Activity(activity_id='2',item_id=db_records[2][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item1', shared_user_id=-1, extra_info={},
                    action_order=1,
                    )
    activity_item2 = Activity(activity_id='3', workflow_id=1, flow_id=flow_define.id,
                    action_id=3, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item2', shared_user_id=-1, extra_info={},
                    action_order=1,
                    )
    activity_item3 = Activity(activity_id='4', workflow_id=1, flow_id=flow_define.id,
                    action_id=3, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item3', shared_user_id=-1, extra_info={},
                    action_order=1,
                    )
    activity_item4 = Activity(activity_id='5', workflow_id=1, flow_id=flow_define.id,
                    action_id=3, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item4', shared_user_id=-1, extra_info={},
                    action_order=1,
                    )
    activity_item5 = Activity(activity_id='6', workflow_id=1, flow_id=flow_define.id,
                    action_id=3, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item5', shared_user_id=-1, extra_info={},
                    action_order=1,
                    )
    activity_item6 = Activity(activity_id='7', workflow_id=1, flow_id=flow_define.id,
                    action_id=3, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item5', shared_user_id=-1, extra_info={},
                    action_order=1,
                    )
    activity_item7 = Activity(activity_id='8', item_id=db_records[0][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=3, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item8', shared_user_id=-1, extra_info={},
                    action_order=1,
                    )
    activity_item8 = Activity(activity_id='9', item_id=db_records[1][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=3, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item8', shared_user_id=-1, extra_info={},
                    action_order=1,
                    )
    activity_guest = Activity(activity_id='guest', item_id=db_records[1][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=3, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item8', shared_user_id=-1,
                    action_order=1,
                    extra_info={"guest_mail":"guest@test.org","related_title":"related_guest_activity","usage_record_id":str(db_records[1][2].id),"usage_activity_id":str(uuid.uuid4())}
                    )
    with db.session.begin_nested():
        db.session.add(workflow)
        db.session.add(del_workflow)
        db.session.add(app_del_workflow)
        db.session.add(activity)
        db.session.add(activity2)
        db.session.add(activity3)
        db.session.add(del_activity)
        db.session.add(app_del_activity)
        db.session.add(activity_item1)
        db.session.add(activity_item2)
        db.session.add(activity_item3)
        db.session.add(activity_item4)
        db.session.add(activity_item5)
        db.session.add(activity_item6)
        db.session.add(activity_item7)
        db.session.add(activity_item8)
        db.session.add(activity_guest)
    db.session.commit()

    activity_action = ActivityAction(activity_id=activity.activity_id,
                                     action_id=1,action_status="M",
                                     action_handler=1, action_order=1)
    activity_action1_item1 = ActivityAction(activity_id=activity_item1.activity_id,
                                            action_id=1,action_status="M",
                                            action_handler=1, action_order=1)
    activity_action2_item1 = ActivityAction(activity_id=activity_item1.activity_id,
                                            action_id=3,action_status="M",
                                            action_handler=1, action_order=2)
    activity_action3_item1 = ActivityAction(activity_id=activity_item1.activity_id,
                                            action_id=5,action_status="M",
                                            action_handler=1, action_order=3)
    activity_action1_item2 = ActivityAction(activity_id=activity_item2.activity_id,
                                            action_id=1,action_status="M",
                                            action_handler=1, action_order=1)
    activity_action2_item2 = ActivityAction(activity_id=activity_item2.activity_id,
                                            action_id=3,action_status="M",
                                            action_handler=1, action_order=2)
    activity_action3_item2 = ActivityAction(activity_id=activity_item2.activity_id,
                                            action_id=5,action_status="M",
                                            action_handler=1, action_order=3)
    activity_item2_feedbackmail = ActionFeedbackMail(activity_id='3',
                                action_id=3,
                                feedback_maillist=None
                                )
    activity_item3_feedbackmail = ActionFeedbackMail(activity_id='4',
                                action_id=3,
                                feedback_maillist=[{"email": "test@org", "author_id": ""}]
                                )
    activity_item4_feedbackmail = ActionFeedbackMail(activity_id='5',
                                action_id=3,
                                feedback_maillist=[{"email": "test@org", "author_id": "1"}]
                                )
    activity_item5_feedbackmail = ActionFeedbackMail(activity_id='6',
                                action_id=3,
                                feedback_maillist=[{"email": "test1@org", "author_id": "2"}]
                                )
    activity_item5_Authors = Authors(id=1,json={'affiliationInfo': [{'affiliationNameInfo': [{'affiliationName': '', 'affiliationNameLang': 'ja', 'affiliationNameShowFlg': 'true'}], 'identifierInfo': [{'affiliationId': 'aaaa', 'affiliationIdType': '1', 'identifierShowFlg': 'true'}]}], 'authorIdInfo': [{'authorId': '1', 'authorIdShowFlg': 'true', 'idType': '1'}, {'authorId': '1', 'authorIdShowFlg': 'true', 'idType': '2'}], 'authorNameInfo': [{'familyName': '一', 'firstName': '二', 'fullName': '一\u3000二 ', 'language': 'ja-Kana', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'true'}], 'emailInfo': [{'email': 'test@org'}], 'gather_flg': 0, 'id': {'_id': 'HZ9iXYMBnq6bEezA2CK3', '_index': 'tenant1-authors-author-v1.0.0', '_primary_term': 29, '_seq_no': 0, '_shards': {'failed': 0, 'successful': 1, 'total': 2}, '_type': 'author-v1.0.0', '_version': 1, 'result': 'created'}, 'is_deleted': 'false', 'pk_id': '1'})
    activity_item6_feedbackmail = ActionFeedbackMail(activity_id='7',
                                action_id=3,
                                feedback_maillist={"email": "test1@org", "author_id": "2"}
                                )
    with db.session.begin_nested():
        db.session.add(activity_action)
        db.session.add(activity_action1_item1)
        db.session.add(activity_action2_item1)
        db.session.add(activity_action3_item1)
        db.session.add(activity_item2_feedbackmail)
        db.session.add(activity_item3_feedbackmail)
        db.session.add(activity_item4_feedbackmail)
        db.session.add(activity_item5_feedbackmail)
        db.session.add(activity_item5_Authors)
        db.session.add(activity_item6_feedbackmail)
    db.session.commit()

    activity_03 = Activity(activity_id='A-00000003-00000', workflow_id=1, flow_id=flow_define.id,
                    action_id=3, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item5', shared_user_id=-1, extra_info={},
                    action_order=1,
                    )
    with db.session.begin_nested():
        db.session.add(activity_03)

    activity_action03_1 = ActivityAction(activity_id=activity_03.activity_id,
                                            action_id=1,action_status="M",action_comment="",
                                            action_handler=1, action_order=1)
    activity_action03_2 = ActivityAction(activity_id=activity_03.activity_id,
                                            action_id=3,action_status="F",action_comment="",
                                            action_handler=0, action_order=2)
    with db.session.begin_nested():
        db.session.add(activity_action03_1)
        db.session.add(activity_action03_2)
    db.session.commit()

    history = ActivityHistory(
        activity_id=activity.activity_id,
        action_id=activity.action_id,
        action_order=activity.action_order,
    )
    with db.session.begin_nested():
        db.session.add(history)
    db.session.commit()
    doi_identifier = Identifier(id=1, repository='Root Index',jalc_flag= True,jalc_crossref_flag= True,jalc_datacite_flag=True,ndl_jalc_flag=True,
        jalc_doi='123',jalc_crossref_doi='1234',jalc_datacite_doi='12345',ndl_jalc_doi='123456',suffix='def',
        created_userId='1',created_date=datetime.strptime('2022-09-28 04:33:42','%Y-%m-%d %H:%M:%S'),
        updated_userId='1',updated_date=datetime.strptime('2022-09-28 04:33:42','%Y-%m-%d %H:%M:%S')
    )
    doi_identifier2 = Identifier(id=2, repository='test',jalc_flag= True,jalc_crossref_flag= True,jalc_datacite_flag=True,ndl_jalc_flag=True,
        jalc_doi=None,jalc_crossref_doi=None,jalc_datacite_doi=None,ndl_jalc_doi=None,suffix=None,
        created_userId='1',created_date=datetime.strptime('2022-09-28 04:33:42','%Y-%m-%d %H:%M:%S'),
        updated_userId='1',updated_date=datetime.strptime('2022-09-28 04:33:42','%Y-%m-%d %H:%M:%S')
        )
    with db.session.begin_nested():
        db.session.add(doi_identifier)
        db.session.add(doi_identifier2)
    db.session.commit()
    return {'flow_define':flow_define,
            'item_type':item_type,
            'workflow':workflow,
            'action_feedback_mail':activity_item3_feedbackmail,
            'action_feedback_mail1':activity_item4_feedbackmail,
            'action_feedback_mail2':activity_item5_feedbackmail,
            'action_feedback_mail3':activity_item6_feedbackmail,
            'activities':[activity,activity_item1,activity_item2,activity_item3,activity_item7,activity_item8,activity_guest,del_activity,app_del_activity],
            'activity_actions':[activity_action,activity_action1_item1,activity_action2_item1,activity_action3_item1],
    }

@pytest.fixture()
def workflow(app, db, item_type, action_data, users):
    flow_define = FlowDefine(id=1,flow_id=uuid.uuid4(),
                             flow_name='Registration Flow',
                             flow_user=1)
    with db.session.begin_nested():
        db.session.add(flow_define)
    db.session.commit()

    # setting flow action(start, item register, oa policy, item link, identifier grant, approval, end)
    flow_actions = list()
    # start
    flow_actions.append(FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=1,
                     action_version='1.0.0',
                     action_order=1,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    # item register
    flow_actions.append(FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=3,
                     action_version='1.0.0',
                     action_order=2,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    # oa policy
    flow_actions.append(FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=6,
                     action_version='1.0.0',
                     action_order=3,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    # item link
    flow_actions.append(FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=5,
                     action_version='1.0.0',
                     action_order=4,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    # identifier grant
    flow_actions.append(FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=7,
                     action_version='1.0.0',
                     action_order=5,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    # approval
    flow_actions.append(FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=4,
                     action_version='1.0.0',
                     action_order=6,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    # end
    flow_actions.append(FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=2,
                     action_version='1.0.0',
                     action_order=7,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    with db.session.begin_nested():
        db.session.add_all(flow_actions)
    db.session.commit()
    workflow = WorkFlow(flows_id=uuid.uuid4(),
                        flows_name='test workflow01',
                        itemtype_id=1,
                        index_tree_id=None,
                        flow_id=1,
                        is_deleted=False,
                        open_restricted=False,
                        location_id=None,
                        is_gakuninrdm=False)
    deleted_workflow = WorkFlow(flows_id=uuid.uuid4(),
                        flows_name='test workflow02',
                        itemtype_id=1,
                        index_tree_id=None,
                        flow_id=1,
                        is_deleted=True,
                        open_restricted=False,
                        location_id=None,
                        is_gakuninrdm=False)
    with db.session.begin_nested():
        db.session.add(workflow)
        db.session.add(deleted_workflow)
    db.session.commit()

    return {
        "flow":flow_define,
        "flow_action":flow_actions,
        "workflow":workflow
    }

@pytest.fixture()
def workflow_one(app, db, item_type, action_data, users):
    flow_define = FlowDefine(id=2,flow_id=uuid.uuid4(),
                             flow_name='Registration Flow2',
                             flow_user=1)
    with db.session.begin_nested():
        db.session.add(flow_define)
    db.session.commit()

    # setting flow action(start, item register, oa policy, item link, identifier grant, approval, end)
    flow_actions = list()
    # start
    flow_actions.append(FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=1,
                     action_version='1.0.0',
                     action_order=1,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    with db.session.begin_nested():
        db.session.add_all(flow_actions)
    db.session.commit()
    workflow = WorkFlow(flows_id=uuid.uuid4(),
                        flows_name='test workflow02',
                        itemtype_id=1,
                        index_tree_id=None,
                        flow_id=2,
                        is_deleted=False,
                        open_restricted=False,
                        location_id=None,
                        is_gakuninrdm=False)
    with db.session.begin_nested():
        db.session.add(workflow)
    db.session.commit()

    return {
        "flow":flow_define,
        "flow_action":flow_actions,
        "workflow":workflow
    }

@pytest.fixture()
def no_begin_action(app, db):
    """Set up the database without a 'begin_action' in the _Action table."""
    actions_to_update = db.session.query(Action).filter_by(action_endpoint='begin_action').all()
    if actions_to_update:
        for action in actions_to_update:
            action.action_endpoint = "other_action"
        db.session.commit()

@pytest.fixture()
def workflow_open_restricted(app, db, item_type, action_data, users):
    flow_define1 = FlowDefine(id=2,flow_id=uuid.uuid4(),
                                flow_name='terms_of_use_only',
                                flow_user=1)
    flow_define2 = FlowDefine(id=3,flow_id=uuid.uuid4(),
                                flow_name='usage application',
                                flow_user=1)
    with db.session.begin_nested():
        db.session.add(flow_define1)
        db.session.add(flow_define2)
    db.session.commit()

    # setting flow action(start, item register, oa policy, item link, identifier grant, approval, end)
    flow_actions1 = list()
    flow_actions2 = list()
    # flow_define1
    # start
    flow_actions1.append(FlowAction(status='N',
                    flow_id=flow_define1.flow_id,
                    action_id=1,
                    action_version='1.0.0',
                    action_order=1,
                    action_condition='',
                    action_status='A',
                    action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                    send_mail_setting={}))
    # end
    flow_actions1.append(FlowAction(status='N',
                    flow_id=flow_define1.flow_id,
                    action_id=2,
                    action_version='1.0.0',
                    action_order=2,
                    action_condition='',
                    action_status='A',
                    action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                    send_mail_setting={}))
    # flow_define2
    # start
    flow_actions2.append(FlowAction(status='N',
                    flow_id=flow_define2.flow_id,
                    action_id=1,
                    action_version='1.0.0',
                    action_order=1,
                    action_condition='',
                    action_status='A',
                    action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                    send_mail_setting={}))
    # item register
    flow_actions2.append(FlowAction(status='N',
                    flow_id=flow_define2.flow_id,
                    action_id=3,
                    action_version='1.0.0',
                    action_order=2,
                    action_condition='',
                    action_status='A',
                    action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                    send_mail_setting={}))
    # approval
    flow_actions2.append(FlowAction(status='N',
                    flow_id=flow_define2.flow_id,
                    action_id=4,
                    action_version='1.0.0',
                    action_order=3,
                    action_condition='',
                    action_status='A',
                    action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                    send_mail_setting={}))
    # end
    flow_actions2.append(FlowAction(status='N',
                    flow_id=flow_define2.flow_id,
                    action_id=2,
                    action_version='1.0.0',
                    action_order=4,
                    action_condition='',
                    action_status='A',
                    action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                    send_mail_setting={}))
    with db.session.begin_nested():
        db.session.add_all(flow_actions1)
        db.session.add_all(flow_actions2)
    db.session.commit()
    workflow1 = WorkFlow(flows_id=uuid.uuid4(),
                        flows_name='terms_of_use_only',
                        itemtype_id=1,
                        index_tree_id=None,
                        flow_id=2,
                        is_deleted=False,
                        open_restricted=True,
                        location_id=None,
                        is_gakuninrdm=False)
    workflow2 = WorkFlow(flows_id=uuid.uuid4(),
                        flows_name='usage application',
                        itemtype_id=1,
                        index_tree_id=None,
                        flow_id=3,
                        is_deleted=False,
                        open_restricted=True,
                        location_id=None,
                        is_gakuninrdm=False)
    workflow3 = WorkFlow(flows_id=uuid.uuid4(),
                        flows_name='nomal workflow',
                        itemtype_id=1,
                        index_tree_id=None,
                        flow_id=3,
                        is_deleted=False,
                        open_restricted=False,
                        location_id=None,
                        is_gakuninrdm=False)
    with db.session.begin_nested():
        db.session.add(workflow1)
        db.session.add(workflow2)
        db.session.add(workflow3)
    db.session.commit()

    workflow_role1 = WorkflowRole(
        workflow_id=workflow1.id
        ,role_id=users[2]["obj"].id # sysadmin
    )
    workflow_role2 = WorkflowRole(
        workflow_id=workflow2.id
        ,role_id=users[2]["obj"].id # sysadmin
    )
    workflow_role3 = WorkflowRole(
        workflow_id=workflow3.id
        ,role_id=users[2]["obj"].id # sysadmin
    )
    with db.session.begin_nested():
        db.session.add(workflow_role1)
        db.session.add(workflow_role2)
        db.session.add(workflow_role3)
    db.session.commit()

    return [{
            "flow":flow_define1,
            "flow_action":flow_actions1,
            "workflow":workflow1
        },{
            "flow":flow_define2,
            "flow_action":flow_actions2,
            "workflow":workflow2
        },{
            "flow":flow_define2,
            "flow_action":flow_actions2,
            "workflow":workflow3
        }]

@pytest.fixture()
def location(app, db, instance_path):
    with db.session.begin_nested():
        Location.query.delete()
        loc = Location(name='local', uri=instance_path, default=True)
        db.session.add(loc)
    db.session.commit()
    return loc

@pytest.fixture()
def db_records(db, location):
    record_data = json_data("data/test_records.json")
    item_data = json_data("data/test_items.json")
    record_num = len(record_data)
    result = []
    for d in range(record_num):
        result.append(create_record(record_data[d], item_data[d]))
        db.session.commit()

    yield result

@pytest.fixture()
def db_records_for_doi_validation_test(db, location):
    record_data = json_data("data/test_records_doi_validation_test.json")
    item_data = json_data("data/test_items_doi_validation_test.json")
    record_num = len(record_data)
    result = []
    for d in range(record_num):
        result.append(create_record(record_data[d], item_data[d]))
        db.session.commit()

    yield result

@pytest.fixture()
def add_file(db, location):
    def factory(record, contents=b'test example', filename="generic_file.txt"):
        b = Bucket.create()
        r = RecordsBuckets.create(bucket=b, record=record.model)
        ObjectVersion.create(b,filename)
        stream = BytesIO(contents)
        record.files[filename] = stream
        record.files.dumps()
        record.commit()
        db.session.commit()
        return b,r
    return factory

@pytest.fixture()
def db_register2(app, db):
    session_lifetime = SessionLifetime(lifetime=60,is_delete=False)

    with db.session.begin_nested():
        db.session.add(session_lifetime)


@pytest.fixture()
def db_register_fullaction(app, db, db_records, users, action_data, item_type):
    flow_define = FlowDefine(flow_id=uuid.uuid4(),
                             flow_name='Registration Flow',
                             flow_user=1)
    del_flow_define = FlowDefine(flow_id=uuid.uuid4(),
                                flow_name='Delete Flow',
                                flow_user=1,
                                flow_type='2')
    app_flow_define = FlowDefine(flow_id=uuid.uuid4(),
                                flow_name='Delete Approval Flow',
                                flow_user=1,
                                flow_type='2')
    two_app_flow_define = FlowDefine(flow_id=uuid.uuid4(),
                                flow_name='Delete two Approval Flow',
                                flow_user=1,
                                flow_type='2')
    with db.session.begin_nested():
        db.session.add(flow_define)
        db.session.add(del_flow_define)
        db.session.add(app_flow_define)
        db.session.add(two_app_flow_define)
    db.session.commit()

    # setting flow action(start, item register, oa policy, item link, identifier grant, approval, end)
    flow_actions = list()
    del_flow_actions = list()
    del_app_flow_actions = list()
    two_app_flow_actions = list()
    # start
    flow_actions.append(FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=1,
                     action_version='1.0.0',
                     action_order=1,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    # item register
    flow_actions.append(FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=3,
                     action_version='1.0.0',
                     action_order=2,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    # oa policy
    flow_actions.append(FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=6,
                     action_version='1.0.0',
                     action_order=3,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    # item link
    flow_actions.append(FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=5,
                     action_version='1.0.0',
                     action_order=4,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    # identifier grant
    flow_actions.append(FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=7,
                     action_version='1.0.0',
                     action_order=5,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    # approval
    flow_actions.append(FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=4,
                     action_version='1.0.0',
                     action_order=6,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    # end
    flow_actions.append(FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=2,
                     action_version='1.0.0',
                     action_order=7,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    # delete flow action
    # start
    del_flow_actions.append(FlowAction(status='N',
                     flow_id=del_flow_define.flow_id,
                     action_id=1,
                     action_version='1.0.0',
                     action_order=1,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2025/05/01 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    # end
    del_flow_actions.append(FlowAction(status='N',
                     flow_id=del_flow_define.flow_id,
                     action_id=2,
                     action_version='1.0.0',
                     action_order=2,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2025/05/01 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    # delete aooroval flow action
    # start
    del_app_flow_actions.append(FlowAction(status='N',
                     flow_id=app_flow_define.flow_id,
                     action_id=1,
                     action_version='1.0.0',
                     action_order=1,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2025/05/01 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    # approval
    del_app_flow_actions.append(FlowAction(status='N',
                     flow_id=app_flow_define.flow_id,
                     action_id=4,
                     action_version='1.0.0',
                     action_order=2,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2025/05/01 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    # end
    del_app_flow_actions.append(FlowAction(status='N',
                     flow_id=app_flow_define.flow_id,
                     action_id=2,
                     action_version='1.0.0',
                     action_order=3,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2025/05/01 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    # delete two aooroval flow action
    # start
    two_app_flow_actions.append(FlowAction(status='N',
                     flow_id=two_app_flow_define.flow_id,
                     action_id=1,
                     action_version='1.0.0',
                     action_order=1,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2025/05/01 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    # approval
    two_app_flow_actions.append(FlowAction(status='N',
                     flow_id=two_app_flow_define.flow_id,
                     action_id=4,
                     action_version='1.0.0',
                     action_order=2,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2025/05/01 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    # second approval
    two_app_flow_actions.append(FlowAction(status='N',
                     flow_id=two_app_flow_define.flow_id,
                     action_id=4,
                     action_version='1.0.0',
                     action_order=3,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2025/05/01 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    # end
    two_app_flow_actions.append(FlowAction(status='N',
                     flow_id=two_app_flow_define.flow_id,
                     action_id=2,
                     action_version='1.0.0',
                     action_order=4,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2025/05/01 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    with db.session.begin_nested():
        db.session.add_all(flow_actions)
        db.session.add_all(del_flow_actions)
        db.session.add_all(del_app_flow_actions)
        db.session.add_all(two_app_flow_actions)
    db.session.commit()

    # setting workflow, activity(not exist item, exist item)
    workflow = WorkFlow(flows_id=uuid.uuid4(),
                        flows_name='test workflow01',
                        itemtype_id=1,
                        index_tree_id=None,
                        flow_id=1,
                        is_deleted=False,
                        open_restricted=False,
                        location_id=None,
                        is_gakuninrdm=False)
    del_workflow = WorkFlow(flows_id=uuid.uuid4(),
                        flows_name='test delete workflow',
                        itemtype_id=1,
                        index_tree_id=None,
                        flow_id=1,
                        delete_flow_id=del_flow_define.id,
                        is_deleted=False,
                        open_restricted=False,
                        location_id=None,
                        is_gakuninrdm=False)
    app_del_workflow = WorkFlow(flows_id=uuid.uuid4(),
                        flows_name='test delete approval workflow',
                        itemtype_id=1,
                        index_tree_id=None,
                        flow_id=1,
                        delete_flow_id=app_flow_define.id,
                        is_deleted=False,
                        open_restricted=False,
                        location_id=None,
                        is_gakuninrdm=False)
    two_app_del_workflow = WorkFlow(flows_id=uuid.uuid4(),
                        flows_name='test delete two approval workflow',
                        itemtype_id=1,
                        index_tree_id=None,
                        flow_id=1,
                        delete_flow_id=two_app_flow_define.id,
                        is_deleted=False,
                        open_restricted=False,
                        location_id=None,
                        is_gakuninrdm=False)
    activity = Activity(activity_id='1',workflow_id=1, flow_id=flow_define.id,
                action_id=1, activity_login_user=1,
                activity_update_user=1,
                activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                activity_community_id=3,
                activity_confirm_term_of_use=True,
                title='test', shared_user_id=-1, extra_info={},
                action_order=1,
                )
    activity2 = Activity(activity_id='A-00000001-10001',workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=1,
                    action_status = 'M',
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_id=-1, extra_info={},
                    action_order=6)

    activity3 = Activity(activity_id='A-00000001-10002',workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=1,
                    action_status = 'C',
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_id=-1, extra_info={},
                    action_order=6)
    # identifier登録あり
    activity_item1 = Activity(activity_id='2',item_id=db_records[2][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item1', shared_user_id=-1, extra_info={},
                    action_order=1,
                    )
    # identifier登録なし
    activity_item2 = Activity(activity_id='3',item_id=db_records[4][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item1', shared_user_id=-1, extra_info={},
                    action_order=1,
                    )
    # ゲスト作成アクティビティ
    activity_item3 = Activity(activity_id='4',item_id=db_records[5][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item1', shared_user_id=-1, extra_info={"guest_mail":"guest@test.org"},
                    action_order=1,
                    )
    # item_idが"."を含まない
    activity_item4 = Activity(activity_id='5',item_id=db_records[0][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item1', shared_user_id=-1, extra_info={"guest_mail":"guest@test.org"},
                    action_order=1,
                    )
    # not identifier value in without_ver
    activity_item5 = Activity(activity_id='6',item_id=db_records[3][2].id,workflow_id=1, flow_id=flow_define.id,
                action_id=1, activity_login_user=users[3]["id"],
                activity_update_user=1,
                activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                activity_community_id=3,
                activity_confirm_term_of_use=True,
                title='test item1', shared_user_id=-1, extra_info={"guest_mail":"guest@test.org"},
                action_order=1,
                )
    # same identifier with without_ver
    activity_item6 = Activity(activity_id='7',item_id=db_records[1][2].id,workflow_id=1, flow_id=flow_define.id,
                action_id=1, activity_login_user=users[3]["id"],
                activity_update_user=1,
                activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                activity_community_id=3,
                activity_confirm_term_of_use=True,
                title='test item1', shared_user_id=-1, extra_info={"guest_mail":"guest@test.org"},
                action_order=1,
                )
    # delete flow activity
    del_activity = Activity(activity_id='A-00000001-10020',workflow_id=2, flow_id=del_flow_define.id,
                    action_id=1, activity_login_user=1,
                    activity_update_user=1,
                    activity_start=datetime.strptime('2025/05/02 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_id=-1, extra_info={},
                    action_order=1,
                    )
    # delete approval flow activity
    app_del_activity = Activity(activity_id='A-00000001-10021',item_id=db_records[7][2].id,workflow_id=3, flow_id=app_flow_define.id,
                    action_id=1, activity_login_user=1,
                    activity_update_user=1,
                    activity_start=datetime.strptime('2025/05/02 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_id=-1, extra_info={},
                    action_order=1,
                    )
    # delete two approval flow activity
    two_app_del_activity = Activity(activity_id='A-00000001-10022',item_id=db_records[8][2].id,workflow_id=4, flow_id=two_app_flow_define.id,
                    action_id=1, activity_login_user=1,
                    activity_update_user=1,
                    activity_start=datetime.strptime('2025/05/02 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_id=-1, extra_info={},
                    action_order=1,
                    )
    # delete flow activity
    two_app_del_activity2 = Activity(activity_id='A-00000001-10023',item_id=db_records[9][2].id,workflow_id=4, flow_id=two_app_flow_define.id,
                    action_id=1, activity_login_user=1,
                    activity_update_user=1,
                    activity_start=datetime.strptime('2025/05/02 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_id=-1, extra_info={},
                    action_order=1,
                    )
    with db.session.begin_nested():
        db.session.add(workflow)
        db.session.add(del_workflow)
        db.session.add(app_del_workflow)
        db.session.add(two_app_del_workflow)
        db.session.add(activity)
        db.session.add(activity2)
        db.session.add(activity3)
        db.session.add(activity_item1)
        db.session.add(activity_item2)
        db.session.add(activity_item3)
        db.session.add(activity_item4)
        db.session.add(activity_item5)
        db.session.add(activity_item6)
        db.session.add(del_activity)
        db.session.add(app_del_activity)
        db.session.add(two_app_del_activity)
        db.session.add(two_app_del_activity2)
    db.session.commit()

    feedbackmail_action1 = ActionFeedbackMail(
        activity_id=activity_item1.activity_id,
        action_id=3,
        feedback_maillist=[{"email":"test@test.org"}]
        )
    feedbackmail_action2 = ActionFeedbackMail(
        activity_id=activity_item2.activity_id,
        action_id=3,
        feedback_maillist=[]
    )
    feedbackmail_action3 = ActionFeedbackMail(
        activity_id=activity_item4.activity_id,
        action_id=3,
        feedback_maillist=[]
    )
    feedbackmail = FeedbackMailList(
        item_id=activity_item2.item_id,
        mail_list=[{"email":"test@test.org"}]
    )
    with db.session.begin_nested():
        db.session.add(feedbackmail_action1)
        db.session.add(feedbackmail_action2)
        db.session.add(feedbackmail_action3)
        db.session.add(feedbackmail)
    db.session.commit()

    permissions = list()
    for i in range(len(users)):
        permissions.append(FilePermission(users[i]["id"],"1.1","test_file","2",None,-1))
    with db.session.begin_nested():
        db.session.add_all(permissions)
    db.session.commit()

    def set_activityaction(_activity, _action,_flow_action):
        action_handler = _activity.activity_login_user \
            if not _action.action_endpoint == 'approval' else -1
        activity_action = ActivityAction(
            activity_id=_activity.activity_id,
            action_id=_flow_action.action_id,
            action_status="B",
            action_handler=action_handler,
            action_order=_flow_action.action_order
        )
        db.session.add(activity_action)

    # setting activity_action in activity existed item
    for flow_action in flow_actions:
        action = action_data[0][flow_action.action_id-1]
        set_activityaction(activity_item1, action, flow_action)
        set_activityaction(activity_item2, action, flow_action)
        set_activityaction(activity_item3, action, flow_action)
        set_activityaction(activity_item4, action, flow_action)
        set_activityaction(activity_item5, action, flow_action)
        set_activityaction(activity_item6, action, flow_action)

    # setting activity_action in activity existed item
    for flow_action in del_flow_actions:
        action = action_data[0][flow_action.action_id-1]
        set_activityaction(del_activity, action, flow_action)
    # setting activity_action in activity existed item
    for flow_action in del_app_flow_actions:
        action = action_data[0][flow_action.action_id-1]
        set_activityaction(app_del_activity, action, flow_action)
    # setting activity_action in activity existed item
    for flow_action in two_app_flow_actions:
        action = action_data[0][flow_action.action_id-1]
        set_activityaction(two_app_del_activity, action, flow_action)
        set_activityaction(two_app_del_activity2, action, flow_action)


    # flow_action_role = FlowActionRole(
    #     flow_action_id=flow_actions[5].id,
    #     action_role=None,
    #     action_user=1
    # )
    # with db.session.begin_nested():
    #     db.session.add(flow_action_role)
    # db.session.commit()

    action_identifier1=ActionIdentifier(
        activity_id=activity_item1.activity_id,
        action_id=7,
        action_identifier_select=-2,
        action_identifier_jalc_doi="",
        action_identifier_jalc_cr_doi="",
        action_identifier_jalc_dc_doi="",
        action_identifier_ndl_jalc_doi=""
    )
    action_identifier3=ActionIdentifier(
        activity_id=activity_item3.activity_id,
        action_id=7,
        action_identifier_select=1,
        action_identifier_jalc_doi="",
        action_identifier_jalc_cr_doi="",
        action_identifier_jalc_dc_doi="",
        action_identifier_ndl_jalc_doi=""
    )
    with db.session.begin_nested():
        db.session.add(action_identifier1)
        db.session.add(action_identifier3)
    db.session.commit()

    doi_identifier = Identifier(id=1, repository='Root Index',jalc_flag= True,jalc_crossref_flag= True,jalc_datacite_flag=True,ndl_jalc_flag=True,
        jalc_doi='123',jalc_crossref_doi='456',jalc_datacite_doi='789',ndl_jalc_doi='000',suffix='def',
        created_userId='1',created_date=datetime.strptime('2022-09-28 04:33:42','%Y-%m-%d %H:%M:%S'),
        updated_userId='1',updated_date=datetime.strptime('2022-09-28 04:33:42','%Y-%m-%d %H:%M:%S')
    )
    doi_identifier2 = Identifier(id=2, repository='test',jalc_flag= True,jalc_crossref_flag= True,jalc_datacite_flag=True,ndl_jalc_flag=True,
        jalc_doi=None,jalc_crossref_doi=None,jalc_datacite_doi=None,ndl_jalc_doi=None,suffix=None,
        created_userId='1',created_date=datetime.strptime('2022-09-28 04:33:42','%Y-%m-%d %H:%M:%S'),
        updated_userId='1',updated_date=datetime.strptime('2022-09-28 04:33:42','%Y-%m-%d %H:%M:%S')
        )
    with db.session.begin_nested():
        db.session.add(doi_identifier)
        db.session.add(doi_identifier2)
    db.session.commit()

    gActivity = GuestActivity(
        user_mail="guest@mail.com",
        record_id="1",
        file_name="test",
        activity_id="2",
        token="token",
        expiration_date=5,
        is_usage_report=True
    )
    with db.session.begin_nested():
        db.session.add(gActivity)
    db.session.commit()

    return {"flow_actions":flow_actions,
            "activities":[activity,activity_item1,activity_item2,activity_item3,activity_item4,activity_item5,activity_item6,del_activity,app_del_activity,two_app_del_activity,two_app_del_activity2]}

@pytest.fixture()
def db_register_usage_application(app, db, db_records, users, action_data, item_type ):
    workflows = {}


    flow_id1 = uuid.uuid4()
    # flow_id2 = uuid.uuid4()
    flow_id3 = uuid.uuid4()
    flow_id4 = uuid.uuid4()

    #workflow_flow_define
    flow_define1 = FlowDefine(
        flow_id=flow_id1, flow_name="利用登録", flow_user=1, flow_status="A"
    )
    flow_define3 = FlowDefine(
        flow_id=flow_id3, flow_name="利用申請", flow_user=1, flow_status="A"
    )
    flow_define4 = FlowDefine(
        flow_id=flow_id4, flow_name="2段階利用申請", flow_user=1, flow_status="A"
    )

    # workflow_flow_action
    flow_action1_1 = FlowAction(
        status="N",
        flow_id=flow_id1,
        action_id=1,
        action_version="1.0.0",
        action_order=1,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": False, "inform_approval": False, "request_approval": False},
    )
    flow_action1_2 = FlowAction(
        status="N",
        flow_id=flow_id1,
        action_id=2,
        action_version="1.0.0",
        action_order=3,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": False, "inform_approval": False, "request_approval": False},
    )
    flow_action1_3 = FlowAction(
        status="N",
        flow_id=flow_id1,
        action_id=3,
        action_version="1.0.1",
        action_order=2,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": False, "inform_approval": True, "request_approval": False},
    )

    flow_action3_1 = FlowAction(
        status="N",
        flow_id=flow_id3,
        action_id=1,
        action_version="1.0.0",
        action_order=1,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": False, "inform_approval": False, "request_approval": False},
    )
    flow_action3_2 = FlowAction(
        status="N",
        flow_id=flow_id3,
        action_id=2,
        action_version="1.0.0",
        action_order=4,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": False, "inform_approval": False, "request_approval": False},
    )
    flow_action3_3 = FlowAction(
        status="N",
        flow_id=flow_id3,
        action_id=3,
        action_version="1.0.1",
        action_order=2,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": False, "inform_approval": False, "request_approval": False},
    )
    flow_action3_4 = FlowAction(
        status="N",
        flow_id=flow_id3,
        action_id=4,
        action_version="2.0.0",
        action_order=3,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": True, "inform_approval": True, "request_approval": True},
    )
    flow_action4_1 = FlowAction(
        status="N",
        flow_id=flow_id4,
        action_id=1,
        action_version="1.0.0",
        action_order=1,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": False, "inform_approval": False, "request_approval": False},
    )
    flow_action4_2 = FlowAction(
        status="N",
        flow_id=flow_id4,
        action_id=2,
        action_version="1.0.0",
        action_order=5,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": False, "inform_approval": False, "request_approval": False},
    )
    flow_action4_3 = FlowAction(
        status="N",
        flow_id=flow_id4,
        action_id=3,
        action_version="1.0.1",
        action_order=2,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": False, "inform_approval": False, "request_approval": False},
    )
    flow_action4_4 = FlowAction(
        status="N",
        flow_id=flow_id4,
        action_id=4,
        action_version="2.0.0",
        action_order=3,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": True, "inform_approval": True, "request_approval": True},
    )
    flow_action4_5 = FlowAction(
        status="N",
        flow_id=flow_id4,
        action_id=4,
        action_version="2.0.0",
        action_order=4,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": True, "inform_approval": True, "request_approval": True},
    )


    with db.session.begin_nested():
        db.session.add_all([flow_define1,flow_define3,flow_define4])
    db.session.commit()
    #workflow_workflow
    workflow_workflow1 = WorkFlow(
        flows_id=flow_id1,
        flows_name="利用登録",
        itemtype_id=1,
        index_tree_id=None,
        flow_id=flow_define1.id,
        flow_define=flow_define1,
        is_deleted=False,
        open_restricted=True,
        # location_id=location.id,
        # location=location,
        is_gakuninrdm=False,
    )

    workflow_workflow3 = WorkFlow(
        flows_id=flow_id3,
        flows_name="利用申請",
        itemtype_id=1,
        index_tree_id=None,
        flow_id=flow_define3.id,
        flow_define=flow_define3,
        is_deleted=False,
        open_restricted=True,
        # location_id=location.id,
        # location=location,
        is_gakuninrdm=False,
    )
    workflow_workflow4 = WorkFlow(
        flows_id=flow_id4,
        flows_name="2段階利用申請",
        itemtype_id=1,
        index_tree_id=None,
        flow_id=flow_define4.id,
        flow_define=flow_define4,
        is_deleted=False,
        open_restricted=True,
        # location_id=location.id,
        # location=location,
        is_gakuninrdm=False,
    )

    with db.session.begin_nested():
        db.session.add_all([flow_action1_1,flow_action1_2,flow_action1_3])

        db.session.add_all([flow_action3_1,flow_action3_2,flow_action3_3,flow_action3_4])
        db.session.add_all([flow_action4_1,flow_action4_2,flow_action4_3,flow_action4_4,flow_action4_5])
        db.session.add_all([workflow_workflow1, workflow_workflow3, workflow_workflow4])
    db.session.commit()
    workflows.update({
		"flow_define1"       : flow_define1
		# ,"flow_define2"       : flow_define2
		,"flow_define3"       : flow_define3
		,"flow_define4"       : flow_define4
		,"flow_action1_1"     : flow_action1_1
		,"flow_action1_2"     : flow_action1_2
		,"flow_action1_3"     : flow_action1_3
		# ,"flow_action2_1"     : flow_action2_1
		# ,"flow_action2_2"     : flow_action2_2
		,"flow_action3_1"     : flow_action3_1
		,"flow_action3_2"     : flow_action3_2
		,"flow_action3_3"     : flow_action3_3
		,"flow_action3_4"     : flow_action3_4
		,"flow_action4_1"     : flow_action4_1
		,"flow_action4_2"     : flow_action4_2
		,"flow_action4_3"     : flow_action4_3
		,"flow_action4_4"     : flow_action4_4
		,"flow_action4_5"     : flow_action4_5
		,"workflow_workflow1" : workflow_workflow1
		# ,"workflow_workflow2" : workflow_workflow2
		,"workflow_workflow3" : workflow_workflow3
		,"workflow_workflow4" : workflow_workflow4
    })

    # 利用登録(now -> item_registration, next ->end)
    activity1 = Activity(activity_id='A-00000001-20001'
                        ,workflow_id=workflow_workflow1.id
                        , flow_id=flow_define1.id,
                    action_id=3,
                    item_id=db_records[2][2].id,
                    activity_login_user=1,
                    action_status = 'M',
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=None,
                    activity_confirm_term_of_use=True,
                    title='test'
                    , shared_user_id=-1
                    , extra_info={},
                    action_order=2)
    activity1_pre_action = ActivityAction(
        activity_id='A-00000001-20001'
        ,action_id=3
        ,action_status = 'M'
        ,action_order=2
    )
    activity1_next_action = ActivityAction(
        activity_id='A-00000001-20001'
        ,action_id=2
        ,action_status = 'M'
        ,action_order=3
    )
    # 利用申請(next ->end)
    activity2 = Activity(activity_id='A-00000001-20002'
                        ,workflow_id=workflow_workflow3.id
                        ,flow_id=flow_define3.id
                        ,action_id=4
                        ,item_id=db_records[2][2].id
                    , activity_login_user=1
                    , action_status = 'M'
                    , activity_update_user=1
                    , activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f')
                    , activity_community_id=3
                    , activity_confirm_term_of_use=True
                    , title='test'
                    , shared_user_id=-1
                    , extra_info={}
                    , action_order=3)
    activity2_pre_action = ActivityAction(
        activity_id='A-00000001-20002'
        ,action_id=4
        ,action_status = 'M'
        ,action_order=3
    )
    activity2_next_action = ActivityAction(
        activity_id='A-00000001-20002'
        ,action_id=2
        ,action_status = 'M'
        ,action_order=4
        ,action_handler=-1
    )
    file_permission = FilePermission(
        user_id = 1
        ,record_id= 1
        ,file_name= "aaa.txt"
        ,usage_application_activity_id='A-00000001-20002'
        ,usage_report_activity_id=None
        ,status = -1
    )
    # ２段階利用申請(next -> approval2)
    activity3 = Activity(activity_id='A-00000001-20003'
                        ,workflow_id=workflow_workflow4.id
                        ,flow_id=flow_define4.id
                        ,action_id=4
                        ,item_id=db_records[2][2].id
                        ,activity_login_user=1
                        ,action_status = 'M'
                        ,activity_update_user=1
                        ,activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f')
                        ,activity_community_id=3
                        ,activity_confirm_term_of_use=True
                        ,title='test'
                        ,shared_user_id=-1
                        ,extra_info={"file_name": "aaa.txt", "record_id": "1", "user_mail": "aaa@test.org", "related_title": "test", "is_restricted_access": True}
                        ,action_order=3)
    activity3_pre_action = ActivityAction(
        activity_id='A-00000001-20003'
        ,action_id=4
        ,action_status = 'M'
        ,action_order=3
    )
    activity3_next_action = ActivityAction(
        activity_id='A-00000001-20003'
        ,action_id=4
        ,action_status = 'M'
        ,action_order=4
    )
    # ２段階利用申請(next ->end)
    activity4 = Activity(activity_id='A-00000001-20004'
                        ,workflow_id=workflow_workflow4.id
                        ,flow_id=flow_define4.id
                        ,action_id=4
                        ,item_id=db_records[2][2].id
                        ,activity_login_user=1
                        ,action_status = 'M'
                        ,activity_update_user=1
                        ,activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f')
                        ,activity_community_id=3
                        ,activity_confirm_term_of_use=True
                        ,title='test'
                        ,shared_user_id=-1
                        ,extra_info={"file_name": "aaa.txt", "record_id": "1", "user_mail": "aaa@test.org", "related_title": "test", "is_restricted_access": True}
                        ,action_order=4)
    activity4_pre_action = ActivityAction(
        activity_id='A-00000001-20004'
        ,action_id=4
        ,action_status = 'M'
        ,action_order=4
    )
    activity4_next_action = ActivityAction(
        activity_id='A-00000001-20004'
        ,action_id=2
        ,action_status = 'M'
        ,action_order=5
    )
    guest_activity = GuestActivity(
        activity_id='A-00000001-20004'
        ,record_id=1
        ,user_mail = 'aaa@test.org'
        ,file_name = "aaa.txt"
        ,token="abc"
        ,expiration_date=5
        ,is_usage_report=False
    )
    with db.session.begin_nested():
        db.session.add(activity1)
        db.session.add(activity2)
        db.session.add(activity3)
        db.session.add(activity4)
    db.session.commit()
    with db.session.begin_nested():
        db.session.add(activity1_next_action)
        db.session.add(activity2_next_action)
        db.session.add(activity3_next_action)
        db.session.add(activity4_next_action)
        db.session.add(activity1_pre_action)
        db.session.add(activity2_pre_action)
        db.session.add(activity3_pre_action)
        db.session.add(activity4_pre_action)
        db.session.add(file_permission)
        db.session.add(guest_activity)
    db.session.commit()
    workflows.update({
        "activity1":activity1
        ,"activity2":activity2
        ,"activity3":activity3
        ,"activity4":activity4
    })

    permissions = list()
    for i in range(len(users)):
        permissions.append(FilePermission(users[i]["id"],"1.1","test_file","2",None,-1))
    with db.session.begin_nested():
        db.session.add_all(permissions)
    db.session.commit()

    def set_activityaction(_activity, _action,_flow_action):
        action_handler = _activity.activity_login_user \
            if not _action.action_endpoint == 'approval' else -1
        activity_action = ActivityAction(
            activity_id=_activity.activity_id,
            action_id=_flow_action.action_id,
            action_status="F",
            action_handler=action_handler,
            action_order=_flow_action.action_order
        )
        db.session.add(activity_action)

    # setting activity_action in activity existed item
    # for flow_action in flow_actions:
    #     action = action_data[0][flow_action.action_id-1]
    #     set_activityaction(activity_item1, action, flow_action)
    #     set_activityaction(activity_item2, action, flow_action)
    #     set_activityaction(activity_item3, action, flow_action)
    #     set_activityaction(activity_item4, action, flow_action)
    #     set_activityaction(activity_item5, action, flow_action)
    #     set_activityaction(activity_item6, action, flow_action)

    # db.session.commit()
    return workflows
    # {"flow_actions":flow_actions,
    #         "activities":[activity,activity_item1,activity_item2,activity_item3,activity_item4,activity_item5,activity_item6]}


@pytest.fixture()
def db_register_request_mail(app, db, db_records, users, action_data, item_type):
    flow_define = FlowDefine(flow_id=uuid.uuid4(),
                             flow_name='Registration Flow',
                             flow_user=1)
    with db.session.begin_nested():
        db.session.add(flow_define)
    db.session.commit()

    # setting flow action(start, item register, oa policy, item link, identifier grant, approval, end)
    flow_actions = list()
    # start
    flow_actions.append(FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=1,
                     action_version='1.0.0',
                     action_order=1,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    # item register
    flow_actions.append(FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=3,
                     action_version='1.0.0',
                     action_order=2,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    # oa policy
    flow_actions.append(FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=6,
                     action_version='1.0.0',
                     action_order=3,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    # item link
    flow_actions.append(FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=5,
                     action_version='1.0.0',
                     action_order=4,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    # identifier grant
    flow_actions.append(FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=7,
                     action_version='1.0.0',
                     action_order=5,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    # approval
    flow_actions.append(FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=4,
                     action_version='1.0.0',
                     action_order=6,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    # end
    flow_actions.append(FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=2,
                     action_version='1.0.0',
                     action_order=7,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={}))
    with db.session.begin_nested():
        db.session.add_all(flow_actions)
    db.session.commit()

    # setting workflow, activity(not exist item, exist item)
    workflow = WorkFlow(flows_id=uuid.uuid4(),
                        flows_name='test workflow01',
                        itemtype_id=1,
                        index_tree_id=None,
                        flow_id=1,
                        is_deleted=False,
                        open_restricted=False,
                        location_id=None,
                        is_gakuninrdm=False)
    activity = Activity(activity_id='1',workflow_id=1, flow_id=flow_define.id,
                action_id=1, activity_login_user=1,
                activity_update_user=1,
                activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                activity_community_id=3,
                activity_confirm_term_of_use=True,
                title='test', shared_user_id=None, extra_info={},
                action_order=1,
                )
    activity2 = Activity(activity_id='A-00000001-10001',workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=1,
                    action_status = 'M',
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_id=None, extra_info={},
                    action_order=6)

    activity3 = Activity(activity_id='A-00000001-10002',workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=1,
                    action_status = 'C',
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_id=None, extra_info={},
                    action_order=6)
    # identifier登録あり
    activity_item1 = Activity(activity_id='2',item_id=db_records[2][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item1', shared_user_id=None, extra_info={},
                    action_order=1,
                    )
    # identifier登録なし
    activity_item2 = Activity(activity_id='3',item_id=db_records[4][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item1', shared_user_id=None, extra_info={},
                    action_order=1,
                    )
    # ゲスト作成アクティビティ
    activity_item3 = Activity(activity_id='4',item_id=db_records[5][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item1', shared_user_id=None, extra_info={"guest_mail":"guest@test.org"},
                    action_order=1,
                    )
    # item_idが"."を含まない
    activity_item4 = Activity(activity_id='5',item_id=db_records[0][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item1', shared_user_id=None, extra_info={"guest_mail":"guest@test.org"},
                    action_order=1,
                    )
    # not identifier value in without_ver
    activity_item5 = Activity(activity_id='6',item_id=db_records[3][2].id,workflow_id=1, flow_id=flow_define.id,
                action_id=1, activity_login_user=users[3]["id"],
                activity_update_user=1,
                activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                activity_community_id=3,
                activity_confirm_term_of_use=True,
                title='test item1', shared_user_id=None, extra_info={"guest_mail":"guest@test.org"},
                action_order=1,
                )
    # same identifier with without_ver
    activity_item6 = Activity(activity_id='7',item_id=db_records[1][2].id,workflow_id=1, flow_id=flow_define.id,
                action_id=1, activity_login_user=users[3]["id"],
                activity_update_user=1,
                activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                activity_community_id=3,
                activity_confirm_term_of_use=True,
                title='test item1', shared_user_id=None, extra_info={"guest_mail":"guest@test.org"},
                action_order=1,
                )
    with db.session.begin_nested():
        db.session.add(workflow)
        db.session.add(activity)
        db.session.add(activity2)
        db.session.add(activity3)
        db.session.add(activity_item1)
        db.session.add(activity_item2)
        db.session.add(activity_item3)
        db.session.add(activity_item4)
        db.session.add(activity_item5)
        db.session.add(activity_item6)
    db.session.commit()

    feedbackmail_action1 = ActionFeedbackMail(
        activity_id=activity_item1.activity_id,
        action_id=3,
        feedback_maillist=[{"email":"test@test.org"}]
        )
    feedbackmail_action2 = ActionFeedbackMail(
        activity_id=activity_item2.activity_id,
        action_id=3,
        feedback_maillist=[]
    )
    feedbackmail_action3 = ActionFeedbackMail(
        activity_id=activity_item4.activity_id,
        action_id=3,
        feedback_maillist=[]
    )
    feedbackmail = FeedbackMailList(
        item_id=activity_item2.item_id,
        mail_list=[{"email":"test@test.org"}]
    )
    with db.session.begin_nested():
        db.session.add(feedbackmail_action1)
        db.session.add(feedbackmail_action2)
        db.session.add(feedbackmail_action3)
        db.session.add(feedbackmail)
    db.session.commit()

    permissions = list()
    for i in range(len(users)):
        permissions.append(FilePermission(users[i]["id"],"1.1","test_file","2",None,-1))
    with db.session.begin_nested():
        db.session.add_all(permissions)
    db.session.commit()

    def set_activityaction(_activity, _action,_flow_action):
        action_handler = _activity.activity_login_user \
            if not _action.action_endpoint == 'approval' else -1
        activity_action = ActivityAction(
            activity_id=_activity.activity_id,
            action_id=_flow_action.action_id,
            action_status="F",
            action_handler=action_handler,
            action_order=_flow_action.action_order
        )
        db.session.add(activity_action)

    # setting activity_action in activity existed item
    for flow_action in flow_actions:
        action = action_data[0][flow_action.action_id-1]
        set_activityaction(activity_item1, action, flow_action)
        set_activityaction(activity_item2, action, flow_action)
        set_activityaction(activity_item3, action, flow_action)
        set_activityaction(activity_item4, action, flow_action)
        set_activityaction(activity_item5, action, flow_action)
        set_activityaction(activity_item6, action, flow_action)


    flow_action_role = FlowActionRole(
        action_user = None,
        flow_action_id = flow_actions[5].id,
        action_user_exclude = False)
    with db.session.begin_nested():
        db.session.add(flow_action_role)
    db.session.commit()

    action_identifier1=ActionIdentifier(
        activity_id=activity_item1.activity_id,
        action_id=7,
        action_identifier_select=-2,
        action_identifier_jalc_doi="",
        action_identifier_jalc_cr_doi="",
        action_identifier_jalc_dc_doi="",
        action_identifier_ndl_jalc_doi=""
    )
    action_identifier3=ActionIdentifier(
        activity_id=activity_item3.activity_id,
        action_id=7,
        action_identifier_select=1,
        action_identifier_jalc_doi="",
        action_identifier_jalc_cr_doi="",
        action_identifier_jalc_dc_doi="",
        action_identifier_ndl_jalc_doi=""
    )
    with db.session.begin_nested():
        db.session.add(action_identifier1)
        db.session.add(action_identifier3)
    db.session.commit()
    return {"flow_actions":flow_actions,
            "activities":[activity,activity_item1,activity_item2,activity_item3,activity_item4,activity_item5,activity_item6]}


@pytest.fixture()
def site_info(db):
    site_info = {
        "site_name":["test_site"],
        "notify":["test_notify"],
    }
    SiteInfo.update(site_info)

@pytest.fixture()
def get_mapping_data(db):
    def factory(item_id):
        metadata = MappingData(item_id)
        return metadata
    return factory


@pytest.fixture()
def db_guestactivity(app, db, db_register):
    activity_id1 = db_register['activities'][1].activity_id
    activity_id2 = db_register['activities'][0].activity_id
    file_name = "Test_file"
    guest_mail = "user@test.com"

    token1 = generate_guest_activity_token_value(activity_id1, file_name, datetime.utcnow(), guest_mail)
    record1 = GuestActivity(
        user_mail=guest_mail,
        record_id="record_id",
        file_name=file_name,
        activity_id=activity_id1,
        token=token1,
        expiration_date=-500,
        is_usage_report=True
    )

    token2 = generate_guest_activity_token_value(activity_id2, file_name, datetime.utcnow(), guest_mail)
    record2 = GuestActivity(
        user_mail=guest_mail,
        record_id="record_id",
        file_name=file_name,
        activity_id=activity_id2,
        token=token2,
        expiration_date=500,
        is_usage_report=True
    )

    with db.session.begin_nested():
        db.session.add(record1)
        db.session.add(record2)
    db.session.commit()

    return [token1, token2]

@pytest.fixture()
def db_user_profile(app, db, users):
    user_profile = UserProfile(
        user_id=users[2]["id"],
        _username="sysadmin",
        _displayname="sysadmin user",
        fullname="test taro",
    )
    db.session.add(user_profile)
    db.session.commit()
    return user_profile


@pytest.fixture()
def db_notification_user_settings(app, db, users):
    notification_settings = NotificationsUserSettings(
        user_id=users[2]["id"],
        subscribe_email=True,
    )
    db.session.add(notification_settings)
    db.session.commit()
    return notification_settings
