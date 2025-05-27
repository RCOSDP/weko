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

"""call external system"""

import json
import traceback
from flask import current_app
from urllib3.util.retry import Retry
import requests
from requests.adapters import HTTPAdapter

from weko_deposit.api import WekoRecord
from weko_records.models import ItemReference, OaStatus
from weko_admin.models import ApiCertificate


def call_external_system(old_record=None,
                         new_record=None,
                         old_item_reference_list=None,
                         new_item_reference_list=None):
    """call external system if needed
    Args:
        old_record(WekoRocord): record before update
        new_record(WekoRocord): record after update
        old_item_reference_list(list(ItemReference)):
            item reference list before update
        new_item_reference_list(list(ItemReference)):
            item reference list after update
    """
    EXTERNAL_SYSTEM = current_app.config.get("EXTERNAL_SYSTEM")
    if EXTERNAL_SYSTEM is None:
        return
    if new_item_reference_list is None:
        new_item_reference_list = []
    if old_item_reference_list is None:
        old_item_reference_list = []
    if not validate_records(
            old_record,
            new_record,
            old_item_reference_list,
            new_item_reference_list):
        return
    external_system_list = select_call_external_system_list(
        old_record=old_record,
        new_record=new_record,
        old_item_reference_list=old_item_reference_list,
        new_item_reference_list=new_item_reference_list
    )

    # case OA assist
    if EXTERNAL_SYSTEM.OA in external_system_list:
        # get oa token
        token = get_oa_token()
        if not token:
            return

        # call oa update status api
        record = new_record if new_record else old_record
        action = get_action(old_record, new_record)
        data = {}
        data["action"] = action.value
        data["item_info"] = {}
        data["item_info"]["pub_date"] = \
            record.get("pubdate",{}).get("attribute_value")
        ITEM_ACTION = current_app.config.get("ITEM_ACTION")
        if action == ITEM_ACTION.DELETED:
            data["item_info"]["publish_status"] = -1
        else:
            data["item_info"]["publish_status"] = int(record.get("publish_status"))

        files = []
        for property in record.values():
            if isinstance(property, dict):
                if property.get("attribute_type") == "file":
                    files = property.get("attribute_value_mlt")
        file_counts = get_file_counts(files)
        data["file_counts"] = file_counts

        pid_value_without_ver = get_pid_value_without_ver(old_record, new_record)
        article_id = get_article_id(pid_value_without_ver)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        remarks = {}
        remarks["action"] = action.value
        oa_result = {}

        update_status_url = current_app.config.get(
            "WEKO_RECORDS_UI_OA_UPDATE_STATUS_URL", "")
        if update_status_url and isinstance(update_status_url, str):
            update_status_url = update_status_url.format(article_id)
            current_app.logger.debug("call OA update status api")
            try:
                with requests.Session() as s:
                    retries = Retry(
                        total=current_app.config.get(
                            "WEKO_RECORDS_UI_OA_API_RETRY_COUNT"),
                        status_forcelist=[500, 502, 503, 504])
                    s.mount('https://', HTTPAdapter(max_retries=retries))
                    s.mount('http://', HTTPAdapter(max_retries=retries))
                    response = s.put(update_status_url,
                                     headers=headers,
                                     json=data)
                    if response.status_code == 200:
                        oa_result["status"] = response.json().get("status")
                    else:
                        oa_result["status"] = response.json().get("status")
                        oa_result["message"] = response.json().get("message")

            except requests.exceptions.RequestException as req_err:
                current_app.logger.error(req_err)
                current_app.logger.error(traceback.format_exc())
                oa_result["status"] = "error"

            finally:
                remarks[EXTERNAL_SYSTEM.OA.value] = oa_result
                # TODO 基本監査ログ機能が実装されたらそちらに出力する
                current_app.logger.info(remarks)
                # 基本監査ログに機能ID、処理ID、対象キー、備考を渡して出力する

                # operation_type_id: 機能ID
                # operation_id: 処理ID
                # target: 対象キー
                # remarks: 備考

                # user_log.info(
                #     operation_type_id = "ITEM",
                #     operation_id = "ITEM_EXTERNAL_LINK"
                #     target_key = pid_value_without_ver,
                #     remarks = remarks
                # )

def get_oa_token():
    """ Get oa token

    Returns:
        str: oa token
    """

    headers = {
        'Content-Type': 'application/json'
    }
    api_cert = ApiCertificate.select_by_api_code(
        current_app.config.get("WEKO_RECORDS_UI_OA_API_CODE"))
    if not api_cert:
        return
    cert_data = api_cert.get("cert_data", {})
    client_id = cert_data.get("client_id") if cert_data else None
    client_secret = cert_data.get("client_secret") if cert_data else None
    if not client_secret or not client_id:
        current_app.logger.debug("client_id or client_secret is None")
        return
    token = None
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    get_token_url = current_app.config.get(
        "WEKO_RECORDS_UI_OA_GET_TOKEN_URL")
    if get_token_url:
        current_app.logger.debug("call OA token api")
        try:
            with requests.Session() as s:
                retries = Retry(
                    total=current_app.config.get(
                        "WEKO_RECORDS_UI_OA_API_RETRY_COUNT"),
                    status_forcelist=[500, 502, 503, 504])
                s.mount('https://', HTTPAdapter(max_retries=retries))
                s.mount('http://', HTTPAdapter(max_retries=retries))
                response = s.post(get_token_url, headers=headers, json=data)
            if response.text:
                res = json.loads(response.text)
                token = res.get("access_token")

        except requests.exceptions.RequestException as req_err:
            current_app.logger.error(req_err)
            current_app.logger.error(traceback.format_exc())
    return token


def select_call_external_system_list(old_record=None,
                                     new_record=None,
                                     old_item_reference_list=None,
                                     new_item_reference_list=None):
    """Determine the list of external systems to integrate with
    Args:
        old_record(WekoRocord): record before update
        new_record(WekoRocord): record after update
        old_item_reference_list(list(ItemReference)):
            item reference list before update
        new_item_reference_list(list(ItemReference)):
            item reference list after update
    Returns:
        list: external systems to integrate with
    """
    EXTERNAL_SYSTEM = current_app.config.get("EXTERNAL_SYSTEM")
    ITEM_ACTION = current_app.config.get("ITEM_ACTION")

    selected_system_set = set()
    try:
        pid_value = get_pid_value_without_ver(old_record, new_record)
        article_id = get_article_id(pid_value)
        action = get_action(old_record, new_record)
        if article_id:
            if action == ITEM_ACTION.CREATED or action == ITEM_ACTION.DELETED:
                selected_system_set.add(EXTERNAL_SYSTEM.OA)
            elif action == ITEM_ACTION.UPDATED:
                changed_property = get_record_diff(old_record, new_record)
                property_list = ["pubdate", "publish_status", "file_counts"]
                for property in property_list:
                    if changed_property["before"].get(property) != \
                        changed_property["after"].get(property):
                        selected_system_set.add(EXTERNAL_SYSTEM.OA)

    except Exception as ex:
        current_app.logger.error(ex)
        current_app.logger.error(traceback.format_exc())

    return list(selected_system_set)


def get_pid_value_without_ver(old_record, new_record):
    """get pid value(integer)
    Args:
        old_record(WekoRecord): record before update
        new_record(WekoRecord): record after update
    Returns:
        str: pid value without ver
    """
    old_recid = None
    new_recid = None
    if isinstance(old_record, dict):
        old_recid = old_record.get('recid','').split('.')[0]
    if isinstance(new_record, dict):
        new_recid = new_record.get('recid','').split('.')[0]
    if old_recid and new_recid and (old_recid != new_recid):
        return
    return new_recid if new_recid else old_recid


def get_action(old_record, new_record):
    """determine the action performed on the item
    Args:
        old_record(WekoRecord): record before update
        new_record(WekoRecord): record after update
    Returns:
        Enum: action performed on the item
    """
    ITEM_ACTION = current_app.config.get("ITEM_ACTION")
    action = None
    if old_record and new_record:
        action = ITEM_ACTION.UPDATED
    elif not old_record and new_record:
        action = ITEM_ACTION.CREATED
    elif old_record and not new_record:
        action = ITEM_ACTION.DELETED
    return action


def get_article_id(pid):
    """get article id using pid without ver
    Args:
        pid(str): item pid without ver
    Returns:
        int: article id
    """
    oa_status = OaStatus.get_oa_status_by_weko_item_pid(pid)
    return oa_status.oa_article_id if oa_status else None


def get_file_counts(files):
    """file counts by publish status
    Args:
        files: file data in record
    Returns:
        file counts by publish status
    """
    # avoid circular import
    from .utils import is_future

    FILE_OPEN_STATUS = current_app.config.get("FILE_OPEN_STATUS")
    file_counts = {}
    open_count = 0
    embargo_count = 0
    pirvate_count = 0
    restricted_count = 0

    for file in files:
        role = file.get("accessrole")
        if role == "open_access":
            open_count += 1
        elif role == "open_date":
            open_date = ""
            access_date = file.get("accessdate")
            if access_date:
                open_date = access_date
            else:
                open_date = file.get("date",[{}])[0].get("dateValue")
            if is_future(open_date):
                embargo_count += 1
            else:
                open_count += 1
        elif role == "open_login" or role == "open_no":
            pirvate_count += 1
        elif role == "open_restricted":
            restricted_count += 1

    file_counts[FILE_OPEN_STATUS.PUBLIC.value] = open_count
    file_counts[FILE_OPEN_STATUS.EMBARGO.value] = embargo_count
    file_counts[FILE_OPEN_STATUS.PRIVATE.value] = pirvate_count
    file_counts[FILE_OPEN_STATUS.RESTRICTED.value] = restricted_count
    return file_counts


def validate_records(old_record,
                     new_record,
                     old_item_reference_list,
                     new_item_reference_list):
    """valudate records
    Args:
        old_record(WekoRocord): record before update
        new_record(WekoRocord): record after update
        old_item_reference_list(list(ItemReference)):
            item reference list before update
        new_item_reference_list(list(ItemReference)):
            item reference list after update
    Returns:
        boolean: Whether records are valid
    """
    if not old_record is None and not isinstance(old_record, WekoRecord):
        return False
    if not new_record is None and not isinstance(new_record, WekoRecord):
        return False
    action = get_action(old_record, new_record)
    if action is None:
        return False
    # whether pid matches
    pid_value_without_ver = get_pid_value_without_ver(old_record, new_record)
    if pid_value_without_ver is None:
        return False
    if not isinstance(old_item_reference_list, list):
        return
    for reference in old_item_reference_list:
        if not isinstance(reference, ItemReference):
            return False
        if pid_value_without_ver != reference.src_item_pid.split('.')[0]:
            return False
    if not isinstance(new_item_reference_list, list):
        return
    for reference in new_item_reference_list:
        if not isinstance(reference, ItemReference):
            return False
        if pid_value_without_ver != reference.src_item_pid.split('.')[0]:
            return False
    return True


def get_record_diff(old_record, new_record):
    """get the difference between old record and new record
    Args:
        old_record(WekoRocord): record before update
        new_record(WekoRocord): record after update
    Returns:
        dict: the difference of publish_status, pubdate and file_counts
        between old record and new record
    """
    diff = {}
    if old_record is None:
        old_record = {}
    if new_record is None:
        new_record = {}

    # case change publish status
    old_pub_status = old_record.get("publish_status")
    new_pub_status = new_record.get("publish_status")
    diff["before"] = {}
    diff["after"] = {}
    if old_pub_status != new_pub_status:
        diff["before"]["publish_status"] = old_pub_status
        diff["after"]["publish_status"] = new_pub_status

    # case change pubdate
    old_pubdate = old_record.get("pubdate",{}).get("attribute_value")
    new_pubdate = new_record.get("pubdate",{}).get("attribute_value")
    if old_pubdate != new_pubdate:
        diff["before"]["pubdate"] = old_pubdate
        diff["after"]["pubdate"] = new_pubdate

    # case change files
    old_files = []
    new_files = []
    for property in old_record.values():
        if isinstance(property, dict):
            if property.get("attribute_type") == "file":
                old_files = property.get("attribute_value_mlt")
    for property in new_record.values():
        if isinstance(property, dict):
            if property.get("attribute_type") == "file":
                new_files = property.get("attribute_value_mlt")
    old_file_counts = get_file_counts(old_files)
    new_file_counts = get_file_counts(new_files)
    if old_file_counts != new_file_counts:
        diff["before"]["file_counts"] = old_file_counts
        diff["after"]["file_counts"] = new_file_counts
    return diff
