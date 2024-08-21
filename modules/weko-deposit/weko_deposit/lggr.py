# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Deposit is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Resource for weko-deposit log messages."""

WEKO_DEPOSIT_MESSAGE = {
    'WEKO_DEPOSIT_FAILED_UPDATE_ITEM': {
        'msgid': 'WEKO_DEPOSIT_E_0001',
        'msgstr': "FAILED to update item: {pid}",
        'msglvl': 'ERROR',
    },
    'WEKO_DEPOSIT_FAILED_DELETE_ITEM': {
        'msgid': 'WEKO_DEPOSIT_E_0002',
        'msgstr': "FAILED to delete item: {pid}",
        'msglvl': 'ERROR',
    },
    'WEKO_DEPOSIT_FAILED_ITEM_PROCESS': {
        'msgid': 'WEKO_DEPOSIT_E_0003',
        'msgstr': "FAILED item process: {pid}",
        'msglvl': 'ERROR',
    },
    'WEKO_DEPOSIT_FAILED_FILE_UPLOAD': {
        'msgid': 'WEKO_DEPOSIT_E_0004',
        'msgstr': "FAILED file upload: {file_id}",
        'msglvl': 'ERROR',
    },
    'WEKO_DEPOSIT_FAILED_REGISTER_INDEX': {
        'msgid': 'WEKO_DEPOSIT_E_0005',
        'msgstr': "FAILED to register index designation: {pid}",
        'msglvl': 'ERROR',
    },
    'WEKO_DEPOSIT_FAILED_ADD_AUTHOR': {
        'msgid': 'WEKO_DEPOSIT_E_0006',
        'msgstr': "FAILED to add author: {author_id}",
        'msglvl': 'ERROR',
    },
    'WEKO_DEPOSIT_FAILED_QUIT_ADD_AUTHOR': {
        'msgid': 'WEKO_DEPOSIT_E_0007',
        'msgstr': "FAILED to quit adding author.",
        'msglvl': 'ERROR',
    },
    'WEKO_DEPOSIT_FAILED_SAVE_AUTHOR': {
        'msgid': 'WEKO_DEPOSIT_E_0008',
        'msgstr': "FAILED to save author: {author_id}",
        'msglvl': 'ERROR',
    },
    'WEKO_DEPOSIT_FAIILED_DELETE_AUTHOR': {
        'msgid': 'WEKO_DEPOSIT_E_0009',
        'msgstr': "FAILED to delete author: {author_id}",
        'msglvl': 'ERROR',
    },
    'WEKO_DEPOSIT_FAILED_MERGE_AUTHORID': {
        'msgid': 'WEKO_DEPOSIT_E_0010',
        'msgstr': "FAILED to merge author ID:{author_id}",
        'msglvl': 'ERROR',
    },
    'WEKO_DEPOSIT_UPDATE_ITEM': {
        'msgid': 'WEKO_DEPOSIT_I_0001',
        'msgstr': "Update item: {pid}",
        'msglvl': 'INFO',
    },
    'WEKO_DEPOSIT_DELETE_ITEM': {
        'msgid': 'WEKO_DEPOSIT_I_0002',
        'msgstr': "Delete item: {pid}",
        'msglvl': 'INFO',
    },
    'WEKO_DEPOSIT_CREATE_ITEM': {
        'msgid': 'WEKO_DEPOSIT_I_0003',
        'msgstr': "Create item: {pid}",
        'msglvl': 'INFO',
    },
    'WEKO_DEPOSIT_UPLOAD_FILE': {
        'msgid': 'WEKO_DEPOSIT_I_0004',
        'msgstr': "Upload file: {file_id}",
        'msglvl': 'INFO',
    },
    'WEKO_DEPOSIT_QUIT_FILE_UPLOAD': {
        'msgid': 'WEKO_DEPOSIT_I_0005',
        'msgstr': "File upload has been quitted: {file_id}",
        'msglvl': 'INFO',
    },
    'WEKO_DEPOSIT_CHANGE_MULTI_UPLOAD': {
        'msgid': 'WEKO_DEPOSIT_I_0006',
        'msgstr': "The multi-upload function has been changed to "\
            "{configuration_value}.",
        'msglvl': 'INFO',
    },
    'WEKO_DEPOSIT_CHANGE_MULTI_UPLOAD_DETAIL_SETTING': {
        'msgid': 'WEKO_DEPOSIT_I_0007',
        'msgstr': "The multi-upload function has been changed {section} to "\
            "{configuration_value}.",
        'msglvl': 'INFO',
    },
    'WEKO_DEPOSIT_REGISTER_INDEX': {
        'msgid': 'WEKO_DEPOSIT_I_0008',
        'msgstr': "Destination index has been registered: {pid}",
        'msglvl': 'INFO',
    },
    'WEKO_DEPOSIT_ADD_AUTHOR': {
        'msgid': 'WEKO_DEPOSIT_I_0009',
        'msgstr': "Author added: {author_id}",
        'msglvl': 'INFO',
    },
    'WEKO_DEPOSIT_QUIT_ADD_AUTHOR': {
        'msgid': 'WEKO_DEPOSIT_I_0010',
        'msgstr': "The addition of author was quitted.",
        'msglvl': 'INFO',
    },
    'WEKO_DEPOSIT_SAVE_AUTHOR': {
        'msgid': 'WEKO_DEPOSIT_I_0011',
        'msgstr': "Author saved: {author_id}",
        'msglvl': 'INFO',
    },
    'WEKO_DEPOSIT_DELETE_AUTHOR': {
        'msgid': 'WEKO_DEPOSIT_I_0012',
        'msgstr': "Delete author: {author_id}",
        'msglvl': 'INFO',
    },
    'WEKO_DEPOSIT_SEARCH_AUTHOR': {
        'msgid': 'WEKO_DEPOSIT_I_0013',
        'msgstr': "Search author: {query}, results: {num} authors",
        'msglvl': 'INFO',
    },
    'WEKO_DEPOSIT_MERGE_AUTHORID': {
        'msgid': 'WEKO_DEPOSIT_I_0014',
        'msgstr': "Merged author ID: {author_id}",
        'msglvl': 'INFO',
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
    param = WEKO_DEPOSIT_MESSAGE.get(key, None)
    if param:
        weko_logger_base(param=param, ex=ex, **kwargs)
    else:
        weko_logger_base(key=key, ex=ex, **kwargs)
