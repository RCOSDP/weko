# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""WEKO Search Serializer."""

from invenio_records_rest.serializers.json import JSONSerializer

from .utils import OpenSearchDetailData


class AtomSerializer(JSONSerializer):
    """Serialize search result to atom format."""

    def serialize_search(self, pid_fetcher, search_result, links=None,
                         item_links_factory=None, **kwargs):
        """Serialize a search result.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.
        :param item_links_factory:
        """
        detail_data = OpenSearchDetailData(pid_fetcher, search_result,
                                           OpenSearchDetailData.OUTPUT_ATOM,
                                           links, item_links_factory, **kwargs)
        return detail_data.output_open_search_detail_data()
