# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test of multipart objects."""

import hashlib
from io import BytesIO
from os.path import exists

from invenio_files_rest.models import Bucket, MultipartObject, ObjectVersion, Part


def make_stream(size):
    """Make a stream of a given size."""
    s = BytesIO()
    s.seek(size - 1)
    s.write(b"\0")
    s.seek(0)
    return s


def test_multipart_creation(app, db, bucket):
    """Test multipart creation."""
    mp = MultipartObject.create(bucket, "test.txt", 100, 20)
    db.session.commit()
    assert mp.upload_id
    assert mp.size == 100
    assert mp.chunk_size == 20
    assert mp.completed is False
    assert mp.bucket.size == 100
    assert exists(mp.file.uri)


def test_multipart_last_part(app, db, bucket):
    """Test multipart creation."""
    mp = MultipartObject.create(bucket, "test.txt", 100, 20)
    assert mp.last_part_size == 0
    assert mp.last_part_number == 4
    mp = MultipartObject.create(bucket, "test.txt", 101, 20)
    assert mp.last_part_size == 1
    assert mp.last_part_number == 5


def test_part_creation(app, db, bucket, get_md5):
    """Test part creation."""
    assert bucket.size == 0
    mp = MultipartObject.create(bucket, "test.txt", 5, 2)
    db.session.commit()
    assert bucket.size == 5

    Part.create(mp, 2, stream=BytesIO(b"p"))
    Part.create(mp, 0, stream=BytesIO(b"p1"))
    Part.create(mp, 1, stream=BytesIO(b"p2"))
    db.session.commit()
    assert bucket.size == 5

    mp.complete()
    db.session.commit()
    assert bucket.size == 5

    # Assert checksum of part.
    m = hashlib.md5()
    m.update(b"p2")
    assert "md5:{0}".format(m.hexdigest()) == Part.get_or_none(mp, 1).checksum

    obj = mp.merge_parts()
    db.session.commit()
    assert bucket.size == 5

    assert MultipartObject.query.count() == 0
    assert Part.query.count() == 0

    assert obj.file.size == 5
    assert obj.file.checksum == get_md5(b"p1p2p")
    assert obj.file.storage().open().read() == b"p1p2p"
    assert obj.file.writable is False
    assert obj.file.readable is True

    assert obj.version_id == ObjectVersion.get(bucket, "test.txt").version_id


def test_multipart_full(app, db, bucket):
    """Test full multipart object."""
    app.config.update(
        dict(
            FILES_REST_MULTIPART_CHUNKSIZE_MIN=5 * 1024 * 1024,
            FILES_REST_MULTIPART_CHUNKSIZE_MAX=5 * 1024 * 1024 * 1024,
        )
    )

    # Initial parameters
    chunks = 20
    chunk_size = 5 * 1024 * 1024  # 5 MiB
    last_chunk = 1024 * 1024  # 1 MiB
    size = (chunks - 1) * chunk_size + last_chunk

    # Initiate
    mp = MultipartObject.create(bucket, "testfile", size=size, chunk_size=chunk_size)
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

    app.config.update(
        dict(
            FILES_REST_MULTIPART_CHUNKSIZE_MIN=2,
            FILES_REST_MULTIPART_CHUNKSIZE_MAX=20,
        )
    )
