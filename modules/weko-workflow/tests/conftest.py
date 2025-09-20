# -*- coding: utf-8 -*-
"""Pytest configuration."""

import copy
import os, sys
import shutil
import tempfile
import json
from unittest.mock import patch
import uuid
from datetime import datetime, timedelta
from six import BytesIO
from mock import patch

import pytest
from flask import Flask, url_for, Response
from flask_babelex import Babel, lazy_gettext as _
from flask_menu import Menu
from flask_oauthlib.provider import OAuth2Provider
from elasticsearch import Elasticsearch
from invenio_assets import InvenioAssets
from invenio_access import InvenioAccess
from invenio_access.models import ActionUsers,ActionRoles
from invenio_accounts.testutils import create_test_user
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import User, Role
from invenio_deposit import InvenioDeposit
from invenio_i18n import InvenioI18N
from invenio_cache import InvenioCache
from invenio_admin import InvenioAdmin
from invenio_db import InvenioDB, db as db_
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidrelations.contrib.records import RecordDraft
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_stats import InvenioStats
from invenio_search import RecordsSearch,InvenioSearch
from invenio_communities.views.ui import blueprint as invenio_communities_blueprint
from invenio_communities.models import Community
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_mail.models import MailTemplates, MailTemplateGenres, MailTemplateUsers, MailType
from invenio_oauth2server import InvenioOAuth2Server, InvenioOAuth2ServerREST
from invenio_oauth2server.models import Client, Token
from invenio_oauth2server.views import settings_blueprint as oauth2server_settings_blueprint
from invenio_records_ui import InvenioRecordsUI
from invenio_rest import InvenioREST
from weko_deposit.api import WekoIndexer, WekoRecord
from weko_deposit.api import WekoDeposit as WekoDepositAPI
from weko_search_ui.config import WEKO_SYS_USER
from weko_records_ui import WekoRecordsUI
from weko_admin import WekoAdmin
from weko_admin.models import SessionLifetime,Identifier
from weko_records.models import ItemTypeName, ItemType,FeedbackMailList,ItemTypeMapping,ItemTypeProperty
from weko_records.api import ItemsMetadata, Mapping
from weko_records.config import WEKO_RECORDS_REFERENCE_SUPPLEMENT
from weko_records_ui.models import FilePermission
from weko_user_profiles import WekoUserProfiles
from weko_index_tree.models import Index
from weko_logging.audit import WekoLoggingUserActivity
from weko_workflow import WekoWorkflow
from weko_search_ui import WekoSearchUI
from weko_workflow.models import ActionStatusPolicy, Activity, ActionStatus, Action, ActivityAction, WorkFlow, FlowDefine, FlowAction, ActionFeedbackMail, ActivityRequestMail, ActionIdentifier,FlowActionRole, ActivityHistory,GuestActivity, WorkflowRole
from weko_workflow.utils import MappingData, generate_guest_activity_token_value
from weko_workflow.views import workflow_blueprint as weko_workflow_blueprint
from weko_workflow.config import WEKO_WORKFLOW_ACTION_START,WEKO_WORKFLOW_ACTION_END,WEKO_WORKFLOW_ACTION_ITEM_REGISTRATION,WEKO_WORKFLOW_REQUEST_MAIL_ID,WEKO_WORKFLOW_ACTION_APPROVAL,WEKO_WORKFLOW_ACTION_ITEM_LINK,WEKO_WORKFLOW_ACTION_OA_POLICY_CONFIRMATION,WEKO_WORKFLOW_ACTION_IDENTIFIER_GRANT,WEKO_WORKFLOW_ACTION_ITEM_REGISTRATION_USAGE_APPLICATION,WEKO_WORKFLOW_ACTION_GUARANTOR,WEKO_WORKFLOW_ACTION_ADVISOR,WEKO_WORKFLOW_ACTION_ADMINISTRATOR,WEKO_WORKFLOW_REST_ENDPOINTS,WEKO_WORKFLOW_APPROVAL_PREVIEW,WEKO_WORKFLOW_ACTIVITYLOG_XLS_COLUMNS, DOI_VALIDATION_INFO, DOI_VALIDATION_INFO_CROSSREF, DOI_VALIDATION_INFO_DATACITE, DOI_VALIDATION_INFO_JALC, IDENTIFIER_GRANT_SELECT_DICT
from weko_workflow.ext import WekoWorkflowREST
from weko_workflow.scopes import activity_scope
from weko_theme.config import THEME_INSTITUTION_NAME
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database
from tests.helpers import json_data, create_record, fill_oauth2_headers, create_activity, create_flow
from invenio_files_rest.models import Location, Bucket,ObjectVersion
from invenio_files_rest import InvenioFilesREST
from invenio_records import InvenioRecords
from invenio_oauth2server import InvenioOAuth2Server
from invenio_pidrelations import InvenioPIDRelations
from invenio_pidstore import InvenioPIDStore
from weko_index_tree.api import Indexes
from weko_index_tree.models import Index
from weko_schema_ui.config import WEKO_SCHEMA_JPCOAR_V1_SCHEMA_NAME,WEKO_SCHEMA_DDI_SCHEMA_NAME
from weko_index_tree.config import WEKO_INDEX_TREE_DEFAULT_DISPLAY_NUMBER
from weko_user_profiles.models import UserProfile
from weko_authors.models import Authors
from invenio_records_files.api import RecordsBuckets
from weko_redis.redis import RedisConnection
from weko_items_ui import WekoItemsUI
from weko_admin.models import SiteInfo
from weko_admin import WekoAdmin
from weko_deposit import WekoDeposit
from weko_admin.models import AdminSettings
from weko_notifications import WekoNotifications
from weko_notifications.models import NotificationsUserSettings
from weko_logging.audit import WekoLoggingUserActivity

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

@pytest.fixture(scope="function")
def db_session(db_session):
    with patch.object(db_session, "remove", lambda: None):
        yield db_session

class MockEs():
    def __init__(self,**keywargs):
        self.indices = self.MockIndices()
        self.es = Elasticsearch()
        self.cluster = self.MockCluster()
    def index(self, id="",version="",version_type="",index="",doc_type="",body="",**arguments):
        pass
    def delete(self,id="",index="",doc_type="",**kwargs):
        return Response(response=json.dumps({}),status=500)
    def exists(self,**arguments):
        pass
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
                'name': _(\
                    'Creative Commons Attribution-ShareAlike 4.0 International '\
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
                'name': _(\
                    'Creative Commons Attribution-NoDerivatives 4.0 International '\
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
                'name': _(\
                    'Creative Commons Attribution-NonCommercial 4.0 International'\
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
                'name': _(\
                    'Creative Commons Attribution-NonCommercial-ShareAlike 4.0'\
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
                'name': _(\
                    'Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 '\
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
        WEKO_ITEMS_UI_USAGE_APPLICATION_TITLE_KEY="UsageApplication",
        WEKO_ITEMS_UI_USAGE_REPORT_TITLE_KEY="UsageReport",
        WEKO_ITEMS_UI_AUTO_FILL_TITLE_SETTING={"UsageApplication": ["ライフ利用申請","累積利用申請","組合せ分析利用申請","都道府県利用申請","地点情報利用申請",],"UsageReport": ["利用報告"],"OutputRegistration": ["成果物登録"]},
        WEKO_ITEMS_UI_AUTO_FILL_TITLE={"UsageApplication": {"en": "Usage Application","ja": "利用申請",},"UsageReport": {"en": "Usage Report","ja": "利用報告",},"OutputRegistration": {"en": "Output Registration","ja": "成果物",},},
        WEKO_ITEMS_UI_OUTPUT_REGISTRATION_TITLE={"en": "Output Registration","ja": "成果物",},
        WEKO_ITEMS_UI_OUTPUT_REGISTRATION_TITLE_KEY="OutputRegistration",
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
        WEKO_INDEX_TREE_DEFAULT_DISPLAY_NUMBER=WEKO_INDEX_TREE_DEFAULT_DISPLAY_NUMBER,
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
        WEKO_RECORDS_REFERENCE_SUPPLEMENT=WEKO_RECORDS_REFERENCE_SUPPLEMENT,
        WEKO_WORKFLOW_ACTION_START=WEKO_WORKFLOW_ACTION_START,
        WEKO_WORKFLOW_ACTION_END=WEKO_WORKFLOW_ACTION_END,
        WEKO_WORKFLOW_ACTION_ITEM_REGISTRATION=WEKO_WORKFLOW_ACTION_ITEM_REGISTRATION,
        WEKO_WORKFLOW_REQUEST_MAIL_ID=WEKO_WORKFLOW_REQUEST_MAIL_ID,
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
        IDENTIFIER_GRANT_SELECT_DICT=IDENTIFIER_GRANT_SELECT_DICT,
        WEKO_SYS_USER=WEKO_SYS_USER,
        RECORDS_UI_ENDPOINTS=dict(
            recid=dict(
                pid_type='recid',
                route='/records/<pid_value>',
                view_imp='weko_records_ui.views.default_view_method',
                template='weko_records_ui/detail.html',
                record_class='weko_deposit.api:WekoRecord',
                permission_factory_imp='weko_records_ui.permissions'
                                    ':page_permission_factory',
            ),
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
        THEME_INSTITUTION_NAME=THEME_INSTITUTION_NAME,
        OAUTH2_CACHE_TYPE='simple',
        WEKO_WORKFLOW_REST_ENDPOINTS=WEKO_WORKFLOW_REST_ENDPOINTS,
        WEKO_PERMISSION_ROLE_USER=[
            'System Administrator',
            'Repository Administrator',
            'Contributor',
            'Community Administrator'
        ],
        WEKO_WORKFLOW_APPROVAL_PREVIEW=WEKO_WORKFLOW_APPROVAL_PREVIEW,
        WEKO_WORKFLOW_USAGE_REPORT_WORKFLOW_NAME = '利用報告/Data Usage Report',
        WEKO_WORKFLOW_TODO_TAB = 'todo'
    )

    app_.testing = True
    Babel(app_)
    InvenioI18N(app_)
    Menu(app_)
    # InvenioTheme(app_)
    OAuth2Provider(app_)
    InvenioAccess(app_)
    InvenioAccounts(app_)
    InvenioFilesREST(app_)
    InvenioCache(app_)
    InvenioDB(app_)
    InvenioDeposit(app_)
    InvenioStats(app_)
    InvenioAssets(app_)
    InvenioAdmin(app_)
    InvenioPIDRelations(app_)
    InvenioJSONSchemas(app_)
    InvenioPIDStore(app_)
    InvenioRecords(app_)
    InvenioRecordsUI(app_)
    InvenioREST(app_)
    InvenioOAuth2Server(app_)
    InvenioOAuth2ServerREST(app_)
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
    WekoLoggingUserActivity(app_)
    WekoNotifications(app_)
    # WekoRecordsUI(app_)
    # app_.register_blueprint(invenio_theme_blueprint)
    app_.register_blueprint(invenio_communities_blueprint)
    # app_.register_blueprint(invenio_admin_blueprint)
    # app_.register_blueprint(invenio_accounts_blueprint)
    # app_.register_blueprint(weko_theme_blueprint)
    # app_.register_blueprint(weko_admin_blueprint)
    app_.register_blueprint(weko_workflow_blueprint)
    WekoWorkflowREST(app_)
    app_.register_blueprint(oauth2server_settings_blueprint)

    return app_


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app


@pytest.yield_fixture()
def i18n_app(app):
    with app.test_request_context(headers=[('If-None-Match', 'match')]):
        yield app


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
    user = User.query.filter_by(email='user@test.org').one_or_none()
    if not user:
        user = create_test_user(email='user@test.org')
    
    contributor = User.query.filter_by(email='user@test.org').one_or_none()
    if not contributor:
        contributor = create_test_user(email='contributor@test.org')

    comadmin = User.query.filter_by(email='comadmin@test.org').one_or_none()
    if not comadmin:
        comadmin = create_test_user(email='comadmin@test.org')

    repoadmin = User.query.filter_by(email='repoadmin@test.org').one_or_none()
    if not repoadmin:
        repoadmin = create_test_user(email='repoadmin@test.org')
    
    sysadmin = User.query.filter_by(email='sysadmin@test.org').one_or_none()
    if not sysadmin:
        sysadmin = create_test_user(email='sysadmin@test.org')

    generaluser = User.query.filter_by(email='generaluser@test.org').one_or_none()
    if not generaluser:
        generaluser = create_test_user(email='generaluser@test.org')

    originalroleuser = User.query.filter_by(email='originalroleuser@test.org').one_or_none()
    if not originalroleuser:
        originalroleuser = create_test_user(email='originalroleuser@test.org')

    originalroleuser2 = User.query.filter_by(email='originalroleuser2@test.org').one_or_none()
    if not originalroleuser2:
        originalroleuser2 = create_test_user(email='originalroleuser2@test.org')

    student = User.query.filter_by(email='student@test.org').one_or_none()
    if not student:
        student = create_test_user(email='student@test.org')

    sysadmin_role = Role.query.filter_by(name='System Administrator').one_or_none()
    if not sysadmin_role:
        sysadmin_role = ds.create_role(name='System Administrator')

    repoadmin_role = Role.query.filter_by(name='Repository Administrator').one_or_none()
    if not repoadmin_role:
        repoadmin_role = ds.create_role(name='Repository Administrator')

    contributor_role = Role.query.filter_by(name='Contributor').one_or_none()
    if not contributor_role:
        contributor_role = ds.create_role(name='Contributor')

    comadmin_role = Role.query.filter_by(name='Community Administrator').one_or_none()
    if not comadmin_role:
        comadmin_role = ds.create_role(name='Community Administrator')

    general_role = Role.query.filter_by(name='General').one_or_none()
    if not general_role:
        general_role = ds.create_role(name='General')
    
    originalrole = Role.query.filter_by(name='Original Role').one_or_none()
    if not originalrole:
        originalrole = ds.create_role(name='Original Role')
    
    studentrole = Role.query.filter_by(name='Student').one_or_none()
    if not studentrole:
        studentrole = ds.create_role(name='Student')
    
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

    index = Index.query.filter_by(id=1).one_or_none()
    if not index:
        index = Index(id=1,parent=0,position=0,index_name="com_index",display_no=5,public_state=True)
        db.session.add(index)
        db.session.commit()
    

    comm = Community.query.filter_by(id="comm01").one_or_none()
    if not comm:
        comm = Community.create(community_id="comm01", role_id=sysadmin_role.id,
                            id_user=sysadmin.id, title="test community",
                            description=("this is test community"),
                            root_node_id=index.id)
        db.session.add(comm)
        db.session.commit()

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
def users_1(app, db):
    """Create users."""
    ds = app.extensions['invenio-accounts'].datastore
    user_count = User.query.filter_by(email='user1@sample.com').count()
    if user_count != 1:
        user_1 = create_test_user(email='user1@sample.com')
    else:
        user_1 = User.query.filter_by(email='user1@sample.com').first()

    user_count = User.query.filter_by(email='user2@sample.com').count()
    if user_count != 1:
        user_2 = create_test_user(email='user2@sample.com')
    else:
        user_2 = User.query.filter_by(email='user2@sample.com').first()

    user_count = User.query.filter_by(email='sysadmin@test.org').count()
    if user_count != 1:
        sysadmin = create_test_user(email='sysadmin@test.org')
    else:
        sysadmin = User.query.filter_by(email='sysadmin@test.org').first()
        
    role_count = Role.query.filter_by(name='System Administrator').count()
    if role_count != 1:
        sysadmin_role = ds.create_role(name='System Administrator')
        general_role = ds.create_role(name='General')
    else:
        sysadmin_role = Role.query.filter_by(name='System Administrator').first()
        general_role = Role.query.filter_by(name='General').first()

    ds.add_role_to_user(sysadmin, sysadmin_role)
    ds.add_role_to_user(user_1, general_role)
    ds.add_role_to_user(user_2, general_role)

    # Assign access authorization
    with db.session.begin_nested():
        action_users = [
            ActionUsers(action='superuser-access', user=sysadmin),
        ]
        db.session.add_all(action_users)
        action_roles = [
            ActionRoles(action='superuser-access', role=sysadmin_role),
        ]
        db.session.add_all(action_roles)
    db.session.commit()
    index = Index.query.filter_by(id=1).one_or_none()
    if not index:
        index = Index(id=1,parent=0,position=0,index_name="com_index",display_no=5,public_state=True)
        db.session.add(index)
        db.session.commit()
    
    comm = Community.query.filter_by(id="comm01").one_or_none()
    if not comm:
        comm = Community.create(community_id="comm01", role_id=sysadmin_role.id,
                            id_user=sysadmin.id, title="test community",
                            description=("this is test community"),
                            root_node_id=index.id)
        db.session.add(comm)
        db.session.commit()
    db.session.commit()
    return [
        {'email': user_1.email, 'id': user_1.id, 'obj': user_1},
        {'email': user_2.email, 'id': user_2.id, 'obj': user_2},
        {'email': sysadmin.email, 'id': sysadmin.id, 'obj': sysadmin},
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
    workflows.append(create_flow(db, 1, "normal_flow","normal_workflow", None, None, item_type[0]['obj']))

    # action_role of action with action_id 1 is test_role01
    workflows.append(create_flow(db, 2, "test_role01_role_flow","test_role01_role_workfow",{5:{"value":roles[3].id,"flg":False}},None, item_type[0]['obj']))

    # action_role of action with action_id 1 is test_role02
    workflows.append(create_flow(db, 3, "test_role02_role_flow","test_role02_role_workfow",{5:{"value":roles[4].id,"flg":False}},None,item_type[0]['obj']))

    # action_role of action with action_id 1 is test_role01 and deny
    workflows.append(create_flow(db, 4, "test_role01_role_deny_flow","test_role01_role_deny_workfow",{5:{"value":roles[3].id,"flg":True}},None,item_type[0]['obj']))

    # action_role of action with action_id 1 is test_role02 and deny
    workflows.append(create_flow(db, 5, "test_role02_role_deny_flow","test_role02_role_deny_workfow",{5:{"value":roles[4].id,"flg":True}},None,item_type[0]['obj']))

    # action_user of action with action_id 1 is test_role01_user
    workflows.append(create_flow(db, 6,"test_role01_user_flow","test_role01_user_workflow",None,{5:{"value":users[2].id,"flg":False}},item_type[0]['obj']))

    # action_user of action with action_id 1 is test_role02_user
    workflows.append(create_flow(db, 7,"test_role02_user_flow","test_role02_user_workflow",None,{5:{"value":users[4].id,"flg":False}},item_type[0]['obj']))

    # action_user of action with action_id 1 is test_role01_user and deny
    workflows.append(create_flow(db, 8,"test_role01_user_deny_flow","test_role01_user_deny_workflow",None,{5:{"value":users[2].id,"flg":True}},item_type[0]['obj']))

    # action_user of action with action_id 1 is test_role02_user and deny
    workflows.append(create_flow(db, 9,"test_role02_user_deny_flow","test_role02_user_deny_workflow",None,{5:{"value":users[4].id,"flg":True}},item_type[0]['obj']))
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
def item_type_usage_report(db):
    with db.session.begin_nested():
        item_type_name = ItemTypeName(
            id=31003,
            name="利用報告-Data Usage Report",
            has_site_license=True,
            is_active=True
        )
        db.session.add(item_type_name)

        item_type_schema = dict()
        with open("tests/data/item_type/itemtype_schema_31003.json", "r") as f:
            item_type_schema = json.load(f)
        
        item_type_form = dict()
        with open("tests/data/item_type/itemtype_form_31003.json", "r") as f:
            item_type_form = json.load(f)

        item_type_render = dict()
        with open("tests/data/item_type/itemtype_render_31003.json", "r") as f:
            item_type_render = json.load(f)

        item_type_mapping = dict()
        with open("tests/data/item_type/itemtype_mapping_31003.json", "r") as f:
            item_type_mapping = json.load(f)

        item_type = ItemType(
            id=31003,
            name_id=31003,
            harvesting_type=False,
            schema=item_type_schema,
            form=item_type_form,
            render=item_type_render,
            tag=1,
            version_id=1,
            is_deleted=False,
        )

        db.session.add(item_type)

        item_type_mapping = ItemTypeMapping(
            id=31003,
            item_type_id=31003,
            mapping=item_type_mapping
        )

        db.session.add(item_type_mapping)
    return item_type

@pytest.fixture()
def workflow_usage_report(db, item_type_usage_report, action_data):
    workflow = create_flow(
        db,
        31001,
        "利用報告/Data Usage Report",
        "利用報告/Data Usage Report",
        None,
        None,
        item_type_usage_report
    )
    return workflow

@pytest.fixture()
def activity_usage_report(db, activity_acl_users, workflow_usage_report):
    users = activity_acl_users["users"]
    workflow = workflow_usage_report
    activities = [
        create_activity(db,"利用報告1",1,["4"],users[0],-1,workflow,'M',3),
        create_activity(db,"利用報告2",2,["4"],users[0],-1,workflow,'M',3),
        create_activity(db,"利用報告3",3,["4"],users[0],-1,workflow,'M',3),
        create_activity(db,"利用報告4",4,["4"],users[0],-1,workflow,'M',3),
        create_activity(db,"利用報告5",5,["4"],users[0],-1,workflow,'M',3),
        create_activity(db,"利用報告6",6,["4"],users[0],-1,workflow,'M',3),
        create_activity(db,"利用報告7",7,["4"],users[0],-1,workflow,'M',3),
        create_activity(db,"利用報告8",8,["4"],users[0],-1,workflow,'M',3),
        create_activity(db,"利用報告9",9,["4"],users[0],-1,workflow,'M',3),
        create_activity(db,"利用報告10",10,["4"],users[0],-1,workflow,'M',3),
    ]
    return activities


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
    item_types = []

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
    item_types.append({"id": item_type.id, "obj": item_type})


    # 31001: 利用申請
    item_type_name_31001 = ItemTypeName(
        id=31001, name="利用申請", has_site_license=True, is_active=True
    )
    item_type_schema_31001 = dict()
    with open("tests/data/item_type/itemtype_schema_31001.json", "r") as f:
        item_type_schema_31001 = json.load(f)

    item_type_form_31001 = dict()
    with open("tests/data/item_type/itemtype_form_31001.json", "r") as f:
        item_type_form_31001 = json.load(f)

    item_type_render_31001 = dict()
    with open("tests/data/item_type/itemtype_render_31001.json", "r") as f:
        item_type_render_31001 = json.load(f)

    item_type_mapping_31001 = dict()
    with open("tests/data/item_type/itemtype_mapping_31001.json", "r") as f:
        item_type_mapping_31001 = json.load(f)

    item_type_31001 = ItemType(
        id=31001,
        name_id=31001,
        harvesting_type=True,
        schema=item_type_schema_31001,
        form=item_type_form_31001,
        render=item_type_render_31001,
        tag=1,
        version_id=1,
        is_deleted=False,
    )

    item_type_mapping_31001 = ItemTypeMapping(id=31001, item_type_id=31001, mapping=item_type_mapping_31001)

    with db.session.begin_nested():
        db.session.add(item_type_name_31001)
        db.session.add(item_type_31001)
        db.session.add(item_type_mapping_31001)

    item_types.append({"id": 31001, "obj": item_type_31001})

    return item_types

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
def db_register_full_action(app, db, db_records, users, action_data, item_type):
    flow_define = FlowDefine.query.filter_by(flow_name='Registration Flow').one_or_none()
    if not flow_define:
        flow_define = FlowDefine(flow_id=uuid.uuid4(),
                             flow_name='Registration Flow',
                             flow_user=1)

    del_flow_define = FlowDefine.query.filter_by(flow_name='Delete Flow').one_or_none()
    if not del_flow_define:
        del_flow_define = FlowDefine(flow_id=uuid.uuid4(),
                                flow_name='Delete Flow',
                                flow_user=1,
                                flow_type='2')

    app_flow_define = FlowDefine.query.filter_by(flow_name='Delete Approval Flow').one_or_none()
    if not app_flow_define:
        app_flow_define = FlowDefine(flow_id=uuid.uuid4(),
                                flow_name='Delete Approval Flow',
                                flow_user=1,
                                flow_type='2')
    
    with db.session.begin_nested():
        db.session.add(flow_define)
        db.session.add(del_flow_define)
        db.session.add(app_flow_define)
    db.session.commit()

    flow_action1 = FlowAction.query.filter_by(flow_id=flow_define.flow_id, action_id=1).one_or_none()

    if not flow_action1:
        flow_action1 = FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=1,
                     action_version='1.0.0',
                     action_order=1,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={})
    
    flow_action2 = FlowAction.query.filter_by(flow_id=flow_define.flow_id, action_id=3, action_order=2).one_or_none()
    if not flow_action2:
        flow_action2 = FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=3,
                     action_version='1.0.0',
                     action_order=2,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={})
    
    flow_action3 = FlowAction.query.filter_by(flow_id=flow_define.flow_id, action_id=5).one_or_none()
    if not flow_action3:
        flow_action3 = FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=5,
                     action_version='1.0.0',
                     action_order=3,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={})
    
    flow_action4 = FlowAction.query.filter_by(flow_id=flow_define.flow_id, action_id=3, action_order=1).one_or_none()
    if not flow_action4:
        flow_action4 = FlowAction(status='N',
                     flow_id=flow_define.flow_id,
                     action_id=3,
                     action_version='1.0.0',
                     action_order=1,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={})
    
    del_flow_action1 = FlowAction.query.filter_by(flow_id=del_flow_define.flow_id, action_id=1).one_or_none()
    if not del_flow_action1:
        del_flow_action1 = FlowAction(status='N',
                     flow_id=del_flow_define.flow_id,
                     action_id=1,
                     action_version='1.0.0',
                     action_order=1,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2025/05/01 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={})

    del_flow_action2 = FlowAction.query.filter_by(flow_id=del_flow_define.flow_id, action_id=2).one_or_none()
    if not del_flow_action2:
        del_flow_action2 = FlowAction(status='N',
                     flow_id=del_flow_define.flow_id,
                     action_id=2,
                     action_version='1.0.0',
                     action_order=2,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2025/05/01 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={})
    
    app_flow_action1 = FlowAction.query.filter_by(flow_id=app_flow_define.flow_id, action_id=1).one_or_none()
    if not app_flow_action1:
        app_flow_action1 = FlowAction(status='N',
                     flow_id=app_flow_define.flow_id,
                     action_id=1,
                     action_version='1.0.0',
                     action_order=1,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2025/05/01 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={})
    
    app_flow_action2 = FlowAction.query.filter_by(flow_id=app_flow_define.flow_id, action_id=4).one_or_none()
    if not app_flow_action2:
        app_flow_action2 = FlowAction(status='N',
                     flow_id=app_flow_define.flow_id,
                     action_id=4,
                     action_version='1.0.0',
                     action_order=2,
                     action_condition='',
                     action_status='A',
                     action_date=datetime.strptime('2025/05/01 0:00:00','%Y/%m/%d %H:%M:%S'),
                     send_mail_setting={})
    
    app_flow_action3 = FlowAction.query.filter_by(flow_id=app_flow_define.flow_id, action_id=2).one_or_none()
    if not app_flow_action3:
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
        db.session.add(flow_action4)
        db.session.add(del_flow_action1)
        db.session.add(del_flow_action2)
        db.session.add(app_flow_action1)
        db.session.add(app_flow_action2)
        db.session.add(app_flow_action3)
    db.session.commit()

    action_role_1 = FlowActionRole.query.filter_by(flow_action_id=flow_action1.id, action_role=1, action_user=1).one_or_none()
    if not action_role_1:
        action_role_1 = FlowActionRole(flow_action_id=flow_action1.id,
                                   action_role=1,
                                   action_user=1)
    
    action_role_2_1 = FlowActionRole.query.filter_by(flow_action_id=flow_action2.id, action_role=1, action_user=2).one_or_none()    
    if not action_role_2_1:
        action_role_2_1 = FlowActionRole(flow_action_id=flow_action2.id,
                                   action_role=1,
                                   action_user=2)
    
    action_role_2_2 = FlowActionRole.query.filter_by(flow_action_id=flow_action2.id, action_role=2, action_user=1).one_or_none()    
    if not action_role_2_2:
        action_role_2_2 = FlowActionRole(flow_action_id=flow_action2.id,
                                   action_role=2,
                                   action_user=1)
    
    action_role_2_3 = FlowActionRole.query.filter_by(flow_action_id=flow_action2.id, action_role=2, action_user=2).one_or_none()
    if not action_role_2_3:
        action_role_2_3 = FlowActionRole(flow_action_id=flow_action2.id,
                                   action_role=2,
                                   action_user=2)
    
    action_role_2_4 = FlowActionRole.query.filter_by(flow_action_id=flow_action2.id, action_role=2, action_user=3).one_or_none()
    if not action_role_2_4:
        action_role_2_4 = FlowActionRole(flow_action_id=flow_action2.id,
                                   action_role=2,
                                   action_user=3)
    
    action_role_3 = FlowActionRole.query.filter_by(flow_action_id=flow_action3.id, action_role=1, action_user=3).one_or_none()
    if not action_role_3:
        action_role_3 = FlowActionRole(flow_action_id=flow_action3.id,
                                   action_role=1,
                                   action_user=3)

    action_role_4_1 = FlowActionRole.query.filter_by(flow_action_id=flow_action4.id, action_role=1, action_user=1, action_role_exclude=True, action_user_exclude=True).one_or_none()
    if not action_role_4_1:
        action_role_4_1 = FlowActionRole(flow_action_id=flow_action4.id,
                                   action_role=1,
                                   action_user=1,
                                   action_role_exclude=True,
                                   action_user_exclude=True
                                   )
    
    action_role_4_2 = FlowActionRole.query.filter_by(flow_action_id=flow_action4.id, action_role=1, action_user=2, action_role_exclude=True, action_user_exclude=True).one_or_none()    
    if not action_role_4_2:
        action_role_4_2 = FlowActionRole(flow_action_id=flow_action4.id,
                                   action_role=1,
                                   action_user=2,
                                   action_role_exclude=True,
                                   action_user_exclude=True
                                   )
    
    action_role_4_3 = FlowActionRole.query.filter_by(flow_action_id=flow_action4.id, action_role=1, action_user=3, action_role_exclude=False, action_user_exclude=False).one_or_none()  
    if not action_role_4_3:
        action_role_4_3 = FlowActionRole(flow_action_id=flow_action4.id,
                                   action_role=1,
                                   action_user=3,
                                   action_role_exclude=False,
                                   action_user_exclude=False
                                   )
    
    action_role_4_4 = FlowActionRole.query.filter_by(flow_action_id=flow_action4.id, action_role=2, action_user=1).one_or_none()
    if not action_role_4_4: 
        action_role_4_4 = FlowActionRole(flow_action_id=flow_action4.id,
                                   action_role=2,
                                   action_user=1
                                   )
    with db.session.begin_nested():
        db.session.add(action_role_1)
        db.session.add(action_role_2_1)
        db.session.add(action_role_2_2)
        db.session.add(action_role_2_3)
        db.session.add(action_role_2_4)
        db.session.add(action_role_3)
        db.session.add(action_role_4_1)
        db.session.add(action_role_4_2)
        db.session.add(action_role_4_3)
        db.session.add(action_role_4_4)
    db.session.commit()

    workflow = WorkFlow.query.filter_by(flows_name='test workflow1').one_or_none()
    if not workflow:
        workflow = WorkFlow(flows_id=uuid.uuid4(),
                        flows_name='test workflow1',
                        itemtype_id=1,
                        index_tree_id=None,
                        flow_id=1,
                        is_deleted=False,
                        open_restricted=False,
                        location_id=None,
                        is_gakuninrdm=False)
    
    del_workflow = WorkFlow.query.filter_by(flows_name='test delete workflow').one_or_none()
    if not del_workflow:
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
    
    app_del_workflow = WorkFlow.query.filter_by(flows_name='test delete approval workflow').one_or_none()
    if not app_del_workflow:
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
    
    activity = Activity.query.filter_by(activity_id='1').one_or_none()
    if not activity:
        activity = Activity(activity_id='1',workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=1,
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_ids='[]', extra_info={},
                    action_order=1,
                    )
    
    activity2 = Activity.query.filter_by(activity_id='A-00000001-10001').one_or_none()
    if not activity2:
        activity2 = Activity(activity_id='A-00000001-10001',workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=1,
                    action_status = 'M',
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_ids='[]', extra_info={},
                    action_order=6)

    activity3 = Activity.query.filter_by(activity_id='A-00000001-10002').one_or_none()
    if not activity3:
        activity3 = Activity(activity_id='A-00000001-10002',workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=1,
                    action_status = 'C',
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_ids=[], extra_info={},
                    action_order=6)

    del_activity = Activity.query.filter_by(activity_id='A-00000001-10010').one_or_none()
    if not del_activity:
        del_activity = Activity(activity_id='A-00000001-10010',workflow_id=2, flow_id=del_flow_define.id,
                    action_id=1, activity_login_user=1,
                    activity_update_user=1,
                    activity_start=datetime.strptime('2025/05/02 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_ids=[], extra_info={},
                    action_order=1,
                    )
    
    app_del_activity = Activity.query.filter_by(activity_id='A-00000001-10011').one_or_none()
    if not app_del_activity:
        app_del_activity = Activity(activity_id='A-00000001-10011',workflow_id=3, flow_id=app_flow_define.id,
                    action_id=1, activity_login_user=1,
                    activity_update_user=1,
                    activity_start=datetime.strptime('2025/05/02 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_ids=[], extra_info={},
                    action_order=1,
                    )
    
    activity_item1 = Activity.query.filter_by(activity_id='2').one_or_none()
    if not activity_item1:
        activity_item1 = Activity(activity_id='2',item_id=db_records[2][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item1', shared_user_ids=[], extra_info={},
                    action_order=1,
                    )
    
    activity_item2 = Activity.query.filter_by(activity_id='3').one_or_none()
    activity_item2 = Activity(activity_id='3', workflow_id=1, flow_id=flow_define.id,
                    action_id=3, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item2', shared_user_ids=[], extra_info={},
                    action_order=1,
                    )
    activity_item3 = Activity.query.filter_by(activity_id='4').one_or_none()
    if not activity_item3:
        activity_item3 = Activity(activity_id='4', workflow_id=1, flow_id=flow_define.id,
                    action_id=3, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item3', shared_user_ids=[], extra_info={},
                    action_order=1,
                    )
    
    activity_item4 = Activity.query.filter_by(activity_id='5').one_or_none()
    if not activity_item4:
        activity_item4 = Activity(activity_id='5', workflow_id=1, flow_id=flow_define.id,
                    action_id=3, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item4', shared_user_ids=[], extra_info={},
                    action_order=1,
                    )
        
    activity_item5 = Activity.query.filter_by(activity_id='6').one_or_none()
    if not activity_item5:
        activity_item5 = Activity(activity_id='6', workflow_id=1, flow_id=flow_define.id,
                    action_id=3, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item5', shared_user_ids=[], extra_info={},
                    action_order=1,
                    )
    
    activity_item6 = Activity.query.filter_by(activity_id='7').one_or_none()
    if not activity_item6:
        activity_item6 = Activity(activity_id='7', workflow_id=1, flow_id=flow_define.id,
                    action_id=3, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item5', shared_user_ids=[], extra_info={},
                    action_order=1,
                    )
    
    activity_item7 = Activity.query.filter_by(activity_id='8').one_or_none()
    if not activity_item7:
        activity_item7 = Activity(activity_id='8', item_id=db_records[0][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=3, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item8', shared_user_ids=[], extra_info={},
                    action_order=1,
                    )
    
    activity_item8 = Activity.query.filter_by(activity_id='9').one_or_none()
    if not activity_item8:
        activity_item8 = Activity(activity_id='9', item_id=db_records[1][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=3, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item8', shared_user_ids='[]', extra_info={},
                    action_order=1,
                    )
    
    activity_item9 = Activity.query.filter_by(activity_id='10').one_or_none()
    if not activity_item9:
        activity_item9 = Activity(activity_id='10', item_id=db_records[1][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=3, activity_login_user=users[5]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2023/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item9', shared_user_ids=[6], extra_info={},
                    action_order=1,
                    )
    
    activity_item10 = Activity.query.filter_by(activity_id='11').one_or_none()
    if not activity_item10:
        activity_item10 = Activity(activity_id='11', item_id=db_records[1][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=3, activity_login_user=users[0]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2023/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='制限公開', shared_user_ids=[2,4], extra_info={},
                    action_order=1,
                    )
    
    activity_guest = Activity.query.filter_by(activity_id='guest').one_or_none()
    if not activity_guest:
        activity_guest = Activity(activity_id='guest', item_id=db_records[1][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=3, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item8', shared_user_ids=[],
                    action_order=1,
                    extra_info={"guest_mail":"guest@test.org","record_id": 1,"related_title":"related_guest_activity","usage_record_id":str(db_records[1][2].id),"usage_activity_id":str(uuid.uuid4())}
                    )
    
    activity_landing_url = Activity.query.filter_by(activity_id='A-00000001-10003').one_or_none()
    if not activity_landing_url:
        activity_landing_url = Activity(activity_id='A-00000001-10003',workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=1,
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_ids=[], extra_info={"record_id": 1},
                    action_order=6)
    
    activity_terms_of_use = Activity.query.filter_by(activity_id='A-00000001-10004').one_or_none()
    if not activity_terms_of_use:
        activity_terms_of_use = Activity(activity_id='A-00000001-10004',workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=1,
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_ids=[], extra_info={"record_id": 1, "file_name":"aaa.txt"},
                    action_order=6)
    
    activity_no_contents = Activity.query.filter_by(activity_id='A-00000001-10005').one_or_none()
    if not activity_no_contents:
        activity_no_contents = Activity(activity_id='A-00000001-10005',workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=1,title='test', shared_user_ids=[], extra_info={"record_id": 1, "file_name":"recid/1.0"},
                    action_order=6)
    
    activity_guest_2 = Activity.query.filter_by(activity_id='guest_2').one_or_none()
    if not activity_guest_2:
        activity_guest_2 = Activity(activity_id='guest_2', item_id=db_records[1][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=3, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item11', shared_user_ids=[1],
                    action_order=1,
                    extra_info={"guest_mail":"guest@test.org","record_id": 2,"related_title":"related_guest_activity","usage_record_id":str(db_records[1][2].id),"usage_activity_id":str(uuid.uuid4())}
                    )

    activity_guest_3 = Activity.query.filter_by(activity_id='guest_3').one_or_none()
    if not activity_guest_3:
        activity_guest_3 = Activity(activity_id='guest_3', item_id=db_records[1][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=3, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item11', shared_user_ids=[1],
                    action_order=1,
                    extra_info={"guest_mail":"guest@test.org","record_id": 3,"related_title":"related_guest_activity","usage_record_id":str(db_records[1][2].id),"usage_activity_id":str(uuid.uuid4())}
                    )
    
    activity_guest_4 = Activity.query.filter_by(activity_id='guest_4').one_or_none()
    if not activity_guest_4:
        activity_guest_4 = Activity(activity_id='guest_4', item_id=db_records[1][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=3, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item11', shared_user_ids=[1],
                    action_order=1,
                    extra_info={"guest_mail":"guest@test.org","record_id": 4,"related_title":"related_guest_activity","usage_record_id":str(db_records[1][2].id),"usage_activity_id":str(uuid.uuid4())}
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
        db.session.add(activity_item9)
        db.session.add(activity_item10)
        db.session.add(activity_guest)
        db.session.add(activity_guest_2)
        db.session.add(activity_guest_3)
        db.session.add(activity_guest_4)
    db.session.commit()

    activity_action = ActivityAction.query.filter_by(activity_id=activity.activity_id, action_id=1).one_or_none()
    if not activity_action:
        activity_action = ActivityAction(activity_id=activity.activity_id,
                                     action_id=1,action_status="M",
                                     action_handler=1, action_order=1)
    activity_action1_item1 = ActivityAction.query.filter_by(activity_id=activity_item1.activity_id, action_id=1).one_or_none()
    if not activity_action1_item1:
        activity_action1_item1 = ActivityAction(activity_id=activity_item1.activity_id,
                                            action_id=1,action_status="M",
                                            action_handler=1, action_order=1)
    
    activity_action2_item1 = ActivityAction.query.filter_by(activity_id=activity_item1.activity_id, action_id=3).one_or_none()
    if not activity_action2_item1:
        activity_action2_item1 = ActivityAction(activity_id=activity_item1.activity_id,
                                            action_id=3,action_status="M",
                                            action_handler=1, action_order=2)
    
    activity_action3_item1 = ActivityAction.query.filter_by(activity_id=activity_item1.activity_id, action_id=5).one_or_none()
    if not activity_action3_item1:
        activity_action3_item1 = ActivityAction(activity_id=activity_item1.activity_id,
                                            action_id=5,action_status="M",
                                            action_handler=1, action_order=3)
    
    activity_action1_item2 = ActivityAction.query.filter_by(activity_id=activity_item2.activity_id, action_id=1).one_or_none()
    if not activity_action1_item2:
        activity_action1_item2 = ActivityAction(activity_id=activity_item2.activity_id,
                                            action_id=1,action_status="M",
                                            action_handler=1, action_order=1)
    activity_action2_item2 = ActivityAction.query.filter_by(activity_id=activity_item2.activity_id, action_id=3).one_or_none()
    if not activity_action2_item2:
        activity_action2_item2 = ActivityAction(activity_id=activity_item2.activity_id,
                                            action_id=3,action_status="M",
                                            action_handler=1, action_order=2)
    
    activity_action3_item2 = ActivityAction.query.filter_by(activity_id=activity_item2.activity_id, action_id=5).one_or_none()
    if not activity_action3_item2:
        activity_action3_item2 = ActivityAction(activity_id=activity_item2.activity_id,
                                            action_id=5,action_status="M",
                                            action_handler=1, action_order=3)
    
    activity_item2_feedbackmail = ActionFeedbackMail.query.filter_by(activity_id=activity_item2.activity_id, action_id=3).one_or_none()
    if not activity_item2_feedbackmail:
        activity_item2_feedbackmail = ActionFeedbackMail(activity_id='3',
                                action_id=3,
                                feedback_maillist=None
                                )
    activity_item3_feedbackmail = ActionFeedbackMail.query.filter_by(activity_id=activity_item3.activity_id, action_id=3).one_or_none()
    if not activity_item3_feedbackmail:
        activity_item3_feedbackmail = ActionFeedbackMail(activity_id='4',
                                action_id=3,
                                feedback_maillist=[{"email": "test@org", "author_id": ""}]
                                )
    
    activity_item4_feedbackmail = ActionFeedbackMail.query.filter_by(activity_id=activity_item4.activity_id, action_id=3).one_or_none()
    if not activity_item4_feedbackmail:
        activity_item4_feedbackmail = ActionFeedbackMail(activity_id='5',
                                action_id=3,
                                feedback_maillist=[{"email": "test@org", "author_id": "1"}]
                                )

    activity_item5_feedbackmail = ActionFeedbackMail.query.filter_by(activity_id=activity_item5.activity_id, action_id=3).one_or_none()
    if not activity_item5_feedbackmail:
        activity_item5_feedbackmail = ActionFeedbackMail(activity_id='6',
                                action_id=3,
                                feedback_maillist=[{"email": "test1@org", "author_id": "2"}]
                                )
    
    activity_item5_Authors = Authors.query.filter_by(id=1).one_or_none()
    if not activity_item5_Authors:
        activity_item5_Authors = Authors(id=1,json={'affiliationInfo': [{'affiliationNameInfo': [{'affiliationName': '', 'affiliationNameLang': 'ja', 'affiliationNameShowFlg': 'true'}], 'identifierInfo': [{'affiliationId': 'aaaa', 'affiliationIdType': '1', 'identifierShowFlg': 'true'}]}], 'authorIdInfo': [{'authorId': '1', 'authorIdShowFlg': 'true', 'idType': '1'}, {'authorId': '1', 'authorIdShowFlg': 'true', 'idType': '2'}], 'authorNameInfo': [{'familyName': '一', 'firstName': '二', 'fullName': '一\u3000二 ', 'language': 'ja-Kana', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'true'}], 'emailInfo': [{'email': 'test@org'}], 'gather_flg': 0, 'id': {'_id': 'HZ9iXYMBnq6bEezA2CK3', '_index': 'tenant1-authors-author-v1.0.0', '_primary_term': 29, '_seq_no': 0, '_shards': {'failed': 0, 'successful': 1, 'total': 2}, '_type': 'author-v1.0.0', '_version': 1, 'result': 'created'}, 'is_deleted': 'false', 'pk_id': '1'})
    
    activity_item6_feedbackmail = ActionFeedbackMail.query.filter_by(activity_id=activity_item6.activity_id, action_id=3).one_or_none()
    if not activity_item6_feedbackmail:
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

    activity_03 = Activity.query.filter_by(activity_id='A-00000003-00000').one_or_none()
    if not activity_03:
        activity_03 = Activity(activity_id='A-00000003-00000', workflow_id=1, flow_id=flow_define.id,
                    action_id=3, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item5', shared_user_ids='[]', extra_info={},
                    action_order=1,
                    )
    with db.session.begin_nested():
        db.session.add(activity_03)

    activity_action03_1 = ActivityAction.query.filter_by(activity_id=activity_03.activity_id, action_id=1).one_or_none()
    if not activity_action03_1:
        activity_action03_1 = ActivityAction(activity_id=activity_03.activity_id,
                                            action_id=1,action_status="M",action_comment="",
                                            action_handler=1, action_order=1)
    
    activity_action03_2 = ActivityAction.query.filter_by(activity_id=activity_03.activity_id, action_id=3).one_or_none()
    if not activity_action03_2:
        activity_action03_2 = ActivityAction(activity_id=activity_03.activity_id,
                                            action_id=3,action_status="F",action_comment="",
                                            action_handler=0, action_order=2)
    with db.session.begin_nested():
        db.session.add(activity_action03_1)
        db.session.add(activity_action03_2)
    db.session.commit()

    history = ActivityHistory.query.filter_by(activity_id=activity.activity_id, action_id=activity.action_id).one_or_none()
    if not history:
        history = ActivityHistory(
            activity_id=activity.activity_id,
            action_id=activity.action_id,
            action_order=activity.action_order,
        )

    with db.session.begin_nested():
        db.session.add(history)
    db.session.commit()
    
    doi_identifier = Identifier.query.filter_by(id=1).one_or_none()
    if not doi_identifier:
        doi_identifier = Identifier(id=1, repository='Root Index',jalc_flag= True,jalc_crossref_flag= True,jalc_datacite_flag=True,ndl_jalc_flag=True,
            jalc_doi='123',jalc_crossref_doi='1234',jalc_datacite_doi='12345',ndl_jalc_doi='123456',suffix='def',
            created_userId='1',created_date=datetime.strptime('2022-09-28 04:33:42','%Y-%m-%d %H:%M:%S'),
            updated_userId='1',updated_date=datetime.strptime('2022-09-28 04:33:42','%Y-%m-%d %H:%M:%S')
        )
    
    doi_identifier2 = Identifier.query.filter_by(id=2).one_or_none()
    if not doi_identifier2:
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
            'item_type':item_type[0]["obj"],
            'workflow':workflow,
            'action_feedback_mail':activity_item3_feedbackmail,
            'action_feedback_mail1':activity_item4_feedbackmail,
            'action_feedback_mail2':activity_item5_feedbackmail,
            'action_feedback_mail3':activity_item6_feedbackmail,
            'activities':[activity,activity_item1,activity_item2,activity_item3,activity_item7,activity_item8,activity_item9,activity_item10,activity_guest,activity_landing_url,activity_terms_of_use,activity_no_contents,activity_guest_2,activity_guest_3,activity_guest_4,del_activity,app_del_activity],
            'activity_actions':[activity_action,activity_action1_item1,activity_action2_item1,activity_action3_item1],
    }

@pytest.fixture()
def db_register_1(app, db, db_records, users_1, action_data, item_type):
    flow_define = FlowDefine(flow_id=uuid.uuid4(),
                             flow_name='Registration Flow',
                             flow_user=1)
    with db.session.begin_nested():
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
    with db.session.begin_nested():
        db.session.add(flow_action1)
        db.session.add(flow_action2)
        db.session.add(flow_action3)
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
    activity = Activity(activity_id='A-00000001-00005',item_id=db_records[2][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=users_1[0]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2023/09/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='テスト タイトル5', shared_user_ids=[{"user":2}], extra_info={},
                    action_order=1,
                    )

    with db.session.begin_nested():
        db.session.add(workflow)
        db.session.add(activity)
    db.session.commit()

    activity_action = ActivityAction(activity_id=activity.activity_id,
                                     action_id=1,action_status="M",
                                     action_handler=1, action_order=1)

    with db.session.begin_nested():
        db.session.add(activity_action)
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
            "activities":[activity]}


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
def db_records_1(db, location):
    record_data = json_data("data/test_records_1.json")
    item_data = json_data("data/test_items_1.json")
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
                title='test', shared_user_ids=[], extra_info={},
                action_order=1,
                )
    activity2 = Activity(activity_id='A-00000001-10001',workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=1,
                    action_status = 'M',
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_ids=[], extra_info={},
                    action_order=6)

    activity3 = Activity(activity_id='A-00000001-10002',workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=1,
                    action_status = 'C',
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_ids=[], extra_info={},
                    action_order=6)
    # identifier登録あり
    activity_item1 = Activity(activity_id='2',item_id=db_records[2][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item1', shared_user_ids=[], extra_info={},
                    action_order=1,
                    )
    # identifier登録なし
    activity_item2 = Activity(activity_id='3',item_id=db_records[4][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item1', shared_user_ids=[], extra_info={},
                    action_order=1,
                    )
    # ゲスト作成アクティビティ
    activity_item3 = Activity(activity_id='4',item_id=db_records[5][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item1', shared_user_ids=[], extra_info={"guest_mail":"guest@test.org"},
                    action_order=1,
                    )
    # item_idが"."を含まない
    activity_item4 = Activity(activity_id='5',item_id=db_records[0][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item1', shared_user_ids=[], extra_info={"guest_mail":"guest@test.org"},
                    action_order=1,
                    )
    # not identifier value in without_ver
    activity_item5 = Activity(activity_id='6',item_id=db_records[3][2].id,workflow_id=1, flow_id=flow_define.id,
                action_id=1, activity_login_user=users[3]["id"],
                activity_update_user=1,
                activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                activity_community_id=3,
                activity_confirm_term_of_use=True,
                title='test item1', shared_user_ids=[], extra_info={"guest_mail":"guest@test.org"},
                action_order=1,
                )
    # same identifier with without_ver
    activity_item6 = Activity(activity_id='7',item_id=db_records[1][2].id,workflow_id=1, flow_id=flow_define.id,
                action_id=1, activity_login_user=users[3]["id"],
                activity_update_user=1,
                activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                activity_community_id=3,
                activity_confirm_term_of_use=True,
                title='test item1', shared_user_ids=[], extra_info={"guest_mail":"guest@test.org"},
                action_order=1,
                )
    # delete flow activity
    del_activity = Activity(activity_id='A-00000001-10020',workflow_id=2, flow_id=del_flow_define.id,
                    action_id=1, activity_login_user=1,
                    activity_update_user=1,
                    activity_start=datetime.strptime('2025/05/02 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_ids=[], extra_info={},
                    action_order=1,
                    )
    # delete approval flow activity
    app_del_activity = Activity(activity_id='A-00000001-10021',item_id=db_records[7][2].id,workflow_id=3, flow_id=app_flow_define.id,
                    action_id=1, activity_login_user=1,
                    activity_update_user=1,
                    activity_start=datetime.strptime('2025/05/02 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_ids=[], extra_info={},
                    action_order=1,
                    )
    # delete two approval flow activity
    two_app_del_activity = Activity(activity_id='A-00000001-10022',item_id=db_records[8][2].id,workflow_id=4, flow_id=two_app_flow_define.id,
                    action_id=1, activity_login_user=1,
                    activity_update_user=1,
                    activity_start=datetime.strptime('2025/05/02 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_ids=[], extra_info={},
                    action_order=1,
                    )
    # delete flow activity
    two_app_del_activity2 = Activity(activity_id='A-00000001-10023',item_id=db_records[9][2].id,workflow_id=4, flow_id=two_app_flow_define.id,
                    action_id=1, activity_login_user=1,
                    activity_update_user=1,
                    activity_start=datetime.strptime('2025/05/02 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_ids=[], extra_info={},
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

    flow_action_role = FlowActionRole(
        flow_action_id=flow_actions[5].id,
        action_role=None,
        action_user=1
    )
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
def db_register_usage_application_workflows(app, db, action_data, item_type ):
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
        send_mail_setting={"inform_reject": {"mail": "0", "send": False}, "inform_approval": {"mail": "0", "send": False}, "request_approval": {"mail": "0", "send": False}},
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
        send_mail_setting={"inform_reject": {"mail": "0", "send": False}, "inform_approval": {"mail": "0", "send": False}, "request_approval": {"mail": "0", "send": False}},
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
        send_mail_setting={"inform_reject": {"mail": "0", "send": False}, "inform_approval": {"mail": "0", "send": True}, "request_approval": {"mail": "0", "send": False}},
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
        send_mail_setting={"inform_reject": {"mail": "0", "send": False}, "inform_approval": {"mail": "0", "send": False}, "request_approval": {"mail": "0", "send": False}},
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
        send_mail_setting={"inform_reject": {"mail": "0", "send": False}, "inform_approval": {"mail": "0", "send": False}, "request_approval": {"mail": "0", "send": False}},
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
        send_mail_setting={"inform_reject": {"mail": "0", "send": False}, "inform_approval": {"mail": "0", "send": False}, "request_approval": {"mail": "0", "send": False}},
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
        send_mail_setting={"inform_reject": {"mail": "0", "send": True}, "inform_approval": {"mail": "0", "send": True}, "request_approval": {"mail": "0", "send": True}},
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
        send_mail_setting={"inform_reject": {"mail": "0", "send": False}, "inform_approval": {"mail": "0", "send": False}, "request_approval": {"mail": "0", "send": False}},
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
        send_mail_setting={"inform_reject": {"mail": "0", "send": False}, "inform_approval": {"mail": "0", "send": False}, "request_approval": {"mail": "0", "send": False}},
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
        send_mail_setting={"inform_reject": {"mail": "0", "send": False}, "inform_approval": {"mail": "0", "send": False}, "request_approval": {"mail": "0", "send": False}},
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
        send_mail_setting={"inform_reject": {"mail": "0", "send": True}, "inform_approval": {"mail": "0", "send": True}, "request_approval": {"mail": "0", "send": True}},
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
        send_mail_setting={"inform_reject": {"mail": "0", "send": True}, "inform_approval": {"mail": "0", "send": True}, "request_approval": {"mail": "0", "send": True}},
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
		"flow_define1"        : flow_define1      
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
    return workflows


@pytest.fixture()
def db_register_usage_application(app, db, db_records, users, action_data, item_type, db_register_usage_application_workflows ):
    workflows = db_register_usage_application_workflows
    
    # 利用登録(now -> item_registration, next ->end)
    activity1 = Activity(activity_id='A-00000001-20001'
                        ,workflow_id=workflows["workflow_workflow1"].id
                        , flow_id=workflows["flow_define1"].id,
                    action_id=3, 
                    item_id=db_records[2][2].id,
                    activity_login_user=1,
                    action_status = 'M',
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=None,
                    activity_confirm_term_of_use=True,
                    title='test'
                    , shared_user_ids=[]
                    , extra_info={"file_name": "aaa.txt", "record_id": "1", "user_mail": "aaa@test.org", "related_title": "test", "is_restricted_access": True},
                    action_order=2)
    activity1_pre_action = ActivityAction(
        activity_id='A-00000001-20001'
        ,action_id=3
        ,action_status = 'M'
        ,action_order=2
        ,action_handler=-1
    )
    activity1_next_action = ActivityAction(
        activity_id='A-00000001-20001'
        ,action_id=2
        ,action_status = 'M'
        ,action_order=3
        ,action_handler=1
    )
    # 利用申請(next ->end)
    activity2 = Activity(activity_id='A-00000001-20002'
                        ,workflow_id=workflows["workflow_workflow3"].id
                        ,flow_id=workflows["flow_define3"].id
                        ,action_id=4
                        ,item_id=db_records[2][2].id
                    , activity_login_user=1
                    , action_status = 'M'
                    , activity_update_user=1
                    , activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f')
                    , activity_community_id=3
                    , activity_confirm_term_of_use=True
                    , title='test'
                    , shared_user_ids=[]
                    , extra_info={}
                    , action_order=3)
    activity2_pre_action = ActivityAction(
        activity_id='A-00000001-20002'
        ,action_id=4
        ,action_status = 'M'
        ,action_order=3
        ,action_handler=1
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
                        ,workflow_id=workflows["workflow_workflow4"].id
                        ,flow_id=workflows["flow_define4"].id
                        ,action_id=4
                        ,item_id=db_records[2][2].id
                        ,activity_login_user=1
                        ,action_status = 'M'
                        ,activity_update_user=1
                        ,activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f')
                        ,activity_community_id=3
                        ,activity_confirm_term_of_use=True
                        ,title='test'
                        ,shared_user_ids=[]
                        ,extra_info={"file_name": "aaa.txt", "record_id": "1", "user_mail": "aaa@test.org", "related_title": "test", "is_restricted_access": True}
                        ,action_order=3)
    activity3_pre_action = ActivityAction(
        activity_id='A-00000001-20003'
        ,action_id=4
        ,action_status = 'M'
        ,action_order=3
        ,action_handler=1
    )
    activity3_next_action = ActivityAction(
        activity_id='A-00000001-20003'
        ,action_id=4
        ,action_status = 'M'
        ,action_order=4
        ,action_handler=1
    )
    # ２段階利用申請(next ->end)
    activity4 = Activity(activity_id='A-00000001-20004'
                        ,workflow_id=workflows["workflow_workflow4"].id
                        ,flow_id=workflows["flow_define4"].id
                        ,action_id=4
                        ,item_id=db_records[2][2].id
                        ,activity_login_user=1
                        ,action_status = 'M'
                        ,activity_update_user=1
                        ,activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f')
                        ,activity_community_id=3
                        ,activity_confirm_term_of_use=True
                        ,title='test'
                        ,shared_user_ids=[]
                        ,extra_info={"file_name": "aaa.txt", "record_id": "1", "user_mail": "aaa@test.org", "related_title": "test", "is_restricted_access": True}
                        ,action_order=4)
    activity4_pre_action = ActivityAction(
        activity_id='A-00000001-20004'
        ,action_id=4
        ,action_status = 'M'
        ,action_order=4
        ,action_handler=1
    )
    activity4_next_action = ActivityAction(
        activity_id='A-00000001-20004'
        ,action_id=2
        ,action_status = 'M'
        ,action_order=5
        ,action_handler=1
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
    # 利用申請(next ->end)
    activity5 = Activity(activity_id='A-00000001-20005'
                        ,workflow_id=workflows["workflow_workflow3"].id
                        ,flow_id=workflows["flow_define3"].id
                        ,action_id=4
                        ,item_id=db_records[2][2].id
                    , activity_login_user=1
                    , action_status = 'M'
                    , activity_update_user=1
                    , activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f')
                    , activity_community_id=3
                    , activity_confirm_term_of_use=True
                    , title='test'
                    , shared_user_ids=[]
                    , extra_info={"file_name": "recid/15.0", "record_id": "1", "user_mail": "aaa@test.org", "related_title": "test", "is_restricted_access": True}
                    , action_order=3)
    activity5_pre_action = ActivityAction(
        activity_id='A-00000001-20005'
        ,action_id=4
        ,action_status = 'M'
        ,action_order=3
        ,action_handler=1
    )
    activity5_next_action = ActivityAction(
        activity_id='A-00000001-20005'
        ,action_id=2
        ,action_status = 'M'
        ,action_order=4
        ,action_handler=-1
    )
    file_permission = FilePermission(
        user_id = 1
        ,record_id= 1
        ,file_name= "aaa.txt"
        ,usage_application_activity_id='A-00000001-20005'
        ,usage_report_activity_id=None
        ,status = -1
    )
    with db.session.begin_nested():
        db.session.add(activity1)
        db.session.add(activity2)
        db.session.add(activity3)
        db.session.add(activity4)
        db.session.add(activity5)
    db.session.commit()
    with db.session.begin_nested():
        db.session.add(activity1_next_action)
        db.session.add(activity2_next_action)
        db.session.add(activity3_next_action)
        db.session.add(activity4_next_action)
        db.session.add(activity5_next_action)
        db.session.add(activity1_pre_action)
        db.session.add(activity2_pre_action)
        db.session.add(activity3_pre_action)
        db.session.add(activity4_pre_action)
        db.session.add(activity5_pre_action)
        db.session.add(file_permission)
        db.session.add(guest_activity)
    db.session.commit()
    workflows.update({
        "activity1":activity1
        ,"activity2":activity2
        ,"activity3":activity3
        ,"activity4":activity4
        ,"activity5":activity5
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
                title='test', shared_user_ids=[], extra_info={},
                action_order=1,
                )
    activity2 = Activity(activity_id='A-00000001-10001',workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=1,
                    action_status = 'M',
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_ids=[], extra_info={},
                    action_order=6)

    activity3 = Activity(activity_id='A-00000001-10002',workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=1,
                    action_status = 'C',
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_ids=[], extra_info={},
                    action_order=6)
    # identifier登録あり
    activity_item1 = Activity(activity_id='2',item_id=db_records[2][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item1', shared_user_ids=[], extra_info={},
                    action_order=1,
                    )
    # identifier登録なし
    activity_item2 = Activity(activity_id='3',item_id=db_records[4][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item1', shared_user_ids=[], extra_info={},
                    action_order=1,
                    )
    # ゲスト作成アクティビティ
    activity_item3 = Activity(activity_id='4',item_id=db_records[5][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item1', shared_user_ids=[], extra_info={"guest_mail":"guest@test.org"},
                    action_order=1,
                    )
    # item_idが"."を含まない
    activity_item4 = Activity(activity_id='5',item_id=db_records[0][2].id,workflow_id=1, flow_id=flow_define.id,
                    action_id=1, activity_login_user=users[3]["id"],
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test item1', shared_user_ids=[], extra_info={"guest_mail":"guest@test.org"},
                    action_order=1,
                    )
    # not identifier value in without_ver
    activity_item5 = Activity(activity_id='6',item_id=db_records[3][2].id,workflow_id=1, flow_id=flow_define.id,
                action_id=1, activity_login_user=users[3]["id"],
                activity_update_user=1,
                activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                activity_community_id=3,
                activity_confirm_term_of_use=True,
                title='test item1', shared_user_ids=[], extra_info={"guest_mail":"guest@test.org"},
                action_order=1,
                )
    # same identifier with without_ver
    activity_item6 = Activity(activity_id='7',item_id=db_records[1][2].id,workflow_id=1, flow_id=flow_define.id,
                action_id=1, activity_login_user=users[3]["id"],
                activity_update_user=1,
                activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                activity_community_id=3,
                activity_confirm_term_of_use=True,
                title='test item1', shared_user_ids=[], extra_info={"guest_mail":"guest@test.org"},
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
        action_user_exclude = False,
        action_request_mail = True)
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
            "activities":[activity,activity_item1,activity_item2,activity_item3,activity_item4,activity_item5,activity_item6]}


@pytest.fixture()
def workflow_approval(app, db, item_type, action_data, users):
    """Register data for approval API in DB."""

    # Register data in workflow_flow_define table
    flow_define = FlowDefine(flow_id=uuid.uuid4(), flow_name='Registration Flow', flow_user=1,)
    with db.session.begin_nested():
        db.session.add(flow_define)
    db.session.commit()

    # Register data in workflow_flow_action table
    flow_actions = []
    # start
    flow_actions.append(
        FlowAction(
            status='N',
            flow_id=flow_define.flow_id,
            action_id=1,
            action_version='1.0.0',
            action_order=1,
            action_condition='',
            action_status='A',
            action_date=datetime.strptime('2023/07/01 14:00:00', '%Y/%m/%d %H:%M:%S'),
            send_mail_setting={},
        )
    )
    # item register
    flow_actions.append(
        FlowAction(
            status='N',
            flow_id=flow_define.flow_id,
            action_id=3,
            action_version='1.0.0',
            action_order=2,
            action_condition='',
            action_status='A',
            action_date=datetime.strptime('2023/07/01 14:00:00', '%Y/%m/%d %H:%M:%S'),
            send_mail_setting={},
        )
    )
    # item link
    flow_actions.append(
        FlowAction(
            status='N',
            flow_id=flow_define.flow_id,
            action_id=5,
            action_version='1.0.0',
            action_order=3,
            action_condition='',
            action_status='A',
            action_date=datetime.strptime('2023/07/01 14:00:00', '%Y/%m/%d %H:%M:%S'),
            send_mail_setting={},
        )
    )
    # identifier grant
    flow_actions.append(
        FlowAction(
            status='N',
            flow_id=flow_define.flow_id,
            action_id=7,
            action_version='1.0.0',
            action_order=4,
            action_condition='',
            action_status='A',
            action_date=datetime.strptime('2023/07/01 14:00:00', '%Y/%m/%d %H:%M:%S'),
            send_mail_setting={},
        )
    )
    # approval
    flow_actions.append(
        FlowAction(
            status='N',
            flow_id=flow_define.flow_id,
            action_id=4,
            action_version='1.0.0',
            action_order=5,
            action_condition='',
            action_status='A',
            action_date=datetime.strptime('2023/07/01 14:00:00', '%Y/%m/%d %H:%M:%S'),
            send_mail_setting={},
        )
    )
    # approval
    flow_actions.append(
        FlowAction(
            status='N',
            flow_id=flow_define.flow_id,
            action_id=4,
            action_version='1.0.0',
            action_order=6,
            action_condition='',
            action_status='A',
            action_date=datetime.strptime('2023/07/01 14:00:00', '%Y/%m/%d %H:%M:%S'),
            send_mail_setting={},
        )
    )
    # end
    flow_actions.append(
        FlowAction(
            status='N',
            flow_id=flow_define.flow_id,
            action_id=2,
            action_version='1.0.0',
            action_order=7,
            action_condition='',
            action_status='A',
            action_date=datetime.strptime('2023/07/01 14:00:00', '%Y/%m/%d %H:%M:%S'),
            send_mail_setting={},
        )
    )
    with db.session.begin_nested():
        db.session.add_all(flow_actions)
    db.session.commit()

    # Register data in workflow_workflow table
    workflow = WorkFlow(
        flows_id=uuid.uuid4(),
        flows_name='test workflow01',
        itemtype_id=1,
        index_tree_id=None,
        flow_id=1,
        is_deleted=False,
        open_restricted=False,
        location_id=None,
        is_gakuninrdm=False,
    )
    with db.session.begin_nested():
        db.session.add(workflow)
    db.session.commit()

    return {
        "flow": flow_define,
        "flow_action": flow_actions,
        "workflow": workflow
    }


@pytest.fixture()
def db_register_approval(app, db, db_records, workflow_approval, users):
    """Register data for approval API in DB."""

    # Register data in workflow_activity table
    # Next action is approval
    activities = []
    activities.append(
        Activity(
            activity_id='1', item_id=db_records[0][2].id, workflow_id=1, flow_id=workflow_approval['flow'].id, action_id=4,
            activity_login_user=1, activity_update_user=1,
            activity_start=datetime.strptime('2023/07/10 10:00:00.000', '%Y/%m/%d %H:%M:%S.%f'),
            activity_community_id=3,
            activity_confirm_term_of_use=True,
            title='test', shared_user_ids=[], extra_info={}, action_order=5,
        )
    )
    # Next action is item register
    activities.append(
        Activity(
            activity_id='2', item_id=db_records[1][2].id, workflow_id=1, flow_id=workflow_approval['flow'].id, action_id=3,
            activity_login_user=1, activity_update_user=1,
            activity_start=datetime.strptime('2023/07/10 10:00:00.000', '%Y/%m/%d %H:%M:%S.%f'),
            activity_community_id=3,
            activity_confirm_term_of_use=True,
            title='test', shared_user_ids=[], extra_info={}, action_order=2,
        )
    )
    with db.session.begin_nested():
        db.session.add_all(activities)
    db.session.commit()

    # Register data in workflow_activity_action table
    activity1_actions = []
    activity1_actions.append(ActivityAction(activity_id=activities[0].activity_id, action_id=1, action_status="F", action_handler=1, action_order=1,))
    activity1_actions.append(ActivityAction(activity_id=activities[0].activity_id, action_id=3, action_status="F", action_handler=1, action_order=2,))
    activity1_actions.append(ActivityAction(activity_id=activities[0].activity_id, action_id=5, action_status="F", action_handler=1, action_order=3,))
    activity1_actions.append(ActivityAction(activity_id=activities[0].activity_id, action_id=7, action_status="F", action_handler=1, action_order=4,))
    activity1_actions.append(ActivityAction(activity_id=activities[0].activity_id, action_id=4, action_status="F", action_handler=1, action_order=5,))
    activity1_actions.append(ActivityAction(activity_id=activities[0].activity_id, action_id=4, action_status="F", action_handler=1, action_order=6,))
    activity1_actions.append(ActivityAction(activity_id=activities[0].activity_id, action_id=2, action_status="F", action_handler=1, action_order=7,))
    activity2_actions = []
    activity2_actions.append(ActivityAction(activity_id=activities[1].activity_id, action_id=1, action_status="F", action_handler=1, action_order=1,))
    activity2_actions.append(ActivityAction(activity_id=activities[1].activity_id, action_id=3, action_status="F", action_handler=1, action_order=2,))
    activity2_actions.append(ActivityAction(activity_id=activities[1].activity_id, action_id=5, action_status="F", action_handler=1, action_order=3,))
    activity2_actions.append(ActivityAction(activity_id=activities[1].activity_id, action_id=7, action_status="F", action_handler=1, action_order=4,))
    activity2_actions.append(ActivityAction(activity_id=activities[1].activity_id, action_id=4, action_status="F", action_handler=1, action_order=5,))
    activity2_actions.append(ActivityAction(activity_id=activities[1].activity_id, action_id=4, action_status="F", action_handler=1, action_order=6,))
    activity2_actions.append(ActivityAction(activity_id=activities[1].activity_id, action_id=2, action_status="F", action_handler=1, action_order=7,))
    with db.session.begin_nested():
        db.session.add_all(activity1_actions)
        db.session.add_all(activity2_actions)
    db.session.commit()

    # Register data in workflow_action_history table
    activity1_histories = []
    activity1_histories.append(
        ActivityHistory(
            activity_id=activities[0].activity_id,
            action_id=workflow_approval['flow_action'][0].action_id,
            action_version=workflow_approval['flow_action'][0].action_version,
            action_status='F',
            action_user=users[2]['id'],
            action_date=datetime.strptime('2023/07/10 10:00:01.000', '%Y/%m/%d %H:%M:%S.%f'),
            action_comment=None,
            action_order=workflow_approval['flow_action'][0].action_order,
        )
    )
    activity1_histories.append(
        ActivityHistory(
            activity_id=activities[0].activity_id,
            action_id=workflow_approval['flow_action'][1].action_id,
            action_version=workflow_approval['flow_action'][1].action_version,
            action_status='F',
            action_user=users[2]['id'],
            action_date=datetime.strptime('2023/07/10 10:00:03.000', '%Y/%m/%d %H:%M:%S.%f'),
            action_comment=None,
            action_order=workflow_approval['flow_action'][1].action_order,
        )
    )
    activity1_histories.append(
        ActivityHistory(
            activity_id=activities[0].activity_id,
            action_id=workflow_approval['flow_action'][2].action_id,
            action_version=workflow_approval['flow_action'][2].action_version,
            action_status='F',
            action_user=users[2]['id'],
            action_date=datetime.strptime('2023/07/10 10:00:05.000', '%Y/%m/%d %H:%M:%S.%f'),
            action_comment=None,
            action_order=workflow_approval['flow_action'][2].action_order,
        )
    )
    activity1_histories.append(
        ActivityHistory(
            activity_id=activities[0].activity_id,
            action_id=workflow_approval['flow_action'][3].action_id,
            action_version=workflow_approval['flow_action'][3].action_version,
            action_status='F',
            action_user=users[2]['id'],
            action_date=datetime.strptime('2023/07/10 10:00:07.000', '%Y/%m/%d %H:%M:%S.%f'),
            action_comment=None,
            action_order=workflow_approval['flow_action'][3].action_order,
        )
    )
    activity2_histories = []
    activity2_histories.append(
        ActivityHistory(
            activity_id=activities[1].activity_id,
            action_id=workflow_approval['flow_action'][0].action_id,
            action_version=workflow_approval['flow_action'][0].action_version,
            action_status='F',
            action_user=users[2]['id'],
            action_date=datetime.strptime('2023/07/10 10:00:01.000', '%Y/%m/%d %H:%M:%S.%f'),
            action_comment=None,
            action_order=workflow_approval['flow_action'][0].action_order,
        )
    )
    with db.session.begin_nested():
        db.session.add_all(activity1_histories)
        db.session.add_all(activity2_histories)
    db.session.commit()

    return {
        'activity': activities,
        'action': [activity1_actions, activity2_actions],
        'activity_history': [activity1_histories, activity2_histories]
    }


@pytest.fixture()
def db_register_activity(app, db, db_records, workflow_approval, users):
    """Data for GetActivities."""

    # Register data in workflow_activity table
    activities = []
    activities.append(
        Activity(
            activity_id='A-20230714-00001',
            item_id=db_records[0][2].id,
            workflow_id=1,
            flow_id=1,
            action_id=1,
            activity_login_user=users[0]['id'],
            activity_update_user=users[0]['id'],
            activity_status='B',
            activity_start=datetime.strptime('2023/07/10 10:00:00.000', '%Y/%m/%d %H:%M:%S.%f'),
            activity_community_id=3,
            activity_confirm_term_of_use=True,
            title='contributor-todo',
            shared_user_ids=[{'user': users[0]['id']}],
            extra_info={},
            action_order=5
        )
    )
    activities.append(
        Activity(
            activity_id='A-20230714-00002',
            item_id=db_records[0][2].id,
            workflow_id=1,
            flow_id=1,
            action_id=1,
            activity_login_user=users[2]['id'],
            activity_update_user=users[2]['id'],
            activity_status='B',
            activity_start=datetime.strptime('2023/07/10 10:00:00.000', '%Y/%m/%d %H:%M:%S.%f'),
            activity_community_id=3,
            activity_confirm_term_of_use=True,
            title='sysadmin-todo',
            shared_user_ids=[{'user': users[2]['id']}],
            extra_info={},
            action_order=7
        )
    )
    activities.append(
        Activity(
            activity_id='A-20230714-00003',
            item_id=db_records[0][2].id,
            workflow_id=1,
            flow_id=1,
            action_id=2,
            activity_login_user=users[0]['id'],
            activity_update_user=users[0]['id'],
            activity_status='M',
            activity_start=datetime.strptime('2023/07/10 10:00:00.000', '%Y/%m/%d %H:%M:%S.%f'),
            activity_community_id=3,
            activity_confirm_term_of_use=True,
            title='contributor-wait',
            shared_user_ids=[{'user': users[2]['id']}],
            extra_info={},
            action_order=5
        )
    )
    with db.session.begin_nested():
        db.session.add_all(activities)
    db.session.commit()

    # Register data in workflow_flow_define table
    flow_define = FlowDefine(flow_name='Registration Activities', flow_user=1,)
    with db.session.begin_nested():
        db.session.add(flow_define)
    db.session.commit()

    # Register data in workflow_flow_action table
    flow_actions = []
    flow_actions.append(
        FlowAction(
            status='N',
            flow_id=flow_define.flow_id,
            action_id=1,
            action_version='1.0.0',
            action_order=5,
            action_condition='',
            action_status='A',
            action_date=datetime.strptime('2023/07/01 14:00:00', '%Y/%m/%d %H:%M:%S'),
            send_mail_setting={},
        )
    )
    flow_actions.append(
        FlowAction(
            status='N',
            flow_id=flow_define.flow_id,
            action_id=1,
            action_version='1.0.0',
            action_order=5,
            action_condition='',
            action_status='A',
            action_date=datetime.strptime('2023/07/01 14:00:00', '%Y/%m/%d %H:%M:%S'),
            send_mail_setting={},
        )
    )
    with db.session.begin_nested():
        db.session.add_all(flow_actions)
    db.session.commit()

    # Register data in workflow_activity_action table
    activity1_actions = []
    activity1_actions.append(
        ActivityAction(
            activity_id=activities[2].activity_id,
            action_id=2,
            action_status='M',
            action_handler=users[2]['id'],
            action_order=5
        )
    )
    with db.session.begin_nested():
        db.session.add_all(activity1_actions)
    db.session.commit()

    return {
        'activity': activities,
    }


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
def db_guestactivity(app, db, db_register_full_action):
    activity_id1 = db_register_full_action['activities'][1].activity_id
    activity_id2 = db_register_full_action['activities'][0].activity_id
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
def client_oauth(users):
    """Create client."""
    # create resource_owner -> client_1
    client_ = Client(
        client_id='client_test_u1c1',
        client_secret='client_test_u1c1',
        name='client_test_u1c1',
        description='',
        is_confidential=False,
        user=users[2]['obj'],
        _redirect_uris='',
        _default_scopes='',
    )
    with db_.session.begin_nested():
        db_.session.add(client_)
    db_.session.commit()
    return client_


@pytest.fixture()
def create_oauth_token(client, client_oauth, users):
    """Create token."""
    token1_ = Token(
        client=client_oauth,
        user=users[2]['obj'],   # sysadmin
        token_type='u',
        access_token='dev_access_1',
        refresh_token='dev_refresh_1',
        expires=datetime.now() + timedelta(hours=10),
        is_personal=False,
        is_internal=True,
        _scopes=activity_scope.id,
    )
    token2_ = Token(
        client=client_oauth,
        user=users[8]['obj'],   # student
        token_type='u',
        access_token='dev_access_2',
        refresh_token='dev_refresh_2',
        expires=datetime.now() + timedelta(hours=10),
        is_personal=False,
        is_internal=True,
        _scopes=activity_scope.id,
    )
    token3_ = Token(
        client=client_oauth,
        user=users[4]['obj'],   # generaluser
        token_type='u',
        access_token='dev_access_3',
        refresh_token='dev_refresh_3',
        expires=datetime.now() + timedelta(hours=10),
        is_personal=False,
        is_internal=True,
        _scopes=activity_scope.id,
    )
    token4_ = Token(
        client=client_oauth,
        user=users[4]['obj'],   # generaluser
        token_type='u',
        access_token='dev_access_4',
        refresh_token='dev_refresh_4',
        expires=datetime.now() + timedelta(hours=10),
        is_personal=False,
        is_internal=True,
        _scopes=None,
    )
    with db_.session.begin_nested():
        db_.session.add(token1_)
        db_.session.add(token2_)
        db_.session.add(token3_)
        db_.session.add(token4_)
    db_.session.commit()
    return [token1_, token2_, token3_, token4_]


@pytest.fixture()
def json_headers():
    """JSON headers."""
    return [('Content-Type', 'application/json'), ('Accept', 'application/json')]


@pytest.fixture()
def auth_headers(client, json_headers, create_oauth_token):
    """Authentication headers (with a valid oauth2 token).

    It uses the token associated with the first user.
    """
    return [
        fill_oauth2_headers(json_headers, create_oauth_token[0]),   # sysadmin
        fill_oauth2_headers(json_headers, create_oauth_token[1]),   # student
        json_headers,                                               # not login
        fill_oauth2_headers(json_headers, create_oauth_token[2]),   # generaluser
        fill_oauth2_headers(json_headers, create_oauth_token[3]),   # generaluser(no scope)
    ]


@pytest.fixture()
def activity_with_roles(app, workflow, db, item_type, users):
    # flow action role
    flow_actions = workflow['flow_action']
    flow_action_roles = [
        FlowActionRole(id = 1,
                    flow_action_id = flow_actions[2].id,
                    action_user_exclude = False,
                    action_item_registrant = False),
        FlowActionRole(id = 2,
                    flow_action_id = flow_actions[3].id,
                    action_user_exclude = False,
                    action_item_registrant = True),
        FlowActionRole(id = 3,
                    flow_action_id = flow_actions[4].id,
                    action_user_exclude = True,
                    action_item_registrant = False),
        FlowActionRole(id = 4,
                    flow_action_id = flow_actions[5].id,
                    action_user_exclude = True,
                    action_item_registrant = True),
    ]
    with db.session.begin_nested():
        db.session.add_all(flow_action_roles)
    db.session.commit()

    item_metdata = ItemsMetadata.create(
        data = {
            "id": "1",
            "pid": {
                "type": "depid",
                "value": "1",
                "revision_id": 0
            },
            "lang": "ja",
            "owner": str(users[0]['obj'].id),
            "title": "sample01",
            "owners": [
                users[0]['obj'].id
            ],
            "status": "published",
            "$schema": "/items/jsonschema/" + str(item_type[0].get("id")),
            "pubdate": "2020-08-29",
            "created_by": users[0]['obj'].id,
            "owners_ext": {
                "email": "sample@nii.ac.jp",
                "username": "sample",
                "displayname": "sample"
            },
            "shared_user_ids": [],
            "item_1617186331708": [
                {
                "subitem_1551255647225": "sample01",
                "subitem_1551255648112": "ja"
                }
            ],
            "item_1617258105262": {
                "resourceuri": "http://purl.org/coar/resource_type/c_5794",
                "resourcetype": "conference paper"
            }
        },
        item_type_id = item_type[0].get("id"),
    )

    # set activity
    activity = Activity(
        activity_id='1', workflow_id=workflow["workflow"].id,
        flow_id=workflow["flow"].id,
        action_id=4,
        activity_login_user=users[0]['obj'].id,
        activity_update_user=1,
        activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
        activity_community_id=3,
        activity_confirm_term_of_use=True,
        title='test', shared_user_ids=[], extra_info={},
        action_order=6, item_id=item_metdata.model.id,
        action_status=ActionStatusPolicy.ACTION_BEGIN
    )
    with db.session.begin_nested():
        db.session.add(activity)
    db.session.commit()

    activity_action = ActivityAction(activity_id=activity.activity_id,
                                    action_id=4,action_status="M",
                                    action_handler=1, action_order=6)

    with db.session.begin_nested():
        db.session.add(activity_action)
    db.session.commit()

    return {
        "activity": activity,
        "itemMetadata": item_metdata
    }

@pytest.fixture()
def activity_with_roles_for_request_mail(app, workflow, db, item_type, users):
    # flow action role
    flow_actions = workflow['flow_action']
    flow_action_roles = [
        FlowActionRole(id = 1,
                    flow_action_id = flow_actions[2].id,
                    action_role = 2,
                    action_role_exclude = False),
        FlowActionRole(id = 2,
                    flow_action_id = flow_actions[3].id,
                    action_role = 2,
                    action_role_exclude = True),
        FlowActionRole(id = 3,
                    flow_action_id = flow_actions[4].id,
                    action_user_exclude = False,
                    action_request_mail = True),
        FlowActionRole(id = 4,
                    flow_action_id = flow_actions[5].id,
                    action_user_exclude = True,
                    action_request_mail = True),
        FlowActionRole(id = 5,
                    flow_action_id = flow_actions[1].id,
                    action_user = 2,
                    action_user_exclude = False,
                    )            
    ]
    with db.session.begin_nested():
        db.session.add_all(flow_action_roles)
    db.session.commit()

    item_metdata = ItemsMetadata.create(
        data = {
            "id": "1",
            "pid": {
                "type": "depid",
                "value": "1",
                "revision_id": 0
            },
            "lang": "ja",
            "owner": str(users[0]['obj'].id),
            "title": "sample01",
            "owners": [
                users[0]['obj'].id
            ],
            "status": "published",
            "$schema": "/items/jsonschema/" + str(item_type[0].get("id")),
            "pubdate": "2020-08-29",
            "created_by": users[0]['obj'].id,
            "owners_ext": {
                "email": "sample@nii.ac.jp",
                "username": "sample",
                "displayname": "sample"
            },
            "shared_user_ids": [],
            "item_1617186331708": [
                {
                "subitem_1551255647225": "sample01",
                "subitem_1551255648112": "ja"
                }
            ],
            "item_1617258105262": {
                "resourceuri": "http://purl.org/coar/resource_type/c_5794",
                "resourcetype": "conference paper"
            }
        },
        item_type_id = item_type[0].get("id"),
    )

    # set activity
    activity = Activity(
        activity_id='1', workflow_id=workflow["workflow"].id,
        flow_id=workflow["flow"].id,
        action_id=4,
        activity_login_user=users[0]['obj'].id,
        activity_update_user=1,
        activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
        activity_community_id=3,
        activity_confirm_term_of_use=True,
        title='test', shared_user_ids=[], extra_info={},
        action_order=6, item_id=item_metdata.model.id,
        action_status=ActionStatusPolicy.ACTION_BEGIN
    )
    
    with db.session.begin_nested():
        db.session.add(activity)
    db.session.commit()

    activity_action = ActivityAction(activity_id=activity.activity_id,
                                    action_id=4,action_status="M",
                                    action_handler=1, action_order=6)

    with db.session.begin_nested():
        db.session.add(activity_action)
    db.session.commit()

    request_mail = ActivityRequestMail(activity_id = activity.activity_id,
                                    display_request_button = True,
                                    request_maillist = [{"email": "contributor@test.org", "author_id": "1"}])
    
    with db.session.begin_nested():
        db.session.add(request_mail)
    db.session.commit()

    return {
        "activity": activity,
        "itemMetadata": item_metdata
    }

@pytest.fixture()
def db_register_for_application_api_workflow(app, db, action_data, item_type):
    #workflow_flow_define
    flow_id1 = uuid.uuid4()
    flow_id2 = uuid.uuid4()
    flow_define1 = FlowDefine(
        flow_id=flow_id1, flow_name="利用申請", flow_user=1, flow_status="A"
    )
    flow_define2 = FlowDefine(
        flow_id=flow_id2, flow_name="利用申請_with_index_tree_id", flow_user=1, flow_status="A"
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
        send_mail_setting={"inform_reject": {"mail": "0", "send": False}, "inform_approval": {"mail": "0", "send": False}, "request_approval": {"mail": "0", "send": False}},
    )
    flow_action1_2 = FlowAction(
        status="N",
        flow_id=flow_id1,
        action_id=2,
        action_version="1.0.0",
        action_order=4,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": {"mail": "0", "send": False}, "inform_approval": {"mail": "0", "send": False}, "request_approval": {"mail": "0", "send": False}},
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
        send_mail_setting={"inform_reject": {"mail": "0", "send": False}, "inform_approval": {"mail": "0", "send": False}, "request_approval": {"mail": "0", "send": False}},
    )
    flow_action1_4 = FlowAction(
        status="N",
        flow_id=flow_id1,
        action_id=4,
        action_version="2.0.0",
        action_order=3,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": {"mail": "0", "send": True}, "inform_approval": {"mail": "0", "send": True}, "request_approval": {"mail": "0", "send": True}},
    )

    flow_action2_1 = FlowAction(
        status="N",
        flow_id=flow_id2,
        action_id=1,
        action_version="1.0.0",
        action_order=1,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": {"mail": "0", "send": False}, "inform_approval": {"mail": "0", "send": False}, "request_approval": {"mail": "0", "send": False}},
    )
    flow_action2_2 = FlowAction(
        status="N",
        flow_id=flow_id2,
        action_id=2,
        action_version="1.0.0",
        action_order=4,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": {"mail": "0", "send": False}, "inform_approval": {"mail": "0", "send": False}, "request_approval": {"mail": "0", "send": False}},
    )
    flow_action2_3 = FlowAction(
        status="N",
        flow_id=flow_id2,
        action_id=3,
        action_version="1.0.1",
        action_order=2,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": {"mail": "0", "send": False}, "inform_approval": {"mail": "0", "send": False}, "request_approval": {"mail": "0", "send": False}},
    )
    flow_action2_4 = FlowAction(
        status="N",
        flow_id=flow_id2,
        action_id=4,
        action_version="2.0.0",
        action_order=3,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={"inform_reject": {"mail": "0", "send": True}, "inform_approval": {"mail": "0", "send": True}, "request_approval": {"mail": "0", "send": True}},
    )
    with db.session.begin_nested():
        db.session.add_all([flow_define1, flow_define2])
    db.session.commit()

    #workflow_workflow
    workflow_workflow1 = WorkFlow(
        flows_id=flow_id1,
        flows_name="利用申請",
        itemtype_id=31001,
        index_tree_id=None,
        flow_id=flow_define1.id,
        flow_define=flow_define1,
        is_deleted=False,
        open_restricted=True,
        # location_id=location.id,
        # location=location,
        is_gakuninrdm=False,
    )
    workflow_workflow2 = WorkFlow(
        flows_id=flow_id2,
        flows_name="利用申請_with_index_tree_id",
        itemtype_id=31001,
        index_tree_id=1002,     # Set index_tree_id
        flow_id=flow_define2.id,
        flow_define=flow_define2,
        is_deleted=False,
        open_restricted=True,
        # location_id=location.id,
        # location=location,
        is_gakuninrdm=False,
    )

    with db.session.begin_nested():
        db.session.add_all([flow_action1_1,flow_action1_2,flow_action1_3,flow_action1_4])
        db.session.add_all([flow_action2_1,flow_action2_2,flow_action2_3,flow_action2_4])
        db.session.add_all([workflow_workflow1, workflow_workflow2])
    db.session.commit()

    return {
		"flow_define1"          : flow_define1
		,"flow_define2"         : flow_define2
		,"flow_action1_1"       : flow_action1_1
		,"flow_action1_2"       : flow_action1_2
		,"flow_action1_3"       : flow_action1_3
		,"flow_action1_4"       : flow_action1_4
		,"flow_action2_1"       : flow_action2_1
		,"flow_action2_2"       : flow_action2_2
		,"flow_action2_3"       : flow_action2_3
		,"flow_action2_4"       : flow_action2_4
		,"workflow_workflow1"   : workflow_workflow1
		,"workflow_workflow2"   : workflow_workflow2
    }

@pytest.fixture()
def db_register_for_application_api(app, db, users, db_register_for_application_api_workflow, records_restricted):
    workflows = db_register_for_application_api_workflow
    flow_define1 = workflows["flow_define1"]
    flow_define2 = workflows["flow_define2"]
    flow_action1_1 = workflows["flow_action1_1"]
    flow_action1_2 = workflows["flow_action1_2"]
    flow_action1_3 = workflows["flow_action1_3"]
    flow_action1_4 = workflows["flow_action1_4"]
    flow_action2_1 = workflows["flow_action2_1"]
    flow_action2_2 = workflows["flow_action2_2"]
    flow_action2_3 = workflows["flow_action2_3"]
    flow_action2_4 = workflows["flow_action2_4"]
    workflow_workflow1 = workflows["workflow_workflow1"]
    workflow_workflow2 = workflows["workflow_workflow2"]
    
    # 1.利用申請(now -> item_registration)
    activity1 = Activity(activity_id='A-00000001-20001'
                        ,workflow_id=workflow_workflow1.id
                        ,flow_id=flow_define1.id
                        ,action_id=3
                        ,item_id=None
                        ,activity_login_user=users[8]["id"]
                        ,action_status = 'B'
                        ,activity_update_user=users[8]["id"]
                        ,activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f')
                        ,activity_community_id=None
                        ,activity_confirm_term_of_use=True
                        ,title=None
                        ,shared_user_ids=[]
                        ,extra_info={"file_name": "test.txt", "record_id": "1", "user_mail": users[8]["email"], "related_title": "test", "is_restricted_access": True}
                        ,action_order=2)
    activity1_pre_action = ActivityAction(
        activity_id='A-00000001-20001'
        ,action_id=1
        ,action_status = 'F'
        ,action_order=1
        ,action_handler=1
    )
    activity1_next_action = ActivityAction(
        activity_id='A-00000001-20001'
        ,action_id=4
        ,action_status = 'F'
        ,action_order=3
        ,action_handler=-1
    )
    # file_permission = FilePermission(
    #     user_id = 1
    #     ,record_id= 1
    #     ,file_name= "test.txt"
    #     ,usage_application_activity_id='A-00000001-20001'
    #     ,usage_report_activity_id=None
    #     ,status = -1
    # )

    # 2.利用申請Guest(now -> item_registration)
    activity2 = Activity(activity_id='A-00000001-20002'
                        ,workflow_id=workflow_workflow1.id
                        ,flow_id=flow_define1.id
                        ,action_id=3
                        ,item_id=None
                        ,activity_login_user=None
                        ,action_status = 'M'
                        ,activity_update_user=None
                        ,activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f')
                        ,activity_community_id=None
                        ,activity_confirm_term_of_use=True
                        ,title=None
                        ,shared_user_ids=[]
                        ,extra_info={"file_name": "test.txt", "record_id": "1", "guest_mail": "guest@example.org", "related_title": "test", "is_restricted_access": True}
                        ,action_order=2)
    activity2_pre_action = ActivityAction(
        activity_id='A-00000001-20002'
        ,action_id=1
        ,action_status = 'F'
        ,action_order=1
        ,action_handler=1
    )
    activity2_next_action = ActivityAction(
        activity_id='A-00000001-20002'
        ,action_id=4
        ,action_status = 'F'
        ,action_order=3
        ,action_handler=-1
    )
    guest_activity2 = GuestActivity(
        activity_id='A-00000001-20002'
        ,record_id=1
        ,user_mail = 'guest@example.org'
        ,file_name = "test.txt"
        ,token="abc123"
        ,expiration_date=10
        ,is_usage_report=False
    )
    
    # 3.利用申請(end)
    activity3 = Activity(activity_id='A-00000001-20003'
                        ,workflow_id=workflow_workflow1.id
                        ,flow_id=flow_define1.id
                        ,action_id=2
                        ,item_id=None
                        ,activity_login_user=1
                        ,action_status = 'F'
                        ,activity_update_user=1
                        ,activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f')
                        ,activity_community_id=None
                        ,activity_confirm_term_of_use=True
                        ,title=None
                        ,shared_user_ids=[1]
                        ,extra_info={"file_name": "test.txt", "record_id": "1", "user_mail": users[8]["email"], "related_title": "test", "is_restricted_access": True}
                        ,action_order=4)
    activity3_action1 = ActivityAction(
        activity_id='A-00000001-20003'
        ,action_id=1
        ,action_status = 'F'
        ,action_order=1
        ,action_handler=1
    )
    activity3_action2 = ActivityAction(
        activity_id='A-00000001-20003'
        ,action_id=3
        ,action_status = 'F'
        ,action_order=2
        ,action_handler=1
    )
    activity3_action3 = ActivityAction(
        activity_id='A-00000001-20003'
        ,action_id=4
        ,action_status = 'F'
        ,action_order=3
        ,action_handler=-1
    )
    activity3_action4 = ActivityAction(
        activity_id='A-00000001-20003'
        ,action_id=2
        ,action_status = 'F'
        ,action_order=4
        ,action_handler=-1
    )

    # 4.利用申請Guest(now -> approval)
    activity4 = Activity(activity_id='A-00000001-20004'
                        ,workflow_id=workflow_workflow1.id
                        ,flow_id=flow_define1.id
                        ,action_id=4
                        ,item_id=None
                        ,activity_login_user=None
                        ,action_status = 'M'
                        ,activity_update_user=None
                        ,activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f')
                        ,activity_community_id=None
                        ,activity_confirm_term_of_use=True
                        ,title=None
                        ,shared_user_ids=[]
                        ,extra_info={"file_name": "test.txt", "record_id": "1", "guest_mail": "guest@example.org", "related_title": "test", "is_restricted_access": True}
                        ,action_order=3)
    activity4_action1 = ActivityAction(
        activity_id='A-00000001-20004'
        ,action_id=1
        ,action_status = 'F'
        ,action_order=1
        ,action_handler=1
    )
    activity4_action2 = ActivityAction(
        activity_id='A-00000001-20004'
        ,action_id=3
        ,action_status = 'F'
        ,action_order=2
        ,action_handler=1
    )
    activity4_action3 = ActivityAction(
        activity_id='A-00000001-20004'
        ,action_id=4
        ,action_status = 'F'
        ,action_order=3
        ,action_handler=-1
    )
    activity4_action4 = ActivityAction(
        activity_id='A-00000001-20004'
        ,action_id=2
        ,action_status = 'F'
        ,action_order=4
        ,action_handler=1
    )
    guest_activity4 = GuestActivity(
        activity_id='A-00000001-20004'
        ,record_id=1
        ,user_mail = 'guest@example.org'
        ,file_name = "test.txt"
        ,token="abc123"
        ,expiration_date=10
        ,is_usage_report=False
    )

    # 5.利用申請Guest(now -> item_registration) with set index workflow
    activity5 = Activity(activity_id='A-00000001-20005'
                        ,workflow_id=workflow_workflow2.id
                        ,flow_id=flow_define2.id
                        ,action_id=3
                        ,item_id=None
                        ,activity_login_user=None
                        ,action_status = 'M'
                        ,activity_update_user=None
                        ,activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f')
                        ,activity_community_id=None
                        ,activity_confirm_term_of_use=True
                        ,title=None
                        ,shared_user_ids=[]
                        ,extra_info={"file_name": "test.txt", "record_id": "1", "guest_mail": "guest@example.org", "related_title": "test", "is_restricted_access": True}
                        ,action_order=2)
    activity5_pre_action = ActivityAction(
        activity_id='A-00000001-20005'
        ,action_id=1
        ,action_status = 'F'
        ,action_order=1
        ,action_handler=1
    )
    activity5_next_action = ActivityAction(
        activity_id='A-00000001-20005'
        ,action_id=4
        ,action_status = 'F'
        ,action_order=3
        ,action_handler=-1
    )
    guest_activity5 = GuestActivity(
        activity_id='A-00000001-20005'
        ,record_id=1
        ,user_mail = 'guest@example.org'
        ,file_name = "test.txt"
        ,token="abc123"
        ,expiration_date=10
        ,is_usage_report=False
    )
    
    # 6.利用申請 edit item (now -> item_registration)
    activity6 = Activity(activity_id='A-00000001-20006'
                        ,workflow_id=workflow_workflow1.id
                        ,flow_id=flow_define1.id
                        ,action_id=3
                        ,item_id=records_restricted[0]["rec_uuid"]
                        ,activity_login_user=users[8]["id"]
                        ,action_status = 'B'
                        ,activity_update_user=users[8]["id"]
                        ,activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f')
                        ,activity_community_id=None
                        ,activity_confirm_term_of_use=True
                        ,title=None
                        ,shared_user_ids=[]
                        ,extra_info={"file_name": "test.txt", "record_id": "1", "user_mail": users[8]["email"], "related_title": "test", "is_restricted_access": True}
                        ,action_order=2)
    activity6_pre_action = ActivityAction(
        activity_id='A-00000001-20006'
        ,action_id=1
        ,action_status = 'F'
        ,action_order=1
        ,action_handler=1
    )
    activity6_next_action = ActivityAction(
        activity_id='A-00000001-20006'
        ,action_id=4
        ,action_status = 'F'
        ,action_order=3
        ,action_handler=-1
    )

    with db.session.begin_nested():
        db.session.add(activity1)
        db.session.add(activity2)
        db.session.add(activity3)
        db.session.add(activity4)
        db.session.add(activity5)
        db.session.add(activity6)
    db.session.commit()
    with db.session.begin_nested():
        db.session.add(activity1_pre_action)
        db.session.add(activity1_next_action)
        db.session.add(activity2_pre_action)
        db.session.add(activity2_next_action)
        db.session.add(activity3_action1)
        db.session.add(activity3_action2)
        db.session.add(activity3_action3)
        db.session.add(activity3_action4)
        db.session.add(activity4_action1)
        db.session.add(activity4_action2)
        db.session.add(activity4_action3)
        db.session.add(activity4_action4)
        db.session.add(activity5_pre_action)
        db.session.add(activity5_next_action)
        db.session.add(activity6_pre_action)
        db.session.add(activity6_next_action)
        # db.session.add(file_permission)
        db.session.add(guest_activity2)
        db.session.add(guest_activity4)
        db.session.add(guest_activity5)
    db.session.commit()

    # Register data in workflow_action_history table
    activity1_histories = []
    activity1_histories.append(
        ActivityHistory(
            activity_id=activity1.activity_id,
            action_id=flow_action1_1.action_id,
            action_version=flow_action1_1.action_version,
            action_status='F',
            action_user=users[8]["id"],
            action_date=datetime.strptime('2023/07/10 10:00:01.000', '%Y/%m/%d %H:%M:%S.%f'),
            action_comment="Begin Action",
            action_order=flow_action1_1.action_order,
        )
    )

    activity2_histories = []
    activity2_histories.append(
        ActivityHistory(
            activity_id=activity2.activity_id,
            action_id=flow_action1_1.action_id,
            action_version=flow_action1_1.action_version,
            action_status='F',
            action_user=None,
            action_date=datetime.strptime('2023/07/10 10:00:01.000', '%Y/%m/%d %H:%M:%S.%f'),
            action_comment="Begin Action",
            action_order=flow_action1_1.action_order,
        )
    )

    activity3_histories = []
    activity3_histories.append(
        ActivityHistory(
            activity_id=activity3.activity_id,
            action_id=flow_action1_1.action_id,
            action_version=flow_action1_1.action_version,
            action_status='F',
            action_user=users[8]["id"],
            action_date=datetime.strptime('2023/07/10 10:00:01.000', '%Y/%m/%d %H:%M:%S.%f'),
            action_comment="Begin Action",
            action_order=flow_action1_1.action_order,
        )
    )
    activity3_histories.append(
        ActivityHistory(
            activity_id=activity3.activity_id,
            action_id=flow_action1_3.action_id,
            action_version=flow_action1_3.action_version,
            action_status='F',
            action_user=users[8]["id"],
            action_date=datetime.strptime('2023/07/10 10:00:01.000', '%Y/%m/%d %H:%M:%S.%f'),
            action_comment="",
            action_order=flow_action1_3.action_order,
        )
    )
    activity3_histories.append(
        ActivityHistory(
            activity_id=activity3.activity_id,
            action_id=flow_action1_4.action_id,
            action_version=flow_action1_4.action_version,
            action_status='F',
            action_user=1,
            action_date=datetime.strptime('2023/07/10 10:00:01.000', '%Y/%m/%d %H:%M:%S.%f'),
            action_comment="",
            action_order=flow_action1_4.action_order,
        )
    )
    activity3_histories.append(
        ActivityHistory(
            activity_id=activity3.activity_id,
            action_id=flow_action1_2.action_id,
            action_version=flow_action1_2.action_version,
            action_status='F',
            action_user=1,
            action_date=datetime.strptime('2023/07/10 10:00:01.000', '%Y/%m/%d %H:%M:%S.%f'),
            action_comment="End Action",
            action_order=flow_action1_2.action_order,
        )
    )

    activity4_histories = []
    activity4_histories.append(
        ActivityHistory(
            activity_id=activity4.activity_id,
            action_id=flow_action1_1.action_id,
            action_version=flow_action1_1.action_version,
            action_status='F',
            action_user=None,
            action_date=datetime.strptime('2023/07/10 10:00:01.000', '%Y/%m/%d %H:%M:%S.%f'),
            action_comment="Begin Action",
            action_order=flow_action1_1.action_order,
        )
    )
    activity4_histories.append(
        ActivityHistory(
            activity_id=activity4.activity_id,
            action_id=flow_action1_3.action_id,
            action_version=flow_action1_3.action_version,
            action_status='F',
            action_user=None,
            action_date=datetime.strptime('2023/07/10 10:00:01.000', '%Y/%m/%d %H:%M:%S.%f'),
            action_comment="",
            action_order=flow_action1_3.action_order,
        )
    )

    activity5_histories = []
    activity5_histories.append(
        ActivityHistory(
            activity_id=activity5.activity_id,
            action_id=flow_action2_1.action_id,
            action_version=flow_action2_1.action_version,
            action_status='F',
            action_user=None,
            action_date=datetime.strptime('2023/07/10 10:00:01.000', '%Y/%m/%d %H:%M:%S.%f'),
            action_comment="Begin Action",
            action_order=flow_action2_1.action_order,
        )
    )

    activity6_histories = []
    activity6_histories.append(
        ActivityHistory(
            activity_id=activity6.activity_id,
            action_id=flow_action1_1.action_id,
            action_version=flow_action1_1.action_version,
            action_status='F',
            action_user=users[8]["id"],
            action_date=datetime.strptime('2023/07/10 10:00:01.000', '%Y/%m/%d %H:%M:%S.%f'),
            action_comment="Begin Action",
            action_order=flow_action1_1.action_order,
        )
    )

    with db.session.begin_nested():
        db.session.add_all(activity1_histories)
        db.session.add_all(activity2_histories)
        db.session.add_all(activity3_histories)
        db.session.add_all(activity4_histories)
        db.session.add_all(activity5_histories)
        db.session.add_all(activity6_histories)
    db.session.commit()

    permissions = list()
    for i in range(len(users)):
        permissions.append(FilePermission(users[i]["id"],"1.1","test_file","2",None,-1))
    with db.session.begin_nested():
        db.session.add_all(permissions)
    db.session.commit()

    workflows.update({
        "activity1"     : activity1
        ,"activity2"    : activity2
        ,"activity3"    : activity3
        ,"activity4"    : activity4
        ,"activity5"    : activity5
        ,"activity6"    : activity6
    })
    return workflows

    

@pytest.fixture()
def application_api_request_body(app, item_type):
    bodies = []
    results = []

    # 0: Success
    body = {
        "item_1616221831877": {
            "subitem_restricted_access_dataset_usage": "restricted item"
        },
        "item_1616221851421": {
            "subitem_mail_address": "contributor@example.org",
            "subitem_fullname": "情報 太郎"
        },
        "item_1616221894659": [
            {
                "subitem_restricted_access_institution_name": "test institution"
            }
        ],
        "item_1616222047122": {
            "subitem_restricted_access_wf_issued_date": "2023-08-25"
        },
        "pubdate": "2023-08-25"
    }

    bodies.append(body)

    # 1: Invalid enum
    body = {
        "item_1616221831877": {
            "subitem_restricted_access_dataset_usage": "restricted item"
        },
        "item_1616221960771": {
            "subitem_restricted_access_research_plan_type": "aaa"
        },
        "item_1616221851421": {
            "subitem_fullname": "情報 太郎"
        }
    }
    bodies.append(body)

    # 2: missing required
    body = {
        "item_1616221831877": {
            "subitem_restricted_access_dataset_usage": "restricted item"
        }
    }
    bodies.append(body)

    return bodies

@pytest.fixture()
def indextree(client, users):
    indicies = []
    index_metadata1 = {
        "id": 1001,
        "parent": 0,
        "value": "test index1",
    }

    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        assert Indexes.create(index_metadata1["parent"], index_metadata1)
        index = Index.get_index_by_id(index_metadata1["id"])
        index.public_state = True
        index.harvest_public_state = True
    indicies.append(index_metadata1)

    index_metadata2 = {
        "id": 1002,
        "parent": 0,
        "value": "test index2",
    }

    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        assert Indexes.create(index_metadata2["parent"], index_metadata2)
        index = Index.get_index_by_id(index_metadata2["id"])
        index.public_state = True
        index.harvest_public_state = True
    indicies.append(index_metadata2)

    return indicies

@pytest.fixture()
def records_restricted(app, db, db_register_for_application_api_workflow, users, location, item_type, indextree):
    indexer = WekoIndexer()
    indexer.get_es_index()
    results = []

    wf1 :WorkFlow = db_register_for_application_api_workflow.get("workflow_workflow1")
    # wf2 :WorkFlow = db_register_for_application_api.get("workflow_workflow2")

    id = 101
    index_id = indextree[0]["id"] # 1001
    results.append(make_record_restricted(db, indexer, id, index_id, wf1.itemtype_id, str(users[8]["id"]))) # student

    return results

def make_record_restricted(db, indexer, id, index_id, item_type_id, userId):
    """ make open_resirected record"""
    record_data = {
        "_oai": {"id": "oai:weko3.example.org:000000{:02d}".format(id), "sets": [f"{index_id}"]},
        "path": [f"{index_id}"],
        "owner": f"{userId}",
        "recid": "{}".format(id),
        "title": [
            "edit_item"
        ],
        "pubdate": {"attribute_name": "PubDate", "attribute_value": "2021-08-06"},
        "_buckets": {"deposit": "27202db8-aefc-4b85-b5ae-4921ac151ddf"},
        "_deposit": {
            "id": "{}".format(id),
            "pid": {"type": "depid", "value": "{}".format(id), "revision_id": 0},
            "owners": [userId],
            "status": "private",
        },
        "item_title": "edit_item",
        "author_link": [],
        "item_type_id": f"{item_type_id}",
        "publish_date": "2021-08-06",
        "publish_status": "1",
        "weko_shared_ids": [],
        "item_1616221831877": {
            "subitem_restricted_access_dataset_usage": "edit_item"
        },
        "item_1616221851421": {
            "subitem_fullname": "情報 花子",
            "subitem_mail_address": "contributor@example.org"
        },
        "item_1616221960771": {
            "subitem_restricted_access_research_plan_type": "Abstract"
        },
        "item_1616222047122": {
            "subitem_restricted_access_wf_issued_date": "2023-09-03",
            "subitem_restricted_access_wf_issued_date_type": "Created"
        },
        "item_1616222067301": {
            "subitem_restricted_access_application_date": "2023-09-03",
            "subitem_restricted_access_application_date_type": "Issued"
        },
        "item_1616222093486": {
            "subitem_restricted_access_approval_date_type": "Accepted"
        },
        "item_1616222117209": {
            "subitem_restricted_access_item_title": "利用申請20230903edit_item_情報 花子"
        },
        "pubdate": "2023-08-25",
        "relation_version_is_last": True,
    }

    item_data = {
        "id": f"{id}",
        "pid": {"type": "recid", "value": f"{id}", "revision_id": 0},
        "path": [f"{index_id}"],
        "owner": f"{userId}",
        "title": "edit_item",
        "owners": [userId],
        "status": "draft",
        "$schema": "https://localhost:8443/items/jsonschema/1",
        "pubdate": "2021-08-06",
        "feedback_mail_list": [],
        "item_1616221831877": {
            "subitem_restricted_access_dataset_usage": "edit_item"
        },
        "item_1616221851421": {
            "subitem_fullname": "情報 花子",
            "subitem_mail_address": "contributor@example.org"
        },
        "item_1616221960771": {
            "subitem_restricted_access_research_plan_type": "Abstract"
        },
        "item_1616222047122": {
            "subitem_restricted_access_wf_issued_date": "2023-09-03",
            "subitem_restricted_access_wf_issued_date_type": "Created"
        },
        "item_1616222067301": {
            "subitem_restricted_access_application_date": "2023-09-03",
            "subitem_restricted_access_application_date_type": "Issued"
        },
        "item_1616222093486": {
            "subitem_restricted_access_approval_date_type": "Accepted"
        },
        "item_1616222117209": {
            "subitem_restricted_access_item_title": "利用申請20230903edit_item_情報 花子"
        },
        "pubdate": "2023-08-25",
    }

    rec_uuid = uuid.uuid4()

    recid = PersistentIdentifier.create(
        "recid",
        str(id),
        object_type="rec",
        object_uuid=rec_uuid,
        status=PIDStatus.REGISTERED,
    )
    depid = PersistentIdentifier.create(
        "depid",
        str(id),
        object_type="rec",
        object_uuid=rec_uuid,
        status=PIDStatus.REGISTERED,
    )
    parent = PersistentIdentifier.create(
        "parent",
        "parent:{}".format(id),
        object_type="rec",
        object_uuid=rec_uuid,
        status=PIDStatus.REGISTERED,
    )
    rec_uuid2 = uuid.uuid4()
    recid_v1 = PersistentIdentifier.create(
        "recid",
        str(id + 0.1),
        object_type="rec",
        object_uuid=rec_uuid2,
        status=PIDStatus.REGISTERED,
    )
    depid_v1 = PersistentIdentifier.create(
        "depid",
        str(id + 0.1),
        object_type="rec",
        object_uuid=rec_uuid2,
        status=PIDStatus.REGISTERED,
    )

    h1 = PIDVersioning(parent=parent)
    h1.insert_child(child=recid)
    h1.insert_child(child=recid_v1)
    RecordDraft.link(recid, depid)
    RecordDraft.link(recid_v1, depid_v1)

    record = WekoRecord.create(record_data, id_=rec_uuid)
    # from six import BytesIO
    import base64

    bucket = Bucket.create()
    record_buckets = RecordsBuckets.create(record=record.model, bucket=bucket)

    deposit = WekoDepositAPI(record, record.model)
    deposit.commit()

    indexer.upload_metadata(record_data, rec_uuid, 1, False)
    item = ItemsMetadata.create(item_data, id_=rec_uuid, item_type_id=item_type_id)

    record_v1 = WekoRecord.create(record_data, id_=rec_uuid2)
    # from six import BytesIO
    import base64

    bucket_v1 = Bucket.create()
    record_buckets = RecordsBuckets.create(record=record_v1.model, bucket=bucket_v1)
    deposit_v1 = WekoDepositAPI(record_v1, record_v1.model)
    deposit_v1.commit()

    record_data_v1 = copy.deepcopy(record_data)
    indexer.upload_metadata(record_data_v1, rec_uuid2, 1, False)
    item_v1 = ItemsMetadata.create(item_data, id_=rec_uuid2, item_type_id=item_type_id)

    db.session.flush()
    # db.session.expunge_all()

    return {
        "depid": depid,
        "recid": recid,
        "parent": parent,
        "record": record,
        "record_data": record_data,
        "item": item,
        "item_data": item_data,
        "deposit": deposit,
        "rec_uuid": rec_uuid,
        "rec_uuid2": rec_uuid2,
    }

@pytest.fixture()
def db_guestactivity_2(app, db, db_register):
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
def mail_templates(db):
    """Create mail templates."""
    genres = []
    genre1 = MailTemplateGenres(
        id=1,
        name="Notification of secret URL provision"
    )
    genres.append(genre1)
    genre2 = MailTemplateGenres(
        id=2,
        name="Guidance to the application form"
    )
    genres.append(genre2)
    genre3 = MailTemplateGenres(
        id=3,
        name="Others"
    )
    genres.append(genre3)
    db.session.add_all(genres)
    db.session.commit()
    template = MailTemplates(
        id=1,
        mail_subject="test subject",
        mail_body="test body",
        default_mail=True,
        mail_genre_id=genre1.id,
    )
    db.session.add(template)
    db.session.commit()
    return template


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

@pytest.fixture
def db_mail_templates(db):
    genre1 = MailTemplateGenres(id=1, name='Test Genre1')
    genre2 = MailTemplateGenres(id=2, name='Test Genre2')
    genre3 = MailTemplateGenres(id=3, name='Test Genre3')
    db.session.add(genre1)
    db.session.add(genre2)
    db.session.add(genre3)

    mail_template = MailTemplates(
        id = 1,
        mail_subject = 'Test Subject',
        mail_body = 'Test Body',
        default_mail = True,
        mail_genre_id = 1
    )
    db.session.add(mail_template)
    return mail_template

@pytest.fixture
def db_mail_template_users(db, db_mail_templates):
    user1 = User(id=1, email='user1@example.com', active=True)
    user2 = User(id=2, email='user2@example.com', active=True)

    mail_template = db_mail_templates

    mail_template_user1_recipient = MailTemplateUsers(
        template=mail_template,
        user=user1,
        mail_type=MailType.RECIPIENT
    )
    mail_template_user1_cc = MailTemplateUsers(
        template=mail_template,
        user=user1,
        mail_type=MailType.CC
    )
    mail_template_user1_bcc = MailTemplateUsers(
        template=mail_template,
        user=user1,
        mail_type=MailType.BCC
    )
    mail_template_user2_recipient = MailTemplateUsers(
        template=mail_template,
        user=user2,
        mail_type=MailType.RECIPIENT
    )
    mail_template_user2_cc = MailTemplateUsers(
        template=mail_template,
        user=user2,
        mail_type=MailType.CC
    )
    mail_template_user2_bcc = MailTemplateUsers(
        template=mail_template,
        user=user2,
        mail_type=MailType.BCC
    )
    db.session.add(mail_template_user1_recipient)
    db.session.add(mail_template_user1_cc)
    db.session.add(mail_template_user1_bcc)
    db.session.add(mail_template_user2_recipient)
    db.session.add(mail_template_user2_cc)
    db.session.add(mail_template_user2_bcc)
    db.session.commit()

    users = [user1, user2]
    mail_template_users = [
        mail_template_user1_recipient,
        mail_template_user1_cc,
        mail_template_user1_bcc,
        mail_template_user2_recipient,
        mail_template_user2_cc,
        mail_template_user2_bcc
    ]

    return mail_template, users, mail_template_users
