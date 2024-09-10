# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Schema-Ui is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Resource for weko-schema_ui log messages."""

from flask import current_app


WEKO_SCHEMA_UI_MESSAGE = {
    'WEKO_SCHEMA_UI_FAILED_ADD_SEARCH_CONDITION': {
        'msgid': 'WEKO_SCHEMA_UI_E_0001',
        'msgstr': "FAILED to add search condition.",
        'loglevel': 'ERROR',
    },
    'WEKO_SCHEMA_UI_FAILED_DELETE_SEARCH_CONDITION': {
        'msgid': 'WEKO_SCHEMA_UI_E_0002',
        'msgstr': "FAILED to delete search condition.",
        'loglevel': 'ERROR',
    },
    'WEKO_SCHEMA_UI_FAILED_EXPORT_SEARCH_CONDITION': {
        'msgid': 'WEKO_SCHEMA_UI_E_0003',
        'msgstr': "FAILED to export items added to the search condition.",
        'loglevel': 'ERROR',
    },
    'WEKO_SCHEMA_UI_FAILED_MAP_JPCOARSCHEMA_SEARCH': {
        'msgid': 'WEKO_SCHEMA_UI_E_0004',
        'msgstr': "FAILED to map JPCOAR schema for search.",
        'loglevel': 'ERROR',
    },
    'WEKO_SCHEMA_UI_FAILED_OUTPUT_RSS_DOCUMENT': {
        'msgid': 'WEKO_SCHEMA_UI_E_0005',
        'msgstr': "FAILED to output RSS document.",
        'loglevel': 'ERROR',
    },
    'WEKO_SCHEMA_UI_FAILED_ADD_OAISCHEMA': {
        'msgid': 'WEKO_SCHEMA_UI_E_0006',
        'msgstr': "FAILED to add OAI schema.",
        'loglevel': 'ERROR',
    },
    'WEKO_SCHEMA_UI_ADD_SEARCH_CONDITION': {
        'msgid': 'WEKO_SCHEMA_UI_I_0001',
        'msgstr': "Search condition added.",
        'loglevel': 'INFO',
    },
    'WEKO_SCHEMA_UI_DELETE_SEARCH_CONDITION': {
        'msgid': 'WEKO_SCHEMA_UI_I_0002',
        'msgstr': "Search condition deleted.",
        'loglevel': 'INFO',
    },
    'WEKO_SCHEMA_UI_EXPORT_SEARCH_CONDITION': {
        'msgid': 'WEKO_SCHEMA_UI_I_0003',
        'msgstr': "Items added to the search condition have been exported.",
        'loglevel': 'INFO',
    },
    'WEKO_SCHEMA_UI_MAPPED_JPCOARSCHEMA_SEARCH': {
        'msgid': 'WEKO_SCHEMA_UI_I_0004',
        'msgstr': "Successfully mapped JPCOAR schema for search.",
        'loglevel': 'INFO',
    },
    'WEKO_SCHEMA_UI_ENABLED_RSS_FEEDS': {
        'msgid': 'WEKO_SCHEMA_UI_I_0005',
        'msgstr': "RSS feeds are now enabled.",
        'loglevel': 'INFO',
    },
    'WEKO_SCHEMA_UI_OUTPUT_RSS_DOCUMENT': {
        'msgid': 'WEKO_SCHEMA_UI_I_0006',
        'msgstr': "RSS document has been output.",
        'loglevel': 'INFO',
    },
    'WEKO_SCHEMA_UI_ADD_OAISCHEMA_SUCCESS': {
        'msgid': 'WEKO_SCHEMA_UI_I_0007',
        'msgstr': "The OAI schema was successfully added.",
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
    param = WEKO_SCHEMA_UI_MESSAGE.get(key, None)
    if param:
        weko_logger_base(app=current_app, param=param, ex=ex, **kwargs)
    else:
        weko_logger_base(app=current_app, key=key, ex=ex, **kwargs)
