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
from invenio_i18n.ext import current_i18n
from invenio_oaiserver.response import get_identifier
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
    cur_lang = current_i18n.language
    arr = obj['mapping_dict'][key]
    lang_key = obj['mapping_dict']['{}__lang'.format(key)]
    if lang_key:
        lang_key = lang_key[-1]
    result = None
    if arr:
        result = obj[arr[0]]
        for i in range(len(arr)):
            if i != 0 and result:
                # Update index in order to get data by language.
                if arr[i] in ['attribute_value_mlt', 'creatorNames']:
                    temp = result.get(arr[i])
                    k = 0
                    # Check show data with current language. (1)
                    for j in temp:
                        if j.get(lang_key):
                            if j.get(lang_key) == cur_lang:
                                arr[i+1] = k
                                break
                            k = k + 1
                    # (1) not exist => Priority 'en'. (2)
                    if k == len(temp):
                        k = 0
                        for j in temp:
                            if j.get(lang_key) == 'en':
                                arr[i+1] = k
                                break
                            k = k + 1
                    # (2) not exist => Priority the first element.
                    if k == len(temp):
                        arr[i+1] = 0
                # Get data.
                if type(result) is list:
                    result = result[arr[i]]
                else:
                    result = result.get(arr[i])
    return result if result else ''


class RecordSchemaCSLJSON(Schema):
    """Schema for records in CSL-JSON."""

    id = fields.Str(attribute='pid.pid_value')
    version = fields.Method('get_version')
    issued = fields.Method('get_issue_date')
    page = fields.Method('get_page')
    DOI = fields.Method('get_doi')
    type = fields.Function(
        lambda obj: get_data_from_mapping('dc:type', obj))
    title = fields.Function(
        lambda obj: get_data_from_mapping('dc:title', obj))
    abstract = fields.Function(
        lambda obj: get_data_from_mapping('datacite:description', obj))
    author = fields.Function(
        lambda obj: [{
            'given': None,
            'suffix': get_data_from_mapping('jpcoar:creator', obj),
            'family': None}])
    language = fields.Function(
        lambda obj: get_data_from_mapping('dc:language', obj))
    container_title = fields.Function(
        lambda obj: get_data_from_mapping('dcterms:alternative', obj))
    volume = fields.Function(
        lambda obj: get_data_from_mapping('jpcoar:volume', obj))
    issue = fields.Function(
        lambda obj: get_data_from_mapping('jpcoar:issue', obj))
    publisher = fields.Function(
        lambda obj: get_data_from_mapping('dc:publisher', obj))

    def get_version(self, obj):
        """Get version."""
        version = None
        itemdatas = _get_itemdata(obj['metadata'], 'Version')
        schema = get_attribute_schema(config.WEKO_ITEMPROPS_SCHEMAID_VERSION)
        if not itemdatas:
            return missing
        for itemdata in itemdatas:
            _, version = _get_mapping_data(schema, itemdata, "Version")
        if version:
            return version
        return missing

    def get_issue_date(self, obj):
        """Get issue date."""
        metadata = get_data_from_mapping('datacite:date', obj)
        if not metadata:
            return missing
        date = from_isodate(metadata)
        date_parts = [[date.year, date.month, date.day]]
        result = {'date-parts': date_parts}
        return result if date else missing

    def get_page(self, obj):
        """Get page."""
        page_start = get_data_from_mapping('jpcoar:pageStart', obj)
        page_end = get_data_from_mapping('jpcoar:pageEnd', obj)
        if not page_start and not page_end:
            return missing
        return '{}-{}'.format(page_start, page_end)

    def get_doi(self, obj):
        """Get doi."""
        # Get DOI info and add to metadata.
        identifier = 'system_identifier'
        record = obj['record']
        identifier_data = get_identifier(record)
        obj['metadata'][identifier] = identifier_data
        return get_data_from_mapping('jpcoar:identifier', obj)
