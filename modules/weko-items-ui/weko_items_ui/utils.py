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

"""Module of weko-items-ui utils.."""

import calendar
import copy
import csv
import json
import os
import re
import shutil
import sys
import tempfile
import time
import traceback
import unicodedata
import secrets
import pytz
from collections import OrderedDict
from datetime import date, datetime, timedelta, timezone
from io import StringIO

import bagit
from sqlalchemy.exc import SQLAlchemyError
from elasticsearch.exceptions import NotFoundError
from elasticsearch import exceptions as es_exceptions
from flask import abort, current_app, flash, redirect, request, send_file, url_for
from flask_babelex import gettext as _
from flask_login import current_user
from sqlalchemy import MetaData, Table
from sqlalchemy.sql import text
from jsonschema import SchemaError, ValidationError

from invenio_accounts.models import Role, userrole
from invenio_cache import current_cache
from invenio_db import db
from invenio_i18n.ext import current_i18n
from invenio_indexer.api import RecordIndexer
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidrelations.models import PIDRelation
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_records.api import RecordBase
from invenio_accounts.models import User
from invenio_search import RecordsSearch
from invenio_stats.utils import QueryRankingHelper

from weko_authors.api import WekoAuthors
from weko_deposit.api import WekoDeposit, WekoRecord
from weko_deposit.pidstore import get_record_without_version
from weko_index_tree.api import Indexes
from weko_index_tree.utils import (
    check_index_permissions, get_index_id, get_user_roles
)
from weko_notifications.models import NotificationsUserSettings
from weko_records.api import FeedbackMailList, JsonldMapping, RequestMailList, ItemTypes, Mapping
from weko_records.serializers.utils import get_item_type_name
from weko_records.utils import replace_fqdn_of_file_metadata
from weko_records_ui.errors import AvailableFilesNotFoundRESTError
from weko_records_ui.permissions import (
    check_created_id, check_file_download_permission, check_publish_status
)
from weko_redis.redis import RedisConnection
from weko_search_ui.config import ROCRATE_METADATA_FILE, WEKO_IMPORT_DOI_TYPE
from weko_search_ui.mapper import JsonLdMapper
from weko_search_ui.query import item_search_factory
from weko_search_ui.utils import (
    check_sub_item_is_system, get_root_item_option, get_sub_item_option
)
from weko_schema_ui.models import PublishStatus
from weko_user_profiles import UserProfile
from weko_workflow.api import WorkActivity
from weko_workflow.config import (
    IDENTIFIER_GRANT_LIST, WEKO_SERVER_CNRI_HOST_LINK
)
from weko_workflow.models import (
    Activity, FlowAction, FlowActionRole, FlowDefine, ActionStatusPolicy as ASP
)
from weko_workflow.utils import IdentifierHandle
from weko_admin.models import ApiCertificate


def get_list_username():
    """Get list username.

    Query database to get all available username
    return: list of username
    TODO:
    """
    current_user_id = current_user.get_id()
    current_app.logger.debug("current_user:{}".format(current_user))
    from weko_user_profiles.models import UserProfile

    users = UserProfile.query.filter(UserProfile.user_id != current_user_id).all()
    result = list()
    for user in users:
        username = user.get_username
        if username:
            result.append(username)

    return result


def get_list_email():
    """Get list email.

    Query database to get all available email
    return: list of email
    """
    current_user_id = current_user.get_id()
    result = list()
    users = User.query.filter(User.id != current_user_id).all()
    for user in users:
        email = user.email
        if email:
            result.append(email)
    # try:
    #     metadata = MetaData()
    #     metadata.reflect(bind=db.engine)
    #     table_name = 'accounts_user'

    #     user_table = Table(table_name, metadata)
    #     record = db.session.query(user_table)

    #     data = record.all()

    #     for item in data:
    #         if not int(current_user_id) == item[0]:
    #             result.append(item[1])
    # except Exception as e:
    #     result = str(e)

    return result


def get_user_info_by_username(username):
    """Get user information by username.

    Query database to get user id by using username
    Get email from database using user id
    Pack response data: user id, user name, email

    parameter:
        username: The username
    return: response pack
    """
    result = dict()
    try:
        user = UserProfile.get_by_username(username)
        user_id = user.user_id

        metadata = MetaData()
        metadata.reflect(bind=db.engine)
        table_name = 'accounts_user'

        user_table = Table(table_name, metadata)
        record = db.session.query(user_table)

        data = record.all()

        for item in data:
            if item[0] == user_id:
                result['username'] = username
                result['user_id'] = user_id
                result['email'] = item[1]
                return result
        return None
    except Exception as e:
        result['error'] = str(e)


def validate_user(username, email):
    """Validate user information.

    Get user id from database using username
    Get user id from database using email
    Compare 2 user id to validate user information
    Pack responde data:
        results: user information (username, user id, email)
        validation: username is match with email or not
        error: null if no error occurs

    param:
        username: The username
        email: The email
    return: response data
    """
    result = {
        'results': '',
        'validation': False,
        'error': ''
    }
    try:
        user = UserProfile.get_by_username(username)
        user_id = 0

        metadata = MetaData()
        metadata.reflect(bind=db.engine)
        table_name = 'accounts_user'

        user_table = Table(table_name, metadata)
        record = db.session.query(user_table)

        data = record.all()

        for item in data:
            if item[1] == email:
                user_id = item[0]
                break

        if user.user_id == user_id:
            user_info = dict()
            user_info['username'] = username
            user_info['user_id'] = user_id
            user_info['email'] = email
            result['results'] = user_info
            result['validation'] = True
        return result
    except Exception as e:
        result['error'] = str(e)

    return result


def get_user_info_by_email(email):
    """
    Get user information by email.

    Query database to get user id by using email
    Get username from database using user id
    Pack response data: user id, user name, email

    parameter:
        email: The email
    return: response
    """
    result = dict()
    try:
        metadata = MetaData()
        metadata.reflect(bind=db.engine)
        table_name = 'accounts_user'

        user_table = Table(table_name, metadata)
        record = db.session.query(user_table)

        data = record.all()
        for item in data:
            if item[1] == email:
                user = UserProfile.get_by_userid(item[0])
                if user is None:
                    result['username'] = ""
                else:
                    result['username'] = user.get_username
                result['user_id'] = item[0]
                result['email'] = email
                return result
        return None
    except Exception as e:
        result['error'] = str(e)


def get_user_information(user_id):
    """
    Get user information user_id.

    Query database to get email by using user_id
    Get username from database using user id
    Pack response data: user id, user name, email

    parameter:
        user_id: The user_id
    return: response
    """
    result = {
        'username': '',
        'email': '',
        'fullname': '',
    }
    user_info = UserProfile.get_by_userid(user_id)
    if user_info is not None:
        result['username'] = user_info.get_username
        result['fullname'] = user_info.fullname

    metadata = MetaData()
    metadata.reflect(bind=db.engine)
    table_name = 'accounts_user'

    user_table = Table(table_name, metadata)
    record = db.session.query(user_table)

    data = record.all()

    for item in data:
        if item[0] == user_id:
            result['email'] = item[1]
            return result

    return result


def get_user_permission(user_id):
    """
    Get user permission user_id.

    Compare current id with id of current user
    parameter:
        user_id: The user_id
    return: true if current id is the same with id of current user.
    If not return false
    """
    current_id = current_user.get_id()
    if current_id is None:
        return False
    if str(user_id) == current_id:
        return True
    return False


def get_current_user():
    """
    Get user id of user currently login.

    parameter:
    return: current_id
    """
    current_id = current_user.get_id()
    return current_id


def find_hidden_items(item_id_list, idx_paths=None, check_creator_permission=False, has_permission_indexes=[]):
    """
    Find items that should not be visible by the current user.

    parameter:
        item_id_list: list of uuid of items to be checked.
        idx_paths: List of index paths.
        check_creator_permission: List of index paths.
    return: List of items ID that the user cannot access.
    """
    if not item_id_list:
        return []

    # Check if is admin
    roles = get_user_roles()
    if roles[0]:
        return []

    has_permission_index = []
    no_permission_index = []
    hidden_list = []
    for record in WekoRecord.get_records(item_id_list):

        if check_creator_permission:
            # Check if user is owner of the item
            if check_created_id(record):
                continue

            # Check if item are public
            is_public = check_publish_status(record)
        else:
            is_public = True
        # Check if indices are public
        has_index_permission = False
        for idx in record.navi:
            if has_permission_indexes:
                if str(idx.cid) in has_permission_indexes:
                    has_index_permission = True
                    break
            else:
                if str(idx.cid) in has_permission_index:
                    has_index_permission = True
                    break
                elif idx.cid in no_permission_index:
                    continue
                if check_index_permissions(None, idx.cid) \
                        and (not idx_paths or idx.path in idx_paths):
                    has_permission_index.append(idx.cid)
                    has_index_permission = True
                    break
                else:
                    no_permission_index.append(idx.cid)
        if is_public and has_index_permission:
            continue

        hidden_list.append(str(record.id))

    return hidden_list


def get_permission_record(rank_type, es_data, display_rank, has_permission_indexes):
    """
    Find items that should be visible by the current user.

    parameter:
        rank_type: Ranking Type. e.g. 'most_reviewed_items' or 'most_downloaded_items' or 'created_most_items_user' or 'most_searched_keywords' or 'new_items'
        es_data: List of ranking data.
        display_rank: Number of ranking display.
        has_permission_indexes: List of can be view by the current user.
    return: List of ranking data that the user can access.
    """

    if not es_data:
        return []

    result = []
    roles = get_user_roles()
    date_list = []
    for data in es_data:
        if len(result) == display_rank:
            break

        add_flag = False
        pid_value = data['key'] \
            if 'key' in data \
            else data.get('_item_metadata').get('control_number')
        try:
            record = WekoRecord.get_record_by_pid(pid_value)
            if (record.pid and record.pid.status == PIDStatus.DELETED) or \
                    ('publish_status' in record and record['publish_status'] == PublishStatus.DELETE.value):
                continue
            if roles[0]:
                add_flag = True
            else:
                is_public = roles[0] or check_created_id(record) or check_publish_status(record)
                has_index_permission = False
                for idx in record.navi:
                    if str(idx.cid) in has_permission_indexes:
                        has_index_permission = True
                        break
                add_flag = is_public and has_index_permission
        except PIDDoesNotExistError:
            # do not add deleted items into ranking list.
            add_flag = False
            current_app.logger.debug("PID {} does not exist.".format(pid_value))

        if add_flag:
            if rank_type == 'new_items':
                if data['publish_date'] not in date_list:
                    ranking_data = parse_ranking_results(
                        rank_type,
                        pid_value,
                        record=record,
                        date=data['publish_date']
                    )
                    date_list.append(data['publish_date'])
                else:
                    ranking_data = parse_ranking_results(
                        rank_type,
                        pid_value,
                        record=record
                    )
            else:
                ranking_data = parse_ranking_results(
                    rank_type,
                    pid_value,
                    count=data['count'],
                    rank=len(result) + 1,
                    record=record
                )
            result.append(ranking_data)

    return result

def parse_ranking_results(rank_type,
                          key,
                          count=-1,
                          rank=-1,
                          record=None,
                          date=''):
    """
    Parse the raw stats results to be usable by the view.

    parameter:
        rank_type: Ranking Type. e.g. 'most_reviewed_items' or 'most_downloaded_items' or 'created_most_items_user' or 'most_searched_keywords' or 'new_items'
        key: key value. e.g. pid_value or search_key or user_id ...
        count: Count of rank data. Defaults to -1.
        rank: Rank number of rank data. Defaults to -1.
        record: WekoRecord object. Defaults to 'None'.
        date: Date of new item. Defaults to ''. e.g. '2022-10-01'

    Returns:
        Rank data.
        e.g. {'rank': 1, 'count': 100, 'title': 'ff', 'url': '../records/3'} or {'date': '2022-08-18', 'title': '2', 'url': '../records/1'}
    """

    if rank_type in ['most_reviewed_items', 'most_downloaded_items', 'new_items']:
        url = '../records/{0}'.format(key)
        title = record.get_titles
    elif rank_type == 'most_searched_keywords':
        url = '../search?page=1&size=20&search_type=1&q={0}'.format(key)
        title = key
    elif rank_type == 'created_most_items_user':
        url = None
        user_info = None
        if key:
            user_info = UserProfile.get_by_userid(key)
        title = '{}'.format(user_info.username) if user_info else 'None'

    if rank == -1:
        if date:
            res = dict(
                key=key,
                date=date,
                title=title,
                url=url
            )
        else:
            res = dict(
                key=key,
                title=title,
                url=url
            )
    else:
        res = dict(
            key=key,
            rank=rank,
            count=count,
            title=title,
            url=url
        )

    return res



def parse_ranking_new_items(result_data):
    """Parse ranking new items.

    :param result_data: result data
    """
    data_list = list()
    if not result_data or not result_data.get('hits') \
            or not result_data.get('hits').get('hits'):
        return data_list
    for item_data in result_data.get('hits').get('hits'):
        item_created = item_data.get('_source')
        data = dict()
        data['record_id'] = item_data.get('_id')
        data['create_date'] = item_created.get('publish_date', '')
        data['pid_value'] = item_created.get('control_number')
        meta_data = item_created.get('_item_metadata')
        item_title = ''
        if isinstance(meta_data, dict):
            item_title = meta_data.get('item_title')
        data['record_name'] = item_title
        data_list.append(data)
    return data_list


def parse_ranking_record(result_data):
    """Parse ranking record.

    :param result_data: result data
    """
    data_list = list()
    if not result_data or not result_data.get('hits') \
            or not result_data.get('hits').get('hits'):
        return data_list
    for item_data in result_data.get('hits').get('hits'):
        if item_data.get('_source', {}).get('control_number'):
            data_list.append(item_data.get('_source').get('control_number'))
    return data_list


def validate_form_input_data(
        result: dict, item_id: str, data: dict):
    """Validate input data.

    :param result: result dictionary.
    :param item_id: item type identifier.
    :param data: form input data
    :param activity_id: activity id
    """
    # current_app.logger.error("result: {}".format(result))
    # current_app.logger.error("item_id: {}".format(item_id))
    # current_app.logger.error("data: {}".format(data))
    def _get_jpcoar_mapping_value_mapping(key, item_type_mapping):
        ret = {}
        if key in item_type_mapping and "jpcoar_mapping" in item_type_mapping[key]:
            ret = item_type_mapping[key]["jpcoar_mapping"]
        return ret

    def _get_keys_that_exist_from_data(given_data: dict) -> list:
        ret = []
        if given_data is not None:
            if type(given_data) is dict:
                ret = list(given_data.keys())
            elif type(given_data) is str:
                ret = list(given_data)
        return ret


    # Get langauge key - DONE
    # Iterate data for validating the value -
    # Check each item and raise an error for duplicate langauge value -

    item_type = ItemTypes.get_by_id(item_id)
    json_schema = item_type.schema.copy()
    data_keys = list(data.keys())
    item_type_mapping = Mapping.get_record(item_type.id)
    item_type_mapping_keys = list(item_type_mapping.keys())
    is_error = False
    items_to_be_checked_for_duplication: list = []
    items_to_be_checked_for_ja_kana: list = []
    items_to_be_checked_for_ja_latn: list = []
    items_to_be_checked_for_date_format: list = []

    # TITLE VARIABLES
    mapping_title_item_key: str = ""
    mapping_title_language_key: tuple = ("_","_")

    # ALTERNATIVE TITLE VARIABLES
    mapping_alternative_title_item_key: str = ""
    mapping_alternative_title_language_key: tuple = ("_","_")

    # CREATOR VARIABLES
    mapping_creator_item_key: str = ""
    mapping_creator_given_name_language_key: tuple = ("_","_")
    mapping_creator_family_name_language_key: tuple = ("_","_")
    mapping_creator_affiliation_name_language_key: tuple = ("_","_")
    mapping_creator_creator_name_language_key: tuple = ("_","_")
    mapping_creator_alternative_name_language_key: tuple = ("_","_")

    # CONTRIBUTOR VARIABLES
    mapping_contributor_item_key = ""
    mapping_contributor_given_name_language_key: tuple = ("_","_")
    mapping_contributor_family_name_language_key: tuple = ("_","_")
    mapping_contributor_affiliation_name_language_key: tuple = ("_","_")
    mapping_contributor_contributor_name_language_key: tuple = ("_","_")
    mapping_contributor_alternative_name_language_key: tuple = ("_","_")

    # RELATION VARIABLES
    mapping_relation_item_key = ""
    mapping_related_title_language_key: tuple = ("_","_")

    # FUNDING REFERENCE VARIABLES
    mapping_funding_reference_item_key = ""
    mapping_funding_reference_funder_name_language_key: tuple = ("_","_")
    mapping_funding_reference_award_title_language_key: tuple = ("_","_")

    # SOURCE TITLE VARIABLES
    mapping_source_title_item_key: str = ""
    mapping_source_title_language_key: tuple = ("_","_")

    # DEGREE NAME VARIABLES
    mapping_degree_name_item_key: str = ""
    mapping_degree_name_language_key: str = ""

    # DEGREE GRANTOR NAME VARIABLES
    mapping_degree_grantor_item_key: str = ""
    mapping_degree_grantor_name_language_key: tuple = ("_","_")

    # CONFERENCE VARIABLES
    mapping_conference_item_key: str = ""
    mapping_conference_date_language_key: tuple = ("_","_")
    mapping_conference_name_language_key: tuple = ("_","_")
    mapping_conference_venue_language_key: tuple = ("_","_")
    mapping_conference_place_language_key: tuple = ("_","_")
    mapping_conference_sponsor_language_key: tuple = ("_","_")

    # HOLDING AGENT VARIABLES
    mapping_holding_agent_item_key: str = ""
    mapping_holding_agent_name_language_key: tuple = ("_","_")

    # CATALOG VARIABLES
    mapping_catalog_item_key: str = ""
    mapping_catalog_title_language_key: tuple = ("_","_")

    # DATE PATTERN VARIABLES
    date_pattern_list = [
        # YYYY
        # 1997
        r"^[0-9]{4}$",
        # YYYY-MM
        # 1997-07
        r'^[0-9]{4}-[0-9]{2}$',
        # YYYY-MM-DD
        # 1997-07-16
        r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$',
        # YYYY-MM-DDThh:mm+TZD
        # 1997-07-16T19:20+01:00
        r'^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}\+[0-9]{2}:[0-9]{2}$',
        # YYYY-MM-DDThh:mm-TZD
        # 1997-07-16T19:20-01:00
        r'^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}-[0-9]{2}:[0-9]{2}$',
        # YYYY-MM-DDThh:mm:ss+TZD
        # 1997-07-16T19:20:30+01:00
        r'^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\+[0-9]{2}:[0-9]{2}$',
        # YYYY-MM-DDThh:mm:ss-TZD
        # 1997-07-16T19:20:30-01:00
        r'^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}-[0-9]{2}:[0-9]{2}$',
        # YYYY-MM-DDThh:mm:ss.ss+TZD
        # 1997-07-16T19:20:30.45+01:00
        r'^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{2}\+[0-9]{2}:[0-9]{2}$',
        # YYYY-MM-DDThh:mm:ss.ss-TZD
        # 1997-07-16T19:20:30.45-01:00
        r'^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{2}-[0-9]{2}:[0-9]{2}$',
    ]

    """
    This code snippet is for dcterms date format validation. Once 'dcterms date' property is created and added to
    デフォルトアイテムタイプ（フル）とデフォルトアイテムタイプ（シンプル）metadata via update_item_type.py 'dcterms date'
    validation code will be added inside this function using the code snippet below.

    ### CODE SNIPPET FOR DCTERMS DATE FORMAT VALIDATION -- START
    elif mapping_dcterms_date_item_key == data_key:
            for data_dcterms_date_values in data_item_value_list:
                items_to_be_checked_for_date_format.append(data_dcterms_date_values.get("subitem_1522650091861"))
            # Validation for DATE FORMAT
            validation_date_format_error_checker(
                _("DATE FORMAT TEST"),
                items_to_be_checked_for_date_format
            )
            # Reset validation lists below for the next item to be validated
            items_to_be_checked_for_date_format = []
    ### DATE FORMAT TEST -- END
    """

    """
    This loop snippet is for getting the mapping language key of each item that is stored in the database
    """
    for key in item_type_mapping_keys:
        jpcoar_value: dict = _get_jpcoar_mapping_value_mapping(key, item_type_mapping)
        jpcoar_value_keys_lv1: list = list(jpcoar_value)

        for key_lv1 in jpcoar_value_keys_lv1:
            if "title" == key_lv1:
                title_sub_items: dict = jpcoar_value[key_lv1]
                title_sub_items_keys: list = list(title_sub_items.keys())
                mapping_title_item_key: str = key

                for title_sub_item in title_sub_items:
                    if "@attributes" == title_sub_item:
                        mapping_title_language_key: list = title_sub_items.get(title_sub_item, {}).get("xml:lang", "_").split(".")

            elif "alternative" == key_lv1:
                alternative_title_sub_items: dict = jpcoar_value[key_lv1]
                alternative_title_sub_items_title_sub_items_keys: list = list(alternative_title_sub_items.keys())
                mapping_alternative_title_item_key: str = key

                for alternative_title_sub_item in alternative_title_sub_items:
                    if "@attributes" == alternative_title_sub_item:
                        mapping_alternative_title_language_key: list = alternative_title_sub_items.get(alternative_title_sub_item, {}).get("xml:lang", "_").split(".")

            elif "creator" == key_lv1:
                mapping_creator_item_key: str = key
                creator_sub_items: dict = jpcoar_value[key_lv1]
                creator_sub_items_keys: list = list(creator_sub_items.keys())

                for creator_sub_item in creator_sub_items:
                    if creator_sub_item == "givenName":
                        mapping_creator_given_name_language_key = (
                            creator_sub_items.get(creator_sub_item, {}).get("@attributes", {"xml:lang": "_._"}).get("xml:lang", "_._").split(".")
                        )
                    elif creator_sub_item == "familyName":
                        mapping_creator_family_name_language_key = (
                            creator_sub_items.get(creator_sub_item, {}).get("@attributes", {"xml:lang": "_._"}).get("xml:lang", "_._").split(".")
                        )
                    elif creator_sub_item == "affiliation":
                        mapping_creator_affiliation_name_language_key = (
                            creator_sub_items.get(creator_sub_item, {}).get("affiliationName", {}).get("@attributes", {"xml:lang": "_._"}).get("xml:lang", "_._").split(".")
                        )
                    elif creator_sub_item == "creatorName":
                        mapping_creator_creator_name_language_key = (
                            creator_sub_items.get(creator_sub_item, {}).get("@attributes", {"xml:lang": "_._"}).get("xml:lang", "_._").split(".")
                        )
                    elif creator_sub_item == "creatorAlternative":
                        mapping_creator_alternative_name_language_key = (
                            creator_sub_items.get(creator_sub_item, {}).get("@attributes", {"xml:lang": "_._"}).get("xml:lang", "_._").split(".")
                        )

            elif "contributor" == key_lv1:
                mapping_contributor_item_key: str = key
                contributor_sub_items: dict = jpcoar_value[key_lv1]
                contributor_sub_items_keys: list = list(contributor_sub_items.keys())

                for contributor_sub_item in contributor_sub_items:
                    if contributor_sub_item == "givenName":
                        mapping_contributor_given_name_language_key = (
                            contributor_sub_items.get(contributor_sub_item, {}).get("@attributes", {"xml:lang": "_._"}).get("xml:lang", "_._").split(".")
                        )
                    elif contributor_sub_item == "familyName":
                        mapping_contributor_family_name_language_key = (
                            contributor_sub_items.get(contributor_sub_item, {}).get("@attributes", {"xml:lang": "_._"}).get("xml:lang", "_._").split(".")
                        )
                    elif contributor_sub_item == "affiliation":
                        mapping_contributor_affiliation_name_language_key = (
                            contributor_sub_items.get(contributor_sub_item, {}).get("affiliationName", {}).get("@attributes", {"xml:lang": "_._"}).get("xml:lang", "_._").split(".")
                        )
                    elif contributor_sub_item == "contributorName":
                        mapping_contributor_contributor_name_language_key = (
                            contributor_sub_items.get(contributor_sub_item, {}).get("@attributes", {"xml:lang": "_._"}).get("xml:lang", "_._").split(".")
                        )
                    elif contributor_sub_item == "contributorAlternative":
                        mapping_contributor_alternative_name_language_key = (
                            contributor_sub_items.get(contributor_sub_item, {}).get("@attributes", {"xml:lang": "_._"}).get("xml:lang", "_._").split(".")
                        )

            elif "relation" == key_lv1:
                mapping_relation_item_key: str = key
                relation_sub_items: dict = jpcoar_value[key_lv1]
                relation_sub_items_keys:list  = list(relation_sub_items.keys())

                for relation_sub_item in relation_sub_items:
                    if relation_sub_item == "relatedTitle":
                        mapping_related_title_language_key = (
                            relation_sub_items.get(relation_sub_item, {}).get("@attributes", {"xml:lang": "_._"}).get("xml:lang", "_._").split(".")
                        )

            elif "fundingReference" == key_lv1:
                mapping_funding_reference_item_key: str = key
                funding_reference_sub_items: dict = jpcoar_value[key_lv1]
                funding_reference_sub_items_keys: list = list(funding_reference_sub_items.keys())

                for funding_reference_sub_item in funding_reference_sub_items:
                    if funding_reference_sub_item == "funderName":
                        mapping_funding_reference_funder_name_language_key = (
                            funding_reference_sub_items.get(funding_reference_sub_item, {}).get("@attributes", {"xml:lang": "_._"}).get("xml:lang", "_._").split(".")
                        )
                    elif funding_reference_sub_item == "awardTitle":
                        mapping_funding_reference_award_title_language_key = (
                            funding_reference_sub_items.get(funding_reference_sub_item, {}).get("@attributes", {"xml:lang": "_._"}).get("xml:lang", "_._").split(".")
                        )

            elif "sourceTitle" == key_lv1:
                if len(jpcoar_value.keys()) == 1:
                    source_title_sub_items: dict = jpcoar_value[key_lv1]
                    source_title_sub_items_keys: list = list(source_title_sub_items.keys())
                    mapping_source_title_item_key: str = key

                    for source_title_sub_item in source_title_sub_items:
                        if "@attributes" == source_title_sub_item:
                            mapping_source_title_language_key: list = source_title_sub_items.get(source_title_sub_item, {}).get("xml:lang", "_").split(".")

            elif "degreeName" == key_lv1:
                degree_name_sub_items: dict = jpcoar_value[key_lv1]
                degree_name_sub_items_keys: list = list(degree_name_sub_items.keys())
                mapping_degree_name_item_key: str = key

                for degree_name_sub_item in degree_name_sub_items:
                    if "@attributes" == degree_name_sub_item:
                        mapping_degree_name_language_key: list = degree_name_sub_items.get(degree_name_sub_item, {}).get("xml:lang", "_").split(".")

            elif "degreeGrantor" == key_lv1:
                mapping_degree_grantor_item_key: str = key
                degree_grantor_sub_items: dict = jpcoar_value[key_lv1]
                degree_grantor_sub_items_keys:list  = list(degree_grantor_sub_items.keys())

                for degree_grantor_sub_item in degree_grantor_sub_items:
                    if degree_grantor_sub_item == "degreeGrantorName":
                        mapping_degree_grantor_name_language_key = (
                            degree_grantor_sub_items.get(degree_grantor_sub_item, {}).get("@attributes", {"xml:lang": "_._"}).get("xml:lang", "_._").split(".")
                        )

            elif "conference" == key_lv1:
                mapping_conference_item_key: str = key
                conference_sub_items: dict = jpcoar_value[key_lv1]
                conference_sub_items_keys: list = list(conference_sub_items.keys())
                for conference_sub_item in conference_sub_items:
                    if conference_sub_item == "conferenceDate":
                        mapping_conference_date_language_key = (
                            conference_sub_items.get(conference_sub_item, {}).get("@attributes", {"xml:lang": "_._"}).get("xml:lang", "_._").split(".")
                        )
                    elif conference_sub_item == "conferenceName":
                        mapping_conference_name_language_key = (
                            conference_sub_items.get(conference_sub_item, {}).get("@attributes", {"xml:lang": "_._"}).get("xml:lang", "_._").split(".")
                        )
                    elif conference_sub_item == "conferencePlace":
                        mapping_conference_place_language_key = (
                            conference_sub_items.get(conference_sub_item, {}).get("@attributes", {"xml:lang": "_._"}).get("xml:lang", "_._").split(".")
                        )
                    elif conference_sub_item == "conferenceVenue":
                        mapping_conference_venue_language_key = (
                            conference_sub_items.get(conference_sub_item, {}).get("@attributes", {"xml:lang": "_._"}).get("xml:lang", "_._").split(".")
                        )
                    elif conference_sub_item == "conferenceSponsor":
                        mapping_conference_sponsor_language_key = (
                            conference_sub_items.get(conference_sub_item, {}).get("@attributes", {"xml:lang": "_._"}).get("xml:lang", "_._").split(".")
                        )

    """
    For iterating the argument 'data' and validating its language value
    """
    def validation_duplication_error_checker(item_error_message: str, items_to_be_checked_for_duplication: list):

        def _validate_language_value(
                language_value_list: list,
                language_value: str,
                duplication_error: str,
                item_error_message: str
        ):
            if language_value_list.count(language_value) > 1:
                raise ValidationError(f"{item_error_message} -- {duplication_error}")

        duplication_error: str = """
            Please ensure that the following applicable items have no duplicate language values:
            Title, Creator Name ,Creator Family Name, Creator Given Name, Creator Affliation Name,
            Contributor Name ,Contributor Family Name, Contributor Given Name, Contributor Affliation Name,
            Related Title, Funding Reference Funder Name, Funding Reference Award Title, Source Title, Degree Name,
            Degree Grantor Name, Conference Name, Conference Sponsor, Conference Date, Conference Venue, Conference Place,
            Holding Agent Name, Catalog Title
        """

        try:
            for lang_value in items_to_be_checked_for_duplication:
                _validate_language_value(
                    items_to_be_checked_for_duplication,
                    lang_value,
                    duplication_error,
                    item_error_message
                )

        except ValidationError as error:
            current_app.logger.error(traceback.format_exc())
            current_app.logger.error(error)
            result["is_valid"] = False
            result['error'] = f"{item_error_message} -- {duplication_error}"

    def validation_ja_kana_error_checker(item_error_message: str, items_to_be_checked_for_ja_kana: list):

        def _validate_language_value(
                language_value_list: list,
                language_value: str,
                ja_kana_error: str,
                item_error_message: str
        ):
            if language_value == "ja-Kana" and "ja" not in language_value_list:
                raise ValidationError(f"{item_error_message} -- {ja_kana_error}")

        ja_kana_error: str = """
            If ja-Kana is used, please ensure that the following applicable items have ja language values:
            Creator Name ,Creator Family Name, Creator Given Name, Creator Alternative Name,
            Contributor Name ,Contributor Family Name, Contributor Given Name, Contributor Alternative Name,
            Holding Agent Name, Catalog Title.
        """

        try:
            for lang_value in items_to_be_checked_for_ja_kana:
                _validate_language_value(
                    items_to_be_checked_for_ja_kana,
                    lang_value,
                    ja_kana_error,
                    item_error_message
                )

        except ValidationError as error:
            current_app.logger.error(traceback.format_exc())
            current_app.logger.error(error)
            result["is_valid"] = False
            result['error'] = f"{item_error_message} -- {ja_kana_error}"

    def validation_ja_latn_error_checker(item_error_message: str, items_to_be_checked_for_ja_latn: list):

        def _validate_language_value(
                language_value_list: list,
                language_value: str,
                ja_latn_error: str,
                item_error_message: str
        ):
            if language_value == "ja-Latn" and "ja" not in language_value_list:
                raise ValidationError(f"{item_error_message} -- {ja_latn_error}")

        ja_latn_error: str = """
            If ja-Latn is used, please ensure that the following applicable items have ja language values:
            Creator Name ,Creator Family Name, Creator Given Name, Creator Alternative Name,
            Contributor Name ,Contributor Family Name, Contributor Given Name, Contributor Alternative Name,
            Holding Agent Name, Catalog Title.
        """

        try:
            for lang_value in items_to_be_checked_for_ja_latn:
                _validate_language_value(
                    items_to_be_checked_for_ja_latn,
                    lang_value,
                    ja_latn_error,
                    item_error_message
                )

        except ValidationError as error:
            current_app.logger.error(traceback.format_exc())
            current_app.logger.error(error)
            result["is_valid"] = False
            result['error'] = f"{item_error_message} -- {ja_latn_error}"

    def validation_date_format_error_checker(item_error_message: str, items_to_be_checked_for_date_format: list):

        def _validate_date_format(
                date_value: str,
                date_format_error: str,
                item_error_message: str
        ):
            result = False

            for pattern in date_pattern_list:
                if re.match(pattern, date_value):
                    result = True

            if not result:
                raise ValidationError(f"{item_error_message} -- {date_format_error}")

        date_format_error: str = """
            Please ensure that entered date has the following formats: YYYY, YYYY-MM, YYYY-MM-DD,
            YYYY-MM-DDThh:mm+TZD, YYYY-MM-DDThh:mm-TZD, YYYY-MM-DDThh:mm:ss+TZD, YYYY-MM-DDThh:mm:ss-TZD,
            YYYY-MM-DDThh:mm:ss.ss+TZD, YYYY-MM-DDThh:mm:ss.ss-TZD
        """

        try:
            for date_value in items_to_be_checked_for_date_format:
                _validate_date_format(
                    date_value,
                    date_format_error,
                    item_error_message
                )

        except ValidationError as error:
            current_app.logger.error(traceback.format_exc())
            current_app.logger.error(error)
            """
            Commeneted out result["is_valid"] and result["error"] will be enabled when "dcterms date" will be used
            """
            # result["is_valid"] = False
            # result['error'] = f"{item_error_message} -- {date_format_error}"

    # """
    # This snippet is for testing 'validation_date_format_error_checker' while 'dcterms date' doesn't exist yet
    # """
    # date_format_test_data = [
    #     "1997",
    #     "1997-07",
    #     "1997-07-16",
    #     "1997-07-16T19:20+01:00",
    #     "1997-07-16T19:20-01:00",
    #     "1997-07-16T19:20:30+01:00",
    #     "1997-07-16T19:20:30-01:00",
    #     "1997-07-16T19:20:30.45+01:00",
    #     "1997-07-16T19:20:30.45-01:00",
    #     "199-this-will-result-in-error"
    # ]
    # for date in date_format_test_data:
    #     validation_date_format_error_checker("DATE FORMAT TEST", [date])

    for data_key in data_keys:
        data_item_value_list = data[data_key]
        # Validate TITLE item values from data
        if mapping_title_item_key == data_key:
            for data_item_values in data_item_value_list:
                keys_that_exist_in_data: list = _get_keys_that_exist_from_data(data_item_values)
                for mapping_key in list(set(mapping_title_language_key)):
                    if mapping_key in keys_that_exist_in_data:
                        # Append TITLE LANGUAGE value to items_to_be_checked_for_duplication list
                        items_to_be_checked_for_duplication.append(data_item_values.get(mapping_key))
                        items_to_be_checked_for_ja_kana.append(data_item_values.get(mapping_key))
                        items_to_be_checked_for_ja_latn.append(data_item_values.get(mapping_key))
                    else:
                        pass
            # Validation for TITLE
            validation_duplication_error_checker(
                _("Title"),
                items_to_be_checked_for_duplication
            )
            validation_ja_kana_error_checker(
                _("Title"),
                items_to_be_checked_for_ja_kana
            )
            validation_ja_latn_error_checker(
                _("Title"),
                items_to_be_checked_for_ja_latn
            )
            # Reset validation lists below for the next item to be validated
            items_to_be_checked_for_duplication = []
            items_to_be_checked_for_ja_kana = []
            items_to_be_checked_for_ja_latn = []

        # Validate ALTERNATIVE TITLE item values from data
        elif mapping_alternative_title_item_key == data_key:
            for data_item_values in data_item_value_list:
                keys_that_exist_in_data: list = _get_keys_that_exist_from_data(data_item_values)
                for mapping_key in list(set(mapping_alternative_title_language_key)):
                    if mapping_key in keys_that_exist_in_data:
                        # Append ALTERNATIVE TITLE LANGUAGE value to items_to_be_checked_for_duplication list
                        items_to_be_checked_for_ja_kana.append(data_item_values.get(mapping_key))
                        items_to_be_checked_for_ja_latn.append(data_item_values.get(mapping_key))
                    else:
                        pass

            # Validation for ALTERNATIVE TITLE
            validation_ja_kana_error_checker(
                _("Alternative Title"),
                items_to_be_checked_for_ja_kana
            )
            validation_ja_latn_error_checker(
                _("Alternative Title"),
                items_to_be_checked_for_ja_latn
            )
            # Reset validation lists below for the next item to be validated
            items_to_be_checked_for_ja_kana = []
            items_to_be_checked_for_ja_latn = []

        # Validate CREATOR item values from data
        elif mapping_creator_item_key == data_key:
            for data_creator_item_values in data_item_value_list:
                if isinstance(data_creator_item_values, dict):
                    for data_creator_item_values_key in list(data_creator_item_values.keys()):
                        # CREATOR GIVEN NAMES
                        if data_creator_item_values_key == mapping_creator_given_name_language_key[0]:
                            given_names_values: [dict] = data_creator_item_values.get(mapping_creator_given_name_language_key[0])
                            for given_name_values in given_names_values:
                                keys_that_exist_in_data: list = _get_keys_that_exist_from_data(given_name_values)
                                for mapping_key in mapping_creator_given_name_language_key:
                                    if mapping_key in keys_that_exist_in_data:
                                        # Append CREATOR GIVEN NAME LANGUAGE value to items_to_be_checked_for_duplication list
                                        items_to_be_checked_for_duplication.append(given_name_values.get(mapping_key))
                                        items_to_be_checked_for_ja_kana.append(given_name_values.get(mapping_key))
                                        items_to_be_checked_for_ja_latn.append(given_name_values.get(mapping_key))
                            # Validation for CREATOR GIVEN NAMES
                            validation_duplication_error_checker(
                                _("Creator Given Name"),
                                items_to_be_checked_for_duplication
                            )
                            validation_ja_kana_error_checker(
                                _("Creator Given Name"),
                                items_to_be_checked_for_ja_kana
                            )
                            validation_ja_latn_error_checker(
                                _("Creator Given Name"),
                                items_to_be_checked_for_ja_latn
                            )
                            # Reset validation lists below for the next item to be validated
                            items_to_be_checked_for_duplication = []
                            items_to_be_checked_for_ja_kana = []
                            items_to_be_checked_for_ja_latn = []

                        # CREATOR FAMILY NAMES
                        elif data_creator_item_values_key == mapping_creator_family_name_language_key[0]:
                            family_names_values: [dict] = data_creator_item_values.get(mapping_creator_family_name_language_key[0])
                            for family_name_values in family_names_values:
                                keys_that_exist_in_data: list = _get_keys_that_exist_from_data(family_name_values)
                                for mapping_key in mapping_creator_family_name_language_key:
                                    if mapping_key in keys_that_exist_in_data:
                                        # Append CREATOR FAMILY NAMES NAME LANGUAGE value to items_to_be_checked_for_duplication list
                                        items_to_be_checked_for_duplication.append(family_name_values.get(mapping_key))
                                        items_to_be_checked_for_ja_kana.append(family_name_values.get(mapping_key))
                                        items_to_be_checked_for_ja_latn.append(family_name_values.get(mapping_key))
                            # Validation for CREATOR FAMILY NAMES
                            validation_duplication_error_checker(
                                _("Creator Family Name"),
                                items_to_be_checked_for_duplication
                            )
                            validation_ja_kana_error_checker(
                                _("Creator Family Name"),
                                items_to_be_checked_for_ja_kana
                            )
                            validation_ja_latn_error_checker(
                                _("Creator Family Name"),
                                items_to_be_checked_for_ja_latn
                            )
                            # Reset validation lists below for the next item to be validated
                            items_to_be_checked_for_duplication = []
                            items_to_be_checked_for_ja_kana = []
                            items_to_be_checked_for_ja_latn = []

                        # CREATOR AFFLIATION NAMES
                        elif data_creator_item_values_key == mapping_creator_affiliation_name_language_key[0]:
                            creator_affiliations: [dict] = data_creator_item_values.get(mapping_creator_affiliation_name_language_key[0])
                            for creator_affiliation in creator_affiliations:
                                creator_affiliation_names: [dict] = creator_affiliation.get(mapping_creator_affiliation_name_language_key[1])
                                for creator_affiliation_name_values in creator_affiliation_names:
                                    keys_that_exist_in_data: list = _get_keys_that_exist_from_data(creator_affiliation_name_values)
                                    for mapping_key in list(set(mapping_creator_affiliation_name_language_key)):
                                        if mapping_key in keys_that_exist_in_data:
                                            # Append CREATOR AFFLIATION NAMES LANGUAGE value to items_to_be_checked_for_duplication list
                                            items_to_be_checked_for_duplication.append(creator_affiliation_name_values.get(mapping_key))
                                # Validation for CREATOR AFFLIATION NAMES
                                validation_duplication_error_checker(
                                    _("Creator Affiliation Name"),
                                    items_to_be_checked_for_duplication
                                )
                                # Reset validation lists below for the next item to be validated
                                items_to_be_checked_for_duplication = []

                        # CREATOR NAMES
                        elif data_creator_item_values_key == mapping_creator_creator_name_language_key[0]:
                            creator_names_values: [dict] = data_creator_item_values.get(mapping_creator_creator_name_language_key[0])
                            for creator_name_values in creator_names_values:
                                keys_that_exist_in_data: list = _get_keys_that_exist_from_data(creator_name_values)
                                for mapping_key in list(set(mapping_creator_creator_name_language_key)):
                                    if mapping_key in keys_that_exist_in_data:
                                        # Append CREATOR AFFLIATION NAMES LANGUAGE value to items_to_be_checked_for_duplication list
                                        items_to_be_checked_for_duplication.append(creator_name_values.get(mapping_key))
                                        items_to_be_checked_for_ja_kana.append(creator_name_values.get(mapping_key))
                                        items_to_be_checked_for_ja_latn.append(creator_name_values.get(mapping_key))
                            # Validation for CREATOR NAMES
                            validation_duplication_error_checker(
                                _("Creator Name"),
                                items_to_be_checked_for_duplication
                            )
                            validation_ja_kana_error_checker(
                                _("Creator Name"),
                                items_to_be_checked_for_ja_kana
                            )
                            validation_ja_latn_error_checker(
                                _("Creator Name"),
                                items_to_be_checked_for_ja_latn
                            )
                            # Reset validation lists below for the next item to be validated
                            items_to_be_checked_for_duplication = []
                            items_to_be_checked_for_ja_kana = []
                            items_to_be_checked_for_ja_latn = []

                        # CREATOR ALTERNATIVE NAMES
                        elif data_creator_item_values_key == mapping_creator_alternative_name_language_key[0]:
                            creator_alternative_names_values: [dict] = data_creator_item_values.get(mapping_creator_alternative_name_language_key[0])
                            for creator_alternative_name_values in creator_alternative_names_values:
                                keys_that_exist_in_data: list = _get_keys_that_exist_from_data(creator_alternative_name_values)
                                for mapping_key in list(set(mapping_creator_alternative_name_language_key)):
                                    if mapping_key in keys_that_exist_in_data:
                                        # Append CREATOR ALTERNATIVE NAMES LANGUAGE value to items_to_be_checked_for_duplication list
                                        items_to_be_checked_for_ja_kana.append(creator_alternative_name_values.get(mapping_key))
                                        items_to_be_checked_for_ja_latn.append(creator_alternative_name_values.get(mapping_key))
                            # Validation for CREATOR ALTERNATIVE NAMES
                            validation_ja_kana_error_checker(
                                _("Creator Alternative Name"),
                                items_to_be_checked_for_ja_kana
                            )
                            validation_ja_latn_error_checker(
                                _("Creator Alternative Name"),
                                items_to_be_checked_for_ja_latn
                            )
                            # Reset validation lists below for the next item to be validated
                            items_to_be_checked_for_ja_kana = []
                            items_to_be_checked_for_ja_latn = []

                        else:
                            pass

        # Validate CONTRIBUTOR item values from data
        elif mapping_contributor_item_key == data_key:
            for data_contributor_item_values in data_item_value_list:
                if isinstance(data_contributor_item_values, dict):
                    for data_contributor_item_values_key in list(data_contributor_item_values.keys()):
                        # CONTRIBUTOR GIVEN NAMES
                        if data_contributor_item_values_key == mapping_contributor_given_name_language_key[0]:
                            given_names_values: [dict] = data_contributor_item_values.get(mapping_contributor_given_name_language_key[0])
                            for given_name_values in given_names_values:
                                keys_that_exist_in_data: list = _get_keys_that_exist_from_data(given_name_values)
                                for mapping_key in list(set(mapping_contributor_given_name_language_key)):
                                    if mapping_key in keys_that_exist_in_data:
                                        # Append CONTRIBUTOR GIVEN NAMES LANGUAGE value to items_to_be_checked_for_duplication list
                                        items_to_be_checked_for_duplication.append(given_name_values.get(mapping_key))
                                        items_to_be_checked_for_ja_kana.append(given_name_values.get(mapping_key))
                                        items_to_be_checked_for_ja_latn.append(given_name_values.get(mapping_key))
                            # Validation for CONTRIBUTOR GIVEN NAMES
                            validation_duplication_error_checker(
                                _("Contributor Given Name"),
                                items_to_be_checked_for_duplication
                            )
                            validation_ja_kana_error_checker(
                                _("Contributor Given Name"),
                                items_to_be_checked_for_ja_kana
                            )
                            validation_ja_latn_error_checker(
                                _("Contributor Given Name"),
                                items_to_be_checked_for_ja_latn
                            )
                            # Reset validation lists below for the next item to be validated
                            items_to_be_checked_for_duplication = []
                            items_to_be_checked_for_ja_kana = []
                            items_to_be_checked_for_ja_latn = []

                        # CONTRIBUTOR FAMILY NAMES
                        elif data_contributor_item_values_key == mapping_contributor_family_name_language_key[0]:
                            family_names_values: [dict] = data_contributor_item_values.get(mapping_contributor_family_name_language_key[0])
                            for family_name_values in family_names_values:
                                keys_that_exist_in_data: list = _get_keys_that_exist_from_data(family_name_values)
                                for mapping_key in list(set(mapping_contributor_family_name_language_key)):
                                    if mapping_key in keys_that_exist_in_data:
                                        # Append CONTRIBUTOR FAMILY NAMES LANGUAGE value to items_to_be_checked_for_duplication list
                                        items_to_be_checked_for_duplication.append(family_name_values.get(mapping_key))
                                        items_to_be_checked_for_ja_kana.append(family_name_values.get(mapping_key))
                                        items_to_be_checked_for_ja_latn.append(family_name_values.get(mapping_key))
                            # Validation for CONTRIBUTOR FAMILY NAMES
                            validation_duplication_error_checker(
                                _("Contributor Family Name"),
                                items_to_be_checked_for_duplication
                            )
                            validation_ja_kana_error_checker(
                                _("Contributor Family Name"),
                                items_to_be_checked_for_ja_kana
                            )
                            validation_ja_latn_error_checker(
                                _("Contributor Family Name"),
                                items_to_be_checked_for_ja_latn
                            )
                            # Reset validation lists below for the next item to be validated
                            items_to_be_checked_for_duplication = []
                            items_to_be_checked_for_ja_kana = []
                            items_to_be_checked_for_ja_latn = []

                        # CONTRIBUTOR AFFLIATION NAMES
                        elif data_contributor_item_values_key == mapping_contributor_affiliation_name_language_key[0]:
                            contributor_affiliations: [dict] = data_contributor_item_values.get(mapping_contributor_affiliation_name_language_key[0])
                            for contributor_affiliation in contributor_affiliations:
                                contributor_affiliation_names: [dict] = contributor_affiliation.get(mapping_contributor_affiliation_name_language_key[1])
                                for contributor_affiliation_name_values in contributor_affiliation_names:
                                    keys_that_exist_in_data: list = _get_keys_that_exist_from_data(contributor_affiliation_name_values)
                                    for mapping_key in list(set(mapping_contributor_affiliation_name_language_key)):
                                        if mapping_key in keys_that_exist_in_data:
                                            # Append CONTRIBUTOR AFFILIATION NAMES LANGUAGE value to items_to_be_checked_for_duplication list
                                            items_to_be_checked_for_duplication.append(contributor_affiliation_name_values.get(mapping_key))
                                # Validation for CONTRIBUTOR AFFILIATION NAMES
                                validation_duplication_error_checker(
                                    _("Contributor Affiliation Name"),
                                    items_to_be_checked_for_duplication
                                )
                                # Reset validation lists below for the next item to be validated
                                items_to_be_checked_for_duplication = []

                        # CONTRIBUTOR NAMES
                        elif data_contributor_item_values_key == mapping_contributor_contributor_name_language_key[0]:
                            contributor_names_values: [dict] = data_contributor_item_values.get(mapping_contributor_contributor_name_language_key[0])
                            for contributor_name_values in contributor_names_values:
                                keys_that_exist_in_data: list = _get_keys_that_exist_from_data(contributor_name_values)
                                for mapping_key in list(set(mapping_contributor_contributor_name_language_key)):
                                    if mapping_key in keys_that_exist_in_data:
                                        # Append CONTRIBUTOR NAMES LANGUAGE value to items_to_be_checked_for_duplication list
                                        items_to_be_checked_for_duplication.append(contributor_name_values.get(mapping_key))
                                        items_to_be_checked_for_ja_kana.append(contributor_name_values.get(mapping_key))
                                        items_to_be_checked_for_ja_latn.append(contributor_name_values.get(mapping_key))
                            # Validation for CONTRIBUTOR NAMES
                            validation_duplication_error_checker(
                                _("Contributor Name"),
                                items_to_be_checked_for_duplication
                            )
                            validation_ja_kana_error_checker(
                                _("Contributor Name"),
                                items_to_be_checked_for_ja_kana
                            )
                            validation_ja_latn_error_checker(
                                _("Contributor Name"),
                                items_to_be_checked_for_ja_latn
                            )
                            # Reset validation lists below for the next item to be validated
                            items_to_be_checked_for_duplication = []
                            items_to_be_checked_for_ja_kana = []
                            items_to_be_checked_for_ja_latn = []

                        # CONTRIBUTOR ALTERNATIVE NAMES
                        elif data_contributor_item_values_key == mapping_contributor_alternative_name_language_key[0]:
                            contributor_alternative_names_values: [dict] = data_contributor_item_values.get(mapping_contributor_alternative_name_language_key[0])
                            for contributor_alternative_name_values in contributor_alternative_names_values:
                                keys_that_exist_in_data: list = _get_keys_that_exist_from_data(contributor_alternative_name_values)
                                for mapping_key in list(set(mapping_contributor_alternative_name_language_key)):
                                    if mapping_key in keys_that_exist_in_data:
                                        # Append CONTRIBUTOR ALTERNATIVE NAMES LANGUAGE value to items_to_be_checked_for_duplication list
                                        items_to_be_checked_for_ja_kana.append(contributor_alternative_name_values.get(mapping_key))
                                        items_to_be_checked_for_ja_latn.append(contributor_alternative_name_values.get(mapping_key))
                            # Validation for CONTRIBUTOR ALTERNATIVE NAMES
                            validation_ja_kana_error_checker(
                                _("Contributor Alternative Name"),
                                items_to_be_checked_for_ja_kana
                            )
                            validation_ja_latn_error_checker(
                                _("Contributor Alternative Name"),
                                items_to_be_checked_for_ja_latn
                            )
                            # Reset validation lists below for the next item to be validated
                            items_to_be_checked_for_ja_kana = []
                            items_to_be_checked_for_ja_latn = []

                        else:
                            pass

        # Validate RELATION item values from data
        elif mapping_relation_item_key == data_key:
            for data_relation_item_values in data_item_value_list:
                if isinstance(data_relation_item_values, dict):
                    for data_relation_item_values_key in list(data_relation_item_values.keys()):
                        # RELATED TITLE
                        if data_relation_item_values_key == mapping_related_title_language_key[0]:
                            related_title_values: [dict] = data_relation_item_values.get(mapping_related_title_language_key[0])
                            for related_title_value in related_title_values:
                                keys_that_exist_in_data: list = _get_keys_that_exist_from_data(related_title_value)
                                for mapping_key in list(set(mapping_related_title_language_key)):
                                    if mapping_key in keys_that_exist_in_data:
                                        # Append CREATOR AFFILIATION NAMES LANGUAGE value to items_to_be_checked_for_duplication list
                                        items_to_be_checked_for_duplication.append(related_title_value.get(mapping_key))
                            # Validation for RELATED TITLE
                            validation_duplication_error_checker(
                                _("Relation Related Title"),
                                items_to_be_checked_for_duplication
                            )
                            # Reset validation lists below for the next item to be validated
                            items_to_be_checked_for_duplication = []

                        else:
                            pass

        # Validate FUNDING REFERENCE item values from data
        elif mapping_funding_reference_item_key == data_key:
            for data_funding_reference_item_values in data_item_value_list:
                if isinstance(data_funding_reference_item_values, dict):
                    for data_funding_reference_item_values_key in list(data_funding_reference_item_values.keys()):
                        # FUNDING REFERENCE FUNDER NAME
                        if data_funding_reference_item_values_key == mapping_funding_reference_funder_name_language_key[0]:
                            funding_reference_funder_name_values: [dict] = data_funding_reference_item_values.get(mapping_funding_reference_funder_name_language_key[0])
                            for funding_reference_funder_name_value in funding_reference_funder_name_values:
                                keys_that_exist_in_data: list = _get_keys_that_exist_from_data(funding_reference_funder_name_value)
                                for mapping_key in list(set(mapping_funding_reference_funder_name_language_key)):
                                    if mapping_key in keys_that_exist_in_data:
                                        # Append FUNDING REFERENCE FUNDER NAME LANGUAGE value to items_to_be_checked_for_duplication list
                                        items_to_be_checked_for_duplication.append(funding_reference_funder_name_value.get(mapping_key))
                            # Validation for FUNDING REFERENCE FUNDER NAME
                            validation_duplication_error_checker(
                                _("Funding Reference Funder Name"),
                                items_to_be_checked_for_duplication
                            )
                            # Reset validation lists below for the next item to be validated
                            items_to_be_checked_for_duplication = []

                        # FUNDING REFERENCE AWARD TITLE
                        elif data_funding_reference_item_values_key == mapping_funding_reference_award_title_language_key[0]:
                            funding_reference_award_title_values: [dict] = data_funding_reference_item_values.get(mapping_funding_reference_award_title_language_key[0])
                            for funding_reference_award_title_value in funding_reference_award_title_values:
                                keys_that_exist_in_data: list = _get_keys_that_exist_from_data(funding_reference_award_title_value)
                                for mapping_key in list(set(mapping_funding_reference_award_title_language_key)):
                                    if mapping_key in keys_that_exist_in_data:
                                        # Append FUNDING REFERENCE AWARD TITLE LANGUAGE value to items_to_be_checked_for_duplication list
                                        items_to_be_checked_for_duplication.append(funding_reference_award_title_value.get(mapping_key))
                            # Validation for FUNDING REFERENCE AWARD TITLE
                            validation_duplication_error_checker(
                                _("Funding Reference Award Title"),
                                items_to_be_checked_for_duplication
                            )
                            # Reset validation lists below for the next item to be validated
                            items_to_be_checked_for_duplication = []

                        else:
                            pass

        # Validate SOURCE TITLE item values from data
        elif mapping_source_title_item_key == data_key:
            for data_source_title_values in data_item_value_list:
                keys_that_exist_in_data: list = _get_keys_that_exist_from_data(data_source_title_values)
                for mapping_key in list(set(mapping_source_title_language_key)):
                    if mapping_key in keys_that_exist_in_data:
                        # Append SOURCE TITLE LANGUAGE value to items_to_be_checked_for_duplication list
                        items_to_be_checked_for_duplication.append(data_source_title_values.get(mapping_key))
                else:
                    pass
            # Validation for SOURCE TITLE
            validation_duplication_error_checker(
                _("Source Title"),
                items_to_be_checked_for_duplication
            )
            # Reset validation lists below for the next item to be validated
            items_to_be_checked_for_duplication = []

        # Validate DEGREE NAME item values from data
        elif mapping_degree_name_item_key == data_key:
            for data_degree_name_values in data_item_value_list:
                keys_that_exist_in_data: list = _get_keys_that_exist_from_data(data_degree_name_values)
                for mapping_key in list(set(mapping_degree_name_language_key)):
                    if mapping_key in keys_that_exist_in_data:
                        # Append DEGREE NAME LANGUAGE value to items_to_be_checked_for_duplication list
                        items_to_be_checked_for_duplication.append(data_degree_name_values.get(mapping_key))
                else:
                    pass
            # Validation for DEGREE NAME
            validation_duplication_error_checker(
                _("Degree Name"),
                items_to_be_checked_for_duplication
            )
            # Reset validation lists below for the next item to be validated
            items_to_be_checked_for_duplication = []

        # Validate DEGREE GRANTOR item values from data
        elif mapping_degree_grantor_item_key == data_key:
            for data_degree_grantor_item_values in data_item_value_list:
                if isinstance(data_degree_grantor_item_values, dict):
                    for data_degree_grantor_item_values_key in list(data_degree_grantor_item_values.keys()):
                        # DEGREE GRANTOR
                        if data_degree_grantor_item_values_key == mapping_degree_grantor_name_language_key[0]:
                            degree_grantor_values: [dict] = data_degree_grantor_item_values.get(mapping_degree_grantor_name_language_key[0])
                            for degree_grantor_values in degree_grantor_values:
                                # Append DEGREE GRANTOR NAME LANGUAGE value to items_to_be_checked_for_duplication list
                                items_to_be_checked_for_duplication.append(degree_grantor_values.get(mapping_degree_grantor_name_language_key[1]))
                            # Validation for DEGREE GRANTOR NAME
                            validation_duplication_error_checker(
                                _("Degree Grantor Name"),
                                items_to_be_checked_for_duplication
                            )
                            # Reset validation lists below for the next item to be validated
                            items_to_be_checked_for_duplication = []
                        else:
                            pass

        # Validate CONFERENCE item values from data
        elif mapping_conference_item_key == data_key:
            # EXCLUSIVE LOOP FOR CONFERENCE DATE
            for data_conference_item_values in data_item_value_list:
                if isinstance(data_conference_item_values, dict):
                    for data_conference_item_values_key in list(data_conference_item_values.keys()):
                        if data_conference_item_values_key == mapping_conference_date_language_key[0]:
                            date_values: dict = data_conference_item_values.get(mapping_conference_date_language_key[0])
                            keys_that_exist_in_data: list = _get_keys_that_exist_from_data(date_values)
                            for mapping_key in list(set(mapping_conference_date_language_key)):
                                if mapping_key in keys_that_exist_in_data:
                                    # Append CONFERENCE DATE LANGUAGE value to items_to_be_checked_for_duplication list
                                    items_to_be_checked_for_duplication.append(date_values.get(mapping_key))
            if isinstance(data_conference_item_values, dict):
                # Validation for CONFERENCE DATE
                validation_duplication_error_checker(
                    _("Conference Date"),
                    items_to_be_checked_for_duplication
                )
                # Reset validation lists below for the next item to be validated
                items_to_be_checked_for_duplication = []

            for data_conference_item_values in data_item_value_list:
                if isinstance(data_conference_item_values, dict):
                    for data_conference_item_values_key in list(data_conference_item_values.keys()):
                        # CONFERENCE NAMES
                        if data_conference_item_values_key == mapping_conference_name_language_key[0]:
                            conference_names_values: [dict] = data_conference_item_values.get(mapping_conference_name_language_key[0])
                            for conference_name_values in conference_names_values:
                                keys_that_exist_in_data: list = _get_keys_that_exist_from_data(conference_name_values)
                                for mapping_key in list(set(mapping_conference_name_language_key)):
                                    if mapping_key in keys_that_exist_in_data:
                                        # Append CONFERENCE NAME LANGUAGE value to items_to_be_checked_for_duplication list
                                        items_to_be_checked_for_duplication.append(conference_name_values.get(mapping_key))
                            # Validation for CONFERENCE NAMES
                            validation_duplication_error_checker(
                                _("Conference Name"),
                                items_to_be_checked_for_duplication
                            )
                            # Reset validation lists below for the next item to be validated
                            items_to_be_checked_for_duplication = []

                        # CONFERENCE PLACE
                        elif data_conference_item_values_key == mapping_conference_place_language_key[0]:
                            conference_places_values: [dict] = data_conference_item_values.get(mapping_conference_place_language_key[0])
                            for conference_place_values in conference_places_values:
                                keys_that_exist_in_data: list = _get_keys_that_exist_from_data(conference_place_values)
                                for mapping_key in list(set(mapping_conference_place_language_key)):
                                    if mapping_key in keys_that_exist_in_data:
                                        # Append CONFERENCE PLACE LANGUAGE value to items_to_be_checked_for_duplication list
                                        items_to_be_checked_for_duplication.append(conference_place_values.get(mapping_key))
                            # Validation for CONFERENCE PLACES
                            validation_duplication_error_checker(
                                _("Conference Place"),
                                items_to_be_checked_for_duplication
                            )
                            # Reset validation lists below for the next item to be validated
                            items_to_be_checked_for_duplication = []

                        # CONFERENCE VENUE
                        elif data_conference_item_values_key == mapping_conference_venue_language_key[0]:
                            conference_venue_values: [dict] = data_conference_item_values.get(mapping_conference_venue_language_key[0])
                            for conference_venue_value in conference_venue_values:
                                keys_that_exist_in_data: list = _get_keys_that_exist_from_data(conference_venue_value)
                                for mapping_key in list(set(mapping_conference_venue_language_key)):
                                    if mapping_key in keys_that_exist_in_data:
                                        # Append CONFERENCE PLACE LANGUAGE value to items_to_be_checked_for_duplication list
                                        items_to_be_checked_for_duplication.append(conference_venue_value.get(mapping_key))
                            # Validation for CONFERENCE VENUE
                            validation_duplication_error_checker(
                                _("Conference Venue"),
                                items_to_be_checked_for_duplication
                            )
                            # Reset validation lists below for the next item to be validated
                            items_to_be_checked_for_duplication = []

                        # CONFERENCE SPONSOR
                        elif data_conference_item_values_key == mapping_conference_sponsor_language_key[0]:
                            conference_sponsor_values: [dict] = data_conference_item_values.get(mapping_conference_sponsor_language_key[0])
                            for conference_sponsor_value in conference_sponsor_values:
                                keys_that_exist_in_data: list = _get_keys_that_exist_from_data(conference_sponsor_value)
                                for mapping_key in list(set(mapping_conference_sponsor_language_key)):
                                    if mapping_key in keys_that_exist_in_data:
                                        # Append CONFERENCE SPONSOR LANGUAGE value to items_to_be_checked_for_duplication list
                                        items_to_be_checked_for_duplication.append(conference_sponsor_value.get(mapping_key))
                            # Validation for CONFERENCE SPONSOR
                            validation_duplication_error_checker(
                                _("Conference Sponsor"),
                                items_to_be_checked_for_duplication
                            )
                            # Reset validation lists below for the next item to be validated
                            items_to_be_checked_for_duplication = []

                        else:
                            pass

        else:
            pass

    # Remove excluded item in json_schema
    remove_excluded_items_in_json_schema(item_id, json_schema)

    data['$schema'] = json_schema.copy()

    validation_data = RecordBase(data)

    try:
        validation_data.validate()
    except ValidationError as error:
        current_app.logger.error(traceback.format_exc())
        current_app.logger.error(error)
        result["is_valid"] = False
        if 'required' == error.validator:
            result['error'] = _('Please input all required item.')
        elif 'pattern' == error.validator:
            result['error'] = _('Please input the correct data.')
        else:
            result['error'] = _(error.message)
    except SchemaError as error:
        current_app.logger.error(traceback.format_exc())
        current_app.logger.error(error)
        current_app.logger.error("data:{}".format(data))
        result["is_valid"] = False
        result['error'] = 'Schema Error:<br/><br/>' + _(error.message)
    except Exception as ex:
        current_app.logger.error(ex)
        result["is_valid"] = False
        result['error'] = _(str(ex))


def parse_node_str_to_json_schema(node_str: str):
    """Parse node_str to json schema.

    :param node_str: node string
    :return: json schema
    """
    json_node = {}
    nodes = node_str.split('.')
    if len(nodes) > 0:
        json_node["item"] = nodes[len(nodes) - 1]
        for x in reversed(range(len(nodes) - 1)):
            json_node["child"] = copy.deepcopy(json_node)
            json_node["item"] = nodes[x]

    return json_node


def update_json_schema_with_required_items(node: dict, json_data: dict):
    """Update json schema with the required items.

    :param node: json schema return from def parse_node_str_to_json_schema
    :param json_data: The json schema
    """

    # current_app.logger.error("node:{}".format(node))
    # current_app.logger.error("json_data:{}".format(json_data))

    if not node.get('child'):
        if not json_data.get('required'):
            json_data['required'] = []
        json_data['required'].append(node['item'])
    else:
        if json_data['properties'][node['item']].get('items'):
            update_json_schema_with_required_items(
                node['child'], json_data['properties'][node['item']]['items'])
        else:
            update_json_schema_with_required_items(
                node['child'], json_data['properties'][node['item']])


def update_json_schema_by_activity_id(json_data, activity_id):
    """Update json schema by activity id.

    :param json_data: The json schema
    :param activity_id: Activity ID
    :return: json schema
    """

    redis_connection = RedisConnection()
    sessionstore = redis_connection.connection(db=current_app.config['ACCOUNTS_SESSION_REDIS_DB_NO'], kv = True)
    if not sessionstore.redis.exists(
        'updated_json_schema_{}'.format(activity_id)) or not sessionstore.get(
        'updated_json_schema_{}'.format(activity_id)):
        return None
    session_data = sessionstore.get(
        'updated_json_schema_{}'.format(activity_id))
    error_list = json.loads(session_data.decode('utf-8'))
    #current_app.logger.error("error_list:{}".format(error_list))
    if error_list:
        for item in error_list['required']:
            node = parse_node_str_to_json_schema(item)
            if node:
                update_json_schema_with_required_items(node, json_data)
        for item in error_list['pattern']:
            node = parse_node_str_to_json_schema(item)
            if node:
                update_json_schema_with_required_items(node, json_data)
    return json_data


def update_schema_form_by_activity_id(schema_form, activity_id):
    """Update schema form by activity id.

    :param schema_form: The schema form
    :param activity_id: Activity ID
    :return: schema form
    """

    redis_connection = RedisConnection()
    sessionstore = redis_connection.connection(db=current_app.config['ACCOUNTS_SESSION_REDIS_DB_NO'], kv = True)
    if not sessionstore.redis.exists(
        'updated_json_schema_{}'.format(activity_id)) \
        or not sessionstore.get(
            'updated_json_schema_{}'.format(activity_id)):
        return None
    session_data = sessionstore.get(
        'updated_json_schema_{}'.format(activity_id))
    error_list = json.loads(session_data.decode('utf-8'))

    if error_list and error_list['either']:
        either_required_list = error_list['either']
        recursive_prepare_either_required_list(
            schema_form, either_required_list)

        recursive_update_schema_form_with_condition(
            schema_form, either_required_list)

    return schema_form


def recursive_prepare_either_required_list(schema_form, either_required_list):
    """Recursive prepare either required list.

    :param schema_form: The schema form
    :param either_required_list: Either required list
    """
    for elem in schema_form:
        if elem.get('items'):
            recursive_prepare_either_required_list(
                elem.get('items'), either_required_list)
        else:
            if elem.get('key') and '[]' in elem['key']:
                for x, group in enumerate(either_required_list):
                    for i, ids in enumerate(group):
                        if isinstance(ids, list):
                            for y, _id in enumerate(ids):
                                if elem['key'].replace('[]', '') == _id:
                                    either_required_list[x][i][y] = elem['key']
                                    break
                        elif isinstance(ids, str):
                            if elem['key'].replace('[]', '') == ids:
                                either_required_list[x][i] = elem['key']
                                break


def recursive_update_schema_form_with_condition(
        schema_form, either_required_list):
    """Update chema form with condition.

    :param schema_form: The schema form
    :param either_required_list: Either required list
    """
    def prepare_either_condition_required(group_idx, key):
        """Prepare either condition required list."""
        _key = key.replace('[]', '')
        cond_1 = 'model.either_valid_' + str(group_idx)
        cond_2 = cond_1 + ".indexOf('" + _key + "')"
        return ["!{} || {} !== -1".format(cond_1, cond_2),
                "{} && {} === -1".format(cond_1, cond_2)]

    def set_on_change(elem):
        """Set onChange event."""
        calback_func_name = None
        if elem.get('onChange'):
            calback_func_name = elem.get('onChange').split('(')[0]
            elem['onChange'] = \
                "onChangeEitherField(this, form, modelValue, '" \
                + calback_func_name + "')"
        else:
            elem['onChange'] = \
                "onChangeEitherField(this, form, modelValue, undefined)"

    schema_form_condition = []
    for index, elem in enumerate(schema_form):
        if elem.get('items'):
            recursive_update_schema_form_with_condition(
                elem.get('items'), either_required_list)
        else:
            if elem.get('key'):
                for group_idx, group in enumerate(either_required_list):
                    for ids in group:
                        if isinstance(ids, list):
                            for _id in ids:
                                if elem['key'] == _id:
                                    set_on_change(elem)
                                    if len(group) != 1:
                                        cond_required, cond_not_required = \
                                            prepare_either_condition_required(
                                                group_idx, _id)
                                        condition_item = copy.deepcopy(elem)
                                        condition_item['required'] = True
                                        condition_item['condition'] \
                                            = cond_required
                                        schema_form_condition.append(
                                            {'index': index, 'item':
                                                condition_item})

                                        elem['condition'] = cond_not_required
                                    else:
                                        elem['required'] = True
                        elif isinstance(ids, str):
                            if elem['key'] == ids:
                                set_on_change(elem)
                                if len(group) != 1:
                                    cond_required, cond_not_required = \
                                        prepare_either_condition_required(
                                            group_idx, ids)
                                    condition_item = copy.deepcopy(elem)
                                    condition_item['required'] = True
                                    condition_item['condition'] = \
                                        cond_required
                                    schema_form_condition.append({
                                        'index': index,
                                        'item': condition_item})

                                    elem['condition'] = cond_not_required
                                else:
                                    elem['required'] = True

    for index, condition_item in enumerate(schema_form_condition):
        schema_form.insert(
            condition_item['index'] + index + 1,
            condition_item['item'])


def package_export_file(item_type_data):
    """Export TSV/CSV Files.

    Args:
        item_type_data (_type_): schema's Item Type

    Returns:
        _io.StringIO: TSV/CSV file
    """
    # current_app.logger.error("item_type_data:{}".format(item_type_data))
    file_output = StringIO()
    file_format = current_app.config.get('WEKO_ADMIN_OUTPUT_FORMAT', 'tsv').lower()
    file_delimiter = '\t' if file_format == 'tsv' else ','
    jsonschema_url = item_type_data.get('root_url') + item_type_data.get(
        'jsonschema')

    file_writer = csv.writer(file_output,
                             delimiter=file_delimiter,
                             lineterminator='\n')
    file_writer.writerow(['#ItemType',
                         item_type_data.get('name'),
                         jsonschema_url])

    keys = item_type_data['keys']
    labels = item_type_data['labels']
    is_systems = item_type_data['is_systems']
    options = item_type_data['options']
    file_metadata_writer = csv.DictWriter(file_output,
                                          fieldnames=keys,
                                          delimiter=file_delimiter,
                                          lineterminator='\n')
    file_metadata_label_writer = csv.DictWriter(file_output,
                                                fieldnames=labels,
                                                delimiter=file_delimiter,
                                                lineterminator='\n')
    file_metadata_is_system_writer = csv.DictWriter(file_output,
                                                    fieldnames=is_systems,
                                                    delimiter=file_delimiter,
                                                    lineterminator='\n')
    file_metadata_option_writer = csv.DictWriter(file_output,
                                                 fieldnames=options,
                                                 delimiter=file_delimiter,
                                                 lineterminator='\n')
    file_metadata_data_writer = csv.writer(file_output,
                                           delimiter=file_delimiter,
                                           lineterminator='\n')
    file_metadata_writer.writeheader()
    file_metadata_label_writer.writeheader()
    file_metadata_is_system_writer.writeheader()
    file_metadata_option_writer.writeheader()
    for recid in item_type_data.get('recids'):
        file_metadata_data_writer.writerow(
            [recid, item_type_data.get('root_url') + 'records/' + str(recid)]
            + item_type_data['data'].get(recid)
        )

    # current_app.logger.error("file_output: {}".format(file_output.getvalue()))
    return file_output


def make_stats_file(item_type_id, recids, list_item_role, export_path=""):
    """Prepare TSV/CSV data for each Item Types.

    Arguments:
        item_type_id    -- ItemType ID
        recids          -- List records ID
        export_path     -- path of temp_dir
    Returns:
        ret             -- Key properties
        ret_label       -- Label properties
        records.attr_output -- Record data
    Rises:
        KeyError: 'EMAIL_DISPLAY_FLG'
        KeyError: 'WEKO_RECORDS_UI_LICENSE_DICT'
        NameError: name '_' is not defined

    """
    from weko_records_ui.views import escape_newline, escape_str

    item_type = ItemTypes.get_by_id(item_type_id)
    if item_type:
        list_hide = get_item_from_option(item_type_id, item_type=ItemTypes(item_type.schema, model=item_type))
    else:
        list_hide = get_item_from_option(item_type_id)
    no_permission_show_hide = hide_meta_data_for_role(
        list_item_role.get(item_type_id))
    if no_permission_show_hide and item_type and item_type.render.get('table_row'):
        for name_hide in list_hide:
            item_type.render['table_row'] = hide_table_row(
                item_type.render.get('table_row'), name_hide)

    table_row_properties = item_type.render['table_row_map']['schema'].get(
        'properties')

    class RecordsManager:
        """Management data for exporting records."""

        first_recid = 0
        cur_recid = 0
        recids = []
        records = {}
        attr_data = {}
        attr_output = {}

        def __init__(self, record_ids):
            """Class initialization."""
            self.recids = record_ids
            self.first_recid = record_ids[0]
            for record_id in record_ids:
                record = WekoRecord.get_record_by_pid(record_id)

                # Custom Record Metadata for export
                _custom_export_metadata(record)

                self.records[record_id] = record
                self.attr_output[record_id] = []

        def get_max_ins(self, attr):
            """Get max data each main property in all exporting records."""
            largest_size = 1
            self.attr_data[attr] = {'max_size': 0}
            for record in self.records:
                if isinstance(self.records[record].get(attr), dict) \
                    and self.records[record].get(attr).get(
                        'attribute_value_mlt'):
                    self.attr_data[attr][record] = self.records[record][attr][
                        'attribute_value_mlt']
                else:
                    if self.records[record].get(attr):
                        self.attr_data[attr][record] = \
                            self.records[record].get(attr)
                    else:
                        self.attr_data[attr][record] = []
                rec_size = len(self.attr_data[attr][record])
                if rec_size > largest_size:
                    largest_size = rec_size
            self.attr_data[attr]['max_size'] = largest_size

            return self.attr_data[attr]['max_size']

        def get_max_ins_feedback_mail(self):
            """Get max data each feedback mail in all exporting records."""
            largest_size = 1
            self.attr_data['feedback_mail_list'] = {'max_size': 0}
            for record_id, record in self.records.items():
                if check_created_id(record):
                    mail_list = FeedbackMailList.get_mail_list_by_item_id(
                        record.id)
                    self.attr_data['feedback_mail_list'][record_id] = [
                        mail.get('email') for mail in mail_list]
                    if len(mail_list) > largest_size:
                        largest_size = len(mail_list)
            self.attr_data['feedback_mail_list']['max_size'] = largest_size

            return self.attr_data['feedback_mail_list']['max_size']

        def get_max_ins_request_mail(self):
            """Get max data each request mail in all exporting records."""
            largest_size = 1
            self.attr_data['request_mail_list'] = {'max_size': 0}
            for record_id, record in self.records.items():
                if check_created_id(record):
                    mail_list = RequestMailList.get_mail_list_by_item_id(
                        record.id)
                    self.attr_data['request_mail_list'][record_id] = [
                        mail.get('email') for mail in mail_list]
                    if len(mail_list) > largest_size:
                        largest_size = len(mail_list)
            self.attr_data['request_mail_list']['max_size'] = largest_size

            return self.attr_data['request_mail_list']['max_size']

        def get_max_items(self, item_attrs):
            """Get max data each sub property in all exporting records."""
            max_length = 0
            list_attr = []
            for attr in item_attrs.split('.'):
                index_left_racket = attr.find('[')
                if index_left_racket >= 0:
                    list_attr.extend(
                        [attr[:index_left_racket],
                         attr[index_left_racket:]]
                    )
                else:
                    list_attr.append(attr)

            level = len(list_attr)
            if level == 1:
                return self.attr_data[item_attrs]['max_size']
            elif level > 1:
                max_length = 1
                for record in self.records:
                    _data = self.records[record].get(list_attr[0])
                    if _data:
                        _data = _data['attribute_value_mlt']
                        for attr in list_attr[1:]:
                            if re.search(r'^\[\d+\]$', attr):
                                idx = int(attr[1:-1])
                                if isinstance(_data, list) \
                                        and len(_data) > idx:
                                    _data = _data[idx]
                                else:
                                    _data = []
                                    break
                            elif isinstance(_data, list):
                                _data = _data[0]
                                if isinstance(_data, dict) and _data.get(attr):
                                    _data = _data.get(attr)
                            elif isinstance(_data, dict) and _data.get(attr):
                                _data = _data.get(attr)
                            else:
                                _data = []
                                break
                        if isinstance(_data, list) and len(_data) > max_length:
                            max_length = len(_data)
            return max_length

        def get_subs_item(self,
                          item_key,
                          item_label,
                          properties,
                          data=None,
                          is_object=False):
            """Building key, label and data from key properties.

            Arguments:
                item_key    -- Key properties
                item_label  -- Label properties
                properties  -- Data properties
                data        -- Record data
                is_object   -- Is objecting property?
            Returns:
                o_ret       -- Key properties
                o_ret_label -- Label properties
                ret_data    -- Record data

            """
            o_ret = []
            o_ret_label = []
            ret_data = []
            max_items = self.get_max_items(item_key)
            max_items = 1 if is_object else max_items
            for idx in range(max_items):
                key_list = []
                key_label = []
                key_data = []
                for key in sorted(properties):
                    if not is_object:
                        new_key = '{}[{}].{}'.format(
                            item_key, str(idx), key)
                        new_label = '{}[{}].{}'.format(
                            item_label, str(idx), properties[key].get('title'))
                    else:
                        new_key = '{}.{}'.format(item_key, key)
                        new_label = '{}.{}'.format(
                            item_label, properties[key].get('title'))

                    if properties[key].get('format', '') == 'checkboxes':
                        new_key += '[{}]'
                        new_label += '[{}]'
                        if isinstance(data, dict):
                            data = [data]
                        if data and data[idx].get(key):
                            for idx_c in range(len(data[idx][key])):
                                key_list.append(new_key.format(idx_c))
                                key_label.append(new_label.format(idx_c))
                                key_data.append(data[idx][key][idx_c])
                        else:
                            key_list.append(new_key.format('0'))
                            key_label.append(new_label.format('0'))
                            key_data.append('')
                    elif properties[key]['type'] in ['array', 'object']:
                        if data and idx < len(data) and data[idx].get(key):
                            m_data = data[idx][key]
                        else:
                            m_data = None

                        if properties[key]['type'] == 'object':
                            new_properties = properties[key]['properties']
                            new_is_object = True
                        else:
                            new_properties = \
                                properties[key]['items']['properties']
                            new_is_object = False

                        sub, sublabel, subdata = self.get_subs_item(
                            new_key, new_label, new_properties,
                            m_data, new_is_object)
                        key_list.extend(sub)
                        key_label.extend(sublabel)
                        key_data.extend(subdata)
                    else:
                        if 'iscreator' in new_key:
                            continue
                        if isinstance(data, dict):
                            data = [data]
                        key_list.append(new_key)
                        key_label.append(new_label)
                        if data and idx < len(data) and data[idx].get(key):
                            key_data.append(escape_newline(data[idx][key]))
                            # key_data.append(escape_str(data[idx][key]))
                        else:
                            key_data.append('')

                key_list_len = len(key_list)
                for key_index in range(key_list_len):
                    item_key_split = item_key.split('.')
                    if 'filename' in key_list[key_index]:
                        key_list.insert(0, '.file_path[{}]'.format(
                            str(idx)))
                        key_label.insert(0, '.ファイルパス[{}]'.format(
                            str(idx)))
                        output_path = ""
                        if key_data[key_index]:
                            file_path = "recid_{}/{}".format(str(self.cur_recid), key_data[key_index])
                            output_path = file_path if os.path.exists(os.path.join(export_path,file_path)) else ""
                        key_data.insert(0,output_path)
                        break
                    elif 'thumbnail_label' in key_list[key_index] \
                            and len(item_key_split) == 2:
                        if '[' in item_key_split[0]:
                            key_list.insert(0, '.thumbnail_path[{}]'.format(
                                str(idx)))
                            key_label.insert(0, '.サムネイルパス[{}]'.format(
                                str(idx)))
                        else:
                            key_list.insert(0, '.thumbnail_path')
                            key_label.insert(0, '.サムネイルパス')
                        if key_data[key_index]:
                            key_data.insert(0, 'recid_{}/{}'.format(str(
                                self.cur_recid), key_data[key_index]))
                        else:
                            key_data.insert(0, '')
                        break

                o_ret.extend(key_list)
                o_ret_label.extend(key_label)
                ret_data.extend(key_data)

            return o_ret, o_ret_label, ret_data

    records = RecordsManager(recids)

    ret = ['#.id', '.uri']
    ret_label = ['#ID', 'URI']

    max_path = records.get_max_ins('path')
    for i in range(max_path):
        ret.append('.metadata.path[{}]'.format(i))
        ret.append('.pos_index[{}]'.format(i))
        ret_label.append('.IndexID[{}]'.format(i))
        ret_label.append('.POS_INDEX[{}]'.format(i))

    ret.append('.publish_status')
    ret_label.append('.PUBLISH_STATUS')

    max_feedback_mail = records.get_max_ins_feedback_mail()
    for i in range(max_feedback_mail):
        ret.append('.feedback_mail[{}]'.format(i))
        ret_label.append('.FEEDBACK_MAIL[{}]'.format(i))

    max_request_mail = records.get_max_ins_request_mail()
    for i in range(max_request_mail):
        ret.append('.request_mail[{}]'.format(i))
        ret_label.append('.REQUEST_MAIL[{}]'.format(i))

    ret.extend(['.cnri', '.doi_ra', '.doi', '.edit_mode'])
    ret_label.extend(['.CNRI', '.DOI_RA', '.DOI', 'Keep/Upgrade Version'])
    has_pubdate = len([
        record for _, record in records.records.items()
        if record.get('pubdate')
    ])
    if has_pubdate:
        ret.append('.metadata.pubdate')
        ret_label.append('公開日' if current_i18n.language == 'ja' else 'PubDate')

    for recid in recids:
        record = records.records[recid]
        paths = records.attr_data['path'][recid]
        index_infos = Indexes.get_path_list(paths)
        for info in index_infos:
            records.attr_output[recid].append(info.cid)
            records.attr_output[recid].append(info.name_en.replace(
                '-/-', current_app.config['WEKO_ITEMS_UI_INDEX_PATH_SPLIT']))
        records.attr_output[recid].extend(
            [''] * (max_path * 2 - len(records.attr_output[recid]))
        )

        records.attr_output[recid].append(
            'public' if record['publish_status'] == PublishStatus.PUBLIC.value else 'private')
        feedback_mail_list = records.attr_data['feedback_mail_list'] \
            .get(recid, [])
        records.attr_output[recid].extend(feedback_mail_list)
        records.attr_output[recid].extend(
            [''] * (max_feedback_mail - len(feedback_mail_list))
        )

        request_mail_list = records.attr_data['request_mail_list'] \
            .get(recid, [])
        records.attr_output[recid].extend(request_mail_list)
        records.attr_output[recid].extend(
            [''] * (max_request_mail - len(request_mail_list))
        )

        pid_cnri = record.pid_cnri
        cnri = ''
        if pid_cnri:
            cnri = pid_cnri.pid_value.replace(WEKO_SERVER_CNRI_HOST_LINK, '')
        records.attr_output[recid].append(cnri)

        identifier = IdentifierHandle(record.pid_recid.object_uuid)
        doi_value, doi_type = identifier.get_idt_registration_data()
        doi_type_str = doi_type[0] if doi_type and doi_type[0] else ''
        doi_str = doi_value[0] if doi_value and doi_value[0] else ''
        if doi_type_str and doi_str:
            doi_domain = ''
            if doi_type_str == WEKO_IMPORT_DOI_TYPE[0]:
                doi_domain = IDENTIFIER_GRANT_LIST[1][2]
            elif doi_type_str == WEKO_IMPORT_DOI_TYPE[1]:
                doi_domain = IDENTIFIER_GRANT_LIST[2][2]
            elif doi_type_str == WEKO_IMPORT_DOI_TYPE[2]:
                doi_domain = IDENTIFIER_GRANT_LIST[3][2]
            elif doi_type_str == WEKO_IMPORT_DOI_TYPE[3]:
                doi_domain = IDENTIFIER_GRANT_LIST[4][2]
            if doi_domain and doi_str.startswith(doi_domain):
                doi_str = doi_str.replace(doi_domain + '/', '', 1)
        records.attr_output[recid].extend([
            doi_type_str,
            doi_str
        ])
        # .edit Keep/Upgrade default is Keep
        records.attr_output[recid].append('Keep')
        if has_pubdate:
            pubdate = record.get('pubdate', {}).get('attribute_value', '')
            records.attr_output[recid].append(pubdate)

    for item_key in item_type.render.get('table_row'):
        item = table_row_properties.get(item_key)
        records.get_max_ins(item_key)
        keys = []
        labels = []
        for recid in recids:
            records.cur_recid = recid
            if item.get('type') == 'array':
                key, label, data = records.get_subs_item(
                    item_key,
                    item.get('title'),
                    item['items']['properties'],
                    records.attr_data[item_key][recid]
                )
                if not keys:
                    keys = key
                if not labels:
                    labels = label
                records.attr_output[recid].extend(data)
            elif item.get('type') == 'object':
                key, label, data = records.get_subs_item(
                    item_key,
                    item.get('title'),
                    item['properties'],
                    records.attr_data[item_key][recid],
                    True
                )
                if not keys:
                    keys = key
                if not labels:
                    labels = label
                records.attr_output[recid].extend(data)
            else:
                if not keys:
                    keys = [item_key]
                if not labels:
                    labels = [item.get('title')]
                data = records.attr_data[item_key].get(recid) or {}
                attr_val = data.get("attribute_value", "")
                if isinstance(attr_val,str):
                    records.attr_output[recid].append(attr_val)
                else:
                    records.attr_output[recid].extend(attr_val)

        new_keys = []
        for key in keys:
            if 'file_path' not in key and 'thumbnail_path' not in key:
                key = '.metadata.{}'.format(key)
            new_keys.append(key)
        ret.extend(new_keys)
        ret_label.extend(labels)

    ret_system = []
    ret_option = []
    multiple_option = ['.metadata.path', '.pos_index',
                       '.feedback_mail', '.request_mail', '.file_path', '.thumbnail_path']
    meta_list = item_type.render.get('meta_list', {})
    meta_list.update(item_type.render.get('meta_fix', {}))
    form = item_type.render.get('table_row_map', {}).get('form', {})
    del_num = 0
    total_col = len(ret)
    for index in range(total_col):
        _id = ret[index - del_num]
        key = re.sub(r'\[\d+\]', '[]', _id.replace('.metadata.', ''))
        root_key = key.split('.')[0].replace('[]', '')
        if root_key in meta_list:
            is_system = check_sub_item_is_system(key, form)
            ret_system.append('System' if is_system else '')

            _, _, root_option = get_root_item_option(
                root_key,
                meta_list.get(root_key)
            )
            sub_options = get_sub_item_option(key, form)
            if not sub_options:
                ret_option.append(', '.join(root_option))
            else:
                if no_permission_show_hide and 'Hide' in sub_options:
                    del ret[index - del_num]
                    del ret_label[index - del_num]
                    del ret_system[index - del_num]
                    for recid in recids:
                        del records.attr_output[recid][index - del_num - 2]
                    del_num += 1
                else:
                    ret_option.append(
                        ', '.join(list(set(root_option + sub_options)))
                    )
        elif key == '#.id':
            ret_system.append('#')
            ret_option.append('#')
        elif key == '.edit_mode' or key == '.publish_status':
            ret_system.append('')
            ret_option.append('Required')
        elif '[' in _id and _id.split('[')[0] in multiple_option:
            ret_system.append('')
            ret_option.append('Allow Multiple')
        else:
            ret_system.append('')
            ret_option.append('')

    return [ret, ret_label, ret_system, ret_option], records.attr_output


def get_list_file_by_record_id(recid):
    """Get file buckets by record id.

    Arguments:
        recid     -- {number} record id.
    Returns:
        list_file  -- list file name of record.

    """
    body = {
        "query": {
            "function_score": {
                "query": {
                    "match": {
                        "_id": recid
                    }
                }
            }
        },
        "_source": ["file"],
        "size": 1
    }
    indexer = RecordIndexer()
    result = indexer.client.search(
        index=current_app.config['INDEXER_DEFAULT_INDEX'],
        body=body
    )
    list_file_name = []

    if isinstance(result, dict) and isinstance(result.get('hits'), dict) and \
            isinstance(result['hits'].get('hits'), list) and \
            len(result['hits']['hits']) > 0 and \
            isinstance(result['hits']['hits'][0], dict) and \
            isinstance(result['hits']['hits'][0].get('_source'), dict) and \
            isinstance(result['hits']['hits'][0]['_source'].get('file'), dict)\
            and result['hits']['hits'][0]['_source']['file'].get('URI'):
        list_file = result['hits']['hits'][0]['_source']['file'].get('URI')

        list_file_name = [
            recid + '/' + item.get('value') for item in list_file]
    return list_file_name


def write_bibtex_files(item_types_data, export_path):
    """Write Bibtex data to files.

    @param item_types_data:
    @param export_path:
    @return:
    """
    # current_app.logger.error("item_types_data:{}".format(item_types_data))
    # current_app.logger.error("export_path:{}".format(export_path))

    for item_type_id in item_types_data:
        item_type_data = item_types_data[item_type_id]
        output = make_bibtex_data(item_type_data['recids'])
        # create file to write data in case has output of Bibtex
        if output:
            with open('{}/{}.bib'.format(export_path,
                                         item_type_data.get('name')),
                      'w', encoding='utf8') as file:
                file.write(output)


def write_files(item_types_data, export_path, list_item_role):
    """Write TSV/CSV data to files.

    @param item_types_data:
    @param export_path:
    @param list_item_role:
    @return:
    """
    current_app.logger.debug("item_types_data:{}".format(item_types_data))
    current_app.logger.debug("export_path:{}".format(export_path))
    current_app.logger.debug("list_item_role:{}".format(list_item_role))
    file_format = current_app.config.get('WEKO_ADMIN_OUTPUT_FORMAT', 'tsv').lower()

    for item_type_id in item_types_data:

        current_app.logger.debug("item_type_id:{}".format(item_type_id))
        current_app.logger.debug("item_types_data[item_type_id]['recids']:{}".format(item_types_data[item_type_id]['recids']))
        headers, records = make_stats_file(
            item_type_id,
            item_types_data[item_type_id]['recids'],
            list_item_role,
            export_path)
        current_app.logger.debug("headers:{}".format(headers))
        current_app.logger.debug("records:{}".format(records))
        keys, labels, is_systems, options = headers
        item_types_data[item_type_id]['recids'].sort()
        item_types_data[item_type_id]['keys'] = keys
        item_types_data[item_type_id]['labels'] = labels
        item_types_data[item_type_id]['is_systems'] = is_systems
        item_types_data[item_type_id]['options'] = options
        item_types_data[item_type_id]['data'] = records
        item_type_data = item_types_data[item_type_id]
        with open('{}/{}.{}'.format(export_path,
                                    item_type_data.get('name'),
                                    file_format),
                  'w', encoding="utf-8-sig") as file:
            file_output = package_export_file(item_type_data)
            file.write(file_output.getvalue())


def check_item_type_name(name):
    """Check a list of allowed characters in filenames.

    :return: new name
    """
    new_name = re.sub(r'[\/:*"<>|\s]', '_', name)
    return new_name


def export_items(post_data):
    """Gather all the item data and export and return as a JSON or BIBTEX.

    :return: JSON, BIBTEX
    """
    current_app.logger.debug("post_data:{}".format(post_data))
    include_contents = (
        True if post_data.get('export_file_contents_radio') == 'True' else False
    )
    export_format = post_data['export_format_radio']
    record_ids = json.loads(post_data['record_ids'])
    invalid_record_ids = json.loads(post_data['invalid_record_ids'])
    if isinstance(invalid_record_ids,dict) or isinstance(invalid_record_ids,list):
        invalid_record_ids = [int(i) for i in invalid_record_ids]
    else:
        invalid_record_ids = [invalid_record_ids]
    # Remove all invalid records
    record_ids = list(set(record_ids) - set(invalid_record_ids))
    record_metadata = (
        json.loads(post_data['record_metadata'])
        if post_data.get('record_metadata') else {}
    )
    if len(record_ids) > _get_max_export_items():
        return abort(400)
    elif len(record_ids) == 0:
        return '',204

    result = {'items': []}
    temp_path = tempfile.TemporaryDirectory(
        prefix=current_app.config['WEKO_ITEMS_UI_EXPORT_TMP_PREFIX']
    )
    item_types_data = {}

    try:
        # Set export folder
        datetime_now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        export_path = os.path.join(temp_path.name, datetime_now)

        if export_format == "ROCRATE":
            make_rocrate(record_ids, export_path)
        else:
            # Double check for limits
            for record_id in record_ids:
                record_path = export_path + '/recid_' + str(record_id)
                os.makedirs(record_path, exist_ok=True)
                exported_item, list_item_role = _export_item(
                    record_id,
                    export_format,
                    include_contents,
                    record_path,
                    record_metadata.get(str(record_id))
                )
                result['items'].append(exported_item)

                item_type_id = exported_item.get('item_type_id')
                item_type = ItemTypes.get_by_id(item_type_id)
                if not item_types_data.get(item_type_id):
                    item_type_name = check_item_type_name(
                        item_type.item_type_name.name
                    )
                    item_types_data[item_type_id] = {
                        'item_type_id': item_type_id,
                        'name': f'{item_type_name}({item_type_id})',
                        'root_url': request.url_root,
                        'jsonschema': 'items/jsonschema/' + item_type_id,
                        'keys': [],
                        'labels': [],
                        'recids': [],
                        'data': {},
                    }
                item_types_data[item_type_id]['recids'].append(record_id)

            # Create export info file
            if export_format == 'BIBTEX':
                write_bibtex_files(item_types_data, export_path)
            else:
                write_files(item_types_data, export_path, list_item_role)

            # Create bag
            bagit.make_bag(export_path)
        # Create download file
        # zip filename: export_{uuid}-{%Y%m%d%H%M%S}
        zip_path = os.path.join(
            tempfile.gettempdir(),
            export_path.split("/")[-2] + "-" + export_path.split("/")[-1]
        )
        shutil.make_archive(zip_path, 'zip', export_path)
    except Exception:
        current_app.logger.error("Failed to export items.")
        traceback.print_exc()
        flash(_('Error occurred during item export.'), 'error')
        return redirect(url_for('weko_items_ui.export'))
    resp = send_file(
        zip_path+".zip",
        as_attachment=True,
        attachment_filename='export.zip'
    )
    os.remove(zip_path+".zip")
    temp_path.cleanup()
    return resp


def make_rocrate(record_ids, export_path):
    """Make RO-Crate BagIt for export.

    Args:
        record_ids (list): List of record IDs to export.
        export_path (str): Path to export the RO-Crate.
    """
    # Get Metadata from ElasticSearch
    metadata_dict = _get_metadata_dict_in_es(record_ids)

    for record_id in record_ids:
        # crate each record directory
        record_path = os.path.join(export_path, f"recid_{record_id}")
        os.makedirs(record_path, exist_ok=True)
        _export_file(record_id, record_path)
        # Metadata
        metadata, filenames = metadata_dict.get(str(record_id), ({}, []))
        item_type_id = metadata.get("item_type_id")
        mappings = JsonldMapping.get_by_itemtype_id(item_type_id)
        mapper = JsonLdMapper(item_type_id, None)
        for m in mappings:
            mapper.json_mapping = m.mapping
            if mapper.is_valid:
                break
        if mapper.json_mapping is None:
            raise Exception("No valid mapping found for item type")

        # Create RO-Crate info file
        rocrate = mapper.to_rocrate_metadata(
            metadata, extracted_files=filenames
        )
        jsonld_path = os.path.join(
            record_path, ROCRATE_METADATA_FILE.split("/")[-1]
        )
        with open(jsonld_path, "w", encoding="utf8") as f:
            json.dump(
                rocrate.metadata.generate(), f, indent=2, sort_keys=True,
                ensure_ascii=False
            )

        bagit.make_bag(record_path, checksums=["sha256"])

        shutil.make_archive(record_path, "zip", record_path)
        shutil.rmtree(record_path)

    # Create README.md file
    readme_path = os.path.join(export_path, "README.md")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    source_path = current_app.config["WEKO_ITEMS_UI_README_MD"]
    src_readme_path = os.path.join(current_dir, source_path)
    shutil.copyfile(src_readme_path, readme_path)


def _get_metadata_dict_in_es(record_ids):
    """Get metadata by record id from ElasticSearch.

    :param record_ids: Record IDs
    :return: Metadata
    """
    metadata_dict = {}
    try:
        # Get metadata from ElasticSearch
        search = RecordsSearch(
            index=current_app.config["SEARCH_UI_SEARCH_INDEX"])
        search = search.filter("terms", control_number=record_ids)
        search = search.filter("term", relation_version_is_last=True)
        search = search.sort("control_number")
        search = search.source(["_item_metadata", "content"])
        search = search.params(from_=0, size=100)
        search_result = search.execute().to_dict()
        record_list = search_result.get("hits", {}).get("hits", [])
        for record in record_list:
            [key] = record.get("sort")
            metadata = record.get("_source", {}).get("_item_metadata", {})
            content = record.get("_source", {}).get("content", [])
            extraction_file_list = [
                file_content.get("filename") for file_content in content
            ]
            metadata_dict.update({key: (metadata, extraction_file_list)})
    except NotFoundError as e:
        current_app.logger.error("Index do not exist yet: ", str(e))

    return metadata_dict


def _get_max_export_items():
    """Get max amount of items to export."""
    max_table = current_app.config['WEKO_ITEMS_UI_MAX_EXPORT_NUM_PER_ROLE']
    non_user_max = current_app.config['WEKO_ITEMS_UI_DEFAULT_MAX_EXPORT_NUM']
    current_user_id = current_user.get_id()

    if not current_user_id:  # Non-logged in users
        return non_user_max

    try:
        roles = db.session.query(Role).join(userrole).filter_by(
            user_id=current_user_id).all()
    except Exception:
        return current_app.config['WEKO_ITEMS_UI_DEFAULT_MAX_EXPORT_NUM']

    current_max = non_user_max
    for role in roles:
        if role in max_table and max_table[role] > current_max:
            current_max = max_table[role]
    return current_max


def _export_item(record_id,
                 export_format,
                 include_contents,
                 tmp_path=None,
                 records_data=None):
    """Exports files for record according to view permissions.

    Args:
        record_id (_type_): _description_
        export_format (_type_): _description_
        include_contents (bool): _description_
        tmp_path (_type_, optional): _description_. Defaults to None.
        records_data (dict, optional): _description_. Defaults to None.
    """
    # current_app.logger.error("record_id:{}".format(record_id))
    # current_app.logger.error("export_format:{}".format(export_format))
    # current_app.logger.error("include_contents:{}".format(include_contents))
    # current_app.logger.error("tmp_path:{}".format(tmp_path))
    # current_app.logger.error("records_data:{}".format(records_data))
    def del_hide_sub_metadata(keys, metadata):
        """Delete hide metadata."""
        if isinstance(metadata, dict):
            data = metadata.get(keys[0])
            if data:
                if len(keys) > 1:
                    del_hide_sub_metadata(keys[1:], data)
                else:
                    del metadata[keys[0]]
        elif isinstance(metadata, list):
            count = len(metadata)
            for index in range(count):
                del_hide_sub_metadata(keys[1:] if len(
                    keys) > 1 else keys, metadata[index])

    exported_item = {}
    record = WekoRecord.get_record_by_pid(record_id)
    list_item_role = {}
    if record:
        exported_item['record_id'] = record.id
        exported_item['name'] = 'recid_{}'.format(record_id)
        exported_item['files'] = []
        exported_item['path'] = 'recid_' + str(record_id)
        exported_item['item_type_id'] = record.get('item_type_id')
        if not records_data:
            records_data = record
        if exported_item['item_type_id']:
            item_type_id = exported_item['item_type_id']
            list_hidden = []
            item_type = ItemTypes.get_by_id(item_type_id)
            if item_type:
                list_hidden = get_ignore_item_from_mapping(item_type_id, item_type)
            if records_data.get('metadata'):
                meta_data = records_data.get('metadata')
                _custom_export_metadata(meta_data.get('_item_metadata', {}),
                                        False, False)
                record_role_ids = {
                    'weko_creator_id': meta_data.get('weko_creator_id'),
                    'weko_shared_id': meta_data.get('weko_shared_id')
                }
                list_item_role.update(
                    {exported_item['item_type_id']: record_role_ids})
                if hide_meta_data_for_role(record_role_ids):
                    for hide_key in list_hidden:
                        if isinstance(hide_key, str) \
                                and meta_data.get(hide_key):
                            del records_data['metadata'][hide_key]
                        elif isinstance(hide_key, list):
                            del_hide_sub_metadata(
                                hide_key, records_data['metadata'])

        # Create metadata file.
        # with open('{}/{}_metadata.json'.format(tmp_path,
        #                                        exported_item['name']),
        #           'w',
        #           encoding='utf8') as output_file:
        #     json.dump(records_data, output_file, indent=2,
        #               sort_keys=True, ensure_ascii=False)
        # First get all of the files, checking for permissions while doing so
        if include_contents:
            # Get files
            for file in record.files:  # TODO: Temporary processing
                if check_file_download_permission(record, file.info()):
                    if file.info().get('accessrole') != 'open_restricted':
                        exported_item['files'].append(file.info())
                        # TODO: Then convert the item into the desired format
                        if file:
                            file_buffered = file.obj.file.storage().open()
                            temp_file = open(
                                tmp_path + '/' + file.obj.basename, 'wb')
                            temp_file.write(file_buffered.read())
                            temp_file.close()

    return exported_item, list_item_role


def _export_file(record_id, data_path=None):
    """Exports files for record according to view permissions.

    :param record_id: Record ID
    :param data_path: Data Path. Defaults to None.
    """
    record = WekoRecord.get_record_by_pid(record_id)
    if record:
        # Get files
        for file in record.files:
            if check_file_download_permission(record, file.info()):
                accessrole = file.info().get("accessrole")
                if accessrole == "open_restricted":
                    continue
                if accessrole == "open_date":
                    file_date = file.info().get("date", {})
                    date_value = (
                        file_date[0].get("dateValue")
                            if isinstance(file_date, list) and file_date
                        else file_date.get("dateValue")
                            if isinstance(file_date, dict)
                        else None
                    )
                    open_date = datetime.strptime(date_value, "%Y-%m-%d")
                    if open_date.date() > datetime.now().date():
                        continue
                with file.obj.file.storage().open() as file_buffered:
                    tmp_path = os.path.join(data_path, file.obj.basename)
                    with open(tmp_path, "wb") as temp_file:
                        temp_file.write(file_buffered.read())


def _custom_export_metadata(record_metadata: dict, hide_item: bool = True,
                            replace_license: bool = True):
    """Custom export metadata.

    Args:
        record_metadata (dict): Record metadata
        hide_item (bool): Hide item flag.
        replace_license (bool): Replace license flag.
    """
    from weko_records_ui.utils import hide_item_metadata, replace_license_free
    # current_app.logger.error("record_metadata:{}".format(record_metadata))
    # Hide private metadata
    if hide_item:
        hide_item_metadata(record_metadata)
    # Change the item name 'licensefree' to 'license_note'.
    if replace_license:
        replace_license_free(record_metadata, False)

    for k, v in record_metadata.items():
        if isinstance(v, dict) and v.get('attribute_type') == 'file':
            replace_fqdn_of_file_metadata(v.get("attribute_value_mlt", []))


def get_new_items_by_date(start_date: str, end_date: str, ranking=False) -> dict:
    """Get ranking new item by date.

    :param start_date:
    :param end_date:
    :param ranking:
    :return:
    """
    record_search = RecordsSearch(
        index=current_app.config['SEARCH_UI_SEARCH_INDEX'])
    result = dict()

    try:
        indexes = Indexes.get_public_indexes_list()
        if len(indexes) == 0:
            return result
        search_instance, _qs_kwargs = item_search_factory(None,
                                                          record_search,
                                                          start_date,
                                                          end_date,
                                                          indexes,
                                                          query_with_publish_status=False,
                                                          ranking=ranking)
        search_result = search_instance.execute()
        result = search_result.to_dict()
    except NotFoundError as e:
        current_app.logger.debug("Indexes do not exist yet: ", str(e))

    return result


def update_schema_remove_hidden_item(schema, render, items_name):
    """Update schema: remove hidden items.

    :param schema: json schema
    :param render: json render
    :param items_name: list items which has hidden flg
    :return: The json object.
    """
    for item in items_name:
        hidden_flg = False
        key = schema[item]['key']
        if render['meta_list'].get(key):
            hidden_flg = render['meta_list'][key]['option']['hidden']
        if render.get('meta_system') and render['meta_system'].get(key):
            hidden_flg = render['meta_system'][key]['option']['hidden']
        if hidden_flg:
            schema[item]['condition'] = 1

    return schema


def get_files_from_metadata(record):
    """
    Get files from record meta_data.

    @param record:
    @return:
    """
    current_app.logger.debug("record: {}".format(record))
    files = OrderedDict()
    for key in record:
        meta_data = record.get(key)
        if isinstance(meta_data, dict) and \
                meta_data.get('attribute_type', '') == "file":
            file_metadata = meta_data.get("attribute_value_mlt", [])
            for f in file_metadata:
                if f.get("version_id"):
                    files[f["version_id"]] = f
            break
    current_app.logger.debug("files: {}".format(files))
    return files


def to_files_js(record):
    """List files in a deposit.

    Args:
        record (WekoDeposit): record object.

    Returns:
        list: File information taken from metadata
    """
    current_app.logger.debug("type: {}".format(type(record)))
    res = []
    files = record.files or []
    files_content_dict = {}
    files_thumbnail = []
    for f in files:
        if f.is_thumbnail:
            files_thumbnail.append(f)
        else:
            files_content_dict[f.key] = f
    # Get files form meta_data, so that you can append any extra info to files
    # (which not contained by file_bucket) such as license below
    files_from_meta = get_files_from_metadata(record)

    # get file with order similar metadata
    files_content = []
    for _k, f in files_from_meta.items():
        if files_content_dict.get(f.get('filename')):
            files_content.append(files_content_dict.get(f.get('filename')))

    for f in [*files_content, *files_thumbnail]:
        res.append({
            'displaytype': files_from_meta.get(str(f.version_id),
                                               {}).get("displaytype", ''),
            'filename': f.get('filename', ''),
            'mimetype': f.mimetype,
            'licensetype': files_from_meta.get(str(f.version_id),
                                               {}).get("licensetype", ''),
            'key': f.key,
            'version_id': str(f.version_id),
            'checksum': f.file.checksum,
            'size': f.file.size,
            'completed': True,
            'progress': 100,
            'links': {
                'self': (
                    current_app.config['DEPOSIT_FILES_API']
                    + u'/{bucket}/{key}?versionId={version_id}'.format(
                        bucket=f.bucket_id,
                        key=f.key,
                        version_id=f.version_id,
                    )),
            },
            'is_show': f.is_show,
            'is_thumbnail': f.is_thumbnail
        })

    return res


def update_sub_items_by_user_role(item_type_id, schema_form):
    """Update sub item by user role.

    @param item_type_id:
    @param schema_form:
    @return:
    """
    item_type_name = get_item_type_name(item_type_id)
    excluded_sub_items = get_excluded_sub_items(item_type_name)
    excluded_forms = []
    for form in schema_form:
        if "title_{}".format(form.get('title')).lower() in excluded_sub_items:
            excluded_forms.append(form)
        elif form.get('items') and \
                form['items'][0]['key'].split('.')[1] in excluded_sub_items:
            excluded_forms.append(form)
    for item in excluded_forms:
        schema_form.remove(item)


def remove_excluded_items_in_json_schema(item_id, json_schema):
    """Remove excluded items in json_schema.

    :item_id: object
    :json_schema: object
    """
    # Check role for input(5 item type)
    item_type_name = get_item_type_name(item_id)
    excluded_sub_items = get_excluded_sub_items(item_type_name)
    if len(excluded_sub_items) == 0:
        return
    """ Check excluded sub item name which exist in json_schema """
    """     Case exist => add sub item to array """
    properties = json_schema.get('properties')
    removed_json_schema = []
    if properties:
        for pro in properties:
            pro_val = properties.get(pro)
            sub_pro = pro_val.get('properties')
            if pro_val and sub_pro:
                for sub_item in excluded_sub_items:
                    sub_property = sub_pro.get(sub_item)
                    if sub_property:
                        removed_json_schema.append(pro)
    """ If sub item array have data, we remove sub items im json_schema """
    if len(removed_json_schema) > 0:
        for item in removed_json_schema:
            if properties.get(item):
                del properties[item]


def get_excluded_sub_items(item_type_name):
    """Get excluded sub items by role.

    :item_type_name: object
    """
    usage_application_item_type = current_app.config.get(
        'WEKO_ITEMS_UI_USAGE_APPLICATION_ITEM_TYPE')
    if (not usage_application_item_type or not isinstance(
            usage_application_item_type, dict)):
        return []
    current_user_role = get_current_user_role()
    item_type_role = []
    item_type = usage_application_item_type.get(item_type_name.strip())
    if current_user_role and item_type and item_type.get(
            current_user_role.name):
        item_type_role = item_type.get(current_user_role.name)
    return item_type_role


def get_current_user_role():
    """Get current user roles."""
    current_user_role = ''
    for role in current_user.roles:
        if role in current_app.config['WEKO_USERPROFILES_ROLES']:
            current_user_role = role
            break
    return current_user_role


def is_need_to_show_agreement_page(item_type_name):
    """Check need to show Terms and Conditions or not."""
    current_user_role = get_current_user_role()
    general_role = current_app.config['WEKO_USERPROFILES_GENERAL_ROLE']
    item_type_list = current_app.config[
        'WEKO_ITEMS_UI_LIST_ITEM_TYPE_NOT_NEED_AGREE']
    if (current_user_role == general_role
            and item_type_name in item_type_list):
        return False
    return True


def update_index_tree_for_record(pid_value, index_tree_id):
    """Update index tree for record.

    :param index_tree_id:
    :param pid_value: pid value to get record and WekoDeposit
    :return:True set successfully otherwise False
    """
    list_index = []
    list_index.append(index_tree_id)
    data = {"index": list_index}
    record = WekoRecord.get_record_by_pid(pid_value)
    deposit = WekoDeposit(record, record.model)
    # deposit.clear()
    deposit.update(data)
    deposit.commit()


def validate_user_mail(users, activity_id, request_data, keys, result):
    """Validate user mail.

    @param result:
    @param keys:
    @param users:
    @param activity_id:
    @param request_data:
    @return:
    """
    result['validate_required_email'] = []
    result['validate_register_in_system'] = []
    for index, user in enumerate(users):
        email = request_data.get(user)
        user_info = get_user_info_by_email(email)
        action_order = check_approval_email(activity_id, user)
        if action_order:
            if not email:
                result['validate_required_email'].append(keys[index])
            elif not (user_info and user_info.get('user_id') is not None):
                result['validate_register_in_system'].append(keys[index])
            if email and user_info and \
                    user_info.get('user_id') is not None:
                update_action_handler(activity_id,
                                        action_order,
                                        user_info.get('user_id'))
                keys = True
                continue
    result[
        'validate_map_flow_and_item_type'] = check_approval_email_in_flow(
        activity_id, users)

    return result


def check_approval_email(activity_id, user):
    """Check approval email.

    @param user:
    @param activity_id:
    @return:
    """
    action_order = db.session.query(FlowAction.action_order) \
        .outerjoin(FlowActionRole).outerjoin(FlowDefine) \
        .outerjoin(Activity) \
        .filter(Activity.activity_id == activity_id) \
        .filter(FlowActionRole.specify_property == user) \
        .first()
    return action_order[0] if action_order and action_order[0] else None


def check_approval_email_in_flow(activity_id, users):
    """Count approval email.

    @param users:
    @param activity_id:
    @return:
    """
    flow_action_role = FlowActionRole.query \
        .outerjoin(FlowAction).outerjoin(FlowDefine) \
        .outerjoin(Activity) \
        .filter(Activity.activity_id == activity_id) \
        .filter(FlowActionRole.specify_property.isnot(None)) \
        .all()

    map_list = [y for x in flow_action_role for y in users if
                x.specify_property == y]
    return True if len(map_list) == len(flow_action_role) else False


def update_action_handler(activity_id, action_order, user_id):
    """Update action handler for each action of activity.

    :param activity_id:
    :param action_order:
    :param user_id:
    :return:
    """
    from weko_workflow.models import ActivityAction
    with db.session.begin_nested():
        activity_action = ActivityAction.query.filter_by(
            activity_id=activity_id,
            action_order=action_order).one_or_none()
        if activity_action:
            activity_action.action_handler = user_id
            db.session.merge(activity_action)


def validate_user_mail_and_index(request_data):
    """Validate user's mail,index tree.

    :param request_data:
    :return:
    """
    # current_app.logger.error("request_data:{}".format(request_data))
    users = request_data.get('user_to_check', [])
    keys = request_data.get('user_key_to_check', [])
    auto_set_index_action = request_data.get('auto_set_index_action', False)
    activity_id = request_data.get('activity_id')
    result = {
        "index": True
    }
    try:
        result = validate_user_mail(users, activity_id, request_data, keys,
                                    result)
        if auto_set_index_action is True:
            is_existed_valid_index_tree_id = True if \
                get_index_id(activity_id) else False
            result['index'] = is_existed_valid_index_tree_id
        db.session.commit()
    except Exception as ex:
        result['validation'] = False
        db.session.rollback()
        import traceback
        traceback.print_exc()
        result['error'] = str(ex)
    return result


def recursive_form(schema_form):
    """
    Recur the all the child form to set value for specific property.

    :param schema_form:
    :return: from result
    """
    for form in schema_form:
        if 'items' in form:
            recursive_form(form.get('items', []))
        # Set value for titleMap of select in case of position
        # and select format
        if (form.get('title', '') == 'Position' and form.get('type', '')
                == 'select'):
            dict_data = []
            positions = current_app.config.get(
                'WEKO_USERPROFILES_POSITION_LIST')
            for val in positions:
                if val[0]:
                    current_position = {
                        "value": val[0],
                        "name": str(val[1])
                    }
                    dict_data.append(current_position)
                    form['titleMap'] = dict_data


def set_multi_language_name(item, cur_lang):
    """Set multi language name: Get corresponding language and set to json.

    :param item: json object
    :param cur_lang: current language
    :return: The modified json object.
    """
    try:
        if 'titleMap' in item:
            for value in item['titleMap']:
                if 'name_i18n' in value \
                        and len(value['name_i18n'][cur_lang]) > 0:
                    value['name'] = value['name_i18n'][cur_lang]
    except Exception as ex:
        if 'titleMap' in item:
            for value in item['titleMap']:
                if 'name_i18n' in value \
                        and len(value['name_i18n']['en']) > 0:
                    value['name'] = value['name_i18n']['en']


def get_data_authors_prefix_settings():
    """Get all authors prefix settings."""
    from weko_authors.models import AuthorsPrefixSettings
    try:
        return db.session.query(AuthorsPrefixSettings).all()
    except Exception as e:
        current_app.logger.error(e)
        return None

def get_data_authors_affiliation_settings():
    """Get all authors affiliation settings."""
    from weko_authors.models import AuthorsAffiliationSettings
    try:
        return db.session.query(AuthorsAffiliationSettings).all()
    except Exception as e:
        current_app.logger.error(e)
        return None

def get_weko_link(metadata):
    """
    メタデータからweko_idを取得し、weko_idに対応するpk_idと一緒に
    weko_linkを作成します。
    args
        metadata: dict
        例：{
                "metainfo": {
                    "item_30002_creator2": [
                        {
                            "nameIdentifiers": [
                                {
                                    "nameIdentifier": "8",
                                    "nameIdentifierScheme": "WEKO",
                                    "nameIdentifierURI": ""
                                }
                            ]
                        }
                    ]
                },
                "files": [],
                "endpoints": {
                    "initialization": "/api/deposits/items"
                }
            }
    return
        weko_link: dict
        例：{"2": "10002"}
    """
    weko_link = {}
    weko_id_list=[]
    for x in metadata["metainfo"].values():
        if not isinstance(x, list):
            continue
        for y in x:
            if not isinstance(y, dict):
                continue
            for key, value in y.items():
                if not key == "nameIdentifiers":
                    continue
                for z in value:
                    if z.get("nameIdentifierScheme","") == "WEKO":
                        if z.get("nameIdentifier","") not in weko_id_list:
                            weko_id_list.append(z.get("nameIdentifier"))
    weko_link = {}
    for weko_id in weko_id_list:
        pk_id = WekoAuthors.get_pk_id_by_weko_id(weko_id)
        if int(pk_id) > 0:
            weko_link[pk_id] = weko_id
    return weko_link

def hide_meta_data_for_role(record):
    """
    Show hide metadate for curent user role.

    :return:
    """
    is_hidden = True

    # Admin users
    supers = current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER']

    roles = current_user.roles if current_user else []
    for role in list(roles):
        if role.name in supers:
            is_hidden = False
            break
    # Community users
    community_role_names = current_app.config[
        'WEKO_PERMISSION_ROLE_COMMUNITY']
    for role in list(roles):
        if role.name in community_role_names:
            is_hidden = False
            break

    # Item Register users and Sharing users
    if record and current_user.get_id() in [
        record.get('weko_creator_id'),
            str(record.get('weko_shared_id'))]:
        is_hidden = False

    return is_hidden


def get_ignore_item_from_mapping(_item_type_id, item_type):
    """Get ignore item from mapping.

    :param _item_type_id:
    :param item_type:
    :return ignore_list:
    """
    ignore_list = []
    meta_options, item_type_mapping = get_options_and_order_list(
        _item_type_id, item_type_data=ItemTypes(item_type.schema, model=item_type))
    sub_ids = get_hide_list_by_schema_form(item_type=item_type)
    for key, val in meta_options.items():
        hidden = val.get('option').get('hidden')
        if hidden:
            ignore_list.append(
                get_mapping_name_item_type_by_key(key, item_type_mapping))
    for sub_id in sub_ids:
        key = [re.sub(r'\[\d*\]', '', _id) for _id in sub_id.split('.')]
        if key[0] in item_type_mapping:
            mapping = item_type_mapping.get(key[0]).get('jpcoar_mapping')
            if isinstance(mapping, dict):
                for _name in mapping.keys():
                    name = None
                    if len(key) > 1:
                        tree_name = get_mapping_name_item_type_by_sub_key(
                            '.'.join(key[1:]),mapping.get(_name)
                        )
                        if tree_name is not None:
                            name = [_name]
                            name += tree_name
                    else:
                        name = [_name]
                    if name is not None:
                        ignore_list.append(name)
    return ignore_list


def get_mapping_name_item_type_by_key(key, item_type_mapping):
    """Get mapping name item type by key.

    :param item_type_mapping:
    :param key:
    :return: name
    """
    for mapping_key in item_type_mapping:
        if mapping_key == key:
            property_data = item_type_mapping.get(mapping_key)
            if isinstance(property_data.get('jpcoar_mapping'), dict):
                for name in property_data.get('jpcoar_mapping'):
                    return name
    return key


def get_mapping_name_item_type_by_sub_key(key, item_type_mapping):
    """Get mapping name item type by sub key.

    :param item_type_mapping:
    :param key:
    :return: name
    """
    tree_name = None
    for mapping_key in item_type_mapping:
        property_data = item_type_mapping.get(mapping_key)

        if isinstance(property_data, dict):
            _mapping_name = get_mapping_name_item_type_by_sub_key(
                key, property_data)
            if _mapping_name is not None:
                tree_name = [mapping_key] \
                    if mapping_key != '@attributes' else []
                tree_name += _mapping_name
                break
        elif key == property_data:
            if mapping_key!= '@value':
                tree_name = [mapping_key]
            else:
                tree_name = []
            break
    return tree_name


def del_hide_sub_item(key, mlt, hide_list):
    if isinstance(mlt, dict):
        for k, v in mlt.copy().items():
            if isinstance(v, dict) or isinstance(v, list):
                del_hide_sub_item(key, v, hide_list)
            elif isinstance(v, str):
                for h in hide_list:
                    if h.startswith(key) and h.endswith(k) and k in mlt:
                        mlt.pop(k)
            else:
                pass
    elif isinstance(mlt, list):
        for v in mlt:
            del_hide_sub_item(key, v, hide_list)
    else:
        pass

def get_hide_list_by_schema_form(item_type=None, schemaform=None):
    """Get hide list by schema form."""
    ids = []
    if item_type and not schemaform:
        schemaform = item_type.render.get('table_row_map', {}).get('form', {})
    if schemaform:
        for item in schemaform:
            if not item.get('items'):
                if item.get('isHide'):
                    ids.append(item.get('key'))
            else:
                ids += get_hide_list_by_schema_form(schemaform=item.get('items'))
    return ids


def get_hide_parent_keys(item_type=None, meta_list=None):
    """Get all hide parent keys.

    :param item_type:
    :param meta_list:
    :return: hide parent keys
    """
    if item_type and not meta_list:
        meta_list = item_type.render.get('meta_list', {})
    hide_parent_keys = []
    for key, val in meta_list.items():
        hidden = val.get('option', {}).get('hidden')
        hide_parent_keys.append(key.replace('[]', '')) if hidden else None
    return hide_parent_keys


def get_hide_parent_and_sub_keys(item_type):
    """Get all hide parent and sub keys.

    :param item_type: item type select from db.
    :return: hide parent keys, hide sub keys.
    """
    # Get parent keys of 'Hide' items.
    meta_list = item_type.render.get('meta_list', {})
    hide_parent_key = get_hide_parent_keys(item_type, meta_list)
    # Get sub keys of 'Hide' items.
    forms = item_type.render.get('table_row_map', {}).get('form', {})
    hide_sub_keys = get_hide_list_by_schema_form(item_type, forms)
    hide_sub_keys = [prop.replace('[]', '') for prop in hide_sub_keys]
    return hide_parent_key, hide_sub_keys


def get_item_from_option(_item_type_id, item_type=None):
    """Get all keys of properties that is set Hide option on metadata."""
    ignore_list = []
    meta_options = get_options_list(_item_type_id, json_item=item_type)
    for key, val in meta_options.items():
        hidden = val.get('option').get('hidden')
        if hidden:
            ignore_list.append(key)
    return ignore_list


def get_options_list(item_type_id, json_item=None):
    """Get Options by item type id.

    :param item_type_id:
    :param json_item:
    :return: options dict
    """
    meta_options = {}
    if json_item is None:
        json_item = ItemTypes.get_record(item_type_id)
    if json_item:
        meta_options = json_item.model.render.get('meta_fix')
        meta_options.update(json_item.model.render.get('meta_list'))
    return meta_options


def get_options_and_order_list(item_type_id, item_type_mapping=None,
                               item_type_data=None, mapping_flag=True):
    """Get Options by item type id.

    :param item_type_id:
    :param item_type_mapping:
    :param item_type_data:
    :return: options dict and item type mapping
    """
    from weko_records.api import Mapping
    meta_options = None
    item_type_mapping = None
    if item_type_id:
        meta_options = get_options_list(item_type_id, item_type_data)
        if item_type_mapping is None and mapping_flag:
            item_type_mapping = Mapping.get_record(item_type_id)

    if mapping_flag:
        return meta_options, item_type_mapping
    else:
        return meta_options


def hide_table_row(table_row, hide_key):
    """Get Options by item type id.

    :param hide_key:
    :param table_row:
    :return: table_row
    """
    for key in table_row:
        if key == hide_key:
            del table_row[table_row.index(hide_key)]
    return table_row


def is_schema_include_key(schema):
    """Check if schema have filename/billing_filename key."""
    properties = schema.get('properties')
    need_file = False
    need_billing_file = False
    for key in properties:
        item = properties.get(key)
        # Do check for object type
        if 'properties' in item:
            object = item.get('properties')
            if 'is_billing' in object and 'filename' in object:
                need_billing_file = True
            if 'is_billing' not in object and 'filename' in object:
                need_file = True
        # Do check for array/multiple type
        elif 'items' in item:
            object = item.get('items').get('properties')
            if 'is_billing' in object and 'filename' in object:
                need_billing_file = True
            if 'is_billing' not in object and 'filename' in object:
                need_file = True
    return need_file, need_billing_file


def isExistKeyInDict(_key, _dict):
    """Check key exist in dict and value of key is dict type.

    :param _key: key in dict.
    :param _dict: dict.
    :return: if key exist and value of this key is dict type => return True
    else False.
    """
    return isinstance(_dict, dict) and isinstance(_dict.get(_key), dict)


def set_validation_message(item, cur_lang):
    """Set validation message.

    :param item: json of control (ex: json of text input).
    :param cur_lang: current language.
    :return: item, set validationMessage attribute for item.
    """
    # current_app.logger.error("item:{}".format(item))
    i18n = 'validationMessage_i18n'
    message_attr = 'validationMessage'
    if i18n in item and cur_lang:
        item[message_attr] = item[i18n][cur_lang]


def translate_validation_message(item_property, cur_lang):
    """Recursive in order to set translate language validation message.

    :param item_property: .
    :param cur_lang: .
    :return: .
    """
    # current_app.logger.error("item_property:{}".format(item_property))
    # current_app.logger.error("cur_lang:{}".format(cur_lang))

    items_attr = 'items'
    properties_attr = 'properties'
    if isExistKeyInDict(items_attr, item_property):
        for _key1, value1 in item_property.get(items_attr).items():
            if not isinstance(value1, dict):
                continue
            for _key2, value2 in value1.items():
                set_validation_message(value2, cur_lang)
                translate_validation_message(value2, cur_lang)
    if isExistKeyInDict(properties_attr, item_property):
        for _key, value in item_property.get(properties_attr).items():
            set_validation_message(value, cur_lang)
            translate_validation_message(value, cur_lang)


def get_workflow_by_item_type_id(
    item_type_name_id, item_type_id, with_deleted=True
):
    """Get workflow settings by item type id.

    Args:
        item_type_name_id (int): Item type name id.
        item_type_id (int): Item type id.
        with_deleted (bool): Whether to include deleted workflows. Defaults to True.

    Returns:
        WorkFlow: The workflow object if found, otherwise None.

    """
    from weko_workflow.models import WorkFlow

    query = WorkFlow.query.filter_by(itemtype_id=item_type_id)
    if not with_deleted:
        query = query.filter_by(is_deleted=False)
    workflow = query.first()

    if not workflow:
        item_type_list = ItemTypes.get_by_name_id(item_type_name_id)
        id_list = [x.id for x in item_type_list]
        query = (
            WorkFlow.query
            .filter(WorkFlow.itemtype_id.in_(id_list))
            .order_by(WorkFlow.itemtype_id.desc())
            .order_by(WorkFlow.flow_id.asc())
        )
        if not with_deleted:
            query = query.filter_by(is_deleted=False)
        workflow = query.first()
    return workflow if isinstance(workflow, WorkFlow) else None


def validate_bibtex(record_ids):
    """Validate data of records for Bibtex exporting.

    @param record_ids:
    @return:
    """
    lst_invalid_ids = []
    err_msg = _('Please input all required item.')
    from weko_schema_ui.serializers import WekoBibTexSerializer
    for record_id in record_ids:
        record = WekoRecord.get_record_by_pid(record_id)
        pid = record.pid_recid
        serializer = WekoBibTexSerializer()
        result = serializer.serialize(pid, record, True)
        if not result or result == err_msg:
            lst_invalid_ids.append(record_id)
    return lst_invalid_ids


def make_bibtex_data(record_ids):
    """Serialize all Bibtex data by record ids.

    @param record_ids:
    @return:
    """
    from weko_records_ui.utils import hide_item_metadata

    result = ''
    err_msg = _('Please input all required item.')
    from weko_schema_ui.serializers import WekoBibTexSerializer
    for record_id in record_ids:
        record = WekoRecord.get_record_by_pid(record_id)
        pid = record.pid_recid

        hide_item_metadata(record)

        serializer = WekoBibTexSerializer()
        output = serializer.serialize(pid, record)
        result += output if output != err_msg else ''
    return result


def translate_schema_form(form_element, cur_lang):
    """Translate title and validation message in Schema Form.

    :param form_element: Schema Form element
    :param cur_lang: Current language
    """
    msg_i18n_key = "validationMessage_i18n"
    title_i18n_key = "title_i18n"
    if (
        form_element.get(title_i18n_key)
        and cur_lang in form_element[title_i18n_key]
        and len(form_element[title_i18n_key][cur_lang]) > 0
    ):
        form_element['title'] = form_element[title_i18n_key][cur_lang]

    des_i18n_key = "description_i18n"
    if (form_element.get(des_i18n_key)
        and cur_lang in form_element[des_i18n_key]
            and len(form_element[des_i18n_key][cur_lang]) > 0):
        form_element['description'] = form_element[des_i18n_key][cur_lang]

    if (
        form_element.get(msg_i18n_key)
        and cur_lang in form_element[msg_i18n_key]
        and len(form_element[msg_i18n_key][cur_lang]) > 0
    ):
        form_element['validationMessage'] = \
            form_element[msg_i18n_key][cur_lang]

    if form_element.get('items'):
        for sub_elem in form_element['items']:
            translate_schema_form(sub_elem, cur_lang)

class WekoQueryRankingHelper(QueryRankingHelper):
    @classmethod
    def get(cls, **kwargs):
        result = []
        try:
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            params = {
                'start_date': start_date,
                'end_date': end_date + 'T23:59:59',
                'agg_size': str(kwargs.get('agg_size', 10)),
                'event_type': kwargs.get('event_type', ''),
                'group_field': kwargs.get('group_field', ''),
                'count_field': kwargs.get('count_field', ''),
                'must_not': kwargs.get('must_not', ''),
                'new_items': False
            }
            query_config = current_app.config["WEKO_ITEMS_UI_RANKING_QUERY"][kwargs.get("ranking_type")]
            query_class = query_config["query_class"]
            cfg  =json.loads(json.dumps(query_config["query_config"]))
            cfg.update(query_name=kwargs.get("ranking_type"))
            all_query = query_class(**cfg)
            all_res = all_query.run(**params)
            cls.Calculation(all_res, result)
        except es_exceptions.NotFoundError as e:
            current_app.logger.debug(e)
        except Exception as e:
            current_app.logger.debug(e)

        return result

def get_ranking(settings):
    """Get ranking.

    :param settings: ranking setting.
    :return:
    """

    def _get_index_info(index_json, index_info):
        for index in index_json:
            index_info[index["id"]] = {
                'index_name': index["name"],
                'parent': str(index["pid"])
            }
            if index["children"]:
                _get_index_info(index["children"], index_info)

    current_app.logger.debug("get_ranking start")

    rank_buffer = current_app.config['WEKO_ITEMS_UI_RANKING_BUFFER']
    index_json = Indexes.get_browsing_tree_ignore_more()
    index_info = {}
    _get_index_info(index_json, index_info)
    has_permission_indexes = list(index_info.keys())
    # get statistical period
    end_date_original = date.today()  # - timedelta(days=1)
    start_date_original = end_date_original - timedelta(
        days=int(settings.statistical_period))
    rankings = {}
    start_date = start_date_original.strftime('%Y-%m-%d')
    end_date = end_date_original.strftime('%Y-%m-%d')
    # most_reviewed_items
    current_app.logger.debug("get most_reviewed_items start")
    if settings.rankings['most_reviewed_items']:
        result = WekoQueryRankingHelper.get(
            start_date=start_date,
            end_date=end_date,
            agg_size=settings.display_rank + rank_buffer,
            event_type='record-view',
            group_field='pid_value',
            count_field='count',
            must_not=json.dumps([{"wildcard": {"pid_value": "*.*"}}]),
            ranking_type='most_view_ranking'
        )
        rankings['most_reviewed_items'] = get_permission_record('most_reviewed_items', result, settings.display_rank, has_permission_indexes)

    # most_downloaded_items
    current_app.logger.debug("get most_downloaded_items start")
    if settings.rankings['most_downloaded_items']:
        result = QueryRankingHelper.get(
            start_date=start_date,
            end_date=end_date,
            agg_size=settings.display_rank + rank_buffer,
            event_type='file-download',
            group_field='item_id',
            count_field='count',
            must_not=json.dumps([{"wildcard": {"item_id": "*.*"}}])
        )

        current_app.logger.debug("finished getting most_downloaded_items data from ES")
        rankings['most_downloaded_items'] = get_permission_record('most_downloaded_items', result, settings.display_rank, has_permission_indexes)

    # created_most_items_user
    current_app.logger.debug("get created_most_items_user start")
    if settings.rankings['created_most_items_user']:
        result = QueryRankingHelper.get(
            start_date=start_date,
            end_date=end_date,
            agg_size=settings.display_rank,
            event_type='item-create',
            group_field='cur_user_id',
            count_field='count',
            must_not=json.dumps([{"wildcard": {"pid_value": "*.*"}}])
        )

        current_app.logger.debug("finished getting created_most_items_user data from ES")
        ranking_data = []
        for s in result:
            ranking_data.append(parse_ranking_results(
                'created_most_items_user',
                s['key'],
                count=s['count'],
                rank=len(ranking_data) + 1
            ))
        rankings['created_most_items_user'] = ranking_data

    # most_searched_keywords
    current_app.logger.debug("get most_searched_keywords start")
    if settings.rankings['most_searched_keywords']:
        filter_list = current_app.config['WEKO_ITEMS_UI_SEARCH_RANK_KEY_FILTER']
        must_not = [{"wildcard": {"search_type": "2*"}}]
        for f in filter_list:
            must_not.append({"match": {"search_key": f}})
        result = QueryRankingHelper.get(
            start_date=start_date,
            end_date=end_date,
            agg_size=settings.display_rank,
            event_type='search',
            group_field='search_key',
            count_field='count',
            must_not=json.dumps(must_not)
        )

        current_app.logger.debug("finished getting most_searched_keywords data from ES")
        ranking_data = []
        for s in result:
            ranking_data.append(parse_ranking_results(
                'most_searched_keywords',
                s['key'],
                count=s['count'],
                rank=len(ranking_data) + 1
            ))
        rankings['most_searched_keywords'] = ranking_data

    # new_items
    current_app.logger.debug("get new_items start")
    if settings.rankings['new_items']:
        new_item_start_date = (
            end_date_original
            - timedelta(
                days=int(settings.new_item_period) - 1
            )
        )
        if new_item_start_date < start_date_original:
            new_item_start_date = start_date_original
        result = QueryRankingHelper.get_new_items(
            start_date=new_item_start_date.strftime('%Y-%m-%d'),
            end_date=end_date,
            agg_size=settings.display_rank + rank_buffer,
            must_not=json.dumps([{"wildcard": {"control_number": "*.*"}}])
        )

        current_app.logger.debug("finished getting new_items data from ES")
        rankings['new_items'] = get_permission_record('new_items', result, settings.display_rank, has_permission_indexes)

    return rankings


def __sanitize_string(s: str):
    """Sanitize control characters without '\x09', '\x0a', '\x0d' and '0x7f'.

    Args:
        s (str): target string

    Returns:
        str: sanitized string
    """
    s = s.strip()
    sanitize_str = ""
    for i in s:
        if ord(i) in [9, 10, 13] or (31 < ord(i) != 127):
            sanitize_str += i
    return sanitize_str


def sanitize_input_data(data):
    """Sanitize control characters without '\x09', '\x0a', '\x0d' and '0x7f'.

    Args:
        data (dict or list): target dict or list
    """
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, str):
                data[k] = __sanitize_string(v)
            else:
                sanitize_input_data(v)
    elif isinstance(data, list):
        for i in range(len(data)):
            if isinstance(data[i], str):
                data[i] = __sanitize_string(data[i])
            else:
                sanitize_input_data(data[i])

def check_duplicate(data, is_item=True, exclude_ids=[]):
    """
    Check if a record or item is duplicate in records_metadata.

    Args:
        data (dict or str): Metadata dictionary (or JSON string).
        is_item (bool): True if checking an item, False if checking a record.

    Returns:
        tuple:
            - bool: True if duplicate exists, False otherwise.
            - list: List of duplicate record IDs.
            - list: List of duplicate record URLs.
    """
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError as e:
            current_app.logger.error(f"JSON decode failed: {e}")
            return False, [], []

    if not isinstance(data, dict):
        current_app.logger.error("The provided data is not a dictionary.")
        return False, [], []

    metadata = data if is_item else data.get("metainfo", {})
    if not isinstance(metadata, dict):
        current_app.logger.error("Metadata format is invalid.")
        return False, [], []

    identifier = title = resource_type = creator = ""
    author_links = metadata.get("author_link", [])
    host = request.host

    # Extract other fields
    for key, value in metadata.items():
        if isinstance(value, dict) and "resourcetype" in value:
            resource_type = value["resourcetype"]
        if isinstance(value, list):
            for v in value:
                if isinstance(v, dict):
                    if "subitem_identifier_uri" in v:
                        identifier = v["subitem_identifier_uri"]
                    if "subitem_title" in v:
                        title = v["subitem_title"]
                    if "creatorNames" in v:
                        creator_info = v["creatorNames"][0] if v["creatorNames"] else {}
                        creator = creator_info.get("creatorName", "")


    # 1. Check identifier
    if identifier:
        query = text(f"""
            SELECT COALESCE(CAST(SPLIT_PART(jsonb_extract_path_text(json, 'recid'), '.', 1) AS INTEGER), 0)
            FROM records_metadata
            WHERE jsonb_path_exists(json, '$.**.subitem_identifier_uri ? (@ == "{identifier}")')
        """)
        result = db.session.execute(query).fetchall()
        if result:
            recid_list = [r[0] for r in result]
            return True, recid_list, [f"https://{host}/records/{r}" for r in recid_list]

    # 2. Normalize title
    normalized_title = unicodedata.normalize("NFKC", title).lower()
    normalized_title = re.sub(r'[\s,　]', '', normalized_title)

    query = text("""
        SELECT COALESCE(CAST(SPLIT_PART(jsonb_extract_path_text(json, 'recid'), '.', 1) AS INTEGER), 0), json
        FROM records_metadata
        WHERE jsonb_path_exists(json, '$.**.subitem_title')
    """)
    result = db.session.execute(query).fetchall()

    matched_recids = set()
    for recid, json_obj in result:
        json_str = json.dumps(json_obj, ensure_ascii=False)
        titles = re.findall(r'"subitem_title"\s*:\s*"([^"]+)"', json_str)
        for t in titles:
            cleaned = unicodedata.normalize("NFKC", t).lower()
            cleaned = re.sub(r'[\s,　]', '', cleaned)
            if cleaned == normalized_title:
                matched_recids.add(recid)
                break

    matched_recids -= set(exclude_ids)

    if not matched_recids:
        return False, [], []

    # 3. Match resource_type
    query = text(f"""
        SELECT COALESCE(CAST(SPLIT_PART(jsonb_extract_path_text(json, 'recid'), '.', 1) AS INTEGER), 0)
        FROM records_metadata
        WHERE jsonb_path_exists(json, '$.**.resourcetype ? (@ == "{resource_type}")')
    """)
    result = db.session.execute(query).fetchall()
    recids_resource = {r[0] for r in result}
    matched_recids &= recids_resource
    matched_recids -= set(exclude_ids)

    if not matched_recids:
        return False, [], []

    # 4. Author check (via author_link or creator)
    final_matched = set()
    if author_links:
        # Get fullName(s) from authors table via author_link
        placeholders = ','.join([f':aid{i}' for i in range(len(author_links))])
        params = {f'aid{i}': aid for i, aid in enumerate(author_links)}
        query = text(f"""
            SELECT json FROM authors
            WHERE jsonb_path_exists(json, '$.authorIdInfo[*].authorId')
            AND jsonb_extract_path_text(json, 'authorIdInfo', '0', 'authorId') IN ({placeholders})
        """)
        result = db.session.execute(query, params).fetchall()

        author_names = set()
        for row in result:
            json_obj = row[0]
            name_info = json_obj.get("authorNameInfo", [])
            for n in name_info:
                full = n.get("fullName")
                if full:
                    cleaned = re.sub(r'[\s,　]', '', full)
                    author_names.add(cleaned)

        if author_names:
            query = text("""
                SELECT COALESCE(CAST(SPLIT_PART(jsonb_extract_path_text(json, 'recid'), '.', 1) AS INTEGER), 0), json
                FROM records_metadata
                WHERE jsonb_path_exists(json, '$.**.creatorNames[*].creatorName')
            """)
            result = db.session.execute(query).fetchall()
            for recid, json_obj in result:
                json_str = json.dumps(json_obj, ensure_ascii=False)
                creators = re.findall(r'"creatorName"\s*:\s*"([^"]+)"', json_str)
                for name in creators:
                    cleaned = re.sub(r'[\s,　]', '', name)
                    if cleaned in author_names:
                        final_matched.add(recid)
                        break
    else:
        normalized_creator = re.sub(r'[\s,　]', '', creator)
        query = text("""
            SELECT COALESCE(CAST(SPLIT_PART(jsonb_extract_path_text(json, 'recid'), '.', 1) AS INTEGER), 0), json
            FROM records_metadata
            WHERE jsonb_path_exists(json, '$.**.creatorNames[*].creatorName')
        """)
        result = db.session.execute(query).fetchall()
        for recid, json_obj in result:
            json_str = json.dumps(json_obj, ensure_ascii=False)
            creators = re.findall(r'"creatorName"\s*:\s*"([^"]+)"', json_str)
            for name in creators:
                cleaned = re.sub(r'[\s,　]', '', name)
                if cleaned == normalized_creator:
                    final_matched.add(recid)
                    break

    final_matched &= matched_recids
    if final_matched:
        links = [f"https://{host}/records/{r}" for r in final_matched]
        return True, list(final_matched), links

    current_app.logger.info("No duplicates found.")
    return False, [], []



def is_duplicate_item(metadata, exclude_ids=[]):
    """Check if an item is duplicate in records_metadata.

    Args:
        metadata (dict): Metadata dictionary.
        exclude_ids (list, Optional): List of record IDs to exclude from the check.

    Returns:
        tuple:
            - bool: True if duplicate exists, False otherwise.
            - list: List of duplicate record IDs.
            - list: List of duplicate record URLs.
    """
    return check_duplicate(metadata, is_item=True, exclude_ids=exclude_ids)


def is_duplicate_record(data, exclude_ids=[]):
    """Check if a record is duplicate in records_metadata.

    Args:
        data (dict): Metadata dictionary.
        exclude_ids (list, Optional): List of record IDs to exclude from the check.

    Returns:
        tuple:
            - bool: True if duplicate exists, False otherwise.
            - list: List of duplicate record IDs.
            - list: List of duplicate record URLs.
    """
    return check_duplicate(data, is_item=False, exclude_ids=exclude_ids)


def save_title(activity_id, request_data):
    """Save title.

    :param activity_id: activity id.
    :param request_data: request data.
    :return:
    """
    activity = WorkActivity()
    db_activity = activity.get_activity_detail(activity_id)
    item_type_id = db_activity.workflow.itemtype.id
    if item_type_id:
        item_type_mapping = Mapping.get_record(item_type_id)
        # current_app.logger.debug("item_type_mapping:{}".format(item_type_mapping))
        key, key_child = get_key_title_in_item_type_mapping(item_type_mapping)
    if key and key_child:
        title = get_title_in_request(request_data, key, key_child)
        activity.update_title(activity_id, title)


def get_key_title_in_item_type_mapping(item_type_mapping):
    """Get key title in item type mapping.

    :param item_type_mapping: item type mapping.
    :return:
    """
    for mapping_key in item_type_mapping:
        property_data = item_type_mapping.get(
            mapping_key).get('jpcoar_mapping')
        if isinstance(property_data,
                      dict) and 'title' in property_data and property_data.get(
                'title').get('@value'):
            return mapping_key, property_data.get('title').get('@value')
    return None, None


def get_title_in_request(request_data, key, key_child):
    """Get title in request.

    :param request_data: activity id.
    :param key: key of title.
    :param key_child: key child of title.
    :return:
    """
    result = ''
    try:
        title = request_data.get('metainfo')
        if title and key in title:
            title_value = title.get(key)
            if isinstance(title_value, dict) and key_child in title_value:
                result = title_value.get(key_child)
            elif isinstance(title_value, list) and len(title_value) > 0:
                title_value = title_value[0]
                if key_child in title_value:
                    result = title_value.get(key_child)
    except Exception:
        pass
    return result


def hide_form_items(item_type, schema_form):
    """
    Hide form items.

    :param item_type: Item type data
    :param schema_form: Schema form data.
    """
    system_properties = [
        'subitem_systemidt_identifier',
        'subitem_systemfile_datetime',
        'subitem_systemfile_filename',
        'subitem_system_id_rg_doi',
        'subitem_system_date_type',
        'subitem_system_date',
        'subitem_system_identifier_type',
        'subitem_system_identifier',
        'subitem_system_text'
    ]
    for i in system_properties:
        hidden_items = [
            schema_form.index(form) for form in schema_form
            if form.get('items') and form[
                'items'][0]['key'].split('.')[1] == i]
        if hidden_items and i in json.dumps(schema_form):
            schema_form = update_schema_remove_hidden_item(
                schema_form,
                item_type.render,
                hidden_items
            )
    hide_thumbnail(schema_form)
    return schema_form


def hide_thumbnail(schema_form):
    """Hide thumbnail item.

    :param schema_form:
    :return:
    """
    def is_thumbnail(items):
        for item in items:
            if isinstance(item, dict) and 'subitem_thumbnail' in item.get(
                    'key', ''):
                return True
        return False

    for form_data in schema_form:
        data_items = form_data.get('items')
        if isinstance(data_items, list) and is_thumbnail(data_items):
            form_data['condition'] = 1
            break


def get_ignore_item(_item_type_id, item_type_data=None):
    """Get ignore item from mapping.

    :param _item_type_id:
    :param item_type_data:
    :return ignore_list:
    """
    ignore_list = []
    sub_ids = []
    meta_options = get_options_and_order_list(
        _item_type_id, item_type_data=item_type_data, mapping_flag=False)
    schema_form = None
    if item_type_data is not None:
        schema_form = item_type_data.model.render.get("table_row_map", {}).get(
            'form')
        sub_ids = get_hide_list_by_schema_form(schemaform=schema_form)
    for key, val in meta_options.items():
        hidden = val.get('option').get('hidden')
        if hidden:
            ignore_list.append(key)
    for sub_id in sub_ids:
        key = [_id.replace('[]', '') for _id in sub_id.split('.')]
        ignore_list.append(key)
    return ignore_list


def make_stats_file_with_permission(item_type_id, recids,
                                   records_metadata, permissions,export_path=""):
    """Prepare TSV/CSV data for each Item Types.

    Args:
        item_type_id (_type_): ItemType ID
        recids (_type_): List records ID
        records_metadata (_type_): _description_
        permissions (_type_): _description_
        export_path (str): path of temp_dir

    Returns:
        _type_: _description_
    """
    """

    Arguments:
        item_type_id    --
        recids          --
    Returns:
        ret             -- Key properties
        ret_label       -- Label properties
        records.attr_output -- Record data

    """
    # current_app.logger.error("item_type_id:{}".format(item_type_id))
    # current_app.logger.error("recids:{}".format(recids))
    # current_app.logger.error("records_metadata:{}".format(records_metadata))
    # current_app.logger.error("records_metadata:{}".format(type(records_metadata)))
    # current_app.logger.error("permissions:{}".format(permissions))
    from weko_records_ui.utils import check_items_settings, hide_by_email
    from weko_records_ui.views import escape_newline, escape_str

    def _get_root_item_option(item_id, item, sub_form={'title_i18n': {}}):
        """Handle if is root item."""
        _id = '.metadata.{}'.format(item_id)
        _name = sub_form.get('title_i18n', {}).get(
            permissions['current_language']()) or item.get('title')

        _option = []
        if item.get('option').get('required'):
            _option.append('Required')
        if item.get('option').get('hidden'):
            _option.append('Hide')
        if item.get('option').get('multiple'):
            _option.append('Allow Multiple')
            _id += '[0]'
            _name += '[0]'

        return _id, _name, _option

    item_type = ItemTypes.get_by_id(item_type_id).render
    table_row_properties = item_type['table_row_map']['schema'].get(
        'properties')

    class RecordsManager:
        """Management data for exporting records."""

        first_recid = 0
        cur_recid = 0
        recids = []
        records = {}
        attr_data = {}
        attr_output = {}

        def __init__(self, record_ids, records_metadata):
            """Class initialization."""
            def hide_metadata_email(record):
                """Hiding emails only.

                :param name_keys:
                :param lang_keys:
                :param datas:
                :return:
                """
                check_items_settings()

                record['weko_creator_id'] = record.get('owner')

                if permissions['hide_meta_data_for_role'](record) and \
                        not current_app.config['EMAIL_DISPLAY_FLG']:
                    record = hide_by_email(record, True)

                    return True

                record.pop('weko_creator_id')
                return False

            self.recids = record_ids
            self.first_recid = record_ids[0]
            for record_id in record_ids:
                record = records_metadata.get(record_id)

                # Custom Record Metadata for export
                hide_metadata_email(record)
                _custom_export_metadata(record, False, True)

                self.records[record_id] = record
                self.attr_output[record_id] = []

        def get_max_ins(self, attr):
            """Get max data each main property in all exporting records."""
            largest_size = 1
            self.attr_data[attr] = {'max_size': 0}
            for record in self.records:
                if isinstance(self.records[record].get(attr), dict) \
                    and self.records[record].get(attr).get(
                        'attribute_value_mlt'):
                    self.attr_data[attr][record] = self.records[record][attr][
                        'attribute_value_mlt']
                else:
                    if self.records[record].get(attr):
                        self.attr_data[attr][record] = \
                            self.records[record].get(attr)
                    else:
                        self.attr_data[attr][record] = []
                rec_size = len(self.attr_data[attr][record])
                if rec_size > largest_size:
                    largest_size = rec_size
            self.attr_data[attr]['max_size'] = largest_size

            return self.attr_data[attr]['max_size']

        def get_max_ins_feedback_mail(self):
            """Get max data each feedback mail in all exporting records."""
            largest_size = 1
            self.attr_data['feedback_mail_list'] = {'max_size': 0}
            for record_id, record in self.records.items():
                if permissions['check_created_id'](record):
                    mail_list = FeedbackMailList.get_mail_list_by_item_id(
                        record.id)
                    self.attr_data['feedback_mail_list'][record_id] = [
                        mail.get('email') for mail in mail_list]
                    if len(mail_list) > largest_size:
                        largest_size = len(mail_list)
            self.attr_data['feedback_mail_list']['max_size'] = largest_size

            return self.attr_data['feedback_mail_list']['max_size']

        def get_max_ins_request_mail(self):
            """Get max data each request mail in all exporting records."""
            largest_size = 1
            self.attr_data['request_mail_list'] = {'max_size': 0}
            for record_id, record in self.records.items():
                if permissions['check_created_id'](record):
                    mail_list = RequestMailList.get_mail_list_by_item_id(
                        record.id)
                    self.attr_data['request_mail_list'][record_id] = [
                        mail.get('email') for mail in mail_list]
                    if len(mail_list) > largest_size:
                        largest_size = len(mail_list)
            self.attr_data['request_mail_list']['max_size'] = largest_size

            return self.attr_data['request_mail_list']['max_size']

        def get_max_items(self, item_attrs):
            """Get max data each sub property in all exporting records."""
            max_length = 0
            list_attr = []
            for attr in item_attrs.split('.'):
                index_left_racket = attr.find('[')
                if index_left_racket >= 0:
                    list_attr.extend(
                        [attr[:index_left_racket],
                         attr[index_left_racket:]]
                    )
                else:
                    list_attr.append(attr)

            level = len(list_attr)
            if level == 1:
                return self.attr_data[item_attrs]['max_size']
            elif level > 1:
                max_length = 1
                for record in self.records:
                    _data = self.records[record].get(list_attr[0])
                    if _data:
                        _data = _data['attribute_value_mlt']
                        for attr in list_attr[1:]:
                            if re.search(r'^\[\d+\]$', attr):
                                idx = int(attr[1:-1])
                                if isinstance(_data, list) \
                                        and len(_data) > idx:
                                    _data = _data[idx]
                                else:
                                    _data = []
                                    break
                            elif isinstance(_data, list):
                                _data = _data[0]
                                if isinstance(_data, dict) and _data.get(attr):
                                    _data = _data.get(attr)
                            elif isinstance(_data, dict) and _data.get(attr):
                                _data = _data.get(attr)
                            else:
                                _data = []
                                break
                        if isinstance(_data, list) and len(_data) > max_length:
                            max_length = len(_data)
            return max_length

        def get_subs_item(self,
                          item_key,
                          item_label,
                          properties,
                          data=None,
                          is_object=False):
            """Building key, label and data from key properties.

            Arguments:
                item_key    -- Key properties
                item_label  -- Label properties
                properties  -- Data properties
                data        -- Record data
                is_object   -- Is objecting property?
            Returns:
                o_ret       -- Key properties
                o_ret_label -- Label properties
                ret_data    -- Record data

            """
            o_ret = []
            o_ret_label = []
            ret_data = []
            max_items = self.get_max_items(item_key)
            max_items = 1 if is_object else max_items
            for idx in range(max_items):
                key_list = []
                key_label = []
                key_data = []
                for key in sorted(properties):
                    if not is_object:
                        new_key = '{}[{}].{}'.format(
                            item_key, str(idx), key)
                        new_label = '{}[{}].{}'.format(
                            item_label, str(idx), properties[key].get('title'))
                    else:
                        new_key = '{}.{}'.format(item_key, key)
                        new_label = '{}.{}'.format(
                            item_label, properties[key].get('title'))

                    if properties[key].get('format', '') == 'checkboxes':
                        new_key += '[{}]'
                        new_label += '[{}]'
                        if isinstance(data, dict):
                            data = [data]
                        if data and data[idx].get(key):
                            for idx_c in range(len(data[idx][key])):
                                key_list.append(new_key.format(idx_c))
                                key_label.append(new_label.format(idx_c))
                                key_data.append(data[idx][key][idx_c])
                        else:
                            key_list.append(new_key.format('0'))
                            key_label.append(new_label.format('0'))
                            key_data.append('')
                    elif properties[key]['type'] in ['array', 'object']:
                        if data and idx < len(data) and data[idx].get(key):
                            m_data = data[idx][key]
                        else:
                            m_data = None

                        if properties[key]['type'] == 'object':
                            new_properties = properties[key]['properties']
                            new_is_object = True
                        else:
                            new_properties = \
                                properties[key]['items']['properties']
                            new_is_object = False

                        sub, sublabel, subdata = self.get_subs_item(
                            new_key, new_label, new_properties,
                            m_data, new_is_object)
                        key_list.extend(sub)
                        key_label.extend(sublabel)
                        key_data.extend(subdata)
                    else:
                        if 'iscreator' in new_key:
                            continue
                        if isinstance(data, dict):
                            data = [data]
                        key_list.append(new_key)
                        key_label.append(new_label)
                        if data and idx < len(data) and data[idx].get(key):
                            key_data.append(escape_newline(data[idx][key]))
                            # key_data.append(escape_str(data[idx][key]))
                        else:
                            key_data.append('')

                key_list_len = len(key_list)
                for key_index in range(key_list_len):
                    item_key_split = item_key.split('.')
                    if 'filename' in key_list[key_index]:
                        key_list.insert(0, '.file_path[{}]'.format(
                            str(idx)))
                        key_label.insert(0, '.ファイルパス[{}]'.format(
                            str(idx)))
                        output_path = ""
                        if key_data[key_index]:
                            file_path = "recid_{}/{}".format(str(self.cur_recid), key_data[key_index])
                            output_path = file_path if os.path.exists(os.path.join(export_path,file_path)) else ""
                        key_data.insert(0,output_path)
                        break
                    elif 'thumbnail_label' in key_list[key_index] \
                            and len(item_key_split) == 2:
                        if '[' in item_key_split[0]:
                            key_list.insert(0, '.thumbnail_path[{}]'.format(
                                str(idx)))
                            key_label.insert(0, '.サムネイルパス[{}]'.format(
                                str(idx)))
                        else:
                            key_list.insert(0, '.thumbnail_path')
                            key_label.insert(0, '.サムネイルパス')
                        if key_data[key_index]:
                            key_data.insert(0, 'recid_{}/{}'.format(str(
                                self.cur_recid), key_data[key_index]))
                        else:
                            key_data.insert(0, '')
                        break

                o_ret.extend(key_list)
                o_ret_label.extend(key_label)
                ret_data.extend(key_data)

            return o_ret, o_ret_label, ret_data

    records = RecordsManager(recids, records_metadata)

    ret = ['#.id', '.uri']
    ret_label = ['#ID', 'URI']

    max_path = records.get_max_ins('path')
    for i in range(max_path):
        ret.append('.metadata.path[{}]'.format(i))
        ret.append('.pos_index[{}]'.format(i))
        ret_label.append('.IndexID[{}]'.format(i))
        ret_label.append('.POS_INDEX[{}]'.format(i))

    ret.append('.publish_status')
    ret_label.append('.PUBLISH_STATUS')

    max_feedback_mail = records.get_max_ins_feedback_mail()
    for i in range(max_feedback_mail):
        ret.append('.feedback_mail[{}]'.format(i))
        ret_label.append('.FEEDBACK_MAIL[{}]'.format(i))

    max_request_mail = records.get_max_ins_request_mail()
    for i in range(max_request_mail):
        ret.append('.request_mail[{}]'.format(i))
        ret_label.append('.REQUEST_MAIL[{}]'.format(i))

    ret.extend(['.cnri', '.doi_ra', '.doi', '.edit_mode'])
    ret_label.extend(['.CNRI', '.DOI_RA', '.DOI', 'Keep/Upgrade Version'])
    ret.append('.metadata.pubdate')
    ret_label.append('公開日' if
                     permissions['current_language']() == 'ja' else 'PubDate')

    for recid in recids:
        record = records.records[recid]
        paths = records.attr_data['path'][recid]
        index_infos = Indexes.get_path_list(paths)
        for info in index_infos:
            records.attr_output[recid].append(info.cid)
            records.attr_output[recid].append(info.name_en.replace(
                '-/-', current_app.config['WEKO_ITEMS_UI_INDEX_PATH_SPLIT']))
        records.attr_output[recid].extend(
            [''] * (max_path * 2 - len(records.attr_output[recid]))
        )

        records.attr_output[recid].append(
            'public' if record['publish_status'] == PublishStatus.PUBLIC.value else 'private')
        feedback_mail_list = records.attr_data['feedback_mail_list'] \
            .get(recid, [])
        records.attr_output[recid].extend(feedback_mail_list)
        records.attr_output[recid].extend(
            [''] * (max_feedback_mail - len(feedback_mail_list))
        )

        request_mail_list = records.attr_data['request_mail_list'] \
            .get(recid, [])
        records.attr_output[recid].extend(request_mail_list)
        records.attr_output[recid].extend(
            [''] * (max_request_mail - len(request_mail_list))
        )

        pid_cnri = record.pid_cnri
        cnri = ''
        if pid_cnri:
            cnri = pid_cnri.pid_value.replace(WEKO_SERVER_CNRI_HOST_LINK, '')
        records.attr_output[recid].append(cnri)

        identifier = IdentifierHandle(record.pid_recid.object_uuid)
        doi_value, doi_type = identifier.get_idt_registration_data()
        doi_type_str = doi_type[0] if doi_type and doi_type[0] else ''
        doi_str = doi_value[0] if doi_value and doi_value[0] else ''
        if doi_type_str and doi_str:
            doi_domain = ''
            if doi_type_str == WEKO_IMPORT_DOI_TYPE[0]:
                doi_domain = IDENTIFIER_GRANT_LIST[1][2]
            elif doi_type_str == WEKO_IMPORT_DOI_TYPE[1]:
                doi_domain = IDENTIFIER_GRANT_LIST[2][2]
            elif doi_type_str == WEKO_IMPORT_DOI_TYPE[2]:
                doi_domain = IDENTIFIER_GRANT_LIST[3][2]
            elif doi_type_str == WEKO_IMPORT_DOI_TYPE[3]:
                doi_domain = IDENTIFIER_GRANT_LIST[4][2]
            if doi_domain and doi_str.startswith(doi_domain):
                doi_str = doi_str.replace(doi_domain + '/', '', 1)
        records.attr_output[recid].extend([
            doi_type_str,
            doi_str
        ])

        # .edit Keep or Upgrade. default is Keep
        records.attr_output[recid].append('Keep')

        records.attr_output[recid].append(record[
            'pubdate']['attribute_value'])

    for item_key in item_type.get('table_row'):
        item = table_row_properties.get(item_key)
        records.get_max_ins(item_key)
        keys = []
        labels = []
        for recid in recids:
            records.cur_recid = recid
            # print("item.get(type):{}".format(item.get('type')))
            # print("item_key:{}".format(item_key))
            # print("records.attr_data[item_key]: {}".format(records.attr_data[item_key]))
            if item.get('type') == 'array':
                key, label, data = records.get_subs_item(
                    item_key,
                    item.get('title'),
                    item['items']['properties'],
                    records.attr_data[item_key][recid]
                )
                if not keys:
                    keys = key
                if not labels:
                    labels = label
                records.attr_output[recid].extend(data)
            elif item.get('type') == 'object':
                key, label, data = records.get_subs_item(
                    item_key,
                    item.get('title'),
                    item['properties'],
                    records.attr_data[item_key][recid],
                    True
                )
                if not keys:
                    keys = key
                if not labels:
                    labels = label
                records.attr_output[recid].extend(data)
            else:
                if not keys:
                    keys = [item_key]
                if not labels:
                    labels = [item.get('title')]
                data = records.attr_data[item_key].get(recid) or {}
                attr_val = data.get("attribute_value", "")
                if isinstance(attr_val,str):
                    records.attr_output[recid].append(attr_val)
                else:
                    records.attr_output[recid].extend(attr_val)

        new_keys = []
        for key in keys:
            if 'file_path' not in key and 'thumbnail_path' not in key:
                key = '.metadata.{}'.format(key)
            new_keys.append(key)
        ret.extend(new_keys)
        ret_label.extend(labels)

    ret_system = []
    ret_option = []
    multiple_option = ['.metadata.path', '.pos_index',
                       '.feedback_mail', '.request_mail', '.file_path', '.thumbnail_path']
    meta_list = item_type.get('meta_list', {})
    meta_list.update(item_type.get('meta_fix', {}))
    form = item_type.get('table_row_map', {}).get('form', {})
    del_num = 0
    total_col = len(ret)
    for index in range(total_col):
        _id = ret[index - del_num]
        key = re.sub(r'\[\d+\]', '[]', _id.replace('.metadata.', ''))
        root_key = key.split('.')[0].replace('[]', '')
        if root_key in meta_list:
            is_system = check_sub_item_is_system(key, form)
            ret_system.append('System' if is_system else '')

            _, _, root_option = _get_root_item_option(
                root_key,
                meta_list.get(root_key)
            )
            sub_options = get_sub_item_option(key, form)
            if not sub_options:
                ret_option.append(', '.join(root_option))
            else:
                ret_option.append(
                    ', '.join(list(set(root_option + sub_options)))
                )
        elif key == '#.id':
            ret_system.append('#')
            ret_option.append('#')
        elif key == '.edit_mode' or key == '.publish_status':
            ret_system.append('')
            ret_option.append('Required')
        elif '[' in _id and _id.split('[')[0] in multiple_option:
            ret_system.append('')
            ret_option.append('Allow Multiple')
        else:
            ret_system.append('')
            ret_option.append('')

    return [ret, ret_label, ret_system, ret_option], records.attr_output


def check_item_is_being_edit(
        recid: PersistentIdentifier,
        post_workflow=None,
        activity=None):
    """Check an item is being edit.

    Args:
        recid (PersistentIdentifier): _description_
        post_workflow (Activity, optional): _description_. Defaults to None.
        activity (activity:<weko_workflow.api.WorkActivity, optional): _description_. Defaults to None.

    Returns:
        bool: True: editing, False: available
    """
    # current_app.logger.error("recid:{}".format(recid))
    # current_app.logger.error("post_workflow:{}".format(post_workflow))
    # current_app.logger.error("activity:{}".format(activity))
    if not isinstance(activity, WorkActivity):
        activity = WorkActivity()
    if not isinstance(post_workflow, Activity):
        latest_pid = PIDVersioning(child=recid).last_child
        item_uuid = latest_pid.object_uuid
        post_workflow = activity.get_workflow_activity_by_item_id(item_uuid)
    if (
        post_workflow and post_workflow.action_status
            in [ASP.ACTION_BEGIN, ASP.ACTION_DOING]
    ):
        current_app.logger.debug("post_workflow: {0} status: {1}".format(
            post_workflow, post_workflow.action_status))
        return str(post_workflow.activity_id)

    draft_pid = PersistentIdentifier.query.filter_by(
        pid_type='recid',
        pid_value="{}.0".format(recid.pid_value)
    ).one_or_none()
    if isinstance(draft_pid, PersistentIdentifier):
        draft_workflow = activity.get_workflow_activity_by_item_id(
            draft_pid.object_uuid
        )
        if (
            draft_workflow
            and draft_workflow.action_status in [ASP.ACTION_BEGIN, ASP.ACTION_DOING]
        ):
            current_app.logger.debug("draft_workflow: {0} status: {1}".format(
                draft_pid.object_uuid, draft_workflow.action_status)
            )
            return str(draft_workflow.activity_id)

        pv = PIDVersioning(child=recid)
        latest_pid = PIDVersioning(parent=pv.parent,child=recid).get_children(
            pid_status=PIDStatus.REGISTERED
        ).filter(PIDRelation.relation_type == 2).order_by(
            PIDRelation.index.desc()
        ).first()
        latest_workflow = activity.get_workflow_activity_by_item_id(
            latest_pid.object_uuid
        )
        if (
            latest_workflow
            and latest_workflow.action_status in [ASP.ACTION_BEGIN, ASP.ACTION_DOING]
        ):
            current_app.logger.debug("latest_workflow: {0} status: {1}".format(
                latest_pid.object_uuid, latest_workflow.action_status))
            return str(latest_workflow.activity_id)

    pv = PIDVersioning(child=recid)
    versions_uuid = [
        record.object_uuid
        for record in PIDVersioning(parent=pv.parent, child=recid)
        .get_children(pid_status=PIDStatus.REGISTERED)
        .filter(PIDRelation.relation_type == 2)
        .order_by(PIDRelation.index.desc())
        .all()
    ]
    last_activity = (
        Activity.query
        .filter(Activity.item_id.in_(versions_uuid))
        .filter(Activity.action_status.in_([ASP.ACTION_BEGIN, ASP.ACTION_DOING]))
        .order_by(Activity.updated.desc())
        .first()
    )
    if isinstance(last_activity, Activity):
        current_app.logger.debug("last_activity: {0} status: {1}".format(
            last_activity.item_id, last_activity.action_status))
        return str(last_activity.activity_id)

    return ""


def check_item_is_deleted(recid):
    """Check an item is deleted.

    Args:
        recid (str): recid or object_uuid of recid

    Returns:
        bool: True: deleted, False: available
    """
    pid = PersistentIdentifier.query.filter_by(
        pid_type='recid', pid_value=recid).first()
    if not pid:
        pid = PersistentIdentifier.query.filter_by(
            pid_type='recid', object_uuid=recid).first()
    return pid and pid.status == PIDStatus.DELETED


def permission_ranking(result, pid_value_permissions, display_rank, list_name,
                       pid_value):
    """Permission ranking.

    Args:
        result (_type_): _description_
        pid_value_permissions (_type_): _description_
        display_rank (_type_): _description_
        list_name (_type_): _description_
        pid_value (_type_): _description_
    """
    list_result = list()
    for data in result.get(list_name, []):
        if data.get(pid_value, '') in pid_value_permissions:
            list_result.append(data)
        if len(list_result) == display_rank:
            break
    result[list_name] = list_result


def has_permission_edit_item(record, recid):
    """Check current user has permission to edit item.

    @param record: record metadata.
    @param recid: pid_value of pidstore_pid.
    @return: True/False
    """
    permission = check_created_id(record)
    pid = PersistentIdentifier.query.filter_by(
        pid_type='recid',
        pid_value=recid
    ).first()
    can_edit = True if pid == get_record_without_version(pid) else False
    return can_edit and permission

def lock_item_will_be_edit(pid_value):
    """Lock item will be edit.

    Lock the item to prevent double-click operation.
    The lock will be released after 3 seconds.

    Args:
        pid_value (str): recid of item.

    Returns:
        bool: If lock is successful, return True.
    """
    redis_connection = RedisConnection()
    sessionstorage = redis_connection.connection(
        db=current_app.config['ACCOUNTS_SESSION_REDIS_DB_NO'], kv = True
    )
    if sessionstorage.redis.exists("pid_{}_will_be_edit".format(pid_value)):
        return False

    sessionstorage.put(
        "pid_{}_will_be_edit".format(pid_value),
        str(current_user.get_id()).encode('utf-8'),
        ttl_secs=3
    )
    return True

def get_file_download_data(item_id, record, filenames, query_date=None, size=None):
    """Get file download data.

    Args:
        item_id (int): Item id
        record (WekoRecord): Record
        filenames (list[str]): Filenames
        query_date (str): Period(yyyy-MM)
        size (str): Ranking display number

    Returns:
        dict: Ranking result dict
    """
    result = {}

    # Check available
    available_filenames = []
    target_files = [f for f in record.files if f.info().get('filename') in filenames]

    for file in target_files:
        if check_file_download_permission(record, file.info()):
            available_filenames.append(file.info().get('filename'))
    if not available_filenames:
        raise AvailableFilesNotFoundRESTError()

    result['ranking'] = [{'filename': f, 'download_total': 0} for f in available_filenames]

    # Get root file ids
    from invenio_files_rest.models import ObjectVersion
    root_file_id_list = []
    bucket_id = record.get('_buckets', {}).get('deposit')

    for filename in available_filenames:
        obv = ObjectVersion.get(bucket_id, filename)
        root_file_id_list.append(str(obv.root_file_id) if obv else '')

    # Set parameter
    params = {
        'item_id': str(item_id),
        'root_file_id_list': root_file_id_list,
    }

    if query_date:
        year = int(query_date[0: 4])
        month = int(query_date[5: 7])
        _, lastday = calendar.monthrange(year, month)
        params.update({
            'start_date': f'{query_date}-01',
            'end_date': f'{query_date}-{str(lastday).zfill(2)}T23:59:59'
        })

    try:
        try:
            from invenio_stats.proxies import current_stats
            # file download query
            query_download_total_cfg = current_stats.queries['item-file-download-aggs']
            query_download_total = query_download_total_cfg.query_class(**query_download_total_cfg.query_config)
            res_download_total = query_download_total.run(**params)
        except Exception as e:
            current_app.logger.error(traceback.print_exc())
            res_download_total = {'download_ranking': {'buckets': []}}

        for b in res_download_total.get('download_ranking', {}).get('buckets'):
            for r in result['ranking']:
                if r.get('filename') == b.get('key'):
                    r['download_total'] = b.get('doc_count')
                    break

        # Sort
        result['ranking'].sort(key=lambda x:x['download_total'], reverse=True)
        if size:
            result['ranking'] = result['ranking'][:int(size)]

    except Exception as e:
        current_app.logger.error(traceback.print_exc())
        current_app.logger.debug(e)

    if query_date:
        result['period'] = query_date
    else:
        result['period'] = 'total'

    return result


# --- 通知対象取得関数 ---

def get_notification_targets(deposit, user_id, shared_id):
    """
    Retrieve notification targets for a given deposit and user.

    Args:
        deposit (dict): The deposit data containing information about owners
                        and shared users.
        user_id (int): The ID of the current user.

    Returns:
        dict: A dictionary containing the following keys:
            - "targets" (list): List of User objects who are the notification targets.
            - "settings" (dict): A dictionary mapping user IDs to their notification settings.
            - "profiles" (dict): A dictionary mapping user IDs to their user profiles.
    """
    owners = deposit.get("_deposit", {}).get("owners", [])
    set_target_id = set(owners)
    is_shared = shared_id != -1
    if is_shared:
        set_target_id.add(shared_id)
    set_target_id.discard(int(user_id))

    target_ids = list(set_target_id)
    current_app.logger.debug(f"[get_notification_targets] target_ids: {target_ids}")

    try:
        targets = User.query.filter(User.id.in_(target_ids)).all()
        settings = NotificationsUserSettings.query.filter(
            NotificationsUserSettings.user_id.in_(target_ids)
        ).all()
        profiles = UserProfile.query.filter(
            UserProfile.user_id.in_(target_ids)
        ).all()

        return {
            "targets": targets,
            "settings": {s.user_id: s for s in settings},
            "profiles": {p.user_id: p for p in profiles}
        }
    except SQLAlchemyError:
        current_app.logger.exception("[get_notification_targets] DB access failed")
        return dict()


def get_notification_targets_approver(activity):
    """
    Retrieve notification targets for the approval process in a workflow.

    Args:
        activity (Activity): The workflow activity instance containing information such as
            the actor, flow definition, and community ID.

    Returns:
        dict: A dictionary containing the following keys:
            - "targets" (list of User): List of users to be notified.
            - "settings" (dict): Mapping of user_id to NotificationsUserSettings for the targets.
            - "profiles" (dict): Mapping of user_id to UserProfile for the targets.
            - "actor" (dict): A dictionary with the name and email of the actor (initiator).
    """
    from weko_workflow.api import Flow, GetCommunity
    from weko_workflow.models import Action
    try:
        actor_id = activity.activity_login_user
        actor_profile = UserProfile.get_by_userid(actor_id)
        actor_name = actor_profile.username if actor_profile else None

        flow_id = activity.flow_define.flow_id
        flow_detail = Flow().get_flow_detail(flow_id)
        approval_action = Action.query.filter_by(
            action_endpoint="approval"
        ).one()
        approval_action_role = None
        for action in flow_detail.flow_actions:
            if (
                action.action_id == approval_action.id
                and action.action_order == activity.action_order + 1
            ):
                approval_action_role = action.action_role
                break

        admin_role_id = Role.query.filter_by(
            name=current_app.config.get("WEKO_ADMIN_PERMISSION_ROLE_REPO")
        ).one().id

        target_role = {admin_role_id}
        if approval_action_role:
            action_role_id = approval_action_role.action_role
            if isinstance(action_role_id, int) and approval_action_role.action_role_exclude:
                target_role.discard(action_role_id)

        set_target_id = {
            uid[0] for uid in db.session.query(userrole.c.user_id)
            .filter(userrole.c.role_id.in_(target_role)).distinct()
        }

        if approval_action_role:
            action_user_id = approval_action_role.action_user
            if isinstance(action_user_id, int):
                if approval_action_role.action_user_exclude:
                    set_target_id.discard(action_user_id)
                else:
                    set_target_id.add(action_user_id)

        community_id = activity.activity_community_id
        if community_id is not None:
            community_admin_role_id = Role.query.filter_by(
                name=current_app.config.get("WEKO_ADMIN_PERMISSION_ROLE_COMMUNITY")
            ).one().id
            community_owner_role_id = GetCommunity.get_community_by_id(community_id).id_role
            role_left = userrole.alias("role_left")
            role_right = userrole.alias("role_right")

            set_community_admin_id = {
                uid[0] for uid in db.session.query(role_left.c.user_id)
                .join(role_right, role_left.c.role_id == role_right.c.role_id)
                .filter(
                    role_left.c.role_id == community_admin_role_id,
                    role_right.c.role_id == community_owner_role_id
                ).distinct()
            }
            set_target_id.update(set_community_admin_id)

        is_shared = activity.shared_user_id is not None and activity.shared_user_id != -1
        if not is_shared:
            set_target_id.discard(actor_id)

        targets = User.query.filter(User.id.in_(list(set_target_id))).all()
        settings = NotificationsUserSettings.query.filter(
            NotificationsUserSettings.user_id.in_(list(set_target_id))
        ).all()
        profiles = UserProfile.query.filter(
            UserProfile.user_id.in_(list(set_target_id))
        ).all()
        actor = User.query.filter_by(id=actor_id).one_or_none()

        return {
            "targets": targets,
            "settings": {s.user_id: s for s in settings},
            "profiles": {p.user_id: p for p in profiles},
            "actor": {"name": actor_name, "email": actor.email}
        }

    except SQLAlchemyError:
        current_app.logger.exception("[get_notification_targets_approver] DB access failed")
        return dict()


def get_notification_targets_approved(deposit, user_id, activity):
    """
    Retrieve notification targets for a given deposit and user.

    Args:
        deposit (dict): The deposit data containing information about owners
                        and shared users.
        user_id (int): The ID of the current user.
        activity (Activity): The workflow activity instance.

    Returns:
        dict: A dictionary containing the following keys:
            - "targets" (list): List of User objects who are the notification targets.
            - "settings" (dict): A dictionary mapping user IDs to their notification settings.
            - "profiles" (dict): A dictionary mapping user IDs to their user profiles.
    """
    owners = deposit.get("_deposit", {}).get("owners", [])
    set_target_id = set(owners)
    is_shared = deposit.get("weko_shared_id") != -1

    actor_id = activity.activity_login_user
    if actor_id:
        set_target_id.add(actor_id)

    if is_shared:
        set_target_id.add(deposit.get("weko_shared_id"))
    else:
        set_target_id.discard(int(user_id))

    target_ids = list(set_target_id)
    current_app.logger.debug(f"[get_notification_targets_approved] target_ids: {target_ids}")

    try:
        targets = User.query.filter(User.id.in_(target_ids)).all()
        settings = NotificationsUserSettings.query.filter(
            NotificationsUserSettings.user_id.in_(target_ids)
        ).all()
        profiles = UserProfile.query.filter(
            UserProfile.user_id.in_(target_ids)
        ).all()

        return {
            "targets": targets,
            "settings": {s.user_id: s for s in settings},
            "profiles": {p.user_id: p for p in profiles}
        }
    except SQLAlchemyError:
        current_app.logger.exception("[get_notification_targets_approved] DB access failed")
        return dict()

# --- メール本文生成関数 ---

def create_item_deleted_data(deposit, profile, target, url):
    """
    Generate the email content for item deletion notification.

    Args:
        deposit (dict): Data of the deleted item.
        profile (UserProfile): Profile information of the user receiving the notification.
        target (User): User object of the recipient.
        url (str): URL of the deleted item.

    Returns:
        dict: A dictionary containing the filled email subject and body with the following keys:
              - 'subject' (str): The subject of the email.
              - 'body' (str): The body of the email.
    """
    from weko_workflow.utils import load_template, fill_template
    language = (
        profile.language if profile
        else current_app.config.get("WEKO_WORKFLOW_MAIL_DEFAULT_LANGUAGE")
    )
    timezone = profile.timezone if profile else "UTC"
    registration_date = datetime.now(pytz.timezone(timezone))

    template_file = 'email_notification_item_deleted_{language}.tpl'
    template = load_template(template_file, language)

    data = {
        "item_title": deposit.get("item_title", ""),
        "submitter_name": profile.username if profile else target.email,
        "registration_date": registration_date.strftime("%Y-%m-%d %H:%M:%S"),
        "record_url": url
    }

    return fill_template(template, data)



def create_direct_registered_data(deposit, profile, target, url):
    """
    Generate email content for a direct registration notification.

    Args:
        deposit (dict): Data of the registered item.
        profile (UserProfile): Profile information of the user receiving the notification.
        target (User): User object of the recipient.
        url (str): URL of the registered item.

    Returns:
        dict: A dictionary containing the filled email subject and body with the following keys:
            - 'subject' (str): The subject of the email.
            - 'body' (str): The body of the email.
    """
    from weko_workflow.utils import load_template, fill_template
    language = (
        profile.language if profile
        else current_app.config.get("WEKO_WORKFLOW_MAIL_DEFAULT_LANGUAGE")
    )
    timezone = profile.timezone if profile else "UTC"
    registration_date = datetime.now(pytz.timezone(timezone))

    template_file = 'email_notification_item_registered_{language}.tpl'
    template = load_template(template_file, language)

    data = {
        "item_title": deposit.get("item_title", ""),
        "submitter_name": profile.username if profile else target.email,
        "registration_date": registration_date.strftime("%Y-%m-%d %H:%M:%S"),
        "record_url": url
    }
    return fill_template(template, data)


# --- 共通通知送信関数 ---

def send_mail_from_notification_info(get_info_func, context_obj, content_creator, record_url=None):
    """
    Send notification emails to a list of users based on the provided context and content creator function.

    Args:
        get_info_func (function): A function that retrieves notification target information.
                                  It should accept `context_obj` as an argument and return a dictionary
                                  containing "targets", "settings", "profiles", and optionally "actor".
        context_obj (object): The context object used to retrieve notification target information.
        content_creator (function): A function that generates the email content.
                                     It should accept `context_obj`, `profile`, `target`, `record_url`, and optionally `actor`
                                     as arguments and return a dictionary with "subject" and "body" keys.
        record_url (str, optional): The URL of the record associated with the notification. Defaults to None.

    Returns:
        int: The total number of successfully sent emails.
"""
    from weko_workflow.utils import send_mail

    with db.session.begin_nested():
        info = get_info_func(context_obj)

    targets = info.get("targets", [])
    settings = info.get("settings", {})
    profiles = info.get("profiles", {})
    actor = info.get("actor", None)

    send_count = 0

    for target in targets:
        try:
            setting = settings.get(target.id)
            if not setting:
                current_app.logger.debug(f"[send_mail] No setting for user_id: {target.id}")
                continue
            if not target.confirmed_at:
                current_app.logger.debug(f"[send_mail] User {target.id} not confirmed")
                continue
            if not setting.subscribe_email:
                current_app.logger.debug(f"[send_mail] User {target.id} unsubscribed from emails")
                continue

            profile = profiles.get(target.id)
            if actor:
                mail_data = content_creator(context_obj, profile, target, record_url, actor)
            else:
                mail_data = content_creator(context_obj, profile, target, record_url)

            recipient = target.email
            current_app.logger.debug(f"[send_mail] Sending to: {target.id}")
            res = send_mail(mail_data.get("subject"), recipient, mail_data.get("body"))

            if res:
                send_count += 1

        except Exception:
            current_app.logger.exception(
                f"[send_mail] Failed for user_id: {target.id}"
            )

    current_app.logger.debug(f"[send_mail] Total mails sent: {send_count}")
    return send_count


# --- 各イベントから呼び出すエントリーポイント ---

def send_mail_item_deleted(pid_value, deposit, user_id, shared_id=-1):
    """
    Send a notification email when an item is deleted.

    Args:
        pid_value (str): The persistent identifier (PID) of the deleted item.
        deposit (dict): The deposit data of the deleted item.
        user_id (int): The ID of the user who initiated the deletion.

    Returns:
        int: The total number of successfully sent emails.
    """
    record_url = request.host_url + f"records/{pid_value}"
    current_app.logger.debug(f"[send_mail_item_deleted] pid_value: {pid_value}, user_id: {user_id}")
    return send_mail_from_notification_info(
        get_info_func=lambda obj: get_notification_targets(obj, user_id, shared_id),
        context_obj=deposit,
        content_creator=create_item_deleted_data,
        record_url=record_url
    )


def send_mail_direct_registered(pid_value, user_id, share_id=-1):
    """
    Send a notification email for a directly registered item.

    Args:
        pid_value (str): The persistent identifier (PID) of the registered item.
        user_id (int): The ID of the user who registered the item.
        share_id (int): The shared ID of the user.

    Returns:
        int: The total number of successfully sent emails.
    """
    deposit = WekoRecord.get_record_by_pid(pid_value)
    record_url = request.host_url + f"records/{pid_value}"
    current_app.logger.debug(f"[send_mail_direct_registered] pid_value: {pid_value}, user_id: {user_id}")
    return send_mail_from_notification_info(
        get_info_func=lambda obj: get_notification_targets(obj, user_id, share_id),
        context_obj=deposit,
        content_creator=create_direct_registered_data,
        record_url=record_url
    )
