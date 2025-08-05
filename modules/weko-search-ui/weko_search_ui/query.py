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
import re
import sys
from datetime import datetime
from datetime import timezone
from functools import partial

from elasticsearch_dsl.query import Bool, Q
from flask import current_app, request
from flask_security import current_user
from flask_babelex import get_timezone
from invenio_communities.models import Community
from invenio_records_rest.errors import InvalidQueryRESTError
from weko_index_tree.api import Indexes
from weko_index_tree.utils import get_user_roles
from weko_schema_ui.models import PublishStatus
from werkzeug.datastructures import MultiDict

from . import config
from .api import SearchSetting
from .permissions import search_permission


def get_item_type_aggs(search_index):
    """Get item types aggregations.

    :return: aggs dict
    """
    from weko_admin.utils import get_facet_search_query

    facets = get_facet_search_query(search_permission.can())
    return facets.get(search_index).get("aggs", {})


def get_permission_filter(index_id: str = None, is_community=False):
    """Check permission.

    Args:
        index_id (str, optional): Index Identifier Number. Defaults to None.
        is_community (bool): Includes child indexes under the specified index. Defaults to False.

    Returns:
        List: Query command.

    """
    is_admin, roles = get_user_roles()
    if is_admin:
        pub_status = [PublishStatus.PUBLIC.value, PublishStatus.PRIVATE.value]
    else:
        pub_status = [PublishStatus.PUBLIC.value]
    is_perm = search_permission.can()
    status = Q("terms", publish_status=pub_status)
    version = Q("match", relation_version_is_last="true")

    rng = Q("range", **{"publish_date": {"lte": "now/d","time_zone":str(get_timezone())}})
    term_list = []
    mst = []
    is_perm_paths = Indexes.get_browsing_tree_paths()
    is_perm_indexes = [item.split("/")[-1] for item in is_perm_paths]
    search_type = request.values.get("search_type")

    if index_id:
        index_id = str(index_id)
        if search_type == config.WEKO_SEARCH_TYPE_DICT["FULL_TEXT"]:
            should_path = []
            if index_id in is_perm_indexes:
                if is_community:
                    child_ids = Indexes.get_child_list_recursive(int(index_id))
                    term_list.extend([i for i in child_ids if i in is_perm_indexes])
                else:
                    term_list.append(index_id)
                should_path.append(Q("terms", path=term_list))

            terms = Q("bool", should=should_path)
        else:  # In case search_type is keyword or index
            if index_id in is_perm_indexes:
                if is_community:
                    child_ids = Indexes.get_child_list_recursive(int(index_id))
                    term_list.extend([i for i in child_ids if i in is_perm_indexes])
                else:
                    term_list.append(index_id)

            terms = Q("terms", path=term_list)
    else:
        terms = Q("terms", path=is_perm_indexes)

    if is_admin:
        mst.append(status)
    else:
        mst.append(status)
        mst.append(rng)

    mut = []

    if is_perm:
        user_id, result = check_permission_user()

        if result:
            user_terms = Q("terms", publish_status=[
                PublishStatus.PUBLIC.value, PublishStatus.PRIVATE.value])
            creator_user_match = Q("match", weko_creator_id=user_id)
            shared_user_match = Q("terms", weko_shared_ids=[user_id])
            shuld = []
            shuld.append(Q("bool", must=[user_terms, creator_user_match]))
            shuld.append(Q("bool", must=[user_terms, shared_user_match]))
            shuld.append(Q("bool", must=mst))
            mut.append(Q("bool", should=shuld, must=[terms]))
            mut.append(Q("bool", must=version))
    else:
        mut = mst
        mut.append(terms)
        base_mut = [status, version]
        mut.append(Q("bool", must=base_mut))

    return mut, is_perm_paths


def default_search_factory(self, search, query_parser=None, search_type=None, additional_params=None):
    """Parse query using Weko-Query-Parser. MetaData Search.

    :param self: REST view.
    :param search: Elastic search DSL search instance.
    :param query_parser: Query parser. (Default: ``None``)
    :param search_type: Search type. (Default: ``None``)
    :returns: Tuple with search instance and URL arguments.
    """

    def _get_search_qs_query(qs=None):
        """Qs of search bar keywords for detail simple search.

        :param qs: Query string.
        :return: Query parser.
        """
        qs = qs.replace("　", " ").replace(" | ", " OR ")
        q = (
            Q(
                "query_string",
                query=qs,
                default_operator="and",
                fields=["search_*", "search_*.ja"],
            )
            if qs
            else None
        )

        return q

    def _get_detail_keywords_query():
        """Get keywords query.

        :return: Query parser.
        """

        def _get_keywords_query(k, v):
            qry = None
            kv = (
                params.get("lang") if k == "language" else params.get(k)
            )

            if not kv:
                return

            if isinstance(v, str):
                split_text_list = _split_text_by_or(kv)

                if len(split_text_list) == 1:
                    name_dict = dict(operator="and")
                    name_dict.update(dict(query=kv))
                    qry = Q("match", **{v: name_dict})
                else:
                    # OR search
                    should_list = []
                    for split_text in split_text_list:
                        name_dict = dict(operator="and")
                        name_dict.update(dict(query=split_text))
                        should_list.append(Q("match", **{v: name_dict}))
                    qry = Q("bool", should=should_list, minimum_should_match=1)

            elif isinstance(v, list):
                if k == "title" and params.get("exact_title_match"):
                    should_list = []
                    should_list.append(Q("term", **{"title":kv}))
                    should_list.append(Q("term", **{"alternative":kv}))
                    qry = Q("bool", should=should_list, minimum_should_match=1)
                else:
                    split_text_list = _split_text_by_or(kv)
                    if len(split_text_list) == 1:
                        qry = Q(
                            "multi_match",
                            query=kv,
                            type="most_fields",
                            minimum_should_match="75%",
                            operator="and",
                            fields=v,
                        )
                    else:
                        # OR search
                        should_list = []
                        for split_text in split_text_list:
                            should_list.append(Q(
                                "multi_match",
                                query=split_text,
                                type="most_fields",
                                minimum_should_match="75%",
                                operator="and",
                                fields=v,
                        ))
                        qry = Q("bool", should=should_list, minimum_should_match=1)

            elif isinstance(v, dict):

                for key, vlst in v.items():

                    if isinstance(vlst, list):
                        shud = []
                        kvl = [
                            x
                            for x in kv.split(",")
                            if x.isdecimal() and int(x) < len(vlst) + 1
                        ]

                        for j in map(partial(lambda x, y: x[int(y)], vlst), kvl):
                            name_dict = dict(operator="and")
                            name_dict.update(dict(query=j))
                            shud.append(Q("match", **{key: name_dict}))

                        kvl = [
                            x for x in kv.split(",") if not x.isdecimal() and x in vlst
                        ]

                        for j in kvl:

                            if j == "other" and k=="language":
                                source = "boolean flg=false; for(lang in doc['language']){if (!params.param1.contains(lang)){flg=true;}} return flg;"
                                params = {"param1":vlst}
                                script = Q("script",script={"source":source,"params":params})
                                shud.append(Q("bool",filter=script))
                            else:
                                name_dict = dict(operator="and")
                                name_dict.update(dict(query=j))
                                shud.append(Q("match", **{key: name_dict}))

                        if shud:
                            return Q("bool", should=shud)

            elif isinstance(v, tuple) and len(v) >= 2:
                shud = []

                for i in map(lambda x: v[1](x), kv.split(",")):
                    shud.append(Q("match", **{v[0]: i}))

                if shud:
                    qry = Q("bool", should=shud)

            return qry

        def _get_object_query(k, v):
            # text value
            kv = params.get(k)
            if not kv:
                return
            if isinstance(v, tuple) and len(v) > 1 and isinstance(v[1], dict):
                # attr keyword in request url
                attrs = map(lambda x: (x, params.get(x)), list(v[1].keys()))
                for attr_key, attr_val_str in attrs:
                    attr_obj = v[1].get(attr_key)
                    if isinstance(attr_obj, dict) and attr_val_str:
                        if isinstance(v[0], str) and len(v[0]):
                            attr_key_hit = [
                                x for x in attr_obj.keys() if v[0] + "." in x
                            ]
                            if attr_key_hit:
                                vlst = attr_obj.get(attr_key_hit[0])
                                if isinstance(vlst, list):
                                    attr_val = [
                                        int(x)
                                        for x in attr_val_str.split(",")
                                        if x.isdecimal() and int(x) < len(vlst)
                                    ]
                                    if attr_val:
                                        name = v[0] + ".value"
                                        schemas = [vlst[i] for i in attr_val]
                                        return Bool(
                                            must=[
                                                {"term": {name: kv}},
                                                {"terms": {attr_key_hit[0]: schemas}},
                                            ]
                                        )
            return None

        def _get_nested_query(k, v):
            # text value
            kv = params.get(k)

            if not kv:
                return

            shuld = []

            if isinstance(v, tuple) and len(v) > 1 and isinstance(v[1], dict):
                # attr keyword in request url
                for attr_key, attr_val_str in map(
                    lambda x: (x, params.get(x)), list(v[1].keys())
                ):
                    attr_obj = v[1].get(attr_key)

                    if isinstance(attr_obj, dict) and attr_val_str:

                        if isinstance(v[0], str) and not len(v[0]):

                            # For ID search
                            for key in attr_val_str.split(","):
                                attr = attr_obj.get(key)

                                if isinstance(attr, tuple):
                                    attr = [attr]

                                if isinstance(attr, list):
                                    for alst in attr:
                                        if isinstance(alst, tuple):
                                            val_attr_lst = alst[1].split("=")
                                            qt = None

                                            # attribute conditon
                                            field_name = alst[0] + "." + val_attr_lst[0]
                                            if "=*" in alst[1]:
                                                name = alst[0] + "." + val_attr_lst[0]
                                                qt = [
                                                    Q("term", **{name: key})
                                                ]

                                            split_text_list = _split_text_by_or(kv)
                                            if len(split_text_list) == 1:
                                                name = alst[0] + ".value"
                                                name_dict = dict(operator="and")
                                                name_dict.update(dict(query=kv))
                                                mut = [Q("match", **{name: name_dict})]

                                                mut.extend(qt or [])
                                                qry = Q("bool", must=mut)

                                            else:
                                                # OR search
                                                should_list = []
                                                for split_text in split_text_list:
                                                    name = alst[0] + ".value"
                                                    name_dict = dict(operator="and")
                                                    name_dict.update(dict(query=split_text))
                                                    should_list.append(Q("match", **{name: name_dict}))
                                                mut = []
                                                mut.extend(qt or [])
                                                qry = Q("bool", must=mut, should=should_list, minimum_should_match=1)
                                            shuld.append(
                                                Q("nested", path=alst[0], query=qry)
                                            )
                        else:
                            attr_key_hit = [
                                x for x in attr_obj.keys() if v[0] + "." in x
                            ]

                            if attr_key_hit:
                                vlst = attr_obj.get(attr_key_hit[0])

                                if isinstance(vlst, list):
                                    attr_val = [
                                        x
                                        for x in attr_val_str.split(",")
                                        if x.isdecimal() and int(x) < len(vlst)
                                    ]

                                    if attr_val:
                                        mst = []
                                        name = v[0] + ".value"
                                        qry = Q(
                                            "multi_match",
                                            query=kv,
                                            type="most_fields",
                                            minimum_should_match="75%",
                                            operator="and",
                                            fields=[name],
                                        )
                                        mst.append(qry)
                                        name = attr_key_hit[0]
                                        name_val = list(
                                            map(
                                                partial(lambda m, n: m[int(n)], vlst),
                                                attr_val,
                                            )
                                        )
                                        qm = Q("terms", **{name: name_val})
                                        mst.append(qm)
                                        shuld.append(
                                            Q(
                                                "nested",
                                                path=v[0],
                                                query=Q("bool", must=mst),
                                            )
                                        )
                    elif isinstance(attr_obj, str) and attr_val_str:
                        query = Q(
                            "bool",
                            must=[{"terms": {attr_obj: attr_val_str.split(",")}}],
                        )
                        shuld.append(Q("nested", path=v[0], query=query))

            return Q("bool", should=shuld) if shuld else None

        def _get_date_query(k, v):
            """[summary]

            Args:
                k ([string]): 'date_range1'
                v ([type]): [('from', 'to'), 'date_range1']

            Returns:
                [type]: query
            """

            # text value
            qry = None

            if isinstance(v, list) and len(v) >= 2:
                date_from = params.get(k + "_" + v[0][0])
                date_to = params.get(k + "_" + v[0][1])

                if not date_from or not date_to:
                    return

                pattern = r"^(\d{4}-\d{2}-\d{2})|(\d{4}-\d{2})|(\d{4})|(\d{6})|(\d{8})$"
                p = re.compile(pattern)
                if p.match(date_from) and p.match(date_to):
                    if len(date_from) == 8:
                        date_from = datetime.strptime(date_from, "%Y%m%d").strftime(
                            "%Y-%m-%d"
                        )
                    if len(date_to) == 8:
                        date_to = datetime.strptime(date_to, "%Y%m%d").strftime(
                            "%Y-%m-%d"
                        )
                    if len(date_from) == 6:
                        date_from = datetime.strptime(date_from, "%Y%m").strftime(
                            "%Y-%m"
                        )
                    if len(date_to) == 6:
                        date_to = datetime.strptime(date_to, "%Y%m").strftime("%Y-%m")
                else:
                    return

                qv = {}
                qv.update(dict(gte=date_from))
                qv.update(dict(lte=date_to))

                if isinstance(v[1], str):
                    qry = Q("range", **{v[1]: qv})
                elif isinstance(v[1], tuple) and len(v[1]) >= 2:
                    path = v[1][0]
                    dt = v[1][1]

                    if isinstance(dt, dict):

                        for attr_key, attr_val_str in map(
                            lambda x: (x, params.get(x)), list(dt.keys())
                        ):
                            attr_obj = dt.get(attr_key)

                            if isinstance(attr_obj, dict) and attr_val_str:
                                attr_key_hit = [
                                    x for x in attr_obj.keys() if path + "." in x
                                ]

                                if attr_key_hit:
                                    vlst = attr_obj.get(attr_key_hit[0])

                                    if isinstance(vlst, list):
                                        attr_val = [x for x in attr_val_str.split(",")]
                                        shud = []
                                        for j in attr_val:
                                            qt = Q("term", **{attr_key_hit[0]: j})
                                            shud.append(qt)

                                        qry = Q("range", **{path + ".value": qv})
                                        qry = Q(
                                            "nested",
                                            path=path,
                                            query=Q("bool", should=shud, must=[qry]),
                                        )
            current_app.logger.debug(qry)
            return qry

        def _get_text_query(k, v):
            qry = None
            kv = (
                params.get("lang") if k == "language" else params.get(k)
            )

            if not kv:
                return

            if isinstance(v, str):
                split_text_list = _split_text_by_or(kv)
                if len(split_text_list) == 1:
                    name_dict = dict(operator="and")
                    name_dict.update(dict(query=kv))
                    qry = Q("match", **{v: name_dict})

                else:
                    # OR search
                    should_list = []
                    for split_text in split_text_list:
                        name_dict = dict(operator="and")
                        name_dict.update(dict(query=split_text))
                        should_list.append(Q("match", **{v: name_dict}))
                    qry = Q("bool", should=should_list, minimum_should_match=1)
            return qry

        def _get_range_query(k, v):
            qry = None

            if isinstance(v, list) and len(v) >= 2:
                value_from = params.get(k + "_" + v[0][0])
                value_to = params.get(k + "_" + v[0][1])

                if not value_from or not value_to:
                    return

                qv = {}
                qv.update(dict(gte=value_from))
                qv.update(dict(lte=value_to))

                if isinstance(v[1], str):
                    qry = Q("range", **{v[1]: qv})
            return qry

        def _get_geo_distance_query(k, v):

            qry = None

            if isinstance(v, list) and len(v) >= 2:
                value_lat = params.get(k + "_" + v[0][0])
                value_lon = params.get(k + "_" + v[0][1])
                value_distance = params.get(k + "_" + v[0][2])

                if not value_lat or not value_lon or not value_distance:
                    return

                qv = {}
                qv.update(dict(lat=value_lat))
                qv.update(dict(lon=value_lon))

                if isinstance(v[1], str):
                    qry = {"geo_distance": {"distance": value_distance, v[1]: qv}}

            return qry

        def _get_geo_shape_query(k, v):
            qry = None

            if isinstance(v, list) and len(v) >= 2:
                value_lat = params.get(k + "_" + v[0][0])
                value_lon = params.get(k + "_" + v[0][1])
                value_distance = params.get(k + "_" + v[0][2])

                if not value_lat or not value_lon or not value_distance:
                    return

                qv = []
                qv.append(value_lon)
                qv.append(value_lat)

                if isinstance(v[1], str):
                    qry = {
                        "geo_shape": {
                            v[1]: {
                                "shape": {
                                    "type": "circle",
                                    "coordinates": qv,
                                    "radius": value_distance,
                                }
                            }
                        }
                    }

            return qry

        params = request.values.to_dict()
        if additional_params:
            params.update(additional_params)
        kwd = current_app.config["WEKO_SEARCH_KEYWORDS_DICT"]
        ks = kwd.get("string")
        kd = kwd.get("date")
        kn = kwd.get("nested")
        ko = kwd.get("object")
        kr = kwd.get("range")
        kt = kwd.get("text")
        kgd = kwd.get("geo_distance")
        kgs = kwd.get("geo_shape")

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

            for k, v in ko.items():
                qy = _get_object_query(k, v)

                if qy:
                    mut.append(qy)
            for k, v in kt.items():
                qy = _get_text_query(k, v)

                if qy:
                    mut.append(qy)
            for k, v in kr.items():
                qy = _get_range_query(k, v)

                if qy:
                    mut.append(qy)

            for k, v in kgd.items():
                qy = _get_geo_distance_query(k, v)

                if qy:
                    mut.append(qy)

            for k, v in kgs.items():
                qy = _get_geo_shape_query(k, v)

                if qy:
                    mut.append(qy)

        except Exception as e:
            current_app.logger.exception(
                "Detail search query parser failed. err:{0}".format(e)
            )

        current_app.logger.debug(mut)
        return mut

    def _get_simple_search_query(qs=None):
        """Query parser for simple search.

        :param qs: Query string.
        :return: Query parser.
        """
        # add Permission filter by publish date and status
        mst, _ = get_permission_filter()

        q = _get_search_qs_query(qs)

        if q:
            mst.append(q)

        mst.extend(_get_detail_keywords_query())

        return Q("bool", must=mst) if mst else Q()

    def _get_simple_search_community_query(community_id, qs=None):
        """Query parser for simple search.

        :param qs: Query string.
        :return: Query parser.
        """
        # add  Permission filter by publish date and status
        comm = Community.get(community_id)
        root_node_id = comm.root_node_id

        mst, _ = get_permission_filter(root_node_id, is_community=True)
        q = _get_search_qs_query(qs)

        if q:
            mst.append(q)

        mst.extend(_get_detail_keywords_query())
        return Q("bool", must=mst) if mst else Q()

    def _get_file_content_query(qstr):
        """Query for searching indexed file contents."""
        split_text_list = _split_text_by_or(qstr)
        if len(split_text_list) == 1:
            multi_cont_q = Q(
                "multi_match",
                query=qstr,
                operator="and",
                fields=["content.attachment.content"],
            )
        else:
            # OR search
            should_list = []
            for split_text in split_text_list:
                should_list.append(Q(
                    "multi_match",
                    query=split_text,
                    operator="and",
                    fields=["content.attachment.content"],
                ))
            multi_cont_q = Q("bool", should=should_list, minimum_should_match=1)

        # Search fields may increase so leaving as multi
        qstr = qstr.replace("　", " ").replace(" | ", " OR ")
        multi_q = Q(
            "query_string",
            query=qstr,
            default_operator="and",
            fields=["search_*", "search_*.ja"],
        )

        nested_content = Q("nested", query=multi_cont_q, path="content")
        return Q("bool", should=[nested_content, multi_q])

    def _default_parser(qstr=None):
        """Default parser that uses the Q() from elasticsearch_dsl.

           Full text Search.
           Detail Search.

        :param qstr: Query string.
        :returns: Query parser.
        """
        # add  Permission filter by publish date and status
        mst, _ = get_permission_filter()

        # multi keywords search filter
        mkq = _get_detail_keywords_query()

        if mkq:
            # details search
            mst.extend(mkq)

        if qstr:
            q_s = _get_file_content_query(qstr)
            mst.append(q_s)

        return Q("bool", must=mst) if mst else Q()

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
        mst, _ = get_permission_filter(root_node_id, is_community=True)

        # multi keywords search filter
        mkq = _get_detail_keywords_query()

        if mkq:
            # details search
            mst.extend(mkq)

        if qstr:
            q_s = _get_file_content_query(qstr)
            mst.append(q_s)

        return Q("bool", must=mst) if mst else Q()

    from invenio_records_rest.facets import default_facets_factory
    from invenio_records_rest.sorter import default_sorter_factory

    # add by ryuu at 1004 start curate
    comm_ide = request.values.get("provisional_communities")

    # simple search
    comm_id_simple = request.values.get("community")

    # add by ryuu at 1004 end
    if comm_id_simple:
        query_parser = query_parser or _default_parser_community
    else:
        query_parser = query_parser or _default_parser

    if search_type is None:
        search_type = request.values.get("search_type")

    if request.values.get("format"):
        qs = request.values.get("keyword")
    else:
        # Escape special characters for avoiding ES search errors
        qs = (
            request.values.get("q", "")
            .replace("\\", r"\\")
            .replace("+", r"\+")
            .replace("-", r"\-")
            .replace("=", r"\=")
            .replace("&&", r"\&&")
            .replace("||", r"\||")
            .replace("!", r"\!")
            .replace("(", r"\(")
            .replace(")", r"\)")
            .replace("{", r"\{")
            .replace("}", r"\}")
            .replace("[", r"\[")
            .replace("]", r"\]")
            .replace("^", r"\^")
            .replace('"', r"\"")
            .replace("~", r"\~")
            .replace("*", r"\*")
            .replace("?", r"\?")
            .replace(":", r"\:")
            .replace("/", r"\/")
        )

    # full text search
    if search_type == config.WEKO_SEARCH_TYPE_DICT["FULL_TEXT"]:
        if comm_id_simple:
            query_q = query_parser(comm_id_simple, qs)
        else:
            query_q = query_parser(qs)
    else:
        # simple search
        if comm_ide:
            query_q = _get_simple_search_community_query(comm_ide, qs)
        elif comm_id_simple:
            query_q = _get_simple_search_community_query(comm_id_simple, qs)
        else:
            query_q = _get_simple_search_query(qs)

    src = {"_source": {"excludes": ["content"]}}
    search._extra.update(src)

    try:
        search = search.filter(query_q)
    except SyntaxError:
        current_app.logger.debug(
            "Failed parsing query: {0}".format(request.values.get("q", "")),
            exc_info=True,
        )
        raise InvalidQueryRESTError()

    search_index = search._index[0]
    search, urlkwargs = default_facets_factory(search, search_index)
    search, sortkwargs = default_sorter_factory(search, search_index)

    for key, value in sortkwargs.items():
        urlkwargs.add(key, value)

        current_app.logger.debug("key: {}".format(key))
        current_app.logger.debug("value: {}".format(value))
        current_app.logger.debug("sortkwargs: {}".format(sortkwargs))

        # defalult sort
        if not sortkwargs:
            sort_key, sort = SearchSetting.get_default_sort(
                current_app.config["WEKO_SEARCH_TYPE_KEYWORD"]
            )
            key_fileds = SearchSetting.get_sort_key(sort_key)
            current_app.logger.debug("sort_key: {}".format(sort_key))
            current_app.logger.debug("sort: {}".format(sort))
            current_app.logger.debug("key_fileds: {}".format(key_fileds))

            if key_fileds:
                sort_obj = dict()
                nested_sorting = SearchSetting.get_nested_sorting(sort_key)

                if sort == "desc":
                    sort_obj[key_fileds] = dict(order="desc", unmapped_type="long")
                    sort_key = "-" + sort_key
                else:
                    sort_obj[key_fileds] = dict(order="asc", unmapped_type="long")

                if nested_sorting:
                    sort_obj[key_fileds].update({"nested": nested_sorting})

                search._sort.append(sort_obj)

            urlkwargs.add("sort", sort_key)

    urlkwargs.add("q", query_q)
    # debug elastic search query
    current_app.logger.debug("query: {}".format(json.dumps((search.query()).to_dict())))
    # {"query": {"bool": {"filter": [{"bool": {"must": [{"match": {"publish_status": "0"}}, {"range": {"publish_date": {"lte": "now/d"}}}, {"terms": {"path": ["1031", "1029", "1025", "952", "953", "943", "940", "1017", "1015", "1011", "881", "893", "872", "869", "758", "753", "742", "530", "533", "502", "494", "710", "702", "691", "315", "351", "288", "281", "759", "754", "744", "531", "534", "503", "495", "711", "704", "692", "316", "352", "289", "282", "773", "771", "767", "538", "539", "519", "510", "756", "745", "733", "337", "377", "308", "299", "2063", "2061", "2057", "1984", "1985", "1975", "1972", "2049", "2047", "2043", "1913", "1925", "1904", "1901", "1790", "1785", "1774", "1562", "1565", "1534", "1526", "1742", "1734", "1723", "1347", "1383", "1320", "1313", "1791", "1786", "1776", "1563", "1566", "1535", "1527", "1743", "1736", "1724", "1348", "1384", "1321", "1314", "1805", "1803", "1799", "1570", "1571", "1551", "1542", "1788", "1777", "1765", "1369", "1409", "1340", "1331", "4127", "4125", "4121", "4048", "4049", "4039", "4036", "4113", "4111", "4107", "3977", "3989", "3968", "3965", "3854", "3849", "3838", "3626", "3629", "3598", "3590", "3806", "3798", "3787", "3411", "3447", "3384", "3377", "3855", "3850", "3840", "3627", "3630", "3599", "3591", "3807", "3800", "3788", "3412", "3448", "3385", "3378", "3869", "3867", "3863", "3634", "3635", "3615", "3606", "3852", "3841", "3829", "3433", "3473", "3404", "3395"]}}, {"bool": {"must": [{"match": {"publish_status": "0"}}, {"match": {"relation_version_is_last": "true"}}]}}]}}], "must": [{"match_all": {}}]}}, "aggs": {"Data Language": {"filter": {"bool": {"must": [{"term": {"publish_status": "0"}}]}}, "aggs": {"Data Language": {"terms": {"field": "language", "size": 1000}}}}, "Access": {"filter": {"bool": {"must": [{"term": {"publish_status": "0"}}]}}, "aggs": {"Access": {"terms": {"field": "accessRights", "size": 1000}}}}, "Location": {"filter": {"bool": {"must": [{"term": {"publish_status": "0"}}]}}, "aggs": {"Location": {"terms": {"field": "geoLocation.geoLocationPlace", "size": 1000}}}}, "Temporal": {"filter": {"bool": {"must": [{"term": {"publish_status": "0"}}]}}, "aggs": {"Temporal": {"terms": {"field": "temporal", "size": 1000}}}}, "Topic": {"filter": {"bool": {"must": [{"term": {"publish_status": "0"}}]}}, "aggs": {"Topic": {"terms": {"field": "subject.value", "size": 1000}}}}, "Distributor": {"filter": {"bool": {"must": [{"term": {"contributor.@attributes.contributorType": "Distributor"}}, {"term": {"publish_status": "0"}}]}}, "aggs": {"Distributor": {"terms": {"field": "contributor.contributorName", "size": 1000}}}}, "Data Type": {"filter": {"bool": {"must": [{"term": {"description.descriptionType": "Other"}}, {"term": {"publish_status": "0"}}]}}, "aggs": {"Data Type": {"terms": {"field": "description.value", "size": 1000}}}}}, "from": 0, "size": 20, "_source": {"excludes": ["content"]}}
    # {"query": {"bool": {"filter": [{"bool": {"must": [{"match": {"publish_status": "0"}}, {"range": {"publish_date": {"lte": "now/d"}}}, {"terms": {"path": ["1031", "1029", "1025", "952", "953", "943", "940", "1017", "1015", "1011", "881", "893", "872", "869", "758", "753", "742", "530", "533", "502", "494", "710", "702", "691", "315", "351", "288", "281", "759", "754", "744", "531", "534", "503", "495", "711", "704", "692", "316", "352", "289", "282", "773", "771", "767", "538", "539", "519", "510", "756", "745", "733", "337", "377", "308", "299", "2063", "2061", "2057", "1984", "1985", "1975", "1972", "2049", "2047", "2043", "1913", "1925", "1904", "1901", "1790", "1785", "1774", "1562", "1565", "1534", "1526", "1742", "1734", "1723", "1347", "1383", "1320", "1313", "1791", "1786", "1776", "1563", "1566", "1535", "1527", "1743", "1736", "1724", "1348", "1384", "1321", "1314", "1805", "1803", "1799", "1570", "1571", "1551", "1542", "1788", "1777", "1765", "1369", "1409", "1340", "1331", "4127", "4125", "4121", "4048", "4049", "4039", "4036", "4113", "4111", "4107", "3977", "3989", "3968", "3965", "3854", "3849", "3838", "3626", "3629", "3598", "3590", "3806", "3798", "3787", "3411", "3447", "3384", "3377", "3855", "3850", "3840", "3627", "3630", "3599", "3591", "3807", "3800", "3788", "3412", "3448", "3385", "3378", "3869", "3867", "3863", "3634", "3635", "3615", "3606", "3852", "3841", "3829", "3433", "3473", "3404", "3395"]}}, {"bool": {"must": [{"match": {"publish_status": "0"}}, {"match": {"relation_version_is_last": "true"}}]}}]}}], "must": [{"match_all": {}}]}}, "aggs": {"Data Language": {"filter": {"bool": {"must": [{"term": {"publish_status": "0"}}]}}, "aggs": {"Data Language": {"terms": {"field": "language", "size": 1000}}}}, "Access": {"filter": {"bool": {"must": [{"term": {"publish_status": "0"}}]}}, "aggs": {"Access": {"terms": {"field": "accessRights", "size": 1000}}}}, "Location": {"filter": {"bool": {"must": [{"term": {"publish_status": "0"}}]}}, "aggs": {"Location": {"terms": {"field": "geoLocation.geoLocationPlace", "size": 1000}}}}, "Temporal": {"filter": {"bool": {"must": [{"term": {"publish_status": "0"}}]}}, "aggs": {"Temporal": {"terms": {"field": "temporal", "size": 1000}}}}, "Topic": {"filter": {"bool": {"must": [{"term": {"publish_status": "0"}}]}}, "aggs": {"Topic": {"terms": {"field": "subject.value", "size": 1000}}}}, "Distributor": {"filter": {"bool": {"must": [{"term": {"contributor.@attributes.contributorType": "Distributor"}}, {"term": {"publish_status": "0"}}]}}, "aggs": {"Distributor": {"terms": {"field": "contributor.contributorName", "size": 1000}}}}, "Data Type": {"filter": {"bool": {"must": [{"term": {"description.descriptionType": "Other"}}, {"term": {"publish_status": "0"}}]}}, "aggs": {"Data Type": {"terms": {"field": "description.value", "size": 1000}}}}}, "sort": [{"date_range1.gte": {"order": "asc", "unmapped_type": "date"}}], "from": 0, "size": 20, "_source": {"excludes": ["content"]}}
    current_app.logger.debug("urlkwargs: {}".format(urlkwargs))
    # MultiDict([('sort', 'relevance'), ('q', Bool(must=[Match(publish_status='0'), Range(publish_date={'lte': 'now/d'}), Terms(path=['1031', '1029', '1025', '952', '953', '943', '940', '1017', '1015', '1011', '881', '893', '872', '869', '758', '753', '742', '530', '533', '502', '494', '710', '702', '691', '315', '351', '288', '281', '759', '754', '744', '531', '534', '503', '495', '711', '704', '692', '316', '352', '289', '282', '773', '771', '767', '538', '539', '519', '510', '756', '745', '733', '337', '377', '308', '299', '2063', '2061', '2057', '1984', '1985', '1975', '1972', '2049', '2047', '2043', '1913', '1925', '1904', '1901', '1790', '1785', '1774', '1562', '1565', '1534', '1526', '1742', '1734', '1723', '1347', '1383', '1320', '1313', '1791', '1786', '1776', '1563', '1566', '1535', '1527', '1743', '1736', '1724', '1348', '1384', '1321', '1314', '1805', '1803', '1799', '1570', '1571', '1551', '1542', '1788', '1777', '1765', '1369', '1409', '1340', '1331', '4127', '4125', '4121', '4048', '4049', '4039', '4036', '4113', '4111', '4107', '3977', '3989', '3968', '3965', '3854', '3849', '3838', '3626', '3629', '3598', '3590', '3806', '3798', '3787', '3411', '3447', '3384', '3377', '3855', '3850', '3840', '3627', '3630', '3599', '3591', '3807', '3800', '3788', '3412', '3448', '3385', '3378', '3869', '3867', '3863', '3634', '3635', '3615', '3606', '3852', '3841', '3829', '3433', '3473', '3404', '3395']), Bool(must=[Match(publish_status='0'), Match(relation_version_is_last='true')])]))])

    return search, urlkwargs


def item_path_search_factory(self, search, index_id=None):
    """Parse query using Weko-Query-Parser.

    :param self: REST view.
    :param search: Elastic search DSL search instance.
    :param index_id: Index Identifier contains item's path
    :returns: Tuple with search instance and URL arguments.
    """

    def _get_index_earch_query():
        """Prepare search query.

        Returns:
            [dict]: Search query.

        """
        query_q = {
            "_source": {"excludes": ["content"]},
            "query": {
                "bool": {"must": [{"match": {"relation_version_is_last": "true"}}]}
            },
            "aggs": {},
            "post_filter":{}
        }

        aggs_template = {
            "terms": {
                "field": "path",
                "include": "@idxchild",
                "size": "@count",
            },
            "aggs": {
                "date_range": {
                    "filter": {"match": {"publish_status": PublishStatus.PUBLIC.value}},
                    "aggs": {
                        "available": {
                            "range": {
                                "field": "publish_date",
                                "ranges": [
                                    {"from": "now+1d/d"},
                                    {"to": "now+1d/d"},
                                ],
                            },
                        }
                    },
                },
                "no_available": {
                    "filter": {
                        "bool": {
                            "must_not": [{"match": {"publish_status": PublishStatus.PUBLIC.value}}]
                        }
                    }
                },
            },
        }

        q = request.values.get("q") or "0" if index_id is None else index_id
        activity_id = request.values.get("item_link")

        pid_value = None
        if activity_id:
            from weko_workflow.api import WorkActivity
            from invenio_pidstore.models import PersistentIdentifier
            from weko_deposit.pidstore import get_record_without_version

            activity = WorkActivity().get_activity_detail(activity_id)
            current_pid = PersistentIdentifier.get_by_object(
                pid_type='recid',
                object_type='rec',
                object_uuid=activity.item_id)
            pid_without_ver = get_record_without_version(current_pid)
            pid_value = pid_without_ver.pid_value
            query_q["query"]["bool"]["must_not"] = [{"match": {"control_number": pid_value}}]

        if q != "0":
            # add item type aggs
            aggs_template["aggs"].update(get_item_type_aggs(search._index[0]))

            if q:
                mut, is_perm_paths = get_permission_filter(q)
            else:
                mut, is_perm_paths = get_permission_filter()

            if mut:
                mut = list(map(lambda x: x.to_dict(), mut))
                post_filter = query_q["post_filter"]

                if mut[0].get("bool"):
                    mst = mut[0]["bool"]["must"]
                    mst.append({"bool": {"should":  mut[0]["bool"]["should"]}})
                    post_filter["bool"] = {"must": mst}
                else:
                    post_filter["bool"] = {"must": mut}

            # create search query
            if q:
                try:
                    child_idx = Indexes.get_child_list_recursive(q)
                    max_clause_count = current_app.config.get(
                        "OAISERVER_ES_MAX_CLAUSE_COUNT", 1024
                    )

                    if len(child_idx) > max_clause_count:
                        div_indexes = []
                        for div in range(0, int(len(child_idx) / max_clause_count) + 1):
                            _right = div * max_clause_count
                            _left = (
                                (div + 1) * max_clause_count
                                if len(child_idx) > (div + 1) * max_clause_count
                                else len(child_idx)
                            )
                            div_indexes.append(
                                {"terms": {"path": child_idx[_right:_left]}}
                            )

                        query_q["query"]["bool"]["must"].append(
                            {"bool": {"should": div_indexes},
                                "bool": {"must": [{"terms": {"publish_status": [
                                    PublishStatus.PUBLIC.value, PublishStatus.PRIVATE.value]}}]}}
                        )
                    else:
                        query_q["query"]["bool"]["must"].append({
                            "bool": {
                                "must": [
                                    {"terms": {"publish_status": [
                                        PublishStatus.PUBLIC.value, PublishStatus.PRIVATE.value]}},
                                    {"terms": {"path": child_idx}}
                                ]
                            }
                        })
                    delta = 1000
                    if len(child_idx)<=delta:
                        aggs = json.dumps(aggs_template).replace("@idxchild","|".join(child_idx))
                        query_q["aggs"]["path"] = json.loads(aggs)
                    else:
                        for i in range(len(child_idx)//delta+1):
                            to = i*delta+delta
                            if len(child_idx) < to:
                                to = len(child_idx)
                            child_list = child_idx[i*delta:to]
                            aggs = json.dumps(aggs_template).replace("@idxchild","|".join(child_list))
                            query_q["aggs"]["path_{}".format(i)] = json.loads(aggs)
                except BaseException as ex:
                    current_app.logger.error(ex)
                    import traceback

                    traceback.print_exc(file=sys.stdout)
            else:
                query_q["aggs"]["path"] = aggs_template
            count = str(Indexes.get_index_count())
            query_q = json.dumps(query_q).replace("@count", count)
            query_q = json.loads(query_q)

            return query_q, is_perm_paths
        else:
            # add item type aggs
            query_not_q = {
                "_source": {"excludes": ["content"]},
                "query": {
                    "bool": {"must": [{"match": {"relation_version_is_last": "true"}}]}
                },
                "aggs": {
                    "path": {
                        "terms": {"field": "path", "size": "@count"},
                        "aggs": {
                            "date_range": {
                                "filter": {"match": {"publish_status": PublishStatus.PUBLIC.value}},
                                "aggs": {
                                    "available": {
                                        "range": {
                                            "field": "publish_date",
                                            "ranges": [
                                                {"from": "now+1d/d"},
                                                {"to": "now+1d/d"},
                                            ],
                                        },
                                    }
                                },
                            },
                            "no_available": {
                                "filter": {
                                    "bool": {
                                        "must_not": [{"match": {"publish_status": PublishStatus.PUBLIC.value}}]
                                    }
                                }
                            },
                        },
                    }
                },
                "post_filter": {},
            }

            is_perm_paths = []
            if q:
                mut, is_perm_paths = get_permission_filter(q)
            else:
                mut, is_perm_paths = get_permission_filter()

            child_idx = [item.split("/")[-1] for item in is_perm_paths]
            child_idx = list(set(child_idx))
            max_clause_count = current_app.config.get(
                "OAISERVER_ES_MAX_CLAUSE_COUNT", 1024
            )

            if len(child_idx) > max_clause_count:
                div_indexes = []
                for div in range(0, int(len(child_idx) / max_clause_count) + 1):
                    _right = div * max_clause_count
                    _left = (
                        (div + 1) * max_clause_count
                        if len(child_idx) > (div + 1) * max_clause_count
                        else len(child_idx)
                    )
                    div_indexes.append({"terms": {"path": child_idx[_right:_left]}})
                query_not_q["query"]["bool"]["must"].append(
                    {"bool": {"should": div_indexes},
                     "bool": {"must": [{"terms": {"publish_status": [
                         PublishStatus.PUBLIC.value, PublishStatus.PRIVATE.value]}}]}}
                )
            else:
                query_not_q["query"]["bool"]["must"].append({
                    "bool": {
                        "must": [
                            {"terms": {"publish_status": [
                                PublishStatus.PUBLIC.value, PublishStatus.PRIVATE.value]}},
                            {"terms": {"path": child_idx}}
                        ]
                    }
                })

            query_not_q["aggs"]["path"]["aggs"].update(
                get_item_type_aggs(search._index[0])
            )

            if mut:
                mut = list(map(lambda x: x.to_dict(), mut))
                post_filter = query_not_q["post_filter"]

                if mut[0].get("bool"):
                    mst = mut[0]["bool"]["must"]
                    mst.append({"bool": {"should":  mut[0]["bool"]["should"]}})
                    post_filter["bool"] = {"must": mst}
                else:
                    post_filter["bool"] = {"must": mut}

            # create search query
            count = str(Indexes.get_index_count())
            query_not_q = json.dumps(query_not_q).replace("@count", count)
            query_not_q = json.loads(query_not_q)

            return query_not_q, is_perm_paths

    # create a index search query
    query_q, is_perm_paths = _get_index_earch_query()
    urlkwargs = MultiDict()

    try:
        # Aggregations.
        extr = search._extra.copy()
        search.update_from_dict(query_q)
        search._extra.update(extr)
    except SyntaxError:
        q = request.values.get("q", "") if index_id is None else index_id
        current_app.logger.debug("Failed parsing query: {0}".format(q), exc_info=True)
        raise InvalidQueryRESTError()

    from invenio_records_rest.sorter import default_sorter_factory

    search_index = search._index[0]
    search, sortkwargs = default_sorter_factory(search, search_index)

    for key, value in sortkwargs.items():
        # set custom sort option
        if "custom_sort" in value:
            ind_id = request.values.get("q", "")
            search._sort = []

            if value == "custom_sort":
                script_str, default_sort = SearchSetting.get_custom_sort(ind_id, "asc")
            else:
                script_str, default_sort = SearchSetting.get_custom_sort(ind_id, "desc")

            search._sort.append(script_str)
            search._sort.append(default_sort)

        # set selectbox
        urlkwargs.add(key, value)

    # default sort
    if not sortkwargs:
        ind_id = request.values.get("q", "")
        root_flag = True if ind_id and ind_id == "0" else False
        sort_key, sort = SearchSetting.get_default_sort(
            current_app.config["WEKO_SEARCH_TYPE_INDEX"], root_flag
        )
        sort_obj = dict()
        key_fileds = SearchSetting.get_sort_key(sort_key)

        if "custom_sort" not in sort_key:
            if sort == "desc":
                sort_obj[key_fileds] = dict(order="desc", unmapped_type="long")
                sort_key = "-" + sort_key
            else:
                sort_obj[key_fileds] = dict(order="asc", unmapped_type="long")
            search._sort.append(sort_obj)
        else:
            ind_id = request.values.get("q", "")
            if sort == "desc":
                script_str, default_sort = SearchSetting.get_custom_sort(ind_id, "desc")
                sort_key = "-" + sort_key
            else:
                script_str, default_sort = SearchSetting.get_custom_sort(ind_id, "asc")

            search._sort = []
            search._sort.append(script_str)
            search._sort.append(default_sort)

        urlkwargs.add("sort", sort_key)

    urlkwargs.add("q", query_q)
    urlkwargs.add("is_perm_paths", is_perm_paths)
    # debug elastic search query
    current_app.logger.debug(json.dumps((search.query()).to_dict()))
    return search, urlkwargs


def check_permission_user():
    """
    Check role user.

    :return: result
    """
    result = True
    user_id = (
        current_user.get_id()
        if current_user and current_user.is_authenticated
        else None
    )

    if user_id:
        users = current_app.config["WEKO_PERMISSION_ROLE_USER"]

        for lst in list(current_user.roles or []):

            if lst.name == users[2]:
                result = True

    return user_id, result


weko_search_factory = item_path_search_factory
es_search_factory = default_search_factory


def opensearch_factory(self, search, query_parser=None):
    """Factory for opensearch.

    :param self:
    :param search:
    :param query_parser:
    :return:
    """
    index_id = request.values.get("q")
    search_type = config.WEKO_SEARCH_TYPE_DICT["FULL_TEXT"]

    if index_id:
        index_id = str(index_id)
        return item_path_search_factory(self, search, index_id=index_id)
    else:
        additional_params = {
            "exact_title_match": request.args.get("exact_title_match") == "true"
        }
        return default_search_factory(
            self, search, query_parser, search_type=search_type, additional_params=additional_params
        )


def item_search_factory(
    self,
    search,
    start_date,
    end_date,
    list_index_id=None,
    query_with_publish_status=False,
    ranking=False,
):
    """Factory for opensearch.

    :param self:
    :param search: Record Search's instance
    :param start_date: Start date for search
    :param end_date: End date for search
    :param list_index_id: index tree list or None
    :param query_with_publish_status: Only query public items
    :param ranking: Ranking check
    :return:
    """

    def _get_query(start_term, end_term, indexes):
        query_string = "_type:{} AND relation_version_is_last:true ".format(
            current_app.config["INDEXER_DEFAULT_DOC_TYPE"]
        )
        if not query_with_publish_status:
            query_string += " AND publish_status:{} ".format(PublishStatus.PUBLIC.value)
        query_string += " AND publish_date:[{} TO {}]".format(start_term, end_term)

        query_q = {
            "size": 10000,
            "query": {"bool": {"must": [{"query_string": {"query": query_string}}]}},
            "sort": [{"publish_date": {"order": "desc"}}],
        }
        query_must_param = []
        if indexes:
            indexes_num = len(indexes)
            max_clause_count = 1024
            for div in range(0, int(indexes_num / max_clause_count) + 1):
                e_right = div * max_clause_count
                e_left = (
                    (div + 1) * max_clause_count
                    if indexes_num > (div + 1) * max_clause_count
                    else indexes_num
                )
                div_indexes = []
                for index in indexes[e_right:e_left]:
                    div_indexes.append({"wildcard": {"path": str(index)}})
                query_must_param.append({"bool": {"should": div_indexes}})
        if ranking:
            query_must_param.append({"exists": {"field": "path"}})
        if query_must_param:
            query_q["query"]["bool"]["must"] += query_must_param
        query_q["query"]["bool"]["must_not"] = [{"match": {"publish_status": PublishStatus.DELETE.value}}]
        return query_q

    query_q = _get_query(start_date, end_date, list_index_id)
    urlkwargs = MultiDict()

    try:
        extr = search._extra.copy()
        search.update_from_dict(query_q)
        search._extra.update(extr)
    except SyntaxError:
        current_app.logger.debug(
            "Failed parsing query: {0}".format(query_q), exc_info=True
        )
        raise InvalidQueryRESTError()
    # debug elastic search query
    current_app.logger.debug(json.dumps((search.query()).to_dict()))
    return search, urlkwargs

def _split_text_by_or(text):
    """split text by " OR " or " | "

    Args:
        text(str): input text
    Returns:
        list: list of split text
    """
    if not isinstance(text, str):
        return []
    text = text.replace("　", " ")
    pattern = r'(?<= )(?:OR|\|)(?= )'
    split_text_list = re.split(pattern, text)
    split_text_list = [item.strip() for item in split_text_list]
    return split_text_list
