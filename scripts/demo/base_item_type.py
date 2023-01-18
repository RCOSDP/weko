# coding:utf-8
'''
Script with the base data for generating item type.
'''
from properties import AddProperty, property_config


def base_data():
    ''' Generates a base dictionary for generating item type '''
    post_data = {
        'upload_file': False,
        'table_row': [],
        'table_row_map': {
            'name': None,
            'action': 'new',
            'mapping': {
                'pubdate': {
                    'display_lang_type': '',
                    'jpcoar_mapping': '',
                    'junii2_mapping': '',
                    'lido_mapping': '',
                    'lom_mapping': '',
                    'oai_dc_mapping': '',
                    'spase_mapping': ''
                }
            },
            'form': [
                {
                    'key': 'pubdate',
                    'type': 'template',
                    'title': '公開日',
                    'title_i18n': {
                        'ja': '公開日',
                        'en': 'PubDate'
                    },
                    'required': True,
                    'format': 'yyyy-MM-dd',
                    'templateUrl': property_config.DATEPICKER_URL
                }
            ],
            'schema': {
                '$schema': 'http://json-schema.org/draft-04/schema#',
                'type': 'object',
                'description': '',
                'properties': {
                    'pubdate': {
                        'type': 'string',
                        'title': '公開日',
                        'format': 'datetime'
                    }
                },
                'required': ['pubdate']
            }
        },
        'meta_list': {},
        'meta_fix': {
            'pubdate': {
                'title': '公開日',
                'title_i18n': {
                    'ja': '公開日',
                    'en': 'PubDate'
                },
                'input_type': 'datetime',
                'input_value': '',
                'option': {
                    'required': True,
                    'multiple': False,
                    'hidden': False,
                    'showlist': False,
                    'crtf': False
                }
            }
        },
        'meta_system': {},
        'schemaeditor': {
            'schema': {}
        },
        'edit_notes': {}
    }
    AddProperty.S_file(
        post_data=post_data,
        key='system_file',
        title='File Information',
        title_ja='ファイル情報',
        title_en='File Information')
    AddProperty.S_identifier(
        post_data=post_data,
        key='system_identifier_doi',
        title='Persistent Identifier(DOI)',
        title_ja='永続識別子（DOI）',
        title_en='Persistent Identifier(DOI)')
    AddProperty.S_identifier(
        post_data=post_data,
        key='system_identifier_hdl',
        title='Persistent Identifier(HDL)',
        title_ja='永続識別子（HDL）',
        title_en='Persistent Identifier(HDL)')
    AddProperty.S_identifier(
        post_data=post_data,
        key='system_identifier_uri',
        title='Persistent Identifier(URI)',
        title_ja='永続識別子（URI）',
        title_en='Persistent Identifier(URI)')
    return post_data
