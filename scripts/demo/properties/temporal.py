# coding:utf-8
"""Definition of temporal property."""
from .property_func import get_property_schema, get_property_form, set_post_data, get_select_value
from . import property_config as config

property_id = config.TEMPORAL
multiple_flag = True
name_ja = '時間的範囲'
name_en = 'Temporal'


def add(post_data, key, **kwargs):
    """Add to a item type."""
    option = kwargs.pop('option')
    set_post_data(post_data, property_id, name_ja, key, option, form, schema, **kwargs)

    if kwargs.pop('mapping', True):
        post_data['table_row_map']['mapping'][key] = {
            'display_lang_type': '',
            'jpcoar_v1_mapping': {
                'temporal': {
                    '@attributes': {
                        'xml:lang': 'subitem_temporal_language'
                    },
                    '@value': 'subitem_temporal_text'
                }
            },
            'jpcoar_mapping': {
                'temporal': {
                    '@attributes': {
                        'xml:lang': 'subitem_temporal_language'
                    },
                    '@value': 'subitem_temporal_text'
                }
            },
            'junii2_mapping': '',
            'lido_mapping': '',
            'lom_mapping': '',
            'oai_dc_mapping': {
                'coverage': {
                    '@value': 'subitem_temporal_text'
                }
            },
            'spase_mapping': ''
        }
    else:
        post_data['table_row_map']['mapping'][key] = config.DEFAULT_MAPPING


def schema(title='', multi_flag=multiple_flag):
    """Get schema text of item type."""
    def _schema():
        """Schema text."""
        _d = {
            'type': 'object',
            'properties': {
                'subitem_temporal_text': {
                    'format': 'text',
                    'title': '時間的範囲',
                    'type': 'string'
                },
                'subitem_temporal_language': {
                    'editAble': True,
                    'type': ['null', 'string'],
                    'format': 'select',
                    'enum': config.LANGUAGE_VAL2_1,
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
                    'key': '{}.subitem_temporal_text'.format(key),
                    'title': '時間的範囲',
                    'title_i18n': {
                        'en': 'Temporal',
                        'ja': '時間的範囲'
                    },
                    'type': 'text'
                },
                {
                    'key': '{}.subitem_temporal_language'.format(key),
                    'title': '言語',
                    'title_i18n': {
                        'en': 'Language',
                        'ja': '言語'
                    },
                    'titleMap': get_select_value(config.LANGUAGE_VAL2_1),
                    'type': 'select'
                }
            ],
            'key': key.replace('[]', '')
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
