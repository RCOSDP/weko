# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Search source dumper.

Dumper used to dump/load an the body of an Search document.
"""

from datetime import datetime
from uuid import UUID

import arrow
import pytz
from invenio_db import db
from sqlalchemy.sql.sqltypes import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.sql.type_api import Variant
from sqlalchemy_utils.types.uuid import UUIDType

from ..systemfields.model import ModelField
from .base import Dumper


class SearchDumperExt:
    """Interface for Search dumper extensions."""

    def dump(self, record, data):
        """Dump the data."""

    def load(self, data, record_cls):
        """Load the data.

        Reverse the changes made by the dump method.
        """


class SearchDumper(Dumper):
    """Search source dumper."""

    def __init__(self, extensions=None, model_fields=None):
        """."""
        self._extensions = extensions or []
        self._model_fields = {
            "id": ("uuid", UUID),
            "version_id": ("version_id", int),
            "created": ("created", datetime),
            "updated": ("updated", datetime),
            # is_deleted is purposely not added (deleted record isnt indexed)
        }
        self._model_fields.update(model_fields or {})

    @staticmethod
    def _sa_type(model_cls, model_field_name):
        """Introspection of SQLAlchemy column data type.

        :param model_cls: The SQLALchemy model.
        :param model_field_name: The name of the field on the SQLAlchemy model.
        """
        try:
            sa_type = model_cls.__table__.columns[model_field_name].type
            sa_type_class = sa_type.__class__

            # Deal with variant class
            if issubclass(sa_type_class, Variant):
                sa_type = sa_type.impl
                sa_type_class = sa_type.__class__

            if issubclass(sa_type_class, DateTime):
                return datetime
            elif issubclass(sa_type_class, Boolean):
                return bool
            elif issubclass(sa_type_class, Integer):
                return int
            elif issubclass(sa_type_class, UUIDType):
                return UUID
            elif issubclass(sa_type_class, String):
                return str
            elif issubclass(sa_type_class, JSON):
                return dict
            return None
        except (KeyError, AttributeError):
            return None

    @staticmethod
    def _serialize(value, dump_type):
        """Serialize a value according to it's data type.

        :param value: Value to serialize.
        :param dump_type: Data type use for serialization (supported: str, int,
            bool, float, datetime, date, uuid).
        """
        if value is None:
            return value
        if dump_type in (datetime,):
            return pytz.utc.localize(value).isoformat()
        elif dump_type in (UUID,):
            return str(value)
        elif dump_type is not None:
            return dump_type(value)
        return value

    @staticmethod
    def _deserialize(value, dump_type):
        """Deserialize a value according to it's data type.

        :param value: Value to deserialize.
        :param dump_type: Data type use for deserialization (supported: str,
            int, bool, float, datetime, date, uuid).
        """
        if value is None:
            return value
        if dump_type in (datetime,):
            return arrow.get(value).datetime.replace(tzinfo=None)
        elif dump_type in (UUID,):
            return dump_type(value)
        elif dump_type is not None:
            return dump_type(value)
        return value

    def _dump_model_field(self, record, model_field_name, dump, dump_key, dump_type):
        """Helper method to dump model fields.

        :param record: The record being dumped.
        :param model_field_name: The name of the SQLAlchemy model field on the
            record's model.
        :param dump: The dictionary of the current dump.
        :param dump_key: The key to use in the dump.
        :param dump_type: The data type used for serialization.
        """
        # If model is not defined, we dump None into the field value.
        if record.model is None:
            dump[dump_key] = None
            return
        with db.session.no_autoflush:
            # Retrieve value of the field on the model.
            val = getattr(record.model, model_field_name)

        # Determine data type if not set.
        if dump_type is None:
            dump_type = self._sa_type(record.model_cls, model_field_name)

        # Serialize (according to data type) and set value in output on the
        # specified key.
        dump[dump_key] = self._serialize(val, dump_type)

    def _load_model_field(
        self, record_cls, model_field_name, dump, dump_key, dump_type
    ):
        """Helper method to load model fields from dump.

        :param record_cls: The record class being used for loading.
        :param model_field_name: The name of the SQLAlchemy model field on the
            record's model.
        :param dump: The dictionary of the dump.
        :param dump_key: The key to use in the dump.
        :param dump_type: The data type used for deserialization.
        """
        # Retrieve the value
        val = dump.pop(dump_key)

        # Return None values immediately.
        if val is None:
            return val

        # Determine dump data type if not provided
        if dump_type is None:
            sa_field = getattr(record_cls.model_cls, model_field_name)
            dump_type = self._sa_type(record_cls.model_cls, model_field_name)

        # Deserialize the value
        return self._deserialize(val, dump_type)

    @staticmethod
    def _iter_modelfields(record_cls):
        """Internal helper method to extract all model fields."""
        for attr_name in dir(record_cls):
            systemfield = getattr(record_cls, attr_name)
            if isinstance(systemfield, ModelField):
                if systemfield.dump:
                    yield systemfield

    def dump(self, record, data):
        """Dump a record.

        The method adds the following keys (if the record has an associated
        model):

        - ``uuid`` - UUID of the record.
        - ``version_id`` -  the revision id of the record.
        - ``created`` - Creation timestamp in UTC.
        - ``updated`` - Modification timestamp in UTC.
        """
        # Copy data first, otherwise we modify the record.
        dump_data = super().dump(record, data)

        # Dump model fields explicitly requested
        it = self._model_fields.items()
        for model_field_name, (dump_key, dump_type) in it:
            self._dump_model_field(
                record,
                model_field_name,
                dump_data,
                dump_key,
                dump_type,
            )

        # Dump model fields defined as system fields.
        for systemfield in self._iter_modelfields(record.__class__):
            self._dump_model_field(
                record,
                systemfield.model_field_name,
                dump_data,
                systemfield.dump_key,
                systemfield.dump_type,
            )

        # Allow extensions to integrate as well.
        for e in self._extensions:
            e.dump(record, dump_data)

        return dump_data

    def load(self, dump_data, record_cls):
        """Load a record from an Search document source.

        The method reverses the changes made during the dump. If a model was
        associated, a model will also be initialized.

        .. warning::
            The model is not added to the SQLAlchemy session. If you plan on
            using the model, you must merge it into the session using e.g.:

            .. code-block:: python

                db.session.merge(record.model)
        """
        # First allow extensions to modify the data.
        for e in self._extensions:
            e.load(dump_data, record_cls)

        # Load explicitly defined model fields.
        model_data = {}
        it = self._model_fields.items()
        for model_field_name, (dump_key, dump_type) in it:
            model_data[model_field_name] = self._load_model_field(
                record_cls, model_field_name, dump_data, dump_key, dump_type
            )

        # Load model fields defined as system fields
        for systemfield in self._iter_modelfields(record_cls):
            model_data[systemfield.model_field_name] = self._load_model_field(
                record_cls,
                systemfield.model_field_name,
                dump_data,
                systemfield.dump_key,
                systemfield.dump_type,
            )

        # Initialize model if an id was provided.
        if model_data.get("id") is not None:
            model_data["data"] = dump_data
            model = record_cls.model_cls(**model_data)
        else:
            model = None

        return record_cls(dump_data, model=model)
