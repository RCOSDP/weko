# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Facets tests."""

import pytest
from flask import Flask
from invenio_rest.errors import RESTValidationError
from invenio_search.engine import dsl
from werkzeug.datastructures import MultiDict

from invenio_records_rest.facets import (
    _aggregations,
    _create_filter_dsl,
    _post_filter,
    _query_filter,
    default_facets_factory,
    range_filter,
    terms_filter,
)


def test_terms_filter():
    """Test terms filter."""
    f = terms_filter("test")
    assert f(["a", "b"]).to_dict() == dict(terms={"test": ["a", "b"]})


def test_range_filter():
    """Test range filter."""
    f = range_filter("test", start_date_math="startmath", end_date_math="endmath")
    assert f(["1821--1940"]) == dsl.query.Range(
        test={
            "gte": "1821||startmath",
            "lte": "1940||endmath",
        }
    )
    assert f([">1821--"]) == dsl.query.Range(test={"gt": "1821||startmath"})
    assert f(["1821--<1940"]) == dsl.query.Range(
        test={"gte": "1821||startmath", "lt": "1940||endmath"}
    )

    assert pytest.raises(RESTValidationError, f, ["2016"])
    assert pytest.raises(RESTValidationError, f, ["--"])


def test_create_filter_dsl():
    """Test request value extraction."""
    app = Flask("testapp")
    kwargs = MultiDict([("a", "1")])
    defs = dict(
        type=terms_filter("type.type"),
        subtype=terms_filter("type.subtype"),
    )

    with app.test_request_context("?type=a&type=b&subtype=c&type=zażółcić"):
        filters, args = _create_filter_dsl(kwargs, defs)
        assert len(filters) == 2
        assert args == MultiDict(
            [
                ("a", "1"),
                ("type", "a"),
                ("type", "b"),
                ("subtype", "c"),
                ("type", "zażółcić"),
            ]
        )

    kwargs = MultiDict([("a", "1")])
    with app.test_request_context("?atype=a&atype=b"):
        filters, args = _create_filter_dsl(kwargs, defs)
        assert not filters
        assert args == kwargs


def test_post_filter(app):
    """Test post filter."""
    urlargs = MultiDict()
    defs = dict(
        type=terms_filter("type"),
        subtype=terms_filter("subtype"),
    )

    with app.test_request_context("?type=test"):
        search = dsl.Search().query(dsl.Q(query="value"))
        search, args = _post_filter(search, urlargs, defs)
        assert "post_filter" in search.to_dict()
        assert search.to_dict()["post_filter"] == dict(terms=dict(type=["test"]))
        assert args["type"] == "test"

    with app.test_request_context("?anotertype=test"):
        search = dsl.Search().query(dsl.Q(query="value"))
        search, args = _post_filter(search, urlargs, defs)
        assert "post_filter" not in search.to_dict()


def test_query_filter(app):
    """Test post filter."""
    urlargs = MultiDict()
    defs = dict(
        type=terms_filter("type"),
        subtype=terms_filter("subtype"),
    )

    with app.test_request_context("?type=test"):
        search = dsl.Search().query(dsl.Q("multi_match", query="value"))
        body = search.to_dict()
        search, args = _query_filter(search, urlargs, defs)
        assert "post_filter" not in search.to_dict()
        assert search.to_dict()["query"]["bool"]["must"][0] == body["query"]
        assert search.to_dict()["query"]["bool"]["filter"] == [
            dict(terms=dict(type=["test"]))
        ]
        assert args["type"] == "test"

    with app.test_request_context("?anotertype=test"):
        search = dsl.Search().query(dsl.Q(query="value"))
        body = search.to_dict()
        query, args = _query_filter(search, urlargs, defs)
        assert query.to_dict() == body


def test_aggregations(app):
    """Test aggregations."""
    with app.test_request_context(""):
        search = dsl.Search().query(dsl.Q(query="value"))
        defs = dict(
            type=dict(
                terms=dict(field="upload_type"),
            ),
            subtype=dict(
                terms=dict(field="subtype"),
            ),
        )
        assert _aggregations(search, defs).to_dict()["aggs"] == defs


def test_default_facets_factory(app):
    """Test aggregations."""
    defs = dict(
        aggs=dict(
            type=dict(
                terms=dict(field="upload_type"),
            ),
            subtype=dict(
                terms=dict(field="subtype"),
            ),
        ),
        filters=dict(
            subtype=terms_filter("subtype"),
        ),
        post_filters=dict(
            type=terms_filter("type"),
        ),
    )
    app.config["RECORDS_REST_FACETS"]["testidx"] = defs
    with app.test_request_context("?type=a&subtype=b"):
        search = dsl.Search().query(dsl.Q(query="value"))
        search, urlkwargs = default_facets_factory(search, "testidx")
        assert search.to_dict()["aggs"] == defs["aggs"]
        assert "post_filter" in search.to_dict()
        assert search.to_dict()["query"]["bool"]["filter"][0]["terms"]["subtype"]

        search = dsl.Search().query(dsl.Q(query="value"))
        search, urlkwargs = default_facets_factory(search, "anotheridx")
        assert "aggs" not in search.to_dict()
        assert "post_filter" not in search.to_dict()
        assert "bool" not in search.to_dict()["query"]


def test_selecting_one_specified_facet(app):
    defs = dict(
        aggs=dict(
            facet_1=dict(
                terms=dict(field="one_field"),
            ),
            facet_2=dict(
                terms=dict(field="other_field"),
            ),
            facet_3=dict(terms=dict(field="some_other_field")),
        ),
        filters=dict(
            subtype=terms_filter("subtype"),
        ),
        post_filters=dict(
            type=terms_filter("type"),
        ),
    )

    expected_agg = dict(facet_2=dict(terms=dict(field="other_field")))
    app.config["RECORDS_REST_FACETS"]["test_facet_names"] = defs
    with app.test_request_context("?type=a&subtype=b&facets=facet_2"):
        search = dsl.Search().query(dsl.Q(query="value"))
        search, urlkwargs = default_facets_factory(search, "test_facet_names")
        assert search.to_dict().get("aggs") == expected_agg


def test_selecting_specified_facet(app):
    defs = dict(
        aggs=dict(
            facet_1=dict(
                terms=dict(field="one_field"),
            ),
            facet_2=dict(
                terms=dict(field="other_field"),
            ),
            facet_3=dict(terms=dict(field="some_other_field")),
        ),
        filters=dict(
            subtype=terms_filter("subtype"),
        ),
        post_filters=dict(
            type=terms_filter("type"),
        ),
    )

    expected_agg = dict(
        facet_1=dict(
            terms=dict(field="one_field"),
        ),
        facet_3=dict(terms=dict(field="some_other_field")),
    )
    app.config["RECORDS_REST_FACETS"]["test_facet_names"] = defs
    with app.test_request_context("?type=a&subtype=b&facets=facet_1,facet_3"):
        search = dsl.Search().query(dsl.Q(query="value"))
        search, urlkwargs = default_facets_factory(search, "test_facet_names")
        assert search.to_dict().get("aggs") == expected_agg


def test_turn_off_facets(app):
    defs = dict(
        aggs=dict(
            facet_1=dict(
                terms=dict(field="one_field"),
            ),
            facet_2=dict(
                terms=dict(field="other_field"),
            ),
            facet_3=dict(terms=dict(field="some_other_field")),
        ),
        filters=dict(
            subtype=terms_filter("subtype"),
        ),
        post_filters=dict(
            type=terms_filter("type"),
        ),
    )

    app.config["RECORDS_REST_FACETS"]["test_facet_names"] = defs
    with app.test_request_context("?type=a&subtype=b&facets=null"):
        search = dsl.Search().query(dsl.Q(query="value"))
        search, urlkwargs = default_facets_factory(search, "test_facet_names")
        assert search.to_dict().get("aggs") is None


def test_selecting_all_facets_by_default(app):
    defs = dict(
        aggs=dict(
            facet_1=dict(
                terms=dict(field="one_field"),
            ),
            facet_2=dict(
                terms=dict(field="other_field"),
            ),
            facet_3=dict(terms=dict(field="some_other_field")),
        ),
        filters=dict(
            subtype=terms_filter("subtype"),
        ),
        post_filters=dict(
            type=terms_filter("type"),
        ),
    )

    expected_agg = defs["aggs"]
    app.config["RECORDS_REST_FACETS"]["test_facet_names"] = defs
    with app.test_request_context("?type=a&subtype=b"):
        search = dsl.Search().query(dsl.Q(query="value"))
        search, urlkwargs = default_facets_factory(search, "test_facet_names")
        assert search.to_dict().get("aggs") == expected_agg
