import io
import json
import os
from http import HTTPStatus

import pytest
from flask_security import url_for_security
from invenio_files_rest.models import ObjectVersion
from sword3common.exceptions import ContentMalformed
from sword3common.exceptions import ContentTypeNotAcceptable

from invenio_sword.api import SWORDDeposit
from invenio_sword.packaging import SimpleZipPackaging
from invenio_sword.packaging import SWORDBagItPackaging

original_deposit = (
    object()
)  # A sentinel, representing the original deposit in our expected data

packaged_content = {
    "example.svg": {
        "rel": [
            "http://purl.org/net/sword/3.0/terms/derivedResource",
            "http://purl.org/net/sword/3.0/terms/fileSetFile",
        ],
        "contentType": "image/svg+xml",
        "status": "http://purl.org/net/sword/3.0/filestate/ingested",
        "derivedFrom": original_deposit,
    },
    "hello.txt": {
        "rel": [
            "http://purl.org/net/sword/3.0/terms/derivedResource",
            "http://purl.org/net/sword/3.0/terms/fileSetFile",
        ],
        "contentType": "text/plain",
        "status": "http://purl.org/net/sword/3.0/filestate/ingested",
        "derivedFrom": original_deposit,
    },
}

ingest_test_parameters = [
    # A binary deposit
    (
        "binary.svg",
        "http://purl.org/net/sword/3.0/package/Binary",
        "image/svg+xml",
        {
            "binary.svg": {
                "rel": [
                    "http://purl.org/net/sword/3.0/terms/fileSetFile",
                    "http://purl.org/net/sword/3.0/terms/originalDeposit",
                ],
                "contentType": "image/svg+xml",
                "status": "http://purl.org/net/sword/3.0/filestate/ingested",
                "packaging": "http://purl.org/net/sword/3.0/package/Binary",
            }
        },
    ),
    # A simple zip deposit
    (
        "simple.zip",
        "http://purl.org/net/sword/3.0/package/SimpleZip",
        "application/zip",
        {
            original_deposit: {
                "rel": ["http://purl.org/net/sword/3.0/terms/originalDeposit"],
                "contentType": "application/zip",
                "status": "http://purl.org/net/sword/3.0/filestate/ingested",
                "packaging": "http://purl.org/net/sword/3.0/package/SimpleZip",
            },
            **packaged_content,  # type: ignore
        },
    ),
    # A BagIt deposit
    (
        "bagit.zip",
        "http://purl.org/net/sword/3.0/package/SWORDBagIt",
        "application/zip",
        {
            original_deposit: {
                "rel": ["http://purl.org/net/sword/3.0/terms/originalDeposit"],
                "contentType": "application/zip",
                "status": "http://purl.org/net/sword/3.0/filestate/ingested",
                "packaging": "http://purl.org/net/sword/3.0/package/SWORDBagIt",
            },
            **packaged_content,  # type: ignore
        },
    ),
]


@pytest.mark.parametrize(
    "filename,packaging,content_type,expected_links", ingest_test_parameters
)
def test_ingest(
    api,
    users,
    location,
    es,
    task_delay,
    fixtures_path,
    filename,
    packaging,
    content_type,
    expected_links,
):
    with api.test_request_context(), api.test_client() as client:
        client.post(
            url_for_security("login"),
            data={"email": users[0]["email"], "password": "tester"},
        )

        with open(os.path.join(fixtures_path, filename), "rb") as f:
            response = client.post(
                "/sword/service-document",
                data=f,
                headers={
                    "Packaging": packaging,
                    "Content-Type": content_type,
                    "Content-Disposition": "attachment; filename={}".format(filename),
                },
            )
        assert response.status_code == HTTPStatus.CREATED

        assert task_delay.call_count == 1
        task_self = task_delay.call_args[0][0]
        task_self.apply()

        response = client.get(response.headers["Location"])

        metadata_file_count = 0

        for link in response.json["links"]:
            key = link["@id"].split("/", 7)[-1]
            if key.startswith(".metadata-"):
                metadata_file_count += 1
                continue

            if (
                "http://purl.org/net/sword/3.0/terms/originalDeposit" in link["rel"]
                and "http://purl.org/net/sword/3.0/terms/fileSetFile" not in link["rel"]
            ):
                expected_link = expected_links[original_deposit]
            else:
                expected_link = expected_links[key]

            if "derivedFrom" in link:
                link["derivedFrom"] = original_deposit

            expected_link["@id"] = response.json["@id"] + "/file/" + key

            assert link == expected_link

        assert len(response.json["links"]) == len(expected_links) + metadata_file_count


@pytest.mark.parametrize(
    "filename,packaging,content_type,expected_links", ingest_test_parameters
)
def test_create_with_metadata_and_then_ingest(
    api,
    users,
    location,
    es,
    fixtures_path,
    task_delay,
    filename,
    packaging,
    content_type,
    expected_links,
):
    with api.test_request_context(), api.test_client() as client:
        client.post(
            url_for_security("login"),
            data={"email": users[0]["email"], "password": "tester"},
        )

        response = client.post(
            "/sword/service-document",
            data=io.BytesIO(json.dumps({}).encode()),
            headers={
                "Metadata-Format": "http://purl.org/net/sword/3.0/types/Metadata",
                "Content-Type": "application/ld+json",
                "Content-Disposition": "attachment; metadata=true",
                "In-Progress": "true",
            },
        )
        assert response.status_code == HTTPStatus.CREATED
        assert task_delay.call_count == 0

        with open(os.path.join(fixtures_path, filename), "rb") as f:
            client.post(
                response.headers["Location"],
                data=f,
                headers={
                    "Packaging": packaging,
                    "Content-Type": content_type,
                    "Content-Disposition": "attachment; filename={}".format(filename),
                },
            )

        assert task_delay.call_count == 1
        task_self = task_delay.call_args[0][0]
        task_self.apply()

        response = client.get(response.headers["Location"])

        metadata_link_count = 0

        for link in response.json["links"]:
            key = link["@id"].split("/", 7)[-1]

            # Ignore ingested metadata files
            if key.startswith(".metadata-"):
                metadata_link_count += 1
                continue

            if (
                "http://purl.org/net/sword/3.0/terms/originalDeposit" in link["rel"]
                and "http://purl.org/net/sword/3.0/terms/fileSetFile" not in link["rel"]
            ):
                expected_link = expected_links[original_deposit]
            else:
                expected_link = expected_links[key]

            if "derivedFrom" in link:
                link["derivedFrom"] = original_deposit

            expected_link["@id"] = response.json["@id"] + "/file/" + key

            assert link == expected_link

        assert len(response.json["links"]) == len(expected_links) + metadata_link_count


@pytest.mark.parametrize(
    "filename,content_type,packaging_class,exception_class",
    [
        ("simple.zip", "application/zip", SWORDBagItPackaging, ContentMalformed),
        ("binary.svg", "application/zip", SWORDBagItPackaging, ContentMalformed),
        ("binary.svg", "application/zip", SimpleZipPackaging, ContentMalformed),
        ("binary.svg", "image/svg+xml", SWORDBagItPackaging, ContentTypeNotAcceptable),
        ("binary.svg", "image/svg+xml", SimpleZipPackaging, ContentTypeNotAcceptable),
    ],
)
def test_bad_files(
    api,
    location,
    filename,
    content_type,
    packaging_class,
    exception_class,
    fixtures_path,
):
    with api.app_context():
        record = SWORDDeposit.create({})
        packaging = packaging_class(record)
        with open(os.path.join(fixtures_path, filename), "rb") as stream:
            object_version = ObjectVersion.create(
                record.bucket, key=filename, stream=stream, mimetype=content_type
            )
        with pytest.raises(exception_class):
            packaging.unpack(object_version)


def test_unknown_packaging_format(api, location, users, task_delay):
    with api.test_request_context(), api.test_client() as client:
        client.post(
            url_for_security("login"),
            data={"email": users[0]["email"], "password": "tester"},
        )

        response = client.post(
            "/sword/service-document",
            data=io.BytesIO(b"data"),
            headers={
                "Packaging": "http://something.invalid/",
                "Content-Type": "text/plain",
                "Content-Disposition": "attachment; filename=data.txt",
            },
        )

        assert response.status_code == HTTPStatus.UNSUPPORTED_MEDIA_TYPE
        assert response.json["@type"] == "PackagingFormatNotAcceptable"

        assert not task_delay.called
