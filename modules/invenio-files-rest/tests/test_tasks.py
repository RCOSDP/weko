# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module test views."""

import errno
from io import BytesIO
from os.path import exists, join
from unittest.mock import MagicMock, patch

import pytest
from fs.errors import FSError, ResourceNotFound

from invenio_files_rest.models import Bucket, FileInstance, ObjectVersion
from invenio_files_rest.tasks import (
    clear_orphaned_files,
    migrate_file,
    remove_file_data,
    schedule_checksum_verification,
    verify_checksum,
)


def test_verify_checksum(app, db, dummy_location):
    """Test celery tasks for checksum verification."""
    b1 = Bucket.create()
    with open("README.rst", "rb") as fp:
        obj = ObjectVersion.create(b1, "README.rst", stream=fp)
    db.session.commit()
    file_id = obj.file_id

    verify_checksum(str(file_id))

    f = FileInstance.query.get(file_id)
    assert f.last_check_at
    assert f.last_check is True

    f.uri = "invalid"
    db.session.add(f)
    db.session.commit()
    pytest.raises(ResourceNotFound, verify_checksum, str(file_id), throws=True)

    f = FileInstance.query.get(file_id)
    assert f.last_check is True

    verify_checksum(str(file_id), throws=False)
    f = FileInstance.query.get(file_id)
    assert f.last_check is None

    f.last_check = True
    db.session.add(f)
    db.session.commit()
    with pytest.raises(ResourceNotFound):
        verify_checksum(str(file_id), pessimistic=True)
    f = FileInstance.query.get(file_id)
    assert f.last_check is None


def test_schedule_checksum_verification(app, db, dummy_location):
    """Test file checksum verification scheduling celery task."""
    b1 = Bucket.create()
    objects = []
    for i in range(100):
        objects.append(ObjectVersion.create(b1, str(i), stream=BytesIO(b"tests")))
    db.session.commit()

    # 100 files of the 5-byte content 'tests' should be 500 bytes in total
    assert sum(o.file.size for o in objects) == 500

    for obj in objects:
        assert obj.file.last_check is True
        assert obj.file.last_check_at is None

    schedule_task = schedule_checksum_verification.s(
        frequency={"minutes": 20}, batch_interval={"minutes": 1}
    )

    def checked_files():
        return len([o for o in ObjectVersion.get_by_bucket(b1) if o.file.last_check_at])

    # Scheduling for 100 files, for all of them to be checked every 20 minutes,
    # with batches of equal number of file being sent out every minute
    # should total to 20 batches with 5 files per batch.
    schedule_task.apply(kwargs={"max_count": 0})
    assert checked_files() == 5

    # Repeat the schedule
    schedule_task.apply(kwargs={"max_count": 0})
    assert checked_files() == 10

    schedule_task.apply(kwargs={"max_count": 3})  # 3 files are checked
    assert checked_files() == 13

    # Scheduling for 500 bytes of files, for all of them to be checked every 20
    # minutes, with equal in size batches being sent out every minute should
    # total to 20 batches of 25 bytes per batch (5 files).
    schedule_task.apply(kwargs={"max_size": 0})
    assert checked_files() == 18

    schedule_task.apply(kwargs={"max_size": 15})  # 3 files are checked
    assert checked_files() == 21


def test_migrate_file(app, db, dummy_location, extra_location, bucket, objects):
    """Test file migration."""
    obj = objects[0]

    # Test pre-condition
    old_uri = obj.file.uri
    assert exists(old_uri)
    assert old_uri == join(
        dummy_location.uri,
        str(obj.file.id)[0:2],
        str(obj.file.id)[2:4],
        str(obj.file.id)[4:],
        "data",
    )
    assert FileInstance.query.count() == 4

    # Migrate file
    with patch("invenio_files_rest.tasks.verify_checksum") as verify_checksum:
        migrate_file(
            obj.file_id, location_name=extra_location.name, post_fixity_check=True
        )
        assert verify_checksum.delay.called

    # Get object again
    obj = ObjectVersion.get(bucket, obj.key)
    new_uri = obj.file.uri
    assert exists(old_uri)
    assert exists(new_uri)
    assert new_uri != old_uri
    assert FileInstance.query.count() == 5


def test_migrate_file_copyfail(
    app, db, dummy_location, extra_location, bucket, objects
):
    """Test a failed copy."""
    obj = objects[0]

    assert FileInstance.query.count() == 4
    with patch("fs.osfs.io") as io:
        e = OSError()
        e.errno = errno.EPERM
        io.open = MagicMock(side_effect=e)
        pytest.raises(
            FSError, migrate_file, obj.file_id, location_name=extra_location.name
        )
    assert FileInstance.query.count() == 4


def test_remove_file_data(app, db, dummy_location, versions):
    """Test remove file data."""
    # Remove an object, so file instance have no references
    obj = versions[1]
    assert obj.is_head is False
    file_ = obj.file
    obj.remove()
    db.session.commit()

    # Remove the file instance - file not writable
    assert exists(file_.uri)
    assert FileInstance.query.count() == 4
    remove_file_data(str(file_.id))
    assert FileInstance.query.count() == 4
    assert exists(file_.uri)

    # Remove the file instance - file is writable
    file_.writable = True
    db.session.commit()
    assert exists(file_.uri)
    assert FileInstance.query.count() == 4
    remove_file_data(str(file_.id))
    assert FileInstance.query.count() == 3
    assert not exists(file_.uri)

    # Try to remove file instance with references.
    obj = versions[0]
    assert exists(obj.file.uri)
    assert FileInstance.query.count() == 3
    remove_file_data(str(obj.file.id))
    assert exists(obj.file.uri)


def test_clear_orphaned_files(app, db, dummy_location, versions):
    """Test clearing orphan files."""
    # create an orphaned file
    obj = versions[1]
    file_ = obj.file
    for obj in file_.objects:
        obj.remove()

    file_.writable = False
    db.session.commit()

    # make sure that the file is orphaned
    assert not file_.objects

    # try to delete the orphan which is marked as not writable
    assert exists(file_.uri)
    assert FileInstance.query.count() == 4
    clear_orphaned_files()
    assert exists(file_.uri)
    assert FileInstance.query.count() == 4

    # try to force the deletion
    assert exists(file_.uri)
    assert FileInstance.query.count() == 4
    clear_orphaned_files(force_delete_check=lambda fi: True)
    assert not exists(file_.uri)
    assert FileInstance.query.count() == 3
