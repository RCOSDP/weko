# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2021-2024 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Tests Invenio-Records JSONSchema ref resolver."""

import pytest

from invenio_records.api import Record
from invenio_records.resolver import urljoin_with_custom_scheme


def local_ref_resolver_store_factory():
    """Build local JSONSchema ref resolver store."""
    return {
        "local://authors.json": {
            "$id": "local://authors.json",
            "type": "array",
            "items": {"type": "string"},
        },
        "local://books.json": {
            "$id": "local://books.json",
            "type": "object",
            "definitions": {
                "price": {
                    "type": "string",
                },
            },
            "properties": {
                "title": {"type": "string"},
                "price": {"$ref": "#/definitions/price"},
                "authors": {"$ref": "local://authors.json"},
            },
        },
    }


@pytest.fixture(scope="module")
def app_config(app_config):
    app_config["RECORDS_REFRESOLVER_CLS"] = (
        "invenio_records.resolver.InvenioRefResolver"
    )
    app_config["RECORDS_REFRESOLVER_STORE"] = local_ref_resolver_store_factory()
    return app_config


def test_invenio_refresolver_with_local_store(db):
    """Test InvenioRefResolver with local store and complex JSONSchema."""
    data = {
        "$schema": "local://books.json#",
        "title": "The Lord of the Rings",
        "price": "20",
        "authors": [
            "J. R. R. Tolkien",
        ],
    }
    Record.create(data).commit()
    db.session.commit()


@pytest.mark.parametrize(
    "resolution_scope, scope, expected_output",
    [
        # Custom scheme simple cases
        ("local://books.json", "local://books.json#", "local://books.json"),
        ("local://books.json#", "local://books.json", "local://books.json"),
        ("local://books.json#", "#", "local://books.json"),
        # Custom scheme with internal refs
        (
            "local://books.json",
            "local://books.json#/definitions/price",
            "local://books.json#/definitions/price",
        ),
        (
            "local://books.json",
            "#/definitions/price",
            "local://books.json#/definitions/price",
        ),
    ],
)
def test_urljoin_with_custom_scheme(resolution_scope, scope, expected_output):
    """Test urljoin supporting custom schemas."""
    assert urljoin_with_custom_scheme(resolution_scope, scope) == expected_output
