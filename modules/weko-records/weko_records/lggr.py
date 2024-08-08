"""Resource for weko-records log messages."""

WEKO_ACCOUNTS_MESSAGE = {
    'WEKO_RECORDS_SEARCH_ITEM': {
        'msgid': 'WEKO_RECORDS_INFO_1401',
        'msgstr': "Search item: {query}, result: {num}",
        'msglvl': 'INFO',
    },
    'WEKO_RECORDS_FAILED_SEARCH_ITEM': {
        'msgid': 'WEKO_RECORDS_ERROR_1401',
        'msgstr': "FAILED to search item: {query}",
        'msglvl': 'ERROR',
    },
    'WEKO_RECORDS_ENABLED_RSS_FEEDS': {
        'msgid': 'WEKO_RECORDS_INFO_1402',
        'msgstr': "RSS feeds are now enabled.",
        'msglvl': 'INFO',
    },
    'WEKO_RECORDS_OUTPUT_RSS_DOCUMENT': {
        'msgid': 'WEKO_RECORDS_INFO_1403',
        'msgstr': "RSS document has been output.",
        'msglvl': 'INFO',
    },
    'WEKO_RECORDS_FAILED_OUTPUT_RSS_DOCUMENT': {
        'msgid': 'WEKO_RECORDS_ERROR_1402',
        'msgstr': "FAILED to output RSS document.",
        'msglvl': 'ERROR',
    },
    'WEKO_RECORDS_SERIALIZE_RESULT_TO_RSS': {
        'msgid': 'WEKO_RECORDS_INFO_1404',
        'msgstr': "Serialized search results into RSS format.",
        'msglvl': 'INFO',
    },
    'WEKO_RECORDS_FAILED_SERIALIZE_RESULT_TO_RSS': {
        'msgid': 'WEKO_RECORDS_ERROR_1403',
        'msgstr': "FAILED to serialize search results into RSS format.",
        'msglvl': 'ERROR',
    },
    'WEKO_RECORDS_DELETE_RECORD': {
        'msgid': 'WEKO_RECORDS_INFO_1405',
        'msgstr': "{dlt_nm} record was deleted. Uuid: {uuid}",
        'msglvl': 'INFO',
    },
    'WEKO_RECORDS_RESTORE_RECORD': {
        'msgid': 'WEKO_RECORDS_INFO_1406',
        'msgstr': "Record restored. Uuid: {uuid}",
        'msglvl': 'INFO',
    },
    'WEKO_RECORDS_FAILED_DELETE_RECORD': {
        'msgid': 'WEKO_RECORDS_ERROR_1404',
        'msgstr': "FAILED to delete records. Uuid: {uuid}",
        'msglvl': 'ERROR',
    },
    'WEKO_RECORDS_FAILED_RESTORE_RECORD': {
        'msgid': 'WEKO_RECORDS_ERROR_1405',
        'msgstr': "FAILED to restore record. Uuid: {uuid}",
        'msglvl': 'ERROR',
    },
}
