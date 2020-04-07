# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""WEKO Search Serializer."""

from flask import current_app, flash, json, render_template, \
    render_template_string, request
from invenio_records_rest.schemas.json import RecordSchemaJSONV1
from invenio_records_rest.serializers.json import JSONSerializer

from .atom import AtomSerializer
from .jpcoar import JpcoarSerializer
from .rss import RssSerializer


class OpenSearchSerializer(JSONSerializer):
    """Extend JSONSerializer to modify search result."""

    def serialize_search(self, pid_fetcher, search_result, links=None,
                         item_links_factory=None, **kwargs):
        """Serialize a search result.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.

        """
        format = request.values.get('format')
        if format and format == 'atom':
            mimetype = 'application/atom+xml'
            atom_v1 = AtomSerializer(RecordSchemaJSONV1)
            return atom_v1.serialize_search(pid_fetcher, search_result,
                                            links=None, item_links_factory=None,
                                            **kwargs), mimetype
        elif format and format == 'rss':
            mimetype = 'application/rss+xml'
            rss_v1 = RssSerializer(RecordSchemaJSONV1)
            return rss_v1.serialize_search(pid_fetcher, search_result,
                                           links=None, item_links_factory=None,
                                           **kwargs), mimetype
        elif format and format == 'jpcoar':
            mimetype = 'application/xml'
            jpcoar_v1 = JpcoarSerializer(RecordSchemaJSONV1)
            return jpcoar_v1.serialize_search(pid_fetcher, search_result,
                                              links=None, item_links_factory=None,
                                              **kwargs), mimetype
        else:
            mimetype = 'application/json'
            json_v1 = JSONSerializer(RecordSchemaJSONV1)
            return json_v1.serialize_search(pid_fetcher, search_result,
                                            links=None, item_links_factory=None,
                                            **kwargs), mimetype
