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
    request, url_for, redirect
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

import orjson
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

def redirect_to_search(page, size):
    """ Redirects to search page with the same query string
    Args:
        page (int): page number
        size (int): size of the page
    Returns:
        response: redirect response
    """
    url = request.host_url + "search?search_type=0&q="
    if page:
        url += "&page=" + str(page)
    if size:
        url += "&size=" + str(size)
    get_args = request.args.to_dict()
    for key, param in get_args.items():
        if key == "page_no" or key == "list_view_num" \
            or key == "log_term" or key == "lang":
            continue
        url += "&" + key + "=" + param
    response = make_response(redirect(url))
    response.status_code = 302
    return response

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
        size = RecordsListResource.adjust_list_view_num(size)
        formats = request.values.getlist('format')
        selected_format = None
        if formats:
            if 'html' in formats:
                selected_format = 'html'
            else:
                selected_format = formats[0]
        else:
            selected_format = None

        if (not selected_format or selected_format == "html") and request.values.get('q') is None:
            return redirect_to_search(page, size)

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

        def get_item_control_number(search_result):
            return search_result["hits"]["hits"][-1]["_source"]["control_number"]

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
            sort_key_arrangement = "desc"
        else:
            sort_key = list(sort_element[0].keys())[0]
            sort_key_arrangement = sort_element[0][sort_key]["order"]

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
                cache_name_url_args = orjson.loads(sessionstorage.get(f"{cache_name}_url_args"))
                q_check = cache_name_url_args.get("q") != request.args.to_dict().get("q")
                sort_check = cache_name_url_args.get("sort") != request.args.to_dict().get("sort")
                size_check = cache_name_url_args.get("size") != request.args.to_dict().get("size")

                if (q_check or sort_check) or size_check:
                    sessionstorage.delete(cache_name)
                    sessionstorage.delete(f"{cache_name}_url_args")
                    json_data = orjson.dumps(request.args.to_dict())
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
                json_data = orjson.dumps(request.args.to_dict())
                sessionstorage.put(
                    f"{cache_name}_url_args",
                    json_data,
                    ttl_secs=current_app.config.get(
                        'RECORDS_REST_DEFAULT_TTL_VALUE',
                        RECORDS_REST_DEFAULT_TTL_VALUE
                    )
                )
        
        url_args_check()

        next_items_sort_value = ""

        if page * size > self.max_result_window:
            start_value = int(self.max_result_window) - 1
            end_value = int(self.max_result_window)
            search_after_start_value = search[start_value:end_value]
            search_after_start_value = search_after_start_value.execute()
            last_sort_value = get_item_control_number(search_after_start_value)

            # Sort to be used for search_after regardless of the selected sort type on the search results page
            search._extra.update({"sort": [{"control_number": {"order": f"{sort_key_arrangement}"}}]})

            # Size for search. Dynamically changes depending on the size selected on the search results page
            search_after_size = {"size": size}

            next_items_sort_value = None

            if sessionstorage.redis.exists(cache_name):
                if orjson.loads(sessionstorage.get(cache_name)).get(cache_key):
                    cache_name_checker = orjson.loads(sessionstorage.get(cache_name)).get(cache_key)
                else:
                    cache_name_checker = None
            else:
                cache_name_checker = None

            if sessionstorage.redis.exists(cache_name):
                if cache_name_checker:
                    page_list = []
                    cache_name_stored_data = orjson.loads(sessionstorage.get(cache_name))
                    for cached_page in cache_name_stored_data.keys():
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

                    next_search_after_set = search
                    next_search_after_set._extra.update(search_after_size)
                    next_search_after_set._extra.update({"search_after": [orjson.loads(sessionstorage.get(cache_name)).get(cache_key).get("control_number")]})
                    next_items_sort_value = next_search_after_set.execute()["hits"]["hits"][-1]["_source"]["control_number"]
                    
                else:
                    page_list = []
                    cache_name_stored_data = orjson.loads(sessionstorage.get(cache_name))
                    for cached_page in cache_name_stored_data.keys():
                        try:
                            page_list.append(int(cached_page))
                        except KeyError:
                            # This exception is to filter not numerical values
                            current_app.logger.error(f"{cached_page}: {e}")
                            current_app.logger.error(traceback.format_exc())
                            pass
                        except:
                            current_app.logger.error('An error occurred besides the possibly expected KeyError')
                            current_app.logger.error(traceback.format_exc())
                    sorted_page_list = sorted(page_list)

                    if ((page - 1) == sorted_page_list[-1] or page > sorted_page_list[-1]) and page * size > self.max_result_window:
                        cache_data = cache_name_stored_data.get(str(int(cache_key) - 1))
                        next_search_after_set = search
                        next_search_after_set._extra.update(search_after_size)
                        next_search_after_set._extra.update({"search_after": [orjson.loads(sessionstorage.get(cache_name)).get(str(sorted_page_list[-1])).get("control_number")]})
                        
                        try:
                            if cache_data.get("control_number") is None:
                                next_items_sort_value = last_sort_value
                            else:
                                next_items_sort_value = get_item_control_number(next_search_after_set.execute())
                        except Exception as err:
                            """
                            Possible known error:
                            1) elasticsearch.exceptions.RequestError: TransportError(400, 'parsing_exception', 'Expected [VALUE_STRING] or [VALUE_NUMBER] or [VALUE_BOOLEAN] or [VALUE_NULL] but found [START_ARRAY] inside search_after.')
                            2) elasticsearch.exceptions.TransportError: TransportError(500, 'search_phase_execution_exception', 'Cannot invoke "java.lang.Long.longValue()" because "value" is null')
                            """
                            current_app.logger.error('*** If search_after runs properly ignore this error')
                            current_app.logger.error(traceback.format_exc())

                            try:
                                next_items_sort_value = get_item_control_number(next_search_after_set.execute())
                            except Exception as e:
                                # This exception is for getting value of the 10,000th element
                                current_app.logger.error('*** If search_after runs properly ignore this error')
                                current_app.logger.error(traceback.format_exc())
                                next_items_sort_value = last_sort_value

                        next_search_after_set = None
                        cache_name_stored_data[cache_key] = {"control_number": next_items_sort_value}

                        json_data = orjson.dumps(cache_name_stored_data)
                        sessionstorage.put(
                            cache_name,
                            json_data,
                            ttl_secs=current_app.config.get(
                                'RECORDS_REST_DEFAULT_TTL_VALUE',
                                RECORDS_REST_DEFAULT_TTL_VALUE
                            )
                        )
                    else:
                        next_items_sort_value = last_sort_value
            else:
                next_items_sort_value = last_sort_value

            if sessionstorage.redis.exists(cache_name):
                if orjson.loads(sessionstorage.get(cache_name)).get(cache_key):
                    next_items_search_after = {"search_after": [orjson.loads(sessionstorage.get(cache_name)).get(cache_key).get("control_number")]}
                else:
                    next_items_search_after = {"search_after": [next_items_sort_value]}
            else:
                next_items_search_after = {"search_after": [next_items_sort_value]}

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
            json_data = orjson.dumps({cache_key: {"control_number": [next_items_sort_value]}})
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

        return self.make_response(
            pid_fetcher=self.pid_fetcher,
            search_result=search_result.to_dict(),
            links=links,
            item_links_factory=self.item_links_factory,
        )


    @classmethod
    def adjust_list_view_num(cls, size: int) -> int:
        """adjust parameter 'list_view_num'

        Args:
            size (int): request parameter size

        Returns:
            int: adjusted size (20, 50, 75, 100)
        """
        if size <= 20:
            return 20
        elif size > 20 and size <= 50:
            return 50
        elif size > 50 and size <= 75:
            return 75

        return 100


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
            record = record.patch(data)
        except (JsonPatchException, JsonPointerException):
            raise PatchJSONFailureRESTError()

        record.commit()
        db.session.commit()
        if self.indexer_class:
            self.indexer_class().index(record)

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
            record.clear()
            record.update(data)
            record.commit()
            db.session.commit()
        except BaseException as e:
            current_app.logger.error(traceback.format_exc())

        if self.indexer_class:
            self.indexer_class().index(record)
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