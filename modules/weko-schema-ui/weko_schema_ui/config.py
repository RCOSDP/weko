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

"""Configuration for weko-schema-ui."""

WEKO_SCHEMA_UI_BASE_TEMPLATE = 'weko_schema_ui/base.html'
"""Default base template for the demo page."""

WEKO_SCHEMA_UI_UPLOAD = 'weko_schema_ui/upload.html'

WEKO_SCHEMA_UI_LIST = 'weko_schema_ui/list.html'

WEKO_SCHEMA_UI_SEARCH_API = '/api/schemas/'
"""URL of search endpoint for schemas."""

WEKO_SCHEMA_UI_RECORD_API = '/api/schemas/{pid_value}'
"""URL of search endpoint for schemas."""

WEKO_SCHEMA_UI_FILES_API = '/api/schemas/files'
"""URL of files endpoints for uploading."""

WEKO_SCHEMA_UI_DEFAULT_SCHEMAFORM = 'json/weko_schema_ui/form.json'
WEKO_SCHEMA_UI_FORM_JSONSCHEMA = 'json/weko_schema_ui/schema.json'

WEKO_SCHEMA_REST_XSD_LOCATION_FOLDER = '{0}/static/xsd/'

_PID = 'pid(depid,record_class="weko_schema_ui.api:WekoSchema")'

WEKO_SCHEMA_REST_ENDPOINTS = {
    'depid': {
        'pid_type': 'depid',
        'pid_minter': 'deposit',
        'pid_fetcher': 'deposit',
        'record_class': 'weko_schema_ui.api:WekoSchema',
        'record_serializers': {
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_response'),
        },
        'schemas_route': '/schemas/',
        'schema_route': '/schemas/<pid_value>',
        'schemas_put_route': '/schemas/put/<pid_value>/<path:key>',
        # 'schemas_formats_route': '/schemas/formats/',
        'default_media_type': 'application/json',
        'max_result_window': 10000,
    },
}
"""Basic REST deposit configuration."""

WEKO_SCHEMA_UI_RESPONSE_MESSAGES = {}

WEKO_SCHEMA_CACHE_PREFIX = 'cache_{schema_name}'
""" cache items prifix info"""

# WEKO_SCHEMA_UI_FORMAT_EDIT = 'weko_schema_ui/edit.html'
# WEKO_SCHEMA_UI_FORMAT_EDIT_API = '/api/schemas/'
# """URL of search endpoint for schemas."""
#
# WEKO_SCHEMA_UI_FORMAT_SCHEMAFORM = 'json/weko_schema_ui/format_form.json'
# WEKO_SCHEMA_UI_FORMAT_FORM_JSONSCHEMA = 'json/weko_schema_ui/format_schema.json'
