# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test location related views."""

import pytest
from flask import json, url_for
from testutils import login_user

from invenio_files_rest.models import Bucket


def get_json(resp):
    """Get JSON from response."""
    return json.loads(resp.get_data(as_text=True))


@pytest.mark.parametrize(
    "user, expected",
    [
        (None, 401),
        ("auth", 403),
        ("location", 200),
    ],
)
def test_post_bucket(app, client, headers, dummy_location, permissions, user, expected):
    """Test post a bucket."""
    expected_keys = [
        "id",
        "links",
        "size",
        "quota_size",
        "max_file_size",
        "locked",
        "created",
        "updated",
    ]
    params = [{}, {"location_name": dummy_location.name}]

    login_user(client, permissions[user])

    for data in params:
        resp = client.post(
            url_for("invenio_files_rest.location_api"), data=data, headers=headers
        )
        assert resp.status_code == expected
        if resp.status_code == 200:
            resp_json = get_json(resp)
            for key in expected_keys:
                assert key in resp_json
            assert Bucket.get(resp_json["id"])


@pytest.mark.parametrize(
    "user, expected",
    [
        (None, 405),
        ("auth", 405),
        ("location", 405),
    ],
)
def test_get_location(
    app, client, headers, dummy_location, permissions, user, expected
):
    """Test GET a location."""
    login_user(client, permissions[user])
    r = client.get(url_for("invenio_files_rest.location_api"), headers=headers)
    assert r.status_code == expected
