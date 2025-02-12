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

"""Module of weko-workflow utils."""

import base64
import json
import os
from collections import OrderedDict
from copy import deepcopy
from datetime import datetime, timedelta
from typing import List, NoReturn, Optional, Tuple, Union
import traceback

import redis
from redis import sentinel
from celery.task.control import inspect
from flask import current_app, request, session
from flask_babelex import gettext as _
from flask_security import current_user
from invenio_accounts.models import Role, User, userrole
from invenio_cache import current_cache
from invenio_db import db
from invenio_files_rest.models import Bucket, ObjectVersion
from invenio_i18n.ext import current_i18n
from invenio_mail.admin import MailSettingView
from invenio_mail.models import MailConfig
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidrelations.models import PIDRelation
from invenio_pidstore.models import PersistentIdentifier, \
    PIDDoesNotExistError, PIDStatus
from invenio_pidstore.resolver import Resolver
from invenio_records.models import RecordMetadata
from invenio_records_files.models import RecordsBuckets
from passlib.handlers.oracle import oracle10
from simplekv.memory.redisstore import RedisStore
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound
from weko_admin.models import Identifier, SiteInfo
from weko_admin.utils import get_restricted_access
from weko_deposit.api import WekoDeposit, WekoRecord
from weko_handle.api import Handle
from weko_records.api import FeedbackMailList, ItemsMetadata, ItemTypeNames, \
    ItemTypes, Mapping
from weko_records.models import ItemType
from weko_records.serializers.utils import get_full_mapping, get_item_type_name
from weko_records_ui.models import FilePermission
from weko_redis import RedisConnection
from weko_user_profiles.config import \
    WEKO_USERPROFILES_INSTITUTE_POSITION_LIST, \
    WEKO_USERPROFILES_POSITION_LIST
from weko_user_profiles.utils import get_user_profile_info
from werkzeug.utils import import_string
from weko_deposit.pidstore import get_record_without_version

from weko_workflow.config import IDENTIFIER_GRANT_LIST, \
    IDENTIFIER_GRANT_SUFFIX_METHOD, \
    WEKO_WORKFLOW_USAGE_APPLICATION_ITEM_TYPES_LIST, \
    WEKO_WORKFLOW_USAGE_REPORT_ITEM_TYPES_LIST


from .api import GetCommunity, UpdateItem, WorkActivity, WorkActivityHistory, \
    WorkFlow , Flow
from .config import DOI_VALIDATION_INFO, DOI_VALIDATION_INFO_CROSSREF, DOI_VALIDATION_INFO_DATACITE, IDENTIFIER_GRANT_SELECT_DICT, \
    WEKO_SERVER_CNRI_HOST_LINK
from .models import Action as _Action, Activity
from .models import ActionStatusPolicy, ActivityStatusPolicy, GuestActivity,FlowAction
from .models import WorkFlow as _WorkFlow


# 2.1.2.1 デフォルト絞込み条件取得処理
def get_workspace_filterCon():


    return None

# 2.1.2.2 ESからアイテム一覧取得処理
def get_es_itemlist():

    return None


# 2.1.2.3 お気に入り既読未読ステータス取得処理
def get_workspace_status_management(recid):

    return None

# 2.1.2.4 アクセス数取得処理
def get_access_cnt(recid):

    accessCnt = 0


    return accessCnt

# 2.1.2.5 アイテムステータス取得処理
def get_item_status(recid):

    accessCnt = 0


    return accessCnt


# 2.1.2.6 ダウンロード数取得処理
def get_download_cnt(fielList):

    fileDownloadCnt = 0


    return fileDownloadCnt

# 2.1.2.7 ユーザー名と所属情報取得処理
def get_userNm_affiliation(fielList):

    userNm = ""
    affiliation= ""
    userInfo = userInfo[userNm,affiliation]
    return userInfo
