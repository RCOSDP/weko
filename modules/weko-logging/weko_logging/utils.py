# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""User activity log utilities."""

import csv
import json
import traceback
import zipfile
from celery.result import AsyncResult
from celery.task.control import revoke
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from flask import current_app
from io import BufferedReader, BytesIO, StringIO
from sys import stdout

from invenio_db import db
from invenio_files_rest.models import FileInstance, Location
from weko_admin.utils import get_redis_cache, reset_redis_cache
from weko_logging.models import UserActivityLog


class UserActivityLogUtils:
    """Utility for user activity (audit) log."""

    USER_ACTIVITY_LOG_EXPORT_CACHE_STATUS_KEY = "weko_user_activity_log_export_status"

    USER_ACTIVITY_LOG_EXPORT_CACHE_URL_KEY = "weko_user_activity_log_export_url"

    @classmethod
    def package_export_log(cls):
        """Get log data as tsv format.

        Returns:
            str: File uri.
        
        Raises:
            Exception: if failed to write log data to tsv.
        """
        file_uri = None
        try:
            log_records = UserActivityLog.query.all()
            log_data = [ log_record.to_dict() for log_record in log_records ]
            zip_stream = BytesIO()
            basename = datetime.now().strftime("user_activity_logs_%y%m%d%H%M%S")
            output_files = [{
                "filename": f"{basename}.tsv",
                "data": log_data
            }]

            log_zip = zipfile.ZipFile(zip_stream, "w")
            for file in output_files:
                log_zip.writestr(
                    file["filename"],
                    cls._write_log_to_tsv(file["data"])
                )

            # set bufferd reader
            reader = BufferedReader(BytesIO(zip_stream.getvalue()))

            # save data into location
            cache_url = cls.get_export_url()
            if not cache_url:
                file = FileInstance.create()
                file.set_contents(
                    reader,
                    default_location=Location.get_default().uri
                )
            else:
                file = FileInstance.get_by_uri(cache_url['file_uri'])
                if not file:
                    raise Exception("FileInstance record not found.")
                file.writable = True
                file.set_contents(reader)

            log_zip.close()
            file_uri = file.uri if file else None
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to write log data to tsv: {e}")
            traceback.print_exc(file=stdout)
            raise e

        return file_uri

    @classmethod
    def cancel_export_log(cls):
        """Cancel export log.

        Returns:
            bool: True if success, False if failed.
        """

        try:
            export_status = cls.get_export_task_status()
            if export_status:
                task_id = export_status.get("task_id")
                revoke(task_id, terminate=True)
                state = AsyncResult(task_id).state
                if state == "REVOKED":
                    cls.clear_export_status()
                    return True
                else:
                    return False
            return True
        except Exception as ex:
            current_app.logger.error(ex)
            return False

    @classmethod
    def delete_log(cls):
        """Delete logs.

        Raises:
            Exception: if failed to delete logs.
        """
        # get config from current_app
        config = current_app.config.get("WEKO_LOGGING_USER_ACTIVITY_SETTING")
        if config is None:
            raise Exception("WEKO_LOGGING_USER_ACTIVITY_SETTING is not set.")

        when = config.get("delete").get("when")
        interval = config.get("delete").get("interval")
        if when is None or interval is None:
            raise Exception("WEKO_LOGGING_USER_ACTIVITY_SETTING.delete.when or interval is not set.")

        # set date according to when and interval
        deletion_date_to = None
        if when == "days":
            deletion_date_to = datetime.now() - timedelta(days=interval)
        elif when == "weeks":
            deletion_date_to = datetime.now() - timedelta(weeks=interval)
        elif when == "months":
            deletion_date_to = datetime.now() - relativedelta(months=interval)
        elif when == "years":
            deletion_date_to = datetime.now() - relativedelta(years=interval)
        else:
            raise Exception("WEKO_LOGGING_USER_ACTIVITY_SETTING.delete.when is invalid.")

        UserActivityLog.query.filter(UserActivityLog.date < deletion_date_to).delete()
        db.session.commit()

    @classmethod
    def get_export_task_status(cls):
        """Get export status from cache.

        Returns:
            dict: The export status.
        """
        json_data = get_redis_cache(cls.USER_ACTIVITY_LOG_EXPORT_CACHE_STATUS_KEY)
        return json.loads(json_data) if json_data else {}

    @classmethod
    def set_export_status(cls, start_time=None, task_id=None):
        """Set export status into cache.

        Args:
            start_time (datetime): The start time.
            task_id (str): The task id.

        Returns:
            dict: The export status.
        """
        cache_data = cls.get_export_task_status() or dict()
        if start_time:
            cache_data['start_time'] = start_time
        if task_id:
            cache_data['task_id'] = task_id

        reset_redis_cache(
            cls.USER_ACTIVITY_LOG_EXPORT_CACHE_STATUS_KEY,
            json.dumps(cache_data)
        )
        return cache_data

    @classmethod
    def get_export_url(cls):
        """Get export status from cache.

        Returns:
            dict: The download url info.
        """
        json_data = get_redis_cache(cls.USER_ACTIVITY_LOG_EXPORT_CACHE_URL_KEY)
        return json.loads(json_data) if json_data else {}

    @classmethod
    def save_export_url(cls, start_time, end_time, file_uri):
        """Save export url to cache.

        Args:
            start_time (datetime): The start time.
            end_time (datetime): The end time.
            file_uri (str): The file uri.
        """
        export_result = dict(
            start_time=start_time,
            end_time=end_time,
            file_uri=file_uri
        )
        reset_redis_cache(
            cls.USER_ACTIVITY_LOG_EXPORT_CACHE_URL_KEY,
            json.dumps(export_result)
        )

    @classmethod
    def clear_export_status(cls):
        """Delete export status from cache."""
        reset_redis_cache(cls.USER_ACTIVITY_LOG_EXPORT_CACHE_STATUS_KEY, "")
        reset_redis_cache(cls.USER_ACTIVITY_LOG_EXPORT_CACHE_URL_KEY, "")

    @classmethod
    def _write_log_to_tsv(cls, log_data: list):
        """Write log data to tsv format.

        Args:
            log_data (list): The log data.
        
        Returns:
            str: The log data in TSV format.
        """
        tsv = ""
        if not log_data:
            return tsv
        stream = StringIO()
        fieldsnames = log_data[0].keys()
        tsv_writer = csv.DictWriter(
            stream, fieldnames=fieldsnames, delimiter='\t'
        )
        tsv_writer.writeheader()
        tsv_writer.writerows(log_data)
        tsv = stream.getvalue()
        stream.close()
        return tsv
