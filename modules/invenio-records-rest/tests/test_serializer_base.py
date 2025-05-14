# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio serializer tests."""

from __future__ import absolute_import, print_function

from datetime import datetime

from tests.helpers import create_record
from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record

from invenio_records_rest.serializers.base import PreprocessorMixin

keys = ['pid', 'metadata', 'links', 'revision', 'created', 'updated']


# .tox/c1/bin/pytest --cov=invenio_records_rest tests/test_serializer_base.py::test_preprocessor_mixin_record -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/invenio-records-rest/.tox/c1/tmp
def test_preprocessor_mixin_record(app, db, item_type):
    """Test preprocessor mixin."""
    pid, record = create_record({'title': 'test', 'aref': {'$ref': '#/title'}})
    record.model.created = datetime(2015, 10, 1, 11, 11, 11, 1)
    db.session.commit()

    data = PreprocessorMixin().preprocess_record(pid, record)
    for k in keys:
        assert k in data

    assert data['metadata']['title'] == 'test'
    assert data['metadata']['aref'] == {'$ref': '#/title'}
    assert data['created'] == '2015-10-01T11:11:11.000001+00:00'
    assert data['revision'] == 1

    data = PreprocessorMixin(replace_refs=True).preprocess_record(
        pid, Record({'title': 'test2', 'aref': {'$ref': '#/title'}}))
    assert data['created'] is None
    assert data['updated'] is None
    assert data['metadata']['aref'] == 'test2'
    
    pid, record = create_record({'title': 'test3', 'aref':{'$ref':'#/title'},'item_type_id':15})
    record.model.created = datetime(2015, 10, 1, 11, 11, 11, 1)
    db.session.commit()
    data = PreprocessorMixin().preprocess_record(pid, record)
    assert data['metadata']['title'] == 'test3'
    assert data['created'] == '2015-10-01T11:11:11.000001+00:00'
    assert data['revision'] == 1
    assert data['metadata']['aref'] == {'$ref': '#/title'}


def test_preprocessor_mixin_searchhit():
    """Test preprocessor mixin."""
    pid = PersistentIdentifier(
        pid_type='doi', pid_value='10.1234/foo', status='R')

    data = PreprocessorMixin.preprocess_search_hit(pid, {
        '_source': {
            'title': 'test',
            '_created': '2015-10-01T11:11:11.000001+00:00',
            '_updated': '2015-12-01T11:11:11.000001+00:00',
        },
        '_version': 1,
    })

    for k in keys:
        assert k in data

    assert data['metadata']['title'] == 'test'
    assert data['created'] == '2015-10-01T11:11:11.000001+00:00'
    assert data['revision'] == 1
    assert '_created' not in data['metadata']
    assert '_updated' not in data['metadata']

    data = PreprocessorMixin.preprocess_search_hit(pid, {
        '_source': {'title': 'test'},
        '_version': 1,
    })
    assert data['created'] is None
    assert data['updated'] is None
