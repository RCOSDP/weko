# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016, 2017 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Celery tasks for Invenio-Files-REST."""

from __future__ import absolute_import, print_function

import math
import uuid
from datetime import date, datetime, timedelta

import sqlalchemy as sa
from celery import current_app as current_celery
from celery import current_task, group, shared_task
from celery.states import state
from celery.utils.log import get_task_logger
from flask import current_app
from invenio_db import db
from sqlalchemy.exc import IntegrityError

from .models import FileInstance, Location, MultipartObject, ObjectVersion
from .utils import obj_or_import_string

logger = get_task_logger(__name__)


def progress_updater(size, total):
    """Progress reporter for checksum verification."""
    current_task.update_state(
        state=state('PROGRESS'),
        meta=dict(size=size, total=total)
    )


@shared_task(ignore_result=True)
def verify_checksum(file_id, pessimistic=False, chunk_size=None, throws=True,
                    checksum_kwargs=None):
    """Verify checksum of a file instance.

    :param file_id: The file ID.
    """
    f = FileInstance.query.get(uuid.UUID(file_id))

    # Anything might happen during the task, so being pessimistic and marking
    # the file as unchecked is a reasonable precaution
    if pessimistic:
        f.clear_last_check()
        db.session.commit()
    f.verify_checksum(
        progress_callback=progress_updater, chunk_size=chunk_size,
        throws=throws, checksum_kwargs=checksum_kwargs)
    db.session.commit()


def default_checksum_verification_files_query():
    """Return a query of valid FileInstances for checksum verficiation."""
    return FileInstance.query


@shared_task(ignore_result=True)
def schedule_checksum_verification(frequency=None, batch_interval=None,
                                   max_count=None, max_size=None,
                                   files_query=None,
                                   checksum_kwargs=None):
    """Schedule a batch of files for checksum verification.

    The purpose of this task is to be periodically called through `celerybeat`,
    in order achieve a repeated verification cycle of all file checksums, while
    following a set of constraints in order to throttle the execution rate of
    the checks.

    :param dict frequency: Time period over which a full check of all files
        should be performed. The argument is a dictionary that will be passed
        as arguments to the `datetime.timedelta` class. Defaults to a month (30
        days).
    :param dict batch_interval: How often a batch is sent. If not supplied,
        this information will be extracted, if possible, from the
        celery.conf['CELERYBEAT_SCHEDULE'] entry of this task. The argument is
        a dictionary that will be passed as arguments to the
        `datetime.timedelta` class.
    :param int max_count: Max count of files of a single batch. When set to `0`
        it's automatically calculated to be distributed equally through the
        number of total batches.
    :param int max_size: Max size of a single batch in bytes. When set to `0`
        it's automatically calculated to be distributed equally through the
        number of total batches.
    :param str files_query: Import path for a function returning a
        FileInstance query for files that should be checked.
    :param dict checksum_kwargs: Passed to ``FileInstance.verify_checksum``.
    """
    assert max_count is not None or max_size is not None
    frequency = timedelta(**frequency) if frequency else timedelta(days=30)
    if batch_interval:
        batch_interval = timedelta(**batch_interval)
    else:
        celery_schedule = current_celery.conf.get('CELERYBEAT_SCHEDULE', {})
        batch_interval = batch_interval or next(
            (v['schedule'] for v in celery_schedule.values()
             if v.get('task') == schedule_checksum_verification.name), None)
    if not batch_interval or not isinstance(batch_interval, timedelta):
        raise Exception(u'No "batch_interval" could be decided')

    total_batches = int(
        frequency.total_seconds() / batch_interval.total_seconds())

    files = obj_or_import_string(
        files_query, default=default_checksum_verification_files_query)()
    files = files.order_by(
        sa.func.coalesce(FileInstance.last_check_at, date.min))

    if max_count is not None:
        all_files_count = files.count()
        min_count = int(math.ceil(all_files_count / total_batches))
        max_count = min_count if max_count == 0 else max_count
        if max_count < min_count:
            current_app.logger.warning(
                 u'The "max_count" you specified ({0}) is smaller than the '
                 'minimum batch file count required ({1}) in order to achieve '
                 'the file checks over the specified period ({2}).'
                 .format(max_count, min_count, frequency))
        files = files.limit(max_count)

    if max_size is not None:
        all_files_size = db.session.query(
            sa.func.sum(FileInstance.size)).scalar()
        min_size = int(math.ceil(all_files_size / total_batches))
        max_size = min_size if max_size == 0 else max_size
        if max_size < min_size:
            current_app.logger.warning(
                 u'The "max_size" you specified ({0}) is smaller than the '
                 'minimum batch total file size required ({1}) in order to '
                 'achieve the file checks over the specified period ({2}).'
                 .format(max_size, min_size, frequency))

    files = files.yield_per(1000)
    scheduled_file_ids = []
    total_size = 0
    for f in files:
        # Add at least the first file, since it might be larger than "max_size"
        scheduled_file_ids.append(str(f.id))
        total_size += f.size
        if max_size and max_size <= total_size:
            break
    group(
        verify_checksum.s(
            file_id, pessimistic=True, throws=False,
            checksum_kwargs=(checksum_kwargs or {}))
        for file_id in scheduled_file_ids
    ).apply_async()


@shared_task(ignore_result=True, max_retries=3, default_retry_delay=20 * 60)
def migrate_file(src_id, location_name, post_fixity_check=False):
    """Task to migrate a file instance to a new location.

    .. note:: If something goes wrong during the content copy, the destination
        file instance is removed.

    :param src_id: The :class:`invenio_files_rest.models.FileInstance` ID.
    :param location_name: Where to migrate the file.
    :param post_fixity_check: Verify checksum after migration.
        (Default: ``False``)
    """
    location = Location.get_by_name(location_name)
    f_src = FileInstance.get(src_id)

    # Create destination
    f_dst = FileInstance.create()
    db.session.commit()

    try:
        # Copy contents
        f_dst.copy_contents(
            f_src,
            progress_callback=progress_updater,
            default_location=location.uri,
        )
        db.session.commit()
    except Exception:
        # Remove destination file instance if an error occurred.
        db.session.delete(f_dst)
        db.session.commit()
        raise

    # Update all objects pointing to file.
    ObjectVersion.relink_all(f_src, f_dst)
    db.session.commit()

    # Start a fixity check
    if post_fixity_check:
        verify_checksum.delay(str(f_dst.id))


@shared_task(ignore_result=True)
def remove_file_data(file_id, silent=True):
    """Remove file instance and associated data.

    :param file_id: The :class:`invenio_files_rest.models.FileInstance` ID.
    :param silent: It stops propagation of a possible arised IntegrityError
        exception. (Default: ``True``)
    :raises sqlalchemy.exc.IntegrityError: Raised if the database removal goes
        wrong and silent is set to ``False``.
    """
    try:
        # First remove FileInstance from database and commit transaction to
        # ensure integrity constraints are checked and enforced.
        f = FileInstance.get(file_id)
        if not f.writable:
            return
        f.delete()
        db.session.commit()
        # Next, remove the file on disk. This leaves the possibility of having
        # a file on disk dangling in case the database removal works, and the
        # disk file removal doesn't work.
        f.storage().delete()
    except IntegrityError:
        if not silent:
            raise


@shared_task()
def merge_multipartobject(upload_id, version_id=None):
    """Merge multipart object.

    :param upload_id: The :class:`invenio_files_rest.models.MultipartObject`
        upload ID.
    :param version_id: Optionally you can define which file version.
        (Default: ``None``)
    :returns: The :class:`invenio_files_rest.models.ObjectVersion` version
        ID.
    """
    mp = MultipartObject.query.filter_by(upload_id=upload_id).one_or_none()
    if not mp:
        raise RuntimeError('Upload ID does not exists.')
    if not mp.completed:
        raise RuntimeError('MultipartObject is not completed.')

    try:
        obj = mp.merge_parts(
            version_id=version_id,
            progress_callback=progress_updater
        )
        db.session.commit()
        return str(obj.version_id)
    except Exception:
        db.session.rollback()
        raise


@shared_task(ignore_result=True)
def remove_expired_multipartobjects():
    """Remove expired multipart objects."""
    delta = current_app.config['FILES_REST_MULTIPART_EXPIRES']
    expired_dt = datetime.utcnow() - delta

    file_ids = []
    for mp in MultipartObject.query_expired(expired_dt):
        file_ids.append(str(mp.file_id))
        mp.delete()

    for fid in file_ids:
        remove_file_data.delay(fid)
