# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""WEKO3 module docstring."""
import time
from datetime import datetime

from celery import shared_task
from weko_admin.models import SessionLifetime

from .config import WEKO_ADMIN_LIFETIME_DEFAULT
from .utils import import_items_to_system, remove_temp_dir


@shared_task
def import_item(item):
    """Import Item ."""
    start_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result = import_items_to_system(item) or dict()
    result['start_date'] = start_date
    return result


@shared_task
def remove_temp_dir_task(path):
    """Import Item ."""
    try:
        db_lifetime = SessionLifetime.get_validtime()
        if db_lifetime is None:
            time.sleep(WEKO_ADMIN_LIFETIME_DEFAULT)
            remove_temp_dir(path)
        else:
            time.sleep(db_lifetime.lifetime * 60)
            remove_temp_dir(path)

    except BaseException:
        pass
