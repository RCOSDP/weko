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

"""Record serialization."""

from invenio_records_rest.serializers.citeproc import CiteprocSerializer
from invenio_records_rest.serializers.json import JSONSerializer
from invenio_records_rest.serializers.response import record_responsify, \
    search_responsify
from invenio_records_rest.serializers.schemas.json import RecordSchemaJSONV1
from pkg_resources import resource_filename

from .depositschema import DepositSchemaV1
from .json import WekoJSONSerializer
from .opensearchresponse import oepnsearch_responsify
from .opensearchserializer import OpenSearchSerializer
from .schemas.csl import RecordSchemaCSLJSON
from .searchserializer import SearchSerializer

deposit_json_v1 = JSONSerializer(DepositSchemaV1, replace_refs=True)
#: JSON record serializer for individual records.
deposit_json_v1_response = record_responsify(
    deposit_json_v1, 'application/json')

# For search result list
json_v1 = SearchSerializer(RecordSchemaJSONV1)
json_v1_search = search_responsify(json_v1, 'application/json')

# For opensearch serialize
opensearch_v1 = OpenSearchSerializer(RecordSchemaJSONV1)
opensearch_v1_search = oepnsearch_responsify(opensearch_v1)

#: CSL-JSON serializer
csl_v1 = WekoJSONSerializer(RecordSchemaCSLJSON, replace_refs=True)
#: CSL Citation Formatter serializer
citeproc_v1 = CiteprocSerializer(csl_v1)

#: CSL-JSON record serializer for individual records.
csl_v1_response = record_responsify(
    csl_v1, 'application/vnd.citationstyles.csl+json')
#: CSL Citation Formatter serializer for individual records.
citeproc_v1_response = record_responsify(citeproc_v1, 'text/x-bibliography')
