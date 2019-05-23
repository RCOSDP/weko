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

import json

from invenio_formatter.filters.datetime import from_isodate
from marshmallow import Schema, fields, missing

import weko_records.config as config
from weko_records.serializers.utils import get_attribute_schema, \
    get_item_type_name, get_item_type_name_id

from flask import current_app
import json


def _get_itemdata(obj, key):
    """Get data from 'attribute_value_mlt' phase."""
    for item in obj:
        itemdata = obj.get(item, {})
        if (type(itemdata)) is dict and itemdata.get('attribute_name') == key:
            value = itemdata.get('attribute_value_mlt')
            if value:
                return value
    return None


def _get_mapping_data(inschema, indata, inText):
    """Get mapping by item type."""
    for key, value in inschema.get('properties').items():
        if value.get('title') == inText:
            return value, indata.get(key)
    return None


def _get_creator_name(obj, inName):
    """Parsing creator data for multiple item type."""
    schema = get_attribute_schema(config.WEKO_ITEMPROPS_SCHEMAID_CREATOR)
    value, name_data = _get_mapping_data(schema, obj, inName)
    if name_data:
        _, name = _get_mapping_data(value.get('items'), name_data[0], inName)

    if name:
        return name
    return None


def _get_creator_name_ex_it(obj, inName):
    """Parsing creator data for multiple item type."""
    itemdatas = _get_itemdata(obj, '作成者')
    if itemdatas is None:
        return None

    for itemdata in itemdatas:
        family_name = itemdata.get(inName + 's')
        if family_name:
            return family_name[0].get(inName)
        else:
            return None


class CreatorSchema(Schema):
    """Schema for an creator."""

    family = fields.Method('get_family_name')
    given = fields.Method('get_given_name')
    suffix = fields.Method('get_suffix_name')

    def get_family_name(self, obj):
        """Get family name."""
        # current_app.logger.debug(obj)
        # item_type = get_item_type_name_id(obj.get('item_type_id'))
        # if item_type <= config.WEKO_ITEMTYPE_ID_BASEFILESVIEW:
        #     family_name = _get_creator_name_ex_it(obj, 'familyName')
        # else:
        family_name = _get_creator_name(obj, "Family Name")

        if family_name:
            return family_name

    def get_given_name(self, obj):
        """Get given name."""
        # current_app.logger.debug(obj)
        # item_type = get_item_type_name_id(obj.get('item_type_id'))
        # if item_type <= config.WEKO_ITEMTYPE_ID_BASEFILESVIEW:
        #     given_name = _get_creator_name_ex_it(obj, 'givenName')
        # else:
        given_name = _get_creator_name(obj, "Given Name")

        if given_name:
            return given_name

    def get_suffix_name(self, obj):
        """Get suffix name."""
        # current_app.logger.debug(obj)
        # item_type = get_item_type_name_id(obj.get('item_type_id'))
        # if item_type <= config.WEKO_ITEMTYPE_ID_BASEFILESVIEW:
        #     suffix_name = _get_creator_name_ex_it(obj, 'creatorName')
        # else:
        suffix_name = _get_creator_name(obj, "Creator Name")

        if suffix_name:
            return suffix_name


class RecordSchemaCSLJSON(Schema):
    """Schema for records in CSL-JSON."""

    _attr_creators = 'metadata.item_1551264340087.attribute_value_mlt'
    id = fields.Str(attribute='pid.pid_value')
    type = fields.Method('get_itemtype_name')
    title = fields.Str(attribute='metadata.item_title')
    abstract = fields.Method('get_description')
    author = fields.List(fields.Nested(CreatorSchema),
                         attribute=_attr_creators)

    issued = fields.Method('get_issue_date')
    language = fields.Method('get_language')
    version = fields.Method('get_version')

    DOI = fields.Method('get_doi')

    container_title = fields.Method('get_container_title')
    page = fields.Method('get_pages')
    volume = fields.Method('get_volume')
    issue = fields.Method('get_issue')

    publisher = fields.Method('get_publishers')

    def get_creators_itemid(self, obj):
        """Get description."""
        for item in obj['metadata']:
            itemdata = obj.get(item, {})
            if (type(itemdata)) is dict and itemdata.get('attribute_name') == 'Creator':
                value = itemdata

        if value:
            return 'metadata.' + value + '.attribute_value_mlt'
        return missing

    def get_itemtype_name(self, obj):
        """Get description."""
        item_type = get_item_type_name(obj['metadata'].get('item_type_id'))

        if item_type:
            return item_type
        return missing

    def get_description(self, obj):
        """Get description."""
        itemdatas = _get_itemdata(obj['metadata'], 'Description')
        schema = get_attribute_schema(config.WEKO_ITEMPROPS_SCHEMAID_DESCRIP)
        if itemdatas is None:
            return missing

        for itemdata in itemdatas:
            _, description = _get_mapping_data(schema, itemdata, "Description")

        if description:
            return description
        return missing

    def get_issue_date(self, obj):
        """Get issue date."""
        metadata = obj['metadata']['pubdate']['attribute_value']
        if metadata is None:
            return missing
        else:
            datedata = from_isodate(metadata)
            return {'date-parts': [[datedata.year, datedata.month,
                                    datedata.day]]} if datedata else missing

    def get_language(self, obj):
        """Get language."""
        language = []
        itemdatas = _get_itemdata(obj['metadata'], 'Language')
        schema = get_attribute_schema(config.WEKO_ITEMPROPS_SCHEMAID_LANGUAG)
        if itemdatas is None:
            return missing

        for itemdata in itemdatas:
            _, language = _get_mapping_data(schema, itemdata, "Language")

        if language:
            return language
        return missing

    def get_version(self, obj):
        """Get version."""
        itemdatas = _get_itemdata(obj['metadata'], 'Version')
        schema = get_attribute_schema(config.WEKO_ITEMPROPS_SCHEMAID_VERSION)
        if itemdatas is None:
            return missing

        for itemdata in itemdatas:
            _, version = _get_mapping_data(schema, itemdata, "Version")

        if version:
            return version
        return missing

    def get_doi(self, obj):
        """Get DOI."""
        itemdatas = _get_itemdata(obj['metadata'], 'Identifier Registration')
        schema = get_attribute_schema(config.WEKO_ITEMPROPS_SCHEMAID_DOI)
        if itemdatas is None:
            return missing

        for itemdata in itemdatas:
            _, doi = _get_mapping_data(
                schema, itemdata, "Identifier Registration")
            _, doi_type = _get_mapping_data(
                schema, itemdata, "Identifier Registration Type")

        if doi:
            return '{} ({})'.format(doi, doi_type)
        return missing

    def get_container_title(self, obj):
        """Get alternative title."""
        alternative_title = []
        itemdatas = _get_itemdata(obj['metadata'], 'Alternative Title')
        schema = get_attribute_schema(69)
        if itemdatas is None:
            return missing

        for itemdata in itemdatas:
            _, data = _get_mapping_data(schema, itemdata, "Alternative Title")
            alternative_title.append(config.WEKO_ITEMPROPS_SCHEMAID_ALTITLE)

        if len(alternative_title):
            return alternative_title[0]
        return missing

    def get_pages(self, obj):
        """Get number of pages."""
        itemdatas = _get_itemdata(obj['metadata'], 'Number of Pages')
        schema = get_attribute_schema(config.WEKO_ITEMPROPS_SCHEMAID_PAGES)
        if itemdatas is None:
            return missing

        for itemdata in itemdatas:
            _, pages = _get_mapping_data(schema, itemdata, "Number of Pages")

        if pages:
            return pages
        return missing

    def get_volume(self, obj):
        """Get volume."""
        itemdatas = _get_itemdata(obj['metadata'], "Volume Number")
        schema = get_attribute_schema(config.WEKO_ITEMPROPS_SCHEMAID_VOLUME)
        if itemdatas is None:
            return missing

        for itemdata in itemdatas:
            _, volume = _get_mapping_data(schema, itemdata, "Volume Number")

        if volume:
            return volume
        return missing

    def get_issue(self, obj):
        """Get issue number."""
        itemdatas = _get_itemdata(obj['metadata'], "Issue Number")
        schema = get_attribute_schema(config.WEKO_ITEMPROPS_SCHEMAID_ISSUENO)
        if itemdatas is None:
            return missing

        for itemdata in itemdatas:
            _, issue = _get_mapping_data(schema, itemdata, "Issue Number")

        if issue:
            return issue
        return missing

    def get_publishers(self, obj):
        """Get publisher."""
        publisher = []
        itemdatas = _get_itemdata(obj['metadata'], "Publisher")
        schema = get_attribute_schema(config.WEKO_ITEMPROPS_SCHEMAID_PUBLISH)
        if itemdatas is None:
            return missing

        for itemdata in itemdatas:
            _, data = _get_mapping_data(schema, itemdata, "Publisher")
            publisher.append(data)

        if len(publisher):
            return publisher[0]
        return missing
