# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Items-Ui is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Resource for weko-items_ui log messages."""

from flask import current_app


WEKO_ITEMS_UI_MESSAGE = {
    'WEKO_ITEMS_UI_FAILED_SEARCH_ITEM': {
        'msgid': 'WEKO_ITEMS_UI_E_0001',
        'msgstr': "FAILED to search item: {query}",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMS_UI_FAILED_ADD_SEARCH_CONDITION': {
        'msgid': 'WEKO_ITEMS_UI_E_0002',
        'msgstr': "FAILED to add search condition.",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMS_UI_FAILED_DELETE_SEARCH_CONDITION': {
        'msgid': 'WEKO_ITEMS_UI_E_0003',
        'msgstr': "FAILED to delete search condition.",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMS_UI_FAILED_EXPORT_SEARCH_CONDITION': {
        'msgid': 'WEKO_ITEMS_UI_E_0004',
        'msgstr': "FAILED to export items added to the search condition.",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMS_UI_FAILED_SETTINGS_FACETED_SEARCH': {
        'msgid': 'WEKO_ITEMS_UI_E_0005',
        'msgstr': "FAILED to change faceted search settings to {set_value}.",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMS_UI_FAILED_CHANGE_ITEM_DISPLAY_SETTINGS': {
        'msgid': 'WEKO_ITEMS_UI_E_0006',
        'msgstr': "FAILED to change item display method settings.",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMS_UI_FAILED_OUTPUT_RSS_DOCUMENT': {
        'msgid': 'WEKO_ITEMS_UI_E_0007',
        'msgstr': "Failed to output RSS for the item corresponding to the "\
            "search result.",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMS_UI_FAILED_OUTPUT_RSS_DOCUMENT': {
        'msgid': 'WEKO_ITEMS_UI_E_0008',
        'msgstr': "FAILED to output RSS document.",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMS_UI_FAILED_SAVE_INDEX_SETTINGS': {
        'msgid': 'WEKO_ITEMS_UI_E_0009',
        'msgstr': "Failed to save changes to index settings.",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMS_UI_FAILED_SAVE_INDEX': {
        'msgid': 'WEKO_ITEMS_UI_E_0010',
        'msgstr': "FAILED to save index designation: {pid}",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMS_UI_FAILED_POPULATE_AUTO_METADATA_CROSSREF': {
        'msgid': 'WEKO_ITEMS_UI_E_0011',
        'msgstr': "FAILED to automatically populate metadata via CrossRef. "\
            "Itemid: {pid}",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMS_UI_FAILED_POPULATE_AUTO_METADATA_CINII': {
        'msgid': 'WEKO_ITEMS_UI_E_0012',
        'msgstr': "FAILED to automatically populate metadata via CiNii. "\
            "Itemid: {pid}",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMS_UI_FAILED_POPULATE_AUTO_METADATA_WEKOID': {
        'msgid': 'WEKO_ITEMS_UI_E_0013',
        'msgstr': "FAILED to automatically populate metadata via WEKOID. "\
            "Itemid: {pid}",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMS_UI_FAILED_EXPORT_ITEM_IN_JSON': {
        'msgid': 'WEKO_ITEMS_UI_E_0014',
        'msgstr': "FAILED to export selected items in json format.",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMS_UI_FAILED_EXPORT_ITEM_IN_BIBTEX': {
        'msgid': 'WEKO_ITEMS_UI_E_0015',
        'msgstr': "FAILED to export selected items in bibtex format.",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMS_UI_FAILED_ASSIGN_PROXY_CONTRIBUTOR': {
        'msgid': 'WEKO_ITEMS_UI_E_0016',
        'msgstr': "Failed to assign a proxy contributor for the item.",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMS_UI_FAILED_REGISTER_INDEX': {
        'msgid': 'WEKO_ITEMS_UI_E_0017',
        'msgstr': "FAILED to register index designation: {pid}",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMS_UI_FAILED_SAVE_RANKING_SETTINGS': {
        'msgid': 'WEKO_ITEMS_UI_E_0018',
        'msgstr': "FAILED to save ranking settings.",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMS_UI_FAILED_CREATE_RANKING_LISTS': {
        'msgid': 'WEKO_ITEMS_UI_E_0019',
        'msgstr': "FAILED to create ranking lists.",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMS_UI_SEARCH_ITEM': {
        'msgid': 'WEKO_ITEMS_UI_I_0001',
        'msgstr': "Search item: {query}, result: {num}",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMS_UI_ADD_SEARCH_CONDITION': {
        'msgid': 'WEKO_ITEMS_UI_I_0002',
        'msgstr': "Search condition added.",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMS_UI_DELETE_SEARCH_CONDITION': {
        'msgid': 'WEKO_ITEMS_UI_I_0003',
        'msgstr': "Search condition deleted.",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMS_UI_EXPORT_SEARCH_CONDITION': {
        'msgid': 'WEKO_ITEMS_UI_I_0004',
        'msgstr': "Items added to the search condition have been exported.",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMS_UI_CHANGE_ITEM_DISPLAY_SETTINGS': {
        'msgid': 'WEKO_ITEMS_UI_I_0005',
        'msgstr': "Settings for how items are displayed have been changed.",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMS_UI_OUTPUT_RSS_DOCUMENT': {
        'msgid': 'WEKO_ITEMS_UI_I_0006',
        'msgstr': "RSS output for items corresponding to the search results.",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMS_UI_ENABLED_RSS_FEEDS': {
        'msgid': 'WEKO_ITEMS_UI_I_0007',
        'msgstr': "RSS feeds are now enabled.",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMS_UI_CHANGED_RSS_FEEDS_SETTING': {
        'msgid': 'WEKO_ITEMS_UI_I_0008',
        'msgstr': "The RSS feeds has been changed to {configuration_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMS_UI_CHANGED_RSS_FEEDS_DETAILS_SETTING': {
        'msgid': 'WEKO_ITEMS_UI_I_0009',
        'msgstr': "The RSS feeds has been changed {section} to "\
            "{configuration_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMS_UI_OUTPUT_RSS_DOCUMENT': {
        'msgid': 'WEKO_ITEMS_UI_I_0010',
        'msgstr': "RSS document has been output.",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMS_UI_CHANGE_DISPLAY_SETTINGS_SEARCH_RESULTS': {
        'msgid': 'WEKO_ITEMS_UI_I_0011',
        'msgstr': "The display setting for search results has been changed "\
            "to {configuration_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMS_UI_CHANGE_DISPLAY_DETAIL_SETTING _SEARCH_RESULTS': {
        'msgid': 'WEKO_ITEMS_UI_I_0012',
        'msgstr': "The display setting for search results has been changed "\
            "{section} to {configuration_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMS_UI_ENABLE_ITEM_EXPORT': {
        'msgid': 'WEKO_ITEMS_UI_I_0013',
        'msgstr': "Item export is now enabled.",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMS_UI_DISABLE_ITEM_EXPORT': {
        'msgid': 'WEKO_ITEMS_UI_I_0014',
        'msgstr': "Item export is now disabled.",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMS_UI_SAVED_INDEX': {
        'msgid': 'WEKO_ITEMS_UI_I_0015',
        'msgstr': "Index designation saved: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMS_UI_QUIT_INDEX': {
        'msgid': 'WEKO_ITEMS_UI_I_0016',
        'msgstr': "Index designation quitted: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMS_UI_POPULATE_AUTO_METADATA_CROSSREF': {
        'msgid': 'WEKO_ITEMS_UI_I_0017',
        'msgstr': "Metadata was automatically populated via CrossRef. "\
            "Itemid: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMS_UI_POPULATE_AUTO_METADATA_CINII': {
        'msgid': 'WEKO_ITEMS_UI_I_0018',
        'msgstr': "Metadata was automatically populated via CiNii. "\
            "Itemid: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMS_UI_POPULATE_AUTO_METADATA_WEKOID': {
        'msgid': 'WEKO_ITEMS_UI_I_0019',
        'msgstr': "Metadata was automatically populated via WEKOID. "\
            "Itemid: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMS_UI_EXPORT_ITEM_IN_JSON': {
        'msgid': 'WEKO_ITEMS_UI_I_0020',
        'msgstr': "Selected items have been exported in json format.",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMS_UI_EXPORT_ITEM_IN_BIBTEX': {
        'msgid': 'WEKO_ITEMS_UI_I_0021',
        'msgstr': "Selected items have been exported in bibtex format.",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMS_UI_EXPORT_ITEM_IN_JSON_WITH_FILE_CONTENTS': {
        'msgid': 'WEKO_ITEMS_UI_I_0022',
        'msgstr': "Selected items have been exported in json format with "\
            "File Contents.",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMS_UI_EXPORT_ITEM_IN_BIBTEX_WITH_FILE_CONTENTS': {
        'msgid': 'WEKO_ITEMS_UI_I_0023',
        'msgstr': "Selected items have been exported in bibtex format with "\
            "File Contents.",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMS_UI_ASSIGN_PROXY_CONTRIBUTOR': {
        'msgid': 'WEKO_ITEMS_UI_I_0024',
        'msgstr': "A proxy contributor has been assigned for the item: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMS_UI_REGISTER_INDEX': {
        'msgid': 'WEKO_ITEMS_UI_I_0025',
        'msgstr': "Destination index has been registered: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMS_UI_SAVED_RANKING_SETTINGS': {
        'msgid': 'WEKO_ITEMS_UI_I_0026',
        'msgstr': "Ranking settings have been saved.",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMS_UI_CREATED_RANKING_LISTS': {
        'msgid': 'WEKO_ITEMS_UI_I_0027',
        'msgstr': "Ranking lists have been created.",
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
    param = WEKO_ITEMS_UI_MESSAGE.get(key, None)
    if param:
        weko_logger_base(app=current_app, param=param, ex=ex, **kwargs)
    else:
        weko_logger_base(app=current_app, key=key, ex=ex, **kwargs)
