# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test view functions."""
import json

import pytest
from flask import url_for

from invenio_stats import current_stats


def test_post_request(app, db, users, queries_config, sample_histogram_query_data):
    """Test post request to stats API."""
    with app.test_client() as client:
        headers = [("Content-Type", "application/json"), ("Accept", "application/json")]
        sample_histogram_query_data["mystat"]["stat"] = "test-query"
        resp = client.post(
            url_for(
                "invenio_stats.stat_query",
                access_token=users["authorized"].allowed_token,
            ),
            headers=headers,
            data=json.dumps(sample_histogram_query_data),
        )
        resp_json = json.loads(resp.data.decode("utf-8"))
        assert resp_json["mystat"]["value"] == 100

        sample_histogram_query_data["mystat"]["stat"] = "unknown-query"
        resp = client.post(
            url_for(
                "invenio_stats.stat_query",
                access_token=users["authorized"].allowed_token,
            ),
            headers=headers,
            data=json.dumps(sample_histogram_query_data),
        )
        assert resp.status_code == 400


@pytest.mark.parametrize(
    "which_user, expected_code",
    [("authorized", 200), ("unauthorized", 403), (None, 401)],
)
def test_unauthorized_request(
    app,
    sample_histogram_query_data,
    users,
    queries_config,
    custom_permission_factory,
    which_user,
    expected_code,
):
    """Test rejecting unauthorized requests."""

    def client_req(user):
        with app.test_client() as client:
            headers = [
                ("Content-Type", "application/json"),
                ("Accept", "application/json"),
            ]
            resp = client.post(
                url_for(
                    "invenio_stats.stat_query",
                    access_token=user.allowed_token if user else None,
                ),
                headers=headers,
                data=json.dumps(sample_histogram_query_data),
            )
            return resp.status_code

    sample_histogram_query_data["mystat"]["stat"] = "test-query"
    user = users[which_user] if which_user else None
    assert client_req(user) == expected_code

    factory = current_stats.queries["test-query"].permission_factory
    assert factory.query_name == "test-query"
    assert factory.params == sample_histogram_query_data["mystat"]["params"]
