# coding:utf-8
"""Definition of record name property."""
from .property_func import get_property_schema, get_property_form, set_post_data, get_select_value
import property_config as config

property_id = config.RECORD_NAME
multiple_flag = True
name_ja = '収録物名'
name_en = 'Source Title'


def add(post_data, key, **kwargs):
    """Add record name to a item type."""
    option = kwargs['option']
    set_post_data(post_data, property_id, name_ja, key, option, form, schema, **kwargs)

    post_data['table_row_map']['mapping'][key] = {
        'display_lang_type': '',
        'jpcoar_mapping': {
            'sourceTitle': {
                '@attributes': {
                    'xml:lang': 'subitem_record_name_language'
                },
                '@value': 'subitem_record_name'
            }
        },
        'junii2_mapping': '',
        'lido_mapping': '',
        'lom_mapping': '',
        'oai_dc_mapping': {
            'identifier': {
                '@value': 'subitem_record_name'
            }
        },
        'spase_mapping': ''
    }


def schema(title='', multi_flag=multiple_flag):
    """Get schema text of item type."""
    def _schema():
        """Schema text."""
        _d = {
            'type': 'object',
            'properties': {
                'subitem_record_name': {
                    'format': 'text',
                    'title': '収録物名',
                    'type': 'string'
                },
                'subitem_record_name_language': {
                    'editAble': True,
                    'enum': config.LANGUAGE_VAL2_1,
                    'format': 'select',
                    'title': '言語',
                    'type': ['null', 'string']
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
                    'key': '{}.subitem_record_name_language'.format(key),
                    'title': '言語',
                    'title_i18n': {
                        'ja': '言語',
                        'en': 'Language'
                    },
                    'titleMap': get_select_value(config.LANGUAGE_VAL2_1),
                    'type': 'select'
                },
                {
                    'key': '{}.subitem_record_name'.format(key),
                    'title': '収録物名',
                    'title_i18n': {
                        'ja': '収録物名',
                        'en': 'Source Title'
                    },
                    'type': 'text'
                }
            ],
            'key': key.replace('[]', '')
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
