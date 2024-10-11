# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Index-Tree is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Resource for weko-index_tree log messages."""

from flask import current_app


WEKO_INDEX_TREE_MESSAGE = {
    'WEKO_INDEX_TREE_FAILED_INDEX_SEARCH': {
        'msgid': 'WEKO_INDEX_TREE_E_0001',
        'msgstr': "FAILED to search item from index.",
        'loglevel': 'ERROR',
    },
    'WEKO_INDEX_TREE_FAILED_OUTPUT_RSS_DOCUMENT': {
        'msgid': 'WEKO_INDEX_TREE_E_0002',
        'msgstr': "FAILED to output RSS document.",
        'loglevel': 'ERROR',
    },
    'WEKO_INDEX_TREE_FAILED_GET_DATA_FOR_RSS': {
        'msgid': 'WEKO_INDEX_TREE_E_0003',
        'msgstr': "FAILED to get data for RSS output.",
        'loglevel': 'ERROR',
    },
    'WEKO_INDEX_TREE_FAILED_UPDATE_ITEMS_IN_BULK': {
        'msgid': 'WEKO_INDEX_TREE_E_0004',
        'msgstr': "FAILED to update items in bulk",
        'loglevel': 'ERROR',
    },
    'WEKO_INDEX_TREE_FAILED_REGISTER_NEW_INDEX': {
        'msgid': 'WEKO_INDEX_TREE_E_0005',
        'msgstr': "FAILED to register new index in the index tree.",
        'loglevel': 'ERROR',
    },
    'WEKO_INDEX_TREE_FAILED_UPDATE_INDEX_TREE': {
        'msgid': 'WEKO_INDEX_TREE_E_0006',
        'msgstr': "FAILED to update index tree.",
        'loglevel': 'ERROR',
    },
    'WEKO_INDEX_TREE_FAILED_PUBLISH_INDEX': {
        'msgid': 'WEKO_INDEX_TREE_E_0007',
        'msgstr': "FAILED to publish index.",
        'loglevel': 'ERROR',
    },
    'WEKO_INDEX_TREE_FAILED_UPDATE_INDEX': {
        'msgid': 'WEKO_INDEX_TREE_E_0008',
        'msgstr': "FAILED to update index.",
        'loglevel': 'ERROR',
    },
    'WEKO_INDEX_TREE_FAILED_INDEX_NO_LONGER_PUBLISHED': {
        'msgid': 'WEKO_INDEX_TREE_E_0009',
        'msgstr': "FAILED to stop publishing the index.",
        'loglevel': 'ERROR',
    },
    'WEKO_INDEX_TREE_FAILED_MOVE_INDEX_TREE': {
        'msgid': 'WEKO_INDEX_TREE_E_0010',
        'msgstr': "FAILED to move index tree.",
        'loglevel': 'ERROR',
    },
    'WEKO_INDEX_TREE_FAILED_DELETE_INDEX_TREE': {
        'msgid': 'WEKO_INDEX_TREE_E_0011',
        'msgstr': "FAILED to delete index tree.",
        'loglevel': 'ERROR',
    },
    'WEKO_INDEX_TREE_FAILED_DISPLAY_INDEX_LINK': {
        'msgid': 'WEKO_INDEX_TREE_E_0012',
        'msgstr': "FAILED to change display setting of the index link.",
        'loglevel': 'ERROR',
    },
    'WEKO_INDEX_TREE_INDEX_SEARCH_RESULT': {
        'msgid': 'WEKO_INDEX_TREE_I_0001',
        'msgstr': "index search : {search_content}, results: {num} items",
        'loglevel': 'INFO',
    },
    'WEKO_INDEX_TREE_ENABLED_RSS_FEEDS': {
        'msgid': 'WEKO_INDEX_TREE_I_0002',
        'msgstr': "RSS feeds are now enabled.",
        'loglevel': 'INFO',
    },
    'WEKO_INDEX_TREE_CHANGED_RSS_FEEDS_SETTING': {
        'msgid': 'WEKO_INDEX_TREE_I_0003',
        'msgstr': "The RSS feeds has been changed to {configuration_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_INDEX_TREE_CHANGED_RSS_FEEDS_DETAILS_SETTING': {
        'msgid': 'WEKO_INDEX_TREE_I_0004',
        'msgstr': "The RSS feeds has been changed {section} to "\
            "{configuration_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_INDEX_TREE_OUTPUT_RSS_DOCUMENT': {
        'msgid': 'WEKO_INDEX_TREE_I_0005',
        'msgstr': "RSS document has been output.",
        'loglevel': 'INFO',
    },
    'WEKO_INDEX_TREE_GET_DATA_FOR_RSS': {
        'msgid': 'WEKO_INDEX_TREE_I_0006',
        'msgstr': "Got data for RSS output.",
        'loglevel': 'INFO',
    },
    'WEKO_INDEX_TREE_CHANGE_DISPLAY_SETTINGS_SEARCH_RESULTS': {
        'msgid': 'WEKO_INDEX_TREE_I_0007',
        'msgstr': "The display setting for search results has been changed "\
            "to {configuration_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_INDEX_TREE_CHANGE_DISPLAY_DETAIL_SETTINGS_SEARCH_RESULTS': {
        'msgid': 'WEKO_INDEX_TREE_I_0008',
        'msgstr': "The display setting for search results has been changed "\
            "{section} to {configuration_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_INDEX_TREE_UPDATE_ITEMS_IN_BULK': {
        'msgid': 'WEKO_INDEX_TREE_I_0009',
        'msgstr': "Items updated in bulk: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_INDEX_TREE_REGISTER_NEW_INDEX': {
        'msgid': 'WEKO_INDEX_TREE_I_0010',
        'msgstr': "New index is registered in the index tree.",
        'loglevel': 'INFO',
    },
    'WEKO_INDEX_TREE_UPDATE_INDEX_TREE': {
        'msgid': 'WEKO_INDEX_TREE_I_0011',
        'msgstr': "Index tree updated.",
        'loglevel': 'INFO',
    },
    'WEKO_INDEX_TREE_PUBLISH_INDEX': {
        'msgid': 'WEKO_INDEX_TREE_I_0012',
        'msgstr': "Index became open to public.",
        'loglevel': 'INFO',
    },
    'WEKO_INDEX_TREE_INDEX_NO_LONGER_PUBLISHED': {
        'msgid': 'WEKO_INDEX_TREE_I_0013',
        'msgstr': "Index is no longer published.",
        'loglevel': 'INFO',
    },
    'WEKO_INDEX_TREE_UPDATE_INDEX': {
        'msgid': 'WEKO_INDEX_TREE_I_0014',
        'msgstr': "Index updated.",
        'loglevel': 'INFO',
    },
    'WEKO_INDEX_TREE_DELETE_INDEX_TREE': {
        'msgid': 'WEKO_INDEX_TREE_I_0015',
        'msgstr': "Index tree deleted.",
        'loglevel': 'INFO',
    },
    'WEKO_INDEX_TREE_MOVED_INDEX_TREE': {
        'msgid': 'WEKO_INDEX_TREE_I_0016',
        'msgstr': "Index tree has been moved.",
        'loglevel': 'INFO',
    },
    'WEKO_INDEX_TREE_CHANGE_ORDER_ITEMS': {
        'msgid': 'WEKO_INDEX_TREE_I_0017',
        'msgstr': "The order in which items are displayed has changed.",
        'loglevel': 'INFO',
    },
    'WEKO_INDEX_TREE_CHANGE_DISPLAY_INDEX_LINK_SETTING': {
        'msgid': 'WEKO_INDEX_TREE_I_0018',
        'msgstr': "The display setting of the index link has been changed to "\
            "{configuration_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_INDEX_TREE_CHANGE_DISPLAY_INDEX_LINK_DETAIL_SETTING': {
        'msgid': 'WEKO_INDEX_TREE_I_0019',
        'msgstr': "The display setting of the index link has been changed "\
            "{section} to {configuration_value}.",
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
    param = WEKO_INDEX_TREE_MESSAGE.get(key, None)
    if param:
        weko_logger_base(app=current_app, param=param, ex=ex, **kwargs)
    else:
        weko_logger_base(app=current_app, key=key, ex=ex, **kwargs)
