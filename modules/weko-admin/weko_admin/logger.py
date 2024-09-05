# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Admin is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Resource for weko-admin log messages."""

from flask import current_app


WEKO_ADMIN_MESSAGE = {
    'WEKO_ADMIN_FAILED_FEEDBACK_ADDRESS_SET': {
        'msgid': 'WEKO_ADMIN_E_0001',
        'msgstr': "Failed to set address for Feedback email.",
        'loglevel': 'ERROR',
    },
    'WEKO_ADMIN_FAILED_REGISTER_NEW_INDEX': {
        'msgid': 'WEKO_ADMIN_E_0002',
        'msgstr': "FAILED to register new index in the index tree.",
        'loglevel': 'ERROR',
    },
    'WEKO_ADMIN_FAILED_UPDATE_INDEX_TREE': {
        'msgid': 'WEKO_ADMIN_E_0003',
        'msgstr': "FAILED to update index tree.",
        'loglevel': 'ERROR',
    },
    'WEKO_ADMIN_FAILED_PUBLISH_INDEX': {
        'msgid': 'WEKO_ADMIN_E_0004',
        'msgstr': "FAILED to publish index.",
        'loglevel': 'ERROR',
    },
    'WEKO_ADMIN_FAILED_UPDATE_INDEX': {
        'msgid': 'WEKO_ADMIN_E_0005',
        'msgstr': "FAILED to update index.",
        'loglevel': 'ERROR',
    },
    'WEKO_ADMIN_FAILED_INDEX_NO_LONGER_PUBLISHED': {
        'msgid': 'WEKO_ADMIN_E_0006',
        'msgstr': "FAILED to stop publishing the index.",
        'loglevel': 'ERROR',
    },
    'WEKO_ADMIN_FAILED_MOVE_INDEX_TREE': {
        'msgid': 'WEKO_ADMIN_E_0007',
        'msgstr': "FAILED to move index tree.",
        'loglevel': 'ERROR',
    },
    'WEKO_ADMIN_FAILED_DELETE_INDEX_TREE': {
        'msgid': 'WEKO_ADMIN_E_0008',
        'msgstr': "FAILED to delete index tree.",
        'loglevel': 'ERROR',
    },
    'WEKO_ADMIN_FAILED_SAVE_RANKING_SETTINGS': {
        'msgid': 'WEKO_ADMIN_E_0009',
        'msgstr': "FAILED to save ranking settings.",
        'loglevel': 'ERROR',
    },
    'WEKO_ADMIN_FAILED_EXPORT_FULL_ITEM': {
        'msgid': 'WEKO_ADMIN_E_0010',
        'msgstr': "FAILED to export all items.",
        'loglevel': 'ERROR',
    },
    'WEKO_ADMIN_FAILED_CANCEL_EXPORT_FULL_ITEM': {
        'msgid': 'WEKO_ADMIN_E_0011',
        'msgstr': "FAILED to cancel full export of the item.",
        'loglevel': 'ERROR',
    },
    'WEKO_ADMIN_FAILED_BULK_IMPORT_ITEMS': {
        'msgid': 'WEKO_ADMIN_E_0012',
        'msgstr': "FAILED to bulk umport items.",
        'loglevel': 'ERROR',
    },
    'WEKO_ADMIN_FAILED_DOWNLOAD_ITEM_ON_SCREEN': {
        'msgid': 'WEKO_ADMIN_E_0013',
        'msgstr': "FAILED to download list of items displayed on the screen "\
            "in TSV format.",
        'loglevel': 'ERROR',
    },
    'WEKO_ADMIN_FAILED_REFERENCE_NUM_ITEMS_REGISTERED': {
        'msgid': 'WEKO_ADMIN_E_0014',
        'msgstr': "FAILED to reference the number of items registered.",
        'loglevel': 'ERROR',
    },
    'WEKO_ADMIN_FAILED_DOWNLOAD_FIX_FORM_REPORTS': {
        'msgid': 'WEKO_ADMIN_E_0015',
        'msgstr': "FAILED to download Fixed Form Reports.",
        'loglevel': 'ERROR',
    },
    'WEKO_ADMIN_FAILED_SET_UP_CUSTOM_REPORT': {
        'msgid': 'WEKO_ADMIN_E_0016',
        'msgstr': "FAILED to set up custom report.",
        'loglevel': 'ERROR',
    },
    'WEKO_ADMIN_FAILED_SEND_EMAIL': {
        'msgid': 'WEKO_ADMIN_E_0017',
        'msgstr': "FAILED to send email.",
        'loglevel': 'ERROR',
    },
    'WEKO_ADMIN_FAILED_SAVE_SITE_INFO': {
        'msgid': 'WEKO_ADMIN_E_0018',
        'msgstr': "FAILED to save Site Information.",
        'loglevel': 'ERROR',
    },
    'WEKO_ADMIN_FAILED_SAVED_SITE_LICENCE': {
        'msgid': 'WEKO_ADMIN_E_0019',
        'msgstr': "FAILED to save Site Licence.",
        'loglevel': 'ERROR',
    },
    'WEKO_ADMIN_FAILED_SAVE_WEB_API_ACCOUNT_INFO': {
        'msgid': 'WEKO_ADMIN_E_0020',
        'msgstr': "FAILED to save Web API account information.",
        'loglevel': 'ERROR',
    },
    'WEKO_ADMIN_FAILED_SAVE_PDF_FILE_SETTINGS': {
        'msgid': 'WEKO_ADMIN_E_0021',
        'msgstr': "FAILED to save the settings in the PDF file.",
        'loglevel': 'ERROR',
    },
    'WEKO_ADMIN_FAILED_SAVE_RESTRICTRD_ACCESS_SETTINGS': {
        'msgid': 'WEKO_ADMIN_E_0022',
        'msgstr': "FAILED to save settings of Restricted Access.",
        'loglevel': 'ERROR',
    },
    'WEKO_ADMIN_FAILED_SEND_EMAIL_REMINDER_REPORT_USAGE': {
        'msgid': 'WEKO_ADMIN_E_0023',
        'msgstr': "FAILED send email reminder to report usage.",
        'loglevel': 'ERROR',
    },
    'WEKO_ADMIN_RESENT_MAIL': {
        'msgid': 'WEKO_ADMIN_W_0001',
        'msgstr': "The email failed to send and has been resent.",
        'loglevel': 'WARN',
    },
    'WEKO_ADMIN_FEEDBACK_ADDRESS_SET': {
        'msgid': 'WEKO_ADMIN_I_0001',
        'msgstr': "Feedback email address set.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_REGISTER_NEW_INDEX': {
        'msgid': 'WEKO_ADMIN_I_0002',
        'msgstr': "New index is registered in the index tree.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_UPDATE_INDEX_TREE': {
        'msgid': 'WEKO_ADMIN_I_0003',
        'msgstr': "Index tree updated.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_PUBLISH_INDEX': {
        'msgid': 'WEKO_ADMIN_I_0004',
        'msgstr': "Index became open to public.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_INDEX_NO_LONGER_PUBLISHED': {
        'msgid': 'WEKO_ADMIN_I_0005',
        'msgstr': "Index is no longer published.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_UPDATE_INDEX': {
        'msgid': 'WEKO_ADMIN_I_0006',
        'msgstr': "Index updated.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_DELETE_INDEX_TREE': {
        'msgid': 'WEKO_ADMIN_I_0007',
        'msgstr': "Index tree deleted.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_MOVED_INDEX_TREE': {
        'msgid': 'WEKO_ADMIN_I_0008',
        'msgstr': "Index tree has been moved.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_SAVED_RANKING_SETTINGS': {
        'msgid': 'WEKO_ADMIN_I_0009',
        'msgstr': "Ranking settings have been saved.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_EXPORT_FULL_ITEM': {
        'msgid': 'WEKO_ADMIN_I_0010',
        'msgstr': "Full export of the item has been performed.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_CANCEL_EXPORT_FULL_ITEM': {
        'msgid': 'WEKO_ADMIN_I_0011',
        'msgstr': "Full export of the item has been cancelled.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_BULK_IMPORT_ITEMS': {
        'msgid': 'WEKO_ADMIN_I_0012',
        'msgstr': "Bulk import of items has been done.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_DOWNLOAD_ITEM_ON_SCREEN': {
        'msgid': 'WEKO_ADMIN_I_0013',
        'msgstr': "List of items displayed on the screen has been downloaded "\
            "in TSV format.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_REFERENCE_NUM_ITEMS_REGISTERED': {
        'msgid': 'WEKO_ADMIN_I_0014',
        'msgstr': "The number of items registered was referenced.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_DOWNLOAD_FIX_FORM_REPORTS': {
        'msgid': 'WEKO_ADMIN_I_0015',
        'msgstr': "Fixed Form Reports was downloaded.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_SET_UP_CUSTOM_REPORT': {
        'msgid': 'WEKO_ADMIN_I_0016',
        'msgstr': "Custom report has been set up.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_CHANGE_FEEDBACK_EMAIL_SETTING': {
        'msgid': 'WEKO_ADMIN_I_0017',
        'msgstr': "Feedback email setting has been changed to "\
            "{configuration_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_CHANGE_FEEDBACK_EMAIL_DETAIL_SETTING': {
        'msgid': 'WEKO_ADMIN_I_0018',
        'msgstr': "Feedback email setting has been changed {section} to "\
            "{configuration_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_SENT_EMAIL': {
        'msgid': 'WEKO_ADMIN_I_0019',
        'msgstr': "Email has been sent.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_CHANGE_ITEM_USAGE_DISPLAY_SETTING': {
        'msgid': 'WEKO_ADMIN_I_0020',
        'msgstr': "The display setting for item usage stats has been changed "\
            "to {configuration_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_CHANGE_ITEM_USAGE_DISPLAY_DETAIL_SETTING': {
        'msgid': 'WEKO_ADMIN_I_0021',
        'msgstr': "The display setting for item usage stats has been changed "\
            "{section} to {configuration_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_SAVED_ITEM_IDENTIFIER': {
        'msgid': 'WEKO_ADMIN_I_0022',
        'msgstr': "The item identifier has been saved.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_CHANGE_ITEM_EXPORT_SETTINGS': {
        'msgid': 'WEKO_ADMIN_I_0023',
        'msgstr': "Item export settings have been changed to {set_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_CHANGE_FILE_OUTPUT_SETTINGS': {
        'msgid': 'WEKO_ADMIN_I_0024',
        'msgstr': "Content file output settings have been changed to "\
            "{set_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_EXCLUDED_IPADDRESS': {
        'msgid': 'WEKO_ADMIN_I_0025',
        'msgstr': "IP address: {ip_address} was excluded from the aggregate "\
            "usage statistics.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_EXCLUDED_USERID': {
        'msgid': 'WEKO_ADMIN_I_0026',
        'msgstr': "User: {user_id} was excluded from the aggregate usage "\
            "statistics.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_CHANGED_SEARCH_AUTHOR_SETTINGS': {
        'msgid': 'WEKO_ADMIN_I_0027',
        'msgstr': "Search Author Setting has been changed to {set_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_CHANGED_SEARCH_SETTING': {
        'msgid': 'WEKO_ADMIN_I_0028',
        'msgstr': "Index tree/facet search setting has been changed to "\
            "{set_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_CHANGED_OTHER_SEARCH_SETTINGS': {
        'msgid': 'WEKO_ADMIN_I_0029',
        'msgstr': "Other search settings have changed.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_CHANGED_FACETED_SEARCH_SETTINGS': {
        'msgid': 'WEKO_ADMIN_I_0030',
        'msgstr': "Faceted search settings have been changed to {set_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_CHANGED_FACETED_SEARCH_DETAIL_SETTINGS': {
        'msgid': 'WEKO_ADMIN_I_0031',
        'msgstr': "Faceted search settings have been changed {section} to "\
            "{set_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_SAVED_FACETED_SEARCH_ITEM': {
        'msgid': 'WEKO_ADMIN_I_0032',
        'msgstr': "Item to be faceted searched has been saved.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_DELETE_FACETED_SEARCH_ITEM': {
        'msgid': 'WEKO_ADMIN_I_0033',
        'msgstr': "Item to be faceted searched has been deleted.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_SEARCH_FACETED_SEARCH_ITEM': {
        'msgid': 'WEKO_ADMIN_I_0034',
        'msgstr': "Item to be faceted searched has been searched. "\
            "{search_type} : {search_word}",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_SAVED_SITE_INFO': {
        'msgid': 'WEKO_ADMIN_I_0035',
        'msgstr': "Site Information saved.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_SAVED_SITE_LICENCE': {
        'msgid': 'WEKO_ADMIN_I_0036',
        'msgstr': "Site Licence saved.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_SAVE_WEB_API_ACCOUNT_INFO': {
        'msgid': 'WEKO_ADMIN_I_0037',
        'msgstr': "Web API account information has been saved.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_DISPLAY_PDF_FILE': {
        'msgid': 'WEKO_ADMIN_I_0038',
        'msgstr': "PDF file is now displayed on screen.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_SAVED_PDF_FILE_SETTINGS': {
        'msgid': 'WEKO_ADMIN_I_0039',
        'msgstr': "Settings of the PDF file have been saved.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_SAVED_RESTRICTRD_ACCESS_SETTINGS': {
        'msgid': 'WEKO_ADMIN_I_0040',
        'msgstr': "Restricted Access settings have been saved.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_SENT_EMAIL_REMINDER_REPORT_USAGE': {
        'msgid': 'WEKO_ADMIN_I_0041',
        'msgstr': "Email reminder to report usage has been sent.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_RECONFIGUR_ITEM_INDEX': {
        'msgid': 'WEKO_ADMIN_I_0042',
        'msgstr': "The item index has been reconfigured.",
        'loglevel': 'INFO',
    },
    'WEKO_ADMIN_PERFORMED_REINDEX_ITEM': {
        'msgid': 'WEKO_ADMIN_I_0043',
        'msgstr': "Item re-indexing has been performed.",
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
    param = WEKO_ADMIN_MESSAGE.get(key, None)
    if param:
        weko_logger_base(app=current_app, param=param, ex=ex, **kwargs)
    else:
        weko_logger_base(app=current_app, key=key, ex=ex, **kwargs)
