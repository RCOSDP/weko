# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Sitemap is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Resource for weko-sitemap log messages."""

from flask import current_app


WEKO_SITEMAP_MESSAGE = {
    'WEKO_SITEMAP_FAILED_GENERATE_SITEMAP': {
        'msgid': 'WEKO_SITEMAP_E_0001',
        'msgstr': "FAILED sitemap generation.",
        'loglevel': 'ERROR',
    },
    'WEKO_SITEMAP_GENERATE_SITEMAP': {
        'msgid': 'WEKO_SITEMAP_I_0001',
        'msgstr': "Sitemap has been generated.",
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
    param = WEKO_SITEMAP_MESSAGE.get(key, None)
    if param:
        weko_logger_base(app=current_app, param=param, ex=ex, **kwargs)
    else:
        weko_logger_base(app=current_app, key=key, ex=ex, **kwargs)
