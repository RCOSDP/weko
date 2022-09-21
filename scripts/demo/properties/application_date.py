# coding:utf-8
"""Definition of application date property."""
from .property_func import get_property_schema, get_property_form, set_post_data, get_select_value
from . import property_config as config

property_id = config.APPLICATION_DATE
multiple_flag = False
name_ja = '申請日'
name_en = 'Application Date'
date_type = ['Issued']


def add(post_data, key, **kwargs):
    """Add to a item type."""
    option = kwargs.pop('option')
    set_post_data(post_data, property_id, name_ja, key, option, form, schema, **kwargs)

    if kwargs.pop('mapping', True):
        post_data['table_row_map']['mapping'][key] = {
            'display_lang_type': '',
            'jpcoar_v1_mapping':  {
                'date': {
                    '@attributes': {
                        'dateType': 'subitem_restricted_access_application_date_type'
                    },
                    '@value': 'subitem_restricted_access_application_date'
                }
            },
            'jpcoar_mapping':  {
                'date': {
                    '@attributes': {
                        'dateType': 'subitem_restricted_access_application_date_type'
                    },
                    '@value': 'subitem_restricted_access_application_date'
                }
            },
            'junii2_mapping': '',
            'lido_mapping': '',
            'lom_mapping': '',
            'oai_dc_mapping': '',
            'spase_mapping': ''
        }
    else:
        post_data['table_row_map']['mapping'][key] = config.DEFAULT_MAPPING


def schema(title='', multi_flag=multiple_flag):
    """Get schema text of item type."""
    def _schema():
        """Schema text."""
        _d = {
            'system_prop': True,
            'type': 'object',
            'properties': {
                'subitem_restricted_access_application_date': {
                    'format': 'datetime',
                    'title': '申請日',
                    'type': 'string'
                },
                'subitem_restricted_access_application_date_type': {
                    'type': 'string',
                    'format': 'select',
                    'enum': date_type,
                    'title': '申請日タイプ'
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
                    'format': 'yyyy-MM-dd',
                    'key': '{}.subitem_restricted_access_application_date'.format(key),
                    'templateUrl': config.DATEPICKER_MULTI_FORMAT_URL,
                    'title': '申請日',
                    'title_i18n': {
                        'ja': '申請日',
                        'en': 'Application Date'
                    },
                    'type': 'template'
                },
                {
                    'key': '{}.subitem_restricted_access_application_date_type'.format(key),
                    'title': '申請日タイプ',
                    'title_i18n': {
                        'ja': '申請日タイプ',
                        'en': 'Application Date Type'
                    },
                    'titleMap': get_select_value(date_type),
                    'type': 'select'
                }
            ],
            'key': key.replace('[]', '')
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
