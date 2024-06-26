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
import shutil
from datetime import datetime, timedelta

from celery import shared_task
from celery.result import AsyncResult
from celery.task.control import inspect
from flask import current_app
from weko_admin.api import TempDirInfo
from weko_admin.utils import get_redis_cache
from weko_redis.redis import RedisConnection
from invenio_db import db

from .utils import (
    check_import_items,
    delete_exported,
    export_all,
    get_lifetime,
    import_items_to_system,
)


@shared_task
def check_import_items_task(file_path, is_change_identifier: bool, host_url,
                            lang="en", all_index_permission=True, can_edit_indexes=[]):
    """Check import items."""
    result = {"start_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    with current_app.test_request_context(
        host_url, headers=[("Accept-Language", lang)]
    ):
        check_result = check_import_items(file_path, is_change_identifier,
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


@shared_task
def remove_temp_dir_task(path):
    """Import Item ."""
    shutil.rmtree(path)
    TempDirInfo().delete(path)


@shared_task
def delete_task_id_cache(task_id, cache_key):
    """delete admin_cache_KEY_EXPORT_ALL_{user_id} from redis"""
    if get_redis_cache(cache_key) == task_id:
        state = AsyncResult(task_id).state
        if state == "REVOKED":
            redis_connection = RedisConnection()
            datastore = redis_connection.connection(db=current_app.config['CACHE_REDIS_DB'], kv = True)
            datastore.delete(cache_key)

@shared_task
def export_all_task(root_url, user_id, data, timezone):
    """Export all items."""
    from weko_admin.utils import reset_redis_cache

    _task_config = current_app.config["WEKO_SEARCH_UI_BULK_EXPORT_URI"]
    _expired_time = current_app.config["WEKO_SEARCH_UI_BULK_EXPORT_EXPIRED_TIME"]
    _cache_key = current_app.config["WEKO_ADMIN_CACHE_PREFIX"].format(
        name=_task_config,
        user_id=user_id
    )
    _task_key_config = current_app.config["WEKO_SEARCH_UI_BULK_EXPORT_TASK"]
    _task_key = current_app.config["WEKO_ADMIN_CACHE_PREFIX"].format(
        name=_task_key_config,
        user_id=user_id
    )

    uri = export_all(root_url, user_id, data, timezone)
    reset_redis_cache(_cache_key, uri)
    delete_exported_task.apply_async(
        args=(
            uri,
            _cache_key,
            _task_key
        ),
        countdown=int(_expired_time) * 60,
    )


@shared_task
def delete_exported_task(uri, cache_key, task_key):
    """Delete expired exported file."""
    redis_connection = RedisConnection()
    datastore = redis_connection.connection(db=current_app.config['CACHE_REDIS_DB'], kv = True)
    if datastore.redis.exists(cache_key):
        datastore.delete(task_key)
    try:
        delete_exported(uri, cache_key)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)


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
