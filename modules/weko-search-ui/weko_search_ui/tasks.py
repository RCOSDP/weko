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
from celery.task.control import inspect
from flask import current_app
from weko_admin.api import TempDirInfo

from .utils import check_import_items, delete_exported, export_all, \
    get_lifetime, import_items_to_system


@shared_task
def check_import_items_task(file_path, is_change_identifier: bool,
                            host_url, lang='en'):
    """Check import items."""
    result = {'start_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    with current_app.test_request_context(host_url,
                                          headers=[('Accept-Language', lang)]):
        check_result = check_import_items(file_path, is_change_identifier)
    # remove zip file
    shutil.rmtree('/'.join(file_path.split('/')[:-1]))
    data_path = check_result.get('data_path', '')
    if check_result.get('error'):
        remove_temp_dir_task.apply_async((data_path,))
        result['error'] = check_result.get('error')
    else:
        list_record = check_result.get('list_record', [])
        num_record_err = len(
            [i for i in list_record if i.get('errors')])
        if len(list_record) == num_record_err:
            remove_temp_dir_task.apply_async((data_path,))
        else:
            expire = datetime.now() + \
                timedelta(seconds=get_lifetime())
            TempDirInfo().set(
                data_path,
                {'expire': expire.strftime('%Y-%m-%d %H:%M:%S')}
            )
        result['data_path'] = data_path
        result['list_record'] = list_record

    result['end_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return result


@shared_task(ignore_results=False)
def import_item(item, request_info):
    """Import Item."""
    try:
        start_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result = import_items_to_system(item, request_info) or dict()
        result['start_date'] = start_date
        return result
    except Exception as ex:
        current_app.logger.error(ex)


@shared_task
def remove_temp_dir_task(path):
    """Import Item ."""
    shutil.rmtree(path)
    TempDirInfo().delete(path)


@shared_task
def export_all_task(root_url):
    """Export all items."""
    from weko_admin.utils import reset_redis_cache
    _task_config = current_app.config['WEKO_SEARCH_UI_BULK_EXPORT_URI']
    _expired_time = current_app.\
        config['WEKO_SEARCH_UI_BULK_EXPORT_EXPIRED_TIME']
    _cache_key = current_app.config['WEKO_ADMIN_CACHE_PREFIX'].\
        format(name=_task_config)

    uri = export_all(root_url)
    reset_redis_cache(_cache_key, uri)
    delete_exported_task.apply_async(
        args=(uri, _cache_key,), countdown=int(_expired_time) * 60)


@shared_task
def delete_exported_task(uri, cache_key):
    """Delete expired exported file."""
    delete_exported(uri, cache_key)


def is_import_running():
    """Check import is running."""
    if not check_celery_is_run():
        return 'celery_not_run'

    active = inspect().active()
    for worker in active:
        for task in active[worker]:
            if task['name'] == 'weko_search_ui.tasks.import_item':
                return 'is_import_running'

    reserved = inspect().reserved()
    for worker in reserved:
        for task in reserved[worker]:
            if task['name'] == 'weko_search_ui.tasks.import_item':
                return 'is_import_running'


def check_celery_is_run():
    """Check celery is running, or not."""
    if not inspect().ping():
        return False
    else:
        return True