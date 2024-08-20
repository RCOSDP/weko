# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Search-Ui is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Resource for weko-search_ui log messages."""

WEKO_SEARCH_UI_MESSAGE = {
    'WEKO_SEARCH_UI_FAILED_SEARCH_ITEM': {
        'msgid': 'WEKO_SEARCH_UI_E_0001',
        'msgstr': "FAILED to search item: {query}",
        'msglvl': 'ERROR',
    },
    'WEKO_SEARCH_UI_FAILED_ADD_SEARCH_CONDITION': {
        'msgid': 'WEKO_SEARCH_UI_E_0002',
        'msgstr': "FAILED to add search condition.",
        'msglvl': 'ERROR',
    },
    'WEKO_SEARCH_UI_FAILED_DELETE_SEARCH_CONDITION': {
        'msgid': 'WEKO_SEARCH_UI_E_0003',
        'msgstr': "FAILED to delete search condition.",
        'msglvl': 'ERROR',
    },
    'WEKO_SEARCH_UI_FAILED_EXPORT_SEARCH_CONDITION': {
        'msgid': 'WEKO_SEARCH_UI_E_0004',
        'msgstr': "FAILED to export items added to the search condition.",
        'msglvl': 'ERROR',
    },
    'WEKO_SEARCH_UI_FAILED_OUTPUT_RSS_DOCUMENT': {
        'msgid': 'WEKO_SEARCH_UI_E_0005',
        'msgstr': "FAILED to output RSS document.",
        'msglvl': 'ERROR',
    },
    'WEKO_SEARCH_UI_FAILED_INDEX_SEARCH': {
        'msgid': 'WEKO_SEARCH_UI_E_0006',
        'msgstr': "FAILED to search item from index.",
        'msglvl': 'ERROR',
    },
    'WEKO_SEARCH_UI_FAILED_SAVE_INDEX_SETTINGS': {
        'msgid': 'WEKO_SEARCH_UI_E_0007',
        'msgstr': "Failed to save changes to index settings.",
        'msglvl': 'ERROR',
    },
    'WEKO_SEARCH_UI_FAILED_DISPLAY_SETTINGS_JOURNAL_INFO': {
        'msgid': 'WEKO_SEARCH_UI_E_0008',
        'msgstr': "FAILED to change display settings of index {index_name} "\
            "for journal information to {conf_value}.",
        'msglvl': 'ERROR',
    },
    'WEKO_SEARCH_UI_FAILED_SAVE_JOURNAL_INFO': {
        'msgid': 'WEKO_SEARCH_UI_E_0009',
        'msgstr': "FAILED to save journal information. "\
            "Index name: {index_name}",
        'msglvl': 'ERROR',
    },
    'WEKO_SEARCH_UI_FAILED_OUTPUT _JOURNAL_INFO': {
        'msgid': 'WEKO_SEARCH_UI_E_0010',
        'msgstr': "FAILED to output journal information. "\
            "Index name: {index_name}",
        'msglvl': 'ERROR',
    },
    'WEKO_SEARCH_UI_FAILED_BULK_DELETE_ITEMS': {
        'msgid': 'WEKO_SEARCH_UI_E_0011',
        'msgstr': "FAILED to bulk delete items targeted at the index.",
        'msglvl': 'ERROR',
    },
    'WEKO_SEARCH_UI_FAILED_EXPORT_FULL_ITEM': {
        'msgid': 'WEKO_SEARCH_UI_E_0012',
        'msgstr': "FAILED to export all items.",
        'msglvl': 'ERROR',
    },
    'WEKO_SEARCH_UI_FAILED_CANCEL_EXPORT_FULL_ITEM': {
        'msgid': 'WEKO_SEARCH_UI_E_0013',
        'msgstr': "FAILED to cancel full export of the item.",
        'msglvl': 'ERROR',
    },
    'WEKO_SEARCH_UI_FAILED_BULK_IMPORT_ITEMS': {
        'msgid': 'WEKO_SEARCH_UI_E_0014',
        'msgstr': "FAILED to bulk umport items.",
        'msglvl': 'ERROR',
    },
    'WEKO_SEARCH_UI_FAILED_DOWNLOAD_ITEM_ON_SCREEN': {
        'msgid': 'WEKO_SEARCH_UI_E_0015',
        'msgstr': "FAILED to download list of items displayed on the screen "\
            "in TSV format.",
        'msglvl': 'ERROR',
    },
    'WEKO_SEARCH_UI_FAILED_REGISTER_NEW_INDEX': {
        'msgid': 'WEKO_SEARCH_UI_E_0016',
        'msgstr': "FAILED to register new index in the index tree.",
        'msglvl': 'ERROR',
    },
    'WEKO_SEARCH_UI_FAILED_UPDATE_INDEX_TREE': {
        'msgid': 'WEKO_SEARCH_UI_E_0017',
        'msgstr': "FAILED to update index tree.",
        'msglvl': 'ERROR',
    },
    'WEKO_SEARCH_UI_FAILED_PUBLISH_INDEX': {
        'msgid': 'WEKO_SEARCH_UI_E_0018',
        'msgstr': "FAILED to publish index.",
        'msglvl': 'ERROR',
    },
    'WEKO_SEARCH_UI_FAILED_UPDATE_INDEX': {
        'msgid': 'WEKO_SEARCH_UI_E_0019',
        'msgstr': "FAILED to update index.",
        'msglvl': 'ERROR',
    },
    'WEKO_SEARCH_UI_FAILED_INDEX_NO_LONGER_PUBLISHED': {
        'msgid': 'WEKO_SEARCH_UI_E_0020',
        'msgstr': "FAILED to stop publishing the index.",
        'msglvl': 'ERROR',
    },
    'WEKO_SEARCH_UI_FAILED_MOVE_INDEX_TREE': {
        'msgid': 'WEKO_SEARCH_UI_E_0021',
        'msgstr': "FAILED to move index tree.",
        'msglvl': 'ERROR',
    },
    'WEKO_SEARCH_UI_FAILED_DELETE_INDEX_TREE': {
        'msgid': 'WEKO_SEARCH_UI_E_0022',
        'msgstr': "FAILED to delete index tree.",
        'msglvl': 'ERROR',
    },
    'WEKO_SEARCH_UI_SEARCH_ITEM': {
        'msgid': 'WEKO_SEARCH_UI_I_0001',
        'msgstr': "Search item: {query}, result: {num}",
        'msglvl': 'INFO',
    },
    'WEKO_SEARCH_UI_ADD_SEARCH_CONDITION': {
        'msgid': 'WEKO_SEARCH_UI_I_0002',
        'msgstr': "Search condition added.",
        'msglvl': 'INFO',
    },
    'WEKO_SEARCH_UI_DELETE_SEARCH_CONDITION': {
        'msgid': 'WEKO_SEARCH_UI_I_0003',
        'msgstr': "Search condition deleted.",
        'msglvl': 'INFO',
    },
    'WEKO_SEARCH_UI_EXPORT_SEARCH_CONDITION': {
        'msgid': 'WEKO_SEARCH_UI_I_0004',
        'msgstr': "Items added to the search condition have been exported.",
        'msglvl': 'INFO',
    },
    'WEKO_SEARCH_UI_ENABLED_RSS_FEEDS': {
        'msgid': 'WEKO_SEARCH_UI_I_0005',
        'msgstr': "RSS feeds are now enabled.",
        'msglvl': 'INFO',
    },
    'WEKO_SEARCH_UI_OUTPUT_RSS_DOCUMENT': {
        'msgid': 'WEKO_SEARCH_UI_I_0006',
        'msgstr': "RSS document has been output.",
        'msglvl': 'INFO',
    },
    'WEKO_SEARCH_UI_INDEX_SEARCH_RESULT': {
        'msgid': 'WEKO_SEARCH_UI_I_0007',
        'msgstr': "index search : {search_content}, results: {num} items",
        'msglvl': 'INFO',
    },
    'WEKO_SEARCH_UI_CHANGE_DISPLAY_SETTINGS_SEARCH_RESULTS': {
        'msgid': 'WEKO_SEARCH_UI_I_0008',
        'msgstr': "The display setting for search results has been changed "\
            "to {conf_value}.",
        'msglvl': 'INFO',
    },
    'WEKO_SEARCH_UI_DISPLAY_SETTINGS_JOURNAL_INFO': {
        'msgid': 'WEKO_SEARCH_UI_I_0009',
        'msgstr': "Display settings of index {index_name} for journal "\
            "information has been changed to {conf_value}.",
        'msglvl': 'INFO',
    },
    'WEKO_SEARCH_UI_SAVE_JOURNAL_INFO': {
        'msgid': 'WEKO_SEARCH_UI_I_0010',
        'msgstr': "Journal information edited. Index name: {index_name}",
        'msglvl': 'INFO',
    },
    'WEKO_SEARCH_UI_OUTPUT _JOURNAL_INFO': {
        'msgid': 'WEKO_SEARCH_UI_I_0011',
        'msgstr': "Journal information has been output. "\
            "Index name: {index_name}",
        'msglvl': 'INFO',
    },
    'WEKO_SEARCH_UI_BULK_DELETE_ITEMS': {
        'msgid': 'WEKO_SEARCH_UI_I_0012',
        'msgstr': "Bulk deletion of items targeted at the index was "\
            "successful.",
        'msglvl': 'INFO',
    },
    'WEKO_SEARCH_UI_EXPORT_FULL_ITEM': {
        'msgid': 'WEKO_SEARCH_UI_I_0013',
        'msgstr': "Full export of the item has been performed.",
        'msglvl': 'INFO',
    },
    'WEKO_SEARCH_UI_CANCEL_EXPORT_FULL_ITEM': {
        'msgid': 'WEKO_SEARCH_UI_I_0014',
        'msgstr': "Full export of the item has been cancelled.",
        'msglvl': 'INFO',
    },
    'WEKO_SEARCH_UI_BULK_IMPORT_ITEMS': {
        'msgid': 'WEKO_SEARCH_UI_I_0015',
        'msgstr': "Bulk import of items has been done.",
        'msglvl': 'INFO',
    },
    'WEKO_SEARCH_UI_DOWNLOAD_ITEM_ON_SCREEN': {
        'msgid': 'WEKO_SEARCH_UI_I_0016',
        'msgstr': "List of items displayed on the screen has been downloaded "\
            "in TSV format.",
        'msglvl': 'INFO',
    },
    'WEKO_SEARCH_UI_REGISTER_NEW_INDEX': {
        'msgid': 'WEKO_SEARCH_UI_I_0017',
        'msgstr': "New index is registered in the index tree.",
        'msglvl': 'INFO',
    },
    'WEKO_SEARCH_UI_UPDATE_INDEX_TREE': {
        'msgid': 'WEKO_SEARCH_UI_I_0018',
        'msgstr': "Index tree updated.",
        'msglvl': 'INFO',
    },
    'WEKO_SEARCH_UI_PUBLISH_INDEX': {
        'msgid': 'WEKO_SEARCH_UI_I_0019',
        'msgstr': "Index became open to public.",
        'msglvl': 'INFO',
    },
    'WEKO_SEARCH_UI_INDEX_NO_LONGER_PUBLISHED': {
        'msgid': 'WEKO_SEARCH_UI_I_0020',
        'msgstr': "Index is no longer published.",
        'msglvl': 'INFO',
    },
    'WEKO_SEARCH_UI_UPDATE_INDEX': {
        'msgid': 'WEKO_SEARCH_UI_I_0021',
        'msgstr': "Index updated.",
        'msglvl': 'INFO',
    },
    'WEKO_SEARCH_UI_DELETE_INDEX_TREE': {
        'msgid': 'WEKO_SEARCH_UI_I_0022',
        'msgstr': "Index tree deleted.",
        'msglvl': 'INFO',
    },
    'WEKO_SEARCH_UI_MOVED_INDEX_TREE': {
        'msgid': 'WEKO_SEARCH_UI_I_0023',
        'msgstr': "Index tree has been moved.",
        'msglvl': 'INFO',
    },
    'WEKO_SEARCH_UI_CHANGE_ORDER_ITEMS': {
        'msgid': 'WEKO_SEARCH_UI_I_0024',
        'msgstr': "The order in which items are displayed has changed.",
        'msglvl': 'INFO',
    },
}

from weko_logging.lggr import weko_logger_base

def weko_logger(key=None, ex=None, **kwargs):
    """Log message with key.

    Method to output logs in current_app.logger using the resource.

    Args:
        key (str): key of message.
            Not required if ex is specified.
        ex (Exception): exception object.
            If you catch an exception, specify it here.
        **kwargs: message parameters.
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
    param = WEKO_SEARCH_UI_MESSAGE.get(key, None)
    if param:
        weko_logger_base(param=param, ex=ex, **kwargs)
    else:
        weko_logger_base(key=key, ex=ex, **kwargs)
