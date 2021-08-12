import io
from http import HTTPStatus

from flask import url_for
from flask_security import url_for_security
from invenio_db import db
from invenio_files_rest.models import ObjectVersion
from invenio_files_rest.models import ObjectVersionTag

from invenio_sword.api import SWORDDeposit
from invenio_sword.enum import ObjectTagKey


def test_get_status_document_not_found(api, location, es):
    with api.app_context(), api.test_client() as client:
        response = client.get("/sword/deposit/1234")
        assert response.status_code == HTTPStatus.NOT_FOUND


def test_get_status_document(api, users, location, es):
    with api.test_request_context(), api.test_client() as client:
        client.post(
            url_for_security("login"),
            data={"email": users[0]["email"], "password": "tester"},
        )
        record = SWORDDeposit.create({})
        record.commit()
        db.session.commit()

        ObjectVersion.create(
            record.bucket,
            "file.n3",
            mimetype="text/n3",
            stream=io.BytesIO(b"1 _:a 2 ."),
        )

        response = client.get("/sword/deposit/{}".format(record.pid.pid_value))
        assert response.status_code == HTTPStatus.OK
        assert len(response.json["links"]) == 1
        assert response.json["links"][0]["contentType"] == "text/n3"


def test_put_status_document(api, users, location, es):
    with api.test_request_context(), api.test_client() as client:
        client.post(
            url_for_security("login"),
            data={"email": users[0]["email"], "password": "tester"},
        )
        record = SWORDDeposit.create({})
        record.commit()
        db.session.commit()

        object_version = ObjectVersion.create(
            record.bucket,
            "file.n3",
            mimetype="text/n3",
            stream=io.BytesIO(b"1 _:a 2 ."),
        )
        ObjectVersionTag.create(
            object_version=object_version,
            key=ObjectTagKey.FileSetFile.value,
            value="true",
        )

        response = client.put(
            "/sword/deposit/{}".format(record.pid.pid_value), data=b""
        )
        assert response.status_code == HTTPStatus.OK

        # This should have removed the previous file, as the empty PUT is a reset.
        object_versions = list(
            ObjectVersion.query.filter_by(bucket=record.bucket).order_by("created")
        )
        assert len(object_versions) == 2
        assert not object_versions[0].is_head
        assert object_versions[1].is_head
        assert object_versions[1].file is None


def test_cant_unpublish(api, users, location, es):
    with api.test_request_context(), api.test_client() as client:
        client.post(
            url_for_security("login"),
            data={"email": users[0]["email"], "password": "tester"},
        )

        response = client.post(url_for("invenio_sword.depid_service_document"))
        assert response.status_code == HTTPStatus.CREATED
        assert "http://purl.org/net/sword/3.0/state/ingested" in [
            state["@id"] for state in response.json["state"]
        ]

        response = client.post(
            response.headers["Location"], headers={"In-Progress": "true"}
        )
        assert response.status_code == HTTPStatus.CONFLICT


def test_delete_status_document(api, users, location, es):
    with api.test_request_context(), api.test_client() as client:
        client.post(
            url_for_security("login"),
            data={"email": users[0]["email"], "password": "tester"},
        )
        record = SWORDDeposit.create({})
        record.commit()
        db.session.commit()

        response = client.delete("/sword/deposit/{}".format(record.pid.pid_value))
        assert response.status_code == HTTPStatus.NO_CONTENT

        response = client.get("/sword/deposit/{}".format(record.pid.pid_value))
        assert response.status_code == HTTPStatus.GONE
