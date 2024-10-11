# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Groups is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Resource for weko-groups log messages."""

from flask import current_app


WEKO_GROUPS_MESSAGE = {
    'WEKO_GROUPS_FAILED_CREATE_NEW_GROUP': {
        'msgid': 'WEKO_GROUPS_E_0001',
        'msgstr': "FAILED to create new group.",
        'loglevel': 'ERROR',
    },
    'WEKO_GROUPS_FAILED_UPDATE_GROUP': {
        'msgid': 'WEKO_GROUPS_E_0002',
        'msgstr': "FAILED to update group {group_id}",
        'loglevel': 'ERROR',
    },
    'WEKO_GROUPS_FAILED_DELETE_GROUP': {
        'msgid': 'WEKO_GROUPS_E_0003',
        'msgstr': "FAILED to delete group {group_id}",
        'loglevel': 'ERROR',
    },
    'WEKO_GROUPS_FAILED_DISPLAY_MEMBER_LIST': {
        'msgid': 'WEKO_GROUPS_E_0004',
        'msgstr': "FAILED to display member list of group {group_id}",
        'loglevel': 'ERROR',
    },
    'WEKO_GROUPS_FAILED_LEAVE_GROUP': {
        'msgid': 'WEKO_GROUPS_E_0005',
        'msgstr': "FAILED to leave group {group_id}",
        'loglevel': 'ERROR',
    },
    'WEKO_GROUPS_FAILED_APPROVE_USER_TO_GROUP': {
        'msgid': 'WEKO_GROUPS_E_0006',
        'msgstr': "FAILED to approve membership for the group {group_id}",
        'loglevel': 'ERROR',
    },
    'WEKO_GROUPS_FAILED_REMOVE_USER_FROM_GROUP': {
        'msgid': 'WEKO_GROUPS_E_0007',
        'msgstr': "FAILED to remove user {user_id} from group {group_id}",
        'loglevel': 'ERROR',
    },
    'WEKO_GROUPS_FAILED_ACCEPT_INVITATION_FROM_GROUP': {
        'msgid': 'WEKO_GROUPS_E_0008',
        'msgstr': "FAILED to accept the invitation to join the group "\
            "{group_id}",
        'loglevel': 'ERROR',
    },
    'WEKO_GROUPS_FAILED_REFUSE_INVITATION_FROM_GROUP': {
        'msgid': 'WEKO_GROUPS_E_0009',
        'msgstr': "FAILED to refuse the invitation to join the group "\
            "{group_id}",
        'loglevel': 'ERROR',
    },
    'WEKO_GROUPS_FAILED_INVITE_USER_TO_GROUP': {
        'msgid': 'WEKO_GROUPS_E_0010',
        'msgstr': "Failed to invite new member.",
        'loglevel': 'ERROR',
    },
    'WEKO_GROUPS_LOGIN_SUCCESSED': {
        'msgid': 'WEKO_GROUPS_I_0001',
        'msgstr': "Login request SUCCESSED",
        'loglevel': 'INFO',
    },
    'WEKO_GROUPS_LOGIN_FAILED': {
        'msgid': 'WEKO_GROUPS_I_0002',
        'msgstr': "Login request FAILED",
        'loglevel': 'INFO',
    },
    'WEKO_GROUPS_USER_LOGOUT': {
        'msgid': 'WEKO_GROUPS_I_0003',
        'msgstr': "User logged out",
        'loglevel': 'INFO',
    },
    'WEKO_GROUPS_CREATE_NEW_GROUP': {
        'msgid': 'WEKO_GROUPS_I_0004',
        'msgstr': "Create new group: {group_id}",
        'loglevel': 'INFO',
    },
    'WEKO_GROUPS_UPDATE_GROUP': {
        'msgid': 'WEKO_GROUPS_I_0005',
        'msgstr': "Group {group_id} was updated.",
        'loglevel': 'INFO',
    },
    'WEKO_GROUPS_DELETE_GROUP': {
        'msgid': 'WEKO_GROUPS_I_0006',
        'msgstr': "Delete group: {group_id}",
        'loglevel': 'INFO',
    },
    'WEKO_GROUPS_DISPLAY_MEMBER_LIST': {
        'msgid': 'WEKO_GROUPS_I_0007',
        'msgstr': "Group {group_id} member list displayed. ",
        'loglevel': 'INFO',
    },
    'WEKO_GROUPS_LEAVED_GROUP': {
        'msgid': 'WEKO_GROUPS_I_0008',
        'msgstr': "Leaved group {group_id}",
        'loglevel': 'INFO',
    },
    'WEKO_GROUPS_APPROVE_USER_TO_GROUP': {
        'msgid': 'WEKO_GROUPS_I_0009',
        'msgstr': "Approved user {user_id} to be member of group {group_id}",
        'loglevel': 'INFO',
    },
    'WEKO_GROUPS_REMOVE_USER_FROM_GROUP': {
        'msgid': 'WEKO_GROUPS_I_0010',
        'msgstr': "Remove user {user_id} from group {group_id}",
        'loglevel': 'INFO',
    },
    'WEKO_GROUPS_ACCEPT_INVITATION_FROM_GROUP': {
        'msgid': 'WEKO_GROUPS_I_0011',
        'msgstr': "The invitation to join the group {group_id} was accepted.",
        'loglevel': 'INFO',
    },
    'WEKO_GROUPS_REFUSE_INVITATION_FROM_GROUP': {
        'msgid': 'WEKO_GROUPS_I_0012',
        'msgstr': "Group invitation refused to accept.",
        'loglevel': 'INFO',
    },
    'WEKO_GROUPS_INVITE_USER_TO_GROUP': {
        'msgid': 'WEKO_GROUPS_I_0013',
        'msgstr': "Invite user {user_id} to group {group_id}",
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
    param = WEKO_GROUPS_MESSAGE.get(key, None)
    if param:
        weko_logger_base(app=current_app, param=param, ex=ex, **kwargs)
    else:
        weko_logger_base(app=current_app, key=key, ex=ex, **kwargs)
