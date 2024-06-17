# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020-2021 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Model relations.

A model relation relies on database-level foreign keys to define a relationship
instead of injecting the IDs inside the record dictionary. On indexing, the
specified attributes from the related record are dumped into the index.

.. code-block:: python

    # Your database model defines a foreign key to the related model.
    class MyRecordModel(db.Model, RecordMetadataBase):
        # FK:
        user_id = db.Column(UserModel.id, ..., db.ForeignKey(...))

    class MyRecord(Record)

        # The database model used by the record.
        model_cls = MyRecordModel

        # System field defining the related_id as a model attribute (and
        # ensuring the id is dumped to the index).
        user_id = ModelField("user_id")

        # System field defining the relation
        relations = RelationsField(
            related=ModelRelation(
                # The related record class.
                UserRecord,
                # The attribute name of the ModelField.
                'user_id',
                # Top-level key to dump in index
                'user',
                # Attributes to dump (in addition to id)
                keys=['email', 'username', 'profile'],
            )
"""

from .errors import InvalidRelationValue
from .relations import RelationBase
from .results import RelationResult


class ModelRelationResult(RelationResult):
    """Result class for a model relation."""

    def _lookup_id(self):
        return getattr(self.record, self.field._model_field_name)

    def validate(self):
        """Validate relation."""
        # The relation is validated via database-level foreign key constraints.
        return True

    def dereference(self, keys=None, attrs=None):
        """Dereference the relation field object inside the record."""
        # Prepare the record dictionary to look like: {'id': ...}
        if self.field.key not in self.record:
            id_ = self._lookup_id()
            if id_ is None:
                return None
            else:
                self.record[self.field.key] = {self.field._value_key_suffix: str(id_)}

        data = self.record[self.field.key]
        return self._dereference_one(data, keys or self.keys, attrs or self.attrs)

    def clean(self, keys=None, attrs=None):
        """Clean the record."""
        # Don't store anything inside the record committed to the database.
        self.record.pop(self.field.key, None)


class ModelRelation(RelationBase):
    """Define a relation stored as a foreign key on the record's model."""

    result_cls = ModelRelationResult

    def __init__(self, record_cls, model_field_name, key, keys=None, attrs=None):
        """Constructor."""
        self._record_cls = record_cls
        self._model_field_name = model_field_name
        super().__init__(key=key, keys=keys, attrs=attrs)

    def resolve(self, id_):
        """Get the related object."""
        return self._record_cls.get_record(id_)

    def parse_value(self, value):
        """Extract id from object being set on relation."""
        if isinstance(value, self._record_cls):
            return value.id
        elif isinstance(value, self._record_cls.model_cls):
            return value.id
        else:
            raise InvalidRelationValue(
                f"Invalid value. Expected {self._record_cls} or "
                f"{self._record_cls.model_cls}"
            )

    def set_value(self, record, value):
        """Set an related object."""
        store_value = self.parse_value(value)
        # The existence of the related object is checked via database-level
        # foreign key constraints.
        setattr(record, self._model_field_name, store_value)

    def get_value(self, record):
        """Return the resolved relation from a record."""
        return self.result_cls(self, record)

    def clear_value(self, record):
        """Clear the relation."""
        setattr(record, self._model_field_name, None)
