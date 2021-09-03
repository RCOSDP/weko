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
from datetime import datetime

from celery import shared_task
from celery.task.control import inspect
from flask import current_app

from .utils import delete_exported, export_all, import_items_to_system, \
    remove_temp_dir


@shared_task
def import_item(item, request_info):
    """Import Item ."""
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
    remove_temp_dir(path)


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
    if not inspect().ping():
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
