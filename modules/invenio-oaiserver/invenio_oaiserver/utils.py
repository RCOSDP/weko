# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Utilities."""

from __future__ import absolute_import, print_function

from datetime import datetime
from functools import partial

from flask import current_app
from lxml import etree
from lxml.builder import E
from lxml.etree import Element
from weko_index_tree.api import Indexes
from weko_schema_ui.schema import get_oai_metadata_formats
from werkzeug.utils import import_string

try:
    from functools import lru_cache
except ImportError:  # pragma: no cover
    from functools32 import lru_cache

ns = {
    None: 'http://datacite.org/schema/kernel-4',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'xml': 'xml',
}

NS_EPRINTS = {None: 'http://www.openarchives.org/OAI/2.0/eprints'}
EPRINTS_SCHEMA_LOCATION = 'http://www.openarchives.org/OAI/2.0/eprints'
EPRINTS_SCHEMA_LOCATION_XSD = \
    'http://www.openarchives.org/OAI/2.0/eprints.xsd'

NS_OAI_IDENTIFIER = {None:
                     'http://www.openarchives.org/OAI/2.0/oai-identifier'}
OAI_IDENTIFIER_SCHEMA_LOCATION = \
    'http://www.openarchives.org/OAI/2.0/oai-identifier'
OAI_IDENTIFIER_SCHEMA_LOCATION_XSD = \
    'http://www.openarchives.org/OAI/2.0/oai-identifier.xsd'

NS_FRIENDS = {None: 'http://www.openarchives.org/OAI/2.0/friends/'}
FRIENDS_SCHEMA_LOCATION = 'http://www.openarchives.org/OAI/2.0/friends/'
FRIENDS_SCHEMA_LOCATION_XSD = \
    'http://www.openarchives.org/OAI/2.0/friends/.xsd'

OUTPUT_HARVEST = 3
HARVEST_PRIVATE = 2
PRIVATE_INDEX = 1


@lru_cache(maxsize=100)
def serializer(metadata_prefix):
    """Return etree_dumper instances.

    :param metadata_prefix: One of the metadata identifiers configured in
        ``OAISERVER_METADATA_FORMATS``.
    """
    metadataFormats = get_oai_metadata_formats(current_app)
    serializer_ = metadataFormats[metadata_prefix]['serializer']

    if isinstance(serializer_, tuple):
        return partial(import_string(serializer_[0]), **serializer_[1])
    return import_string(serializer_)


def dumps_etree(pid, record, **kwargs):
    """Dump MARC21 compatible record.

    :param pid: The :class:`invenio_pidstore.models.PersistentIdentifier`
        instance.
    :param record: The :class:`invenio_records.api.Record` instance.
    :returns: A LXML Element instance.
    """
    from dojson.contrib.to_marc21 import to_marc21
    from dojson.contrib.to_marc21.utils import dumps_etree

    return dumps_etree(to_marc21.do(record['_source']), **kwargs)


def datetime_to_datestamp(dt, day_granularity=False):
    """Transform datetime to datestamp.

    :param dt: The datetime to convert.
    :param day_granularity: Set day granularity on datestamp.
    :returns: The datestamp.
    """
    # assert dt.tzinfo is None  # only accept timezone naive datetimes
    # ignore microseconds
    dt = dt.replace(microsecond=0)
    result = dt.isoformat() + 'Z'
    if day_granularity:
        result = result[:-10]
    return result


def eprints_description(metadataPolicy, dataPolicy,
                        submissionPolicy=None, content=None):
    """Generate the eprints element for the identify response.

    The eprints container is used by the e-print community to describe
    the content and policies of repositories.
    For the full specification and schema definition visit:
    http://www.openarchives.org/OAI/2.0/guidelines-eprints.htm
    """
    eprints = Element(etree.QName(NS_EPRINTS[None], 'eprints'),
                      nsmap=NS_EPRINTS)
    eprints.set(etree.QName(ns['xsi'], 'schemaLocation'),
                '{0} {1}'.format(EPRINTS_SCHEMA_LOCATION,
                                 EPRINTS_SCHEMA_LOCATION_XSD))
    if content:
        contentElement = etree.Element('content')
        for key, value in content.items():
            contentElement.append(E(key, value))
        eprints.append(contentElement)

    metadataPolicyElement = etree.Element('metadataPolicy')
    for key, value in metadataPolicy.items():
        metadataPolicyElement.append(E(key, value))
        eprints.append(metadataPolicyElement)

    dataPolicyElement = etree.Element('dataPolicy')
    for key, value in dataPolicy.items():
        dataPolicyElement.append(E(key, value))
        eprints.append(dataPolicyElement)

    if submissionPolicy:
        submissionPolicyElement = etree.Element('submissionPolicy')
        for key, value in submissionPolicy.items():
            submissionPolicyElement.append(E(key, value))
        eprints.append(submissionPolicyElement)
    return etree.tostring(eprints, pretty_print=True)


def oai_identifier_description(scheme, repositoryIdentifier,
                               delimiter, sampleIdentifier):
    """Generate the oai-identifier element for the identify response.

    The OAI identifier format is intended to provide persistent resource
    identifiers for items in repositories that implement OAI-PMH.
    For the full specification and schema definition visit:
    http://www.openarchives.org/OAI/2.0/guidelines-oai-identifier.htm
    """
    oai_identifier = Element(etree.QName(NS_OAI_IDENTIFIER[None],
                             'oai_identifier'),
                             nsmap=NS_OAI_IDENTIFIER)
    oai_identifier.set(etree.QName(ns['xsi'], 'schemaLocation'),
                       '{0} {1}'.format(OAI_IDENTIFIER_SCHEMA_LOCATION,
                                        OAI_IDENTIFIER_SCHEMA_LOCATION_XSD))
    oai_identifier.append(E('scheme', scheme))
    oai_identifier.append(E('repositoryIdentifier', repositoryIdentifier))
    oai_identifier.append(E('delimiter', delimiter))
    oai_identifier.append(E('sampleIdentifier', sampleIdentifier))
    return etree.tostring(oai_identifier, pretty_print=True)


def friends_description(baseURLs):
    """Generate the friends element for the identify response.

    The friends container is recommended for use by repositories
    to list confederate repositories.
    For the schema definition visit:
    http://www.openarchives.org/OAI/2.0/guidelines-friends.htm
    """
    friends = Element(etree.QName(NS_FRIENDS[None], 'friends'),
                      nsmap=NS_FRIENDS)
    friends.set(etree.QName(ns['xsi'], 'schemaLocation'),
                '{0} {1}'.format(FRIENDS_SCHEMA_LOCATION,
                                 FRIENDS_SCHEMA_LOCATION_XSD))
    for baseURL in baseURLs:
        friends.append(E('baseURL', baseURL))
    return etree.tostring(friends, pretty_print=True)


def handle_license_free(record_metadata):
    """Merge licensetype and licensefree.

    Delete licensetype when licensetype equal 'license_free'
    but licensefree is empty.

    :param record_metadata: Record's Metadata.
    :returns: Directed edit.
    """
    _license_type = 'licensetype'
    _license_free = 'licensefree'
    _license_type_free = 'license_free'
    _attribute_type = 'file'
    _attribute_value_mlt = 'attribute_value_mlt'

    _license_dict = current_app.config['WEKO_RECORDS_UI_LICENSE_DICT']
    if _license_dict:
        _license_type_free = _license_dict[0].get('value')

    for val in record_metadata.values():
        if isinstance(val, dict) and \
                val.get('attribute_type') == _attribute_type:
            for attr in val.get(_attribute_value_mlt, {}):
                if attr.get(_license_type) == _license_type_free:
                    if attr.get(_license_free):
                        attr[_license_type] = attr.get(_license_free)
                        del attr[_license_free]
                    else:
                        del attr[_license_type]

    return record_metadata


def get_index_state():
    from weko_records_ui.utils import is_future
    index_state = {}
    ids = Indexes.get_all_indexes()
    for index in ids:
        index_id = str(index.id)
        if not index.harvest_public_state:
            index_state[index_id] = {
                'parent': None,
                'msg': HARVEST_PRIVATE
            }
        elif '-99' not in index.browsing_role \
                or not index.public_state \
                or (index.public_date and
                    is_future(index.public_date)):
            index_state[index_id] = {
                'parent': None,
                'msg': PRIVATE_INDEX
            }
        else:
            index_state[index_id] = {
                'parent': str(index.parent),
                'msg': OUTPUT_HARVEST
            }
    return index_state


def is_output_harvest(path_list, index_state):
    def _check(index_id):
        if index_id in index_state:
            if not index_state[index_id]['parent'] \
                    or index_state[index_id]['parent'] == '0':
                return index_state[index_id]['msg']
            else:
                return _check(index_state[index_id]['parent'])
        else:
            return HARVEST_PRIVATE

    result = 0
    for path in path_list:
        current_app.logger.debug(path)
        index_id = path.split('/')[-1]
        result = max([result, _check(index_id)])
    return result if result != 0 else HARVEST_PRIVATE


def get_community_index_from_set(set):
    """Get community index from set.
    
    Args:
        set (str): Set string.
    
    Returns:
        str: index_id of community.
    """
    from invenio_communities.models import Community
    com_prefix = current_app.config['COMMUNITIES_OAI_FORMAT'].replace(
        '{community_id}', '')
    com_id = set.replace(com_prefix, '')
    com = Community.query.filter_by(id=com_id).first()
    return str(com.root_node_id) if com else None