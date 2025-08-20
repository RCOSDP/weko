# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Weko logging user activity logger wrapper."""

from flask import current_app, g, has_request_context
from werkzeug.local import LocalProxy

from weko_logging.models import UserActivityLog
from weko_logging.handler import UserActivityLogHandler

_logger = LocalProxy(lambda: current_app.extensions["weko-logging-activity"])

class UserActivityLogger:
    """User activity logger."""

    def __init__(self, app):
        """Initialize user logger.

        Args:
            app (Flask): The Flask application.
        """
        self.app = app

    @classmethod
    def error(cls, operation=None, target_key=None,
              request_info=None, remarks=None):
        """Output as error log.

        Args:
            operation (str): User operation type.
            target_key (str): Operation target key (e.g. id).
            request_info (dict): Request information (Required if called by shared task).
            remarks (str): Remarks.
        """
        user_id = UserActivityLogHandler.get_user_id()
        community_id = UserActivityLogHandler.get_community_id_from_path(request_info)

        log_group_id = cls.get_log_group_id(request_info)

        error_message = f"Error occurred: operation={operation}, log_group_id={log_group_id}, target_key={target_key}, "
        error_message += f"user_id={user_id}, community_id={community_id}"
        _logger.error(error_message, extra={
            "log_group_id": log_group_id,
            "operation": operation,
            "target_key": target_key,
            "request_info": request_info,
            "community_id": community_id,
            "required_commit": True,
            "remarks": remarks,
        })

    @classmethod
    def info(cls, operation=None, target_key=None, request_info=None, 
             required_commit=True, remarks=None):
        """Output as info log.

        Args:
            operation (str): User operation type.
            target_key (str): Operation target key (e.g. id).
            request_info (dict): Request information (Required if called by shared task).
            required_commit (bool): Whether to commit the log.
            remarks (str): Remarks.
        """
        user_id = UserActivityLogHandler.get_user_id()
        community_id = UserActivityLogHandler.get_community_id_from_path(request_info)

        log_group_id = cls.get_log_group_id(request_info)
        # If log_group_id is None, issue a new one
        if log_group_id is None:
            cls.issue_log_group_id(None)
            log_group_id = cls.get_log_group_id(request_info)

        message = f"Info: operation={operation}, log_group_id={log_group_id}, target_key={target_key}, "
        message += f"user_id={user_id}, community_id={community_id}"

        _logger.info(message, extra={
            "log_group_id": log_group_id,
            "operation": operation,
            "target_key": target_key,
            "request_info": request_info,
            "community_id": community_id,
            "required_commit": required_commit,
            "remarks": remarks,
        })
        
    @classmethod
    def get_log_group_id(cls, request_info):
        """Get log group id

        Args:
            request_info (dict): The request information.

        Returns:
            int: The log group ID.
        """
        log_group_id = None
        if request_info and "log_group_id" in request_info:
            log_group_id = request_info["log_group_id"]
        elif has_request_context() and hasattr(g, "log_group_id"):
            log_group_id = g.log_group_id

        return log_group_id

    @classmethod
    def issue_log_group_id(cls, session):
        """Issue a new log group ID and store request context.

        Args:
            session: The database session.

        Returns:
            bool: True if the log group ID was successfully issued, False otherwise.
        """
        if not has_request_context():
            return False

        log_group_id = UserActivityLog.get_log_group_sequence(session)
        g.log_group_id = log_group_id
        return True

    @classmethod
    def get_summary_from_request(cls):
        """Get the request summary.

        Args:
            request_info (dict): The request information.

        Returns:
            dict: The request summary.
        """
        return UserActivityLogHandler.get_summary_from_request()