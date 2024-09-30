# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test bucket related views."""

import pytest
from flask import url_for
from testutils import login_user

from invenio_files_rest.models import ObjectVersion


@pytest.mark.parametrize(
    "user, expected",
    [
        (None, 404),
        ("auth", 404),
        ("objects", 404),  # TODO - return 403 instead
        ("bucket", 200),
        ("location", 200),
    ],
)
def test_head(client, headers, bucket, permissions, user, expected):
    """Test checking existence of bucket."""
    login_user(client, permissions[user])

    # Existing bucket
    resp = client.head(
        url_for("invenio_files_rest.bucket_api", bucket_id=bucket.id),
        headers=headers,
    )
    assert resp.status_code == expected
    assert not resp.data

    # Non-existing bucket
    assert (
        client.head(
            url_for("invenio_files_rest.bucket_api", bucket_id="invalid"),
            headers=headers,
        ).status_code
        == 404
    )


def test_head_locked_deleted(client, db, headers, bucket, permissions):
    """Test checking existence of bucket."""
    bucket_url = url_for("invenio_files_rest.bucket_api", bucket_id=bucket.id)

    login_user(client, permissions["location"])

    # Locked bucket
    bucket.locked = True
    db.session.commit()
    assert client.head(bucket_url).status_code == 200

    # Deleted bucket
    bucket.deleted = True
    db.session.commit()
    assert client.head(bucket_url).status_code == 404


@pytest.mark.parametrize(
    "user, expected",
    [
        (None, 404),
        ("auth", 404),
        ("objects", 404),  # TODO - return 403 instead
        ("bucket", 200),
        ("location", 200),
    ],
)
def test_get(client, headers, permissions, bucket, objects, get_json, user, expected):
    """Test listing objects."""
    login_user(client, permissions[user])
    # Existing bucket
    resp = client.get(
        url_for(
            "invenio_files_rest.bucket_api",
            bucket_id=bucket.id,
        ),
        headers=headers,
    )
    assert resp.status_code == expected

    if resp.status_code == 200:
        data = get_json(resp)
        assert len(data["contents"]) == 2
        assert all([x["is_head"] for x in data["contents"]])

        assert set(data["contents"][0].keys()) == {
            "checksum",
            "created",
            "delete_marker",
            "is_head",
            "key",
            "links",
            "mimetype",
            "size",
            "updated",
            "version_id",
            "tags",
        }
        assert set(data.keys()) == {
            "contents",
            "created",
            "id",
            "links",
            "locked",
            "max_file_size",
            "quota_size",
            "size",
            "updated",
        }

    # Non-existing bucket
    resp = client.get(
        url_for(
            "invenio_files_rest.bucket_api",
            bucket_id="invalid",
        ),
        headers=headers,
    )
    assert resp.status_code == 404


@pytest.mark.parametrize(
    "user, expected",
    [
        (None, 404),
        ("auth", 404),
        ("bucket", 403),  # User already knowns bucket exists.
        ("objects", 404),  # TODO - return 403 instead
        ("location", 200),
    ],
)
def test_get_versions(
    client, headers, permissions, bucket, objects, get_json, user, expected
):
    """Test listing objects."""
    login_user(client, permissions[user])

    resp = client.get(
        url_for(
            "invenio_files_rest.bucket_api",
            bucket_id=bucket.id,
            versions="1",
        ),
        headers=headers,
    )
    assert resp.status_code == expected

    if resp.status_code == 200:
        data = get_json(resp)
        assert len(data["contents"]) == 4
        assert data["id"] == str(bucket.id)


@pytest.mark.parametrize(
    "user, expected",
    [
        (None, 404),
        ("auth", 404),
        ("objects", 404),  # TODO - return 403 instead
        ("bucket", 200),
        ("location", 200),
    ],
)
def test_get_empty_bucket(
    db, client, headers, bucket, objects, permissions, get_json, user, expected
):
    """Test getting objects from an empty bucket."""
    # Delete the objects created in the fixtures to have an empty bucket with
    # permissions set up.
    for obj in objects:
        ObjectVersion.delete(obj.bucket_id, obj.key)
    db.session.commit()

    login_user(client, permissions[user])

    resp = client.get(
        url_for("invenio_files_rest.bucket_api", bucket_id=bucket.id),
        headers=headers,
    )
    assert resp.status_code == expected
    if resp.status_code == 200:
        assert get_json(resp)["contents"] == []
