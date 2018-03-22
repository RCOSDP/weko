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

"""Blueprint for Weko deposit rest."""

import json, uuid, shutil
import os.path

# from copy import deepcopy
from functools import partial

from flask import Blueprint, abort, current_app, jsonify, request, \
    url_for, redirect
from invenio_db import db
from invenio_oauth2server import require_api_auth, require_oauth_scopes
from invenio_pidstore.errors import PIDInvalidAction
from invenio_pidstore import current_pidstore
from invenio_records_rest.utils import obj_or_import_string
from invenio_records_rest.links import default_links_factory
from invenio_records.api import Record
from invenio_records_rest.views import \
    create_error_handlers as records_rest_error_handlers
from invenio_records_rest.views import \
    create_url_rules
from invenio_records_rest.views import need_record_permission, pass_record
from invenio_rest import ContentNegotiatedMethodView
from invenio_rest.views import create_api_errorhandler
from webargs import fields
from webargs.flaskparser import use_kwargs
from werkzeug.utils import secure_filename
from invenio_records_rest.errors import InvalidDataRESTError, \
    UnsupportedMediaRESTError
from invenio_files_rest.storage import PyFSFileStorage
from invenio_records_rest.errors import MaxResultWindowRESTError
from weko_index_tree.api import Indexes


def create_blueprint(app, endpoints):
    """Create Invenio-Deposit-REST blueprint.

    See: :data:`invenio_deposit.config.DEPOSIT_REST_ENDPOINTS`.

    :param endpoints: List of endpoints configuration.
    :returns: The configured blueprint.
    """
    blueprint = Blueprint(
        'weko_deposit_rest',
        __name__,
        url_prefix='',
    )

    for endpoint, options in (endpoints or {}).items():

        if 'record_serializers' in options:
            record_serializers = options.get('record_serializers')
            record_serializers = {mime: obj_or_import_string(func)
                           for mime, func in record_serializers.items()}
        else:
            record_serializers = {}

        if 'search_serializers' in options:
            serializers = options.get('search_serializers')
            search_serializers = {mime: obj_or_import_string(func)
                                  for mime, func in serializers.items()}
        else:
            search_serializers = {}

        record_class = obj_or_import_string(options.get('record_class'),
                                            default=Record)
        # search_class = obj_or_import_string(options.get('search_class'))
        # search_factory = obj_or_import_string(options.get('search_factory_imp'))

        search_class_kwargs = {}
        search_class_kwargs['index'] = options.get('search_index')
        search_class_kwargs['doc_type'] = options.get('search_type')
        # search_class = partial(search_class, **search_class_kwargs)

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
            # search_class=search_class,
            # record_loaders=obj_or_import_string(
            #     options.get('record_loaders'),
            #     default=app.config['RECORDS_REST_DEFAULT_LOADERS']
            # ),
            # search_factory=search_factory,
            links_factory=obj_or_import_string(
                options.get('links_factory_imp'), default=default_links_factory
            ),
            pid_type=options.get('pid_type'),
            pid_minter=options.get('pid_minter'),
            pid_fetcher=options.get('pid_fetcher'),
            loaders={
                options.get('default_media_type'): lambda: request.get_json()},
            # max_result_window=options.get('max_result_window'),
        )

        isr = ItemResource.as_view(
            ItemResource.view_name.format(endpoint),
            ctx=ctx,
            # search_serializers=search_serializers,
            record_serializers=record_serializers,
            default_media_type=options.get('default_media_type'),
        )

        blueprint.add_url_rule(
            options.pop('rdc_rout'),
            view_func=isr,
            methods=['PUT', 'POST'],
        )

    return blueprint


class ItemResource(ContentNegotiatedMethodView):
    """redirect to next page(index select) """
    view_name = '{0}_item'

    def __init__(self, ctx, search_serializers=None,
                 record_serializers=None,
                 default_media_type=None, **kwargs):
        """Constructor."""
        super(ItemResource, self).__init__(
            method_serializers={
                # 'GET': search_serializers,
                'PUT': record_serializers,
                'POST': record_serializers,
            },
            default_method_media_type={
                # 'GET': default_media_type,
                'PUT': default_media_type,
                'POST': default_media_type,
            },
            default_media_type=default_media_type,
            **kwargs
        )
        for key, value in ctx.items():
            setattr(self, key, value)

        self.pid_fetcher = current_pidstore.fetchers[self.pid_fetcher]

    @pass_record
    def post(self, pid, record, **kwargs):
        """"""
        from weko_deposit.links import base_factory
        response = self.make_response(pid, record, 201, links_factory=base_factory)

        return response

    def put(self, **kwargs):
        """"""
        try:
            data = request.get_json()
            pid = kwargs.get('pid_value').value

            # item metadata cached on Redis by pid
            import redis
            from simplekv.memory.redisstore import RedisStore
            datastore = RedisStore(redis.StrictRedis.from_url(
                current_app.config['CACHE_REDIS_URL']))
            cache_key = current_app.config[
                'WEKO_DEPOSIT_ITEMS_CACHE_PREFIX'].format(pid_value=pid)
            ttl_sec = int(current_app.config['WEKO_DEPOSIT_ITEMS_CACHE_TTL'])
            datastore.put(cache_key, json.dumps(data), ttl_secs=ttl_sec)
        except:
            abort(400, "Failed to register item")

        return jsonify({'status': 'success'})
