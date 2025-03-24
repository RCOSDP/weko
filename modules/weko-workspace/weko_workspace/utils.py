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

import json
from datetime import datetime,timezone
import requests
from flask import current_app, request
from flask_babelex import gettext as _
from flask_security import current_user
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier
from sqlalchemy.exc import SQLAlchemyError
from weko_user_profiles.models import UserProfile
from weko_records.models import OaStatus
from weko_admin.utils import StatisticMail

from .models import WorkspaceDefaultConditions, WorkspaceStatusManagement

def get_workspace_filterCon():
    """
    Retrieves the default filtering conditions for the current user.

    Returns:
        tuple:
            - default_con (dict): The user's default filtering conditions. 
                If the query fails or returns None, `DEFAULT_FILTERS` is returned.
            - isnotNone (bool): Indicates whether a non-null value was successfully retrieved from the database. 
                Returns False if the query fails or returns None.

    Raises:
        SQLAlchemyError: If a database query error occurs, the function returns `DEFAULT_FILTERS`.
        Exception: If any other unexpected error occurs, the function returns `DEFAULT_FILTERS`.
    """

    try:
        isnotNone = True
        DEFAULT_FILTERS = current_app.config["WEKO_WORKSPACE_DEFAULT_FILTERS"]

        default_con = (
            WorkspaceDefaultConditions.query.filter_by(user_id=current_user.id)
            .with_entities(WorkspaceDefaultConditions.default_con)
            .scalar()
        )
        if default_con is None:
            default_con = DEFAULT_FILTERS
            isnotNone = False

    except SQLAlchemyError as e:
        default_con = DEFAULT_FILTERS
        isnotNone = False
    except Exception as e:
        default_con = DEFAULT_FILTERS
        isnotNone = False
    return default_con, isnotNone


# 2.1.2.2 ESからアイテム一覧取得処理
def get_es_itemlist():
    """
    Fetches records data from an external API.

    Returns:
        dict or None: The records data in JSON format if the API requests are successful; 
                      returns `None` if an error occurs.

    Raises:
        requests.exceptions.RequestException: If an HTTP error occurs, such as a timeout or invalid response.
        json.JSONDecodeError: If the response cannot be decoded as JSON.
        KeyError: If the expected keys are missing in the response data.
    """
    invenio_api_path = "/api/workspace/search"
    headers = {"Accept": "application/json"}
    base_url = request.host_url.rstrip("/")

    try:
        response = requests.get(base_url + invenio_api_path, headers=headers)
        response.raise_for_status() 
        size = response.json()["hits"]["total"]

        response = requests.get(base_url + invenio_api_path + "?size=" + str(size), headers=headers)
        response.raise_for_status()
        records_data = response.json()
        return records_data
    except requests.exceptions.RequestException as e:
        return None
    except json.JSONDecodeError as e:
        return None
    except KeyError as e:
        return None


def get_workspace_status_management(recid: str):
    """
    Retrieves the workspace status for a specific user and record ID.

    Args:
        recid (int): The record ID for which the workspace status is being queried.

    Returns:
        tuple or None: A tuple containing two boolean values:
            - `is_favorited` (bool): Whether the workspace is favorited.
            - `is_read` (bool): Whether the workspace has been read.
            If the query fails or no result is found, returns `None`.

    Raises:
        SQLAlchemyError: If a database error occurs during the query, returns `None`.
    """
    try:
        result = (
            WorkspaceStatusManagement.query.filter_by(user_id=current_user.id, recid=recid)
            .with_entities(
                WorkspaceStatusManagement.is_favorited,
                WorkspaceStatusManagement.is_read
            )
            .first()
        )
        return result
    except SQLAlchemyError:
        return None


def get_accessCnt_downloadCnt(recid: str):
    """
    Retrieves the access and download counts for a specific record.

    Args:
        recid (int): The record ID for which access and download statistics are being fetched.

    Returns:
        tuple: A tuple containing two integers:
            - accessCnt (int): The number of accesses (views) of the record.
            - downloadCnt (int): The total number of file downloads related to the record.
            If an error occurs, returns (0, 0).

    Raises:
        Exception: If any error occurs during the process (e.g., failure in retrieving UUID 
                   or querying statistics), the function returns (0, 0).
    """
    try:
        uuid = PersistentIdentifier.get(
            current_app.config["WEKO_WORKSPACE_PID_TYPE"], recid
        ).object_uuid

        time = None
        result = StatisticMail.get_item_information(uuid, time, "")

        accessCnt = int(float(result["detail_view"]))
        downloadCnt = int(sum(float(value) for value in result["file_download"].values()))

        return (accessCnt, downloadCnt)

    except Exception:
        return (0, 0)


# 2.1.2.5 アイテムステータス取得処理
def get_item_status(recId: str):
    """
    Get the converted OA status for a given recid.

    Args:
        recId (str): The record ID (WEKO item PID or related identifier).

    Returns:
        str: The converted OA status based on the mapping, defaults to "Unlinked" if not found.
    """
    # recIdをwekoItemPidとしてそのまま使用（文字列として受け取る）
    wekoItemPid = recId

    # 元のメソッドを呼び出してOA状態を取得
    oaStatusRecord = OaStatus.get_oa_status_by_weko_item_pid(wekoItemPid)

    # レコードが存在しない場合、"Unlinked"を返す
    if oaStatusRecord is None:
        return "Unlinked"

    # 元の状態を取得し、変換を行う
    originalStatus = oaStatusRecord.oa_status
    return current_app.config.get("WEKO_WORKSPACE_OA_STATUS_MAPPING").get(originalStatus, "Unlinked")


def get_userNm_affiliation():
    """
    Retrieve the username of the current user.

    Returns:
        str: The username if available; otherwise, the user's email.
    """
    userNm = (
        UserProfile.query.filter_by(user_id=current_user.id)
        .with_entities(UserProfile.username)
        .scalar()
    )

    userNm = current_user.email if userNm is None else userNm

    return userNm


# お気に入り既読未読ステータス情報登録
def insert_workspace_status(user_id, recid, is_favorited=False, is_read=False):
    """
    Adds a new workspace status entry to the database.

    Args:
        user_id (int): The ID of the user whose workspace status is being recorded.
        recid (int): The record ID associated with the workspace status.
        is_favorited (bool): The status indicating whether the workspace is favorited.
        is_read (bool): The status indicating whether the workspace has been read.

    Returns:
        WorkspaceStatusManagement: The newly created workspace status entry.

    Raises:
        Exception: If an error occurs during the database commit, the transaction is rolled back 
                  and the exception is raised.
    """
    new_status = WorkspaceStatusManagement(
        user_id=user_id,
        recid=recid,
        is_favorited=is_favorited,
        is_read=is_read,
        created=datetime.now(timezone.utc),
        updated=datetime.now(timezone.utc),
    )
    db.session.add(new_status)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e
    return new_status


# お気に入り既読未読ステータス情報更新
def update_workspace_status(user_id, recid, is_favorited=False, is_read=False):
    """
    Update the favorite status and read status of a workspace item.

    Args:
        user_id (str): The ID of the user whose workspace status is being updated.
        recid (str): The record ID of the workspace item to update.
        is_favorited (bool, optional): The updated favorite status. Defaults to False.
        is_read (bool, optional): The updated read status. Defaults to False.

    Returns:
        WorkspaceStatusManagement or None: The updated workspace status record if the status 
                                            was found and updated, or `None` if the status 
                                            for the given `user_id` and `recid` was not found.

    Raises:
        Exception: If an error occurs during the commit, the transaction is rolled back and 
                  the exception is raised.
    """
    status = WorkspaceStatusManagement.query.filter_by(
        user_id=user_id, recid=recid
    ).first()
    if status:
        if is_favorited is not None:
            status.is_favorited = is_favorited
        if is_read is not None:
            status.is_read = is_read
        status.updated = datetime.now(timezone.utc)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
        return status
    else:
        return None


def extract_metadata_info(item_metadata):
    """
    Extract filelist and peer_reviewed information from _item_metadata.

    Args:
        item_metadata (dict): The _item_metadata content from JSON.

    Returns:
        tuple: (filelist, peer_reviewed)
            - filelist (list): List of filenames, returns empty list if no files.
            - peer_reviewed (bool): True if "Peer reviewed", False otherwise or if not present.
    """
    filelist = []
    peer_reviewed = False

    # filelistを抽出
    for key, value in item_metadata.items():
        if isinstance(value, dict) and value.get("attribute_type") == "file":
            # attribute_typeが "file" の内容を見つける
            filelist = value.get("attribute_value_mlt", [])
            break  # 見つけたらループを終了

    # peer_reviewedを抽出
    for key, value in item_metadata.items():
        if isinstance(value, dict) and "attribute_value_mlt" in value:
            for item in value["attribute_value_mlt"]:
                if "subitem_peer_reviewed" in item:
                    peer_reviewed_value = item["subitem_peer_reviewed"]
                    peer_reviewed = peer_reviewed_value == "Peer reviewed"
                    break  # 見つけたら内側のループを終了
            if peer_reviewed:  # peer_reviewedが見つかった場合、外側のループを終了
                break
    return filelist, peer_reviewed