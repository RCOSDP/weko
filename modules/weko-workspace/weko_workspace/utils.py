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


from copy import deepcopy
from flask_babelex import gettext as _
from weko_records.api import (
    ItemTypes,
    Mapping,
)
from weko_items_autofill.utils import sort_by_item_type_order
from .api import CiNiiURL, JALCURL, DATACITEURL, JamasURL
from lxml import etree


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
        size_param = "?size=" + str(size) if size else ""

        response = requests.get(base_url + invenio_api_path + size_param, headers=headers)
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


def changeLang(language: str, defaultconditions: dict):
    """
        Translates the labels in the given dictionary to Japanese if the selected language is "ja".
        
        Parameters:
        language (str): The target language code. If it is "ja", the labels will be translated to Japanese.
        defaultconditions (dict): A dictionary containing resource attributes, where each key represents a category
                                and each value is a dictionary that may contain a "label" field.
        
        Returns:
        dict: The updated dictionary with translated labels if the language is "ja"; otherwise, the original dictionary.
        """

    if "ja" == language:
        label_mapping = {
            "Resource Type": "リソースタイプ",
            "Peer Review": "査読",
            "Related To Paper": "論文への関連",
            "Related To Data": "根拠データへの関連",
            "Funding Reference - Funder Name": "資金別情報 - 助成機関名",
            "Funding Reference - Award Title": "資金別情報 - 研究課題名",
            "File": "本文ファイル",
            "Favorite": "お気に入り",
        }

        for key in defaultconditions:
            if "label" in defaultconditions[key]:
                old_label = defaultconditions[key]["label"]
                if old_label in label_mapping:
                    defaultconditions[key]["label"] = label_mapping[old_label]

    return defaultconditions


def changeMsg(language: str, type: str, boolFlg: bool, message: str):

    if "ja" == language:
        # デフォルト条件登録の場合
        if 1 == type:
            message = "デフォルト条件の保存に成功しました。"

        # デフォルト条件リセットの場合
        elif 2 == type:
            if boolFlg:
                message = "デフォルト条件のリセットに成功しました。"
            else:
                message = "リセットするデフォルト条件が見つかりません。"
    else:
        pass

    return message


def convert_jamas_xml_data_to_dictionary(api_data, encoding='utf-8'):
    """Convert Jamas XML data to dictionary.

    :param api_data: CrossRef Jamas data
    :param encoding: Encoding type
    :return: Jamas data is converted to dictionary.
    """
    result = {}
    rtn_data = {
        'response': {},
        'error': ''
    }
    try:
        root = etree.XML(api_data.encode(encoding))
        jamas_xml_data_keys = current_app.config['WEKO_ITEMS_AUTOFILL_CROSSREF_XML_DATA_KEYS']
        for elem in root.getiterator():
            if etree.QName(elem).localname in jamas_xml_data_keys:
                if etree.QName(elem).localname == "contributor" or etree.QName(
                        elem).localname == "organization":
                        pass
                elif etree.QName(elem).localname == "year":
                    pass
                elif etree.QName(elem).localname in ["issn", "isbn"]:
                    pass
                else:
                    result.update({etree.QName(elem).localname: elem.text})

        rtn_data['response'] = result
    except Exception as e:
        rtn_data['error'] = str(e)
    return rtn_data


def get_jamas_record_data(doi, item_type_id):
    """Get record data base on Jamas API.

    :param doi: The Jamas doi
    :param item_type_id: The item type ID
    :return:
    """
    result = list()
    api_response = JamasURL(doi).get_data()
    if api_response["error"]:
        return result

    api_response = convert_jamas_xml_data_to_dictionary(
        api_response['response'])
    if api_response["error"]:
        return result

    api_data = get_jamas_data_by_key(api_response, 'all')
    items = ItemTypes.get_by_id(item_type_id)
    if items is None:
        return result
    elif items.form is not None:
        autofill_key_tree = sort_by_item_type_order(
            items.form,
            get_autofill_key_tree(
                items.form,
                get_jamas_autofill_item(item_type_id)))
        result = build_record_model(autofill_key_tree, api_data)

    return result


def get_jamas_autofill_item(item_id):
    """Get Jamas autofill item.

    :param item_id: Item ID
    :return:
    """
    jpcoar_item = get_item_id(item_id)
    jamas_req_item = dict()
    for key in current_app.config[
            'WEKO_WORKSPACE_AUTOFILL_JAMAS_REQUIRED_ITEM']:
        if jpcoar_item.get(key) is not None:
            jamas_req_item[key] = jpcoar_item.get(key)
    return jamas_req_item


def get_jamas_data_by_key(api, keyword):
    """Get Jamas data based on keyword.

    Arguments:
        api: Jamas data
        keyword: search keyword

    Returns:
        Jamas data for keyword

    """
    if api['error'] or api['response'] is None:
        return None

    data = api['response']
    result = dict()
    if keyword == 'title' and data.get('dc:title'):
        result[keyword] = get_jamas_title_data(data.get('dc:title'))
    elif keyword == 'creator' and data.get('dc:creator'):
        result[keyword] = get_jamas_creator_data(data.get('dc:creator'))
    elif keyword == 'sourceTitle' and data.get('prism:publicationName'):
        result[keyword] = get_jamas_source_title_data(
            data.get('prism:publicationName')
        )
    elif keyword == 'volume' and data.get('prism:volume'):
        result[keyword] = pack_single_value_as_dict(data.get('prism:volume'))
    elif keyword == 'issue' and data.get('prism:number'):
        result[keyword] = pack_single_value_as_dict(data.get('prism:number'))
    elif keyword == 'pageStart' and data.get('prism:startingPage'):
        result[keyword] = pack_single_value_as_dict(data.get('prism:startingPage'))
    elif keyword == 'numPages':
        result[keyword] = pack_single_value_as_dict(data.get('prism:pageRange'))
    elif keyword == 'date' and data.get('prism:publicationDate'):
        result[keyword] = get_jamas_issue_date(data.get('prism:publicationDate'))
    elif keyword == 'relation':
        result[keyword] = get_jamas_relation_data(
            data.get('prism:issn'),
            data.get('prism:eIssn'),
            data.get('prism:doi')
        )
    elif keyword == 'sourceIdentifier':
        result[keyword] = get_jamas_source_data(data.get('prism:issn'))
    elif keyword == 'all':
        for key in current_app.config[
                'WEKO_WORKSPACE_AUTOFILL_JAMAS_REQUIRED_ITEM']:
            result[key] = get_jamas_data_by_key(api, key).get(key)
    return result


def get_jamas_source_data(data):
    """Get Jamas source data.

    :param data:
    :return:
    """
    result = list()
    if data:
        new_data = dict()
        new_data['@value'] = data
        new_data['@type'] = 'ISSN'
        result.append(new_data)
    return result


def get_jamas_relation_data(issn, eIssn, doi):
    """Get Jamas relation data.

    :param issn, eIssn, doi:
    :return:
    """
    result = list()
    if doi:
        new_data = dict()
        new_data['@value'] = doi
        new_data['@type'] = "DOI"
        result.append(new_data)
    if issn and len(result) == 0:
        for element in issn:
            new_data = dict()
            new_data['@value'] = element
            new_data['@type'] = "ISSN"
            result.append(new_data)
    if eIssn and len(result) == 0:
        for element in eIssn:
            new_data = dict()
            new_data['@value'] = element
            new_data['@type'] = "EISSN"
            result.append(new_data)
    if len(result) == 0:
        return pack_single_value_as_dict(None)
    return result


def get_jamas_issue_date(data):
    """Get Jamas issued date.

    Arguments:
        data -- issued data

    Returns:
        Issued date is packed

    """
    result = dict()
    if data:
        result['@value'] = data
        result['@type'] = 'Issued'
    else:
        result['@value'] = None
        result['@type'] = None
    return result


def get_jamas_source_title_data(data):
    """Get source title information.

    Arguments:
        data -- created data

    Returns:
        Source title  data

    """
    new_data = dict()
    default_language = 'en'
    new_data['@value'] = data
    new_data['@language'] = data['dc:language'] if data['dc:language'] else default_language
    return new_data


def get_jamas_creator_data(data):
    """Get creator name from Jamas data.

    Arguments:
        data -- Jamas data

    """
    result = list()
    default_language = 'en'
    for name_data in data:
        full_name = ''
        full_name = name_data.get('dc:creator')

        new_data = dict()
        new_data['@value'] = full_name
        new_data['@language'] = data['dc:language'] if data['dc:language'] else default_language
        result.append(new_data)
    return result


def get_jamas_title_data(data):
    """Get title data from Jamas.

    Arguments:
        data -- title data

    Returns:
        Packed title data

    """
    result = list()
    default_language = 'en'
    if isinstance(data, list):
        for title in data:
            new_data = dict()
            new_data['@value'] = title
            new_data['@language'] = data['dc:language'] if data['dc:language'] else default_language
            result.append(new_data)
    else:
        new_data = dict()
        new_data['@value'] = data
        new_data['@language'] = data['dc:language'] if data['dc:language'] else default_language
        result.append(new_data)
    return result


def get_cinii_record_data(doi, item_type_id):
    """Get record data base on CiNii API.

    :param doi: The CiNii doi
    :param item_type_id: The item type ID
    :return:
    """
    result = list()
    api_response = CiNiiURL(doi).get_data()
    if api_response["error"] \
            or not isinstance(api_response['response'], dict) \
            or not api_response['response']['items']:
        return result
    api_data = get_cinii_data_by_key(api_response, 'all')
    items = ItemTypes.get_by_id(item_type_id)

    if items is None:
        return result
    elif items.form is not None:
        autofill_key_tree = get_autofill_key_tree(
            items.form, get_cinii_autofill_item(item_type_id))
        result = build_record_model(autofill_key_tree, api_data)
    return result


def get_cinii_data_by_key(api, keyword):
    """Get data from CiNii based on keyword.

    :param: api: CiNii data
    :param: keyword: keyword for search
    :return: data for keyword
    """
    import json
    data_response = api['response']
    result = dict()
    if data_response is None:
        return result
    data = data_response

    if keyword == 'title' and data['items'][0].get('title'):
        result[keyword] = get_cinii_title_data(data['items'][0].get('title'))
    elif keyword == 'creator' and data['items'][0].get('dc:creator'):
        result[keyword] = get_cinii_creator_data(data['items'][0].get('dc:creator'))
    elif keyword == 'description' and data['items'][0].get('description'):
        result[keyword] = get_cinii_description_data(
            data['items'][0].get('description')
        )
    elif keyword == 'subject' and data['items'][0].get('dc:subject'):
        result[keyword] = get_cinii_subject_data(data['items'][0].get('dc:subject'), data['items'][0].get('title'))
    elif keyword == 'sourceTitle' and data['items'][0].get('prism:publicationName'):
        result[keyword] = get_cinii_title_data(
            data['items'][0].get('prism:publicationName')
        )
    elif keyword == 'volume' and data['items'][0].get('prism:volume'):
        result[keyword] = pack_single_value_as_dict(data['items'][0].get('prism:volume'))
    elif keyword == 'issue' and data['items'][0].get('prism:number'):
        result[keyword] = pack_single_value_as_dict(data['items'][0].get('prism:number'))
    elif keyword == 'pageStart' and data['items'][0].get('prism:startingPage'):
        result[keyword] = get_cinii_page_data(data['items'][0].get('prism:startingPage'))
    elif keyword == 'pageEnd' and data['items'][0].get('prism:endingPage'):
        result[keyword] = get_cinii_page_data(data['items'][0].get('prism:endingPage'))
    elif keyword == 'numPages':
        result[keyword] = get_cinii_numpage(
            data['items'][0].get('prism:startingPage'), data['items'][0].get('prism:endingPage'))
    elif keyword == 'date' and data['items'][0].get('prism:publicationDate'):
        result[keyword] = get_cinii_date_data(
            data['items'][0].get('prism:publicationDate'))
    elif keyword == 'publisher' and data['items'][0].get('dc:publisher'):
        result[keyword] = get_cinii_title_data(data['items'][0].get('dc:publisher'))
    elif keyword == 'sourceIdentifier' and data['items'][0].get('prism:issn'):
        result[keyword] = pack_data_with_multiple_type_cinii(
            data['items'][0].get('prism:issn')
        )
    elif keyword == "relation" and data['items'][0].get('dc:identifier'):
        result[keyword] = get_cinii_product_identifier(
            data['items'][0].get('dc:identifier'),
            'cir:DOI',
            'cir:NAID'
        )
    elif keyword == 'all':
        for key in current_app.config.get("WEKO_ITEMS_AUTOFILL_CINII_REQUIRED_ITEM"):
            result[key] = get_cinii_data_by_key(api, key).get(key)
    return result

    
def get_cinii_product_identifier(data, type1, type2):
    """Identifier Mapping.

    :param: api: CiNii data
    :param: keyword: keyword for search
    :return: Identifier
    """
    result = list()
    for item in data:
        if item.get('@type') == type1:
            new_data = dict()
            new_data['@value'] = item.get('@value')
            new_data['@type'] = "DOI"
            result.append(new_data)
        if item.get('@type') == type2:
            new_data = dict()
            new_data['@value'] = item.get('@value')
            new_data['@type'] = "NAID"
            result.append(new_data)
    return result
    

def pack_data_with_multiple_type_cinii(data):
    """Map CiNii multi data with type.

    Arguments:
        data1
        type1
        data2
        type2

    Returns:
        packed data

    """
    result = list()
    new_data = dict()
    new_data['@value'] = data
    new_data['@type'] = "ISSN"
    result.append(new_data)

    return result


def get_cinii_date_data(data):
    """Get publication date.

    Get publication date from CiNii data
    format:
    {
        '@value': date
        '@type': type of date
    }

    :param: data: date
    :return: date and date type is packed
    """
    result = dict()
    if len(data.split('-')) != 3:
        result['@value'] = None
        result['@type'] = None
    else:
        result['@value'] = data
        result['@type'] = 'Issued'
    return result


def get_cinii_numpage(startingPage, endingPage):
    """Get number of page.

    If CiNii have pageRange, get number of page
    If not, number of page equals distance between start and end page

    :param: data: CiNii data
    :return: number of page is packed
    """
    if startingPage and endingPage:
        try:
            end = int(endingPage)
            start = int(startingPage)
            num_pages = end - start + 1
            return pack_single_value_as_dict(str(num_pages))
        except Exception as e:
            current_app.logger.debug(e)
            return pack_single_value_as_dict(None)
    return {"@value": None}



def get_cinii_page_data(data):
    """Get start page and end page data.

    Get page info and pack it:
    {
        '@value': number
    }

    :param: data: No of page
    :return: packed data
    """
    try:
        result = int(data)
        return pack_single_value_as_dict(str(result))
    except Exception as e:
        current_app.logger.debug(e)
        return pack_single_value_as_dict(None)



def pack_single_value_as_dict(data):
    """Pack value as dictionary.

    Based on return format
    {
        '@value': value
    }

    :param: data: data need to pack
    :return: dictionary contain packed data
    """
    new_data = dict()
    new_data['@value'] = data
    return new_data


def get_cinii_subject_data(data, title):
    """Get subject data from CiNii.

    Get subject and form it as format:
    {
        '@value': title,
        '2language': language,
        '@scheme': scheme of subject
        '@URI': source of subject
    }

    :param: data: subject data
    :return: packed data
    """
    result = list()
    default_language = 'ja'
    for sub in data:
        new_data = dict()
        new_data["@scheme"] = "Other"
        new_data["@value"] = sub
        new_data["@language"] = default_language
        result.append(new_data)
    return result


def get_cinii_creator_data(data):
    """Get creator data from CiNii.

    Get creator name and form it as format:
    {
        '@value': name,
        '@language': language
    }

    :param: data: creator data
    :return: list of creator name
    """
    result = list()
    default_language = 'ja'
    for item in data:
        name_data = item
        if name_data:
            result_creator = list()
            new_data = dict()
            new_data['@value'] = name_data
            new_data['@language'] = default_language
            result_creator.append(new_data)
            result.append(result_creator)
    return result


def get_cinii_contributor_data(data):
    """Get contributor data from CiNii.

    Get contributor name and form it as format:
    {
        '@value': name,
        '@language': language
    }

    :param: data: marker data
    :return:packed data
    """
    result = list()
    for item in data:
        name_data = item
        if name_data:

            result.append(get_basic_cinii_data(name_data))
    return result


def get_cinii_title_data(data):
    """Get title data from CiNii.

    Get title name and form it as format:
    {
        '@value': name,
        '@language': language
    }

    :param: data: marker data
    :return:packed data
    """
    result = list()
    default_language = 'ja'
    new_data = dict()
    new_data['@value'] = data
    new_data['@language'] = default_language
    result.append(new_data)
    return result


def get_basic_cinii_data(data):
    """Get basic data template from CiNii.

        Basic value format:
        {
            '@value': value,
            '@language': language
        }

    :param: data: CiNii data
    :return: list converted data
    """
    result = list()
    default_language = 'ja'

    for item in data:
        new_data = dict()
        new_data['@value'] = item
        new_data['@language'] = default_language
        result.append(new_data)
    return result


def get_cinii_description_data(data):
    """Get description data from CiNii.

    Get description and form it as format:
    {
        '@value': description,
        '@language': language,
        '@type': type of description
    }

    :param: description data
    :return: packed data
    """
    result = list()
    default_language = 'ja'
    default_type = 'Abstract'
    new_data = dict()

    new_data['@value'] = data
    new_data['@type'] = default_type
    new_data["@language"] = default_language
    result.append(new_data)
    return result


def get_autofill_key_tree(schema_form, item, result=None):
    """Get auto fill key tree.

    :param schema_form: schema form
    :param item: The mapping items
    :param result: The key result
    :return: Autofill key tree
    """
    if result is None:
        result = dict()
    if not isinstance(item, dict):
        return None
    for key, val in item.items():
        if isinstance(val, dict) and 'model_id' in val.keys():
            parent_key = val['model_id']
            key_data = dict()
            if parent_key == "pubdate":
                continue
            if key == "creator":
                creator_name_object = val.get("creatorName")
                if creator_name_object:
                    key_data = get_key_value(schema_form,
                                             creator_name_object, parent_key)
            elif key == "contributor":
                contributor_name = val.get("contributorName")
                if contributor_name:
                    key_data = get_key_value(schema_form,
                                             contributor_name, parent_key)
            elif key == "relation":
                related_identifier = val.get("relatedIdentifier")
                if related_identifier:
                    key_data = get_key_value(schema_form,
                                             related_identifier, parent_key)
            else:
                key_data = get_key_value(schema_form, val, parent_key)
            if key_data:
                if isinstance(result.get(key), list):
                    result[key].append({key: key_data})
                elif result.get(key):
                    result[key] = [{key: result.get(key)}, {key: key_data}]
                else:
                    result[key] = key_data
        elif isinstance(val, list):
            for mapping_data in val:
                get_autofill_key_tree(schema_form, mapping_data, result)

    return result


def get_key_value(schema_form, val, parent_key):
    """Get key value.

    :param schema_form: Schema form
    :param val: Schema form value
    :param parent_key: The parent key
    :return: The key value
    """
    key_data = dict()
    if val.get("@value") is not None:
        value_key = val.get('@value')
        key_data['@value'] = get_autofill_key_path(
            schema_form,
            parent_key,
            value_key
        ).get('key')

    if val.get("@attributes") is not None:
        value_key = val.get('@attributes')
        if value_key.get("xml:lang") is not None:
            key_data['@language'] = get_autofill_key_path(
                schema_form,
                parent_key,
                value_key.get("xml:lang")
            ).get('key')
        if value_key.get("identifierType") is not None:
            key_data['@type'] = get_autofill_key_path(
                schema_form,
                parent_key,
                value_key.get("identifierType")
            ).get('key')
        if value_key.get("descriptionType") is not None:
            key_data['@type'] = get_autofill_key_path(
                schema_form,
                parent_key,
                value_key.get("descriptionType")
            ).get('key')
        if value_key.get("subjectScheme") is not None:
            key_data['@scheme'] = get_autofill_key_path(
                schema_form,
                parent_key,
                value_key.get("subjectScheme")
            ).get('key')
        if value_key.get("subjectURI") is not None:
            key_data['@URI'] = get_autofill_key_path(
                schema_form,
                parent_key,
                value_key.get("subjectURI")
            ).get('key')
        if value_key.get("dateType") is not None:
            key_data['@type'] = get_autofill_key_path(
                schema_form,
                parent_key,
                value_key.get("dateType")
            ).get('key')

    return key_data


def get_item_id(item_type_id):
    """Get dictionary contain item id.

    Get from mapping between item type and jpcoar
    :param item_type_id: The item type id
    :return: dictionary
    """
    def _get_jpcoar_mapping(rtn_results, jpcoar_data):
        for u, s in jpcoar_data.items():
            if rtn_results.get(u) is not None:
                data = list()
                if isinstance(rtn_results.get(u), list):
                    data = rtn_results.get(u)
                    data.append({u: {**s, "model_id": k}})
                else:
                    rtn_results.get(u)
                    data.append({u: rtn_results.get(u)})
                    data.append({u: {**s, "model_id": k}})
                rtn_results[u] = data
            else:
                rtn_results[u] = s
                rtn_results[u]['model_id'] = k

    results = dict()
    item_type_mapping = Mapping.get_record(item_type_id)
    try:
        for k, v in item_type_mapping.items():
            jpcoar = v.get("jpcoar_mapping")
            if isinstance(jpcoar, dict):
                _get_jpcoar_mapping(results, jpcoar)
    except Exception as e:
        current_app.logger.debug(e)
        results['error'] = str(e)

    return results


def get_cinii_autofill_item(item_id):
    """Get CiNii autofill item.

    :param item_id: Item ID.
    :return:
    """
    jpcoar_item = get_item_id(item_id)
    cinii_req_item = dict()
    
    for key in current_app.config.get("WEKO_ITEMS_AUTOFILL_CINII_REQUIRED_ITEM"):
        if jpcoar_item.get(key) is not None:
            cinii_req_item[key] = jpcoar_item.get(key)
    return cinii_req_item


def build_record_model(item_autofill_key, api_data):
    """Build record record_model.

    :param item_autofill_key: Item auto-fill key
    :param api_data: Api data
    :return: Record model list
    """
    def _build_record_model(_api_data, _item_autofill_key, _record_model_lst,
                            _filled_key):
        """Build record model.

        @param _api_data: Api data
        @param _item_autofill_key: Item auto-fill key
        @param _record_model_lst: Record model list
        """
        for k, v in _item_autofill_key.items():
            data_model = {}
            api_autofill_data = _api_data.get(k)
            if not api_autofill_data or k in _filled_key:
                continue
            if isinstance(v, dict):
                build_form_model(data_model, v)
            elif isinstance(v, list):
                for mapping_data in v:
                    _build_record_model(_api_data, mapping_data,
                                        _record_model_lst, _filled_key)
            record_model = {}
            for key, value in data_model.items():
                merge_dict(record_model, value)
            new_record_model = fill_data(record_model, api_autofill_data)
            if new_record_model:
                _record_model_lst.append(new_record_model)
                _filled_key.append(k)

    record_model_lst = list()
    filled_key = list()
    if not api_data or not item_autofill_key:
        return record_model_lst
    _build_record_model(api_data, item_autofill_key, record_model_lst,
                        filled_key)

    return record_model_lst


def merge_dict(original_dict, merged_dict, over_write=True):
    """Merge dictionary.

    @param original_dict: the original dictionary.
    @param merged_dict: the merged dictionary.
    @param over_write: the over write flag.
    """
    if isinstance(original_dict, list) and isinstance(merged_dict, list):
        for data in merged_dict:
            for data_1 in original_dict:
                merge_dict(data_1, data)
    elif isinstance(original_dict, dict) and isinstance(merged_dict, dict):
        for key in merged_dict:
            if key in original_dict:
                if isinstance(original_dict[key], (dict, list)) and isinstance(
                        merged_dict[key], (dict, list)):
                    merge_dict(original_dict[key], merged_dict[key])
                elif original_dict[key] == merged_dict[key]:
                    continue
                else:
                    if over_write:
                        merged_dict[key] = original_dict[key]
                    else:
                        current_app.logger.error('Conflict at "{}"'.format(key))
            else:
                original_dict[key] = merged_dict[key]


def get_autofill_key_path(schema_form, parent_key, child_key):
    """Get auto fill key path.

    :param schema_form: Schema form
    :param parent_key: Parent key
    :param child_key: Child key
    :return: The key path
    """
    result = dict()
    key_result = ''
    existed = False
    try:
        for item in schema_form:
            if item.get("key") == parent_key:
                items_list = item.get("items")
                for item_data in items_list:
                    if existed:
                        break
                    existed, key_result = get_specific_key_path(
                        child_key.split('.'), item_data)
        result['key'] = key_result
    except Exception as e:
        current_app.logger.debug(e)
        result['key'] = None
        result['error'] = str(e)

    return result


def get_specific_key_path(des_key, form):
    """Get specific path of des_key on form.

    @param des_key: Destination key
    @param form: The form key list
    @return: Existed flag and path result
    """
    existed = False
    path_result = None
    if isinstance(form, dict):
        list_keys = form.get("key", None)
        if list_keys:
            list_keys = list_keys.replace('[]', '').split('.')
            # Always remove the first element because it is parents key
            list_keys.pop(0)
            if set(list_keys) == set(des_key):
                existed = True
        if existed:
            return existed, form.get("key")
        elif not existed and form.get("items"):
            return get_specific_key_path(des_key, form.get("items"))
    elif isinstance(form, list):
        for child_form in form:
            if existed:
                break
            existed, path_result = get_specific_key_path(des_key, child_form)
    return existed, path_result


def build_form_model(form_model, form_key, autofill_key=None):
    """Build form model.

    @param form_model:
    @param form_key:
    @param autofill_key:
    """
    if isinstance(form_key, dict):
        for k, v in form_key.items():
            if isinstance(v, str) and v:
                arr = v.split('.')
                form_model[k] = {}
                build_form_model(form_model[k], arr, k)
    elif isinstance(form_key, list):
        if len(form_key) > 1:
            key = form_key.pop(0)
            build_model(form_model, key)
            key = key.replace("[]", "")
            if isinstance(form_model, dict):
                build_form_model(form_model[key], form_key,
                                 autofill_key)
            else:
                build_form_model(form_model[0].get(key), form_key,
                                 autofill_key)
        elif len(form_key) == 1:
            key = form_key.pop(0)
            if isinstance(form_model, list):
                form_model.append({key: autofill_key})
            elif isinstance(form_model, dict):
                form_model[key] = autofill_key


def build_model(form_model, form_key):
    """Build model.

    @param form_model:
    @param form_key:
    """
    child_model = {}
    if '[]' in form_key:
        form_key = form_key.replace("[]", "")
        child_model = []
    if isinstance(form_model, dict):
        form_model[form_key] = child_model
    else:
        form_model.append({form_key: child_model})


def fill_data(form_model, autofill_data):
    """Fill data to form model.

    @param form_model: the form model.
    @param autofill_data: the autofill data
    @param is_multiple_data: multiple flag.
    """
    result = {} if isinstance(form_model, dict) else []
    is_multiple_data = is_multiple(form_model, autofill_data)
    if isinstance(autofill_data, list):
        key = list(form_model.keys())[0] if len(form_model) != 0 else None
        if is_multiple_data or (not is_multiple_data and isinstance(form_model.get(key),list)):
            model_clone = {}
            deepcopy_API(form_model[key][0], model_clone)
            result[key]=[]
            for data in autofill_data:
                model = {}
                deepcopy_API(model_clone, model)
                new_model = fill_data(model, data)
                result[key].append(new_model.copy())
        else:
            result = fill_data(form_model, autofill_data[0])
    elif isinstance(autofill_data, dict):
        if isinstance(form_model, dict):
            for k, v in form_model.items():
                if isinstance(v, str):
                    result[k] = autofill_data.get(v,'')
                else:
                    new_v = fill_data(v, autofill_data)
                    result[k] = new_v
        elif isinstance(form_model, list):
            for v in form_model:
                new_v = fill_data(v, autofill_data)
                result.append(new_v)
    else:
        return
    return result

def deepcopy_API(original_object, new_object):
    """Copy dictionary object.

    @param original_object: the original object.
    @param new_object: the new object.
    @return:
    """
    import copy
    if isinstance(original_object, dict):
        for k, v in original_object.items():
            new_object[k] = copy.deepcopy(v)
    elif isinstance(original_object, list):
        for original_data in original_object:
            if isinstance(original_data, (dict, list)):
                deepcopy_API(copy.deepcopy(original_data), new_object)
    else:
        return


def is_multiple(form_model, autofill_data):
    """Check form model.

    @param form_model: Form model data.
    @param autofill_data: Autofill data.
    @return: True if form model can auto-fill with multiple data.
    """
    if isinstance(autofill_data, list) and len(autofill_data) > 1:
        for key in form_model:
            return isinstance(form_model[key], list)
    else:
        return False


def get_jalc_record_data(doi, item_type_id):
    """Get record data base on jalc API.

    :param doi: The jalc doi
    :param item_type_id: The item type ID
    :return:
    """
    result = list()
    api_response = JALCURL(doi).get_data()
    if api_response["error"] \
            or not isinstance(api_response['response'], dict):
        return result
    api_data = get_jalc_data_by_key(api_response, 'all')
    items = ItemTypes.get_by_id(item_type_id)

    if items is None:
        return result
    elif items.form is not None:
        autofill_key_tree = get_autofill_key_tree(
            items.form, get_cinii_autofill_item(item_type_id))
        result = build_record_model(autofill_key_tree, api_data)
    return result


def get_jalc_data_by_key(api, keyword):
    """Get data from jalc based on keyword.

    :param: api: jalc data
    :param: keyword: keyword for search
    :return: data for keyword
    """
    import json
    data_response = api['response']
    result = dict()
    if data_response is None:
        return result
    data = data_response
    if keyword == 'title' and data['data']['title_list'][0]:
        result[keyword] = get_jalc_title_data(data['data']['title_list'][0])
    elif keyword == 'creator' and data['data']['creator_list']:
        result[keyword] = get_jalc_creator_data(data['data']['creator_list'])
    elif keyword == 'sourceTitle' and data['data']['journal_title_name_list']:

        result[keyword] = get_jalc_subject_data(data['data']['journal_title_name_list'])
    elif keyword == 'volume' and data['data'].get('volume'):
        result[keyword] = pack_single_value_as_dict(data['data'].get('volume'))
    elif keyword == 'issue' and data['data'].get('issue'):
        result[keyword] = pack_single_value_as_dict(data['data'].get('issue'))
    elif keyword == 'pageStart' and data['data'].get('first_page'):
        result[keyword] = get_jalc_page_data(data['data'].get('first_page'))
    elif keyword == 'pageEnd' and data['data'].get('last_page'):
        result[keyword] = get_jalc_page_data(data['data'].get('last_page'))
    elif keyword == 'numPages':
        result[keyword] = get_jalc_numpage(
            data['data'].get('first_page'), data['data'].get('last_page'))
    elif keyword == 'date' and data['data'].get('date'):
        result[keyword] = get_jalc_date_data(
            data['data'].get('date'))
    elif keyword == 'publisher' and data['data'].get('publisher_list'):
        result[keyword] = get_jalc_publisher_data(data['data'].get('publisher_list'))
    elif keyword == 'sourceIdentifier' and data['data'].get('journal_id_list'):
        result[keyword] = pack_data_with_multiple_type_jalc(
            data['data'].get('journal_id_list')
        )
    elif keyword == "relation" and data['data'].get('doi'):
        result[keyword] = get_jalc_product_identifier(
            data['data'].get('doi')
        )
    elif keyword == 'all':
        for key in current_app.config.get("WEKO_ITEMS_AUTOFILL_CINII_REQUIRED_ITEM"):
            result[key] = get_jalc_data_by_key(api, key).get(key)
    return result


def get_jalc_publisher_data(data):
    """Get title data from jalc.

    Get title name and form it as format:
    {
        '@value': name,
        '@language': language
    }

    :param: data: marker data
    :return:packed data
    """
    result = list()
    default_language = 'en'
    for item in data:
        new_data = dict()
        new_data['@value'] = item['publisher_name']
        new_data['@language'] = item['lang'] if item['lang'] else default_language
        result.append(new_data)


def get_jalc_title_data(data):
    """Get title data from jalc.

    Get title name and form it as format:
    {
        '@value': name,
        '@language': language
    }

    :param: data: marker data
    :return:packed data
    """
    result = list()
    default_language = 'en'
    new_data = dict()
    new_data['@value'] = data['title']
    new_data['@language'] = data['lang'] if data['lang'] else default_language
    result.append(new_data)
    return result


def get_jalc_creator_data(data):
    """Get creator data from jalc.

    Get creator name and form it as format:
    {
        '@value': name,
        '@language': language
    }

    :param: data: creator data
    :return: list of creator name
    """
    result = list()
    default_language = 'ja'

    for item in data:
        if 'names' in item:
            result_creator = []
            for name_entry in item['names']:
                new_data = dict()
                full_name = name_entry['last_name'] + ' ' + name_entry['first_name']
                new_data['@value'] = full_name
                new_data['@language'] = name_entry['lang'] if name_entry['lang'] else default_language
                result_creator.append(new_data)
            result.append(result_creator)
    return result


def get_jalc_contributor_data(data):
    """Get contributor data from jalc.

    Get contributor name and form it as format:
    {
        '@value': name,
        '@language': language
    }

    :param: data: marker data
    :return:packed data
    """
    result = list()
    for item in data:
        name_data = item
        if name_data:
            result.append(get_basic_cinii_data(name_data))
    return result


def get_jalc_description_data(data):
    """Get description data from jalc.

    Get description and form it as format:
    {
        '@value': description,
        '@language': language,
        '@type': type of description
    }

    :param: description data
    :return: packed data
    """
    result = list()
    default_language = 'ja'
    default_type = 'Abstract'

    new_data = dict()
    new_data['@value'] = data
    new_data['@type'] = default_type
    new_data["@language"] = default_language
    result.append(new_data)
    return result


def get_jalc_subject_data(data):
    """Get subject data from jalc.

    Get subject and form it as format:
    {
        '@value': title,
        '2language': language,
        '@scheme': scheme of subject
        '@URI': source of subject
    }

    :param: data: subject data
    :return: packed data
    """
    result = list()
    default_language = 'ja'
    for sub in data:
        new_data = dict()
        new_data["@type"] = sub['type']
        new_data["@value"] = sub['journal_title_name']
        new_data['@language'] = sub['lang'] if sub['lang'] else default_language
        result.append(new_data)
    return result


def get_jalc_page_data(data):
    """Get start page and end page data.

    Get page info and pack it:
    {
        '@value': number
    }

    :param: data: No of page
    :return: packed data
    """
    try:
        result = int(data)
        return pack_single_value_as_dict(str(result))
    except Exception as e:
        current_app.logger.debug(e)
        return pack_single_value_as_dict(None)


def get_jalc_numpage(startingPage, endingPage):
    """Get number of page.

    If jalc have pageRange, get number of page
    If not, number of page equals distance between start and end page

    :param: data: jalc data
    :return: number of page is packed
    """  
    if startingPage and endingPage:
        try:
            end = int(endingPage)
            start = int(startingPage)
            num_pages = end - start + 1
            return pack_single_value_as_dict(str(num_pages))
        except Exception as e:
            current_app.logger.debug(e)
            return pack_single_value_as_dict(None)
    return {"@value": None}


def get_jalc_date_data(data):
    """Get publication date.

    Get publication date from jalc data
    format:
    {
        '@value': date
        '@type': type of date
    }

    :param: data: date
    :return: date and date type is packed
    """
    result = dict()
    if len(data.split('-')) != 3:
        result['@value'] = None
        result['@type'] = None
    else:
        result['@value'] = data
        result['@type'] = 'Issued'
    return result


def pack_data_with_multiple_type_jalc(data):
    """Map jalc multi data with type.

    Arguments:
        data1
        type1
        data2
        type2

    Returns:
        packed data

    """
    result = list()
    new_data = dict()

    for sub in data:
        new_data = dict()
        new_data["@type"] = sub['type']
        new_data["@value"] = sub['journal_id']
        result.append(new_data)
    return result


def get_jalc_product_identifier(data):
    result = list()
    new_data = dict()
    new_data['@value'] = data
    result.append(new_data)
    return result


def get_datacite_record_data(doi, item_type_id):
    """Get record data base on DATACITE API.

    :param doi: The DATACITE doi
    :param item_type_id: The item type ID
    :return:
    """
    result = list()

    api_response = DATACITEURL(doi).get_data()
    if api_response["error"] \
            or not isinstance(api_response['response'], dict):
        return result
    api_data = get_datacite_data_by_key(api_response, 'all')
    items = ItemTypes.get_by_id(item_type_id)
    if items is None:
        return result
    elif items.form is not None:
        autofill_key_tree = get_autofill_key_tree(
            items.form, get_cinii_autofill_item(item_type_id))
        result = build_record_model(autofill_key_tree, api_data) 
    return result


def get_datacite_data_by_key(api, keyword):
    """Get data from DATACITE based on keyword.

    :param: api: DATACITE data
    :param: keyword: keyword for search
    :return: data for keyword
    """
    import json
    data_response = api['response']
    result = dict()
    if data_response is None:
        return result
    data = data_response
    if keyword == 'title' and data['data']['attributes'].get('titles'):
        result[keyword] = get_datacite_title_data(data['data']['attributes'].get('titles'))
    elif keyword == 'creator' and data['data']['attributes'].get('creators'):
        result[keyword] = get_datacite_creator_data(data['data']['attributes'].get('creators'))
    elif keyword == 'contributor' and data['data']['attributes'].get('contributors'):
        result[keyword] = get_datacite_contributor_data(data['data']['attributes'].get('contributors'))
    elif keyword == 'description' and data['data']['attributes'].get('descriptions'):
        result[keyword] = get_datacite_description_data(
            data['data']['attributes'].get('descriptions')
        )    
    elif keyword == 'subject' and data['data']['attributes'].get('subjects'):
        result[keyword] = get_datacite_subject_data(data['data']['attributes'].get('subjects'))
    elif keyword == 'sourceTitle' and data['data']['attributes'].get('publisher'):
        result[keyword] = get_datacite_publisher_data(
            data['data']['attributes'].get('publisher')
        )
    elif keyword == 'sourceIdentifier' and data['data']['attributes'].get('identifiers'):
        result[keyword] = pack_data_with_multiple_type_datacite(
            data['data']['attributes'].get('identifiers')
        )
    elif keyword == "relation" and data['data'].get('id'):
        result[keyword] = get_datacite_product_identifier(
            data['data'].get('id')
        )
    elif keyword == 'all':
        for key in current_app.config.get("WEKO_ITEMS_AUTOFILL_CINII_REQUIRED_ITEM"):
            result[key] = get_datacite_data_by_key(api, key).get(key)
    return result


def get_datacite_publisher_data(data):
    """Get title data from datacite.

    Get title name and form it as format:
    {
        '@value': name,
        '@language': language
    }

    :param: data: marker data
    :return:packed data
    """
    result = list()
    default_language = 'en'
    new_data = dict()
    new_data["@type"] = data
    
    new_data['@language'] = default_language
    
    result.append(new_data)
    return result


def get_datacite_title_data(data):
    """Get title data from datacite.

    Get title name and form it as format:
    {
        '@value': name,
        '@language': language
    }

    :param: data: marker data
    :return:packed data
    """
    result = list()
    default_language = 'ja'
    for title in data:
        new_data = dict()
        new_data["@value"] = title['title']
        
        new_data['@language'] = title.get('lang', default_language)
        
        result.append(new_data)
    return result


def get_datacite_creator_data(data):
    """Get creator data from datacite.

    Get creator name and form it as format:
    {
        '@value': name,
        '@language': language
    }

    :param: data: creator data
    :return: list of creator name
    """
    result = list()
    default_language = 'ja'
    for item in data:
        if 'name' in item:
            result_creator = list()
            new_data = dict()
            new_data['@value'] = item['name']
            new_data['@language'] = default_language
            
            result_creator.append(new_data)
            result.append(result_creator)
    return result


def get_datacite_contributor_data(data):
    """Get contributor data from datacite.

    Get contributor name and form it as format:
    {
        '@value': name,
        '@language': language
    }

    :param: data: marker data
    :return:packed data
    """
    result = list()
    default_language = 'ja'
    for item in data:
        if 'name' in item:
            result_creator = list()
            new_data = dict()
            new_data['@value'] = item['name']
            new_data['@language'] = default_language
            
            result_creator.append(new_data)
            result.append(result_creator)
    return result


def get_datacite_description_data(data):
    """Get description data from datacite.

    Get description and form it as format:
    {
        '@value': description,
        '@language': language,
        '@type': type of description
    }

    :param: description data
    :return: packed data
    """
    result = list()
    default_language = 'ja'
    default_type = 'Abstract'
    for item in data:
        if 'description' in item:
            result_creator = list()
            new_data = dict()
            new_data['@value'] = item['description']
            new_data['@language'] = default_language
            
            result_creator.append(new_data)
            result.append(result_creator)
    return result


def get_datacite_subject_data(data):
    """Get subject data from datacite.

    Get subject and form it as format:
    {
        '@value': title,
        '2language': language,
        '@scheme': scheme of subject
        '@URI': source of subject
    }

    :param: data: subject data
    :return: packed data
    """
    result = list()
    default_language = 'ja'
    for sub in data:
        if 'subject' in sub: 
            result_creator = list()
            new_data = dict()
            new_data['@value'] = sub['subject'] 
            new_data['@subjectScheme'] = sub['subjectScheme']
            
            result_creator.append(new_data)
            result.append(result_creator)
    return result


def get_datacite_date_data(data):
    """Get publication date.

    Get publication date from datacite data
    format:
    {
        '@value': date
        '@type': type of date
    }

    :param: data: date
    :return: date and date type is packed
    """
    result = dict()

    result = dict()
    if len(data.split('-')) != 3:
        result['@value'] = None
        result['@type'] = None
    else:
        result['@value'] = data
        result['@type'] = 'Issued'
    return result


def pack_data_with_multiple_type_datacite(data):
    """Map datacite multi data with type.

    Arguments:
        data

    Returns:
        packed data

    """
    result = list()
    if data:
        new_data = dict()
        new_data['@value'] = data
        new_data['@type'] = "DOI"
        result.append(new_data)
    else:
        new_data = dict()
        new_data['@value'] = None
        new_data['@type'] = None
        result.append(new_data)
    return result


def get_datacite_product_identifier(data):

    result = list()
    if data:
        new_data = dict()
        new_data['@value'] = data
        new_data['@type'] = "DOI"
        result.append(new_data)
    else:
        new_data = dict()
        new_data['@value'] = None
        new_data['@type'] = None
        result.append(new_data)
    return result
    