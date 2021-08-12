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
"""Test the BagIt implementation."""
import os
from http import HTTPStatus

import pytest
from flask import url_for
from flask_security import url_for_security
from invenio_files_rest.models import Bucket
from invenio_files_rest.models import ObjectVersion
from invenio_records.models import RecordMetadata
from sword3common.constants import PackagingFormat
from sword3common.exceptions import ContentMalformed
from sword3common.exceptions import ContentTypeNotAcceptable
from sword3common.exceptions import ValidationFailed

from invenio_sword.api import SWORDDeposit
from invenio_sword.packaging import Packaging


def test_post_service_document_with_bagit_bag(
    api, users, location, fixtures_path, task_delay
):
    with api.test_request_context(), api.test_client() as client:
        client.post(
            url_for_security("login"),
            data={"email": users[0]["email"], "password": "tester"},
        )

        with open(os.path.join(fixtures_path, "bagit.zip"), "rb") as f:
            response = client.post(
                url_for("invenio_sword.depid_service_document"),
                input_stream=f,
                headers={
                    "Content-Type": "application/zip",
                    "Packaging": "http://purl.org/net/sword/3.0/package/SWORDBagIt",
                },
            )

        assert response.status_code == HTTPStatus.CREATED

        # Check that we attempted to queue a task
        assert task_delay.call_count == 1
        task_self = task_delay.call_args[0][0]

        task_self.apply()

        # db.session.refresh(record)

        bucket = Bucket.query.one()
        obj_1 = ObjectVersion.query.filter_by(bucket=bucket, key="example.svg").one()
        obj_2 = ObjectVersion.query.filter_by(bucket=bucket, key="hello.txt").one()

        assert obj_1.mimetype == "image/svg+xml"
        assert obj_2.mimetype == "text/plain"

        record_metadata = RecordMetadata.query.one()
        assert record_metadata.json == {
            "$schema": "http://localhost/schemas/deposits/deposit-v1.0.0.json",
            "_bucket": str(bucket.id),
            "_deposit": {
                "created_by": 1,
                # A bit of a cheat, but we know this is the deposit pid_value, and it's maintained by invenio-deposit,
                # not the code that we are testing.
                "id": record_metadata.json["_deposit"]["id"],
                "owners": [1],
                "status": "published",
            },
            "bagitInfo": {
                "Bag-Software-Agent": "bagit.py v1.7.0 "
                "<https://github.com/LibraryOfCongress/bagit-python>",
                "Bagging-Date": "2020-01-07",
                "Payload-Oxum": "473.2",
            },
            "metadata": {"title_statement": {"title": "The title"}},
            "swordMetadata": {
                "@context": "https://swordapp.github.io/swordv3/swordv3.jsonld",
                "@type": "Metadata",
                "dc:contributor": "A.N. Other",
                "dc:title": "The title",
                "dcterms:abstract": "This is my abstract",
            },
            "swordMetadataSourceFormat": "http://purl.org/net/sword/3.0/types/Metadata",
        }


@pytest.mark.parametrize(
    "filename,error_class",
    [
        ("bagit-broken-sha.zip", ValidationFailed),
        ("bagit-no-bagit-txt.zip", ContentMalformed),
        ("bagit-with-fetch.zip", ValidationFailed),
    ],
)
def test_unpack_document_with_broken_bag(
    api, location, filename, error_class, fixtures_path
):
    with api.test_request_context():
        record = SWORDDeposit.create({})
        with open(os.path.join(fixtures_path, filename), "rb") as stream:
            object_version = ObjectVersion.create(
                bucket=record.bucket, key=filename, stream=stream
            )

        packaging = Packaging.for_record_and_name(record, PackagingFormat.SwordBagIt)
        with pytest.raises(error_class):
            packaging.unpack(object_version)


def test_post_service_document_with_incorrect_content_type(
    api, users, location, fixtures_path
):
    with api.test_request_context():
        record = SWORDDeposit.create({})
        with open(os.path.join(fixtures_path, "bagit.zip"), "rb") as stream:
            object_version = ObjectVersion.create(
                bucket=record.bucket,
                key="bagit.zip",
                stream=stream,
                mimetype="application/tar",
            )

        packaging = Packaging.for_record_and_name(record, PackagingFormat.SwordBagIt)
        with pytest.raises(ContentTypeNotAcceptable):
            packaging.unpack(object_version)
