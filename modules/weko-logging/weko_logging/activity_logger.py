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

        :param app: The flask application.
        """
        self.app = app

    @classmethod
    def error(cls, operation=None, parent_id=None, target_key=None, remarks=None):
        """Output as error log.

        :param operation: User operation type.
        :param parent_id: Parent log id.
        :param target_key: Operation target key(eg. id).
        :param remarks: Remarks.
        """

        user_id = UserActivityLogHandler.get_user_id()
        community_id = UserActivityLogHandler.get_community_id_from_path()

        error_message = f"Error occurred: operation={operation}, parent_id={parent_id}, target_key={target_key}, "
        error_message += f"user_id={user_id}, community_id={community_id}"
        _logger.error(error_message, extra={
            "parent_id": parent_id,
            "operation": operation,
            "target_key": target_key,
            "remarks": remarks,
        })

    @classmethod
    def info(cls, operation=None, parent_id=None, target_key=None, remarks=None):
        """Output as info log.

        :param operation: User operation type.
        :param parent_id: Parent log id.
        :param target_key: Operation target key(eg. id).
        :param remarks: Remarks.
        """
        user_id = UserActivityLogHandler.get_user_id()
        community_id = UserActivityLogHandler.get_community_id_from_path()

        error_message = f"Info: operation={operation}, parent_id={parent_id}, target_key={target_key}, "
        error_message += f"user_id={user_id}, community_id={community_id}"

        _logger.info(error_message, extra={
            "parent_id": parent_id,
            "operation": operation,
            "target_key": target_key,
            "remarks": remarks,
        })

    @classmethod
    def get_next_parent_id(session):
        """Get next parent id.

        :param session: The database session.
        :return: The next log id.
        """
        return UserActivityLog.get_sequence(session)