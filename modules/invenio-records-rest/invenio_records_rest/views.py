# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""REST API resources."""

from __future__ import absolute_import, print_function

import pickle
import inspect
import traceback
import uuid
from collections import defaultdict
from functools import partial, wraps

from elasticsearch import VERSION as ES_VERSION
from elasticsearch.exceptions import RequestError
from flask import Blueprint, abort, current_app, jsonify, make_response, \
    request, url_for
from flask.views import MethodView
from flask_babelex import gettext as _
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_pidstore import current_pidstore
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.api import Record
from invenio_rest import ContentNegotiatedMethodView
from invenio_rest.decorators import require_content_types
from invenio_search import RecordsSearch
from jsonpatch import JsonPatchException, JsonPointerException
from jsonschema.exceptions import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from ._compat import wrap_links_factory
from .errors import InvalidDataRESTError, InvalidQueryRESTError, \
    JSONSchemaValidationError, MaxResultWindowRESTError, \
    PatchJSONFailureRESTError, PIDResolveRESTError, \
    SuggestMissingContextRESTError, SuggestNoCompletionsRESTError, \
    UnhandledElasticsearchError, UnsupportedMediaRESTError
from .links import default_links_factory
from .proxies import current_records_rest
from .query import es_search_factory
from .utils import obj_or_import_string

import json
import os
import sys
import math

from flask_security import current_user
from flask import session
from invenio_accounts.models import User
from weko_redis.redis import RedisConnection

from .config import RECORDS_REST_DEFAULT_TTL_VALUE

def elasticsearch_query_parsing_exception_handler(error):
    """Handle query parsing exceptions from ElasticSearch."""
    description = _('The syntax of the search query is invalid.')
    return InvalidQueryRESTError(description=description).get_response()


def create_error_handlers(blueprint, error_handlers_registry=None):
    """Create error handlers on blueprint.

    :params blueprint: Records API blueprint.
    :params error_handlers_registry: Configuration of error handlers per
        exception or HTTP status code and view name.

        The dictionary has the following structure:

        .. code-block:: python

            {
                SomeExceptionClass: {
                    'recid_list': 'path.to.error_handler_function_foo',
                    'recid_item': 'path.to.error_handler_function_foo',
                },
                410: {
                    'custom_pid_list': 'path.to.error_handler_function_bar',
                    'custom_pid_item': 'path.to.error_handler_function_bar',
                    'recid_item': 'path.to.error_handler_function_baz',
                    'recid_list': 'path.to.error_handler_function_baz',
                },
            }
    :returns: Configured blueprint.
    """
    error_handlers_registry = error_handlers_registry or {}

    # Catch record validation errors
    @blueprint.errorhandler(ValidationError)
    def validation_error(error):
        """Catch validation errors."""
        return JSONSchemaValidationError(error=error).get_response()

    @blueprint.errorhandler(RequestError)
    def elasticsearch_badrequest_error(error):
        """Catch errors of ElasticSearch."""
        handlers = current_app.config[
            'RECORDS_REST_ELASTICSEARCH_ERROR_HANDLERS']
        cause_types = {c['type'] for c in error.info['error']['root_cause']}

        for cause_type, handler in handlers.items():
            if cause_type in cause_types:
                return handler(error)

        # Default exception for unhandled errors
        exception = UnhandledElasticsearchError()
        current_app.logger.exception(error)  # Log the original stacktrace
        return exception.get_response()

    for exc_or_code, handlers in error_handlers_registry.items():
        # Build full endpoint names and resolve handlers
        handlers = {
            '.'.join([blueprint.name, view_name]): obj_or_import_string(func)
            for view_name, func in handlers.items()
        }

        def dispatch_handler(error):
            def default_handler(e):
                raise e
            return handlers.get(request.endpoint, default_handler)(error)
        blueprint.register_error_handler(exc_or_code, dispatch_handler)

    return blueprint


def create_blueprint_from_app(app):
    """Create Invenio-Records-REST blueprint from a Flask application.

    .. note::

        This function assumes that the application has loaded all extensions
        that want to register REST endpoints via the ``RECORDS_REST_ENDPOINTS``
        configuration variable.

    :params app: A Flask application.
    :returns: Configured blueprint.
    """
    return create_blueprint(app.config.get('RECORDS_REST_ENDPOINTS'))


def create_blueprint(endpoints):
    """Create Invenio-Records-REST blueprint.

    :params endpoints: Dictionary representing the endpoints configuration.
    :returns: Configured blueprint.
    """
    endpoints = endpoints or {}

    blueprint = Blueprint(
        'invenio_records_rest',
        __name__,
        url_prefix='',
    )
    
    @blueprint.teardown_request
    def dbsession_clean(exception):
        current_app.logger.debug("invenio_records_rest dbsession_clean: {}".format(exception))
        if exception is None:
            try:
                db.session.commit()
            except:
                db.session.rollback()
        db.session.remove()

    error_handlers_registry = defaultdict(dict)
    for endpoint, options in endpoints.items():
        error_handlers = options.pop('error_handlers', {})
        for rule in create_url_rules(endpoint, **options):
            for exc_or_code, handler in error_handlers.items():
                view_name = rule['view_func'].__name__
                error_handlers_registry[exc_or_code][view_name] = handler
            blueprint.add_url_rule(**rule)

    return create_error_handlers(blueprint, error_handlers_registry)


def create_url_rules(endpoint, list_route=None, item_route=None,
                     pid_type=None, pid_minter=None, pid_fetcher=None,
                     read_permission_factory_imp=None,
                     create_permission_factory_imp=None,
                     update_permission_factory_imp=None,
                     delete_permission_factory_imp=None,
                     list_permission_factory_imp=None,
                     record_class=None,
                     record_serializers=None,
                     record_serializers_aliases=None,
                     record_loaders=None,
                     search_class=None,
                     indexer_class=RecordIndexer,
                     search_serializers=None,
                     search_index=None, search_type=None,
                     default_media_type=None,
                     max_result_window=None, use_options_view=True,
                     search_factory_imp=None, links_factory_imp=None,
                     suggesters=None, default_endpoint_prefix=None):
    """Create Werkzeug URL rules.

    :param endpoint: Name of endpoint.
    :param list_route: Record listing URL route. Required.
    :param item_route: Record URL route (must include ``<pid_value>`` pattern).
        Required.
    :param pid_type: Persistent identifier type for endpoint. Required.
    :param pid_minter: It identifies the registered minter name.
    :param pid_fetcher: It identifies the registered fetcher name.
    :param read_permission_factory_imp: Import path to factory that creates a
        read permission object for a given record.
    :param create_permission_factory_imp: Import path to factory that creates a
        create permission object for a given record.
    :param update_permission_factory_imp: Import path to factory that creates a
        update permission object for a given record.
    :param delete_permission_factory_imp: Import path to factory that creates a
        delete permission object for a given record.
    :param list_permission_factory_imp: Import path to factory that
        creates a list permission object for a given index/list.
    :param default_endpoint_prefix: ignored.
    :param record_class: A record API class or importable string used when
        creating new records.
    :param record_serializers: Serializers used for records.
    :param record_serializers_aliases: A mapping of query arg `format` values
        to valid mimetypes: dict(alias -> mimetype).
    :param record_loaders: It contains the list of record deserializers for
        supperted formats.
    :param search_class: Import path or class object for the object in charge
        of execute the search queries. The default search class is
        :class:`invenio_search.api.RecordsSearch`.
        For more information about resource loading, see the Search of
        ElasticSearch DSL library.
    :param indexer_class: Import path or class object for the object in charge
        of indexing records. The default indexer is
        :class:`invenio_indexer.api.RecordIndexer`.
    :param search_serializers: Serializers used for search results.
    :param search_index: Name of the search index used when searching records.
    :param search_type: Name of the search type used when searching records.
    :param default_media_type: Default media type for both records and search.
    :param max_result_window: Maximum number of results that Elasticsearch can
        provide for the given search index without use of scroll. This value
        should correspond to Elasticsearch ``index.max_result_window`` value
        for the index.
    :param use_options_view: Determines if a special option view should be
        installed.
    :param search_factory_imp: Factory to parse quieries.
    :param links_factory_imp: Factory for record links generation.
    :param suggesters: Suggester fields configuration.

    :returns: a list of dictionaries with can each be passed as keywords
        arguments to ``Blueprint.add_url_rule``.
    """
    assert list_route
    assert item_route
    assert pid_type
    assert search_serializers
    assert record_serializers

    read_permission_factory = obj_or_import_string(
        read_permission_factory_imp
    )
    create_permission_factory = obj_or_import_string(
        create_permission_factory_imp
    )
    update_permission_factory = obj_or_import_string(
        update_permission_factory_imp
    )
    delete_permission_factory = obj_or_import_string(
        delete_permission_factory_imp
    )
    list_permission_factory = obj_or_import_string(
        list_permission_factory_imp
    )
    links_factory = obj_or_import_string(
        links_factory_imp, default=default_links_factory
    )
    # For backward compatibility. Previous signature was links_factory(pid).
    if wrap_links_factory(links_factory):
        orig_links_factory = links_factory

        def links_factory(pid, record=None, **kwargs):
            return orig_links_factory(pid)

    record_class = obj_or_import_string(
        record_class, default=Record
    )
    search_class = obj_or_import_string(
        search_class, default=RecordsSearch
    )

    indexer_class = obj_or_import_string(
        indexer_class, default=None
    )

    search_class_kwargs = {}
    if search_index:
        search_class_kwargs['index'] = search_index
    else:
        search_index = search_class.Meta.index

    if search_type:
        search_class_kwargs['doc_type'] = search_type
    else:
        search_type = search_class.Meta.doc_types

    if search_class_kwargs:
        search_class = partial(search_class, **search_class_kwargs)

    if record_loaders:
        record_loaders = {mime: obj_or_import_string(func)
                          for mime, func in record_loaders.items()}
    record_serializers = {mime: obj_or_import_string(func)
                          for mime, func in record_serializers.items()}
    search_serializers = {mime: obj_or_import_string(func)
                          for mime, func in search_serializers.items()}

    list_view = RecordsListResource.as_view(
        RecordsListResource.view_name.format(endpoint),
        minter_name=pid_minter,
        pid_type=pid_type,
        pid_fetcher=pid_fetcher,
        read_permission_factory=read_permission_factory,
        create_permission_factory=create_permission_factory,
        list_permission_factory=list_permission_factory,
        record_serializers=record_serializers,
        record_loaders=record_loaders,
        search_serializers=search_serializers,
        search_class=search_class,
        indexer_class=indexer_class,
        default_media_type=default_media_type,
        max_result_window=max_result_window,
        search_factory=(obj_or_import_string(
            search_factory_imp, default=es_search_factory
        )),
        item_links_factory=links_factory,
        record_class=record_class,
    )
    item_view = RecordResource.as_view(
        RecordResource.view_name.format(endpoint),
        read_permission_factory=read_permission_factory,
        update_permission_factory=update_permission_factory,
        delete_permission_factory=delete_permission_factory,
        serializers=record_serializers,
        serializers_query_aliases=record_serializers_aliases,
        loaders=record_loaders,
        search_class=search_class,
        indexer_class=indexer_class,
        links_factory=links_factory,
        default_media_type=default_media_type)

    views = [
        dict(rule=list_route, view_func=list_view),
        dict(rule=item_route, view_func=item_view),
    ]
    if suggesters:
        suggest_view = SuggestResource.as_view(
            SuggestResource.view_name.format(endpoint),
            suggesters=suggesters,
            search_class=search_class,
        )

        views.append(dict(
            rule=list_route + '_suggest',
            view_func=suggest_view
        ))

    if use_options_view:
        options_view = RecordsListOptionsResource.as_view(
            RecordsListOptionsResource.view_name.format(endpoint),
            search_index=search_index,
            max_result_window=max_result_window,
            default_media_type=default_media_type,
            search_media_types=search_serializers.keys(),
            item_media_types=record_serializers.keys(),
        )
        return [
            dict(rule="{0}_options".format(list_route),
                 view_func=options_view)
        ] + views
    return views


def pass_record(f):
    """Decorator to retrieve persistent identifier and record.

    This decorator will resolve the ``pid_value`` parameter from the route
    pattern and resolve it to a PID and a record, which are then available in
    the decorated function as ``pid`` and ``record`` kwargs respectively.
    """
    @wraps(f)
    def inner(self, pid_value, *args, **kwargs):
        try:
            pid, record = request.view_args['pid_value'].data
            return f(self, pid=pid, record=record, *args, **kwargs)
        except SQLAlchemyError as ex:
            current_app.logger.error('sqlalchemy error: ', ex)
            raise PIDResolveRESTError(pid)

    return inner


def verify_record_permission(permission_factory, record):
    """Check that the current user has the required permissions on record.

    In case the permission check fails, an Flask abort is launched.
    If the user was previously logged-in, a HTTP error 403 is returned.
    Otherwise, is returned a HTTP error 401.

    :param permission_factory: permission factory used to check permissions.
    :param record: record whose access is limited.
    """
    # Note, cannot be done in one line due overloading of boolean
    # operations permission object.
    if not permission_factory(record=record).can():
        from flask_login import current_user
        if not current_user.is_authenticated:
            abort(401)
        abort(403)
        from weko_records_ui.permissions import check_publish_status,check_created_id
        from weko_index_tree.utils import get_user_roles
        is_admin = False
        is_owner = False
        roles = get_user_roles()
        current_app.logger.error("roles :{}".format(roles))
        if roles[0]:
            is_admin = True
        if check_created_id(record):
            is_owner = True
        is_public = check_publish_status(record)
        if not is_public and not is_admin and not is_owner:
                abort(403)


def need_record_permission(factory_name):
    """Decorator checking that the user has the required permissions on record.

    :param factory_name: name of the permission factory.
    """
    def need_record_permission_builder(f):
        @wraps(f)
        def need_record_permission_decorator(self, record=None, *args,
                                             **kwargs):
            permission_factory = (
                getattr(self, factory_name)
                or getattr(current_records_rest, factory_name)
            )

            # FIXME use context instead
            request._methodview = self

            if permission_factory and record:
                verify_record_permission(permission_factory, record)
            return f(self, record=record, *args, **kwargs)
        return need_record_permission_decorator
    return need_record_permission_builder


class RecordsListOptionsResource(MethodView):
    """Resource for displaying options about records list/item views."""

    view_name = '{0}_list_options'

    def __init__(self, search_index=None, max_result_window=None,
                 default_media_type=None, search_media_types=None,
                 item_media_types=None):
        """Initialize method view."""
        self.search_index = search_index
        self.max_result_window = max_result_window or 10000
        self.default_media_type = default_media_type
        self.item_media_types = item_media_types
        self.search_media_types = search_media_types

    def get(self):
        """Get options."""
        opts = current_app.config['RECORDS_REST_SORT_OPTIONS'].get(
            self.search_index)

        sort_fields = []
        if opts:
            for key, item in sorted(opts.items(), key=lambda x: x[1]['order']):
                sort_fields.append(
                    {key: dict(
                        title=item['title'],
                        default_order=item.get('default_order', 'asc'))}
                )

        return jsonify(dict(
            sort_fields=sort_fields,
            max_result_window=self.max_result_window,
            default_media_type=self.default_media_type,
            search_media_types=sorted(self.search_media_types),
            item_media_types=sorted(self.item_media_types),
        ))


class RecordsListResource(ContentNegotiatedMethodView):
    """Resource for records listing."""

    view_name = '{0}_list'

    def __init__(self, minter_name=None, pid_type=None,
                 pid_fetcher=None, read_permission_factory=None,
                 create_permission_factory=None,
                 list_permission_factory=None,
                 search_class=None,
                 record_serializers=None,
                 record_loaders=None,
                 search_serializers=None, default_media_type=None,
                 max_result_window=None, search_factory=None,
                 item_links_factory=None, record_class=None,
                 indexer_class=None, **kwargs):
        """Constructor."""
        super(RecordsListResource, self).__init__(
            method_serializers={
                'GET': search_serializers,
                'POST': record_serializers,
            },
            default_method_media_type={
                'GET': default_media_type,
                'POST': default_media_type,
            },
            default_media_type=default_media_type,
            **kwargs)
        self.pid_type = pid_type
        self.minter = current_pidstore.minters[minter_name]
        self.pid_fetcher = current_pidstore.fetchers[pid_fetcher]
        self.read_permission_factory = read_permission_factory
        self.create_permission_factory = create_permission_factory or \
            current_records_rest.create_permission_factory
        self.list_permission_factory = list_permission_factory or \
            current_records_rest.list_permission_factory
        self.search_class = search_class
        self.max_result_window = max_result_window or 10000
        self.search_factory = partial(search_factory, self)
        self.item_links_factory = item_links_factory
        self.loaders = record_loaders or \
            current_records_rest.loaders
        self.record_class = record_class or Record
        self.indexer_class = indexer_class

    @need_record_permission('list_permission_factory')
    def get(self, **kwargs):
        """Search records.

        Permissions: the `list_permission_factory` permissions are
            checked.

        :returns: Search result containing hits and aggregations as
                  returned by invenio-search.
        """
        # default_results_size = current_app.config.get(
        #     'RECORDS_REST_DEFAULT_RESULTS_SIZE', 10)
        # page_no is parameters for Opensearch
        page = request.values.get('page',
                                  request.values.get('page_no', 1, type=int),
                                  type=int)
        # list_view_num is parameters for Opensearch
        size = request.values.get('size',
                                  request.values.get(
                                      'list_view_num', 10, type=int),
                                  type=int)

        # if page * size >= self.max_result_window:
        #     raise MaxResultWindowRESTError()

        # Arguments that must be added in prev/next links
        urlkwargs = dict()
        search_obj = self.search_class()
        search = search_obj.with_preference_param().params(version=True)

        # this line of code will process the query string and as a result
        # will put the correct "total" and "hits" into the search variable
        search, qs_kwargs = self.search_factory(search)

        from flask_security import current_user
        from flask import session
        from invenio_accounts.models import User

        query = request.values.get('q')

        # Search_after trigger
        use_search_after = False

        def get_item_sort_value(search_result):
            return list(search_result["hits"]["hits"][-1]["sort"])
        
        def set_sort_value(sort_condition, sort_value):
            
            sort_fields = [list(condition.keys())[0] for condition in sort_condition]
            new_data = {}
            for i, field in enumerate(sort_fields):
                sort_field = ""
                if field == "_script":
                    target_script = sort_condition[i][field].get("script") \
                        if isinstance(sort_condition[i][field].get("script"),str) else sort_condition[i][field].get("script",{}).get("source","")
                    if "control_number" in target_script:
                        sort_field = "control_number"
                    if "date_range" in target_script:
                        sort_field = "date_range"
                else:
                    sort_field=field
                new_data[sort_field] = sort_value[i]

            return new_data
        
        def get_new_search_after(_page, search_after_size, cache_data, search_query, last_sort_value, first_page_over_max_results, sort_condition):
            
            conn_num = ""
            # The first page whose page*size is greater than max_result_window
            page_list = []
            is_error = False
            for cached_page in cache_data.keys():
                try:
                    page_list.append(int(cached_page))
                except ValueError:
                    # This exception is for excluding non numerical values
                    current_app.logger.error(f"{cached_page}: {e}")
                    current_app.logger.error(traceback.format_exc())
                    pass
                except:
                    current_app.logger.error('An error occurred besides the possibly expected KeyError')
                    current_app.logger.error(traceback.format_exc())
            sorted_page_list = sorted(page_list)
            if _page in sorted_page_list and cache_data.get(str(_page),{}):
                next_items_sort_value = list(cache_data.get(str(_page),{}).values())
            else:
                try:
                    if _page == first_page_over_max_results:
                        next_items_sort_value = last_sort_value
                    else:
                        if (_page-1) in sorted_page_list and cache_data.get(str(_page-1)):
                            conn_num = list(cache_data.get(str(_page-1),{}).values())
                            next_search_after_set = search_query
                            next_search_after_set._extra.update(search_after_size)
                            next_search_after_set._extra.update({"search_after": conn_num})
                            next_items_sort_value = get_item_sort_value(next_search_after_set.execute(ignore_cache=True))
                        else:
                            prev_page_last_control_number = (size*(page-1)-size*math.floor(self.max_result_window/size))
                            num_per_max = prev_page_last_control_number//self.max_result_window
                            target_index=prev_page_last_control_number%self.max_result_window
                            if target_index==0:
                                target_index=self.max_result_window
                            else:
                                num_per_max+=1

                            max_size_sort_value, max_cache_data = get_max_result_sort_value(num_per_max, search, sort_condition)
                            next_search_after_set = search_query
                            next_search_after_set._extra.update({"size": target_index})
                            next_search_after_set._extra.update({"search_after": max_size_sort_value})
                            next_items_sort_value = get_item_sort_value(next_search_after_set.execute(ignore_cache=True))
                except Exception as e:
                    current_app.logger.error(traceback.format_exc())
                    next_items_sort_value = last_sort_value
                    is_error = True

            if is_error != True and str(_page) not in cache_data:
                cache_data[str(_page)] = set_sort_value(sort_condition, next_items_sort_value)
            return next_items_sort_value, cache_data

        def get_max_result_sort_value(max_size_key, search, sort_condition, max_cache_data=None):
            """Get search_after used to search max_size_key*max_result_window ~ (max_size_key+1)*max_result_window"""
            max_size_cache_name = f"{cache_name}_max_result"
            if max_cache_data is None:
                max_cache_data = json.loads(sessionstorage.get(max_size_cache_name)) \
                    if sessionstorage.redis.exists(max_size_cache_name) else {}
            if max_cache_data.get(str(max_size_key)):
                new_sort_value = list(max_cache_data.get(str(max_size_key),{}).values())
            else:
                last_sort_value, max_cache_data = get_max_result_sort_value(max_size_key-1, search, sort_condition, max_cache_data=max_cache_data)

                max_result_search = search
                max_result_search._extra.update({"size": self.max_result_window})
                max_result_search._extra.update({"search_after": last_sort_value})
                new_sort_value = get_item_sort_value(max_result_search.execute(ignore_cache=True))
                max_cache_data[str(max_size_key)] = set_sort_value(sort_condition, new_sort_value)
                sessionstorage.put(
                    max_size_cache_name,
                    json.dumps(max_cache_data).encode('utf-8'),
                    ttl_secs=current_app.config.get(
                        'RECORDS_REST_DEFAULT_TTL_VALUE',
                        RECORDS_REST_DEFAULT_TTL_VALUE
                    )
                )

            return new_sort_value, max_cache_data


        # Sort key being used in the query
        relevance_sort_is_used = False
        try:
            sort_element = search.to_dict()["sort"]
        except KeyError:
            # Since "relevance" sort type has no "sort" key, it will produce a "KeyError"
            # This exception is for when sort type "relevance" is used
            sort_element = "control_number"
            relevance_sort_is_used = True
        
        if relevance_sort_is_used:
            sort_key = sort_element
        else:
            sort_key = list(sort_element[0].keys())[0]

        # Cache Storage
        redis_connection = RedisConnection()
        sessionstorage = redis_connection.connection(db=current_app.config['ACCOUNTS_SESSION_REDIS_DB_NO'], kv = True)

        # For saving current user to session storage for seach_after use as cache name
        if current_user.is_authenticated:
            cache_name = User.query.get(current_user.id).email
        else:
            cache_name = "anonymous_user"
        
        # For saving a specific page for search_after use as cache key
        cache_key = str(page)

        # For checking search results option changes and resetting cache upon option change
        def url_args_check():
            if sessionstorage.redis.exists(f"{cache_name}_url_args"):
                cache_name_url_args = json.loads(sessionstorage.get(f"{cache_name}_url_args"))
                q_check = cache_name_url_args.get("q") != request.args.to_dict().get("q")
                sort_check = cache_name_url_args.get("sort") != request.args.to_dict().get("sort")
                size_check = cache_name_url_args.get("size") != request.args.to_dict().get("size")

                if (q_check or sort_check) or size_check:
                    sessionstorage.delete(cache_name)
                    sessionstorage.delete(f"{cache_name}_url_args")
                    sessionstorage.delete(f"{cache_name}_max_result")
                    json_data = json.dumps(request.args.to_dict()).encode('utf-8')
                    sessionstorage.put(
                        f"{cache_name}_url_args",
                        json_data,
                        ttl_secs=current_app.config.get(
                            'RECORDS_REST_DEFAULT_TTL_VALUE',
                            RECORDS_REST_DEFAULT_TTL_VALUE
                        )
                    )
            else:
                if sessionstorage.redis.exists(cache_name):
                    sessionstorage.delete(cache_name)
                if sessionstorage.redis.exists(f"{cache_name}_max_result"):
                    sessionstorage.delete(f"{cache_name}_max_result")
                json_data = json.dumps(request.args.to_dict()).encode('utf-8')
                sessionstorage.put(
                    f"{cache_name}_url_args",
                    json_data,
                    ttl_secs=current_app.config.get(
                        'RECORDS_REST_DEFAULT_TTL_VALUE',
                        RECORDS_REST_DEFAULT_TTL_VALUE
                    )
                )
        
        url_args_check()
        next_items_sort_value = []
        if page * size > self.max_result_window:
            if "sort" not in search.to_dict():
                from .sorter import eval_field
                search_index=search._index[0]
                control_number_sort_option = current_app.config['RECORDS_REST_SORT_OPTIONS'].get(search_index,{}).get('controlnumber')
                if control_number_sort_option is not None:
                    search._extra.update({"sort": [
                        eval_field(
                            control_number_sort_option['fields'][0],'asc',control_number_sort_option.get('nested')
                        )
                    ]})
            page_value = size*((math.floor(self.max_result_window/size)+1)-1)
            start_value=page_value-1
            end_value=page_value
            search_after_start_value = search[start_value:end_value]
            search_after_start_value = search_after_start_value.execute()
            last_sort_value = get_item_sort_value(search_after_start_value)
            
            sort_condition=search.to_dict().get("sort")

            #sort_fields = [list(condition.keys())[0] for condition in sort_condition]
            
            if not sessionstorage.redis.exists(f"{cache_name}_max_result"):
                sessionstorage.put(
                    f"{cache_name}_max_result",
                    json.dumps({"1": set_sort_value(sort_condition, last_sort_value)}).encode('utf-8'),
                    ttl_secs=current_app.config.get(
                        'RECORDS_REST_DEFAULT_TTL_VALUE',
                        RECORDS_REST_DEFAULT_TTL_VALUE
                    )
                )

            # Size for search. Dynamically changes depending on the size selected on the search results page
            search_after_size = {"size": size}

            next_items_sort_value = None

            if sessionstorage.redis.exists(cache_name):
                cache_data = json.loads(sessionstorage.get(cache_name))
            else:
                cache_data = {}
            first_page_over_max_results = math.floor(self.max_result_window/size)+1

            next_items_sort_value, cache_data = get_new_search_after(page, search_after_size, cache_data, search, last_sort_value, first_page_over_max_results, sort_condition)
            json_data = json.dumps(cache_data).encode('utf-8')
            sessionstorage.put(
                cache_name,
                json_data,
                ttl_secs=current_app.config.get(
                    'RECORDS_REST_DEFAULT_TTL_VALUE',
                    RECORDS_REST_DEFAULT_TTL_VALUE
                )
            )

            if sessionstorage.redis.exists(cache_name):
                if json.loads(sessionstorage.get(cache_name)).get(cache_key):
                    next_items_search_after = {"search_after": list(json.loads(sessionstorage.get(cache_name)).get(cache_key).values())}
                else:
                    next_items_search_after = {"search_after": next_items_sort_value}
            else:
                next_items_search_after = {"search_after": next_items_sort_value}
            search._extra.update(search_after_size)
            search._extra.update(next_items_search_after)

            # Search after trigger set to true
            use_search_after = True

        if use_search_after:
            search = search[0:size]
        else:
            search = search[(page - 1) * size:page * size]
            use_search_after = False

        if query:
            urlkwargs['q'] = query

        # Execute search
        search_result = search.execute()

        if not sessionstorage.redis.exists(cache_name) and size * math.floor(self.max_result_window/size) <= self.max_result_window:
            json_data = json.dumps({cache_key: next_items_sort_value}).encode('utf-8')
            sessionstorage.put(
                cache_name,
                json_data,
                ttl_secs=current_app.config.get(
                    'RECORDS_REST_DEFAULT_TTL_VALUE',
                    RECORDS_REST_DEFAULT_TTL_VALUE
                )
            )

        # Generate links for prev/next
        urlkwargs.update(
            size=size,
            _external=True,
        )
        endpoint = '.{0}_list'.format(
            current_records_rest.default_endpoint_prefixes[self.pid_type])
        links = dict(self=url_for(endpoint, page=page, **urlkwargs))
        if page > 1:
            links['prev'] = url_for(endpoint, page=page - 1, **urlkwargs)
        if size * page < search_result.hits.total and \
                size * page < self.max_result_window:
            links['next'] = url_for(endpoint, page=page + 1, **urlkwargs)
        from weko_search_ui.utils import combine_aggs
        search_result = combine_aggs(search_result.to_dict())
        return self.make_response(
            pid_fetcher=self.pid_fetcher,
            search_result=search_result,
            links=links,
            item_links_factory=self.item_links_factory,
        )

    @need_record_permission('create_permission_factory')
    def post(self, **kwargs):
        """Create a record.

        Permissions: ``create_permission_factory``

        Procedure description:

        #. First of all, the `create_permission_factory` permissions are
            checked.

        #. Then, the record is deserialized by the proper loader.

        #. A second call to the `create_permission_factory` factory is done:
            it differs from the previous call because this time the record is
            passed as parameter.

        #. A `uuid` is generated for the record and the minter is called.

        #. The record class is called to create the record.

        #. The HTTP response is built with the help of the item link factory.

        :returns: The created record.
        """
        if request.mimetype not in self.loaders:
            raise UnsupportedMediaRESTError(request.mimetype)

        data = self.loaders[request.mimetype]()
        if data is None:
            raise InvalidDataRESTError()

        # Check permissions
        permission_factory = self.create_permission_factory
        if permission_factory:
            verify_record_permission(permission_factory, data)

        try:
            # Create uuid for record
            record_uuid = uuid.uuid4()
            # Create persistent identifier
            pid = self.minter(record_uuid, data=data)
            # Create record
            record = self.record_class.create(data, id_=record_uuid)

            db.session.commit()

            # Index the record
            if self.indexer_class:
                self.indexer_class().index(record)

            response = self.make_response(
                pid, record, 201, links_factory=self.item_links_factory)

            # Add location headers
            endpoint = '.{0}_item'.format(
                current_records_rest.default_endpoint_prefixes[pid.pid_type])
            location = url_for(endpoint, pid_value=pid.pid_value, _external=True)
            response.headers.extend(dict(location=location))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            response = self.make_response(None, None, 500)
        
        return response


class RecordResource(ContentNegotiatedMethodView):
    """Resource for record items."""

    view_name = '{0}_item'

    def __init__(self, read_permission_factory=None,
                 update_permission_factory=None,
                 delete_permission_factory=None, default_media_type=None,
                 links_factory=None,
                 loaders=None, search_class=None, indexer_class=None,
                 **kwargs):
        """Constructor."""
        super(RecordResource, self).__init__(
            method_serializers={
                'DELETE': {'*/*': lambda *args: make_response(*args), },
            },
            default_method_media_type={
                'GET': default_media_type,
                'PUT': default_media_type,
                'DELETE': '*/*',
                'PATCH': default_media_type,
            },
            default_media_type=default_media_type,
            **kwargs)
        self.search_class = search_class
        self.read_permission_factory = read_permission_factory
        self.update_permission_factory = update_permission_factory
        self.delete_permission_factory = delete_permission_factory
        self.links_factory = links_factory
        self.loaders = loaders or current_records_rest.loaders
        self.indexer_class = indexer_class

    @pass_record
    @need_record_permission('delete_permission_factory')
    def delete(self, pid, record, **kwargs):
        """Delete a record.

        Permissions: ``delete_permission_factory``

        Procedure description:

        #. The record is resolved reading the pid value from the url.

        #. The ETag is checked.

        #. The record is deleted.

        #. All PIDs are marked as DELETED.

        :param pid: Persistent identifier for record.
        :param record: Record object.
        """
        self.check_etag(str(record.model.version_id))

        try:
            record.delete()
            # mark all PIDs as DELETED
            all_pids = PersistentIdentifier.query.filter(
                PersistentIdentifier.object_type == pid.object_type,
                PersistentIdentifier.object_uuid == pid.object_uuid,
            ).all()
            for rec_pid in all_pids:
                if not rec_pid.is_deleted():
                    rec_pid.delete()
            db.session.commit()

            if self.indexer_class:
                self.indexer_class().delete(record)
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)

        return '', 204

    @pass_record
    @need_record_permission('read_permission_factory')
    def get(self, pid, record, **kwargs):
        """Get a record.

        Permissions: ``read_permission_factory``

        Procedure description:

        #. The record is resolved reading the pid value from the url.

        #. The ETag and If-Modifed-Since is checked.

        #. The HTTP response is built with the help of the link factory.

        :param pid: Persistent identifier for record.
        :param record: Record object.
        :returns: The requested record.
        """
        etag = str(record.revision_id)
        self.check_etag(str(record.revision_id))
        self.check_if_modified_since(record.updated, etag=etag)

        return self.make_response(
            pid, record, links_factory=self.links_factory
        )

    @require_content_types('application/json-patch+json')
    @pass_record
    @need_record_permission('update_permission_factory')
    def patch(self, pid, record, **kwargs):
        """Modify a record.

        Permissions: ``update_permission_factory``

        The data should be a JSON-patch, which will be applied to the record.
        Requires header ``Content-Type: application/json-patch+json``.

        Procedure description:

        #. The record is deserialized using the proper loader.

        #. The ETag is checked.

        #. The record is patched.

        #. The HTTP response is built with the help of the link factory.

        :param pid: Persistent identifier for record.
        :param record: Record object.
        :returns: The modified record.
        """
        data = self.loaders[request.mimetype]()
        if data is None:
            raise InvalidDataRESTError()

        self.check_etag(str(record.revision_id))
        try:
            try:
                record = record.patch(data)
            except (JsonPatchException, JsonPointerException):
                raise PatchJSONFailureRESTError()

            record.commit()
            db.session.commit()

            if self.indexer_class:
                self.indexer_class().index(record)
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)

        return self.make_response(
            pid, record, links_factory=self.links_factory)

    @pass_record
    @need_record_permission('update_permission_factory')
    def put(self, pid, record, **kwargs):
        """Replace a record.

        Permissions: ``update_permission_factory``

        The body should be a JSON object, which will fully replace the current
        record metadata.

        Procedure description:

        #. The ETag is checked.

        #. The record is updated by calling the record API `clear()`,
           `update()` and then `commit()`.

        #. The HTTP response is built with the help of the link factory.

        :param pid: Persistent identifier for record.
        :param record: Record object.
        :returns: The modified record.
        """
        if request.mimetype not in self.loaders:
            raise UnsupportedMediaRESTError(request.mimetype)

        data = self.loaders[request.mimetype]()
        if data is None:
            raise InvalidDataRESTError()

        self.check_etag(str(record.revision_id))

        try:
            current_app.logger.debug(type(record))
            role_ids = []
            can_edit_indexes = []
            if current_user and current_user.is_authenticated:
                for role in current_user.roles:
                    if role.name in current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER']:
                        role_ids = []
                        break
                    else:
                        role_ids.append(role.id)
            if role_ids:
                from invenio_communities.models import Community
                from weko_index_tree.api import Indexes

                comm_list = Community.query.filter(
                    Community.id_role.in_(role_ids)
                ).all()
                for comm in comm_list:
                    for index in Indexes.get_self_list(comm.root_node_id):
                        if index.cid not in can_edit_indexes:
                            can_edit_indexes.append(str(index.cid))
                path = record.get('path', [])
                data['index'] = list(set(list(set(path) - set(can_edit_indexes)) + data.get('index', [])))
            record.clear()
            record.update(data)
            record.commit()
            db.session.commit()

            if self.indexer_class:
                self.indexer_class().index(record)
        except BaseException as e:
            db.session.rollback()
            current_app.logger.error(traceback.format_exc())
            return self.make_response(None, None, 500)

        return self.make_response(
            pid, record, links_factory=self.links_factory)


class SuggestResource(MethodView):
    """Resource for records suggests."""

    view_name = '{0}_suggest'

    def __init__(self, suggesters, search_class=None, **kwargs):
        """Constructor."""
        self.suggesters = suggesters
        self.search_class = search_class

    def get(self, **kwargs):
        """Get suggestions."""
        completions = []
        size = request.values.get('size', type=int)

        for k in self.suggesters.keys():
            val = request.values.get(k)
            if val:
                # Get completion suggestions
                opts = pickle.loads(pickle.dumps(self.suggesters[k], -1))

                if 'context' in opts.get('completion', {}):
                    ctx_field = opts['completion']['context']
                    ctx_val = request.values.get(ctx_field)
                    if not ctx_val:
                        raise SuggestMissingContextRESTError
                    opts['completion']['context'] = {
                        ctx_field: ctx_val
                    }

                if size:
                    opts['completion']['size'] = size

                completions.append((k, val, opts))

        if not completions:
            raise SuggestNoCompletionsRESTError(
                ', '.join(sorted(self.suggesters.keys())))

        # Add completions
        s = self.search_class()
        for field, val, opts in completions:
            source = opts.pop('_source', None)
            if source is not None and ES_VERSION[0] >= 5:
                s = s.source(source).suggest(field, val, **opts)
            else:
                s = s.suggest(field, val, **opts)

        if ES_VERSION[0] == 2:
            # Execute search
            response = s.execute_suggest().to_dict()
            for field, _, _ in completions:
                for resp in response[field]:
                    for op in resp['options']:
                        if 'payload' in op:
                            op['_source'] = pickle.loads(pickle.dumps(op['payload'], -1))
        elif ES_VERSION[0] >= 5:
            response = s.execute().to_dict()['suggest']

        result = dict()
        for field, val, opts in completions:
            result[field] = response[field]

        return make_response(jsonify(result))