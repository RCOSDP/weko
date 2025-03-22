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

"""WEKO3 authors tasks."""
from datetime import datetime

from celery import shared_task, states
from celery.result import GroupResult
from celery.task.control import inspect
from flask import current_app
from weko_workflow.utils import delete_cache_data, get_cache_data

from weko_authors.config import WEKO_AUTHORS_IMPORT_CACHE_KEY

from .utils import export_authors, import_author_to_system, save_export_url, \
    set_export_status


@shared_task
def export_all():
    """Export all creator."""
    try:
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        set_export_status(start_time=start_time)
        file_uri = export_authors()
        if file_uri:
            end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_export_url(start_time, end_time, file_uri)

        return file_uri
    except Exception as ex:
        current_app.logger.error(ex)


@shared_task
def import_author(author):
    """Import Author."""
    result = {'start_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    try:
        import_author_to_system(author)
        result['status'] = states.SUCCESS
    except Exception as ex:
        current_app.logger.error(ex)
        result['status'] = states.FAILURE
        if ex.args and len(ex.args) and isinstance(ex.args[0], dict) \
                and ex.args[0].get('error_id'):
            error_msg = ex.args[0].get('error_id')
            result['error_id'] = error_msg

    result['end_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return result


def check_is_import_available(group_task_id=None):
    """Is import available."""
    result = {
        'is_available': True
    }

    if not inspect(timeout=current_app.config.get("CELERY_GET_STATUS_TIMEOUT", 3.0)).ping():
        result['is_available'] = False
        result['celery_not_run'] = True
    else:
        cache_data = get_cache_data(WEKO_AUTHORS_IMPORT_CACHE_KEY)
        if cache_data:
            task = GroupResult.restore(cache_data.get('group_task_id'))
            if task:
                if task.successful() or task.failed():
                    delete_cache_data(WEKO_AUTHORS_IMPORT_CACHE_KEY)
                else:
                    result['is_available'] = False
                    if group_task_id and group_task_id == task.id:
                        result['continue_data'] = cache_data
            else:
                delete_cache_data(WEKO_AUTHORS_IMPORT_CACHE_KEY)

    return result
