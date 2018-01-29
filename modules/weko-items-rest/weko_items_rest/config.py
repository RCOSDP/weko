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

"""Configuration for weko-items-rest."""

from flask import request

from .facets import terms_filter
from .utils import check_elasticsearch, deny_all


def _(x):
    return x


ITEMS_REST_ENDPOINTS = dict(
    items=dict(
        pid_type='items',
        pid_minter='recid',
        pid_fetcher='recid',
        record_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        record_class='weko_records.api:FilesMetadata',
        file_route='/item/files/',
        item_route='/item/files/<pid_value>',
        file_put_route='/item/files/put/<pid_value>/<path:key>',
        default_media_type='application/json',
        max_result_window=10000,
    ),
)

ITEMS_REST_FILE_DOWNLOAD_BASE_URL = 'record/{0}/files/{1}'

"""Default REST endpoints loaded.

This option can be overwritten to describe the endpoints of different
record types. Each endpoint is in charge of managing all its CRUD operations
(GET, POST, PUT, DELETE, ...).

The structure of the dictionary is as follows:

.. code-block:: python

    from flask import abort
    from flask_security import current_user
    from invenio_records_rest.query import es_search_factory


    def search_factory(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        return es_search_factory(*args, **kwargs)


    def permission_check_factory():
        def check_title(record, *args, **kwargs):
            def can(self):
                if record['title'] == 'Hello World':
                    return True
            return type('Check', (), {'can': can})()


    ITEMS_REST_ENDPOINTS = {
        'endpoint-prefix': {
            'create_permission_factory_imp': permission_check_factory(),
            'default_endpoint_prefix': True,
            'default_media_type': 'application/json',
            'delete_permission_factory_imp': permission_check_factory(),
            'item_route': ''/recods/<pid(record-pid-type):pid_value>'',
            'links_factory_imp': ('invenio_records_rest.links:'
                                  'default_links_factory'),
            'list_route': '/records/',
            'max_result_window': 10000,
            'pid_fetcher': '<registered-pid-fetcher>',
            'pid_minter': '<registered-minter-name>',
            'pid_type': '<record-pid-type>',
            'read_permission_factory_imp': permission_check_factory(),
            'record_class': 'mypackage.api:MyRecord',
            'record_loaders': {
                'application/json': 'mypackage.loaders:json_loader'
            },
            'record_serializers': {
                'application/json': 'mypackage.utils:my_json_serializer'
            },
            'search_class': 'mypackage.utils:mysearchclass',
            'search_factory_imp': search_factory(),
            'search_index': 'elasticsearch-index-name',
            'search_serializers': {
                'application/json': 'mypackage.utils:my_json_search_serializer'
            },
            'search_type': 'elasticsearch-doc-type',
            'suggesters': {
                'my_url_param_to_complete': {
                    'completion': {
                        'field': 'suggest_byyear_elasticsearch_field',
                        'size': 10,
                        'context': 'year'
                    }
                },
            },
            'update_permission_factory_imp': permission_check_factory(),
            'use_options_view': True,
        },
    }

:param create_permission_factory_imp: Import path to factory that create
    permission object for a given record.

:param default_endpoint_prefix: declare the current endpoint as the default
    when building endpoints for the defined ``pid_type``. By default the
    default prefix is defined to be the value of ``pid_type``.

:param default_media_type: Default media type for both records and search.

:param delete_permission_factory_imp: Import path to factory that creates a
    delete permission object for a given record.

:param item_route: URL rule for a single record.

:param links_factory_imp: Factory for record links generation.

:param list_route: Base URL for the records endpoint.

:param max_result_window: Maximum total number of records retrieved from a
    query.

:param pid_type: It specifies the record pid type. Required.
    You can generate an URL to list all records of the given ``pid_type`` by
    calling ``url_for('invenio_records_rest.{0}_list'.format(
    current_records_rest.default_endpoint_prefixes[pid_type]))``.

:param pid_fetcher: It identifies the registered fetcher name. Required.

:param pid_minter: It identifies the registered minter name. Required.

:param read_permission_factory_imp: Import path to factory that creates a
    read permission object for a given record.

:param record_class: A record API class or importable string.

:param record_loaders: It contains the list of record deserializers for
    supperted formats.

:param record_serializers: It contains the list of record serializers for
    supported formats.

:param search_class: Import path or class object for the object in charge of
    execute the search queries. The default search class is
    class`invenio_search.api.RecordsSearch`.
    For more information about resource loading, see the `Search
    <http://elasticsearch-dsl.readthedocs.io/en/latest/search_dsl.html>` of the
    ElasticSearch DSL library.

:param search_factory_imp: Factory to parse quieries.

:param search_index: Name of the search index used when searching records.

:param search_serializers: It contains the list of records serializers for all
    supported format. This configuration differ from the previous because in
    this case it handle a list of records resulted by a search query instead of
    a single record.

:param search_type: Name of the search type used when searching records.

:param suggesters: Suggester fields configuration. Any element of the
    dictionary represents a suggestion field. The key of the dictionary element
    is used to identify the url query parameter. The ``field`` parameter
    identifies the suggester field name in your elasticsearch schema.
    To have more information about suggestion configuration, you can read
    suggesters section on ElasticSearch documentation.

    .. note:: Only completion suggessters are supported.

:param update_permission_factory_imp: Import path to factory that creates a
    update permission object for a given record.

:param use_options_view: Determines if a special option view should be
    installed.
"""

ITEMS_REST_DEFAULT_LOADERS = {
    'application/json': lambda: request.get_json(),
    'application/json-patch+json': lambda: request.get_json(force=True),
}
"""Default data loaders per request mime type.

This option can be overritten in each REST endpoint as follows:

.. code-block:: python

    ITEMS_REST_ENDPOINTS = {
        'recid': {
            ...
            'record_loaders': {
                'aplication/json': 'mypackage.utils:myloader',
            },
            ...
        }
    }

"""

ITEMS_REST_SORT_OPTIONS = dict(
    records=dict(
        bestmatch=dict(
            title=_('Best match'),
            fields=['_score'],
            default_order='desc',
            order=1,
        ),
        mostrecent=dict(
            title=_('Most recent'),
            fields=['-_created'],
            default_order='asc',
            order=2,
        ),
    )
)
"""Sort options for default sorter factory.

The structure of the dictionary is as follows:

.. code-block:: python

    ITEMS_REST_SORT_OPTIONS = {
        '<index or index alias>': {
            '<sort-field-name>': {
                'fields': ['<search_field>', '<search_field>', ...],
                'title': '<title displayed to end user in search-ui>',
                'default_order': '<default sort order in search-ui>',
            }
        }
    }

Each search field can be either:

- A string of the form ``'<field name>'`` (ascending) or ``'-<field name>'``
  (descending).
- A dictionary with Elasicsearch sorting syntax (e.g.
  ``{'price' : {'order' : 'asc', 'mode' : 'avg'}}``).
- A callable taking one boolean parameter (``True`` for ascending and ``False``
  for descending) and returning a dictionary like above. This is useful if you
  need to extract extra sorting parameters (e.g. for geo location searches).
"""

ITEMS_REST_DEFAULT_SORT = dict(
    records=dict(
        query='bestmatch',
        noquery='mostrecent',
    )
)
"""Default sort option per index with/without query string.

The structure of the dictionary is as follows:

.. code-block:: python

    ITEMS_REST_DEFAULT_SORT = {
        '<index or index alias>': {
            'query': '<default-sort-if-a-query-is-passed-from-url>',
            'noquery': '<default-sort-if-no-query-in-passed-from-url>',
        }
    }
"""

ITEMS_REST_FACETS = dict(
    records=dict(
        aggs=dict(
            type=dict(terms=dict(field='type'))
        ),
        post_filters=dict(
            type=terms_filter('type'),
        )
    )
)
"""Facets per index for the default facets factory.

The structure of the dictionary is as follows:

.. code-block:: python

    ITEMS_REST_FACETS = {
        '<index or index alias>': {
            'aggs': {
                '<key>': <aggregation definition>,
                ...
            }
            'filters': {
                '<key>': <filter func>,
                ...
            }
            'post_filters': {
                '<key>': <filter func>,
                ...
            }
        }
    }
"""

ITEMS_REST_DEFAULT_CREATE_PERMISSION_FACTORY = None
"""Default create permission factory: reject any request."""

ITEMS_REST_DEFAULT_READ_PERMISSION_FACTORY = check_elasticsearch
"""Default read permission factory: check if the record exists."""

ITEMS_REST_DEFAULT_UPDATE_PERMISSION_FACTORY = deny_all
"""Default update permission factory: reject any request."""

ITEMS_REST_DEFAULT_DELETE_PERMISSION_FACTORY = deny_all
"""Default delete permission factory: reject any request."""

ITEMS_REST_ELASTICSEARCH_ERROR_HANDLERS = {
    'query_parsing_exception': (
        'invenio_records_rest.views'
        ':elasticsearch_query_parsing_exception_handler'
    ),
}
"""Handlers for ElasticSearch error codes."""

ITEMS_REST_FILE_MAXSIZE = 25*1024*1024

"""If specificd as 0, size no limit."""
