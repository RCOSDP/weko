# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Weko logging user activity logger wrapper."""

from flask import current_app
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
    def error(cls, operation=None, parent_id=None,
              target_key=None, request_info=None, remarks=None):
        """Output as error log.

        Args:
            operation (str): User operation type.
            parent_id (int): Parent log id.
            target_key (str): Operation target key (e.g. id).
            request_info (dict): Request information (Required if called by shared task).
            remarks (str): Remarks.
        """
        user_id = UserActivityLogHandler.get_user_id()
        community_id = UserActivityLogHandler.get_community_id_from_path(request_info)

        error_message = f"Error occurred: operation={operation}, parent_id={parent_id}, target_key={target_key}, "
        error_message += f"user_id={user_id}, community_id={community_id}"
        _logger.error(error_message, extra={
            "parent_id": parent_id,
            "operation": operation,
            "target_key": target_key,
            "request_info": request_info,
            "community_id": community_id,
            "required_commit": True,
            "remarks": remarks,
        })

    @classmethod
    def info(cls, operation=None, parent_id=None,
             target_key=None, request_info=None, 
             required_commit=True, remarks=None):
        """Output as info log.

        Args:
            operation (str): User operation type.
            parent_id (int): Parent log id.
            target_key (str): Operation target key (e.g. id).
            request_info (dict): Request information (Required if called by shared task).
            required_commit (bool): Whether to commit the log.
            remarks (str): Remarks.
        """
        user_id = UserActivityLogHandler.get_user_id()
        community_id = UserActivityLogHandler.get_community_id_from_path(request_info)

        error_message = f"Info: operation={operation}, parent_id={parent_id}, target_key={target_key}, "
        error_message += f"user_id={user_id}, community_id={community_id}"

        _logger.info(error_message, extra={
            "parent_id": parent_id,
            "operation": operation,
            "target_key": target_key,
            "request_info": request_info,
            "community_id": community_id,
            "required_commit": required_commit,
            "remarks": remarks,
        })

    @classmethod
    def get_next_parent_id(cls, session):
        """Get the next parent ID.

        Args:
            session: The database session.

        Returns:
            int: The next log ID.
        """
        return UserActivityLog.get_sequence(session)

    @classmethod
    def get_summary_from_request(cls):
        """Get the request summary.

        Args:
            request_info (dict): The request information.

        Returns:
            dict: The request summary.
        """
        return UserActivityLogHandler.get_summary_from_request()