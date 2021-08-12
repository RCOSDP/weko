import io
import json
import os
from http import HTTPStatus

from flask import url_for
from flask_security import url_for_security
from invenio_db import db
from invenio_files_rest.models import ObjectVersion
from invenio_files_rest.models import ObjectVersionTag
from sqlalchemy import null
from sqlalchemy import true

from invenio_sword.api import SWORDDeposit
from invenio_sword.enum import ObjectTagKey
from invenio_sword.packaging import SWORDBagItPackaging


def test_get_fileset_url(api, users, location, es):
    with api.test_request_context(), api.test_client() as client:
        client.post(
            url_for_security("login"),
            data={"email": users[0]["email"], "password": "tester"},
        )
        record = SWORDDeposit.create({})
        record.commit()
        db.session.commit()

        response = client.get(
            url_for("invenio_sword.depid_fileset", pid_value=record.pid.pid_value)
        )
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


def test_put_fileset_url(api, users, location, es, task_delay):
    with api.test_request_context(), api.test_client() as client:
        client.post(
            url_for_security("login"),
            data={"email": users[0]["email"], "password": "tester"},
        )
        record = SWORDDeposit.create({})
        record.commit()
        object_version = ObjectVersion.create(
            record.bucket,
            key="old-file.txt",
            stream=io.BytesIO(b"hello"),
            mimetype="text/plain",
        )
        ObjectVersionTag.create(
            object_version=object_version,
            key=ObjectTagKey.FileSetFile.value,
            value="true",
        )
        db.session.commit()

        response = client.put(
            url_for("invenio_sword.depid_fileset", pid_value=record.pid.pid_value),
            data=b"hello again",
            headers={
                "Content-Disposition": "attachment; filename=new-file.txt",
                "Content-Type": "text/plain",
            },
        )
        assert response.status_code == HTTPStatus.NO_CONTENT

        assert task_delay.call_count == 1
        task_self = task_delay.call_args[0][0]
        task_self.apply()

        # Check original ObjectVersion is marked deleted
        original_object_versions = list(
            ObjectVersion.query.filter_by(
                bucket=record.bucket, key="old-file.txt"
            ).order_by("created")
        )
        assert len(original_object_versions) == 2
        assert not original_object_versions[0].is_head
        assert original_object_versions[1].is_head
        assert original_object_versions[1].file is None

        # Check new object has been created
        new_object_version = ObjectVersion.query.filter_by(
            bucket=record.bucket, key="new-file.txt"
        ).one()
        assert new_object_version.is_head


def test_post_fileset_url(api, users, location, es, task_delay):
    with api.test_request_context(), api.test_client() as client:
        client.post(
            url_for_security("login"),
            data={"email": users[0]["email"], "password": "tester"},
        )
        record = SWORDDeposit.create({})
        record.commit()
        ObjectVersion.create(
            record.bucket,
            key="old-file.txt",
            stream=io.BytesIO(b"hello"),
            mimetype="text/plain",
        )
        db.session.commit()

        response = client.post(
            url_for("invenio_sword.depid_fileset", pid_value=record.pid.pid_value),
            data=b"hello again",
            headers={
                "Content-Disposition": "attachment; filename=new-file.txt",
                "Content-Type": "text/plain",
            },
        )
        assert response.status_code == HTTPStatus.NO_CONTENT

        # Check original ObjectVersion is still there
        original_object_versions = list(
            ObjectVersion.query.filter_by(
                bucket=record.bucket, key="old-file.txt"
            ).order_by("created")
        )
        assert len(original_object_versions) == 1
        assert original_object_versions[0].is_head

        # Check new object has been created
        new_object_version = ObjectVersion.query.filter_by(
            bucket=record.bucket, key="new-file.txt"
        ).one()
        assert new_object_version.is_head


def test_delete_fileset(
    api, users, location, es, fixtures_path, test_metadata_format, task_delay
):
    with api.test_request_context(), api.test_client() as client:
        client.post(
            url_for_security("login"),
            data={"email": users[0]["email"], "password": "tester"},
        )

        # Create a deposit, initially with a metadata deposit
        original_response = client.post(
            url_for("invenio_sword.depid_service_document"),
            data=json.dumps(
                {
                    "@context": "https://swordapp.github.io/swordv3/swordv3.jsonld",
                    "title": "A title",
                }
            ),
            headers={
                "Content-Disposition": "attachment; metadata=true",
                "In-Progress": "true",
            },
        )

        assert ObjectVersion.query.count() == 1

        # Add some extra metadata
        response = client.post(
            original_response.json["metadata"]["@id"],
            data=b"some metadata",
            headers={"Metadata-Format": test_metadata_format},
        )
        assert response.status_code == HTTPStatus.NO_CONTENT

        assert ObjectVersion.query.count() == 2

        with open(os.path.join(fixtures_path, "bagit.zip"), "rb") as f:
            response = client.post(
                original_response.headers["Location"],
                data=f,
                headers={
                    "Packaging": SWORDBagItPackaging.packaging_name,
                    "Content-Type": "application/zip",
                    "In-Progress": "true",
                },
            )
            assert response.status_code == HTTPStatus.OK

        assert task_delay.call_count == 1
        task_self = task_delay.call_args[0][0]
        task_self.apply()

        # One test metadata, one old SWORD metadata, one new SWORD metadata, one original deposit, and two files
        assert ObjectVersion.query.count() == 6
        # One test metadata, one new SWORD metadata, one original deposit, and two files
        assert ObjectVersion.query.filter(ObjectVersion.is_head == true()).count() == 5

        # Now let's delete the fileset. This should ensure that there is only one extant file, as the SWORD metadata and
        # original deposit were deposited as part of a fileset, leaving only the test dataset
        response = client.delete(original_response.json["fileSet"]["@id"])
        assert response.status_code == HTTPStatus.NO_CONTENT

        # All four previously extent files now have file_id=NULL versions
        assert ObjectVersion.query.count() == 10
        assert (
            ObjectVersion.query.filter(
                ObjectVersion.is_head == true(), ObjectVersion.file_id != null()
            ).count()
            == 1
        )
