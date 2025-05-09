# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Files download/upload REST API similar to S3 for Invenio."""

from __future__ import absolute_import, print_function

import sys
import traceback
import uuid
from functools import partial, wraps

from flask import Blueprint, abort, current_app, jsonify, request, session
from flask_login import current_user
from invenio_db import db
from invenio_records.models import RecordMetadata
from invenio_rest import ContentNegotiatedMethodView
from marshmallow import missing
from six.moves.urllib.parse import parse_qsl
from webargs import fields
from webargs.flaskparser import use_kwargs

from weko_logging.activity_logger import UserActivityLogger

from .errors import DuplicateTagError, ExhaustedStreamError, FileSizeError, \
    InvalidTagError, MissingQueryParameter, MultipartInvalidChunkSize
from .models import Bucket, Location, MultipartObject, ObjectVersion, \
    ObjectVersionTag, Part
from .proxies import current_files_rest, current_permission_factory
from .serializer import json_serializer
from .signals import file_downloaded, file_previewed
from .tasks import merge_multipartobject, remove_file_data
from .utils import _location_has_quota, delete_file_instance

blueprint = Blueprint(
    'invenio_files_rest',
    __name__,
    url_prefix='/files',
    template_folder='templates',
    static_folder='static',
)

admin_blueprint = Blueprint(
    'invenio_files_rest_admin',
    __name__,
    template_folder='templates',
    static_folder='static',
)

api_blueprint = Blueprint(
    'invenio_files_rest_api',
    __name__,
    url_prefix='/adm',
    template_folder='templates',
    static_folder='static',
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
    qs = request.headers.get(
        current_app.config['FILES_REST_FILE_TAGS_HEADER'], '')

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
@use_kwargs({
    'part_number': fields.Int(
        load_from='partNumber',
        location='query',
        required=True,
        data_key='partNumber',
    ),
    'content_length': fields.Int(
        load_from='Content-Length',
        location='headers',
        required=True,
        validate=minsize_validator,
        data_key='Content-Length',
    ),
    'content_type': fields.Str(
        load_from='Content-Type',
        location='headers',
        data_key='Content-Type',

    ),
    'content_md5': fields.Str(
        data_key='Content-MD5',
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
        content_md5, None


@use_kwargs({
    'content_md5': fields.Str(
        load_from='Content-MD5',
        data_key='Content-MD5',
        location='headers',
        missing=None,
    ),
    'content_length': fields.Int(
        load_from='Content-Length',
        data_key='Content-Length',
        location='headers',
        required=True,
        validate=minsize_validator,
    ),
    'content_type': fields.Str(
        load_from='Content-Type',
        data_key='Content-Type',
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

    return request.stream, content_length, content_md5, parse_header_tags()


@use_kwargs({
    'part_number': fields.Int(
        load_from='_chunkNumber',
        data_key='_chunkNumber',
        location='form',
        required=True,
    ),
    'content_length': fields.Int(
        load_from='_currentChunkSize',
        data_key='_currentChunkSize',
        location='form',
        required=True,
        validate=minsize_validator,
    ),
    'uploaded_file': fields.Raw(
        load_from='file',
        data_key='file',
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
        uploaded_file.headers.get('Content-Type'), None, None


@use_kwargs({
    'content_length': fields.Int(
        load_from='_totalSize',
        data_key='_totalSize',
        location='form',
        required=True,
    ),
    'content_type': fields.Str(
        load_from='Content-Type',
        data_key='Content-Type',
        location='headers',
        required=True,
    ),
    'uploaded_file': fields.Raw(
        load_from='file',
        data_key='file',
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
    :param file_tags_header: The file tags. (Default: ``None``)
    :returns: A tuple containing stream, content length, and empty header.
    """
    if not content_type.startswith('multipart/form-data'):
        abort(422)

    return uploaded_file.stream, content_length, None, parse_header_tags()


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
        if is_guest_login_can_access_file(permission):
            return
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


def is_guest_login_can_access_file(permission):
    """Check guest login upload file.

    Args:
        permission: The permission to check.

    Returns:
        [boolean]: True if the guest user can upload file.

    """
    if session and session.get('guest_token') is not None:
        guest_access_file_actions = [
            "files-rest-object-read", "files-rest-bucket-update",
            "files-rest-object-delete", "files-rest-object-delete-version",
        ]
        for need in permission.needs:
            if need.method == 'action' and \
                    need.value in guest_access_file_actions:
                return True
    return False


#
# REST resources
#
class LocationResource(ContentNegotiatedMethodView):
    """Service resource."""

    def __init__(self, *args, **kwargs):
        """Instantiate content negotiated view."""
        super(LocationResource, self).__init__(*args, **kwargs)

    @need_location_permission('location-update', hidden=False)
    def post(self):
        """Create bucket."""
        try:
            bucket = Bucket.create(
                storage_class=current_app.config[
                    'FILES_REST_DEFAULT_STORAGE_CLASS'
                ],
            )
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
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
        """Instantiate content negotiated view."""
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
    @need_bucket_permission('bucket-read')
    def head(self, bucket=None, **kwargs):
        """Check the existence of the bucket."""


class ObjectResource(ContentNegotiatedMethodView):
    """Object item resource."""

    delete_args = {
        'version_id': fields.UUID(
            location='query',
            load_from='versionId',
            data_key='versionId',
            missing=None,
        ),
        'upload_id': fields.UUID(
            location='query',
            load_from='uploadId',
            data_key='uploadId',
            missing=None,
        ),
        'uploads': fields.Raw(
            location='query',
            validate=invalid_subresource_validator,
        ),
    }

    get_args = dict(
        delete_args,
        download=fields.Raw(
            location='query',
            missing=None,
        )
    )

    post_args = {
        'uploads': fields.Raw(
            location='query',
        ),
        'upload_id': fields.UUID(
            location='query',
            load_from='uploadId',
            data_key='uploadId',
            missing=None,
        )
    }

    put_args = {
        'upload_id': fields.UUID(
            location='query',
            load_from='uploadId',
            data_key='uploadId',
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
            data_key='partSize',
        ),
    }

    def __init__(self, *args, **kwargs):
        """Instantiate content negotiated view."""
        super(ObjectResource, self).__init__(*args, **kwargs)

    #
    # ObjectVersion helpers
    #
    @staticmethod
    def check_object_permission(obj, file_access_permission=False):
        """Retrieve object and abort if it doesn't exists."""
        # Check for guest user (not login)
        # If not login => has permission
        if not file_access_permission:
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
        from invenio_records_files.models import RecordsBuckets
        from weko_records_ui.permissions import check_file_download_permission

        from invenio_files_rest.models import as_bucket_id

        # Get record metadata (table records_metadata) from bucket_id.
        bucket_id = as_bucket_id(bucket)
        rb = RecordsBuckets.query.filter_by(bucket_id=bucket_id).first()
        rm = RecordMetadata.query.filter_by(id=rb.record_id).first()
        # Check and file_access_permission of file in this record metadata.
        file_access_permission = False
        flag = False
        for k, v in rm.json.items():
            if isinstance(v, dict) and v.get('attribute_type') == 'file':
                for item in v.get('attribute_value_mlt', []):
                    is_this_version = item.get('version_id') == version_id
                    is_preview = item.get('displaytype') == 'preview'
                    if is_this_version and is_preview:
                        file_access_permission = \
                            check_file_download_permission(rm.json, item)
                        flag = True
                        break
            if flag:
                break
        # Get and check exists of current bucket info.
        obj = ObjectVersion.get(bucket, key, version_id=version_id)
        if not obj:
            abort(404, 'Object does not exists.')
        # Check permission. if it is not permission, return None.
        cls.check_object_permission(obj, file_access_permission)
        return obj

    def create_object(self, bucket, key,
                      is_thumbnail=None, replace_version_id=None):
        """Create a new object.

        :param bucket: The bucket (instance or id) to get the object from.
        :param key: The file key.
        :param is_thumbnail: for thumbnail.
        :returns: A Flask response.
        """
        # Initial validation of size based on Content-Length.
        # User can tamper with Content-Length, so this is just an initial up
        # front check. The storage subsystem must validate the size limit as
        # well.
        stream, content_length, content_md5, tags = \
            current_files_rest.upload_factory()

        size_limit = bucket.size_limit
        location_limit = bucket.location.max_file_size
        if location_limit is not None:
            size_limit = min(size_limit, location_limit)
        if content_length and size_limit and content_length > size_limit:
            desc = 'File size limit exceeded.' \
                if isinstance(size_limit, int) else size_limit.reason
            current_app.logger.error(desc)
            raise FileSizeError(description=desc)
        if not _location_has_quota(bucket, content_length):
            desc = 'Location has no quota'
            current_app.logger.error(desc)
            raise FileSizeError(description=desc)
        try:
            obj = ObjectVersion.create(bucket, key, is_thumbnail=is_thumbnail)
            obj.set_contents(
                stream, size=content_length, size_limit=size_limit,
                replace_version_id=replace_version_id)
            # Check add tags
            if tags:
                for key, value in tags.items():
                    ObjectVersionTag.create(obj, key, value)

            db.session.commit()
            opration = "FILE_CREATE" if not replace_version_id else "FILE_UPDATE"
            UserActivityLogger.info(
                operation=opration,
                target_key=key
            )
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            exec_info = sys.exc_info()
            tb_info = traceback.format_tb(exec_info[2])
            opration = "FILE_CREATE" if not replace_version_id else "FILE_UPDATE"
            UserActivityLogger.error(
                operation=opration,
                target_key=key,
                remarks=tb_info[0]
            )

        _response = self.make_response(
            data=obj,
            context={
                'class': ObjectVersion,
                'bucket': bucket,
            },
            etag=obj.file.checksum
        )
        if replace_version_id:
            _response.data = _response.data.replace(
                bytes('"key":"{}"'.format(_response.json['key']), 'utf-8'),
                bytes(
                    '"key":"'
                    + _response.json['key'] + '?replace_version_id='
                    + replace_version_id + '"',
                    'utf-8')
            )
        return _response

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
        try:
            file_key = obj.key if hasattr(obj, 'key') else None
            if version_id is None:
                # Create a delete marker.
                with db.session.begin_nested():
                    ObjectVersion.delete(bucket, obj.key)
            else:
                # Permanently delete specific object version.
                check_permission(
                    current_permission_factory(bucket, 'object-delete-version'),
                    hidden=False,
                )
                obj.remove()
                # Set newest object as head
                if obj.is_head:
                    obj_to_restore = \
                        ObjectVersion.get_versions(obj.bucket,
                                                obj.key,
                                                desc=True).first()
                    if obj_to_restore:
                        obj_to_restore.is_head = True

                if obj.file_id and not delete_file_instance(obj.file_id):
                    remove_file_data.delay(str(obj.file_id))

            db.session.commit()
            UserActivityLogger.info(
                operation="FILE_DELETE",
                target_key=file_key
            )
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            file_key = obj.key if hasattr(obj, 'key') else None
            exec_info = sys.exc_info()
            tb_info = traceback.format_tb(exec_info[2])
            UserActivityLogger.error(
                operation="FILE_DELETE",
                target_key=file_key,
                remarks=tb_info[0]
            )
        return self.make_response('', 204)

    @staticmethod
    def send_object(
            bucket,
            obj,
            expected_chksum=None,
            logger_data=None,
            restricted=True,
            as_attachment=False,
            is_preview=False,
            convert_to_pdf=False):
        """Send an object for a given bucket.

        :param is_preview: Determine the type of event.
            True: file-preview, False: file-download
        :param bucket: The bucket (instance or id) to get the object from.
        :param obj: A :class:`invenio_files_rest.models.ObjectVersion`
            instance.
        :params expected_chksum: Expected checksum.
        :param logger_data: The python logger.
        :param convert_to_pdf: Preview file convert to PDF flag.
        :param kwargs: Keyword arguments passed to ``Object.send_file()``
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

        if is_preview:
            allow_aggs = bool(request.args
                              and request.args.get('allow_aggs', '') == 'True')
            if allow_aggs:
                file_previewed.send(current_app._get_current_object(), obj=obj)
        else:
            file_downloaded.send(current_app._get_current_object(), obj=obj)
        return obj.send_file(restricted=restricted,
                             as_attachment=as_attachment,
                             convert_to_pdf=convert_to_pdf)

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
        try:
            multipart = MultipartObject.create(bucket, key, size, part_size)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
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
        content_length, part_number, stream, content_type, content_md5, tags =\
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
        try:
            multipart.complete()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)

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
        try:
            multipart.delete()
            db.session.commit()
            if multipart.file_id:
                remove_file_data.delay(str(multipart.file_id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
        return self.make_response('', 204)

    #
    # HTTP methods implementations
    #
    @use_kwargs(get_args)
    @pass_bucket
    def get(self, bucket=None, key=None, version_id=None, upload_id=None,
            uploads=None, download=None):
        """Get object or list parts of a multpart upload.

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
            # If 'download' is missing from query string it will have
            # the value None.
            return self.send_object(bucket, obj,
                                    as_attachment=download is not None)

    @use_kwargs(post_args)
    @pass_bucket
    @need_bucket_permission('bucket-update')
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
    @need_bucket_permission('bucket-update')
    def put(self, bucket=None, key=None, is_thumbnail=None, upload_id=None):
        """Update a new object or upload a part of a multipart upload.

        :param bucket: The bucket (instance or id) to get the object from.
            (Default: ``None``)
        :param key: The file key. (Default: ``None``)
        :param is_thumbnail: for thumbnail.
        :param upload_id: The upload ID. (Default: ``None``)
        :returns: A Flask response.
        """
        if upload_id is not None:
            return self.multipart_uploadpart(bucket, key, upload_id)
        else:
            is_thumbnail = True if is_thumbnail is not None else False
            replace_version_id = request.args.get('replace_version_id')
            return self.create_object(bucket, key, is_thumbnail=is_thumbnail,
                                      replace_version_id=replace_version_id)

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


class LocationUsageAmountInfo(ContentNegotiatedMethodView):
    """REST API resource providing location usage amount."""

    def __init__(self, *args, **kwargs):
        """Instatiate content negotiated view."""
        super(LocationUsageAmountInfo, self).__init__(*args, **kwargs)

    def get(self, **kwargs):
        """Get location usage amount."""
        result = []

        locations = Location.query.order_by(Location.name.asc()).all()
        for location in locations:
            data = {}
            data['name'] = location.name
            data['default'] = location.default
            data['size'] = location.size
            data['quota_size'] = location.quota_size
            # number of registered files
            buckets = Bucket.query.with_entities(
                Bucket.id).filter_by(location=location)
            data['files'] = ObjectVersion.query.filter(
                ObjectVersion.bucket_id.in_(buckets.subquery())).count()

            result.append(data)

        return jsonify(result)


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
object_thumbnail_view = ObjectResource.as_view(
    'object_thumbnail_api',
    serializers={
        'application/json': json_serializer,
    }
)
location_usage_amount = LocationUsageAmountInfo.as_view(
    'location_usage_amount_info',
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
blueprint.add_url_rule(
    '/<string:is_thumbnail>/<string:bucket_id>/<path:key>',
    view_func=object_thumbnail_view,
)
api_blueprint.add_url_rule(
    '/locations',
    view_func=location_usage_amount,
)


@blueprint.teardown_request
@admin_blueprint.teardown_request
@api_blueprint.teardown_request
def dbsession_clean(exception):
    current_app.logger.debug("invenio_files_rest dbsession_clean: {}".format(exception))
    if exception is None:
        try:
            db.session.commit()
        except:
            db.session.rollback()
    db.session.remove()