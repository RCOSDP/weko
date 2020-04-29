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
import copy
from copy import deepcopy

from flask import current_app
from flask_login import current_user


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
                current_app.logger.error('Cannot parse maxItems: ', str(e))
                return None
        if 'minItems' in properties[item].keys():
            min_item = item_data.get('minItems')
            if not min_item:
                continue
            try:
                item_data['minItems'] = int(min_item)
            except Exception as e:
                current_app.logger.error('Cannot parse minItems: ', str(e))
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
    helper_remove_empty_enum(json_schema)
    data = deepcopy(json_schema)
    required = deepcopy(data.get('required'))
    if not required:
        return json_schema
    if 'pubdate' in required:
        required.remove('pubdate')
    if len(required) == 0:
        return json_schema
    properties = data.get('properties')
    if not properties:
        return None
    for item in required:
        required_data = add_required_subitem(properties.get(item))
        if required_data:
            properties[item] = required_data
    return data


def helper_remove_empty_enum(data):
    """Help to remove enum key if it is empty.

    Arguments:
        data {dict} -- schema to remove enum key

    """
    if "enum" in data.keys():
        if not data.get("enum"):
            data.pop("enum", None)
    elif "properties" in data.keys():
        for k, v in data.get("properties").items():
            if v:
                helper_remove_empty_enum(v)
    elif "items" in data.keys():
        helper_remove_empty_enum(data.get("items"))


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
                if sub_data is None:
                    sub_data = v
                    list_required_item.append(str(k))
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


def has_system_admin_access():
    """Use to check if a user has System Administrator access."""
    is_sys_admin = False
    if current_user.is_authenticated:
        system_admin = current_app.config['WEKO_ADMIN_PERMISSION_ROLE_SYSTEM']
        for role in list(current_user.roles or []):
            if role.name == system_admin:
                is_sys_admin = True
                break
    return is_sys_admin


def get_lst_mapping(current_checking, parent_node=[]):
    """Get list detail mapping of current checking node.

    @param current_checking:
    @param parent_node:
    @return:
    """
    for key, val in current_checking.items():
        if isinstance(val, str):
            parent_node.append(key)
            return_val = '.'.join(parent_node)
            yield return_val
        else:
            parent_node_clone = copy.deepcopy(parent_node)
            parent_node_clone.append(key)
            for i in get_lst_mapping(val, parent_node_clone):
                yield i


def get_detail_node(lst_data, idx):
    """Get detail info of node.

    @param lst_data:
    @param idx:
    @return:
    """
    item_key = next(iter(lst_data[idx]))
    item_val = lst_data[idx].get(item_key)
    lst_values = [i for i in item_val if i.endswith('@value')]
    return item_key, item_val, lst_values


def get_all_mapping(item_value):
    """Get all mapping of each item.

    @param item_value:
    @return:
    """
    lst_result = []
    for sub_key, sub_val in item_value.items():
        if sub_key.endswith('_mapping') and isinstance(sub_val, dict):
            for i in get_lst_mapping(sub_val, [sub_key]):
                lst_result.append(i)
    return lst_result


def check_duplicate_mapping(data_mapping, meta_system, item_type):
    """Check_duplicate mapping.

    @param data_mapping:
    @param meta_system:
    @param item_type:
    @return:
    """
    def process_overlap():
        """Process partial overlap if any."""
        for overlap_val in lst_overlap:
            overlap_key = overlap_val.replace('.@value', '')
            lst_all_src = [i for i in item_src_val if
                           i.startswith(overlap_key)]
            lst_all_des = [i for i in item_des_val if
                           i.startswith(overlap_key)]
            if lst_all_src != lst_all_des:
                item_src_name = item_type.schema.get(
                    'properties').get(item_src_key).get('title')
                item_des_name = item_type.schema.get(
                    'properties').get(item_des_key).get('title')
                lst_duplicate.append([item_src_name, item_des_name])

    lst_temporary = {}
    for item_key, item_value in data_mapping.items():
        lst_temporary[item_key] = get_all_mapping(item_value)
    lst_mapping_detail = []
    for k, v in lst_temporary.items():
        lst_mapping_detail.append({k: v})
    lst_duplicate = []
    for i in range(len(lst_mapping_detail)):
        item_src_key, item_src_val, lst_values_src = get_detail_node(
            lst_mapping_detail, i)
        if item_src_key in meta_system:
            continue
        for j in range(i + 1, len(lst_mapping_detail)):
            item_des_key, item_des_val, lst_values_des = get_detail_node(
                lst_mapping_detail, j)
            if item_src_key in meta_system:
                continue
            lst_overlap = list(
                set(lst_values_src).intersection(lst_values_des))
            if lst_overlap:
                process_overlap()

    return lst_duplicate
