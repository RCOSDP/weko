# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020-2021 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Relations system field."""
from copy import deepcopy

from invenio_db import db

from ...dictutils import dict_lookup, parse_lookup_key
from .errors import InvalidRelationValue
from .results import RelationListResult, RelationNestedListResult, RelationResult


class RelationBase:
    """Base class for defining relation fields."""

    result_cls = RelationResult

    def __init__(
        self,
        key=None,
        attrs=None,
        keys=None,
        _value_key_suffix="id",
        _clear_empty=True,
        cache_key=None,
        value_check=None,
    ):
        """Initialize the relation."""
        self.key = key
        self.attrs = attrs or []
        self.keys = keys or []
        self._value_key_suffix = _value_key_suffix
        self._clear_empty = _clear_empty
        self._cache_key = cache_key
        self.value_check = value_check
        self._cache_ref = None

    def inject_cache(self, cache, default_key):
        """Internal method used by mapping to inject a shared cache."""
        self._cache_ref = cache
        if self._cache_key is None:
            self._cache_key = default_key
        if self._cache_key not in self._cache_ref:
            self._cache_ref[self._cache_key] = {}

    @property
    def cache(self):
        """Get the cache for this relation.

        Note the cache is shared with all relations defined on the same system
        field.
        """
        return self._cache_ref[self._cache_key]

    def resolve(self, id_):
        """Resolve a relation by its ID (has to be implemented)."""
        raise NotImplementedError()

    @property
    def value_key(self):
        """Default stored value key getter."""
        return f"{self.key}.{self._value_key_suffix}"

    def exists(self, id_):
        """Default existence check by ID."""
        return self.resolve(id_) is not None

    def exists_many(self, ids):
        """Default multiple existence check by a list of IDs."""
        return all(self.exists(i) for i in ids)

    def get_value(self, record):
        """Return the resolved relation from a record."""
        return self.result_cls(self, record)

    def parse_value(self, value):
        """Parse an object to a resolvable ID to be stored."""
        return value

    def set_value(self, record, value):
        """Set the relation value."""
        store_value = self.parse_value(value)
        if self.exists(store_value):
            # TODO: stolen from `SystemField.set_dictkey`
            keys = parse_lookup_key(self.value_key)
            try:
                parent = dict_lookup(record, keys, parent=True)
            except KeyError as e:
                parent = record
                for k in keys[:-1]:
                    if k not in parent:
                        parent[k] = {}
                    else:
                        if not isinstance(parent[k], dict):
                            raise KeyError(
                                f"Expected a dict at subkey '{k}'. "
                                f"Found '{parent[k].__class__.__name__}'."
                            )
                    parent = parent[k]

            if not isinstance(parent, dict):
                raise KeyError(
                    f"Expected a dict at subkey '{keys[-2]}'. "
                    f"Found '{parent.__class__.__name__}'."
                )

            parent[keys[-1]] = store_value
        else:
            raise InvalidRelationValue("Invalid field value.")

    def clear_value(self, record):
        """Clear the relation value."""
        keys = parse_lookup_key(self.value_key)
        try:
            parent = dict_lookup(record, keys, parent=True)
        except KeyError as e:
            parent = record
            for k in keys[:-1]:
                if k not in parent:  # Nothing to set
                    return
                parent = parent[k]
        parent.pop(keys[-1], None)
        if self._clear_empty and parent == {}:
            parent = dict_lookup(record, keys[:-1], parent=True)
            parent.pop(keys[-2], None)


class ListRelation(RelationBase):
    """Primary-key relation list type."""

    result_cls = RelationListResult

    def __init__(self, *args, relation_field=None, **kwargs):
        """Initialize the list relation.

        :param relation_field:  The field representing the relation. (Intended
                                to be used when we are passing a list of
                                objects but only one field of each object is
                                referring to a relation)
        :type relation_field: str
        """
        self.relation_field = relation_field
        super().__init__(*args, **kwargs)

    def parse_value(self, value):
        """Parse a record (or ID) to the ID to be stored."""
        if isinstance(value, (tuple, list)):
            if self.relation_field:
                return [
                    super(ListRelation, self).parse_value(v.get(self.relation_field))
                    for v in value
                    if self.relation_field in v
                ]
            return [super(ListRelation, self).parse_value(v) for v in value]
        else:
            raise InvalidRelationValue("Invalid value. Expected list.")

    def _get_parent(self, record, keys):
        """Get parent dict."""
        try:
            parent = dict_lookup(record, keys[:-1], parent=True)
        except KeyError as e:
            parent = record
            for k in keys[:-2]:
                if k not in parent:
                    parent[k] = {}
                else:
                    if not isinstance(parent[k], dict):
                        raise KeyError(
                            f"Expected a dict at subkey '{k}'. "
                            f"Found '{parent[k].__class__.__name__}'."
                        )
                parent = parent[k]
        return parent

    def set_value(self, record, value):
        """Set the relation value."""
        store_values = self.parse_value(value)
        # Validate all values
        if self.exists_many(store_values):
            keys = parse_lookup_key(self.value_key)
            store_key, rel_id_key = keys[-2:]
            parent = self._get_parent(record, keys)

            if self.relation_field:
                values_list = deepcopy(value)
                for v in values_list:
                    sv = v.get(self.relation_field)
                    if sv:
                        v[self.relation_field] = {rel_id_key: sv}
            else:
                values_list = [{rel_id_key: sv} for sv in store_values]

            parent[store_key] = values_list
        else:
            raise InvalidRelationValue("Invalid values.")

    def clear_value(self, record):
        """Clear the relation value."""
        keys = parse_lookup_key(self.key)
        try:
            parent = dict_lookup(record, keys, parent=True)
        except KeyError as e:
            parent = record
            for k in keys[:-1]:
                if k not in parent:  # Nothing to set
                    return
                parent = parent[k]
        parent.pop(keys[-1], None)
        if self._clear_empty and parent == []:
            parent = dict_lookup(record, keys[:-1], parent=True)
            parent.pop(keys[-2], None)


class PKRelation(RelationBase):
    """Primary-key relation type."""

    def __init__(self, *args, record_cls=None, **kwargs):
        """Initialize the PK relation."""
        self.record_cls = record_cls
        super().__init__(*args, **kwargs)

    def resolve(self, id_):
        """Resolve the value using the record class."""
        if id_ in self.cache:
            return self.cache[id_]

        try:
            obj = self.record_cls.get_record(id_)
            # We detach the related record model from the database session when
            # we add it in the cache. Otherwise, accessing the cached record
            # model, will execute a new select query after a db.session.commit.
            db.session.expunge(obj.model)
            self.cache[id_] = obj
            return obj
        # TODO: there's many ways Record.get_record can fail...
        except Exception:
            return None

    def parse_value(self, value):
        """Parse a record (or ID) to the ID to be stored."""
        if isinstance(value, str):
            return value
        elif isinstance(value, self.record_cls):
            return str(value.id)
        else:
            raise InvalidRelationValue(
                f'Invalid value. Expected "str" or "{self.record_cls}"'
            )

    # TODO: We could have a more efficient "exists" via PK queries
    # def exists(self, id_):
    #     """Check if an ID exists using the record class."""
    #     return bool(self.record_cls.model_cls.query.filter_by(id=id_))
    #
    # def exists_many(self, ids):
    #     """."""
    #     self.record_cls.get_record(id_)


class PKListRelation(ListRelation, PKRelation):
    """Primary-key list relation."""


class NestedListRelation(ListRelation):
    """Primary-key relation list type."""

    result_cls = RelationNestedListResult

    def exists_many(self, ids):
        """Default multiple existence check by a list of IDs."""
        return all(all(self.exists(i) for i in inner_ids) for inner_ids in ids)

    def parse_value(self, value):
        """Parse a record (or ID) to the ID to be stored."""
        if isinstance(value, (tuple, list)):
            outter_list = []
            if self.relation_field:
                for inner_list in value:
                    inner_v = inner_list.get(self.relation_field)
                    if inner_v:
                        outter_list.append(
                            [super(ListRelation, self).parse_value(v) for v in inner_v]
                        )
            else:
                for inner_list in value:
                    outter_list.append(
                        [super(ListRelation, self).parse_value(v) for v in inner_list]
                    )
            return outter_list
        else:
            raise InvalidRelationValue("Invalid value. Expected list.")

    def set_value(self, record, value):
        """Set the relation value."""
        store_values = self.parse_value(value)
        # Validate all values
        if self.exists_many(store_values):
            keys = parse_lookup_key(self.value_key)
            store_key, rel_id_key = keys[-2:]
            parent = self._get_parent(record, keys)

            if self.relation_field:
                values_list = deepcopy(value)
                for v in values_list:
                    inner_sv = v.get(self.relation_field)
                    if inner_sv:
                        v[self.relation_field] = [{rel_id_key: sv} for sv in inner_sv]
            else:
                values_list = [
                    [{rel_id_key: sv} for sv in inner_values]
                    for inner_values in store_values
                ]

            parent[store_key] = values_list
        else:
            raise InvalidRelationValue("Invalid values.")


class PKNestedListRelation(NestedListRelation, PKRelation):
    """Primary-key nested list relation."""
