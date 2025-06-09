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

import re
from datetime import datetime

from invenio_formatter.filters.datetime import from_isodate
from invenio_i18n.ext import current_i18n
from invenio_oaiserver.response import get_identifier
from marshmallow import Schema, fields, missing, ValidationError

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
    def _get_data_by_recursive(meta, value_key, lang_key):
        """Get data by recursive."""
        if isinstance(meta, list):
            value_list = []
            for v in meta:
                temp = _get_data_by_recursive(v, value_key, lang_key)
                if temp:
                    if isinstance(v, dict) and value_key in v:
                        if isinstance(value_list, list):
                            value_list = {}
                        value_list.update(temp)
                    else:
                        value_list.append(temp)
            if value_list:
                return value_list
        elif isinstance(meta, dict):
            if value_key in meta:
                if lang_key in meta:
                    return {meta[lang_key]: meta[value_key]}
                else:
                    return {"None Language": meta[value_key]}
            else:
                for v in list(meta.values()):
                    temp = _get_data_by_recursive(v, value_key, lang_key)
                    if temp:
                        return temp
                return None
        else:
            return None

    def _get_data_by_lang(data_list, cur_lang):
        """Get data by lang."""
        if isinstance(data_list, dict):
            lang_list = list(data_list.keys())
            if cur_lang in lang_list:
                return data_list[cur_lang]
            elif 'en' in lang_list:
                return data_list['en']
            elif len(lang_list) > 0:
                return data_list[lang_list[0]]
            return ''
        if isinstance(data_list, list):
            return_list = []
            for v in data_list:
                temp = _get_data_by_lang(v, cur_lang)
                if temp:
                    return_list.append(temp)
            if return_list:
                return ', '.join(return_list)
            else:
                return ''

    cur_lang = current_i18n.language
    arr = obj['mapping_dict'][key]
    lang_key = obj['mapping_dict']['{}__lang'.format(key)]
    if lang_key:
        lang_key = lang_key[-1]
    result = None
    if arr:
        temp_data = obj[arr[0]]
        data_list = _get_data_by_recursive(temp_data, arr[-1], lang_key)
        result = _get_data_by_lang(data_list, cur_lang)
    return result if result else ''


class RecordSchemaCSLJSON(Schema):
    """Schema for records in CSL-JSON."""

    id = fields.Str(attribute='pid.pid_value')
    version = fields.Method('get_version')
    issued = fields.Method('get_issue_date')
    page = fields.Method('get_page')

    identifier = fields.Method('get_doi')
    if "doi.org" in str(identifier):
        """ extract doi identifier """
        DOI = identifier.split("doi.org/")[1]
    else:
        URL = identifier

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
        date_parts = [[]]
        metadata = get_data_from_mapping('datacite:date', obj)
        if not metadata:
            return missing
        if re.search("\d{4}-\d{2}-\d{2}",metadata):
            format = "%Y-%m-%d"
            metadata = datetime.strptime(metadata, format)
            date = from_isodate(metadata)
            date_parts = [[date.year, date.month, date.day]]
        elif re.search("\d{4}-\d{2}",metadata):
            format = "%Y-%m"
            metadata = datetime.strptime(metadata, format)
            date = from_isodate(metadata)
            date_parts = [[date.year, date.month]]
        elif re.search("\d{4}",metadata):
            format = "%Y"
            metadata = datetime.strptime(metadata, format)
            date = from_isodate(metadata)
            date_parts = [[date.year]]
        else:
            raise ValidationError("Incorrect format")
        
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
