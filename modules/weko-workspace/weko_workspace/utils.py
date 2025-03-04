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
import requests

from redis import sentinel
from celery.task.control import inspect
from flask import current_app, request, session, jsonify
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
from invenio_pidstore.models import (
    PersistentIdentifier,
    PIDDoesNotExistError,
    PIDStatus,
)
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
from weko_records.api import (
    FeedbackMailList,
    ItemsMetadata,
    ItemTypeNames,
    ItemTypes,
    Mapping,
)
from weko_records.models import ItemType
from weko_records.serializers.utils import get_full_mapping, get_item_type_name
from weko_records_ui.models import FilePermission
from weko_redis import RedisConnection
from weko_user_profiles.config import (
    WEKO_USERPROFILES_INSTITUTE_POSITION_LIST,
    WEKO_USERPROFILES_POSITION_LIST,
)
from weko_user_profiles.utils import get_user_profile_info
from werkzeug.utils import import_string
from weko_deposit.pidstore import get_record_without_version

# =============================================================
from weko_user_profiles.models import UserProfile
from weko_admin.utils import StatisticMail

from .models import *
from .defaultfilters import DEFAULT_FILTERS


def get_workspace_filterCon():
    """Get default conditions of the current login user.

    Arguments:
        --

    Returns:
        default_con -- default conditions json
    """
    # print("======workspace def get_workspace_filterCon(): ======")

    try:
        isnotNone = True
        default_con = (
            WorkspaceDefaultConditions.query.filter_by(user_id=current_user.id)
            .with_entities(WorkspaceDefaultConditions.default_con)
            .scalar()
        )
        if default_con is None:
            # current_app.logger.warning(f"No default conditions found for user {current_user.id}, using DEFAULT_FILTERS.")
            print(
                f"============================== No default conditions found for user {current_user.id}, using DEFAULT_FILTERS."
            )
            default_con = DEFAULT_FILTERS
            isnotNone = False

    except SQLAlchemyError as e:
        # current_app.logger.error(f"Database error while fetching default conditions for user {current_user.id}: {e}")
        print(
            f"============================== Database error while fetching default conditions for user {current_user.id}: {e}"
        )
        default_con = DEFAULT_FILTERS
        isnotNone = False
    except Exception as e:
        # current_app.logger.error(f"Unexpected error while fetching default conditions for user {current_user.id}: {e}")
        print(
            f"============================== Unexpected error while fetching default conditions for user {current_user.id}: {e}"
        )
        default_con = DEFAULT_FILTERS
        isnotNone = False

    # print(default_con)

    return default_con, isnotNone


# 2.1.2.2 ESからアイテム一覧取得処理
def get_es_itemlist():
    """Get the item list from Elasticsearch.

    Args:
        ----
    """

    # print("======workspace def get_es_itemlist(): ======")

    invenio_api_path = "/api/worksapce/search"
    headers = {"Accept": "application/json"}

    response = requests.get(request.host_url.rstrip("/") + invenio_api_path, headers=headers)
    size = response.json()["hits"]["total"]
    
    response = requests.get(request.host_url.rstrip("/") + invenio_api_path + "?size="+str(size), headers=headers)
    records_data = response.json()
    # print("=======records_data start=======")
    # print(records_data)
    # print("=======records_data end=======")
    return records_data


def get_workspace_status_management(recid: str):
    """Get the favorite status and read status of the item.

    Arguments:
        recid {string} -- recid of item

    Returns:
        [tuple] -- the favorite status and read status
        tuple[0] -- the favorite status
        tuple[1] -- the read status
    """

    # print("======workspace def get_workspace_status_management(): ======")

    result = (
        WorkspaceStatusManagement.query.filter_by(user_id=current_user.id, recid=recid)
        .with_entities(
            WorkspaceStatusManagement.is_favorited, WorkspaceStatusManagement.is_read
        )
        .first()
    )

    return result


def get_accessCnt_downloadCnt(recid: str):
    """Get access count and download count of item.

    Arguments:
        recid {string} -- recid of item

    Returns:
        [tuple] -- access count and download count
        tuple[0] -- access count
        tuple[1] -- download count

    """
    # print("======workspace def get_access_cnt(recid:int): ======")

    uuid = PersistentIdentifier.get(
        current_app.config["WEKO_WORKSPACE_PID_TYPE"], recid
    ).object_uuid

    time = None

    result = StatisticMail.get_item_information(uuid, time, "")

    accessCnt = int(float(result["detail_view"]))

    downloadCnt = int(sum(float(value) for value in result["file_download"].values()))

    # print((accessCnt,downloadCnt))
    return (accessCnt, downloadCnt)


# TODO 2.1.2.5 アイテムステータス取得処理
def get_item_status(recid: int):

    # テストデータ
    itemSts = "Unlinked-testdata"

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
    affiliation = "ivis-testdata"

    """Get user name"""
    userNm = (
        UserProfile.query.filter_by(user_id=current_user.id)
        .with_entities(UserProfile.username)
        .scalar()
    )

    userNm = current_user.email if userNm is None else userNm

    """Get user affiliation information"""
    # TODO 外部サービスを参照する必要。取得先確認待ち。

    return (userNm, affiliation)


# お気に入り既読未読ステータス情報登録
def insert_workspace_status(user_id, recid, is_favorited=False, is_read=False):
    """Insert the favorite status and read status of the item.

    Args:
        user_id (_type_): _description_
        recid (_type_): _description_
        is_favorited (bool, optional): _description_. Defaults to False.
        is_read (bool, optional): _description_. Defaults to False.

    Raises:
        e: _description_

    Returns:
        _type_: _description_
    """
    new_status = WorkspaceStatusManagement(
        user_id=user_id,
        recid=recid,
        is_favorited=is_favorited,
        is_read=is_read,
        created=datetime.utcnow(),
        updated=datetime.utcnow(),
    )
    db.session.add(new_status)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e
    return new_status


# お気に入り既読未読ステータス情報更新
def update_workspace_status(user_id, recid, is_favorited=None, is_read=None):
    """Update the favorite status and read status of the item.

    Args:
        user_id (_type_): _description_
        recid (_type_): _description_
        is_favorited (_type_, optional): _description_. Defaults to None.
        is_read (_type_, optional): _description_. Defaults to None.

    Raises:
        e: _description_

    Returns:
        _type_: _description_
    """
    status = WorkspaceStatusManagement.query.filter_by(
        user_id=user_id, recid=recid
    ).first()
    if status:
        if is_favorited is not None:
            status.is_favorited = is_favorited
        if is_read is not None:
            status.is_read = is_read
        status.updated = datetime.utcnow()

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
        return status
    else:
        return None
