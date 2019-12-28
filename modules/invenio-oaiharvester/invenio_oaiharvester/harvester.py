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

import re
from collections import OrderedDict
from functools import partial
from flask import current_app

import dateutil
import requests
import xmltodict
from celery import shared_task
from invenio_db import db
from lxml import etree
from weko_deposit.api import WekoDeposit
from weko_records.models import ItemType
from json import loads, dumps
from collections import OrderedDict
from .models import HarvestSettings

DEFAULT_FIELD = [
    'title',
    'keywords',
    'keywords_en',
    'pubdate',
    'lang']


def list_sets(url, encoding='utf-8'):
    """Get sets list."""
    # Avoid SSLError - dh key too small
    requests.packages.urllib3.disable_warnings()
    requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += 'HIGH:!DH:!aNULL'

    sets = []
    payload = {
        'verb': 'ListSets'}
    while True:
        response = requests.get(url, params=payload)
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
    response = requests.get(url, params=payload)
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
        item_schema['properties'][affiliation_key]['items'])['Affiliation Name']
    affiliation_name_identifier = map_field(
        item_schema['properties'][affiliation_key]['items'])['Affiliation Name Identifier']
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
        item_schema['properties'][affiliation_key]['items'])['Affiliation Name']
    affiliation_name_identifier = map_field(
        item_schema['properties'][affiliation_key]['items'])['Affiliation Name Identifier']
    contributor_name = map_field(
        item_schema['properties'][contributor_name_key]['items'])['Contributor Name']
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
        schema['properties'][root_key]['items']['properties'][rights]['items'])['Rights']
    rights_lang = map_field(
        schema['properties'][root_key]['items']['properties'][rights]['items'])['Language']
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
    root_key = map_field(schema).get('Identifier')
    res[root_key] = []
    identifier = map_field(
        schema['properties'][root_key]['items'])['Identifier']
    identifier_type = map_field(
        schema['properties'][root_key]['items'])['Identifier Type']
    for it in identifier_list:
        item = {}
        if isinstance(it, str):
            item[identifier] = it
        elif isinstance(it, OrderedDict):
            item[identifier] = it.get('#text')
            if it.get('@identifierType'):
                item[identifier_type] = it.get('@identifierType')
        res[root_key].append(item)


def add_identifier_registration(schema, res, identifierRegistration):
    """Add identfier registration."""
    root_key = map_field(schema).get('Identifier Registration')
    identifier_registration = map_field(
        schema['properties'][root_key])['Identifier Registration']
    identifier_registration_type = map_field(
        schema['properties'][root_key])['Identifier Registration Type']
    res[root_key] = {
        identifier_registration: identifierRegistration.get('#text'),
        identifier_registration_type: identifierRegistration.get('@identifierType')}


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
                contributor_name_array_subitems['Contributor Name']: contributor_name,
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
                related_identifier_array_subitems['Related Identifier Type']: ''},
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


def add_identifier_dc(schema, res, identifier, identifier_type=''):
    """Add identifier."""
    identifier_field = map_field(schema)['Identifier']
    subitems = map_field(schema['properties'][identifier_field]['items'])
    identifier_item_name = subitems['Identifier']
    identifier_type_item_name = subitems['Identifier Type']
    if identifier_field not in res:
        res[identifier_field] = []
    res[identifier_field].append(
        {identifier_item_name: identifier, identifier_type_item_name: identifier_type})


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


def add_titlStmt_ddi(schema, res, list_stdyDscr):
    if isinstance(list_stdyDscr, list):
        for i in list_stdyDscr:
            if isinstance(i, OrderedDict):
                add_titlStmt_ddi(schema, res, i)
    elif isinstance(list_stdyDscr, OrderedDict):
        for k, v in list_stdyDscr.items():
            if isinstance(v, OrderedDict):
                if k == 'titlStmt':
                    for k1, v1 in v.items():
                        if k1 == 'titl':
                            add_title_ddi(schema, res, v1)
                        elif k1 == 'altTitl':
                            add_alternative_title_ddi(schema, res, v1)
                else:
                    add_titlStmt_ddi(schema, res, v)


def add_title_ddi(schema, res, titl):
    title = 'Title'
    root_key = map_field(schema).get(title)
    # if not root_key:
    #     return
    res[root_key] = []
    # item = {}
    title_sub = map_field(schema['properties'][root_key]['items'])[title]
    # language = map_field(schema['properties'][root_key]['items'])['Language']
    # for k,v in titl.items():
    #     if k == '@xml:lang':
    #         item[language] = v
    #     elif k == '#text':
    #         item[title] = v
    item = add_medium_ddi(schema, titl, title)

    res[root_key].append(item)
    res['title'] = res[root_key][0][title_sub]


def add_alternative_title_ddi(schema, res, altTitl):
    alternative_title = 'Alternative Title'
    root_key = map_field(schema).get(alternative_title)
    # if not root_key:
    #     return
    res[root_key] = []
    # item = {}
    # title = map_field(schema['properties'][root_key]['items'])['Alternative Title']
    # language = map_field(schema['properties'][root_key]['items'])['Language']
    # for k,v in altTitl.items():
    #     if k == '@xml:lang':
    #         item[language] = v
    #     elif k == '#text':
    #         item[title] = v
    item = add_medium_ddi(schema, altTitl, alternative_title)
    res[root_key].append(item)


def add_medium_ddi(schema, altTitl, key):
    root_key = map_field(schema).get(key)
    if not root_key:
        return
    # res[root_key] = []
    item = {}
    title = map_field(schema['properties'][root_key]['items'])[key]
    language = map_field(schema['properties'][root_key]['items']).get(
        'Language')
    for k, v in altTitl.items():
        if k == '@xml:lang':
            item[language] = v
        elif k == '#text':
            item[title] = v
    return item


def add_rspStmt_ddi(schema, res, list_stdyDscr):
    if isinstance(list_stdyDscr, list):
        for i in list_stdyDscr:
            if isinstance(i, OrderedDict):
                add_rspStmt_ddi(schema, res, i)
    elif isinstance(list_stdyDscr, OrderedDict):
        for k, v in list_stdyDscr.items():
            if isinstance(v, OrderedDict):
                if k == 'rspStmt':
                    for k1, v1 in v.items():
                        if k1 == 'AuthEnty':
                            add_creator_ddi(schema, res, v1)
                else:
                    add_rspStmt_ddi(schema, res, v)


def add_creator_ddi(schema, res, authEnty):
    root_key = map_field(schema).get('Creator')
    if not root_key:
        return
    item_schema = schema['properties'][root_key]['items']
    creator_name_identifier_parent = map_field(item_schema)[
        'Creator Name Identifier']
    creator_name_identifier_child = map_field(
        item_schema['properties'][creator_name_identifier_parent]['items'])[
        'Creator Name Identifier']
    creator_name_parent = map_field(item_schema)['Creator Name']
    creator_name_child = \
    map_field(item_schema['properties'][creator_name_parent]['items'])[
        'Creator Name']
    affiliation = map_field(item_schema)['Affiliation']
    item_schema_affiliation = item_schema['properties'][affiliation]['items']
    affiliation_name_parent = map_field(item_schema_affiliation)[
        'Affiliation Name']
    affiliation_name_child = map_field(
        item_schema_affiliation['properties'][affiliation_name_parent][
            'items'])['Affiliation Name']
    res[root_key] = []
    item = {}
    for k, v in authEnty.items():
        if k == '#text':
            item[creator_name_parent] = {}
            item[creator_name_parent][creator_name_child] = v
        elif k == '@ID':
            item[creator_name_identifier_parent] = {}
            item[creator_name_identifier_parent][
                creator_name_identifier_child] = v
        elif k == '@affiliation':
            item[affiliation] = {}
            item[affiliation][affiliation_name_parent] = {}
            item[affiliation][affiliation_name_parent][
                affiliation_name_child] = v
    res[root_key].append(item)


def add_prodStmt_ddi(schema, res, list_stdyDscr):
    if isinstance(list_stdyDscr, list):
        for i in list_stdyDscr:
            if isinstance(i, OrderedDict):
                add_prodStmt_ddi(schema, res, i)
    elif isinstance(list_stdyDscr, OrderedDict):
        for k, v in list_stdyDscr.items():
            if isinstance(v, OrderedDict):
                if k == 'prodStmt':
                    for k1, v1 in v.items():
                        if k1 == 'producer':
                            add_publisher_ddi(schema, res, v1)
                        elif k1 == 'copyright':
                            add_rights_ddi(schema, res, v1)
                        elif k1 == 'prodDate':
                            add_date_ddi(schema, res, v1)
                        elif k1 == 'fundAg':
                            add_funderName_ddi(schema, res, v1)
                        elif k1 == 'grantNo':
                            add_awardNumber_ddi(schema, res, v1)
                else:
                    add_prodStmt_ddi(schema, res, v)


def add_publisher_ddi(schema, res, producer):
    publisher = 'Publisher'
    root_key = map_field(schema).get(publisher)
    res[root_key] = []
    item = add_medium_ddi(schema, producer, publisher)
    res[root_key].append(item)


def add_rights_ddi(schema, res, rights):
    root_key = map_field(schema).get('Rights')
    if not root_key:
        return
    item_chema = schema['properties'][root_key]['items']
    rights_parent = map_field(item_chema)['Rights']
    rights_child = map_field(item_chema['properties'][rights_parent]['items'])[
        'Rights']
    res[root_key] = []
    item = {}
    for k, v in rights.items():
        if k == '#text':
            item[rights_parent] = {}
            item[rights_parent][rights_child] = v
    res[root_key].append(item)


def add_date_ddi(schema, res, prodDate):
    root_key = map_field(schema).get('Date')
    if not root_key:
        return
    item_chema = schema['properties'][root_key]['items']
    date = map_field(item_chema)['Date']
    res[root_key] = []
    item = {}
    if prodDate:
        item[date] = prodDate
    res[root_key].append(item)


def add_funderName_ddi(schema, res, fundAg):
    root_key = map_field(schema).get('Funding Reference')
    if not root_key:
        return
    item_schema_funder = schema['properties'][root_key]['items']
    funder_name_parent = map_field(item_schema_funder)['Funder Name']
    funder_name_child = \
    map_field(item_schema_funder['properties'][funder_name_parent]['items'])[
        'Funder Name']
    funder_identifier_parent = map_field(item_schema_funder)[
        'Funder Identifier']
    funder_identifier_child = map_field(
        item_schema_funder['properties'][funder_identifier_parent]['items'])[
        'Funder Identifier']
    res[root_key] = []
    item = {}
    for k, v in fundAg.items():
        if k == '#text':
            item[funder_name_parent] = {}
            item[funder_name_parent][funder_name_child] = v
        if k == '@ID':
            item[funder_identifier_parent] = {}
            item[funder_identifier_parent][funder_identifier_child] = v
    res[root_key].append(item)


def add_awardNumber_ddi(schema, res, grantNo):
    pass


def add_stdyDscr_ddi(schema, res, list_stdyDscr):
    if not isinstance(list_stdyDscr, list):
        list_stdyDscr = [list_stdyDscr]
    add_titlStmt_ddi(schema, res, list_stdyDscr)
    add_rspStmt_ddi(schema, res, list_stdyDscr)
    add_prodStmt_ddi(schema, res, list_stdyDscr)
    add_topic_ddi(schema, res, list_stdyDscr)
    add_version_ddi(schema, res, list_stdyDscr)
    add_summary_ddi(schema, res, list_stdyDscr)
    add_time_period_ddi(schema, res, list_stdyDscr)
    add_uri_ddi(schema, res, list_stdyDscr)
    add_geographic_ddi(schema, res, list_stdyDscr)


# function by Viet Huynh
def to_dict(input_ordered_dict):
    """Convert OrderDict to Dict."""
    return loads(dumps(input_ordered_dict))


def add_topic_ddi(schema, res, list_stdy_dscr):
    """Convert Topic to item metadata."""
    if isinstance(list_stdy_dscr, list):
        for i in list_stdy_dscr:
            if isinstance(i, OrderedDict):
                add_topic_ddi(schema, res, i)
    elif isinstance(list_stdy_dscr, OrderedDict):
        for k, v in list_stdy_dscr.items():
            if isinstance(v, OrderedDict):
                if k == 'stdyInfo':
                    for k1, v1 in v.items():
                        if k1 == 'subject':
                            for k2, v2 in v1.items():
                                if k2 == 'topcClas':
                                    subject = 'Subject'
                                    root_key = map_field(schema).get(subject)
                                    res[root_key] = []
                                    item = add_medium_ddi(schema, v2, subject)
                                    res[root_key].append(item)


def add_version_ddi(schema, res, list_stdy_dscr):
    """Convert Version to item metadata."""
    if isinstance(list_stdy_dscr, list):
        for i in list_stdy_dscr:
            if isinstance(i, OrderedDict):
                add_version_ddi(schema, res, i)
    elif isinstance(list_stdy_dscr, OrderedDict):
        data = to_dict(list_stdy_dscr)
        if data.get("citation"):
            citation = data.get("citation")
            if citation.get("verStmt"):
                verstmt = citation.get("verStmt")
                if verstmt.get('version'):
                    version_value = verstmt.get('version')
                    version = 'Version'
                    root_key = map_field(schema).get(version)
                    res[root_key] = []
                    term = map_field(
                        schema['properties'][root_key])[version]
                    item = dict()
                    item[term] = version_value
                    res[root_key].append(item)


def add_summary_ddi(schema, res, list_stdy_dscr):
    """Convert Description to item metadata."""
    if isinstance(list_stdy_dscr, list):
        for i in list_stdy_dscr:
            if isinstance(i, OrderedDict):
                add_summary_ddi(schema, res, i)
    elif isinstance(list_stdy_dscr, OrderedDict):
        data = to_dict(list_stdy_dscr)
        if data.get("stdyInfo"):
            stdy_info = data.get("stdyInfo")
            if stdy_info.get("abstract"):
                abstract = stdy_info.get("abstract")
                if abstract:
                    summary = 'Description'
                    root_key = map_field(schema).get(summary)
                    res[root_key] = []
                    item = add_medium_ddi(schema, abstract, summary)
                    res[root_key].append(item)


def add_time_period_ddi(schema, res, list_stdy_dscr):
    """Convert Temporal to item metadata."""
    if isinstance(list_stdy_dscr, list):
        for i in list_stdy_dscr:
            if isinstance(i, OrderedDict):
                add_time_period_ddi(schema, res, i)
    elif isinstance(list_stdy_dscr, OrderedDict):
        data = to_dict(list_stdy_dscr)
        if data.get("stdyInfo"):
            stdy_info = data.get("stdyInfo")
            if stdy_info.get("sumDscr"):
                sum_dscr = stdy_info.get("sumDscr")
                if sum_dscr.get('timePrd'):
                    temporal_value = sum_dscr.get('timePrd')
                    temporal = 'Temporal'
                    root_key = map_field(schema).get(temporal)
                    res[root_key] = []
                    term = dict(**{
                        "#text": temporal_value
                    })
                    item = add_medium_ddi(schema, term, temporal)
                    res[root_key].append(item)


def add_uri_ddi(schema, res, list_stdy_dscr):
    """Convert Identifier to item metadata."""
    if isinstance(list_stdy_dscr, list):
        for i in list_stdy_dscr:
            if isinstance(i, OrderedDict):
                add_uri_ddi(schema, res, i)
    elif isinstance(list_stdy_dscr, OrderedDict):
        data = to_dict(list_stdy_dscr)
        if data.get("citation"):
            citation = data.get("citation")
            if citation.get("holdings"):
                holdings = citation.get("holdings")
                identifier = 'Identifier'
                root_key = map_field(schema).get(identifier)
                res[root_key] = []
                item = dict()
                title = map_field(schema['properties'][root_key]['items']).get(
                    identifier)
                item[title] = holdings
                res[root_key].append(item)


def add_geographic_ddi(schema, res, list_stdy_dscr):
    """Convert Geo Location Place to item metadata."""
    if isinstance(list_stdy_dscr, list):
        for i in list_stdy_dscr:
            if isinstance(i, OrderedDict):
                add_geographic_ddi(schema, res, i)
    elif isinstance(list_stdy_dscr, OrderedDict):
        data = to_dict(list_stdy_dscr)
        if data.get("stdyInfo"):
            stdy_info = data.get("stdyInfo")
            if stdy_info.get("sumDscr"):
                sum_dscr = stdy_info.get("sumDscr")
                if sum_dscr.get("geogCover"):
                    geo_grap = sum_dscr.get("geogCover")
                    geo_location = 'Geo Location'
                    geo_location_place = 'Geo Location Place'
                    root_key = map_field(schema).get(geo_location)
                    res[root_key] = []
                    nested_key_1 = map_field(schema['properties'][root_key][
                        'items']).get(geo_location_place)
                    nested_key_2 = map_field(schema['properties'][root_key][
                        'items']['properties'][nested_key_1]['items']).get(
                        geo_location_place
                    )
                    item = dict(**{
                        nested_key_1: [
                            {
                                nested_key_2: geo_grap
                            }
                        ]
                    })
                    res[root_key].append(item)
# function by Viet Huynh


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
            'contributor': partial(add_contributor_dc, self.itemtype.schema, res),
            'title': partial(add_title_dc, self.itemtype.schema, res),
            'subject': partial(add_subject_dc, self.itemtype.schema, res),
            'description': partial(add_description_dc, self.itemtype.schema, res),
            'publisher': partial(add_publisher_dc, self.itemtype.schema, res),
            'date': partial(add_date_dc, self.itemtype.schema, res),
            'identifier': partial(add_identifier_dc, self.itemtype.schema, res),
            'language': partial(add_language_dc, self.itemtype.schema, res),
            'relation': partial(add_relation_dc, self.itemtype.schema, res),
            'rights': partial(add_rights_dc, self.itemtype.schema, res)}
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
        res = {'$schema': self.itemtype.id,
               'pubdate': str(self.datestamp())}
        add_funcs = {
            'dc:title': partial(add_title, self.itemtype.schema, res),
            'dcterms:alternative': partial(add_alternative, self.itemtype.schema, res),
            'jpcoar:creator': partial(add_creator_jpcoar, self.itemtype.schema, res),
            'jpcoar:contributor': partial(add_contributor_jpcoar, self.itemtype.schema, res),
            'dcterms:accessRights': partial(add_access_rights, self.itemtype.schema, res),
            'rioxxterms:apc': partial(add_apc, self.itemtype.schema, res),
            'dc:rights': partial(add_rights, self.itemtype.schema, res),
            #            'jpcoar:rightsHolder' : ,
            'jpcoar:subject': partial(add_subject, self.itemtype.schema, res),
            'datacite:description': partial(add_description, self.itemtype.schema, res),
            'dc:publisher': partial(add_publisher, self.itemtype.schema, res),
            'datacite:date': partial(add_date, self.itemtype.schema, res),
            'dc:language': partial(add_language, self.itemtype.schema, res),
            'datacite:version': partial(add_version, self.itemtype.schema, res),
            'oaire:version': partial(add_version_type, self.itemtype.schema, res),
            'jpcoar:identifier': partial(add_identifier, self.itemtype.schema, res),
            'jpcoar:identifierRegistration': partial(add_identifier_registration, self.itemtype.schema, res),
            #            'jpcoar:relation' : ,
            'dcterms:temporal': partial(add_temporal, self.itemtype.schema, res),
            #            'datacite:geoLocation' : ,
            #            'jpcoar:fundingReference' : ,
            'jpcoar:sourceIdentifier': partial(add_source_identifier, self.itemtype.schema, res),
            'jpcoar:sourceTitle': partial(add_source_title, self.itemtype.schema, res),
            'jpcoar:volume': partial(add_volume, self.itemtype.schema, res),
            'jpcoar:issue': partial(add_issue, self.itemtype.schema, res),
            'jpcoar:numPages': partial(add_num_pages, self.itemtype.schema, res),
            'jpcoar:pageStart': partial(add_page_start, self.itemtype.schema, res),
            'jpcoar:pageEnd': partial(add_page_end, self.itemtype.schema, res),
            'dcndl:dissertationNumber': partial(add_dissertation_number, self.itemtype.schema, res),
            'dcndl:dateGranted': partial(add_date_granted, self.itemtype.schema, res),
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
    def __init__(self, xml):
        """Init."""
        super().__init__(xml)

    def map(self):
        if self.is_deleted():
            return {}
        self.map_itemtype('codeBook')
        res = {'$schema': self.itemtype.id,
               'pubdate': str(self.datestamp())}
        add_funcs = {
            'stdyDscr': partial(add_stdyDscr_ddi, self.itemtype.schema, res)
        }

        for tag in self.json['record']['metadata']['codeBook']:
            if tag in add_funcs:
                add_funcs[tag](
                    self.json['record']['metadata']['codeBook'][tag])
        current_app.logger.info("***************************************")
        current_app.logger.info(res)
        current_app.logger.info("***************************************")
        return res
