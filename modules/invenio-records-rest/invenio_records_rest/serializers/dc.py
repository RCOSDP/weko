# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Marshmallow based DublinCore serializer for records."""

from __future__ import absolute_import, print_function

from dcxml import simpledc
from invenio_records.api import Record

from .base import PreprocessorMixin, SerializerMixinInterface
from .marshmallow import MarshmallowMixin


class DublinCoreSerializer(SerializerMixinInterface, MarshmallowMixin,
                           PreprocessorMixin):
    """Marshmallow based DublinCore serializer for records.

    Note: This serializer is not suitable for serializing large number of
    records.
    """

    def serialize(self, pid, record, links_factory=None):
        """Serialize a single record and persistent identifier.

        :param pid: Persistent identifier instance.
        :param record: Record instance.
        :param links_factory: Factory function for record links.
        """
        return simpledc.tostring(
            self.transform_record(pid, record, links_factory))

    def serialize_search(self, pid_fetcher, search_result, links=None,
                         item_links_factory=None):
        """Serialize a search result.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.
        """
        records = []
        for hit in search_result['hits']['hits']:
            records.append(simpledc.tostring(self.transform_search_hit(
                pid_fetcher(hit['_id'], hit['_source']),
                hit,
                links_factory=item_links_factory,
            )))

        return "\n".join(records)

    def serialize_oaipmh(self, pid, record):
        """Serialize a single record for OAI-PMH."""
        obj = self.transform_record(pid, record['_source']) \
            if isinstance(record['_source'], Record) \
            else self.transform_search_hit(pid, record)

        return simpledc.dump_etree(obj)
