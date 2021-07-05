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

from celery import shared_task
from flask import current_app

from .utils import delete_export_status, export_authors, save_export_url, \
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

        delete_export_status()

        return file_uri
    except Exception as ex:
        current_app.logger.error(ex)
