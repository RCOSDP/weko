# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Search-Ui is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Harvest records from an OAI-PMH repository."""

import os
import xmltodict
from datetime import date
from functools import partial

from flask import current_app

from weko_records.api import Mapping, ItemTypes
from weko_records.models import ItemType
from weko_records.serializers.utils import get_full_mapping

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
        for prop_k, prop_v in self.itemtype.schema["properties"].items():
            self._apply_property(item_map, "", "", prop_k, prop_v)
        return item_map

    def _apply_property(self, item_map, key, value, prop_k, prop_v):
        """
            This process is part of “_create_item_map” and is not
            intended for any other use.
        """
        if "title" in prop_v:
            key = key + "." + prop_v["title"] if key else prop_v["title"]
            value = value + "." + prop_k if value else prop_k

        if prop_v["type"] == "object":
            for child_k, child_v in prop_v["properties"].items():
                self._apply_property(item_map, key, value, child_k, child_v)
        elif prop_v["type"] == "array":
            self._apply_property(
                item_map, key, value, "items", prop_v["items"])
        else:
            item_map[key] = value


class JsonLdMapper(JsonMapper):
    """JsonLdMapper."""
    def __init__(self, itemtype_id, json_mapping):
        """Init."""
        self.json_mapping = json_mapping
        super().__init__(None, itemtype_id)

    def map_to_itemtype(self, json_ld):
        """Map to item type."""
        metadata = JsonLdMapper.process_json_ld(json_ld)
        item_map = self._create_item_map()
        mapped_metadata = {

        }

        # result = {
        #     "pubdate": self.json_id.get("datePublished"),
        #     "publish_status": "private",
        #     "path": self.json_id.get("wk:index"),
        #     "item_1617186331708": {},
        #     "item_1617258105262": {},
        #     ...
        # }
        return mapped_metadata

    @staticmethod
    def process_json_ld(json_ld):
        """Process json-ld.

        Make metadata json-ld data flat.
        Pick up metadata from @graph and resolve links
        to be able to use in mapping to WEKO item type.

        Note:
            SWORDBagIt metadata format is not supported yet.

        Args:
            json_ld (dict): Json-ld data.

        Returns:
            dict: Processed json data.
        """
        metadata = {}
        context = json_ld.get("@context", "")
        format = ""
        # check if the json-ld context is valid
        if "https://swordapp.github.io/swordv3/swordv3.jsonld" in context:
            # TODO: support SWORD json-ld format
            format = "sword-bagit"
            pass
        elif (
            "https://w3id.org/ro/crate/1.1/context" in context
                or isinstance(context, dict)
                and "https://w3id.org/ro/crate/1.1/context" in context.values()
            ):
            # check structure of RO-Crate json-ld
            format = "ro-crate"
            if "@graph" not in json_ld or not isinstance(json_ld.get("@graph"), list):
                raise ValueError('Invalid json-ld format: "@graph" is not found.')
            # transform list which contains @id to dict in @graph
            for v in json_ld.get("@graph"):
                if isinstance(v, dict) and "@id" in v:
                    metadata.update({v["@id"]: v})
                else:
                    raise ValueError('Invalid json-ld format: Objects without "@id" are directly under "@graph"')
        else:
            raise ValueError('Invalid json-ld format: "@context" is not found.')
        if metadata is None:
            raise ValueError("Invalid json-ld format: Metadata is not found.")


        def _resolve_link(parent, key, value):
            if isinstance(value, dict):
                if len(value) == 1 and "@id" in value and value["@id"] in metadata:
                    parent[key] = metadata[value["@id"]]
                else:
                    for k, v in value.items():
                        _resolve_link(value, k, v)
            elif isinstance(value, list):
                for i, v in enumerate(value):
                    _resolve_link(value, i, v)

        # Restore metadata to tree structure by tracing "@id" in linked data
        for key, value in metadata.items():
            _resolve_link(metadata, key, value)

        processed_metadata = {}

        def _parse_metadata(parent, key, value):
            if "@type" in key:
                return
            if isinstance(value, dict):
                for k, v in value.items():
                    key_name = key if parent == "" else f"{parent}.{key}"
                    _parse_metadata(key_name, k, v)
            elif isinstance(value, list):
                for i, d in enumerate(value):
                    key_name = f"{key}[{i}]" if parent == "" else f"{parent}.{key}[{i}]"
                    if isinstance(d, dict):
                        for k, v in d.items():
                            _parse_metadata(key_name, k, v)
                    else:
                        processed_metadata[key_name] = d
            else:
                key_name = key if parent == "" else f"{parent}.{key}"
                processed_metadata[key_name] = value

        # Get the root of the metadata tree structure
        root = metadata.get(
            current_app.config["WEKO_SWORDSERVER_METADATA_FILE_ROCRATE"]
            ).get("about").get("@id")
        if not root in metadata:
            msg = "Invalid json-ld format: Root object is not found."
            raise ValueError(msg)

        for key, value in metadata.get(root).items():
            _parse_metadata("", key, value)

        return processed_metadata, format
