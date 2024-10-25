# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-swordserver."""

from invenio_oaiharvester.harvester import JsonMapper


class WekoSwordMapper(JsonMapper):
    """WekoSwordMapper."""
    def __init__(self, json, itemtype_name, json_map):
        """Init."""
        self.json_map = json_map
        super().__init__(json, itemtype_name)

    def map(self):
        """Maping JSON-LD;self.json Metadata into item_type format."""
        if self.is_deleted():
            return {}

        res = {'$schema': self.itemtype.id,
               'pubdate': str(self.datestamp())}

        item_map = self._create_item_map()

        metadata = self._create_metadata(item_map, self.json_map)

        """ resourcetype.Type Setting """
        item_path = item_map['resourcetype.Type']
        item_paths = item_path.split('.')
        metadata[item_paths[0]] = {}
        metadata[item_paths[0]][item_paths[1]] = 'dataset'

        res = {**res, **metadata}
        return res
