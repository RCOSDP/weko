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

"""Utils for weko-itemtypes-ui."""

from flask import current_app
from copy import deepcopy


def remove_xsd_prefix(jpcoar_lists):
    """Remove xsd prefix."""
    jpcoar_copy = {}

    def remove_prefix(jpcoar_src, jpcoar_dst):
        for key, value in jpcoar_src.items():
            if 'type' == key:
                jpcoar_dst[key] = value
                continue
            jpcoar_dst[key.split(':').pop()] = {}
            if isinstance(value, object):
                remove_prefix(value, jpcoar_dst[key.split(':').pop()])

    remove_prefix(jpcoar_lists, jpcoar_copy)
    return jpcoar_copy


def fix_json_schema(json_schema):
    """Fix format for json schema.

    Arguments:
        json_schema {dictionary} -- The json schema

    Returns:
        dictionary -- The json schema after fix format

    """
    return fix_min_max_multiple_item(
        parse_required_item_in_schema(
            json_schema))


def fix_min_max_multiple_item(json_schema):
    """Fix min max value for multiple type.

    Arguments:
        json_schema {dictionary} -- The json schema

    Returns:
        dictionary -- The json schema after fix format

    """
    properties = deepcopy(json_schema.get('properties'))
    for item in properties:
        item_data = properties[item]
        if 'maxItems' in properties[item].keys():
            max_item = item_data.get('maxItems')
            if not max_item:
                continue
            try:
                item_data['maxItems'] = int(max_item)
            except Exception as e:
                print('Cannot parse maxItems ' + e)
                return None
        if 'minItems' in properties[item].keys():
            min_item = item_data.get('minItems')
            if not min_item:
                continue
            try:
                item_data['minItems'] = int(min_item)
            except Exception as e:
                print('Cannot parse minItems ' + e)
                return None
    json_schema['properties'] = properties
    return json_schema


def parse_required_item_in_schema(json_schema):
    """Get required item and split to sub items.

    Arguments:
        json_schema {dictionary} -- The schema data

    Returns:
        dictionary -- The schema after parse

    """
    data = deepcopy(json_schema)
    required = deepcopy(data.get('required'))
    if 'pubdate' in required:
        required.remove('pubdate')
    if len(required) == 0:
        return None
    properties = data.get('properties')
    if not properties:
        return None
    for item in required:
        required_data = add_required_subitem(properties.get(item))
        if required_data:
            properties[item] = required_data
    return data


def add_required_subitem(data):
    """Get schema after add required.

    Arguments:
        data {dictionary} -- item in schema

    Returns:
        dictionary -- data after add required

    """
    if not data:
        return None
    item = deepcopy(data)
    has_item = False
    if 'items' in item.keys():
        has_item = True
        sub_item = item.get('items')
    else:
        sub_item = item

    properties = sub_item.get('properties')
    list_required_item = list()
    if not properties:
        return None
    if 'type' in sub_item.keys() and sub_item['type'] == 'object':
        for k, v in properties.items():
            if is_properties_exist_in_item(v):
                sub_data = add_required_subitem(v)
                properties[k] = sub_data
            else:
                list_required_item.append(str(k))
        sub_item['required'] = list_required_item
    else:
        for k, v in properties.items():
            if not add_required_subitem(v):
                return None
            else:
                sub_data = add_required_subitem(v)
                properties[k] = sub_data
    if has_item:
        item['items'] = sub_item
        return item
    else:
        return sub_item


def is_properties_exist_in_item(data):
    """Check item have children or not.

    Arguments:
        data {dictionary} -- Item data

    Returns:
        boolean -- True if child is exists

    """
    if data.get('properties') or data.get('items'):
        return True
    return False
