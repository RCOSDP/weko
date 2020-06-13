# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Citeproc serializer tests."""

from __future__ import absolute_import, print_function

import json

import pytest
from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record
from werkzeug.exceptions import BadRequest

from invenio_records_rest.errors import StyleNotFoundRESTError
from invenio_records_rest.serializers.citeproc import CiteprocSerializer, \
    StyleNotFoundError


def get_test_data():
    pid = PersistentIdentifier(pid_type='recid', pid_value='1')
    record = Record({
        'title': 'Citeproc test', 'type': 'book',
        'creators': [
            {'family_name': 'Doe', 'given_name': 'John'},
            {'family_name': 'Smith', 'given_name': 'Jane'}
        ],
        'publication_date': [2016, 1, 1]
    })
    return pid, record


class TestSerializer(object):
    """TestSerializer"""

    def serialize(self, pid, record, links_factory=None):
        csl_json = {}
        csl_json['id'] = pid.pid_value
        csl_json['type'] = record['type']
        csl_json['title'] = record['title']
        csl_json['author'] = [{'family': a['family_name'],
                               'given': a['given_name']}
                              for a in record['creators']]
        csl_json['issued'] = {'date-parts': [record['publication_date']]}
        return json.dumps(csl_json)


def test_serialize():
    """Test Citeproc serialization."""
    pid, record = get_test_data()

    serializer = CiteprocSerializer(TestSerializer())
    data = serializer.serialize(pid, record)
    assert 'Citeproc test' in data
    assert 'Doe, J.' in data
    assert '& Smith, J.' in data
    assert '2016.' in data


def test_serializer_args():
    """Test Citeproc serialization arguments."""
    pid, record = get_test_data()

    serializer = CiteprocSerializer(TestSerializer())
    data = serializer.serialize(pid, record, style='science')
    assert '1.' in data
    assert 'J. Doe,' in data
    assert 'J. Smith,' in data
    assert 'Citeproc test' in data
    assert '(2016)' in data


def test_nonexistent_style():
    """Test Citeproc exceptions."""
    pid, record = get_test_data()

    serializer = CiteprocSerializer(TestSerializer())
    with pytest.raises(StyleNotFoundError):
        serializer.serialize(pid, record, style='non-existent')


def test_serializer_in_request(app):
    """Test Citeproc serialization while in a request context."""
    pid, record = get_test_data()

    serializer = CiteprocSerializer(TestSerializer())

    with app.test_request_context(query_string={'style': 'science'}):
        data = serializer.serialize(pid, record)
        assert '1.' in data
        assert 'J. Doe,' in data
        assert 'J. Smith,' in data
        assert 'Citeproc test' in data
        assert '(2016)' in data

    with app.test_request_context(query_string={'style': 'non-existent'}):
        with pytest.raises(StyleNotFoundRESTError):
            serializer.serialize(pid, record, style='non-existent')
