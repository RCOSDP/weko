# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

# .tox/c1/bin/pytest --cov=invenio_files_rest tests/test_models.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-files-rest/.tox/c1/tmp

"""Module test views."""

from __future__ import absolute_import, print_function

import sys,os
import uuid
from os.path import getsize
from mock import patch
import shutil

import pytest
from fs.errors import ResourceNotFoundError
from six import BytesIO, b
from sqlalchemy.exc import IntegrityError

from invenio_files_rest.errors import BucketLockedError, \
    FileInstanceAlreadySetError, FileInstanceUnreadableError, \
    InvalidKeyError, InvalidOperationError
from invenio_files_rest.models import Bucket, BucketTag, FileInstance, \
    Location, ObjectVersion, ObjectVersionTag


def test_location(app, db):
    """Test location model."""
    with db.session.begin_nested():
        l1 = Location(name='test1', uri='file:///tmp', default=False)
        l2 = Location(name='test2', uri='file:///tmp', default=True)
        l3 = Location(name='test3', uri='file:///tmp', default=False)
        db.session.add(l1)
        db.session.add(l2)
        db.session.add(l3)

    assert Location.get_by_name('test1').name == 'test1'
    assert Location.get_by_name('test2').name == 'test2'
    assert Location.get_by_name('test3').name == 'test3'

    assert Location.get_default().name == 'test2'
    assert len(Location.all()) == 3

    assert str(Location.get_by_name('test1')) == 'test1'


def test_location_default(app, db):
    """Test location model."""
    with db.session.begin_nested():
        l1 = Location(name='test1', uri='file:///tmp', default=False)
        db.session.add(l1)

    assert Location.get_default() is None

    with db.session.begin_nested():
        l2 = Location(name='test2', uri='file:///tmp', default=True)
        l3 = Location(name='test3', uri='file:///tmp', default=True)
        db.session.add(l2)
        db.session.add(l3)

    assert Location.get_default() is None


def test_location_validation(app, db):
    """Test validation of location name."""
    pytest.raises(ValueError, Location, name='UPPER', uri='file://', )
    pytest.raises(ValueError, Location, name='1ab', uri='file://', )
    pytest.raises(ValueError, Location, name='a' * 21, uri='file://', )


def test_bucket_removal(app, db, bucket, objects):
    """Test removal of bucket."""
    assert Bucket.query.count() == 1
    assert ObjectVersion.query.count() == 4
    assert FileInstance.query.count() == 4
    bucket.locked = True
    pytest.raises(BucketLockedError, bucket.remove)
    bucket.locked = False
    bucket.remove()
    assert Bucket.query.count() == 0
    assert ObjectVersion.query.count() == 0
    assert FileInstance.query.count() == 4


def test_bucket_kwargs_creation(app, db, dummy_location):
    """Test kwargs during object creation."""
    b = Bucket.create(quota_size=100, max_file_size=10)
    assert b.quota_size == 100
    assert b.max_file_size == 10


def test_bucket_create_object(app, db):
    """Test bucket creation."""
    with db.session.begin_nested():
        l1 = Location(name='test1', uri='file:///tmp/1', default=False)
        l2 = Location(name='test2', uri='file:///tmp/2', default=True)
        db.session.add(l1)
        db.session.add(l2)

    assert Location.query.count() == 2

    # Simple create
    with db.session.begin_nested():
        b = Bucket.create()
        assert b.id
        assert b.default_location == Location.get_default().id
        assert b.location == Location.get_default()
        assert b.default_storage_class == \
            app.config['FILES_REST_DEFAULT_STORAGE_CLASS']
        assert b.size == 0
        assert b.quota_size is None
        assert b.max_file_size is None
        assert b.deleted is False

    # __repr__ test
    assert str(b) == str(b.id)

    # Retrieve one
    assert Bucket.get(b.id).id == b.id

    # Create with location_name and storage class
    with db.session.begin_nested():
        b = Bucket.create(location=l1, storage_class='A')
        assert b.default_location == Location.get_by_name('test1').id
        assert b.default_storage_class == 'A'

        # Create using location name instead
        b = Bucket.create(location=l2.name, storage_class='A')
        assert b.default_location == Location.get_by_name('test2').id

    # Retrieve one
    assert Bucket.all().count() == 3

    # Invalid storage class.
    pytest.raises(ValueError, Bucket.create, storage_class='X')


def test_bucket_retrieval(app, db, dummy_location):
    """Test bucket get/create."""
    # Create two buckets
    with db.session.begin_nested():
        b1 = Bucket.create()
        Bucket.create()

    assert Bucket.all().count() == 2

    # Mark one as deleted.
    with db.session.begin_nested():
        b1.deleted = True

    assert Bucket.all().count() == 1


def test_object_create(app, db, dummy_location):
    """Test object creation."""
    with db.session.begin_nested():
        b = Bucket.create()
        # Create one object version
        obj1 = ObjectVersion.create(b, "test")
        assert obj1.bucket_id == b.id
        assert obj1.key == 'test'
        assert obj1.version_id
        assert obj1.file_id is None
        assert obj1.is_head is True
        assert obj1.bucket == b

        # Set fake location.
        obj1.set_location("file:///tmp/obj1", 1, "checksum")

        # Create one object version for same object key
        obj2 = ObjectVersion.create(b, "test")
        assert obj2.bucket_id == b.id
        assert obj2.key == 'test'
        assert obj2.version_id != obj1.version_id
        assert obj2.file_id is None
        assert obj2.is_head is True
        assert obj2.bucket == b

        # Set fake location
        obj2.set_location("file:///tmp/obj2", 2, "checksum")

        # Create a new object version for a different object with no location.
        # I.e. it is considered a delete marker.
        obj3 = ObjectVersion.create(b, "deleted_obj")

        # Create a new object containing key in unicode
        obj4 = ObjectVersion.create(b, u"hellö")

    # Object __repr__
    assert repr(obj1) == \
        u"{0}:{1}:{2}".format(
            obj1.bucket_id, obj1.version_id, obj1.key)

    if sys.version_info[0] >= 3:  # python3
        assert repr(obj4) == \
            u"{0}:{1}:{2}".format(
                obj4.bucket_id, obj4.version_id, obj4.key)
    else:  # python2
        assert repr(obj4) == \
            u"{0}:{1}:{2}".format(
                obj4.bucket_id, obj4.version_id, obj4.key).encode('utf-8')

    # Sanity check
    assert ObjectVersion.query.count() == 4

    # Assert that obj2 is the head version
    obj = ObjectVersion.get(b.id, "test", version_id=obj1.version_id)
    assert obj.version_id == obj1.version_id
    assert obj.is_head is False
    obj = ObjectVersion.get(b.id, "test", version_id=obj2.version_id)
    assert obj.version_id == obj2.version_id
    assert obj.is_head is True
    # Assert that getting latest version gets obj2
    obj = ObjectVersion.get(b.id, "test")
    assert obj.version_id == obj2.version_id
    assert obj.is_head is True

    # Assert that obj3 is not retrievable (without specifying version id).
    assert ObjectVersion.get(b.id, "deleted_obj") is None
    # Assert that obj3 *is* retrievable (when specifying version id).
    assert \
        ObjectVersion.get(b.id, "deleted_obj", version_id=obj3.version_id) == \
        obj3


def test_object_create_with_fileid(app, db, dummy_location):
    """Test object creation."""
    with db.session.begin_nested():
        b = Bucket.create()
        obj = ObjectVersion.create(b, 'test', stream=BytesIO(b'test'))

    assert b.size == 4

    ObjectVersion.create(b, 'test', _file_id=obj.file)
    assert b.size == 8


def test_object_multibucket(app, db, dummy_location):
    """Test object creation in multiple buckets."""
    with db.session.begin_nested():
        # Create two buckets each with an object using the same key
        b1 = Bucket.create()
        b2 = Bucket.create()
        obj1 = ObjectVersion.create(b1, "test")
        obj1.set_location("file:///tmp/obj1", 1, "checksum")
        obj2 = ObjectVersion.create(b2, "test")
        obj2.set_location("file:///tmp/obj2", 2, "checksum")

    # Sanity check
    assert ObjectVersion.query.count() == 2

    # Assert object versions are correctly created in each bucket.
    obj = ObjectVersion.get(b1.id, "test")
    assert obj.is_head is True
    assert obj.version_id == obj1.version_id
    obj = ObjectVersion.get(b2.id, "test")
    assert obj.is_head is True
    assert obj.version_id == obj2.version_id


def test_object_get_by_bucket(app, db, dummy_location):
    """Test object listing."""
    b1 = Bucket.create()
    b2 = Bucket.create()

    # First version of object
    obj1_first = ObjectVersion.create(b1, "test")
    obj1_first.set_location("b1test1", 1, "achecksum")
    # Intermediate version which is a delete marker.
    obj1_intermediate = ObjectVersion.create(b1, "test")
    obj1_intermediate.set_location("b1test2", 1, "achecksum")
    # Latest version of object
    obj1_latest = ObjectVersion.create(b1, "test")
    obj1_latest.set_location("b1test3", 1, "achecksum")
    # Create objects in/not in same bucket using different key.
    ObjectVersion.create(b1, "another").set_location(
        "b1another1", 1, "achecksum")
    ObjectVersion.create(b2, "test").set_location("b2test1", 1, "achecksum")
    db.session.commit()

    # Sanity check
    assert ObjectVersion.query.count() == 5
    assert ObjectVersion.get(b1, "test")
    assert ObjectVersion.get(b1, "another")
    assert ObjectVersion.get(b2, "test")

    # Retrieve objects for a bucket with/without versions
    assert ObjectVersion.get_by_bucket(b1).count() == 2
    assert ObjectVersion.get_by_bucket(b1, versions=True).count() == 4
    assert ObjectVersion.get_by_bucket(b2).count() == 1
    assert ObjectVersion.get_by_bucket(b2, versions=True).count() == 1

    # Assert order of returned objects (alphabetical)
    objs = ObjectVersion.get_by_bucket(b1.id).all()
    assert objs[0].key == "another"
    assert objs[1].key == "test"

    # Assert order of returned objects verions (creation date ascending)
    objs = ObjectVersion.get_by_bucket(b1.id, versions=True).all()
    assert objs[0].key == "another"
    assert objs[1].key == "test"
    assert objs[1].version_id == obj1_latest.version_id
    assert objs[2].key == "test"
    assert objs[2].version_id == obj1_intermediate.version_id
    assert objs[3].key == "test"
    assert objs[3].version_id == obj1_first.version_id


def test_object_delete(app, db, dummy_location):
    """Test object creation."""
    # Create three versions, with latest being a delete marker.
    with db.session.begin_nested():
        b1 = Bucket.create()
        ObjectVersion.create(b1, "test").set_location(
            "b1test1", 1, "achecksum")
        ObjectVersion.create(b1, "test").set_location(
            "b1test2", 1, "achecksum")
        obj_deleted = ObjectVersion.delete(b1, "test")

    assert ObjectVersion.query.count() == 3
    assert ObjectVersion.get(b1, "test") is None
    assert ObjectVersion.get_by_bucket(b1).count() == 0

    obj = ObjectVersion.get(b1, "test", version_id=obj_deleted.version_id)
    assert obj.deleted
    assert obj.file_id is None

    ObjectVersion.create(b1, "test").set_location(
        "b1test4", 1, "achecksum")

    assert ObjectVersion.query.count() == 4
    assert ObjectVersion.get(b1.id, "test") is not None
    assert ObjectVersion.get_by_bucket(b1.id).count() == 1


def test_object_remove(app, db, bucket, objects):
    """Test object remove."""
    obj = objects[0]
    obj_size = obj.file.size
    before_size = bucket.size

    assert ObjectVersion.query.count() == 4
    obj.remove()
    assert ObjectVersion.query.count() == 3
    assert bucket.size == before_size - obj_size

    bucket.locked = True
    obj = objects[1]
    pytest.raises(BucketLockedError, obj.remove)
    assert ObjectVersion.query.count() == 3


def test_object_remove_marker(app, db, bucket, objects):
    """Test object remove."""
    obj = objects[0]
    assert ObjectVersion.query.count() == 4
    obj = ObjectVersion.delete(obj.bucket, obj.key)
    db.session.commit()
    assert ObjectVersion.query.count() == 5
    obj = ObjectVersion.get(obj.bucket, obj.key, version_id=obj.version_id)
    obj.remove()
    assert ObjectVersion.query.count() == 4


def test_object_set_contents(app, db, dummy_location):
    """Test object set contents."""
    with db.session.begin_nested():
        b1 = Bucket.create()
        obj = ObjectVersion.create(b1, "LICENSE")
        assert obj.file_id is None
        assert FileInstance.query.count() == 0

        # Save a file.
        with open('LICENSE', 'rb') as fp:
            obj.set_contents(fp)

    # Assert size, location and checksum
    assert obj.file_id is not None
    assert obj.file.uri is not None
    assert obj.file.size == getsize('LICENSE')
    assert obj.file.checksum is not None
    assert b1.size == obj.file.size

    # Try to overwrite
    with db.session.begin_nested():
        with open('LICENSE', 'rb') as fp:
            pytest.raises(FileInstanceAlreadySetError, obj.set_contents, fp)

    # Save a new version with different content
    with db.session.begin_nested():
        obj2 = ObjectVersion.create(b1, "LICENSE")
        with open('README.rst', 'rb') as fp:
            obj2.set_contents(fp)

    assert obj2.file_id is not None and obj2.file_id != obj.file_id
    assert obj2.file.size == getsize('README.rst')
    assert obj2.file.uri != obj.file.uri
    assert Bucket.get(b1.id).size == obj.file.size + obj2.file.size

    obj2.file.verify_checksum()
    assert obj2.file.last_check_at
    assert obj2.file.last_check is True
    old_checksum = obj2.file.checksum
    obj2.file.checksum = "md5:invalid"
    assert obj2.file.verify_checksum() is False

    previous_last_check = obj2.file.last_check
    previous_last_check_date = obj2.file.last_check_at
    with db.session.begin_nested():
        obj2.file.checksum = old_checksum
        obj2.file.uri = 'invalid'
    pytest.raises(ResourceNotFoundError, obj2.file.verify_checksum)
    assert obj2.file.last_check == previous_last_check
    assert obj2.file.last_check_at == previous_last_check_date

    obj2.file.verify_checksum(throws=False)
    assert obj2.file.last_check is None
    assert obj2.file.last_check_at != previous_last_check_date


def test_object_set_location(app, db, dummy_location):
    """Test object set contents."""
    with db.session.begin_nested():
        b1 = Bucket.create()
        obj = ObjectVersion.create(b1, "LICENSE")
        assert obj.file_id is None
        assert FileInstance.query.count() == 0
        obj.set_location("b1test1", 1, "achecksum")
        assert FileInstance.query.count() == 1
        pytest.raises(
            FileInstanceAlreadySetError,
            obj.set_location, "b1test1", 1, "achecksum")


def test_object_snapshot(app, db, dummy_location):
    """Test snapshot creation."""
    b1 = Bucket.create()
    b2 = Bucket.create()
    ObjectVersion.create(b1, "versioned").set_location("b1v1", 1, "achecksum")
    ObjectVersion.create(b1, "versioned").set_location("b1v2", 1, "achecksum")
    ObjectVersion.create(b1, "deleted").set_location("b1d1", 1, "achecksum")
    ObjectVersion.delete(b1, "deleted")
    ObjectVersion.create(b1, "undeleted").set_location("b1u1", 1, "achecksum")
    ObjectVersion.delete(b1, "undeleted")
    ObjectVersion.create(b1, "undeleted").set_location("b1u2", 1, "achecksum")
    ObjectVersion.create(b1, "simple").set_location("b1s1", 1, "achecksum")
    ObjectVersion.create(b2, "another").set_location("b2a1", 1, "achecksum")
    db.session.commit()

    assert ObjectVersion.query.count() == 9
    assert FileInstance.query.count() == 7
    assert Bucket.query.count() == 2
    assert ObjectVersion.get_by_bucket(b1).count() == 3
    assert ObjectVersion.get_by_bucket(b2).count() == 1

    # check that for 'undeleted' key there is only one HEAD
    heads = [o for o in ObjectVersion.query.filter_by(
        bucket_id=b1.id, key='undeleted').all() if o.is_head]
    assert len(heads) == 1
    assert heads[0].file.uri == 'b1u2'

    b3 = b1.snapshot(lock=True)
    db.session.commit()

    # Must be locked as requested.
    assert b1.locked is False
    assert b3.locked is True

    assert Bucket.query.count() == 3
    assert ObjectVersion.query.count() == 12
    assert FileInstance.query.count() == 7
    assert ObjectVersion.get_by_bucket(b1).count() == 3
    assert ObjectVersion.get_by_bucket(b2).count() == 1
    assert ObjectVersion.get_by_bucket(b3).count() == 3
    assert ObjectVersion.get_by_bucket(b1, versions=True,
                                       with_deleted=True).count() == 8
    assert ObjectVersion.get_by_bucket(b3, versions=True).count() == 3


def test_object_snapshot_deleted(app, db, dummy_location):
    """Test snapshot creation of a deleted bucket."""
    b1 = Bucket.create()
    b2 = Bucket.create()
    b2.deleted = True
    db.session.commit()

    b3 = b1.snapshot()
    assert b3.id != b1.id
    assert b3.locked is False

    # b2 is deleted.
    with pytest.raises(InvalidOperationError) as excinfo:
        b2.snapshot()
    assert excinfo.value.get_body() != {}


def test_bucket_sync_new_object(app, db, dummy_location):
    """Test that a new file in src in synced to dest."""
    b1 = Bucket.create()
    b2 = Bucket.create()
    ObjectVersion.create(b1, "filename").set_location("b1v1", 1, "achecksum")
    db.session.commit()

    assert ObjectVersion.get_by_bucket(b1).count() == 1
    assert ObjectVersion.get_by_bucket(b2).count() == 0
    b1.sync(b2)
    assert ObjectVersion.get_by_bucket(b1).count() == 1
    assert ObjectVersion.get_by_bucket(b2).count() == 1
    assert ObjectVersion.get(b2, "filename")


def test_bucket_sync_same_object(app, db, dummy_location):
    """Test that an exiting file in src and dest is not changed."""
    b1 = Bucket.create()
    b2 = Bucket.create()
    ObjectVersion.create(b1, "filename").set_location("b1v1", 1, "achecksum")
    b1.sync(b2)
    db.session.commit()

    b1_version_id = ObjectVersion.get(b1, "filename").version_id
    b2_version_id = ObjectVersion.get(b2, "filename").version_id

    b1.sync(b2)

    assert ObjectVersion.get_by_bucket(b1).count() == 1
    assert ObjectVersion.get_by_bucket(b2).count() == 1
    assert ObjectVersion.get(b1, "filename").version_id == b1_version_id
    assert ObjectVersion.get(b2, "filename").version_id == b2_version_id


def test_bucket_sync_deleted_object(app, db, dummy_location):
    """Test that a deleted object in src is deleted in dest."""
    b1 = Bucket.create()
    b2 = Bucket.create()
    ObjectVersion.create(b1, "filename").set_location("b1v1", 1, "achecksum")
    ObjectVersion.create(b2, "filename").set_location("b2v1", 1, "achecksum")
    ObjectVersion.create(b2, "extra-deleted").set_location("b3v1", 1, "asum")
    ObjectVersion.delete(b1, "filename")
    db.session.commit()

    b1.sync(b2)

    assert ObjectVersion.get_by_bucket(b1).count() == 0
    assert ObjectVersion.get_by_bucket(b2).count() == 1
    assert ObjectVersion.get(b2, "extra-deleted")

    ObjectVersion.delete(b2, "extra-deleted")
    db.session.commit()

    b1.sync(b2)

    assert ObjectVersion.get_by_bucket(b1).count() == 0
    assert ObjectVersion.get_by_bucket(b2).count() == 0


def test_bucket_sync_delete_extras(app, db, dummy_location):
    """Test that an extra object in dest is deleted when syncing."""
    b1 = Bucket.create()
    b2 = Bucket.create()
    ObjectVersion.create(b1, "filename").set_location("b1v1", 1, "achecksum")
    ObjectVersion.create(b2, "filename").set_location("b2v1", 1, "achecksum")
    ObjectVersion.create(b2, "extra-deleted").set_location("b3v1", 1, "asum")
    db.session.commit()

    b1.sync(b2, delete_extras=True)

    assert ObjectVersion.get_by_bucket(b1).count() == 1
    assert ObjectVersion.get_by_bucket(b2).count() == 1
    assert not ObjectVersion.get(b2, "extra-deleted")


def test_bucket_sync(app, db, dummy_location):
    """Test that a bucket is correctly synced."""
    b1 = Bucket.create()
    b2 = Bucket.create()
    ObjectVersion.create(b1, "filename1").set_location("b1v11", 1, "achecksum")
    ObjectVersion.create(b1, "filename2").set_location("b1v12", 1, "achecksum")
    ObjectVersion.create(b1, "filename3").set_location("b1v13", 1, "achecksum")
    ObjectVersion.create(b2, "extra1").set_location("b2v11", 1, "achecksum")
    db.session.commit()

    b1.sync(b2)

    assert ObjectVersion.get_by_bucket(b1).count() == 3
    assert ObjectVersion.get_by_bucket(b2).count() == 4

    ObjectVersion.delete(b1, "filename1")
    ObjectVersion.create(b2, "extra2").set_location("b2v12", 1, "achecksum")
    ObjectVersion.create(b2, "extra3").set_location("b2v13", 1, "achecksum")
    ObjectVersion.delete(b2, "extra3")
    db.session.commit()

    b1.sync(b2, delete_extras=True)

    assert ObjectVersion.get_by_bucket(b1).count() == 2
    assert ObjectVersion.get_by_bucket(b2).count() == 2


def test_bucket_sync_deleted(app, db, dummy_location):
    """Test bucket sync of a deleted bucket."""
    b1 = Bucket.create()
    b1.deleted = True
    db.session.commit()

    with pytest.raises(InvalidOperationError) as excinfo:
        b1.sync(Bucket.create())
    assert excinfo.value.get_body() != {}


def test_object_copy(app, db, dummy_location):
    """Copy object."""
    f = FileInstance(uri="f1", size=1, checksum="mychecksum")
    db.session.add(f)
    db.session.commit()
    b1 = Bucket.create()
    b2 = Bucket.create()

    # Delete markers cannot be copied
    obj_deleted = ObjectVersion.create(b1, "deleted")
    with pytest.raises(InvalidOperationError) as excinfo:
        obj_deleted.copy(b2)
    assert excinfo.value.get_body() != {}

    # Copy onto self.
    obj = ObjectVersion.create(b1, "selftest").set_file(f)
    db.session.commit()
    obj_copy = obj.copy()
    db.session.commit()
    assert obj_copy.version_id != obj.version_id
    assert obj_copy.key == obj.key
    assert obj_copy.bucket == obj.bucket
    assert obj_copy.file_id == obj.file_id
    versions = ObjectVersion.get_versions(b1, "selftest").all()
    assert versions[0] == obj_copy
    assert versions[1] == obj

    # Copy new key
    obj_copy2 = obj_copy.copy(key='newkeytest')
    db.session.commit()
    assert obj_copy2.version_id != obj_copy.version_id
    assert obj_copy2.key == "newkeytest"
    assert obj_copy2.bucket == obj_copy.bucket
    assert obj_copy2.file_id == obj_copy.file_id

    # Copy to bucket
    obj_copy3 = obj_copy2.copy(bucket=b2)
    assert obj_copy3.version_id != obj_copy2.version_id
    assert obj_copy3.key == obj_copy2.key
    assert obj_copy3.bucket == b2
    assert obj_copy3.file_id == obj_copy2.file_id


def test_object_set_file(app, db, dummy_location):
    """Test object set file."""
    b = Bucket.create()
    f = FileInstance(uri="f1", size=1, checksum="mychecksum")
    obj = ObjectVersion.create(b, "test").set_file(f)
    db.session.commit()
    assert obj.file == f

    assert pytest.raises(FileInstanceAlreadySetError, obj.set_file, f)


def test_object_mimetype(app, db, dummy_location):
    """Test object set file."""
    b = Bucket.create()
    db.session.commit()
    obj1 = ObjectVersion.create(b, "test.pdf", stream=BytesIO(b'pdfdata'))
    obj2 = ObjectVersion.create(b, "README", stream=BytesIO(b'pdfdata'))
    obj3 = ObjectVersion.create(b, "test.csv.gz", stream=BytesIO(b'gzdata'))

    assert obj1.mimetype == "application/pdf"
    assert obj2.mimetype == "application/octet-stream"
    assert obj3.mimetype == "application/gzip"

    # Override computed MIME type.
    obj2.mimetype = "text/plain"
    db.session.commit()
    assert ObjectVersion.get(b, "README").mimetype == "text/plain"


def test_object_restore(app, db, dummy_location):
    """Restore object."""
    f1 = FileInstance(uri="f1", size=1, checksum="mychecksum")
    f2 = FileInstance(uri="f2", size=2, checksum="mychecksum2")
    db.session.add(f1)
    db.session.add(f2)
    b1 = Bucket.create()

    obj1 = ObjectVersion.create(b1, "test").set_file(f1)
    ObjectVersion.create(b1, "test").set_file(f2)
    obj_deleted = ObjectVersion.delete(b1, "test")
    db.session.commit()

    assert ObjectVersion.query.count() == 3
    # Cannot restore a deleted version.
    with pytest.raises(InvalidOperationError) as excinfo:
        obj_deleted.restore()
    assert excinfo.value.get_body() != {}

    # Restore first version
    obj_new = obj1.restore()
    db.session.commit()

    assert ObjectVersion.query.count() == 4
    assert obj_new.is_head is True
    assert obj_new.version_id != obj1.version_id
    assert obj_new.key == obj1.key
    assert obj_new.file_id == obj1.file_id
    assert obj_new.bucket == obj1.bucket


def test_object_relink_all(app, db, dummy_location):
    """Test relinking files."""
    b1 = Bucket.create()
    obj1 = ObjectVersion.create(
        b1, "relink-test", stream=BytesIO(b('relinkthis')))
    ObjectVersion.create(b1, "do-not-touch", stream=BytesIO(b('na')))
    b1.snapshot()
    db.session.commit()

    assert ObjectVersion.query.count() == 4
    assert FileInstance.query.count() == 2

    fnew = FileInstance.create()
    fnew.copy_contents(obj1.file, default_location=b1.location.uri)
    db.session.commit()

    fold = obj1.file

    assert ObjectVersion.query.filter_by(file_id=fold.id).count() == 2
    assert ObjectVersion.query.filter_by(file_id=fnew.id).count() == 0

    ObjectVersion.relink_all(obj1.file, fnew)
    db.session.commit()

    assert ObjectVersion.query.filter_by(file_id=fold.id).count() == 0
    assert ObjectVersion.query.filter_by(file_id=fnew.id).count() == 2


def test_object_validation(app, db, dummy_location):
    """Test validating the ObjectVersion."""
    b1 = Bucket.create()
    ObjectVersion.create(b1, 'x' * 255)  # Should not raise
    pytest.raises(InvalidKeyError, ObjectVersion.create, b1, 'x' * 256)


def test_bucket_tags(app, db, dummy_location):
    """Test bucket tags."""
    b = Bucket.create()
    BucketTag.create(b, "mykey", "testvalue")
    BucketTag.create(b, "another_key", "another value")
    db.session.commit()

    # Duplicate key
    pytest.raises(Exception, BucketTag.create, b, "mykey", "newvalue")

    # Test get
    assert BucketTag.query.count() == 2
    assert BucketTag.get(b.id, "mykey").value == "testvalue"
    assert BucketTag.get_value(b, "another_key") == "another value"
    assert BucketTag.get_value(b.id, "invalid") is None

    # Test delete
    BucketTag.delete(b, "mykey")
    assert BucketTag.query.count() == 1
    BucketTag.delete(b, "invalid")
    assert BucketTag.query.count() == 1

    # Create or update
    BucketTag.create_or_update(b, "another_key", "newval")
    BucketTag.create_or_update(b, "newkey", "testval")
    db.session.commit()
    assert BucketTag.get_value(b, "another_key") == "newval"
    assert BucketTag.get_value(b, "newkey") == "testval"

    # Get tags as dictionary
    assert b.get_tags() == dict(another_key="newval", newkey="testval")

    b2 = Bucket.create()
    assert b2.get_tags() == dict()

    # Test cascading delete.
    Bucket.query.delete()
    db.session.commit()
    assert BucketTag.query.count() == 0


def test_fileinstance_get(app, db, dummy_location):
    """Test fileinstance get."""
    f = FileInstance.create()
    db.session.commit()
    # Get existing file.
    assert FileInstance.get(f.id) is not None
    # Non-existing files returns none
    assert FileInstance.get(uuid.uuid4()) is None


def test_fileinstance_get_by_uri(app, db, dummy_location):
    """Test file get by uri."""
    f = FileInstance.create()
    f.uri = "LICENSE"
    db.session.commit()

    assert FileInstance.get_by_uri("LICENSE") is not None
    FileInstance.get_by_uri("NOTVALID") is None
    pytest.raises(AssertionError, FileInstance.get_by_uri, None)


def test_fileinstance_create(app, db, dummy_location):
    """Test file instance create."""
    f = FileInstance.create()
    assert f.id
    assert f.readable is False
    assert f.writable is True
    assert f.uri is None
    assert f.size == 0
    assert f.checksum is None
    assert f.last_check_at is None
    assert f.last_check is None
    db.session.commit()

    # Check unique constraint on URI with none values.
    f = FileInstance.create()
    f = FileInstance.create()
    db.session.commit()


def test_fileinstance_set_contents(app, db, dummy_location):
    """Test file instance create."""
    counter = dict(called=False)

    def callback(total, size):
        counter['called'] = True

    f = FileInstance.create()
    db.session.commit()
    assert f.readable is False
    assert f.writable is True
    data = BytesIO(b("test file instance set contents"))
    f.set_contents(
        data, default_location=dummy_location.uri, progress_callback=callback)
    db.session.commit()
    assert f.readable is True
    assert f.writable is False
    assert counter['called']

    pytest.raises(
        ValueError,
        f.set_contents,
        BytesIO(b("different content")),
        location=dummy_location,
    )


def test_fileinstance_copy_contents(app, db, dummy_location):
    """Test copy contents."""
    counter = dict(called=False)

    def callback(total, size):
        counter['called'] = True

    # Create source and set data.
    data = b('this is some data')
    src = FileInstance.create()
    src.set_contents(BytesIO(data), default_location=dummy_location.uri)
    db.session.commit()

    # Create destination - and use it to copy_contents from another object.
    dst = FileInstance.create()
    assert dst.size == 0
    assert dst.uri is None
    db.session.commit()

    # Copy contents
    dst.copy_contents(
        src, progress_callback=callback, default_location=dummy_location.uri)
    db.session.commit()
    assert dst.size == src.size
    assert dst.checksum == src.checksum
    assert dst.uri != src.uri
    assert counter['called']

    # Read data
    fp = dst.storage().open()
    assert data == fp.read()
    fp.close()


def test_fileinstance_copy_contents_invalid(app, db, dummy_location):
    """Test invalid copy contents."""
    # Source not readable
    src = FileInstance.create()
    dst = FileInstance.create()
    pytest.raises(ValueError, dst.copy_contents, src)

    # Create valid source
    data = b('this is some data')
    src = FileInstance.create()
    src.set_contents(BytesIO(data), default_location=dummy_location.uri)
    db.session.commit()

    # Destination not writable
    dst.writable = False
    pytest.raises(ValueError, dst.copy_contents, src)
    # Size is not 0
    dst.writable = True
    dst.size = 1
    pytest.raises(ValueError, dst.copy_contents, src)

# .tox/c1/bin/pytest --cov=invenio_files_rest tests/test_models.py::test_fileinstance_send_file -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-files-rest/.tox/c1/tmp
def test_fileinstance_send_file(app, db, dummy_location,dummy_s3_location,mocker):
    """Test file instance send file."""
    f = FileInstance.create()
    # File not readable
    pytest.raises(FileInstanceUnreadableError, f.send_file)

    # Write data
    data = b("test file instance set contents")
    f.set_contents(BytesIO(data), default_location=dummy_location.uri)
    db.session.commit()

    # Send data
    with app.test_request_context():
        res = f.send_file('test.txt')
        assert int(res.headers['Content-Length']) == len(data)

    data = {'url': {'url': 'https://test_server/record/1/files/test_file.docx'}, 'date': [{'dateType': 'Available', 'dateValue': '2023-04-06'}], 'format': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'filename': 'test_file.docx', 'filesize': [{'value': '31 KB'}], 'mimetype': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'accessrole': 'open_access', 'version_id': '174af28a-2a26-428c-ae90-1fae1dffd21c', 'displaytype': 'preview'}
    def mock_convert(pdf_dir,target_uri):
        if os.path.exists(pdf_dir):
            shutil.rmtree(pdf_dir)
        os.makedirs(pdf_dir)
        with open(target_uri,"rb") as f:
            data = f.read()
        with open(pdf_dir+"/data.pdf","wb") as f:
            f.write(data)

    mocker.patch("invenio_files_rest.storage.pyfs.PyFSFileStorage.open",return_value=open(os.path.join(os.path.dirname(__file__),"data/test_file.docx"),"rb"))
    with app.test_request_context("/record/1/files/test_file.docx"):
        with patch("invenio_files_rest.models.convert_to",side_effect=mock_convert) as mock_convert:
            with patch("os.path.isfile",return_value=False):
                f = FileInstance(
                    id=1,
                    uri="s3://test_file.docx",
                    json=data,
                    readable=True
                )
                res = f.send_file("test_file.docx",True,"application/vnd.openxmlformats-officedocument.wordprocessingml.document",False,None,False,True)
                mock_convert.assert_called_with("/var/tmp/pdf_dir/1","/var/tmp/convert_1/test_file.docx")
                shutil.rmtree("/var/tmp/pdf_dir/1")

def test_fileinstance_send_file_s3_path1(app, db, dummy_location,dummy_s3_location,mocker):
    """Test file instance send file."""
    f = FileInstance.create()
    # File not readable
    pytest.raises(FileInstanceUnreadableError, f.send_file)

    # Write data
    data = b("test file instance set contents")
    f.set_contents(BytesIO(data), default_location=dummy_location.uri)
    db.session.commit()

    # Send data
    with app.test_request_context():
        res = f.send_file('test.txt')
        assert int(res.headers['Content-Length']) == len(data)

    data = {'url': {'url': 'https://test_server/record/1/files/test_file.docx'}, 'date': [{'dateType': 'Available', 'dateValue': '2023-04-06'}], 'format': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'filename': 'test_file.docx', 'filesize': [{'value': '31 KB'}], 'mimetype': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'accessrole': 'open_access', 'version_id': '174af28a-2a26-428c-ae90-1fae1dffd21c', 'displaytype': 'preview'}
    def mock_convert(pdf_dir,target_uri):
        if os.path.exists(pdf_dir):
            shutil.rmtree(pdf_dir)
        os.makedirs(pdf_dir)
        with open(target_uri,"rb") as f:
            data = f.read()
        with open(pdf_dir+"/data.pdf","wb") as f:
            f.write(data)

    mocker.patch("invenio_files_rest.storage.pyfs.PyFSFileStorage.open",return_value=open(os.path.join(os.path.dirname(__file__),"data/test_file.docx"),"rb"))
    with app.test_request_context("/record/1/files/test_file.docx"):
        with patch("invenio_files_rest.models.convert_to",side_effect=mock_convert) as mock_convert:
            with patch("os.path.isfile",return_value=False):
                f = FileInstance(
                    id=1,
                    uri="https://s3.amazonaws.com/bucket_name/test_file.docx",
                    json=data,
                    readable=True
                )
                res = f.send_file("test_file.docx",True,"application/vnd.openxmlformats-officedocument.wordprocessingml.document",False,None,False,True)
                mock_convert.assert_called_with("/var/tmp/pdf_dir/1","/var/tmp/convert_1/test_file.docx")
                shutil.rmtree("/var/tmp/pdf_dir/1")

def test_fileinstance_send_file_s3_path2(app, db, dummy_location,dummy_s3_location,mocker):
    """Test file instance send file."""
    f = FileInstance.create()
    # File not readable
    pytest.raises(FileInstanceUnreadableError, f.send_file)

    # Write data
    data = b("test file instance set contents")
    f.set_contents(BytesIO(data), default_location=dummy_location.uri)
    db.session.commit()

    # Send data
    with app.test_request_context():
        res = f.send_file('test.txt')
        assert int(res.headers['Content-Length']) == len(data)

    data = {'url': {'url': 'https://test_server/record/1/files/test_file.docx'}, 'date': [{'dateType': 'Available', 'dateValue': '2023-04-06'}], 'format': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'filename': 'test_file.docx', 'filesize': [{'value': '31 KB'}], 'mimetype': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'accessrole': 'open_access', 'version_id': '174af28a-2a26-428c-ae90-1fae1dffd21c', 'displaytype': 'preview'}
    def mock_convert(pdf_dir,target_uri):
        if os.path.exists(pdf_dir):
            shutil.rmtree(pdf_dir)
        os.makedirs(pdf_dir)
        with open(target_uri,"rb") as f:
            data = f.read()
        with open(pdf_dir+"/data.pdf","wb") as f:
            f.write(data)

    mocker.patch("invenio_files_rest.storage.pyfs.PyFSFileStorage.open",return_value=open(os.path.join(os.path.dirname(__file__),"data/test_file.docx"),"rb"))
    with app.test_request_context("/record/1/files/test_file.docx"):
        with patch("invenio_files_rest.models.convert_to",side_effect=mock_convert) as mock_convert:
            with patch("os.path.isfile",return_value=False):
                f = FileInstance(
                    id=1,
                    uri="https://bucket_name.s3.us-east-1.amazonaws.com/test_file.docx",
                    json=data,
                    readable=True
                )
                res = f.send_file("test_file.docx",True,"application/vnd.openxmlformats-officedocument.wordprocessingml.document",False,None,False,True)
                mock_convert.assert_called_with("/var/tmp/pdf_dir/1","/var/tmp/convert_1/test_file.docx")
                shutil.rmtree("/var/tmp/pdf_dir/1")



def test_fileinstance_validation(app, db, dummy_location):
    """Test validating the FileInstance."""
    f = FileInstance.create()
    f.set_uri('x' * 255, 1000, 1000)  # Should not raise
    pytest.raises(ValueError, f.set_uri, 'x' * 256, 1000, 1000)


def test_object_version_tags(app, db, dummy_location):
    """Test object version tags."""
    f = FileInstance(uri="f1", size=1, checksum="mychecksum")
    db.session.add(f)
    db.session.commit()
    b = Bucket.create()
    obj1 = ObjectVersion.create(b, "test").set_file(f)
    ObjectVersionTag.create(obj1, "mykey", "testvalue")
    ObjectVersionTag.create(obj1, "another_key", "another value")
    db.session.commit()

    # Duplicate key
    pytest.raises(
        IntegrityError, ObjectVersionTag.create, obj1, "mykey", "newvalue")

    # Test get
    assert ObjectVersionTag.query.count() == 2
    assert ObjectVersionTag.get(obj1, "mykey").value == "testvalue"
    assert ObjectVersionTag.get_value(obj1.version_id, "another_key") \
        == "another value"
    assert ObjectVersionTag.get_value(obj1, "invalid") is None

    # Test delete
    ObjectVersionTag.delete(obj1, "mykey")
    assert ObjectVersionTag.query.count() == 1
    ObjectVersionTag.delete(obj1, "invalid")
    assert ObjectVersionTag.query.count() == 1

    # Create or update
    ObjectVersionTag.create_or_update(obj1, "another_key", "newval")
    ObjectVersionTag.create_or_update(obj1.version_id, "newkey", "testval")
    db.session.commit()
    assert ObjectVersionTag.get_value(obj1, "another_key") == "newval"
    assert ObjectVersionTag.get_value(obj1, "newkey") == "testval"

    # Get tags as dictionary
    assert obj1.get_tags() == dict(another_key="newval", newkey="testval")
    obj2 = ObjectVersion.create(b, 'test2')
    assert obj2.get_tags() == dict()

    # Copy object version
    obj_copy = obj1.copy()
    db.session.commit()
    assert obj_copy.get_tags() == dict(another_key="newval", newkey="testval")
    assert ObjectVersionTag.query.count() == 4

    # Cascade delete
    ObjectVersion.query.delete()
    db.session.commit()
    assert ObjectVersionTag.query.count() == 0

def test_get_location_all(app, db, dummy_location):
    """Test validating the FileInstance."""
    f = FileInstance.create()
    locations = f.get_location_all()
    assert locations == [dummy_location]
