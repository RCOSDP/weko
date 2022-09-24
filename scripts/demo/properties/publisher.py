# coding:utf-8
"""Definition of publisher property."""
from .property_func import get_property_schema, get_property_form, set_post_data, get_select_value
from . import property_config as config

property_id = config.PUBLISHER
multiple_flag = True
name_ja = '出版者'
name_en = 'Publisher'


def add(post_data, key, **kwargs):
    """Add to a item type."""
    option = kwargs.pop('option')
    set_post_data(post_data, property_id, name_ja, key, option, form, schema, **kwargs)

    if kwargs.pop('mapping', True):
        post_data['table_row_map']['mapping'][key] = {
            'display_lang_type': '',
            'jpcoar_v1_mapping': {
                'publisher': {
                    '@attributes': {
                        'xml:lang': 'subitem_publisher_language'
                    },
                    '@value': 'subitem_publisher'
                }
            },
            'jpcoar_mapping': {
                'publisher': {
                    '@attributes': {
                        'xml:lang': 'subitem_publisher_language'
                    },
                    '@value': 'subitem_publisher'
                }
            },
            'junii2_mapping': '',
            'lido_mapping': '',
            'lom_mapping': '',
            'oai_dc_mapping': {
                'publisher': {
                    '@value': 'subitem_publisher'
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
                'subitem_publisher': {
                    'format': 'text',
                    'title': '出版者',
                    'type': 'string'
                },
                'subitem_publisher_language': {
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
                    'key': '{}.subitem_publisher_language'.format(key),
                    'title': '言語',
                    'title_i18n': {
                        'en': 'Language',
                        'ja': '言語'
                    },
                    'titleMap': get_select_value(config.LANGUAGE_VAL2_1),
                    'type': 'select'
                },
                {
                    'key': '{}.subitem_publisher'.format(key),
                    'title': '出版者',
                    'title_i18n': {
                        'en': 'Publisher',
                        'ja': '出版者'
                    },
                    'type': 'text'
                }
            ],
            'key': key.replace('[]', '')
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
