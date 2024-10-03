# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Authors is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Resource for weko-authors log messages."""

from flask import current_app


WEKO_AUTHORS_MESSAGE = {
    'WEKO_AUTHORS_FAILED_ADD_AUTHOR': {
        'msgid': 'WEKO_AUTHORS_E_0001',
        'msgstr': "FAILED to add author: {author_id}",
        'loglevel': 'ERROR',
    },
    'WEKO_AUTHORS_FAILED_QUIT_ADD_AUTHOR': {
        'msgid': 'WEKO_AUTHORS_E_0002',
        'msgstr': "FAILED to quit adding author.",
        'loglevel': 'ERROR',
    },
    'WEKO_AUTHORS_FAILED_SAVE_AUTHOR': {
        'msgid': 'WEKO_AUTHORS_E_0003',
        'msgstr': "FAILED to save author: {author_id}",
        'loglevel': 'ERROR',
    },
    'WEKO_AUTHORS_FAIILED_DELETE_AUTHOR': {
        'msgid': 'WEKO_AUTHORS_E_0004',
        'msgstr': "FAILED to delete author: {author_id}",
        'loglevel': 'ERROR',
    },
    'WEKO_AUTHORS_FAILED_MERGE_AUTHORID': {
        'msgid': 'WEKO_AUTHORS_E_0005',
        'msgstr': "FAILED to merge author ID:{author_id}",
        'loglevel': 'ERROR',
    },
    'WEKO_AUTHORS_FAILED_EXPORT_ALLCREATOR': {
        'msgid': 'WEKO_AUTHORS_E_0006',
        'msgstr': "FAILED to export all creator.",
        'loglevel': 'ERROR',
    },
    'WEKO_AUTHORS_FAILED_QUIT_EXPORT_ALLCREATOR': {
        'msgid': 'WEKO_AUTHORS_E_0007',
        'msgstr': "FAILED to quit all creator export.",
        'loglevel': 'ERROR',
    },
    'WEKO_AUTHORS_FAILED_REGIST_NEW_CREATOR': {
        'msgid': 'WEKO_AUTHORS_E_0008',
        'msgstr': "FAILED to regist new creator in import file.",
        'loglevel': 'ERROR',
    },
    'WEKO_AUTHORS_FAILED_UPDATE_CREATOR': {
        'msgid': 'WEKO_AUTHORS_E_0009',
        'msgstr': "FAILED to update creator in import file: {author_id}",
        'loglevel': 'ERROR',
    },
    'WEKO_AUTHORS_FAILED_DELETE_CREATOR': {
        'msgid': 'WEKO_AUTHORS_E_0010',
        'msgstr': "FAILED to delete creator in import file: {author_id}",
        'loglevel': 'ERROR',
    },
    'WEKO_AUTHORS_FAILED_DOWNLOAD_AUTHORS_LIST': {
        'msgid': 'WEKO_AUTHORS_E_0011',
        'msgstr': "FAILED to download list of authors shown on screen.",
        'loglevel': 'ERROR',
    },
    'WEKO_AUTHORS_FAILED_ADD_AUTHOR_PREFIX': {
        'msgid': 'WEKO_AUTHORS_E_0012',
        'msgstr': "FAILED to add author prefix.",
        'loglevel': 'ERROR',
    },
    'WEKO_AUTHORS_FAILED _SAVE_AUTHOR_PREFIX': {
        'msgid': 'WEKO_AUTHORS_E_0013',
        'msgstr': "FAILED to save author prefix: {prefix_id}",
        'loglevel': 'ERROR',
    },
    'WEKO_AUTHORS_FAILED_CANCEL_AUTHOR_PREFIX': {
        'msgid': 'WEKO_AUTHORS_E_0014',
        'msgstr': "FAILED to cancel editing author prefix: {prefix_id}",
        'loglevel': 'ERROR',
    },
    'WEKO_AUTHORS_FAILED _DELETE_AUTHOR_PREFIX_PREFIXID': {
        'msgid': 'WEKO_AUTHORS_E_0015',
        'msgstr': "FAILED to delete author prefix: {prefix_id}",
        'loglevel': 'ERROR',
    },
    'WEKO_AUTHORS_ADD_AUTHOR': {
        'msgid': 'WEKO_AUTHORS_I_0001',
        'msgstr': "Author added: {author_id}",
        'loglevel': 'INFO',
    },
    'WEKO_AUTHORS_QUIT_ADD_AUTHOR': {
        'msgid': 'WEKO_AUTHORS_I_0002',
        'msgstr': "The addition of author was quitted.",
        'loglevel': 'INFO',
    },
    'WEKO_AUTHORS_SAVE_AUTHOR': {
        'msgid': 'WEKO_AUTHORS_I_0003',
        'msgstr': "Author saved: {author_id}",
        'loglevel': 'INFO',
    },
    'WEKO_AUTHORS_DELETE_AUTHOR': {
        'msgid': 'WEKO_AUTHORS_I_0004',
        'msgstr': "Delete author: {author_id}",
        'loglevel': 'INFO',
    },
    'WEKO_AUTHORS_SEARCH_AUTHOR': {
        'msgid': 'WEKO_AUTHORS_I_0005',
        'msgstr': "Search author: {search_content}, results: {count}",
        'loglevel': 'INFO',
    },
    'WEKO_AUTHORS_MERGE_AUTHORID': {
        'msgid': 'WEKO_AUTHORS_I_0006',
        'msgstr': "Merged author ID: {author_id}",
        'loglevel': 'INFO',
    },
    'WEKO_AUTHORS_EXPORT_ALLCREATOR': {
        'msgid': 'WEKO_AUTHORS_I_0007',
        'msgstr': "All creator exported.",
        'loglevel': 'INFO',
    },
    'WEKO_AUTHORS_QUIT_EXPORT_ALLCREATOR': {
        'msgid': 'WEKO_AUTHORS_I_0008',
        'msgstr': "All creator export was quitted.",
        'loglevel': 'INFO',
    },
    'WEKO_AUTHORS_REGIST_NEW_CREATOR': {
        'msgid': 'WEKO_AUTHORS_I_0009',
        'msgstr': "Register new creator in import file:{author_id} ",
        'loglevel': 'INFO',
    },
    'WEKO_AUTHORS_UPDATE_CREATOR': {
        'msgid': 'WEKO_AUTHORS_I_0010',
        'msgstr': "Update creator in import file: {author_id}",
        'loglevel': 'INFO',
    },
    'WEKO_AUTHORS_DELETE_CREATOR': {
        'msgid': 'WEKO_AUTHORS_I_0011',
        'msgstr': "Delete creator in import file: {author_id}",
        'loglevel': 'INFO',
    },
    'WEKO_AUTHORS_DOWNLOAD_AUTHORS_LIST': {
        'msgid': 'WEKO_AUTHORS_I_0012',
        'msgstr': "Downloaded list of authors shown on screen.",
        'loglevel': 'INFO',
    },
    'WEKO_AUTHORS_ADD_AUTHOR_PREFIX': {
        'msgid': 'WEKO_AUTHORS_I_0013',
        'msgstr': "Added author prefix: {prefix_id}",
        'loglevel': 'INFO',
    },
    'WEKO_AUTHORS_SAVED_AUTHOR_PREFIX': {
        'msgid': 'WEKO_AUTHORS_I_0014',
        'msgstr': "Saved author prefix: {prefix_id}",
        'loglevel': 'INFO',
    },
    'WEKO_AUTHORS_CANCEL_AUTHOR_PREFIX': {
        'msgid': 'WEKO_AUTHORS_I_0015',
        'msgstr': "Cancelled editing author prefix: {prefix_id}",
        'loglevel': 'INFO',
    },
    'WEKO_AUTHORS_DELETE_AUTHOR_PREFIX': {
        'msgid': 'WEKO_AUTHORS_I_0016',
        'msgstr': "Delete author prefix: {prefix_id}",
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
    param = WEKO_AUTHORS_MESSAGE.get(key, None)
    if param:
        weko_logger_base(app=current_app, param=param, ex=ex, **kwargs)
    else:
        weko_logger_base(app=current_app, key=key, ex=ex, **kwargs)
