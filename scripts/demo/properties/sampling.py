# coding:utf-8
"""Definition of sampling property."""
from .property_func import get_property_schema, get_property_form, set_post_data, get_select_value
from . import property_config as config

property_id = config.SAMPLING
multiple_flag = False
name_ja = '抽出'
name_en = 'Sampling'
description_type = [
    None,
    'Methods'
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
                'subitem_sampling_procedure': {
                    'format': 'text',
                    'title': '抽出方法',
                    'type': 'string'
                },
                'subitem_sampling_procedure_language': {
                    'editAble': True,
                    'type': ['null', 'string'],
                    'format': 'select',
                    'enum': config.LANGUAGE_VAL2_2,
                    'title': '言語'
                },
                'subitem_sampling_description_type': {
                    'format': 'select',
                    'title': '(JPCOAR対応用)記述タイプ',
                    'type': ['null', 'string'],
                    'enum': description_type
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
                    'key': '{}.subitem_sampling_procedure'.format(key),
                    'title': '抽出方法',
                    'title_i18n': {
                        'en': 'Sampling Procedure',
                        'ja': '抽出方法'
                    },
                    'type': 'text'
                },
                {
                    'key': '{}.subitem_sampling_procedure_language'.format(key),
                    'title': '言語',
                    'title_i18n': {
                        'en': 'Language',
                        'ja': '言語'
                    },
                    'titleMap': get_select_value(config.LANGUAGE_VAL2_2),
                    'type': 'select'
                },
                {
                    'key': '{}.subitem_sampling_description_type'.format(key),
                    'title': '(JPCOAR対応用)記述タイプ',
                    'title_i18n': {
                        'en': '(for JPCOAR)Description Type',
                        'ja': '(JPCOAR対応用)記述タイプ'
                    },
                    'titleMap': get_select_value(description_type),
                    'type': 'select'
                }
            ]
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
