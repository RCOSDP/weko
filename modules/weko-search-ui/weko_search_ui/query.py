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

import orjson
import re
import sys
import pytz
from datetime import datetime
from datetime import timezone
from functools import partial

from elasticsearch_dsl.query import Bool, Q
from flask import current_app, request
from flask_security import current_user
from flask_babelex import get_timezone
from invenio_communities.models import Community
from invenio_records_rest.errors import InvalidQueryRESTError
from weko_index_tree.api import Indexes, Index
from weko_index_tree.config import WEKO_INDEX_TREE_PUBLIC_DEFAULT_TIMEZONE
from weko_records.models import ItemTypeName
from weko_index_tree.utils import get_user_roles
from weko_schema_ui.models import PublishStatus
from werkzeug.datastructures import MultiDict

from . import config
from .api import SearchSetting
from .permissions import search_permission


def get_permission_filter(index_id: str = None):
    """Check permission.

    Args:
        index_id (str, optional): Index Identifier Number. Defaults to None.

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
                should_path.append(Q("terms", path=index_id))

            terms = Q("bool", should=should_path)
        else:  # In case search_type is keyword or index
            if index_id in is_perm_indexes:
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
            shared_user_match = Q("match", weko_shared_id=user_id)
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


def default_search_factory(self, search, query_parser=None, search_type=None):
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

    def _get_search_index_query(index_key, index_list_key, include_childe_key):

        def _get_child_index(idx_list):
            index_id_list = []
            for index in idx_list:
                child_id_list = [child_idx.id for child_idx in Index.query.filter_by(parent=index).all()]
                if child_id_list:
                    for child_id in child_id_list:
                        index_id_list.append(str(child_id))
                    index_id_list.extend(_get_child_index(child_id_list))
            return index_id_list

        index_id_list = []
        index_id = request.values.get(index_key)
        if index_id:
            index_id_list.append(str(index_id))

        idx = request.values.get(index_list_key)
        if idx:
            idx_list = idx.split(',')
            index_id_list.extend(idx_list)

            recursive = request.values.get(include_childe_key)
            if recursive == '1':
                index_id_list.extend(_get_child_index(idx_list))

        shud = []
        for index_id in index_id_list:
            if index_id.isdecimal():
                shud.append(Q("match", **{'path.tree': int(index_id)}))

        return Q("bool", should=shud) if shud else None

    def _get_detail_keywords_query():
        """Get keywords query.

        :return: Query parser.
        """

        def _get_opensearch_parameter(k):
            kv = None
            if k == 'publisher':
                kv = request.values.get('pub')
            elif k == 'cname':
                kv = request.values.get('con')
            elif k == 'mimetype':
                kv = request.values.get('form')
            elif k == 'srctitle':
                kv = request.values.get('jtitle')
            elif k == 'spatial':
                kv = request.values.get('sp')
            elif k == 'temporal':
                kv = request.values.get('era')
            elif k == 'versiontype':
                kv = request.values.get('textver')
            elif k == 'dissno':
                kv = request.values.get('grantid')
            elif k == 'dgname':
                kv = request.values.get('grantor')
            elif k == 'itemtype':
                kv = request.values.get('itemTypeList')
                if kv is None:
                    return kv
                # Convert ID to Name
                item_type_id_list = [int(i) for i in kv.split(',')]
                item_type_name_list = ItemTypeName.query.filter(ItemTypeName.id.in_(item_type_id_list)).all()
                kv = ",".join([i.name for i in item_type_name_list])
            elif k == 'language':
                kv = request.values.get('ln')
                if kv is not None and kv != '':
                    lang_dict = current_app.config['WEKO_SEARCH_UI_OPENSEARCH_LANGUAGE_PARAM']
                    lang_list = []
                    for lang in kv.split(','):
                        lang_list.append(lang_dict.get(lang))
                    kv = ','.join(lang_list)

            return kv

        def _get_keywords_query(k, v):
            qry = None
            kv = (
                request.values.get("lang") if (k == "language" and request.values.get('q') is not None) else request.values.get(k)
            )

            if not kv:
                kv = _get_opensearch_parameter(k)
                if not kv:
                    return

            if isinstance(v, str):
                kvl = kv.split(",")
                shud = []
                for j in kvl:
                    name_dict = dict(operator="and")
                    name_dict.update(dict(query=j))
                    shud.append(Q("match", **{v: name_dict}))
                if shud:
                    qry = Q("bool", should=shud)
            elif isinstance(v, list):
                qry = Q(
                    "multi_match",
                    query=kv,
                    type="most_fields",
                    minimum_should_match="75%",
                    operator="and",
                    fields=v,
                )
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
            kv = request.values.get(k)
            if not kv:
                if k == 'subject':
                    kv = request.values.get('kw')
                if not kv:
                    return
            if isinstance(v, tuple) and len(v) > 1 and isinstance(v[1], dict):
                # attr keyword in request url
                attrs = map(lambda x: (x, request.values.get(x)), list(v[1].keys()))
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
                    else:
                        name = v[0] + ".value"
                        return Bool(
                            must=[
                                {"term": {name: kv}},
                            ]
                        )
            return None

        def _get_nested_query(k, v):
            # text value
            kv = request.values.get(k)

            if not kv:
                return

            shuld = []

            if isinstance(v, tuple) and len(v) > 1 and isinstance(v[1], dict):
                # attr keyword in request url
                for attr_key, attr_val_str in map(
                    lambda x: (x, request.values.get(x)), list(v[1].keys())
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
                                            name = alst[0] + ".value"
                                            name_dict = dict(operator="and")
                                            name_dict.update(dict(query=kv))
                                            mut = [Q("match", **{name: name_dict})]
                                            qt = None

                                            if "=*" in alst[1]:
                                                name = alst[0] + "." + val_attr_lst[0]
                                                qt = [
                                                    Q("term", **{name: val_attr_lst[1]})
                                                ]

                                            mut.extend(qt or [])
                                            qry = Q("bool", must=mut)
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
                date_from = request.values.get(k + "_" + v[0][0])
                date_to = request.values.get(k + "_" + v[0][1])

                if not date_from:
                    if k == 'dategranted':
                        date_from = request.values.get('grantDateFrom')
                if not date_to:
                    if k == 'dategranted':
                        date_to = request.values.get('grantDateUntil')

                if not date_from and not date_to:
                    return

                pattern = r"^(\d{4}-\d{2}-\d{2})|(\d{4}-\d{2})|(\d{4})|(\d{6})|(\d{8})$"
                p = re.compile(pattern)

                qv = {}
                if date_from and p.match(date_from):
                    if len(date_from) == 8:
                        date_from = datetime.strptime(date_from, "%Y%m%d").strftime("%Y-%m-%d")
                    if len(date_from) == 6:
                        date_from = datetime.strptime(date_from, "%Y%m").strftime("%Y-%m")
                    qv.update(dict(gte=date_from))
                if date_to and p.match(date_to):
                    if len(date_to) == 8:
                        date_to = datetime.strptime(date_to, "%Y%m%d").strftime("%Y-%m-%d")
                    if len(date_to) == 6:
                        date_to = datetime.strptime(date_to, "%Y%m").strftime("%Y-%m")
                    qv.update(dict(lte=date_to))
                if not qv:
                    return

                if isinstance(v[1], str):
                    qry = Q("range", **{v[1]: qv})
                elif isinstance(v[1], tuple) and len(v[1]) >= 2:
                    path = v[1][0]
                    dt = v[1][1]

                    if isinstance(dt, dict):

                        for attr_key, attr_val_str in map(
                            lambda x: (x, request.values.get(x)), list(dt.keys())
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
                request.values.get("lang") if k == "language" else request.values.get(k)
            )

            if not kv:
                return

            if isinstance(v, str):
                name_dict = dict(operator="and")
                name_dict.update(dict(query=kv))
                qry = Q("match", **{v: name_dict})

            return qry

        def _get_range_query(k, v):
            qry = None

            if isinstance(v, list) and len(v) >= 2:
                value_from = request.values.get(k + "_" + v[0][0])
                value_to = request.values.get(k + "_" + v[0][1])

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
                value_lat = request.values.get(k + "_" + v[0][0])
                value_lon = request.values.get(k + "_" + v[0][1])
                value_distance = request.values.get(k + "_" + v[0][2])

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
                value_lat = request.values.get(k + "_" + v[0][0])
                value_lon = request.values.get(k + "_" + v[0][1])
                value_distance = request.values.get(k + "_" + v[0][2])

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

        def _get_search_type_query():
            type_list = current_app.config["WEKO_SEARCH_UI_OPENSEARCH_TYPE_PARAM"]
            type_idxs = request.values.get('typeList')
            if not type_idxs:
                return None

            shud = []
            for type_idx in type_idxs.split(','):
                if not type_idx.isdecimal():
                    continue
                target_list = type_list[int(type_idx)]
                for target in target_list:
                    name_dict = dict(operator="and")
                    name_dict.update(dict(query=target))
                    shud.append(Q("match", **{'type.raw': name_dict}))

            if shud:
                return Q("bool", should=shud)

            return None

        def _get_search_id_query():
            id = request.values.get('idDes')
            if not id:
                return

            id_idxs = request.values.get('idList')
            id_idxs = id_idxs.split(',') if id_idxs else []
            id_type_list = current_app.config["WEKO_SEARCH_UI_OPENSEARCH_ID_PARAM"]

            shuld = []
            for idx, id_type in enumerate(id_type_list):
                if id_idxs and str(idx) not in id_idxs:
                    continue

                if isinstance(id_type, str):
                    name = id_type + ".value"
                    name_dict = dict(operator="and")
                    name_dict.update(dict(query=id))
                    mut = [Q("match", **{name: name_dict})]

                    qry = Q("bool", must=mut)
                    shuld.append(Q("nested", path=id_type, query=qry))

                elif isinstance(id_type, list):
                    qry = Q(
                        "multi_match",
                        query=id,
                        type="most_fields",
                        minimum_should_match="75%",
                        operator="and",
                        fields=id_type,
                    )
                    shuld.append(qry)

            return Q("bool", should=shuld) if shuld else None

        def _get_search_license_query():
            riDes = request.values.get('riDes')
            riList = request.values.get('riList')
            riList = riList.split(',') if riList else []
            if riList:
                license_type_list = current_app.config["WEKO_SEARCH_UI_OPENSEARCH_LICENSE_PARAM"]

                target = []
                search_rides = False
                for k, v in license_type_list.items():
                    if k not in riList:
                        continue
                    if k != 'free_input':
                        target.extend(v)
                    else:
                        if riDes:
                            search_rides = True
                        else:
                            target.extend(v)

                shuld = []
                if target:
                    query = Q('bool', must=[{'terms': {'content.licensetype.raw': target}}])
                    nested = Q('nested', path='content', query=query)
                    shuld.append(nested)
                if search_rides:
                    other_must = [
                        {'terms': {'content.licensetype.raw': ['license_free']}},
                        {'terms': {"content.licensefree.raw": [riDes]}}
                    ]
                    other_query = Q('bool', must=other_must)
                    other_nested = Q('nested', path='content', query=other_query)
                    shuld.append(other_nested)

                return Q('bool', should=shuld) if shuld else None

            else:
                if riDes:
                    # Search only free_input
                    other_must = [
                        {'terms': {'content.licensetype.raw': ['license_free']}},
                        {'terms': {"content.licensefree.raw": [riDes]}}
                    ]
                    other_query = Q('bool', must=other_must)
                    shuld = [Q('nested', path='content', query=other_query)]
                    return Q('bool', should=shuld) if shuld else None
                else:
                    return None

        def _get_date_query_for_opensearch():
            qy = []
            date_created = request.values.get('date')
            if date_created:
                qv = {'gte': date_created, 'lte': date_created}
                shud = [Q('term', **{'date.dateType': 'Created'})]

                qry = Q('range', **{'date.value': qv})
                qry = Q('nested', path='date', query=Q('bool', should=shud, must=[qry]))
                qy.append(qry)

            year_issued_from = request.values.get('pubYearFrom')
            year_issued_until = request.values.get('pubYearUntil')
            if year_issued_from or year_issued_until:
                qv = {}
                if year_issued_from:
                    qv.update(dict(gte=year_issued_from + '-01-01'))
                if year_issued_until:
                    qv.update(dict(lte=year_issued_until + '-12-31'))
                shud = [Q('term', **{'date.dateType': 'Issued'})]

                qry = Q('range', **{'date.value': qv})
                qry = Q('nested', path='date', query=Q('bool', should=shud, must=[qry]))
                qy.append(qry)

            date_issued_from = request.values.get('pubDateFrom')
            date_issued_until = request.values.get('pubDateUntil')
            if date_issued_from or date_issued_until:
                qv = {}
                if date_issued_from:
                    qv.update(dict(gte=date_issued_from))
                if date_issued_until:
                    qv.update(dict(lte=date_issued_until))
                shud = [Q('term', **{'date.dateType': 'Issued'})]

                qry = Q('range', **{'date.value': qv})
                qry = Q('nested', path='date', query=Q('bool', should=shud, must=[qry]))
                qy.append(qry)

            return qy


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

            qy = _get_search_index_query('index_id', 'idx', 'recursive')
            if qy:
                mut.append(qy)
            qy = _get_search_type_query()
            if qy:
                mut.append(qy)
            qy = _get_search_id_query()
            if qy:
                mut.append(qy)
            qy = _get_search_license_query()
            if qy:
                mut.append(qy)
            qy = _get_date_query_for_opensearch()
            if qy:
                mut.extend(qy)

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

        mst, _ = get_permission_filter(root_node_id)
        q = _get_search_qs_query(qs)

        if q:
            mst.append(q)

        mst.extend(_get_detail_keywords_query())
        return Q("bool", must=mst) if mst else Q()

    def _get_file_content_query(qstr):
        """Query for searching indexed file contents."""
        multi_cont_q = Q(
            "multi_match",
            query=qstr,
            operator="and",
            fields=["content.attachment.content"],
        )

        # Search fields may increase so leaving as multi
        multi_q = Q(
            "query_string",
            query=qstr,
            default_operator="and",
            fields=["search_*", "search_*.ja"],
        )

        nested_content = Q("nested", query=multi_cont_q, path="content")
        return Q("bool", should=[nested_content, multi_q])

    def _get_file_meta_query(qstr):
        """Query for searching indexed file meta."""
        # Search fields may increase so leaving as multi
        qstr = "*" + qstr + "*"
        multi_q = Q(
            "query_string",
            query=qstr,
            default_operator="and",
            fields=["_item_metadata.*.raw"],
        )

        return Q("bool", should=[multi_q])

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

        qs_all = request.values.get('all')
        if qs_all:
            q_s = _get_file_content_query(qs_all)
            mst.append(q_s)

        qs_meta = request.values.get('meta')
        if qs_meta:
            q_s = _get_file_meta_query(qs_meta)
            mst.append(q_s)

        if not qs_all and not qs_meta and qstr:
            q_s = _get_file_content_query(qstr)
            mst.append(q_s)

        q_s = _get_search_index_query('', 'cur_index_id', 'recursive')
        if q_s:
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
        mst, _ = get_permission_filter(root_node_id)

        # multi keywords search filter
        mkq = _get_detail_keywords_query()

        if mkq:
            # details search
            mst.extend(mkq)

        qs_all = request.values.get('all')
        if qs_all:
            q_s = _get_file_content_query(qs_all)
            mst.append(q_s)

        qs_meta = request.values.get('meta')
        if qs_meta:
            q_s = _get_file_meta_query(qs_meta)
            mst.append(q_s)

        if not qs_all and not qs_meta and qstr:
            q_s = _get_file_content_query(qstr)
            mst.append(q_s)

        q_s = _get_search_index_query('', 'cur_index_id', 'recursive')
        if q_s:
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

    q_param = request.values.get("q", "")
    if not q_param:
        qs = request.values.get("keyword")
    else:
        # Escape special characters for avoiding ES search errors
        qs = (
            q_param
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
    current_app.logger.debug("query: {}".format(orjson.dumps((search.query()).to_dict()).decode()))
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
        tz = pytz.timezone(WEKO_INDEX_TREE_PUBLIC_DEFAULT_TIMEZONE)
        now = datetime.now()
        utc_offset = pytz.utc.localize(now) - tz.localize(now)
        minutes = int(utc_offset.total_seconds() / 60) if utc_offset else 0
        offset = f"{'+' if minutes >= 0 else '-'}{abs(minutes)}m"
        date_range = "now+1d" + offset + "/d"
        query_q = {
            "_source": {"excludes": ["content"]},
            "query": {
                "bool": {"must": [{"match": {"relation_version_is_last": "true"}}]}
            },
            "aggs": {
                "path": {
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
                                            {"from": date_range},
                                            {"to": date_range},
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

        q = request.values.get("q") or "0" if index_id is None else index_id

        if q != "0":
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
                    child_idx_str = "|".join(child_idx)
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

                    query_q = orjson.dumps(query_q).decode().replace("@idxchild", child_idx_str)
                    query_q = orjson.loads(query_q)
                except BaseException as ex:
                    current_app.logger.error(ex)
                    import traceback

                    traceback.print_exc(file=sys.stdout)

            count = str(Indexes.get_index_count())
            query_q = orjson.dumps(query_q).decode().replace("@count", count)
            query_q = orjson.loads(query_q)

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
                                                {"from": date_range},
                                                {"to": date_range},
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
            query_not_q = orjson.dumps(query_not_q).decode().replace("@count", count)
            query_not_q = orjson.loads(query_not_q)

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
    current_app.logger.debug(orjson.dumps(str((search.query()).to_dict())).decode())
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
        return default_search_factory(
            self, search, query_parser, search_type=search_type
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
    current_app.logger.debug(orjson.dumps((search.query()).to_dict()).decode())
    return search, urlkwargs


def feedback_email_search_factory(self, search):
    """Factory for search feedback email list.

    :param self:
    :param search:
    :return:
    """

    def _get_query():
        query_string = "_type:{} AND " "relation_version_is_last:true ".format(
            current_app.config["INDEXER_DEFAULT_DOC_TYPE"]
        )
        query_q = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "nested": {
                                "path": "feedback_mail_list",
                                "query": {
                                    "bool": {
                                        "must": [
                                            {
                                                "exists": {
                                                    "field": "feedback_mail_list.email"
                                                }
                                            }
                                        ]
                                    }
                                },
                            }
                        },
                        {"query_string": {"query": query_string}},
                    ]
                }
            },
            "aggs": {
                "feedback_mail_list": {
                    "nested": {"path": "feedback_mail_list"},
                    "aggs": {
                        "email_list": {
                            "terms": {
                                "field": "feedback_mail_list.email",
                                "size": config.WEKO_SEARCH_MAX_FEEDBACK_MAIL,
                            }
                        }
                    },
                }
            },
        }
        return query_q

    query_q = _get_query()

    try:
        # Aggregations.
        extr = search._extra.copy()
        search.update_from_dict(query_q)
        search._extra.update(extr)
    except SyntaxError:
        current_app.logger.debug(
            "Failed parsing query: {0}".format(query_q), exc_info=True
        )
        raise InvalidQueryRESTError()
    # debug elastic search query
    current_app.logger.debug(orjson.dumps((search.query()).to_dict()).decode())
    return search

def facet_condition_search_factory(self, search, query_parser=None):
    """Factory for get facet condition.

    :param self:
    :param search:
    :param query_parser:
    :return:
    """
    search_type = request.values.get("search_type")
    q = str(request.values.get("q"))
    if search_type == config.WEKO_SEARCH_TYPE_DICT["INDEX"] and re.fullmatch('\d+', q):
        # index search
        return item_path_search_factory(self, search, index_id=q)
    else:
        # full_text or keyword search
        search_type = config.WEKO_SEARCH_TYPE_DICT["FULL_TEXT"] if search_type == config.WEKO_SEARCH_TYPE_DICT["INDEX"] else search_type
        return default_search_factory(
            self, search, query_parser, search_type=search_type
        )