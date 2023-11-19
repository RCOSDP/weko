# coding:utf-8
"""Definition of Resource Type(Simple) property."""
from .property_func import get_property_schema, get_property_form, set_post_data, get_select_value
from . import property_config as config

property_id = config.RESOURCE_TYPE_SIMPLE
multiple_flag = False
name_ja = '資源タイプ（シンプル）'
name_en = 'Resource Type(Simple)'
resource_type = [
    None,
    "journal article",
    "departmental bulletin paper",
    "doctoral thesis",
    "other"
]

def add(post_data, key, **kwargs):
    """Add resource type to a item type."""
    if 'option' in kwargs:
        kwargs.pop('option')
    option = {
        'required': True,
        'multiple': multiple_flag,
        'hidden': False,
        'showlist': False,
        'crtf': False,
        'oneline': False
    }
    set_post_data(post_data, property_id, name_ja, key, option, form, schema, **kwargs)

    if kwargs.pop('mapping', True):
        post_data['table_row_map']['mapping'][key] = {
            'display_lang_type': '',
            'jpcoar_v1_mapping': {
                'type': {
                    '@attributes': {
                        'rdf:resource': 'resourceuri'
                    },
                    '@value': 'resourcetype'
                }
            },
            'jpcoar_mapping': {
                'type': {
                    '@attributes': {
                        'rdf:resource': 'resourceuri'
                    },
                    '@value': 'resourcetype'
                }
            },
            'junii2_mapping': '',
            'lido_mapping': '',
            'lom_mapping': '',
            'oai_dc_mapping': {
                'type': {
                    '@value': 'resourcetype'
                }
            },
            'spase_mapping': ''
        }
    else:
        post_data['table_row_map']['mapping'][key] = config.DEFAULT_MAPPING


def schema(title='', multi_flag=multiple_flag):
    """Get schema text of item type."""

    def _schema():
        _d = {
            'system_prop': True,
            'type': 'object',
            'properties': {
                'resourceuri': {
                    'format': 'text',
                    'title': '資源タイプ識別子',
                    'title_i18n': {
                        'en': 'Resource Type Identifier(Simple)',
                        'ja': '資源タイプ識別子（シンプル）'
                    },
                    'type': 'string'
                },
                'resourcetype': {
                    'type': ['null', 'string'],
                    'format': 'select',
                    'enum': resource_type,
                    'currentEnum': resource_type[1:],
                    'title': '資源タイプ',
                    'title_i18n': {
                        'en': 'Resource Type(Simple)',
                        'ja': '資源タイプ（シンプル） '
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
            'items': [
                {
                    'key': '{}.resourceuri'.format(key),
                    'readonly': True,
                    'title': '資源',
                    'title_i18n': {
                        'en': 'Resource Type Identifier(Simple)',
                        'ja': '資源タイプ識別子（シンプル）'
                    },
                    'type': 'text'
                },
                {
                    'key': '{}.resourcetype'.format(key),
                    'onChange': 'resourceTypeSelect()',
                    'title': 'タイプ ',
                    'title_i18n': {
                        'en': 'Resource Type(Simple)',
                        'ja': '資源タイプ（シンプル） '
                    },
                    'titleMap': get_select_value(resource_type),
                    'type': 'select'
                }
            ],
            'key': key.replace('[]', ''),
            "title_i18n": {
                "en": "Resource Type(Simple)",
                "ja": "資源タイプ（シンプル）"
            },
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
