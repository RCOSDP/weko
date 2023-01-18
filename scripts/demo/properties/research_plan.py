# coding:utf-8
"""Definition of research plan property."""
from .property_func import get_property_schema, get_property_form, set_post_data
from . import property_config as config

property_id = config.RESEARCH_PLAN
multiple_flag = False
name_ja = '研究計画'
name_en = 'Research Plan'


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
                'subitem_research_plan': {
                    'title': '研究計画',
                    'type': 'string',
                    'format': 'textarea',
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
                    'key': '{}.subitem_research_plan'.format(key),
                    'title': '研究計画',
                    'title_i18n': {
                        'en': 'Research Plan',
                        'ja': '研究計画'
                    },
                    'type': 'textarea'
                }
            ],
            'key': key.replace('[]', '')
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
