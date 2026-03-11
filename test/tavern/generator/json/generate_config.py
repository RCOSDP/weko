DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DEFAULT_VALUE = {
    'string': {
        'min': 1,
        'max': 10
    },
    'int': {
        'min': 1,
        'max': 100
    },
    'float': {
        'min': 1.0,
        'max': 100.0
    },
    'date': {
        'min': '2025-01-01',
        'max': '2025-12-31'
    },
    'datetime': {
        'min': '2025-01-01 00:00:00',
        'max': '2025-12-31 23:59:59'
    },
    'list': {
        'min': 1,
        'max': 5
    }
}