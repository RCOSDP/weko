# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020-2021 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Relations system field.

The field consists of:

- The system field itself.
- A relation mapping which is an object returned when accessing the system
  field from an instance (e.g. ``record.relations``).
- Relations (e.g. PKRelation) used for defining a relationship to a specific
  record type.
- Results, values returned when accessing a field (e.g.
  ``record.relations.languages``).
"""

from .errors import InvalidCheckValue, InvalidRelationValue, RelationError
from .field import MultiRelationsField, RelationsField
from .mapping import RelationsMapping
from .modelrelations import ModelRelation
from .relations import (
    ListRelation,
    NestedListRelation,
    PKListRelation,
    PKNestedListRelation,
    PKRelation,
    RelationBase,
)
from .results import RelationListResult, RelationNestedListResult, RelationResult

__all__ = (
    "InvalidCheckValue",
    "InvalidRelationValue",
    "ListRelation",
    "ModelRelation",
    "MultiRelationsField",
    "NestedListRelation",
    "PKListRelation",
    "PKNestedListRelation",
    "PKRelation",
    "RelationBase",
    "RelationError",
    "RelationListResult",
    "RelationNestedListResult",
    "RelationResult",
    "RelationsField",
    "RelationsMapping",
)
