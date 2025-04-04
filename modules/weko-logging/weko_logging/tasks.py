# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Tasks for the WEKO logging module."""

from datetime import datetime
from celery import shared_task
from flask import current_app

from .utils import UserActivityLogUtils

@shared_task(ignore_results=False)
def export_all_user_activity_logs():
    """Export all user activity logs task.

    :raises: Exception if failed to export logs.
    """
    try:
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        UserActivityLogUtils.set_export_status(start_time=start_time)
        zip_file_uri = UserActivityLogUtils.package_export_log()
        if zip_file_uri:
            end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            UserActivityLogUtils.save_export_url(start_time, end_time, zip_file_uri)
        return zip_file_uri
    except Exception as ex:
        current_app.logger.error(ex)
        raise

@shared_task(ignore_results=True)
def delete_log():
    """Delete logs task."""
    with current_app.app_context():
        delete_log()