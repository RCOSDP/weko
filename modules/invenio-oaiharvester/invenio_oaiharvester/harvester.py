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
from collections import OrderedDict, defaultdict
from functools import partial
from json import dumps, loads

import dateutil
import requests
import xmltodict
from bs4 import BeautifulSoup
from flask import current_app
from lxml import etree
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from weko_records.api import Mapping
from weko_records.models import ItemType
from weko_records.serializers.utils import get_full_mapping, get_mapping
from weko_records.utils import get_options_and_order_list

from .config import OAIHARVESTER_BACKOFF_FACTOR, OAIHARVESTER_DOI_PREFIX, \
    OAIHARVESTER_HDL_PREFIX, OAIHARVESTER_RETRY_COUNT, \
    OAIHARVESTER_VERIFY_TLS_CERTIFICATE

DEFAULT_FIELD = [
    'title',
    'keywords',
    'keywords_en',
    'pubdate',
    'lang',
    'item_titles',
    'item_language',
    'item_keyword']


DDI_MAPPING_KEY_TITLE = 'stdyDscr.citation.titlStmt.titl.@value'
DDI_MAPPING_KEY_URI = 'stdyDscr.citation.holdings.@value'

TEXT = '#text'
LANG = '@xml:lang'


def list_sets(url, encoding='utf-8'):
    """Get sets list."""
    # Avoid SSLError - dh key too small
    requests.packages.urllib3.disable_warnings()
    requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += 'HIGH:!DH:!aNULL'

    sets = []
    payload = {
        'verb': 'ListSets'}
    while True:
        response = requests.get(url, params=payload,
                                verify=OAIHARVESTER_VERIFY_TLS_CERTIFICATE)
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

    if resumption_token is None:
        payload = {
            'verb': 'ListRecords',
            'from': from_date,
            'until': until_date,
            'metadataPrefix': metadata_prefix,
            'set': setspecs}
    else:
        payload = {
            'verb': 'ListRecords',
            'resumptionToken': resumption_token}
    records = []
    rtoken = None

    with requests.Session() as s:
        retries = Retry(total=OAIHARVESTER_RETRY_COUNT,
                        backoff_factor=OAIHARVESTER_BACKOFF_FACTOR,
                        status_forcelist=[500, 502, 503, 504])
        s.mount('https://', HTTPAdapter(max_retries=retries))
        s.mount('http://', HTTPAdapter(max_retries=retries))
        response = s.get(url, params=payload,
                         verify=OAIHARVESTER_VERIFY_TLS_CERTIFICATE)

    response.raise_for_status()
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
    for field_name in schema.get("properties", []):
        if field_name not in DEFAULT_FIELD:
            res[schema['properties'][field_name]['title']] = field_name
    return res


def update_recs(subitems, subitem_key, data_list):
    if data_list != [{}]:
        if subitem_key in subitems:
            if len(subitems[subitem_key]) != len(data_list):
                subitems[subitem_key].extend(data_list)
            else:
                for idx, meta in enumerate(data_list):
                    if isinstance(meta, dict):
                        for key, val in meta.items():
                            if isinstance(val, list):
                                update_recs(
                                    subitems[subitem_key][idx],
                                    key,
                                    val
                                )
                            else:
                                subitems[subitem_key][idx].update(meta)
                    else:
                        subitems[subitem_key].extend(meta)
        else:
            subitems[subitem_key] = data_list


def subitem_recs(subitems, subitem_key_list, schema, oai_key_list, metadata):
    """Generate subitem metadata.

    Args:
        subitems ([type]): [description] result
        subitem_key_list ([type]): [description] subitem key list
        schema ([type]): [description] property schema
        oai_key_list ([type]): [description] oai key list
        metadata ([type]): [description] oai metadata from base url
    """
    subitem_key = subitem_key_list[0] if subitem_key_list else None
    if not subitem_key:
        return None

    subschema = None
    oai_key = oai_key_list[0] if oai_key_list else None
    if schema.get('items', {}).get('properties', {}).get(subitem_key):
        subschema = schema['items']['properties'][subitem_key]
    elif schema.get('properties', {}).get(subitem_key):
        subschema = schema['properties'][subitem_key]
    else:
        current_app.logger.debug("subitem_key: {}, schema: {}".format(subitem_key, schema))

    if subschema:
        if subschema.get('items', {}).get('properties', None):
            if oai_key and oai_key in metadata:
                if isinstance(metadata[oai_key], list):
                    _tmp = []
                    for m in metadata[oai_key]:
                        _i = {}
                        subitem_recs(
                            _i,
                            subitem_key_list[1:],
                            subschema,
                            oai_key_list[1:],
                            m
                        )
                        _tmp.append(_i)
                    if _tmp:
                        update_recs(subitems, subitem_key, _tmp)
                else:
                    _tmp = {}
                    subitem_recs(
                        _tmp,
                        subitem_key_list[1:],
                        subschema,
                        oai_key_list[1:],
                        metadata[oai_key]
                    )
                    if _tmp:
                        update_recs(subitems, subitem_key, [_tmp])
            else:
                current_app.logger.debug("oai_key: {}, metadata: {}".format(oai_key, metadata))
        elif subschema.get('properties', None):
            if oai_key and oai_key in metadata:
                _tmp = {}
                if isinstance(metadata[oai_key], list):
                    for m in metadata[oai_key]:
                        subitem_recs(
                            _tmp,
                            subitem_key_list[1:],
                            subschema,
                            oai_key_list[1:],
                            m
                        )
                        if _tmp:
                            break
                else:
                    subitem_recs(
                        _tmp,
                        subitem_key_list[1:],
                        subschema,
                        oai_key_list[1:],
                        metadata[oai_key]
                    )
                if _tmp:
                    if subitem_key in subitems:
                        subitems[subitem_key].update(_tmp)
                    else:
                        subitems[subitem_key] = _tmp
            else:
                current_app.logger.debug("oai_key: {}, metadata: {}".format(oai_key, metadata))
        else:
            if isinstance(metadata, OrderedDict):
                if isinstance(metadata.get(oai_key), str) or isinstance(metadata.get(oai_key), list):
                    subitems[subitem_key] = metadata.get(oai_key)
                else:
                    current_app.logger.debug("oai_key: {}, metadata: {}".format(oai_key, metadata))
            elif isinstance(metadata, str) and oai_key == TEXT:
                subitems[subitem_key] = metadata
            elif isinstance(metadata, list):
                subitems[subitem_key] = metadata
            else:
                current_app.logger.debug("metadata: {}".format(metadata))


def parsing_metadata(mappin, props, patterns, metadata, res):
    """Genererate item metadata.

    Args:
        mappin ([type]): [description]
        schema ([type]): [description]
        patterns ([type]): [description]
        metadata ([type]): [description]

    Returns:
        [type]: [description]

    """
    # current_app.logger.debug('{0} {1} {2}: {3}'.format(
    #     __file__, 'parsing_metadata()', 'mappin', mappin))
    # current_app.logger.debug('{0} {1} {2}: {3}'.format(
    #     __file__, 'parsing_metadata()', 'props', props))
    # current_app.logger.debug('{0} {1} {2}: {3}'.format(
    #     __file__, 'parsing_metadata()', 'patterns', patterns))
    # current_app.logger.debug('{0} {1} {2}: {3}'.format(
    #     __file__, 'parsing_metadata()', 'metadata', metadata))
    # current_app.logger.debug('{0} {1} {2}: {3}'.format(
    #     __file__, 'parsing_metadata()', 'res', res))
    mapping = mappin.get(patterns[0][0])
    if not mapping:
        return None, None
    else:
        mapping.sort()

    item_key = mapping[0].split('.')[0]

    if item_key and props.get(item_key):
        item_schema = props[item_key]
        ret = []
        for data in metadata:
            items = {}
            for mapping_key, oai_key in patterns:
                mapping = mappin.get(mapping_key)
                if mapping and oai_key:
                    mapping.sort()

                    subitem_key_list = None
                    if ',' in mapping[0]:
                        subitem_key_list = mapping[0].split(',')[0].split('.')[1:]
                    else:
                        subitems = mapping[0].split('.')[1:]
                    
                    if subitems:
                        if subitems[0] in item_schema:
                            submetadata = subitem_recs(
                                item_schema[subitems[0]],
                                subitems[1:],
                                value,
                                it
                            )

                            if submetadata:
                                if isinstance(submetadata, list):
                                    if items.get(subitems[0]):
                                        if len(items[subitems[0]]) != len(submetadata):
                                            items[subitems[0]].extend(submetadata)
                                            continue

                                        for idx, meta in enumerate(submetadata):
                                            if isinstance(meta, dict):
                                                items[subitems[0]][idx].update(
                                                    meta)
                                            else:
                                                items[subitems[0]].extend(meta)
                                    else:
                                        items[subitems[0]] = submetadata
                                elif isinstance(submetadata, dict):
                                    submetadata_key = None
                                    if len(list(submetadata.keys())) > 0:
                                        submetadata_key = list(submetadata.keys())[0]
                                    if items.get(subitems[0]):
                                        items[subitems[0]].update(submetadata)
                                    else:
                                        items[subitems[0]] = submetadata
                                else:
                                    items[subitems[0]] = submetadata
            if items:
                ret.append(items)

        if item_key and ret:
            if res.get(item_key):
                res[item_key].extend(ret)
            else:
                res[item_key] = ret

        # current_app.logger.debug('{0} {1} {2}: {3}'.format(
        #     __file__, 'parsing_metadata()', 'item_key', item_key))
        # current_app.logger.debug('{0} {1} {2}: {3}'.format(
        #     __file__, 'parsing_metadata()', 'ret', ret))

        return item_key, ret

    else:
        return None, None


def add_title(schema, mapping, res, metadata):
    """Add title of the resource.

    Args:
        schema ([type]): [description]
        res ([type]): [description]
        mapping ([type]): [description]
        titles ([type]): [description]
    """
    patterns = [
        ('title.@value', TEXT),
        ('title.@attributes.xml:lang', LANG)
    ]

    item_key, ret = parsing_metadata(mapping, schema, patterns, metadata, res)

    if item_key and ret:
        if isinstance(metadata[0], str):
            res['title'] = metadata[0]
        elif isinstance(metadata[0], OrderedDict):
            res['title'] = metadata[0].get(TEXT)


def add_alternative(schema, mapping, res, metadata):
    """Add titles other than the main title such as the \
    title for a contents page or colophon."""
    patterns = [
        ('alternative.@value', TEXT),
        ('alternative.@attributes.xml:lang', LANG)
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_creator_jpcoar(schema, mapping, res, metadata):
    """Add individual or organisation that is responsible for \
    the creation of the resource."""
    patterns = [
        ('creator.givenName.@value',
            'jpcoar:givenName.#text'),
        ('creator.givenName.@attributes.xml:lang',
            'jpcoar:givenName.@xml:lang'),
        ('creator.familyName.@value',
            'jpcoar:familyName.#text'),
        ('creator.familyName.@attributes.xml:lang',
            'jpcoar:familyName.@xml:lang'),
        ('creator.creatorName.@value',
            'jpcoar:creatorName.#text'),
        ('creator.creatorName.@attributes.xml:lang',
            'jpcoar:creatorName.@xml:lang'),
        ('creator.creatorName.@attributes.nameType',
            'jpcoar:creatorName.@nameType'),
        ('creator.creatorAlternative.@value',
            'jpcoar:creatorAlternative.#text'),
        ('creator.creatorAlternative.@attributes.xml:lang',
            'jpcoar:creatorAlternative.@xml:lang'),
        ('creator.@attributes.creatorType',
            '@creatorType'),
        ('creator.nameIdentifier.@value',
            'jpcoar:nameIdentifier.#text'),
        ('creator.nameIdentifier.@attributes.nameIdentifierURI',
            'jpcoar:nameIdentifier.@nameIdentifierURI'),
        ('creator.nameIdentifier.@attributes.nameIdentifierScheme',
            'jpcoar:nameIdentifier.@nameIdentifierScheme'),
        ('creator.affiliation.nameIdentifier.@value',
            'jpcoar:affiliation.jpcoar:nameIdentifier.#text'),
        ('creator.affiliation.nameIdentifier.@attributes.nameIdentifierURI',
            'jpcoar:affiliation.jpcoar:nameIdentifier.@nameIdentifierURI'),
        ('creator.affiliation.nameIdentifier.@attributes.nameIdentifierScheme',
            'jpcoar:affiliation.jpcoar:nameIdentifier.@nameIdentifierScheme'),
        ('creator.affiliation.affiliationName.@value',
            'jpcoar:affiliation.jpcoar:affiliationName.#text'),
        ('creator.affiliation.affiliationName.@attributes.xml:lang',
            'jpcoar:affiliation.jpcoar:affiliationName.@xml:lang'),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_contributor_jpcoar(schema, mapping, res, metadata):
    """Add contributor.

    Args:
        schema ([type]): [description]
        mapping ([type]): [description]
        res ([type]): [description]
        metadata ([type]): [description]
    """
    patterns = [
        ('contributor.@attributes.contributorType',
         '@contributorType'),
        ('contributor.nameIdentifier.@value',
            'jpcoar:nameIdentifier.#text'),
        ('contributor.nameIdentifier.@attributes.nameIdentifierURI',
            'jpcoar:nameIdentifier.@nameIdentifierURI'),
        ('contributor.nameIdentifier.@attributes.nameIdentifierScheme',
            'jpcoar:nameIdentifier.@nameIdentifierScheme'),
        ('contributor.givenName.@value',
            'jpcoar:givenName.#text'),
        ('contributor.givenName.@attributes.xml:lang',
            'jpcoar:givenName.@xml:lang'),
        ('contributor.familyName.@value',
            'jpcoar:familyName.#text'),
        ('contributor.familyName.@attributes.xml:lang',
            'jpcoar:familyName.@xml:lang'),
        ('contributor.contributorName.@value',
            'jpcoar:contributorName.#text'),
        ('contributor.contributorName.@attributes.xml:lang',
            'jpcoar:contributorName.@xml:lang'),
        ('contributor.contributorName.@attributes.nameType',
            'jpcoar:contributorName.@nameType'),
        ('contributor.contributorAlternative.@value',
            'jpcoar:contributorAlternative.#text'),
        ('contributor.contributorAlternative.@attributes.xml:lang',
            'jpcoar:contributorAlternative.@xml:lang'),
        ('contributor.affiliation.nameIdentifier.@value',
            'jpcoar:affiliation.jpcoar:nameIdentifier.#text'),
        ('contributor.affiliation.nameIdentifier.@attributes.nameIdentifierURI',
            'jpcoar:affiliation.jpcoar:nameIdentifier.@nameIdentifierURI'),
        ('contributor.affiliation.nameIdentifier.@attributes.nameIdentifierScheme',
            'jpcoar:affiliation.jpcoar:nameIdentifier.@nameIdentifierScheme'),
        ('contributor.affiliation.affiliationName.@value',
            'jpcoar:affiliation.jpcoar:affiliationName.#text'),
        ('contributor.affiliation.affiliationName.@attributes.xml:lang',
            'jpcoar:affiliation.jpcoar:affiliationName.@xml:lang'),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_publisher_jpcoar(schema, mapping, res, metadata):
    """Add publisher."""
    patterns = [
        (
            'publisher_jpcoar.publisherName.@value',
            'jpcoar:publisherName.#text'
        ),
        (
            'publisher_jpcoar.publisherName.@attributes.xml:lang',
            'jpcoar:publisherName.@xml:lang'
        ),
        (
            'publisher_jpcoar.publisherDescription.@value',
            'jpcoar:publisherDescription.#text'
        ),
        (
            'publisher_jpcoar.publisherDescription.@attributes.xml:lang',
            'jpcoar:publisherDescription.@xml:lang'
        ),
        (
            'publisher_jpcoar.location.@value',
            'dcndl:location.#text'
        ),
        (
            'publisher_jpcoar.publicationPlace.@value',
            'dcndl:publicationPlace.#text'
        ),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_access_right(schema, mapping, res, metadata):
    """Add the access status of the resource.

    Args:
        schema ([type]): [description]
        mapping ([type]): [description]
        res ([type]): [description]
        access_rights ([type]): [description]
    """
    patterns = [
        ('accessRights.@value', TEXT),
        ('accessRights.@attributes.rdf:resource', '@rdf:resource'),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_apc(schema, mapping, res, metadata):
    """Add apc.

    Args:
        schema ([type]): [description]
        mapping ([type]): [description]
        res ([type]): [description]
        metadata ([type]): [description]
    """
    patterns = [
        ('apc.@value', TEXT),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_right(schema, mapping, res, metadata):
    """Add rights."""
    patterns = [
        ('rights.@value', TEXT),
        ('rights.@attributes.xml:lang', LANG),
        ('rights.@attributes.rdf:resource', '@rdf:resource'),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_subject(schema, mapping, res, metadata):
    """Add subject."""
    patterns = [
        (
            'subject.@value',
             TEXT
        ),
        (
            'subject.@attributes.xml:lang',
            LANG
        ),
        (
            'subject.@attributes.subjectURI',
            '@subjectURI'
        ),
        (
            'subject.@attributes.subjectScheme',
            '@subjectScheme'
        ),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_description(schema, mapping, res, metadata):
    """Add description.

    If 'descriptionType' is missed, default value is 'Others'.

    Args:
        schema ([type]): [description]
        mapping ([type]): [description]
        res ([type]): [description]
        metadata ([type]): [description]
    """
    patterns = [
        ('description.@value', TEXT),
        ('description.@attributes.xml:lang', LANG),
        ('description.@attributes.descriptionType', '@descriptionType')
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_publisher(schema, mapping, res, metadata):
    """Add publisher."""
    patterns = [
        ('publisher.@value', TEXT),
        ('publisher.@attributes.xml:lang', LANG),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_date(schema, mapping, res, metadata):
    """Add date."""
    patterns = [
        ('date.@value', TEXT),
        ('date.@attributes.dateType', '@dateType'),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_date_dcterms(schema, mapping, res, metadata):
    patterns = [
        ('date_dcterms.@value', '#text'),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_edition(schema, mapping, res, metadata):
    patterns = [
        (
            'edition.@value',
            '#text'
        ),
        (
            'edition.@attributes.xml:lang',
            '@xml:lang'
        ),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_volumeTitle(schema, mapping, res, metadata):
    patterns = [
        (
            'volumeTitle.@value',
            '#text'
        ),
        (
            'volumeTitle.@attributes.xml:lang',
            '@xml:lang'
        ),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_originalLanguage(schema, mapping, res, metadata):
    patterns = [
        (
            'originalLanguage.@value',
            '#text'
        ),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_extent(schema, mapping, res, metadata):
    patterns = [
        (
            'extent.@value',
            '#text'
        ),
        (
            'extent.@attributes.xml:lang',
            '@xml:lang'
        ),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_format(schema, mapping, res, metadata):
    patterns = [
        (
            'format.@value',
            '#text'
        ),
        (
            'format.@attributes.xml:lang',
            '@xml:lang'
        ),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_holdingAgent(schema, mapping, res, metadata):
    patterns = [
        (
            'holdingAgent.holdingAgentName.@value',
            'jpcoar:holdingAgentName.#text'
        ),
        (
            'holdingAgent.holdingAgentName.@attributes.xml:lang',
            'jpcoar:holdingAgentName.@xml:lang'
        ),
        (
            'holdingAgent.holdingAgentNameIdentifier.@value',
            'jpcoar:holdingAgentNameIdentifier.#text',
        ),
        (
            'holdingAgent.holdingAgentNameIdentifier.@attributes.nameIdentifierScheme',
            'jpcoar:holdingAgentNameIdentifier.@nameIdentifierScheme',
        ),
        (
            'holdingAgent.holdingAgentNameIdentifier.@attributes.nameIdentifierURI',
            'jpcoar:holdingAgentNameIdentifier.@nameIdentifierURI',
        ),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_datasetSeries(schema, mapping, res, metadata):
    patterns = [
        (
            'datasetSeries.@value',
            '#text',
        ),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_catalog(schema, mapping, res, metadata):
    patterns = [
        (
            'catalog.contributor.@attributes.contributorType',
            'jpcoar:contributor.@contributorType',
        ),
        (
            'catalog.contributor.contributorName.@value',
            'jpcoar:contributor.jpcoar:contributorName.#text',
        ),
        (
            'catalog.contributor.contributorName.@attributes.xml:lang',
            'jpcoar:contributor.jpcoar:contributorName.@xml:lang',
        ),
        (
            'catalog.identifier.@value',
            'jpcoar:identifier.#text'
        ),
        (
            'catalog.identifier.@attributes.identifierType',
            'jpcoar:identifier.@identifierType'
        ),
        (
            'catalog.title.@value',
            'dc:title.#text'
        ),
        (
            'catalog.title.@attributes.xml:lang',
            'dc:title.@xml:lang'
        ),
        (
            'catalog.description.@value',
            'datacite:description.#text'
        ),
        (
            'catalog.description.@attributes.xml:lang',
            'datacite:description.@xml:lang'
        ),
        (
            'catalog.description.@attributes.descriptionType',
            'datacite:description.@descriptionType'
        ),
        (
            'catalog.subject.@value',
            'jpcoar:subject.#text'
        ),
        (
            'catalog.subject.@attributes.xml:lang',
            'jpcoar:subject.@xml:lang'
        ),
        (
            'catalog.subject.@attributes.subjectURI',
            'jpcoar:subject.@subjectURI'
        ),
        (
            'catalog.subject.@attributes.subjectScheme',
            'jpcoar:subject.@subjectScheme'
        ),
        (
            'catalog.license.@value',
            'jpcoar:license.#text'
        ),
        (
            'catalog.license.@attributes.xml:lang',
            'jpcoar:license.@xml:lang'
        ),
        (
            'catalog.license.@attributes.licenseType',
            'jpcoar:license.@licenseType'
        ),
        (
            'catalog.license.@attributes.rdf:resource',
            'jpcoar:license.@rdf:resource'
        ),
        (
            'catalog.rights.@value',
            'dc:rights.#text'
        ),
        (
            'catalog.rights.@attributes.xml:lang',
            'dc:rights.@xml:lang'
        ),
        (
            'catalog.rights.@attributes.rdf:resource',
            'dc:rights.@rdf:resource'
        ),
        (
            'catalog.accessRights.@value',
            'dcterms:accessRights.#text'
        ),
        (
            'catalog.accessRights.@attributes.rdf:resource',
            'dcterms:accessRights.@rdf:resource'
        ),
        (
            'catalog.file.URI.@value',
            'jpcoar:file.jpcoar:URI.#text'
        ),
        (
            'catalog.file.URI.@attributes.objectType',
            'jpcoar:file.jpcoar:URI.@objectType'
        ),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_language(schema, mapping, res, metadata):
    """Add language."""
    patterns = [
        ('language.@value', TEXT),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_version(schema, mapping, res, metadata):
    """Add version."""
    patterns = [
        ('version.@value', TEXT),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_version_type(schema, mapping, res, metadata):
    """Add version type."""
    patterns = [
        ('versionType.@value', TEXT),
        ('versionType.@attributes.rdf:resource', '@rdf:resource'),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_identifier_registration(schema, mapping, res, metadata):
    """Add identfier registration."""
    patterns = [
        ('identifierRegistration.@value',
            TEXT),
        ('identifierRegistration.@attributes.identifierType',
            '@identifierType'),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_temporal(schema, mapping, res, metadata):
    """Add temporal."""
    patterns = [
        ('temporal.@value', TEXT),
        ('temporal.@attributes.xml:lang', LANG),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_source_identifier(schema, mapping, res, metadata):
    """Add source identifier."""
    patterns = [
        ('sourceIdentifier.@value', TEXT),
        ('sourceIdentifier.@attributes.identifierType', '@identifierType'),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_file(schema, mapping, res, metadata):
    """Add file."""
    patterns = [
        ('file.version.@value',
            'datacite:version.#text'),
        ('file.mimeType.@value',
            'jpcoar:mimeType.#text'),
        ('file.extent.@value',
            'jpcoar:extent.#text'),
        ('file.date.@value',
            'datacite:date.#text'),
        ('file.date.@attributes.dateType',
            'datacite:date.@dateType'),
        ('file.URI.@value',
            'jpcoar:URI.#text'),
        ('file.URI.@attributes.objectType',
            'jpcoar:URI.@objectType'),
        ('file.URI.@attributes.label',
            'jpcoar:URI.@label'),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_identifier(schema, mapping, res, metadata):
    """Add identifier."""
    patterns = [
        ('identifier.@value', TEXT),
        ('identifier.@attributes.identifierType', '@identifierType'),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_source_title(schema, mapping, res, metadata):
    """Add source title."""
    patterns = [
        ('sourceTitle.@value', TEXT),
        ('sourceTitle.@attributes.xml:lang', LANG),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_volume(schema, mapping, res, metadata):
    """Add volume."""
    patterns = [
        ('volume.@value', TEXT),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_issue(schema, mapping, res, metadata):
    """Add issue."""
    patterns = [
        ('issue.@value', TEXT),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_num_page(schema, mapping, res, metadata):
    """Add num pages."""
    patterns = [
        ('numPages.@value', TEXT),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_page_start(schema, mapping, res, metadata):
    """Add page start."""
    patterns = [
        ('pageStart.@value', TEXT),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_page_end(schema, mapping, res, metadata):
    """Add page end."""
    patterns = [
        ('pageEnd.@value', TEXT),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_dissertation_number(schema, mapping, res, metadata):
    """Add dissertation number."""
    patterns = [
        ('dissertationNumber.@value', TEXT),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_date_granted(schema, mapping, res, metadata):
    """Add date granted."""
    patterns = [
        ('dateGranted.@value', TEXT),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_conference(schema, mapping, res, metadata):
    """Add conference information."""
    patterns = [
        ('conference.conferenceCountry.@value',
            'jpcoar:conferenceCountry.#text'),
        ('conference.conferenceSequence.@value',
            'jpcoar:conferenceSequence.#text'),
        ('conference.conferencePlace.@value',
            'jpcoar:conferencePlace.#text'),
        ('conference.conferencePlace.@attributes.xml:lang',
            'jpcoar:conferencePlace.@xml:lang'),
        ('conference.conferenceName.@value',
            'jpcoar:conferenceName.#text'),
        ('conference.conferenceName.@attributes.xml:lang',
            'jpcoar:conferenceName.@xml:lang'),
        ('conference.conferenceSponsor.@value',
            'jpcoar:conferenceSponsor.#text'),
        ('conference.conferenceSponsor.@attributes.xml:lang',
            'jpcoar:conferenceSponsor.@xml:lang'),
        ('conference.conferenceDate.@value',
            'jpcoar:conferenceDate.#text'),
        ('conference.conferenceDate.@startYear',
            'jpcoar:conferenceDate.@startYear'),
        ('conference.conferenceDate.@startMonth',
            'jpcoar:conferenceDate.@startMonth'),
        ('conference.conferenceDate.@startDay',
            'jpcoar:conferenceDate.@startDay'),
        ('conference.conferenceDate.@endYear',
            'jpcoar:conferenceDate.@endYear'),
        ('conference.conferenceDate.@endMonth',
            'jpcoar:conferenceDate.@endMonth'),
        ('conference.conferenceDate.@endDay',
            'jpcoar:conferenceDate.@endDay'),
        ('conference.conferenceDate.@attributes.xml:lang',
            'jpcoar:conferenceDate.@xml:lang'),
        ('conference.conferenceVenue.@value',
            'jpcoar:conferenceVenue.#text'),
        ('conference.conferenceVenue.@attributes.xml:lang',
            'jpcoar:conferenceVenue.@xml:lang'),
        
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_degree_grantor(schema, mapping, res, metadata):
    """Add information on the degree granting institution."""
    patterns = [
        ('degreeGrantor.nameIdentifier.@value',
            'jpcoar:nameIdentifier.#text'),
        ('degreeGrantor.nameIdentifier.@attributes.nameIdentifierScheme',
            'jpcoar:nameIdentifier.@nameIdentifierScheme'),
        ('degreeGrantor.degreeGrantorName.@value',
            'jpcoar:degreeGrantorName.#text'),
        ('degreeGrantor.degreeGrantorName.@attributes.xml:lang',
            'jpcoar:degreeGrantorName.@xml:lang'),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_degree_name(schema, mapping, res, metadata):
    """Add academic degree and field of the degree specified in \
    the Degree Regulation."""
    patterns = [
        ('degreeName.@value',
            TEXT),
        ('degreeName.@attributes.xml:lang',
            LANG),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_funding_reference(schema, mapping, res, metadata):
    """Add the grant information if you have received \
    financial support (funding) to create the resource."""
    patterns = [
        (
            'fundingReference.funderName.@value',
            'jpcoar:funderName.#text'
        ),
        (
            'fundingReference.funderName.@attributes.xml:lang',
            'jpcoar:funderName.@xml:lang'
        ),
        (
            'fundingReference.funderIdentifier.@value',
            'jpcoar:funderIdentifier.#text'
        ),
        (
            'fundingReference.funderIdentifier.@attributes.funderIdentifierType',
            'jpcoar:funderIdentifier.@funderIdentifierType'
        ),
        (
            'fundingReference.funderIdentifier.@attributes.funderIdentifierTypeURI',
            'jpcoar:funderIdentifier.@funderIdentifierTypeURI'
        ),
        (
            'fundingReference.fundingStreamIdentifier.@value',
            'jpcoar:fundingStreamIdentifier.#text'
        ),
        (
            'fundingReference.fundingStreamIdentifier.@attributes.fundingStreamIdentifierType',
            'jpcoar:fundingStreamIdentifier.@fundingStreamIdentifierType'
        ),
        (
            'fundingReference.fundingStreamIdentifier.@attributes.fundingStreamIdentifierTypeURI',
            'jpcoar:fundingStreamIdentifier.@fundingStreamIdentifierTypeURI',
        ),
        (
            'fundingReference.fundingStream.@value',
            'jpcoar:fundingStream.#text'
        ),
        (
            'fundingReference.fundingStream.@attributes.xml:lang',
            'jpcoar:fundingStream.@xml:lang'
        ),
        (
            'fundingReference.awardNumber.@value',
            'jpcoar:awardNumber.#text'
        ),
        (
            'fundingReference.awardNumber.@attributes.awardURI',
            'jpcoar:awardNumber.@awardURI'
        ),
        (
            'fundingReference.awardNumber.@attributes.awardNumberType',
            'jpcoar:awardNumber.@awardNumberType'
        ),
        (
            'fundingReference.awardTitle.@value',
            'jpcoar:awardTitle.#text'
        ),
        (
            'fundingReference.awardTitle.@attributes.xml:lang',
            'jpcoar:awardTitle.@xml:lang'
        ),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_geo_location(schema, mapping, res, metadata):
    """Add Spatial region or named place where the resource was \
    gathered or about which the data is focused."""
    patterns = [
        ('geoLocation.geoLocationPoint.pointLongitude.@value',
            'datacite:geoLocationPoint.datacite:pointLongitude.#text'),
        ('geoLocation.geoLocationPoint.pointLatitude.@value',
            'datacite:geoLocationPoint.datacite:pointLatitude.#text'),
        ('geoLocation.geoLocationPlace.@value',
            'datacite:geoLocationPlace.#text'),
        ('geoLocation.geoLocationBox.westBoundLongitude.@value',
            'datacite:geoLocationBox.datacite:westBoundLongitude.#text'),
        ('geoLocation.geoLocationBox.southBoundLatitude.@value',
            'datacite:geoLocationBox.datacite:southBoundLatitude.#text'),
        ('geoLocation.geoLocationBox.northBoundLatitude.@value',
            'datacite:geoLocationBox.datacite:northBoundLatitude.#text'),
        ('geoLocation.geoLocationBox.eastBoundLongitude.@value',
            'datacite:geoLocationBox.datacite:eastBoundLongitude.#text'),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_relation(schema, mapping, res, metadata):
    """Add the relationship between the registering resource \
    and other related resource.

    Select and enter 'relationType' from the controlled vocabularies.
    If there is no corresponding vocabulary, do not enter 'relationType'.
    """
    patterns = [
        ('relation.@attributes.relationType',
            '@relationType'),
        ('relation.relatedTitle.@value',
            'jpcoar:relatedTitle.#text'),
        ('relation.relatedTitle.@attributes.xml:lang',
            'jpcoar:relatedTitle.@xml:lang'),
        ('relation.relatedIdentifier.@value',
            'jpcoar:relatedIdentifier.#text'),
        ('relation.relatedIdentifier.@attributes.identifierType',
            'jpcoar:relatedIdentifier.@identifierType'),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_rights_holder(schema, mapping, res, metadata):
    """Add the information on the rights holder of such as copyright \
    other than the creator or contributor."""
    patterns = [
        ('rightsHolder.rightsHolderName.@value',
            'jpcoar:rightsHolderName.#text'),
        ('rightsHolder.rightsHolderName.@attributes.xml:lang',
            'jpcoar:rightsHolderName.@xml:lang'),
        ('rightsHolder.nameIdentifier.@value',
            'jpcoar:nameIdentifier.#text'),
        ('rightsHolder.nameIdentifier.@attributes.nameIdentifierURI',
            'jpcoar:nameIdentifier.@nameIdentifierURI'),
        ('rightsHolder.nameIdentifier.@attributes.nameIdentifierScheme',
            'jpcoar:nameIdentifier.@nameIdentifierScheme'),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_resource_type(schema, mapping, res, metadata):
    """Add publisher."""
    patterns = [
        ('type.@value', TEXT),
        ('type.@attributes.rdf:resource', '@rdf:resource'),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_creator_dc(schema, mapping, res, metadata):
    """Add creator."""
    patterns = [
        ('creator.@value', TEXT),
        ('creaotr.@attributes.xml:lang', LANG),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


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
            item[temporal] = it.get(TEXT)
            item[language] = it.get(LANG)
        res[root_key].append(item)


def add_source_dc(schema, mapping, res, metadata):
    """Add source."""
    patterns = [
        ('source.@value', TEXT),
        ('source.@attributes.xml:lang', LANG),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_coverage_dc(schema, mapping, res, metadata):
    """Add coverage."""
    patterns = [
        ('coverage.@value', TEXT),
        ('coverage.@attributes.xml:lang', LANG),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_format_dc(schema, mapping, res, metadata):
    """Add file."""
    patterns = [
        ('format.@value', TEXT),
        ('format.@attributes.xml:lang', LANG),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_contributor_dc(schema, mapping, res, metadata):
    """Add contributor."""
    patterns = [
        ('contributor.@value', TEXT),
        ('contributor.@attributes.xml:lang', LANG),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_relation_dc(schema, mapping, res, metadata):
    """Add relation."""
    patterns = [
        ('relation.@value', TEXT),
        ('relation.@attributes.xml:lang', LANG),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_rights_dc(schema, mapping, res, metadata):
    """Add rights."""
    patterns = [
        ('rights.@value', TEXT),
        ('rights.@attributes.xml:lang', LANG),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_identifier_dc(schema, mapping, res, metadata):
    """Add identifier."""
    patterns = [
        ('identifier.@value', TEXT),
        ('identifier.@attributes.xml:lang', LANG),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_description_dc(schema, mapping, res, metadata):
    """Add description."""
    patterns = [
        ('description.@value', TEXT),
        ('description.@attributes.xml:lang', LANG),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_subject_dc(schema, mapping, res, metadata):
    """Add subject."""
    patterns = [
        ('subject.@value', TEXT),
        ('subject.@attributes.xml:lang', LANG),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_title_dc(schema, mapping, res, metadata):
    """Add title."""
    #    if 'title_en' not in res:
    #        res['title_en'] = title
    patterns = [
        ('title.@value', TEXT),
        ('title.@attributes.xml:lang', LANG)
    ]

    item_key, ret = parsing_metadata(mapping, schema, patterns, metadata, res)

    if item_key and ret:
        if isinstance(metadata[0], str):
            res['title'] = metadata[0]
        elif isinstance(metadata[0], OrderedDict):
            res['title'] = metadata[0].get(TEXT)


def add_language_dc(schema, mapping, res, metadata):
    """Add language."""
    patterns = [
        ('language.@value', TEXT),
        ('language.@attributes.xml:lang', LANG),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_date_dc(schema, mapping, res, metadata):
    """Add date."""
    patterns = [
        ('date.@value', TEXT),
        ('date.@attributes.xml:lang', LANG),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_publisher_dc(schema, mapping, res, metadata):
    """Add publisher."""
    patterns = [
        ('publisher.@value', TEXT),
        ('publisher.@attributes.xml:lang', LANG),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_resource_type_dc(schema, mapping, res, metadata):
    """Add resoruce_type."""
    patterns = [
        ('type.@value', TEXT),
        ('type.@attributes.xml:lang', LANG),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def to_dict(input_ordered_dict):
    """Convert OrderDict to Dict."""
    return loads(dumps(input_ordered_dict))


RESOURCE_TYPE_MAP = {
    'conference paper': 'Conference Paper',
    'data paper': 'Journal Article',
    'departmental bulletin paper': 'Departmental Bulletin Paper',
    'editorial': 'Article',
    'journal article': 'Journal Article',
    'newspaper': 'Journal Article',
    'periodical': 'Article',
    'review article': 'Article',
    'software paper': 'Article',
    'article': 'Article',
    'book': 'Book',
    'book part': 'Book',
    'cartographic material': 'Others',
    'map': 'Others',
    'conference object': 'Presentation',
    'conference proceedings': 'Presentation',
    'conference poster': 'Presentation',
    'dataset': 'Data or Dataset',
    'interview': 'Others',
    'image': 'Others',
    'still image': 'Others',
    'moving image': 'Others',
    'video': 'Others',
    'lecture': 'Others',
    'patent': 'Others',
    'internal report': 'Others',
    'report': 'Research Paper',
    'research report': 'Research Paper',
    'technical report': 'Technical Report',
    'policy report': 'Others',
    'report part': 'Others',
    'working paper': 'Others',
    'data management plan': 'Others',
    'sound': 'Others',
    'thesis': 'Thesis or Dissertation',
    'bachelor thesis': 'Thesis or Dissertation',
    'master thesis': 'Thesis or Dissertation',
    'doctoral thesis': 'Thesis or Dissertation',
    'interactive resource': 'Others',
    'learning object': 'Learning Material',
    'manuscript': 'Others',
    'musical notation': 'Others',
    'research proposal': 'Others',
    'software': 'Software',
    'technical documentation': 'Others',
    'workflow': 'Others',
    'other': 'Others'
}

RESOURCE_TYPE_URI = {
    'conference paper': 'http://purl.org/coar/resource_type/c_5794',
    'data paper': 'http://purl.org/coar/resource_type/c_beb9',
    'departmental bulletin paper': 'http://purl.org/coar/resource_type/c_6501',
    'editorial': 'http://purl.org/coar/resource_type/c_b239',
    'journal': 'http://purl.org/coar/resource_type/c_0640',
    'journal article': 'http://purl.org/coar/resource_type/c_6501',
    'newspaper': 'http://purl.org/coar/resource_type/c_2fe3',
    'periodical': 'http://purl.org/coar/resource_type/c_2659',
    'review article': 'http://purl.org/coar/resource_type/c_dcae04bc',
    'other periodical': 'http://purl.org/coar/resource_type/QX5C-AR31',
    'software paper': 'http://purl.org/coar/resource_type/c_7bab',
    'article': 'http://purl.org/coar/resource_type/c_6501',
    'book': 'http://purl.org/coar/resource_type/c_2f33',
    'book part': 'http://purl.org/coar/resource_type/c_3248',
    'cartographic material': 'http://purl.org/coar/resource_type/c_12cc',
    'map': 'http://purl.org/coar/resource_type/c_12cd',
    'conference output': 'http://purl.org/coar/resource_type/c_c94f',
    'conference presentation': 'http://purl.org/coar/resource_type/c_c94f',
    'conference object': 'http://purl.org/coar/resource_type/c_c94f',
    'conference proceedings': 'http://purl.org/coar/resource_type/c_f744',
    'conference poster': 'http://purl.org/coar/resource_type/c_6670',
    'dataset': 'http://purl.org/coar/resource_type/c_ddb1',
    'interview': 'http://purl.org/coar/resource_type/c_26e4',
    'image': 'http://purl.org/coar/resource_type/c_c513',
    'still image': 'http://purl.org/coar/resource_type/c_ecc8',
    'moving image': 'http://purl.org/coar/resource_type/c_8a7e',
    'video': 'http://purl.org/coar/resource_type/c_12ce',
    'lecture': 'http://purl.org/coar/resource_type/c_8544',
    'patent': 'http://purl.org/coar/resource_type/c_15cd',
    'internal report': 'http://purl.org/coar/resource_type/c_18ww',
    'report': 'http://purl.org/coar/resource_type/c_93fc',
    'research report': 'http://purl.org/coar/resource_type/c_18ws',
    'technical report': 'http://purl.org/coar/resource_type/c_18gh',
    'policy report': 'http://purl.org/coar/resource_type/c_186u',
    'report part': 'http://purl.org/coar/resource_type/c_ba1f',
    'working paper': 'http://purl.org/coar/resource_type/c_8042',
    'data management plan': 'http://purl.org/coar/resource_type/c_ab20',
    'sound': 'http://purl.org/coar/resource_type/c_18cc',
    'thesis': 'http://purl.org/coar/resource_type/c_46ec',
    'bachelor thesis': 'http://purl.org/coar/resource_type/c_7a1f',
    'master thesis': 'http://purl.org/coar/resource_type/c_bdcc',
    'doctoral thesis': 'http://purl.org/coar/resource_type/c_db06',
    'interactive resource': 'http://purl.org/coar/resource_type/c_e9a0',
    'learning object': 'http://purl.org/coar/resource_type/c_e059',
    'manuscript': 'http://purl.org/coar/resource_type/c_0040',
    'musical notation': 'http://purl.org/coar/resource_type/c_18cw',
    'research proposal': 'http://purl.org/coar/resource_type/c_baaf',
    'software': 'http://purl.org/coar/resource_type/c_5ce6',
    'technical documentation': 'http://purl.org/coar/resource_type/c_71bd',
    'workflow': 'http://purl.org/coar/resource_type/c_393c',
    'other（その他）': 'http://purl.org/coar/resource_type/c_1843',
    'other（プレプリント）': '',
    'aggregated data': 'http://purl.org/coar/resource_type/ACF7-8YT9',
    'clinical trial data': 'http://purl.org/coar/resource_type/c_cb28',
    'compiled data': 'http://purl.org/coar/resource_type/FXF3-D3G7',
    'encoded data': 'http://purl.org/coar/resource_type/AM6W-6QAW',
    'experimental data': 'http://purl.org/coar/resource_type/63NG-B465',
    'genomic data': 'http://purl.org/coar/resource_type/A8F1-NPV9',
    'geospatial data': 'http://purl.org/coar/resource_type/2H0M-X761',
    'laboratory notebook': 'http://purl.org/coar/resource_type/H41Y-FW7B',
    'measurement and test data': 'http://purl.org/coar/resource_type/DD58-GFSX',
    'observational data': 'http://purl.org/coar/resource_type/FF4C-28RK',
    'recorded data': 'http://purl.org/coar/resource_type/CQMR-7K63',
    'simulation data': 'http://purl.org/coar/resource_type/W2XT-7017',
    'survey data': 'http://purl.org/coar/resource_type/NHD0-W6SY',
    'design patent': 'http://purl.org/coar/resource_type/C53B-JCY5/',
    'PCT application': 'http://purl.org/coar/resource_type/SB3Y-W4EH/',
    'plant patent': 'http://purl.org/coar/resource_type/Z907-YMBB/',
    'plant variety protection': 'http://purl.org/coar/resource_type/GPQ7-G5VE/',
    'software patent': 'http://purl.org/coar/resource_type/MW8G-3CR8/',
    'trademark': 'http://purl.org/coar/resource_type/H6QP-SC1X/',
    'utility model': 'http://purl.org/coar/resource_type/9DKX-KSAF/',
    'commentary': 'http://purl.org/coar/resource_type/D97F-VB57',
    'design': 'http://purl.org/coar/resource_type/542X-3S04/',
    'industrial design': 'http://purl.org/coar/resource_type/JBNF-DYAD/',
    'layout design': 'http://purl.org/coar/resource_type/BW7T-YM2G/',
    'peer review': 'http://purl.org/coar/resource_type/H9BQ-739P/',
    'research protocol': 'http://purl.org/coar/resource_type/YZ1N-ZFT9/',
    'source code': 'http://purl.org/coar/resource_type/QH80-2R4E/',
    'transcription': 'http://purl.org/coar/resource_type/6NC7-GK9S/',
}


def map_sets(sets, encoding='utf-8'):
    """Get sets map."""
    res = OrderedDict()
    pattern = '<setSpec>(.+)</setSpec><setName>(.+)</setName>'
    for s in sets:
        xml = etree.tostring(s, encoding=encoding).decode()
        m = re.search(pattern, xml)
        if m:
            spec = m.group(1)
            name = m.group(2)
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

        for item in BaseMapper.itemtype_map:
            if 'Others' == item or 'Multiple' == item:
                self.itemtype = BaseMapper.itemtype_map.get(item)
                break

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
            if isinstance(t, OrderedDict):
                t = t[TEXT]
            if t.lower() in RESOURCE_TYPE_MAP:
                resource_type = RESOURCE_TYPE_MAP.get(t.lower())
                if BaseMapper.itemtype_map.get(resource_type):
                    self.itemtype = BaseMapper.itemtype_map.get(resource_type)


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
        self.identifiers = []
        res = {'$schema': self.itemtype.id,
               'pubdate': str(self.datestamp())}
        item_type_mapping = Mapping.get_record(self.itemtype.id)
        item_map = get_full_mapping(item_type_mapping, "oai_dc_mapping")

        args = [self.itemtype.schema.get('properties'), item_map, res]

        add_funcs = {
            'dc:creator': partial(add_creator_dc, *args),
            'dc:contributor': partial(add_contributor_dc, *args),
            'dc:title': partial(add_title_dc, *args),
            'dc:subject': partial(add_subject_dc, *args),
            'dc:description': partial(add_description_dc, *args),
            'dc:publisher': partial(add_publisher_dc, *args),
            'dc:type': partial(add_resource_type_dc, *args),
            'dc:date': partial(add_date_dc, *args),
            'dc:identifier': partial(add_identifier_dc, *args),
            'dc:language': partial(add_language_dc, *args),
            'dc:relation': partial(add_relation_dc, *args),
            'dc:rights': partial(add_rights_dc, *args),
            'dc:coverage': partial(add_coverage_dc, *args),
            'dc:source': partial(add_source_dc, *args),
            'dc:format': partial(add_format_dc, *args)
        }

        tags = self.json['record']['metadata']['oai_dc:dc']
        for t in tags:
            if t in add_funcs:
                if not isinstance(tags[t], list):
                    metadata = [tags[t]]
                else:
                    metadata = tags[t]
                add_funcs[t](metadata)
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

        item_type_mapping = Mapping.get_record(self.itemtype.id)
        item_map = get_full_mapping(item_type_mapping, "jpcoar_mapping")

        args = [self.itemtype.schema.get('properties'), item_map, res]

        add_funcs = {
            'dc:title':
                partial(add_title, *args),
            'dcterms:alternative':
                partial(add_alternative, *args),
            'jpcoar:creator':
                partial(add_creator_jpcoar, *args),
            'jpcoar:contributor':
                partial(add_contributor_jpcoar, *args),
            'dcterms:accessRights':
                partial(add_access_right, *args),
            'rioxxterms:apc':
                partial(add_apc, *args),
            'dc:rights':
                partial(add_right, *args),
            'jpcoar:subject':
                partial(add_subject, *args),
            'datacite:description':
                partial(add_description, *args),
            'dc:publisher':
                partial(add_publisher, *args),
            'datacite:date':
                partial(add_date, *args),
            'dc:language':
                partial(add_language, *args),
            'datacite:version':
                partial(add_version, *args),
            'oaire:version':
                partial(add_version_type, *args),
            'jpcoar:identifierRegistration':
                partial(add_identifier_registration, *args),
            'dcterms:temporal':
                partial(add_temporal, *args),
            'datacite:geoLocation':
                partial(add_geo_location, *args),
            'jpcoar:sourceIdentifier':
                partial(add_source_identifier, *args),
            'jpcoar:sourceTitle':
                partial(add_source_title, *args),
            'jpcoar:volume':
                partial(add_volume, *args),
            'jpcoar:issue':
                partial(add_issue, *args),
            'jpcoar:numPages':
                partial(add_num_page, *args),
            'jpcoar:pageStart':
                partial(add_page_start, *args),
            'jpcoar:pageEnd':
                partial(add_page_end, *args),
            'dcndl:dissertationNumber':
                partial(add_dissertation_number, *args),
            'dcndl:dateGranted':
                partial(add_date_granted, *args),
            'dc:type':
                partial(add_resource_type, *args),
            'jpcoar:relation':
                partial(add_relation, *args),
            'jpcoar:degreeGrantor':
                partial(add_degree_grantor, *args),
            'dcndl:degreeName':
                partial(add_degree_name, *args),
            'jpcoar:conference':
                partial(add_conference, *args),
            'jpcoar:fundingReference':
                partial(add_funding_reference, *args),
            'jpcoar:rightsHolder':
                partial(add_rights_holder, *args),
            'jpcoar:file':
                partial(add_file, *args),
            'jpcoar:identifier':
                partial(add_identifier, *args),
            'jpcoar:publisher':
                partial(add_publisher_jpcoar, *args),
            'dcterms:date':
                partial(add_date_dcterms, *args),
            'dcndl:edition':
                partial(add_edition, *args),
            'dcndl:volumeTitle':
                partial(add_volumeTitle, *args),
            'dcndl:originalLanguage':
                partial(add_originalLanguage, *args),
            'dcterms:extent':
                partial(add_extent, *args),
            'jpcoar:format':
                partial(add_format, *args),
            'jpcoar:holdingAgent':
                partial(add_holdingAgent, *args),
            'jpcoar:datasetSeries':
                partial(add_datasetSeries, *args),
            'jpcoar:catalog':
                partial(add_catalog, *args),
        }

        tags = self.json['record']['metadata']['jpcoar:jpcoar']

        for t in tags:
            if t in add_funcs:
                if not isinstance(tags[t], list):
                    metadata = [tags[t]]
                else:
                    metadata = tags[t]
                add_funcs[t](metadata)

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
            item_map = get_mapping(self.itemtype.id, "ddi_mapping")
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
                    else:# isinstance(current_temp[i_r], list):
                        if current_temp[i_r]:
                            current_temp[i_r][0].update(val)
                        else:
                            current_temp[i_r].append(val)
                    # break
                elif i_r in current_temp:
                    current_temp = current_temp[i_r][0]
                    target = target[i_r][0]
                else:# i_r not in current_temp:
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
                            val = {TEXT: val}
                        elif isinstance(val, list):
                            for i in range(len(val)):
                                if isinstance(val[i], str):
                                    val[i] = {TEXT: val[i]}

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
                data_mapping = {TEXT: data_mapping}
                if dict_data.get(current_key):
                    dict_data[current_key].append(data_mapping)
                else:
                    dict_data[current_key] = [data_mapping]

        def parse_to_obj_data_by_mapping_keys(vals, keys):
            """Parse all data to type of object by mapping key."""
            def get_same_key_from_form(sub_key):
                """Get the same key with sub_key in form."""
                for item_sub_key_form in item_sub_keys_form:
                    if item_sub_key_form.replace("[]", "") in sub_key.split(','):
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
                if {"full": full_key_val_obj, "key": sub_keys_clone, "val": {last_key: parse_data}} not in temp_lst:
                    temp_lst.append(
                        {"full": full_key_val_obj,
                         "key": sub_keys_clone,
                         "val": {last_key: parse_data}})

            try:
                list_result = []
                list_temp = []
                root_key = ''
                for val_obj in vals:
                    temp_lst = []
                    for key_pair in keys:
                        for mapping_key, item_sub_key in key_pair.items():
                            #current_app.logger.debug('mapping key:  %s , item_sub_key:  %s' % (mapping_key,item_sub_key))
                            item_sub_key = get_same_key_from_form(item_sub_key)
                            sub_keys = item_sub_key.split('.')
                            root_key = sub_keys[0]
                            last_key = sub_keys.pop()
                            sub_keys_clone = copy.deepcopy(sub_keys)
                            if mapping_key.split(".@")[1] == "value":
                                if val_obj.get(TEXT):
                                    value = val_obj[TEXT].replace(
                                        '\n', '$NEWLINE')
                                    soup = BeautifulSoup(value, "html.parser")
                                    for tag in soup.find_all():
                                        tag.unwrap()
                                    value = soup.get_text(strip=True). \
                                        replace('$NEWLINE', '\n').replace(
                                            '\xa0', ' ')
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
                        if root_key.replace("[]", "") in result_dict and isinstance(result_dict[root_key.replace("[]", "")],
                                                                                    list):
                            temp_data = result_dict[root_key.replace(
                                "[]", "")][0]
                            if temp_data.values() \
                                    and isinstance(list(temp_data.values())[0], str):
                                temp_set = set(temp_data.values()) - set(['ja', 'en'])
                                if temp_set not in list_temp:
                                    list_temp.append(temp_set)
                                    list_result.append(temp_data)
                            else:
                                if temp_data not in list_result:
                                    list_result.append(temp_data)
                        else: # root_key.replace("[]", "") in result_dict and isinstance(
                                #result_dict[root_key.replace("[]", "")], dict):
                            temp_data = result_dict[root_key.replace("[]", "")]
                            temp_set = set(temp_data.values()) - set(['ja', 'en'])
                            if temp_set not in list_temp:
                                list_temp.append(temp_set)
                                list_result.append(temp_data)
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
        temp_list = []
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
            if lst_keys_with_prefix:
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
            # set resourcetype
            type = [{"resourcetype": "dataset","resourceuri": "http://purl.org/coar/resource_type/c_ddb1"}]
            res['type'] = type
            return res


class JsonMapper(BaseMapper):
    """ Mapper to map from Json format file to ItemType.

        The original file to be mapped by this Mapper is assumed to be a
        JSON-LD or a file described in JSON.

        The information to be used for this mapper mapping is created and used
        based on the contents of item_type.schema.

        In this Mapper, do not write your own mapping code for individual
        items, but implement mapping by the rules of item_type.schema,
        JSON-LD or JSON description format.

    """
    def __init__(self, json, itemtype_name):
        self.json = json
        self.itemtype_name = itemtype_name

        if not BaseMapper.itemtype_map:
            BaseMapper.update_itemtype_map()

        for item in BaseMapper.itemtype_map:
            if self.itemtype_name == item:
                self.itemtype = BaseMapper.itemtype_map.get(item)

    def map_itemtype(self, type_tag):
        """Map itemtype."""
        self.itemtype = BaseMapper.itemtype_map[self.itemtype_name]

    def _create_item_map(self):
        """ Create Mapping information from ItemType.

            This mapping information consists of the following.

                KEY: Identifier for the ItemType item
                     (value obtained by concatenating the “title”
                     attribute of each item in the schema)
                VALUE: Item Code. Subitem code identifier.

            Returns:
                item_map: Mapping information about ItemType.

            Examples:
                For example, in the case of “Title of BioSample of ItemType”,
                it would be as follows.

                KEY: title.Title
                VALUE: item_1723710826523.subitem_1551255647225
        """

        item_map = {}
        for prop_k, prop_v in self.itemtype.schema['properties'].items():
            self._apply_property(item_map, '', '', prop_k, prop_v)
        return item_map

    def _apply_property(self, item_map, key, value, prop_k, prop_v):
        """
            This process is part of “_create_item_map” and is not
            intended for any other use.
        """
        if 'title' in prop_v:
            key = key + '.' + prop_v['title'] if key else prop_v['title']
            value = value + '.' + prop_k if value else prop_k

        if prop_v['type'] == 'object':
            for child_k, child_v in prop_v['properties'].items():
                self._apply_property(item_map, key, value, child_k, child_v)
        elif prop_v['type'] == 'array':
            self._apply_property(item_map, key, value,
                                 'items', prop_v['items'])
        else:
            item_map[key] = value

    def _create_metadata(self, item_map, json_map):
        """ Create Metadata.

            For the parameter “item_map”, see “_create_item_map”.
            The parameter “json_map” is assumed to be
            the following information.

                KEY: KEY similar to the KEY information in “item_map”.
                VALUE: Information that is the path to the target
                       item in the json file.
                       To assign multiple json values to a single ItemType
                       item, define the values as an array.

            For the same KEY in item_map and json_map,
            link the json file value to the item code.

            Args:
                item_map: Mapping information for ItemyType
                json_map: Mapping information in Json file

            Returns:
                result: Metadata corresponding to ItemType

            Example
                For example, in the case of “Title of BioSample of ItemType”,
                it would be as follows.

                item_map:
                    KEY: title.Title
                    VALUE: item_1723710826523.subitem_1551255647225
                json_map;
                    KEY: title.Title
                    VALUE: title

                Combining the above, the “title” value in the json file is
                defined as the Metadata for
                “item_1723710826523.subitem_1551255647225”.
        """

        result = {}
        for k, v in json_map.items():
            if isinstance(v, list):
                # Assign multiple json values to ItemType items
                for cv in v:
                    self._apply_item_metadata(result, k, cv, item_map)
            else:
                self._apply_item_metadata(result, k, v, item_map)

        return result

    def _apply_item_metadata(self, metadata, item_map_key, json_key_path,
                             item_map):
        """
            This process is part of “_create_metadata” and is not
            intended for any other use.
        """

        json_keys = json_key_path.split('.')
        json_key = json_keys[0]
        value = self.json['record']['metadata'].get(json_key)
        if value:
            # Perform processing only if there are values to be set
            # in the json file.
            item_path = item_map[item_map_key]

            item_paths = item_path.split('.')
            item_key = item_paths[0]
            if isinstance(value, list):
                # If the json value is a List.
                if not metadata.get(item_key):
                    # If Metadata does not yet have a definition,
                    # create a container array.
                    metadata[item_key] = []
                for i, v in enumerate(value):
                    # If the json value is a List, the element is a dict.
                    # If there is no dict container for the element,
                    # a container is created.
                    if i >= len(metadata[item_key]):
                        metadata[item_key].append({})
                    self._apply_child_metadata(metadata[item_key][i], v,
                                               json_keys[1:], item_paths[1:])
            else:
                # If the json value is not a List.
                if not metadata.get(item_key):
                    # If Metadata does not yet have a definition,
                    # create a dict that will serve as a container.
                    metadata[item_key] = {}
                self._apply_child_metadata(
                            metadata[item_key],
                            self.json['record']['metadata'],
                            json_keys, item_paths[1:])

    def _apply_child_metadata(self, child_metadata, json_data, json_keys,
                              subitem_keys):
        """
            This process is part of “_create_metadata” and is not
            intended for any other use.
        """
        json_key = json_keys[0]
        value = json_data.get(json_key)
        if not value:
            # Perform processing only if there are values
            # to be set in the json file.
            return
        elif isinstance(value, dict):
            if len(subitem_keys) == 1:
                # If the subitem code is fixed, the item
                # to be retrieved is fixed.
                if value.get(json_keys[1]):
                    child_metadata[subitem_keys[0]] = str(value[json_keys[1]])
            else:
                if not child_metadata.get(subitem_keys[0]):
                    # If Metadata does not yet have a definition,
                    # create a dict that will serve as a container.
                    child_metadata[subitem_keys[0]] = {}
                self._apply_child_metadata(
                    child_metadata[subitem_keys[0]],
                    value, json_keys[1:], subitem_keys[1:])
        else:
            if len(subitem_keys) == 1:
                # If the subitem code is fixed, the item
                #  to be retrieved is fixed.
                child_metadata[subitem_keys[0]] = str(value)
            else:
                if not child_metadata.get(subitem_keys[0]):
                    # If Metadata does not yet have a definition,
                    # create a dict that will serve as a container.
                    child_metadata[subitem_keys[0]] = {}
                if child_metadata[subitem_keys[0]].get(subitem_keys[1:][0]):
                    # The case where multiple json values are set for
                    # one item of ItemType.
                    child_metadata[subitem_keys[0]] = [
                        child_metadata[subitem_keys[0]]]
                    child_metadata[subitem_keys[0]].append({})
                    self._apply_child_metadata(
                        child_metadata[subitem_keys[0]][-1],
                        json_data, json_keys, subitem_keys[1:])
                else:
                    self._apply_child_metadata(
                        child_metadata[subitem_keys[0]],
                        json_data, json_keys, subitem_keys[1:])


class BIOSAMPLEMapper(JsonMapper):
    """
       Mapper for BioSample. Please refer to JsonMapper
       for details on how to use it.
    """
    def __init__(self, json):
        """Init."""
        super().__init__(json, 'Biosample')

    def map(self):
        if self.is_deleted():
            return {}

        res = {'$schema': self.itemtype.id,
               'pubdate': str(self.datestamp())}

        item_map = self._create_item_map()
        json_map = {
            'identifier.入力内容': 'identifier',
            'type.入力内容': 'type',
            'title.Title': 'title',
            'sameAs.関連名称.関連名称': ['sameAs.identifier', 'sameAs.type'],
            'sameAs.関連識別子.関連識別子': 'sameAs.url',
            'organism.Organism Identifier': 'organism.identifier',
            'organism.Organism Name': 'organism.name',
            'attributes.Attribute Name': 'attribute.attribute_name',
            'attributes.Attribute Display Name': 'attribute.display_name',
            'attributes.Attribute Harmonized Name':
                'attribute.harmonized_name',
            'attributes.Attribute Content': 'attribute.content',
            'description.入力内容': 'description',
            'Model Name.入力内容': 'model.name',
            'package.Package Display Name': 'Package.display_name',
            'package.Package Name': 'Package.name',
            'dbXrefs.関連名称.関連名称': ['dbXrefs.identifier', 'dbXrefs.type'],
            'dbXrefs.関連識別子.関連識別子': 'dbXrefs.url',
            'dbXrefsStatistics.Statistic Count': 'dbXrefsStatistics.count',
            'dbXrefsStatistics.Statistic Type': 'dbXrefsStatistics.type',
            'distribution.Distribution URL': 'distribution.contentUrl',
            'distribution.Distribution Format': 'distribution.encodingFormat',
            'distribution.Distribution Type': 'distribution.type',
            'downloadUrl.Download Name': 'downloadUrl.name',
            'downloadUrl.Download FTP URL': 'downloadUrl.ftpUrl',
            'downloadUrl.Download Type': 'downloadUrl.type',
            'downloadUrl.Download URL': 'downloadUrl.url',
            'status.入力内容': 'status',
            'visibility.入力内容': 'visibility',
            'dateCreated.日付': 'dateCreated',
            'dateModified.日付': 'dateModified',
            'datePublished.日付': 'datePublished',
            'isPartOf.入力内容': 'isPartOf',
            'name.入力内容': 'name',
            'url.識別子': 'url'
        }
        metadata = self._create_metadata(item_map, json_map)

        """ resourcetype.Type Setting """
        item_path = item_map['resourcetype.Type']
        item_paths = item_path.split('.')
        metadata[item_paths[0]] = {}
        metadata[item_paths[0]][item_paths[1]] = 'dataset'
        res = {**res, **metadata}

        return res


class BIOPROJECTMapper(JsonMapper):
    """
       Mapper for BioProject. Please refer to JsonMapper
       for details on how to use it.
    """
    def __init__(self, json):
        """Init."""
        super().__init__(json, 'Bioproject')

    def map(self):
        if self.is_deleted():
            return {}

        res = {'$schema': self.itemtype.id,
               'pubdate': str(self.datestamp())}

        item_map = self._create_item_map()
        json_map = {
            'identifier.入力内容': 'identifier',
            'type.入力内容': 'type',
            'objectType.入力内容': 'objectType',
            'organism.Organism Identifier': 'organism.identifier',
            'organism.Organism Name': 'organism.name',
            'title.Title': 'title',
            'description.内容記述': 'description',
            'publication.Publication Date': 'publication.date',
            'publication.Publication Id': 'publication.id',
            'publication.Publication Status': 'publication.status',
            'publication.Publication Reference': 'publication.Reference',
            'publication.Publication Db Type': 'publication.DbType',
            'grant.Grant Id': 'grant.id',
            'grant.Grant Title': 'grant.title',
            'grant.Agency.Agency Abberiation': 'grant.agency.abbreviation',
            'grant.Agency.Agency Name': 'grant.agency.name',
            'externalLink.関連識別子.関連識別子': 'externalLink.URL',
            'externalLink.関連名称.関連名称': 'externalLink.label',
            'distribution.Distribution URL': 'distribution.contentUrl',
            'distribution.Distribution Format': 'distribution.encodingFormat',
            'distribution.Distribution Type': 'distribution.type',
            'download.入力内容': 'download',
            'status.入力内容': 'status',
            'visibility.入力内容': 'visibility',
            'dateCreated.日付': 'dateCreated',
            'dateModified.日付': 'dateModified',
            'datePublished.日付': 'datePublished',
            'isPartOf.入力内容': 'isPartOf',
            'name.入力内容': 'name',
            'url.識別子': 'url',
            'dbXrefs.関連名称.関連名称': ['dbXrefs.identifier', 'dbXrefs.type'],
            'dbXrefs.関連識別子.関連識別子': 'dbXrefs.url'
        }

        metadata = self._create_metadata(item_map, json_map)

        """ resourcetype.Type Setting """
        item_path = item_map['resourcetype.Type']
        item_paths = item_path.split('.')
        metadata[item_paths[0]] = {}
        metadata[item_paths[0]][item_paths[1]] = 'dataset'

        res = {**res, **metadata}
        return res
