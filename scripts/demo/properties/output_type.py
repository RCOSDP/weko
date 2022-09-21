# coding:utf-8
"""Definition of output type property."""
from .property_func import get_property_schema, get_property_form, set_post_data, get_select_value
from . import property_config as config

property_id = config.OUTPUT_TYPE
multiple_flag = False
name_ja = '成果物のタイプ'
name_en = 'Output Type'
output_type = {
    'Books': '図書',
    'Thesis (refereed)': '論文（査読有り）',
    'Thesis (unrefereed)': '論文（査読無し）',
    'Conference report (international conference or abroad conference)':
    '学会報告（国際学会または国外学会）',
    'Conference report (domestic conference)':
    '学会報告（国内学会）',
    'Others': 'その他'
}


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
                'subitem_output_type': {
                    'title': '成果物のタイプ',
                    'type': 'string',
                    'format': 'radios',
                    'enum': list(output_type.keys())
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
                    'key': '{}.subitem_output_type'.format(key),
                    'title': '成果物のタイプ',
                    'title_i18n': {
                        'en': 'Output Type',
                        'ja': '成果物のタイプ'
                    },
                    'titleMap': get_select_value(output_type),
                    'type': 'radios'
                }
            ],
            'key': key.replace('[]', '')
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
