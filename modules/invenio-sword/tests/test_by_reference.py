import io
import json
import unittest.mock
import urllib.error
import uuid
from http import HTTPStatus

import pytest
import pytest_httpserver
from flask_security import url_for_security
from invenio_db import db
from invenio_files_rest.models import Bucket
from invenio_files_rest.models import ObjectVersion
from invenio_records.models import RecordMetadata
from invenio_sword.schemas import ByReferenceSchema
from sword3common.constants import JSON_LD_CONTEXT
from sword3common.constants import PackagingFormat
from sword3common.exceptions import ContentTypeNotAcceptable

from invenio_sword import tasks
from invenio_sword.api import SWORDDeposit
from invenio_sword.enum import FileState
from invenio_sword.enum import ObjectTagKey
from invenio_sword.utils import TagManager


@pytest.mark.parametrize(
    "data,fields_with_errors, fields_without_errors",
    [
        # Missing fields
        ({}, ["@context", "@type", "byReferenceFiles"], []),
        # Wrong @context value
        ({"@context": "http://example.com/"}, ["@context"], []),
        # Correct @context value
        ({"@context": JSON_LD_CONTEXT}, [], ["@context"]),
        # Wrong @type value
        ({"@type": "Metadata"}, ["@type"], []),
        # Correct @type value
        ({"@type": "ByReference"}, [], ["@type"]),
        # Missing fields in byReferenceFiles
        ({"byReferenceFiles": [{}]}, ["byReferenceFiles"], []),
    ],
)
def test_by_reference_validation(
    api, users, location, es, data, fields_with_errors, fields_without_errors
):
    with api.test_request_context(), api.test_client() as client:
        client.post(
            url_for_security("login"),
            data={"email": users[0]["email"], "password": "tester"},
        )

        response = client.post(
            "/sword/service-document",
            data=json.dumps(data),
            headers={
                "Content-Disposition": "attachment; by-reference=true",
                "Content-Type": "application/ld+json",
            },
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.is_json
        assert response.json["@type"] == "ValidationFailed"
        # The fields with errors are the superset of the ones we expected; i.e. it shouldn't accept data we
        # in this test know is wrong
        print(response.json)
        assert set(response.json["errors"]) >= set(fields_with_errors)
        # We know these fields to be good
        assert not (set(response.json["errors"]) & set(fields_without_errors))


def test_by_reference_deposit(
    api,
    users,
    location,
    es,
    httpserver: pytest_httpserver.HTTPServer,
    task_delay: unittest.mock.Mock,
):
    with api.test_request_context(), api.test_client() as client:
        client.post(
            url_for_security("login"),
            data={"email": users[0]["email"], "password": "tester"},
        )

        response = client.post(
            "/sword/service-document",
            data=json.dumps(
                {
                    "@context": JSON_LD_CONTEXT,
                    "@type": "ByReference",
                    "byReferenceFiles": [
                        {
                            "@id": httpserver.url_for("some-resource.json"),
                            "contentDisposition": "attachment; filename=some-resource.json",
                            "contentType": "application/json",
                            "dereference": True,
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
        assert response.is_json

        bucket = Bucket.query.one()
        object_version: ObjectVersion = ObjectVersion.query.filter(
            ObjectVersion.bucket == bucket
        ).one()

        record_metadata = RecordMetadata.query.one()

        assert task_delay.call_args_list == (
            [
                unittest.mock.call(
                    tasks.dereference_object.s(
                        str(record_metadata.id), str(object_version.version_id)
                    )
                    | tasks.unpack_object.si(
                        str(record_metadata.id), str(object_version.version_id)
                    )
                )
            ]
        )

        # Ensure that no requests were made
        assert httpserver.log == []


def test_by_reference_and_metadata_deposit(
    api,
    users,
    location,
    es,
    httpserver: pytest_httpserver.HTTPServer,
    task_delay: unittest.mock.Mock,
):
    with api.test_request_context(), api.test_client() as client:
        client.post(
            url_for_security("login"),
            data={"email": users[0]["email"], "password": "tester"},
        )

        response = client.post(
            "/sword/service-document",
            data=json.dumps(
                {
                    "metadata": {
                        "@context": JSON_LD_CONTEXT,
                        "@type": "Metadata",
                        "dc:title": "Some data",
                    },
                    "by-reference": {
                        "@context": JSON_LD_CONTEXT,
                        "@type": "ByReference",
                        "byReferenceFiles": [
                            {
                                "@id": httpserver.url_for("some-resource.json"),
                                "contentDisposition": "attachment; filename=some-resource.json",
                                "contentType": "application/json",
                                "dereference": True,
                            }
                        ],
                    },
                }
            ),
            headers={
                "Content-Disposition": "attachment; by-reference=true; metadata=true",
                "Content-Type": "application/ld+json",
            },
        )
        assert response.status_code == HTTPStatus.CREATED
        assert response.is_json

        bucket = Bucket.query.one()
        object_version: ObjectVersion = ObjectVersion.query.filter(
            ObjectVersion.bucket == bucket, ObjectVersion.key == "some-resource.json",
        ).one()

        record_metadata = RecordMetadata.query.one()

        assert record_metadata.json["metadata"] == {
            "title_statement": {"title": "Some data"}
        }

        assert task_delay.call_args_list == (
            [
                unittest.mock.call(
                    tasks.dereference_object.s(
                        str(record_metadata.id), str(object_version.version_id)
                    )
                    | tasks.unpack_object.si(
                        str(record_metadata.id), str(object_version.version_id)
                    )
                )
            ]
        )

        # Ensure that no requests were made
        assert httpserver.log == []


def test_dereference_task(
    api, users, location, es, httpserver: pytest_httpserver.HTTPServer
):
    file_contents = "File contents.\n"

    with api.test_request_context():
        record = SWORDDeposit.create({})
        object_version = ObjectVersion.create(bucket=record.bucket, key="some-file.txt")
        TagManager(object_version).update(
            {
                ObjectTagKey.ByReferenceURL: httpserver.url_for("some-file.txt"),
                # This one should get removed after dereferencing
                ObjectTagKey.ByReferenceNotDeleted: "true",
                ObjectTagKey.Packaging: PackagingFormat.SimpleZip,
            }
        )

        httpserver.expect_request("/some-file.txt").respond_with_data(file_contents)

        db.session.refresh(object_version)
        tasks.dereference_object(record.id, object_version.version_id)

        # Check requests
        assert len(httpserver.log) == 1
        assert httpserver.log[0][0].path == "/some-file.txt"

        db.session.refresh(object_version)
        assert object_version.file is not None
        assert object_version.file.storage().open().read() == file_contents.encode(
            "utf-8"
        )

        assert TagManager(object_version) == {
            ObjectTagKey.ByReferenceURL: httpserver.url_for("some-file.txt"),
            ObjectTagKey.Packaging: PackagingFormat.SimpleZip,
            ObjectTagKey.FileState: FileState.Pending,
        }


def test_dereference_without_url(api, location, es):
    with api.test_request_context():
        record = SWORDDeposit.create({})

        object_version = ObjectVersion.create(bucket=record.bucket, key="some-file.txt")
        with pytest.raises(ValueError):
            tasks.dereference_object(record.id, object_version.version_id)


def test_dereference_already_dereferenced(
    api, location, es, httpserver: pytest_httpserver.HTTPServer
):
    with api.test_request_context():
        record = SWORDDeposit.create({})

        object_version = ObjectVersion.create(
            bucket=record.bucket, key="some-file.txt", stream=io.BytesIO(b"data")
        )
        TagManager(object_version).update(
            {
                ObjectTagKey.ByReferenceURL: httpserver.url_for("some-file.txt"),
                ObjectTagKey.Packaging: PackagingFormat.SimpleZip,
            }
        )

        httpserver.expect_request("/some-file.txt").respond_with_data(b"data")

        db.session.refresh(object_version)

        result = tasks.dereference_object(record.id, object_version.version_id)
        assert result == ["some-file.txt"]

        assert httpserver.log == []


def test_dereference_when_not_head(
    api, location, es, httpserver: pytest_httpserver.HTTPServer
):
    with api.test_request_context():
        record = SWORDDeposit.create({})

        object_version = ObjectVersion.create(
            bucket=record.bucket, key="some-file.txt", stream=io.BytesIO(b"data")
        )
        TagManager(object_version).update(
            {
                ObjectTagKey.ByReferenceURL: httpserver.url_for("some-file.txt"),
                ObjectTagKey.Packaging: PackagingFormat.SimpleZip,
            }
        )
        # This makes the object version we already had a non-head one
        ObjectVersion.delete(record.bucket, object_version.key)

        httpserver.expect_request("/some-file.txt").respond_with_data(b"data")

        db.session.refresh(object_version)

        result = tasks.dereference_object(record.id, object_version.version_id)
        assert result == ["some-file.txt"]
        assert httpserver.log == []


def test_error_dereferencing(
    api, users, location, es, httpserver: pytest_httpserver.HTTPServer
):
    with api.test_request_context():
        record = SWORDDeposit.create({})
        object_version = ObjectVersion.create(bucket=record.bucket, key="some-file.txt")
        TagManager(object_version).update(
            {
                ObjectTagKey.ByReferenceURL: httpserver.url_for("some-file.txt"),
                # This one should get removed after dereferencing
                ObjectTagKey.ByReferenceNotDeleted: "true",
                ObjectTagKey.Packaging: PackagingFormat.SimpleZip,
            }
        )

        httpserver.expect_request("/some-file.txt").respond_with_data(
            b"", status=HTTPStatus.GONE
        )

        db.session.refresh(object_version)

        with pytest.raises(urllib.error.HTTPError):
            tasks.dereference_object(record.id, object_version.version_id)

        db.session.refresh(object_version)

        tags = TagManager(object_version)
        assert tags.get(ObjectTagKey.FileState) == FileState.Error


def test_error_unpacking(api, users, location, es):
    with api.test_request_context():
        record = SWORDDeposit.create({})
        object_version = ObjectVersion.create(
            bucket=record.bucket, key="some-file.txt", mimetype="text/plain"
        )
        TagManager(object_version).update(
            {ObjectTagKey.Packaging: PackagingFormat.SimpleZip,}
        )

        db.session.refresh(object_version)

        with pytest.raises(ContentTypeNotAcceptable):
            tasks.unpack_object(record.id, object_version.version_id)

        db.session.refresh(object_version)

        tags = TagManager(object_version)
        assert tags.get(ObjectTagKey.FileState) == FileState.Error


def test_schema_different_url_types(api):
    temporary_id = uuid.uuid4()

    schema = ByReferenceSchema(
        context={"url_adapter": api.url_map.bind("invenio.example")}
    )
    result = schema.load(
        {
            "@context": JSON_LD_CONTEXT,
            "@type": "ByReference",
            "byReferenceFiles": [
                {
                    "@id": "http://elsewhere.example/",
                    "contentDisposition": "attachment; filename=file.txt",
                    "contentType": "text/plain",
                    "dereference": True,
                },
                {
                    "@id": "http://invenio.example/sword/service-document",
                    "contentDisposition": "attachment; filename=file.txt",
                    "contentType": "text/plain",
                    "dereference": True,
                },
                {
                    "@id": f"http://invenio.example/sword/staging/{temporary_id}",
                    "contentDisposition": "attachment; filename=file.txt",
                    "contentType": "text/plain",
                    "dereference": True,
                },
            ],
        }
    )

    assert result["files"][0].url == "http://elsewhere.example/"
    assert result["files"][1].url == "http://invenio.example/sword/service-document"
    assert result["files"][2].temporary_id == temporary_id
