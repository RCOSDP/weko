# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Harvest records from an OAI-PMH repository."""

import copy
import re
from collections import OrderedDict
from functools import partial
from json import dumps, loads

import dateutil
import requests
import xmltodict
from lxml import etree
from weko_records.api import Mapping
from weko_records.models import ItemType
from weko_records.serializers.utils import get_mapping
from weko_records.utils import get_options_and_order_list

from .config import OAIHARVESTER_DOI_PREFIX, OAIHARVESTER_HDL_PREFIX, OAIHARVESTER_VERIFY_TLS_CERTIFICATE

DEFAULT_FIELD = [
    'title',
    'keywords',
    'keywords_en',
    'pubdate',
    'lang']

SYSTEM_IDENTIFIER_URI = 'system_identifier_uri'
SYSTEM_IDENTIFIER_HDL = 'system_identifier_hdl'
SYSTEM_IDENTIFIER_DOI = 'system_identifier_doi'
SUBITEM_SYSTEMIDT_IDENTIFIER = 'subitem_systemidt_identifier'
DDI_MAPPING_KEY_TITLE = 'stdyDscr.citation.titlStmt.titl.@value'
DDI_MAPPING_KEY_URI = 'stdyDscr.citation.holdings.@value'


def list_sets(url, encoding='utf-8'):
    """Get sets list."""
    # Avoid SSLError - dh key too small
    requests.packages.urllib3.disable_warnings()
    requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += 'HIGH:!DH:!aNULL'

    sets = []
    payload = {
        'verb': 'ListSets'}
    while True:
        response = requests.get(url, params=payload, verify = OAIHARVESTER_VERIFY_TLS_CERTIFICATE )
        et = etree.XML(response.text.encode(encoding))
        sets = sets + et.findall('./ListSets/set', namespaces=et.nsmap)
        resumptionToken = et.find(
            './ListSets/resumptionToken',
            namespaces=et.nsmap)
        if resumptionToken is not None and resumptionToken.text is not None:
            payload['resumptionToken'] = resumptionToken.text
        else:
            break
    return sets


def list_records(
        url,
        from_date=None,
        until_date=None,
        metadata_prefix=None,
        setspecs='*',
        resumption_token=None,
        encoding='utf-8'):
    """Get records list."""
    # Avoid SSLError - dh key too small
    requests.packages.urllib3.disable_warnings()
    requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += 'HIGH:!DH:!aNULL'

    payload = {
        'verb': 'ListRecords',
        'from': from_date,
        'until': until_date,
        'metadataPrefix': metadata_prefix,
        'set': setspecs}
    if resumption_token:
        payload['resumptionToken'] = resumption_token
    records = []
    rtoken = None
    response = requests.get(url, params=payload, verify = OAIHARVESTER_VERIFY_TLS_CERTIFICATE)
    et = etree.XML(response.text.encode(encoding))
    records = records + et.findall('./ListRecords/record', namespaces=et.nsmap)
    resumptionToken = et.find(
        './ListRecords/resumptionToken',
        namespaces=et.nsmap)
    if resumptionToken is not None:
        rtoken = resumptionToken.text
    return records, rtoken


def map_field(schema):
    """Get field map."""
    res = {}
    for field_name in schema['properties']:
        if field_name not in DEFAULT_FIELD:
            res[schema['properties'][field_name]['title']] = field_name
    return res


def get_newest_itemtype_info(type_name):
    """Get itemtype info."""
    target = None
    for t in ItemType.query.all():
        if t.item_type_name.name == type_name:
            if target is None or target.updated < t.updated:
                target = t
    return target


def add_alternative(schema, res, alternative_list):
    """Add alternative."""
    if not isinstance(alternative_list, list):
        alternative_list = [alternative_list]
    root_key = map_field(schema).get('Alternative Title')
    if not root_key:
        return
    res[root_key] = []
    alternative_title = map_field(schema['properties'][root_key]['items'])[
        'Alternative Title']
    language = map_field(schema['properties'][root_key]['items'])['Language']
    for it in alternative_list:
        item = {}
        if isinstance(it, str):
            item[alternative_title] = it
        elif isinstance(it, OrderedDict):
            item[alternative_title] = it.get('#text')
            item[language] = it.get('@xml:lang')
        res[root_key].append(item)


def add_title(schema, res, title_list):
    """Add title."""
    if not isinstance(title_list, list):
        title_list = [title_list]
    root_key = map_field(schema).get('Title')
    if not root_key:
        return
    res[root_key] = []
    title = map_field(schema['properties'][root_key]['items'])['Title']
    language = map_field(schema['properties'][root_key]['items'])['Language']
    for it in title_list:
        item = {}
        if isinstance(it, str):
            item[title] = it
        elif isinstance(it, OrderedDict):
            item[title] = it.get('#text')
            item[language] = it.get('@xml:lang')
        res[root_key].append(item)
    res['title'] = res[root_key][0][title]


def add_description(schema, res, description_list):
    """Add description."""
    if not isinstance(description_list, list):
        description_list = [description_list]
    root_key = map_field(schema).get('Description')
    if not root_key:
        return
    res[root_key] = []
    description = map_field(schema['properties'][root_key]['items'])[
        'Description']
    description_type = map_field(schema['properties'][root_key]['items'])[
        'Description Type']
    language = map_field(schema['properties'][root_key]['items'])['Language']
    for it in description_list:
        item = {}
        if isinstance(it, str):
            item[description] = it
        elif isinstance(it, OrderedDict):
            item[description] = it.get('#text')
            item[description_type] = \
                it.get('@descriptionType') if it.get(
                    '@descriptionType') else 'Other'
            if it.get('@xml:lang'):
                item[language] = it.get('@xml:lang')
        res[root_key].append(item)


def add_creator_jpcoar(schema, res, creator_list):
    """Add creator."""
    if not isinstance(creator_list, list):
        creator_list = [creator_list]
    root_key = map_field(schema).get('Creator')
    if not root_key:
        return
    res[root_key] = []
    item_schema = schema['properties'][root_key]['items']
    affiliation_key = map_field(item_schema)['Affiliation']
    creator_alternative_key = map_field(item_schema)['Creator Alternative']
    creator_name_key = map_field(item_schema)['Creator Name']
    creator_name_identifier_key = map_field(
        item_schema)['Creator Name Identifier']
    family_name_key = map_field(item_schema)['Family Name']
    given_name_key = map_field(item_schema)['Given Name']
    affiliation_name = map_field(
        item_schema['properties'][affiliation_key]['items'])
    ['Affiliation Name']
    affiliation_name_identifier = map_field(
        item_schema['properties'][affiliation_key]['items'])
    ['Affiliation Name Identifier']
    creator_name = map_field(
        item_schema['properties'][creator_name_key]['items'])['Creator Name']
    creator_name_lang = map_field(
        item_schema['properties'][creator_name_key]['items'])['Language']
    item = {}
    for it in creator_list:
        if 'jpcoar:creatorName' in it:
            item[creator_name_key] = []
            if not isinstance(it['jpcoar:creatorName'], list):
                names = [it['jpcoar:creatorName']]
            else:
                names = it['jpcoar:creatorName']
            for name in names:
                if isinstance(name, str):
                    item[creator_name_key].append({creator_name: name})
                elif isinstance(name, OrderedDict):
                    item[creator_name_key].append({
                        creator_name: name.get('#text'),
                        creator_name_lang: name.get('@xml:lang')})
        res[root_key].append(item)


def add_contributor_jpcoar(schema, res, contributor_list):
    """Add contributor."""
    if not isinstance(contributor_list, list):
        contributor_list = [contributor_list]
    root_key = map_field(schema).get('Contributor')
    if not root_key:
        return
    res[root_key] = []
    item_schema = schema['properties'][root_key]['items']
    affiliation_key = map_field(item_schema)['Affiliation']
    contributor_alternative_key = map_field(
        item_schema)['Contributor Alternative']
    contributor_name_key = map_field(item_schema)['Contributor Name']
    contributor_name_identifier_key = map_field(
        item_schema)['Contributor Name Identifier']
    family_name_key = map_field(item_schema)['Family Name']
    given_name_key = map_field(item_schema)['Given Name']
    affiliation_name = map_field(
        item_schema['properties'][affiliation_key]['items'])
    ['Affiliation Name']
    affiliation_name_identifier = map_field(
        item_schema['properties'][affiliation_key]['items'])
    ['Affiliation Name Identifier']
    contributor_name = map_field(
        item_schema['properties'][contributor_name_key]['items'])
    ['Contributor Name']
    contributor_name_lang = map_field(
        item_schema['properties'][contributor_name_key]['items'])['Language']
    item = {}
    for it in contributor_list:
        if 'jpcoar:contributorName' in it:
            item[contributor_name_key] = []
            if not isinstance(it['jpcoar:contributorName'], list):
                names = [it['jpcoar:contributorName']]
            else:
                names = it['jpcoar:contributorName']
            for name in names:
                if isinstance(name, str):
                    item[contributor_name_key].append({contributor_name: name})
                elif isinstance(name, OrderedDict):
                    item[contributor_name_key].append({
                        contributor_name: name.get('#text'),
                        contributor_name_lang: name.get('@xml:lang')})
        res[root_key].append(item)


def add_access_rights(schema, res, accessRights):
    """Add access rights."""
    root_key = map_field(schema).get('Access Rights')
    access_rights = map_field(
        schema['properties'][root_key])['Access Rights']
    access_rights_resource = map_field(
        schema['properties'][root_key])['Access Rights Resource']
    res[root_key] = {
        access_rights: accessRights.get('#text'),
        access_rights_resource: accessRights.get('@rdf:resource')}


def add_rights(schema, res, rights_list):
    """Add rights."""
    if not isinstance(rights_list, list):
        rights_list = [rights_list]
    root_key = map_field(schema).get('Rights')
    res[root_key] = []
    rights = map_field(
        schema['properties'][root_key]['items'])['Rights']
    rights_text = map_field(
        schema['properties'][root_key]['items']['properties'][rights]
        ['items'])['Rights']
    rights_lang = map_field(
        schema['properties'][root_key]['items']['properties'][rights]
        ['items'])['Language']
    rights_resource = map_field(
        schema['properties'][root_key]['items'])['Rights Resource']
    for it in rights_list:
        item = {}
        item[rights] = {}
        if isinstance(it, str):
            item[rights][rights_text] = it
        elif isinstance(it, OrderedDict):
            item[rights][rights_text] = it.get('#text')
            if it.get('@xml:lang'):
                item[rights][rights_lang] = it.get('@xml:lang')
            item[rights_resource] = it.get('@rdf:resource')
        res[root_key].append(item)


def add_rightsholder(schema, res, rightsholder_list):
    """Add rightsholder."""
    if not isinstance(rights_list, list):
        rightsholder_list = [rightsholder_list]
    root_key = map_field(schema).get('Rights Holder')
    res[root_key] = []
    rights_holder_name_key = map_field(
        sch['properties'][root_key]['items'])['Rights Holder Name']
    rights_holder_identifier_key = map_field(
        sch['properties'][root_key]['items'])['Rights Holder Identifier']


def add_subject(schema, res, subject_list):
    """Add subject."""
    if not isinstance(subject_list, list):
        subject_list = [subject_list]
    root_key = map_field(schema).get('Subject')
    res[root_key] = []
    subject = map_field(
        schema['properties'][root_key]['items'])['Subject']
    subject_uri = map_field(
        schema['properties'][root_key]['items'])['Subject URI']
    subject_scheme = map_field(
        schema['properties'][root_key]['items'])['Subject Scheme']
    language = map_field(
        schema['properties'][root_key]['items'])['Language']
    for it in subject_list:
        item = {}
        if isinstance(it, str):
            item[subject] = it
        elif isinstance(it, OrderedDict):
            item[subject] = it.get('#text')
            if it.get('@subjectScheme'):
                item[subject_scheme] = it.get('@subjectScheme')
            if it.get('@subjectURI'):
                item[subject_uri] = it.get('@subjectURI')
            if it.get('@xml:lang'):
                item[language] = it.get('@xml:lang')
        res[root_key].append(item)


def add_publisher(schema, res, publisher_list):
    """Add publisher."""
    if not isinstance(publisher_list, list):
        publisher_list = [publisher_list]
    root_key = map_field(schema).get('Publisher')
    if not root_key:
        return
    res[root_key] = []
    publisher = map_field(schema['properties'][root_key]['items'])['Publisher']
    language = map_field(schema['properties'][root_key]['items'])['Language']
    for it in publisher_list:
        item = {}
        if isinstance(it, str):
            item[publisher] = it
        elif isinstance(it, OrderedDict):
            item[publisher] = it.get('#text')
            item[language] = it.get('@xml:lang')
        res[root_key].append(item)


def add_identifier(schema, res, identifier_list):
    """Add identfier."""
    if not isinstance(identifier_list, list):
        identifier_list = [identifier_list]
    for it in identifier_list:
        item = dict(
            identifier=None,
            type=None
        )
        if isinstance(it, str):
            item['identifier'] = it
        elif isinstance(it, OrderedDict):
            item['identifier'] = it.get('#text')
            if it.get('@identifierType'):
                item['type'] = it.get('@identifierType')
        res.append(item)


def add_identifier_registration(schema, res, identifierRegistration):
    """Add identfier registration."""
    root_key = map_field(schema).get('Identifier Registration')
    identifier_registration = map_field(
        schema['properties'][root_key])['Identifier Registration']
    identifier_registration_type = map_field(
        schema['properties'][root_key])['Identifier Registration Type']
    res[root_key] = {
        identifier_registration: identifierRegistration.get('#text'),
        identifier_registration_type: identifierRegistration.get(
            '@identifierType')}


def add_date(schema, res, date_list):
    """Add date."""
    if not isinstance(date_list, list):
        date_list = [date_list]
    root_key = map_field(schema).get('Date')
    res[root_key] = []
    date = map_field(
        schema['properties'][root_key]['items'])['Date']
    date_type = map_field(
        schema['properties'][root_key]['items'])['Date Type']
    for it in date_list:
        item = {}
        if isinstance(it, str):
            item[date] = it
        elif isinstance(it, OrderedDict):
            item[date] = it.get('#text')
            if it.get('@dateType'):
                item[date_type] = it.get('@dateType')
        res[root_key].append(item)


def add_language(schema, res, language_list):
    """Add language."""
    if not isinstance(language_list, list):
        language_list = [language_list]
    root_key = map_field(schema).get('Language')
    res[root_key] = []
    language = map_field(schema['properties'][root_key]['items'])['Language']
    for it in language_list:
        if 'lang' not in res:
            res['lang'] = it
        res[root_key].append({language: it})


def add_temporal(schema, res, temporal_list):
    """Add temporal."""
    if not isinstance(temporal_list, list):
        temporal_list = [temporal_list]
    root_key = map_field(schema).get('Temporal')
    if not root_key:
        return
    res[root_key] = []
    temporal = map_field(schema['properties'][root_key]['items'])['Temporal']
    language = map_field(schema['properties'][root_key]['items'])['Language']
    for it in temporal_list:
        item = {}
        if isinstance(it, str):
            item[temporal] = it
        elif isinstance(it, OrderedDict):
            item[temporal] = it.get('#text')
            item[language] = it.get('@xml:lang')
        res[root_key].append(item)


def add_file(schema, res, file_list):
    """Add file."""
    if not isinstance(file_list, list):
        file_list = [file_list]
    root_key = map_field(schema).get('File')
    res[root_key] = []
    uri_key = map_field(schema['properties'][root_key]['items'])['URI']
    uri_schema = \
        schema['properties'][root_key]['items']['properties'][uri_key]['items']
    uri = map_field(uri_schema)['URI']
    uri_label = map_field(uri_schema)['URI Label']
    uri_object_type = map_field(uri_schema)['URI Object Type']
    for it in file_list:
        item = {}
        if 'jpcoar:URI' in it:
            uri_item = {}
            if it['jpcoar:URI'].get('#text'):
                uri_item[uri] = it['jpcoar:URI'].get('#text')
            if it['jpcoar:URI'].get('@label'):
                uri_item[uri_label] = it['jpcoar:URI'].get('@label')
            if it['jpcoar:URI'].get('@objectType'):
                uri_item[uri_object_type] = it['jpcoar:URI'].get('@objectType')
            item[uri_key] = [uri_item]
        res[root_key].append(item)


def add_apc(schema, res, rioxxtermsapc):
    """Add apc."""
    root_key = map_field(schema).get('APC')
    apc = map_field(schema['properties'][root_key])['APC']
    res[root_key] = {apc: rioxxtermsapc}


def add_source_title(schema, res, source_title_list):
    """Add source title."""
    if not isinstance(source_title_list, list):
        source_title_list = [source_title_list]
    root_key = map_field(schema).get('Source Title')
    if not root_key:
        return
    res[root_key] = []
    source_title = map_field(schema['properties'][root_key]['items'])[
        'Source Title']
    language = map_field(schema['properties'][root_key]['items'])['Language']
    for it in source_title_list:
        item = {}
        if isinstance(it, str):
            item[source_title] = it
        elif isinstance(it, OrderedDict):
            item[source_title] = it.get('#text')
            item[language] = it.get('@xml:lang')
        res[root_key].append(item)


def add_source_identifier(schema, res, source_identifier_list):
    """Add source identifier."""
    if not isinstance(source_identifier_list, list):
        source_identifier_list = [source_identifier_list]
    root_key = map_field(schema).get('Source Identifier')
    res[root_key] = []
    source_identifier = map_field(
        schema['properties'][root_key]['items'])['Source Identifier']
    source_identifier_type = map_field(
        schema['properties'][root_key]['items'])['Source Identifier Type']
    for it in source_identifier_list:
        item = {}
        if isinstance(it, str):
            item[identifie] = it
        elif isinstance(it, OrderedDict):
            item[source_identifier] = it.get('#text')
            if it.get('@identifierType'):
                item[source_identifier_type] = it.get('@identifierType')
        res[root_key].append(item)


def add_volume(schema, res, jpcoarvolume):
    """Add volume."""
    root_key = map_field(schema).get('Volume Number')
    volume_number = map_field(schema['properties'][root_key])['Volume Number']
    res[root_key] = {volume_number: jpcoarvolume}


def add_issue(schema, res, jpcoarissue):
    """Add issue."""
    root_key = map_field(schema).get('Issue Number')
    issue_number = map_field(schema['properties'][root_key])['Issue Number']
    res[root_key] = {issue_number: jpcoarissue}


def add_num_pages(schema, res, numPages):
    """Add num pages."""
    root_key = map_field(schema).get('Number of Pages')
    number_of_pages = map_field(schema['properties'][root_key])[
        'Number of Pages']
    res[root_key] = {number_of_pages: numPages}


def add_page_start(schema, res, pageStart):
    """Add page start."""
    root_key = map_field(schema).get('Page Start')
    page_start = map_field(schema['properties'][root_key])['Page Start']
    res[root_key] = {page_start: pageStart}


def add_page_end(schema, res, pageEnd):
    """Add page end."""
    root_key = map_field(schema).get('Page End')
    page_end = map_field(schema['properties'][root_key])['Page End']
    res[root_key] = {page_end: pageEnd}


def add_dissertation_number(schema, res, dissertationNumber):
    """Add dissertation number."""
    root_key = map_field(schema).get('Dissertation Number')
    dissertation_number = map_field(schema['properties'][root_key])[
        'Dissertation Number']
    res[root_key] = {dessertation_number: dissertationNumber}


def add_degree_name(schema, res, degree_name_list):
    """Add degree name."""
    if not isinstance(degree_name_list, list):
        degree_name_list = [degree_name_list]
    root_key = map_field(schema).get('Degree Name')
    if not root_key:
        return
    res[root_key] = []
    degree_name = map_field(
        schema['properties'][root_key]['items'])['Degree Name']
    language = map_field(schema['properties'][root_key]['items'])['Language']
    for it in degree_name_list:
        item = {}
        if isinstance(it, str):
            item[degree_name] = it
        elif isinstance(it, OrderedDict):
            item[degree_name] = it.get('#text')
            item[language] = it.get('@xml:lang')
        res[root_key].append(item)


def add_date_granted(schema, res, dateGranted):
    """Add date granted."""
    root_key = map_field(schema).get('Date Granted')
    date_granted = map_field(schema['properties'][root_key])['Date Granted']
    res[root_key] = {date_granted: dateGranted}


def add_version(schema, res, dataciteVersion):
    """Add version."""
    root_key = map_field(schema).get('Version')
    version = map_field(schema['properties'][root_key])['Version']
    res[root_key] = {version: dateciteVersion}


def add_version_type(schema, res, oaireVersion):
    """Add version type."""
    root_key = map_field(schema).get('Version Type')
    version_type = map_field(schema['properties'][root_key])['Version Type']
    if isinstance(oaireVersion, str):
        res[root_key] = {version_type: oaireVersion}
    elif isinstance(oaireVersion, OrderedDict):
        res[root_key] = {version_type: oaireVersion.get('#text')}


def add_geo_location(schema, res, geoLocation_list):
    """Add geo location."""
    if not isinstance(geoLocation_list, list):
        geoLocation_list = [geoLocation_list]
    root_key = map_field(schema).get('Geo Location')


def add_creator_dc(schema, res, creator_name, lang=''):
    """Add creator."""
    creator_field = map_field(schema)['Creator']
    subitems = map_field(schema['properties'][creator_field]['items'])
    creator_name_array_name = subitems['Creator Name']
    creator_name_array_subitems = \
        map_field(schema['properties'][creator_field]['items']
                  ['properties'][creator_name_array_name]['items'])
    item = {subitems['Creator Name']: {
        creator_name_array_subitems['Creator Name']: creator_name,
        creator_name_array_subitems['Language']: lang}}
    if creator_field not in res:
        res[creator_field] = []
    res[creator_field].append(item)


def add_data_by_key(schema, res, resource_list, key):
    """Add data by parent key.

    :param schema:
    :param res:
    :param resource_list:
    :param key:
    :return:
    """
    if not isinstance(resource_list, list):
        resource_list = [resource_list]
    root_key = map_field(schema).get(key)
    if not root_key:
        return
    if not res.get(root_key):
        res[root_key] = []
    temporal = map_field(schema['properties'][root_key]['items'])[key]
    language = map_field(schema['properties'][root_key]['items'])['Language']
    for it in resource_list:
        item = {}
        if isinstance(it, str):
            item[temporal] = it
        elif isinstance(it, OrderedDict):
            item[temporal] = it.get('#text')
            item[language] = it.get('@xml:lang')
        res[root_key].append(item)


def add_source_dc(schema, res, source_list):
    """Add description."""
    add_data_by_key(schema, res, source_list, 'Description')


def add_coverage_dc(schema, res, coverage_list):
    """Add temporal."""
    add_data_by_key(schema, res, coverage_list, 'Temporal')


def add_format_dc(schema, res, file_list):
    """Add file."""
    if not isinstance(file_list, list):
        file_list = [file_list]
    root_key = map_field(schema).get('File')
    if not res.get(root_key):
        res[root_key] = []
    format_key = map_field(schema['properties'][root_key]['items'])['Format']
    for it in file_list:
        item = {}
        if isinstance(it, str):
            item[format_key] = it
        elif isinstance(it, OrderedDict):
            item[format_key] = it.get('#text')
        res[root_key].append(item)


def add_contributor_dc(schema, res, contributor_name, lang=''):
    """Add contributor."""
    contributor_field = map_field(schema)['Contributor']
    subitems = map_field(schema['properties'][contributor_field]['items'])
    contributor_name_array_name = subitems['Contributor Name']
    contributor_name_array_subitems = \
        map_field(schema['properties'][contributor_field]['items']
                  ['properties'][contributor_name_array_name]['items'])
    item = {subitems['Affiliation']: [],
            subitems['Contributor Alternative']: [],
            subitems['Contributor Name Identifier']: [],
            subitems['Family Name']: [],
            subitems['Given Name']: [],
            subitems['Contributor Name']: {
                contributor_name_array_subitems['Contributor Name']:
                    contributor_name,
                contributor_name_array_subitems['Language']: lang}}
    if contributor_field not in res:
        res[contributor_field] = []
    res[contributor_field].append(item)


def add_relation_dc(schema, res, relation, relation_type=''):
    """Add relation."""
    relation_field = map_field(schema)['Relation']
    subitems = map_field(schema['properties'][relation_field]['items'])
    related_identifier_array_name = subitems['Related Identifier']
    related_identifier_array_subitems = \
        map_field(schema['properties'][relation_field]['items']
                  ['properties'][related_identifier_array_name]['items'])
    related_title_array_name = subitems['Related Title']
    related_title_array_subitems = \
        map_field(schema['properties'][relation_field]['items']
                  ['properties'][related_title_array_name]['items'])
    item = {subitems['Relation']: relation,
            subitems['Relation Type']: relation_type,
            subitems['Related Identifier']: {
                related_identifier_array_subitems['Related Identifier']: '',
                related_identifier_array_subitems['Related Identifier Type']:
                    ''},
            subitems['Related Title']: {
                related_title_array_subitems['Related Title']: '',
                related_title_array_subitems['Language']: ''}}
    if relation_field not in res:
        res[relation_field] = []
    res[relation_field].append(item)


def add_rights_dc(schema, res, rights, lang='', rights_resource=''):
    """Add rights."""
    rights_field = map_field(schema)['Rights']
    subitems = map_field(schema['properties'][rights_field]['items'])
    rights_array_name = subitems['Rights']
    rights_array_subitems = \
        map_field(schema['properties'][rights_field]['items']
                  ['properties'][rights_array_name]['items'])
    item = {subitems['Rights Resource']: rights_resource,
            subitems['Rights']: {
                rights_array_subitems['Rights']: rights,
                rights_array_subitems['Language']: lang}}
    if rights_field not in res:
        res[rights_field] = []
    res[rights_field].append(item)


def add_identifier_dc(schema, res, self_identifier, identifier):
    """Add identifier."""
    self_identifier.clear()
    if identifier.startswith(OAIHARVESTER_DOI_PREFIX):
        self_identifier.append({'type': 'DOI', 'identifier': identifier})
    elif identifier.startswith(OAIHARVESTER_HDL_PREFIX):
        self_identifier.append({'type': 'HDL', 'identifier': identifier})
    else:
        res['system_identifier_doi'] = []
        res['system_identifier_doi'].append(
            {'subitem_systemidt_identifier': identifier})


def add_description_dc(schema, res, description, description_type='', lang=''):
    """Add description."""
    description_field = map_field(schema)['Description']
    subitems = map_field(schema['properties'][description_field]['items'])
    description_item_name = subitems['Description']
    description_type_item_name = subitems['Description Type']
    language_item_name = subitems['Language']
    if description_field not in res:
        res[description_field] = []
    res[description_field].append({
        description_item_name: description,
        description_type_item_name: description_type,
        language_item_name: lang})


def add_subject_dc(schema, res, subject, subject_uri='',
                   subject_scheme='', lang=''):
    """Add subject."""
    subject_field = map_field(schema)['Subject']
    subitems = map_field(schema['properties'][subject_field]['items'])
    subject_item_name = subitems['Subject']
    subject_uri_item_name = subitems['Subject URI']
    subject_scheme_item_name = subitems['Subject Scheme']
    language_item_name = subitems['Language']
    if subject_field not in res:
        res[subject_field] = []
    res[subject_field].append({
        subject_item_name: subject,
        subject_uri_item_name: subject_uri,
        subject_scheme_item_name: subject_scheme,
        language_item_name: lang})


def add_title_dc(schema, res, title, lang=''):
    """Add title."""
    #    if 'title_en' not in res:
    #        res['title_en'] = title
    if 'title' not in res:
        res['title'] = title
    title_field = map_field(schema)['Title']
    subitems = map_field(schema['properties'][title_field]['items'])
    title_item_name = subitems['Title']
    language_item_name = subitems['Language']
    if title_field not in res:
        res[title_field] = []
    res[title_field].append({title_item_name: title, language_item_name: lang})


def add_language_dc(schema, res, lang):
    """Add language."""
    if 'lang' not in res:
        res['lang'] = lang
    language_field = map_field(schema)['Language']
    subitems = map_field(schema['properties'][language_field]['items'])
    language_item_name = subitems['Language']
    if language_field not in res:
        res[language_field] = []
    res[language_field].append({language_item_name: lang})


def add_date_dc(schema, res, date, date_type=''):
    """Add date."""
    date_field = map_field(schema)['Date']
    subitems = map_field(schema['properties'][date_field]['items'])
    date_item_name = subitems['Date']
    date_type_item_name = subitems['Date Type']
    if date_field not in res:
        res[date_field] = []
    res[date_field].append(
        {date_item_name: date, date_type_item_name: date_type})


def add_publisher_dc(schema, res, publisher, lang=''):
    """Add publisher."""
    publisher_field = map_field(schema)['Publisher']
    subitems = map_field(schema['properties'][publisher_field]['items'])
    publisher_item_name = subitems['Publisher']
    language_item_name = subitems['Language']
    if publisher_field not in res:
        res[publisher_field] = []
    res[publisher_field].append(
        {publisher_item_name: publisher, language_item_name: lang})


def add_resource_type_dc(schema, res, dc_type):
    """Add publisher."""
    resource_type_field = map_field(schema)['Resource Type']
    subitems = map_field(schema['properties'][resource_type_field])
    type_item = subitems['Type']
    resource_item = subitems['Resource']
    if resource_type_field not in res:
        res[resource_type_field] = []
    res[resource_type_field].append(
        {type_item: dc_type, resource_item: RESOURCE_TYPE_URI.get(dc_type,
                                                                  '')})


def to_dict(input_ordered_dict):
    """Convert OrderDict to Dict."""
    return loads(dumps(input_ordered_dict))


RESOURCE_TYPE_MAP = {
    'conference paper': 'Article',
    'data paper': 'Article',
    'departmental bulletin paper': 'Article',
    'editorial': 'Article',
    'journal article': 'Article',
    'periodical': 'Article',
    'review article': 'Article',
    'article': 'Article',
    'Book': 'Book',
    'book part': 'Book',
    'cartographic material': 'Cartographic Material',
    'map': 'Cartographic Material',
    'conference object': 'Conference Object',
    'conference proceedings': 'Conference Object',
    'conference poster': 'Conference Object',
    'presentation': 'Conference Object',
    'dataset': 'Dataset',
    'image': 'Image',
    'still image': 'Image',
    'moving image': 'Image',
    'video': 'Image',
    'lecture': 'Lecture',
    'patent': 'Patent',
    'internal report': 'Report',
    'report': 'Report',
    'research report': 'Report',
    'technical report': 'Report',
    'policy report': 'Report',
    'report part': 'Report',
    'working paper': 'Report',
    'research paper': 'Report',
    'sound': 'Sound',
    'thesis': 'Thesis',
    'bachelor thesis': 'Thesis',
    'master thesis': 'Thesis',
    'doctoral thesis': 'Thesis',
    'thesis or dissertation': 'Thesis',
    'interactive resource': 'Multiple',
    'learning material': 'Multiple',
    'musical notation': 'Multiple',
    'research proposal': 'Multiple',
    'software': 'Multiple',
    'technical documentation': 'Multiple',
    'workflow': 'Multiple',
    'other': 'Multiple',
}

RESOURCE_TYPE_URI = {
    'interactive resource':
        "http://purl.org/coar/resource_type/c_e9a0",
    'learning material':
        "http://purl.org/coar/resource_type/c_1843",
    'musical notation':
        "http://purl.org/coar/resource_type/c_18cw",
    'research proposal':
        "http://purl.org/coar/resource_type/c_baaf",
    'software':
        "http://purl.org/coar/resource_type/c_5ce6",
    'technical documentation':
        "http://purl.org/coar/resource_type/c_71bd",
    'workflow':
        "http://purl.org/coar/resource_type/c_393c",
    'other（その他）':
        "http://purl.org/coar/resource_type/c_1843",
    'other（プレプリント）':
        "",
    'conference object':
        "http://purl.org/coar/resource_type/c_c94f",
    'conference proceedings':
        "http://purl.org/coar/resource_type/c_f744",
    'conference poster':
        "http://purl.org/coar/resource_type/c_6670",
    'patent':
        "http://purl.org/coar/resource_type/c_15cd",
    'lecture':
        "http://purl.org/coar/resource_type/c_8544",
    'book':
        "http://purl.org/coar/resource_type/c_2f33",
    'book part':
        "http://purl.org/coar/resource_type/c_3248",
    'dataset':
        "http://purl.org/coar/resource_type/c_ddb1",
    'conference paper':
        "http://purl.org/coar/resource_type/c_5794",
    'data paper':
        "http://purl.org/coar/resource_type/c_beb9",
    'departmental bulletin paper':
        "http://purl.org/coar/resource_type/c_6501",
    'editorial':
        "http://purl.org/coar/resource_type/c_b239",
    'journal article':
        "http://purl.org/coar/resource_type/c_6501",
    'periodical':
        "http://purl.org/coar/resource_type/c_2659",
    'review article':
        "http://purl.org/coar/resource_type/c_dcae04bc",
    'article':
        "http://purl.org/coar/resource_type/c_6501",
    'image':
        "http://purl.org/coar/resource_type/c_c513",
    'still image':
        "http://purl.org/coar/resource_type/c_ecc8",
    'moving image':
        "http://purl.org/coar/resource_type/c_8a7e",
    'video':
        "http://purl.org/coar/resource_type/c_12ce",
    'cartographic material':
        "http://purl.org/coar/resource_type/c_12cc",
    'map':
        "http://purl.org/coar/resource_type/c_12cd",
    'sound':
        "http://purl.org/coar/resource_type/c_18cc",
    'internal report':
        "http://purl.org/coar/resource_type/c_18ww",
    'report':
        "http://purl.org/coar/resource_type/c_93fc",
    'research report':
        "http://purl.org/coar/resource_type/c_18ws",
    'technical report':
        "http://purl.org/coar/resource_type/c_18gh",
    'policy report':
        "http://purl.org/coar/resource_type/c_186u",
    'report part':
        "http://purl.org/coar/resource_type/c_ba1f",
    'working paper':
        "http://purl.org/coar/resource_type/c_8042",
    'thesis':
        "http://purl.org/coar/resource_type/c_46ec",
    'bachelor thesis':
        "http://purl.org/coar/resource_type/c_7a1f",
    'master thesis':
        "http://purl.org/coar/resource_type/c_bdcc",
    'doctoral thesis':
        "http://purl.org/coar/resource_type/c_db06"
}


def map_sets(sets, encoding='utf-8'):
    """Get sets map."""
    res = OrderedDict()
    pattern = '<setSpec>(.+)</setSpec><setName>(.+)</setName>'
    for s in sets:
        xml = etree.tostring(s, encoding=encoding).decode()
        m = re.search(pattern, xml)
        spec = m.group(1)
        name = m.group(2)
        if spec and name:
            res[spec] = name
    return res


class BaseMapper:
    """BaseMapper."""

    itemtype_map = {}
    identifiers = []

    @classmethod
    def update_itemtype_map(cls):
        """Update itemtype map."""
        for t in ItemType.query.all():
            cls.itemtype_map[t.item_type_name.name] = t

    def __init__(self, xml):
        """Init."""
        self.xml = xml
        self.json = xmltodict.parse(xml)
        if not BaseMapper.itemtype_map:
            BaseMapper.update_itemtype_map()
        self.itemtype = BaseMapper.itemtype_map['Multiple']

    def is_deleted(self):
        """Check deleted."""
        return self.json['record']['header'].get('@status') == 'deleted'

    def identifier(self):
        """Get identifier."""
        return self.json['record']['header'].get('identifier')

    def datestamp(self):
        """Get datestamp."""
        datestring = self.json['record']['header'].get('datestamp')
        return dateutil.parser.parse(datestring).date()

    def specs(self):
        """Get specs."""
        s = self.json['record']['header'].get('setSpec')
        return s if isinstance(s, list) else [s]

    def map_itemtype(self, type_tag):
        """Map itemtype."""
        types = self.json['record']['metadata'][type_tag].get('dc:type')
        if types is None:
            return
        types = types if isinstance(types, list) else [types]
        for t in types:
            if type(t) == OrderedDict:
                t = t['#text']
            if t.lower() in RESOURCE_TYPE_MAP:
                self.itemtype \
                    = BaseMapper.itemtype_map[RESOURCE_TYPE_MAP[t.lower()]]
                break


class DCMapper(BaseMapper):
    """DC Mapper."""

    def __init__(self, xml):
        """Init."""
        super().__init__(xml)

    def map(self):
        """Get map."""
        if self.is_deleted():
            return {}
        self.map_itemtype('oai_dc:dc')
        res = {'$schema': self.itemtype.id,
               'pubdate': str(self.datestamp())}
        dc_tags = {
            'title': [], 'creator': [], 'contributor': [], 'rights': [],
            'subject': [], 'description': [], 'publisher': [], 'date': [],
            'type': [], 'format': [], 'identifier': [], 'source': [],
            'language': [], 'relation': [], 'coverage': []}
        add_funcs = {
            'creator': partial(add_creator_dc, self.itemtype.schema, res),
            'contributor': partial(add_contributor_dc, self.itemtype.schema,
                                   res),
            'title': partial(add_title_dc, self.itemtype.schema, res),
            'subject': partial(add_subject_dc, self.itemtype.schema, res),
            'description': partial(add_description_dc, self.itemtype.schema,
                                   res),
            'publisher': partial(add_publisher_dc, self.itemtype.schema, res),
            'type': partial(add_resource_type_dc, self.itemtype.schema, res),
            'date': partial(add_date_dc, self.itemtype.schema, res),
            'identifier': partial(add_identifier_dc, self.itemtype.schema, res,
                                  self.identifiers),
            'language': partial(add_language_dc, self.itemtype.schema, res),
            'relation': partial(add_relation_dc, self.itemtype.schema, res),
            'rights': partial(add_rights_dc, self.itemtype.schema, res),
            'coverage': partial(add_coverage_dc, self.itemtype.schema, res),
            'source': partial(add_description_dc, self.itemtype.schema, res),
            'format': partial(add_format_dc, self.itemtype.schema, res)
        }
        for tag in dc_tags:
            if tag in add_funcs:
                m = '<dc:{0}.*>(.+?)</dc:{0}>'.format(tag)
                dc_tags[tag] = re.findall(m, self.xml)
                for value in dc_tags[tag]:
                    add_funcs[tag](value)
        return res


class JPCOARMapper(BaseMapper):
    """JPCOARMapper."""

    def __init__(self, xml):
        """Init."""
        super().__init__(xml)

    def map(self):
        """Get map."""
        if self.is_deleted():
            return {}
        self.map_itemtype('jpcoar:jpcoar')
        self.identifiers = []
        res = {'$schema': self.itemtype.id,
               'pubdate': str(self.datestamp())}
        add_funcs = {
            'dc:title': partial(add_title, self.itemtype.schema, res),
            'dcterms:alternative': partial(add_alternative,
                                           self.itemtype.schema, res),
            'jpcoar:creator': partial(
                add_creator_jpcoar,
                self.itemtype.schema,
                res
            ),
            'jpcoar:contributor': partial(add_contributor_jpcoar,
                                          self.itemtype.schema, res),
            'dcterms:accessRights': partial(add_access_rights,
                                            self.itemtype.schema, res),
            'rioxxterms:apc': partial(add_apc, self.itemtype.schema, res),
            'dc:rights': partial(add_rights, self.itemtype.schema, res),
            #            'jpcoar:rightsHolder' : ,
            'jpcoar:subject': partial(add_subject, self.itemtype.schema, res),
            'datacite:description': partial(add_description,
                                            self.itemtype.schema, res),
            'dc:publisher': partial(add_publisher, self.itemtype.schema, res),
            'datacite:date': partial(add_date, self.itemtype.schema, res),
            'dc:language': partial(add_language, self.itemtype.schema, res),
            'datacite:version': partial(
                add_version,
                self.itemtype.schema,
                res
            ),
            'oaire:version': partial(add_version_type, self.itemtype.schema,
                                     res),
            'jpcoar:identifier': partial(add_identifier,
                                         None,
                                         self.identifiers),
            'jpcoar:identifierRegistration': partial(
                add_identifier_registration, self.itemtype.schema, res),
            #            'jpcoar:relation' : ,
            'dcterms:temporal': partial(add_temporal, self.itemtype.schema,
                                        res),
            #            'datacite:geoLocation' : ,
            #            'jpcoar:fundingReference' : ,
            'jpcoar:sourceIdentifier': partial(add_source_identifier,
                                               self.itemtype.schema, res),
            'jpcoar:sourceTitle': partial(add_source_title,
                                          self.itemtype.schema, res),
            'jpcoar:volume': partial(add_volume, self.itemtype.schema, res),
            'jpcoar:issue': partial(add_issue, self.itemtype.schema, res),
            'jpcoar:numPages': partial(
                add_num_pages,
                self.itemtype.schema,
                res
            ),
            'jpcoar:pageStart': partial(
                add_page_start,
                self.itemtype.schema,
                res
            ),
            'jpcoar:pageEnd': partial(
                add_page_end,
                self.itemtype.schema,
                res
            ),
            'dcndl:dissertationNumber': partial(
                add_dissertation_number,
                self.itemtype.schema,
                res
            ),
            'dcndl:dateGranted': partial(
                add_date_granted,
                self.itemtype.schema,
                res
            ),
            #            'jpcoar:degreeGrantor' : ,
            #            'jpcoar:conference' : ,
            'jpcoar:file': partial(add_file, self.itemtype.schema, res),
        }
        for tag in self.json['record']['metadata']['jpcoar:jpcoar']:
            if tag in add_funcs:
                add_funcs[tag](
                    self.json['record']['metadata']['jpcoar:jpcoar'][tag])
        return res


class DDIMapper(BaseMapper):
    """DDIMapper."""

    def __init__(self, xml):
        """Init."""
        super().__init__(xml)
        self.record_title = ""

    def ddi_harvest_processing(self, harvest_data, res):
        """Process parsing DDI data."""
        def get_mapping_ddi():
            """Get DDI mapping."""
            item_type_id = self.itemtype.id
            type_mapping = Mapping.get_record(item_type_id)
            item_map = get_mapping(type_mapping, "ddi_mapping")
            lst_keys_x = list(item_map.keys())
            for i in lst_keys_x:
                lst_keys.append(i)
                lst_keys_unique.add(i.split(".@")[0])
            return item_map

        def merge_dict(result, target, val, keys):
            """Merge all value has same parent key to a result object."""
            if not result:
                result.update(target)
                return
            current_temp = result
            last_key = keys[-1]
            for i in keys:
                i_r = i.replace("[]", "")
                if str(last_key) == str(i):
                    if not current_temp.get(i_r):
                        if "[]" in i:
                            current_temp[i_r] = []
                        else:
                            current_temp[i_r] = {}
                    if isinstance(current_temp[i_r], dict):
                        current_temp[i_r].update(val)
                    elif isinstance(current_temp[i_r], list):
                        if current_temp[i_r]:
                            current_temp[i_r][0].update(val)
                        else:
                            current_temp[i_r].append(val)
                    break
                elif i_r in current_temp:
                    current_temp = current_temp[i_r]
                    target = target[i_r]
                    if isinstance(current_temp, list):
                        current_temp = current_temp[0]
                        target = target[0]
                elif i_r not in current_temp:
                    current_temp[i_r] = [] if '[]' in i else {}
                    if isinstance(current_temp[i_r], list):
                        current_temp[i_r] = target[i_r]
                    else:
                        current_temp[i_r].update(target[i_r])
                    break
            return result

        def merge_data_by_mapping_keys(parent_key, data_mapping):
            """Merge all sub data by parent key(prefix key)."""
            current_key = parent_key
            if current_key in lst_keys_unique:
                if dict_data.get(current_key):
                    dict_data[current_key].append(data_mapping)
                else:
                    dict_data[current_key] = [data_mapping]
            if isinstance(data_mapping, dict):
                for key, val in data_mapping.items():
                    full_key = current_key + '.' + key
                    if full_key in lst_keys_unique:
                        if isinstance(val, str):
                            val = {'#text': val}
                        elif isinstance(val, list):
                            for i in range(len(val)):
                                if isinstance(val[i], str):
                                    val[i] = {'#text': val[i]}

                        if dict_data.get(full_key):
                            if isinstance(val, list):
                                dict_data[full_key].extend(val)
                            else:
                                dict_data[full_key].append(val)
                        else:
                            if isinstance(val, list):
                                dict_data[full_key] = val
                            else:
                                dict_data[full_key] = [val]
                    else:
                        merge_data_by_mapping_keys(full_key, val)
            elif isinstance(data_mapping, list):
                for data in data_mapping:
                    merge_data_by_mapping_keys(parent_key, data)
            elif isinstance(data_mapping, str) and '@' not in current_key:
                data_mapping = {'#text': data_mapping}
                if dict_data.get(current_key):
                    dict_data[current_key].append(data_mapping)
                else:
                    dict_data[current_key] = [data_mapping]

        def parse_to_obj_data_by_mapping_keys(vals, keys):
            """Parse all data to type of object by mapping key."""
            def get_same_key_from_form(sub_key):
                """Get the same key with sub_key in form."""
                for item_sub_key_form in item_sub_keys_form:
                    if item_sub_key_form.replace("[]", "") == sub_key:
                        sub_key = item_sub_key_form
                        break
                return sub_key

            def parse_each_obj(parse_data):
                """Parse data for each item."""
                full_key_val_obj = {last_key: parse_data}
                while sub_keys:
                    current_key = sub_keys.pop()
                    if '[]' in current_key:
                        full_key_val_obj = {
                            current_key.replace("[]", ""):
                                [full_key_val_obj]}
                    else:
                        full_key_val_obj = {
                            current_key: full_key_val_obj}
                temp_lst.append(
                    {"full": full_key_val_obj,
                     "key": sub_keys_clone,
                     "val": {last_key: parse_data}})

            try:
                list_result = []
                root_key = ''
                for val_obj in vals:
                    temp_lst = []
                    for key_pair in keys:
                        for mapping_key, item_sub_key in key_pair.items():
                            item_sub_key = get_same_key_from_form(item_sub_key)
                            sub_keys = item_sub_key.split('.')
                            root_key = sub_keys[0]
                            last_key = sub_keys.pop()
                            sub_keys_clone = copy.deepcopy(sub_keys)
                            if mapping_key.split(".@")[1] == "value":
                                if val_obj.get('#text'):
                                    value = val_obj['#text']
                                    if mapping_key == DDI_MAPPING_KEY_TITLE:
                                        self.record_title = value
                                    if mapping_key == DDI_MAPPING_KEY_URI:
                                        handle_identifier(value)
                                    parse_each_obj(value)
                            elif 'attributes' in mapping_key.split(".@")[1]:
                                att = mapping_key.split(".")[-1]
                                if val_obj.get('@' + att):
                                    att = val_obj['@' + att]
                                    parse_each_obj(att)
                    result_dict = {}
                    for temp_obj in temp_lst:
                        merge_dict(result_dict, temp_obj['full'],
                                   temp_obj['val'], temp_obj['key'])
                    if result_dict:
                        if isinstance(result_dict[root_key.replace("[]", "")],
                                      list):
                            list_result.append(
                                result_dict[root_key.replace("[]", "")][0])
                        elif isinstance(result_dict[root_key.replace("[]", "")],
                                        dict):
                            list_result.append(
                                result_dict[root_key.replace("[]", "")])
                return list_result, root_key.replace("[]", "")
            except Exception:
                import traceback
                traceback.print_exc()

        def get_all_key(prefix):
            """Get all keys with the prefix key."""
            result = []
            for i in lst_keys:
                if i.startswith(prefix):
                    result.append({i: item_mapping[i]})
            return result

        def convert_to_lst(src_lst):
            """Unify all to data to type of list."""
            result = []
            for i in src_lst:
                if isinstance(i, list):
                    result.extend(i)
                else:
                    result.append(i)
            return result

        def get_all_keys_forms():
            """Get all keys current item type forms."""
            all_keys, _ = get_options_and_order_list(self.itemtype.id)
            all_keys_result = []
            for i in all_keys:
                all_keys_result.append(i[0])
            return all_keys_result

        def handle_identifier(identifier):
            """Handel Identifiers."""
            if identifier.startswith(OAIHARVESTER_DOI_PREFIX):
                self.identifiers.append({'type': 'DOI',
                                         'identifier': identifier})
            elif identifier.startswith(OAIHARVESTER_HDL_PREFIX):
                self.identifiers.append({'type': 'HDL', 'identifier':
                                        identifier})

        lst_keys = []
        harvest_data = to_dict(harvest_data)
        lst_keys_unique = set()
        item_mapping = get_mapping_ddi()
        dict_data = {}
        item_sub_keys_form = get_all_keys_forms()
        # Convert harvest data to simple dict data by mapping keys
        for k, v in harvest_data.items():
            if isinstance(v, dict):
                merge_data_by_mapping_keys(k, v)
        for k, v in dict_data.items():
            lst_keys_with_prefix = get_all_key(k)
            if not lst_keys_with_prefix:
                continue
            lst_parsed, first_key = parse_to_obj_data_by_mapping_keys(
                convert_to_lst(v), lst_keys_with_prefix)
            if lst_parsed:
                if not res.get(first_key):
                    res[first_key] = lst_parsed
                else:
                    res[first_key].extend(lst_parsed)

    def map_itemtype(self, type_tag):
        """Map itemtype."""
        self.itemtype = BaseMapper.itemtype_map['Harvesting DDI']

    def map(self):
        """Get map."""
        if self.is_deleted():
            return {}
        self.map_itemtype('codeBook')
        res = {'$schema': self.itemtype.id,
               'pubdate': str(self.datestamp())}
        if self.json['record']['metadata']['codeBook']:
            self.ddi_harvest_processing(self.json['record']
                                        ['metadata']['codeBook'], res)
            res['title'] = self.record_title
            return res
