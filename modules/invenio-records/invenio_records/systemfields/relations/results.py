# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020-2021 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Relations system field."""

from ...dictutils import dict_lookup, dict_set
from .errors import InvalidCheckValue, InvalidRelationValue


class RelationResult:
    """Relation access result."""

    def __init__(self, field, record):
        """Initialize the relation result."""
        self.field = field
        self.record = record

    def _lookup_id(self):
        return dict_lookup(self.record, self.value_key)

    def _lookup_data(self):
        return dict_lookup(self.record, self.key)

    def __call__(self, force=True):
        """Resolve the relation."""
        try:
            val = self._lookup_id()
            obj = self.resolve(val)
            return obj
        except KeyError:
            return None

    def __getattr__(self, name):
        """Proxy attribute access to field."""
        return getattr(self.field, name)

    def _value_check(self, value_to_check, object):
        """Checks if the value is present in the object."""
        for key, value in value_to_check.items():
            if key not in object:
                raise InvalidCheckValue(f"Invalid key {key}.")
            if isinstance(value, dict):
                self._value_check(value, object[key])
            else:
                if not isinstance(value, list):
                    raise InvalidCheckValue(
                        f"Invalid value_check value: {value}; it must be " "a list"
                    )
                elif isinstance(object[key], list):
                    value_exist = set(object[key]).intersection(set(value))
                    if not value_exist:
                        raise InvalidCheckValue(
                            f"Failed cross checking value_check value "
                            f"{value} with record value {object[key]}."
                        )
                else:
                    if object[key] not in value:
                        raise InvalidCheckValue(
                            f"Failed cross checking value_check value "
                            f"{value} with record value {object[key]}."
                        )

    def validate(self):
        """Validate the field."""
        try:
            val = self._lookup_id()
            if not self.exists(val):
                raise InvalidRelationValue(f"Invalid value {val}.")
            if self.value_check:
                data = self._lookup_data()
                obj = self.resolve(data[self.field._value_key_suffix])
                self._value_check(self.value_check, obj)
        except KeyError:
            return None

    def dereference(self, keys=None, attrs=None):
        """Dereference the relation field object inside the record."""
        try:
            data = self._lookup_data()
            return self._dereference_one(data, keys or self.keys, attrs or self.attrs)
        except KeyError:
            return None

    def clean(self, keys=None, attrs=None):
        """Clean the dereferenced attributes inside the record."""
        try:
            data = self._lookup_data()
            return self._clean_one(data, keys or self.keys, attrs or self.attrs)
        except KeyError:
            return None

    def _dereference_one(self, data, keys, attrs):
        """Dereference a single object into a dict."""
        # Don't dereference if already referenced.
        if "@v" in data:
            return data

        # Get related record
        obj = self.resolve(data[self.field._value_key_suffix])
        # Inject selected key/values from related record into
        # the current record.

        # From record dictionary
        if keys is None:
            data.update({k: v for k, v in obj.items()})
        else:
            new_obj = {}
            for k in keys:
                try:
                    val = dict_lookup(obj, k)
                    if val:
                        dict_set(new_obj, k, val)
                except KeyError:
                    pass
            data.update(new_obj)

        # From record attributes (i.e. system fields)
        for a in attrs:
            data[a] = getattr(obj, a)

        # Add a version counter "@v" used for optimistic
        # concurrency control. It allows to search for all
        # outdated records and reindex them.
        data["@v"] = f"{obj.id}::{obj.revision_id}"
        return data

    def _clean_one(self, data, keys, attrs):
        """Remove all but "id" key for a dereferenced related object."""
        relation_id = data[self.field._value_key_suffix]
        data.clear()
        data[self.field._value_key_suffix] = relation_id
        return data


class RelationListResult(RelationResult):
    """Relation access result."""

    def __call__(self, force=True):
        """Resolve the relation."""
        try:
            values = self._lookup_data()
            return (self.resolve(v[self._value_key_suffix]) for v in values)
        except KeyError:
            return None

    def _lookup_id(self, data):
        return dict_lookup(data, self.field._value_key_suffix)

    def _lookup_data(self):
        data = dict_lookup(self.record, self.key)
        if self.relation_field:
            filtered_data = [
                e.get(self.relation_field) for e in data if self.relation_field in e
            ]
            return filtered_data
        return data

    def validate(self):
        """Validate the field."""
        try:
            values = self._lookup_data()
            if values and not isinstance(values, list):
                raise InvalidRelationValue(f"Invalid value {values}, should be list.")

            for v in values:
                relation_id = self._lookup_id(v)
                if not self.exists(relation_id):
                    raise InvalidRelationValue(f"Invalid value {relation_id}.")
                if self.value_check:
                    obj = self.resolve(v[self.field._value_key_suffix])
                    self._value_check(self.value_check, obj)
        except KeyError:
            return None

    def _apply_items(self, func, keys=None, attrs=None):
        """Iterate over the list of objects."""
        # The attributes we want to get from the related record.
        keys = keys or self.keys
        attrs = attrs or self.attrs
        try:
            # Get the list of objects we have to dereference/clean.
            values = self._lookup_data()
            if values:
                for v in values:
                    # Only dereference/clean if "id" key is present in parent.
                    # Note, we control via the JSONSchema if a record can have
                    # only related records (by requiring precense of "id" key),
                    # or if you can mix non-linked records.
                    if self.field._value_key_suffix in v:
                        func(v, keys, attrs)
                return values
        except KeyError:
            return None

    def dereference(self, keys=None, attrs=None):
        """Dereference the relation field object inside the record.

        Dereferences a list of ids::

            [{"id": "eng"}]

        Into

            [{"id": "eng", "title": ..., "@v": ...}]
        """
        return self._apply_items(self._dereference_one, keys, attrs)

    def clean(self, keys=None, attrs=None):
        """Clean the dereferenced attributes inside the record.

        Reverses changes made by dereference.
        """
        return self._apply_items(self._clean_one, keys, attrs)

    def append(self, value):
        """Append a relation to the list."""
        raise NotImplementedError()

    def insert(self, index, value):
        """Insert a relation to the list."""
        raise NotImplementedError()


class RelationNestedListResult(RelationListResult):
    """Relation access result."""

    def __call__(self, force=True):
        """Resolve the relation."""
        try:
            values = self._lookup_data()
            parent_iter = []
            for inner_values in values:
                inner_iter = []
                for v in inner_values:
                    try:
                        inner_iter.append(self.resolve(v[self._value_key_suffix]))
                    except KeyError:
                        continue
                parent_iter.append(iter(inner_iter))
            return iter(parent_iter)
        except KeyError:
            return None

    def validate(self):
        """Validate the field."""
        try:
            values = self._lookup_data()
            if values and not isinstance(values, list):
                raise InvalidRelationValue(f"Invalid value {values}, should be list.")

            for outter_v in values:
                if outter_v and not isinstance(outter_v, list):
                    raise InvalidRelationValue(
                        f"Invalid inner value {outter_v}, should be list."
                    )
                for v in outter_v:
                    relation_id = self._lookup_id(v)
                    if not self.exists(relation_id):
                        raise InvalidRelationValue(f"Invalid value {relation_id}.")
                    if self.value_check:
                        obj = self.resolve(v[self.field._value_key_suffix])
                        self._value_check(self.value_check, obj)
        except KeyError:
            return None

    def _apply_items(self, func, keys=None, attrs=None):
        """Iterate over the list of objects."""
        # The attributes we want to get from the related record.
        attrs = attrs or self.attrs
        keys = keys or self.keys
        try:
            # Get the list of objects we have to dereference/clean.
            values = self._lookup_data()
            if values:
                for outter_v in values:
                    for v in outter_v:
                        if self.field._value_key_suffix in v:
                            func(v, keys, attrs)
                return values
        except KeyError:
            return None
