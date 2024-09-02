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
        'msglvl': 'DEBUG',
    },
    'WEKO_COMMON_FOR_START': {
        'msgid': 'WEKO_COMMON_D_0002',
        'msgstr': "Start for sentence",
        'msglvl': 'DEBUG',
    },
    'WEKO_COMMON_FOR_END': {
        'msgid': 'WEKO_COMMON_D_0003',
        'msgstr': "End for sentence",
        'msglvl': 'DEBUG',
    },
    'WEKO_COMMON_RETURN_VALUE': {
        'msgid': 'WEKO_COMMON_D_0004',
        'msgstr': "Return value: {value}",
        'msglvl': 'DEBUG',
    },
    'WEKO_COMMON_IF_ENTER': {
        'msgid': 'WEKO_COMMON_D_0005',
        'msgstr': "Enter IF: {branch}",
        'msglvl': 'DEBUG',
    },
    'WEKO_COMMON_FAILED_DBCONNECTION': {
        'msgid': 'WEKO_COMMON_E_0001',
        'msgstr': "FAILED database connection.",
        'msglvl': 'ERROR',
    },
    'WEKO_COMMON_NOT_FOUND_OBJECT': {
        'msgid': 'WEKO_COMMON_E_0002',
        'msgstr': "NOT found object: {object}",
        'msglvl': 'ERROR',
    },
    'WEKO_COMMON_DB_SOME_ERROR': {
        'msgid': 'WEKO_COMMON_E_0003',
        'msgstr': "Some errors in the DB.",
        'msglvl': 'ERROR',
    },
    'WEKO_COMMON_ERROR_UNEXPECTED': {
        'msgid': 'WEKO_COMMON_E_0004',
        'msgstr': "Unexpected error.",
        'msglvl': 'ERROR',
    },
    'WEKO_COMMON_ERROR_ELASTICSEARCH': {
        'msgid': 'WEKO_COMMON_E_0005',
        'msgstr': "ERROR in Elasticsearch.",
        'msglvl': 'ERROR',
    },
    'WEKO_COMMON_ERROR_REDIS': {
        'msgid': 'WEKO_COMMON_E_0006',
        'msgstr': "ERROR in Redis.",
        'msglvl': 'ERROR',
    },
    'WEKO_COMMON_FAILED_GET_PID': {
        'msgid': 'WEKO_COMMON_E_0007',
        'msgstr': "FAILED to get pid.",
        'msglvl': 'ERROR',
    },
    'WEKO_COMMON_CALLED_ARGUMENT': {
        'msgid': 'WEKO_COMMON_I_0001',
        'msgstr': "Called with arg: arg={arg}",
        'msglvl': 'INFO',
    },
    'WEKO_COMMON_UNAUTHORISED_ACCESS': {
        'msgid': 'WEKO_COMMON_I_0002',
        'msgstr': "Unauthorised access by guest user.",
        'msglvl': 'INFO',
    },
    'WEKO_COMMON_DBCONNECTION_RETRY': {
        'msgid': 'WEKO_COMMON_W_0001',
        'msgstr': "Retry connection count {count}",
        'msglvl': 'WARN',
    },
}
