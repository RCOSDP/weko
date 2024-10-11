# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Items-Autofill is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Resource for weko-items_autofill log messages."""

from flask import current_app


WEKO_ITEMS_AUTOFILL_MESSAGE = {
    'WEKO_ITEMS_AUTOFILL_FAILED_SET_WEB_API_ACCOUNT_INFO': {
        'msgid': 'WEKO_ITEMS_AUTOFILL_E_0001',
        'msgstr': "FAILED to save Web API account information. Itemid: {pid}",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMS_AUTOFILL_FAILED_POPULATE_AUTO_METADATA_CROSSREF': {
        'msgid': 'WEKO_ITEMS_AUTOFILL_E_0002',
        'msgstr': "FAILED to automatically populate metadata via CrossRef. "\
            "Itemid: {pid}",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMS_AUTOFILL_FAILED_POPULATE_AUTO_METADATA_CINII': {
        'msgid': 'WEKO_ITEMS_AUTOFILL_E_0003',
        'msgstr': "FAILED to automatically populate metadata via CiNii. "\
            "Itemid: {pid}",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMS_AUTOFILL_FAILED_POPULATE_AUTO_METADATA_WEKOID': {
        'msgid': 'WEKO_ITEMS_AUTOFILL_E_0004',
        'msgstr': "FAILED to automatically populate metadata via WEKOID. "\
            "Itemid: {pid}",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMS_AUTOFILL_SET_WEB_API_ACCOUNT_INFO': {
        'msgid': 'WEKO_ITEMS_AUTOFILL_I_0001',
        'msgstr': "Web API account information has been set. "\
            "Itemid: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMS_AUTOFILL_POPULATE_AUTO_METADATA_CROSSREF': {
        'msgid': 'WEKO_ITEMS_AUTOFILL_I_0002',
        'msgstr': "Metadata was automatically populated via CrossRef. "\
            "Itemid: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMS_AUTOFILL_POPULATE_AUTO_METADATA_CINII': {
        'msgid': 'WEKO_ITEMS_AUTOFILL_I_0003',
        'msgstr': "Metadata was automatically populated via CiNii. "\
            "Itemid: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMS_AUTOFILL_POPULATE_AUTO_METADATA_WEKOID': {
        'msgid': 'WEKO_ITEMS_AUTOFILL_I_0004',
        'msgstr': "Metadata was automatically populated via WEKOID. "\
            "Itemid: {pid}",
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
    param = WEKO_ITEMS_AUTOFILL_MESSAGE.get(key, None)
    if param:
        weko_logger_base(app=current_app, param=param, ex=ex, **kwargs)
    else:
        weko_logger_base(app=current_app, key=key, ex=ex, **kwargs)
