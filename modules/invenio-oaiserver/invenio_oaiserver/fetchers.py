# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2022 CERN.
# Copyright (C) 2021 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Persistent identifier fetchers."""

from invenio_pidstore.errors import PersistentIdentifierError
from invenio_pidstore.fetchers import FetchedPID
from invenio_search.engine import dsl

from .models import OAISet
from .provider import OAIIDProvider
from .query import query_string_parser


def oaiid_fetcher(record_uuid, data):
    """Fetch a record's identifier.

    :param record_uuid: The record UUID.
    :param data: The record data.
    :returns: A :class:`invenio_pidstore.fetchers.FetchedPID` instance.
    """
    pid_value = data.get("_oai", {}).get("id")
    if pid_value is None:
        raise PersistentIdentifierError()

    return FetchedPID(
        provider=OAIIDProvider,
        pid_type=OAIIDProvider.pid_type,
        pid_value=str(pid_value),
    )


def set_records_query_fetcher(setSpec):
    """Fetch query to retrieve records based on provided set spec."""
    set = OAISet.query.filter(OAISet.spec == setSpec).first()
    if set is None:
        # raise error that no matches can be found ?
        query = dsl.Q("match_none")
    else:
        query = dsl.Q(query_string_parser(set.search_pattern))

    return query
