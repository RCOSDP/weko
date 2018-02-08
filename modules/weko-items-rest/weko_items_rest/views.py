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

"""REST API resources."""

import copy
import json
import uuid
import hashlib

from functools import partial, wraps

from elasticsearch.exceptions import RequestError
from flask import Blueprint, abort, current_app, jsonify, make_response, \
    request, url_for, Flask, flash
from flask.views import MethodView
from flask_babelex import gettext as _
from flask_babelex import Babel
from invenio_db import db
from invenio_pidstore import current_pidstore
from invenio_pidstore.models import PersistentIdentifier
from invenio_pidstore.resolver import Resolver
from invenio_records.api import Record
from invenio_rest import ContentNegotiatedMethodView
from invenio_rest.decorators import require_content_types
from invenio_search import RecordsSearch
from jsonpatch import JsonPatchException, JsonPointerException
from jsonschema.exceptions import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from .api import get_item
from .errors import InvalidDataRESTError, InvalidQueryRESTError, \
    JSONSchemaValidationError, MaxResultWindowRESTError, \
    PatchJSONFailureRESTError, PIDResolveRESTError, \
    SuggestMissingContextRESTError, SuggestNoCompletionsRESTError, \
    UnsupportedMediaRESTError, FileMaxSizeExceededError
from .links import default_links_factory
from .proxies import current_items_rest
from .query import es_search_factory
from .utils import obj_or_import_string


app = Flask(__name__)
babel = Babel(app)


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(['ja', 'ja_JP', 'en'])


def get_image_src(mimetype):
    """ Get image src by file type
    :param mimetype:
    :return src: dict
    """
    src = ""
    if "text/" in mimetype:
        src = "icon_16_txt.jpg"
    elif "doc" in mimetype or "docx" in mimetype:
        src = "icon_16_doc.jpg"
    elif "xls" in mimetype or "xlsx" in mimetype:
        src = "icon_16_xls.jpg"
    elif "ppt" in mimetype:
        src = "icon_16_ppt.jpg"
    elif "zip" in mimetype or "rar" in mimetype:
        src = "icon_16_txt.jpg"
    elif "audio/" in mimetype:
        src = "icon_16_music.jpg"
    elif "xml" in mimetype:
        src = "icon_16_xml.jpg"
    elif "image/" in mimetype:
        src = "icon_16_picture.jpg"
    elif "pdf" in mimetype:
        src = "icon_16_pdf.jpg"
    elif "video/" in mimetype:
        if "flv" in mimetype:
            src = "icon_16_flash.jpg"
        else:
            src = "icon_16_movie.jpg"
    else:
        src = "icon_16_others.jpg"

    return dict(image_src="/static/images/icon/" + src)

def elasticsearch_query_parsing_exception_handler(error):
    """
    Handle query parsing exceptions from ElasticSearch.

    :param error: Error info.
    :return: InvalidQueryRESTError.
    """
    description = _('The syntax of the search query is invalid.')
    return InvalidQueryRESTError(description=description).get_response()


def create_error_handlers(blueprint):
    """Create error handlers on blueprint.

    :param blueprint: Records API blueprint.
    :returns: Configured blueprint.
    """
    # Catch record validation errors
    @blueprint.errorhandler(ValidationError)
    def validation_error(error):
        """
        Catch validation errors.

        :param error: Error msg.
        :return: JSONSchemaValidationError.
        """
        return JSONSchemaValidationError(error=error).get_response()

    @blueprint.errorhandler(RequestError)
    def elasticsearch_badrequest_error(error):
        """
        Catch errors of ElasticSearch.

        :param error: Error msg.
        :return: Error result
        """
        handlers = current_app.config[
            'ITEMS_REST_ELASTICSEARCH_ERROR_HANDLERS']
        cause_types = {c['type'] for c in error.info['error']['root_cause']}

        for cause_type, handler in handlers.items():
            if cause_type in cause_types:
                return handler(error)
        return error

    return blueprint


def create_blueprint(endpoints):
    """Create Invenio-Records-REST blueprint.

    :param endpoints: Dictionary representing the endpoints configuration.
    :returns: Configured blueprint.
    """
    blueprint = Blueprint(
        'weko_items_rest',
        __name__,
        url_prefix='',
    )

    for endpoint, options in (endpoints or {}).items():
        for rule in create_url_rules(endpoint, **options):
            blueprint.add_url_rule(**rule)
    return create_error_handlers(blueprint)


def create_url_rules(endpoint, list_route=None, item_route=None,
                     file_route=None, file_put_route=None,
                     pid_type=None, pid_minter=None, pid_fetcher=None,
                     read_permission_factory_imp=None,
                     create_permission_factory_imp=None,
                     update_permission_factory_imp=None,
                     delete_permission_factory_imp=None,
                     record_class=None,
                     record_serializers=None,
                     record_serializers_aliases=None,
                     record_loaders=None,
                     search_class=None,
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
    :param default_endpoint_prefix: ignored.
    :param record_class: A record API class or importable string.
    :param record_serializers: Serializers used for records.
    :param record_serializers_aliases: A mapping of query arg `format` values
        to valid mimetypes: dict(alias -> mimetype).
    :param record_loaders: It contains the list of record deserializers for
        supperted formats.
    :param search_class: Import path or class object for the object in charge
        of execute the search queries. The default search class is
        class`invenio_search.api.RecordsSearch`.
        For more information about resource loading, see the Search of
        ElasticSearch DSL library.
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
    assert file_put_route
    assert item_route
    assert file_route
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
    links_factory = obj_or_import_string(
        links_factory_imp, default=default_links_factory
    )
    record_class = obj_or_import_string(
        record_class, default=Record
    )
    search_class = obj_or_import_string(
        search_class, default=RecordsSearch
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

    resolver = Resolver(pid_type=pid_type, object_type='rec',
                        getter=partial(record_class.get_record,
                                       with_deleted=True))

    file_put_view = FilePutResource.as_view(
        FilePutResource.view_name.format(endpoint),
        resolver=resolver,
        read_permission_factory=read_permission_factory,
        update_permission_factory=update_permission_factory,
        delete_permission_factory=delete_permission_factory,
        serializers=record_serializers,
        serializers_query_aliases=record_serializers_aliases,
        loaders=record_loaders,
        search_class=search_class,
        links_factory=links_factory,
        record_class=record_class,
        default_media_type=default_media_type)

    file_view = RecordsListResource.as_view(
        RecordsListResource.view_name.format(endpoint),
        resolver=resolver,
        minter_name=pid_minter,
        pid_type=pid_type,
        pid_fetcher=pid_fetcher,
        read_permission_factory=read_permission_factory,
        create_permission_factory=create_permission_factory,
        record_serializers=record_serializers,
        record_loaders=record_loaders,
        search_serializers=search_serializers,
        search_class=search_class,
        default_media_type=default_media_type,
        max_result_window=max_result_window,
        search_factory=(obj_or_import_string(
            search_factory_imp, default=es_search_factory
        )),
        item_links_factory=links_factory,
        record_class=record_class,
    )

    item_view = ItemsListResource.as_view(
        ItemsListResource.view_name.format(endpoint),
        resolver=resolver,
        minter_name=pid_minter,
        pid_type=pid_type,
        pid_fetcher=pid_fetcher,
        read_permission_factory=read_permission_factory,
        create_permission_factory=create_permission_factory,
        record_serializers=record_serializers,
        record_loaders=record_loaders,
        search_serializers=search_serializers,
        search_class=search_class,
        default_media_type=default_media_type,
        max_result_window=max_result_window,
        search_factory=(obj_or_import_string(
            search_factory_imp, default=es_search_factory
        )),
        item_links_factory=links_factory,
        record_class=record_class,
    )

    views = [
        dict(rule=item_route, view_func=item_view),
        dict(rule=file_route, view_func=file_view),
        dict(rule=file_put_route, view_func=file_put_view),
    ]

    return views


def pass_record(f):
    """Decorator to retrieve persistent identifier and record."""
    @wraps(f)
    def inner(self, pid_value, *args, **kwargs):
        """
        Parse request args.

        :param pid_value: pid_value
        :return: function running result
        """
        try:
            pid, record = request.view_args['pid_value'].data
            return f(self, pid=pid, record=record, *args, **kwargs)
        except SQLAlchemyError:
            raise PIDResolveRESTError(pid)

    return inner


def before_upload(f):
    @wraps(f)
    def file_maxsize(self, *args, **kwargs):
        size = len(request.data)
        maxsize = current_app.config['ITEMS_REST_FILE_MAXSIZE']
        if (maxsize > 0) and (size > maxsize):
            raise FileMaxSizeExceededError()
        return f(self, *args, **kwargs)
    return file_maxsize


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


def need_record_permission(factory_name):
    """Decorator checking that the user has the required permissions on record.

    :param factory_name: Name of the factory to retrieve.
    """
    def need_record_permission_builder(f):
        @wraps(f)
        def need_record_permission_decorator(self, record=None, *args,
                                             **kwargs):
            permission_factory = (
                getattr(self, factory_name) or
                getattr(current_items_rest, factory_name)
            )

            request._methodview = self

            if permission_factory:
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
        opts = current_app.config['ITEMS_REST_SORT_OPTIONS'].get(
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

    view_name = '{0}_file'

    def __init__(self, resolver=None, minter_name=None, pid_type=None,
                 pid_fetcher=None, read_permission_factory=None,
                 create_permission_factory=None, search_class=None,
                 record_serializers=None,
                 record_loaders=None,
                 search_serializers=None, default_media_type=None,
                 max_result_window=None, search_factory=None,
                 item_links_factory=None, record_class=None, **kwargs):
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
        self.resolver = resolver
        self.pid_type = pid_type
        self.minter = current_pidstore.minters[minter_name]
        self.pid_fetcher = current_pidstore.fetchers[pid_fetcher]
        self.read_permission_factory = read_permission_factory
        self.create_permission_factory = \
            create_permission_factory or \
            current_items_rest.create_permission_factory
        self.search_class = search_class
        self.max_result_window = max_result_window or 10000
        self.search_factory = partial(search_factory, self)
        self.item_links_factory = item_links_factory
        self.loaders = record_loaders or current_items_rest.loaders
        self.record_class = record_class or Record

    def get(self, **kwargs):
        """Search records.

        :returns: the search result containing hits and aggregations as
            returned by invenio-search.
        """
        page = request.values.get('page', 1, type=int)
        size = request.values.get('size', 10, type=int)
        if page * size >= self.max_result_window:
            raise MaxResultWindowRESTError()

        # Arguments that must be added in prev/next links
        urlkwargs = dict()
        search_obj = self.search_class()
        search = search_obj.with_preference_param().params(version=True)
        search = search[(page - 1) * size:page * size]

        search, qs_kwargs = self.search_factory(search)
        urlkwargs.update(qs_kwargs)

        # Execute search
        search_result = search.execute()

        # Generate links for prev/next
        urlkwargs.update(
            size=size,
            _external=True,
        )
        endpoint = '.{0}_list'.format(
            current_items_rest.default_endpoint_prefixes[self.pid_type])
        links = dict(self=url_for(endpoint, page=page, **urlkwargs))
        if page > 1:
            links['prev'] = url_for(endpoint, page=page - 1, **urlkwargs)
        if size * page < search_result.hits.total \
                and size * page < self.max_result_window:
            links['next'] = url_for(endpoint, page=page + 1, **urlkwargs)

        return self.make_response(
            pid_fetcher=self.pid_fetcher,
            search_result=search_result.to_dict(),
            links=links,
            item_links_factory=self.item_links_factory,
        )

    @need_record_permission('create_permission_factory')
    def post(self, **kwargs):
        """Create a record.

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
        record = self.record_class.create(data, pid=pid.pid_value)

        db.session.commit()

        response = self.make_response(
            pid, record, 201, links_factory=self.item_links_factory)

        # Add location headers
        endpoint = '.{0}_file'.format(
            current_items_rest.default_endpoint_prefixes['items'])
        location = url_for(endpoint, pid_value=pid.pid_value, _external=True)
        response.headers.extend(dict(location=location))
        return response


class RecordResource(ContentNegotiatedMethodView):
    """Resource for record items."""

    view_name = '{0}_item'

    def __init__(self, resolver=None, read_permission_factory=None,
                 update_permission_factory=None,
                 delete_permission_factory=None, default_media_type=None,
                 links_factory=None,
                 loaders=None, search_class=None,
                 **kwargs):
        """Constructor.

        :param resolver: Persistent identifier resolver instance.
        :param read_permission_factory: permission factory for read
        :param update_permission_factory: permission factory for update
        :param delete_permission_factory: permission factory for delete
        :param default_media_type: default media_type
        :param links_factory: links_factory
        :param loaders: loaders
        :param search_class: search_class
        """
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
        self.resolver = resolver
        self.search_class = search_class
        self.read_permission_factory = read_permission_factory
        self.update_permission_factory = update_permission_factory
        self.delete_permission_factory = delete_permission_factory
        self.links_factory = links_factory
        self.loaders = loaders or current_items_rest.loaders

    @pass_record
    @need_record_permission('delete_permission_factory')
    def delete(self, pid, record, **kwargs):
        """Delete a record.

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

        return '', 204

    @pass_record
    @need_record_permission('read_permission_factory')
    def get(self, pid, record, **kwargs):
        """Get a record.

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

        The data should be a JSON-patch, which will be applied to the record.

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

        return self.make_response(
            pid, record, links_factory=self.links_factory)

    # @pass_record
    @need_record_permission('update_permission_factory')
    def put(self, pid, record, **kwargs):
        """Replace a record.

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

        record.clear()
        record.update(data)
        record.commit()
        db.session.commit()
        return self.make_response(
            pid, record, links_factory=self.links_factory)


class FilePutResource(ContentNegotiatedMethodView):
    """Resource for record items."""

    view_name = '{0}_filePut'

    def __init__(self, resolver=None, read_permission_factory=None,
                 update_permission_factory=None,
                 delete_permission_factory=None, default_media_type=None,
                 links_factory=None,
                 loaders=None, search_class=None, record_class=None,
                 **kwargs):
        """Constructor.

        :param resolver: Persistent identifier resolver instance.
        :param read_permission_factory: permission factory for read
        :param update_permission_factory: permission factory for update
        :param delete_permission_factory: permission factory for delete
        :param default_media_type: default media_type
        :param links_factory: links_factory
        :param loaders: loaders
        :param search_class: search_class
        """
        super(FilePutResource, self).__init__(
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
        self.resolver = resolver
        self.search_class = search_class
        self.read_permission_factory = read_permission_factory
        self.update_permission_factory = update_permission_factory
        self.delete_permission_factory = delete_permission_factory
        self.links_factory = links_factory
        self.loaders = loaders or current_items_rest.loaders
        self.record_class = record_class or Record

    @pass_record
    @need_record_permission('delete_permission_factory')
    def delete(self, pid, record, **kwargs):
        """Delete a record.

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

        return '', 204

    @pass_record
    @need_record_permission('read_permission_factory')
    def get(self, pid, record, **kwargs):
        """Get a record.

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

        The data should be a JSON-patch, which will be applied to the record.

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

        return self.make_response(
            pid, record, links_factory=self.links_factory)

    @before_upload
    def put(self, **kwargs):
        """Replace a record.

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
        fn = request.view_args['key']
        pid = request.view_args['pid_value']
        size = len(request.data)

        #. TODO: hash

        sha256 = hashlib.sha256(request.data).hexdigest()

        if size > 0:
            url = request.host_url + current_app.config[
                'ITEMS_REST_FILE_DOWNLOAD_BASE_URL'].format(pid, fn)

            jsc = dict(display_name=fn)
            jsc.update(dict(file_name=url))
            jsc.update(dict(preview=url.replace("/files/", "/preview/")))
            jsc.update(dict(size=size))
            jsc.update(dict(checksum=sha256))
            jsc.update(dict(mimetype=request.mimetype))
            jsc.update(get_image_src(request.mimetype))

            # Create record
            record = self.record_class.create(data=jsc, con=request.data,
                                              pid=pid)
            db.session.commit()

        jd = {"key": fn, "mimetype": request.mimetype, "links": {},
              "size": size}
        data = dict(key=fn, mimetype='text/plain')
        response = current_app.response_class(json.dumps(jd),
                                              mimetype='application/json')
        response.status_code = 200
        return response


class ItemsListResource(ContentNegotiatedMethodView):
    """Resource for items listing."""

    view_name = '{0}_add'

    def __init__(self, resolver=None, minter_name=None, pid_type=None,
                 pid_fetcher=None, read_permission_factory=None,
                 create_permission_factory=None, search_class=None,
                 record_serializers=None,
                 record_loaders=None,
                 search_serializers=None, default_media_type=None,
                 max_result_window=None, search_factory=None,
                 item_links_factory=None, record_class=None, **kwargs):
        """Constructor."""
        super(ItemsListResource, self).__init__(
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
        self.resolver = resolver
        self.pid_type = pid_type
        self.minter = current_pidstore.minters[minter_name]
        self.pid_fetcher = current_pidstore.fetchers[pid_fetcher]
        self.read_permission_factory = read_permission_factory
        self.create_permission_factory = \
            create_permission_factory or \
            current_items_rest.create_permission_factory
        self.search_class = search_class
        self.max_result_window = max_result_window or 10000
        self.search_factory = partial(search_factory, self)
        self.item_links_factory = item_links_factory
        self.loaders = record_loaders or current_items_rest.loaders
        self.record_class = record_class or Record

    def get(self, **kwargs):
        """Search records.

        :returns: the search result containing hits and aggregations as
            returned by invenio-search.
        """
        page = request.values.get('page', 1, type=int)
        size = request.values.get('size', 10, type=int)
        if page * size >= self.max_result_window:
            raise MaxResultWindowRESTError()

        # Arguments that must be added in prev/next links
        urlkwargs = dict()
        search_obj = self.search_class()
        search = search_obj.with_preference_param().params(version=True)
        search = search[(page - 1) * size:page * size]

        search, qs_kwargs = self.search_factory(search)
        urlkwargs.update(qs_kwargs)

        # Execute search
        search_result = search.execute()

        # Generate links for prev/next
        urlkwargs.update(
            size=size,
            _external=True,
        )
        endpoint = '.{0}_add'.format(
            current_items_rest.default_endpoint_prefixes[self.pid_type])
        links = dict(self=url_for(endpoint, page=page, **urlkwargs))
        if page > 1:
            links['prev'] = url_for(endpoint, page=page - 1, **urlkwargs)
        if size * page < search_result.hits.total \
                and size * page < self.max_result_window:
            links['next'] = url_for(endpoint, page=page + 1, **urlkwargs)

        return self.make_response(
            pid_fetcher=self.pid_fetcher,
            search_result=search_result.to_dict(),
            links=links,
            item_links_factory=self.item_links_factory,
        )

    @need_record_permission('create_permission_factory')
    def post(self, **kwargs):
        """Create a record.

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

        get_item(data, request.view_args['pid_value'])

        return jsonify({'status': 'success'})


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
            val = request.values.get(k, type=str)
            if val:
                # Get completion suggestions
                opts = copy.deepcopy(self.suggesters[k])

                if 'context' in opts.get('completion', {}):
                    ctx_field = opts['completion']['context']
                    ctx_val = request.values.get(ctx_field, type=str)
                    if not ctx_val:
                        raise SuggestMissingContextRESTError
                        # raise SuggestMissingContextRESTError(ctx_field)
                    opts['completion']['context'] = {
                        ctx_field: ctx_val
                    }

                if size:
                    opts['completion']['size'] = size

                completions.append((k, val, opts))

        if not completions:
            # raise SuggestNoCompletionsRESTError
            raise SuggestNoCompletionsRESTError(
                ', '.join(sorted(self.suggesters.keys())))

        # Add completions
        s = self.search_class()
        for field, val, opts in completions:
            s = s.suggest(field, val, **opts)

        # Execute search
        response = s.execute_suggest().to_dict()

        result = dict()
        for field, val, opts in completions:
            result[field] = response[field]

        return make_response(jsonify(result))
