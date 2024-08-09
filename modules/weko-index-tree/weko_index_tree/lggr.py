"""Resource for weko-index_tree log messages."""

WEKO_INDEX_TREE_MESSAGE = {
    'WEKO_INDEX_TREE_FAILED_INDEX_SEARCH': {
        'msgid': 'WEKO_INDEX_TREE_E_0001',
        'msgstr': "FAILED to search item from index.",
        'msglvl': 'ERROR',
    },
    'WEKO_INDEX_TREE_FAILED_OUTPUT_RSS_DOCUMENT': {
        'msgid': 'WEKO_INDEX_TREE_E_0002',
        'msgstr': "FAILED to output RSS document.",
        'msglvl': 'ERROR',
    },
    'WEKO_INDEX_TREE_FAILED_GET_DATA_FOR_RSS': {
        'msgid': 'WEKO_INDEX_TREE_E_0003',
        'msgstr': "FAILED to get data for RSS output.",
        'msglvl': 'ERROR',
    },
    'WEKO_INDEX_TREE_FAILED_UPDATE_ITEMS_IN_BULK': {
        'msgid': 'WEKO_INDEX_TREE_E_0004',
        'msgstr': "FAILED to update items in bulk",
        'msglvl': 'ERROR',
    },
    'WEKO_INDEX_TREE_FAILED_REGISTER_NEW_INDEX': {
        'msgid': 'WEKO_INDEX_TREE_E_0005',
        'msgstr': "FAILED to register new index in the index tree.",
        'msglvl': 'ERROR',
    },
    'WEKO_INDEX_TREE_FAILED_UPDATE_INDEX_TREE': {
        'msgid': 'WEKO_INDEX_TREE_E_0006',
        'msgstr': "FAILED to update index tree.",
        'msglvl': 'ERROR',
    },
    'WEKO_INDEX_TREE_FAILED_PUBLISH_INDEX': {
        'msgid': 'WEKO_INDEX_TREE_E_0007',
        'msgstr': "FAILED to publish index.",
        'msglvl': 'ERROR',
    },
    'WEKO_INDEX_TREE_FAILED_UPDATE_INDEX': {
        'msgid': 'WEKO_INDEX_TREE_E_0008',
        'msgstr': "FAILED to update index.",
        'msglvl': 'ERROR',
    },
    'WEKO_INDEX_TREE_FAILED_INDEX_NO_LONGER_PUBLISHED': {
        'msgid': 'WEKO_INDEX_TREE_E_0009',
        'msgstr': "FAILED to stop publishing the index.",
        'msglvl': 'ERROR',
    },
    'WEKO_INDEX_TREE_FAILED_MOVE_INDEX_TREE': {
        'msgid': 'WEKO_INDEX_TREE_E_0010',
        'msgstr': "FAILED to move index tree.",
        'msglvl': 'ERROR',
    },
    'WEKO_INDEX_TREE_FAILED_DELETE_INDEX_TREE': {
        'msgid': 'WEKO_INDEX_TREE_E_0011',
        'msgstr': "FAILED to delete index tree.",
        'msglvl': 'ERROR',
    },
    'WEKO_INDEX_TREE_FAILED_DISPLAY_INDEX_LINK': {
        'msgid': 'WEKO_INDEX_TREE_E_0012',
        'msgstr': "FAILED to change display setting of the index link.",
        'msglvl': 'ERROR',
    },
    'WEKO_INDEX_TREE_INDEX_SEARCH_RESULT': {
        'msgid': 'WEKO_INDEX_TREE_I_0001',
        'msgstr': "index search : {srch_cntnt}, results: {num} items",
        'msglvl': 'INFO',
    },
    'WEKO_INDEX_TREE_ENABLED_RSS_FEEDS': {
        'msgid': 'WEKO_INDEX_TREE_I_0002',
        'msgstr': "RSS feeds are now enabled.",
        'msglvl': 'INFO',
    },
    'WEKO_INDEX_TREE_OUTPUT_RSS_DOCUMENT': {
        'msgid': 'WEKO_INDEX_TREE_I_0003',
        'msgstr': "RSS document has been output.",
        'msglvl': 'INFO',
    },
    'WEKO_INDEX_TREE_GET_DATA_FOR_RSS': {
        'msgid': 'WEKO_INDEX_TREE_I_0004',
        'msgstr': "Got data for RSS output.",
        'msglvl': 'INFO',
    },
    'WEKO_INDEX_TREE_CHANGE_DISPLAY_SETTINGS_SEARCH_RESULTS': {
        'msgid': 'WEKO_INDEX_TREE_I_0005',
        'msgstr': "The display setting for search results has been changed to {conf_value}.",
        'msglvl': 'INFO',
    },
    'WEKO_INDEX_TREE_UPDATE_ITEMS_IN_BULK': {
        'msgid': 'WEKO_INDEX_TREE_I_0006',
        'msgstr': "Items updated in bulk: {pid}",
        'msglvl': 'INFO',
    },
    'WEKO_INDEX_TREE_REGISTER_NEW_INDEX': {
        'msgid': 'WEKO_INDEX_TREE_I_0007',
        'msgstr': "New index is registered in the index tree.",
        'msglvl': 'INFO',
    },
    'WEKO_INDEX_TREE_UPDATE_INDEX_TREE': {
        'msgid': 'WEKO_INDEX_TREE_I_0008',
        'msgstr': "Index tree updated.",
        'msglvl': 'INFO',
    },
    'WEKO_INDEX_TREE_PUBLISH_INDEX': {
        'msgid': 'WEKO_INDEX_TREE_I_0009',
        'msgstr': "Index became open to public.",
        'msglvl': 'INFO',
    },
    'WEKO_INDEX_TREE_INDEX_NO_LONGER_PUBLISHED': {
        'msgid': 'WEKO_INDEX_TREE_I_0010',
        'msgstr': "Index is no longer published.",
        'msglvl': 'INFO',
    },
    'WEKO_INDEX_TREE_UPDATE_INDEX': {
        'msgid': 'WEKO_INDEX_TREE_I_0011',
        'msgstr': "Index updated.",
        'msglvl': 'INFO',
    },
    'WEKO_INDEX_TREE_DELETE_INDEX_TREE': {
        'msgid': 'WEKO_INDEX_TREE_I_0012',
        'msgstr': "Index tree deleted.",
        'msglvl': 'INFO',
    },
    'WEKO_INDEX_TREE_MOVED_INDEX_TREE': {
        'msgid': 'WEKO_INDEX_TREE_I_0013',
        'msgstr': "Index tree has been moved.",
        'msglvl': 'INFO',
    },
    'WEKO_INDEX_TREE_CHANGE_ORDER_ITEMS': {
        'msgid': 'WEKO_INDEX_TREE_I_0014',
        'msgstr': "The order in which items are displayed has changed.",
        'msglvl': 'INFO',
    },
    'WEKO_INDEX_TREE_DISPLAY_INDEX_LINK': {
        'msgid': 'WEKO_INDEX_TREE_I_0015',
        'msgstr': "The display setting of the index link has been changed to {configuration_value}.",
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
    param = WEKO_INDEX_TREE_MESSAGE.get(key, None)
    if param:
        weko_logger_base(param=param, ex=ex, **kwargs)
    else:
        weko_logger_base(key=key, ex=ex, **kwargs)
