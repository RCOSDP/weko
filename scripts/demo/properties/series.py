# coding:utf-8
"""Definition of series property."""
from .property_func import get_property_schema, get_property_form, set_post_data, get_select_value
from . import property_config as config

property_id = config.SERIES
multiple_flag = False
name_ja = 'シリーズ'
name_en = 'Series'


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
                'subitem_series': {
                    'format': 'text',
                    'title': 'シリーズ',
                    'type': 'string'
                },
                'subitem_series_language': {
                    'editAble': True,
                    'type': ['null', 'string'],
                    'format': 'select',
                    'enum': config.LANGUAGE_VAL2_2,
                    'title': '言語'
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
            'items': [
                {
                    'key': '{}.subitem_series'.format(key),
                    'title': 'シリーズ',
                    'title_i18n': {
                        'ja': 'シリーズ',
                        'en': 'Series'
                    },
                    'type': 'text'
                },
                {
                    'key': '{}.subitem_series_language'.format(key),
                    'title': '言語',
                    'title_i18n': {
                        'ja': '言語',
                        'en': 'Language'
                    },
                    'titleMap': get_select_value(config.LANGUAGE_VAL2_2),
                    'type': 'select'
                }
            ],
            'key': key.replace('[]', '')
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
