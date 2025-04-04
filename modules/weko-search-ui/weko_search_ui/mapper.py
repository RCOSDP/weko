# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Search-Ui is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Harvest records from an OAI-PMH repository."""

import os
import re
import json
import itertools
import xmltodict
from datetime import date
from functools import partial
from rocrate.rocrate import ROCrate
from rocrate.model.contextentity import ContextEntity

from flask import current_app, url_for

from weko_records.api import Mapping, ItemTypes, FeedbackMailList, ItemLink
from weko_records.models import ItemType
from weko_records.serializers.utils import get_full_mapping

from .config import ROCRATE_METADATA_FILE

DEFAULT_FIELD = [
    "title",
    "keywords",
    "keywords_en",
    "pubdate",
    "lang",
    "item_titles",
    "item_language",
    "item_keyword",
]


DDI_MAPPING_KEY_TITLE = "stdyDscr.citation.titlStmt.titl.@value"
DDI_MAPPING_KEY_URI = "stdyDscr.citation.holdings.@value"

TEXT = "#text"
LANG = "@xml:lang"


def get_subitem_text_key(*element_names):
    if element_names:
        return ".".join(list(element_names) + [TEXT])
    return ""


def get_subitem_lang_key(*element_names):
    if element_names:
        return ".".join(list(element_names) + [LANG])
    return ""


def subitem_recs(schema, keys, value, metadata):
    """Generate subitem metadata.

    Args:
        schema ([type]): [description]
        keys ([type]): [description]
        value ([type]): [description]
        metadata ([type]): [description]

    Returns:
        [type]: [description]

    """
    subitems = None
    item_key = keys[0] if keys else None
    if schema.get("items", {}).get("properties", {}).get(item_key):
        subitems = []
        if len(keys) > 1:
            _subitems = subitem_recs(
                schema["items"]["properties"][item_key],
                keys[1:],
                value,
                metadata
            )
            if _subitems:
                subitems.append(_subitems)
        else:
            if "." in value:
                _v = value.split(".")
                if len(_v) > 2 or not metadata.get(_v[0]):
                    return None

                if isinstance(metadata.get(_v[0]), str) and _v[1] == TEXT:
                    subitems.append({item_key: metadata.get(_v[0], "")})
                elif isinstance(metadata.get(_v[0]), list):
                    for item in metadata.get(_v[0]):
                        if isinstance(item, str):
                            subitems.append({item_key: item})
                        else:
                            subitems.append({item_key: item.get(_v[1], "")})
                elif isinstance(metadata.get(_v[0]), dict):
                    subitems.append({item_key: metadata.get(_v[0], {}).get(_v[1], "")})
            else:
                if isinstance(metadata, str) and value == TEXT:
                    subitems.append({item_key: metadata})
                elif isinstance(metadata, dict):
                    subitems.append({item_key: metadata.get(value, "")})
    elif schema.get("properties", {}).get(item_key):
        subitems = {}
        if len(keys) > 1:
            subitems = subitem_recs(
                schema["properties"][item_key], keys[1:], value, metadata
            )
        else:
            if "." in value:
                _v = value.split(".")
                if len(_v) > 2 or not metadata.get(_v[0]):
                    if _v[-1] == TEXT:
                        data = metadata.get(_v[0], {})
                        for v_key in _v[1:-1]:
                            data = data.get(v_key, {})
                        if type(data) == str:
                            subitems[item_key] = data
                    elif len(_v) > 2:
                        subitems[item_key] = (
                            metadata.get(_v[0], {}).get(_v[1], {}).get(_v[2], {})
                        )
                    else:
                        return None
                elif isinstance(metadata.get(_v[0]), str) and _v[1] == TEXT:
                    subitems[item_key] = metadata.get(_v[0])
                elif isinstance(metadata.get(_v[0]), list):
                    subitems[item_key] = metadata.get(_v[0])[0].get(_v[1], "")
                elif isinstance(metadata.get(_v[0]), dict):
                    subitems[item_key] = metadata.get(_v[0], {}).get(_v[1], "")
            else:
                if isinstance(metadata, str) and value == TEXT:
                    subitems[item_key] = metadata
                elif isinstance(metadata, dict):
                    subitems[item_key] = metadata.get(value, "")
    elif not item_key:
        if "." in value:
            _v = value.split(".")
            if len(_v) > 2 or not metadata.get(_v[0]):
                return None

            if isinstance(metadata.get(_v[0]), str) and _v[1] == TEXT:
                subitems = metadata.get(_v[0])
            elif isinstance(metadata.get(_v[0]), list):
                subitems = metadata.get(_v[0])[0].get(_v[1], "")
            elif isinstance(metadata.get(_v[0]), dict):
                subitems = metadata.get(_v[0], {}).get(_v[1], "")
        else:
            if isinstance(metadata, str) and value == TEXT:
                subitems = metadata
            if isinstance(metadata, list):
                subitems = metadata[0]
            elif isinstance(metadata, dict):
                subitems = metadata.get(value, "")
    else:
        current_app.logger.debug("item_key: {0}".format(item_key))

    return subitems


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
    # current_app.logger.warn('{0} {1} {2}: {3}'.format(
    #     __file__, 'parsing_metadata()', 'mappin', mappin))
    # current_app.logger.warn('{0} {1} {2}: {3}'.format(
    #     __file__, 'parsing_metadata()', 'props', props))
    # current_app.logger.warn('{0} {1} {2}: {3}'.format(
    #     __file__, 'parsing_metadata()', 'patterns', patterns))
    # current_app.logger.warn('{0} {1} {2}: {3}'.format(
    #     __file__, 'parsing_metadata()', 'metadata', metadata))
    # current_app.logger.warn('{0} {1} {2}: {3}'.format(
    #     __file__, 'parsing_metadata()', 'res', res))
    mapping_keys = set()
    for pattern in patterns:
        temp_mapping = mappin.get(pattern[0])
        if temp_mapping:
            keys = set([subkey.split(".")[0] for subkey in temp_mapping])
            mapping_keys = mapping_keys.union(keys)

    mapping_keys = list(mapping_keys)
    if not mapping_keys:
        return None, None
    else:
        mapping_keys.sort()

    ret = []
    for item_key in mapping_keys:
        if item_key and props.get(item_key):
            is_item_type_array = ("items" in props[item_key].keys()) and \
                (props[item_key]["type"] == "array")
            if is_item_type_array:
                item_schema = props[item_key]["items"]["properties"]
            elif props[item_key]['type'] == 'object':
                item_schema = props[item_key]["properties"]
            else:
                item_schema = props[item_key]

            ret = []
            for it in metadata:
                items = {}
                for elem, value in patterns:
                    mapping = mappin.get(elem)

                    if mappin.get(elem) and value:
                        mapping.sort()

                        subitems = None
                        if "," in mapping[0]:
                            subitems = mapping[0].split(",")[0].split(".")[1:]
                        else:
                            subitems = mapping[0].split(".")[1:]

                        if subitems:
                            if subitems[0] in item_schema:
                                submetadata = subitem_recs(
                                    item_schema[subitems[0]], subitems[1:], value, it
                                )

                                if submetadata:
                                    if isinstance(submetadata, list):
                                        if items.get(subitems[0]):
                                            if len(items[subitems[0]]) != len(
                                                submetadata
                                            ):
                                                items[subitems[0]].extend(submetadata)
                                                continue

                                            for idx, meta in enumerate(submetadata):
                                                if isinstance(meta, dict):
                                                    items[subitems[0]][idx].update(meta)
                                                else:
                                                    items[subitems[0]].extend(meta)
                                        else:
                                            items[subitems[0]] = submetadata
                                    elif isinstance(submetadata, dict):
                                        if items.get(subitems[0]):
                                            items[subitems[0]].update(submetadata)
                                        else:
                                            items[subitems[0]] = submetadata
                                    else:
                                        items[subitems[0]] = submetadata
                if items:
                    ret.append(items)

            if item_key and ret:
                if not is_item_type_array and len(ret) == 1:
                    res[item_key] = ret[0]
                elif item_key in res:
                    res[item_key].extend(ret)
                else:
                    res[item_key] = ret

    if item_key and ret:
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
        ("title.@value", TEXT),
        ("title.@attributes.xml:lang", LANG)
    ]

    item_key, ret = parsing_metadata(mapping, schema, patterns, metadata, res)

    if item_key and ret:
        if isinstance(metadata[0], str):
            res["title"] = metadata[0]
        elif isinstance(metadata[0], dict):
            res["title"] = metadata[0].get(TEXT)


def add_alternative(schema, mapping, res, metadata):
    """Add titles other than the main title such as the \
    title for a contents page or colophon."""
    patterns = [
        ("alternative.@value", TEXT),
        ("alternative.@attributes.xml:lang", LANG),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_creator_jpcoar(schema, mapping, res, metadata):
    """Add individual or organisation that is responsible for \
    the creation of the resource."""
    patterns = [
        ("creator.@attributes.creatorType", "@creatorType"),
        # jpcoar:nameIdentifier
        ("creator.nameIdentifier.@value", get_subitem_text_key("jpcoar:nameIdentifier")),
        ("creator.nameIdentifier.@attributes.nameIdentifierURI", "jpcoar:nameIdentifier.@nameIdentifierURI"),
        ("creator.nameIdentifier.@attributes.nameIdentifierScheme", "jpcoar:nameIdentifier.@nameIdentifierScheme"),
        # jpcoar:creatorName
        ("creator.creatorName.@value", get_subitem_text_key("jpcoar:creatorName")),
        ("creator.creatorName.@attributes.xml:lang", get_subitem_lang_key("jpcoar:creatorName")),
        ("creator.creatorName.@attributes.nameType", "jpcoar:creatorName.@nameType"),
        # jpcoar:familyName
        ("creator.familyName.@value", get_subitem_text_key("jpcoar:familyName")),
        ("creator.familyName.@attributes.xml:lang", get_subitem_lang_key("jpcoar:familyName")),
        # jpcoar:givenName
        ("creator.givenName.@value", get_subitem_text_key("jpcoar:givenName")),
        ("creator.givenName.@attributes.xml:lang", get_subitem_lang_key("jpcoar:givenName")),
        # jpcoar:creatorAlternative
        ("creator.creatorAlternative.@value", get_subitem_text_key("jpcoar:creatorAlternative")),
        ("creator.creatorAlternative.@attributes.xml:lang", get_subitem_lang_key("jpcoar:creatorAlternative")),
        # jpcoar:affiliation
        ('creator.affiliation.nameIdentifier.@value', get_subitem_text_key("jpcoar:affiliation", "jpcoar:nameIdentifier")),
        ("creator.affiliation.nameIdentifier.@attributes.nameIdentifierURI", "jpcoar:affiliation.jpcoar:nameIdentifier.@nameIdentifierURI"),
        ("creator.affiliation.nameIdentifier.@attributes.nameIdentifierScheme", "jpcoar:affiliation.jpcoar:nameIdentifier.@nameIdentifierScheme"),
        ("creator.affiliation.affiliationName.@value", get_subitem_text_key("jpcoar:affiliation", "jpcoar:affiliationName")),
        ("creator.affiliation.affiliationName.@attributes.xml:lang", get_subitem_lang_key("jpcoar:affiliation", "jpcoar:affiliationName")),
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
        ("contributor.@attributes.contributorType", "@contributorType"),
        # jpcoar:nameIdentifier
        ("contributor.nameIdentifier.@value", get_subitem_text_key("jpcoar:nameIdentifier")),
        ("contributor.nameIdentifier.@attributes.nameIdentifierURI", "jpcoar:nameIdentifier.@nameIdentifierURI"),
        ("contributor.nameIdentifier.@attributes.nameIdentifierScheme", "jpcoar:nameIdentifier.@nameIdentifierScheme"),
        # jpcoar:contributorName
        ("contributor.contributorName.@value", get_subitem_text_key("jpcoar:contributorName")),
        ("contributor.contributorName.@attributes.xml:lang", get_subitem_lang_key("jpcoar:contributorName")),
        ("contributor.contributorName.@attributes.nameType", "jpcoar:contributorName.@nameType"),
        # jpcoar:familyName
        ("contributor.familyName.@value", get_subitem_text_key("jpcoar:familyName")),
        ("contributor.familyName.@attributes.xml:lang", get_subitem_lang_key("jpcoar:familyName")),
        # jpcoar:givenName
        ("contributor.givenName.@value", get_subitem_text_key("jpcoar:givenName")),
        ("contributor.givenName.@attributes.xml:lang", get_subitem_lang_key("jpcoar:givenName")),
        # jpcoar:contributorAlternative
        ("contributor.contributorAlternative.@value", get_subitem_text_key("jpcoar:contributorAlternative")),
        ("contributor.contributorAlternative.@attributes.xml:lang", get_subitem_lang_key("jpcoar:contributorAlternative")),
        # jpcoar:affiliation
        ("contributor.affiliation.nameIdentifier.@value", get_subitem_text_key("jpcoar:affiliation", "jpcoar:nameIdentifier")),
        ("contributor.affiliation.nameIdentifier.@attributes.nameIdentifierURI", "jpcoar:affiliation.jpcoar:nameIdentifier.@nameIdentifierURI"),
        ("contributor.affiliation.nameIdentifier.@attributes.nameIdentifierScheme", "jpcoar:affiliation.jpcoar:nameIdentifier.@nameIdentifierScheme"),
        ("contributor.affiliation.affiliationName.@value", get_subitem_text_key("jpcoar:affiliation", "jpcoar:affiliationName")),
        ("contributor.affiliation.affiliationName.@attributes.xml:lang", get_subitem_lang_key("jpcoar:affiliation", "jpcoar:affiliationName")),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_publisher_jpcoar(schema, mapping, res, metadata):
    """Add publisher."""
    patterns = [
        # jpcoar:publisherName
        ("publisher_jpcoar.publisherName.@value", get_subitem_text_key("jpcoar:publisherName")),
        ("publisher_jpcoar.publisherName.@attributes.xml:lang", get_subitem_lang_key("jpcoar:publisherName")),
        # jpcoar:publisherDescription
        ("publisher_jpcoar.publisherDescription.@value", get_subitem_text_key("jpcoar:publisherDescription")),
        ("publisher_jpcoar.publisherDescription.@attributes.xml:lang", get_subitem_lang_key("jpcoar:publisherDescription")),
        # dcndl:location
        ("publisher_jpcoar.location.@value", get_subitem_text_key("dcndl:location")),
        ("publisher_jpcoar.location.@attributes.xml:lang", get_subitem_lang_key("dcndl:location")),
        # dcndl:publicationPlace
        ("publisher_jpcoar.publicationPlace.@value", get_subitem_text_key("dcndl:publicationPlace")),
        ("publisher_jpcoar.publicationPlace.@attributes.xml:lang", get_subitem_lang_key("dcndl:publicationPlace"))
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
        ("accessRights.@value", TEXT),
        ("accessRights.@attributes.rdf:resource", "@rdf:resource"),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_right(schema, mapping, res, metadata):
    """Add rights."""
    patterns = [
        ("rights.@value", TEXT),
        ("rights.@attributes.xml:lang", LANG),
        ("rights.@attributes.rdf:resource", "@rdf:resource"),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_subject(schema, mapping, res, metadata):
    """Add subject."""
    patterns = [
        ("subject.@value", TEXT),
        ("subject.@attributes.xml:lang", LANG),
        ("subject.@attributes.subjectURI", "@subjectURI"),
        ("subject.@attributes.subjectScheme", "@subjectScheme"),
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
        ("description.@value", TEXT),
        ("description.@attributes.xml:lang", LANG),
        ("description.@attributes.descriptionType", "@descriptionType"),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_publisher(schema, mapping, res, metadata):
    """Add publisher."""
    patterns = [
        ("publisher.@value", TEXT),
        ("publisher.@attributes.xml:lang", LANG),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_date(schema, mapping, res, metadata):
    """Add date."""
    patterns = [
        ("date.@value", TEXT),
        ("date.@attributes.dateType", "@dateType"),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_date_dcterms(schema, mapping, res, metadata):
    patterns = [
        ("date_dcterms.@value", TEXT),
        ("date_dcterms.@attributes.xml:lang", LANG),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_edition(schema, mapping, res, metadata):
    patterns = [
        ("edition.@value", TEXT),
        ("edition.@attributes.xml:lang", LANG),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_volumeTitle(schema, mapping, res, metadata):
    patterns = [
        ("volumeTitle.@value", TEXT),
        ("volumeTitle.@attributes.xml:lang", LANG),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_originalLanguage(schema, mapping, res, metadata):
    patterns = [
        ("originalLanguage.@value", TEXT),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_extent(schema, mapping, res, metadata):
    patterns = [
        ("extent.@value", TEXT),
        ("extent.@attributes.xml:lang", LANG),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_format(schema, mapping, res, metadata):
    patterns = [
        ("format.@value", TEXT),
        ("format.@attributes.xml:lang", LANG),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_holdingAgent(schema, mapping, res, metadata):
    patterns = [
        # jpcoar:holdingAgentNameIdentifier
        ("holdingAgent.holdingAgentNameIdentifier.@value", get_subitem_text_key("jpcoar:holdingAgentNameIdentifier")),
        ("holdingAgent.holdingAgentNameIdentifier.@attributes.nameIdentifierScheme", "jpcoar:holdingAgentNameIdentifier.@nameIdentifierScheme"),
        ("holdingAgent.holdingAgentNameIdentifier.@attributes.nameIdentifierURI", "jpcoar:holdingAgentNameIdentifier.@nameIdentifierURI"),
        # jpcoar:holdingAgentName
        ("holdingAgent.holdingAgentName.@value", get_subitem_text_key("jpcoar:holdingAgentName")),
        ("holdingAgent.holdingAgentName.@attributes.xml:lang", get_subitem_lang_key("jpcoar:holdingAgentName")),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_datasetSeries(schema, mapping, res, metadata):
    patterns = [
        ("datasetSeries.@value", TEXT),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_catalog(schema, mapping, res, metadata):
    patterns = [
        # jpcoar:contributor
        ("catalog.contributor.@attributes.contributorType", "jpcoar:contributor.@contributorType"),
        ("catalog.contributor.contributorName.@value", get_subitem_text_key("jpcoar:contributor", "jpcoar:contributorName")),
        ("catalog.contributor.contributorName.@attributes.xml:lang", get_subitem_lang_key("jpcoar:contributor", "jpcoar:contributorName")),
        # jpcoar:identifier
        ("catalog.identifier.@value", get_subitem_text_key("jpcoar:identifier")),
        ("catalog.identifier.@attributes.identifierType", "jpcoar:identifier.@identifierType"),
        # dc:title
        ("catalog.title.@value", get_subitem_text_key("dc:title")),
        ("catalog.title.@attributes.xml:lang", get_subitem_lang_key("dc:title")),
        # datacite:description
        ("catalog.description.@value", get_subitem_text_key("datacite:description")),
        ("catalog.description.@attributes.xml:lang", get_subitem_lang_key("datacite:description")),
        ("catalog.description.@attributes.descriptionType", "datacite:description.@descriptionType"),
        # jpcoar:subject
        ("catalog.subject.@value", get_subitem_text_key("jpcoar:subject")),
        ("catalog.subject.@attributes.xml:lang", get_subitem_lang_key("jpcoar:subject")),
        ("catalog.subject.@attributes.subjectURI", "jpcoar:subject.@subjectURI"),
        ("catalog.subject.@attributes.subjectScheme", "jpcoar:subject.@subjectScheme"),
        # jpcoar:license
        ("catalog.license.@value", get_subitem_text_key("jpcoar:license")),
        ("catalog.license.@attributes.xml:lang", get_subitem_lang_key("jpcoar:license")),
        ("catalog.license.@attributes.licenseType", "jpcoar:license.@licenseType"),
        ("catalog.license.@attributes.rdf:resource", "jpcoar:license.@rdf:resource"),
        # dc:rights
        ("catalog.rights.@value", get_subitem_text_key("dc:rights")),
        ("catalog.rights.@attributes.xml:lang", get_subitem_lang_key("dc:rights")),
        ("catalog.rights.@attributes.rdf:resource", "dc:rights.@rdf:resource"),
        # dcterms:accessRights
        ("catalog.accessRights.@value", get_subitem_text_key("dcterms:accessRights")),
        ("catalog.accessRights.@attributes.rdf:resource", "dcterms:accessRights.@rdf:resource"),
        # jpcoar:file
        ("catalog.file.URI.@value", get_subitem_text_key("jpcoar:file", "jpcoar:URI")),
        ("catalog.file.URI.@attributes.objectType", "jpcoar:file.jpcoar:URI.@objectType"),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_language(schema, mapping, res, metadata):
    """Add language."""
    patterns = [
        ("language.@value", TEXT),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_version(schema, mapping, res, metadata):
    """Add version."""
    patterns = [
        ("version.@value", TEXT),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_version_type(schema, mapping, res, metadata):
    """Add version type."""
    patterns = [
        ("versiontype.@value", TEXT),
        ("versiontype.@attributes.rdf:resource", "@rdf:resource"),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_identifier_registration(schema, mapping, res, metadata):
    """Add identfier registration."""
    patterns = [
        ("identifierRegistration.@value", TEXT),
        ("identifierRegistration.@attributes.identifierType", "@identifierType"),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_temporal(schema, mapping, res, metadata):
    """Add temporal."""
    patterns = [
        ("temporal.@value", TEXT),
        ("temporal.@attributes.xml:lang", LANG),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_source_identifier(schema, mapping, res, metadata):
    """Add source identifier."""
    patterns = [
        ("sourceIdentifier.@value", TEXT),
        ("sourceIdentifier.@attributes.identifierType", "@identifierType"),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_file(schema, mapping, res, metadata):
    """Add file."""
    patterns = [
        # jpcoar:URI
        ("file.URI.@value", get_subitem_text_key("jpcoar:URI")),
        ("file.URI.@attributes.objectType", "jpcoar:URI.@objectType"),
        ("file.URI.@attributes.label", "jpcoar:URI.@label"),
        # jpcoar:mimeType
        ("file.mimeType.@value", get_subitem_text_key("jpcoar:mimeType")),
        # jpcoar:extent
        ("file.extent.@value", get_subitem_text_key("jpcoar:extent")),
        # datacite:date
        ("file.date.@value", get_subitem_text_key("datacite:date")),
        ("file.date.@attributes.dateType", "datacite:date.@dateType"),
        # datacite:version
        ("file.version.@value", get_subitem_text_key("datacite:version")),
    ]

    item_key, ret = parsing_metadata(mapping, schema, patterns, metadata, res)
    if ret and item_key:
        for file_info in ret:
            if not file_info.get("filename"):
                file_info["filename"] = os.path.basename(
                    file_info.get("url", {}).get("url", "")
                )
        files_info = res.get("files_info", [])
        files_info.append({"key": item_key, "items": ret})
        res["files_info"] = files_info


def add_identifier(schema, mapping, res, metadata):
    """Add identifier."""
    patterns = [
        ("identifier.@value", TEXT),
        ("identifier.@attributes.identifierType", "@identifierType"),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_source_title(schema, mapping, res, metadata):
    """Add source title."""
    patterns = [
        ("sourceTitle.@value", TEXT),
        ("sourceTitle.@attributes.xml:lang", LANG),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_volume(schema, mapping, res, metadata):
    """Add volume."""
    patterns = [
        ("volume.@value", TEXT),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_issue(schema, mapping, res, metadata):
    """Add issue."""
    patterns = [
        ("issue.@value", TEXT),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_num_page(schema, mapping, res, metadata):
    """Add num pages."""
    patterns = [
        ("numPages.@value", TEXT),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_page_start(schema, mapping, res, metadata):
    """Add page start."""
    patterns = [
        ("pageStart.@value", TEXT),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_page_end(schema, mapping, res, metadata):
    """Add page end."""
    patterns = [
        ("pageEnd.@value", TEXT),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_dissertation_number(schema, mapping, res, metadata):
    """Add dissertation number."""
    patterns = [
        ("dissertationNumber.@value", TEXT),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_date_granted(schema, mapping, res, metadata):
    """Add date granted."""
    patterns = [
        ("dateGranted.@value", TEXT),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_conference(schema, mapping, res, metadata):
    """Add conference information."""
    patterns = [
        # jpcoar:conferenceName
        ("conference.conferenceName.@value", get_subitem_text_key("jpcoar:conferenceName")),
        ("conference.conferenceName.@attributes.xml:lang", get_subitem_lang_key("jpcoar:conferenceName")),
        # jpcoar:conferenceSequence
        ("conference.conferenceSequence.@value", get_subitem_text_key("jpcoar:conferenceSequence")),
        # jpcoar:conferenceSponsor
        ("conference.conferenceSponsor.@value", get_subitem_text_key("jpcoar:conferenceSponsor")),
        ("conference.conferenceSponsor.@attributes.xml:lang", get_subitem_lang_key("jpcoar:conferenceSponsor")),
        # jpcoar:conferenceDate
        ("conference.conferenceDate.@value", get_subitem_text_key("jpcoar:conferenceDate")),
        ("conference.conferenceDate.@attributes.startDay", "jpcoar:conferenceDate.@startDay"),
        ("conference.conferenceDate.@attributes.startMonth", "jpcoar:conferenceDate.@startMonth"),
        ("conference.conferenceDate.@attributes.startYear", "jpcoar:conferenceDate.@startYear"),
        ("conference.conferenceDate.@attributes.endDay", "jpcoar:conferenceDate.@endDay"),
        ("conference.conferenceDate.@attributes.endMonth", "jpcoar:conferenceDate.@endMonth"),
        ("conference.conferenceDate.@attributes.endYear", "jpcoar:conferenceDate.@endYear"),
        ("conference.conferenceDate.@attributes.xml:lang", get_subitem_lang_key("jpcoar:conferenceDate")),
        # jpcoar:conferenceVenue
        ("conference.conferenceVenue.@value", get_subitem_text_key("jpcoar:conferenceVenue")),
        ("conference.conferenceVenue.@attributes.xml:lang", get_subitem_lang_key("jpcoar:conferenceVenue")),
        # jpcoar:conferencePlace
        ("conference.conferencePlace.@value", get_subitem_text_key("jpcoar:conferencePlace")),
        ("conference.conferencePlace.@attributes.xml:lang", get_subitem_lang_key("jpcoar:conferencePlace")),
        # jpcoar:conferenceCountry
        ("conference.conferenceCountry.@value", get_subitem_text_key("jpcoar:conferenceCountry")),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_degree_grantor(schema, mapping, res, metadata):
    """Add information on the degree granting institution."""
    patterns = [
        # jpcoar:nameIdentifier
        ("degreeGrantor.nameIdentifier.@value", get_subitem_text_key("jpcoar:nameIdentifier")),
        ("degreeGrantor.nameIdentifier.@attributes.nameIdentifierScheme", "jpcoar:nameIdentifier.@nameIdentifierScheme"),
        # jpcoar:degreeGrantorName
        ("degreeGrantor.degreeGrantorName.@value", get_subitem_text_key("jpcoar:degreeGrantorName")),
        ("degreeGrantor.degreeGrantorName.@attributes.xml:lang", get_subitem_lang_key("jpcoar:degreeGrantorName")),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_degree_name(schema, mapping, res, metadata):
    """Add academic degree and field of the degree specified in \
    the Degree Regulation."""
    patterns = [
        ("degreeName.@value", TEXT),
        ("degreeName.@attributes.xml:lang", LANG),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_funding_reference(schema, mapping, res, metadata):
    """Add the grant information if you have received \
    financial support (funding) to create the resource."""
    patterns = [
        # jpcoar:funderIdentifier
        ("fundingReference.funderIdentifier.@value", get_subitem_text_key("jpcoar:funderIdentifier")),
        ("fundingReference.funderIdentifier.@attributes.funderIdentifierType", "jpcoar:funderIdentifier.@funderIdentifierType"),
        ("fundingReference.funderIdentifier.@attributes.funderIdentifierTypeURI", "jpcoar:funderIdentifier.@funderIdentifierTypeURI"),
        # jpcoar:funderName
        ("fundingReference.funderName.@value", get_subitem_text_key("jpcoar:funderName")),
        ("fundingReference.funderName.@attributes.xml:lang", get_subitem_lang_key("jpcoar:funderName")),
        # jpcoar:fundingStreamIdentifier
        ("fundingReference.fundingStreamIdentifier.@value", get_subitem_text_key("jpcoar:fundingStreamIdentifier")),
        ("fundingReference.fundingStreamIdentifier.@attributes.fundingStreamIdentifierType", "jpcoar:fundingStreamIdentifier.@fundingStreamIdentifierType"),
        ("fundingReference.fundingStreamIdentifier.@attributes.fundingStreamIdentifierTypeURI", "jpcoar:fundingStreamIdentifier.@fundingStreamIdentifierTypeURI"),
        # jpcoar:fundingStream
        ("fundingReference.fundingStream.@value", get_subitem_text_key("jpcoar:fundingStream")),
        ("fundingReference.fundingStream.@attributes.xml:lang", get_subitem_lang_key("jpcoar:fundingStream")),
        # jpcoar:awardNumber
        ("fundingReference.awardNumber.@value", get_subitem_text_key("jpcoar:awardNumber")),
        ("fundingReference.awardNumber.@attributes.awardURI", "jpcoar:awardNumber.@awardURI"),
        ("fundingReference.awardNumber.@attributes.awardNumberType", "jpcoar:awardNumber.@awardNumberType"),
        # jpcoar:awardTitle
        ("fundingReference.awardTitle.@value", get_subitem_text_key("jpcoar:awardTitle")),
        ("fundingReference.awardTitle.@attributes.xml:lang", get_subitem_lang_key("jpcoar:awardTitle")),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_geo_location(schema, mapping, res, metadata):
    """Add Spatial region or named place where the resource was \
    gathered or about which the data is focused."""
    patterns = [
        # datacite:geoLocationPoint
        (
            "geoLocation.geoLocationPoint.pointLongitude.@value",
            get_subitem_text_key("datacite:geoLocationPoint", "datacite:pointLongitude"),
        ),
        (
            "geoLocation.geoLocationPoint.pointLatitude.@value",
            get_subitem_text_key("datacite:geoLocationPoint", "datacite:pointLatitude"),
        ),
        # datacite:geoLocationBox
        (
            "geoLocation.geoLocationBox.westBoundLongitude.@value",
            get_subitem_text_key("datacite:geoLocationBox", "datacite:westBoundLongitude"),
        ),
        (
            "geoLocation.geoLocationBox.eastBoundLongitude.@value",
            get_subitem_text_key("datacite:geoLocationBox", "datacite:eastBoundLongitude"),
        ),
        (
            "geoLocation.geoLocationBox.southBoundLatitude.@value",
            get_subitem_text_key("datacite:geoLocationBox", "datacite:southBoundLatitude"),
        ),
        (
            "geoLocation.geoLocationBox.northBoundLatitude.@value",
            get_subitem_text_key("datacite:geoLocationBox", "datacite:northBoundLatitude"),
        ),
        # datacite:geoLocationPlace
        (
            "geoLocation.geoLocationPlace.@value",
            get_subitem_text_key("datacite:geoLocationPlace"),
        ),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_relation(schema, mapping, res, metadata):
    """Add the relationship between the registering resource \
    and other related resource.

    Select and enter 'relationType' from the controlled vocabularies.
    If there is no corresponding vocabulary, do not enter 'relationType'.
    """
    patterns = [
        ("relation.@attributes.relationType", "@relationType"),
        # jpcoar:relatedIdentifier
        ("relation.relatedIdentifier.@value",get_subitem_text_key("jpcoar:relatedIdentifier")),
        ("relation.relatedIdentifier.@attributes.identifierType","jpcoar:relatedIdentifier.@identifierType"),
        # jpcoar:relatedTitle
        ("relation.relatedTitle.@value", get_subitem_text_key("jpcoar:relatedTitle")),
        ("relation.relatedTitle.@attributes.xml:lang", get_subitem_lang_key("jpcoar:relatedTitle")),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_rights_holder(schema, mapping, res, metadata):
    """Add the information on the rights holder of such as copyright \
    other than the creator or contributor."""
    patterns = [
        # jpcoar:nameIdentifier
        (
            "rightsHolder.nameIdentifier.@value",
            get_subitem_text_key("jpcoar:nameIdentifier"),
        ),
        (
            "rightsHolder.nameIdentifier.@attributes.nameIdentifierURI",
            "jpcoar:nameIdentifier.@nameIdentifierURI",
        ),
        (
            "rightsHolder.nameIdentifier.@attributes.nameIdentifierScheme",
            "jpcoar:nameIdentifier.@nameIdentifierScheme",
        ),
        # jpcoar:rightsHolderName
        (
            "rightsHolder.rightsHolderName.@value",
            get_subitem_text_key("jpcoar:rightsHolderName"),
        ),
        (
            "rightsHolder.rightsHolderName.@attributes.xml:lang",
            get_subitem_lang_key("jpcoar:rightsHolderName"),
        ),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


def add_resource_type(schema, mapping, res, metadata):
    """Add publisher."""
    patterns = [
        ("type.@value", TEXT),
        ("type.@attributes.rdf:resource", "@rdf:resource"),
    ]

    parsing_metadata(mapping, schema, patterns, metadata, res)


RESOURCE_TYPE_V2_MAP = {
    # Article
    "conference paper": "Conference Paper",
    "data paper": "Journal Article",
    "departmental bulletin paper": "Departmental Bulletin Paper",
    "editorial": "Article",
    "journal": "Article",
    "journal article": "Journal Article",
    "newspaper": "Article",
    "review article": "Article",
    "other periodical": "Others",
    "software paper": "Article",
    "article": "Article",
    # Book
    "book": "Book",
    "book part": "Book",
    # Cartographic Material
    "cartographic material": "Others",
    "map": "Others",
    # Conference object
    "conference output": "Presentation",
    "conference presentation": "Presentation",
    "conference proceedings": "Presentation",
    "conference poster": "Presentation",
    # Dataset
    "aggregated data": "Data or Dataset",
    "clinical trial data": "Data or Dataset",
    "compiled data": "Data or Dataset",
    "dataset": "Data or Dataset",
    "encoded data": "Data or Dataset",
    "experimental data": "Data or Dataset",
    "genomic data": "Data or Dataset",
    "geospatial data": "Data or Dataset",
    "laboratory notebook": "Data or Dataset",
    "measurement and test data": "Data or Dataset",
    "observational data": "Data or Dataset",
    "recorded data": "Data or Dataset",
    "simulation data": "Data or Dataset",
    "survey data": "Data or Dataset",
    # Image
    "image": "Others",
    "still image": "Others",
    "moving image": "Others",
    "video": "Others",
    # Lecture
    "lecture": "Others",
    # Patent
    "design patent": "Others",
    "patent": "Others",
    "PCT application": "Others",
    "plant patent": "Others",
    "plant variety protection": "Others",
    "software patent": "Others",
    "trademark": "Others",
    "utility model": "Others",
    # Report
    "report": "Research Paper",
    "research report": "Research Paper",
    "technical report": "Technical Report",
    "policy report": "Others",
    "working paper": "Others",
    "data management plan": "Others",
    # Sound
    "sound": "Others",
    # Thesis
    "thesis": "Thesis or Dissertation",
    "bachelor thesis": "Thesis or Dissertation",
    "master thesis": "Thesis or Dissertation",
    "doctoral thesis": "Thesis or Dissertation",
    # Multiple
    "commentary": "Others",
    "design": "Others",
    "industrial design": "Others",
    "interactive resource": "Others",
    "layout design": "Others",
    "learning object": "Learning Material",
    "manuscript": "Others",
    "musical notation": "Others",
    "peer review": "Others",
    "research proposal": "Others",
    "research protocol": "Others",
    "software": "Software",
    "source code": "Software",
    "technical documentation": "Others",
    "transcription": "Others",
    "workflow": "Others",
    "other": "Others",
}


class BaseMapper:
    """BaseMapper."""

    itemtype_map = {}
    identifiers = []

    @classmethod
    def update_itemtype_map(cls):
        """Update itemtype map."""
        for t in ItemTypes.get_all(with_deleted=False):
            cls.itemtype_map[t.item_type_name.name] = t

    def __init__(self, xml):
        """Init."""
        self.xml = xml
        self.json = xmltodict.parse(xml) if xml else {}
        if not BaseMapper.itemtype_map:
            BaseMapper.update_itemtype_map()

        self.itemtype = None
        for item in BaseMapper.itemtype_map:
            if "Others" == item or "Multiple" == item:
                self.itemtype = BaseMapper.itemtype_map.get(item)
                break


class JPCOARV2Mapper(BaseMapper):
    """JPCOAR V2 Mapper."""

    def __init__(self, xml):
        """Init."""
        super().__init__(xml)

    def map(self, item_type_name):
        """Get map."""
        default_metadata = {"pubdate": date.today().isoformat()}
        if not item_type_name or not self.json or "jpcoar:jpcoar" not in self.json.keys():
            return default_metadata

        self.itemtype = self.itemtype_map.get(item_type_name)

        if not self.itemtype:
            return default_metadata

        self.identifiers = []
        res = {"$schema": self.itemtype.id, **default_metadata}

        item_type_mapping = Mapping.get_record(self.itemtype.id)
        item_map = get_full_mapping(item_type_mapping, "jpcoar_mapping")

        args = [self.itemtype.schema.get("properties"), item_map, res]

        add_funcs = {
            "dc:title": partial(add_title, *args),
            "dcterms:alternative": partial(add_alternative, *args),
            "jpcoar:creator": partial(add_creator_jpcoar, *args),
            "jpcoar:contributor": partial(add_contributor_jpcoar, *args),
            "dcterms:accessRights": partial(add_access_right, *args),
            "dc:rights": partial(add_right, *args),
            "jpcoar:rightsHolder": partial(add_rights_holder, *args),
            "jpcoar:subject": partial(add_subject, *args),
            "datacite:description": partial(add_description, *args),
            "dc:publisher": partial(add_publisher, *args),
            "jpcoar:publisher": partial(add_publisher_jpcoar, *args),
            "datacite:date": partial(add_date, *args),
            "dcterms:date": partial(add_date_dcterms, *args),
            "dc:language": partial(add_language, *args),
            "dc:type": partial(add_resource_type, *args),
            "datacite:version": partial(add_version, *args),
            "oaire:version": partial(add_version_type, *args),
            "jpcoar:identifier": partial(add_identifier, *args),
            "jpcoar:identifierRegistration": partial(add_identifier_registration, *args),
            "jpcoar:relation": partial(add_relation, *args),
            "dcterms:temporal": partial(add_temporal, *args),
            "datacite:geoLocation": partial(add_geo_location, *args),
            "jpcoar:fundingReference": partial(add_funding_reference, *args),
            "jpcoar:sourceIdentifier": partial(add_source_identifier, *args),
            "jpcoar:sourceTitle": partial(add_source_title, *args),
            "jpcoar:volume": partial(add_volume, *args),
            "jpcoar:issue": partial(add_issue, *args),
            "jpcoar:numPages": partial(add_num_page, *args),
            "jpcoar:pageStart": partial(add_page_start, *args),
            "jpcoar:pageEnd": partial(add_page_end, *args),
            "dcndl:dissertationNumber": partial(add_dissertation_number, *args),
            "dcndl:degreeName": partial(add_degree_name, *args),
            "dcndl:dateGranted": partial(add_date_granted, *args),
            "jpcoar:degreeGrantor": partial(add_degree_grantor, *args),
            "jpcoar:conference": partial(add_conference, *args),
            "dcndl:edition": partial(add_edition, *args),
            "dcndl:volumeTitle": partial(add_volumeTitle, *args),
            "dcndl:originalLanguage": partial(add_originalLanguage, *args),
            "dcterms:extent": partial(add_extent, *args),
            "jpcoar:format": partial(add_format, *args),
            "jpcoar:holdingAgent": partial(add_holdingAgent, *args),
            "jpcoar:datasetSeries": partial(add_datasetSeries, *args),
            "jpcoar:file": partial(add_file, *args),
            "jpcoar:catalog": partial(add_catalog, *args),
        }

        tags = self.json["jpcoar:jpcoar"]

        for t in tags:
            if t in add_funcs:
                if not isinstance(tags[t], list):
                    metadata = [tags[t]]
                else:
                    metadata = tags[t]
                add_funcs[t](metadata)

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
    def __init__(self, json, itemtype_id=None, itemtype_name=None):
        """Initilize JsonMapper.

        Args:
            json (dict): metadata with json format.
            itemtype_id (int, optional): item type id. Defaults to None.
            itemtype_name (str, optional): item type name. Defaults to None.
        """
        self.json = json
        if itemtype_id is not None:
            self.itemtype = ItemTypes.get_by_id(itemtype_id)
            self.itemtype_name = self.itemtype.item_type_name.name

        else:
            self.itemtype_name = itemtype_name
            if not BaseMapper.itemtype_map:
                BaseMapper.update_itemtype_map()

            for item in BaseMapper.itemtype_map:
                if self.itemtype_name == item:
                    self.itemtype = BaseMapper.itemtype_map.get(item)

    def _create_item_map(self, detail=False):
        """ Create Mapping information from ItemType.

            This mapping information consists of the following.

                KEY: Identifier for the ItemType item
                        (value obtained by concatenating the “title”
                        attribute of each item in the schema)
                VALUE: Item Code. Subitem code identifier.

            Returns:
                item_map: Mapping information about ItemType.

            Examples:
                For example, in the case of “Title of Default ItemType”,
                it would be as follows.

                KEY: Title.タイトル
                VALUE: item_30001_title0.subitem_title
        """

        item_map = {}
        for prop_k, prop_v in self.itemtype.schema["properties"].items():
            self._apply_property(item_map, "", "", prop_k, prop_v, detail)
        return item_map

    def _apply_property(self, item_map, key, value, prop_k, prop_v, detail):
        """
            This process is part of “_create_item_map” and is not
            intended for any other use.
        """
        if "title" in prop_v:
            key = key + "." + prop_v["title"] if key else prop_v["title"]
            value = value + "." + prop_k if value else prop_k

        if prop_v["type"] == "object":
            item_map.update({key: value}) if detail else None
            for child_k, child_v in prop_v["properties"].items():
                self._apply_property(
                    item_map, key, value, child_k, child_v, detail)
        elif prop_v["type"] == "array":
            item_map.update({key: value}) if detail else None
            self._apply_property(
                item_map, key, value, "items", prop_v["items"], detail)
        else:
            item_map[key] = value

    def _get_property_type(self, chained_path):
        """Get itemtype property type.

        Get the type of the property specified by the path.

        Args:
            chained_path (str):
                path of the property. <br>
                e.g. "item_30001_title0.subitem_title"
        Returns:
            str: property type. e.g. "string", "array", "object"
        """
        # property_type = ""
        properties = self.itemtype.schema.get("properties")
        for p in chained_path.split("."):
            if properties[p].get("type") == "object":
                property_type = "object"
                properties = properties[p].get("properties")
            elif properties[p].get("type") == "array":
                property_type = "array"
                properties = properties[p].get("items").get("properties")
            else:
                property_type = properties[p].get("type")
        return property_type

    def required_properties(self):
        """Get required properties.

        Get required properties of the item type.

        Returns:
            dict[str, str]: required properties.
        """
        if self.itemtype is None:
            return {}

        required = self._get_required(self.itemtype.schema)
        # return required
        return {
            title: key for title, key in self._create_item_map(detail=True).items()
            if key in required
        }

    def _get_required(self, schema, parent=None):
        required = schema.get("required", []).copy()
        for k, v in schema.get("properties", {}).items():
            if v.get("type") == "object":
                required.extend([
                    f"{k}.{r}" for r in self._get_required(v, k)
                ])
            elif v.get("type") == "array":
                required.extend([
                    f"{k}.{r}" for r in self._get_required(v.get("items", {}), k)
                ])
        return required

    class _InformedMetadata(dict):
        """Meatadata with identifier."""
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.id = None
            """Identifier of the metadata."""
            self.link_data = []
            """Link data. <br>
            e.g. [{"item_id": 123, "sele_id": "isSupplementedBy"}]
            """
            self.list_file = []
            """List of files."""
            self.non_extract = []
            """Non-extract file list for elastic search."""
            self.save_as_is = False
            """Flag to save BagIt as is. for SWORD deposit."""
            self.cnri = ""
            """CNRI for grant. .CNRI in tsv"""
            self.doi_ra = ""
            """DOI_RA for grant. .DOI_RA in tsv"""
            self.doi = ""
            """DOI for grant. .DOI in tsv"""
            self.metadata_replace = False
            """Flag to save only metadata. for SWORD deposit."""


class JsonLdMapper(JsonMapper):
    """JsonLdMapper."""

    AT_TYPE_MAP = {
        "File": "File",
        "Contributor": "Person",
        "Creator": "Person",
        "Publisher": "Organization"
    }

    def __init__(self, itemtype_id, json_mapping):
        """Initilize JsonLdMapper.

        Args:
            itemtype_id (int): item type id.
            json_mapping (dict): mapping between json-ld and item type metadata.
        """
        self.json_mapping = json_mapping
        super().__init__(None, itemtype_id)

    @property
    def is_valid(self):
        """Validate json-ld.

        Returns:
            bool: True if valid, False otherwise.
        """
        return self.validate() is None

    def validate(self):
        """Validate json-ld mapping.

        Check if the json-ld mapping has required properties and
        is in the item type.

        Returns:
            errors (list[str] | None): list of errors.
        """
        from flask_babelex import lazy_gettext as _
        errors = []
        item_map = self._create_item_map(detail=True)
        required_map = self.required_properties()

        errors += [
            _("{key} is required", key=k.replace(".", ">"))
            for k in required_map
            if k not in self.json_mapping
        ]

        errors += [
            _("{key} is not in itemtype", key=k.replace(".", ">"))
            for k in self.json_mapping.keys()
            if k not in item_map
        ]

        return errors if errors else None

    def to_item_metadata(self, json_ld):
        """Map to item type metadata.

        Map json-ld to item type metadata.
        RO-Crate and SWORD BagIt format are supported.

        Args:
            json_ld (dict): metadata with json-ld format.
        Returns:
            list[dict]: list of mapped metadata.
        """
        metadatas, format = self._deconstruct_json_ld(json_ld)
        list_items = [ self._map_to_item(metadata) for metadata in metadatas ]

        return list_items, format

    def _map_to_item(self, metadata):
        """Map json-ld to item type metadata.

        Args:
            metadata (_InformedMetadata):
                metadata with deconstructed json-ld format.
        Returns:
            dict: mapped metadata.
        """
        item_map = self._create_item_map(detail=True)
            # e.g. { "Title.タイトル": "item_30001_title0.subitem_title" }
        properties_mapping = {
            # make map of json-ld key to itemtype metadata key
            # e.g. { "dc:title.value": "item_30001_title0.subitem_title" }
            ld_key: item_map.get(prop_name)
                for prop_name, ld_key in self.json_mapping.items()
                if prop_name in item_map
        }

        fixed_properties = {}
        for k, v in properties_mapping.items():
            if k.startswith("$") and "." in v:
                key = v[:v.rfind(".")]
                sub_key = v[v.rfind(".")+1:]
                value = k[1:]
                if key not in fixed_properties:
                    fixed_properties[key] = {}
                fixed_properties[key][sub_key] = value

        mapped_metadata = self._InformedMetadata()
        mapped_metadata.id = metadata.id
        mapped_metadata.link_data = metadata.link_data
        mapped_metadata.list_file = [
            filename[5:] for filename in metadata.list_file
            if filename.startswith("data/")
        ]
        mapped_metadata.non_extract = [
            filename[5:] for filename in metadata.non_extract
            if filename.startswith("data/")
        ]
        mapped_metadata.save_as_is = metadata.save_as_is
        mapped_metadata.metadata_replace = metadata.metadata_replace
        mapped_metadata.update({"id": metadata["id"]} if "id" in metadata else {})
        mapped_metadata.update({"uri": metadata["uri"]} if "uri" in metadata else {})
        mapped_metadata.setdefault("publish_status", "private")
        mapped_metadata.setdefault("edit_mode", "Keep")

        missing_metadata = {}

        def _empty_metadata(parent_prop_key):
            return fixed_properties.get(parent_prop_key, {})

        def _set_metadata(
            parent, META_KEY, meta_props, PROP_PATH, prop_props
        ):
            """
            Args:
                parent (dict): parent metadata.
                META_KEY (str): deconstructed json-ld key.
                meta_props (list[str]): json-ld hierarchy split by ".".
                PROP_PATH (str): itemtype metadata hierarchy.
                prop_props (list[str]):
                    itemtype metadata metadata split by ".".
            """
            # meta_key="dc:type.@id", meta_path="dc:type.@id, meta_props=["dc:type", "@id"]
            # prop_path=item_30001_resource_type11.resourceuri, prop_props=["item_30001_resource_type11","resourceuri"]
            if len(prop_props) == 0:
                raise Exception()
            if len(prop_props) == 1:
                meta_value = metadata.get(META_KEY)
                if self._get_property_type(PROP_PATH) == "array":
                    schema = self.itemtype.schema["properties"]
                    for prop in PROP_PATH:
                        schema = schema.get(prop)
                    schema = schema.get("items").get("properties")
                    interim = list(schema.keys())[0]
                    if parent.get(prop_props[0]) is None:
                        parent[prop_props[0]] = [
                            {interim: meta_value}
                        ]
                    else:
                        parent[prop_props[0]].append(
                            {interim: meta_value}
                        )
                else:
                    parent.update({prop_props[0]: meta_value})
                return

            parent_prop_key = re.split(rf"\.{prop_props[1]}(?=\.|$)", PROP_PATH)[0]
            m_index = re.search(r"\[(\d+)\]", meta_props[0])
            index = int(m_index.group(1)) if m_index is not None else None
            if not parent_prop_key in properties_mapping.values():
                # The corresponding layers are different,
                # so the prop_path needs to progress to the lower layer.
                if self._get_property_type(parent_prop_key) == "object":
                    sub_prop_object = parent.get(
                        prop_props[0], {} # TODO: FIXED VALUE
                    )
                    # FIXME: check sub_sub propaty type
                    sub_sub_object = sub_prop_object.get(
                        prop_props[1], {} # TODO: FIXED VALUE
                    )
                    _set_metadata(
                        sub_sub_object, META_KEY, meta_props[1:],
                        PROP_PATH, prop_props[1:]
                    )
                    sub_prop_object.update({prop_props[1]: sub_sub_object})
                    parent.update({prop_props[0]: sub_prop_object})
                elif self._get_property_type(parent_prop_key) == "array":
                    sub_prop_array = parent.get(prop_props[0], [])
                    index = 0 if index is None else index
                    if len(sub_prop_array) <= index:
                        sub_prop_array.extend([
                            {} # TODO: FIXED VALUE
                            for _ in range(index - len(sub_prop_array) + 1)
                        ])
                    # FIXME: check sub_sub propaty type
                    sub_sub_object = {} # TODO: FIXED VALUE
                    _set_metadata(
                        sub_sub_object, META_KEY, meta_props,
                        PROP_PATH, prop_props[1:]
                    )
                    sub_prop_array[index].update(sub_sub_object)
                    parent.update({prop_props[0]: sub_prop_array})
                return
            if self._get_property_type(parent_prop_key) == "object":
                sub_prop_object = parent.get(
                    prop_props[0], _empty_metadata(parent_prop_key)
                )
                if index is not None and index > 1:
                    return
                _set_metadata(
                    sub_prop_object, META_KEY, meta_props[1:],
                    PROP_PATH, prop_props[1:]
                )
                parent.update({prop_props[0]: sub_prop_object})

            elif self._get_property_type(parent_prop_key) == "array":
                sub_prop_array = parent.get(prop_props[0], [])
                index = 0 if index is None else index
                if len(sub_prop_array) <= index:
                    sub_prop_array.extend([
                        _empty_metadata(parent_prop_key)
                        for _ in range(index - len(sub_prop_array) + 1)
                    ])
                _set_metadata(
                    sub_prop_array[index], META_KEY, meta_props[1:],
                    PROP_PATH, prop_props[1:]
                )
                parent.update({prop_props[0]: sub_prop_array})
            return

        for META_KEY in metadata:
            META_PATH = re.sub(r"\[\d+\]", "", META_KEY)
            if "wk:index" in META_PATH:
                path = mapped_metadata.get("path", [])
                path.append(int(metadata.get(META_KEY)))
                mapped_metadata["path"] = path
            elif "wk:publishStatus" in META_PATH:
                mapped_metadata["publish_status"] = metadata.get(META_KEY)
            elif "wk:editMode" in META_PATH:
                mapped_metadata["edit_mode"] = metadata.get(META_KEY)
            elif "wk:feedbackMail" in META_PATH:
                # TODO: implement handling author_id
                feedback_mail_list = metadata.get("feedback_mail_list", [])
                feedback_mail_list.append({
                    "email": metadata.get(META_KEY), "author_id": ""}
                )
                mapped_metadata["feedback_mail_list"] = feedback_mail_list
            # TODO: implement request mail list
            elif "wk:grant" in META_PATH:
                # TODO: implement grant mapping
                pass
            elif META_PATH not in properties_mapping:
                missing_metadata[META_KEY] = metadata[META_KEY]
            else:
                meta_props = META_KEY.split(".")
                PROP_PATH = properties_mapping[META_PATH]
                prop_props = PROP_PATH.split(".")
                # meta_key="dc:type.@id", meta_path="dc:type.@id", meta_props=["dc:type","@id"],
                # prop_path=item_30001_resource_type11.resourceuri, prop_props=["item_30001_resource_type11","resourceuri"]
                _set_metadata(
                    mapped_metadata, META_KEY, meta_props,
                    PROP_PATH, prop_props
                )

        # Check if "Extra" prepared in itemtype schema form item_map
        if "Extra" in item_map:
            extra_key = item_map["Extra"]
            prop_type = self._get_property_type(extra_key)
            if prop_type == "array":
                extra_schema = self.itemtype.schema["properties"].get(
                    extra_key).get("items").get("properties")
                interim = list(extra_schema.keys())[0]
                mapped_metadata[item_map.get("Extra")] = [
                    {interim: str(missing_metadata)}
                ]
            else:
                mapped_metadata[item_map.get("Extra")] = str(missing_metadata)


        files_info = []
        for v in item_map.values():
            if not v.endswith(".filename"):
                continue

            files_key = v.split(".")[0]
            files = mapped_metadata.get(files_key, [])

            # remove "data/" prefix from label
            files = [
                file["url"].update({"label": label[5:]})
                for file in files
                for label in [file["url"].get("label")]
                if label.startswith("data/")
            ]

            files_info.append({
                "key": files_key,
                "items": mapped_metadata.get(files_key, [])
            })
        mapped_metadata["files_info"] = files_info
        # result = {
        #     "pubdate": "2021-10-15",
        #     "publish_status": "private",
        #     "path": [1623632832836],
        #     "item_1617186331708": {...},
        #     "item_1617258105262": {...},
        #     ...
        # }
        return mapped_metadata

    @classmethod
    def _deconstruct_json_ld(cls, json_ld):
        """Deconstruct json-ld.

        Deconstructing json-ld metadata values ​​one by one
        to be able to use in mapping to WEKO item type.
        If json-ld is in RO-Crate format, resolve links and
        pick up metadata from @graph and resolve links.

        Note:
            SWORDBagIt metadata format is not supported yet.

        Args:
            json_ld (dict): Json-ld in SWORD BagIt or RO-Crate format.

        Returns:
            list[dict]: Deconstructed json data list.

        Raises:
            ValueError: Invalid json-ld format.

        Examples:

            >>> json_ld = {
            ...   "@context": "https://w3id.org/ro/crate/1.1/context",
            ...   "@graph": [
            ...     {
            ...       "@id": "./",
            ...       "dc:title": {
            ...         "value": "Title"
            ...         "language": "en"
            ...       },
            ...       "dc:creator": [
            ...         {
            ...           "@id": "https://orcid.org/0000-0002-1825-0097"
            ...         },
            ...         {
            ...           "@id": "https://orcid.org/0000-0002-1825-0098"
            ...         }
            ...       ]
            ...     }
            ...   ]
            ... }
            >>> JsonLdMapper.process_json_ld(json_ld)
            [
              {
                "dc.title.value": "Title",
                "dc.title.language": "en",
                "dc.creator[0].@id": "https://orcid.org/0000-0002-1825-0097",
                "dc.creator[1].@id": "https://orcid.org/0000-0002-1825-0098"
              }
            ]
        """
        extracted = {}
        context = json_ld.get("@context", "")
        format = ""
        # Check if the json-ld context is valid
        if "https://swordapp.github.io/swordv3/swordv3.jsonld" in context:
            # TODO: support SWORD json-ld format
            format = "sword-bagit"
            extracted = json_ld
        elif (
            "https://w3id.org/ro/crate/1.1/context" in context
                or isinstance(context, dict)
                and "https://w3id.org/ro/crate/1.1/context" in context.values()
            ):
            # Check structure of RO-Crate json-ld
            format = "ro-crate"
            if "@graph" not in json_ld or not isinstance(json_ld["@graph"], list):
                raise ValueError('Invalid json-ld format: "@graph" is not found.')
            # Convert the list containing @id in @graph to a dict
            try:
                extracted = {v["@id"]: v for v in json_ld["@graph"]}
            except KeyError as ex:
                raise ValueError(
                    'Invalid json-ld format: Objects without "@id" '
                    'are directly under "@graph"'
                ) from ex
            rocrate_entity_key = ROCRATE_METADATA_FILE.split("/")[-1]
            if rocrate_entity_key not in extracted:
                raise ValueError(
                    f'Invalid json-ld format: "{rocrate_entity_key}" entity is not found.'
                )
        else:
            raise ValueError('Invalid json-ld format: "@context" is invalid.')
        if not extracted:
            raise ValueError("Invalid json-ld format: Metadata is not found.")

        def _resolve_link(parent, key, value):
            """Resolve links in json-ld metadata and restore hierarchy."""
            if isinstance(value, dict):
                if len(value) == 1 and "@id" in value and value["@id"] in extracted:
                    parent[key] = extracted[value["@id"]]
                else:
                    for k, v in value.items():
                        _resolve_link(value, k, v)
            elif isinstance(value, list):
                for i, v in enumerate(value):
                    _resolve_link(value, i, v)

        # Restore metadata to tree structure by tracing "@id" in linked data
        for key, value in extracted.items():
            _resolve_link(extracted, key, value)

        list_extracted = []
        if format == "ro-crate":
            extracted = extracted.get(rocrate_entity_key).get("about")
            if extracted.get("wk:is_splited", False) and "hasPart" in extracted:
                # each metadata part must be in "hasPart"
                list_extracted = [ part for part in extracted.get("hasPart") ]
            else:
                list_extracted = [ extracted ]
        else:
            list_extracted = [ extracted ]

        list_deconstructed = []
        for extracted in list_extracted:
            metadata = cls._deconstruct_dict(extracted, cls._InformedMetadata())
            metadata.update(
                {"id": extracted["identifier"]}
                if "identifier" in extracted else {}
            )
            metadata.update(
                {"uri": extracted["uri"]}
                if "uri" in extracted else {}
            )
            metadata.id = extracted["@id"]
            metadata.link_data = [
                {"item_id": link.get("identifier"), "sele_id" : link.get("value")}
                    for link in extracted.get("wk:itemLinks", [])
            ]
            metadata.list_file = [
                file["@id"] for file in extracted.get("hasPart", [])
            ]
            metadata.non_extract = [
                file["@id"] for file in extracted.get("hasPart", [])
                    if not file.get("wk:textExtraction", True)
            ]
            metadata.save_as_is = extracted.get("wk:saveAsIs", False)
            metadata.metadata_replace = extracted.get("wk:metadataReplace", False)
            list_deconstructed.append(metadata)

        return list_deconstructed, format

    @classmethod
    def _deconstruct_dict(cls, dict_data, return_data=None):
        """Deconstruct dictioanry data.

        Deconstructing dictionary hierarchy. <br>
        Chain the keys of the dictionary hierarchy with "." and
        list index with "[]".

        Args:
            dict_data (dict): dictionary data.
            return_data (dict | None):
                return data. Defaults to None. <br>
                if specified, return data is updated with deconstructed data.
        Returns:
            dict: deconstructed dictionary data.
        """

        def _deconstructer(metadata, parent, key, value):
            if "@type" in key:
                return
            if isinstance(value, dict):
                for k, v in value.items():
                    key_name = key if parent == "" else f"{parent}.{key}"
                    _deconstructer(metadata, key_name, k, v)
            elif isinstance(value, list):
                for i, d in enumerate(value):
                    key_name = f"{key}[{i}]" if parent == "" else f"{parent}.{key}[{i}]"
                    if isinstance(d, dict):
                        for k, v in d.items():
                            _deconstructer(metadata, key_name, k, v)
                    else:
                        metadata[key_name] = d
            else:
                key_name = key if parent == "" else f"{parent}.{key}"
                metadata[key_name] = value

        return_data = {} if return_data is None else return_data
        for key, value in dict_data.items():
            _deconstructer(return_data, "", key, value)

        return return_data

    def to_rocrate_metadata(self, metadata, **kwargs):
        """Map to RO-Crate format.

        Args:
            metadata (dict): metadata with item type format.
        Returns:
            dict: metadata with RO-Crate format.
        """
        item_map = self._create_item_map(detail=True)
            # e.g. { "Title.タイトル": "item_30001_title0.subitem_title" }
        properties_mapping = {
            # make map of json-ld key to itemtype metadata key
            # e.g. { "item_30001_title0.subitem_title": "dc:title.value" }
            item_map.get(prop_name): ld_key
                for prop_name, ld_key in self.json_mapping.items()
                if prop_name in item_map
        }

        # generate @id
        id_template = "_:{s}_{i}"
        _sequential = (id_template.format(i=i, s="{s}") for i in itertools.count())
        gen_id = lambda key: next(_sequential).format(s=key)

        rocrate = ROCrate()

        rocrate.name = metadata["title"][0]
        rocrate.description = metadata["item_title"]
        rocrate.datePublished = metadata["publish_date"]
        rocrate.root_dataset["identifier"] = metadata["control_number"]
        rocrate.root_dataset["uri"] = url_for(
            "invenio_records_ui.recid",
            pid_value=metadata["control_number"], _external=True
        )
        rocrate.root_dataset["wk:publishStatus"] = (
            "public" if metadata["publish_status"] == "0" else "private")
        rocrate.root_dataset["wk:index"] = metadata.get("path", [])
        rocrate.root_dataset["wk:editMode"] = "Keep"


        # wk:feedbackMail
        feedback_mail_list = FeedbackMailList.get_mail_list_by_item_id(
            metadata["control_number"]
        )
        rocrate.root_dataset["wk:feedbackMail"] = feedback_mail_list
        rocrate.root_dataset["wk:index"] = metadata.get("path", [])
        rocrate.root_dataset["wk:editMode"] = "Keep"

        # wk:textExtraction
        for k, v in properties_mapping.items():
            if k.endswith(".filename"):
                list_k_file = v.split(".")[1:]
                break

        extracted_files = kwargs.get("extracted_files", [])
        for file in rocrate.root_dataset.get("hasPart", []):
            for k_file in list_k_file[:-1]:
                file = file[k_file]
            if file[list_k_file[-1]] not in extracted_files:
                file["wk:textExtraction"] = False
                rocrate.add(file)

        # wk:itemLinks
        list_item_link_info = ItemLink.get_item_link_info(
            metadata["control_number"]
        )
        list_entity = []
        list_at_id = []
        for item_link_info in list_item_link_info:
            dict_item_link = {
                "identifier": item_link_info.item_links,
                "value": item_link_info.value
            }
            list_entity.append(dict_item_link)
            list_at_id.append(gen_id("itemLinks"))
        add_list_entity(
            rocrate.root_dataset, "wk:itemLinks", list_at_id, "PropertyValue",
            list_entity
        )

        # wk:metadaAutoFill
        rocrate.root_dataset["wk:metadataAutoFill"] = False



        entity_factory = lambda typename: type(typename, (ContextEntity,), {
            "_empty": lambda self: {
                "@id": self.id,
                "@type": typename
            }
        })

        def add_entity(parent, key, at_id, at_type, data=None, **kwargs):
            """
            Args:
                parent (dict): parent entity
                key (str): the key vocabulary to assign to the entity.
                at_id (str): identifier of entity. "@id" in entity.
                at_type (str): type of entity. "@type" in entity.
                data (dict | None):
                    metadata of entity. Defaults to None and create empty entity.
                **kwargs:
                    metadata of entity.
                    if specified, create entity from kwargs. <br>
                    keyward must be a vocabulary to assign to the value of entity.
            Returns:
                ContextEntity: created entity.
            """
            params = kwargs or data or {}
            entity = entity_factory(at_type)(rocrate, at_id, params)
            parent[key] = entity
            rocrate.add(entity)
            return entity

        def add_list_entity(parent, key, list_at_id, at_type, list_data=None):
            """
            Args:
                parent (dict): parent entity
                key (str): the key vocabulary to assign to the entity.
                list_at_id (list[str]):
                    list of identifier of entity. "@id" in entity.
                at_type (str): type of entity. "@type" in entity.
                list_data (list[dict] | None):
                    metadata of entity. Defaults to None.
            Returns:
                list[ContextEntity]: created entities.
            """
            list_data = list_data or [{} for _ in list_at_id]
            entities = [
                entity_factory(at_type)(rocrate, at_id, params)
                for at_id, params in zip(list_at_id, list_data)
            ]
            parent[key] = entities
            rocrate.add(*entities)
            return entities

        def append_entity(parent, key, at_id, at_type, data=None, **kwargs):
            """
            Args:
                parent (dict): parent entities list
                key (str): the key vocabulary to assign to the entity.
                at_id (str): identifier of entity. "@id" in entity.
                at_type (str): type of entity. "@type" in entity.
                data (dict | None):
                    metadata of entity. Defaults to None and create empty entity.
                **kwargs:
                    metadata of entity.
                    if specified, create entity from kwargs. <br>
                    keyward must be a vocabulary to assign to the value of entity.
            Returns:
                ContextEntity: created entity.
            """
            params = data or {}
            entity = entity_factory(at_type)(rocrate, at_id, params)
            origin = parent[key]
            origin.append(entity)
            parent[key] = origin
            rocrate.add(entity)
            return entity

        def add_property(parent, key, value):
            parent[key] = value
            return parent

        def ensure_entity_list_size(parent, key, at_type, size):
            """Ensure list size including empty entity.

            Args:
                parent (_type_): Parent entity
                key (_type_): Key of ro-crate-metadata.json
                at_type (_type_): _description_
                size (_type_): _description_
            """
            if key not in parent or parent.get(key) is None:
                parent[key] = []

            current_size = len(parent[key])
            for i in range(current_size, size):
                append_entity(parent, key, gen_id(key), at_type)
            return

        def extract_list_indices(meta_props, prop_props, property_map):
            """Exteract list indices.

            Args:
                meta_props (list): _description_
                prop_props (list): _description_
                property_map (dict): _description_

            Returns:
                list: _description_
            """
            list_index = []
            for prop in meta_props:
                m = re.search(r"\[(\d+)\]", prop)
                list_index.append(int(m.group(1)) if m else None)

            # case: list_index > prop_props
            if len(list_index) > len(prop_props):
                list_non_corresponding = []
                definition_key = ""

                for i, meta_key in enumerate(meta_props):
                    definition_key += re.sub(r'\[\d+\]$', '', meta_key)
                    if definition_key not in property_map:
                        list_non_corresponding.append(i)
                    definition_key += "."
                list_index = [
                    index for i, index in enumerate(list_index) if i not in list_non_corresponding
                ]
            # case: list_index < prop_props
            elif len(list_index) < len(prop_props):
                list_non_corresponding = []
                definition_key = ""
                reversed_map = {v: k for k, v in property_map.items()}

                for i, prop_key in enumerate(prop_props):
                    definition_key += prop_key
                    if definition_key not in reversed_map:
                        list_non_corresponding.append(i)
                    definition_key += "."
                for i in sorted(list_non_corresponding):
                    list_index.insert(i, None)
            return list_index

        def gen_type(meta_path):
            """Generate "@type" of entity by using AT_TYPE_MAP.

            Args:
                meta_path (str): Key of metadata.

            Returns:
                str: "@type" of entity.
            """
            for k, v in self.item_map.items():
                if v == meta_path:
                    meta_key = k
                    break

            for k, v in self.AT_TYPE_MAP.items():
                if k in meta_key:
                    return v
            return "PropertyValue"

        def _set_rocrate_metadata(
            parent, META_PATH, META_KEY, meta_props, PROP_PATH, prop_props, deconstructed
        ):
            # Get list_index
            list_index = extract_list_indices(meta_props, prop_props, properties_mapping)

            # case: prop_props = []
            if len(prop_props) == 0:
                raise Exception("prop_props is empty")

            # case: prop_props = [prop]
            if len(prop_props) == 1:
                index = list_index[0] if list_index else None
                prop = prop_props[0]
                at_type = gen_type()
                # at_type = type_map[prop] if prop in type_map else "PropertyValue"

                # dict
                if index is None:
                    # If prop is "@id", do nothing.
                    if prop == "@id":
                        pass
                    # If prop is under root, add property directly.
                    else:
                        parent[prop] = deconstructed[META_KEY]
                # list
                else:
                    ensure_entity_list_size(parent, prop, at_type, index + 1)
                    parent[prop][index] = deconstructed[META_KEY]

                return

            _set_child_rocrate_metadata(
                parent, META_PATH, META_KEY, meta_props, PROP_PATH, prop_props,
                list_index, deconstructed
                )
            return

        def _set_child_rocrate_metadata(
            parent, META_PATH, META_KEY, meta_props, PROP_PATH, prop_props, list_index, deconstructed
        ):
            if len(prop_props) == 0:
                raise Exception("prop_props is empty")

            prop = prop_props[0]
            index = list_index[0] if list_index else None
            at_type = gen_type(META_PATH)

            # dict
            if index is None:
                if len(prop_props) == 1:
                    if prop == "@id":
                        pass
                    else:
                        parent[prop] = deconstructed[META_KEY]
                        rocrate.add(parent)
                else:
                    if "@id" in prop_props:
                        at_id = deconstructed[META_KEY]
                        add_entity(parent, prop, at_id, at_type)
                    else:
                        if prop not in parent:
                            add_entity(
                                parent, prop, gen_id(meta_props[0]), at_type
                            )
                        _set_child_rocrate_metadata(
                            parent[prop], META_PATH, META_KEY, meta_props[1:],
                            PROP_PATH, prop_props[1:], list_index[1:],
                            deconstructed
                        )
            # list
            else:
                if len(prop_props) == 1:
                    if prop not in parent:
                        list_val = ["" for _ in range(index + 1)]
                    else:
                        list_val = parent[prop]
                    if len(list_val) <= index:
                        list_val.extend(
                            ["" for _ in range(index - len(list_val) + 1)]
                        )
                    list_val[index] = deconstructed[META_KEY]
                    parent[prop] = list_val
                    rocrate.add(parent)
                else:
                    ensure_entity_list_size(parent, prop, at_type, index + 1)
                    if isinstance(parent[prop], list):
                        _set_child_rocrate_metadata(
                            parent[prop][index], META_PATH, META_KEY,
                            meta_props[1:], PROP_PATH, prop_props[1:],
                            list_index[1:], deconstructed
                        )
                    else:
                        raise Exception(
                            f"Unexpected structure for prop {prop} at index {index}"
                        )
            return

        deconstructed = self._deconstruct_dict(metadata)

        for record_key in deconstructed:
            if "attribute_value" not in record_key:
                continue

            META_PATH = re.sub(r"\[\d+\]", "", record_key)
            META_KEY = record_key.replace(
                ".attribute_value_mlt", "").replace(".attribute_value", "")
            meta_props = META_KEY.split(".")
            PROP_PATH = properties_mapping[META_PATH] # attribute_value
            prop_props = PROP_PATH.split(".")
            print(f"--- {META_KEY}: {deconstructed[record_key]}, {gen_id(meta_props[0])} ---")

            _set_rocrate_metadata(
                rocrate.root_dataset, META_PATH, META_KEY, meta_props,
                PROP_PATH, prop_props, deconstructed
            )

        # Extra
        extra_field = deconstructed.get(item_map["Extra"], None)
        if extra_field:
            if isinstance(extra_field, dict):
                str_extra_dict = extra_field.get("subitem_text_value")
            else:
                str_extra_dict = extra_field[0].get("subitem_text_value")
            extra_entity = {
                "description": "Metadata which is not able to be mapped",
                "value": str_extra_dict
            }
            add_entity(
                rocrate.root_dataset, "additionalProperty", gen_id("extra"),
                "PropertyValue", extra_entity
            )

        return rocrate
