# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Redis is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Resource for weko-redis log messages."""

from flask import current_app


WEKO_REDIS_MESSAGE = {
    'WEKO_REDIS_FAILED_DIRECT_REDIS_CONNECT': {
        'msgid': 'WEKO_REDIS_E_0001',
        'msgstr': "FAILED direct Redis connection.",
        'loglevel': 'ERROR',
    },
    'WEKO_REDIS_FAILED_DATA_STORE_CONNECT': {
        'msgid': 'WEKO_REDIS_E_0002',
        'msgstr': "FAILED data store connection via Redis.",
        'loglevel': 'ERROR',
    },
    'WEKO_REDIS_FAILED_REDIS_SENTINEL_CONNECT': {
        'msgid': 'WEKO_REDIS_E_0003',
        'msgstr': "FAILED Redis Sentinel connection.",
        'loglevel': 'ERROR',
    },
    'WEKO_REDIS_SUCCESS_DIRECT_REDIS_CONNECT': {
        'msgid': 'WEKO_REDIS_I_0001',
        'msgstr': "Direct Redis connection established successfully.",
        'loglevel': 'INFO',
    },
    'WEKO_REDIS_SUCCESS_DATA_STORE_CONNECT': {
        'msgid': 'WEKO_REDIS_I_0002',
        'msgstr': "Data store connection established successfully via Redis.",
        'loglevel': 'INFO',
    },
    'WEKO_REDIS_SUCCESS_REDIS_SENTINEL_CONNECT': {
        'msgid': 'WEKO_REDIS_I_0003',
        'msgstr': "Redis Sentinel connection established successfully.",
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
    param = WEKO_REDIS_MESSAGE.get(key, None)
    if param:
        weko_logger_base(app=current_app, param=param, ex=ex, **kwargs)
    else:
        weko_logger_base(app=current_app, key=key, ex=ex, **kwargs)
