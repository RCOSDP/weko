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

"""WEKO3 module docstring."""
import os
import gc
import json
import os
import pickle
import shutil
from datetime import datetime, timedelta
import sys
import traceback

from celery import shared_task
from celery.result import AsyncResult
from celery.task.control import inspect
from flask import current_app, request
from flask_babelex import gettext as _

from weko_admin.api import TempDirInfo
from weko_admin.utils import get_redis_cache, reset_redis_cache
from weko_redis.redis import RedisConnection
from invenio_db import db

from .utils import (
    check_jsonld_import_items,
    check_tsv_import_items,
    delete_exported,
    export_all,
    write_files,
    get_lifetime,
    import_items_to_system,
)


@shared_task
def check_import_items_task(
    file_path, is_change_identifier: bool, host_url,
    lang="en", all_index_permission=True, can_edit_indexes=[]
):
    """Check import items."""
    result = {"start_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    with current_app.test_request_context(
        host_url, headers=[("Accept-Language", lang)]
    ):
        check_result = check_tsv_import_items(file_path, is_change_identifier,
                                        all_index_permission=all_index_permission,
                                        can_edit_indexes=can_edit_indexes)
    # remove zip file
    shutil.rmtree("/".join(file_path.split("/")[:-1]))
    data_path = check_result.get("data_path", "")
    if check_result.get("error"):
        remove_temp_dir_task.apply_async((data_path,))
        result["error"] = check_result.get("error")
    else:
        list_record = check_result.get("list_record", [])
        num_record_err = len([i for i in list_record if i.get("errors")])
        if len(list_record) == num_record_err:
            remove_temp_dir_task.apply_async((data_path,))
        else:
            expire = datetime.now() + timedelta(seconds=get_lifetime())
            TempDirInfo().set(
                data_path, {"expire": expire.strftime("%Y-%m-%d %H:%M:%S")}
            )
        result["data_path"] = data_path
        result["list_record"] = list_record

    result["end_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return result


@shared_task
def check_rocrate_import_items_task(
    file_path, is_change_identifier: bool, host_url,
    packaging, mapping_id, lang="en", can_edit_indexes=[]
):
    """Check RO-Crate import items.
    Check the contents of an RO-Crate file and processes its metadata.

    Args:
        file_path (str): File path.
        is_change_identifier (bool): Change identifier or not.
        host_url (str): Host URL.
        packaging (str): Packaging.
        mapping_id (int): Mapping ID.
        lang (str): Language code(default is "en").
        can_edit_indexes (list): List of editable indexes.
    Returns:
        dict: Check Result.
            - start_date (str): Start date of the check.
            - end_date (str): End date of the check.
            - data_path (str): Path to the data.
            - list_record (list): List of records with their metadata.
            - error (str): Error message if any error occurs.
    """
    result = {"start_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    with current_app.test_request_context(
        host_url, headers=[("Accept-Language", lang)]
    ):
        check_result = check_jsonld_import_items(
            file_path, packaging, mapping_id,
            validate_bagit=False,
            is_change_identifier=is_change_identifier,
            can_edit_indexes=can_edit_indexes
        )
        list_record = check_result.get("list_record", [])
        check_flag_metadata_replace(list_record)
        check_import_item_splited(check_result)

    # remove zip file
    shutil.rmtree("/".join(file_path.split("/")[:-1]))
    data_path = check_result.get("data_path", "")
    if check_result.get("error"):
        remove_temp_dir_task.apply_async((data_path,))
        result["error"] = check_result.get("error")
    else:
        num_record_err = len([i for i in list_record if i.get("errors")])
        if len(list_record) == num_record_err:
            remove_temp_dir_task.apply_async((data_path,))
        else:
            expire = datetime.now() + timedelta(seconds=get_lifetime())
            TempDirInfo().set(
                data_path, {"expire": expire.strftime("%Y-%m-%d %H:%M:%S")}
            )
        result["data_path"] = data_path
        result["list_record"] = list_record

    result["end_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return result


@shared_task(ignore_results=False)
def import_item(item, request_info):
    """Import Item."""
    try:
        start_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result = import_items_to_system(item, request_info) or dict()
        result["start_date"] = start_date
        return result
    except Exception as ex:
        current_app.logger.error(ex)
        traceback.print_exc(file=sys.stdout)


@shared_task
def remove_temp_dir_task(path):
    """Import Item ."""
    shutil.rmtree(path)
    TempDirInfo().delete(path)


@shared_task
def delete_task_id_cache_on_revoke(task_id, cache_key):
    """delete admin_cache_KEY_EXPORT_ALL_{user_id} from redis

    Delete the export task ID cache from Redis if the task has been revoked.

    This task checks if the given cache key in Redis matches the provided task ID.
    If the task state is "REVOKED", it deletes the cache key from Redis to clean up
    any remaining task information.

    Args:
        task_id (str): The Celery task ID to check.
        cache_key (str): The Redis cache key associated with the export task.

    Returns:
        None
    """
    if get_redis_cache(cache_key) == task_id:
        state = AsyncResult(task_id).state
        if state == "REVOKED":
            redis_connection = RedisConnection()
            datastore = redis_connection.connection(db=current_app.config['CACHE_REDIS_DB'], kv = True)
            datastore.delete(cache_key)

@shared_task
def export_all_task(root_url, user_id, data, start_time):
    """
    Celery task to export all items for a user.

    This task calls the export_all function to export all items for the specified user,
    using the provided root URL, data, and start time.
    Args:
        root_url (str): The root URL for the export process.
        user_id (str): The ID of the user performing the export.
        data (dict): The data to be exported.
        start_time (str): The start time of the export process.

    Returns:
        None
    """
    export_all(root_url, user_id, data, start_time)

@shared_task(bind=True)
def write_files_task(self, export_path, pickle_file_name , user_id):
    """
    Celery task to process export data from a pickle file and write files.
    This task reads export data from the specified pickle file, updates the export
    status in Redis cache, and calls the write_files function to perform the actual
    file writing process. The task also manages export progress and error states
    in Redis, and removes the pickle file after processing.

    Args:
        export_path (str): The directory path where export files will be written.
        pickle_file_name (str): The name of the pickle file containing export data.
        user_id (str): The ID of the user performing the export.

    Raises:
        Any exception during processing will be logged, and error status will be
        updated in Redis cache.
    """
    try:
        _msg_config = current_app.config["WEKO_SEARCH_UI_BULK_EXPORT_MSG"]
        _msg_key = current_app.config["WEKO_ADMIN_CACHE_PREFIX"].format(
            name=_msg_config,
            user_id=user_id
        )
        _file_create_config = \
            current_app.config["WEKO_SEARCH_UI_BULK_EXPORT_FILE_CREATE_RUN_MSG"]
        _file_create_key = current_app.config["WEKO_ADMIN_CACHE_PREFIX"].format(
            name=_file_create_config,
            user_id=user_id
        )

        # update task_id in redis
        _task_id_config = \
            current_app.config["WEKO_SEARCH_UI_BULK_EXPORT_TASK"]
        _task_id_key = current_app.config["WEKO_ADMIN_CACHE_PREFIX"].format(
            name=_task_id_config,
            user_id=user_id
        )
        reset_redis_cache(_task_id_key, str(self.request.id))

        item_type_id = pickle_file_name.split(".")[1]
        part = pickle_file_name.split(".")[2]
        json_data = json.loads(get_redis_cache(_file_create_key))
        pickle_path = export_path + '/' + pickle_file_name
        def _update_redis_status(json_data, file_name, status,item_type_id):
            """Update status in redis cache.
            Args:
                json_data (dict): The cache to be updated
                file_name (str): file name to be updated
                status (str): Change to this status
                item_type_id (str): Target item type ID
            """
            part_name = os.path.splitext(file_name)[1]
            part_index = part_name.find('part')
            part_number = part_name[part_index + 4:] if part_index != -1 else 1
            json_data['write_file_status'][item_type_id + '.' + str(part_number)] = status
            reset_redis_cache(_file_create_key, json.dumps(json_data))
            del part_name, part_index, part_number

        if not json_data['cancel_flg']:
            with open(pickle_path, 'rb') as f:
                import_datas = pickle.load(f)
            _update_redis_status(json_data, import_datas['name'], 'started',import_datas['item_type_id'])
            with open(pickle_path, 'rb') as f:
                import_datas = pickle.load(f)

            result = write_files(import_datas, export_path, user_id, 0)
            json_data = json.loads(get_redis_cache(_file_create_key))
            if result:
                _update_redis_status(json_data, import_datas['name'], 'finished',import_datas['item_type_id'])
            else:
                reset_redis_cache(_msg_key, "Export failed.")
                json_data['cancel_flg'] = True
                _update_redis_status(json_data, import_datas['name'], 'error',import_datas['item_type_id'])
        else:
            _update_redis_status(json_data, f"{item_type_id}.{part}", 'canceled',item_type_id)
        os.remove(pickle_path)
    except Exception as e:
        import traceback
        current_app.logger.error(traceback.format_exc())
        reset_redis_cache(_msg_key, "Export failed.")
        json_data['cancel_flg'] = True
        _update_redis_status(json_data, f"{item_type_id}.{part}", 'error',item_type_id)
        os.remove(pickle_path)

def is_import_running():
    """Check import is running."""
    if not check_celery_is_run():
        return "celery_not_run"

    _timeout = current_app.config.get("CELERY_GET_STATUS_TIMEOUT", 3.0)
    active = inspect(timeout=_timeout).active()
    for worker in active:
        for task in active[worker]:
            if task["name"] == "weko_search_ui.tasks.import_item":
                return "is_import_running"

    reserved = inspect(timeout=_timeout).reserved()
    for worker in reserved:
        for task in reserved[worker]:
            if task["name"] == "weko_search_ui.tasks.import_item":
                return "is_import_running"


def check_celery_is_run():
    """Check celery is running, or not."""
    if not inspect(timeout=current_app.config.get("CELERY_GET_STATUS_TIMEOUT", 3.0)).ping():
        return False
    else:
        return True

def check_session_lifetime():
    """Check session lifetime."""
    lifetime = get_lifetime()
    return True if lifetime >= 86400 else False


def check_flag_metadata_replace(list_record):
    """Check metadata_replace flag.

    `wk:metadataReplace` cannot be used in the import item.

    Args:
        list_record (list): List of record.
    """
    error = _("`wk:metadata_replace` flag cannot be used in RO-Crate Import.")
    for item in list_record:
        if item.get("metadata_replace"):
            item["errors"] = (
                item["errors"] + [error] if item.get("errors") else [error]
            )

def check_import_item_splited(check_result):
    """Check import item splited.

    `wk:isSplited` cannot be used in the import item.

    Args:
        list_record (list): List of record.
    """
    error = _("`wk:isSplited` flag cannot be used in RO-Crate Import.")
    list_record = check_result.get("list_record", [])
    if len(list_record) > 1:
        current_app.logger.error(
            "The number of import items is more than 2. "
            "`wk:isSplited` flag cannot be used."
        )
        check_result["error"] = error
