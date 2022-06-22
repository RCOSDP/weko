# coding:utf-8
"""Definition of advisor property."""
from .property_func import get_property_schema, get_property_form, set_post_data
from . import property_config as config

property_id = config.ADVISOR
multiple_flag = False
name_ja = '指導教員'
name_en = 'Advisor'


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
                'subitem_advisor_fullname': {
                    'title': '[指導教員] 氏名',
                    'type': 'string',
                    'format': 'text',
                },
                'subitem_advisor_mail_address': {
                    'title': '[指導教員] メールアドレス',
                    'type': 'string',
                    'format': 'text',
                    'pattern': '^\\S+@\\S+$',
                },
                'subitem_advisor_phone_number': {
                    'title': '[指導教員] 電話番号',
                    'type': 'string',
                    'format': 'text',
                    'pattern': '\\d+',
                },
                'subitem_advisor_position': {
                    'title': '[指導教員] 役職',
                    'type': ['null', 'string'],
                    'format': 'string',
                    'enum': [],
                },
                'subitem_advisor_position(others)': {
                    'title': '[指導教員] 役職（その他）',
                    'type': 'string',
                    'format': 'text',
                },
                'subitem_advisor_university/institution': {
                    'title': '[指導教員] 所属',
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
                    'key': '{}.subitem_advisor_fullname'.format(key),
                    'title': '[指導教員] 氏名',
                    'title_i18n': {
                        'en': '[Advisor] Full name',
                        'ja': '[指導教員] 氏名'
                    },
                    'type': 'text'
                },
                {
                    'approval': True,
                    'key': '{}.subitem_advisor_mail_address'.format(key),
                    'title': '[指導教員] メールアドレス',
                    'title_i18n': {
                        'en': '[Advisor] Mail Address',
                        'ja': '[指導教員] メールアドレス'
                    },
                    'type': 'text'
                },
                {
                    'key': '{}.subitem_advisor_phone_number'.format(key),
                    'title': '[指導教員] 電話番号',
                    'title_i18n': {
                        'en': '[Advisor] Phone number',
                        'ja': '[指導教員] 電話番号'
                    },
                    'type': 'text'
                },
                {
                    'key': '{}.subitem_advisor_position'.format(key),
                    'title': '[指導教員] 役職',
                    'title_i18n': {
                        'en': '[Advisor] Position',
                        'ja': '[指導教員] 役職'
                    },
                    'type': 'text'
                },
                {
                    'key': '{}.subitem_advisor_position(others)'.format(key),
                    'title': '[指導教員] 役職（その他）',
                    'title_i18n': {
                        'en': '[Advisor] Position(Others)',
                        'ja': '[指導教員] 役職（その他）'
                    },
                    'type': 'text'
                },
                {
                    'key': '{}.subitem_advisor_university/institution'.format(key),
                    'title': '[指導教員] 所属',
                    'title_i18n': {
                        'en': '[Advisor] University/Institution',
                        'ja': '[指導教員] 所属'
                    },
                    'type': 'text'
                }
            ],
            'key': key.replace('[]', '')
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
