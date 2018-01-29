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

"""Implementention of various utility functions."""

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
from .proxies import current_items_rest


def build_default_endpoint_prefixes(records_rest_endpoints):
    """Build the default_endpoint_prefixes map.

    :param records_rest_endpoints: endpoints config info
    """
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

    :param value: Import path or class object to instantiate.
    :param default: Default object to return if the import fails.
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

    :param record: A record object.
    :returns: A object instance with a ``can()`` method.
    """
    def can(self):
        """Try to search for given record."""
        search = request._methodview.search_class()
        search = search.get_record(str(record.id))
        return search.count() == 1

    return type('CheckES', (), {'can': can})()


class LazyPIDValue(object):
    """Lazy resolver for PID value."""

    def __init__(self, resolver, value):
        """Initialize with resolver and URL value.

        :param resolver: Used to resolve PID value and return a record.
        :param value: PID value.
        """
        self.resolver = resolver
        self.value = value

    @cached_property
    def data(self):
        """Resolve PID value and return tuple with PID and record.

        :returns: A tuple with the PID and the record resolved.
        """
        try:
            return self.resolver.resolve(self.value)
        except PIDDoesNotExistError:
            raise PIDDoesNotExistRESTError()
        except PIDUnregistered:
            raise PIDUnregisteredRESTError()
        except PIDDeletedError:
            raise PIDDeletedRESTError()
        except PIDMissingObjectError as e:
            current_app.logger.exception(
                'No object assigned to {0}.'.format(e.pid),
                extra={'pid': e.pid})
            raise PIDMissingObjectRESTError(e.pid)
        except PIDRedirectedError as e:
            try:
                location = url_for(
                    '.{0}_item'.format(
                        current_items_rest.default_endpoint_prefixes[
                            e.destination_pid.pid_type]),
                    pid_value=e.destination_pid.pid_value)
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
                        e.destination_pid.pid_type),
                    extra={
                        'pid': e.pid,
                        'destination_pid': e.destination_pid,
                    })
                raise PIDRedirectedRESTError(e.destination_pid.pid_type)


class PIDConverter(BaseConverter):
    """Resolve PID value."""

    def __init__(self, url_map, pid_type, getter=None, record_class=None):
        """Initialize PID resolver.

        :param url_map: url map info
        :param pid_type: the type of pid
        """
        super(PIDConverter, self).__init__(url_map)
        getter = obj_or_import_string(getter, default=partial(
            obj_or_import_string(record_class, default=Record).get_record,
            with_deleted=True
        ))
        self.resolver = Resolver(pid_type=pid_type, object_type='rec',
                                 getter=getter)

    def to_python(self, value):
        """Resolve PID value.

        :param value: pid value
        """
        return LazyPIDValue(self.resolver, value)


class PIDPathConverter(PIDConverter, PathConverter):
    """Resolve PID path value."""
