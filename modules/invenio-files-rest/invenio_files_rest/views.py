# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
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

"""Files download/upload REST API similar to S3 for Invenio."""

from __future__ import absolute_import, print_function

import uuid
from functools import partial, wraps

from flask import Blueprint, abort, current_app, request
from flask_login import current_user
from invenio_db import db
from invenio_rest import ContentNegotiatedMethodView
from marshmallow import missing
from webargs import fields
from webargs.flaskparser import use_kwargs

from .errors import FileSizeError, MissingQueryParameter, \
    MultipartInvalidChunkSize
from .models import Bucket, MultipartObject, ObjectVersion, Part
from .proxies import current_files_rest, current_permission_factory
from .serializer import json_serializer
from .signals import file_downloaded
from .tasks import merge_multipartobject, remove_file_data

blueprint = Blueprint(
    'invenio_files_rest',
    __name__,
    url_prefix='/files',
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
    if value < current_app.config['FILES_REST_MIN_FILE_SIZE']:
        raise FileSizeError()


def invalid_subresource_validator(value):
    """Ensure subresource."""
    abort(405)


#
# Part upload factories
#
@use_kwargs({
    'part_number': fields.Int(
        load_from='partNumber',
        location='query',
        required=True,
    ),
    'content_length': fields.Int(
        load_from='Content-Length',
        location='headers',
        required=True,
        validate=minsize_validator,
    ),
    'content_type': fields.Str(
        load_from='Content-Type',
        location='headers',
    ),
    'content_md5': fields.Str(
        load_from='Content-MD5',
        location='headers',
    ),
})
def default_partfactory(part_number=None, content_length=None,
                        content_type=None, content_md5=None):
    """Get default part factory.

    :param part_number: The part number. (Default: ``None``)
    :param content_length: The content length. (Default: ``None``)
    :param content_type: The HTTP Content-Type. (Default: ``None``)
    :param content_md5: The content MD5. (Default: ``None``)
    :returns: The content length, the part number, the stream, the content
        type, MD5 of the content.
    """
    return content_length, part_number, request.stream, content_type, \
        content_md5


@use_kwargs({
    'content_md5': fields.Str(
        load_from='Content-MD5',
        location='headers',
        missing=None,
    ),
    'content_length': fields.Int(
        load_from='Content-Length',
        location='headers',
        required=True,
        validate=minsize_validator,
    ),
    'content_type': fields.Str(
        load_from='Content-Type',
        location='headers',
        missing='',
    ),
})
def stream_uploadfactory(content_md5=None, content_length=None,
                         content_type=None):
    """Get default put factory.

    If Content-Type is ``'multipart/form-data'`` then the stream is aborted.

    :param content_md5: The content MD5. (Default: ``None``)
    :param content_length: The content length. (Default: ``None``)
    :param content_type: The HTTP Content-Type. (Default: ``None``)
    :returns: The stream, content length, MD5 of the content.
    """
    if content_type.startswith('multipart/form-data'):
        abort(422)
    return request.stream, content_length, content_md5


@use_kwargs({
    'part_number': fields.Int(
        load_from='_chunkNumber',
        location='form',
        required=True,
    ),
    'content_length': fields.Int(
        load_from='_currentChunkSize',
        location='form',
        required=True,
        validate=minsize_validator,
    ),
    'uploaded_file': fields.Raw(
        load_from='file',
        location='files',
        required=True,
    ),
})
def ngfileupload_partfactory(part_number=None, content_length=None,
                             uploaded_file=None):
    """Part factory for ng-file-upload.

    :param part_number: The part number. (Default: ``None``)
    :param content_length: The content length. (Default: ``None``)
    :param uploaded_file: The upload request. (Default: ``None``)
    :returns: The content length, part number, stream, HTTP Content-Type
        header.
    """
    return content_length, part_number, uploaded_file.stream, \
        uploaded_file.headers.get('Content-Type'), None


@use_kwargs({
    'content_length': fields.Int(
        load_from='_totalSize',
        location='form',
        required=True,
    ),
    'content_type': fields.Str(
        load_from='Content-Type',
        location='headers',
        required=True,
    ),
    'uploaded_file': fields.Raw(
        load_from='file',
        location='files',
        required=True,
    ),
})
def ngfileupload_uploadfactory(content_length=None, content_type=None,
                               uploaded_file=None):
    """Get default put factory.

    If Content-Type is ``'multipart/form-data'`` then the stream is aborted.

    :param content_length: The content length. (Default: ``None``)
    :param content_type: The HTTP Content-Type. (Default: ``None``)
    :param uploaded_file: The upload request. (Default: ``None``)
    :returns: A tuple containing stream, content length, and empty header.
    """
    if not content_type.startswith('multipart/form-data'):
        abort(422)

    return uploaded_file.stream, content_length, None


#
# Object retrieval
#
def pass_bucket(f):
    """Decorate to retrieve a bucket."""
    @wraps(f)
    def decorate(*args, **kwargs):
        bucket_id = kwargs.pop('bucket_id')
        bucket = Bucket.get(as_uuid(bucket_id))
        if not bucket:
            abort(404, 'Bucket does not exist.')
        return f(bucket=bucket, *args, **kwargs)
    return decorate


def pass_multipart(with_completed=False):
    """Decorate to retrieve an object."""
    def decorate(f):
        @wraps(f)
        def inner(self, bucket, key, upload_id, *args, **kwargs):
            obj = MultipartObject.get(
                bucket, key, upload_id, with_completed=with_completed)
            if obj is None:
                abort(404, 'uploadId does not exists.')
            return f(self, obj, *args, **kwargs)
        return inner
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
                abort(403,
                      'You do not have a permission for this action')
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
            check_permission(current_permission_factory(
                object_getter(*args, **kwargs),
                action(*args, **kwargs) if callable(action) else action,

            ), hidden=hidden)
            return f(*args, **kwargs)
        return decorate
    return decorator_builder


need_location_permission = partial(
    need_permissions,
    lambda *args, **kwargs: kwargs.get('location')
)


need_bucket_permission = partial(
    need_permissions,
    lambda *args, **kwargs: kwargs.get('bucket')
)


#
# REST resources
#
class LocationResource(ContentNegotiatedMethodView):
    """Service resource."""

    def __init__(self, *args, **kwargs):
        """Instatiate content negotiated view."""
        super(LocationResource, self).__init__(*args, **kwargs)

    @need_location_permission('location-update', hidden=False)
    def post(self):
        """Create bucket."""
        with db.session.begin_nested():
            bucket = Bucket.create(
                storage_class=current_app.config[
                    'FILES_REST_DEFAULT_STORAGE_CLASS'
                ],
            )
        db.session.commit()
        return self.make_response(
            data=bucket,
            context={
                'class': Bucket,
            }
        )


class BucketResource(ContentNegotiatedMethodView):
    """Bucket item resource."""

    get_args = {
        'versions': fields.Raw(
            location='query',
        ),
        'uploads': fields.Raw(
            location='query',
        )
    }

    def __init__(self, *args, **kwargs):
        """Instatiate content negotiated view."""
        super(BucketResource, self).__init__(*args, **kwargs)

    @need_permissions(lambda self, bucket: bucket, 'bucket-listmultiparts')
    def multipart_listuploads(self, bucket):
        """List objects in a bucket.

        :param bucket: A :class:`invenio_files_rest.models.Bucket` instance.
        :returns: The Flask response.
        """
        return self.make_response(
            data=MultipartObject.query_by_bucket(bucket).limit(1000).all(),
            context={
                'class': MultipartObject,
                'bucket': bucket,
                'many': True,
            }
        )

    @need_permissions(
        lambda self, bucket, versions: bucket,
        'bucket-read',
    )
    def listobjects(self, bucket, versions):
        """List objects in a bucket.

        :param bucket: A :class:`invenio_files_rest.models.Bucket` instance.
        :returns: The Flask response.
        """
        if versions is not missing:
            check_permission(
                current_permission_factory(bucket, 'bucket-read-versions'),
                hidden=False
            )
        return self.make_response(
            data=ObjectVersion.get_by_bucket(
                bucket.id, versions=versions is not missing).limit(1000).all(),
            context={
                'class': ObjectVersion,
                'bucket': bucket,
                'many': True,
            }
        )

    @use_kwargs(get_args)
    @pass_bucket
    def get(self, bucket=None, versions=None, uploads=None):
        """Get list of objects in the bucket.

        :param bucket: A :class:`invenio_files_rest.models.Bucket` instance.
        :returns: The Flask response.
        """
        if uploads is not missing:
            return self.multipart_listuploads(bucket)
        else:
            return self.listobjects(bucket, versions)

    @pass_bucket
    @need_bucket_permission('bucket-read')
    def head(self, bucket=None, **kwargs):
        """Check the existence of the bucket."""


class ObjectResource(ContentNegotiatedMethodView):
    """Object item resource."""

    get_args = {
        'version_id': fields.UUID(
            location='query',
            load_from='versionId',
            missing=None,
        ),
        'upload_id': fields.UUID(
            location='query',
            load_from='uploadId',
            missing=None,
        ),
        'uploads': fields.Raw(
            location='query',
            validate=invalid_subresource_validator,
        ),
    }

    delete_args = get_args

    post_args = {
        'uploads': fields.Raw(
            location='query',
        ),
        'upload_id': fields.UUID(
            location='query',
            load_from='uploadId',
            missing=None,
        )
    }

    put_args = {
        'upload_id': fields.UUID(
            location='query',
            load_from='uploadId',
            missing=None,
        ),
    }

    multipart_init_args = {
        'size': fields.Int(
            locations=('query', 'json'),
            missing=None,
        ),
        'part_size': fields.Int(
            locations=('query', 'json'),
            missing=None,
            load_from='partSize',
        ),
    }

    def __init__(self, *args, **kwargs):
        """Instatiate content negotiated view."""
        super(ObjectResource, self).__init__(*args, **kwargs)

    #
    # ObjectVersion helpers
    #
    @staticmethod
    def check_object_permission(obj):
        """Retrieve object and abort if it doesn't exists."""
        check_permission(current_permission_factory(
            obj,
            'object-read'
        ))
        if not obj.is_head:
            check_permission(
                current_permission_factory(obj, 'object-read-version'),
                hidden=False
            )

    @classmethod
    def get_object(cls, bucket, key, version_id):
        """Retrieve object and abort if it doesn't exists.

        If the file is not found, the connection is aborted and the 404
        error is returned.

        :param bucket: The bucket (instance or id) to get the object from.
        :param key: The file key.
        :param version_id: The version ID.
        :returns: A :class:`invenio_files_rest.models.ObjectVersion` instance.
        """
        obj = ObjectVersion.get(bucket, key, version_id=version_id)
        if not obj:
            abort(404, 'Object does not exists.')

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
        stream, content_length, content_md5 = \
            current_files_rest.upload_factory()

        size_limit = bucket.size_limit
        if content_length and size_limit and content_length > size_limit:
            desc = 'File size limit exceeded.' \
                if isinstance(size_limit, int) else size_limit.reason
            raise FileSizeError(description=desc)

        with db.session.begin_nested():
            obj = ObjectVersion.create(bucket, key)
            obj.set_contents(
                stream, size=content_length, size_limit=size_limit)
        db.session.commit()
        return self.make_response(
            data=obj,
            context={
                'class': ObjectVersion,
                'bucket': bucket,
            },
            etag=obj.file.checksum
        )

    @need_permissions(
        lambda self, bucket, obj, *args: obj,
        'object-delete',
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
            db.session.commit()
        else:
            # Permanently delete specific object version.
            check_permission(
                current_permission_factory(bucket, 'object-delete-version'),
                hidden=False,
            )
            obj.remove()
            db.session.commit()
            if obj.file_id:
                remove_file_data.delay(str(obj.file_id))

        return self.make_response('', 204)

    @staticmethod
    def send_object(bucket, obj, expected_chksum=None, logger_data=None,
                    restricted=True):
        """Send an object for a given bucket.

        :param bucket: The bucket (instance or id) to get the object from.
        :param obj: A :class:`invenio_files_rest.models.ObjectVersion`
            instance.
        :params expected_chksum: Expected checksum.
        :param logger_data: The python logger.
        :returns: A Flask response.
        """
        if not obj.is_head:
            check_permission(
                current_permission_factory(obj, 'object-read-version'),
                hidden=False
            )

        if expected_chksum and obj.file.checksum != expected_chksum:
            current_app.logger.warning(
                'File checksum mismatch detected.', extra=logger_data)

        file_downloaded.send(current_app._get_current_object(), obj=obj)
        return obj.send_file(restricted=restricted)

    #
    # MultipartObject helpers
    #
    @pass_multipart(with_completed=True)
    @need_permissions(
        lambda self, multipart: multipart,
        'multipart-read'
    )
    def multipart_listparts(self, multipart):
        """Get parts of a multipart upload.

        :param multipart: A :class:`invenio_files_rest.models.MultipartObject`
            instance.
        :returns: A Flask response.
        """
        return self.make_response(
            data=Part.query_by_multipart(
                multipart).order_by(Part.part_number).limit(1000).all(),
            context={
                'class': Part,
                'multipart': multipart,
                'many': True,
            }
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
            raise MissingQueryParameter('size')
        if part_size is None:
            raise MissingQueryParameter('partSize')
        multipart = MultipartObject.create(bucket, key, size, part_size)
        db.session.commit()
        return self.make_response(
            data=multipart,
            context={
                'class': MultipartObject,
                'bucket': bucket,
            }
        )

    @pass_multipart(with_completed=True)
    def multipart_uploadpart(self, multipart):
        """Upload a part.

        :param multipart: A :class:`invenio_files_rest.models.MultipartObject`
            instance.
        :returns: A Flask response.
        """
        content_length, part_number, stream, content_type, content_md5 = \
            current_files_rest.multipart_partfactory()

        if content_length:
            ck = multipart.last_part_size if \
                part_number == multipart.last_part_number \
                else multipart.chunk_size

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
                'class': Part,
            },
            etag=p.checksum
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
                'class': MultipartObject,
                'bucket': multipart.bucket,
                'object_version_id': version_id,
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
        'multipart-delete',
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
        return self.make_response('', 204)

    #
    # HTTP methods implementations
    #
    @use_kwargs(get_args)
    @pass_bucket
    def get(self, bucket=None, key=None, version_id=None, upload_id=None,
            uploads=None):
        """Get object or list parts of a multpart upload.

        :param bucket: The bucket (instance or id) to get the object from.
            (Default: ``None``)
        :param key: The file key. (Default: ``None``)
        :param version_id: The version ID. (Default: ``None``)
        :param upload_id: The upload ID. (Default: ``None``)
        :returns: A Flask response.
        """
        if upload_id:
            return self.multipart_listparts(bucket, key, upload_id)
        else:
            obj = self.get_object(bucket, key, version_id)
            return self.send_object(bucket, obj)

    @use_kwargs(post_args)
    @pass_bucket
    @need_bucket_permission('bucket-update')
    def post(self, bucket=None, key=None, uploads=None, upload_id=None):
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
    @need_bucket_permission('bucket-update')
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
    def delete(self, bucket=None, key=None, version_id=None, upload_id=None,
               uploads=None):
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
    'location_api',
    serializers={
        'application/json': json_serializer,
    }
)
bucket_view = BucketResource.as_view(
    'bucket_api',
    serializers={
        'application/json': json_serializer,
    }
)
object_view = ObjectResource.as_view(
    'object_api',
    serializers={
        'application/json': json_serializer,
    }
)

blueprint.add_url_rule(
    '',
    view_func=location_view,
)
blueprint.add_url_rule(
    '/<string:bucket_id>',
    view_func=bucket_view,
)
blueprint.add_url_rule(
    '/<string:bucket_id>/<path:key>',
    view_func=object_view,
)
