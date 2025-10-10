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

from flask import current_app
from invenio_records_rest.errors import InvalidQueryRESTError
from invenio_search import RecordsSearch
from weko_index_tree.api import Indexes
from weko_schema_ui.models import PublishStatus
from weko_search_ui.utils import execute_search_with_pagination

from .config import WEKO_ROOT_INDEX


def get_items_by_index_tree(index_tree_id):
    """Get tree items."""
    records_search = RecordsSearch()
    records_search = records_search.with_preference_param().params(
        version=False)
    records_search = records_search.sort({"control_number": {"order": "asc"}})
    records_search._index[0] = current_app.config['SEARCH_UI_SEARCH_INDEX']
    search_instance = item_path_search_factory(
        search=records_search,
        index_id=index_tree_id
    )
    return execute_search_with_pagination(search_instance, -1)


def get_item_changes_by_index(index_tree_id, date_from, date_until):
    """Get tree items."""
    records_search = RecordsSearch()
    records_search = records_search.with_preference_param().params(
        version=False)
    records_search._index[0] = current_app.config['SEARCH_UI_SEARCH_INDEX']
    search_instance = item_changes_search_factory(
        search=records_search,
        index_id=index_tree_id,
        date_from=date_from,
        date_until=date_until
    )
    return execute_search_with_pagination(search_instance, -1)


def item_path_search_factory(search, index_id="0"):
    """Parse query using Weko-Query-Parser.

    :param search: Elastic search DSL search instance.
    :param index_id: Index Identifier contains item's path
    :returns: Tuple with search instance and URL arguments.
    """
    def _get_index_search_query():
        """Get index search query."""
        query_q = {
            "from": 0,
            "size": 10000,
            "_source": {
                "excludes": [
                    "content",
                    "_item_metadata"
                ]
            },
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
            "post_filter": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "publish_status": PublishStatus.PUBLIC.value
                            }
                        },
                        {
                            "range": {
                                "publish_date": {
                                    "lte": "now/d"
                                }
                            }
                        }
                    ]
                }
            }
        }

        q = str(index_id)
        if q != str(current_app.config.get("WEKO_ROOT_INDEX", WEKO_ROOT_INDEX)):
            post_filter = query_q['post_filter']

            if post_filter:
                list_path = Indexes.get_list_path_publish(index_id)
                post_filter['bool']['must'].append({
                    "terms": {
                        "path": list_path
                    }
                })
            # create search query
            try:
                query_q = json.dumps(query_q).replace("@index", q)
                query_q = json.loads(query_q)
            except BaseException:
                pass
        else:
            post_filter = query_q['post_filter']

            if post_filter:
                list_path = Indexes.get_list_path_publish(index_id)
                post_filter['bool']['must'].append({
                    "terms": {
                        "path": list_path
                    }
                })
            wild_card = []
            child_list = Indexes.get_child_list(q)
            if child_list:
                for item in child_list:
                    wc = {
                        "wildcard": {
                            "path.tree": item.cid
                        }
                    }
                    wild_card.append(wc)
                query_q['query']['bool']['must'] = [
                    {
                        "bool": {
                            "should": wild_card
                        }
                    },
                    {
                        "match": {
                            "relation_version_is_last": "true"
                        }
                    }
                ]
        return query_q

    # create a index search query
    query_q = _get_index_search_query()
    try:
        # Aggregations.
        extr = search._extra.copy()
        search.update_from_dict(query_q)
        search._extra.update(extr)
    except SyntaxError:
        current_app.logger.debug("Failed parsing query: {0}".format(query_q),
                                 exc_info=True)
        raise InvalidQueryRESTError()

    return search


def item_changes_search_factory(search,
                                index_id=0,
                                date_from="now/d",
                                date_until="now/d"):
    """
    Parse query using Weko-Query-Parser.

    :param search: Elastic search DSL search instance.
    :param index_id: Index Identifier contains item's path
    :returns: Tuple with search instance and URL arguments.
    """
    def _get_index_search_query(_date_from: str, _date_until: str) -> dict:
        query_q = {
            "from": 0,
            "size": 10000,
            "_source": {
                "excludes": [
                    "content",
                    "_item_metadata"
                ]
            },
            "query": {
                "bool": {
                    "should": [
                        {
                            "match": {
                                "path.tree": "@index"
                            }
                        },
                        {
                            "bool": {
                                "must_not": {
                                    "exists": {
                                        "field": "path.tree"
                                    }
                                }
                            }
                        }
                    ]
                }
            },
            "sort": [
                {
                    "_updated": {
                        "order": "asc"
                    }
                }
            ],
            "post_filter": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "publish_date": {
                                    "lte": "now/d"
                                }
                            }
                        }
                    ],
                    "should": [
                        {
                            "terms": {
                                "path": []
                            }
                        }
                    ]
                }
            }
        }

        q = str(index_id)
        if q != str(current_app.config.get("WEKO_ROOT_INDEX", WEKO_ROOT_INDEX)):
            post_filter = query_q['post_filter']

            if post_filter:
                list_path = Indexes.get_list_path_publish(index_id)
                post_filter['bool']['should'] = {
                    "terms": {
                        "path": list_path
                    }
                }
                post_filter['bool']['must'].append({
                    "range": {
                        "_updated": {
                            "lte": _date_until,
                            "gte": _date_from
                        }
                    }
                })
            # create search query
            try:
                query_q = json.dumps(query_q).replace("@index", q)
                query_q = json.loads(query_q)
            except BaseException:
                pass
        else:
            post_filter = query_q['post_filter']
            if post_filter:
                list_path = Indexes.get_list_path_publish(index_id)
                post_filter['bool']['must'].append({
                    "terms": {
                        "path": list_path
                    }
                })
                post_filter['bool']['must'].append({
                    "range": {
                        "_updated": {
                            "lte": _date_until,
                            "gte": _date_from
                        }
                    }
                })
            # create search query
            wild_card = []
            child_list = Indexes.get_child_list(q)
            if child_list:
                for item in child_list:
                    wc = {
                        "wildcard": {
                            "path.tree": item.cid
                        }
                    }
                    wild_card.append(wc)
                query_q['query']['bool']['should'] = [
                    {
                        "bool": {
                            "should": wild_card
                        }
                    },
                    {
                        "match": {
                            "relation_version_is_last": "true"
                        }
                    }
                ]
        return query_q

    # create a index search query
    query_q = _get_index_search_query(date_from, date_until)

    try:
        search.update_from_dict(query_q)
    except SyntaxError:
        current_app.logger.debug("Failed parsing query: {0}".format(query_q),
                                 exc_info=True)
        raise InvalidQueryRESTError()

    return search
