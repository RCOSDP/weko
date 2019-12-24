# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""General utility functions module."""

from functools import partial

import six
from flask import abort, current_app, jsonify, make_response, request, url_for
from invenio_pidstore.errors import PIDDeletedError, PIDDoesNotExistError, \
    PIDMissingObjectError, PIDRedirectedError, PIDUnregistered
from invenio_pidstore.resolver import Resolver
from invenio_records.api import Record
from werkzeug.routing import BaseConverter, BuildError, PathConverter
from werkzeug.utils import cached_property, import_string

from .errors import PIDDeletedRESTError, PIDDoesNotExistRESTError, \
    PIDMissingObjectRESTError, PIDRedirectedRESTError, \
    PIDUnregisteredRESTError
from .proxies import current_records_rest


def build_default_endpoint_prefixes(records_rest_endpoints):
    """Build the default_endpoint_prefixes map."""
    pid_types = set()
    guessed = set()
    endpoint_prefixes = {}

    for key, endpoint in records_rest_endpoints.items():
        pid_type = endpoint['pid_type']
        pid_types.add(pid_type)
        is_guessed = key == pid_type
        is_default = endpoint.get('default_endpoint_prefix', False)

        if is_default:
            if pid_type in endpoint_prefixes and pid_type not in guessed:
                raise ValueError('More than one "{0}" defined.'.format(
                    pid_type
                ))
            endpoint_prefixes[pid_type] = key
            guessed -= {pid_type}
        elif is_guessed and pid_type not in endpoint_prefixes:
            endpoint_prefixes[pid_type] = key
            guessed |= {pid_type}

    not_found = pid_types - set(endpoint_prefixes.keys())
    if not_found:
        raise ValueError('No endpoint-prefix for {0}.'.format(
            ', '.join(not_found)
        ))

    return endpoint_prefixes


def obj_or_import_string(value, default=None):
    """Import string or return object.

    :params value: Import path or class object to instantiate.
    :params default: Default object to return if the import fails.
    :returns: The imported object.
    """
    if isinstance(value, six.string_types):
        return import_string(value)
    elif value:
        return value
    return default


def load_or_import_from_config(key, app=None, default=None):
    """Load or import value from config.

    :returns: The loaded value.
    """
    app = app or current_app
    imp = app.config.get(key)
    return obj_or_import_string(imp, default=default)


def allow_all(*args, **kwargs):
    """Return permission that always allow an access.

    :returns: A object instance with a ``can()`` method.
    """
    return type('Allow', (), {'can': lambda self: True})()


def deny_all(*args, **kwargs):
    """Return permission that always deny an access.

    :returns: A object instance with a ``can()`` method.
    """
    return type('Deny', (), {'can': lambda self: False})()


def check_elasticsearch(record, *args, **kwargs):
    """Return permission that check if the record exists in ES index.

    :params record: A record object.
    :returns: A object instance with a ``can()`` method.
    """
    def can(self):
        """Try to search for given record."""
        search = request._methodview.search_class()
        search = search.get_record(str(record.id))
        return search.count() == 1

    return type('CheckES', (), {'can': can})()


class LazyPIDValue(object):
    """Lazy PID resolver.

    The PID will not be resolved until the `data` property is accessed.
    """

    def __init__(self, resolver, value):
        """Initialize with resolver object and the PID value.

        :params resolver: Resolves for PID,
                          see :class:`invenio_pidstore.resolver.Resolver`.
        :params value: PID value.
        :type value: str
        """
        self.resolver = resolver
        self.value = value

    @cached_property
    def data(self):
        """Resolve PID from a value and return a tuple with PID and the record.

        :returns: A tuple with the PID and the record resolved.
        """
        try:
            return self.resolver.resolve(self.value)
        except PIDDoesNotExistError as pid_error:
            raise PIDDoesNotExistRESTError(pid_error=pid_error)
        except PIDUnregistered as pid_error:
            raise PIDUnregisteredRESTError(pid_error=pid_error)
        except PIDDeletedError as pid_error:
            raise PIDDeletedRESTError(pid_error=pid_error)
        except PIDMissingObjectError as pid_error:
            current_app.logger.exception(
                'No object assigned to {0}.'.format(pid_error.pid),
                extra={'pid': pid_error.pid})
            raise PIDMissingObjectRESTError(pid_error.pid, pid_error=pid_error)
        except PIDRedirectedError as pid_error:
            try:
                location = url_for(
                    '.{0}_item'.format(
                        current_records_rest.default_endpoint_prefixes[
                            pid_error.destination_pid.pid_type]),
                    pid_value=pid_error.destination_pid.pid_value)
                data = dict(
                    status=301,
                    message='Moved Permanently',
                    location=location,
                )
                response = make_response(jsonify(data), data['status'])
                response.headers['Location'] = location
                abort(response)
            except (BuildError, KeyError):
                current_app.logger.exception(
                    'Invalid redirect - pid_type "{0}" '
                    'endpoint missing.'.format(
                        pid_error.destination_pid.pid_type),
                    extra={
                        'pid': pid_error.pid,
                        'destination_pid': pid_error.destination_pid,
                    })
                raise PIDRedirectedRESTError(
                    pid_error.destination_pid.pid_type, pid_error=pid_error)


class PIDConverter(BaseConverter):
    """Converter for PID values in the route mapping.

    This class is a custom routing converter defining the 'PID' type.
    See http://werkzeug.pocoo.org/docs/0.12/routing/#custom-converters.

    Use ``pid`` as a type in the route pattern, e.g.: the use of
    route decorator: ``@blueprint.route('/record/<pid(recid):pid_value>')``,
    will match and resolve a path: ``/record/123456``.
    """

    def __init__(self, url_map, pid_type, getter=None, record_class=None):
        """Initialize the converter."""
        super(PIDConverter, self).__init__(url_map)
        getter = obj_or_import_string(getter, default=partial(
            obj_or_import_string(record_class, default=Record).get_record,
            with_deleted=True
        ))
        self.resolver = Resolver(pid_type=pid_type, object_type='rec',
                                 getter=getter)

    def to_python(self, value):
        """Resolve PID value."""
        return LazyPIDValue(self.resolver, value)


class PIDPathConverter(PIDConverter, PathConverter):
    """PIDConverter with support for path-like (with slashes) PID values.

    This class is a custom routing converter defining the 'PID' type.
    See http://werkzeug.pocoo.org/docs/0.12/routing/#custom-converters.

    Use ``pidpath`` as a type in the route patter, e.g.: the use of a route
    decorator: ``@blueprint.route('/record/<pidpath(recid):pid_value>')``,
    will match and resolve a path containing a DOI: ``/record/10.1010/12345``.
    """
