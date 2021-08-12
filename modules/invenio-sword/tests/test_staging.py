import datetime
import io
import json
import uuid
from http import HTTPStatus

import pytest

from helpers import login
from invenio_files_rest.models import MultipartObject, Part, ObjectVersion
from invenio_records.models import RecordMetadata
from invenio_sword import tasks
from invenio_sword.api import SegmentedUploadRecord, SWORDDeposit
from invenio_sword.enum import ObjectTagKey, FileState
from invenio_sword.schemas import ByReferenceFileDefinition
from invenio_sword.utils import TagManager
from sword3common.constants import JSON_LD_CONTEXT, PackagingFormat


def test_start_segmented_unauthenticated(api):
    with api.test_request_context(), api.test_client() as client:
        response = client.post(
            "/sword/staging",
            headers={
                "Content-Disposition": "segment-init; segment_count=2; segment_size=1000000; size=2000000",
            },
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_start_without_content_disposition(api, users):
    with api.test_request_context(), api.test_client() as client:
        login(client)
        response = client.post("/sword/staging",)
        assert response.status_code == HTTPStatus.BAD_REQUEST


def test_start_segmented_small_segment(api, users):
    with api.test_request_context(), api.test_client() as client:
        login(client)
        response = client.post(
            "/sword/staging",
            headers={
                "Content-Disposition": "segment-init; segment_count=2; segment_size=1; size=2",
            },
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert "segment_size" in response.json["errors"]


def test_start_segmented(api, location, users):
    with api.test_request_context(), api.test_client() as client:
        login(client)
        response = client.post(
            "/sword/staging",
            headers={
                "Content-Disposition": "segment-init; segment_count=2; segment_size=10000000; size=20000000",
            },
        )
        assert response.status_code == HTTPStatus.CREATED
        assert "Location" in response.headers

        record_metadata = RecordMetadata.query.one()
        record = SegmentedUploadRecord(record_metadata.json, model=record_metadata)

        response = client.get(response.headers["Location"])
        assert response.json == {
            "@context": JSON_LD_CONTEXT,
            "@id": "http://localhost/sword/staging/" + str(record.id),
            "@type": "Temporary",
            "segments": {
                "received": [],
                "expecting": [1, 2],
                "size": 20000000,
                "segment_size": 10000000,
            },
        }


def test_access_someone_elses_segmented_upload(api, users, location):
    with api.test_request_context(), api.test_client() as client:
        login(client, **users[0])
        response = client.post(
            "/sword/staging",
            headers={
                "Content-Disposition": "segment-init; segment_count=2; segment_size=10000000; size=20000000",
            },
        )
        assert response.status_code == HTTPStatus.CREATED
        assert "Location" in response.headers

        # record_metadata = RecordMetadata.query.one()
        # record = SegmentedUploadRecord(record_metadata.json, model=record_metadata)

    with api.test_request_context(), api.test_client() as client:
        login(client, **users[1])
        response = client.get(response.headers["Location"])
        assert response.status_code == HTTPStatus.FORBIDDEN
        assert response.json["@type"] == "AuthenticationFailed"


def test_access_unknown_segmented_upload(api, users, location):
    with api.test_request_context(), api.test_client() as client:
        login(client)
        response = client.get("/sword/staging/" + str(uuid.uuid4()))
        assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.parametrize(
    "content_disposition",
    [
        "segment; segment_index=1",  # incorrect parameter name
        "",  # missing entirely
        "netgems; segment_number=1",  # wrong disposition type
    ],
)
def test_upload_with_wrong_content_disposition(
    api, users, location, content_disposition
):
    with api.test_request_context(), api.test_client() as client:
        login(client)
        init_response = client.post(
            "/sword/staging",
            headers={
                "Content-Disposition": f"segment-init; segment_count=2; segment_size=10; size=15",
            },
        )
        assert init_response.status_code == HTTPStatus.CREATED

        response = client.post(
            init_response.headers["Location"],
            headers={"Content-Disposition": content_disposition},
            data=b"1234567890",
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.parametrize(
    "segment_count,segment_size,size",
    [
        (2, 12, 24),  # segments all the same size
        (3, 10, 26),  # differently-sized final segment
        (2, 10, 19),  # check for off-by-one errors
        (2, 10, 20),  # check for off-by-one errors
        (3, 10, 21),  # check for off-by-one errors
    ],
)
def test_upload_segments(api, users, location, segment_count, segment_size, size):
    # e.g. b'ABC...XYZ'
    data = bytes(65 + i for i in range(size))

    with api.test_request_context(), api.test_client() as client:
        login(client)
        init_response = client.post(
            "/sword/staging",
            headers={
                "Content-Disposition": f"segment-init; segment_count={segment_count}; segment_size={segment_size}; size={size}",
            },
        )
        assert init_response.status_code == HTTPStatus.CREATED
        assert "Location" in init_response.headers

        segment_number = 0
        for i in range(0, size, segment_size):
            # Haven't yet finished the upload
            multipart_object: MultipartObject = MultipartObject.query.one()
            assert multipart_object.completed is False

            segment_number += 1
            response = client.post(
                init_response.headers["Location"],
                headers={
                    "Content-Disposition": f"segment; segment_number={segment_number}",
                },
                data=data[i : i + segment_size],
            )
            assert response.status_code == HTTPStatus.NO_CONTENT

        # Check that the test code got the number of segments right.
        assert segment_number == segment_count

        # MultipartObject has been marked complete
        multipart_object: MultipartObject = MultipartObject.query.one()
        assert multipart_object.completed is True


@pytest.mark.parametrize(
    "segment_number,segment_size",
    [
        (1, 8),  # too short
        (1, 12),  # too long
        (2, 3),  # too short final segment
        (2, 7),  # too long final segment
        (2, 10),  # also too long final segment, but the otherwise usual size
    ],
)
def test_upload_wrong_segment_size(api, users, location, segment_number, segment_size):
    with api.test_request_context(), api.test_client() as client:
        login(client)
        init_response = client.post(
            "/sword/staging",
            headers={
                "Content-Disposition": f"segment-init; segment_count=2; segment_size=10; size=15",
            },
        )
        assert init_response.status_code == HTTPStatus.CREATED
        assert "Location" in init_response.headers

        response = client.post(
            init_response.headers["Location"],
            headers={
                "Content-Disposition": f"segment; segment_number={segment_number}",
            },
            data=bytes(65 + i for i in range(segment_size)),
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.json["@type"] == "InvalidSegmentSize"


def test_delete_segmented_upload(api, users, location):
    with api.test_request_context(), api.test_client() as client:
        login(client)

        # Create a segmented upload
        init_response = client.post(
            "/sword/staging",
            headers={
                "Content-Disposition": f"segment-init; segment_count=2; segment_size=10; size=15",
            },
        )
        assert init_response.status_code == HTTPStatus.CREATED
        assert "Location" in init_response.headers

        # Upload a single segment
        response = client.post(
            init_response.headers["Location"],
            headers={"Content-Disposition": f"segment; segment_number=1",},
            data=b"1234567890",
        )

        # Delete the whole thing
        response = client.delete(init_response.headers["Location"],)
        assert response.status_code == HTTPStatus.NO_CONTENT

        assert MultipartObject.query.count() == 0
        assert Part.query.count() == 0


def test_post_by_reference_segmented(api, users, location, task_delay):
    with api.test_request_context(), api.test_client() as client:
        # Assemble a segmented upload from parts, and complete it
        segmented_upload_record: SegmentedUploadRecord = SegmentedUploadRecord.create(
            {}
        )
        multipart_object = MultipartObject.create(
            bucket=segmented_upload_record.bucket,
            key="some-key",
            size=15,
            chunk_size=10,
        )
        Part.create(multipart_object, 0, stream=io.BytesIO(b"abcdefghij"))
        Part.create(multipart_object, 1, stream=io.BytesIO(b"klmno"))
        multipart_object.complete()

        login(client)

        ttl = (
            datetime.datetime.now(tz=datetime.timezone.utc)
            + datetime.timedelta(0, 3600)
        ).isoformat()

        response = client.post(
            "/sword/service-document",
            data=json.dumps(
                {
                    "@context": JSON_LD_CONTEXT,
                    "@type": "ByReference",
                    "byReferenceFiles": [
                        {
                            "@id": f"http://localhost/sword/staging/{segmented_upload_record.id}",
                            "contentDisposition": "attachment; filename=some-resource.json",
                            "contentType": "application/json",
                            "dereference": True,
                            "ttl": ttl,
                        }
                    ],
                }
            ),
            headers={
                "Content-Disposition": "attachment; by-reference=true",
                "Content-Type": "application/ld+json",
            },
        )

        assert response.status_code == HTTPStatus.CREATED

        object_version = ObjectVersion.query.one()
        tags = TagManager(object_version)

        assert tags == {
            ObjectTagKey.Packaging: "http://purl.org/net/sword/3.0/package/Binary",
            ObjectTagKey.ByReferenceTemporaryID: str(segmented_upload_record.id),
            ObjectTagKey.FileState: FileState.Pending,
            ObjectTagKey.ByReferenceDereference: "true",
            ObjectTagKey.ByReferenceNotDeleted: "true",
            ObjectTagKey.OriginalDeposit: "true",
            ObjectTagKey.ByReferenceTTL: ttl,
        }


def test_by_reference_sets_tag(api, users, location, task_delay):
    with api.test_request_context():
        # Assemble a segmented upload from parts, and complete it
        segmented_upload_record: SegmentedUploadRecord = SegmentedUploadRecord.create(
            {}
        )
        multipart_object = MultipartObject.create(
            bucket=segmented_upload_record.bucket,
            key="some-key",
            size=15,
            chunk_size=10,
        )
        Part.create(multipart_object, 0, stream=io.BytesIO(b"abcdefghij"))
        Part.create(multipart_object, 1, stream=io.BytesIO(b"klmno"))
        multipart_object.complete()

        record: SWORDDeposit = SWORDDeposit.create({})
        record.set_by_reference_files(
            [
                ByReferenceFileDefinition(
                    temporary_id=segmented_upload_record.id,
                    content_disposition="attachment; filename=something.txt",
                    content_type="text/plain",
                    packaging=PackagingFormat.Binary,
                    dereference=True,
                ),
            ],
            lambda *args: True,
            "http://localhost/",
        )

        object_version = ObjectVersion.query.one()
        tags = TagManager(object_version)

        assert tags == {
            ObjectTagKey.OriginalDeposit: "true",
            ObjectTagKey.ByReferenceTemporaryID: str(segmented_upload_record.id),
            ObjectTagKey.Packaging: "http://purl.org/net/sword/3.0/package/Binary",
            ObjectTagKey.FileState: FileState.Pending,
            ObjectTagKey.ByReferenceDereference: "true",
            ObjectTagKey.ByReferenceNotDeleted: "true",
        }

        tasks.dereference_object(record.id, object_version.version_id)

        assert object_version.file.storage().open().read() == b"abcdefghijklmno"


def test_dereference_missing_upload(api, users, location, task_delay):
    with api.test_request_context():
        # Assemble a segmented upload from parts, and complete it
        segmented_upload_record: SegmentedUploadRecord = SegmentedUploadRecord.create(
            {}
        )
        MultipartObject.create(
            bucket=segmented_upload_record.bucket,
            key="some-key",
            size=15,
            chunk_size=10,
        )

        record: SWORDDeposit = SWORDDeposit.create({})
        record.set_by_reference_files(
            [
                ByReferenceFileDefinition(
                    temporary_id=segmented_upload_record.id,
                    content_disposition="attachment; filename=something.txt",
                    content_type="text/plain",
                    packaging=PackagingFormat.Binary,
                    dereference=True,
                ),
            ],
            lambda *args: True,
            "http://localhost/",
        )

        object_version = ObjectVersion.query.one()

        with pytest.raises(ValueError):
            tasks.dereference_object(record.id, object_version.version_id)

        assert TagManager(object_version)[ObjectTagKey.FileState] == FileState.Error
