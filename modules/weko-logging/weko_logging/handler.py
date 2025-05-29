# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Weko logging handler."""

import logging
import urllib
from datetime import datetime
from flask import request, current_app
from flask_security import current_user

from invenio_accounts.models import User
from invenio_db import db
from weko_logging.models import UserActivityLog

class UserActivityLogHandler(logging.Handler):
    """Logging handler for audit logs."""

    def __init__(self, app):
        """Initialize the handler.

        Args:
            app (Flask): The Flask application.
        """
        super(UserActivityLogHandler, self).__init__()
        self.app = app

    def emit(self, record):
        """Emit a log record.

        Args:
            record (logging.LogRecord): The log record.
        Raises:
            Exception: If failed to create user activity log.
        """
        # if not has operation, skip create record
        if not hasattr(record, "operation"):
            return

        # create record if error level is error or info
        if record.levelname not in ["ERROR", "INFO"]:
            return

        operation = record.operation
        # get operation_type_id, operation_id, target from config "WEKO_LOGGING_OPERATION_MASTER"
        operation_type_id, operation_id, target = self._get_target_from_operation_id(operation)

        if operation_type_id is None or operation_id is None:
            current_app.logger.error(f"Invalid operation: {operation}")
            raise ValueError(f"Invalid operation: {operation}")

        # get log group id
        log_group_id = None
        if hasattr(record, "log_group_id"):
            log_group_id = record.log_group_id or None

        # get user_id from current_user
        user_id = self.get_user_id()
        eppn = None
        if user_id:
            user = User.query.filter_by(id=user_id).first()
            # get eppn from user
            if user is not None:
                shib_users = list(user.shib_weko_user)
                if shib_users is not None and len(shib_users) == 1:
                    shib_user = shib_users[0]
                    eppn = shib_user.shib_eppn

        # get source, ip_address and client_id from request
        ip_address = None
        source = None
        client_id = None

        # get request info from extra     
        request_summury = record.request_info if hasattr(record, "request_info") else None
        if not request_summury:
            request_summury = self.get_summary_from_request()

        # get community id from request
        community_id = None
        if hasattr(record, "community_id"):
            community_id = record.community_id
        else:
            self.get_community_id_from_path(request_summury)

        # ip address
        ip_address = request_summury.get("ip_address")
        # source
        source = request_summury.get("path")
        # client id
        client_id = request_summury.get("client_id")

        # get other values from record
        target_key = record.target_key if hasattr(record, "target_key") else None

        if not target and target_key:
            current_app.logger.error("target and target_key must be set together")
            raise ValueError("target and target_key must be set together")

        remarks = record.remarks if hasattr(record, "remarks") else None

        timestamp_seconds = record.created
        created_dt = datetime.fromtimestamp(timestamp_seconds)

        user_activity_log = UserActivityLog(
            user_id=user_id,
            log={},
            log_group_id=log_group_id,
            community_id=community_id,
            remarks=remarks,
        )
        log = {
            "id": None,
            "log_level": record.levelname,
            "date": created_dt.strftime("%Y/%m/%d %H:%M:%S.%f"),
            "user_id": user_id,
            "eppn": eppn,
            "ip_address": ip_address,
            "client_id": client_id,
            "community_id": community_id or "",
            "source": source,
            "log_group_id": log_group_id,
            "operation_type_id": operation_type_id,
            "operation_id": operation_id,
            "target": target,
            "target_key": target_key,
        }

        try:
            with db.session.begin_nested():
                db.session.add(user_activity_log)
                db.session.flush()
                log["id"] = user_activity_log.id
                user_activity_log.log = log
            if hasattr(record, "required_commit") and record.required_commit:
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to create user activity log: {e}")
            current_app.logger.error(e.__traceback__)
            raise

    @classmethod
    def get_community_id_from_path(cls, request_info):
        """Get community id from request path.
        
        Args:
            request_info (dict): The request path.

        Returns:
            str: The community id if it exists, otherwise None.
        """
        if request_info:
            request_path = request_info.get("path", "")
            request_args = request_info.get("args", {})
        elif request:
            request_path = request.path
            request_args = request.args
        else:
            return None
        community_id = None
        path_info = urllib.parse.urlparse(request_path)
        if "/c/" in str(path_info.path):
            community_path = path_info.path.split("/c/")[1]
            community_id = community_path.split("/")[0]
        elif "community" in request_args:
            community_id = request_args.get("community")
        return community_id

    @classmethod
    def get_user_id(cls):
        """Get user id from current_user.

        Returns:
            str: The user id.
        """
        user_id = None
        if current_user and current_user.is_authenticated and \
            hasattr(current_user, "id"):
            user_id = current_user.id
        return user_id

    def _get_target_from_operation_id(self, operation):
        """Get target from operation id.

        Args:
            operation(str): The operation id.

        Returns:
            Tuple: The operation type id, operation id, and target.
        """
        # get target from config "WEKO_LOGGING_OPERATION_MASTER"
        operation_master = self.app.config.get(
            "WEKO_LOGGING_OPERATION_MASTER", {}
        )
        for operation_category in operation_master.values():
            if operation not in operation_category.get("operation", {}).keys():
                continue

            operation_info = operation_category["operation"][operation]
            operation_type_id = operation_category.get("id")
            operation_id = operation_info.get("id")
            target = operation_info.get("target")
            return (operation_type_id, operation_id, target)
        return (None, None, None)

    @classmethod
    def get_summary_from_request(cls):
        """Get request information from Flask request.

        Returns:
            dict: The request information.
        """
        if not request:
            return {}
    
        request_summary = {}
        # ip address
        if hasattr(request, "remote_addr") and request.remote_addr:
            request_summary["ip_address"] = request.remote_addr
        elif request.headers.getlist("X-Forwarded-For"):
            forwarded_list = request.headers.getlist("X-Forwarded-For")
            request_summary["ip_address"] = forwarded_list[0]

        # source
        if hasattr(request, "path") and request.path:
            request_summary["path"] = request.path

        # get client id from request oauth
        if hasattr(request, "oauth") and request.oauth:
            request_summary["client_id"] = request.oauth.client.client_id

        # get args from request
        if hasattr(request, "args") and request.args:
            request_summary["args"] = request.args
        
        return request_summary
