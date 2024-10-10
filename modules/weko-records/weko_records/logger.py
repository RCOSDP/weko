# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Resource for weko-records log messages."""

from flask import current_app


WEKO_RECORDS_MESSAGE = {
    'WEKO_RECORDS_FAILED_SEARCH_ITEM': {
        'msgid': 'WEKO_RECORDS_E_0001',
        'msgstr': "FAILED to search item: {query}",
        'loglevel': 'ERROR',
    },
    'WEKO_RECORDS_FAILED_OUTPUT_RSS_DOCUMENT': {
        'msgid': 'WEKO_RECORDS_E_0002',
        'msgstr': "FAILED to output RSS document.",
        'loglevel': 'ERROR',
    },
    'WEKO_RECORDS_FAILED_SERIALIZE_RESULT_TO_RSS': {
        'msgid': 'WEKO_RECORDS_E_0003',
        'msgstr': "FAILED to serialize search results into RSS format.",
        'loglevel': 'ERROR',
    },
    'WEKO_RECORDS_FAILED_DELETE_RECORD': {
        'msgid': 'WEKO_RECORDS_E_0004',
        'msgstr': "FAILED to delete records. Uuid: {uuid}",
        'loglevel': 'ERROR',
    },
    'WEKO_RECORDS_FAILED_RESTORE_RECORD': {
        'msgid': 'WEKO_RECORDS_E_0005',
        'msgstr': "FAILED to restore record. Uuid: {uuid}",
        'loglevel': 'ERROR',
    },
    'WEKO_RECORDS_SEARCH_ITEM': {
        'msgid': 'WEKO_RECORDS_I_0001',
        'msgstr': "Search item: {query}, result: {num}",
        'loglevel': 'INFO',
    },
    'WEKO_RECORDS_ENABLED_RSS_FEEDS': {
        'msgid': 'WEKO_RECORDS_I_0002',
        'msgstr': "RSS feeds are now enabled.",
        'loglevel': 'INFO',
    },
    'WEKO_RECORDS_CHANGED_RSS_FEEDS_SETTING': {
        'msgid': 'WEKO_RECORDS_I_0003',
        'msgstr': "The RSS feeds has been changed to {configuration_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_RECORDS_CHANGED_RSS_FEEDS_DETAILS_SETTING': {
        'msgid': 'WEKO_RECORDS_I_0004',
        'msgstr': "The RSS feeds has been changed {section} to "\
            "{configuration_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_RECORDS_OUTPUT_RSS_DOCUMENT': {
        'msgid': 'WEKO_RECORDS_I_0005',
        'msgstr': "RSS document has been output.",
        'loglevel': 'INFO',
    },
    'WEKO_RECORDS_SERIALIZE_RESULT_TO_RSS': {
        'msgid': 'WEKO_RECORDS_I_0006',
        'msgstr': "Serialized search results into RSS format.",
        'loglevel': 'INFO',
    },
    'WEKO_RECORDS_DELETE_RECORD': {
        'msgid': 'WEKO_RECORDS_I_0007',
        'msgstr': "{delete_num} record was deleted. Uuid: {uuid}",
        'loglevel': 'INFO',
    },
    'WEKO_RECORDS_RESTORE_RECORD': {
        'msgid': 'WEKO_RECORDS_I_0008',
        'msgstr': "Record restored. Uuid: {uuid}",
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
    param = WEKO_RECORDS_MESSAGE.get(key, None)
    if param:
        weko_logger_base(app=current_app, param=param, ex=ex, **kwargs)
    else:
        weko_logger_base(app=current_app, key=key, ex=ex, **kwargs)
