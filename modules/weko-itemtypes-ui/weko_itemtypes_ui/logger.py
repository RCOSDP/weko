# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Itemstypes-Ui is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Resource for weko-itemtypes_ui log messages."""

from flask import current_app


WEKO_ITEMTYPES_UI_MESSAGE = {
    'WEKO_ITEMTYPES_UI_FAILED_UPDATE_ITEM': {
        'msgid': 'WEKO_ITEMTYPES_UI_E_0001',
        'msgstr': "FAILED to update item: {pid}",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMTYPES_UI_FAILED_DELETE_ITEM': {
        'msgid': 'WEKO_ITEMTYPES_UI_E_0002',
        'msgstr': "FAILED to delete item: {pid}",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMTYPES_UI_FAILED_ADD_ITEM_TYPE': {
        'msgid': 'WEKO_ITEMTYPES_UI_E_0003',
        'msgstr': "FAILED to add item type.",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMTYPES_UI_FAILED_COPY_ITEM_TYPE': {
        'msgid': 'WEKO_ITEMTYPES_UI_E_0004',
        'msgstr': "FAILED to copy item type.",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMTYPES_UI_FAILED_SAVE_EDITS_TO_ITEM_TYPE': {
        'msgid': 'WEKO_ITEMTYPES_UI_E_0005',
        'msgstr': "FAILED to save edits to the item type.",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMTYPES_UI_FAILED_DELETE_ITEM_TYPE': {
        'msgid': 'WEKO_ITEMTYPES_UI_E_0006',
        'msgstr': "FAILED to delete item type.",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMTYPES_UI_FAILED_RESTORE_ITEM_TYPE': {
        'msgid': 'WEKO_ITEMTYPES_UI_E_0007',
        'msgstr': "Failed to restore logical deleted item type.",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMTYPES_UI_FAILED_ADD_PROPERTY': {
        'msgid': 'WEKO_ITEMTYPES_UI_E_0008',
        'msgstr': "FAILED to add property.",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMTYPES_UI_FAILED_EXPORT_ITEM_TYPE': {
        'msgid': 'WEKO_ITEMTYPES_UI_E_0009',
        'msgstr': "FAILED to export item type.",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMTYPES_UI_FAILED_IMPORT_ITEM_TYPE': {
        'msgid': 'WEKO_ITEMTYPES_UI_E_0010',
        'msgstr': "FAILED to import item type.",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMTYPES_UI_FAILED_SAVE_NEW_MAPPING': {
        'msgid': 'WEKO_ITEMTYPES_UI_E_0011',
        'msgstr': "FAILED to save new mapping.",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMTYPES_UI_FAILED_SAVE_PROPERTY_EDITS': {
        'msgid': 'WEKO_ITEMTYPES_UI_E_0012',
        'msgstr': "FAILED to save property edits.",
        'loglevel': 'ERROR',
    },
    'WEKO_ITEMTYPES_UI_UPDATE_ITEM': {
        'msgid': 'WEKO_ITEMTYPES_UI_I_0001',
        'msgstr': "Update item: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMTYPES_UI_DELETE_ITEM': {
        'msgid': 'WEKO_ITEMTYPES_UI_I_0002',
        'msgstr': "Delete item: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMTYPES_UI_ADD_ITEM_TYPE': {
        'msgid': 'WEKO_ITEMTYPES_UI_I_0003',
        'msgstr': "Item type {itemtype_name} added.",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMTYPES_UI_COPY_ITEM_TYPE': {
        'msgid': 'WEKO_ITEMTYPES_UI_I_0004',
        'msgstr': "Item type {itemtype_name} copied.",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMTYPES_UI_SAVED_EDITS_TO_ITEM_TYPE': {
        'msgid': 'WEKO_ITEMTYPES_UI_I_0005',
        'msgstr': "Edits to the item type {itemtype_name} have been saved.",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMTYPES_UI_DELETE_ITEM_TYPE': {
        'msgid': 'WEKO_ITEMTYPES_UI_I_0006',
        'msgstr': "Item type {itemtype_name} deleted.",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMTYPES_UI_RESTORE_ITEM_TYPE': {
        'msgid': 'WEKO_ITEMTYPES_UI_I_0007',
        'msgstr': "Logically deleted item type {itemtype_name} have been "\
            "restored.",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMTYPES_UI_ADD_PROPERTY': {
        'msgid': 'WEKO_ITEMTYPES_UI_I_0008',
        'msgstr': "Property has been added.",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMTYPES_UI_EXPORT_ITEM_TYPE': {
        'msgid': 'WEKO_ITEMTYPES_UI_I_0009',
        'msgstr': "Item type exported.",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMTYPES_UI_IMPORT_ITEM_TYPE': {
        'msgid': 'WEKO_ITEMTYPES_UI_I_0010',
        'msgstr': "Item type imported.",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMTYPES_UI_SAVED_NEW_MAPPING': {
        'msgid': 'WEKO_ITEMTYPES_UI_I_0011',
        'msgstr': "New mapping has been saved.",
        'loglevel': 'INFO',
    },
    'WEKO_ITEMTYPES_UI_SAVED_PROPERTY_EDITS': {
        'msgid': 'WEKO_ITEMTYPES_UI_I_0012',
        'msgstr': "Property edits have been saved.",
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
    param = WEKO_ITEMTYPES_UI_MESSAGE.get(key, None)
    if param:
        weko_logger_base(app=current_app, param=param, ex=ex, **kwargs)
    else:
        weko_logger_base(app=current_app, key=key, ex=ex, **kwargs)
