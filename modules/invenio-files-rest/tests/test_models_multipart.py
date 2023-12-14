# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test of multipart objects."""

from __future__ import absolute_import, print_function

import hashlib
from os.path import exists
from unittest.mock import MagicMock, patch

from six import BytesIO

from invenio_files_rest.models import Bucket, MultipartObject, ObjectVersion, \
    Part
from flask_login.utils import login_user


def make_stream(size):
    """Make a stream of a given size."""
    s = BytesIO()
    s.seek(size - 1)
    s.write(b'\0')
    s.seek(0)
    return s


def test_multipart_creation(app, db, bucket, admin_user):
    """Test multipart creation."""
    with app.test_request_context():
        login_user(admin_user)
        mp = MultipartObject.create(bucket, 'test.txt', 100, 20)
        db.session.commit()
        assert mp.upload_id
        assert mp.size == 100
        assert mp.chunk_size == 20
        assert mp.completed is False
        assert mp.bucket.size == 100
        # assert exists(mp.file.uri)
        
        try:
            mp = MultipartObject.create(bucket, 'test.txt', 1, 20)
        except:
            pass


def test_multipart_last_part(app, db, bucket, admin_user):
    """Test multipart creation."""
    with app.test_request_context():
        login_user(admin_user)
        mp = MultipartObject.create(bucket, 'test.txt', 100, 20)
        assert mp.last_part_size == 0
        assert mp.last_part_number == 4
        mp = MultipartObject.create(bucket, 'test.txt', 101, 20)
        assert mp.last_part_size == 1
        assert mp.last_part_number == 5


def test_part_creation(app, client, db, bucket, get_sha256, admin_user):
    """Test part creation."""
    assert bucket.size == 0
    with app.test_request_context(): 
        login_user(admin_user)
        mp = MultipartObject.create(bucket, 'test.txt', 5, 2)
        db.session.commit()
        assert bucket.size == 5

        try:
            Part.create(mp, -1)
        except:
            pass
        Part.create(mp, 2, stream=BytesIO(b'p'))
        Part.create(mp, 0, stream=BytesIO(b'p1'))
        Part.create(mp, 1, stream=BytesIO(b'p2'))
        db.session.commit()
        assert bucket.size == 5

        mp.complete()
        db.session.commit()
        assert bucket.size == 5

        # Assert checksum of part.
        # m = hashlib.sha256()
        # m.update(b'p2')
        # assert "sha256:{0}".format(m.hexdigest()) == \
        #     Part.get_or_none(mp, 1).checksum

        # obj = mp.merge_parts()
        # db.session.commit()
        # assert bucket.size == 5

        # assert MultipartObject.query.count() == 0
        # assert Part.query.count() == 0

        # assert obj.file.size == 5
        # assert obj.file.checksum == get_sha256(b'p1p2p')
        # assert obj.file.storage().open().read() == b'p1p2p'
        # assert obj.file.writable is False
        # assert obj.file.readable is True

        # assert obj.version_id == ObjectVersion.get(bucket, 'test.txt').version_id


def test_multipart_full(app, db, bucket):
    """Test full multipart object."""
    app.config.update(dict(
        FILES_REST_MULTIPART_CHUNKSIZE_MIN=5 * 1024 * 1024,
        FILES_REST_MULTIPART_CHUNKSIZE_MAX=5 * 1024 * 1024 * 1024,
    ))

    # Initial parameters
    chunks = 20
    chunk_size = 5 * 1024 * 1024  # 5 MiB
    last_chunk = 1024 * 1024  # 1 MiB
    size = (chunks - 1) * chunk_size + last_chunk

    # Initiate
    mp = MultipartObject.create(
        bucket, 'testfile', size=size, chunk_size=chunk_size)
    db.session.commit()

    # Create parts
    for i in range(chunks):
        part_size = chunk_size if i < chunks - 1 else last_chunk
        Part.create(mp, i, stream=make_stream(part_size))
        db.session.commit()

    # Complete
    mp.complete()
    db.session.commit()

    # Merge parts.
    pre_size = mp.bucket.size
    mp.merge_parts()
    db.session.commit()

    # Test size update
    bucket = Bucket.get(bucket.id)
    assert bucket.size == pre_size

    app.config.update(dict(
        FILES_REST_MULTIPART_CHUNKSIZE_MIN=2,
        FILES_REST_MULTIPART_CHUNKSIZE_MAX=20,
    ))

def test_remove(app, db, bucket, multipart):
    assert bucket == bucket.remove()
    assert Bucket.query.count() == 0
    
def test_delete(app, db, bucket, multipart, permissions):
    assert multipart.file == multipart.file.delete()
    
def test_create(app, db, bucket):
    key = "key1"
    content = b"abcdefg"
    assert ObjectVersion.create(
            bucket, key, stream=BytesIO(content), current_login_user_id=1, size=len(content)
        ).created_user_id == 1

def test_complete(app, db, bucket, multipart):
    try:
        multipart.complete()
    except:
        assert True
    
    for i in range(0,6):
        Part.create(multipart, i)
    db.session.commit()
    assert multipart.complete().completed == True
    
def test_merge_parts(db, multipart):
    for i in range(0,6):
        Part.create(multipart, i)
    db.session.commit()
    multipart.complete()
    multipart.merge_parts()
    assert Part.query.filter_by(upload_id=multipart.upload_id).count() == 0
    
def test_get_by_uploadId(db, multipart):
    assert MultipartObject.get_by_uploadId(multipart.upload_id) == multipart
    
def test_get_by_fileId(multipart):
    assert MultipartObject.get_by_fileId(multipart.file_id) == multipart
     
def test_query_by_file_id(db, multipart):
    assert MultipartObject.query_by_file_id(multipart.file_id).first() == multipart
    
def test_get_by_upload_id_partNumber(db, multipart):
    for i in range(0,6):
        Part.create(multipart, i)
    db.session.commit()
    assert Part.get_by_upload_id_partNumber(multipart.upload_id, 1).multipart == multipart
    
def test_get_or_create(db, multipart):
    assert Part.get_or_create(multipart, 1, None)
    p = Part.create(multipart, 2)
    with patch("invenio_files_rest.models.Part.get_or_none", return_value = p):
        assert Part.get_or_create(multipart, 2, None).multipart == multipart
    
