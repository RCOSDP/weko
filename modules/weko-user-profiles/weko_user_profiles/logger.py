# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-User-Profiles is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Resource for weko-user-profiles log messages."""

from flask import current_app


WEKO_USER_PROFILES_MESSAGE = {
    'WEKO_USER_PROFILES_FAILED_UPDATE_USER_PROFILE': {
        'msgid': 'WEKO_USER_PROFILES_E_0001',
        'msgstr': "FAILED to update user {user_id} profile.",
        'loglevel': 'ERROR',
    },
    'WEKO_USER_PROFILES_FAILED_DELETE_RECORD': {
        'msgid': 'WEKO_USER_PROFILES_E_0002',
        'msgstr': "FAILED to delete {num} record.",
        'loglevel': 'ERROR',
    },
    'WEKO_USER_PROFILES_SENT_CONFIRMATION_EMAIL': {
        'msgid': 'WEKO_USER_PROFILES_I_0001',
        'msgstr': "Confirmation email has been sent.",
        'loglevel': 'INFO',
    },
    'WEKO_USER_PROFILES_UPDATE_USER_PROFILE': {
        'msgid': 'WEKO_USER_PROFILES_I_0002',
        'msgstr': "User {user_id} profile updated.",
        'loglevel': 'INFO',
    },
    'WEKO_USER_PROFILES_DELETE_RECORD': {
        'msgid': 'WEKO_USER_PROFILES_I_0003',
        'msgstr': "{num} record was deleted.",
        'loglevel': 'INFO',
    },
}

from weko_logging.console import WekoLoggingConsole
weko_logger_base = WekoLoggingConsole.weko_logger_base

def weko_logger(key=None, ex=None, **kwargs):
    """Log message with key.

    Method to output logs in current_app.logger using the resource.

    Args:
        key (str): \
            key of message. Not required if ex is specified.
        ex (Exception): \
            exception object.
            If you catch an exception, specify it here.
        **kwargs: \
            message parameters.
            If you want to replace the placeholder in the message,
            specify the key-value pair here.

    Returns:
        None

    Examples:
    * Log message with key::

        weko_logger(key='WEKO_COMMON_SAMPLE')

    * Log message with key and parameters::

        weko_logger(key='WEKO_COMMON_SAMPLE', param1='param1', \
param2='param2')

    * Log message with key and exception::

        weko_logger(key='WEKO_COMMON_SAMPLE', ex=ex)

    * Log message with key, parameters and exception::

        weko_logger(key='WEKO_COMMON_SAMPLE', param1='param1', \
param2='param2', ex=ex)
    """
    # get message parameters from resource
    param = WEKO_USER_PROFILES_MESSAGE.get(key, None)
    if param:
        weko_logger_base(app=current_app, param=param, ex=ex, **kwargs)
    else:
        weko_logger_base(app=current_app, key=key, ex=ex, **kwargs)
