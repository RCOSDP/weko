# coding:utf-8
"""Common source code."""


def _schema():
    return {}


def get_property_schema(title='', _schema=_schema, multi_flag=False):
    """Get schema text of item type.

    Args:
        title (str, optional): Schema title. Defaults to ''.
        _schema ([type], optional): Schema function. Defaults to _schema.
        multi_flag (bool, optional): Multiple flag. Defaults to False.

    Returns:
        [dict]: schema property.
    """
    if title:
        if multi_flag:
            schema_property = {
                'type': 'array',
                'title': title,
                'minItems': '1',
                'maxItems': '9999',
                'items': _schema()
            }
        else:
            schema_property = _schema()
            schema_property['title'] = title
    else:
        schema_property = _schema()
        schema_property['format'] = 'object'

    return schema_property


def _form(key):
    return {'key': key.replace('[]', '')}


def get_property_form(key='', title='', title_ja='', title_en='', multi_flag=False,
         _form=_form):
    """Get form text of item type.

    Args:
        key (str, optional): parent key. Defaults to ''.
        title (str, optional): title. Defaults to ''.
        title_ja (str, optional): title in Japanese. Defaults to ''.
        title_en (str, optional): title in English. Defaults to ''.
        multi_flag (bool, optional): Multiple flag. Defaults to False.
        _form ([type], optional): form function. Defaults to _form.

    Returns:
        [dict]: form property.
    """
    if key:
        if multi_flag:
            d = _form('{}[]'.format(key))
            d['add'] = 'New'
            d['style'] = {'add': 'btn-success'}
        else:
            d = _form(key)
            d['type'] = 'fieldset'
        d['title'] = title
    else:
        if multi_flag:
            d = _form('parentkey[]')
            d['add'] = 'New'
            d['style'] = {'add': 'btn-success'}
        else:
            d = _form('parentkey')
            d['type'] = 'fieldset'
    d['title_i18n'] = {'ja': title_ja, 'en': title_en}
    return d


def set_post_data(post_data, property_id, name, key, option, form, schema, **kwargs):
    """Set meta list data.

    Args:
        post_dat (dict, optional): item type data.
        property_id (str, optional): property id.
        name (str, optional): property name.
        key (str, optional): property key.
        option (dict, optional): property option.
        form ([type], optional): form function.
        schema ([type], optional): schema function.
    """
    title = kwargs.get('title', name)
    title_ja = kwargs.get('title_ja', '')
    title_en = kwargs.get('title_en', '')
    sys_property = kwargs.get('sys_property', False)

    post_data['table_row_map']['form'].append(form(key, title, title_ja, title_en, option['multiple']))
    post_data['table_row_map']['schema']['properties'][key] = schema(title, option['multiple'])
    if option['required']:
        post_data['table_row_map']['schema']['required'].append(key)
    meta_data = {
        'title': title,
        'title_i18n': {
            'ja': title_ja,
            'en': title_en
        },
        'input_type': 'cus_' + property_id,
        'input_value': '',
        'option': {
            'required': option['required'],
            'multiple': option['multiple'],
            'hidden': option['hidden'],
            'showlist': option['showlist'],
            'crtf': option['crtf'],
            'oneline': option['oneline']
        }
    }
    if sys_property:
        post_data['meta_system'][key] = meta_data
    else:
        post_data['table_row'].append(key)
        post_data['schemaeditor']['schema'][key] = schema(multi_flag=False)
        meta_data['input_minItems'] = '1'
        meta_data['input_maxItems'] = '9999'
        post_data['meta_list'][key] = meta_data
        post_data['edit_notes'][key] = ''


def get_select_value(value_list=None):
    """Get select item of item type.

    Args:
        value_list ([type], optional): select value data. Defaults to None.

    Returns:
        [list]: select item list.
    """
    if value_list:
        if isinstance(value_list, list):
            return [{'name': v, 'value': v} for v in value_list if v is not None]
        elif isinstance(value_list, dict):
            return [{'name': k, 'value': k, 'name_i18n': {'en': k, 'ja': v}}
                    for k, v in value_list.items() if k is not None]
        else:
            return []
    else:
        return []
