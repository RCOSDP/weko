# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""REST API serializers."""

import json
from time import sleep

from flask import current_app, request, url_for
from invenio_rest.serializer import BaseSchema as InvenioRestBaseSchema
from marshmallow import fields, missing, post_dump

from .errors import FilesException
from .models import Bucket, MultipartObject, ObjectVersion, Part


class BaseSchema(InvenioRestBaseSchema):
    """Base schema for all serializations."""

    created = fields.DateTime(dump_only=True)
    updated = fields.DateTime(dump_only=True)
    links = fields.Method("dump_links", dump_only=True)

    def dump_links(self, o):
        """Get base links."""
        return missing


class BucketSchema(BaseSchema):
    """Schema for bucket."""

    id = fields.UUID()
    size = fields.Integer()
    quota_size = fields.Integer()
    max_file_size = fields.Integer()
    locked = fields.Boolean()

    def dump_links(self, o):
        """Dump links."""
        return {
            "self": url_for(".bucket_api", bucket_id=o.id, _external=True),
            "versions": url_for(".bucket_api", bucket_id=o.id, _external=True)
            + "?versions",
            "uploads": url_for(".bucket_api", bucket_id=o.id, _external=True)
            + "?uploads",
        }


class ObjectVersionSchema(BaseSchema):
    """Schema for ObjectVersions."""

    key = fields.Str()
    version_id = fields.UUID()
    is_head = fields.Boolean()
    mimetype = fields.Str()
    size = fields.Integer(attribute="file.size")
    checksum = fields.String(attribute="file.checksum")
    delete_marker = fields.Boolean(attribute="deleted")
    tags = fields.Method("dump_tags", dump_only=True)

    def dump_tags(self, o):
        """Dump tags."""
        return o.get_tags()

    def dump_links(self, o):
        """Dump links."""
        params = {"versionId": o.version_id}
        data = {
            "self": url_for(
                ".object_api",
                bucket_id=o.bucket_id,
                key=o.key,
                _external=True,
                **(params if not o.is_head or o.deleted else {})
            ),
            "version": url_for(
                ".object_api",
                bucket_id=o.bucket_id,
                key=o.key,
                _external=True,
                **params
            ),
        }

        if o.is_head and not o.deleted:
            data.update(
                {
                    "uploads": url_for(
                        ".object_api", bucket_id=o.bucket_id, key=o.key, _external=True
                    )
                    + "?uploads",
                }
            )

        return data

    @post_dump(pass_many=True)
    def wrap(self, data, many):
        """Wrap response in envelope."""
        if not many:
            return data
        else:
            data = {"contents": data}
            bucket = self.context.get("bucket")
            if bucket:
                data.update(BucketSchema().dump(bucket).data)
            return data


class MultipartObjectSchema(BaseSchema):
    """Schema for ObjectVersions."""

    _endpoint = ".object_api"

    id = fields.UUID(attribute="upload_id", dump_only=True)
    bucket = fields.UUID(attribute="bucket_id", dump_only=True)
    key = fields.Str(dump_only=True)
    completed = fields.Boolean(dump_only=True)
    size = fields.Integer()
    part_size = fields.Integer(attribute="chunk_size")
    last_part_number = fields.Integer(dump_only=True)
    last_part_size = fields.Integer(dump_only=True)

    def dump_links(self, o):
        """Dump links."""
        links = {
            "self": url_for(
                ".object_api",
                bucket_id=o.bucket_id,
                key=o.key,
                uploadId=o.upload_id,
                _external=True,
            ),
            "object": url_for(
                ".object_api",
                bucket_id=o.bucket_id,
                key=o.key,
                _external=True,
            ),
        }

        version_id = self.context.get("object_version_id")
        if version_id:
            links.update(
                {
                    "object_version": url_for(
                        ".object_api",
                        bucket_id=o.bucket_id,
                        key=o.key,
                        versionId=version_id,
                        _external=True,
                    )
                }
            )

        bucket = self.context.get("bucket")
        if bucket:
            links.update(
                {
                    "bucket": url_for(
                        ".bucket_api",
                        bucket_id=o.bucket_id,
                        _external=True,
                    )
                }
            )

        return links


class PartSchema(BaseSchema):
    """Schema for parts."""

    part_number = fields.Integer()
    start_byte = fields.Integer()
    end_byte = fields.Integer()
    checksum = fields.Str()

    links = None

    @post_dump(pass_many=True)
    def wrap(self, data, many):
        """Wrap response in envelope."""
        if not many:
            return data
        else:
            data = {"parts": data}
            multipart = self.context.get("multipart")
            if multipart:
                data.update(
                    MultipartObjectSchema(context={"bucket": multipart.bucket})
                    .dump(multipart)
                    .data
                )
            return data


serializer_mapping = {
    Bucket: BucketSchema,
    ObjectVersion: ObjectVersionSchema,
    MultipartObject: MultipartObjectSchema,
    Part: PartSchema,
}


def schema_from_context(context, serializer_mapping):
    """Determine which schema to use."""
    item_class = context.get("class")
    return (
        serializer_mapping[item_class] if item_class else BaseSchema,
        context.get("many", False),
    )


def _format_args():
    if request and request.args.get("prettyprint"):
        return dict(
            indent=2,
            separators=(", ", ": "),
        )
    else:
        return dict(
            indent=None,
            separators=(",", ":"),
        )


def wait_for_taskresult(task_result, content, interval, max_rounds):
    """Get helper to wait for async task result to finish.

    The task will periodically send whitespace to prevent the connection from
    being closed.

    :param task_result: The async task to wait for.
    :param content: The content to return when the task is ready.
    :param interval: The duration of a sleep period before check again if the
        task is ready.
    :param max_rounds: The maximum number of intervals the function check
        before returning an Exception.
    :returns: An iterator on the content or a
        :class:`invenio_files_rest.errors.FilesException` exception if the
        timeout happened or the job failed.
    """
    assert max_rounds > 0

    def _whitespace_waiting():
        current = 0
        while current < max_rounds and current != -1:
            if task_result.ready():
                # Task is done and we return
                current = -1
                if task_result.successful():
                    yield content
                else:
                    yield FilesException(description="Job failed.").get_body()
            else:
                # Send whitespace to prevent connection from closing.
                current += 1
                sleep(interval)
                yield b" "

        # Timed-out reached
        if current == max_rounds:
            yield FilesException(description="Job timed out.").get_body()

    return _whitespace_waiting()


def json_serializer(
    data=None,
    code=200,
    headers=None,
    context=None,
    etag=None,
    task_result=None,
    serializer_mapping=serializer_mapping,
    view_name=None,
):
    """Build a json flask response using the given data.

    :param data: The data to serialize. (Default: ``None``)
    :param code: The HTTP status code. (Default: ``200``)
    :param headers: The HTTP headers to include. (Default: ``None``)
    :param context: The schema class context. (Default: ``None``)
    :param etag: The ETag header. (Default: ``None``)
    :param task_result: Optionally you can pass async task to wait for.
        (Default: ``None``)
    :param serializer_mapping: Optionally provide the serializer with a
        different mapping.
    :param view_name: Optionally push to the marshmallow context the view
        name prefix,usefull in case of multiple routes pointing to the same
        blueprint.
    :returns: A Flask response with json data.
    :rtype: :py:class:`flask.Response`
    """
    context = context or {}
    if view_name:
        context.update({"view_name": view_name})
    schema_class, many = schema_from_context(context, serializer_mapping)

    if data is not None:
        # Generate JSON response
        data = json.dumps(
            schema_class(context=context).dump(data, many=many).data, **_format_args()
        )

        interval = current_app.config["FILES_REST_TASK_WAIT_INTERVAL"]
        max_rounds = int(
            current_app.config["FILES_REST_TASK_WAIT_MAX_SECONDS"] // interval
        )

        response = current_app.response_class(
            # Stream response if waiting for task result.
            data
            if task_result is None
            else wait_for_taskresult(
                task_result,
                data,
                interval,
                max_rounds,
            ),
            mimetype="application/json",
        )
    else:
        response = current_app.response_class(mimetype="application/json")

    response.status_code = code
    if headers is not None:
        response.headers.extend(headers)

    if etag:
        response.set_etag(etag)

    return response
