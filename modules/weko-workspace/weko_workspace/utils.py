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

from functools import wraps
from datetime import datetime,timezone
import traceback
from elasticsearch_dsl.query import Q
from elasticsearch.exceptions import TransportError
from invenio_cache import current_cache
from invenio_search import RecordsSearch
from jsonschema import validate, ValidationError
from flask import current_app
from flask_babelex import gettext as _
from flask_security import current_user
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier
from sqlalchemy.exc import SQLAlchemyError
from weko_schema_ui.models import PublishStatus
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
from .api import CiNiiURL, JALCURL, DATACITEURL, JamasURL
from lxml import etree

def is_update_cache():
    """Return True if Autofill Api has been updated.
    
    Returns:
        bool: True if the Autofill API has been updated, False otherwise.
    """
    return current_app.config['WEKO_WORKSPACE_AUTOFILL_API_UPDATED']

def cached_api_json(timeout=50, key_prefix="cached_api_json"):
    """Cache Api response data.

    Args:
        timeout (int): Cache timeout in seconds.
        key_prefix (str): Prefix for the cache key.
    Returns:
        function: Decorator function to cache API responses.
    """
    def caching(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            key = key_prefix
            for value in args:
                key += str(value)
            cache_fun = current_cache.cached(
                timeout=timeout,
                key_prefix=key,
                forced_update=is_update_cache,
            )
            if current_cache.get(key) is None:
                data = cache_fun(f)(*args, **kwargs)
                current_cache.set(key, data)
                return data
            else:
                return current_cache.get(key)

        return wrapper

    return caching


def get_workspace_filterCon():
    """
    Retrieves the default filtering conditions for the current user.

    Returns:
        tuple(dict, bool):
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
        TransportError: If an error occurs during the Elasticsearch query, returns `None`.
        Exception: If any other unexpected error occurs, returns `None`.
    """
    try:
        size = 10000
        search_index = current_app.config["WEKO_WORKSPACE_ITEM_SEARCH_INDEX"]
        search_type = current_app.config["WEKO_WORKSPACE_ITEM_SEARCH_TYPE"]
        search_obj = RecordsSearch(index=search_index, doc_type=search_type)
        search = search_obj.with_preference_param().params(version=True)

        # Set the search query
        publish_status_match = Q("terms", publish_status=[
            PublishStatus.PUBLIC.value, PublishStatus.PRIVATE.value
        ])
        user_id = (
            current_user.get_id()
            if current_user and current_user.is_authenticated
            else None
        )
        creator_user_match = Q("match", weko_creator_id=user_id)
        shared_user_match = Q("match", weko_shared_id=user_id)
        shuld = []
        shuld.append(Q("bool", must=[publish_status_match, creator_user_match]))
        shuld.append(Q("bool", must=[publish_status_match, shared_user_match]))
        must = []
        must.append(Q("bool", should=shuld))
        must.append(Q("bool", must=Q("match", relation_version_is_last="true")))
        search = search.filter(Q("bool", must=must))
        search = search.query(Q("bool", must=Q("match_all")))

        # Set size / Exclude content field from the source
        src = {
            "size": size,
            "_source": {"excludes": ["content"]}
        }
        search._extra.update(src)

        # Set sorting
        search = search.sort("-control_number")

        # Execute search. Use search_after to retrieve all records
        records = []
        current_app.logger.debug(f"[workspace] search obj: {search.to_dict()}")
        page = search.execute().to_dict()
        current_app.logger.debug(f"[workspace] search result: {page}")
        while page.get('hits', {}).get('hits', []):
            records.extend(page.get('hits', {}).get('hits', []))
            if len(page.get('hits', {}).get('hits', [])) < size:
                break
            search = search.extra(search_after=page.get('hits', {}).get('hits', [])[-1].get('sort'))
            current_app.logger.debug(f"[workspace] search obj: {search.to_dict()}")
            page = search.execute().to_dict()
            current_app.logger.debug(f"[workspace] search result: {page}")
        return records

    except TransportError as e:
        traceback.print_exc()
        current_app.logger.error(f"Failed to get workflow item list from ES: {e} / {search.to_dict()}")
        return None
    except Exception as e:
        traceback.print_exc()
        current_app.logger.error(e)
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
def get_item_status(recId: str, file_info: dict):
    """
    Get the converted OA status for a given recid.

    Args:
        recId (str): The record ID (WEKO item PID or related identifier).
        file_info (dict): A dictionary containing file information.

    Returns:
        str: The converted OA status based on the mapping, defaults to "Unlinked" if not found.
    """
    # recIdをwekoItemPidとしてそのまま使用（文字列として受け取る）
    wekoItemPid = recId

    # 元のメソッドを呼び出してOA状態を取得
    oaStatusRecord = OaStatus.get_oa_status_by_weko_item_pid(wekoItemPid)

    # レコードが存在しない場合、"Unlinked"を返す
    if oaStatusRecord is None:
        return _("Unlinked")

    # 元の状態を取得し、変換を行う
    originalStatus = oaStatusRecord.oa_status

    # Check embargo item status
    if originalStatus == "Processed Fulltext Registered (Embargo)":
        is_embargo = False
        if file_info.get('date'):
            date_value = file_info['date'][0].get('dateValue')
            if date_value:
                is_embargo =\
                    date_value > datetime.now(timezone.utc).strftime('%Y-%m-%d')
        originalStatus = originalStatus if is_embargo \
            else "Processed Fulltext Opened (OA)"
    replaced_status = current_app.config.get("WEKO_WORKSPACE_OA_STATUS_MAPPING")\
                                        .get(originalStatus, "Unlinked")

    return replaced_status


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
        jamas_xml_data_keys = current_app.config.get(
            "WEKO_WORKSPACE_AUTOFILL_JAMAS_XML_DATA_KEYS", {}
        )
        for elem in root.getiterator():
            localname = etree.QName(elem).localname
            if elem.text and localname in jamas_xml_data_keys.keys():
                data = result.get(localname, None)
                is_multiple = jamas_xml_data_keys.get(localname)
                if is_multiple:
                    if not data:
                        data = []
                    data.append(elem.text)
                elif not data:
                    data = elem.text
                result[localname] = data
        rtn_data['response'] = result
    except Exception as e:
        rtn_data['error'] = str(e)
    return rtn_data


@cached_api_json(timeout=50, key_prefix="jamas_data")
def get_jamas_record_data(doi, item_type_id, exclude_duplicate_lang=True):
    """Get record data base on Jamas API.

    Args:
        doi (str): The Jamas DOI.
        item_type_id (int): The item type ID.
        exclude_duplicate_lang (bool): Whether to exclude duplicate languages in the result.

    Returns:
        list: A list of dictionaries containing the record data.
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
    from weko_items_autofill.utils import sort_by_item_type_order
    if items is None:
        return result
    elif items.form is not None:
        autofill_key_tree = sort_by_item_type_order(
            items.form,
            get_autofill_key_tree(
                items.form,
                get_jamas_autofill_item(item_type_id)))
        result = build_record_model(
            autofill_key_tree, api_data, items.schema, exclude_duplicate_lang
        )

    return result


def get_jamas_autofill_item(item_type_id):
    """Get Jamas autofill item.

    Args:
        item_type_id (int): The item type ID.
    
    Returns:
        dict: A dictionary containing the Jamas required item data.
    """
    jpcoar_item = get_item_id(item_type_id)
    jamas_req_item = dict()
    for key in current_app.config[
            'WEKO_WORKSPACE_AUTOFILL_JAMAS_REQUIRED_ITEM']:
        if jpcoar_item.get(key) is not None:
            jamas_req_item[key] = jpcoar_item.get(key)
    return jamas_req_item


def get_jamas_data_by_key(api, keyword):
    """Get Jamas data based on keyword.

    Args:
        api (dict): Jamas data response.
        keyword (str): Keyword for search.

    Returns:
        dict: Jamas data for the specified keyword.

    """
    if api['error'] or api['response'] is None:
        return None

    data = api['response']
    language = get_jamas_language_data(data.get('language'))
    result = dict()
    if keyword == 'title' and data.get('title'):
        result[keyword] = pack_with_language_value_for_jamas(
            data.get('title'), language
        )
    elif keyword == 'creator' and data.get('creator'):
        result[keyword] = get_jamas_creator_data(
            data.get('creator'), language
        )
    elif keyword == 'sourceTitle' and data.get('publicationName'):
        result[keyword] = pack_with_language_value_for_jamas(
            data.get('publicationName'), language
        )
    elif keyword == 'volume' and data.get('volume'):
        result[keyword] = pack_single_value_for_jamas(data.get('volume'))
    elif keyword == 'issue' and data.get('number'):
        result[keyword] = pack_single_value_for_jamas(data.get('number'))
    elif keyword == 'pageStart' and data.get('startingPage'):
        result[keyword] = pack_single_value_for_jamas(data.get('startingPage'))
    elif keyword == 'numPages':
        result[keyword] = pack_single_value_for_jamas(data.get('pageRange'))
    elif keyword == 'date' and data.get('publicationDate'):
        result[keyword] = get_jamas_issue_date(data.get('publicationDate'))
    elif keyword == 'relation':
        result[keyword] = get_jamas_relation_data(
            data.get('issn'),
            data.get('eIssn'),
            data.get('doi')
        )
    elif keyword == 'sourceIdentifier':
        result[keyword] = get_jamas_source_data(data.get('issn'))
    elif keyword == 'publisher':
        result[keyword] = pack_with_language_value_for_jamas(
            data.get('publisher'), language
        )
    elif keyword == 'description' and data.get('description'):
        result[keyword] = pack_with_language_value_for_jamas(
            data.get('description'), language
        )
    elif keyword == 'all':
        for key in current_app.config[
                'WEKO_WORKSPACE_AUTOFILL_JAMAS_REQUIRED_ITEM']:
            result[key] = get_jamas_data_by_key(api, key).get(key)
    return result

def pack_single_value_for_jamas(data):
    """Pack single value for Jamas.

    Args:
        data (str or list): A single value or a list of values to be packed.

    Returns:
        list: A list containing dictionaries with the value.
    """
    result = []
    if isinstance(data, str):
        result.append({
            '@value': data
        })
    elif isinstance(data, list):
        for d in data:
            new_data = {}
            new_data['@value'] = d
            result.append(new_data)
    return result


def pack_with_language_value_for_jamas(data, language="en"):
    """Pack data with language value for Jamas.

    Args:
        data (str or list): A string or a list of strings to be packed.
        language (str): The language of the article. Defaults to "en".

    Returns:
        list: A list containing dictionaries with value and language.
    """
    result = []
    if isinstance(data, str):
        result.append({
            '@value': data,
            '@language': language
        })
    elif isinstance(data, list):
        for d in data:
            result.append({
                '@value': d,
                '@language': language
            })
    return result

def get_jamas_source_data(data):
    """Get Jamas source data.

    Args:
        data (str or list): A source identifier string or a list of identifiers.

    Returns:
        list: A list containing dictionaries with source identifier values and their types.
    """
    result = []
    
    if isinstance(data, str):
        result.append({
            '@value': data,
            '@type': "ISSN"
        })
    elif isinstance(data, list):
        for d in data:
            result.append({
                '@value': d,
                '@type': "ISSN"
            })
    return result


def get_jamas_relation_data(issn, eissn, doi):
    """Get Jamas relation data.

    Args:
        issn (str or list): ISSN or a list of ISSNs.
        eissn (str or list): EISSN or a list of EISSNs.
        doi (str or list): DOI or a list of DOIs.

    Returns:
        list: A list of dictionaries containing the relation data with types.
    """
    result = []
    # doi
    if isinstance(doi, str):
        result.append({
            '@value': doi,
            '@type': "DOI"
        })
    elif isinstance(doi, list):
        for d in doi:
            result.append({
                '@value': d,
                '@type': "DOI"
            })

    #issn
    if isinstance(issn, str):
        result.append({
            '@value': issn,
            '@type': "ISSN"
        })
    elif isinstance(issn, list):
        for d in issn:
            result.append({
                '@value': d,
                '@type': "ISSN"
            })
    
    # eissn
    if isinstance(eissn, str):
        result.append({
            '@value': eissn,
            '@type': "EISSN"
        })
    elif isinstance(eissn, list):
        for d in eissn:
            result.append({
                '@value': d,
                '@type': "EISSN"
            })
    
    return result


def get_jamas_issue_date(data):
    """Get Jamas issued date.

    Args:
        data (str): The publication date string in the format "YYYY-MM-DD".

    Returns:
        dict: A dictionary containing the issued date and its type.

    """
    result = []
    if isinstance(data, str):
        result.append({
            '@value': data.replace('.', '-').replace("年", "-")\
                .replace("月", "-").replace("日", ""),
            '@type': "Issued"
        })
    elif isinstance(data, list):
        for d in data:
            result.append({
                '@value': d.replace('.', '-').replace("年", "-")\
                    .replace("月", "-").replace("日", ""),
                '@type': "Issued"
            })
    return result


def get_jamas_creator_data(data, language="en"):
    """Get creator name from Jamas data.

    Args:
        data (str or list): A creator name string or a list of creator names.
        language (str): The language of the article. Defaults to "en".

    Returns:
        list: A list containing dictionaries with creator names and their languages.

    """
    result = []
    if isinstance(data, str):
        result.append({
            '@value': data,
            '@language': language
        })
    elif isinstance(data, list):
        for d in data:
            result.append([{
                '@value': d,
                '@language': language
            }])
    return result


def get_jamas_language_data(data):
    """Get language data from Jamas.

    Args:
        data (list or str): A list of languages or a single language string.

    Returns:
        list: A list containing a dictionary with the language.
    """
    default_language = current_app.config.get(
        "WEKO_WORKSPACE_DATA_DEFAULT_LANGUAGE", "en"
    )
    if isinstance(data, str):
        result = data if data else default_language
    elif isinstance(data, list) and len(data) > 0:
        result = data[0] if data[0] else default_language
    else:
        result = default_language

    # Convert language codes to standard format
    if result in ["jpn", "japanese", "日本語"]:
        result = "ja"
    elif result in ["eng", "English", "英語"]:
        result = "en"
    else:
        pass

    return result


@cached_api_json(timeout=50, key_prefix="cinii_data")
def get_cinii_record_data(doi, item_type_id, exclude_duplicate_lang=True):
    """Get record data base on CiNii API.

    Args:
        doi (str): The CiNii DOI.
        item_type_id (int): The item type ID.
        exclude_duplicate_lang (bool): Whether to exclude duplicate languages in the result.

    Returns:
        list: A list of dictionaries containing the record data.
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
        result = build_record_model(
            autofill_key_tree, api_data, items.schema, exclude_duplicate_lang
        )
    return result


def get_cinii_data_by_key(api, keyword):
    """Get data from CiNii based on keyword.

    Args:
        api (dict): CiNii data response.
        keyword (str): Keyword for search.

    Returns:
        dict: CiNii data for the specified keyword.
    """
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
        for key in current_app.config.get("WEKO_WORKSPACE_CINII_REQUIRED_ITEM"):
            result[key] = get_cinii_data_by_key(api, key).get(key)
    return result


def get_cinii_product_identifier(data, type1, type2):
    """Identifier Mapping.

    Args:
        data (list): A list of identifiers.
        type1 (str): The first identifier type (e.g., 'cir:DOI').
        type2 (str): The second identifier type (e.g., 'cir:NAID').

    Returns:
        list: A list of dictionaries containing the identifiers with their types.
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

    Args:
        data (str or list): A string or a list of ISSNs.

    Returns:
        list: A list of dictionaries containing the ISSN values and their type.

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

    Args:
        data (str): The publication date string in the format "YYYY-MM-DD".

    Returns:
        dict: A dictionary containing the issued date and its type.
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

    Args:
        startingPage (str): The starting page number.
        endingPage (str): The ending page number.

    Returns:
        dict: A dictionary containing the number of pages.
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

    Args:
        data (str): The page number as a string.

    Returns:
        dict: A dictionary containing the page number.
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

    Args:
        data (str): The value to be packed.
    
    Returns:
        dict: A dictionary containing the value.
    """
    new_data = dict()
    new_data['@value'] = data
    return new_data


def get_cinii_subject_data(data, title):
    """Get subject data from CiNii.

    Get subject and form it as format:
    {
        '@value': title,
        '@language': language,
        '@scheme': scheme of subject
        '@URI': source of subject
    }

    Args:
        data (list): A list of subjects.
        title (str): The title of the item.
    
    Returns:
        list: A list of dictionaries containing the subject data.
    """
    result = list()
    for sub in data:
        new_data = dict()
        new_data["@scheme"] = "Other"
        new_data["@value"] = sub
        new_data["@language"] = current_app.config.get(
            "WEKO_WORKSPACE_DATA_DEFAULT_LANGUAGE", "en"
        )
        result.append(new_data)
    return result


def get_cinii_creator_data(data):
    """Get creator data from CiNii.

    Get creator name and form it as format:
    {
        '@value': name,
        '@language': language
    }

    Args:
        data (list): A list of creator names.
    
    Returns:
        list: A list of lists, each containing a dictionary with the creator name and language.
    """
    result = list()
    for item in data:
        name_data = item
        if name_data:
            result_creator = list()
            new_data = dict()
            new_data['@value'] = name_data
            new_data['@language'] = current_app.config.get(
                "WEKO_WORKSPACE_DATA_DEFAULT_LANGUAGE", "en"
            )
            result_creator.append(new_data)
            result.append(result_creator)
    return result


def get_cinii_title_data(data):
    """Get title data from CiNii.

    Get title name and form it as format:
    {
        '@value': name,
        '@language': language
    }

    Args:
        data (str): The title of the item.

    Returns:
        list: A list containing a dictionary with the title and its language.
    """
    result = list()
    new_data = dict()
    new_data['@value'] = data
    new_data['@language'] = current_app.config.get(
        "WEKO_WORKSPACE_DATA_DEFAULT_LANGUAGE", "en"
    )
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

    Args:
        data (str): The description of the item.

    Returns:
        list: A list containing a dictionary with the description, language, and type.
    """
    result = list()
    default_type = 'Abstract'
    new_data = dict()

    new_data['@value'] = data
    new_data['@type'] = default_type
    new_data["@language"] = current_app.config.get(
        "WEKO_WORKSPACE_DATA_DEFAULT_LANGUAGE", "en"
    )
    result.append(new_data)
    return result


def get_autofill_key_tree(schema_form, item, result=None):
    """Get auto fill key tree.

    Args:
        schema_form (dict): The schema form.
        item (dict): The item data to be processed.
        result (dict, optional): The result dictionary to store the processed data. Defaults to None.

    Returns:
        dict: A dictionary containing the processed data based on the schema form and item.
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

    Args:
        schema_form (dict): The schema form.
        val (dict): The value to be processed.
        parent_key (str): The parent key for the value.

    Returns:
        dict: A dictionary containing the key data based on the schema form and value.
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
    
    Args:
        item_type_id (int): The item type ID.
    
    Returns:
        dict: A dictionary containing the item ID and its corresponding jpcoar mapping.
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

    Args:
        item_id (int): The item ID.

    Returns:
        dict: A dictionary containing the CiNii required item data.
    """
    jpcoar_item = get_item_id(item_id)
    cinii_req_item = dict()

    for key in current_app.config.get("WEKO_WORKSPACE_CINII_REQUIRED_ITEM"):
        if jpcoar_item.get(key) is not None:
            cinii_req_item[key] = jpcoar_item.get(key)
    return cinii_req_item


def build_record_model(item_autofill_key, api_data, schema=None, exclude_duplicate_lang=False):
    """Build record record_model.

    Args:
        item_autofill_key (dict): The item auto-fill key.
        api_data (dict): The API data to be processed.
        schema (dict, optional): The schema for the record model. Defaults to None.
        exclude_duplicate_lang (bool, optional): Whether to exclude duplicate languages in the result. Defaults to False.

    Returns:
        list: A list of dictionaries containing the record model data.
    """
    def _build_record_model(_api_data, _item_autofill_key, _record_model_lst,
                            _filled_key, _schema, _exclude_duplicate_lang):
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
                    _build_record_model(
                        _api_data, mapping_data, _record_model_lst,
                        _filled_key, _schema, _exclude_duplicate_lang
                    )
            record_model = {}
            for key, value in data_model.items():
                merge_dict(record_model, value)
            new_record_model = fill_data(
                record_model, api_autofill_data, _schema, _exclude_duplicate_lang
            )
            if new_record_model:
                _record_model_lst.append(new_record_model)
                _filled_key.append(k)

    record_model_lst = list()
    filled_key = list()
    if not api_data or not item_autofill_key:
        return record_model_lst
    _build_record_model(api_data, item_autofill_key, record_model_lst,
                        filled_key, schema, exclude_duplicate_lang)

    return record_model_lst


def merge_dict(original_dict, merged_dict, over_write=True):
    """Merge dictionary.

    Args:
        original_dict (dict or list): The original dictionary or list to be merged.
        merged_dict (dict or list): The dictionary or list to merge into the original.
        over_write (bool, optional): Whether to overwrite existing values. Defaults to True.

    Returns:
        None: The function modifies the original_dict in place.
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

    Args:
        schema_form (list): The schema form list.
        parent_key (str): The parent key to search in the schema form.
        child_key (str): The child key to find the specific path.

    Returns:
        dict: A dictionary containing the key path result or an error message.
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

    Args:
        des_key (list): The desired key path to search for.
        form (dict or list): The form data to search in.
    
    Returns:
        tuple (existed, path_result):
            A tuple where `existed` is a boolean indicating if the key exists,
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

    Args:
        form_model (dict or list): The form model to be built.
        form_key (list or dict): The keys to build the form model.
        autofill_key (str, optional): The key to autofill the form model. Defaults to None.

    Returns:
        None: The function modifies the form_model in place.
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

    Args:
        form_model (dict or list): The form model to be built.
        form_key (str): The key to build the model.

    Returns:
        None: The function modifies the form_model in place.
    """
    child_model = {}
    if '[]' in form_key:
        form_key = form_key.replace("[]", "")
        child_model = []
    if isinstance(form_model, dict):
        form_model[form_key] = child_model
    else:
        form_model.append({form_key: child_model})


def fill_data(form_model, autofill_data, schema=None, exclude_duplicate_lang=False):
    """Fill data to form model.

    Args:
        form_model (dict or list): The form model to be filled.
        autofill_data (dict or list): The data to fill into the form model.
        schema (dict, optional): The schema for validation. Defaults to None.
        exclude_duplicate_lang (bool, optional): Whether to exclude duplicate languages in the result. Defaults to False.

    Returns:
        dict or list: The filled form model with the autofill data.
    """
    result = {} if isinstance(form_model, dict) else []
    is_multiple_data = is_multiple(form_model, autofill_data)

    def validate_data(data, sub_schema):
        if sub_schema is None:
            current_app.logger.debug("=== Validation skipped ===")
            return True
        try:
            validate(instance=data, schema=sub_schema)
            current_app.logger.debug(f"Validation passed: {data} matches schema {sub_schema}")
            return True
        except ValidationError as e:
            current_app.logger.debug(f"Validation failed: {e.message}")
            return False

    if isinstance(autofill_data, list):
        key = list(form_model.keys())[0] if len(form_model) != 0 else None
        sub_schema = None
        if schema:
            sub_schema = get_subschema(schema, key)
            if sub_schema and sub_schema.get("type") == "array":
                sub_schema = sub_schema.get("items")

        if is_multiple_data or (not is_multiple_data and isinstance(form_model.get(key),list)):
            model_clone = {}
            deepcopy_API(form_model[key][0], model_clone)
            result[key]=[]
            used_lang_set = set()
            for data in autofill_data:
                if exclude_duplicate_lang and isinstance(data, dict) and data.get('@language'):
                    if data.get('@language') in used_lang_set:
                        continue
                    used_lang_set.add(data.get('@language'))
                model = {}
                deepcopy_API(model_clone, model)
                new_model = fill_data(model, data, sub_schema, exclude_duplicate_lang)
                result[key].append(new_model.copy())
        else:
            result = fill_data(form_model, autofill_data[0], schema, exclude_duplicate_lang)
    elif isinstance(autofill_data, dict):
        if isinstance(form_model, dict):
            for k, v in form_model.items():
                subschema = get_subschema(schema, k)
                if isinstance(v, str):
                    value = autofill_data.get(v, '')
                    if not validate_data(value, subschema):
                        continue
                    result[k] = value
                else:
                    new_v = fill_data(v, autofill_data, subschema, exclude_duplicate_lang)
                    result[k] = new_v
        elif isinstance(form_model, list):
            for v in form_model:
                new_v = fill_data(v, autofill_data, schema, exclude_duplicate_lang)
                result.append(new_v)
    else:
        return
    return result


def get_subschema(schema, key):
    """Get sub schema.

    Args:
        schema (dict): The schema to search in.
        key (str): The key to search for.
    Returns:
        dict: The sub schema if found, otherwise None.
    """
    if not schema:
        return None

    if schema.get("type") == "object" and "properties" in schema:
        return schema["properties"].get(key)

    if schema.get("type") == "array" and "items" in schema:
        return get_subschema(schema["items"], key)

    return None


def deepcopy_API(original_object, new_object):
    """Copy dictionary object.

    Args:
        original_object (dict or list): The original object to be copied.
        new_object (dict or list): The new object to store the copied data.

    Returns:
        None: The function modifies the new_object in place.
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

    Args:
        form_model (dict or list): The form model to check.
        autofill_data (list): The data to check against the form model.

    Returns:
        bool: True if the form model is a list and has more than one item, False otherwise.
    """
    if isinstance(autofill_data, list) and len(autofill_data) > 1:
        for key in form_model:
            return isinstance(form_model[key], list)
    else:
        return False


@cached_api_json(timeout=50, key_prefix="jalc_data")
def get_jalc_record_data(doi, item_type_id, exclude_duplicate_lang=True):
    """Get record data base on jalc API.

    Args:
        doi (str): The DOI of the item.
        item_type_id (int): The item type ID.
        exclude_duplicate_lang (bool, optional): Whether to exclude duplicate languages in the result. Defaults to True.

    Returns:
        list: A list of dictionaries containing the record data from JALC.
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
            items.form, get_jalc_autofill_item(item_type_id))
        result = build_record_model(
            autofill_key_tree, api_data, schema=items.schema,
            exclude_duplicate_lang=exclude_duplicate_lang
        )
    current_app.logger.debug(f"[get_jalc_record_data] result={result}")
    return result


def get_jalc_data_by_key(api, keyword):
    """Get data from jalc based on keyword.

    Args:
        api (dict): The API response data.
        keyword (str): The keyword to search for in the API data.

    Returns:
        dict: A dictionary containing the data for the specified keyword.
    """
    data_response = api['response']
    result = dict()
    if data_response is None:
        return result
    data = data_response
    if keyword == 'title'\
        and data['data'].get('title_list')\
        and data['data']['title_list'][0]:
        result[keyword] = get_jalc_title_data(data['data']['title_list'][0])
    elif keyword == 'creator' and data['data'].get('creator_list'):
        result[keyword] = get_jalc_creator_data(data['data']['creator_list'])
    elif keyword == 'sourceTitle' and data['data'].get('journal_title_name_list'):
        result[keyword] = get_jalc_source_title_data(data['data']['journal_title_name_list'])
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
        for key in current_app.config.get("WEKO_WORKSPACE_JALC_REQUIRED_ITEM"):
            result[key] = get_jalc_data_by_key(api, key).get(key)
    return result


def get_jalc_publisher_data(data):
    """Get title data from jalc.

    Get title name and form it as format:
    {
        '@value': name,
        '@language': language
    }

    Args:
        data (list): A list of publisher names.
    
    Returns:
        list: A list of dictionaries containing the publisher names and their languages.
    """
    result = list()
    default_language = current_app.config.get(
        "WEKO_WORKSPACE_DATA_DEFAULT_LANGUAGE", "en"
    )
    for item in data:
        new_data = dict()
        new_data['@value'] = item.get('publisher_name')
        new_data['@language'] = item.get('lang', default_language)
        result.append(new_data)
    return result


def get_jalc_title_data(data):
    """Get title data from jalc.

    Get title name and form it as format:
    {
        '@value': name,
        '@language': language
    }

    Args:
        data (dict): The title data containing the title and language.

    Returns:
        list: A list containing a dictionary with the title and its language.
    """
    result = list()
    default_language = current_app.config.get(
        "WEKO_WORKSPACE_DATA_DEFAULT_LANGUAGE", "en"
    )
    new_data = dict()
    new_data['@value'] = data.get('title')
    new_data['@language'] = data.get('lang', default_language)
    result.append(new_data)
    return result


def get_jalc_creator_data(data):
    """Get creator data from jalc.

    Get creator name and form it as format:
    {
        '@value': name,
        '@language': language
    }

    Args:
        data (list): A list of creator names.

    Returns:
        list: A list of lists, each containing a dictionary with the creator names and languages.
    """
    result = list()
    default_language = current_app.config.get(
        "WEKO_WORKSPACE_DATA_DEFAULT_LANGUAGE", "en"
    )

    for item in data:
        if 'names' in item:
            result_creator = []
            for name_entry in item['names']:
                new_data = dict()
                full_name = name_entry.get('last_name',"") + ' ' + name_entry.get('first_name',"")
                new_data['@value'] = full_name
                new_data['@language'] = name_entry.get('lang', default_language)
                result_creator.append(new_data)
            result.append(result_creator)
    return result


def get_jalc_source_title_data(data):
    """Get source title data from jalc.

    Get title and form it as format:
    {
        '@value': title,
        '@language': language,
    }

    Args:
        data (list): A list of source titles.

    Returns:
        list: A list of dictionaries containing the source title data.
    """
    result = list()
    default_language = current_app.config.get(
        "WEKO_WORKSPACE_DATA_DEFAULT_LANGUAGE", "en"
    )
    for sub in data:
        new_data = dict()
        new_data["@value"] = sub.get('journal_title_name')
        new_data['@language'] = sub.get('lang', default_language)
        result.append(new_data)
    return result


def get_jalc_page_data(data):
    """Get start page and end page data.

    Get page info and pack it:
    {
        '@value': number
    }

    Args:
        data (str): The page number as a string.

    Returns:
        dict: A dictionary containing the page number packed as '@value'.
    """
    try:
        result = int(data)
        return pack_single_value_as_dict(str(result))
    except Exception as e:
        current_app.logger.error(e)
        return pack_single_value_as_dict(None)


def get_jalc_numpage(startingPage, endingPage):
    """Get number of page.

    If jalc have pageRange, get number of page
    If not, number of page equals distance between start and end page

    Args:
        startingPage (str): The starting page number as a string.
        endingPage (str): The ending page number as a string.
    
    Returns:
        dict: A dictionary containing the number of pages packed as '@value'.
    """
    if startingPage and endingPage:
        try:
            end = int(endingPage)
            start = int(startingPage)
            num_pages = end - start + 1
            return pack_single_value_as_dict(str(num_pages))
        except Exception as e:
            current_app.logger.error(e)
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

    Args:
        data (str): The publication date in the format 'YYYY-MM-DD'.

    Returns:
        dict: A dictionary containing the publication date packed as '@value' and its type as '@type'.
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

    Args:
        data (list): A list of dictionaries containing journal IDs and their types.

    Returns:
        list: A list of dictionaries, each containing the type and journal ID.

    """
    result = list()
    new_data = dict()

    for sub in data:
        new_data = dict()
        new_data["@type"] = sub.get('type')
        new_data["@value"] = sub.get('journal_id')
        result.append(new_data)
    return result


def get_jalc_product_identifier(data):
    """Get product identifier from jalc.

    Args:
        data (str): The DOI of the item.
    
    Returns:
        list: A list containing a dictionary with the product identifier packed as '@value'.
    """
    result = list()
    new_data = dict()
    new_data['@value'] = data
    result.append(new_data)
    return result


def get_jalc_autofill_item(item_id):
    """Get JaLC autofill item.
    
    Args:
        item_id (int): The item ID.
        
    Returns:
        dict: A dictionary containing the JaLC required item data.
    """
    jpcoar_item = get_item_id(item_id)
    jalc_req_item = dict()

    for key in current_app.config.get("WEKO_WORKSPACE_JALC_REQUIRED_ITEM"):
        if jpcoar_item.get(key) is not None:
            jalc_req_item[key] = jpcoar_item.get(key)
    return jalc_req_item


@cached_api_json(timeout=50, key_prefix="datacite_data")
def get_datacite_record_data(doi, item_type_id, exclude_duplicate_lang=True):
    """Get record data base on DATACITE API.

    Args:
        doi (str): The DOI of the item.
        item_type_id (int): The item type ID.
        exclude_duplicate_lang (bool, optional): Whether to exclude duplicate languages in the result. Defaults to True.

    Returns:
        list: A list of dictionaries containing the record data from DATACITE.
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
            items.form, get_datacite_autofill_item(item_type_id))
        result = build_record_model(
            autofill_key_tree, api_data, items.schema, exclude_duplicate_lang
        )
    return result


def get_datacite_data_by_key(api, keyword):
    """Get data from DATACITE based on keyword.

    Args:
        api (dict): The API response data.
        keyword (str): The keyword to search for in the API data.

    Returns:
        dict: A dictionary containing the data for the specified keyword.
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
        for key in current_app.config.get("WEKO_WORKSPACE_DATACITE_REQUIRED_ITEM"):
            result[key] = get_datacite_data_by_key(api, key).get(key)
    return result


def get_datacite_publisher_data(data):
    """Get title data from datacite.

    Get title name and form it as format:
    {
        '@value': name,
        '@language': language
    }

    Args:
        data (str): The publisher name.

    Returns:
        list: A list containing a dictionary with the publisher name and its language.
    """
    result = list()
    new_data = dict()
    new_data["@value"] = data
    new_data['@language'] = current_app.config.get(
        "WEKO_WORKSPACE_DATA_DEFAULT_LANGUAGE", "en"
    )

    result.append(new_data)
    return result


def get_datacite_title_data(data):
    """Get title data from datacite.

    Get title name and form it as format:
    {
        '@value': name,
        '@language': language
    }

    Args:
        data (list): A list of dictionaries containing title information.
    
    Returns:
        list: A list of dictionaries, each containing a title and its language.
    """
    result = list()
    default_language = current_app.config.get(
        "WEKO_WORKSPACE_DATA_DEFAULT_LANGUAGE", "en"
    )
    for title in data:
        new_data = dict()
        new_data["@value"] = title.get('title')
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

    Args:
        data (list): A list of dictionaries containing creator names and languages.
    
    Returns:
        list: A list of lists, each containing a dictionary with the creator names and languages.
    """
    result = list()
    default_language = current_app.config.get(
        "WEKO_WORKSPACE_DATA_DEFAULT_LANGUAGE", "en"
    )
    for item in data:
        if 'name' in item:
            result_creator = list()
            new_data = dict()
            new_data['@value'] = item.get('name')
            new_data['@language'] = item.get('lang', default_language)

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

    Args:
        data (list): A list of dictionaries containing contributor names and languages.

    Returns:
        list: A list of lists, each containing a dictionary with the contributor names and languages.
    """
    result = list()
    default_language = current_app.config.get(
        "WEKO_WORKSPACE_DATA_DEFAULT_LANGUAGE", "en"
    )
    for item in data:
        if 'name' in item:
            result_creator = list()
            new_data = dict()
            new_data['@value'] = item.get('name')
            new_data['@language'] = item.get('lang', default_language)

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

    Args:
        data (list): A list of dictionaries containing description information.

    Returns:
        list: A list of dictionaries, each containing a description, its language, and type.
    """
    result = list()
    default_language = current_app.config.get(
        "WEKO_WORKSPACE_DATA_DEFAULT_LANGUAGE", "en"
    )
    default_type = 'Abstract'
    for item in data:
        if 'description' in item:
            new_data = dict()
            new_data['@value'] = item.get('description')
            new_data['@language'] = item.get('lang', default_language)

            result.append(new_data)
    return result


def get_datacite_subject_data(data):
    """Get subject data from datacite.

    Get subject and form it as format:
    {
        '@value': title,
        '@language': language,
        '@scheme': scheme of subject
        '@URI': source of subject
    }

    Args:
        data (list): A list of dictionaries containing subject information.

    Returns:
        list: A list of dictionaries, each containing a subject, its language, and scheme.
    """
    result = list()
    default_language = current_app.config.get(
        "WEKO_WORKSPACE_DATA_DEFAULT_LANGUAGE", "en"
    )
    for sub in data:
        if 'subject' in sub:
            new_data = dict()
            new_data['@value'] = sub.get('subject')
            new_data['@scheme'] = sub.get('subjectScheme')
            new_data['@language'] = sub.get('lang', default_language)

            result.append(new_data)
    return result


def pack_data_with_multiple_type_datacite(data):
    """Map datacite multi data with type.

    Args:
        data (list): A list of dictionaries containing identifiers and their types.

    Returns:
        list: A list of dictionaries, each containing the type and identifier.

    """
    result = list()
    for d in data:
        new_data = dict()
        new_data['@value'] = d.get('identifier')
        new_data['@type'] = d.get('identifierType')
        result.append(new_data)
    return result


def get_datacite_product_identifier(data):
    """Get product identifier from datacite.

    Args:
        data (str): The DOI of the item.

    Returns:
        list: A list containing a dictionary with the product identifier packed as '@value'.
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


def get_datacite_autofill_item(item_id):
    """Get DataCite autofill item.
    
    Args:
        item_id (int): The item ID.
        
    Returns:
        dict: A dictionary containing the DataCite required item data.
    """
    jpcoar_item = get_item_id(item_id)
    datacite_req_item = dict()

    for key in current_app.config.get("WEKO_WORKSPACE_DATACITE_REQUIRED_ITEM"):
        if jpcoar_item.get(key) is not None:
            datacite_req_item[key] = jpcoar_item.get(key)
    return datacite_req_item
