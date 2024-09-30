# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Search tests."""

import re

import pytest
from flask import url_for, current_app
from helpers import assert_hits_len, get_json, parse_url, to_relative_url
from mock import patch

from invenio_accounts.testutils import login_user_via_session
def test_json_result_serializer(app, indexed_10records, search_url, admin_settings):
    """JSON result."""
    with app.test_client() as client:
        # Get a query with only one record
        res = client.get(search_url, query_string={"q": "control_number:3"})
        assert_hits_len(res, 1)
        assert res.status_code == 200

        # Check serialization of record
        record = get_json(res)["hits"]["hits"][0]

        for k in ["id", "created", "updated", "metadata", "links"]:
            assert k in record

        pid, db_record = indexed_10records[0]
        assert record["id"] == pid.pid_value
        db_record_dump = db_record.dumps()
        for k in ["title", "control_number"]:
            assert record["metadata"][k] == db_record_dump[k]


def test_page_size(app, indexed_10records, search_url, admin_settings):
    """Test page and size parameters."""
    with app.test_client() as client:
        # Limit records
        res = client.get(search_url, query_string=dict(page=1, size=2))
        assert_hits_len(res, 2)

        # All records
        res = client.get(search_url, query_string=dict(page=1, size=10))
        assert_hits_len(res, len(indexed_10records))

        # Last page
        res = client.get(search_url, query_string=dict(page=100, size=100))
        assert_hits_len(res, 0)

        # Exceed max result window
        res = client.get(search_url, query_string=dict(page=100, size=101))
        assert res.status_code == 400
        assert "message" in get_json(res)

        res = client.get(search_url, query_string=dict(page=101, size=100))
        assert res.status_code == 400
        assert "message" in get_json(res)


def test_page_size_without_size_in_request(app, indexed_10records, search_url, admin_settings):
    """Test default size parameter."""
    with app.test_client() as client:
        res = client.get(search_url, query_string=dict(page=1))
        assert_hits_len(res, len(indexed_10records))


def test_page_size_without_size_in_request_with_five_as_default(
    app, indexed_10records, search_url, admin_settings
):
    """Test custom default page parameter."""
    config = {"RECORDS_REST_DEFAULT_RESULTS_SIZE": 2}
    with app.test_client() as client, patch.dict(app.config, config):
        res = client.get(search_url, query_string=dict(page=1))
        assert_hits_len(res, 2)

@pytest.mark.parametrize('app', [dict(
    max_result_window=20
)], indirect=['app'])
def test_page_size_exceed_max_result_window(app,indexed_100records, aggs_and_facet, search_user, admin_settings, account_redis, search_url):
    # In this test, max_result_window is set to 20
    email = search_user["email"]
    
    page_cache = email
    args_cache = f"{email}_url_args"
    max_cache = f"{email}_max_result"
    account_redis.delete(page_cache)
    account_redis.delete(args_cache)
    account_redis.delete(max_cache)
    current_app.config["RECORDS_REST_SORT_OPTIONS"][current_app.config["SEARCH_UI_SEARCH_INDEX"]]=dict(
        controlnumber=dict(
            title="ID",
            fields=["control_number"],
            default_order="asc",
            order=2,
        ),
        wtl=dict(
            title="Title",
            fields=["title"],
            default_order="asc",
            order=3,
        ),
        temporal=dict(
            title="Temporal",
            fields=["date_range1.gte"],
            default_order="asc",
            order=12,
        )
    )
        
    import json
    with app.test_client() as client:
        login_user_via_session(client, search_user["obj"])
        
        # The page is the first page where page*size>max_result_window
        res = client.get(search_url, query_string=dict(page=3, size=7))
        res_control_numbers = [d["metadata"]["control_number"] for d in get_json(res)["hits"]["hits"]]
        assert res_control_numbers == ["15", "16", "17", "18", "19", "20", "21"]
        assert json.loads(account_redis.get(page_cache)) == {"3":{"control_number":14.0}}
        assert json.loads(account_redis.get(max_cache)) == {"1":{"control_number":14.0}}

        # cache for page not exists, cache for page-1 exists
        res = client.get(search_url, query_string=dict(page=4, size=7))
        res_control_numbers = [d["metadata"]["control_number"] for d in get_json(res)["hits"]["hits"]]
        assert res_control_numbers == ["22", "23", "24", "25", "26", "27", "28"]
        assert json.loads(account_redis.get(page_cache)) == {"3":{"control_number":14.0},"4":{"control_number":21.0}}
        assert json.loads(account_redis.get(max_cache)) == {"1":{"control_number":14.0}}

        # cache for page exists
        res = client.get(search_url, query_string=dict(page=4, size=7))
        res_control_numbers = [d["metadata"]["control_number"] for d in get_json(res)["hits"]["hits"]]
        assert res_control_numbers == ["22", "23", "24", "25", "26", "27", "28"]
        assert json.loads(account_redis.get(page_cache)) == {"3":{"control_number":14.0},"4":{"control_number":21.0}}
        assert json.loads(account_redis.get(max_cache)) == {"1":{"control_number":14.0}}

        # cache for page-1 not exists, Target does not exist in max_result cache
        res = client.get(search_url, query_string=dict(page=6, size=7))
        res_control_numbers = [d["metadata"]["control_number"] for d in get_json(res)["hits"]["hits"]]
        assert res_control_numbers == ["36", "37", "38", "39", "40", "41", "42"]
        assert json.loads(account_redis.get(page_cache)) == {"3":{"control_number":14.0},"4":{"control_number":21.0},"6":{"control_number":35.0}}
        assert json.loads(account_redis.get(max_cache)) == {"1":{"control_number":14.0},"2":{"control_number":34.0}}
        
        # cache for page-1 not exists, Target exist in max_result cache
        res = client.get(search_url, query_string=dict(page=8, size=7))
        res_control_numbers = [d["metadata"]["control_number"] for d in get_json(res)["hits"]["hits"]]
        assert res_control_numbers == ["50", "51", "52", "53", "54", "55", "56"]
        assert json.loads(account_redis.get(page_cache)) == {"3":{"control_number":14.0},"4":{"control_number":21.0},"6":{"control_number":35.0},"8":{"control_number":49.0}}
        assert json.loads(account_redis.get(max_cache)) == {"1":{"control_number":14.0},"2":{"control_number":34.0}}

        # sort is title, target_index=0
        res = client.get(search_url, query_string=dict(page=5, size=10,sort="wtl"))
        res_control_numbers = [d["metadata"]["control_number"] for d in get_json(res)["hits"]["hits"]]
        assert res_control_numbers == ["45", "46", "47", "48", "49", "5", "50","51","52","53"]
        assert json.loads(account_redis.get(page_cache)) == {"5":{"title":"test_item44", "control_number":44.0}}
        assert json.loads(account_redis.get(max_cache)) == {"1":{"control_number":26.0, "title":"test_item26"}}
        
    account_redis.delete(email)
    account_redis.delete(args_cache)
    account_redis.delete(max_cache)

def test_pagination(app, indexed_10records, aggs_and_facet, search_url, admin_settings):
    """Test pagination."""
    with app.test_client() as client:
        # Limit records
        res = client.get(search_url, query_string=dict(size=1, page=1))
        assert_hits_len(res, 1)
        data = get_json(res)
        assert "self" in data["links"]
        assert "next" in data["links"]
        assert "prev" not in data["links"]

        # Assert next URL before calling it
        next_url = get_json(res)["links"]["next"]
        parsed_url = parse_url(next_url)
        assert parsed_url["qs"]["size"] == ["1"]
        assert parsed_url["qs"]["page"] == ["2"]

        # Access next URL
        res = client.get(to_relative_url(next_url))
        assert_hits_len(res, 1)
        data = get_json(res)
        assert data["links"]["self"] == next_url
        assert "next" in data["links"]
        assert "prev" in data["links"]


def test_page_links(app, indexed_10records, aggs_and_facet, search_url, admin_settings):
    """Test Link HTTP header on multi-page searches."""
    with app.test_client() as client:
        # Limit records
        res = client.get(search_url, query_string=dict(size=1, page=1))
        assert_hits_len(res, 1)

        def parse_link_header(response):
            """Parse the links from a REST response's HTTP header."""
            return {
                k: v
                for (k, v) in map(
                    lambda s: re.findall(r'<(.*)>; rel="(.*)"', s)[0][::-1],
                    [x for x in res.headers["Link"].split(", ")],
                )
            }

        links = parse_link_header(res)
        data = get_json(res)["links"]
        assert "self" in data and "self" in links and data["self"] == links["self"]
        assert "next" in data and "next" in links and data["next"] == links["next"]
        assert "prev" not in data and "prev" not in links

        # Assert next URL before calling it
        first_url = links["self"]
        next_url = links["next"]
        parsed_url = parse_url(next_url)
        assert parsed_url["qs"]["size"] == ["1"]
        assert parsed_url["qs"]["page"] == ["2"]

        # Access next URL
        res = client.get(to_relative_url(next_url))
        assert_hits_len(res, 1)
        links = parse_link_header(res)
        assert links["self"] == next_url
        assert "next" in links
        assert "prev" in links and links["prev"] == first_url


def test_query(app, indexed_10records, aggs_and_facet, search_url, admin_settings):
    """Test query."""
    with app.test_client() as client:
        # Valid query syntax
        res = client.get(search_url, query_string=dict(q="control_number:1"))
        assert len(get_json(res)["hits"]["hits"]) == 1


@pytest.mark.parametrize(
    "app",
    [
        dict(
            endpoint=dict(
                search_factory_imp="invenio_records_rest.query.es_search_factory"
            )
        )
    ],
    indirect=["app"],
)
def test_search_query_syntax(app, indexed_10records, aggs_and_facet, search_url, admin_settings):
    """Test search engine query syntax."""
    with app.test_client() as client:
        # Valid search query syntax
        res = client.get(search_url, query_string=dict(q="+control_number:1"))
        assert len(get_json(res)["hits"]["hits"]) == 1


def test_sort(app, indexed_10records, aggs_and_facet, search_url, admin_settings):
    """Test invalid accept header."""
    with app.test_client() as client:
        res = client.get(search_url, query_string={"sort": "-control_number"})
        assert res.status_code == 200
        # Min control_number in test records set.
        assert get_json(res)["hits"]["hits"][0]["metadata"]["control_number"] == "10"

        res = client.get(search_url, query_string={"sort": "control_number"})
        assert res.status_code == 200
        # Max control_number in test records set.
        assert get_json(res)["hits"]["hits"][0]["metadata"]["control_number"] == "1"


def test_invalid_accept(app, indexed_10records, aggs_and_facet, search_url, admin_settings):
    """Test invalid accept header."""
    headers = [("Accept", "application/does_not_exist")]

    with app.test_client() as client:
        res = client.get(search_url, headers=headers)
        assert res.status_code == 406
        data = get_json(res)
        assert "message" in data
        assert data["status"] == 406


def test_aggregations_info(app, indexed_10records, aggs_and_facet, search_url, admin_settings, facet_search, redis_connect):
    """Test aggregations."""
    with app.test_client() as client:
        # Facets are defined in the "app" fixture.
        res = client.get(search_url)
        data = get_json(res)
        assert "aggregations" in data
        # len 3 because testrecords.json have three diff values for "control_number"
        assert len(data["aggregations"]["control_number"]["buckets"]) == 10
        assert data["aggregations"]["control_number"]["buckets"][0] == dict(key="1", doc_count=1)


def test_filters(app, indexed_10records, aggs_and_facet, search_url, admin_settings, facet_search, redis_connect):
    """Test aggregations."""
    with app.test_client() as client:
        res = client.get(search_url, query_string=dict(control_number="4"))
        assert_hits_len(res, 1)


def test_query_wrong(app, indexed_10records, aggs_and_facet, search_url, admin_settings):
    """Test invalid accept header."""
    with app.test_client() as client:
        res = client.get(search_url, query_string={"q": "test"})
        assert res.status_code == 200

        res = client.get(search_url, query_string={"q": "test:a"})
        assert res.status_code == 200

        res = client.get(search_url, query_string={"q": "test:"})
        assert res.status_code == 400

        res = client.get(search_url, query_string={"q": "test;"})
        assert res.status_code == 200


@pytest.mark.parametrize(
    "app",
    [
        dict(
            endpoint=dict(
                search_factory_imp="invenio_records_rest.query.es_search_factory"
            )
        )
    ],
    indirect=["app"],
)
def test_search_exception(app, indexed_10records, aggs_and_facet):
    """Test search exception."""
    with app.test_client() as client:
        res = client.get(url_for("invenio_records_rest.recid_list", q="i/o"))
        assert res.status_code == 400
        assert "The syntax of the search query is invalid." in res.get_data(
            as_text=True
        )


def test_dynamic_aggregation(app, indexed_records, search_url):
    """Test invalid accept header."""
    with app.test_client() as client:

        def stars_aggs():
            """Include only my deposits in the aggregation."""
            return {"terms": {"field": "stars", "include": [4, 5]}}

        app.config["RECORDS_REST_FACETS"]["invenio-records-rest"]["aggs"][
            "test"
        ] = stars_aggs
        res = client.get(search_url, query_string={"q": ""})
        assert res.status_code == 200
        data = get_json(res)
        expected = sorted(
            [{"doc_count": 2, "key": 4}, {"doc_count": 1, "key": 5}],
            key=lambda x: x["doc_count"],
        )
        assert (
            sorted(
                data["aggregations"]["test"]["buckets"], key=lambda x: x["doc_count"]
            )
            == expected
        )


def test_from_parameter_pagination(app, indexed_records, search_url):
    """Test "from" parameter pagination."""
    with app.test_client() as client:
        res = client.get(search_url, query_string={"size": 1, "from": 1})
        assert_hits_len(res, 1)
        data = get_json(res)
        assert "self" in data["links"]
        assert "next" in data["links"]
        assert "prev" not in data["links"]

        next_url = get_json(res)["links"]["next"]
        parsed_url = parse_url(next_url)

        assert parsed_url["qs"]["size"] == ["1"]
        assert parsed_url["qs"]["from"] == ["2"]
        assert "page" not in parsed_url["qs"]

        self_url = get_json(res)["links"]["self"]
        parsed_url = parse_url(self_url)

        assert parsed_url["qs"]["size"] == ["1"]
        assert parsed_url["qs"]["from"] == ["1"]
        assert "page" not in parsed_url["qs"]

        res = client.get(next_url)
        assert_hits_len(res, 1)
        data = get_json(res)

        assert data["links"]["self"] == next_url
        assert "next" in data["links"]
        assert "prev" in data["links"]

        next_url = get_json(res)["links"]["next"]
        parsed_url = parse_url(next_url)

        assert parsed_url["qs"]["size"] == ["1"]
        assert parsed_url["qs"]["from"] == ["3"]
        assert "page" not in parsed_url["qs"]


def test_from_parameter_edges(app, indexed_records, search_url):
    """Test first and last values for "from" parameter pagination."""
    with app.test_client() as client:
        res = client.get(search_url, query_string={"size": 1, "from": 1})
        assert_hits_len(res, 1)
        data = get_json(res)
        assert "self" in data["links"]
        assert "next" in data["links"]
        assert "prev" not in data["links"]

        res = client.get(search_url, query_string={"size": 1, "from": 4})
        assert_hits_len(res, 1)
        data = get_json(res)
        assert "self" in data["links"]
        assert "next" not in data["links"]
        assert "prev" in data["links"]


def test_from_parameter_invalid_pagination(app, indexed_records, search_url):
    """Test invalid edge values for "from" parameter pagination."""
    with app.test_client() as client:
        res = client.get(search_url, query_string={"size": 1, "from": 0})
        data = get_json(res)
        assert res.status_code == 400
        assert data["message"] == "Invalid pagination parameters."
        errors = {(e["field"], e["message"]) for e in data["errors"]}
        assert errors == {
            ("from", "Must be at least 1."),
        } or errors == {
            ("from", "Must be greater than or equal to 1."),
        }

        res = client.get(search_url, query_string={"size": 1, "from": 10001})
        assert res.status_code == 400
        data = get_json(res)
        assert data["message"] == "Maximum number of 10000 results have been reached."


@pytest.mark.parametrize(
    "app",
    [
        dict(
            records_rest_endpoints=dict(
                recid=dict(
                    pid_type="recid",
                    max_result_window=3,
                )
            ),
        )
    ],
    indirect=["app"],
)
def test_max_result_window_valid_params(app, indexed_records, search_url):
    """Test max_result_window with a valid page/from/size parameters."""
    with app.test_client() as client:
        res = client.get(search_url, query_string={"size": 3})
        assert_hits_len(res, 3)

        res = client.get(search_url, query_string={"page": 1, "size": 3})
        assert_hits_len(res, 3)
        data = get_json(res)

        res = client.get(search_url, query_string={"from": 3, "size": 1})
        assert_hits_len(res, 1)
        data = get_json(res)
        assert "self" in data["links"]
        assert "next" not in data["links"]
        assert "prev" in data["links"]


@pytest.mark.parametrize(
    "app",
    [
        dict(
            records_rest_endpoints=dict(
                recid=dict(
                    pid_type="recid",
                    max_result_window=3,
                )
            ),
        )
    ],
    indirect=["app"],
)
def test_max_result_window_invalid_params(app, indexed_records, search_url):
    """Test max_result_window with an invalid page/from/size parameters."""
    with app.test_client() as client:
        res = client.get(search_url, query_string={"size": 4})
        assert res.status_code == 400
        assert "Maximum number of 3 results have been reached." in res.get_data(
            as_text=True
        )

        res = client.get(search_url, query_string={"page": 1, "size": 4})
        assert res.status_code == 400
        assert "Maximum number of 3 results have been reached." in res.get_data(
            as_text=True
        )

        res = client.get(search_url, query_string={"from": 4, "size": 1})
        assert res.status_code == 400
        assert "Maximum number of 3 results have been reached." in res.get_data(
            as_text=True
        )

        res = client.get(search_url, query_string={"from": 3, "size": 2})
        assert res.status_code == 400
        assert "Maximum number of 3 results have been reached." in res.get_data(
            as_text=True
        )