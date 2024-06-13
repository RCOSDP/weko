# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Utilities."""

import re
from datetime import datetime
from functools import lru_cache, partial

from flask import current_app
from invenio_base.utils import obj_or_import_string
from lxml import etree
from lxml.builder import E
from lxml.etree import Element

from .proxies import current_oaiserver

ns = {
    None: "http://datacite.org/schema/kernel-4",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "xml": "xml",
}

NS_EPRINTS = {None: "http://www.openarchives.org/OAI/2.0/eprints"}
EPRINTS_SCHEMA_LOCATION = "http://www.openarchives.org/OAI/2.0/eprints"
EPRINTS_SCHEMA_LOCATION_XSD = "http://www.openarchives.org/OAI/2.0/eprints.xsd"

NS_OAI_IDENTIFIER = {None: "http://www.openarchives.org/OAI/2.0/oai-identifier"}
OAI_IDENTIFIER_SCHEMA_LOCATION = "http://www.openarchives.org/OAI/2.0/oai-identifier"
OAI_IDENTIFIER_SCHEMA_LOCATION_XSD = (
    "http://www.openarchives.org/OAI/2.0/oai-identifier.xsd"
)

NS_FRIENDS = {None: "http://www.openarchives.org/OAI/2.0/friends/"}
FRIENDS_SCHEMA_LOCATION = "http://www.openarchives.org/OAI/2.0/friends/"
FRIENDS_SCHEMA_LOCATION_XSD = "http://www.openarchives.org/OAI/2.0/friends/.xsd"


@lru_cache(maxsize=100)
def serializer(metadata_prefix):
    """Return etree_dumper instances.

    :param metadata_prefix: One of the metadata identifiers configured in
        ``OAISERVER_METADATA_FORMATS``.
    """
    metadataFormats = current_app.config["OAISERVER_METADATA_FORMATS"]
    serializer_ = metadataFormats[metadata_prefix]["serializer"]
    if isinstance(serializer_, tuple):
        return partial(obj_or_import_string(serializer_[0]), **serializer_[1])
    return obj_or_import_string(serializer_)


def dumps_etree(pid, record, **kwargs):
    """Dump MARC21 compatible record.

    :param pid: The :class:`invenio_pidstore.models.PersistentIdentifier`
        instance.
    :param record: The :class:`invenio_records.api.Record` instance.
    :returns: A LXML Element instance.
    """
    from dojson.contrib.to_marc21 import to_marc21
    from dojson.contrib.to_marc21.utils import dumps_etree

    return dumps_etree(to_marc21.do(record["_source"]), **kwargs)


def datetime_to_datestamp(dt, day_granularity=False):
    """Transform datetime to datestamp.

    :param dt: The datetime to convert.
    :param day_granularity: Set day granularity on datestamp.
    :returns: The datestamp.
    """
    # assert dt.tzinfo is None  # only accept timezone naive datetimes
    # ignore microseconds
    if type(dt) == str:
        dt = datetime.fromisoformat(dt)

    dt = dt.replace(microsecond=0, tzinfo=None)
    result = dt.isoformat() + "Z"
    if day_granularity:
        result = result[:-10]
    return result


def eprints_description(
    metadataPolicy, dataPolicy, submissionPolicy=None, content=None
):
    """Generate the eprints element for the identify response.

    The eprints container is used by the e-print community to describe
    the content and policies of repositories.
    For the full specification and schema definition visit:
    http://www.openarchives.org/OAI/2.0/guidelines-eprints.htm
    """
    eprints = Element(etree.QName(NS_EPRINTS[None], "eprints"), nsmap=NS_EPRINTS)
    eprints.set(
        etree.QName(ns["xsi"], "schemaLocation"),
        "{0} {1}".format(EPRINTS_SCHEMA_LOCATION, EPRINTS_SCHEMA_LOCATION_XSD),
    )
    if content:
        contentElement = etree.Element("content")
        for key, value in content.items():
            contentElement.append(E(key, value))
        eprints.append(contentElement)

    metadataPolicyElement = etree.Element("metadataPolicy")
    for key, value in metadataPolicy.items():
        metadataPolicyElement.append(E(key, value))
        eprints.append(metadataPolicyElement)

    dataPolicyElement = etree.Element("dataPolicy")
    for key, value in dataPolicy.items():
        dataPolicyElement.append(E(key, value))
        eprints.append(dataPolicyElement)

    if submissionPolicy:
        submissionPolicyElement = etree.Element("submissionPolicy")
        for key, value in submissionPolicy.items():
            submissionPolicyElement.append(E(key, value))
        eprints.append(submissionPolicyElement)
    return etree.tostring(eprints, pretty_print=True)


def oai_identifier_description(
    scheme, repositoryIdentifier, delimiter, sampleIdentifier
):
    """Generate the oai-identifier element for the identify response.

    The OAI identifier format is intended to provide persistent resource
    identifiers for items in repositories that implement OAI-PMH.
    For the full specification and schema definition visit:
    http://www.openarchives.org/OAI/2.0/guidelines-oai-identifier.htm
    """
    oai_identifier = Element(
        etree.QName(NS_OAI_IDENTIFIER[None], "oai_identifier"), nsmap=NS_OAI_IDENTIFIER
    )
    oai_identifier.set(
        etree.QName(ns["xsi"], "schemaLocation"),
        "{0} {1}".format(
            OAI_IDENTIFIER_SCHEMA_LOCATION, OAI_IDENTIFIER_SCHEMA_LOCATION_XSD
        ),
    )
    oai_identifier.append(E("scheme", scheme))
    oai_identifier.append(E("repositoryIdentifier", repositoryIdentifier))
    oai_identifier.append(E("delimiter", delimiter))
    oai_identifier.append(E("sampleIdentifier", sampleIdentifier))
    return etree.tostring(oai_identifier, pretty_print=True)


def friends_description(baseURLs):
    """Generate the friends element for the identify response.

    The friends container is recommended for use by repositories
    to list confederate repositories.
    For the schema definition visit:
    http://www.openarchives.org/OAI/2.0/guidelines-friends.htm
    """
    friends = Element(etree.QName(NS_FRIENDS[None], "friends"), nsmap=NS_FRIENDS)
    friends.set(
        etree.QName(ns["xsi"], "schemaLocation"),
        "{0} {1}".format(FRIENDS_SCHEMA_LOCATION, FRIENDS_SCHEMA_LOCATION_XSD),
    )
    for baseURL in baseURLs:
        friends.append(E("baseURL", baseURL))
    return etree.tostring(friends, pretty_print=True)


def sanitize_unicode(value):
    """Removes characters incompatible with XML1.0.

    Following W3C recommandation : https://www.w3.org/TR/REC-xml/#charsets
    Based on https://lsimons.wordpress.com/2011/03/17/stripping-illegal-characters-out-of-xml-in-python/ # noqa
    """
    return re.sub("[\x00-\x08\x0B\x0C\x0E-\x1F\uD800-\uDFFF\uFFFE\uFFFF]", "", value)


def record_sets_fetcher(record):
    """Fetch a record's sets."""
    return record.get("_oai", {}).get("sets", [])


def getrecord_fetcher(record_uuid):
    """Fetch record data as dict for serialization."""
    record = current_oaiserver.record_cls.get_record(record_uuid)
    record_dict = record.dumps()
    record_dict["updated"] = record.updated
    return record_dict
