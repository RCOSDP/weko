# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Swordserver is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Resource for weko-swordserver log messages."""

from flask import current_app


WEKO_SWORDSERVER_MESSAGE = {
    'WEKO_SWORDSERVER_FAILED_RETRIEVE_FILE': {
        'msgid': 'WEKO_SWORDSERVER_E_0001',
        'msgstr': "FAILED to retrieve {file_type} file.",
        'loglevel': 'ERROR',
    },
    'WEKO_SWORDSERVER_FAILED_UPDATE_FILE': {
        'msgid': 'WEKO_SWORDSERVER_E_0002',
        'msgstr': "FAILED to update {file_type} file.",
        'loglevel': 'ERROR',
    },
    'WEKO_SWORDSERVER_FAILED_DELETE_FILE': {
        'msgid': 'WEKO_SWORDSERVER_E_0003',
        'msgstr': "FAILED to delete {file_type} file.",
        'loglevel': 'ERROR',
    },
    'WEKO_SWORDSERVER_FAILED_CREATE_FILE': {
        'msgid': 'WEKO_SWORDSERVER_E_0004',
        'msgstr': "FAILED to create {file_type} file.",
        'loglevel': 'ERROR',
    },
    'WEKO_SWORDSERVER_RETRIEVE_FILE': {
        'msgid': 'WEKO_SWORDSERVER_I_0001',
        'msgstr': "{file_name} file retrieved.",
        'loglevel': 'INFO',
    },
    'WEKO_SWORDSERVER_UPDATE_FILE': {
        'msgid': 'WEKO_SWORDSERVER_I_0002',
        'msgstr': "{file_type} file updated.",
        'loglevel': 'INFO',
    },
    'WEKO_SWORDSERVER_DELETE_FILE': {
        'msgid': 'WEKO_SWORDSERVER_I_0003',
        'msgstr': "{file_type} file deleted.",
        'loglevel': 'INFO',
    },
    'WEKO_SWORDSERVER_CREATE_FILE': {
        'msgid': 'WEKO_SWORDSERVER_I_0004',
        'msgstr': "{file_type} file created.",
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
    param = WEKO_SWORDSERVER_MESSAGE.get(key, None)
    if param:
        weko_logger_base(app=current_app, param=param, ex=ex, **kwargs)
    else:
        weko_logger_base(app=current_app, key=key, ex=ex, **kwargs)
