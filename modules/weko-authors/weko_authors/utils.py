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

"""Utils for weko-authors."""

import base64
import csv
import os
import chardet
import io
import re
import sys
import tempfile
import traceback
import re
import copy
import json
import math
import datetime
from time import sleep
from copy import deepcopy
from functools import reduce
from operator import getitem
from sys import stdout
from sqlalchemy.exc import SQLAlchemyError
from redis.exceptions import RedisError

from flask import current_app, jsonify
from flask_babelex import gettext as _
from flask_security import current_user
from invenio_accounts.models import User
from invenio_cache import current_cache
from invenio_db import db
from invenio_indexer.api import RecordIndexer

from .contrib.validation import (
    validate_by_extend_validator, validate_external_author_identifier,
    validate_map, validate_required, check_weko_id_is_exits_for_import
)
from .api import WekoAuthors
from .errors import AuthorsValidationError, AuthorsPermissionError
from .models import AuthorsPrefixSettings, AuthorsAffiliationSettings, Authors

def update_cache_data(key: str, value: str, timeout=None):
    """Create or Update cache data.

    Args:
        key (str): Cache key.
        value (str): Cache value.
        timeout (optional): Cache expired.
    """
    if timeout is not None:
        current_cache.set(key, value, timeout=timeout)
    else:
        current_cache.set(key, value)

def get_author_prefix_obj(scheme):
    """Check item Scheme exist in DB."""
    try:
        return db.session.query(AuthorsPrefixSettings).filter(
            AuthorsPrefixSettings.scheme == scheme).one_or_none()
    except Exception as ex:
        current_app.logger.debug(ex)
    return None

def get_author_prefix_obj_by_id(id):
    """Check if the item Scheme exists in the DB by ID.

    Args:
        id (int): author_prefix record ID.

    Returns:
        AuthorsPrefixSettings: The prefix object if exists, else None.
    """
    try:
        obj = AuthorsPrefixSettings.query.filter(
            AuthorsPrefixSettings.id == id).one_or_none()
    except Exception as ex:
        current_app.logger.error(ex)
        traceback.print_exc()
    return obj if isinstance(obj, AuthorsPrefixSettings) else None

def get_author_affiliation_obj(scheme):
    """Check item Scheme exist in DB."""
    try:
        return db.session.query(AuthorsAffiliationSettings).filter(
            AuthorsAffiliationSettings.scheme == scheme).one_or_none()
    except Exception as ex:
        current_app.logger.error(ex)
        traceback.print_exc()
    return None

def get_author_affiliation_obj_by_id(id):
    """Check if the item Scheme exists in the DB by ID.

    Args:
        id (int): ID value.

    Returns:
        AuthorsAffiliationSettings: The affiliation object if exists, else None.
    """
    try:
        obj = AuthorsAffiliationSettings.query.filter(
            AuthorsAffiliationSettings.id == id).one_or_none()
    except Exception as ex:
        current_app.logger.error(ex)
        traceback.print_exc()
    return obj if isinstance(obj, AuthorsAffiliationSettings) else None


def check_email_existed(email: str):
    """Check email has existed.

    :param email: email string.
    :returns: author info.
    """
    body = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"gather_flg": 0}},
                    {"term": {"emailInfo.email.raw": email}}
                ]
            }
        }
    }

    indexer = RecordIndexer()
    result = indexer.client.search(
        index=current_app.config['WEKO_AUTHORS_ES_INDEX_NAME'],
        doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],
        body=body
    )

    if result['hits']['total']:
        return {
            'email': email,
            'author_id': result['hits']['hits'][0]['_source']['pk_id']
        }
    else:
        return {
            'email': email,
            'author_id': ''
        }

def validate_weko_id(weko_id, pk_id = None):
    """Validate WEKO ID.

    Args:
        weko_id (str): WEKO ID.
        pk_id (str, optional): Primary key ID.

    Returns:
        tuple: (bool, str or None)
    """
    if not bool(re.fullmatch(r'[0-9]+', weko_id)):
        return False, "not half digit"

    try:
        result = check_weko_id_is_exists(weko_id, pk_id)
    except Exception as ex:
        current_app.logger.error(ex)
        raise ex

    if result == True:
        return False, "already exists"
    return True, None

def check_weko_id_is_exists(weko_id, pk_id = None):
    """Check if weko_id exists in Elasticsearch.

    If author_id is the same as pk_id, skip checking.
    weko_id is the value of authorId where authorIdInfo.Idtype is 1.

    Args:
        weko_id (str): WEKO ID.
        pk_id (str, optional): Primary key ID.

    Returns:
        bool: True if exists, False otherwise.
    """
    query = {
        "_source": ["pk_id", "authorIdInfo"],  # Get Author id info field only
        "query": {
            "bool": {
                "must": [
                    {
                        "term": {
                            "authorIdInfo.authorId": weko_id
                        }
                    },
                    {"term": {"gather_flg": {"value": 0}}}
                ],
                "must_not": [
                    {"term": {"is_deleted": True}}
                ]
            }
        }
    }

    # search from elasticsearch
    indexer = RecordIndexer()
    result = indexer.client.search(
        index=current_app.config['WEKO_AUTHORS_ES_INDEX_NAME'],
        body=query
    )

    # if same weko_id exists, return True
    for res in result['hits']['hits']:
        # if same author_id exists, skip checking
        if pk_id and pk_id == res['_source']['pk_id']:
            continue
        author_id_info_from_es = res['_source']['authorIdInfo']
        for info in author_id_info_from_es:
            if info.get('idType') == '1':
                author_id = info.get('authorId')
                if author_id == weko_id:
                    return True
    return False


def check_period_date(data):
    """Check period date.

    Args:
        data (dict): json data of author DB.

    Returns:
        tuple: (bool, str or None)
            - bool: True if period date is valid, False otherwise.
            - str: Error type if period date is invalid, None otherwise.
    """
    from datetime import datetime
    if data.get("affiliationInfo"):
        for affiliation in data.get("affiliationInfo"):
            if affiliation.get("affiliationPeriodInfo"):
                for periodinfo in affiliation.get("affiliationPeriodInfo"):
                    if periodinfo.get("periodStart") or periodinfo.get("periodEnd"):
                        if periodinfo.get("periodStart"):
                            date_str = periodinfo.get("periodStart")
                            try:
                                datetime.strptime(date_str, "%Y-%m-%d")
                            except ValueError:
                                return False, "not date format"
                        if periodinfo.get("periodEnd"):
                            date_str = periodinfo.get("periodEnd")
                            try:
                                datetime.strptime(date_str, "%Y-%m-%d")
                            except ValueError:
                                return False, "not date format"
                        if periodinfo.get("periodStart") and periodinfo.get("periodEnd"):
                            period_start = datetime.strptime(periodinfo.get("periodStart"), "%Y-%m-%d")
                            period_end = datetime.strptime(periodinfo.get("periodEnd"), "%Y-%m-%d")
                            if period_start > period_end:
                                return False, "start is after end"
    return True, None

def get_export_status(user_id):
    """Get export status from cache."""
    key = f'{current_app.config.get("WEKO_AUTHORS_EXPORT_CACHE_STATUS_KEY")}_{user_id}'
    return current_cache.get(key) or {}


def set_export_status(user_id, start_time=None, task_id=None):
    """Set export status into cache."""
    data = get_export_status(user_id) or dict()
    if start_time:
        data['start_time'] = start_time
    if task_id:
        data['task_id'] = task_id

    key = f'{current_app.config.get("WEKO_AUTHORS_EXPORT_CACHE_STATUS_KEY")}_{user_id}'
    current_cache.set(key, data, timeout=0)
    return data


def delete_export_status(user_id):
    """Delete export status."""
    key = f'{current_app.config.get("WEKO_AUTHORS_EXPORT_CACHE_STATUS_KEY")}_{user_id}'
    current_cache.delete(key)


def get_export_url(user_id):
    """Get exported info from cache."""
    # return current_cache.get(current_app.config.get("WEKO_AUTHORS_EXPORT_CACHE_URL_KEY")) or {}
    key = f'{current_app.config.get("WEKO_AUTHORS_EXPORT_CACHE_URL_KEY")}_{user_id}'
    return current_cache.get(key) or {}


def save_export_url(start_time, end_time, file_uri, user_id):
    """Save exported info into cache."""
    data = dict(
        start_time=start_time,
        end_time=end_time,
        file_uri=file_uri
    )

    key = f'{current_app.config.get("WEKO_AUTHORS_EXPORT_CACHE_URL_KEY")}_{user_id}'
    current_cache.set(key, data, timeout=0)
    return data

def delete_export_url(user_id):
    """Delete exported URL from cache."""
    key = f'{current_app.config.get("WEKO_AUTHORS_EXPORT_CACHE_URL_KEY")}_{user_id}'
    current_cache.delete(key)
    # current_cache.delete(current_app.config.get("WEKO_AUTHORS_EXPORT_CACHE_URL_KEY"))

def handle_exception(ex, attempt, retrys, interval, stop_point=0):
    """Manage sleep and retries.

    Args:
        ex (Exception): Exception object.
        attempt (int): Number of attempts.
        retrys (int): Number of retries.
        interval (int): Retry interval.
        stop_point (int, optional): Stop point. Defaults to 0.
    """
    current_app.logger.error(ex)
    # Raise the exception for the last retry
    if attempt == retrys - 1:
        current_app.logger.info(f"Connection failed, Stop export.")
        if stop_point != 0:
            update_cache_data(
                current_app.config["WEKO_AUTHORS_EXPORT_CACHE_STOP_POINT_KEY"],
                stop_point,
                current_app.config["WEKO_AUTHORS_CACHE_TTL"]
                )
        raise ex
    current_app.logger.info(f"Connection failed, retrying in {interval} seconds...")
    sleep(interval)

def export_authors(user_id):
    """Export all authors.

    Returns:
        str: File URI.
    """
    from invenio_files_rest.models import FileInstance, Location
    file_uri = None
    retrys = current_app.config["WEKO_AUTHORS_BULK_EXPORT_MAX_RETRY"]
    interval = current_app.config["WEKO_AUTHORS_BULK_EXPORT_RETRY_INTERVAL"]
    size =  current_app.config.get("WEKO_AUTHORS_EXPORT_BATCH_SIZE", 1000)
    stop_point = current_cache.get(
        f'{current_app.config["WEKO_AUTHORS_EXPORT_CACHE_STOP_POINT_KEY"]}_{user_id}'
    )
    mappings = []
    schemes = {}
    records_count = 0
    temp_file_path = ""

    try:

        for attempt in range(retrys):
            try:
                # get mapping
                mappings = deepcopy(current_app.config["WEKO_AUTHORS_FILE_MAPPING"])
                affiliation_mappings = deepcopy(current_app.config["WEKO_AUTHORS_FILE_MAPPING_FOR_AFFILIATION"])
                community_mappings = deepcopy(current_app.config["WEKO_AUTHORS_FILE_MAPPING_FOR_COMMUNITY"])

                user = User.query.get(user_id)
                communities, is_super = get_managed_community(user)
                community_ids = [c.id for c in communities] if not is_super else None

                # get the number of authors (excluding deleted and merged authors)
                records_count = WekoAuthors.get_records_count(False, False, community_ids)
                # Get the maximum value of multiple items on the mapping
                mappings, affiliation_mappings, community_mappings = \
                    WekoAuthors.mapping_max_item(mappings, affiliation_mappings, community_mappings, records_count)

                schemes = WekoAuthors.get_identifier_scheme_info()
                aff_schemes = WekoAuthors.get_affiliation_identifier_scheme_info()

                # Get the path of the temporary file
                temp_file_path=current_cache.get(
                    f'{current_app.config["WEKO_AUTHORS_EXPORT_CACHE_TEMP_FILE_PATH_KEY"]}_{user_id}')
                break
            except SQLAlchemyError as ex:
                traceback.print_exc(file=stdout)
                handle_exception(ex, attempt, retrys, interval)
            except RedisError as ex:
                traceback.print_exc(file=stdout)
                handle_exception(ex, attempt, retrys, interval)
            except TimeoutError as ex:
                traceback.print_exc(file=stdout)
                handle_exception(ex, attempt, retrys, interval)

        # If stop_point is not None, set start_point to stop_point
        start_point = stop_point if stop_point else 0

        current_cache.delete(
            f'{current_app.config["WEKO_AUTHORS_EXPORT_CACHE_STOP_POINT_KEY"]}_{user_id}')
        # Get authors 1000 at a time and write data
        for i in range(start_point, records_count, size):
            current_app.logger.info(f"Export authors start_point：{start_point}")
            row_header = []
            row_label_en = []
            row_label_jp = []
            row_data = []

            # Retry process for obtaining author information
            for attempt in range(retrys):
                current_app.logger.info(f"Export authors retry count：{attempt}")
                try:
                    # Get author information from start in WEKO_EXPORT_BATCH_SIZE units
                    authors = WekoAuthors.get_by_range(i, size, False, False, community_ids)
                    row_header, row_label_en, row_label_jp, row_data =\
                        WekoAuthors.prepare_export_data(mappings, affiliation_mappings, community_mappings, authors, schemes, aff_schemes, i, size)
                    break
                except SQLAlchemyError as ex:
                    traceback.print_exc(file=stdout)
                    handle_exception(ex, attempt, retrys, interval, stop_point=i)
                except RedisError as ex:
                    traceback.print_exc(file=stdout)
                    handle_exception(ex, attempt, retrys, interval, stop_point=i)
                except TimeoutError as ex:
                    traceback.print_exc(file=stdout)
                    handle_exception(ex, attempt, retrys, interval, stop_point=i)
            # Write to temporary file
            write_to_tempfile(i, row_header, row_label_en, row_label_jp, row_data, user_id)
        # Save the completed temporary file to file instance
        with open(temp_file_path, 'rb') as f:
            reader = io.BufferedReader(f)
            # save data into location
            cache_url = get_export_url(user_id)
            if not cache_url:
                file = FileInstance.create()
                file.set_contents(
                    reader, default_location=Location.get_default().uri)
            else:
                file = FileInstance.get_by_uri(cache_url['file_uri'])
                file.writable = True
                file.set_contents(reader)
        file_uri = file.uri if file else None
        # Delete temporary file after completion
        os.remove(temp_file_path)
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        # If stop_point is not set, delete the temporary file
        if not current_cache.get(f'{current_app.config["WEKO_AUTHORS_EXPORT_CACHE_STOP_POINT_KEY"]}_{user_id}'):
            os.remove(temp_file_path)
        current_app.logger.error(ex)
        traceback.print_exc(file=stdout)
    current_cache.set(
        f'{current_app.config.get("WEKO_AUTHORS_EXPORT_TARGET_CACHE_KEY")}_{user_id}',
        "author_db",
        timeout=0
    )

    return file_uri

def export_prefix(target, user_id):
    """Export id_prefix or affiliation_id.

    Args:
        target (str): Export target. 'id_prefix' or 'affiliation_id'.

    Returns:
        str: File URI.
    """
    from invenio_files_rest.models import FileInstance, Location
    file_uri = None
    retrys = current_app.config["WEKO_AUTHORS_BULK_EXPORT_MAX_RETRY"]
    interval = current_app.config["WEKO_AUTHORS_BULK_EXPORT_RETRY_INTERVAL"]
    target_db_name = "author_prefix_settings" if target == "id_prefix" else "author_affiliation_settings"
    row_first = [f"#{target_db_name}"]
    row_header = ["#scheme", "name", "url", "is_deleted"]
    row_label_en = ["#Scheme", "Name", "URL", "Delete Flag"]
    row_label_jp = ["#スキーム", "名前", "URL", "削除フラグ"]

    for attempt in range(retrys):
        try:
            user = User.query.get(user_id)
            communities, is_super = get_managed_community(user)
            community_ids = [c.id for c in communities] if not is_super else None

            if target == "id_prefix":
                prefix = WekoAuthors.get_id_prefix_all(community_ids=community_ids)
            elif target == "affiliation_id":
                prefix = WekoAuthors.get_affiliation_id_all(community_ids=community_ids)

            community_length = max(list(map(
                lambda x: len(x.communities), prefix
            )))
            current_app.logger.error(f"Community length: {community_length}")

            row_header += [f"community_ids[{i}]" for i in range(community_length)]
            row_label_en += [f"Community ID[{i}]" for i in range(community_length)]
            row_label_jp += [f"コミュニティID[{i}]" for i in range(community_length)]

            row_data = WekoAuthors.prepare_export_prefix(target, prefix, community_length)
            # write file data to a stream
            file_io = io.StringIO()
            if current_app.config.get('WEKO_ADMIN_OUTPUT_FORMAT', 'tsv').lower() == 'csv':
                writer = csv.writer(file_io, delimiter=',',
                                    quotechar='"', quoting=csv.QUOTE_MINIMAL,
                                    lineterminator='\n')
            else:
                writer = csv.writer(file_io, delimiter='\t',
                                    quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerows([row_first, row_header, row_label_en, row_label_jp, *row_data])
            reader = io.BufferedReader(io.BytesIO(
                file_io.getvalue().encode("utf-8-sig")))

            # save data into location
            cache_url = get_export_url(user_id)
            if not cache_url:
                file = FileInstance.create()
                file.set_contents(
                    reader, default_location=Location.get_default().uri)
            else:
                file = FileInstance.get_by_uri(cache_url['file_uri'])
                file.writable = True
                file.set_contents(reader)
            file_uri = file.uri if file else None
            db.session.commit()
            current_cache.set(
                f'{current_app.config.get("WEKO_AUTHORS_EXPORT_TARGET_CACHE_KEY")}_{user_id}',
                target,
                timeout=0
            )
            break
        except SQLAlchemyError as ex:
            traceback.print_exc(file=stdout)
            handle_exception(ex, attempt, retrys, interval)
        except RedisError as ex:
            traceback.print_exc(file=stdout)
            handle_exception(ex, attempt, retrys, interval)
        except TimeoutError as ex:
            traceback.print_exc(file=stdout)
            handle_exception(ex, attempt, retrys, interval)
    return file_uri

def check_file_name(export_target):
    """Get file name.

    Args:
        export_target (str):
            Export target. "author_db" or "id_prefix" or "affiliation_id".

    Returns:
        str: File base name.
    """
    file_base_name = ""
    if export_target == "author_db":
        file_base_name = current_app.config.get('WEKO_AUTHORS_EXPORT_FILE_NAME')
    elif export_target == "id_prefix":
        file_base_name = current_app.config.get('WEKO_AUTHORS_ID_PREFIX_EXPORT_FILE_NAME')
    elif export_target == "affiliation_id":
        file_base_name = current_app.config.get('WEKO_AUTHORS_AFFILIATION_EXPORT_FILE_NAME')
    return file_base_name

def write_to_tempfile(start, row_header, row_label_en, row_label_jp, row_data, user_id):
    """Write data to a temporary file.

    Args:
        start (int): Start position of data.
        row_header (list): Header.
        row_label_en (list): English labels.
        row_label_jp (list): Japanese labels.
        row_data (list): Data.
    """
    # Get the path of the temporary file
    temp_file_path=current_cache.get( \
        f'{current_app.config["WEKO_AUTHORS_EXPORT_CACHE_TEMP_FILE_PATH_KEY"]}_{user_id}')

    # Open the file and write data
    try:
        with open(temp_file_path, 'a', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            # Write header and labels only on the first line
            if start == 0:
                writer.writerow(row_header)
                writer.writerow(row_label_en)
                writer.writerow(row_label_jp)
            writer.writerows(row_data)
    except Exception as ex:
        current_app.logger.error(ex)
        traceback.print_exc(file=stdout)

def check_import_data(file_name):
    """Validate importing tsv/csv file.

    Args:
        file_name (str): File name.

    Returns:
        dict: Check information.
    """
    result = {}
    temp_file_path = current_cache.get(
        current_app.config["WEKO_AUTHORS_IMPORT_CACHE_USER_TSV_FILE_KEY"]
    )
    try:
        affiliation_mappings = deepcopy(current_app.config["WEKO_AUTHORS_FILE_MAPPING_FOR_AFFILIATION"])
        mapping = deepcopy(current_app.config["WEKO_AUTHORS_FILE_MAPPING"])
        mapping.append(affiliation_mappings)
        flat_mapping_all, flat_mapping_ids = flatten_authors_mapping(mapping)
        file_format = file_name.split('.')[-1].lower()
        max_part_num = unpackage_and_check_import_file(
            file_format, file_name, temp_file_path, flat_mapping_ids
        )
        list_import_id=[]
        temp_folder_path = os.path.join(
            tempfile.gettempdir(),
            current_app.config.get("WEKO_AUTHORS_IMPORT_TMP_DIR")
        )
        base_file_name = os.path.splitext(os.path.basename(temp_file_path))[0]
        check_file_name = f"{base_file_name}-check"
        num_total = 0
        num_new = 0
        num_update = 0
        num_delete = 0
        num_error = 0
        for i in range(1, max_part_num+1):
            part_file_name = f'{base_file_name}-part{i}'
            part_file_path = os.path.join(temp_folder_path, part_file_name)
            with open(part_file_path, "r", encoding="utf-8-sig") as pf:
                data = json.load(pf)
                result_part = validate_import_data(
                    file_format, data, flat_mapping_ids, flat_mapping_all, list_import_id)
                num_total += len(result_part)
                num_new += len([item for item in result_part\
                    if item['status'] == 'new' and not item.get('errors')])
                num_update += len([item for item in result_part\
                    if item['status'] == 'update' and not item.get('errors')])
                num_delete += len([item for item in result_part\
                    if item['status'] == 'deleted' and not item.get('errors')])
                num_error += len([item for item in result_part\
                    if item.get('errors')])
            write_tmp_part_file(i, result_part, check_file_name)
            try:
                os.remove(part_file_path)
                current_app.logger.info(f"Deleted: {part_file_path}")
            except Exception as e:
                current_app.logger.error(f"Error deleting {part_file_path}: {e}")
                traceback.print_exc()
        part1_check_file_name = f"{check_file_name}-part1"
        check_file_part1_path = os.path.join(temp_folder_path, part1_check_file_name)
        with open(check_file_part1_path, "r", encoding="utf-8-sig") as check_part1:
            result['list_import_data'] = json.load(check_part1)
        result["max_page"] = max_part_num
        result["counts"]={}
        result["counts"]["num_total"] = num_total
        result["counts"]["num_new"] = num_new
        result["counts"]["num_update"] = num_update
        result["counts"]["num_delete"] = num_delete
        result["counts"]["num_error"] = num_error

    except Exception as ex:
        error = _('Internal server error')
        traceback.print_exc()
        if isinstance(ex, UnicodeDecodeError):
            error = ex.reason
        elif ex.args and len(ex.args) and isinstance(ex.args[0], dict) \
                and ex.args[0].get('error_msg'):
            error = ex.args[0].get('error_msg')
        result['error'] = error
    try:
        os.remove(temp_file_path)
        current_app.logger.debug(f"Deleted: {temp_file_path}")
    except Exception as e:
        current_app.logger.error(f"Error deleting {temp_file_path}: {e}")
        traceback.print_exc()

    return result

def check_import_data_for_prefix(target, file_name: str, file_content: str):
    """Validate tsv/csv file for id_prefix or affiliation_id import.

    Args:
        target (str): Import target.
        file_name (str): File name.
        file_content (str): File content (base64).

    Returns:
        dict: Check information.
    """
    tmp_prefix = current_app.config['WEKO_AUTHORS_IMPORT_TMP_PREFIX']
    temp_file = tempfile.NamedTemporaryFile(prefix=tmp_prefix)
    result = {}

    try:
        temp_file.write(base64.b64decode(file_content))
        temp_file.flush()

        file_format = file_name.split('.')[-1].lower()
        file_data = unpackage_and_check_import_file_for_prefix(
            file_format, file_name, temp_file.name)
        result['list_import_data'] = validate_import_data_for_prefix(file_data, target)
    except Exception as ex:
        error = _('Internal server error')
        traceback.print_exc()
        if isinstance(ex, UnicodeDecodeError):
            error = ex.reason
        elif ex.args and len(ex.args) and isinstance(ex.args[0], dict) \
                and ex.args[0].get('error_msg'):
            error = ex.args[0].get('error_msg')
        result['error'] = error

    return result

def getEncode(filepath):
    """Detect file encoding.

    Args:
        filepath (str): File path.

    Returns:
        str: Detected encoding.
    """
    with open(filepath, mode='rb') as fr:
        b = fr.read()
    enc = chardet.detect(b)
    return enc.get('encoding', 'utf-8-sig')

def clean_deep(data):
    """Clean data recursively.

    Example:
        {'fullname': 'Jane Doe',
         'warnings': None,
         'email': {"test":"","test2":"test2"},
         'test': [{"test":""},{"test2":"test2"}]}
        becomes
        {'fullname': 'Jane Doe', 'email': {"test2":"test2"},
         'test': [{"test2":"test2"}]}

    Args:
        data (dict): Data to clean.

    Returns:
        dict: Cleaned data.
    """
    if isinstance(data, dict):
        return {k: clean_deep(v) for k, v in data.items() if v is not None and v != ''}
    elif isinstance(data, list):
        cleaned_list = [clean_deep(v) for v in data if v is not None and v != '']
        return [item for item in cleaned_list if item != {}]
    else:
        return data

def unpackage_and_check_import_file(file_format, file_name, temp_file_path, mapping_ids):
    """Unpackage and check format of import file.

    Args:
        file_format (str): File format.
        file_name (str): File uploaded name.
        temp_file_path (str): Temp file path.
        mapping_ids (list): List only mapping ids.

    Returns:
        list: Tsv data.

    """
    from weko_search_ui.utils import handle_check_consistence_with_mapping, \
        handle_check_duplication_item_id, parse_to_json_form
    header = []
    file_data = []
    current_app.logger.debug("temp_file_path:{}".format(temp_file_path))
    enc = getEncode(temp_file_path)
    json_size=current_app.config.get("WEKO_AUTHORS_IMPORT_BATCH_SIZE")
    with open(temp_file_path, 'r', newline="", encoding=enc) as file:
        if file_format == 'csv':
            file_reader = csv.reader(file, dialect='excel', delimiter=',')
        else:
            file_reader = csv.reader(file, dialect='excel', delimiter='\t')
        count = 0
        try:
            for num, data_row in enumerate(file_reader, start=1):
                count += 1
                if num == 1:
                    header = data_row
                    header[0] = header[0].replace('#', '', 1)
                    # remove BOM
                    # header[0] = header[0].replace('\ufeff', '')
                    duplication_item_ids = \
                        handle_check_duplication_item_id(header)
                    if duplication_item_ids:
                        msg = _(
                            'The following metadata keys are duplicated.'
                            '<br/>{}')
                        raise Exception({
                            'error_msg':
                                msg.format('<br/>'.join(duplication_item_ids))
                        })

                    not_consistent_list = \
                        handle_check_consistence_with_mapping(
                            mapping_ids, header)
                    if not_consistent_list:
                        msg = _('Specified item does not consistency '
                                'with DB item.<br/>{}')
                        raise Exception({
                            'error_msg': msg.format(
                                '<br/>'.join(not_consistent_list))
                        })
                elif num in [2, 3] and data_row[0].startswith('#'):
                    continue
                elif num > 3:
                    data_parse_metadata = clean_deep(parse_to_json_form(
                        zip(header, data_row),
                        include_empty=True
                    ))

                    if not data_parse_metadata:
                        raise Exception({
                            'error_msg': _('Cannot read {} file correctly.')
                                .format(file_format.upper())
                        })

                    file_data.append(dict(**data_parse_metadata))
                    # Write to a temporary file when File data is the same as json size
                    if len(file_data) == json_size:
                        write_tmp_part_file(math.ceil((num-3)/json_size), file_data, temp_file_path)
                        file_data = []
            # Write file_data that has not been written yet
            if len(file_data) != 0:
                write_tmp_part_file(math.ceil((count-3)/json_size), file_data, temp_file_path)
            # Error if the number of lines in the file is less than 3
            elif not file_data and count <= 3:
                current_app.logger.error("There is no data to import.")
                raise Exception({
                    'error_msg': _('There is no data to import.')
                })
        except UnicodeDecodeError as ex:
            ex.reason = _(
                '{} could not be read. Make sure the file format is '
                '{} and that the file is UTF-8 encoded.'
            ).format(file_name, file_format.upper())
            raise
        except Exception as ex:
            raise

    return math.ceil((count-3)/json_size)

def write_tmp_part_file(part_num, file_data, temp_file_path):
    """Write data to temp file for Import.

    Args:
        part_num (int): Count of list.
        file_data (list): Author data from tsv/csv.
        temp_file_path (str): Path of base file.
    """
    temp_folder_path = os.path.join(
        tempfile.gettempdir(),
        current_app.config.get("WEKO_AUTHORS_IMPORT_TMP_DIR")
    )
    base_name = os.path.splitext(os.path.basename(temp_file_path))[0]
    part_file_name = f"{base_name}-part{part_num}"
    part_file_path = os.path.join(temp_folder_path, part_file_name)
    with open(part_file_path, 'w', encoding='utf-8-sig') as part_file:
        json.dump(file_data, part_file)

def validate_import_data(file_format, file_data, mapping_ids, mapping, list_import_id):
    """Validate import data.

    Args:
        file_format (str): File format.
        file_data (list): Author data from tsv/csv.
        mapping_ids (list): List only mapping ids.
        mapping (list): List mapping.
        list_import_id (list): List import id.

    Returns:
        list: Author data after validation.
    """
    authors_prefix = {}
    affilaition_id_prefix = {}
    with db.session.no_autoflush:
        authors_prefix = AuthorsPrefixSettings.query.all()
        authors_prefix = {
            prefix.scheme: prefix.id for prefix in authors_prefix}
        affilaition_id_prefix = AuthorsAffiliationSettings.query.all()
        affilaition_id_prefix = {
            prefix.scheme: prefix.id for prefix in affilaition_id_prefix}

    existed_authors_id, existed_external_authors_id = \
        WekoAuthors.get_author_for_validation()
    for item in file_data:
        errors = []
        warnings = []

        pk_id = item.get('pk_id')
        weko_id = item.get("weko_id")
        current_weko_id = WekoAuthors.get_weko_id_by_pk_id(pk_id)
        item["current_weko_id"] = current_weko_id
        errors_msg = check_weko_id_is_exits_for_import(pk_id, weko_id, existed_external_authors_id)
        if errors_msg:
            errors.extend(errors_msg)

        # check duplication WEKO ID
        if pk_id and pk_id not in list_import_id:
            list_import_id.append(pk_id)
        elif pk_id:
            errors.append(_('There is duplicated data in the {} file.').format(file_format))

        # set status
        set_record_status(file_format, existed_authors_id, item, errors, warnings)

        try:
            community_ids= item.get('community_ids')
            if item.get('status') == 'new':
                validate_community_ids(community_ids, is_create=True)
            elif item.get('status') == 'update':
                old = Authors.query.get(pk_id)
                old_community_ids = [c.id for c in old.communities]
                validate_community_ids(community_ids, old_ids=old_community_ids)
            elif item.get('status') == 'deleted':
                check, message = check_delete_affiliation(pk_id)
                if not check:
                    errors.append(message)
        except AuthorsValidationError as e:
            errors.append(e.description)

        # get data folow by mapping
        data_by_mapping = {}
        for _key in mapping_ids:
            data_by_mapping[_key] = get_values_by_mapping(
                _key.split('.'), item)

        # Validation
        for field in mapping:
            _key = field['key']
            values = data_by_mapping[_key]
            validation = field['validation']

            # check required
            if validation.get('required'):
                errors_key = validate_required(
                    item, values, validation.get('required'))
                if errors_key:
                    errors.extend(list(map(
                        lambda k: _('{} is required item.').format(k),
                        errors_key
                    )))

            # check allow data
            if validation.get('map'):
                errors_key = validate_map(
                    values, validation.get('map'))
                if errors_key:
                    error_msg = _('{} should be set by one of {}.')
                    errors.extend(list(map(
                        lambda k: error_msg.format(k, validation.get('map')),
                        errors_key
                    )))

            # check by extend validator
            if validation.get('validator'):
                errors_msg = validate_by_extend_validator(
                    item, values, validation.get('validator'))
                if errors_msg:
                    errors.extend(errors_msg)

            # autofill data if empty
            if not errors and field.get('autofill'):
                autofill_data(item, values, field.get('autofill'))

            # convert mask data
            if not errors and field.get('mask'):
                convert_data_by_mask(item, values, field.get('mask'))

            if _key == 'authorIdInfo[0].idType':
                # convert scheme data
                convert_scheme_to_id(item, values, authors_prefix)
                # check external author identifier exist
                warning = validate_external_author_identifier(
                    item, values, existed_external_authors_id)
                if warning:
                    warnings.append(warning)
            if _key == "affiliationInfo[0].identifierInfo[0].affiliationIdType":
                convert_scheme_to_id(item, values, affilaition_id_prefix)

        if errors:
            item['errors'] = item['errors'] + errors \
                if item.get('errors') else errors
        if warnings:
            item['warnings'] = item['warnings'] + warnings \
                if item.get('warnings') else warnings

    return file_data


def unpackage_and_check_import_file_for_prefix(file_format, file_name, temp_file):
    """Unpackage and check format of import file for prefix.

    Args:
        file_format (str): File format.
        file_name (str): File uploaded name.
        temp_file (str): Temp file path.

    Returns:
        list: Tsv data.
    """
    from weko_search_ui.utils import handle_check_duplication_item_id
    header = []
    file_data = []
    current_app.logger.debug("temp_file:{}".format(temp_file))
    prefix_mapping_key = current_app.config['WEKO_AUTHORS_FILE_MAPPING_FOR_PREFIX']
    enc = getEncode(temp_file)
    with open(temp_file, 'r', newline="", encoding=enc) as file:
        if file_format == 'csv':
            file_reader = csv.reader(file, dialect='excel', delimiter=',')
        else:
            file_reader = csv.reader(file, dialect='excel', delimiter='\t')
        try:
            for num, data_row in enumerate(file_reader, start=1):
                if num ==2:
                    header = data_row
                    header[0] = header[0].replace('#', '', 1)
                    duplication_ids = \
                        handle_check_duplication_item_id(header)
                    if duplication_ids:
                        msg = _(
                            'The following metadata keys are duplicated.'
                            '<br/>{}')
                        raise Exception({
                            'error_msg':
                                msg.format('<br/>'.join(duplication_ids))
                        })
                    not_consistent_list = \
                        handle_check_consistence_with_mapping_for_prefix(
                            prefix_mapping_key, header)
                    if not_consistent_list:
                        msg = _('Specified item does not consistency '
                                'with DB item.<br/>{}')
                        raise Exception({
                            'error_msg': msg.format(
                                '<br/>'.join(not_consistent_list))
                        })
                elif num in [3, 4] and data_row[0].startswith('#'):
                    continue
                elif num > 4:
                    pass
                    tmp_data ={}
                    try:
                        for num, data in enumerate(data_row, start=0):
                            raw_header = header[num]
                            header_key = re.sub(r'\[\d+\]$', '', raw_header)
                            is_array = '[' in raw_header
                            if is_array:
                                if data:
                                    tmp_data.setdefault(header_key, []).append(data)
                            else:
                                tmp_data[header_key] = data
                    except Exception as ex:
                        current_app.logger.error(ex)
                        traceback.print_exc()
                        raise Exception({
                            'error_msg': _('Cannot read {} file correctly.').format(file_format.upper())
                        }) from ex
                    file_data.append(tmp_data)
        except UnicodeDecodeError as ex:
            ex.reason = _('{} could not be read. Make sure the file'
                          + ' format is {} and that the file is'
                          + ' UTF-8 encoded.').format(file_name, file_format.upper())
            raise
        except Exception as ex:
            raise
    return file_data


def handle_check_consistence_with_mapping_for_prefix(keys, header):
    """Check consistence with mapping.

    Args:
        keys (list): Mapping keys.
        header (list): Header row.

    Returns:
        list: Not consistent items.
    """
    not_consistent_list = []
    idx_pattern = re.compile(r'^(?P<base>[^\[\]]+)\[(?P<idx>\d+)\]$')

    for item in header:
        m = idx_pattern.match(item)
        if m:
            base = m.group('base')
            if f"{base}[0]" not in keys:
                not_consistent_list.append(item)
        else:
            if item not in keys:
                not_consistent_list.append(item)
    return not_consistent_list

def validate_import_data_for_prefix(file_data, target):
    """Validate data from tsv for prefix import.

    Checks:
        - Whether 'scheme' key is empty.
        - Whether 'name' key is empty.
        - Whether 'url' is not a valid URL.
        - Whether it is create, update, or delete.
          if scheme is existing, it is update,
          if scheme is not existing, it is create,
          if is_deleted is 'D', it is delete.
        - For id_prefix, whether 'scheme' is 'WEKO'.
        - Whether the same value appears twice 'scheme'.
        - For deletion, whether the specified scheme exists.
        - For deletion, whether the specified scheme is used.

    Args:
        file_data (list): Data from unpackage_and_check_import_file_for_prefix.
        target (str): 'id_prefix' or 'affiliation_id'.

    Returns:
        list: Validated data.
    """
    if target == "id_prefix":
        existed_prefix = WekoAuthors.get_scheme_of_id_prefix()
        used_scheme, id_type_and_scheme = WekoAuthors.get_used_scheme_of_id_prefix()
    elif target == "affiliation_id":
        existed_prefix = WekoAuthors.get_scheme_of_affiliaiton_id()
        used_scheme, id_type_and_scheme = WekoAuthors.get_used_scheme_of_affiliation_id()

    list_import_scheme = []

    for item in file_data:
        errors = []
        scheme = item.get('scheme', "")
        name = item.get('name', "")
        url = item.get('url', "")
        is_deleted = item.get('is_deleted')
        community_ids = item.get("community_ids", [])
        # Check if the 'scheme' key is empty
        if not scheme:
            errors.append(_("Scheme is required item."))
        # For id_prefix, check if 'scheme' is 'WEKO'
        if target == "id_prefix" and scheme == "WEKO":
            errors.append(_("The scheme WEKO cannot be used."))
        # Check if the 'name' key is empty
        if not name:
            errors.append(_("Name is required item."))
        # If url exists, check if url is not a valid URL
        if url and not url.startswith("http"):
            errors.append(_("URL is not URL format."))
        if is_deleted == "D":
            # For deletion, check if the specified scheme exists
            if scheme not in existed_prefix:
                errors.append(_("The specified scheme does not exist."))
            else:
                # For deletion, check if the specified scheme is used in author DB
                if scheme in used_scheme:
                    errors.append(_("The specified scheme is used in the author ID."))
                id = [k for k, v in id_type_and_scheme.items() if v == scheme]
                item['id'] = id[0]
                item['status'] = 'deleted'
        else:
            # If scheme exists in existed_prefix, it's update; otherwise, create
            if scheme in existed_prefix:
                id = [k for k, v in id_type_and_scheme.items() if v == scheme]
                item['id'] = id[0]
                item['status'] = 'update'
            else:
                item['status'] = 'new'

        # Check if the same value appears twice in 'scheme'
        if scheme in list_import_scheme:
            errors.append(_("The specified scheme is duplicated."))
        else:
            list_import_scheme.append(scheme)

        try:
            if item.get('status') == 'new':
                validate_community_ids(community_ids, is_create=True)
            elif item.get('status') == 'update':
                if target == "id_prefix":
                    old = AuthorsPrefixSettings.query.get(item.get('id'))
                elif target == "affiliation_id":
                    old = AuthorsAffiliationSettings.query.get(item.get('id'))
                old_community_ids = [c.id for c in old.communities]
                validate_community_ids(community_ids, old_ids=old_community_ids)
            elif item.get('status') == 'deleted':
                if target == "id_prefix":
                    check, message = check_delete_prefix(item.get('id'))
                elif target == "affiliation_id":
                    check, message = check_delete_affiliation(item.get('id'))

                if not check:
                    errors.append(message)
        except AuthorsValidationError as ex:
            errors.append(ex.description)

        if errors:
            item['errors'] = item['errors'] + errors \
                if item.get('errors') else errors
    return file_data

def band_check_file_for_user(max_page):
    """Merge split check results for user download.

    Args:
        max_page (int): Maximum page number.

    Returns:
        str: Path to the merged check file.
    """
    check_file_name = get_check_base_name()
    temp_folder_path = os.path.join(
        tempfile.gettempdir(),
        current_app.config.get("WEKO_AUTHORS_IMPORT_TMP_DIR")
    )
    check_file_download_name = "{}_{}.{}".format(
        "import_author_check_result",
        datetime.datetime.now().strftime("%Y%m%d%H%M"),
        "tsv"
    )
    check_file_path = os.path.join(temp_folder_path, check_file_download_name)
    try:
        with open(check_file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter='\t')
            writer.writerow(["No.", "Current WEKO ID", "New WEKO ID", "full_name", "MailAddress", "Check Result"])
            for i in range(1, max_page+1):
                part_check_file_name = f"{check_file_name}-part{i}"
                check_file_part_path = os.path.join(temp_folder_path, part_check_file_name)
                with open(check_file_part_path, "r", encoding="utf-8-sig") as check_part_file:
                    data = json.load(check_part_file)
                batch_size = current_app.config.get("WEKO_AUTHORS_IMPORT_BATCH_SIZE")
                for index, entry in enumerate(data, start=(i-1)*batch_size+1):
                    pk_id = entry.get("pk_id", "")
                    full_name_info =""
                    for author_name_info in entry.get("authorNameInfo", [{}]):
                        family_name = author_name_info.get("familyName", "")
                        first_name = author_name_info.get("firstName", "")
                        full_name = f"{family_name},{first_name}"
                        if len(full_name)!=1:
                            if len(full_name_info)==0:
                                full_name_info += full_name
                            else:
                                full_name_info += f"\n{full_name}"

                    current_weko_id = entry.get("current_weko_id", "")
                    new_weko_id = entry.get("weko_id", "")
                    email = ""
                    if entry.get("emailInfo", [{}]):
                        email_info = entry.get("emailInfo", [{}])[0]
                        email = email_info.get("email", "")
                    check_result = get_check_result(entry)

                    writer.writerow([index, current_weko_id, new_weko_id, full_name_info, email, check_result])
    except Exception as ex:
        raise

    update_cache_data(
        current_app.config["WEKO_AUTHORS_IMPORT_CACHE_BAND_CHECK_USER_FILE_PATH_KEY"],
        check_file_path,
        current_app.config["WEKO_AUTHORS_CACHE_TTL"]
        )
    return check_file_path

def get_check_result(entry):
    """Check status and errors in JSON and return a label.

    Args:
        entry (dict): Entry data.

    Returns:
        str: Check result label.
    """
    errors = entry.get("errors", [])
    status = entry.get("status", "")

    if errors:
        return "Error: " + " ".join(errors)
    else:
        if status == "new":
            return _('Register')
        elif status == "update":
            return _('Update')
        elif status == "deleted":
            return _('Delete')
        else:
            return status

def get_values_by_mapping(keys, data, parent_key=None):
    """Get values folow by mapping."""
    result = []
    current_key = keys[0].replace('[0]', '')
    current_key_with_parent = parent_key + '.' + \
        current_key if parent_key else current_key
    current_data = data.get(current_key)

    if isinstance(current_data, list):
        for idx, item in enumerate(current_data):
            result.extend(get_values_by_mapping(
                keys[1:],
                item,
                current_key_with_parent + '[{}]'.format(idx)
            ))
    elif isinstance(current_data, dict):
        result.extend(get_values_by_mapping(
            keys[1:], current_data, current_key_with_parent))
    else:
        reduce_keys = [
            (int(k.replace(']', '')) if k.endswith(']') else k)
            for k in current_key_with_parent.replace('[', '.').split('.')
        ]
        result = [{
            'key': current_key_with_parent,
            'reduce_keys': reduce_keys,
            'value': current_data
        }]
    return result


def autofill_data(item, values, autofill_data):
    """Autofill data if empty."""
    for value in values:
        if not value['value']:
            reduce_keys = value['reduce_keys']
            uplevel_data = reduce(getitem, reduce_keys[:-1], item)

            # check either required
            either_required = autofill_data.get('condition', {}) \
                .get('either_required', [])
            if either_required:
                check = [cond for cond in either_required
                         if uplevel_data.get(cond)]
                autofill_val = ''
                if check:
                    autofill_val = autofill_data.get('value', '')
                uplevel_data[reduce_keys[-1]] = autofill_val


def convert_data_by_mask(item, values, mask):
    """Convert data if have mask."""
    for value in values:
        if value['value']:
            import_value = [key for key, val in mask.items()
                            if val == value['value']]
            import_value = import_value[0] if import_value else None
            reduce_keys = value['reduce_keys']
            reduce(getitem, reduce_keys[:-1],
                   item)[reduce_keys[-1]] = import_value


def convert_scheme_to_id(item, values, authors_prefix):
    """Convert scheme to id."""
    for value in values:
        if value['value']:
            reduce_keys = value['reduce_keys']
            reduce(getitem, reduce_keys[:-1], item)[reduce_keys[-1]] = \
                str(authors_prefix.get(value['value'], None))


def set_record_status(file_format, list_existed_author_id, item, errors, warnings):
    """Set status to import data."""
    item['status'] = 'new'
    pk_id = item.get('pk_id')
    err_msg = _("Specified Author ID does not exist.")
    if item.get('is_deleted', '') == 'D':
        item['status'] = 'deleted'
        if not pk_id or list_existed_author_id.get(pk_id) is None:
            errors.append(err_msg)
        elif get_count_item_link(pk_id) > 0:
            errors.append(
                _('The author is linked to items and cannot be deleted.'))
    elif pk_id:
        if list_existed_author_id.get(pk_id) is not None:
            item['status'] = 'update'
            if not list_existed_author_id.get(pk_id):
                warnings.append(_('The specified author has been deleted.'
                                  ' Update author information with {} content'
                                  ', but author remains deleted as it is.').format(file_format))
        else:
            errors.append(err_msg)


def flatten_authors_mapping(mapping, parent_key=None):
    """Flatten author mappings."""
    result_all = []
    result_keys = []
    for item in mapping:
        current_key = parent_key + '[0].' + item['json_id'] \
            if parent_key else item['json_id']
        if item.get('child'):
            child_result_all, child_result_keys = flatten_authors_mapping(
                item['child'], current_key)
            result_all.extend(child_result_all)
            result_keys.extend(child_result_keys)
        else:
            result_all.append(dict(
                key=current_key,
                label=dict(
                    en=item['label_en'],
                    jp=item['label_jp']
                ),
                mask=item.get('mask', {}),
                validation=item.get('validation', {}),
                autofill=item.get('autofill', '')
            ))
            result_keys.append(current_key)
    return result_all, result_keys

def prepare_import_data(max_page_for_import_tab):
    """Prepare import data for display and import.

    Args:
        max_page_for_import_tab (int): Maximum page number for import tab.

    Returns:
        tuple (list, dict, int):
    """

    # Create check file path
    check_file_name = get_check_base_name()

    max_display = current_app.config.get("WEKO_AUTHORS_IMPORT_MAX_NUM_OF_DISPLAYS")
    temp_folder_path = os.path.join(
        tempfile.gettempdir(),
        current_app.config.get("WEKO_AUTHORS_IMPORT_TMP_DIR")
    )
    # Author data for front display
    authors = []
    # Variable for the total number of imports to be executed
    count = 0
    # Record the point where the maximum number of author data displayed on
    # the front is reached
    reached_point = {}
    for i in range(1, max_page_for_import_tab+1):
        part_check_file_name = f"{check_file_name}-part{i}"
        check_file_part_path = os.path.join(temp_folder_path, part_check_file_name)
        with open(check_file_part_path, "r", encoding="utf-8-sig") as check_part_file:
            data = json.load(check_part_file)
            # Count which data in json
            count_for_json = 0
            for item in data:
                check_result = False if item.get("errors", []) else True
                if check_result:
                    if count < max_display:
                        item.pop("warnings", None)
                        authors.append(item)
                    elif count == max_display:
                        reached_point["part_number"] = i
                        reached_point["count"] = count_for_json
                    else:
                        pass
                    count += 1
                count_for_json += 1
    return authors, reached_point, count

def import_author_to_system(
    author, status, weko_id, force_change_mode, request_info=None
):
    """Import author to DB and ES.

    Args:
        author (dict): Author metadata from tsv/csv.
        status (str): Import status.
        weko_id (str): WEKO ID.
        force_change_mode (bool): Force change mode.
        request_info (dict, optional): Request info for logging.

    Raises:
        Exception: If import fails.
    """
    from weko_logging.activity_logger import UserActivityLogger
    if author:
        try:
            check_weko_id = check_weko_id_is_exists(weko_id, author.get('pk_id'))

            author["is_deleted"] = True if author.get("is_deleted") else False
            if not author.get('authorIdInfo'):
                author["authorIdInfo"] = []

            if not author.get('emailInfo'):
                author['emailInfo'] = []

            for nameInfo in author.get('authorNameInfo', []):
                if "fullName" not in nameInfo:
                    fullName = nameInfo.get("familyName", "") + " " + nameInfo.get("firstName", "")
                    nameInfo["fullName"] = fullName

            if status == 'new':
                if check_weko_id:
                    current_app.logger.error("WekoID is duplicated")
                    raise Exception({'error_id': "WekoID is duplicated"})
                author["authorIdInfo"].insert(
                    0,
                    {
                        "idType": "1",
                        "authorId": weko_id,
                        "authorIdShowFlg": "true"
                    }
                )
                WekoAuthors.create(author)
            else:
                if status == 'deleted' \
                        and get_count_item_link(author['pk_id']) > 0:
                    raise Exception({'error_id': 'delete_author_link'})

                if check_weko_id:
                    current_app.logger.error("WekoID is duplicated")
                    raise Exception({'error_id': "WekoID is duplicated"})
                author["authorIdInfo"].insert(
                    0,
                    {
                        "idType": "1",
                        "authorId": weko_id,
                        "authorIdShowFlg": "true"
                    }
                )
                WekoAuthors.update(author['pk_id'], author, force_change_mode)
            db.session.commit()
            if status == "new":
                UserActivityLogger.info(operation="AUTHOR_CREATE", request_info=request_info)
            else:
                UserActivityLogger.info(
                    operation="AUTHOR_UPDATE",
                    target_key=author['pk_id'],
                    request_info=request_info,
                )
        except Exception as ex:
            db.session.rollback()
            current_app.logger.error(
                'Author id: %s import error.' % author['pk_id'])
            traceback.print_exc(file=sys.stdout)
            exec_info = sys.exc_info()
            tb_info = traceback.format_tb(exec_info[2])
            if status != "new" and author.get("pk_id"):
                UserActivityLogger.error(
                    operation="AUTHOR_UPDATE",
                    target_key=author['pk_id'],
                    request_info=request_info,
                    remarks=tb_info[0]
                )
            else:
                UserActivityLogger.error(
                    operation="AUTHOR_CREATE",
                    request_info=request_info,
                    remarks=tb_info[0]
                )
            raise

def create_result_file_for_user(json):
    """Create a result file for the user.
    The part displayed on the front end and the part managed on the back end
    are taken separately and merged.

    Args:
        json (list): Author data displayed at the front end.

    Returns:
        str: Path to the result file.
    """
    temp_folder_path = os.path.join(
        tempfile.gettempdir(),
        current_app.config.get("WEKO_AUTHORS_IMPORT_TMP_DIR")
    )
    result_over_max_file_path = current_cache.get(\
            current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_OVER_MAX_FILE_PATH_KEY"])
    result_file_name = "{}_{}.{}".format(
        "import_author_result",
        datetime.datetime.now().strftime("%Y%m%d%H%M"),
        "tsv"
    )
    result_file_path = os.path.join(temp_folder_path, result_file_name)

    if not result_over_max_file_path:
        return None
    try :
        with open(result_file_path, "w", encoding="utf-8") as result_file:
            writer = csv.writer(result_file, delimiter='\t')
            # write header
            writer.writerow([
                "No.", "Start Date", "End Date",
                "Previous WEKO ID", "New WEKO ID", "full_name", "Status"
            ])
            # write the json sent from the front desk.
            for data in json:
                number = data.get("No.", "")
                start_date = data.get("Start Date", "")
                end_date = data.get("End Date", "")
                prev_weko_id = data.get("Previous WEKO ID", "")
                new_weko_id = data.get("New WEKO ID", "")
                full_name = data.get("full_name", "")
                status = data.get("Status", "")
                writer.writerow([number, start_date, end_date, prev_weko_id, new_weko_id, full_name, status])
            count = len(json) + 1
            with open(result_over_max_file_path, "r", encoding="utf-8") as file:
                file_reader = csv.reader(file, dialect='excel', delimiter='\t')
                for row in file_reader:
                    row[0] = count
                    writer.writerow(row)
                    count += 1
    except Exception as e:
        current_app.logger.error(e)
        traceback.print_exc()
    update_cache_data(
        current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_FILE_PATH_KEY"],
        result_file_path,
        current_app.config["WEKO_AUTHORS_CACHE_TTL"]
        )
    return result_file_path

def get_count_item_link(pk_id):
    """Get count of item link of author.

    Args:
        pk_id (str): Author primary key ID.

    Returns:
        int: Count of linked items.
    """
    count = 0
    query_q = {
        "query": {"term": {"author_link.raw": pk_id}},
        "_source": ["control_number"]
    }
    result_itemCnt = RecordIndexer().client.search(
        index=current_app.config['SEARCH_UI_SEARCH_INDEX'],
        body=query_q
    )

    if result_itemCnt \
            and 'hits' in result_itemCnt \
            and 'total' in result_itemCnt['hits'] \
            and result_itemCnt['hits']['total'] > 0:
        count = result_itemCnt['hits']['total']
    return count


def count_authors():
    """Count authors from Elasticsearch.

    Returns:
        dict: Count result.
    """
    should = [
        {'bool': {'must': [{'term': {'is_deleted': {'value': 'false'}}}]}},
        {'bool': {'must_not': {'exists': {'field': 'is_deleted'}}}}
    ]
    match = [{'term': {'gather_flg': 0}}, {'bool': {'should': should}}]

    query = {'bool': {'must': match}}

    indexer = RecordIndexer()
    result = indexer.client.count(
        index=current_app.config['WEKO_AUTHORS_ES_INDEX_NAME'],
        doc_type=current_app.config['WEKO_AUTHORS_ES_DOC_TYPE'],
        body={'query': query}
    )

    return result

def import_id_prefix_to_system(id_prefix):
    """Import id_prefix from tsv/csv to DB.

    Args:
        id_prefix (dict): id_prefix metadata from tsv/csv.

    Raises:
        Exception: If import fails.
    """
    if id_prefix:
        retrys = current_app.config["WEKO_AUTHORS_BULK_IMPORT_MAX_RETRY"]
        interval = current_app.config["WEKO_AUTHORS_BULK_IMPORT_RETRY_INTERVAL"]
        try:
            status = id_prefix.pop('status')
            for attempt in range(retrys):
                try:
                    if not id_prefix.get('url'):
                        id_prefix['url'] = ""
                    check = get_author_prefix_obj(id_prefix['scheme'])
                    if status == 'new':
                        if check is None:
                            AuthorsPrefixSettings.create(**id_prefix)
                    elif status == 'update':
                        if check is None or check.id == id_prefix['id']:
                            AuthorsPrefixSettings.update(**id_prefix)
                    elif status == 'deleted':
                        used_external_id_prefix,_ = WekoAuthors.get_used_scheme_of_id_prefix()
                        if id_prefix["scheme"] in used_external_id_prefix:
                            raise Exception({'error_id': 'delete_author_link'})
                        else:
                            if check is None or check.id == id_prefix['id']:
                                AuthorsPrefixSettings.delete(id_prefix['id'])
                    else:
                        raise Exception({'error_id': 'status_error'})
                    db.session.commit()
                    break
                except SQLAlchemyError as ex:
                    traceback.print_exc(file=stdout)
                    handle_exception(ex, attempt, retrys, interval)
                except TimeoutError as ex:
                    traceback.print_exc(file=stdout)
                    handle_exception(ex, attempt, retrys, interval)
        except Exception as ex:
            db.session.rollback()
            current_app.logger.error(
                f'Id prefix: {id_prefix["scheme"]} import error.')
            traceback.print_exc(file=sys.stdout)
            raise

def import_affiliation_id_to_system(affiliation_id):
    """Import affiliation_id from tsv/csv to DB.

    Args:
        affiliation_id (dict): affiliation_id metadata from tsv/csv.

    Raises:
        Exception: If import fails.
    """
    if affiliation_id:
        retrys = current_app.config["WEKO_AUTHORS_BULK_IMPORT_MAX_RETRY"]
        interval = current_app.config["WEKO_AUTHORS_BULK_IMPORT_RETRY_INTERVAL"]
        try:
            status = affiliation_id.pop('status')
            for attempt in range(retrys):
                try:
                    if not affiliation_id.get('url'):
                        affiliation_id['url'] = ""
                    check = get_author_affiliation_obj(affiliation_id['scheme'])
                    if status == 'new':
                        if check is None:
                            AuthorsAffiliationSettings.create(**affiliation_id)
                    elif status == 'update':
                        if check is None or check.id == affiliation_id['id']:
                            AuthorsAffiliationSettings.update(**affiliation_id)
                    elif status == 'deleted':
                        used_external_id_prefix,_ = WekoAuthors.get_used_scheme_of_affiliation_id()
                        if affiliation_id["scheme"] in used_external_id_prefix:
                            raise Exception({'error_id': 'delete_author_link'})
                        else:
                            if check is None or check.id == affiliation_id['id']:
                                AuthorsAffiliationSettings.delete(affiliation_id['id'])
                    else:
                        raise Exception({'error_id': 'status_error'})
                    db.session.commit()
                    break
                except SQLAlchemyError as ex:
                    handle_exception(ex, attempt, retrys, interval)
                except TimeoutError as ex:
                    handle_exception(ex, attempt, retrys, interval)
        except Exception as ex:
            db.session.rollback()
            current_app.logger.error(
                f'Affiliation Id: {affiliation_id["scheme"]} import error.')
            traceback.print_exc(file=sys.stdout)
            raise

def update_data_for_weko_link(data, weko_link):
    """Update weko_link based on authors table and update data if different.

    Args:
        data (dict): Metadata, especially from workflowactivity temp_data column.
        weko_link (dict): weko_link mapping.
    """
    old_weko_link = weko_link
    weko_link = copy.deepcopy(old_weko_link)
    # Update weko_link with new values.
    for pk_id in weko_link.keys():
        author = Authors.get_author_by_id(pk_id)
        if author:
            # Get weko_id.
            author_id_info = author["authorIdInfo"]
            for i in author_id_info:
                # If idType is 1, get weko_id and update weko_link.
                if i.get('idType') == '1':
                    weko_link[pk_id] = i.get('authorId')
                    break
    if weko_link == old_weko_link:
        # If weko_link has not changed, do nothing.
        return
    # If weko_link has changed, update metadata.
    for x_key, x_value in data.items():
        if not isinstance(x_value, list):
            continue
        for y_index, y in enumerate(x_value, start=0):
            if not isinstance(y, dict):
                continue
            for y_key, y_value in y.items():
                if not y_key == "nameIdentifiers":
                    continue
                for z_index, z in enumerate(y_value, start=0):
                    if (
                        z.get("nameIdentifierScheme","") != "WEKO"
                        or z.get("nameIdentifier") not in old_weko_link.values()
                    ):
                        continue
                    # Get pk_id whose value matches weko_id from weko_link.
                    pk_id = [
                        k for k, v in old_weko_link.items()
                        if v == z.get("nameIdentifier")
                    ][0]
                    z["nameIdentifier"] = weko_link.get(pk_id)

def get_check_base_name():
    """Get base name for check file.

    Returns:
        str: Base file name for check.
    """
    temp_file_path = current_cache.get(\
        current_app.config["WEKO_AUTHORS_IMPORT_CACHE_USER_TSV_FILE_KEY"])
    base_file_name = os.path.splitext(os.path.basename(temp_file_path))[0]
    return f"{base_file_name}-check"

from invenio_communities.models import Community

def validate_community_ids(new_ids, old_ids=None, is_create=False):
    """Validate community IDs.

    Args:
        new_ids (iterable): The new community IDs.
        old_ids (iterable): The old community IDs.
        is_create (bool): Flag indicating if this is a create operation.
    """
    new_ids = set(new_ids)
    old_ids = set(old_ids) if old_ids else set()

    # 形式チェック
    for cid in new_ids:
        if not re.match(r'^[a-zA-Z0-9_-]+$', cid):
            raise AuthorsValidationError(description=f"Invalid community ID format: {cid}")

    # 存在チェック
    existing_ids = {c.id for c in Community.query.filter(Community.id.in_(new_ids)).all()}
    missing_ids = new_ids - existing_ids
    if missing_ids:
        raise AuthorsValidationError(description=f"Community ID(s) {', '.join(missing_ids)} does not exist.")

    # 権限チェック
    managed_communities, is_super = get_managed_community(current_user)
    managed_ids = {c.id for c in managed_communities}

    if is_super:
        return

    if is_create:
        unauthorized = new_ids - managed_ids
        if unauthorized:
            raise AuthorsPermissionError(description=f'You do not have management permissions for the community "{", ".join(unauthorized)}".')
        if not (new_ids & managed_ids):
            raise AuthorsValidationError(description='You must assign at least one managed community.')

    else:
        if not (old_ids & managed_ids):
            raise AuthorsPermissionError(description='You do not manage the existing record.')
        if not (new_ids & managed_ids):
            raise AuthorsPermissionError(description='You must include at least one community ID that you manage.')

        added = new_ids - old_ids
        removed = old_ids - new_ids

        unauthorized_add = added - managed_ids
        if unauthorized_add:
            raise AuthorsPermissionError(
                description=f'You do not have management permissions for the community "{", ".join(unauthorized_add)}".'
            )

        unauthorized_remove = removed - managed_ids
        if unauthorized_remove:
            raise AuthorsPermissionError(
                description=f'You do not have management permissions for the community "{", ".join(unauthorized_remove)}".'
            )

    return


def get_managed_community(user):
    """Get communities managed by the user.

    Args:
        user (User): The user object.

    Returns:
        list: List of communities managed by the user.
    """
    managed_communities = []
    if user.is_authenticated:
        try:
            is_super = any(role.name in current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER'] for role in user.roles)
            if is_super:
                managed_communities = Community.query.all()
            else:
                managed_communities = Community.get_repositories_by_user(user)
        except Exception as e:
            current_app.logger.error(f"Error fetching managed communities: {e}")
            traceback.print_exc()
    return managed_communities, is_super


def check_delete_entity(entity, entity_type, id):
    entity_instance = entity.query.get(id)
    if not entity_instance:
        return False, f'{entity_type} not found.'
    communities = entity_instance.communities

    # 現在のユーザーが管理しているコミュニティを取得
    managed_communities, is_super = get_managed_community(current_user)
    managed_community_ids = {comm.id for comm in managed_communities}

    if is_super:
        return True, None
    elif communities == []:
        # entityに関連付けられているコミュニティがない場合はリポジトリ管理者以上のみ削除可能
        return False, f'You do not have permissions for this {entity_type}.'
    else:
        # entityに関連付けられているすべてのコミュニティの管理者であれば削除可能
        unauthorized_communities = [com.id for com in communities
                                    if com.id not in managed_community_ids]
        if not unauthorized_communities:
            return True, None
        return False, f'You do not have management permissions for the community "{unauthorized_communities}".'


def check_delete_author(id):
    return check_delete_entity(Authors, 'Author', id)

def check_delete_prefix(id):
    return check_delete_entity(AuthorsPrefixSettings, 'Prefix', id)

def check_delete_affiliation(id):
    return check_delete_entity(AuthorsAffiliationSettings, 'Affiliation', id)