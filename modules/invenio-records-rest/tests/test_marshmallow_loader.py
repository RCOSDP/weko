# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio marshmallow loader tests."""

from __future__ import absolute_import, print_function

import json
from copy import deepcopy

import pytest
from helpers import get_json
from invenio_records.api import Record
from invenio_records.models import RecordMetadata
from marshmallow import Schema, fields

from invenio_records_rest.loaders import json_pid_checker
from invenio_records_rest.loaders.marshmallow import MarshmallowErrors, \
    marshmallow_loader
from invenio_records_rest.schemas import Nested, RecordMetadataSchemaJSONV1, \
    RecordSchemaJSONV1
from invenio_records_rest.schemas.fields import PersistentIdentifier


class _TestSchema(Schema):
    """Test schema."""

    title = fields.Str(required=True, attribute='metadata.mytitle')
    random = fields.Str(required=True, attribute='metadata.nonexistant')
    id = fields.Str(attribute='pid.pid_value')


class NestedSchema(Schema):
    """Test nested schema."""
    sample = fields.Str(required=True, attribute='metadata.nested')


class _TestSchemaNested(Schema):
    """Test schema with custom Nested field."""

    nested_field = Nested(NestedSchema, attribute='metadata.nested',
                          many=True, required=True)


class _TestMetadataSchema(Schema):
        """Test schema."""

        title = fields.Str()
        stars = fields.Integer()
        year = fields.Integer()
        control_number = PersistentIdentifier()


def test_marshmallow_load(app, db, es, test_data, search_url, search_class):
    """Test marshmallow loader."""
    app.config['RECORDS_REST_DEFAULT_LOADERS'] = {
        'application/json': marshmallow_loader(_TestMetadataSchema)}

    with app.test_client() as client:
        HEADERS = [
            ('Accept', 'application/json'),
            ('Content-Type', 'application/json')
        ]

        # Create record
        req_data = test_data[0]
        res = client.post(
            search_url, data=json.dumps(req_data), headers=HEADERS)
        assert res.status_code == 201

        # Check that the returned response matches the stored data
        original_res_data = get_json(res)
        model_record = RecordMetadata.query.one()
        assert original_res_data['metadata'] == model_record.json

        # Try to modify the "control_number"
        req_data = deepcopy(original_res_data['metadata'])
        req_data['control_number'] = 42
        req_url = original_res_data['links']['self']
        res = client.put(req_url, data=json.dumps(req_data), headers=HEADERS)
        res_data = get_json(res)
        model_record = RecordMetadata.query.one()
        assert res_data['metadata'] == original_res_data['metadata']
        assert res_data['metadata'] == model_record.json


def test_marshmallow_load_errors(app, db, es, test_data, search_url,
                                 search_class):
    """Test marshmallow loader errors."""
    app.config['RECORDS_REST_DEFAULT_LOADERS'] = {
        'application/json': marshmallow_loader(_TestSchema)}

    with app.test_client() as client:
        HEADERS = [
            ('Accept', 'application/json'),
            ('Content-Type', 'application/json')
        ]

        # Create record
        incomplete_data = dict(test_data[0])
        del incomplete_data['title']
        res = client.post(
            search_url, data=json.dumps(incomplete_data), headers=HEADERS)
        assert res.status_code == 400


def test_marshmallow_load_nested_errors(app, db, es, test_data, search_url,
                                        search_class):
    """Test loading nested errors."""
    app.config['RECORDS_REST_DEFAULT_LOADERS'] = {
        'application/json': marshmallow_loader(_TestSchemaNested)}

    with app.test_client() as client:
        HEADERS = [
            ('Accept', 'application/json'),
            ('Content-Type', 'application/json')
        ]

        # Create record
        missing_top_most_required_field = dict(nested="test")
        res = client.post(
            search_url, data=json.dumps(missing_top_most_required_field),
            headers=HEADERS)
        assert res.status_code == 400
        response_json = json.loads(res.data.decode('utf-8'))
        assert response_json['errors'][0]['field'] == 'nested_field'


def test_marshmallow_errors(test_data):
    """Test MarshmallowErrors class."""
    incomplete_data = dict(test_data[0])
    res = _TestSchema(context={}).load(json.dumps(incomplete_data))
    me = MarshmallowErrors(res.errors)

    with pytest.raises(TypeError):
        next(me)
    # assert __iter__ method works
    iter(me)
    # assert __next__ method works
    assert next(me)


def test_json_pid_checker_loader(app, db, es, search_url, search_class):
    """Test loading using the record metadata schema."""
    app.config['RECORDS_REST_DEFAULT_LOADERS'] = {
        'application/json': json_pid_checker}

    with app.test_client() as client:
        HEADERS = [
            ('Accept', 'application/json'),
            ('Content-Type', 'application/json')
        ]

        # Create record
        req_data = {'foo': 42, 'bar': ['here', 'it', 'comes']}
        req_url = search_url
        res = client.post(req_url, data=json.dumps(req_data), headers=HEADERS)
        assert res.status_code == 201

        original_res_data = get_json(res)
        model_record = RecordMetadata.query.one()
        assert 'control_number' in model_record.json
        assert original_res_data['metadata'] == model_record.json
        assert all(original_res_data['metadata'][k] == v
                   for k, v in req_data.items())
        assert all(model_record.json[k] == v for k, v in req_data.items())
