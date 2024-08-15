# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2024 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Utility functions for data processing."""

import os
from functools import wraps

from flask import current_app
from invenio_search import current_search
from invenio_search.utils import build_index_from_parts


def schema_to_index(schema, index_names=None):
    """Get index given a schema URL.

    :param schema: The schema name
    :param index_names: A list of index name.
    :returns: The index.
    """
    parts = schema.split("/")
    rec_type, ext = os.path.splitext(parts[-1])
    parts[-1] = rec_type

    if ext not in {
        ".json",
    }:
        return None

    if index_names is None:
        index = build_index_from_parts(*parts)
        return index

    for start in range(len(parts)):
        name = build_index_from_parts(*parts[start:])
        if name in index_names:
            return name

    return None


def default_record_to_index(record):
    """Get index given a record.

    It tries to extract from `record['$schema']` the index.
    If it fails, return the default values.

    :param record: The record object.
    :returns: index.
    """
    # The indices could be defined either in the mappings or in the index_templates
    index_names = list(current_search.mappings.keys()) + list(
        current_search.index_templates.keys()
    )
    schema = record.get("$schema", "")
    if isinstance(schema, dict):
        schema = schema.get("$ref", "")

    index = schema_to_index(schema, index_names=index_names)

    return index or current_app.config["INDEXER_DEFAULT_INDEX"]
