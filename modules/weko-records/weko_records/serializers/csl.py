# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""CSL Docstring."""

import json
from datetime import datetime
from os.path import dirname, join

from jsonref import JsonRef


class ObjectType(object):
    """Class to load object types data."""

    index_id = None
    index_internal_id = None
    types = None
    subtypes = None

    @classmethod
    def _load_data(cls):
        """Load object types for JSON data."""
        if cls.index_id is None:
            with open(join(dirname(__file__), "data", "objecttypes.json")) \
                    as fp:
                data = json.load(fp)

            cls.index_internal_id = {}
            cls.index_id = {}
            cls.types = set()
            cls.subtypes = {}
            for objtype in data:
                cls.index_internal_id[objtype['internal_id']] = objtype
                cls.index_id[objtype['id'][:-1]] = objtype
                if '-' in objtype['internal_id']:
                    type_, subtype = objtype['internal_id'].split('-')
                    cls.types.add(type_)
                    if type_ not in cls.subtypes:
                        cls.subtypes[type_] = set()
                    cls.subtypes[type_].add(subtype)
                else:
                    cls.types.add(objtype['internal_id'])

    @classmethod
    def _jsonloader(cls, uri, **dummy_kwargs):
        """Local JSON loader for JsonRef."""
        cls._load_data()
        return cls.index_id[uri]

    @classmethod
    def get(cls, value):
        """Get object type value."""
        cls._load_data()
        try:
            return JsonRef.replace_refs(
                cls.index_internal_id[value],
                jsonschema=True,
                loader=cls._jsonloader)
        except KeyError:
            return None

    @classmethod
    def get_types(cls):
        """Get object type value."""
        cls._load_data()
        return cls.types

    @classmethod
    def get_subtypes(cls, type_):
        """Get object type value."""
        cls._load_data()
        return cls.subtypes[type_]

    @classmethod
    def get_by_dict(cls, value):
        """Get object type dict with type and subtype key."""
        if not value:
            return None
        if 'subtype' in value:
            if isinstance(value, AttrDict):
                value = value.to_dict()
            internal_id = "{0}-{1}".format(
                value.get('type', ''),
                value.get('subtype', '')
            )
        else:
            internal_id = value['type']
        return cls.get(internal_id)

    @classmethod
    def get_openaire_subtype(cls, value):
        """Get the OpenAIRE community-specific subtype.

        OpenAIRE community-specific subtype requires that the record is
        accepted to the relevant community.

        :param value: Full 'metadata' dictionary. Higher level metadata is
                      required since we are fetching both 'resource_type' and
                      'communities'.
        :type value: dict
        :returns: Subtype in the form "openaire:<OA-comm-ID>:<OA-subtype-ID>"
                  or None.
        :rtype: str
        """
        comms = value.get('communities', [])
        oa_type = value['resource_type'].get('openaire_subtype')
        if oa_type and is_valid_openaire_type(value['resource_type'], comms):
            return 'openaire:' + oa_type
