import io
import json
from http import HTTPStatus

import pytest
from flask import url_for
from flask_security import url_for_security
from invenio_db import db

from invenio_sword.api import SWORDDeposit
from invenio_sword.metadata import SWORDMetadata


def test_get_metadata_document(api, users, location, es):
    with api.test_request_context(), api.test_client() as client:
        client.post(
            url_for_security("login"),
            data={"email": users[0]["email"], "password": "tester"},
        )

        record = SWORDDeposit.create({})
        record.set_metadata({"dc:title": "Deposit title"}, SWORDMetadata)
        record.commit()
        db.session.commit()

        response = client.get("/sword/deposit/{}".format(record.pid.pid_value))
        assert response.status_code == HTTPStatus.OK

        response = client.get("/sword/deposit/{}/metadata".format(record.pid.pid_value))
        assert response.status_code == HTTPStatus.OK
        assert response.is_json
        assert response.json == {
            "@id": "http://localhost/sword/deposit/{}".format(record.pid.pid_value),
            "@context": "https://swordapp.github.io/swordv3/swordv3.jsonld",
            "dc:title": "Deposit title",
        }


def test_get_metadata_document_when_not_available(api, users, location, es):
    with api.test_request_context(), api.test_client() as client:
        client.post(
            url_for_security("login"),
            data={"email": users[0]["email"], "password": "tester"},
        )
        record = SWORDDeposit.create({})
        record.commit()
        db.session.commit()

        status_response = client.get("/sword/deposit/{}".format(record.pid.pid_value))
        assert status_response.status_code == HTTPStatus.OK
        status_response = client.get(
            "/sword/deposit/{}/metadata".format(record.pid.pid_value)
        )
        assert status_response.status_code == HTTPStatus.OK


def test_put_metadata_document_without_body(api, users, location, es):
    with api.test_request_context(), api.test_client() as client:
        client.post(
            url_for_security("login"),
            data={"email": users[0]["email"], "password": "tester"},
        )
        record = SWORDDeposit.create({})
        record.commit()
        db.session.commit()

        response = client.put("/sword/deposit/{}/metadata".format(record.pid.pid_value))
        assert response.status_code == HTTPStatus.BAD_REQUEST


def test_put_metadata_document_invalid_json(api, users, location, es):
    with api.test_request_context(), api.test_client() as client:
        client.post(
            url_for_security("login"),
            data={"email": users[0]["email"], "password": "tester"},
        )
        record = SWORDDeposit.create({})
        record.commit()
        db.session.commit()

        response = client.put(
            "/sword/deposit/{}/metadata".format(record.pid.pid_value),
            headers={
                "Content-Type": "application/ld+json",
                "Metadata-Format": "http://purl.org/net/sword/3.0/types/Metadata",
            },
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST


def test_put_metadata_document(api, users, location, es):
    with api.test_request_context(), api.test_client() as client:
        client.post(
            url_for_security("login"),
            data={"email": users[0]["email"], "password": "tester"},
        )
        record = SWORDDeposit.create({})
        record.commit()
        db.session.commit()

        response = client.put(
            "/sword/deposit/{}/metadata".format(record.pid.pid_value),
            headers={
                "Metadata-Format": "http://purl.org/net/sword/3.0/types/Metadata",
                "Content-Type": "application/ld+json",
            },
            data=json.dumps({}),
        )
        assert response.status_code == HTTPStatus.NO_CONTENT

        record = SWORDDeposit.get_record(record.id)
        assert (
            record["swordMetadataSourceFormat"]
            == "http://purl.org/net/sword/3.0/types/Metadata"
        )
        assert any(
            "http://purl.org/net/sword/3.0/terms/formattedMetadata" in link["rel"]
            and link["metadataFormat"] == "http://purl.org/net/sword/3.0/types/Metadata"
            for link in record.get_status_as_jsonld()["links"]
        )


@pytest.mark.parametrize(
    "view_name,status_code,additional_headers",
    [
        ("invenio_sword.depid_metadata", HTTPStatus.NO_CONTENT, {}),
        (
            "invenio_sword.depid_item",
            HTTPStatus.OK,
            {"Content-Disposition": "attachment; metadata=true"},
        ),
    ],
)
def test_post_metadata_document_to_append(
    api, users, location, es, view_name, status_code, additional_headers
):
    with api.test_request_context(), api.test_client() as client:
        client.post(
            url_for_security("login"),
            data={"email": users[0]["email"], "password": "tester"},
        )
        record = SWORDDeposit.create({})
        record.set_metadata(
            {
                "@context": "https://swordapp.github.io/swordv3/swordv3.jsonld",
                "dc:title": "Some title",
                "dc:subject": "Some subject",
            },
            SWORDMetadata,
        )
        record.commit()
        db.session.commit()

        response = client.post(
            url_for(view_name, pid_value=record.pid.pid_value),
            headers={
                "Metadata-Format": "http://purl.org/net/sword/3.0/types/Metadata",
                "Content-Type": "application/ld+json",
                **additional_headers,
            },
            data=json.dumps(
                {
                    "@context": "https://swordapp.github.io/swordv3/swordv3.jsonld",
                    "dc:subject": "Another subject",
                    "dc:creator": "A person",
                }
            ),
        )
        assert response.status_code == status_code

        record = SWORDDeposit.get_record(record.id)
        assert (
            record["swordMetadataSourceFormat"]
            == "http://purl.org/net/sword/3.0/types/Metadata"
        )
        assert record["swordMetadata"] == {
            "@context": "https://swordapp.github.io/swordv3/swordv3.jsonld",
            "dc:title": "Some title",
            "dc:subject": "Another subject",
            "dc:creator": "A person",
        }


def test_post_metadata_document_with_additional_metadata_format(
    api, users, location, es, test_metadata_format
):
    with api.test_request_context(), api.test_client() as client:
        client.post(
            url_for_security("login"),
            data={"email": users[0]["email"], "password": "tester"},
        )
        record = SWORDDeposit.create({})
        record.set_metadata(
            {
                "@context": "https://swordapp.github.io/swordv3/swordv3.jsonld",
                "dc:title": "Some title",
                "dc:subject": "Some subject",
            },
            SWORDMetadata,
        )
        record.commit()
        db.session.commit()

        response = client.post(
            "/sword/deposit/{}/metadata".format(record.pid.pid_value),
            headers={
                "Metadata-Format": test_metadata_format,
                "Content-Type": "text/plain",
            },
            data=io.BytesIO(b"some metadata"),
        )
        assert response.status_code == HTTPStatus.NO_CONTENT

        record = SWORDDeposit.get_record(record.id)
        # Check nothing changed
        assert (
            record["swordMetadataSourceFormat"]
            == "http://purl.org/net/sword/3.0/types/Metadata"
        )
        assert record["swordMetadata"] == {
            "@context": "https://swordapp.github.io/swordv3/swordv3.jsonld",
            "dc:title": "Some title",
            "dc:subject": "Some subject",
        }
        assert len(
            [
                link
                for link in record.get_status_as_jsonld()["links"]
                if "http://purl.org/net/sword/3.0/terms/formattedMetadata"
                in link["rel"]
            ]
        )


def test_put_metadata_document_with_unsupported_format(api, users, location, es):
    with api.test_request_context(), api.test_client() as client:
        client.post(
            url_for_security("login"),
            data={"email": users[0]["email"], "password": "tester"},
        )
        record = SWORDDeposit.create({})
        record.commit()
        db.session.commit()

        response = client.put(
            "/sword/deposit/{}/metadata".format(record.pid.pid_value),
            headers={
                "Metadata-Format": "http://sword.invalid/Metadata",
                "Content-Type": "application/ld+json",
            },
            data=json.dumps({}),
        )
        assert response.status_code == HTTPStatus.UNSUPPORTED_MEDIA_TYPE
        assert response.json["@type"] == "MetadataFormatNotAcceptable"


def test_delete_metadata_document(api, users, location, es):
    with api.test_request_context(), api.test_client() as client:
        client.post(
            url_for_security("login"),
            data={"email": users[0]["email"], "password": "tester"},
        )
        record = SWORDDeposit.create({})
        record.set_metadata({"dc:title": "Deposit title"}, SWORDMetadata)
        record.commit()
        db.session.commit()

        assert record.get("swordMetadataSourceFormat") is not None
        assert record.get("swordMetadata") is not None

        response = client.delete(
            "/sword/deposit/{}/metadata".format(record.pid.pid_value)
        )
        assert response.status_code == HTTPStatus.NO_CONTENT

        record = SWORDDeposit.get_record(record.id)
        assert record.get("swordMetadataSourceFormat") is None
        assert record.get("swordMetadata") is None
