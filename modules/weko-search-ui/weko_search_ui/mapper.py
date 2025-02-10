# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Search-Ui is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


import xmltodict

from flask import current_app

from weko_records.api import ItemTypes
from weko_records.serializers.utils import get_full_mapping

class BaseMapper:
    """BaseMapper."""

    itemtype_map = {}
    identifiers = []

    @classmethod
    def update_itemtype_map(cls):
        """Update itemtype map."""
        for t in ItemTypes.get_all(with_deleted=False):
            cls.itemtype_map[t.item_type_name.name] = t

    def __init__(self, xml):
        """Init."""
        self.xml = xml
        self.json = xmltodict.parse(xml) if xml else {}
        if not BaseMapper.itemtype_map:
            BaseMapper.update_itemtype_map()

        self.itemtype = None
        for item in BaseMapper.itemtype_map:
            if "Others" == item or "Multiple" == item:
                self.itemtype = BaseMapper.itemtype_map.get(item)
                break


class JsonMapper(BaseMapper):
    """ Mapper to map from Json format file to ItemType.

        The original file to be mapped by this Mapper is assumed to be a
        JSON-LD or a file described in JSON.

        The information to be used for this mapper mapping is created and used
        based on the contents of item_type.schema.

        In this Mapper, do not write your own mapping code for individual
        items, but implement mapping by the rules of item_type.schema,
        JSON-LD or JSON description format.

    """
    def __init__(self, json, itemtype_id=None, itemtype_name=None):
        self.json = json
        if itemtype_id is not None:
            self.itemtype = ItemTypes.get_by_id(itemtype_id)
            self.itemtype_name = self.itemtype.item_type_name.name

        else:
            self.itemtype_name = itemtype_name
            if not BaseMapper.itemtype_map:
                BaseMapper.update_itemtype_map()

            for item in BaseMapper.itemtype_map:
                if self.itemtype_name == item:
                    self.itemtype = BaseMapper.itemtype_map.get(item)

    def _create_item_map(self):
        """ Create Mapping information from ItemType.

            This mapping information consists of the following.

                KEY: Identifier for the ItemType item
                        (value obtained by concatenating the “title”
                        attribute of each item in the schema)
                VALUE: Item Code. Subitem code identifier.

            Returns:
                item_map: Mapping information about ItemType.

            Examples:
                For example, in the case of “Title of BioSample of ItemType”,
                it would be as follows.

                KEY: title.Title
                VALUE: item_1723710826523.subitem_1551255647225
        """

        item_map = {}
        for prop_k, prop_v in self.itemtype.schema["properties"].items():
            self._apply_property(item_map, "", "", prop_k, prop_v)
        return item_map

    def _apply_property(self, item_map, key, value, prop_k, prop_v):
        """
            This process is part of “_create_item_map” and is not
            intended for any other use.
        """
        if "title" in prop_v:
            key = key + "." + prop_v["title"] if key else prop_v["title"]
            value = value + "." + prop_k if value else prop_k

        if prop_v["type"] == "object":
            for child_k, child_v in prop_v["properties"].items():
                self._apply_property(item_map, key, value, child_k, child_v)
        elif prop_v["type"] == "array":
            self._apply_property(
                item_map, key, value, "items", prop_v["items"])
        else:
            item_map[key] = value


class JsonLdMapper(JsonMapper):
    """JsonLdMapper."""
    def __init__(self, itemtype_id, json_mapping):
        """Init."""
        self.json_mapping = json_mapping
        super().__init__(None, itemtype_id)

    def map_to_itemtype(self, json_ld):
        """Map to item type."""
        metadata = JsonLdMapper.process_json_ld(json_ld)
        item_map = self._create_item_map()
        mapped_metadata = {

        }

        # result = {
        #     "pubdate": self.json_id.get("datePublished"),
        #     "publish_status": "private",
        #     "path": self.json_id.get("wk:index"),
        #     "item_1617186331708": {},
        #     "item_1617258105262": {},
        #     ...
        # }
        return mapped_metadata

    @staticmethod
    def process_json_ld(json_ld):
        """Process json-ld.

        Make metadata json-ld data flat.
        Pick up metadata from @graph and resolve links
        to be able to use in mapping to WEKO item type.

        Note:
            SWORDBagIt metadata format is not supported yet.

        Args:
            json_ld (dict): Json-ld data.

        Returns:
            dict: Processed json data.
        """
        metadata = {}
        context = json_ld.get("@context", "")
        format = ""

        # check if the json-ld context is valid
        if "https://swordapp.github.io/swordv3/swordv3.jsonld" in context:
            # TODO: support SWORD json-ld format
            format = "sword-bagit"
            pass
        elif "https://w3id.org/ro/crate/1.1/context" in context:
            # check structure of RO-Crate json-ld
            format = "ro-crate"
            if "@graph" not in json_ld or not isinstance(json_ld.get("@graph"), list):
                msg = 'Invalid json-ld format: "@graph" is not found.'
                raise ValueError(msg)
            # transform list which contains @id to dict in @graph
            for v in json_ld.get("@graph"):
                if isinstance(v, dict) and "@id" in v:
                    metadata.update({v["@id"]: v})
                else:
                    msg = "Invalid json-ld format: Objects without “@id” are directly under “@graph"
                    raise ValueError(msg)
        else:
            msg = 'Invalid json-ld format: "@context" is not found.'
            raise ValueError(msg)


        def _resolve_link(parent, key, value):
            if isinstance(value, dict):
                if len(value) == 1 and "@id" in value and value["@id"] in metadata:
                    parent[key] = metadata[value["@id"]]
                else:
                    for k, v in value.items():
                        _resolve_link(value, k, v)
            elif isinstance(value, list):
                for i, v in enumerate(value):
                    _resolve_link(value, i, v)

        # Restore metadata to tree structure by tracing "@id" in linked data
        for key, value in metadata.items():
            _resolve_link(metadata, key, value)

        processed_metadata = {}

        def _parse_metadata(parent, key, value):
            if isinstance(value, dict):
                for k, v in value.items():
                    key_name = key if parent == "" else f"{parent}.{key}"
                    _parse_metadata(key_name, k, v)
            elif isinstance(value, list):
                for i, d in enumerate(value):
                    key_name = f"{key}[{i}]" if parent == "" else f"{parent}.{key}[{i}]"
                    if isinstance(d, dict):
                        for k, v in d.items():
                            _parse_metadata(key_name, k, v)
                    else:
                        processed_metadata[key_name] = d
            else:
                if key == "@type":
                    return
                key_name = key if parent == "" else f"{parent}.{key}"
                processed_metadata[key_name] = value

        # Get the root of the metadata tree structure
        root = metadata.get(
            current_app.config["WEKO_SWORDSERVER_METADATA_FILE_ROCRATE"]
            ).get("about").get("@id")
        if not root in metadata:
            msg = "Invalid json-ld format: Root object is not found."
            raise ValueError(msg)

        for key, value in metadata.get(root).items():
            _parse_metadata("", key, value)

        return processed_metadata, format
