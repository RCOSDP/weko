# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Record serialization."""

from ..schemas import RecordSchemaJSONV1
from .json import JSONSerializer
from .response import record_responsify, search_responsify

json_v1 = JSONSerializer(RecordSchemaJSONV1)
"""JSON v1 serializer."""

json_v1_response = record_responsify(json_v1, "application/json")
"""JSON response builder that uses the JSON v1 serializer."""

json_v1_search = search_responsify(json_v1, "application/json")
"""JSON search response builder that uses the JSON v1 serializer."""
