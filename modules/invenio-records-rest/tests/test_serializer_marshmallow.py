# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio serializer tests."""

from __future__ import absolute_import, print_function

from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record
from marshmallow import Schema, fields

from invenio_records_rest.serializers.base import PreprocessorMixin
from invenio_records_rest.serializers.marshmallow import MarshmallowMixin

# .tox/c1/bin/pytest --cov=invenio_records_rest tests/test_serializer_marshmallow.py -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/invenio-records-rest/.tox/c1/tmp

class SimpleMarshmallowSerializer(MarshmallowMixin, PreprocessorMixin):
    """Simple Marshmallow serializer."""


class _TestSchema(Schema):
    title = fields.Str(attribute='metadata.title')
    author = fields.Function(lambda metadata, context: context['author'])


def test_transform_record(app, db):
    """Test marshmallow serializer."""
    serializer = SimpleMarshmallowSerializer(_TestSchema)
    data = serializer.transform_record(
        PersistentIdentifier(pid_type='recid', pid_value='1'),
        Record({'title': 'test'}),
        marshmallow_context=dict(author='test2')
    )
    assert data == dict(title='test', author='test2')


def test_transform_search_hit(app, db):
    """Test marshmallow serializer."""
    serializer = SimpleMarshmallowSerializer(_TestSchema)
    data = serializer.transform_record(
        PersistentIdentifier(pid_type='recid', pid_value='1'),
        Record({'title': 'test'}),
        marshmallow_context=dict(author='test2')
    )
    assert data == dict(title='test', author='test2')


def test_transform_record_default_schema(app, db):
    """Test marshmallow serializer without providing a schema."""
    serializer = SimpleMarshmallowSerializer()
    data = serializer.transform_record(
        PersistentIdentifier(pid_type='recid', pid_value='1'),
        Record({'title': 'test'})
    )
    assert data == {
        'id': 1,
        'created': None,
        'links': {},
        'metadata': {'title': 'test'},
        'updated': None
    }
