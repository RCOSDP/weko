# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Logging is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Logging utils."""

import logging

class WekoLoggingFilter(logging.Filter):
    """Filter for loggers."""

    def filter(self, record):
        """Filter log record.

        Override the filter method to add user_id and ip_address to \
            log record.
        """
        from weko_accounts.utils import get_remote_addr

        record.user_id = get_current_user_id()
        record.ip_address = get_remote_addr()

        # If the user is not authenticated, set the user_id to 'Guest'
        if (record.ip_address is not None) and (record.user_id is None):
            record.user_id = 'Guest'

        # Replace the attribute name of the log record
        if hasattr(record, 'wpathname'):
            record.pathname = record.wpathname
        if hasattr(record, 'wlineno'):
            record.lineno = record.wlineno
        if hasattr(record, 'wfuncName'):
            record.funcName = record.wfuncName

        return True

wekoLoggingFilter = WekoLoggingFilter()

def get_current_user_id():
    """Get current user id.

    Method to get the user id of the currently authenticated user.
    If the user is not authenticated, return None.

    Returns:
        Integer: \
            If user is authenticated, return user id.
        None: \
            If user is not authenticated, return None.
    """
    from flask_login import current_user

    user_id = None
    if hasattr(current_user, 'id'):
        user_id = current_user.id

    return user_id