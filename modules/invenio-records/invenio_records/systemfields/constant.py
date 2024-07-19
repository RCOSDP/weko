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


class ConstantField(SystemField):
    """Constant fields add a constant value to a key in the record."""

    def __init__(self, key=None, value=""):
        """Initialize the field.

        :param key: The key to set in the dictionary (dot notation supported
                    for nested lookup).
        :param value: The value to set for the key.
        """
        self.value = value
        super().__init__(key=key)

    def pre_init(self, record, data, model=None, **kwargs):
        """Sets the key in the record during record instantiation."""
        if data is None:
            # A deleted record.
            return
        try:
            dict_lookup(data, self.key)
        except KeyError:
            # Key is not present, so add it.
            data[self.key] = self.value

    def __get__(self, record, owner=None):
        """Accessing the attribute."""
        # Class access
        if record is None:
            return self
        # Instance access
        try:
            return dict_lookup(record, self.key)
        except KeyError:
            return None
