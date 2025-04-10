# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Default configuration of deposit module."""

from invenio_records_rest.facets import terms_filter
from invenio_records_rest.utils import check_elasticsearch

from .utils import check_oauth2_scope_write, \
    check_oauth2_scope_write_elasticsearch

DEPOSIT_SEARCH_API = '/api/deposits'
"""URL of search endpoint for deposits."""

DEPOSIT_RECORDS_API = '/api/deposits/{pid_value}'
"""URL of record endpoint for deposits."""

DEPOSIT_FILES_API = '/api/files'
"""URL of files endpoints for uploading."""

DEPOSIT_PID_MINTER = 'recid'
"""PID minter used for record submissions."""

DEPOSIT_JSONSCHEMAS_PREFIX = 'deposits/'
"""Prefix for all deposit JSON schemas."""

DEPOSIT_DEFAULT_JSONSCHEMA = 'deposits/deposit-v1.0.0.json'
"""Default JSON schema used for new deposits."""

DEPOSIT_DEFAULT_SCHEMAFORM = 'json/invenio_deposit/form.json'
"""Default Angular Schema Form."""

_PID = 'pid(depid,record_class="invenio_deposit.api:Deposit")'

DEPOSIT_REST_ENDPOINTS = {
    'depid': {
        'pid_type': 'depid',
        'pid_minter': 'deposit',
        'pid_fetcher': 'deposit',
        'record_class': 'invenio_deposit.api:Deposit',
        'files_serializers': {
            'application/json': ('invenio_deposit.serializers'
                                 ':json_v1_files_response'),
        },
        'record_serializers': {
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_response'),
        },
        'search_class': 'invenio_deposit.search:DepositSearch',
        'search_serializers': {
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        'list_route': '/deposits/',
        'indexer_class': None,
        'item_route': '/deposits/<{0}:pid_value>'.format(_PID),
        'file_list_route': '/deposits/<{0}:pid_value>/files'.format(_PID),
        'file_item_route':
            '/deposits/<{0}:pid_value>/files/<path:key>'.format(_PID),
        'default_media_type': 'application/json',
        'links_factory_imp': 'invenio_deposit.links:deposit_links_factory',
        'create_permission_factory_imp': check_oauth2_scope_write,
        'read_permission_factory_imp': check_elasticsearch,
        'update_permission_factory_imp':
            check_oauth2_scope_write_elasticsearch,
        'delete_permission_factory_imp':
            check_oauth2_scope_write_elasticsearch,
        'max_result_window': 10000,
    },
}
"""Basic REST deposit configuration.

Most of the configurations have the same meaning of the record configuration
:data:`invenio_records_rest.config.RECORDS_REST_ENDPOINTS`.
Deposit introduce also configuration for files.
"""

DEPOSIT_REST_SORT_OPTIONS = {
    'deposits': {
        'bestmatch': {
            'fields': ['-_score'],
            'title': 'Best match',
            'default_order': 'asc',
            'order': 2,
        },
        'mostrecent': {
            'fields': ['-_updated'],
            'title': 'Most recent',
            'default_order': 'asc',
            'order': 1,
        },
    },
}
"""Basic deposit sort configuration.
See :data:`invenio_records_rest.config.RECORDS_REST_SORT_OPTIONS` for more
information.
"""

DEPOSIT_REST_DEFAULT_SORT = {
    'deposits': {
        'query': 'bestmatch',
        'noquery': 'mostrecent',
    }
}
"""Default deposit sort configuration.
See :data:`invenio_records_rest.config.RECORDS_REST_DEFAULT_SORT` for more
information.
"""

DEPOSIT_REST_FACETS = {
    'deposits': {
        'aggs': {
            'status': {
                'terms': {'field': '_deposit.status'},
            },
        },
        'post_filters': {
            'status': terms_filter('_deposit.status'),
        },
    },
}
"""Basic deposit facts configuration.
See :data:`invenio_records_rest.config.RECORDS_REST_FACETS` for more
information.
"""

DEPOSIT_RECORDS_UI_ENDPOINTS = {
    'depid': {
        'pid_type': 'depid',
        'route': '/deposit/<pid_value>',
        'template': 'invenio_deposit/edit.html',
        'record_class': 'invenio_deposit.api:Deposit',
        'view_imp': 'invenio_deposit.views.ui.default_view_method',
    },
}
"""Basic deposit UI endpoints configuration.

The structure of the dictionary is as follows:

.. code-block:: python

    DEPOSIT_RECORDS_UI_ENDPOINTS = {
        '<pid-type>': {
            'pid_type': '<pid-type>',
            'route': '/unique/path/to/deposit/<pid_value>',
            'template': 'invenio_deposit/edit.html',
            'record_class': 'mypackage.api:MyDeposit',
            'view_imp': 'mypackage.views.view_method',
            'jsonschema' 'path/to/jsonschema/deposit.json',
            'schemaform': 'path/to/schema/form.json',
        }
    }
"""

DEPOSIT_UI_ENDPOINT = '{scheme}://{host}/deposit/{pid_value}'
"""The UI endpoint for depositions with pid."""

DEPOSIT_UI_INDEX_TEMPLATE = 'invenio_deposit/index.html'
"""Template for the index page."""

DEPOSIT_UI_NEW_TEMPLATE = 'invenio_deposit/edit.html'
"""Template for a new deposit page."""

DEPOSIT_UI_TOMBSTONE_TEMPLATE = 'invenio_deposit/tombstone.html'
"""Template for a tombstone deposit page."""

DEPOSIT_UI_JSTEMPLATE_ACTIONS = \
    'node_modules/invenio-records-js/dist/templates/actions.html'
"""Template for <invenio-records-actions> defined by `invenio-records-js`."""

DEPOSIT_UI_JSTEMPLATE_ERROR = \
    'node_modules/invenio-records-js/dist/templates/error.html'
"""Template for <invenio-records-error> defined by `invenio-records-js`."""

DEPOSIT_UI_JSTEMPLATE_FORM = \
    'templates/invenio_deposit/form.html'
"""Template for <invenio-records-form> defined by `invenio-records-js`."""

DEPOSIT_UI_JSTEMPLATE_WORKSPACE_FORM = \
    'templates/invenio_deposit/workspace_form.html'
"""Template for <invenio-records-form> defined by `invenio-records-js`."""

DEPOSIT_UI_SEARCH_INDEX = 'deposits'
"""Search index name for the deposit."""

DEPOSIT_DEFAULT_STORAGE_CLASS = 'S'
"""Default storage class."""

DEPOSIT_REGISTER_SIGNALS = True
"""Enable the signals registration."""

DEPOSIT_FORM_TEMPLATES_BASE = 'templates/invenio_deposit/decorators'
"""Angular Schema Form temmplates location."""

DEPOSIT_FORM_TEMPLATES_WORKSPACE_BASE = 'templates/invenio_deposit/decorators_workspace'
"""Angular Schema Form temmplates location."""

DEPOSIT_FORM_TEMPLATES = {
    'default': 'default.html',
    'fieldset': 'fieldset.html',
    'array': 'array.html',
    'radios_inline': 'radios_inline.html',
    'radios': 'radios.html',
    'select': 'select.html',
    'button': 'button.html',
    'textarea': 'textarea.html'
}
"""Templates for Angular Schema Form."""

DEPOSIT_FORM_TEMPLATES_WORKSPACE = {
    'default': 'default.html',
    'fieldset': 'fieldset.html',
    'array': 'array.html',
    'radios_inline': 'radios_inline.html',
    'radios': 'radios.html',
    'select': 'select.html',
    'button': 'button.html',
    'textarea': 'textarea.html'
}
"""Templates for Angular Schema Form."""

DEPOSIT_RESPONSE_MESSAGES = {}
"""Alerts shown when actions are completed on deposit."""
