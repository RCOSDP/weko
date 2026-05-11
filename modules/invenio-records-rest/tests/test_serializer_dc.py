# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Dublin Core serializer tests."""

from __future__ import absolute_import, print_function

import pytest

# Skip this entire module if dcxml is not available
dcxml = pytest.importorskip("dcxml")

from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record
from marshmallow import Schema, fields

from invenio_records_rest.serializers.dc import DublinCoreSerializer


class SimpleSchema(Schema):
    """Test schema."""

    titles = fields.Raw(attribute="metadata.titles")


# .tox/c1/bin/pytest --cov=invenio_records_rest tests/test_serializer_dc.py::test_serialize -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/invenio-records-rest/.tox/c1/tmp
def test_serialize(app, db, item_type):
    """Test JSON serialize."""
    pid = PersistentIdentifier(pid_type="recid", pid_value="2")
    record = Record({"titles": ["DC test"], "item_type_id": "15"})

    data = DublinCoreSerializer(SimpleSchema).serialize(pid, record)

    assert "<dc:title>DC test</dc:title>" in data

    s = DublinCoreSerializer(SimpleSchema)
    tree = s.serialize_oaipmh(pid, {"_source": record})
    assert len(tree) == 1
