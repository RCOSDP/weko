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
import shutil
import tempfile
import uuid
import xml.etree.ElementTree as ET
import xmltodict
from datetime import date, datetime, timedelta
from os.path import join
from time import sleep
import pytest
import requests
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import RequestError
from flask import Flask, url_for
from flask.cli import ScriptInfo
from flask_babelex import Babel
from flask_babelex import lazy_gettext as _
from flask_celeryext import FlaskCeleryExt
from flask_login import LoginManager, current_user, login_user
from flask_menu import Menu
from mock import Mock, patch, MagicMock
from pytest_mock import mocker
from simplekv.memory.redisstore import RedisStore
from six import BytesIO
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy_utils.functions import create_database, database_exists, drop_database
from werkzeug.local import LocalProxy
from invenio_records.api import Record
from invenio_stats.processors import EventsIndexer
from tests.helpers import create_record, json_data

from invenio_access import InvenioAccess
from invenio_access.models import ActionRoles, ActionUsers
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import Role, User
from invenio_accounts.testutils import create_test_user, login_user_via_session
from invenio_admin import InvenioAdmin
from invenio_assets import InvenioAssets
from invenio_cache import InvenioCache
from invenio_communities import InvenioCommunities
from invenio_communities.models import Community
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_db.utils import drop_alembic_version_table
from invenio_deposit import InvenioDeposit
from invenio_deposit.api import Deposit
from invenio_deposit.config import (
    DEPOSIT_DEFAULT_JSONSCHEMA,
    DEPOSIT_DEFAULT_STORAGE_CLASS,
    DEPOSIT_JSONSCHEMAS_PREFIX,
    DEPOSIT_RECORDS_UI_ENDPOINTS,
    DEPOSIT_REST_ENDPOINTS,
)
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.models import Bucket, FileInstance, Location, ObjectVersion
from invenio_files_rest.permissions import (
    bucket_listmultiparts_all,
    bucket_read_all,
    bucket_read_versions_all,
    bucket_update_all,
    location_update_all,
    multipart_delete_all,
    multipart_read_all,
    object_delete_all,
    object_delete_version_all,
    object_read_all,
    object_read_version_all,
)
from invenio_files_rest.views import blueprint as invenio_files_rest_blueprint
from invenio_i18n import InvenioI18N
from invenio_indexer import InvenioIndexer
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_mail import InvenioMail
from invenio_oaiharvester.models import HarvestSettings
from invenio_oaiserver import InvenioOAIServer
from invenio_oaiserver.models import Identify, OAISet
from invenio_pidrelations import InvenioPIDRelations
from invenio_pidrelations.contrib.records import RecordDraft
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidrelations.models import PIDRelation
from invenio_pidstore import InvenioPIDStore, current_pidstore
from invenio_pidstore.models import PersistentIdentifier, PIDStatus, RecordIdentifier
from invenio_pidstore.providers.recordid import RecordIdProvider
from invenio_queues.proxies import current_queues
from invenio_records import InvenioRecords
from invenio_records.models import RecordMetadata
from invenio_records_files.models import RecordsBuckets
from invenio_records_rest import InvenioRecordsREST, config
from invenio_records_rest.config import RECORDS_REST_SORT_OPTIONS
from invenio_records_rest.facets import terms_filter
from invenio_records_rest.utils import PIDConverter
from invenio_records_rest.views import create_blueprint_from_app
from invenio_rest import InvenioREST
from invenio_search import InvenioSearch, RecordsSearch, current_search, current_search_client
from invenio_stats import InvenioStats
from invenio_stats.config import SEARCH_INDEX_PREFIX as index_prefix
from invenio_indexer.signals import before_record_index
from invenio_indexer.api import RecordIndexer
from invenio_stats.contrib.event_builders import (
    build_file_unique_id,
    build_record_unique_id,
    file_download_event_builder,
)

from weko_admin import WekoAdmin
from weko_admin.config import WEKO_ADMIN_DEFAULT_ITEM_EXPORT_SETTINGS, WEKO_ADMIN_MANAGEMENT_OPTIONS
from weko_admin.models import FacetSearchSetting, Identifier, SessionLifetime
from weko_deposit.api import WekoDeposit
from weko_deposit.api import WekoDeposit as aWekoDeposit
from weko_deposit.api import WekoIndexer, WekoRecord
from weko_deposit.config import WEKO_BUCKET_QUOTA_SIZE, WEKO_MAX_FILE_SIZE
from weko_groups import WekoGroups
from weko_index_tree import WekoIndexTree, WekoIndexTreeREST
from weko_index_tree.api import Indexes
from weko_index_tree.config import WEKO_INDEX_TREE_REST_ENDPOINTS as _WEKO_INDEX_TREE_REST_ENDPOINTS
from weko_index_tree.models import Index, IndexStyle
from weko_items_ui.config import WEKO_ITEMS_UI_FILE_SISE_PREVIEW_LIMIT, WEKO_ITEMS_UI_MS_MIME_TYPE
from weko_records import WekoRecords
from weko_records.api import ItemsMetadata, ItemTypes, Mapping, ItemTypeNames
from weko_records.config import WEKO_ITEMTYPE_EXCLUDED_KEYS
from weko_records.models import ItemType, ItemTypeMapping, ItemTypeName, ItemMetadata
from weko_records.serializers.utils import get_full_mapping
from weko_records_ui.config import (
    EMAIL_DISPLAY_FLG,
    WEKO_PERMISSION_ROLE_COMMUNITY,
    WEKO_PERMISSION_SUPER_ROLE_USER,
    WEKO_RECORDS_UI_BULK_UPDATE_FIELDS,
)
from weko_records_ui.models import PDFCoverPageSettings, RocrateMapping
from weko_redis.redis import RedisConnection
from weko_schema_ui.models import OAIServerSchema
from weko_theme import WekoTheme
from weko_theme.config import THEME_BODY_TEMPLATE, WEKO_THEME_ADMIN_ITEM_MANAGEMENT_INIT_TEMPLATE
from weko_workflow import WekoWorkflow
from weko_workflow.models import Action, ActionStatus, ActionStatusPolicy, Activity, FlowAction, FlowDefine, WorkFlow
from weko_search_ui import WekoSearchREST, WekoSearchUI
from weko_search_ui.config import SEARCH_UI_SEARCH_INDEX, WEKO_SEARCH_TYPE_DICT, WEKO_SEARCH_UI_BASE_TEMPLATE, WEKO_SEARCH_KEYWORDS_DICT, CHILD_INDEX_THUMBNAIL_WIDTH, CHILD_INDEX_THUMBNAIL_HEIGHT, ROCRATE_METADATA_FILE, SWORD_METADATA_FILE
from weko_search_ui.rest import create_blueprint
from weko_search_ui.views import blueprint_api


from invenio_oaiharvester.models import OAIHarvestConfig, HarvestSettings




# from moto import mock_s3





FIXTURE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")


class TestSearch(RecordsSearch):
    """Test record search."""

    class Meta:
        """Test configuration."""

        index = "invenio-records-rest"
        doc_types = None

    def __init__(self, **kwargs):
        """Add extra options."""
        super(TestSearch, self).__init__(**kwargs)
        self._extra.update(**{"_source": {"excludes": ["_access"]}})


# class MockEs():
#     def __init__(self,**keywargs):
#         self.indices = self.MockIndices()
#         self.es = Elasticsearch()
#         self.cluster = self.MockCluster()
#     def index(self, id="",version="",version_type="",index="",doc_type="",body="",**arguments):
#         pass
#     def delete(self,id="",index="",doc_type="",**kwargs):
#         return Response(response=json.dumps({}),status=500)
#     @property
#     def transport(self):
#         return self.es.transport
#     class MockIndices():
#         def __init__(self,**keywargs):
#             self.mapping = dict()
#         def delete(self,index="", ignore=""):
#             pass
#         def delete_template(self,index=""):
#             pass
#         def create(self,index="",body={},ignore=""):
#             self.mapping[index] = body
#         def put_alias(self,index="", name="", ignore=""):
#             pass
#         def put_template(self,name="", body={}, ignore=""):
#             pass
#         def refresh(self,index=""):
#             pass
#         def exists(self, index="", **kwargs):
#             if index in self.mapping:
#                 return True
#             else:
#                 return False
#         def flush(self,index="",wait_if_ongoing=""):
#             pass
#         def delete_alias(self, index="", name="",ignore=""):
#             pass

#         # def search(self,index="",doc_type="",body={},**kwargs):
#         #     pass
#     class MockCluster():
#         def __init__(self,**kwargs):
#             pass
#         def health(self, wait_for_status="", request_timeout=0):
#             pass


@pytest.yield_fixture(scope="session")
def search_class():
    """Search class."""
    yield TestSearch


@pytest.yield_fixture()
def instance_path():
    """Temporary instance path."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.fixture()
def base_app(instance_path, search_class, request):
    """Flask application fixture."""
    app_ = Flask(
        "testapp",
        instance_path=instance_path,
        static_folder=join(instance_path, "static"),
    )
    os.environ["INVENIO_WEB_HOST_NAME"] = "127.0.0.1"
    app_.config.update(
        ACCOUNTS_JWT_ENABLE=True,
        SECRET_KEY="SECRET_KEY",
        WEKO_INDEX_TREE_UPDATED=True,
        DEPOSIT_FILES_API="/api/files",
        TESTING=True,
        FILES_REST_DEFAULT_QUOTA_SIZE=None,
        FILES_REST_DEFAULT_STORAGE_CLASS="S",
        FILES_REST_STORAGE_CLASS_LIST={
            "S": "Standard",
            "A": "Archive",
        },
        CACHE_REDIS_URL=os.environ.get("CACHE_REDIS_URL", "redis://redis:6379/0"),
        CACHE_REDIS_DB="0",
        CACHE_REDIS_HOST="redis",
        WEKO_INDEX_TREE_STATE_PREFIX="index_tree_expand_state",
        REDIS_PORT="6379",
        DEPOSIT_DEFAULT_JSONSCHEMA=DEPOSIT_DEFAULT_JSONSCHEMA,
        SERVER_NAME="TEST_SERVER",
        LOGIN_DISABLED=False,
        INDEXER_DEFAULT_DOCTYPE="item-v1.0.0",
        WEKO_SCHEMA_JPCOAR_V1_SCHEMA_NAME = 'jpcoar_v1_mapping',
        WEKO_SCHEMA_JPCOAR_V2_SCHEMA_NAME = 'jpcoar_mapping',
        WEKO_SCHEMA_JPCOAR_V2_RESOURCE_TYPE_REPLACE={
            'periodical':'journal',
            'interview':'other',
            'internal report':'other',
            'report part':'other',
        },
        WEKO_SCHEMA_DDI_SCHEMA_NAME = "ddi_mapping",
        INDEXER_FILE_DOC_TYPE="content",
        INDEXER_DEFAULT_INDEX="{}-weko-item-v1.0.0".format("test"),
        INDEX_IMG="indextree/36466818-image.jpg",
        # SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
        #                                   'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     "SQLALCHEMY_DATABASE_URI", "sqlite:///test.db"
        # ),
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI','postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        SEARCH_ELASTIC_HOSTS=os.environ.get("SEARCH_ELASTIC_HOSTS", "elasticsearch"),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        JSONSCHEMAS_HOST="inveniosoftware.org",
        ACCOUNTS_USERINFO_HEADERS=True,
        I18N_LANGUAGES=[("ja", "Japanese"), ("en", "English")],
        WEKO_INDEX_TREE_INDEX_LOCK_KEY_PREFIX="lock_index_",
        WEKO_PERMISSION_SUPER_ROLE_USER=WEKO_PERMISSION_SUPER_ROLE_USER,
        WEKO_PERMISSION_ROLE_COMMUNITY=WEKO_PERMISSION_ROLE_COMMUNITY,
        EMAIL_DISPLAY_FLG=EMAIL_DISPLAY_FLG,
        THEME_SITEURL="https://localhost",
        DEPOSIT_RECORDS_UI_ENDPOINTS=DEPOSIT_RECORDS_UI_ENDPOINTS,
        DEPOSIT_REST_ENDPOINTS=DEPOSIT_REST_ENDPOINTS,
        DEPOSIT_DEFAULT_STORAGE_CLASS=DEPOSIT_DEFAULT_STORAGE_CLASS,
        # RECORDS_REST_SORT_OPTIONS=RECORDS_REST_SORT_OPTIONS,
        RECORDS_REST_DEFAULT_LOADERS={
            "application/json": lambda: request.get_json(),
            "application/json-patch+json": lambda: request.get_json(force=True),
        },
        FILES_REST_OBJECT_KEY_MAX_LEN=255,
        # SEARCH_UI_SEARCH_INDEX=SEARCH_UI_SEARCH_INDEX,
        SEARCH_UI_SEARCH_INDEX="test-weko",
        CHILD_INDEX_THUMBNAIL_WIDTH = CHILD_INDEX_THUMBNAIL_WIDTH,
        CHILD_INDEX_THUMBNAIL_HEIGHT = CHILD_INDEX_THUMBNAIL_HEIGHT,
        # SEARCH_ELASTIC_HOSTS=os.environ.get("INVENIO_ELASTICSEARCH_HOST"),
        SEARCH_INDEX_PREFIX="{}-".format("test"),
        SEARCH_CLIENT_CONFIG=dict(timeout=120, max_retries=10),
        OAISERVER_ID_PREFIX="oai:inveniosoftware.org:recid/",
        OAISERVER_RECORD_INDEX="_all",
        OAISERVER_REGISTER_SET_SIGNALS=True,
        WEKO_ITEMS_UI_FILE_SISE_PREVIEW_LIMIT=WEKO_ITEMS_UI_FILE_SISE_PREVIEW_LIMIT,
        WEKO_ITEMS_UI_MS_MIME_TYPE=WEKO_ITEMS_UI_MS_MIME_TYPE,
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
        THEME_SITENAME="WEKO3",
        IDENTIFIER_GRANT_SUFFIX_METHOD=0,
        THEME_FRONTPAGE_TEMPLATE="weko_theme/frontpage.html",
        BASE_EDIT_TEMPLATE="weko_theme/edit.html",
        BASE_PAGE_TEMPLATE="weko_theme/page.html",
        RECORDS_REST_ENDPOINTS=copy.deepcopy(config.RECORDS_REST_ENDPOINTS),
        RECORDS_REST_DEFAULT_CREATE_PERMISSION_FACTORY=None,
        RECORDS_REST_DEFAULT_DELETE_PERMISSION_FACTORY=None,
        RECORDS_REST_DEFAULT_READ_PERMISSION_FACTORY=None,
        RECORDS_REST_DEFAULT_UPDATE_PERMISSION_FACTORY=None,
        RECORDS_REST_DEFAULT_RESULTS_SIZE=10,
        RECORDS_REST_DEFAULT_SEARCH_INDEX=search_class.Meta.index,
        RECORDS_REST_FACETS={
            search_class.Meta.index: {
                "aggs": {"stars": {"terms": {"field": "stars"}}},
                "post_filters": {
                    "stars": terms_filter("stars"),
                },
            }
        },
        RECORDS_REST_SORT_OPTIONS={
            search_class.Meta.index: dict(
                year=dict(
                    fields=["year"],
                )
            ),
            "test-weko": {
                "test-weko": {"fields": [1,2,3], "nested": 1},
                'controlnumber': {'title': 'ID', 'fields': ['control_number'], 'default_order': 'asc', 'order': 2,}
            },
        },
        FILES_REST_DEFAULT_MAX_FILE_SIZE=None,
        WEKO_ADMIN_ENABLE_LOGIN_INSTRUCTIONS=False,
        WEKO_ADMIN_MANAGEMENT_OPTIONS=WEKO_ADMIN_MANAGEMENT_OPTIONS,
        WEKO_ADMIN_DEFAULT_ITEM_EXPORT_SETTINGS=WEKO_ADMIN_DEFAULT_ITEM_EXPORT_SETTINGS,
        WEKO_ADMIN_CACHE_TEMP_DIR_INFO_KEY_DEFAULT="cache::temp_dir_info",
        WEKO_ITEMS_UI_EXPORT_TMP_PREFIX="weko_export_",
        WEKO_SEARCH_UI_IMPORT_TMP_PREFIX="weko_import_",
        WEKO_AUTHORS_ES_INDEX_NAME="{}-authors".format(index_prefix),
        WEKO_AUTHORS_ES_DOC_TYPE="author-v1.0.0",
        WEKO_HANDLE_ALLOW_REGISTER_CNRI=True,
        WEKO_PERMISSION_ROLE_USER=[
            "System Administrator",
            "Repository Administrator",
            "Contributor",
            "General",
            "Community Administrator",
        ],
        WEKO_RECORDS_UI_LICENSE_DICT=[
            {
                "name": _("write your own license"),
                "value": "license_free",
            },
            # version 0
            {
                "name": _(
                    "Creative Commons CC0 1.0 Universal Public Domain Designation"
                ),
                "code": "CC0",
                "href_ja": "https://creativecommons.org/publicdomain/zero/1.0/deed.ja",
                "href_default": "https://creativecommons.org/publicdomain/zero/1.0/",
                "value": "license_12",
                "src": "88x31(0).png",
                "src_pdf": "cc-0.png",
                "href_pdf": "https://creativecommons.org/publicdomain/zero/1.0/"
                "deed.ja",
                "txt": "This work is licensed under a Public Domain Dedication "
                "International License.",
            },
            # version 3.0
            {
                "name": _("Creative Commons Attribution 3.0 Unported (CC BY 3.0)"),
                "code": "CC BY 3.0",
                "href_ja": "https://creativecommons.org/licenses/by/3.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by/3.0/",
                "value": "license_6",
                "src": "88x31(1).png",
                "src_pdf": "by.png",
                "href_pdf": "http://creativecommons.org/licenses/by/3.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                " 3.0 International License.",
            },
            {
                "name": _(
                    "Creative Commons Attribution-ShareAlike 3.0 Unported "
                    "(CC BY-SA 3.0)"
                ),
                "code": "CC BY-SA 3.0",
                "href_ja": "https://creativecommons.org/licenses/by-sa/3.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-sa/3.0/",
                "value": "license_7",
                "src": "88x31(2).png",
                "src_pdf": "by-sa.png",
                "href_pdf": "http://creativecommons.org/licenses/by-sa/3.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-ShareAlike 3.0 International License.",
            },
            {
                "name": _(
                    "Creative Commons Attribution-NoDerivs 3.0 Unported (CC BY-ND 3.0)"
                ),
                "code": "CC BY-ND 3.0",
                "href_ja": "https://creativecommons.org/licenses/by-nd/3.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nd/3.0/",
                "value": "license_8",
                "src": "88x31(3).png",
                "src_pdf": "by-nd.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nd/3.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NoDerivatives 3.0 International License.",
            },
            {
                "name": _(
                    "Creative Commons Attribution-NonCommercial 3.0 Unported"
                    " (CC BY-NC 3.0)"
                ),
                "code": "CC BY-NC 3.0",
                "href_ja": "https://creativecommons.org/licenses/by-nc/3.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nc/3.0/",
                "value": "license_9",
                "src": "88x31(4).png",
                "src_pdf": "by-nc.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nc/3.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NonCommercial 3.0 International License.",
            },
            {
                "name": _(
                    "Creative Commons Attribution-NonCommercial-ShareAlike 3.0 "
                    "Unported (CC BY-NC-SA 3.0)"
                ),
                "code": "CC BY-NC-SA 3.0",
                "href_ja": "https://creativecommons.org/licenses/by-nc-sa/3.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nc-sa/3.0/",
                "value": "license_10",
                "src": "88x31(5).png",
                "src_pdf": "by-nc-sa.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nc-sa/3.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NonCommercial-ShareAlike 3.0 International License.",
            },
            {
                "name": _(
                    "Creative Commons Attribution-NonCommercial-NoDerivs "
                    "3.0 Unported (CC BY-NC-ND 3.0)"
                ),
                "code": "CC BY-NC-ND 3.0",
                "href_ja": "https://creativecommons.org/licenses/by-nc-nd/3.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nc-nd/3.0/",
                "value": "license_11",
                "src": "88x31(6).png",
                "src_pdf": "by-nc-nd.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nc-nd/3.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NonCommercial-ShareAlike 3.0 International License.",
            },
            # version 4.0
            {
                "name": _("Creative Commons Attribution 4.0 International (CC BY 4.0)"),
                "code": "CC BY 4.0",
                "href_ja": "https://creativecommons.org/licenses/by/4.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by/4.0/",
                "value": "license_0",
                "src": "88x31(1).png",
                "src_pdf": "by.png",
                "href_pdf": "http://creativecommons.org/licenses/by/4.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                " 4.0 International License.",
            },
            {
                "name": _(
                    "Creative Commons Attribution-ShareAlike 4.0 International "
                    "(CC BY-SA 4.0)"
                ),
                "code": "CC BY-SA 4.0",
                "href_ja": "https://creativecommons.org/licenses/by-sa/4.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-sa/4.0/",
                "value": "license_1",
                "src": "88x31(2).png",
                "src_pdf": "by-sa.png",
                "href_pdf": "http://creativecommons.org/licenses/by-sa/4.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-ShareAlike 4.0 International License.",
            },
            {
                "name": _(
                    "Creative Commons Attribution-NoDerivatives 4.0 International "
                    "(CC BY-ND 4.0)"
                ),
                "code": "CC BY-ND 4.0",
                "href_ja": "https://creativecommons.org/licenses/by-nd/4.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nd/4.0/",
                "value": "license_2",
                "src": "88x31(3).png",
                "src_pdf": "by-nd.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nd/4.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NoDerivatives 4.0 International License.",
            },
            {
                "name": _(
                    "Creative Commons Attribution-NonCommercial 4.0 International"
                    " (CC BY-NC 4.0)"
                ),
                "code": "CC BY-NC 4.0",
                "href_ja": "https://creativecommons.org/licenses/by-nc/4.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nc/4.0/",
                "value": "license_3",
                "src": "88x31(4).png",
                "src_pdf": "by-nc.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nc/4.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NonCommercial 4.0 International License.",
            },
            {
                "name": _(
                    "Creative Commons Attribution-NonCommercial-ShareAlike 4.0"
                    " International (CC BY-NC-SA 4.0)"
                ),
                "code": "CC BY-NC-SA 4.0",
                "href_ja": "https://creativecommons.org/licenses/by-nc-sa/4.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
                "value": "license_4",
                "src": "88x31(5).png",
                "src_pdf": "by-nc-sa.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nc-sa/4.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NonCommercial-ShareAlike 4.0 International License.",
            },
            {
                "name": _(
                    "Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 "
                    "International (CC BY-NC-ND 4.0)"
                ),
                "code": "CC BY-NC-ND 4.0",
                "href_ja": "https://creativecommons.org/licenses/by-nc-nd/4.0/deed.ja",
                "href_default": "https://creativecommons.org/licenses/by-nc-nd/4.0/",
                "value": "license_5",
                "src": "88x31(6).png",
                "src_pdf": "by-nc-nd.png",
                "href_pdf": "http://creativecommons.org/licenses/by-nc-nd/4.0/",
                "txt": "This work is licensed under a Creative Commons Attribution"
                "-NonCommercial-ShareAlike 4.0 International License.",
            },
        ],
        WEKO_RECORDS_UI_BULK_UPDATE_FIELDS=WEKO_RECORDS_UI_BULK_UPDATE_FIELDS,
        WEKO_SEARCH_UI_BULK_EXPORT_URI="URI_EXPORT_ALL",
        WEKO_SEARCH_UI_BULK_EXPORT_EXPIRED_TIME=3,
        WEKO_SEARCH_UI_BULK_EXPORT_TASK="KEY_EXPORT_ALL",
        WEKO_ADMIN_CACHE_PREFIX="admin_cache_{name}_{user_id}",
        WEKO_INDEXTREE_JOURNAL_FORM_JSON_FILE="schemas/schemaform.json",
        WEKO_INDEXTREE_JOURNAL_REST_ENDPOINTS=dict(
            tid=dict(
                record_class="weko_indextree_journal.api:Journals",
                admin_indexjournal_route="/admin/indexjournal/<int:journal_id>",
                journal_route="/admin/indexjournal",
                # item_tree_journal_route='/tree/journal/<int:pid_value>',
                # journal_move_route='/tree/journal/move/<int:index_id>',
                default_media_type="application/json",
                create_permission_factory_imp="weko_indextree_journal.permissions:indextree_journal_permission",
                read_permission_factory_imp="weko_indextree_journal.permissions:indextree_journal_permission",
                update_permission_factory_imp="weko_indextree_journal.permissions:indextree_journal_permission",
                delete_permission_factory_imp="weko_indextree_journal.permissions:indextree_journal_permission",
            )
        ),
        WEKO_OPENSEARCH_SYSTEM_SHORTNAME="WEKO",
        WEKO_BUCKET_QUOTA_SIZE=WEKO_BUCKET_QUOTA_SIZE,
        WEKO_MAX_FILE_SIZE=WEKO_MAX_FILE_SIZE,
        WEKO_OPENSEARCH_SYSTEM_DESCRIPTION=(
            "WEKO - NII Scholarly and Academic Information Navigator"
        ),
        WEKO_OPENSEARCH_IMAGE_URL="static/favicon.ico",
        WEKO_ADMIN_OUTPUT_FORMAT="tsv",
        WEKO_THEME_DEFAULT_COMMUNITY="Root Index",
        WEKO_ITEMS_UI_OUTPUT_REGISTRATION_TITLE="",
        WEKO_ITEMS_UI_MULTIPLE_APPROVALS=True,
        WEKO_THEME_ADMIN_ITEM_MANAGEMENT_TEMPLATE="weko_theme/admin/item_management_display.html",
        THEME_BODY_TEMPLATE=THEME_BODY_TEMPLATE,
        WEKO_THEME_ADMIN_ITEM_MANAGEMENT_INIT_TEMPLATE=WEKO_THEME_ADMIN_ITEM_MANAGEMENT_INIT_TEMPLATE,
        WEKO_SEARCH_REST_ENDPOINTS=dict(
            recid=dict(
                pid_type="recid",
                pid_minter="recid",
                pid_fetcher="recid",
                pid_value="1.0",
                search_class=RecordsSearch,
                # search_index="test-weko",
                # search_index=SEARCH_UI_SEARCH_INDEX,
                search_index="test-weko",
                search_type="item-v1.0.0",
                search_factory_imp="weko_search_ui.query.weko_search_factory",
                # record_class='',
                record_serializers={
                    "application/json": (
                        "invenio_records_rest.serializers" ":json_v1_response"
                    ),
                },
                search_serializers={
                    "application/json": ("weko_records.serializers" ":json_v1_search"),
                },
                index_route="/index/",
                search_api_route="/<string:version>/records",
                search_result_list_route="/<string:version>/records/list",
                tree_route="/index",
                item_tree_route="/index/<string:pid_value>",
                index_move_route="/index/move/<int:index_id>",
                links_factory_imp="weko_search_ui.links:default_links_factory",
                default_media_type="application/json",
                max_result_window=10000,
            ),
        ),
        # WEKO_INDEX_TREE_REST_ENDPOINTS=dict(
        #     tid=dict(
        #         record_class="weko_index_tree.api:Indexes",
        #         index_route="/tree/index/<int:index_id>",
        #         tree_route="/tree",
        #         item_tree_route="/tree/<string:pid_value>",
        #         index_move_route="/tree/move/<int:index_id>",
        #         default_media_type="application/json",
        #         create_permission_factory_imp="weko_index_tree.permissions:index_tree_permission",
        #         read_permission_factory_imp="weko_index_tree.permissions:index_tree_permission",
        #         update_permission_factory_imp="weko_index_tree.permissions:index_tree_permission",
        #         delete_permission_factory_imp="weko_index_tree.permissions:index_tree_permission",
        #     )
        # ),
        WEKO_INDEX_TREE_REST_ENDPOINTS=copy.deepcopy(_WEKO_INDEX_TREE_REST_ENDPOINTS),
        WEKO_INDEX_TREE_STYLE_OPTIONS={
            "id": "weko",
            "widths": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"],
        },
        WEKO_SEARCH_TYPE_KEYWORD="keyword",
        WEKO_SEARCH_UI_SEARCH_TEMPLATE="weko_search_ui/search.html",
        WEKO_INDEX_TREE_INDEX_ADMIN_TEMPLATE="weko_index_tree/admin/index_edit_setting.html",
        WEKO_INDEX_TREE_LIST_API="/api/tree",
        WEKO_INDEX_TREE_API="/api/tree/index/",
        WEKO_SEARCH_UI_TO_NUMBER_FORMAT="99999999999999.99",
        WEKO_SEARCH_UI_BASE_TEMPLATE=WEKO_SEARCH_UI_BASE_TEMPLATE,
        WEKO_SEARCH_KEYWORDS_DICT=WEKO_SEARCH_KEYWORDS_DICT,
        SWORD_METADATA_FILE = SWORD_METADATA_FILE,
        ROCRATE_METADATA_FILE = ROCRATE_METADATA_FILE,
        WEKO_ITEMS_UI_INDEX_PATH_SPLIT = '///',
        WEKO_SEARCH_UI_BULK_EXPORT_RETRY = 5,
        WEKO_SEARCH_UI_BULK_EXPORT_LIMIT = 100
    )
    app_.url_map.converters["pid"] = PIDConverter
    app_.config["RECORDS_REST_ENDPOINTS"]["recid"]["search_class"] = search_class

    # Parameterize application.
    if hasattr(request, "param"):
        if "endpoint" in request.param:
            app.config["RECORDS_REST_ENDPOINTS"]["recid"].update(
                request.param["endpoint"]
            )
        if "records_rest_endpoints" in request.param:
            original_endpoint = app.config["RECORDS_REST_ENDPOINTS"]["recid"]
            del app.config["RECORDS_REST_ENDPOINTS"]["recid"]
            for new_endpoint_prefix, new_endpoint_value in request.param[
                "records_rest_endpoints"
            ].items():
                new_endpoint = dict(original_endpoint)
                new_endpoint.update(new_endpoint_value)
                app.config["RECORDS_REST_ENDPOINTS"][new_endpoint_prefix] = new_endpoint

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
    InvenioREST(app_)
    InvenioIndexer(app_)
    InvenioI18N(app_)
    InvenioPIDRelations(app_)
    InvenioOAIServer(app_)
    InvenioMail(app_)
    InvenioStats(app_)
    InvenioAdmin(app_)
    InvenioPIDStore(app_)
    InvenioFilesREST(app_)
    InvenioDeposit(app_)
    WekoRecords(app_)
    WekoSearchUI(app_)
    WekoWorkflow(app_)
    WekoGroups(app_)
    WekoAdmin(app_)
    WekoIndexTree(app_)
    WekoIndexTreeREST(app_)
    # WekoTheme(app_)
    # InvenioCommunities(app_)

    # search = InvenioSearch(app_, client=MockEs())
    # search.register_mappings(search_class.Meta.index, 'mock_module.mappings')
    InvenioRecordsREST(app_)
    app_.register_blueprint(create_blueprint_from_app(app_))
    from weko_theme.views import blueprint as weko_theme_blueprint
    app_.register_blueprint(weko_theme_blueprint)
    from invenio_communities.views.ui import blueprint as invenio_communities_blueprint
    app_.register_blueprint(invenio_communities_blueprint)

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
def i18n_app(app):
    with app.test_request_context(headers=[("Accept-Language", "ja")]):
        app.extensions["invenio-oauth2server"] = 1
        app.extensions["invenio-queues"] = 1
        yield app


@pytest.yield_fixture()
def client(app):
    """Get test client."""
    with app.test_client() as client:
        yield client


@pytest.yield_fixture()
def client_rest(app):
    app.register_blueprint(
        create_blueprint(app, app.config["WEKO_SEARCH_REST_ENDPOINTS"])
    )
    with app.test_client() as client:
        yield client


@pytest.yield_fixture()
def client_rest_weko_search_ui(app):
    WekoSearchREST(app)
    with app.test_client() as client:
        yield client


@pytest.yield_fixture()
def client_api(app):
    app.register_blueprint(blueprint_api)
    with app.test_client() as client:
        yield client


@pytest.yield_fixture()
def client_request_args(app, file_instance_mock):
    app.register_blueprint(
        create_blueprint(app, app.config["WEKO_SEARCH_REST_ENDPOINTS"])
    )

    file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data",
        "sample_file",
        "sample_file.txt",
    )

    # files = {'upload_file': open(file_path,'rb')}
    # values = {'DB': 'photcat', 'OUT': 'txt', 'SHORT': 'short'}

    # r = requests.post(url, files=files, data=values)

    with app.test_client() as client:
        with patch("flask.templating._render", return_value=""):
            r = client.get(
                "/",
                query_string={
                    "index_id": "33",
                    "page": 1,
                    "count": 20,
                    "term": 14,
                    "lang": "en",
                    "parent_id": 33,
                    "index_info": {},
                    "community": "comm1",
                    "item_link": "1",
                    "is_search": 1,
                    "search_type": WEKO_SEARCH_TYPE_DICT["INDEX"],
                    "is_change_identifier": True,
                    "remote_addr": "0.0.0.0",
                    "referrer": "test",
                    "host": "127.0.0.1",
                    # 'search_type': WEKO_SEARCH_TYPE_DICT["FULL_TEXT"],
                },
            )
        yield r


@pytest.fixture()
def location(app, db):
    """Create default location."""
    tmppath = tempfile.mkdtemp()
    with db.session.begin_nested():
        Location.query.delete()
        loc = Location(name="local", uri=tmppath, default=True)
        db.session.add(loc)
    db.session.commit()
    return location


@pytest.fixture()
def user(app, db):
    """Create a example user."""
    return create_test_user(email="test@test.org")


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


@pytest.fixture
def indices(app, db):
    with db.session.begin_nested():
        # Create a test Indices
        testIndexOne = Index(
            index_name="testIndexOne",
            browsing_role="Contributor",
            public_state=True,
            id=11,
        )
        testIndexTwo = Index(
            index_name="testIndexTwo",
            browsing_group="group_test1",
            public_state=True,
            id=22,
        )
        testIndexThree = Index(
            index_name="testIndexThree",
            browsing_role="Contributor",
            public_state=True,
            harvest_public_state=True,
            id=33,
            item_custom_sort={"1": 1},
            public_date=datetime.today() - timedelta(days=1),
        )
        testIndexThreeChild = Index(
            index_name="testIndexThreeChild",
            browsing_role="Contributor",
            parent=33,
            index_link_enabled=True,
            index_link_name="test_link",
            public_state=True,
            harvest_public_state=False,
            id=44,
            public_date=datetime.today() - timedelta(days=1),
        )
        testIndexMore = Index(
            index_name="testIndexMore", parent=33, public_state=True, id="more"
        )
        testIndexPrivate = Index(
            index_name="testIndexPrivate", public_state=False, id=55
        )

        db.session.add(testIndexThree)
        db.session.add(testIndexThreeChild)

    return {
        "index_dict": dict(testIndexThree),
        "index_non_dict": testIndexThree,
        "index_non_dict_child": testIndexThreeChild,
    }


@pytest.fixture
def indices2(app, db):
    dict_list = []
    with db.session.begin_nested():
        testIndexA = Index(
            index_name="A",
            index_name_english="A",
            browsing_role="3,-98,-99",
            parent=0,
            position=1,
            public_state=True,
            id=1
        )
        testIndexAC = Index(
            index_name="C",
            index_name_english="C",
            browsing_role="3,-98,-99",
            parent=1,
            position=1,
            public_state=True,
            id=2
        )
        testIndexB = Index(
            index_name="B",
            index_name_english="B",
            browsing_role="3,-98,-99",
            parent=0,
            position=2,
            public_state=True,
            id=3
        )
        testIndexBC = Index(
            index_name="C",
            index_name_english="C",
            browsing_role="3,-98,-99",
            parent=3,
            position=1,
            public_state=True,
            id=4
        )

        db.session.add(testIndexA)
        db.session.add(testIndexAC)
        db.session.add(testIndexB)
        db.session.add(testIndexBC)
        dict_list.append(testIndexA)
        dict_list.append(testIndexAC)
        dict_list.append(testIndexB)
        dict_list.append(testIndexBC)


@pytest.fixture()
def esindex(app, db_records):
    current_search_client.indices.delete(index="test-*")
    with open("tests/data/item-v1.0.0.json", "r") as f:
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
    # print(current_search_client.indices.get_alias())

    for depid, recid, parent, doi, record, item in db_records:
        current_search_client.index(
            index="test-weko-item-v1.0.0",
            doc_type="item-v1.0.0",
            id=record.id,
            body=record,
            refresh="true",
        )

    try:
        yield current_search_client
    finally:
        current_search_client.indices.delete(index="test-*")


@pytest.fixture()
def es_authors_index(app):
    current_search_client.indices.delete(index="test-*")

    try:
        index_name = "test-authors"
        current_search_client.indices.create(
            index_name
        )

    except Exception:
        pass

    try:
        yield current_search_client
    finally:
        current_search_client.indices.delete(index=index_name)


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


@pytest.fixture()
def db_records2(db, instance_path, users):
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
            result.append(create_record(db,record_data[d], item_data[d]))
    db.session.commit()

    index_metadata = {
        "id": 1,
        "parent": 0,
        "value": "Index(public_state = True,harvest_public_state = True)",
    }
    with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
        # ret = Indexes.create(0, index_metadata)
        index_one = Index(id=index_metadata["id"], index_name="index_one")
        db.session.add(index_one)
        db.session.commit()
        index = Index.get_index_by_id(1)
        index.public_state = True
        index.harvest_public_state = True

    yield result


@pytest.fixture()
def db_records3(db):
    record_data = json_data("data/test_records2.json")
    item_data = json_data("data/test_items2.json")
    record_num = len(record_data)
    result = []
    with db.session.begin_nested():
        for d in range(record_num):
            result.append(create_record(record_data[d], item_data[d]))
    db.session.commit()

    yield result


@pytest.fixture
def redis_connect(app):
    redis_connection = RedisConnection().connection(
        db=app.config["CACHE_REDIS_DB"], kv=True
    )
    return redis_connection


@pytest.fixture()
def db_register(app, db):
    action_datas = dict()
    with open("tests/data/actions.json", "r") as f:
        action_datas = json.load(f)
    actions_db = list()
    with db.session.begin_nested():
        for data in action_datas:
            actions_db.append(Action(**data))
        db.session.add_all(actions_db)

    actionstatus_datas = dict()
    with open("tests/data/action_status.json") as f:
        actionstatus_datas = json.load(f)
    actionstatus_db = list()
    with db.session.begin_nested():
        for data in actionstatus_datas:
            actionstatus_db.append(ActionStatus(**data))
        db.session.add_all(actionstatus_db)

    index = Index(public_state=True)

    index_private = Index(
        id=999,
        parent=1,
        public_state=False,
        public_date=datetime.strptime("2099/04/24 0:00:00", "%Y/%m/%d %H:%M:%S"),
    )

    flow_define = FlowDefine(
        flow_id=uuid.uuid4(), flow_name="Registration Flow", flow_user=1
    )

    item_type_name = ItemTypeName(
        name="test item type", has_site_license=True, is_active=True
    )

    item_type = ItemType(
        name_id=1,
        harvesting_type=True,
        schema={"type": "test schema"},
        form={"type": "test form"},
        render={"type": "test render"},
        tag=1,
        version_id=1,
        is_deleted=False,
    )

    flow_action1 = FlowAction(
        status="N",
        flow_id=flow_define.flow_id,
        action_id=1,
        action_version="1.0.0",
        action_order=1,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={},
    )
    flow_action2 = FlowAction(
        status="N",
        flow_id=flow_define.flow_id,
        action_id=3,
        action_version="1.0.0",
        action_order=2,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={},
    )
    flow_action3 = FlowAction(
        status="N",
        flow_id=flow_define.flow_id,
        action_id=5,
        action_version="1.0.0",
        action_order=3,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={},
    )

    workflow = WorkFlow(
        flows_id=uuid.uuid4(),
        flows_name="test workflow1",
        itemtype_id=1,
        index_tree_id=1,
        flow_id=1,
        is_deleted=False,
        open_restricted=False,
        location_id=None,
        is_gakuninrdm=False,
    )

    activity = Activity(
        activity_id="1",
        workflow_id=1,
        flow_id=flow_define.id,
        action_id=1,
        activity_login_user=1,
        activity_update_user=1,
        activity_start=datetime.strptime(
            "2022/04/14 3:01:53.931", "%Y/%m/%d %H:%M:%S.%f"
        ),
        activity_community_id=3,
        activity_confirm_term_of_use=True,
        title="test",
        shared_user_id=-1,
        extra_info={},
        action_order=6,
    )

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
        "flow_define": flow_define,
        "item_type": item_type,
        "workflow": workflow,
        "activity": activity,
        "indices": {
            "index": index,
            "index_private": index_private,
        },
    }


@pytest.fixture()
def db_register2(app, db):
    session_lifetime = SessionLifetime(lifetime=60, is_delete=False)

    with db.session.begin_nested():
        db.session.add(session_lifetime)


@pytest.fixture()
def records(db):
    with db.session.begin_nested():
        id1 = uuid.UUID("b7bdc3ad-4e7d-4299-bd87-6d79a250553f")
        rec1 = RecordMetadata(
            id=id1, json=json_data("data/record01.json"), version_id=1
        )

        id2 = uuid.UUID("362e800c-08a2-425d-a2b6-bcae7d5c3701")
        rec2 = RecordMetadata(
            id=id2, json=json_data("data/record02.json"), version_id=2
        )

        id3 = uuid.UUID("3ead53d0-8e4a-489e-bb6c-d88433a029c2")
        rec3 = RecordMetadata(
            id=id3, json=json_data("data/record03.json"), version_id=3
        )

        db.session.add(rec1)
        db.session.add(rec2)
        db.session.add(rec3)

        search_query_result = json_data("data/search_result.json")

    return search_query_result


@pytest.fixture()
def pdfcoverpage(app, db):
    with db.session.begin_nested():
        pdf_cover_sample = PDFCoverPageSettings(
            avail="enable",
            header_display_type="string",
            header_output_string="test",
            header_output_image="test",
            header_display_position="center",
        )

        db.session.add(pdf_cover_sample)

    return pdf_cover_sample


@pytest.fixture()
def item_type(app, db):
    _item_type_name = ItemTypeName(name="test")
    _item_type_name2 = ItemTypeName(name="test2")
    _item_type_name3 = ItemTypeName(name="test3")

    _render = {
        "meta_list": {
            "file": {
                "title": "ファイル名",
                "title_i18n": {"ja": "ファイル名", "en": "File"},
                "input_type": "cus_1",
                "input_value": "",
                "option": {
                    "required": False,
                    "multiple": True,
                    "hidden": False,
                    "showlist": False,
                    "crtf": False,
                    "oneline": False,
                },
            },
            "thumbnail": {
                "title": "ラベル",
                "title_i18n": {"ja": "ラベル", "en": "Thumbnail"},
                "input_type": "cus_2",
                "input_value": "",
                "option": {
                    "required": False,
                    "multiple": True,
                    "hidden": False,
                    "showlist": False,
                    "crtf": False,
                    "oneline": False,
                },
            },
        },
        "meta_fix": {
            "pubdate": {
                "title": "公開日",
                "title_i18n": {"ja": "公開日", "en": "PubDate"},
                "input_type": "datetime",
                "input_value": "",
                "option": {
                    "required": True,
                    "multiple": False,
                    "hidden": False,
                    "showlist": False,
                    "crtf": False,
                },
            }
        },
        "table_row_map": {
            "schema": {
                "properties": {
                    "item_1": {},
                    "pubdate": {"type": "string", "title": "公開日", "format": "datetime"},
                    "file": {
                        "type": "array",
                        "format": "array",
                        "title": "URI",
                        "items": {
                            "type": "object",
                            "format": "object",
                            "properties": {
                                "url": {
                                    "type": "object",
                                    "format": "object",
                                    "properties": {
                                        "label": {
                                            "format": "text",
                                            "title": "ラベル",
                                            "type": "string",
                                        },
                                        "url": {
                                            "format": "text",
                                            "title": "本文URL",
                                            "type": "string",
                                        },
                                    },
                                    "title": "本文URL",
                                },
                                "filename": {
                                    "type": ["null", "string"],
                                    "format": "text",
                                    "enum": [],
                                    "title": "ファイル名",
                                },
                            },
                        },
                    },
                    "thumbnail": {
                        "type": "array",
                        "format": "array",
                        "title": "URI",
                        "items": {
                            "type": "object",
                            "format": "object",
                            "properties": {
                                "thumbnail_label": {
                                    "format": "text",
                                    "title": "ラベル",
                                    "type": "string",
                                },
                                "thumbnail_url": {
                                    "format": "text",
                                    "title": "URI",
                                    "type": "string",
                                },
                            },
                        },
                    },
                }
            }
        },
        "table_row": ["pubdate", "file", "thumbnail"],
    }

    with open("tests/data/itemtype_schema.json", "r") as f:
        item_type_schema = json.load(f)

    sample1 = ItemTypes.create(
        name="test",
        item_type_name=_item_type_name,
        schema=item_type_schema,
        render=_render,
        tag=1,
    )

    sample2 = ItemTypes.create(
        name="test2",
        item_type_name=_item_type_name2,
        schema=item_type_schema,
        render=_render,
        tag=2,
    )

    sample3 = ItemTypes.create(
        name="test3",
        item_type_name=_item_type_name3,
        schema=item_type_schema,
        render=_render,
        tag=3,
    )

    return [sample1, sample2, sample3]


@pytest.fixture()
def item_type2(app, db):
    _item_type_name = ItemTypeName(name="test2")

    _render = {
        "meta_list": {},
        "table_row_map": {"schema": {"properties": {"item_1": {}}}},
        "table_row": ["1"],
    }

    return ItemTypes.create(
        name="test2", item_type_name=_item_type_name, schema={}, render=_render, tag=1
    )

@pytest.fixture()
def item_type_mapping2(app, db, item_type2):
    return Mapping.create(item_type2.model.id, {})


@pytest.fixture()
def mock_execute(app):
    def factory(data):
        if isinstance(data, str):
            data = json_data(data)
        dummy = response.Response(Search(), data)
        return dummy

    return factory


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
def communities(app, db, user, indices):
    """Create some example communities."""
    user1 = db_.session.merge(user)
    ds = app.extensions["invenio-accounts"].datastore
    r = ds.create_role(name="superuser", description="1234")
    ds.add_role_to_user(user1, r)
    ds.commit()
    db.session.commit()

    comm0 = Community.create(
        community_id="comm1",
        role_id=r.id,
        page=0, ranking=0, curation_policy='',fixed_points=0, thumbnail_path='',catalog_json=[], login_menu_enabled=False,
        id_user=user1.id,
        title="Title1",
        description="Description1",
        root_node_id=33,
    )
    db.session.add(comm0)

    return comm0


@pytest.fixture()
def communities2(app, db, user, indices):
    """Create some example communities."""
    user1 = db_.session.merge(user)
    ds = app.extensions["invenio-accounts"].datastore
    r = ds.create_role(name="superuser", description="1234")
    ds.add_role_to_user(user1, r)
    ds.commit()
    db.session.commit()

    comm0 = Community.create(
        community_id="Root Index",
        role_id=r.id,
        id_user=user1.id,
        title="Title1",
        description="Description1",
        root_node_id=33,
    )
    db.session.add(comm0)

    return comm0


@pytest.fixture()
def communities3(app, db, user, indices):
    """Create some example communities."""
    user1 = db_.session.merge(user)
    ds = app.extensions["invenio-accounts"].datastore
    r = ds.create_role(name="superuser", description="1234")
    ds.add_role_to_user(user1, r)
    ds.commit()
    db.session.commit()

    comm0 = Community.create(
        community_id="comm1",
        role_id=r.id,
        id_user=user1.id,
        title="Title1",
        description="Description1",
        root_node_id=33,
    )
    db.session.add(comm0)

    return comm0


@pytest.fixture()
def mock_users():
    """Create mock users."""
    mock_auth_user = Mock()
    mock_auth_user.get_id = lambda: "123"
    mock_auth_user.is_authenticated = True

    mock_anon_user = Mock()
    mock_anon_user.is_authenticated = False
    return {"anonymous": mock_anon_user, "authenticated": mock_auth_user}


@pytest.yield_fixture()
def mock_user_ctx(mock_users):
    """Run in a mock authenticated user context."""
    with patch("invenio_stats.utils.current_user", mock_users["authenticated"]):
        yield


@pytest.fixture
def file_instance_mock(db):
    """Mock of a file instance."""

    class FileInstance(object):
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data",
        "sample_file",
        "sample_file.txt",
    )

    file = FileInstance(
        id="deadbeef-65bd-4d9b-93e2-ec88cc59aec5", uri=file_path, size=4, updated=None
    )

    # db.session.add(file)
    # db.session.commit()

@pytest.fixture
def create_file_instance(db):
    file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data",
        "sample_file",
        "sample_file.txt",
    )

    file = FileInstance(
        id="deadbeef-65bd-4d9b-93e2-ec88cc59aec5", uri=file_path, size=4, updated=None
    )

    db.session.add(file)
    db.session.commit()
    return file_path


@pytest.yield_fixture()
def es(app):
    """Provide elasticsearch access, create and clean indices.

    Don't create template so that the test or another fixture can modify the
    enabled events.
    """
    current_search_client.indices.delete(index="*")
    current_search_client.indices.delete_template("*")
    list(current_search.create())
    try:
        yield current_search_client
    finally:
        current_search_client.indices.delete(index="*")
        current_search_client.indices.delete_template("*")


def generate_events(
    app,
    index_id="33",
    page=1,
    count=20,
    term=14,
    lang="en",
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
                    entry_date, datetime.time(minute=ts % 60, second=ts % 60)
                ).isoformat(),
                index_id="33",
                page=1,
                count=20,
                term=14,
                lang="en",
            )

            yield build_event(True)

    mock_queue = Mock()
    mock_queue.consume.return_value = generator_list()
    # mock_queue.routing_key = 'stats-file-download'
    mock_queue.routing_key = "generate-sample"

    EventsIndexer(
        mock_queue, preprocessors=[build_file_unique_id], double_click_window=0
    ).run()
    current_search_client.indices.refresh(index="*")


@pytest.yield_fixture()
def generate_request(app, es, mock_user_ctx, request):
    """Parametrized pre indexed sample events."""
    generate_events(app=app, **request.param)
    yield


@pytest.yield_fixture()
def dummy_location(db):
    """File system location."""
    tmppath = tempfile.mkdtemp()

    loc = Location(name="testloc", uri=tmppath, default=True)
    db.session.add(loc)
    db.session.commit()

    yield loc

    shutil.rmtree(tmppath)


# @pytest.fixture()
# def bucket(db, dummy_location):
#     """File system location."""
#     b1 = Bucket.create()
#     db.session.commit()
#     return b1


@pytest.yield_fixture()
def permissions(db, bucket):
    """Permission for users."""
    users = {
        None: None,
    }

    for user in ["auth", "location", "bucket", "objects", "objects-read-version"]:
        users[user] = create_test_user(
            email="{0}@invenio-software.org".format(user), password="pass1", active=True
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
        db.session.add(ActionUsers(action=perm.value, user=users["location"]))
    for perm in bucket_perms:
        db.session.add(
            ActionUsers(
                action=perm.value, argument=str(bucket.id), user=users["bucket"]
            )
        )
    for perm in objects_perms:
        db.session.add(
            ActionUsers(
                action=perm.value, argument=str(bucket.id), user=users["objects"]
            )
        )
    db.session.commit()

    yield users


@pytest.yield_fixture()
def index_style(db):
    index_style_one = IndexStyle(id="weko", index_link_enabled=True)
    db.session.add(index_style_one)
    db.session.commit()


@pytest.fixture()
def facet_search_setting(db):
    datas = json_data("data/facet_search_setting.json")
    settings = list()

    for setting in datas:
        settings.append(FacetSearchSetting(**datas[setting]))
    with db.session.begin_nested():
        db.session.add_all(settings)


@pytest.fixture()
def db_activity(db, db_records2, db_itemtype, db_workflow, users):
    user = users[3]["id"]
    depid, recid, parent, doi, record, item = db_records2[0]
    rec_uuid = uuid.uuid4()
    draft = PersistentIdentifier.create(
        "recid",
        "{}.0".format((parent.pid_value).split(":")[1]),
        object_type="rec",
        object_uuid=rec_uuid,
        status=PIDStatus.REGISTERED,
    )
    rel = PIDRelation.create(parent, draft, 2)
    flow_define = db_workflow["flow_define"]
    workflow = db_workflow["workflow"]
    activity = Activity(
        activity_id="A-00000000-00001",
        workflow_id=workflow.id,
        flow_id=flow_define.id,
        action_id=2,
        activity_login_user=user,
        action_status=ActionStatusPolicy.ACTION_DOING,
        activity_update_user=user,
        item_id=draft.object_uuid,
        activity_start=datetime.strptime(
            "2022/04/14 3:01:53.931", "%Y/%m/%d %H:%M:%S.%f"
        ),
        activity_confirm_term_of_use=True,
        title="test",
        shared_user_id=-1,
        extra_info={},
        action_order=6,
    )
    with db.session.begin_nested():
        db.session.add(activity)
        db.session.add(rel)

    return {"activity": activity, "recid": recid, "item": item, "record": record}


@pytest.fixture()
def db_itemtype(app, db, make_itemtype):
    itemtype_id = 1000
    itemtype_data = {
        "name": "テストアイテムタイプ_" + str(itemtype_id),
        "schema": "tests/data/itemtype_schema.json",
        "form": "tests/data/itemtype_form.json",
        "render": "tests/data/itemtype_render.json",
        "mapping":"tests/data/itemtype_mapping.json"
    }

    return make_itemtype(itemtype_id, itemtype_data)


@pytest.fixture()
def db_workflow(app, db, db_itemtype, users):
    action_datas = dict()
    with open("tests/data/actions.json", "r") as f:
        action_datas = json.load(f)
    actions_db = list()
    with db.session.begin_nested():
        for data in action_datas:
            actions_db.append(Action(**data))
        db.session.add_all(actions_db)

    actionstatus_datas = dict()
    with open("tests/data/action_status.json") as f:
        actionstatus_datas = json.load(f)
    actionstatus_db = list()
    with db.session.begin_nested():
        for data in actionstatus_datas:
            actionstatus_db.append(ActionStatus(**data))
        db.session.add_all(actionstatus_db)

    flow_id = uuid.uuid4()
    flow_define = FlowDefine(
        flow_id=flow_id, flow_name="Registration", flow_user=1, flow_status="A"
    )
    flow_action1 = FlowAction(
        status="N",
        flow_id=flow_id,
        action_id=1,
        action_version="1.0.0",
        action_order=1,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={},
    )
    flow_action2 = FlowAction(
        status="N",
        flow_id=flow_id,
        action_id=3,
        action_version="1.0.0",
        action_order=2,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={},
    )
    flow_action3 = FlowAction(
        status="N",
        flow_id=flow_id,
        action_id=5,
        action_version="1.0.0",
        action_order=3,
        action_condition="",
        action_status="A",
        action_date=datetime.strptime("2018/07/28 0:00:00", "%Y/%m/%d %H:%M:%S"),
        send_mail_setting={},
    )

    workflow = WorkFlow(
        flows_id=uuid.uuid4(),
        flows_name="test workflow1",
        itemtype_id=1,
        index_tree_id=None,
        flow_id=1,
        is_deleted=False,
        open_restricted=False,
        location_id=None,
        is_gakuninrdm=False,
    )
    activity = Activity(
        activity_id="A-00000000-00000",
        workflow_id=1,
        flow_id=flow_define.id,
        action_id=1,
        activity_login_user=1,
        activity_update_user=1,
        activity_start=datetime.strptime(
            "2022/04/14 3:01:53.931", "%Y/%m/%d %H:%M:%S.%f"
        ),
        activity_community_id=3,
        activity_confirm_term_of_use=True,
        title="test",
        shared_user_id=-1,
        extra_info={},
        action_order=6,
    )

    with db.session.begin_nested():
        db.session.add(flow_define)
        db.session.add(flow_action1)
        db.session.add(flow_action2)
        db.session.add(flow_action3)
        db.session.add(workflow)
        db.session.add(activity)

    return {
        "flow_define": flow_define,
        "workflow": workflow,
        "activity": activity,
        "flow_action1": flow_action1,
        "flow_action2": flow_action2,
        "flow_action3": flow_action3,
    }


@pytest.fixture()
def bucket(db, location):
    """File system location."""
    bucket = Bucket.create(location)
    db.session.commit()
    return bucket


@pytest.fixture()
def testfile(db, bucket):
    """File system location."""
    obj = ObjectVersion.create(bucket, "testfile", stream=BytesIO(b"atest"))
    db.session.commit()
    return obj


@pytest.yield_fixture()
def search_url():
    """Search class."""
    yield url_for("invenio_records_rest.recid_list")


@pytest.fixture()
def filerecord(db):
    """Record fixture."""
    rec_uuid = uuid.uuid4()
    provider = RecordIdProvider.create(object_type="rec", object_uuid=rec_uuid)
    filerecord = Record.create(
        {
            "control_number": provider.pid.pid_value,
            "title": "TestDefault",
        },
        id_=rec_uuid,
    )
    db.session.commit()
    return filerecord


@pytest.fixture()
def record_with_file(db, filerecord, testfile):
    """Record with a test file."""
    rb = RecordsBuckets(record_id=filerecord.id, bucket_id=testfile.bucket_id)
    db.session.add(rb)
    filerecord.update(
        dict(
            _files=[
                dict(
                    bucket=str(testfile.bucket_id),
                    key=testfile.key,
                    size=testfile.file.size,
                    checksum=str(testfile.file.checksum),
                    version_id=str(testfile.version_id),
                ),
            ]
        )
    )
    filerecord.commit()
    db.session.commit()
    return filerecord


@pytest.fixture()
def test_records():
    results = []
    #
    results.append(
        {
            "input": os.path.join(FIXTURE_DIR, "records", "successRecord00.json"),
            "output": "",
        }
    )
    results.append(
        {
            "input": os.path.join(FIXTURE_DIR, "records", "successRecord01.json"),
            "output": "",
        }
    )
    results.append(
        {
            "input": os.path.join(FIXTURE_DIR, "records", "successRecord02.json"),
            "output": "",
        }
    )
    # 存在しない日付が設定されている
    results.append(
        {
            "input": os.path.join(FIXTURE_DIR, "records", "noExistentDate00.json"),
            "output": "Please specify Open Access Date with YYYY-MM-DD.",
        }
    )
    # 日付がYYYY-MM-DD でない
    results.append(
        {
            "input": os.path.join(FIXTURE_DIR, "records", "wrongDateFormat00.json"),
            "output": "Please specify Open Access Date with YYYY-MM-DD.",
        }
    )
    results.append(
        {
            "input": os.path.join(FIXTURE_DIR, "records", "wrongDateFormat01.json"),
            "output": "Please specify Open Access Date with YYYY-MM-DD.",
        }
    )
    results.append(
        {
            "input": os.path.join(FIXTURE_DIR, "records", "wrongDateFormat02.json"),
            "output": "Please specify Open Access Date with YYYY-MM-DD.",
        }
    )

    return results


@pytest.fixture()
def test_list_records():
    tmp = []
    results = []
    tmp.append(
        {
            "input": os.path.join(FIXTURE_DIR, "list_records", "list_records.json"),
            "output": os.path.join(
                FIXTURE_DIR, "list_records", "list_records_result.json"
            ),
        }
    )
    tmp.append(
        {
            "input": os.path.join(FIXTURE_DIR, "list_records", "list_records00.json"),
            "output": os.path.join(
                FIXTURE_DIR, "list_records", "list_records00_result.json"
            ),
        }
    )
    tmp.append(
        {
            "input": os.path.join(FIXTURE_DIR, "list_records", "list_records01.json"),
            "output": os.path.join(
                FIXTURE_DIR, "list_records", "list_records01_result.json"
            ),
        }
    )
    tmp.append(
        {
            "input": os.path.join(FIXTURE_DIR, "list_records", "list_records02.json"),
            "output": os.path.join(
                FIXTURE_DIR, "list_records", "list_records02_result.json"
            ),
        }
    )

    tmp.append(
        {
            "input": os.path.join(FIXTURE_DIR, "list_records", "list_records03.json"),
            "output": os.path.join(
                FIXTURE_DIR, "list_records", "list_records03_result.json"
            ),
        }
    )

    for t in tmp:
        with open(t.get("input"), encoding="utf-8") as f:
            input_data = json.load(f)
        with open(t.get("output"), encoding="utf-8") as f:
            output_data = json.load(f)
        results.append({"input": input_data, "output": output_data})
    return results


@pytest.fixture()
def test_importdata():
    files = [os.path.join(FIXTURE_DIR, "import00.zip")]
    return files


@pytest.fixture()
def mocker_itemtype(mocker):
    item_type = Mock()
    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "item_type/15_render.json"
    )
    with open(filepath, encoding="utf-8") as f:
        render = json.load(f)
    item_type.render = render

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "item_type/15_schema.json"
    )
    with open(filepath, encoding="utf-8") as f:
        schema = json.load(f)
    item_type.schema = schema

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "item_type/15_form.json"
    )
    with open(filepath, encoding="utf-8") as f:
        form = json.load(f)
    item_type.form = form

    item_type.item_type_name.name = "デフォルトアイテムタイプ（フル）"
    item_type.item_type_name.item_type.first().id = 15

    mocker.patch("weko_records.api.ItemTypes.get_by_id", return_value=item_type)


@pytest.fixture()
def celery(app):
    """Get queueobject for testing bulk operations."""
    return app.extensions["flask-celeryext"].celery


@pytest.fixture()
def record_with_metadata():
    data = json_data("data/list_records/list_records_new_item_doira.json")
    return data


@pytest.fixture()
def item_render():
    data = json_data("data/itemtype1_render.json")
    return data


@pytest.yield_fixture()
def es(app):
    """Elasticsearch fixture."""
    try:
        list(current_search.create())
    # except RequestError:
    except:
        list(current_search.delete(ignore=[404]))
        list(current_search.create(ignore=[400]))
    current_search_client.indices.refresh()
    yield current_search_client
    list(current_search.delete(ignore=[404]))


@pytest.fixture()
def deposit(app, es, users, location, db):
    """New deposit with files."""
    record = {"title": "fuu"}
    with app.test_request_context():
        datastore = app.extensions["security"].datastore
        login_user(datastore.find_user(email=users[0]["email"]))
        deposit = Deposit.create(record)
        deposit.commit()
        db.session.commit()
    sleep(2)
    return deposit


@pytest.fixture()
def db_index(client, users):
    index_metadata = {
        "id": 1,
        "parent": 0,
        "value": "Index(public_state = True,harvest_public_state = True)",
    }

    with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
        ret = Indexes.create(0, index_metadata)
        index = Index.get_index_by_id(1)
        # index.public_state = True
        # index.harvest_public_state = True

    index_metadata = {
        "id": 2,
        "parent": 0,
        "value": "Index(public_state = True,harvest_public_state = False)",
    }

    with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
        Indexes.create(0, index_metadata)
        index = Index.get_index_by_id(2)
        # index.public_state = True
        # index.harvest_public_state = False

    index_metadata = {
        "id": 3,
        "parent": 0,
        "value": "Index(public_state = False,harvest_public_state = True)",
    }

    with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
        Indexes.create(0, index_metadata)
        index = Index.get_index_by_id(3)
        # index.public_state = False
        # index.harvest_public_state = True

    index_metadata = {
        "id": 4,
        "parent": 0,
        "value": "Index(public_state = False,harvest_public_state = False)",
    }

    with patch("flask_login.utils._get_user", return_value=users[3]["obj"]):
        Indexes.create(0, index_metadata)
        index = Index.get_index_by_id(4)
        # index.public_state = False
        # index.harvest_public_state = False


@pytest.fixture()
def es_records(app, db, db_index, location, db_itemtype, db_oaischema):
    indexer = WekoIndexer()
    indexer.get_es_index()
    results = []
    with app.test_request_context():
        for i in range(1, 10):
            record_data = {
                "_oai": {
                    "id": "oai:weko3.example.org:000000{:02d}".format(i),
                    "sets": ["{}".format((i % 2) + 1)],
                },
                "path": ["{}".format((i % 2) + 1)],
                "recid": "{}".format(i),
                "pubdate": {
                    "attribute_name": "PubDate",
                    "attribute_value": "2022-08-20",
                },
                "_buckets": {"deposit": "3e99cfca-098b-42ed-b8a0-20ddd09b3e02"},
                "_deposit": {
                    "id": "{}".format(i),
                    "pid": {"type": "depid", "value": "{}".format(i), "revision_id": 0},
                    "owner": "1",
                    "owners": [1],
                    "status": "draft",
                    "created_by": 1,
                    "owners_ext": {
                        "email": "wekosoftware@nii.ac.jp",
                        "username": "",
                        "displayname": "",
                    },
                },
                "item_title": "title",
                "author_link": [],
                "item_type_id": "1",
                "publish_date": "2022-08-20",
                "publish_status": "1",
                "weko_shared_id": -1,
                "item_1617186331708": {
                    "attribute_name": "Title",
                    "attribute_value_mlt": [
                        {
                            "subitem_1551255647225": "タイトル",
                            "subitem_1551255648112": "ja",
                        },
                        {
                            "subitem_1551255647225": "title",
                            "subitem_1551255648112": "en",
                        },
                    ],
                },
                "item_1617258105262": {
                    "attribute_name": "Resource Type",
                    "attribute_value_mlt": [
                        {
                            "resourceuri": "http://purl.org/coar/resource_type/c_5794",
                            "resourcetype": "conference paper",
                        }
                    ],
                },
                "relation_version_is_last": True,
                "item_1617605131499": {
                    "attribute_name": "File",
                    "attribute_type": "file",
                    "attribute_value_mlt": [
                        {
                            "url": {
                                "url": "https://weko3.example.org/record/{}/files/hello.txt".format(
                                    i
                                )
                            },
                            "date": [
                                {"dateType": "Available", "dateValue": "2022-09-07"}
                            ],
                            "format": "plain/text",
                            "filename": "hello.txt",
                            "filesize": [{"value": "146 KB"}],
                            "accessrole": "open_access",
                            "version_id": "",
                            "mimetype": "application/pdf",
                            "file": "",
                        }
                    ],
                },
            }

            item_data = {
                "id": "{}".format(i),
                "cnri": "cnricnricnri",
                "cnri_suffix_not_existed": "cnri_suffix_not_existed",
                "is_change_identifier": "is_change_identifier",
                "pid": {"type": "depid", "value": "{}".format(i), "revision_id": 0},
                "lang": "ja",
                "publish_status": "public",
                "owner": "1",
                "title": "title",
                "owners": [1],
                "item_type_id": 1,
                "status": "keep",
                "$schema": "/items/jsonschema/1",
                "item_title": "item_title",
                "metadata": record_data,
                "pubdate": "2022-08-20",
                "created_by": 1,
                "owners_ext": {
                    "email": "wekosoftware@nii.ac.jp",
                    "username": "",
                    "displayname": "",
                },
                "shared_user_id": -1,
                "item_1617186331708": [
                    {"subitem_1551255647225": "タイトル", "subitem_1551255648112": "ja"},
                    {"subitem_1551255647225": "title", "subitem_1551255648112": "en"},
                ],
                "item_1617258105262": {
                    "resourceuri": "http://purl.org/coar/resource_type/c_5794",
                    "resourcetype": "conference paper",
                },
            }

            rec_uuid = uuid.uuid4()

            recid = PersistentIdentifier.create(
                "recid",
                str(i),
                object_type="rec",
                object_uuid=rec_uuid,
                status=PIDStatus.REGISTERED,
            )
            depid = PersistentIdentifier.create(
                "depid",
                str(i),
                object_type="rec",
                object_uuid=rec_uuid,
                status=PIDStatus.REGISTERED,
            )
            rel = PIDRelation.create(recid, depid, 3)
            db.session.add(rel)
            parent = None
            doi = None
            parent = PersistentIdentifier.create(
                "parent",
                "parent:{}".format(i),
                object_type="rec",
                object_uuid=rec_uuid,
                status=PIDStatus.REGISTERED,
            )
            rel = PIDRelation.create(parent, recid, 2, 0)
            db.session.add(rel)
            if i % 2 == 1:
                doi = PersistentIdentifier.create(
                    "doi",
                    "https://doi.org/10.xyz/{}".format((str(i)).zfill(10)),
                    object_type="rec",
                    object_uuid=rec_uuid,
                    status=PIDStatus.REGISTERED,
                )
                hdl = PersistentIdentifier.create(
                    "hdl",
                    "https://hdl.handle.net/0000/{}".format((str(i)).zfill(10)),
                    object_type="rec",
                    object_uuid=rec_uuid,
                    status=PIDStatus.REGISTERED,
                )

            record = WekoRecord.create(record_data, id_=rec_uuid)
            # from six import BytesIO
            import base64

            from invenio_files_rest.models import Bucket
            from invenio_records_files.models import RecordsBuckets

            bucket = Bucket.create()
            record_buckets = RecordsBuckets.create(record=record.model, bucket=bucket)
            stream = BytesIO(b"Hello, World")
            # record.files['hello.txt'] = stream
            # obj=ObjectVersion.create(bucket=bucket.id, key='hello.txt', stream=stream)
            record["item_1617605131499"]["attribute_value_mlt"][0]["file"] = (
                base64.b64encode(stream.getvalue())
            ).decode("utf-8")
            deposit = WekoDeposit(record, record.model)
            deposit.commit()
            # record['item_1617605131499']['attribute_value_mlt'][0]['version_id'] = str(obj.version_id)
            record["item_1617605131499"]["attribute_value_mlt"][0]["version_id"] = "1"

            record_data["content"] = [
                {
                    "date": [{"dateValue": "2021-07-12", "dateType": "Available"}],
                    "accessrole": "open_access",
                    "displaytype": "simple",
                    "filename": "hello.txt",
                    "attachment": {},
                    "format": "text/plain",
                    "mimetype": "text/plain",
                    "filesize": [{"value": "1 KB"}],
                    "version_id": "{}".format("1"),
                    "url": {
                        "url": "http://localhost/record/{}/files/hello.txt".format(i)
                    },
                    "file": (base64.b64encode(stream.getvalue())).decode("utf-8"),
                }
            ]
            indexer.upload_metadata(record_data, rec_uuid, 1, False)
            item = ItemsMetadata.create(item_data, id_=rec_uuid)

            results.append(
                {
                    "depid": depid,
                    "recid": recid,
                    "parent": parent,
                    "doi": doi,
                    "hdl": hdl,
                    "record": record,
                    "record_data": record_data,
                    "item": item,
                    "item_data": item_data,
                    "deposit": deposit,
                }
            )

    sleep(3)
    es = Elasticsearch("http://{}:9200".format(app.config["SEARCH_ELASTIC_HOSTS"]))
    # print(es.cat.indices())
    return {"indexer": indexer, "results": results}


@pytest.fixture()
def indextree(client, users):
    from weko_index_tree.api import Indexes

    index_metadata = {
        "id": 1,
        "parent": 0,
        "value": "Index(public_state = True,harvest_public_state = True)",
    }

    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        ret = Indexes.create(0, index_metadata)
        index = Index.get_index_by_id(1)
        index.public_state = True
        index.harvest_public_state = True

    index_metadata = {
        "id": 2,
        "parent": 0,
        "value": "Index(public_state = True,harvest_public_state = False)",
    }

    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        Indexes.create(0, index_metadata)
        index = Index.get_index_by_id(2)
        index.public_state = True
        index.harvest_public_state = False

    index_metadata = {
        "id": 3,
        "parent": 0,
        "value": "Index(public_state = False,harvest_public_state = True)",
    }

    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        Indexes.create(0, index_metadata)
        index = Index.get_index_by_id(3)
        index.public_state = False
        index.harvest_public_state = True

    index_metadata = {
        "id": 4,
        "parent": 0,
        "value": "Index(public_state = False,harvest_public_state = False)",
    }

    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        Indexes.create(0, index_metadata)
        index = Index.get_index_by_id(4)
        index.public_state = False
        index.harvest_public_state = False


@pytest.fixture()
def doi_records(app, db, identifier, indextree, location, db_itemtype, db_oaischema):
    indexer = WekoIndexer()
    indexer.get_es_index()
    results = []
    with app.test_request_context():
        i = 1
        filename = "helloworld.pdf"
        mimetype = "application/pdf"
        filepath = "tests/data/helloworld.pdf"
        results.append(
            make_record(db, indexer, i, filepath, filename, mimetype, "xyz.jalc")
        )

        i = 2
        filename = "helloworld.docx"
        mimetype = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        filepath = "tests/data/helloworld.docx"
        results.append(
            make_record(db, indexer, i, filepath, filename, mimetype, "xyz.crossref")
        )

        i = 3
        filename = "helloworld.zip"
        mimetype = "application/zip"
        filepath = "tests/data/helloworld.zip"
        results.append(
            make_record(db, indexer, i, filepath, filename, mimetype, "xyz.datacite")
        )

        i = 4
        filename = "helloworld.pdf"
        mimetype = "application/pdf"
        filepath = "tests/data/helloworld.pdf"
        results.append(
            make_record(db, indexer, i, filepath, filename, mimetype, "xyz.ndl")
        )

        i = 5
        filename = "helloworld.pdf"
        mimetype = "application/pdf"
        filepath = "tests/data/helloworld.pdf"
        results.append(
            make_record(db, indexer, i, filepath, filename, mimetype)
        )

    return indexer, results


@pytest.fixture()
def es_item_file_pipeline(es):
    from elasticsearch.client.ingest import IngestClient

    p = IngestClient(current_search_client)
    p.put_pipeline(
        id="item-file-pipeline",
        body={
            "description": "Index contents of each file.",
            "processors": [
                {
                    "foreach": {
                        "field": "content",
                        "processor": {
                            "attachment": {
                                "indexed_chars": -1,
                                "target_field": "_ingest._value.attachment",
                                "field": "_ingest._value.file",
                                "properties": ["content"],
                            }
                        },
                    }
                },
                {
                    "foreach": {
                        "field": "content",
                        "processor": {"remove": {"field": "_ingest._value.file"}},
                    }
                },
            ],
        },
    )


@pytest.fixture()
def identifier(db):
    doi_identifier = Identifier(
        id=1,
        repository="Root Index",
        jalc_flag=True,
        jalc_crossref_flag=True,
        jalc_datacite_flag=True,
        ndl_jalc_flag=True,
        jalc_doi="xyz.jalc",
        jalc_crossref_doi="xyz.crossref",
        jalc_datacite_doi="xyz.datacite",
        ndl_jalc_doi="xyz.ndl",
        suffix="def",
        created_userId="1",
        created_date=datetime.strptime("2022-09-28 04:33:42", "%Y-%m-%d %H:%M:%S"),
        updated_userId="1",
        updated_date=datetime.strptime("2022-09-28 04:33:42", "%Y-%m-%d %H:%M:%S"),
    )
    db.session.add(doi_identifier)
    db.session.commit()
    return doi_identifier


def record_indexer_receiver(sender, json=None, record=None, index=None,
                            **kwargs):
    """Mock-receiver of a before_record_index signal."""
    if ES_VERSION[0] == 2:
        suggest_byyear = {}
        suggest_byyear['context'] = {
            'year': json['year']
        }
        suggest_byyear['input'] = [json['title'], ]
        suggest_byyear['output'] = json['title']
        suggest_byyear['payload'] = copy.deepcopy(json)

        suggest_title = {}
        suggest_title['input'] = [json['title'], ]
        suggest_title['output'] = json['title']
        suggest_title['payload'] = copy.deepcopy(json)

        json['suggest_byyear'] = suggest_byyear
        json['suggest_title'] = suggest_title

    elif ES_VERSION[0] >= 5:
        suggest_byyear = {}
        suggest_byyear['contexts'] = {
            'year': [str(json['year'])]
        }
        suggest_byyear['input'] = [json['title'], ]

        suggest_title = {}
        suggest_title['input'] = [json['title'], ]
        json['suggest_byyear'] = suggest_byyear
        json['suggest_title'] = suggest_title

    return json




@pytest.yield_fixture()
def es(app):
    """Elasticsearch fixture."""
    try:
        list(current_search.create())
    except RequestError:
        list(current_search.delete(ignore=[404]))
        list(current_search.create(ignore=[400]))
    current_search_client.indices.refresh()
    yield current_search_client
    list(current_search.delete(ignore=[404]))


@pytest.yield_fixture()
def indexer(app, es):
    """Create a record indexer."""
    InvenioIndexer(app)
    before_record_index.connect(record_indexer_receiver, sender=app)
    yield RecordIndexer()


def make_record(db, indexer, i, filepath, filename, mimetype, doi_prefix=None):
    record_data = {
        "_oai": {
            "id": "oai:weko3.example.org:000000{:02d}".format(i),
            "sets": ["{}".format((i % 2) + 1)],
        },
        "path": ["{}".format((i % 2) + 1)],
        "owner": "1",
        "recid": "{}".format(i),
        "title": [
            "ja_conference paperITEM00000009(public_open_access_open_access_simple)"
        ],
        "pubdate": {"attribute_name": "PubDate", "attribute_value": "2021-08-06"},
        "_buckets": {"deposit": "27202db8-aefc-4b85-b5ae-4921ac151ddf"},
        "_deposit": {
            "id": "{}".format(i),
            "pid": {"type": "depid", "value": "{}".format(i), "revision_id": 0},
            "owners": [1],
            "status": "published",
        },
        "item_title": "ja_conference paperITEM00000009(public_open_access_open_access_simple)",
        "author_link": ["4"],
        "item_type_id": "1",
        "publish_date": "2021-08-06",
        "publish_status": "0",
        "weko_shared_id": -1,
        "item_1617186331708": {
            "attribute_name": "Title",
            "attribute_value_mlt": [
                {
                    "subitem_1551255647225": "ja_conference paperITEM00000009(public_open_access_open_access_simple)",
                    "subitem_1551255648112": "ja",
                },
                {
                    "subitem_1551255647225": "en_conference paperITEM00000009(public_open_access_simple)",
                    "subitem_1551255648112": "en",
                },
            ],
        },
        "item_1617186385884": {
            "attribute_name": "Alternative Title",
            "attribute_value_mlt": [
                {
                    "subitem_1551255720400": "Alternative Title",
                    "subitem_1551255721061": "en",
                },
                {
                    "subitem_1551255720400": "Alternative Title",
                    "subitem_1551255721061": "ja",
                },
            ],
        },
        "item_1617186419668": {
            "attribute_name": "Creator",
            "attribute_type": "creator",
            "attribute_value_mlt": [
                {
                    "givenNames": [
                        {"givenName": "太郎", "givenNameLang": "ja"},
                        {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Taro", "givenNameLang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                    "creatorNames": [
                        {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                        {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                        {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                    ],
                    "nameIdentifiers": [
                        {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://orcid.org/",
                            "nameIdentifierScheme": "ORCID",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                            "nameIdentifierScheme": "CiNii",
                        },
                        {
                            "nameIdentifier": "zzzzzzz",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                            "nameIdentifierScheme": "KAKEN2",
                        },
                    ],
                    "creatorAffiliations": [
                        {
                            "affiliationNames": [
                                {
                                    "affiliationName": "University",
                                    "affiliationNameLang": "en",
                                }
                            ],
                            "affiliationNameIdentifiers": [
                                {
                                    "affiliationNameIdentifier": "0000000121691048",
                                    "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                    "affiliationNameIdentifierScheme": "ISNI",
                                }
                            ],
                        }
                    ],
                },
                {
                    "givenNames": [
                        {"givenName": "太郎", "givenNameLang": "ja"},
                        {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Taro", "givenNameLang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                    "creatorNames": [
                        {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                        {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                        {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                    ],
                    "nameIdentifiers": [
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://orcid.org/",
                            "nameIdentifierScheme": "ORCID",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                            "nameIdentifierScheme": "CiNii",
                        },
                        {
                            "nameIdentifier": "zzzzzzz",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                            "nameIdentifierScheme": "KAKEN2",
                        },
                    ],
                },
                {
                    "givenNames": [
                        {"givenName": "太郎", "givenNameLang": "ja"},
                        {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Taro", "givenNameLang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                    "creatorNames": [
                        {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                        {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                        {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                    ],
                    "nameIdentifiers": [
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://orcid.org/",
                            "nameIdentifierScheme": "ORCID",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                            "nameIdentifierScheme": "CiNii",
                        },
                        {
                            "nameIdentifier": "zzzzzzz",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                            "nameIdentifierScheme": "KAKEN2",
                        },
                    ],
                },
            ],
        },
        "item_1617186476635": {
            "attribute_name": "Access Rights",
            "attribute_value_mlt": [
                {
                    "subitem_1522299639480": "open access",
                    "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
                }
            ],
        },
        "item_1617186499011": {
            "attribute_name": "Rights",
            "attribute_value_mlt": [
                {
                    "subitem_1522650717957": "ja",
                    "subitem_1522650727486": "http://localhost",
                    "subitem_1522651041219": "Rights Information",
                }
            ],
        },
        "item_1617186609386": {
            "attribute_name": "Subject",
            "attribute_value_mlt": [
                {
                    "subitem_1522299896455": "ja",
                    "subitem_1522300014469": "Other",
                    "subitem_1522300048512": "http://localhost/",
                    "subitem_1523261968819": "Sibject1",
                }
            ],
        },
        "item_1617186626617": {
            "attribute_name": "Description",
            "attribute_value_mlt": [
                {
                    "subitem_description": "Description\nDescription<br/>Description",
                    "subitem_description_type": "Abstract",
                    "subitem_description_language": "en",
                },
                {
                    "subitem_description": "概要\n概要\n概要\n概要",
                    "subitem_description_type": "Abstract",
                    "subitem_description_language": "ja",
                },
            ],
        },
        "item_1617186643794": {
            "attribute_name": "Publisher",
            "attribute_value_mlt": [
                {"subitem_1522300295150": "en", "subitem_1522300316516": "Publisher"}
            ],
        },
        "item_1617186660861": {
            "attribute_name": "Date",
            "attribute_value_mlt": [
                {
                    "subitem_1522300695726": "Available",
                    "subitem_1522300722591": "2021-06-30",
                }
            ],
        },
        "item_1617186702042": {
            "attribute_name": "Language",
            "attribute_value_mlt": [{"subitem_1551255818386": "jpn"}],
        },
        "item_1617186783814": {
            "attribute_name": "Identifier",
            "attribute_value_mlt": [
                {
                    "subitem_identifier_uri": "http://localhost",
                    "subitem_identifier_type": "URI",
                }
            ],
        },
        "item_1617186859717": {
            "attribute_name": "Temporal",
            "attribute_value_mlt": [
                {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
            ],
        },
        "item_1617186882738": {
            "attribute_name": "Geo Location",
            "attribute_value_mlt": [
                {
                    "subitem_geolocation_place": [
                        {"subitem_geolocation_place_text": "Japan"}
                    ]
                }
            ],
        },
        "item_1617186901218": {
            "attribute_name": "Funding Reference",
            "attribute_value_mlt": [
                {
                    "subitem_1522399143519": {
                        "subitem_1522399281603": "ISNI",
                        "subitem_1522399333375": "http://xxx",
                    },
                    "subitem_1522399412622": [
                        {
                            "subitem_1522399416691": "en",
                            "subitem_1522737543681": "Funder Name",
                        }
                    ],
                    "subitem_1522399571623": {
                        "subitem_1522399585738": "Award URI",
                        "subitem_1522399628911": "Award Number",
                    },
                    "subitem_1522399651758": [
                        {
                            "subitem_1522721910626": "en",
                            "subitem_1522721929892": "Award Title",
                        }
                    ],
                }
            ],
        },
        "item_1617186920753": {
            "attribute_name": "Source Identifier",
            "attribute_value_mlt": [
                {
                    "subitem_1522646500366": "ISSN",
                    "subitem_1522646572813": "xxxx-xxxx-xxxx",
                }
            ],
        },
        "item_1617186941041": {
            "attribute_name": "Source Title",
            "attribute_value_mlt": [
                {"subitem_1522650068558": "en", "subitem_1522650091861": "Source Title"}
            ],
        },
        "item_1617186959569": {
            "attribute_name": "Volume Number",
            "attribute_value_mlt": [{"subitem_1551256328147": "1"}],
        },
        "item_1617186981471": {
            "attribute_name": "Issue Number",
            "attribute_value_mlt": [{"subitem_1551256294723": "111"}],
        },
        "item_1617186994930": {
            "attribute_name": "Number of Pages",
            "attribute_value_mlt": [{"subitem_1551256248092": "12"}],
        },
        "item_1617187024783": {
            "attribute_name": "Page Start",
            "attribute_value_mlt": [{"subitem_1551256198917": "1"}],
        },
        "item_1617187045071": {
            "attribute_name": "Page End",
            "attribute_value_mlt": [{"subitem_1551256185532": "3"}],
        },
        "item_1617187112279": {
            "attribute_name": "Degree Name",
            "attribute_value_mlt": [
                {"subitem_1551256126428": "Degree Name", "subitem_1551256129013": "en"}
            ],
        },
        "item_1617187136212": {
            "attribute_name": "Date Granted",
            "attribute_value_mlt": [{"subitem_1551256096004": "2021-06-30"}],
        },
        "item_1617187187528": {
            "attribute_name": "Conference",
            "attribute_value_mlt": [
                {
                    "subitem_1599711633003": [
                        {
                            "subitem_1599711636923": "Conference Name",
                            "subitem_1599711645590": "ja",
                        }
                    ],
                    "subitem_1599711655652": "1",
                    "subitem_1599711660052": [
                        {
                            "subitem_1599711680082": "Sponsor",
                            "subitem_1599711686511": "ja",
                        }
                    ],
                    "subitem_1599711699392": {
                        "subitem_1599711704251": "2020/12/11",
                        "subitem_1599711712451": "1",
                        "subitem_1599711727603": "12",
                        "subitem_1599711731891": "2000",
                        "subitem_1599711735410": "1",
                        "subitem_1599711739022": "12",
                        "subitem_1599711743722": "2020",
                        "subitem_1599711745532": "ja",
                    },
                    "subitem_1599711758470": [
                        {
                            "subitem_1599711769260": "Conference Venue",
                            "subitem_1599711775943": "ja",
                        }
                    ],
                    "subitem_1599711788485": [
                        {
                            "subitem_1599711798761": "Conference Place",
                            "subitem_1599711803382": "ja",
                        }
                    ],
                    "subitem_1599711813532": "JPN",
                }
            ],
        },
        "item_1617258105262": {
            "attribute_name": "Resource Type",
            "attribute_value_mlt": [
                {
                    "resourceuri": "http://purl.org/coar/resource_type/c_5794",
                    "resourcetype": "conference paper",
                }
            ],
        },
        "item_1617265215918": {
            "attribute_name": "Version Type",
            "attribute_value_mlt": [
                {
                    "subitem_1522305645492": "AO",
                    "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
                }
            ],
        },
        "item_1617349709064": {
            "attribute_name": "Contributor",
            "attribute_value_mlt": [
                {
                    "givenNames": [
                        {"givenName": "太郎", "givenNameLang": "ja"},
                        {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                        {"givenName": "Taro", "givenNameLang": "en"},
                    ],
                    "familyNames": [
                        {"familyName": "情報", "familyNameLang": "ja"},
                        {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                        {"familyName": "Joho", "familyNameLang": "en"},
                    ],
                    "contributorType": "ContactPerson",
                    "nameIdentifiers": [
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://orcid.org/",
                            "nameIdentifierScheme": "ORCID",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://ci.nii.ac.jp/",
                            "nameIdentifierScheme": "CiNii",
                        },
                        {
                            "nameIdentifier": "xxxxxxx",
                            "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                            "nameIdentifierScheme": "KAKEN2",
                        },
                    ],
                    "contributorMails": [{"contributorMail": "wekosoftware@nii.ac.jp"}],
                    "contributorNames": [
                        {"lang": "ja", "contributorName": "情報, 太郎"},
                        {"lang": "ja-Kana", "contributorName": "ジョウホウ, タロウ"},
                        {"lang": "en", "contributorName": "Joho, Taro"},
                    ],
                }
            ],
        },
        "item_1617349808926": {
            "attribute_name": "Version",
            "attribute_value_mlt": [{"subitem_1523263171732": "Version"}],
        },
        "item_1617351524846": {
            "attribute_name": "APC",
            "attribute_value_mlt": [{"subitem_1523260933860": "Unknown"}],
        },
        "item_1617353299429": {
            "attribute_name": "Relation",
            "attribute_value_mlt": [
                {
                    "subitem_1522306207484": "isVersionOf",
                    "subitem_1522306287251": {
                        "subitem_1522306382014": "arXiv",
                        "subitem_1522306436033": "xxxxx",
                    },
                    "subitem_1523320863692": [
                        {
                            "subitem_1523320867455": "en",
                            "subitem_1523320909613": "Related Title",
                        }
                    ],
                }
            ],
        },
        "item_1617605131499": {
            "attribute_name": "File",
            "attribute_type": "file",
            "attribute_value_mlt": [
                {
                    "url": {
                        "url": "https://weko3.example.org/record/{0}/files/{1}".format(
                            i, filename
                        )
                    },
                    "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                    "format": "text/plain",
                    "filename": "{}".format(filename),
                    "filesize": [{"value": "1 KB"}],
                    "mimetype": "{}".format(mimetype),
                    "accessrole": "open_access",
                    "version_id": "c1502853-c2f9-455d-8bec-f6e630e54b21",
                    "displaytype": "simple",
                }
            ],
        },
        "item_1617610673286": {
            "attribute_name": "Rights Holder",
            "attribute_value_mlt": [
                {
                    "nameIdentifiers": [
                        {
                            "nameIdentifier": "xxxxxx",
                            "nameIdentifierURI": "https://orcid.org/",
                            "nameIdentifierScheme": "ORCID",
                        }
                    ],
                    "rightHolderNames": [
                        {
                            "rightHolderName": "Right Holder Name",
                            "rightHolderLanguage": "ja",
                        }
                    ],
                }
            ],
        },
        "item_1617620223087": {
            "attribute_name": "Heading",
            "attribute_value_mlt": [
                {
                    "subitem_1565671149650": "ja",
                    "subitem_1565671169640": "Banner Headline",
                    "subitem_1565671178623": "Subheading",
                },
                {
                    "subitem_1565671149650": "en",
                    "subitem_1565671169640": "Banner Headline",
                    "subitem_1565671178623": "Subheding",
                },
            ],
        },
        "item_1617944105607": {
            "attribute_name": "Degree Grantor",
            "attribute_value_mlt": [
                {
                    "subitem_1551256015892": [
                        {
                            "subitem_1551256027296": "xxxxxx",
                            "subitem_1551256029891": "kakenhi",
                        }
                    ],
                    "subitem_1551256037922": [
                        {
                            "subitem_1551256042287": "Degree Grantor Name",
                            "subitem_1551256047619": "en",
                        }
                    ],
                }
            ],
        },
        "relation_version_is_last": True,
    }

    item_data = {
        "id": "{}".format(i),
        "pid": {"type": "recid", "value": "{}".format(i), "revision_id": 0},
        "path": ["{}".format((i % 2) + 1)],
        "owner": "1",
        "title": "ja_conference paperITEM00000009(public_open_access_open_access_simple)",
        "owners": [1],
        "status": "draft",
        "$schema": "https://localhost:8443/items/jsonschema/1",
        "pubdate": "2021-08-06",
        "feedback_mail_list": [{"email": "wekosoftware@nii.ac.jp", "author_id": ""}],
        "item_1617186331708": [
            {
                "subitem_1551255647225": "ja_conference paperITEM00000009(public_open_access_open_access_simple)",
                "subitem_1551255648112": "ja",
            },
            {
                "subitem_1551255647225": "en_conference paperITEM00000009(public_open_access_simple)",
                "subitem_1551255648112": "en",
            },
        ],
        "item_1617186385884": [
            {
                "subitem_1551255720400": "Alternative Title",
                "subitem_1551255721061": "en",
            },
            {
                "subitem_1551255720400": "Alternative Title",
                "subitem_1551255721061": "ja",
            },
        ],
        "item_1617186419668": [
            {
                "givenNames": [
                    {"givenName": "太郎", "givenNameLang": "ja"},
                    {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                    {"givenName": "Taro", "givenNameLang": "en"},
                ],
                "familyNames": [
                    {"familyName": "情報", "familyNameLang": "ja"},
                    {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                    {"familyName": "Joho", "familyNameLang": "en"},
                ],
                "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                "creatorNames": [
                    {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                    {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                    {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                ],
                "nameIdentifiers": [
                    {"nameIdentifier": "4", "nameIdentifierScheme": "WEKO"},
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://orcid.org/",
                        "nameIdentifierScheme": "ORCID",
                    },
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://ci.nii.ac.jp/",
                        "nameIdentifierScheme": "CiNii",
                    },
                    {
                        "nameIdentifier": "zzzzzzz",
                        "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                        "nameIdentifierScheme": "KAKEN2",
                    },
                ],
                "creatorAffiliations": [
                    {
                        "affiliationNames": [
                            {
                                "affiliationName": "University",
                                "affiliationNameLang": "en",
                            }
                        ],
                        "affiliationNameIdentifiers": [
                            {
                                "affiliationNameIdentifier": "0000000121691048",
                                "affiliationNameIdentifierURI": "http://isni.org/isni/0000000121691048",
                                "affiliationNameIdentifierScheme": "ISNI",
                            }
                        ],
                    }
                ],
            },
            {
                "givenNames": [
                    {"givenName": "太郎", "givenNameLang": "ja"},
                    {"givenName": "タロ", "givenNameLang": "ja-Kana"},
                    {"givenName": "Taro", "givenNameLang": "en"},
                ],
                "familyNames": [
                    {"familyName": "情報", "familyNameLang": "ja"},
                    {"familyName": "ジウホウ", "familyNameLang": "ja-Kana"},
                    {"familyName": "Joho", "familyNameLang": "en"},
                ],
                "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                "creatorNames": [
                    {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                    {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                    {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                ],
                "nameIdentifiers": [
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://orcid.org/",
                        "nameIdentifierScheme": "ORCID",
                    },
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://ci.nii.ac.jp/",
                        "nameIdentifierScheme": "CiNii",
                    },
                    {
                        "nameIdentifier": "zzzzzzz",
                        "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                        "nameIdentifierScheme": "KAKEN2",
                    },
                ],
            },
            {
                "givenNames": [
                    {"givenName": "太郎", "givenNameLang": "ja"},
                    {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                    {"givenName": "Taro", "givenNameLang": "en"},
                ],
                "familyNames": [
                    {"familyName": "情報", "familyNameLang": "ja"},
                    {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                    {"familyName": "Joho", "familyNameLang": "en"},
                ],
                "creatorMails": [{"creatorMail": "wekosoftware@nii.ac.jp"}],
                "creatorNames": [
                    {"creatorName": "情報, 太郎", "creatorNameLang": "ja"},
                    {"creatorName": "ジョウホウ, タロウ", "creatorNameLang": "ja-Kana"},
                    {"creatorName": "Joho, Taro", "creatorNameLang": "en"},
                ],
                "nameIdentifiers": [
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://orcid.org/",
                        "nameIdentifierScheme": "ORCID",
                    },
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://ci.nii.ac.jp/",
                        "nameIdentifierScheme": "CiNii",
                    },
                    {
                        "nameIdentifier": "zzzzzzz",
                        "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                        "nameIdentifierScheme": "KAKEN2",
                    },
                ],
            },
        ],
        "item_1617186476635": {
            "subitem_1522299639480": "open access",
            "subitem_1600958577026": "http://purl.org/coar/access_right/c_abf2",
        },
        "item_1617186499011": [
            {
                "subitem_1522650717957": "ja",
                "subitem_1522650727486": "http://localhost",
                "subitem_1522651041219": "Rights Information",
            }
        ],
        "item_1617186609386": [
            {
                "subitem_1522299896455": "ja",
                "subitem_1522300014469": "Other",
                "subitem_1522300048512": "http://localhost/",
                "subitem_1523261968819": "Sibject1",
            }
        ],
        "item_1617186626617": [
            {
                "subitem_description": "Description\nDescription<br/>Description",
                "subitem_description_type": "Abstract",
                "subitem_description_language": "en",
            },
            {
                "subitem_description": "概要\n概要\n概要\n概要",
                "subitem_description_type": "Abstract",
                "subitem_description_language": "ja",
            },
        ],
        "item_1617186643794": [
            {"subitem_1522300295150": "en", "subitem_1522300316516": "Publisher"}
        ],
        "item_1617186660861": [
            {
                "subitem_1522300695726": "Available",
                "subitem_1522300722591": "2021-06-30",
            }
        ],
        "item_1617186702042": [{"subitem_1551255818386": "jpn"}],
        "item_1617186783814": [
            {
                "subitem_identifier_uri": "http://localhost",
                "subitem_identifier_type": "URI",
            }
        ],
        "item_1617186859717": [
            {"subitem_1522658018441": "en", "subitem_1522658031721": "Temporal"}
        ],
        "item_1617186882738": [
            {"subitem_geolocation_place": [{"subitem_geolocation_place_text": "Japan"}]}
        ],
        "item_1617186901218": [
            {
                "subitem_1522399143519": {
                    "subitem_1522399281603": "ISNI",
                    "subitem_1522399333375": "http://xxx",
                },
                "subitem_1522399412622": [
                    {
                        "subitem_1522399416691": "en",
                        "subitem_1522737543681": "Funder Name",
                    }
                ],
                "subitem_1522399571623": {
                    "subitem_1522399585738": "Award URI",
                    "subitem_1522399628911": "Award Number",
                },
                "subitem_1522399651758": [
                    {
                        "subitem_1522721910626": "en",
                        "subitem_1522721929892": "Award Title",
                    }
                ],
            }
        ],
        "item_1617186920753": [
            {"subitem_1522646500366": "ISSN", "subitem_1522646572813": "xxxx-xxxx-xxxx"}
        ],
        "item_1617186941041": [
            {"subitem_1522650068558": "en", "subitem_1522650091861": "Source Title"}
        ],
        "item_1617186959569": {"subitem_1551256328147": "1"},
        "item_1617186981471": {"subitem_1551256294723": "111"},
        "item_1617186994930": {"subitem_1551256248092": "12"},
        "item_1617187024783": {"subitem_1551256198917": "1"},
        "item_1617187045071": {"subitem_1551256185532": "3"},
        "item_1617187112279": [
            {"subitem_1551256126428": "Degree Name", "subitem_1551256129013": "en"}
        ],
        "item_1617187136212": {"subitem_1551256096004": "2021-06-30"},
        "item_1617187187528": [
            {
                "subitem_1599711633003": [
                    {
                        "subitem_1599711636923": "Conference Name",
                        "subitem_1599711645590": "ja",
                    }
                ],
                "subitem_1599711655652": "1",
                "subitem_1599711660052": [
                    {"subitem_1599711680082": "Sponsor", "subitem_1599711686511": "ja"}
                ],
                "subitem_1599711699392": {
                    "subitem_1599711704251": "2020/12/11",
                    "subitem_1599711712451": "1",
                    "subitem_1599711727603": "12",
                    "subitem_1599711731891": "2000",
                    "subitem_1599711735410": "1",
                    "subitem_1599711739022": "12",
                    "subitem_1599711743722": "2020",
                    "subitem_1599711745532": "ja",
                },
                "subitem_1599711758470": [
                    {
                        "subitem_1599711769260": "Conference Venue",
                        "subitem_1599711775943": "ja",
                    }
                ],
                "subitem_1599711788485": [
                    {
                        "subitem_1599711798761": "Conference Place",
                        "subitem_1599711803382": "ja",
                    }
                ],
                "subitem_1599711813532": "JPN",
            }
        ],
        "item_1617258105262": {
            "resourceuri": "http://purl.org/coar/resource_type/c_5794",
            "resourcetype": "conference paper",
        },
        "item_1617265215918": {
            "subitem_1522305645492": "AO",
            "subitem_1600292170262": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
        },
        "item_1617349709064": [
            {
                "givenNames": [
                    {"givenName": "太郎", "givenNameLang": "ja"},
                    {"givenName": "タロウ", "givenNameLang": "ja-Kana"},
                    {"givenName": "Taro", "givenNameLang": "en"},
                ],
                "familyNames": [
                    {"familyName": "情報", "familyNameLang": "ja"},
                    {"familyName": "ジョウホウ", "familyNameLang": "ja-Kana"},
                    {"familyName": "Joho", "familyNameLang": "en"},
                ],
                "contributorType": "ContactPerson",
                "nameIdentifiers": [
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://orcid.org/",
                        "nameIdentifierScheme": "ORCID",
                    },
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://ci.nii.ac.jp/",
                        "nameIdentifierScheme": "CiNii",
                    },
                    {
                        "nameIdentifier": "xxxxxxx",
                        "nameIdentifierURI": "https://kaken.nii.ac.jp/",
                        "nameIdentifierScheme": "KAKEN2",
                    },
                ],
                "contributorMails": [{"contributorMail": "wekosoftware@nii.ac.jp"}],
                "contributorNames": [
                    {"lang": "ja", "contributorName": "情報, 太郎"},
                    {"lang": "ja-Kana", "contributorName": "ジョウホ, タロウ"},
                    {"lang": "en", "contributorName": "Joho, Taro"},
                ],
            }
        ],
        "item_1617349808926": {"subitem_1523263171732": "Version"},
        "item_1617351524846": {"subitem_1523260933860": "Unknown"},
        "item_1617353299429": [
            {
                "subitem_1522306207484": "isVersionOf",
                "subitem_1522306287251": {
                    "subitem_1522306382014": "arXiv",
                    "subitem_1522306436033": "xxxxx",
                },
                "subitem_1523320863692": [
                    {
                        "subitem_1523320867455": "en",
                        "subitem_1523320909613": "Related Title",
                    }
                ],
            }
        ],
        "item_1617605131499": [
            {
                "url": {
                    "url": "https://weko3.example.org/record/{0}/files/{1}".format(
                        i, filename
                    )
                },
                "date": [{"dateType": "Available", "dateValue": "2021-07-12"}],
                "format": "{}".format(mimetype),
                "filename": "{}".format(filename),
                "filesize": [{"value": "1 KB"}],
                "mimetype": "{}".format(mimetype),
                "accessrole": "open_access",
                "version_id": "c1502853-c2f9-455d-8bec-f6e630e54b21",
                "displaytype": "simple",
            }
        ],
        "item_1617610673286": [
            {
                "nameIdentifiers": [
                    {
                        "nameIdentifier": "xxxxxx",
                        "nameIdentifierURI": "https://orcid.org/",
                        "nameIdentifierScheme": "ORCID",
                    }
                ],
                "rightHolderNames": [
                    {
                        "rightHolderName": "Right Holder Name",
                        "rightHolderLanguage": "ja",
                    }
                ],
            }
        ],
        "item_1617620223087": [
            {
                "subitem_1565671149650": "ja",
                "subitem_1565671169640": "Banner Headline",
                "subitem_1565671178623": "Subheading",
            },
            {
                "subitem_1565671149650": "en",
                "subitem_1565671169640": "Banner Headline",
                "subitem_1565671178623": "Subheding",
            },
        ],
        "item_1617944105607": [
            {
                "subitem_1551256015892": [
                    {
                        "subitem_1551256027296": "xxxxxx",
                        "subitem_1551256029891": "kakenhi",
                    }
                ],
                "subitem_1551256037922": [
                    {
                        "subitem_1551256042287": "Degree Grantor Name",
                        "subitem_1551256047619": "en",
                    }
                ],
            }
        ],
    }

    rec_uuid = uuid.uuid4()

    recid = PersistentIdentifier.create(
        "recid",
        str(i),
        object_type="rec",
        object_uuid=rec_uuid,
        status=PIDStatus.REGISTERED,
    )
    depid = PersistentIdentifier.create(
        "depid",
        str(i),
        object_type="rec",
        object_uuid=rec_uuid,
        status=PIDStatus.REGISTERED,
    )
    parent = None
    doi = None
    hdl = None
    recid_v1 = PersistentIdentifier.create(
        "recid",
        str(i + 0.1),
        object_type="rec",
        object_uuid=rec_uuid,
        status=PIDStatus.REGISTERED,
    )
    rec_uuid2 = uuid.uuid4()
    depid_v1 = PersistentIdentifier.create(
        "depid",
        str(i + 0.1),
        object_type="rec",
        object_uuid=rec_uuid2,
        status=PIDStatus.REGISTERED,
    )
    parent = PersistentIdentifier.create(
        "parent",
        "parent:{}".format(i),
        object_type="rec",
        object_uuid=rec_uuid2,
        status=PIDStatus.REGISTERED,
    )

    h1 = PIDVersioning(parent=parent)
    h1.insert_child(child=recid)
    h1.insert_child(child=recid_v1)
    RecordDraft.link(recid, depid)
    RecordDraft.link(recid_v1, depid_v1)

    if doi_prefix and len(doi_prefix):
        doi = PersistentIdentifier.create(
            "doi",
            "https://doi.org/{0}/{1}".format(doi_prefix, (str(i)).zfill(10)),
            object_type="rec",
            object_uuid=rec_uuid,
            status=PIDStatus.REGISTERED,
        )
        hdl = PersistentIdentifier.create(
            "hdl",
            "https://hdl.handle.net/0000/{}".format((str(i)).zfill(10)),
            object_type="rec",
            object_uuid=rec_uuid,
            status=PIDStatus.REGISTERED,
        )

    record = WekoRecord.create(record_data, id_=rec_uuid)
    # from six import BytesIO
    import base64

    bucket = Bucket.create()
    record_buckets = RecordsBuckets.create(record=record.model, bucket=bucket)

    # stream = BytesIO(b"Hello, World")
    obj = None
    with open(filepath, "rb") as f:
        stream = BytesIO(f.read())
        record.files[filename] = stream
        record["item_1617605131499"]["attribute_value_mlt"][0]["file"] = (
            base64.b64encode(stream.getvalue())
        ).decode("utf-8")
    with open(filepath, "rb") as f:
        obj = ObjectVersion.create(bucket=bucket.id, key=filename, stream=f)
    deposit = aWekoDeposit(record, record.model)
    deposit.commit()
    record["item_1617605131499"]["attribute_value_mlt"][0]["version_id"] = str(
        obj.version_id
    )

    record_data["content"] = [
        {
            "date": [{"dateValue": "2021-07-12", "dateType": "Available"}],
            "accessrole": "open_access",
            "displaytype": "simple",
            "filename": filename,
            "attachment": {},
            "format": mimetype,
            "mimetype": mimetype,
            "filesize": [{"value": "1 KB"}],
            "version_id": "{}".format(obj.version_id),
            "url": {"url": "http://localhost/record/{0}/files/{1}".format(i, filename)},
            "file": (base64.b64encode(stream.getvalue())).decode("utf-8"),
        }
    ]
    indexer.upload_metadata(record_data, rec_uuid, 1, False)
    item = ItemsMetadata.create(item_data, id_=rec_uuid, item_type_id=1)

    record_v1 = WekoRecord.create(record_data, id_=rec_uuid2)
    # from six import BytesIO
    import base64

    bucket_v1 = Bucket.create()
    record_buckets = RecordsBuckets.create(record=record_v1.model, bucket=bucket_v1)
    # stream = BytesIO(b"Hello, World")
    record_v1.files[filename] = stream
    obj_v1 = ObjectVersion.create(bucket=bucket_v1.id, key=filename, stream=stream)
    record_v1["item_1617605131499"]["attribute_value_mlt"][0]["file"] = (
        base64.b64encode(stream.getvalue())
    ).decode("utf-8")
    deposit_v1 = aWekoDeposit(record_v1, record_v1.model)
    deposit_v1.commit()
    record_v1["item_1617605131499"]["attribute_value_mlt"][0]["version_id"] = str(
        obj_v1.version_id
    )

    record_data_v1 = copy.deepcopy(record_data)
    record_data_v1["content"] = [
        {
            "date": [{"dateValue": "2021-07-12", "dateType": "Available"}],
            "accessrole": "open_access",
            "displaytype": "simple",
            "filename": filename,
            "attachment": {},
            "format": mimetype,
            "mimetype": mimetype,
            "filesize": [{"value": "1 KB"}],
            "version_id": "{}".format(obj_v1.version_id),
            "url": {"url": "http://localhost/record/{0}/files/{1}".format(i, filename)},
            "file": (base64.b64encode(stream.getvalue())).decode("utf-8"),
        }
    ]
    indexer.upload_metadata(record_data_v1, rec_uuid2, 1, False)
    item_v1 = ItemsMetadata.create(item_data, id_=rec_uuid2, item_type_id=1)

    return {
        "depid": depid,
        "recid": recid,
        "parent": parent,
        "doi": doi,
        "hdl": hdl,
        "record": record,
        "record_data": record_data,
        "item": item,
        "item_data": item_data,
        "deposit": deposit,
        "filename": filename,
        "mimetype": mimetype,
        "obj": obj,
    }

@pytest.fixture
def make_itemtype(app,db):
    def factory(id,datas):
        result = dict()
        item_type_name = ItemTypeName(
            name=datas["name"],has_site_license=True,is_active=True
        )
        item_type_schema=dict()
        with open(datas["schema"],"r") as f:
            item_type_schema = json.load(f)
        item_type_form = dict()
        with open(datas["form"], "r") as f:
            item_type_form = json.load(f)

        item_type_render = dict()
        with open(datas["render"], "r") as f:
            item_type_render = json.load(f)

        with db.session.begin_nested():
            db.session.add(item_type_name)


        item_type = ItemType(
            name_id=item_type_name.id,
            harvesting_type=True,
            schema=item_type_schema,
            form=item_type_form,
            render=item_type_render,
            tag=1,
            version_id=1,
            is_deleted=False,
        )

        if "mapping" in datas:
            item_type_mapping = dict()
            with open(datas["mapping"], "r") as f:
                item_type_mapping = json.load(f)
            item_type_mapping = ItemTypeMapping(id=id, item_type_id=id, mapping=item_type_mapping)
            db.session.add(item_type_mapping)
            result["item_type_mapping"] = item_type_mapping
        with db.session.begin_nested():
            db.session.add(item_type)

        db.session.commit()
        result["item_type_name"] = item_type_name
        result["item_type"] = item_type

        return result
    return factory

@pytest.fixture()
def create_export_all_data(db):
    indexer = WekoIndexer()
    indexer.get_es_index()
    filepath = "tests/data/helloworld.pdf"
    filename = "helloworld.pdf"
    mimetype = "application/pdf"
    uuid_list = db.session.query(PersistentIdentifier.object_uuid).distinct(PersistentIdentifier.object_uuid).all()
    uuid_list = [uuid[0] for uuid in uuid_list]
    item_meta_data_list = ItemMetadata.query.filter(ItemMetadata.id.in_(uuid_list)).all()
    for meta in item_meta_data_list:
        meta.item_type_id = 1
        db.session.merge(meta)
    for i in range(1000, 1110):
        make_record(db, indexer, i, filepath, filename, mimetype, '')

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
def db_itemtype_jpcoar(app, db):
    # Multiple
    item_type_multiple_name = ItemTypeName(
        id=10, name="Multiple", has_site_license=True, is_active=True
    )
    item_type_multiple_schema = dict()
    with open("tests/data/jpcoar/v2/itemtype_multiple_schema.json", "r") as f:
        item_type_multiple_schema = json.load(f)

    item_type_multiple_form = dict()
    with open("tests/data/jpcoar/v2/itemtype_multiple_form.json", "r") as f:
        item_type_multiple_form = json.load(f)

    item_type_multiple_render = dict()
    with open("tests/data/jpcoar/v2/itemtype_multiple_render.json", "r") as f:
        item_type_multiple_render = json.load(f)

    item_type_multiple_mapping = dict()
    with open("tests/data/jpcoar/v2/itemtype_multiple_mapping.json", "r") as f:
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

    with db.session.begin_nested():
        db.session.add(item_type_multiple_name)
        db.session.add(item_type_multiple)
        db.session.add(item_type_multiple_mapping)
    db.session.commit()

    return {
        "item_type_multiple_name": item_type_multiple_name,
        "item_type_multiple": item_type_multiple,
        "item_type_multiple_mapping": item_type_multiple_mapping,
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

@pytest.fixture()
def mapper_jpcoar(db_itemtype_jpcoar):
    def factory(type):
        xml_str = ''
        with open('tests/data/jpcoar/v2/test_base.xml', 'r', encoding='utf-8') as xml_file:
            xml_str = xml_file.read()
        self_json = xmltodict.parse(xml_str)
        tags = self_json["jpcoar:jpcoar"]
        item_type = ItemType.query.filter_by(id=10).first()
        item_type_mapping = Mapping.get_record(item_type.id)
        item_map = get_full_mapping(item_type_mapping, "jpcoar_mapping")
        res = {"$schema":item_type.id,"pubdate": date.today()}

        if not isinstance(tags[type],list):
            metadata = [tags[type]]
        else:
            metadata = tags[type]
        return item_type.schema.get("properties"),item_map,res,metadata
    return factory

@pytest.fixture()
def db_rocrate_mapping(db):
    item_type_name = ItemTypeName(id=40001, name='test item type', has_site_license=True, is_active=True)
    with db.session.begin_nested():
        db.session.add(item_type_name)
    db.session.commit()

    item_type = ItemType(
        id=40001,
        name_id=40001,
        harvesting_type=True,
        schema={'type': 'test schema'},
        form={'type': 'test form'},
        render={'type': 'test render'},
        tag=1,
        version_id=1,
        is_deleted=False,
    )

    with db.session.begin_nested():
        db.session.add(item_type)
    db.session.commit()

    with open('tests/data/rocrate/rocrate_mapping.json', 'r') as f:
        mapping = json.load(f)
    rocrate_mapping = RocrateMapping(item_type_id=40001, mapping=mapping)

    with db.session.begin_nested():
        db.session.add(rocrate_mapping)
    db.session.commit()
