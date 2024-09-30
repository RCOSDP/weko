# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Related model field.

The related model field serializes/dumps a related object into the record JSON
dictionary (basically denormalization). This way, the object can be recreated
directly from the record JSON dictionary instead of querying the database.

This is useful for instance during search queries to avoid hitting the
database. In addition you can subclass this field to provide life-cycle hooks
on the record. For instance a PIDField, could create the related persistent
identifier.
"""

from invenio_db import db
from sqlalchemy import inspect

from .base import SystemField, SystemFieldContext


class RelatedModelFieldContext(SystemFieldContext):
    """Context for RelatedModelField.

    This class implements the class-level methods available on a
    RelatedModelField. I.e. when you access the field through the class, for
    instance:

    .. code-block:: python

        Record.myattr.session_merge(record)
    """

    def session_merge(self, record):
        """Merge the PID to the session if not persistent."""
        obj = self.field.obj(record)
        if not inspect(obj).persistent:
            obj = db.session.merge(obj)
            self.field._set_cache(record, obj)


class RelatedModelField(SystemField):
    """Related model system field."""

    def __init__(
        self, model, key=None, required=False, load=None, dump=None, context_cls=None
    ):
        """Initialize the field.

        :param model: Related SQLAlchemy model.
        :param key: Name of key in the record to serialize the related object
            under.
        :param required: Flag to determine if a related object is required on
            record commit time.
        :param load: Callable to load the related object from a JSON object.
        :param dump: Callable to dump the related object as a JSON object.
        :param context_cls: The context class is used to provide additional
            methods on the field itself.
        """
        self._model = model
        self._required = required
        self._load = load or model.load_obj
        self._dump = dump or model.dump_obj
        self._context_cls = context_cls or RelatedModelFieldContext
        super().__init__(key=key)

    #
    # Life-cycle hooks
    #
    def pre_commit(self, record):
        """Called before a record is committed."""
        # Make sure we serialize/dump the related objet on record.commit() time
        # as it might have changed.
        related_obj = getattr(record, self.attr_name)
        if related_obj is not None:
            self.set_obj(record, related_obj)
        elif self._required:
            raise RuntimeError("You must provide a related object.")

    #
    # Helpers
    #
    def obj(self, record):
        """Get the related object.

        Uses a cached object if it exists.

        IMPORTANT: By default, if the object is loaded from the record JSON
        object instead of from the database model, it is NOT added to the
        database session. Thus, the related object will be in a transient state
        instead of persistent state. This is useful for instance in search
        queries to avoid hitting the database, however if you need to make
        operations on it you should add it to the session using:

        .. code-block::

            Record.myattr.session_merge(record)
        """
        # Check cache
        obj = self._get_cache(record)
        if obj:
            return obj

        obj = self._load(self, record)
        if obj:
            # Cache object
            self._set_cache(record, obj)
            return obj
        return None

    def set_obj(self, record, obj):
        """Set the object."""
        assert isinstance(obj, self._model)

        # Store data values on the attribute name (e.g. 'type') using dump
        # method provided by either to the field or a function on the related
        # object.
        self._dump(self, record, obj)

        # Cache object
        self._set_cache(record, obj)

    #
    # Data descriptor methods (i.e. attribute access)
    #
    def __get__(self, record, owner=None):
        """Get the persistent identifier."""
        if record is None:
            return self._context_cls(self, owner)
        return self.obj(record)

    def __set__(self, record, pid):
        """Set persistent identifier on record."""
        self.set_obj(record, pid)
