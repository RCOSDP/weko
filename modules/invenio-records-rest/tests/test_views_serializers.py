# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Default serializer tests."""

import json

import pytest
from flask import current_app


def json_record(*args, **kwargs):
    """Test serializer."""
    return current_app.response_class(
        json.dumps({"json_record": "json_record"}), content_type="application/json"
    )


def xml_record(*args, **kwargs):
    """Test serializer."""
    return current_app.response_class(
        "<record>TEST</record>", content_type="application/xml"
    )


def json_search(pid_fetcher, search_result, **kwargs):
    """Test serializer."""
    return current_app.response_class(
        json.dumps([{"test": "test"}, search_result["hits"]["total"]]),
        content_type="application/json",
    )


def xml_search(*args, **kwargs):
    """Test serializer."""
    return current_app.response_class(
        "<collection><record>T1</record><record>T2</record></collection>",
        content_type="application/xml",
    )


@pytest.mark.parametrize(
    "app",
    [
        dict(
            endpoint=dict(
                record_serializers={
                    "application/json": "test_views_serializers:json_record",
                    "application/xml": "test_views_serializers.xml_record",
                },
                search_serializers={
                    "application/json": "test_views_serializers:json_search",
                    "application/xml": "test_views_serializers.xml_search",
                },
                default_media_type="application/xml",
            ),
        )
    ],
    indirect=["app"],
    scope="function",
)
def test_default_serializer(app, db, search, indexed_records):
    """Test default serializer."""
    # Create records
    accept_json = [("Accept", "application/json")]
    accept_xml = [("Accept", "application/xml")]

    with app.test_client() as client:
        res = client.get("/records/", headers=accept_json)
        assert res.status_code == 200
        assert res.content_type == "application/json"

        res = client.get("/records/", headers=accept_xml)
        assert res.status_code == 200
        assert res.content_type == "application/xml"

        res = client.get("/records/")
        assert res.status_code == 200
        assert res.content_type == "application/xml"

        res = client.get("/records/1", headers=accept_json)
        assert res.status_code == 200
        assert res.content_type == "application/json"

        res = client.get("/records/1", headers=accept_xml)
        assert res.status_code == 200
        assert res.content_type == "application/xml"

        res = client.get("/records/1")
        assert res.status_code == 200
        assert res.content_type == "application/xml"


@pytest.mark.parametrize(
    "app",
    [
        dict(
            endpoint=dict(
                record_serializers={
                    "application/json": "test_views_serializers:json_record",
                    "application/xml": "test_views_serializers.xml_record",
                },
                record_serializers_aliases={
                    "get-json": "application/json",
                },
                search_serializers={
                    "application/json": "test_views_serializers:json_search",
                    "application/xml": "test_views_serializers.xml_search",
                },
                search_serializers_aliases={
                    "list-json": "application/json",
                },
                default_media_type="application/xml",
            ),
        )
    ],
    indirect=["app"],
    scope="function",
)
def test_serializer_aliases(app, db, search, indexed_records):
    """Test serializers aliases."""
    with app.test_client() as client:
        res = client.get("/records/")
        assert res.status_code == 200
        assert res.content_type == "application/xml"

        res = client.get("/records/?format=list-json")
        assert res.status_code == 200
        assert res.content_type == "application/json"

        res = client.get("/records/1")
        assert res.status_code == 200
        assert res.content_type == "application/xml"

        res = client.get("/records/1?format=get-json")
        assert res.status_code == 200
        assert res.content_type == "application/json"
