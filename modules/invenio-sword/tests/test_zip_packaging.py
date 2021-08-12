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

from invenio_files_rest.models import ObjectVersion

from invenio_sword.api import SWORDDeposit
from invenio_sword.packaging import SimpleZipPackaging

fixtures_path = os.path.join(os.path.dirname(__file__), "fixtures")


def test_simple_zip(api, users, location):
    with api.test_request_context():
        record = SWORDDeposit.create({})
        with open(os.path.join(fixtures_path, "simple.zip"), "rb") as stream:
            object_version = ObjectVersion.create(
                bucket=record.bucket,
                key="deposit.zip",
                stream=stream,
                mimetype="application/zip",
            )

        SimpleZipPackaging(record).unpack(object_version)

        obj_1 = ObjectVersion.query.filter_by(
            bucket=record.bucket, key="example.svg"
        ).one()
        obj_2 = ObjectVersion.query.filter_by(
            bucket=record.bucket, key="hello.txt"
        ).one()

        assert obj_1.mimetype == "image/svg+xml"
        assert obj_2.mimetype == "text/plain"
