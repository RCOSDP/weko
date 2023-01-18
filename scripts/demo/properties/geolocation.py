# coding:utf-8
"""Definition of geoLocation property."""
from .property_func import get_property_schema, get_property_form, set_post_data
from . import property_config as config

property_id = config.GEOLOCATION
multiple_flag = True
name_ja = '位置情報'
name_en = 'Geo Location'


def add(post_data, key, **kwargs):
    """Add to a item type."""
    option = kwargs.pop('option')
    set_post_data(post_data, property_id, name_ja, key, option, form, schema, **kwargs)

    if kwargs.pop('mapping', True):
        post_data['table_row_map']['mapping'][key] = {
            'display_lang_type': '',
            'jpcoar_v1_mapping': {
                'geoLocation': {
                    'geoLocationPoint': {
                        'pointLongitude': {
                            '@value': 'subitem_geolocation_point.subitem_point_longitude'
                        },
                        'pointLatitude': {
                            '@value': 'subitem_geolocation_point.subitem_point_latitude'
                        }
                    },
                    'geoLocationBox': {
                        'westBoundLongitude': {
                            '@value': 'subitem_geolocation_box.subitem_west_longitude'
                        },
                        'eastBoundLongitude': {
                            '@value': 'subitem_geolocation_box.subitem_east_longitude'
                        },
                        'southBoundLatitude': {
                            '@value': 'subitem_geolocation_box.subitem_south_latitude'
                        },
                        'northBoundLatitude': {
                            '@value': 'subitem_geolocation_box.subitem_north_latitude'
                        }
                    },
                    'geoLocationPlace': {
                        '@value': 'subitem_geolocation_place.subitem_geolocation_place_text'
                    }
                }
            },
            'jpcoar_mapping': {
                'geoLocation': {
                    'geoLocationPoint': {
                        'pointLongitude': {
                            '@value': 'subitem_geolocation_point.subitem_point_longitude'
                        },
                        'pointLatitude': {
                            '@value': 'subitem_geolocation_point.subitem_point_latitude'
                        }
                    },
                    'geoLocationBox': {
                        'westBoundLongitude': {
                            '@value': 'subitem_geolocation_box.subitem_west_longitude'
                        },
                        'eastBoundLongitude': {
                            '@value': 'subitem_geolocation_box.subitem_east_longitude'
                        },
                        'southBoundLatitude': {
                            '@value': 'subitem_geolocation_box.subitem_south_latitude'
                        },
                        'northBoundLatitude': {
                            '@value': 'subitem_geolocation_box.subitem_north_latitude'
                        }
                    },
                    'geoLocationPlace': {
                        '@value': 'subitem_geolocation_place.subitem_geolocation_place_text'
                    }
                }
            },
            'junii2_mapping': '',
            'lido_mapping': '',
            'lom_mapping': '',
            'oai_dc_mapping': {
                'coverage': {
                    '@value': 'subitem_geolocation_place.subitem_geolocation_place_text'
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
            'type': 'object',
            'properties': {
                'subitem_geolocation_point': {
                    'title': '位置情報（点）',
                    'type': 'object',
                    'format': 'object',
                    'properties': {
                        'subitem_point_longitude': {
                            'format': 'text',
                            'title': '経度',
                            'type': 'string'
                        },
                        'subitem_point_latitude': {
                            'format': 'text',
                            'title': '緯度',
                            'type': 'string'
                        }
                    }
                },
                'subitem_geolocation_box': {
                    'title': '位置情報（空間）',
                    'type': 'object',
                    'format': 'object',
                    'properties': {
                        'subitem_west_longitude': {
                            'format': 'text',
                            'title': '西部経度',
                            'type': 'string'
                        },
                        'subitem_east_longitude': {
                            'format': 'text',
                            'title': '東部経度',
                            'type': 'string'
                        },
                        'subitem_south_latitude': {
                            'format': 'text',
                            'title': '南部緯度',
                            'type': 'string'
                        },
                        'subitem_north_latitude': {
                            'format': 'text',
                            'title': '北部緯度',
                            'type': 'string'
                        }
                    }
                },
                'subitem_geolocation_place': {
                    'format': 'array',
                    'title': '位置情報（自由記述）',
                    'type': 'array',
                    'items': {
                        'format': 'object',
                        'type': 'object',
                        'properties': {
                            'subitem_geolocation_place_text': {
                                'format': 'text',
                                'title': '位置情報（自由記述）',
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
                    'items': [
                        {
                            'key': '{}.subitem_geolocation_point.subitem_point_longitude'.format(key),
                            'title': '経度',
                            'title_i18n': {
                                'en': 'Point Longitude',
                                'ja': '経度'
                            },
                            'type': 'text'
                        },
                        {
                            'key': '{}.subitem_geolocation_point.subitem_point_latitude'.format(key),
                            'title': '緯度',
                            'title_i18n': {
                                'en': 'Point Latitude',
                                'ja': '緯度'
                            },
                            'type': 'text'
                        }
                    ],
                    'key': '{}.subitem_geolocation_point'.format(key),
                    'type': 'fieldset',
                    'title': '位置情報（点）',
                    'title_i18n': {
                        'en': 'Geo Location Point',
                        'ja': '位置情報（点）'
                    }
                },
                {
                    'items': [
                        {
                            'key': '{}.subitem_geolocation_box.subitem_west_longitude'.format(key),
                            'title': '西部経度',
                            'title_i18n': {
                                'en': 'West Bound Longitude',
                                'ja': '西部経度'
                            },
                            'type': 'text'
                        },
                        {
                            'key': '{}.subitem_geolocation_box.subitem_east_longitude'.format(key),
                            'title': '東部経度',
                            'title_i18n': {
                                'en': 'East Bound Longitude',
                                'ja': '東部経度'
                            },
                            'type': 'text'
                        },
                        {
                            'key': '{}.subitem_geolocation_box.subitem_south_latitude'.format(key),
                            'title': '南部緯度',
                            'title_i18n': {
                                'en': 'South Bound Latitude',
                                'ja': '南部緯度'
                            },
                            'type': 'text'
                        },
                        {
                            'key': '{}.subitem_geolocation_box.subitem_north_latitude'.format(key),
                            'title': '北部緯度',
                            'title_i18n': {
                                'en': 'North Bound Latitude',
                                'ja': '北部緯度'
                            },
                            'type': 'text'
                        }
                    ],
                    'key': '{}.subitem_geolocation_box'.format(key),
                    'type': 'fieldset',
                    'title': '位置情報（空間）',
                    'title_i18n': {
                        'en': 'Geo Location Box',
                        'ja': '位置情報（空間）'
                    }
                },
                {
                    'add': 'New',
                    'items': [
                        {
                            'key': '{}.subitem_geolocation_place[].subitem_geolocation_place_text'.format(key),
                            'title': '位置情報（自由記述）',
                            'title_i18n': {
                                'en': 'Geo Location Place',
                                'ja': '位置情報（自由記述）'
                            },
                            'type': 'text'
                        }
                    ],
                    'key': '{}.subitem_geolocation_place'.format(key),
                    'style': {
                        'add': 'btn-success'
                    },
                    'title': '位置情報（自由記述）',
                    'title_i18n': {
                        'en': 'Geo Location Place',
                        'ja': '位置情報（自由記述）'
                    }
                }
            ],
            'key': key.replace('[]', '')
        }
        return _d

    return get_property_form(key, title, title_ja, title_en, multi_flag, _form)
