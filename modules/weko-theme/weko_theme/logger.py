# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Theme is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Resource for weko-theme log messages."""

from flask import current_app


WEKO_THEME_MESSAGE = {
    'WEKO_THEME_FAILED_SEARCH_ITEM': {
        'msgid': 'WEKO_THEME_E_0001',
        'msgstr': "FAILED to search item: {query}",
        'loglevel': 'ERROR',
    },
    'WEKO_THEME_FAILED_ADD_SEARCH_CONDITION': {
        'msgid': 'WEKO_THEME_E_0002',
        'msgstr': "FAILED to add search condition.",
        'loglevel': 'ERROR',
    },
    'WEKO_THEME_FAILED_DELETE_SEARCH_CONDITION': {
        'msgid': 'WEKO_THEME_E_0003',
        'msgstr': "FAILED to delete search condition.",
        'loglevel': 'ERROR',
    },
    'WEKO_THEME_FAILED_EXPORT_SEARCH_CONDITION': {
        'msgid': 'WEKO_THEME_E_0004',
        'msgstr': "FAILED to export items added to the search condition.",
        'loglevel': 'ERROR',
    },
    'WEKO_THEME_FAILED_INDEX_SEARCH': {
        'msgid': 'WEKO_THEME_E_0005',
        'msgstr': "FAILED to search item from index.",
        'loglevel': 'ERROR',
    },
    'WEKO_THEME_FAILED_SETTINGS_FACETED_SEARCH': {
        'msgid': 'WEKO_THEME_E_0006',
        'msgstr': "FAILED to change faceted search settings to {set_value}.",
        'loglevel': 'ERROR',
    },
    'WEKO_THEME_FAILED_CHANGE_ITEM_DISPLAY_SETTINGS': {
        'msgid': 'WEKO_THEME_E_0007',
        'msgstr': "FAILED to change item display method settings.",
        'loglevel': 'ERROR',
    },
    'WEKO_THEME_FAILED_OUTPUT_RSS_DOCUMENT': {
        'msgid': 'WEKO_THEME_E_0008',
        'msgstr': "FAILED to output RSS document.",
        'loglevel': 'ERROR',
    },
    'WEKO_THEME_FAILED_CREATE_WIDGET_TEMPLATE': {
        'msgid': 'WEKO_THEME_E_0009',
        'msgstr': "FAILED to create Widget templates.",
        'loglevel': 'ERROR',
    },
    'WEKO_THEME_FAILED_CHANGE_BACKGROUND_COLOUR': {
        'msgid': 'WEKO_THEME_E_0010',
        'msgstr': "FAILED to change screen background colour.",
        'loglevel': 'ERROR',
    },
    'WEKO_THEME_SEARCH_ITEM': {
        'msgid': 'WEKO_THEME_I_0001',
        'msgstr': "Search item: {query}, result: {num}",
        'loglevel': 'INFO',
    },
    'WEKO_THEME_ADD_SEARCH_CONDITION': {
        'msgid': 'WEKO_THEME_I_0002',
        'msgstr': "Search condition added.",
        'loglevel': 'INFO',
    },
    'WEKO_THEME_DELETE_SEARCH_CONDITION': {
        'msgid': 'WEKO_THEME_I_0003',
        'msgstr': "Search condition deleted.",
        'loglevel': 'INFO',
    },
    'WEKO_THEME_EXPORT_SEARCH_CONDITION': {
        'msgid': 'WEKO_THEME_I_0004',
        'msgstr': "Items added to the search condition have been exported.",
        'loglevel': 'INFO',
    },
    'WEKO_THEME_INDEX_SEARCH_RESULT': {
        'msgid': 'WEKO_THEME_I_0005',
        'msgstr': "index search : {query}, results: {num} items",
        'loglevel': 'INFO',
    },
    'WEKO_THEME_SETTINGS_FACETED_SEARCH': {
        'msgid': 'WEKO_THEME_I_0006',
        'msgstr': "Faceted search settings have been changed to {set_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_THEME_DETAIL_SETTINGS_FACETED_SEARCH': {
        'msgid': 'WEKO_THEME_I_0007',
        'msgstr': "Faceted search settings have been changed {section} to "\
            "{set_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_THEME_CHANGE_ITEM_DISPLAY_SETTINGS': {
        'msgid': 'WEKO_THEME_I_0008',
        'msgstr': "Settings for how items are displayed have been changed.",
        'loglevel': 'INFO',
    },
    'WEKO_THEME_ENABLED_RSS_FEEDS': {
        'msgid': 'WEKO_THEME_I_0009',
        'msgstr': "RSS feeds are now enabled.",
        'loglevel': 'INFO',
    },
    'WEKO_THEME_CHANGED_RSS_FEEDS_SETTING': {
        'msgid': 'WEKO_THEME_I_0010',
        'msgstr': "The RSS feeds has been changed to {configuration_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_THEME_CHANGED_RSS_FEEDS_DETAILS_SETTING': {
        'msgid': 'WEKO_THEME_I_0011',
        'msgstr': "The RSS feeds has been changed {section} to "\
            "{configuration_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_THEME_OUTPUT_RSS_DOCUMENT': {
        'msgid': 'WEKO_THEME_I_0012',
        'msgstr': "RSS document has been output.",
        'loglevel': 'INFO',
    },
    'WEKO_THEME_CREATE_WIDGET_TEMPLATE': {
        'msgid': 'WEKO_THEME_I_0013',
        'msgstr': "Widget templates have been created.",
        'loglevel': 'INFO',
    },
    'WEKO_THEME_REGISTER_PAGE_LAYOUT': {
        'msgid': 'WEKO_THEME_I_0014',
        'msgstr': "Page layout has been registered.",
        'loglevel': 'INFO',
    },
    'WEKO_THEME_USER_AGREE_COOKIE': {
        'msgid': 'WEKO_THEME_I_0015',
        'msgstr': "Cookie use has been agreed.",
        'loglevel': 'INFO',
    },
    'WEKO_THEME_USER_REFUSE_COOKIE': {
        'msgid': 'WEKO_THEME_I_0016',
        'msgstr': "Cookie usage refused.",
        'loglevel': 'INFO',
    },
    'WEKO_THEME_CHANGE_ORDER_ITEMS': {
        'msgid': 'WEKO_THEME_I_0017',
        'msgstr': "The order in which items are displayed has changed.",
        'loglevel': 'INFO',
    },
    'WEKO_THEME_CHANGE_BACKGROUND_COLOUR': {
        'msgid': 'WEKO_THEME_I_0018',
        'msgstr': "Screen background colour has changed.",
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
    param = WEKO_THEME_MESSAGE.get(key, None)
    if param:
        weko_logger_base(app=current_app, param=param, ex=ex, **kwargs)
    else:
        weko_logger_base(app=current_app, key=key, ex=ex, **kwargs)
