# -*- coding: utf-8 -*-
#
# This file is part of Zenodo.
# Copyright (C) 2016 CERN.
#
# Zenodo is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Zenodo is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Zenodo; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Weko CSL-JSON schema."""

from __future__ import absolute_import, print_function

from invenio_formatter.filters.datetime import from_isodate
from marshmallow import Schema, fields, missing

import weko_records.config as config
from weko_records.serializers.utils import get_attribute_schema


def _get_itemdata(obj, key):
    """Get data from 'attribute_value_mlt' phase."""
    for item in obj:
        itemdata = obj.get(item, {})
        if (type(itemdata)) is dict and itemdata.get('attribute_name') == key:
            value = itemdata.get('attribute_value_mlt')
            if value:
                return value
    return None


def _get_mapping_data(schema, data, keyword):
    """Get mapping by item type."""
    for key, value in schema.get('properties').items():
        if data and value.get('title') == keyword:
            return value, data.get(key)
    return None, None


def get_data_from_mapping(key, obj):
    """Get data base on mapping."""
    arr = obj['mapping_dict'][key]
    result = None
    if arr:
        result = obj[arr[0]]
        for i in range(len(arr)):
            if i != 0 and result:
                if type(result) is list:
                    result = result[arr[i]]
                else:
                    result = result.get(arr[i])
    return result if result else missing


class RecordSchemaCSLJSON(Schema):
    """Schema for records in CSL-JSON."""

    id = fields.Str(attribute='pid.pid_value')
    version = fields.Method('get_version')
    issued = fields.Method('get_issue_date')
    type = fields.Function(
        lambda obj: get_data_from_mapping('dc:type', obj))
    title = fields.Function(
        lambda obj: get_data_from_mapping('dc:title', obj))
    abstract = fields.Function(
        lambda obj: get_data_from_mapping('datacite:description', obj))
    author = fields.Function(
        lambda obj: [{'given': None, 'suffix':
            get_data_from_mapping('jpcoar:creator', obj), 'family': None}])
    language = fields.Function(
        lambda obj: get_data_from_mapping('dc:language', obj))
    DOI = fields.Function(
        lambda obj: get_data_from_mapping('jpcoar:identifier', obj))
    container_title = fields.Function(
        lambda obj: get_data_from_mapping('dcterms:alternative', obj))
    page = fields.Function(
        lambda obj: get_data_from_mapping('jpcoar:numPages', obj))
    volume = fields.Function(
        lambda obj: get_data_from_mapping('jpcoar:volume', obj))
    issue = fields.Function(
        lambda obj: get_data_from_mapping('datacite:date', obj))
    publisher = fields.Function(
        lambda obj: get_data_from_mapping('dc:publisher', obj))

    def get_issue_date(self, obj):
        """Get issue date."""
        metadata = get_data_from_mapping('datacite:date', obj)
        if metadata is None:
            return missing
        datedata = from_isodate(metadata)
        return {'date-parts': [[datedata.year, datedata.month,
                                datedata.day]]} if datedata else missing

    def get_version(self, obj):
        """Get version."""
        version = None
        itemdatas = _get_itemdata(obj['metadata'], 'Version')
        schema = get_attribute_schema(config.WEKO_ITEMPROPS_SCHEMAID_VERSION)
        if itemdatas is None:
            return missing
        for itemdata in itemdatas:
            _, version = _get_mapping_data(schema, itemdata, "Version")
        if version:
            return version
        return missing
