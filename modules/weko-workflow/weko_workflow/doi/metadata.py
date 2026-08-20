# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Metadata supply layer shared by every DOI registration agency.

The agencies never touch the raw item metadata.  They ask this class for
JPCOAR values, so that the "which item type property holds the title" problem
is solved once instead of once per agency.
"""

import re

from flask import current_app

_LANG_RE = re.compile(r'^[a-z]{2}$')
"""Crossref and DataCite only accept two letter language codes."""

_DATE_RE = re.compile(r'^(\d{4})(?:-(\d{1,2}))?(?:-(\d{1,2}))?')

_THREE_LETTER_LANGUAGES = {
    'jpn': 'ja', 'eng': 'en', 'fra': 'fr', 'fre': 'fr', 'deu': 'de',
    'ger': 'de', 'zho': 'zh', 'chi': 'zh', 'kor': 'ko', 'spa': 'es',
    'por': 'pt', 'rus': 'ru', 'ita': 'it', 'nld': 'nl', 'dut': 'nl',
}
"""JPCOAR writes ISO 639-2 codes where Crossref wants ISO 639-1."""


class DoiMetadataSource(object):
    """Read only view of one item, expressed in JPCOAR terms."""

    def __init__(self, item_uuid, doi, resource_url, record=None,
                 mapping=None):
        """Load the record and its JPCOAR mapping.

        :param item_uuid: uuid of the item to register
        :param doi: DOI being registered
        :param resource_url: URL the DOI has to resolve to
        :param record: already loaded record, to save a query
        :param mapping: already loaded ``MappingData``, mostly for tests
        """
        from ..utils import MappingData

        self.item_uuid = item_uuid
        self.doi = doi
        self.resource_url = resource_url
        self._mapping = mapping or (
            MappingData(record=record) if record is not None
            else MappingData(item_id=item_uuid))
        self.record = self._mapping.record

    # -- generic accessors ------------------------------------------------

    def property_keys(self, mapping_key):
        """Return the item type properties a JPCOAR key is mapped to.

        :param mapping_key: JPCOAR key, e.g. ``title.@value``
        :return: list of property keys, e.g. ``['item_1617186331708.title']``
        """
        return self._mapping.item_map.get(mapping_key) or []

    def values(self, mapping_key):
        """Return every non empty value mapped to a JPCOAR key.

        :param mapping_key: JPCOAR key, e.g. ``title.@value``
        :return: flat list of values
        """
        data = self._mapping.get_data_by_mapping(mapping_key, True)
        result = []
        for values in data.values():
            for value in values:
                if value not in (None, '', []):
                    result.append(value)
        return result

    def first(self, mapping_key):
        """Return the first non empty value mapped to a JPCOAR key.

        :param mapping_key: JPCOAR key
        :return: the value, or None
        """
        values = self.values(mapping_key)
        return values[0] if values else None

    def pairs(self, value_key, attribute_key):
        """Zip values with the attribute that qualifies them.

        Both keys have to live under the same item type property, which is
        what JPCOAR guarantees for pairs such as title/xml:lang or
        date/dateType.

        :param value_key: JPCOAR key of the value
        :param attribute_key: JPCOAR key of the attribute
        :return: list of ``(value, attribute)`` tuples
        """
        values = self._mapping.get_data_by_mapping(value_key)
        attributes = self._mapping.get_data_by_mapping(attribute_key)
        result = []
        for property_key, value_list in values.items():
            root = property_key.split('.')[0]
            attribute_list = []
            for attribute_property, candidates in attributes.items():
                if attribute_property.split('.')[0] == root:
                    attribute_list = candidates
                    break
            for index, value in enumerate(value_list):
                if value in (None, '', []):
                    continue
                attribute = attribute_list[index] \
                    if index < len(attribute_list) else None
                result.append((value, attribute))
        return result

    def entries(self, mapping_key):
        """Return the repeated sub items a JPCOAR key lives in.

        Used where flattening loses the grouping, typically creators: a
        multilingual record repeats ``creatorName`` per language, so the
        values have to stay attached to the creator they belong to.

        :param mapping_key: JPCOAR key living under the repeated property
        :return: list of ``(entry, sub_path)`` tuples
        """
        keys = self.property_keys(mapping_key)
        if not keys:
            return []
        root = keys[0].split('.')[0]
        sub_path = keys[0].split('.')[1:]
        attribute = self.record.get(root) or {}
        values = attribute.get('attribute_value_mlt') or []
        if isinstance(values, dict):
            values = [values]
        return [(entry, sub_path) for entry in values
                if isinstance(entry, dict)]

    def sub_values(self, entry, mapping_key):
        """Read a JPCOAR key inside one repeated sub item.

        :param entry: sub item returned by :meth:`entries`
        :param mapping_key: JPCOAR key to read
        :return: flat list of values
        """
        from ..utils import get_item_value_in_deep

        result = []
        for property_key in self.property_keys(mapping_key):
            sub_path = property_key.split('.')[1:]
            if not sub_path:
                continue
            for value in get_item_value_in_deep(entry, sub_path) or []:
                if value not in (None, '', []):
                    result.append(value)
        return result

    # -- typed accessors --------------------------------------------------

    def titles(self):
        """Return the titles with their language.

        :return: list of ``(title, language)`` tuples
        """
        pairs = self.pairs('title.@value', 'title.@attributes.xml:lang')
        if pairs:
            return pairs
        return [(value, None) for value in self.values('title.@value')]

    def language(self):
        """Return the language of the record, when usable as is.

        :return: two letter language code, or None
        """
        for value in self.values('language.@value'):
            code = _normalize_language(value)
            if code:
                return code
        languages = [_normalize_language(lang)
                     for dummy_title, lang in self.titles()]
        languages = [code for code in languages if code]
        if 'en' in languages:
            return 'en'
        return languages[0] if languages else None

    def creators(self):
        """Return the creators, one entry per person or organisation.

        Multilingual names collapse to a single name: the English one when
        the record carries it, the first one otherwise.

        :return: list of dicts with ``surname``, ``given``, ``orcid`` and
            ``affiliation`` keys
        """
        creators = []
        for entry, dummy_path in self.entries('creator.creatorName.@value'):
            names = self._sub_pairs(
                entry, 'creator.creatorName.@value',
                'creator.creatorName.@attributes.xml:lang')
            given = self._sub_pairs(
                entry, 'creator.givenName.@value',
                'creator.givenName.@attributes.xml:lang')
            family = self._sub_pairs(
                entry, 'creator.familyName.@value',
                'creator.familyName.@attributes.xml:lang')

            surname = _preferred(family) or _preferred(names)
            if not surname:
                continue
            creator = {
                'surname': surname,
                'given': _preferred(given) if family else None,
                'orcid': self._creator_orcid(entry),
                'affiliation': _first(self.sub_values(
                    entry, 'creator.affiliation.affiliationName.@value')),
            }
            creators.append(creator)
        return creators

    def _sub_pairs(self, entry, value_key, language_key):
        """Zip a creator's names with their language."""
        values = self.sub_values(entry, value_key)
        languages = self.sub_values(entry, language_key)
        return [(value, languages[index] if index < len(languages) else None)
                for index, value in enumerate(values)]

    def _creator_orcid(self, entry):
        """Return the creator's ORCID when the record carries one."""
        identifiers = self.sub_values(
            entry, 'creator.nameIdentifier.@value')
        schemes = self.sub_values(
            entry, 'creator.nameIdentifier.@attributes.nameIdentifierScheme')
        for index, identifier in enumerate(identifiers):
            scheme = schemes[index] if index < len(schemes) else None
            if scheme and str(scheme).upper() == 'ORCID':
                return _as_orcid_url(identifier)
        return None

    def publication_date(self):
        """Return the date the item was made public.

        ``dateType="Issued"`` wins; any other date is used as a fallback so
        that a record is never rejected for the sole lack of a date.

        :return: dict with ``year`` and optionally ``month`` and ``day``
        """
        dates = self.pairs('date.@value',
                           'date.@attributes.dateType')
        for value, date_type in dates:
            if date_type and str(date_type).lower() == 'issued':
                parsed = _parse_date(value)
                if parsed:
                    return parsed
        for value, dummy_type in dates:
            parsed = _parse_date(value)
            if parsed:
                return parsed
        for key in ('publish_date', 'pubdate'):
            parsed = _parse_date(_scalar(self.record.get(key)))
            if parsed:
                return parsed
        return None

    def resource_type(self):
        """Return the JPCOAR resource type of the item.

        :return: resource type, e.g. ``journal article``
        """
        return self.first('type.@value')

    def abstract(self):
        """Return the first description usable as an abstract.

        :return: text, or None
        """
        return self.first('description.@value')

    def publisher(self):
        """Return the publisher of the item.

        :return: publisher name, or None
        """
        return self.first('publisher.@value') \
            or self.first('publisher_jpcoar.publisherName.@value')

    def journal(self):
        """Return the journal the item was published in.

        :return: dict with ``full_title``, ``issn``, ``volume``, ``issue``,
            ``page_start`` and ``page_end`` keys
        """
        issn = None
        for value, identifier_type in self.pairs(
                'sourceIdentifier.@value',
                'sourceIdentifier.@attributes.identifierType'):
            if identifier_type and str(identifier_type).upper() in (
                    'ISSN', 'EISSN', 'PISSN'):
                issn = value
                break
        return {
            'full_title': self.first('sourceTitle.@value'),
            'issn': issn,
            'volume': self.first('volume.@value'),
            'issue': self.first('issue.@value'),
            'page_start': self.first('pageStart.@value'),
            'page_end': self.first('pageEnd.@value'),
        }

    def degree_grantor(self):
        """Return the institution which granted the degree.

        :return: name, or None
        """
        return self.first('degreeGrantor.degreeGrantorName.@value')


def _normalize_language(value):
    """Return a two letter language code, or None when there is none.

    :param value: language as written in the metadata, ``eng`` or ``en``
    :return: two letter code Crossref and DataCite accept
    """
    if not value:
        return None
    code = str(value).strip().lower()
    if _LANG_RE.match(code):
        return code
    return _THREE_LETTER_LANGUAGES.get(code)


def _preferred(pairs):
    """Return the English value of a multilingual list, or the first one."""
    if not pairs:
        return None
    for value, language in pairs:
        if language and str(language).lower().startswith('en'):
            return value
    return pairs[0][0]


def _first(values):
    """Return the first element of a list, or None."""
    return values[0] if values else None


def _scalar(value):
    """Unwrap the one element lists item metadata is full of."""
    if isinstance(value, list):
        return value[0] if value else None
    if isinstance(value, dict):
        return value.get('attribute_value')
    return value


def _as_orcid_url(value):
    """Return an ORCID as the URL form both agencies expect."""
    if not value:
        return None
    value = str(value).strip()
    if value.startswith('http'):
        return value
    return 'https://orcid.org/{0}'.format(value)


def _parse_date(value):
    """Split a JPCOAR date into year, month and day.

    :param value: date string such as ``2026-08-19``
    :return: dict with ``year`` and optionally ``month``/``day``, or None
    """
    if not value:
        return None
    match = _DATE_RE.match(str(value).strip())
    if not match:
        current_app.logger.debug(
            'DOI deposit: unusable date {0}'.format(value))
        return None
    date = {'year': int(match.group(1))}
    if match.group(2):
        date['month'] = int(match.group(2))
    if match.group(3):
        date['day'] = int(match.group(3))
    return date
