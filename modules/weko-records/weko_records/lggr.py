"""Resource for weko-records log messages."""

WEKO_RECORDS_MESSAGE = {
    'WEKO_RECORDS_FAILED_SEARCH_ITEM': {
        'msgid': 'WEKO_RECORDS_E_0001',
        'msgstr': "FAILED to search item: {query}",
        'msglvl': 'ERROR',
    },
    'WEKO_RECORDS_FAILED_OUTPUT_RSS_DOCUMENT': {
        'msgid': 'WEKO_RECORDS_E_0002',
        'msgstr': "FAILED to output RSS document.",
        'msglvl': 'ERROR',
    },
    'WEKO_RECORDS_FAILED_SERIALIZE_RESULT_TO_RSS': {
        'msgid': 'WEKO_RECORDS_E_0003',
        'msgstr': "FAILED to serialize search results into RSS format.",
        'msglvl': 'ERROR',
    },
    'WEKO_RECORDS_FAILED_DELETE_RECORD': {
        'msgid': 'WEKO_RECORDS_E_0004',
        'msgstr': "FAILED to delete records. Uuid: {uuid}",
        'msglvl': 'ERROR',
    },
    'WEKO_RECORDS_FAILED_RESTORE_RECORD': {
        'msgid': 'WEKO_RECORDS_E_0005',
        'msgstr': "FAILED to restore record. Uuid: {uuid}",
        'msglvl': 'ERROR',
    },
    'WEKO_RECORDS_SEARCH_ITEM': {
        'msgid': 'WEKO_RECORDS_I_0001',
        'msgstr': "Search item: {query}, result: {num}",
        'msglvl': 'INFO',
    },
    'WEKO_RECORDS_ENABLED_RSS_FEEDS': {
        'msgid': 'WEKO_RECORDS_I_0002',
        'msgstr': "RSS feeds are now enabled.",
        'msglvl': 'INFO',
    },
    'WEKO_RECORDS_OUTPUT_RSS_DOCUMENT': {
        'msgid': 'WEKO_RECORDS_I_0003',
        'msgstr': "RSS document has been output.",
        'msglvl': 'INFO',
    },
    'WEKO_RECORDS_SERIALIZE_RESULT_TO_RSS': {
        'msgid': 'WEKO_RECORDS_I_0004',
        'msgstr': "Serialized search results into RSS format.",
        'msglvl': 'INFO',
    },
    'WEKO_RECORDS_DELETE_RECORD': {
        'msgid': 'WEKO_RECORDS_I_0005',
        'msgstr': "{dlt_nm} record was deleted. Uuid: {uuid}",
        'msglvl': 'INFO',
    },
    'WEKO_RECORDS_RESTORE_RECORD': {
        'msgid': 'WEKO_RECORDS_I_0006',
        'msgstr': "Record restored. Uuid: {uuid}",
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
    param = WEKO_RECORDS_MESSAGE.get(key, None)
    if param:
        weko_logger_base(param=param, ex=ex, **kwargs)
    else:
        weko_logger_base(key=key, ex=ex, **kwargs)
