"""Resource for all modules log messages."""

WEKO_ACCOUNTS_MESSAGE = {
    'WEKO_COMMON_FAILED_DBCONNECTION': {
        'msgid': 'WEKO_COMMON_ERROR_9001',
        'msgstr': "FAILED database connection.",
        'msglvl': 'ERROR',
    },
    'WEKO_COMMON_NOT_FOUND_OBJECT': {
        'msgid': 'WEKO_COMMON_ERROR_9002',
        'msgstr': "NOT found object: {object}",
        'msglvl': 'ERROR',
    },
    'WEKO_COMMON_DB_OTHER_ERROR': {
        'msgid': 'WEKO_COMMON_ERROR_9003',
        'msgstr': "Other errors in the DB.",
        'msglvl': 'ERROR',
    },
    'WEKO_COMMON_DBCONNECTION_RETRY': {
        'msgid': 'WEKO_COMMON_WARN_9001',
        'msgstr': "Retry connection count {cnt}",
        'msglvl': 'WARN',
    },
    'WEKO_COMMON_CALLED_ARGUMENT': {
        'msgid': 'WEKO_COMMON_INFO_9001',
        'msgstr': "Called with arg: arg={arg}",
        'msglvl': 'INFO',
    },
    'WEKO_COMMON_UNAUTHORISED_ACCESS': {
        'msgid': 'WEKO_COMMON_INFO_9002',
        'msgstr': "Unauthorised access by guest user.",
        'msglvl': 'INFO',
    },
    'WEKO_COMMON_FOR_LOOP_ITERATION': {
        'msgid': 'WEKO_COMMON_DEBUG_9001',
        'msgstr': "Loop iteration {cnt}, {elem}",
        'msglvl': 'DEBUG',
    },
    'WEKO_COMMON_FOR_START': {
        'msgid': 'WEKO_COMMON_DEBUG_9002',
        'msgstr': "Start for sentence",
        'msglvl': 'DEBUG',
    },
    'WEKO_COMMON_FOR_END': {
        'msgid': 'WEKO_COMMON_DEBUG_9003',
        'msgstr': "End for sentence",
        'msglvl': 'DEBUG',
    },
    'WEKO_COMMON_RETURN_VALUE': {
        'msgid': 'WEKO_COMMON_DEBUG_9004',
        'msgstr': "Return value: {value}",
        'msglvl': 'DEBUG',
    },
    'WEKO_COMMON_IF_ENTER': {
        'msgid': 'WEKO_COMMON_DEBUG_9005',
        'msgstr': "Enter IF: {line}",
        'msglvl': 'DEBUG',
    },
    'WEKO_COMMON_ERROR_UNEXPECTED': {
        'msgid': 'WEKO_COMMON_ERROR_9004',
        'msgstr': "Unexpected error.",
        'msglvl': 'ERROR',
    },
}

import traceback
from flask import Flask, current_app
from weko_logging.ext import app

from weko_logging.ext import CustomLogFilter
def weko_logger(key=None, ex=None, **kwargs):
    # Add custom filter to log user_id and ip_address
    app.logger.addFilter(CustomLogFilter())


    param = WEKO_ACCOUNTS_MESSAGE.get(key, None)
    if not param:
        return

    msgid = param.get('msgid', None)
    msgstr = param.get('msgstr', None)
    msglvl = param.get('msglvl', None)

    msg = msgid + ' : ' + msgstr

    if msglvl == 'ERROR':
        current_app.logger.error(msg.format(**kwargs))
    elif msglvl == 'WARNING':
        current_app.logger.warning(msg.format(**kwargs))
    elif msglvl == 'INFO':
        current_app.logger.info(msg.format(**kwargs))
    elif msglvl == 'DEBUG':
        current_app.logger.debug(msg.format(**kwargs))
    else:
        pass

    if ex:
        current_app.logger.error(
            ex.__class__.__name__ + ": " + str(ex))
        traceback.print_exc()

    return
