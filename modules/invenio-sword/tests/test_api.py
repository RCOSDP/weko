# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.
"""Test the API."""
import re
from http import HTTPStatus

from flask_security import url_for_security
from invenio_files_rest.models import ObjectVersion

from invenio_sword.api import pid_resolver


def test_get_service_document(api):
    with api.test_client() as client:
        response = client.get("/sword/service-document")
        assert response.status_code == HTTPStatus.OK
        assert response.is_json


def test_deposit_empty(api, users, location):
    with api.test_request_context(), api.test_client() as client:
        client.post(
            url_for_security("login"),
            data={"email": users[0]["email"], "password": "tester"},
        )

        response = client.post("/sword/service-document")
        assert response.status_code == HTTPStatus.CREATED
        match = re.match(
            "^http://localhost/sword/deposit/([^/]+)$", response.headers["Location"]
        )
        assert match is not None
        pid_value = match.group(1)
        _, record = pid_resolver.resolve(pid_value)
        assert dict(record) == {
            "metadata": {},
            "$schema": "http://localhost/schemas/deposits/deposit-v1.0.0.json",
            "_deposit": {
                "id": pid_value,
                "status": "published",
                "owners": [users[0]["id"]],
                "created_by": users[0]["id"],
            },
            "_bucket": record.bucket_id,
        }

        # POSTing with no metadata, by-reference, or request body should result in no files being created.
        assert ObjectVersion.query.filter_by(bucket=record.bucket).count() == 0


def test_metadata_deposit(api, users, location, metadata_document):
    with api.test_request_context(), api.test_client() as client:
        client.post(
            url_for_security("login"),
            data={"email": users[0]["email"], "password": "tester"},
        )

        response = client.post(
            "/sword/service-document",
            data=metadata_document,
            headers={
                "Content-Disposition": "attachment; metadata=true",
                "Content-Type": "application/ld+json",
            },
        )
        assert response.status_code == HTTPStatus.CREATED
        match = re.match(
            "^http://localhost/sword/deposit/([^/]+)$", response.headers["Location"]
        )
        assert match is not None
        pid_value = match.group(1)
        _, record = pid_resolver.resolve(pid_value)
        assert dict(record) == {
            "metadata": {"title_statement": {"title": "The title"}},
            "swordMetadata": {
                "@context": "https://swordapp.github.io/swordv3/swordv3.jsonld",
                "@type": "Metadata",
                "dc:contributor": "A.N. Other",
                "dc:title": "The title",
                "dcterms:abstract": "This is my abstract",
            },
            "swordMetadataSourceFormat": "http://purl.org/net/sword/3.0/types/Metadata",
            "$schema": "http://localhost/schemas/deposits/deposit-v1.0.0.json",
            "_deposit": {
                "id": pid_value,
                "status": "published",
                "owners": [users[0]["id"]],
                "created_by": users[0]["id"],
            },
            "_bucket": record.bucket_id,
        }
