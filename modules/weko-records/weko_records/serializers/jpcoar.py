# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""WEKO Search Serializer."""

import copy
from datetime import datetime

import pytz
from flask import current_app, flash, json, request, url_for
from invenio_records_rest.serializers.json import JSONSerializer
from weko_index_tree.api import Index

from weko_records.api import Mapping

from .dc import DcWekoBaseExtension, DcWekoEntryExtension
from .feed import WekoFeedGenerator
from .opensearch import OpensearchEntryExtension, OpensearchExtension
from .prism import PrismEntryExtension, PrismExtension


class JpcoarSerializer(JSONSerializer):
    """Serialize search result to jpcoar format."""

    def serialize_search(self, pid_fetcher, search_result, links=None,
                         item_links_factory=None, **kwargs):
        """Serialize a search result.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: search engine search result.
        :param links: Dictionary of links to add to response.

        """
        fg = WekoFeedGenerator()

        # Add extentions
        fg.register_extension('dc',
                              DcWekoBaseExtension,
                              DcWekoEntryExtension)
        fg.register_extension('opensearch',
                              extension_class_feed=OpensearchExtension,
                              extension_class_entry=OpensearchEntryExtension)
        fg.register_extension('prism',
                              extension_class_feed=PrismExtension,
                              extension_class_entry=PrismEntryExtension)

        # Set totalResults
        _totalResults = search_result['hits']['total']['value']
        fg.opensearch.totalResults(str(_totalResults))

        startPage = request.args.get('page_no', type=str)
        startPage = 1 if startPage is None or not startPage.isnumeric() else int(startPage)

        size = request.args.get('list_view_num', type=str)
        size = 20 if size is None or not size.isnumeric() else int(size)

        # Set startIndex
        _startIndex = (startPage - 1) * size + 1
        fg.opensearch.startIndex(str(_startIndex))

        # Set itemPerPage
        _itemPerPage = len(search_result['hits']['hits'])
        fg.opensearch.itemsPerPage(str(_itemPerPage))

        for hit in search_result['hits']['hits']:
            fe = fg.add_entry()

            # Set item url
            _pid = hit['_source']['_item_metadata']['control_number']
            item_url = request.host_url + 'records/' + _pid
            fe.itemUrl(item_url)

            # Set item record
            item_metadata = {'metadata': hit['_source'].copy()}
            fe.itemData(item_metadata)

        return fg.jpcoar_str(pretty=True)
