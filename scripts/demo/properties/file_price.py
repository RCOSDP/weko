# coding:utf-8
"""Definition of price files property."""
from .property_func import get_property_schema, get_property_form, set_post_data, get_select_value
from . import property_config as config

property_id = config.FILE_PRICE
multiple_flag = True
name_ja = '課金ファイル情報'
name_en = 'Price Files Information'


def add(post_data, key, **kwargs):
    """Add to a item type."""
    option = kwargs.pop('option')
    set_post_data(post_data, property_id, name_ja, key, option, form, schema, **kwargs)

    if kwargs.pop('mapping', True):
        post_data['table_row_map']['mapping'][key] = {
            'display_lang_type': '',
            'jpcoar_v1_mapping': {
                'file': {
                    'date': {
                        '@attributes': {
                            'dateType': 'date.dateType'
                        },
                        '@value': 'date.dateValue'
                    },
                    'extent': {
                        '@value': 'filesize.value'
                    },
                    'mimeType': {
                        '@value': 'format'
                    },
                    'URI': {
                        '@attributes': {
                            'label': 'url.label',
                            'objectType': 'url.objectType'
                        },
                        '@value': 'url.url'
                    },
                    'version': {
                        '@value': 'version'
                    }
                }
            },
            'jpcoar_mapping': {
                'file': {
                    'date': {
                        '@attributes': {
                            'dateType': 'date.dateType'
                        },
                        '@value': 'date.dateValue'
                    },
                    'extent': {
                        '@value': 'filesize.value'
                    },
                    'mimeType': {
                        '@value': 'format'
                    },
                    'URI': {
                        '@attributes': {
                            'label': 'url.label',
                            'objectType': 'url.objectType'
                        },
                        '@value': 'url.url'
                    },
                    'version': {
                        '@value': 'version'
                    }
                }
            },
            'junii2_mapping': '',
            'lido_mapping': '',
            'lom_mapping': '',
            'oai_dc_mapping': {
                'identifier': {
                    '@value': 'url.url'
                },
                'format': {
                    '@value': 'format'
                }
            },
            'spase_mapping': ''
        }
    else:
        post_data['table_row_map']['mapping'][key] = config.DEFAULT_MAPPING


def schema(title='', multi_flag=multiple_flag):
    """Get schema text of item type."""

    def _schema():
        """Schema text."""
        _d = {
            'billing_file_prop': True,
            'type': 'object',
            'properties': {
                'is_billing': {
                    'format': 'text',
                    'title': 'is_billing',
                    'type': 'string'
                },
                'url': {
                    'type': 'object',
                    'format': 'object',
                    'properties': {
                        'objectType': {
                            'type': ['null', 'string'],
                            'format': 'select',
                            'enum': config.FILE_TYPE_VAL,
                            'title': 'オブジェクトタイプ'
                        },
                        'label': {
                            'format': 'text',
                            'title': 'ラベル',
                            'type': 'string'
                        },
                        'url': {
                            'format': 'text',
                            'title': '本文URL',
                            'type': 'string'
                        }
                    },
                    'title': '本文URL'
                },
                'format': {
                    'format': 'text',
                    'title': 'フォーマット',
                    'type': 'string'
                },
                'filesize': {
                    'type': 'array',
                    'format': 'array',
                    'items': {
                        'type': 'object',
                        'format': 'object',
                        'properties': {
                            'value': {
                                'format': 'text',
                                'title': 'サイズ',
                                'type': 'string'
                            }
                        }
                    },
                    'title': 'サイズ'
                },
                'date': {
                    'type': 'array',
                    'format': 'array',
                    'items': {
                        'type': 'object',
                        'format': 'object',
                        'properties': {
                            'dateType': {
                                'type': ['null', 'string'],
                                'format': 'select',
                                'enum': config.DATE_TYPE_VAL,
                                'title': '日付タイプ'
                            },
                            'dateValue': {
                                'format': 'datetime',
                                'title': '日付',
                                'type': 'string'
                            }
                        }
                    },
                    'title': '日付'
                },
                'version': {
                    'format': 'text',
                    'title': 'バージョン情報',
                    'type': 'string'
                },
                'accessrole': {
                    'type': ['null', 'string'],
                    'format': 'radios',
                    'enum': [
                        None,
                        'open_access',
                        'open_date',
                        'open_login',
                        'open_no'
                    ],
                    'title': 'アクセス'
                },
                'displaytype': {
                    'type': ['null', 'string'],
                    'format': 'select',
                    'enum': [
                        None,
                        'detail',
                        'simple',
                        'preview'
                    ],
                    'title': '表示形式'
                },
                'filename': {
                    'type': ['null', 'string'],
                    'format': 'select',
                    'enum': [],
                    'title': 'ファイル名'
                },
                'licensefree': {
                    'format': 'textarea',
                    'title': '自由ライセンス',
                    'type': 'string'
                },
                'licensetype': {
                    'type': ['null', 'string'],
                    'format': 'select',
                    'enum': [],
                    'title': 'ライセンス'
                },
                'groupsprice': {
                    'format': 'array',
                    'items': {
                        'format': 'object',
                        'properties': {
                            'group': {
                                'enum': [],
                                'format': 'select',
                                'title': 'グループ',
                                'type': ['null', 'string']
                            },
                            'price': {
                                'format': 'text',
                                'pattern': '^[0-9]*$',
                                'title': '価格',
                                'type': 'string'
                            }
                        },
                        'type': 'object'
                    },
                    'title': 'グループ・価格',
                    'type': 'array'
                }
            }
        }
        return _d

    return get_property_schema(title, _schema, multi_flag)


def form(key='', title='', title_ja=name_ja, title_en=name_en, multi_flag=multiple_flag):
    """Get form text of item type."""

    def _condition(key, item_name):
        """set condition text"""
        if multi_flag:
            temp_key = '{}[arrayIndex]'.format(key.replace('[]', ''))
        else:
            temp_key = key.replace('[]', '')
        condition = ""
        if item_name == 'accessdate':
            condition = "model.{}.accessrole == 'open_date'".format(temp_key)
        elif item_name == 'groupsprice':
            condition = "model.{}.accessrole == 'open_login'".format(temp_key)
        elif item_name == 'licensefree':
            condition = "model.{}.licensetype == 'license_free'".format(
                temp_key)
        return condition

    def _form(key):
        """Form text."""
        _d = {
            'items': [
                {
                    'key': '{}.filename'.format(key),
                    'onChange': 'fileNameSelect(modelValue)',
                    'title': 'ファイル名',
                    'title_i18n': {
                        'en': 'FileName',
                        'ja': 'ファイル名'
                    },
                    'titleMap': [],
                    'type': 'select'
                },
                {
                    "key": "{}.url".format(key),
                    "title": "本文URL",
                    "title_i18n": {
                        "en": "Text URL",
                        "ja": "本文URL"
                    },
                    "type": "fieldset",
                    "items": [
                        {
                            'key': '{}.url.label'.format(key),
                            'title': 'ラベル',
                            'title_i18n': {
                                'en': 'Label',
                                'ja': 'ラベル'
                            },
                            'type': 'text'
                        },
                        {
                            'key': '{}.url.objectType'.format(key),
                            'type': 'select',
                            'title': 'オブジェクトタイプ',
                            'title_i18n': {
                                'en': 'Object Type',
                                'ja': 'オブジェクトタイプ'
                            },
                            'titleMap': get_select_value(config.FILE_TYPE_VAL)
                        }
                    ]
                },
                {
                    'key': '{}.version'.format(key),
                    'title': 'バージョン情報',
                    'title_i18n': {
                        'en': 'Version',
                        'ja': 'バージョン情報'
                    },
                    'type': 'text'
                },
                {
                    'key': '{}.displaytype'.format(key),
                    'type': 'select',
                    'title': '表示形式',
                    'titleMap': [
                        {
                            'name': '詳細表示',
                            'value': 'detail',
                            'name_i18n': {
                                'en': 'Detail',
                                'ja': '詳細表示'
                            }
                        },
                        {
                            'name': '簡易表示',
                            'value': 'simple',
                            'name_i18n': {
                                'en': 'Simple',
                                'ja': '簡易表示'
                            }
                        },
                        {
                            'name': 'プレビュー',
                            'value': 'preview',
                            'name_i18n': {
                                'en': 'Preview',
                                'ja': 'プレビュー'
                            }
                        }
                    ],
                    'title_i18n': {
                        'en': 'Preview',
                        'ja': '表示形式'
                    }
                },
                {
                    'key': '{}.licensetype'.format(key),
                    'title': 'ライセンス',
                    'title_i18n': {
                        'en': 'License',
                        'ja': 'ライセンス'
                    },
                    'titleMap': [],
                    'type': 'select'
                },
                {
                    'condition': _condition(key, 'licensefree'),
                    'key': '{}.licensefree'.format(key),
                    'notitle': True,
                    'type': 'textarea'
                },
                {
                    'key': '{}.accessrole'.format(key),
                    'type': 'radios',
                    'title': 'アクセス',
                    'title_i18n': {
                        'en': 'Access',
                        'ja': 'アクセス'
                    },
                    'titleMap': [
                        {
                            'name': 'オープンアクセス',
                            'value': 'open_access',
                            'name_i18n': {
                                'en': 'Open Access',
                                'ja': 'オープンアクセス'
                            }
                        },
                        {
                            'name': 'オープンアクセス日を指定する',
                            'value': 'open_date',
                            'name_i18n': {
                                'en': 'Input Open Access Date',
                                'ja': 'オープンアクセス日を指定する'
                            }
                        },
                        {
                            'name': 'ログインユーザのみ',
                            'value': 'open_login',
                            'name_i18n': {
                                'en': 'Registered User Only',
                                'ja': 'ログインユーザのみ'
                            }
                        },
                        {
                            'name': '開しない',
                            'value': 'open_no',
                            'name_i18n': {
                                'en': 'Do not Publish',
                                'ja': '公開しない'
                            }
                        }
                    ]
                },
                {
                    'condition': _condition(key, 'accessdate'),
                    'format': 'yyyy-MM-dd',
                    'key': '{}.date[0].dateValue'.format(key),
                    'templateUrl': config.DATEPICKER_URL,
                    'title': '公開日',
                    'title_i18n': {
                        'en': 'Opendate',
                        'ja': '公開日'
                    },
                    'type': 'template'
                },
                {
                    'add': 'New',
                    'condition': _condition(key, 'groupsprice'),
                    'items': [
                        {
                            'key': '{}.groupsprice[].group'.format(key),
                            'title': 'グループ',
                            'title_i18n': {
                                'en': 'Group',
                                'ja': 'グループ'
                            },
                            'titleMap': [],
                            'type': 'select'
                        },
                        {
                            'key': '{}.groupsprice[].price'.format(key),
                            'title': '価格',
                            'title_i18n': {
                                'en': 'Price',
                                'ja': '価格'
                            },
                            'type': 'string',
                            'validationMessage': '半角数字を入力してください。',
                            'validationMessage_i18n': {
                                'en': 'Please enter half-width numbers.',
                                'ja': '半角数字を入力してください。'
                            }
                        }
                    ],
                    'key': '{}.groupsprice'.format(key),
                    'style': {
                        'add': 'btn-success'
                    },
                    'title': 'Group/Price',
                    'title_i18n': {
                        'en': 'Group/Price',
                        'ja': 'グループ・価格'
                    }
                }
            ],
            'key': key.replace('[]', '')
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
