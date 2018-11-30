# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""WEKO Search Serializer."""

import copy

def get_mapping(item_type_mapping, mapping_type):
    """
    Format itemtype mapping data. [Key:Schema, Value:ItemId]
    :param item_type_mapping:
    :param mapping_type:
    :return:
    """

    def get_schema_key_info(schema, parent_key, schema_json={}):

        for k, v in schema.items():
            key = parent_key + '.' + k if parent_key else k
            if isinstance(v, dict):
                child_key = copy.deepcopy(key)
                get_schema_key_info(v, child_key, schema_json)
            else:
                schema_json[key] = v

        return schema_json

    schema = {}
    for item_id, maps in item_type_mapping.items():
        if isinstance(maps[mapping_type], dict):
            item_schema = get_schema_key_info(maps[mapping_type], '', {})
            for k, v in item_schema.items():
                item_schema[k] = item_id + '.' + v if v else item_id
            schema.update(item_schema)

    return schema

def get_metadata_from_map(item_data, item_id):
    """
    Get item metadata from search result.
    :param item_data:
    :param item_id:
    :return:
    """

    def get_sub_item_data(props, parent_key=''):
        key = parent_key if parent_key else ''
        value = {}

        if isinstance(props, list):
            for prop in props:
                for k, v in prop.items():
                    if isinstance(v, list) or isinstance(v, dict):
                        value.update(get_sub_item_data(v, key))
                    else:
                        sub_key = key + '.' + k if key else k
                        if sub_key in value:
                            if isinstance(value[sub_key], list):
                                value[sub_key].append(v)
                            else:
                                _value = value[sub_key]
                                value[sub_key] = [_value, v]
                        else:
                            value[sub_key] = v
        else:
            for k, v in props.items():
                if isinstance(v, list) or isinstance(v, dict):
                    value.update(get_sub_item_data(v, key))
                else:
                    sub_key = key + '.' + k if key else k
                    if sub_key in value:
                        if isinstance(value[sub_key], list):
                            value[sub_key].append(v)
                        else:
                            _value = value[sub_key]
                            value[sub_key] = [_value, v]
                    else:
                        value[sub_key] = v
        return value

    item_value = {}
    if 'attribute_value' in item_data:
        item_value[item_id] = item_data['attribute_value']
    elif 'attribute_value_mlt' in item_data:
        item_value.update(get_sub_item_data(item_data['attribute_value_mlt'],
                                            item_id))

    return item_value
