# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Loaders for deserializing records in the REST API."""

from ..schemas import RecordMetadataSchemaJSONV1, RecordSchemaJSONV1
from .marshmallow import json_patch_loader, marshmallow_loader

json_v1 = marshmallow_loader(RecordSchemaJSONV1)
"""Simple example loader that will take any JSON."""

json_patch_v1 = json_patch_loader
"""Simple example loader that will take any JSON patch."""

json_pid_checker = marshmallow_loader(RecordMetadataSchemaJSONV1)

__all__ = ("json_v1", "json_patch_loader", "json_pid_checker")
