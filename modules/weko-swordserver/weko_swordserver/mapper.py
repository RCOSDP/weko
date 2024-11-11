# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-swordserver."""

from invenio_oaiharvester.harvester import JsonMapper

from .errors import WekoSwordserverException


class WekoSwordMapper(JsonMapper):
    """WekoSwordMapper."""
    def __init__(self, json, itemtype, json_map):
        """Init."""
        self.json = json
        self.itemtype = itemtype
        self.itemtype_name = itemtype.item_type_name.name
        self.json_map = json_map

    def map(self):
        """Maping JSON-LD;self.json Metadata into item_type format."""
        if self.is_deleted():
            return {}

        res = {
            '$schema': self.itemtype.id,
            'pubdate': str(self.datestamp())
        }

        item_map = self._create_item_map()
        metadata = self._create_metadata(item_map, self.json_map)

        # resourcetype.Type Setting
        if 'resourcetype.Type' in item_map:
            item_path = item_map['resourcetype.Type']
            item_paths = item_path.split('.')
            metadata[item_paths[0]] = {}
            metadata[item_paths[0]][item_paths[1]] = 'dataset'

        res = {**res, **metadata}
        return res


    def _apply_child_metadata(self, child_metadata, json_data, json_keys,
                              subitem_keys):
        """
            This process is part of “_create_metadata” and is not
            intended for any other use.
        """
        def _get_json_value(json, keys):
            """
                Get json value.
            """
            if isinstance(json, dict):
                return _get_json_value(json.get(keys[0]), keys[1:])
            elif isinstance(json, list):
                if len(keys) == 1:
                    return _get_json_value(json[0], keys)
                return [_get_json_value(cv, keys) for cv in json]
            else:
                return json

        json_key = json_keys[0]
        value = json_data.get(json_key)
        if not value:
            # Perform processing only if there are values
            # to be set in the json file.
            return
        elif isinstance(value, dict):
            if len(subitem_keys) == 1:
                # If the subitem code is fixed, the item
                # to be retrieved is fixed.
                if value.get(json_keys[1]):
                    child_metadata[subitem_keys[0]] = _get_json_value(value, json_keys[1:])
            else:
                if not child_metadata.get(subitem_keys[0]):
                    # If Metadata does not yet have a definition,
                    # create a dict that will serve as a container.
                    child_metadata[subitem_keys[0]] = {}
                self._apply_child_metadata(
                    child_metadata[subitem_keys[0]],
                    value, json_keys[1:], subitem_keys[1:])
        else:
            if len(subitem_keys) == 1:
                # If the subitem code is fixed, the item
                #  to be retrieved is fixed.
                for cv in value:
                    child_metadata[subitem_keys[0]] = _get_json_value(cv, json_keys[1:])
            else:
                if not child_metadata.get(subitem_keys[0]):
                    # If Metadata does not yet have a definition,
                    # create a dict that will serve as a container.
                    child_metadata[subitem_keys[0]] = {}
                if child_metadata[subitem_keys[0]].get(subitem_keys[1:][0]):
                    # The case where multiple json values are set for
                    # one item of ItemType.
                    child_metadata[subitem_keys[0]] = [
                        child_metadata[subitem_keys[0]]]
                    child_metadata[subitem_keys[0]].append({})
                    self._apply_child_metadata(
                        child_metadata[subitem_keys[0]][-1],
                        json_data, json_keys, subitem_keys[1:])
                else:
                    self._apply_child_metadata(
                        child_metadata[subitem_keys[0]],
                        json_data, json_keys, subitem_keys[1:])


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
        # FIXME: stack error message and i18n
        for k, v in self.json_map.items():
            if k not in item_map:
                raise WekoSwordserverException(f"Invalid mapping: {k}")
