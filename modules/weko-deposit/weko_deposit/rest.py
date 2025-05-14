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

import json
import sys
from wsgiref.util import request_uri

import redis
from redis import sentinel
from elasticsearch import ElasticsearchException
from flask import Blueprint, abort, current_app, jsonify, request
from invenio_db import db
from invenio_pidstore import current_pidstore
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.api import Record
from invenio_records.models import RecordMetadata
from invenio_records_rest.links import default_links_factory
from invenio_records_rest.utils import obj_or_import_string
from invenio_records_rest.views import pass_record
from invenio_rest import ContentNegotiatedMethodView
from simplekv.memory.redisstore import RedisStore
from sqlalchemy.exc import SQLAlchemyError
from weko_redis.redis import RedisConnection

from .api import WekoDeposit, WekoRecord

# from copy import deepcopy


def publish(**kwargs):
    """Publish item."""
    try:
        pid_value = kwargs.get('pid_value').value
        pid = PersistentIdentifier.query.filter_by(
            pid_type='recid', pid_value=pid_value).first()
        r = RecordMetadata.query.filter_by(id=pid.object_uuid).first()
        dep = WekoDeposit(r.json, r)
        dep.publish()
    except BaseException:
        abort(400, "Failed to publish item")

    return jsonify({'status': 'success'})


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
    
    @blueprint.teardown_request
    def dbsession_clean(exception):
        current_app.logger.debug("weko_deposit dbsession_clean: {}".format(exception))
        if exception is None:
            try:
                db.session.commit()
            except:
                db.session.rollback()
        db.session.remove()

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
        # search_factory = obj_or_import_string(options.get(
        # 'search_factory_imp'))

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
            options.pop('rdc_route'),
            view_func=isr,
            methods=['PUT', 'POST'],
        )

        blueprint.add_url_rule(
            options.pop('pub_route'),
            view_func=publish,
            methods=['PUT'],
        )
    
    return blueprint


class ItemResource(ContentNegotiatedMethodView):
    """Redirect to next page(index select)."""

    view_name = '{0}_item'

    def __init__(self, ctx, search_serializers=None,
                 record_serializers=None,
                 default_media_type=None,
                 **kwargs):
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
        current_app.logger.debug('kwargs: {0}'.format(kwargs))
        for key, value in ctx.items():
            setattr(self, key, value)

        self.pid_fetcher = current_pidstore.fetchers[self.pid_fetcher]

    @pass_record
    def post(self, pid, record, **kwargs):
        """Post."""
        from weko_deposit.links import base_factory
        return self.make_response(pid,
                                  record,
                                  201,
                                  links_factory=base_factory)

    def put(self, **kwargs):
        """Put."""
        from weko_workflow.api import WorkActivity
        try:
            data = request.get_json()
            self.__sanitize_input_data(data)
            pid_value = kwargs.get('pid_value').value
            edit_mode = data.get('edit_mode')

            if edit_mode and edit_mode == 'upgrade':
                data.pop('edit_mode')
                cur_pid = PersistentIdentifier.get('recid', pid_value)
                pid = PersistentIdentifier.get(
                    'recid', pid_value.split(".")[0])
                deposit = WekoDeposit.get_record(pid.object_uuid)

                upgrade_record = deposit.newversion(pid)

                with db.session.begin_nested():

                    if upgrade_record and ".0" in pid_value:
                        _upgrade_record = WekoDeposit(
                            upgrade_record,
                            upgrade_record.model)
                        _upgrade_record.merge_data_to_record_without_version(
                            cur_pid)
                    activity = WorkActivity()
                    wf_activity = activity.get_workflow_activity_by_item_id(
                        cur_pid.object_uuid)
                    if wf_activity:
                        wf_activity.item_id = upgrade_record.model.id
                        db.session.merge(wf_activity)
                db.session.commit()
                pid = PersistentIdentifier.query.filter_by(
                    pid_type='recid',
                    object_uuid=upgrade_record.model.id).one_or_none()
                pid_value = pid.pid_value if pid else pid_value

                # create item link info of upgrade record from parent record
                weko_record = WekoRecord.get_record_by_pid(
                    upgrade_record.pid.pid_value)
                if weko_record:
                    weko_record.update_item_link(pid_value.split(".")[0])

            # Saving ItemMetadata cached on Redis by pid
            redis_connection = RedisConnection()
            datastore = redis_connection.connection(db=current_app.config['CACHE_REDIS_DB'], kv = True)
            cache_key = current_app.config[
                'WEKO_DEPOSIT_ITEMS_CACHE_PREFIX'].format(pid_value=pid_value)
            ttl_sec = int(current_app.config['WEKO_DEPOSIT_ITEMS_CACHE_TTL'])
            datastore.put(
                cache_key,
                json.dumps(data).encode('utf-8'),
                ttl_secs=ttl_sec)
        except SQLAlchemyError as ex:
            current_app.logger.error('sqlalchemy error: %s', ex)
            db.session.rollback()
            abort(400, "Failed to register item!")

        except ElasticsearchException as ex:
            current_app.logger.error('elasticsearch error: %s', ex)
            db.session.rollback()

            # elasticseacrh remove
            # dammy()

            abort(400, "Failed to register item!")
        except redis.RedisError as ex:
            current_app.logger.error('redis error: %s', ex)
            db.session.rollback()

            # elasticseacrh remove
            # dammy()

            abort(400, "Failed to register item!")
        except BaseException as ex:
            current_app.logger.error('Unexpected error: %s', ex)
            db.session.rollback()
            abort(400, "Failed to register item!")

        return jsonify({'status': 'success'})

    @staticmethod
    def __sanitize_string(s: str):
        """Sanitize string.

        :param s:
        :return:
        """
        s = s.strip()
        sanitize_str = ""
        for i in s:
            if ord(i) in [9, 10, 13] or (31 < ord(i) != 127):
                sanitize_str += i
        return sanitize_str

    def __sanitize_input_data(self, data):
        """Sanitize input data.

        :param data: input data.
        """
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, str):
                    data[k] = self.__sanitize_string(v)
                else:
                    self.__sanitize_input_data(v)
        elif isinstance(data, list):
            for i in range(len(data)):
                if isinstance(data[i], str):
                    data[i] = self.__sanitize_string(data[i])
                else:
                    self.__sanitize_input_data(data[i])
