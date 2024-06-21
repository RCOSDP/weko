# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test object related views."""

from datetime import timedelta, timezone
from io import BytesIO
from unittest.mock import patch

import pytest
from flask import url_for
from fs.opener import open_fs as opendir
from testutils import BadBytesIO, login_user

from invenio_files_rest.models import FileInstance, ObjectVersion
from invenio_files_rest.tasks import remove_file_data


@pytest.mark.parametrize(
    "user, expected",
    [
        (None, 404),
        ("auth", 404),
        ("objects", 404),
        ("bucket", 404),
        ("location", 404),
    ],
)
def test_get_not_found(client, headers, bucket, permissions, user, expected):
    """Test getting a non-existing object."""
    login_user(client, permissions[user])
    resp = client.get(
        url_for(
            "invenio_files_rest.object_api",
            bucket_id=bucket.id,
            key="non-existing.pdf",
        ),
        headers=headers,
    )
    assert resp.status_code == expected


@pytest.mark.parametrize(
    "user, expected",
    [
        (None, 404),
        ("auth", 404),
        ("bucket", 200),
        ("location", 200),
        ("objects", 200),
    ],
)
def test_get(client, headers, bucket, objects, permissions, user, expected):
    """Test getting an object."""
    login_user(client, permissions[user])

    for obj in objects:
        object_url = url_for(
            "invenio_files_rest.object_api",
            bucket_id=bucket.id,
            key=obj.key,
        )

        # Get specifying version (of latest obj).
        resp = client.get(
            object_url,
            query_string="versionId={0}".format(obj.version_id),
            headers=headers,
        )
        assert resp.status_code == expected

        # Get latest
        resp = client.get(object_url, headers=headers)
        assert resp.status_code == expected

        if resp.status_code == 200:
            # Strips prefix 'md5:' from checksum value.
            assert resp.content_md5 == obj.file.checksum[4:]
            assert resp.get_etag()[0] == obj.file.checksum


def test_get_with_x_sendfile(
    client, headers, bucket, objects, permissions, offload_file_serving
):
    """Test getting a redirect to an object."""

    login_user(client, permissions["bucket"])

    for obj in objects:
        object_url = url_for(
            "invenio_files_rest.object_api",
            bucket_id=bucket.id,
            key=obj.key,
        )

        # Get specifying version (of latest obj).
        resp = client.get(
            object_url,
            query_string="versionId={0}".format(obj.version_id),
            headers=headers,
        )
        assert resp.status_code == 200

        assert resp.headers["X-Accel-Redirect"].startswith("/user_files/")

        resp = client.delete(
            url_for(
                "invenio_files_rest.object_api",
                bucket_id=bucket.id,
                key=obj.key,
            )
        )

        resp = client.get(
            url_for(
                "invenio_files_rest.object_api",
                bucket_id=bucket.id,
                key=obj.key,
            )
        )
        assert resp.status_code == 404


def test_get_download(client, headers, bucket, objects, permissions):
    """Test getting an object."""
    login_user(client, permissions["objects"])

    for obj in objects:
        object_url = url_for(
            "invenio_files_rest.object_api", bucket_id=bucket.id, key=obj.key
        )

        # Get specifying version (of latest obj).
        resp = client.get(
            object_url,
            query_string=dict(versionId=obj.version_id, download=True),
            headers=headers,
        )
        assert resp.status_code == 200

        # Check if the 'Content-Disposition' is an attachment
        assert resp.headers["Content-Disposition"] == "attachment; filename={0}".format(
            obj.key
        )


def test_last_modified_utc_conversion(client, headers, bucket, permissions):
    """Test date conversion of the DB object 'updated' timestamp (UTC) to a
    correct Last-Modified date (also UTC) in the response header.

    This test makes sure that DB timestamps are not treated as localtime.
    """
    key = "last_modified_test.txt"
    data = b"some_new_content"
    object_url = url_for("invenio_files_rest.object_api", bucket_id=bucket.id, key=key)
    login_user(client, permissions["bucket"])

    # Make a new PUT and get the DB object 'updated' datetime
    put_resp = client.put(object_url, input_stream=BytesIO(data))
    updated = ObjectVersion.get(bucket, key).updated
    assert put_resp.status_code == 200
    # GET the object and make sure the Last-Modified parameter in the header
    # is the same (sans the microseconds resolution) timestamp
    get_resp = client.get(object_url)
    last_modified = get_resp.last_modified
    if last_modified.tzinfo and not updated.tzinfo:
        updated = updated.replace(tzinfo=timezone.utc)
    assert get_resp.status_code == 200
    assert abs(last_modified - updated) < timedelta(seconds=1)


def test_get_unreadable_file(client, headers, bucket, objects, db, admin_user):
    """Test getting an object with an unreadable file."""
    login_user(client, admin_user)

    obj = objects[0]
    assert obj.is_head
    obj.file.readable = False
    db.session.commit()

    resp = client.get(
        url_for(
            "invenio_files_rest.object_api",
            bucket_id=bucket.id,
            key=obj.key,
        )
    )
    assert resp.status_code == 503


@pytest.mark.parametrize(
    "user, expected",
    [
        (None, 404),
        ("auth", 404),
        ("objects", 403),
        ("bucket", 403),
        ("location", 200),
    ],
)
def test_get_versions(client, headers, bucket, versions, permissions, user, expected):
    """Test object version getting."""
    login_user(client, permissions[user])

    for obj in versions:
        if obj.is_head is True:
            continue
        resp = client.get(
            url_for(
                "invenio_files_rest.object_api",
                bucket_id=bucket.id,
                key=obj.key,
            ),
            query_string=dict(versionId=obj.version_id),
        )
        assert resp.status_code == expected

        if resp.status_code == 200:
            # Strips prefix 'md5:' from checksum value.
            assert resp.content_md5 == obj.file.checksum[4:]
            assert resp.get_etag()[0] == obj.file.checksum


@pytest.mark.parametrize(
    "user",
    [
        None,
        "auth",
        "objects",
        "bucket",
        "location",
    ],
)
def test_get_versions_invalid(client, headers, bucket, objects, permissions, user):
    """Test object version getting."""
    versions = [
        ("c1057411-ad8a-4e4f-ac0e-f6f8b395d277", 404),
        ("invalid", 422),  # Not a UUID
    ]

    login_user(client, permissions[user])
    for v, expected in versions:
        for obj in objects:
            resp = client.get(
                url_for(
                    "invenio_files_rest.object_api",
                    bucket_id=bucket.id,
                    key=obj.key,
                ),
                query_string=dict(versionId=v),
            )
            assert resp.status_code == expected


@pytest.mark.parametrize(
    "user,expected",
    [
        (None, 404),
        ("auth", 404),
        ("bucket", 403),
        ("location", 403),
    ],
)
def test_post(client, headers, permissions, bucket, user, expected):
    """Test ObjectResource view POST method."""

    key = "file.pdf"
    data = b"mycontent"

    login_user(client, permissions[user])

    resp = client.post(
        url_for("invenio_files_rest.object_api", bucket_id=bucket.id, key=key),
        data={"file": (BytesIO(data), key)},
        headers={"Accept": "*/*"},
    )
    assert resp.status_code == expected


@pytest.mark.parametrize(
    "user,expected",
    [
        (None, 404),
        ("auth", 404),
        ("objects", 404),
        ("bucket", 200),
        ("location", 200),
    ],
)
def test_put(client, bucket, permissions, get_md5, get_json, user, expected):
    """Test upload of an object."""

    key = "test.txt"
    data = b"updated_content"
    checksum = get_md5(data, prefix=True)
    object_url = url_for("invenio_files_rest.object_api", bucket_id=bucket.id, key=key)

    login_user(client, permissions[user])
    resp = client.put(
        object_url,
        input_stream=BytesIO(data),
    )
    assert resp.status_code == expected

    if expected == 200:
        assert resp.get_etag()[0] == checksum

        resp = client.get(object_url)
        assert resp.status_code == 200
        assert resp.data == data
        assert resp.content_md5 == checksum[4:]


def test_put_versioning(client, bucket, permissions, get_md5, get_json):
    """Test versioning feature."""
    key = "test.txt"
    files = [b"v1", b"v2"]
    object_url = url_for("invenio_files_rest.object_api", bucket_id=bucket.id, key=key)

    # Upload to same key twice
    login_user(client, permissions["location"])
    for f in files:
        resp = client.put(object_url, input_stream=BytesIO(f))
        assert resp.status_code == 200

    # Assert we have two versions
    resp = client.get(
        url_for(
            "invenio_files_rest.bucket_api",
            bucket_id=bucket.id,
        ),
        query_string="versions=1",
    )
    data = get_json(resp, code=200)
    assert len(data["contents"]) == 2

    # Assert we can get both versions
    for item in data["contents"]:
        assert client.get(item["links"]["self"]).status_code == 200


@pytest.mark.parametrize(
    "quota_size, max_file_size, expected, err",
    [
        (50, 100, 400, "Bucket quota"),
        (100, 50, 400, "Maximum file size"),
        (100, 100, 200, None),
        (None, None, 200, None),
    ],
)
def test_put_file_size_errors(
    client, db, bucket, quota_size, max_file_size, expected, err, admin_user
):
    """Test that file size errors are properly raised."""
    login_user(client, admin_user)

    filedata = b"a" * 75
    object_url = url_for(
        "invenio_files_rest.object_api", bucket_id=bucket.id, key="test.txt"
    )

    # Set quota and max file size
    bucket.quota_size = quota_size
    bucket.max_file_size = max_file_size
    db.session.commit()

    # Test set limits.
    resp = client.put(object_url, input_stream=BytesIO(filedata))
    assert resp.status_code == expected

    # Test correct error message.
    if err:
        assert err in resp.get_data(as_text=True)

    # Test that versions are counted.
    if max_file_size == 100 and quota_size == 100:
        resp = client.put(object_url, input_stream=BytesIO(filedata))
        assert resp.status_code == 400


def test_put_invalid_key(client, db, bucket, admin_user):
    login_user(client, admin_user)

    """Test invalid key name."""
    key = "a" * 2000
    object_url = url_for("invenio_files_rest.object_api", bucket_id=bucket.id, key=key)

    # Test set limits.
    resp = client.put(object_url, input_stream=BytesIO(b"test"))
    assert resp.status_code == 400


def test_put_zero_size(client, bucket, admin_user):
    """Test zero size file."""
    login_user(client, admin_user)

    object_url = url_for(
        "invenio_files_rest.object_api", bucket_id=bucket.id, key="test.txt"
    )

    # Test set limits.
    resp = client.put(object_url, input_stream=BytesIO(b""))
    assert resp.status_code == 400


def test_put_deleted_locked(client, db, bucket, admin_user):
    """Test that file size errors are properly raised."""
    login_user(client, admin_user)

    object_url = url_for(
        "invenio_files_rest.object_api", bucket_id=bucket.id, key="test.txt"
    )

    # Can upload
    resp = client.put(object_url, input_stream=BytesIO(b"test"))
    assert resp.status_code == 200

    # Locked bucket
    bucket.locked = True
    db.session.commit()
    resp = client.put(object_url, input_stream=BytesIO(b"test"))
    assert resp.status_code == 403

    # Deleted bucket
    bucket.deleted = True
    db.session.commit()
    resp = client.put(object_url, input_stream=BytesIO(b"test"))
    assert resp.status_code == 404


def test_put_error(client, bucket, admin_user):
    """Test upload - cancelled by user."""
    login_user(client, admin_user)

    object_url = url_for(
        "invenio_files_rest.object_api", bucket_id=bucket.id, key="test.txt"
    )

    pytest.raises(
        ValueError, client.put, object_url, input_stream=BadBytesIO(b"a" * 128)
    )
    assert FileInstance.query.count() == 0
    assert ObjectVersion.query.count() == 0
    # Ensure that the file was removed.
    fs = opendir(bucket.location.uri)
    assert len(list(fs.walk("."))) == 3


def test_put_multipartform(client, bucket, admin_user):
    """Test upload via multipart/form-data."""
    login_user(client, admin_user)

    object_url = url_for(
        "invenio_files_rest.object_api", bucket_id=bucket.id, key="test.txt"
    )

    res = client.put(
        object_url,
        data={
            "_chunkNumber": "0",
            "_currentChunkSize": "100",
            "_chunkSize": "10000000",
            "_totalSize": "100",
            "file": (BytesIO(b"a" * 100), "test.txt"),
        },
    )
    assert res.status_code == 200


@pytest.mark.parametrize(
    "user, expected",
    [
        (None, 404),
        ("auth", 404),
        ("objects", 403),
        ("bucket", 204),
        ("location", 204),
    ],
)
def test_delete(client, db, bucket, objects, permissions, user, expected):
    """Test deleting an object."""
    login_user(client, permissions[user])
    for obj in objects:
        # Valid object
        resp = client.delete(
            url_for(
                "invenio_files_rest.object_api",
                bucket_id=bucket.id,
                key=obj.key,
            )
        )
        assert resp.status_code == expected
        if resp.status_code == 204:
            assert not ObjectVersion.get(bucket.id, obj.key)
            resp = client.get(
                url_for(
                    "invenio_files_rest.object_api",
                    bucket_id=bucket.id,
                    key=obj.key,
                )
            )
            assert resp.status_code == 404
        else:
            assert ObjectVersion.get(bucket.id, obj.key)

        # Invalid object
        assert (
            client.delete(
                url_for(
                    "invenio_files_rest.object_api",
                    bucket_id=bucket.id,
                    key="invalid",
                )
            ).status_code
            == 404
        )


@pytest.mark.parametrize(
    "user, expected",
    [
        (None, 404),
        ("auth", 404),
        ("objects", 403),
        ("bucket", 403),
        ("location", 204),
    ],
)
def test_delete_versions(client, db, bucket, versions, permissions, user, expected):
    """Test deleting an object."""
    login_user(client, permissions[user])
    for obj in versions:
        # Valid delete
        resp = client.delete(
            url_for(
                "invenio_files_rest.object_api",
                bucket_id=bucket.id,
                key=obj.key,
                versionId=obj.version_id,
            )
        )
        assert resp.status_code == expected
        if resp.status_code == 204:
            assert not ObjectVersion.get(bucket.id, obj.key, version_id=obj.version_id)

        # Invalid object
        assert (
            client.delete(
                url_for(
                    "invenio_files_rest.object_api",
                    bucket_id=bucket.id,
                    key=obj.key,
                    versionId="deadbeef-65bd-4d9b-93e2-ec88cc59aec5",
                )
            ).status_code
            == 404
        )


def test_delete_versions_head_reset(client, db, bucket, versions, admin_user):
    """Test head setting after deletion."""
    login_user(client, admin_user)
    key = "LICENSE"
    versions_to_delete = [version for version in versions if version.key == key]
    assert len(versions_to_delete) == 2
    for obj in versions_to_delete:
        if obj.is_head:
            version_to_delete = obj
        else:
            new_head_obj = obj
    assert not new_head_obj.is_head
    res = client.delete(
        url_for(
            "invenio_files_rest.object_api",
            bucket_id=bucket.id,
            key=version_to_delete.key,
            versionId=version_to_delete.version_id,
        )
    )
    assert res.status_code == 204
    assert new_head_obj.is_head


def test_delete_locked_deleted(client, db, bucket, versions, admin_user):
    """Test a deleted/locked bucket."""
    obj = versions[0]
    object_url = url_for(
        "invenio_files_rest.object_api", bucket_id=bucket.id, key=obj.key
    )

    # Locked bucket
    bucket.locked = True
    db.session.commit()

    login_user(client, admin_user)

    # Latest version
    resp = client.delete(object_url)
    assert resp.status_code == 403
    # Previous version
    resp = client.delete(
        object_url, query_string="versionId={0}".format(obj.version_id)
    )
    assert resp.status_code == 403

    # Deleted bucket
    bucket.deleted = True
    db.session.commit()
    # Latest version
    resp = client.delete(object_url)
    assert resp.status_code == 404
    # Previous version
    resp = client.delete(
        object_url, query_string="versionId={0}".format(obj.version_id)
    )
    assert resp.status_code == 404


def test_delete_unwritable(client, db, bucket, versions, admin_user):
    """Test deleting a file which is not writable."""
    obj = versions[0]

    # Unwritable file.
    obj.file.writable = False
    db.session.commit()

    login_user(client, admin_user)

    # Delete specific version
    with patch("invenio_files_rest.views.remove_file_data") as task:
        resp = client.delete(
            url_for(
                "invenio_files_rest.object_api",
                bucket_id=bucket.id,
                key=obj.key,
                versionId=obj.version_id,
            ),
        )
        assert task.delay.called
    assert resp.status_code == 204

    # Won't remove anything because file is not writable.
    assert FileInstance.query.count() == 4
    remove_file_data(obj.file_id)
    assert FileInstance.query.count() == 4


def test_put_header_tags(app, client, bucket, permissions, get_md5, get_json):
    """Test upload of an object with tags in the headers."""
    key = "test.txt"
    headers = {
        app.config["FILES_REST_FILE_TAGS_HEADER"]: ("key1=val1&key2=val2&key3=val3")
    }

    login_user(client, permissions["bucket"])
    resp = client.put(
        url_for("invenio_files_rest.object_api", bucket_id=bucket.id, key=key),
        input_stream=BytesIO(b"updated_content"),
        headers=headers,
    )
    assert resp.status_code == 200

    tags = ObjectVersion.get(bucket, key).get_tags()
    assert tags["key1"] == "val1"
    assert tags["key2"] == "val2"
    assert tags["key3"] == "val3"


def test_put_header_invalid_tags(app, client, bucket, permissions, get_md5, get_json):
    """Test upload of an object with tags in the headers."""
    header_name = app.config["FILES_REST_FILE_TAGS_HEADER"]
    invalid = [
        # We don't test zero-length values/keys, because they are filtered out
        # from parse_qsl
        ("a" * 256, "valid"),
        ("valid", "b" * 256),
    ]

    login_user(client, permissions["bucket"])
    # Invalid key or values
    for k, v in invalid:
        resp = client.put(
            url_for("invenio_files_rest.object_api", bucket_id=bucket.id, key="k"),
            input_stream=BytesIO(b"updated_content"),
            headers={header_name: "{}={}".format(k, v)},
        )
        assert resp.status_code == 400

    # Duplicate key
    resp = client.put(
        url_for("invenio_files_rest.object_api", bucket_id=bucket.id, key="k"),
        input_stream=BytesIO(b"updated_content"),
        headers={header_name: "a=1&a=2"},
    )
    assert resp.status_code == 400
