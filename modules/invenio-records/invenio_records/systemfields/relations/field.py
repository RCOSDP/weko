# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020-2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Relations system field."""

from werkzeug.utils import cached_property

from ..base import SystemField
from .mapping import RelationsMapping
from .relations import RelationBase


#
# System field
#
class RelationsField(SystemField):
    """Relations field for connections to external entities."""

    def __init__(self, **fields):
        """Initialize the field."""
        super().__init__()
        assert all(isinstance(f, RelationBase) for f in fields.values())
        self._original_fields = fields

    def __getattr__(self, name):
        """Get a field definition."""
        if name in self._fields:
            return self._fields[name]
        raise AttributeError

    def __iter__(self):
        """Iterate over the configured fields."""
        return iter(getattr(self, f) for f in self._fields)

    def __contains__(self, name):
        """Return if a field exists in the configured fields."""
        return name in self._fields

    #
    # Properties
    #
    @cached_property
    def _fields(self):
        """Get the fields."""
        return self._original_fields

    #
    # Helpers
    #
    def obj(self, instance):
        """Get the relations object."""
        # Check cache
        obj = self._get_cache(instance)
        if obj:
            return obj
        obj = RelationsMapping(record=instance, fields=self._fields)
        self._set_cache(instance, obj)
        return obj

    #
    # Data descriptor
    #
    def __get__(self, record, owner=None):
        """Accessing the attribute."""
        # Class access
        if record is None:
            return self
        return self.obj(record)

    def __set__(self, instance, values):
        """Setting the attribute."""
        obj = self.obj(instance)
        for k, v in values.items():
            setattr(obj, k, v)

    #
    # Record extension
    #
    def pre_commit(self, record):
        """Initialise the model field."""
        self.obj(record).validate()
        self.obj(record).clean()


class MultiRelationsField(RelationsField):
    """Relations field for connections to external entities.

    It allows to define nested relation fields. For example:

    .. code-block:: python

        class Record:

            relations = MultiRelationsField(
                field_one=PIDListRelation(
                    "metadata.field_one",
                    ...
                ),
                inner=RelationsField(
                    inner_field=PIDListRelation(
                        "metadata.inner_field",
                    ...
                    ),
                )
            )
    """

    def __init__(self, **fields):
        """Initialize the field.

        The nested RelationFields will be flattened to the root.
        In the example above, the relations field has a field (field_one)
        and a nested RelationsField with a field (inner_field). However,
        both of them will be accessed through the relations field.

        .. code-block:: python

            relations.field_one
            relations.inner_field  # correct
            relations.inner.inner_field  # incorrect
        """
        super().__init__()  # no fields passed since validation happens in this class
        assert all(
            isinstance(f, RelationBase) or isinstance(f, RelationsField)
            for f in fields.values()
        )

        self._original_fields = fields
        self._relation_fields = set()

    @cached_property
    def _fields(self):
        """Mutates self._fields to include all nested fields."""
        fields = {}
        self._relation_fields = set()
        for key, field in self._original_fields.items():
            if isinstance(field, RelationBase):
                fields[key] = field
            elif isinstance(field, RelationsField):
                self._relation_fields.add(key)
                for inner_name, inner_field in field._fields.items():
                    if inner_name not in fields:
                        fields[inner_name] = inner_field
        return fields

    #
    # Data descriptor
    #
    def __set__(self, instance, values):
        """Setting the attribute."""
        obj = self.obj(instance)
        for k, v in values.items():
            if k in self._relation_fields:
                for kk, vv in v.items():
                    setattr(obj, kk, vv)
            else:
                setattr(obj, k, v)
