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

"""Blueprint for Index Search rest."""

from datetime import datetime
import inspect
import json
import pickle
import traceback
from functools import partial

from flask import Blueprint, abort, current_app, jsonify, redirect, request, url_for, Response
from flask_babelex import get_locale
from elasticsearch.exceptions import ElasticsearchException
from invenio_db import db
from invenio_files_rest.storage import PyFSFileStorage
from invenio_i18n.ext import current_i18n
from invenio_oauth2server import require_api_auth, require_oauth_scopes
from invenio_pidstore import current_pidstore
from invenio_pidstore.errors import PIDInvalidAction
from invenio_records.api import Record
from invenio_records_rest.errors import (
    InvalidDataRESTError,
    MaxResultWindowRESTError,
    UnsupportedMediaRESTError,
)
from invenio_records_rest.links import default_links_factory
from invenio_records_rest.utils import obj_or_import_string
from invenio_records_rest.views import (
    create_error_handlers as records_rest_error_handlers,
)
from invenio_records_rest.views import (
    create_url_rules,
    need_record_permission,
    pass_record,
)
from invenio_records_rest.facets import terms_condition_filter, range_filter
from invenio_rest import ContentNegotiatedMethodView
from invenio_rest.views import create_api_errorhandler
from webargs import fields
from webargs.flaskparser import use_kwargs
from weko_accounts.utils import limiter
from weko_admin.models import SearchManagement as sm
from weko_admin.utils import get_facet_search_query
from werkzeug.http import generate_etag
from werkzeug.exceptions import NotFound
from weko_index_tree.api import Indexes
from weko_index_tree.utils import count_items, recorrect_private_items_count
from weko_items_ui.scopes import item_read_scope
from weko_records.api import ItemTypes
from weko_records.models import ItemType
from werkzeug.utils import secure_filename

from .error import InvalidRequestError, VersionNotFoundRESTError, InternalServerError
from .api import SearchSetting
from .query import default_search_factory


def create_blueprint(app, endpoints):
    """Create Invenio-Deposit-REST blueprint.

    See: :data:`invenio_deposit.config.DEPOSIT_REST_ENDPOINTS`.

    :param endpoints: List of endpoints configuration.
    :returns: The configured blueprint.
    """
    blueprint = Blueprint(
        "weko_search_rest",
        __name__,
        url_prefix="",
    )

    @blueprint.teardown_request
    def dbsession_clean(exception):
        current_app.logger.debug("weko_search_ui dbsession_clean: {}".format(exception))
        if exception is None:
            try:
                db.session.commit()
            except:
                db.session.rollback()
        db.session.remove()


    for endpoint, options in (endpoints or {}).items():
        if "record_serializers" in options:
            serializers = options.get("record_serializers")
            serializers = {
                mime: obj_or_import_string(func) for mime, func in serializers.items()
            }
        else:
            serializers = {}

        if "search_serializers" in options:
            serializers = options.get("search_serializers")
            search_serializers = {
                mime: obj_or_import_string(func) for mime, func in serializers.items()
            }
        else:
            search_serializers = {}

        record_class = obj_or_import_string(options.get("record_class"), default=Record)
        search_class = obj_or_import_string(options.get("search_class"))
        search_factory = obj_or_import_string(options.get("search_factory_imp"))

        search_class_kwargs = {}
        search_class_kwargs["index"] = options.get("search_index")
        search_class_kwargs["doc_type"] = options.get("search_type")
        search_class = partial(search_class, **search_class_kwargs)

        ctx = dict(
            read_permission_factory=obj_or_import_string(
                options.get("read_permission_factory_imp")
            ),
            create_permission_factory=obj_or_import_string(
                options.get("create_permission_factory_imp")
            ),
            update_permission_factory=obj_or_import_string(
                options.get("update_permission_factory_imp")
            ),
            delete_permission_factory=obj_or_import_string(
                options.get("delete_permission_factory_imp")
            ),
            record_class=record_class,
            search_class=search_class,
            record_loaders=obj_or_import_string(
                options.get("record_loaders"),
                default=app.config["RECORDS_REST_DEFAULT_LOADERS"],
            ),
            search_factory=search_factory,
            links_factory=obj_or_import_string(
                options.get("links_factory_imp"), default=default_links_factory
            ),
            pid_type=options.get("pid_type"),
            pid_minter=options.get("pid_minter"),
            pid_fetcher=options.get("pid_fetcher"),
            loaders={options.get("default_media_type"): lambda: request.get_json()},
            max_result_window=options.get("max_result_window"),
        )

        isr = IndexSearchResource.as_view(
            IndexSearchResource.view_name.format(endpoint),
            ctx=ctx,
            search_serializers=search_serializers,
            record_serializers=serializers,
            default_media_type=options.get("default_media_type"),
        )

        isr_api = IndexSearchResourceAPI.as_view(
            IndexSearchResourceAPI.view_name.format(endpoint),
            ctx=ctx,
            search_serializers=search_serializers,
            record_serializers=serializers,
            default_media_type=options.get("default_media_type"),
        )

        isrlg = IndexSearchResultList.as_view(
            IndexSearchResultList.view_name.format(endpoint),
            ctx=ctx,
            search_serializers=search_serializers,
            record_serializers=serializers,
            default_media_type=options.get("default_media_type"),
        )

        blueprint.add_url_rule(
            options.get("index_route"),
            view_func=isr,
            methods=['GET'],
        )

        blueprint.add_url_rule(
            options.get("search_api_route"),
            view_func=isr_api,
            methods=['GET'],
        )

        blueprint.add_url_rule(
            options.get("search_result_list_route"),
            view_func=isrlg,
            methods=['POST'],
        )

    return blueprint


class IndexSearchResource(ContentNegotiatedMethodView):
    """Index aggs Seach API."""

    view_name = "{0}_index"

    def __init__(
        self,
        ctx,
        search_serializers=None,
        record_serializers=None,
        default_media_type=None,
        **kwargs
    ):
        """Constructor."""
        super(IndexSearchResource, self).__init__(
            method_serializers={
                "GET": search_serializers,
                "POST": record_serializers,
            },
            default_method_media_type={
                "GET": default_media_type,
                "POST": default_media_type,
            },
            default_media_type=default_media_type,
            **kwargs
        )
        for key, value in ctx.items():
            setattr(self, key, value)

        self.pid_fetcher = current_pidstore.fetchers[self.pid_fetcher]

    def get(self, **kwargs):
        """Search records.

        :returns: the search result containing hits and aggregations as
        returned by invenio-search.
        """
        from weko_admin.models import FacetSearchSetting
        from weko_admin.utils import get_facet_search_query

        page = request.values.get("page", 1, type=int)
        size = request.values.get("size", 20, type=int)
        is_search = request.values.get("is_search", 0 ,type=int ) #toppage and search_page is 1
        community_id = request.values.get("c")
        params = {}
        facets = get_facet_search_query()
        search_index = current_app.config["SEARCH_UI_SEARCH_INDEX"]
        if facets and search_index and "post_filters" in facets[search_index]:
            post_filters = facets[search_index]["post_filters"]
            for param in post_filters:
                value = request.args.getlist(param)
                if value:
                    params[param] = value
        if page * size >= self.max_result_window:
            raise MaxResultWindowRESTError()
        urlkwargs = dict()
        search_obj = self.search_class()
        search = search_obj.with_preference_param().params(version=True)
        search = search[(page - 1) * size : page * size]
        search, qs_kwargs = self.search_factory(self, search)
        query = request.values.get("q")
        if query:
            urlkwargs["q"] = query

        # Execute search
        weko_faceted_search_mapping = FacetSearchSetting.get_activated_facets_mapping()
        from weko_admin.utils import get_title_facets
        titles, order, uiTypes, isOpens, displayNumbers, searchConditions = get_title_facets()
        current_app.logger.warning(search)
        for param in params:
            query_key = weko_faceted_search_mapping[param]
            if query_key == 'temporal':
                range_value = params[param][0].split('--')
                search = search.post_filter({"range": {"date_range1": {"gte": range_value[0], "lte": range_value[1]}}})
            else:
                if searchConditions[param]  == 'AND':
                    q_list = []
                    for value in params[param]:
                        q_list.append({ "term": {query_key: value}})
                    search = search.post_filter({"bool": {"must": q_list}})
                else:
                    search = search.post_filter({"terms": {query_key: params[param]}})
        search_result = search.execute()
        # Generate links for prev/next
        urlkwargs.update(
            size=size,
            _external=True,
        )
        links = dict(
            self=url_for("weko_search_rest.recid_index", page=page, **urlkwargs)
        )
        if page > 1:
            links["prev"] = url_for(
                "weko_search_rest.recid_index", page=page - 1, **urlkwargs
            )
        if (
            size * page < search_result.hits.total
            and size * page < self.max_result_window
        ):
            links["next"] = url_for(
                "weko_search_rest.recid_index", page=page + 1, **urlkwargs
            )
        # aggs result identify
        rd = search_result.to_dict()
        from weko_search_ui.utils import combine_aggs
        rd = combine_aggs(rd)
        q = request.values.get("q") or ""
        lang = current_i18n.language

        try:
            paths = Indexes.get_self_list(q, community_id)
        except BaseException:
            paths = []
        import pickle
        agp = rd["aggregations"]["path"]["buckets"]
        rd["aggregations"]["aggregations"] = pickle.loads(pickle.dumps(agp, -1))
        nlst = []
        items_count = dict()
        public_indexes = Indexes.get_public_indexes_list()
        recorrect_private_items_count(agp)
        for i in agp:
            items_count[i["key"]] = {
                "key": i["key"],
                "doc_count": i["doc_count"],
                "no_available": i["no_available"]["doc_count"],
                "public_state": True if i["key"] in public_indexes else False,
            }

        is_perm_paths = qs_kwargs.get("is_perm_paths", [])
        if is_search == 1:
            for k in range(len(agp)):
                if q == agp[k].get("key"):
                    current_idx = {}
                    _child_indexes = []
                    p = {}
                    for path in paths:
                        if path.path == agp[k].get("key"):
                            p = path
                            break
                    if hasattr(p,"name"):
                        agp[k]["name"] = p.name if p.name and lang == "ja" else p.name_en
                        agp[k]["date_range"] = dict()
                        comment = p.comment
                        agp[k]["comment"] = (comment,)
                        result = agp.pop(k)
                        result["comment"] = comment
                        current_idx = result
                        for _path in is_perm_paths:
                            if (
                                _path.startswith(str(p.path) + "/") or _path == p.path
                            ) and items_count.get(str(_path.split("/")[-1])):
                                _child_indexes.append(items_count[str(_path.split("/")[-1])])
                        private_count, public_count = count_items(_child_indexes)
                        current_idx["date_range"]["pub_cnt"] = public_count
                        current_idx["date_range"]["un_pub_cnt"] = private_count
                        nlst.append(current_idx)
                        break
            for p in paths:
                current_idx = {}
                _child_indexes = []
                if p.path == q:
                    continue
                index_id = p.cid
                index_info = Indexes.get_index(index_id=index_id)
                rss_status = index_info.rss_status
                nd = {
                    "doc_count": 0,
                    "key": p.path,
                    "name": p.name if p.name and lang == "ja" else p.name_en,
                    "date_range": {"pub_cnt": 0, "un_pub_cnt": 0},
                    "rss_status": rss_status,
                    "comment": p.comment,
                    "image_name": index_info.image_name,
                    "image_width": current_app.config['CHILD_INDEX_THUMBNAIL_WIDTH'],
                    "image_height": current_app.config['CHILD_INDEX_THUMBNAIL_HEIGHT'],
                }
                current_idx = nd
                for _path in is_perm_paths:
                    if (
                        _path.startswith(str(p.path) + "/") or _path == p.path
                    ) and items_count.get(str(_path.split("/")[-1])):
                        _child_indexes.append(items_count[str(_path.split("/")[-1])])
                private_count, public_count = count_items(_child_indexes)
                current_idx["date_range"]["pub_cnt"] = public_count
                current_idx["date_range"]["un_pub_cnt"] = private_count
                if p.path in is_perm_paths:
                    nlst.append(current_idx)
        else:
            for p in paths:
                m = 0
                current_idx = {}
                for k in range(len(agp)):
                    if p.path == agp[k].get("key"):
                        agp[k]["name"] = p.name if p.name and lang == "ja" else p.name_en
                        agp[k]["date_range"] = dict()
                        comment = p.comment
                        agp[k]["comment"] = (comment,)
                        result = agp.pop(k)
                        result["comment"] = comment
                        current_idx = result
                        m = 1
                        break
                if m == 0:
                    index_id = p.cid
                    index_info = Indexes.get_index(index_id=index_id)
                    rss_status = index_info.rss_status
                    nd = {
                        "doc_count": 0,
                        "key": p.path,
                        "name": p.name if p.name and lang == "ja" else p.name_en,
                        "date_range": {"pub_cnt": 0, "un_pub_cnt": 0},
                        "rss_status": rss_status,
                        "comment": p.comment,
                        "image_name": index_info.image_name,
                        "image_width": current_app.config['CHILD_INDEX_THUMBNAIL_WIDTH'],
                        "image_height": current_app.config['CHILD_INDEX_THUMBNAIL_HEIGHT'],
                    }
                    current_idx = nd
                _child_indexes = []
                for _path in is_perm_paths:
                    if (
                        _path.startswith(str(p.path) + "/") or _path == p.path
                    ) and items_count.get(str(_path.split("/")[-1])):
                        _child_indexes.append(items_count[str(_path.split("/")[-1])])
                private_count, public_count = count_items(_child_indexes)
                current_idx["date_range"]["pub_cnt"] = public_count
                current_idx["date_range"]["un_pub_cnt"] = private_count
                if p.path in is_perm_paths:
                    nlst.append(current_idx)
        agp.clear()
        # process index tree image info
        custom_sort_data = None
        if len(nlst):
            index_id = nlst[0].get("key").split("/")[-1]
            index_info = Indexes.get_index(index_id=index_id)
            # update by weko_dev17 at 2019/04/04
            if len(index_info.image_name) > 0:
                nlst[0]["img"] = index_info.image_name
            nlst[0]["display_format"] = index_info.display_format
            nlst[0]["rss_status"] = index_info.rss_status
            if index_id == q:
                custom_sort_data = index_info
        # Update rss_status for index child
        for idx in range(0, len(nlst)):
            index_id = nlst[idx].get("key").split("/")[-1]
            index_info = Indexes.get_index(index_id=index_id)
            nlst[idx]["rss_status"] = index_info.rss_status
            if index_id == q:
                custom_sort_data = index_info
        agp.append(nlst)
        for hit in rd["hits"]["hits"]:
            try:
                # Register comment
                _comment = list()
                _comment.append(hit["_source"]["title"][0])
                hit["_source"]["_comment"] = _comment
                # Register custom_sort
                cn = hit["_source"]["control_number"]
                if custom_sort_data and custom_sort_data.item_custom_sort.get(cn):
                    hit["_source"]["custom_sort"] = {
                        str(custom_sort_data.id): str(custom_sort_data.item_custom_sort.get(cn))
                    }
            except Exception:
                pass

        # add info (headings & page info)
        try:
            item_type_list = {}
            for hit in rd["hits"]["hits"]:
                # get item type schema
                item_type_id = hit["_source"]["_item_metadata"]["item_type_id"]
                if item_type_id in item_type_list:
                    item_type = pickle.loads(pickle.dumps(item_type_list[item_type_id], -1))
                else:
                    item_type = ItemType.query.filter_by(id=item_type_id).first()
                    item_type_list[item_type_id] = pickle.loads(pickle.dumps(item_type, -1))
                # heading
                heading = get_heading_info(hit, lang, item_type)
                hit["_source"]["heading"] = heading
                # page info
                if "pageStart" not in hit["_source"]:
                    hit["_source"]["pageStart"] = []
                if "pageEnd" not in hit["_source"]:
                    hit["_source"]["pageEnd"] = []
        except Exception as ex:
            current_app.logger.error(ex)

        return self.make_response(
            pid_fetcher=self.pid_fetcher,
            search_result=rd,
            links=links,
            item_links_factory=self.links_factory,
        )


def get_heading_info(data, lang, item_type):
    """Get heading info."""
    item_key = None
    heading_subitem_key = "subitem_heading_banner_headline"
    subheading_subitem_key = "subitem_heading_headline"
    lang_subitem_key = "subitem_heading_language"
    # get item id of heading
    if item_type and "properties" in item_type.schema:
        for key, value in item_type.schema["properties"].items():
            if (
                "properties" in value
                and value["type"] == "object"
                and heading_subitem_key in value["properties"]
            ):
                item_key = key
                break
            elif (
                "items" in value
                and value["type"] == "array"
                and "properties" in value["items"]
                and heading_subitem_key in value["items"]["properties"]
            ):
                item_key = key
                break

    # get heading data
    heading_text = ""
    subheading_text = ""
    if item_key and item_key in data["_source"]["_item_metadata"]:
        temp = data["_source"]["_item_metadata"][item_key]["attribute_value_mlt"]
        if len(temp) > 1:
            for v in temp:
                heading_tmp = ""
                subheading_tmp = ""
                if heading_subitem_key in v:
                    heading_tmp = v[heading_subitem_key]
                if subheading_subitem_key in v:
                    subheading_tmp = v[subheading_subitem_key]
                if lang and lang_subitem_key in v and v[lang_subitem_key] == lang:
                    heading_text = heading_tmp
                    subheading_text = subheading_tmp
                    break
        elif len(temp) == 1 or (heading_text == "" and subheading_text == ""):
            if heading_subitem_key in temp[0]:
                heading_text = temp[0][heading_subitem_key]
            if subheading_subitem_key in temp[0]:
                subheading_text = temp[0][subheading_subitem_key]
    if subheading_text:
        heading = heading_text + " : " + subheading_text
    else:
        heading = heading_text

    return heading


class IndexSearchResourceAPI(ContentNegotiatedMethodView):
    """Resource for records searching."""

    view_name = '{0}_searchapi'

    def __init__(
        self,
        ctx,
        search_serializers=None,
        record_serializers=None,
        default_media_type=None,
        **kwargs
    ):
        """Constructor."""
        super(IndexSearchResourceAPI, self).__init__(
            method_serializers={
                'GET': search_serializers,
            },
            default_method_media_type={
                'GET': default_media_type,
            },
            default_media_type=default_media_type,
            **kwargs
        )
        for key, value in ctx.items():
            setattr(self, key, value)

        self.pid_fetcher = current_pidstore.fetchers[self.pid_fetcher]
        self.search_factory = default_search_factory

    @require_api_auth(allow_anonymous=True)
    @require_oauth_scopes(item_read_scope.id)
    @limiter.limit('')
    def get(self, **kwargs):
        """Search records.

        :returns: Search result containing hits and aggregations as returned by invenio-search.
        """
        version = kwargs.get('version')
        func_name = f'get_{version}'
        if func_name in [func[0] for func in inspect.getmembers(self, inspect.ismethod)]:
            return getattr(self, func_name)(**kwargs)
        else:
            raise VersionNotFoundRESTError()

    def get_v1(self, **kwargs):
        try:
            # Language setting
            language = request.headers.get('Accept-Language')
            if language:
                get_locale().language = language

            # Generate Search Query Class
            search_obj = self.search_class()
            search = search_obj.with_preference_param().params(version=True)

            # Pagenation Setting
            page = request.values.get('page', type=int)
            cursor = request.values.get('cursor')
            size = request.values.get('size', 20, type=int)
            if not page and cursor:
                cursor = cursor.split(',')
                search._extra.update(dict(search_after=cursor))
                search._extra.update(dict(size=size))
            else:
                if not page:
                    page = 1
                if page * size >= self.max_result_window:
                    raise MaxResultWindowRESTError()
                search = search[(page - 1) * size: page * size]

            # filter by registered item type in RocrateMapping
            from weko_records_ui.models import RocrateMapping
            mapping = RocrateMapping.query.all()
            item_type_ids = [x.item_type_id for x in mapping]
            item_types = ItemTypes.get_records(item_type_ids)
            additional_params = {
                'itemtype': ','.join([x.model.item_type_name.name for x in item_types]),
                'exact_title_match': request.args.get('exact_title_match') == 'true'
            }

            # Query Generate
            search, qs_kwargs = self.search_factory(self, search, additional_params=additional_params)

            # search only if mapping exists
            if len(item_type_ids) == 0:
                search = search.query('match_none')

            # Sort Setting
            sort = request.values.get('sort')
            sort_query = []
            is_id_sort = False
            if sort:
                sort = sort.split(',')
                for sort_key_element in sort:
                    order = 'asc'
                    if sort_key_element.startswith('-'):
                        sort_key_element = sort_key_element.lstrip('-')
                        order = 'desc'

                    key_filed = SearchSetting.get_sort_key(sort_key_element)
                    if key_filed:
                        sort_element = {}
                        sort_element[key_filed] = {'order': order, 'unmapped_type': 'long'}
                        sort_query.append(sort_element)
                        if sort_key_element == 'controlnumber':
                            is_id_sort = True

            if not is_id_sort:
                sort_element = {}
                sort_element['control_number'] = {'order': 'asc', 'unmapped_type': 'long'}
                sort_query.append(sort_element)

            search._sort = sort_query

            # Facet Setting
            facets = get_facet_search_query(has_permission=False)
            search_index = current_app.config['SEARCH_UI_SEARCH_INDEX']
            aggs = facets.get(search_index, {}).get('aggs', {})
            for name, agg in aggs.items():
                search.aggs[name] = agg

            # Execute search
            search_results = search.execute()
            search_results = search_results.to_dict()

            # Convert RO-Crate format
            from weko_records_ui.utils import RoCrateConverter
            converter = RoCrateConverter()
            rocrate_list = []
            for search_result in search_results['hits']['hits']:
                metadata = search_result['_source']['_item_metadata']
                item_type_id = metadata['item_type_id']
                mapping = RocrateMapping.query.filter_by(item_type_id=item_type_id).one_or_none()
                rocrate = converter.convert(metadata, mapping.mapping, language)
                rocrate_list.append({
                    'id': search_result['_source']['control_number'],
                    'metadata': rocrate,
                })

            # Check pretty
            indent = 4 if request.args.get('pretty') == 'true' else None

            cursor = None
            if len(search_results['hits']['hits']) > 0:
                sort_key = search_results['hits']['hits'][-1].get('sort')
                if sort_key:
                    cursor = sort_key[0]

            # Create facet result
            facet_list = {}
            dic = search_results.get('aggregations', {})
            for k, v in dic.items():
                if isinstance(v, dict) and k in v and 'buckets' in v[k]:
                    facet_list[k] = {}
                    facet_list[k]['buckets'] = v[k]['buckets']

            # Create result
            result = {
                'total_results': search_results['hits']['total'],
                'count_results': len(rocrate_list),
                'cursor': cursor,
                'page': page,
                'search_results': rocrate_list,
                'aggregations' : facet_list
            }
            res = Response(
                response=json.dumps(result, indent=indent),
                status=200,
                content_type='application/json')

            # Response header setting
            res.headers['Cache-Control'] = 'no-store'
            res.headers['Pragma'] = 'no-cache'
            res.headers['Expires'] = 0

            return res

        except MaxResultWindowRESTError:
            raise MaxResultWindowRESTError()

        except ElasticsearchException:
            raise InternalServerError()

        except Exception:
            current_app.logger.error(traceback.print_exc())
            raise InternalServerError()


class IndexSearchResultList(ContentNegotiatedMethodView):
    """Get resource for records searching."""

    view_name = '{0}_search_result_get'

    def __init__(
        self,
        ctx,
        search_serializers=None,
        record_serializers=None,
        default_media_type=None,
        **kwargs
    ):
        """Constructor."""
        super(IndexSearchResultList, self).__init__(
            method_serializers={
                'POST': search_serializers,
            },
            default_method_media_type={
                'POST': default_media_type,
            },
            default_media_type=default_media_type,
            **kwargs
        )
        for key, value in ctx.items():
            setattr(self, key, value)

        self.pid_fetcher = current_pidstore.fetchers[self.pid_fetcher]
        self.search_factory = default_search_factory

    @require_api_auth(allow_anonymous=True)
    @require_oauth_scopes(item_read_scope.id)
    @limiter.limit('')
    def post(self, **kwargs):
        """Search records.

        :returns: Search result containing hits and aggregations as returned by invenio-search.
        """
        version = kwargs.get('version')
        func_name = f'post_{version}'
        if func_name in [func[0] for func in inspect.getmembers(self, inspect.ismethod)]:
            return getattr(self, func_name)(**kwargs)
        else:
            raise VersionNotFoundRESTError()

    def post_v1(self, **kwargs):
        try:
            # Language setting
            from weko_user_profiles.config import USERPROFILES_LANGUAGE_LIST
            language = request.headers.get('Accept-Language')
            if not language in [lang[0] for lang in USERPROFILES_LANGUAGE_LIST[1:]]:
                language = 'en'
            get_locale().language = language

            # Get input json
            try:
                input_json = request.json
                for input_header in input_json:
                    if not(type(input_header["name"]) == dict and input_header["roCrateKey"]):
                        raise InvalidRequestError()
            except:
                raise InvalidRequestError()
            if not input_json:
                raise InvalidRequestError()

            # Generate Search Query Class
            search_obj = self.search_class()
            search = search_obj.with_preference_param().params(version=True)
            search._extra.update(dict(size=10000))

            # filter by registered item type in RocrateMapping
            from weko_records_ui.models import RocrateMapping
            mapping = RocrateMapping.query.all()
            item_type_ids = [x.item_type_id for x in mapping]
            item_types = ItemTypes.get_records(item_type_ids)
            additional_params = {
                'itemtype': ','.join([x.model.item_type_name.name for x in item_types]),
                'exact_title_match': request.args.get('exact_title_match') == 'true'
            }

            # Query Generate
            search, qs_kwargs = self.search_factory(self, search, additional_params=additional_params)

            # search only if mapping exists
            if len(item_type_ids) == 0:
                search = search.query('match_none')

            # Sort Setting
            sort = request.values.get('sort')
            sort_query = []
            is_id_sort = False
            if sort:
                sort = sort.split(',')
                for sort_key_element in sort:
                    order = 'asc'
                    if sort_key_element.startswith('-'):
                        sort_key_element = sort_key_element.lstrip('-')
                        order = 'desc'

                    key_filed = SearchSetting.get_sort_key(sort_key_element)
                    if key_filed:
                        sort_element = {}
                        sort_element[key_filed] = {'order': order, 'unmapped_type': 'long'}
                        sort_query.append(sort_element)
                        if sort_key_element == 'controlnumber':
                            is_id_sort = True

            if not is_id_sort:
                sort_element = {}
                sort_element['control_number'] = {'order': 'asc', 'unmapped_type': 'long'}
                sort_query.append(sort_element)

            search._sort = sort_query

            # Execute search
            search_results = search.execute()
            search_results = search_results.to_dict()

            # Convert RO-Crate format
            from weko_records_ui.utils import RoCrateConverter
            converter = RoCrateConverter()
            rocrate_list = []
            update_time_list = []
            for search_result in search_results['hits']['hits']:
                source = search_result['_source']
                metadata = source['_item_metadata']
                item_type_id = metadata['item_type_id']
                mapping = RocrateMapping.query.filter_by(item_type_id=item_type_id).one_or_none()
                rocrate = converter.convert(metadata, mapping.mapping, language)
                rocrate_list.append({
                    'id': search_result['_source']['control_number'],
                    'metadata': rocrate,
                })
                update_time_list.append(source["_updated"])

            # Create TSV
            from .utils import result_download_ui
            dl_response = result_download_ui(rocrate_list, input_json, language)

            # Check Etag
            hash_str = str(search_result) + str(input_json)
            etag = generate_etag(hash_str.encode('utf-8'))
            self.check_etag(etag, weak=True)

            return dl_response

        except (InvalidRequestError, NotFound) as e:
            raise e

        except ElasticsearchException:
            raise InternalServerError()

        except Exception:
            current_app.logger.error(traceback.print_exc())
            raise InternalServerError()
