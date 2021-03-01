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

from weko_workflow.utils import delete_cache_item_lock_info
from .utils import import_items_to_system, remove_temp_dir


@shared_task
def import_item(item, url_root):
    """Import Item ."""
    start_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result = import_items_to_system(item, url_root) or dict()
    result['start_date'] = start_date
    item_id = item.get('id')
    delete_cache_item_lock_info(
        int(item_id) if item.get('status') != 'new' else None)
    return result


@shared_task
def remove_temp_dir_task(path):
    """Import Item ."""
    remove_temp_dir(path)
