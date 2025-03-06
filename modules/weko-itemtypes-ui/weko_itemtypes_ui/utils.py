# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 National Institute of Informatics.
#
# Permission is hereby granted, free of charge, to any person obtaining a 
# copy of this software and associated documentation files (the 
# "Software"), to deal in the Software without restriction, including 
# without limitation the rights to use, copy, modify, merge, publish, 
# distribute, sublicense, and/or sell copies of the Software, and to 
# permit persons to whom the Software is furnished to do so, subject to 
# the following conditions:
#
# The above copyright notice and this permission notice shall be 
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, 
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE 
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION 
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION 
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""Utils for weko-itemtypes-ui."""
import copy
import json
import pickle
from copy import deepcopy

from flask import current_app
from flask_login import current_user
from weko_itemtypes_ui.config import DISABLE_DUPLICATION_CHECK
from invenio_db import db
from weko_records.api import ItemTypes,ItemTypeProps,ItemTypeNames
from sqlalchemy.orm.attributes import flag_modified

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


def fix_json_schema(json_schema: dict):
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
                error_msg='Cannot parse maxItems: '+str(e)
                current_app.logger.error(error_msg)
                return None
        if 'minItems' in properties[item].keys():
            min_item = item_data.get('minItems')
            if not min_item:
                continue
            try:
                item_data['minItems'] = int(min_item)
            except Exception as e:
                error_msg='Cannot parse minItems: '+str(e)
                current_app.logger.error(error_msg)
                return None
    json_schema['properties'] = properties
    return json_schema


def parse_required_item_in_schema(json_schema: dict):
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


def helper_remove_empty_enum(data: dict):
    """Help to remove enum key if it is empty.

    Arguments:
        data {dict} -- schema to remove enum key

    """
    if isinstance(data,list):
        print(data)
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
        if len(list_required_item) > 0:
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


def get_detail_node(lst_data, idx, meta_list):
    """Get detail info of node.

    @param lst_data:
    @param idx:
    @return:
    """
    item_key = next(iter(lst_data[idx]))
    item_val = lst_data[idx].get(item_key)
    lst_values = sorted([i for i in item_val])
    input_type = meta_list.get(item_key, {}).get('input_type')
    return item_key, item_val, lst_values, input_type


def get_all_mapping(item_value, mapping_type):
    """Get all mapping of each item.

    @param item_value:
    @return:
    """
    lst_result = []
    if item_value and isinstance(item_value, dict):
        for sub_key, sub_val in item_value.items():
            if sub_key == mapping_type and isinstance(sub_val, dict):
                for i in get_lst_mapping(sub_val, [sub_key]):
                    lst_result.append(i)
    return lst_result


def check_duplicate_mapping(
        data_mapping, meta_system, item_type, mapping_type):
    """Check_duplicate mapping.

    @param data_mapping:
    @param meta_system:
    @param item_type:
    @return:
    """
    
    if current_app.config.get('DISABLE_DUPLICATION_CHECK',DISABLE_DUPLICATION_CHECK):
        return []
    
    def process_overlap():
        """Process partial overlap if any."""
        for overlap_val in lst_overlap:
            lst_all_src = [i for i in item_src_val]
            lst_all_des = [i for i in item_des_val]
            if lst_all_src != lst_all_des \
                    and not [item_src_name, item_des_name] in lst_duplicate:
                lst_duplicate.append([item_src_name, item_des_name])

    lst_temporary = {}
    meta_list = item_type.render.get('meta_list')
    table_row = item_type.render.get('table_row')
    properties = item_type.schema.get('properties')
    table_row += [
        'pubdate',
        'system_file',
        'system_identifier_doi',
        'system_identifier_hdl',
        'system_identifier_uri'
    ]

    for item_key, item_value in deepcopy(data_mapping).items():
        if item_key in table_row:
            lst_temporary[item_key] = get_all_mapping(item_value, mapping_type)
        else:
            data_mapping.pop(item_key)
    lst_mapping_detail = []
    for k, v in lst_temporary.items():
        lst_mapping_detail.append({k: v})
    lst_duplicate = []
    for i in range(len(lst_mapping_detail)):
        item_src_key, item_src_val, lst_values_src, input_type_src = \
            get_detail_node(lst_mapping_detail, i, meta_list)
        for j in range(i + 1, len(lst_mapping_detail)):
            item_des_key, item_des_val, lst_values_des, input_type_des = \
                get_detail_node(lst_mapping_detail, j, meta_list)
            if item_des_key == 'system_file' \
                    or item_src_key == 'system_file' \
                    or input_type_src != input_type_des:
                continue
            item_des_in_sys = item_des_key in meta_system
            item_src_in_sys = item_src_key in meta_system
            
            lst_overlap = list(
                set(lst_values_src).intersection(lst_values_des))
            if lst_overlap:
                if item_src_key in properties:
                    item_src_name = properties.get(
                        item_src_key).get('title')
                else:
                    continue
                if item_des_key in properties:
                    item_des_name = properties.get(
                        item_des_key).get('title')
                else:
                    continue

                if (item_des_in_sys and item_src_in_sys) \
                        or [item_src_name, item_des_name] in lst_duplicate:
                    continue
                elif (item_des_in_sys or item_src_in_sys) and lst_overlap:
                    lst_duplicate.append([item_src_name, item_des_name])
                else:
                    process_overlap()

    return lst_duplicate

def update_required_schema_not_exist_in_form(schema, forms):
    """Update required in schema.

    if item exist in schema but not exist in form,
    delete required in schema.

    @param schema:
    @param forms:
    @return schema:
    """
    def get_form_by_key(key, forms):
        """Get form base on key of schema."""
        for form in forms:
            if key == form.get('key'):
                return form
        return {'items': []}

    schema_properties = schema.get('properties')
    for k, v in schema_properties.items():
        required_list = v.get('items').get(
            'required') if 'items' in v.keys() else v.get('required')
        if not required_list:
            continue
        form = get_form_by_key(k, forms)
        items = form.get('items', [])
        excludes = []
        for required in required_list:
            flag = 0
            for item in items:
                key = item.get('key', '').split('.')[-1]
                if required == key:
                    break
                flag = flag + 1
            if flag == len(items):
                excludes.append(required)
        for exclude in excludes:
            required_list.remove(exclude)
        if len(required_list) == 0:
            if 'items' in v.keys():
                del v['items']['required']
            else:
                del v['required']
    return schema


def update_text_and_textarea(item_type_id, new_schema, new_form):
    """Update type and format of text and textarea when change.

    @param item_type_id:  edited id of item type.
    @param new_schema: new edited schema
    @param new_form: new edited form
    @return new_schema: new edited schema
    @return new_form: new edited form
    """
    def is_text(prop):
        """Check this property is text property.

        @param prop:  property.
        @return True/False: if this is text, return True else False.
        """
        items = prop.get('items', {}).get('properties', {}) \
            if is_multiple(prop) else prop.get('properties', {})
        if items.get('subitem_text_value') \
                and items.get('subitem_text_language'):
            return True
        return False

    def is_textarea(prop):
        """Check this property is textarea property.

        @param prop:  property.
        @return True/False: if this is textarea, return True else False.
        """
        items = prop.get('items', {}).get('properties', {}) \
            if is_multiple(prop) else prop.get('properties', {})
        if items.get('subitem_textarea_value') \
                and items.get('subitem_textarea_language'):
            return True
        return False

    def is_text_or_textarea(prop):
        """Check this property is text or textarea property.

        @param prop:  property.
        @return True/False: if this is text or textarea, return True else False.
        """
        return is_text(prop) or is_textarea(prop)

    def get_format_string(prop):
        """Get format of this property.

        @param prop:  property.
        @return 'text'/'textarea': if this is text,
                                    return 'text' else 'textarea'.
        """
        return 'text' if is_text(prop) else 'textarea'

    def is_multiple(prop):
        """Check this property is multiple property.

        @param prop:  property.
        @return True/False: if this is multiple, return True else False.
        """
        result = False
        if prop.get('maxItems') or prop.get('maxItems'):
            result = True
        return result

    from weko_records.api import ItemTypes
    new_properties = new_schema.get('properties')

    item_type = ItemTypes.get_by_id(item_type_id)
    old_schema = item_type.schema
    old_properties = old_schema.get('properties')
    for key, val in old_properties.items():
        new_val = new_properties.get(key, {})
        if is_text_or_textarea(val) and is_text_or_textarea(new_val):
            new_format = get_format_string(new_val)
            old_format = get_format_string(val)
            value_key = 'subitem_{}_value'.format(old_format)
            lang_key = 'subitem_{}_language'.format(old_format)
            is_multiple_prop = is_multiple(new_val)
            # Update format for "Text" or "Textarea" schema.
            items_map = new_val['items']['properties'] \
                if is_multiple_prop else new_val['properties']
            prop_temp = {}
            for item_key, item_val in items_map.items():
                if item_val.get('format') in ['text', 'textarea']:
                    prop_temp[value_key] = item_val
                    prop_temp[value_key]['format'] = new_format
                else:
                    prop_temp[lang_key] = item_val
            if is_multiple_prop:
                new_val['items']['properties'] = prop_temp
            else:
                new_val['properties'] = prop_temp
            # Update format for "Text" or "Textarea" form.
            for new_f in new_form:
                if new_f.get('key') == key:
                    for item in new_f['items']:
                        key_pattern = '{}[].{}' if is_multiple_prop else '{}.{}'
                        if item.get('type') in ['text', 'textarea']:
                            item['key'] = key_pattern.format(key, value_key)
                            item['type'] = new_format
                        else:
                            item['key'] = key_pattern.format(key, lang_key)
    return new_schema, new_form

