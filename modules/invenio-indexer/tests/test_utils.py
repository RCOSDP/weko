# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test API."""

from unittest.mock import patch

import pytest

from invenio_indexer.utils import schema_to_index


def test_schema_to_index_with_names(app):
    """Test that prefix is added to the index when creating it."""
    result = schema_to_index("default.json", index_names=["default"])
    assert result == "default"


@pytest.mark.parametrize(
    ("schema, expected, index_names"),
    (
        (
            "records/record-v1.0.0.json",
            "records-record-v1.0.0",
            None,
        ),
        (
            "/records/record-v1.0.0.json",
            "records-record-v1.0.0",
            None,
        ),
        (
            "default-v1.0.0.json",
            "default-v1.0.0",
            None,
        ),
        (
            "default-v1.0.0.json",
            None,
            [],
        ),
        (
            "invalidextension",
            None,
            None,
        ),
    ),
)
def test_schema_to_index(schema, expected, index_names, app):
    """Test the expected value of schema to index."""
    result = schema_to_index(schema, index_names=index_names)
    assert result == expected
