# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020-2024 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test of dictionary utilities."""

from copy import deepcopy

import pytest

from invenio_records.dictutils import (
    clear_none,
    dict_lookup,
    dict_merge,
    filter_dict_keys,
)


def test_clear_none():
    """Test clearning of the dictionary."""
    d = {
        "a": None,
        "b": {"c": None},
        "d": ["1", None, []],
        "e": [{"a": None, "b": []}],
    }

    clear_none(d)
    # Modifications are done in place, so gotta test after the function call.
    assert d == {"d": ["1"]}

    d = {
        "a": None,
        "b": [
            {"a": "1", "b": None},
        ],
    }
    clear_none(d)
    # Modifications are done in place, so gotta test after the function call.
    assert d == {"b": [{"a": "1"}]}


def test_dict_lookup():
    """Test lookup by a key."""
    d = {
        "a": 1,
        "b": {"c": None},
        "d": ["1", "2"],
    }
    assert dict_lookup(d, "a") == d["a"]
    assert dict_lookup(d, "b") == d["b"]
    assert dict_lookup(d, "b.c") == d["b"]["c"]
    assert dict_lookup(d, "d") == d["d"]
    assert dict_lookup(d, "d.0") == d["d"][0]
    assert dict_lookup(d, "d.1") == d["d"][1]
    assert dict_lookup(d, "d.-1") == d["d"][-1]

    assert pytest.raises(KeyError, dict_lookup, d, "x")
    assert pytest.raises(KeyError, dict_lookup, d, "a.x")
    assert pytest.raises(KeyError, dict_lookup, d, "b.x")
    assert pytest.raises(KeyError, dict_lookup, d, "b.c.0")
    assert pytest.raises(KeyError, dict_lookup, d, "d.3")


def test_dict_merge():
    """Test dict merge."""
    dest = dict()
    source = dict(foo="bar")
    dict_merge(dest, source)

    assert dest == dict(foo="bar")

    dest = {"foo1": "bar1", "metadata": {"field1": 3}}
    source = {"foo2": "bar2", "metadata": {"field2": "test"}}
    dict_merge(dest, source)

    assert dest == {
        "foo1": "bar1",
        "foo2": "bar2",
        "metadata": {"field1": 3, "field2": "test"},
    }


def test_filter_dict_keys():
    """Test filter dict keys."""
    source = {
        "foo1": {"bar1": 1, "bar2": 2},
        "foo2": 1,
        "foo3": {"bar1": {"foo4": 0}, "bar2": 1, "bar3": 2},
        "foo4": {},
    }

    assert filter_dict_keys(
        source, ["foo1.bar1", "foo2", "foo3.bar1.foo4", "foo3.bar3"]
    ) == {"foo1": {"bar1": 1}, "foo2": 1, "foo3": {"bar1": {"foo4": 0}, "bar3": 2}}
