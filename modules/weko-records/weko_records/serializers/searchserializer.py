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
from invenio_records_rest.serializers.json import JSONSerializer
from weko_records.utils import sort_meta_data_by_options

from flask import json, flash

from weko_index_tree.utils import get_user_roles, get_user_groups, \
    check_roles, check_groups
from weko_index_tree.api import Indexes

class SearchSerializer(JSONSerializer):
    """
    extend JSONSerializer to modify search result
    """

    def transform_search_hit(self, pid, record_hit, links_factory=None):
        sort_meta_data_by_options(record_hit)
        return super(SearchSerializer, self).\
            transform_search_hit(pid, record_hit, links_factory)

    # def serialize_search(self, pid_fetcher, search_result, links=None,
    #                      item_links_factory=None, **kwargs):
    #     """Serialize a search result.
    #
    #     :param pid_fetcher: Persistent identifier fetcher.
    #     :param search_result: Elasticsearch search result.
    #     :param links: Dictionary of links to add to response.
    #     """
    #
    #     # Get user info
    #     roles = get_user_roles()
    #     groups = get_user_groups()
    #
    #     flash(roles)
    #     flash(groups)
    #
    #     indexes = {}
    #     for hit in search_result['hits']['hits']:
    #         is_authorized = True
    #
    #         paths = hit['_source']['_item_metadata']['path']
    #         for path in paths:
    #             index_id = path.split('/')[-1]
    #             if not index_id in indexes:
    #                 indexes[index_id] = dict(Indexes.get_index(index_id))
    #
    #             is_authorized = check_roles(roles,
    #                                         indexes[index_id]['browsing_role']) and \
    #                             check_groups(groups,
    #                                          indexes[index_id]['browsing_group'])
    #
    #         # TODO
    #         if is_authorized:
    #
    #
    #
    #
    #
    #
    #         # index = dict(Indexes.get_index('1538469278676'))
    #
    #     # tree = Indexes.get_index_tree()
    #     # flash(dict(Indexes.get_index('1538469278676')))
    #
    #
    #     return json.dumps(dict(
    #         hits=dict(
    #             hits=[self.transform_search_hit(
    #                 pid_fetcher(hit['_id'], hit['_source']),
    #                 hit,
    #                 links_factory=item_links_factory,
    #                 **kwargs
    #             ) for hit in search_result['hits']['hits']],
    #             total=search_result['hits']['total'],
    #         ),
    #         links=links or {},
    #         aggregations=search_result.get('aggregations', dict()),
    #     ), **self._format_args())

        # return json.dumps(dict(
        #     hits=dict(
        #         hits=[self.transform_search_hit(
        #             pid_fetcher(hit['_id'], hit['_source']),
        #             hit,
        #             links_factory=item_links_factory,
        #             **kwargs
        #         ) for hit in search_result['hits']['hits']],
        #         total=search_result['hits']['total'],
        #     ),
        #     links=links or {},
        #     aggregations=search_result.get('aggregations', dict()),
        # ), **self._format_args())
