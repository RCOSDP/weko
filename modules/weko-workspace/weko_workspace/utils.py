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

"""Module of weko-workspace utils."""

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
from flask import current_app, request, session,jsonify
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

# =============================================================
from weko_user_profiles.models import UserProfile
from weko_admin.utils import StatisticMail


# TODO 2.1.2.1 デフォルト絞込み条件取得処理
def get_workspace_filterCon():
    default_con = {
        "name":"guan.shuang",
    }

    user_id = current_user.id
    # print("user_id " + str(user_id))

    # モデルクラスからデータを取得。


    return default_con

# TODO 2.1.2.2 ESからアイテム一覧取得処理
def get_es_itemlist(jsonCondition):

    fake_response = {
        "took": 5,
        "timed_out": False,
        "_shards": {
            "total": 5,
            "successful": 5,
            "skipped": 0,
            "failed": 0
        },
        "hits": {
            "total": {
                "value": 2,
                "relation": "eq"
            },
            "max_score": 1.0,
            "hits": [
                {
                    "_index": "your_index_name",
                    "_type": "_doc",
                    "_id": "90e81f37-8aa6-4bcd-abac-91d1df25fc45",
                    "_score": 1.0,
                    "_source": {
                        "title": "First Document",
                        "content": "This is the content of the first document.",
                        "author": "John Doe",
                        "date": "2023-10-01"
                    }
                },
            ]
        }
    }
    return json.dumps(fake_response, indent=4)


# TODO 2.1.2.3 お気に入り既読未読ステータス取得処理
def get_workspace_status_management(recid:int):
    isFavoritedSts = False
    isRead = True

    user_id = current_user.id


    stsRes = (isFavoritedSts,isRead)
    return stsRes


def get_accessCnt_downloadCnt (item_id:str):
    """Get access count and download count of item.

    Arguments:
        item_id {string} -- recid of item

    Returns:
        [tuple] -- access count and download count
        tuple[0] -- access count
        tuple[1] -- download count

    """
    # print("======workspace def get_access_cnt(recid:int): ======")
    
    uuid = PersistentIdentifier.get(current_app.config['WEKO_WORKSPACE_PID_TYPE'],item_id).object_uuid
    time = None

    result = StatisticMail.get_item_information(uuid,time,"")

    accessCnt = int(float(result["detail_view"]))

    downloadCnt = int(sum(float(value) for value in result["file_download"].values()))

    return (accessCnt,downloadCnt)

# TODO 2.1.2.5 アイテムステータス取得処理
def get_item_status(recid:int):

    itemSts = ""


    return itemSts


def get_userNm_affiliation():
    """Get user name and affiliation information of item.

    Arguments:
        --

    Returns:
        [tuple] -- user name and affiliation information
        tuple[0] -- user name
        tuple[1] -- affiliation information

    """

    # print("======workspace def get_userNm_affiliation(): ======")
    # userNm = "guan.shuang"
    affiliation= "ivis"
    
    """Get user name"""
    userNm = (
    UserProfile.query
        .filter_by(user_id=current_user.id)
        .with_entities(UserProfile.username)
        .scalar()
    )

    userNm = current_user.email if userNm is None else userNm
    
    
    """Get user affiliation information"""
    # TODO 外部サービスを参照する必要。取得先確認待ち。

    return (userNm,affiliation)
