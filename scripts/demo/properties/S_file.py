# coding:utf-8
"""Definition of system file property."""
from .property_func import get_property_schema, get_property_form, set_post_data, get_select_value
from . import property_config as config

property_id = config.S_FILE
multiple_flag = False
name = name_ja = name_en = 'S_File'
date_type = [
    'Accepted',
    'Available',
    'Collected',
    'Copyrighted',
    'Created',
    'Issued',
    'Submitted',
    'Updated',
    'Valid'
]
filename_type = [
    'Abstract',
    'Fulltext',
    'Summary',
    'Thumbnail',
    'Other'
]

def add(post_data, key, **kwargs):
    """Add to a item type."""
    option = {
        "crtf": False,
        "hidden": True,
        "oneline": False,
        "multiple": False,
        "required": False,
        "showlist": False
    }
    kwargs['sys_property'] = True
    set_post_data(post_data, property_id, name, key, option, form, schema, **kwargs)

    post_data['table_row_map']['mapping'][key] = {
        'display_lang_type': '',
        'jpcoar_v1_mapping': {
            'system_file': {
                'URI': {
                    '@value': 'subitem_systemfile_filename_uri',
                    '@attributes': {
                        'label': 'subitem_systemfile_filename_label',
                        'objectType': 'subitem_systemfile_filename_type'
                    }
                },
                'date': {
                    '@value': 'subitem_systemfile_datetime_date',
                    '@attributes': {
                        'dateType': 'subitem_systemfile_datetime_type'
                    }
                },
                'extent': {
                    '@value': 'subitem_systemfile_size'
                },
                'version': {
                    '@value': 'subitem_systemfile_version'
                },
                'mimeType': {
                    '@value': 'subitem_systemfile_mimetype'
                }
            }
        },
        'jpcoar_mapping': {
            'system_file': {
                'URI': {
                    '@value': 'subitem_systemfile_filename_uri',
                    '@attributes': {
                        'label': 'subitem_systemfile_filename_label',
                        'objectType': 'subitem_systemfile_filename_type'
                    }
                },
                'date': {
                    '@value': 'subitem_systemfile_datetime_date',
                    '@attributes': {
                        'dateType': 'subitem_systemfile_datetime_type'
                    }
                },
                'extent': {
                    '@value': 'subitem_systemfile_size'
                },
                'version': {
                    '@value': 'subitem_systemfile_version'
                },
                'mimeType': {
                    '@value': 'subitem_systemfile_mimetype'
                }
            }
        },
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
                'subitem_systemfile_size': {
                    'type': 'string',
                    'title': 'SYSTEMFILE Size',
                    'format': 'text'
                },
                'subitem_systemfile_version': {
                    'type': 'string',
                    'title': 'SYSTEMFILE Version',
                    'format': 'text'
                },
                'subitem_systemfile_datetime': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'format': 'object',
                        'properties': {
                            'subitem_systemfile_datetime_date': {
                                'type': 'string',
                                'title': 'SYSTEMFILE DateTime Date',
                                'format': 'datetime'
                            },
                            'subitem_systemfile_datetime_type': {
                                'enum': date_type,
                                'type': 'string',
                                'title': 'SYSTEMFILE DateTime Type',
                                'format': 'select'
                            }
                        }
                    },
                    'title': 'SYSTEMFILE DateTime',
                    'format': 'array'
                },
                'subitem_systemfile_filename': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'format': 'object',
                        'properties': {
                            'subitem_systemfile_filename_uri': {
                                'type': 'string',
                                'title': 'SYSTEMFILE Filename URI',
                                'format': 'text'
                            },
                            'subitem_systemfile_filename_type': {
                                'enum': filename_type,
                                'type': 'string',
                                'title': 'SYSTEMFILE Filename Type',
                                'format': 'select'
                            },
                            'subitem_systemfile_filename_label': {
                                'type': 'string',
                                'title': 'SYSTEMFILE Filename Label',
                                'format': 'text'
                            }
                        }
                    },
                    'title': 'SYSTEMFILE Filename',
                    'format': 'array'
                },
                'subitem_systemfile_mimetype': {
                    'type': 'string',
                    'title': 'SYSTEMFILE MimeType',
                    'format': 'text'
                }
            }
        }
        return _d

    return get_property_schema(title, _schema, multi_flag)


def form(key='', title='', title_ja='', title_en='', multi_flag=multiple_flag):
    """Get form text of item type."""
    def _form(key):
        """Form text."""
        _d = {
            'items': [
                {
                    'add': 'New',
                    'key': 'parentkey.subitem_systemfile_filename',
                    'items': [
                        {
                            'key': 'parentkey.subitem_systemfile_filename[].subitem_systemfile_filename_label',
                            'type': 'text',
                            'title': 'SYSTEMFILE Filename Label'
                        },
                        {
                            'key': 'parentkey.subitem_systemfile_filename[].subitem_systemfile_filename_type',
                            'type': 'select',
                            'title': 'SYSTEMFILE Filename Type',
                            'titleMap': get_select_value(filename_type)
                        },
                        {
                            'key': 'parentkey.subitem_systemfile_filename[].subitem_systemfile_filename_uri',
                            'type': 'text',
                            'title': 'SYSTEMFILE Filename URI'
                        }
                    ],
                    'style': {
                        'add': 'btn-success'
                    },
                    'title': 'SYSTEMFILE Filename'
                },
                {
                    'key': 'parentkey.subitem_systemfile_mimetype',
                    'type': 'text',
                    'title': 'SYSTEMFILE MimeType'
                },
                {
                    'key': 'parentkey.subitem_systemfile_size',
                    'type': 'text',
                    'title': 'SYSTEMFILE Size'
                },
                {
                    'add': 'New',
                    'key': 'parentkey.subitem_systemfile_datetime',
                    'items': [
                        {
                            'key': 'parentkey.subitem_systemfile_datetime[].subitem_systemfile_datetime_date',
                            'type': 'template',
                            'title': 'SYSTEMFILE DateTime Date',
                            'format': 'yyyy-MM-dd',
                            'templateUrl': config.DATEPICKER_URL
                        },
                        {
                            'key': 'parentkey.subitem_systemfile_datetime[].subitem_systemfile_datetime_type',
                            'type': 'select',
                            'title': 'SYSTEMFILE DateTime Type',
                            'titleMap': get_select_value(date_type)
                        }
                    ],
                    'style': {
                        'add': 'btn-success'
                    },
                    'title': 'SYSTEMFILE DateTime'
                },
                {
                    'key': 'parentkey.subitem_systemfile_version',
                    'type': 'text',
                    'title': 'SYSTEMFILE Version'
                }
            ],
            'key': key.replace('[]', '')
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
