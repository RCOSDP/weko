# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Index-Tree-Journal is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Resource for weko-index_tree_journal log messages."""

from flask import current_app


WEKO_INDEX_TREE_JOURNAL_MESSAGE = {
    'WEKO_INDEX_TREE_JOURNAL_FAILED_DISPLAY_SETTINGS_JOURNAL_INFO': {
        'msgid': 'WEKO_INDEX_TREE_JOURNAL_E_0001',
        'msgstr': "FAILED to change display settings of index {index_name} "\
            "for journal information to {configuration_value}.",
        'loglevel': 'ERROR',
    },
    'WEKO_INDEX_TREE_JOURNAL_FAILED_SAVE_JOURNAL_INFO': {
        'msgid': 'WEKO_INDEX_TREE_JOURNAL_E_0002',
        'msgstr': "FAILED to save journal information. "\
            "Index name: {index_name}",
        'loglevel': 'ERROR',
    },
    'WEKO_INDEX_TREE_JOURNAL_FAILED_OUTPUT _JOURNAL_INFO': {
        'msgid': 'WEKO_INDEX_TREE_JOURNAL_E_0003',
        'msgstr': "FAILED to output journal information. "\
            "Index name: {index_name}",
        'loglevel': 'ERROR',
    },
    'WEKO_INDEX_TREE_JOURNAL_FAILED_CREATE_NEW_JOURNAL_INFO': {
        'msgid': 'WEKO_INDEX_TREE_JOURNAL_E_0004',
        'msgstr': "FAILED to create new journal information. "\
            "Index name: {index_name}",
        'loglevel': 'ERROR',
    },
    'WEKO_INDEX_TREE_JOURNAL_FAILED_DELETE_JOURNAL_INFO': {
        'msgid': 'WEKO_INDEX_TREE_JOURNAL_E_0005',
        'msgstr': "FAILED to delete journal information. "\
            "Index name: {index_name}",
        'loglevel': 'ERROR',
    },
    'WEKO_INDEX_TREE_JOURNAL_DISPLAY_SETTINGS_JOURNAL_INFO': {
        'msgid': 'WEKO_INDEX_TREE_JOURNAL_I_0001',
        'msgstr': "Display settings of index {index_name} for journal "\
            "information has been changed to {configuration_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_INDEX_TREE_JOURNAL_DISPLAY_DETAIL_SETTINGS_JOURNAL_INFO': {
        'msgid': 'WEKO_INDEX_TREE_JOURNAL_I_0002',
        'msgstr': "Display settings of index {index_name} for journal "\
            "information has been changed {section} to {configuration_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_INDEX_TREE_JOURNAL_SAVE_JOURNAL_INFO': {
        'msgid': 'WEKO_INDEX_TREE_JOURNAL_I_0003',
        'msgstr': "Journal information edited. Index name: {index_name}",
        'loglevel': 'INFO',
    },
    'WEKO_INDEX_TREE_JOURNAL_OUTPUT _JOURNAL_INFO': {
        'msgid': 'WEKO_INDEX_TREE_JOURNAL_I_0004',
        'msgstr': "Journal information has been output. "\
            "Index name: {index_name}",
        'loglevel': 'INFO',
    },
    'WEKO_INDEX_TREE_JOURNAL_CREATE_NEW_JOURNAL_INFO': {
        'msgid': 'WEKO_INDEX_TREE_JOURNAL_I_0005',
        'msgstr': "New journal information has been created. "\
            "Index name: {index_name}",
        'loglevel': 'INFO',
    },
    'WEKO_INDEX_TREE_JOURNAL_DELETE_JOURNAL_INFO': {
        'msgid': 'WEKO_INDEX_TREE_JOURNAL_I_0006',
        'msgstr': "Journal information has been deleted. "\
            "Index name: {index_name}",
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
    param = WEKO_INDEX_TREE_JOURNAL_MESSAGE.get(key, None)
    if param:
        weko_logger_base(app=current_app, param=param, ex=ex, **kwargs)
    else:
        weko_logger_base(app=current_app, key=key, ex=ex, **kwargs)
