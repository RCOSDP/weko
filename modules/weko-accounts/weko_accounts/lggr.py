"""Resource for weko-accounts log messages."""

WEKO_ACCOUNTS_MESSAGE = {
    'WEKO_ACCOUNTS_LOGIN_SUCCESSED': {
        'msgid': 'WEKO_ACCOUNTS_I_0001',
        'msgstr': "Login request SUCCESSED",
        'msglvl': 'INFO',
    },
    'WEKO_ACCOUNTS_LOGIN_FAILED': {
        'msgid': 'WEKO_ACCOUNTS_I_0002',
        'msgstr': "Login request FAILED",
        'msglvl': 'INFO',
    },
    'WEKO_ACCOUNTS_USER_LOGOUT': {
        'msgid': 'WEKO_ACCOUNTS_I_0003',
        'msgstr': "User logged out",
        'msglvl': 'INFO',
    },
}

from weko_logging.lggr import weko_logger_base

def weko_logger(key=None, ex=None, **kwargs):
    """Log message with key.

    Method to output logs in current_app.logger using the resource.

    Args:
        key (str): key of message.
            Not required if ex is specified.
        ex (Exception): exception object.
            If you catch an exception, specify it here.
        **kwargs: message parameters.
            If you want to replace the placeholder in the message,
            specify the key-value pair here.

    Returns:
        None

    Examples:
    * Log message with key::

        weko_logger(key='WEKO_COMMON_SAMPLE')

    * Log message with key and parameters::

        weko_logger(key='WEKO_COMMON_SAMPLE', param1='param1', param2='param2')

    * Log message with key and exception::

        weko_logger(key='WEKO_COMMON_SAMPLE', ex=ex)

    * Log message with key, parameters and exception::

        weko_logger(key='WEKO_COMMON_SAMPLE', param1='param1', param2='param2', ex=ex)
    """
    # get message parameters from resource
    param = WEKO_ACCOUNTS_MESSAGE.get(key, None)
    if param:
        weko_logger_base(param=param, ex=ex, **kwargs)
    else:
        weko_logger_base(key=key, ex=ex, **kwargs)

# weko_logger(key='WEKO_ACCOUNTS_LOGIN_SUCCESSED')
# weko_logger(key='FOR_LOOP_ITERATION')