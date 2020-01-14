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

"""Query parser."""

import json

from flask import current_app, request
from invenio_records_rest.errors import InvalidQueryRESTError
from weko_index_tree.api import Indexes
from weko_search_ui.query import get_item_type_aggs, get_permission_filter
from invenio_search import RecordsSearch


def get_items_by_index_tree(index_tree_id):
    """Get tree items."""
    records_search = RecordsSearch()
    records_search = records_search.with_preference_param().params(
        version=False)
    records_search._index[0] = current_app.config['SEARCH_UI_SEARCH_INDEX']
    search_instance = item_path_search_factory(search=records_search, index_id=index_tree_id)
    search_result = search_instance.execute()
    rd = search_result.to_dict()

    return rd.get('hits').get('hits')


def get_item_changes_by_index(index_tree_id):
    """Get tree items."""
    records_search = RecordsSearch()
    records_search = records_search.with_preference_param().params(
        version=False)
    records_search._index[0] = current_app.config['SEARCH_UI_SEARCH_INDEX']
    search_instance = item_changes_search_factory(search=records_search, index_id=index_tree_id)
    search_result = search_instance.execute()
    rd = search_result.to_dict()

    return rd.get('hits').get('hits')


def item_path_search_factory(search, index_id=None):
    """
    Parse query using Weko-Query-Parser.

    :param search: Elastic search DSL search instance.
    :param index_id: Index Identifier contains item's path
    :returns: Tuple with search instance and URL arguments.
    """
    def _get_index_search_query():
        query_q = {
            "_source": {
                "excludes": ['content']
            },
            "from": "0",
            "size": "10000",
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "path.tree": "@index"
                            }
                        },
                        {
                            "match": {
                                "relation_version_is_last": "true"
                            }
                        }
                    ]
                }
            },
            "aggs": {
                "path": {
                    "terms": {
                        "field": "path.tree",
                        "include": "@index|@index/[^/]+",
                    },
                    "aggs": {
                        "date_range": {
                            "filter": {
                                "match": {"publish_status": "0"}
                            },
                        },
                        "no_available": {
                            "filter": {
                                "bool": {
                                    "must_not": [
                                        {
                                            "match": {
                                                "publish_status": "0"
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }
            },
            "post_filter": {}
        }

        q = index_id
        if q:
            query_q['aggs']['path']['aggs']. \
                update(get_item_type_aggs(search._index[0]))
            mut = get_permission_filter(q)
            mut = list(map(lambda x: x.to_dict(), mut))
            post_filter = query_q['post_filter']
            if mut[0].get('bool'):
                post_filter['bool'] = mut[0]['bool']
            else:
                post_filter['bool'] = {'must': mut}
            if post_filter:
                list_path = Indexes.get_list_path_publish(index_id)
                post_filter['bool']['must'] = []
                post_filter['bool']['must'].append(
                    {
                        "terms": {
                            "path": list_path
                        }
                    }
                )
            # create search query
            if q:
                try:
                    fp = Indexes.get_self_path(q)
                    current_app.logger.debug(query_q)
                    query_q = json.dumps(query_q).replace("@index", fp.path)
                    query_q = json.loads(query_q)
                except BaseException:
                    pass
            return query_q
    # create a index search query
    query_q = _get_index_search_query()
    try:
        # Aggregations.
        extr = search._extra.copy()
        search.update_from_dict(query_q)
        search._extra.update(extr)
    except SyntaxError:
        q = request.values.get('q', '') if index_id is None else index_id
        current_app.logger.debug(
            "Failed parsing query: {0}".format(q),
            exc_info=True)
        raise InvalidQueryRESTError()
    return search


def item_changes_search_factory(search, index_id=None):
    """
    Parse query using Weko-Query-Parser.

    :param search: Elastic search DSL search instance.
    :param index_id: Index Identifier contains item's path
    :returns: Tuple with search instance and URL arguments.
    """
    def _get_index_search_query():
        query_q = {
            "_source": {
                "excludes": ['content']
            },
            "from": "0",
            "size": "10000",
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "path.tree": "@index"
                            }
                        },
                        {
                            "match": {
                                "relation_version_is_last": "true"
                            }
                        }
                    ]
                }
            },
            "aggs": {
                "path": {
                    "terms": {
                        "field": "path.tree",
                        "include": "@index|@index/[^/]+",
                    },
                    "aggs": {
                        "date_range": {
                            "filter": {
                                "match": {"publish_status": "0"}
                            },
                        },
                        "no_available": {
                            "filter": {
                                "bool": {
                                    "must_not": [
                                        {
                                            "match": {
                                                "publish_status": "0"
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }
            },
            "post_filter": {}
        }

        q = index_id
        if q:
            query_q['aggs']['path']['aggs']. \
                update(get_item_type_aggs(search._index[0]))
            mut = get_permission_filter(q)
            mut = list(map(lambda x: x.to_dict(), mut))
            post_filter = query_q['post_filter']
            if mut[0].get('bool'):
                post_filter['bool'] = mut[0]['bool']
            else:
                post_filter['bool'] = {'must': mut}
            if post_filter:
                list_path = Indexes.get_list_path_publish(index_id)
                post_filter['bool']['must'] = []
                post_filter['bool']['must'].append(
                    {
                        "terms": {
                            "path": list_path
                        }
                    }
                )
            # create search query
            if q:
                try:
                    fp = Indexes.get_self_path(q)
                    query_q = json.dumps(query_q).replace("@index", fp.path)
                    query_q = json.loads(query_q)
                except BaseException:
                    pass
            return query_q
    # create a index search query
    query_q = _get_index_search_query()
    try:
        # Aggregations.
        extr = search._extra.copy()
        search.update_from_dict(query_q)
        search._extra.update(extr)
    except SyntaxError:
        q = request.values.get('q', '') if index_id is None else index_id
        current_app.logger.debug(
            "Failed parsing query: {0}".format(q),
            exc_info=True)
        raise InvalidQueryRESTError()
    return search
