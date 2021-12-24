# coding:utf-8
"""Definition of published url (doi) property."""
from .property_func import get_property_schema, get_property_form, set_post_data
import property_config as config

property_id = config.PUBLISHED_DOI_URL
multiple_flag = False
name_ja = '公表URL（DOI）'
name_en = 'Published URL (DOI)'


def add(post_data, key, **kwargs):
    """Add volume to a item type."""
    option = kwargs['option']
    set_post_data(post_data, property_id, name_ja, key, option, form, schema, **kwargs)

    post_data['table_row_map']['mapping'][key] = {
        'display_lang_type': '',
        'jpcoar_mapping': '',
        'junii2_mapping': '',
        'lido_mapping': '',
        'lom_mapping': '',
        'oai_dc_mapping': '',
        'spase_mapping': ''
    }


def schema(title='', multi_flag=multiple_flag):
    """Get schema text of item type."""
    def _schema():
        """Schema text."""
        _d = {
            'system_prop': True,
            'type': 'object',
            'properties': {
                'subitem_published_url_(doi)': {
                    'format': 'text',
                    'title': '公表URL（DOI）',
                    'type': 'string'
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
                    'key': '{}.subitem_published_url_(doi)'.format(key),
                    'title': '公表URL（DOI）',
                    'title_i18n': {
                        'en': 'Published URL (DOI)',
                        'ja': '公表URL（DOI）'
                    },
                    'type': 'text'
                }
            ],
            'key': key.replace('[]', '')
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
