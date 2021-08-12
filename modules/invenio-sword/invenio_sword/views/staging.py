"""
Segmented file upload support

See <https://swordapp.github.io/swordv3/swordv3.html#9.7.>.
"""
import datetime

import math
from http import HTTPStatus

from flask_login import current_user
from invenio_db import db
from sqlalchemy.orm.exc import NoResultFound

import sword3common.exceptions
from flask import request, url_for, Response
from werkzeug.http import parse_options_header

from invenio_files_rest.errors import MultipartMissingParts, UnexpectedFileSizeError
from invenio_files_rest.models import MultipartObject, Part
from invenio_records_rest.views import need_record_permission
from invenio_sword.api import SegmentedUploadRecord

from invenio_sword.schemas import SegmentInitSchema, SegmentUploadSchema
from invenio_sword.views import SWORDDepositView


__all__ = ["StagingURLView", "TemporaryURLView"]


class SegmentedUploadView(SWORDDepositView):
    record_class = SegmentedUploadRecord


class StagingURLView(SegmentedUploadView):
    """POST to this to start a segmented file upload and create a temporary URL"""

    view_name = "staging_url"

    @need_record_permission("create_permission_factory")
    def post(self, **kwargs):
        content_disposition, content_disposition_options = parse_options_header(
            request.headers.get("Content-Disposition", "")
        )
        if content_disposition != "segment-init":
            raise sword3common.exceptions.BadRequest(
                "Content-Disposition must be 'segment-init'"
            )
        parsed_content_disposition_options = SegmentInitSchema().load(
            content_disposition_options
        )

        record: SegmentedUploadRecord = SegmentedUploadRecord.create(
            {"_segmentedUpload": {"owners": [int(current_user.get_id())],}}
        )
        MultipartObject.create(
            bucket=record.bucket,
            key=str(record.id),
            size=parsed_content_disposition_options["size"],
            chunk_size=parsed_content_disposition_options["segment_size"],
        )

        response = Response(status=HTTPStatus.CREATED)
        response.headers["Location"] = url_for(
            "invenio_sword.temporary_url", temporary_id=record.id, _external=True,
        )
        db.session.commit()
        return response


class TemporaryURLView(SegmentedUploadView):
    """Upload file segments here"""

    view_name = "temporary_url"
    record_class = SegmentedUploadRecord

    def dispatch_request(self, temporary_id, *args, **kwargs):
        try:
            record = SegmentedUploadRecord.get_record(temporary_id)
        except NoResultFound as e:
            raise sword3common.exceptions.NotFound from e
        if int(current_user.get_id()) not in record["_segmentedUpload"]["owners"]:
            raise sword3common.exceptions.SwordException.for_status_code_and_name(
                HTTPStatus.FORBIDDEN, None
            )
        multipart_object: MultipartObject = MultipartObject.query.filter_by(
            bucket_id=record.bucket_id,
        ).one()
        return super().dispatch_request(
            record=record, multipart_object=multipart_object, *args, **kwargs
        )

    def get(self, *, record: SegmentedUploadRecord, multipart_object: MultipartObject):
        part_numbers = set(
            db.session.query(Part.part_number).filter_by(
                upload_id=multipart_object.upload_id
            )
        )

        segment_count = math.ceil(multipart_object.size / multipart_object.chunk_size)

        return {
            "@type": "Temporary",
            "segments": {
                "received": sorted(part_numbers),
                "expecting": [
                    i for i in range(1, segment_count + 1) if i not in part_numbers
                ],
                "size": multipart_object.size,
                "segment_size": multipart_object.chunk_size,
            },
        }

    def post(self, *, record: SegmentedUploadRecord, multipart_object: MultipartObject):
        content_disposition, content_disposition_options = parse_options_header(
            request.headers.get("Content-Disposition", "")
        )
        if content_disposition != "segment":
            raise sword3common.exceptions.BadRequest(
                "Content-Disposition must be 'segment'"
            )
        parsed_content_disposition_options = SegmentUploadSchema(
            segment_count=multipart_object.last_part_number + 1
        ).load(content_disposition_options)

        try:
            Part.create(
                multipart_object,
                # SWORD segment_numbers are indexed from 1, whereas invenio part numbers are indexed from 0
                parsed_content_disposition_options["segment_number"] - 1,
                request.stream,
            )
        except UnexpectedFileSizeError as e:
            raise sword3common.exceptions.InvalidSegmentSize(e.description) from e

        # Attempt to mark it complete, as a segmented upload is complete as soon as the last part is uploaded, and
        # this method does that check for us
        try:
            multipart_object.complete()
        except MultipartMissingParts:
            pass

        multipart_object.updated = datetime.datetime.utcnow()
        db.session.add(multipart_object)

        db.session.commit()
        return Response(status=HTTPStatus.NO_CONTENT)

    def delete(
        self, *, record: SegmentedUploadRecord, multipart_object: MultipartObject
    ):
        multipart_object.delete()
        db.session.commit()
        return Response(status=HTTPStatus.NO_CONTENT)
