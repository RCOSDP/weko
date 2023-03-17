# coding:utf-8
"""Definition of guarantor property."""
from .property_func import get_property_schema, get_property_form, set_post_data
from . import property_config as config

property_id = config.GUARANTOR
multiple_flag = False
name_ja = '保証人'
name_en = 'Guarantor'


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
                'subitem_guarantor_fullname': {
                    'title': '[保証人] 氏名',
                    'type': 'string',
                    'format': 'text',
                },
                'subitem_guarantor_mail_address': {
                    'title': '[保証人] メールアドレス',
                    'type': 'string',
                    'format': 'text',
                    'pattern': '^\\S+@\\S+$',
                },
                'subitem_guarantor_phone_number': {
                    'title': '[保証人] 電話番号',
                    'type': 'string',
                    'format': 'text',
                    'pattern': '\\d+',
                },
                'subitem_guarantor_position': {
                    'title': '[保証人] 役職',
                    'type': ['null', 'string'],
                    'format': 'string',
                    'enum': [],
                },
                'subitem_guarantor_position(others)': {
                    'title': '[保証人] 役職（その他）',
                    'type': 'string',
                    'format': 'text',
                },
                'subitem_guarantor_university/institution': {
                    'title': '[保証人] 所属',
                    'type': 'string',
                    'format': 'text',
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
                    'key': '{}.subitem_guarantor_fullname'.format(key),
                    'title': '[保証人] 氏名',
                    'title_i18n': {
                        'en': '[Guarantor] Full name',
                        'ja': '[保証人] 氏名'
                    },
                    'type': 'text'
                },
                {
                    'approval': True,
                    'key': '{}.subitem_guarantor_mail_address'.format(key),
                    'title': '[保証人] メールアドレス',
                    'title_i18n': {
                        'en': '[Guarantor] Mail Address',
                        'ja': '[保証人] メールアドレス'
                    },
                    'type': 'text'
                },
                {
                    'key': '{}.subitem_guarantor_phone_number'.format(key),
                    'title': '[保証人] 電話番号',
                    'title_i18n': {
                        'en': '[Guarantor] Phone number',
                        'ja': '[保証人] 電話番号'
                    },
                    'type': 'text'
                },
                {
                    'key': '{}.subitem_guarantor_position'.format(key),
                    'title': '[保証人] 役職',
                    'title_i18n': {
                        'en': '[Guarantor] Position',
                        'ja': '[保証人] 役職'
                    },
                    'type': 'text'
                },
                {
                    'key': '{}.subitem_guarantor_position(others)'.format(key),
                    'title': '[保証人] 役職（その他）',
                    'title_i18n': {
                        'en': '[Guarantor] Position(Others)',
                        'ja': '[保証人] 役職（その他）'
                    },
                    'type': 'text'
                },
                {
                    'key': '{}.subitem_guarantor_university/institution'.format(key),
                    'title': '[保証人] 所属',
                    'title_i18n': {
                        'en': '[Guarantor] University/Institution',
                        'ja': '[保証人] 所属'
                    },
                    'type': 'text'
                }
            ],
            'key': key.replace('[]', '')
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
