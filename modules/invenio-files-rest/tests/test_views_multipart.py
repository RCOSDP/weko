# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module test views."""

from __future__ import absolute_import, print_function
from datetime import timedelta
import io

import json
import uuid
import pytest
from flask import url_for
from mock import MagicMock, patch
from six import BytesIO
from invenio_files_rest.errors import MultipartExhausted
from invenio_files_rest.views import ObjectResource
from tests.testutils import BadBytesIO, login_user

from invenio_files_rest.models import Bucket, FileInstance, MultipartObject, ObjectVersion, Part
from invenio_files_rest.tasks import merge_multipartobject


def obj_url(bucket):
    """Get object URL."""
    return url_for(
        'invenio_files_rest.object_api',
        bucket_id=str(bucket.id),
        key='mybigfile',
    )


def test_post_init(client, headers, permissions, bucket, get_json):
    """Test init multipart upload."""
    cases = [
        (None, 404),
        ('auth', 404),
        ('objects', 404),  # TODO - use 403 instead
        ('bucket', 200),
        ('location', 200),
    ]

    for user, expected in cases:
        login_user(client, permissions[user])

        # Initiate multipart upload
        res = client.post(
            obj_url(bucket),
            query_string='uploads',
            headers={'Content-Type': 'application/json'},
            data=json.dumps({
                'size': 10,
                'partSize': 4,
            })
        )
        assert res.status_code == expected

        if res.status_code == 200:
            data = get_json(res)
            expected_keys = [
                'id', 'bucket', 'completed', 'size', 'part_size',
                'last_part_number', 'last_part_size', 'links'
            ]
            for k in expected_keys:
                assert k in data


def test_post_init_querystring(client, bucket, get_json, admin_user):
    """Test init multipart upload."""
    login_user(client, admin_user)

    res = client.post(
        obj_url(bucket),
        query_string='uploads&size=10&partSize=4',
    )
    assert res.status_code == 200


def test_get_init_not_allowed(client, bucket, get_json):
    """Test get request to ?uploads."""
    res = client.get(
        obj_url(bucket),
        query_string='uploads',
    )
    assert res.status_code == 405


def test_post_invalid_partsizes(client, headers, bucket, get_json, admin_user):
    """Test invalid multipart init."""
    login_user(client, admin_user)

    # Part size too large
    res = client.post(
        obj_url(bucket), query_string='uploads', headers=headers,
        data=json.dumps({'size': 30, 'partSize': 21}))
    assert res.status_code == 400

    # Part size too small
    res = client.post(
        obj_url(bucket), query_string='uploads', headers=headers,
        data=json.dumps({'size': 30, 'partSize': 1}))
    assert res.status_code == 400

    # Size too large
    res = client.post(
        obj_url(bucket), query_string='uploads', headers=headers,
        data=json.dumps({'size': 2 * 100 + 1, 'partSize': 2}))
    assert res.status_code == 400


def test_post_size_limits(client, db, headers, bucket, admin_user):
    """Test invalid multipart init."""
    login_user(client, admin_user)

    bucket.quota_size = 100
    db.session.commit()

    # Bucket quota exceed
    res = client.post(
        obj_url(bucket), query_string='uploads', headers=headers,
        data=json.dumps({'size': 101, 'partSize': 20}))
    assert res.status_code == 400

    bucket.max_file_size = 50
    db.session.commit()

    # Max file size exceeded
    res = client.post(
        obj_url(bucket), query_string='uploads', headers=headers,
        data=json.dumps({'size': 51, 'partSize': 20}))
    assert res.status_code == 400


def test_post_locked_bucket(client, db, headers, bucket, get_json, admin_user):
    """Test invalid multipart init."""
    login_user(client, admin_user)

    bucket.locked = True
    db.session.commit()

    res = client.post(
        obj_url(bucket), query_string='uploads', headers=headers,
        data=json.dumps({'size': 10, 'partSize': 2}))
    assert res.status_code == 403

    bucket.deleted = True
    db.session.commit()

    res = client.post(
        obj_url(bucket), query_string='uploads', headers=headers,
        data=json.dumps({'size': 10, 'partSize': 2}))
    assert res.status_code == 404


def test_post_invalidkey(client, db, headers, bucket, admin_user):
    """Test invalid multipart init."""
    login_user(client, admin_user)

    object_url = url_for(
        'invenio_files_rest.object_api',
        bucket_id=str(bucket.id),
        key='a' * 1025,
    ) + 'uploads'

    # Bucket quota exceed
    res = client.post(
        object_url, query_string='uploads', headers=headers,
        data=json.dumps({'size': 50, 'partSize': 20}))
    assert res.status_code == 400


def test_put(client, db, bucket, permissions, multipart, multipart_url,
             get_sha256, get_json):
    """Test part upload."""
    cases = [
        (None, 404),
        ('auth', 404),
        ('objects', 404),  # TODO - use 403 instead
        ('bucket', 200),
        ('location', 200),
    ]

    for user, expected in cases:
        login_user(client, permissions[user])

        data = b'a' * multipart.chunk_size
        res = client.put(
            multipart_url + '&partNumber={0}'.format(1),
            input_stream=BytesIO(data),
        )
        assert res.status_code == expected

        if res.status_code == 200:
            assert res.get_etag()[0] == get_sha256(data)

            # Assert content
            with open(multipart.file.uri, 'rb') as fp:
                fp.seek(multipart.chunk_size)
                content = fp.read(multipart.chunk_size)
            assert content == data
            assert Part.count(multipart) == 1
            assert Part.get_or_none(multipart, 1).checksum == get_sha256(data)


def test_put_not_found(client, db, bucket, permissions, multipart,
                       multipart_url, get_md5):
    """Test invalid multipart id."""
    res = client.put(url_for(
        'invenio_files_rest.object_api',
        bucket_id=str(multipart.bucket_id),
        key=multipart.key,
        uploadId='deadbeef-65bd-4d9b-93e2-ec88cc59aec5',
        partNumber=1,
    ), input_stream=BytesIO(b'a' * multipart.chunk_size))
    assert res.status_code == 404


def test_put_wrong_sizes(client, db, bucket, multipart, multipart_url,
                         admin_user):
    """Test invalid part sizes."""
    login_user(client, admin_user)

    cases = [
        b'a' * (multipart.chunk_size + 1),
        b'a' * (multipart.chunk_size - 1),
        b'',
    ]
    for data in cases:
        res = client.put(
            multipart_url + '&partNumber={0}'.format(1),
            input_stream=BytesIO(data),
        )
        assert res.status_code == 400


def test_put_ngfileupload(client, db, bucket, multipart, multipart_url,
                          admin_user):
    """Test invalid part sizes."""
    login_user(client, admin_user)

    res = client.put(
        multipart_url,
        data={
            '_chunkNumber': '0',
            '_currentChunkSize': str(multipart.chunk_size),
            '_chunkSize': str(multipart.chunk_size),
            '_totalSize': str(multipart.size),
            'file': (
                BytesIO(b'a' * multipart.chunk_size),
                multipart.key
            )
        }
    )
    assert res.status_code == 200


def test_put_invalid_part_number(client, db, bucket, multipart, multipart_url,
                                 admin_user):
    """Test invalid part number."""
    login_user(client, admin_user)

    data = b'a' * multipart.chunk_size
    for c in [400, 2000, 'a']:
        res = client.put(
            multipart_url + '&partNumber={0}'.format(c),
            input_stream=BytesIO(data),
        )
        assert res.status_code == 400


def test_put_completed_multipart(client, db, bucket, multipart, multipart_url,
                                 admin_user):
    """Test uploading to a completed multipart upload."""
    login_user(client, admin_user)

    multipart.completed = True
    db.session.commit()

    res = client.put(
        multipart_url + '&partNumber={0}'.format(1),
        input_stream=BytesIO(b'a' * multipart.chunk_size),
    )
    assert res.status_code == 403


def test_put_badstream(client, db, bucket, multipart, multipart_url, get_json,
                       admin_user):
    """Test uploading to a completed multipart upload."""
    login_user(client, admin_user)

    client.put(
        multipart_url + '&partNumber={0}'.format(1),
        input_stream=BytesIO(b'a' * multipart.chunk_size),
    )

    # Part exists
    data = get_json(client.get(multipart_url), code=200)
    assert len(data['parts']) == 1

    pytest.raises(
        ValueError,
        client.put,
        multipart_url + '&partNumber={0}'.format(1),
        input_stream=BadBytesIO(b'b' * multipart.chunk_size),
    )

    # Part was removed due to faulty upload which might have written partial
    # content to the file.
    data = get_json(client.get(multipart_url), code=200)
    assert len(data['parts']) == 0


def test_get(client, db, bucket, permissions, multipart, multipart_url,
             get_json):
    """Test get parts."""
    Part.create(multipart, 0)
    Part.create(multipart, 1)
    Part.create(multipart, 3)
    db.session.commit()

    cases = [
        (None, 404),
        ('auth', 404),
        ('objects', 404),
        ('bucket', 200),
        ('location', 200),
    ]

    for user, expected in cases:
        login_user(client, permissions[user])

        res = client.get(multipart_url)
        assert res.status_code == expected

        if res.status_code == 200:
            data = get_json(res)
            assert len(data['parts']) == 3


def test_get_empty(client, multipart, multipart_url, get_json, admin_user):
    """Test get parts when empty."""
    login_user(client, admin_user)

    data = get_json(client.get(multipart_url), code=200)
    assert len(data['parts']) == 0
    assert data['id'] == str(multipart.upload_id)


def test_get_serialization(client, multipart, multipart_url, get_json,
                           admin_user):
    """Test get parts when empty."""
    login_user(client, admin_user)

    client.put(
        multipart_url + '&partNumber={0}'.format(1),
        input_stream=BytesIO(b'a' * multipart.chunk_size),
    )

    data = get_json(client.get(multipart_url), code=200)
    assert len(data['parts']) == 1

    expected_keys = [
        'part_number', 'start_byte', 'end_byte', 'checksum', 'created',
        'updated'
    ]
    for k in expected_keys:
        assert k in data['parts'][0]

    expected_keys = [
        'id', 'bucket', 'key', 'completed', 'size', 'part_size', 'links',
        'last_part_number', 'last_part_size', 'created', 'updated',
    ]
    for k in expected_keys:
        assert k in data


@pytest.mark.parametrize('user, expected', [
    (None, 404),
    ('auth', 404),
    ('objects', 404),
    ('bucket', 200),
    ('location', 200),
])
def test_post_complete(client, headers, permissions, bucket, multipart,
                       multipart_url, parts, get_json, user, expected):
    """Test complete multipart upload."""
    login_user(client, permissions[user])

    # Mock celery task to emulate real usage.
    def _mock_celery_result():
        yield False
        yield False
        merge_multipartobject(str(multipart.upload_id))
        yield True

    result_iter = _mock_celery_result()

    task_result = MagicMock()
    task_result.ready = MagicMock(side_effect=lambda *args: next(result_iter))
    task_result.successful = MagicMock(return_value=True)

    # Complete multipart upload
    with patch('invenio_files_rest.views.merge_multipartobject') as task:
        task.delay = MagicMock(return_value=task_result)

        res = client.post(multipart_url)
        assert res.status_code == expected

        if res.status_code == 200:
            data = get_json(res)
            assert data['completed'] is True
            assert task.called_with(str(multipart.upload_id))
            # Two whitespaces expected to have been sent to client before
            # JSON was sent.
            assert res.data.startswith(b'  {')

            # Multipart object no longer exists
            assert client.get(multipart_url).status_code == 404

            # # Object exists
            # assert client.get(data['links']['object']).status_code == 200


def test_post_complete_fail(client, headers, bucket, multipart,
                            multipart_url, parts, get_json, admin_user):
    """Test completing multipart when merge fails."""
    login_user(client, admin_user)

    # Mock celery task to emulate real usage.
    task_result = MagicMock()
    task_result.ready = MagicMock(side_effect=[False, False, True])
    task_result.successful = MagicMock(return_value=False)

    # Complete multipart upload
    with patch('invenio_files_rest.views.merge_multipartobject') as task:
        task.delay = MagicMock(return_value=task_result)

        res = client.post(multipart_url)
        data = get_json(res, code=200)
        assert res.data.startswith(b'  {')
        assert data['status'] == 500
        assert data['message'] == 'Job failed.'

        # Multipart object still exists.
        data = get_json(client.get(multipart_url), code=200)
        assert data['completed'] is True

        # # Object doesn't exists yet.
        # assert client.get(data['links']['object']).status_code == 404


def test_post_complete_timeout(app, client, headers, bucket, multipart,
                               multipart_url, parts, get_json, admin_user):
    """Test completing multipart when merge fails."""
    login_user(client, admin_user)

    max_rounds = int(
        app.config['FILES_REST_TASK_WAIT_MAX_SECONDS'] //
        app.config['FILES_REST_TASK_WAIT_INTERVAL'])

    # Mock celery task to emulate real usage.
    task_result = MagicMock()
    task_result.ready = MagicMock(return_value=False)

    # Complete multipart upload
    with patch('invenio_files_rest.views.merge_multipartobject') as task:
        task.delay = MagicMock(return_value=task_result)

        res = client.post(multipart_url)
        data = get_json(res, code=200)
        assert res.data.startswith(b' ' * max_rounds)
        assert data['status'] == 500
        assert data['message'] == 'Job timed out.'

        # Multipart object still exists.
        data = get_json(client.get(multipart_url), code=200)
        assert data['completed'] is True

        # # Object doesn't exists yet.
        # assert client.get(data['links']['object']).status_code == 404


def test_delete(client, db, bucket, multipart, multipart_url, permissions,
                parts, get_json):
    """Test complete when parts are missing."""
    assert bucket.size == multipart.size

    cases = [
        (None, 404),
        ('auth', 404),
        ('objects', 404),
        ('bucket', 404),
        ('location', 204),
    ]

    for user, expected in cases:
        login_user(client, permissions[user])
        res = client.delete(multipart_url)
        assert res.status_code == expected

        if res.status_code == 204:
            assert client.get(multipart_url).status_code == 404
            assert MultipartObject.query.count() == 0
            assert Part.query.count() == 0
            assert Bucket.get(bucket.id).size == 0


def test_delete_invalid(client, db, multipart, multipart_url,
                        parts, get_json):
    """Test complete when parts are missing."""
    multipart.complete()
    db.session.commit()
    res = client.delete(multipart_url)
    assert res.status_code == 404


def test_delete_init_not_allowed(client, bucket):
    """Test get request to ?uploads."""
    res = client.delete(
        obj_url(bucket),
        query_string='uploads',
    )
    assert res.status_code == 405


def test_get_listuploads(client, db, bucket, multipart, multipart_url,
                         permissions, parts, get_json):
    """Test get list of multipart uploads in bucket."""
    cases = [
        (None, 404),
        ('auth', 404),
        ('objects', 404),
        ('bucket', 404),
        ('location', 200),
    ]

    for user, expected in cases:
        login_user(client, permissions[user])

        res = client.get(url_for(
            'invenio_files_rest.bucket_api',
            bucket_id=str(bucket.id),
        ) + '?uploads')
        assert res.status_code == expected


def test_already_exhausted_input_stream(app, client, db, bucket, admin_user):
    """Test server error when file stream is already read."""
    key = 'test.json'
    data = b'{"json": "file"}'
    object_url = url_for(
        'invenio_files_rest.object_api', bucket_id=bucket.id, key=key)
    # Add a new before request hook which reads the incoming request payload.
    # This simulates what happens when Sentry's raven-python library when it
    # reads the JSON payloads, breaking the upload of JSON files
    # (`application/json`).

    def consume_request_input_stream(*args):
        """Reads input stream object."""
        from flask import request
        request.data

    app.before_request(consume_request_input_stream)
    login_user(client, admin_user)
    resp = client.put(
        object_url,
        input_stream=BytesIO(data),
    )
    assert resp.status_code == 400
    # resp = client.post(
    #     object_url,
    #     input_stream=BytesIO(data),
    # )
    # assert resp.status_code == 500
def assert_role(response,is_permission,status_code=403):
    if is_permission:
        assert response.status_code != status_code
    else:
        assert response.status_code == status_code
        
def test_lock_upload_id(app, client, multipart, users, admin_user, redis_connect):
    # status 403
    login_user(client, users[0])
    res = client.post("/largeFileUpload/lock_upload_id")
    assert_role(res, False)
    
    # mocker.patch("weko_admin.utils.RedisConnection.connection",return_value=redis_connect)
    with patch("invenio_files_rest.views.RedisConnection.connection", return_value=redis_connect):
        # status 200
        login_user(client, admin_user)
        res = client.post("/largeFileUpload/lock_upload_id?upload_id=" + str(multipart.upload_id))
        assert res.status_code == 200
        
        # status 500
        res = client.post("/largeFileUpload/lock_upload_id?upload_idabc")
        assert res.status_code == 500
        
    m = MagicMock()
    m.iter_keys = lambda: ["upload_id" + str(multipart.upload_id)]
    
    with patch("invenio_files_rest.views.RedisConnection.connection", return_value=m):
        # status 400
        res = client.post("/largeFileUpload/lock_upload_id?upload_id=" + str(multipart.upload_id))
        assert res.status_code == 400
        
def test_unlock_upload_id(app, client, multipart, users, admin_user, redis_connect):
    # status 403
    login_user(client, users[0])
    res = client.post("/largeFileUpload/unlock_upload_id")
    assert_role(res, False)
    
    with patch("invenio_files_rest.views.RedisConnection.connection", return_value=redis_connect):
        # status 200
        login_user(client, admin_user)
        res = client.post("/largeFileUpload/unlock_upload_id?upload_id=" + str(multipart.upload_id))
        assert res.status_code == 200
        
        # status 500
        res = client.post("/largeFileUpload/unlock_upload_id?upload_idabc")
        assert res.status_code == 500

def test_createFileInstance(client, bucket, users, admin_user):
    # status 403
    login_user(client, users[0])
    res = client.post("/largeFileUpload/createFileInstance")
    assert_role(res, False)
    
    # status 400
    login_user(client, admin_user)
    res = client.post("/largeFileUpload/createFileInstance?size=")
    assert res.status_code == 400
    
    # status 200
    res = client.post("/largeFileUpload/createFileInstance?size=" + str(10 * 1024 * 1024 * 1024))
    assert res.status_code == 200
    
    # status 500
    res = client.post("/largeFileUpload/createFileInstance?size=abc")
    assert res.status_code == 500
    
def test_checkMultipartObjectInstance(app, client, bucket, db, multipart, users, admin_user):
    # status 403
    login_user(client, users[0])
    res = client.post("/largeFileUpload/checkMultipartObjectInstance")
    assert_role(res, False)
    
    # status 200
    login_user(client, admin_user)
    res = client.post("/largeFileUpload/checkMultipartObjectInstance?upload_id=" + str(multipart.upload_id))
    assert res.status_code == 200
    
    with db.session.begin_nested():
        multipart.created = multipart.created - timedelta(days=5)
        db.session.add(multipart)
    db.session.commit()
    
    # status 404
    res = client.post("/largeFileUpload/checkMultipartObjectInstance?upload_id=" + str(multipart.upload_id))
    assert res.status_code == 404
    
    with db.session.begin_nested():
        multipart.completed = True
        db.session.add(multipart)
    db.session.commit()
    
    # status 400
    res = client.post("/largeFileUpload/checkMultipartObjectInstance?upload_id=" + str(multipart.upload_id))
    assert res.status_code == 400
    
    # status 500
    res = client.post("/largeFileUpload/checkMultipartObjectInstance?upload_id=abc")
    assert res.status_code == 500

def test_createMultipartObject(app, client, bucket, db, multipart, users, admin_user):
    # status 403
    login_user(client, users[0])
    res = client.post("/largeFileUpload/createMultipartObjectInstance")
    assert res.status_code == 403
    
    login_user(client, admin_user)
    
    # status 400
    res = client.post(f"/largeFileUpload/createMultipartObjectInstance?file_id={multipart.file_id}&key={multipart.key}&size={str(10 * 1024 * 1024 * 1024)}&chunk_size={str(100 * 1024 * 1024)}")
    assert res.status_code == 400
    
    # status 200
    uuid1 = str(uuid.uuid4())
    res = client.post("/largeFileUpload/createFileInstance?size=" + str(10 * 1024 * 1024 * 1024))
    uuid2 = res.get_data().decode()
    
    res = client.post(f"/largeFileUpload/createMultipartObjectInstance?upload_id={uuid1}&file_id={uuid2}&key={multipart.key}&size={str(10 * 1024 * 1024 * 1024)}&chunk_size={str(100 * 1024 * 1024)}")
    assert res.status_code == 200
    
    # status 500
    with patch("invenio_files_rest.views.db") as db:
        db.session.add = MagicMock(side_effect = lambda: "error")
        res = client.post(f"/largeFileUpload/createMultipartObjectInstance?upload_id={uuid1}&file_id={uuid2}&key={multipart.key}&size={str(10 * 1024 * 1024 * 1024)}&chunk_size={str(100 * 1024 * 1024)}")
        assert res.status_code == 500
        
def test_get_or_create_part(app, client, bucket, db, multipart, users, admin_user):
    # status 403
    login_user(client, users[0])
    res = client.get("/largeFileUpload/part")
    assert res.status_code == 403
    
    # GET status 400
    login_user(client, admin_user)
    res = client.get(f"/largeFileUpload/part?upload_id={multipart.upload_id}")
    assert res.status_code == 400
    
    # GET status 200
    res = client.get(f"/largeFileUpload/part?upload_id={multipart.upload_id}&part_number=1&check_sum=abcdefg")
    assert res.status_code == 200
    
    # POST status 200
    res = client.post(f"/largeFileUpload/part?upload_id={multipart.upload_id}&part_number=1&check_sum=abcdefg")
    assert res.status_code == 200
    
    # GET status 200
    res = client.get(f"/largeFileUpload/part?upload_id={multipart.upload_id}&part_number=1&check_sum=abcdefg")
    assert res.status_code == 200

    # POST status 500
    res = client.post(f"/largeFileUpload/part?upload_id={multipart.upload_id}&part_number=1&check_sum=abcdefg")
    assert res.status_code == 500

def test_complete_multipart(app, client, bucket, db, multipart, users, admin_user):
    # status 403
    login_user(client, users[0])
    res = client.post("/largeFileUpload/complete_multipart")
    assert res.status_code == 403
    
    # status 400
    login_user(client, admin_user)
    res = client.post("/largeFileUpload/complete_multipart")
    assert res.status_code == 400
    
    # status 200
    res = client.post(f"/largeFileUpload/complete_multipart?upload_id={multipart.upload_id}")
    assert res.status_code == 200
    
    # status 500
    res = client.post(f"/largeFileUpload/complete_multipart?upload_id=")
    assert res.status_code == 500
    
def test_get_multipart_last_part_size(app, client, db, bucket, multipart, admin_user):
    login_user(client, admin_user)
    for i in range(0,6):
        Part.create(multipart, i)
    db.session.commit()
    multipart.complete()
    db.session.commit()
    ObjectVersion.create(multipart.bucket, multipart.key, multipart.file_id)
    db.session.commit()
    res = client.get(f"/files/{str(multipart.bucket_id)}/{str(multipart.key)}?upload_id={multipart.upload_id}&last_part_size=True")
    assert res.status_code == 200
    
def test_multipart_listparts(app, client, db, bucket, multipart, admin_user):
    login_user(client, admin_user)
    for i in range(0,6):
        Part.create(multipart, i)
    db.session.commit()
    ObjectVersion.create(multipart.bucket, multipart.key, multipart.file_id)
    db.session.commit()
    res = client.get(f"/files/{str(multipart.bucket_id)}/{str(multipart.key)}?upload_id={multipart.upload_id}")
    assert res.status_code == 200
    
def test_multipart_init1(app, client, db, bucket, admin_user, redis_connect):
    login_user(client, admin_user)
    
    # MissingQueryParameter('size')
    res = client.post(f"/files/{str(bucket.id)}/sample?uploads")
    assert res.status_code == 403
    
    # MissingQueryParameter('part_size')
    res = client.post(f"/files/{str(bucket.id)}/sample?uploads&size=100")
    assert res.status_code == 403
        
def test_multipart_init2(app, client, db, bucket, admin_user, redis_connect):
    login_user(client, admin_user)
    # normal
    with patch("invenio_files_rest.views.RedisConnection.connection", return_value=redis_connect):
        res = client.post(f"/files/{str(bucket.id)}/sample?uploads&size=100&part_size=10")
        assert res.status_code == 200
        
def test_multipart_uploadpart1(app, client, db, bucket, multipart, admin_user, redis_connect):
    s = MagicMock()
    login_user(client, admin_user)
    
    with patch("invenio_files_rest.current_files_rest.multipart_partfactory", return_value = (0, 1, s, None, None, None)):
        
        res = client.put(f"/files/{str(bucket.id)}/{multipart.key}?upload_id={multipart.upload_id}")
        assert res.status_code == 200
        
    with patch("invenio_files_rest.current_files_rest.multipart_partfactory", return_value = (10, 1, s, None, None, None)):
        
        # error MultipartInvalidChunkSize
        res = client.put(f"/files/{str(bucket.id)}/{multipart.key}?upload_id={multipart.upload_id}")
        assert res.status_code == 403
        
def test_multipart_uploadpart2(app, client, db, bucket, multipart, admin_user, redis_connect):
    s = MagicMock()
    login_user(client, admin_user)
    with patch("invenio_files_rest.current_files_rest.multipart_partfactory", return_value = (20, 1, s, None, None, None)):
        with patch("invenio_files_rest.views.RedisConnection.connection", return_value=redis_connect):
            
            # error MultipartExhausted
            res = client.put(f"/files/{str(bucket.id)}/{multipart.key}?upload_id={multipart.upload_id}")
            assert res.status_code == 400
        
            redis_connect.put(
                    "upload_id" + str(multipart.upload_id),
                    b"lock"
                    )
            
            s.read = MagicMock(side_effect = lambda: "error")
            
            # error Exception
            res = client.put(f"/files/{str(bucket.id)}/{multipart.key}?upload_id={multipart.upload_id}")
            assert res.status_code == 403
            
def test_multipart_uploadpart3(app, client, db, bucket, multipart, admin_user, redis_connect):
    s = MagicMock()
    login_user(client, admin_user)
    with patch("invenio_files_rest.current_files_rest.multipart_partfactory", return_value = (20, 1, s, None, None, None)):
        with patch("invenio_files_rest.views.RedisConnection.connection", return_value=redis_connect):
            redis_connect.put(
                    "upload_id" + str(multipart.upload_id),
                    b"lock"
                    )

            s.read = MagicMock(return_value = io.BytesIO(b"abcdefg"))
            
            with patch("invenio_files_rest.views.get_hash", return_value="hash"):
                # normal
                res = client.put(f"/files/{str(bucket.id)}/{multipart.key}?upload_id={multipart.upload_id}")
                assert res.status_code == 200
    
        
def test_multipart_complete(app, client, db, bucket, multipart, admin_user, redis_connect):
    login_user(client, admin_user)
    for i in range(0,6):
        Part.create(multipart, i)
    db.session.commit()
    with patch("invenio_files_rest.views.RedisConnection.connection", return_value=redis_connect):
        res = client.post(f"/files/{str(bucket.id)}/{multipart.key}?upload_id={multipart.upload_id}")
        assert res.status_code == 200
        
def test_multipart_delete(client, db, bucket, multipart, admin_user):
    login_user(client, admin_user)
    for i in range(0,6):
        Part.create(multipart, i)
    db.session.commit()
    res = client.delete(f"/files/{str(bucket.id)}/{multipart.key}?upload_id={multipart.upload_id}")
    assert res.status_code == 200

def test_ObjectResource_get_with_parameter(client, db, bucket, multipart, objects, admin_user, multipart_url):
    login_user(client, admin_user)
    for i in range(0,6):
        Part.create(multipart, i)
    db.session.commit()
    
    res = client.get(f"/files/{str(multipart.bucket_id)}/{str(multipart.key)}?upload_id={multipart.upload_id}&last_part_size=True")
    assert res.status_code == 200
    
    res = client.get(f"/files/{str(multipart.bucket_id)}/{str(multipart.key)}?upload_id={multipart.upload_id}")
    assert res.status_code == 200
            
def test_ObjectResource_get_without_parameter(client, db, bucket, multipart, objects, admin_user, multipart_url):
    login_user(client, admin_user)
    for i in range(0,6):
        Part.create(multipart, i)
    db.session.commit()
    
    multipart.complete()
    db.session.commit()
    
    with patch("invenio_files_rest.views.ObjectResource.get_object", return_value = objects[0]):
        with patch("invenio_files_rest.views.ObjectResource.send_object", return_value = True):
            res = client.get(f"/files/{str(multipart.bucket_id)}/{str(multipart.key)}")
            assert res.status_code == 200
            
def test_ObjectResource_post_abort(client, db, bucket, multipart, admin_user):
    login_user(client, admin_user)
    
    res = client.post(f"/files/{str(multipart.bucket_id)}/{str(multipart.key)}")
    assert res.status_code == 403
    
    with patch("invenio_files_rest.views.ObjectResource.multipart_init", side_effect = lambda: "error"):
        res = client.post(f"/files/{str(multipart.bucket_id)}/{str(multipart.key)}?uploads")
        assert res.status_code == 403
        
def test_ObjectResource_put_abort(client, multipart, admin_user):
    login_user(client, admin_user)
    
    with patch("invenio_files_rest.views.ObjectResource.multipart_uploadpart", side_effect = lambda: "error"):
        res = client.put(f"/files/{str(multipart.bucket_id)}/{str(multipart.key)}?upload_id={multipart.upload_id}")
        assert res.status_code == 403

def test_ObjectResource_delete(client, db, bucket, multipart, objects, admin_user):
    login_user(client, admin_user)
    
    with patch("invenio_files_rest.views.ObjectResource.get_object", return_value = objects[0]):
        res = client.delete(f"/files/{str(multipart.bucket_id)}/{str(multipart.key)}?version_id={objects[0].version_id}")
        assert res.status_code == 204