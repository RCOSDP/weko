# coding:utf-8
"""Definition of conference property."""
from .property_func import get_property_schema, get_property_form, set_post_data, get_select_value
from . import property_config as config

property_id = config.CONFERENCE
multiple_flag = True
name_ja = '会議記述'
name_en = 'Conference'


def add(post_data, key, **kwargs):
    """Add to a item type."""
    option = kwargs.pop('option')
    set_post_data(post_data, property_id, name_ja, key, option, form, schema, **kwargs)

    if kwargs.pop('mapping', True):
        post_data['table_row_map']['mapping'][key] = {
            'display_lang_type': '',
            'jpcoar_v1_mapping': {
                'conference': {
                    'conferenceName': {
                        '@attributes': {
                            'xml:lang': 'subitem_conference_names.subitem_conference_name_language'
                        },
                        '@value': 'subitem_conference_names.subitem_conference_name'
                    },
                    'conferenceSequence': {
                        '@value': 'subitem_conference_sequence'
                    },
                    'conferenceSponsor': {
                        '@attributes': {
                            'xml:lang': 'subitem_conference_sponsors.subitem_conference_sponsor_language'
                        },
                        '@value': 'subitem_conference_sponsors.subitem_conference_sponsor'
                    },
                    'conferenceDate': {
                        '@attributes': {
                            'xml:lang': 'subitem_conference_date.subitem_conference_date_language',
                            'startDay': 'subitem_conference_date.subitem_conference_start_day',
                            'startMonth': 'subitem_conference_date.subitem_conference_start_month',
                            'startYear': 'subitem_conference_date.subitem_conference_start_year',
                            'endDay': 'subitem_conference_date.subitem_conference_end_day',
                            'endMonth': 'subitem_conference_date.subitem_conference_end_month',
                            'endYear': 'subitem_conference_date.subitem_conference_end_year'
                        },
                        '@value': 'subitem_conference_date.subitem_conference_period'
                    },
                    'conferenceVenue': {
                        '@attributes': {
                            'xml:lang': 'subitem_conference_venues.subitem_conference_venue_language'
                        },
                        '@value': 'subitem_conference_venues.subitem_conference_venue'
                    },
                    'conferencePlace': {
                        '@attributes': {
                            'xml:lang': 'subitem_conference_places.subitem_conference_place_language'
                        },
                        '@value': 'subitem_conference_places.subitem_conference_place'
                    },
                    'conferenceCountry': {
                        '@value': 'subitem_conference_country'
                    }
                }
            },
            'jpcoar_mapping': {
                'conference': {
                    'conferenceName': {
                        '@attributes': {
                            'xml:lang': 'subitem_conference_names.subitem_conference_name_language'
                        },
                        '@value': 'subitem_conference_names.subitem_conference_name'
                    },
                    'conferenceSequence': {
                        '@value': 'subitem_conference_sequence'
                    },
                    'conferenceSponsor': {
                        '@attributes': {
                            'xml:lang': 'subitem_conference_sponsors.subitem_conference_sponsor_language'
                        },
                        '@value': 'subitem_conference_sponsors.subitem_conference_sponsor'
                    },
                    'conferenceDate': {
                        '@attributes': {
                            'xml:lang': 'subitem_conference_date.subitem_conference_date_language',
                            'startDay': 'subitem_conference_date.subitem_conference_start_day',
                            'startMonth': 'subitem_conference_date.subitem_conference_start_month',
                            'startYear': 'subitem_conference_date.subitem_conference_start_year',
                            'endDay': 'subitem_conference_date.subitem_conference_end_day',
                            'endMonth': 'subitem_conference_date.subitem_conference_end_month',
                            'endYear': 'subitem_conference_date.subitem_conference_end_year'
                        },
                        '@value': 'subitem_conference_date.subitem_conference_period'
                    },
                    'conferenceVenue': {
                        '@attributes': {
                            'xml:lang': 'subitem_conference_venues.subitem_conference_venue_language'
                        },
                        '@value': 'subitem_conference_venues.subitem_conference_venue'
                    },
                    'conferencePlace': {
                        '@attributes': {
                            'xml:lang': 'subitem_conference_places.subitem_conference_place_language'
                        },
                        '@value': 'subitem_conference_places.subitem_conference_place'
                    },
                    'conferenceCountry': {
                        '@value': 'subitem_conference_country'
                    }
                }
            },
            'junii2_mapping': '',
            'lido_mapping': '',
            'lom_mapping': '',
            'oai_dc_mapping': '',
            'spase_mapping': ''
        }
    else:
        post_data['table_row_map']['mapping'][key] = config.DEFAULT_MAPPING


def schema(title='', multi_flag=multiple_flag):
    """Get schema text of item type."""
    def _schema():
        """Schema text."""
        _d = {
            'type': 'object',
            'properties': {
                'subitem_conference_names': {
                    'type': 'array',
                    'format': 'array',
                    'items': {
                        'type': 'object',
                        'format': 'object',
                        'properties': {
                            'subitem_conference_name_language': {
                                'type': ['null', 'string'],
                                'format': 'select',
                                'enum': config.LANGUAGE_VAL2_1,
                                'title': '言語'
                            },
                            'subitem_conference_name': {
                                'format': 'text',
                                'title': '会議名',
                                'type': 'string'
                            }
                        }
                    },
                    'title': '会議名'
                },
                'subitem_conference_sequence': {
                    'format': 'text',
                    'title': '回次',
                    'type': 'string'
                },
                'subitem_conference_sponsors': {
                    'type': 'array',
                    'format': 'array',
                    'items': {
                        'type': 'object',
                        'format': 'object',
                        'properties': {
                            'subitem_conference_sponsor_language': {
                                'type': ['null', 'string'],
                                'format': 'select',
                                'enum': config.LANGUAGE_VAL2_1,
                                'title': '言語'
                            },
                            'subitem_conference_sponsor': {
                                'format': 'text',
                                'title': '主催機関',
                                'type': 'string'
                            }
                        }
                    },
                    'title': '主催機関'
                },
                'subitem_conference_date': {
                    'type': 'object',
                    'format': 'object',
                    'properties': {
                        'subitem_conference_start_year': {
                            'format': 'text',
                            'title': '開始年',
                            'type': 'string'
                        },
                        'subitem_conference_start_month': {
                            'format': 'text',
                            'title': '開始月',
                            'type': 'string'
                        },
                        'subitem_conference_start_day': {
                            'format': 'text',
                            'title': '開始日',
                            'type': 'string'
                        },
                        'subitem_conference_end_year': {
                            'format': 'text',
                            'title': '終了年',
                            'type': 'string'
                        },
                        'subitem_conference_end_month': {
                            'format': 'text',
                            'title': '終了月',
                            'type': 'string'
                        },
                        'subitem_conference_end_day': {
                            'format': 'text',
                            'title': '終了日',
                            'type': 'string'
                        },
                        'subitem_conference_period': {
                            'format': 'text',
                            'title': '開催期間',
                            'type': 'string'
                        },
                        'subitem_conference_date_language': {
                            'type': ['null', 'string'],
                            'format': 'select',
                            'enum': config.LANGUAGE_VAL2_1,
                            'title': '言語'
                        }
                    },
                    'title': '開催期間'
                },
                'subitem_conference_venues': {
                    'type': 'array',
                    'format': 'array',
                    'items': {
                        'type': 'object',
                        'format': 'object',
                        'properties': {
                            'subitem_conference_venue_language': {
                                'type': ['null', 'string'],
                                'format': 'select',
                                'enum': config.LANGUAGE_VAL2_1,
                                'title': '言語'
                            },
                            'subitem_conference_venue': {
                                'format': 'text',
                                'title': '開催会場',
                                'type': 'string'
                            }
                        }
                    },
                    'title': '開催会場'
                },
                'subitem_conference_places': {
                    'type': 'array',
                    'format': 'array',
                    'items': {
                        'type': 'object',
                        'format': 'object',
                        'properties': {
                            'subitem_conference_place_language': {
                                'type': ['null', 'string'],
                                'format': 'select',
                                'enum': config.LANGUAGE_VAL2_1,
                                'title': '言語'
                            },
                            'subitem_conference_place': {
                                'format': 'text',
                                'title': '開催地',
                                'type': 'string'
                            }
                        }
                    },
                    'title': '開催地'
                },
                'subitem_conference_country': {
                    'type': ['null', 'string'],
                    'format': 'select',
                    'enum': config.COUNTRY_VAL,
                    'title': '開催国'
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
                    'items': [
                        {
                            'key': '{}.subitem_conference_names[].subitem_conference_name'.format(key),
                            'title': '会議名',
                            'title_i18n': {
                                'en': 'Conference Name',
                                'ja': '会議名'
                            },
                            'type': 'text'
                        },
                        {
                            'key': '{}.subitem_conference_names[].subitem_conference_name_language'.format(key),
                            'title': '言語',
                            'title_i18n': {
                                'en': 'Language',
                                'ja': '言語'
                            },
                            'titleMap': get_select_value(config.LANGUAGE_VAL2_1),
                            'type': 'select'
                        }
                    ],
                    'key': '{}.subitem_conference_names'.format(key),
                    'style': {
                        'add': 'btn-success'
                    },
                    'title': '会議名',
                    'title_i18n': {
                        'en': 'Conference Name',
                        'ja': '会議名'
                    }
                },
                {
                    'key': '{}.subitem_conference_sequence'.format(key),
                    'title': '回次',
                    'title_i18n': {
                        'en': 'Conference Sequence',
                        'ja': '回次'
                    },
                    'type': 'text'
                },
                {
                    'add': 'New',
                    'items': [
                        {
                            'key': '{}.subitem_conference_sponsors[].subitem_conference_sponsor'.format(key),
                            'title': '主催機関',
                            'title_i18n': {
                                'en': 'Conference Sponsor',
                                'ja': '主催機関'
                            },
                            'type': 'text'
                        },
                        {
                            'key': '{}.subitem_conference_sponsors[].subitem_conference_sponsor_language'.format(key),
                            'title': '言語',
                            'title_i18n': {
                                'en': 'Language',
                                'ja': '言語'
                            },
                            'titleMap': get_select_value(config.LANGUAGE_VAL2_1),
                            'type': 'select'
                        }
                    ],
                    'key': '{}.subitem_conference_sponsors'.format(key),
                    'style': {
                        'add': 'btn-success'
                    },
                    'title': '主催機関',
                    'title_i18n': {
                        'en': 'Conference Sponsor',
                        'ja': '主催機関'
                    }
                },
                {
                    'items': [
                        {
                            'key': '{}.subitem_conference_date.subitem_conference_start_year'.format(key),
                            'title': '開始年',
                            'title_i18n': {
                                'en': 'Start Year',
                                'ja': '開始年'
                            },
                            'type': 'text'
                        },
                        {
                            'key': '{}.subitem_conference_date.subitem_conference_start_month'.format(key),
                            'title': '開始月',
                            'title_i18n': {
                                'en': 'Start Month',
                                'ja': '開始月'
                            },
                            'type': 'text'
                        },
                        {
                            'key': '{}.subitem_conference_date.subitem_conference_start_day'.format(key),
                            'title': '開始日',
                            'title_i18n': {
                                'en': 'Start Day',
                                'ja': '開始日'
                            },
                            'type': 'text'
                        },
                        {
                            'key': '{}.subitem_conference_date.subitem_conference_end_year'.format(key),
                            'title': '終了年',
                            'title_i18n': {
                                'en': 'End Year',
                                'ja': '終了年'
                            },
                            'type': 'text'
                        },
                        {
                            'key': '{}.subitem_conference_date.subitem_conference_end_month'.format(key),
                            'title': '終了月',
                            'title_i18n': {
                                'en': 'End Month',
                                'ja': '終了月'
                            },
                            'type': 'text'
                        },
                        {
                            'key': '{}.subitem_conference_date.subitem_conference_end_day'.format(key),
                            'title': '終了日',
                            'title_i18n': {
                                'en': 'End Day',
                                'ja': '終了日'
                            },
                            'type': 'text'
                        },
                        {
                            'key': '{}.subitem_conference_date.subitem_conference_period'.format(key),
                            'title': '開催期間',
                            'title_i18n': {
                                'en': 'Conference Date',
                                'ja': '開催期間'
                            },
                            'type': 'text'
                        },
                        {
                            'key': '{}.subitem_conference_date.subitem_conference_date_language'.format(key),
                            'title': '言語',
                            'title_i18n': {
                                'en': 'Language',
                                'ja': '言語'
                            },
                            'titleMap': get_select_value(config.LANGUAGE_VAL2_1),
                            'type': 'select'
                        }
                    ],
                    'key': '{}.subitem_conference_date'.format(key),
                    'type': 'fieldset',
                    'title': '開催期間',
                    'title_i18n': {
                        'en': 'Conference Date',
                        'ja': '開催期間'
                    }
                },
                {
                    'add': 'New',
                    'items': [
                        {
                            'key': '{}.subitem_conference_venues[].subitem_conference_venue'.format(key),
                            'title': '開催会場',
                            'title_i18n': {
                                'en': 'Conference Venue',
                                'ja': '開催会場'
                            },
                            'type': 'text'
                        },
                        {
                            'key': '{}.subitem_conference_venues[].subitem_conference_venue_language'.format(key),
                            'title': '言語',
                            'title_i18n': {
                                'en': 'Language',
                                'ja': '言語'
                            },
                            'titleMap': get_select_value(config.LANGUAGE_VAL2_1),
                            'type': 'select'
                        }
                    ],
                    'key': '{}.subitem_conference_venues'.format(key),
                    'style': {
                        'add': 'btn-success'
                    },
                    'title': '開催会場',
                    'title_i18n': {
                        'en': 'Conference Venue',
                        'ja': '開催会場'
                    }
                },
                {
                    'add': 'New',
                    'items': [
                        {
                            'key': '{}.subitem_conference_places[].subitem_conference_place'.format(key),
                            'title': '開催地',
                            'title_i18n': {
                                'en': 'Conference Place',
                                'ja': '開催地'
                            },
                            'type': 'text'
                        },
                        {
                            'key': '{}.subitem_conference_places[].subitem_conference_place_language'.format(key),
                            'title': '言語',
                            'title_i18n': {
                                'en': 'Language',
                                'ja': '言語'
                            },
                            'titleMap': get_select_value(config.LANGUAGE_VAL2_1),
                            'type': 'select'
                        }
                    ],
                    'key': '{}.subitem_conference_places'.format(key),
                    'style': {
                        'add': 'btn-success'
                    },
                    'title': '開催地',
                    'title_i18n': {
                        'en': 'Conference Place',
                        'ja': '開催地'
                    }
                },
                {
                    'key': '{}.subitem_conference_country'.format(key),
                    'title': '開催国',
                    'title_i18n': {
                        'en': 'Conference Country',
                        'ja': '開催国'
                    },
                    'titleMap': get_select_value(config.COUNTRY_VAL),
                    'type': 'select'
                }
            ],
            'key': key.replace('[]', '')
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
