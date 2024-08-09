"""Resource for weko-itemtypes_ui log messages."""

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
        'msgstr': "Enter IF: {line}",
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
    'WEKO_COMMON_DB_OTHER_ERROR': {
        'msgid': 'WEKO_COMMON_E_0003',
        'msgstr': "Other errors in the DB.",
        'msglvl': 'ERROR',
    },
    'WEKO_COMMON_ERROR_UNEXPECTED': {
        'msgid': 'WEKO_COMMON_E_0004',
        'msgstr': "Unexpected error.",
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

import inspect
import traceback
from flask import current_app

def weko_logger_base(key=None, param=None, ex=None, **kwargs):
    """Log message with key.

    Method to output logs in current_app.logger using the resource.

    Args:
        key (str): key of message.
            Not required if param is specified.
        param (dict): message parameters.
            Not required if key is specified.
        ex (Exception): exception object.
            Not required.
        **kwargs: message parameters.
            If you want to replace the placeholder in the message,
            specify the key-value pair here.

    Returns:
        None
    """
    # get message parameters from common resource
    if not param:
        param = WEKO_COMMON_MESSAGE.get(key, None)
    if not param:
        return
    
    current_app.logger.info('param is None!!!!!!!!!!')

    msgid = param.get('msgid', None)
    msgstr = param.get('msgstr', None)
    msglvl = param.get('msglvl', None)

    msg = msgid + ' : ' + msgstr

    # get pathname, lineno, funcName of caller
    frame = inspect.stack()[2]
    extra = {
        'wpathname': frame.filename,
        'wlineno': frame.lineno,
        'wfuncName': frame.function,
    }
    print(extra)

    # output log by msglvl
    if msglvl == 'ERROR':
        current_app.logger.error(msg.format(**kwargs), extra=extra)
    elif msglvl == 'WARN':
        current_app.logger.warning(msg.format(**kwargs), extra=extra)
    elif msglvl == 'INFO':
        current_app.logger.info(msg.format(**kwargs), extra=extra)
    elif msglvl == 'DEBUG':
        current_app.logger.debug(msg.format(**kwargs), extra=extra)
    else:
        pass

    if ex:
        current_app.logger.error(
            ex.__class__.__name__ + ": " + str(ex), extra=extra)
        traceback.print_exc()
