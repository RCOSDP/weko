# coding:utf-8
"""Definition of topic property."""
from .property_func import get_property_schema, get_property_form, set_post_data, get_select_value
from . import property_config as config

property_id = config.TOPIC
multiple_flag = False
name_ja = 'トピック'
name_en = 'Topic'
subject_schema = [
    None,
    'Other'
]


def add(post_data, key, **kwargs):
    """Add to a item type."""
    option = kwargs.pop('option')
    set_post_data(post_data, property_id, name_ja, key, option, form, schema, **kwargs)

    kwargs.pop('mapping', True)
    post_data['table_row_map']['mapping'][key] = config.DEFAULT_MAPPING


def schema(title='', multi_flag=multiple_flag):
    """Get schema text of item type."""
    def _schema():
        """Schema text."""
        _d = {
            'type': 'object',
            'properties': {
                'subitem_topic': {
                    'format': 'text',
                    'title': 'トピック',
                    'title_i18n': {
                        'en': 'Topic',
                        'ja': 'トピック'
                    },
                    'type': 'string'
                },
                'subitem_topic_language': {
                    'editAble': True,
                    'type': ['null', 'string'],
                    'format': 'select',
                    'enum': config.LANGUAGE_VAL2_2,
                    'currentEnum': config.LANGUAGE_VAL2_2[1:],
                    'title': '言語',
                    'title_i18n': {
                        'en': 'Language',
                        'ja': '言語'
                    },
                },
                'subitem_topic_vocab': {
                    'format': 'text',
                    'title': '統制語彙',
                    'title_i18n': {
                        'en': 'Topic Vocab',
                        'ja': '統制語彙'
                    },
                    'type': 'string'
                },
                'subitem_topic_vocab_uri': {
                    'format': 'text',
                    'title': '統制語彙参照URI',
                    'title_i18n': {
                        'en': 'Topic Vocab URI',
                        'ja': '統制語彙参照URI'
                    },
                    'type': 'string'
                },
                'subitem_topic_subject_scheme': {
                    'format': 'select',
                    'title': '(JPCOAR対応用)主題スキーム',
                    'title_i18n': {
                        'en': '(for JPCOAR)Subject Scheme',
                        'ja': '(JPCOAR対応用)主題スキーム'
                    },
                    'type': ['null', 'string'],
                    'enum': subject_schema,
                    'currentEnum': subject_schema[1:]
                }
            }
        }
        return _d

    return get_property_schema(title, _schema, multi_flag)


def form(key='', title='', title_ja=name_ja, title_en=name_en, multi_flag=multiple_flag):
    """Get form text of item type."""
    def _form(key):
        """Form text."""
        _d = {
            'key': key.replace('[]', ''),
            'items': [
                {
                    'key': '{}.subitem_topic'.format(key),
                    'title': 'トピック',
                    'title_i18n': {
                        'en': 'Topic',
                        'ja': 'トピック'
                    },
                    'type': 'text'
                },
                {
                    'key': '{}.subitem_topic_language'.format(key),
                    'title': '言語',
                    'title_i18n': {
                        'en': 'Language',
                        'ja': '言語'
                    },
                    'titleMap': get_select_value(config.LANGUAGE_VAL2_2),
                    'type': 'select'
                },
                {
                    'key': '{}.subitem_topic_vocab'.format(key),
                    'title': '統制語彙',
                    'title_i18n': {
                        'en': 'Topic Vocab',
                        'ja': '統制語彙'
                    },
                    'type': 'text'
                },
                {
                    'key': '{}.subitem_topic_vocab_uri'.format(key),
                    'title': '統制語彙参照URI',
                    'title_i18n': {
                        'en': 'Topic Vocab URI',
                        'ja': '統制語彙参照URI'
                    },
                    'type': 'text'
                },
                {
                    'key': '{}.subitem_topic_subject_scheme'.format(key),
                    'title': '(JPCOAR対応用)主題スキーム',
                    'title_i18n': {
                        'en': '(for JPCOAR)Subject Scheme',
                        'ja': '(JPCOAR対応用)主題スキーム'
                    },
                    'titleMap': get_select_value(subject_schema),
                    'type': 'select'
                }
            ]
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
