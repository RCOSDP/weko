# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-swordserver."""

from flask import current_app

from invenio_oaiharvester.harvester import JsonMapper

from .errors import WekoSwordserverException, ErrorType

from weko_search_ui.mapper import JsonLdMapper


class WekoSwordMapper(JsonMapper):
    """WekoSwordMapper."""
    def __init__(self, json, json_ld, itemtype, json_map):
        """Init."""
        self.json = json
        self.itemtype = itemtype
        self.itemtype_name = itemtype.item_type_name.name
        self.json_map = json_map
        self.all_properties, _ = JsonLdMapper._deconstruct_json_ld(json_ld)

    def map(self):
        """Maping JSON-LD;self.json Metadata into item_type format."""
        if self.is_deleted():
            return {}

        res = {
            "pubdate": str(self.datestamp()),
            "publish_status": self.json.get("record").get("header").get("publish_status"),
            "path": [self.json.get("record").get("header").get("indextree")]
        }

        item_map = self._create_item_map()
        metadata = self._create_metadata(item_map)

        files_info = []
        for v in item_map.values():
            if not v.endswith(".filename"):
                continue
            files_key = v.split(".")[0]
            files_info.append({
                "key": files_key,
                "items": metadata.get(files_key, [])
            })

        files_info = {"files_info": files_info}

        res = {**res, **files_info, **metadata}
        return res


    # TODO: Refactor mapping logic
    def _create_metadata(self, item_map):
        """Create metadata.

        Args:
            item_map (dict): item_map

        Returns:
            dict: mapped metadata
        """
        metadata = {}
        path_and_value = {}

        # Create metadata for each item in json_map
        for k, v in self.json_map.items():
            json_value = self._get_json_metadata_value(v)
            # if json_value is None:
            if not isinstance(json_value, bool) and (json_value is None or ((len(json_value )> 0) and all(val is None for val in json_value))):
                continue
            type_of_item_type_path = self._get_type_of_item_type_path(item_map[k])
            self._create_metadata_of_a_property(metadata, item_map[k], type_of_item_type_path, json_value)

            # Create path_and_value
            # Remove "d2Vrby0uLw==." from v if it is included
            if "d2Vrby0uLw==." in v:
                v = v.replace("d2Vrby0uLw==.", "")
            path_and_value[v] = json_value

        # Create Extra field
        extra_dict = self._get_extra_dict(path_and_value, self.all_properties)

        # Check if "Extra" prepared in itemtype schema form item_map
        if "Extra" in item_map:
            metadata[item_map.get("Extra")] = str(extra_dict)

        return metadata


    def _get_json_metadata_value(self, json_map_key):
        """Get json value.

        If the value got from self.json is in list, the result is list.
        If the value got from self.json is in multiple dimensions, the result
        is multi dimension list.

        Examples:

        1. If the value of json_map_key includes single [] like below, the
           result is one dimension list.

            "example_key_1": {
                "key_arr": [
                    {
                        "key_val": "value1"
                    },
                    {
                        "key_val": "value2"
                    }
                ],
            }

            _get_json_metadata_value("example_key_1") -> ["value1", "value2"]


        2. If the value of json_map_key includes double [] like below, the
           result is two dimension list.

            "example_key_2": {
                "key_arr1": [
                    {
                        "key_arr2": [
                            {
                                "key_val": "value1"
                            },
                            {
                                "key_val": "value2"
                            }
                        ]
                    },
                    {
                        "key_arr2": [
                            {
                                "key_val": "value3"
                            },
                            {
                                "key_val": "value4"
                            }
                        ]
                    }
                ]
            }

            _get_json_metadata_value("example_key_2")
                -> [["value1", "value2"], ["value3", "value4"]]


        Args:
            json_map_key (str): Path of ProcessedJson get from json_map

        Returns:
            any: Element of metadata
        """
        # define internal functions
        def _detect_dict(json_keys, dict_):
            """Get json value from dict.

            Args:
                json_keys (list): List of keys in dict
                dict_ (dict): Dict which contains metadata

            Returns:
                any: Element of metadata
            """
            json_key = json_keys[0]
            value = dict_.get(json_key)

            # No json_key in dict: {"other_key": value}
            if value is None:
                return None
            # dict in dict: {"json_key": {}}
            elif isinstance(value, dict):
                if len(json_keys) == 1:
                    return value
                return _detect_dict(json_keys[1:], value)
            # list in dict: {"json_key": []}
            elif isinstance(value, list):
                if len(json_keys) == 1:
                    return value
                return _detect_list(json_keys[1:], value)
            # value in dict: {"json_key": value}
            else:
                if len(json_keys) == 1:
                    return value
                else:
                    current_app.logger.error(
                        f"Invalid mapping definition: Value: {value} got from {json_key} but still need to get {json_keys[1:]}."
                    )
                    raise WekoSwordserverException(
                        f"Value: {value} got from {json_key} but still need to get {json_keys[1:]}. Check the mapping definition.",
                        errorType=ErrorType.ServerError
                    )

        def _detect_list(json_keys, list_):
            """Get json value from list.

            Args:
                json_keys (list): List of keys in list_of_dict
                list_ (list): List of dict which contains metadata

            Returns:
                any: Element of metadata
            """
            list_result = []
            for value in list_:
                # dict in list: [{}, {}, ...]
                if isinstance(value, dict):
                    result = _detect_dict(json_keys, value)
                    list_result.append(result)
                # list in list: [[], [], ...]
                elif isinstance(value, list):
                    current_app.logger.error(
                        "Invalid metadata file: List in list not supported."
                    )
                    raise WekoSwordserverException(
                        "List in list not supported. Check your metadata file.",
                        errorType=ErrorType.ContentMalformed
                    )
                # value in list: [value, value, ...]
                else:
                    current_app.logger.error(
                        f"Invalid mapping definition: Value: {value} got from list but still need to get {json_keys}."
                    )
                    raise WekoSwordserverException(
                        f"Value: {value} got from list but still need to get {json_keys}. Check the mapping definition.",
                        errorType=ErrorType.ServerError
                    )
            return list_result

        json_keys = json_map_key.split('.')
        json_key = json_keys[0]
        value = self.json['record']['metadata'].get(json_key)

        if value is None:
            return None
        # dict in dict: {"json_key": {}}
        elif isinstance(value, dict):
            if len(json_keys) == 1:
                current_app.logger.error("Invalid mapping definition: Value is dict but still need to get more keys.")
                raise WekoSwordserverException(
                    "Value is dict but still need to get more keys. Check the mapping definition.",
                    errorType=ErrorType.ServerError
                )
            return _detect_dict(json_keys[1:], value)
        # list in dict: {"json_key": []}
        elif isinstance(value, list):
            return _detect_list(json_keys[1:], value)
        # value in dict: {"json_key": value}
        else:
            if len(json_keys) == 1:
                return value
            else:
                current_app.logger.error(
                    f"Invalid mapping definition: Value: {value} got from {json_key} but still need to get {json_keys[1:]}."
                )
                raise WekoSwordserverException(
                    f"Value: {value} got from {json_key} but still need to get {json_keys[1:]}. Check the mapping definition.",
                    errorType=ErrorType.ServerError
                )


    def _get_type_of_item_type_path(self, item_map_key):
        """Get type of item type path.

        Args:
            item_map_key (str): Path of item type get from item_map

        Returns:
            list: Type of item type path
        """
        item_map_keys = item_map_key.split('.')
        type_of_item_type_path = []
        current_schema = self.itemtype.schema.get("properties")

        for item_map_key in item_map_keys:
            # If "type" is "object" in item_tyep_schema, next path is in "properties"
            if current_schema[item_map_key].get("type") == "object":
                type_of_item_type_path.append("object")
                current_schema = current_schema[item_map_key].get("properties")
            # If "type" is "array" in item_tyep_schema, next path is in "items" > "properties"
            elif current_schema[item_map_key].get("type") == "array":
                type_of_item_type_path.append("array")
                current_schema = current_schema[item_map_key].get("items").get("properties")
            # If "type" is other than "object" or "array" in item_tyep_schema, it is the end of the path
            else:
                type_of_item_type_path.append("value")

        # Check if the list ends with 'value' and contains 'value' only once
        if not (type_of_item_type_path[-1] == "value" and type_of_item_type_path.count("value") == 1):
            current_app.logger.error(
                "Failed in mapping process: type_of_item_type_path must contain exactly one 'value' element at the end."
            )
            raise WekoSwordserverException(
                "Some error occurred in the server. Can not create metadata.",
                errorType=ErrorType.ServerError
            )
        return type_of_item_type_path


    def _create_metadata_of_a_property(self, metadata, item_map_key, type_of_item_type_path, json_value):
        """Create metadata of a property.

        Args:
            metadata (dict): Metadata
            item_map_key (str): Path of item type get from item_map
            type_of_item_type_path (list): "type" of each key in ItemType, contains "value", "object", and "array"
            json_value (any): Value got from ProcessedJson
        """
        item_map_keys = item_map_key.split('.')
        dim_json_value = self._get_dimensions(json_value)
        num_array_type = type_of_item_type_path.count("array")

        # If dim_json_value is bigger than num_array_type, pick the first element of json_value until dim_json_value equals to num_array_type
        executed = False
        while dim_json_value > num_array_type:
            if not executed:
                # TODO: add warning
                executed = True
            json_value = json_value[0] if not json_value == [] else None
            dim_json_value = self._get_dimensions(json_value)

        # If item_map_keys length is 1, it means that the item_map_keys contains only last key
        if len(item_map_keys) == 1:
            # If json_value is list, use only first element
            if dim_json_value > 0:
                metadata[item_map_keys[0]] = json_value[0]
            # If json_value is not list, use json_value
            else:
                metadata[item_map_keys[0]] = json_value
        # If item_map_keys length is more than 1, it is necessary to create nested metadata
        else:
            _item_map_key = item_map_keys[0]
            _type = type_of_item_type_path[0]

            # If _type is "object", create nested metadata
            if _type == "object":
                if not metadata.get(_item_map_key):
                    metadata[_item_map_key] = {}
                metadata = metadata[_item_map_key]
                self._create_child_metadata_of_a_property(metadata, item_map_keys[1:], type_of_item_type_path[1:], json_value)
            # If _type is "array", do the following method
            else:
                if not metadata.get(_item_map_key):
                    metadata[_item_map_key] = [{} for _ in range(len(json_value) if isinstance(json_value, list) else 1)]
                elif isinstance(json_value, list) and len(metadata[_item_map_key]) < len(json_value):
                    metadata[_item_map_key].append({} for _ in range(len(json_value) - len(metadata[_item_map_key])))
                metadata = metadata[_item_map_key]

                # Create nested metadata for each element of json_value
                for i in range(len(metadata)):
                    if isinstance(json_value, list):
                        json_val = json_value[i]
                    else:
                        json_val = json_value
                    self._create_child_metadata_of_a_property(metadata[i], item_map_keys[1:], type_of_item_type_path[1:], json_val)
        return


    def _create_child_metadata_of_a_property(self, child_metadata, item_map_keys, type_of_item_type_path, json_value):
        """Create child metadata of a property.

        Args:
            child_metadata (dict): Child metadata
            item_map_keys (list): List of keys in ItemType
            type_of_item_type_path (list): "type" of each key in ItemType, contains "value", "object", and "array"
            json_value (any): Value got from ProcessedJson
        """
        # If item_map_keys length is 1, it means that the item_map_keys contains only last key
        if len(item_map_keys) == 1:
            # Only if json_value is not None, add json_value to metadata
            if json_value is not None:
                child_metadata[item_map_keys[0]] = json_value
        # If item_map_keys length is more than 1, it is necessary to create nested metadata
        else:
            _item_map_key = item_map_keys[0]
            _type = type_of_item_type_path[0]

            # If _type is "object", create nested metadata
            if _type == "object":
                if not child_metadata.get(_item_map_key):
                    child_metadata[_item_map_key] = {}
                child_metadata = child_metadata[_item_map_key]
                self._create_child_metadata_of_a_property(child_metadata, item_map_keys[1:], type_of_item_type_path[1:], json_value)
            # If _type is "array", do the following method
            else:
                if not child_metadata.get(_item_map_key):
                    child_metadata[_item_map_key] = [{} for _ in range(len(json_value) if isinstance(json_value, list) else 1)]
                elif isinstance(json_value, list) and len(child_metadata[_item_map_key]) < len(json_value):
                    child_metadata[_item_map_key].append({} for _ in range(len(json_value) - len(child_metadata[_item_map_key])))
                child_metadata = child_metadata[_item_map_key]
                for i in range(len(child_metadata)):
                    if isinstance(json_value, list):
                        json_val = json_value[i]
                    else:
                        json_val = json_value
                    self._create_child_metadata_of_a_property(child_metadata[i], item_map_keys[1:], type_of_item_type_path[1:], json_val)
        return


    def _get_dimensions(self, lst):
        """
        Get dimensions of list.

        e.g.
            1 -> 0
            [1, 2, 3] -> 1
            [[1, 2], [3, 4]] -> 2
            [[[1, 2], [3, 4]], [[5, 6], [7, 8]]] -> 3
            [] -> 1
        """
        # If lst is not list, return 0
        if not isinstance(lst, list):
            return 0
        # If lst is empty, return 1
        elif not lst:
            return 1
        # If lst is not empty, return 1 + dimensions of lst[0]
        else:
            return 1 + self._get_dimensions(lst[0])


    # TODO: Add methods for extra area.
    def _get_extra_dict(self, path_and_value, all_properties):
        """Get dict of Extra field.

        Args:
            path_and_value (dict): dict contains pairs of path of JSON metadata and a value or list of values
            all_properties (dict): dict contains pairs of path of JSON metadata and a value

        Returns:
            dict: dict to be Extra field
        """
        import re

        list_pop_keys = []

        for k, v in all_properties.items():
            # case that '[' is included in the key.
            if '[' in k:
                # get indices of '[' and ']'
                indice = [int(i) for i in re.findall(r'\[(\d)+\]', k)]
                # get key name without '[' and ']'
                key = re.sub(r'\[\d+\]', '', k)
                if key in path_and_value.keys():
                    # get value from path_and_value
                    value = path_and_value
                    for idx in indice:
                        try:
                            value = value[key][idx]
                        except:
                            value = None
                    if value:
                        list_pop_keys.append(k)
            # case that NO '[' is included in the key.
            else:
                if k in path_and_value.keys():
                    list_pop_keys.append(k)

        for k in list_pop_keys:
            all_properties.pop(k)

        return all_properties


    def is_valid_mapping(self):
        """Check if the mapping is valid."""
        try:
            self.validate_mapping()
        except WekoSwordserverException:
            return False
        return True


    def validate_mapping(self):
        """Validate mapping."""
        item_map = self._create_item_map()
        # FIXME: if required metadata is not defined in the json file.
        # not only top level but also child metadata should be checked.
        error_msg = []
        for k, v in self.json_map.items():
            if k not in item_map:
                error_msg.append(f"{k} is not defined.")

        if error_msg:
            raise WekoSwordserverException(error_msg)
