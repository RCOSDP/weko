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
from wsgiref.util import request_uri

import redis
from redis import sentinel
from invenio_search.engine import search
from flask import Blueprint, abort, current_app, jsonify, request
from invenio_db import db
from invenio_pidstore import current_pidstore
from invenio_pidstore.models import PersistentIdentifier
from invenio_pidstore.errors import PIDDoesNotExistError, PIDInvalidAction
from invenio_records.api import Record
from invenio_records.models import RecordMetadata
from invenio_records_rest.links import default_links_factory
from invenio_records_rest.utils import obj_or_import_string
from invenio_records_rest.views import pass_record
from invenio_rest import ContentNegotiatedMethodView
from sqlalchemy.exc import SQLAlchemyError
from weko_records.errors import WekoRecordsError
from weko_redis.errors import WekoRedisError
from weko_redis.redis import RedisConnection
from weko_workflow.api import WorkActivity
from weko_workflow.errors import WekoWorkflowError

from .api import WekoDeposit, WekoRecord
from .errors import WekoDepositError
from .links import base_factory
from .logger import weko_logger

def publish(**kwargs):
    """Publish item.

    Publish the deposit.

    Args:
        **kwargs: Keyword arguments.<br>
            pid_value (str): Persistent Identifier value. Required.
    """
    try:
        pid_value = kwargs.get('pid_value').value
        pid = PersistentIdentifier.query.filter_by(
            pid_type='recid', pid_value=pid_value).first()
        r = RecordMetadata.query.filter_by(id=pid.object_uuid).first()
        dep = WekoDeposit(r.json, r)
        dep.update_feedback_mail()
        dep.publish()
    except SQLAlchemyError as ex:
        weko_logger(key='WEKO_COMMON_DB_SOME_ERROR', ex=ex)
        abort(400, "Some errors in the DB.")
    except Exception:
        abort(400, "Failed to publish item")

    return jsonify({'status': 'success'})


def create_blueprint(app, endpoints):
    """Create Invenio-Deposit-REST blueprint.

    See: :data:`invenio_deposit.config.DEPOSIT_REST_ENDPOINTS`.

    Args:
        app: The Flask application.
        endpoints (dict): List of endpoints configuration.

    Returns:
        The configured blueprint.
    """
    blueprint = Blueprint(
        'weko_deposit_rest',
        __name__,
        url_prefix='',
    )

    @blueprint.teardown_request
    def dbsession_clean(exception):
        """Clean up the database session.

        Clwan up the database session after each request.

        Args:
            exception (:obj:`Exception`): Exception object.
        """
        if exception is None:
            weko_logger(app=app, key='WEKO_COMMON_IF_ENTER', branch='exception is None')
            try:
                db.session.commit()
            except SQLAlchemyError as ex:
                weko_logger(app=app, key='WEKO_COMMON_DB_SOME_ERROR', ex=ex)
                db.session.rollback()
                raise WekoDepositError(ex=ex)
        weko_logger(app=app, key='WEKO_COMMON_ERROR_UNEXPECTED', ex=exception)
        db.session.remove()

    weko_logger(app=app, key='WEKO_COMMON_FOR_START')
    for i, (endpoint, options) in enumerate((endpoints or {}).items()):
        weko_logger(app=app, key='WEKO_COMMON_FOR_LOOP_ITERATION',
                    count=i, element=endpoint)

        if 'record_serializers' in options:
            weko_logger(app=app, key='WEKO_COMMON_IF_ENTER',
                        branch='record_serializers in options.')

            record_serializers = options.get('record_serializers')
            record_serializers = {mime: obj_or_import_string(func)
                                for mime, func in record_serializers.items()}
        else:
            weko_logger(app=app, key='WEKO_COMMON_IF_ENTER',
                        branch='record_serializers not in options.')

            record_serializers = {}

        if 'search_serializers' in options:
            weko_logger(app=app, key='WEKO_COMMON_IF_ENTER',
                        branch='search_serializers in options.')

            serializers = options.get('search_serializers')
            search_serializers = {mime: obj_or_import_string(func)
                                for mime, func in serializers.items()}
        else:
            weko_logger(app=app, key='WEKO_COMMON_IF_ENTER',
                        branch='search_serializers not in options.')

            search_serializers = {}

        record_class = obj_or_import_string(options.get('record_class'),
                                            default=Record)

        search_class_kwargs = {}
        search_class_kwargs['index'] = options.get('search_index')
        search_class_kwargs['doc_type'] = options.get('search_type')

        ctx = {
            "read_permission_factory": obj_or_import_string(
                options.get('read_permission_factory_imp')
            ),
            "create_permission_factory": obj_or_import_string(
                options.get('create_permission_factory_imp')
            ),
            "update_permission_factory": obj_or_import_string(
                options.get('update_permission_factory_imp')
            ),
            "delete_permission_factory": obj_or_import_string(
                options.get('delete_permission_factory_imp')
            ),
            "record_class": record_class,
            "links_factory": obj_or_import_string(
                options.get('links_factory_imp'), default=default_links_factory
            ),
            "pid_type": options.get('pid_type'),
            "pid_minter": options.get('pid_minter'),
            "pid_fetcher": options.get('pid_fetcher'),
            "loaders": {
                options.get('default_media_type'): lambda: request.get_json()
                }
        }

        isr = ItemResource.as_view(
            ItemResource.view_name.format(endpoint),
            ctx=ctx,
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

    weko_logger(app=app, key='WEKO_COMMON_FOR_END')
    weko_logger(app=app, key='WEKO_COMMON_RETURN_VALUE', value=blueprint)
    return blueprint


class ItemResource(ContentNegotiatedMethodView):
    """Redirect to next page(index select).

    Attributes:
        pid_fetcher (str): Persistent Identifier fetcher.
    """

    view_name = '{0}_item'

    def __init__(self, ctx, search_serializers=None,
                 record_serializers=None,
                 default_media_type=None,
                 **kwargs):
        """Constructor.

        Initialize the ItemResource.

        Args:
            ctx (dict): Context object.
            search_serializers: Search serializers.\
                A mapping of HTTP method name. Default to `None`.\
                Not used.
            record_serializers: Record serializers. \
                A mapping of HTTP method name. Default to `None`.
            default_media_type: Default media type.
            **kwargs: Keyword arguments
        """

        super().__init__(
            method_serializers={
                'PUT': record_serializers,
                'POST': record_serializers,
            },
            default_method_media_type={
                'PUT': default_media_type,
                'POST': default_media_type,
            },
            default_media_type=default_media_type,
            **kwargs
        )
        weko_logger(key='WEKO_COMMON_CALLED_KW_ARGUMENT', kwarg=kwargs)

        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, (key, value) in enumerate(ctx.items()):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=key)
            setattr(self, key, value)
        weko_logger(key='WEKO_COMMON_FOR_END')

        self.pid_fetcher = current_pidstore.fetchers[self.pid_fetcher]

    @pass_record
    def post(self, pid, record, **kwargs):
        """Post the record.

        This method is used to create a new record in the system.

        Args:
            pid (:obj:`PersistentIdentifier`):\
                Persistent Identifier instance associated with the record.
            record (Objct): The record object to be created.
            **kwargs: Keyword arguments. Not used.

        Returns:
            Response: Response object containing the result of the operation.
        """
        result = self.make_response(pid,
                                  record,
                                  201,
                                  links_factory=base_factory)
        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=result)
        return result

    def put(self, **kwargs):
        """Put the record.

        Put the record to Postgres DB, Elasticsearch, and Redis.
        If failed, rollback the transaction and abort 400.

        Args:
            **kwargs: Keyword arguments.
                pid_value (str): Persistent Identifier value. Required.

        """
        try:
            data = request.get_json()
            self.__sanitize_input_data(data)
            pid_value = kwargs.get('pid_value').value
            edit_mode = data.get('edit_mode')

            if edit_mode and edit_mode == 'upgrade':
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch='edit_mode == upgrade')

                data.pop('edit_mode')
                cur_pid = PersistentIdentifier.get('recid', pid_value)
                pid = PersistentIdentifier.get(
                    'recid', pid_value.split(".")[0])
                deposit = WekoDeposit.get_record(pid.object_uuid)

                upgrade_record = deposit.newversion(pid)

                with db.session.begin_nested():
                    if upgrade_record is not None and ".0" in pid_value:
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch="upgrade_record is not None "
                                        "and '.0' in pid_value")

                        _upgrade_record = WekoDeposit(
                            upgrade_record,
                            upgrade_record.model)
                        _upgrade_record.merge_data_to_record_without_version(
                            cur_pid)

                    activity = WorkActivity()
                    wf_activity = activity.get_workflow_activity_by_item_id(
                        cur_pid.object_uuid)
                    if wf_activity is not None:
                        weko_logger(key='WEKO_COMMON_IF_ENTER',
                                    branch='wf_activity is not None')

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
        except PIDDoesNotExistError as ex:
            weko_logger(key='WEKO_COMMON_NOT_FOUND_OBJECT', object=pid_value)
            db.session.rollback()
            abort(400, "Not Found PID in DB.")
        except PIDInvalidAction as ex:
            weko_logger(key='WEKO_COMMON_DB_OTHER_ERROR', ex=ex)
            db.session.rollback()
            abort(400, "Invalid operation on PID.")
        except WekoRecordsError as ex:
            db.session.rollback()
            abort(400, "Not Found Record in DB.")
        except WekoRedisError as ex:
            db.session.rollback()
            abort(400, "Failed to register item!")
        except WekoWorkflowError as ex:
            db.session.rollback()
            abort(400, "Failed to get activity!")

        except SQLAlchemyError as ex:
            weko_logger(key='WEKO_COMMON_DB_SOME_ERROR', ex=ex)
            db.session.rollback()
            abort(400, "Failed to register item!")

        except search.OpenSearchException as ex:
            weko_logger(key='WEKO_COMMON_ERROR_ELASTICSEARCH', ex=ex)
            db.session.rollback()
            abort(400, "Failed to register item!")

        except redis.RedisError as ex:
            weko_logger(key='WEKO_COMMON_ERROR_REDIS', ex=ex)
            db.session.rollback()
            abort(400, "Failed to register item!")

        except Exception as ex:
            weko_logger(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=ex)
            db.session.rollback()
            abort(400, "Failed to register item!")

        return jsonify({'status': 'success'})

    @staticmethod
    def __sanitize_string(s):
        """Sanitize string.

        Get sanitized string validated by the following rules:
        - Remove leading and trailing whitespaces.
        - Remove control characters except for tab, line feed, and carriage\
        return.

        Args:
            s (str): String.

        Returns:
            str: Sanitized string.
        """
        s = s.strip()
        sanitize_str = ""

        weko_logger(key='WEKO_COMMON_FOR_START')
        for i, c in enumerate(s):
            weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                        count=i, element=c)
            if ord(c) in [9, 10, 13] or (31 < ord(c) != 127):
                weko_logger(key='WEKO_COMMON_IF_ENTER',
                            branch=f"charcter:{c} is valid")
                sanitize_str += c
        weko_logger(key='WEKO_COMMON_FOR_END')

        weko_logger(key='WEKO_COMMON_RETURN_VALUE', value=sanitize_str)
        return sanitize_str

    def __sanitize_input_data(self, data):
        """Sanitize input data.

        Sanitize input data validated by the following rules:
        - Remove leading and trailing whitespaces.
        - Remove control characters except for tab, line feed, and carriage\
        return.

        Args:
            data (dict | list): input data to be sanitized.
        """
        if isinstance(data, dict):
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch="data is dict")

            weko_logger(key='WEKO_COMMON_FOR_START')
            for i, (k, v) in enumerate(data.items()):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=k)
                if isinstance(v, str):
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"{v} is str")
                    data[k] = self.__sanitize_string(v)
                else:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"{v} is not str")
                    self.__sanitize_input_data(v)
            weko_logger(key='WEKO_COMMON_FOR_END')

        elif isinstance(data, list):
            weko_logger(key='WEKO_COMMON_IF_ENTER',
                        branch='data is not dict')

            weko_logger(key='WEKO_COMMON_FOR_START')
            for i in range(len(data)):
                weko_logger(key='WEKO_COMMON_FOR_LOOP_ITERATION',
                            count=i, element=data[i])
                if isinstance(data[i], str):
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"{data[i]} is str")
                    data[i] = self.__sanitize_string(data[i])
                else:
                    weko_logger(key='WEKO_COMMON_IF_ENTER',
                                branch=f"{data[i]} is not str")
                    self.__sanitize_input_data(data[i])
            weko_logger(key='WEKO_COMMON_FOR_END')
