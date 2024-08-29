# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Marshmallow schemas for serialization."""

from .json import (
    Nested,
    RecordMetadataSchemaJSONV1,
    RecordSchemaJSONV1,
    StrictKeysMixin,
)

__all__ = (
    "RecordSchemaJSONV1",
    "StrictKeysMixin",
    "Nested",
    "RecordMetadataSchemaJSONV1",
)
