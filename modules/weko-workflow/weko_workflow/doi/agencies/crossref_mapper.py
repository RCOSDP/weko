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

"""Build a Crossref deposit from JPCOAR item metadata.

The element order of every record type follows the Crossref metadata input
schema; reordering the calls below breaks the deposit even though the values
are unchanged.
"""

import re
import time
import xml.etree.ElementTree as ElementTree

from flask import current_app

CROSSREF_NS = 'http://www.crossref.org/schema/5.4.0'
JATS_NS = 'http://www.ncbi.nlm.nih.gov/JATS1'
XSI_NS = 'http://www.w3.org/2001/XMLSchema-instance'

JOURNAL_ARTICLE_TYPES = (
    'conference paper', 'data paper', 'departmental bulletin paper',
    'editorial', 'journal', 'journal article', 'review article', 'article',
    'newspaper', 'software paper', 'periodical',
)
"""JPCOAR resource types Crossref registers as ``journal_article``."""

THESIS_TYPES = (
    'thesis', 'bachelor thesis', 'master thesis', 'doctoral thesis',
)
"""JPCOAR resource types Crossref registers as a dissertation."""

XML_DECLARATION = '<?xml version="1.0" encoding="UTF-8"?>\n'
"""Crossref expects the deposited file to declare its encoding."""

_ITEM_NUMBER_MAX_LENGTH = 32
"""Crossref rejects an ``item_number`` longer than this."""


def _register_namespaces():
    """Keep the generated prefixes stable and readable."""
    ElementTree.register_namespace('', CROSSREF_NS)
    ElementTree.register_namespace('jats', JATS_NS)
    ElementTree.register_namespace('xsi', XSI_NS)


def _element(parent, tag, text=None, namespace=CROSSREF_NS, **attributes):
    """Append a namespaced child element."""
    child = ElementTree.SubElement(parent, '{{{0}}}{1}'.format(namespace, tag))
    if text is not None:
        child.text = str(text)
    for name, value in attributes.items():
        if value is not None:
            child.set(name, str(value))
    return child


def _add_date(parent, tag, date, **attributes):
    """Append a Crossref ``date_t`` element (month, day, then year)."""
    if not date:
        return None
    element = _element(parent, tag, **attributes)
    if date.get('month'):
        _element(element, 'month', '{0:02d}'.format(int(date['month'])))
    if date.get('day'):
        _element(element, 'day', '{0:02d}'.format(int(date['day'])))
    _element(element, 'year', '{0:04d}'.format(int(date['year'])))
    return element


def normalize_item_number(value):
    """Fit an item uuid into Crossref's 32 character ``item_number``.

    :param value: item uuid
    :return: alphanumeric value of at most 32 characters
    """
    return re.sub(r'[^0-9A-Za-z]', '', str(value))[:_ITEM_NUMBER_MAX_LENGTH]


def choose_record_type(source):
    """Decide which Crossref record type the item is deposited as.

    ``WEKO_CROSSREF_RECORD_TYPE_POLICY`` selects between depositing
    everything as ``posted_content`` -- which keeps the mapping small -- and
    following the resource type.

    :param source: a :class:`~weko_workflow.doi.metadata.DoiMetadataSource`
    :return: ``journal_article`` or ``posted_content``
    """
    policy = current_app.config.get(
        'WEKO_CROSSREF_RECORD_TYPE_POLICY', 'posted_content')
    if policy != 'auto':
        return 'posted_content'

    resource_type = (source.resource_type() or '').lower()
    if resource_type in JOURNAL_ARTICLE_TYPES \
            and source.journal().get('full_title'):
        return 'journal_article'
    return 'posted_content'


def posted_content_type(source):
    """Return the ``posted_content/@type`` the resource type maps to."""
    resource_type = (source.resource_type() or '').lower()
    if resource_type in THESIS_TYPES:
        return 'dissertation'
    return 'other'


def build_doi_batch(source, batch_id):
    """Build the whole Crossref deposit for one item.

    :param source: a :class:`~weko_workflow.doi.metadata.DoiMetadataSource`
    :param batch_id: value of ``doi_batch_id``
    :return: ``(xml, record_type)``
    """
    _register_namespaces()
    root = ElementTree.Element(
        '{{{0}}}doi_batch'.format(CROSSREF_NS), {'version': '5.4.0'})
    root.set(
        '{{{0}}}schemaLocation'.format(XSI_NS),
        '{0} https://www.crossref.org/schemas/crossref5.4.0.xsd'.format(
            CROSSREF_NS))

    _build_head(root, batch_id)
    body = ElementTree.SubElement(root, '{{{0}}}body'.format(CROSSREF_NS))

    record_type = choose_record_type(source)
    if record_type == 'journal_article':
        _build_journal(body, source)
    else:
        _build_posted_content(body, source)

    # ElementTree only emits the declaration for some encodings, and the
    # attribute order differs between Python versions; write the declaration
    # ourselves so that the payload is the same everywhere.
    xml = XML_DECLARATION + ElementTree.tostring(
        root, encoding='unicode')
    return xml, record_type


def _build_head(root, batch_id):
    """Build the ``head`` element out of the depositor settings."""
    head = ElementTree.SubElement(root, '{{{0}}}head'.format(CROSSREF_NS))
    _element(head, 'doi_batch_id', batch_id)
    _element(head, 'timestamp', time.strftime('%Y%m%d%H%M%S') + '000')
    depositor = _element(head, 'depositor')
    _element(depositor, 'depositor_name',
             current_app.config.get('WEKO_CROSSREF_DEPOSITOR_NAME'))
    _element(depositor, 'email_address',
             current_app.config.get('WEKO_CROSSREF_DEPOSITOR_EMAIL'))
    _element(head, 'registrant',
             current_app.config.get('WEKO_CROSSREF_REGISTRANT'))


def _build_contributors(parent, source):
    """Build the ``contributors`` element, first author first."""
    creators = source.creators()
    if not creators:
        return
    contributors = _element(parent, 'contributors')
    for index, creator in enumerate(creators):
        person = _element(
            contributors, 'person_name',
            sequence='first' if index == 0 else 'additional',
            contributor_role='author')
        if creator.get('given'):
            _element(person, 'given_name', creator['given'])
        _element(person, 'surname', creator['surname'])
        if creator.get('affiliation'):
            affiliations = _element(person, 'affiliations')
            institution = _element(affiliations, 'institution')
            _element(institution, 'institution_name', creator['affiliation'])
        if creator.get('orcid'):
            _element(person, 'ORCID', creator['orcid'])


def _build_titles(parent, source):
    """Build the ``titles`` element out of the multilingual JPCOAR titles."""
    titles = source.titles()
    primary = None
    original = None
    for title, language in titles:
        if language and str(language).lower().startswith('en'):
            primary = (title, language)
            break
    if primary is None and titles:
        primary = titles[0]
    for title, language in titles:
        if primary and title != primary[0]:
            original = (title, language)
            break

    element = _element(parent, 'titles')
    _element(element, 'title', primary[0] if primary else '')
    if original:
        _element(element, 'original_language_title', original[0],
                 language=_language_attribute(original[1]))


def _language_attribute(value):
    """Return a language code Crossref accepts, or None."""
    if not value:
        return None
    code = str(value).strip().lower()
    return code if re.match(r'^[a-z]{2}$', code) else None


def _build_abstract(parent, source):
    """Build the JATS abstract element."""
    abstract = source.abstract()
    if not abstract:
        return
    element = _element(parent, 'abstract', namespace=JATS_NS)
    _element(element, 'p', abstract, namespace=JATS_NS)


def _build_doi_data(parent, source):
    """Build the ``doi_data`` element, the only mandatory part."""
    doi_data = _element(parent, 'doi_data')
    _element(doi_data, 'doi', source.doi)
    _element(doi_data, 'resource', source.resource_url)


def _build_posted_content(body, source):
    """Build a ``posted_content`` record."""
    posted_content = _element(
        body, 'posted_content', type=posted_content_type(source),
        language=source.language())
    _build_contributors(posted_content, source)
    _build_titles(posted_content, source)
    _add_date(posted_content, 'posted_date', source.publication_date())

    institution_name = source.degree_grantor() or source.publisher()
    if institution_name:
        institution = _element(posted_content, 'institution')
        _element(institution, 'institution_name', institution_name)

    _element(posted_content, 'item_number',
             normalize_item_number(source.item_uuid),
             item_number_type='uuid')
    _build_abstract(posted_content, source)
    _build_doi_data(posted_content, source)


def _build_journal(body, source):
    """Build a ``journal`` record holding a single ``journal_article``."""
    journal_data = source.journal()
    journal = _element(body, 'journal')

    metadata = _element(journal, 'journal_metadata')
    _element(metadata, 'full_title', journal_data.get('full_title'))
    if journal_data.get('issn'):
        _element(metadata, 'issn', _normalize_issn(journal_data['issn']),
                 media_type='electronic')

    publication_date = source.publication_date()
    issue = _element(journal, 'journal_issue')
    _add_date(issue, 'publication_date', publication_date,
              media_type='online')
    if journal_data.get('volume'):
        volume = _element(issue, 'journal_volume')
        _element(volume, 'volume', journal_data['volume'])
    if journal_data.get('issue'):
        _element(issue, 'issue', journal_data['issue'])

    article = _element(journal, 'journal_article',
                       publication_type='full_text',
                       language=source.language())
    _build_titles(article, source)
    _build_contributors(article, source)
    _build_abstract(article, source)
    _add_date(article, 'publication_date', publication_date,
              media_type='online')
    if journal_data.get('page_start'):
        pages = _element(article, 'pages')
        _element(pages, 'first_page', journal_data['page_start'])
        if journal_data.get('page_end'):
            _element(pages, 'last_page', journal_data['page_end'])
    _build_doi_data(article, source)


def _normalize_issn(value):
    """Return an ISSN in the ``NNNN-NNNX`` form Crossref expects."""
    digits = re.sub(r'[^0-9Xx]', '', str(value)).upper()
    if len(digits) == 8:
        return '{0}-{1}'.format(digits[:4], digits[4:])
    return str(value).strip()
