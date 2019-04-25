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


def _get_itemdata(obj, key):
    """Get data from 'attribute_value_mlt' phase."""
    for item in obj:
        itemdata = obj.get(item, {})
        if (type(itemdata)) is dict and itemdata.get('attribute_name') == key:
            return itemdata.get('attribute_value_mlt')

    return None


def _get_creator_by_lang(textdata, lang):
    """Get creator name by lang."""
    creator_name = []
    for text in textdata:
        for value in sorted(text[0]):
            if text[0][value] == lang:
                creator_name.append([text[0][index]
                                     for index in sorted(text[0])].pop(0))

    return creator_name


def _get_relation_by_type(textdata, inputtype):
    """Get realtion name by type."""
    result = None
    for text in textdata:
        if type(text) is list:
            for relation in text:
                for subitem in relation:
                    if relation[subitem] == inputtype:
                        result = relation
    if result is not None:
        result = [result[index] for index in sorted(result)]
    return result


def _get_names_from_obj(obj):
    """Parsing data from 'Creator' data."""
    creator_name = []
    itemdatas = _get_itemdata(obj, 'Creator')
    if itemdatas is None:
        return None

    for itemdata in itemdatas:
        textdata = [itemdata[val] for val in sorted(itemdata)]
        creator_data = _get_creator_by_lang(textdata, 'ja')
        if len(creator_data) > 0:
            creator_name.append(creator_data)

    for itemdata in itemdatas:
        textdata = [itemdata[val] for val in sorted(itemdata)]
        creator_data = _get_creator_by_lang(textdata, 'en')
        if len(creator_data) > 0:
            creator_name.append(creator_data)

    if len(creator_name):
        return creator_name[0]
    else:
        return None


class CreatorSchema(Schema):
    """Schema for an creator."""

    family = fields.Method('get_family_name')
    given = fields.Method('get_given_name')
    suffix = fields.Method('get_suffix_name')

    def get_family_name(self, obj):
        """Get family name."""
        if _get_names_from_obj(obj) is not None:
            return _get_names_from_obj(obj)[1]
        else:
            return missing

    def get_given_name(self, obj):
        """Get given name."""
        if _get_names_from_obj(obj) is not None:
            return _get_names_from_obj(obj)[2]
        else:
            return missing

    def get_suffix_name(self, obj):
        """Get suffix name."""
        if _get_names_from_obj(obj) is not None:
            return _get_names_from_obj(obj)[0]
        else:
            return missing


class RecordSchemaCSLJSON(Schema):
    """Schema for records in CSL-JSON."""

    id = fields.Str(attribute='pid.pid_value')
    type = fields.Str(attribute='metadata.item_type_id')
    title = fields.Str(attribute='metadata.item_title')
    abstract = fields.Method('get_description')
    author = fields.List(fields.Nested(CreatorSchema), attribute='metadata')

    issued = fields.Method('get_issue_date')
    language = fields.Method('get_language')
    version = fields.Method('get_version')
    note = fields.Str('')

    DOI = fields.Method('get_doi')
    ISBN = fields.Method('get_isbn')
    ISSN = fields.Method('get_issn')

    container_title = fields.Method('get_container_title')
    page = fields.Method('get_pages')
    volume = fields.Method('get_volume')
    issue = fields.Method('get_issue')

    publisher = fields.Method('get_publisher')
    publisher_place = fields.Str('')

    def get_description(self, obj):
        """Get description."""
        description = []
        itemdatas = _get_itemdata(obj['metadata'], 'Description')
        if itemdatas is None:
            return missing

        for itemdata in itemdatas:
            textdata = [itemdata[val] for val in sorted(itemdata)]
            description.append(
                '{} ({})-Type:{}'.format(textdata[0], textdata[1],
                                         textdata[2]))

        return description[0]

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
        if itemdatas is None:
            return missing

        for itemdata in itemdatas:
            language.append(itemdata.popitem()[1])

        return language[0]

    def get_version(self, obj):
        """Get version."""
        version = []
        itemdatas = _get_itemdata(obj['metadata'], 'Version')
        if itemdatas is None:
            return missing

        for itemdata in itemdatas:
            version.append(itemdata.popitem()[1])

        return version[0]

    def get_doi(self, obj):
        """Get DOI."""
        doi = []
        itemdatas = _get_itemdata(obj['metadata'], 'Identifier Registration')
        if itemdatas is None:
            return missing

        for itemdata in itemdatas:
            textdata = [itemdata[val] for val in sorted(itemdata)]
            doi.append('{} ({})'.format(textdata[0], textdata[1]))

        return doi[0]

    def get_container_title(self, obj):
        """Get alternative title."""
        alternative_title = []
        itemdatas = _get_itemdata(obj['metadata'], 'Alternative Title')
        if itemdatas is None:
            return missing

        for itemdata in itemdatas:
            textdata = [itemdata[val] for val in sorted(itemdata)]
            alternative_title.append(
                '{} ({})'.format(textdata[0], textdata[1]))

        return alternative_title[0]

    def get_pages(self, obj):
        """Get number of pages."""
        pages = []
        itemdatas = _get_itemdata(obj['metadata'], 'Number of Pages')
        if itemdatas is None:
            return missing

        for itemdata in itemdatas:
            pages.append(itemdata.popitem()[1])

        return pages[0]

    def get_volume(self, obj):
        """Get volume."""
        volume = []
        itemdatas = _get_itemdata(obj['metadata'], 'Volume Number')
        if itemdatas is None:
            return missing

        for itemdata in itemdatas:
            volume.append(itemdata.popitem()[1])

        return volume[0]

    def get_issue(self, obj):
        """Get issue number."""
        issue = []
        itemdatas = _get_itemdata(obj['metadata'], 'Issue Number')
        if itemdatas is None:
            return missing

        for itemdata in itemdatas:
            issue.append(itemdata.popitem()[1])

        return issue[0]

    def get_publisher(self, obj):
        """Get publisher."""
        publisher = []
        itemdatas = _get_itemdata(obj['metadata'], 'Publisher')
        if itemdatas is None:
            return missing

        for itemdata in itemdatas:
            textdata = [itemdata[val] for val in sorted(itemdata)]
            publisher.append('{} ({})'.format(textdata[0], textdata[1]))

        return publisher[0]

    def get_isbn(self, obj):
        """Get ISBN."""
        isbn_data = []
        itemdatas = _get_itemdata(obj['metadata'], 'Relation')
        if itemdatas is None:
            return missing

        for itemdata in itemdatas:
            textdata = [itemdata[val] for val in sorted(itemdata)]
            isbn = _get_relation_by_type(textdata, 'ISBN')
            if isbn is not None:
                isbn_data.append(isbn[0])

        if len(isbn_data):
            return isbn_data[0]
        else:
            return missing

    def get_issn(self, obj):
        """Get ISSN."""
        issn_data = []
        itemdatas = _get_itemdata(obj['metadata'], 'Relation')
        if itemdatas is None:
            return missing

        for itemdata in itemdatas:
            textdata = [itemdata[val] for val in sorted(itemdata)]
            issn = _get_relation_by_type(textdata, 'ISSN')
            if issn is not None:
                issn_data.append(issn[0])

        if len(issn_data):
            return issn_data[0]
        else:
            return missing

    def get_publisher_place(self, obj):
        """Get alternative title."""
        publisher_place = []
        itemdatas = _get_itemdata(obj['metadata'], 'Geo Location')
        if itemdatas is None:
            return missing

        for itemdata in itemdatas:
            textdata = [itemdata[val] for val in sorted(itemdata)]
            if textdata[2]:
                publisher_place.append(textdata[2])

        return publisher_place[0]
