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

WEKO_SCHEMA_UI_ADMIN_UPLOAD = 'weko_schema_ui/admin/upload.html'

WEKO_SCHEMA_UI_ADMIN_LIST = 'weko_schema_ui/admin/list.html'

WEKO_SCHEMA_UI_SEARCH_API = '/api/schemas/'
"""URL of search endpoint for schemas."""

WEKO_SCHEMA_UI_RECORD_API = '/api/schemas/{pid_value}'
"""URL of search endpoint for schemas."""

WEKO_SCHEMA_UI_FILES_API = '/api/schemas/files'
"""URL of files endpoints for uploading."""

WEKO_SCHEMA_UI_DEFAULT_SCHEMAFORM = 'json/weko_schema_ui/form.json'
WEKO_SCHEMA_UI_FORM_JSONSCHEMA = 'json/weko_schema_ui/schema.json'

WEKO_SCHEMA_REST_XSD_LOCATION_FOLDER = '{0}/data/xsd/'
"""データスキーマ."""

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

WEKO_SCHEMA_DDI_VERSION = "2.5"
"""DDI Schema version"""

WEKO_SCHEMA_DDI_SCHEMA_NAME = "ddi_mapping"
"""DDI schema name"""

WEKO_SCHEMA_JPCOAR_V1_SCHEMA_NAME = 'jpcoar_v1_mapping'
"""JPCOAR v1.0 schema name"""

WEKO_SCHEMA_JPCOAR_V2_SCHEMA_NAME = 'jpcoar_mapping'
"""JPCOAR v2.0 schema name"""

WEKO_SCHEMA_JPCOAR_V1_RESOURCE_TYPE_REPLACE = {
    'other periodical':'other',
    'conference output':'conference object',
    'conference presentation':'conference object',
    'aggregated data': 'dataset',
    'clinical trial data': 'dataset',
    'compiled data': 'dataset',
    'encoded data': 'dataset',
    'experimental data': 'dataset',
    'genomic data': 'dataset',
    'geospatial data': 'dataset',
    'laboratory notebook': 'dataset',
    'measurement and test data': 'dataset',
    'observational data': 'dataset',
    'recorded data': 'dataset',
    'simulation data': 'dataset',
    'survey data': 'dataset',
    'design patent': 'patent',
    'PCT application': 'patent',
    'plant patent': 'patent',
    'plant variety protection': 'patent',
    'software patent': 'patent',
    'trademark': 'patent',
    'utility model': 'patent',
    'commentary': 'other',
    'design': 'other',
    'industrial design': 'other',
    'layout design': 'other',
    'peer review': 'other',
    'research protocol': 'other',
    'source code':'software',
    'transcription': 'other',
    'journal':'periodical',
}
"""Resource type replace list for jpcoar v1.0"""

WEKO_SCHEMA_JPCOAR_V2_RESOURCE_TYPE_REPLACE={
    'periodical':'journal',
    'interview':'other',
    'internal report':'other',
    'report part':'other',
    'conference object':'conference output',
}
"""Resource type replace list for jpcoar v2.0"""


WEKO_SCHEMA_JPCOAR_V1_NAMEIDSCHEME_REPLACE = {'e-Rad_Researcher':'e-Rad'}
"""nameIdentifierScheme replace list for jpcoar v1.0"""

WEKO_SCHEMA_JPCOAR_V2_NAMEIDSCHEME_REPLACE = {'e-Rad':'e-Rad_Researcher'}
"""nameIdentifierScheme replace list for jpcoar v2.0"""

WEKO_SCHEMA_UI_LIST_SCHEME = ['e-Rad', 'e-Rad_Researcher','NRID', 'ORCID', 'ISNI', 'VIAF', 'AID',
                              'kakenhi', 'Ringgold', 'GRID', 'ROR']
""" List of scheme """

WEKO_SCHEMA_UI_LIST_SCHEME_AFFILIATION = ['ISNI', 'kakenhi',
                                          'Ringgold', 'GRID','ROR']
""" List of affiliation scheme """

WEKO_SCHEME_FIRST_INDEX = 0
""" Name Identifior Item first index """

WEKO_SCHEMA_RECORD_URL = "{}records/{}"
"""Pattern of url record."""

WEKO_SCHEMA_VERSION_TYPE = {
    "modified": "oaire:versiontype",
    "original": "oaire:version"
}
"""Modified and original for versiontype key"""

WEKO_SCHEMA_PUBLISHER_TYPE = {
    "modified": "jpcoar:publisher_jpcoar",
    "original": "jpcoar:publisher"
}
"""Modified and original for publisher key"""

WEKO_SCHEMA_DATE_TYPE = {
    "modified": "dcterms:date_dcterms",
    "original": "dcterms:date"
}
"""Modified and original for publisher key"""

WEKO_SCHEMA_RELATION_TYPE = [
    'inSeries','isCitedBy','Cites','isVersionOf','hasVersion','isPartOf','hasPart',
    'isReferencedBy','references','isFormatOf','hasFormat',
    'isReplacedBy','replaces','isRequiredBy','requires','isSupplementedBy',
    'isSupplementTo','isIdenticalTo','isDerivedFrom','isSourceOf'
]
"""jpcoar:relation relationType Controlled Vocabularies"""

WEKO_SCHEMA_DATE_DEFAULT_DATETYPE = "Issued"

WEKO_SCHEMA_DATE_DATETYPE_MAPPING = {
    'departmental bulletin paper': WEKO_SCHEMA_DATE_DEFAULT_DATETYPE
}