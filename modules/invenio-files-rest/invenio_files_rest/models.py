# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Models for Invenio-Files-REST.

The entities of this module consists of:

 * **Buckets** - Identified by UUIDs, and contains objects.
 * **Buckets tags** - Identified uniquely with a bucket by a key. Used to store
   extra metadata for a bucket.
 * **Objects** - Identified uniquely within a bucket by string keys. Each
   object can have multiple object versions (note: Objects do not have their
   own database table).
 * **Object versions** - Identified by UUIDs and belongs to one specific object
   in one bucket. Each object version has zero or one file instance. If the
   object version has no file instance, it is considered a *delete marker*.
 * **File instance** - Identified by UUIDs. Represents a physical file on disk.
   The location of the file is specified via a URI. A file instance can have
   many object versions.
 * **Locations** - A bucket belongs to a specific location. Locations can be
   used to represent e.g. different storage systems and/or geographical
   locations.
 * **Multipart Objects** - Identified by UUIDs and belongs to a specific bucket
   and key.
 * **Part object** - Identified by their multipart object and a part number.

The actual file access is handled by a storage interface. Also, objects do not
have their own model, but are represented via the :py:data:`ObjectVersion`
model.
"""

from __future__ import absolute_import, print_function

import shutil
import mimetypes
import os
import re
import sys
import uuid
from datetime import datetime
from functools import wraps
from os.path import basename

import six
import sqlalchemy as sa
from flask import current_app, flash, redirect, request, url_for
from flask_login import current_user
from invenio_db import db
from invenio_previewer.api import convert_to
from sqlalchemy.dialects import mysql, postgresql
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import validates
from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy.sql.expression import func
from sqlalchemy_utils.types import JSONType, UUIDType
from weko_admin.models import AdminSettings

from .errors import BucketLockedError, FileInstanceAlreadySetError, \
    FileInstanceUnreadableError, FileSizeError, InvalidKeyError, \
    InvalidOperationError, MultipartAlreadyCompleted, \
    MultipartInvalidChunkSize, MultipartInvalidPartNumber, \
    MultipartInvalidSize, MultipartMissingParts, MultipartNotCompleted
from .proxies import current_files_rest

slug_pattern = re.compile('^[a-z][a-z0-9-]+$')


#
# Helpers
#
def validate_key(key):
    """Validate key.

    :param key: The key to validate.
    :raises invenio_files_rest.errors.InvalidKeyError: If the key is longer
        than the maximum length defined in
        :data:`invenio_files_rest.config.FILES_REST_FILE_URI_MAX_LEN`.
    :returns: The key.
    """
    if len(key) > current_app.config['FILES_REST_OBJECT_KEY_MAX_LEN']:
        raise InvalidKeyError()
    return key


def as_bucket(value):
    """Get a bucket object from a bucket ID or a bucket object.

    :param value: A :class:`invenio_files_rest.models.Bucket` or a Bucket ID.
    :returns: A :class:`invenio_files_rest.models.Bucket` instance.
    """
    return value if isinstance(value, Bucket) else Bucket.get(value)


def as_bucket_id(value):
    """Get a bucket ID from a bucket ID or a bucket object.

    :param value: A :class:`invenio_files_rest.models.Bucket` instance of a
        bucket ID.
    :returns: The :class:`invenio_files_rest.models.Bucket` ID.
    """
    return value.id if isinstance(value, Bucket) else value


def as_object_version(value):
    """Get an object version object from an object version ID or an object version.

    :param value: A :class:`invenio_files_rest.models.ObjectVersion` or an
        object version ID.
    :returns: A :class:`invenio_files_rest.models.ObjectVersion` instance.
    """
    return value if isinstance(value, ObjectVersion) \
        else ObjectVersion.query.filter_by(version_id=value).one_or_none()


def as_object_version_id(value):
    """Get an object version ID from an object version ID or an object version.

    :param value: A :class:`invenio_files_rest.models.ObjectVersion` instance
        of a object version ID.
    :returns: The :class:`invenio_files_rest.models.ObjectVersion` version_id.
    """
    return value.version_id if isinstance(value, ObjectVersion) else value


#
# Decorators to validate state.
#
def update_bucket_size(f):
    """Decorate to update bucket size after operation."""
    @wraps(f)
    def inner(self, *args, **kwargs):
        res = f(self, *args, **kwargs)
        self.bucket.size += self.file.size
        # self.bucket.location.size += self.file.size
        return res
    return inner


def ensure_state(default_getter, exc_class, default_msg=None):
    """Create a decorator factory function."""
    def decorator(getter=default_getter, msg=default_msg):
        def ensure_decorator(f):
            @wraps(f)
            def inner(self, *args, **kwargs):
                if not getter(self):
                    raise exc_class(msg) if msg else exc_class()
                return f(self, *args, **kwargs)
            return inner
        return ensure_decorator

    return decorator


class BucketError(object):
    """Represents a bucket level error.

    .. note:: This is not an actual exception.
    """

    def __init__(self, message):
        self.res = dict(message=message)

    def to_dict(self):
        return self.res


class ObjectVersionError(object):
    """Represents an object version level error.

    .. note:: This is not an actual exception.
    """

    def __init__(self, message):
        self.res = dict(message=message)

    def to_dict(self):
        return self.res


ensure_readable = ensure_state(
    lambda o: o.readable,
    FileInstanceUnreadableError)
"""Ensure file is readable."""

ensure_writable = ensure_state(
    lambda o: o.writable,
    ValueError, 'File is not writable.')
"""Ensure file is writeable."""

ensure_completed = ensure_state(
    lambda o: o.completed,
    MultipartNotCompleted)
"""Ensure file is completed."""

ensure_uncompleted = ensure_state(
    lambda o: not o.completed,
    MultipartAlreadyCompleted)
"""Ensure file is not completed."""

ensure_not_deleted = ensure_state(
    lambda o: not o.deleted,
    InvalidOperationError,
    [BucketError('Cannot make snapshot of a deleted bucket.')])
"""Ensure file is not deleted."""

ensure_unlocked = ensure_state(
    lambda o: not o.locked,
    BucketLockedError)
"""Ensure bucket is locked."""

ensure_no_file = ensure_state(
    lambda o: o.file_id is None,
    FileInstanceAlreadySetError)
"""Ensure file is not already set."""

ensure_is_previous_version = ensure_state(
    lambda o: not o.is_head,
    InvalidOperationError,
    [ObjectVersionError('Cannot restore latest version.')])
"""Ensure file is the previous version."""


#
# Model definitions
#
class Timestamp(object):
    """Timestamp model mix-in with fractional seconds support.

    SQLAlchemy-Utils timestamp model, does not have support for fractional
    seconds.
    """

    created = db.Column(
        db.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mysql'),
        default=datetime.utcnow,
        nullable=False
    )
    """Creation timestamp."""

    updated = db.Column(
        db.DateTime().with_variant(mysql.DATETIME(fsp=6), 'mysql'),
        default=datetime.utcnow,
        nullable=False
    )
    """Modification timestamp."""


@db.event.listens_for(Timestamp, 'before_update', propagate=True)
def timestamp_before_update(mapper, connection, target):
    """Listen for updating updated field."""
    target.updated = datetime.utcnow()


class Location(db.Model, Timestamp):
    """Model defining base locations."""

    __tablename__ = 'files_location'

    id = db.Column(db.Integer, primary_key=True)
    """Internal identifier for locations.

    The internal identifier is used only used as foreign key for buckets in
    order to decrease storage requirements per row for buckets.
    """

    name = db.Column(db.String(20), unique=True, nullable=False)
    """External identifier of the location."""

    uri = db.Column(db.String(255), nullable=False)
    """URI of the location."""

    default = db.Column(db.Boolean(name='default'),
                        nullable=False,
                        default=False)
    """True if the location is the default location.

    At least one location should be the default location.
    """

    type = db.Column(db.String(20), nullable=True)

    access_key = db.Column(db.String(128), nullable=True)

    secret_key = db.Column(db.String(128), nullable=True)

    s3_endpoint_url = db.Column(db.String(128), nullable=True)

    s3_send_file_directly = db.Column(db.Boolean(name='s3_send_file_directly'), nullable=False, default=True)

    size = db.Column(db.BigInteger, default=0, nullable=True)

    quota_size = db.Column(db.BigInteger, nullable=True)

    max_file_size = db.Column(db.BigInteger, nullable=True)

    s3_default_block_size = db.Column(db.BigInteger, nullable=True)

    s3_maximum_number_of_parts = db.Column(db.BigInteger, nullable=True)

    s3_region_name = db.Column(db.String(128), nullable=True)

    s3_signature_version = db.Column(db.String(20), nullable=True)

    s3_url_expiration = db.Column(db.BigInteger, nullable=True)

    @validates('name')
    def validate_name(self, key, name):
        """Validate name."""
        if not slug_pattern.match(name) or len(name) > 20:
            raise ValueError(
                'Invalid location name (lower-case alphanumeric + danshes).')
        return name

    @classmethod
    def get_by_name(cls, name):
        """Fetch a specific location object."""
        return cls.query.filter_by(
            name=name,
        ).one()

    def get_by_uri(cls, uri):
        """Fetch a specific location object by uri."""
        return cls.query.filter_by(
            uri=uri,
        ).one()

    @classmethod
    def get_default(cls):
        """Fetch the default location object."""
        try:
            return cls.query.filter_by(default=True).one_or_none()
        except MultipleResultsFound:
            return None

    @classmethod
    def all(cls):
        """Return query that fetches all locations."""
        return Location.query.all()

    def __repr__(self):
        """Return representation of location."""
        return self.name


class Bucket(db.Model, Timestamp):
    """Model for storing buckets.

    A bucket is a container of objects. Buckets have a default location and
    storage class. Individual objects in the bucket can however have different
    locations and storage classes.

    A bucket can be marked as deleted. A bucket can also be marked as locked
    to prevent operations on the bucket.

    Each bucket can also define a quota. The size of a bucket is the size
    of all objects in the bucket (including all versions).
    """

    __tablename__ = 'files_bucket'

    id = db.Column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4,
    )
    """Bucket identifier."""

    default_location = db.Column(
        db.Integer,
        db.ForeignKey(Location.id, ondelete='RESTRICT'),
        nullable=False)
    """Default location."""

    default_storage_class = db.Column(
        db.String(1), nullable=False,
        default=lambda: current_app.config['FILES_REST_DEFAULT_STORAGE_CLASS'])
    """Default storage class."""

    size = db.Column(db.BigInteger, default=0, nullable=False)
    """Size of bucket.

    This is a computed property which can rebuilt any time from the objects
    inside the bucket.
    """

    quota_size = db.Column(
        db.BigInteger,
        nullable=True,
        default=lambda: current_app.config['FILES_REST_DEFAULT_QUOTA_SIZE']
    )
    """Quota size of bucket.

    Usage of this property depends on which file size limiters are installed.
    """

    max_file_size = db.Column(
        db.BigInteger,
        nullable=True,
        default=lambda: current_app.config['FILES_REST_DEFAULT_MAX_FILE_SIZE']
    )
    """Maximum size of a single file in the bucket.

    Usage of this property depends on which file size limiters are installed.
    """

    locked = db.Column(db.Boolean(name='locked'),
                       default=False,
                       nullable=False)
    """Lock state of bucket.

    Modifications are not allowed on a locked bucket.
    """

    deleted = db.Column(db.Boolean(name='deleted'),
                        default=False,
                        nullable=False)
    """Delete state of bucket."""

    location = db.relationship(Location, backref='buckets')
    """Location associated with this bucket."""

    def __repr__(self):
        """Return representation of location."""
        return str(self.id)

    @property
    def quota_left(self):
        """Get how much space is left in the bucket."""
        if self.quota_size:
            return max(self.quota_size - self.size, 0)

    @property
    def size_limit(self):
        """Get size limit for this bucket.

        The limit is based on the minimum output of the file size limiters.
        """
        limits = [
            lim for lim in current_files_rest.file_size_limiters(
                self)
            if lim.limit is not None
        ]
        return min(limits) if limits else None

    @validates('default_storage_class')
    def validate_storage_class(self, key, default_storage_class):
        """Validate storage class."""
        if default_storage_class not in \
           current_app.config['FILES_REST_STORAGE_CLASS_LIST']:
            raise ValueError('Invalid storage class.')
        return default_storage_class

    @ensure_not_deleted()
    def snapshot(self, lock=False):
        """Create a snapshot of latest objects in bucket.

        :param lock: Create the new bucket in a locked state.
        :returns: Newly created bucket containing copied ObjectVersion.
        """
        with db.session.begin_nested():
            bucket = Bucket(
                default_location=self.default_location,
                default_storage_class=self.default_storage_class,
                quota_size=self.quota_size,
            )
            db.session.add(bucket)

        for o in ObjectVersion.get_by_bucket(self):
            o.copy(bucket=bucket, is_thumbnail=o.is_thumbnail)

        bucket.locked = True if lock else self.locked

        return bucket

    @ensure_not_deleted(msg=[BucketError('Cannot sync a deleted bucket.')])
    def sync(self, bucket, delete_extras=False):
        """Sync self bucket ObjectVersions to the destination bucket.

        The bucket is fully mirrored with the destination bucket following the
        logic:

         * same ObjectVersions are not touched
         * new ObjectVersions are added to destination
         * deleted ObjectVersions are deleted in destination
         * extra ObjectVersions in dest are deleted if `delete_extras` param is
           True

        :param bucket: The destination bucket.
        :param delete_extras: Delete extra ObjectVersions in destination if
            True.
        :returns: The bucket with an exact copy of ObjectVersions in self.
        """
        assert not bucket.locked

        src_ovs = ObjectVersion.get_by_bucket(bucket=self, with_deleted=True)
        dest_ovs = ObjectVersion.get_by_bucket(bucket=bucket,
                                               with_deleted=True)
        # transform into a dict { key: object version }
        src_keys = {ov.key: ov for ov in src_ovs}
        dest_keys = {ov.key: ov for ov in dest_ovs}

        for key, ov in src_keys.items():
            if not ov.deleted:
                if key not in dest_keys or \
                        ov.file_id != dest_keys[key].file_id:
                    ov.copy(bucket=bucket)
            elif key in dest_keys and not dest_keys[key].deleted:
                ObjectVersion.delete(bucket, key)

        if delete_extras:
            for key, ov in dest_keys.items():
                if key not in src_keys:
                    ObjectVersion.delete(bucket, key)

        return bucket

    def get_tags(self):
        """Get tags for bucket as dictionary."""
        return {t.key: t.value for t in self.tags}

    @classmethod
    def create(cls, location=None, storage_class=None, **kwargs):
        r"""Create a bucket.

        :param location: Location of a bucket (instance or name).
            Default: Default location.
        :param storage_class: Storage class of a bucket.
            Default: Default storage class.
        :param \**kwargs: Keyword arguments are forwarded to the class
        :param \**kwargs: Keyword arguments are forwarded to the class
            constructor.
        :returns: Created bucket.
        """
        with db.session.begin_nested():
            if location is None:
                location = Location.get_default()
            elif isinstance(location, six.string_types):
                location = Location.get_by_name(location)

            obj = cls(
                default_location=location.id,
                default_storage_class=storage_class or current_app.config[
                    'FILES_REST_DEFAULT_STORAGE_CLASS'],
                **kwargs
            )
            db.session.add(obj)
        return obj

    @classmethod
    def get(cls, bucket_id):
        """Get a bucket object (excluding deleted).

        :param bucket_id: Bucket identifier.
        :returns: Bucket instance.
        """
        return cls.query.filter_by(
            id=bucket_id,
            deleted=False
        ).one_or_none()

    @classmethod
    def all(cls):
        """Return query of all buckets (excluding deleted)."""
        return cls.query.filter_by(
            deleted=False
        )

    @classmethod
    def delete(cls, bucket_id):
        """Delete a bucket.

        Does not actually delete the Bucket, just marks it as deleted.
        """
        bucket = cls.get(bucket_id)
        if not bucket or bucket.deleted:
            return False

        bucket.deleted = True
        return True

    @ensure_unlocked()
    def remove(self):
        """Permanently remove a bucket and all objects (including versions).

        .. warning::

           This by-passes the normal versioning and should only be used when
           you want to permanently delete a bucket and its objects. Otherwise
           use :py:data:`Bucket.delete()`.

           Note the method does not remove the associated file instances which
           must be garbage collected.

        :returns: ``self``.
        """
        with db.session.begin_nested():
            ObjectVersion.query.filter_by(
                bucket_id=self.id
            ).delete()
            self.query.filter_by(id=self.id).delete()
        return self


class BucketTag(db.Model):
    """Model for storing tags associated to buckets.

    This is useful to store extra information for a bucket.
    """

    __tablename__ = 'files_buckettags'

    bucket_id = db.Column(
        UUIDType,
        db.ForeignKey(Bucket.id, ondelete='CASCADE'),
        default=uuid.uuid4,
        primary_key=True, )

    key = db.Column(db.String(255), primary_key=True)
    """Tag key."""

    value = db.Column(db.Text, nullable=False)
    """Tag value."""

    bucket = db.relationship(Bucket, backref='tags')
    """Relationship to buckets."""

    @classmethod
    def get(cls, bucket, key):
        """Get tag object."""
        return cls.query.filter_by(
            bucket_id=as_bucket_id(bucket),
            key=key,
        ).one_or_none()

    @classmethod
    def create(cls, bucket, key, value):
        """Create a new tag for bucket."""
        with db.session.begin_nested():
            obj = cls(
                bucket_id=as_bucket_id(bucket),
                key=key,
                value=value
            )
            db.session.add(obj)
        return obj

    @classmethod
    def create_or_update(cls, bucket, key, value):
        """Create or update a new tag for bucket."""
        obj = cls.get(bucket, key)
        if obj:
            obj.value = value
            db.session.merge(obj)
        else:
            obj = cls.create(bucket, key, value)
        return obj

    @classmethod
    def get_value(cls, bucket, key):
        """Get tag value."""
        obj = cls.get(bucket, key)
        return obj.value if obj else None

    @classmethod
    def delete(cls, bucket, key):
        """Delete a tag."""
        with db.session.begin_nested():
            cls.query.filter_by(
                bucket_id=as_bucket_id(bucket),
                key=key,
            ).delete()


class FileInstance(db.Model, Timestamp):
    """Model for storing files.

    A file instance represents a file on disk. A file instance may be linked
    from many objects, while an object can have one and only one file instance.

    A file instance also records the storage class, size and checksum of the
    file on disk.

    Additionally, a file instance can be read only in case the storage layer
    is not capable of writing to the file (e.g. can typically be used to
    link to files on externally controlled storage).
    """

    __tablename__ = 'files_files'

    id = db.Column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4,
    )
    """Identifier of file."""

    uri = db.Column(db.Text().with_variant(mysql.VARCHAR(255), 'mysql'),
                    unique=True, nullable=True)
    """Location of file."""

    storage_class = db.Column(db.String(1), nullable=True)
    """Storage class of file."""

    size = db.Column(db.BigInteger, default=0, nullable=True)
    """Size of file."""

    checksum = db.Column(db.String(255), nullable=True)
    """String representing the checksum of the object."""

    readable = db.Column(db.Boolean(name='readable'),
                         default=True,
                         nullable=False)
    """Defines if the file is read only."""

    writable = db.Column(db.Boolean(name='writable'),
                         default=True,
                         nullable=False)
    """Defines if file is writable.

    This property is used to create a file instance prior to having the actual
    file at the given URI. This is useful when e.g. copying a file instance.
    """

    last_check_at = db.Column(db.DateTime, nullable=True)
    """Timestamp of last fixity check."""

    last_check = db.Column(db.Boolean(name='last_check'), default=True)
    """Result of last fixity check."""

    json = db.Column(
        db.JSON().with_variant(
            postgresql.JSONB(none_as_null=True),
            'postgresql',
        ).with_variant(
            JSONType(),
            'sqlite',
        ).with_variant(
            JSONType(),
            'mysql',
        ),
        default=lambda: dict(),
        nullable=True
    )

    @validates('uri')
    def validate_uri(self, key, uri):
        """Validate uri."""
        if len(uri) > current_app.config['FILES_REST_FILE_URI_MAX_LEN']:
            raise ValueError(
                'FileInstance URI too long ({0}).'.format(len(uri)))
        return uri

    @classmethod
    def get(cls, file_id):
        """Get a file instance."""
        return cls.query.filter_by(id=file_id).one_or_none()

    @classmethod
    def get_by_uri(cls, uri):
        """Get a file instance by URI."""
        assert uri is not None
        return cls.query.filter_by(uri=uri).one_or_none()

    @classmethod
    def get_location_by_file_instance(cls):
        """Get a file instance by URI."""
        return db.session.query(Location).filter(
            FileInstance.uri.like(Location.uri + "%")) \
            .filter(FileInstance.id == cls.id) \
            .first()

    @classmethod
    def get_location_all(cls):
        """Get all location ."""
        return db.session.query(Location)

    @classmethod
    def create(cls):
        """Create a file instance.

        Note, object is only added to the database session.
        """
        obj = cls(
            id=uuid.uuid4(),
            writable=True,
            readable=False,
            size=0,
        )
        db.session.add(obj)
        return obj

    def delete(self):
        """Delete a file instance.

        The file instance can be deleted if it has no references from other
        objects. The caller is responsible to test if the file instance is
        writable and that the disk file can actually be removed.

        .. note::

           Normally you should use the Celery task to delete a file instance,
           as this method will not remove the file on disk.
        """
        location = self.get_location_by_file_instance()
        location.size = location.size - self.size
        self.query.filter_by(id=self.id).delete()
        return self

    def storage(self, **kwargs):
        """Get storage interface for object.

        Uses the applications storage factory to create a storage interface
        that can be used for this particular file instance.

        :returns: Storage interface.
        """
        return current_files_rest.storage_factory(fileinstance=self, **kwargs)

    @ensure_readable()
    def update_checksum(self, progress_callback=None, chunk_size=None,
                        checksum_kwargs=None, **kwargs):
        """Update checksum based on file."""
        self.checksum = self.storage(**kwargs).checksum(
            progress_callback=progress_callback, chunk_size=chunk_size,
            **(checksum_kwargs or {}))

    def clear_last_check(self):
        """Clear the checksum of the file."""
        with db.session.begin_nested():
            self.last_check = None
            self.last_check_at = datetime.utcnow()
        return self

    def verify_checksum(self, progress_callback=None, chunk_size=None,
                        throws=True, checksum_kwargs=None, **kwargs):
        """Verify checksum of file instance.

        :param bool throws: If `True`, exceptions raised during checksum
            calculation will be re-raised after logging. If set to `False`, and
            an exception occurs, the `last_check` field is set to `None`
            (`last_check_at` of course is updated), since no check actually was
            performed.
        :param dict checksum_kwargs: Passed as `**kwargs`` to
            ``storage().checksum``.
        """
        try:
            real_checksum = self.storage(**kwargs).checksum(
                progress_callback=progress_callback, chunk_size=chunk_size,
                **(checksum_kwargs or {}))
        except Exception as exc:
            current_app.logger.exception(str(exc))
            if throws:
                raise
            real_checksum = None
        with db.session.begin_nested():
            self.last_check = (None if real_checksum is None
                               else (self.checksum == real_checksum))
            self.last_check_at = datetime.utcnow()
        return self.last_check

    @ensure_writable()
    def init_contents(self, size=0, **kwargs):
        """Initialize file."""
        self.set_uri(
            *self.storage(**kwargs).initialize(size=size),
            readable=False, writable=True)

    @ensure_writable()
    def update_contents(self, stream, seek=0, size=None, chunk_size=None,
                        progress_callback=None, **kwargs):
        """Save contents of stream to this file.

        :param obj: ObjectVersion instance from where this file is accessed
            from.
        :param stream: File-like stream.
        """
        self.checksum = None
        return self.storage(**kwargs).update(
            stream, seek=seek, size=size, chunk_size=chunk_size,
            progress_callback=progress_callback
        )

    @ensure_writable()
    def set_contents(self, stream, chunk_size=None, size=None, size_limit=None,
                     progress_callback=None, is_set_size_location=True,
                     **kwargs):
        """Save contents of stream to this file.

        :param obj: ObjectVersion instance from where this file is accessed
            from.
        :param stream: File-like stream.
        """
        old_size = self.size if self.size else 0
        self.set_uri(
            *self.storage(**kwargs).save(
                stream, chunk_size=chunk_size, size=size,
                size_limit=size_limit, progress_callback=progress_callback))
        if is_set_size_location:
            location = self.get_location_by_file_instance()
            location.size = location.size + self.size - old_size

    @ensure_writable()
    def copy_contents(self, fileinstance, progress_callback=None,
                      chunk_size=None, **kwargs):
        """Copy this file instance into another file instance."""
        def copy(storage, src, chunk_size=None, progress_callback=None):
            fp = src.open(mode='rb')
            try:
                return storage.save(fp, chunk_size=chunk_size,
                                    progress_callback=progress_callback)
            finally:
                fp.close()

        if not fileinstance.readable:
            raise ValueError('Source file instance is not readable.')
        if not self.size == 0:
            raise ValueError('File instance has data.')

        storage = self.storage(**kwargs)
        fileinstance_storage = fileinstance.storage(**kwargs)
        copy_result = copy(storage, fileinstance_storage, chunk_size=chunk_size,
                           progress_callback=progress_callback)
        self.set_uri(*copy_result)

    @ensure_readable()
    def send_file(self, filename, restricted=True, mimetype=None,
                  trusted=False, chunk_size=None, as_attachment=False,
                  convert_to_pdf=False, **kwargs):
        """Send file to client."""
        # Convert ms office file to PDF for preview
        if convert_to_pdf:

            try:
                settings = AdminSettings.get('convert_pdf_settings')

                # Load settings from settings if there is not settings in db
                if settings:
                    path = settings.path
                else:
                    path = current_app.config['FILES_REST_DEFAULT_PDF_SAVE_PATH']

                pdf_dir = path + '/pdf_dir/' + str(self.id)
                pdf_filename = '/data.pdf'
                file_type = os.path.splitext(self.json['filename'])[1].lower()
                # Change preview file to pdf
                self.json['mimetype'] = 'application/pdf'
                self.json['filename'] = self.json['filename'].replace(
                    file_type, '.pdf')

                if not os.path.isfile(pdf_dir + pdf_filename):
                    convert_dir = path+"/convert_"+str(self.id)
                    target_uri = self.uri
                    tmp_uri = self.uri
                    if tmp_uri.startswith('https://'):
                        if tmp_uri.startswith('https://s3'):
                            # ex: https://s3.us-east-1.amazonaws.com/bucket_name/file_name
                            parts = tmp_uri.split('/')
                            tmp_uri = 's3://' + '/'.join(parts[3:])
                            self.uri = tmp_uri
                        else:
                            # ex: https://bucket_name.s3.us-east-1.amazonaws.com/file_name
                            parts = tmp_uri.split('/')
                            sub_parts = parts[2].split('.')
                            tmp_uri = 's3://' + sub_parts[0] + '/' + '/'.join(parts[3:])
                            self.uri = tmp_uri
                    if self.uri.startswith("s3://"):
                        target_uri = convert_dir+"/"+self.uri.split("/")[-1]
                        if os.path.exists(convert_dir):
                            shutil.rmtree(convert_dir)
                        os.makedirs(convert_dir)
                        fp = self.storage(**kwargs).open(mode='rb')
                        data = fp.read()
                        fp.close()
                        with open(target_uri,"wb") as f:
                            f.write(data)

                    convert_to(pdf_dir, target_uri)

                    if os.path.exists(convert_dir):
                        shutil.rmtree(convert_dir)

                self.uri = pdf_dir + pdf_filename
                self.size = os.path.getsize(pdf_dir + pdf_filename)
            except Exception as ex:
                current_app.logger.error('convert to pdf error')
                current_app.logger.error(ex)

        return self.storage(**kwargs).send_file(
            filename,
            mimetype=mimetype,
            restricted=restricted,
            checksum=self.checksum,
            trusted=trusted,
            chunk_size=chunk_size,
            as_attachment=as_attachment,
        )

    def set_uri(self, uri, size, checksum, readable=True, writable=False,
                storage_class=None):
        """Set a location of a file."""
        self.uri = uri
        self.size = size
        self.checksum = checksum
        self.writable = writable
        self.readable = readable
        self.storage_class = \
            current_app.config['FILES_REST_DEFAULT_STORAGE_CLASS'] \
            if storage_class is None else \
            storage_class
        return self

    def update_json(self, jsn):
        """Update file metadata.

        :param jsn: Dictionary of file metadata.
        :return:
        """
        self.json = jsn.copy()

    def upload_file(self, fjson, **kwargs):
        """Put file to Elasticsearch.

        :param fjson:
        :param kwargs:
        """
        self.storage(**kwargs).upload_file(fjson)

    def read_file(self, fjson, **kwargs):
        """Put file to Elasticsearch.

        :param fjson:
        :param kwargs:
        """
        return self.storage(**kwargs).read_file(fjson)


class ObjectVersion(db.Model, Timestamp):
    """Model for storing versions of objects.

    A bucket stores one or more objects identified by a key. Each object is
    versioned where each version is represented by an ``ObjectVersion``.

    An object version can either be 1) a *normal version* which is linked to
    a file instance, or 2) a *delete marker*, which is *not* linked to a file
    instance.

    An normal object version is linked to a physical file on disk via a file
    instance. This allows for multiple object versions to point to the same
    file on disk, to optimize storage efficiency (e.g. useful for snapshotting
    an entire bucket without duplicating the files).

    A delete marker object version represents that the object at hand was
    deleted.

    The latest version of an object is marked using the ``is_head`` property.
    If the latest object version is a delete marker the object will not be
    shown in the bucket.
    """

    __tablename__ = 'files_object'

    version_id = db.Column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4)
    """Identifier for the specific version of an object."""

    key = db.Column(
        db.Text().with_variant(mysql.VARCHAR(255), 'mysql'), nullable=False)
    """Key identifying the object."""

    bucket_id = db.Column(
        UUIDType,
        db.ForeignKey(Bucket.id, ondelete='RESTRICT'),
        default=uuid.uuid4, nullable=False)
    """Bucket identifier."""

    file_id = db.Column(
        UUIDType,
        db.ForeignKey(FileInstance.id, ondelete='RESTRICT'), nullable=True)
    """File instance for this object version.

    A null value in this column defines that the object has been deleted.
    """

    root_file_id = db.Column(UUIDType, nullable=True)
    """File id in the first time for this object version."""

    _mimetype = db.Column(
        db.String(255),
        index=True,
        nullable=True, )
    """MIME type of the object."""

    is_head = db.Column(db.Boolean(name='is_head'),
                        nullable=False,
                        default=True)
    """Defines if object is the latest version."""

    created_user_id = db.Column(db.Integer, nullable=True, default=0)
    """created user id of uploading."""

    updated_user_id = db.Column(db.Integer, nullable=True, default=0)
    """updated user id of uploading."""

    # Relationships definitions
    bucket = db.relationship(Bucket, backref='objects')
    """Relationship to buckets."""

    file = db.relationship(FileInstance, backref='objects')
    """Relationship to file instance."""

    is_show = db.Column(db.Boolean(name='is_show'),
                        nullable=False,
                        default=False)

    is_thumbnail = db.Column(db.Boolean(name='is_thumbnail'),
                             nullable=False,
                             default=False)
    """Defines if object is the thumbnail."""

    __table_args__ = (
        db.UniqueConstraint('bucket_id', 'version_id', 'key'),
    )

    @validates('key')
    def validate_key(self, key, key_):
        """Validate key."""
        return validate_key(key_)

    def __unicode__(self):
        """Return unicoded object."""
        return u"{0}:{1}:{2}".format(
            self.bucket_id, self.version_id, self.key)

    # https://docs.python.org/3.3/howto/pyporting.html#str-unicode
    if sys.version_info[0] >= 3:  # Python 3
        def __repr__(self):
            """Return representation of location."""
            return self.__unicode__()
    else:  # Python 2
        def __repr__(self):
            """Return representation of location."""
            return self.__unicode__().encode('utf8')

    @hybrid_property
    def mimetype(self):
        """Get MIME type of object."""
        from .utils import guess_mimetype
        return self._mimetype if self._mimetype else guess_mimetype(self.key)

    @mimetype.setter
    def mimetype(self, value):
        """Setter for MIME type."""
        self._mimetype = value

    @property
    def basename(self):
        """Return filename of the object."""
        return basename(self.key)

    @property
    def deleted(self):
        """Determine if object version is a delete marker."""
        return self.file_id is None

    @ensure_no_file()
    @update_bucket_size
    def set_contents(self, stream, chunk_size=None, size=None, size_limit=None,
                     replace_version_id=None, root_file_id=None,
                     progress_callback=None, is_set_size_location=True):
        """Save contents of stream to file instance.

        If a file instance has already been set, this methods raises an
        ``FileInstanceAlreadySetError`` exception.

        :param stream: File-like stream.
        :param size: Size of stream if known.
        :param chunk_size: Desired chunk size to read stream in. It is up to
            the storage interface if it respects this value.
        :param replace_version_id: The ObjectVersion ID
            of the previous version of the file.
        :param root_file_id: The FileInstance ID
            of the first version of the file.
        """
        if size_limit is None:
            size_limit = self.bucket.size_limit

        self.file = FileInstance.create()
        self.file.set_contents(
            stream, size_limit=size_limit, size=size, chunk_size=chunk_size,
            progress_callback=progress_callback,
            default_location=self.bucket.location.uri,
            default_storage_class=self.bucket.default_storage_class,
            is_set_size_location=is_set_size_location
        )

        if root_file_id:
            self.root_file_id = root_file_id
        else:
            replace_version = ObjectVersion.get(version_id=replace_version_id) \
                if replace_version_id else None
            self.root_file_id = replace_version.root_file_id \
                if replace_version else self.file.id

        return self

    @ensure_no_file()
    @update_bucket_size
    def set_location(self, uri, size, checksum, storage_class=None):
        """Set only URI location of for object.

        Useful to link files on externally controlled storage. If a file
        instance has already been set, this methods raises an
        ``FileInstanceAlreadySetError`` exception.

        :param uri: Full URI to object (which can be interpreted by the storage
            interface).
        :param size: Size of file.
        :param checksum: Checksum of file.
        :param storage_class: Storage class where file is stored ()
        """
        self.file = FileInstance()
        self.file.set_uri(
            uri, size, checksum, storage_class=storage_class
        )
        db.session.add(self.file)
        return self

    @ensure_no_file()
    @update_bucket_size
    def set_file(self, fileinstance):
        """Set a file instance."""
        self.file = fileinstance
        return self

    def send_file(self, restricted=True, trusted=False,
                  convert_to_pdf=False, **kwargs):
        """Wrap around FileInstance's send file."""
        return self.file.send_file(
            self.basename,
            restricted=restricted,
            mimetype=self.mimetype,
            trusted=trusted,
            convert_to_pdf=convert_to_pdf,
            **kwargs
        )

    @ensure_is_previous_version()
    def restore(self):
        """Restore this object version to become the latest version.

        Raises an exception if the object is the latest version.
        """
        # Note, copy calls create which will fail if bucket is locked.
        return self.copy()

    @ensure_not_deleted(
        msg=[ObjectVersionError('Cannot copy a delete marker.')])
    def copy(self, bucket=None, key=None, is_thumbnail=False):
        """Copy an object version to a given bucket + object key.

        The copy operation is handled completely at the metadata level. The
        actual data on disk is not copied. Instead, the two object versions
        will point to the same physical file (via the same FileInstance).

        All the tags associated with the current object version are copied over
        to the new instance.

        .. warning::

           If the destination object exists, it will be replaced by the new
           object version which will become the latest version.

        :param bucket: The bucket (instance or id) to copy the object to.
            Default: current bucket.
        :param key: Key name of destination object.
            Default: current object key.
        :param is_thumbnail: for thumbnail.
            Default: False.
        :returns: The copied object version.
        """
        new_ob = ObjectVersion.create(
            self.bucket if bucket is None else as_bucket(bucket),
            key or self.key,
            _file_id=self.file_id,
            root_file_id=self.root_file_id,
            is_thumbnail=is_thumbnail
        )

        for tag in self.tags:
            ObjectVersionTag.create_or_update(object_version=new_ob,
                                              key=tag.key,
                                              value=tag.value)

        return new_ob

    @ensure_unlocked(getter=lambda o: not o.bucket.locked)
    def remove(self):
        """Permanently remove a specific object version from the database.

        .. warning::

           This by-passes the normal versioning and should only be used when
           you want to permanently delete a specific object version. Otherwise
           use :py:data:`ObjectVersion.delete()`.

           Note the method does not remove the associated file instance which
           must be garbage collected.

        :returns: ``self``.
        """
        with db.session.begin_nested():
            if self.file_id:
                self.bucket.size -= self.file.size
            self.query.filter_by(
                bucket_id=self.bucket_id,
                key=self.key,
                version_id=self.version_id,
            ).delete()

        return self

    @classmethod
    def create(cls, bucket, key, _file_id=None, root_file_id=None, stream=None,
               mimetype=None, version_id=None, is_thumbnail=False, **kwargs):
        """Create a new object in a bucket.

        The created object is by default created as a delete marker. You must
        use ``set_contents()`` or ``set_location()`` in order to change this.

        :param bucket: The bucket (instance or id) to create the object in.
        :param key: Key of object.
        :param _file_id: For internal use.
        :param root_file_id: The FileInstance ID
            of the first version of the file.
        :param stream: File-like stream object. Used to set content of object
            immediately after being created.
        :param mimetype: MIME type of the file object if it is known.
        :param is_thumbnail: for thumbnail.
        :param kwargs: Keyword arguments passed to ``Object.set_contents()``.
        """
        bucket = as_bucket(bucket)

        if bucket.locked:
            raise BucketLockedError()

        with db.session.begin_nested():
            latest_obj = cls.query.filter(
                cls.bucket == bucket, cls.key == key, cls.is_head.is_(True)
            ).one_or_none()

            login_user_id = 0
            if current_user and current_user.is_authenticated:
                login_user_id = current_user.get_id()

            if latest_obj is not None:
                # set updated user id.
                latest_obj.updated_user_id = login_user_id
                latest_obj.is_head = False
                db.session.add(latest_obj)

            # By default objects are created in a deleted state (i.e.
            # file_id is null).
            obj = cls(
                bucket=bucket,
                key=key,
                version_id=version_id or uuid.uuid4(),
                is_head=True,
                mimetype=mimetype,
                created_user_id=login_user_id,
                updated_user_id=login_user_id,
                is_show=False,
                is_thumbnail=is_thumbnail,
            )
            if _file_id:
                file_ = _file_id if isinstance(_file_id, FileInstance) else \
                    FileInstance.get(_file_id)
                obj.set_file(file_)
                obj.root_file_id = root_file_id or file_.id
            db.session.add(obj)
        if stream:
            obj.set_contents(stream, **kwargs)
        return obj

    @classmethod
    def get(cls, bucket=None, key=None, version_id=None):
        """Fetch a specific object.

        By default the latest object version is returned, if
        ``version_id`` is not set.

        :param bucket: The bucket (instance or id) to get the object from.
        :param key: Key of object.
        :param version_id: Specific version of an object.
        """
        filters = []

        if bucket:
            filters.append(cls.bucket_id == as_bucket_id(bucket))
        if key:
            filters.append(cls.key == key)
        if version_id:
            filters.append(cls.version_id == version_id)
        else:
            filters.append(cls.is_head.is_(True))
            filters.append(cls.file_id.isnot(None))

        return cls.query.filter(*filters).one_or_none()

    @classmethod
    def get_versions(cls, bucket, key, desc=True):
        """Fetch all versions of a specific object.

        :param bucket: The bucket (instance or id) to get the object from.
        :param key: Key of object.
        :param desc: Sort results desc if True, asc otherwise.
        :returns: The query to execute to fetch all versions.
        """
        filters = [
            cls.bucket_id == as_bucket_id(bucket),
            cls.key == key,
        ]

        order = cls.created.desc() if desc else cls.created.asc()

        return cls.query.filter(*filters).order_by(cls.key, order)

    @classmethod
    def delete(cls, bucket, key):
        """Delete an object.

        Technically works by creating a new version which works as a delete
        marker.

        :param bucket: The bucket (instance or id) to delete the object from.
        :param key: Key of object.
        :returns: Created delete marker object if key exists else ``None``.
        """
        bucket_id = as_bucket_id(bucket)

        obj = cls.get(bucket_id, key)
        if obj:
            return cls.create(as_bucket(bucket), key)
        return None

    @classmethod
    def get_by_bucket(cls, bucket, versions=False, with_deleted=False,
                      asc_sort=False):
        """Return query that fetches all the objects in a bucket.

        :param bucket: The bucket (instance or id) to query.
        :param versions: Select all versions if True, only heads otherwise.
        :param with_deleted: Select also deleted objects if True.
        :param asc_sort: whether prioritize acs sorting or not.
        :returns: The query to retrieve filtered objects in the given bucket.
        """
        bucket_id = bucket.id if isinstance(bucket, Bucket) else bucket

        filters = [
            cls.bucket_id == bucket_id,
        ]

        if not versions:
            filters.append(cls.is_head.is_(True))

        if not with_deleted:
            filters.append(cls.file_id.isnot(None))

        query = cls.query.filter(*filters)

        if asc_sort:
            query = query.order_by(cls.created.asc(), cls.key)
        else:
            query = query.order_by(cls.key, cls.created.desc())
        return query

    @classmethod
    def relink_all(cls, old_file, new_file):
        """Relink all object versions (for a given file) to a new file.

        .. warning::

           Use this method with great care.
        """
        new_file.checksum = old_file.checksum
        assert old_file.checksum == new_file.checksum
        assert old_file.id
        assert new_file.id

        with db.session.begin_nested():
            ObjectVersion.query.filter_by(file_id=str(old_file.id)).update({
                ObjectVersion.file_id: str(new_file.id)})

    @classmethod
    def num_version_link_to_files(cls, file_ids):
        """Count the number of versions that link to files with file_id.

        :param file_ids: Specific list of file id.
        """
        if file_ids:
            return db.session.query(cls.file_id, func.count(cls.version_id)) \
                .filter(cls.file_id.in_(file_ids)) \
                .group_by(cls.file_id) \
                .all()

        return []

    def get_tags(self):
        """Get tags for object version as dictionary."""
        return {t.key: t.value for t in self.tags}

    def __eq__(self, other):
        """Check if the two object are equals."""
        return other and isinstance(other, self.__class__) and \
            self.key == other.key and self.file_id == other.file_id

    def __ne__(self, other):
        """Check if are not equal."""
        return not self.__eq__(other=other)


class ObjectVersionTag(db.Model):
    """Model for storing tags associated to object versions.

    Used for storing extra technical information for an object version.
    """

    __tablename__ = 'files_objecttags'

    version_id = db.Column(
        UUIDType,
        db.ForeignKey(ObjectVersion.version_id, ondelete='CASCADE'),
        default=uuid.uuid4,
        primary_key=True, )
    """Object version id."""

    key = db.Column(db.String(255), primary_key=True)
    """Tag key."""

    value = db.Column(db.Text, nullable=False)
    """Tag value."""

    object_version = db.relationship(ObjectVersion, backref='tags')
    """Relationship to object versions."""

    def copy(self, object_version=None, key=None):
        """Copy a tag to a given object version.

        :param object_version: The object version instance to copy the tag to.
            Default: current object version.
        :param key: Key of destination tag.
            Default: current tag key.
        :return: The copied object version tag.
        """
        return ObjectVersionTag.create(
            self.object_version if object_version is None else object_version,
            key or self.key,
            self.value
        )

    @classmethod
    def get(cls, object_version, key):
        """Get the tag object."""
        return cls.query.filter_by(
            version_id=as_object_version_id(object_version),
            key=key,
        ).one_or_none()

    @classmethod
    def create(cls, object_version, key, value):
        """Create a new tag for a given object version."""
        assert len(key) < 256
        assert len(value) < 256
        with db.session.begin_nested():
            obj = cls(version_id=as_object_version_id(object_version),
                      key=key,
                      value=value)
            db.session.add(obj)
        return obj

    @classmethod
    def create_or_update(cls, object_version, key, value):
        """Create or update a new tag for a given object version."""
        assert len(key) < 256
        assert len(value) < 256
        obj = cls.get(object_version, key)
        if obj:
            obj.value = value
            db.session.merge(obj)
        else:
            obj = cls.create(object_version, key, value)
        return obj

    @classmethod
    def get_value(cls, object_version, key):
        """Get the tag value."""
        obj = cls.get(object_version, key)
        return obj.value if obj else None

    @classmethod
    def delete(cls, object_version, key=None):
        """Delete tags.

        :param object_version: The object version instance or id.
        :param key: Key of the tag to delete.
            Default: delete all tags.
        """
        with db.session.begin_nested():
            q = cls.query.filter_by(
                version_id=as_object_version_id(object_version))
            if key:
                q = q.filter_by(key=key)
            q.delete()


class MultipartObject(db.Model, Timestamp):
    """Model for storing files in chunks.

    A multipart object belongs to a specific bucket and key and is identified
    by an upload id. You can have multiple multipart uploads for the same
    bucket and key. Once all parts of a multipart object is uploaded, the state
    is changed to ``completed``. Afterwards it is not possible to upload
    new parts. Once completed, the multipart object is merged, and added as
    a new version in the current object/bucket.

    All parts for a multipart upload must be of the same size, except for the
    last part.
    """

    __tablename__ = 'files_multipartobject'

    __table_args__ = (
        db.UniqueConstraint('upload_id', 'bucket_id', 'key', name='uix_item'),
    )

    upload_id = db.Column(
        UUIDType,
        default=uuid.uuid4,
        primary_key=True,
    )
    """Identifier for the specific version of an object."""

    bucket_id = db.Column(
        UUIDType,
        db.ForeignKey(Bucket.id, ondelete='RESTRICT'),
    )
    """Bucket identifier."""

    key = db.Column(
        db.Text().with_variant(mysql.VARCHAR(255), 'mysql'),
    )
    """Key identifying the object."""

    file_id = db.Column(
        UUIDType,
        db.ForeignKey(FileInstance.id, ondelete='RESTRICT'), nullable=False)
    """File instance for this multipart object."""

    chunk_size = db.Column(db.Integer, nullable=True)
    """Size of chunks for file."""

    size = db.Column(db.BigInteger, nullable=True)
    """Size of file."""

    completed = db.Column(db.Boolean(name='completed'),
                          nullable=False,
                          default=False)
    """Defines if object is the completed."""

    # Relationships definitions
    bucket = db.relationship(Bucket, backref='multipart_objects')
    """Relationship to buckets."""

    file = db.relationship(FileInstance, backref='multipart_objects')
    """Relationship to buckets."""

    def __repr__(self):
        """Return representation of the multipart object."""
        return "{0}:{2}:{1}".format(
            self.bucket_id, self.key, self.upload_id)

    @property
    def last_part_number(self):
        """Get last part number."""
        return int(self.size / self.chunk_size) \
            if self.size % self.chunk_size else \
            int(self.size / self.chunk_size) - 1

    @property
    def last_part_size(self):
        """Get size of last part."""
        return self.size % self.chunk_size

    @validates('key')
    def validate_key(self, key, key_):
        """Validate key."""
        return validate_key(key_)

    @staticmethod
    def is_valid_chunksize(chunk_size):
        """Check if size is valid."""
        min_csize = current_app.config['FILES_REST_MULTIPART_CHUNKSIZE_MIN']
        max_csize = current_app.config['FILES_REST_MULTIPART_CHUNKSIZE_MAX']
        return chunk_size >= min_csize and chunk_size <= max_csize

    @staticmethod
    def is_valid_size(size, chunk_size):
        """Validate max theoretical size."""
        min_csize = current_app.config['FILES_REST_MULTIPART_CHUNKSIZE_MIN']
        max_size = \
            chunk_size * current_app.config['FILES_REST_MULTIPART_MAX_PARTS']
        return size > min_csize and size <= max_size

    def expected_part_size(self, part_number):
        """Get expected part size for a particular part number."""
        last_part = self.multipart.last_part_number

        if part_number == last_part:
            return self.multipart.last_part_size
        elif part_number >= 0 and part_number < last_part:
            return self.multipart.chunk_size
        else:
            raise MultipartInvalidPartNumber()

    @ensure_uncompleted()
    def complete(self):
        """Mark a multipart object as complete."""
        if Part.count(self) != self.last_part_number + 1:
            raise MultipartMissingParts()

        with db.session.begin_nested():
            self.completed = True
            self.file.readable = True
            self.file.writable = False
        return self

    @ensure_completed()
    def merge_parts(self, version_id=None, **kwargs):
        """Merge parts into object version."""
        self.file.update_checksum(**kwargs)
        with db.session.begin_nested():
            obj = ObjectVersion.create(
                self.bucket,
                self.key,
                _file_id=self.file_id,
                version_id=version_id
            )
            self.delete()
        return obj

    def delete(self):
        """Delete a multipart object."""
        # Update bucket size.
        self.bucket.size -= self.size
        # Remove parts
        Part.query_by_multipart(self).delete()
        # Remove self
        self.query.filter_by(upload_id=self.upload_id).delete()

    @classmethod
    def create(cls, bucket, key, size, chunk_size):
        """Create a new object in a bucket."""
        bucket = as_bucket(bucket)

        if bucket.locked:
            raise BucketLockedError()

        # Validate chunk size.
        if not cls.is_valid_chunksize(chunk_size):
            raise MultipartInvalidChunkSize()

        # Validate max theoretical size.
        if not cls.is_valid_size(size, chunk_size):
            raise MultipartInvalidSize()

        # Validate max bucket size.
        bucket_limit = bucket.size_limit
        if bucket_limit and size > bucket_limit:
            desc = 'File size limit exceeded.' \
                if isinstance(bucket_limit, int) else bucket_limit.reason
            raise FileSizeError(description=desc)

        with db.session.begin_nested():
            file_ = FileInstance.create()
            file_.size = size
            obj = cls(
                upload_id=uuid.uuid4(),
                bucket=bucket,
                key=key,
                chunk_size=chunk_size,
                size=size,
                completed=False,
                file=file_,
            )
            bucket.size += size
            db.session.add(obj)
        file_.init_contents(
            size=size,
            default_location=bucket.location.uri,
            default_storage_class=bucket.default_storage_class,
        )
        return obj

    @classmethod
    def get(cls, bucket, key, upload_id, with_completed=False):
        """Fetch a specific multipart object."""
        q = cls.query.filter_by(
            upload_id=upload_id,
            bucket_id=as_bucket_id(bucket),
            key=key,
        )
        if not with_completed:
            q = q.filter(cls.completed.is_(False))

        return q.one_or_none()

    @classmethod
    def query_expired(cls, dt, bucket=None):
        """Query all uncompleted multipart uploads."""
        q = cls.query.filter(cls.created < dt).filter_by(completed=True)
        if bucket:
            q = q.filter(cls.bucket_id == as_bucket_id(bucket))
        return q

    @classmethod
    def query_by_bucket(cls, bucket):
        """Query all uncompleted multipart uploads."""
        return cls.query.filter(cls.bucket_id == as_bucket_id(bucket))


class Part(db.Model, Timestamp):
    """Part object."""

    __tablename__ = 'files_multipartobject_part'

    upload_id = db.Column(
        UUIDType,
        db.ForeignKey(MultipartObject.upload_id, ondelete='RESTRICT'),
        primary_key=True,
    )
    """Multipart object identifier."""

    part_number = db.Column(db.Integer, primary_key=True, autoincrement=False)
    """Part number."""

    checksum = db.Column(db.String(255), nullable=True)
    """String representing the checksum of the part."""

    # Relationships definitions
    multipart = db.relationship(MultipartObject, backref='parts')
    """Relationship to multipart objects."""

    @property
    def start_byte(self):
        """Get start byte in file of this part."""
        return self.part_number * self.multipart.chunk_size

    @property
    def end_byte(self):
        """Get end byte in file for this part."""
        return min(
            (self.part_number + 1) * self.multipart.chunk_size,
            self.multipart.size
        )

    @property
    def part_size(self):
        """Get size of this part."""
        return self.end_byte - self.start_byte

    @classmethod
    def create(cls, mp, part_number, stream=None, **kwargs):
        """Create a new part object in a multipart object."""
        if part_number < 0 or part_number > mp.last_part_number:
            raise MultipartInvalidPartNumber()

        with db.session.begin_nested():
            obj = cls(
                multipart=mp,
                part_number=part_number,
            )
            db.session.add(obj)
        if stream:
            obj.set_contents(stream, **kwargs)
        return obj

    @classmethod
    def get_or_none(cls, mp, part_number):
        """Get part number."""
        return cls.query.filter_by(
            upload_id=mp.upload_id,
            part_number=part_number
        ).one_or_none()

    @classmethod
    def get_or_create(cls, mp, part_number):
        """Get or create a part."""
        obj = cls.get_or_none(mp, part_number)
        if obj:
            return obj
        return cls.create(mp, part_number)

    @classmethod
    def delete(cls, mp, part_number):
        """Get part number."""
        return cls.query.filter_by(
            upload_id=mp.upload_id,
            part_number=part_number
        ).delete()

    @classmethod
    def query_by_multipart(cls, multipart):
        """Get all parts for a specific multipart upload.

        :param multipart: A :class:`invenio_files_rest.models.MultipartObject`
            instance.
        :returns: A :class:`invenio_files_rest.models.Part` instance.
        """
        upload_id = multipart.upload_id \
            if isinstance(multipart, MultipartObject) else multipart
        return cls.query.filter_by(
            upload_id=upload_id
        )

    @classmethod
    def count(cls, mp):
        """Count number of parts for a given multipart object."""
        return cls.query_by_multipart(mp).count()

    @ensure_uncompleted(getter=lambda o: not o.multipart.completed)
    def set_contents(self, stream, progress_callback=None):
        """Save contents of stream to part of file instance.

        If a the MultipartObject is completed this methods raises an
        ``MultipartAlreadyCompleted`` exception.

        :param stream: File-like stream.
        :param size: Size of stream if known.
        :param chunk_size: Desired chunk size to read stream in. It is up to
            the storage interface if it respects this value.
        """
        size, checksum = self.multipart.file.update_contents(
            stream, seek=self.start_byte, size=self.part_size,
            progress_callback=progress_callback,
        )
        self.checksum = checksum
        return self


__all__ = (
    'Bucket',
    'FileInstance',
    'Location',
    'MultipartObject',
    'ObjectVersion',
    'Part',
)
