# coding:utf-8
"""Definition of thumbnail property."""
from .property_func import get_property_schema, get_property_form, set_post_data, get_select_value
from . import property_config as config

property_id = config.THUMBNAIL
multiple_flag = False
name_ja = 'サムネイル'
name_en = 'Thumbnail'


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
                'subitem_thumbnail': {
                    'type': 'array',
                    'format': 'array',
                    'title': 'URI',
                    'items': {
                        'type': 'object',
                        'format': 'object',
                        'properties': {
                            'thumbnail_label': {
                                'format': 'text',
                                'title': 'ラベル',
                                'type': 'string'
                            },
                            'thumbnail_url': {
                                'format': 'text',
                                'title': 'URI',
                                'type': 'string'
                            }
                        }
                    }
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
                    'add': 'New',
                    'key': '{}.subitem_thumbnail'.format(key),
                    'items': [
                        {
                            'key': '{}.subitem_thumbnail[].thumbnail_url'.format(key),
                            'readonly': True,
                            'title': 'URI',
                            'title_i18n': {
                                'en': 'URI',
                                'ja': 'URI'
                            },
                            'type': 'text'
                        },
                        {
                            'key': '{}.subitem_thumbnail[].thumbnail_label'.format(key),
                            'readonly': True,
                            'title': 'ラベル',
                            'title_i18n': {
                                'en': 'Label',
                                'ja': 'ラベル'
                            },
                            'type': 'text'
                        }
                    ],
                    'style': {
                        'add': 'btn-success'
                    },
                    'title': 'URI'
                }
            ],
            'key': key.replace('[]', '')
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
