# coding:utf-8
"""Definition of title property."""
from .property_func import get_property_schema, get_property_form, set_post_data, get_select_value
from . import property_config as config

property_id = config.TITLE
multiple_flag = True
name_ja = 'タイトル'
name_en = 'Title'


def add(post_data, key, **kwargs):
    """Add to a item type."""
    option = kwargs.pop('option')
    set_post_data(post_data, property_id, name_ja, key, option, form, schema, **kwargs)

    if kwargs.pop('mapping', True):
        post_data['table_row_map']['mapping'][key] = {
            'display_lang_type': '',
            'jpcoar_v1_mapping': {
                'title': {
                    '@value': 'subitem_title',
                    '@attributes': {
                        'xml:lang': 'subitem_title_language'
                    }
                }
            },
            'jpcoar_mapping': {
                'title': {
                    '@value': 'subitem_title',
                    '@attributes': {
                        'xml:lang': 'subitem_title_language'
                    }
                }
            },
            'junii2_mapping': '',
            'lido_mapping': '',
            'lom_mapping': '',
            'oai_dc_mapping': {
                'title': {
                    '@value': 'subitem_title'
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
                'subitem_title': {
                    'format': 'text',
                    'type': 'string',
                    'title': 'タイトル',
                    "title_i18n": {
                            "en": "Title",
                            "ja": "タイトル"
                    },
                },
                'subitem_title_language': {
                    'editAble': True,
                    'type': ['null', 'string'],
                    'format': 'select',
                    'currentEnum': (config.LANGUAGE_VAL2_1)[1:],
                    'enum': config.LANGUAGE_VAL2_1,
                    'title': '言語',
                    "title_i18n": {
                            "en": "Language",
                            "ja": "言語"
                    },
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
            "title": "Title",
            'items': [
                {
                    'key': '{}.subitem_title'.format(key),
                    'title': 'タイトル',
                    'title_i18n': {
                        'ja': 'タイトル',
                        'en': 'Title'
                    },
                    'title_i18n_temp': {
                        'ja': 'タイトル',
                        'en': 'Title'
                    },
                    'type': 'text'
                },
                {
                    'key': '{}.subitem_title_language'.format(key),
                    'title': '言語',
                    'title_i18n': {
                        'ja': '言語',
                        'en': 'Language'
                    },
                    'title_i18n_temp': {
                        'ja': '言語',
                        'en': 'Language'
                    },
                    'titleMap': get_select_value(config.LANGUAGE_VAL2_1),
                    'type': 'select'
                }
            ],
            'key': key.replace('[]', '')
        }
        
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
