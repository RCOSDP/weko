# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2022 CERN.
# Copyright (C) 2022 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Percolator."""

import json

from flask import current_app
from invenio_indexer.api import RecordIndexer
from invenio_search import current_search, current_search_client
from invenio_search.engine import search
from invenio_search.utils import build_index_name

from invenio_oaiserver.query import query_string_parser


def _build_percolator_index_name(index):
    """Build percolator index name."""
    suffix = "-percolators"
    return build_index_name(index, suffix=suffix, app=current_app)


def _create_percolator_mapping(index, mapping_path=None):
    """Update mappings with the percolator field.

    .. note::

        This is only needed from ElasticSearch v5 onwards, because percolators
        are now just a special type of field inside mappings.
    """
    percolator_index = _build_percolator_index_name(index)
    if not mapping_path:
        mapping_path = current_search.mappings[index]
    if not current_search_client.indices.exists(percolator_index):
        with open(mapping_path, "r") as body:
            mapping = json.load(body)
            mapping["mappings"]["properties"].update(PERCOLATOR_MAPPING["properties"])
            current_search_client.indices.create(index=percolator_index, body=mapping)


PERCOLATOR_MAPPING = {"properties": {"query": {"type": "percolator"}}}


def _new_percolator(spec, search_pattern):
    """Create new percolator associated with the new set."""
    if spec and search_pattern:
        query = query_string_parser(search_pattern=search_pattern).to_dict()
        oai_records_index = current_app.config["OAISERVER_RECORD_INDEX"]
        for index, mapping_path in current_search.mappings.items():
            # Skip indices/mappings not used by OAI-PMH
            if not index.startswith(oai_records_index):
                continue
            # Create the percolator doc_type in the existing index for >= ES5
            # TODO: Consider doing this only once in app initialization
            try:
                _create_percolator_mapping(index, mapping_path)
                current_search_client.index(
                    index=_build_percolator_index_name(index),
                    id="oaiset-{}".format(spec),
                    body={"query": query},
                )
            except Exception as e:
                current_app.logger.warning(e)


def _delete_percolator(spec, search_pattern):
    """Delete percolator associated with the removed/updated oaiset."""
    oai_records_index = current_app.config["OAISERVER_RECORD_INDEX"]
    # Create the percolator doc_type in the existing index for >= ES5
    for index, mapping_path in current_search.mappings.items():
        # Skip indices/mappings not used by OAI-PMH
        if not index.startswith(oai_records_index):
            continue
        current_search_client.delete(
            index=_build_percolator_index_name(index),
            id="oaiset-{}".format(spec),
            ignore=[404],
        )


def create_percolate_query(
    percolator_ids=None,
    documents=None,
    document_search_ids=None,
    document_search_indices=None,
):
    """Create percolate query for provided arguments."""
    queries = []
    # documents or (document_search_ids and document_search_indices) has to be set
    # TODO: discuss if this is needed or documents alone is enough.
    if documents is not None:
        queries.append(
            {
                "percolate": {
                    "field": "query",
                    "documents": documents,
                }
            }
        )
    elif (
        document_search_ids is not None
        and document_search_indices is not None
        and len(document_search_ids) == len(document_search_indices)
    ):
        queries.extend(
            [
                {
                    "percolate": {
                        "field": "query",
                        "index": search_index,
                        "id": search_id,
                        "name": f"{search_index}:{search_id}",
                    }
                }
                for (search_id, search_index) in zip(
                    document_search_ids, document_search_indices
                )
            ]
        )
    else:
        raise Exception(
            "Either documents or (document_search_ids and document_search_indices) must be specified."
        )

    if percolator_ids:
        queries.append({"ids": {"values": percolator_ids}})

    query = {"query": {"bool": {"must": queries}}}
    return query


def percolate_query(
    percolator_index,
    percolator_ids=None,
    documents=None,
    document_search_ids=None,
    document_search_indices=None,
):
    """Get results for a percolate query."""
    query = create_percolate_query(
        percolator_ids=percolator_ids,
        documents=documents,
        document_search_ids=document_search_ids,
        document_search_indices=document_search_indices,
    )
    result = search.helpers.scan(
        current_search_client,
        index=percolator_index,
        query=query,
        scroll="1m",
    )
    return result


def sets_search_all(records):
    """Retrieve sets for provided records."""
    if not records:
        return []

    # TODO: records should all have the same index. maybe add index as parameter?
    record_index = RecordIndexer()._record_to_index(records[0])
    _create_percolator_mapping(record_index)
    percolator_index = _build_percolator_index_name(record_index)
    record_sets = [[] for _ in range(len(records))]

    result = percolate_query(percolator_index, documents=records)

    prefix = "oaiset-"
    prefix_len = len(prefix)

    for s in result:
        set_index_id = s["_id"]
        if set_index_id.startswith(prefix):
            set_spec = set_index_id[prefix_len:]
            for record_index in s.get("fields", {}).get(
                "_percolator_document_slot", []
            ):
                record_sets[record_index].append(set_spec)
    return record_sets


def find_sets_for_record(record):
    """Fetch a record's sets."""
    return sets_search_all([record])[0]
