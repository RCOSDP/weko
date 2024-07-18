# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C)      2022 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Tests for the user profile utilities."""

import pytest
from marshmallow import Schema, fields

from invenio_accounts.profiles.dicts import ValidatedDict


class RequiredFieldSchema(Schema):
    """Schema with one optional and one required field."""

    optional = fields.String(required=False)
    required = fields.String(required=True)


class OptionalFieldsSchema(Schema):
    """Schema with only one optional field."""

    optional = fields.String()


def test_validated_dict_required_fields():
    """Test if the removal of required fields fails."""
    # we can leave out the optional field
    dictionary = ValidatedDict(RequiredFieldSchema, required="ok")
    assert "required" in dictionary
    assert "optional" not in dictionary

    # removal of the required field shouldn't work...
    with pytest.raises(ValueError):
        dictionary.pop("required", None)

    with pytest.raises(ValueError):
        del dictionary["required"]

    with pytest.raises(ValueError):
        dictionary.clear()

    # we can't leave out the required field
    with pytest.raises(ValueError):
        ValidatedDict(RequiredFieldSchema, optional="ok")


def test_validated_dict_optional_fields():
    """Test if we can delete optional fields."""
    # test a few ways of deleting optional fields
    dictionary = ValidatedDict(OptionalFieldsSchema, optional="ok")
    assert dictionary
    dictionary.pop("optional", None)
    assert not dictionary

    dictionary = ValidatedDict(OptionalFieldsSchema, optional="ok")
    del dictionary["optional"]
    assert not dictionary

    dictionary = ValidatedDict(OptionalFieldsSchema, optional="ok")
    dictionary.clear()
    assert not dictionary

    dictionary = ValidatedDict(OptionalFieldsSchema, optional="ok")


def test_validated_dict():
    """A few general tests for the validated dictionary."""
    # unexpected values should raise an error
    with pytest.raises(ValueError):
        ValidatedDict(OptionalFieldsSchema, required="ok")

    # setting wrong types should raise an error
    with pytest.raises(ValueError):
        ValidatedDict(OptionalFieldsSchema, optional=123)

    # update should work...
    dictionary = ValidatedDict(OptionalFieldsSchema)
    assert "optional" not in dictionary
    dictionary.update({"optional": "yes"})
    assert dictionary["optional"] == "yes"

    # ... but not with a wrong type
    with pytest.raises(ValueError):
        dictionary.update({"optional": False})

    # setdefault should work as expected
    dictionary = ValidatedDict(RequiredFieldSchema, required="ok")
    assert "optional" not in dictionary
    dictionary.setdefault("optional", "yes")
    assert dictionary["optional"] == "yes"
    dictionary.setdefault("optional", "no")
    assert dictionary["optional"] == "yes"

    # setting values per key should also work
    dictionary["required"] = "absolutely"
    assert dictionary["required"] == "absolutely"
    with pytest.raises(ValueError):
        dictionary["required"] = None
