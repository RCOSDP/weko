# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Logging is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Resource for common log messages."""

WEKO_COMMON_MESSAGE = {
    'WEKO_COMMON_FOR_LOOP_ITERATION': {
        'msgid': 'WEKO_COMMON_D_0001',
        'msgstr': "Loop iteration {count}, {element}",
        'loglevel': 'DEBUG',
    },
    'WEKO_COMMON_FOR_START': {
        'msgid': 'WEKO_COMMON_D_0002',
        'msgstr': "Start for sentence",
        'loglevel': 'DEBUG',
    },
    'WEKO_COMMON_FOR_END': {
        'msgid': 'WEKO_COMMON_D_0003',
        'msgstr': "End for sentence",
        'loglevel': 'DEBUG',
    },
    'WEKO_COMMON_RETURN_VALUE': {
        'msgid': 'WEKO_COMMON_D_0004',
        'msgstr': "Return value: {value}",
        'loglevel': 'DEBUG',
    },
    'WEKO_COMMON_IF_ENTER': {
        'msgid': 'WEKO_COMMON_D_0005',
        'msgstr': "Enter IF: {branch}",
        'loglevel': 'DEBUG',
    },
    'WEKO_COMMON_INIT_APP': {
        'msgid': 'WEKO_COMMON_D_0006',
        'msgstr': "Init app: {ext}",
        'loglevel': 'DEBUG',
    },
    'WEKO_COMMON_INIT_CONFIG': {
        'msgid': 'WEKO_COMMON_D_0007',
        'msgstr': "Init config: {config}={value}",
        'loglevel': 'DEBUG',
    },
    'WEKO_COMMON_WHILE_START':{
        'msgid': 'WEKO_COMMON_D_0008',
        'msgstr': "Start while sentence",
        'loglevel': 'DEBUG',
    },
    'WEKO_COMMON_WHILE_END':{
        'msgid': 'WEKO_COMMON_D_0009',
        'msgstr': "End while sentence",
        'loglevel': 'DEBUG',
    },
    'WEKO_COMMON_WHILE_LOOP_ITERATION':{
        'msgid': 'WEKO_COMMON_D_0010',
        'msgstr': "Loop iteration {count}, {element}",
        'loglevel': 'DEBUG',
    },
    'WEKO_COMMON_FAILED_DBCONNECTION': {
        'msgid': 'WEKO_COMMON_E_0001',
        'msgstr': "FAILED database connection.",
        'loglevel': 'ERROR',
    },
    'WEKO_COMMON_NOT_FOUND_OBJECT': {
        'msgid': 'WEKO_COMMON_E_0002',
        'msgstr': "NOT found object: {object}",
        'loglevel': 'ERROR',
    },
    'WEKO_COMMON_DB_SOME_ERROR': {
        'msgid': 'WEKO_COMMON_E_0003',
        'msgstr': "Some errors in the DB.",
        'loglevel': 'ERROR',
    },
    'WEKO_COMMON_ERROR_UNEXPECTED': {
        'msgid': 'WEKO_COMMON_E_0004',
        'msgstr': "Unexpected error.",
        'loglevel': 'ERROR',
    },
    'WEKO_COMMON_ERROR_ELASTICSEARCH': {
        'msgid': 'WEKO_COMMON_E_0005',
        'msgstr': "ERROR in Elasticsearch.",
        'loglevel': 'ERROR',
    },
    'WEKO_COMMON_ERROR_REDIS': {
        'msgid': 'WEKO_COMMON_E_0006',
        'msgstr': "ERROR in Redis.",
        'loglevel': 'ERROR',
    },
    'WEKO_COMMON_FAILED_GET_PID': {
        'msgid': 'WEKO_COMMON_E_0007',
        'msgstr': "FAILED to get pid.",
        'loglevel': 'ERROR',
    },
    'WEKO_COMMON_CALLED_ARGUMENT': {
        'msgid': 'WEKO_COMMON_I_0001',
        'msgstr': "Called with arg: arg={arg}",
        'loglevel': 'INFO',
    },
    'WEKO_COMMON_UNAUTHORISED_ACCESS': {
        'msgid': 'WEKO_COMMON_I_0002',
        'msgstr': "Unauthorised access by guest user.",
        'loglevel': 'INFO',
    },
    'WEKO_COMMON_CALLED_KW_ARGUMENT': {
        'msgid': 'WEKO_COMMON_I_0003',
        'msgstr': "Called with kwarg: kwarg={kwarg}",
        'loglevel': 'INFO',
    },
    'WEKO_COMMON_DBCONNECTION_RETRY': {
        'msgid': 'WEKO_COMMON_W_0001',
        'msgstr': "Retry connection count {count}",
        'loglevel': 'WARN',
    },
}
