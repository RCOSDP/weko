import datetime
import uuid
from urllib.parse import urlparse

import math
from flask import current_app
from marshmallow import Schema
from marshmallow import ValidationError, fields, post_load, validates, validates_schema
from marshmallow import validate
from marshmallow.validate import Range
from werkzeug.exceptions import HTTPException

from sword3common.constants import JSON_LD_CONTEXT, PackagingFormat

__all__ = ["ByReferenceSchema"]


class ByReferenceFileDefinition:
    def __init__(
        self,
        *,
        url: str = None,
        temporary_id: uuid.UUID = None,
        content_disposition: str,
        content_type: str,
        content_length: int = None,
        dereference: bool,
        packaging: str,
        ttl: datetime.datetime = None
    ):
        assert url or temporary_id
        self.url = url
        self.temporary_id = temporary_id
        self.content_disposition = content_disposition
        self.content_type = content_type
        self.content_length = content_length
        self.dereference = dereference
        self.packaging = packaging
        self.ttl = ttl


class _ByReferenceFileSchema(Schema):
    url = fields.Url(data_key="@id", required=True)
    content_disposition = fields.String(data_key="contentDisposition", required=True)
    content_length = fields.Integer(data_key="contentLength", strict=True)
    content_type = fields.String(data_key="contentType", required=True)
    dereference = fields.Boolean(required=True)
    packaging = fields.String(missing=PackagingFormat.Binary)
    ttl = fields.AwareDateTime()

    @validates_schema
    def validate_url(self, data, **kwargs):
        parsed_url = urlparse(data["url"])
        if parsed_url.hostname == self.context["url_adapter"].server_name:
            try:
                rule, rv = self.context["url_adapter"].match(parsed_url.path)
            except HTTPException:
                return None
            if rule == "invenio_sword.temporary_url":
                data["temporary_id"] = rv["temporary_id"]
                del data["url"]

    @post_load
    def make_object(self, data, **kwargs):
        return ByReferenceFileDefinition(**data)


class ByReferenceSchema(Schema):
    jsonld_context = fields.String(
        data_key="@context",
        validate=[validate.OneOf([JSON_LD_CONTEXT])],
        required=True,
    )
    jsonld_type = fields.String(
        data_key="@type", validate=[validate.OneOf(["ByReference"])], required=True,
    )
    files = fields.List(
        fields.Nested(_ByReferenceFileSchema),
        data_key="byReferenceFiles",
        required=True,
    )


class SegmentInitSchema(Schema):
    """For validating parameters on `Content-Disposition: segment-init` headers"""

    # validate parameters are lambdas to defer accessing current_app until we're inside the application context

    size = fields.Integer(
        required=True,
        validate=lambda value: Range(
            current_app.config["FILES_REST_MULTIPART_MAX_PARTS"]
        ),
    )
    segment_count = fields.Integer(
        required=True,
        validate=lambda value: Range(
            1, current_app.config["FILES_REST_MULTIPART_MAX_PARTS"]
        ),
    )
    segment_size = fields.Integer(
        required=True,
        validate=lambda value: Range(
            current_app.config["FILES_REST_MULTIPART_CHUNKSIZE_MIN"],
            current_app.config["FILES_REST_MULTIPART_CHUNKSIZE_MAX"],
        )(value),
    )

    @validates_schema
    def validate_segment_count(self, data, **kwargs):
        if data["segment_count"] != math.ceil(data["size"] / data["segment_size"]):
            raise ValidationError(
                {
                    "segment_count": "Wrong number of segments for given size and segment_size."
                }
            )


class SegmentUploadSchema(Schema):
    segment_number = fields.Integer(required=True)

    def __init__(self, *args, segment_count, **kwargs):
        self._segment_count = segment_count
        super().__init__(*args, **kwargs)

    @validates("segment_number")
    def validate_segment_number(self, value):
        return Range(1, self._segment_count)(value)
