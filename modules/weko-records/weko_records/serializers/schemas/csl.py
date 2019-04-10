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

from invenio_formatter.filters.datetime import from_isodate
from marshmallow import Schema, fields, missing

from weko_records.serializers.csl import ObjectType


def _get_itemdata(obj, key):
    metadata = obj['metadata']
    for item in metadata:
        itemdata = metadata.get(item, {})
        if (type(itemdata)) is dict and itemdata.get('attribute_name') == key:
            return itemdata.get('attribute_value_mlt')

    return None


def _get_creator_by_lang(textdata, lang):
    creator_name = []
    for text in textdata:
        for value in sorted(text[0]):
            if text[0][value] == lang:
                creator_name.append([text[0][index]
                                     for index in sorted(text[0])].pop(0))

    return creator_name


def get_names_from_obj(obj):
    creator_name = []
    itemdatas = {}
    for item in obj:
        itemdata = obj.get(item, {})
        if (type(itemdata)) is dict and itemdata.get('attribute_name') == 'Creator':
            itemdatas = itemdata.get('attribute_value_mlt')

    for itemdata in itemdatas:
        textdata = [itemdata[val] for val in sorted(itemdata)]
        creator_name.append(_get_creator_by_lang(textdata, 'en'))

    return creator_name[0]


class CreatorSchema(Schema):
    """Schema for an creator."""

    family = fields.Method('get_family_name')
    given = fields.Method('get_given_name')
    name = fields.Method('get_name')

    def get_family_name(self, obj):
        """Get family name."""
        family_name = get_names_from_obj(obj)[1]
        return family_name if family_name else 'family'

    def get_given_name(self, obj):
        """Get given name."""
        given_name = get_names_from_obj(obj)[2]
        return given_name if given_name else 'given'

    def get_name(self, obj):
        """Get name."""
        _name = get_names_from_obj(obj)[0]
        return _name if _name else 'name'


class RecordSchemaCSLJSON(Schema):
    """Schema for records in CSL-JSON."""

    id = fields.Str(attribute='pid.pid_value')
    type = fields.Str(attribute='metadata.item_type_id')
    title = fields.Str(attribute='metadata.item_title')
    abstract = fields.Method('get_description')
    # author = fields.List(fields.Nested(CreatorSchema), attribute='metadata')

    issued = fields.Method('get_issue_date')
    language = fields.Method('get_language')
    version = fields.Method('get_version')
    note = fields.Str('This data is not map with zenodo')

    DOI = fields.Method('get_doi')
    ISBN = fields.Str('This data is not map with zenodo')
    ISSN = fields.Str('This data is not map with zenodo')

    container_title = fields.Method('get_container_title')
    page = fields.Method('get_pages')
    volume = fields.Method('get_volume')
    issue = fields.Method('get_issue')

    publisher = fields.Method('get_publisher')
    publisher_place = fields.Str('This data is not map with zenodo')

    def get_description(self, obj):
        """Get description."""
        description = []
        itemdatas = _get_itemdata(obj, 'Description')
        if itemdatas is None:
            return 'Not description data'

        for itemdata in itemdatas:
            textdata = [itemdata[val] for val in sorted(itemdata)]
            description.append(
                (('{} ({})-Type:{}').format(textdata[0], textdata[1], textdata[2])))

        return description[0]

    def get_creator(self, obj):
        """Get creator."""
        creator_name = []
        itemdatas = _get_itemdata(obj, 'Creator')
        if itemdatas is None:
            return 'Not creator data'

        for itemdata in itemdatas:
            textdata = [itemdata[val] for val in sorted(itemdata)]
            creator_name.append(_get_creator_by_lang(textdata, 'en'))

        return creator_name[0]

    def get_issue_date(self, obj):
        """Get issue date."""
        issue_date = []
        itemdatas = _get_itemdata(obj, 'Date')
        if itemdatas is None:
            return 'Not issue date data'

        for itemdata in itemdatas:
            textdata = [itemdata[val] for val in sorted(itemdata)]
            datedata = from_isodate(textdata[0])
            issue_date.append(
                {'date-parts': [[datedata.year, datedata.month, datedata.day]]} if datedata else missing)

        return issue_date[0]

    def get_language(self, obj):
        """Get language."""
        language = []
        itemdatas = _get_itemdata(obj, 'Language')
        if itemdatas is None:
            return 'Not language data'

        for itemdata in itemdatas:
            language.append(itemdata.popitem()[1])

        return language[0]

    def get_version(self, obj):
        """Get version."""
        version = []
        itemdatas = _get_itemdata(obj, 'Version')
        if itemdatas is None:
            return 'Not version data'

        for itemdata in itemdatas:
            version.append(itemdata.popitem()[1])

        return version[0]

    def get_doi(self, obj):
        """Get DOI."""
        doi = []
        itemdatas = _get_itemdata(obj, 'Identifier Registration')
        if itemdatas is None:
            return 'Not DOI data'

        for itemdata in itemdatas:
            textdata = [itemdata[val] for val in sorted(itemdata)]
            doi.append(('{} ({})').format(textdata[0], textdata[1]))

        return doi[0]

    def get_container_title(self, obj):
        """Get alternative title."""
        alternative_title = []
        itemdatas = _get_itemdata(obj, 'Alternative Title')
        if itemdatas is None:
            return 'Not alternative title data'

        for itemdata in itemdatas:
            textdata = [itemdata[val] for val in sorted(itemdata)]
            alternative_title.append(
                ('{} ({})').format(textdata[0], textdata[1]))

        return alternative_title[0]

    def get_pages(self, obj):
        """Get number of pages."""
        pages = []
        itemdatas = _get_itemdata(obj, 'Number of Pages')
        if itemdatas is None:
            return 'Not alternative title data'

        for itemdata in itemdatas:
            pages.append(itemdata.popitem()[1])

        return pages[0]

    def get_volume(self, obj):
        """Get volume."""
        volume = []
        itemdatas = _get_itemdata(obj, 'Volume Number')
        if itemdatas is None:
            return 'Not volume data'

        for itemdata in itemdatas:
            volume.append(itemdata.popitem()[1])

        return volume[0]

    def get_issue(self, obj):
        """Get issue number."""
        issue = []
        itemdatas = _get_itemdata(obj, 'Issue Number')
        if itemdatas is None:
            return 'Not issue number data'

        for itemdata in itemdatas:
            issue.append(itemdata.popitem()[1])

        return issue[0]

    def get_publisher(self, obj):
        """Get publisher."""
        publisher = []
        itemdatas = _get_itemdata(obj, 'Publisher')
        if itemdatas is None:
            return 'No publisher data'

        for itemdata in itemdatas:
            textdata = [itemdata[val] for val in sorted(itemdata)]
            publisher.append(('{} ({})').format(textdata[0], textdata[1]))

        return publisher[0]
