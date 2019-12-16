# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Marshmallow based JSON serializer for records."""

from __future__ import absolute_import, print_function

from flask import json, request

from .base import PreprocessorMixin, SerializerMixinInterface
from .marshmallow import MarshmallowMixin


class JSONSerializerMixin(SerializerMixinInterface):
    """Mixin serializing records as JSON."""

    @staticmethod
    def _format_args():
        """Get JSON dump indentation and separates."""
        if request and request.args.get('prettyprint'):
            return dict(
                indent=2,
                separators=(', ', ': '),
            )
        else:
            return dict(
                indent=None,
                separators=(',', ':'),
            )

    def serialize(self, pid, record, links_factory=None, **kwargs):
        """Serialize a single record and persistent identifier.

        :param pid: Persistent identifier instance.
        :param record: Record instance.
        :param links_factory: Factory function for record links.
        """
        return json.dumps(
            self.transform_record(pid, record, links_factory, **kwargs),
            **self._format_args())

    def serialize_search(self, pid_fetcher, search_result, links=None,
                         item_links_factory=None, **kwargs):
        """Serialize a search result.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.
        """
        return json.dumps(dict(
            hits=dict(
                hits=[self.transform_search_hit(
                    pid_fetcher(hit['_id'], hit['_source']),
                    hit,
                    links_factory=item_links_factory,
                    **kwargs
                ) for hit in search_result['hits']['hits']],
                total=search_result['hits']['total'],
            ),
            links=links or {},
            aggregations=search_result.get('aggregations', dict()),
        ), **self._format_args())


class JSONSerializer(JSONSerializerMixin, MarshmallowMixin, PreprocessorMixin):
    """Marshmallow based JSON serializer for records."""
