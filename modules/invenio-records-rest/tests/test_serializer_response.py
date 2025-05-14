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

from invenio_records_rest.serializers.response import record_responsify, \
    search_responsify

import pytest
from werkzeug.exceptions import InternalServerError

class TestSerializer(object):
    """Test serializer."""

    def serialize(self, pid, record, **kwargs):
        """Dummy method."""
        return "{0}:{1}".format(pid.pid_value, record['title'])

    def serialize_search(self, fetcher, result, **kwargs):
        """Dummy method."""
        return str(len(result))

# .tox/c1/bin/pytest --cov=invenio_records_rest tests/test_serializer_response.py::test_record_responsify -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-records-rest/.tox/c1/tmp
def test_record_responsify(app):
    """Test JSON serialize."""
    rec_serializer = record_responsify(
        TestSerializer(), 'application/x-custom')

    pid = PersistentIdentifier(pid_type='recid', pid_value='1')
    rec = Record({'title': 'test'})
    resp = rec_serializer(pid, rec, headers=[('X-Test', 'test')])
    assert resp.status_code == 200
    assert resp.content_type == 'application/x-custom'
    assert resp.get_data(as_text=True) == "1:test"
    assert resp.headers['X-Test'] == 'test'

    resp = rec_serializer(pid, rec, code=201)
    assert resp.status_code == 200

    
    with pytest.raises(InternalServerError):
        rec_serializer(None, rec, code=201)


# .tox/c1/bin/pytest --cov=invenio_records_rest tests/test_serializer_response.py::test_search_responsify -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-records-rest/.tox/c1/tmp
def test_search_responsify(app, item_type):
    """Test JSON serialize."""
    search_serializer = search_responsify(
        TestSerializer(), 'application/x-custom')

    def fetcher():
        pass

    tmp = [{'_source': {'item_type_id': '15', 'item_metadata': {'test': 'test'}}}]
    result = {"hits": {"hits": tmp}}

    resp = search_serializer(fetcher, result)
    assert resp.status_code == 200
    assert resp.content_type == 'application/x-custom'
    assert resp.get_data(as_text=True) == "1"

    resp = search_serializer(
        fetcher, result, code=201, headers=[('X-Test', 'test')])
    assert resp.status_code == 201
    assert resp.headers['X-Test'] == 'test'
