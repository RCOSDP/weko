# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Dublin Core serializer tests."""

from __future__ import absolute_import, print_function

from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record
from marshmallow import Schema, fields

from invenio_records_rest.serializers.dc import DublinCoreSerializer


class SimpleSchema(Schema):
    """Test schema."""

    titles = fields.Raw(attribute='metadata.titles')


def test_serialize():
    """Test JSON serialize."""
    pid = PersistentIdentifier(pid_type='recid', pid_value='2')
    record = Record({'titles': ['DC test']})
    data = DublinCoreSerializer(SimpleSchema).serialize(pid, record)

    assert """<dc:title>DC test</dc:title>""" in data

    s = DublinCoreSerializer(SimpleSchema)
    tree = s.serialize_oaipmh(
        pid, {'_source': record})
    assert len(tree) == 1


def test_serialize_search():
    """Test JSON serialize."""
    def fetcher(obj_uuid, data):
        assert obj_uuid in ['a', 'b']
        return PersistentIdentifier(pid_type='doi', pid_value='a')

    data = DublinCoreSerializer(SimpleSchema).serialize_search(
        fetcher,
        dict(
            hits=dict(
                hits=[
                    {'_source': {'titles': ['A']}, '_id': 'a',
                     '_version': 1},
                    {'_source': {'titles': ['B']}, '_id': 'b',
                     '_version': 1},
                ],
                total=2,
            ),
            aggregations={},
        )
    )
    assert """<dc:title>A</dc:title>""" in data
    assert """<dc:title>B</dc:title>""" in data

    s = DublinCoreSerializer(SimpleSchema)
    tree = s.serialize_oaipmh(
        PersistentIdentifier(pid_type='doi', pid_value='10.1234/b'),
        {'_source': {'titles': ['B']}, '_id': 'b', '_version': 1})
    assert len(tree) == 1
