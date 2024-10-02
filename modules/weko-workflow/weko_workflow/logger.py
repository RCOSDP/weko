# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Workflow is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Resource for weko-workflow log messages."""

from flask import current_app


WEKO_WORKFLOW_MESSAGE = {
    'WEKO_WORKFLOW_FAILED_SAVE': {
        'msgid': 'WEKO_WORKFLOW_E_0001',
        'msgstr': "FAILED to save worfflow: {workflow_id}",
        'loglevel': 'ERROR',
    },
    'WEKO_WORKFLOW_FAILED_SAVE_OA_POLICY_CONFIRMATION': {
        'msgid': 'WEKO_WORKFLOW_E_0002',
        'msgstr': "FAILED to save OA Policy Confirmation.",
        'loglevel': 'ERROR',
    },
    'WEKO_WORKFLOW_FAILED_SAVE_METADATA': {
        'msgid': 'WEKO_WORKFLOW_E_0003',
        'msgstr': "FAILED to save Metadata: {pid}",
        'loglevel': 'ERROR',
    },
    'WEKO_WORKFLOW_FAILED_SAVE_INDEX': {
        'msgid': 'WEKO_WORKFLOW_E_0004',
        'msgstr': "FAILED to save index designation: {pid}",
        'loglevel': 'ERROR',
    },
    'WEKO_WORKFLOW_FAILED_SAVE_COMMENT': {
        'msgid': 'WEKO_WORKFLOW_E_0005',
        'msgstr': "FAILED to save comment: {pid}",
        'loglevel': 'ERROR',
    },
    'WEKO_WORKFLOW_FAILED_SAVE_ITEMLINK': {
        'msgid': 'WEKO_WORKFLOW_E_0006',
        'msgstr': "FAILED to save Item link: {pid}",
        'loglevel': 'ERROR',
    },
    'WEKO_WORKFLOW_FAILED_SAVE_DOI': {
        'msgid': 'WEKO_WORKFLOW_E_0007',
        'msgstr': "FAILED to save DOI grant: {pid}",
        'loglevel': 'ERROR',
    },
    'WEKO_WORKFLOW_FAILED_AUTHORIZATION': {
        'msgid': 'WEKO_WORKFLOW_E_0008',
        'msgstr': "Authorization FAILED: {pid}",
        'loglevel': 'ERROR',
    },
    'WEKO_WORKFLOW_FAILED_ITEM_PROCESS': {
        'msgid': 'WEKO_WORKFLOW_E_0009',
        'msgstr': "FAILED item process: {pid}",
        'loglevel': 'ERROR',
    },
    'WEKO_WORKFLOW_FAILED_FILE_UPLOAD': {
        'msgid': 'WEKO_WORKFLOW_E_0010',
        'msgstr': "FAILED file upload: {file_id}",
        'loglevel': 'ERROR',
    },
    'WEKO_WORKFLOW_FAILED_SET_WEB_API_ACCOUNT_INFO': {
        'msgid': 'WEKO_WORKFLOW_E_0011',
        'msgstr': "FAILED to save Web API account information. Itemid: {pid}",
        'loglevel': 'ERROR',
    },
    'WEKO_WORKFLOW_FAILED_SAVE_FLOW': {
        'msgid': 'WEKO_WORKFLOW_E_0012',
        'msgstr': "FAILED to save flow action: {flow_id}",
        'loglevel': 'ERROR',
    },
    'WEKO_WORKFLOW_FAILED_DELETE_FLOW': {
        'msgid': 'WEKO_WORKFLOW_E_0013',
        'msgstr': "FAILED to delete flow: {flow_id}",
        'loglevel': 'ERROR',
    },
    'WEKO_WORKFLOW_FAILED_VALIDATION': {
        'msgid': 'WEKO_WORKFLOW_E_0014',
        'msgstr': "Validation Error occurred in {type}",
        'loglevel': 'ERROR',
    },
    'WEKO_WORKFLOW_CREATE_WORKFLOW': {
        'msgid': 'WEKO_WORKFLOW_I_0001',
        'msgstr': "Create workflow: {workflow_id}",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_UPDATE_WORKFLOW': {
        'msgid': 'WEKO_WORKFLOW_I_0002',
        'msgstr': "Update workflow: {workflow_id}",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_SAVED_SUCCESSFULLY': {
        'msgid': 'WEKO_WORKFLOW_I_0003',
        'msgstr': "Workflow saved: {workflow_id}",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_EDIT_ITEM': {
        'msgid': 'WEKO_WORKFLOW_I_0004',
        'msgstr': "Edit item: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_DELETE_SUCCESSFULLY': {
        'msgid': 'WEKO_WORKFLOW_I_0005',
        'msgstr': "Delete workflow: {workflow_id}",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_DOWNLOAD_TSV': {
        'msgid': 'WEKO_WORKFLOW_I_0006',
        'msgstr': "Download TSV file.",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_CREATE_ACTIVITY': {
        'msgid': 'WEKO_WORKFLOW_I_0007',
        'msgstr': "Create activity.",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_DELETE_ACTIVITY': {
        'msgid': 'WEKO_WORKFLOW_I_0008',
        'msgstr': "Activity has been deleted.",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_SAVED_OA_POLICY_CONFIRMATION': {
        'msgid': 'WEKO_WORKFLOW_I_0009',
        'msgstr': "OA Policy Confirmation has been saved.",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_FORCED_OUT_OA_POLICY_CONFIRMATION': {
        'msgid': 'WEKO_WORKFLOW_I_0010',
        'msgstr': "OA Policy Confirmation has been forced out.",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_SAVED_METADATA': {
        'msgid': 'WEKO_WORKFLOW_I_0011',
        'msgstr': "Metadata saved: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_QUIT_METADATA': {
        'msgid': 'WEKO_WORKFLOW_I_0012',
        'msgstr': "Metadata input was quitted: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_SAVED_INDEX': {
        'msgid': 'WEKO_WORKFLOW_I_0013',
        'msgstr': "Index designation saved: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_QUIT_INDEX': {
        'msgid': 'WEKO_WORKFLOW_I_0014',
        'msgstr': "Index designation quitted: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_SAVED_COMMENT': {
        'msgid': 'WEKO_WORKFLOW_I_0015',
        'msgstr': "Comment saved: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_QUIT_COMMENT': {
        'msgid': 'WEKO_WORKFLOW_I_0016',
        'msgstr': "Comment quitted: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_SAVED_ITEMLINK': {
        'msgid': 'WEKO_WORKFLOW_I_0017',
        'msgstr': "Item link saved: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_QUIT_ITEMLINK': {
        'msgid': 'WEKO_WORKFLOW_I_0018',
        'msgstr': "Item link has been quitted {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_REQUEST_DOI': {
        'msgid': 'WEKO_WORKFLOW_I_0019',
        'msgstr': "Requested for DOI grant: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_GRANT_DOI': {
        'msgid': 'WEKO_WORKFLOW_I_0020',
        'msgstr': "DOI has been granted: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_QUIT_DOI_GRANT': {
        'msgid': 'WEKO_WORKFLOW_I_0021',
        'msgstr': "DOI grant has been quitted: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_APPROVED_CONTENT': {
        'msgid': 'WEKO_WORKFLOW_I_0022',
        'msgstr': "The content has been approved: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_NOT_APPROVED_CONTENT': {
        'msgid': 'WEKO_WORKFLOW_I_0023',
        'msgstr': "Content not approved: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_SAVED_APPROVAL_RESULT': {
        'msgid': 'WEKO_WORKFLOW_I_0024',
        'msgstr': "Approval result saved: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_QUIT_APPROVAL_RESULT': {
        'msgid': 'WEKO_WORKFLOW_I_0025',
        'msgstr': "Approval result has been quitted: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_CREATE_ITEM': {
        'msgid': 'WEKO_WORKFLOW_I_0026',
        'msgstr': "Create item: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_UPLOAD_FILE': {
        'msgid': 'WEKO_WORKFLOW_I_0027',
        'msgstr': "Upload file: {file_id}",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_QUIT_FILE_UPLOAD': {
        'msgid': 'WEKO_WORKFLOW_I_0028',
        'msgstr': "File upload has been quitted: {file_id}",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_CHANGE_SETTINGS_MULTIPART_UPLOAD': {
        'msgid': 'WEKO_WORKFLOW_I_0029',
        'msgstr': "The multipart upload function setting has been changed to "\
            "{configuration_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_CHANGE_DETAIL_SETTINGS_MULTIPART_UPLOAD': {
        'msgid': 'WEKO_WORKFLOW_I_0030',
        'msgstr': "The multipart upload function setting has been changed "\
            "{section} to {configuration_value}.",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_SET_WEB_API_ACCOUNT_INFO': {
        'msgid': 'WEKO_WORKFLOW_I_0031',
        'msgstr': "Web API account information has been set. Itemid: {pid}",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_CREATE_FLOW': {
        'msgid': 'WEKO_WORKFLOW_I_0032',
        'msgstr': "Create flow: {flow_id}",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_UPDATE_FLOW': {
        'msgid': 'WEKO_WORKFLOW_I_0033',
        'msgstr': "Update flow: {flow_id}",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_SAVED_FLOW': {
        'msgid': 'WEKO_WORKFLOW_I_0034',
        'msgstr': "Flow action saved successfully: {flow_id}",
        'loglevel': 'INFO',
    },
    'WEKO_WORKFLOW_DETELE_FLOW': {
        'msgid': 'WEKO_WORKFLOW_I_0035',
        'msgstr': "Delete flow: {flow_id}",
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
    param = WEKO_WORKFLOW_MESSAGE.get(key, None)
    if param:
        weko_logger_base(app=current_app, param=param, ex=ex, **kwargs)
    else:
        weko_logger_base(app=current_app, key=key, ex=ex, **kwargs)
