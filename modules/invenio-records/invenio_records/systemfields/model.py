# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Constant system field."""

from ..dictutils import dict_lookup
from .base import SystemField


class ModelField(SystemField):
    """Model field for providing get and set access on a model field."""

    def __init__(
        self, model_field_name=None, dump=True, dump_key=None, dump_type=None, **kwargs
    ):
        """Initialize the field.

        :param model_field_name: Name of field on the database model.
        :param dump: Set to false to not dump the field.
        :param dump_key: The dictionary key to use in dumps.
        :param dump_type: The data type used to determine how to serialize the
            model field.
        """
        self._model_field_name = model_field_name
        self.dump = dump
        self._dump_key = dump_key
        self._dump_type = dump_type
        super().__init__(**kwargs)

    #
    # Helpers
    #
    @property
    def model_field_name(self):
        """The name of the SQLAlchemy field on the model.

        Defaults to the attribute name used on the class.
        """
        return self._model_field_name or self.attr_name

    @property
    def dump_key(self):
        """The dictionary key to use in dump output.

        Note, it's up to the dumper to choose if it respects this name.
        The name defaults to the model field name.
        """
        return self._dump_key or self.model_field_name

    @property
    def dump_type(self):
        """The data type used to determine how to serialize the model field.

        Defaults to none, meaning the dumper will determine how to dump it.
        """
        return self._dump_type

    def _set(self, model, value):
        """Internal method to set value on the model's field."""
        setattr(model, self.model_field_name, value)

    #
    # Data descriptor
    #
    def __get__(self, record, owner=None):
        """Accessing the attribute."""
        # Class access
        if record is None:
            return self
        # Instance access
        try:
            return getattr(record.model, self.model_field_name)
        except AttributeError:
            return None

    def __set__(self, instance, value):
        """Accessing the attribute."""
        self._set(instance.model, value)

    #
    # Record extension
    #
    def post_init(self, record, data, model=None, field_data=None):
        """Initialise the model field."""
        if field_data is not None:
            self._set(model, field_data)
