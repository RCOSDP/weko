# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
# Copyright (C) 2022 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Files download/upload REST API similar to S3 for Invenio."""

import uuid
from functools import partial, wraps
from urllib.parse import parse_qsl

from flask import Blueprint, abort, current_app, request
from flask_login import current_user
from invenio_db import db
from invenio_rest import ContentNegotiatedMethodView
from marshmallow import missing
from webargs import fields
from webargs.flaskparser import use_kwargs

from .errors import (
    DuplicateTagError,
    ExhaustedStreamError,
    FileSizeError,
    InvalidTagError,
    MissingQueryParameter,
    MultipartInvalidChunkSize,
)
from .models import Bucket, MultipartObject, ObjectVersion, ObjectVersionTag, Part
from .proxies import current_files_rest, current_permission_factory
from .serializer import json_serializer
from .signals import file_deleted, file_downloaded, file_uploaded
from .tasks import merge_multipartobject, remove_file_data

blueprint = Blueprint(
    "invenio_files_rest",
    __name__,
    url_prefix="/files",
)


#
# Helpers
#
def as_uuid(value):
    """Convert value to UUID."""
    try:
        return uuid.UUID(value)
    except ValueError:
        abort(404)


def minsize_validator(value):
    """Validate Content-Length header.

    :raises invenio_files_rest.errors.FileSizeError: If the value is less
        than :data:`invenio_files_rest.config.FILES_REST_MIN_FILE_SIZE` size.
    """
    if value < current_app.config["FILES_REST_MIN_FILE_SIZE"]:
        raise FileSizeError()


def invalid_subresource_validator(value):
    """Ensure subresource."""
    abort(405)


def validate_tag(key, value):
    """Validate a tag.

    Keys must be less than 128 chars and values must be less than 256 chars.
    """
    # Note, parse_sql does not include a keys if the value is an empty string
    # (e.g. 'key=&test=a'), and thus technically we should not get strings
    # which have zero length.
    klen = len(key)
    vlen = len(value)

    return klen > 0 and klen < 256 and vlen > 0 and vlen < 256


def parse_header_tags():
    """Parse tags specified in the HTTP request header."""
    # Get the value of the custom HTTP header and interpret it as an query
    # string
    qs = request.headers.get(current_app.config["FILES_REST_FILE_TAGS_HEADER"], "")

    tags = {}
    for key, value in parse_qsl(qs):
        # Check for duplicate keys
        if key in tags:
            raise DuplicateTagError()
        # Check for too short/long keys and values.
        if not validate_tag(key, value):
            raise InvalidTagError()
        tags[key] = value
    return tags or None


#
# Part upload factories
#
@use_kwargs(
    {
        "part_number": fields.Int(
            metadata={
                "load_from": "partNumber",
                "location": "query",
            },
            required=True,
            data_key="partNumber",
        ),
        "content_length": fields.Int(
            metadata={
                "load_from": "Content-Length",
                "location": "headers",
            },
            required=True,
            validate=minsize_validator,
            data_key="Content-Length",
        ),
        "content_type": fields.Str(
            metadata={
                "load_from": "Content-Type",
                "location": "headers",
            },
            data_key="Content-Type",
        ),
        "content_md5": fields.Str(
            metadata={
                "load_from": "Content-MD5",
                "location": "headers",
            },
            data_key="Content-MD5",
        ),
    }
)
def default_partfactory(
    part_number=None, content_length=None, content_type=None, content_md5=None
):
    """Get default part factory.

    :param part_number: The part number. (Default: ``None``)
    :param content_length: The content length. (Default: ``None``)
    :param content_type: The HTTP Content-Type. (Default: ``None``)
    :param content_md5: The content MD5. (Default: ``None``)
    :returns: The content length, the part number, the stream, the content
        type, MD5 of the content.
    """
    return content_length, part_number, request.stream, content_type, content_md5, None


@use_kwargs(
    {
        "content_md5": fields.Str(
            metadata={
                "load_from": "Content-MD5",
                "location": "headers",
            },
            data_key="Content-MD5",
            load_default=None,
        ),
        "content_length": fields.Int(
            metadata={
                "load_from": "Content-Length",
                "location": "headers",
            },
            data_key="Content-Length",
            required=True,
            validate=minsize_validator,
        ),
        "content_type": fields.Str(
            metadata={
                "load_from": "Content-Type",
                "location": "headers",
            },
            data_key="Content-Type",
            load_default="",
        ),
    }
)
def stream_uploadfactory(content_md5=None, content_length=None, content_type=None):
    """Get default put factory.

    If Content-Type is ``'multipart/form-data'`` then the stream is aborted.

    :param content_md5: The content MD5. (Default: ``None``)
    :param content_length: The content length. (Default: ``None``)
    :param content_type: The HTTP Content-Type. (Default: ``None``)
    :returns: The stream, content length, MD5 of the content.
    """
    if content_type.startswith("multipart/form-data"):
        abort(422)

    return request.stream, content_length, content_md5, parse_header_tags()


@use_kwargs(
    {
        "part_number": fields.Int(
            metadata={
                "load_from": "_chunkNumber",
                "location": "form",
            },
            data_key="_chunkNumber",
            required=True,
        ),
        "content_length": fields.Int(
            metadata={
                "load_from": "_currentChunkSize",
                "location": "form",
            },
            data_key="_currentChunkSize",
            required=True,
            validate=minsize_validator,
        ),
        "uploaded_file": fields.Raw(
            metadata={
                "load_from": "file",
                "location": "files",
            },
            data_key="file",
            required=True,
        ),
    }
)
def ngfileupload_partfactory(part_number=None, content_length=None, uploaded_file=None):
    """Part factory for ng-file-upload.

    :param part_number: The part number. (Default: ``None``)
    :param content_length: The content length. (Default: ``None``)
    :param uploaded_file: The upload request. (Default: ``None``)
    :returns: The content length, part number, stream, HTTP Content-Type
        header.
    """
    return (
        content_length,
        part_number,
        uploaded_file.stream,
        uploaded_file.headers.get("Content-Type"),
        None,
        None,
    )


@use_kwargs(
    {
        "content_length": fields.Int(
            metadata={
                "load_from": "_totalSize",
                "location": "form",
            },
            data_key="_totalSize",
            required=True,
        ),
        "content_type": fields.Str(
            metadata={
                "load_from": "Content-Type",
                "location": "headers",
            },
            data_key="Content-Type",
            required=True,
        ),
        "uploaded_file": fields.Raw(
            metadata={
                "load_from": "file",
                "location": "files",
            },
            data_key="file",
            required=True,
        ),
    }
)
def ngfileupload_uploadfactory(
    content_length=None, content_type=None, uploaded_file=None
):
    """Get default put factory.

    If Content-Type is ``'multipart/form-data'`` then the stream is aborted.

    :param content_length: The content length. (Default: ``None``)
    :param content_type: The HTTP Content-Type. (Default: ``None``)
    :param uploaded_file: The upload request. (Default: ``None``)
    :param file_tags_header: The file tags. (Default: ``None``)
    :returns: A tuple containing stream, content length, and empty header.
    """
    if not content_type.startswith("multipart/form-data"):
        abort(422)

    return uploaded_file.stream, content_length, None, parse_header_tags()


#
# Object retrieval
#
def pass_bucket(f):
    """Decorate to retrieve a bucket."""

    @wraps(f)
    def decorate(*args, **kwargs):
        bucket_id = kwargs.pop("bucket_id")
        bucket = Bucket.get(as_uuid(bucket_id))
        if not bucket:
            abort(404, "Bucket does not exist.")
        return f(bucket=bucket, *args, **kwargs)

    return decorate


def pass_multipart(with_completed=False):
    """Decorate to retrieve an object."""

    def decorate(f):
        @wraps(f)
        def inner(self, bucket, key, upload_id, *args, **kwargs):
            obj = MultipartObject.get(
                bucket, key, upload_id, with_completed=with_completed
            )
            if obj is None:
                abort(404, "uploadId does not exists.")
            return f(self, obj, *args, **kwargs)

        return inner

    return decorate


def ensure_input_stream_is_not_exhausted(f):
    """Make sure that the input stream has not been read already."""

    @wraps(f)
    def decorate(*args, **kwargs):
        if request.content_length and request.stream.is_exhausted:
            raise ExhaustedStreamError()
        return f(*args, **kwargs)

    return decorate


#
# Permission checking
#
def check_permission(permission, hidden=True):
    """Check if permission is allowed.

    If permission fails then the connection is aborted.

    :param permission: The permission to check.
    :param hidden: Determine if a 404 error (``True``) or 401/403 error
        (``False``) should be returned if the permission is rejected (i.e.
        hide or reveal the existence of a particular object).
    """
    if permission is not None and not permission.can():
        if hidden:
            abort(404)
        else:
            if current_user.is_authenticated:
                abort(403, "You do not have a permission for this action")
            abort(401)


def need_permissions(object_getter, action, hidden=True):
    """Get permission for buckets or abort.

    :param object_getter: The function used to retrieve the object and pass it
        to the permission factory.
    :param action: The action needed.
    :param hidden: Determine which kind of error to return. (Default: ``True``)
    """

    def decorator_builder(f):
        @wraps(f)
        def decorate(*args, **kwargs):
            check_permission(
                current_permission_factory(
                    object_getter(*args, **kwargs),
                    action(*args, **kwargs) if callable(action) else action,
                ),
                hidden=hidden,
            )
            return f(*args, **kwargs)

        return decorate

    return decorator_builder


need_location_permission = partial(
    need_permissions, lambda *args, **kwargs: kwargs.get("location")
)


need_bucket_permission = partial(
    need_permissions, lambda *args, **kwargs: kwargs.get("bucket")
)


#
# REST resources
#
class LocationResource(ContentNegotiatedMethodView):
    """Service resource."""

    def __init__(self, *args, **kwargs):
        """Instantiate content negotiated view."""
        super(LocationResource, self).__init__(*args, **kwargs)

    @need_location_permission("location-update", hidden=False)
    def post(self):
        """Create bucket."""
        with db.session.begin_nested():
            bucket = Bucket.create()
        db.session.commit()
        return self.make_response(
            data=bucket,
            context={
                "class": Bucket,
            },
        )


class BucketResource(ContentNegotiatedMethodView):
    """Bucket item resource."""

    get_args = {
        "versions": fields.Raw(
            metadata={"location": "query"},
        ),
        "uploads": fields.Raw(
            metadata={"location": "query"},
        ),
    }

    def __init__(self, *args, **kwargs):
        """Instantiate content negotiated view."""
        super(BucketResource, self).__init__(*args, **kwargs)

    @need_permissions(lambda self, bucket: bucket, "bucket-listmultiparts")
    def multipart_listuploads(self, bucket):
        """List objects in a bucket.

        :param bucket: A :class:`invenio_files_rest.models.Bucket` instance.
        :returns: The Flask response.
        """
        return self.make_response(
            data=MultipartObject.query_by_bucket(bucket).limit(1000).all(),
            context={
                "class": MultipartObject,
                "bucket": bucket,
                "many": True,
            },
        )

    @need_permissions(
        lambda self, bucket, versions: bucket,
        "bucket-read",
    )
    def listobjects(self, bucket, versions):
        """List objects in a bucket.

        :param bucket: A :class:`invenio_files_rest.models.Bucket` instance.
        :returns: The Flask response.
        """
        if versions is not missing:
            check_permission(
                current_permission_factory(bucket, "bucket-read-versions"), hidden=False
            )
        return self.make_response(
            data=ObjectVersion.get_by_bucket(
                bucket.id, versions=versions is not missing
            )
            .limit(1000)
            .all(),
            context={
                "class": ObjectVersion,
                "bucket": bucket,
                "many": True,
            },
        )

    @use_kwargs(get_args)
    @pass_bucket
    def get(self, bucket=None, versions=missing, uploads=missing):
        """Get list of objects in the bucket.

        :param bucket: A :class:`invenio_files_rest.models.Bucket` instance.
        :returns: The Flask response.
        """
        if uploads is not missing:
            return self.multipart_listuploads(bucket)
        else:
            return self.listobjects(bucket, versions)

    @pass_bucket
    @need_bucket_permission("bucket-read")
    def head(self, bucket=None, **kwargs):
        """Check the existence of the bucket."""


class ObjectResource(ContentNegotiatedMethodView):
    """Object item resource."""

    delete_args = {
        "version_id": fields.UUID(
            metadata={
                "load_from": "versionId",
                "location": "query",
            },
            data_key="versionId",
            load_default=None,
        ),
        "upload_id": fields.UUID(
            metadata={
                "load_from": "uploadId",
                "location": "query",
            },
            data_key="uploadId",
            load_default=None,
        ),
        "uploads": fields.Raw(
            metadata={
                "location": "query",
            },
            validate=invalid_subresource_validator,
        ),
    }

    get_args = dict(
        delete_args,
        download=fields.Raw(
            metadata={
                "location": "query",
            },
            load_default=None,
        ),
    )

    post_args = {
        "uploads": fields.Raw(
            metadata={
                "location": "query",
            }
        ),
        "upload_id": fields.UUID(
            metadata={
                "location": "query",
                "load_from": "uploadId",
            },
            data_key="uploadId",
            load_default=None,
        ),
    }

    put_args = {
        "upload_id": fields.UUID(
            metadata={
                "location": "query",
                "load_from": "uploadId",
            },
            data_key="uploadId",
            load_default=None,
        ),
    }

    multipart_init_args = {
        "size": fields.Int(
            metadata={
                "locations": ("query", "json"),
            },
            load_default=None,
        ),
        "part_size": fields.Int(
            metadata={
                "locations": ("query", "json"),
                "load_from": "partSize",
            },
            load_default=None,
            data_key="partSize",
        ),
    }

    def __init__(self, *args, **kwargs):
        """Instantiate content negotiated view."""
        super(ObjectResource, self).__init__(*args, **kwargs)

    #
    # ObjectVersion helpers
    #
    @staticmethod
    def check_object_permission(obj):
        """Retrieve object and abort if it doesn't exists."""
        check_permission(current_permission_factory(obj, "object-read"))
        if not obj.is_head:
            check_permission(
                current_permission_factory(obj, "object-read-version"), hidden=False
            )

    @classmethod
    def get_object(cls, bucket, key, version_id):
        """Retrieve object and abort if it doesn't exist.

        If the file is not found, the connection is aborted and the 404
        error is returned.

        :param bucket: The bucket (instance or id) to get the object from.
        :param key: The file key.
        :param version_id: The version ID.
        :returns: A :class:`invenio_files_rest.models.ObjectVersion` instance.
        """
        obj = ObjectVersion.get(bucket, key, version_id=version_id)
        if not obj:
            abort(404, "Object does not exists.")

        cls.check_object_permission(obj)

        return obj

    def create_object(self, bucket, key):
        """Create a new object.

        :param bucket: The bucket (instance or id) to get the object from.
        :param key: The file key.
        :returns: A Flask response.
        """
        # Initial validation of size based on Content-Length.
        # User can tamper with Content-Length, so this is just an initial up
        # front check. The storage subsystem must validate the size limit as
        # well.
        stream, content_length, content_md5, tags = current_files_rest.upload_factory()

        size_limit = bucket.size_limit
        if content_length and size_limit and content_length > size_limit:
            desc = (
                "File size limit exceeded."
                if isinstance(size_limit, int)
                else size_limit.reason
            )
            raise FileSizeError(description=desc)

        with db.session.begin_nested():
            obj = ObjectVersion.create(bucket, key)
            obj.set_contents(stream, size=content_length, size_limit=size_limit)
            # Check add tags
            if tags:
                for key, value in tags.items():
                    ObjectVersionTag.create(obj, key, value)

        db.session.commit()
        file_uploaded.send(current_app._get_current_object(), obj=obj)
        return self.make_response(
            data=obj,
            context={
                "class": ObjectVersion,
                "bucket": bucket,
            },
            etag=obj.file.checksum,
        )

    @need_permissions(
        lambda self, bucket, obj, *args: obj,
        "object-delete",
        hidden=False,  # Because get_object permission check has already run
    )
    def delete_object(self, bucket, obj, version_id):
        """Delete an existing object.

        :param bucket: The bucket (instance or id) to get the object from.
        :param obj: A :class:`invenio_files_rest.models.ObjectVersion`
            instance.
        :param version_id: The version ID.
        :returns: A Flask response.
        """
        if version_id is None:
            # Create a delete marker.
            with db.session.begin_nested():
                ObjectVersion.delete(bucket, obj.key)
        else:
            # Permanently delete specific object version.
            check_permission(
                current_permission_factory(bucket, "object-delete-version"),
                hidden=False,
            )
            obj.remove()
            # Set newest object as head
            if obj.is_head:
                latest = ObjectVersion.get_versions(
                    obj.bucket, obj.key, desc=True
                ).first()
                if latest:
                    latest.is_head = True

            if obj.file_id:
                remove_file_data.delay(str(obj.file_id))
        db.session.commit()
        file_deleted.send(current_app._get_current_object(), obj=obj)
        return self.make_response("", 204)

    @staticmethod
    def send_object(
        bucket,
        obj,
        expected_chksum=None,
        logger_data=None,
        restricted=True,
        as_attachment=False,
    ):
        """Send an object for a given bucket.

        :param bucket: The bucket (instance or id) to get the object from.
        :param obj: A :class:`invenio_files_rest.models.ObjectVersion`
            instance.
        :params expected_chksum: Expected checksum.
        :param logger_data: The python logger.
        :param kwargs: Keyword arguments passed to ``Object.send_file()``
        :returns: A Flask response.
        """
        if not obj.is_head:
            check_permission(
                current_permission_factory(obj, "object-read-version"), hidden=False
            )

        if expected_chksum and obj.file.checksum != expected_chksum:
            current_app.logger.warning(
                "File checksum mismatch detected.", extra=logger_data
            )

        file_downloaded.send(current_app._get_current_object(), obj=obj)
        return obj.send_file(restricted=restricted, as_attachment=as_attachment)

    #
    # MultipartObject helpers
    #
    @pass_multipart(with_completed=True)
    @need_permissions(lambda self, multipart: multipart, "multipart-read")
    def multipart_listparts(self, multipart):
        """Get parts of a multipart upload.

        :param multipart: A :class:`invenio_files_rest.models.MultipartObject`
            instance.
        :returns: A Flask response.
        """
        return self.make_response(
            data=Part.query_by_multipart(multipart)
            .order_by(Part.part_number)
            .limit(1000)
            .all(),
            context={
                "class": Part,
                "multipart": multipart,
                "many": True,
            },
        )

    @use_kwargs(multipart_init_args)
    def multipart_init(self, bucket, key, size=None, part_size=None):
        """Initialize a multipart upload.

        :param bucket: The bucket (instance or id) to get the object from.
        :param key: The file key.
        :param size: The total size.
        :param part_size: The part size.
        :raises invenio_files_rest.errors.MissingQueryParameter: If size or
            part_size are not defined.
        :returns: A Flask response.
        """
        if size is None:
            raise MissingQueryParameter("size")
        if part_size is None:
            raise MissingQueryParameter("partSize")
        multipart = MultipartObject.create(bucket, key, size, part_size)
        db.session.commit()
        return self.make_response(
            data=multipart,
            context={
                "class": MultipartObject,
                "bucket": bucket,
            },
        )

    @pass_multipart(with_completed=True)
    def multipart_uploadpart(self, multipart):
        """Upload a part.

        :param multipart: A :class:`invenio_files_rest.models.MultipartObject`
            instance.
        :returns: A Flask response.
        """
        (
            content_length,
            part_number,
            stream,
            content_type,
            content_md5,
            tags,
        ) = current_files_rest.multipart_partfactory()

        if content_length:
            ck = (
                multipart.last_part_size
                if part_number == multipart.last_part_number
                else multipart.chunk_size
            )

            if ck != content_length:
                raise MultipartInvalidChunkSize()

        # Create part
        try:
            p = Part.get_or_create(multipart, part_number)
            p.set_contents(stream)
            db.session.commit()
        except Exception:
            # We remove the Part since incomplete data may have been written to
            # disk (e.g. client closed connection etc.) so it must be
            # reuploaded.
            db.session.rollback()
            Part.delete(multipart, part_number)
            raise
        return self.make_response(
            data=p,
            context={
                "class": Part,
            },
            etag=p.checksum,
        )

    @pass_multipart(with_completed=True)
    def multipart_complete(self, multipart):
        """Complete a multipart upload.

        :param multipart: A :class:`invenio_files_rest.models.MultipartObject`
            instance.
        :returns: A Flask response.
        """
        multipart.complete()
        db.session.commit()

        version_id = str(uuid.uuid4())

        return self.make_response(
            data=multipart,
            context={
                "class": MultipartObject,
                "bucket": multipart.bucket,
                "object_version_id": version_id,
            },
            # This will wait for the result, and send whitespace on the
            # connection until the task has finished (or max timeout reached).
            task_result=merge_multipartobject.delay(
                str(multipart.upload_id),
                version_id=version_id,
            ),
        )

    @pass_multipart()
    @need_permissions(
        lambda self, multipart: multipart,
        "multipart-delete",
    )
    def multipart_delete(self, multipart):
        """Abort a multipart upload.

        :param multipart: A :class:`invenio_files_rest.models.MultipartObject`
            instance.
        :returns: A Flask response.
        """
        multipart.delete()
        db.session.commit()
        if multipart.file_id:
            remove_file_data.delay(str(multipart.file_id))
        return self.make_response("", 204)

    #
    # HTTP methods implementations
    #
    @use_kwargs(get_args)
    @pass_bucket
    def get(
        self,
        bucket=None,
        key=None,
        version_id=None,
        upload_id=None,
        uploads=None,
        download=None,
    ):
        """Get object or list parts of a multipart upload.

        :param bucket: The bucket (instance or id) to get the object from.
            (Default: ``None``)
        :param key: The file key. (Default: ``None``)
        :param version_id: The version ID. (Default: ``None``)
        :param upload_id: The upload ID. (Default: ``None``)
        :param download: The download flag. (Default: ``None``)
        :returns: A Flask response.
        """
        if upload_id:
            return self.multipart_listparts(bucket, key, upload_id)
        else:
            obj = self.get_object(bucket, key, version_id)
            if current_app.config["FILES_REST_XSENDFILE_ENABLED"]:
                response_constructor = current_app.config[
                    "FILES_REST_XSENDFILE_RESPONSE_FUNC"
                ]
                return response_constructor(obj)
            # If 'download' is missing from query string it will have
            # the value None.
            return self.send_object(bucket, obj, as_attachment=download is not None)

    @use_kwargs(post_args)
    @pass_bucket
    @need_bucket_permission("bucket-update")
    @ensure_input_stream_is_not_exhausted
    def post(self, bucket=None, key=None, uploads=missing, upload_id=None):
        """Upload a new object or start/complete a multipart upload.

        :param bucket: The bucket (instance or id) to get the object from.
            (Default: ``None``)
        :param key: The file key. (Default: ``None``)
        :param upload_id: The upload ID. (Default: ``None``)
        :returns: A Flask response.
        """
        if uploads is not missing:
            return self.multipart_init(bucket, key)
        elif upload_id is not None:
            return self.multipart_complete(bucket, key, upload_id)
        abort(403)

    @use_kwargs(put_args)
    @pass_bucket
    @need_bucket_permission("bucket-update")
    @ensure_input_stream_is_not_exhausted
    def put(self, bucket=None, key=None, upload_id=None):
        """Update a new object or upload a part of a multipart upload.

        :param bucket: The bucket (instance or id) to get the object from.
            (Default: ``None``)
        :param key: The file key. (Default: ``None``)
        :param upload_id: The upload ID. (Default: ``None``)
        :returns: A Flask response.
        """
        if upload_id is not None:
            return self.multipart_uploadpart(bucket, key, upload_id)
        else:
            return self.create_object(bucket, key)

    @use_kwargs(delete_args)
    @pass_bucket
    def delete(
        self, bucket=None, key=None, version_id=None, upload_id=None, uploads=None
    ):
        """Delete an object or abort a multipart upload.

        :param bucket: The bucket (instance or id) to get the object from.
            (Default: ``None``)
        :param key: The file key. (Default: ``None``)
        :param version_id: The version ID. (Default: ``None``)
        :param upload_id: The upload ID. (Default: ``None``)
        :returns: A Flask response.
        """
        if upload_id is not None:
            return self.multipart_delete(bucket, key, upload_id)
        else:
            obj = self.get_object(bucket, key, version_id)
            return self.delete_object(bucket, obj, version_id)


#
# Blueprint definition
#
location_view = LocationResource.as_view(
    "location_api",
    serializers={
        "application/json": json_serializer,
    },
)
bucket_view = BucketResource.as_view(
    "bucket_api",
    serializers={
        "application/json": json_serializer,
    },
)
object_view = ObjectResource.as_view(
    "object_api",
    serializers={
        "application/json": json_serializer,
    },
)

blueprint.add_url_rule(
    "",
    view_func=location_view,
)
blueprint.add_url_rule(
    "/<string:bucket_id>",
    view_func=bucket_view,
)
blueprint.add_url_rule(
    "/<string:bucket_id>/<path:key>",
    view_func=object_view,
)
