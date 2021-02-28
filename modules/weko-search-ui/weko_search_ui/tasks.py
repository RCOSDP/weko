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
from flask import current_app

from .utils import Exporter, export_all_admin, import_items_to_system, \
    remove_temp_dir


@shared_task
def import_item(item, url_root):
    """Import Item ."""
    start_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result = import_items_to_system(item, url_root) or dict()
    result['start_date'] = start_date
    return result


@shared_task
def remove_temp_dir_task(path):
    """Import Item ."""
    remove_temp_dir(path)


@shared_task
def export_all_items(root_url):
    """Export all items."""
    from weko_admin.utils import reset_redis_cache
    _task_config = current_app.config['WEKO_SEARCH_UI_BULK_EXPORT_URI']
    _cache_key = current_app.config['WEKO_ADMIN_CACHE_PREFIX'].\
        format(name=_task_config)

    uri = export_all_admin(root_url)
    current_app.logger.error('*' * 60)
    reset_redis_cache(_cache_key,
                      uri)
    current_app.logger.error(uri)


@shared_task
def delete_export_all():
    """Delete expried exported file."""
    Exporter().delete_file_instance()
