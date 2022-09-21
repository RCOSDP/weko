# coding:utf-8
"""Definition of distributor property."""
from .property_func import get_property_schema, get_property_form, set_post_data, get_select_value
from . import property_config as config

property_id = config.DISTRIBUTOR
multiple_flag = False
name_ja = '配布者'
name_en = 'Distributor'
id_type = [
    None,
    'Distributor'
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
                'subitem_distributor_name': {
                    'format': 'text',
                    'title': '配布者、配布機関名',
                    'type': 'string'
                },
                'subitem_distributor_language': {
                    'editAble': True,
                    'type': ['null', 'string'],
                    'format': 'select',
                    'enum': config.LANGUAGE_VAL2_2,
                    'title': '言語'
                },
                'subitem_distributor_abbreviation': {
                    'format': 'text',
                    'title': '配布機関略称',
                    'type': 'string'
                },
                'subitem_distributor_affiliation': {
                    'format': 'text',
                    'title': '配布者の所属',
                    'type': 'string'
                },
                'subitem_distributor_uri': {
                    'format': 'text',
                    'title': '配布機関URI',
                    'type': 'string'
                },
                'subitem_distributor_id_type': {
                    'type': ['null', 'string'],
                    'format': 'select',
                    'enum': id_type,
                    'title': '(JPCOAR対応用)寄与者属性'
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
                    'key': '{}.subitem_distributor_name'.format(key),
                    'title': '配布者、配布機関名',
                    'title_i18n': {
                        'en': 'Distributor Name',
                        'ja': '配布者、配布機関名'
                    },
                    'type': 'text'
                },
                {
                    'key': '{}.subitem_distributor_language'.format(key),
                    'title': '言語',
                    'title_i18n': {
                        'en': 'Language',
                        'ja': '言語'
                    },
                    'titleMap': get_select_value(config.LANGUAGE_VAL2_1),
                    'type': 'select'
                },
                {
                    'key': '{}.subitem_distributor_abbreviation'.format(key),
                    'title': '配布機関略称',
                    'title_i18n': {
                        'en': 'Distributor Abbreviation',
                        'ja': '配布機関略称'
                    },
                    'type': 'text'
                },
                {
                    'key': '{}.subitem_distributor_affiliation'.format(key),
                    'title': '配布者の所属',
                    'title_i18n': {
                        'en': 'Distributor Affiliation',
                        'ja': '配布者の所属'
                    },
                    'type': 'text'
                },
                {
                    'key': '{}.subitem_distributor_uri'.format(key),
                    'title': '配布機関URI',
                    'title_i18n': {
                        'en': 'Distributor URI',
                        'ja': '配布機関URI'
                    },
                    'type': 'text'
                },
                {
                    'key': '{}.subitem_distributor_id_type'.format(key),
                    'title': '(JPCOAR対応用)寄与者属性',
                    'title_i18n': {
                        'en': '(for JPCOAR)Contributor Identifier Type',
                        'ja': '(JPCOAR対応用)寄与者属性'
                    },
                    'titleMap': get_select_value(id_type),
                    'type': 'select'
                }
            ],
            'key': key.replace('[]', '')
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
