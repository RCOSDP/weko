# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Gridlayout is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Resource for weko-gridlayout log messages."""

from flask import current_app


WEKO_GRIDLAYOUT_MESSAGE = {
    'WEKO_GRIDLAYOUT_FAILED_OUTPUT_RSS_DOCUMENT': {
        'msgid': 'WEKO_GRIDLAYOUT_E_0001',
        'msgstr': "FAILED to output RSS document.",
        'loglevel': 'ERROR',
    },
    'WEKO_GRIDLAYOUT_FAILED_BUILD_RSS_DATA_IN_XML': {
        'msgid': 'WEKO_GRIDLAYOUT_E_0002',
        'msgstr': "FAILED to build RSS-formatted data in XML format.",
        'loglevel': 'ERROR',
    },
    'WEKO_GRIDLAYOUT_FAILED_CREATE_WIDGET': {
        'msgid': 'WEKO_GRIDLAYOUT_E_0003',
        'msgstr': "FAILED to create new widget.",
        'loglevel': 'ERROR',
    },
    'WEKO_GRIDLAYOUT_FAILED_SAVE_WIDGET': {
        'msgid': 'WEKO_GRIDLAYOUT_E_0004',
        'msgstr': "FAILED to edit widget: {widget_id}",
        'loglevel': 'ERROR',
    },
    'WEKO_GRIDLAYOUT_FAILED_APPLY_FILTER': {
        'msgid': 'WEKO_GRIDLAYOUT_E_0005',
        'msgstr': "FAILED to apply filter.",
        'loglevel': 'ERROR',
    },
    'WEKO_GRIDLAYOUT_FAILED_RESET_FILTER': {
        'msgid': 'WEKO_GRIDLAYOUT_E_0006',
        'msgstr': "FAILED to reset filter.",
        'loglevel': 'ERROR',
    },
    'WEKO_GRIDLAYOUT_FAILED_DELETE_WIDGET': {
        'msgid': 'WEKO_GRIDLAYOUT_E_0007',
        'msgstr': "FAILED to delete selected widgets.",
        'loglevel': 'ERROR',
    },
    'WEKO_GRIDLAYOUT_FAILED_QUIT_DELETE_WIDGET': {
        'msgid': 'WEKO_GRIDLAYOUT_E_0008',
        'msgstr': "FAILED to quit the deletion of selected widgets: "\
            "{num} records",
        'loglevel': 'ERROR',
    },
    'WEKO_GRIDLAYOUT_FAILED_SEARCH_WIDGET': {
        'msgid': 'WEKO_GRIDLAYOUT_E_0009',
        'msgstr': "FAILED to search wedgets: {query}",
        'loglevel': 'ERROR',
    },
    'WEKO_GRIDLAYOUT_FAILED_ADD_PAGE': {
        'msgid': 'WEKO_GRIDLAYOUT_E_0010',
        'msgstr': "FAILED to add page.",
        'loglevel': 'ERROR',
    },
    'WEKO_GRIDLAYOUT_FAILED_SAVE_EDIT_PAGE': {
        'msgid': 'WEKO_GRIDLAYOUT_E_0011',
        'msgstr': "FAILED to save page edits.",
        'loglevel': 'ERROR',
    },
    'WEKO_GRIDLAYOUT_FAILED_DELETE_PAGE': {
        'msgid': 'WEKO_GRIDLAYOUT_E_0012',
        'msgstr': "FAILED to delete page.",
        'loglevel': 'ERROR',
    },
    'WEKO_GRIDLAYOUT_ENABLED_RSS_FEEDS': {
        'msgid': 'WEKO_GRIDLAYOUT_I_0001',
        'msgstr': "RSS feeds are now enabled.",
        'loglevel': 'INFO',
    },
    'WEKO_GRIDLAYOUT_CHANGED_RSS_FEEDS_SETTING': {
        'msgid': 'WEKO_GRIDLAYOUT_I_0002',
        'msgstr': "The RSS feeds has been changed to {configuration_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_GRIDLAYOUT_CHANGED_RSS_FEEDS_DETAILS_SETTING': {
        'msgid': 'WEKO_GRIDLAYOUT_I_0003',
        'msgstr': "The RSS feeds has been changed {section} to "\
            "{configuration_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_GRIDLAYOUT_OUTPUT_RSS_DOCUMENT': {
        'msgid': 'WEKO_GRIDLAYOUT_I_0004',
        'msgstr': "RSS document has been output.",
        'loglevel': 'INFO',
    },
    'WEKO_GRIDLAYOUT_BUILT_RSS_DATA_IN_XML': {
        'msgid': 'WEKO_GRIDLAYOUT_I_0005',
        'msgstr': "RSS-formatted data built in XML format.",
        'loglevel': 'INFO',
    },
    'WEKO_GRIDLAYOUT_CREATE_WIDGET': {
        'msgid': 'WEKO_GRIDLAYOUT_I_0006',
        'msgstr': "New widget created: {widget_id}",
        'loglevel': 'INFO',
    },
    'WEKO_GRIDLAYOUT_SAVE_WIDGET': {
        'msgid': 'WEKO_GRIDLAYOUT_I_0007',
        'msgstr': "Widget edits have been saved: {widget_id}",
        'loglevel': 'INFO',
    },
    'WEKO_GRIDLAYOUT_APPLY_FILTER': {
        'msgid': 'WEKO_GRIDLAYOUT_I_0008',
        'msgstr': "Filter has been applied.",
        'loglevel': 'INFO',
    },
    'WEKO_GRIDLAYOUT_RESET_FILTER': {
        'msgid': 'WEKO_GRIDLAYOUT_I_0009',
        'msgstr': "Filter has been reset.",
        'loglevel': 'INFO',
    },
    'WEKO_GRIDLAYOUT_DELETE_WIDGET': {
        'msgid': 'WEKO_GRIDLAYOUT_I_0010',
        'msgstr': "Selected widget has been deleted: {num} records",
        'loglevel': 'INFO',
    },
    'WEKO_GRIDLAYOUT_QUIT_DELETE_WIDGET': {
        'msgid': 'WEKO_GRIDLAYOUT_I_0011',
        'msgstr': "Cancelled deletion of selected widgets.",
        'loglevel': 'INFO',
    },
    'WEKO_GRIDLAYOUT_SEARCH_WIDGET': {
        'msgid': 'WEKO_GRIDLAYOUT_I_0012',
        'msgstr': "Search widgets: {query}, results: {num} records",
        'loglevel': 'INFO',
    },
    'WEKO_GRIDLAYOUT_ADD_PAGE': {
        'msgid': 'WEKO_GRIDLAYOUT_I_0013',
        'msgstr': "Page added.",
        'loglevel': 'INFO',
    },
    'WEKO_GRIDLAYOUT_SAVE_EDIT_PAGE': {
        'msgid': 'WEKO_GRIDLAYOUT_I_0014',
        'msgstr': "Page edits have been saved.",
        'loglevel': 'INFO',
    },
    'WEKO_GRIDLAYOUT_DELETE_PAGE': {
        'msgid': 'WEKO_GRIDLAYOUT_I_0015',
        'msgstr': "Page deleted.",
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
    param = WEKO_GRIDLAYOUT_MESSAGE.get(key, None)
    if param:
        weko_logger_base(app=current_app, param=param, ex=ex, **kwargs)
    else:
        weko_logger_base(app=current_app, key=key, ex=ex, **kwargs)
