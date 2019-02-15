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

import json
import os.path
import shutil
import uuid
# from copy import deepcopy
from functools import partial

from flask import (
    Blueprint, abort, current_app, jsonify, redirect, request, url_for)
from invenio_db import db
from invenio_files_rest.storage import PyFSFileStorage
from invenio_oauth2server import require_api_auth, require_oauth_scopes
from invenio_pidstore import current_pidstore
from invenio_pidstore.errors import PIDInvalidAction
from invenio_records.api import Record
from invenio_records_rest.errors import (
    InvalidDataRESTError, MaxResultWindowRESTError, UnsupportedMediaRESTError)
from invenio_records_rest.links import default_links_factory
from invenio_records_rest.utils import obj_or_import_string
from invenio_records_rest.views import \
    create_error_handlers as records_rest_error_handlers
from invenio_records_rest.views import (
    create_url_rules, need_record_permission, pass_record)
from invenio_rest import ContentNegotiatedMethodView
from invenio_rest.views import create_api_errorhandler
from webargs import fields
from webargs.flaskparser import use_kwargs
from weko_index_tree.api import Indexes
from werkzeug.utils import secure_filename
from invenio_i18n.ext import current_i18n
from . import config
from weko_admin.models import SearchManagement as sm

def create_blueprint(app, endpoints):
    """Create Invenio-Deposit-REST blueprint.

    See: :data:`invenio_deposit.config.DEPOSIT_REST_ENDPOINTS`.

    :param endpoints: List of endpoints configuration.
    :returns: The configured blueprint.
    """
    blueprint = Blueprint(
        'weko_search_rest',
        __name__,
        url_prefix='',
    )

    for endpoint, options in (endpoints or {}).items():
        if 'record_serializers' in options:
            serializers = options.get('record_serializers')
            serializers = {mime: obj_or_import_string(func)
                           for mime, func in serializers.items()}
        else:
            serializers = {}

        if 'search_serializers' in options:
            serializers = options.get('search_serializers')
            search_serializers = {mime: obj_or_import_string(func)
                                  for mime, func in serializers.items()}
        else:
            search_serializers = {}

        record_class = obj_or_import_string(options.get('record_class'),
                                            default=Record)
        search_class = obj_or_import_string(options.get('search_class'))
        search_factory = obj_or_import_string(
            options.get('search_factory_imp'))

        search_class_kwargs = {}
        search_class_kwargs['index'] = options.get('search_index')
        search_class_kwargs['doc_type'] = options.get('search_type')
        search_class = partial(search_class, **search_class_kwargs)

        ctx = dict(
            read_permission_factory=obj_or_import_string(
                options.get('read_permission_factory_imp')
            ),
            create_permission_factory=obj_or_import_string(
                options.get('create_permission_factory_imp')
            ),
            update_permission_factory=obj_or_import_string(
                options.get('update_permission_factory_imp')
            ),
            delete_permission_factory=obj_or_import_string(
                options.get('delete_permission_factory_imp')
            ),
            record_class=record_class,
            search_class=search_class,
            record_loaders=obj_or_import_string(
                options.get('record_loaders'),
                default=app.config['RECORDS_REST_DEFAULT_LOADERS']
            ),
            search_factory=search_factory,
            links_factory=obj_or_import_string(
                options.get('links_factory_imp'), default=default_links_factory
            ),
            pid_type=options.get('pid_type'),
            pid_minter=options.get('pid_minter'),
            pid_fetcher=options.get('pid_fetcher'),
            loaders={
                options.get('default_media_type'): lambda: request.get_json()},
            max_result_window=options.get('max_result_window'),
        )

        isr = IndexSearchResource.as_view(
            IndexSearchResource.view_name.format(endpoint),
            ctx=ctx,
            search_serializers=search_serializers,
            record_serializers=serializers,
            default_media_type=options.get('default_media_type'),
        )

        blueprint.add_url_rule(
            options.pop('index_route'),
            view_func=isr,
            methods=['GET', 'POST'],
        )

    return blueprint


class IndexSearchResource(ContentNegotiatedMethodView):
    """
     Index aggs Seach API
    """
    view_name = '{0}_index'

    def __init__(self, ctx, search_serializers=None,
                 record_serializers=None,
                 default_media_type=None, **kwargs):
        """Constructor."""
        super(IndexSearchResource, self).__init__(
            method_serializers={
                'GET': search_serializers,
                'POST': record_serializers,
            },
            default_method_media_type={
                'GET': default_media_type,
                'POST': default_media_type,
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

        page = request.values.get('page', 1, type=int)
        size = request.values.get('size', 20, type=int)

        current_app.logger.debug(page)
        current_app.logger.debug(size)

        if page * size >= self.max_result_window:
            raise MaxResultWindowRESTError()
        urlkwargs = dict()
        search_obj = self.search_class()
        search = search_obj.with_preference_param().params(version=True)
        search = search[(page - 1) * size:page * size]
        search, qs_kwargs = self.search_factory(self, search)

        urlkwargs.update(qs_kwargs)
        # Execute search
        search_result = search.execute()
        # Generate links for prev/next
        urlkwargs.update(
            size=size,
            _external=True,
        )
        # endpoint = '.{0}_index'.format(
        #     current_records_rest.default_endpoint_prefixes[self.pid_type])

        links = dict(self=url_for('weko_search_rest.recid_index', page=page,
                                  **urlkwargs))
        if page > 1:
            links['prev'] = url_for('weko_search_rest.recid_index',
                                    page=page - 1, **urlkwargs)
        if size * page < search_result.hits.total and \
                size * page < self.max_result_window:
            links['next'] = url_for('weko_search_rest.recid_index',
                                    page=page + 1, **urlkwargs)
        # aggs result identify
        rd = search_result.to_dict()
        q = request.values.get('q')
        lang = current_i18n.language

        if q:
            try:
                paths = Indexes.get_self_list(q)
            except BaseException:
                paths = []
            agp = rd["aggregations"]["path"]["buckets"]
            nlst = []

            for p in paths:
                m = 0
                for k in range(len(agp)):
                    if p.path == agp[k].get("key"):
                        agp[k]["name"] = p.name if lang == "ja" else p.name_en
                        date_range = agp[k].pop("date_range")
                        no_available = agp[k].pop("no_available")
                        pub = dict()
                        bkt = date_range['available']['buckets']
                        if bkt:
                            for d in bkt:
                                pub["pub_cnt" if d.get("to") else "un_pub_cnt"] = d.get(
                                    "doc_count")
                            pub["un_pub_cnt"] += no_available['doc_count']
                            agp[k]["date_range"] = pub
                            nlst.append(agp.pop(k))
                            m = 1
                        break
                if m == 0:
                    nd = {'doc_count': 0, 'key': p.path, 'name': p.name if lang == "ja" else p.name_en,
                          'date_range': {'pub_cnt': 0, 'un_pub_cnt': 0}}
                    nlst.append(nd)
            agp.clear()
            # process index tree image info
            if len(nlst):
                index_id = nlst[0].get('key')
                index_id = index_id if '/' not in index_id \
                    else index_id.split('/').pop()
                index_info = Indexes.get_index(index_id=index_id)
                if index_info.display_format == '2' \
                    and len(index_info.image_name) > 0:
                    nlst[0]['img'] = index_info.image_name
            agp.append(nlst)
        return self.make_response(
            pid_fetcher=self.pid_fetcher,
            search_result=rd,
            links=links,
            item_links_factory=self.links_factory,
        )

