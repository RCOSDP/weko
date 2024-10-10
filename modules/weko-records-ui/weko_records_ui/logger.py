# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Records-ui is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Resource for weko-records_ui log messages."""

from flask import current_app


WEKO_RECORDS_UI_MESSAGE = {
    'WEKO_RECORDS_UI_FAILED_UPDATE_ITEMS_IN_BULK': {
        'msgid': 'WEKO_RECORDS_UI_E_0001',
        'msgstr': "FAILED to update items in bulk",
        'loglevel': 'ERROR',
    },
    'WEKO_RECORDS_UI_FAILED_SAVE_INDEX_SETTINGS': {
        'msgid': 'WEKO_RECORDS_UI_E_0002',
        'msgstr': "Failed to save changes to index settings.",
        'loglevel': 'ERROR',
    },
    'WEKO_RECORDS_UI_FAILED_UPDATE_ITEM': {
        'msgid': 'WEKO_RECORDS_UI_E_0003',
        'msgstr': "FAILED to update item: {pid}",
        'loglevel': 'ERROR',
    },
    'WEKO_RECORDS_UI_FAILED_DELETE_ITEM': {
        'msgid': 'WEKO_RECORDS_UI_E_0004',
        'msgstr': "FAILED to delete item: {pid}",
        'loglevel': 'ERROR',
    },
    'WEKO_RECORDS_UI_FAILED_ITEM_PROCESS': {
        'msgid': 'WEKO_RECORDS_UI_E_0005',
        'msgstr': "FAILED item process: {pid}",
        'loglevel': 'ERROR',
    },
    'WEKO_RECORDS_UI_FAILED_FILE_UPLOAD': {
        'msgid': 'WEKO_RECORDS_UI_E_0006',
        'msgstr': "FAILED file upload: {file_id}",
        'loglevel': 'ERROR',
    },
    'WEKO_RECORDS_UI_UPDATE_ITEMS_IN_BULK': {
        'msgid': 'WEKO_RECORDS_UI_I_0001',
        'msgstr': "Items updated in bulk: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_RECORDS_UI_CHANGE_DISPLAY_SETTINGS_SEARCH_RESULTS': {
        'msgid': 'WEKO_RECORDS_UI_I_0002',
        'msgstr': "The display setting for search results has been changed "\
            "to {configuration_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_RECORDS_UI_CHANGE_DISPLAY_DETAIL_SETTINGS_SEARCH_RESULTS': {
        'msgid': 'WEKO_RECORDS_UI_I_0003',
        'msgstr': "The display setting for search results has been changed "\
            "{section} to {configuration_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_RECORDS_UI_UPDATE_ITEM': {
        'msgid': 'WEKO_RECORDS_UI_I_0004',
        'msgstr': "Update item: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_RECORDS_UI_DELETE_ITEM': {
        'msgid': 'WEKO_RECORDS_UI_I_0005',
        'msgstr': "Delete item: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_RECORDS_UI_CREATE_ITEM': {
        'msgid': 'WEKO_RECORDS_UI_I_0006',
        'msgstr': "Create item: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_RECORDS_UI_UPLOAD_FILE': {
        'msgid': 'WEKO_RECORDS_UI_I_0007',
        'msgstr': "Upload file: {file_id}",
        'loglevel': 'INFO',
    },
    'WEKO_RECORDS_UI_QUIT_FILE_UPLOAD': {
        'msgid': 'WEKO_RECORDS_UI_I_0008',
        'msgstr': "File upload has been quitted: {file_id}",
        'loglevel': 'INFO',
    },
    'WEKO_RECORDS_UI_CHANGE_SETTINGS_MULTIPART_UPLOAD': {
        'msgid': 'WEKO_RECORDS_UI_I_0009',
        'msgstr': "The multipart upload function setting has been changed to "\
            "{configuration_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_RECORDS_UI_USER_AUTH_EXISTS': {
        'msgid': 'WEKO_RECORDS_UI_I_0010',
        'msgstr': "Authorisation exists for the user.",
        'loglevel': 'INFO',
    },
    'WEKO_RECORDS_UI_USER_NO_AUTH': {
        'msgid': 'WEKO_RECORDS_UI_I_0011',
        'msgstr': "User is not authorised.",
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
    param = WEKO_RECORDS_UI_MESSAGE.get(key, None)
    if param:
        weko_logger_base(app=current_app, param=param, ex=ex, **kwargs)
    else:
        weko_logger_base(app=current_app, key=key, ex=ex, **kwargs)
