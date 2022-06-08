# coding:utf-8
"""Definition of heading property."""
from .property_func import get_property_schema, get_property_form, set_post_data, get_select_value
from . import property_config as config

property_id = config.HEADING
multiple_flag = True
name_ja = '見出し'
name_en = 'Heading'


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
            'system_prop': True,
            'type': 'object',
            'properties': {
                'subitem_heading_banner_headline': {
                    'format': 'text',
                    'title': '大見出し',
                    'type': 'string'
                },
                'subitem_heading_headline': {
                    'format': 'text',
                    'title': '小見出し',
                    'type': 'string'
                },
                'subitem_heading_language': {
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
                    'key': '{}.subitem_heading_banner_headline'.format(key),
                    'title': '大見出し',
                    'title_i18n': {
                        'en': 'Heading',
                        'ja': '大見出し'
                    },
                    'type': 'text'
                },
                {
                    'key': '{}.subitem_heading_headline'.format(key),
                    'title': '小見出し',
                    'title_i18n': {
                        'en': 'Subheading',
                        'ja': '小見出し'
                    },
                    'type': 'text'
                },
                {
                    'key': '{}.subitem_heading_language'.format(key),
                    'title': '言語',
                    'titleMap': get_select_value(config.LANGUAGE_VAL2_1),
                    'title_i18n': {
                        'en': 'Language',
                        'ja': '言語'
                    },
                    'type': 'select'
                }
            ],
            'key': key.replace('[]', '')
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
