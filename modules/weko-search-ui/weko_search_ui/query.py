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

"""Query factories for REST API."""

import json
from datetime import datetime
from werkzeug.datastructures import MultiDict

from elasticsearch_dsl.query import Q
from flask import current_app, request
from invenio_records_rest.errors import InvalidQueryRESTError
from weko_index_tree.api import Indexes
from .permissions import search_permission


def default_search_factory(self, search, query_parser=None):
    """Parse query using Weko-Query-Parser. MetaData Search.

    :param self: REST view.
    :param search: Elastic search DSL search instance.
    :param query_parser: Query parser. (Default: ``None``)
    :returns: Tuple with search instance and URL arguments.
    """

    # check permission
    is_perm = search_permission.can()

    def _get_permission_filter():
        mut = []
        if not is_perm:
            mut.append(Q('match', publish_status='0'))
            mut.append(Q('range', date={'lte': 'now/d'}))
        return mut

    def _get_dsearch_query(qs=None):
        """for detail search"""
        kw = ['search_title', 'search_creator', 'subject', 'search_sh',
              'description', 'search_publisher', 'search_contributor',
              'itemtype', 'NIItype', 'format', 'search_id', 'jtitle',
              'language', 'search_spatial', 'search_temporal', 'rights',
              'textversion', 'grantid', 'degreename', 'grantor']
        kd = ['date_s', 'date_e', 'dateofissued_s', 'dateofissued_e',
              'dateofgranted_s', 'dateofgranted_e']

        mut = []
        qv = dict()
        qd = dict()
        qd1 = dict()
        for k in kw:
            kv = request.values.get(k)
            if kv:
                mut.append(Q('query_string', query=kv, default_operator='and', default_field=k))

        i = 0
        while i < 6:
            s = request.values.get(kd[i])
            e = request.values.get(kd[i + 1])
            if s and e:
                s = datetime.strptime(s, '%Y%m%d').strftime('%Y-%m-%d')
                e = datetime.strptime(e, '%Y%m%d').strftime('%Y-%m-%d')

                qv.update(dict(gte=s))
                qv.update(dict(lte=e))
                qd1.update({kd[i].split('_')[0]: qv})

            i += 2

        if qd1:
            qd["range"] = qd1
            mut.append(qd)

        # add  Permission filter by publish date and status
        mt = _get_permission_filter()
        if mt:
            mut.extend(mt)

        if qs:
            mut.append(Q('query_string', query=qs, default_operator='and', fields=['search_*', 'search_*.ja']))

        del qv, qd, qd1

        return Q('bool', must=mut) if mut else Q(), mut

    def _default_parser(qstr=None):
        """Default parser that uses the Q() from elasticsearch_dsl. Full text Search.

        :param qstr: Query string.
        :returns: Query parser.
        """
        # add  Permission filter by publish date and status
        mt = _get_permission_filter()
        # multi keyword search filter
        kmt = _get_dsearch_query()[1]
        if kmt:
            mt.extend(kmt)

        if qstr:
            q_s = Q('multi_match', query=qstr, operator='and',
                    fields=['content.file.content^1.5',
                            'content.file.content.ja^1.2',
                            '_all'],
                    type='most_fields', minimum_should_match='75%')
            mt.append(q_s)
            qur = Q('bool', must=mt)
        else:
            if mt:
                mt.append(Q())
                qur = Q('bool', must=mt)
            else:
                qur = Q()
        return qur

    from invenio_records_rest.facets import default_facets_factory
    from invenio_records_rest.sorter import default_sorter_factory

    query_parser = query_parser or _default_parser

    search_type = request.values.get('search_type')
    qs = request.values.get('q')

    # full text search
    if search_type and '0' in search_type:
        if qs:
            query_q = query_parser(qs)
        else:
            # detail search
            query_q = _get_dsearch_query()[0]
    else:
        # simple search
        query_q = _get_dsearch_query(qs)[0]

    src = {'_source': {'exclude': ['content']}}
    # extr = search._extra.copy()
    # search.update_from_dict(src)
    search._extra.update(src)

    try:
        search = search.query(query_q)
    except SyntaxError:
        current_app.logger.debug(
            "Failed parsing query: {0}".format(
                request.values.get('q', '')),
            exc_info=True)
        raise InvalidQueryRESTError()

    search_index = search._index[0]
    search, urlkwargs = default_facets_factory(search, search_index)
    search, sortkwargs = default_sorter_factory(search, search_index)
    for key, value in sortkwargs.items():
        urlkwargs.add(key, value)

    urlkwargs.add('q', query_q)
    return search, urlkwargs


def item_path_search_factory(self, search):
    """Parse query using Weko-Query-Parser.

    :param self: REST view.
    :param search: Elastic search DSL search instance.
    :returns: Tuple with search instance and URL arguments.
    """

    # check permission
    is_perm = search_permission.can()

    query_q = {
        "query": {
            "match": {
                "path.tree": "@index"
            }
        },
        "aggs": {
            "path": {
                "terms": {
                    "field": "path.tree",
                    "include": "@index|@index/[^/]+"
                },
                "aggs": {
                    "date_range": {
                        "range": {
                            "field": "date",
                            "format": "YYYY-MM-DD",
                            "ranges": [
                                {
                                    "from": "now/d"
                                },
                                {
                                    "to": "now/d"
                                }
                            ]
                        }
                    }
                }
            }
        },
        "post_filter": {
            "term": {
                "path": "@index"
            }
        }
    }

    if not is_perm:
        mut = []
        mut.append({'match': {'publish_status': '0'}})
        mut.append({'range': {'date': {'lte': 'now/d'}}})
        mut.append({'term': query_q['post_filter'].pop('term')})
        query_q['post_filter']['bool'] = {'must': mut}

    # create search query
    q = request.values.get('q')
    if q:
        try:
            fp = Indexes.get_self_path(q)
            if fp:
                query_q = json.dumps(query_q).replace("@index", fp.path)
                query_q = json.loads(query_q)
        except:
            pass

    urlkwargs = MultiDict()
    try:
        # Aggregations.
        extr = search._extra.copy()
        search.update_from_dict(query_q)
        search._extra.update(extr)
    except SyntaxError:
        current_app.logger.debug(
            "Failed parsing query: {0}".format(
                request.values.get('q', '')),
            exc_info=True)
        raise InvalidQueryRESTError()

    from invenio_records_rest.sorter import default_sorter_factory
    search_index = search._index[0]
    search, sortkwargs = default_sorter_factory(search, search_index)
    for key, value in sortkwargs.items():
        urlkwargs.add(key, value)

    urlkwargs.add('q', query_q)
    return search, urlkwargs


weko_search_factory = item_path_search_factory
es_search_factory = default_search_factory
