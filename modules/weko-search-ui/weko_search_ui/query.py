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

from datetime import datetime
from functools import partial

from elasticsearch_dsl.query import Q
from flask import current_app, request
from invenio_records_rest.errors import InvalidQueryRESTError


def default_search_factory(self, search, query_parser=None):
    """Parse query using Weko-Query-Parser.

    :param self: REST view.
    :param search: Elastic search DSL search instance.
    :param query_parser: Query parser. (Default: ``None``)
    :returns: Tuple with search instance and URL arguments.
    """
    def _get_dsearch_query():
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
                mut.append(dict(match={k: kv}))

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

        qs = request.values.get('q')
        if qs:
            for s in qs.split(" "):
                mut.append({"query_string": dict(query=s)})

        del qv, qd, qd1

        return Q('bool', must=mut)

    def _default_parser(qstr=None):
        """Default parser that uses the Q() from elasticsearch_dsl.

        :param qstr: Query string.
        :returns: Query parser.
        """
        nd = datetime.today().strftime('%Y-%m-%d')
        if qstr:
            return Q(
                'filtered',
                query=Q(
                    'bool',
                    should=[
                        Q('has_child', type='content', query=Q('bool', must=[
                            Q('multi_match', query=qstr,
                              fields=['file.content.en*^1.5',
                                      'file.content.jp'], type='most_fields',
                              minimum_should_match='75%')]),
                          inner_hits={'fields': ['file.content']}),
                        Q('query_string', query=qstr)
                    ]
                ),
                # filter=Q('range', date={'lte': nd})
            )

        return Q()

    from invenio_records_rest.facets import default_facets_factory
    from invenio_records_rest.sorter import default_sorter_factory

    query_parser = query_parser or _default_parser

    qs = request.values.get('q')
    query_q = _get_dsearch_query()
    if (len(query_q.must) == 1 and qs) or (len(query_q.must) < 1 and not qs):
        query_q = query_parser(qs)

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


es_search_factory = default_search_factory


def weko_search_parser(search_factory):
    """Set the default search factory to use Weko-query-parser.

    :param search_factory: Search factory.
    :returns: Partial function.
    """
    from invenio_query_parser.contrib.elasticsearch import IQ
    return partial(default_search_factory, query_parser=IQ)


weko_search_factory = weko_search_parser(default_search_factory)
