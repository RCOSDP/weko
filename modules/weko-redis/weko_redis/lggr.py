"""Resource for weko-redis log messages."""

WEKO_ACCOUNTS_MESSAGE = {
    'WEKO_REDIS_SUCCESS_DIRECT_REDIS_CONNECT': {
        'msgid': 'WEKO_REDIS_INFO_1601',
        'msgstr': "Direct Redis connection established successfully.",
        'msglvl': 'INFO',
    },
    'WEKO_REDIS_FAILED_DIRECT_REDIS_CONNECT': {
        'msgid': 'WEKO_REDIS_ERROR_1601',
        'msgstr': "FAILED direct Redis connection.",
        'msglvl': 'ERROR',
    },
    'WEKO_REDIS_SUCCESS_DATA_STORE_CONNECT': {
        'msgid': 'WEKO_REDIS_INFO_1602',
        'msgstr': "Data store connection established successfully via Redis.",
        'msglvl': 'INFO',
    },
    'WEKO_REDIS_FAILED_DATA_STORE_CONNECT': {
        'msgid': 'WEKO_REDIS_ERROR_1602',
        'msgstr': "FAILED data store connection via Redis.",
        'msglvl': 'ERROR',
    },
    'WEKO_REDIS_SUCCESS_REDIS_SENTINEL_CONNECT': {
        'msgid': 'WEKO_REDIS_INFO_1603',
        'msgstr': "Redis Sentinel connection established successfully.",
        'msglvl': 'INFO',
    },
    'WEKO_REDIS_FAILED_REDIS_SENTINEL_CONNECT': {
        'msgid': 'WEKO_REDIS_ERROR_1603',
        'msgstr': "FAILED Redis Sentinel connection.",
        'msglvl': 'ERROR',
    },
}
