# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2022 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Validated dictionary classes for user profiles and preferences."""

from inspect import isclass

from invenio_base.utils import load_or_import_from_config
from marshmallow import ValidationError


class ValidatedDict(dict):
    """A dictionary class that validates itself when properties are set."""

    def __init__(self, schema, *args, **kwargs):
        """Constructor, validates the given data."""
        self._schema = schema() if isclass(schema) else schema
        self._validate(dict(*args, **kwargs))
        super().__init__(*args, **kwargs)

    def _validate(self, data):
        """Validate the data with the dictionary's schema."""
        try:
            if self._schema is not None:
                # without schema, we basically revert to a normal dictionary
                # with more overhead
                self._schema.load(data)
        except ValidationError as error:
            raise ValueError(f"Validation failed: {error}")

    def _try_op(self, op_name, *args, **kwargs):
        """Try the named operation and see if it violates the schema."""
        data = {**self}
        getattr(data, op_name)(*args, **kwargs)
        self._validate(data)

    def clear(self):
        """Remove all items from the dictionary."""
        self._validate({})
        return super().clear()

    def pop(self, key, default=None):
        """Remove specified key and return the corresponding value."""
        self._try_op("pop", key, default)
        return super().pop(key, default)

    def popitem(self, *args, **kwargs):
        """Remove and return a (key, value) pair as a 2-tuple."""
        self._try_op("popitem", *args, **kwargs)
        return super().popitem(*args, **kwargs)

    def update(self, e, **f):
        """Update the dict from dict/iterable e and f."""
        self._try_op("update", e, **f)
        return super().update(e, **f)

    def setdefault(self, key, default=None):
        """Insert key with a value of default if key is not in the dict."""
        self._try_op("setdefault", key, default)
        return super().setdefault(key, default)

    def __setitem__(self, key, value):
        """Validate the dictionary and set the value if successful."""
        data = {**self, key: value}
        self._validate(data)
        super().__setitem__(key, value)

    def __delitem__(self, key):
        """Validate the dictionary and delete the key if successful."""
        data = {**self}
        del data[key]
        self._validate(data)
        super().__delitem__(key)


class UserProfileDict(ValidatedDict):
    """Dictionary that validates itself against the user profile schema."""

    def __init__(self, **kwargs):
        """Constructor."""
        schema = load_or_import_from_config("ACCOUNTS_USER_PROFILE_SCHEMA")
        super().__init__(schema, **kwargs)


class UserPreferenceDict(ValidatedDict):
    """Dictionary that validates itself against the preference schema."""

    def __init__(self, **kwargs):
        """Constructor."""
        schema = load_or_import_from_config("ACCOUNTS_USER_PREFERENCES_SCHEMA")
        super().__init__(schema, **kwargs)
