"""Resource for weko-theme log messages."""

WEKO_THEME_MESSAGE = {
    'WEKO_THEME_FAILED_SEARCH_ITEM': {
        'msgid': 'WEKO_THEME_E_0001',
        'msgstr': "FAILED to search item: {query}",
        'msglvl': 'ERROR',
    },
    'WEKO_THEME_FAILED_ADD_SEARCH_CONDITION': {
        'msgid': 'WEKO_THEME_E_0002',
        'msgstr': "FAILED to add search condition.",
        'msglvl': 'ERROR',
    },
    'WEKO_THEME_FAILED_DELETE_SEARCH_CONDITION': {
        'msgid': 'WEKO_THEME_E_0003',
        'msgstr': "FAILED to delete search condition.",
        'msglvl': 'ERROR',
    },
    'WEKO_THEME_FAILED_EXPORT_SEARCH_CONDITION': {
        'msgid': 'WEKO_THEME_E_0004',
        'msgstr': "FAILED to export items added to the search condition.",
        'msglvl': 'ERROR',
    },
    'WEKO_THEME_FAILED_INDEX_SEARCH': {
        'msgid': 'WEKO_THEME_E_0005',
        'msgstr': "FAILED to search item from index.",
        'msglvl': 'ERROR',
    },
    'WEKO_THEME_FAILED_SETTINGS_FACETED_SEARCH': {
        'msgid': 'WEKO_THEME_E_0006',
        'msgstr': "FAILED to change faceted search settings to {set_value}.",
        'msglvl': 'ERROR',
    },
    'WEKO_THEME_FAILED_CHANGE_ITEM_DISPLAY_SETTINGS': {
        'msgid': 'WEKO_THEME_E_0007',
        'msgstr': "FAILED to change item display method settings.",
        'msglvl': 'ERROR',
    },
    'WEKO_THEME_FAILED_OUTPUT_RSS_DOCUMENT': {
        'msgid': 'WEKO_THEME_E_0008',
        'msgstr': "FAILED to output RSS document.",
        'msglvl': 'ERROR',
    },
    'WEKO_THEME_FAILED_CREATE_WIDGET_TEMPLATE': {
        'msgid': 'WEKO_THEME_E_0009',
        'msgstr': "FAILED to create Widget templates.",
        'msglvl': 'ERROR',
    },
    'WEKO_THEME_FAILED_CHANGE_BACKGROUND_COLOUR': {
        'msgid': 'WEKO_THEME_E_0010',
        'msgstr': "FAILED to change screen background colour.",
        'msglvl': 'ERROR',
    },
    'WEKO_THEME_SEARCH_ITEM': {
        'msgid': 'WEKO_THEME_I_0001',
        'msgstr': "Search item: {query}, result: {num}",
        'msglvl': 'INFO',
    },
    'WEKO_THEME_ADD_SEARCH_CONDITION': {
        'msgid': 'WEKO_THEME_I_0002',
        'msgstr': "Search condition added.",
        'msglvl': 'INFO',
    },
    'WEKO_THEME_DELETE_SEARCH_CONDITION': {
        'msgid': 'WEKO_THEME_I_0003',
        'msgstr': "Search condition deleted.",
        'msglvl': 'INFO',
    },
    'WEKO_THEME_EXPORT_SEARCH_CONDITION': {
        'msgid': 'WEKO_THEME_I_0004',
        'msgstr': "Items added to the search condition have been exported.",
        'msglvl': 'INFO',
    },
    'WEKO_THEME_INDEX_SEARCH_RESULT': {
        'msgid': 'WEKO_THEME_I_0005',
        'msgstr': "index search : {query}, results: {num} items",
        'msglvl': 'INFO',
    },
    'WEKO_THEME_SETTINGS_FACETED_SEARCH': {
        'msgid': 'WEKO_THEME_I_0006',
        'msgstr': "Faceted search settings have been changed to {set_value}.",
        'msglvl': 'INFO',
    },
    'WEKO_THEME_CHANGE_ITEM_DISPLAY_SETTINGS': {
        'msgid': 'WEKO_THEME_I_0007',
        'msgstr': "Settings for how items are displayed have been changed.",
        'msglvl': 'INFO',
    },
    'WEKO_THEME_ENABLED_RSS_FEEDS': {
        'msgid': 'WEKO_THEME_I_0008',
        'msgstr': "RSS feeds are now enabled.",
        'msglvl': 'INFO',
    },
    'WEKO_THEME_OUTPUT_RSS_DOCUMENT': {
        'msgid': 'WEKO_THEME_I_0009',
        'msgstr': "RSS document has been output.",
        'msglvl': 'INFO',
    },
    'WEKO_THEME_CREATE_WIDGET_TEMPLATE': {
        'msgid': 'WEKO_THEME_I_0010',
        'msgstr': "Widget templates have been created.",
        'msglvl': 'INFO',
    },
    'WEKO_THEME_REGISTER_PAGE_LAYOUT': {
        'msgid': 'WEKO_THEME_I_0011',
        'msgstr': "Page layout has been registered.",
        'msglvl': 'INFO',
    },
    'WEKO_THEME_USER_AGREE_COOKIE': {
        'msgid': 'WEKO_THEME_I_0012',
        'msgstr': "Cookie use has been agreed.",
        'msglvl': 'INFO',
    },
    'WEKO_THEME_USER_REFUSE_COOKIE': {
        'msgid': 'WEKO_THEME_I_0013',
        'msgstr': "Cookie usage refused.",
        'msglvl': 'INFO',
    },
    'WEKO_THEME_CHANGE_ORDER_ITEMS': {
        'msgid': 'WEKO_THEME_I_0014',
        'msgstr': "The order in which items are displayed has changed.",
        'msglvl': 'INFO',
    },
    'WEKO_THEME_CHANGE_BACKGROUND_COLOUR': {
        'msgid': 'WEKO_THEME_I_0015',
        'msgstr': "Screen background colour has changed.",
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
    param = WEKO_THEME_MESSAGE.get(key, None)
    if param:
        weko_logger_base(param=param, ex=ex, **kwargs)
    else:
        weko_logger_base(key=key, ex=ex, **kwargs)
