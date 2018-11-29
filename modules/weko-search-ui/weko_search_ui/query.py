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
from functools import partial

from elasticsearch_dsl.query import Q
from flask import current_app, request, flash
from flask_security import current_user
from invenio_records_rest.errors import InvalidQueryRESTError
from weko_index_tree.api import Indexes
from werkzeug.datastructures import MultiDict

from .permissions import search_permission
from invenio_communities.models import Community


def get_item_type_aggs(search_index):
    """
     get item types aggregations
    :return: aggs dict
    """
    return current_app.config['RECORDS_REST_FACETS']. \
        get(search_index).get("aggs", {})


def get_permission_filter(comm_id=None):
    # check permission
    is_perm = search_permission.can()
    mut = []
    match = Q('match', publish_status='0')
    # ava = [Q('range', **{'date.value': {'lte': 'now/d'}}),
    #        Q('term', **{'date.dateType': 'Available'})]
    # rng = Q('nested', path='date', query=Q('bool', must=ava))
    ava = Q('range', **{'publish_date': {'lte': 'now/d'}})
    rng = ava
    mst = []
    if comm_id is not None:
        path_list = Indexes.get_all_path_list(comm_id)
        match_list=[]
        for p_l in path_list:
            match_q = Q('match', path=p_l)
            match_list.append(match_q)
        mst.append(Q('bool', should=match_list))
    if not is_perm:
        mut.append(match)
        mut.append(rng)
        mut.append(get_index_filter()[0])
    else:
        user_id, result = check_admin_user()
        if result:
            shuld = [Q('match', weko_creator_id=user_id)]
            mut2 = [match, rng]
            shuld.append(Q('bool', must=mut2))
            if comm_id is not None:
                mut.append(Q('bool', should=shuld, must=mst))
            else:
                mut.append(Q('bool', should=shuld, must=get_index_filter()))

    return mut


def get_index_filter():

    paths = Indexes.get_browsing_tree_paths()
    mst = []
    q_list = []
    for path in paths:
        match_q = Q('match', path=path)
        q_list.append(match_q)
    mst.append(Q('bool', should=q_list))

    return mst


def default_search_factory(self, search, query_parser=None, search_type=None):
    """Parse query using Weko-Query-Parser. MetaData Search.

    :param self: REST view.
    :param search: Elastic search DSL search instance.
    :param query_parser: Query parser. (Default: ``None``)
    :returns: Tuple with search instance and URL arguments.
    """

    def _get_search_qs_query(qs=None):
        """
        qs of search bar keywords for detail simple search.
        :param qs: Query string.
        :return: Query parser.
        """
        q = Q('query_string', query=qs, default_operator='and',
              fields=['search_*', 'search_*.ja']) if qs else None
        return q

    def _get_detail_keywords_query():
        """
        Get keywords query
        :return: Query parser.
        """

        def _get_keywords_query(k, v):
            qry = None
            kv = request.values.get(k)
            if not kv:
                return

            if isinstance(v, str):
                name_dict = dict(operator="and")
                name_dict.update(dict(query=kv))
                qry = Q('match', **{v: name_dict})
            elif isinstance(v, list):
                qry = Q('multi_match', query=kv, type='most_fields',
                        minimum_should_match='75%',
                        operator='and', fields=v)
            elif isinstance(v, dict):
                for key, vlst in v.items():
                    if isinstance(vlst, list):
                        shud = []
                        kvl = [x for x in kv.split(',')
                              if x.isdecimal() and int(x) < len(vlst)]
                        for j in map(partial(lambda x, y: x[int(y)], vlst), kvl):
                            name_dict = dict(operator="and")
                            name_dict.update(dict(query=j))
                            shud.append(Q('match', **{key: name_dict}))

                        kvl = [x for x in kv.split(',')
                               if not x.isdecimal() and x in vlst]
                        for j in kvl:
                            name_dict = dict(operator="and")
                            name_dict.update(dict(query=j))
                            shud.append(Q('match', **{key: name_dict}))
                        if shud:
                            return Q('bool', should=shud)
            elif isinstance(v, tuple) and len(v) >= 2:
                shud = []
                for i in map(lambda x: v[1](x), kv.split(',')):
                    shud.append(Q('term', **{v[0]: i}))
                if shud:
                    qry = Q('bool', should=shud)

            return qry

        def _get_nested_query(k, v):
            # text value
            kv = request.values.get(k)
            if not kv:
                return

            shuld = []
            if isinstance(v, tuple) and len(v) > 1 and isinstance(v[1], dict):
                # attr keyword in request url
                for attr_key, attr_val_str in map(lambda x: (x, request.values.get(x)), list(v[1].keys())):
                    attr_obj = v[1].get(attr_key)
                    if isinstance(attr_obj, dict) and attr_val_str:
                        if isinstance(v[0], str) and not len(v[0]):
                            # For ID search
                            for key in attr_val_str.split(','):
                                attr = attr_obj.get(key)
                                if isinstance(attr, tuple):
                                    attr = [attr]

                                if isinstance(attr, list):
                                    for alst in attr:
                                        if isinstance(alst, tuple):
                                            val_attr_lst = alst[1].split('=')
                                            name = alst[0] + ".value"
                                            name_dict = dict(operator="and")
                                            name_dict.update(dict(query=kv))
                                            mut = [Q('match', **{name: name_dict})]

                                            qt = None
                                            if '=*' not in alst[1]:
                                                name = alst[0] + "." + val_attr_lst[0]
                                                qt = [Q('term', **{name: val_attr_lst[1]})]

                                            mut.extend(qt or [])
                                            qry = Q('bool', must=mut)
                                            shuld.append(Q('nested', path=alst[0], query=qry))
                        else:
                            attr_key_hit = [x for x in attr_obj.keys() if v[0] + "." in x]
                            if attr_key_hit:
                                vlst = attr_obj.get(attr_key_hit[0])
                                if isinstance(vlst, list):
                                    attr_val = [x for x in attr_val_str.split(',')
                                                if x.isdecimal() and int(x) < len(vlst)]
                                    if attr_val:
                                        shud = []
                                        name = v[0] + ".value"
                                        name_dict = dict(operator="and")
                                        name_dict.update(dict(query=kv))
                                        qm = Q('match', **{name: name_dict})

                                        for j in map(partial(lambda m, n: m[int(n)], vlst), attr_val):
                                            name = attr_key_hit[0]
                                            qm = Q('term', **{name: j})
                                            shud.append(qm)

                                        shuld.append(Q('nested', path=v[0],
                                                       query=Q('bool', should=shud, must=[qm])))

            return Q('bool', should=shuld) if shuld else None

        def _get_date_query(k, v):
            # text value
            qry = None
            if isinstance(v, list) and len(v) >= 2:
                date_from = request.values.get(k + "_" + v[0][0])
                date_to = request.values.get(k + "_" + v[0][1])
                if not date_from or not date_to:
                    return

                date_from = datetime.strptime(date_from, '%Y%m%d').strftime('%Y-%m-%d')
                date_to = datetime.strptime(date_to, '%Y%m%d').strftime('%Y-%m-%d')

                qv = {}
                qv.update(dict(gte=date_from))
                qv.update(dict(lte=date_to))
                if isinstance(v[1], str):
                    qry = Q('range', **{v[1]: qv})
                elif isinstance(v[1], tuple) and len(v[1]) >= 2:
                    path = v[1][0]
                    dt = v[1][1]
                    if isinstance(dt, dict):
                        for attr_key, attr_val_str in map(lambda x: (x, request.values.get(x)), list(dt.keys())):
                            attr_obj = dt.get(attr_key)
                            if isinstance(attr_obj, dict) and attr_val_str:
                                attr_key_hit = [x for x in attr_obj.keys() if path + "." in x]
                                if attr_key_hit:
                                    vlst = attr_obj.get(attr_key_hit[0])
                                    if isinstance(vlst, list):
                                        attr_val = [x for x in attr_val_str.split(',')]
                                        shud = []
                                        for j in map(partial(lambda m, n: m[int(n)], vlst), attr_val):
                                            qt = Q('term', **{attr_key_hit[0]: j})
                                            shud.append(qt)

                                        qry = Q('range', **{path + ".value": qv})
                                        qry = Q('nested', path=path, query=Q('bool', should=shud, must=[qry]))
            return qry

        kwd = current_app.config['WEKO_SEARCH_KEYWORDS_DICT']
        ks = kwd.get('string')
        kd = kwd.get('date')
        kn = kwd.get('nested')

        mut = []
        try:
            for k, v in ks.items():
                qy = _get_keywords_query(k, v)
                if qy:
                    mut.append(qy)

            for k, v in kn.items():
                qy = _get_nested_query(k, v)
                if qy:
                    mut.append(qy)

            for k, v in kd.items():
                qy = _get_date_query(k, v)
                if qy:
                    mut.append(qy)
        except Exception as e:
            current_app.logger.exception(
                'Detail search query parser failed. err:{0}'.format(e))
        return mut

    def _get_simple_search_query(qs=None):
        """
          query parser for simple search
        :param qs: Query string.
        :return: Query parser.
        """
        # add  Permission filter by publish date and status
        mt = get_permission_filter()
        q = _get_search_qs_query(qs)
        if q:
            mt.append(q)
        mt.extend(_get_detail_keywords_query())
        return Q('bool', must=mt) if mt else Q()

    def _get_simple_search_community_query(community_id,qs=None):
        """
          query parser for simple search
        :param qs: Query string.
        :return: Query parser.
        """
        # add  Permission filter by publish date and status
        comm = Community.get(community_id)
        root_node_id = comm.root_node_id

        mt = get_permission_filter(root_node_id)
        q = _get_search_qs_query(qs)

        if q:
            mt.append(q)
        mt.extend(_get_detail_keywords_query())
        return Q('bool', must=mt) if mt else Q()

    def _default_parser(qstr=None):
        """Default parser that uses the Q() from elasticsearch_dsl.
           Full text Search.
           Detail Search.
        :param qstr: Query string.
        :returns: Query parser.
        """
        # add  Permission filter by publish date and status
        mt = get_permission_filter()

        # multi keywords search filter
        kmt = _get_detail_keywords_query()
        # detail search
        if kmt:
            mt.extend(kmt)
            q = _get_search_qs_query(qs)
            if q:
                mt.append(q)
        else:
            # Full Text Search
            if qstr:
                q_s = Q('multi_match', query=qstr, operator='and',
                        fields=['content.file.content^1.5',
                                'content.file.content.ja^1.2',
                                '_all', 'search_string'],
                        type='most_fields', minimum_should_match='75%')
                mt.append(q_s)
        return Q('bool', must=mt) if mt else Q()

    def _default_parser_community(community_id, qstr=None):
        """Default parser that uses the Q() from elasticsearch_dsl.
           Full text Search.
           Detail Search.
        :param qstr: Query string.
        :returns: Query parser.
        """
        # add  Permission filter by publish date and status

        comm = Community.get(community_id)
        root_node_id = comm.root_node_id
        mt = get_permission_filter(root_node_id)

        # multi keywords search filter
        kmt = _get_detail_keywords_query()
        # detail search
        if kmt:
            mt.extend(kmt)
            q = _get_search_qs_query(qs)
            if q:
                mt.append(q)
        else:
            # Full Text Search
            if qstr:
                q_s = Q('multi_match', query=qstr, operator='and',
                        fields=['content.file.content^1.5',
                                'content.file.content.ja^1.2',
                                '_all', 'search_string'],
                        type='most_fields', minimum_should_match='75%')
                mt.append(q_s)
        return Q('bool', must=mt) if mt else Q()


    from invenio_records_rest.facets import default_facets_factory
    from invenio_records_rest.sorter import default_sorter_factory

    # add by ryuu at 1004 start curate
    comm_ide = request.values.get('provisional_communities')
    # simple search
    comm_id_simple = request.values.get('community')
    # add by ryuu at 1004 end
    if comm_id_simple is not None:
        query_parser = query_parser or _default_parser_community
    else:
        query_parser = query_parser or _default_parser

    if search_type is None:
        search_type = request.values.get('search_type')

    qs = request.values.get('q')

    # full text search
    if search_type and '0' in search_type:
        if comm_id_simple is not None:
            query_q = query_parser(comm_id_simple, qs)
        else:
            query_q = query_parser(qs)

    else:
        # simple search
        if comm_ide is not None:
            query_q = _get_simple_search_community_query(comm_ide, qs)
        elif comm_id_simple is not None:
            query_q = _get_simple_search_community_query(comm_id_simple, qs)
        else:
            query_q = _get_simple_search_query(qs)

    src = {'_source': {'excludes': ['content']}}
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


def item_path_search_factory(self, search, index_id=None):
    """Parse query using Weko-Query-Parser.

    :param self: REST view.
    :param search: Elastic search DSL search instance.
    :returns: Tuple with search instance and URL arguments.
    """

    def _get_index_earch_query():

        query_q = {
            "_source": {
                "excludes": ['content']
            },
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
                            "filter": {
                                "match": {"publish_status": "0"}
                            },
                            "aggs": {
                                "available": {
                                    "range": {
                                        "field": "publish_date",
                                        "ranges": [
                                            {
                                                "from": "now+1d/d"
                                            },
                                            {
                                                "to": "now+1d/d"
                                            }
                                        ]
                                    },
                                }
                            }
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
            "post_filter": {
                "term": {
                    "path": "@index"
                }
            }
        }

        # add item type aggs
        query_q['aggs']['path']['aggs']. \
            update(get_item_type_aggs(search._index[0]))

        mut = get_permission_filter()
        if mut:
            mut = list(map(lambda x: x.to_dict(), mut))
            post_filter = query_q['post_filter']
            if mut[0].get('bool'):
                post_filter['bool'] = {'must': [{'term': post_filter.pop('term')}, mut[0]['bool']['must'][0]],
                                       'should': mut[0]['bool']['should']}
                # post_filter['bool'] = {'must': [{'term': post_filter.pop('term')}],
                #                        'should': mut[0]['bool']['should']}
            else:
                mut.append({'term': post_filter.pop('term')})
                post_filter['bool'] = {'must': mut}

        # create search query
        q = request.values.get('q') if index_id is None else index_id
        if q:
            try:
                fp = Indexes.get_self_path(q)
                if fp:
                    query_q = json.dumps(query_q).replace("@index", fp.path)
                    query_q = json.loads(query_q)
            except BaseException:
                pass
        return query_q

    # create a index search query
    query_q = _get_index_earch_query()
    urlkwargs = MultiDict()
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

    from invenio_records_rest.sorter import default_sorter_factory
    search_index = search._index[0]

    search, sortkwargs = default_sorter_factory(search, search_index)

    for key, value in sortkwargs.items():
        # set custom sort option
        if value == 'custom_sort':
            ind_id = request.values.get('q', '')
            factor_obj = Indexes.get_item_sort(ind_id)
            script_str = {
                "_script": {
                    "script": "factor.get(doc[\"control_number\"].value)&&factor.get(doc[\"control_number\"].value) !=0 ? factor.get(doc[\"control_number\"].value):Integer.MAX_VALUE",
                    "type": "number",
                    "params": {
                        "factor": factor_obj
                    },
                    "order": "asc"
                }
            }
            default_sort = {'_score': {'order': 'desc'}}
            search._sort=[]
            search._sort.append(script_str)
            search._sort.append(default_sort)
        if value =="-custom_sort":
            ind_id = request.values.get('q', '')
            factor_obj = Indexes.get_item_sort(ind_id)
            script_str = {
                "_script": {
                    "script": "factor.get(doc[\"control_number\"].value)&&factor.get(doc[\"control_number\"].value) !=0 ? factor.get(doc[\"control_number\"].value):0",
                    "type": "number",
                    "params": {
                        "factor": factor_obj
                    },
                    "order": "desc"
                }
            }
            default_sort = {'_score': {'order': 'asc'}}
            search._sort = []
            search._sort.append(script_str)
            search._sort.append(default_sort)
        # set selectbox
        urlkwargs.add(key, value)

    urlkwargs.add('q', query_q)
    return search, urlkwargs


def check_admin_user():
    """
    Check administrator role user.
    :return: result
    """
    result = True
    user_id = current_user.get_id() \
        if current_user and current_user.is_authenticated else None
    if user_id:
        users = current_app.config['WEKO_PERMISSION_ROLE_USER']
        for lst in list(current_user.roles or []):
            # if is administrator
            if lst.name == users[2]:
                result = True
    return user_id, result

weko_search_factory = item_path_search_factory
es_search_factory = default_search_factory

def opensearch_factory(self, search, query_parser=None):
    """
    Factory for opensearch.
    :param self:
    :param search:
    :param query_parser:
    :return:
    """
    index_id = request.values.get('index_id')
    if index_id:
        return item_path_search_factory(self,
                                        search,
                                        index_id=index_id)
    else:
        return default_search_factory(self,
                                      search,
                                      query_parser,
                                      search_type='0')
